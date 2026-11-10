##FRAF Floodplain Reassemblage=group
##Cox Spatial Autocorrelation and Thinning Sensitivity v1.6 - Performance Safe - v17.10.10 Aligned=name
##RiskTable=file
##RiskLayerName=string Risk Table
##PlacePolygons=vector
##PlaceIdField=field PlacePolygons
##ReachName=selection Mamoré;Jamuna
##OutputFolder=folder
##BaseSpacingM=number 150
##ThinningSpacingsM=string 300,450,600,750
##MaxOffsetsPerSpacing=number 9
##MoranBandsM=string 0-225;225-375;375-525;525-750;750-1000;1000-1500;1500-2500
##MoranPermutations=number 49
##MoranMagnitudeThreshold=number 0.05
##MaxPlacesPerInterval=number 3000
##EventClusterDistanceM=number 225
##MinEventsForModel=number 10
##MinEventsForThinnedModel=number 50
##UseReducedReactivationThinning=boolean TRUE
##UseJamunaReactivationDiagnosticFallback=boolean TRUE
##JamunaDiagnosticMinEvents=number 50
##RunReactivation=boolean TRUE
##RunStorageFormation=boolean TRUE
##RunStabilisation=boolean TRUE
##RunStorageReworking=boolean TRUE
##WriteResidualGeoPackage=boolean TRUE
##WriteMoranPartialCheckpoints=boolean TRUE

# ARCHIVAL ANNOTATION — FRAF Paper 2 / DIAG / v1.6 (documentation-only)
# Archive filename: FRAF_P2_DIAG_ResidualSpatialDependenceThinning_v1_6.rsx
# Original source: FRAF_Cox_Spatial_Autocorrelation_Sensitivity_v1_6_PERFORMANCE_SAFE.rsx
# Role: sensitivity analysis of residual spatial dependence and coefficient stability.
# Not a production hazard-model refit, an independent-river validation, or a
# replacement for transition prediction and subsequent footprint verification.
# Original executable expressions, QGIS Processing declarations, model scopes,
# field names, thresholds, and output filenames are retained exactly.
#
# Operational dependencies: QGIS R Processing provider and R packages listed
# below; full Stage 4 / Step 3 risk table plus one geometry per PLACE_ID.
# Coordinates and bands are in metres once geometry is projected.
#
# Historical alignment qualification: this v1.6 source explicitly matches the
# v17.10.10 Cox model specifications. It should not be presented as independently
# verified against later production versions (including v17.10.15.1).
#
# Provenance caveat: three original reporting strings still say v1.5 (the
# summary `note`, 12_run_QA_log.txt `script`, and final console message).
# They are legacy metadata strings, not a change to the diagnostic calculations.
# Retained here because this archive task does not change executable code.
# ============================================================
# FRAF Cox Spatial Autocorrelation and Thinning Sensitivity v1.6
# 01-09-2026
#
# ALIGNED TO
#   Floodplain_KM_AG_Cox_STATE_v17.10.10_TWO_MODE_MEMORY_ISOLATED_REVIEW_PACK
#
# PURPOSE
#   Spatial-dependence sensitivity analysis for the historic total-time
#   Cox / Andersen-Gill transition models.
#
# v1.6 changes from v1.5
#   1) Performance-safe Moran defaults:
#        MaxPlacesPerInterval 15,000 -> 3,000;
#        MoranPermutations 199 -> 49.
#      Moran-I magnitude remains the substantive spatial-dependence diagnostic;
#      permutation p-values are retained as secondary descriptive evidence.
#   2) Explicit model/interval/band progress messages are emitted during Moran
#      analysis and model/spacing/offset messages during spatial thinning.
#   3) Optional partial Moran checkpoint CSV is rewritten after each completed
#      model so a long run has recoverable progress.
#   4) Centroid warnings are suppressed after explicit PLACE_ID-only geometry
#      preparation; this does not change centroid coordinates.
#   5) Nearest-neighbour QA now safely returns NA when no finite neighbour
#      distance can be obtained, instead of Inf.
#   6) Residual GeoPackage layers are written without deleting earlier layers.
#
# v1.5 alignment retained
#   1) DS->AD now exactly matches the v17.10.10 historic specification:
#        spatial + history core + ASM_STORAGE_FRAC_PREV_Z +
#        ASM_QUIET_SINCE_PREV_Z + ASM_N_STORAGE_EVT_PREV_Z.
#      ASM_N_REACTIVATE_PREV_Z is NOT a DS->AD term.
#   2) Mamoré AD->DS is separated into the same two v17.10.10 scopes:
#        depositional_storage_full_event:
#          all eligible storage events, assemblage-history terms only;
#        depositional_storage_local_position_subset:
#          explicit local-geometry subset with relative position/bank curvature.
#      Jamuna AD->DS retains the full-event interval-start distance model.
#   3) Output model names carry their v17.10.10 production model names and scope.
#   4) The Jamuna SF->AD convergence guard from v1.4 is retained.
#   5) QA provenance string was corrected to v1.5 and is now updated to v1.6.
#
# IMPORTANT
#   - Primary event/risk fields are read from the Stage 4 Step 3 Risk Table.
#   - PLACE_ID clustering handles repeat observations of the same place.
#   - Moran's I is calculated within observation intervals.
#   - Thinning is applied to whole PLACE_ID histories.
#   - Reduced Jamuna SF->AD fits are diagnostic sensitivity models only.
#     They do not replace the v17.10.10 primary scientific model.
# ============================================================

# Validate all required R libraries before starting a costly run.
# This script uses sf for place geometry, spdep for neighbourhood weights and
# Moran statistics, survival for cluster-robust Cox fits, and tidyverse tools
# for data assembly and publication diagnostics.
required_packages <- c("sf","dplyr","tidyr","readr","ggplot2","survival","broom","spdep")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly=TRUE)]
if (length(missing_packages)) {
  stop("Missing required R package(s): ", paste(missing_packages, collapse=", "))
}

suppressPackageStartupMessages({
  library(sf); library(dplyr); library(tidyr); library(readr)
  library(ggplot2); library(survival); library(broom); library(spdep)
})
# Use planar geometry throughout after projecting to a metric CRS.
# Fix the random seed so Moran permutation tests are reproducible for the same
# input ordering, parameter settings, and R/package implementations.
sf::sf_use_s2(FALSE)
set.seed(20260818)

# Resolve the QGIS OutputFolder parameter, create it if needed, and store
# all diagnostic CSV, image, GeoPackage and completion-marker outputs there.
out_dir <- if (exists("OutputFolder") && !is.null(OutputFolder) &&
               nzchar(as.character(OutputFolder)[1])) as.character(OutputFolder)[1] else tempdir()
dir.create(out_dir, recursive=TRUE, showWarnings=FALSE)
out_dir <- normalizePath(out_dir, winslash="/", mustWork=TRUE)

# Convert event/risk-set fields to integer 0/1 indicators.
# Missing or unparsable entries are treated as zero; investigate source coding
# when a risk set unexpectedly has no eligible observations.
int01 <- function(x) {
  z <- suppressWarnings(as.integer(as.character(x)))
  z[is.na(z)] <- 0L
  as.integer(z != 0L)
}
# Coerce textual or factor covariates to numeric without flooding QGIS logs.
# Failed conversions become NA and may reduce complete-case model support.
num_or_na <- function(x) suppressWarnings(as.numeric(as.character(x)))
# Select the first present field according to declared precedence.
# The *_PRIMARY aliases are deliberately examined before their legacy aliases.
first_existing <- function(dat,candidates) {
  h <- candidates[candidates %in% names(dat)]
  if (!length(h)) NA_character_ else h[1]
}
# Finite-only quantile helper for summaries affected by sparse diagnostics.
safe_q <- function(x,p) {
  x <- x[is.finite(x)]
  if (!length(x)) return(NA_real_)
  as.numeric(quantile(x,p,na.rm=TRUE,names=FALSE))
}
# Parse requested thinning spacings into unique positive metre distances.
parse_numeric_csv <- function(x) {
  z <- trimws(unlist(strsplit(as.character(x),",",fixed=TRUE)))
  z <- suppressWarnings(as.numeric(z))
  sort(unique(z[is.finite(z) & z>0]))
}
# Parse non-overlapping or user-specified annuli of neighbour distances.
# Each resulting row provides lower/upper bounds and a descriptive band label.
parse_distance_bands <- function(x) {
  p <- trimws(unlist(strsplit(as.character(x),";",fixed=TRUE)))
  bind_rows(lapply(p,function(s) {
    ab <- trimws(unlist(strsplit(s,"-",fixed=TRUE)))
    if (length(ab)!=2L) return(NULL)
    a <- suppressWarnings(as.numeric(ab[1])); b <- suppressWarnings(as.numeric(ab[2]))
    if (!is.finite(a)||!is.finite(b)||b<=a) return(NULL)
    tibble(dmin=a,dmax=b,band=paste0(a,"-",b," m"))
  }))
}
# Read an attribute-only risk table from GeoPackage, SQLite, CSV or RDS.
# Accept explicit |layername= URIs and provide a risk-name fallback when a
# single unambiguous risk table can be found inside a container.
read_risk_table <- function(path,layer_name="") {
  path <- as.character(path)[1]
  if (grepl("\\|layername=",path,ignore.case=TRUE)) {
    layer_name <- sub(".*\\|layername=","",path,ignore.case=TRUE)
    path <- sub("\\|.*$","",path)
  }
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("gpkg","sqlite","db")) {
    layers <- sf::st_layers(path,options="LIST_ALL_TABLES=YES")$name
    lyr <- layer_name
    if (!nzchar(lyr)||!lyr%in%layers) {
      guess <- layers[grepl("risk",layers,ignore.case=TRUE)]
      if (length(guess)==1L) lyr <- guess[1]
      else if (length(layers)==1L) lyr <- layers[1]
    }
    if (!nzchar(lyr)||!lyr%in%layers)
      stop("Could not identify RiskTable layer. Available: ",paste(layers,collapse=", "))
    obj <- suppressWarnings(sf::st_read(path,layer=lyr,quiet=TRUE,options="LIST_ALL_TABLES=YES"))
    return(if (inherits(obj,"sf")) sf::st_drop_geometry(obj) else as.data.frame(obj))
  }
  if (ext=="csv") return(readr::read_csv(path,show_col_types=FALSE,progress=FALSE))
  if (ext=="rds") return(readRDS(path))
  obj <- tryCatch(sf::st_read(path,quiet=TRUE),error=function(e)NULL)
  if (!is.null(obj)) return(sf::st_drop_geometry(obj))
  stop("Unsupported RiskTable format: ",ext)
}
# Create log1p(nonnegative distance in kilometres), then standardise it.
# Scaling uses the available full diagnostic risk table, not an origin-specific
# training split; values are used for retrospective sensitivity only.
add_logkm_z <- function(dat,nm) {
  if (!nm%in%names(dat)) return(dat)
  x <- num_or_na(dat[[nm]])
  y <- log1p(pmax(x,0)/1000)
  ok <- is.finite(y); out <- rep(NA_real_,length(y))
  if (sum(ok)>=2L) {
    s <- sd(y[ok]); if (is.finite(s)&&s>0) out[ok] <- (y[ok]-mean(y[ok]))/s
  }
  dat[[paste0(nm,"_LOGKM_Z")]] <- out
  dat
}
# Create full-record z-scores for available numeric antecedent predictors.
# A constant or under-supported variable remains NA and is filtered later.
add_z <- function(dat,nm) {
  if (!nm%in%names(dat)) return(dat)
  x <- num_or_na(dat[[nm]]); ok <- is.finite(x); out <- rep(NA_real_,length(x))
  if (sum(ok)>=2L) {
    s <- sd(x[ok]); if (is.finite(s)&&s>0) out[ok] <- (x[ok]-mean(x[ok]))/s
  }
  dat[[paste0(nm,"_Z")]] <- out
  dat
}
# Check whether a numeric covariate has finite nonzero variance.
has_var <- function(dat,nm) {
  if (!nm%in%names(dat)) return(FALSE)
  x <- num_or_na(dat[[nm]]); x <- x[is.finite(x)]
  length(x)>1L && is.finite(sd(x)) && sd(x)>0
}
# Remove predictors absent from data or without usable variation.
# The resulting diagnostic specification can be narrower than its declaration.
keep_varying <- function(dat,terms) {
  unique(terms[vapply(terms,function(tm) {
    if (!tm%in%names(dat)) return(FALSE)
    x <- dat[[tm]]
    if (is.factor(x)||is.character(x)) return(length(unique(na.omit(as.character(x))))>1L)
    z <- suppressWarnings(as.numeric(x)); s <- suppressWarnings(sd(z,na.rm=TRUE))
    is.finite(s)&&s>0
  },logical(1))])
}
# Find a complete-case model population with sufficient observed events.
# If too few events remain, drop the predictor costing the most event rows.
# This adaptive filtering supports diagnostic convergence but means a refit
# must be compared by its actual retained terms, not its declared term list.
complete_case_for_terms <- function(dat,terms,event_field,min_events=10L) {
  terms_current <- keep_varying(dat,terms)
  if (!length(terms_current)) return(list(data=dat[0,,drop=FALSE],terms=character()))
  repeat {
    cc <- complete.cases(dat[,terms_current,drop=FALSE])
    ne <- sum(int01(dat[[event_field]][cc])==1L,na.rm=TRUE)
    if (ne>=min_events || length(terms_current)<=1L) break
    losses <- vapply(terms_current,function(tm)
      sum(int01(dat[[event_field]])==1L & is.na(dat[[tm]]),na.rm=TRUE),numeric(1))
    drop_tm <- names(which.max(losses))[1]
    message("[Model prep] Dropping ",drop_tm," to retain events; event loss=",max(losses))
    terms_current <- setdiff(terms_current,drop_tm)
  }
  cc <- complete.cases(dat[,terms_current,drop=FALSE])
  list(data=dat[cc,,drop=FALSE],terms=terms_current)
}
# Fit a counting-process Cox model: Surv(tstart_yr, tstop_yr, event).
# cluster(PLACE_ID) adjusts variance for repeated observations of each fixed
# place; it does not remove spatial dependence across neighbouring places.
# Retain warnings because convergence and separation govern interpretation.
fit_cox <- function(dat,event_field,terms,label,min_events=10L) {
  if (!nrow(dat)||!length(terms)) return(NULL)
  ne <- sum(int01(dat[[event_field]])==1L,na.rm=TRUE)
  if (ne<min_events) {
    message("[Cox] ",label," skipped: only ",ne," events.")
    return(NULL)
  }
  f <- as.formula(paste0("survival::Surv(tstart_yr,tstop_yr,",event_field,") ~ ",
                         paste(terms,collapse=" + ")," + cluster(PLACE_ID)"))
  warns <- character()
  mod <- tryCatch(
    withCallingHandlers(
      survival::coxph(f,data=dat,ties="efron",x=TRUE,y=TRUE,model=TRUE),
      warning=function(w) {warns<<-c(warns,conditionMessage(w));invokeRestart("muffleWarning")}
    ),
    error=function(e) {message("[Cox] ",label," failed: ",conditionMessage(e));NULL}
  )
  if (is.null(mod)) return(NULL)
  list(model=mod,warnings=unique(warns))
}
# Recognise common coxph non-convergence/infinite-coefficient warnings.
cox_warning_nonconvergence <- function(warnings) {
  length(warnings)>0L && any(grepl(
    "did not converge|ran out of iterations|beta may be infinite|loglik converged before variable",
    warnings,ignore.case=TRUE))
}
# Require finite fitted coefficients and no recognised convergence warning.
# Other sources of bias or unsupported proportional hazards are not ruled out.
cox_fit_clean <- function(fit) {
  if (is.null(fit)||is.null(fit$model)) return(FALSE)
  cf <- coef(fit$model)
  length(cf)>0L && all(is.finite(cf)) && !cox_warning_nonconvergence(fit$warnings)
}
# Attempt reduced candidate models in order, stopping at the first clean fit.
# Used for the Jamuna SF->AD diagnostic fallback when its primary model is
# unstable. Record which terms and cohort were actually fitted.
fit_first_clean_diagnostic <- function(dat0,event_field,candidate_term_sets,label_prefix,min_events=50L) {
  audit <- list()
  for (nm in names(candidate_term_sets)) {
    prep <- complete_case_for_terms(dat0,candidate_term_sets[[nm]],event_field,min_events)
    d <- prep$data; tt <- prep$terms
    ne <- if(nrow(d))sum(int01(d[[event_field]])==1L,na.rm=TRUE)else 0L
    if(!nrow(d)||!length(tt)||ne<min_events) {
      audit[[length(audit)+1]] <- tibble(candidate=nm,n_rows=nrow(d),
        n_places=if(nrow(d))n_distinct(d$PLACE_ID)else 0L,n_events=ne,
        terms=paste(tt,collapse="; "),clean_convergence=FALSE,
        warning="SKIPPED_INSUFFICIENT_DATA_OR_EVENTS")
      next
    }
    ft <- fit_cox(d,event_field,tt,paste0(label_prefix,"_",nm),min_events)
    clean <- cox_fit_clean(ft)
    audit[[length(audit)+1]] <- tibble(candidate=nm,n_rows=nrow(d),
      n_places=n_distinct(d$PLACE_ID),n_events=ne,terms=paste(tt,collapse="; "),
      clean_convergence=clean,
      warning=if(is.null(ft))"FIT_FAILED"else paste(ft$warnings,collapse=" | "))
    if(clean) return(list(selected=list(fit=ft,data=d,terms=tt),
                         selected_name=nm,audit=bind_rows(audit)))
  }
  list(selected=NULL,selected_name=NA_character_,audit=bind_rows(audit))
}
# Extract coefficient and hazard-ratio diagnostics for each fitted model.
# Flag non-finite, extreme, and potentially separated estimates; compare signs
# with a matched 150 m reference when supplied. Interpret flagged predictors
# by direction only rather than treating unstable HR magnitudes as reliable.
model_stats <- function(fit,dat,event_field,model_name,production_model,model_scope,
                        spacing,offset_id,baseline_tidy=NULL,principal_terms=character()) {
  if(is.null(fit)) return(tibble())
  td <- broom::tidy(fit$model,conf.int=TRUE,exponentiate=FALSE) %>%
    mutate(
      hazard_ratio=exp(estimate),hr_conf_low=exp(conf.low),hr_conf_high=exp(conf.high),
      model=model_name,production_model=production_model,model_scope=model_scope,
      spacing_m=spacing,offset_id=offset_id,
      n_places=n_distinct(dat$PLACE_ID),n_rows=nrow(dat),
      n_events=sum(int01(dat[[event_field]])==1L,na.rm=TRUE),
      concordance=tryCatch(summary(fit$model)$concordance[[1]],error=function(e)NA_real_),
      predictor_role=case_when(
        model_name=="reactivation" & term=="MAM_NEAR_CHANNEL_PREV" ~ "PRINCIPAL_DIRECTION_ONLY",
        term%in%principal_terms ~ "PRINCIPAL", TRUE ~ "SECONDARY"),
      cox_warning=paste(fit$warnings,collapse=" | "),
      model_warning_flag=length(fit$warnings)>0L,
      coefficient_finite=is.finite(estimate),se_finite=is.finite(std.error),
      ci_finite=is.finite(conf.low)&is.finite(conf.high),
      very_large_abs_beta=is.finite(estimate)&abs(estimate)>8,
      very_large_se=is.finite(std.error)&std.error>5
    )
  warn_index <- NA_integer_
  if(length(fit$warnings)) {
    hit <- regmatches(fit$warnings,regexpr("variable[[:space:]]+[0-9]+",fit$warnings,ignore.case=TRUE))
    hit <- hit[nzchar(hit)]
    if(length(hit)) warn_index <- suppressWarnings(as.integer(gsub("[^0-9]","",hit[1])))
  }
  td <- td %>% mutate(
    warning_variable_index=warn_index,
    warning_targets_term=if(is.finite(warn_index))row_number()==warn_index else FALSE,
    separation_flag=(!coefficient_finite)|(!se_finite)|(!ci_finite)|
      very_large_abs_beta|very_large_se|warning_targets_term,
    interpretation_mode=case_when(
      predictor_role=="PRINCIPAL_DIRECTION_ONLY" ~ "DIRECTION_ONLY_SEPARATION",
      separation_flag ~ "DIRECTION_ONLY_SEPARATION",TRUE~"QUANTITATIVE"),
    quantitative_stability_eligible=interpretation_mode=="QUANTITATIVE"
  )
  if(!is.null(baseline_tidy)&&nrow(baseline_tidy)) {
    ref <- baseline_tidy %>% select(term,beta_baseline=estimate,hr_baseline=hazard_ratio)
    td <- td %>% left_join(ref,by="term") %>%
      mutate(delta_beta=estimate-beta_baseline,
             hr_ratio_to_baseline=hazard_ratio/hr_baseline,
             direction_same_as_baseline=case_when(
               is.na(beta_baseline)~NA,estimate==0|beta_baseline==0~NA,
               sign(estimate)==sign(beta_baseline)~TRUE,TRUE~FALSE))
  }
  td
}

# -----------------------------
# Inputs and spatial reference
# ---------------------------------
# RiskTable holds interval-start covariates, transition-specific event flags,
# and transition-specific eligibility. PlacePolygons supplies fixed-place
# geometry; it must match PLACE_ID consistently across both datasets.
# Input and coordinates
# -----------------------------
# Input-table read and place geometry alignment. Failed spatial joins are
# excluded when X/Y are checked below, potentially reducing the cohort.
risk <- read_risk_table(RiskTable,if(exists("RiskLayerName"))RiskLayerName else "")
if(!inherits(PlacePolygons,"sf")) PlacePolygons <- sf::st_as_sf(PlacePolygons)
if(!exists("PlaceIdField")||is.null(PlaceIdField)||!nzchar(PlaceIdField))
  stop("Select PlaceIdField.")
if(!PlaceIdField%in%names(PlacePolygons)) stop("PlaceIdField not found.")

reach_label <- if(exists("ReachName") && suppressWarnings(as.integer(ReachName))==1L) "Jamuna" else "Mamoré"
base_spacing <- as.numeric(BaseSpacingM)
thin_spacings <- parse_numeric_csv(ThinningSpacingsM)
moran_bands <- parse_distance_bands(MoranBandsM)
max_offsets <- max(1L,as.integer(MaxOffsetsPerSpacing))
max_places_interval <- max(100L,as.integer(MaxPlacesPerInterval))
min_events_model <- max(1L,as.integer(MinEventsForModel))
min_events_thinned <- max(min_events_model,as.integer(MinEventsForThinnedModel))
use_reduced_react_thinning <- isTRUE(UseReducedReactivationThinning)
write_moran_checkpoints <- if(exists("WriteMoranPartialCheckpoints")) isTRUE(WriteMoranPartialCheckpoints) else TRUE
moran_permutations <- suppressWarnings(as.integer(MoranPermutations))
if(!is.finite(moran_permutations) || moran_permutations < 0L) moran_permutations <- 49L

message("[v1.6] Performance-safe spatial sensitivity")
message("[v1.6] Moran maximum places per interval: ", max_places_interval)
message("[v1.6] Moran permutations per valid band: ", moran_permutations)
message("[v1.6] Thinning offsets remain capped at: ", max_offsets)
flush.console()

# Extract geometry and ID only, dissolve duplicate PLACE_ID polygons, and
# project geographic coordinates into a suitable UTM zone. A representative
# centroid supplies a repeatable one-point location for spatial diagnostics;
# it is not a measured eroding-bank or transition-event centroid.
place_geom <- PlacePolygons %>%
  mutate(PLACE_ID=as.character(.data[[PlaceIdField]])) %>% select(PLACE_ID)
if(anyDuplicated(place_geom$PLACE_ID))
  place_geom <- place_geom %>% group_by(PLACE_ID) %>% summarise(.groups="drop")
if(sf::st_is_longlat(place_geom)) {
  cen <- st_coordinates(suppressWarnings(st_centroid(st_union(place_geom))))[1,]
  zone <- floor((cen[1]+180)/6)+1
  epsg <- if(cen[2]>=0)32600+zone else 32700+zone
  place_geom <- st_transform(place_geom,epsg)
}
place_pts <- suppressWarnings(st_centroid(place_geom))
xy <- st_coordinates(place_pts)
place_lookup <- place_pts %>% mutate(X=xy[,1],Y=xy[,2]) %>%
  st_drop_geometry() %>% select(PLACE_ID,X,Y)

# JOIN KEY: assemble PLACE_ID from native PLACE_ID or legacy BLOCK_ID,
# then attach the fixed spatial coordinates to every longitudinal row.
risk_id <- first_existing(risk,c("PLACE_ID","BLOCK_ID"))
if(is.na(risk_id)) stop("Risk table requires PLACE_ID or BLOCK_ID.")
risk$PLACE_ID <- as.character(risk[[risk_id]])
risk <- risk %>% left_join(place_lookup,by="PLACE_ID")

# Counting-process exposure must have valid start and stop years.
# Legacy column aliases are interpreted only when canonical fields are absent.
if(!"tstart_yr"%in%names(risk)) {
  f <- first_existing(risk,c("YEAR1","Y1","START_YEAR","T1_YEAR","year1","y1"))
  if(is.na(f)) stop("No start-time field.")
  risk$tstart_yr <- num_or_na(risk[[f]])
}
if(!"tstop_yr"%in%names(risk)) {
  f <- first_existing(risk,c("YEAR2","Y2","END_YEAR","T2_YEAR","year2","y2"))
  if(is.na(f)) stop("No stop-time field.")
  risk$tstop_yr <- num_or_na(risk[[f]])
}
risk$tstart_yr <- num_or_na(risk$tstart_yr)
risk$tstop_yr <- num_or_na(risk$tstop_yr)
risk$interval_id <- paste0(format(round(risk$tstart_yr,6),trim=TRUE),"_",
                           format(round(risk$tstop_yr,6),trim=TRUE))

# authoritative primary fields
# Primary state-event and risk-set definitions take precedence over legacy
# fields; each outcome has a separate eligible denominator. This script
# analyses SF->AD, AD->DS, DS->SF and DS->AD, not broad FP->AD prediction.
aliases <- list(
 REACTIVATE_EVT=c("REACTIVATE_EVT_PRIMARY","REACTIVATE_EVT"),
 STORAGE_EVT=c("STORAGE_EVT_PRIMARY","STORAGE_EVT"),
 STABILISE_EVT=c("STABILISE_EVT_PRIMARY","STABILISE_EVT"),
 STORAGE_REWORK_EVT=c("STORAGE_REWORK_EVT_PRIMARY","STORAGE_REWORK_EVT"),
 REACTIVATE_RISK_SET=c("REACTIVATE_RISK_SET_PRIMARY","REACTIVATE_RISK_SET"),
 STORAGE_RISK_SET=c("STORAGE_RISK_SET_PRIMARY","STORAGE_RISK_SET"),
 STABILISE_RISK_SET=c("STABILISE_RISK_SET_PRIMARY","STABILISE_RISK_SET"),
 STORAGE_REWORK_RISK_SET=c("STORAGE_REWORK_RISK_SET_PRIMARY","STORAGE_REWORK_RISK_SET"))
for(target in names(aliases)) {
  src <- first_existing(risk,aliases[[target]])
  if(is.na(src)) stop("Required primary/fallback field missing: ",target)
  risk[[target]] <- int01(risk[[src]])
}
# Compatibility fallback: if the dedicated DS->AD population is empty,
# substitute the DS-origin STABILISE_RISK_SET. This is an existing analytical
# choice and should be reported when triggered; it is not the broad FP risk set.
# v17.10.10 DS risk fallback
if(sum(risk$STORAGE_REWORK_RISK_SET==1L,na.rm=TRUE)==0L &&
   sum(risk$STABILISE_RISK_SET==1L,na.rm=TRUE)>0L) {
  warning("Dedicated DS->AD risk set empty; using STABILISE_RISK_SET as common DS origin population.")
  risk$STORAGE_REWORK_RISK_SET <- risk$STABILISE_RISK_SET
}

# Only valid person/place-time intervals with matched coordinates remain.
# Missing positions are excluded from both residual and thinning analyses.
risk <- risk %>% filter(is.finite(tstart_yr),is.finite(tstop_yr),tstop_yr>tstart_yr,
                        is.finite(X),is.finite(Y))

# -----------------------------
# Antecedent predictor preparation
# ---------------------------------
# Covariates ending in _PREV represent history known before interval onset.
# The model is retrospective; this routine must not reinterpret the derived
# full-record z-scores as independently trained forecast standardisation.
# Predictor preparation
# -----------------------------
# Coerce only recognised source fields to numeric before transformed spatial
# predictors and antecedent assemblage-history z-scores are constructed.
numeric_fields <- c(
 "ASM_N_REACTIVATE_PREV","ASM_N_STORAGE_EVT_PREV","ASM_N_STABILISE_PREV",
 "ASM_DIST_FREQ_PREV","ASM_STORAGE_FRAC_PREV","ASM_STAB_FP_FRAC_PREV",
 "ASM_QUIET_SINCE_PREV","ASM_N_EPISODES_PREV","ASM_MAX_QUIET_PREV",
 "ASM_DOM_RATIO_PREV","ASM_COV_FRAC",
 "DIST_ACTIVE_CURR","DIST_WATER_CURR","DIST_CL_REF","DIST_CL_CURR",
 "DIST_CHANNEL_PREV","DIST_BANK_PREV","BANK_SETBACK_PREV",
 "INSIDE_CHANNEL_PREV","OUTER_BANK_PREV","INNER_BANK_PREV",
 "NEAR_CHANNEL_HALF_PREV","NEAR_CHANNEL_FULL_PREV",
 "NEAR_BANK_HALF_PREV","NEAR_BANK_FULL_PREV",
 "OUTER_CURV_REACT_HALF_PREV","OUTER_CURV_REACT_FULL_PREV",
 "INNER_CURV_STORAGE_HALF_PREV","INNER_CURV_STORAGE_FULL_PREV",
 "OUTER_CURV_STORAGE_HALF_PREV","OUTER_CURV_STORAGE_FULL_PREV",
 "REL_CHANNEL_POS_PREV","GEOM_SUPPORT_PREV","M3_MODEL_ELIGIBLE_PRIMARY")
for(nm in intersect(numeric_fields,names(risk))) risk[[nm]] <- num_or_na(risk[[nm]])
for(nm in c("DIST_ACTIVE_CURR","DIST_WATER_CURR","DIST_CL_REF","DIST_CL_CURR",
            "DIST_CHANNEL_PREV","DIST_BANK_PREV","BANK_SETBACK_PREV"))
  risk <- add_logkm_z(risk,nm)

# Return a numeric vector or NA vector for optional source covariates.
get_num <- function(dat,nm) if(nm%in%names(dat))num_or_na(dat[[nm]])else rep(NA_real_,nrow(dat))
# Convert logical geometry predicates to explicit binary covariates.
indicator01 <- function(x){y<-as.logical(x);y[is.na(y)]<-FALSE;as.integer(y)}
# Mamoré geometry indicators describe previous-margin proximity,
# inner/outer-bank exposure, and curvature. The coding follows the aligned
# historic script and should not be generalised to Jamuna geometry.
risk$MAM_NEAR_CHANNEL_PREV <- get_num(risk,"NEAR_CHANNEL_FULL_PREV")
risk$MAM_OUTER_REACT_EXPOSED_PREV <- indicator01(
  get_num(risk,"INSIDE_CHANNEL_PREV")==0 & get_num(risk,"OUTER_BANK_PREV")==1 &
  get_num(risk,"NEAR_CHANNEL_FULL_PREV")==1)
risk$MAM_OUTER_CURV_REACT_PREV <- get_num(risk,"OUTER_CURV_REACT_FULL_PREV")
risk$MAM_NEAR_BANK_STORAGE_PREV <- get_num(risk,"NEAR_BANK_HALF_PREV")
risk$MAM_INNER_STORAGE_EXPOSED_PREV <- indicator01(
  get_num(risk,"INSIDE_CHANNEL_PREV")==1 & get_num(risk,"INNER_BANK_PREV")==1 &
  get_num(risk,"NEAR_BANK_HALF_PREV")==1)
risk$MAM_OUTER_STORAGE_EXPOSED_PREV <- indicator01(
  get_num(risk,"INSIDE_CHANNEL_PREV")==1 & get_num(risk,"OUTER_BANK_PREV")==1 &
  get_num(risk,"NEAR_BANK_HALF_PREV")==1)
risk$MAM_INNER_CURV_STORAGE_PREV <- get_num(risk,"INNER_CURV_STORAGE_HALF_PREV")
risk$MAM_OUTER_CURV_STORAGE_PREV <- get_num(risk,"OUTER_CURV_STORAGE_HALF_PREV")

for(nm in c("ASM_STORAGE_FRAC_PREV","ASM_STAB_FP_FRAC_PREV","ASM_DOM_RATIO_PREV",
            "ASM_N_EPISODES_PREV","ASM_MAX_QUIET_PREV","ASM_QUIET_SINCE_PREV",
            "ASM_COV_FRAC","ASM_N_REACTIVATE_PREV","ASM_N_STORAGE_EVT_PREV",
            "ASM_N_STABILISE_PREV","REL_CHANNEL_POS_PREV",
            "MAM_OUTER_CURV_REACT_PREV","MAM_INNER_CURV_STORAGE_PREV",
            "MAM_OUTER_CURV_STORAGE_PREV")) risk <- add_z(risk,nm)

# Select river-specific spatial parametrisation when Mamoré local-geometry
# support is populated. Otherwise use one available distance predictor as
# the common Jamuna/braided-style fallback.
has_local_geom_support <- reach_label=="Mamoré" &&
  all(c("GEOM_SUPPORT_PREV","DIST_CHANNEL_PREV","INSIDE_CHANNEL_PREV")%in%names(risk)) &&
  any(num_or_na(risk$GEOM_SUPPORT_PREV)==1,na.rm=TRUE)

if(has_local_geom_support) {
  react_spatial <- c("MAM_NEAR_CHANNEL_PREV","MAM_OUTER_REACT_EXPOSED_PREV",
                     "MAM_OUTER_CURV_REACT_PREV_Z")
  storage_full_spatial <- character()
  storage_local_spatial <- c("REL_CHANNEL_POS_PREV_Z","MAM_NEAR_BANK_STORAGE_PREV",
    "MAM_INNER_STORAGE_EXPOSED_PREV","MAM_INNER_CURV_STORAGE_PREV_Z",
    "MAM_OUTER_STORAGE_EXPOSED_PREV","MAM_OUTER_CURV_STORAGE_PREV_Z")
  stabilise_spatial <- "DIST_CHANNEL_PREV_LOGKM_Z"
  rework_spatial <- react_spatial
  spatial_framework <- "Mamoré interval-start local geometry; AD->DS full-event/local-position scopes separated"
} else {
  fallback <- if(has_var(risk,"DIST_ACTIVE_CURR_LOGKM_Z"))"DIST_ACTIVE_CURR_LOGKM_Z" else
    if(has_var(risk,"DIST_CL_REF_LOGKM_Z"))"DIST_CL_REF_LOGKM_Z" else
    if(has_var(risk,"DIST_CL_CURR_LOGKM_Z"))"DIST_CL_CURR_LOGKM_Z" else
    if(has_var(risk,"DIST_WATER_CURR_LOGKM_Z"))"DIST_WATER_CURR_LOGKM_Z" else character()
  react_spatial <- storage_full_spatial <- stabilise_spatial <- rework_spatial <- fallback
  storage_local_spatial <- character()
  spatial_framework <- if(length(fallback))paste("Jamuna/braided interval-start spatial predictor:",fallback) else "No spatial predictor"
}

# Core assemblage-memory terms are antecedent composition, episode count,
# quiet-time maximum, and coverage fraction. Transition-specific terms are
# appended in the model specification block below.
history_core <- c("ASM_DOM_RATIO_PREV_Z","ASM_N_EPISODES_PREV_Z",
                  "ASM_MAX_QUIET_PREV_Z","ASM_COV_FRAC_Z")

# Restrict each transition to its own risk population.
# Mamoré AD->DS local-position analysis additionally requires supported
# local geometry and the eligible within-channel position subset.
apply_model_scope <- function(dat,sp) {
  dat <- dat %>% filter(.data[[sp$risk]]==1L)
  if(identical(sp$scope,"local_geometry_subset")) {
    req <- c("GEOM_SUPPORT_PREV","INSIDE_CHANNEL_PREV","REL_CHANNEL_POS_PREV_Z")
    if(!all(req%in%names(dat))) return(dat[0,,drop=FALSE])
    dat <- dat %>% filter(GEOM_SUPPORT_PREV==1L,INSIDE_CHANNEL_PREV==1L,
                          is.finite(REL_CHANNEL_POS_PREV_Z))
  }
  dat
}

# Declare *distinct* scientific transition models and eligible populations.
# Mamoré AD->DS has both full-event and explicit local-position subset
# scopes, so their coefficients are not assumed to estimate identical risks.
# All labels refer to the production model v17.10.10, not v17.10.15.1.
model_specs <- list(
 reactivation=list(run=isTRUE(RunReactivation),risk="REACTIVATE_RISK_SET",event="REACTIVATE_EVT",
   label="Stabilised Floodplain -> Active Domain",production_model="active_domain_reactivation",
   scope="full_risk_set",
   terms=c(react_spatial,history_core,"ASM_N_REACTIVATE_PREV_Z"),
   principal_terms=react_spatial),
 storage_formation_full_event=list(run=isTRUE(RunStorageFormation),risk="STORAGE_RISK_SET",event="STORAGE_EVT",
   label="Active Domain -> Depositional Storage",production_model="depositional_storage_full_event",
   scope="full_event",
   terms=c(storage_full_spatial,history_core,"ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
   principal_terms=c(storage_full_spatial,"ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z")),
 storage_formation_local_position_subset=list(run=isTRUE(RunStorageFormation)&&has_local_geom_support,
   risk="STORAGE_RISK_SET",event="STORAGE_EVT",
   label="Active Domain -> Depositional Storage (local-position subset)",
   production_model="depositional_storage_local_position_subset",scope="local_geometry_subset",
   terms=c(storage_local_spatial,history_core,"ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
   principal_terms=c(storage_local_spatial,"ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z")),
 stabilisation=list(run=isTRUE(RunStabilisation),risk="STABILISE_RISK_SET",event="STABILISE_EVT",
   label="Depositional Storage -> Stabilised Floodplain",production_model="floodplain_stabilisation",
   scope="full_risk_set",
   terms=c(stabilise_spatial,history_core,"ASM_STORAGE_FRAC_PREV_Z","ASM_STAB_FP_FRAC_PREV_Z",
           "ASM_QUIET_SINCE_PREV_Z","ASM_N_STABILISE_PREV_Z"),
   principal_terms=c(stabilise_spatial,"ASM_STORAGE_FRAC_PREV_Z","ASM_STAB_FP_FRAC_PREV_Z")),
 storage_reworking=list(run=isTRUE(RunStorageReworking),risk="STORAGE_REWORK_RISK_SET",
   event="STORAGE_REWORK_EVT",label="Depositional Storage -> Active Domain",
   production_model="depositional_storage_reworking",scope="full_risk_set",
   terms=c(rework_spatial,history_core,"ASM_STORAGE_FRAC_PREV_Z",
           "ASM_QUIET_SINCE_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
   principal_terms=c(rework_spatial,"ASM_STORAGE_FRAC_PREV_Z"))
)
model_specs <- model_specs[vapply(model_specs,function(z)isTRUE(z$run),logical(1))]

# A thinning sensitivity comparison is only like-for-like with its explicit
# 150 m reference. The optional SF->AD reduced thinning model omits one
# history term, so it is labelled diagnostic rather than the production fit.
# thinning terms
# First process the enabled model definitions; disabling a transition
# here changes the diagnostic scope, not the original historical model.
for(nm in names(model_specs)) {
  model_specs[[nm]]$thinning_terms <- model_specs[[nm]]$terms
  model_specs[[nm]]$thinning_note <- "Same specification as aligned v17.10.10 150 m model"
}
if("reactivation"%in%names(model_specs)&&use_reduced_react_thinning) {
  model_specs$reactivation$thinning_terms <- setdiff(model_specs$reactivation$terms,"ASM_N_REACTIVATE_PREV_Z")
  model_specs$reactivation$thinning_note <-
    "Reduced SF->AD thinning diagnostic excludes ASM_N_REACTIVATE_PREV_Z; primary model retained separately"
}

# Jamuna SF->AD may separate or fail to converge; diagnostic fallbacks
# are tried in declared order and identified in all output provenance.
jamuna_react_diag_candidates <- list()
if(reach_label=="Jamuna"&&"reactivation"%in%names(model_specs)) {
  sp <- model_specs$reactivation$principal_terms
  jamuna_react_diag_candidates <- list(
    FULL_MINUS_REACT_COUNT=setdiff(model_specs$reactivation$terms,"ASM_N_REACTIVATE_PREV_Z"),
    REDUCED_NO_COV_REACTCOUNT=unique(c(sp,"ASM_DOM_RATIO_PREV_Z","ASM_N_EPISODES_PREV_Z","ASM_MAX_QUIET_PREV_Z")),
    SPATIAL_PLUS_EPISODES_QUIET=unique(c(sp,"ASM_N_EPISODES_PREV_Z","ASM_MAX_QUIET_PREV_Z")),
    SPATIAL_ONLY=unique(sp))
}

# Persist actual declared/refit terms, production labels, scope, and
# river-specific spatial framework before any lengthy modelling.
write_csv(bind_rows(lapply(names(model_specs),function(nm)tibble(
  model=nm,production_model=model_specs[[nm]]$production_model,
  model_scope=model_specs[[nm]]$scope,transition=model_specs[[nm]]$label,
  spatial_framework=spatial_framework,
  declared_terms=paste(model_specs[[nm]]$terms,collapse="; "),
  thinning_terms=paste(model_specs[[nm]]$thinning_terms,collapse="; "),
  thinning_model_note=model_specs[[nm]]$thinning_note,
  principal_terms=paste(model_specs[[nm]]$principal_terms,collapse="; ")
))),file.path(out_dir,"00_spatial_sensitivity_model_specifications.csv"))

# -----------------------------
# Baseline, residual and contingency model fitting
# ------------------------------------------------
# Fit each complete-case transition-specific 150 m model and retain warning,
# coefficient and event-support QA. Martingale residuals are derived from a
# clean fallback *only* if the guarded Jamuna SF->AD primary fit fails.
# Baseline and diagnostic fits
# -----------------------------
# Create separate stores for primary 150 m fits, diagnostic residual fits,
# and their actual fitted terms. A fallback does not silently replace primary
# scientific coefficients in the baseline export.
baseline_models <- baseline_data <- baseline_terms <- baseline_tidy <- list()
diagnostic_models <- diagnostic_data <- diagnostic_terms <- diagnostic_tidy <- diagnostic_source <- list()
diagnostic_audit <- residual_rows <- all_model_stats <- list()

use_jamuna_fallback <- isTRUE(UseJamunaReactivationDiagnosticFallback)
jamuna_min_events <- max(min_events_model,as.integer(JamunaDiagnosticMinEvents))

for(nm in names(model_specs)) {
  sp <- model_specs[[nm]]
  dat0 <- apply_model_scope(risk,sp)
  prep <- complete_case_for_terms(dat0,sp$terms,sp$event,min_events_model)
  dat <- prep$data; terms <- prep$terms
  fit <- fit_cox(dat,sp$event,terms,nm,min_events_model)
  if(is.null(fit)) next
  baseline_models[[nm]]<-fit;baseline_data[[nm]]<-dat;baseline_terms[[nm]]<-terms
  td0 <- model_stats(fit,dat,sp$event,nm,sp$production_model,sp$scope,
                     base_spacing,"FULL_150M",principal_terms=sp$principal_terms)
  td0$primary_model_clean_convergence <- cox_fit_clean(fit)
  baseline_tidy[[nm]]<-td0;all_model_stats[[paste0(nm,"_baseline")]]<-td0

  diag_fit<-fit;diag_dat<-dat;diag_terms<-terms;diag_name<-"PRIMARY_150M"
  if(nm=="reactivation"&&reach_label=="Jamuna"&&use_jamuna_fallback&&!cox_fit_clean(fit)) {
    fb <- fit_first_clean_diagnostic(dat0,sp$event,jamuna_react_diag_candidates,
                                     "reactivation_DIAGNOSTIC",jamuna_min_events)
    if(nrow(fb$audit)) {
      fb$audit$model<-nm;fb$audit$production_model<-sp$production_model
      diagnostic_audit[[nm]]<-fb$audit
    }
    if(is.null(fb$selected)) stop("Jamuna SF->AD: no clean diagnostic fallback converged.")
    diag_fit<-fb$selected$fit;diag_dat<-fb$selected$data;diag_terms<-fb$selected$terms
    diag_name<-paste0("DIAGNOSTIC_",fb$selected_name)
  }
  diagnostic_models[[nm]]<-diag_fit;diagnostic_data[[nm]]<-diag_dat
  diagnostic_terms[[nm]]<-diag_terms;diagnostic_source[[nm]]<-diag_name
  dtd <- model_stats(diag_fit,diag_dat,sp$event,nm,sp$production_model,sp$scope,
                     base_spacing,diag_name,principal_terms=sp$principal_terms)
  dtd$diagnostic_model_source<-diag_name
  dtd$diagnostic_clean_convergence<-cox_fit_clean(diag_fit)
  diagnostic_tidy[[nm]]<-dtd

  # Martingale residuals are event minus fitted cumulative hazard under the
  # specified Cox model. Their spatial dependence is assessed within intervals;
  # residual clustering is not itself an event-occurrence prediction metric.
  rr <- residuals(diag_fit$model,type="martingale")
  if(length(rr)!=nrow(diag_dat)) stop("Residual length mismatch: ",nm)
  diag_dat$MARTINGALE_RESID<-as.numeric(rr)
  diag_dat$MODEL_NAME<-nm;diag_dat$PRODUCTION_MODEL<-sp$production_model
  diag_dat$MODEL_SCOPE<-sp$scope;diag_dat$TRANSITION_LABEL<-sp$label
  diag_dat$DIAGNOSTIC_MODEL_SOURCE<-diag_name
  diagnostic_data[[nm]]<-diag_dat
  residual_rows[[nm]]<-diag_dat %>% select(
    PLACE_ID,X,Y,interval_id,tstart_yr,tstop_yr,all_of(sp$event),
    MARTINGALE_RESID,MODEL_NAME,PRODUCTION_MODEL,MODEL_SCOPE,
    TRANSITION_LABEL,DIAGNOSTIC_MODEL_SOURCE)
}

# Stop when no model can be fitted; otherwise export the actual term,
# cohort, convergence and residual-model selection information for each fit.
if(!length(baseline_models)) stop("No baseline Cox model could be fitted.")
write_csv(bind_rows(baseline_tidy),file.path(out_dir,"01_baseline_cox_coefficients.csv"))
write_csv(bind_rows(diagnostic_tidy),file.path(out_dir,"01a_spatial_diagnostic_cox_coefficients.csv"))
if(length(diagnostic_audit))
  write_csv(bind_rows(diagnostic_audit),file.path(out_dir,"01c_jamuna_reactivation_diagnostic_model_audit.csv"))
write_csv(bind_rows(lapply(names(diagnostic_models),function(nm)tibble(
 model=nm,production_model=model_specs[[nm]]$production_model,model_scope=model_specs[[nm]]$scope,
 transition=model_specs[[nm]]$label,
 primary_model_clean_convergence=cox_fit_clean(baseline_models[[nm]]),
 spatial_diagnostic_source=diagnostic_source[[nm]],
 spatial_diagnostic_terms=paste(diagnostic_terms[[nm]],collapse="; "),
 spatial_diagnostic_clean_convergence=cox_fit_clean(diagnostic_models[[nm]])
))),file.path(out_dir,"01d_spatial_diagnostic_model_selection_summary.csv"))

# -----------------------------
# Reference fit for thinning comparisons
# -------------------------------------
# Create a 150 m fit that uses *the same terms* as the thinned refits. Where
# the clean Jamuna SF->AD fallback is necessary, that fallback becomes the
# diagnostic reference, while the production baseline remains separately stored.
# Like-for-like thinning reference
# -----------------------------
thin_ref_models<-thin_ref_data<-thin_ref_terms<-thin_ref_tidy<-list()
for(nm in names(diagnostic_models)) {
  sp<-model_specs[[nm]]
  if(nm=="reactivation"&&reach_label=="Jamuna"&&startsWith(diagnostic_source[[nm]],"DIAGNOSTIC_")) {
    dat_ref<-diagnostic_data[[nm]] %>% select(-MARTINGALE_RESID,-MODEL_NAME,-PRODUCTION_MODEL,
      -MODEL_SCOPE,-TRANSITION_LABEL,-DIAGNOSTIC_MODEL_SOURCE)
    terms_ref<-diagnostic_terms[[nm]];fit_ref<-diagnostic_models[[nm]]
    ref_note<-paste0("Jamuna SF->AD uses clean diagnostic reference: ",diagnostic_source[[nm]])
  } else {
    dat0<-apply_model_scope(risk,sp)
    prep<-complete_case_for_terms(dat0,sp$thinning_terms,sp$event,min_events_model)
    dat_ref<-prep$data;terms_ref<-prep$terms
    fit_ref<-fit_cox(dat_ref,sp$event,terms_ref,paste0(nm,"_THINNING_REFERENCE"),min_events_model)
    if(is.null(fit_ref))next
    ref_note<-sp$thinning_note
  }
  st<-model_stats(fit_ref,dat_ref,sp$event,nm,sp$production_model,sp$scope,
                  base_spacing,"THINNING_REFERENCE_150M",principal_terms=sp$principal_terms)
  st$thinning_model_note<-ref_note;st$reference_clean_convergence<-cox_fit_clean(fit_ref)
  thin_ref_models[[nm]]<-fit_ref;thin_ref_data[[nm]]<-dat_ref
  thin_ref_terms[[nm]]<-terms_ref;thin_ref_tidy[[nm]]<-st
}
write_csv(bind_rows(thin_ref_tidy),file.path(out_dir,"01b_thinning_reference_150m_coefficients.csv"))

# -----------------------------
# Within-interval residual spatial dependence
# -------------------------------------------
# For each transition and observation interval, measure correlation between
# place-wise Martingale residuals in user-defined distance annuli. This
# preserves temporal bracketing, though shared geomorphic events can still
# create dependence between adjacent spatial observations.
# Moran I within intervals
# -----------------------------
# Construct distance-band neighbours; request a KD-tree when supported.
# Used for both residual Moran's I and event-cluster connected components.
make_nb <- function(coords,dmin,dmax) {
  args<-list(x=coords,d1=dmin,d2=dmax,row.names=NULL)
  if("use_kd_tree"%in%names(formals(spdep::dnearneigh)))args$use_kd_tree<-TRUE
  do.call(spdep::dnearneigh,args)
}

moran_rows<-list()
# The partial checkpoint file is rewritten after each finished model and
# removed only following successful creation of the complete Moran CSV.
# It provides recovery evidence after a long or interrupted computation.
moran_checkpoint_file <- file.path(out_dir,"02_residual_moran_by_interval_distance_PARTIAL.csv")
if(file.exists(moran_checkpoint_file)) file.remove(moran_checkpoint_file)

moran_model_names <- names(residual_rows)
# Progress reports identify model, interval and band to make long runs
# diagnosable. Data reduction below applies only to Moran computation.
for(mi in seq_along(moran_model_names)) {
  nm <- moran_model_names[mi]
  rd <- residual_rows[[nm]]
  interval_ids <- unique(rd$interval_id)

  message(sprintf("[Moran] model %d/%d: %s (%d intervals)",
                  mi,length(moran_model_names),nm,length(interval_ids)))
  flush.console()

  for(ii in seq_along(interval_ids)) {
    iid <- interval_ids[ii]
    z<-rd%>%filter(interval_id==iid,is.finite(MARTINGALE_RESID),is.finite(X),is.finite(Y))
    n_full<-nrow(z)
    if(n_full<20) {
      message(sprintf("[Moran]   interval %d/%d %s skipped: n=%d <20",
                      ii,length(interval_ids),iid,n_full))
      flush.console()
      next
    }

    sampled<-FALSE
    # Performance-safe deterministic spatially ordered subsampling caps each
    # interval's Moran calculation (v1.6 default 3,000 places). This limits
    # computational cost but makes Moran estimates sample-dependent.
    if(nrow(z)>max_places_interval) {
      # Deterministic spatially ordered sample: reproducible and memory-safe.
      z<-z%>%arrange(X,Y)
      idx<-unique(round(seq(1,nrow(z),length.out=max_places_interval)))
      z<-z[idx,,drop=FALSE]
      sampled<-TRUE
    }

    message(sprintf("[Moran]   interval %d/%d %s: %d/%d places%s",
                    ii,length(interval_ids),iid,nrow(z),n_full,
                    if(sampled)" [sampled]" else ""))
    flush.console()

    coords<-as.matrix(z[,c("X","Y")])
    vals<-z$MARTINGALE_RESID

    for(b in seq_len(nrow(moran_bands))) {
      message(sprintf("[Moran]     band %d/%d: %s",
                      b,nrow(moran_bands),moran_bands$band[b]))
      flush.console()

      nb<-tryCatch(
        make_nb(coords,moran_bands$dmin[b],moran_bands$dmax[b]),
        error=function(e) {
          message("[Moran]       neighbour construction failed: ",conditionMessage(e))
          NULL
        })
      if(is.null(nb)) next

      # Skip distance bands with inadequate neighbour connectivity. Zero
      # neighbours are allowed in the weight object but do not establish spatial
      # correlation on their own.
      nlinks<-sum(lengths(nb))/2
      nwith<-sum(lengths(nb)>0)
      if(nlinks<5||nwith<10) {
        message(sprintf("[Moran]       skipped: links=%d, places-with-neighbours=%d",
                        nlinks,nwith))
        flush.console()
        next
      }

      lw<-tryCatch(
        nb2listw(nb,style="W",zero.policy=TRUE),
        error=function(e) {
          message("[Moran]       weights failed: ",conditionMessage(e))
          NULL
        })
      if(is.null(lw)) next

      # Compute row-standardised Moran's I for a specific residual interval/band.
      # A positive value indicates local similarity under these spatial weights;
      # a negative value indicates dissimilarity. Interpretation is conditional
      # on sampled locations and the fitted model.
      obs<-tryCatch(
        spdep::moran(vals,lw,n=length(vals),S0=Szero(lw),zero.policy=TRUE)$I,
        error=function(e) NA_real_)

      # Permutation significance is secondary. The downstream v1.6 summary
      # classifies descriptive dependence from Moran-I magnitude.
      mc <- NULL
      # Permutation p-values are secondary descriptive checks, not the cutoff
      # used to classify residual dependence in the final summary (49 by default).
      # Permutation counts limit the resolution of reported p-values.
      if(moran_permutations > 0L) {
        mc<-tryCatch(
          moran.mc(vals,lw,nsim=moran_permutations,
                   zero.policy=TRUE,return_boot=FALSE),
          error=function(e) {
            message("[Moran]       permutation test failed: ",conditionMessage(e))
            NULL
          })
      }

      moran_rows[[length(moran_rows)+1]]<-tibble(
        model=nm,
        production_model=model_specs[[nm]]$production_model,
        model_scope=model_specs[[nm]]$scope,
        transition=model_specs[[nm]]$label,
        interval_id=iid,
        tstart_yr=z$tstart_yr[1],
        tstop_yr=z$tstop_yr[1],
        distance_band=moran_bands$band[b],
        dmin_m=moran_bands$dmin[b],
        dmax_m=moran_bands$dmax[b],
        n_places_full_interval=n_full,
        n_places_used=nrow(z),
        interval_sampled=sampled,
        n_places_with_neighbours=nwith,
        n_pair_links=nlinks,
        moran_I=obs,
        permutation_p=if(is.null(mc))NA_real_ else mc$p.value,
        permutations=moran_permutations
      )
    }
  }

  if(write_moran_checkpoints && length(moran_rows)) {
    write_csv(bind_rows(moran_rows),moran_checkpoint_file)
    message("[Moran] checkpoint written after model: ",nm)
    flush.console()
  }
}

moran_detail<-bind_rows(moran_rows)
# The full Moran detail is saved before the temporary checkpoint is
# removed. Empty results remain distinguishable from successful evidence.
write_csv(moran_detail,file.path(out_dir,"02_residual_moran_by_interval_distance.csv"))
if(file.exists(moran_checkpoint_file)) file.remove(moran_checkpoint_file)

if(nrow(moran_detail)) {
 # Summarise interval-wise I distributions by model and distance band.
 # Medians are across observed intervals, not area-weighted residual moments.
 moran_summary<-moran_detail%>%
  group_by(model,production_model,model_scope,transition,distance_band,dmin_m,dmax_m)%>%
  summarise(
   n_intervals=n(),
   median_moran_I=median(moran_I,na.rm=TRUE),
   q25_moran_I=safe_q(moran_I,.25),
   q75_moran_I=safe_q(moran_I,.75),
   max_moran_I=max(moran_I,na.rm=TRUE),
   proportion_positive=mean(moran_I>0,na.rm=TRUE),
   proportion_p_lt_0_05=mean(permutation_p<.05,na.rm=TRUE),
   median_places_used=median(n_places_used,na.rm=TRUE),
   proportion_intervals_sampled=mean(interval_sampled%in%TRUE,na.rm=TRUE),
   .groups="drop")
} else {
 moran_summary<-tibble()
}
write_csv(moran_summary,file.path(out_dir,"03_residual_moran_summary.csv"))

if(nrow(moran_summary)) {
 p<-ggplot(moran_summary,aes(x=(dmin_m+dmax_m)/2,y=median_moran_I,
                             group=model,linetype=model))+
   geom_hline(yintercept=0,linewidth=.3)+
   geom_line()+geom_point()+
   labs(x="Distance-band midpoint (m)",y="Median within-interval Moran's I",
        title=paste0(reach_label," Cox martingale residual spatial correlogram"))+
   theme_bw()
 ggsave(file.path(out_dir,"04_residual_moran_correlogram.png"),p,width=9,height=6,dpi=200)
}

# -----------------------------
# Transition-event cluster descriptors
# ------------------------------------
# Build distance-connected components of *event-positive* places within each
# observation interval. This characterises scale/aggregation of mapped event
# cells but is not a separate physical erosion-footprint reconciliation.
# Event clustering
# -----------------------------
# Label connected components in the event-neighbour graph.
# This describes spatial event agglomeration, not independently observed
# physical erosion objects or statistically independent event counts.
components_nb<-function(nb){
 n<-length(nb);comp<-rep(NA_integer_,n);cid<-0L
 for(i in seq_len(n)){if(!is.na(comp[i]))next;cid<-cid+1L;q<-i;comp[i]<-cid
  while(length(q)){v<-q[1];q<-q[-1];nei<-nb[[v]];nei<-nei[nei>0 & is.na(comp[nei])]
   if(length(nei)){comp[nei]<-cid;q<-c(q,nei)}}}
 comp
}
cluster_rows<-list()
for(nm in names(diagnostic_data)) {
 dat<-diagnostic_data[[nm]];ef<-model_specs[[nm]]$event
 for(iid in unique(dat$interval_id)) {
  ev<-dat%>%filter(interval_id==iid,.data[[ef]]==1L,is.finite(X),is.finite(Y))%>%distinct(PLACE_ID,.keep_all=TRUE)
  ne<-nrow(ev)
  if(ne==0)sizes<-integer() else if(ne==1)sizes<-1L else {
   nb<-tryCatch(make_nb(as.matrix(ev[,c("X","Y")]),0,as.numeric(EventClusterDistanceM)),error=function(e)NULL)
   if(is.null(nb))next;sizes<-as.integer(table(components_nb(nb)))
  }
  cluster_rows[[length(cluster_rows)+1]]<-tibble(
   model=nm,production_model=model_specs[[nm]]$production_model,model_scope=model_specs[[nm]]$scope,
   transition=model_specs[[nm]]$label,interval_id=iid,n_event_places=ne,
   n_event_clusters=length(sizes),median_cluster_places=if(length(sizes))median(sizes)else NA_real_,
   max_cluster_places=if(length(sizes))max(sizes)else NA_real_,
   pct_events_in_largest_cluster=if(ne>0)100*max(sizes)/ne else NA_real_,
   cluster_distance_m=as.numeric(EventClusterDistanceM))
 }
}
event_clusters<-bind_rows(cluster_rows)
# Emit the per-interval cluster audit for each diagnostic transition model.
write_csv(event_clusters,file.path(out_dir,"05_event_cluster_summary_by_interval.csv"))

# -----------------------------
# Place-history thinning sensitivity
# ----------------------------------
# Repeat Cox refits after selecting one retained place per offset square
# block at 300/450/600/750 m (configurable). This is a sensitivity to dense
# spatial sampling, not a spatially blocked held-out forecast experiment.
# Spatial block thinning
# -----------------------------
unique_places<-place_lookup%>%filter(is.finite(X),is.finite(Y))
# Generate x/y lattice offsets at increments of the base grid spacing.
# Cap their count with deterministic subsampling to control runtime.
build_offsets<-function(spacing){
 offs<-seq(0,spacing-base_spacing,by=base_spacing);if(!length(offs))offs<-0
 g<-expand.grid(offset_x=offs,offset_y=offs)
 if(nrow(g)>max_offsets){idx<-unique(round(seq(1,nrow(g),length.out=max_offsets)));g<-g[idx,,drop=FALSE]}
 g$offset_id<-paste0("OX",g$offset_x,"_OY",g$offset_y);g
}
# Choose one PLACE_ID nearest each shifted square-block centre.
# The selection occurs once at the place level; *all* at-risk intervals for
# selected places are retained to avoid splitting their event histories.
select_block_sample<-function(pl,spacing,ox,oy){
 x0<-min(pl$X);y0<-min(pl$Y)
 pl%>%mutate(BX=floor((X-x0-ox)/spacing),BY=floor((Y-y0-oy)/spacing),
  CX=x0+ox+(BX+.5)*spacing,CY=y0+oy+(BY+.5)*spacing,D2=(X-CX)^2+(Y-CY)^2)%>%
  group_by(BX,BY)%>%slice_min(D2,n=1,with_ties=FALSE)%>%ungroup()%>%pull(PLACE_ID)
}
# Audit actual nearest-neighbour separations after nominal block thinning.
# Increase search radius progressively; use NA if no finite neighbour distance
# can be measured rather than reporting an artificial infinity.
nn_summary<-function(pl){
 if(nrow(pl)<2)return(tibble(nn_min=NA_real_,nn_median=NA_real_,nn_q25=NA_real_,nn_q75=NA_real_))
 coords<-as.matrix(pl[,c("X","Y")]);nearest<-rep(NA_real_,nrow(coords));rad<-max(base_spacing*1.5,1)
 for(iter in 1:8){
  nb<-tryCatch(make_nb(coords,0,rad),error=function(e)NULL);if(is.null(nb))break
  for(i in seq_along(nb))if(!is.finite(nearest[i])&&length(nb[[i]])){
   j<-nb[[i]];nearest[i]<-min(sqrt((coords[j,1]-coords[i,1])^2+(coords[j,2]-coords[i,2])^2))}
  if(mean(is.finite(nearest))>.99)break;rad<-rad*2
 }
 finite_nearest<-nearest[is.finite(nearest)]
 if(!length(finite_nearest))
   return(tibble(nn_min=NA_real_,nn_median=NA_real_,nn_q25=NA_real_,nn_q75=NA_real_))
 tibble(nn_min=min(finite_nearest),nn_median=safe_q(finite_nearest,.5),
        nn_q25=safe_q(finite_nearest,.25),nn_q75=safe_q(finite_nearest,.75))
}
# Retain full 150 m place-count and observed nearest-neighbour spacing
# as the reference against which nominal spacing changes can be assessed.
thin_qa<-list()
bnn<-nn_summary(unique_places)
thin_qa[[1]]<-tibble(spacing_m=base_spacing,offset_id="FULL_150M",n_places=nrow(unique_places),
 nn_min_m=bnn$nn_min,nn_median_m=bnn$nn_median,nn_q25_m=bnn$nn_q25,nn_q75_m=bnn$nn_q75)

# Each thinning offset yields one reduced spatial set. A fit is skipped
# when event support falls below MinEventsForThinnedModel (default 50).
thin_run_spacings <- thin_spacings[thin_spacings>base_spacing]
for(si in seq_along(thin_run_spacings)) {
 spacing <- thin_run_spacings[si]
 offsets_this <- build_offsets(spacing)
 message(sprintf("[Thinning] spacing %d/%d: %g m (%d offsets)",
                 si,length(thin_run_spacings),spacing,nrow(offsets_this)))
 flush.console()
 for(j in seq_len(nrow(offsets_this))) {
  off<-offsets_this[j,]
  message(sprintf("[Thinning]   offset %d/%d: %s",
                  j,nrow(offsets_this),off$offset_id))
  flush.console()
  ids<-select_block_sample(unique_places,spacing,off$offset_x,off$offset_y)
  ps<-unique_places%>%filter(PLACE_ID%in%ids);nn<-nn_summary(ps)
  thin_qa[[length(thin_qa)+1]]<-tibble(spacing_m=spacing,offset_id=off$offset_id,n_places=length(ids),
   nn_min_m=nn$nn_min,nn_median_m=nn$nn_median,nn_q25_m=nn$nn_q25,nn_q75_m=nn$nn_q75)
  for(nm in names(thin_ref_models)) {
   message("[Thinning]     model: ",nm)
   flush.console()
   sp<-model_specs[[nm]];d<-thin_ref_data[[nm]]%>%filter(PLACE_ID%in%ids)
   ne<-sum(d[[sp$event]]==1L,na.rm=TRUE)
   if(ne<min_events_thinned)next
   ft<-fit_cox(d,sp$event,thin_ref_terms[[nm]],paste0(nm,"_",spacing,"_",off$offset_id),min_events_thinned)
   if(is.null(ft))next
   st<-model_stats(ft,d,sp$event,nm,sp$production_model,sp$scope,spacing,off$offset_id,
                   thin_ref_tidy[[nm]],sp$principal_terms)
   st$thinning_model_note<-sp$thinning_note
   all_model_stats[[paste(nm,spacing,off$offset_id,sep="_")]]<-st
  }
 }
}
thinning_qa<-bind_rows(thin_qa)
# Export realized spacing QA separately from model coefficients.
write_csv(thinning_qa,file.path(out_dir,"06_thinning_spatial_QA.csv"))
write_csv(thinning_qa%>%group_by(spacing_m)%>%summarise(
 n_offsets=n(),median_actual_nn_m=median(nn_median_m,na.rm=TRUE),
 q25_actual_nn_m=safe_q(nn_median_m,.25),q75_actual_nn_m=safe_q(nn_median_m,.75),.groups="drop"),
 file.path(out_dir,"06b_nominal_vs_actual_thinning_spacing.csv"))

# Join Cox coefficient diagnostics to actual nearest-neighbour spacing.
# Preserve warning/separation flags for every fitted offset and predictor.
coef_all<-bind_rows(all_model_stats)%>%left_join(
 thinning_qa%>%select(spacing_m,offset_id,nn_min_m,nn_median_m,nn_q25_m,nn_q75_m),
 by=c("spacing_m","offset_id"))
write_csv(coef_all,file.path(out_dir,"07_thinning_cox_all_coefficients.csv"))
sep_audit<-coef_all%>%select(any_of(c("model","production_model","model_scope","spacing_m","offset_id","term",
 "predictor_role","n_places","n_rows","n_events","estimate","std.error","conf.low","conf.high",
 "hazard_ratio","hr_conf_low","hr_conf_high","cox_warning","model_warning_flag","separation_flag",
 "interpretation_mode","quantitative_stability_eligible","nn_min_m","nn_median_m")))
write_csv(sep_audit,file.path(out_dir,"07b_cox_convergence_separation_audit.csv"))
write_csv(sep_audit%>%filter(separation_flag%in%TRUE),file.path(out_dir,"07c_cox_flagged_separation_terms.csv"))

# Coefficient-stability summaries exclude flagged estimates from numeric
# HR/beta quantiles, but keep direction-only evidence separately. Direction
# agreement refers to the explicit 150 m thinning reference, not a held-out
# evaluation against new observations.
coef_summary<-coef_all%>%filter(spacing_m>base_spacing,!is.na(term))%>%
 group_by(model,production_model,model_scope,term,predictor_role,spacing_m)%>%
 summarise(n_offsets=n(),n_offsets_flagged_separation=sum(separation_flag%in%TRUE,na.rm=TRUE),
  proportion_offsets_flagged_separation=mean(separation_flag%in%TRUE,na.rm=TRUE),
  n_quantitative_offsets=sum(quantitative_stability_eligible%in%TRUE,na.rm=TRUE),
  median_actual_nn_m=median(nn_median_m,na.rm=TRUE),
  median_beta=if(any(quantitative_stability_eligible%in%TRUE))median(estimate[quantitative_stability_eligible%in%TRUE],na.rm=TRUE)else NA_real_,
  q25_beta=if(any(quantitative_stability_eligible%in%TRUE))safe_q(estimate[quantitative_stability_eligible%in%TRUE],.25)else NA_real_,
  q75_beta=if(any(quantitative_stability_eligible%in%TRUE))safe_q(estimate[quantitative_stability_eligible%in%TRUE],.75)else NA_real_,
  median_hr=if(any(quantitative_stability_eligible%in%TRUE))median(hazard_ratio[quantitative_stability_eligible%in%TRUE],na.rm=TRUE)else NA_real_,
  median_delta_beta=if(any(quantitative_stability_eligible%in%TRUE))median(delta_beta[quantitative_stability_eligible%in%TRUE],na.rm=TRUE)else NA_real_,
  proportion_same_direction=mean(direction_same_as_baseline%in%TRUE,na.rm=TRUE),
  median_concordance=median(concordance,na.rm=TRUE),.groups="drop")%>%
 mutate(stability_interpretation=ifelse(predictor_role=="PRINCIPAL_DIRECTION_ONLY"|n_quantitative_offsets==0,
                                       "DIRECTION_ONLY_SEPARATION","QUANTITATIVE"))
write_csv(coef_summary,file.path(out_dir,"08_thinning_coefficient_stability_summary.csv"))
write_csv(coef_summary%>%filter(stability_interpretation=="DIRECTION_ONLY_SEPARATION"),
          file.path(out_dir,"08b_direction_only_separation_terms.csv"))

# -----------------------------
# Optional residual mapping outputs
# ---------------------------------
# Write model-specific layers containing place centroids joined to
# per-interval Martingale residuals. The source deletes any existing residual
# GeoPackage before writing; later layers must append, not replace it.
# Residual GeoPackage
# -----------------------------
if(isTRUE(WriteResidualGeoPackage)&&length(residual_rows)) {
 ra<-bind_rows(residual_rows)
 gpkg<-file.path(out_dir,"10_cox_martingale_residuals.gpkg")
 if(file.exists(gpkg))file.remove(gpkg)
 first_layer <- TRUE
 for(nm in unique(ra$MODEL_NAME)) {
  x<-place_pts%>%select(PLACE_ID)%>%
    left_join(ra%>%filter(MODEL_NAME==nm),by="PLACE_ID")
  layer_name <- paste0("residuals_",nm)
  if(first_layer) {
    st_write(x,gpkg,layer=layer_name,quiet=TRUE,delete_dsn=FALSE,delete_layer=TRUE)
    first_layer <- FALSE
  } else {
    st_write(x,gpkg,layer=layer_name,quiet=TRUE,delete_layer=TRUE)
  }
 }
}

# -----------------------------
# Integrative QA and interpretation
# ---------------------------------
# Combine descriptive Moran range, event-cluster size, thinning direction
# consistency and separation rates into one per-model summary. This assesses
# robustness and residual dependence, not proof of independent observations.
# Overall summary
# -----------------------------
summary_rows<-list()
moran_threshold<-as.numeric(MoranMagnitudeThreshold)
if(!is.finite(moran_threshold)||moran_threshold<0)moran_threshold<-.05
for(nm in names(baseline_models)) {
 base<-baseline_tidy[[nm]]
 ms<-moran_summary%>%filter(model==nm)
 cs<-event_clusters%>%filter(model==nm)
 th<-coef_summary%>%filter(model==nm)
 # IMPORTANT: Despite the parameter label 'magnitude threshold', the actual
 # code uses median Moran's I >= threshold; negative I of the same absolute
 # magnitude is not counted. This preserved v1.6 convention measures extent
 # of positive residual autocorrelation, not absolute dependence magnitude.
 hit<-ms%>%filter(median_moran_I>=moran_threshold)
 corr_extent<-if(!nrow(ms))NA_real_ else if(nrow(hit))max(hit$dmax_m,na.rm=TRUE) else 0
 qp<-th%>%filter(predictor_role=="PRINCIPAL",stability_interpretation=="QUANTITATIVE")
 qd<-th%>%filter(predictor_role=="PRINCIPAL_DIRECTION_ONLY"|stability_interpretation=="DIRECTION_ONLY_SEPARATION")
 summary_rows[[nm]]<-tibble(
  reach=reach_label,model=nm,production_model=model_specs[[nm]]$production_model,
  model_scope=model_specs[[nm]]$scope,transition=model_specs[[nm]]$label,
  baseline_places=unique(base$n_places)[1],baseline_rows=unique(base$n_rows)[1],
  baseline_events=unique(base$n_events)[1],baseline_concordance=unique(base$concordance)[1],
  moran_magnitude_threshold=moran_threshold,descriptive_residual_correlation_extent_m=corr_extent,
  median_event_cluster_count=if(nrow(cs))median(cs$n_event_clusters,na.rm=TRUE)else NA_real_,
  median_largest_cluster_pct=if(nrow(cs))median(cs$pct_events_in_largest_cluster,na.rm=TRUE)else NA_real_,
  mean_principal_quantitative_thinning_direction_stability=if(nrow(qp))mean(qp$proportion_same_direction,na.rm=TRUE)else NA_real_,
  mean_direction_only_term_thinning_direction_stability=if(nrow(qd))mean(qd$proportion_same_direction,na.rm=TRUE)else NA_real_,
  baseline_any_separation_flag=any(base$separation_flag%in%TRUE,na.rm=TRUE),
  mean_thinning_separation_flag_rate=if(nrow(th))mean(th$proportion_offsets_flagged_separation,na.rm=TRUE)else NA_real_,
  note="v1.5 aligned to v17.10.10; correlation extent uses median Moran I magnitude, not significance.")
}
overall<-bind_rows(summary_rows)
# Per-model synthesis is intended for sensitivity reporting; it should
# be read alongside the raw Moran and coefficient-level audit tables.
write_csv(overall,file.path(out_dir,"11_spatial_dependence_overall_summary.csv"))

# Preserve the original run QA log for downstream reproduction.
# The existing `script=` field still names v1.5; that legacy reporting label
# has deliberately not been modified in this documentation-only version.
capture.output(list(
 script="FRAF_Cox_Spatial_Autocorrelation_Sensitivity_v1_5",
 aligned_production_script="Floodplain_KM_AG_Cox_STATE_v17.10.10",
 reach=reach_label,base_spacing_m=base_spacing,thinning_spacings_m=thin_spacings,
 max_offsets_per_spacing=max_offsets,moran_bands=moran_bands,
 moran_permutations=as.integer(MoranPermutations),
 moran_magnitude_threshold=moran_threshold,
 event_cluster_distance_m=as.numeric(EventClusterDistanceM),
 models_fitted=names(baseline_models),
 production_models=vapply(model_specs,function(z)z$production_model,character(1)),
 model_scopes=vapply(model_specs,function(z)z$scope,character(1)),
 min_events_for_model=min_events_model,min_events_for_thinned_model=min_events_thinned,
 spatial_framework=spatial_framework,
 risk_rows_after_time_coordinate_filter=nrow(risk),
 unique_places_in_risk=n_distinct(risk$PLACE_ID),place_polygons=nrow(place_lookup)
),file=file.path(out_dir,"12_run_QA_log.txt"))

# Write the v1.6 completion marker after all declared outputs are saved.
# This does not certify convergence of every attempted transition/offset.
writeLines(c(
 "FRAF Cox Spatial Autocorrelation Sensitivity v1.6 completed.",
 paste0("Reach: ",reach_label),
 "Aligned production model: v17.10.10",
 paste0("Output: ",out_dir)
),file.path(out_dir,"00_SPATIAL_SENSITIVITY_COMPLETED.txt"))

# Existing completion-message label is v1.5 although script is v1.6.
# No functional change made; archive users should use the file header and
# 00_SPATIAL_SENSITIVITY_COMPLETED.txt for the intended code version.
message("[Spatial sensitivity v1.5] Complete.")
message("Key outputs: 00_spatial_sensitivity_model_specifications.csv; ",
        "01_baseline_cox_coefficients.csv; 03_residual_moran_summary.csv; ",
        "07b_cox_convergence_separation_audit.csv; ",
        "08_thinning_coefficient_stability_summary.csv; ",
        "11_spatial_dependence_overall_summary.csv")
