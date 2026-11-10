##FRAF_Step3B_Distance_Response_Diagnostic_v1_4_1_JAMUNA_READY=name
##Input_table=file
##Output_directory=folder
##Transition=selection active_domain_reactivation;depositional_storage_reworking
##Reach=selection Mamore;Jamuna
##Margin_distance_field=string AUTO
##Centreline_distance_field=string AUTO
##Event_field=string AUTO
##Risk_set_field=string AUTO
##Start_time_field=string AUTO
##Stop_time_field=string AUTO
##ID_field=string PLACE_ID
##Cluster_field=string PLACE_ID
##Interval_field=string AUTO
##Loop_reactivation_field=string AUTO
##Spline_df=number 4
##Model_distance_cap_quantile=number 0.999
##N_distance_bins=number 20
##Max_distance_for_plot=number 0
##Distal_threshold_m=number 1000
##Use_robust_SE=boolean TRUE
##Run_PH_test=boolean TRUE
##Plot_width=number 8
##Plot_height=number 6

# -----------------------------------------------------------------------------
# PAPER 2 PUBLICATION ARCHIVE — DOCUMENTATION ONLY (v1.4.1)
# Archive alias: FRAF_P2_DIAG_DistanceResponse_v1_4_1.rsx
# Original: FRAF_Step3B_Distance_Response_Diagnostic_v1_4_1_JAMUNA_READY(1).rsx
# Source version and execution: no executable edits; this is NOT a new model fit.
# Purpose: compare marginal vs reference-centreline distance and functional form
# for two transition-specific historical Cox risk populations: SF->AD and DS->AD.
# The executable's QGIS Processing name, runtime messages, filenames, and field
# conventions are deliberately retained to preserve source/run traceability.
# This diagnostic assists response-function selection; it does not construct
# the underlying assemblage, risk table, or held-out prediction footprints.
# -----------------------------------------------------------------------------
# FRAF Step 3B — Formal Distance-Response Diagnostic v1.4.1 — v17.10.13 aligned — overflow safe — Jamuna ready
# Canonical model terminology:
#   active_domain_reactivation     = Stabilised floodplain -> Active domain
#   depositional_storage_reworking = Depositional storage -> Active domain
# Compares interval-start margin vs centreline distance and linear/log1p/spline response forms.
# v17.10.13 alignment: *_CURR fields are interval-start y1; Mamore local *_PREV
# fields are also matched to y1 (PREV identifies lookup/history source, not y0).
# Cox clustering follows v17.10.13: cluster(PLACE_ID).
# For DS->AD, explicitly diagnoses the distal tail and only labels loop
# reactivation when a genuine loop-reactivation source field exists.

# [DIAG-01] Output and small utility functions.
# Existing output files with the same names may be overwritten on rerun.
# CSV writer uses base R; data-frame labels preserve the executable's own terms.
options(stringsAsFactors = FALSE, warn = 1)
dir.create(Output_directory, recursive = TRUE, showWarnings = FALSE)
msg <- function(...) { cat(paste0(...), "\n"); flush.console() }
write_csv_safe <- function(x, name) utils::write.csv(x, file.path(Output_directory, name), row.names=FALSE, na="")
safe_num <- function(x) suppressWarnings(as.numeric(as.character(x)))

# [DIAG-02] Resolve a requested field, or try known aliases in priority order.
# AUTO / NONE means use candidates; required absent fields stop the diagnostic.
# CSV auditing below is essential because different river workflows use
# distinct operational names for interval-start distance and event indicators.
pick_field <- function(nms, requested, candidates=character(), required=TRUE) {
  if (!is.null(requested) && length(requested)==1L && !is.na(requested) && nzchar(requested) &&
      !toupper(requested) %in% c("AUTO","NONE")) {
    hit <- nms[toupper(nms)==toupper(requested)]
    if (length(hit)) return(hit[1])
    if (required) stop("Requested field not found: ", requested)
    return(NA_character_)
  }
  up <- toupper(nms)
  for (cand in candidates) {
    j <- match(toupper(cand), up)
    if (!is.na(j)) return(nms[j])
  }
  if (required) stop("Could not auto-detect required field. Tried: ", paste(candidates, collapse=", "))
  NA_character_
}

# [DIAG-03] Read the supplied fixed-place longitudinal risk table.
# Supported formats: CSV/TXT, RDS, and selected vector data sources via sf.
# Spatial geometry is dropped: the Cox models here operate on table rows.
# Input river identity is selected in the algorithm, not inferred from data.
read_input <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("csv","txt")) return(utils::read.csv(path, check.names=FALSE))
  if (ext=="rds") return(readRDS(path))
  if (ext %in% c("gpkg","shp","geojson","sqlite")) {
    if (!requireNamespace("sf", quietly=TRUE)) stop("Package 'sf' is required to read spatial input.")
    return(sf::st_drop_geometry(sf::st_read(path, quiet=TRUE)))
  }
  stop("Unsupported input type: .", ext)
}

# [DIAG-04] R dependencies are checked before analysis.
# survival supplies counting-process Cox fitting and PH tests;
# splines supplies natural cubic spline basis functions.
if (!requireNamespace("survival", quietly=TRUE)) stop("Package 'survival' is required.")
if (!requireNamespace("splines", quietly=TRUE)) stop("Package 'splines' is required.")

# [DIAG-05] QGIS selection parameters are zero-indexed.
# The selected model is one transition population at a time; the script must
# be executed separately for SF->AD and DS->AD, and for each study river.
# Broad eligible FP->AD prediction is a distinct risk population, not this SF->AD fit.
model_key <- c("active_domain_reactivation","depositional_storage_reworking")[Transition+1]
reach_key <- c("Mamore","Jamuna")[Reach+1]
transition_label <- if (model_key=="active_domain_reactivation")
  "Stabilised floodplain -> Active domain" else "Depositional storage -> Active domain"

# [DIAG-06] Load the analyst-selected risk table and record available fields.
# This script does not check that the chosen table belongs to the selected reach;
# document the input path and selection outside the executable for provenance.
d <- read_input(Input_table); nms <- names(d)

# [DIAG-07] Transition-specific risk/event definitions.
# Reactivation is SF->AD; storage reworking is DS->AD.
# Only observed rows with the selected at-risk flag and binary event enter fits.
if (model_key=="active_domain_reactivation") {
  event_candidates <- c("REACTIVATE_EVT","REACTIVATE_EVT_PRIMARY","SF_AD_EVENT","SF_TO_AD_EVENT")
  risk_candidates <- c("REACTIVATE_RISK_SET","REACTIVATE_RISK_SET_PRIMARY","SF_AD_RISK_SET","SF_TO_AD_RISK_SET")
} else {
  event_candidates <- c("STORAGE_REWORK_EVT","STORAGE_REWORK_EVT_PRIMARY","DS_AD_EVENT","DS_TO_AD_EVENT")
  risk_candidates <- c("STORAGE_REWORK_RISK_SET","STORAGE_REWORK_RISK_SET_PRIMARY","DS_AD_RISK_SET","DS_TO_AD_RISK_SET")
}

# [DIAG-08] The exact resolved event and risk-set columns are exported.
# Check candidate priority if multiple potentially valid versions coexist.
event_f <- pick_field(nms, Event_field, event_candidates, TRUE)
risk_f <- pick_field(nms, Risk_set_field, risk_candidates, TRUE)

# AUTO field priorities are aligned to v17.10.13:
# Mamore: local interval-start channel geometry first.
# Jamuna: interval-start active-domain margin (DIST_ACTIVE_CURR) and fixed/reference
#         centreline distance (DIST_CL_REF) first.
# [DIAG-09] Distance is measured at the start of the exposure interval.
# Mamore local '*_PREV' fields refer to matched interval-start geometry,
# not to a hypothetical extra previous observation date.
# Jamuna AUTO prefers active-domain margin DIST_ACTIVE_CURR and reference
# centreline DIST_CL_REF; these are different geometric reference objects.
# The field selected should be interpreted physically, not just by name.
margin_candidates <- if (reach_key=="Mamore")
  c("DIST_CHANNEL_PREV","DIST_BANK_PREV","DIST_ACTIVE_CURR","DIST_WATER_CURR","DIST_CHANNEL_CURR") else
  c("DIST_ACTIVE_CURR","DIST_WATER_CURR","DIST_CHANNEL_PREV","DIST_BANK_PREV")
centre_candidates <- if (reach_key=="Mamore")
  c("DIST_CL_PREV","DIST_CL_CURR","DIST_CL_REF") else
  c("DIST_CL_REF","DIST_CL_CURR","DIST_CL_PREV")

# [DIAG-10] Resolve reference geometry columns separately by river.
# Margin vs centreline is an alternative exposure measure, not two predictors
# fitted simultaneously. The subsequent comparison uses identical retained rows.
margin_f <- pick_field(nms, Margin_distance_field, margin_candidates, TRUE)
centre_f <- pick_field(nms, Centreline_distance_field, centre_candidates, TRUE)
if (reach_key=="Jamuna") {
  msg("[Step 3B] Jamuna resolved distance fields: margin=",margin_f,
      "; centreline=",centre_f,
      ". AUTO priority is DIST_ACTIVE_CURR / DIST_CL_REF.")
}
# [DIAG-11] Auxiliary identifiers, interval times and optional loop status.
# The Cox robust cluster defaults to PLACE_ID. Optional interval labels support
# diagnosing exceptional distant reactivation episodes.
# Loop reactivation is only classified if an explicit source field exists.
start_f <- pick_field(nms, Start_time_field, c("TSTART","TSTART_YR","START_TIME","INTERVAL_START_RANK","START_RANK"), FALSE)
stop_f <- pick_field(nms, Stop_time_field, c("TSTOP","TSTOP_YR","STOP_TIME","INTERVAL_END_RANK","END_RANK"), FALSE)
id_f <- pick_field(nms, ID_field, c("PLACE_ID","BLOCK_ID","CELL_ID","ID"), FALSE)
cluster_f <- pick_field(nms, Cluster_field, c("PLACE_ID","BLOCK_ID","CELL_ID","ID"), FALSE)
interval_f <- pick_field(nms, Interval_field, c("INTERVAL_LABEL","INTERVAL","STEP","STEP_ID","PERIOD","YEAR_PAIR","INTERVAL_ID","INTERVAL_NAME"), FALSE)
loop_f <- pick_field(nms, Loop_reactivation_field,
  c("LOOP_REACTIVATION","LOOP_REACTIVATION_EVT","LOOP_REACT_EVT","OLD_LOOP_REACTIVATION","CUTOFF_LOOP_REACTIVATION","CUTOFF_REACTIVATION"), FALSE)

# [DIAG-12] Field-resolution audit, written before filtering and fitting.
# This file is the primary trace of which aliases the source actually used.
write_csv_safe(data.frame(
  role=c("model","transition","reach","event","risk_set","margin_distance","centreline_distance","start_time","stop_time","interval","id","cluster","loop_reactivation"),
  field=c(model_key,transition_label,reach_key,event_f,risk_f,margin_f,centre_f,start_f,stop_f,interval_f,id_f,cluster_f,loop_f)),
  "01_field_resolution.csv")

# [DIAG-13] Coerce event, risk and distances into analysis columns.
# Both distance variables are required because both references are compared.
# Rows missing either valid distance will not enter either model family.
x <- data.frame(event=safe_num(d[[event_f]]), risk=safe_num(d[[risk_f]]),
                margin_distance=safe_num(d[[margin_f]]), centreline_distance=safe_num(d[[centre_f]]))
if (!is.na(start_f)) x$tstart <- safe_num(d[[start_f]])
if (!is.na(stop_f)) x$tstop <- safe_num(d[[stop_f]])
if (!is.na(id_f)) x$id <- d[[id_f]]
if (!is.na(cluster_f)) x$cluster <- d[[cluster_f]]
if (!is.na(interval_f)) x$interval <- as.character(d[[interval_f]])
if (!is.na(loop_f)) x$loop_reactivation <- safe_num(d[[loop_f]])

# v1.4: construct an interval identifier from the Cox start/stop times when
# no explicit interval field is present. This is essential for diagnosing
# concentration of distal events in exceptional reactivation intervals.
# [DIAG-14] Construct interval identity from start/stop when necessary.
# The constructed label is descriptive; it does not modify event times.
# Without resolved times or interval labels, some interval-tail QA is unavailable.
interval_source <- if (!is.na(interval_f)) interval_f else NA_character_
if (!("interval" %in% names(x)) && all(c("tstart","tstop") %in% names(x))) {
  fmt_time <- function(z) {
    ifelse(is.finite(z), format(round(z, 6), trim=TRUE, scientific=FALSE), NA_character_)
  }
  x$interval <- paste0(fmt_time(x$tstart), " -> ", fmt_time(x$tstop))
  interval_source <- paste0(start_f, " + ", stop_f, " (constructed)")
  msg("[Step 3B] No explicit interval field found; constructed interval labels from ",
      start_f, " and ", stop_f, ".")
}

# [DIAG-15] Assemble the transition-specific analysed risk population.
# Eligible records have risk==1, event 0/1 and finite nonnegative distances.
# Minimum event support is five; this is a diagnostic guard, not a guarantee
# that every spline or model comparison is statistically stable.
x <- x[is.finite(x$risk) & x$risk==1 & is.finite(x$event) & x$event %in% c(0,1) &
       is.finite(x$margin_distance) & x$margin_distance>=0 &
       is.finite(x$centreline_distance) & x$centreline_distance>=0,,drop=FALSE]
if (!nrow(x)) stop("No usable transition-specific risk-set rows.")
if (sum(x$event==1)<5) stop("Fewer than 5 usable transition events.")

# [DIAG-16] Exposure time for empirical event rates.
# With valid start/stop columns: exposure = stop - start, positive only.
# Otherwise a unit-exposure fallback is used; such rates are per record,
# not measured person/place-years. Counting-process Cox also uses times only
# when both columns are present with some finite data.
has_times <- all(c("tstart","tstop") %in% names(x)) && any(is.finite(x$tstart)) && any(is.finite(x$tstop))
if (has_times) {
  x$exposure <- x$tstop-x$tstart
  x <- x[is.finite(x$exposure) & x$exposure>0,,drop=FALSE]
} else x$exposure <- 1

# [DIAG-17] Save interval resolution and table-field QA.
# Note: the 01b 'reach' field is populated from the selection index in the
# original executable, while the 01 file supplies the human-readable river.
# This behaviour is preserved, not corrected in the publication source copy.
write_csv_safe(data.frame(
  interval_available=("interval" %in% names(x)),
  interval_source=ifelse(is.na(interval_source), "NONE", interval_source),
  unique_intervals=if ("interval" %in% names(x)) length(unique(x$interval)) else 0,
  stringsAsFactors=FALSE),
  "01a_interval_resolution.csv")

write_csv_safe(data.frame(
  reach=Reach,
  model=model_key,
  transition=transition_label,
  margin_distance_field=margin_f,
  centreline_distance_field=centre_f,
  event_field=event_f,
  risk_set_field=risk_f,
  start_time_field=ifelse(is.na(start_f),"NONE",start_f),
  stop_time_field=ifelse(is.na(stop_f),"NONE",stop_f),
  id_field=id_f,
  cluster_field=cluster_f,
  interval_field=ifelse(is.na(interval_f),"CONSTRUCTED_FROM_TIME",interval_f),
  stringsAsFactors=FALSE),
  "01b_resolved_fields.csv")

# [DIAG-18] Extract the first concordance element from survival::summary.
# Concordance is descriptive in-sample discrimination; it is not held-out AUC.
calc_cindex <- function(fit) {
  z <- try(summary(fit)$concordance, silent=TRUE)
  if (inherits(z,"try-error") || is.null(z)) return(NA_real_)
  as.numeric(z[1])
}

# [DIAG-19] One distance-reference family: null, linear, log1p and spline.
# Run separately for active-domain margin and reference-centreline distance.
# Each family uses the common transition-specific subset assembled above.
# There are no additional non-distance covariates in these diagnostic Cox fits.
fit_family <- function(dat, distance_col, distance_label) {
  dd_raw <- dat[is.finite(dat[[distance_col]]),,drop=FALSE]

  # Extreme distal observations can make the partial likelihood numerically
  # separable and cause exp(eta) overflow. Preserve RAW distance everywhere for
  # empirical/tail diagnostics, but cap the MODEL covariate only. This prevents
  # a handful of extreme values from crashing the formal response-form test.
# [DIAG-20] Guard extreme distal predictor values against model overflow.
# The cap is a quantile of the *raw* distance column, bounded to [0.95, 1].
# Only the fitted covariate is capped; raw distances remain in empirical bins,
# event quantiles and distal-tail summaries. Thus distal event geometry is not
# silently discarded even where the model response becomes constant past cap.
  cq <- min(max(as.numeric(Model_distance_cap_quantile), 0.95), 1.0)
  cap <- if (cq < 1) as.numeric(stats::quantile(dd_raw[[distance_col]], cq, na.rm=TRUE, type=8)) else Inf
  dd <- dd_raw
  dd$distance_model <- pmin(dd[[distance_col]], cap)
  n_capped <- sum(dd[[distance_col]] > cap, na.rm=TRUE)
  event_capped <- sum(dd$event==1 & dd[[distance_col]] > cap, na.rm=TRUE)
  cap_info <- data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
                         distance_field=if(distance_col=="margin_distance") margin_f else centre_f,
                         cap_quantile=cq,cap_distance=cap,n_rows=nrow(dd),n_capped=n_capped,
                         events_capped=event_capped)

# [DIAG-21] Standardise capped distances separately for linear and log1p.
# Coefficient units from these normalised predictors are not m or km directly.
# Spline uses the standardised capped raw distance and requested basis df.
  mu <- mean(dd$distance_model); sdv <- sd(dd$distance_model)
  if (!is.finite(sdv) || sdv<=0) stop("Zero/invalid distance variance: ", distance_label)
  dd$distance_z <- (dd$distance_model-mu)/sdv
  ld <- log1p(dd$distance_model); lmu <- mean(ld); lsd <- sd(ld)
  if (!is.finite(lsd) || lsd<=0) stop("Zero/invalid log-distance variance: ", distance_label)
  dd$log_distance_z <- (ld-lmu)/lsd

# [DIAG-22] Historical counting-process formulation where time is available.
# PLACE_ID clustering requests robust variance via survival::cluster(),
# addressing repeated PLACE histories but not between-place spatial dependence.
# Without times, a one-time-unit survival response is used as a fallback.
  if (has_times) surv_term <- "survival::Surv(tstart,tstop,event)" else { dd$.time <- 1; surv_term <- "survival::Surv(.time,event)" }
  cl <- if (isTRUE(Use_robust_SE) && "cluster" %in% names(dd)) " + survival::cluster(cluster)" else ""

# [DIAG-23] Fit wrapper captures convergence and numerical warnings.
# Failure of one form is recorded rather than terminating all comparisons.
# Ties use Efron; the original source controls optimisation and retains x/model.
  safe_ff <- function(rhs, form) {
    msg("[Step 3B]   fitting ", distance_label, " / ", form, " ...")
    warns <- character()
    fit <- tryCatch(
      withCallingHandlers(
        survival::coxph(as.formula(paste(surv_term,"~",rhs,cl)), data=dd, ties="efron",
                        x=TRUE, model=TRUE,
                        control=survival::coxph.control(iter.max=40, eps=1e-8, toler.inf=1e-8)),
        warning=function(w) { warns <<- c(warns, conditionMessage(w)); invokeRestart("muffleWarning") }
      ),
      error=function(e) e
    )
    if (inherits(fit,"error")) {
      msg("[Step 3B]   FAILED: ", form, " — ", conditionMessage(fit))
      return(list(fit=NULL,status="FAILED",message=conditionMessage(fit),warnings=paste(unique(warns),collapse=" | ")))
    }
    list(fit=fit,status="OK",message="",warnings=paste(unique(warns),collapse=" | "))
  }

# [DIAG-24] Compare four prespecified response forms.
# The null form is a diagnostic reference; the distances are fitted one at a
# time and should not be interpreted as a causal or multivariable adjustment.
  fits <- list(
    none=safe_ff("1","none"),
    linear=safe_ff("distance_z","linear"),
    log1p=safe_ff("log_distance_z","log1p"),
    spline=safe_ff(paste0("splines::ns(distance_z,df=",round(Spline_df),")"),paste0("natural_spline_df",round(Spline_df)))
  )

# [DIAG-25] Export full in-sample fit comparison and warning state.
# AIC is calculated from the unpenalised partial likelihood; the robust
# clustered sandwich variance does not make AIC a held-out metric.
# Delta AIC is computed within each distance-reference family here.
  forms <- c(none="none",linear="linear",log1p="log1p",spline=paste0("natural_spline_df",round(Spline_df)))
  rows <- lapply(names(fits), function(nm) {
    z <- fits[[nm]]; fit <- z$fit
    if (is.null(fit)) return(data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
      distance_field=if(distance_col=="margin_distance") margin_f else centre_f,response_form=forms[[nm]],
      n=nrow(dd),events=sum(dd$event),logLik=NA_real_,df=NA_real_,AIC=NA_real_,concordance=NA_real_,
      fit_status=z$status,fit_message=z$message,fit_warnings=z$warnings))
    data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
      distance_field=if(distance_col=="margin_distance") margin_f else centre_f,response_form=forms[[nm]],
      n=fit$n,events=fit$nevent,logLik=as.numeric(logLik(fit)),df=attr(logLik(fit),"df"),AIC=AIC(fit),
      concordance=calc_cindex(fit),fit_status=z$status,fit_message=z$message,fit_warnings=z$warnings)
  })
  cmp <- do.call(rbind, rows)
  if (any(is.finite(cmp$AIC))) cmp$delta_AIC_within_reference <- cmp$AIC-min(cmp$AIC,na.rm=TRUE) else cmp$delta_AIC_within_reference <- NA_real_

# [DIAG-26] Linear-versus-natural-spline likelihood comparison.
# The LR calculation reflects conventional partial-likelihood nesting;
# it is not a robust sandwich-based hypothesis test under spatial dependence.
# Interpret alongside the fitted curves, exposure patterns and PH diagnostics.
  m1 <- fits$linear$fit; m3 <- fits$spline$fit
  if (!is.null(m1) && !is.null(m3)) {
    lr <- 2*(as.numeric(logLik(m3))-as.numeric(logLik(m1))); ddf <- attr(logLik(m3),"df")-attr(logLik(m1),"df")
    nonlinear <- data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
      distance_field=if(distance_col=="margin_distance") margin_f else centre_f,comparison="linear_vs_natural_spline",
      LR_chisq=lr,df=ddf,p_value=pchisq(lr,df=ddf,lower.tail=FALSE),test_status="OK")
  } else nonlinear <- data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
      distance_field=if(distance_col=="margin_distance") margin_f else centre_f,comparison="linear_vs_natural_spline",
      LR_chisq=NA_real_,df=NA_real_,p_value=NA_real_,test_status="NOT_AVAILABLE_MODEL_FAILURE")

# [DIAG-27] Predict spline relative hazard curves on a descriptive grid.
# Automatic display range uses the raw-distance 99th percentile unless
# Max_distance_for_plot sets an explicit maximum. Clamping fitted covariates
# past the cap yields a flat estimated tail; it is not evidence of a real plateau.
# Numerically bounded log hazards protect CSV export against exp overflow.
  pmax <- if (is.finite(Max_distance_for_plot) && Max_distance_for_plot>0) min(Max_distance_for_plot,max(dd_raw[[distance_col]])) else as.numeric(quantile(dd_raw[[distance_col]],.99,na.rm=TRUE))
  curve <- data.frame()
  if (!is.null(m3)) {
    gd <- seq(0,pmax,length.out=300)
    gdm <- pmin(gd,cap)
    nd <- data.frame(distance_z=(gdm-mu)/sdv,log_distance_z=(log1p(gdm)-lmu)/lsd)
    if ("cluster" %in% names(dd)) nd$cluster <- dd$cluster[1]
    pr <- try(predict(m3,newdata=nd,type="lp",se.fit=TRUE,reference="zero"),silent=TRUE)
    if (!inherits(pr,"try-error")) {
      ref <- as.numeric(predict(m3,newdata=nd[1,,drop=FALSE],type="lp",reference="zero"))
      lp <- as.numeric(pr$fit)-ref; se <- as.numeric(pr$se.fit)
      # Avoid output overflow while retaining all finite diagnostic information.
      lp <- pmax(pmin(lp,700),-700)
      curve <- data.frame(model=model_key,transition=transition_label,distance_reference=distance_label,
        distance_field=if(distance_col=="margin_distance") margin_f else centre_f,distance=gd,
        model_distance=pmin(gd,cap),relative_hazard_vs_zero=exp(lp),
        rh_lcl95=exp(pmax(pmin(lp-1.96*se,700),-700)),rh_ucl95=exp(pmax(pmin(lp+1.96*se,700),-700)))
    }
  }

# [DIAG-28] Optional proportional-hazards test for the spline form.
# This is a model diagnostic, not a cure for PH violation. A nonsignificant
# result does not establish time-invariant causal effects.
  ph <- NULL
  if (isTRUE(Run_PH_test) && !is.null(m3)) {
    z <- try(survival::cox.zph(m3,transform="identity",terms=TRUE,singledf=FALSE),silent=TRUE)
    if (!inherits(z,"try-error")) {
      ph <- as.data.frame(z$table); ph$term <- rownames(ph); rownames(ph)<-NULL
      ph$model<-model_key; ph$transition<-transition_label; ph$distance_reference<-distance_label
      ph$distance_field<-if(distance_col=="margin_distance") margin_f else centre_f
    }
  }
  list(cmp=cmp,nonlinear=nonlinear,curve=curve,ph=ph,cap_info=cap_info)
}

# [DIAG-29] Empirical event frequencies by equal-width raw-distance bins.
# Rates use the summed exposure defined above. Event counts are observational;
# bins are descriptive and do not impose distance-dependent risk thresholds.
# Display may be truncated at raw-distance 99th percentile by default.
empirical_bins <- function(dat,distance_col,distance_label) {
  pmax <- if (is.finite(Max_distance_for_plot) && Max_distance_for_plot>0) min(Max_distance_for_plot,max(dat[[distance_col]])) else as.numeric(quantile(dat[[distance_col]],.99))
  z <- dat[dat[[distance_col]]<=pmax,,drop=FALSE]
  z$bin <- cut(z[[distance_col]],breaks=seq(0,pmax,length.out=max(5,round(N_distance_bins))+1),include.lowest=TRUE,right=FALSE)
  a1<-aggregate(event~bin,z,length); names(a1)[2]<-"n_rows"
  a2<-aggregate(event~bin,z,sum); names(a2)[2]<-"events"
  a3<-aggregate(exposure~bin,z,sum); names(a3)[2]<-"place_time"
  a4<-aggregate(z[[distance_col]],list(bin=z$bin),mean); names(a4)<-c("bin","mean_distance")
  o<-Reduce(function(a,b) merge(a,b,by="bin",all=TRUE),list(a1,a2,a3,a4))
  o$event_rate_per_1000_place_time<-1000*o$events/o$place_time
  o$model<-model_key; o$transition<-transition_label; o$distance_reference<-distance_label
  o$distance_field<-if(distance_col=="margin_distance") margin_f else centre_f
  o
}

# [DIAG-30] Fit both geometrical references for the same transition.
# Each supplied river and transition requires a separate QGIS Processing run.
msg("[Step 3B] Fitting margin-distance family...")
fm <- fit_family(x,"margin_distance","interval_start_active_channel_margin")
msg("[Step 3B] Fitting centreline-distance family...")
fc <- fit_family(x,"centreline_distance","centreline_reference")
# [DIAG-31] In-sample AIC comparison and model-distance cap audit.
# The global delta AIC compares form + reference on the common row population.
# Saved tables retain failure messages so incomplete families remain visible.
comparison <- rbind(fm$cmp,fc$cmp); if (any(is.finite(comparison$AIC))) comparison$delta_AIC_global <- comparison$AIC-min(comparison$AIC,na.rm=TRUE) else comparison$delta_AIC_global <- NA_real_
write_csv_safe(comparison,"02_model_comparison_margin_vs_centreline.csv")
write_csv_safe(rbind(fm$cap_info,fc$cap_info),"02a_model_distance_cap_diagnostic.csv")
write_csv_safe(rbind(fm$nonlinear,fc$nonlinear),"03_nonlinearity_tests.csv")
write_csv_safe(rbind(fm$curve,fc$curve),"04_relative_hazard_response_curves.csv")
write_csv_safe(rbind(empirical_bins(x,"margin_distance","interval_start_active_channel_margin"),
                     empirical_bins(x,"centreline_distance","centreline_reference")),"05_empirical_event_rates_by_distance.csv")
if (!is.null(fm$ph) || !is.null(fc$ph)) write_csv_safe(rbind(fm$ph,fc$ph),"06_PH_distance_tests.csv")

# [DIAG-32] Event-distance quantiles from the retained at-risk observations.
# These are raw event locations and are not the fitted capped covariate values.
qfun <- function(v) as.numeric(quantile(v,probs=c(.5,.75,.9,.95,.99),na.rm=TRUE))
write_csv_safe(rbind(
  data.frame(distance_reference="interval_start_active_channel_margin",distance_field=margin_f,quantile=c(.5,.75,.9,.95,.99),distance=qfun(x$margin_distance[x$event==1])),
  data.frame(distance_reference="centreline_reference",distance_field=centre_f,quantile=c(.5,.75,.9,.95,.99),distance=qfun(x$centreline_distance[x$event==1]))),
  "07_event_distance_quantiles.csv")

# -----------------------------------------------------------------------------
# v1.4 distal-event diagnostic for BOTH modelled transitions
# -----------------------------------------------------------------------------
# The same threshold summary and event export is now produced for SF->AD and
# DS->AD. This allows anomalous distal SF->AD events to be checked rather than
# silently absorbed into the fitted distance response.
# [DIAG-33] Distal-event thresholds apply to BOTH SF->AD and DS->AD.
# These describe events farther than each threshold from the active margin,
# their fraction of all events and at-risk place-time. Thresholds are
# diagnostic sensitivity points, not formally estimated hazard breakpoints.
thresholds <- sort(unique(c(250,500,1000,2000,5000,Distal_threshold_m)))
distal_prefix <- if (model_key=="active_domain_reactivation") "SF_AD" else "DS_AD"

# [DIAG-34] Summarise distal events and exposure at each threshold.
# Counts include the analysed risk population only, not all EA erosion.
ts <- do.call(rbind,lapply(thresholds,function(thr) {
  ev <- x$event==1
  distal <- x$margin_distance>thr
  pt <- sum(x$exposure[distal], na.rm=TRUE)
  data.frame(
    model=model_key,
    transition=transition_label,
    threshold_m=thr,
    total_events=sum(ev,na.rm=TRUE),
    distal_events=sum(ev & distal,na.rm=TRUE),
    distal_event_fraction=if (sum(ev,na.rm=TRUE)>0) sum(ev & distal,na.rm=TRUE)/sum(ev,na.rm=TRUE) else NA_real_,
    distal_risk_rows=sum(distal,na.rm=TRUE),
    distal_place_time=pt,
    distal_rate_per_1000_place_time=if (is.finite(pt) && pt>0) 1000*sum(ev & distal,na.rm=TRUE)/pt else NA_real_
  )
}))
write_csv_safe(ts,paste0("08_",distal_prefix,"_distal_tail_summary.csv"))

# Export all event records beyond the user-selected threshold, preserving
# PLACE_ID, interval, start/stop time, margin distance and centreline distance
# where available. These records are intended for direct geomorphic/map review.
# [DIAG-35] Export individual distal event records for map validation.
# Candidate far-field reactivation must be reviewed geomorphically; distance
# alone does not establish channel-avulsion or abandoned-loop mechanisms.
de <- x[x$event==1 & x$margin_distance>Distal_threshold_m,,drop=FALSE]
if (nrow(de)) {
  write_csv_safe(de,paste0("09_",distal_prefix,"_distal_event_records.csv"))
} else {
  write_csv_safe(data.frame(
    model=model_key,transition=transition_label,
    note=paste0("No events beyond ",Distal_threshold_m," m")),
    paste0("09_",distal_prefix,"_distal_event_records.csv"))
}

# Interval concentration is now always attempted. If no explicit interval field
# existed, v1.4 uses the constructed tstart -> tstop identifier above.
# [DIAG-36] Identify exceptional observation intervals in the distal tail.
# Interval labels derive from a source field or start/stop times as documented.
# This distinguishes persistent distance response from a few influential years.
if ("interval" %in% names(x)) {
  evx <- x[x$event==1,,drop=FALSE]
  evx$distal <- evx$margin_distance>Distal_threshold_m
  a <- aggregate(event~interval,evx,sum); names(a)[2] <- "events"
  b <- aggregate(distal~interval,evx,sum); names(b)[2] <- "distal_events"
  med <- aggregate(margin_distance~interval,evx,function(v) median(v,na.rm=TRUE))
  names(med)[2] <- "median_event_margin_distance"
  p90 <- aggregate(margin_distance~interval,evx,function(v) as.numeric(quantile(v,.90,na.rm=TRUE,names=FALSE)))
  names(p90)[2] <- "p90_event_margin_distance"
  p95 <- aggregate(margin_distance~interval,evx,function(v) as.numeric(quantile(v,.95,na.rm=TRUE,names=FALSE)))
  names(p95)[2] <- "p95_event_margin_distance"
  mx <- aggregate(margin_distance~interval,evx,function(v) max(v,na.rm=TRUE))
  names(mx)[2] <- "max_event_margin_distance"
  ii <- Reduce(function(u,v) merge(u,v,by="interval",all=TRUE),list(a,b,med,p90,p95,mx))
  ii$distal_fraction <- ifelse(ii$events>0,ii$distal_events/ii$events,NA_real_)
  ii <- ii[order(-ii$distal_events,-ii$distal_fraction,-ii$max_event_margin_distance),]
  write_csv_safe(ii,paste0("10_",distal_prefix,"_distal_events_by_interval.csv"))
} else {
  writeLines(
    "No interval identifier could be resolved or constructed.",
    file.path(Output_directory,paste0("10_",distal_prefix,"_distal_events_by_interval_NOTE.txt"))
  )
}

# Explicit loop-reactivation stratification is relevant to DS->AD only and only
# where a genuine source field exists. It is never inferred from distance.
# [DIAG-37] Optional genuine loop-reactivation stratification for DS->AD.
# When no explicit source flag is available, write a NOTE instead of inventing
# a loop classification from distance, bend curvature or reach morphology.
if (model_key=="depositional_storage_reworking") {
  if ("loop_reactivation" %in% names(x)) {
    zz <- x[x$event==1,,drop=FALSE]
    zz$distal <- zz$margin_distance>Distal_threshold_m
    tab <- aggregate(cbind(event,distal)~loop_reactivation,zz,sum)
    tab$distal_fraction <- ifelse(tab$event>0,tab$distal/tab$event,NA_real_)
    write_csv_safe(tab,"11_DS_AD_loop_reactivation_stratification.csv")
  } else {
    writeLines(c(
      "No explicit loop-reactivation field was found.",
      "Loop status is NOT inferred from distance, outer-bank exposure, curvature, or near-channel flags.",
      "Use 09_DS_AD_distal_event_records.csv and 10_DS_AD_distal_events_by_interval.csv",
      "to identify candidate cutoff/abandoned-loop reactivation episodes geomorphically."),
      file.path(Output_directory,"11_DS_AD_loop_reactivation_NOTE.txt"))
  }
} else {
  writeLines(c(
    "SF->AD distal-event review file.",
    "Distal SF->AD events are exported to test whether they are genuine lateral reactivation,",
    "geometry/reference anomalies, or exceptional channel-reorganisation events."),
    file.path(Output_directory,"11_SF_AD_distal_event_review_NOTE.txt"))
}


# [DIAG-38] Raster figure export of spline response and uncertainty.
# Figures are descriptive model visualisations; their relative hazards are
# referenced to distance zero using the fitted, capped distance response.
plot_curve <- function(curve,title_txt,fn) {
  if (is.null(curve) || !nrow(curve)) return(invisible(NULL))
  png(file.path(Output_directory,fn),width=Plot_width,height=Plot_height,units="in",res=180)
  plot(curve$distance,curve$relative_hazard_vs_zero,type="l",lwd=2,xlab="Distance",ylab="Relative hazard (distance 0 = 1)",main=title_txt)
  lines(curve$distance,curve$rh_lcl95,lty=2); lines(curve$distance,curve$rh_ucl95,lty=2); abline(h=1,lty=3); dev.off()
}
plot_curve(fm$curve,paste0(transition_label,": margin-distance spline response"),"Figure_01_margin_distance_response.png")
plot_curve(fc$curve,paste0(transition_label,": centreline-distance spline response"),"Figure_02_centreline_distance_response.png")

# [DIAG-39] Observed event-distance ECDFs for two geometrical references.
# Event distributions alone do not normalise by the population at risk.
png(file.path(Output_directory,"Figure_03_event_distance_ECDF_comparison.png"),width=Plot_width,height=Plot_height,units="in",res=180)
plot(ecdf(x$margin_distance[x$event==1]),do.points=FALSE,verticals=TRUE,xlab="Distance",ylab="Cumulative proportion of events",main=paste0(transition_label,": event-distance ECDF"))
lines(ecdf(x$centreline_distance[x$event==1]),lty=2)
legend("bottomright",legend=c(paste0("Margin: ",margin_f),paste0("Centreline: ",centre_f)),lty=c(1,2),bty="n")
abline(h=c(.5,.75,.9,.95),lty=3); dev.off()

# [DIAG-40] Final diagnostic interpretation and completion marker.
# Best AIC identifies an in-sample distance response form, not proof that the
# same form will predict held-out intervals or transfer to another river.
# Use the distal-tail/interval outputs before treating outliers as new mechanisms.
# 12_diagnostic_summary.txt describes the decision logic; 00_RUN_COMPLETED.txt
# records that the script reached its normal completion statement.
# No archive comment changes the original output filenames or their content.
best <- if (any(is.finite(comparison$AIC))) comparison[which.min(comparison$AIC),] else comparison[1,]
writeLines(c("FRAF Step 3B — Distance-Response Diagnostic v1.4.1 — v17.10.13 aligned","================================================",
  paste("Model:",model_key),paste("Transition:",transition_label),paste("Reach:",reach_key),
  paste("Risk-set rows:",nrow(x)),paste("Events:",sum(x$event)),paste("Margin-distance field:",margin_f),
  paste("Centreline-distance field:",centre_f),
  paste("v17.10.13 time basis: predictors for (y1, y2] use geometry at interval start y1"),
  paste("v17.10.13 local Mamore note: *_PREV geometry is matched to y1; PREV denotes lookup/history source"),
  paste("Best distance model by global AIC:",best$distance_reference,"/",best$response_form),"",
  "Decision logic:","1. Compare margin vs centreline using AIC, empirical event rates, nonlinearity and PH tests.",
  "2. Do not narrow susceptibility bands solely to resemble one annual erosion footprint.",
  "3. Inspect distal-tail concentration by interval for BOTH SF->AD and DS->AD before changing the distance form.",
  "4. For DS->AD, test whether distal concentration reflects a distinct cutoff/abandoned-loop reactivation mechanism.",
  "5. Loop reactivation is only classified from an explicit source field; otherwise candidate distal episodes are exported for review."),
  file.path(Output_directory,"12_diagnostic_summary.txt"))
writeLines(c("completed=TRUE",paste0("model=",model_key),paste0("transition=",transition_label),paste0("reach=",reach_key),
  paste0("risk_rows=",nrow(x)),paste0("events=",sum(x$event)),paste0("best_distance_reference=",best$distance_reference),paste0("best_response_form=",best$response_form)),
  file.path(Output_directory,"00_RUN_COMPLETED.txt"))
msg("[Step 3B] Complete. Outputs written to: ",Output_directory)
