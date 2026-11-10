##FRAF Step3E Jamuna DSAD Piecewise Distance Final v1.0=group
##FRAF_Step3E_Jamuna_DSAD_Piecewise_Distance_Final_v1_1_2_ORDER_FIX=name
##Input_table=file
##ID_field=string AUTO
##Start_field=string AUTO
##Stop_field=string AUTO
##Event_field=string STORAGE_REWORK_EVT
##Risk_set_field=string STORAGE_REWORK_RISK_SET
##Distance_field=string DIST_ACTIVE_CURR
##Knot1_event_quantile=number 0.75
##Knot2_event_quantile=number 0.90
##Cluster_by_ID=boolean TRUE
##Run_PH_test=boolean TRUE
##Response_plot_max_m=number 2000
##Response_plot_step_m=number 10
##Output_Directory=folder

# =============================================================================
# FRAF — Step 3E
# Jamuna DS->AD final reduced-history distance-form comparison
# Version 1.1.2
#
# Purpose
# -------
# Final, deliberately narrow Cox sensitivity after J3B/J3C/J3D:
#   M0  linear DIST_ACTIVE_CURR
#   M1  one-knot piecewise linear DIST_ACTIVE_CURR
#   M2  two-knot piecewise linear DIST_ACTIVE_CURR
#
# All models:
#   * use the SAME complete-case population;
#   * use STORAGE_REWORK_EVT / STORAGE_REWORK_RISK_SET by default;
#   * retain the J3D DS->AD history terms EXCEPT ASM_N_EPISODES_PREV;
#   * standardise continuous history terms on the common population;
#   * use the raw distance in km for interpretable piecewise slopes;
#   * optionally cluster robust variance by PLACE/BLOCK ID;
#   * export AIC, LR tests, concordance, coefficients, cox.zph diagnostics,
#     event-distance quantiles and relative-hazard response curves.
#
# IMPORTANT
# ---------
# Knot positions are derived ONCE from the observed DS->AD EVENT-distance
# distribution on the final common analysis population. The defaults are
# the 75th and 90th event-distance quantiles. They are descriptive quantiles,
# not AIC-optimised breakpoints, so this script does NOT search for optimal
# knots. The resolved metre values are written to the output metadata.
#
# Selected J3D reduced-history specification:
#   ASM_DOM_RATIO_PREV
#   ASM_MAX_QUIET_PREV
#   ASM_COV_FRAC
#   ASM_STORAGE_FRAC_PREV
#   ASM_QUIET_SINCE_PREV
#   ASM_N_STORAGE_EVT_PREV
#
# ASM_N_EPISODES_PREV is deliberately omitted.
# =============================================================================

# PUBLICATION ARCHIVE / DIAG-J — EXECUTABLE-FIDELITY ANNOTATION
# Source: FRAF_Step3E_Jamuna_DSAD_Piecewise_Distance_Final_v1_1_2_ORDER_FIX.rsx
# Archive alias: FRAF_P2_DIAG_JamunaDSADPiecewiseDistance_v1_1_2.rsx
# Former workflow designation: Step3E v1.1.2 (ORDER_FIX).
# Scope: Jamuna Depositional Storage -> Active Domain (DS->AD) distance-form
# diagnostic; supports Paper 2 Supplementary S6, Table S13.
# This file adds comments only. The source's QGIS Processing header,
# calculations, model terms, output filenames, internal version identifiers,
# and ordering remain unchanged. Do not infer a successful run or an exact
# numerical reproduction of Table S13 from source inspection alone.
# QGIS group label still refers to v1.0 while the Processing name and
# run metadata identify v1.1.2; this is inherited source metadata.
# ----------------------------------------------------------------------------
# SOFTWARE DEPENDENCE
# The main model depends on R survival::coxph and survival::cox.zph;
# spatial input also depends on sf, only when a spatial file is supplied.
# This is an R/QGIS Processing .rsx script, not a standalone Python module.
suppressPackageStartupMessages(library(survival))

# EXECUTION CONTRACT / FILE OUTPUTS
# Output_Directory is created if absent. Existing files of matching names
# can be overwritten. Separate river/run directories are recommended.
# write_out() exports flat tables without row names; the entire analysis
# is specified by the selected Risk Table, QGIS parameters and R environment.
dir.create(Output_Directory, recursive=TRUE, showWarnings=FALSE)
msg <- function(...) cat(paste0(...,"\n"))
write_out <- function(x,nm) write.csv(x,file.path(Output_Directory,nm),row.names=FALSE,na="")

# INPUT COERCION — numeric conversion is tolerant of factor/character data.
# Conversion failures become NA and are handled by subsequent filters.
safe_num <- function(x) suppressWarnings(as.numeric(as.character(x)))
# EVENT / RISK INDICATORS
# Numeric non-zero values, common boolean strings and event/risk labels
# become TRUE. Missing or unrecognised values become FALSE, rather than
# generating events. Check source coding before comparing event counts.
as_flag <- function(x) {
  z <- safe_num(x)
  out <- rep(FALSE,length(x))
  ok <- is.finite(z)
  out[ok] <- z[ok] != 0
  if(any(!ok)) {
    s <- tolower(trimws(as.character(x[!ok])))
    out[!ok] <- s %in% c("1","true","t","yes","y","event","at_risk","atrisk")
  }
  out[is.na(out)] <- FALSE
  out
}
# FIELD RESOLUTION
# Explicit fields are case-insensitive; AUTO searches specified aliases.
# Failure is explicit when a required field cannot be identified.
pick <- function(nms,requested,cands,label) {
  if(!is.null(requested) && length(requested) && !is.na(requested) &&
     trimws(requested)!="" && toupper(trimws(requested))!="AUTO") {
    h <- nms[toupper(nms)==toupper(trimws(requested))]
    if(length(h)) return(h[1])
    stop(label," field not found: ",requested)
  }
  for(z in cands) {
    h <- nms[toupper(nms)==toupper(z)]
    if(length(h)) return(h[1])
  }
  stop("AUTO could not resolve ",label," field.")
}
# STANDARDISATION DETAIL (SOURCE-IMPLEMENTATION QUALIFICATION)
# std() uses mean and SD of the supplied full numeric column, before the
# eventual risk/complete-case filter below. Although the three Cox models
# share one final complete-case population, this code does NOT recompute
# z-scores on that filtered population. Already *_Z fields are used as-is.
std <- function(z) {
  z <- safe_num(z); mu <- mean(z,na.rm=TRUE); ss <- sd(z,na.rm=TRUE)
  if(!is.finite(ss) || ss<=0) return(rep(NA_real_,length(z)))
  (z-mu)/ss
}

# Progress messages retain the original Step 3E version wording for audit.
msg("[Step 3E v1.1.2] Jamuna DS->AD final piecewise-distance comparison started.")

# INPUT FILE SUPPORT
# CSV and TXT are read as comma-separated tables; RDS can be read directly.
# For GeoPackage, shapefile, GeoJSON or SQLite, geometry is dropped: this
# analysis is at the place-interval record level, not polygon intersecting.
# Verify that the selected input belongs to the Jamuna analysis: no
# automatic river-identification or source-file hash check is performed.
read_input <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("csv","txt"))
    return(utils::read.csv(path, check.names=FALSE))
  if (ext=="rds") return(readRDS(path))
  if (ext %in% c("gpkg","shp","geojson","sqlite")) {
    if (!requireNamespace("sf", quietly=TRUE))
      stop("Package 'sf' is required to read spatial input.")
    return(sf::st_drop_geometry(sf::st_read(path, quiet=TRUE)))
  }
  stop("Unsupported input type: .", ext)
}

# Load exactly one historical analysis table. All subsequent model variants
# use records drawn from this table and no outside time or spatial data.
d <- read_input(Input_table)
nms <- names(d)

# FIELD MAPPING: place identity, start/stop counting-process time,
# DS->AD event, DS at-risk status, and interval-start AD-margin distance.
# Default Distance_field=DIST_ACTIVE_CURR, interpreted as METRES.
# The code does not infer physical units from input metadata.
id_f <- pick(nms,ID_field,c("PLACE_ID","BLOCK_ID","CELL_ID","ID"),"ID")
start_f <- pick(nms,Start_field,c("tstart_yr","TSTART","START","INTERVAL_START","y1"),"start")
stop_f <- pick(nms,Stop_field,c("tstop_yr","TSTOP","STOP","INTERVAL_END","y2"),"stop")
event_f <- pick(nms,Event_field,c("STORAGE_REWORK_EVT","STORAGE_REWORK_EVT_PRIMARY"),"event")
risk_f <- pick(nms,Risk_set_field,c("STORAGE_REWORK_RISK_SET","STORAGE_REWORK_RISK_SET_PRIMARY"),"risk set")
dist_f <- pick(nms,Distance_field,c("DIST_ACTIVE_CURR"),"distance")

# PARAMETER CHECKS
# A strictly increasing pair of event-distance quantile probabilities
# is required, along with positive response-plot length and step size.
# Defaults: first knot q75, second knot q90, plotting to 2,000 m at 10 m.
if(Knot1_event_quantile <= 0 || Knot1_event_quantile >= 1 ||
   Knot2_event_quantile <= 0 || Knot2_event_quantile >= 1 ||
   Knot2_event_quantile <= Knot1_event_quantile)
  stop("Require 0 < Knot1_event_quantile < Knot2_event_quantile < 1.")
if(Response_plot_step_m <= 0 || Response_plot_max_m <= 0)
  stop("Response plot limits must be positive.")

# J3D-selected DS->AD history specification, with N_EPISODES deliberately absent.
# COVARIATE SPECIFICATION (J3D REDUCED-HISTORY LINEAGE)
# Retains six history terms from the preceding DS->AD investigation.
# ASM_N_EPISODES_PREV is deliberately excluded; no automatic search,
# re-estimation of predictors, or held-out feature selection occurs here.
# All candidate distance shapes have IDENTICAL history terms.
history_raw <- c(
  "ASM_DOM_RATIO_PREV",
  "ASM_MAX_QUIET_PREV",
  "ASM_COV_FRAC",
  "ASM_STORAGE_FRAC_PREV",
  "ASM_QUIET_SINCE_PREV",
  "ASM_N_STORAGE_EVT_PREV"
)
# Accept already-standardised fields if raw versions are unavailable.
# Allow source fields either unstandardised or already ending in *_Z.
# The chosen form is recorded for each term in the field-resolution audit.
resolve_history <- function(base) {
  h <- nms[toupper(nms)==toupper(base)]
  if(length(h)) return(c(field=h[1],already_z="FALSE"))
  hz <- nms[toupper(nms)==toupper(paste0(base,"_Z"))]
  if(length(hz)) return(c(field=hz[1],already_z="TRUE"))
  c(field=NA_character_,already_z=NA_character_)
}
# FIELD AUDIT — required predictors must all be resolvable; failure of
# any field stops execution, rather than silently reducing the formula.
hr <- lapply(history_raw,resolve_history)
hist_audit <- data.frame(
  requested=history_raw,
  resolved=vapply(hr,function(x)x["field"],character(1)),
  already_standardised=vapply(hr,function(x)x["already_z"],character(1)),
  stringsAsFactors=FALSE
)
write_out(hist_audit,"01_field_resolution.csv")
if(any(is.na(hist_audit$resolved)))
  stop("Required reduced-history field(s) absent: ",
       paste(hist_audit$requested[is.na(hist_audit$resolved)],collapse=", "))

# CANONICAL WORKING TABLE
# Converts source field names to id / tstart / tstop / event / risk /
# distance_m, and retains a numeric copy of each history predictor.
# Counting-process time coordinates are not altered or interpolated.
x <- data.frame(
  id=as.character(d[[id_f]]),
  tstart=safe_num(d[[start_f]]),
  tstop=safe_num(d[[stop_f]]),
  event=as.integer(as_flag(d[[event_f]])),
  risk=as.integer(as_flag(d[[risk_f]])),
  distance_m=safe_num(d[[dist_f]]),
  stringsAsFactors=FALSE
)

# Apply supplied *_Z values as recorded; otherwise standardise raw
# fields using the imported column. This happens BEFORE filtering.
for(i in seq_len(nrow(hist_audit))) {
  src <- hist_audit$resolved[i]
  nm <- paste0(history_raw[i],"_Z")
  v <- safe_num(d[[src]])
  if(toupper(src)==toupper(nm)) x[[nm]] <- v else x[[nm]] <- std(v)
}

# MATCHED ANALYTICAL POPULATION
# Restrict to DS->AD risk=1, valid positive-length time intervals,
# finite non-negative distance, nonmissing ID and six complete history
# fields. The same x is passed to M0, M1 and M2; an event must be coded
# within the eligible DS risk set to contribute to their event counts.
# This is not a broad FP->AD risk analysis: DS remains its own risk state.
hist_z <- paste0(history_raw,"_Z")
# Risk set + valid counting-process interval + common complete cases.
keep <- x$risk==1 & is.finite(x$tstart) & is.finite(x$tstop) &
        x$tstop>x$tstart & is.finite(x$distance_m) & x$distance_m>=0
keep <- keep & complete.cases(x[,hist_z,drop=FALSE]) & !is.na(x$id) & x$id!=""
x <- x[keep,,drop=FALSE]

if(nrow(x)==0 || sum(x$event)<5) stop("No usable DS->AD analysis population.")

# Event-distance quantiles.
# KNOT CONSTRUCTION / DATA DEPENDENCE
# Derive candidate breakpoints from distances of OBSERVED DS->AD events
# in the final common population. The locations are outcome-informed
# descriptive quantiles and NOT fixed a priori geographic distances.
# No model-fit/AIC optimisation over a grid of possible knots is done.
# The quantile values must be regenerated for a different Risk Table.
evd <- x$distance_m[x$event==1 & is.finite(x$distance_m)]
# Export reference event-distance quantiles in metres using R quantile
# type=7; the selected q75/q90 quantiles also appear in this output.
qs <- sort(unique(c(0,.1,.25,.5,.75,.9,.95,.99,1,
                    Knot1_event_quantile,Knot2_event_quantile)))
qvals <- as.numeric(quantile(evd,qs,na.rm=TRUE,names=FALSE,type=7))
write_out(data.frame(quantile=qs,distance_m=qvals),
          "02_event_distance_quantiles.csv")

# Final piecewise knots: fixed descriptive quantiles of the observed event
# distance distribution, not selected by model fit.
# Both knots are calculated ONCE, before any of the candidate models
# are fitted; they are common to M1 and M2 and ordered by construction.
# A zero-width segment causes a hard stop rather than an invalid fit.
Knot1_m <- as.numeric(quantile(evd,Knot1_event_quantile,na.rm=TRUE,names=FALSE,type=7))
Knot2_m <- as.numeric(quantile(evd,Knot2_event_quantile,na.rm=TRUE,names=FALSE,type=7))
if(!is.finite(Knot1_m) || !is.finite(Knot2_m) || Knot2_m <= Knot1_m)
  stop("Derived event-distance knots are invalid/non-distinct: ",
       Knot1_m,", ",Knot2_m," m.")
msg("[Step 3E v1.1.2] Derived piecewise knots from event distances: q",
    Knot1_event_quantile," = ",round(Knot1_m,3)," m; q",
    Knot2_event_quantile," = ",round(Knot2_m,3)," m.")

write_out(data.frame(
  knot=c("knot1","knot2"),
  event_quantile=c(Knot1_event_quantile,Knot2_event_quantile),
  distance_m=c(Knot1_m,Knot2_m),
  derivation="Observed DS->AD event-distance quantile on final common population",
  stringsAsFactors=FALSE),
  "02a_piecewise_knot_definition.csv")

# Construct piecewise bases only AFTER the event-distance knots have been derived.
# Coefficients are log-HR per km within each segment.
# SEGMENTED DISTANCE BASES / UNITS
# Piecewise distance is expressed in kilometres, so segment coefficients
# are log hazard ratios per km (conditional on other fitted terms).
# M1: pmin(d,k1) and positive excess above k1.
# M2: distance accumulated below k1, between knots, and beyond k2.
# These are continuous linear splines (hinge/segment bases), NOT splines
# with smoothed derivatives and NOT stratified Cox models.
x$D_km <- x$distance_m/1000
k1 <- Knot1_m/1000
k2 <- Knot2_m/1000
x$D1_km <- pmin(x$D_km,k1)
x$D1_tail_km <- pmax(x$D_km-k1,0)
x$D2a_km <- pmin(x$D_km,k1)
x$D2b_km <- pmax(pmin(x$D_km,k2)-k1,0)
# METADATA PROVENANCE
# The preceding knot-definition export records both knot locations.
# The following 00_model_metadata.csv output identifies the original SOURCE
# SCRIPT name and version 1.1.2. Publication aliasing does not change those
# executable strings: retain the original source identity for audit.
x$D2c_km <- pmax(x$D_km-k2,0)

write_out(data.frame(
  item=c("script","version","transition","event_field","risk_field","distance_field",
         "knot_method","knot1_event_quantile","knot1_m",
         "knot2_event_quantile","knot2_m","rows","events","cluster_by_ID",
         "history_terms","omitted_after_J3D"),
  value=c("FRAF_Step3E_Jamuna_DSAD_Piecewise_Distance_Final_v1_1_2_ORDER_FIX.rsx","1.1.2",
          "Depositional Storage -> Active Domain",event_f,risk_f,dist_f,
          "event-distance quantiles; no AIC knot search",
          Knot1_event_quantile,Knot1_m,Knot2_event_quantile,Knot2_m,
          nrow(x),sum(x$event),Cluster_by_ID,
          paste(hist_z,collapse="; "),"ASM_N_EPISODES_PREV_Z"),
  stringsAsFactors=FALSE),"00_model_metadata.csv")

# ROBUST VARIANCE / PLACE DEPENDENCE
# Optional cluster(id) requests a sandwich variance estimator for
# repeated observations of the same PLACE or BLOCK ID. It does not by
# itself remove correlations between neighbouring PLACEs or test PH.
cluster_rhs <- if(isTRUE(Cluster_by_ID)) " + cluster(id)" else ""
surv_lhs <- "Surv(tstart,tstop,event)"
hist_rhs <- paste(hist_z,collapse=" + ")

# THREE NESTED DISTANCE-FORM CANDIDATES
# M0: linear AD-margin distance in km.
# M1: two segment slopes divided at event-distance q75.
# M2: three segment slopes divided at q75 and q90.
# Cox counting-process form Surv(tstart,tstop,event), Efron ties.
# The common history specification and eligible records are held fixed;
# the diagnostic evaluates in-sample functional-form differences.
forms <- list(
  M0_linear = as.formula(paste(surv_lhs,"~ D_km +",hist_rhs,cluster_rhs)),
  M1_piecewise_1knot = as.formula(paste(surv_lhs,"~ D1_km + D1_tail_km +",hist_rhs,cluster_rhs)),
  M2_piecewise_2knot = as.formula(paste(surv_lhs,"~ D2a_km + D2b_km + D2c_km +",hist_rhs,cluster_rhs))
)

# FITTING AND NUMERICAL QA
# Iteration tolerance and maximum iterations are explicitly specified.
# Warnings are caught and recorded, but a fit returning a coxph object
# is classified status=OK even if the warning indicates instability.
# Check recorded warnings/convergence before accepting coefficient values.
fits <- list(); fit_rows <- list(); coef_rows <- list(); ph_rows <- list()
# Per-model exports: log likelihood, AIC, concordance, number of
# parameters, robust coefficient SE when present, and PH diagnostics.
# cox.zph runs conditionally; a PH rejection limits constant-HR inference,
# even if rank discrimination or fit statistics improve.
for(nm in names(forms)) {
  msg("[Step 3E] Fitting ",nm," ...")
  ww <- character()
  fit <- tryCatch(withCallingHandlers(
    coxph(forms[[nm]],data=x,ties="efron",x=TRUE,y=TRUE,model=FALSE,
          control=coxph.control(iter.max=50,eps=1e-8,toler.inf=1e-8)),
    warning=function(w){ww <<- c(ww,conditionMessage(w)); invokeRestart("muffleWarning")}),
    error=function(e)e)
  if(inherits(fit,"error")) {
    fit_rows[[nm]] <- data.frame(model=nm,status="FAILED",n=nrow(x),events=sum(x$event),
      logLik=NA,AIC=NA,concordance=NA,n_parameters=NA,warnings=conditionMessage(fit))
    next
  }
  fits[[nm]] <- fit
  sm <- try(summary(fit),silent=TRUE)
  conc <- if(!inherits(sm,"try-error")&&!is.null(sm$concordance)) as.numeric(sm$concordance[1]) else NA_real_
  fit_rows[[nm]] <- data.frame(model=nm,status="OK",n=nrow(x),events=sum(x$event),
    logLik=as.numeric(logLik(fit)),AIC=AIC(fit),concordance=conc,
    n_parameters=length(coef(fit)),warnings=paste(unique(ww),collapse=" | "))
  if(!inherits(sm,"try-error")&&!is.null(sm$coefficients)) {
    cf <- sm$coefficients
    coef_rows[[nm]] <- data.frame(
      model=nm,term=rownames(cf),beta=cf[,"coef"],HR=exp(cf[,"coef"]),
      robust_SE=if("robust se"%in%colnames(cf))cf[,"robust se"] else
                if("se(coef)"%in%colnames(cf))cf[,"se(coef)"] else NA_real_,
      z=if("z"%in%colnames(cf))cf[,"z"] else NA_real_,
      p=if("Pr(>|z|)"%in%colnames(cf))cf[,"Pr(>|z|)"] else NA_real_,
      row.names=NULL)
  }
  if(isTRUE(Run_PH_test)) {
    zz <- try(cox.zph(fit,transform="km"),silent=TRUE)
    if(!inherits(zz,"try-error")) {
      tb <- as.data.frame(zz$table)
      ph_rows[[nm]] <- data.frame(model=nm,term=rownames(tb),
        chisq=tb[,1],df=tb[,2],p=tb[,3],row.names=NULL)
    } else {
      ph_rows[[nm]] <- data.frame(model=nm,term="PH_TEST_FAILED",
                                  chisq=NA,df=NA,p=NA)
    }
  }
  msg("[Step 3E] ",nm," complete.")
}

# FUNCTIONAL-FORM COMPARISONS
# Delta AIC uses the best successfully fitted model as the reference;
# likelihood-ratio contrasts are calculated relative to M0_linear.
# All are same-record, in-sample comparisons: neither AIC nor LR nor C
# constitutes held-out performance verification. PH and fit stability
# must be interpreted independently of an improvement in AIC.
cmp <- do.call(rbind,fit_rows); rownames(cmp) <- NULL
if(any(cmp$status=="OK")) {
  cmp$delta_AIC <- cmp$AIC-min(cmp$AIC[cmp$status=="OK"],na.rm=TRUE)
} else cmp$delta_AIC <- NA_real_
cmp$LR_vs_linear <- NA_real_; cmp$LR_df <- NA_real_; cmp$LR_p <- NA_real_
i0 <- which(cmp$model=="M0_linear" & cmp$status=="OK")
if(length(i0)==1) {
  for(i in seq_len(nrow(cmp))) if(i!=i0 && cmp$status[i]=="OK") {
    df_lr <- cmp$n_parameters[i]-cmp$n_parameters[i0]
    lr <- 2*(cmp$logLik[i]-cmp$logLik[i0])
    cmp$LR_vs_linear[i] <- lr; cmp$LR_df[i] <- df_lr
    if(df_lr>0) cmp$LR_p[i] <- pchisq(lr,df=df_lr,lower.tail=FALSE)
  }
}
write_out(cmp,"03_model_comparison.csv")
if(length(coef_rows)) write_out(do.call(rbind,coef_rows),"04_coefficients.csv")
if(length(ph_rows)) write_out(do.call(rbind,ph_rows),"05_PH_diagnostics.csv")

# ---------------------------------------------------------------------------
# Relative-hazard curves: history terms fixed at zero (their standardised mean).
# Each curve is normalised to HR=1 at distance=0. This isolates distance form.
# ---------------------------------------------------------------------------
# PREDICTED RESPONSE CURVES — NOT PROBABILITY FORECASTS
# Build a distance-only evaluation grid. Knots are included if within
# the specified plot range. Curve values hold standardised history terms
# at zero and are normalised to relative HR=1 at zero distance.
grid_m <- unique(c(seq(0,Response_plot_max_m,by=Response_plot_step_m),
                   Knot1_m,Knot2_m))
grid_m <- sort(grid_m[grid_m>=0 & grid_m<=Response_plot_max_m])
# Synthetic reference rows are used only for constructing displayed
# conditional relative-hazard curves, never added to a model risk set.
nd <- data.frame(id="REFERENCE",tstart=0,tstop=1,event=0,
                 distance_m=grid_m,D_km=grid_m/1000)
for(v in hist_z) nd[[v]] <- 0
nd$D1_km <- pmin(nd$D_km,k1)
nd$D1_tail_km <- pmax(nd$D_km-k1,0)
nd$D2a_km <- pmin(nd$D_km,k1)
nd$D2b_km <- pmax(pmin(nd$D_km,k2)-k1,0)
nd$D2c_km <- pmax(nd$D_km-k2,0)

# For fitted models, calculate the linear predictor manually from their
# DISTANCE coefficients. This avoids cluster(id) prediction issues.
# Coefficients of history terms cancel in a relative comparison with
# history fixed at zero. Exponentiation is bounded to avoid overflow.
curve_rows <- list()
for(nm in names(fits)) {
  fit <- fits[[nm]]
  # Manual model-matrix calculation avoids predict() issues with cluster().
  b <- coef(fit)
  distance_terms <- switch(nm,
    M0_linear=c("D_km"),
    M1_piecewise_1knot=c("D1_km","D1_tail_km"),
    M2_piecewise_2knot=c("D2a_km","D2b_km","D2c_km"))
  eta <- rep(0,nrow(nd))
  for(v in distance_terms) if(v %in% names(b)) eta <- eta + nd[[v]]*b[[v]]
  eta <- eta-eta[1]
  curve_rows[[nm]] <- data.frame(model=nm,distance_m=grid_m,
                                  relative_hazard=exp(pmax(pmin(eta,700),-700)))
}
# EXPORT CAVEAT: successful model fitting is assumed for response curves.
# If ALL models fail, the original source may not finish curve/plot output.
curves <- do.call(rbind,curve_rows); rownames(curves) <- NULL
write_out(curves,"06_distance_response_curves.csv")

# Plot.
# PLOTTING
# The displayed hazard scale is capped at 5 to retain readable curves.
# This is a VISUAL cap only; the CSV contains uncapped relative hazards.
# Model curves need not identify a unique geomorphic threshold at 150 m
# resolution; the earliest segmented interval can be much narrower.
png(file.path(Output_Directory,"07_distance_response_comparison.png"),
    width=1800,height=1200,res=180)
ok_models <- unique(curves$model)
yr <- curves$relative_hazard[is.finite(curves$relative_hazard)]
ylim <- c(0, min(max(yr,na.rm=TRUE),5))
if(!is.finite(ylim[2]) || ylim[2]<=0) ylim <- c(0,1)
plot(NA,xlim=c(0,Response_plot_max_m),ylim=ylim,
     xlab="Distance from active-domain margin (m)",
     ylab="Relative hazard (HR; distance 0 m = 1)",
     main="Jamuna DS->AD: final distance-form comparison")
ltys <- seq_along(ok_models)
for(i in seq_along(ok_models)) {
  z <- curves[curves$model==ok_models[i],]
  lines(z$distance_m,pmin(z$relative_hazard,ylim[2]),lty=ltys[i],lwd=2)
}
abline(v=c(Knot1_m,Knot2_m),lty=3)
legend("topright",legend=ok_models,lty=ltys,lwd=2,bty="n")
dev.off()

# Simple decision aid; not an automatic scientific model selection.
# REPORTING AID / SCIENTIFIC DECISION
# The decision CSV describes the three options but does NOT automatically
# select M2. Paper 2 S6 Table S13 reports stronger in-sample fit of the
# segmented Jamuna DS->AD model, but retains linear AD-margin distance
# as the parsimonious principal interpretation; the first segment is
# shorter than the 150 m fixed-place support and PH warnings persist.
# For numerical provenance compare 00_model_metadata.csv and
# 03_model_comparison.csv against the published S13 analysis population.
decision <- data.frame(
  criterion=c("Same population","Linear reference","One-knot comparison",
              "Two-knot comparison","Interpretation rule"),
  value=c(
    paste0(nrow(x)," rows; ",sum(x$event)," events"),
    "M0_linear",
    paste0("M1, knot=",Knot1_m," m"),
    paste0("M2, knots=",Knot1_m,", ",Knot2_m," m"),
    "Prefer piecewise only if improvement is substantial, stable, convergent and geomorphically interpretable; otherwise retain linear and report nonlinearity as sensitivity."
  ),stringsAsFactors=FALSE)
write_out(decision,"08_decision_aid.csv")

# END-OF-RUN SOURCE NOTE
# Expected products: 00_model_metadata.csv; 01_field_resolution.csv;
# 02_event_distance_quantiles.csv; 02a_piecewise_knot_definition.csv;
# 03_model_comparison.csv; 04_coefficients.csv; 05_PH_diagnostics.csv
# (if PH tests enabled); 06_distance_response_curves.csv;
# 07_distance_response_comparison.png; 08_decision_aid.csv.
# This script does not export a separate immutable hash/input manifest.
# Retain the original Risk Table location, parameters, output folder,
# R package versions and result hashes in the external run manifest.
msg("[Step 3E v1.1.2] Complete. Outputs written to: ",Output_Directory)
