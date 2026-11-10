##FRAF Floodplain Reassemblage=group
##Jamuna FP to AD - Joint source-period Cox v1.0=name
##AnalysisReadyRDS=file
##OutputFolder=folder
##RunJointPH=boolean TRUE
##RunWithinPeriodPH=boolean TRUE
##SaveCompactModels=boolean TRUE

# ARCHIVE IDENTITY — FRAF Paper 2, Stage 06F: Jamuna FP->AD source-by-period Cox.
# Original delivered file: FRAF_Jamuna_FP_AD_Joint_Piecewise_Cox_v1_0.rsx.
# This archive version adds comments only; original R statements, data contracts,
# Processing parameters, model formulas, QA guards, and output names are intact.
# The historical model supports S5 Tables S21–S22, conditional on matching the
# published numerical cells with the relevant completed run CSVs.
# This is neither the September four-transition model (06/07) nor the October
# held-out broad FP->AD P1/P2 source-comparison forecasts (07P).
# Source contrast here means a comparison of distance SLOPES, not a source HR.
# The archived source README is retained separately in the ZIP package.
# Jamuna FP->AD joint source-and-period Cox (historical, non-forecast).
# Uses the authoritative fully adjudicated T1-defined binary risk population,
# with the corrected NOMINAL-T1 ACTIVE distance stored in the upstream RDS.
# Same pre-registered elapsed-time boundaries as the preceding PH triage.
# Two nested models have IDENTICAL source x period baseline hazard strata:
#   Reference: two source-specific slopes that do not vary with epoch.
#   Joint:     six source-specific slopes (SF/PRE x Early/Middle/Late).
# Primary formal test is an across-PLACE cluster-ROBUST 4-df Wald contrast
# of the four extra temporal distance coefficients. LRT is descriptive ONLY.
# No SOURCE hazard ratio is estimated: SOURCE is a baseline stratum.
# This is not a calibrated forecast and does not alter spatial inputs.
# Validated only against static source/output logic here, not run on Windows R.

# RUNTIME DEPENDENCY.
# Requires R (QGIS R Processing provider) and survival. The analysis-ready RDS
# is generated upstream by Jamuna historical FP->AD v1.0.1; this script does
# not read or rebuild raw channel polygons, the EA grid, or floodplain states.
suppressPackageStartupMessages({
  if (!requireNamespace('survival', quietly=TRUE)) stop('R package survival is required')
  library(survival)
})

# INPUT URI NORMALISATION.
# Remove any QGIS |layername suffix from the file parameter before readRDS().
# No geometry operations or external data modifications occur here.
pfile <- function(x) sub('\\|.*$', '', as.character(x)[1L])
# SCIENTIFIC INPUT CONTRACT.
# AnalysisReadyRDS must contain the authoritative original T1-defined binary
# FP->AD eligible cohort (including eligible pre-existing FP and SF; excluding
# DS). The historical cohort is not a separate organisational state.
infile <- pfile(AnalysisReadyRDS)
root <- as.character(OutputFolder)[1L]
if (!file.exists(infile)) stop('Input RDS does not exist: ', infile)
if (is.na(root) || !nzchar(trimws(root))) stop('Provide OutputFolder')
dir.create(root, recursive=TRUE, showWarnings=FALSE)
# RUN FOLDER.
# Retain the original timestamped output-directory naming for direct lineage
# matching to the successful 2026-10-16T11:21:27 run and its completed record.
out <- file.path(root, paste0('Jamuna_FP_AD_Joint_Piecewise_Cox_v1_0_',
                              format(Sys.time(),'%Y%m%dT%H%M%S')))
if (!dir.create(out, recursive=TRUE, showWarnings=FALSE)) stop('Unable to create output directory')
write.csv(data.frame(input=infile,output=out,started=as.character(Sys.time())),
          file.path(out,'00_input_provenance.csv'),row.names=FALSE)
# PROVENANCE: run start.
# The file records the exact validated analysis-ready RDS used for the fit.
# The corresponding completed-run record is emitted only after all core work.
writeLines(c('STARTED',as.character(Sys.time()),infile),file.path(out,'00_RUN_STARTED.txt'))
# CSV EXPORT HELPER.
# Output files have fixed names that are cross-referenced in Table S1 and the
# run archive. Writing CSVs does not alter the analysis input RDS.
put <- function(x,nm) {
  utils::write.csv(as.data.frame(x), file.path(out,nm),row.names=FALSE,na='')
}
# CONDITION CAPTURE.
# Collect numerical or convergence warnings as strings, preserving diagnostic
# information rather than letting R discard messages in batch execution.
getwarnings <- function(expr) {
  warn <- character()
  result <- withCallingHandlers(expr,warning=function(w){
    warn <<- unique(c(warn,conditionMessage(w)))
    invokeRestart('muffleWarning')
  })
  list(value=result,warnings=warn)
}
# HISTORICAL COX FITTING.
# All models use Efron tie handling and a 65-iteration limit. Clustered robust
# variance is supplied through cluster(PLACE_ID) in model formulas; for PH
# screens, store model/x/y components so cox.zph can reconstruct fit inputs.
# Reject nonfinite coefficients, robust covariances or log likelihood.
fit_model <- function(form,df,for_ph=FALSE){
  warns <- character()
  fit <- tryCatch(withCallingHandlers(
    survival::coxph(form, data=df, ties='efron',
      x=isTRUE(for_ph), y=isTRUE(for_ph), model=isTRUE(for_ph),
      control=survival::coxph.control(iter.max=65)),
    warning=function(w){
      warns <<- unique(c(warns,conditionMessage(w)))
      invokeRestart('muffleWarning')
    }),error=function(e)e)
  if(inherits(fit,'error')) stop('Cox fitting error: ',conditionMessage(fit))
  b <- stats::coef(fit)
  V <- stats::vcov(fit)
  if(anyNA(b) || any(!is.finite(b)) || any(!is.finite(V)) ||
     !is.finite(fit$loglik[length(fit$loglik)]))
    stop('Cox returned nonfinite estimates or likelihood')
  if(any(!is.finite(diag(V))) || any(diag(V)<=0))
    stop('Nonpositive or nonfinite robust-variance diagonal')
  list(fit=fit,warnings=warns)
}
# COEFFICIENT EXPORT.
# Each beta is a log-hazard slope per one unit increase of log1p(distance_km),
# not a per-metre slope. Robust 95% intervals use beta +/- 1.96 robust SE.
# exp(beta) is a scale-specific relative hazard multiplier, not a source HR.
coefficients <- function(fit,model_name){
  b<-stats::coef(fit);V<-stats::vcov(fit)
  se<-sqrt(diag(V))
  data.frame(model=model_name,term=names(b),beta=as.numeric(b),
             robust_se=as.numeric(se),
             lower_95=as.numeric(b-1.96*se),upper_95=as.numeric(b+1.96*se),
             HR_per_unit_log1p_km=exp(as.numeric(b)),stringsAsFactors=FALSE)
}
# CLUSTER-ROBUST WALD TESTS.
# Contrast matrices act on the estimated six slopes and the PLACE_ID-robust
# covariance matrix. Return NA with a diagnostic status if singular; never
# substitute an unclustered likelihood ratio as the primary inference.
wald <- function(b,V,C,label){
  C<-as.matrix(C)
  if(ncol(C)!=length(b))stop('Wald contrast does not match coefficient vector')
  est<-as.numeric(C %*% b)
  covar<-C %*% V %*% t(C)
  stat<-tryCatch(as.numeric(t(est)%*%solve(covar,est)),error=function(e)NA_real_)
  df<-nrow(C)
  data.frame(test=label,df=df,robust_wald_chisq=stat,
    robust_p=if(is.finite(stat))stats::pchisq(stat,df,lower.tail=FALSE) else NA_real_,
    status=if(is.finite(stat))'OK' else 'ROBUST_CONTRAST_SINGULAR',
    stringsAsFactors=FALSE)
}
# COMPACT MODEL SERIALISATION.
# Drop large row-level prediction vectors and design matrices before saving
# fitted Cox objects; this manages archive size without refitting the models.
clean_fit <- function(fit){
  fit$model <- NULL
  fit$x <- NULL
  fit$y <- NULL
  fit$linear.predictors <- NULL  # remove large in-sample row vector
  fit$residuals <- NULL
  fit$weights <- NULL
  fit
}
# PROPORTIONAL-HAZARDS DIAGNOSTIC.
# Schoenfeld-residual screens use identity-time transformation. Unlike the
# cluster-robust Wald comparisons, cox.zph diagnostics are not spatially
# cluster-robust tests; failure restricts constant-slope interpretation.
# Failed numerical PH calculations are recorded as QA rather than fatal error.
ph_report <- function(fit,prefix){
  # cox.zph is a Schoenfeld PH screening diagnostic; it is not a
  # spatially cluster-robust hypothesis test, unlike Wald tests above.
  warnings<-character()
  ph<-tryCatch(withCallingHandlers(survival::cox.zph(fit,transform='identity'),
    warning=function(w){warnings<<-unique(c(warnings,conditionMessage(w)));
                         invokeRestart('muffleWarning')}),error=function(e)e)
  if(inherits(ph,'error')){
    put(data.frame(term='PH_UNAVAILABLE',chisq=NA_real_,df=NA_real_,p=NA_real_,
      status=conditionMessage(ph),warnings=paste(warnings,collapse=' | ')),
      paste0(prefix,'_PH.csv'))
    return(invisible(FALSE))
  }
  tab<-as.data.frame(ph$table)
  put(data.frame(term=rownames(tab),chisq=tab$chisq,df=tab$df,p=tab$p,
      status='NUMERIC_PH_TEST',warnings=paste(warnings,collapse=' | ')),
      paste0(prefix,'_PH.csv'))
  capture.output(print(ph),file=file.path(out,paste0(prefix,'_PH.txt')))
  invisible(TRUE)
}

# MAIN HISTORICAL RUN (READ-ONLY INPUT; NEW OUTPUT DIRECTORY).
# Stop on invalid source data, missing covariates, changed event totals,
# nonconservative time splitting or a model-estimation failure.
tryCatch({
# LOAD PREVALIDATED BINARY OBSERVATIONS.
# Use the RDS from Final Historic v1.0.1 rather than older risk table versions.
# The source RDS contains original T1 eligibility and nominal-T1 distance.
  d <- readRDS(infile)
# MINIMUM MODEL FIELDS.
# TSTART/TSTOP: absolute elapsed observation years; EVENT: adjudicated FP->AD.
# SRC: antecedent source class; SRC_PRE: pre-existing-FP indicator;
# PLACE_ID: recurrence clustering key; Z: log1p(T1 distance metres / 1000).
  required <- c('TSTART','TSTOP','EVENT','SRC','SRC_PRE','PLACE_ID','Z')
  missing <- setdiff(required,names(d))
  if(length(missing)) stop('Analysis RDS missing fields: ',paste(missing,collapse=', '))
# FROZEN COHORT GUARD.
# The 1,585,497-row total is a scientific input invariant. The script fails
# rather than silently fitting a different eligible population.
  if(nrow(d)!=1585497L) stop('Unexpected T1 binary population: ',nrow(d))
  # Keep only the seven validated necessary fields (avoid old diagnostics
  # or out-of-model T2 columns contaminating fitting or memory consumption).
  d <- as.data.frame(d[,required,drop=FALSE],stringsAsFactors=FALSE)
# COMPLETE-CASE AND TIME VALIDITY.
# Missing or nonfinite predictors, nonpositive observation durations and
# invalid event/source indicators are hard errors, not implicit omissions.
  if(anyNA(d) || any(!is.finite(d$TSTART)) || any(!is.finite(d$TSTOP)) ||
     any(!is.finite(d$Z)) || any(d$TSTOP<=d$TSTART) ||
     any(!d$EVENT %in% c(0L,1L)) || any(!d$SRC_PRE %in% c(0L,1L)) ||
     any(!nzchar(as.character(d$PLACE_ID))))
    stop('Missing or invalid field in the validated risk population')
  d$SRC_PRE<-as.integer(d$SRC_PRE)
  d$EVENT<-as.integer(d$EVENT)
  d$PLACE_ID<-as.character(d$PLACE_ID)
  d$SRC<-as.character(d$SRC)
# SOURCE SEMANTICS.
# The only eligible FP provenance sources are STABILISED_FLOODPLAIN and
# PREEXISTING_FLOODPLAIN. Depositional Storage is excluded from broad FP.
# The binary flag is reconciled with the categorical source on every row.
  if(any(!d$SRC %in% c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN')) ||
     any(d$SRC_PRE != as.integer(d$SRC=='PREEXISTING_FLOODPLAIN')))
    stop('Incorrect source provenance or source flag')
# AUTHORITATIVE OUTCOME AND SOURCE SUPPORT.
# Expect exactly 14,391 FP->AD events: 13,234 from pre-existing FP and
# 1,157 from SF. These totals are checked before any temporal splitting.
  if(sum(d$EVENT)!=14391L ||
     sum(d$EVENT==1L & d$SRC_PRE==1L)!=13234L ||
     sum(d$EVENT==1L & d$SRC_PRE==0L)!=1157L)
    stop('Authoritative 14391 events or source assignment changed')
# ELAPSED-TIME SUPPORT.
# Count exposure on the original interval-specific start/stop times, not as
# a fixed number of equally spaced annual samples; retain uneven gaps.
  all_time <- sum(d$TSTOP-d$TSTART)
  min_time <- min(d$TSTART)
  max_time <- max(d$TSTOP)
# FROZEN PERIOD CUTPOINTS.
# Early/Middle/Late boundaries are 12.342 and 24.683 elapsed years (Jamuna).
# These cutpoints were selected from the historical record, not a held-out
# forecast design; model coefficients remain record-conditional associations.
  bnds <- c(min_time,12.342,24.683,max_time)
  if(!(min_time<12.342 && 12.342<24.683 && 24.683<max_time))
    stop('Period cutpoints do not lie strictly inside observation time support')
  era <- c('EARLY','MIDDLE','LATE')
# SIX SOURCE x PERIOD BASELINE STRATA.
# Separate SF and pre-existing FP baseline hazards in each of three periods.
# Both reference and joint models will have these exact six strata.
  strata_names <- c('SF_EARLY','PRE_EARLY','SF_MIDDLE','PRE_MIDDLE','SF_LATE','PRE_LATE')
  nn <- nrow(d)
# SPLIT-INTEGRITY TRACKERS.
# Accumulate per-original-row exposure and event counts across period cuts;
# these arrays detect any duplicated event or lost risk time during splitting.
  copied_exposure <- numeric(nn)
  copied_events <- integer(nn)
  segments <- vector('list',3L)
  support <- list()
# TIME SPLITTING.
# Split only intervals crossing a frozen period boundary. Carry the original
# T1 distance, source and place identity forward unchanged to all segments.
  for(k in seq_along(era)){
    lo<-bnds[k];hi<-bnds[k+1L]
# OVERLAP RULE.
# Retain observations with strictly positive duration inside this period;
# intersections are computed on continuous start/stop times.
    ix<-which(d$TSTART<hi & d$TSTOP>lo)
    s<-d[ix,c('TSTART','TSTOP','EVENT','PLACE_ID','SRC_PRE','Z'),drop=FALSE]
    true_stop<-s$TSTOP
    s$TSTART<-pmax(s$TSTART,lo)
    s$TSTOP<-pmin(s$TSTOP,hi)
    if(any(s$TSTOP<=s$TSTART))stop('Invalid split time in ',era[k])
# BOUNDARY EVENT ALLOCATION.
# An event belongs to the segment ending at the event's observed TSTOP.
# If that time equals an epoch boundary, it is assigned to the earlier epoch.
    s$EVENT<-as.integer(s$EVENT==1L & true_stop<=hi)
    copied_exposure[ix]<-copied_exposure[ix]+s$TSTOP-s$TSTART
    copied_events[ix]<-copied_events[ix]+s$EVENT
# SOURCE-PERIOD INDICATOR.
# Each split observation belongs to exactly one of six strata; the baseline
# for a stratum is allowed to differ independently from every other stratum.
    s$SRC_PERIOD<-factor(ifelse(s$SRC_PRE==1L,paste0('PRE_',era[k]),
                                               paste0('SF_',era[k])),
                          levels=strata_names)
    # Keep era label only for QA; no date/outcome-derived predictor is added.
    s$PERIOD<-era[k]
# SOURCE-PERIOD EXPOSURE REPORT.
# Counts, event support, place-years, and unique places are emitted for each
# source-period combination to assess sparse-event limitations.
    for(pre in c(0L,1L)){
      at<-s$SRC_PRE==pre
      support[[length(support)+1L]]<-data.frame(
        period=era[k],period_start=lo,period_end=hi,
        source=if(pre==0L)'STABILISED_FLOODPLAIN' else 'PREEXISTING_FLOODPLAIN',
        split_risk_intervals=sum(at),events=sum(s$EVENT[at]),
        place_years=sum(s$TSTOP[at]-s$TSTART[at]),
        unique_places=length(unique(s$PLACE_ID[at])))
    }
    segments[[k]]<-s
    message('[Jamuna joint] ',era[k],': ',nrow(s),' risk intervals; ',sum(s$EVENT),' events')
    rm(s,ix,true_stop);invisible(gc(FALSE))
  }
# EVENT AND PLACE-TIME CONSERVATION.
# Time splitting must reproduce exactly the original event indicators and
# original observation exposure for each row, within numerical tolerance.
  total_split_events<-sum(copied_events)
  max_dur_error<-max(abs(copied_exposure-(d$TSTOP-d$TSTART)))
  n_bad_events<-sum(copied_events!=d$EVENT)
  original_events<-sum(d$EVENT)
  split_time<-sum(copied_exposure)
  split_row_count<-sum(vapply(segments,nrow,integer(1)))
  qa<-data.frame(check=c('original_rows','split_rows','original_events','split_events',
       'rows_with_event_mismatch','max_per_row_exposure_error_yr',
       'original_total_place_years','split_total_place_years','difference_place_years',
       'source_PRE_events','source_SF_events','period_cut_1','period_cut_2'),
       value=as.character(c(nn,split_row_count,original_events,total_split_events,
         n_bad_events,max_dur_error,all_time,split_time,split_time-all_time,
         13234,1157,12.342,24.683)))
# REPRODUCIBILITY OUTPUT.
# 01_population_and_split_integrity.csv provides row/event/exposure checks
# that should be retained with the published run for verification.
  put(qa,'01_population_and_split_integrity.csv')
  support_df<-do.call(rbind,support)
# SUPPORT OUTPUT.
# The six risk populations and event denominators accompany the coefficients;
# this matters when discussing sparse SF and late pre-existing-FP periods.
  put(support_df,'02_source_period_support.csv')
  # Exact reproduction of successfully audited period/source support from
  # Jamuna PH Temporal Triage v1.0.1 (16 Oct 2026).
# HISTORICAL SUPPORT REPRODUCTION.
# The pre-audited source-period interval and event totals are enforced exactly,
# preventing a nominally successful but population-mismatched refit.
  expected_support_intervals<-c(494854L,92498L,491156L,15756L,575016L,1593L)
  expected_support_events<-c(340L,10960L,97L,1898L,720L,376L)
  if(!identical(as.integer(support_df$split_risk_intervals),expected_support_intervals) ||
     !identical(as.integer(support_df$events),expected_support_events))
    stop('Time-split source/epoch support differs from audited PH triage; investigate before fitting')
# STRICT TIME-SPLIT ACCEPTANCE.
# Any event mismatch or significant place-time discrepancy is fatal: the
# resulting Cox comparison must not be interpreted on a changed risk set.
  if(original_events!=14391L || total_split_events!=14391L || n_bad_events!=0L ||
     max_dur_error>1e-8 || abs(all_time-split_time)>0.001)
    stop('Event or person-time preservation failed. See 01_population_and_split_integrity.csv')
  rm(d,copied_exposure,copied_events,support);invisible(gc(FALSE))
# ASSEMBLE MODEL FRAME.
# Bind the three split period tables. The expanded split-row count is larger
# than the 1,585,497 original place-interval rows, but neither exposure nor
# event totals may change (successful run reports 1,670,873 split rows).
  q<-do.call(rbind,segments)
  rownames(q)<-NULL
  rm(segments);invisible(gc(FALSE))
  if(anyNA(q)||nrow(q)!=split_row_count || sum(q$EVENT)!=14391L)
    stop('Post-split data failure')
  if(!identical(levels(q$SRC_PERIOD),strata_names))
    stop('Source-period factor levels changed after bind')
  # Columns are zero outside their own source x period stratum.  Therefore
  # slopes are directly interpretable for that stratum, not an extrapolated
  # comparison of baseline hazards across fundamentally different sources.
# STRATUM-ACTIVE DESIGN COLUMNS.
# The six joint predictors equal Z only within their corresponding source
# and period; otherwise they are zero. They are distinct coefficient slopes,
# not separate source hazard ratios.
  for(lev in strata_names){
    nm<-paste0('Z_',lev)
    q[[nm]]<-ifelse(q$SRC_PERIOD==lev,q$Z,0)
  }
# REFERENCE DESIGN.
# The reference Cox model shares one SF distance slope across periods and
# one pre-existing-FP distance slope across periods, while baselines vary.
  q$Z_SF<-ifelse(q$SRC_PRE==0L,q$Z,0)
  q$Z_PRE<-ifelse(q$SRC_PRE==1L,q$Z,0)
  rm(lev,nm);invisible(gc(FALSE))
  message('[Jamuna joint] Fully matched population and time split. Fit common two-slope reference.')
# REFERENCE COX MODEL.
# Absolute elapsed counting-process time, two source-specific distance slopes,
# all six baseline strata, Efron event ties and PLACE_ID clustered uncertainty.
  form_ref<-survival::Surv(TSTART,TSTOP,EVENT) ~ Z_SF + Z_PRE +
    strata(SRC_PERIOD) + cluster(PLACE_ID)
# REFERENCE FIT AND FINITE-FIT CHECK.
# The matching reference is essential: both model alternatives must differ
# only in temporal slope flexibility, not baselines or risk eligibility.
  rr<-fit_model(form_ref,q,for_ph=FALSE)
  ref<-rr$fit
  if(ref$n!=nrow(q) || ref$nevent!=14391L) stop('Reference Cox unexpectedly dropped risk rows/events')
  ref_coef<-coefficients(ref,'SOURCE_SLOPES_CONSTANT_BY_PERIOD')
# REFERENCE RESULTS.
# Keep two-slope coefficients for the nested source-by-period model comparison;
# these are not by themselves the six published historical period slopes.
  put(ref_coef,'10_reference_source_coefficients.csv')
  ref_loglik<-as.numeric(tail(ref$loglik,1L))
  ref_status<-if(length(rr$warnings))'WARNINGS_REVIEW' else 'FINITE'
  ref_warnings<-paste(rr$warnings,collapse=' | ')
  if(isTRUE(SaveCompactModels))saveRDS(clean_fit(ref),file.path(out,'40_reference_source_slopes_compact.rds'))
  rm(rr,ref);invisible(gc(FALSE))

  message('[Jamuna joint] Fit six source x period distance coefficients jointly.')
# JOINT MODEL DESIGN.
# Six coefficients are estimated simultaneously using the same source x
# period baseline strata and identical split population as the reference.
  full_covars<-paste0('Z_',strata_names)
# JOINT HISTORICAL COX MODEL.
# A single survival fit estimates SF_EARLY/PRE_EARLY, SF_MIDDLE/PRE_MIDDLE
# and SF_LATE/PRE_LATE distance effects; repeated places are clustered.
  form_joint<-stats::as.formula(paste0('survival::Surv(TSTART,TSTOP,EVENT) ~ ',
    paste(full_covars,collapse=' + '),' + strata(SRC_PERIOD) + cluster(PLACE_ID)'))
# JOINT MODEL NUMERICAL INTEGRITY.
# When RunJointPH is enabled retain the model frame for Schoenfeld tests;
# normal Cox fitting uses validated, fully matched six-slope model data.
  ff<-fit_model(form_joint,q,for_ph=isTRUE(RunJointPH))
  fit<-ff$fit
  if(fit$n!=nrow(q) || fit$nevent!=14391L) stop('Joint Cox unexpectedly dropped risk rows/events')
  full_warnings<-paste(ff$warnings,collapse=' | ')
  full_status<-if(length(ff$warnings))'WARNINGS_REVIEW' else 'FINITE'
  b<-stats::coef(fit);V<-stats::vcov(fit)
# COEFFICIENT CONTRACT.
# Reject dropped, aliased or unexpected model slopes before creating tables
# or attempting historical source/temporal comparisons.
  if(!setequal(names(b),full_covars))stop('The six intended coefficients were not all estimated')
  b<-b[full_covars];V<-V[full_covars,full_covars,drop=FALSE]
  coef_tab<-coefficients(fit,'JOINT_SOURCE_PERIOD')
  coef_tab<-coef_tab[match(full_covars,coef_tab$term),,drop=FALSE]
  coef_tab$source<-rep(c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN'),3)
  coef_tab$period<-rep(era,each=2)
# TABLE S21 GENERATOR.
# This is the exact publication-relevant six-coefficient CSV: beta, robust SE,
# confidence bounds and source-period labels. Verify published numerical values
# against the CSV from the same completed run.
  put(coef_tab,'11_joint_six_source_period_coefficients.csv')

  # Contrasts include 4-df joint temporal variation within both sources,
  # 2-df variation separately by source, plus source differences within epoch.
# CONTRAST MATRIX CONSTRUCTOR.
# Map named coefficient differences into the six-term parameter vector;
# term-name verification prevents accidental exchange of SF and PRE slopes.
  makeC <- function(contrasts){
    m<-matrix(0,nrow=length(contrasts),ncol=length(b),
             dimnames=list(NULL,names(b)))
    for(i in seq_along(contrasts)){
      v<-contrasts[[i]]
      if(any(!names(v)%in%names(b)))stop('Unknown robust contrast term')
      m[i,names(v)]<-v
    }
    m
  }
# SOURCE-SPECIFIC TEMPORAL CONTRASTS.
# Compare MIDDLE/EARLY and LATE/EARLY distance coefficients separately for SF
# and pre-existing FP. Both differences jointly give a two-df test per source.
  sf_con<-list(c(Z_SF_MIDDLE=1,Z_SF_EARLY=-1),c(Z_SF_LATE=1,Z_SF_EARLY=-1))
  pre_con<-list(c(Z_PRE_MIDDLE=1,Z_PRE_EARLY=-1),c(Z_PRE_LATE=1,Z_PRE_EARLY=-1))
# PRIMARY TEMPORAL TESTS.
# The combined four-df robust Wald test assesses all four time interactions;
# two two-df tests ask whether distance effects vary within each source.
  tests<-rbind(
    wald(b,V,makeC(c(sf_con,pre_con)),'ALL_TEMPORAL_CHANGES_BOTH_SOURCES'),
    wald(b,V,makeC(sf_con),'SF_TEMPORAL_CHANGES'),
    wald(b,V,makeC(pre_con),'PRE_TEMPORAL_CHANGES'))
# WITHIN-PERIOD SOURCE-SLOPE CONTRASTS.
# These contrasts compare PRE and SF distance coefficients in each epoch;
# because baseline hazards are source stratified, no overall PRE/SF HR exists.
  for(e in era){
    src_con<-setNames(c(1,-1),c(paste0('Z_PRE_',e),paste0('Z_SF_',e)))
    tests<-rbind(tests,wald(b,V,makeC(list(src_con)),paste0('PRE_VS_SF_',e)))
  }
# TABLE S22 GENERATOR.
# Write all six robust temporal and source tests and their degrees of freedom;
# these are contrasts on distance slopes with PLACE-clustered covariance.
  put(tests,'12_robust_wald_temporal_and_source_tests.csv')
  # Interpret interaction contrasts as distance-slope differences; because
  # source baselines are stratified there is no constant PRE/SF hazard ratio.
# INDIVIDUAL TIME EFFECTS.
# Separate one-df MIDDLE-minus-EARLY and LATE-minus-EARLY contrasts supply
# confidence intervals for particular changes, complementing joint tests.
  contrasts<-list()
  for(src in c('SF','PRE')) for(e in c('MIDDLE','LATE')){
    x<-paste0('Z_',src,'_',e); z<-paste0('Z_',src,'_EARLY')
    cvec<-setNames(c(1,-1),c(x,z))
    v<-makeC(list(cvec));delta<-as.numeric(v%*%b)
    delta_se<-sqrt(as.numeric(v%*%V%*%t(v)))
    contrasts[[length(contrasts)+1L]]<-data.frame(source=src,contrast=paste(e,'MINUS EARLY'),
       beta_difference=delta,robust_se=delta_se,
       lower_95=delta-1.96*delta_se,upper_95=delta+1.96*delta_se,
       p_robust_1df=stats::pchisq((delta/delta_se)^2,1,lower.tail=FALSE))
  }
  put(do.call(rbind,contrasts),'12_individual_period_slope_contrasts.csv')
  # Precomputed previous, separately fitted epoch estimates are used ONLY
  # as a deterministic reproduction check (not a fitting constraint).
# PRIOR EPOCH-FIT REPRODUCTION CHECK.
# These six frozen values are from earlier independently fitted period models.
# The current joint model must reproduce them within 0.02; they are used as
# post-fit QA, never supplied to survival::coxph as fixed coefficients.
  prev <- c(Z_SF_EARLY=-7.98815393999036,Z_PRE_EARLY=-4.61514745322654,
            Z_SF_MIDDLE=-7.44678179232957,Z_PRE_MIDDLE=-6.93142378646330,
            Z_SF_LATE=-10.5735752419867,Z_PRE_LATE=-6.02386353583729)
  comparison<-data.frame(term=full_covars,prior_epoch_independent=prev[full_covars],
       joint_beta=as.numeric(b),joint_minus_prior=as.numeric(b-prev[full_covars]),
       within_tolerance_0_02=abs(as.numeric(b-prev[full_covars]))<0.02)
  put(comparison,'13_reconcile_with_previously_completed_epoch_fits.csv')
# INTEGRITY TOLERANCE.
# Stop rather than accept changed slope estimates when a same-stratum joint
# fit differs appreciably from previously audited period estimates.
  if(any(!comparison$within_tolerance_0_02))
    stop('Joint fit disagrees with previous epoch fits by >=0.02: inspect timing/strata before any conclusion')
# LIKELIHOOD COMPARISON, SECONDARY ONLY.
# The unclustered likelihood ratio ignores recurrence clustering; use the
# robust Wald p-value for primary temporal tests and report LRT descriptively.
  delta_ll<-2*(as.numeric(tail(fit$loglik,1))-ref_loglik)
  put(data.frame(reference='SOURCE_SLOPES_CONSTANT_BY_PERIOD',
     joint='SIX_SOURCE_PERIOD_SLOPES',reference_loglik=ref_loglik,
     joint_loglik=as.numeric(tail(fit$loglik,1)),twice_loglik_gain=delta_ll,
     nominal_extra_df=4,
     LRT_p_unclustered_descriptive_only=stats::pchisq(max(0,delta_ll),4,lower.tail=FALSE),
     robust_joint_Wald_p=tests$robust_p[1],
     caveat='Use robust Wald p for inferential contrast; likelihood-ratio p ignores shared-place dependence.'),
     '14_reference_vs_joint_comparison.csv')
# MODEL-FIT AUDIT.
# Retain warnings, log likelihoods, full split population/event counts and
# concordance. Numerical convergence is not equivalent to proportional hazards.
  put(data.frame(model=c('SOURCE_SLOPES_CONSTANT_BY_PERIOD','SIX_SOURCE_PERIOD_SLOPES'),
    source_period_baseline_strata=6L,
    n=c(nn,nn),split_rows=c(nrow(q),nrow(q)),events=c(14391L,14391L),
    convergence=c(ref_status,full_status),
    warnings=c(ref_warnings,full_warnings),
    partial_loglik=c(ref_loglik,as.numeric(tail(fit$loglik,1))),
    concordance=c(NA_real_,if(!is.null(fit$concordance))as.numeric(fit$concordance[1]) else NA_real_)),
    '15_model_fit_integrity.csv')
# JOINT PH SCREEN.
# The six-term model includes structurally zero covariate columns outside
# specific strata; numerical cox.zph interpretation requires caution.
  if(isTRUE(RunJointPH)){
    message('[Jamuna joint] Numerical joint-model PH diagnostics (plots deliberately omitted).')
    ph_report(fit,'20_joint')
  }else{
    put(data.frame(term='NOT_RUN',status='RunJointPH=FALSE'), '20_joint_PH.csv')
  }
  # Compute baseline hazard while full fitted frame is present. Baseline
  # is stratified by SOURCE x PERIOD. Never treat it as a calibrated forecast.
# ESTIMATED HISTORICAL BASELINES.
# Save source x epoch cumulative baseline hazard only as retrospective model
# output. These baselines are not calibrated held-out susceptibility forecasts.
  base<-tryCatch(survival::basehaz(fit,centered=FALSE),error=function(e)e)
  if(inherits(base,'error')){
    put(data.frame(status='NOT_AVAILABLE',message=conditionMessage(base)),
        '31_baseline_hazard_QA.csv')
  }else{
    put(base,'31_source_period_baseline_cumulative_hazard.csv')
    put(data.frame(status='OK',nrows=nrow(base)), '31_baseline_hazard_QA.csv')
  }
# COMPACT JOINT MODEL ARCHIVE.
# Store a reduced fitted survival object when requested; the scientific
# specification and coefficients are also preserved in human-readable files.
  if(isTRUE(SaveCompactModels)){
    saveRDS(clean_fit(fit),file.path(out,'40_joint_piecewise_cox_compact.rds'))
  }
  rm(fit,ff,base);invisible(gc(FALSE))

  # Independent within-period PH SCREEN (not a second model search):
  # slopes are unchanged. This isolates residual time trend within each
  # epoch, where the joint numerical test may be hard to interpret because
  # many covariates are structurally zero outside their own strata.
# SIX WITHIN-STRATUM PH SCREENS.
# Refit each source-period separately only to assess residual time trends;
# these diagnostics do not reselect the published joint six-slope model.
  if(isTRUE(RunWithinPeriodPH)){
    message('[Jamuna joint] Within source x period PH screens (six tests)')
    rows<-list()
    for(lev in strata_names){
# DIAGNOSTIC DATA SLICE.
# Use the correct observed time/risk segment for one source-period at a time;
# exclude irrelevant zero-coded coefficients used in the joint design.
      sub<-q[q$SRC_PERIOD==lev,c('TSTART','TSTOP','EVENT','Z','PLACE_ID'),drop=FALSE]
      sub_fit<-tryCatch(fit_model(
        survival::Surv(TSTART,TSTOP,EVENT)~ Z+cluster(PLACE_ID),
        sub,for_ph=TRUE),error=function(e)e)
      if(inherits(sub_fit,'error')){
        rows[[length(rows)+1L]]<-data.frame(source_period=lev,n=nrow(sub),
           events=sum(sub$EVENT),chisq=NA_real_,p=NA_real_,
           status=paste0('FIT_ERROR: ',conditionMessage(sub_fit)))
      }else{
# PH DIAGNOSTIC FAILURE HANDLING.
# Record failed within-stratum tests explicitly rather than converting them
# to apparent non-significant tests; PH tests are not a fit-selection oracle.
        ph<-tryCatch(survival::cox.zph(sub_fit$fit,transform='identity'),error=function(e)e)
        if(inherits(ph,'error')){
          rows[[length(rows)+1L]]<-data.frame(source_period=lev,n=nrow(sub),
            events=sum(sub$EVENT),chisq=NA_real_,p=NA_real_,
            status=paste0('PH_ERROR: ',conditionMessage(ph)))
        }else{
          rows[[length(rows)+1L]]<-data.frame(source_period=lev,n=nrow(sub),
            events=sum(sub$EVENT),chisq=as.numeric(ph$table['Z','chisq']),
            p=as.numeric(ph$table['Z','p']),status='NUMERIC_PH_SCREEN')
        }
        rm(ph,sub_fit)
      }
      rm(sub);invisible(gc(FALSE))
    }
    put(do.call(rbind,rows),'21_within_source_period_PH.csv')
  }
# FROZEN SCIENTIFIC SPECIFICATION.
# 90_frozen_scientific_specification.csv records the exact population,
# log-distance transform, fixed periods, baseline strata and clustering
# used for the completed historical model, distinct from forecasting specs.
  put(data.frame(parameter=c('transition','river','risk','endpoint','distance',
      'boundary_1','boundary_2','period_type','source_baseline','cluster',
      'ties','event_allocation','hypothesis','model_use'),
      value=c('FP_to_AD','Jamuna','All T1 eligible, 1585497 binary rows',
      'Original authoritative events; adjudicated non-events',
      'Z=log1p(DIST_ACTIVE_CURR_m/1000), antecedent nominal T1',
      '12.342 elapsed years','24.683 elapsed years',
      'source-period-specific absolute elapsed-time baseline',
      'Separate source x epoch baselines','PLACE_ID robust','Efron',
      'Event at boundary allocated to interval ending at boundary',
      '4-df robust Wald: do distance slopes vary among periods?',
      'Historical inferential model only; no rolling prediction verification')),
      '90_frozen_scientific_specification.csv')
# SUCCESS RECORD AND RUN MATCH.
# The run status is written only at completion and includes model totals,
# cutpoints, robust Wald p, and guarantees that original geometry and event
# eligibility were unmodified. The supplied 16 Oct 2026 record reproduces
# this completion text exactly (including p=6.16798e-33).
  writeLines(c('COMPLETED',as.character(Sys.time()),
    'Input RDS fully validated: 1,585,497 original T1 risk rows; 14,391 authoritative events.',
    paste('Expanded split rows:',nrow(q)),'Epoch cutpoints: 12.342 / 24.683 years.',
    paste('Joint robust Wald temporal p:',format(tests$robust_p[1],digits=6)),
    'Both reference and joint model used identical six source x epoch baseline strata.',
    'Historical source-specific gradients only. No source HR, no predictive calibration.',
    'PH screens are numerical, separate from cluster-robust slope-contrast tests.',
    'No geometry, eligibility, source event, or T1 distance modified.'),
    file.path(out,'00_RUN_COMPLETED.txt'))
  message('[Jamuna joint] COMPLETED: ',out)
# FAILURE PROVENANCE.
# On error, leave already written diagnostic CSVs in the output directory,
# add 00_RUN_FAILED.txt, then rethrow the error; a partial run must not be
# mistaken for a completed publication result.
},error=function(e){
  writeLines(c('FAILED',as.character(Sys.time()),conditionMessage(e),
      'Previously written CSVs remain in the output directory.'),
      file.path(out,'00_RUN_FAILED.txt'))
  stop(e)
})
