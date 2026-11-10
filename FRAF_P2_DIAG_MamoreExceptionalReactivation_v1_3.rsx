##FRAF_Step3B2_Mamore_Exceptional_Reactivation_Mapper_v1_3_EXCEPTION_QA=name
##Risk_table=file
##Place_geometry=vector
##Channel_outlines=multiple vector
##Channel_year_field=string YEAR
##Channel_outline_years=string AUTO
##Output_directory=folder
##Place_id_field=string PLACE_ID
##Event_DS_AD_field=string AUTO
##Risk_DS_AD_field=string AUTO
##Event_SF_AD_field=string AUTO
##Risk_SF_AD_field=string AUTO
##Margin_distance_field=string AUTO
##Start_time_field=string AUTO
##Stop_time_field=string AUTO
##Interval_field=string AUTO
##Distal_threshold_m=number 1000
##Exceptional_interval_min_distal_events=number 25
##Exceptional_interval_min_distal_fraction=number 0.25
##Exceptional_interval_absolute_distal_events=number 50
##Exclude_calendar_start_years=string 1986
##Cluster_distance_m=number 300
##Former_AD_overlap_buffer_m=number 0
##Write_all_event_layers=boolean TRUE
# [FRAF-P2 DIAG-X archive] ARCHIVAL ID: DIAG-X | Paper 2 supplementary S6.4, Table S14.
# [FRAF-P2 DIAG-X archive] ARCHIVE NAME: FRAF_P2_DIAG_MamoreExceptionalReactivation_v1_3.rsx.
# [FRAF-P2 DIAG-X archive] ORIGINAL SOURCE: FRAF_Step3B2_Mamore_Exceptional_Reactivation_Mapper_v1_3_EXCEPTION_QA.rsx.
# [FRAF-P2 DIAG-X archive] FORMER STAGE: Step 3B.2 v1.3 (exceptional-reoccupation mapping and QA).
# [FRAF-P2 DIAG-X archive] PURPOSE: identify intervals with numerous distal DS->AD reworking events,
# [FRAF-P2 DIAG-X archive] inspect former Active Domain occupation, and map associated events.
# [FRAF-P2 DIAG-X archive] SCOPE: diagnostic interval screening and maps, NOT a Cox model refit,
# [FRAF-P2 DIAG-X archive] an independent erosion model, or automatic mechanism identification.
# [FRAF-P2 DIAG-X archive] CODE INTEGRITY: these archive annotations are comment-only; QGIS parameters,
# [FRAF-P2 DIAG-X archive] active R statements, calculations and output names are intact.
# [FRAF-P2 DIAG-X archive] The script retains its original QGIS Processing display name and log labels
# [FRAF-P2 DIAG-X archive] so the archive can be related to historical runs without relabelling them.
# [FRAF-P2 DIAG-X archive]
##Write_interval_channel_layers=boolean TRUE

# FRAF Step 3B.2 — Mamore Exceptional Reactivation Mapper v1.3
# DATED-OUTLINE VERSION
#
# This version does NOT require a pre-built channel chronology layer.
# It scans a directory of dated channel-outline files / GeoPackage layers,
# parses dates from filenames or layer names, and builds the chronology
# internally.
#
# Recognised date patterns include:
#   YYYY_MM_DD
#   YYYY-MM-DD
#   YYYYMMDD
#   YYYY
#
# For a multi-layer GeoPackage, every layer is inspected. A date in the layer
# name takes priority over the file name.
#
# The four exceptional DS->AD intervals are identified from the Step 3B risk
# table itself. For each interval, the mapper writes:
#   * channel_start
#   * channel_end
#   * historic_AD_before
#   * distal DS->AD
#   * coincident distal SF->AD
# and attributes each distal event to earlier channel occupation.

# [FRAF-P2 DIAG-X archive] EXECUTION INPUTS: an interval-long Risk Table; fixed PLACE polygons;
# [FRAF-P2 DIAG-X archive] and QGIS-selected dated channel-outline layers for the Mamore reach.
# [FRAF-P2 DIAG-X archive] The Risk Table and PLACE geometry must use corresponding PLACE_IDs and
# [FRAF-P2 DIAG-X archive] consistent spatial coverage; the script does not independently verify
# [FRAF-P2 DIAG-X archive] river identity or enforce complete risk-to-geometry matching.
# [FRAF-P2 DIAG-X archive] Distance and clustering settings are stated in metres: a suitable
# [FRAF-P2 DIAG-X archive] projected, metre-unit CRS is an analyst prerequisite, not a code assertion.
# [FRAF-P2 DIAG-X archive]
options(stringsAsFactors=FALSE, warn=1)
dir.create(Output_directory, recursive=TRUE, showWarnings=FALSE)

if (!requireNamespace("sf", quietly=TRUE))
  stop("Package 'sf' is required.")

msg <- function(...) { cat(paste0(...), "\n"); flush.console() }
msg("[Step 3B.2 v1.3] EXCEPTION_QA script started.")
safe_num <- function(x) suppressWarnings(as.numeric(as.character(x)))
write_csv_safe <- function(x, fn)
  utils::write.csv(x, file.path(Output_directory, fn), row.names=FALSE, na="")

# [FRAF-P2 DIAG-X archive] AUTO FIELD RESOLUTION: identify risk-table fields by several historical
# [FRAF-P2 DIAG-X archive] aliases. Resolved names are written to 00_field_resolution_and_parameters.csv.
# [FRAF-P2 DIAG-X archive] Review this audit if upstream field definitions or Risk Table versions changed.
# [FRAF-P2 DIAG-X archive]
pick_field <- function(nms, requested, candidates=character(), required=TRUE) {
  if (!is.null(requested) && length(requested)==1L && !is.na(requested) &&
      nzchar(requested) && !toupper(trimws(requested)) %in% c("AUTO","NONE")) {
    hit <- nms[toupper(nms)==toupper(trimws(requested))]
    if (length(hit)) return(hit[1])
    if (required) stop("Requested field not found: ",requested)
    return(NA_character_)
  }
  up <- toupper(nms)
  for (cand in candidates) {
    j <- match(toupper(cand),up)
    if (!is.na(j)) return(nms[j])
  }
  if (required)
    stop("Could not auto-detect required field. Tried: ",
         paste(candidates,collapse=", "))
  NA_character_
}

# [FRAF-P2 DIAG-X archive] RISK INPUT: CSV/TXT, RDS and common OGR vector/table formats are supported.
# [FRAF-P2 DIAG-X archive] For multipurpose GeoPackages the selected layer should be verified; this
# [FRAF-P2 DIAG-X archive] reader does not explicitly request a named Risk Table layer.
# [FRAF-P2 DIAG-X archive]
read_table <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("csv","txt"))
    return(utils::read.csv(path,check.names=FALSE))
  if (ext=="rds") return(readRDS(path))
  if (ext %in% c("gpkg","shp","geojson","sqlite"))
    return(sf::st_drop_geometry(sf::st_read(path,quiet=TRUE)))
  stop("Unsupported risk table input: ",path)
}

# [FRAF-P2 DIAG-X archive] PLACE GEOMETRY: sf object or readable vector reference. Geometry and PLACE_ID
# [FRAF-P2 DIAG-X archive] are needed for mapping and former-channel intersection, not for event coding.
# [FRAF-P2 DIAG-X archive]
as_sf_input <- function(x) {
  if (inherits(x,"sf")) return(x)
  path <- as.character(x)[1]
  z <- sf::st_read(path,quiet=TRUE)
  if (!inherits(z,"sf")) stop("Place geometry input is not spatial.")
  z
}

fmt_time <- function(z) {
  ifelse(is.finite(z),
         format(round(z,6),trim=TRUE,scientific=FALSE),
         NA_character_)
}

# [FRAF-P2 DIAG-X archive] COVERAGE EXCLUSION PARAMETER: parse excluded calendar START years,
# [FRAF-P2 DIAG-X archive] default 1986, to prevent incomplete channel-outline coverage from being
# [FRAF-P2 DIAG-X archive] interpreted as evidence for exceptional geomorphic reoccupation.
# [FRAF-P2 DIAG-X archive] This does not erase those intervals from the diagnostic summary.
# [FRAF-P2 DIAG-X archive]
parse_year_list <- function(x) {
  if (is.null(x) || length(x)==0 || is.na(x) || !nzchar(trimws(x)) ||
      toupper(trimws(x)) %in% c("AUTO","NONE"))
    return(integer(0))
  vals <- trimws(unlist(strsplit(as.character(x), "[,;]")))
  vals <- vals[nzchar(vals)]
  yy <- suppressWarnings(as.integer(vals))
  if (any(!is.finite(yy)))
    stop("Exclude_calendar_start_years must contain YYYY values separated by commas or semicolons.")
  unique(yy)
}

# Parse a date from text. Returns POSIX Date or NA.
# [FRAF-P2 DIAG-X archive] CHRONOLOGY BACKSTOP: recognise YYYY-MM-DD, YYYY_MM_DD, YYYYMMDD and YYYY.
# [FRAF-P2 DIAG-X archive] A bare YYYY is assigned January 1; do not claim day-level precision for it.
# [FRAF-P2 DIAG-X archive]
parse_date_from_text <- function(txt) {
  s <- basename(as.character(txt))

  # YYYY_MM_DD or YYYY-MM-DD
  m <- regexpr("(19|20)[0-9]{2}[-_][01][0-9][-_][0-3][0-9]",s,perl=TRUE)
  if (m[1]>0) {
    v <- regmatches(s,m)
    v <- gsub("_","-",v)
    d <- suppressWarnings(as.Date(v,"%Y-%m-%d"))
    if (!is.na(d)) return(d)
  }

  # YYYYMMDD
  m <- regexpr("(19|20)[0-9]{6}",s,perl=TRUE)
  if (m[1]>0) {
    v <- regmatches(s,m)
    d <- suppressWarnings(as.Date(v,"%Y%m%d"))
    if (!is.na(d)) return(d)
  }

  # Bare year as last resort
  m <- regexpr("(19|20)[0-9]{2}",s,perl=TRUE)
  if (m[1]>0) {
    y <- regmatches(s,m)
    d <- suppressWarnings(as.Date(paste0(y,"-01-01")))
    if (!is.na(d)) return(d)
  }
  as.Date(NA)
}

# [FRAF-P2 DIAG-X archive] CALENDAR CONVENTION: fraction of the actual calendar year elapsed from Jan 1;
# [FRAF-P2 DIAG-X archive] leap-year durations are accounted for when deriving decimal chronology.
# [FRAF-P2 DIAG-X archive]
decimal_year <- function(d) {
  if (is.na(d)) return(NA_real_)
  y <- as.integer(format(d,"%Y"))
  y0 <- as.Date(sprintf("%04d-01-01",y))
  y1 <- as.Date(sprintf("%04d-01-01",y+1))
  y + as.numeric(d-y0)/as.numeric(y1-y0)
}

# -------------------------------------------------------------------------
# Build chronology from QGIS-selected dated channel outline layers
# -------------------------------------------------------------------------
# [FRAF-P2 DIAG-X archive] INPUT SOURCE PROVENANCE: preserve any available selected-layer/source label.
# [FRAF-P2 DIAG-X archive] For already-instantiated sf objects this label may be a generic fallback.
# [FRAF-P2 DIAG-X archive]
extract_source_label <- function(z, fallback) {
  candidates <- c("name","layer_name","source","dsn","path","filename")
  for (nm in candidates) {
    a <- attr(z,nm,exact=TRUE)
    if (!is.null(a) && length(a) && nzchar(as.character(a)[1]))
      return(as.character(a)[1])
  }
  fallback
}

# [FRAF-P2 DIAG-X archive] EXPLICIT DATE OVERRIDE: Channel_outline_years must give one date/year per
# [FRAF-P2 DIAG-X archive] selected outline in the same sequence; otherwise AUTO field/name parsing.
# [FRAF-P2 DIAG-X archive]
parse_manual_outline_dates <- function(x, n_expected) {
  if (is.null(x) || length(x)==0 || is.na(x) || !nzchar(trimws(x)) ||
      toupper(trimws(x))=="AUTO")
    return(rep(as.Date(NA), n_expected))

  vals <- trimws(unlist(strsplit(x, "[,;]")))
  vals <- vals[nzchar(vals)]

  if (length(vals)!=n_expected)
    stop("Channel_outline_years contains ", length(vals),
         " values but ", n_expected, " channel outlines were selected. ",
         "Supply one year/date per selected outline, in the same order.")

  out <- rep(as.Date(NA), length(vals))
  for (i in seq_along(vals)) {
    v <- vals[i]
    d <- suppressWarnings(as.Date(v))
    if (is.na(d) && grepl("^[0-9]{4}$", v))
      d <- as.Date(paste0(v, "-01-01"))
    if (is.na(d) && grepl("^[0-9]{8}$", v))
      d <- suppressWarnings(as.Date(v, "%Y%m%d"))
    if (is.na(d))
      stop("Could not parse Channel_outline_years value: ", v,
           ". Use YYYY or YYYY-MM-DD.")
    out[i] <- d
  }
  out
}

# [FRAF-P2 DIAG-X archive] QGIS MULTIPLE-VECTOR NORMALISATION: handle selected sf objects or vector
# [FRAF-P2 DIAG-X archive] references; despite legacy introductory wording this routine does not
# [FRAF-P2 DIAG-X archive] crawl an arbitrary folder of outlines by itself.
# [FRAF-P2 DIAG-X archive]
normalise_multiple_vectors <- function(x) {
  # QGIS may supply a list of sf objects, a single sf object, a character
  # vector of datasource references, or a semicolon-delimited character string.
  if (inherits(x,"sf")) return(list(x))
  if (is.list(x) && length(x)) return(x)
  if (is.character(x)) {
    vals <- x
    if (length(vals)==1 && grepl(";",vals,fixed=TRUE))
      vals <- strsplit(vals,";",fixed=TRUE)[[1]]
    vals <- trimws(vals)
    vals <- vals[nzchar(vals)]
    return(as.list(vals))
  }
  stop("Channel_outlines was not received as a usable multiple-vector input.")
}

# [FRAF-P2 DIAG-X archive] SELECTED OUTLINE LOADER: accepts a path or a path|layername=... reference.
# [FRAF-P2 DIAG-X archive] Each selected layer is handled as a dated channel-outline observation.
# [FRAF-P2 DIAG-X archive]
read_selected_outline <- function(obj, i) {
  if (inherits(obj,"sf")) {
    z <- obj
    label <- extract_source_label(z,paste0("selected_channel_",i))
    return(list(sf=z,label=label))
  }

  ref <- as.character(obj)[1]
  if (!nzchar(ref)) stop("Empty channel outline reference at position ",i)

  # QGIS/OGR references can sometimes be path|layername=...
  layer_name <- NA_character_
  path <- ref
  if (grepl("\\|layername=",ref,ignore.case=TRUE)) {
    bits <- strsplit(ref,"\\|layername=",perl=TRUE)[[1]]
    path <- bits[1]
    if (length(bits)>1) layer_name <- bits[2]
  }

  z <- if (!is.na(layer_name)) {
    sf::st_read(path,layer=layer_name,quiet=TRUE)
  } else {
    sf::st_read(path,quiet=TRUE)
  }
  label <- if (!is.na(layer_name)) layer_name else basename(path)
  list(sf=z,label=label)
}

# [FRAF-P2 DIAG-X archive] YEAR/DATE ASSIGNMENT: priority to the requested attribute, then recognised
# [FRAF-P2 DIAG-X archive] date-field aliases, then a date in the selected layer/source name.
# [FRAF-P2 DIAG-X archive] Multiple different calendar years in an explicit year field are rejected.
# [FRAF-P2 DIAG-X archive]
detect_outline_date <- function(z, label, year_field_request="YEAR") {
  nms <- names(z)

  req <- trimws(as.character(year_field_request)[1])
  if (!nzchar(req) || toupper(req)=="AUTO")
    req <- "YEAR"

  # First preference: requested per-layer year/date field.
  hit <- nms[toupper(nms)==toupper(req)]
  if (length(hit)) {
    vals <- z[[hit[1]]]
    vals <- vals[!is.na(vals)]
    if (!length(vals))
      stop("Channel year field ",hit[1]," is present but contains no values in ",label)

    # Require one unique year/date per selected outline layer.
    u <- unique(as.character(vals))
    u <- u[nzchar(trimws(u))]
    if (!length(u))
      stop("Channel year field ",hit[1]," contains no usable values in ",label)

    if (length(u)>1) {
      # If values are dates within the same calendar year, accept that year.
      yy <- suppressWarnings(as.integer(substr(u,1,4)))
      yy <- yy[is.finite(yy)]
      if (!length(yy) || length(unique(yy))>1)
        stop("Channel outline ",label," contains multiple different values in ",
             hit[1],": ",paste(head(u,10),collapse=", "),
             ". Each selected channel outline should represent one year.")
      y <- unique(yy)[1]
    } else {
      raw <- trimws(u[1])
      # Bare YYYY
      if (grepl("^[0-9]{4}$", raw)) {
        y <- as.integer(raw)
      } else {
        # Numeric YYYY stored as e.g. 1984.0
        yn <- suppressWarnings(as.numeric(raw))
        if (is.finite(yn) && yn>=1900 && yn<=2100) {
          y <- as.integer(round(yn))
        } else {
          d <- suppressWarnings(as.Date(raw))
          if (is.na(d))
            stop("Could not interpret ",hit[1]," value '",raw,
                 "' in ",label," as YYYY or a date.")
          return(list(date=d, source=paste0("field:",hit[1])))
        }
      }
    }

    if (!is.finite(y) || y<1900 || y>2100)
      stop("Implausible channel year ",y," in ",label)

    return(list(
      date=as.Date(sprintf("%04d-01-01",y)),
      source=paste0("field:",hit[1])
    ))
  }

  # AUTO fallback candidates if requested field is absent.
  dcands <- c("YEAR","YR","CH_YEAR","OBS_YEAR","DATE","CH_DATE","OBS_DATE","CHANNEL_DATE")
  for (cand in dcands) {
    hit2 <- nms[toupper(nms)==cand]
    if (!length(hit2)) next
    vals <- z[[hit2[1]]]
    vals <- vals[!is.na(vals)]
    if (!length(vals)) next
    raw <- trimws(as.character(vals[1]))

    if (grepl("^[0-9]{4}$", raw)) {
      y <- as.integer(raw)
      return(list(date=as.Date(sprintf("%04d-01-01",y)),
                  source=paste0("field:",hit2[1])))
    }

    yn <- suppressWarnings(as.numeric(raw))
    if (is.finite(yn) && yn>=1900 && yn<=2100) {
      y <- as.integer(round(yn))
      return(list(date=as.Date(sprintf("%04d-01-01",y)),
                  source=paste0("field:",hit2[1])))
    }

    d <- suppressWarnings(as.Date(raw))
    if (!is.na(d))
      return(list(date=d,source=paste0("field:",hit2[1])))
  }

  # Last resort: selected layer/source label.
  d <- parse_date_from_text(label)
  list(date=d,source="layer/source name")
}

# [FRAF-P2 DIAG-X archive] CHRONOLOGY CONSTRUCTION: validate every selected outline, record whether it
# [FRAF-P2 DIAG-X archive] was used in 00_channel_outline_manifest.csv, transform to PLACE CRS, make
# [FRAF-P2 DIAG-X archive] valid, and union all outlines for each observation date.
# [FRAF-P2 DIAG-X archive] An unusable individual outline is recorded and skipped; none usable is fatal.
# [FRAF-P2 DIAG-X archive] Check the manifest before using the inferred interval/outline matches.
# [FRAF-P2 DIAG-X archive]
build_channel_chronology <- function(selected_layers, target_crs, year_field_request="YEAR", manual_years="AUTO") {
  items <- normalise_multiple_vectors(selected_layers)
  if (!length(items)) stop("No channel outline layers were selected.")
  manual_dates <- parse_manual_outline_dates(manual_years, length(items))

  manifest <- list()
  objects <- list()

  for (i in seq_along(items)) {
    r <- try(read_selected_outline(items[[i]],i),silent=TRUE)
    if (inherits(r,"try-error")) {
      manifest[[i]] <- data.frame(
        selection_index=i, source_label=paste0("selection_",i),
        parsed_date="", parsed_decimal_year=NA_real_,
        date_source="", used=FALSE, feature_count=NA_integer_,
        message=as.character(r), stringsAsFactors=FALSE)
      next
    }

    z <- r$sf
    label <- r$label

    if (!is.na(manual_dates[i])) {
      dd <- list(date=manual_dates[i], source="Channel_outline_years parameter")
    } else {
      dd <- try(detect_outline_date(z,label,year_field_request),silent=TRUE)
      if (inherits(dd,"try-error")) {
        manifest[[i]] <- data.frame(
          selection_index=i, source_label=label,
          parsed_date="", parsed_decimal_year=NA_real_,
          date_source="", used=FALSE, feature_count=nrow(z),
          message=as.character(dd), stringsAsFactors=FALSE
        )
        next
      }
    }

    d <- dd$date
    if (is.na(d)) {
      manifest[[i]] <- data.frame(
        selection_index=i, source_label=label,
        parsed_date="", parsed_decimal_year=NA_real_,
        date_source=dd$source, used=FALSE, feature_count=nrow(z),
        message="Could not resolve a date from field or layer/source name.",
        stringsAsFactors=FALSE)
      next
    }

    if (!inherits(z,"sf") || !nrow(z)) {
      manifest[[i]] <- data.frame(
        selection_index=i, source_label=label,
        parsed_date=as.character(d), parsed_decimal_year=decimal_year(d),
        date_source=dd$source, used=FALSE, feature_count=nrow(z),
        message="Layer is empty or not sf.", stringsAsFactors=FALSE)
      next
    }

    if (is.na(sf::st_crs(z))) {
      manifest[[i]] <- data.frame(
        selection_index=i, source_label=label,
        parsed_date=as.character(d), parsed_decimal_year=decimal_year(d),
        date_source=dd$source, used=FALSE, feature_count=nrow(z),
        message="Undefined CRS.", stringsAsFactors=FALSE)
      next
    }

    if (sf::st_crs(z)!=target_crs)
      z <- sf::st_transform(z,target_crs)

    z <- sf::st_make_valid(z)
    geom <- suppressWarnings(sf::st_union(z))

    zz <- sf::st_sf(
      data.frame(
        CH_DATE=as.Date(d),
        CH_DEC_YEAR=decimal_year(d),
        CH_SOURCE=label,
        stringsAsFactors=FALSE
      ),
      geometry=sf::st_sfc(geom,crs=target_crs)
    )
    objects[[length(objects)+1L]] <- zz

    manifest[[i]] <- data.frame(
      selection_index=i, source_label=label,
      parsed_date=as.character(d), parsed_decimal_year=decimal_year(d),
      date_source=dd$source, used=TRUE, feature_count=nrow(z),
      message="", stringsAsFactors=FALSE)
  }

  man <- do.call(rbind,manifest)
  write_csv_safe(man,"00_channel_outline_manifest.csv")

  if (!length(objects))
    stop("None of the selected channel layers had a resolvable date. ",
         "See 00_channel_outline_manifest.csv.")

  ch <- do.call(rbind,objects)

  # One authoritative selected outline per date is preferred. If the user
  # deliberately selects more than one layer for the same date, union them
  # and make this explicit in the manifest/CH_SOURCE field.
  dates <- sort(unique(ch$CH_DATE))
  out <- vector("list",length(dates))
  for (i in seq_along(dates)) {
    z <- ch[ch$CH_DATE==dates[i],,drop=FALSE]
    u <- suppressWarnings(sf::st_union(z))
    out[[i]] <- sf::st_sf(
      data.frame(
        CH_DATE=dates[i],
        CH_DEC_YEAR=decimal_year(dates[i]),
        CH_SOURCE=paste(unique(z$CH_SOURCE),collapse="; "),
        stringsAsFactors=FALSE
      ),
      geometry=sf::st_sfc(u,crs=target_crs)
    )
  }

  do.call(rbind,out)
}

# -------------------------------------------------------------------------
# Read risk / place inputs
# -------------------------------------------------------------------------
# [FRAF-P2 DIAG-X archive] BEGIN INPUT CROSSWALK: event and exposure variables are obtained from the
# [FRAF-P2 DIAG-X archive] supplied longitudinal Risk Table; spatial intersections use PLACE polygons.
# [FRAF-P2 DIAG-X archive] This diagnostic does not create/reclassify authoritative states or events.
# [FRAF-P2 DIAG-X archive]
risk <- read_table(Risk_table)
places <- as_sf_input(Place_geometry)

if (is.na(sf::st_crs(places))) stop("Place geometry CRS is undefined.")

rn <- names(risk)
pn <- names(places)

# Project default PLACE_ID but permit equivalent fallback.
pid_req_r <- Place_id_field
pid_req_p <- Place_id_field
if (toupper(trimws(Place_id_field))=="PLACE_ID" && !"PLACE_ID" %in% toupper(rn))
  pid_req_r <- "AUTO"
if (toupper(trimws(Place_id_field))=="PLACE_ID" && !"PLACE_ID" %in% toupper(pn))
  pid_req_p <- "AUTO"

# [FRAF-P2 DIAG-X archive] KEY SELECTION: PLACE_ID is preferred, with historical ID aliases available.
# [FRAF-P2 DIAG-X archive] Matching numeric labels alone is not proof of identical PLACE geometry.
# [FRAF-P2 DIAG-X archive]
pid_r <- pick_field(rn,pid_req_r,c("PLACE_ID","BLOCK_ID","CELL_ID","ID"),TRUE)
pid_p <- pick_field(pn,pid_req_p,c("PLACE_ID","BLOCK_ID","CELL_ID","ID"),TRUE)

# [FRAF-P2 DIAG-X archive] EVENT FAMILIES: DS->AD uses STORAGE_REWORK_EVT; SF->AD uses REACTIVATE_EVT.
# [FRAF-P2 DIAG-X archive] Risk-set names can be resolved but are NOT used to filter the event frame
# [FRAF-P2 DIAG-X archive] below. Interpret results as event-based mapping, not exposure-adjusted rates.
# [FRAF-P2 DIAG-X archive]
ds_evt_f <- pick_field(rn,Event_DS_AD_field,
                       c("STORAGE_REWORK_EVT","STORAGE_REWORK_EVT_PRIMARY",
                         "DS_AD_EVENT","DS_TO_AD_EVENT"),TRUE)
ds_risk_f <- pick_field(rn,Risk_DS_AD_field,
                        c("STORAGE_REWORK_RISK_SET","STORAGE_REWORK_RISK_SET_PRIMARY",
                          "DS_AD_RISK_SET","DS_TO_AD_RISK_SET"),FALSE)
sf_evt_f <- pick_field(rn,Event_SF_AD_field,
                       c("REACTIVATE_EVT","REACTIVATE_EVT_PRIMARY",
                         "SF_AD_EVENT","SF_TO_AD_EVENT"),TRUE)
sf_risk_f <- pick_field(rn,Risk_SF_AD_field,
                        c("REACTIVATE_RISK_SET","REACTIVATE_RISK_SET_PRIMARY",
                          "SF_AD_RISK_SET","SF_TO_AD_RISK_SET"),FALSE)
margin_f <- pick_field(rn,Margin_distance_field,
                       c("DIST_CHANNEL_PREV","DIST_BANK_PREV","DIST_ACTIVE_CURR",
                         "DIST_WATER_CURR","BANK_SETBACK_PREV"),TRUE)
start_f <- pick_field(rn,Start_time_field,
                      c("TSTART_YR","TSTART","START_TIME",
                        "INTERVAL_START_RANK","START_RANK"),TRUE)
stop_f <- pick_field(rn,Stop_time_field,
                     c("TSTOP_YR","TSTOP","STOP_TIME",
                       "INTERVAL_END_RANK","END_RANK"),TRUE)
interval_f <- pick_field(rn,Interval_field,
                         c("INTERVAL_LABEL","INTERVAL","STEP","STEP_ID","PERIOD",
                           "YEAR_PAIR","INTERVAL_ID","INTERVAL_NAME"),FALSE)

# [FRAF-P2 DIAG-X archive] The selected channel-outline chronology is explicitly rebuilt from the input
# [FRAF-P2 DIAG-X archive] layers. Source dates, unioned geometries and CRS control all later
# [FRAF-P2 DIAG-X archive] historical-overlap interpretation.
# [FRAF-P2 DIAG-X archive]
chan <- build_channel_chronology(Channel_outlines,
                                 sf::st_crs(places),
                                 Channel_year_field,
                                 Channel_outline_years)

# -------------------------------------------------------------------------
# Risk-event frame
# -------------------------------------------------------------------------
# [FRAF-P2 DIAG-X archive] EVENT FRAME: retain PLACE, DS->AD and SF->AD flags, interval timing, and
# [FRAF-P2 DIAG-X archive] specified margin distance. No new event is inferred by this mapper.
# [FRAF-P2 DIAG-X archive]
rr <- data.frame(
  PLACE_ID=as.character(risk[[pid_r]]),
  DS_AD_EVENT=safe_num(risk[[ds_evt_f]]),
  SF_AD_EVENT=safe_num(risk[[sf_evt_f]]),
  MARGIN_DIST_M=safe_num(risk[[margin_f]]),
  TSTART=safe_num(risk[[start_f]]),
  TSTOP=safe_num(risk[[stop_f]]),
  stringsAsFactors=FALSE
)
if (!is.na(ds_risk_f)) rr$DS_AD_RISK_SET <- safe_num(risk[[ds_risk_f]])
if (!is.na(sf_risk_f)) rr$SF_AD_RISK_SET <- safe_num(risk[[sf_risk_f]])
if (!is.na(interval_f)) {
  rr$INTERVAL_ID <- as.character(risk[[interval_f]])
} else {
  rr$INTERVAL_ID <- paste0(fmt_time(rr$TSTART)," -> ",fmt_time(rr$TSTOP))
}

# [FRAF-P2 DIAG-X archive] INCLUSION FILTER: removes risk rows without finite margin distance or valid
# [FRAF-P2 DIAG-X archive] numeric start/stop; the script does not separately export their counts.
# [FRAF-P2 DIAG-X archive] Review whether this completeness restriction materially affects a reach.
# [FRAF-P2 DIAG-X archive]
rr <- rr[is.finite(rr$MARGIN_DIST_M) &
         is.finite(rr$TSTART) & is.finite(rr$TSTOP),,drop=FALSE]
# [FRAF-P2 DIAG-X archive] DISTAL CRITERION: strictly greater than the user-set distance (default
# [FRAF-P2 DIAG-X archive] 1000 m). DS->AD and SF->AD are distinguished by their own event flags;
# [FRAF-P2 DIAG-X archive] the same distance threshold is used only for diagnostic screening.
# [FRAF-P2 DIAG-X archive]
rr$DS_DISTAL <- rr$DS_AD_EVENT==1 & rr$MARGIN_DIST_M>Distal_threshold_m
rr$SF_DISTAL <- rr$SF_AD_EVENT==1 & rr$MARGIN_DIST_M>Distal_threshold_m

dsev <- rr[rr$DS_AD_EVENT==1,,drop=FALSE]
if (!nrow(dsev)) stop("No DS->AD events found.")

# Exceptional interval summary.
# [FRAF-P2 DIAG-X archive] INTERVAL SCREENING: count all DS->AD events and distal DS->AD events per
# [FRAF-P2 DIAG-X archive] observation interval; summarise median, 95th-percentile and maximum distance.
# [FRAF-P2 DIAG-X archive] The exceptional-interval decision is made from this event frame.
# [FRAF-P2 DIAG-X archive]
a <- aggregate(DS_AD_EVENT~INTERVAL_ID,dsev,sum); names(a)[2] <- "DS_AD_EVENTS"
b <- aggregate(DS_DISTAL~INTERVAL_ID,dsev,sum); names(b)[2] <- "DS_AD_DISTAL_EVENTS"
ts <- aggregate(TSTART~INTERVAL_ID,dsev,min)
te <- aggregate(TSTOP~INTERVAL_ID,dsev,max)
dm <- aggregate(MARGIN_DIST_M~INTERVAL_ID,dsev,median); names(dm)[2] <- "EVENT_DIST_MEDIAN_M"
d95 <- aggregate(MARGIN_DIST_M~INTERVAL_ID,dsev,
                 function(v) as.numeric(quantile(v,.95,na.rm=TRUE,names=FALSE)))
names(d95)[2] <- "EVENT_DIST_P95_M"
dx <- aggregate(MARGIN_DIST_M~INTERVAL_ID,dsev,max); names(dx)[2] <- "EVENT_DIST_MAX_M"

ints <- Reduce(function(u,v) merge(u,v,by="INTERVAL_ID",all=TRUE),
               list(a,b,ts,te,dm,d95,dx))
ints$DS_AD_DISTAL_FRACTION <- ints$DS_AD_DISTAL_EVENTS/ints$DS_AD_EVENTS

# Infer calendar years before exceptional-interval selection so incomplete
# start-channel years can be explicitly excluded from geomorphic attribution.
# [FRAF-P2 DIAG-X archive] TIME RECONCILIATION: offset elapsed Risk Table time using the earliest
# [FRAF-P2 DIAG-X archive] channel observation. This assumes compatible temporal origins and does not
# [FRAF-P2 DIAG-X archive] by itself establish an exact mapping of every individual interval.
# [FRAF-P2 DIAG-X archive] See 02_interval_to_channel_date_matching.csv for deviations.
# [FRAF-P2 DIAG-X archive]
risk_origin <- min(rr$TSTART,na.rm=TRUE)
channel_origin <- min(chan$CH_DEC_YEAR,na.rm=TRUE)
calendar_offset <- channel_origin-risk_origin
rr_to_calendar <- function(t) t+calendar_offset

ints$CAL_START_DEC_YEAR <- rr_to_calendar(ints$TSTART)
ints$CAL_STOP_DEC_YEAR <- rr_to_calendar(ints$TSTOP)
ints$CAL_START_YEAR <- floor(ints$CAL_START_DEC_YEAR + 1e-6)
ints$CAL_STOP_YEAR <- floor(ints$CAL_STOP_DEC_YEAR + 1e-6)

# Two routes into the exceptional set:
# A) >= minimum distal-event count AND >= minimum distal fraction; OR
# B) >= absolute distal-event count irrespective of distal fraction.
# Route B ensures a large episode such as 1991-1992 (91 distal events,
# ~19% distal fraction) is not omitted merely because the interval also
# contains many near-margin events.
# [FRAF-P2 DIAG-X archive] TWO ALTERNATIVE FLAG RULES: (A) distal count >= 25 AND distal fraction >=
# [FRAF-P2 DIAG-X archive] 0.25, OR (B) distal count >= 50 irrespective of fraction, at default settings.
# [FRAF-P2 DIAG-X archive] The absolute-count route protects large distal episodes with lower distal
# [FRAF-P2 DIAG-X archive] fractions from being missed (historical example: 1991-1992).
# [FRAF-P2 DIAG-X archive] These are transparent screening thresholds, not physically universal limits.
# [FRAF-P2 DIAG-X archive]
ints$EXCEPTIONAL_FRACTION_RULE <-
  ints$DS_AD_DISTAL_EVENTS >= Exceptional_interval_min_distal_events &
  ints$DS_AD_DISTAL_FRACTION >= Exceptional_interval_min_distal_fraction

ints$EXCEPTIONAL_ABSOLUTE_RULE <-
  ints$DS_AD_DISTAL_EVENTS >= Exceptional_interval_absolute_distal_events

ints$EXCEPTIONAL_RAW <-
  ints$EXCEPTIONAL_FRACTION_RULE | ints$EXCEPTIONAL_ABSOLUTE_RULE

# Explicit QA exclusion for calendar-start years with incomplete channel
# coverage. These intervals remain in the summary for transparency but are
# not mapped or used in geomorphic attribution.
excluded_years <- parse_year_list(Exclude_calendar_start_years)
# [FRAF-P2 DIAG-X archive] COVERAGE QA: intervals beginning in excluded years, default 1986, remain
# [FRAF-P2 DIAG-X archive] listed with reason TRUNCATED_START_CHANNEL_OUTLINE but are not selected for
# [FRAF-P2 DIAG-X archive] geomorphic attribution or mapping even if they meet the raw event threshold.
# [FRAF-P2 DIAG-X archive]
ints$EXCLUDE_GEOMORPHIC_ATTRIBUTION <-
  ints$CAL_START_YEAR %in% excluded_years
ints$EXCLUSION_REASON <- ifelse(
  ints$EXCLUDE_GEOMORPHIC_ATTRIBUTION,
  "TRUNCATED_START_CHANNEL_OUTLINE",
  ""
)

ints$EXCEPTIONAL <- ints$EXCEPTIONAL_RAW &
  !ints$EXCLUDE_GEOMORPHIC_ATTRIBUTION

ints <- ints[order(-ints$DS_AD_DISTAL_EVENTS,-ints$DS_AD_DISTAL_FRACTION),]
write_csv_safe(ints,"01_exceptional_interval_summary.csv")

# [FRAF-P2 DIAG-X archive] RETAINED EXCEPTIONAL INTERVALS: actual count and labels depend on the supplied
# [FRAF-P2 DIAG-X archive] Risk Table, distance field, threshold parameters and exclusions. The reference
# [FRAF-P2 DIAG-X archive] to four exceptional intervals is an observed analytical result, not hardcoded.
# [FRAF-P2 DIAG-X archive]
exceptional <- ints[ints$EXCEPTIONAL %in% TRUE,,drop=FALSE]
if (!nrow(exceptional)) stop("No non-excluded intervals met exceptional thresholds.")

excluded <- ints[ints$EXCEPTIONAL_RAW %in% TRUE &
                 ints$EXCLUDE_GEOMORPHIC_ATTRIBUTION %in% TRUE,,drop=FALSE]

msg("[Step 3B.2] Exceptional intervals retained for attribution: ",
    paste(exceptional$INTERVAL_ID,collapse="; "))
if (nrow(excluded))
  msg("[Step 3B.2] Exceptional intervals excluded by channel-coverage QA: ",
      paste(excluded$INTERVAL_ID,collapse="; "))

# -------------------------------------------------------------------------
# Join event rows to place geometry
# -------------------------------------------------------------------------
# [FRAF-P2 DIAG-X archive] SPATIAL EVENT JOIN: attach PLACE geometry to events from selected exceptional
# [FRAF-P2 DIAG-X archive] intervals by PLACE_ID. Verify uniqueness and matching outside this script:
# [FRAF-P2 DIAG-X archive] unmatched/duplicated IDs are not explicitly disallowed here.
# [FRAF-P2 DIAG-X archive]
pk <- places
pk$PLACE_ID_JOIN <- as.character(pk[[pid_p]])
pk <- pk[,c("PLACE_ID_JOIN",attr(pk,"sf_column")),drop=FALSE]

# [FRAF-P2 DIAG-X archive] Associated SF->AD events are drawn from the SAME selected observation
# [FRAF-P2 DIAG-X archive] intervals; they are not automatically tested for event-to-event coincidence.
# [FRAF-P2 DIAG-X archive]
event_rows <- rr[(rr$DS_AD_EVENT==1 | rr$SF_AD_EVENT==1) &
                 rr$INTERVAL_ID %in% exceptional$INTERVAL_ID,,drop=FALSE]

ev <- merge(event_rows,pk,by.x="PLACE_ID",by.y="PLACE_ID_JOIN",
            all.x=TRUE,sort=FALSE)
ev <- sf::st_as_sf(ev)

ds_all <- ev[ev$DS_AD_EVENT==1,,drop=FALSE]
ds_dist <- ev[ev$DS_DISTAL %in% TRUE,,drop=FALSE]
sf_dist <- ev[ev$SF_DISTAL %in% TRUE,,drop=FALSE]

# -------------------------------------------------------------------------
# Match model elapsed-time intervals to dated channel observations
# -------------------------------------------------------------------------
# The risk-table-to-calendar offset was established above so that exceptional
# intervals could be screened against known channel-coverage exclusions.
# [FRAF-P2 DIAG-X archive] CHANNEL DATE MATCHING: choose nearest available dated channel polygon at
# [FRAF-P2 DIAG-X archive] each inferred interval start/end. No tolerance is enforced. Always inspect
# [FRAF-P2 DIAG-X archive] START_ABS_DIFF_YR and END_ABS_DIFF_YR in the matching CSV.
# [FRAF-P2 DIAG-X archive]
nearest_channel <- function(target_dec_year) {
  j <- which.min(abs(chan$CH_DEC_YEAR-target_dec_year))
  chan[j,,drop=FALSE]
}

# [FRAF-P2 DIAG-X archive] FORMER AD OCCUPATION: union channel polygons strictly older than the inferred
# [FRAF-P2 DIAG-X archive] interval start, excluding the start-date outline itself.
# [FRAF-P2 DIAG-X archive] Such overlap is evidence of historical mapped occupation, not proof of a
# [FRAF-P2 DIAG-X archive] specific cutoff mechanism or sub-surface stratigraphic continuity.
# [FRAF-P2 DIAG-X archive]
historic_before <- function(target_dec_year) {
  chan[chan$CH_DEC_YEAR < target_dec_year-1e-6,,drop=FALSE]
}

# [FRAF-P2 DIAG-X archive] GEOPACKAGE OUTPUT: named event, start/end channel and former-AD review layers;
# [FRAF-P2 DIAG-X archive] empty layers are omitted rather than written with zero features.
# [FRAF-P2 DIAG-X archive]
write_layer <- function(x,layer,gpkg) {
  if (is.null(x) || !inherits(x,"sf") || !nrow(x)) return(invisible(FALSE))
  suppressWarnings(sf::st_write(x,gpkg,layer=layer,delete_layer=TRUE,quiet=TRUE))
  invisible(TRUE)
}
sanitize_layer <- function(x) substr(gsub("[^A-Za-z0-9_]+","_",x),1,45)

# [FRAF-P2 DIAG-X archive] ARCHIVE CAUTION: the script removes any pre-existing GeoPackage at this exact
# [FRAF-P2 DIAG-X archive] output path before writing. Use an appropriate run-specific output folder.
# [FRAF-P2 DIAG-X archive]
gpkg <- file.path(Output_directory,"Mamore_Exceptional_Reactivation_Review.gpkg")
if (file.exists(gpkg)) file.remove(gpkg)

all_ds <- list()
all_sf <- list()
cluster_rows <- list()
ci <- 0L
match_rows <- list()

# [FRAF-P2 DIAG-X archive] PER-INTERVAL MAPPING: select the nearest start/end channel outlines; construct
# [FRAF-P2 DIAG-X archive] unioned pre-existing channel occupation; enrich DS->AD/SF->AD distal events;
# [FRAF-P2 DIAG-X archive] cluster DS->AD event PLACEs; and export review layers.
# [FRAF-P2 DIAG-X archive]
for (ii in seq_len(nrow(exceptional))) {
  intid <- exceptional$INTERVAL_ID[ii]
  t0 <- exceptional$TSTART[ii]
  t1 <- exceptional$TSTOP[ii]

  cal0 <- rr_to_calendar(t0)
  cal1 <- rr_to_calendar(t1)
  ch0 <- nearest_channel(cal0)
  ch1 <- nearest_channel(cal1)
  hist <- historic_before(cal0)

# [FRAF-P2 DIAG-X archive] TIME-MATCH AUDIT: quantify decimal-year mismatch against selected channel
# [FRAF-P2 DIAG-X archive] observations. The code records these differences but does not abort when large.
# [FRAF-P2 DIAG-X archive]
  match_rows[[ii]] <- data.frame(
    INTERVAL_ID=intid,TSTART=t0,TSTOP=t1,
    EXPECTED_START_DEC_YEAR=cal0,
    MATCHED_START_DATE=as.character(ch0$CH_DATE[1]),
    MATCHED_START_DEC_YEAR=ch0$CH_DEC_YEAR[1],
    START_ABS_DIFF_YR=abs(ch0$CH_DEC_YEAR[1]-cal0),
    EXPECTED_END_DEC_YEAR=cal1,
    MATCHED_END_DATE=as.character(ch1$CH_DATE[1]),
    MATCHED_END_DEC_YEAR=ch1$CH_DEC_YEAR[1],
    END_ABS_DIFF_YR=abs(ch1$CH_DEC_YEAR[1]-cal1),
    stringsAsFactors=FALSE
  )

  ds_i <- ds_dist[ds_dist$INTERVAL_ID==intid,,drop=FALSE]
  sf_i <- sf_dist[sf_dist$INTERVAL_ID==intid,,drop=FALSE]

  hist_union <- NULL
  if (nrow(hist)) {
    hu <- suppressWarnings(sf::st_union(sf::st_make_valid(hist)))
    hist_union <- sf::st_sf(
      data.frame(ID=1),
      geometry=sf::st_sfc(hu,crs=sf::st_crs(places))
    )
  }

# [FRAF-P2 DIAG-X archive] FORMER_AD_OVERLAP: any intersection with mapped channel polygons predating
# [FRAF-P2 DIAG-X archive] the interval start. For polygon PLACEs, overlap proportion uses intersection
# [FRAF-P2 DIAG-X archive] area divided by PLACE area; point-like geometries use a binary indicator.
# [FRAF-P2 DIAG-X archive] Optional buffering broadens the historical occupation mask, not the event.
# [FRAF-P2 DIAG-X archive]
  enrich <- function(z) {
    if (!nrow(z)) return(z)
    z$FORMER_AD_OVERLAP <- FALSE
    z$FORMER_AD_OVERLAP_PROP <- 0
    if (!is.null(hist_union)) {
      target <- hist_union
      if (Former_AD_overlap_buffer_m!=0)
        target <- sf::st_buffer(target,Former_AD_overlap_buffer_m)
      hit <- lengths(sf::st_intersects(z,target))>0
      z$FORMER_AD_OVERLAP <- hit

      gt <- unique(as.character(sf::st_geometry_type(z)))
      if (all(grepl("POLYGON",gt))) {
        a0 <- as.numeric(sf::st_area(z))
        it <- suppressWarnings(sf::st_intersection(
          z[,c("PLACE_ID"),drop=FALSE],target))
        if (nrow(it)) {
          ia <- aggregate(as.numeric(sf::st_area(it)),
                          by=list(it$PLACE_ID),sum)
          names(ia) <- c("PLACE_ID","INT_AREA")
          m <- match(z$PLACE_ID,ia$PLACE_ID)
          z$FORMER_AD_OVERLAP_PROP <- ifelse(is.na(m),0,
                                             pmin(1,ia$INT_AREA[m]/a0))
        }
      } else {
        z$FORMER_AD_OVERLAP_PROP <- as.numeric(hit)
      }
    }
    z
  }

  ds_i <- enrich(ds_i)
  sf_i <- enrich(sf_i)

# [FRAF-P2 DIAG-X archive] CLUSTERS: centroid-to-centroid proximity (default 300 m) linked transitively
# [FRAF-P2 DIAG-X archive] by a flood-fill procedure. A connected component can span more than 300 m.
# [FRAF-P2 DIAG-X archive] The cluster ID alone does NOT identify a cutoff or an abandoned-loop process;
# [FRAF-P2 DIAG-X archive] mechanism attribution requires visual review of dated channel layers.
# [FRAF-P2 DIAG-X archive]
  # Spatial cluster IDs.
  if (nrow(ds_i)) {
    pts <- sf::st_centroid(sf::st_geometry(ds_i))
    xy <- sf::st_coordinates(pts)
    n <- nrow(ds_i)
    comp <- integer(n)
    cid <- 0L
    for (j in seq_len(n)) {
      if (comp[j]!=0) next
      cid <- cid+1L
      queue <- j; comp[j] <- cid
      while (length(queue)) {
        q <- queue[1]; queue <- queue[-1]
        dd <- (xy[,1]-xy[q,1])^2 + (xy[,2]-xy[q,2])^2
        nb <- which(dd<=Cluster_distance_m^2 & comp==0)
        if (length(nb)) {
          comp[nb] <- cid
          queue <- c(queue,nb)
        }
      }
    }
    ds_i$REACT_CLUSTER_ID <- paste0("R",sprintf("%02d",ii),"_",
                                    sprintf("%03d",comp))

    for (cl in unique(ds_i$REACT_CLUSTER_ID)) {
      z <- ds_i[ds_i$REACT_CLUSTER_ID==cl,,drop=FALSE]
      ci <- ci+1L
      cluster_rows[[ci]] <- data.frame(
        INTERVAL_ID=intid,
        REACT_CLUSTER_ID=cl,
        N_DS_AD_DISTAL=nrow(z),
        MEDIAN_MARGIN_DIST_M=median(z$MARGIN_DIST_M,na.rm=TRUE),
        MAX_MARGIN_DIST_M=max(z$MARGIN_DIST_M,na.rm=TRUE),
        N_FORMER_AD=sum(z$FORMER_AD_OVERLAP,na.rm=TRUE),
        PROP_FORMER_AD=mean(z$FORMER_AD_OVERLAP,na.rm=TRUE),
        MEAN_FORMER_AD_OVERLAP_PROP=mean(z$FORMER_AD_OVERLAP_PROP,na.rm=TRUE),
        stringsAsFactors=FALSE)
    }
  }

  all_ds[[ii]] <- ds_i
  all_sf[[ii]] <- sf_i

# [FRAF-P2 DIAG-X archive] SPATIAL REVIEW PACKAGE: for each interval export start/end channel,
# [FRAF-P2 DIAG-X archive] historic_AD_before, distal DS->AD and distal SF->AD layers where non-empty.
# [FRAF-P2 DIAG-X archive]
  tag <- paste0("I",ii,"_",sanitize_layer(intid))
  if (isTRUE(Write_interval_channel_layers)) {
    write_layer(ch0,paste0(tag,"_channel_start"),gpkg)
    write_layer(ch1,paste0(tag,"_channel_end"),gpkg)
    if (!is.null(hist_union))
      write_layer(hist_union,paste0(tag,"_historic_AD_before"),gpkg)
  }
  write_layer(ds_i,paste0(tag,"_DS_AD_distal"),gpkg)
  write_layer(sf_i,paste0(tag,"_SF_AD_distal"),gpkg)
}

# [FRAF-P2 DIAG-X archive] CORE QA CSV: 02_interval_to_channel_date_matching.csv includes inferred
# [FRAF-P2 DIAG-X archive] calendar interval times and nearest dated-outline matches. A good source
# [FRAF-P2 DIAG-X archive] manifest without good interval matches is insufficient for mechanism claims.
# [FRAF-P2 DIAG-X archive]
matches <- do.call(rbind,match_rows)
write_csv_safe(matches,"02_interval_to_channel_date_matching.csv")

# [FRAF-P2 DIAG-X archive] EVENT ATTRIBUTION TABLES: retain mapped distal events, source-event fields,
# [FRAF-P2 DIAG-X archive] former-AD overlap and DS->AD cluster identifiers for further inspection.
# [FRAF-P2 DIAG-X archive]
ds_enriched <- if (length(all_ds)) do.call(rbind,all_ds) else ds_dist[FALSE,]
sf_enriched <- if (length(all_sf)) do.call(rbind,all_sf) else sf_dist[FALSE,]

if (isTRUE(Write_all_event_layers))
  write_layer(ds_all,"DS_AD_all_events_exceptional_intervals",gpkg)
write_layer(ds_enriched,"DS_AD_distal_gt_threshold",gpkg)
write_layer(sf_enriched,"SF_AD_distal_gt_threshold",gpkg)

if (nrow(ds_enriched))
  write_csv_safe(sf::st_drop_geometry(ds_enriched),
                 "03_DS_AD_distal_event_attribution.csv")
if (nrow(sf_enriched))
  write_csv_safe(sf::st_drop_geometry(sf_enriched),
                 "04_SF_AD_distal_event_attribution.csv")
if (length(cluster_rows))
  write_csv_safe(do.call(rbind,cluster_rows),
                 "05_reactivation_cluster_summary.csv")

# Interval attribution.
# [FRAF-P2 DIAG-X archive] INTERVAL SUMMARY: proportion of mapped distal DS->AD and SF->AD events whose
# [FRAF-P2 DIAG-X archive] PLACE geometry overlaps older channel occupation. Geomorphic class labels
# [FRAF-P2 DIAG-X archive] (R1-R4) are not inferred or exported by these metrics.
# [FRAF-P2 DIAG-X archive]
summ <- exceptional
summ$N_DS_DISTAL_MAPPED <- 0L
summ$N_DS_FORMER_AD <- 0L
summ$PROP_DS_FORMER_AD <- NA_real_
summ$N_SF_DISTAL_MAPPED <- 0L
summ$N_SF_FORMER_AD <- 0L
summ$PROP_SF_FORMER_AD <- NA_real_

for (i in seq_len(nrow(summ))) {
  id <- summ$INTERVAL_ID[i]
  zd <- ds_enriched[ds_enriched$INTERVAL_ID==id,,drop=FALSE]
  zs <- sf_enriched[sf_enriched$INTERVAL_ID==id,,drop=FALSE]

  summ$N_DS_DISTAL_MAPPED[i] <- nrow(zd)
  if (nrow(zd)) {
    summ$N_DS_FORMER_AD[i] <- sum(zd$FORMER_AD_OVERLAP,na.rm=TRUE)
    summ$PROP_DS_FORMER_AD[i] <- mean(zd$FORMER_AD_OVERLAP,na.rm=TRUE)
  }
  summ$N_SF_DISTAL_MAPPED[i] <- nrow(zs)
  if (nrow(zs)) {
    summ$N_SF_FORMER_AD[i] <- sum(zs$FORMER_AD_OVERLAP,na.rm=TRUE)
    summ$PROP_SF_FORMER_AD[i] <- mean(zs$FORMER_AD_OVERLAP,na.rm=TRUE)
  }
}
write_csv_safe(summ,"06_interval_attribution_summary.csv")

# [FRAF-P2 DIAG-X archive] CONFIGURATION AUDIT: export the resolved input field aliases, thresholds,
# [FRAF-P2 DIAG-X archive] calendar offset, source-outline count and clustering distance.
# [FRAF-P2 DIAG-X archive] No source-file SHA-256 or QGIS run manifest is generated by the original code.
# [FRAF-P2 DIAG-X archive]
audit <- data.frame(
  item=c("risk_place_id","geometry_place_id",
         "DS_AD_event","SF_AD_event","margin_distance",
         "risk_start","risk_stop","risk_interval",
         "risk_origin","channel_origin","calendar_offset",
         "channel_outline_count","distal_threshold_m",
         "exceptional_min_distal_events","exceptional_min_distal_fraction",
         "exceptional_absolute_distal_events","exclude_calendar_start_years",
         "cluster_distance_m"),
  value=c(pid_r,pid_p,ds_evt_f,sf_evt_f,margin_f,start_f,stop_f,
          ifelse(is.na(interval_f),"constructed",interval_f),
          risk_origin,channel_origin,calendar_offset,
          nrow(chan),Distal_threshold_m,
          Exceptional_interval_min_distal_events,
          Exceptional_interval_min_distal_fraction,
          Exceptional_interval_absolute_distal_events,
          Exclude_calendar_start_years,
          Cluster_distance_m),
  stringsAsFactors=FALSE)
write_csv_safe(audit,"00_field_resolution_and_parameters.csv")

# [FRAF-P2 DIAG-X archive] ORIGINAL RUN README: describes how to inspect dated outlines and manually
# [FRAF-P2 DIAG-X archive] assign ordinary margin migration, former-channel reoccupation, cutoff-related
# [FRAF-P2 DIAG-X archive] reorganisation or unresolved/other. This taxonomy is not automated.
# [FRAF-P2 DIAG-X archive]
readme <- c(
  "FRAF Step 3B.2 Mamore Exceptional Reactivation Mapper v1.3",
  "DATED OUTLINE VERSION",
  "",
  "The script builds the channel chronology internally from the dated channel layers selected in QGIS.",
  "Check 00_channel_outline_manifest.csv first; it records every selected outline and resolved date.",
  "Check 02_interval_to_channel_date_matching.csv to ensure elapsed-time intervals",
  "have been matched to the correct calendar channel dates.",
  "",
  "Exceptional-interval inclusion uses either:",
  "  (a) the minimum distal-event count plus minimum distal fraction, OR",
  "  (b) the absolute distal-event count threshold irrespective of distal fraction.",
  "This retains large distal episodes such as 1991-1992.",
  "",
  "Intervals whose calendar start year is listed in Exclude_calendar_start_years",
  "remain in 01_exceptional_interval_summary.csv but are excluded from mapping",
  "and geomorphic attribution. Default 1986 exclusion reason:",
  "TRUNCATED_START_CHANNEL_OUTLINE.",
  "",
  "Key GeoPackage:",
  gpkg,
  "",
  "FORMER_AD_OVERLAP means the distal event intersects any channel outline",
  "strictly earlier than the interval-start matched calendar date.",
  "",
  "REACT_CLUSTER_ID is a proximity cluster, not an automatic geomorphic label.",
  "Use channel_start, channel_end and historic_AD_before to attribute clusters as:",
  "R1 ordinary margin migration",
  "R2 former-channel / abandoned-loop reoccupation",
  "R3 cutoff-associated reorganisation",
  "R4 unresolved/other."
)
writeLines(readme,file.path(Output_directory,"00_README_STEP3B2.txt"))

# [FRAF-P2 DIAG-X archive] COMPLETION LOG: successful script completion establishes only that the
# [FRAF-P2 DIAG-X archive] diagnostic outputs were written. Numerical agreement with Supplementary
# [FRAF-P2 DIAG-X archive] S6 Table S14 requires matching the original river-specific output CSVs and
# [FRAF-P2 DIAG-X archive] analyst review of the selected exceptional intervals.
# [FRAF-P2 DIAG-X archive]
msg("[Step 3B.2] Complete.")
msg("[Step 3B.2] Dated outlines read: ",nrow(chan))
msg("[Step 3B.2] Exceptional intervals mapped: ",nrow(exceptional))
msg("[Step 3B.2] Exceptional intervals excluded by QA: ",nrow(excluded))
msg("[Step 3B.2] GeoPackage: ",gpkg)
