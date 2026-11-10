##FRAF Floodplain Reassemblage=group
##Mamoré FP to AD - Historical PH and Temporal Investigation v1.0=name
##ReleasedBinaryTable=file
##OriginalHistoricalOutputFolder=folder
##OutputParentFolder=folder
##RunNO1986Sensitivity=boolean TRUE
##RunWithinSourcePeriodPH=boolean TRUE
##RunFullSourceInteractionPH=boolean TRUE
##MinimumEventsPerSourcePeriod=number 8
##FirstPeriodCutElapsedYears=number -1
##SecondPeriodCutElapsedYears=number -1

# ARCHIVE ROLE — Paper 2 / Stage 06F / Mamore historical source-period Cox.
# Original source: FRAF_Mamore_FP_AD_Historical_PH_Temporal_Investigation_v1_0.rsx.
# Publication copy: comments have been added ONLY; formulas, QGIS declarations,
# output paths, input rules, tests and execution behaviour are unmodified.
# This procedure produces six source-period distance slopes (S21) and robust
# Wald source/temporal comparisons (S22), plus main-versus-NO1986 sensitivity.
# The source-period model is historical explanatory inference, not the
# separate matched held-out FP->AD P1/P2 forecast (07P).
# Mamoré FP->AD HISTORICAL inference only. No rolling forecasts, no maps, no
# event/state relabelling, no source GeoPackage writes. Uses EXACT released
# locally-qualified T1 model cohort from 17 Oct final P1/P2 run, including the
# 1986 analyst-attested qualification. A conservative NO1986 sensitivity is
# evaluated on an explicitly defined, smaller historical population.
#
# Primary scientific estimand: in counting-process (absolute elapsed-time)
# Cox fits, does the effect of T1 Active-Domain distance vary between EARLY,
# MIDDLE, LATE thirds of the 1984-2025 historical record and by T1 provenance?
# Source x period BASELINE hazards are separate; there is NO common SOURCE HR.
# Temporal contrasts are PLACE_ID-cluster-robust Wald tests (not an LRT).
# Cox-Schoenfeld PH screens are diagnostic, NOT spatially cluster-robust tests.
# This runs on the user's Windows R 4.6 / QGIS R Processing; not run on input
# GeoPackage here. Input source/1986 mapping is analyst qualified, not an
# independently validated observation footprint.

# DEPENDENCIES.
# The QGIS R Processing runtime requires sf for GeoPackage I/O and survival
# for Cox counting-process fits and Schoenfeld residual tests.
suppressPackageStartupMessages({
  if(!requireNamespace('survival',quietly=TRUE))stop('Required R package survival is missing')
  if(!requireNamespace('sf',quietly=TRUE))stop('Required R package sf is missing')
  library(survival)
})
options(stringsAsFactors=FALSE, scipen=99)

# PATH AND SERIALISATION HELPERS.
# QGIS inputs may be URI strings containing a layer suffix. These functions
# remove the suffix, normalize Windows paths, quote SQL identifiers, and write
# CSV or plain-text provenance records without changing the input GeoPackage.
path_only<-function(x) sub('\\|.*$','',as.character(x)[1L])
normalize_slashes<-function(x) gsub('\\\\','/',path_only(x))
num<-function(x) suppressWarnings(as.numeric(x))
qsql<-function(x) paste0('"',gsub('"','""',x,fixed=TRUE),'"')
write_file<-function(d,name,folder){
  utils::write.csv(as.data.frame(d),file.path(folder,name),row.names=FALSE,na='')
}
write_note<-function(lines,name,folder){
  writeLines(as.character(lines),file.path(folder,name),useBytes=TRUE)
}
# WARNING CAPTURE.
# Retain Cox fitting warnings for later QA rather than suppressing their
# provenance. Fatal R errors remain separate from warnings.
warn_capture<-function(expr){
  warnings<-character()
  ans<-tryCatch(withCallingHandlers(expr,warning=function(w){
    warnings<<-unique(c(warnings,conditionMessage(w)))
    invokeRestart('muffleWarning')
  }),error=function(e)e)
  list(value=ans,warnings=warnings)
}
# FINITE-FIT GUARD.
# All Cox fits use Efron ties. Clustered model formulas supply robust variance;
# for PH requests, x/y/model components are retained for cox.zph.
# Reject non-finite coefficients, covariance or log-likelihood and explicit
# nonconvergence. Finite estimates alone do not imply PH adequacy.
fit_cox<-function(form,dat,for_ph=FALSE,allow_warning=TRUE){
  r<-warn_capture(survival::coxph(form,data=dat,ties='efron',
    x=isTRUE(for_ph),y=isTRUE(for_ph),model=isTRUE(for_ph),
    control=survival::coxph.control(iter.max=65)))
  if(inherits(r$value,'error'))stop('Cox fitting error: ',conditionMessage(r$value))
  fit<-r$value
  b<-stats::coef(fit);V<-stats::vcov(fit)
  if(!length(b)||any(!is.finite(b))||any(!is.finite(V))||
      any(diag(V)<=0)||!is.finite(tail(fit$loglik,1)))
    stop('Cox returned nonfinite coefficients, robust variance or log-likelihood')
  if(!isTRUE(fit$converged) && !is.null(fit$converged))
    stop('Cox convergence flag is FALSE')
  if(length(r$warnings)&&!allow_warning)
    stop('Cox emitted warnings: ',paste(r$warnings,collapse=' | '))
  list(fit=fit,warnings=r$warnings)
}
# COEFFICIENT EXPORT.
# Report log-distance slopes and place-cluster robust standard errors, 95%
# normal-approximation bounds and exp(beta). The unit is a one-unit change
# in log1p(distance in km); HR is NOT the effect of one metre.
get_coefs<-function(fit,model){
  b<-stats::coef(fit);se<-sqrt(diag(stats::vcov(fit)))
  data.frame(model=model,term=names(b),beta=as.numeric(b),
    robust_se=as.numeric(se),lower_95=as.numeric(b-1.96*se),
    upper_95=as.numeric(b+1.96*se),HR_per_unit_log1p_km=exp(as.numeric(b)),
    stringsAsFactors=FALSE)
}
# JOINT ROBUST WALD CONTRASTS.
# Construct contrasts of beta from the PLACE_ID-clustered covariance matrix.
# The all-temporal-change hypothesis has four degrees of freedom; p-values
# are not likelihood-ratio tests. Singular robust contrasts are reported NA.
wald<-function(b,V,terms_list,name){
  C<-matrix(0,nrow=length(terms_list),ncol=length(b),
    dimnames=list(NULL,names(b)))
  for(i in seq_along(terms_list)){
    v<-terms_list[[i]]
    if(!all(names(v)%in%names(b)))stop('Missing coefficient in contrast ',name)
    C[i,names(v)]<-v
  }
  est<-as.numeric(C%*%b)
  cv<-C%*%V%*%t(C)
  chisq<-tryCatch(as.numeric(crossprod(est,solve(cv,est))),error=function(e)NA_real_)
  data.frame(test=name,df=nrow(C),robust_wald_chisq=chisq,
    robust_p=if(is.finite(chisq))stats::pchisq(chisq,nrow(C),lower.tail=FALSE) else NA_real_,
    status=if(is.finite(chisq))'OK' else 'SINGULAR_ROBUST_CONTRAST',
    stringsAsFactors=FALSE)
}
# PROPORTIONAL-HAZARDS SCREEN.
# cox.zph supplies diagnostic Schoenfeld-type tests; these are NOT place-cluster
# robust tests. PH failure limits constant-coefficient interpretation but does
# not, by itself, invalidate a finite historical Cox fit.
ph_csv<-function(fit,name,folder,transform='km'){
  r<-warn_capture(survival::cox.zph(fit,transform=transform))
  if(inherits(r$value,'error')){
    ans<-data.frame(model=name,term='PH_FAILED',chisq=NA_real_,
      df=NA_real_,p=NA_real_,transform=transform,
      status='FAILED',warning=paste(c(conditionMessage(r$value),r$warnings),collapse=' | '))
  }else{
    tb<-as.data.frame(r$value$table)
    ans<-data.frame(model=name,term=rownames(tb),chisq=num(tb$chisq),
       df=num(tb$df),p=num(tb$p),transform=transform,
       status='NUMERIC_PH_TEST',warning=paste(r$warnings,collapse=' | '))
    capture.output(print(r$value),
      file=file.path(folder,paste0('20_PH_',name,'.txt')))
  }
  write_file(ans,paste0('20_PH_',name,'.csv'),folder)
  ans
}
# READ-ONLY GEOPACKAGE ACCESS.
# SQLite attribute queries are passed through sf; geometry is discarded to
# avoid retaining large geometries during Cox estimation.
read_table<-function(p,sql){
  v<-suppressWarnings(sf::st_read(p,query=sql,quiet=TRUE,
                                  options='LIST_ALL_TABLES=YES'))
  if(inherits(v,'sf'))v<-sf::st_drop_geometry(v)
  as.data.frame(v,stringsAsFactors=FALSE)
}
require_layer<-function(p,layer){
  n<-sf::st_layers(p,options='LIST_ALL_TABLES=YES')$name
  if(!layer%in%n)stop('Required layer ',layer,' not found; available: ',paste(n,collapse=', '))
}

# RELEASED INPUT AND RUN PROVENANCE.
# The input is the released, locally 1986-qualified FP->AD binary table, NOT
# the unadjudicated risk table. The prior v1.0.1 Cox run is a reference guard,
# not the script generating these six-period coefficients.
source_path<-normalize_slashes(ReleasedBinaryTable)
history_root<-normalize_slashes(OriginalHistoricalOutputFolder)
parent<-normalize_slashes(OutputParentFolder)
if(!file.exists(source_path))stop('Select the released T2 binary threshold-reconciled GeoPackage')
if(!dir.exists(parent))dir.create(parent,recursive=TRUE,showWarnings=FALSE)
if(!dir.exists(parent))stop('Cannot create OutputParentFolder: ',parent)
if(!dir.exists(history_root))stop('Select the completed historical Cox output folder for reproduction QA')
run_root<-file.path(parent,paste0('Mamore_FP_AD_Historical_PH_Temporal_v1_0_',
                       format(Sys.time(),'%Y%m%dT%H%M%S')))
if(!dir.create(run_root,recursive=TRUE,showWarnings=FALSE))
  stop('Cannot create new timestamped output folder: ',run_root)
# OUTPUT LAYOUT.
# 01_Targeted_PH: reference/full-source PH tests.
# 02_Temporal_Triage: elapsed-period specification and summarized slopes.
# 03_Joint_Source_Period: principal complete-record six-slope model.
# 04_NO1986_Sensitivity: separately refitted reduced-population six-slope model.
# WARNING: folders 03 and 04 deliberately contain files with IDENTICAL names,
# including 11_joint_six_source_period_coefficients.csv and
# 12_robust_wald_temporal_and_source_tests.csv. Directory provenance is essential
# when reconciling sensitivity exports against published S21-S22.
f_target<-file.path(run_root,'01_Targeted_PH')
f_temporal<-file.path(run_root,'02_Temporal_Triage')
f_joint<-file.path(run_root,'03_Joint_Source_Period')
f_sens<-file.path(run_root,'04_NO1986_Sensitivity')
for(f in c(f_target,f_temporal,f_joint,f_sens))dir.create(f)
write_note(c('STARTED',as.character(Sys.time()),
  paste0('ReleasedBinaryTable=',source_path),paste0('HistoricalReference=',history_root)),
  '00_RUN_STARTED.txt',run_root)

# Main model inputs retain 1986-qualified support exactly as released.
# FROZEN POPULATION ASSERTIONS.
# Main fitted cohort: 1,001,403 eligible rows and 8,350 FP->AD events;
# 7,178 pre-existing and 1,172 stabilised-source events.
# Conservative NO1986 cohort: 944,341 rows, 7,484 events. Fail immediately
# if inputs do not reproduce these released October counts.
expected<-list(main_rows=1001403L,main_events=8350L,
               pre_events=7178L,sf_events=1172L,
               no1986_rows=944341L,no1986_events=7484L)
levels6<-c('SF_EARLY','PRE_EARLY','SF_MIDDLE','PRE_MIDDLE','SF_LATE','PRE_LATE')
eras<-c('EARLY','MIDDLE','LATE')

# The period splitter performs explicit per-original-row event and exposure
# reconciliation. An event at a cut is allocated to the period ending there.
# SOURCE-PERIOD COUNTING-PROCESS SPLITTING.
# Split every eligible observation interval at elapsed-time period boundaries.
# Retain full exposure duration and allocate each event exactly once to the
# period ending at its observed event time. Check event and time conservation.
# No missing observation is filled with an inferred annual state.
period_split<-function(d,bounds,folder,prefix=''){
  n<-nrow(d);expl<-numeric(n);events<-integer(n)
  splits<-vector('list',3L);support<-list()
  for(k in 1:3){
    ix<-which(d$TSTART<bounds[k+1] & d$TSTOP>bounds[k])
    z<-d[ix,c('TSTART','TSTOP','EVENT','PLACE_ID','SRC','SRC_PRE','Z'),drop=FALSE]
    orig_stop<-z$TSTOP
    z$TSTART<-pmax(z$TSTART,bounds[k]);z$TSTOP<-pmin(z$TSTOP,bounds[k+1])
    if(any(z$TSTART>=z$TSTOP))stop('Period splitting made zero-duration rows')
# EVENT-AT-BOUNDARY ALLOCATION.
# The event remains on the last portion of its original interval (end time
# at or before the current period upper limit), avoiding duplicated events.
    z$EVENT<-as.integer(z$EVENT==1L & orig_stop<=bounds[k+1])
    expl[ix]<-expl[ix]+z$TSTOP-z$TSTART
    events[ix]<-events[ix]+z$EVENT
    z$PERIOD<-eras[k]
    z$SRC_PERIOD<-factor(ifelse(z$SRC_PRE==1L,
                                paste0('PRE_',eras[k]),paste0('SF_',eras[k])),levels=levels6)
    for(pre in c(0L,1L)){
      j<-z$SRC_PRE==pre
      support[[length(support)+1L]]<-data.frame(period=eras[k],
        period_start=bounds[k],period_end=bounds[k+1],
        source=if(pre==1L)'PREEXISTING_FLOODPLAIN' else 'STABILISED_FLOODPLAIN',
        split_risk_intervals=sum(j),events=sum(z$EVENT[j]),
        place_years=sum(z$TSTOP[j]-z$TSTART[j]),
        unique_places=length(unique(z$PLACE_ID[j])))
    }
    splits[[k]]<-z
    rm(z,orig_stop,ix);invisible(gc(FALSE))
  }
  qa<-data.frame(check=c('original_rows','split_rows','original_events',
    'split_events','event_mismatches','max_original_row_exposure_error_years',
    'original_place_years','split_place_years','split_minus_original_place_years',
    'period_cut_1','period_cut_2'),
    value=as.character(c(n,sum(vapply(splits,nrow,integer(1))),sum(d$EVENT),
      sum(events),sum(events!=d$EVENT),max(abs(expl-(d$TSTOP-d$TSTART))),
      sum(d$TSTOP-d$TSTART),sum(expl),
      sum(expl)-sum(d$TSTOP-d$TSTART),bounds[2],bounds[3])))
# SPLIT INTEGRITY EVIDENCE.
# Record source-row count, generated split rows, event conservation, and
# absolute person-years. An inconsistent split is fatal before Cox fitting.
  write_file(qa,paste0(prefix,'01_population_and_split_integrity.csv'),folder)
  su<-do.call(rbind,support);rownames(su)<-NULL
  write_file(su,paste0(prefix,'02_source_period_support.csv'),folder)
  bad<-sum(events!=d$EVENT)>0L||any(!is.finite(expl))||
    max(abs(expl-(d$TSTOP-d$TSTART)))>1e-8||
    abs(sum(expl)-sum(d$TSTOP-d$TSTART))>1e-5
  rm(expl,events,support)
  if(bad)stop('Exposure/event splitting failed: see 01_population_and_split_integrity.csv')
  q<-do.call(rbind,splits);rownames(q)<-NULL
  if(nrow(q)!=sum(as.integer(qa$value[qa$check=='split_rows'])))
    stop('Split count mismatch')
  list(data=q,support=su,qa=qa)
}

# JOINT SIX-SLOPE MODEL — REUSED FOR TWO COHORTS.
# The same function is called on (a) the released full 1986-qualified cohort
# and (b) a strict sensitivity excluding both 1986-linked intervals.
# Each source x EARLY/MIDDLE/LATE group receives a separate baseline hazard
# and its own distance slope. A shared SOURCE HR is not estimated.
joint_run<-function(d,bounds,folder,minimum_events,run_ph=TRUE,within_ph=TRUE,
                     case='MAIN'){
  p<-period_split(d,bounds,folder)
  q<-p$data
# SUPPORT THRESHOLD.
# Each of the six source-period groups must have the configured minimum event
# count; otherwise no six-coefficient fit is attempted.
  if(any(p$support$events<minimum_events)){
    write_note(c(paste0('INSUFFICIENT_SOURCE_PERIOD_EVENTS (required ',minimum_events,')'),
       paste(paste(p$support$source,p$support$period,p$support$events,sep=':'),collapse='; '),
       'No six-coefficient model attempted; reduce complexity only after reviewing support.'),
       '00_SOURCE_PERIOD_SUPPORT_BLOCK.txt',folder)
    return(list(status='SUPPORT_INADEQUATE',coefs=NULL,tests=NULL,
       support=p$support,fit_rows=nrow(q),warnings='Insufficient source-period events'))
  }
  for(lev in levels6)q[[paste0('Z_',lev)]]<-ifelse(q$SRC_PERIOD==lev,q$Z,0)
  q$Z_SF<-ifelse(q$SRC_PRE==0L,q$Z,0)
  q$Z_PRE<-ifelse(q$SRC_PRE==1L,q$Z,0)
# REFERENCE VERSUS TIME-VARYING SOURCE SLOPES.
# Reference fit has one slope for each source shared across periods, with
# separate source-period baseline hazards. It is NOT the final six-slope fit.
  ref<-fit_cox(survival::Surv(TSTART,TSTOP,EVENT)~Z_SF+Z_PRE+
      strata(SRC_PERIOD)+cluster(PLACE_ID),q,for_ph=FALSE)
  if(ref$fit$n!=nrow(q)||ref$fit$nevent!=sum(d$EVENT))
    stop('Reference Cox dropped observations/events')
  write_file(get_coefs(ref$fit,'SOURCE_SLOPES_CONSTANT_BY_PERIOD'),
      '10_reference_source_coefficients.csv',folder)
  ref_ll<-as.numeric(tail(ref$fit$loglik,1L));ref_warn<-ref$warnings
  rm(ref);invisible(gc(FALSE))
# FINAL HISTORICAL SCIENTIFIC MODEL.
# Surv(TSTART,TSTOP,EVENT) ~ six source-period-specific Z slopes
# + strata(SRC_PERIOD) + cluster(PLACE_ID), with Efron ties.
# Z = log1p(interval-start DIST_ACTIVE_CURR metres / 1000).
# Coefficients are conditional historical associations, not held-out scores.
  form<-stats::as.formula(paste0('survival::Surv(TSTART,TSTOP,EVENT) ~ ',
    paste(paste0('Z_',levels6),collapse=' + '),
    ' + strata(SRC_PERIOD) + cluster(PLACE_ID)'))
  full<-fit_cox(form,q,for_ph=isTRUE(run_ph),allow_warning=TRUE)
  fit<-full$fit
  if(fit$n!=nrow(q)||fit$nevent!=sum(d$EVENT))
    stop('Joint Cox dropped observations/events')
  coef_names<-paste0('Z_',levels6)
  b<-stats::coef(fit);V<-stats::vcov(fit)
  if(!setequal(names(b),coef_names))stop('Joint Cox did not estimate all six slopes')
  b<-b[coef_names];V<-V[coef_names,coef_names,drop=FALSE]
  ct<-get_coefs(fit,'JOINT_SOURCE_PERIOD')
  ct<-ct[match(coef_names,ct$term),,drop=FALSE]
  ct$source<-rep(c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN'),3L)
  ct$period<-rep(eras,each=2L)
# S21 GENERATING EXPORT.
# This file is generated in BOTH 03_Joint_Source_Period and
# 04_NO1986_Sensitivity. The publication must cite the MAIN folder's output
# if reporting the released full-cohort model; the sensitivity uses the
# separate folder's file with the SAME BASENAME.
  write_file(ct,'11_joint_six_source_period_coefficients.csv',folder)
  sf_con<-list(c(Z_SF_MIDDLE=1,Z_SF_EARLY=-1),c(Z_SF_LATE=1,Z_SF_EARLY=-1))
  pr_con<-list(c(Z_PRE_MIDDLE=1,Z_PRE_EARLY=-1),c(Z_PRE_LATE=1,Z_PRE_EARLY=-1))
# S22 ROBUST TEMPORAL AND SOURCE HYPOTHESES.
# Joint four-df change across source-specific period slopes; separate two-df
# within-source temporal changes; one-df pre-existing versus SF contrast
# within each elapsed period. Uses the cluster-robust covariance matrix.
  tests<-rbind(
    wald(b,V,c(sf_con,pr_con),'ALL_TEMPORAL_CHANGES_BOTH_SOURCES'),
    wald(b,V,sf_con,'SF_TEMPORAL_CHANGES'),
    wald(b,V,pr_con,'PRE_TEMPORAL_CHANGES'))
  for(e in eras){
    v<-setNames(c(1,-1),c(paste0('Z_PRE_',e),paste0('Z_SF_',e)))
    tests<-rbind(tests,wald(b,V,list(v),paste0('PRE_VS_SF_',e)))
  }
# S22 GENERATING EXPORT.
# As with the six-coefficient file, this basename is duplicated in the MAIN
# and NO1986 run subdirectories; retain relative path in run manifest.
  write_file(tests,'12_robust_wald_temporal_and_source_tests.csv',folder)
  individual<-list()
  for(src in c('SF','PRE'))for(era in c('MIDDLE','LATE')){
    v<-setNames(c(1,-1),c(paste0('Z_',src,'_',era),paste0('Z_',src,'_EARLY')))
    x<-unname(sum(b[names(v)]*v));se<-sqrt(as.numeric(t(v)%*%V[names(v),names(v)]%*%v))
    individual[[length(individual)+1L]]<-data.frame(source=src,
      contrast=paste(era,'MINUS EARLY'),beta_difference=x,robust_se=se,
      lower_95=x-1.96*se,upper_95=x+1.96*se,
      p_robust_1df=stats::pchisq((x/se)^2,1,lower.tail=FALSE))
  }
  write_file(do.call(rbind,individual),'12_individual_period_slope_contrasts.csv',folder)
# FIT COMPARISON QUALIFICATION.
# Partial log-likelihood gains are descriptive; a conventional LRT cannot
# replace the robust Wald inference under clustered observations.
  ll<-as.numeric(tail(fit$loglik,1L))
  write_file(data.frame(reference_loglik=ref_ll,joint_loglik=ll,
    twice_loglik_gain_descriptive_only=2*(ll-ref_ll),
    robust_joint_Wald_p=tests$robust_p[1],
    note='LRT is not cluster robust; use PLACE_ID robust Wald test for temporal inference'),
    '14_reference_vs_joint_comparison.csv',folder)
  write_file(data.frame(model=c('SOURCE_SLOPES_CONSTANT_BY_PERIOD','SIX_SOURCE_PERIOD_SLOPES'),
    n_original=nrow(d),n_split=nrow(q),events=sum(d$EVENT),
    status='COEFFICIENTS_FINITE',
    warnings=c(paste(ref_warn,collapse=' | '),paste(full$warnings,collapse=' | ')),
    partial_loglik=c(ref_ll,ll)),
    '15_model_fit_integrity.csv',folder)
# JOINT PH AND WITHIN-SOURCE-PERIOD DIAGNOSTICS.
# Main analysis can produce 20_joint_PH.csv and 21_within_source_period_PH.csv.
# A diagnostic failure need not mean that the fitted six-slope coefficients
# or robust contrasts are non-finite. NO1986 disables PH in its joint_run call.
  joint_ph_status<-'NOT_REQUESTED'
  if(isTRUE(run_ph)){
    r<-ph_csv(fit,'JOINT_SOURCE_PERIOD',folder,transform='identity')
    joint_ph_status<-if(all(r$status=='NUMERIC_PH_TEST'))'COMPLETED' else 'DIAGNOSTIC_FAILED'
    write_file(r,'20_joint_PH.csv',folder)
  }else{
    write_file(data.frame(term='NOT_RUN',status='RunJointPH=FALSE'),
      '20_joint_PH.csv',folder)
  }
  full_warnings<-full$warnings
  rm(fit,full);invisible(gc(FALSE))
  within_status<-'NOT_REQUESTED'
  if(isTRUE(within_ph)){
    rows<-list()
    for(lev in levels6){
      sub<-q[q$SRC_PERIOD==lev,c('TSTART','TSTOP','EVENT','Z','PLACE_ID'),drop=FALSE]
      z<-tryCatch(fit_cox(survival::Surv(TSTART,TSTOP,EVENT)~Z+cluster(PLACE_ID),
            sub,for_ph=TRUE),error=function(e)e)
      if(inherits(z,'error')){
        rows[[length(rows)+1L]]<-data.frame(source_period=lev,n=nrow(sub),
          events=sum(sub$EVENT),chisq=NA_real_,p=NA_real_,
          status=paste0('FIT_ERROR: ',conditionMessage(z)))
      }else{
        ph<-ph_csv(z$fit,paste0('WITHIN_',lev),folder,transform='identity')
        ix<-which(ph$term=='Z')
        rows[[length(rows)+1L]]<-data.frame(source_period=lev,n=nrow(sub),
          events=sum(sub$EVENT),chisq=if(length(ix))ph$chisq[ix[1L]] else NA_real_,
          p=if(length(ix))ph$p[ix[1L]] else NA_real_,
          status=if(length(ix))ph$status[ix[1L]] else 'PH_UNAVAILABLE')
      }
      rm(sub,z);invisible(gc(FALSE))
    }
    ph_within<-do.call(rbind,rows)
    write_file(ph_within,'21_within_source_period_PH.csv',folder)
    within_status<-if(all(ph_within$status=='NUMERIC_PH_TEST'))'COMPLETED' else 'PARTIAL_DIAGNOSTIC_FAILURE'
  }
  write_file(data.frame(joint_PH_status=joint_ph_status,within_PH_status=within_status,
      model_warnings=paste(full_warnings,collapse=' | ')),
    '22_joint_PH_execution_QA.csv',folder)
  list(status=if(length(full_warnings))'COEFFICIENTS_FINITE_WARNINGS_REVIEW' else 'FITTED',
       coefs=ct,tests=tests,support=p$support,fit_rows=nrow(q),
       warnings=paste(full_warnings,collapse=' | '))
}

# MAIN PROCESSING BRANCH.
# Independent preflight validates released column names, final cohort counts,
# source class and event support, finite elapsed exposure and unique IDs.
# The run writes an explicit FAILED marker on fatal errors.
tryCatch({
  if(!is.finite(num(MinimumEventsPerSourcePeriod))||
     num(MinimumEventsPerSourcePeriod)<1L)stop('MinimumEventsPerSourcePeriod must be >= 1')
  minimum_events<-as.integer(num(MinimumEventsPerSourcePeriod))
# AUTHORITATIVE RELEASE LAYER.
# Only released FP->AD event and eligibility fields are queried; this script
# does not rebuild any organisational states, risk sets or channel geometry.
  table_layer<-'T2_FP_AD_Threshold_Reconciled'
  require_layer(source_path,table_layer)
  required<-c('PLACE_ID','BLOCK_ID','y1','y2','tstart_yr','tstop_yr',
    'T1_SOURCE','DIST_ACTIVE_CURR','T2_BINARY_OUTCOME_ADJ',
    'ORIGINAL_FP_EVENT','FIT_ELIGIBLE_LOCAL_1986','THRESHOLD_RELEASED')
  fields<-names(read_table(source_path,paste0('SELECT * FROM ',qsql(table_layer),' LIMIT 1')))
  if(length(setdiff(required,fields)))
    stop('Required released fields missing: ',paste(setdiff(required,fields),collapse=', '))
# ELIGIBILITY AND OUTCOME FILTER.
# FIT_ELIGIBLE_LOCAL_1986=1 is the locally qualified, released population;
# T2_BINARY_OUTCOME_ADJ must be a resolved binary outcome.
# Pre-existing FP and SF are the only allowed sources; DS is excluded.
  sql<-paste0('SELECT ',paste(qsql(required),collapse=','),
    ' FROM ',qsql(table_layer),
    ' WHERE "FIT_ELIGIBLE_LOCAL_1986"=1 AND "T2_BINARY_OUTCOME_ADJ" IN (0,1)')
  raw<-read_table(source_path,sql)
# OBSERVATION-TIME MODEL FIELDS.
# TSTART/TSTOP are elapsed observation-time coordinates; EVENT comes from
# released binary adjudication; source is T1_SOURCE; Z is interval-start
# Active-Domain distance in km transformed by log1p.
  d<-data.frame(PLACE_ID=as.character(raw$PLACE_ID),
      TSTART=num(raw$tstart_yr),TSTOP=num(raw$tstop_yr),
      EVENT=as.integer(num(raw$T2_BINARY_OUTCOME_ADJ)),
      SRC=toupper(trimws(as.character(raw$T1_SOURCE))),
      Z=log1p(num(raw$DIST_ACTIVE_CURR)/1000),
      y1=num(raw$y1),y2=num(raw$y2))
  rm(raw);invisible(gc(FALSE))
  d$SRC_PRE<-as.integer(d$SRC=='PREEXISTING_FLOODPLAIN')
  if(nrow(d)!=expected$main_rows||sum(d$EVENT)!=expected$main_events)
    stop('Main population changed: expected 1,001,403 rows and 8,350 events; got ',
      nrow(d),' rows and ',sum(d$EVENT),' events')
  if(anyNA(d)||any(!is.finite(d$TSTART))||any(!is.finite(d$TSTOP))||
      any(!is.finite(d$Z))||any(d$Z<0)||any(d$TSTOP<=d$TSTART)||
      any(!d$EVENT%in%c(0L,1L))||
      any(!d$SRC%in%c('STABILISED_FLOODPLAIN','PREEXISTING_FLOODPLAIN'))||
      any(!nzchar(d$PLACE_ID)))stop('Invalid source, event, exposure, key or T1 covariate')
  if(sum(d$EVENT[d$SRC_PRE==1L])!=expected$pre_events||
     sum(d$EVENT[d$SRC_PRE==0L])!=expected$sf_events)
    stop('T1 source event assignment differs from the released final rolling P1/P2 model')
  dates_key<-paste(d$PLACE_ID,format(d$TSTART,digits=15,scientific=FALSE,trim=TRUE),sep='#')
  if(anyDuplicated(dates_key))stop('Duplicate PLACE_ID and interval start; abort')
  rm(dates_key);invisible(gc(FALSE))
  write_file(data.frame(n=nrow(d),events=sum(d$EVENT),
      PRE_events=sum(d$EVENT[d$SRC_PRE==1L]),
      SF_events=sum(d$EVENT[d$SRC_PRE==0L]),
      unique_places=length(unique(d$PLACE_ID)),min_TSTART=min(d$TSTART),
      max_TSTOP=max(d$TSTOP),place_years=sum(d$TSTOP-d$TSTART),
      input_geoPackage=source_path), '01_population_QA.csv',f_target)
# REPRODUCTION GUARD AGAINST THE PRIOR MODEL.
# The reference result file 10_historic_cox_main_and_no1986.csv must exist.
# A new distance-only fit must recover the prior rounded log-distance beta
# (-26.43705, tolerance 0.05) before the source-period fit proceeds.
  note_ref<-file.path(history_root,'10_historic_cox_main_and_no1986.csv')
  if(!file.exists(note_ref))stop('OriginalHistoricalOutputFolder lacks 10_historic_cox_main_and_no1986.csv')
  # The raw log-distance beta is expected -26.43705 from the completed v1.0.1
  # main historical fit. Refit is an INDEPENDENT data/estimand integrity guard.
  message('[Mamoré PH] Fitting original distance-only historical model')
  distance<-fit_cox(survival::Surv(TSTART,TSTOP,EVENT)~Z+cluster(PLACE_ID),d,for_ph=TRUE)
  write_file(get_coefs(distance$fit,'MAIN_DISTANCE_ONLY'),'10_historic_distance_refit_coefficients.csv',f_target)
  p1_beta<-as.numeric(stats::coef(distance$fit)[['Z']])
  agreement<-is.finite(p1_beta)&&abs(p1_beta-(-26.43705))<0.05
  write_file(data.frame(model='MAIN_DISTANCE_ONLY',
    prior_beta_raw_logkm_rounded=-26.43705,refit_beta_raw_logkm=p1_beta,
    absolute_difference=abs(p1_beta+26.43705),
    status=if(agreement)'MATCH_PRIOR_ROUNDED_BETA' else 'DIFFERENCE_REQUIRES_REVIEW',
    fit_n=distance$fit$n,fit_events=distance$fit$nevent,
    source_file=note_ref,warnings=paste(distance$warnings,collapse=' | ')),
    '10_PH_refit_integrity.csv',f_target)
  phs<-list(ph_csv(distance$fit,'MAIN_DISTANCE_ONLY',f_target,'km'))
  rm(distance);invisible(gc(FALSE))
  if(!agreement)stop('Original historical distance raw-beta refit does not match prior (-26.43705; tolerance 0.05). See 10_PH_refit_integrity.csv. Stop before period-specific inference.')

  # For cross-river comparability run BOTH forms used in Jamuna:
  # ordinary source interaction (one baseline) and source-stratified slopes.
# TARGETED PH COMPARISONS.
# Optional full-source interaction tests a common-baseline alternative.
# The source-stratified model then tests separate source slopes; neither
# should be conflated with the six-source-by-period main model.
  if(isTRUE(RunFullSourceInteractionPH)){
    message('[Mamoré PH] Fitting full source interaction')
    one<-tryCatch(fit_cox(survival::Surv(TSTART,TSTOP,EVENT)~
          Z+SRC_PRE+Z:SRC_PRE+cluster(PLACE_ID),d,for_ph=TRUE),error=function(e)e)
    if(inherits(one,'error')){
      phs[[length(phs)+1L]]<-data.frame(model='SOURCE_INTERACTION',term='PH_FAILED',
        chisq=NA_real_,df=NA_real_,p=NA_real_,transform='km',status='REFIT_FAILED',
        warning=conditionMessage(one))
    }else{
      write_file(get_coefs(one$fit,'SOURCE_INTERACTION'),
        '11_full_source_interaction_coefficients.csv',f_target)
      phs[[length(phs)+1L]]<-ph_csv(one$fit,'SOURCE_INTERACTION',f_target,'km')
    }
    rm(one);invisible(gc(FALSE))
  }
  message('[Mamoré PH] Fitting source-stratified distance slopes')
  d$Z_SF<-ifelse(d$SRC_PRE==0L,d$Z,0)
  d$Z_PRE<-ifelse(d$SRC_PRE==1L,d$Z,0)
  tw<-fit_cox(survival::Surv(TSTART,TSTOP,EVENT)~Z_SF+Z_PRE+
        strata(SRC)+cluster(PLACE_ID),d,for_ph=TRUE)
  write_file(get_coefs(tw$fit,'SOURCE_STRATIFIED_SOURCE_SLOPES'),
      '11_source_stratified_distance_slopes.csv',f_target)
  phs[[length(phs)+1L]]<-ph_csv(tw$fit,'SOURCE_STRATIFIED',f_target,'km')
  rm(tw);d$Z_SF<-NULL;d$Z_PRE<-NULL;invisible(gc(FALSE))
  ph_all<-do.call(rbind,phs)
  write_file(ph_all,'20_PH_tests.csv',f_target)
  ph_failures<-sum(ph_all$status!='NUMERIC_PH_TEST')
  write_file(subset(ph_all,model=='SOURCE_STRATIFIED'),
    '20_full_stratified_interaction_PH.csv',f_temporal)

  # Equal THIRDS of observation-time exposure support, analogous in concept
  # (NOT identical calendar boundaries) to Jamuna's 12.342 / 24.683 yrs.
# ELAPSED-TIME PERIODS.
# Defaults divide the available Mamore elapsed record into equal thirds;
# optional manual cuts must both be supplied. Actual observation intervals
# are split at those elapsed-year boundaries. These are NOT calendar-thirds
# shared with Jamuna, whose independent thresholds differ.
  min_t<-min(d$TSTART);max_t<-max(d$TSTOP)
  bounds<-c(min_t,min_t+(max_t-min_t)/3,min_t+2*(max_t-min_t)/3,max_t)
  custom1<-num(FirstPeriodCutElapsedYears);custom2<-num(SecondPeriodCutElapsedYears)
  if(xor(custom1>=0,custom2>=0))stop('Both period cuts must be -1 or both positive')
  if(custom1>=0&&custom2>=0)bounds[2:3]<-c(custom1,custom2)
  if(!all(diff(bounds)>0))stop('Temporal period cuts must be strictly inside original range')
  write_file(data.frame(period=eras,start_elapsed=bounds[1:3],end_elapsed=bounds[2:4],
    rule=if(custom1>=0)'USER_DEFINED_ABSOLUTE_ELAPSED_CUTS' else 'EQUAL_ELAPSED_THIRDS',
    comparison='Jamuna thirds are NOT equal calendar years to Mamoré thirds'),
    '00_period_specification.csv',f_temporal)
  write_note(c('NO PERIOD INPUT USES FUTURE OUTCOME LABELS',
    paste('Historical elapsed time range:',min_t,'to',max_t),
    paste('Boundaries:',paste(signif(bounds,12),collapse='; ')),
    'Separate source-period baselines; no constant source hazard ratio estimated.',
    'PH cox.zph scores are not cluster-robust; Wald contrasts use robust PLACE_ID covariance.'),
    '00_METHOD_NOTES.txt',f_temporal)

  message('[Mamoré temporal] Source-period joint model, MAIN 1986-qualified cohort')
# MAIN, RELEASED-COHORT HISTORICAL FIT.
# This is the authoritative full-cohort file destination for S21-S22,
# provided the publication's frozen figures match the recorded results.
  main<-joint_run(d,bounds,f_joint,minimum_events,
    run_ph=TRUE,within_ph=isTRUE(RunWithinSourcePeriodPH),case='MAIN')
  if(!is.null(main$coefs)){
    write_file(data.frame(model_period=paste(main$coefs$period,
      ifelse(main$coefs$source=='STABILISED_FLOODPLAIN','SF','PRE'),sep='_'),
      source=main$coefs$source,beta=main$coefs$beta,
      robust_se=main$coefs$robust_se,lower_95=main$coefs$lower_95,
      upper_95=main$coefs$upper_95,HR_per_unit_Z=main$coefs$HR_per_unit_log1p_km),
      '31_epoch_source_distance_slopes.csv',f_temporal)
  }

  sens_status<-'NOT_REQUESTED'
# CONSERVATIVE 1986 EXCLUSION.
# Exclude both 1985-1986 and 1986-1988 observation intervals, not just
# places south of the analyst-attested cutoff. The re-fitted sensitivity has
# 57,062 fewer rows and 866 fewer events than the full cohort.
# Because only early intervals are removed, changes may concentrate in
# EARLY slopes, while MIDDLE and LATE point estimates remain unchanged.
  if(isTRUE(RunNO1986Sensitivity)){
    no86<-!(d$y1==19850101 & d$y2==19860101 |
            d$y1==19860101 & d$y2==19880101)
    dx<-d[no86,,drop=FALSE]
    if(nrow(dx)!=expected$no1986_rows||sum(dx$EVENT)!=expected$no1986_events)
      stop('NO1986 population differs from audited 944,341 rows / 7,484 events; STOP')
    write_file(data.frame(main_rows=nrow(d),main_events=sum(d$EVENT),
      no1986_rows=nrow(dx),no1986_events=sum(dx$EVENT),
      removed_rows=nrow(d)-nrow(dx),removed_events=sum(d$EVENT)-sum(dx$EVENT),
      excluded_intervals='1985-1986;1986-1988',
      evidence_1986='analyst-attested qualification; not independent imagery footprint'),
      '00_NO1986_population_and_rule.csv',f_sens)
    message('[Mamoré temporal] Conservative NO1986 source-period sensitivity')
# SENSITIVITY FIT OUTPUT DIRECTORY.
# Write a second 11_joint_six_source_period_coefficients.csv and
# 12_robust_wald_temporal_and_source_tests.csv under 04_NO1986_Sensitivity.
# Do NOT accidentally use these as the full-population S21-S22 source.
    sen<-joint_run(dx,bounds,f_sens,minimum_events,
         run_ph=FALSE,within_ph=FALSE,case='NO1986')
    sens_status<-sen$status
    if(!is.null(main$coefs)&&!is.null(sen$coefs)){
      ix<-match(main$coefs$term,sen$coefs$term)
      write_file(data.frame(term=main$coefs$term,source=main$coefs$source,
        period=main$coefs$period,main_beta=main$coefs$beta,
        no1986_beta=sen$coefs$beta[ix],
        no1986_minus_main_beta=sen$coefs$beta[ix]-main$coefs$beta,
        main_robust_se=main$coefs$robust_se,no1986_robust_se=sen$coefs$robust_se[ix],
        caveat='Different risk/event populations; coefficient changes are sensitivity not causal effects'),
# DIRECT MAIN-VERSUS-SENSITIVITY RECONCILIATION.
# This exported side-by-side difference table is the clearest way to
# identify why early-period slopes may differ between versions of S21.
        '30_main_vs_NO1986_source_period_slopes.csv',f_sens)
      write_file(data.frame(main_temporal_robust_p=main$tests$robust_p[1],
        no1986_temporal_robust_p=sen$tests$robust_p[1],
        main_events=sum(d$EVENT),no1986_events=sum(dx$EVENT)),
        '30_main_vs_NO1986_temporal_wald.csv',f_sens)
    }
    rm(dx,no86,sen);invisible(gc(FALSE))
  }
# RUN-SPECIFICATION MANIFEST.
# The 90_frozen_scientific_specification.csv records input, released cohort,
# distance scale, separate source-period baselines, PH transforms, elapsed
# period cuts, 1986 evidential status, and lack of rolling refitting.
  write_file(data.frame(parameter=c('river','transition','input','historical_reference',
    'main_risk_rows','main_events','source_PRE_events','source_SF_events',
    'original_time_basis','covariate','baseline','robust_uncertainty',
    'PH_transform_full','PH_transform_joint','period_rule',
    'period_cut_1','period_cut_2','main_fit_status','NO1986_fit_status',
    '1986_evidence','rolling_prediction_refit'),
    value=c('Mamore','FP_to_AD',source_path,history_root,nrow(d),sum(d$EVENT),
      sum(d$EVENT[d$SRC_PRE==1]),sum(d$EVENT[d$SRC_PRE==0]),
      'Absolute TSTART/TSTOP elapsed study years',
      'Z=log1p(DIST_ACTIVE_CURR_m/1000) using T1 nominal ACTIVE distance',
      'Separate SOURCE x PERIOD baseline hazards','cluster(PLACE_ID) robust sandwich',
      'km','identity',if(custom1>=0)'User cuts' else 'Equal elapsed thirds',
      bounds[2],bounds[3],main$status,sens_status,
      'Analyst-attested 1986 north-of-truncation coverage; NO1986 separate',
      'NO: all P1/P2 rolling forecasts unchanged')),
    '90_frozen_scientific_specification.csv',run_root)
  status<-if(is.null(main$coefs))'COMPLETED_WITH_SOURCE_PERIOD_SUPPORT_LIMITATION' else
    if(ph_failures>0L)'COMPLETED_WITH_PH_DIAGNOSTIC_FAILURES' else 'COMPLETED'
# FINAL STATUS AND INTEGRITY MARKERS.
# A COMPLETED_WITH_PH_DIAGNOSTIC_FAILURES marker may coexist with a fitted
# joint source-period model; see individual 20/21 PH QA rather than treating
# all model parameters as failed. No prediction or polygon layers are updated.
  write_note(c(status,as.character(Sys.time()),
     paste0('output=',run_root),paste0('main_model_rows=',nrow(d)),
     paste0('authoritative_events=',sum(d$EVENT)),
     paste0('temporal_support_status=',main$status),
     paste0('full_history_PH_diagnostic_failures=',ph_failures),
     paste0('NO1986_status=',sens_status),
     if(!agreement)'CAUTION: distance-only refit differs from prior rounded beta; investigate before publication' else
       'Distance-only raw-beta reproduction MATCH_PRIOR_ROUNDED_BETA',
     'Models are historical; no rolling predictions or 5c2/5d files were modified.'),
     '00_RUN_COMPLETED.txt',run_root)
  message('[Mamoré PH temporal] ',status,': ',run_root)
},error=function(e){
  write_note(c('FAILED',as.character(Sys.time()),conditionMessage(e),
      'Outputs already generated are diagnostic partial results; do not treat as complete.'),
      '00_RUN_FAILED.txt',run_root)
  stop(e)
})
