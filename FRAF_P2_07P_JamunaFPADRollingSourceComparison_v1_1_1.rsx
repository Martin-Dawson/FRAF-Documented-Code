##FRAF Floodplain Reassemblage=group
##Jamuna FP to AD - Final rolling prediction P1 P2 v1.1.1 baseline fix=name
##AnalysisReadyRDS=file
##OutputFolder=folder
##ForecastOrigins=string 25,30,35
##WriteQGISForecastCSVs=boolean TRUE
##WriteCombinedPredictionGZ=boolean TRUE
##MinimumTrainingEvents=number 20
# ===========================================================================
# FRAF PAPER 2 — PUBLICATION SOURCE ARCHIVE (COMMENT-ONLY ANNOTATION)
# Archived filename : FRAF_P2_07P_JamunaFPADRollingSourceComparison_v1_1_1.rsx
# Original source   : FRAF_Jamuna_FP_AD_Final_Rolling_Prediction_Source_Comparison_v1_1_1.rsx
# River / analysis : Jamuna broad eligible FP -> AD; matched rolling P1 versus P2
# Archive stage    : 07P — supplementary October rolling-origin source comparison
# Publication use  : S7 Tables S15c–S15e; prediction rows for S8/S9 mapping
# Related core    : Stage 07 v17.10.15.1 state-transition forecasts; separate run
#
# Broad FP is an eligibility-defined prediction population containing eligible
# pre-existing floodplain plus Stabilised Floodplain (SF); it EXCLUDES
# Depositional Storage (DS). FP is not a fourth organisational state.
# P1: interval-start AD-margin log-distance only.
# P2: P1 plus interval-start antecedent source and source x distance slope.
# Both models are evaluated on matched held-out origins T25/T30/T35.
# Forecast baselines and normalisation are learned from training rows only.
# No claims of spatially independent validation or prospective corridor
# definition are made; separate QGIS scripts perform polygon verification.
# QGIS Processing `##` directives, R calculations, schema, output filenames,
# field names and computational control flow are kept EXACTLY as supplied.
# No automated R/QGIS execution is asserted by this archival annotation.
# ===========================================================================


# Jamuna FP -> AD rolling prediction, v1.1.1 (2026-10-16).
# Fix: explicit less-than comparison of successive baseline hazard increments.
# Former `diff(bv$hazard)<-1e-9` was parsed by R as assignment to diff() (`diff<-`).
# Fix: use equivalent Surv(DUR,EVENT) instead of Surv(0,DUR,EVENT),
# fit via coxph.fit not agreg.fit, and source-orthogonal centering for P2.
# Numerical instability is never suppressed via arbitrary coefficient clipping.
# Failure writes origin/model diagnostics and stops; no penalised/changed model silently substituted.
# R 4.6; QGIS R Processing provider; survival dependency.
# Reads ONLY the completed validated T1-defined RDS from historical Cox v1.0.1.
# P1: distance-only; P2: distance + initial-source main effect and distance interaction.
# P1/P2 use identical held-out test rows, but each has a separate TRAIN-ONLY fit,
# TRAIN-ONLY Z scale and TRAIN-ONLY Cox gap-time baseline hazard.
# IMPORTANT: source is a known T1 covariate, never a T2 outcome or historic full union.
# Historical six-coefficient (full-record) model is NOT used in forecasting.
# Frozen scope: 35 original valid interval-start ranks, T25/30/35; gap time,
# no interpolation, Efron ties, cluster(PLACE_ID) robust SE, current T1 Z.
# Forecast is RETROSPECTIVE: the fixed spatial analysis corridor is itself
# constructed retrospectively; no claim of operational prospectiveness.
# No original GeoPackage, geometry, RDS, state or event fields are rewritten.

# DEPENDENCY CHECK — `survival` supplies Cox fitting, baseline hazard and Surv().
# The script runs through the QGIS R Processing provider; it is not a standalone
# QGIS polygon-processing algorithm and does not modify the risk-source files.
suppressPackageStartupMessages({
  if (!requireNamespace('survival', quietly=TRUE)) stop('The R package survival is required')
  library(survival)
})
# Use stable character handling and limit scientific-notation formatting in exports.
options(stringsAsFactors=FALSE, scipen=99)
# Coerce numeric inputs without emitting conversion warnings; downstream checks must reject
# missing/non-finite values before a fitted model or forecast is accepted.
number <- function(x) suppressWarnings(as.numeric(x))
# Treat only literal TRUE as an enabled QGIS Processing option.
flag <- function(x) isTRUE(x)
# Remove a QGIS provider layer suffix (\|...) from a selected input path.
path_input <- function(x) sub('\\|.*$', '', as.character(x)[1L])
# Write a plain, UTF-8-compatible CSV under this run's newly created output folder.
# The global `out` variable is established before these helpers are called.
writing <- function(d, name) {
  utils::write.csv(as.data.frame(d), file.path(out, name), row.names=FALSE, na='')
}
# Write status/manifest text files to the run directory, preserving source paths.
write_text <- function(x, nm) writeLines(x, file.path(out, nm), useBytes=TRUE)
# Stop immediately on a failed invariant rather than proceeding with an altered population.
fail <- function(...) stop(paste(..., collapse=''))
# Define a tolerance-based finite scalar comparison helper (retained from source).
scalar_equal <- function(x,y,tol=1e-8) is.finite(x) && is.finite(y) && abs(x-y)<tol

# Exact binary-discrimination metrics; average precision handles tied scores
# as one threshold (i.e. no arbitrary order within identical predicted scores).
# Compute the empirical ROC AUC using average ranks for tied predicted scores.
# AUC is undefined when the scored subset contains only events or only non-events.
auc_score <- function(y,p) {
  ok <- is.finite(p) & !is.na(y)
  y <- y[ok]; p<-p[ok]; n1<-sum(y==1L); n0<-sum(y==0L)
  if (!n1 || !n0) return(NA_real_)
  r <- rank(p, ties.method='average')
  (sum(r[y==1L])-n1*(n1+1)/2)/(n1*n0)
}
# Compute average precision by grouping identical scores at a single threshold.
# This avoids introducing artificial precision changes through arbitrary tie ordering.
ap_score <- function(y,p) {
  ok <- is.finite(p) & !is.na(y)
  y <- y[ok];p <- p[ok]; n1<-sum(y==1L)
  if (!n1) return(NA_real_)
  oo <- order(p,decreasing=TRUE)
  y<-y[oo]; p<-p[oo]
  # cumulative precision at the end of each same-score block
  last <- which(!duplicated(p,fromLast=TRUE))
  cum_evt <- cumsum(y==1L)
  recalls <- c(0,cum_evt[last]/n1)
  prec <- cum_evt[last]/last
  sum(diff(recalls)*prec)
}
# Evaluate calibration via two logistic regressions of held-out event flags:
# intercept with logit(score) as an offset, and slope against logit(score).
# For degenerate scores, sparse outcomes or fitting problems, return NA rather than inventing values.
calibration_score <- function(y,p) {
  res<-c(intercept=NA_real_, slope=NA_real_)
  if(length(y)<10L || length(unique(y))<2L || any(!is.finite(p))) return(res)
  q <- stats::qlogis(pmin(1-1e-10,pmax(1e-10,p)))
  if (sd(q)<1e-12) return(res)
  # Fit a binomial calibration model with warnings recorded, not silently accepted.
  # Return NA if the model fails to converge or the requested coefficient is non-finite.
  safe_glm_term<-function(formula,term_index){
    warns<-character()
    ff<-tryCatch(withCallingHandlers(stats::glm(formula,family=binomial(),
                        control=stats::glm.control(maxit=50)),
               warning=function(w){warns<<-c(warns,conditionMessage(w));
                                      invokeRestart('muffleWarning')}),
             error=function(e) NULL)
    if(is.null(ff)||!isTRUE(ff$converged)||length(warns)||
       length(stats::coef(ff))<term_index ||
       !is.finite(stats::coef(ff)[term_index]))return(NA_real_)
    unname(stats::coef(ff)[term_index])
  }
  res['intercept']<-safe_glm_term(y~1+offset(q),1L)
  res['slope']<-safe_glm_term(y~q,2L)
  res
}
# Summarise one river/origin/model/source subset of held-out event probabilities.
# Report N/events/prevalence, AUC, AP, AP lift, Brier, prevalence-referenced skill,
# calibration and saturation counts; denominators are the finite scored subset.
metric <- function(origin,model,subset,y,p,lp) {
  good<-is.finite(p) & is.finite(lp) & !is.na(y)
  yy<-y[good]; pp<-p[good]
  prev<-if(length(yy))mean(yy) else NA_real_
  base_brier<-if(is.finite(prev))prev*(1-prev) else NA_real_
  cal<-calibration_score(yy,pp)
  brier<-if(length(yy))mean((yy-pp)^2) else NA_real_
  ap<-ap_score(yy,pp)
  data.frame(origin_rank=origin,model=model,source_subset=subset,
     risk_rows=length(y),predicted_rows=sum(good),events_all=sum(y==1L),
     predicted_events=sum(yy==1L),prevalence=prev,
     AUC=auc_score(yy,pp),average_precision=ap,
     AP_lift=if(is.finite(prev)&&prev>0)ap/prev else NA_real_,
     Brier=brier,prevalence_reference_Brier=base_brier,
     Brier_skill=if(is.finite(base_brier)&&base_brier>0)1-brier/base_brier else NA_real_,
     calibration_intercept=cal[['intercept']],calibration_slope=cal[['slope']],
     mean_probability=if(length(pp))mean(pp) else NA_real_,
     predicted_probability_sum=if(length(pp))sum(pp) else NA_real_,
     zero_probabilities=sum(pp==0),unit_probabilities=sum(pp==1),
     stringsAsFactors=FALSE)
}

# JAMUNA SOURCE CONTRACT — ingest the previously validated T1-defined binary
# AnalysisReadyRDS created for the final reach-specific historical Cox analysis.
rds_path <- path_input(AnalysisReadyRDS)
if (!file.exists(rds_path)) fail('Input AnalysisReadyRDS does not exist: ',rds_path)
# Create a new timestamped result directory; never overwrite previous completed runs.
root <- trimws(as.character(OutputFolder)[1L])
if(!nzchar(root)||is.na(root))fail('Select an OutputFolder')
if(!dir.exists(root))dir.create(root,recursive=TRUE,showWarnings=FALSE)
out<-file.path(root,paste0('Jamuna_FP_AD_Final_Rolling_P1_P2_v1_1_1_',
                         format(Sys.time(),'%Y%m%dT%H%M%S')))
if(!dir.create(out,recursive=TRUE,showWarnings=FALSE))fail('Cannot create output: ',out)
# Write a run-start marker immediately, before attempting source validation/fitting.
write_text(c('STARTED',as.character(Sys.time()),rds_path,
             'Models: P1 distance-only; P2 distance x T1 source; gap time; train-only'),
           '00_RUN_STARTED.txt')

# MAIN REPRODUCIBLE RUN — any error writes an explicit failure marker and stops.
tryCatch({
  # Read the immutable, analysis-ready Jamuna risk rows. All subsequent model
  # fitting operates on these rows rather than recomputing T1 states or events.
  d<-readRDS(rds_path)
  if(!is.data.frame(d)) fail('AnalysisReadyRDS is not a data frame')
  # Freeze the required source fields: identifiers, interval times, interval-start
  # floodplain provenance, T1 distance, final binary event and eligibility flags.
  required<-c('PLACE_ID','BLOCK_ID','TSTART','TSTOP','EVENT','SRC','Z','SRC_PRE')
  miss<-setdiff(required,names(d))
  if(length(miss))fail('Input RDS lacks columns: ',paste(miss,collapse=', '))
  # Frozen provenance prevents fitting to legacy or changed risk populations.
  # JAMUNA FROZEN CENSUS — exactly 1,585,497 eligible rows; a population
  # change cannot be silently accepted as the October publication run.
  if(nrow(d)!=1585497L) fail('Expected exactly 1,585,497 final T1 risk rows, got ',nrow(d))
  # Normalise the Jamuna RDS's start/stop times, distances, events and keys.
  d$TSTART<-number(d$TSTART);d$TSTOP<-number(d$TSTOP)
  d$Z<-number(d$Z);d$EVENT<-number(d$EVENT)
  d$SRC_PRE<-number(d$SRC_PRE)
  # Normalise place/block join keys and construct model-ready elapsed-time and
  # T1 covariate fields; source provenance is available before the event interval.
  d$PLACE_ID<-as.character(d$PLACE_ID)
  d$BLOCK_ID<-as.character(d$BLOCK_ID)
  d$SRC<-toupper(as.character(d$SRC))
  # Interval geometry is elapsed start–stop time, not assumed one-year steps.
  # Nonpositive gaps, missing endpoints and non-finite time values are rejected.
  if(anyNA(d$TSTART)||anyNA(d$TSTOP)||any(!is.finite(d$TSTART))||
     any(!is.finite(d$TSTOP))||any(d$TSTOP<=d$TSTART))fail('Invalid time intervals in RDS')
  # Events must remain the authoritative labelled FP→AD binary outcomes.
  # Eligibility explicitly excludes Depositional Storage (DS) from broad FP→AD.
  # Require exactly 14,391 known, authoritative FP→AD events in this risk file.
  if(anyNA(d$EVENT)||any(!d$EVENT %in% c(0,1))||sum(d$EVENT)!=14391L)
     fail('Final authoritative binary-event population is not conserved')
  # Z represents log1p(T1 Active-Domain margin distance in kilometres).
  # Do not substitute outcome-time distance: that would leak future geometry.
  if(anyNA(d$Z)||any(!is.finite(d$Z))||any(d$Z < -1e-12))
     fail('T1 log1p(distance/1000) not finite/nonnegative')
  # Enforce exactly two eligible antecedent floodplain sources:
  # STABILISED_FLOODPLAIN versus PREEXISTING_FLOODPLAIN; neither is DS.
  # SRC_PRE must agree with the categorical T1 floodplain source; reject mismatches.
  if(anyNA(d$SRC)||any(!d$SRC %in% c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN'))||
     anyNA(d$SRC_PRE)||any(!d$SRC_PRE %in% c(0,1))||
     any((d$SRC=='PREEXISTING_FLOODPLAIN') != (d$SRC_PRE==1)))
     fail('T1 floodplain source field is invalid or disagrees with SRC_PRE')
  # Every row must have joinable identifiers for the fixed-place spatial grid.
  if(anyNA(d$PLACE_ID)||any(!nzchar(d$PLACE_ID))||anyNA(d$BLOCK_ID)||
     any(!nzchar(d$BLOCK_ID)))fail('Missing PLACE/BLOCK key')
  # Parent RDS has one observation per PLACE x distinct start time.
  # Reject duplicate PLACE_ID × interval-start records before any score is joined
  # to mapped cells; duplicated keys would invalidate matched P1/P2 evaluation.
  pair_key<-paste(d$PLACE_ID,format(d$TSTART,digits=15,scientific=FALSE,trim=TRUE),sep='#')
  if(anyDuplicated(pair_key))fail('Duplicate PLACE_ID x TSTART interval; no forecasts computed')
  rm(pair_key);invisible(gc(FALSE))
  # Retain the observed duration of each interval in years as the gap-time horizon.
  duration<-d$TSTOP-d$TSTART
  # JAMUNA ORIGIN CLOCK — recover all 35 distinct interval starts from the
  # validated T1 RDS; T25/T30/T35 refer to ranks, not elapsed years.
  origin_times<-sort(unique(d$TSTART))
  # An incorrect Jamuna origin calendar invalidates the frozen T25/T30/T35 labels.
  # The historical Jamuna T25/T30/T35 mapping requires 35 interval starts.
  if(length(origin_times)!=35L)fail('Expected 35 original dated T1 ranks; got ',length(origin_times),
             '. Cannot infer production Tn ranks from this RDS.')
  # The validated original 35-start calendar produces these three ranks; checks
  # reject an incorrectly ranked or differently timed input instead of relabelling.
  # Cross-check that the Jamuna source ranks correspond to the intended
  # 2013 / 2018 / 2023 interval starts within the stored elapsed-time tolerance.
  expected_elapsed<-c('25'=26,'30'=31,'35'=36)
  for(r in names(expected_elapsed)) {
     elapsed<-origin_times[as.integer(r)]
     if(!is.finite(elapsed)||abs(elapsed-expected_elapsed[[r]])>0.20)
       fail('Input original rank T',r,' does not align with the expected 2013/2018/2023 T1 observation. Got elapsed start ',elapsed)
  }
  # Validate user-provided forecast origin ranks; this production script admits
  # only unique T25, T30 and T35 values, not a generic rolling window.
  requested<-trimws(strsplit(as.character(ForecastOrigins)[1L],',',fixed=TRUE)[[1L]])
  if(!length(requested)||any(!grepl('^(25|30|35)$',requested))||anyDuplicated(requested))
    fail('ForecastOrigins may contain unique values drawn only from 25,30,35')
  requested<-as.integer(requested)
  # Require sufficient preceding training events independently of later outcomes.
  min_event<-number(MinimumTrainingEvents)[1L]
  if(!is.finite(min_event)||min_event<1||min_event!=floor(min_event))
    fail('MinimumTrainingEvents must be a positive integer')
  # Archive the complete original rank-to-date key for reproducible interpretation.
  writing(data.frame(origin_rank=seq_along(origin_times),TSTART=origin_times,
         training_known_by_TSTART=NA_character_,
         published_reach_year=ifelse(seq_along(origin_times)==25,'2013',
                      ifelse(seq_along(origin_times)==30,'2018',
                      ifelse(seq_along(origin_times)==35,'2023',NA_character_)))),
         '01_original_35_origin_rank_calendar.csv')
  # Export input/population audit: total records, events, source mix, place counts
  # and the full event-exposure duration across the eligible record.
  writing(data.frame(check=c('input_rds','n_rows','authoritative_events','known_non_events',
      'distinct_T1_origins','unique_at_risk_places','source_PRE_rows','source_SF_rows',
      'source_PRE_events','source_SF_events','total_place_years','test_origin_ranks'),
      value=c(rds_path,nrow(d),sum(d$EVENT),sum(d$EVENT==0),length(origin_times),
       length(unique(d$PLACE_ID)),sum(d$SRC_PRE==1),sum(d$SRC_PRE==0),
       sum(d$EVENT[d$SRC_PRE==1]),sum(d$EVENT[d$SRC_PRE==0]),
       format(sum(duration),digits=16),paste(requested,collapse=','))),
       '01_final_binary_population_QA.csv')
  message('[Jamuna rolling P1/P2] Final binary population: ',nrow(d),
          ' rows; ',sum(d$EVENT),' events; ',length(origin_times),' original start ranks')
  # Training/exposure checks and test support written before any model fitting.
  # Build an explicit training/test population manifest before fitting any model.
  support<-list();selected_rows<-list()
  # ROLLING-ORIGIN SPLIT — train on observations completed no later than
  # the held-out start; score all qualifying rows beginning at that start.
  for(rank in requested){
     # Select the elapsed-time origin by authoritative rank; never use the test outcome
     # or later channel geometry when fitting the model at this origin.
     st<-origin_times[rank]
     # Training eligibility is TSTOP <= TSTART(origin), preventing held-out leakage.
     itrain<-which(d$TSTOP <= st + 1e-9)
     # Held-out population consists of intervals with TSTART exactly at the origin.
     # The two competing predictors are fitted/scored against these identical cells.
     itest<-which(abs(d$TSTART-st)<1e-9)
     # A train/test period with no eligible exposure cannot be evaluated.
     if(!length(itrain)||!length(itest))fail('No train/test rows at T',rank)
     if(any(d$TSTOP[itrain]>st+1e-9)||any(d$TSTART[itest]!=st))
        fail('Training uses future information or test starts incorrectly at T',rank)
     # Disallow any shared observation between training and held-out testing.
     if(length(intersect(itrain,itest)))fail('Train/test overlap at T',rank)
     # No unknown endpoint labels are admitted into training or reported validation.
     if(anyNA(d$EVENT[itrain])||anyNA(d$EVENT[itest]))fail('Unknown endpoint in train/test')
     if(sum(d$EVENT[itrain])<min_event)fail('Too few training events at T',rank)
     # Old archived counts were 100/70/42; new events must be identical because
     # only non-event eligibility and T1 distances were corrected.
     # MAMORE T25/T30/T35 event counts are frozen at 156/140/222.
     # An event-count change indicates a different eligibility or mapping version.
     expected_test_events<-switch(as.character(rank),'25'=100L,'30'=70L,'35'=42L)
     if(sum(d$EVENT[itest])!=expected_test_events)
        fail('Held-out T',rank,' event count disagrees with authoritative original ',expected_test_events,
              ' (found ',sum(d$EVENT[itest]),'); stop rather than silently relabel event history')
     # Also enumerate SF and pre-existing floodplain separately to detect shrinking
     # antecedent-source populations without changing the pooled matched forecast.
     # Compute evaluation metrics on ALL, SF-only and PRE-only subsets.
     # Small or one-class subsets correctly have undefined AUC/calibration entries.
     for(src in c('ALL','STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN')){
        tt<-if(src=='ALL')itest else itest[d$SRC[itest]==src]
        tr<-if(src=='ALL')itrain else itrain[d$SRC[itrain]==src]
        support[[length(support)+1L]]<-data.frame(origin_rank=rank,
           TSTART_elapsed=st,source=src,training_rows=length(tr),
           training_events=sum(d$EVENT[tr]),training_places=length(unique(d$PLACE_ID[tr])),
           training_last_TSTOP=max(d$TSTOP[tr]),
           test_rows=length(tt),test_events=sum(d$EVENT[tt]),
           test_places=length(unique(d$PLACE_ID[tt])),
           test_horizon_min=min(duration[tt]),test_horizon_max=max(duration[tt]))
     }
     # Retain the exact indices used by both models; this is the matched-pair guarantee.
     selected_rows[[as.character(rank)]]<-list(train=itrain,test=itest,st=st)
  }
  # Persist per-origin source counts before any possible model-fitting failure.
  writing(do.call(rbind,support),'02_train_test_origin_and_source_support.csv')
  # R memory: once basehaz computed, release the large cox fit; retain only
  # coefficients, robust covariance and model baseline hazard.
  # Pre-fit checks are computed solely on training data and saved regardless
  # of any fitting failure. A gap-time Surv(0,DUR,EVENT) object with every
  # T0=0 has the same Cox partial likelihood as Surv(DUR,EVENT); using the
  # latter invokes the standard right-censored coxph.fit rather than agreg.fit.
  # Source-centred P2 is an EXACT LINEAR REPARAMETERISATION of
  # X + SRC_PRE + X:SRC_PRE, not a change of predictors or estimand.
  # Fit one origin-specific P1 or P2 Cox model on strictly pre-origin labelled intervals.
  # P1 has one globally scaled log-distance term. P2 adds separate within-source
  # distance slopes and a source intercept; this is an algebraic reparameterisation
  # of distance + source + distance:source, not a different risk population.
  # Both fits use gap duration as survival time, Efron ties, PLACE_ID-clustered variance;
  # fail rather than output forecasts following warnings, non-convergence or bad baselines.
  # BEGIN FITTING HELPER — all transformations are learned from training only.
  fit_training<-function(ix,model_name,rank){
     # Estimate the common P1 log-distance mean/SD from this origin's training set.
     zmu<-mean(d$Z[ix]); zsd<-stats::sd(d$Z[ix])
     if(!is.finite(zsd)||zsd<1e-8)fail('Training log-distance is constant at T',rank)
     zz<-d$Z[ix]; ss<-d$SRC_PRE[ix]; ev<-d$EVENT[ix]
     sf<-ss==0; pre<-ss==1
     # P2 estimates distinct within-source location/scale terms using only SF/PRE
     # training intervals; this stabilises the source interaction parameterisation.
     mean_sf<-mean(zz[sf]); sd_sf<-stats::sd(zz[sf])
     mean_pre<-mean(zz[pre]); sd_pre<-stats::sd(zz[pre])
     # P2 is unsupported if either source has zero observed training events
     # or insufficient non-degenerate distance variation; write an audit and abort.
     if(model_name=='P2_DISTANCE_SOURCE' &&
        (!all(is.finite(c(mean_sf,sd_sf,mean_pre,sd_pre))) ||
            sd_sf<1e-8 || sd_pre<1e-8 ||
            sum(ev[sf])==0 || sum(ev[pre])==0)) {
        writing(data.frame(origin_rank=rank,model=model_name,
           reason='source_variation_or_events_insufficient',
           SF_rows=sum(sf),PRE_rows=sum(pre),SF_events=sum(ev[sf]),PRE_events=sum(ev[pre]),
           SF_distance_SD=sd_sf,PRE_distance_SD=sd_pre),
           paste0('09_fit_failure_T',rank,'_',model_name,'.csv'))
        fail('P2 source training support inadequate at T',rank,
             '; inspect 09_fit_failure_T',rank,'_',model_name,'.csv')
     }
     if(!is.finite(mean_sf))mean_sf<-NA_real_
     if(!is.finite(mean_pre))mean_pre<-NA_real_
     # Keep all train-only scaling parameters for applying exactly the same
     # linear-predictor transformation in held-out cells and saved RDS files.
     scale_stats<-list(global_mean=zmu,global_sd=zsd,
                       SF_mean=mean_sf,SF_sd=sd_sf,PRE_mean=mean_pre,PRE_sd=sd_pre)
     # Build the gap-time survival response using the actual interval duration.
     # Surv(DUR,EVENT) is equivalent to Surv(0,DUR,EVENT) when every start is 0.
     dat<-data.frame(DUR=duration[ix],EVENT=ev,
         PLACE_ID=d$PLACE_ID[ix],X=(zz-zmu)/zsd,SRC_PRE=ss)
     # P1: one pooled distance gradient, with PLACE_ID cluster-robust variance.
     if(model_name=='P1_DISTANCE') {
        f<-Surv(DUR,EVENT) ~ X + cluster(PLACE_ID)
        xnames<-c('X')
     # P2: source-specific distance slopes plus the antecedent-source main effect.
     # The source is measured at interval start and is not a fourth assemblage state.
     } else if(model_name=='P2_DISTANCE_SOURCE') {
        # Separate within-source centring removes the unstable near-collinearity
        # of a shared X and X:SRC_PRE when source distance distributions differ.
        dat$X_SF<-ifelse(sf,(zz-mean_sf)/sd_sf,0)
        dat$X_PRE<-ifelse(pre,(zz-mean_pre)/sd_pre,0)
        f<-Surv(DUR,EVENT) ~ X_SF + X_PRE + SRC_PRE + cluster(PLACE_ID)
        xnames<-c('X_SF','X_PRE','SRC_PRE')
     } else fail('Unexpected model ',model_name)
     # Export exposure variation and event ranges within ALL/SF/PRE training groups.
     # These distributions help explain instability when the PRE subset becomes small.
     design<-do.call(rbind,lapply(c('ALL','SF','PRE'),function(src){
         keep<-switch(src,ALL=rep(TRUE,length(ev)),SF=sf,PRE=pre)
         z<-zz[keep];y<-ev[keep]
         data.frame(origin_rank=rank,model=model_name,source=src,
             training_rows=length(y),training_events=sum(y),
             training_non_events=sum(y==0),
             Z_min=min(z),Z_p01=unname(quantile(z,.01)),
             Z_median=median(z),Z_p99=unname(quantile(z,.99)),Z_max=max(z),
             Z_min_events=if(sum(y)>0)min(z[y==1]) else NA_real_,
             Z_max_events=if(sum(y)>0)max(z[y==1]) else NA_real_,
             gap_years_min=min(dat$DUR[keep]),
             gap_years_max=max(dat$DUR[keep]),
             within_source_sd=stats::sd(z),stringsAsFactors=FALSE)
     }))
     # Record the model design even if a later Cox fit cannot be used.
     writing(design,paste0('09_fit_design_T',rank,'_',model_name,'.csv'))
     message('[Jamuna rolling v1.1.1] fitting T',rank,' ',model_name,
             ': ',nrow(dat),' intervals / ',sum(ev),' events; right-censored equivalent')
     # Catch all Cox warnings; a warning disqualifies a probability forecast here
     # rather than being suppressed or replaced by a penalised model.
     caught<-character()
     error_msg<-NA_character_
     # Unpenalised Cox fit: Efron handling of tied events and 50-iteration guard.
     # Clustered PLACE_ID covariance accounts for within-place recurrence only;
     # it does not remove dependence among neighbouring places.
     fit<-tryCatch(withCallingHandlers(
       survival::coxph(f,data=dat,ties='efron',x=TRUE,y=TRUE,model=FALSE,
             control=survival::coxph.control(iter.max=50)),
       warning=function(w){caught<<-c(caught,conditionMessage(w));invokeRestart('muffleWarning')}),
       error=function(e){error_msg<<-conditionMessage(e);NULL})
     # Reject warning-bearing/non-finite/non-converged models, exporting explicit
     # failure diagnostics before stopping the entire origin/model run.
     if(is.null(fit) || length(caught) ||
        (is.list(fit) && (!is.null(fit$fail) ||
        any(!is.finite(stats::coef(fit))) || anyNA(fit$var) ||
        any(!is.finite(fit$var)) || fit$iter>=50))) {
       writing(data.frame(origin_rank=rank,model=model_name,
           cox_response='Surv(DUR,EVENT)',
           parametric_form=if(model_name=='P2_DISTANCE_SOURCE')
             'source-orthogonal equivalent of X + SRC_PRE + X:SRC_PRE' else 'distance-only',
           failure=if(!is.na(error_msg))error_msg else
               if(length(caught))paste(unique(caught),collapse=' | ') else
               if(is.null(fit))'coxph returned NULL' else 'nonfinite_robust_covariance_or_iteration_limit',
           train_rows=length(ev),train_events=sum(ev),
           SF_train_events=sum(ev[sf]),PRE_train_events=sum(ev[pre]),
           distance_train_global_sd=zsd,SF_train_sd=sd_sf,PRE_train_sd=sd_pre),
           paste0('09_fit_failure_T',rank,'_',model_name,'.csv'))
       fail('Unstable/unfittable unpenalised Cox at T',rank,' ',model_name,
           ' (',if(!is.na(error_msg))error_msg else paste(caught,collapse=' | '),
           '). See 09_fit_design and 09_fit_failure CSV. ',
           'No prediction issued from a nonconvergent model.')
     }
     # Freeze the fitted coefficient names and verify they match P1/P2 design.
     beta<-stats::coef(fit)
     if(!identical(sort(names(beta)),sort(xnames)))
       fail('Unexpected coxph coefficients: ',paste(names(beta),collapse=','))
     # Extract train-only Breslow-type cumulative baseline via survival::basehaz.
     # This baseline converts relative Cox scores to the next-interval probabilities.
     bv<-tryCatch(withCallingHandlers(survival::basehaz(fit,centered=FALSE),
          warning=function(w){caught<<-c(caught,conditionMessage(w));invokeRestart('muffleWarning')}),
          error=function(e){error_msg<<-conditionMessage(e);NULL})
     # Require finite, nonnegative, nondecreasing cumulative hazard on valid times.
     if(is.null(bv)||length(caught)||!nrow(bv)||any(!is.finite(bv$hazard))||
        any(bv$hazard<0)||any(!is.finite(bv$time))||any(diff(bv$hazard) < -1e-9)) {
       writing(data.frame(origin_rank=rank,model=model_name,
           problem='basehaz failed or nonfinite',
           details=if(is.na(error_msg))paste(caught,collapse=' | ') else error_msg),
           paste0('09_baseline_failure_T',rank,'_',model_name,'.csv'))
       fail('Train-only Cox baseline hazard failed for ',model_name,' T',rank,
            '; inspect 09_baseline_failure CSV')
     }
     # Keep only baseline time/H0 and coefficient summaries; free the large fit.
     baseline<-data.frame(time=number(bv$time),H0=number(bv$hazard))
     # Standard errors use the PLACE_ID-clustered robust covariance from coxph.
     robustSE<-sqrt(diag(fit$var))
     # Preserve numerical coefficient/CI/HR scales and train-only centring terms.
     # The exponential guard prevents floating-point overflow in exported HRs, not beta clipping.
     coefficient_rows<-data.frame(origin_rank=rank,model=model_name,
       term=names(beta),beta=unname(beta),robust_se=unname(robustSE),
       HR_per_training_source_scale=exp(pmax(-700,pmin(700,unname(beta)))),
       robust_ci_low=unname(beta)-1.96*unname(robustSE),
       robust_ci_high=unname(beta)+1.96*unname(robustSE),
       train_logkm_mean=zmu,train_logkm_SD=zsd,
       SF_train_mean=mean_sf,SF_train_SD=sd_sf,
       PRE_train_mean=mean_pre,PRE_train_SD=sd_pre)
     # Translate fitted source-specific slopes back into a common raw Z
     # log-distance scale for between-model comparisons of the gradients.
     sf_grad<-if(model_name=='P1_DISTANCE')unname(beta[['X']])/zsd else
                   unname(beta[['X_SF']])/sd_sf
     pre_grad<-if(model_name=='P1_DISTANCE')sf_grad else
                   unname(beta[['X_PRE']])/sd_pre
     gradients<-data.frame(origin_rank=rank,model=model_name,
         source=c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN'),
         raw_Z_log_distance_beta=c(sf_grad,pre_grad))
     # This concordance is IN-SAMPLE training concordance, not held-out AUC.
     con<-tryCatch(unname(summary(fit)$concordance[1L]),error=function(e) NA_real_)
     if(length(con)!=1L||!is.finite(con)||con<0||con>1)con<-NA_real_
     # Retain fitting support, partial likelihood, train concordance and hazard
     # support range for a model-qualification and audit trail.
     overview<-data.frame(origin_rank=rank,model=model_name,
         train_rows=nrow(dat),train_events=sum(dat$EVENT),
         train_source_PRE_rows=sum(dat$SRC_PRE==1),
         train_source_PRE_events=sum(dat$EVENT[dat$SRC_PRE==1]),
         train_logkm_mean=zmu,train_logkm_SD=zsd,
         SF_train_mean=mean_sf,SF_train_SD=sd_sf,
         PRE_train_mean=mean_pre,PRE_train_SD=sd_pre,
         beta_n=length(beta),partial_loglik=tail(fit$loglik,1L),
         training_concordance=con,training_concordance_not_validation=TRUE,
         baseline_number_times=nrow(baseline),
         min_event_time=min(baseline$time),max_event_time=max(baseline$time),
         cox_response='Surv(DUR,EVENT)',parametrisation=if(model_name=='P1_DISTANCE')
              'train-standardised distance' else 'within-source-centred orthogonal',
         warnings='',fit_status='CLEAN')
     # Release the full design matrix, event vectors and fitted Cox object to reduce RAM.
     rm(fit,dat);invisible(gc(FALSE))
     list(beta=beta,baseline=baseline,scales=scale_stats,
          mean=zmu,sd=zsd,coefficients=coefficient_rows,
          gradients=gradients,overview=overview)
  }
  # Apply one saved origin-specific fit to the unchanged held-out test rows.
  # Reconstruct train-only standardisation, evaluate the train-only cumulative baseline
  # at each observed test interval duration, and derive probability 1-exp(-H0*exp(lp)).
  # Disallow extrapolation beyond the observed baseline event-time support.
  # BEGIN FORECAST HELPER — only the origin-specific fitted object is used.
  predict_one<-function(obj,idx,model_name,rank){
     # Read strictly antecedent distance/source predictors from the held-out rows.
     z<-d$Z[idx];s<-d$SRC_PRE[idx]
     # P1: one pooled distance gradient, with PLACE_ID cluster-robust variance.
     if(model_name=='P1_DISTANCE') {
         lp<-unname(obj$beta[['X']])*(z-obj$mean)/obj$sd
     } else {
         lp<-unname(obj$beta[['X_SF']])*ifelse(s==0,
                  (z-obj$scales$SF_mean)/obj$scales$SF_sd,0)+
             unname(obj$beta[['X_PRE']])*ifelse(s==1,
                  (z-obj$scales$PRE_mean)/obj$scales$PRE_sd,0)+
             unname(obj$beta[['SRC_PRE']])*s
     }
     if(any(!is.finite(lp)))fail('Non-finite test linear predictor ',model_name,' at T',rank)
     # Evaluate each held-out observation duration against the *training* baseline.
     bh<-obj$baseline
     dt<-duration[idx]
     # Step-function cumulative hazard: find latest observed train event time <= dt.
     j<-findInterval(dt,bh$time)
     H<-numeric(length(dt));inside<-j>0L
     H[inside]<-bh$H0[j[inside]]
     # No extrapolation of the training baseline beyond observed event support.
     # Do not extrapolate baseline hazards beyond the time interval supported by
     # training events; this is distinct from later calendar-year origin ranks.
     out_of_time<-dt>max(bh$time)+1e-9
     below_first<-dt<min(bh$time)-1e-9
     if(any(out_of_time))fail('Held-out T',rank,' ',model_name,
          ' horizon exceeds latest training event time. No baseline extrapolation permitted.')
     if(any(below_first))fail('Held-out T',rank,' ',model_name,
          ' horizon predates first training event time. Zero-hazard extrapolation forbidden.')
     # Compute cumulative individual hazard H0(dt) * exp(linear predictor).
     # The exponential numerical guard prevents overflow during probability evaluation.
     hp<-H*exp(pmax(-700,pmin(700,lp)))
     # Convert cumulative hazard into a [0,1] event probability, using expm1
     # for numerical accuracy when risks are small.
     pp<- -expm1(-hp)
     if(any(!is.finite(pp))||any(pp<0)||any(pp>1))
         fail('Invalid held-out probabilities for ',model_name,' T',rank)
     list(prob=pp,lp=lp,
          baseline_horizon_min=min(H),baseline_horizon_max=max(H),
          forecast_horizon_min=min(dt),forecast_horizon_max=max(dt),
          test_prob_min=min(pp),test_prob_max=max(pp),
          test_lp_min=min(lp),test_lp_max=max(lp),
          n_probability_zero=sum(pp==0),n_probability_one=sum(pp==1))
  }

  # Allocate separate collectors for models, held-out metrics and provenance.
  model_coeffs<-list();model_grads<-list();model_fits<-list();evals<-list()
  paired<-list();exposures<-list();captures<-list();export_rows<-list()
  # ROLLING-ORIGIN SPLIT — train on observations completed no later than
  # the held-out start; score all qualifying rows beginning at that start.
  for(rank in requested){
    st<-selected_rows[[as.character(rank)]]$st
    itrain<-selected_rows[[as.character(rank)]]$train
    itest<-selected_rows[[as.character(rank)]]$test
    message('[Jamuna rolling P1/P2] T',rank,' train ',length(itrain),
            ' (',sum(d$EVENT[itrain]),' events); test ',length(itest),
            ' (',sum(d$EVENT[itest]),' events)')
    preds<-list(); metrics_by_model<-list()
    # Fit and score both P1 and P2 independently for the SAME origin-specific
    # eligible test row indices; only the forecast predictor block changes.
    for(mod in c('P1_DISTANCE','P2_DISTANCE_SOURCE')){
      # Refit each model on the preceding historical intervals, never the full record.
      fit<-fit_training(itrain,mod,rank)
      # Score the common held-out risk population for this origin/model.
      pred<-predict_one(fit,itest,mod,rank)
      model_coeffs[[length(model_coeffs)+1L]]<-fit$coefficients
      model_grads[[length(model_grads)+1L]]<-fit$gradients
      model_fits[[length(model_fits)+1L]]<-fit$overview
      exposures[[length(exposures)+1L]]<-data.frame(origin_rank=rank,model=mod,
       train_hazard_min_time=min(fit$baseline$time),
       train_hazard_max_time=max(fit$baseline$time),
       test_duration_min=pred$forecast_horizon_min,
       test_duration_max=pred$forecast_horizon_max,
       baseline_H0_at_test_min=pred$baseline_horizon_min,
       baseline_H0_at_test_max=pred$baseline_horizon_max,
       test_pred_probability_min=pred$test_prob_min,
       test_pred_probability_max=pred$test_prob_max,
       test_linear_predictor_min=pred$test_lp_min,
       test_linear_predictor_max=pred$test_lp_max,
       saturated_zero_predictions=pred$n_probability_zero,
       saturated_one_predictions=pred$n_probability_one)
      # Archive model coefficients, training baseline, source scaling and exact
      # origin metadata in per-origin RDS objects for reproducibility.
      saveRDS(list(version='1.1.1',origin_rank=rank,model=mod,
                   trained_until_elapsed=st,train_n=length(itrain),
                   baseline=fit$baseline,coefficients=fit$beta,
                   train_logkm_mean=fit$mean,train_logkm_sd=fit$sd,
                   source_specific_train_scalers=fit$scales,
                   transformation='Z=log1p(DIST_ACTIVE_CURR_m/1000)',
                   time_basis='gap_time',cox_response='Surv(DUR,EVENT)',
                   baseline_method='coxph Efron basehaz centered FALSE',
                   cluster='PLACE_ID',source='T1 SRC_PRE'),
          file.path(out,paste0('40_prediction_object_T',rank,'_',mod,'.rds')),
          compress='gzip')
      preds[[mod]]<-pred
      ee<-list()
      # Also enumerate SF and pre-existing floodplain separately to detect shrinking
      # antecedent-source populations without changing the pooled matched forecast.
      # Compute evaluation metrics on ALL, SF-only and PRE-only subsets.
      # Small or one-class subsets correctly have undefined AUC/calibration entries.
      for(src in c('ALL','STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN')){
         keep<-if(src=='ALL')rep(TRUE,length(itest)) else d$SRC[itest]==src
         ee[[length(ee)+1L]]<-metric(rank,mod,src,
           d$EVENT[itest][keep],pred$prob[keep],pred$lp[keep])
      }
      evals[[length(evals)+1L]]<-do.call(rbind,ee)
      # A standalone CSV per origin/model makes QGIS join by BLOCK_ID explicit.
      # Prepare flat held-out forecast rows for mapping and independent verification.
      if(flag(WriteQGISForecastCSVs)||flag(WriteCombinedPredictionGZ)){
         # Attach the river-specific observed interval dates to each Tn forecast.
         dates<-switch(as.character(rank),'25'=c(20130101L,20140101L),
           '30'=c(20180101L,20190101L),'35'=c(20230101L,20240101L))
         # Export block/place identifiers, origin/date, the T1 source and distance,
         # held-out event flag, risk probability and linear predictor.
         tab<-data.frame(origin_rank=rank,model=mod,Y1=dates[1L],Y2=dates[2L],
           BLOCK_ID=d$BLOCK_ID[itest],PLACE_ID=d$PLACE_ID[itest],
           TSTART=d$TSTART[itest],TSTOP=d$TSTOP[itest],
           INTERVAL_YEARS=duration[itest],T1_SOURCE=d$SRC[itest],
           SRC_PRE=d$SRC_PRE[itest],
           DIST_ACTIVE_CURR_M=1000*expm1(d$Z[itest]),
           Z_T1=d$Z[itest],EVENT=d$EVENT[itest],
           P_STATUS=pred$prob,P_EVENT=pred$prob,
           LINEAR_PREDICTOR=pred$lp,stringsAsFactors=FALSE)
         # Every BLOCK_ID maps to one scored cell per origin/model, avoiding ambiguous
         # spatial joins and false replication of events.
         if(anyDuplicated(tab$BLOCK_ID))fail('Non-unique BLOCK_ID at T',rank,
                      '; map joins must be 1:1 per origin')
         if(flag(WriteQGISForecastCSVs))
             writing(tab,paste0('30_QGIS_forecast_T',rank,'_',mod,'.csv'))
         # Optionally combine all per-origin prediction rows in a compressed archive.
         if(flag(WriteCombinedPredictionGZ)) export_rows[[length(export_rows)+1L]]<-tab
      }
      rm(fit);invisible(gc(FALSE))
    }
    # MATCHED MODEL COMPARISON — P1/P2 scores refer to exactly the same
    # held-out event vector; compare AUC, AP, Brier skill and calibration directly.
    pa<-preds[['P1_DISTANCE']]$prob
    pb<-preds[['P2_DISTANCE_SOURCE']]$prob
    if(length(pa)!=length(itest)||length(pb)!=length(itest)||any(!is.finite(pa))||
       any(!is.finite(pb)))fail('P1/P2 held-out score population mismatch at T',rank)
    yy<-d$EVENT[itest]
    m1<-metric(rank,'P1_DISTANCE','ALL',yy,pa,preds[['P1_DISTANCE']]$lp)
    m2<-metric(rank,'P2_DISTANCE_SOURCE','ALL',yy,pb,preds[['P2_DISTANCE_SOURCE']]$lp)
    # The reported differences are P2 minus P1, with no change of test samples.
    # These are descriptive held-out contrasts, not independent-river validation.
    paired[[length(paired)+1L]]<-data.frame(origin_rank=rank,
       matched_rows=length(itest),matched_events=sum(yy==1),
       delta_AUC_P2_minus_P1=m2$AUC-m1$AUC,
       delta_AP_P2_minus_P1=m2$average_precision-m1$average_precision,
       delta_Brier_P2_minus_P1=m2$Brier-m1$Brier,
       delta_Brier_skill_P2_minus_P1=m2$Brier_skill-m1$Brier_skill,
       delta_abs_calib_intercept_P2_minus_P1=abs(m2$calibration_intercept)-abs(m1$calibration_intercept),
       delta_abs_calib_slope_error_P2_minus_P1=abs(m2$calibration_slope-1)-abs(m1$calibration_slope-1),
       score_pearson_cor=if(stats::sd(pa)>0&&stats::sd(pb)>0)stats::cor(pa,pb) else NA_real_)
    # Emit descriptive cell-based capture only. Area-based geometry overlays
    # MUST be generated later using actual clipped 150 m hex polygon areas.
    for(mod in names(preds)){
       pp<-preds[[mod]]$prob
       # Ranked top percentages here select CELL COUNTS, not clipped polygon areas.
       # These diagnostic captures must not be labelled polygon recall/IoU.
       for(pct in c(2.5,5,10,20,30)){
          n_top<-max(1L,ceiling(length(itest)*pct/100))
          top<-order(pp,decreasing=TRUE)[seq_len(n_top)]
          selected_rows_count<-sum(yy[top]==1L)
          captures[[length(captures)+1L]]<-data.frame(
              origin_rank=rank,model=mod,top_cell_percent=pct,
              total_test_cells=length(itest),number_top_cells=n_top,
              total_event_cells=sum(yy==1L),event_cells_in_top=selected_rows_count,
              event_cell_recall=if(sum(yy==1L)>0)selected_rows_count/sum(yy==1L) else NA_real_)
       }
    }
  }
  # FINAL OUTPUT BLOCK — retain all model and forecasting QA in CSV files.
  writing(do.call(rbind,model_fits),'10_rolling_model_fit_status.csv')
  writing(do.call(rbind,model_coeffs),'11_rolling_robust_coefficients.csv')
  writing(do.call(rbind,model_grads),'12_rolling_source_distance_gradients.csv')
  # Main held-out discrimination/probability metrics: source of the reported
  # matched broad FP→AD Tables S15c–d and support for S15e.
  writing(do.call(rbind,evals),'20_rolling_origin_metrics_by_source.csv')
  # Export explicit paired model deltas used to verify October P1→P2 changes.
  writing(do.call(rbind,paired),'21_P2_minus_P1_paired_test_comparison.csv')
  # Keep cell-ranked capture separately from the polygon-area overlays in S8/S9.
  writing(do.call(rbind,captures),'22_descriptive_top_CELL_event_capture_NOT_AREA.csv')
  # Preserve evidence that each scored horizon fell within its training baseline.
  writing(do.call(rbind,exposures),'23_baseline_forecast_horizon_QA.csv')
  # Optionally combine all per-origin prediction rows in a compressed archive.
  if(flag(WriteCombinedPredictionGZ)){
      outgz<-gzfile(file.path(out,'30_ALL_rolling_prediction_rows.csv.gz'),open='wt')
      tryCatch(utils::write.csv(do.call(rbind,export_rows),outgz,row.names=FALSE,na=''),
         finally=close(outgz))
  }
  # Write the frozen forecasting specification, input population, timing and
  # non-included analyses for interpreting the emitted results.
  writing(data.frame(item=c('scientific_purpose','P1','P2','prediction_time_basis',
       'training_eligibility','T1_covariate','frozen_binary_population','forecast_origins',
       'forecast_label_meaning','heldout_test','source_information','gap_time_baseline',
       'probability_formula','normalisation','paired_test','MAP_SCOPE',
       'spatial_support','prospective_caveat','not_included'),
       value=c('Held-out rolling interval FP to AD forecasts, not refit of joint historical Cox',
       'Pooled distance-only gap-time Cox',
       'Pooled gap-time Cox with source-centred distance + SRC_PRE, algebraically equivalent to distance + source + interaction',
       'Surv(interval_duration,EVENT), mathematically identical because start=0',
       'Only observed intervals with TSTOP <= the heldout origin TSTART',
       'Z=log1p(DIST_ACTIVE_CURR_m/1000) verified nominal T1',
       'Final RDS T1 1585497 binary rows, 14391 authoritative events',
       paste(requested,collapse=','),
       'Tn = rank among the 35 original distinct interval-start dates',
       'All risk rows TSTART == origin; P1/P2 test keys exactly identical',
       'PRE versus SF from T1; no T2 or future state predictors',
       'Efron Cox baseline estimated only on training gaps; coxph.fit right censored',
       'P=1-exp(-H0(interval_duration)*exp(lp))',
       'Train-only overall distance scaling (P1); within-source train-only scaling (P2)',
       'P2 minus P1 on matched heldout T1 rows',
       'Probability CSVs for future Module5 polygons; no geometry overlays in this script',
       '150m equivalent-area hex KM blocks; cell-capture percentages are not area recall',
       'Retrospective origin withheld outcomes; corridor itself is defined from full observation record',
       'Full-history joint model coefficients; P3 temporal; retraining by test outcomes; source stratification selection')),
       '90_frozen_forecasting_specification.csv')
  # Successful completion marker certifies that every requested origin/model
  # passed the script's own population, fit, baseline and prediction checks.
  write_text(c('COMPLETED',as.character(Sys.time()),
       paste('Original T1 binary risk rows:',nrow(d),'; authoritative events:',sum(d$EVENT)),
       paste('Origins:',paste(requested,collapse=',')),
       'P1 and P2 refitted only using historical known outcomes at each origin.',
       'P1/P2 predictions evaluated on IDENTICAL risk rows at each origin.',
       'Warning-free numeric fits and baseline hazard support required.',
       'No historical six-coefficient full-record model coefficients used.',
       'Right-censored Surv(DUR,EVENT) is exactly equivalent to all-zero-start gap-time counting process.',
       'P2 within-source centering is algebraically equivalent to original source interaction.',
       'No full-period union covariates used (corridor spatial support is retrospective).',
       'QGIS CSV rows store P_STATUS = held-out event probability; footprint overlay not performed.'),
       '00_RUN_COMPLETED.txt')
  message('[Jamuna rolling P1/P2] COMPLETED. Outputs: ',out)
# On failure write 00_RUN_FAILED.txt; do not mark a partial output complete.
},error=function(e){
  write_text(c('FAILED',as.character(Sys.time()),conditionMessage(e),
               paste('Source RDS:',rds_path)), '00_RUN_FAILED.txt')
  stop(e)
})
