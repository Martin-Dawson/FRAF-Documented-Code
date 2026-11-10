##FRAF Floodplain Reassemblage=group
##Cox Assemblage Memory Block Test v1.0=name
##RiskTable=file
##RiskLayerName=string Risk Table
##OutputFolder=folder
##ReachName=selection Mamoré;Jamuna
##MamoreReactivationExposure=selection Full-width channel-margin zone;Half-width channel-margin zone
##MamoreDSADSpatial=selection Linear previous-channel-margin;Linear previous-channel-margin + curvature
##IncludeCoverageControl=boolean TRUE
##IncludeMamorePriorReactivationCount=boolean FALSE

# ============================================================================
# REPOSITORY SOURCE FILE: FRAF_P2_06M_CoxMemoryComparison_v1_0.rsx
# FRAF Paper 2 | Supplementary explanatory Cox model comparison.
#
# ARCHIVAL PURPOSE / PROVENANCE
# - Documents the existing v1.0 implementation of the paired nested models;
#   it does not modify the analysis, its QGIS Processing parameter header, or
#   the Processing algorithm name displayed inside QGIS.
# - This is a secondary explanatory model comparison, not the parent historic
#   Cox estimation/prediction workflow and not a held-out forecasting test.
# - Source state/risk membership comes from the Stage 4 Step 3 Risk Table;
#   antecedent ASM_*_PREV variables were assembled upstream at interval start.
# - This module neither reconstructs the assemblage nor rebuilds risk sets.
# - Spatial coefficients are reach-specific; a shared variable name does not
#   imply identical geomorphic geometry or transferred hazard coefficients.
#
# SCIENTIFIC READING GUIDE
# - M0: selected spatial-exposure variables, optionally ASM_COV_FRAC_Z.
# - M1: exactly M0 plus the specified antecedent assemblage-history block.
# - Compare only within transition on the matched complete-case sample.
# - Cluster-robust history-block Wald p is the primary conditional test;
#   partial-likelihood LR p is conventional, not cluster-robust.
# - Delta AIC and delta concordance describe IN-SAMPLE fit and ranking;
#   they are not independent predictive-performance improvements.
# - Positive (AIC_M0 - AIC_M1) favours M1; positive (C_M1 - C_M0)
#   indicates greater concordance in the fitted matched sample.
#
# IMPORTANT IMPLEMENTATION SCOPE
# - The current code filters on transition-specific RISK_SET columns, but does
#   NOT explicitly filter M3_MODEL_ELIGIBLE_PRIMARY or individual transition-
#   specific model-eligibility fields. Confirm eligibility of supplied rows
#   against the authoritative historical analysis before publication use.
# - DS->AD can select a strict event/risk alias if primary columns exist but
#   have no positive entries. Record which alias was selected in the run log.
# - Cox PH assumptions, spatial independence beyond PLACE clustering, and
#   external transfer are not established by these block tests.
#
# FRAF Cox Assemblage Memory Block Test v1.0
# Purpose
#   Formal nested comparison of:
#     M0 = transition-specific spatial exposure (+ optional coverage control)
#     M1 = M0 + antecedent geomorphic-history block
#
#   The state condition is held fixed by each transition-specific risk set.
#   M0 and M1 are fitted to exactly the same complete-case rows, events and places.
#
# Principal transitions
#   1. Stabilised Floodplain -> Active Domain (SF->AD)
#   2. Depositional Storage -> Active Domain (DS->AD)
#   3. Depositional Storage -> Stabilised Floodplain (DS->SF)
#
# Broad Eligible-Floodplain -> AD is deliberately excluded because the current
# production broad risk population mixes resolved SF with left-censored
# pre-existing floodplain, for which the history variables are not observationally
# equivalent.
#
# Scientific alignment
#   - Jamuna SF->AD: linear interval-start Active-Domain-margin distance.
#   - Jamuna DS->AD: linear interval-start Active-Domain-margin distance.
#   - Jamuna DS->SF: log Active-Domain-margin distance.
#   - Mamoré SF->AD: lagged local near-channel/outer-bank/curvature exposure.
#   - Mamoré DS->AD: linear previous-channel-margin distance, with curvature only
#     when explicitly selected.
#   - Mamoré DS->SF: log previous-channel-margin distance.
#   - Jamuna SF->AD and DS->AD omit ASM_N_EPISODES_PREV in accordance with the
#     final v17.10.15 specification.
#   - Mamoré prior-reactivation count is excluded by default because it is known
#     to be separation-prone; it can be reintroduced as an explicit sensitivity.
#
# Inference
#   - Partial-likelihood LR and delta AIC describe added model fit.
#   - The primary inferential test is a joint robust Wald test of the history block,
#     using the cluster-robust covariance from coxph(... + cluster(PLACE_ID)).
#   - Delta concordance describes added ranking information.
#
# Memory safety
#   GeoPackage input is schema-inspected first and SQL-projected to only the
#   fields needed here. Rows are also restricted in SQL to the union of the three
#   state-specific risk populations before materialisation in R.
# ============================================================================

# -----------------------------
# 0. Startup
# -----------------------------
# OutputFolder is the required QGIS Processing folder argument. Create the
# destination before any modelling or diagnostic exports are attempted.
out_dir <- as.character(OutputFolder)[1]
if (is.na(out_dir) || !nzchar(trimws(out_dir))) stop("OutputFolder is empty.")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# QGIS selection parameters are commonly passed as zero-based integer indices;
# the same code also accepts a textual reach label for direct R invocation.
reach_raw <- as.character(ReachName)[1]
reach_index <- suppressWarnings(as.integer(reach_raw))
reach_label <- if (!is.na(reach_index)) {
  if (reach_index == 0L) "Mamoré" else "Jamuna"
} else if (grepl("jamuna", reach_raw, ignore.case = TRUE)) {
  "Jamuna"
} else {
  "Mamoré"
}

# Normalise Processing checkboxes to logicals. This prevents e.g. "0" being
# interpreted as TRUE simply because it is a non-empty character value.
as_flag <- function(x, default = FALSE) {
  if (length(x) == 0L || is.null(x) || all(is.na(x))) return(default)
  if (is.logical(x)) return(isTRUE(x[1]))
  sx <- toupper(trimws(as.character(x[1])))
  if (sx %in% c("TRUE", "T", "YES", "Y", "1")) return(TRUE)
  if (sx %in% c("FALSE", "F", "NO", "N", "0")) return(FALSE)
  iv <- suppressWarnings(as.integer(x[1]))
  if (!is.na(iv)) return(iv != 0L)
  default
}

# Keep the historically selected Mamoré geometry specification explicit in
# the run provenance, rather than silently choosing a model after fitting.
mamore_react_half <- suppressWarnings(as.integer(MamoreReactivationExposure)) == 1L
mamore_dsad_curvature <- suppressWarnings(as.integer(MamoreDSADSpatial)) == 1L
include_coverage <- as_flag(IncludeCoverageControl, TRUE)
include_mamore_react_count <- as_flag(IncludeMamorePriorReactivationCount, FALSE)

writeLines(
  c(
    paste0("FRAF Cox Assemblage Memory Block Test v1.0 started: ",
           format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
    paste0("Reach: ", reach_label),
    paste0("RiskTable: ", paste(as.character(RiskTable), collapse = " | ")),
    paste0("RiskLayerName: ", as.character(RiskLayerName)[1]),
    paste0("Coverage control in both models: ", include_coverage),
    paste0("Mamoré reactivation exposure: ",
           ifelse(mamore_react_half, "half-width", "full-width")),
    paste0("Mamoré DS->AD spatial model: ",
           ifelse(mamore_dsad_curvature,
                  "linear previous-channel-margin + curvature",
                  "linear previous-channel-margin")),
    paste0("Include Mamoré prior-reactivation count: ", include_mamore_react_count)
  ),
  file.path(out_dir, "00_RUN_STARTED.txt"),
  useBytes = TRUE
)

# 'sf' reads GeoPackage tables with SQL projection. 'survival' supplies Cox
# partial-likelihood fits, repeated-interval Surv(), and robust clustering.
.required_packages <- c("sf", "survival")
.missing_packages <- .required_packages[!vapply(
  .required_packages, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1)
)]
if (length(.missing_packages) > 0L) {
  stop("Missing required R package(s): ", paste(.missing_packages, collapse = ", "))
}
library("sf")
library("survival")

# sf geometry engine setting retained from the source; this analysis uses
# attribute-only Risk Table rows after the GeoPackage read.
sf::sf_use_s2(FALSE)

# -----------------------------
# 1. General helpers
# -----------------------------
# Numeric conversion is intentionally permissive for SQLite/QGIS type variants;
# downstream complete-case checks will remove non-finite predictor values.
num <- function(x) suppressWarnings(as.numeric(x))

# Convert TRUE/FALSE, text booleans and numeric event/risk indicators to 0/1.
# NOTE: missing/unrecognised values become 0 in this original implementation;
# the integrity check does not distinguish genuinely absent from negative flags.
int01 <- function(x) {
  if (is.logical(x)) {
    out <- as.integer(x)
  } else {
    sx <- toupper(trimws(as.character(x)))
    out <- suppressWarnings(as.integer(as.numeric(sx)))
    true_tokens <- sx %in% c("TRUE", "T", "YES", "Y")
    false_tokens <- sx %in% c("FALSE", "F", "NO", "N")
    out[is.na(out) & true_tokens] <- 1L
    out[is.na(out) & false_tokens] <- 0L
  }
  out[is.na(out)] <- 0L
  as.integer(out != 0L)
}

# Normalise identifier spellings before risk-row uniqueness and Cox clustering;
# PLACE_ID identifies a fixed position, not an interval-specific polygon.
clean_key <- function(x) {
  y <- trimws(as.character(x))
  y[y %in% c("", "NA", "NaN", "NULL", "None")] <- NA_character_
  y
}

# Return first available event/risk alias in prescribed priority order;
# primary ambiguity-bridged fields precede strict observed-state fields.
first_existing_name <- function(nms, candidates, required = TRUE, label = "field") {
  hit <- candidates[candidates %in% nms]
  if (length(hit) > 0L) return(hit[1])
  if (required) stop("Missing required ", label, ": ", paste(candidates, collapse = " / "))
  NA_character_
}

# Centre and standardise a numeric predictor using all finite input rows;
# retain missing values to support a common subsequent complete-case filter.
# The source scales over the pooled three-population input, not separately
# for each transition, and does not compute training-only forecast scaling.
zscore_preserve_na <- function(x) {
  x <- num(x)
  out <- rep(NA_real_, length(x))
  ok <- is.finite(x)
  if (sum(ok) < 2L) return(out)
  s <- stats::sd(x[ok])
  if (!is.finite(s) || s == 0) return(out)
  out[ok] <- (x[ok] - mean(x[ok])) / s
  out
}

# Channel-margin distance in metres -> log(1 + distance in kilometres), then Z.
# Negative distances become NA as they are not meaningful here.
logkm_z <- function(x) {
  x <- num(x)
  x[x < 0] <- NA_real_
  zscore_preserve_na(log1p(x / 1000))
}

# Detect a constant explanatory term after restricting to the shared analysis
# sample. A non-varying history variable is removed from M1, not added to M0.
has_variation <- function(x) {
  if (is.factor(x) || is.character(x)) {
    length(unique(stats::na.omit(x))) > 1L
  } else {
    xx <- num(x)
    xx <- xx[is.finite(xx)]
    length(xx) > 1L && is.finite(stats::sd(xx)) && stats::sd(xx) > 0
  }
}

# Reserved short string-length helper (retained as written for compatibility).
safe_nchar <- function(x) ifelse(is.na(x), 0L, nchar(x))

# Suppress sf's expected warning for non-spatial GeoPackage tables, while
# leaving unrelated provider warnings visible to the analyst.
st_read_qgis_safe <- function(...) {
  withCallingHandlers(
    sf::st_read(...),
    warning = function(w) {
      msg <- conditionMessage(w)
      if (grepl("no simple feature geometries present", msg, fixed = TRUE)) {
        invokeRestart("muffleWarning")
      }
    }
  )
}

# Resolve ordinary .gpkg paths and QGIS provider URI suffixes such as
# '|layername=Risk Table' without changing the selected input table.
parse_gpkg_source <- function(x, layer_hint = NULL) {
  x <- as.character(x)[1]
  layer_from_uri <- NA_character_

  if (grepl("\\|layername=", x, ignore.case = TRUE)) {
    parts <- strsplit(x, "\\|", fixed = FALSE)[[1]]
    path <- parts[1]
    layer_part <- parts[grepl("^layername=", parts, ignore.case = TRUE)]
    if (length(layer_part) > 0L) {
      layer_from_uri <- sub("^layername=", "", layer_part[1], ignore.case = TRUE)
    }
  } else {
    path <- x
  }

  if (grepl("dbname=", path, ignore.case = TRUE)) {
    path2 <- sub(".*dbname='([^']+)'.*", "\\1", path)
    if (!identical(path2, path)) path <- path2
  }

  hint <- as.character(layer_hint)[1]
  if (is.na(hint)) hint <- ""
  layer <- if (!is.na(layer_from_uri) && nzchar(layer_from_uri)) layer_from_uri else hint

  list(path = path, layer = layer)
}

# Identify the authoritative Stage 4 Step 3 Risk Table sublayer, rejecting
# PLACE_interval_long (the upstream table before final covariate attribution).
# If a GeoPackage contains multiple plausible tables, demand an explicit name.
choose_gpkg_layer <- function(path, requested_layer = NULL) {
  layers <- sf::st_layers(path, options = "LIST_ALL_TABLES=YES")
  layer_names <- layers$name

  requested_layer <- as.character(requested_layer)[1]
  if (is.na(requested_layer)) requested_layer <- ""
  requested_layer <- trimws(requested_layer)

  if (nzchar(requested_layer) && requested_layer %in% layer_names) {
    if (identical(requested_layer, "PLACE_interval_long")) {
      stop("RiskLayerName points to PLACE_interval_long, not the Stage 4 Step 3 Risk Table.")
    }
    return(requested_layer)
  }

  preferred <- c(
    "RISK_TABLE", "Risk Table", "Risk_Table", "RiskTable",
    "Stage_4_Risk_Table", "Stage4_Risk_Table", "Version 2", "Version_2"
  )
  hit <- preferred[preferred %in% layer_names]
  if (length(hit) > 0L) return(hit[1])

  non_raw <- setdiff(layer_names, c("PLACE_interval_long", "KM_blocks", "INPUT"))
  if (length(non_raw) == 1L) return(non_raw[1])

  stop(
    "RiskLayerName is missing or ambiguous. Available tables/layers: ",
    paste(layer_names, collapse = ", ")
  )
}

# Escape SQLite identifier quotes in field and table names assembled into
# the restricted SELECT query (not string-value interpolation).
sql_quote_identifier <- function(x) {
  paste0('"', gsub('"', '""', as.character(x), fixed = TRUE), '"')
}

# -----------------------------
# 2. Memory-safe projected input
# -----------------------------
# Narrow column allowlist: preserve primary and strict aliases for the three
# memory-comparison transitions (SF->AD, DS->AD and DS->SF).
# AD->DS is intentionally outside this *formal memory* test.
event_risk_candidates <- c(
  "REACTIVATE_EVT_PRIMARY", "REACTIVATE_EVT",
  "REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET",
  "STABILISE_EVT_PRIMARY", "STABILISE_EVT",
  "STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET",
  "STORAGE_REWORK_EVT_PRIMARY", "STORAGE_REWORK_EVT",
  "STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET"
)

# Only antecedent history measures from Stage 4 Step 3 are required; do not
# import final full-period assemblage totals as early-interval predictors.
history_raw_fields <- c(
  "ASM_DOM_RATIO_PREV",
  "ASM_N_EPISODES_PREV",
  "ASM_MAX_QUIET_PREV",
  "ASM_COV_FRAC",
  "ASM_N_REACTIVATE_PREV",
  "ASM_STORAGE_FRAC_PREV",
  "ASM_STAB_FP_FRAC_PREV",
  "ASM_QUIET_SINCE_PREV",
  "ASM_N_STORAGE_EVT_PREV",
  "ASM_N_STABILISE_PREV"
)

# Shared time/identifier fields, event/risk indicators, historic assemblage
# covariates, and spatial-margin distances required for both reaches.
common_fields <- c(
  "PLACE_ID", "BLOCK_ID", "tstart_yr", "tstop_yr",
  event_risk_candidates,
  history_raw_fields,
  "DIST_ACTIVE_CURR",
  "DIST_CHANNEL_PREV"
)

# Extra Mamoré-only dynamic bank-side and curvature exposure fields. They are
# produced from geometry dated at or before the beginning of each interval.
mamore_geom_fields <- c(
  "GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV",
  "OUTER_BANK_PREV", "INNER_BANK_PREV",
  "NEAR_CHANNEL_HALF_PREV", "NEAR_CHANNEL_FULL_PREV",
  "OUTER_CURV_REACT_HALF_PREV", "OUTER_CURV_REACT_FULL_PREV",
  "MAM_NEAR_CHANNEL_PREV",
  "MAM_OUTER_REACT_EXPOSED_PREV",
  "MAM_OUTER_CURV_REACT_PREV"
)

# Build the list of required/requested fields BEFORE loading the large Risk
# Table. This avoids reading millions of extraneous history columns.
input_candidates <- unique(c(
  common_fields,
  if (!identical(reach_label, "Jamuna")) mamore_geom_fields else character(0)
))

# SQL load restriction is a union of relevant risk populations, not a
# fitted-model risk-set definition. Each model filters again later.
risk_where_candidates <- c(
  "REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET",
  "STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET",
  "STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET"
)

# Projection-first GeoPackage input path: inspect schema, select named columns,
# and WHERE-filter candidate risk rows in SQLite before R materialisation.
# Fail explicitly if projected access fails; there is no full-table fallback.
read_memory_table_projected <- function(source, layer_hint = NULL) {
  # Direct sf object path supports testing, but the QGIS file interface below
  # is the production memory-safe path. Geometry is dropped immediately.
  if (inherits(source, "sf")) {
    dat <- sf::st_drop_geometry(source)
    keep <- intersect(input_candidates, names(dat))
    dat <- dat[, keep, drop = FALSE]
    return(dat)
  }

  source_chr <- as.character(source)[1]
  if (is.na(source_chr) || !nzchar(source_chr)) stop("Empty RiskTable source.")
  if (!grepl("\\.gpkg($|\\|)", source_chr, ignore.case = TRUE)) {
    stop(
      "This standalone memory test expects the Stage 4 Step 3 GeoPackage Risk Table. ",
      "GeoPackage input is required so fields and risk rows can be SQL-projected before loading."
    )
  }

  src <- parse_gpkg_source(source_chr, layer_hint)
  lyr <- choose_gpkg_layer(src$path, src$layer)

  # Read a single input record only to discover field names and minimise data
  # transfer; do not load the full GeoPackage merely to enumerate its schema.
  schema_obj <- st_read_qgis_safe(
    src$path, layer = lyr, quiet = TRUE,
    options = "LIST_ALL_TABLES=YES", n_max = 1
  )
  available <- names(schema_obj)
  rm(schema_obj)

  keep <- intersect(input_candidates, available)

  if (!any(c("PLACE_ID", "BLOCK_ID") %in% keep) ||
      !all(c("tstart_yr", "tstop_yr") %in% keep)) {
    stop("Risk Table lacks the required place key and/or survival time fields.")
  }

  present_risk_where <- intersect(risk_where_candidates, available)
  if (length(present_risk_where) == 0L) {
    stop("No recognised state-specific risk-set field is present in the Risk Table.")
  }

  # Explicit SQL projection; predicates use the union of all recognised risk
  # sets, allowing strict and primary aliases for input-compatibility QA.
  select_sql <- paste(vapply(keep, sql_quote_identifier, character(1)), collapse = ", ")
  where_sql <- paste(
    vapply(
      present_risk_where,
      function(nm) paste0("COALESCE(CAST(", sql_quote_identifier(nm), " AS INTEGER),0)=1"),
      character(1)
    ),
    collapse = " OR "
  )

  query_sql <- paste0(
    "SELECT ", select_sql,
    " FROM ", sql_quote_identifier(lyr),
    " WHERE (", where_sql, ")"
  )

  message(
    "[Memory] SQL projection: selecting ", length(keep), " of ", length(available),
    " source fields and restricting rows to the union of SF/DS risk populations."
  )

  # The projected SQL query is executed by the source provider. A provider
  # failure is fatal to avoid unplanned RAM exhaustion on the full Risk Table.
  obj <- tryCatch(
    st_read_qgis_safe(src$path, query = query_sql, quiet = FALSE),
    error = function(e) {
      stop(
        "SQL-projected Risk Table read failed. Full-table fallback is disabled to ",
        "avoid a memory overflow. Error: ", conditionMessage(e)
      )
    }
  )

  dat <- if (inherits(obj, "sf")) sf::st_drop_geometry(obj) else as.data.frame(obj)
  rm(obj)
  message("[Memory] Loaded ", format(nrow(dat), big.mark = ","), " rows x ", ncol(dat), " fields.")
  dat
}

# Only this projected subset enters the remainder of the R workflow.
risk <- read_memory_table_projected(RiskTable, RiskLayerName)

utils::write.csv(
  data.frame(field = names(risk), stringsAsFactors = FALSE),
  file.path(out_dir, "00_INPUT_FIELDS.csv"),
  row.names = FALSE, na = ""
)

if (!"PLACE_ID" %in% names(risk) && "BLOCK_ID" %in% names(risk)) risk$PLACE_ID <- risk$BLOCK_ID
if (!"BLOCK_ID" %in% names(risk) && "PLACE_ID" %in% names(risk)) risk$BLOCK_ID <- risk$PLACE_ID
if (!all(c("PLACE_ID", "tstart_yr", "tstop_yr") %in% names(risk))) {
  stop("Missing PLACE_ID/BLOCK_ID or tstart_yr/tstop_yr after projected read.")
}

# Standardise fixed-place identifiers and continuous-time year fields before
# detecting duplicated PLACE x (start, stop) records.
risk$PLACE_ID <- clean_key(risk$PLACE_ID)
risk$BLOCK_ID <- clean_key(risk$BLOCK_ID)
risk$tstart_yr <- num(risk$tstart_yr)
risk$tstop_yr <- num(risk$tstop_yr)

# -----------------------------
# 3. Authoritative event/risk aliases
# -----------------------------
# SF->AD and DS->SF: prefer the authoritative primary (ambiguity-bridged)
# event/risk fields when available, with strict definitions as fallback.
react_evt_src <- first_existing_name(
  names(risk), c("REACTIVATE_EVT_PRIMARY", "REACTIVATE_EVT"),
  TRUE, "SF->AD event field"
)
react_risk_src <- first_existing_name(
  names(risk), c("REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET"),
  TRUE, "SF->AD risk field"
)
stab_evt_src <- first_existing_name(
  names(risk), c("STABILISE_EVT_PRIMARY", "STABILISE_EVT"),
  TRUE, "DS->SF event field"
)
stab_risk_src <- first_existing_name(
  names(risk), c("STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET"),
  TRUE, "DS->SF risk field"
)

risk$REACTIVATE_EVT_MODEL <- int01(risk[[react_evt_src]])
risk$REACTIVATE_RISK_MODEL <- int01(risk[[react_risk_src]])
risk$STABILISE_EVT_MODEL <- int01(risk[[stab_evt_src]])
risk$STABILISE_RISK_MODEL <- int01(risk[[stab_risk_src]])

# DS->AD has a historical compatibility guard: selects the first alias with
# at least one positive value, rather than merely the first present field.
# SCIENTIFIC CAUTION: legitimate zero-event primary data can therefore lead
# to a strict-definition fallback. The selected alias is logged; verify it.
choose_informative_binary <- function(dat, candidates, label) {
  present <- candidates[candidates %in% names(dat)]
  if (length(present) == 0L) stop("Missing ", label, ": ", paste(candidates, collapse = " / "))

  counts <- vapply(present, function(nm) sum(int01(dat[[nm]]) == 1L, na.rm = TRUE), numeric(1))
  informative <- present[counts > 0]
  chosen <- if (length(informative) > 0L) informative[1] else present[1]

  message(
    "[DS->AD QA] ", label, " candidates: ",
    paste(sprintf("%s=%s", present, format(counts, big.mark = ",")), collapse = "; "),
    "; selected=", chosen
  )

  list(name = chosen, values = int01(dat[[chosen]]), counts = counts)
}

# Independently choose DS->AD event and DS->AD risk aliases. The selections
# are recorded in the console for source-to-model reproducibility.
rw_evt_pick <- choose_informative_binary(
  risk, c("STORAGE_REWORK_EVT_PRIMARY", "STORAGE_REWORK_EVT"), "event"
)
rw_risk_pick <- choose_informative_binary(
  risk, c("STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET"), "risk set"
)

risk$STORAGE_REWORK_EVT_MODEL <- rw_evt_pick$values
risk$STORAGE_REWORK_RISK_MODEL <- rw_risk_pick$values

# Backstop when no dedicated DS->AD population is marked: DS->SF shares
# the DS starting state, so its risk field can stand in for missing DS risk.
# Treat this as an audit-requiring compatibility fallback, not a new ontology.
if (sum(risk$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE) == 0L &&
    sum(risk$STABILISE_RISK_MODEL == 1L, na.rm = TRUE) > 0L) {
  warning(
    "Dedicated DS->AD risk field is empty; using the DS->SF risk set as the ",
    "canonical Depositional-Storage starting-state population."
  )
  risk$STORAGE_REWORK_RISK_MODEL <- risk$STABILISE_RISK_MODEL
}

# Count selected at-risk rows and events, and flag any event whose selected
# risk-set indicator is zero. The model run stops on event/risk mismatch.
integrity <- data.frame(
  transition = c("SF->AD", "DS->AD", "DS->SF"),
  risk_rows = c(
    sum(risk$REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE),
    sum(risk$STABILISE_RISK_MODEL == 1L, na.rm = TRUE)
  ),
  events = c(
    sum(risk$REACTIVATE_EVT_MODEL == 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_MODEL == 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT_MODEL == 1L, na.rm = TRUE)
  ),
  events_outside_risk = c(
    sum(risk$REACTIVATE_EVT_MODEL == 1L & risk$REACTIVATE_RISK_MODEL != 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_MODEL == 1L & risk$STORAGE_REWORK_RISK_MODEL != 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT_MODEL == 1L & risk$STABILISE_RISK_MODEL != 1L, na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)

utils::write.csv(
  integrity,
  file.path(out_dir, "00_EVENT_RISK_INTEGRITY_QA.csv"),
  row.names = FALSE, na = ""
)

if (any(integrity$events_outside_risk > 0L)) {
  stop("At least one event lies outside its corresponding risk set. See 00_EVENT_RISK_INTEGRITY_QA.csv.")
}

# Input read and this in-memory restriction are BOTH keyed to state-specific
# risk flags. No explicit M3_MODEL_ELIGIBLE_PRIMARY filter is implemented here.
# Consequently, compare the sampled rows with the parent historic modelling
# specification if primary QA exclusions are intended for the publication.
# Keep only the three required state-specific risk populations.
risk <- risk[
  risk$REACTIVATE_RISK_MODEL == 1L |
    risk$STORAGE_REWORK_RISK_MODEL == 1L |
    risk$STABILISE_RISK_MODEL == 1L,
  , drop = FALSE
]

# A fixed PLACE can contribute multiple intervals, but the same period must
# not be duplicated for that PLACE; clustering addresses within-PLACE repeats.
dup_key <- paste(risk$PLACE_ID, risk$tstart_yr, risk$tstop_yr, sep = "\r")
n_duplicate_interval_rows <- sum(duplicated(dup_key))
if (n_duplicate_interval_rows > 0L) {
  stop(
    "Duplicate PLACE_ID + tstart_yr + tstop_yr rows found in the analysis population: ",
    n_duplicate_interval_rows
  )
}

# -----------------------------
# 4. Recreate final transformed predictors
# -----------------------------
# Record the planned antecedent metrics independently of the model term lists.
# Missing metrics do not silently become zeros; affected models are skipped.
required_history_raw <- c(
  "ASM_DOM_RATIO_PREV", "ASM_N_EPISODES_PREV", "ASM_MAX_QUIET_PREV",
  "ASM_STORAGE_FRAC_PREV", "ASM_STAB_FP_FRAC_PREV",
  "ASM_QUIET_SINCE_PREV", "ASM_N_STORAGE_EVT_PREV", "ASM_N_STABILISE_PREV"
)

missing_history_raw <- setdiff(required_history_raw, names(risk))
if (length(missing_history_raw) > 0L) {
  warning(
    "Some planned history fields are absent and affected model(s) will be skipped: ",
    paste(missing_history_raw, collapse = ", ")
  )
}

# One consistent naming convention for standardised history and observation-
# coverage fields: *_Z. Raw inputs remain untouched for other QA checks.
z_map <- c(
  ASM_DOM_RATIO_PREV = "ASM_DOM_RATIO_PREV_Z",
  ASM_N_EPISODES_PREV = "ASM_N_EPISODES_PREV_Z",
  ASM_MAX_QUIET_PREV = "ASM_MAX_QUIET_PREV_Z",
  ASM_COV_FRAC = "ASM_COV_FRAC_Z",
  ASM_N_REACTIVATE_PREV = "ASM_N_REACTIVATE_PREV_Z",
  ASM_STORAGE_FRAC_PREV = "ASM_STORAGE_FRAC_PREV_Z",
  ASM_STAB_FP_FRAC_PREV = "ASM_STAB_FP_FRAC_PREV_Z",
  ASM_QUIET_SINCE_PREV = "ASM_QUIET_SINCE_PREV_Z",
  ASM_N_STORAGE_EVT_PREV = "ASM_N_STORAGE_EVT_PREV_Z",
  ASM_N_STABILISE_PREV = "ASM_N_STABILISE_PREV_Z"
)

for (src in names(z_map)) {
  if (src %in% names(risk)) {
    risk[[z_map[[src]]]] <- zscore_preserve_na(risk[[src]])
  }
}

# Jamuna exposure: current/interval-start margin distance. Both linear-Z
# and log-kilometre-Z representations are derived; specifications select one.
if ("DIST_ACTIVE_CURR" %in% names(risk)) {
  risk$DIST_ACTIVE_CURR_LINEAR_Z <- zscore_preserve_na(risk$DIST_ACTIVE_CURR)
  risk$DIST_ACTIVE_CURR_LOGKM_Z <- logkm_z(risk$DIST_ACTIVE_CURR)
}

# Mamoré exposure: channel geometry at the previous/interval-start timestep;
# keep linear and logarithmic distance transformations distinct.
if ("DIST_CHANNEL_PREV" %in% names(risk)) {
  risk$DIST_CHANNEL_PREV_LINEAR_Z <- zscore_preserve_na(risk$DIST_CHANNEL_PREV)
  risk$DIST_CHANNEL_PREV_LOGKM_Z <- logkm_z(risk$DIST_CHANNEL_PREV)
}

# Mamoré-specific covariate reconstruction. The default full-width threshold
# can be switched to half-width for a predefined sensitivity specification.
if (!identical(reach_label, "Jamuna")) {
  react_near_field <- if (mamore_react_half) "NEAR_CHANNEL_HALF_PREV" else "NEAR_CHANNEL_FULL_PREV"
  react_curv_field <- if (mamore_react_half) "OUTER_CURV_REACT_HALF_PREV" else "OUTER_CURV_REACT_FULL_PREV"

  if (react_near_field %in% names(risk)) {
    risk$MAM_NEAR_CHANNEL_PREV <- num(risk[[react_near_field]])
  } else if (!"MAM_NEAR_CHANNEL_PREV" %in% names(risk)) {
    stop("Mamoré SF->AD requires ", react_near_field, " or MAM_NEAR_CHANNEL_PREV.")
  } else {
    risk$MAM_NEAR_CHANNEL_PREV <- num(risk$MAM_NEAR_CHANNEL_PREV)
  }

  # Outer-bank exposure combines non-channel position, outer-bend side, and
  # proximity at the selected channel-width scale. It is not an event flag.
  can_derive_outer_exposure <- all(
    c("INSIDE_CHANNEL_PREV", "OUTER_BANK_PREV", react_near_field) %in% names(risk)
  )
  if (can_derive_outer_exposure) {
    inside <- num(risk$INSIDE_CHANNEL_PREV)
    outer <- num(risk$OUTER_BANK_PREV)
    near <- num(risk[[react_near_field]])
    risk$MAM_OUTER_REACT_EXPOSED_PREV <- as.integer(
      !is.na(inside) & !is.na(outer) & !is.na(near) &
        inside == 0 & outer == 1 & near == 1
    )
  } else if ("MAM_OUTER_REACT_EXPOSED_PREV" %in% names(risk)) {
    risk$MAM_OUTER_REACT_EXPOSED_PREV <- int01(risk$MAM_OUTER_REACT_EXPOSED_PREV)
  } else {
    stop("Mamoré SF->AD requires raw outer-bank exposure fields or MAM_OUTER_REACT_EXPOSED_PREV.")
  }

  if (react_curv_field %in% names(risk)) {
    risk$MAM_OUTER_CURV_REACT_PREV <- num(risk[[react_curv_field]])
  } else if ("MAM_OUTER_CURV_REACT_PREV" %in% names(risk)) {
    risk$MAM_OUTER_CURV_REACT_PREV <- num(risk$MAM_OUTER_CURV_REACT_PREV)
  } else {
    stop("Mamoré SF->AD requires ", react_curv_field, " or MAM_OUTER_CURV_REACT_PREV.")
  }

  # Signed/local curvature exposure is standardised separately from the binary
  # near-channel and outer-bank indicators used by Mamoré SF->AD.
  risk$MAM_OUTER_CURV_REACT_PREV_Z <- zscore_preserve_na(risk$MAM_OUTER_CURV_REACT_PREV)
}

# -----------------------------
# 5. Frozen model specifications
# -----------------------------
# Coverage is an observational support/control term included in BOTH M0 and
# M1 when selected and available. It is not part of the tested history block.
# The field describes overall ASM polygon coverage, not a held-out outcome.
coverage_control <- if (include_coverage && "ASM_COV_FRAC_Z" %in% names(risk)) {
  "ASM_COV_FRAC_Z"
} else {
  character(0)
}

# Core antecedent assemblage-memory block: prior dominance, episode count,
# and maximum quiet interval (all precomputed upstream using prior observations).
history_core <- c(
  "ASM_DOM_RATIO_PREV_Z",
  "ASM_N_EPISODES_PREV_Z",
  "ASM_MAX_QUIET_PREV_Z"
)
# Jamuna SF->AD and DS->AD exclude episode count under the frozen source
# specification; DS->SF retains it. This is not data-driven selection here.
history_core_no_episodes <- setdiff(history_core, "ASM_N_EPISODES_PREV_Z")

# The Jamuna model family uses distance to the Active Domain margin for its
# spatial-only comparator. Distance is linear for reactivation/reworking,
# logarithmic for DS stabilisation.
if (identical(reach_label, "Jamuna")) {
  specs <- list(
    list(
      model = "active_domain_reactivation",
      transition = "Stabilised Floodplain -> Active Domain",
      code = "SF_AD",
      risk_field = "REACTIVATE_RISK_MODEL",
      event_field = "REACTIVATE_EVT_MODEL",
      spatial_framework = "linear_active_domain_margin",
      spatial_terms = c("DIST_ACTIVE_CURR_LINEAR_Z"),
      control_terms = coverage_control,
      history_terms = history_core_no_episodes
    ),
    list(
      model = "depositional_storage_reworking",
      transition = "Depositional Storage -> Active Domain",
      code = "DS_AD",
      risk_field = "STORAGE_REWORK_RISK_MODEL",
      event_field = "STORAGE_REWORK_EVT_MODEL",
      spatial_framework = "linear_active_domain_margin_storage_reworking",
      spatial_terms = c("DIST_ACTIVE_CURR_LINEAR_Z"),
      control_terms = coverage_control,
      history_terms = c(
        history_core_no_episodes,
        "ASM_STORAGE_FRAC_PREV_Z",
        "ASM_QUIET_SINCE_PREV_Z",
        "ASM_N_STORAGE_EVT_PREV_Z"
      )
    ),
    list(
      model = "floodplain_stabilisation",
      transition = "Depositional Storage -> Stabilised Floodplain",
      code = "DS_SF",
      risk_field = "STABILISE_RISK_MODEL",
      event_field = "STABILISE_EVT_MODEL",
      spatial_framework = "active_domain_margin_stabilisation",
      spatial_terms = c("DIST_ACTIVE_CURR_LOGKM_Z"),
      control_terms = coverage_control,
      history_terms = c(
        history_core,
        "ASM_STORAGE_FRAC_PREV_Z",
        "ASM_STAB_FP_FRAC_PREV_Z",
        "ASM_QUIET_SINCE_PREV_Z",
        "ASM_N_STABILISE_PREV_Z"
      )
    )
  )
} else {
  # Default Mamoré SF->AD memory excludes prior-reactivation count because
  # a history count may cause quasi/separation; enable only as sensitivity.
  mamore_sfad_history <- history_core
  if (include_mamore_react_count) {
    mamore_sfad_history <- c(mamore_sfad_history, "ASM_N_REACTIVATE_PREV_Z")
  }

  # The Mamoré DS->AD baseline is previous-channel-margin linear distance;
  # optional curvature belongs to BOTH models if chosen, so nestedness remains.
  mamore_dsad_spatial <- c(
    "DIST_CHANNEL_PREV_LINEAR_Z",
    if (mamore_dsad_curvature) "MAM_OUTER_CURV_REACT_PREV_Z" else character(0)
  )

  specs <- list(
    list(
      model = "active_domain_reactivation",
      transition = "Stabilised Floodplain -> Active Domain",
      code = "SF_AD",
      risk_field = "REACTIVATE_RISK_MODEL",
      event_field = "REACTIVATE_EVT_MODEL",
      spatial_framework = "lagged_local_outer_bank_reactivation",
      spatial_terms = c(
        "MAM_NEAR_CHANNEL_PREV",
        "MAM_OUTER_REACT_EXPOSED_PREV",
        "MAM_OUTER_CURV_REACT_PREV_Z"
      ),
      control_terms = coverage_control,
      history_terms = mamore_sfad_history
    ),
    list(
      model = "depositional_storage_reworking",
      transition = "Depositional Storage -> Active Domain",
      code = "DS_AD",
      risk_field = "STORAGE_REWORK_RISK_MODEL",
      event_field = "STORAGE_REWORK_EVT_MODEL",
      spatial_framework = if (mamore_dsad_curvature) {
        "linear_previous_channel_margin_plus_curvature_storage_reworking"
      } else {
        "linear_previous_channel_margin_storage_reworking"
      },
      spatial_terms = mamore_dsad_spatial,
      control_terms = coverage_control,
      history_terms = c(
        history_core,
        "ASM_STORAGE_FRAC_PREV_Z",
        "ASM_QUIET_SINCE_PREV_Z",
        "ASM_N_STORAGE_EVT_PREV_Z"
      )
    ),
    list(
      model = "floodplain_stabilisation",
      transition = "Depositional Storage -> Stabilised Floodplain",
      code = "DS_SF",
      risk_field = "STABILISE_RISK_MODEL",
      event_field = "STABILISE_EVT_MODEL",
      spatial_framework = "lagged_channel_margin_stabilisation",
      spatial_terms = c("DIST_CHANNEL_PREV_LOGKM_Z"),
      control_terms = coverage_control,
      history_terms = c(
        history_core,
        "ASM_STORAGE_FRAC_PREV_Z",
        "ASM_STAB_FP_FRAC_PREV_Z",
        "ASM_QUIET_SINCE_PREV_Z",
        "ASM_N_STABILISE_PREV_Z"
      )
    )
  )
}

# Export the frozen, reach/transition-specific covariate specification BEFORE
# fitting. This is the auditable source of which history terms were requested.
spec_table <- do.call(
  rbind,
  lapply(specs, function(sp) {
    data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      spatial_framework = sp$spatial_framework,
      spatial_terms = paste(sp$spatial_terms, collapse = "; "),
      control_terms = paste(sp$control_terms, collapse = "; "),
      history_terms = paste(sp$history_terms, collapse = "; "),
      risk_field = sp$risk_field,
      event_field = sp$event_field,
      stringsAsFactors = FALSE
    )
  })
)
utils::write.csv(
  spec_table,
  file.path(out_dir, "06_MODEL_TERM_SPECIFICATIONS.csv"),
  row.names = FALSE, na = ""
)

# -----------------------------
# 6. Cox fitting and block-test helpers
# -----------------------------
# Andersen-Gill counting-process style Cox fit with (tstart,tstop] intervals.
# PLACE_ID clustering gives a sandwich covariance for repeated place histories.
# A fit warning is captured (not silently lost) and returned for output QA.
# Tied events use the Efron approximation, matching the frozen model syntax.
fit_cox_checked <- function(dat, event_field, terms) {
  rhs <- if (length(terms) > 0L) paste(terms, collapse = " + ") else "1"
  form <- stats::as.formula(
    paste0(
      "survival::Surv(tstart_yr, tstop_yr, ", event_field, ") ~ ",
      rhs, " + cluster(PLACE_ID)"
    )
  )

  warnings <- character(0)
  fit <- tryCatch(
    withCallingHandlers(
      survival::coxph(
        form,
        data = dat,
        ties = "efron",
        x = TRUE,
        model = FALSE,
        control = survival::coxph.control(iter.max = 50)
      ),
      warning = function(w) {
        warnings <<- unique(c(warnings, conditionMessage(w)))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) e
  )

  if (inherits(fit, "error")) {
    return(list(model = NULL, warning_text = paste(c(warnings, conditionMessage(fit)), collapse = " | ")))
  }

  list(model = fit, warning_text = paste(warnings, collapse = " | "))
}

# Extract fitted-data Cox concordance C. This is descriptive ranking on the
# analysis sample, not cross-validation or a held-out discrimination metric.
get_concordance <- function(mod) {
  if (is.null(mod)) return(NA_real_)
  cc <- tryCatch(summary(mod)$concordance, error = function(e) NULL)
  if (is.null(cc) || length(cc) == 0L) return(NA_real_)
  as.numeric(cc[1])
}

# Joint H0: all added ASM history coefficients equal zero, conditional on the
# chosen spatial/coverage baseline and on the matched risk population.
# Use the robust sandwich covariance (mod$var), not naive varcov.
# Eigen decomposition yields a generalised inverse if the covariance is rank-
# deficient; test degrees of freedom then equal the retained positive rank.
wald_block_robust <- function(mod, history_terms) {
  if (is.null(mod) || length(history_terms) == 0L) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_, rank = 0L))
  }

  b_all <- stats::coef(mod)
  idx <- match(history_terms, names(b_all), nomatch = 0L)
  idx <- idx[idx > 0L]
  if (length(idx) == 0L) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_, rank = 0L))
  }

  b <- as.numeric(b_all[idx])
  V <- mod$var[idx, idx, drop = FALSE]
  V <- (V + t(V)) / 2

  if (any(!is.finite(b)) || any(!is.finite(V))) {
    return(list(stat = NA_real_, df = length(idx), p = NA_real_, rank = NA_integer_))
  }

  # The variance matrix is symmetrised before spectral inversion. Non-finite
  # or non-invertible matrices yield NA diagnostics rather than fictitious p.
  ee <- tryCatch(eigen(V, symmetric = TRUE), error = function(e) NULL)
  if (is.null(ee)) {
    return(list(stat = NA_real_, df = length(idx), p = NA_real_, rank = NA_integer_))
  }

  vmax <- max(abs(ee$values), na.rm = TRUE)
  tol <- if (is.finite(vmax) && vmax > 0) vmax * 1e-10 else 1e-12
  pos <- which(ee$values > tol)
  if (length(pos) == 0L) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_, rank = 0L))
  }

  Vinv <- ee$vectors[, pos, drop = FALSE] %*%
    diag(1 / ee$values[pos], nrow = length(pos)) %*%
    t(ee$vectors[, pos, drop = FALSE])

  stat <- as.numeric(t(b) %*% Vinv %*% b)
  df <- length(pos)
  p <- stats::pchisq(stat, df = df, lower.tail = FALSE)

  list(stat = stat, df = df, p = p, rank = df)
}

# Individual history hazard ratios and approximate 95% Wald intervals are
# secondary descriptors; the pre-specified BLOCK test addresses the joint
# hypothesis and should not be replaced by cherry-picked term p-values.
robust_coef_table <- function(mod, terms, block_type) {
  if (is.null(mod) || length(terms) == 0L) return(NULL)

  b_all <- stats::coef(mod)
  out <- lapply(terms, function(tm) {
    idx <- match(tm, names(b_all), nomatch = 0L)
    if (idx == 0L) return(NULL)

    b <- as.numeric(b_all[idx])
    se <- sqrt(as.numeric(mod$var[idx, idx]))
    z <- b / se
    p <- 2 * stats::pnorm(abs(z), lower.tail = FALSE)

    data.frame(
      term = tm,
      block = block_type,
      coefficient = b,
      robust_se = se,
      hazard_ratio = exp(b),
      conf_low_95 = exp(b - 1.96 * se),
      conf_high_95 = exp(b + 1.96 * se),
      robust_z = z,
      robust_p = p,
      stringsAsFactors = FALSE
    )
  })

  do.call(rbind, out)
}

# -----------------------------
# 7. Run the three nested comparisons
# -----------------------------
# Each successful fit contributes a paired comparison and, where supported,
# separate block-Wald, spatial coefficient shift, and same-sample QA records.
comparison_rows <- list()
wald_rows <- list()
spatial_change_rows <- list()
sample_qa_rows <- list()
history_coef_rows <- list()

# Fit independently for SF->AD, DS->AD, and DS->SF. All state-specific risk
# rows are retained from the input until this transition-level filtering.
for (sp in specs) {
  message("[Memory block] ", reach_label, " | ", sp$transition)

  # The complete-case term union is fixed BEFORE fitting EITHER model; M0 does
  # not benefit from extra rows just because it contains fewer predictors.
  requested_terms <- unique(c(sp$spatial_terms, sp$control_terms, sp$history_terms))
  missing_terms <- setdiff(requested_terms, names(risk))

  if (length(missing_terms) > 0L) {
    comparison_rows[[length(comparison_rows) + 1L]] <- data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      spatial_framework = sp$spatial_framework,
      rows = 0L, places = 0L, events = 0L,
      spatial_terms = paste(sp$spatial_terms, collapse = "; "),
      control_terms = paste(sp$control_terms, collapse = "; "),
      history_terms_requested = paste(sp$history_terms, collapse = "; "),
      history_terms_used = "",
      history_terms_dropped_nonvarying = "",
      loglik_baseline = NA_real_, loglik_full = NA_real_,
      delta_loglik_full_minus_baseline = NA_real_,
      lr_stat = NA_real_, lr_df = NA_integer_, lr_p_conventional = NA_real_,
      aic_baseline = NA_real_, aic_full = NA_real_,
      delta_aic_baseline_minus_full = NA_real_,
      concordance_baseline = NA_real_, concordance_full = NA_real_,
      delta_concordance_full_minus_baseline = NA_real_,
      robust_history_wald_chisq = NA_real_, robust_history_wald_df = NA_integer_,
      robust_history_wald_p = NA_real_,
      baseline_warning = "",
      full_warning = "",
      status = paste0("SKIPPED_MISSING_TERMS: ", paste(missing_terms, collapse = "; ")),
      stringsAsFactors = FALSE
    )
    next
  }

  # Restrict to the specified source-state risk set. Event flags are only
  # meaningful within their corresponding eligible starting-state population.
  idx_risk <- risk[[sp$risk_field]] == 1L
  dd <- risk[idx_risk, c(
    "PLACE_ID", "tstart_yr", "tstop_yr", sp$event_field, requested_terms
  ), drop = FALSE]

  names(dd)[names(dd) == sp$event_field] <- "event_internal"
  dd$event_internal <- int01(dd$event_internal)

  # Remove missing predictors, invalid survival-year bounds and zero/negative
  # interval durations on the common sample shared by both nested fits.
  complete_fields <- c("PLACE_ID", "tstart_yr", "tstop_yr", "event_internal", requested_terms)
  cc <- stats::complete.cases(dd[, complete_fields, drop = FALSE])
  cc <- cc & is.finite(dd$tstart_yr) & is.finite(dd$tstop_yr) & dd$tstop_yr > dd$tstart_yr
  dd <- dd[cc, , drop = FALSE]

  # Do not fit a Cox model without observed transition events. Record a skip
  # disposition rather than fabricating a baseline/full comparison.
  if (nrow(dd) == 0L || sum(dd$event_internal == 1L, na.rm = TRUE) == 0L) {
    comparison_rows[[length(comparison_rows) + 1L]] <- data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      spatial_framework = sp$spatial_framework,
      rows = nrow(dd),
      places = length(unique(dd$PLACE_ID)),
      events = sum(dd$event_internal == 1L, na.rm = TRUE),
      spatial_terms = paste(sp$spatial_terms, collapse = "; "),
      control_terms = paste(sp$control_terms, collapse = "; "),
      history_terms_requested = paste(sp$history_terms, collapse = "; "),
      history_terms_used = "",
      history_terms_dropped_nonvarying = "",
      loglik_baseline = NA_real_, loglik_full = NA_real_,
      delta_loglik_full_minus_baseline = NA_real_,
      lr_stat = NA_real_, lr_df = NA_integer_, lr_p_conventional = NA_real_,
      aic_baseline = NA_real_, aic_full = NA_real_,
      delta_aic_baseline_minus_full = NA_real_,
      concordance_baseline = NA_real_, concordance_full = NA_real_,
      delta_concordance_full_minus_baseline = NA_real_,
      robust_history_wald_chisq = NA_real_, robust_history_wald_df = NA_integer_,
      robust_history_wald_p = NA_real_,
      baseline_warning = "",
      full_warning = "",
      status = "SKIPPED_NO_COMPLETE_CASE_EVENTS",
      stringsAsFactors = FALSE
    )
    next
  }

  # Check variation on the already-fixed complete-case sample.
  # Drop non-informative terms using ONLY the already matched complete-case
  # sample. Record removed history terms in the exported comparison table.
  varying <- vapply(requested_terms, function(tm) has_variation(dd[[tm]]), logical(1))
  nonvarying <- requested_terms[!varying]

  spatial_used <- intersect(sp$spatial_terms, requested_terms[varying])
  control_used <- intersect(sp$control_terms, requested_terms[varying])
  history_used <- intersect(sp$history_terms, requested_terms[varying])
  history_dropped <- intersect(sp$history_terms, nonvarying)

  if (length(spatial_used) == 0L) {
    comparison_rows[[length(comparison_rows) + 1L]] <- data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      spatial_framework = sp$spatial_framework,
      rows = nrow(dd),
      places = length(unique(dd$PLACE_ID)),
      events = sum(dd$event_internal == 1L),
      spatial_terms = paste(sp$spatial_terms, collapse = "; "),
      control_terms = paste(control_used, collapse = "; "),
      history_terms_requested = paste(sp$history_terms, collapse = "; "),
      history_terms_used = paste(history_used, collapse = "; "),
      history_terms_dropped_nonvarying = paste(history_dropped, collapse = "; "),
      loglik_baseline = NA_real_, loglik_full = NA_real_,
      delta_loglik_full_minus_baseline = NA_real_,
      lr_stat = NA_real_, lr_df = NA_integer_, lr_p_conventional = NA_real_,
      aic_baseline = NA_real_, aic_full = NA_real_,
      delta_aic_baseline_minus_full = NA_real_,
      concordance_baseline = NA_real_, concordance_full = NA_real_,
      delta_concordance_full_minus_baseline = NA_real_,
      robust_history_wald_chisq = NA_real_, robust_history_wald_df = NA_integer_,
      robust_history_wald_p = NA_real_,
      baseline_warning = "",
      full_warning = "",
      status = "SKIPPED_NO_VARYING_SPATIAL_TERM",
      stringsAsFactors = FALSE
    )
    next
  }

  # M0 and M1 are nested by construction: M1 = M0 + surviving antecedent
  # history variables. If no history variable varies, the block test has 0 df.
  baseline_terms <- unique(c(spatial_used, control_used))
  full_terms <- unique(c(baseline_terms, history_used))

  # Both calls receive the identical 'dd' R object and event/time columns.
  # This guards against spurious LR/AIC shifts caused by unmatched rows.
  fit_base <- fit_cox_checked(dd, "event_internal", baseline_terms)
  fit_full <- fit_cox_checked(dd, "event_internal", full_terms)

  mod0 <- fit_base$model
  mod1 <- fit_full$model

  if (is.null(mod0) || is.null(mod1)) {
    comparison_rows[[length(comparison_rows) + 1L]] <- data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      spatial_framework = sp$spatial_framework,
      rows = nrow(dd),
      places = length(unique(dd$PLACE_ID)),
      events = sum(dd$event_internal == 1L),
      spatial_terms = paste(spatial_used, collapse = "; "),
      control_terms = paste(control_used, collapse = "; "),
      history_terms_requested = paste(sp$history_terms, collapse = "; "),
      history_terms_used = paste(history_used, collapse = "; "),
      history_terms_dropped_nonvarying = paste(history_dropped, collapse = "; "),
      loglik_baseline = NA_real_, loglik_full = NA_real_,
      delta_loglik_full_minus_baseline = NA_real_,
      lr_stat = NA_real_, lr_df = NA_integer_, lr_p_conventional = NA_real_,
      aic_baseline = NA_real_, aic_full = NA_real_,
      delta_aic_baseline_minus_full = NA_real_,
      concordance_baseline = NA_real_, concordance_full = NA_real_,
      delta_concordance_full_minus_baseline = NA_real_,
      robust_history_wald_chisq = NA_real_, robust_history_wald_df = NA_integer_,
      robust_history_wald_p = NA_real_,
      baseline_warning = fit_base$warning_text,
      full_warning = fit_full$warning_text,
      status = "FIT_FAILED",
      stringsAsFactors = FALSE
    )
    next
  }

  # Conventional nested partial-likelihood LR = 2*(LL1 - LL0). Because PLACE
  # clustering is used, the ordinary LR p-value is supplemental, not the
  # cluster-robust primary inference. Cox PH failure also affects inference.
  ll0_obj <- stats::logLik(mod0)
  ll1_obj <- stats::logLik(mod1)
  ll0 <- as.numeric(ll0_obj)
  ll1 <- as.numeric(ll1_obj)
  df0 <- attr(ll0_obj, "df")
  df1 <- attr(ll1_obj, "df")
  lr_df <- as.integer(max(0, df1 - df0))
  lr_stat <- 2 * (ll1 - ll0)
  lr_p <- if (lr_df > 0L && is.finite(lr_stat)) {
    stats::pchisq(lr_stat, df = lr_df, lower.tail = FALSE)
  } else {
    NA_real_
  }

  # AIC penalises additional coefficients; positive (AIC0 - AIC1) favours M1.
  # Both AIC and C are computed on the same fitting data, not test intervals.
  aic0 <- stats::AIC(mod0)
  aic1 <- stats::AIC(mod1)
  c0 <- get_concordance(mod0)
  c1 <- get_concordance(mod1)

  # Formal joint history-block comparison using PLACE-cluster robust errors.
  wb <- wald_block_robust(mod1, history_used)

  comparison_rows[[length(comparison_rows) + 1L]] <- data.frame(
    reach = reach_label,
    model = sp$model,
    transition = sp$transition,
    spatial_framework = sp$spatial_framework,
    rows = nrow(dd),
    places = length(unique(dd$PLACE_ID)),
    events = sum(dd$event_internal == 1L),
    spatial_terms = paste(spatial_used, collapse = "; "),
    control_terms = paste(control_used, collapse = "; "),
    history_terms_requested = paste(sp$history_terms, collapse = "; "),
    history_terms_used = paste(history_used, collapse = "; "),
    history_terms_dropped_nonvarying = paste(history_dropped, collapse = "; "),
    loglik_baseline = ll0,
    loglik_full = ll1,
    delta_loglik_full_minus_baseline = ll1 - ll0,
    lr_stat = lr_stat,
    lr_df = lr_df,
    lr_p_conventional = lr_p,
    aic_baseline = aic0,
    aic_full = aic1,
    delta_aic_baseline_minus_full = aic0 - aic1,
    concordance_baseline = c0,
    concordance_full = c1,
    delta_concordance_full_minus_baseline = c1 - c0,
    robust_history_wald_chisq = wb$stat,
    robust_history_wald_df = wb$df,
    robust_history_wald_p = wb$p,
    baseline_warning = fit_base$warning_text,
    full_warning = fit_full$warning_text,
    status = if (nzchar(fit_base$warning_text) || nzchar(fit_full$warning_text)) {
      "FITTED_WITH_WARNING"
    } else {
      "FITTED"
    },
    stringsAsFactors = FALSE
  )

  # Distinct lightweight inferential table for supplementary reporting.
  wald_rows[[length(wald_rows) + 1L]] <- data.frame(
    reach = reach_label,
    model = sp$model,
    transition = sp$transition,
    rows = nrow(dd),
    places = length(unique(dd$PLACE_ID)),
    events = sum(dd$event_internal == 1L),
    history_terms = paste(history_used, collapse = "; "),
    robust_wald_chisq = wb$stat,
    robust_wald_df = wb$df,
    robust_wald_p = wb$p,
    interpretation_basis = "cluster-robust covariance from full nested Cox model",
    stringsAsFactors = FALSE
  )

  # Same-sample QA: both fits were deliberately fitted to the same dd object.
  # Both Cox fit objects should report exactly the same rows and events. The
  # boolean same_input_object is procedural provenance, not independent QA.
  sample_qa_rows[[length(sample_qa_rows) + 1L]] <- data.frame(
    reach = reach_label,
    model = sp$model,
    transition = sp$transition,
    rows_baseline = mod0$n,
    rows_full = mod1$n,
    events_baseline = mod0$nevent,
    events_full = mod1$nevent,
    places_shared_input = length(unique(dd$PLACE_ID)),
    same_rows = identical(as.integer(mod0$n), as.integer(mod1$n)),
    same_events = identical(as.integer(mod0$nevent), as.integer(mod1$nevent)),
    same_input_object = TRUE,
    complete_case_defined_from_full_term_union = TRUE,
    stringsAsFactors = FALSE
  )

  # Spatial coefficient change after adding history.
  # Compare spatial coefficients before/after the history block. Such shifts
  # describe conditional confounding/association, not mechanistic causality.
  b0 <- stats::coef(mod0)
  b1 <- stats::coef(mod1)
  for (tm in spatial_used) {
    if (!tm %in% names(b0) || !tm %in% names(b1)) next
    beta0 <- as.numeric(b0[[tm]])
    beta1 <- as.numeric(b1[[tm]])
    spatial_change_rows[[length(spatial_change_rows) + 1L]] <- data.frame(
      reach = reach_label,
      model = sp$model,
      transition = sp$transition,
      term = tm,
      beta_baseline = beta0,
      beta_full = beta1,
      delta_beta_full_minus_baseline = beta1 - beta0,
      hazard_ratio_baseline = exp(beta0),
      hazard_ratio_full = exp(beta1),
      hazard_ratio_ratio_full_over_baseline = exp(beta1 - beta0),
      percent_change_abs_beta = if (is.finite(beta0) && abs(beta0) > 1e-12) {
        100 * (abs(beta1) - abs(beta0)) / abs(beta0)
      } else {
        NA_real_
      },
      stringsAsFactors = FALSE
    )
  }

  # Export individual robust history effects for interpretation alongside
  # the joint Wald test; ignore unstable or non-finite estimates where flagged.
  hc <- robust_coef_table(mod1, history_used, "history")
  if (!is.null(hc) && nrow(hc) > 0L) {
    hc$reach <- reach_label
    hc$model <- sp$model
    hc$transition <- sp$transition
    hc <- hc[, c(
      "reach", "model", "transition", "term", "block",
      "coefficient", "robust_se", "hazard_ratio",
      "conf_low_95", "conf_high_95", "robust_z", "robust_p"
    )]
    history_coef_rows[[length(history_coef_rows) + 1L]] <- hc
  }

  # Release large Cox design matrices before the next transition model; with
  # SQL-projected input this limits peak memory relative to full-model runs.
  rm(dd, mod0, mod1, fit_base, fit_full)
  invisible(gc(FALSE))
}

# Convert accumulated comparison rows to data frames; absent categories are
# written as empty CSV tables rather than fabricated statistical results.
bind_or_empty <- function(x, template = NULL) {
  if (length(x) == 0L) {
    if (is.null(template)) return(data.frame())
    return(template)
  }
  do.call(rbind, x)
}

# Five analysis outputs are generated; refer to 06_MODEL_TERM_SPECIFICATIONS
# and 00_EVENT_RISK_INTEGRITY_QA for the fit population and selected fields.
comparison_table <- bind_or_empty(comparison_rows)
wald_table <- bind_or_empty(wald_rows)
spatial_change_table <- bind_or_empty(spatial_change_rows)
sample_qa_table <- bind_or_empty(sample_qa_rows)
history_coef_table <- bind_or_empty(history_coef_rows)

utils::write.csv(
  comparison_table,
  file.path(out_dir, "01_MEMORY_MODEL_COMPARISON.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  wald_table,
  file.path(out_dir, "02_MEMORY_BLOCK_ROBUST_WALD.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  spatial_change_table,
  file.path(out_dir, "03_SPATIAL_COEFFICIENT_CHANGE.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  sample_qa_table,
  file.path(out_dir, "04_IDENTICAL_SAMPLE_QA.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  history_coef_table,
  file.path(out_dir, "05_HISTORY_COEFFICIENTS_ROBUST.csv"),
  row.names = FALSE, na = ""
)

# -----------------------------
# MEMORY_TEST_REVIEW.txt mirrors the key comparisons in a human-readable
# narrative so that publication reviewers need not open every output CSV.
# 8. Compact review summary
# -----------------------------
# Signs of deltas are explicitly defined: full-minus-baseline for C and LL,
# baseline-minus-full for AIC. The Wald test is joint/cluster-robust.
review_lines <- c(
  "FRAF COX ASSEMBLAGE MEMORY BLOCK TEST v1.0",
  paste0("Reach: ", reach_label),
  "",
  "Question:",
  "Does antecedent geomorphic history add transition-risk information after the",
  "selected contemporary spatial exposure is already included?",
  "",
  paste0(
    "Baseline model: spatial exposure",
    if (include_coverage) " + ASM_COV_FRAC observation-coverage control." else "."
  ),
  "Full model: identical baseline + antecedent geomorphic-history block.",
  "Both models use exactly the same complete-case rows, events and places.",
  "Primary inferential statistic: cluster-robust joint Wald test of the history block.",
  "Positive delta AIC (baseline minus full) favours the model containing history.",
  "Positive delta concordance (full minus baseline) means history improves ranking.",
  ""
)

# Summarise every requested transition, including nonfit dispositions; do not
# silently exclude missing-term or zero-event models from the review text.
if (nrow(comparison_table) > 0L) {
  for (i in seq_len(nrow(comparison_table))) {
    r <- comparison_table[i, ]
    review_lines <- c(
      review_lines,
      paste0("---- ", r$transition, " ----"),
      paste0("Status: ", r$status),
      paste0("Rows / places / events: ", r$rows, " / ", r$places, " / ", r$events),
      paste0("Spatial framework: ", r$spatial_framework),
      paste0("History terms used: ", r$history_terms_used),
      paste0(
        "Concordance baseline -> full: ",
        ifelse(is.finite(r$concordance_baseline), sprintf("%.6f", r$concordance_baseline), "NA"),
        " -> ",
        ifelse(is.finite(r$concordance_full), sprintf("%.6f", r$concordance_full), "NA"),
        " (delta=",
        ifelse(is.finite(r$delta_concordance_full_minus_baseline),
               sprintf("%.6f", r$delta_concordance_full_minus_baseline), "NA"),
        ")"
      ),
      paste0(
        "AIC baseline -> full: ",
        ifelse(is.finite(r$aic_baseline), sprintf("%.3f", r$aic_baseline), "NA"),
        " -> ",
        ifelse(is.finite(r$aic_full), sprintf("%.3f", r$aic_full), "NA"),
        " (delta baseline-full=",
        ifelse(is.finite(r$delta_aic_baseline_minus_full),
               sprintf("%.3f", r$delta_aic_baseline_minus_full), "NA"),
        ")"
      ),
      paste0(
        "Partial-likelihood LR: ",
        ifelse(is.finite(r$lr_stat), sprintf("%.3f", r$lr_stat), "NA"),
        " on ", ifelse(is.na(r$lr_df), "NA", r$lr_df),
        " df; conventional p=",
        ifelse(is.finite(r$lr_p_conventional),
               format.pval(r$lr_p_conventional, digits = 4, eps = 1e-4), "NA")
      ),
      paste0(
        "Robust history-block Wald: ",
        ifelse(is.finite(r$robust_history_wald_chisq),
               sprintf("%.3f", r$robust_history_wald_chisq), "NA"),
        " on ", ifelse(is.na(r$robust_history_wald_df), "NA", r$robust_history_wald_df),
        " df; p=",
        ifelse(is.finite(r$robust_history_wald_p),
               format.pval(r$robust_history_wald_p, digits = 4, eps = 1e-4), "NA")
      ),
      if (nzchar(r$baseline_warning)) paste0("Baseline warning: ", r$baseline_warning) else "",
      if (nzchar(r$full_warning)) paste0("Full-model warning: ", r$full_warning) else "",
      ""
    )
  }
}

writeLines(
  review_lines,
  file.path(out_dir, "MEMORY_TEST_REVIEW.txt"),
  useBytes = TRUE
)

writeLines(
  c(
    paste0("FRAF Cox Assemblage Memory Block Test v1.0 completed: ",
           format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
    paste0("Reach: ", reach_label),
    paste0("Models requested: ", length(specs)),
    paste0("Comparison rows written: ", nrow(comparison_table)),
    paste0("Output directory: ", out_dir)
  ),
  file.path(out_dir, "00_RUN_COMPLETED.txt"),
  useBytes = TRUE
)

# The original completion marker is written above, after the CSVs and review
# summary. A completed run is not proof that every requested model fitted;
# consult the individual status fields and warnings.
message("Assemblage memory block test completed.")
message("Main output: ", file.path(out_dir, "01_MEMORY_MODEL_COMPARISON.csv"))
