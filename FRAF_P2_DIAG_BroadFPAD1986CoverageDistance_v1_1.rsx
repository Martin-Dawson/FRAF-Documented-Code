##FRAF Floodplain Reassemblage=group
##Broad FP to AD - Paired Cox + 1986 / Distance Checks v1.1=name
##OriginalRiskTable=file
##OriginalRiskLayerName=string AUTO
##SensitivityRiskTable=file
##SensitivityRiskLayerName=string Risk Table
##OutputFolder=folder
##ReachName=selection Mamoré;Jamuna
##RunHistoric=boolean TRUE
##RunRolling=boolean TRUE
##RunPHDiagnostics=boolean FALSE
##ForecastOrigins=string 10,20,30
##OriginInterpretation=selection Unique interval-start rank;Elapsed study year
##MinimumTrainingEvents=number 20
##WritePredictionRows=boolean FALSE
##InventoryVerified=boolean FALSE
##RunMamore1986Exclusion=boolean TRUE
##RunDistanceDiagnostics=boolean TRUE

# FRAF FP->AD paired sensitivity v1.1 - standalone QGIS R Processing script.
# Adapted specifically from FRAF_v17_10_15_1_Mamore_DSAD_Final.rsx.
# Does not modify the original table, the sensitivity GPKG, or other transition models.
# This compares the v17.10.15.1 SPATIAL-ONLY broad Cox specification
# with original versus recovered-zero endpoint eligibility, at the same dates.
# Both historical elapsed-time and rolling interval gap-time fits are reported.
# Predicted events and binary outcomes are unchanged; recovered zero intervals are
# PROVISIONAL until the dated AD layer inventory and overlap coverage are verified.

# [FRAF P2 / DIAG-86: ARCHIVE IDENTITY AND SCOPE]
# Archived name: FRAF_P2_DIAG_BroadFPAD1986CoverageDistance_v1_1.rsx.
# Original name: FRAF_Broad_FP_AD_Cox_1986_Distance_Sensitivity_v1_1.rsx.
# Documentation is comment-only: the QGIS Processing header, statements, thresholds,
# model fits and original output filenames are retained exactly.
# This is a separate broad-FP-to-AD 1986 eligibility/distance sensitivity,
# NOT the generating executable for the principal September/October predictions.
# It does not establish independently whether the 1986 source imagery is complete.
# The manuscript connection is S3.3, with comparison to supplementary evidence.
#
# [FRAF P2 / DIAG-86: ONTOLOGY AND CAUSAL POPULATION]
# Broad eligible FP is the upstream eligible pre-existing floodplain plus
# Stabilised Floodplain (SF), excluding Depositional Storage (DS).
# FP is the prediction/eligibility risk population, NOT an additional assemblage
# state, and this routine does not construct those risk/event fields.
# The comparisons depend on eligibility and FP->AD event flags supplied in
# both upstream GeoPackages; they do not revise geomorphic state assignments.
suppressPackageStartupMessages({
  if (!requireNamespace("sf", quietly=TRUE)) stop("R package 'sf' required (used by production script).")
  if (!requireNamespace("survival", quietly=TRUE)) stop("R package 'survival' required.")
  library(survival)
})

# [FRAF P2 / DIAG-86: GEO-PACKAGE URI HELPER]
# QGIS may supply a file path with an appended '|layername=...' fragment;
# this helper strips that suffix before passing the path to sf/GDAL.
raw_path <- function(x) {
  p <- trimws(as.character(x)[1L]); if (!nzchar(p) || is.na(p)) stop("Empty GeoPackage input path")
  sub("\\|.*$", "", p)
}
# [FRAF P2 / DIAG-86: OPTIONAL LAYER-NAME PARSING]
# Extract an explicit layername from a QGIS URI if present; otherwise use
# the configured layer label or an unambiguous automatic match.
uri_layer <- function(x) {
  p <- as.character(x)[1L]
  m <- regexec("\\|layername=([^|]+)",p,ignore.case=TRUE)
  r <- regmatches(p,m)[[1L]]
  if (length(r)>1L) r[2L] else NULL
}
# [FRAF P2 / DIAG-86: SQL SAFETY AND NUMERIC COERCION]
# Quote SQLite identifiers before assembling queries. Numeric/binary helpers
# standardise counts but never reconstruct event or eligibility classifications.
qi <- function(x) paste0('"', gsub('"','""', as.character(x), fixed=TRUE), '"')
scalar_num <- function(x) suppressWarnings(as.numeric(x))
int01 <- function(x) as.integer(scalar_num(x)==1)
# [FRAF P2 / DIAG-86: RESULTS WRITER]
# Results are written to a new timestamped directory below OutputFolder.
# Original result filenames are deliberately unchanged for run provenance.
write_out <- function(x,name) {
  utils::write.csv(as.data.frame(x), file.path(out,name), row.names=FALSE, na="")
}
# [FRAF P2 / DIAG-86: SELECTIVE EXTRACTION]
# Read only requested fields/rows from the GeoPackage rather than loading
# the much wider production risk table into R memory. Geometry is removed.
read_sql <- function(gpkg, sql) {
  z <- suppressWarnings(sf::st_read(gpkg, query=sql, quiet=TRUE, options="LIST_ALL_TABLES=YES"))
  if (inherits(z,"sf")) z <- sf::st_drop_geometry(z)
  as.data.frame(z, stringsAsFactors=FALSE)
}
# [FRAF P2 / DIAG-86: INPUT LAYER DISCOVERY]
# The original and sensitivity tables may be non-spatial GeoPackage layers.
# The names of internal gpkg_/rtree_ support layers are not candidates.
get_layers <- function(gpkg) sf::st_layers(gpkg, options="LIST_ALL_TABLES=YES")$name
# [FRAF P2 / DIAG-86: UNAMBIGUOUS LAYER SELECTION]
# AUTO accepts a preferred Risk Table name or a single remaining data layer;
# ambiguous choices terminate rather than silently choosing an arbitrary layer.
get_layer <- function(gpkg, label, embedded=NULL) {
  if (!file.exists(gpkg)) stop("GeoPackage not found: ",gpkg)
  ls <- get_layers(gpkg)
  desired <- if (!is.null(embedded)) embedded else as.character(label)[1L]
  if (is.na(desired) || toupper(trimws(desired)) == "AUTO" || !nzchar(trimws(desired))) {
    preferred <- c("Risk Table","RISK_TABLE","Risk_Table")
    found <- preferred[preferred %in% ls]
    if (length(found)>0L) return(found[1L])
    cand <- ls[!grepl("^(gpkg_|rtree_)", ls)]
    if (length(cand)==1L) return(cand[1L])
    stop("Ambiguous Risk Table layer: ", paste(ls,collapse="; "),". Specify table name.")
  }
  if (!desired %in% ls) stop("Layer '",desired,"' not found in ",gpkg,". Found: ",paste(ls,collapse=", "))
  desired
}
# [FRAF P2 / DIAG-86: FIELD PRESENCE CHECK]
# Inspect schema before any comparative fitting. Schema checks cannot alone
# prove that input files are from the same dated spatial reconstruction.
fields_in <- function(gpkg, layer) {
  z <- suppressWarnings(sf::st_read(gpkg, layer=layer, quiet=TRUE,
                   options="LIST_ALL_TABLES=YES", n_max=1))
  names(z)
}

# [FRAF P2 / DIAG-86: TWO INDEPENDENT SOURCE FILES]
# OriginalRiskTable is the authoritative baseline. SensitivityRiskTable
# contains the original columns plus provisional zero-recovery eligibility.
# Distinct file paths are enforced; these are not two layers of one file.
orig_path <- raw_path(OriginalRiskTable)
sens_path <- raw_path(SensitivityRiskTable)
orig_layer <- get_layer(orig_path,OriginalRiskLayerName,uri_layer(OriginalRiskTable))
sens_layer <- get_layer(sens_path,SensitivityRiskLayerName,uri_layer(SensitivityRiskTable))
if (normalizePath(orig_path,winslash="/",mustWork=TRUE)==normalizePath(sens_path,winslash="/",mustWork=TRUE)) {
  stop("Original and sensitivity input paths must be DIFFERENT GeoPackages.")
}
# [FRAF P2 / DIAG-86: REACH AND RUN DIRECTORY]
# The selectable reach is Mamore/Jamuna; the year-1986 exclusion is Mamore-only.
# QGIS choice indices may be numeric (0=Mamore, 1=Jamuna) or textual.
# A timestamped output directory and RUN_STARTED marker isolate each attempt.
reach_code <- suppressWarnings(as.integer(ReachName[1L]))
reach_text <- tolower(trimws(as.character(ReachName)[1L]))
reach <- if ((is.finite(reach_code) && reach_code==1L) ||
             identical(reach_text,"jamuna")) "Jamuna" else "Mamoré"
base <- trimws(as.character(OutputFolder)[1L]); if (!nzchar(base)||is.na(base)) stop("Output folder required")
dir.create(base,recursive=TRUE,showWarnings=FALSE)
out <- file.path(base,paste0("FRAF_", ifelse(reach=="Jamuna","Jamuna","Mamore"),
  "_Broad_FP_AD_1986_Distance_Sensitivity_v1_1_",format(Sys.time(),"%Y%m%dT%H%M%S")))
dir.create(out,recursive=TRUE,showWarnings=FALSE)
if (!dir.exists(out)) stop("Cannot create output directory: ",out)
writeLines(c("STATUS: RUN_STARTED",as.character(Sys.time()),orig_path,sens_path),file.path(out,"00_RUN_STARTED.txt"))

# [FRAF P2 / DIAG-86: FAIL-FAST RUN CONTROLLER]
# Main processing runs inside a tryCatch; a failure writes 00_RUN_FAILED.txt
# and is rethrown. A RUN_STARTED file does not establish completion.
tryCatch({
  message("Original: ",orig_path," / ",orig_layer)
  message("Sensitivity: ",sens_path," / ",sens_layer)
# [FRAF P2 / DIAG-86: REQUIRED UPSTREAM COLUMNS]
# Original baseline needs eligibility/event flags and timing. The sensitivity
# table additionally needs PLACE_ID, interval ends, T1 distance, source and
# original-versus-recovered-zero eligibility/event fields.
# No missing source column is silently inferred from another field.
  orig_cols <- fields_in(orig_path,orig_layer)
  sens_cols <- fields_in(sens_path,sens_layer)
  required_orig <- c("tstart_yr","y1","FP_REACTIVATE_RISK_SET_PRIMARY",
                     "FP_REACTIVATE_EVT_PRIMARY","FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY")
  required_sens <- c("PLACE_ID","tstart_yr","tstop_yr","y1","y2","DIST_ACTIVE_CURR",
                     "FP_REACTIVATE_RISK_SET_PRIMARY","FP_REACTIVATE_EVT_PRIMARY",
                     "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY","FP_REACTIVATE_RISK_SET_SENS",
                     "FP_REACTIVATE_EVT_SENS","FP_REACTIVATE_MODEL_ELIGIBLE_SENS",
                     "FP_SENS_RECOVER_ZERO","FP_REACTIVATE_SOURCE_PRIMARY")
  miss_o <- setdiff(required_orig,orig_cols)
  miss_s <- setdiff(required_sens,sens_cols)
  if (length(miss_o)||length(miss_s)) stop("Missing input fields. Original: ",
         paste(miss_o,collapse=", ")," | Sensitivity: ",paste(miss_s,collapse=", "))

# [FRAF P2 / DIAG-86: BASELINE COUNTS MUST AGREE]
# SQL preflight checks the original broad risk-set row, eligible and event
# counts against unchanged original fields in the sensitivity GeoPackage.
# This is a count-level audit, not a row-level hash or independent geometry QA.
# The program aborts if any compared total differs.
  # Independent integrity preflight against the authoritative FULL Risk Table.
  sumsql <- function(tab) paste0(
    'SELECT COUNT(*) AS n_raw, ',
    'SUM(CASE WHEN "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY" = 1 THEN 1 ELSE 0 END) AS n_eligible, ',
    'SUM(CASE WHEN "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY" = 1 AND "FP_REACTIVATE_EVT_PRIMARY" = 1 THEN 1 ELSE 0 END) AS n_events ',
    'FROM ',qi(tab),' WHERE "FP_REACTIVATE_RISK_SET_PRIMARY" = 1')
  sum_o <- read_sql(orig_path,sumsql(orig_layer)); sum_s <- read_sql(sens_path,sumsql(sens_layer))
  for (f in c("n_raw","n_eligible","n_events")) {
    if (!isTRUE(all.equal(scalar_num(sum_o[[f]][1L]),scalar_num(sum_s[[f]][1L]))))
      stop("Sensitivity table does not reproduce authoritative ORIGINAL ",f,
           ": original=",sum_o[[f]][1L]," sensitivity=",sum_s[[f]][1L])
  }
  write_out(data.frame(source=c("authoritative_original","original_fields_in_sensitivity"),
        n_raw=c(sum_o$n_raw,sum_s$n_raw),n_eligible=c(sum_o$n_eligible,sum_s$n_eligible),
        n_events=c(sum_o$n_events,sum_s$n_events)),"00_source_integrity_QA.csv")

# [FRAF P2 / DIAG-86: ORIGIN FRAME PROVENANCE]
# Rebuild unique interval-start ranks using the FULL original risk table,
# not only raw FP eligible rows, so ranks follow the production calendar.
# Do not interpret default ranks 10/20/30 as the final T25/T30/T35 forecasts.
  # Replicate production origin ranks using the FULL authoritative table,
  # not the subset of raw broad-risk rows (which might omit some start dates).
  ori <- read_sql(orig_path,paste0('SELECT DISTINCT "tstart_yr", "y1" FROM ',qi(orig_layer),
                                   ' ORDER BY CAST("tstart_yr" AS REAL), "y1"'))
  ori$tstart_yr <- scalar_num(ori$tstart_yr)
  ori <- ori[is.finite(ori$tstart_yr),,drop=FALSE]
  ori <- ori[order(ori$tstart_yr),,drop=FALSE]
  ori$origin_rank <- seq_len(nrow(ori))
  if (anyDuplicated(ori$tstart_yr)) {
    warning("Multiple y1 values share interval-start elapsed time; rank matches production DISTINCT(tstart_yr,y1).")
  }
  write_out(ori,"01_available_origin_ranks.csv")

# [FRAF P2 / DIAG-86: MEMORY-SCOPED RISK DATA]
# Load the raw broad FP risk population from the sensitivity file,
# retaining only fields used in paired fits and QA; this subset is not
# an independent reconstruction of the full ontology.
  keep <- intersect(c(required_sens,"BLOCK_ID","ASM_BLOCK_AREA_M2","FP_SENS_RECOVER_LOW"),sens_cols)
  sql <- paste0('SELECT ',paste(vapply(keep,qi,character(1)),collapse=", "),
                ' FROM ',qi(sens_layer),' WHERE "FP_REACTIVATE_RISK_SET_PRIMARY" = 1')
  message("Loading only ",length(keep)," columns of the broad-risk sensitivity table (not full 350+ field table)...")
  d <- read_sql(sens_path,sql)
  if (!nrow(d)) stop("No raw broad FP->AD risk rows.")
  for (col in c("tstart_yr","tstop_yr","DIST_ACTIVE_CURR")) d[[col]]<-scalar_num(d[[col]])
  binary_cols <- c("FP_REACTIVATE_RISK_SET_PRIMARY","FP_REACTIVATE_EVT_PRIMARY",
                   "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY","FP_REACTIVATE_RISK_SET_SENS",
                   "FP_REACTIVATE_EVT_SENS","FP_REACTIVATE_MODEL_ELIGIBLE_SENS","FP_SENS_RECOVER_ZERO")
  for (col in binary_cols) d[[col]]<-int01(d[[col]])
  d$PLACE_ID<-as.character(d$PLACE_ID)
# [FRAF P2 / DIAG-86: EXPOSURE AND DISTANCE TRANSFORMATION]
# Duration is elapsed risk time. DIST_ACTIVE_CURR is treated here as a
# nonnegative metre distance and transformed by log1p(distance / 1000).
# Its true interval-start geometry lineage depends on the upstream lookup;
# this script does not independently recompute polygon-to-PLACE distance.
  d$duration<-d$tstop_yr-d$tstart_yr
  d$log_margin<-ifelse(is.finite(d$DIST_ACTIVE_CURR) & d$DIST_ACTIVE_CURR>=0,
                        log1p(pmax(d$DIST_ACTIVE_CURR,0)/1000),NA_real_)
  if ("ASM_BLOCK_AREA_M2" %in% names(d)) d$area<-scalar_num(d$ASM_BLOCK_AREA_M2) else d$area<-rep(1,nrow(d))
  d$area[!is.finite(d$area)|d$area<=0]<-1
# [FRAF P2 / DIAG-86: PAIRED ELIGIBILITY CONTRAST]
# Both scenarios retain the SAME original FP->AD event labels and raw risk set.
# The sensitivity changes which previously excluded zero-event rows are
# eligible; it does not generate additional erosion/transition events.
# Source labels distinguish pre-existing floodplain from SF where supplied.
  d$evt<-d$FP_REACTIVATE_EVT_PRIMARY
  d$orig_eligible<-d$FP_REACTIVATE_RISK_SET_PRIMARY==1L & d$FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY==1L
  d$sens_eligible<-d$FP_REACTIVATE_RISK_SET_SENS==1L & d$FP_REACTIVATE_MODEL_ELIGIBLE_SENS==1L
  d$source<-as.character(d$FP_REACTIVATE_SOURCE_PRIMARY)

# [FRAF P2 / DIAG-86: CALENDAR YEAR VERSUS ELAPSED TIME]
# Use y1/y2 calendar date strings to identify 1986-linked intervals.
# The elapsed tstart_yr/tstop_yr variables must not be treated as years AD.
# The exclusion removes BOTH 1985->1986 and 1986->1988 intervals symmetrically
# from original and expanded scenarios; it is not a repaired 1986 channel map.
  # Date labels identify the suspect *calendar* intervals. Never use the
  # elapsed tstart_yr/tstop_yr as calendar years.  Both affected intervals
  # must be omitted symmetrically from ORIGINAL and ZERO_RECOVERY training,
  # historic fits, and any test sets for the conservative Mamore check.
  full_1986 <- (reach=="Mamoré" && isTRUE(RunMamore1986Exclusion))
  if (reach != "Mamoré" && isTRUE(RunMamore1986Exclusion))
    message("1986 exclusion requested for Jamuna; ignored (Mamoré-only check).")
  d$year1 <- substr(as.character(d$y1),1L,4L)
  d$year2 <- substr(as.character(d$y2),1L,4L)
  d$is_1986_interval <- d$year1=="1986" | d$year2=="1986"
  if (anyNA(d$is_1986_interval)) stop("Calendar-year tags y1/y2 are missing; cannot validate 1986 exclusions.")
# [FRAF P2 / DIAG-86: EXACT MAMORE INTERVAL GUARD]
# The expected 1986-linked pair is hard-coded for this river chronology:
# 19850101->19860101 and 19860101->19880101.
# A different set blocks execution rather than changing the exclusion silently.
  if (reach=="Mamoré") {
    identified <- unique(paste(as.character(d$y1[d$is_1986_interval]),
                               as.character(d$y2[d$is_1986_interval]),sep="->"))
    expected <- c("19850101->19860101", "19860101->19880101")
    if (!setequal(identified,expected))
      stop("Unexpected 1986-linked calendar intervals; STOP to avoid erroneous exclusion. Found: ",
           paste(identified,collapse="; "))
  } else if (any(d$is_1986_interval)) {
    stop("Unexpected Jamuna 1986-labelled interval in validation table.")
  }
# [FRAF P2 / DIAG-86: ELIGIBILITY/EVENT INVARIANTS]
# Require identical primary and sensitivity event flags and risk sets;
# expanded eligibility may add only recovered-zero candidates, not events.
# Check durations, baseline population totals, origin-frame coverage and
# that every retained event has valid spatial distance.
  if (any(d$FP_REACTIVATE_EVT_PRIMARY!=d$FP_REACTIVATE_EVT_SENS,na.rm=TRUE)) stop("Event fields disagree.")
  if (any(d$FP_REACTIVATE_RISK_SET_PRIMARY!=d$FP_REACTIVATE_RISK_SET_SENS,na.rm=TRUE)) stop("Risk-set fields disagree.")
  if (any(d$orig_eligible & !d$sens_eligible,na.rm=TRUE)) stop("Sensitivity removes originally eligible rows.")
  if (any(d$evt==1L & !d$orig_eligible,na.rm=TRUE)) stop("Some events were not original-eligible.")
  if (any(d$evt==1L & !d$sens_eligible,na.rm=TRUE)) stop("Sensitivity excludes events.")
  if (any(!is.finite(d$duration)|d$duration<=0)) stop("Non-positive/invalid elapsed-time risk intervals.")
  if (sum(d$orig_eligible)!=scalar_num(sum_o$n_eligible[1L])) stop("Original population count mismatch after read.")
  if (sum(d$orig_eligible & d$evt==1L)!=scalar_num(sum_o$n_events[1L])) stop("Original event count mismatch after read.")
  if (length(setdiff(unique(round(d$tstart_yr,9L)),round(ori$tstart_yr,9L)))>0L)
    stop("Broad risk contains interval starts absent from authoritative original origin table.")
  if (anyNA(d$orig_eligible) || anyNA(d$sens_eligible) || anyNA(d$evt))
    stop("Risk, event or eligibility fields contain missing values; model population cannot be validated.")
  if (sum(d$sens_eligible & !d$orig_eligible)!=sum(d$FP_SENS_RECOVER_ZERO==1L))
    stop("Recovered eligibility does not match FP_SENS_RECOVER_ZERO total.")

# [FRAF P2 / DIAG-86: EXPOSURE POPULATION INVENTORY]
# For each population, report rows, distinct PLACEs, event counts,
# place-years and nonmissing distance. These are PLACE-interval observations,
# not independent observations or measured eroded area.
  summarize <- function(sel,label) {
    sub <- d[which(sel),,drop=FALSE]
    data.frame(population=label,rows=nrow(sub),distinct_places=length(unique(sub$PLACE_ID)),
      events=sum(sub$evt==1L),exposure_place_years=sum(sub$duration),
      complete_margin_rows=sum(is.finite(sub$log_margin)),
      complete_margin_events=sum(is.finite(sub$log_margin) & sub$evt==1L),
      rate_1000_place_years=if (nrow(sub)) 1000*sum(sub$evt==1L)/sum(sub$duration) else NA_real_)
  }
  base_sum <- rbind(summarize(d$orig_eligible,"original_eligible"),
                    summarize(d$sens_eligible,"zero_recovery_eligible"),
                    summarize(d$sens_eligible & !d$orig_eligible,"recovered_zero_only"))
  write_out(base_sum,"02_population_reconciliation.csv")
  if (any(base_sum$complete_margin_events[1:2]!=base_sum$events[1:2]))
    stop("Model would lose original or sensitivity EVENTS due to missing Active Domain distance; investigate geometry.")
# [FRAF P2 / DIAG-86: SOURCE-STRATIFIED ELIGIBILITY]
# Report upstream antecedent source categories separately; do not conflate
# recovered zero observations with a novel floodplain state.
  src_summary <- do.call(rbind,lapply(unique(d$source),function(s) {
    i<- d$source==s; i[is.na(i)]<-FALSE
    rbind(data.frame(source=s,summarize(d$orig_eligible & i,"original_eligible")),
          data.frame(source=s,summarize(d$sens_eligible & i,"zero_recovery_eligible")))
  }))
  write_out(src_summary,"03_source_population_comparison.csv")

# [FRAF P2 / DIAG-86: TRANSPARENT COVERAGE EXCLUSION INVENTORY]
# Write the exact calendar intervals and the event/exposure removed for all
# rows, original eligible, expanded eligible and recovered-zero only.
# This supports manuscript S3.3 but does not perform spatial clipping at the
# attested southern truncation line or independently verify 1986 map coverage.
  # Describe the *actual* dated intervals removed in the conservative test.
  # No event flags, state fields or input Risk Tables are changed.
  interval_1986 <- if(reach=="Mamoré") d[d$is_1986_interval,,drop=FALSE] else d[FALSE,,drop=FALSE]
  interval_labels <- if(nrow(interval_1986)) unique(paste(interval_1986$y1,interval_1986$y2,sep="->")) else character()
  ex_rows<-list()
  for(k in c("ALL_1986_LINKED","ORIGINAL_ELIGIBLE_1986_LINKED",
             "ZERO_RECOVERY_ELIGIBLE_1986_LINKED","RECOVERED_ZERO_1986_LINKED")) {
    take<-switch(k,
      ALL_1986_LINKED=d$is_1986_interval,
      ORIGINAL_ELIGIBLE_1986_LINKED=d$is_1986_interval & d$orig_eligible,
      ZERO_RECOVERY_ELIGIBLE_1986_LINKED=d$is_1986_interval & d$sens_eligible,
      RECOVERED_ZERO_1986_LINKED=d$is_1986_interval & d$sens_eligible & !d$orig_eligible)
    z<-d[which(take),,drop=FALSE]
    ex_rows[[length(ex_rows)+1L]]<-data.frame(
       reach=reach,population=k,calendar_intervals=paste(interval_labels,collapse=";"),
       rows=nrow(z),distinct_places=length(unique(z$PLACE_ID)),
       events=sum(z$evt==1L),exposure_place_years=sum(z$duration))
  }
  write_out(do.call(rbind,ex_rows),"05_1986_exclusion_inventory.csv")
  by_interval<-list()
  for (lab in interval_labels) {
    this_pair<-paste(d$y1,d$y2,sep="->")==lab
    for (typ in c("RAW","ORIGINAL_ELIGIBLE","ZERO_RECOVERY_ELIGIBLE","RECOVERED_ZERO")) {
      sel<-switch(typ,
        RAW=this_pair,
        ORIGINAL_ELIGIBLE=this_pair & d$orig_eligible,
        ZERO_RECOVERY_ELIGIBLE=this_pair & d$sens_eligible,
        RECOVERED_ZERO=this_pair & d$sens_eligible & !d$orig_eligible)
      z<-d[which(sel),,drop=FALSE]
      by_interval[[length(by_interval)+1L]]<-data.frame(
        reach=reach,calendar_interval=lab,population=typ,rows=nrow(z),
        events=sum(z$evt==1L),distinct_places=length(unique(z$PLACE_ID)),
        exposure_place_years=sum(z$duration))
    }
  }
  if (length(by_interval)) write_out(do.call(rbind,by_interval),"05_1986_exclusion_by_interval.csv")

# [FRAF P2 / DIAG-86: PAIRED SCENARIO DEFINITIONS]
# ORIGINAL and ZERO_RECOVERY use their respective eligibility flags.
# NO1986 versions remove the same two calendar intervals in BOTH populations.
# The full history remains available; sensitivity exclusion does not retroactively
# alter upstream histories, state definitions or event flags.
  # All model subsets are explicit.  NO1986 uses the SAME excluded intervals
  # for both original and expanded populations, including their event rows.
  scenarios <- c("ORIGINAL","ZERO_RECOVERY")
  if (full_1986) scenarios<-c(scenarios,"ORIGINAL_NO1986","ZERO_RECOVERY_NO1986")
  scenario_sel <- function(scenario) {
    base_sel<-if(grepl("^ORIGINAL",scenario)) d$orig_eligible else d$sens_eligible
    if (grepl("_NO1986$",scenario)) base_sel<-base_sel & !d$is_1986_interval
    base_sel
  }
  
# [FRAF P2 / DIAG-86: DISTANCE/EXPOSURE COMPOSITION]
# Summarise how recovered-zero versus original eligible rows are distributed
# with respect to the Active Domain margin. Quantiles are row-based, whereas
# one mean is exposure-weighted by place-years. Bands in metres are descriptive.
# These checks do NOT independently validate the source imagery inventory.
  # Distance summaries reveal whether recovered zeros occupy systematically
  # different positions relative to the ACTIVE margin.  Distances are in m;
  # quantiles are row-based and descriptive, not independent observations.
  if (isTRUE(RunDistanceDiagnostics)) {
    src_pre<-toupper(trimws(d$source))=="PREEXISTING_FLOODPLAIN"
    src_sf <-toupper(trimws(d$source))=="STABILISED_FLOODPLAIN"
    group_sel<-list(
      SF_ORIGINAL_ELIGIBLE=d$orig_eligible & src_sf,
      PRE_ORIGINAL_ELIGIBLE=d$orig_eligible & src_pre,
      PRE_ORIGINAL_EVENTS=d$orig_eligible & src_pre & d$evt==1L,
      PRE_ORIGINAL_NON_EVENTS=d$orig_eligible & src_pre & d$evt==0L,
      PRE_RECOVERED_ZERO=d$sens_eligible & !d$orig_eligible & src_pre,
      PRE_EXPANDED_ELIGIBLE=d$sens_eligible & src_pre,
      ALL_ORIGINAL_ELIGIBLE=d$orig_eligible,
      ALL_EXPANDED_ELIGIBLE=d$sens_eligible)
    if (full_1986) {
      group_sel$PRE_RECOVERED_ZERO_NO1986<-group_sel$PRE_RECOVERED_ZERO & !d$is_1986_interval
      group_sel$PRE_ORIGINAL_ELIGIBLE_NO1986<-group_sel$PRE_ORIGINAL_ELIGIBLE & !d$is_1986_interval
    }
    grp_summary<-list();bands_summary<-list()
    qnames<-c("q00","q10","q25","q50","q75","q90","q99","q100")
    qprobs<-c(0,0.1,0.25,0.5,0.75,0.9,0.99,1)
    bands<-c(250,500,1000,2000,5000,10000)
    for(nm in names(group_sel)) {
      sub<-d[which(group_sel[[nm]]),,drop=FALSE]
      dd<-sub$DIST_ACTIVE_CURR
      good<-is.finite(dd)&dd>=0
      q<-if(any(good)) as.numeric(stats::quantile(dd[good],qprobs,na.rm=TRUE,names=FALSE))
          else rep(NA_real_,length(qnames))
      w<-sub$duration[good]
      ws<-if(length(w)&&sum(w)>0) stats::weighted.mean(dd[good],w) else NA_real_
      summary_row<-data.frame(reach=reach,population=nm,rows=nrow(sub),
        events=sum(sub$evt==1L),distinct_places=length(unique(sub$PLACE_ID)),
        exposure_place_years=sum(sub$duration),nonmissing_nonnegative_distance=sum(good),
        invalid_or_missing_distance=sum(!good),
        mean_distance_m=if(any(good))mean(dd[good]) else NA_real_,
        exposure_weighted_mean_distance_m=ws,stringsAsFactors=FALSE)
      for(j in seq_along(qnames)) summary_row[[qnames[j]]] <- q[j]
      grp_summary[[length(grp_summary)+1L]]<-summary_row
      for(cut in bands) {
        nle<-sum(dd[good]<=cut)
        bands_summary[[length(bands_summary)+1L]]<-data.frame(
          reach=reach,population=nm,distance_le_m=cut,
          rows_nonmissing=sum(good),rows_le=nle,
          pct_le=if(sum(good))100*nle/sum(good) else NA_real_,
          exposure_years_le=sum(sub$duration[good][dd[good]<=cut]),
          events_le=sum(sub$evt[good][dd[good]<=cut]==1L))
      }
    }
    write_out(do.call(rbind,grp_summary),"06_distance_distributions_by_population.csv")
    write_out(do.call(rbind,bands_summary),"07_distance_band_composition.csv")
  }
# [FRAF P2 / DIAG-86: EXPLORATORY COVERAGE WARNING]
# InventoryVerified is a USER-SUPPLIED flag, not a computed map-footprint audit.
# If FALSE, the run explicitly labels recovered-zero non-events as provisional.
# If TRUE, the run assumes external dated-AD inventory/overlap checks were done;
# it does not itself independently perform or record those checks.
  if (!isTRUE(InventoryVerified)) {
    writeLines("EXPLORATORY ONLY: Mapping inventory and annual Active Domain overlap coverage have NOT been independently verified. Recovered zero-signal rows are provisional non-events.",
               file.path(out,"00_EXPLORATORY_UNVERIFIED.txt"))
  }

# [FRAF P2 / DIAG-86: FIXED SCALER FOR HISTORIC PAIRED FITS]
# A single centre and SD calculated on original eligible log-distance are reused
# across paired historical scenarios. This makes their standardised coefficients
# comparable on the same predictor scale but may differ from standardisation
# used in the integrated multi-transition production Cox frame.
  # In Historic mode, the source production Cox uses one logkm z predictor,
  # Surv(tstart_yr,tstop_yr,event) and robust PLACE_ID clustering, Efron ties.
  # A FIXED original-eligible scaler permits meaningful paired HR comparisons;
  # the original integrated production script standardised on a larger unified
  # Cox frame, so its printed standardized HR may differ numerically. The
  # underlying raw logkm shape and fitted relative-risk ordering are identical.
  base_x <- d$log_margin[d$orig_eligible & is.finite(d$log_margin)]
  global_center<-mean(base_x); global_scale<-stats::sd(base_x)
  if (!is.finite(global_scale)||global_scale<=0) stop("No variation in baseline-eligible log-distance predictor.")
  d$X_GLOBAL <- (d$log_margin-global_center)/global_scale
  write_out(data.frame(term="DIST_ACTIVE_CURR_LOGKM_Z",basis="original_eligible_only_fixed_for_paired_comparison",
             center=global_center,scale=global_scale),"04_fixed_historic_scaler.csv")

# [FRAF P2 / DIAG-86: SINGLE-PREDICTOR COX FITTER]
# Historic fits use counting-process elapsed study time with Efron ties and
# PLACE_ID-clustered variance. Rolling fits use interval gap time and a
# training-subset-specific scaler. Failure/warnings are recorded, not suppressed
# from audit. The unused formal args are retained for exact source fidelity.
  fit_model <- function(sel, timebasis, originlabel, scale_target=NULL) {
    subset <- d[which(sel & is.finite(d$log_margin)),
                c("PLACE_ID","tstart_yr","tstop_yr","duration","evt","log_margin","X_GLOBAL"),drop=FALSE]
    ne <- sum(subset$evt==1L)
    if (nrow(subset)<2L || ne < max(1L,as.integer(MinimumTrainingEvents)))
      return(list(model=NULL,rows=nrow(subset),events=ne,reason="insufficient_events",warnings="",scaler=NULL))
    if (timebasis=="rolling_gap") {
      centre <- mean(subset$log_margin)
      scale <- stats::sd(subset$log_margin)
      if (!is.finite(scale)||scale<=0)
        return(list(model=NULL,rows=nrow(subset),events=ne,reason="constant_predictor",warnings="",scaler=NULL))
      subset$X <- (subset$log_margin-centre)/scale
      subset$PRED_TSTART <- rep(0,nrow(subset))
      subset$PRED_TSTOP <- subset$duration
      f <- survival::Surv(PRED_TSTART,PRED_TSTOP,evt) ~ X + cluster(PLACE_ID)
    } else {
      centre <- global_center;scale<-global_scale
      subset$X <- subset$X_GLOBAL
      f <- survival::Surv(tstart_yr,tstop_yr,evt) ~ X + cluster(PLACE_ID)
    }
    warn <- character()
    model <- tryCatch(withCallingHandlers(
      survival::coxph(f,data=subset,ties="efron",x=TRUE,
                      y=TRUE,model=FALSE,control=survival::coxph.control(iter.max=50)),
      warning=function(w) {warn <<- c(warn,conditionMessage(w));invokeRestart("muffleWarning")}),
      error=function(e) {warn <<- c(warn,conditionMessage(e));NULL})
    if (is.null(model)||any(!is.finite(stats::coef(model))))
      return(list(model=NULL,rows=nrow(subset),events=ne,reason="failed_or_nonfinite_coef",
                  warnings=paste(unique(warn),collapse=" | "),scaler=c(centre=centre,scale=scale)))
    fit <- list(model=model,rows=nrow(subset),events=ne,reason="fitted",
                warnings=paste(unique(warn),collapse=" | "),scaler=c(centre=centre,scale=scale))
    fit
  }
# [FRAF P2 / DIAG-86: REPORT EFFECTS ON TWO SCALES]
# Report exp(beta) for the fitted standardised covariate and exp(beta / SD)
# per unit unstandardised log1p(km) distance. Also report robust uncertainty
# and within-training concordance. These are associations, not physical
# movement-rate coefficients or independent validation metrics.
  fit_row <- function(fit, scenario, analysis, originrank=NA_integer_) {
    if (is.null(fit$model)) return(data.frame(reach=reach,analysis=analysis,scenario=scenario,
      origin_rank=originrank,fit_status=fit$reason,rows=fit$rows,events=fit$events,
      term="DIST_ACTIVE_CURR_LOGKM_Z",coef=NA_real_,hr_per_z=NA_real_,
      raw_logkm_coef=NA_real_,hr_per_unit_logkm=NA_real_,
      se_robust=NA_real_,ci_lower=NA_real_,ci_upper=NA_real_,
      training_concordance=NA_real_,warning=fit$warnings))
    beta<-as.numeric(stats::coef(fit$model)[1L]);scale<-fit$scaler["scale"]
    V <- if (!is.null(fit$model$var)) sqrt(fit$model$var[1L,1L]) else NA_real_
    conc<-tryCatch(as.numeric(summary(fit$model)$concordance[1L]),error=function(e)NA_real_)
    data.frame(reach=reach,analysis=analysis,scenario=scenario,origin_rank=originrank,
      fit_status=fit$reason,rows=fit$rows,events=fit$events,
      term="DIST_ACTIVE_CURR_LOGKM_Z",coef=beta,hr_per_z=exp(beta),
      raw_logkm_coef=beta/scale,hr_per_unit_logkm=exp(beta/scale),
      se_robust=V,ci_lower=exp(beta-1.96*V),ci_upper=exp(beta+1.96*V),
      training_concordance=conc,warning=fit$warnings)
  }

  fit_results<-list()
# [FRAF P2 / DIAG-86: FULL HISTORICAL SENSITIVITY]
# Fit ORIGINAL and ZERO_RECOVERY over all intervals and optionally paired
# NO1986 versions. Optional Schoenfeld diagnostics are kept separate from
# validation; historical PH failure restricts constant-hazard-ratio inference.
  if (isTRUE(RunHistoric)) {
    for (scenario in scenarios) {
      sel <- scenario_sel(scenario)
      message("[Historic] ",reach," ",scenario," risk rows=",sum(sel)," events=",sum(d$evt[sel]==1L))
      fit <- fit_model(sel,"historic", "HISTORIC")
      fit_results[[length(fit_results)+1L]] <- fit_row(fit,scenario,"historic_total_elapsed")
      if (isTRUE(RunPHDiagnostics) && !is.null(fit$model)) {
        ph <- tryCatch(survival::cox.zph(fit$model),error=function(e) e)
        capture.output(ph,file=file.path(out,paste0("10_PH_",scenario,".txt")))
        if (!inherits(ph,"error")) {
          ph_tab <- as.data.frame(ph$table)
          ph_tab$term<-rownames(ph_tab)
          write_out(ph_tab,paste0("10_PH_",scenario,".csv"))
        }
      }
      if (!is.null(fit$model)) {
        capture.output(summary(fit$model),file=file.path(out,paste0("10_cox_summary_",scenario,".txt")))
        bh<-tryCatch(survival::basehaz(fit$model,centered=FALSE),error=function(e) {
          warning("Historic baseline extraction failed: ",conditionMessage(e));NULL
        })
        if (!is.null(bh)) {
          write_out(data.frame(reach=reach,scenario=scenario,time_elapsed_years=bh$time,
                 baseline_cumulative_hazard=bh$hazard),paste0("10_historic_baseline_",scenario,".csv"))
        }
      }
      rm(fit);invisible(gc(FALSE))
    }
    historic_table<-do.call(rbind,fit_results)
    write_out(historic_table,"10_historic_cox_comparison.csv")
    if (full_1986) {
      # Compare on the *same fixed ORIGINAL-eligible scaler*.  The no-1986
      # contrast tests whether the eligibility sensitivity survives removing
      # both intervals, not whether the historically observed river changed.
      a<-historic_table
      pick<-function(tag,key) {
        rr<-a[a$scenario==tag,,drop=FALSE]
        if(!nrow(rr)) return(NA_real_)
        as.numeric(rr[[key]][1L])
      }
      contrast<-data.frame(
        comparison=c("ALL_INTERVALS","EXCLUDE_1986_LINKED"),
        original_coef=c(pick("ORIGINAL","coef"),pick("ORIGINAL_NO1986","coef")),
        expanded_coef=c(pick("ZERO_RECOVERY","coef"),pick("ZERO_RECOVERY_NO1986","coef")),
        original_raw_logkm_coef=c(pick("ORIGINAL","raw_logkm_coef"),pick("ORIGINAL_NO1986","raw_logkm_coef")),
        expanded_raw_logkm_coef=c(pick("ZERO_RECOVERY","raw_logkm_coef"),pick("ZERO_RECOVERY_NO1986","raw_logkm_coef")))
      contrast$expanded_minus_original<-contrast$expanded_coef-contrast$original_coef
      contrast$relative_change_abs_beta_percent<-100*(abs(contrast$expanded_coef)/abs(contrast$original_coef)-1)
      write_out(contrast,"11_1986_historic_paired_effect.csv")
    }
  }

# [FRAF P2 / DIAG-86: CONDITIONAL RANKING AND CALIBRATION]
# AUC is rank concordance against binary held-out labels; average precision
# uses precision at observed event ranks. Brier and logistic calibration are
# computed on available predictions. All depend on the chosen risk population.
  metric_auc <- function(y,score) {
    ok<-y%in%c(0L,1L)&is.finite(score);y<-y[ok];score<-score[ok]
    n1<-sum(y==1L);n0<-sum(y==0L)
    if (!n1||!n0) return(NA_real_)
    ranks<-rank(score,ties.method="average")
    (sum(ranks[y==1L])-n1*(n1+1)/2)/(n1*n0)
  }
  metric_ap <- function(y,score) {
    ok<-y%in%c(0L,1L)&is.finite(score);y<-y[ok];score<-score[ok]
    if (!length(y)||sum(y==1L)==0L) return(NA_real_)
    idx<-order(score,decreasing=TRUE);y<-y[idx]
    sum((cumsum(y)/seq_along(y))[y==1L])/sum(y==1L)
  }
  metric_calibration <- function(y,p) {
    if (length(y)<10L||length(unique(y))<2L) return(c(intercept=NA_real_,slope=NA_real_))
    z<-qlogis(pmax(1e-8,pmin(1-1e-8,p)))
    m<-tryCatch(suppressWarnings(stats::glm(y~z,family=stats::binomial())),error=function(e)NULL)
    if (is.null(m)) return(c(intercept=NA_real_,slope=NA_real_))
    cf<-stats::coef(m);c(intercept=unname(cf[1]),slope=unname(cf[2]))
  }
# [FRAF P2 / DIAG-86: ROLLING GAP-TIME PROBABILITY]
# Evaluate the fitted baseline cumulative hazard at the next interval duration
# and combine with exp(linear predictor). Probabilities are conditional on
# retrospective endpoint-defined eligibility; not an independent prospective map.
  cumhaz_at <- function(bh,dt) {
    ii<-findInterval(dt,bh$time)
    ifelse(ii>0,bh$hazard[pmax(ii,1L)],0)
  }
  predict_test <- function(fit, idx) {
    n<-length(idx); pp<-rep(NA_real_,n);lp<-rep(NA_real_,n)
    if (is.null(fit$model)||n==0L) return(list(prob=pp,lp=lp))
    x<-(d$log_margin[idx]-fit$scaler["centre"])/fit$scaler["scale"]
    beta<-as.numeric(stats::coef(fit$model)[1L]);lp<-as.numeric(beta*x)
    bh<-tryCatch(survival::basehaz(fit$model,centered=FALSE),error=function(e)NULL)
    if (is.null(bh)) return(list(prob=pp,lp=lp))
    good<-is.finite(lp)&is.finite(d$duration[idx])
    if (any(good)) {
      h<-pmax(0,cumhaz_at(bh,d$duration[idx][good]))
      hazard<-exp(pmax(-700,pmin(700,lp[good])))
      pp[good]<-pmax(0,pmin(1,1-exp(-h*hazard)))
    }
    list(prob=pp,lp=lp)
  }
# [FRAF P2 / DIAG-86: MATCHED VERSUS EXPANDED EVALUATION]
# COMMON_ORIGINAL_ELIGIBLE is the fixed comparison set for paired models;
# EXPANDED_ELIGIBLE reflects the changed eligible population and event prevalence.
# Interpret differences within each evaluation definition, not across
# populations as if event prevalence and candidate area were identical.
  metric_row <- function(scenario,rank,subset_label,idx,prob,lp) {
    valid<-which(is.finite(prob) & is.finite(lp))
    y<-d$evt[idx]
    if (!length(valid)) return(data.frame(reach=reach,scenario=scenario,
      origin_rank=rank,eval_population=subset_label,rows=length(idx),predicted_rows=0L,
      observed_events=sum(y==1L),predicted_events=0L,
      AUC=NA_real_,average_precision=NA_real_,brier_score=NA_real_,
      calibration_intercept=NA_real_,calibration_slope=NA_real_))
    cal<-metric_calibration(y[valid],prob[valid])
    data.frame(reach=reach,scenario=scenario,origin_rank=rank,eval_population=subset_label,
      rows=length(idx),predicted_rows=length(valid),observed_events=sum(y==1L),
      predicted_events=sum(y[valid]==1L),AUC=metric_auc(y[valid],prob[valid]),
      average_precision=metric_ap(y[valid],prob[valid]),
      brier_score=mean((y[valid]-prob[valid])^2),
      calibration_intercept=cal["intercept"],calibration_slope=cal["slope"])
  }
# [FRAF P2 / DIAG-86: TOP-AREA EVENT-FLAG CAPTURE]
# Sort places by Cox linear predictor and accumulate nominal area, using
# ASM_BLOCK_AREA_M2 when available (otherwise unit weight). These are binary
# risk-table event capture counts, NOT mapped EA erosion footprints or
# spatial intersection / IoU verification.
  top_capture_rows <- function(scenario,rank,subset_label,idx,prob,lp) {
    good<-which(is.finite(lp));if (!length(good)) return(NULL)
    y<-d$evt[idx][good]; area<-d$area[idx][good]; score<-lp[good]
    # Top-area thresholds use L-P ranking, preserving monotonic rank under Cox.
    o<-order(score,decreasing=TRUE)
    area<-area[o];y<-y[o];cut<-cumsum(area)/sum(area)
    do.call(rbind,lapply(c(0.025,0.05,0.10,0.20,0.30),function(q) {
      taken<-which(cut<=q);if (!length(taken)) taken<-1L
      n_ev<-sum(y[taken]==1L)
      data.frame(reach=reach,scenario=scenario,origin_rank=rank,
        eval_population=subset_label,top_area_fraction=q,
        captured_events=n_ev,total_events=sum(y==1L),
        event_recall=if(sum(y==1L)) n_ev/sum(y==1L) else NA_real_,
        event_flag_precision=n_ev/length(taken),
        selected_area_fraction=sum(area[taken])/sum(area),n_selected_rows=length(taken))
    }))
  }
# [FRAF P2 / DIAG-86: EXPLORATORY ROLLING ORIGINS]
# Train on risk intervals ending no later than the chosen origin; test at the
# selected interval-start rank. Origin ranks come from the original full table.
# Default 10,20,30 values and these conditional metrics are distinct from the
# final matched origin, continuous-score T25/T30/T35 forecast verification.
  if (isTRUE(RunRolling)) {
    # Original v17.10.15.1 production uses zero-based origin interpretation code:
    # 0 = unique interval-start rank, 1 = elapsed study year.
    wanted <- unique(suppressWarnings(as.numeric(trimws(unlist(strsplit(as.character(ForecastOrigins),"[,; ]+"))))))
    wanted<-wanted[is.finite(wanted)];if (!length(wanted)) stop("No valid forecast origins.")
    mode_idx<-suppressWarnings(as.integer(OriginInterpretation[1L]))
    if ((is.finite(mode_idx) && mode_idx==0L) ||
        grepl("^unique",tolower(as.character(OriginInterpretation[1L])))) {
      selected <- ori[ori$origin_rank %in% as.integer(wanted),,drop=FALSE]
    } else {
      selected<-do.call(rbind,lapply(wanted,function(w) {
        ii<-which.min(abs(ori$tstart_yr-(min(ori$tstart_yr)+w)))
        ori[ii,,drop=FALSE]
      }))
      selected<-selected[!duplicated(selected$origin_rank),,drop=FALSE]
    }
    if (!nrow(selected)) stop("No requested forecast origins available (see 01_available_origin_ranks.csv).")
    write_out(selected,"20_selected_forecast_origins.csv")
    metric_rows<-list();capture_rows<-list();train_rows<-list()
    predcon<-NULL
# [FRAF P2 / DIAG-86: OPTIONAL BULK ROW EXPORT]
# Compression is used only when the optional row-level sensitivity output
# is requested. The default avoids large prediction-row exports.
    if (isTRUE(WritePredictionRows)) {
      predcon<-gzfile(file.path(out,"20_rolling_prediction_rows.csv.gz"),open="wt")
    }
    pred_header<-FALSE
    for (r in seq_len(nrow(selected))) {
      rank <- selected$origin_rank[r];start <- selected$tstart_yr[r]
# [FRAF P2 / DIAG-86: TEMPORAL SPLIT, NOT SPATIAL BLOCK VALIDATION]
# Historical risk intervals must end before or at the origin to enter training.
# The test uses the matching interval-start; there is no independent-river or
# spatial-block held-out evaluation in this diagnostic.
      train_time <- d$tstop_yr<=start+1e-10
      test_time <- abs(d$tstart_yr-start)<=1e-10
      message("[Rolling] T",rank," training intervals=",sum(train_time)," holdout intervals=",sum(test_time))
      for (scenario in scenarios) {
        omit_1986_in_eval <- grepl("_NO1986$",scenario)
        eval_ok <- if (omit_1986_in_eval) !d$is_1986_interval else rep(TRUE,nrow(d))
        orig_target <- which(test_time & d$orig_eligible & eval_ok)
        recovered_target <- which(test_time & d$sens_eligible & eval_ok)
        if (!length(recovered_target)) {
          warning("No broad-risk test intervals at T",rank," for scenario ",scenario)
          next
        }
        train_eligible <- scenario_sel(scenario)
        fit<-fit_model(train_time & train_eligible,"rolling_gap",paste0("T",rank))
        train_rows[[length(train_rows)+1L]]<-fit_row(fit,scenario,"rolling_gap_time",rank)
        p_orig<-predict_test(fit,orig_target)
        p_own <-predict_test(fit,recovered_target)
# [FRAF P2 / DIAG-86: IMPORTANT MODEL SCOPE LIMIT]
# The common original-eligible set is constructed once per holdout interval,
# while expanded eligibility is separate. Eligibility relies on retrospectively
# observed T2 state; it is not a T1-only prospective scoring population.
        # Identical ORIGINAL eligibility test set for BOTH fitted models is essential
        # for apples-to-apples CONDITIONAL discrimination/calibration/Brier comparisons.
        # The eligible test subset still depends on T2 outcome provenance: these
        # are NOT unconditional prospective forecasting metrics.
        metric_rows[[length(metric_rows)+1L]]<-metric_row(scenario,rank,"COMMON_ORIGINAL_ELIGIBLE",
                                                           orig_target,p_orig$prob,p_orig$lp)
        metric_rows[[length(metric_rows)+1L]]<-metric_row(scenario,rank,"EXPANDED_ELIGIBLE",
                                                           recovered_target,p_own$prob,p_own$lp)
        capture_rows[[length(capture_rows)+1L]]<-top_capture_rows(scenario,rank,
                                          "COMMON_ORIGINAL_ELIGIBLE",orig_target,p_orig$prob,p_orig$lp)
        capture_rows[[length(capture_rows)+1L]]<-top_capture_rows(scenario,rank,
                                          "EXPANDED_ELIGIBLE",recovered_target,p_own$prob,p_own$lp)
        if (!is.null(predcon)) {
          rec<-data.frame(reach=reach,scenario=scenario,origin_rank=rank,
            PLACE_ID=d$PLACE_ID[recovered_target],tstart_yr=d$tstart_yr[recovered_target],
            tstop_yr=d$tstop_yr[recovered_target],source=d$source[recovered_target],
            originally_eligible=as.integer(d$orig_eligible[recovered_target]),
            sensitivity_eligible=as.integer(d$sens_eligible[recovered_target]),
            observed_event=d$evt[recovered_target],
            predicted_probability=p_own$prob,linear_predictor=p_own$lp)
          utils::write.table(rec,predcon,sep=",",row.names=FALSE,na="",col.names=!pred_header,
                             append=pred_header,qmethod="double")
          pred_header<-TRUE
        }
        rm(fit,p_orig,p_own);invisible(gc(FALSE))
      }
    }
    if (!is.null(predcon)) close(predcon)
    if (!length(train_rows) || !length(metric_rows)) stop("No rolling models evaluated; check origin dates and risk table.")
    rolling_fit_table<-do.call(rbind,train_rows)
    rolling_metric_table<-do.call(rbind,metric_rows)
    write_out(rolling_fit_table,"20_rolling_training_model_comparison.csv")
    write_out(rolling_metric_table,"21_rolling_conditional_validation_original_vs_expanded.csv")
    if (full_1986) {
# [FRAF P2 / DIAG-86: PAIRED ROLLING NO1986 EFFECT]
# Track standardised-independent raw logkm effects and training event counts
# across original/recovered-zero populations, with and without 1986-linked
# calendar intervals; differences remain record-conditional sensitivities.
      cm<-rolling_fit_table
      outc<-list()
      for (rr in unique(cm$origin_rank)) {
        x<-cm[cm$origin_rank==rr,,drop=FALSE]
        getval<-function(tag,key) {
          a<-x[x$scenario==tag,,drop=FALSE]
          if(!nrow(a)) return(NA_real_)
          as.numeric(a[[key]][1L])
        }
        for(scope in c("ALL_INTERVALS","EXCLUDE_1986_LINKED")) {
          tag_o<-if(scope=="ALL_INTERVALS") "ORIGINAL" else "ORIGINAL_NO1986"
          tag_s<-if(scope=="ALL_INTERVALS") "ZERO_RECOVERY" else "ZERO_RECOVERY_NO1986"
          oo<-getval(tag_o,"raw_logkm_coef")
          ss<-getval(tag_s,"raw_logkm_coef")
          outc[[length(outc)+1L]]<-data.frame(reach=reach,origin_rank=rr,
            comparison=scope,original_raw_logkm_coef=oo,expanded_raw_logkm_coef=ss,
            expanded_minus_original=ss-oo,
            relative_change_abs_beta_percent=if(is.finite(oo) && oo!=0)100*(abs(ss)/abs(oo)-1) else NA_real_,
            original_training_events=getval(tag_o,"events"),
            expanded_training_events=getval(tag_s,"events"))
        }
      }
      write_out(do.call(rbind,outc),"23_1986_rolling_paired_effects.csv")
    }
    capture_rows<-Filter(Negate(is.null),capture_rows)
    if (length(capture_rows)) write_out(do.call(rbind,capture_rows),"22_rolling_top_area_event_flag_capture.csv")
  }

  writeLines(c(
    paste("FRAF v1.1 finished:",Sys.time()),paste("Reach:",reach),
    paste("Original:",orig_path,"/",orig_layer),paste("Sensitivity:",sens_path,"/",sens_layer),
    paste("Original eligible:",sum(d$orig_eligible)),
    paste("Sensitivity eligible:",sum(d$sens_eligible)),
    paste("Events unchanged:",sum(d$evt[d$orig_eligible]==1L)),
    paste("Recovered zero candidates:",sum(d$sens_eligible & !d$orig_eligible)),
    paste("Mamoré 1986-linked two-interval exclusion enabled:",full_1986),
    paste("Excluded 1986 linked rows from raw population:",if(full_1986)sum(d$is_1986_interval) else 0),
    paste("Distance distribution diagnostics enabled:",isTRUE(RunDistanceDiagnostics)),
    paste("Annual AD input inventory verified:",isTRUE(InventoryVerified)),
    "Original and sensitivity FP event labels and three-state ontology are unchanged.",
    "No full-historical-union field or future T2 predictor is fitted.",
    "Historic: total-time Cox spatial-only log1p(distance/1000), cluster(PLACE_ID), Efron ties.",
    "Rolling: interval-gap-time Cox, train-only scaling, original full-record interval-origin ranking.",
    "COMMON_ORIGINAL_ELIGIBLE is a conditional paired evaluation; both this and expanded eligibility use retrospective T2 classification.",
    "This is NOT a fully prospective T1-defined forecast verification. Treat rolling metrics as exploratory conditional results.",
    "Event flags/top-area capture are not mapped actual footprint verification.",
    "NO1986 comparisons omit both 1985-1986 and 1986-1988 observations symmetrically from training and evaluation.",
    "These exclusions do not retroactively reconstruct T1 histories or repair 1986 mapping.",
    "If inventory coverage is unverified, estimates are EXPLORATORY."
  ),file.path(out,"00_RUN_COMPLETED.txt"),useBytes=TRUE)
# [FRAF P2 / DIAG-86: TERMINAL STATUS AND LIMITATIONS]
# RUN_COMPLETED records the source paths, counts, flags and cautions.
# A completed diagnostic does not establish that recovered-zero geometry was
# independently verified or that its rolling metrics reproduce final forecasts.
# The original output vocabulary is kept unchanged for numerical provenance.
  message("[SUCCESS] Paired broad FP->AD sensitivity results: ",out)
},error=function(e) {
  writeLines(c("FAILED",as.character(Sys.time()),conditionMessage(e)),
             file.path(out,"00_RUN_FAILED.txt"),useBytes=TRUE)
  stop(e)
})
