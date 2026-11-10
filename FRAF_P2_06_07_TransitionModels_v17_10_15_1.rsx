##FRAF Floodplain Reassemblage=group
##KM AG Cox State v17.10.15.1 - Mamore DSAD Reduced-History Alignment=name
##RiskTable=file
##RiskLayerName=string Risk Table
##OutputFolder=folder
##ReachName=selection Mamoré;Jamuna
##MamoreReactivationExposure=selection Full-width channel-margin zone;Half-width channel-margin zone
##MamoreStorageExposure=selection Half-width bank-adjacent zone;Full-width bank-adjacent zone
##RunKM=boolean TRUE
##RunAG=boolean TRUE
##RunCox=boolean TRUE
##RunStorageReworkInterpretive=boolean TRUE
##RunPHDiagnostics=boolean TRUE
##RunTemporalSensitivity=boolean TRUE
##StrictTemporalAlignment=boolean TRUE
##RunUnionComparison=boolean FALSE
##PureStateMinSupport=number 0.90
##RunDefinitionSensitivity=boolean TRUE
##RunSemanticContrastQA=boolean TRUE
##WriteDetailedStorageAudit=boolean FALSE
##ExportSpatialSummary=boolean FALSE
##PlacePolygons=optional vector
##AnalysisMode=selection Historic only;Prediction only
##RunBroadFloodplainPrediction=boolean TRUE
##MamoreDSADPrincipalSpatialModel=selection Linear previous-channel-margin;Linear previous-channel-margin + curvature
##RunMamoreDSADVariantComparison=boolean TRUE
##MamoreDSADDistalThresholdM=number 1000
##MamoreDSADExceptionalIntervalMinEvents=number 25
##MamoreDSADExceptionalIntervalMinFraction=number 0.18
##ForecastOrigins=string 10,20,30
##OriginInterpretation=selection Unique interval-start rank;Elapsed study year
##MinimumTrainingEvents=number 20
##WriteParquet=boolean TRUE
##WriteFullFittedPredictions=boolean FALSE
##FutureCovariateTable=optional file
##FutureLayerName=string Risk Table
##FutureStartTime=number -1
##FutureStopTime=number -1
# =============================================================================
# FRAF PAPER 2 SOURCE ARCHIVE | 06_07 - TRANSITION MODELS | v17.10.15.1
# =============================================================================
# Archive filename: FRAF_P2_06_07_TransitionModels_v17_10_15_1.rsx
# Original filename: FRAF_v17_10_15_1_Mamore_DSAD_Final.rsx
# Archive action: explanatory comments and file rename ONLY; no logic changes.
# Scope: retrospective transition/persistence analyses (06) AND independent
#        rolling-origin / future transition-risk prediction analyses (07).
# Runtime: QGIS Processing R provider with compatible R and required R packages.
# The QGIS Processing ## parameter header above, registered algorithm name,
# inputs, defaults, numerical operations and output schemas are preserved.
#
# RECONSTRUCTED STATES (Module 3B is authoritative for modelling endpoints):
#   AD = ACTIVE_DOMAIN; DS = DEPOSITIONAL_STORAGE;
#   SF = STABILISED_FLOODPLAIN.
#   UNRESOLVED denotes insufficient state evidence, not a fourth state.
#
# PROCESS-TRANSITION RISK POPULATIONS:
#   SF -> AD : stabilised-floodplain reactivation.
#   AD -> DS : active-domain transition to depositional storage.
#   DS -> SF : depositional-storage stabilisation.
#   DS -> AD : depositional-storage reworking into active occupation.
#   SF -> DS : floodplain-to-storage transition (where modelled/described).
# Broad eligible FP -> AD is a separate prediction population: qualifying
# pre-existing floodplain plus SF; it EXCLUDES DS. FP is not an extra state,
# and the broad risk population is not identical to the fixed INIT_FP cohort.
#
# DATA LINEAGE:
#   Stage 4 Step 3 risk table is the authoritative non-spatial interval panel.
#   Module 3B supplies observed/latent endpoint states and primary bridged
#   event/risk flags; Module 4a/Stage 4 Step 2 supply contextual assemblage
#   history and spatial covariates; the risk table combines these inputs.
#   *_PRIMARY supports ambiguity bridging; strict and pure-state definitions
#   supply alternative sensitivity populations. Their scopes are not pooled.
#
# TEMPORAL INTEGRITY:
#   Covariates labelled *_PREV are constructed from knowledge available by
#   interval start. Dated spatial geometry is selected at/before that start.
#   Prediction scalers/fits are estimated on training intervals only; held-out
#   intervals must not influence their own fitting or preprocessing.
#   Full-record descriptive quantities are not substitutes for interval-start
#   covariates. Distances and curvature depend on the river-specific mapping.
#
# EXECUTION / OUTPUT:
#   AnalysisMode = Historic only OR Prediction only, in SEPARATE R processes.
#   Historic branch: KM, Andersen-Gill / interval hazards, explanatory Cox,
#   proportional-hazards diagnostics, definition/temporal sensitivity, QA.
#   Prediction branch: transition-specific Cox recipes, rolling-origin tests,
#   out-of-sample occurrence and ranked-area metrics, frozen final fits, and
#   optional next-interval forecasts from a separate covariate table.
#   Dedicated completion/failure markers and CHATGPT_REVIEW_PACK support audit.
#   The optional union-area comparison is off by default for memory safety.
#
# v17.10.15.1 SPECIFICATION FREEZE:
#   Mamore DS -> AD Historic and Prediction share the Step-3D-reduced history
#   terms and the selected linear previous-margin spatial specification.
#   The four fixed exceptional intervals enter only the sensitivity comparison;
#   principal all-history fit remains uncut. Other source model specifications
#   are unchanged by this commenting pass.
#
# Interpretation: Cox coefficients describe conditional associations over the
# observation record, not universal physical laws; PH violations can restrict
# coefficient-level inference. Forecast skill is separately held-out tested.
#
# Archive provenance note: this file documents the exact supplied v17.10.15.1
# source. It is not an independent scientific revalidation or a QGIS/R test.
# =============================================================================
# v17.10.15.1 FINAL MAMORE DS->AD REDUCED-HISTORY ALIGNMENT PATCH (24-9-26)
# - Mamore DS->AD Historic and Prediction principal models now use the same
#   Step-3D-selected reduced ASM-history set:
#     ASM_DOM_RATIO_PREV_Z + ASM_COV_FRAC_Z +
#     ASM_STORAGE_FRAC_PREV_Z + ASM_QUIET_SINCE_PREV_Z +
#     ASM_N_STORAGE_EVT_PREV_Z.
#   ASM_N_EPISODES_PREV_Z and ASM_MAX_QUIET_PREV_Z are excluded specifically
#   from Mamore DS->AD; other transition specifications are unchanged.
# - The Mamore DS->AD four-model sensitivity comparison (M1-M4) uses the same
#   reduced history terms as the principal model.
# - The no-cutoff sensitivity is locked to the four Step-3D exceptional intervals
#   (rounded to 6 decimals): 2.002740->4.002740, 7.005479->8.005479,
#   15.010959->16.010959, and 29.021918->30.021918.
#   Threshold-based detection is retained as QA only and no longer determines
#   which intervals are removed from the sensitivity analysis.
# - Principal Historic/Prediction DS->AD training remains ALL-HISTORY; cutoff
#   exclusion remains a mechanism-identification sensitivity only.
# - Active run/completion/version markers updated to v17.10.15.1.
# ============================================================
# v17.10.15.0 MODEL-ALIGNMENT PATCH (24-9-26)
# - Historic Jamuna SF->AD and DS->AD are aligned with the selected prediction
#   specification: linear active-domain-margin distance; ASM_N_EPISODES_PREV_Z
#   removed from these two Jamuna history sets; ASM_N_REACTIVATE_PREV_Z is not
#   reintroduced into Jamuna SF->AD.
# - Historic Mamore DS->AD principal spatial term is linear DIST_CHANNEL_PREV.
#   A QGIS selector can promote linear margin + curvature after triage; the same
#   choice is used by Historic and Prediction modes.
# - Historic Mamore DS->AD can fit the all-history/no-cutoff x with/without
#   curvature four-variant family plus the legacy local-geometry comparator in
#   one run, with lightweight AIC/concordance/coefficient/PH exports.
# - Broad FP->AD prediction is spatial-only and uses active-domain distance,
#   matching the historical broad model rationale; requested broad prediction
#   now fails preflight if its authoritative Stage-4 fields are absent instead
#   of being silently omitted.
# - Active run/completion/version markers are normalised to v17.10.15.0.
# ============================================================
# v17.10.14.6 MEMORY-CLEAN PRODUCTION PATCH (23-9-26)
# - Scientific specification is unchanged from v17.10.14.5.
# - Removes the temporary v17.10.14.4 08ab/08ac broad-FP diagnostic machinery
#   from routine production; those diagnostics established the final spatial-only
#   historical Eligible FP->AD Cox specification and are no longer re-fitted.
# - Retains authoritative broad risk/eligibility QA, source decomposition, 08aa
#   Cox-frame coverage assertion, spatial-only broad Cox, strict SF->AD and DS->AD
#   final specifications, PH safeguards, and the existing prediction recipes.
# - Extends post-historic cleanup to explicitly release broad diagnostic/transient
#   objects and runs full garbage collection before review-package assembly.
# - No observations are thinned or dropped for memory reasons; risk/event/model
#   definitions and fitted scientific specifications are unchanged from 14.5.
# ============================================================
# v17.10.14.5 PRODUCTION PATCH (23-9-26)
# - Retains the corrected authoritative Eligible FP->AD population introduced
#   in v17.10.14.2/3: FP_REACTIVATE_RISK_SET_PRIMARY AND
#   FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY, including qualifying pre-existing FP.
# - Historical broad Eligible FP->AD Cox is now SPATIAL-ONLY.  The v17.10.14.4
#   diagnostics showed that the full broad history model overflows when
#   ASM_DOM_RATIO_PREV_Z and ASM_N_EPISODES_PREV_Z are combined across SF and
#   PREEXISTING_FLOODPLAIN.  These history variables do not have equivalent
#   observational meaning for left-censored pre-existing FP.
# - Broad KM/transition analysis, source QA, and the existing broad predictive
#   recipe are retained.  Strict SF->AD and DS->AD inferential/predictive model
#   specifications are unchanged.
# - v17.10.14.4 source/covariate diagnostics are retained as reproducibility QA.
# ============================================================
# v17.10.14.4 PATCH (22-9-26)
# - Fixes Mamore FINAL_FULL_RECORD fit-only failure:
#   "replacement has 1 row, data has 0".
# - Cause: build_transformed() assigned scalar NA_real_ to the deliberately
#   zero-row final-model target when a candidate predictor had no usable scale.
# - Fix is length-safe only; scientific model/risk/event specifications are
#   unchanged from v17.10.14.
# - Corrects prediction failure marker version text.
# ============================================================
# ============================================================
# 22-9-26
# v17.10.14.5 retains the final Step-3 spatial specification for the three
# principal state-specific prediction models while preserving v17.10.13 as
# the reproducible baseline. Prediction changes ONLY:
#   * Jamuna SF->AD: linear DIST_ACTIVE_CURR (train-standardised) and
#     ASM_N_EPISODES_PREV_Z removed from the candidate history set.
#   * Jamuna DS->AD: linear DIST_ACTIVE_CURR (train-standardised) and
#     ASM_N_EPISODES_PREV_Z removed; other selected storage/history terms retained.
#   * Mamore DS->AD: linear DIST_CHANNEL_PREV (train-standardised), replacing
#     near-channel/outer-bank/curvature terms in the principal prediction model.
#     All historical DS->AD intervals/events remain in production training; the
#     no-cutoff analysis remains a mechanism-identification sensitivity only.
# Expanded FP->AD is deliberately NOT changed: it retains the v17.10.13 broad
# predictive recipe because it is a distinct SF + qualifying pre-existing-FP
# target and has no representative historic broad Cox endpoint. Mamore SF->AD,
# AD->DS and DS->SF are also unchanged. Linear distance is z-standardised on
# each training window for numerical stability; this is exactly linear in raw
# distance and does not alter ranking relative to an unstandardised linear term.
# No risk-set, event, rolling-origin, validation, calibration, capture, scaling
# leakage, or future-forecast definition is otherwise changed.
#
# 4-9-26
# v17.10.13 is a Jamuna historic finalisation memory/I-O hardening release.
# The optional Full analysis area versus historical activity-belt (Section 12)
# comparison is now OFF by default because it is ancillary to the principal
# transition/KM/Cox analyses and can generate severe paging and disk I/O on
# multi-million-row Jamuna Risk Tables. When skipped, a small marker file is
# written so the omission is explicit in the Review Pack. The Section 12 code
# is retained and can still be enabled manually for a dedicated sensitivity run.
# v17.10.12 period-refit ceilings, historic Broad FP->AD analysis, aggressive
# post-historic object release, and streamed Review Pack construction are retained.
# No event, risk-set, KM, AG, Cox, predictor, or prediction definition is changed.
#
# 1-9-26
# v17.10.12 fixes two prediction-path defects exposed by the Jamuna Prediction-only run.
# First, FINAL_FULL_RECORD fit-only mode now creates zero-length prediction-time columns
# safely on its deliberately zero-row target, avoiding the R data-frame error
# "replacement has 1 row, data has 0". Second, Cox target linear predictors are computed
# directly as X beta from the frozen transformed terms and fitted coefficients rather than
# relying on predict.coxph() after memory stripping; prediction failures are now explicitly
# labelled instead of being silently converted to NA while retaining model_status=predicted.
# Scientific transition definitions, risk sets, candidate predictors, training windows and
# fitted Cox coefficients are unchanged from v17.10.9. Additional rolling QA reports both
# status-predicted rows and rows with finite predicted probabilities.
#
# 31-8-26
# v17.10.9 is a process-isolation release for large Jamuna runs. A new AnalysisMode
# parameter provides exactly two production modes: Historic only and Prediction only.
# Historic only performs the complete interpretive KM/AG/Cox/PH/sensitivity/union
# workflow, writes the historic completion marker, releases all large historic objects,
# builds the review package, and terminates without opening the prediction table.
# Prediction only bypasses the historic Risk Table load and all historic modelling, then
# starts the projected-column prediction reader in a fresh R process. This prevents R
# heap fragmentation and Windows commit pressure accumulated by the historic branch from
# carrying into prediction. Scientific historic and predictive specifications are
# unchanged from v17.10.8; only process/memory orchestration and mode-aware markers change.
#
# 31-8-26
# v17.10.8 removes the remaining Jamuna historic comparison memory spike.
# The Full analysis area versus historical activity-belt comparison is now
# summary-first: it no longer binds two complete copies of the longitudinal
# Risk Table to make T1/T2 observation rows. Strict transition-matrix eligibility
# and weighted matrix cells are calculated directly from vectors; state composition
# uses the initial T1 observation plus each interval T2 observation, which is
# algebraically identical after the already-enforced state-chain QA. Obsolete
# historic Cox/QA objects are garbage-collected before Section 12, and the full
# historic Risk Table is released before the Section 12c rate loop. The same
# primary/strict event definitions, weights, domains, rates, matrices and prediction
# specifications are retained.
#
# v17.10.7 removes the remaining Jamuna prediction entry-point memory spike.
# Before prediction begins, large historic-analysis data/model/plot objects are
# released and full garbage collection is requested. Prediction then inspects only
# a one-row GeoPackage schema and issues a SQL SELECT for the raw fields required
# by the enabled prediction engine, so the 4-million-row, 358-field Stage 4 Risk
# Table is never materialised a second time. The later compact-model narrowing,
# streamed rolling archives, lean Cox fits, fit-only final models, frozen-model
# Tn+1 reuse and failure-safe review-pack logic are retained. For non-GeoPackage
# inputs a compatibility fallback reads the source and immediately projects the
# same candidate field set. No scientific model, event, risk-set, predictor,
# fitting, validation or forecast specification is changed from v17.10.6.
#
# v17.10.6 makes review-pack generation failure-safe. Prediction errors are now
# caught at the outer predictive-branch boundary, recorded in a top-level failure
# marker, and execution proceeds far enough to build CHATGPT_REVIEW_PACK from all
# outputs already written. After the pack is built the script raises a final error
# so QGIS still reports an incomplete scientific run. The review priority-indexing
# logic is also corrected. No scientific model, event, risk-set, predictor, fitting,
# validation or memory-management specification is changed from v17.10.5.
#
# v17.10.5 is a prediction-memory hardening release. Scientific model, event,
# risk-set, predictor and validation specifications are unchanged. The predictive
# Cox fits no longer retain x/model frames; formula environments are detached from
# large local data objects; row-level prediction archives are streamed directly to
# compressed CSV; rolling objects are released before final fitting; final models
# are fitted in training-only mode; and genuine Tn+1 forecasts reuse the frozen
# full-record fit/scalers/baseline instead of refitting the model. Row-level Parquet
# materialisation is deliberately suppressed in the streaming paths because it
# would recreate the full archive in memory; compressed CSV remains authoritative.
#
# v17.10.4 incorporates the validated Mamoré reactivation prediction-model
# sensitivity result. ASM_N_REACTIVATE_PREV_Z is removed from the production
# active_domain_reactivation and floodplain_reactivation_broad prediction
# v17.10.12: adds floodplain_reactivation_broad to HISTORIC descriptive, KM, Cox and PH analyses
# v17.10.12 memory/I-O revision: retains overall broad Cox/Schoenfeld diagnostics but skips
# Early/Middle/Late period-interaction refits for the very large broad and initial-floodplain
# risk sets; final Review Pack assembly streams source files in chunks and uses a leaner
# per-file inclusion threshold to avoid whole-file RAM duplication and excessive disk I/O.
# specifications only. All other historic and predictive model specifications
# remain unchanged. binary_auc now uses double precision in the rank denominator
# for million-row full-record prediction sets. A final automatic ChatGPT review
# package stage creates upload-ready thematic text bundles without modifying
# scientific outputs.
#
# v17.10.3 suppresses the expected sf warning emitted when sf::st_read reads a
# non-spatial GeoPackage table ("no simple feature geometries present"). QGIS can
# misreport a successful long R run as failed when this deferred warning reaches
# the console at shutdown. The warning is muffled only for table reads; errors are
# unchanged. Parquet output is also disabled once at preflight when arrow is not
# installed, avoiding repeated harmless messages. No analysis, model, event, risk-set,
# sensitivity, or prediction specification is changed.
#
# 31-8-26
# v17.10.2 fixes a second QGIS Processing R-provider package-discovery issue.
# The provider scans source text naively for package-attachment syntax, including
# text inside comments. A documentation example in the v17.10.1 comments was
# therefore misread as a request for a CRAN package literally named "package".
# All comment text that resembles package-attachment syntax has been removed.
# Required namespaces are still checked generically and the real packages are
# attached below by explicit package names. No analysis, event, risk-set, model,
# sensitivity, or prediction specification is changed.
#
# 30-8-26
# v17.10 integrates the v17.8f interpretive KM/AG/total-time Cox/PH/sensitivity
# branch with the v17.9.11 rolling-origin and genuine Tn+1 prediction branch.
# It promotes Depositional Storage -> Active Domain (DS->AD; storage reworking)
# to a first-class interpretive transition: baseline/stratified KM, interval
# frequency, total-time Cox/Andersen-Gill, primary/strict/pure-state sensitivity,
# and proportional-hazards diagnostics. Prediction retains the v17.9.11 gap-time
# formulation for absolute next-interval probability. The broad floodplain
# reactivation prediction model is optional and is skipped cleanly when its
# Stage 4 Step 3 v6.7+ fields are unavailable or disabled.
#
# DESIGN PRINCIPLE
#   Historic interpretation: total-time Surv(tstart,tstop,event), no future data.
#   Prediction:             interval gap-time model, training-window scaling,
#                           rolling-origin validation and optional Tn+1 forecast.
#   The two branches use the same authoritative primary state/event semantics but
#   remain separate estimands, matching the Paper 2 methodology.
# ============================================================
# 3-8-26
# Floodplain KM/AG/Cox historic-analysis core — state v17.8f primary/strict/pure-state sensitivity with memory-safe split full-event and local-position storage models
# Uses authoritative Stage 4 Step 3 primary events/risk sets; no R-side event/risk reconstruction.
# Cross-framework Module 3 versus Module 4a Storage/Floodplain differences identified by the separate QA workflow do not alter these modelling definitions. ASM_*_PREV fields remain historical assemblage descriptors only.
# v16.1 separates the three residual directional state transitions in competing-outcome outputs.
# v16.2 colours competing outcomes by destination state: floodplain = green, storage = yellow, active = blue.
# v16.3 adds proportional-hazards diagnostics:
#   - early/middle/late interactions for the principal spatial predictors;
#   - exact interval splitting at thirds of the observed record;
#   - period-specific spatial hazard ratios and robust Wald interaction tests;
#   - numerical cox.zph tables and Schoenfeld-residual plots.
# v17.7b retains all v17.7a corrections and fixes the strict event-integrity audit after row-ordering operations. Strict event fields are now compared directly with the authoritative Stage 4 Step 3 strict transition fields, preventing false failures caused by stale pre-sort state-derived vectors. It requires Stage 4 Step 2 v6.4 and corrected Step 3 v6.6 union-domain fields. The principal KM/AG/Cox models remain full-area models. Local Mamoré geometry is retained:
# v17.8 adds an explicit three-definition Mamoré sensitivity framework: primary ambiguity-bridged, strict observed-state, and high-support pure-state. The pure-state threshold is user-set (default 0.90) and requires both endpoint support values to meet the threshold in addition to Step 3 strict eligibility.
# v17.8a adds predictor-level and sequential storage-model missingness diagnostics, writes excluded-event identifiers and missingness combinations, and replaces the two-stage complete-case filter with an iterative rebuild from the original risk-set data whenever a term is dropped.
# v17.8b separates Mamoré storage modelling into: (1) a principal full-event assemblage-history model retaining all eligible storage events; and (2) an explicitly defined local-geometry subset model for relative within-channel position. Primary, strict and pure-state versions are fitted for both scopes, with separate outputs and PH diagnostics. Jamuna retains its full-event Active Domain distance model.
# v17.8c replaces the storage missingness matrix with chunked, streaming QA and a no-missing fast path. This prevents large contiguous-memory allocation failures on the 4-million-row Jamuna Risk Table while preserving the Mamoré local-position diagnostics.
# v17.8d makes the storage audit fully streamed and summary-first. It avoids global row masks and readr audit writes; optional row-level excluded-event output is written incrementally only when explicitly enabled.
# v17.8e makes no change to the KM/AG/Cox event, risk-set or predictor specifications. It clarifies that Module 3 endpoint states remain authoritative while Module 4a ASM_* history fields are lagged assemblage-history covariates rather than substitute endpoint states. It also makes Figure 11 transition-matrix label colour depend on the actual viridis fill luminance, so dark cells use white text and light cells use black text.
# v17.8f adds an immediate output-folder write probe and preflight inventories; explicit Module 3 warning-flag breakdowns; Module 3 x Module 4a T1/T2 disagreement matrices using Step 3 QA endpoint fields when present; and interval-level primary-versus-strict reactivation counts/plot. It also makes early required-field failures leave a diagnostic CSV in the selected output folder.
#   - reactivation: near-channel exposure + local outer-bank curvature only;
#   - storage: relative within-channel position + local inner/outer-bank curvature;
#   - stabilisation: distance from the lagged channel polygon, without curvature;
#   - no unrestricted corridor-wide centreline-distance x curvature model.
# Jamuna retains distance from the current/interval-start Active Domain.
# Figure and table titles retain the geographic reach names Mamoré and Jamuna.
# The original Cox models remain observation-period average models; PH period
# interactions and identity-time Schoenfeld plots are retained.
# ============================================================
# ------------------------------------------------------------
# [FRAF archive / workflow]
# Startup QA: establish a writable output directory and a run-started marker
# before package loading or any large input allocation.
# Output folder — initialise and test BEFORE loading optional packages.
# This guarantees that an early package/input failure does not leave the
# user-selected directory completely silent.
# ------------------------------------------------------------
.output_folder_raw <- ""
if (exists("OutputFolder") && !is.null(OutputFolder) && length(OutputFolder) > 0L) {
  .output_folder_raw <- trimws(as.character(OutputFolder)[1])
  if (is.na(.output_folder_raw)) .output_folder_raw <- ""
}

out_dir <- if (nzchar(.output_folder_raw)) .output_folder_raw else tempdir()
dir.create(out_dir, showWarnings = TRUE, recursive = TRUE)
if (!dir.exists(out_dir)) {
  stop("Could not create/access OutputFolder: ", out_dir)
}
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = TRUE)

# ---------------------------------------------------------------------------
# [FRAF archive / workflow]
# Mode boundary: one R invocation runs either Historic or Prediction, never both.
# Re-run with the other mode in a new R process to avoid retained heap pressure.
# v17.10.9 two-mode process isolation. QGIS selection parameters are normally
# supplied as zero-based integers, but accept descriptive text as well.
# There is deliberately no combined mode: the purpose of this release is to
# guarantee a new R process between the historic and prediction workloads.
# ---------------------------------------------------------------------------
.analysis_mode_raw <- if (exists("AnalysisMode") && !is.null(AnalysisMode) && length(AnalysisMode) > 0L) {
  AnalysisMode[1]
} else {
  0L
}
.analysis_mode_idx <- suppressWarnings(as.integer(.analysis_mode_raw))
if (is.finite(.analysis_mode_idx)) {
  analysis_mode <- if (.analysis_mode_idx == 1L) "Prediction only" else "Historic only"
} else {
  .analysis_mode_txt <- tolower(trimws(as.character(.analysis_mode_raw)[1]))
  analysis_mode <- if (grepl("predict", .analysis_mode_txt, fixed = TRUE)) {
    "Prediction only"
  } else {
    "Historic only"
  }
}
run_historic_mode <- identical(analysis_mode, "Historic only")
run_prediction_mode <- identical(analysis_mode, "Prediction only")
RunPrediction <- isTRUE(run_prediction_mode)

message("Analysis mode: ", analysis_mode)

# Remove stale top-level status markers from an earlier attempt in the same
# output directory. Scientific outputs and the historic completion marker are
# deliberately retained so Prediction-only can append to a prior Historic run.
unlink(file.path(out_dir, c("00_RUN_COMPLETED.txt", "00_RUN_INCOMPLETE.txt")), force = TRUE)
if (isTRUE(run_prediction_mode)) {
  unlink(file.path(out_dir, "00_PREDICTION_BRANCH_FAILED.txt"), force = TRUE)
}

.output_probe <- file.path(out_dir, "00_RUN_STARTED.txt")
tryCatch(
  writeLines(
    c(
      paste0("FRAF KM/AG/Cox v17.10.15.1 started: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
      paste0("Analysis mode: ", analysis_mode),
      paste0("Output directory: ", out_dir),
      paste0("Risk table parameter: ", if (exists("RiskTable")) paste(as.character(RiskTable), collapse = " | ") else "<not supplied>")
    ),
    .output_probe, useBytes = TRUE
  ),
  error = function(e) stop("OutputFolder is not writable: ", out_dir, " | ", conditionMessage(e))
)
message("Output directory verified writable: ", out_dir)

# [FRAF archive / workflow]
# Dependency gate: record missing R packages in an explicit startup-failure file.
# Keep provider metadata above this line intact for QGIS Processing discovery.
# Load analysis packages only after the output destination has been proven writable.
# IMPORTANT (v17.10.2): QGIS Processing may scan comments when discovering R
# dependencies. Keep comments free of function-like package-attachment examples.
# Check namespaces generically, then attach the required packages explicitly below.
.required_packages <- c("sf", "dplyr", "tidyr", "readr", "ggplot2", "survival", "survminer", "broom")
.missing_packages <- .required_packages[!vapply(
  .required_packages,
  function(x) requireNamespace(x, quietly = TRUE),
  logical(1)
)]
if (length(.missing_packages) > 0L) {
  fail_file <- file.path(out_dir, "00_STARTUP_FAILURE.txt")
  writeLines(
    c(
      paste0("Required R package(s) not installed/available: ", paste(.missing_packages, collapse = ", ")),
      paste0("Output directory: ", out_dir),
      paste0("Time: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"))
    ),
    fail_file, useBytes = TRUE
  )
  stop("Required R package(s) not installed/available: ", paste(.missing_packages, collapse = ", "))
}
suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
  library(tidyr)
  library(readr)
  library(ggplot2)
  library(survival)
  library(survminer)
  library(broom)
})
rm(.required_packages, .missing_packages)

if (!exists("RunTemporalSensitivity") || is.null(RunTemporalSensitivity)) RunTemporalSensitivity <- TRUE
if (!exists("StrictTemporalAlignment") || is.null(StrictTemporalAlignment)) StrictTemporalAlignment <- TRUE

if (!exists("RunUnionComparison") || is.null(RunUnionComparison)) RunUnionComparison <- FALSE

if (!exists("RunDefinitionSensitivity") || is.null(RunDefinitionSensitivity)) RunDefinitionSensitivity <- TRUE
if (!exists("RunSemanticContrastQA") || is.null(RunSemanticContrastQA)) RunSemanticContrastQA <- TRUE
if (!exists("RunStorageReworkInterpretive") || is.null(RunStorageReworkInterpretive)) RunStorageReworkInterpretive <- TRUE
# v17.10.9: RunPrediction is set exclusively by AnalysisMode above.
if (!exists("RunBroadFloodplainPrediction") || is.null(RunBroadFloodplainPrediction)) RunBroadFloodplainPrediction <- TRUE
if (!exists("RunMamoreDSADVariantComparison") || is.null(RunMamoreDSADVariantComparison)) RunMamoreDSADVariantComparison <- TRUE
RunMamoreDSADVariantComparison <- isTRUE(as.logical(RunMamoreDSADVariantComparison)[1])
if (!exists("MamoreDSADPrincipalSpatialModel") || is.null(MamoreDSADPrincipalSpatialModel)) MamoreDSADPrincipalSpatialModel <- 0L
.mam_dsad_sel <- suppressWarnings(as.integer(MamoreDSADPrincipalSpatialModel)[1])
if (!is.finite(.mam_dsad_sel)) {
  .mam_txt <- tolower(trimws(as.character(MamoreDSADPrincipalSpatialModel)[1]))
  .mam_dsad_sel <- ifelse(grepl("curv", .mam_txt), 1L, 0L)
}
mamore_dsad_use_curvature <- identical(as.integer(.mam_dsad_sel), 1L)
if (!exists("MamoreDSADDistalThresholdM") || is.null(MamoreDSADDistalThresholdM)) MamoreDSADDistalThresholdM <- 1000
if (!exists("MamoreDSADExceptionalIntervalMinEvents") || is.null(MamoreDSADExceptionalIntervalMinEvents)) MamoreDSADExceptionalIntervalMinEvents <- 25
if (!exists("MamoreDSADExceptionalIntervalMinFraction") || is.null(MamoreDSADExceptionalIntervalMinFraction)) MamoreDSADExceptionalIntervalMinFraction <- 0.18
MamoreDSADDistalThresholdM <- suppressWarnings(as.numeric(MamoreDSADDistalThresholdM)[1])
MamoreDSADExceptionalIntervalMinEvents <- suppressWarnings(as.integer(MamoreDSADExceptionalIntervalMinEvents)[1])
MamoreDSADExceptionalIntervalMinFraction <- suppressWarnings(as.numeric(MamoreDSADExceptionalIntervalMinFraction)[1])
if (!is.finite(MamoreDSADDistalThresholdM)) MamoreDSADDistalThresholdM <- 1000
if (!is.finite(MamoreDSADExceptionalIntervalMinEvents)) MamoreDSADExceptionalIntervalMinEvents <- 25L
if (!is.finite(MamoreDSADExceptionalIntervalMinFraction)) MamoreDSADExceptionalIntervalMinFraction <- 0.18
message("Mamore DS->AD principal spatial model: ",
        ifelse(mamore_dsad_use_curvature, "linear previous-channel margin + curvature", "linear previous-channel margin"))
if (!exists("WriteDetailedStorageAudit") || is.null(WriteDetailedStorageAudit)) WriteDetailedStorageAudit <- FALSE
WriteDetailedStorageAudit <- isTRUE(as.logical(WriteDetailedStorageAudit)[1])
message("Detailed row-level storage audit: ", ifelse(WriteDetailedStorageAudit, "enabled", "disabled (summary-only)"))
if (!exists("PureStateMinSupport") || is.null(PureStateMinSupport)) PureStateMinSupport <- 0.90
PureStateMinSupport <- suppressWarnings(as.numeric(PureStateMinSupport)[1])
if (!is.finite(PureStateMinSupport)) PureStateMinSupport <- 0.90
PureStateMinSupport <- max(0, min(1, PureStateMinSupport))
message("Pure-state endpoint support threshold: ", format(PureStateMinSupport, trim = TRUE))

# [FRAF archive / Historic/QA function: resolve_reach_label]
# Resolve the user-selected Mamore/Jamuna reach into the label used in model branches and output
# titles.
resolve_reach_label <- function(x) {
  if (is.null(x) || length(x) == 0 || is.na(x[1])) return("Mamor\u00e9")
  idx <- suppressWarnings(as.integer(x[1]))
  if (is.finite(idx)) return(ifelse(idx == 1L, "Jamuna", "Mamor\u00e9"))
  txt <- tolower(trimws(as.character(x[1])))
  if (grepl("jamuna", txt, fixed = TRUE)) "Jamuna" else "Mamor\u00e9"
}
reach_label <- resolve_reach_label(if (exists("ReachName")) ReachName else NULL)
message("Reach label for figure/table titles: ", reach_label)
message("v17.10.15.1 process-isolated mode confirmed: ", analysis_mode)

# -----------------------------
# Helper functions
# -----------------------------

# [FRAF archive / Historic/QA function: require_fields]
# Fail early when required risk-table columns are absent, recording a named field-schema check.
require_fields <- function(dat, fields, check_name = "required_fields") {
  missing <- setdiff(fields, names(dat))
  qa <- data.frame(
    check = check_name,
    field = fields,
    present = fields %in% names(dat),
    stringsAsFactors = FALSE
  )
  if (exists("out_dir", inherits = TRUE) && dir.exists(out_dir)) {
    utils::write.csv(
      qa,
      file.path(out_dir, paste0("00_preflight_", gsub("[^A-Za-z0-9_-]+", "_", check_name), ".csv")),
      row.names = FALSE, na = ""
    )
  }
  if (length(missing) > 0) {
    stop("Missing required fields [", check_name, "]: ", paste(missing, collapse = ", "))
  }
}

# [FRAF archive / Historic/QA function: safe_first]
# Read the first usable finite/non-missing value with a stable missing-value fallback.
safe_first <- function(x) {
  x <- x[!is.na(x)]
  if (length(x) == 0) return(NA_real_)
  min(x)
}

# [FRAF archive / Historic/QA function: safe_max]
# Find a maximum while avoiding invalid or entirely missing inputs.
safe_max <- function(x) {
  x <- as.numeric(x)
  if (all(is.na(x))) return(NA_real_)
  max(x, na.rm = TRUE)
}

# [FRAF archive / Historic/QA function: safe_mean]
# Compute a robust mean without allowing an all-missing vector to masquerade as valid data.
safe_mean <- function(x) {
  x <- as.numeric(x)
  if (all(is.na(x))) return(NA_real_)
  mean(x, na.rm = TRUE)
}

# [FRAF archive / Historic/QA function: safe_plot_save]
# Export an analytic plot with fallbacks so a graphics device failure does not silently erase
# the tabular result.
safe_plot_save <- function(plot_obj, filename, width = 8, height = 6, dpi = 300) {
  out_png <- file.path(out_dir, filename)

  # QGIS/R provider on Windows can fail when ggplot2/survminer checks
  # advanced PNG device capabilities, especially for survminer ribbons.
  # Try PNG first; if that fails, write a PDF rather than stopping the run.
  tryCatch({
    ggplot2::ggsave(
      filename = out_png,
      plot = plot_obj,
      width = width,
      height = height,
      dpi = dpi,
      device = "png",
      bg = "white"
    )
  }, error = function(e) {
    message("[Plot warning] PNG failed for ", filename, ": ", conditionMessage(e))
    out_pdf <- sub("\\.png$", ".pdf", out_png, ignore.case = TRUE)
    tryCatch({
      ggplot2::ggsave(
        filename = out_pdf,
        plot = plot_obj,
        width = width,
        height = height,
        device = "pdf"
      )
      message("[Plot warning] Wrote PDF instead: ", out_pdf)
    }, error = function(e2) {
      message("[Plot warning] PDF fallback also failed for ", filename, ": ", conditionMessage(e2))
    })
  })
}


# Return white text on genuinely dark viridis cells and black text on light cells.
# This is used by Figure 11. It follows the same viridis option/direction as the
# fill scale rather than using an arbitrary probability threshold.
# [FRAF archive / Historic/QA function: transition_matrix_text_colour]
# Choose legible label text for matrix tiles from rendered fill luminance rather than fixed
# contrast.
transition_matrix_text_colour <- function(
  probability,
  option = "C",
  direction = -1,
  luminance_cutoff = 0.30
) {
  p <- suppressWarnings(as.numeric(probability))
  out <- rep("black", length(p))
  valid <- is.finite(p)
  if (!any(valid)) return(out)

  p_valid <- pmin(1, pmax(0, p[valid]))
  pal <- viridisLite::viridis(
    256,
    option = option,
    direction = direction,
    begin = 0,
    end = 1
  )
  idx <- pmax(1L, pmin(256L, as.integer(round(p_valid * 255)) + 1L))
  rgb <- grDevices::col2rgb(pal[idx]) / 255

  # Convert sRGB to linear RGB before calculating relative luminance.
  rgb_linear <- ifelse(
    rgb <= 0.04045,
    rgb / 12.92,
    ((rgb + 0.055) / 1.055)^2.4
  )
  luminance <- (
    0.2126 * rgb_linear[1, ] +
    0.7152 * rgb_linear[2, ] +
    0.0722 * rgb_linear[3, ]
  )

  out[valid] <- ifelse(luminance < luminance_cutoff, "white", "black")
  out
}

# [FRAF archive / Historic/QA function: nonempty_factor]
# Convert available categories into a factor while preserving an explicit missing/empty
# interpretation.
nonempty_factor <- function(x) {
  x <- as.character(x)
  x[is.na(x) | x == "" | x == "NA"] <- NA_character_
  factor(x)
}

# [FRAF archive / Historic/QA function: zscore_vec]
# Standardise a numeric vector for historic-model effect-scale comparability.
zscore_vec <- function(x) {
  x <- as.numeric(x)
  s <- stats::sd(x, na.rm = TRUE)
  m <- mean(x, na.rm = TRUE)
  if (is.na(s) || s == 0) return(rep(0, length(x)))
  (x - m) / s
}

# Sensitivity diagnostics must not turn missing fields into zero exposure.
# [FRAF archive / Historic/QA function: zscore_preserve_na]
# Compute a Z score while retaining missing observations as missing.
zscore_preserve_na <- function(x) {
  x <- as.numeric(x)
  out <- rep(NA_real_, length(x))
  ok <- is.finite(x)
  if (sum(ok) < 2L) return(out)
  s <- stats::sd(x[ok])
  if (!is.finite(s) || s == 0) return(out)
  out[ok] <- (x[ok] - mean(x[ok])) / s
  out
}

# [FRAF archive / Historic/QA function: add_z_if_exists]
# Create a standardised predictor only when the requested source field exists.
add_z_if_exists <- function(dat, field, out_field = paste0(field, "_Z")) {
  if (field %in% names(dat)) {
    dat[[out_field]] <- zscore_vec(dat[[field]])
  }
  dat
}

# [FRAF archive / Historic/QA function: add_logkm_if_exists]
# Create a distance transform in log-kilometre units from an available source distance.
add_logkm_if_exists <- function(dat, field, out_field = paste0(field, "_LOGKM")) {
  if (field %in% names(dat)) {
    x <- as.numeric(dat[[field]])
    x[x < 0] <- NA_real_
    dat[[out_field]] <- log1p(x / 1000)
  }
  dat
}

# [FRAF archive / Historic/QA function: factor_if_reasonable]
# Use a factor only when category cardinality is tractable and informative.
factor_if_reasonable <- function(dat, field, max_levels = 15) {
  if (field %in% names(dat)) {
    f <- nonempty_factor(dat[[field]])
    nlev <- n_distinct(na.omit(f))
    if (nlev > 1 && nlev <= max_levels) {
      dat[[field]] <- f
    } else {
      message("[Info] Not using ", field, " as Cox factor; observed levels = ", nlev)
      dat[[field]] <- as.character(dat[[field]])
    }
  }
  dat
}

# [FRAF archive / Historic/QA function: write_if_nonempty]
# Write a table only if nonempty, avoiding deceptive empty scientific exports.
write_if_nonempty <- function(dat, filename) {
  output_path <- file.path(out_dir, filename)
  if (!is.null(dat) && nrow(dat) > 0) {
    write_csv(dat, output_path)
  } else if (file.exists(output_path)) {
    unlink(output_path, force = TRUE)
  }
}

# Small QA tables are written with base R to avoid readr buffer allocations when
# the main Risk Table has already placed the R process under memory pressure.
# [FRAF archive / Historic/QA function: write_audit_csv]
# Export a diagnostic or QA table to the selected output directory.
write_audit_csv <- function(dat, filename) {
  output_path <- file.path(out_dir, filename)
  if (file.exists(output_path)) unlink(output_path, force = TRUE)
  dat <- as.data.frame(dat, stringsAsFactors = FALSE)
  utils::write.table(
    dat, file = output_path, sep = ",", row.names = FALSE, col.names = TRUE,
    quote = TRUE, na = "", qmethod = "double", fileEncoding = "UTF-8"
  )
  invisible(output_path)
}

# [FRAF archive / Historic/QA function: clean_filename]
# Normalise an output-name component for safe use in filesystem paths.
clean_filename <- function(x) {
  x <- gsub("[^A-Za-z0-9_-]+", "_", as.character(x))
  x <- gsub("_+", "_", x)
  x <- gsub("^_|_$", "", x)
  x
}

# [FRAF archive / Historic/QA function: export_km_fit]
# Extract Kaplan-Meier estimates and plot/table outputs with explicit analysis context.
export_km_fit <- function(fit, prefix, analysis_name) {
  if (is.null(fit)) return(invisible(NULL))
  exact_times <- sort(unique(as.numeric(fit$time)))
  exact_times <- exact_times[is.finite(exact_times)]
  if (length(exact_times) > 0) {
    sm <- summary(fit, times = exact_times, extend = TRUE)
    n <- length(sm$time)
    strata <- if (is.null(sm$strata)) rep("All", n) else as.character(sm$strata)
    coords <- tibble(
      analysis = analysis_name,
      stratum = strata,
      time = as.numeric(sm$time),
      n_risk = as.numeric(sm$n.risk),
      n_event = as.numeric(sm$n.event),
      n_censor = as.numeric(sm$n.censor),
      survival = as.numeric(sm$surv),
      std_error = as.numeric(sm$std.err),
      lower_95 = as.numeric(sm$lower),
      upper_95 = as.numeric(sm$upper)
    )
    write_csv(coords, file.path(out_dir, paste0(prefix, "_coordinates.csv")))
  }
  tab <- summary(fit)$table
  if (!is.null(tab)) {
    if (is.null(dim(tab))) {
      tab_df <- tibble(
        analysis = analysis_name,
        stratum = "All",
        statistic = names(tab),
        value = as.numeric(tab)
      )
    } else {
      tab_df <- as.data.frame(tab, check.names = FALSE) %>%
        tibble::rownames_to_column("stratum") %>%
        mutate(analysis = analysis_name, .before = 1)
    }
    write_csv(tab_df, file.path(out_dir, paste0(prefix, "_summary.csv")))
  }
  invisible(NULL)
}


# [FRAF archive / Historic/QA function: int01]
# Normalise numeric, logical, or missing event/risk flags to a 0/1 integer representation.
int01 <- function(x, default = 0L) {
  if (is.null(x)) return(integer(0))
  if (is.factor(x)) x <- as.character(x)
  suppressWarnings(y <- as.integer(as.numeric(x)))
  y[is.na(y)] <- default
  y[y != 0L] <- 1L
  y
}

# [FRAF archive / Historic/QA function: num_or_na]
# Coerce to a numeric vector, marking invalid values as missing.
num_or_na <- function(x) {
  suppressWarnings(as.numeric(x))
}

# Convert common Stage 3/4 date representations to an integer YYYYMMDD code.
# Four-digit years are represented as 1 January of that year. This function is
# used only for temporal provenance QA; survival time remains tstart_yr/tstop_yr.
# [FRAF archive / Historic/QA function: ymd_code]
# Convert observation date/year values into comparable integer calendar codes.
ymd_code <- function(x) {
  raw <- trimws(as.character(x))
  out <- rep(NA_integer_, length(raw))
  for (i in seq_along(raw)) {
    s <- raw[i]
    if (is.na(s) || s == "" || toupper(s) %in% c("NA", "NAN", "NULL")) next
    if (grepl("^[0-9]+\\.0+$", s)) s <- sub("\\.0+$", "", s)
    digits <- gsub("[^0-9]", "", s)
    if (nchar(digits) == 4L) {
      out[i] <- suppressWarnings(as.integer(paste0(digits, "0101")))
    } else if (nchar(digits) >= 8L) {
      out[i] <- suppressWarnings(as.integer(substr(digits, 1L, 8L)))
    }
  }
  out
}

# [FRAF archive / Historic/QA function: safe_cor]
# Compute a correlation only where enough comparable finite observations exist.
safe_cor <- function(x, y, method = "pearson") {
  ok <- is.finite(x) & is.finite(y)
  if (sum(ok) < 3L || stats::sd(x[ok]) == 0 || stats::sd(y[ok]) == 0) return(NA_real_)
  suppressWarnings(stats::cor(x[ok], y[ok], method = method))
}

# [FRAF archive / Historic/QA function: safe_quantile]
# Return a requested empirical percentile while handling empty or invalid inputs.
safe_quantile <- function(x, p) {
  x <- x[is.finite(x)]
  if (length(x) == 0L) return(NA_real_)
  as.numeric(stats::quantile(x, probs = p, names = FALSE, type = 7))
}

# [FRAF archive / Historic/QA function: make_distance_bin]
# Assign a distance to the common corridor-scale analysis bins.
make_distance_bin <- function(x) {
  x <- as.numeric(x)
  as.character(cut(
    x,
    breaks = c(-Inf, 250, 500, 1000, 2000, 5000, Inf),
    labels = c("0-250 m", "250-500 m", "0.5-1 km", "1-2 km", "2-5 km", ">5 km"),
    right = FALSE
  ))
}

# [FRAF archive / Historic/QA function: normalise_ontology_text]
# Standardise historical naming and punctuation before mapping labels to the three-state
# ontology.
normalise_ontology_text <- function(x) {
  x <- as.character(x)
  x <- toupper(trimws(x))
  x <- gsub("[ -]+", "_", x)
  x[x %in% c("", "NA", "NAN")] <- NA_character_
  x
}

# [FRAF archive / Historic/QA function: canonical_state]
# Map supported aliases to AD, DS or SF; leave unsupported information unresolved.
canonical_state <- function(x) {
  z <- normalise_ontology_text(x)
  dplyr::case_when(
    z %in% c("ACTIVE", "ACTIVE_DOMAIN", "CHANNEL", "WATER", "ACTIVE_ZONE", "BRAIDPLAIN", "ACTIVE_CHANNEL", "STABLE_CHANNEL", "INCHANNEL_SURFACE") ~ "ACTIVE_DOMAIN",
    z %in% c("DEPOSITION", "DEPOSITIONAL_STORAGE", "STORAGE", "BAR", "SAND", "ISLAND", "ISLAND_DEPOSITION", "MIGRATION_DEPOSITION", "INFILL_DEPOSITION", "CHANNEL_LEGACY_DEPOSITION") ~ "DEPOSITIONAL_STORAGE",
    z %in% c("STABILISED_FLOODPLAIN", "STABILIZED_FLOODPLAIN", "STABLE_FLOODPLAIN", "INACTIVE_FLOODPLAIN", "PERSISTENT_FLOODPLAIN", "PRESERVED_FLOODPLAIN", "FLOODPLAIN", "VEGETATED_FLOODPLAIN", "RECENT_FLOODPLAIN", "REWORKED_FLOODPLAIN") ~ "STABILISED_FLOODPLAIN",
    TRUE ~ "UNRESOLVED"
  )
}

# [FRAF archive / Historic/QA function: display_state]
# Convert an internal state code into a reader-facing state description.
display_state <- function(x) {
  z <- canonical_state(x)
  dplyr::recode(
    z,
    ACTIVE_DOMAIN = "Active domain",
    DEPOSITIONAL_STORAGE = "Depositional storage",
    STABILISED_FLOODPLAIN = "Stabilised floodplain",
    UNRESOLVED = "Unresolved",
    .default = "Unresolved"
  )
}

# [FRAF archive / Historic/QA function: normalise_fp_condition]
# Harmonise descriptive floodplain-condition fields without changing authoritative endpoint
# states.
normalise_fp_condition <- function(x, fallback_state = NULL) {
  z <- normalise_ontology_text(x)
  fb <- canonical_state(fallback_state)
  out <- dplyr::case_when(
    z %in% c("ACTIVE_DOMAIN", "ACTIVE") ~ "Active domain",
    z %in% c("DEPOSITIONAL_STORAGE", "STORAGE") ~ "Depositional storage",
    z %in% c("RECENT_FLOODPLAIN", "RECENT_FP") ~ "Recent floodplain",
    z %in% c("REWORKED_FLOODPLAIN", "REWORKED_FP") ~ "Reworked floodplain",
    z %in% c("PERSISTENT_FLOODPLAIN", "PERSISTENT_FP", "STABILISED_FLOODPLAIN", "STABILIZED_FLOODPLAIN") ~ "Persistent floodplain",
    fb == "ACTIVE_DOMAIN" ~ "Active domain",
    fb == "DEPOSITIONAL_STORAGE" ~ "Depositional storage",
    fb == "STABILISED_FLOODPLAIN" ~ "Persistent floodplain",
    TRUE ~ "Unresolved"
  )
  factor(
    out,
    levels = c("Active domain", "Depositional storage", "Recent floodplain", "Persistent floodplain", "Reworked floodplain", "Unresolved")
  )
}

# [FRAF archive / Historic/QA function: display_event]
# Convert the reactivation/storage/stabilisation flags into an interpretable event label.
display_event <- function(reactivate_evt, storage_evt, stabilise_evt = 0L) {
  r <- int01(reactivate_evt)
  s <- int01(storage_evt)
  st <- int01(stabilise_evt)
  dplyr::case_when(
    r == 1L & s == 1L ~ "Active Domain reach + storage",
    r == 1L ~ "Reached by Active Domain",
    s == 1L ~ "Depositional storage",
    st == 1L ~ "Storage became stable floodplain",
    TRUE ~ "Persistence"
  )
}

# [FRAF archive / Historic/QA function: display_state_event]
# Describe process transitions and relevant state change categories for display or summary.
display_state_event <- function(
  reactivate_evt,
  storage_evt,
  stabilise_evt,
  storage_rework_evt,
  fp_storage_evt,
  reactivate_transition,
  storage_transition,
  any_state_evt,
  state1,
  state2
) {
  r <- int01(reactivate_evt)
  s <- int01(storage_evt)
  st <- int01(stabilise_evt)
  sr <- int01(storage_rework_evt)
  fps <- int01(fp_storage_evt)
  rt <- int01(reactivate_transition)
  sd <- int01(storage_transition)
  any_state <- int01(any_state_evt)

  s1 <- as.character(state1)
  s2 <- as.character(state2)

  dplyr::case_when(
    # State-defined named transitions.
    r == 1L ~ "Reached by Active Domain",
    s == 1L ~ "Entered Depositional Storage",
    st == 1L ~ "Storage became Stabilised Floodplain",
    sr == 1L ~ "Depositional Storage -> Active Domain",
    fps == 1L ~ "Stabilised Floodplain -> Depositional Storage",

    # Named state transitions that were not confirmed by the corresponding
    # Module 3B E_evt/D_evt process threshold.
    rt == 1L ~ "Unconfirmed reactivation transition",
    sd == 1L ~ "Unconfirmed storage transition",

    # Remaining directional transitions between the three recognised states.
    s1 == "DEPOSITIONAL_STORAGE" &
      s2 == "ACTIVE_DOMAIN" ~
        "Depositional Storage -> Active Domain",

    s1 == "ACTIVE_DOMAIN" &
      s2 == "STABILISED_FLOODPLAIN" ~
        "Active Domain -> Stabilised Floodplain",

    s1 == "STABILISED_FLOODPLAIN" &
      s2 == "DEPOSITIONAL_STORAGE" ~
        "Stabilised Floodplain -> Depositional Storage",

    # Defensive category for unexpected recognised-state changes.
    any_state == 1L ~ "Unclassified state transition",

    TRUE ~ "Persistence"
  )
}

# [FRAF archive / Historic/QA function: derive_state_ontology]
# Recover a conservative ontology label from source classes only where explicit labels are
# unavailable.
derive_state_ontology <- function(domain = NULL, surface = NULL, state = NULL) {
  # Prefer explicit domain/surface/state evidence in the same order as revised Step 3:
  # active-domain > depositional-storage > stabilised floodplain.
  d <- canonical_state(domain)
  s <- canonical_state(surface)
  st <- canonical_state(state)
  out <- dplyr::case_when(
    d == "ACTIVE_DOMAIN" | s == "ACTIVE_DOMAIN" | st == "ACTIVE_DOMAIN" ~ "ACTIVE_DOMAIN",
    d == "DEPOSITIONAL_STORAGE" | s == "DEPOSITIONAL_STORAGE" | st == "DEPOSITIONAL_STORAGE" ~ "DEPOSITIONAL_STORAGE",
    d == "STABILISED_FLOODPLAIN" | s == "STABILISED_FLOODPLAIN" | st == "STABILISED_FLOODPLAIN" ~ "STABILISED_FLOODPLAIN",
    TRUE ~ "UNRESOLVED"
  )
  out[is.na(out) | out == ""] <- "UNRESOLVED"
  out
}

# [FRAF archive / Historic/QA function: derive_event_ontology]
# Create descriptive process-event labels from the available transition flags.
derive_event_ontology <- function(e_evt, d_evt, stabilise_evt = 0L) {
  display_event(e_evt, d_evt, stabilise_evt)
}
# ---------------------------------------------------------------------------
# Shared GeoPackage table reader. This helper must exist outside the historic
# branch because Prediction-only intentionally skips the historic input section.
# It muffles only sf's expected warning for non-spatial GeoPackage tables.
# ---------------------------------------------------------------------------
# [FRAF archive / Historic/QA function: st_read_qgis_safe]
# Read QGIS/GeoPackage sources while handling known provider warnings and preserving actionable
# failures.
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

# ===========================================================================
# HISTORIC-ONLY BRANCH
# ===========================================================================
if (isTRUE(run_historic_mode)) {

# -----------------------------
# [FRAF archive / workflow]
# Historic input gate: read the authoritative Stage 4 risk table with explicit
# GeoPackage layer resolution; reject accidental raw PLACE tables.
# 1. Load risk table from GeoPackage
# -----------------------------

sf::sf_use_s2(FALSE)

# The Jamuna workflow expects the QGIS Module 3b/4a risk table as a GeoPackage.
# CSV input is deliberately not used here because it can lose field typing and
# disconnect the script from the named GPKG layers produced by the QGIS workflow.

message("RiskTable class: ", paste(class(RiskTable), collapse = ", "))

# Read a GeoPackage layer/table while muffling only sf's expected warning for
# non-spatial tables. Errors and all other warnings remain visible.
# [FRAF archive / Historic/QA function: st_read_qgis_safe]
# Read QGIS/GeoPackage sources while handling known provider warnings and preserving actionable
# failures.
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

# [FRAF archive / code note]
# GeoPackage URI parsing is required because a .gpkg may contain multiple
# spatial and non-spatial layers; selecting the wrong layer changes the dataset.
# [FRAF archive / Historic/QA function: parse_gpkg_source]
# Split a GeoPackage path and optional layername into explicit source identifiers.
parse_gpkg_source <- function(x, layer_hint = NULL) {
  x <- as.character(x)[1]

  # QGIS sometimes passes sources as:
  #   path/to/file.gpkg|layername=Risk Table
  # or as an OGR URI. Handle the common pipe syntax explicitly.
  layer_from_uri <- NA_character_
  if (grepl("\\|layername=", x, ignore.case = TRUE)) {
    parts <- strsplit(x, "\\|", fixed = FALSE)[[1]]
    path <- parts[1]
    layer_part <- parts[grepl("^layername=", parts, ignore.case = TRUE)]
    if (length(layer_part) > 0) {
      layer_from_uri <- sub("^layername=", "", layer_part[1], ignore.case = TRUE)
    }
  } else {
    path <- x
  }

  # Strip simple OGR dbname='...' wrappers if passed from a saved QGIS parameter.
  if (grepl("dbname=", path, ignore.case = TRUE)) {
    path2 <- sub(".*dbname='([^']+)'.*", "\\1", path)
    if (!identical(path2, path)) path <- path2
  }

  list(
    path = path,
    layer = dplyr::coalesce(
      na_if(layer_from_uri, ""),
      na_if(as.character(layer_hint)[1], "")
    )
  )
}

# [FRAF archive / Historic/QA function: choose_gpkg_layer]
# Select the intended non-spatial risk table, failing on ambiguous GeoPackage sublayers.
choose_gpkg_layer <- function(path, requested_layer = NULL) {
  # LIST_ALL_TABLES is required because the authoritative Stage 4 Step 3
  # Risk Table is normally geometryless.
  layers <- sf::st_layers(path, options = "LIST_ALL_TABLES=YES")
  layer_names <- layers$name

  message("Available layers/tables in RiskTable GeoPackage:")
  print(layers)

  requested_layer <- as.character(requested_layer)[1]
  if (!is.na(requested_layer) && nzchar(trimws(requested_layer)) && requested_layer %in% layer_names) {
    if (identical(requested_layer, "PLACE_interval_long")) {
      stop(
        "RiskLayerName points to PLACE_interval_long, which is the Stage 3B interval table, ",
        "not the Stage 4 Step 3 Risk Table. Select the Stage 4 Step 3 output table."
      )
    }
    return(requested_layer)
  }

  preferred <- c(
    "RISK_TABLE",
    "Risk Table",
    "Risk_Table",
    "RiskTable",
    "Stage_4_Risk_Table",
    "Stage4_Risk_Table",
    "Version 2",
    "Version_2"
  )
  hit <- preferred[preferred %in% layer_names]
  if (length(hit) > 0) {
    if (!is.na(requested_layer) && nzchar(trimws(requested_layer))) {
      message("Requested RiskLayerName '", requested_layer, "' was not found; using '", hit[1], "'.")
    }
    return(hit[1])
  }

  non_raw <- setdiff(layer_names, c("PLACE_interval_long", "KM_blocks", "INPUT"))
  if (length(non_raw) == 1) {
    message("One non-core table/layer found; using '", non_raw[1], "'.")
    return(non_raw[1])
  }

  stop(
    "RiskLayerName '", requested_layer, "' was not found or is ambiguous. ",
    "Select the Stage 4 Step 3 Risk Table explicitly. Available tables/layers: ",
    paste(layer_names, collapse = ", ")
  )
}

# [FRAF archive / code note]
# Historic branch obtains the full risk panel. Prediction-only mode instead
# uses a projected SQL read so it need not allocate the same large table.
if (inherits(RiskTable, "sf")) {
  message("RiskTable received as sf object from QGIS")
  risk <- RiskTable %>% st_drop_geometry()

} else if (is.character(RiskTable)) {
  src <- parse_gpkg_source(RiskTable, RiskLayerName)
  message("RiskTable received as GeoPackage path: ", src$path)

  if (!grepl("\\.gpkg$", src$path, ignore.case = TRUE)) {
    stop(
      "This workflow expects a GeoPackage Stage 4 Step 3 Risk Table (.gpkg), not: ", src$path,
      ". Select the Stage 4 Step 3 output and set RiskLayerName to its table name."
    )
  }

  selected_layer <- choose_gpkg_layer(src$path, src$layer)
  message("Reading Stage 4 Step 3 Risk Table: ", selected_layer)

  risk_obj <- st_read_qgis_safe(
    src$path,
    layer = selected_layer,
    quiet = FALSE,
    options = "LIST_ALL_TABLES=YES"
  )

  risk <- if (inherits(risk_obj, "sf")) {
    sf::st_drop_geometry(risk_obj)
  } else {
    as.data.frame(risk_obj)
  }

} else {
  stop("RiskTable is neither an sf object nor a GeoPackage file path. Class: ",
       paste(class(RiskTable), collapse = ", "))
}

message("Rows loaded: ", nrow(risk))
message("Fields loaded: ", paste(names(risk), collapse = ", "))

utils::write.csv(
  data.frame(field = names(risk), stringsAsFactors = FALSE),
  file.path(out_dir, "00_input_field_inventory_preflight.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  data.frame(rows_loaded = nrow(risk), columns_loaded = ncol(risk), stringsAsFactors = FALSE),
  file.path(out_dir, "00_input_dimensions_preflight.csv"),
  row.names = FALSE, na = ""
)

# Stage 4 Step 3 prefers BLOCK_ID but retains PLACE_ID for compatibility.
if (!"PLACE_ID" %in% names(risk) && "BLOCK_ID" %in% names(risk)) risk$PLACE_ID <- risk$BLOCK_ID
if (!"BLOCK_ID" %in% names(risk) && "PLACE_ID" %in% names(risk)) risk$BLOCK_ID <- risk$PLACE_ID

# [FRAF archive / code note]
# Preflight fields are checked against the v6.7 Stage 4 semantic contracts;
# missing mandatory fields indicate a pipeline mismatch, not missing at random.
required_core <- c(
  "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
  "STATE1_ONTOLOGY", "STATE2_ONTOLOGY",
  "REACTIVATE_TRANS", "STORAGE_TRANS", "STABILISE_TRANS", "STORAGE_REWORK_TRANS", "FP_STORAGE_TRANS",
  "REACTIVATE_EVT", "STORAGE_EVT", "STABILISE_EVT", "STORAGE_REWORK_EVT", "FP_STORAGE_EVT", "ANY_STATE_EVT",
  "REACTIVATE_RISK_SET", "STORAGE_RISK_SET", "STABILISE_RISK_SET",
  "STORAGE_REWORK_RISK_SET", "FP_STORAGE_RISK_SET", "ANY_STATE_RISK_SET",
  "REACTIVATE_CONFIRMED", "STORAGE_CONFIRMED", "STABILISE_CONFIRMED",
  "STORAGE_REWORK_CONFIRMED", "FP_STORAGE_CONFIRMED",
  "FP_REACTIVATE_EVT_PRIMARY", "FP_REACTIVATE_RISK_SET_PRIMARY",
  "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY", "FP_REACTIVATE_EXCLUSION_REASON_PRIMARY",
  "FP_REACTIVATE_SOURCE_PRIMARY",
  "REACTIVATE_EVT_PRIMARY", "STORAGE_EVT_PRIMARY", "STABILISE_EVT_PRIMARY",
  "STORAGE_REWORK_EVT_PRIMARY", "FP_STORAGE_EVT_PRIMARY", "ANY_STATE_EVT_PRIMARY",
  "REACTIVATE_RISK_SET_PRIMARY", "STORAGE_RISK_SET_PRIMARY", "STABILISE_RISK_SET_PRIMARY",
  "STORAGE_REWORK_RISK_SET_PRIMARY", "FP_STORAGE_RISK_SET_PRIMARY", "ANY_STATE_RISK_SET_PRIMARY",
  "REACTIVATE_BRIDGED", "STORAGE_BRIDGED", "STORAGE_REWORK_BRIDGED", "FP_STORAGE_BRIDGED",
  "M3_EFFECTIVE_STATE_T1_PRIMARY", "M3_MODEL_ELIGIBLE_PRIMARY",
  "M3_MODEL_EXCLUSION_REASON_PRIMARY",
  "PRIMARY_EVENT_DEFINITION_MISMATCH", "PRIMARY_RISK_DEFINITION_MISMATCH",
  "PRIMARY_EVENT_RISK_MISMATCH",
  "M3_ANOMALY_COUNT", "M3_ANOMALY_SEVERITY", "M3_ANOMALY_FLAGS",
  "M3_STATE_SOURCE_T1", "M3_STATE_SOURCE_T2",
  "M3_LATENT_STATE_T1", "M3_LATENT_STATE_T2",
  "M3_ACTIVE_FRAC_T1", "M3_ACTIVE_FRAC_T2",
  "M3_STORAGE_FRAC_T1", "M3_STORAGE_FRAC_T2",
  "M3_STAB_FP_FRAC_T1", "M3_STAB_FP_FRAC_T2",
  "M3_UNRESOLVED_FRAC_T1", "M3_UNRESOLVED_FRAC_T2",
  "M3_STATE_SUM_T1", "M3_STATE_SUM_T2",
  "M3_BACKGROUND_FRAC", "M3_STABLE_EVID_FRAC",
  "M3_STATE_SUPPORT_T1", "M3_STATE_SUPPORT_T2", "M3_STATE_CONF_T1", "M3_STATE_CONF_T2",
  "M3_MIXED_T1", "M3_MIXED_T2", "STORAGE_AGE_YR_T1", "STORAGE_AGE_YR_T2",
  "STORAGE_START_YMD_T1", "STORAGE_START_YMD_T2", "STORAGE_CLOCK_RESET_T2",
  "QA_ACTIVE_BELOW_THRESHOLD", "QA_NONACTIVE_ABOVE_THRESHOLD",
  "QA_ACTIVE_TO_STABLE", "QA_STABILISE_TOO_EARLY",
  "QA_INITIAL_STABLE_NO_EVIDENCE", "QA_STORAGE_WITHOUT_HISTORY",
  "QA_STATE_FRACTION_SUM", "QA_CLOCK_INCONSISTENT", "QA_STATE_SOURCE_INCONSISTENT",
  "QA_LATENT_STATE_INCONSISTENT", "QA_BRIDGED_TRANS_INVALID",
  "M3_ACTIVE_STATE_THR", "M3_ACTIVE_CONTACT_THR", "M3_MIXED_FRAC_THR",
  "M3_BG_STATE_THR", "M3_STABILISE_YEARS", "M3_STABILISE_MODE", "M3_STABLE_EVID_THR",
  "M3_MODEL_ELIGIBLE_STRICT", "M3_MODEL_EXCLUSION_REASON",
  "E_EVT_RAW", "D_EVT_RAW",
  "INIT_FP", "BASE_RISK", "INIT_FP_COHORT",
  "BASE_REACTIVATE_RISK_SET_DERIVED", "BASE_REACTIVATE_EVT",
  "BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED", "BASE_REACTIVATE_EVT_PRIMARY"
)
require_fields(risk, required_core, "stage4_step3_core")

union_domain_fields <- c(
  "ASM_BLOCK_AREA_M2",
  "ASM_UNION_OVERLAP_M2",
  "ASM_UNION_FRAC",
  "ASM_OUTSIDE_UNION_M2",
  "ASM_UNION_CONTACT",
  "ASM_UNION_BOUNDARY",
  "ASM_UNION_CORE50"
)
if (isTRUE(RunUnionComparison)) {
  require_fields(risk, union_domain_fields, "union_domain_fields")
}

# Preserve the strict adjacent-event family before selecting the principal
# ambiguity-bridged family for KM/AG/Cox.
strict_snapshot_fields <- c(
  "REACTIVATE_EVT", "STORAGE_EVT", "STABILISE_EVT",
  "STORAGE_REWORK_EVT", "FP_STORAGE_EVT", "ANY_STATE_EVT",
  "REACTIVATE_RISK_SET", "STORAGE_RISK_SET", "STABILISE_RISK_SET",
  "STORAGE_REWORK_RISK_SET", "FP_STORAGE_RISK_SET", "ANY_STATE_RISK_SET",
  "BASE_REACTIVATE_RISK_SET_DERIVED", "BASE_REACTIVATE_EVT"
)
for (nm in strict_snapshot_fields) {
  risk[[paste0(nm, "_STRICT_AUDIT")]] <- risk[[nm]]
}

message("[Input] Authoritative Stage 4 Step 3 strict and primary semantic fields verified.")

# Independent Risk Table key QA. Duplicate interval rows would inflate exposure
# time and event counts even when the event/risk fields themselves are valid.
risk_key_qa <- tibble(
  check = c(
    "missing PLACE_ID",
    "missing BLOCK_ID",
    "duplicate PLACE_ID + y1 + y2 rows",
    "PLACE_ID maps to multiple BLOCK_ID values",
    "BLOCK_ID maps to multiple PLACE_ID values"
  ),
  n = c(
    sum(is.na(risk$PLACE_ID) | trimws(as.character(risk$PLACE_ID)) == ""),
    sum(is.na(risk$BLOCK_ID) | trimws(as.character(risk$BLOCK_ID)) == ""),
    nrow(
      risk %>%
        count(PLACE_ID, y1, y2, name = "n") %>%
        filter(n > 1L)
    ),
    nrow(
      risk %>%
        distinct(PLACE_ID, BLOCK_ID) %>%
        count(PLACE_ID, name = "n") %>%
        filter(n > 1L)
    ),
    nrow(
      risk %>%
        distinct(PLACE_ID, BLOCK_ID) %>%
        count(BLOCK_ID, name = "n") %>%
        filter(n > 1L)
    )
  )
)
write_csv(risk_key_qa, file.path(out_dir, "00_risk_table_key_QA.csv"))
if (any(risk_key_qa$n > 0, na.rm = TRUE)) {
  stop("Risk Table key integrity failure. See 00_risk_table_key_QA.csv.")
}

# Fail early on propagated fatal Module 3 semantic anomalies, but first write a
# complete row-level audit for diagnosis. Warning and mixed/unresolved rows are
# retained in the audit and later excluded only where a recognised state pair is required.
m3_semantic_qa <- risk %>%
  transmute(
    PLACE_ID, tstart_yr, tstop_yr,
    STATE1_ONTOLOGY = as.character(STATE1_ONTOLOGY),
    STATE2_ONTOLOGY = as.character(STATE2_ONTOLOGY),
    M3_ANOMALY_COUNT = as.integer(num_or_na(M3_ANOMALY_COUNT)),
    M3_ANOMALY_SEVERITY = toupper(as.character(M3_ANOMALY_SEVERITY)),
    M3_ANOMALY_FLAGS = as.character(M3_ANOMALY_FLAGS),
    M3_ACTIVE_FRAC_T1 = num_or_na(M3_ACTIVE_FRAC_T1),
    M3_ACTIVE_FRAC_T2 = num_or_na(M3_ACTIVE_FRAC_T2),
    M3_STORAGE_FRAC_T1 = num_or_na(M3_STORAGE_FRAC_T1),
    M3_STORAGE_FRAC_T2 = num_or_na(M3_STORAGE_FRAC_T2),
    M3_STAB_FP_FRAC_T1 = num_or_na(M3_STAB_FP_FRAC_T1),
    M3_STAB_FP_FRAC_T2 = num_or_na(M3_STAB_FP_FRAC_T2),
    M3_UNRESOLVED_FRAC_T1 = num_or_na(M3_UNRESOLVED_FRAC_T1),
    M3_UNRESOLVED_FRAC_T2 = num_or_na(M3_UNRESOLVED_FRAC_T2),
    M3_STATE_SUM_T1 = num_or_na(M3_STATE_SUM_T1),
    M3_STATE_SUM_T2 = num_or_na(M3_STATE_SUM_T2),
    M3_STATE_SUPPORT_T1 = num_or_na(M3_STATE_SUPPORT_T1),
    M3_STATE_SUPPORT_T2 = num_or_na(M3_STATE_SUPPORT_T2),
    M3_STATE_CONF_T1 = as.character(M3_STATE_CONF_T1),
    M3_STATE_CONF_T2 = as.character(M3_STATE_CONF_T2),
    M3_MIXED_T1 = int01(M3_MIXED_T1),
    M3_MIXED_T2 = int01(M3_MIXED_T2),
    STORAGE_AGE_YR_T1 = num_or_na(STORAGE_AGE_YR_T1),
    STORAGE_AGE_YR_T2 = num_or_na(STORAGE_AGE_YR_T2),
    STORAGE_START_YMD_T1 = as.character(STORAGE_START_YMD_T1),
    STORAGE_START_YMD_T2 = as.character(STORAGE_START_YMD_T2),
    STORAGE_CLOCK_RESET_T2 = int01(STORAGE_CLOCK_RESET_T2),
    QA_STATE_FRACTION_SUM = int01(QA_STATE_FRACTION_SUM),
    QA_CLOCK_INCONSISTENT = int01(QA_CLOCK_INCONSISTENT),
    QA_STATE_SOURCE_INCONSISTENT = int01(QA_STATE_SOURCE_INCONSISTENT),
    M3_ACTIVE_STATE_THR = num_or_na(M3_ACTIVE_STATE_THR),
    M3_ACTIVE_CONTACT_THR = num_or_na(M3_ACTIVE_CONTACT_THR),
    M3_MIXED_FRAC_THR = num_or_na(M3_MIXED_FRAC_THR),
    M3_BG_STATE_THR = num_or_na(M3_BG_STATE_THR),
    M3_STABILISE_YEARS = num_or_na(M3_STABILISE_YEARS),
    M3_STABILISE_MODE = as.integer(num_or_na(M3_STABILISE_MODE)),
    M3_STABLE_EVID_THR = num_or_na(M3_STABLE_EVID_THR),
    M3_MODEL_ELIGIBLE_STRICT = int01(M3_MODEL_ELIGIBLE_STRICT),
    M3_MODEL_EXCLUSION_REASON = as.character(M3_MODEL_EXCLUSION_REASON),
    M3_MODEL_ELIGIBLE_PRIMARY = int01(M3_MODEL_ELIGIBLE_PRIMARY),
    M3_MODEL_EXCLUSION_REASON_PRIMARY = as.character(M3_MODEL_EXCLUSION_REASON_PRIMARY),
    QA_LATENT_STATE_INCONSISTENT = int01(QA_LATENT_STATE_INCONSISTENT),
    QA_BRIDGED_TRANS_INVALID = int01(QA_BRIDGED_TRANS_INVALID),
    PRIMARY_EVENT_DEFINITION_MISMATCH = as.integer(num_or_na(PRIMARY_EVENT_DEFINITION_MISMATCH)),
    PRIMARY_RISK_DEFINITION_MISMATCH = as.integer(num_or_na(PRIMARY_RISK_DEFINITION_MISMATCH)),
    PRIMARY_EVENT_RISK_MISMATCH = int01(PRIMARY_EVENT_RISK_MISMATCH)
  )
write_csv(m3_semantic_qa, file.path(out_dir, "00_module3_semantic_anomaly_rows.csv"))

m3_semantic_summary <- m3_semantic_qa %>%
  summarise(
    rows = n(),
    fatal_rows = sum(M3_ANOMALY_SEVERITY == "FATAL", na.rm = TRUE),
    warning_rows = sum(M3_ANOMALY_SEVERITY == "WARNING", na.rm = TRUE),
    rows_with_flags = sum(M3_ANOMALY_COUNT > 0, na.rm = TRUE),
    mixed_t1 = sum(M3_MIXED_T1 == 1L, na.rm = TRUE),
    mixed_t2 = sum(M3_MIXED_T2 == 1L, na.rm = TRUE),
    strict_ineligible_rows = sum(M3_MODEL_ELIGIBLE_STRICT != 1L, na.rm = TRUE),
    primary_ineligible_rows = sum(M3_MODEL_ELIGIBLE_PRIMARY != 1L, na.rm = TRUE),
    latent_state_flag_rows = sum(QA_LATENT_STATE_INCONSISTENT != 0L, na.rm = TRUE),
    invalid_bridge_flag_rows = sum(QA_BRIDGED_TRANS_INVALID != 0L, na.rm = TRUE),
    primary_event_definition_mismatch_rows = sum(PRIMARY_EVENT_DEFINITION_MISMATCH != 0L, na.rm = TRUE),
    primary_risk_definition_mismatch_rows = sum(PRIMARY_RISK_DEFINITION_MISMATCH != 0L, na.rm = TRUE),
    primary_event_risk_mismatch_rows = sum(PRIMARY_EVENT_RISK_MISMATCH != 0L, na.rm = TRUE),
    state_fraction_flag_rows = sum(QA_STATE_FRACTION_SUM != 0L, na.rm = TRUE),
    storage_clock_flag_rows = sum(QA_CLOCK_INCONSISTENT != 0L, na.rm = TRUE),
    state_source_flag_rows = sum(QA_STATE_SOURCE_INCONSISTENT != 0L, na.rm = TRUE),
    active_state_threshold_values = paste(sort(unique(na.omit(M3_ACTIVE_STATE_THR))), collapse = ";"),
    active_contact_threshold_values = paste(sort(unique(na.omit(M3_ACTIVE_CONTACT_THR))), collapse = ";"),
    mixed_fraction_threshold_values = paste(sort(unique(na.omit(M3_MIXED_FRAC_THR))), collapse = ";"),
    background_threshold_values = paste(sort(unique(na.omit(M3_BG_STATE_THR))), collapse = ";"),
    stabilisation_year_values = paste(sort(unique(na.omit(M3_STABILISE_YEARS))), collapse = ";"),
    stabilisation_mode_values = paste(sort(unique(na.omit(M3_STABILISE_MODE))), collapse = ";"),
    stable_evidence_threshold_values = paste(sort(unique(na.omit(M3_STABLE_EVID_THR))), collapse = ";")
  )
write_csv(m3_semantic_summary, file.path(out_dir, "00_module3_semantic_anomaly_summary.csv"))

# ------------------------------------------------------------------
# v17.8f semantic contrast QA requested for warning diagnosis.
# These outputs are deliberately written before any fatal semantic stop.
# ------------------------------------------------------------------
if (isTRUE(RunSemanticContrastQA)) {
  warning_rows <- m3_semantic_qa %>%
    filter(M3_ANOMALY_SEVERITY == "WARNING")

  warning_flag_combinations <- warning_rows %>%
    mutate(
      M3_ANOMALY_FLAGS = trimws(as.character(M3_ANOMALY_FLAGS)),
      M3_ANOMALY_FLAGS = ifelse(is.na(M3_ANOMALY_FLAGS) | M3_ANOMALY_FLAGS == "", "<blank>", M3_ANOMALY_FLAGS)
    ) %>%
    count(M3_ANOMALY_FLAGS, sort = TRUE, name = "warning_rows") %>%
    mutate(
      warning_pct = ifelse(sum(warning_rows) > 0, 100 * warning_rows / sum(warning_rows), NA_real_)
    )
  write_csv(warning_flag_combinations, file.path(out_dir, "00_module3_warning_flag_combinations.csv"))

  warning_flags_exploded <- warning_rows %>%
    transmute(
      PLACE_ID, tstart_yr, tstop_yr,
      anomaly_flag = trimws(as.character(M3_ANOMALY_FLAGS))
    ) %>%
    mutate(anomaly_flag = ifelse(is.na(anomaly_flag) | anomaly_flag == "", "<blank>", anomaly_flag)) %>%
    tidyr::separate_rows(anomaly_flag, sep = "\\s*[;,|]+\\s*") %>%
    mutate(anomaly_flag = trimws(anomaly_flag)) %>%
    count(anomaly_flag, sort = TRUE, name = "warning_rows") %>%
    mutate(
      warning_pct = ifelse(sum(warning_rows) > 0, 100 * warning_rows / sum(warning_rows), NA_real_)
    )
  write_csv(warning_flags_exploded, file.path(out_dir, "00_module3_warning_flags_exploded.csv"))

  contrast_fields <- c(
    "M3_STATE_T1", "M3_STATE_T2",
    "ASM_STATE_T1_QA", "ASM_STATE_T2_QA",
    "M3_ASM_DISAGREE_T1", "M3_ASM_DISAGREE_T2", "M3_ASM_DISAGREE_ANY"
  )
  contrast_availability <- tibble(
    field = contrast_fields,
    present = contrast_fields %in% names(risk)
  )
  write_csv(contrast_availability, file.path(out_dir, "00_module3_vs_module4a_field_availability.csv"))

  # [FRAF archive / Historic/QA function: make_state_contrast]
  # Cross-check Module 3 authoritative endpoint states against Module 4a assemblage states for QA.
  make_state_contrast <- function(m3_field, asm_field, endpoint_label) {
    d <- risk %>%
      transmute(
        endpoint = endpoint_label,
        M3_state = canonical_state(.data[[m3_field]]),
        M4a_state = canonical_state(.data[[asm_field]])
      ) %>%
      mutate(
        comparable = M3_state != "UNRESOLVED" & M4a_state != "UNRESOLVED",
        agreement = comparable & M3_state == M4a_state
      )

    tab <- d %>%
      count(endpoint, M3_state, M4a_state, comparable, agreement, name = "n") %>%
      group_by(endpoint, M3_state) %>%
      mutate(row_total = sum(n), row_pct = ifelse(row_total > 0, 100 * n / row_total, NA_real_)) %>%
      ungroup()

    summary <- d %>%
      summarise(
        endpoint = endpoint_label,
        rows = n(),
        comparable_recognised_rows = sum(comparable, na.rm = TRUE),
        agreement_rows = sum(agreement, na.rm = TRUE),
        disagreement_rows = sum(comparable & !agreement, na.rm = TRUE),
        disagreement_pct_of_comparable = ifelse(
          sum(comparable, na.rm = TRUE) > 0,
          100 * sum(comparable & !agreement, na.rm = TRUE) / sum(comparable, na.rm = TRUE),
          NA_real_
        ),
        m3_unresolved_rows = sum(M3_state == "UNRESOLVED", na.rm = TRUE),
        m4a_unresolved_rows = sum(M4a_state == "UNRESOLVED", na.rm = TRUE)
      )
    list(table = tab, summary = summary)
  }

  if (all(c("M3_STATE_T1", "ASM_STATE_T1_QA") %in% names(risk))) {
    c1 <- make_state_contrast("M3_STATE_T1", "ASM_STATE_T1_QA", "T1")
    write_csv(c1$table, file.path(out_dir, "00_module3_vs_module4a_T1_matrix.csv"))
  } else {
    c1 <- NULL
  }
  if (all(c("M3_STATE_T2", "ASM_STATE_T2_QA") %in% names(risk))) {
    c2 <- make_state_contrast("M3_STATE_T2", "ASM_STATE_T2_QA", "T2")
    write_csv(c2$table, file.path(out_dir, "00_module3_vs_module4a_T2_matrix.csv"))
  } else {
    c2 <- NULL
  }

  contrast_summaries <- bind_rows(
    if (!is.null(c1)) c1$summary else NULL,
    if (!is.null(c2)) c2$summary else NULL
  )
  if (nrow(contrast_summaries) > 0L) {
    write_csv(contrast_summaries, file.path(out_dir, "00_module3_vs_module4a_disagreement_summary.csv"))
  }

  if (all(c("M3_ASM_DISAGREE_T1", "M3_ASM_DISAGREE_T2", "M3_ASM_DISAGREE_ANY") %in% names(risk))) {
    disagree_flag_summary <- risk %>%
      summarise(
        rows = n(),
        disagree_t1_rows = sum(int01(M3_ASM_DISAGREE_T1) == 1L, na.rm = TRUE),
        disagree_t2_rows = sum(int01(M3_ASM_DISAGREE_T2) == 1L, na.rm = TRUE),
        disagree_any_rows = sum(int01(M3_ASM_DISAGREE_ANY) == 1L, na.rm = TRUE)
      )
    write_csv(disagree_flag_summary, file.path(out_dir, "00_module3_vs_module4a_disagreement_flags.csv"))
  }
}

# [FRAF archive / logic boundary]
# Do not proceed through a fatal Module 3 semantic anomaly. A written QA report
# must identify affected rows before any transition inference is attempted.
if (m3_semantic_summary$fatal_rows[1] > 0) {
  stop(
    "Fatal Module 3 semantic anomalies are present. See ",
    "00_module3_semantic_anomaly_rows.csv and rerun Module 3B/3C before modelling."
  )
}

# [FRAF archive / workflow]
# Independent state QA: recompute fraction partitions, source provenance and
# storage-clock consistency before considering any event/risk-set estimates.
# Independent endpoint-partition, provenance and storage-clock QA. This does not
# trust the Module 3 anomaly flag alone; it recomputes the core invariants from
# the propagated fields before factor relabelling or modelling.
state_partition_clock_qa <- risk %>%
  transmute(
    PLACE_ID = as.character(PLACE_ID),
    tstart_yr = num_or_na(tstart_yr), tstop_yr = num_or_na(tstop_yr),
    y1 = as.character(y1), y2 = as.character(y2),
    s1 = canonical_state(STATE1_ONTOLOGY),
    s2 = canonical_state(STATE2_ONTOLOGY),
    source1 = toupper(trimws(as.character(M3_STATE_SOURCE_T1))),
    source2 = toupper(trimws(as.character(M3_STATE_SOURCE_T2))),
    latent1 = canonical_state(M3_LATENT_STATE_T1),
    latent2 = canonical_state(M3_LATENT_STATE_T2),
    a1 = num_or_na(M3_ACTIVE_FRAC_T1), a2 = num_or_na(M3_ACTIVE_FRAC_T2),
    d1 = num_or_na(M3_STORAGE_FRAC_T1), d2 = num_or_na(M3_STORAGE_FRAC_T2),
    f1 = num_or_na(M3_STAB_FP_FRAC_T1), f2 = num_or_na(M3_STAB_FP_FRAC_T2),
    u1 = num_or_na(M3_UNRESOLVED_FRAC_T1), u2 = num_or_na(M3_UNRESOLVED_FRAC_T2),
    sum1_reported = num_or_na(M3_STATE_SUM_T1), sum2_reported = num_or_na(M3_STATE_SUM_T2),
    support1 = num_or_na(M3_STATE_SUPPORT_T1), support2 = num_or_na(M3_STATE_SUPPORT_T2),
    background_frac = num_or_na(M3_BACKGROUND_FRAC),
    stable_evidence_frac = num_or_na(M3_STABLE_EVID_FRAC),
    active_threshold = num_or_na(M3_ACTIVE_STATE_THR),
    contact_threshold = num_or_na(M3_ACTIVE_CONTACT_THR),
    background_threshold = num_or_na(M3_BG_STATE_THR),
    stabilise_years = num_or_na(M3_STABILISE_YEARS),
    stabilise_mode = as.integer(num_or_na(M3_STABILISE_MODE)),
    stable_evidence_threshold = num_or_na(M3_STABLE_EVID_THR),
    e_raw = int01(E_EVT_RAW), d_raw = int01(D_EVT_RAW),
    age1 = num_or_na(STORAGE_AGE_YR_T1), age2 = num_or_na(STORAGE_AGE_YR_T2),
    start1 = na_if(trimws(as.character(STORAGE_START_YMD_T1)), ""),
    start2 = na_if(trimws(as.character(STORAGE_START_YMD_T2)), ""),
    reset2 = int01(STORAGE_CLOCK_RESET_T2),
    qa_active_below_reported = int01(QA_ACTIVE_BELOW_THRESHOLD),
    qa_nonactive_above_reported = int01(QA_NONACTIVE_ABOVE_THRESHOLD),
    qa_active_stable_reported = int01(QA_ACTIVE_TO_STABLE),
    qa_stabilise_early_reported = int01(QA_STABILISE_TOO_EARLY),
    qa_initial_stable_reported = int01(QA_INITIAL_STABLE_NO_EVIDENCE),
    qa_storage_history_reported = int01(QA_STORAGE_WITHOUT_HISTORY),
    qa_fraction_reported = int01(QA_STATE_FRACTION_SUM),
    qa_clock_reported = int01(QA_CLOCK_INCONSISTENT),
    qa_source_reported = int01(QA_STATE_SOURCE_INCONSISTENT)
  ) %>%
  group_by(PLACE_ID) %>%
  arrange(tstart_yr, tstop_yr, .by_group = TRUE) %>%
  mutate(
    is_initial = row_number() == 1L,
    previous_s2 = lag(s2),
    previous_age2 = lag(age2),
    previous_start2 = lag(start2)
  ) %>%
  ungroup() %>%
  mutate(
    duration = tstop_yr - tstart_yr,
    sum1 = a1 + d1 + f1 + u1,
    sum2 = a2 + d2 + f2 + u2,
    fraction_range_fail = as.integer(
      if_any(c(a1, a2, d1, d2, f1, f2, u1, u2), ~ is.na(.x) | .x < -1e-9 | .x > 1 + 1e-9)
    ),
    fraction_sum_fail = as.integer(
      is.na(sum1) | is.na(sum2) | abs(sum1 - 1) > 1e-6 | abs(sum2 - 1) > 1e-6 |
        is.na(sum1_reported) | is.na(sum2_reported) |
        abs(sum1_reported - 1) > 1e-6 | abs(sum2_reported - 1) > 1e-6
    ),
    expected_support1 = case_when(
      s1 == "ACTIVE_DOMAIN" ~ a1,
      s1 == "DEPOSITIONAL_STORAGE" ~ d1,
      s1 == "STABILISED_FLOODPLAIN" ~ f1,
      TRUE ~ u1
    ),
    expected_support2 = case_when(
      s2 == "ACTIVE_DOMAIN" ~ a2,
      s2 == "DEPOSITIONAL_STORAGE" ~ d2,
      s2 == "STABILISED_FLOODPLAIN" ~ f2,
      TRUE ~ u2
    ),
    support_fail = as.integer(
      is.na(support1) | is.na(support2) |
        abs(support1 - expected_support1) > 1e-6 |
        abs(support2 - expected_support2) > 1e-6
    ),
    active_support_fail = as.integer(
      is.na(active_threshold) |
        (s1 == "ACTIVE_DOMAIN" & (is.na(a1) | a1 + 1e-9 < active_threshold)) |
        (s2 == "ACTIVE_DOMAIN" & (is.na(a2) | a2 + 1e-9 < active_threshold)) |
        (s1 != "ACTIVE_DOMAIN" & !is.na(a1) & a1 >= active_threshold) |
        (s2 != "ACTIVE_DOMAIN" & !is.na(a2) & a2 >= active_threshold)
    ),
    direct_active_to_stable_fail = as.integer(
      s1 == "ACTIVE_DOMAIN" & s2 == "STABILISED_FLOODPLAIN"
    ),
    age_ok = !is.na(age2) & !is.na(stabilise_years) & age2 + 1e-9 >= stabilise_years,
    evidence_ok = !is.na(stable_evidence_frac) & !is.na(stable_evidence_threshold) &
      stable_evidence_frac + 1e-9 >= stable_evidence_threshold,
    stabilisation_rule_fail = as.integer(
      s1 == "DEPOSITIONAL_STORAGE" & s2 == "STABILISED_FLOODPLAIN" &
        case_when(
          stabilise_mode == 0L ~ !age_ok,
          stabilise_mode == 1L ~ !(age_ok | evidence_ok),
          stabilise_mode == 2L ~ !(age_ok & evidence_ok),
          TRUE ~ TRUE
        )
    ),
    initial_stable_provenance_fail = as.integer(
      is_initial & s1 == "STABILISED_FLOODPLAIN" &
        (is.na(background_frac) | is.na(background_threshold) |
           background_frac + 1e-9 < background_threshold) &
        (is.na(stable_evidence_frac) | is.na(stable_evidence_threshold) |
           stable_evidence_frac + 1e-9 < stable_evidence_threshold)
    ),
    # Match the authoritative Module 3B rule exactly. A boundary-mixed T1 row
    # may legitimately resolve from a latent Active Domain into Depositional
    # Storage even when the resolving interval has no raw deposition flag and
    # no pre-existing storage clock. That is a valid ambiguity bridge, not
    # storage without history.
    storage_without_history_fail = as.integer(
      s2 == "DEPOSITIONAL_STORAGE" &
        !s1 %in% c("ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN") &
        latent1 != "ACTIVE_DOMAIN" &
        d_raw == 0L & is.na(age1)
    ),
    initial_source_fail = as.integer(
      is_initial & !(
        (s1 == "ACTIVE_DOMAIN" & source1 == "DATED_ACTIVE_DOMAIN") |
          (s1 == "STABILISED_FLOODPLAIN" & source1 %in% c(
            "EXPLICIT_BACKGROUND_MASK", "DERIVED_CORRIDOR_MINUS_HISTORICAL_ACTIVE", "EXPLICIT_STABLE_EVIDENCE"
          )) |
          (s1 == "UNRESOLVED" & source1 %in% c(
            "BOUNDARY_MIXED_ACTIVE_CONTACT", "INITIAL_INACTIVE_WITHOUT_PROVENANCE"
          ))
      )
    ),
    t1_source_chain_fail = as.integer(!is_initial & source1 != "PREVIOUS_INTERVAL_T2"),
    t2_source_fail = as.integer(
      (s2 == "ACTIVE_DOMAIN" & source2 != "DATED_ACTIVE_DOMAIN") |
        (s2 == "DEPOSITIONAL_STORAGE" & !source2 %in% c(
          "ACTIVE_EXIT_DEPOSITION_CONFIRMED", "ACTIVE_EXIT_UNCONFIRMED_STORAGE",
          "STORAGE_REWORKED_BY_DEPOSITION", "STORAGE_CLOCK_CONTINUES",
          "FRESH_DEPOSITION_ON_STABLE_FLOODPLAIN", "DEPOSITION_FROM_UNRESOLVED",
          "STORAGE_RECOVERED_AFTER_AMBIGUITY"
        )) |
        (s2 == "STABILISED_FLOODPLAIN" & !source2 %in% c(
          "STORAGE_STABILISATION_RULE", "EXPLICIT_BACKGROUND_MASK",
          "DERIVED_CORRIDOR_MINUS_HISTORICAL_ACTIVE", "EXPLICIT_STABLE_EVIDENCE",
          "STABLE_STATE_PERSISTENCE"
        )) |
        (s2 == "UNRESOLVED" & source2 != "BOUNDARY_MIXED_ACTIVE_CONTACT" &
           source2 != "INSUFFICIENT_STATE_EVIDENCE")
    ),
    state_chain_fail = as.integer(!is_initial & (is.na(previous_s2) | s1 != previous_s2)),
    age_start_pair_fail = as.integer(xor(is.na(age1), is.na(start1)) | xor(is.na(age2), is.na(start2))),
    invalid_clock_state_fail = as.integer(
      (!s1 %in% c("DEPOSITIONAL_STORAGE", "UNRESOLVED") & (!is.na(age1) | !is.na(start1))) |
        (!s2 %in% c("DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN", "UNRESOLVED") &
           (!is.na(age2) | !is.na(start2)))
    ),
    reset_start_fail = as.integer(
      s2 == "DEPOSITIONAL_STORAGE" & reset2 == 1L &
        (is.na(age2) | abs(age2) > 1e-9 | is.na(start2) | start2 != y2)
    ),
    storage_increment_fail = as.integer(
      s1 == "DEPOSITIONAL_STORAGE" & s2 %in% c("DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN") &
        reset2 == 0L &
        (is.na(age1) | is.na(age2) | is.na(duration) |
           abs(age2 - (age1 + duration)) > 1e-6 | is.na(start1) | is.na(start2) | start1 != start2)
    ),
    suspended_clock_fail = as.integer(
      s2 == "UNRESOLVED" & !is.na(age1) &
        (is.na(age2) | abs(age2 - age1) > 1e-6 | is.na(start1) | is.na(start2) | start1 != start2)
    ),
    recovered_clock_fail = as.integer(
      s1 == "UNRESOLVED" & !is.na(age1) & s2 == "DEPOSITIONAL_STORAGE" & reset2 == 0L &
        (is.na(age2) | abs(age2 - age1) > 1e-6 | is.na(start1) | is.na(start2) | start1 != start2)
    ),
    clock_carry_fail = as.integer(
      !is_initial & previous_s2 %in% c("DEPOSITIONAL_STORAGE", "UNRESOLVED") &
        (xor(is.na(previous_age2), is.na(age1)) |
           (!is.na(previous_age2) & abs(previous_age2 - age1) > 1e-6) |
           xor(is.na(previous_start2), is.na(start1)) |
           (!is.na(previous_start2) & previous_start2 != start1))
    ),
    reported_flag_fail = as.integer(
      qa_active_below_reported != as.integer(
        (s1 == "ACTIVE_DOMAIN" & (is.na(a1) | a1 + 1e-9 < active_threshold)) |
          (s2 == "ACTIVE_DOMAIN" & (is.na(a2) | a2 + 1e-9 < active_threshold))
      ) |
        qa_nonactive_above_reported != as.integer(
          (s1 != "ACTIVE_DOMAIN" & !is.na(a1) & a1 >= active_threshold) |
            (s2 != "ACTIVE_DOMAIN" & !is.na(a2) & a2 >= active_threshold)
        ) |
        qa_active_stable_reported != direct_active_to_stable_fail |
        qa_stabilise_early_reported != stabilisation_rule_fail |
        qa_initial_stable_reported != initial_stable_provenance_fail |
        qa_storage_history_reported != storage_without_history_fail
    ),
    propagated_fatal_flag = as.integer(
      qa_fraction_reported != 0L | qa_clock_reported != 0L | qa_source_reported != 0L
    ),
    fatal_partition_clock_fail = as.integer(
      fraction_range_fail == 1L | fraction_sum_fail == 1L | support_fail == 1L |
        active_support_fail == 1L | direct_active_to_stable_fail == 1L |
        stabilisation_rule_fail == 1L | initial_stable_provenance_fail == 1L |
        storage_without_history_fail == 1L | initial_source_fail == 1L |
        t1_source_chain_fail == 1L | t2_source_fail == 1L | state_chain_fail == 1L |
        age_start_pair_fail == 1L | invalid_clock_state_fail == 1L |
        reset_start_fail == 1L | storage_increment_fail == 1L |
        suspended_clock_fail == 1L | recovered_clock_fail == 1L |
        clock_carry_fail == 1L | reported_flag_fail == 1L | propagated_fatal_flag == 1L
    )
  )

qa_flag_columns <- c(
  "fraction_range_fail", "fraction_sum_fail", "support_fail", "active_support_fail",
  "direct_active_to_stable_fail", "stabilisation_rule_fail",
  "initial_stable_provenance_fail", "storage_without_history_fail",
  "initial_source_fail", "t1_source_chain_fail", "t2_source_fail", "state_chain_fail",
  "age_start_pair_fail", "invalid_clock_state_fail", "reset_start_fail",
  "storage_increment_fail", "suspended_clock_fail", "recovered_clock_fail",
  "clock_carry_fail", "reported_flag_fail", "propagated_fatal_flag"
)
state_partition_clock_qa$R_QA_ANOMALY_FLAGS <- apply(
  state_partition_clock_qa[, qa_flag_columns, drop = FALSE],
  1,
  function(z) {
    hit <- qa_flag_columns[!is.na(z) & as.integer(z) == 1L]
    if (length(hit) == 0) "NONE" else paste(hit, collapse = ";")
  }
)
state_partition_clock_qa$R_QA_SEVERITY <- ifelse(
  state_partition_clock_qa$fatal_partition_clock_fail == 1L, "FATAL", "NONE"
)
write_csv(state_partition_clock_qa, file.path(out_dir, "00_state_partition_storage_clock_QA.csv"))

state_partition_clock_summary <- state_partition_clock_qa %>%
  summarise(
    rows = n(),
    across(all_of(qa_flag_columns), ~ sum(.x, na.rm = TRUE)),
    fatal_rows = sum(fatal_partition_clock_fail, na.rm = TRUE)
  )
write_csv(state_partition_clock_summary, file.path(out_dir, "00_state_partition_storage_clock_summary.csv"))

# Write and report only fatal rows as a compact diagnostic. This avoids forcing
# the user to inspect the complete interval table when a single invariant fails.
state_partition_clock_fatal <- state_partition_clock_qa %>%
  filter(fatal_partition_clock_fail == 1L)
write_csv(
  state_partition_clock_fatal,
  file.path(out_dir, "00_state_partition_storage_clock_FATAL_rows.csv")
)

if (state_partition_clock_summary$fatal_rows[1] > 0) {
  flag_totals <- unlist(state_partition_clock_summary[1, qa_flag_columns], use.names = TRUE)
  flag_totals <- flag_totals[!is.na(flag_totals) & flag_totals > 0]
  message("State-partition/storage-clock QA: fatal rows = ",
          state_partition_clock_summary$fatal_rows[1])
  if (length(flag_totals) > 0) {
    message(
      "Failing QA totals: ",
      paste(names(flag_totals), as.integer(flag_totals), sep = "=", collapse = "; ")
    )
  }
}

# A near-zero Active→Active proportion usually indicates that water/channel
# polygons, rather than the composite Jamuna ACTIVE zone, were supplied as the
# dated Active Domain input. This is an interval warning, not an automatic fatal.
active_persistence_qa <- state_partition_clock_qa %>%
  group_by(y1, y2) %>%
  summarise(
    active_start_n = sum(s1 == "ACTIVE_DOMAIN", na.rm = TRUE),
    active_to_active_n = sum(s1 == "ACTIVE_DOMAIN" & s2 == "ACTIVE_DOMAIN", na.rm = TRUE),
    active_to_active_prop = ifelse(active_start_n > 0, active_to_active_n / active_start_n, NA_real_),
    QA_LOW_ACTIVE_PERSISTENCE = as.integer(
      active_start_n >= 20 & !is.na(active_to_active_prop) & active_to_active_prop < 0.01
    ),
    .groups = "drop"
  )
write_csv(active_persistence_qa, file.path(out_dir, "00_active_domain_persistence_QA.csv"))
if (any(active_persistence_qa$QA_LOW_ACTIVE_PERSISTENCE == 1L, na.rm = TRUE)) {
  warning(
    "One or more intervals have <1% Active Domain persistence from at least 20 active-start rows. ",
    "For Jamuna, verify that the dated inputs are composite ACTIVE-zone polygons rather than water-only polygons."
  )
}

if (state_partition_clock_summary$fatal_rows[1] > 0) {
  stop(
    "State-partition/provenance/storage-clock integrity failure. See ",
    "00_state_partition_storage_clock_FATAL_rows.csv and ",
    "00_state_partition_storage_clock_summary.csv before modelling."
  )
}

# v17.10.8: every downstream use of the row-level partition/clock QA is complete.
# This table is exceptionally wide and has one row per interval-place observation;
# retaining it through the Cox and union-comparison stages needlessly increases
# peak memory. The compact summary remains available for later provenance notes.
rm(state_partition_clock_qa, state_partition_clock_fatal)
invisible(gc(full = TRUE))
message("[Memory] Released row-level state-partition/storage-clock QA after validation.")

# Stage 4 Step 3 v6.6 writes strict and primary state-native event/risk fields. Older tables may only
# contain E_evt/D_evt and binary state fields, so conservative compatibility
# aliases are derived where possible.
if (!"BLOCK_ID" %in% names(risk)) risk$BLOCK_ID <- risk$PLACE_ID
if (!"A_block" %in% names(risk)) risk$A_block <- NA_real_
if (!"A_E" %in% names(risk)) risk$A_E <- NA_real_
if (!"A_D" %in% names(risk)) risk$A_D <- NA_real_
if (!"state1" %in% names(risk)) risk$state1 <- NA_character_
if (!"state2" %in% names(risk)) risk$state2 <- NA_character_
if (!"at_risk" %in% names(risk)) risk$at_risk <- 1L
if (!"Enter" %in% names(risk)) risk$Enter <- 0L
if (!"Exit" %in% names(risk)) risk$Exit <- 0L

# Initial-floodplain cohort fields from Module 3b / Step 3.
# Record whether the revised dynamic first-event fields were present before
# compatibility defaults are created.
source_has_base_dynamic <- TRUE

# [FRAF archive / workflow]
# Baseline eligibility is a cohort definition, NOT evidence of SF state.
# Do not replace broad FP eligibility or transition-specific risk sets with INIT_FP.
# These define the baseline cohort: places initially outside the first active-domain
# / first EA pair but inside the buffered study corridor. They are cohort flags, not
# state labels. Missing fields are filled conservatively so older risk tables still run.
for (nm in c("INIT_FP", "BASE_RISK", "BASE_REACTIVATE_RISK_SET",
             "BASE_REACTIVATE_RISK_SET_DERIVED", "INIT_FP_COHORT", "BASE_REACTIVATE_EVT")) {
  if (!nm %in% names(risk)) risk[[nm]] <- 0L
}
for (nm in c("INIT_FP_AREA", "INIT_FP_PROP")) {
  if (!nm %in% names(risk)) risk[[nm]] <- NA_real_
}
if (!"BASE_RISK_DEF" %in% names(risk)) risk$BASE_RISK_DEF <- NA_character_


# [FRAF archive / workflow]
# Temporal spatial QA: prefer geometry observed at interval start, and distinguish
# a static reference centreline from dated AD margins or channel positions.
# Distance covariate check. KM uses the whole at-risk floodplain as the
# baseline risk set, then produces separate stratified curves by:
#   1. designated/reference centreline distance,
#   2. active-zone distance, and
#   3. water distance.
# Preferred centreline fields are DIST_CL_REF and DIST_CL_REF_BIN.
# In the authoritative Stage 4 Step 3 v6.6 interface, *_CURR spatial fields
# are calculated from geometry at interval start y1. The explicit local Mamoré
# *_PREV geometry fields are also matched exactly to y1; PREV denotes their
# lookup/history source, not an earlier outcome-time geometry. If a distance is
# present without a corresponding bin field, the script derives coarse bins.
centreline_distance_candidates <- c(
  "DIST_CL_REF", "DIST_CL_CURR", "DIST_CL_PREV", "DIST_CL_INIT", "DIST_CL_MEAN"
)
centreline_bin_candidates <- c(
  "DIST_CL_REF_BIN", "DIST_CL_CURR_BIN", "DIST_CL_PREV_BIN", "DIST_CL_INIT_BIN"
)
active_distance_candidates <- c(
  "DIST_ACTIVE_CURR", "DIST_ACTIVE_PREV", "DIST_ACTIVE_INIT", "DIST_ACTIVE_MEAN"
)
active_bin_candidates <- c(
  "DIST_ACTIVE_CURR_BIN", "DIST_ACTIVE_PREV_BIN"
)
water_distance_candidates <- c(
  "DIST_WATER_CURR", "DIST_WATER_PREV", "DIST_WATER_INIT", "DIST_WATER_MEAN"
)
water_bin_candidates <- c(
  "DIST_WATER_CURR_BIN", "DIST_WATER_PREV_BIN"
)

# Revised Module 4a / Stage 4 Step 2 / Stage 4 Step 3 persistence fields.
# Stage 4 Step 2 normally prefixes Module 4a fields with ASM_, while older Risk Tables may also carry
# selected fields unprefixed.  These candidates allow both forms.
fp_condition_candidates <- c("FP_CONDITION", "ASM_FP_CONDITION")
final_onto_raw_candidates <- c("FINAL_ONTO_RAW", "ASM_FINAL_ONTO_RAW")
surface_age_est_candidates <- c("SURFACE_AGE_EST", "ASM_SURFACE_AGE_EST")
fp_stab_candidates <- c("FP_STAB", "ASM_FP_STAB")
fp_recent_candidates <- c("FP_RECENT", "ASM_FP_RECENT")
fp_reworked_candidates <- c("FP_REWORKED", "ASM_FP_REWORKED")

if (!any(centreline_distance_candidates %in% names(risk))) {
  warning("No centreline-distance fields were found. KM baseline will still run, but centreline-binned KM will be skipped.")
}
if (!any(active_distance_candidates %in% names(risk))) {
  warning("No active-zone-distance fields were found. Active-zone-binned KM will be skipped.")
}
if (!any(water_distance_candidates %in% names(risk))) {
  warning("No water-distance fields were found. Water-distance-binned KM will be skipped.")
}

# [FRAF archive / Historic/QA function: choose_first_field]
# Select the first available field from an ordered list of compatible source aliases.
choose_first_field <- function(dat, candidates) {
  hit <- candidates[candidates %in% names(dat)]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
}

centreline_dist_field <- choose_first_field(risk, centreline_distance_candidates)
centreline_bin_field  <- choose_first_field(risk, centreline_bin_candidates)
active_dist_field <- choose_first_field(risk, active_distance_candidates)
active_bin_field  <- choose_first_field(risk, active_bin_candidates)
water_dist_field <- choose_first_field(risk, water_distance_candidates)
water_bin_field  <- choose_first_field(risk, water_bin_candidates)

message("Centreline distance field selected: ", centreline_dist_field)
message("Centreline distance-bin field selected: ", centreline_bin_field)
message("Active-zone distance field selected: ", active_dist_field)
message("Active-zone distance-bin field selected: ", active_bin_field)
message("Water distance field selected: ", water_dist_field)
message("Water distance-bin field selected: ", water_bin_field)

fp_condition_field <- choose_first_field(risk, fp_condition_candidates)
final_onto_raw_field <- choose_first_field(risk, final_onto_raw_candidates)
surface_age_est_field <- choose_first_field(risk, surface_age_est_candidates)
fp_stab_field <- choose_first_field(risk, fp_stab_candidates)
fp_recent_field <- choose_first_field(risk, fp_recent_candidates)
fp_reworked_field <- choose_first_field(risk, fp_reworked_candidates)

message("Floodplain-condition field selected: ", fp_condition_field)
message("Raw final-state field selected: ", final_onto_raw_field)
message("Surface-age-estimate field selected: ", surface_age_est_field)
message("FP_STAB field selected: ", fp_stab_field)
message("FP_RECENT field selected: ", fp_recent_field)
message("FP_REWORKED field selected: ", fp_reworked_field)

# Stage 4 Step 3 v6.6 strict fields are mandatory for audit. R does not reconstruct
# named events, state transitions or transition-specific risk sets.
input_has_reactivate_evt <- TRUE
input_has_storage_evt <- TRUE
input_has_stabilise_evt <- TRUE
input_has_reactivate_trans <- TRUE
input_has_storage_trans <- TRUE
input_has_stabilise_trans <- TRUE
input_has_any_state_evt <- TRUE
input_has_reactivate_risk <- TRUE
input_has_storage_risk <- TRUE
input_has_stabilise_risk <- TRUE
input_has_any_state_risk <- TRUE
input_has_base_dynamic <- TRUE

# [FRAF archive / logic boundary]
# Retain legacy E/D flags separately as provenance evidence. Reconstructed
# state-defined events must not be overwritten by earlier binary labels.
risk$.LEGACY_E_EVT <- if ("E_evt" %in% names(risk)) int01(risk$E_evt) else rep(NA_integer_, nrow(risk))
risk$.LEGACY_D_EVT <- if ("D_evt" %in% names(risk)) int01(risk$D_evt) else rep(NA_integer_, nrow(risk))
for (nm in c("E_EVT_RAW", "D_EVT_RAW", "E_CONFIRM_AVAILABLE", "D_CONFIRM_AVAILABLE")) {
  if (!nm %in% names(risk)) risk[[nm]] <- NA_integer_
}

risk <- risk %>%
  mutate(
    PLACE_ID = as.character(PLACE_ID),
    BLOCK_ID = as.character(BLOCK_ID),
    tstart_yr = as.numeric(tstart_yr),
    tstop_yr  = as.numeric(tstop_yr),
    A_block = as.numeric(A_block),
    A_E = as.numeric(A_E),
    A_D = as.numeric(A_D),
    at_risk = int01(at_risk, 1L),
    Enter = int01(Enter),
    Exit = int01(Exit),
    INIT_FP = int01(INIT_FP),
    INIT_FP_AREA = num_or_na(INIT_FP_AREA),
    INIT_FP_PROP = num_or_na(INIT_FP_PROP),
    BASE_RISK = int01(BASE_RISK),
    BASE_REACTIVATE_RISK_SET = int01(BASE_REACTIVATE_RISK_SET),
    BASE_REACTIVATE_RISK_SET_DERIVED = int01(BASE_REACTIVATE_RISK_SET_DERIVED),
    INIT_FP_COHORT = int01(INIT_FP_COHORT),
    BASE_REACTIVATE_EVT = int01(BASE_REACTIVATE_EVT),
    BASE_RISK_DEF = as.character(BASE_RISK_DEF),
    duration = tstop_yr - tstart_yr
  ) %>%
  filter(
    !is.na(PLACE_ID),
    PLACE_ID != "",
    !is.na(tstart_yr),
    !is.na(tstop_yr),
    tstop_yr > tstart_yr
  )

legacy_e_evt <- risk$.LEGACY_E_EVT
legacy_d_evt <- risk$.LEGACY_D_EVT

# [FRAF archive / workflow]
# Ontology preflight: preserve Module 3 endpoint classification and recover
# legacy labels conservatively; non-active alone cannot distinguish DS from SF.
# State labels. Revised Step 3 fields are preferred; older tables are mapped
# conservatively. Binary inactivity alone is not interpreted as Depositional
# Storage.
if (!"STATE1_ONTOLOGY" %in% names(risk)) {
  if ("ONTO_STATE_T1" %in% names(risk)) {
    risk$STATE1_ONTOLOGY <- canonical_state(risk$ONTO_STATE_T1)
  } else {
    domain1 <- if ("DOMAIN_T1" %in% names(risk)) risk$DOMAIN_T1 else NA_character_
    surface1 <- if ("SURFACE_T1" %in% names(risk)) risk$SURFACE_T1 else NA_character_
    risk$STATE1_ONTOLOGY <- derive_state_ontology(domain1, surface1, risk$state1)
  }
}
if (!"STATE2_ONTOLOGY" %in% names(risk)) {
  if ("ONTO_STATE_T2" %in% names(risk)) {
    risk$STATE2_ONTOLOGY <- canonical_state(risk$ONTO_STATE_T2)
  } else {
    domain2 <- if ("DOMAIN_T2" %in% names(risk)) risk$DOMAIN_T2 else NA_character_
    surface2 <- if ("SURFACE_T2" %in% names(risk)) risk$SURFACE_T2 else NA_character_
    risk$STATE2_ONTOLOGY <- derive_state_ontology(domain2, surface2, risk$state2)
  }
}

risk$STATE1_ONTOLOGY <- canonical_state(risk$STATE1_ONTOLOGY)
risk$STATE2_ONTOLOGY <- canonical_state(risk$STATE2_ONTOLOGY)

# Stage 4 Step 3 supplies the authoritative strict transition and event fields.
# Avoid storing separate state-derived event vectors here: later grouped ordering
# operations can reorder rows and detach external vectors from their source rows.

# Use Step 3 transition/event fields directly. Strict event integrity is checked
# later against the corresponding authoritative *_TRANS fields in the same rows.
risk$REACTIVATE_TRANS <- int01(risk$REACTIVATE_TRANS)
risk$STORAGE_TRANS <- int01(risk$STORAGE_TRANS)
risk$STABILISE_TRANS <- int01(risk$STABILISE_TRANS)
risk$STORAGE_REWORK_TRANS <- int01(risk$STORAGE_REWORK_TRANS)
risk$FP_STORAGE_TRANS <- int01(risk$FP_STORAGE_TRANS)
risk$ANY_STATE_EVT <- int01(risk$ANY_STATE_EVT)
risk$REACTIVATE_EVT <- int01(risk$REACTIVATE_EVT)
risk$STORAGE_EVT <- int01(risk$STORAGE_EVT)
risk$STABILISE_EVT <- int01(risk$STABILISE_EVT)
risk$STORAGE_REWORK_EVT <- int01(risk$STORAGE_REWORK_EVT)
risk$FP_STORAGE_EVT <- int01(risk$FP_STORAGE_EVT)
risk$REACTIVATE_CONFIRMED <- int01(risk$REACTIVATE_CONFIRMED)
risk$STORAGE_CONFIRMED <- int01(risk$STORAGE_CONFIRMED)
risk$STABILISE_CONFIRMED <- int01(risk$STABILISE_CONFIRMED)
risk$STORAGE_REWORK_CONFIRMED <- int01(risk$STORAGE_REWORK_CONFIRMED)
risk$FP_STORAGE_CONFIRMED <- int01(risk$FP_STORAGE_CONFIRMED)
risk$E_EVT_RAW <- ifelse(!is.na(num_or_na(risk$E_EVT_RAW)), int01(risk$E_EVT_RAW), risk$.LEGACY_E_EVT)
risk$D_EVT_RAW <- ifelse(!is.na(num_or_na(risk$D_EVT_RAW)), int01(risk$D_EVT_RAW), risk$.LEGACY_D_EVT)
risk$E_CONFIRM_AVAILABLE <- ifelse(!is.na(risk$E_EVT_RAW), 1L, int01(risk$E_CONFIRM_AVAILABLE))
risk$D_CONFIRM_AVAILABLE <- ifelse(!is.na(risk$D_EVT_RAW), 1L, int01(risk$D_CONFIRM_AVAILABLE))

# Distinguish named transitions from any state change.
risk$ANY_CONFIRMED_EVT <- ifelse(
  risk$REACTIVATE_EVT == 1L |
    risk$STORAGE_EVT == 1L |
    risk$STABILISE_EVT == 1L |
    risk$STORAGE_REWORK_EVT == 1L |
    risk$FP_STORAGE_EVT == 1L,
  1L, 0L
)

# Compatibility aliases retained for existing output consumers.
risk$REACTIVATE_EVT_PURE <- risk$REACTIVATE_TRANS
risk$STORAGE_EVT_PURE <- risk$STORAGE_TRANS
risk$STABILISE_EVT_PURE <- risk$STABILISE_TRANS
risk$STORAGE_REWORK_EVT_PURE <- risk$STORAGE_REWORK_TRANS
risk$FP_STORAGE_EVT_PURE <- risk$FP_STORAGE_TRANS
risk$ANY_ONTO_EVT_PURE <- risk$ANY_STATE_EVT
risk$ANY_ONTO_EVT <- risk$ANY_STATE_EVT
risk$E_evt <- risk$REACTIVATE_EVT
risk$D_evt <- risk$STORAGE_EVT
risk$ANY_EVT <- risk$ANY_CONFIRMED_EVT
risk$.LEGACY_E_EVT <- NULL
risk$.LEGACY_D_EVT <- NULL

risk$EVENT_ONTOLOGY <- display_event(
  risk$REACTIVATE_EVT,
  risk$STORAGE_EVT,
  risk$STABILISE_EVT
)
risk$EVENT_ONTOLOGY_PURE <- display_event(
  risk$REACTIVATE_TRANS,
  risk$STORAGE_TRANS,
  risk$STABILISE_TRANS
)
risk$EVENT_STATE <- display_state_event(
  risk$REACTIVATE_EVT,
  risk$STORAGE_EVT,
  risk$STABILISE_EVT,
  risk$STORAGE_REWORK_EVT,
  risk$FP_STORAGE_EVT,
  risk$REACTIVATE_TRANS,
  risk$STORAGE_TRANS,
  risk$ANY_STATE_EVT,
  risk$STATE1_ONTOLOGY,
  risk$STATE2_ONTOLOGY
)
risk$event_class <- risk$EVENT_STATE

# Revised Module 4a persistence/floodplain-condition fields are descriptive
# interpretation fields, not the three-state event engine.
risk$FP_CONDITION_MODEL <- if (!is.na(fp_condition_field)) {
  normalise_fp_condition(risk[[fp_condition_field]], risk$STATE2_ONTOLOGY)
} else {
  normalise_fp_condition(NA_character_, risk$STATE2_ONTOLOGY)
}
risk$FINAL_ONTO_RAW_MODEL <- if (!is.na(final_onto_raw_field)) as.character(risk[[final_onto_raw_field]]) else NA_character_
risk$SURFACE_AGE_EST_MODEL <- if (!is.na(surface_age_est_field)) num_or_na(risk[[surface_age_est_field]]) else NA_real_
risk$FP_STAB_MODEL <- if (!is.na(fp_stab_field)) {
  num_or_na(risk[[fp_stab_field]])
} else {
  ifelse(risk$FP_CONDITION_MODEL %in% c("Recent floodplain", "Persistent floodplain", "Reworked floodplain"), 1, 0)
}
risk$FP_RECENT_MODEL <- if (!is.na(fp_recent_field)) {
  num_or_na(risk[[fp_recent_field]])
} else {
  ifelse(risk$FP_CONDITION_MODEL == "Recent floodplain", 1, 0)
}
risk$FP_REWORKED_MODEL <- if (!is.na(fp_reworked_field)) {
  num_or_na(risk[[fp_reworked_field]])
} else {
  ifelse(risk$FP_CONDITION_MODEL == "Reworked floodplain", 1, 0)
}

# [FRAF archive / code note]
# Model event semantics must be reconciled against authoritative Step 3 flags;
# the binary erosion/deposition legacy interface is not a fourth state.
# ============================================================
# LEGACY STORAGE-STABILISATION THRESHOLD QA (not used as main event engine)
# ============================================================
# Revised Module 4a promotes long-lived quiet storage before Stage 4 Step 3.
# This R-side threshold is retained only as a diagnostic comparison.

stab_threshold_yrs <- 20

risk <- risk %>%
  arrange(PLACE_ID, tstart_yr, tstop_yr) %>%
  group_by(PLACE_ID) %>%
  mutate(
    interval_yrs = pmax(0, tstop_yr - tstart_yr),
    active_now_thresh = STATE2_ONTOLOGY == "ACTIVE_DOMAIN",
    storage_now_thresh = STATE2_ONTOLOGY == "DEPOSITIONAL_STORAGE"
  ) %>%
  group_modify(~{
    d <- .x
    n <- nrow(d)
    storage_clock <- numeric(n)
    elapsed <- 0
    in_storage <- FALSE

    for (i in seq_len(n)) {
      if (isTRUE(d$active_now_thresh[i])) {
        elapsed <- 0
        in_storage <- FALSE
      } else if (isTRUE(d$storage_now_thresh[i]) || in_storage) {
        in_storage <- TRUE
        elapsed <- elapsed + d$interval_yrs[i]
      }
      storage_clock[i] <- elapsed
    }

    d$STORAGE_YRS <- storage_clock
    d
  }) %>%
  ungroup() %>%
  mutate(
    STATE2_ONTOLOGY_THRESH = case_when(
      STATE2_ONTOLOGY == "ACTIVE_DOMAIN" ~ "ACTIVE_DOMAIN",
      STORAGE_YRS >= stab_threshold_yrs ~ "STABILISED_FLOODPLAIN",
      STORAGE_YRS > 0 ~ "DEPOSITIONAL_STORAGE",
      TRUE ~ STATE2_ONTOLOGY
    )
  )

risk <- risk %>%
  group_by(PLACE_ID) %>%
  arrange(tstart_yr, tstop_yr, .by_group = TRUE) %>%
  mutate(
    STATE1_ONTOLOGY_THRESH = lag(STATE2_ONTOLOGY_THRESH, default = first(STATE1_ONTOLOGY))
  ) %>%
  ungroup()

risk$STABILISE_EVT_THRESH <- ifelse(
  risk$STATE1_ONTOLOGY_THRESH == "DEPOSITIONAL_STORAGE" &
    risk$STATE2_ONTOLOGY_THRESH == "STABILISED_FLOODPLAIN",
  1L,
  0L
)

risk$STORAGE_EVT_THRESH <- ifelse(
  risk$STATE1_ONTOLOGY_THRESH == "ACTIVE_DOMAIN" &
    risk$STATE2_ONTOLOGY_THRESH == "DEPOSITIONAL_STORAGE",
  1L,
  0L
)

risk$REACTIVATE_EVT_THRESH <- ifelse(
  risk$STATE1_ONTOLOGY_THRESH == "STABILISED_FLOODPLAIN" &
    risk$STATE2_ONTOLOGY_THRESH == "ACTIVE_DOMAIN",
  1L,
  0L
)
risk$ANY_ONTO_EVT_THRESH <- ifelse(
  risk$REACTIVATE_EVT_THRESH == 1 | risk$STORAGE_EVT_THRESH == 1 | risk$STABILISE_EVT_THRESH == 1,
  1L, 0L
)

if (!"NEXT_EVENT_ONTOLOGY" %in% names(risk)) {
  r_next <- if ("REACTIVATE_NEXT" %in% names(risk)) risk$REACTIVATE_NEXT else NA_integer_
  s_next <- if ("STORAGE_NEXT" %in% names(risk)) risk$STORAGE_NEXT else NA_integer_
  st_next <- if ("STABILISE_NEXT" %in% names(risk)) risk$STABILISE_NEXT else NA_integer_
  risk$NEXT_EVENT_ONTOLOGY <- display_event(r_next, s_next, st_next)
}
if (!"STATE_NEXT_ONTOLOGY" %in% names(risk)) risk$STATE_NEXT_ONTOLOGY <- risk$STATE2_ONTOLOGY

risk <- risk %>%
  mutate(
    STATE1_ONTOLOGY = factor(display_state(STATE1_ONTOLOGY), levels = c("Active domain", "Depositional storage", "Stabilised floodplain", "Unresolved")),
    STATE2_ONTOLOGY = factor(display_state(STATE2_ONTOLOGY), levels = c("Active domain", "Depositional storage", "Stabilised floodplain", "Unresolved")),
    EVENT_ONTOLOGY = factor(as.character(EVENT_ONTOLOGY), levels = c("Reached by Active Domain", "Depositional storage", "Storage became stable floodplain", "Active Domain reach + storage", "Persistence")),
    EVENT_ONTOLOGY_PURE = factor(as.character(EVENT_ONTOLOGY_PURE), levels = c("Reached by Active Domain", "Depositional storage", "Storage became stable floodplain", "Active Domain reach + storage", "Persistence")),
    NEXT_EVENT_ONTOLOGY = factor(as.character(NEXT_EVENT_ONTOLOGY), levels = c("Reached by Active Domain", "Depositional storage", "Storage became stable floodplain", "Active Domain reach + storage", "Persistence")),
    EVENT_STATE = factor(
      as.character(EVENT_STATE),
      levels = c(
        "Reached by Active Domain",
        "Entered Depositional Storage",
        "Storage became Stabilised Floodplain",
        "Unconfirmed reactivation transition",
        "Unconfirmed storage transition",
        "Depositional Storage -> Active Domain",
        "Active Domain -> Stabilised Floodplain",
        "Stabilised Floodplain -> Depositional Storage",
        "Unclassified state transition",
        "Persistence"
      )
    ),
    event_class = as.character(EVENT_STATE)
  )

# Standardised distance-bin fields used by KM outputs.
# These do not change the original Risk Table fields.
risk$.DIST_CL_KM_FIELD <- NA_real_
risk$.DIST_CL_BIN_FIELD <- NA_character_
risk$.DIST_ACTIVE_KM_FIELD <- NA_real_
risk$.DIST_ACTIVE_BIN_FIELD <- NA_character_
risk$.DIST_WATER_KM_FIELD <- NA_real_
risk$.DIST_WATER_BIN_FIELD <- NA_character_

if (!is.na(centreline_dist_field)) {
  risk$.DIST_CL_KM_FIELD <- as.numeric(risk[[centreline_dist_field]]) / 1000
}
if (!is.na(active_dist_field)) {
  risk$.DIST_ACTIVE_KM_FIELD <- as.numeric(risk[[active_dist_field]]) / 1000
}
if (!is.na(water_dist_field)) {
  risk$.DIST_WATER_KM_FIELD <- as.numeric(risk[[water_dist_field]]) / 1000
}

if (!is.na(centreline_bin_field)) {
  risk$.DIST_CL_BIN_FIELD <- as.character(risk[[centreline_bin_field]])
} else if (!is.na(centreline_dist_field)) {
  risk$.DIST_CL_BIN_FIELD <- make_distance_bin(risk[[centreline_dist_field]])
  centreline_bin_field <- "derived_from_distance"
}

if (!is.na(active_bin_field)) {
  risk$.DIST_ACTIVE_BIN_FIELD <- as.character(risk[[active_bin_field]])
} else if (!is.na(active_dist_field)) {
  risk$.DIST_ACTIVE_BIN_FIELD <- make_distance_bin(risk[[active_dist_field]])
  active_bin_field <- "derived_from_distance"
}

if (!is.na(water_bin_field)) {
  risk$.DIST_WATER_BIN_FIELD <- as.character(risk[[water_bin_field]])
} else if (!is.na(water_dist_field)) {
  risk$.DIST_WATER_BIN_FIELD <- make_distance_bin(risk[[water_dist_field]])
  water_bin_field <- "derived_from_distance"
}

# Record-start landmark exposures are fixed within PLACE_ID. They provide a
# conventional fixed-stratum alternative to the descriptive time-varying KM
# curves based on interval-start exposure.
# [FRAF archive / code note]
# Compact helper: select first nonmissing values for QA/tables, not to
# fabricate a plausible state at an unresolved observation endpoint.
# [FRAF archive / Historic/QA function: first_nonmissing]
# Select the first observed non-missing element for interval/reach-level summaries.
first_nonmissing <- function(x) {
  z <- x[!is.na(x) & as.character(x) != ""]
  if (length(z) == 0L) return(NA)
  z[1]
}

risk <- risk %>%
  arrange(PLACE_ID, tstart_yr, tstop_yr) %>%
  group_by(PLACE_ID) %>%
  mutate(
    .DIST_CL_LANDMARK_BIN = first_nonmissing(.DIST_CL_BIN_FIELD),
    .DIST_ACTIVE_LANDMARK_BIN = first_nonmissing(.DIST_ACTIVE_BIN_FIELD),
    .DIST_WATER_LANDMARK_BIN = first_nonmissing(.DIST_WATER_BIN_FIELD)
  ) %>%
  ungroup()

# Transition-specific risk sets. Revised Stage 4 Step 3 fields are authoritative.
# State-derived versions are retained for QA and backward compatibility only.
reactivate_risk_from_state <- ifelse(
  as.character(risk$STATE1_ONTOLOGY) == "Stabilised floodplain", 1L, 0L
)
storage_risk_from_state <- ifelse(
  as.character(risk$STATE1_ONTOLOGY) == "Active domain", 1L, 0L
)
stabilise_risk_from_state <- ifelse(
  as.character(risk$STATE1_ONTOLOGY) == "Depositional storage", 1L, 0L
)
any_state_risk_from_state <- ifelse(
  as.character(risk$STATE1_ONTOLOGY) %in%
    c("Active domain", "Depositional storage", "Stabilised floodplain"),
  1L, 0L
)

risk$REACTIVATE_RISK_SET <- int01(risk$REACTIVATE_RISK_SET)
risk$STORAGE_RISK_SET <- int01(risk$STORAGE_RISK_SET)
risk$STABILISE_RISK_SET <- int01(risk$STABILISE_RISK_SET)
risk$STORAGE_REWORK_RISK_SET <- int01(risk$STORAGE_REWORK_RISK_SET)
risk$FP_STORAGE_RISK_SET <- int01(risk$FP_STORAGE_RISK_SET)
risk$ANY_STATE_RISK_SET <- int01(risk$ANY_STATE_RISK_SET)

# Compatibility aliases only.
risk$E_RISK_SET <- risk$REACTIVATE_RISK_SET
risk$D_RISK_SET <- risk$STORAGE_RISK_SET
risk$RISK_SET <- risk$ANY_STATE_RISK_SET
if (!"VALID_NEXT" %in% names(risk)) risk$VALID_NEXT <- 1L
risk$VALID_NEXT <- int01(risk$VALID_NEXT)

# Initial-floodplain first-event cohort is supplied by Stage 4 Step 3 and used directly.
risk <- risk %>%
  mutate(
    INIT_FP = int01(INIT_FP),
    BASE_RISK = int01(BASE_RISK),
    INIT_FP_COHORT = int01(INIT_FP_COHORT),
    BASE_REACTIVATE_RISK_SET_DERIVED = int01(BASE_REACTIVATE_RISK_SET_DERIVED),
    BASE_REACTIVATE_EVT = int01(BASE_REACTIVATE_EVT)
  )
risk$BASE_REACTIVATE_RISK_SET <- risk$BASE_REACTIVATE_RISK_SET_DERIVED

# Risk/event integrity QA. An event outside its corresponding T1 risk set is a
# pipeline error and must not enter KM/AG/Cox models.
risk_event_integrity <- tibble(
  check = c(
    "reactivation event outside reactivation risk set",
    "storage event outside storage risk set",
    "stabilisation event outside stabilisation risk set",
    "storage-rework event outside storage-rework risk set",
    "floodplain-storage event outside floodplain-storage risk set",
    "baseline event outside baseline first-event risk set",
    "reactivation risk differs from T1-derived risk",
    "storage risk differs from T1-derived risk",
    "stabilisation risk differs from T1-derived risk",
    "storage-rework risk differs from T1-derived risk",
    "floodplain-storage risk differs from T1-derived risk",
    "any-state risk differs from T1-derived risk",
    "reactivation event differs from transition",
    "storage event differs from transition",
    "stabilisation event differs from transition",
    "storage-rework event differs from transition",
    "floodplain-storage event differs from transition",
    "direct Active Domain to Stabilised Floodplain transitions",
    "unconfirmed reactivation transitions",
    "unconfirmed storage transitions"
  ),
  n = c(
    sum(risk$REACTIVATE_EVT == 1L & risk$REACTIVATE_RISK_SET != 1L, na.rm = TRUE),
    sum(risk$STORAGE_EVT == 1L & risk$STORAGE_RISK_SET != 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT == 1L & risk$STABILISE_RISK_SET != 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT == 1L & risk$STORAGE_REWORK_RISK_SET != 1L, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT == 1L & risk$FP_STORAGE_RISK_SET != 1L, na.rm = TRUE),
    sum(risk$BASE_REACTIVATE_EVT == 1L & risk$BASE_REACTIVATE_RISK_SET_DERIVED != 1L, na.rm = TRUE),
    sum(risk$REACTIVATE_RISK_SET != reactivate_risk_from_state, na.rm = TRUE),
    sum(risk$STORAGE_RISK_SET != storage_risk_from_state, na.rm = TRUE),
    sum(risk$STABILISE_RISK_SET != stabilise_risk_from_state, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_RISK_SET != stabilise_risk_from_state, na.rm = TRUE),
    sum(risk$FP_STORAGE_RISK_SET != reactivate_risk_from_state, na.rm = TRUE),
    sum(risk$ANY_STATE_RISK_SET != any_state_risk_from_state, na.rm = TRUE),
    # Compare against the authoritative strict transition fields retained in the
    # same rows. Do not compare with pre-sort external vectors: earlier arrange/
    # group_modify operations can reorder rows and create false mismatches.
    sum(risk$REACTIVATE_EVT != risk$REACTIVATE_TRANS, na.rm = TRUE),
    sum(risk$STORAGE_EVT != risk$STORAGE_TRANS, na.rm = TRUE),
    sum(risk$STABILISE_EVT != risk$STABILISE_TRANS, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT != risk$STORAGE_REWORK_TRANS, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT != risk$FP_STORAGE_TRANS, na.rm = TRUE),
    sum(as.character(risk$STATE1_ONTOLOGY) == "Active domain" & as.character(risk$STATE2_ONTOLOGY) == "Stabilised floodplain", na.rm = TRUE),
    sum(risk$REACTIVATE_TRANS == 1L & risk$REACTIVATE_EVT == 0L, na.rm = TRUE),
    sum(risk$STORAGE_TRANS == 1L & risk$STORAGE_EVT == 0L, na.rm = TRUE)
  ),
  fatal = c(rep(TRUE, 18), FALSE, FALSE)
)
write_csv(risk_event_integrity, file.path(out_dir, "00_transition_risk_process_confirmation_QA.csv"))

if (any(risk_event_integrity$n[risk_event_integrity$fatal] > 0, na.rm = TRUE)) {
  stop(
    "Risk-table integrity failure. See 00_transition_risk_process_confirmation_QA.csv. " ,
    "No models or transition matrix were produced."
  )
}

# Explicit confirmed/unconfirmed Active Domain -> Storage audit. State change is
# authoritative; D_EVT_RAW is process confirmation only.
storage_confirmation_qa <- risk %>%
  filter(STORAGE_TRANS == 1L) %>%
  count(
    confirmation = case_when(
      D_EVT_RAW == 1L ~ "process-confirmed storage transition",
      TRUE ~ "state-defined storage transition without process threshold confirmation"
    ),
    name = "n"
  )
write_csv(storage_confirmation_qa, file.path(out_dir, "00_storage_transition_confirmation_QA.csv"))

process_confirmation_integrity <- tibble(
  check = c(
    "REACTIVATE_CONFIRMED differs from reactivation plus E_EVT_RAW",
    "STORAGE_CONFIRMED differs from storage plus D_EVT_RAW",
    "STABILISE_CONFIRMED differs from stabilisation rule event",
    "STORAGE_REWORK_CONFIRMED differs from storage rework plus E_EVT_RAW",
    "FP_STORAGE_CONFIRMED differs from floodplain storage plus D_EVT_RAW"
  ),
  n = c(
    sum(risk$REACTIVATE_CONFIRMED != ifelse(risk$REACTIVATE_EVT == 1L & risk$E_EVT_RAW == 1L, 1L, 0L), na.rm = TRUE),
    sum(risk$STORAGE_CONFIRMED != ifelse(risk$STORAGE_EVT == 1L & risk$D_EVT_RAW == 1L, 1L, 0L), na.rm = TRUE),
    sum(risk$STABILISE_CONFIRMED != risk$STABILISE_EVT, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_CONFIRMED != ifelse(risk$STORAGE_REWORK_EVT == 1L & risk$E_EVT_RAW == 1L, 1L, 0L), na.rm = TRUE),
    sum(risk$FP_STORAGE_CONFIRMED != ifelse(risk$FP_STORAGE_EVT == 1L & risk$D_EVT_RAW == 1L, 1L, 0L), na.rm = TRUE)
  )
)
write_csv(process_confirmation_integrity, file.path(out_dir, "00_process_confirmation_field_QA.csv"))
if (any(process_confirmation_integrity$n > 0, na.rm = TRUE)) {
  stop("Process-confirmation fields are internally inconsistent. See 00_process_confirmation_field_QA.csv.")
}

base_event_counts <- risk %>%
  group_by(PLACE_ID) %>%
  summarise(n_base_events = sum(BASE_REACTIVATE_EVT == 1L, na.rm = TRUE), .groups = "drop")
if (any(base_event_counts$n_base_events > 1L)) {
  stop("Baseline first-event cohort contains more than one BASE_REACTIVATE_EVT for at least one PLACE_ID.")
}

# ---------------------------------------------------------------------------
# PRIMARY AMBIGUITY-BRIDGED EVENT/RISK QA AND ANALYSIS SELECTION
# ---------------------------------------------------------------------------
# Strict adjacent events remain unchanged in *_STRICT_AUDIT and *_TRANS fields.
# Principal KM/AG/Cox models use Stage 4 Step 3 primary fields, which preserve a
# recognised latent T1 state through boundary-mixed unresolved runs.

for (nm in strict_snapshot_fields) {
  risk[[paste0(nm, "_STRICT_AUDIT")]] <- int01(risk[[paste0(nm, "_STRICT_AUDIT")]])
}
primary_binary_fields <- c(
  "REACTIVATE_EVT_PRIMARY", "STORAGE_EVT_PRIMARY", "STABILISE_EVT_PRIMARY",
  "STORAGE_REWORK_EVT_PRIMARY", "FP_STORAGE_EVT_PRIMARY", "ANY_STATE_EVT_PRIMARY",
  "REACTIVATE_RISK_SET_PRIMARY", "STORAGE_RISK_SET_PRIMARY",
  "STABILISE_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET_PRIMARY",
  "FP_STORAGE_RISK_SET_PRIMARY", "ANY_STATE_RISK_SET_PRIMARY",
  "REACTIVATE_BRIDGED", "STORAGE_BRIDGED", "STORAGE_REWORK_BRIDGED",
  "FP_STORAGE_BRIDGED", "BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED",
  "BASE_REACTIVATE_EVT_PRIMARY", "M3_MODEL_ELIGIBLE_PRIMARY",
  "PRIMARY_EVENT_RISK_MISMATCH"
)
for (nm in primary_binary_fields) risk[[nm]] <- int01(risk[[nm]])

risk$M3_MODEL_ELIGIBLE_STRICT <- int01(risk$M3_MODEL_ELIGIBLE_STRICT)
risk$M3_MIXED_T1 <- int01(risk$M3_MIXED_T1)
risk$M3_MIXED_T2 <- int01(risk$M3_MIXED_T2)
risk$M3_EFFECTIVE_STATE_T1_PRIMARY <- canonical_state(risk$M3_EFFECTIVE_STATE_T1_PRIMARY)

expected_primary_reactivate <- as.integer(
  risk$REACTIVATE_EVT_STRICT_AUDIT == 1L | risk$REACTIVATE_BRIDGED == 1L
)
expected_primary_storage <- as.integer(
  risk$STORAGE_EVT_STRICT_AUDIT == 1L | risk$STORAGE_BRIDGED == 1L
)
expected_primary_stabilise <- risk$STABILISE_EVT_STRICT_AUDIT
expected_primary_storage_rework <- as.integer(
  risk$STORAGE_REWORK_EVT_STRICT_AUDIT == 1L | risk$STORAGE_REWORK_BRIDGED == 1L
)
expected_primary_fp_storage <- as.integer(
  risk$FP_STORAGE_EVT_STRICT_AUDIT == 1L | risk$FP_STORAGE_BRIDGED == 1L
)
expected_primary_any <- as.integer(
  expected_primary_reactivate == 1L |
  expected_primary_storage == 1L |
  expected_primary_stabilise == 1L |
  expected_primary_storage_rework == 1L |
  expected_primary_fp_storage == 1L
)

expected_primary_reactivate_risk <- as.integer(
  risk$M3_EFFECTIVE_STATE_T1_PRIMARY == "STABILISED_FLOODPLAIN"
)
expected_primary_storage_risk <- as.integer(
  risk$M3_EFFECTIVE_STATE_T1_PRIMARY == "ACTIVE_DOMAIN"
)
expected_primary_stabilise_risk <- as.integer(
  risk$M3_EFFECTIVE_STATE_T1_PRIMARY == "DEPOSITIONAL_STORAGE"
)
expected_primary_any_risk <- as.integer(
  risk$M3_EFFECTIVE_STATE_T1_PRIMARY %in%
    c("ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN")
)

# [FRAF archive / code note]
# Primary ambiguity bridging can represent legitimate events across mixed
# boundaries. Strict observed and high-support definitions remain separate.
primary_bridge_integrity <- tibble(
  check = c(
    "primary reactivation differs from strict OR bridged",
    "primary storage differs from strict OR bridged",
    "primary stabilisation differs from strict stabilisation",
    "primary storage rework differs from strict OR bridged",
    "primary floodplain storage differs from strict OR bridged",
    "primary any-event differs from named primary events",
    "primary reactivation risk differs from effective T1",
    "primary storage risk differs from effective T1",
    "primary stabilisation risk differs from effective T1",
    "primary storage-rework risk differs from effective T1",
    "primary floodplain-storage risk differs from effective T1",
    "primary any-state risk differs from effective T1",
    "primary reactivation event outside primary risk",
    "primary storage event outside primary risk",
    "primary stabilisation event outside primary risk",
    "primary storage-rework event outside primary risk",
    "primary floodplain-storage event outside primary risk",
    "primary baseline event outside primary baseline risk",
    "more than one primary baseline event for a PLACE",
    "Stage 4 primary event-definition mismatch flag",
    "Stage 4 primary risk-definition mismatch flag",
    "Stage 4 primary event-risk mismatch flag",
    "invalid bridged transition flag",
    "latent-state inconsistency flag",
    "strict-eligible row excluded from primary eligibility"
  ),
  n = c(
    sum(risk$REACTIVATE_EVT_PRIMARY != expected_primary_reactivate, na.rm = TRUE),
    sum(risk$STORAGE_EVT_PRIMARY != expected_primary_storage, na.rm = TRUE),
    sum(risk$STABILISE_EVT_PRIMARY != expected_primary_stabilise, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_PRIMARY != expected_primary_storage_rework, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT_PRIMARY != expected_primary_fp_storage, na.rm = TRUE),
    sum(risk$ANY_STATE_EVT_PRIMARY != expected_primary_any, na.rm = TRUE),
    sum(risk$REACTIVATE_RISK_SET_PRIMARY != expected_primary_reactivate_risk, na.rm = TRUE),
    sum(risk$STORAGE_RISK_SET_PRIMARY != expected_primary_storage_risk, na.rm = TRUE),
    sum(risk$STABILISE_RISK_SET_PRIMARY != expected_primary_stabilise_risk, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_RISK_SET_PRIMARY != expected_primary_stabilise_risk, na.rm = TRUE),
    sum(risk$FP_STORAGE_RISK_SET_PRIMARY != expected_primary_reactivate_risk, na.rm = TRUE),
    sum(risk$ANY_STATE_RISK_SET_PRIMARY != expected_primary_any_risk, na.rm = TRUE),
    sum(risk$REACTIVATE_EVT_PRIMARY == 1L & risk$REACTIVATE_RISK_SET_PRIMARY != 1L, na.rm = TRUE),
    sum(risk$STORAGE_EVT_PRIMARY == 1L & risk$STORAGE_RISK_SET_PRIMARY != 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT_PRIMARY == 1L & risk$STABILISE_RISK_SET_PRIMARY != 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_PRIMARY == 1L & risk$STORAGE_REWORK_RISK_SET_PRIMARY != 1L, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT_PRIMARY == 1L & risk$FP_STORAGE_RISK_SET_PRIMARY != 1L, na.rm = TRUE),
    sum(risk$BASE_REACTIVATE_EVT_PRIMARY == 1L &
          risk$BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED != 1L, na.rm = TRUE),
    sum(
      (risk %>% group_by(PLACE_ID) %>%
         summarise(n_evt = sum(BASE_REACTIVATE_EVT_PRIMARY == 1L, na.rm = TRUE), .groups = "drop"))$n_evt > 1L,
      na.rm = TRUE
    ),
    sum(num_or_na(risk$PRIMARY_EVENT_DEFINITION_MISMATCH) != 0, na.rm = TRUE),
    sum(num_or_na(risk$PRIMARY_RISK_DEFINITION_MISMATCH) != 0, na.rm = TRUE),
    sum(risk$PRIMARY_EVENT_RISK_MISMATCH != 0L, na.rm = TRUE),
    sum(int01(risk$QA_BRIDGED_TRANS_INVALID) != 0L, na.rm = TRUE),
    sum(int01(risk$QA_LATENT_STATE_INCONSISTENT) != 0L, na.rm = TRUE),
    sum(risk$M3_MODEL_ELIGIBLE_STRICT == 1L &
          risk$M3_MODEL_ELIGIBLE_PRIMARY != 1L, na.rm = TRUE)
  ),
  fatal = TRUE
)
write_csv(primary_bridge_integrity, file.path(out_dir, "00_primary_ambiguity_bridge_integrity_QA.csv"))

primary_event_definition_summary <- tibble(
  transition = c(
    "Stabilised Floodplain to Active Domain",
    "Active Domain to Depositional Storage",
    "Depositional Storage to Stabilised Floodplain",
    "Depositional Storage to Active Domain",
    "Stabilised Floodplain to Depositional Storage"
  ),
  strict_events = c(
    sum(risk$REACTIVATE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    sum(risk$STORAGE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE)
  ),
  bridged_events = c(
    sum(risk$REACTIVATE_BRIDGED == 1L, na.rm = TRUE),
    sum(risk$STORAGE_BRIDGED == 1L, na.rm = TRUE),
    0L,
    sum(risk$STORAGE_REWORK_BRIDGED == 1L, na.rm = TRUE),
    sum(risk$FP_STORAGE_BRIDGED == 1L, na.rm = TRUE)
  ),
  primary_events = c(
    sum(risk$REACTIVATE_EVT_PRIMARY == 1L, na.rm = TRUE),
    sum(risk$STORAGE_EVT_PRIMARY == 1L, na.rm = TRUE),
    sum(risk$STABILISE_EVT_PRIMARY == 1L, na.rm = TRUE),
    sum(risk$STORAGE_REWORK_EVT_PRIMARY == 1L, na.rm = TRUE),
    sum(risk$FP_STORAGE_EVT_PRIMARY == 1L, na.rm = TRUE)
  )
)
write_csv(
  primary_event_definition_summary,
  file.path(out_dir, "00_primary_vs_strict_event_counts.csv")
)

# Interval-level primary versus strict event counts. This shows whether
# ambiguity-bridged increments are diffuse through the record or concentrated
# in one/few intervals.
primary_vs_strict_interval <- risk %>%
  group_by(y1, y2, tstart_yr, tstop_yr) %>%
  summarise(
    strict_reactivation = sum(REACTIVATE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    primary_reactivation = sum(REACTIVATE_EVT_PRIMARY == 1L, na.rm = TRUE),
    bridged_reactivation_reported = sum(REACTIVATE_BRIDGED == 1L, na.rm = TRUE),
    strict_storage = sum(STORAGE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    primary_storage = sum(STORAGE_EVT_PRIMARY == 1L, na.rm = TRUE),
    bridged_storage_reported = sum(STORAGE_BRIDGED == 1L, na.rm = TRUE),
    strict_stabilisation = sum(STABILISE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    primary_stabilisation = sum(STABILISE_EVT_PRIMARY == 1L, na.rm = TRUE),
    strict_storage_rework = sum(STORAGE_REWORK_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    primary_storage_rework = sum(STORAGE_REWORK_EVT_PRIMARY == 1L, na.rm = TRUE),
    bridged_storage_rework_reported = sum(STORAGE_REWORK_BRIDGED == 1L, na.rm = TRUE),
    strict_fp_storage = sum(FP_STORAGE_EVT_STRICT_AUDIT == 1L, na.rm = TRUE),
    primary_fp_storage = sum(FP_STORAGE_EVT_PRIMARY == 1L, na.rm = TRUE),
    bridged_fp_storage_reported = sum(FP_STORAGE_BRIDGED == 1L, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    interval = paste0(as.character(y1), " -> ", as.character(y2)),
    extra_reactivation = primary_reactivation - strict_reactivation,
    extra_storage = primary_storage - strict_storage,
    extra_stabilisation = primary_stabilisation - strict_stabilisation,
    extra_storage_rework = primary_storage_rework - strict_storage_rework,
    extra_fp_storage = primary_fp_storage - strict_fp_storage,
    react_bridge_count_check = extra_reactivation - bridged_reactivation_reported
  ) %>%
  arrange(tstart_yr, tstop_yr)
write_csv(primary_vs_strict_interval, file.path(out_dir, "00_primary_vs_strict_event_counts_by_interval.csv"))

reactivation_interval_concentration <- primary_vs_strict_interval %>%
  transmute(
    y1, y2, tstart_yr, tstop_yr, interval,
    strict_reactivation, primary_reactivation,
    extra_reactivation, bridged_reactivation_reported, react_bridge_count_check,
    extra_share_pct = ifelse(
      sum(pmax(extra_reactivation, 0), na.rm = TRUE) > 0,
      100 * pmax(extra_reactivation, 0) / sum(pmax(extra_reactivation, 0), na.rm = TRUE),
      NA_real_
    )
  ) %>%
  arrange(desc(extra_reactivation), tstart_yr)
write_csv(reactivation_interval_concentration, file.path(out_dir, "00_primary_vs_strict_reactivation_interval_concentration.csv"))

reactivation_plot_data <- primary_vs_strict_interval %>%
  select(tstart_yr, tstop_yr, interval, strict_reactivation, primary_reactivation) %>%
  pivot_longer(
    cols = c(strict_reactivation, primary_reactivation),
    names_to = "definition", values_to = "events"
  ) %>%
  mutate(
    definition = recode(
      definition,
      strict_reactivation = "Strict observed-state",
      primary_reactivation = "Primary ambiguity-bridged"
    ),
    interval = factor(interval, levels = primary_vs_strict_interval$interval)
  )

p_reactivation_interval <- ggplot(reactivation_plot_data, aes(x = interval, y = events, group = definition, colour = definition)) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 1.7) +
  labs(
    title = paste0(reach_label, ": primary versus strict reactivation events by interval"),
    x = "Interval", y = "Reactivation event count", colour = "Event definition"
  ) +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 60, hjust = 1))
safe_plot_save(p_reactivation_interval, "00_primary_vs_strict_reactivation_by_interval.png", width = 11, height = 6)

if (any(primary_bridge_integrity$n > 0, na.rm = TRUE)) {
  stop(
    "Primary ambiguity-bridge integrity failure. See ",
    "00_primary_ambiguity_bridge_integrity_QA.csv before modelling."
  )
}

# Map the primary event/risk family onto the established working names. Observed
# endpoint transitions remain in *_TRANS and strict fields remain in
# *_STRICT_AUDIT, so the state-only sensitivity outputs are still genuinely strict.
risk$FP_REACTIVATE_EVT <- int01(risk$FP_REACTIVATE_EVT_PRIMARY)
risk$FP_REACTIVATE_RISK_SET <- int01(risk$FP_REACTIVATE_RISK_SET_PRIMARY)
risk$REACTIVATE_EVT <- risk$REACTIVATE_EVT_PRIMARY
risk$STORAGE_EVT <- risk$STORAGE_EVT_PRIMARY
risk$STABILISE_EVT <- risk$STABILISE_EVT_PRIMARY
risk$STORAGE_REWORK_EVT <- risk$STORAGE_REWORK_EVT_PRIMARY
risk$FP_STORAGE_EVT <- risk$FP_STORAGE_EVT_PRIMARY
risk$REACTIVATE_RISK_SET <- risk$REACTIVATE_RISK_SET_PRIMARY
risk$STORAGE_RISK_SET <- risk$STORAGE_RISK_SET_PRIMARY
risk$STABILISE_RISK_SET <- risk$STABILISE_RISK_SET_PRIMARY
risk$STORAGE_REWORK_RISK_SET <- risk$STORAGE_REWORK_RISK_SET_PRIMARY
# DS->AD and DS->SF share the same interval-start Depositional Storage population.
# Some legacy/partial Risk Tables contain an empty dedicated reworking risk field;
# preserve v17.9.11 semantics by falling back to the stabilisation DS risk set.
if (sum(risk$STORAGE_REWORK_RISK_SET == 1L, na.rm = TRUE) == 0L &&
    sum(risk$STABILISE_RISK_SET == 1L, na.rm = TRUE) > 0L) {
  warning("[DS->AD historic QA] Dedicated storage-reworking risk set is empty; using STABILISE_RISK_SET as the common Depositional Storage origin population.")
  risk$STORAGE_REWORK_RISK_SET <- risk$STABILISE_RISK_SET
}
if (sum(risk$STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1L, na.rm = TRUE) == 0L &&
    sum(risk$STABILISE_RISK_SET_STRICT_AUDIT == 1L, na.rm = TRUE) > 0L) {
  warning("[DS->AD historic QA] Strict storage-reworking risk set is empty; using strict stabilisation DS risk set.")
  risk$STORAGE_REWORK_RISK_SET_STRICT_AUDIT <- risk$STABILISE_RISK_SET_STRICT_AUDIT
}
.ds_rw_outside <- sum(risk$STORAGE_REWORK_EVT == 1L & risk$STORAGE_REWORK_RISK_SET != 1L, na.rm = TRUE)
if (.ds_rw_outside > 0L) {
  stop("[DS->AD historic QA] ", .ds_rw_outside, " storage-reworking events fall outside the final DS risk set. Inspect Stage 4 Step 3 before modelling.")
}
rm(.ds_rw_outside)
risk$FP_STORAGE_RISK_SET <- risk$FP_STORAGE_RISK_SET_PRIMARY
risk$ANY_STATE_RISK_SET <- risk$ANY_STATE_RISK_SET_PRIMARY
risk$BASE_REACTIVATE_RISK_SET_DERIVED <- risk$BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED
risk$BASE_REACTIVATE_RISK_SET <- risk$BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED
risk$BASE_REACTIVATE_EVT <- risk$BASE_REACTIVATE_EVT_PRIMARY
risk$M3_MODEL_ELIGIBLE_ANALYSIS <- risk$M3_MODEL_ELIGIBLE_PRIMARY
risk$M3_MODEL_EXCLUSION_REASON_ANALYSIS <- as.character(risk$M3_MODEL_EXCLUSION_REASON_PRIMARY)
risk$EVENT_DEFINITION_USED <- "PRIMARY_AMBIGUITY_BRIDGED"

if ("REACTIVATE_NEXT_PRIMARY" %in% names(risk)) risk$REACTIVATE_NEXT <- int01(risk$REACTIVATE_NEXT_PRIMARY)
if ("STORAGE_NEXT_PRIMARY" %in% names(risk)) risk$STORAGE_NEXT <- int01(risk$STORAGE_NEXT_PRIMARY)
if ("STABILISE_NEXT_PRIMARY" %in% names(risk)) risk$STABILISE_NEXT <- int01(risk$STABILISE_NEXT_PRIMARY)
if ("STORAGE_REWORK_NEXT_PRIMARY" %in% names(risk)) risk$STORAGE_REWORK_NEXT <- int01(risk$STORAGE_REWORK_NEXT_PRIMARY)
if ("FP_STORAGE_NEXT_PRIMARY" %in% names(risk)) risk$FP_STORAGE_NEXT <- int01(risk$FP_STORAGE_NEXT_PRIMARY)

risk$ANY_CONFIRMED_EVT <- as.integer(
  risk$REACTIVATE_EVT == 1L |
  risk$STORAGE_EVT == 1L |
  risk$STABILISE_EVT == 1L |
  risk$STORAGE_REWORK_EVT == 1L |
  risk$FP_STORAGE_EVT == 1L
)
risk$E_evt <- risk$REACTIVATE_EVT
risk$D_evt <- risk$STORAGE_EVT
risk$ANY_EVT <- risk$ANY_CONFIRMED_EVT
risk$E_RISK_SET <- risk$REACTIVATE_RISK_SET
risk$D_RISK_SET <- risk$STORAGE_RISK_SET
risk$RISK_SET <- risk$ANY_STATE_RISK_SET

risk$EVENT_ONTOLOGY <- factor(
  display_event(risk$REACTIVATE_EVT, risk$STORAGE_EVT, risk$STABILISE_EVT),
  levels = c("Reached by Active Domain", "Depositional storage",
             "Storage became stable floodplain", "Active Domain reach + storage", "Persistence")
)
risk$EVENT_STATE <- factor(
  display_state_event(
    risk$REACTIVATE_EVT, risk$STORAGE_EVT, risk$STABILISE_EVT,
    risk$STORAGE_REWORK_EVT, risk$FP_STORAGE_EVT,
    risk$REACTIVATE_TRANS, risk$STORAGE_TRANS, risk$ANY_STATE_EVT,
    risk$STATE1_ONTOLOGY, risk$STATE2_ONTOLOGY
  ),
  levels = c(
    "Reached by Active Domain", "Entered Depositional Storage",
    "Storage became Stabilised Floodplain", "Unconfirmed reactivation transition",
    "Unconfirmed storage transition", "Depositional Storage -> Active Domain",
    "Active Domain -> Stabilised Floodplain",
    "Stabilised Floodplain -> Depositional Storage",
    "Unclassified state transition", "Persistence"
  )
)
risk$event_class <- as.character(risk$EVENT_STATE)

if (all(c("REACTIVATE_NEXT", "STORAGE_NEXT", "STABILISE_NEXT") %in% names(risk))) {
  risk$NEXT_EVENT_ONTOLOGY <- factor(
    display_event(risk$REACTIVATE_NEXT, risk$STORAGE_NEXT, risk$STABILISE_NEXT),
    levels = c("Reached by Active Domain", "Depositional storage",
               "Storage became stable floodplain", "Active Domain reach + storage", "Persistence")
  )
}

message("[EVENT DEFINITION] PRIMARY ambiguity-bridged events and risk sets selected.")

# ---------------------------------------------------------------------------
# INTERVAL-START SPATIAL TEMPORAL PROVENANCE QA
# ---------------------------------------------------------------------------
# Stage 4 Step 3 v6.6 defines predictors for (y1, y2] from geometry at y1.
# The local Mamoré lookup carries GEOM_YMD_PREV explicitly; this is checked
# row-by-row. *_CURR Active Domain/water/centreline fields are documented as
# interval-start values by the required v6.5 interface and are never interpreted
# here as y2 geometry.
risk$.Y1_YMD_CODE <- ymd_code(risk$y1)
risk$.GEOM_YMD_PREV_CODE <- if ("GEOM_YMD_PREV" %in% names(risk)) ymd_code(risk$GEOM_YMD_PREV) else NA_integer_

local_geom_value_fields <- intersect(
  c("DIST_CHANNEL_PREV", "DIST_BANK_PREV", "DIST_CL_PREV", "CURV_SIGNED_PREV",
    "CURV_ABS_PREV", "REL_CHANNEL_POS_PREV", "LOCAL_WIDTH_PREV"),
  names(risk)
)
has_local_geom_value <- if (length(local_geom_value_fields) > 0L) {
  rowSums(as.data.frame(lapply(risk[local_geom_value_fields], function(x) is.finite(num_or_na(x))))) > 0L
} else rep(FALSE, nrow(risk))
geom_support <- if ("GEOM_SUPPORT_PREV" %in% names(risk)) int01(risk$GEOM_SUPPORT_PREV) else as.integer(has_local_geom_value)
local_geom_expected <- geom_support == 1L | has_local_geom_value
local_geom_missing_date <- local_geom_expected & is.na(risk$.GEOM_YMD_PREV_CODE)
local_geom_unparsed_y1 <- local_geom_expected & is.na(risk$.Y1_YMD_CODE)
local_geom_date_mismatch <- local_geom_expected & !is.na(risk$.Y1_YMD_CODE) &
  !is.na(risk$.GEOM_YMD_PREV_CODE) & risk$.GEOM_YMD_PREV_CODE != risk$.Y1_YMD_CODE
local_geom_future_date <- local_geom_expected & !is.na(risk$.Y1_YMD_CODE) &
  !is.na(risk$.GEOM_YMD_PREV_CODE) & risk$.GEOM_YMD_PREV_CODE > risk$.Y1_YMD_CODE
any_primary_event_row <- risk$ANY_CONFIRMED_EVT == 1L
any_primary_risk_row <- risk$ANY_STATE_RISK_SET == 1L

stage4_version_text <- if ("STATE_MODEL_VERSION" %in% names(risk)) {
  paste(unique(na.omit(as.character(risk$STATE_MODEL_VERSION))), collapse = "; ")
} else if ("ONTOLOGY_VERSION" %in% names(risk)) {
  paste(unique(na.omit(as.character(risk$ONTOLOGY_VERSION))), collapse = "; ")
} else {
  "required Stage 4 Step 3 v6.6 field interface"
}

spatial_temporal_alignment_qa <- tibble::tibble(
  check = c(
    "rows with local geometry expected",
    "local-geometry rows missing GEOM_YMD_PREV",
    "local-geometry rows with unparseable y1",
    "local-geometry rows where GEOM_YMD_PREV differs from y1",
    "local-geometry rows where GEOM_YMD_PREV is later than y1",
    "primary event rows missing required local geometry date",
    "primary at-risk non-event rows missing required local geometry date",
    "duplicate PLACE_ID + y1 + y2 rows"
  ),
  n = c(
    sum(local_geom_expected, na.rm = TRUE),
    sum(local_geom_missing_date, na.rm = TRUE),
    sum(local_geom_unparsed_y1, na.rm = TRUE),
    sum(local_geom_date_mismatch, na.rm = TRUE),
    sum(local_geom_future_date, na.rm = TRUE),
    sum(any_primary_event_row & local_geom_expected & local_geom_missing_date, na.rm = TRUE),
    sum(any_primary_risk_row & !any_primary_event_row & local_geom_expected & local_geom_missing_date, na.rm = TRUE),
    nrow(risk %>% count(PLACE_ID, y1, y2, name = "n") %>% filter(n > 1L))
  ),
  fatal = c(FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
  time_basis = "Predictors for (y1, y2] use geometry at y1",
  source_interface = stage4_version_text
)
write_csv(spatial_temporal_alignment_qa, file.path(out_dir, "00_spatial_temporal_alignment_QA.csv"))

spatial_temporal_alignment_sample <- risk %>%
  transmute(
    PLACE_ID, BLOCK_ID, y1, y2, tstart_yr, tstop_yr,
    Y1_YMD_CODE = .Y1_YMD_CODE,
    GEOM_YMD_PREV = if ("GEOM_YMD_PREV" %in% names(risk)) as.character(GEOM_YMD_PREV) else NA_character_,
    GEOM_YMD_PREV_CODE = .GEOM_YMD_PREV_CODE,
    GEOM_SUPPORT_PREV = geom_support,
    DIST_ACTIVE_CURR = if ("DIST_ACTIVE_CURR" %in% names(risk)) num_or_na(DIST_ACTIVE_CURR) else NA_real_,
    DIST_WATER_CURR = if ("DIST_WATER_CURR" %in% names(risk)) num_or_na(DIST_WATER_CURR) else NA_real_,
    DIST_CL_CURR = if ("DIST_CL_CURR" %in% names(risk)) num_or_na(DIST_CL_CURR) else NA_real_,
    DIST_CL_PREV = if ("DIST_CL_PREV" %in% names(risk)) num_or_na(DIST_CL_PREV) else NA_real_,
    DIST_CHANNEL_PREV = if ("DIST_CHANNEL_PREV" %in% names(risk)) num_or_na(DIST_CHANNEL_PREV) else NA_real_,
    REACTIVATE_EVT_PRIMARY, STORAGE_EVT_PRIMARY, STABILISE_EVT_PRIMARY,
    ANY_STATE_EVT_PRIMARY,
    TEMPORAL_QA_FLAG = case_when(
      local_geom_future_date ~ "FUTURE_GEOMETRY",
      local_geom_date_mismatch ~ "GEOMETRY_DATE_NOT_Y1",
      local_geom_missing_date ~ "MISSING_GEOMETRY_DATE",
      local_geom_unparsed_y1 ~ "UNPARSEABLE_Y1",
      TRUE ~ "PASS_OR_NOT_APPLICABLE"
    )
  ) %>%
  arrange(desc(TEMPORAL_QA_FLAG != "PASS_OR_NOT_APPLICABLE"), PLACE_ID, tstart_yr) %>%
  slice_head(n = 200L)
write_csv(spatial_temporal_alignment_sample, file.path(out_dir, "00_spatial_temporal_alignment_sample.csv"))

spatial_time_dictionary <- tibble::tribble(
  ~field_family, ~actual_time_basis, ~interpretation,
  "DIST_ACTIVE_CURR / DIST_WATER_CURR / DIST_CL_CURR", "interval start y1", "Direct Stage 4 Step 3 geometry selected at y1",
  "GEOM_YMD_PREV and local *_PREV fields", "interval start y1", "Exact PLACE x timestep-geometry lookup at y1; PREV describes the lagged lookup source",
  "DIST_CL_REF", "fixed reference", "Time-invariant reference or union-centreline distance",
  "*_LANDMARK_*", "record-start fixed", "First non-missing exposure for each PLACE_ID",
  "*_Y0", "previous observation", "Exposure at the immediately preceding contiguous interval start",
  "*_T2_DIAGNOSTIC", "interval end y2", "Lead value from the next contiguous interval; diagnostic outcome-time negative control only",
  "*_APPROACH_M_PER_YR", "change before y1", "Positive values indicate movement towards the PLACE before the analysed interval"
)
write_csv(spatial_time_dictionary, file.path(out_dir, "00_spatial_temporal_field_dictionary.csv"))
# [FRAF archive / code note]
# Time-related fields are validated as elapsed observation exposure;
# irregularly spaced remote-sensing observations are not equal-duration trials.
risk$SPATIAL_TIME_BASIS <- "INTERVAL_START_Y1"
risk$SPATIAL_OUTCOME_INTERVAL <- "(y1, y2]"

if (isTRUE(StrictTemporalAlignment) && any(
  spatial_temporal_alignment_qa$fatal & spatial_temporal_alignment_qa$n > 0L,
  na.rm = TRUE
)) {
  stop(
    "Interval-start spatial temporal alignment failure. See ",
    "00_spatial_temporal_alignment_QA.csv and 00_spatial_temporal_alignment_sample.csv."
  )
}

# [FRAF archive / code note]
# A temporally aligned external covariate must be known at or before y1;
# this precludes selecting a subsequent channel outline as a fallback.
# Create previous-observation (y0) distance fields only for contiguous records.
# To control memory on million-row Risk Tables, only the transition-relevant
# local Mamoré pair or braided-reach interval-start fields are expanded. These
# sensitivity covariates never replace the principal y1 predictors.
local_temporal_geometry_available <- any(local_geom_expected, na.rm = TRUE) &&
  any(c("DIST_CHANNEL_PREV", "DIST_BANK_PREV") %in% names(risk))
spatial_y0_candidates <- if (!isTRUE(RunTemporalSensitivity)) {
  character(0)
} else if (local_temporal_geometry_available) {
  intersect(c("DIST_CHANNEL_PREV", "DIST_BANK_PREV"), names(risk))
} else {
  intersect(c("DIST_ACTIVE_CURR", "DIST_WATER_CURR", "DIST_CL_CURR"), names(risk))
}
temporal_spatial_lookup <- risk %>%
  select(
    PLACE_ID, BLOCK_ID, tstart_yr, tstop_yr,
    REACTIVATE_RISK_SET, REACTIVATE_EVT,
    all_of(spatial_y0_candidates)
  ) %>%
  arrange(PLACE_ID, tstart_yr, tstop_yr) %>%
  group_by(PLACE_ID) %>%
  mutate(
    .Y0_TSTART = lag(tstart_yr),
    .Y0_TSTOP = lag(tstop_yr),
    .Y0_CONTIGUOUS = as.integer(!is.na(.Y0_TSTOP) & abs(.Y0_TSTOP - tstart_yr) < 1e-7),
    .T2_TSTART = lead(tstart_yr),
    .T2_CONTIGUOUS = as.integer(!is.na(.T2_TSTART) & abs(tstop_yr - .T2_TSTART) < 1e-7)
  ) %>%
  mutate(
    across(
      all_of(spatial_y0_candidates),
      ~ ifelse(.Y0_CONTIGUOUS == 1L, lag(num_or_na(.x)), NA_real_),
      .names = "{.col}_Y0"
    ),
    across(
      all_of(spatial_y0_candidates),
      ~ ifelse(.T2_CONTIGUOUS == 1L, lead(num_or_na(.x)), NA_real_),
      .names = "{.col}_T2_DIAGNOSTIC"
    )
  ) %>%
  ungroup()

for (nm in spatial_y0_candidates) {
  y0_nm <- paste0(nm, "_Y0")
  rate_nm <- paste0(nm, "_APPROACH_M_PER_YR")
  delta_t <- temporal_spatial_lookup$tstart_yr - temporal_spatial_lookup$.Y0_TSTART
  temporal_spatial_lookup[[rate_nm]] <- ifelse(
    temporal_spatial_lookup$.Y0_CONTIGUOUS == 1L & is.finite(delta_t) & delta_t > 0,
    (num_or_na(temporal_spatial_lookup[[y0_nm]]) - num_or_na(temporal_spatial_lookup[[nm]])) / delta_t,
    NA_real_
  )
}

temporal_generated_fields <- grep(
  "(_Y0$|_T2_DIAGNOSTIC$|_APPROACH_M_PER_YR$|^\\.Y0_|^\\.T2_)",
  names(temporal_spatial_lookup), value = TRUE
)
temporal_spatial_model_lookup <- temporal_spatial_lookup %>%
  select(PLACE_ID, tstart_yr, tstop_yr, all_of(temporal_generated_fields))

previous_observation_spatial_qa <- if (length(spatial_y0_candidates) > 0L) {
  bind_rows(lapply(spatial_y0_candidates, function(nm) {
    y0_nm <- paste0(nm, "_Y0")
    rate_nm <- paste0(nm, "_APPROACH_M_PER_YR")
    tibble::tibble(
      field = nm,
      total_rows = nrow(temporal_spatial_lookup),
      contiguous_previous_rows = sum(temporal_spatial_lookup$.Y0_CONTIGUOUS == 1L, na.rm = TRUE),
      complete_y1_y0_pairs = sum(is.finite(num_or_na(temporal_spatial_lookup[[nm]])) & is.finite(num_or_na(temporal_spatial_lookup[[y0_nm]]))),
      complete_approach_rates = sum(is.finite(num_or_na(temporal_spatial_lookup[[rate_nm]]))),
      complete_t2_negative_controls = sum(is.finite(num_or_na(temporal_spatial_lookup[[paste0(nm, "_T2_DIAGNOSTIC")]]))),
      median_approach_m_per_yr = safe_quantile(num_or_na(temporal_spatial_lookup[[rate_nm]]), 0.5)
    )
  }))
} else {
  tibble::tibble(
    field = NA_character_, total_rows = nrow(temporal_spatial_lookup), contiguous_previous_rows = 0L,
    complete_y1_y0_pairs = 0L, complete_approach_rates = 0L,
    complete_t2_negative_controls = 0L, median_approach_m_per_yr = NA_real_
  )
}
write_csv(previous_observation_spatial_qa, file.path(out_dir, "00_previous_observation_spatial_QA.csv"))

# Pairwise comparisons expose aliases, near-duplicates and substantive differences
# between reference, dated and local spatial measurements.
spatial_pair_specs <- list(
  c("DIST_CL_CURR", "DIST_CL_PREV"),
  c("DIST_CL_CURR", "DIST_CL_REF"),
  c("DIST_ACTIVE_CURR", "DIST_CL_CURR"),
  c("DIST_CHANNEL_PREV", "DIST_CL_PREV")
)
spatial_group_specs <- list(
  all_primary_risk = risk$ANY_STATE_RISK_SET == 1L,
  primary_event = risk$ANY_STATE_RISK_SET == 1L & risk$ANY_CONFIRMED_EVT == 1L,
  primary_non_event = risk$ANY_STATE_RISK_SET == 1L & risk$ANY_CONFIRMED_EVT == 0L
)
spatial_field_comparison <- bind_rows(lapply(spatial_pair_specs, function(pair) {
  xnm <- pair[1]; ynm <- pair[2]
  if (!all(pair %in% names(risk))) return(NULL)
  bind_rows(lapply(names(spatial_group_specs), function(g) {
    keep <- spatial_group_specs[[g]]
    x <- num_or_na(risk[[xnm]][keep]); y <- num_or_na(risk[[ynm]][keep])
    ok <- is.finite(x) & is.finite(y)
    d <- abs(x[ok] - y[ok])
    tibble::tibble(
      field_x = xnm, field_y = ynm, subset = g,
      complete_pairs = sum(ok),
      pearson_r = safe_cor(x, y, "pearson"),
      spearman_rho = safe_cor(x, y, "spearman"),
      median_absolute_difference_m = safe_quantile(d, 0.5),
      p95_absolute_difference_m = safe_quantile(d, 0.95),
      exactly_equal_percent = if (sum(ok) > 0L) 100 * mean(abs(x[ok] - y[ok]) < 1e-9) else NA_real_
    )
  }))
}))
if (nrow(spatial_field_comparison) == 0L) {
  spatial_field_comparison <- tibble::tibble(
    field_x = NA_character_, field_y = NA_character_, subset = "no comparable field pairs",
    complete_pairs = 0L, pearson_r = NA_real_, spearman_rho = NA_real_,
    median_absolute_difference_m = NA_real_, p95_absolute_difference_m = NA_real_,
    exactly_equal_percent = NA_real_
  )
}
write_csv(spatial_field_comparison, file.path(out_dir, "00_spatial_field_comparison.csv"))

# Diagnostic-only T2 negative controls are derived from the next contiguous
# interval-start record, which represents the current interval end y2. They are
# never candidates for principal models.
t2_negative_control_candidates <- tibble::tribble(
  ~t1_field, ~t2_field,
  "DIST_ACTIVE_CURR", "DIST_ACTIVE_CURR_T2_DIAGNOSTIC",
  "DIST_WATER_CURR", "DIST_WATER_CURR_T2_DIAGNOSTIC",
  "DIST_CL_CURR", "DIST_CL_CURR_T2_DIAGNOSTIC",
  "DIST_CL_PREV", "DIST_CL_PREV_T2_DIAGNOSTIC",
  "DIST_CHANNEL_PREV", "DIST_CHANNEL_PREV_T2_DIAGNOSTIC",
  "DIST_BANK_PREV", "DIST_BANK_PREV_T2_DIAGNOSTIC"
) %>%
  mutate(available = t1_field %in% names(temporal_spatial_lookup) & t2_field %in% names(temporal_spatial_lookup)) %>%
  rowwise() %>%
  mutate(
    complete_pairs = if (available) {
      sum(is.finite(num_or_na(temporal_spatial_lookup[[t1_field]])) & is.finite(num_or_na(temporal_spatial_lookup[[t2_field]])))
    } else 0L,
    reactivation_events_with_pair = if (available) {
      sum(
        temporal_spatial_lookup$REACTIVATE_RISK_SET == 1L & temporal_spatial_lookup$REACTIVATE_EVT == 1L &
          is.finite(num_or_na(temporal_spatial_lookup[[t1_field]])) & is.finite(num_or_na(temporal_spatial_lookup[[t2_field]])),
        na.rm = TRUE
      )
    } else 0L,
    diagnostic_transition = "reactivation"
  ) %>%
  ungroup()
write_csv(t2_negative_control_candidates, file.path(out_dir, "00_t2_negative_control_capability_QA.csv"))

# v17.10.8: the expanded temporal lookup has served all alignment/capability QA.
# Later temporal models use cox_data-derived fields rather than this lookup.
rm(temporal_spatial_lookup)
invisible(gc(full = TRUE))
message("[Memory] Released expanded temporal-spatial lookup after QA.")

# Reproducible row sample for QGIS spatial verification. Ten rows are retained
# per event class and record third where available.
record_min_t <- min(risk$tstart_yr, na.rm = TRUE)
record_max_t <- max(risk$tstop_yr, na.rm = TRUE)
record_span_t <- record_max_t - record_min_t
cut_early_t <- record_min_t + record_span_t / 3
cut_middle_t <- record_min_t + 2 * record_span_t / 3
spatial_spotcheck_sample <- risk %>%
  mutate(
    TEMPORAL_PERIOD = case_when(
      tstart_yr < cut_early_t ~ "Early",
      tstart_yr < cut_middle_t ~ "Middle",
      TRUE ~ "Late"
    ),
    SPOTCHECK_CLASS = case_when(
      REACTIVATE_EVT == 1L ~ "reactivation_event",
      STORAGE_EVT == 1L ~ "storage_event",
      STABILISE_EVT == 1L ~ "stabilisation_event",
      ANY_STATE_RISK_SET == 1L & ANY_CONFIRMED_EVT == 0L ~ "primary_non_event",
      TRUE ~ "not_selected"
    )
  ) %>%
  filter(SPOTCHECK_CLASS != "not_selected") %>%
  arrange(SPOTCHECK_CLASS, TEMPORAL_PERIOD, PLACE_ID, tstart_yr) %>%
  group_by(SPOTCHECK_CLASS, TEMPORAL_PERIOD) %>%
  slice_head(n = 10L) %>%
  ungroup() %>%
  select(
    PLACE_ID, BLOCK_ID, y1, y2, tstart_yr, tstop_yr,
    SPOTCHECK_CLASS, TEMPORAL_PERIOD,
    STATE1_ONTOLOGY, STATE2_ONTOLOGY,
    REACTIVATE_EVT, STORAGE_EVT, STABILISE_EVT,
    ANY_CONFIRMED_EVT, ANY_STATE_RISK_SET,
    any_of(c(
      "GEOM_YMD_PREV", "GEOM_SUPPORT_PREV",
      "DIST_ACTIVE_CURR", "DIST_WATER_CURR", "DIST_CL_REF", "DIST_CL_CURR",
      "DIST_CL_PREV", "DIST_CHANNEL_PREV", "DIST_BANK_PREV",
      "OUTER_BANK_PREV", "INNER_BANK_PREV", "CURV_SIGNED_PREV",
      "REL_CHANNEL_POS_PREV", "MAM_OUTER_REACT_EXPOSED_PREV"
    ))
  )
write_csv(spatial_spotcheck_sample, file.path(out_dir, "00_spatial_QGIS_spotcheck_sample.csv"))

# Principal model eligibility comes directly from Stage 4 Step 3. Boundary-mixed
# endpoints are retained only where the latent/effective state rules make them
# eligible; provenance-limited unresolved endpoints remain excluded.
risk_model <- risk %>% filter(M3_MODEL_ELIGIBLE_PRIMARY == 1L)

model_eligibility_qa <- risk %>%
  mutate(principal_included = as.integer(M3_MODEL_ELIGIBLE_PRIMARY == 1L)) %>%
  count(
    principal_included,
    M3_MODEL_EXCLUSION_REASON_PRIMARY,
    M3_EFFECTIVE_STATE_T1_PRIMARY,
    name = "n"
  )
write_csv(model_eligibility_qa, file.path(out_dir, "00_principal_model_eligibility_QA.csv"))

# Primary recurrent risk sets.
risk_valid <- risk_model %>% filter(ANY_STATE_RISK_SET == 1L)
risk_erosion <- risk_model %>% filter(REACTIVATE_RISK_SET == 1L)
# v17.10.12: broad eligible floodplain -> Active Domain uses the authoritative
# Stage 4 Step 3 broad risk/event family and is not restricted to SF origin.
risk_floodplain_broad <- risk %>%
  filter(
    FP_REACTIVATE_RISK_SET == 1L,
    FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L
  )
broad_source_qa <- risk_floodplain_broad %>%
  mutate(FP_REACTIVATE_SOURCE_PRIMARY = as.character(FP_REACTIVATE_SOURCE_PRIMARY)) %>%
  group_by(FP_REACTIVATE_SOURCE_PRIMARY) %>%
  summarise(
    risk_rows = n(),
    events = sum(FP_REACTIVATE_EVT == 1L, na.rm = TRUE),
    .groups = "drop"
  )
write_csv(broad_source_qa, file.path(out_dir, "00_broad_floodplain_source_QA.csv"))

# Every strict eligible SF->AD row/event must be contained in the eligible broad
# FP population. This is a semantic invariant of Stage 4 Step 3 v6.7.
strict_broad_membership_qa <- risk %>%
  summarise(
    strict_risk_not_broad = sum(
      REACTIVATE_RISK_SET == 1L & M3_MODEL_ELIGIBLE_PRIMARY == 1L &
        !(FP_REACTIVATE_RISK_SET == 1L & FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L),
      na.rm = TRUE
    ),
    strict_events_not_broad = sum(
      REACTIVATE_EVT == 1L & M3_MODEL_ELIGIBLE_PRIMARY == 1L &
        !(FP_REACTIVATE_EVT == 1L & FP_REACTIVATE_RISK_SET == 1L &
            FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L),
      na.rm = TRUE
    )
  )
write_csv(strict_broad_membership_qa, file.path(out_dir, "00_broad_floodplain_membership_QA.csv"))
if (strict_broad_membership_qa$strict_risk_not_broad[1] > 0L ||
    strict_broad_membership_qa$strict_events_not_broad[1] > 0L) {
  stop("[Broad FP QA] Strict eligible SF->AD population is not fully nested inside eligible broad FP->AD. Inspect 00_broad_floodplain_membership_QA.csv.")
}

risk_baseline_fp <- risk_model %>% filter(BASE_REACTIVATE_RISK_SET_DERIVED == 1L)
risk_deposition <- risk_model %>% filter(STORAGE_RISK_SET == 1L)
risk_stabilise <- risk_model %>% filter(STABILISE_RISK_SET == 1L)
risk_storage_rework <- risk_model %>% filter(STORAGE_REWORK_RISK_SET == 1L)
risk_any <- risk_model %>% filter(ANY_STATE_RISK_SET == 1L)

# Strict observed-state sensitivity sets. These do not inherit latent states.
# Existing state-only output names are retained for backwards compatibility;
# methodologically they are the Step 3 strict observed-state definition.
risk_model_strict <- risk %>% filter(M3_MODEL_ELIGIBLE_STRICT == 1L)
risk_erosion_pure <- risk_model_strict %>%
  filter(REACTIVATE_RISK_SET_STRICT_AUDIT == 1L)
risk_deposition_pure <- risk_model_strict %>%
  filter(STORAGE_RISK_SET_STRICT_AUDIT == 1L)
risk_stabilise_pure <- risk_model_strict %>%
  filter(STABILISE_RISK_SET_STRICT_AUDIT == 1L)
risk_storage_rework_pure <- risk_model_strict %>%
  filter(STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1L)
risk_any_pure <- risk_model_strict %>%
  filter(ANY_STATE_RISK_SET_STRICT_AUDIT == 1L)

# High-support pure-state sensitivity. Step 3 strict eligibility already removes
# unresolved, mixed, chain-failure and other invalid endpoints. This additional
# definition requires both endpoint state-support fractions to meet the explicit
# user-selected threshold, making it more conservative than the strict model.
risk_model_pure_state <- risk_model_strict %>%
  filter(
    M3_MIXED_T1 == 0L,
    M3_MIXED_T2 == 0L,
    is.finite(M3_STATE_SUPPORT_T1),
    is.finite(M3_STATE_SUPPORT_T2),
    M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
    M3_STATE_SUPPORT_T2 >= PureStateMinSupport
  )
risk_erosion_pure_state <- risk_model_pure_state %>%
  filter(REACTIVATE_RISK_SET_STRICT_AUDIT == 1L)
risk_deposition_pure_state <- risk_model_pure_state %>%
  filter(STORAGE_RISK_SET_STRICT_AUDIT == 1L)
risk_stabilise_pure_state <- risk_model_pure_state %>%
  filter(STABILISE_RISK_SET_STRICT_AUDIT == 1L)
risk_storage_rework_pure_state <- risk_model_pure_state %>%
  filter(STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1L)
risk_any_pure_state <- risk_model_pure_state %>%
  filter(ANY_STATE_RISK_SET_STRICT_AUDIT == 1L)

pure_state_eligibility_qa <- risk %>%
  summarise(
    total_rows = n(),
    primary_eligible_rows = sum(M3_MODEL_ELIGIBLE_PRIMARY == 1L, na.rm = TRUE),
    strict_eligible_rows = sum(M3_MODEL_ELIGIBLE_STRICT == 1L, na.rm = TRUE),
    pure_state_eligible_rows = sum(
      M3_MODEL_ELIGIBLE_STRICT == 1L &
        M3_MIXED_T1 == 0L & M3_MIXED_T2 == 0L &
        is.finite(M3_STATE_SUPPORT_T1) & is.finite(M3_STATE_SUPPORT_T2) &
        M3_STATE_SUPPORT_T1 >= PureStateMinSupport &
        M3_STATE_SUPPORT_T2 >= PureStateMinSupport,
      na.rm = TRUE
    ),
    strict_rows_missing_support = sum(
      M3_MODEL_ELIGIBLE_STRICT == 1L &
        (!is.finite(M3_STATE_SUPPORT_T1) | !is.finite(M3_STATE_SUPPORT_T2)),
      na.rm = TRUE
    ),
    strict_rows_below_support_threshold = sum(
      M3_MODEL_ELIGIBLE_STRICT == 1L &
        is.finite(M3_STATE_SUPPORT_T1) & is.finite(M3_STATE_SUPPORT_T2) &
        (M3_STATE_SUPPORT_T1 < PureStateMinSupport |
           M3_STATE_SUPPORT_T2 < PureStateMinSupport),
      na.rm = TRUE
    ),
    pure_state_min_support = PureStateMinSupport
  )
write_csv(pure_state_eligibility_qa, file.path(out_dir, "00_pure_state_eligibility_QA.csv"))

# Transition-specific event/non-event distributions for interval-start distances.
distance_summary_fields <- intersect(
  c("DIST_ACTIVE_CURR", "DIST_WATER_CURR", "DIST_CL_REF", "DIST_CL_CURR",
    "DIST_CL_PREV", "DIST_CHANNEL_PREV", "DIST_BANK_PREV", "BANK_SETBACK_PREV"),
  names(risk_model)
)
transition_distance_specs <- list(
  list(name = "reactivation", data = risk_erosion, event = "REACTIVATE_EVT"),
  list(name = "initial_floodplain_reactivation", data = risk_baseline_fp, event = "BASE_REACTIVATE_EVT"),
  list(name = "storage", data = risk_deposition, event = "STORAGE_EVT"),
  list(name = "stabilisation", data = risk_stabilise, event = "STABILISE_EVT"),
  list(name = "any_named_primary_transition", data = risk_any, event = "ANY_CONFIRMED_EVT")
)
event_non_event_distance_summary <- bind_rows(lapply(transition_distance_specs, function(spec) {
  if (nrow(spec$data) == 0L || !spec$event %in% names(spec$data)) return(NULL)
  bind_rows(lapply(distance_summary_fields, function(nm) {
    x <- num_or_na(spec$data[[nm]])
    ev <- int01(spec$data[[spec$event]])
    bind_rows(lapply(c(0L, 1L), function(e) {
      z <- x[ev == e & is.finite(x)]
      tibble::tibble(
        transition = spec$name,
        field = nm,
        event = e,
        n = length(z),
        mean_m = if (length(z) > 0L) mean(z) else NA_real_,
        sd_m = if (length(z) > 1L) stats::sd(z) else NA_real_,
        q25_m = safe_quantile(z, 0.25),
        median_m = safe_quantile(z, 0.5),
        q75_m = safe_quantile(z, 0.75)
      )
    }))
  }))
}))
write_if_nonempty(event_non_event_distance_summary, "00_event_non_event_distance_summary.csv")

# Episode-entry summaries freeze the spatial class at entry to each contiguous
# at-risk episode. This complements the interval-start time-varying summaries
# without changing the principal counting-process models.
# [FRAF archive / Historic/QA function: choose_episode_bin]
# Choose a supported exposure/historical-episode grouping field.
choose_episode_bin <- function(candidates, dat) {
  hit <- candidates[candidates %in% names(dat)]
  if (length(hit) == 0L) return(NA_character_)
  usable <- hit[vapply(hit, function(nm) {
    z <- as.character(dat[[nm]])
    sum(!is.na(z) & z != "") > 0L
  }, logical(1))]
  if (length(usable) == 0L) return(NA_character_)
  usable[1]
}

# [FRAF archive / Historic/QA function: summarise_entry_episodes]
# Summarise first entry, recurrence, or exposure-specific events within a risk set.
summarise_entry_episodes <- function(dat, risk_field, event_field, bin_field, transition) {
  if (is.na(bin_field) || !all(c(risk_field, event_field, bin_field) %in% names(dat))) return(NULL)
  episode_rows <- dat %>%
    arrange(PLACE_ID, tstart_yr, tstop_yr) %>%
    group_by(PLACE_ID) %>%
    mutate(
      .risk = int01(.data[[risk_field]]),
      .event = int01(.data[[event_field]]),
      .prev_risk = lag(.risk, default = 0L),
      .prev_stop = lag(tstop_yr),
      .new_episode = as.integer(
        .risk == 1L & (
          .prev_risk != 1L | is.na(.prev_stop) | abs(.prev_stop - tstart_yr) >= 1e-7
        )
      ),
      .episode_id = cumsum(.new_episode)
    ) %>%
    filter(.risk == 1L, .episode_id > 0L) %>%
    group_by(PLACE_ID, .episode_id) %>%
    summarise(
      entry_bin = first_nonmissing(as.character(.data[[bin_field]])),
      episode_start_yr = min(tstart_yr, na.rm = TRUE),
      episode_end_yr = max(tstop_yr, na.rm = TRUE),
      duration_yr = episode_end_yr - episode_start_yr,
      event = max(.event, na.rm = TRUE),
      interval_rows = n(),
      .groups = "drop"
    ) %>%
    filter(!is.na(entry_bin), entry_bin != "")

  if (nrow(episode_rows) == 0L) return(NULL)
  episode_rows %>%
    group_by(entry_bin) %>%
    summarise(
      episodes = n(),
      unique_places = n_distinct(PLACE_ID),
      events = sum(event == 1L, na.rm = TRUE),
      event_fraction = events / episodes,
      median_episode_duration_yr = safe_quantile(duration_yr, 0.5),
      p25_episode_duration_yr = safe_quantile(duration_yr, 0.25),
      p75_episode_duration_yr = safe_quantile(duration_yr, 0.75),
      .groups = "drop"
    ) %>%
    mutate(
      transition = .env$transition,
      entry_bin_field = .env$bin_field,
      time_basis = "spatial class frozen at at-risk episode entry",
      .before = 1
    )
}

react_episode_bin <- choose_episode_bin(
  c("DIST_CL_PREV_BIN", "DIST_ACTIVE_CURR_BIN", ".DIST_ACTIVE_BIN_FIELD", "DIST_CL_REF_BIN"), risk_model
)
storage_episode_bin <- choose_episode_bin(
  c("DIST_CL_PREV_BIN", "DIST_ACTIVE_CURR_BIN", ".DIST_ACTIVE_BIN_FIELD", "DIST_WATER_CURR_BIN"), risk_model
)
stabilise_episode_bin <- choose_episode_bin(
  c("DIST_CL_PREV_BIN", "DIST_ACTIVE_CURR_BIN", ".DIST_ACTIVE_BIN_FIELD", "DIST_CL_REF_BIN"), risk_model
)

episode_entry_spatial_summary <- bind_rows(
  summarise_entry_episodes(risk_model, "REACTIVATE_RISK_SET", "REACTIVATE_EVT", react_episode_bin, "reactivation"),
  summarise_entry_episodes(risk_model, "BASE_REACTIVATE_RISK_SET_DERIVED", "BASE_REACTIVATE_EVT", react_episode_bin, "initial_floodplain_reactivation"),
  summarise_entry_episodes(risk_model, "STORAGE_RISK_SET", "STORAGE_EVT", storage_episode_bin, "storage"),
  summarise_entry_episodes(risk_model, "STABILISE_RISK_SET", "STABILISE_EVT", stabilise_episode_bin, "stabilisation")
)
write_if_nonempty(episode_entry_spatial_summary, "04e_episode_entry_spatial_summary.csv")

run_diagnostics <- tibble(
  n_rows = nrow(risk),
  n_principal_model_rows = nrow(risk_model),
  n_principal_excluded_rows = nrow(risk) - nrow(risk_model),
  event_definition_used = "PRIMARY_AMBIGUITY_BRIDGED",
  n_strict_model_rows = nrow(risk_model_strict),
  n_union_risk_rows = nrow(risk_valid),
  n_erosion_risk_rows = nrow(risk_erosion),
  n_initial_floodplain_reactivate_risk_rows = nrow(risk_baseline_fp),
  n_deposition_risk_rows = nrow(risk_deposition),
  n_stabilise_risk_rows = nrow(risk_stabilise),
  n_any_risk_rows = nrow(risk_any),
  n_original_at_risk_rows = sum(risk$at_risk == 1, na.rm = TRUE),
  n_places = n_distinct(risk$PLACE_ID),
  n_intervals = n_distinct(risk$tstop_yr),
  n_broad_floodplain_reactivation_risk_rows = nrow(risk_floodplain_broad),
  n_broad_floodplain_reactivation_events = sum(risk_floodplain_broad$FP_REACTIVATE_EVT == 1, na.rm = TRUE),
  n_reactivation_events = sum(risk_erosion$REACTIVATE_EVT == 1, na.rm = TRUE),
  n_initial_floodplain_reactivation_events = sum(risk_baseline_fp$BASE_REACTIVATE_EVT == 1, na.rm = TRUE),
  n_initial_floodplain_cohort_places = n_distinct(risk$PLACE_ID[risk$INIT_FP_COHORT == 1]),
  n_storage_events = sum(risk_deposition$STORAGE_EVT == 1, na.rm = TRUE),
  n_stabilisation_events = sum(risk_stabilise$STABILISE_EVT == 1, na.rm = TRUE),
  n_storage_rework_events = sum(risk_any$STORAGE_REWORK_EVT == 1, na.rm = TRUE),
  n_floodplain_storage_events = sum(risk_any$FP_STORAGE_EVT == 1, na.rm = TRUE),
  n_primary_named_transition_events = sum(risk_any$ANY_CONFIRMED_EVT == 1, na.rm = TRUE),
  n_state_transition_events = sum(risk_any$ANY_STATE_EVT == 1, na.rm = TRUE),
  n_state_only_reactivation_events = sum(risk_erosion_pure$REACTIVATE_TRANS == 1, na.rm = TRUE),
  n_state_only_storage_events = sum(risk_deposition_pure$STORAGE_TRANS == 1, na.rm = TRUE),
  n_state_only_stabilisation_events = sum(risk_stabilise_pure$STABILISE_TRANS == 1, na.rm = TRUE),
  n_state_only_any_transition_events = sum(risk_any_pure$ANY_STATE_EVT == 1, na.rm = TRUE),
  has_centreline_ref_distance = "DIST_CL_REF" %in% names(risk),
  has_centreline_ref_bin = "DIST_CL_REF_BIN" %in% names(risk),
  has_active_distance = any(active_distance_candidates %in% names(risk)),
  has_active_bin = any(active_bin_candidates %in% names(risk)),
  has_water_distance = any(water_distance_candidates %in% names(risk)),
  has_water_bin = any(water_bin_candidates %in% names(risk)),
  centreline_distance_field_used = centreline_dist_field,
  centreline_bin_field_used = centreline_bin_field,
  active_distance_field_used = active_dist_field,
  active_bin_field_used = active_bin_field,
  water_distance_field_used = water_dist_field,
  water_bin_field_used = water_bin_field,
  has_prev_asm = "ASM_CLASS_PREV" %in% names(risk),
  has_fp_condition = !is.na(fp_condition_field),
  fp_condition_field_used = fp_condition_field,
  final_onto_raw_field_used = final_onto_raw_field,
  surface_age_est_field_used = surface_age_est_field,
  fp_stab_field_used = fp_stab_field,
  fp_recent_field_used = fp_recent_field,
  fp_reworked_field_used = fp_reworked_field,
  spatial_time_basis = "INTERVAL_START_Y1",
  strict_temporal_alignment = isTRUE(StrictTemporalAlignment),
  run_temporal_sensitivity = isTRUE(RunTemporalSensitivity),
  temporal_sensitivity_fields = paste(spatial_y0_candidates, collapse = "; "),
  temporal_alignment_fatal_failures = sum(
    spatial_temporal_alignment_qa$n[spatial_temporal_alignment_qa$fatal],
    na.rm = TRUE
  )
)

write_csv(run_diagnostics, file.path(out_dir, "00_run_diagnostics.csv"))

# v17.10.12 historic broad-floodplain descriptive exposure summary.
broad_interval_summary <- risk_floodplain_broad %>%
  mutate(duration_yr = pmax(0, as.numeric(tstop_yr) - as.numeric(tstart_yr))) %>%
  group_by(y1, y2, tstart_yr, tstop_yr) %>%
  summarise(
    eligible_rows = n(),
    unique_places = n_distinct(PLACE_ID),
    events = sum(FP_REACTIVATE_EVT == 1L, na.rm = TRUE),
    place_years = sum(duration_yr, na.rm = TRUE),
    rate_per_1000_place_years = ifelse(place_years > 0, 1000 * events / place_years, NA_real_),
    .groups = "drop"
  )
write_csv(broad_interval_summary, file.path(out_dir, "00b_historic_broad_floodplain_reactivation_interval_summary.csv"))

broad_overall_summary <- risk_floodplain_broad %>%
  mutate(duration_yr = pmax(0, as.numeric(tstop_yr) - as.numeric(tstart_yr))) %>%
  summarise(
    model = "floodplain_reactivation_broad",
    transition = "Eligible Floodplain -> Active Domain",
    eligible_rows = n(),
    unique_places_exposed = n_distinct(PLACE_ID),
    events = sum(FP_REACTIVATE_EVT == 1L, na.rm = TRUE),
    unique_places_with_event = n_distinct(PLACE_ID[FP_REACTIVATE_EVT == 1L]),
    place_years = sum(duration_yr, na.rm = TRUE),
    rate_per_1000_place_years = ifelse(place_years > 0, 1000 * events / place_years, NA_real_)
  )
write_csv(broad_overall_summary, file.path(out_dir, "00b_historic_broad_floodplain_reactivation_summary.csv"))

state_risk_qa <- risk %>%
  count(STATE1_ONTOLOGY, STATE2_ONTOLOGY, REACTIVATE_RISK_SET, STORAGE_RISK_SET, STABILISE_RISK_SET,
        REACTIVATE_EVT, STORAGE_EVT, STABILISE_EVT, name = "n")
write_csv(state_risk_qa, file.path(out_dir, "00_state_risk_event_QA.csv"))

state_risk_qa_state_only <- risk %>%
  count(
    STATE1_ONTOLOGY, STATE2_ONTOLOGY,
    REACTIVATE_RISK_SET_STRICT_AUDIT,
    STORAGE_RISK_SET_STRICT_AUDIT,
    STABILISE_RISK_SET_STRICT_AUDIT,
    ANY_STATE_RISK_SET_STRICT_AUDIT,
    REACTIVATE_TRANS, STORAGE_TRANS, STABILISE_TRANS, ANY_STATE_EVT,
    name = "n"
  )
write_csv(state_risk_qa_state_only, file.path(out_dir, "00_state_only_state_risk_event_QA.csv"))

fp_condition_qa <- risk %>%
  count(FP_CONDITION_MODEL, STATE2_ONTOLOGY, FINAL_ONTO_RAW_MODEL, FP_STAB_MODEL, FP_RECENT_MODEL, FP_REWORKED_MODEL, name = "n")
write_csv(fp_condition_qa, file.path(out_dir, "00_fp_condition_QA.csv"))

fp_condition_interval_summary <- risk %>%
  group_by(tstop_yr, FP_CONDITION_MODEL) %>%
  summarise(n = n(), mean_surface_age_est = mean(SURFACE_AGE_EST_MODEL, na.rm = TRUE), .groups = "drop") %>%
  group_by(tstop_yr) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()
write_csv(fp_condition_interval_summary, file.path(out_dir, "00_fp_condition_interval_summary.csv"))

initial_fp_qa <- risk %>%
  summarise(
    rows = n(),
    n_init_fp_rows = sum(INIT_FP == 1, na.rm = TRUE),
    n_base_risk_rows = sum(BASE_RISK == 1, na.rm = TRUE),
    n_init_fp_cohort_rows = sum(INIT_FP_COHORT == 1, na.rm = TRUE),
    n_base_reactivate_risk_rows = sum(BASE_REACTIVATE_RISK_SET_DERIVED == 1, na.rm = TRUE),
    n_base_reactivate_events = sum(BASE_REACTIVATE_EVT == 1, na.rm = TRUE),
    n_base_reactivate_events_outside_derived_risk = sum(BASE_REACTIVATE_EVT == 1 & BASE_REACTIVATE_RISK_SET_DERIVED != 1, na.rm = TRUE),
    n_base_risk_without_effective_stabilised_start = sum(BASE_REACTIVATE_RISK_SET_DERIVED == 1 & M3_EFFECTIVE_STATE_T1_PRIMARY != "STABILISED_FLOODPLAIN", na.rm = TRUE),
    mean_init_fp_prop = mean(INIT_FP_PROP, na.rm = TRUE),
    total_init_fp_area = sum(INIT_FP_AREA, na.rm = TRUE)
  )
write_csv(initial_fp_qa, file.path(out_dir, "00_initial_floodplain_cohort_QA.csv"))

field_inventory <- tibble(field = names(risk))
write_csv(field_inventory, file.path(out_dir, "00_field_inventory.csv"))

# Event/risk-set QA tables
event_risk_qa <- risk %>%
  summarise(
    rows = n(),
    reactivate_events_all = sum(REACTIVATE_EVT == 1, na.rm = TRUE),
    storage_events_all = sum(STORAGE_EVT == 1, na.rm = TRUE),
    stabilise_events_all = sum(STABILISE_EVT == 1, na.rm = TRUE),
    storage_rework_events_all = sum(STORAGE_REWORK_EVT == 1, na.rm = TRUE),
    primary_named_events_all = sum(ANY_CONFIRMED_EVT == 1, na.rm = TRUE),
    state_transitions_all = sum(ANY_STATE_EVT == 1, na.rm = TRUE),
    reactivate_events_in_risk = sum(REACTIVATE_EVT == 1 & REACTIVATE_RISK_SET == 1, na.rm = TRUE),
    base_reactivate_events_in_initial_fp_risk = sum(BASE_REACTIVATE_EVT == 1 & BASE_REACTIVATE_RISK_SET_DERIVED == 1, na.rm = TRUE),
    storage_events_in_risk = sum(STORAGE_EVT == 1 & STORAGE_RISK_SET == 1, na.rm = TRUE),
    stabilise_events_in_risk = sum(STABILISE_EVT == 1 & STABILISE_RISK_SET == 1, na.rm = TRUE),
    storage_rework_events_in_risk = sum(STORAGE_REWORK_EVT == 1 & STORAGE_REWORK_RISK_SET == 1, na.rm = TRUE),
    primary_named_events_in_risk = sum(ANY_CONFIRMED_EVT == 1 & ANY_STATE_RISK_SET == 1, na.rm = TRUE),
    state_transitions_in_risk = sum(ANY_STATE_EVT == 1 & ANY_STATE_RISK_SET == 1, na.rm = TRUE),
    reactivate_events_excluded_from_risk = sum(REACTIVATE_EVT == 1 & REACTIVATE_RISK_SET != 1, na.rm = TRUE),
    storage_events_excluded_from_risk = sum(STORAGE_EVT == 1 & STORAGE_RISK_SET != 1, na.rm = TRUE),
    stabilise_events_excluded_from_risk = sum(STABILISE_EVT == 1 & STABILISE_RISK_SET != 1, na.rm = TRUE),
    storage_rework_events_excluded_from_risk = sum(STORAGE_REWORK_EVT == 1 & STORAGE_REWORK_RISK_SET != 1, na.rm = TRUE)
  )
write_csv(event_risk_qa, file.path(out_dir, "00_event_risk_set_QA.csv"))

event_risk_qa_pure <- risk %>%
  summarise(
    rows = n(),
    state_only_reactivate_events_all = sum(REACTIVATE_TRANS == 1, na.rm = TRUE),
    state_only_storage_events_all = sum(STORAGE_TRANS == 1, na.rm = TRUE),
    state_only_stabilise_events_all = sum(STABILISE_TRANS == 1, na.rm = TRUE),
    state_only_storage_rework_events_all = sum(STORAGE_REWORK_TRANS == 1, na.rm = TRUE),
    state_only_any_events_all = sum(ANY_STATE_EVT == 1, na.rm = TRUE),
    state_only_reactivate_events_in_risk = sum(REACTIVATE_TRANS == 1 & REACTIVATE_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
    state_only_storage_events_in_risk = sum(STORAGE_TRANS == 1 & STORAGE_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
    state_only_stabilise_events_in_risk = sum(STABILISE_TRANS == 1 & STABILISE_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
    state_only_storage_rework_events_in_risk = sum(STORAGE_REWORK_TRANS == 1 & STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
    state_only_any_events_in_risk = sum(ANY_STATE_EVT == 1 & ANY_STATE_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
    state_only_reactivate_events_excluded_from_risk = sum(REACTIVATE_TRANS == 1 & REACTIVATE_RISK_SET_STRICT_AUDIT != 1, na.rm = TRUE),
    state_only_storage_events_excluded_from_risk = sum(STORAGE_TRANS == 1 & STORAGE_RISK_SET_STRICT_AUDIT != 1, na.rm = TRUE),
    state_only_stabilise_events_excluded_from_risk = sum(STABILISE_TRANS == 1 & STABILISE_RISK_SET_STRICT_AUDIT != 1, na.rm = TRUE),
    state_only_storage_rework_events_excluded_from_risk = sum(STORAGE_REWORK_TRANS == 1 & STORAGE_REWORK_RISK_SET_STRICT_AUDIT != 1, na.rm = TRUE)
  )
write_csv(event_risk_qa_pure, file.path(out_dir, "00_state_only_event_risk_set_QA.csv"))

if ("DOMAIN_TRANS" %in% names(risk)) {
  domain_event_qa <- risk %>%
    count(DOMAIN_TRANS, REACTIVATE_EVT, STORAGE_EVT, STABILISE_EVT, ANY_CONFIRMED_EVT, ANY_STATE_EVT, REACTIVATE_RISK_SET, STORAGE_RISK_SET, STABILISE_RISK_SET, ANY_STATE_RISK_SET, name = "n")
  write_csv(domain_event_qa, file.path(out_dir, "00_domain_transition_event_QA.csv"))
}

# -----------------------------
# [FRAF archive / workflow]
# Kaplan-Meier branch: describe time to transition/persistence in eligible places;
# the first-event cohort must not be conflated with recurrent-event risk sets.
# 2. Baseline and stratified KM
# -----------------------------

# KM is a first-event estimator. Recurrent rows after the first event for a
# PLACE_ID are excluded here; the full recurrent risk sets remain available to
# AG summaries and counting-process Cox models.
# [FRAF archive / code note]
# First qualifying event removes a PLACE from its initial-event risk cohort;
# this differs from recurrent Andersen-Gill exposure.
# [FRAF archive / Historic/QA function: make_first_event_table]
# Identify the first qualifying event per PLACE for cohort-restricted survival analyses.
make_first_event_table <- function(dat, event_field) {
  if (nrow(dat) == 0) return(dat)
  dat %>%
    arrange(PLACE_ID, tstart_yr, tstop_yr) %>%
    group_by(PLACE_ID) %>%
    mutate(
      .EVENT_VALUE = int01(.data[[event_field]]),
      .PRIOR_EVENT = lag(cummax(.EVENT_VALUE), default = 0L)
    ) %>%
    filter(.PRIOR_EVENT == 0L) %>%
    ungroup() %>%
    select(-.EVENT_VALUE, -.PRIOR_EVENT)
}

km_risk_erosion <- make_first_event_table(risk_erosion, "REACTIVATE_EVT")
km_risk_floodplain_broad <- make_first_event_table(risk_floodplain_broad, "FP_REACTIVATE_EVT")
km_risk_deposition <- make_first_event_table(risk_deposition, "STORAGE_EVT")
km_risk_stabilise <- make_first_event_table(risk_stabilise, "STABILISE_EVT")
km_risk_storage_rework <- make_first_event_table(risk_storage_rework, "STORAGE_REWORK_EVT")
km_risk_erosion_state <- make_first_event_table(risk_erosion_pure, "REACTIVATE_TRANS")
km_risk_deposition_state <- make_first_event_table(risk_deposition_pure, "STORAGE_TRANS")
km_risk_stabilise_state <- make_first_event_table(risk_stabilise_pure, "STABILISE_TRANS")
km_risk_storage_rework_state <- make_first_event_table(risk_storage_rework_pure, "STORAGE_REWORK_TRANS")

if (RunKM) {

  if (sum(km_risk_floodplain_broad$FP_REACTIVATE_EVT == 1, na.rm = TRUE) > 0) {
    km_FP_BROAD <- survfit(
      Surv(tstart_yr, tstop_yr, FP_REACTIVATE_EVT) ~ 1,
      data = km_risk_floodplain_broad
    )
    export_km_fit(km_FP_BROAD, "01a_KM_floodplain_reactivation_broad_baseline", "floodplain_reactivation_broad")
    p_km_FP_BROAD <- ggsurvplot(
      km_FP_BROAD, conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability eligible floodplain has not yet entered the Active Domain",
      title = "Broad eligible floodplain remaining outside the Active Domain",
      risk.table = FALSE
    )
    safe_plot_save(p_km_FP_BROAD$plot, "01a_KM_floodplain_reactivation_broad_baseline.png")
  }

  if (sum(km_risk_erosion$REACTIVATE_EVT == 1, na.rm = TRUE) > 0) {

    km_E <- survfit(
      Surv(tstart_yr, tstop_yr, REACTIVATE_EVT) ~ 1,
      data = km_risk_erosion
    )
    export_km_fit(km_E, "01_KM_active_domain_reactivation_baseline", "active_domain_reactivation")

    p_km_E <- ggsurvplot(
      km_E,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability place has not yet been reached by the Active Domain",
      title = "Places remaining outside the Active Domain",
      risk.table = FALSE
    )

    safe_plot_save(p_km_E$plot, "01_KM_active_domain_reactivation_baseline.png")
  }

  if (sum(risk_baseline_fp$BASE_REACTIVATE_EVT == 1, na.rm = TRUE) > 0) {

    km_BASE <- survfit(
      Surv(tstart_yr, tstop_yr, BASE_REACTIVATE_EVT) ~ 1,
      data = risk_baseline_fp
    )
    export_km_fit(km_BASE, "01b_KM_initial_floodplain_reactivation_baseline", "initial_floodplain_reactivation")

    p_km_BASE <- ggsurvplot(
      km_BASE,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability initial floodplain remains outside the Active Domain",
      title = "Initial floodplain remaining outside the Active Domain",
      risk.table = FALSE
    )

    safe_plot_save(p_km_BASE$plot, "01b_KM_initial_floodplain_reactivation_baseline.png")
  } else {
    message("[KM] Skipped initial-floodplain cohort KM; rows = ", nrow(risk_baseline_fp),
            "; events = ", sum(risk_baseline_fp$BASE_REACTIVATE_EVT == 1, na.rm = TRUE))
  }

  if (sum(km_risk_deposition$STORAGE_EVT == 1, na.rm = TRUE) > 0) {

    km_D <- survfit(
      Surv(tstart_yr, tstop_yr, STORAGE_EVT) ~ 1,
      data = km_risk_deposition
    )
    export_km_fit(km_D, "02_KM_depositional_storage_baseline", "depositional_storage")

    p_km_D <- ggsurvplot(
      km_D,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability active place has not yet become storage",
      title = "Active places becoming depositional storage",
      risk.table = FALSE
    )

    safe_plot_save(p_km_D$plot, "02_KM_depositional_storage_baseline.png")
  }


  if (sum(km_risk_stabilise$STABILISE_EVT == 1, na.rm = TRUE) > 0) {

    km_S <- survfit(
      Surv(tstart_yr, tstop_yr, STABILISE_EVT) ~ 1,
      data = km_risk_stabilise
    )
    export_km_fit(km_S, "02b_KM_floodplain_stabilisation_baseline", "floodplain_stabilisation")

    p_km_S <- ggsurvplot(
      km_S,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability storage has not yet become stable floodplain",
      title = "Depositional storage becoming stable floodplain",
      risk.table = FALSE
    )

    safe_plot_save(p_km_S$plot, "02b_KM_floodplain_stabilisation_baseline.png")
  }

  if (isTRUE(RunStorageReworkInterpretive) && sum(km_risk_storage_rework$STORAGE_REWORK_EVT == 1, na.rm = TRUE) > 0) {
    km_RW <- survfit(
      Surv(tstart_yr, tstop_yr, STORAGE_REWORK_EVT) ~ 1,
      data = km_risk_storage_rework
    )
    export_km_fit(km_RW, "02c_KM_storage_reworking_baseline", "depositional_storage_reworking")
    p_km_RW <- ggsurvplot(
      km_RW,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability storage has not yet returned to the Active Domain",
      title = "Depositional storage reworking to Active Domain",
      risk.table = FALSE
    )
    safe_plot_save(p_km_RW$plot, "02c_KM_storage_reworking_baseline.png")
  } else if (isTRUE(RunStorageReworkInterpretive)) {
    message("[KM] Skipped DS->AD storage-reworking KM; rows = ", nrow(km_risk_storage_rework),
            "; events = ", sum(km_risk_storage_rework$STORAGE_REWORK_EVT == 1, na.rm = TRUE))
  }

  # State-only baseline KM curves. These use ONLY state-to-state
  # transitions, not pre-existing process-event flags from the Risk Table.
  if (sum(km_risk_erosion_state$REACTIVATE_TRANS == 1, na.rm = TRUE) > 0) {
    km_E_pure <- survfit(Surv(tstart_yr, tstop_yr, REACTIVATE_TRANS) ~ 1, data = km_risk_erosion_state)
    export_km_fit(km_E_pure, "01p_KM_state_only_active_domain_reactivation_baseline", "state_only_active_domain_reactivation")
    p_km_E_pure <- ggsurvplot(
      km_E_pure,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability Stabilised Floodplain remains outside the Active Domain",
      title = "State-only: Stabilised Floodplain reached by Active Domain",
      risk.table = FALSE
    )
    safe_plot_save(p_km_E_pure$plot, "01p_KM_state_only_active_domain_reactivation_baseline.png")
  } else {
    message("[KM pure] Skipped active-domain reactivation; rows = ", nrow(km_risk_erosion_state),
            "; events = ", sum(km_risk_erosion_state$REACTIVATE_TRANS == 1, na.rm = TRUE))
  }

  if (sum(km_risk_deposition_state$STORAGE_TRANS == 1, na.rm = TRUE) > 0) {
    km_D_pure <- survfit(Surv(tstart_yr, tstop_yr, STORAGE_TRANS) ~ 1, data = km_risk_deposition_state)
    export_km_fit(km_D_pure, "02p_KM_state_only_depositional_storage_baseline", "state_only_depositional_storage")
    p_km_D_pure <- ggsurvplot(
      km_D_pure,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability active place remains active",
      title = "State-only: active places becoming depositional storage",
      risk.table = FALSE
    )
    safe_plot_save(p_km_D_pure$plot, "02p_KM_state_only_depositional_storage_baseline.png")
  } else {
    message("[KM pure] Skipped depositional storage; rows = ", nrow(km_risk_deposition_state),
            "; events = ", sum(km_risk_deposition_state$STORAGE_TRANS == 1, na.rm = TRUE))
  }

  if (sum(km_risk_stabilise_state$STABILISE_TRANS == 1, na.rm = TRUE) > 0) {
    km_S_pure <- survfit(Surv(tstart_yr, tstop_yr, STABILISE_TRANS) ~ 1, data = km_risk_stabilise_state)
    export_km_fit(km_S_pure, "02bp_KM_state_only_floodplain_stabilisation_baseline", "state_only_floodplain_stabilisation")
    p_km_S_pure <- ggsurvplot(
      km_S_pure,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability depositional storage remains unstabilised",
      title = "State-only: depositional storage becoming stable floodplain",
      risk.table = FALSE
    )
    safe_plot_save(p_km_S_pure$plot, "02bp_KM_state_only_floodplain_stabilisation_baseline.png")
  } else {
    message("[KM pure] Skipped floodplain stabilisation; rows = ", nrow(km_risk_stabilise_state),
            "; events = ", sum(km_risk_stabilise_state$STABILISE_TRANS == 1, na.rm = TRUE))
  }

  if (isTRUE(RunStorageReworkInterpretive) && sum(km_risk_storage_rework_state$STORAGE_REWORK_TRANS == 1, na.rm = TRUE) > 0) {
    km_RW_pure <- survfit(Surv(tstart_yr, tstop_yr, STORAGE_REWORK_TRANS) ~ 1, data = km_risk_storage_rework_state)
    export_km_fit(km_RW_pure, "02cp_KM_state_only_storage_reworking_baseline", "state_only_depositional_storage_reworking")
    p_km_RW_pure <- ggsurvplot(
      km_RW_pure,
      conf.int = FALSE,
      xlab = "Years since start of record",
      ylab = "Probability depositional storage remains outside the Active Domain",
      title = "State-only: depositional storage reworking to Active Domain",
      risk.table = FALSE
    )
    safe_plot_save(p_km_RW_pure$plot, "02cp_KM_state_only_storage_reworking_baseline.png")
  } else if (isTRUE(RunStorageReworkInterpretive)) {
    message("[KM pure] Skipped DS->AD storage reworking; rows = ", nrow(km_risk_storage_rework_state),
            "; events = ", sum(km_risk_storage_rework_state$STORAGE_REWORK_TRANS == 1, na.rm = TRUE))
  }

  # Stratified KM curves. These all use the whole at-risk floodplain
  # (risk_valid), not a subset of active-zone or water-adjacent cells.
  # Each binning system gives a different descriptive exposure view.
  km_strata <- tibble::tribble(
    ~field, ~source_field, ~label, ~legend, ~prefix, ~time_basis,
    ".DIST_CL_BIN_FIELD", centreline_bin_field, paste0("selected centreline distance bin (", centreline_bin_field, ")"), "Distance from centreline", "centreline_distance", "selected field",
    "DIST_CL_REF_BIN", "DIST_CL_REF_BIN", "fixed reference-centreline distance bin", "Distance from reference centreline", "centreline_ref_distance", "fixed reference",
    "DIST_CL_CURR_BIN", "DIST_CL_CURR_BIN", "interval-start dated-centreline distance bin", "Distance at interval start", "centreline_interval_start_distance", "interval start y1",
    "DIST_CL_PREV_BIN", "DIST_CL_PREV_BIN", "interval-start local-centreline distance bin", "Local distance at interval start", "local_centreline_interval_start_distance", "interval start y1",
    ".DIST_CL_LANDMARK_BIN", ".DIST_CL_LANDMARK_BIN", "record-start landmark centreline-distance bin", "Record-start centreline distance", "centreline_landmark_distance", "record-start fixed",
    ".DIST_ACTIVE_BIN_FIELD", active_bin_field, paste0("selected Active Domain distance bin (", active_bin_field, ")"), "Distance from Active Domain", "active_domain_distance", "selected field",
    "DIST_ACTIVE_CURR_BIN", "DIST_ACTIVE_CURR_BIN", "interval-start Active Domain distance bin", "Distance at interval start", "active_domain_interval_start_distance", "interval start y1",
    "DIST_ACTIVE_PREV_BIN", "DIST_ACTIVE_PREV_BIN", "legacy previous-observation Active Domain distance bin", "Previous-observation distance", "active_domain_previous_observation_distance", "previous observation",
    ".DIST_ACTIVE_LANDMARK_BIN", ".DIST_ACTIVE_LANDMARK_BIN", "record-start landmark Active Domain distance bin", "Record-start Active Domain distance", "active_domain_landmark_distance", "record-start fixed",
    ".DIST_WATER_BIN_FIELD", water_bin_field, paste0("selected water distance bin (", water_bin_field, ")"), "Distance from water", "water_distance", "selected field",
    "DIST_WATER_CURR_BIN", "DIST_WATER_CURR_BIN", "interval-start water-distance bin", "Distance at interval start", "water_interval_start_distance", "interval start y1",
    "DIST_WATER_PREV_BIN", "DIST_WATER_PREV_BIN", "legacy previous-observation water-distance bin", "Previous-observation distance", "water_previous_observation_distance", "previous observation",
    ".DIST_WATER_LANDMARK_BIN", ".DIST_WATER_LANDMARK_BIN", "record-start landmark water-distance bin", "Record-start water distance", "water_landmark_distance", "record-start fixed"
  ) %>%
    filter(field %in% names(risk_valid)) %>%
    rowwise() %>%
    mutate(.non_missing = sum(!is.na(risk_valid[[field]]) & as.character(risk_valid[[field]]) != "")) %>%
    ungroup() %>%
    filter(.non_missing > 0) %>%
    mutate(
      .resolved_source = case_when(
        field == ".DIST_CL_BIN_FIELD" ~ paste0("resolved:", centreline_bin_field),
        field == ".DIST_ACTIVE_BIN_FIELD" ~ paste0("resolved:", active_bin_field),
        field == ".DIST_WATER_BIN_FIELD" ~ paste0("resolved:", water_bin_field),
        TRUE ~ paste0("resolved:", source_field)
      ),
      .alias_priority = as.integer(startsWith(field, ".DIST_") & grepl("_BIN_FIELD$", field))
    ) %>%
    arrange(.alias_priority) %>%
    distinct(.resolved_source, .keep_all = TRUE) %>%
    select(-.non_missing, -.resolved_source, -.alias_priority)

  write_csv(km_strata, file.path(out_dir, "04_spatial_KM_strata_inventory.csv"))
  km_bin_qa_rows <- list()

  # [FRAF archive / code note]
  # KM strata are descriptive risk-set summaries, not fitted transition
  # probabilities for arbitrary places outside the relevant state.
  # [FRAF archive / Historic/QA function: summarise_km_bin]
  # Produce a stratified survival/persistence summary for an exposure bin and transition.
  summarise_km_bin <- function(dat, stratum, event_field, transition, source_field, time_basis) {
    if (nrow(dat) == 0L || !stratum %in% names(dat) || !event_field %in% names(dat)) return(NULL)
    dat %>%
      mutate(.stratum = as.character(.data[[stratum]]), .event = int01(.data[[event_field]])) %>%
      filter(!is.na(.stratum), .stratum != "") %>%
      group_by(.stratum) %>%
      summarise(
        risk_rows = n(),
        unique_places = n_distinct(PLACE_ID),
        events = sum(.event == 1L, na.rm = TRUE),
        person_years = sum(pmax(0, tstop_yr - tstart_yr), na.rm = TRUE),
        interval_event_probability = events / risk_rows,
        event_rate_per_1000_place_years = ifelse(person_years > 0, 1000 * events / person_years, NA_real_),
        .groups = "drop"
      ) %>%
      transmute(
        transition = .env$transition, source_field = .env$source_field, time_basis = .env$time_basis,
        distance_bin = .stratum, risk_rows, unique_places, events, person_years,
        interval_event_probability, event_rate_per_1000_place_years
      )
  }

  for (ii in seq_len(nrow(km_strata))) {
    stratum <- km_strata$field[ii]
    stratum_label <- km_strata$label[ii]
    legend_label <- km_strata$legend[ii]
    file_prefix <- clean_filename(km_strata$prefix[ii])
    source_field <- km_strata$source_field[ii]
    time_basis <- km_strata$time_basis[ii]
    plot_scope <- case_when(
      time_basis == "interval start y1" ~ "descriptive time-varying interval-start exposure",
      time_basis == "record-start fixed" ~ "fixed record-start landmark exposure",
      time_basis == "fixed reference" ~ "fixed reference exposure",
      TRUE ~ time_basis
    )

    risk_s_E <- km_risk_erosion %>%
      mutate(.stratum = nonempty_factor(.data[[stratum]])) %>%
      filter(!is.na(.stratum))

    risk_s_BASE <- risk_baseline_fp %>%
      mutate(.stratum = nonempty_factor(.data[[stratum]])) %>%
      filter(!is.na(.stratum))

    risk_s_D <- km_risk_deposition %>%
      mutate(.stratum = nonempty_factor(.data[[stratum]])) %>%
      filter(!is.na(.stratum))

    risk_s_S <- km_risk_stabilise %>%
      mutate(.stratum = nonempty_factor(.data[[stratum]])) %>%
      filter(!is.na(.stratum))

    risk_s_RW <- km_risk_storage_rework %>%
      mutate(.stratum = nonempty_factor(.data[[stratum]])) %>%
      filter(!is.na(.stratum))

    km_bin_qa_rows[[length(km_bin_qa_rows) + 1L]] <- summarise_km_bin(risk_s_E, stratum, "REACTIVATE_EVT", "reactivation", source_field, time_basis)
    km_bin_qa_rows[[length(km_bin_qa_rows) + 1L]] <- summarise_km_bin(risk_s_BASE, stratum, "BASE_REACTIVATE_EVT", "initial_floodplain_reactivation", source_field, time_basis)
    km_bin_qa_rows[[length(km_bin_qa_rows) + 1L]] <- summarise_km_bin(risk_s_D, stratum, "STORAGE_EVT", "storage", source_field, time_basis)
    km_bin_qa_rows[[length(km_bin_qa_rows) + 1L]] <- summarise_km_bin(risk_s_S, stratum, "STABILISE_EVT", "stabilisation", source_field, time_basis)
    if (isTRUE(RunStorageReworkInterpretive)) {
      km_bin_qa_rows[[length(km_bin_qa_rows) + 1L]] <- summarise_km_bin(risk_s_RW, stratum, "STORAGE_REWORK_EVT", "storage_reworking", source_field, time_basis)
    }

    nlev_E <- n_distinct(risk_s_E$.stratum)
    nlev_BASE <- n_distinct(risk_s_BASE$.stratum)
    nlev_D <- n_distinct(risk_s_D$.stratum)
    nlev_S <- n_distinct(risk_s_S$.stratum)
    nlev_RW <- n_distinct(risk_s_RW$.stratum)

    if (nlev_E > 1 && nlev_E <= 12 && sum(risk_s_E$REACTIVATE_EVT == 1, na.rm = TRUE) > 0) {
      km_E_s <- survfit(
        Surv(tstart_yr, tstop_yr, REACTIVATE_EVT) ~ .stratum,
        data = risk_s_E
      )
      export_km_fit(km_E_s, paste0("04_KM_reactivation_by_", file_prefix), paste0("reactivation_by_", file_prefix))

      p_E_s <- ggsurvplot(
        km_E_s,
        data = risk_s_E,
        conf.int = FALSE,
        pval = FALSE,
        risk.table = FALSE,
        xlab = "Years since start of record",
        ylab = "Probability place has not yet been reached by the Active Domain",
        title = paste("Places remaining outside the Active Domain by", stratum_label, "[", plot_scope, "]"),
        legend.title = legend_label
      )

      safe_plot_save(p_E_s$plot, paste0("04_KM_reactivation_by_", file_prefix, ".png"), width = 9, height = 6)
    } else {
      message("[KM] Skipped reactivation stratification by ", stratum_label,
              "; rows = ", nrow(risk_s_E),
              "; levels = ", nlev_E,
              "; events = ", sum(risk_s_E$REACTIVATE_EVT == 1, na.rm = TRUE))
    }

    if (nlev_BASE > 1 && nlev_BASE <= 12 && sum(risk_s_BASE$BASE_REACTIVATE_EVT == 1, na.rm = TRUE) > 0) {
      km_BASE_s <- survfit(
        Surv(tstart_yr, tstop_yr, BASE_REACTIVATE_EVT) ~ .stratum,
        data = risk_s_BASE
      )
      export_km_fit(km_BASE_s, paste0("04a_KM_initial_floodplain_reactivation_by_", file_prefix), paste0("initial_floodplain_reactivation_by_", file_prefix))

      p_BASE_s <- ggsurvplot(
        km_BASE_s,
        data = risk_s_BASE,
        conf.int = FALSE,
        pval = FALSE,
        risk.table = FALSE,
        xlab = "Years since start of record",
        ylab = "Probability initial floodplain remains outside the Active Domain",
        title = paste("Initial floodplain remaining outside the Active Domain by", stratum_label, "[", plot_scope, "]"),
        legend.title = legend_label
      )

      safe_plot_save(p_BASE_s$plot, paste0("04a_KM_initial_floodplain_reactivation_by_", file_prefix, ".png"), width = 9, height = 6)
    } else {
      message("[KM] Skipped initial-floodplain reactivation stratification by ", stratum_label,
              "; rows = ", nrow(risk_s_BASE),
              "; levels = ", nlev_BASE,
              "; events = ", sum(risk_s_BASE$BASE_REACTIVATE_EVT == 1, na.rm = TRUE))
    }

    if (nlev_D > 1 && nlev_D <= 12 && sum(risk_s_D$STORAGE_EVT == 1, na.rm = TRUE) > 0) {
      km_D_s <- survfit(
        Surv(tstart_yr, tstop_yr, STORAGE_EVT) ~ .stratum,
        data = risk_s_D
      )
      export_km_fit(km_D_s, paste0("04b_KM_storage_by_", file_prefix), paste0("storage_by_", file_prefix))

      p_D_s <- ggsurvplot(
        km_D_s,
        data = risk_s_D,
        conf.int = FALSE,
        pval = FALSE,
        risk.table = FALSE,
        xlab = "Years since start of record",
        ylab = "Probability active place has not yet become storage",
        title = paste("Active places becoming storage by", stratum_label, "[", plot_scope, "]"),
        legend.title = legend_label
      )

      safe_plot_save(p_D_s$plot, paste0("04b_KM_storage_by_", file_prefix, ".png"), width = 9, height = 6)
    } else {
      message("[KM] Skipped storage stratification by ", stratum_label,
              "; rows = ", nrow(risk_s_D),
              "; levels = ", nlev_D,
              "; events = ", sum(risk_s_D$STORAGE_EVT == 1, na.rm = TRUE))
    }

    if (nlev_S > 1 && nlev_S <= 12 && sum(risk_s_S$STABILISE_EVT == 1, na.rm = TRUE) > 0) {
      km_S_s <- survfit(
        Surv(tstart_yr, tstop_yr, STABILISE_EVT) ~ .stratum,
        data = risk_s_S
      )
      export_km_fit(km_S_s, paste0("04c_KM_stabilisation_by_", file_prefix), paste0("stabilisation_by_", file_prefix))

      p_S_s <- ggsurvplot(
        km_S_s,
        data = risk_s_S,
        conf.int = FALSE,
        pval = FALSE,
        risk.table = FALSE,
        xlab = "Years since start of record",
        ylab = "Probability storage has not yet become stable floodplain",
        title = paste("Depositional storage becoming stable floodplain by", stratum_label, "[", plot_scope, "]"),
        legend.title = legend_label
      )

      safe_plot_save(p_S_s$plot, paste0("04c_KM_stabilisation_by_", file_prefix, ".png"), width = 9, height = 6)
    } else {
      message("[KM] Skipped stabilisation stratification by ", stratum_label,
              "; rows = ", nrow(risk_s_S),
              "; levels = ", nlev_S,
              "; events = ", sum(risk_s_S$STABILISE_EVT == 1, na.rm = TRUE))
    }

    if (isTRUE(RunStorageReworkInterpretive)) {
      if (nlev_RW > 1 && nlev_RW <= 12 && sum(risk_s_RW$STORAGE_REWORK_EVT == 1, na.rm = TRUE) > 0) {
        km_RW_s <- survfit(
          Surv(tstart_yr, tstop_yr, STORAGE_REWORK_EVT) ~ .stratum,
          data = risk_s_RW
        )
        export_km_fit(km_RW_s, paste0("04d_KM_storage_reworking_by_", file_prefix), paste0("storage_reworking_by_", file_prefix))
        p_RW_s <- ggsurvplot(
          km_RW_s,
          data = risk_s_RW,
          conf.int = FALSE,
          pval = FALSE,
          risk.table = FALSE,
          xlab = "Years since start of record",
          ylab = "Probability storage has not yet returned to the Active Domain",
          title = paste("Depositional storage reworking by", stratum_label, "[", plot_scope, "]"),
          legend.title = legend_label
        )
        safe_plot_save(p_RW_s$plot, paste0("04d_KM_storage_reworking_by_", file_prefix, ".png"), width = 9, height = 6)
      } else {
        message("[KM] Skipped storage-reworking stratification by ", stratum_label,
                "; rows = ", nrow(risk_s_RW),
                "; levels = ", nlev_RW,
                "; events = ", sum(risk_s_RW$STORAGE_REWORK_EVT == 1, na.rm = TRUE))
      }
    }
  }

  km_bin_qa <- bind_rows(km_bin_qa_rows)
  write_if_nonempty(km_bin_qa, "04_spatial_bin_risk_event_counts.csv")
}

# -----------------------------
# [FRAF archive / workflow]
# Counting-process branch: retain repeated PLACE intervals with tstart/tstop
# elapsed exposure and correct transition-specific eligibility for AG modelling.
# [FRAF archive / code note]
# The AG formulation represents repeated event/exposure rows with interval
# start-stop time; do not collapse them into one row per PLACE.
# 3. AG / interval hazard table
# -----------------------------

if (RunAG) {

  ag_interval <- risk_valid %>%
    group_by(tstart_yr, tstop_yr) %>%
    summarise(
      n_union_risk = n(),
      n_reactivate_risk = sum(REACTIVATE_RISK_SET == 1, na.rm = TRUE),
      n_base_reactivate_risk = sum(BASE_REACTIVATE_RISK_SET_DERIVED == 1, na.rm = TRUE),
      n_storage_risk = sum(STORAGE_RISK_SET == 1, na.rm = TRUE),
      n_stabilise_risk = sum(STABILISE_RISK_SET == 1, na.rm = TRUE),
      n_storage_rework_risk = sum(STORAGE_REWORK_RISK_SET == 1, na.rm = TRUE),
      n_any_risk = sum(ANY_STATE_RISK_SET == 1, na.rm = TRUE),
      n_reactivate = sum(REACTIVATE_EVT == 1, na.rm = TRUE),
      n_base_reactivate = sum(BASE_REACTIVATE_EVT == 1, na.rm = TRUE),
      n_storage = sum(STORAGE_EVT == 1, na.rm = TRUE),
      n_stabilise = sum(STABILISE_EVT == 1, na.rm = TRUE),
      n_storage_rework = sum(STORAGE_REWORK_EVT == 1, na.rm = TRUE),
      n_any_event = sum(ANY_CONFIRMED_EVT == 1, na.rm = TRUE),
      area_block_reactivate = sum(A_block[REACTIVATE_RISK_SET == 1], na.rm = TRUE),
      area_block_storage = sum(A_block[STORAGE_RISK_SET == 1], na.rm = TRUE),
      area_erosion = sum(A_E[REACTIVATE_RISK_SET == 1], na.rm = TRUE),
      area_deposition = sum(A_D[STORAGE_RISK_SET == 1], na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(
      hazard_REACTIVATE = ifelse(n_reactivate_risk > 0, n_reactivate / n_reactivate_risk, NA_real_),
      hazard_BASE_REACTIVATE = ifelse(n_base_reactivate_risk > 0, n_base_reactivate / n_base_reactivate_risk, NA_real_),
      hazard_STORAGE = ifelse(n_storage_risk > 0, n_storage / n_storage_risk, NA_real_),
      hazard_STABILISE = ifelse(n_stabilise_risk > 0, n_stabilise / n_stabilise_risk, NA_real_),
      hazard_STORAGE_REWORK = ifelse(n_storage_rework_risk > 0, n_storage_rework / n_storage_rework_risk, NA_real_),
      hazard_ANY = ifelse(n_any_risk > 0, n_any_event / n_any_risk, NA_real_),
      area_rate_E = ifelse(area_block_reactivate > 0, area_erosion / area_block_reactivate, NA_real_),
      area_rate_D = ifelse(area_block_storage > 0, area_deposition / area_block_storage, NA_real_),
      net_area_balance = area_deposition - area_erosion
    )

  write_csv(
    ag_interval,
    file.path(out_dir, "03_AG_interval_hazard_table.csv")
  )

  p_hazard <- ag_interval %>%
    pivot_longer(
      cols = c(hazard_REACTIVATE, hazard_BASE_REACTIVATE, hazard_STORAGE, hazard_STABILISE, hazard_STORAGE_REWORK, hazard_ANY),
      names_to = "process",
      values_to = "hazard"
    ) %>%
    mutate(process = recode(process,
      hazard_REACTIVATE = "Reached by Active Domain",
      hazard_BASE_REACTIVATE = "Initial floodplain reached by Active Domain",
      hazard_STORAGE = "Depositional storage",
      hazard_STABILISE = "Storage became stable floodplain",
      hazard_STORAGE_REWORK = "Depositional storage reworked to Active Domain",
      hazard_ANY = "Any named primary transition"
    )) %>%
    ggplot(aes(x = tstop_yr, y = hazard, group = process, linetype = process)) +
    geom_line(linewidth = 0.8) +
    geom_point(size = 1.8) +
    labs(
      x = "Interval end year",
      y = "Interval event probability",
      title = "Interval probability of primary ambiguity-bridged changes"
    ) +
    theme_minimal()

  safe_plot_save(p_hazard, "03_AG_interval_hazard.png", width = 8, height = 5)

  p_area <- ag_interval %>%
    pivot_longer(
      cols = c(area_rate_E, area_rate_D),
      names_to = "process",
      values_to = "area_rate"
    ) %>%
    mutate(process = recode(process,
      area_rate_E = "Area reached by Active Domain",
      area_rate_D = "Area becoming storage"
    )) %>%
    ggplot(aes(x = tstop_yr, y = area_rate, group = process, linetype = process)) +
    geom_line(linewidth = 0.8) +
    geom_point(size = 1.8) +
    labs(
      x = "Interval end year",
      y = "Area fraction of transition-specific risk set",
      title = "Interval area rate: Active Domain reach and storage formation"
    ) +
    theme_minimal()

  safe_plot_save(p_area, "03b_AG_interval_area_rate.png", width = 8, height = 5)

  ag_interval_pure <- risk_any_pure %>%
    group_by(tstart_yr, tstop_yr) %>%
    summarise(
      n_union_risk = n(),
      n_reactivate_risk = sum(REACTIVATE_RISK_SET == 1, na.rm = TRUE),
      n_storage_risk = sum(STORAGE_RISK_SET == 1, na.rm = TRUE),
      n_stabilise_risk = sum(STABILISE_RISK_SET == 1, na.rm = TRUE),
      n_storage_rework_risk = sum(STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1, na.rm = TRUE),
      n_any_risk = sum(ANY_STATE_RISK_SET == 1, na.rm = TRUE),
      n_reactivate = sum(REACTIVATE_TRANS == 1, na.rm = TRUE),
      n_storage = sum(STORAGE_TRANS == 1, na.rm = TRUE),
      n_stabilise = sum(STABILISE_TRANS == 1, na.rm = TRUE),
      n_storage_rework = sum(STORAGE_REWORK_TRANS == 1, na.rm = TRUE),
      n_any_event = sum(ANY_STATE_EVT == 1, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(
      hazard_REACTIVATE = ifelse(n_reactivate_risk > 0, n_reactivate / n_reactivate_risk, NA_real_),
      hazard_STORAGE = ifelse(n_storage_risk > 0, n_storage / n_storage_risk, NA_real_),
      hazard_STABILISE = ifelse(n_stabilise_risk > 0, n_stabilise / n_stabilise_risk, NA_real_),
      hazard_STORAGE_REWORK = ifelse(n_storage_rework_risk > 0, n_storage_rework / n_storage_rework_risk, NA_real_),
      hazard_ANY = ifelse(n_any_risk > 0, n_any_event / n_any_risk, NA_real_)
    )

  write_csv(ag_interval_pure, file.path(out_dir, "03p_AG_state_only_interval_hazard_table.csv"))

  p_hazard_pure <- ag_interval_pure %>%
    pivot_longer(
      cols = c(hazard_REACTIVATE, hazard_STORAGE, hazard_STABILISE, hazard_STORAGE_REWORK, hazard_ANY),
      names_to = "process",
      values_to = "hazard"
    ) %>%
    mutate(process = recode(process,
      hazard_REACTIVATE = "Stable floodplain reached by Active Domain",
      hazard_STORAGE = "Active place became depositional storage",
      hazard_STABILISE = "Depositional storage became stable floodplain",
      hazard_STORAGE_REWORK = "Depositional storage reworked to Active Domain",
      hazard_ANY = "Any state transition"
    )) %>%
    ggplot(aes(x = tstop_yr, y = hazard, group = process, linetype = process)) +
    geom_line(linewidth = 0.8) +
    geom_point(size = 1.8) +
    labs(
      x = "Interval end year",
      y = "Interval state-transition probability",
      title = "State-only interval transition probability"
    ) +
    theme_minimal()

  safe_plot_save(p_hazard_pure, "03p_AG_state_only_interval_hazard.png", width = 8, height = 5)


  # Publication-style AG hazard-through-time figures.
  # These are additional outputs; the original AG plots above are retained.
  ag_hazard_long <- ag_interval %>%
    pivot_longer(
      cols = any_of(c(
        "hazard_REACTIVATE",
        "hazard_BASE_REACTIVATE",
        "hazard_STORAGE",
        "hazard_STABILISE",
        "hazard_STORAGE_REWORK",
        "hazard_ANY"
      )),
      names_to = "transition",
      values_to = "hazard"
    ) %>%
    mutate(
      transition = case_when(
        transition == "hazard_REACTIVATE" ~ "Floodplain reached by Active Domain",
        transition == "hazard_BASE_REACTIVATE" ~ "Initial floodplain reached by Active Domain",
        transition == "hazard_STORAGE" ~ "Active place became depositional storage",
        transition == "hazard_STABILISE" ~ "Depositional storage became stable floodplain",
        transition == "hazard_STORAGE_REWORK" ~ "Depositional storage reworked to Active Domain",
        transition == "hazard_ANY" ~ "Any named primary transition",
        TRUE ~ transition
      )
    )

  write_csv(
    ag_hazard_long,
    file.path(out_dir, "03_AG_hazard_through_time_long.csv")
  )

  p_ag_hazard_time <- ag_hazard_long %>%
    filter(!is.na(hazard)) %>%
    ggplot(aes(x = tstop_yr, y = hazard, colour = transition, group = transition)) +
    geom_line(linewidth = 0.9) +
    geom_point(size = 1.8) +
    labs(
      title = "AG interval hazards through time",
      x = "Interval end year",
      y = "Interval event probability",
      colour = "Transition/event"
    ) +
    theme_bw(base_size = 14) +
    theme(
      panel.grid.minor = element_blank(),
      plot.title = element_text(face = "bold", hjust = 0.5),
      legend.position = "right"
    )

  safe_plot_save(
    p_ag_hazard_time,
    "03_AG_hazard_through_time.png",
    width = 10,
    height = 5.8
  )

  ag_hazard_pure_long <- ag_interval_pure %>%
    pivot_longer(
      cols = any_of(c(
        "hazard_REACTIVATE",
        "hazard_STORAGE",
        "hazard_STABILISE",
        "hazard_STORAGE_REWORK",
        "hazard_ANY"
      )),
      names_to = "transition",
      values_to = "hazard"
    ) %>%
    mutate(
      transition = case_when(
        transition == "hazard_REACTIVATE" ~ "Stable floodplain reached by Active Domain",
        transition == "hazard_STORAGE" ~ "Active place became depositional storage",
        transition == "hazard_STABILISE" ~ "Depositional storage became stable floodplain",
        transition == "hazard_STORAGE_REWORK" ~ "Depositional storage reworked to Active Domain",
        transition == "hazard_ANY" ~ "Any state transition",
        TRUE ~ transition
      )
    )

  write_csv(
    ag_hazard_pure_long,
    file.path(out_dir, "03p_AG_state_only_hazard_through_time_long.csv")
  )

  p_ag_hazard_pure_time <- ag_hazard_pure_long %>%
    filter(!is.na(hazard)) %>%
    ggplot(aes(x = tstop_yr, y = hazard, colour = transition, group = transition)) +
    geom_line(linewidth = 0.9) +
    geom_point(size = 1.8) +
    labs(
      title = "State-only transition probabilities through time",
      x = "Interval end year",
      y = "Interval state-transition probability",
      colour = "State transition"
    ) +
    theme_bw(base_size = 14) +
    theme(
      panel.grid.minor = element_blank(),
      plot.title = element_text(face = "bold", hjust = 0.5),
      legend.position = "right"
    )

  safe_plot_save(
    p_ag_hazard_pure_time,
    "03p_AG_state_only_hazard_through_time.png",
    width = 10,
    height = 5.8
  )
}

# -----------------------------
# [FRAF archive / workflow]
# Historical explanatory Cox branch: source events and risk sets from Stage 4;
# fit transition-specific hazards with ONLY antecedent, interval-start predictors.
# [FRAF archive / code note]
# Explanatory modelling is not a second source of event classifications:
# the risk-table eligibility/event columns remain authoritative.
# 4. Cox models: interval-specific, no-leakage ASM_PREV covariates
# -----------------------------

if (RunCox) {

  message("[Cox] Preparing counting-process Cox data")

  # v17.10.14.4: the broad Eligible Floodplain -> AD model has a dedicated
  # Stage 4 v6.7 eligibility definition because guarded PREEXISTING_FLOODPLAIN
  # rows may intentionally have no recognised three-state T1 endpoint.  Build a
  # unified Cox source frame containing (a) the ordinary eligible state-transition
  # frame and (b) authoritative broad-FP rows that are both at risk and broad-model
  # eligible. Transition-specific filters below still isolate every fitted model.
  cox_source <- risk %>%
    filter(
      (M3_MODEL_ELIGIBLE_PRIMARY == 1L & ANY_STATE_RISK_SET == 1L) |
        (FP_REACTIVATE_RISK_SET == 1L & FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L)
    )

  cox_data <- cox_source %>%
    mutate(
      PLACE_ID = as.character(PLACE_ID),
      BLOCK_ID = as.character(BLOCK_ID),
      FP_REACTIVATE_EVT = as.integer(FP_REACTIVATE_EVT),
      FP_REACTIVATE_RISK_SET = as.integer(FP_REACTIVATE_RISK_SET),
      REACTIVATE_EVT = as.integer(REACTIVATE_EVT),
      STORAGE_EVT = as.integer(STORAGE_EVT),
      STABILISE_EVT = as.integer(STABILISE_EVT),
      STORAGE_REWORK_EVT = as.integer(STORAGE_REWORK_EVT),
      ANY_CONFIRMED_EVT = as.integer(ANY_CONFIRMED_EVT),
      REACTIVATE_TRANS = as.integer(REACTIVATE_TRANS),
      STORAGE_TRANS = as.integer(STORAGE_TRANS),
      STABILISE_TRANS = as.integer(STABILISE_TRANS),
      STORAGE_REWORK_TRANS = as.integer(STORAGE_REWORK_TRANS),
      ANY_STATE_EVT = as.integer(ANY_STATE_EVT),
      ANY_ONTO_EVT = as.integer(ANY_ONTO_EVT),
      REACTIVATE_EVT_PURE = as.integer(REACTIVATE_EVT_PURE),
      STORAGE_EVT_PURE = as.integer(STORAGE_EVT_PURE),
      STABILISE_EVT_PURE = as.integer(STABILISE_EVT_PURE),
      ANY_ONTO_EVT_PURE = as.integer(ANY_ONTO_EVT_PURE),
      E_evt = as.integer(E_evt),
      D_evt = as.integer(D_evt),
      ANY_EVT = as.integer(ANY_EVT),
      at_risk = as.integer(at_risk),
      REACTIVATE_RISK_SET = as.integer(REACTIVATE_RISK_SET),
      BASE_REACTIVATE_RISK_SET_DERIVED = as.integer(BASE_REACTIVATE_RISK_SET_DERIVED),
      BASE_REACTIVATE_EVT = as.integer(BASE_REACTIVATE_EVT),
      INIT_FP_COHORT = as.integer(INIT_FP_COHORT),
      STORAGE_RISK_SET = as.integer(STORAGE_RISK_SET),
      STABILISE_RISK_SET = as.integer(STABILISE_RISK_SET),
      STORAGE_REWORK_RISK_SET = as.integer(STORAGE_REWORK_RISK_SET),
      STORAGE_REWORK_RISK_SET_STRICT_AUDIT = as.integer(STORAGE_REWORK_RISK_SET_STRICT_AUDIT),
      ANY_STATE_RISK_SET = as.integer(ANY_STATE_RISK_SET),
      E_RISK_SET = as.integer(E_RISK_SET),
      D_RISK_SET = as.integer(D_RISK_SET),
      RISK_SET = as.integer(RISK_SET),
      tstart_yr = as.numeric(tstart_yr),
      tstop_yr = as.numeric(tstop_yr),
      duration = tstop_yr - tstart_yr,
      interval_id = as.factor(round(tstop_yr, 6)),
      event_class = as.character(EVENT_STATE)
    ) %>%
    filter(
      !is.na(tstart_yr),
      !is.na(tstop_yr),
      tstop_yr > tstart_yr,
      (
        (
          ANY_STATE_RISK_SET == 1L &
            !is.na(REACTIVATE_EVT) &
            !is.na(STORAGE_EVT) &
            !is.na(STABILISE_EVT) &
            !is.na(STORAGE_REWORK_EVT) &
            !is.na(ANY_CONFIRMED_EVT) &
            !is.na(REACTIVATE_TRANS) &
            !is.na(STORAGE_TRANS) &
            !is.na(STABILISE_TRANS) &
            !is.na(STORAGE_REWORK_TRANS) &
            !is.na(ANY_STATE_EVT)
        ) |
        (
          FP_REACTIVATE_RISK_SET == 1L &
            FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L &
            !is.na(FP_REACTIVATE_EVT)
        )
      )
    ) %>%
    left_join(
      temporal_spatial_model_lookup,
      by = c("PLACE_ID", "tstart_yr", "tstop_yr")
    )

  numeric_fields <- c(
    "ASM_N_EVENTS_PREV",
    "ASM_N_ACTIVE_DOMAIN_PREV",
    "ASM_N_STORAGE_PREV",
    "ASM_N_STAB_FP_PREV",
    "ASM_N_REACTIVATE_PREV",
    "ASM_N_STORAGE_EVT_PREV",
    "ASM_N_STABILISE_PREV",
    "ASM_DIST_FREQ_PREV",
    "ASM_STORAGE_FRAC_PREV",
    "ASM_STAB_FP_FRAC_PREV",
    "ASM_LAST_ACTIVE_STEP_PREV",
    "ASM_QUIET_SINCE_PREV",
    "ASM_N_EPISODES_PREV",
    "ASM_MAX_QUIET_PREV",
    "ASM_DOM_RATIO_PREV",
    "ASM_NET_BAL_PREV",
    "ASM_COV_FRAC",
    "DIST_ACTIVE_CURR",
    "DIST_WATER_CURR",
    "DIST_CL_REF",
    "DIST_CL_CURR",
    "CURV_CL_CURR",
    "CURV_EROSION_CURR",
    "DIST_X_CURV_EROSION",

    # Stage 4 Step 3 v6.6 explicit interval-start Mamoré geometry.
    "GEOM_YMD_PREV",
    "GEOM_YEAR_PREV",
    "DIST_CHANNEL_PREV",
    "DIST_BANK_PREV",
    "BANK_SETBACK_PREV",
    "INSIDE_CHANNEL_PREV",
    "DIST_CL_PREV",
    "CL_MEASURE_PREV",
    "CURV_SIGNED_PREV",
    "CURV_ABS_PREV",
    "CURV_SCALED_PREV",
    "OUTER_BANK_PREV",
    "INNER_BANK_PREV",
    "LOCAL_HALF_WIDTH_PREV",
    "LOCAL_WIDTH_PREV",
    "REL_CHANNEL_POS_PREV",
    "NEAR_CHANNEL_HALF_PREV",
    "NEAR_CHANNEL_FULL_PREV",
    "NEAR_BANK_HALF_PREV",
    "NEAR_BANK_FULL_PREV",
    "OUTER_CURV_REACT_HALF_PREV",
    "OUTER_CURV_REACT_FULL_PREV",
    "INNER_CURV_STORAGE_HALF_PREV",
    "INNER_CURV_STORAGE_FULL_PREV",
    "OUTER_CURV_STORAGE_HALF_PREV",
    "OUTER_CURV_STORAGE_FULL_PREV",
    "GEOM_SUPPORT_PREV",
    # Legacy fields retained for older risk tables:
    "ASM_N_EROSION_PREV",
    "ASM_N_DEPOSITION_PREV",
    "ASM_ACTIVE_PREV",
    "ASM_EVER_ERODED_PREV",
    "ASM_EVER_DEPOSITED_PREV",
    "DIST_ACTIVE_PREV",
    "DIST_WATER_PREV",
    "DIST_CL_PREV",
    "DIST_CL_INIT",
    "DIST_CL_MEAN"
  )

  numeric_fields <- unique(c(
    numeric_fields,
    grep("(_Y0$|_APPROACH_M_PER_YR$)", names(cox_data), value = TRUE)
  ))
  for (nm in intersect(numeric_fields, names(cox_data))) {
    cox_data[[nm]] <- suppressWarnings(as.numeric(cox_data[[nm]]))
  }

  # Log-distance transformations reduce leverage from distant cells.
  log_distance_fields <- c(
    "DIST_ACTIVE_CURR",
    "DIST_WATER_CURR",
    "DIST_CL_REF",
    "DIST_CL_CURR",
    "DIST_ACTIVE_PREV",
    "DIST_WATER_PREV",
    "DIST_CL_PREV",
    "DIST_CL_INIT",
    "DIST_CL_MEAN",
    "DIST_CHANNEL_PREV",
    "DIST_BANK_PREV",
    "BANK_SETBACK_PREV"
  )
  for (nm in log_distance_fields) {
    cox_data <- add_logkm_if_exists(cox_data, nm)
    cox_data <- add_z_if_exists(cox_data, paste0(nm, "_LOGKM"))
  }

  # v17.10.15.1: explicit linear margin terms used by the selected Jamuna
  # SF->AD/DS->AD and Mamore DS->AD specifications.
  cox_data <- add_z_if_exists(cox_data, "DIST_ACTIVE_CURR", "DIST_ACTIVE_CURR_LINEAR_Z")
  cox_data <- add_z_if_exists(cox_data, "DIST_CHANNEL_PREV", "DIST_CHANNEL_PREV_LINEAR_Z")

  # ----------------------------------------------------------
  # Canonical local Mamoré exposure fields.
  # Full-width is the primary setting; the QGIS selection can switch to the
  # half-width sensitivity definition without changing model term names.
  # Curvature magnitudes are zero outside their process-specific exposure
  # support, while explicit binary indicators distinguish exposure from a
  # genuinely straight/low-curvature bank.
  # ----------------------------------------------------------
  mamore_react_use_half <- exists("MamoreReactivationExposure") &&
    !is.null(MamoreReactivationExposure) &&
    suppressWarnings(as.integer(MamoreReactivationExposure)) == 1L
  mamore_storage_use_full <- exists("MamoreStorageExposure") &&
    !is.null(MamoreStorageExposure) &&
    suppressWarnings(as.integer(MamoreStorageExposure)) == 1L

  react_near_field <- if (mamore_react_use_half) "NEAR_CHANNEL_HALF_PREV" else "NEAR_CHANNEL_FULL_PREV"
  react_curv_field <- if (mamore_react_use_half) "OUTER_CURV_REACT_HALF_PREV" else "OUTER_CURV_REACT_FULL_PREV"
  storage_near_field <- if (mamore_storage_use_full) "NEAR_BANK_FULL_PREV" else "NEAR_BANK_HALF_PREV"
  storage_inner_curv_field <- if (mamore_storage_use_full) "INNER_CURV_STORAGE_FULL_PREV" else "INNER_CURV_STORAGE_HALF_PREV"
  storage_outer_curv_field <- if (mamore_storage_use_full) "OUTER_CURV_STORAGE_FULL_PREV" else "OUTER_CURV_STORAGE_HALF_PREV"

  # [FRAF archive / Historic/QA function: get_numeric_or_na]
  # Read a requested numeric predictor or safely return missing values if unavailable.
  get_numeric_or_na <- function(dat, field) {
    if (!field %in% names(dat)) return(rep(NA_real_, nrow(dat)))
    suppressWarnings(as.numeric(dat[[field]]))
  }

  # [FRAF archive / Historic/QA function: indicator01]
  # Normalise a model covariate to an explicit binary indicator.
  indicator01 <- function(x) {
    x <- as.logical(x)
    x[is.na(x)] <- FALSE
    as.integer(x)
  }

  cox_data$MAM_NEAR_CHANNEL_PREV <- get_numeric_or_na(cox_data, react_near_field)
  cox_data$MAM_OUTER_REACT_EXPOSED_PREV <- indicator01(
    get_numeric_or_na(cox_data, "INSIDE_CHANNEL_PREV") == 0 &
      get_numeric_or_na(cox_data, "OUTER_BANK_PREV") == 1 &
      get_numeric_or_na(cox_data, react_near_field) == 1
  )
  cox_data$MAM_OUTER_CURV_REACT_PREV <- get_numeric_or_na(cox_data, react_curv_field)

  cox_data$MAM_NEAR_BANK_STORAGE_PREV <- get_numeric_or_na(cox_data, storage_near_field)
  cox_data$MAM_INNER_STORAGE_EXPOSED_PREV <- indicator01(
    get_numeric_or_na(cox_data, "INSIDE_CHANNEL_PREV") == 1 &
      get_numeric_or_na(cox_data, "INNER_BANK_PREV") == 1 &
      get_numeric_or_na(cox_data, storage_near_field) == 1
  )
  cox_data$MAM_OUTER_STORAGE_EXPOSED_PREV <- indicator01(
    get_numeric_or_na(cox_data, "INSIDE_CHANNEL_PREV") == 1 &
      get_numeric_or_na(cox_data, "OUTER_BANK_PREV") == 1 &
      get_numeric_or_na(cox_data, storage_near_field) == 1
  )
  cox_data$MAM_INNER_CURV_STORAGE_PREV <- get_numeric_or_na(cox_data, storage_inner_curv_field)
  cox_data$MAM_OUTER_CURV_STORAGE_PREV <- get_numeric_or_na(cox_data, storage_outer_curv_field)

  if (!identical(reach_label, "Jamuna")) {
    message(
      "[Cox] Mamor\u00e9 local exposure definition: ",
      ifelse(mamore_react_use_half, "half-width", "full-width"),
      "; reactivation field=", react_near_field,
      "; storage zone=", ifelse(mamore_storage_use_full, "full-width", "half-width"),
      "; storage bank field=", storage_near_field
    )
  }

  z_fields <- c(
    "ASM_DIST_FREQ_PREV",
    "ASM_STORAGE_FRAC_PREV",
    "ASM_STAB_FP_FRAC_PREV",
    "ASM_DOM_RATIO_PREV",
    "ASM_NET_BAL_PREV",
    "ASM_N_EPISODES_PREV",
    "ASM_MAX_QUIET_PREV",
    "ASM_QUIET_SINCE_PREV",
    "ASM_COV_FRAC",
    "ASM_N_REACTIVATE_PREV",
    "ASM_N_STORAGE_EVT_PREV",
    "ASM_N_STABILISE_PREV",
    "CURV_CL_CURR",
    "CURV_EROSION_CURR",
    "DIST_X_CURV_EROSION",
    "REL_CHANNEL_POS_PREV",
    "CURV_ABS_PREV",
    "CURV_SCALED_PREV",
    "MAM_OUTER_CURV_REACT_PREV",
    "MAM_INNER_CURV_STORAGE_PREV",
    "MAM_OUTER_CURV_STORAGE_PREV"
  )
  for (nm in z_fields) {
    cox_data <- add_z_if_exists(cox_data, nm)
  }

  # Categorical histories are exported but not included in the primary model
  # when equivalent continuous history metrics are available.
  cox_data <- factor_if_reasonable(cox_data, "ASM_STATE_PREV", max_levels = 10)
  cox_data <- factor_if_reasonable(cox_data, "ASM_STRUCTURE_CL_PREV", max_levels = 10)
  cox_data <- factor_if_reasonable(cox_data, "DIST_CL_CURR_BIN", max_levels = 10)
  cox_data <- factor_if_reasonable(cox_data, "DIST_ACTIVE_CURR_BIN", max_levels = 10)
  cox_data <- factor_if_reasonable(cox_data, "DIST_WATER_CURR_BIN", max_levels = 10)
  cox_data <- factor_if_reasonable(cox_data, "BANK_SIDE_PREV", max_levels = 6)
  cox_data <- factor_if_reasonable(cox_data, "POINT_SIDE_PREV", max_levels = 6)

  # [FRAF archive / Historic/QA function: has_numeric_variation]
  # Verify that a candidate model term has enough variation for estimation.
  has_numeric_variation <- function(dat, field) {
    if (!field %in% names(dat)) return(FALSE)
    x <- suppressWarnings(as.numeric(dat[[field]]))
    x <- x[is.finite(x)]
    length(x) > 1 && stats::sd(x) > 0
  }

  # Select transition-specific spatial frameworks.  The explicit Mamoré
  # geometry fields take precedence.  Curvature is not extended across the
  # corridor and unrestricted centreline distance is not used to modulate it.
  required_local_geom_fields <- c(
    "GEOM_SUPPORT_PREV", "DIST_CHANNEL_PREV", "INSIDE_CHANNEL_PREV",
    "MAM_NEAR_CHANNEL_PREV", "MAM_OUTER_CURV_REACT_PREV_Z",
    "REL_CHANNEL_POS_PREV_Z", "MAM_INNER_CURV_STORAGE_PREV_Z"
  )
  has_local_geom_support <- (
    all(required_local_geom_fields %in% names(cox_data)) &&
      any(suppressWarnings(as.numeric(cox_data$GEOM_SUPPORT_PREV)) == 1, na.rm = TRUE)
  )
  # Once the explicit Stage 4 Step 3 geometry fields are present, retain the local
  # framework even when an individual candidate has little variation.
  # keep_varying() removes unsupported terms within each risk set; the script
  # never reverts to the legacy corridor-wide distance x curvature model.
  use_local_mamore_geometry <- !identical(reach_label, "Jamuna") && has_local_geom_support

  if (use_local_mamore_geometry) {
    reactivation_spatial_candidates <- c(
      "MAM_NEAR_CHANNEL_PREV",
      "MAM_OUTER_REACT_EXPOSED_PREV",
      "MAM_OUTER_CURV_REACT_PREV_Z"
    )
    # [FRAF archive / code note]
    # Mamoré storage formation is analysed at two explicitly different scopes:
    # all supported events versus the lagged local-channel geometry subset.
    # Mamoré storage is deliberately split into two estimands:
    #   1. principal full-event model: assemblage history only;
    #   2. local-position subset: explicitly restricted to representative points
    #      inside the lagged channel with valid local geometry.
    storage_full_spatial_candidates <- character(0)
    storage_local_spatial_candidates <- c(
      "REL_CHANNEL_POS_PREV_Z",
      "MAM_NEAR_BANK_STORAGE_PREV",
      "MAM_INNER_STORAGE_EXPOSED_PREV",
      "MAM_INNER_CURV_STORAGE_PREV_Z",
      "MAM_OUTER_STORAGE_EXPOSED_PREV",
      "MAM_OUTER_CURV_STORAGE_PREV_Z"
    )
    stabilise_spatial_candidates <- c(
      "DIST_CHANNEL_PREV_LOGKM_Z"
    )
    storage_rework_spatial_candidates <- c(
      "DIST_CHANNEL_PREV_LINEAR_Z",
      if (isTRUE(mamore_dsad_use_curvature)) "MAM_OUTER_CURV_REACT_PREV_Z" else character(0)
    )
    any_spatial_candidates <- c(
      "MAM_NEAR_CHANNEL_PREV"
    )
    reactivation_spatial_framework <- "lagged_local_outer_bank_reactivation"
    storage_full_spatial_framework <- "full_event_assemblage_history_storage"
    storage_local_spatial_framework <- "lagged_within_channel_position_subset"
    stabilise_spatial_framework <- "lagged_channel_margin_stabilisation"
    storage_rework_spatial_framework <- if (isTRUE(mamore_dsad_use_curvature)) {
      "linear_previous_channel_margin_plus_curvature_storage_reworking"
    } else {
      "linear_previous_channel_margin_storage_reworking"
    }
    any_spatial_framework <- "lagged_near_channel_summary"
  } else {
    # Braided-reach and backwards-compatible fallbacks. Jamuna retains its
    # full-event spatial storage model and does not create a Mamoré local subset.
    if (has_numeric_variation(cox_data, "DIST_ACTIVE_CURR_LOGKM_Z")) {
      fallback_spatial <- "DIST_ACTIVE_CURR_LOGKM_Z"
      fallback_framework <- "active_domain_braided"
    } else if (has_numeric_variation(cox_data, "DIST_CL_REF_LOGKM_Z")) {
      fallback_spatial <- "DIST_CL_REF_LOGKM_Z"
      fallback_framework <- "reference_centreline"
    } else if (has_numeric_variation(cox_data, "DIST_CL_CURR_LOGKM_Z")) {
      fallback_spatial <- "DIST_CL_CURR_LOGKM_Z"
      fallback_framework <- "dated_centreline_legacy"
    } else if (has_numeric_variation(cox_data, "DIST_WATER_CURR_LOGKM_Z")) {
      fallback_spatial <- "DIST_WATER_CURR_LOGKM_Z"
      fallback_framework <- "water_distance_fallback"
    } else {
      fallback_spatial <- character(0)
      fallback_framework <- "no_spatial_predictor"
    }
    jamuna_linear_active <- if (
      identical(reach_label, "Jamuna") &&
      has_numeric_variation(cox_data, "DIST_ACTIVE_CURR_LINEAR_Z")
    ) "DIST_ACTIVE_CURR_LINEAR_Z" else fallback_spatial
    reactivation_spatial_candidates <- jamuna_linear_active
    storage_full_spatial_candidates <- fallback_spatial
    storage_local_spatial_candidates <- character(0)
    stabilise_spatial_candidates <- fallback_spatial
    storage_rework_spatial_candidates <- jamuna_linear_active
    any_spatial_candidates <- fallback_spatial
    reactivation_spatial_framework <- if (
      identical(reach_label, "Jamuna") &&
      identical(jamuna_linear_active, "DIST_ACTIVE_CURR_LINEAR_Z")
    ) "linear_active_domain_margin" else fallback_framework
    storage_full_spatial_framework <- fallback_framework
    storage_local_spatial_framework <- "not_applicable_non_mamore"
    stabilise_spatial_framework <- fallback_framework
    storage_rework_spatial_framework <- if (
      identical(reach_label, "Jamuna") &&
      identical(jamuna_linear_active, "DIST_ACTIVE_CURR_LINEAR_Z")
    ) "linear_active_domain_margin_storage_reworking" else fallback_framework
    any_spatial_framework <- fallback_framework
  }

  # Backwards-compatible aliases now point to the principal full-event model.
  storage_spatial_candidates <- storage_full_spatial_candidates
  storage_spatial_framework <- storage_full_spatial_framework

  spatial_framework_table <- bind_rows(
    tibble(
      model = c("active_domain_reactivation", "initial_floodplain_reactivation"),
      model_scope = "full_risk_set",
      spatial_framework = reactivation_spatial_framework,
      spatial_terms = paste(reactivation_spatial_candidates, collapse = "; ")
    ),
    tibble(
      model = "depositional_storage_full_event",
      model_scope = "full_event",
      spatial_framework = storage_full_spatial_framework,
      spatial_terms = paste(storage_full_spatial_candidates, collapse = "; ")
    ),
    tibble(
      model = "depositional_storage_local_position_subset",
      model_scope = "local_geometry_subset",
      spatial_framework = storage_local_spatial_framework,
      spatial_terms = paste(storage_local_spatial_candidates, collapse = "; ")
    ),
    tibble(
      model = "floodplain_stabilisation",
      model_scope = "full_risk_set",
      spatial_framework = stabilise_spatial_framework,
      spatial_terms = paste(stabilise_spatial_candidates, collapse = "; ")
    ),
    tibble(
      model = "depositional_storage_reworking",
      model_scope = "full_risk_set",
      spatial_framework = storage_rework_spatial_framework,
      spatial_terms = paste(storage_rework_spatial_candidates, collapse = "; ")
    ),
    tibble(
      model = "any_named_primary_transition",
      model_scope = "full_risk_set",
      spatial_framework = any_spatial_framework,
      spatial_terms = paste(any_spatial_candidates, collapse = "; ")
    )
  )

  message("[Cox] Reactivation spatial framework: ", reactivation_spatial_framework,
          " | ", paste(reactivation_spatial_candidates, collapse = ", "))
  message("[Cox] Storage principal full-event framework: ", storage_full_spatial_framework,
          if (length(storage_full_spatial_candidates) > 0L) paste0(" | ", paste(storage_full_spatial_candidates, collapse = ", ")) else " | assemblage-history terms only")
  if (use_local_mamore_geometry) {
    message("[Cox] Storage local-position sensitivity framework: ", storage_local_spatial_framework,
            " | ", paste(storage_local_spatial_candidates, collapse = ", "))
  }
  message("[Cox] Stabilisation spatial framework: ", stabilise_spatial_framework,
          " | ", paste(stabilise_spatial_candidates, collapse = ", "))

  history_core <- c(
    "ASM_DOM_RATIO_PREV_Z",
    "ASM_N_EPISODES_PREV_Z",
    "ASM_MAX_QUIET_PREV_Z",
    "ASM_COV_FRAC_Z"
  )
  history_core_no_episodes <- setdiff(history_core, "ASM_N_EPISODES_PREV_Z")
  erosion_history_core <- if (identical(reach_label, "Jamuna")) history_core_no_episodes else history_core

  # v17.10.15.1: Step-3D-selected Mamore DS->AD reduced-history reference.
  # Do NOT reuse the generic Mamore history_core here: ASM_N_EPISODES_PREV_Z
  # and ASM_MAX_QUIET_PREV_Z were removed by reduced-model triage.
  mamore_storage_rework_history_core <- c(
    "ASM_DOM_RATIO_PREV_Z",
    "ASM_COV_FRAC_Z"
  )
  storage_rework_history_core <- if (identical(reach_label, "Jamuna")) {
    history_core_no_episodes
  } else {
    mamore_storage_rework_history_core
  }

  erosion_candidates <- c(
    reactivation_spatial_candidates,
    erosion_history_core,
    if (!identical(reach_label, "Jamuna")) "ASM_N_REACTIVATE_PREV_Z" else character(0)
  )
  deposition_history_candidates <- c(
    history_core,
    "ASM_STORAGE_FRAC_PREV_Z",
    "ASM_N_STORAGE_EVT_PREV_Z"
  )
  deposition_full_candidates <- c(
    storage_full_spatial_candidates,
    deposition_history_candidates
  )
  deposition_local_candidates <- if (use_local_mamore_geometry) {
    c(storage_local_spatial_candidates, deposition_history_candidates)
  } else {
    character(0)
  }
  stabilise_candidates <- c(
    stabilise_spatial_candidates,
    history_core,
    "ASM_STORAGE_FRAC_PREV_Z",
    "ASM_STAB_FP_FRAC_PREV_Z",
    "ASM_QUIET_SINCE_PREV_Z",
    "ASM_N_STABILISE_PREV_Z"
  )
  storage_rework_candidates <- c(
    storage_rework_spatial_candidates,
    storage_rework_history_core,
    "ASM_STORAGE_FRAC_PREV_Z",
    "ASM_QUIET_SINCE_PREV_Z",
    "ASM_N_STORAGE_EVT_PREV_Z"
  )
  any_candidates <- c(
    any_spatial_candidates,
    history_core,
    "ASM_DIST_FREQ_PREV_Z"
  )

  # v17.10.14.5: principal historical broad Eligible FP->AD Cox is spatial-only.
  # History terms remain available to the retained v17.10.14.4 diagnostic block,
  # but are not fitted jointly in the production broad Cox model because the
  # corrected population combines resolved SF with left-censored pre-existing FP.
  broad_reactivation_candidates <- c("DIST_ACTIVE_CURR_LOGKM_Z")
  broad_reactivation_diagnostic_candidates <- c(
    "DIST_ACTIVE_CURR_LOGKM_Z",
    "ASM_DOM_RATIO_PREV_Z",
    "ASM_N_EPISODES_PREV_Z",
    "ASM_MAX_QUIET_PREV_Z",
    "ASM_COV_FRAC_Z"
  )
  broad_reactivation_terms <- unique(broad_reactivation_candidates[broad_reactivation_candidates %in% names(cox_data)])
  erosion_terms <- unique(erosion_candidates[erosion_candidates %in% names(cox_data)])
  deposition_full_terms <- unique(deposition_full_candidates[deposition_full_candidates %in% names(cox_data)])
  deposition_local_terms <- unique(deposition_local_candidates[deposition_local_candidates %in% names(cox_data)])
  deposition_terms <- deposition_full_terms
  stabilise_terms <- unique(stabilise_candidates[stabilise_candidates %in% names(cox_data)])
  storage_rework_terms <- unique(storage_rework_candidates[storage_rework_candidates %in% names(cox_data)])
  any_terms <- unique(any_candidates[any_candidates %in% names(cox_data)])

  # Remove terms with no variation after applying each transition-specific
  # risk set. This avoids singular terms that vary globally but not within the
  # eligible start state.
  # [FRAF archive / Historic/QA function: keep_varying]
  # Retain model candidate terms supported by variation in the actual fitting data.
  keep_varying <- function(dat, terms) {
    keep <- character(0)
    for (tm in terms) {
      if (!tm %in% names(dat)) next
      x <- dat[[tm]]
      if (is.factor(x)) {
        if (n_distinct(na.omit(x)) > 1) keep <- c(keep, tm)
      } else {
        s <- suppressWarnings(stats::sd(as.numeric(x), na.rm = TRUE))
        if (is.finite(s) && s > 0) keep <- c(keep, tm)
      }
    }
    unique(keep)
  }

  # [FRAF archive / code note]
  # Sensitivity definitions condition on different observed support;
  # comparative coefficients must be interpreted alongside retention/QA counts.
  # ============================================================
  # STORAGE MODEL PREDICTOR-MISSINGNESS QA — FULLY STREAMED
  # ============================================================
  # Summary counts are accumulated one chunk at a time. No n-row x p matrix,
  # full-length missing-count vector, or full-length sequential mask is created.
  # Optional row-level excluded-event details are written incrementally and are
  # disabled by default for routine Jamuna/Mamoré model runs.

  storage_risk_index <- which(cox_data$STORAGE_RISK_SET == 1L)
  storage_qa_n <- length(storage_risk_index)

  storage_qa_candidate_terms <- if (use_local_mamore_geometry) {
    deposition_local_terms
  } else {
    deposition_full_terms
  }

  storage_qa_chunk_size <- 100000L
  storage_qa_starts <- if (storage_qa_n > 0L) {
    seq.int(1L, storage_qa_n, by = storage_qa_chunk_size)
  } else {
    integer(0)
  }

  # [FRAF archive / Historic/QA function: storage_term_varies]
  # Check whether a storage/retention covariate is estimable within the selected subpopulation.
  storage_term_varies <- function(field) {
    if (!field %in% names(cox_data) || storage_qa_n == 0L) return(FALSE)
    seen <- NULL
    for (st in storage_qa_starts) {
      en <- min(storage_qa_n, st + storage_qa_chunk_size - 1L)
      vals <- cox_data[[field]][storage_risk_index[st:en]]
      vals <- vals[!is.na(vals)]
      if (length(vals) == 0L) next
      seen <- unique(c(seen, head(unique(vals), 2L)))
      if (length(seen) >= 2L) return(TRUE)
    }
    FALSE
  }

  storage_qa_terms <- unique(storage_qa_candidate_terms[
    vapply(storage_qa_candidate_terms, storage_term_varies, logical(1))
  ])

  storage_qa_total_events <- if (storage_qa_n > 0L) {
    sum(cox_data$STORAGE_EVT[storage_risk_index] == 1L, na.rm = TRUE)
  } else 0L

  storage_qa_scope_label <- if (use_local_mamore_geometry) {
    "storage local-position candidate model"
  } else {
    "storage principal full-event model"
  }

  message(
    "[Storage QA] Primary storage risk rows/events before predictor filtering: ",
    storage_qa_n, "/", storage_qa_total_events
  )
  message(
    "[Storage QA] Terms audited for the ", storage_qa_scope_label, ": ",
    if (length(storage_qa_terms) > 0L) paste(storage_qa_terms, collapse = ", ") else "none"
  )

  if (length(storage_qa_terms) > 0L && storage_qa_n > 0L) {
    p <- length(storage_qa_terms)
    predictor_missing_rows <- integer(p)
    predictor_missing_events <- integer(p)
    predictor_only_rows <- integer(p)
    predictor_only_events <- integer(p)
    predictor_distinct <- integer(p)

    seq_rows_before <- integer(p)
    seq_events_before <- integer(p)
    seq_rows_lost <- integer(p)
    seq_events_lost <- integer(p)
    seq_rows_remaining <- integer(p)
    seq_events_remaining <- integer(p)

    complete_rows <- 0L
    complete_events <- 0L
    combination_counts <- integer(0)

    detail_path <- file.path(out_dir, "08_storage_excluded_event_details.csv")
    if (file.exists(detail_path)) unlink(detail_path, force = TRUE)
    detail_header_written <- FALSE

    storage_identifier_fields <- intersect(
      c("BLOCK_ID", "PLACE_ID", "y1", "y2", "tstart_yr", "tstop_yr", "GEOM_YMD", "GEOM_YMD_PREV"),
      names(cox_data)
    )

    for (st in storage_qa_starts) {
      en <- min(storage_qa_n, st + storage_qa_chunk_size - 1L)
      local_pos <- st:en
      global_pos <- storage_risk_index[local_pos]
      chunk_n <- length(global_pos)
      chunk_event <- cox_data$STORAGE_EVT[global_pos] == 1L
      chunk_event[is.na(chunk_event)] <- FALSE

      # One integer vector per chunk records the number of missing audited terms.
      miss_count <- integer(chunk_n)
      for (i in seq_along(storage_qa_terms)) {
        tm <- storage_qa_terms[[i]]
        vals <- cox_data[[tm]][global_pos]
        miss <- is.na(vals)
        predictor_missing_rows[i] <- predictor_missing_rows[i] + sum(miss)
        predictor_missing_events[i] <- predictor_missing_events[i] + sum(chunk_event & miss)
        miss_count <- miss_count + as.integer(miss)
        nonmiss <- vals[!miss]
        if (length(nonmiss) > 0L && predictor_distinct[i] < 2L) {
          predictor_distinct[i] <- min(2L, length(unique(nonmiss)))
        }
        rm(vals, miss, nonmiss)
      }

      # Unique attribution is computed within the same bounded chunk.
      for (i in seq_along(storage_qa_terms)) {
        tm <- storage_qa_terms[[i]]
        vals <- cox_data[[tm]][global_pos]
        only <- is.na(vals) & miss_count == 1L
        predictor_only_rows[i] <- predictor_only_rows[i] + sum(only)
        predictor_only_events[i] <- predictor_only_events[i] + sum(chunk_event & only)
        rm(vals, only)
      }

      # Sequential exclusion is likewise local to the chunk and accumulated.
      remaining <- rep(TRUE, chunk_n)
      for (i in seq_along(storage_qa_terms)) {
        tm <- storage_qa_terms[[i]]
        seq_rows_before[i] <- seq_rows_before[i] + sum(remaining)
        seq_events_before[i] <- seq_events_before[i] + sum(chunk_event & remaining)
        vals <- cox_data[[tm]][global_pos]
        lost <- remaining & is.na(vals)
        seq_rows_lost[i] <- seq_rows_lost[i] + sum(lost)
        seq_events_lost[i] <- seq_events_lost[i] + sum(chunk_event & lost)
        remaining[lost] <- FALSE
        seq_rows_remaining[i] <- seq_rows_remaining[i] + sum(remaining)
        seq_events_remaining[i] <- seq_events_remaining[i] + sum(chunk_event & remaining)
        rm(vals, lost)
      }

      complete_rows <- complete_rows + sum(miss_count == 0L)
      complete_events <- complete_events + sum(chunk_event & miss_count == 0L)

      # Row-level details are optional and streamed directly to disk.
      excluded_event_chunk <- which(chunk_event & miss_count > 0L)
      if (length(excluded_event_chunk) > 0L && WriteDetailedStorageAudit) {
        patterns <- rep("", length(excluded_event_chunk))
        excluded_global <- global_pos[excluded_event_chunk]
        for (tm in storage_qa_terms) {
          miss <- is.na(cox_data[[tm]][excluded_global])
          if (any(miss)) {
            patterns[miss] <- ifelse(patterns[miss] == "", tm, paste0(patterns[miss], "; ", tm))
          }
        }

        tab <- table(patterns, useNA = "no")
        for (nm in names(tab)) {
          combination_counts[nm] <- ifelse(is.na(combination_counts[nm]), 0L, combination_counts[nm]) + as.integer(tab[[nm]])
        }

        details <- cox_data[excluded_global, storage_identifier_fields, drop = FALSE]
        details$MISSING_PREDICTORS <- patterns
        utils::write.table(
          as.data.frame(details), file = detail_path, sep = ",", row.names = FALSE,
          col.names = !detail_header_written, append = detail_header_written,
          quote = TRUE, na = "", qmethod = "double", fileEncoding = "UTF-8"
        )
        detail_header_written <- TRUE
        rm(patterns, excluded_global, tab, details, miss)
      }

      rm(local_pos, global_pos, chunk_event, miss_count, remaining, excluded_event_chunk)
      invisible(gc(FALSE))
    }

    storage_predictor_missingness_qa <- tibble(
      predictor = storage_qa_terms,
      risk_rows_total = storage_qa_n,
      risk_rows_missing = predictor_missing_rows,
      risk_rows_missing_pct = 100 * predictor_missing_rows / storage_qa_n,
      events_total = storage_qa_total_events,
      events_missing = predictor_missing_events,
      events_missing_pct = if (storage_qa_total_events > 0L) 100 * predictor_missing_events / storage_qa_total_events else NA_real_,
      rows_missing_only_this_predictor = predictor_only_rows,
      events_missing_only_this_predictor = predictor_only_events,
      nonmissing_distinct_values = predictor_distinct,
      distinct_count_capped_at_2 = predictor_distinct >= 2L
    ) %>% arrange(desc(events_missing), desc(risk_rows_missing))

    storage_sequential_qa <- tibble(
      sequence = seq_along(storage_qa_terms),
      predictor = storage_qa_terms,
      rows_before = seq_rows_before,
      events_before = seq_events_before,
      rows_lost_at_step = seq_rows_lost,
      events_lost_at_step = seq_events_lost,
      rows_remaining = seq_rows_remaining,
      events_remaining = seq_events_remaining
    )

    if (length(combination_counts) > 0L) {
      storage_event_missing_combinations <- tibble(
        missing_predictor_combination = names(combination_counts),
        excluded_storage_events = as.integer(combination_counts)
      ) %>%
        arrange(desc(excluded_storage_events)) %>%
        mutate(excluded_event_pct = 100 * excluded_storage_events / sum(excluded_storage_events))
    } else {
      storage_event_missing_combinations <- tibble(
        missing_predictor_combination = character(0),
        excluded_storage_events = integer(0),
        excluded_event_pct = numeric(0)
      )
    }

    storage_initial_cc_summary <- tibble(
      definition = if (use_local_mamore_geometry) {
        "primary_storage_local_position_audit_before_iterative_term_pruning"
      } else {
        "primary_storage_full_event_audit_before_iterative_term_pruning"
      },
      audit_mode = ifelse(WriteDetailedStorageAudit, "summary_plus_streamed_event_details", "summary_only"),
      risk_rows = storage_qa_n,
      events = storage_qa_total_events,
      complete_case_rows_all_initial_varying_terms = complete_rows,
      complete_case_events_all_initial_varying_terms = complete_events,
      rows_excluded = storage_qa_n - complete_rows,
      events_excluded = storage_qa_total_events - complete_events
    )

    write_audit_csv(storage_predictor_missingness_qa, "08_storage_predictor_missingness_QA.csv")
    write_audit_csv(storage_sequential_qa, "08_storage_predictor_sequential_exclusion_QA.csv")
    write_audit_csv(storage_event_missing_combinations, "08_storage_event_missingness_combinations_QA.csv")
    write_audit_csv(storage_initial_cc_summary, "08_storage_initial_complete_case_summary_QA.csv")

    if (!WriteDetailedStorageAudit) {
      write_audit_csv(
        tibble(
          AUDIT_STATUS = "NOT_WRITTEN",
          NOTE = "Row-level excluded-event details disabled. Set WriteDetailedStorageAudit=TRUE for a dedicated diagnostic run."
        ),
        "08_storage_excluded_event_details.csv"
      )
    } else if (!detail_header_written) {
      write_audit_csv(
        tibble(
          AUDIT_STATUS = "NO_EXCLUDED_EVENTS",
          NOTE = "No storage events were excluded by missing audited predictors."
        ),
        "08_storage_excluded_event_details.csv"
      )
    }

    message(
      "[Storage QA] Rows/events complete for all audited candidate terms: ",
      complete_rows, "/", complete_events
    )
  } else {
    write_audit_csv(tibble(predictor = character(0)), "08_storage_predictor_missingness_QA.csv")
    write_audit_csv(tibble(sequence = integer(0), predictor = character(0)), "08_storage_predictor_sequential_exclusion_QA.csv")
    write_audit_csv(tibble(missing_predictor_combination = character(0), excluded_storage_events = integer(0)), "08_storage_event_missingness_combinations_QA.csv")
    write_audit_csv(
      tibble(AUDIT_STATUS = "NO_AUDITED_TERMS", NOTE = "No varying storage candidate terms were available."),
      "08_storage_excluded_event_details.csv"
    )
  }

  # Release all audit-only objects before constructing the six storage model
  # datasets. This is especially important for the 4-million-row Jamuna table.
  storage_audit_objects <- intersect(
    c(
      "storage_risk_index", "storage_is_event", "storage_qa_starts",
      "storage_predictor_rows", "storage_predictor_missingness_qa",
      "storage_sequential_qa", "storage_event_missing_combinations",
      "storage_excluded_event_details", "storage_missing_n",
      "storage_remaining", "excluded_event_local", "excluded_global",
      "event_missing_patterns"
    ),
    ls()
  )
  if (length(storage_audit_objects) > 0L) rm(list = storage_audit_objects)
  rm(storage_audit_objects)
  invisible(gc())

  # [FRAF archive / code note]
  # Non-varying predictors and model-row missingness are screened before
  # fitting; dropping a term requires reconstructing the complete-case frame.
  # ============================================================
  # ITERATIVE COMPLETE-CASE MODEL PREPARATION
  # ============================================================
  # The model dataset is rebuilt from the original transition-specific risk
  # set whenever a term is removed after complete-case filtering. This prevents
  # a subsequently discarded predictor from permanently excluding rows/events.
  complete_case_qa <- list()
  complete_case_term_qa <- list()

  # [FRAF archive / Historic/QA function: prepare_model]
  # Build an estimable Cox model frame, recording predictor missingness and retained events.
  prepare_model <- function(dat, candidate_terms, model_name, event_field) {

    n_risk_rows <- nrow(dat)
    n_candidate_terms <- length(candidate_terms)
    initial_events <- if (event_field %in% names(dat)) {
      sum(dat[[event_field]] == 1L, na.rm = TRUE)
    } else {
      NA_integer_
    }

    terms_current <- keep_varying(dat, candidate_terms)
    terms_initial_varying <- terms_current
    iteration <- 0L
    iteration_rows <- list()

    repeat {
      iteration <- iteration + 1L

      if (length(terms_current) == 0L) {
        model_dat <- dat[0, , drop = FALSE]
        iteration_rows[[iteration]] <- tibble(
          model = model_name,
          iteration = iteration,
          terms_before = 0L,
          terms_after = 0L,
          rows_complete = 0L,
          events_complete = 0L,
          dropped_terms = ""
        )
        break
      }

      model_dat <- dat %>%
        filter(if_all(all_of(terms_current), ~ !is.na(.x)))

      terms_next <- keep_varying(model_dat, terms_current)
      dropped_now <- setdiff(terms_current, terms_next)

      iteration_rows[[iteration]] <- tibble(
        model = model_name,
        iteration = iteration,
        terms_before = length(terms_current),
        terms_after = length(terms_next),
        rows_complete = nrow(model_dat),
        events_complete = if (event_field %in% names(model_dat)) {
          sum(model_dat[[event_field]] == 1L, na.rm = TRUE)
        } else {
          NA_integer_
        },
        dropped_terms = paste(dropped_now, collapse = "; ")
      )

      if (identical(terms_next, terms_current)) {
        break
      }

      terms_current <- terms_next
    }

    # Final rebuild from the original risk-set data using only the stable terms.
    model_dat <- if (length(terms_current) > 0L) {
      dat %>% filter(if_all(all_of(terms_current), ~ !is.na(.x)))
    } else {
      dat[0, , drop = FALSE]
    }

    final_events <- if (event_field %in% names(model_dat)) {
      sum(model_dat[[event_field]] == 1L, na.rm = TRUE)
    } else {
      NA_integer_
    }

    complete_case_qa[[model_name]] <<- tibble(
      model = model_name,
      event_field = event_field,
      risk_set_rows = n_risk_rows,
      candidate_terms = n_candidate_terms,
      varying_terms_before_filter = length(terms_initial_varying),
      final_terms = length(terms_current),
      final_term_names = paste(terms_current, collapse = "; "),
      final_complete_case_rows = nrow(model_dat),
      rows_removed_complete_case = n_risk_rows - nrow(model_dat),
      initial_events = initial_events,
      final_events = final_events,
      events_removed_complete_case = initial_events - final_events,
      iterations = iteration
    )

    complete_case_term_qa[[model_name]] <<- bind_rows(iteration_rows)

    list(data = model_dat, terms = terms_current)
  }

  # [FRAF archive / Historic/QA function: make_storage_local_subset]
  # Restrict local-position models to places with valid lagged channel-geometry support.
  make_storage_local_subset <- function(dat) {
    if (!use_local_mamore_geometry || nrow(dat) == 0L) return(dat[0, , drop = FALSE])
    required <- c("GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV", "REL_CHANNEL_POS_PREV_Z")
    if (!all(required %in% names(dat))) return(dat[0, , drop = FALSE])
    dat %>%
      filter(
        !is.na(GEOM_SUPPORT_PREV), GEOM_SUPPORT_PREV == 1L,
        !is.na(INSIDE_CHANNEL_PREV), INSIDE_CHANNEL_PREV == 1L,
        is.finite(REL_CHANNEL_POS_PREV_Z)
      )
  }

  storage_primary_full_dat <- cox_data %>% filter(STORAGE_RISK_SET == 1L)
  storage_primary_local_dat <- make_storage_local_subset(storage_primary_full_dat)

  storage_strict_full_dat <- cox_data %>%
    filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
           STORAGE_RISK_SET_STRICT_AUDIT == 1L)
  storage_strict_local_dat <- make_storage_local_subset(storage_strict_full_dat)

  storage_pure_full_dat <- cox_data %>%
    filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
           STORAGE_RISK_SET_STRICT_AUDIT == 1L,
           M3_MIXED_T1 == 0L, M3_MIXED_T2 == 0L,
           is.finite(M3_STATE_SUPPORT_T1), is.finite(M3_STATE_SUPPORT_T2),
           M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
           M3_STATE_SUPPORT_T2 >= PureStateMinSupport)
  storage_pure_local_dat <- make_storage_local_subset(storage_pure_full_dat)

  if (use_local_mamore_geometry) {
    message(
      "[Storage split] Primary full-event rows/events=", nrow(storage_primary_full_dat), "/",
      sum(storage_primary_full_dat$STORAGE_EVT == 1L, na.rm = TRUE),
      "; explicit local-position subset rows/events=", nrow(storage_primary_local_dat), "/",
      sum(storage_primary_local_dat$STORAGE_EVT == 1L, na.rm = TRUE)
    )
  }

  broad_cox_coverage_qa <- tibble(
    broad_risk_rows_total = sum(risk$FP_REACTIVATE_RISK_SET == 1L & risk$FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L, na.rm = TRUE),
    broad_events_total = sum(risk$FP_REACTIVATE_EVT == 1L & risk$FP_REACTIVATE_RISK_SET == 1L & risk$FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L, na.rm = TRUE),
    broad_risk_rows_in_unified_cox_frame = sum(cox_data$FP_REACTIVATE_RISK_SET == 1L, na.rm = TRUE),
    broad_events_in_unified_cox_frame = sum(cox_data$FP_REACTIVATE_EVT == 1L & cox_data$FP_REACTIVATE_RISK_SET == 1L, na.rm = TRUE)
  ) %>%
    mutate(
      risk_row_retention = ifelse(broad_risk_rows_total > 0, broad_risk_rows_in_unified_cox_frame / broad_risk_rows_total, NA_real_),
      event_retention = ifelse(broad_events_total > 0, broad_events_in_unified_cox_frame / broad_events_total, NA_real_)
    )
  write_csv(broad_cox_coverage_qa, file.path(out_dir, "08aa_broad_floodplain_cox_frame_coverage_QA.csv"))
  if (is.finite(broad_cox_coverage_qa$event_retention[1]) && broad_cox_coverage_qa$event_retention[1] < 0.999) {
    stop("[Broad historic Cox] Authoritative eligible broad FP->AD events were lost from the unified Cox frame. Inspect 08aa_broad_floodplain_cox_frame_coverage_QA.csv; this is fatal in v17.10.14.5.")
  }

  broad_reactivation_obj <- prepare_model(
    cox_data %>% filter(
      FP_REACTIVATE_RISK_SET == 1L,
      FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY == 1L
    ),
    broad_reactivation_terms, "floodplain_reactivation_broad", "FP_REACTIVATE_EVT"
  )
  erosion_obj <- prepare_model(
    cox_data %>% filter(REACTIVATE_RISK_SET == 1),
    erosion_terms, "active_domain_reactivation", "REACTIVATE_EVT"
  )
  baseline_obj <- prepare_model(
    cox_data %>% filter(BASE_REACTIVATE_RISK_SET_DERIVED == 1),
    erosion_terms, "initial_floodplain_reactivation", "BASE_REACTIVATE_EVT"
  )
  # Principal storage model: full eligible event population. For Mamoré this
  # deliberately excludes local-position terms; Jamuna retains Active Domain distance.
  deposition_obj <- prepare_model(
    storage_primary_full_dat,
    deposition_full_terms, "depositional_storage_full_event", "STORAGE_EVT"
  )
  # Secondary Mamoré process model: explicitly defined local-geometry subset.
  deposition_local_obj <- prepare_model(
    storage_primary_local_dat,
    deposition_local_terms, "depositional_storage_local_position_subset", "STORAGE_EVT"
  )
  stabilise_obj <- prepare_model(
    cox_data %>% filter(STABILISE_RISK_SET == 1),
    stabilise_terms, "floodplain_stabilisation", "STABILISE_EVT"
  )
  storage_rework_obj <- if (isTRUE(RunStorageReworkInterpretive)) prepare_model(
    cox_data %>% filter(STORAGE_REWORK_RISK_SET == 1),
    storage_rework_terms, "depositional_storage_reworking", "STORAGE_REWORK_EVT"
  ) else list(data = cox_data[0, , drop = FALSE], terms = character(0))
  any_obj <- prepare_model(
    cox_data %>% filter(ANY_STATE_RISK_SET == 1),
    any_terms, "any_named_primary_transition", "ANY_CONFIRMED_EVT"
  )

  # Strict observed-state sensitivity models use strict eligibility and strict
  # T1 risk sets, while retaining the same no-leakage covariate construction.
  erosion_pure_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             REACTIVATE_RISK_SET_STRICT_AUDIT == 1L),
    erosion_terms, "state_only_active_domain_reactivation", "REACTIVATE_TRANS"
  )
  deposition_pure_obj <- prepare_model(
    storage_strict_full_dat,
    deposition_full_terms, "state_only_depositional_storage_full_event", "STORAGE_TRANS"
  )
  deposition_local_pure_obj <- prepare_model(
    storage_strict_local_dat,
    deposition_local_terms, "state_only_depositional_storage_local_position_subset", "STORAGE_TRANS"
  )
  stabilise_pure_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             STABILISE_RISK_SET_STRICT_AUDIT == 1L),
    stabilise_terms, "state_only_floodplain_stabilisation", "STABILISE_TRANS"
  )
  storage_rework_pure_obj <- if (isTRUE(RunStorageReworkInterpretive)) prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1L),
    storage_rework_terms, "state_only_depositional_storage_reworking", "STORAGE_REWORK_TRANS"
  ) else list(data = cox_data[0, , drop = FALSE], terms = character(0))
  any_pure_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             ANY_STATE_RISK_SET_STRICT_AUDIT == 1L),
    any_terms, "state_only_any_transition", "ANY_STATE_EVT"
  )

  # High-support pure-state models use the same strict transitions and risk sets,
  # but additionally require both endpoint support fractions to meet the selected
  # PureStateMinSupport threshold.
  erosion_pure_state_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             REACTIVATE_RISK_SET_STRICT_AUDIT == 1L,
             M3_MIXED_T1 == 0L, M3_MIXED_T2 == 0L,
             is.finite(M3_STATE_SUPPORT_T1), is.finite(M3_STATE_SUPPORT_T2),
             M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
             M3_STATE_SUPPORT_T2 >= PureStateMinSupport),
    erosion_terms, "pure_state_active_domain_reactivation", "REACTIVATE_TRANS"
  )
  deposition_pure_state_obj <- prepare_model(
    storage_pure_full_dat,
    deposition_full_terms, "pure_state_depositional_storage_full_event", "STORAGE_TRANS"
  )
  deposition_local_pure_state_obj <- prepare_model(
    storage_pure_local_dat,
    deposition_local_terms, "pure_state_depositional_storage_local_position_subset", "STORAGE_TRANS"
  )
  stabilise_pure_state_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             STABILISE_RISK_SET_STRICT_AUDIT == 1L,
             M3_MIXED_T1 == 0L, M3_MIXED_T2 == 0L,
             is.finite(M3_STATE_SUPPORT_T1), is.finite(M3_STATE_SUPPORT_T2),
             M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
             M3_STATE_SUPPORT_T2 >= PureStateMinSupport),
    stabilise_terms, "pure_state_floodplain_stabilisation", "STABILISE_TRANS"
  )
  storage_rework_pure_state_obj <- if (isTRUE(RunStorageReworkInterpretive)) prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             STORAGE_REWORK_RISK_SET_STRICT_AUDIT == 1L,
             M3_MIXED_T1 == 0L, M3_MIXED_T2 == 0L,
             is.finite(M3_STATE_SUPPORT_T1), is.finite(M3_STATE_SUPPORT_T2),
             M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
             M3_STATE_SUPPORT_T2 >= PureStateMinSupport),
    storage_rework_terms, "pure_state_depositional_storage_reworking", "STORAGE_REWORK_TRANS"
  ) else list(data = cox_data[0, , drop = FALSE], terms = character(0))
  any_pure_state_obj <- prepare_model(
    cox_data %>%
      filter(M3_MODEL_ELIGIBLE_STRICT == 1L,
             ANY_STATE_RISK_SET_STRICT_AUDIT == 1L,
             M3_MIXED_T1 == 0L, M3_MIXED_T2 == 0L,
             is.finite(M3_STATE_SUPPORT_T1), is.finite(M3_STATE_SUPPORT_T2),
             M3_STATE_SUPPORT_T1 >= PureStateMinSupport,
             M3_STATE_SUPPORT_T2 >= PureStateMinSupport),
    any_terms, "pure_state_any_transition", "ANY_STATE_EVT"
  )

  write_csv(bind_rows(complete_case_qa), file.path(out_dir, "08_complete_case_filtering_counts.csv"))
  write_csv(bind_rows(complete_case_term_qa), file.path(out_dir, "08_complete_case_term_iterations_QA.csv"))

  broad_reactivation_model_data <- broad_reactivation_obj$data
  erosion_model_data <- erosion_obj$data
  baseline_reactivate_model_data <- baseline_obj$data
  deposition_model_data <- deposition_obj$data
  deposition_local_model_data <- deposition_local_obj$data
  stabilise_model_data <- stabilise_obj$data
  storage_rework_model_data <- storage_rework_obj$data
  any_model_data <- any_obj$data

  erosion_model_data_pure <- erosion_pure_obj$data
  deposition_model_data_pure <- deposition_pure_obj$data
  deposition_local_model_data_pure <- deposition_local_pure_obj$data
  stabilise_model_data_pure <- stabilise_pure_obj$data
  storage_rework_model_data_pure <- storage_rework_pure_obj$data
  any_model_data_pure <- any_pure_obj$data

  erosion_model_data_pure_state <- erosion_pure_state_obj$data
  deposition_model_data_pure_state <- deposition_pure_state_obj$data
  deposition_local_model_data_pure_state <- deposition_local_pure_state_obj$data
  stabilise_model_data_pure_state <- stabilise_pure_state_obj$data
  storage_rework_model_data_pure_state <- storage_rework_pure_state_obj$data
  any_model_data_pure_state <- any_pure_state_obj$data

  broad_reactivation_terms <- broad_reactivation_obj$terms

  # v17.10.14.6 memory-clean production: the temporary 08ab/08ac broad-FP
  # source/covariate and sequential Cox diagnostics have been removed from
  # routine production. Their v17.10.14.4 results established the final
  # spatial-only broad historical Cox specification. Authoritative population
  # retention/source QA and the 08aa coverage assertion remain active above.

  erosion_terms <- erosion_obj$terms
  baseline_reactivate_terms <- baseline_obj$terms
  deposition_terms <- deposition_obj$terms
  deposition_local_terms <- deposition_local_obj$terms
  stabilise_terms <- stabilise_obj$terms
  storage_rework_terms <- storage_rework_obj$terms
  any_terms <- any_obj$terms
  erosion_terms_pure <- erosion_pure_obj$terms
  deposition_terms_pure <- deposition_pure_obj$terms
  deposition_local_terms_pure <- deposition_local_pure_obj$terms
  stabilise_terms_pure <- stabilise_pure_obj$terms
  storage_rework_terms_pure <- storage_rework_pure_obj$terms
  any_terms_pure <- any_pure_obj$terms
  erosion_terms_pure_state <- erosion_pure_state_obj$terms
  deposition_terms_pure_state <- deposition_pure_state_obj$terms
  deposition_local_terms_pure_state <- deposition_local_pure_state_obj$terms
  stabilise_terms_pure_state <- stabilise_pure_state_obj$terms
  storage_rework_terms_pure_state <- storage_rework_pure_state_obj$terms
  any_terms_pure_state <- any_pure_state_obj$terms

  # [FRAF archive / code note]
  # Storage retention diagnostics make model support losses visible rather
  # than silently attributing a lower event count to geomorphic differences.
  # [FRAF archive / Historic/QA function: make_storage_retention_row]
  # Quantify how scope and missingness alter retained storage risk rows/events.
  make_storage_retention_row <- function(definition, model_scope, full_dat, scope_dat, model_dat, event_field, terms) {
    full_events <- if (event_field %in% names(full_dat)) sum(full_dat[[event_field]] == 1L, na.rm = TRUE) else NA_integer_
    scope_events <- if (event_field %in% names(scope_dat)) sum(scope_dat[[event_field]] == 1L, na.rm = TRUE) else NA_integer_
    final_events <- if (event_field %in% names(model_dat)) sum(model_dat[[event_field]] == 1L, na.rm = TRUE) else NA_integer_
    tibble(
      definition = definition,
      model_scope = model_scope,
      full_risk_rows = nrow(full_dat),
      full_risk_events = full_events,
      risk_rows_before_predictor_filter = nrow(scope_dat),
      events_before_predictor_filter = scope_events,
      final_model_rows = nrow(model_dat),
      final_model_events = final_events,
      rows_removed_by_scope = nrow(full_dat) - nrow(scope_dat),
      events_removed_by_scope = full_events - scope_events,
      rows_removed_by_predictor_filter = nrow(scope_dat) - nrow(model_dat),
      events_removed_by_predictor_filter = scope_events - final_events,
      event_retention_pct = ifelse(scope_events > 0, 100 * final_events / scope_events, NA_real_),
      event_retention_pct_of_full_risk = ifelse(full_events > 0, 100 * final_events / full_events, NA_real_),
      final_terms = paste(terms, collapse = "; ")
    )
  }

  storage_final_retention_qa <- bind_rows(
    make_storage_retention_row("primary", "full_event", storage_primary_full_dat, storage_primary_full_dat, deposition_model_data, "STORAGE_EVT", deposition_terms),
    make_storage_retention_row("strict", "full_event", storage_strict_full_dat, storage_strict_full_dat, deposition_model_data_pure, "STORAGE_TRANS", deposition_terms_pure),
    make_storage_retention_row("pure_state", "full_event", storage_pure_full_dat, storage_pure_full_dat, deposition_model_data_pure_state, "STORAGE_TRANS", deposition_terms_pure_state)
  )

  if (use_local_mamore_geometry) {
    storage_final_retention_qa <- bind_rows(
      storage_final_retention_qa,
      make_storage_retention_row("primary", "local_geometry_subset", storage_primary_full_dat, storage_primary_local_dat, deposition_local_model_data, "STORAGE_EVT", deposition_local_terms),
      make_storage_retention_row("strict", "local_geometry_subset", storage_strict_full_dat, storage_strict_local_dat, deposition_local_model_data_pure, "STORAGE_TRANS", deposition_local_terms_pure),
      make_storage_retention_row("pure_state", "local_geometry_subset", storage_pure_full_dat, storage_pure_local_dat, deposition_local_model_data_pure_state, "STORAGE_TRANS", deposition_local_terms_pure_state)
    )
  }

  write_csv(
    storage_final_retention_qa,
    file.path(out_dir, "08_storage_final_model_retention_QA.csv")
  )

  message("[Cox] Reached by Active Domain model rows: ", nrow(erosion_model_data),
          "; reactivation events: ", sum(erosion_model_data$REACTIVATE_EVT == 1, na.rm = TRUE))
  message("[Cox] Initial floodplain reached by Active Domain model rows: ", nrow(baseline_reactivate_model_data),
          "; baseline reactivation events: ", sum(baseline_reactivate_model_data$BASE_REACTIVATE_EVT == 1, na.rm = TRUE))
  message("[Cox] Depositional-storage principal full-event model rows: ", nrow(deposition_model_data),
          "; storage events: ", sum(deposition_model_data$STORAGE_EVT == 1, na.rm = TRUE))
  if (use_local_mamore_geometry) {
    message("[Cox] Depositional-storage local-position subset rows: ", nrow(deposition_local_model_data),
            "; storage events: ", sum(deposition_local_model_data$STORAGE_EVT == 1, na.rm = TRUE))
  }
  message("[Cox] Floodplain-stabilisation model rows: ", nrow(stabilise_model_data),
          "; stabilisation events: ", sum(stabilise_model_data$STABILISE_EVT == 1, na.rm = TRUE))
  if (isTRUE(RunStorageReworkInterpretive)) message("[Cox] Depositional-storage reworking model rows: ", nrow(storage_rework_model_data),
          "; reworking events: ", sum(storage_rework_model_data$STORAGE_REWORK_EVT == 1, na.rm = TRUE))
  message("[Cox] Any named primary transition model rows: ", nrow(any_model_data),
          "; any transition events: ", sum(any_model_data$ANY_CONFIRMED_EVT == 1, na.rm = TRUE))
  message("[Cox strict] Reached by Active Domain rows: ", nrow(erosion_model_data_pure),
          "; strict reactivation events: ", sum(erosion_model_data_pure$REACTIVATE_TRANS == 1, na.rm = TRUE))
  message("[Cox strict] Depositional-storage full-event rows: ", nrow(deposition_model_data_pure),
          "; strict storage events: ", sum(deposition_model_data_pure$STORAGE_TRANS == 1, na.rm = TRUE))
  if (use_local_mamore_geometry) {
    message("[Cox strict] Depositional-storage local-position rows: ", nrow(deposition_local_model_data_pure),
            "; strict storage events: ", sum(deposition_local_model_data_pure$STORAGE_TRANS == 1, na.rm = TRUE))
  }
  message("[Cox strict] Floodplain-stabilisation rows: ", nrow(stabilise_model_data_pure),
          "; strict stabilisation events: ", sum(stabilise_model_data_pure$STABILISE_TRANS == 1, na.rm = TRUE))
  if (isTRUE(RunStorageReworkInterpretive)) message("[Cox strict] Depositional-storage reworking rows: ", nrow(storage_rework_model_data_pure),
          "; strict reworking events: ", sum(storage_rework_model_data_pure$STORAGE_REWORK_TRANS == 1, na.rm = TRUE))
  message("[Cox strict] Any state transition rows: ", nrow(any_model_data_pure),
          "; strict transition events: ", sum(any_model_data_pure$ANY_STATE_EVT == 1, na.rm = TRUE))
  message("[Cox pure-state] Reached by Active Domain rows: ", nrow(erosion_model_data_pure_state),
          "; pure-state reactivation events: ", sum(erosion_model_data_pure_state$REACTIVATE_TRANS == 1, na.rm = TRUE))
  message("[Cox pure-state] Depositional-storage full-event rows: ", nrow(deposition_model_data_pure_state),
          "; pure-state storage events: ", sum(deposition_model_data_pure_state$STORAGE_TRANS == 1, na.rm = TRUE))
  if (use_local_mamore_geometry) {
    message("[Cox pure-state] Depositional-storage local-position rows: ", nrow(deposition_local_model_data_pure_state),
            "; pure-state storage events: ", sum(deposition_local_model_data_pure_state$STORAGE_TRANS == 1, na.rm = TRUE))
  }
  message("[Cox pure-state] Floodplain-stabilisation rows: ", nrow(stabilise_model_data_pure_state),
          "; pure-state stabilisation events: ", sum(stabilise_model_data_pure_state$STABILISE_TRANS == 1, na.rm = TRUE))
  if (isTRUE(RunStorageReworkInterpretive)) message("[Cox pure-state] Depositional-storage reworking rows: ", nrow(storage_rework_model_data_pure_state),
          "; pure-state reworking events: ", sum(storage_rework_model_data_pure_state$STORAGE_REWORK_TRANS == 1, na.rm = TRUE))
  message("[Cox pure-state] Any state transition rows: ", nrow(any_model_data_pure_state),
          "; pure-state transition events: ", sum(any_model_data_pure_state$ANY_STATE_EVT == 1, na.rm = TRUE))
  message("[Cox] Reached by Active Domain terms: ", paste(erosion_terms, collapse = ", "))
  message("[Cox] Depositional-storage principal full-event terms: ", paste(deposition_terms, collapse = ", "))
  if (use_local_mamore_geometry) message("[Cox] Depositional-storage local-position terms: ", paste(deposition_local_terms, collapse = ", "))
  message("[Cox] Floodplain-stabilisation terms: ", paste(stabilise_terms, collapse = ", "))
  if (isTRUE(RunStorageReworkInterpretive)) message("[Cox] Depositional-storage reworking terms: ", paste(storage_rework_terms, collapse = ", "))
  message("[Cox] Any named primary transition terms: ", paste(any_terms, collapse = ", "))

  cox_term_table <- bind_rows(
    tibble(model = "active_domain_reactivation", term = erosion_terms),
    tibble(model = "initial_floodplain_reactivation", term = baseline_reactivate_terms),
    tibble(model = "depositional_storage_full_event", term = deposition_terms),
    tibble(model = "depositional_storage_local_position_subset", term = deposition_local_terms),
    tibble(model = "floodplain_stabilisation", term = stabilise_terms),
    tibble(model = "depositional_storage_reworking", term = storage_rework_terms),
    tibble(model = "any_named_primary_transition", term = any_terms),
    tibble(model = "state_only_active_domain_reactivation", term = erosion_terms_pure),
    tibble(model = "state_only_depositional_storage_full_event", term = deposition_terms_pure),
    tibble(model = "state_only_depositional_storage_local_position_subset", term = deposition_local_terms_pure),
    tibble(model = "state_only_floodplain_stabilisation", term = stabilise_terms_pure),
    tibble(model = "state_only_depositional_storage_reworking", term = storage_rework_terms_pure),
    tibble(model = "state_only_any_state_transition", term = any_terms_pure),
    tibble(model = "pure_state_active_domain_reactivation", term = erosion_terms_pure_state),
    tibble(model = "pure_state_depositional_storage_full_event", term = deposition_terms_pure_state),
    tibble(model = "pure_state_depositional_storage_local_position_subset", term = deposition_local_terms_pure_state),
    tibble(model = "pure_state_floodplain_stabilisation", term = stabilise_terms_pure_state),
    tibble(model = "pure_state_depositional_storage_reworking", term = storage_rework_terms_pure_state),
    tibble(model = "pure_state_any_state_transition", term = any_terms_pure_state)
  )
  write_csv(cox_term_table, file.path(out_dir, "08_cox_terms_used.csv"))
  spatial_framework_table <- spatial_framework_table %>%
    mutate(
      predictor_time_basis = case_when(
        grepl("reference_centreline", spatial_framework) ~ "fixed reference",
        grepl("lagged|active_domain_braided|dated_centreline|water_distance", spatial_framework) ~ "interval start y1",
        TRUE ~ "not applicable or unavailable"
      ),
      outcome_interval = "(y1, y2]",
      temporal_leakage_permitted = FALSE
    )
  write_csv(
    spatial_framework_table,
    file.path(out_dir, "08_spatial_predictor_framework.csv")
  )

  # [FRAF archive / code note]
  # Historic Cox fits use counting-process intervals and model-specific risk
  # populations; their coefficients are not prospective absolute probabilities.
  # [FRAF archive / Historic/QA function: fit_write_cox]
  # Fit an explanatory Cox model and export coefficient, fit and diagnostic products.
  fit_write_cox <- function(model_data, event_field, terms, prefix, title_label) {
    if (length(terms) == 0 || nrow(model_data) == 0 || sum(model_data[[event_field]] == 1, na.rm = TRUE) == 0) {
      message("[Cox] ", title_label, " Cox model skipped: no usable predictors/events.")
      return(NULL)
    }

    f <- as.formula(
      paste0(
        "Surv(tstart_yr, tstop_yr, ", event_field, ") ~ ",
        paste(terms, collapse = " + "),
        " + cluster(PLACE_ID)"
      )
    )

    mod <- tryCatch(
      coxph(
        f,
        data = model_data,
        ties = "efron",
        x = TRUE
      ),
      error = function(e) {
        message("[Cox] ", title_label, " model failed: ", conditionMessage(e))
        NULL
      }
    )
    if (is.null(mod)) return(NULL)

    write_csv(
      broom::tidy(mod, exponentiate = TRUE, conf.int = TRUE),
      file.path(out_dir, paste0(prefix, "_model.csv"))
    )

    capture.output(
      summary(mod),
      file = file.path(out_dir, paste0(prefix, "_model_summary.txt"))
    )

    capture.output(
      try(cox.zph(mod), silent = TRUE),
      file = file.path(out_dir, paste0(prefix, "_ph_test.txt"))
    )

    model_data[[paste0("RISK_", toupper(title_label), "_REL")]] <- predict(mod, newdata = model_data, type = "risk")
    model_data[[paste0("LP_", toupper(title_label))]] <- predict(mod, newdata = model_data, type = "lp")

    keep_cols <- c(
      "PLACE_ID", "BLOCK_ID", "tstart_yr", "tstop_yr",
      "REACTIVATE_EVT", "STORAGE_EVT", "STABILISE_EVT", "STORAGE_REWORK_EVT", "FP_STORAGE_EVT",
      "REACTIVATE_EVT_PRIMARY", "STORAGE_EVT_PRIMARY", "STABILISE_EVT_PRIMARY",
      "STORAGE_REWORK_EVT_PRIMARY", "FP_STORAGE_EVT_PRIMARY", "ANY_STATE_EVT_PRIMARY",
      "REACTIVATE_EVT_STRICT_AUDIT", "STORAGE_EVT_STRICT_AUDIT", "STABILISE_EVT_STRICT_AUDIT",
      "STORAGE_REWORK_EVT_STRICT_AUDIT", "FP_STORAGE_EVT_STRICT_AUDIT", "ANY_STATE_EVT_STRICT_AUDIT",
      "REACTIVATE_BRIDGED", "STORAGE_BRIDGED", "STORAGE_REWORK_BRIDGED", "FP_STORAGE_BRIDGED",
      "ANY_CONFIRMED_EVT", "ANY_STATE_EVT", "ANY_ONTO_EVT",
      "REACTIVATE_CONFIRMED", "STORAGE_CONFIRMED", "STABILISE_CONFIRMED", "STORAGE_REWORK_CONFIRMED", "FP_STORAGE_CONFIRMED",
      "REACTIVATE_TRANS", "STORAGE_TRANS", "STABILISE_TRANS", "STORAGE_REWORK_TRANS", "FP_STORAGE_TRANS", "REACTIVATE_EVT_PURE", "STORAGE_EVT_PURE", "STABILISE_EVT_PURE", "ANY_ONTO_EVT_PURE",
      "BASE_REACTIVATE_EVT", "BASE_REACTIVATE_EVT_PRIMARY", "BASE_REACTIVATE_EVT_STRICT_AUDIT",
      "INIT_FP_COHORT", "BASE_RISK", "BASE_REACTIVATE_RISK_SET_DERIVED",
      "BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED", "BASE_REACTIVATE_RISK_SET_DERIVED_STRICT_AUDIT",
      "E_EVT_RAW", "D_EVT_RAW", "E_CONFIRM_AVAILABLE", "D_CONFIRM_AVAILABLE", "E_evt", "D_evt", "ANY_EVT",
      "REACTIVATE_RISK_SET", "STORAGE_RISK_SET", "STABILISE_RISK_SET",
      "STORAGE_REWORK_RISK_SET", "FP_STORAGE_RISK_SET", "ANY_STATE_RISK_SET",
      "REACTIVATE_RISK_SET_PRIMARY", "STORAGE_RISK_SET_PRIMARY", "STABILISE_RISK_SET_PRIMARY",
      "STORAGE_REWORK_RISK_SET_PRIMARY", "FP_STORAGE_RISK_SET_PRIMARY", "ANY_STATE_RISK_SET_PRIMARY",
      "REACTIVATE_RISK_SET_STRICT_AUDIT", "STORAGE_RISK_SET_STRICT_AUDIT",
      "STABILISE_RISK_SET_STRICT_AUDIT", "STORAGE_REWORK_RISK_SET_STRICT_AUDIT",
      "FP_STORAGE_RISK_SET_STRICT_AUDIT", "ANY_STATE_RISK_SET_STRICT_AUDIT",
      "E_RISK_SET", "D_RISK_SET", "RISK_SET", "event_class",
      "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "EVENT_ONTOLOGY", "NEXT_EVENT_ONTOLOGY",
      "M3_ACTIVE_FRAC_T1", "M3_ACTIVE_FRAC_T2", "M3_STORAGE_FRAC_T1", "M3_STORAGE_FRAC_T2",
      "M3_STAB_FP_FRAC_T1", "M3_STAB_FP_FRAC_T2", "M3_UNRESOLVED_FRAC_T1", "M3_UNRESOLVED_FRAC_T2",
      "M3_STATE_SUM_T1", "M3_STATE_SUM_T2", "M3_STATE_SUPPORT_T1", "M3_STATE_SUPPORT_T2",
      "M3_STATE_CONF_T1", "M3_STATE_CONF_T2", "STORAGE_START_YMD_T1", "STORAGE_START_YMD_T2",
      "STORAGE_AGE_YR_T1", "STORAGE_AGE_YR_T2", "STORAGE_CLOCK_RESET_T2",
      "M3_MODEL_ELIGIBLE_STRICT", "M3_MODEL_EXCLUSION_REASON",
      "M3_MODEL_ELIGIBLE_PRIMARY", "M3_MODEL_EXCLUSION_REASON_PRIMARY",
      "M3_EFFECTIVE_STATE_T1_PRIMARY", "EVENT_DEFINITION_USED",
      "M3_ANOMALY_SEVERITY", "M3_ANOMALY_FLAGS",
      "M3_MIXED_T1", "M3_MIXED_T2", "STORAGE_AGE_YR_T1", "STORAGE_AGE_YR_T2",
      "FP_CONDITION_MODEL", "FINAL_ONTO_RAW_MODEL", "SURFACE_AGE_EST_MODEL", "FP_STAB_MODEL", "FP_RECENT_MODEL", "FP_REWORKED_MODEL",
      "ASM_STATE_PREV", "ASM_CLASS_PREV", "ASM_STRUCTURE_CL_PREV",
      "ASM_N_EVENTS_PREV", "ASM_N_ACTIVE_DOMAIN_PREV", "ASM_N_STORAGE_PREV", "ASM_N_STAB_FP_PREV",
      "ASM_N_REACTIVATE_PREV", "ASM_N_STORAGE_EVT_PREV", "ASM_N_STABILISE_PREV",
      "ASM_N_EROSION_PREV", "ASM_N_DEPOSITION_PREV",
      "ASM_DIST_FREQ_PREV", "ASM_STORAGE_FRAC_PREV", "ASM_STAB_FP_FRAC_PREV",
      "ASM_DOM_RATIO_PREV", "ASM_NET_BAL_PREV", "ASM_N_EPISODES_PREV",
      "ASM_QUIET_SINCE_PREV", "ASM_MAX_QUIET_PREV",
      "ASM_EVER_ERODED_PREV", "ASM_EVER_DEPOSITED_PREV", "ASM_ACTIVE_PREV",
      "ASM_COV_FRAC",
      "DIST_CL_REF", "DIST_CL_CURR", "CURV_CL_CURR", "CURV_EROSION_CURR", "DIST_X_CURV_EROSION",
      "DIST_CL_PREV", "DIST_CL_INIT", "DIST_CL_MEAN",
      "DIST_CL_REF_BIN", "DIST_CL_CURR_BIN", "DIST_CL_PREV_BIN",
      "DIST_ACTIVE_PREV", "DIST_ACTIVE_CURR", "DIST_WATER_PREV", "DIST_WATER_CURR",
      "IN_ACTIVE_PREV", "IN_ACTIVE_CURR", "IN_WATER_PREV", "IN_WATER_CURR",
      "SPATIAL_TIME_BASIS", "SPATIAL_OUTCOME_INTERVAL",
      ".Y1_YMD_CODE", ".GEOM_YMD_PREV_CODE",
      paste0("RISK_", toupper(title_label), "_REL"),
      paste0("LP_", toupper(title_label))
    )

    write_csv(
      model_data %>% select(any_of(keep_cols)),
      file.path(out_dir, paste0(prefix, "_predictions.csv"))
    )

    return(mod)
  }

  broad_reactivation_cox_model <- fit_write_cox(
    broad_reactivation_model_data,
    "FP_REACTIVATE_EVT",
    broad_reactivation_terms,
    "08aa_cox_floodplain_reactivation_broad_interval_PREV",
    "floodplain_reactivation_broad"
  )

  erosion_cox_model <- fit_write_cox(
    erosion_model_data,
    "REACTIVATE_EVT",
    erosion_terms,
    "08_cox_active_domain_reactivation_interval_PREV",
    "reactivation"
  )

  baseline_reactivate_cox_model <- fit_write_cox(
    baseline_reactivate_model_data,
    "BASE_REACTIVATE_EVT",
    baseline_reactivate_terms,
    "08a_cox_initial_floodplain_reactivation_interval_PREV",
    "initial_floodplain_reactivation"
  )

  deposition_cox_model <- fit_write_cox(
    deposition_model_data,
    "STORAGE_EVT",
    deposition_terms,
    "08b_cox_depositional_storage_interval_PREV",
    "storage_full_event"
  )

  deposition_cox_model_local <- fit_write_cox(
    deposition_local_model_data,
    "STORAGE_EVT",
    deposition_local_terms,
    "08bl_cox_depositional_storage_local_position_interval_PREV",
    "storage_local_position"
  )

  stabilise_cox_model <- fit_write_cox(
    stabilise_model_data,
    "STABILISE_EVT",
    stabilise_terms,
    "08c_cox_floodplain_stabilisation_interval_PREV",
    "stabilisation"
  )

  storage_rework_cox_model <- if (isTRUE(RunStorageReworkInterpretive)) fit_write_cox(
    storage_rework_model_data,
    "STORAGE_REWORK_EVT",
    storage_rework_terms,
    "08e_cox_depositional_storage_reworking_interval_PREV",
    "storage_reworking"
  ) else NULL

  # -------------------------------------------------------------------------
  # v17.10.15.1 Mamore DS->AD four-variant comparison.
  # This is deliberately lightweight: it does not write row-level predictions.
  # [FRAF archive / code note]
  # The Step-3D Mamoré DS-to-AD reduced-history set is frozen here.
  # Do not reintroduce episode-count/maximum-quiet terms in this source version.
  # Step-3D supplies the frozen reduced-history and four-interval sensitivity
  # definitions used here; Early/Middle/Late and detailed selection diagnostics
  # remain in the companion Step-3D outputs.
  # -------------------------------------------------------------------------
  if (
    isTRUE(RunMamoreDSADVariantComparison) &&
    isTRUE(RunStorageReworkInterpretive) &&
    !identical(reach_label, "Jamuna") &&
    "DIST_CHANNEL_PREV_LINEAR_Z" %in% names(cox_data)
  ) {
    message("[Mamore DS->AD variants] Building all-history/no-cutoff x curvature comparison.")
    message(
      "[Mamore DS->AD variants] Reduced history terms: ",
      paste(storage_rework_history_core, collapse = ", "),
      " + ASM_STORAGE_FRAC_PREV_Z, ASM_QUIET_SINCE_PREV_Z, ASM_N_STORAGE_EVT_PREV_Z"
    )

    dsad_history_terms <- unique(c(
      storage_rework_history_core,
      "ASM_STORAGE_FRAC_PREV_Z",
      "ASM_QUIET_SINCE_PREV_Z",
      "ASM_N_STORAGE_EVT_PREV_Z"
    ))
    dsad_base_terms <- unique(c("DIST_CHANNEL_PREV_LINEAR_Z", dsad_history_terms))
    dsad_curv_term <- "MAM_OUTER_CURV_REACT_PREV_Z"
    dsad_legacy_terms <- unique(c(
      "MAM_NEAR_CHANNEL_PREV",
      "MAM_OUTER_REACT_EXPOSED_PREV",
      dsad_curv_term,
      dsad_history_terms
    ))

    dsad_needed <- unique(c(
      "PLACE_ID", "tstart_yr", "tstop_yr",
      "STORAGE_REWORK_EVT", "STORAGE_REWORK_RISK_SET",
      "DIST_CHANNEL_PREV",
      dsad_base_terms, dsad_curv_term, dsad_legacy_terms
    ))
    dsad_idx <- which(cox_data$STORAGE_REWORK_RISK_SET == 1L)
    dsad_dat <- cox_data[dsad_idx, intersect(dsad_needed, names(cox_data)), drop = FALSE]
    rm(dsad_idx)

    dsad_base_terms <- keep_varying(dsad_dat, dsad_base_terms)
    dsad_has_curv <- dsad_curv_term %in% keep_varying(dsad_dat, dsad_curv_term)
    dsad_legacy_terms <- keep_varying(dsad_dat, dsad_legacy_terms)

    # Identify exceptional distal-event intervals from the complete observed
    # history. These intervals remain in the principal production model; their
    # exclusion is a mechanism-identification sensitivity only.
    dsad_dat$.INTERVAL_KEY <- paste(
      sprintf("%.6f", round(dsad_dat$tstart_yr, 6)),
      sprintf("%.6f", round(dsad_dat$tstop_yr, 6)),
      sep = " -> "
    )
    dsad_events <- dsad_dat[
      dsad_dat$STORAGE_REWORK_EVT == 1L &
        is.finite(dsad_dat$DIST_CHANNEL_PREV),
      c(".INTERVAL_KEY", "DIST_CHANNEL_PREV"),
      drop = FALSE
    ]
    # Fixed Step-3D exceptional-interval set used for the final production
    # mechanism sensitivity. Keys use the same 6-decimal representation as
    # .INTERVAL_KEY above. Threshold-based detection below is retained as QA.
    dsad_step3d_exceptional <- c(
      "2.002740 -> 4.002740",
      "7.005479 -> 8.005479",
      "15.010959 -> 16.010959",
      "29.021918 -> 30.021918"
    )
    dsad_exceptional <- character(0)
    if (nrow(dsad_events) > 0L) {
      dsad_events$.DISTAL <- dsad_events$DIST_CHANNEL_PREV > MamoreDSADDistalThresholdM
      dsad_interval_n <- aggregate(
        rep(1L, nrow(dsad_events)),
        by = list(interval = dsad_events$.INTERVAL_KEY),
        FUN = sum
      )
      names(dsad_interval_n)[2] <- "events"
      dsad_interval_d <- aggregate(
        as.integer(dsad_events$.DISTAL),
        by = list(interval = dsad_events$.INTERVAL_KEY),
        FUN = sum
      )
      names(dsad_interval_d)[2] <- "distal_events"
      dsad_interval_qa <- merge(dsad_interval_n, dsad_interval_d, by = "interval", all = TRUE)
      dsad_interval_qa$distal_fraction <- ifelse(
        dsad_interval_qa$events > 0,
        dsad_interval_qa$distal_events / dsad_interval_qa$events,
        NA_real_
      )
      dsad_interval_qa$automatic_threshold_exceptional <- (
        dsad_interval_qa$distal_events >= MamoreDSADExceptionalIntervalMinEvents &
          dsad_interval_qa$distal_fraction >= MamoreDSADExceptionalIntervalMinFraction
      )
      dsad_interval_qa$step3d_fixed_exceptional <- (
        dsad_interval_qa$interval %in% dsad_step3d_exceptional
      )
      # Final production sensitivity definition: exact Step-3D four-interval set.
      dsad_interval_qa$exceptional <- dsad_interval_qa$step3d_fixed_exceptional
      dsad_interval_qa <- dsad_interval_qa[
        order(!dsad_interval_qa$step3d_fixed_exceptional,
              -dsad_interval_qa$distal_events,
              -dsad_interval_qa$distal_fraction),
        ,
        drop = FALSE
      ]

      missing_step3d_intervals <- setdiff(dsad_step3d_exceptional, dsad_interval_qa$interval)
      if (length(missing_step3d_intervals) > 0L) {
        stop(
          "[Mamore DS->AD cutoff QA] Final Step-3D exceptional interval(s) ",
          "not found in the current Risk Table: ",
          paste(missing_step3d_intervals, collapse = "; "),
          ". Refusing to substitute threshold-detected intervals."
        )
      }
      dsad_exceptional <- dsad_step3d_exceptional
      write_csv(
        dsad_interval_qa,
        file.path(out_dir, "08e1_Mamore_DSAD_exceptional_interval_diagnostic.csv")
      )
    } else {
      write_csv(
        tibble(
          interval = character(),
          events = integer(),
          distal_events = integer(),
          distal_fraction = numeric(),
          automatic_threshold_exceptional = logical(),
          step3d_fixed_exceptional = logical(),
          exceptional = logical()
        ),
        file.path(out_dir, "08e1_Mamore_DSAD_exceptional_interval_diagnostic.csv")
      )
    }

    # [FRAF archive / code note]
    # Compare Mamoré DS-to-AD variants with explicit geometry and cutoff
    # choices, retaining the same five reduced-history terms throughout.
    # [FRAF archive / Historic/QA function: fit_dsad_variant]
    # Fit one Mamore DS-to-AD spatial/history sensitivity variant with explicit scope metadata.
    fit_dsad_variant <- function(label, scope, dat, terms, curvature_included, legacy = FALSE) {
      terms <- keep_varying(dat, terms)
      if (length(terms) == 0L) {
        return(list(
          fit = NULL,
          stat = tibble(
            variant = label, scope = scope, curvature = curvature_included,
            legacy = legacy, status = "NO_TERMS", n = nrow(dat),
            events = sum(dat$STORAGE_REWORK_EVT == 1L, na.rm = TRUE),
            n_terms = 0L, terms = "", logLik = NA_real_, AIC = NA_real_,
            concordance = NA_real_, warnings = "No varying candidate terms"
          ),
          coef = tibble(), ph = tibble()
        ))
      }
      ok <- complete.cases(dat[, terms, drop = FALSE])
      dd <- dat[ok, , drop = FALSE]
      if (nrow(dd) == 0L || sum(dd$STORAGE_REWORK_EVT == 1L, na.rm = TRUE) == 0L) {
        return(list(
          fit = NULL,
          stat = tibble(
            variant = label, scope = scope, curvature = curvature_included,
            legacy = legacy, status = "NO_USABLE_EVENTS", n = nrow(dd),
            events = sum(dd$STORAGE_REWORK_EVT == 1L, na.rm = TRUE),
            n_terms = length(terms), terms = paste(terms, collapse = "; "),
            logLik = NA_real_, AIC = NA_real_, concordance = NA_real_,
            warnings = "No usable complete-case events"
          ),
          coef = tibble(), ph = tibble()
        ))
      }

      f <- as.formula(paste0(
        "Surv(tstart_yr, tstop_yr, STORAGE_REWORK_EVT) ~ ",
        paste(terms, collapse = " + "),
        " + cluster(PLACE_ID)"
      ))
      ww <- character()
      mod <- tryCatch(
        withCallingHandlers(
          coxph(
            f, data = dd, ties = "efron", x = TRUE,
            control = coxph.control(iter.max = 50, eps = 1e-8, toler.inf = 1e-8)
          ),
          warning = function(w) {
            ww <<- c(ww, conditionMessage(w))
            invokeRestart("muffleWarning")
          }
        ),
        error = function(e) e
      )

      if (inherits(mod, "error")) {
        return(list(
          fit = NULL,
          stat = tibble(
            variant = label, scope = scope, curvature = curvature_included,
            legacy = legacy, status = "FAILED", n = nrow(dd),
            events = sum(dd$STORAGE_REWORK_EVT == 1L, na.rm = TRUE),
            n_terms = length(terms), terms = paste(terms, collapse = "; "),
            logLik = NA_real_, AIC = NA_real_, concordance = NA_real_,
            warnings = paste(c(conditionMessage(mod), ww), collapse = " | ")
          ),
          coef = tibble(), ph = tibble()
        ))
      }

      sm <- try(summary(mod), silent = TRUE)
      conc <- if (!inherits(sm, "try-error") && !is.null(sm$concordance)) {
        as.numeric(sm$concordance[1])
      } else NA_real_

      coef_tab <- tryCatch(
        broom::tidy(mod, exponentiate = TRUE, conf.int = TRUE) %>%
          mutate(variant = label, scope = scope, curvature = curvature_included, legacy = legacy) %>%
          select(variant, scope, curvature, legacy, everything()),
        error = function(e) tibble()
      )

      zph <- try(cox.zph(mod, transform = "km"), silent = TRUE)
      ph_tab <- tibble()
      if (!inherits(zph, "try-error")) {
        zz <- as.data.frame(zph$table)
        ph_tab <- tibble(
          variant = label,
          scope = scope,
          curvature = curvature_included,
          legacy = legacy,
          term = rownames(zz),
          chisq = zz[, 1],
          df = zz[, 2],
          p = zz[, 3]
        )
      } else {
        ph_tab <- tibble(
          variant = label, scope = scope, curvature = curvature_included,
          legacy = legacy, term = "PH_TEST_FAILED",
          chisq = NA_real_, df = NA_real_, p = NA_real_
        )
      }

      list(
        fit = mod,
        stat = tibble(
          variant = label, scope = scope, curvature = curvature_included,
          legacy = legacy, status = "OK", n = nrow(dd),
          events = sum(dd$STORAGE_REWORK_EVT == 1L, na.rm = TRUE),
          n_terms = length(terms), terms = paste(terms, collapse = "; "),
          logLik = as.numeric(logLik(mod)), AIC = AIC(mod),
          concordance = conc, warnings = paste(unique(ww), collapse = " | ")
        ),
        coef = coef_tab,
        ph = ph_tab
      )
    }

    # For the nested curvature comparisons use the same complete-case population
    # within each scope whenever curvature is available, so Delta AIC is valid.
    dsad_common_terms <- unique(c(dsad_base_terms, if (dsad_has_curv) dsad_curv_term else character(0)))
    dsad_common_ok <- if (length(dsad_common_terms) > 0L) {
      complete.cases(dsad_dat[, dsad_common_terms, drop = FALSE])
    } else rep(FALSE, nrow(dsad_dat))
    dsad_all_common <- dsad_dat[dsad_common_ok, , drop = FALSE]
    dsad_no_cut <- if (length(dsad_exceptional) > 0L) {
      dsad_all_common[!(dsad_all_common$.INTERVAL_KEY %in% dsad_exceptional), , drop = FALSE]
    } else {
      dsad_all_common
    }

    dsad_results <- list()
    dsad_results[["M1"]] <- fit_dsad_variant(
      "M1_all_history_linear_margin", "all_history",
      dsad_all_common, dsad_base_terms, FALSE
    )
    if (dsad_has_curv) {
      dsad_results[["M2"]] <- fit_dsad_variant(
        "M2_all_history_linear_margin_plus_curvature", "all_history",
        dsad_all_common, c(dsad_base_terms, dsad_curv_term), TRUE
      )
    }
    dsad_results[["M3"]] <- fit_dsad_variant(
      "M3_no_cutoff_linear_margin", "no_cutoff",
      dsad_no_cut, dsad_base_terms, FALSE
    )
    if (dsad_has_curv) {
      dsad_results[["M4"]] <- fit_dsad_variant(
        "M4_no_cutoff_linear_margin_plus_curvature", "no_cutoff",
        dsad_no_cut, c(dsad_base_terms, dsad_curv_term), TRUE
      )
    }

    # Legacy comparator reproduces the pre-v17.10.15 local near-channel /
    # outer-bank / curvature spatial recipe. Its AIC is not treated as nested
    # unless it happens to use the same complete-case rows.
    if (length(dsad_legacy_terms) > 0L) {
      dsad_results[["L0"]] <- fit_dsad_variant(
        "L0_legacy_local_geometry_all_history", "legacy_all_history",
        dsad_dat, dsad_legacy_terms, TRUE, legacy = TRUE
      )
    }

    dsad_stat <- bind_rows(lapply(dsad_results, `[[`, "stat"))
    dsad_coef <- bind_rows(lapply(dsad_results, `[[`, "coef"))
    dsad_ph <- bind_rows(lapply(dsad_results, `[[`, "ph"))

    dsad_stat$delta_AIC_within_scope <- NA_real_
    for (sc in c("all_history", "no_cutoff")) {
      jj <- which(dsad_stat$scope == sc & dsad_stat$status == "OK" & is.finite(dsad_stat$AIC))
      if (length(jj) > 0L) {
        dsad_stat$delta_AIC_within_scope[jj] <- dsad_stat$AIC[jj] - min(dsad_stat$AIC[jj])
      }
    }
    dsad_stat$exceptional_intervals_removed <- ifelse(
      dsad_stat$scope == "no_cutoff", length(dsad_exceptional), 0L
    )

    write_csv(dsad_stat, file.path(out_dir, "08e2_Mamore_DSAD_variant_model_comparison.csv"))
    write_csv(dsad_coef, file.path(out_dir, "08e3_Mamore_DSAD_variant_coefficients.csv"))
    write_csv(dsad_ph, file.path(out_dir, "09e1_Mamore_DSAD_variant_PH_diagnostics.csv"))

    message(
      "[Mamore DS->AD variants] Completed. Step-3D exceptional intervals removed in sensitivity=",
      length(dsad_exceptional),
      "; curvature available=", dsad_has_curv,
      ". See 08e1/08e2/08e3/09e1 outputs."
    )

    # Drop fitted sensitivity models immediately; only the principal production
    # model is retained for the downstream generic PH/export workflow.
    rm(dsad_results, dsad_stat, dsad_coef, dsad_ph, dsad_all_common, dsad_no_cut,
       dsad_common_ok, dsad_common_terms, dsad_dat, dsad_events)
    invisible(gc())
  }

  any_cox_model <- fit_write_cox(
    any_model_data,
    "ANY_CONFIRMED_EVT",
    any_terms,
    "08d_cox_any_confirmed_named_transition_interval_PREV",
    "confirmed_transition"
  )

  erosion_cox_model_pure <- fit_write_cox(
    erosion_model_data_pure,
    "REACTIVATE_TRANS",
    erosion_terms_pure,
    "08p_cox_state_only_active_domain_reactivation_interval_PREV",
    "strict_reactivation"
  )

  deposition_cox_model_pure <- fit_write_cox(
    deposition_model_data_pure,
    "STORAGE_TRANS",
    deposition_terms_pure,
    "08bp_cox_state_only_depositional_storage_interval_PREV",
    "strict_storage_full_event"
  )

  deposition_cox_model_local_pure <- fit_write_cox(
    deposition_local_model_data_pure,
    "STORAGE_TRANS",
    deposition_local_terms_pure,
    "08bpl_cox_state_only_depositional_storage_local_position_interval_PREV",
    "strict_storage_local_position"
  )

  stabilise_cox_model_pure <- fit_write_cox(
    stabilise_model_data_pure,
    "STABILISE_TRANS",
    stabilise_terms_pure,
    "08cp_cox_state_only_floodplain_stabilisation_interval_PREV",
    "strict_stabilisation"
  )

  storage_rework_cox_model_pure <- if (isTRUE(RunStorageReworkInterpretive)) fit_write_cox(
    storage_rework_model_data_pure,
    "STORAGE_REWORK_TRANS",
    storage_rework_terms_pure,
    "08ep_cox_state_only_depositional_storage_reworking_interval_PREV",
    "strict_storage_reworking"
  ) else NULL

  any_cox_model_pure <- fit_write_cox(
    any_model_data_pure,
    "ANY_STATE_EVT",
    any_terms_pure,
    "08dp_cox_state_only_any_state_transition_interval_PREV",
    "strict_transition"
  )

  erosion_cox_model_pure_state <- fit_write_cox(
    erosion_model_data_pure_state,
    "REACTIVATE_TRANS",
    erosion_terms_pure_state,
    "08q_cox_pure_state_active_domain_reactivation_interval_PREV",
    "pure_state_reactivation"
  )
  deposition_cox_model_pure_state <- fit_write_cox(
    deposition_model_data_pure_state,
    "STORAGE_TRANS",
    deposition_terms_pure_state,
    "08bq_cox_pure_state_depositional_storage_interval_PREV",
    "pure_state_storage_full_event"
  )

  deposition_cox_model_local_pure_state <- fit_write_cox(
    deposition_local_model_data_pure_state,
    "STORAGE_TRANS",
    deposition_local_terms_pure_state,
    "08bql_cox_pure_state_depositional_storage_local_position_interval_PREV",
    "pure_state_storage_local_position"
  )
  stabilise_cox_model_pure_state <- fit_write_cox(
    stabilise_model_data_pure_state,
    "STABILISE_TRANS",
    stabilise_terms_pure_state,
    "08cq_cox_pure_state_floodplain_stabilisation_interval_PREV",
    "pure_state_stabilisation"
  )
  storage_rework_cox_model_pure_state <- if (isTRUE(RunStorageReworkInterpretive)) fit_write_cox(
    storage_rework_model_data_pure_state,
    "STORAGE_REWORK_TRANS",
    storage_rework_terms_pure_state,
    "08eq_cox_pure_state_depositional_storage_reworking_interval_PREV",
    "pure_state_storage_reworking"
  ) else NULL
  any_cox_model_pure_state <- fit_write_cox(
    any_model_data_pure_state,
    "ANY_STATE_EVT",
    any_terms_pure_state,
    "08dq_cox_pure_state_any_state_transition_interval_PREV",
    "pure_state_transition"
  )

  # ----------------------------------------------------------
  # Primary-versus-strict-versus-pure-state comparison outputs
  # ----------------------------------------------------------
  sensitivity_model_specs <- list(
    list(definition = "primary_ambiguity_bridged", model_scope = "principal_full_event", transition = "Stabilised floodplain -> Active domain", model = erosion_cox_model, data = erosion_model_data, event = "REACTIVATE_EVT"),
    list(definition = "strict_observed_state", model_scope = "principal_full_event", transition = "Stabilised floodplain -> Active domain", model = erosion_cox_model_pure, data = erosion_model_data_pure, event = "REACTIVATE_TRANS"),
    list(definition = "pure_state_high_support", model_scope = "principal_full_event", transition = "Stabilised floodplain -> Active domain", model = erosion_cox_model_pure_state, data = erosion_model_data_pure_state, event = "REACTIVATE_TRANS"),
    list(definition = "primary_ambiguity_bridged", model_scope = "principal_full_event", transition = "Active domain -> Depositional storage", model = deposition_cox_model, data = deposition_model_data, event = "STORAGE_EVT"),
    list(definition = "strict_observed_state", model_scope = "principal_full_event", transition = "Active domain -> Depositional storage", model = deposition_cox_model_pure, data = deposition_model_data_pure, event = "STORAGE_TRANS"),
    list(definition = "pure_state_high_support", model_scope = "principal_full_event", transition = "Active domain -> Depositional storage", model = deposition_cox_model_pure_state, data = deposition_model_data_pure_state, event = "STORAGE_TRANS"),
    list(definition = "primary_ambiguity_bridged", model_scope = "local_geometry_subset", transition = "Active domain -> Depositional storage (local-position subset)", model = deposition_cox_model_local, data = deposition_local_model_data, event = "STORAGE_EVT"),
    list(definition = "strict_observed_state", model_scope = "local_geometry_subset", transition = "Active domain -> Depositional storage (local-position subset)", model = deposition_cox_model_local_pure, data = deposition_local_model_data_pure, event = "STORAGE_TRANS"),
    list(definition = "pure_state_high_support", model_scope = "local_geometry_subset", transition = "Active domain -> Depositional storage (local-position subset)", model = deposition_cox_model_local_pure_state, data = deposition_local_model_data_pure_state, event = "STORAGE_TRANS"),
    list(definition = "primary_ambiguity_bridged", model_scope = "principal_full_event", transition = "Depositional storage -> Stabilised floodplain", model = stabilise_cox_model, data = stabilise_model_data, event = "STABILISE_EVT"),
    list(definition = "strict_observed_state", model_scope = "principal_full_event", transition = "Depositional storage -> Stabilised floodplain", model = stabilise_cox_model_pure, data = stabilise_model_data_pure, event = "STABILISE_TRANS"),
    list(definition = "pure_state_high_support", model_scope = "principal_full_event", transition = "Depositional storage -> Stabilised floodplain", model = stabilise_cox_model_pure_state, data = stabilise_model_data_pure_state, event = "STABILISE_TRANS"),
    list(definition = "primary_ambiguity_bridged", model_scope = "principal_full_event", transition = "Depositional storage -> Active domain", model = storage_rework_cox_model, data = storage_rework_model_data, event = "STORAGE_REWORK_EVT"),
    list(definition = "strict_observed_state", model_scope = "principal_full_event", transition = "Depositional storage -> Active domain", model = storage_rework_cox_model_pure, data = storage_rework_model_data_pure, event = "STORAGE_REWORK_TRANS"),
    list(definition = "pure_state_high_support", model_scope = "principal_full_event", transition = "Depositional storage -> Active domain", model = storage_rework_cox_model_pure_state, data = storage_rework_model_data_pure_state, event = "STORAGE_REWORK_TRANS"),
    list(definition = "primary_ambiguity_bridged", model_scope = "principal_full_event", transition = "Any named/state transition", model = any_cox_model, data = any_model_data, event = "ANY_CONFIRMED_EVT"),
    list(definition = "strict_observed_state", model_scope = "principal_full_event", transition = "Any named/state transition", model = any_cox_model_pure, data = any_model_data_pure, event = "ANY_STATE_EVT"),
    list(definition = "pure_state_high_support", model_scope = "principal_full_event", transition = "Any named/state transition", model = any_cox_model_pure_state, data = any_model_data_pure_state, event = "ANY_STATE_EVT")
  )

  # [FRAF archive / Historic/QA function: extract_sensitivity_model_summary]
  # Create comparable fit, AIC and concordance summaries for model-definition sensitivity.
  extract_sensitivity_model_summary <- function(spec) {
    dat <- spec$data
    mod <- spec$model
    n_rows <- if (is.null(dat)) 0L else nrow(dat)
    n_events <- if (!is.null(dat) && spec$event %in% names(dat)) sum(dat[[spec$event]] == 1L, na.rm = TRUE) else NA_integer_
    if (is.null(mod)) {
      return(tibble::tibble(
        definition = spec$definition, model_scope = spec$model_scope, transition = spec$transition,
        n_rows = n_rows, n_events = n_events, concordance = NA_real_,
        concordance_se = NA_real_, log_likelihood = NA_real_, AIC = NA_real_,
        pure_state_min_support = ifelse(spec$definition == "pure_state_high_support", PureStateMinSupport, NA_real_),
        status = "not_fitted"
      ))
    }
    sm <- summary(mod)
    conc <- sm$concordance
    tibble::tibble(
      definition = spec$definition, model_scope = spec$model_scope, transition = spec$transition,
      n_rows = n_rows, n_events = n_events,
      concordance = if (length(conc) >= 1L) as.numeric(conc[1]) else NA_real_,
      concordance_se = if (length(conc) >= 2L) as.numeric(conc[2]) else NA_real_,
      log_likelihood = if (length(mod$loglik) >= 2L) as.numeric(mod$loglik[2]) else NA_real_,
      AIC = tryCatch(stats::AIC(mod), error = function(e) NA_real_),
      pure_state_min_support = ifelse(spec$definition == "pure_state_high_support", PureStateMinSupport, NA_real_),
      status = "fitted"
    )
  }

  # [FRAF archive / Historic/QA function: extract_sensitivity_coefficients]
  # Extract sensitivity-model coefficients and uncertainties in tidy form.
  extract_sensitivity_coefficients <- function(spec) {
    if (is.null(spec$model)) return(NULL)
    broom::tidy(spec$model, exponentiate = TRUE, conf.int = TRUE) %>%
      mutate(
        definition = spec$definition,
        model_scope = spec$model_scope,
        transition = spec$transition,
        pure_state_min_support = ifelse(spec$definition == "pure_state_high_support", PureStateMinSupport, NA_real_),
        .before = 1
      )
  }

  definition_sensitivity_model_summary <- bind_rows(lapply(sensitivity_model_specs, extract_sensitivity_model_summary))
  definition_sensitivity_coefficients <- bind_rows(lapply(sensitivity_model_specs, extract_sensitivity_coefficients))
  write_csv(definition_sensitivity_model_summary, file.path(out_dir, "08s_primary_strict_pure_model_summary.csv"))
  write_csv(definition_sensitivity_coefficients, file.path(out_dir, "08s_primary_strict_pure_coefficients.csv"))

  if (isTRUE(RunDefinitionSensitivity) && nrow(definition_sensitivity_coefficients) > 0L) {
    definition_plot_data <- definition_sensitivity_coefficients %>%
      filter(
        model_scope == "principal_full_event",
        is.finite(estimate), estimate > 0,
        !grepl("^cluster\\(", term),
        !grepl("^strata\\(", term),
        term != "(Intercept)"
      ) %>%
      mutate(
        term_label = gsub("_", " ", term),
        definition = factor(
          definition,
          levels = c("primary_ambiguity_bridged", "strict_observed_state", "pure_state_high_support"),
          labels = c("Primary ambiguity-bridged", "Strict observed-state", paste0("Pure state (support >= ", format(PureStateMinSupport, trim = TRUE), ")"))
        )
      )
    if (nrow(definition_plot_data) > 0L) {
      write_csv(definition_plot_data, file.path(out_dir, "08s_primary_strict_pure_forest_table.csv"))
      p_definition_sensitivity <- ggplot(
        definition_plot_data,
        aes(x = term_label, y = estimate, ymin = conf.low, ymax = conf.high, shape = definition)
      ) +
        geom_hline(yintercept = 1, linetype = "dashed", colour = "grey40") +
        geom_pointrange(position = position_dodge(width = 0.65), linewidth = 0.35, na.rm = TRUE) +
        coord_flip() +
        facet_wrap(~ transition, scales = "free_y") +
        scale_y_log10() +
        labs(
          title = paste0(reach_label, ": primary, strict and pure-state Cox sensitivity"),
          subtitle = paste0("Pure-state endpoint support threshold = ", format(PureStateMinSupport, trim = TRUE)),
          x = NULL, y = "Hazard ratio (log scale)", shape = "Event/state definition"
        ) +
        theme_bw(base_size = 11) +
        theme(panel.grid.minor = element_blank(), legend.position = "bottom")
      safe_plot_save(p_definition_sensitivity, "08s_primary_strict_pure_hazard_ratio_forest.png", width = 12, height = 10)
    }

    local_definition_plot_data <- definition_sensitivity_coefficients %>%
      filter(
        model_scope == "local_geometry_subset",
        is.finite(estimate), estimate > 0,
        !grepl("^cluster\\(", term),
        !grepl("^strata\\(", term),
        term != "(Intercept)"
      ) %>%
      mutate(
        term_label = gsub("_", " ", term),
        definition = factor(
          definition,
          levels = c("primary_ambiguity_bridged", "strict_observed_state", "pure_state_high_support"),
          labels = c("Primary ambiguity-bridged", "Strict observed-state", paste0("Pure state (support >= ", format(PureStateMinSupport, trim = TRUE), ")"))
        )
      )
    if (nrow(local_definition_plot_data) > 0L) {
      write_csv(local_definition_plot_data, file.path(out_dir, "08sl_storage_local_primary_strict_pure_forest_table.csv"))
      p_local_definition_sensitivity <- ggplot(
        local_definition_plot_data,
        aes(x = term_label, y = estimate, ymin = conf.low, ymax = conf.high, shape = definition)
      ) +
        geom_hline(yintercept = 1, linetype = "dashed", colour = "grey40") +
        geom_pointrange(position = position_dodge(width = 0.65), linewidth = 0.35, na.rm = TRUE) +
        coord_flip() +
        scale_y_log10() +
        labs(
          title = paste0(reach_label, ": local-position storage sensitivity"),
          subtitle = paste0("Explicit local-geometry subset; pure-state support threshold = ", format(PureStateMinSupport, trim = TRUE)),
          x = NULL, y = "Hazard ratio (log scale)", shape = "Event/state definition"
        ) +
        theme_bw(base_size = 11) +
        theme(panel.grid.minor = element_blank(), legend.position = "bottom")
      safe_plot_save(p_local_definition_sensitivity, "08sl_storage_local_primary_strict_pure_hazard_ratio_forest.png", width = 10, height = 8)
    }
  }

  # ----------------------------------------------------------
  # Previous-observation temporal sensitivity models
  # ----------------------------------------------------------
  # These models compare the valid interval-start distance, the same measure at
  # y0, and the pre-y1 approach rate. They are diagnostic and do not replace the
  # transition-specific principal models above.
  temporal_sensitivity_rows <- list()

  # [FRAF archive / code note]
  # Temporal sensitivity uses previous-observation exposure only.
  # PH failure qualifies record-wide hazard-ratio interpretation.
  # [FRAF archive / Historic/QA function: choose_temporal_distance]
  # Select a usable interval-start distance term for temporal/PH sensitivity.
  choose_temporal_distance <- function(candidates) {
    hit <- candidates[candidates %in% names(cox_data)]
    hit <- hit[paste0(hit, "_Y0") %in% names(cox_data)]
    if (length(hit) == 0L) return(NA_character_)
    hit[1]
  }

  # [FRAF archive / Historic/QA function: fit_temporal_sensitivity]
  # Assess changes in conditional effects between early, middle and late record periods.
  fit_temporal_sensitivity <- function(dat, event_field, transition, distance_field) {
    if (!isTRUE(RunTemporalSensitivity) || is.na(distance_field) || nrow(dat) == 0L ||
        !event_field %in% names(dat) || sum(dat[[event_field]] == 1L, na.rm = TRUE) == 0L) return(NULL)

    y0_field <- paste0(distance_field, "_Y0")
    rate_field <- paste0(distance_field, "_APPROACH_M_PER_YR")
    if (!all(c(distance_field, y0_field, rate_field) %in% names(dat))) return(NULL)

    d <- dat %>%
      transmute(
        PLACE_ID, tstart_yr, tstop_yr,
        event = int01(.data[[event_field]]),
        T1_LOGKM = log1p(pmax(0, num_or_na(.data[[distance_field]])) / 1000),
        Y0_LOGKM = log1p(pmax(0, num_or_na(.data[[y0_field]])) / 1000),
        APPROACH_KM_PER_YR = num_or_na(.data[[rate_field]]) / 1000
      )
    d$T1_LOGKM_Z <- zscore_preserve_na(d$T1_LOGKM)
    d$Y0_LOGKM_Z <- zscore_preserve_na(d$Y0_LOGKM)
    d$APPROACH_KM_PER_YR_Z <- zscore_preserve_na(d$APPROACH_KM_PER_YR)

    variants <- list(
      interval_start = c("T1_LOGKM_Z"),
      previous_observation = c("Y0_LOGKM_Z"),
      interval_start_plus_approach = c("T1_LOGKM_Z", "APPROACH_KM_PER_YR_Z")
    )

    bind_rows(lapply(names(variants), function(vn) {
      terms <- variants[[vn]]
      dd <- d %>% filter(if_all(all_of(terms), ~ is.finite(.x)))
      if (nrow(dd) == 0L || sum(dd$event == 1L, na.rm = TRUE) == 0L ||
          any(vapply(terms, function(tm) {
            ss <- stats::sd(dd[[tm]], na.rm = TRUE)
            !is.finite(ss) || ss == 0
          }, logical(1)))) {
        return(tibble::tibble(
          transition = .env$transition, distance_field = .env$distance_field, model_variant = .env$vn,
          term = NA_character_, estimate = NA_real_, conf.low = NA_real_, conf.high = NA_real_,
          p.value = NA_real_, n = nrow(dd), events = sum(dd$event == 1L, na.rm = TRUE),
          concordance = NA_real_, status = "not fitted"
        ))
      }
      form <- stats::as.formula(paste0(
        "Surv(tstart_yr, tstop_yr, event) ~ ", paste(terms, collapse = " + "),
        " + cluster(PLACE_ID)"
      ))
      mod <- tryCatch(
        survival::coxph(form, data = dd, ties = "efron", x = TRUE),
        error = function(e) NULL
      )
      if (is.null(mod)) {
        return(tibble::tibble(
          transition = .env$transition, distance_field = .env$distance_field, model_variant = .env$vn,
          term = NA_character_, estimate = NA_real_, conf.low = NA_real_, conf.high = NA_real_,
          p.value = NA_real_, n = nrow(dd), events = sum(dd$event == 1L, na.rm = TRUE),
          concordance = NA_real_, status = "fit failed"
        ))
      }
      conc <- summary(mod)$concordance
      broom::tidy(mod, exponentiate = TRUE, conf.int = TRUE) %>%
        mutate(
          transition = .env$transition,
          distance_field = .env$distance_field,
          model_variant = .env$vn,
          n = as.integer(mod$n),
          events = as.integer(mod$nevent),
          concordance = if (length(conc) >= 1L) as.numeric(conc[1]) else NA_real_,
          status = "fitted",
          .before = 1
        )
    }))
  }

  react_temporal_field <- if (use_local_mamore_geometry) {
    choose_temporal_distance(c("DIST_CHANNEL_PREV", "DIST_CL_PREV", "DIST_ACTIVE_CURR"))
  } else {
    choose_temporal_distance(c("DIST_ACTIVE_CURR", "DIST_CL_REF", "DIST_CL_CURR", "DIST_WATER_CURR"))
  }
  storage_temporal_field <- if (use_local_mamore_geometry) {
    choose_temporal_distance(c("DIST_BANK_PREV", "DIST_CHANNEL_PREV", "DIST_CL_PREV"))
  } else {
    choose_temporal_distance(c("DIST_ACTIVE_CURR", "DIST_WATER_CURR", "DIST_CL_REF", "DIST_CL_CURR"))
  }
  stabilise_temporal_field <- if (use_local_mamore_geometry) {
    choose_temporal_distance(c("DIST_CHANNEL_PREV", "DIST_BANK_PREV", "DIST_CL_PREV"))
  } else {
    choose_temporal_distance(c("DIST_ACTIVE_CURR", "DIST_WATER_CURR", "DIST_CL_REF", "DIST_CL_CURR"))
  }

  temporal_sensitivity_rows[[length(temporal_sensitivity_rows) + 1L]] <- fit_temporal_sensitivity(
    cox_data %>% filter(REACTIVATE_RISK_SET == 1L), "REACTIVATE_EVT",
    "Stabilised floodplain to Active Domain", react_temporal_field
  )
  temporal_sensitivity_rows[[length(temporal_sensitivity_rows) + 1L]] <- fit_temporal_sensitivity(
    cox_data %>% filter(BASE_REACTIVATE_RISK_SET_DERIVED == 1L), "BASE_REACTIVATE_EVT",
    "Initial floodplain to Active Domain", react_temporal_field
  )
  temporal_sensitivity_rows[[length(temporal_sensitivity_rows) + 1L]] <- fit_temporal_sensitivity(
    cox_data %>% filter(STORAGE_RISK_SET == 1L), "STORAGE_EVT",
    "Active Domain to Depositional Storage", storage_temporal_field
  )
  temporal_sensitivity_rows[[length(temporal_sensitivity_rows) + 1L]] <- fit_temporal_sensitivity(
    cox_data %>% filter(STABILISE_RISK_SET == 1L), "STABILISE_EVT",
    "Depositional Storage to Stabilised Floodplain", stabilise_temporal_field
  )

  temporal_sensitivity_results <- bind_rows(temporal_sensitivity_rows)
  if (nrow(temporal_sensitivity_results) == 0L) {
    temporal_sensitivity_results <- tibble::tibble(
      transition = NA_character_, distance_field = NA_character_, model_variant = NA_character_,
      term = NA_character_, estimate = NA_real_, conf.low = NA_real_, conf.high = NA_real_,
      p.value = NA_real_, n = 0L, events = 0L, concordance = NA_real_,
      status = if (isTRUE(RunTemporalSensitivity)) "no usable y0 sensitivity fields" else "disabled"
    )
  }
  write_csv(temporal_sensitivity_results, file.path(out_dir, "08t_previous_observation_temporal_sensitivity.csv"))

  # Optional T2 negative-control models use the next contiguous interval-start
  # value as the current interval-end exposure. Outputs are clearly separated
  # from principal models and are deliberately outcome-contaminated diagnostics.
  t2_negative_control_results <- list()
  available_t2 <- t2_negative_control_candidates %>% filter(available)
  if (nrow(available_t2) > 0L && isTRUE(RunTemporalSensitivity)) {
    for (jj in seq_len(nrow(available_t2))) {
      t1f <- available_t2$t1_field[jj]
      t2f <- available_t2$t2_field[jj]
      dd <- cox_data %>%
        filter(REACTIVATE_RISK_SET == 1L) %>%
        transmute(
          PLACE_ID, tstart_yr, tstop_yr, event = REACTIVATE_EVT,
          T1_LOGKM_Z = zscore_preserve_na(log1p(pmax(0, num_or_na(.data[[t1f]])) / 1000)),
          T2_LOGKM_Z = zscore_preserve_na(log1p(pmax(0, num_or_na(.data[[t2f]])) / 1000))
        )
      for (tm in c("T1_LOGKM_Z", "T2_LOGKM_Z")) {
        dfit <- dd %>% filter(is.finite(.data[[tm]]))
        if (nrow(dfit) == 0L || sum(dfit$event == 1L, na.rm = TRUE) == 0L) next
        tm_sd <- stats::sd(dfit[[tm]], na.rm = TRUE)
        if (!is.finite(tm_sd) || tm_sd == 0) next
        form <- stats::as.formula(paste0("Surv(tstart_yr, tstop_yr, event) ~ ", tm, " + cluster(PLACE_ID)"))
        mod <- tryCatch(survival::coxph(form, data = dfit, ties = "efron", x = TRUE), error = function(e) NULL)
        if (is.null(mod)) next
        t2_negative_control_results[[length(t2_negative_control_results) + 1L]] <- broom::tidy(mod, exponentiate = TRUE, conf.int = TRUE) %>%
          mutate(
            comparison = ifelse(tm == "T1_LOGKM_Z", "valid interval-start predictor", "diagnostic outcome-time negative control"),
            t1_field = t1f, t2_field = t2f, n = mod$n, events = mod$nevent, .before = 1
          )
      }
    }
  }
  t2_negative_control_table <- bind_rows(t2_negative_control_results)
  if (nrow(t2_negative_control_table) == 0L) {
    t2_negative_control_table <- tibble::tibble(
      comparison = "not available", t1_field = NA_character_, t2_field = NA_character_,
      n = 0L, events = 0L, term = NA_character_, estimate = NA_real_,
      std.error = NA_real_, statistic = NA_real_, p.value = NA_real_,
      conf.low = NA_real_, conf.high = NA_real_
    )
  }
  write_csv(t2_negative_control_table, file.path(out_dir, "08t_T2_negative_control_models.csv"))

  # [FRAF archive / Historic/QA function: summarise_cox_fit]
  # Consolidate fitted model quality and event-population metadata into the results table.
  summarise_cox_fit <- function(mod, model_name, transition_label, model_type) {
    if (is.null(mod)) {
      return(tibble(
        model = model_name,
        transition = transition_label,
        model_type = model_type,
        n = NA_integer_,
        events = NA_integer_,
        concordance = NA_real_,
        concordance_se = NA_real_,
        status = "not fitted"
      ))
    }
    sm <- summary(mod)
    conc <- sm$concordance
    tibble(
      model = model_name,
      transition = transition_label,
      model_type = model_type,
      n = as.integer(mod$n),
      events = as.integer(mod$nevent),
      concordance = if (length(conc) >= 1) as.numeric(conc[1]) else NA_real_,
      concordance_se = if (length(conc) >= 2) as.numeric(conc[2]) else NA_real_,
      status = "fitted"
    )
  }

  cox_model_summary <- bind_rows(
    summarise_cox_fit(
      erosion_cox_model,
      "active_domain_reactivation",
      "Stabilised floodplain -> Active domain",
      "primary ambiguity-bridged"
    ),
    summarise_cox_fit(
      baseline_reactivate_cox_model,
      "initial_floodplain_reactivation",
      "Initial floodplain -> Active domain",
      "first-event cohort"
    ),
    summarise_cox_fit(
      deposition_cox_model,
      "depositional_storage_full_event",
      "Active domain -> Depositional storage",
      "primary ambiguity-bridged full-event"
    ),
    summarise_cox_fit(
      deposition_cox_model_local,
      "depositional_storage_local_position_subset",
      "Active domain -> Depositional storage (local-position subset)",
      "primary ambiguity-bridged local subset"
    ),
    summarise_cox_fit(
      stabilise_cox_model,
      "floodplain_stabilisation",
      "Depositional storage -> Stabilised floodplain",
      "state transition"
    ),
    summarise_cox_fit(
      any_cox_model,
      "any_named_primary_transition",
      "Any named primary transition",
      "primary ambiguity-bridged"
    ),
    summarise_cox_fit(
      erosion_cox_model_pure,
      "state_only_active_domain_reactivation",
      "Stabilised floodplain -> Active domain",
      "state-only"
    ),
    summarise_cox_fit(
      deposition_cox_model_pure,
      "state_only_depositional_storage_full_event",
      "Active domain -> Depositional storage",
      "strict observed-state full-event"
    ),
    summarise_cox_fit(
      deposition_cox_model_local_pure,
      "state_only_depositional_storage_local_position_subset",
      "Active domain -> Depositional storage (local-position subset)",
      "strict observed-state local subset"
    ),
    summarise_cox_fit(
      stabilise_cox_model_pure,
      "state_only_floodplain_stabilisation",
      "Depositional storage -> Stabilised floodplain",
      "state-only"
    ),
    summarise_cox_fit(
      any_cox_model_pure,
      "state_only_any_transition",
      "Any state transition",
      "strict observed-state"
    ),
    summarise_cox_fit(
      erosion_cox_model_pure_state,
      "pure_state_active_domain_reactivation",
      "Stabilised floodplain -> Active domain",
      paste0("pure state support >= ", format(PureStateMinSupport, trim = TRUE))
    ),
    summarise_cox_fit(
      deposition_cox_model_pure_state,
      "pure_state_depositional_storage_full_event",
      "Active domain -> Depositional storage",
      paste0("pure state full-event support >= ", format(PureStateMinSupport, trim = TRUE))
    ),
    summarise_cox_fit(
      deposition_cox_model_local_pure_state,
      "pure_state_depositional_storage_local_position_subset",
      "Active domain -> Depositional storage (local-position subset)",
      paste0("pure state local subset support >= ", format(PureStateMinSupport, trim = TRUE))
    ),
    summarise_cox_fit(
      stabilise_cox_model_pure_state,
      "pure_state_floodplain_stabilisation",
      "Depositional storage -> Stabilised floodplain",
      paste0("pure state support >= ", format(PureStateMinSupport, trim = TRUE))
    ),
    summarise_cox_fit(
      any_cox_model_pure_state,
      "pure_state_any_transition",
      "Any state transition",
      paste0("pure state support >= ", format(PureStateMinSupport, trim = TRUE))
    )
  )
  write_csv(cox_model_summary, file.path(out_dir, "08_cox_model_summary.csv"))

  # [FRAF archive / Historic/QA function: tidy_significant]
  # Extract supported coefficient estimates for summary plots/tables.
  tidy_significant <- function(mod, model_name, transition_label, model_type) {
    if (is.null(mod)) return(NULL)
    broom::tidy(mod, exponentiate = TRUE, conf.int = TRUE) %>%
      filter(!is.na(p.value), p.value < 0.05) %>%
      mutate(
        model = model_name,
        transition = transition_label,
        model_type = model_type,
        .before = 1
      )
  }

  cox_significant_terms <- bind_rows(
    tidy_significant(erosion_cox_model, "active_domain_reactivation", "Stabilised floodplain -> Active domain", "primary ambiguity-bridged"),
    tidy_significant(baseline_reactivate_cox_model, "initial_floodplain_reactivation", "Initial floodplain -> Active domain", "first-event cohort"),
    tidy_significant(deposition_cox_model, "depositional_storage_full_event", "Active domain -> Depositional storage", "primary ambiguity-bridged full-event"),
    tidy_significant(deposition_cox_model_local, "depositional_storage_local_position_subset", "Active domain -> Depositional storage (local-position subset)", "primary ambiguity-bridged local subset"),
    tidy_significant(stabilise_cox_model, "floodplain_stabilisation", "Depositional storage -> Stabilised floodplain", "state transition"),
    tidy_significant(any_cox_model, "any_named_primary_transition", "Any named primary transition", "primary ambiguity-bridged"),
    tidy_significant(erosion_cox_model_pure, "state_only_active_domain_reactivation", "Stabilised floodplain -> Active domain", "state-only"),
    tidy_significant(deposition_cox_model_pure, "state_only_depositional_storage_full_event", "Active domain -> Depositional storage", "strict observed-state full-event"),
    tidy_significant(deposition_cox_model_local_pure, "state_only_depositional_storage_local_position_subset", "Active domain -> Depositional storage (local-position subset)", "strict observed-state local subset"),
    tidy_significant(stabilise_cox_model_pure, "state_only_floodplain_stabilisation", "Depositional storage -> Stabilised floodplain", "state-only"),
    tidy_significant(any_cox_model_pure, "state_only_any_transition", "Any state transition", "strict observed-state"),
    tidy_significant(erosion_cox_model_pure_state, "pure_state_active_domain_reactivation", "Stabilised floodplain -> Active domain", "pure-state high-support"),
    tidy_significant(deposition_cox_model_pure_state, "pure_state_depositional_storage_full_event", "Active domain -> Depositional storage", "pure-state high-support full-event"),
    tidy_significant(deposition_cox_model_local_pure_state, "pure_state_depositional_storage_local_position_subset", "Active domain -> Depositional storage (local-position subset)", "pure-state high-support local subset"),
    tidy_significant(stabilise_cox_model_pure_state, "pure_state_floodplain_stabilisation", "Depositional storage -> Stabilised floodplain", "pure-state high-support"),
    tidy_significant(any_cox_model_pure_state, "pure_state_any_transition", "Any state transition", "pure-state high-support")
  )
  write_if_nonempty(cox_significant_terms, "08_cox_significant_predictors.csv")


  # [FRAF archive / code note]
  # Forest plots must distinguish process-transition types and report
  # uncertainty rather than presenting rank coefficients as causal effects.
  # ============================================================
  # Cox hazard-ratio forest plots
  # ============================================================
  # fit_write_cox() writes broom::tidy(..., exponentiate = TRUE), so
  # estimate/conf.low/conf.high are already hazard ratios, not log-HRs.

  # [FRAF archive / Historic/QA function: clean_cox_term_label]
  # Format stored Cox term names for geomorphically interpretable figures.
  clean_cox_term_label <- function(x) {
    x <- as.character(x)

    x <- dplyr::recode(
      x,
      "DIST_CL_CURR_LOGKM_Z" = "Distance from dated centreline at interval start",
      "DIST_CL_PREV_LOGKM_Z" = "Local centreline distance at interval start",
      "DIST_ACTIVE_CURR_LOGKM_Z" = "Distance from Active Domain at interval start",
      "DIST_ACTIVE_PREV_LOGKM_Z" = "Active Domain distance at previous observation",
      "DIST_WATER_CURR_LOGKM_Z" = "Distance from water at interval start",
      "DIST_WATER_PREV_LOGKM_Z" = "Water distance at previous observation",
      "CURV_CL_CURR_Z" = "Dated centreline curvature at interval start",
      "CURV_CL_PREV_Z" = "Local centreline curvature at interval start",
      "CURV_EROSION_CURR_Z" = "Outer-bank curvature at interval start",
      "CURV_EROSION_PREV_Z" = "Local outer-bank curvature at interval start",
      "ASM_DOM_RATIO_LAG_Z" = "Previous dominant-state ratio",
      "ASM_DOM_RATIO_PREV_Z" = "Previous dominant-state ratio",
      "ASM_N_EPISODES_LAG_Z" = "Previous activity episodes",
      "ASM_N_EPISODES_PREV_Z" = "Previous activity episodes",
      "ASM_MAX_QUIET_LAG_Z" = "Previous maximum quiet period",
      "ASM_MAX_QUIET_PREV_Z" = "Previous maximum quiet period",
      "ASM_COV_FRAC_LAG_Z" = "Assemblage coverage fraction",
      "ASM_COV_FRAC_Z" = "Assemblage coverage fraction",
      "ASM_STORAGE_FRAC_PREV_Z" = "Previous storage fraction",
      "ASM_STAB_FP_FRAC_PREV_Z" = "Previous stabilised-floodplain fraction",
      "ASM_QUIET_SINCE_PREV_Z" = "Previous quiet duration",
      "ASM_N_REACTIVATE_PREV_Z" = "Previous reactivation events",
      "ASM_N_STORAGE_EVT_PREV_Z" = "Previous storage events",
      "ASM_N_STABILISE_PREV_Z" = "Previous stabilisation events",
      "DIST_X_CURV_EROSION_Z" = "Distance × outer-bank curvature",
      "MAM_NEAR_CHANNEL_PREV" = "Within interval-start local channel-exposure zone",
      "MAM_OUTER_REACT_EXPOSED_PREV" = "Interval-start near-channel outer-bank exposure",
      "MAM_OUTER_CURV_REACT_PREV_Z" = "Interval-start local outer-bank curvature",
      "REL_CHANNEL_POS_PREV_Z" = "Interval-start relative lateral channel position",
      "MAM_NEAR_BANK_STORAGE_PREV" = "Interval-start bank-adjacent active-channel position",
      "MAM_INNER_STORAGE_EXPOSED_PREV" = "Inner-bank storage exposure",
      "MAM_INNER_CURV_STORAGE_PREV_Z" = "Local inner-bank curvature",
      "MAM_OUTER_STORAGE_EXPOSED_PREV" = "Outer-bank storage exposure",
      "MAM_OUTER_CURV_STORAGE_PREV_Z" = "Local outer-bank storage curvature",
      "DIST_CHANNEL_PREV_LOGKM_Z" = "Distance from channel polygon at interval start",
      .default = x
    )

    x <- gsub("_LOGKM_Z$", " log-distance", x)
    x <- gsub("_PREV_Z$", " interval-start lookup", x)
    x <- gsub("_CURR_Z$", " interval start", x)
    x <- gsub("_Z$", "", x)
    x <- gsub("_PREV$", " interval-start lookup", x)
    x <- gsub("_CURR$", " interval start", x)
    x <- gsub("_", " ", x)
    x
  }

  # [FRAF archive / Historic/QA function: make_cox_forest_plot]
  # Produce a hazard-ratio forest plot from exported coefficient data.
  make_cox_forest_plot <- function(file_info, out_csv, out_png, plot_title) {
    forest_list <- list()

    for (i in seq_len(nrow(file_info))) {
      fp <- file.path(out_dir, file_info$file[i])

      if (file.exists(fp)) {
        d <- read_csv(fp, show_col_types = FALSE)

        if (nrow(d) > 0) {
          d$transition <- file_info$transition[i]
          d$model_group <- file_info$model_group[i]
          forest_list[[length(forest_list) + 1]] <- d
        }
      } else {
        message("[Cox forest] Missing model CSV: ", fp)
      }
    }

    if (length(forest_list) == 0) {
      message("[Cox forest] No model CSVs available for: ", plot_title)
      return(invisible(NULL))
    }

    cox_forest <- bind_rows(forest_list)

    if (!"term" %in% names(cox_forest) || !"estimate" %in% names(cox_forest)) {
      message("[Cox forest] Required columns term/estimate not found for: ", plot_title)
      return(invisible(NULL))
    }

    if (!"conf.low" %in% names(cox_forest)) cox_forest$conf.low <- NA_real_
    if (!"conf.high" %in% names(cox_forest)) cox_forest$conf.high <- NA_real_
    if (!"p.value" %in% names(cox_forest)) cox_forest$p.value <- NA_real_

    cox_forest <- cox_forest %>%
      mutate(
        HR = as.numeric(estimate),
        HR_low = as.numeric(conf.low),
        HR_high = as.numeric(conf.high),
        p_value = as.numeric(p.value),
        term_label = clean_cox_term_label(term),
        significant = case_when(
          !is.na(p_value) & p_value < 0.001 ~ "p < 0.001",
          !is.na(p_value) & p_value < 0.01 ~ "p < 0.01",
          !is.na(p_value) & p_value < 0.05 ~ "p < 0.05",
          TRUE ~ "n.s."
        )
      ) %>%
      filter(
        !is.na(HR),
        HR > 0,
        !grepl("^cluster\\(", term),
        !grepl("^strata\\(", term),
        !grepl("^\\(Intercept\\)$", term)
      )

    if (nrow(cox_forest) == 0) {
      message("[Cox forest] No plottable Cox terms for: ", plot_title)
      return(invisible(NULL))
    }

    write_csv(
      cox_forest,
      file.path(out_dir, out_csv)
    )

    plot_height <- min(14, max(6, 2.5 + 0.18 * nrow(cox_forest)))

    p_forest <- ggplot(
      cox_forest,
      aes(
        x = reorder(term_label, HR),
        y = HR,
        ymin = HR_low,
        ymax = HR_high
      )
    ) +
      geom_hline(
        yintercept = 1,
        linetype = "dashed",
        colour = "grey40"
      ) +
      geom_pointrange(
        aes(shape = significant),
        size = 0.45,
        linewidth = 0.45,
        na.rm = TRUE
      ) +
      coord_flip() +
      facet_wrap(
        ~ transition,
        scales = "free_y"
      ) +
      scale_y_log10() +
      labs(
        title = plot_title,
        x = NULL,
        y = "Hazard ratio (log scale)",
        shape = "Significance"
      ) +
      theme_bw(base_size = 12) +
      theme(
        panel.grid.minor = element_blank(),
        plot.title = element_text(face = "bold", hjust = 0.5),
        strip.text = element_text(face = "bold"),
        legend.position = "bottom"
      )

    safe_plot_save(
      p_forest,
      out_png,
      width = 11,
      height = plot_height
    )

    invisible(cox_forest)
  }

  cox_process_files <- tibble::tibble(
    file = c(
      "08_cox_active_domain_reactivation_interval_PREV_model.csv",
      "08a_cox_initial_floodplain_reactivation_interval_PREV_model.csv",
      "08b_cox_depositional_storage_interval_PREV_model.csv",
      "08c_cox_floodplain_stabilisation_interval_PREV_model.csv",
      "08d_cox_any_confirmed_named_transition_interval_PREV_model.csv"
    ),
    transition = c(
      "Floodplain reached by Active Domain",
      "Initial floodplain reached by Active Domain",
      "Active place became depositional storage",
      "Depositional storage became stable floodplain",
      "Any named primary transition"
    ),
    model_group = "primary_ambiguity_bridged"
  )

  cox_pure_files <- tibble::tibble(
    file = c(
      "08p_cox_state_only_active_domain_reactivation_interval_PREV_model.csv",
      "08bp_cox_state_only_depositional_storage_interval_PREV_model.csv",
      "08cp_cox_state_only_floodplain_stabilisation_interval_PREV_model.csv",
      "08dp_cox_state_only_any_state_transition_interval_PREV_model.csv"
    ),
    transition = c(
      "Stable floodplain reached by Active Domain",
      "Active place became depositional storage",
      "Depositional storage became stable floodplain",
      "Any state transition"
    ),
    model_group = "strict_observed_state"
  )

  cox_pure_state_files <- tibble::tibble(
    file = c(
      "08q_cox_pure_state_active_domain_reactivation_interval_PREV_model.csv",
      "08bq_cox_pure_state_depositional_storage_interval_PREV_model.csv",
      "08cq_cox_pure_state_floodplain_stabilisation_interval_PREV_model.csv",
      "08dq_cox_pure_state_any_state_transition_interval_PREV_model.csv"
    ),
    transition = c(
      "Stable floodplain reached by Active Domain",
      "Active place became depositional storage",
      "Depositional storage became stable floodplain",
      "Any state transition"
    ),
    model_group = "pure_state_high_support"
  )

  make_cox_forest_plot(
    cox_process_files,
    "08_cox_primary_ambiguity_bridged_hazard_ratio_forest_table.csv",
    "08_cox_primary_ambiguity_bridged_hazard_ratio_forest.png",
    "Cox hazard ratios for primary ambiguity-bridged transitions"
  )

  make_cox_forest_plot(
    cox_pure_files,
    "08p_cox_strict_observed_state_hazard_ratio_forest_table.csv",
    "08p_cox_strict_observed_state_hazard_ratio_forest.png",
    "Cox hazard ratios for strict observed-state transitions"
  )

  make_cox_forest_plot(
    cox_pure_state_files,
    "08q_cox_pure_state_hazard_ratio_forest_table.csv",
    "08q_cox_pure_state_hazard_ratio_forest.png",
    paste0("Cox hazard ratios for pure-state transitions (support >= ", format(PureStateMinSupport, trim = TRUE), ")")
  )


  if (use_local_mamore_geometry) {
    cox_storage_local_files <- tibble::tibble(
      file = c(
        "08bl_cox_depositional_storage_local_position_interval_PREV_model.csv",
        "08bpl_cox_state_only_depositional_storage_local_position_interval_PREV_model.csv",
        "08bql_cox_pure_state_depositional_storage_local_position_interval_PREV_model.csv"
      ),
      transition = "Active place became depositional storage (local-position subset)",
      model_group = c("primary_ambiguity_bridged", "strict_observed_state", "pure_state_high_support")
    )
    make_cox_forest_plot(
      cox_storage_local_files,
      "08sl_cox_storage_local_position_hazard_ratio_forest_table.csv",
      "08sl_cox_storage_local_position_hazard_ratio_forest.png",
      "Cox hazard ratios for the Mamore local-position storage subset"
    )
  }


  # [FRAF archive / code note]
  # Schoenfeld and temporal-interaction checks diagnose time-varying
  # conditional relationships; unstable period refits are not definitive effects.
  # ============================================================
  # v16.3 proportional-hazards diagnostics
  # ============================================================
  # The primary models above remain observation-period average Cox models.
  # This section:
  #   1. exports cox.zph tests in machine-readable form;
  #   2. plots scaled Schoenfeld residuals for principal spatial terms;
  #   3. splits counting-process intervals at exact thirds of the record;
  #   4. fits early/middle/late spatial coefficients while retaining the
  #      original non-spatial covariates and cluster(PLACE_ID);
  #   5. exports robust Wald tests of temporal interaction.
  #
  # Period-specific spatial models are fitted for the principal transition
  # pathways and, where available, the separate Mamoré local-position storage subset. The pooled any-transition model is intentionally
  # excluded because changes in the mixture of transition types can create
  # non-proportionality that is difficult to interpret geomorphically.

  if (exists("RunPHDiagnostics") && isTRUE(RunPHDiagnostics)) {

    message("[PH] Running proportional-hazards diagnostics and period interactions.")

    # ----------------------------------------------------------
    # General helpers
    # ----------------------------------------------------------

    # [FRAF archive / Historic/QA function: safe_name]
    # Normalise names for reusable model keys, output files or plot labels.
    safe_name <- function(x) {
      x <- gsub("[^A-Za-z0-9_]+", "_", as.character(x))
      x <- gsub("_+", "_", x)
      x <- gsub("^_|_$", "", x)
      x
    }

    # [FRAF archive / Historic/QA function: ph_term_label]
    # Relabel PH diagnostic terms to match the model and published terminology.
    ph_term_label <- function(x) {
      clean_cox_term_label(x)
    }

    model_record_bounds <- cox_data %>%
      summarise(
        record_start = min(tstart_yr, na.rm = TRUE),
        record_end = max(tstop_yr, na.rm = TRUE)
      )

    ph_record_start <- as.numeric(model_record_bounds$record_start[1])
    ph_record_end <- as.numeric(model_record_bounds$record_end[1])
    ph_record_duration <- ph_record_end - ph_record_start

    if (!is.finite(ph_record_duration) || ph_record_duration <= 0) {
      message("[PH] Diagnostics skipped: invalid observed time range.")
    } else {

      ph_cut_1 <- ph_record_start + ph_record_duration / 3
      ph_cut_2 <- ph_record_start + 2 * ph_record_duration / 3

      ph_period_boundaries <- tibble::tibble(
        period = c("Early", "Middle", "Late"),
        start_time_yr = c(ph_record_start, ph_cut_1, ph_cut_2),
        end_time_yr = c(ph_cut_1, ph_cut_2, ph_record_end),
        record_fraction_start = c(0, 1 / 3, 2 / 3),
        record_fraction_end = c(1 / 3, 2 / 3, 1)
      )

      write_csv(
        ph_period_boundaries,
        file.path(out_dir, "09_PH_period_boundaries.csv")
      )

      message(
        "[PH] Record thirds: Early ", round(ph_record_start, 3), "-", round(ph_cut_1, 3),
        "; Middle ", round(ph_cut_1, 3), "-", round(ph_cut_2, 3),
        "; Late ", round(ph_cut_2, 3), "-", round(ph_record_end, 3), " years."
      )

      # [FRAF archive / Historic/QA function: split_counting_intervals]
      # Split Andersen-Gill counting-process intervals at exact observation-period cut points.
      split_counting_intervals <- function(dat, event_field, cuts) {
        if (nrow(dat) == 0) return(dat)

        out <- dat
        out$.PH_SOURCE_ROW <- seq_len(nrow(out))
        out$.PH_SPLIT_PART <- 1L

        for (cut_value in sort(unique(as.numeric(cuts)))) {
          crossing <- which(
            is.finite(out$tstart_yr) &
              is.finite(out$tstop_yr) &
              out$tstart_yr < cut_value &
              out$tstop_yr > cut_value
          )

          if (length(crossing) == 0) next

          left <- out[crossing, , drop = FALSE]
          right <- out[crossing, , drop = FALSE]

          left$tstop_yr <- cut_value
          left[[event_field]] <- 0L
          left$.PH_SPLIT_PART <- left$.PH_SPLIT_PART * 10L + 1L

          right$tstart_yr <- cut_value
          right$.PH_SPLIT_PART <- right$.PH_SPLIT_PART * 10L + 2L

          keep <- setdiff(seq_len(nrow(out)), crossing)
          out <- dplyr::bind_rows(
            out[keep, , drop = FALSE],
            left,
            right
          )
        }

        out <- out %>%
          mutate(
            PH_PERIOD = case_when(
              tstop_yr <= ph_cut_1 ~ "Early",
              tstart_yr >= ph_cut_2 ~ "Late",
              TRUE ~ "Middle"
            ),
            PH_PERIOD = factor(
              PH_PERIOD,
              levels = c("Early", "Middle", "Late"),
              ordered = TRUE
            )
          ) %>%
          arrange(PLACE_ID, tstart_yr, tstop_yr, .PH_SOURCE_ROW, .PH_SPLIT_PART)

        crossing_after <- sum(
          (out$tstart_yr < ph_cut_1 & out$tstop_yr > ph_cut_1) |
            (out$tstart_yr < ph_cut_2 & out$tstop_yr > ph_cut_2),
          na.rm = TRUE
        )

        if (crossing_after > 0) {
          warning("[PH] ", crossing_after, " rows still cross a period boundary after splitting.")
        }

        out
      }

      # [FRAF archive / Historic/QA function: robust_linear_combination]
      # Estimate a period-specific linear effect and uncertainty from robust Cox covariance.
      robust_linear_combination <- function(mod, weights) {
        beta <- stats::coef(mod)
        V <- stats::vcov(mod)

        L <- rep(0, length(beta))
        names(L) <- names(beta)

        requested_names <- names(weights)
        if (
          length(requested_names) == 0 ||
            !all(requested_names %in% names(beta))
        ) {
          return(tibble::tibble(
            log_hr = NA_real_,
            se = NA_real_,
            HR = NA_real_,
            conf.low = NA_real_,
            conf.high = NA_real_,
            z = NA_real_,
            p.value = NA_real_
          ))
        }

        L[requested_names] <- as.numeric(weights[requested_names])

        if (any(is.na(beta[L != 0]))) {
          return(tibble::tibble(
            log_hr = NA_real_,
            se = NA_real_,
            HR = NA_real_,
            conf.low = NA_real_,
            conf.high = NA_real_,
            z = NA_real_,
            p.value = NA_real_
          ))
        }

        estimate <- sum(L * beta, na.rm = TRUE)
        variance <- as.numeric(t(L) %*% V %*% L)
        se <- if (is.finite(variance) && variance >= 0) sqrt(variance) else NA_real_
        z <- if (is.finite(se) && se > 0) estimate / se else NA_real_
        p_value <- if (is.finite(z)) 2 * stats::pnorm(abs(z), lower.tail = FALSE) else NA_real_

        tibble::tibble(
          log_hr = estimate,
          se = se,
          HR = exp(estimate),
          conf.low = exp(estimate - stats::qnorm(0.975) * se),
          conf.high = exp(estimate + stats::qnorm(0.975) * se),
          z = z,
          p.value = p_value
        )
      }

      # [FRAF archive / Historic/QA function: robust_wald_test]
      # Test specified temporal interaction terms using a robust covariance estimate.
      robust_wald_test <- function(mod, coefficient_names) {
        beta <- stats::coef(mod)
        V <- stats::vcov(mod)

        idx <- match(coefficient_names, names(beta))
        idx <- idx[!is.na(idx)]
        idx <- idx[!is.na(beta[idx])]

        if (length(idx) == 0) {
          return(tibble::tibble(
            df = 0L,
            chisq = NA_real_,
            p.value = NA_real_,
            status = "no estimable interaction coefficients"
          ))
        }

        b <- beta[idx]
        VV <- V[idx, idx, drop = FALSE]

        solution <- tryCatch(
          qr.solve(VV, b),
          error = function(e) NULL
        )

        if (is.null(solution)) {
          return(tibble::tibble(
            df = length(idx),
            chisq = NA_real_,
            p.value = NA_real_,
            status = "robust covariance matrix singular"
          ))
        }

        chisq <- as.numeric(t(b) %*% solution)
        df <- qr(VV)$rank
        p_value <- if (df > 0 && is.finite(chisq)) {
          stats::pchisq(chisq, df = df, lower.tail = FALSE)
        } else {
          NA_real_
        }

        tibble::tibble(
          df = as.integer(df),
          chisq = chisq,
          p.value = p_value,
          status = "fitted"
        )
      }

      # [FRAF archive / Historic/QA function: fit_coxph_checked]
      # Catch non-convergence, separation and unstable PH-sensitivity fits without masking model
      # failures.
      fit_coxph_checked <- function(formula, data, ties = "efron", x = TRUE) {
        fit_warnings <- character(0)
        fit_error <- NULL

        mod <- tryCatch(
          withCallingHandlers(
            survival::coxph(
              formula,
              data = data,
              ties = ties,
              x = x
            ),
            warning = function(w) {
              fit_warnings <<- c(fit_warnings, conditionMessage(w))
              invokeRestart("muffleWarning")
            }
          ),
          error = function(e) {
            fit_error <<- conditionMessage(e)
            NULL
          }
        )

        warning_text <- paste(unique(fit_warnings), collapse = " | ")
        if (!is.null(fit_error)) {
          warning_text <- paste(c(warning_text, fit_error)[nzchar(c(warning_text, fit_error))], collapse = " | ")
        }

        if (is.null(mod)) {
          return(list(
            model = NULL,
            converged = FALSE,
            status = "error",
            warning_text = warning_text
          ))
        }

        warning_nonconvergence <- any(grepl(
          "ran out of iterations|did not converge|coefficient.*infinite|infinite coefficient|singular",
          fit_warnings,
          ignore.case = TRUE
        ))

        beta <- tryCatch(stats::coef(mod), error = function(e) numeric(0))
        covariance <- tryCatch(stats::vcov(mod), error = function(e) NULL)
        coefficients_ok <- length(beta) > 0 && all(is.finite(beta))
        covariance_ok <- !is.null(covariance) && length(covariance) > 0 && all(is.finite(covariance))
        converged <- !warning_nonconvergence && coefficients_ok && covariance_ok

        status <- if (converged) {
          "fitted"
        } else if (warning_nonconvergence) {
          "non-convergent warning"
        } else if (!coefficients_ok) {
          "non-finite coefficient"
        } else {
          "invalid covariance"
        }

        list(
          model = mod,
          converged = converged,
          status = status,
          warning_text = warning_text
        )
      }

      # [FRAF archive / Historic/QA function: save_base_graphics]
      # Save base-R plots to raster/vector formats with device shutdown safeguards.
      save_base_graphics <- function(draw_fun, png_file, pdf_file, width, height, res = 220) {
        pdf_device <- NA_integer_
        pdf_ok <- tryCatch({
          grDevices::pdf(pdf_file, width = width, height = height, onefile = TRUE)
          pdf_device <- grDevices::dev.cur()
          draw_fun()
          grDevices::dev.off(pdf_device)
          pdf_device <- NA_integer_
          TRUE
        }, error = function(e) {
          message("[PH plot] PDF failed for ", basename(pdf_file), ": ", conditionMessage(e))
          if (is.finite(pdf_device) && pdf_device > 1) {
            try(grDevices::dev.off(pdf_device), silent = TRUE)
          }
          FALSE
        })

        png_device <- NA_integer_
        png_ok <- tryCatch({
          grDevices::png(
            filename = png_file,
            width = width,
            height = height,
            units = "in",
            res = res,
            bg = "white"
          )
          png_device <- grDevices::dev.cur()
          draw_fun()
          grDevices::dev.off(png_device)
          png_device <- NA_integer_
          TRUE
        }, error = function(e) {
          message("[PH plot] PNG failed for ", basename(png_file), ": ", conditionMessage(e))
          if (is.finite(png_device) && png_device > 1) {
            try(grDevices::dev.off(png_device), silent = TRUE)
          }
          FALSE
        })

        invisible(pdf_ok || png_ok)
      }

      # [FRAF archive / Historic/QA function: export_schoenfeld_diagnostics]
      # Export Schoenfeld residual/PH tests and selected term-specific diagnostic plots.
      export_schoenfeld_diagnostics <- function(
        mod,
        model_name,
        transition_label,
        spatial_terms,
        filename_stem
      ) {
        if (is.null(mod)) return(NULL)

        zph <- tryCatch(
          survival::cox.zph(mod, transform = "identity", terms = TRUE, singledf = FALSE),
          error = function(e) {
            message("[PH] cox.zph failed for ", model_name, ": ", conditionMessage(e))
            NULL
          }
        )
        if (is.null(zph)) return(NULL)

        zph_table <- as.data.frame(zph$table)
        zph_table$term <- rownames(zph_table)
        rownames(zph_table) <- NULL

        zph_table <- tibble::as_tibble(zph_table) %>%
          rename_with(
            ~ dplyr::recode(
              .x,
              chisq = "chisq",
              df = "df",
              p = "p.value",
              .default = .x
            )
          ) %>%
          mutate(
            model = model_name,
            transition = transition_label,
            term_label = ifelse(term == "GLOBAL", "Global test", ph_term_label(term)),
            .before = 1
          )

        write_csv(
          zph_table,
          file.path(out_dir, paste0(filename_stem, "_PH_test.csv"))
        )

        capture.output(
          zph,
          file = file.path(out_dir, paste0(filename_stem, "_PH_test.txt"))
        )

        available_terms <- colnames(zph$y)
        plot_terms <- spatial_terms[spatial_terms %in% available_terms]

        if (length(plot_terms) == 0) {
          message("[PH] No requested spatial terms available in cox.zph plot for ", model_name)
          return(zph_table)
        }

        n_panels <- length(plot_terms)
        plot_width <- max(6.5, 4.8 * n_panels)
        plot_height <- 5.6

        # [FRAF archive / Historic/QA function: draw_fun]
        # Render the specified residual trend figure inside the guarded graphics export.
        draw_fun <- function() {
          old_par <- graphics::par(no.readonly = TRUE)
          on.exit(graphics::par(old_par), add = TRUE)

          graphics::par(
            mfrow = c(1, n_panels),
            mar = c(4.7, 4.8, 4.0, 1.2),
            oma = c(0, 0, 2.0, 0)
          )

          for (tm in plot_terms) {
            tm_index <- match(tm, available_terms)
            graphics::plot(
              zph,
              var = tm_index,
              resid = FALSE,
              se = TRUE,
              df = 4,
              nsmo = 60,
              xlab = "Elapsed observation time (years)",
              ylab = expression(beta(t)),
              main = ph_term_label(tm)
            )
            graphics::abline(
              h = stats::coef(mod)[tm],
              lty = 2,
              lwd = 1.2,
              col = "grey30"
            )
            graphics::abline(
              v = c(ph_cut_1, ph_cut_2),
              lty = 3,
              lwd = 0.9,
              col = "grey55"
            )
          }

          graphics::mtext(
            transition_label,
            side = 3,
            outer = TRUE,
            line = 0.4,
            font = 2,
            cex = 1.1
          )
        }

        save_base_graphics(
          draw_fun = draw_fun,
          png_file = file.path(out_dir, paste0(filename_stem, "_Schoenfeld.png")),
          pdf_file = file.path(out_dir, paste0(filename_stem, "_Schoenfeld.pdf")),
          width = plot_width,
          height = plot_height
        )

        zph_table
      }

      # --------------------------------------------------------
      # Export Schoenfeld tests and principal-spatial plots for
      # the observation-period average models.
      # --------------------------------------------------------

      ph_model_specs <- list(
        list(
          mod = broad_reactivation_cox_model,
          data = broad_reactivation_model_data,
          event = "FP_REACTIVATE_EVT",
          terms = broad_reactivation_terms,
          model = "floodplain_reactivation_broad",
          transition = "Eligible Floodplain -> Active Domain",
          spatial_terms = c("DIST_ACTIVE_CURR_LOGKM_Z", "DIST_ACTIVE_CURR_Z", "DIST_ACTIVE_CURR"),
          spatial_framework = "broad eligible floodplain; interval-start active-domain distance",
          prefix = "09aa_PH_floodplain_reactivation_broad",
          run_period_interactions = FALSE
        ),
        list(
          mod = erosion_cox_model,
          data = erosion_model_data,
          event = "REACTIVATE_EVT",
          terms = erosion_terms,
          model = "active_domain_reactivation",
          transition = "Stabilised floodplain -> Active domain",
          spatial_terms = reactivation_spatial_candidates,
          spatial_framework = reactivation_spatial_framework,
          prefix = "09a_PH_active_domain_reactivation"
        ),
        list(
          mod = baseline_reactivate_cox_model,
          data = baseline_reactivate_model_data,
          event = "BASE_REACTIVATE_EVT",
          terms = baseline_reactivate_terms,
          model = "initial_floodplain_reactivation",
          transition = "Initial floodplain -> Active domain",
          spatial_terms = reactivation_spatial_candidates,
          spatial_framework = reactivation_spatial_framework,
          prefix = "09b_PH_initial_floodplain_reactivation",
          run_period_interactions = FALSE
        ),
        list(
          mod = deposition_cox_model,
          data = deposition_model_data,
          event = "STORAGE_EVT",
          terms = deposition_terms,
          model = "depositional_storage_full_event",
          transition = "Active domain -> Depositional storage",
          spatial_terms = storage_full_spatial_candidates,
          spatial_framework = storage_full_spatial_framework,
          prefix = "09c_PH_depositional_storage_full_event"
        ),
        list(
          mod = deposition_cox_model_local,
          data = deposition_local_model_data,
          event = "STORAGE_EVT",
          terms = deposition_local_terms,
          model = "depositional_storage_local_position_subset",
          transition = "Active domain -> Depositional storage (local-position subset)",
          spatial_terms = storage_local_spatial_candidates,
          spatial_framework = storage_local_spatial_framework,
          prefix = "09cl_PH_depositional_storage_local_position"
        ),
        list(
          mod = stabilise_cox_model,
          data = stabilise_model_data,
          event = "STABILISE_EVT",
          terms = stabilise_terms,
          model = "floodplain_stabilisation",
          transition = "Depositional storage -> Stabilised floodplain",
          spatial_terms = stabilise_spatial_candidates,
          spatial_framework = stabilise_spatial_framework,
          prefix = "09d_PH_floodplain_stabilisation"
        ),
        list(
          mod = storage_rework_cox_model,
          data = storage_rework_model_data,
          event = "STORAGE_REWORK_EVT",
          terms = storage_rework_terms,
          model = "depositional_storage_reworking",
          transition = "Depositional storage -> Active domain",
          spatial_terms = storage_rework_spatial_candidates,
          spatial_framework = storage_rework_spatial_framework,
          prefix = "09e_PH_depositional_storage_reworking"
        )
      )

      all_ph_tests <- list()
      all_period_hr <- list()
      all_interaction_tests <- list()
      all_period_model_summary <- list()

      for (spec in ph_model_specs) {

        stale_period_outputs <- file.path(
          out_dir,
          paste0(
            spec$prefix,
            c(
              "_period_interaction_model.csv",
              "_period_interaction_model_summary.txt",
              "_period_spatial_HR.csv",
              "_period_spatial_HR.png"
            )
          )
        )
        unlink(stale_period_outputs[file.exists(stale_period_outputs)], force = TRUE)

        model_spatial_terms <- intersect(spec$spatial_terms, spec$terms)

        ph_test <- export_schoenfeld_diagnostics(
          mod = spec$mod,
          model_name = spec$model,
          transition_label = spec$transition,
          spatial_terms = model_spatial_terms,
          filename_stem = spec$prefix
        )

        if (!is.null(ph_test)) {
          all_ph_tests[[length(all_ph_tests) + 1]] <- ph_test
        }

        # v17.10.12: Period-interaction refits can multiply already multi-million-row
        # risk sets and were the dominant historic memory/disk-I/O bottleneck. The
        # observation-period Cox model and Schoenfeld diagnostics above are retained.
        # Broad eligible-floodplain and initial-floodplain models are therefore not
        # re-fit as Early/Middle/Late interaction models.
        if (!is.null(spec$run_period_interactions) && identical(spec$run_period_interactions, FALSE)) {
          message(
            "[PH period] Skipped ", spec$model,
            ": period-interaction refit disabled in v17.10.12 memory-safe mode; ",
            "overall Cox and Schoenfeld diagnostics retained."
          )
          next
        }

        # Automatic protection for very large historic counting-process frames.
        # Splitting these rows into record thirds can create several million rows
        # and force large temporary Cox design matrices. Keep the global PH test
        # but defer period-specific refitting to a dedicated sensitivity run.
        if (!is.null(spec$data) && nrow(spec$data) > 1000000L) {
          message(
            "[PH period] Skipped ", spec$model, ": ", nrow(spec$data),
            " rows exceed the v17.10.12 1,000,000-row period-refit ceiling; ",
            "overall Cox and Schoenfeld diagnostics retained."
          )
          next
        }

        if (
          is.null(spec$mod) ||
            nrow(spec$data) == 0 ||
            length(model_spatial_terms) == 0 ||
            sum(spec$data[[spec$event]] == 1, na.rm = TRUE) == 0
        ) {
          message("[PH period] Skipped ", spec$model, ": no fitted model, data, spatial term or event.")
          next
        }

        period_data <- split_counting_intervals(
          dat = spec$data,
          event_field = spec$event,
          cuts = c(ph_cut_1, ph_cut_2)
        )

        # Early is the reference period. The original spatial coefficient is
        # therefore the Early effect; added columns are deviations in Middle
        # and Late periods.
        interaction_columns <- character(0)

        for (tm in model_spatial_terms) {
          middle_name <- paste0(tm, "__PH_MIDDLE")
          late_name <- paste0(tm, "__PH_LATE")

          period_data[[middle_name]] <- as.numeric(period_data[[tm]]) *
            as.integer(period_data$PH_PERIOD == "Middle")
          period_data[[late_name]] <- as.numeric(period_data[[tm]]) *
            as.integer(period_data$PH_PERIOD == "Late")

          interaction_columns <- c(interaction_columns, middle_name, late_name)
        }

        period_terms <- unique(c(spec$terms, interaction_columns))
        period_terms <- keep_varying(period_data, period_terms)

        if (length(period_terms) == 0) {
          message("[PH period] Skipped ", spec$model, ": no varying period-model terms.")
          next
        }

        period_data <- period_data %>%
          filter(if_all(all_of(period_terms), ~ !is.na(.x)))

        period_formula <- stats::as.formula(
          paste0(
            "Surv(tstart_yr, tstop_yr, ", spec$event, ") ~ ",
            paste(period_terms, collapse = " + "),
            " + cluster(PLACE_ID)"
          )
        )

        period_fit <- fit_coxph_checked(
          formula = period_formula,
          data = period_data,
          ties = "efron",
          x = TRUE
        )
        period_mod <- period_fit$model

        if (is.null(period_mod)) {
          message(
            "[PH period] ", spec$model, " model failed: ",
            ifelse(nzchar(period_fit$warning_text), period_fit$warning_text, "unknown fit error")
          )
          all_period_model_summary[[length(all_period_model_summary) + 1]] <- tibble::tibble(
            model = spec$model,
            transition = spec$transition,
            n_original_rows = nrow(spec$data),
            n_split_rows = nrow(period_data),
            events = sum(period_data[[spec$event]] == 1L, na.rm = TRUE),
            record_start_yr = ph_record_start,
            early_end_yr = ph_cut_1,
            middle_end_yr = ph_cut_2,
            record_end_yr = ph_record_end,
            concordance = NA_real_,
            concordance_se = NA_real_,
            status = period_fit$status,
            fit_warning = period_fit$warning_text
          )
          writeLines(
            c(
              paste0("Fit status: ", period_fit$status),
              paste0("Fit warning/error: ", ifelse(nzchar(period_fit$warning_text), period_fit$warning_text, "unknown fit error"))
            ),
            con = file.path(out_dir, paste0(spec$prefix, "_period_interaction_model_summary.txt"))
          )
          next
        }

        # Always retain the textual model summary for diagnostic review.
        capture.output(
          {
            cat("Fit status:", period_fit$status, "\n")
            if (nzchar(period_fit$warning_text)) cat("Fit warning:", period_fit$warning_text, "\n")
            print(summary(period_mod))
          },
          file = file.path(out_dir, paste0(spec$prefix, "_period_interaction_model_summary.txt"))
        )

        period_sm <- summary(period_mod)
        period_conc <- period_sm$concordance

        model_summary_row <- tibble::tibble(
          model = spec$model,
          transition = spec$transition,
          n_original_rows = nrow(spec$data),
          n_split_rows = nrow(period_data),
          events = as.integer(period_mod$nevent),
          record_start_yr = ph_record_start,
          early_end_yr = ph_cut_1,
          middle_end_yr = ph_cut_2,
          record_end_yr = ph_record_end,
          concordance = if (period_fit$converged && length(period_conc) >= 1) as.numeric(period_conc[1]) else NA_real_,
          concordance_se = if (period_fit$converged && length(period_conc) >= 2) as.numeric(period_conc[2]) else NA_real_,
          status = period_fit$status,
          fit_warning = period_fit$warning_text
        )
        all_period_model_summary[[length(all_period_model_summary) + 1]] <- model_summary_row

        if (!period_fit$converged) {
          message(
            "[PH period] ", spec$model, " was ", period_fit$status,
            "; period-specific HR and Wald outputs were suppressed.",
            ifelse(nzchar(period_fit$warning_text), paste0(" Details: ", period_fit$warning_text), "")
          )
          next
        }

        write_csv(
          broom::tidy(period_mod, exponentiate = TRUE, conf.int = TRUE),
          file.path(out_dir, paste0(spec$prefix, "_period_interaction_model.csv"))
        )

        # Period-specific spatial HRs from robust linear combinations.
        period_hr_rows <- list()

        for (tm in model_spatial_terms) {
          middle_name <- paste0(tm, "__PH_MIDDLE")
          late_name <- paste0(tm, "__PH_LATE")

          early_est <- robust_linear_combination(
            period_mod,
            stats::setNames(1, tm)
          ) %>%
            mutate(period = "Early")

          middle_est <- robust_linear_combination(
            period_mod,
            stats::setNames(c(1, 1), c(tm, middle_name))
          ) %>%
            mutate(period = "Middle")

          late_est <- robust_linear_combination(
            period_mod,
            stats::setNames(c(1, 1), c(tm, late_name))
          ) %>%
            mutate(period = "Late")

          tm_rows <- bind_rows(early_est, middle_est, late_est) %>%
            mutate(
              model = spec$model,
              transition = spec$transition,
              spatial_framework = spec$spatial_framework,
              term = tm,
              predictor = ph_term_label(tm),
              period = factor(period, levels = c("Early", "Middle", "Late"), ordered = TRUE),
              period_start_yr = case_when(
                period == "Early" ~ ph_record_start,
                period == "Middle" ~ ph_cut_1,
                TRUE ~ ph_cut_2
              ),
              period_end_yr = case_when(
                period == "Early" ~ ph_cut_1,
                period == "Middle" ~ ph_cut_2,
                TRUE ~ ph_record_end
              ),
              .before = 1
            )

          period_hr_rows[[length(period_hr_rows) + 1]] <- tm_rows

          tm_wald <- robust_wald_test(
            period_mod,
            c(middle_name, late_name)
          ) %>%
            mutate(
              model = spec$model,
              transition = spec$transition,
              spatial_framework = spec$spatial_framework,
              term = tm,
              predictor = ph_term_label(tm),
              test = "Middle and Late deviations jointly equal zero",
              .before = 1
            )

          all_interaction_tests[[length(all_interaction_tests) + 1]] <- tm_wald
        }

        period_hr_model <- bind_rows(period_hr_rows)
        all_period_hr[[length(all_period_hr) + 1]] <- period_hr_model

        write_csv(
          period_hr_model,
          file.path(out_dir, paste0(spec$prefix, "_period_spatial_HR.csv"))
        )

        # Omnibus robust Wald test across every added spatial interaction.
        omnibus_wald <- robust_wald_test(
          period_mod,
          interaction_columns
        ) %>%
          mutate(
            model = spec$model,
            transition = spec$transition,
            spatial_framework = spec$spatial_framework,
            term = "ALL_SPATIAL_TERMS",
            predictor = "All principal spatial predictors",
            test = "All Middle and Late spatial deviations jointly equal zero",
            .before = 1
          )

        all_interaction_tests[[length(all_interaction_tests) + 1]] <- omnibus_wald

        # Publication-oriented plot of period-specific hazard ratios.
        p_period <- ggplot(
          period_hr_model,
          aes(
            x = period,
            y = HR,
            ymin = conf.low,
            ymax = conf.high,
            group = predictor
          )
        ) +
          geom_hline(
            yintercept = 1,
            linetype = "dashed",
            colour = "grey40"
          ) +
          geom_line(linewidth = 0.55, na.rm = TRUE) +
          geom_pointrange(linewidth = 0.45, na.rm = TRUE) +
          facet_wrap(
            ~ predictor,
            scales = "free_y"
          ) +
          scale_y_log10() +
          labs(
            title = paste0("Period-specific spatial effects: ", spec$transition),
            subtitle = paste0(
              "Early, middle and late thirds of the ", round(ph_record_duration, 1),
              "-year observation record"
            ),
            x = "Observation period",
            y = "Hazard ratio per 1 SD increase (log scale)"
          ) +
          theme_bw(base_size = 11) +
          theme(
            panel.grid.minor = element_blank(),
            plot.title = element_text(face = "bold"),
            strip.text = element_text(face = "bold")
          )

        safe_plot_save(
          p_period,
          paste0(spec$prefix, "_period_spatial_HR.png"),
          width = max(7, 4.2 * length(model_spatial_terms)),
          height = 5.5
        )
      }

      # --------------------------------------------------------
      # Combined diagnostic outputs
      # --------------------------------------------------------

      combined_ph_tests <- bind_rows(all_ph_tests)
      combined_period_hr <- bind_rows(all_period_hr)
      combined_interaction_tests <- bind_rows(all_interaction_tests)
      combined_period_summary <- bind_rows(all_period_model_summary)

      write_if_nonempty(
        combined_ph_tests,
        "09_PH_all_models_tests.csv"
      )

      write_if_nonempty(
        combined_period_hr,
        "09_PH_period_specific_spatial_HR.csv"
      )

      write_if_nonempty(
        combined_interaction_tests,
        "09_PH_spatial_period_interaction_tests.csv"
      )

      write_if_nonempty(
        combined_period_summary,
        "09_PH_period_model_summary.csv"
      )

      if (!is.null(combined_period_hr) && nrow(combined_period_hr) > 0) {
        direction_summary <- combined_period_hr %>%
          mutate(
            direction = case_when(
              is.na(HR) ~ "not estimable",
              HR > 1 ~ "positive",
              HR < 1 ~ "negative",
              TRUE ~ "null"
            )
          ) %>%
          group_by(model, transition, spatial_framework, term, predictor) %>%
          summarise(
            early_HR = HR[period == "Early"][1],
            middle_HR = HR[period == "Middle"][1],
            late_HR = HR[period == "Late"][1],
            early_direction = direction[period == "Early"][1],
            middle_direction = direction[period == "Middle"][1],
            late_direction = direction[period == "Late"][1],
            direction_stable = n_distinct(direction[direction %in% c("positive", "negative")]) <= 1,
            crosses_HR_1 = any(conf.low <= 1 & conf.high >= 1, na.rm = TRUE),
            .groups = "drop"
          )

        write_csv(
          direction_summary,
          file.path(out_dir, "09_PH_period_direction_summary.csv")
        )
      }

      message("[PH] Diagnostics complete. See outputs beginning 09_PH and 09a-09e_PH.")
    }
  }

  write_csv(
    cox_data %>%
      select(
        PLACE_ID,
        BLOCK_ID,
        tstart_yr,
        tstop_yr,
        REACTIVATE_EVT,
        BASE_REACTIVATE_EVT,
        INIT_FP_COHORT,
        BASE_RISK,
        BASE_REACTIVATE_RISK_SET_DERIVED,
        STORAGE_EVT,
        STABILISE_EVT,
        STORAGE_REWORK_EVT,
        ANY_CONFIRMED_EVT,
        REACTIVATE_TRANS,
        STORAGE_TRANS,
        STABILISE_TRANS,
        STORAGE_REWORK_TRANS,
        ANY_STATE_EVT,
        ANY_ONTO_EVT,
        E_EVT_RAW,
        D_EVT_RAW,
        E_CONFIRM_AVAILABLE,
        D_CONFIRM_AVAILABLE,
        E_evt,
        D_evt,
        ANY_EVT,
        REACTIVATE_RISK_SET,
        STORAGE_RISK_SET,
        STABILISE_RISK_SET,
        STORAGE_REWORK_RISK_SET,
        ANY_STATE_RISK_SET,
        E_RISK_SET,
        D_RISK_SET,
        RISK_SET,
        event_class,
        any_of(c(
          "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "EVENT_ONTOLOGY", "NEXT_EVENT_ONTOLOGY",
          "ASM_STATE_PREV",
          "ASM_CLASS_PREV",
          "ASM_STRUCTURE_CL_PREV",
          "ASM_N_EVENTS_PREV",
          "ASM_N_ACTIVE_DOMAIN_PREV",
          "ASM_N_STORAGE_PREV",
          "ASM_N_STAB_FP_PREV",
          "ASM_N_REACTIVATE_PREV",
          "ASM_N_STORAGE_EVT_PREV",
          "ASM_N_STABILISE_PREV",
          "ASM_N_EROSION_PREV",
          "ASM_N_DEPOSITION_PREV",
          "ASM_DIST_FREQ_PREV",
          "ASM_STORAGE_FRAC_PREV",
          "ASM_STAB_FP_FRAC_PREV",
          "ASM_DOM_RATIO_PREV",
          "ASM_NET_BAL_PREV",
          "ASM_N_EPISODES_PREV",
          "ASM_QUIET_SINCE_PREV",
          "ASM_MAX_QUIET_PREV",
          "ASM_EVER_ERODED_PREV",
          "ASM_EVER_DEPOSITED_PREV",
          "ASM_ACTIVE_PREV",
          "ASM_COV_FRAC",
    "ASM_STORAGE_FRAC_PREV",
    "ASM_N_STABILISE_PREV",
          "DIST_CL_REF",
          "DIST_CL_CURR",
          "CURV_CL_CURR",
          "CURV_EROSION_CURR",
          "DIST_X_CURV_EROSION",
          "GEOM_YMD_PREV", "GEOM_YEAR_PREV", "GEOM_SUPPORT_PREV",
          "DIST_CHANNEL_PREV", "DIST_BANK_PREV", "BANK_SETBACK_PREV",
          "INSIDE_CHANNEL_PREV", "DIST_CL_PREV", "CURV_SIGNED_PREV",
          "CURV_ABS_PREV", "CURV_SCALED_PREV", "BANK_SIDE_PREV",
          "OUTER_BANK_PREV", "INNER_BANK_PREV", "LOCAL_WIDTH_PREV",
          "REL_CHANNEL_POS_PREV", "NEAR_CHANNEL_HALF_PREV",
          "NEAR_CHANNEL_FULL_PREV", "NEAR_BANK_HALF_PREV",
          "NEAR_BANK_FULL_PREV", "OUTER_CURV_REACT_HALF_PREV",
          "OUTER_CURV_REACT_FULL_PREV", "INNER_CURV_STORAGE_HALF_PREV",
          "INNER_CURV_STORAGE_FULL_PREV", "OUTER_CURV_STORAGE_HALF_PREV",
          "OUTER_CURV_STORAGE_FULL_PREV",
          "DIST_CL_PREV",
          "DIST_CL_REF_BIN",
          "DIST_CL_CURR_BIN",
          "DIST_ACTIVE_PREV",
          "DIST_ACTIVE_CURR",
          "DIST_WATER_PREV",
          "DIST_WATER_CURR",
          "DIST_ACTIVE_PREV_LOGKM_Z",
          "DIST_ACTIVE_CURR_LOGKM_Z",
          "DIST_WATER_PREV_LOGKM_Z",
          "DIST_WATER_CURR_LOGKM_Z",
          "IN_ACTIVE_PREV",
          "IN_ACTIVE_CURR",
          "IN_WATER_PREV",
          "IN_WATER_CURR"
        ))
      ),
    file.path(out_dir, "08x_cox_interval_PREV_input_table.csv")
  )
}

# -----------------------------
# [FRAF archive / workflow]
# Descriptive transition accounting: summarise mutually exclusive observed
# state changes without implying that every transition shares one risk population.
# [FRAF archive / code note]
# A competing-state event summary helps interpret redistribution among
# AD/DS/SF but cannot override transition-specific eligibility.
# 5. Competing event summary
# -----------------------------

risk_comp <- risk_valid %>%
  mutate(
    event_type = as.character(EVENT_STATE),
    event_type = ifelse(
      is.na(event_type) | event_type == "Persistence",
      "Persistence/no transition",
      event_type
    )
  )

# QA: primary bridged events may resolve across one or more boundary-mixed
# endpoints, so retain the observed pair, effective T1 state and bridge source
# together when auditing the competing-outcome category.
transition_classification_qa <- risk_valid %>%
  count(
    STATE1_ONTOLOGY,
    STATE2_ONTOLOGY,
    M3_EFFECTIVE_STATE_T1_PRIMARY,
    REACTIVATE_BRIDGED,
    STORAGE_BRIDGED,
    STORAGE_REWORK_BRIDGED,
    FP_STORAGE_BRIDGED,
    EVENT_STATE,
    name = "n"
  ) %>%
  arrange(M3_EFFECTIVE_STATE_T1_PRIMARY, STATE2_ONTOLOGY, EVENT_STATE)

write_csv(
  transition_classification_qa,
  file.path(out_dir, "10a_state_outcome_classification_QA.csv")
)

comp_summary <- risk_comp %>%
  group_by(tstart_yr, tstop_yr, event_type) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(tstart_yr, tstop_yr) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()

write_csv(
  comp_summary,
  file.path(out_dir, "10_competing_state_outcome_interval_summary.csv")
)

# Colour competing outcomes by the state reached. Within each destination
# group, darker shades denote primary ambiguity-bridged transitions, intermediate
# shades denote residual directional transitions, and pale shades denote
# unconfirmed transitions.
competing_outcome_levels <- c(
  # Reached Stabilised Floodplain (green)
  "Storage became Stabilised Floodplain",
  "Active Domain -> Stabilised Floodplain",

  # Reached Depositional Storage (yellow)
  "Entered Depositional Storage",
  "Stabilised Floodplain -> Depositional Storage",
  "Unconfirmed storage transition",

  # Reached Active Domain (blue)
  "Reached by Active Domain",
  "Depositional Storage -> Active Domain",
  "Unconfirmed reactivation transition",

  # Defensive fallback
  "Unclassified state transition"
)

competing_outcome_colours <- c(
  # Stabilised Floodplain outcomes: green shades
  "Storage became Stabilised Floodplain" = "#1B7837",
  "Active Domain -> Stabilised Floodplain" = "#7FBF7B",

  # Depositional Storage outcomes: yellow shades
  "Entered Depositional Storage" = "#D99A00",
  "Stabilised Floodplain -> Depositional Storage" = "#F2C230",
  "Unconfirmed storage transition" = "#FFF0A6",

  # Active Domain outcomes: blue shades
  "Reached by Active Domain" = "#2166AC",
  "Depositional Storage -> Active Domain" = "#67A9CF",
  "Unconfirmed reactivation transition" = "#D1E5F0",

  # Unexpected recognised-state change
  "Unclassified state transition" = "#8C8C8C"
)

p_comp <- comp_summary %>%
  filter(event_type != "Persistence/no transition") %>%
  mutate(event_type = factor(event_type, levels = competing_outcome_levels)) %>%
  ggplot(aes(x = tstop_yr, y = prop, fill = event_type)) +
  geom_col(position = "stack") +
  scale_fill_manual(
    values = competing_outcome_colours,
    breaks = competing_outcome_levels,
    drop = TRUE
  ) +
  labs(
    x = "Interval end year",
    y = "Proportion of eligible interval outcomes",
    fill = "State outcome",
    title = "Competing state outcomes"
  ) +
  theme_minimal()

safe_plot_save(p_comp, "10_competing_state_outcome_summary.png", width = 8, height = 5)

# Baseline first-event summary uses the dynamic first-event risk set, not all
# later rows belonging to the initial cohort.
base_comp_summary <- risk_baseline_fp %>%
  mutate(
    event_type = ifelse(
      BASE_REACTIVATE_EVT == 1,
      "Initial floodplain reached by Active Domain",
      "Initial floodplain persistence"
    )
  ) %>%
  group_by(tstart_yr, tstop_yr, event_type) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(tstart_yr, tstop_yr) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()

write_csv(
  base_comp_summary,
  file.path(out_dir, "10b_initial_floodplain_first_event_summary.csv")
)

if (
  nrow(base_comp_summary) > 0 &&
  any(base_comp_summary$event_type == "Initial floodplain reached by Active Domain")
) {
  p_base_comp <- base_comp_summary %>%
    filter(event_type == "Initial floodplain reached by Active Domain") %>%
    ggplot(aes(x = tstop_yr, y = prop)) +
    geom_col() +
    labs(
      x = "Interval end year",
      y = "Proportion of initial-floodplain risk set",
      title = "Initial floodplain reactivated into the active domain"
    ) +
    theme_minimal()
  safe_plot_save(
    p_base_comp,
    "10b_initial_floodplain_reactivation_summary.png",
    width = 8,
    height = 5
  )
}

# State-pair eligibility audit for the transition matrix. Unresolved endpoints
# are not silently reassigned from Module 4a.
strict_matrix_source <- risk_model_strict %>%
  filter(ANY_STATE_RISK_SET_STRICT_AUDIT == 1L)

transition_matrix_eligibility <- risk %>%
  summarise(
    total_rows = n(),
    recognised_pair_rows = sum(
      as.character(STATE1_ONTOLOGY) %in% c("Active domain", "Depositional storage", "Stabilised floodplain") &
      as.character(STATE2_ONTOLOGY) %in% c("Active domain", "Depositional storage", "Stabilised floodplain"),
      na.rm = TRUE
    ),
    excluded_unresolved_or_invalid_rows = total_rows - recognised_pair_rows,
    mixed_endpoint_rows = sum(M3_MIXED_T1 == 1L | M3_MIXED_T2 == 1L, na.rm = TRUE),
    primary_hazard_rows = nrow(risk_valid),
    strict_observed_matrix_rows = nrow(strict_matrix_source),
    matrix_definition = "STRICT_RECOGNISED_ENDPOINT_PAIRS"
  )
write_csv(transition_matrix_eligibility, file.path(out_dir, "11_state_transition_matrix_eligibility_QA.csv"))

# ============================================================
# OBSERVED-STATE TRANSITION MATRIX (publication style)
# ============================================================
# A bridged event may have an unresolved observed endpoint, so it cannot be
# inserted into a categorical endpoint matrix without forcing a state. The
# matrix therefore remains a strict recognised-endpoint summary, while the
# KM/AG/Cox models above use the primary ambiguity-bridged event family.
# Module 4a does not supply or replace matrix endpoint states here.

tm_long <- strict_matrix_source %>%
  transmute(
    State_Start = as.character(STATE1_ONTOLOGY),
    State_End = as.character(STATE2_ONTOLOGY)
  ) %>%
  filter(
    State_Start %in% c("Active domain", "Depositional storage", "Stabilised floodplain"),
    State_End %in% c("Active domain", "Depositional storage", "Stabilised floodplain")
  ) %>%
  count(State_Start, State_End, name = "n") %>%
  group_by(State_Start) %>%
  mutate(prob = n / sum(n)) %>%
  ungroup() %>%
  tidyr::complete(
    State_Start = c("Active domain", "Depositional storage", "Stabilised floodplain"),
    State_End = c("Active domain", "Depositional storage", "Stabilised floodplain"),
    fill = list(n = 0, prob = 0)
  ) %>%
  mutate(
    State_Start = factor(
      State_Start,
      levels = c("Active domain", "Depositional storage", "Stabilised floodplain")
    ),
    State_End = factor(
      State_End,
      levels = c("Active domain", "Depositional storage", "Stabilised floodplain")
    ),
    label_txt = ifelse(prob < 0.01 & prob > 0, "<0.01", sprintf("%.2f", prob)),
    text_col = transition_matrix_text_colour(
      prob,
      option = "C",
      direction = -1,
      luminance_cutoff = 0.30
    )
  )

write_csv(
  tm_long,
  file.path(out_dir, "11_state_transition_probabilities.csv")
)

p_tm <- ggplot(
  tm_long,
  aes(x = State_Start, y = State_End, fill = prob)
) +
  geom_tile(colour = "grey45", linewidth = 0.6) +
  geom_text(
    aes(label = label_txt, colour = text_col),
    size = 5
  ) +
  scale_colour_identity() +
  scale_fill_viridis_c(
    option = "C",
    direction = -1,
    limits = c(0, 1),
    na.value = "white",
    name = "Probability"
  ) +
  labs(
    title = "State transition probability matrix",
    x = "State at start of interval",
    y = "State at end of interval"
  ) +
  theme_bw(base_size = 14) +
  theme(
    panel.grid = element_blank(),
    axis.text.x = element_text(angle = 35, hjust = 1, size = 12),
    axis.text.y = element_text(size = 12),
    plot.title = element_text(size = 18, face = "bold", hjust = 0.5),
    legend.title = element_text(size = 12),
    legend.text = element_text(size = 11)
  )

safe_plot_save(
  p_tm,
  "11_state_transition_matrix.png",
  width = 9,
  height = 6.5
)

# [FRAF archive / code note]
# Domain comparison has distinct denominators: all eligible fixed places
# versus their measured area within the historical channel union.
# ============================================================
# [FRAF archive / workflow]
# Optional retrospective domain contrast, OFF by default for large risk tables.
# Union-channel overlap is a static domain weight, not an observed future event.
# 12. Full analysis area versus historical activity-belt envelope
# ============================================================
# This is a retrospective nested-domain description. The activity-belt envelope uses
# all dated Active Domain/channel positions across the record and is therefore
# not used to define the principal KM/AG/Cox risk sets or as a Cox predictor.
#
# v17.10.8 MEMORY DESIGN
# ----------------------
# Section 12 formerly built two complete copies of the multi-million-row Risk Table
# for several comparisons. In particular, immediately after the comparative
# transition matrix it bound every T1 row to every T2 row before deduplicating the
# observation dates. On Jamuna that was the dominant contiguous-memory spike.
#
# The replacement below is summary-first. All scientific definitions are unchanged:
#   * the full-domain weight is ASM_BLOCK_AREA_M2;
#   * the nested historical activity-belt weight is ASM_UNION_OVERLAP_M2;
#   * transition matrices use strict recognised T1/T2 pairs;
#   * state composition uses one state per block/observation date;
#   * interval transition rates use the primary model eligibility/risk/event fields.
# State-chain QA has already been enforced as fatal above, so a unique observation
# sequence is represented exactly by the initial T1 observation plus every T2
# observation. There is therefore no need to materialise and deduplicate 2*N rows.
if (isTRUE(RunUnionComparison)) {
  message("[Union comparison] Building memory-safe full-area versus historical activity-belt summaries for ", reach_label)

  # Before the comparison, all Cox/KM/AG/PH outputs and the publication transition
  # matrix have already been written. Retain only the full Risk Table plus, when
  # requested, the primary risk subset/geometry needed by Section 13. This also
  # removes strict_matrix_source and the many full-width sensitivity subsets.
  # [FRAF archive / Historic/QA function: fraf_release_pre_union_memory]
  # Release unneeded historical objects before the optional full-versus-union comparison.
  fraf_release_pre_union_memory <- function(env = parent.frame()) {
    nm <- ls(envir = env, all.names = TRUE)
    preserve <- c(
      "risk", "out_dir", "reach_label", "RunUnionComparison", "ExportSpatialSummary",
      "union_domain_fields", "PlacePolygons", "PureStateMinSupport",
      "RunPrediction", "RunBroadFloodplainPrediction", "ForecastOrigins",
      "OriginInterpretation", "MinimumTrainingEvents", "WriteParquet",
      "WriteFullFittedPredictions", "FutureCovariateTable", "FutureLayerName",
      "FutureStartTime", "FutureStopTime", "MamoreReactivationExposure",
      "MamoreStorageExposure", "RiskTable", "RiskLayerName", "OutputFolder"
    )
    if (isTRUE(ExportSpatialSummary)) preserve <- unique(c(preserve, "risk_valid"))

    non_functions <- nm[vapply(nm, function(x) {
      !is.function(get(x, envir = env, inherits = FALSE))
    }, logical(1))]
    non_functions <- setdiff(non_functions, preserve)
    large_drop <- non_functions[vapply(non_functions, function(x) {
      as.numeric(utils::object.size(get(x, envir = env, inherits = FALSE))) > 5 * 1024^2
    }, logical(1))]

    # Explicitly include known full-width historic subsets even when R's object.size
    # under-reports shared column storage.
    known_drop <- intersect(c(
      "risk_model", "risk_model_strict", "risk_model_pure_state",
      "risk_erosion", "risk_baseline_fp", "risk_deposition", "risk_stabilise",
      "risk_storage_rework", "risk_any", "risk_erosion_pure", "risk_deposition_pure",
      "risk_stabilise_pure", "risk_storage_rework_pure", "risk_any_pure",
      "risk_erosion_pure_state", "risk_deposition_pure_state",
      "risk_stabilise_pure_state", "risk_storage_rework_pure_state",
      "risk_any_pure_state", "risk_comp", "strict_matrix_source", "cox_data"
    ), nm)

    drop <- unique(c(large_drop, known_drop))
    drop <- setdiff(drop, preserve)
    drop <- drop[vapply(drop, function(x) {
      !is.function(get(x, envir = env, inherits = FALSE))
    }, logical(1))]

    if (length(drop) > 0L) {
      message("[Union comparison memory] Releasing ", length(drop),
              " obsolete historic objects before Section 12.")
      rm(list = drop, envir = env)
    }
    invisible(gc(full = TRUE))
    invisible(drop)
  }
  fraf_release_pre_union_memory(environment())

  for (nm in union_domain_fields) {
    risk[[nm]] <- suppressWarnings(as.numeric(risk[[nm]]))
  }
  if (!"duration" %in% names(risk)) {
    risk$duration <- as.numeric(risk$tstop_yr) - as.numeric(risk$tstart_yr)
  }
  risk$duration <- suppressWarnings(as.numeric(risk$duration))

  # [FRAF archive / Historic/QA function: first_finite_value]
  # Return a representative finite numeric value for a domain summary.
  first_finite_value <- function(x) {
    x <- suppressWarnings(as.numeric(x))
    x <- x[is.finite(x)]
    if (length(x) == 0) return(NA_real_)
    x[1]
  }
  # [FRAF archive / Historic/QA function: n_unique_finite]
  # Count distinct finite values after controlled rounding for QA.
  n_unique_finite <- function(x, digits = 6L) {
    x <- suppressWarnings(as.numeric(x))
    x <- x[is.finite(x)]
    if (length(x) == 0) return(0L)
    dplyr::n_distinct(round(x, digits = digits))
  }

  # One static weight record per BLOCK_ID, with explicit constancy and balance QA.
  block_domain_weights <- risk %>%
    group_by(BLOCK_ID) %>%
    summarise(
      ASM_BLOCK_AREA_M2 = first_finite_value(ASM_BLOCK_AREA_M2),
      ASM_UNION_OVERLAP_M2 = first_finite_value(ASM_UNION_OVERLAP_M2),
      ASM_UNION_FRAC = first_finite_value(ASM_UNION_FRAC),
      ASM_OUTSIDE_UNION_M2 = first_finite_value(ASM_OUTSIDE_UNION_M2),
      ASM_UNION_CONTACT = first_finite_value(ASM_UNION_CONTACT),
      ASM_UNION_BOUNDARY = first_finite_value(ASM_UNION_BOUNDARY),
      ASM_UNION_CORE50 = first_finite_value(ASM_UNION_CORE50),
      n_block_area_values = n_unique_finite(ASM_BLOCK_AREA_M2),
      n_union_overlap_values = n_unique_finite(ASM_UNION_OVERLAP_M2),
      n_union_frac_values = n_unique_finite(ASM_UNION_FRAC, digits = 10L),
      n_outside_values = n_unique_finite(ASM_OUTSIDE_UNION_M2),
      .groups = "drop"
    ) %>%
    mutate(
      area_tolerance_m2 = pmax(1e-6, abs(ASM_BLOCK_AREA_M2) * 1e-9),
      static_value_fail = as.integer(
        n_block_area_values > 1L | n_union_overlap_values > 1L |
          n_union_frac_values > 1L | n_outside_values > 1L
      ),
      missing_weight_fail = as.integer(
        !is.finite(ASM_BLOCK_AREA_M2) | !is.finite(ASM_UNION_OVERLAP_M2) |
          !is.finite(ASM_UNION_FRAC) | !is.finite(ASM_OUTSIDE_UNION_M2) |
          !is.finite(ASM_UNION_CONTACT) | !is.finite(ASM_UNION_BOUNDARY) |
          !is.finite(ASM_UNION_CORE50)
      ),
      range_fail = as.integer(
        ASM_BLOCK_AREA_M2 <= 0 |
          ASM_UNION_OVERLAP_M2 < -area_tolerance_m2 |
          ASM_OUTSIDE_UNION_M2 < -area_tolerance_m2 |
          ASM_UNION_FRAC < -1e-9 | ASM_UNION_FRAC > 1 + 1e-9
      ),
      area_balance_fail = as.integer(
        abs(ASM_UNION_OVERLAP_M2 + ASM_OUTSIDE_UNION_M2 - ASM_BLOCK_AREA_M2) > area_tolerance_m2
      ),
      fraction_fail = as.integer(
        abs(ASM_UNION_FRAC - ASM_UNION_OVERLAP_M2 / ASM_BLOCK_AREA_M2) > 1e-8
      ),
      flag_fail = as.integer(
        ASM_UNION_CONTACT != as.integer(ASM_UNION_OVERLAP_M2 > area_tolerance_m2) |
          ASM_UNION_BOUNDARY != as.integer(
            ASM_UNION_OVERLAP_M2 > area_tolerance_m2 &
              ASM_OUTSIDE_UNION_M2 > area_tolerance_m2
          ) |
          ASM_UNION_CORE50 != as.integer(ASM_UNION_FRAC >= 0.5)
      ),
      any_fail = pmax(
        static_value_fail, missing_weight_fail, range_fail,
        area_balance_fail, fraction_fail, flag_fail,
        na.rm = TRUE
      )
    )

  union_block_failures <- block_domain_weights %>% filter(any_fail == 1L)
  write_csv(
    union_block_failures,
    file.path(out_dir, "12_full_vs_union_block_weight_failures.csv")
  )

  union_extent_qa <- block_domain_weights %>%
    summarise(
      Reach = reach_label,
      blocks = n(),
      full_analysis_area_m2 = sum(ASM_BLOCK_AREA_M2, na.rm = TRUE),
      full_analysis_area_km2 = full_analysis_area_m2 / 1e6,
      union_channel_area_m2 = sum(ASM_UNION_OVERLAP_M2, na.rm = TRUE),
      union_channel_area_km2 = union_channel_area_m2 / 1e6,
      outside_union_area_m2 = sum(ASM_OUTSIDE_UNION_M2, na.rm = TRUE),
      outside_union_area_km2 = outside_union_area_m2 / 1e6,
      union_share_of_full = union_channel_area_m2 / full_analysis_area_m2,
      blocks_fully_inside = sum(ASM_UNION_CONTACT == 1 & ASM_UNION_BOUNDARY == 0, na.rm = TRUE),
      blocks_boundary = sum(ASM_UNION_BOUNDARY == 1, na.rm = TRUE),
      blocks_wholly_outside = sum(ASM_UNION_CONTACT == 0, na.rm = TRUE),
      static_value_failures = sum(static_value_fail, na.rm = TRUE),
      missing_weight_failures = sum(missing_weight_fail, na.rm = TRUE),
      range_failures = sum(range_fail, na.rm = TRUE),
      area_balance_failures = sum(area_balance_fail, na.rm = TRUE),
      fraction_failures = sum(fraction_fail, na.rm = TRUE),
      flag_failures = sum(flag_fail, na.rm = TRUE),
      total_failure_blocks = sum(any_fail, na.rm = TRUE)
    )
  write_csv(union_extent_qa, file.path(out_dir, "12_full_vs_union_extent_QA.csv"))

  if (nrow(union_block_failures) > 0) {
    stop(
      "Union-domain weights failed R-side QA for ", nrow(union_block_failures),
      " BLOCK_ID values. Inspect 12_full_vs_union_block_weight_failures.csv."
    )
  }

  state_levels_union <- c(
    "Active domain", "Depositional storage", "Stabilised floodplain"
  )
  domain_levels_union <- c("Full analysis area", "Historical activity-belt envelope")

  # Reusable state vectors. These are far smaller than row-binding two copies of risk.
  union_state1 <- as.character(risk$STATE1_ONTOLOGY)
  union_state2 <- as.character(risk$STATE2_ONTOLOGY)
  union_strict_model <- int01(risk$M3_MODEL_ELIGIBLE_STRICT) == 1L
  union_strict_matrix <- union_strict_model &
    int01(risk$ANY_STATE_RISK_SET_STRICT_AUDIT) == 1L &
    union_state1 %in% state_levels_union &
    union_state2 %in% state_levels_union

  # ------------------------------------------------------------
  # [FRAF archive / workflow]
  # Area-weighted matrices use strictly resolved state pairs and explicit eligibility;
  # the union-domain area should not be counted as additional separate cells.
  # 12a. Area-weighted strict state-transition matrices
  # ------------------------------------------------------------
  # [FRAF archive / Historic/QA function: summarise_matrix_eligibility_domain]
  # Audit which strict transitions can enter a weighted matrix for one spatial domain.
  summarise_matrix_eligibility_domain <- function(weight_field, domain_name) {
    w <- suppressWarnings(as.numeric(risk[[weight_field]]))
    valid_weight <- is.finite(w) & w > 0
    strict_model_ok <- valid_weight & union_strict_model
    strict_matrix_ok <- valid_weight & union_strict_matrix
    total_area <- sum(w[valid_weight], na.rm = TRUE)
    matrix_area <- sum(w[strict_matrix_ok], na.rm = TRUE)
    tibble::tibble(
      Reach = reach_label,
      Analysis_Domain = domain_name,
      total_interval_rows = sum(valid_weight, na.rm = TRUE),
      total_area_observation_m2 = total_area,
      strict_model_eligible_rows = sum(strict_model_ok, na.rm = TRUE),
      strict_model_eligible_area_observation_m2 = sum(w[strict_model_ok], na.rm = TRUE),
      strict_matrix_eligible_rows = sum(strict_matrix_ok, na.rm = TRUE),
      strict_matrix_eligible_area_observation_m2 = matrix_area,
      excluded_area_observation_m2 = total_area - matrix_area,
      eligible_area_share = ifelse(total_area > 0, matrix_area / total_area, NA_real_)
    )
  }

  domain_matrix_eligibility <- bind_rows(
    summarise_matrix_eligibility_domain("ASM_BLOCK_AREA_M2", "Full analysis area"),
    summarise_matrix_eligibility_domain("ASM_UNION_OVERLAP_M2", "Historical activity-belt envelope")
  )
  write_csv(
    domain_matrix_eligibility,
    file.path(out_dir, "12_full_vs_union_transition_matrix_eligibility_QA.csv")
  )

  # [FRAF archive / Historic/QA function: summarise_domain_transition_matrix]
  # Aggregate strict state-to-state transition areas without copying the full panel.
  summarise_domain_transition_matrix <- function(weight_field, domain_name) {
    w <- suppressWarnings(as.numeric(risk[[weight_field]]))
    valid <- union_strict_matrix & is.finite(w) & w > 0
    out <- tidyr::expand_grid(
      State_Start = state_levels_union,
      State_End = state_levels_union
    )
    out$area_observation_m2 <- 0
    out$interval_rows <- 0L
    for (ii in seq_len(nrow(out))) {
      hit <- valid & union_state1 == out$State_Start[ii] & union_state2 == out$State_End[ii]
      out$area_observation_m2[ii] <- sum(w[hit], na.rm = TRUE)
      out$interval_rows[ii] <- sum(hit, na.rm = TRUE)
    }
    out %>%
      mutate(Reach = reach_label, Analysis_Domain = domain_name, .before = 1)
  }

  domain_tm <- bind_rows(
    summarise_domain_transition_matrix("ASM_BLOCK_AREA_M2", "Full analysis area"),
    summarise_domain_transition_matrix("ASM_UNION_OVERLAP_M2", "Historical activity-belt envelope")
  ) %>%
    group_by(Reach, Analysis_Domain, State_Start) %>%
    mutate(
      origin_state_area_observation_m2 = sum(area_observation_m2, na.rm = TRUE),
      probability = ifelse(
        origin_state_area_observation_m2 > 0,
        area_observation_m2 / origin_state_area_observation_m2,
        NA_real_
      )
    ) %>%
    ungroup() %>%
    mutate(
      area_observation_km2 = area_observation_m2 / 1e6,
      origin_state_area_observation_km2 = origin_state_area_observation_m2 / 1e6,
      State_Start = factor(State_Start, levels = state_levels_union),
      State_End = factor(State_End, levels = state_levels_union),
      Analysis_Domain = factor(Analysis_Domain, levels = domain_levels_union),
      label_txt = ifelse(
        is.na(probability), "NA",
        sprintf("%.3f\n%.1f km²-observations", probability, area_observation_km2)
      ),
      text_col = ifelse(!is.na(probability) & probability > 0.50, "white", "black"),
      Matrix_Definition = "Strict recognised T1/T2 state pairs; area-observation weighted",
      Domain_Nesting_Note = "Historical activity-belt envelope is nested within the full analysis area"
    )

  write_csv(
    domain_tm,
    file.path(out_dir, "12_full_vs_union_transition_probabilities_area.csv")
  )

  p_domain_tm <- ggplot(
    domain_tm,
    aes(x = State_End, y = State_Start, fill = probability)
  ) +
    geom_tile(colour = "grey45", linewidth = 0.6) +
    geom_text(aes(label = label_txt, colour = text_col), size = 3.7, lineheight = 0.95) +
    scale_colour_identity() +
    scale_fill_viridis_c(
      option = "C", direction = -1, limits = c(0, 1),
      na.value = "white", name = "Probability"
    ) +
    facet_wrap(~Analysis_Domain, nrow = 1) +
    labs(
      title = paste0(reach_label, ": state-transition matrices"),
      subtitle = "Full analysis area compared with the nested historical activity-belt envelope",
      x = "State at end of interval",
      y = "State at start of interval"
    ) +
    theme_bw(base_size = 12) +
    theme(
      panel.grid = element_blank(),
      axis.text.x = element_text(angle = 30, hjust = 1),
      plot.title = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      strip.text = element_text(face = "bold")
    )
  safe_plot_save(
    p_domain_tm,
    "12_full_vs_union_transition_matrix.png",
    width = 13,
    height = 6.5
  )
  rm(p_domain_tm)
  invisible(gc(full = TRUE))
  message("[Union comparison memory] Comparative transition matrix written without row-level domain duplication.")

  # ------------------------------------------------------------
  # [FRAF archive / workflow]
  # Reconstruct compositional area through time from starting T1 plus successive
  # T2 observations without duplicating the longitudinal risk table in memory.
  # 12b. Area-weighted state composition by observation date
  # ------------------------------------------------------------
  # The earlier fatal state-chain QA guarantees that, within each place, T2 of one
  # interval equals T1 of the next. Therefore the unique observation sequence is
  # the first record-wide T1 date plus all T2 dates. The former 2*N endpoint table
  # and subsequent BLOCK_ID/date deduplication are unnecessary.
  # The propagated T1 source explicitly identifies whether a T1 state is carried
  # from the previous interval T2. Retain only non-carried T1 observations (normally
  # the first observation for each place); all subsequent unique dates enter via T2.
  # This also remains correct if a place begins later than the global first date.
  risk$.UNION_INITIAL_T1 <- as.integer(
    toupper(trimws(as.character(risk$M3_STATE_SOURCE_T1))) != "PREVIOUS_INTERVAL_T2"
  )

  state_start_summary <- risk %>%
    group_by(y1, tstart_yr, STATE1_ONTOLOGY) %>%
    summarise(
      initial_rows = sum(.UNION_INITIAL_T1 == 1L, na.rm = TRUE),
      full_area_m2 = sum(ASM_BLOCK_AREA_M2[.UNION_INITIAL_T1 == 1L], na.rm = TRUE),
      union_area_m2 = sum(ASM_UNION_OVERLAP_M2[.UNION_INITIAL_T1 == 1L], na.rm = TRUE),
      wholly_outside_area_m2 = sum(
        ASM_OUTSIDE_UNION_M2[.UNION_INITIAL_T1 == 1L & ASM_UNION_FRAC <= 1e-6],
        na.rm = TRUE
      ),
      .groups = "drop"
    ) %>%
    filter(initial_rows > 0L, is.finite(tstart_yr)) %>%
    transmute(
      OBS_YMD = y1,
      OBS_TIME_YR = as.numeric(tstart_yr),
      State = as.character(STATE1_ONTOLOGY),
      full_area_m2, union_area_m2, wholly_outside_area_m2
    )

  state_end_summary <- risk %>%
    group_by(y2, tstop_yr, STATE2_ONTOLOGY) %>%
    summarise(
      full_area_m2 = sum(ASM_BLOCK_AREA_M2, na.rm = TRUE),
      union_area_m2 = sum(ASM_UNION_OVERLAP_M2, na.rm = TRUE),
      wholly_outside_area_m2 = sum(
        ifelse(ASM_UNION_FRAC <= 1e-6, ASM_OUTSIDE_UNION_M2, 0),
        na.rm = TRUE
      ),
      .groups = "drop"
    ) %>%
    transmute(
      OBS_YMD = y2,
      OBS_TIME_YR = as.numeric(tstop_yr),
      State = as.character(STATE2_ONTOLOGY),
      full_area_m2, union_area_m2, wholly_outside_area_m2
    )

  observation_state_summary <- bind_rows(state_start_summary, state_end_summary) %>%
    mutate(
      State = ifelse(
        State %in% c(state_levels_union, "Unresolved"),
        State, "Unresolved"
      )
    ) %>%
    group_by(OBS_YMD, OBS_TIME_YR, State) %>%
    summarise(
      full_area_m2 = sum(full_area_m2, na.rm = TRUE),
      union_area_m2 = sum(union_area_m2, na.rm = TRUE),
      wholly_outside_area_m2 = sum(wholly_outside_area_m2, na.rm = TRUE),
      .groups = "drop"
    )

  # A successful run has already established zero state-chain conflicts. Retain the
  # historical output file/schema without rebuilding a 2*N endpoint table merely to
  # prove the same invariant a second time.
  state_observation_conflicts <- tibble::tibble(
    BLOCK_ID = character(),
    OBS_YMD = character(),
    OBS_TIME_YR = numeric(),
    recognised_states = integer(),
    states = character()
  )
  write_csv(
    state_observation_conflicts,
    file.path(out_dir, "12_full_vs_union_state_date_conflicts.csv")
  )

  domain_state_composition <- bind_rows(
    observation_state_summary %>%
      transmute(
        Reach = reach_label,
        Analysis_Domain = "Full analysis area",
        OBS_YMD, OBS_TIME_YR, State,
        state_area_m2 = full_area_m2
      ),
    observation_state_summary %>%
      transmute(
        Reach = reach_label,
        Analysis_Domain = "Historical activity-belt envelope",
        OBS_YMD, OBS_TIME_YR, State,
        state_area_m2 = union_area_m2
      )
  ) %>%
    filter(is.finite(state_area_m2), state_area_m2 > 0) %>%
    group_by(Reach, Analysis_Domain, OBS_YMD, OBS_TIME_YR) %>%
    mutate(
      domain_area_m2 = sum(state_area_m2, na.rm = TRUE),
      state_area_km2 = state_area_m2 / 1e6,
      state_percent = 100 * state_area_m2 / domain_area_m2
    ) %>%
    ungroup() %>%
    mutate(
      Analysis_Domain = factor(Analysis_Domain, levels = domain_levels_union),
      State = factor(State, levels = c(state_levels_union, "Unresolved"))
    )
  write_csv(
    domain_state_composition,
    file.path(out_dir, "12_full_vs_union_state_composition_by_date.csv")
  )

  union_state_colours <- c(
    "Active domain" = "#2166AC",
    "Depositional storage" = "#E6AB02",
    "Stabilised floodplain" = "#4DAF4A",
    "Unresolved" = "grey65"
  )
  p_domain_states <- ggplot(
    domain_state_composition,
    aes(x = OBS_TIME_YR, y = state_percent, colour = State, group = State)
  ) +
    geom_line(linewidth = 0.8, na.rm = TRUE) +
    geom_point(size = 1.2, na.rm = TRUE) +
    facet_wrap(~Analysis_Domain, nrow = 1) +
    scale_colour_manual(values = union_state_colours, drop = FALSE) +
    scale_y_continuous(limits = c(0, 100), expand = expansion(mult = c(0, 0.03))) +
    labs(
      title = paste0(reach_label, ": state composition through time"),
      subtitle = "Complete analysis area and nested historical activity-belt envelope",
      x = "Years since start of record",
      y = "Percentage of analysis domain",
      colour = "State"
    ) +
    theme_bw(base_size = 12) +
    theme(
      panel.grid.minor = element_blank(),
      plot.title = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      strip.text = element_text(face = "bold")
    )
  safe_plot_save(
    p_domain_states,
    "12_full_vs_union_state_composition.png",
    width = 13,
    height = 6
  )
  rm(p_domain_states)

  outside_union_state_qa <- observation_state_summary %>%
    group_by(State) %>%
    summarise(
      area_observation_m2 = sum(wholly_outside_area_m2, na.rm = TRUE),
      area_observation_km2 = area_observation_m2 / 1e6,
      .groups = "drop"
    ) %>%
    filter(area_observation_m2 > 0) %>%
    mutate(
      Reach = reach_label,
      percentage = 100 * area_observation_m2 / sum(area_observation_m2),
      Expected_Result = "Approximately 100% Stabilised floodplain"
    ) %>%
    select(Reach, everything())
  write_csv(
    outside_union_state_qa,
    file.path(out_dir, "12_outside_union_state_QA.csv")
  )

  # ------------------------------------------------------------
  # [FRAF archive / workflow]
  # Calculate exposure-normalised area transition rates separately for the
  # full corridor and historical channel union; retain denominator provenance.
  # 12c. Annual area-transition rates for the two nested domains
  # ------------------------------------------------------------
  domain_total_area <- bind_rows(
    block_domain_weights %>%
      summarise(
        Reach = reach_label,
        Analysis_Domain = "Full analysis area",
        domain_area_m2 = sum(ASM_BLOCK_AREA_M2, na.rm = TRUE)
      ),
    block_domain_weights %>%
      summarise(
        Reach = reach_label,
        Analysis_Domain = "Historical activity-belt envelope",
        domain_area_m2 = sum(ASM_UNION_OVERLAP_M2, na.rm = TRUE)
      )
  )

  transition_specs_union <- list(
    list("Reactivation", "REACTIVATE_EVT", "REACTIVATE_RISK_SET"),
    list("Storage formation", "STORAGE_EVT", "STORAGE_RISK_SET"),
    list("Stabilisation", "STABILISE_EVT", "STABILISE_RISK_SET"),
    list("Storage reworking", "STORAGE_REWORK_EVT", "STORAGE_REWORK_RISK_SET"),
    list("Floodplain entering storage", "FP_STORAGE_EVT", "FP_STORAGE_RISK_SET")
  )

  # Keep only columns needed for the rate summaries, then release the full historic
  # Risk Table before repeated interval aggregation. Base column selection is shallow
  # under normal R copy-on-write semantics and avoids another full-width materialisation.
  rate_event_risk_fields <- unique(unlist(lapply(transition_specs_union, function(x) x[2:3])))
  rate_source_fields <- unique(c(
    "M3_MODEL_ELIGIBLE_PRIMARY", "tstart_yr", "tstop_yr", "duration",
    "ASM_BLOCK_AREA_M2", "ASM_UNION_OVERLAP_M2", rate_event_risk_fields
  ))
  rate_source <- risk[, intersect(rate_source_fields, names(risk)), drop = FALSE]
  rm(risk, union_state1, union_state2, union_strict_model, union_strict_matrix,
     state_start_summary, state_end_summary)
  invisible(gc(full = TRUE))
  message("[Union comparison memory] Full historic Risk Table released before interval-rate summaries.")

  rate_rows <- list()
  rr_index <- 0L
  for (domain_name in domain_levels_union) {
    weight_field <- if (domain_name == "Full analysis area") {
      "ASM_BLOCK_AREA_M2"
    } else {
      "ASM_UNION_OVERLAP_M2"
    }
    domain_area_value <- domain_total_area %>%
      filter(Analysis_Domain == domain_name) %>%
      pull(domain_area_m2)
    domain_area_value <- if (length(domain_area_value) > 0) domain_area_value[1] else NA_real_

    for (spec in transition_specs_union) {
      transition_name <- spec[[1]]
      event_field <- spec[[2]]
      risk_field <- spec[[3]]
      if (!all(c(event_field, risk_field, weight_field, "M3_MODEL_ELIGIBLE_PRIMARY") %in% names(rate_source))) next

      # Use the same primary model-eligibility filter as the principal KM/AG/Cox analyses,
      # but construct only a narrow temporary table for this one transition/domain.
      tmp <- rate_source %>%
        transmute(
          Reach = reach_label,
          Analysis_Domain = domain_name,
          Transition = transition_name,
          tstart_yr = as.numeric(tstart_yr),
          tstop_yr = as.numeric(tstop_yr),
          duration = as.numeric(duration),
          MODEL_ELIGIBLE = as.integer(M3_MODEL_ELIGIBLE_PRIMARY),
          DOMAIN_WEIGHT_M2 = as.numeric(.data[[weight_field]]),
          EVENT = as.integer(.data[[event_field]]),
          AT_RISK = as.integer(.data[[risk_field]])
        ) %>%
        filter(
          MODEL_ELIGIBLE == 1L,
          AT_RISK == 1L,
          is.finite(DOMAIN_WEIGHT_M2), DOMAIN_WEIGHT_M2 > 0,
          is.finite(duration), duration > 0
        ) %>%
        group_by(Reach, Analysis_Domain, Transition, tstart_yr, tstop_yr) %>%
        summarise(
          interval_duration_yr = first(duration),
          event_area_m2 = sum(DOMAIN_WEIGHT_M2 * EVENT, na.rm = TRUE),
          at_risk_area_time_m2_yr = sum(DOMAIN_WEIGHT_M2 * duration, na.rm = TRUE),
          at_risk_area_m2 = sum(DOMAIN_WEIGHT_M2, na.rm = TRUE),
          interval_rows = n(),
          events = sum(EVENT == 1L, na.rm = TRUE),
          .groups = "drop"
        ) %>%
        mutate(
          domain_area_m2 = domain_area_value,
          annual_at_risk_area_rate = ifelse(
            at_risk_area_time_m2_yr > 0,
            event_area_m2 / at_risk_area_time_m2_yr,
            NA_real_
          ),
          annual_at_risk_area_percent = 100 * annual_at_risk_area_rate,
          annual_affected_area_km2 = event_area_m2 / interval_duration_yr / 1e6,
          annual_affected_domain_percent = ifelse(
            domain_area_m2 > 0,
            100 * (event_area_m2 / interval_duration_yr) / domain_area_m2,
            NA_real_
          )
        )
      rr_index <- rr_index + 1L
      rate_rows[[rr_index]] <- tmp
      rm(tmp)
      invisible(gc(full = FALSE))
    }
  }

  full_union_interval_rates <- bind_rows(rate_rows) %>%
    mutate(
      Analysis_Domain = factor(Analysis_Domain, levels = domain_levels_union),
      Transition = factor(
        Transition,
        levels = c(
          "Reactivation", "Storage formation", "Stabilisation",
          "Storage reworking", "Floodplain entering storage"
        )
      )
    )
  write_csv(
    full_union_interval_rates,
    file.path(out_dir, "12_full_vs_union_interval_transition_rates.csv")
  )

  full_union_rate_summary <- full_union_interval_rates %>%
    group_by(Reach, Analysis_Domain, Transition) %>%
    summarise(
      total_event_area_m2 = sum(event_area_m2, na.rm = TRUE),
      total_at_risk_area_time_m2_yr = sum(at_risk_area_time_m2_yr, na.rm = TRUE),
      observation_period_area_rate = total_event_area_m2 / total_at_risk_area_time_m2_yr,
      observation_period_area_rate_percent = 100 * observation_period_area_rate,
      total_events = sum(events, na.rm = TRUE),
      .groups = "drop"
    )
  write_csv(
    full_union_rate_summary,
    file.path(out_dir, "12_full_vs_union_transition_rate_summary.csv")
  )

  if (nrow(full_union_interval_rates) > 0) {
    p_domain_rate <- ggplot(
      full_union_interval_rates,
      aes(x = tstop_yr, y = annual_at_risk_area_percent, colour = Transition)
    ) +
      geom_line(linewidth = 0.7, na.rm = TRUE) +
      geom_point(size = 1.1, na.rm = TRUE) +
      facet_wrap(~Analysis_Domain, nrow = 1, scales = "free_y") +
      labs(
        title = paste0(reach_label, ": annual area-transition rates"),
        subtitle = "Transitioned area per year as a percentage of matching at-risk state area",
        x = "Interval end year",
        y = "At-risk area transitioning per year (%)",
        colour = "Transition"
      ) +
      theme_bw(base_size = 12) +
      theme(
        panel.grid.minor = element_blank(),
        plot.title = element_text(face = "bold", hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5),
        strip.text = element_text(face = "bold")
      )
    safe_plot_save(
      p_domain_rate,
      "12_full_vs_union_interval_transition_rates.png",
      width = 13,
      height = 6
    )

    p_domain_area <- ggplot(
      full_union_interval_rates,
      aes(x = tstop_yr, y = annual_affected_domain_percent, colour = Transition)
    ) +
      geom_line(linewidth = 0.7, na.rm = TRUE) +
      geom_point(size = 1.1, na.rm = TRUE) +
      facet_wrap(~Analysis_Domain, nrow = 1, scales = "free_y") +
      labs(
        title = paste0(reach_label, ": annual affected area"),
        subtitle = "Transitioned area per year as a percentage of the complete domain area",
        x = "Interval end year",
        y = "Analysis domain affected per year (%)",
        colour = "Transition"
      ) +
      theme_bw(base_size = 12) +
      theme(
        panel.grid.minor = element_blank(),
        plot.title = element_text(face = "bold", hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5),
        strip.text = element_text(face = "bold")
      )
    safe_plot_save(
      p_domain_area,
      "12_full_vs_union_annual_affected_area.png",
      width = 13,
      height = 6
    )
    rm(p_domain_rate, p_domain_area)
  }

  rm(rate_source, rate_rows)
  invisible(gc(full = TRUE))
  message("[Union comparison] Memory-safe comparison complete.")
} else {
  writeLines(
    c(
      paste0("FRAF v17.10.14.4 union comparison skipped: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
      paste0("Reach: ", reach_label),
      "Section 12 Full analysis area versus historical activity-belt comparison was not run.",
      "Reason: RunUnionComparison is FALSE (v17.10.13 memory-safe default).",
      "Principal transition, KM, AG, Cox, PH and historic Broad FP->AD analyses are unaffected.",
      "Enable RunUnionComparison only for a dedicated sensitivity run with sufficient RAM/commit space."
    ),
    file.path(out_dir, "12_UNION_COMPARISON_SKIPPED_MEMORY_SAFE.txt"),
    useBytes = TRUE
  )
  message("[Union comparison] Skipped (v17.10.13 memory-safe default).")
  invisible(gc(full = TRUE))
}

# -----------------------------
# [FRAF archive / workflow]
# Spatial summary exports join model results to PLACE geometry only as needed;
# the canonical interval risk/prediction tables themselves remain non-spatial.
# [FRAF archive / code note]
# Spatial exports for figures/verification are derived from the fixed
# PLACE geometry; full panel history remains in the non-spatial table.
# 13. Export spatial KM summaries
# -----------------------------

if (ExportSpatialSummary) {
  place_summary <- risk_valid %>%
    group_by(PLACE_ID) %>%
    summarise(
      first_reactivation_year = safe_first(tstop_yr[REACTIVATE_EVT == 1]),
      first_initial_floodplain_reactivation_year = safe_first(tstop_yr[BASE_REACTIVATE_EVT == 1]),
      first_storage_year = safe_first(tstop_yr[STORAGE_EVT == 1]),
      first_stabilisation_year = safe_first(tstop_yr[STABILISE_EVT == 1]),
      first_state_transition_year = safe_first(tstop_yr[ANY_STATE_EVT == 1]),
      ever_reactivated = as.integer(any(REACTIVATE_EVT == 1, na.rm = TRUE)),
      initial_floodplain_cohort = as.integer(any(INIT_FP_COHORT == 1, na.rm = TRUE)),
      ever_initial_floodplain_reactivated = as.integer(any(BASE_REACTIVATE_EVT == 1, na.rm = TRUE)),
      ever_storage = as.integer(any(STORAGE_EVT == 1, na.rm = TRUE)),
      ever_stabilised = as.integer(any(STABILISE_EVT == 1, na.rm = TRUE)),
      ever_state_transition = as.integer(any(ANY_STATE_EVT == 1, na.rm = TRUE)),
      n_reactivation_events = sum(REACTIVATE_EVT == 1, na.rm = TRUE),
      n_initial_floodplain_reactivation_events = sum(BASE_REACTIVATE_EVT == 1, na.rm = TRUE),
      n_storage_events = sum(STORAGE_EVT == 1, na.rm = TRUE),
      n_stabilisation_events = sum(STABILISE_EVT == 1, na.rm = TRUE),
      n_state_transition_events = sum(ANY_STATE_EVT == 1, na.rm = TRUE),
      .groups = "drop"
    )

  optional_place_summaries <- list(
    DIST_CL_REF = "mean_dist_cl_ref",
    DIST_CL_CURR = "mean_dist_cl_curr",
    DIST_CL_PREV = "mean_dist_cl_prev",
    DIST_ACTIVE_CURR = "mean_dist_active_curr",
    DIST_WATER_CURR = "mean_dist_water_curr",
    DIST_ACTIVE_PREV = "mean_dist_active_prev",
    DIST_WATER_PREV = "mean_dist_water_prev",
    ASM_DIST_FREQ_PREV = "mean_asm_dist_freq_prev",
    ASM_MAX_QUIET_PREV = "max_asm_quiet_prev"
  )

  for (src in names(optional_place_summaries)) {
    dst <- optional_place_summaries[[src]]
    if (src %in% names(risk_valid)) {
      tmp <- risk_valid %>%
        group_by(PLACE_ID) %>%
        summarise(.value = if (grepl("MAX_QUIET", src)) safe_max(.data[[src]]) else safe_mean(.data[[src]]), .groups = "drop")
      names(tmp)[names(tmp) == ".value"] <- dst
      place_summary <- left_join(place_summary, tmp, by = "PLACE_ID")
    }
  }

  if (!exists("PlacePolygons") || is.null(PlacePolygons)) {
    warning("ExportSpatialSummary is TRUE, but PlacePolygons is not available. Spatial summary skipped.")
  } else {

    place_sf <- tryCatch(
      sf::st_as_sf(PlacePolygons),
      error = function(e) {
        warning("Could not convert PlacePolygons to sf. Spatial summary skipped: ", conditionMessage(e))
        NULL
      }
    )

    if (!is.null(place_sf)) {

      geom_key <- dplyr::case_when(
        "PLACE_ID" %in% names(place_sf) ~ "PLACE_ID",
        "BLOCK_ID" %in% names(place_sf) ~ "BLOCK_ID",
        TRUE ~ NA_character_
      )

      if (is.na(geom_key)) {
        warning(
          "ExportSpatialSummary is TRUE, but PlacePolygons contains neither PLACE_ID nor BLOCK_ID. ",
          "Available fields: ", paste(names(place_sf), collapse = ", "),
          ". Spatial summary skipped."
        )
      } else {

        message("[Spatial summary] PLACE geometry key selected: ", geom_key)

        # Use character keys to avoid integer conversion failures and to allow
        # IDs copied from either PLACE_ID or BLOCK_ID. Do not assume the sf
        # geometry column is named "geometry"; QGIS/R may use another active
        # geometry column name.
        geom_col <- attr(place_sf, "sf_column")
        if (is.null(geom_col) || !(geom_col %in% names(place_sf))) {
          warning(
            "ExportSpatialSummary is TRUE, but PlacePolygons has no active sf geometry column. ",
            "Spatial summary skipped."
          )
        } else {
          place_geom <- place_sf %>%
            dplyr::mutate(PLACE_ID = as.character(.data[[geom_key]])) %>%
            dplyr::filter(!is.na(PLACE_ID), PLACE_ID != "") %>%
            dplyr::group_by(PLACE_ID) %>%
            dplyr::slice(1) %>%
            dplyr::ungroup() %>%
            dplyr::select(PLACE_ID, dplyr::all_of(geom_col))

          sf::st_geometry(place_geom) <- geom_col

        place_summary_join <- place_summary %>%
          dplyr::mutate(PLACE_ID = as.character(PLACE_ID))

        place_km <- place_geom %>%
          dplyr::left_join(place_summary_join, by = "PLACE_ID")

          sf::st_write(
            place_km,
            file.path(out_dir, "13_PLACE_KM_summary.gpkg"),
            layer = "PLACE_KM_summary",
            delete_dsn = TRUE,
            quiet = TRUE
          )
        }
      }
    }
  }
}

writeLines(
  c(
    paste0("FRAF v17.10.15.1 historic interpretive branch completed: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
    paste0("Reach: ", reach_label),
    paste0("DS->AD interpretive branch: ", ifelse(isTRUE(RunStorageReworkInterpretive), "enabled", "disabled")),
    paste0("Broad Floodplain->AD historic branch: enabled; risk rows=", nrow(risk_floodplain_broad), "; events=", sum(risk_floodplain_broad$FP_REACTIVATE_EVT == 1L, na.rm = TRUE)),
    paste0("Outputs written to: ", out_dir)
  ),
  file.path(out_dir, "00_HISTORIC_BRANCH_COMPLETED.txt"), useBytes = TRUE
)
message("Historic KM/AG/total-time Cox branch complete for ", reach_label, ".")

} else {
  writeLines(
    c(
      paste0("FRAF v17.10.15.1 historic interpretive branch skipped: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
      paste0("Reach: ", reach_label),
      paste0("Analysis mode: ", analysis_mode),
      "Reason: Prediction-only mode deliberately bypasses the historic Risk Table load and all historic modelling.",
      paste0("Outputs written to: ", out_dir)
    ),
    file.path(out_dir, "00_HISTORIC_BRANCH_SKIPPED_PREDICTION_MODE.txt"),
    useBytes = TRUE
  )
  message("[Mode] Historic branch bypassed; prediction will start without a historic Risk Table in memory.")
}

# ---------------------------------------------------------------------------
# v17.10.13 post-historic memory release. In Historic-only mode this happens
# before Review Pack assembly; Prediction-only has no historic objects to clear.
# ---------------------------------------------------------------------------
# v17.10.9 prediction-boundary memory release.
# All scientific historic outputs have already been written to disk above.
# Remove large historic tables, fitted models and ggplot objects before opening
# the prediction Risk Table. The review pack is file-based and does not depend
# on these in-memory objects. Functions and user/QGIS parameters are retained.
# ---------------------------------------------------------------------------
# [FRAF archive / code note]
# Release resident historic model objects before the next independent
# process; avoid retaining unnecessary model frames and graphics.
# [FRAF archive / Historic/QA function: fraf_release_historic_memory]
# Release retrospective analysis data before the separate prediction process or review assembly.
fraf_release_historic_memory <- function(env = parent.frame()) {
  nm <- ls(envir = env, all.names = TRUE)
  cleanup_regex <- paste0(
    "^(risk($|_)|cox_|km_|ag_|p_|broad_|state_partition|m3_semantic|temporal_spatial|",
    "spatial_|storage_|erosion_|deposition_|stabilise_|any_|union_|place_|ph_|",
    "definition_|local_definition|t2_|transition_|domain_|base_|warning_rows$|",
    "strict_|pure_|event_|fp_condition|initial_fp|field_inventory$|run_diagnostics$|",
    "model_eligibility|primary_|reactivation_|outside_union|full_union|competing_|state_)"
  )
  preserve <- c(
    "out_dir", "reach_label", "RiskTable", "RiskLayerName", "OutputFolder",
    "RunPrediction", "RunBroadFloodplainPrediction", "ForecastOrigins",
    "OriginInterpretation", "MinimumTrainingEvents", "WriteParquet",
    "WriteFullFittedPredictions", "FutureCovariateTable", "FutureLayerName",
    "FutureStartTime", "FutureStopTime", "MamoreReactivationExposure",
    "MamoreStorageExposure"
  )

  drop <- nm[grepl(cleanup_regex, nm)]
  if ("PlacePolygons" %in% nm) drop <- unique(c(drop, "PlacePolygons"))

  # Catch any unexpectedly named large historic object as well. At this boundary
  # all analysis outputs are already on disk, so no large non-function object is
  # required by prediction. Ten MiB is deliberately conservative and protects
  # future revisions that introduce a large object under a new name.
  non_functions <- nm[vapply(nm, function(x) {
    !is.function(get(x, envir = env, inherits = FALSE))
  }, logical(1))]
  non_functions <- setdiff(non_functions, preserve)
  large_drop <- non_functions[vapply(non_functions, function(x) {
    as.numeric(utils::object.size(get(x, envir = env, inherits = FALSE))) > 10 * 1024^2
  }, logical(1))]
  drop <- unique(c(drop, large_drop))

  # Never remove functions: several helpers have names that match the broad
  # prefixes above but are still used by the prediction/review stages.
  drop <- drop[vapply(drop, function(x) {
    obj <- get(x, envir = env, inherits = FALSE)
    !is.function(obj)
  }, logical(1))]
  drop <- setdiff(drop, preserve)

  if (length(drop) > 0L) {
    message("[Memory v17.10.15.1] Releasing ", length(drop),
            " historic-analysis objects, including broad transient objects, at the historic-mode boundary.")
    rm(list = drop, envir = env)
  } else {
    message("[Memory] No removable historic-analysis objects found at the historic-mode boundary.")
  }
  invisible(gc(full = TRUE))
  message("[Memory v17.10.15.1] Historic-analysis cleanup and full garbage collection complete.")
  invisible(drop)
}

if (isTRUE(run_historic_mode)) {
  fraf_release_historic_memory(environment())
  message("[Mode] Historic-only memory released before Review Pack assembly (v17.10.15.1 reduced-history-aligned).")
}

# [FRAF archive / code note]
# Prediction code is isolated from the historic branch to prevent R
# memory fragmentation from contaminating the rolling fit workflow.
# ============================================================================
# PREDICTIVE BRANCH — v17.9.11-derived, isolated to avoid object collisions
# [FRAF archive / workflow]
# Prediction outputs use 20_ for independently held-out origin tests, 21_ for
# full-record frozen fitting, and 22_ for truly future (unobserved) targets.
# Output prefixes: 20_ rolling validation, 21_ final frozen models, 22_ Tn+1.
# ============================================================================
# [FRAF archive / logic boundary]
# Errors in the Prediction branch are captured for review-pack preservation;
# scientific completion is not claimed when a model/forecast failed.
prediction_error_message <- NULL

# [FRAF archive / logic boundary]
# Start prediction only in the isolated Prediction-only execution mode.
if (isTRUE(RunPrediction)) {
  message("[Prediction] Starting v17.10.15.1 Prediction-only rolling-origin/future branch in this fresh R process.")
  prediction_error_message <- tryCatch({
    local({
    # ============================================================================
    # 21-8-26
    # v17.9.11: Adds a separate broad floodplain-reactivation prediction model.
    #           The established strict Stabilised Floodplain -> Active Domain model is
    #           retained unchanged for process-specific interpretation. The new
    #           floodplain_reactivation_broad model uses Stage 4 Step 3 v6.7 fields
    #           FP_REACTIVATE_RISK_SET_PRIMARY / FP_REACTIVATE_EVT_PRIMARY, thereby
    #           admitting tightly guarded undisturbed pre-existing floodplain as well
    #           as recognised Stabilised Floodplain. This prevents inherited floodplain
    #           immediately ahead of a migrating bank from being structurally absent
    #           from erosion forecasts. Future Tn+1 handling is schema-safe for the
    #           corresponding Module 5e broad risk field.
    # v17.9.7: Adds a fourth prediction model for Depositional Storage -> Active Domain
    #          (storage reworking), using the authoritative Stage 4 Step 3 primary
    # v17.9.7 fixes storage-rework risk-set QA and non-estimable-model output safety.
    #          STORAGE_REWORK_RISK_SET_PRIMARY / legacy fields are checked for
    #          informative 1-values. Because storage reworking and stabilisation
    #          both originate in Depositional Storage, STABILISE_RISK_MODEL is used
    #          as the canonical fallback if the dedicated rework risk set is empty.
    #          apply_fitted_model() now uses safe fixed-length risk/event vectors,
    #          so a non-estimable model cannot crash tibble construction.
    #          STORAGE_REWORK risk/event fields. For Jamuna it uses interval-start
    #          distance to the Active Domain; for Mamoré it uses the same lagged
    #          channel-margin/outer-bank erosion framework as floodplain reactivation.
    #          Assemblage-history terms describe storage occupancy, prior storage
    #          formation and quiet/reworking history.
    # v17.9.3: Plot-safe rolling-origin validation.
    #          Fixes ggplot2 incompatibility between free facet scales and coord_equal(),
    #          wraps validation-figure export so a graphics failure cannot terminate model
    #          output generation, and suppresses harmless FALSE returns from optional Parquet.
    #          Retains v17.9.2 robust metadata/validation and optional future-table handling.
    # Integrated v17.9.11-derived prediction engine; model definitions remain aligned with the historic branch.
    #
    # PURPOSE
    #   1. Refit the established process-specific Cox models plus a separate broad
    #      eligible-floodplain -> Active Domain prediction model using the v17.8d predictor
    #      frameworks and authoritative Stage 4 Step 3 primary risk/event fields.
    #   2. Export machine-readable coefficients, training scalers and uncentred
    #      baseline cumulative hazards.
    #   3. Perform leakage-safe rolling-origin prediction at T10, T20 and T30
    #      (or user-supplied origins), always training only on intervals ending at
    #      or before the forecast origin.
    #   4. Export absolute next-interval probabilities, calibration/discrimination
    #      metrics, risk-decile calibration data and top-area capture statistics.
    #   5. Optionally apply the final frozen models to a separate Tn covariate table
    #      for a genuine Tn+1 forecast, without requiring Tn+1 geometry.
    #
    # IMPORTANT
    #   - In v17.10 this prediction engine is embedded after the historic branch; it does not replace its KM,
    #     AG, proportional-hazards, definition-sensitivity or streamed storage-QA
    #     outputs.
    #   - Predictor centring/scaling is estimated from each training window only.
    #   - The prediction models use interval gap time (0 to interval duration) so a
    #     baseline-hazard increment can be estimated for a future interval duration.
    #     The v17.8d total-time Cox models remain the interpretive models.
    #   - Places outside a transition risk set are retained with status
    #     'not_in_risk_set'; they are not classified as low risk.
    #   - Mamoré storage retains two estimands:
    #       * full-event assemblage-history model;
    #       * local-position model restricted to supported lagged-channel geometry.
    # ============================================================================

    suppressPackageStartupMessages({
      library(sf)
      library(dplyr)
      library(readr)
      library(tidyr)
      library(survival)
      library(ggplot2)
    })

    sf::sf_use_s2(FALSE)
    options(stringsAsFactors = FALSE)

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Prediction branch has its own helper scope and fresh projected-column reader;
    # do not pass large objects left from Historic mode into this local environment.
    # 0. Parameters and general helpers
    # -----------------------------------------------------------------------------

    out_dir <- if (exists("OutputFolder") && !is.null(OutputFolder) && nzchar(OutputFolder)) {
      OutputFolder
    } else {
      tempdir()
    }
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

    if (!exists("ForecastOrigins") || is.null(ForecastOrigins) || !nzchar(ForecastOrigins)) {
      ForecastOrigins <- "10,20,30"
    }
    if (!exists("MinimumTrainingEvents") || is.null(MinimumTrainingEvents)) MinimumTrainingEvents <- 20
    MinimumTrainingEvents <- max(1L, as.integer(MinimumTrainingEvents)[1])
    if (!exists("WriteParquet") || is.null(WriteParquet)) WriteParquet <- TRUE
    if (isTRUE(WriteParquet) && !requireNamespace("arrow", quietly = TRUE)) {
      message("[Parquet] Package 'arrow' is unavailable; Parquet output disabled for this run and compressed CSV retained.")
      WriteParquet <- FALSE
    }
    if (!exists("WriteFullFittedPredictions") || is.null(WriteFullFittedPredictions)) WriteFullFittedPredictions <- FALSE
    if (!exists("FutureCovariateTable") || is.null(FutureCovariateTable) ||
        length(FutureCovariateTable) == 0L || all(is.na(FutureCovariateTable))) {
      FutureCovariateTable <- ""
    }
    if (!exists("FutureLayerName") || is.null(FutureLayerName)) FutureLayerName <- "Risk Table"
    if (!exists("FutureStartTime") || is.null(FutureStartTime)) FutureStartTime <- -1
    if (!exists("FutureStopTime") || is.null(FutureStopTime)) FutureStopTime <- -1

    # [FRAF archive / Prediction function: resolve_selection]
    # Interpret QGIS selection parameters consistently as index or text.
    resolve_selection <- function(x, labels, default_index = 1L) {
      if (is.null(x) || length(x) == 0L || is.na(x[1])) return(labels[default_index])
      xi <- suppressWarnings(as.integer(x[1]))
      if (is.finite(xi)) {
        # QGIS R provider selections are normally zero based.
        idx <- xi + 1L
        if (idx >= 1L && idx <= length(labels)) return(labels[idx])
      }
      txt <- trimws(as.character(x[1]))
      hit <- which(tolower(labels) == tolower(txt))
      if (length(hit) > 0L) return(labels[hit[1]])
      labels[default_index]
    }

    reach_label <- resolve_selection(
      if (exists("ReachName")) ReachName else NULL,
      c("Mamoré", "Jamuna"),
      1L
    )
    origin_mode <- resolve_selection(
      if (exists("OriginInterpretation")) OriginInterpretation else NULL,
      c("Unique interval-start rank", "Elapsed study year"),
      1L
    )
    react_exposure <- resolve_selection(
      if (exists("MamoreReactivationExposure")) MamoreReactivationExposure else NULL,
      c("Full-width channel-margin zone", "Half-width channel-margin zone"),
      1L
    )
    storage_exposure <- resolve_selection(
      if (exists("MamoreStorageExposure")) MamoreStorageExposure else NULL,
      c("Half-width bank-adjacent zone", "Full-width bank-adjacent zone"),
      1L
    )

    message("Reach: ", reach_label)
    message("Forecast-origin interpretation: ", origin_mode)
    message("Mamore reactivation exposure: ", react_exposure)
    message("Mamore storage exposure: ", storage_exposure)

    # [FRAF archive / Prediction function: int01]
    # Normalise numeric, logical, or missing event/risk flags to a 0/1 integer representation.
    int01 <- function(x, default = 0L) {
      if (is.null(x)) return(integer(0))
      if (is.factor(x)) x <- as.character(x)
      y <- suppressWarnings(as.integer(as.numeric(x)))
      y[is.na(y)] <- default
      y[y != 0L] <- 1L
      y
    }

    # [FRAF archive / Prediction function: num]
    # Convert candidate numeric variables while preserving invalid values as missing.
    num <- function(x) suppressWarnings(as.numeric(x))

    # [FRAF archive / Prediction function: clean_key]
    # Standardise PLACE/BLOCK identifiers before model-frame joins and exports.
    clean_key <- function(x) {
      y <- trimws(as.character(x))
      y[y == "" | is.na(y)] <- NA_character_
      numeric_like <- grepl("^-?[0-9]+(\\.0+)?$", y)
      y[numeric_like] <- sub("\\.0+$", "", y[numeric_like])
      y
    }

    # [FRAF archive / Prediction function: safe_name]
    # Normalise names for reusable model keys, output files or plot labels.
    safe_name <- function(x) {
      x <- gsub("[^A-Za-z0-9_-]+", "_", as.character(x))
      x <- gsub("_+", "_", x)
      gsub("^_|_$", "", x)
    }

    # [FRAF archive / Prediction function: write_csv_gz]
    # Stream or write compressed row-level prediction artifacts.
    write_csv_gz <- function(x, path) {
      con <- gzfile(path, open = "wb")
      tryCatch(
        readr::write_csv(x, con, na = ""),
        finally = close(con)
      )
    }

    # [FRAF archive / Prediction function: write_optional_parquet]
    # Attempt optional Parquet export without making it authoritative for large streaming results.
    write_optional_parquet <- function(x, path) {
      if (!isTRUE(WriteParquet)) return(FALSE)
      if (!requireNamespace("arrow", quietly = TRUE)) {
        message("[Parquet] Package 'arrow' is unavailable; compressed CSV retained.")
        return(FALSE)
      }
      tryCatch({
        arrow::write_parquet(x, path, compression = "zstd")
        TRUE
      }, error = function(e) {
        message("[Parquet] Failed for ", basename(path), ": ", conditionMessage(e))
        FALSE
      })
    }

    # Graphics should never prevent model/prediction tables from being written.
    # [FRAF archive / Prediction function: safe_ggsave]
    # Guard plot export so optional graphics failure does not discard model tables.
    safe_ggsave <- function(filename, plot, ...) {
      tryCatch({
        ggplot2::ggsave(filename = filename, plot = plot, ...)
        invisible(TRUE)
      }, error = function(e) {
        message("[Plot] Could not write ", basename(filename), ": ", conditionMessage(e))
        invisible(FALSE)
      })
    }

    # [FRAF archive / Prediction function: parse_gpkg_source]
    # Split a GeoPackage path and optional layername into explicit source identifiers.
    parse_gpkg_source <- function(x, layer_hint = NULL) {
      x <- as.character(x)[1]
      layer_from_uri <- NA_character_
      if (grepl("\\|layername=", x, ignore.case = TRUE)) {
        parts <- strsplit(x, "\\|")[[1]]
        path <- parts[1]
        lp <- parts[grepl("^layername=", parts, ignore.case = TRUE)]
        if (length(lp) > 0L) layer_from_uri <- sub("^layername=", "", lp[1], ignore.case = TRUE)
      } else {
        path <- x
      }
      if (grepl("dbname=", path, ignore.case = TRUE)) {
        p2 <- sub(".*dbname='([^']+)'.*", "\\1", path)
        if (!identical(path, p2)) path <- p2
      }
      list(
        path = path,
        layer = dplyr::coalesce(
          dplyr::na_if(layer_from_uri, ""),
          dplyr::na_if(as.character(layer_hint)[1], "")
        )
      )
    }

    # [FRAF archive / Prediction function: choose_gpkg_layer]
    # Select the intended non-spatial risk table, failing on ambiguous GeoPackage sublayers.
    choose_gpkg_layer <- function(path, requested = NULL) {
      ls <- sf::st_layers(path, options = "LIST_ALL_TABLES=YES")
      nm <- ls$name
      requested <- as.character(requested)[1]
      if (!is.na(requested) && nzchar(trimws(requested)) && requested %in% nm) return(requested)
      preferred <- c("RISK_TABLE", "Risk Table", "Risk_Table", "RiskTable", "Stage_4_Risk_Table", "Stage4_Risk_Table")
      hit <- preferred[preferred %in% nm]
      if (length(hit) > 0L) return(hit[1])
      noncore <- setdiff(nm, c("PLACE_interval_long", "KM_blocks", "INPUT"))
      if (length(noncore) == 1L) return(noncore[1])
      stop("Cannot identify Risk Table layer. Available: ", paste(nm, collapse = ", "))
    }

    # [FRAF archive / Prediction function: read_table_any]
    # Read a recognised input representation and remove non-modelling geometry.
    read_table_any <- function(source, layer_hint = NULL) {
      if (inherits(source, "sf")) return(sf::st_drop_geometry(source))
      source <- as.character(source)[1]
      if (!nzchar(source)) stop("Empty table source.")
      if (grepl("\\.gpkg($|\\|)", source, ignore.case = TRUE)) {
        src <- parse_gpkg_source(source, layer_hint)
        lyr <- choose_gpkg_layer(src$path, src$layer)
        obj <- st_read_qgis_safe(src$path, layer = lyr, quiet = FALSE, options = "LIST_ALL_TABLES=YES")
        if (inherits(obj, "sf")) sf::st_drop_geometry(obj) else as.data.frame(obj)
      } else if (grepl("\\.csv\\.gz$", source, ignore.case = TRUE)) {
        readr::read_csv(source, show_col_types = FALSE, progress = FALSE)
      } else if (grepl("\\.csv$", source, ignore.case = TRUE)) {
        readr::read_csv(source, show_col_types = FALSE, progress = FALSE)
      } else if (grepl("\\.parquet$", source, ignore.case = TRUE)) {
        if (!requireNamespace("arrow", quietly = TRUE)) stop("Reading Parquet requires the R package 'arrow'.")
        as.data.frame(arrow::read_parquet(source))
      } else {
        stop("Unsupported table source: ", source)
      }
    }

    # v17.10.7: raw columns that can be required by any current prediction
    # transition, including PRIMARY/legacy event-risk fallbacks and the raw local
    # Mamore geometry needed to recreate canonical prediction aliases. This is a
    # deliberately conservative superset; model-specific compacting still occurs
    # later after reach/framework selection.
    prediction_input_candidates <- unique(c(
      "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
      "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "ASM_BLOCK_AREA_M2",
      "REACTIVATE_EVT_PRIMARY", "REACTIVATE_EVT",
      "STORAGE_EVT_PRIMARY", "STORAGE_EVT",
      "STABILISE_EVT_PRIMARY", "STABILISE_EVT",
      "REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET",
      "STORAGE_RISK_SET_PRIMARY", "STORAGE_RISK_SET",
      "STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET",
      "STORAGE_REWORK_EVT_PRIMARY", "STORAGE_REWORK_EVT",
      "STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET",
      "FP_REACTIVATE_EVT_PRIMARY", "FP_REACTIVATE_EVT",
      "FP_REACTIVATE_RISK_SET_PRIMARY", "FP_REACTIVATE_RISK_SET",
      "FP_REACTIVATE_SOURCE_PRIMARY", "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY",
      "ASM_DOM_RATIO_PREV", "ASM_N_EPISODES_PREV", "ASM_MAX_QUIET_PREV",
      "ASM_COV_FRAC", "ASM_N_REACTIVATE_PREV", "ASM_STORAGE_FRAC_PREV",
      "ASM_N_STORAGE_EVT_PREV", "ASM_STAB_FP_FRAC_PREV",
      "ASM_QUIET_SINCE_PREV", "ASM_N_STABILISE_PREV",
      "DIST_ACTIVE_CURR", "DIST_CL_REF", "DIST_CL_CURR", "DIST_WATER_CURR",
      "GEOM_SUPPORT_PREV", "DIST_CHANNEL_PREV", "INSIDE_CHANNEL_PREV",
      "REL_CHANNEL_POS_PREV",
      "NEAR_CHANNEL_HALF_PREV", "NEAR_CHANNEL_FULL_PREV",
      "NEAR_BANK_HALF_PREV", "NEAR_BANK_FULL_PREV",
      "OUTER_CURV_REACT_HALF_PREV", "OUTER_CURV_REACT_FULL_PREV",
      "INNER_CURV_STORAGE_HALF_PREV", "INNER_CURV_STORAGE_FULL_PREV",
      "OUTER_CURV_STORAGE_HALF_PREV", "OUTER_CURV_STORAGE_FULL_PREV",
      "OUTER_BANK_PREV", "INNER_BANK_PREV",
      "MAM_NEAR_CHANNEL_PREV", "MAM_OUTER_REACT_EXPOSED_PREV",
      "MAM_OUTER_CURV_REACT_PREV", "MAM_NEAR_BANK_STORAGE_PREV",
      "MAM_INNER_STORAGE_EXPOSED_PREV", "MAM_INNER_CURV_STORAGE_PREV",
      "MAM_OUTER_STORAGE_EXPOSED_PREV", "MAM_OUTER_CURV_STORAGE_PREV"
    ))

    # [FRAF archive / Prediction function: sql_quote_identifier]
    # Protect SQL column/layer identifiers in projected GeoPackage reads.
    sql_quote_identifier <- function(x) {
      paste0('"', gsub('"', '""', as.character(x), fixed = TRUE), '"')
    }

    # [FRAF archive / code note]
    # This column-projection reader avoids loading hundreds of unused fields
    # from a multi-million-row GeoPackage into memory.
    # [FRAF archive / Prediction function: read_prediction_table_projected]
    # Read only prediction-needed source columns to avoid loading the full wide risk table.
    read_prediction_table_projected <- function(source, layer_hint = NULL) {
      # QGIS normally supplies RiskTable as a GeoPackage path. For that path,
      # inspect one row only to discover the schema, then project columns in SQL
      # before the 4-million-row table enters R memory. Never fall back to a full
      # GeoPackage read if projection fails: that would recreate the OOM condition.
      if (inherits(source, "sf")) {
        dat <- sf::st_drop_geometry(source)
        keep <- intersect(prediction_input_candidates, names(dat))
        message("[Memory] Prediction input supplied in-memory; retaining ",
                length(keep), " of ", ncol(dat), " columns.")
        return(dat[, keep, drop = FALSE])
      }

      source_chr <- as.character(source)[1]
      if (!nzchar(source_chr)) stop("Empty prediction Risk Table source.")

      if (grepl("\\.gpkg($|\\|)", source_chr, ignore.case = TRUE)) {
        src <- parse_gpkg_source(source_chr, layer_hint)
        lyr <- choose_gpkg_layer(src$path, src$layer)

        schema_obj <- st_read_qgis_safe(
          src$path, layer = lyr, quiet = TRUE,
          options = "LIST_ALL_TABLES=YES", n_max = 1
        )
        available <- names(schema_obj)
        rm(schema_obj)
        keep <- intersect(prediction_input_candidates, available)

        # PLACE_ID/BLOCK_ID can alias one another later, but at least one key and
        # both survival-time fields must be physically present in the source.
        if (!any(c("PLACE_ID", "BLOCK_ID") %in% keep) ||
            !all(c("tstart_yr", "tstop_yr") %in% keep)) {
          stop(
            "[Prediction projection QA] GeoPackage layer '", lyr,
            "' lacks the minimum key/time schema. Available fields were inspected ",
            "without loading the full table."
          )
        }

        select_sql <- paste(vapply(keep, sql_quote_identifier, character(1)), collapse = ", ")
        query_sql <- paste0(
          "SELECT ", select_sql, " FROM ", sql_quote_identifier(lyr)
        )
        message(
          "[Memory] Prediction GeoPackage projection: selecting ", length(keep),
          " of ", length(available), " source columns before row materialisation."
        )

        obj <- tryCatch(
          st_read_qgis_safe(src$path, query = query_sql, quiet = FALSE),
          error = function(e) {
            stop(
              "[Prediction projection QA] SQL-projected GeoPackage read failed; ",
              "full-table fallback is intentionally disabled to prevent memory overflow. ",
              "Layer=", lyr, "; error=", conditionMessage(e)
            )
          }
        )
        dat <- if (inherits(obj, "sf")) sf::st_drop_geometry(obj) else as.data.frame(obj)
        rm(obj)
        message(
          "[Memory] Projected prediction input loaded: ",
          format(nrow(dat), big.mark = ","), " rows x ", ncol(dat), " columns."
        )
        return(dat)
      }

      # Compatibility path for CSV/Parquet inputs. These formats do not use the
      # GeoPackage SQL projection above; narrow immediately after reading.
      dat <- read_table_any(source_chr, layer_hint)
      keep <- intersect(prediction_input_candidates, names(dat))
      message("[Memory] Non-GPKG prediction input narrowed immediately from ",
              ncol(dat), " to ", length(keep), " columns.")
      dat[, keep, drop = FALSE]
    }


    # Future covariate GeoPackages are not Risk Tables. Do not use the generic
    # choose_gpkg_layer() preference for a layer called "Risk Table". Instead,
    # identify the Module 5e table by the fields that define its future transition
    # populations.
    future_schema_fields <- c(
      "FP_REACTIVATE_RISK_SET_PRIMARY",
      "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY",
      "REACTIVATE_RISK_SET_PRIMARY",
      "STORAGE_RISK_SET_PRIMARY",
      "STABILISE_RISK_SET_PRIMARY",
      "STORAGE_REWORK_RISK_SET_PRIMARY"
    )

    # [FRAF archive / Prediction function: future_layer_field_names]
    # Inspect an external future-table schema before selecting model-specific fields.
    future_layer_field_names <- function(path, layer) {
      obj <- tryCatch(
        st_read_qgis_safe(
          path, layer = layer, quiet = TRUE,
          options = "LIST_ALL_TABLES=YES", n_max = 1
        ),
        error = function(e) NULL
      )
      if (is.null(obj)) return(character())
      names(obj)
    }

    # [FRAF archive / Prediction function: choose_future_gpkg_layer]
    # Select the intended prospective forecast table from a GeoPackage.
    choose_future_gpkg_layer <- function(path, requested = NULL) {
      ls <- sf::st_layers(path, options = "LIST_ALL_TABLES=YES")
      nm <- ls$name
      if (length(nm) == 0L) stop("[Future QA] No layers/tables found in future GeoPackage: ", path)

      requested <- as.character(requested)[1]
      if (is.na(requested)) requested <- ""
      requested <- trimws(requested)

      # Honour the requested layer only if it actually has future-table structure.
      if (nzchar(requested) && requested %in% nm) {
        f <- future_layer_field_names(path, requested)
        n_risk <- sum(future_schema_fields %in% f)
        if (n_risk >= 3L && "BLOCK_ID" %in% f) {
          message(
            "[Future QA] Using requested future layer '", requested,
            "' (", n_risk, "/5 PRIMARY risk fields found)."
          )
          return(requested)
        }
        warning(
          "[Future QA] Requested FutureLayerName '", requested,
          "' exists but does not look like the Module 5e future table; ",
          "searching GeoPackage layers by schema instead."
        )
      }

      scores <- lapply(nm, function(lyr) {
        f <- future_layer_field_names(path, lyr)
        data.frame(
          layer = lyr,
          n_primary_risk = sum(future_schema_fields %in% f),
          has_block = "BLOCK_ID" %in% f,
          has_time = all(c("tstart_yr", "tstop_yr") %in% f),
          has_state = any(c("STATE1_ONTOLOGY", "CURRENT_STATE_SOURCE") %in% f),
          n_fields = length(f),
          stringsAsFactors = FALSE
        )
      })
      scores <- dplyr::bind_rows(scores)
      scores$score <- (
        10 * scores$n_primary_risk +
        3 * as.integer(scores$has_block) +
        2 * as.integer(scores$has_time) +
        as.integer(scores$has_state)
      )

      candidates <- scores[
        scores$n_primary_risk >= 3L & scores$has_block,
        ,
        drop = FALSE
      ]

      if (nrow(candidates) == 0L) {
        detail <- paste(
          paste0(
            scores$layer, " [primary_risk=", scores$n_primary_risk,
            ", BLOCK_ID=", scores$has_block,
            ", time=", scores$has_time, "]"
          ),
          collapse = "; "
        )
        stop(
          "[Future QA] Could not identify a Module 5e future covariate layer in: ",
          path, ". Layers inspected: ", detail
        )
      }

      best_score <- max(candidates$score)
      best <- candidates[candidates$score == best_score, , drop = FALSE]
      if (nrow(best) > 1L) {
        stop(
          "[Future QA] More than one GeoPackage layer matches the Module 5e schema: ",
          paste(best$layer, collapse = ", "),
          ". Set FutureLayerName to the intended layer."
        )
      }

      chosen <- best$layer[1]
      message(
        "[Future QA] Auto-selected future layer '", chosen,
        "' by Module 5e schema (", best$n_primary_risk[1],
        "/4 PRIMARY risk fields found)."
      )
      chosen
    }

    # [FRAF archive / Prediction function: read_future_table_any]
    # Read the separate Tn covariate table for a genuine as-yet-unobserved next-interval forecast.
    read_future_table_any <- function(source, layer_hint = NULL) {
      source <- as.character(source)[1]
      if (!nzchar(source)) stop("[Future QA] Empty future table source.")

      if (grepl("\\.gpkg($|\\|)", source, ignore.case = TRUE)) {
        src <- parse_gpkg_source(source, layer_hint)
        lyr <- choose_future_gpkg_layer(src$path, src$layer)
        obj <- st_read_qgis_safe(
          src$path, layer = lyr, quiet = FALSE,
          options = "LIST_ALL_TABLES=YES"
        )
        out <- if (inherits(obj, "sf")) sf::st_drop_geometry(obj) else as.data.frame(obj)
        attr(out, "future_source_layer") <- lyr
        return(out)
      }

      out <- read_table_any(source, layer_hint)
      attr(out, "future_source_layer") <- "<non-GPKG table>"
      out
    }

    # [FRAF archive / Prediction function: first_existing]
    # Resolve the first compatible predictor/field alias, optionally enforcing its presence.
    first_existing <- function(dat, candidates, required = FALSE) {
      hit <- candidates[candidates %in% names(dat)]
      if (length(hit) > 0L) return(hit[1])
      if (required) stop("None of the required fields exists: ", paste(candidates, collapse = ", "))
      NA_character_
    }

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Projected-column prediction read: retain only IDs, timings, selected candidate
    # predictors, primary risk/event flags and required QA fields.
    # 1. Load and standardise the Stage 4 Step 3 Risk Table
    # -----------------------------------------------------------------------------

    risk <- read_prediction_table_projected(RiskTable, RiskLayerName)

    if (!"PLACE_ID" %in% names(risk) && "BLOCK_ID" %in% names(risk)) risk$PLACE_ID <- risk$BLOCK_ID
    if (!"BLOCK_ID" %in% names(risk) && "PLACE_ID" %in% names(risk)) risk$BLOCK_ID <- risk$PLACE_ID

    required_core <- c("PLACE_ID", "BLOCK_ID", "tstart_yr", "tstop_yr")
    missing_core <- setdiff(required_core, names(risk))
    if (length(missing_core) > 0L) stop("Missing core fields: ", paste(missing_core, collapse = ", "))

    risk$PLACE_ID <- clean_key(risk$PLACE_ID)
    risk$BLOCK_ID <- clean_key(risk$BLOCK_ID)
    risk$tstart_yr <- num(risk$tstart_yr)
    risk$tstop_yr <- num(risk$tstop_yr)
    if (!"y1" %in% names(risk)) risk$y1 <- risk$tstart_yr
    if (!"y2" %in% names(risk)) risk$y2 <- risk$tstop_yr
    if (!"STATE1_ONTOLOGY" %in% names(risk)) risk$STATE1_ONTOLOGY <- NA_character_
    if (!"STATE2_ONTOLOGY" %in% names(risk)) risk$STATE2_ONTOLOGY <- NA_character_

    # Use primary ambiguity-bridged fields when present, matching v17.8d.
    # Storage reworking receives additional QA below because some Risk Tables can
    # contain an empty PRIMARY risk field while the legacy/shared storage-origin
    # risk set remains populated.
    #
    # Broad eligible-floodplain prediction is optional in the integrated script.
    # The strict SF -> AD process model remains mandatory; the broad model is added
    # only when enabled AND its Step 3 v6.7+ fields are present.
    broad_candidates_evt <- c("FP_REACTIVATE_EVT_PRIMARY", "FP_REACTIVATE_EVT")
    broad_candidates_risk <- c("FP_REACTIVATE_RISK_SET_PRIMARY", "FP_REACTIVATE_RISK_SET")
    broad_eligibility_field <- "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY"
    broad_available <- any(broad_candidates_evt %in% names(risk)) &&
      any(broad_candidates_risk %in% names(risk)) &&
      broad_eligibility_field %in% names(risk)
    run_broad_prediction <- isTRUE(RunBroadFloodplainPrediction) && broad_available
    if (isTRUE(RunBroadFloodplainPrediction) && !broad_available) {
      missing_broad <- c(
        if (!any(broad_candidates_evt %in% names(risk))) paste0("event: ", paste(broad_candidates_evt, collapse = " / ")) else character(0),
        if (!any(broad_candidates_risk %in% names(risk))) paste0("risk: ", paste(broad_candidates_risk, collapse = " / ")) else character(0),
        if (!broad_eligibility_field %in% names(risk)) paste0("eligibility: ", broad_eligibility_field) else character(0)
      )
      stop("[Broad FP QA] Broad floodplain prediction was requested but authoritative fields are unavailable: ",
           paste(missing_broad, collapse = "; "),
           ". Use the current Stage 4 Step 3 Risk Table or set RunBroadFloodplainPrediction=FALSE explicitly.")
    }

    field_map <- list(
      REACTIVATE_EVT_MODEL = c("REACTIVATE_EVT_PRIMARY", "REACTIVATE_EVT"),
      STORAGE_EVT_MODEL = c("STORAGE_EVT_PRIMARY", "STORAGE_EVT"),
      STABILISE_EVT_MODEL = c("STABILISE_EVT_PRIMARY", "STABILISE_EVT"),
      REACTIVATE_RISK_MODEL = c("REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET"),
      STORAGE_RISK_MODEL = c("STORAGE_RISK_SET_PRIMARY", "STORAGE_RISK_SET"),
      STABILISE_RISK_MODEL = c("STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET")
    )
    for (out_nm in names(field_map)) {
      src_nm <- first_existing(risk, field_map[[out_nm]], required = TRUE)
      risk[[out_nm]] <- int01(risk[[src_nm]])
    }
    if (run_broad_prediction) {
      broad_eligible <- int01(risk[[broad_eligibility_field]])
      broad_evt_raw <- int01(risk[[first_existing(risk, broad_candidates_evt, required = TRUE)]])
      broad_risk_raw <- int01(risk[[first_existing(risk, broad_candidates_risk, required = TRUE)]])
      # Authoritative model population = broad risk AND dedicated broad eligibility.
      risk$FP_REACTIVATE_RISK_MODEL <- as.integer(broad_risk_raw == 1L & broad_eligible == 1L)
      risk$FP_REACTIVATE_EVT_MODEL <- as.integer(broad_evt_raw == 1L & broad_eligible == 1L)
      n_broad_ineligible_risk <- sum(broad_risk_raw == 1L & broad_eligible != 1L, na.rm = TRUE)
      n_broad_ineligible_evt <- sum(broad_evt_raw == 1L & broad_eligible != 1L, na.rm = TRUE)
      if (n_broad_ineligible_evt > 0L) {
        stop("[Broad FP QA] ", n_broad_ineligible_evt,
             " broad FP events are outside FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY. ",
             "Inspect Stage 4 Step 3 v6.7.")
      }
      message("[Broad FP QA] dedicated eligibility removed ",
              format(n_broad_ineligible_risk, big.mark = ","),
              " at-risk rows and ", format(n_broad_ineligible_evt, big.mark = ","), " events.")
    } else {
      risk$FP_REACTIVATE_EVT_MODEL <- rep(0L, nrow(risk))
      risk$FP_REACTIVATE_RISK_MODEL <- rep(0L, nrow(risk))
    }

    # Broad eligible-floodplain QA. Every broad event must be inside the broad
    # starting-state risk set. Report how much the risk population expands beyond
    # strict Stabilised Floodplain reactivation.
    n_fp_risk <- sum(risk$FP_REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE)
    n_fp_evt <- sum(risk$FP_REACTIVATE_EVT_MODEL == 1L, na.rm = TRUE)
    n_strict_react_risk <- sum(risk$REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE)
    n_strict_react_evt <- sum(risk$REACTIVATE_EVT_MODEL == 1L, na.rm = TRUE)
    n_fp_evt_outside <- sum(
      risk$FP_REACTIVATE_EVT_MODEL == 1L & risk$FP_REACTIVATE_RISK_MODEL != 1L,
      na.rm = TRUE
    )
    message(
      "[Broad FP QA] broad risk rows/events=", format(n_fp_risk, big.mark = ","), "/",
      format(n_fp_evt, big.mark = ","),
      "; strict SF risk rows/events=", format(n_strict_react_risk, big.mark = ","), "/",
      format(n_strict_react_evt, big.mark = ","),
      "; added risk rows=", format(n_fp_risk - n_strict_react_risk, big.mark = ",")
    )
    if (n_fp_evt_outside > 0L) {
      stop(
        "[Broad FP QA] ", n_fp_evt_outside,
        " FP_REACTIVATE event rows fall outside FP_REACTIVATE_RISK_SET_PRIMARY. ",
        "Inspect Stage 4 Step 3 v6.7 before fitting predictions."
      )
    }
    if (run_broad_prediction && "FP_REACTIVATE_SOURCE_PRIMARY" %in% names(risk)) {
      src_tab <- sort(table(as.character(risk$FP_REACTIVATE_SOURCE_PRIMARY)[risk$FP_REACTIVATE_RISK_MODEL == 1L]), decreasing = TRUE)
      message(
        "[Broad FP QA] source population: ",
        paste(sprintf("%s=%s", names(src_tab), format(as.numeric(src_tab), big.mark = ",")), collapse = "; ")
      )
    }

    # ---------------------------------------------------------------------------
    # Storage-reworking field selection and semantic QA
    # ---------------------------------------------------------------------------
    # [FRAF archive / code note]
    # A risk-set flag must contain actual eligible observations; using an
    # all-zero alias would yield misleading no-event model outputs.
    # [FRAF archive / Prediction function: choose_informative_binary]
    # Select an informative population/event flag and reject unsuitable zero-only aliases.
    choose_informative_binary <- function(dat, candidates, label, required = TRUE) {
      present <- candidates[candidates %in% names(dat)]
      if (length(present) == 0L) {
        if (required) stop("None of the required ", label, " fields exists: ",
                           paste(candidates, collapse = ", "))
        return(list(name = NA_character_, values = integer(nrow(dat)), counts = numeric(0)))
      }

      counts <- vapply(present, function(nm) {
        sum(int01(dat[[nm]]) == 1L, na.rm = TRUE)
      }, numeric(1))

      # Prefer the first candidate (PRIMARY before legacy) that is informative.
      informative <- present[counts > 0]
      chosen <- if (length(informative) > 0L) informative[1] else present[1]

      message("[Storage-rework QA] ", label, " candidates: ",
              paste(sprintf("%s=%s", present, format(counts, big.mark = ",", scientific = FALSE)),
                    collapse = "; "),
              "; selected=", chosen)

      list(name = chosen, values = int01(dat[[chosen]]), counts = counts)
    }

    rw_evt_pick <- choose_informative_binary(
      risk,
      c("STORAGE_REWORK_EVT_PRIMARY", "STORAGE_REWORK_EVT"),
      "event"
    )
    rw_risk_pick <- choose_informative_binary(
      risk,
      c("STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET"),
      "risk-set"
    )

    risk$STORAGE_REWORK_EVT_MODEL <- rw_evt_pick$values
    risk$STORAGE_REWORK_RISK_MODEL <- rw_risk_pick$values

    n_rw_risk_raw <- sum(risk$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE)
    n_stab_risk <- sum(risk$STABILISE_RISK_MODEL == 1L, na.rm = TRUE)
    n_rw_evt <- sum(risk$STORAGE_REWORK_EVT_MODEL == 1L, na.rm = TRUE)

    # Both competing transitions start from Depositional Storage. If the dedicated
    # storage-rework risk field is empty but the stabilisation risk set is populated,
    # use the latter as the canonical storage-origin risk population. This preserves
    # process semantics and prevents an empty upstream convenience field from
    # suppressing the reworking model.
    if (n_rw_risk_raw == 0L && n_stab_risk > 0L) {
      warning(
        "[Storage-rework QA] Dedicated STORAGE_REWORK risk set contains zero eligible rows. ",
        "Using STABILISE_RISK_MODEL as the canonical Depositional-Storage starting-state ",
        "risk set for Depositional Storage -> Active Domain."
      )
      risk$STORAGE_REWORK_RISK_MODEL <- risk$STABILISE_RISK_MODEL
    }

    n_rw_risk_final <- sum(risk$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE)
    n_rw_evt_outside <- sum(
      risk$STORAGE_REWORK_EVT_MODEL == 1L &
        risk$STORAGE_REWORK_RISK_MODEL != 1L,
      na.rm = TRUE
    )

    message(
      "[Storage-rework QA] final risk rows=", format(n_rw_risk_final, big.mark = ",", scientific = FALSE),
      "; events=", format(n_rw_evt, big.mark = ",", scientific = FALSE),
      "; stabilisation-origin risk rows=", format(n_stab_risk, big.mark = ",", scientific = FALSE),
      "; events outside final risk set=", format(n_rw_evt_outside, big.mark = ",", scientific = FALSE)
    )

    if (n_rw_evt_outside > 0L) {
      stop(
        "[Storage-rework QA] ", n_rw_evt_outside,
        " storage-reworking event rows fall outside the final Depositional-Storage risk set. ",
        "Inspect Stage 4 Step 3 before fitting predictions."
      )
    }

    risk <- risk %>%
      filter(
        !is.na(PLACE_ID), !is.na(BLOCK_ID),
        is.finite(tstart_yr), is.finite(tstop_yr),
        tstop_yr > tstart_yr
      )

    # Duplicate interval rows would invalidate rolling prediction and exposure time.
    key_qa <- risk %>% count(PLACE_ID, tstart_yr, tstop_yr, name = "n") %>% filter(n > 1L)
    if (nrow(key_qa) > 0L) {
      write_csv(key_qa, file.path(out_dir, "20_prediction_duplicate_interval_rows.csv"))
      stop("Duplicate PLACE_ID/tstart/tstop rows found. See 20_prediction_duplicate_interval_rows.csv")
    }

    # Convert candidate raw fields to numeric without requiring all to exist.
    numeric_candidates <- unique(c(
      "ASM_BLOCK_AREA_M2",
      "ASM_DOM_RATIO_PREV", "ASM_N_EPISODES_PREV", "ASM_MAX_QUIET_PREV", "ASM_COV_FRAC",
      "ASM_N_REACTIVATE_PREV", "ASM_STORAGE_FRAC_PREV", "ASM_N_STORAGE_EVT_PREV",
      "ASM_STAB_FP_FRAC_PREV", "ASM_QUIET_SINCE_PREV", "ASM_N_STABILISE_PREV",
      "DIST_ACTIVE_CURR", "DIST_CL_REF", "DIST_CL_CURR", "DIST_WATER_CURR",
      "GEOM_SUPPORT_PREV", "DIST_CHANNEL_PREV", "INSIDE_CHANNEL_PREV", "REL_CHANNEL_POS_PREV",
      "NEAR_CHANNEL_HALF_PREV", "NEAR_CHANNEL_FULL_PREV",
      "NEAR_BANK_HALF_PREV", "NEAR_BANK_FULL_PREV",
      "OUTER_CURV_REACT_HALF_PREV", "OUTER_CURV_REACT_FULL_PREV",
      "INNER_CURV_STORAGE_HALF_PREV", "INNER_CURV_STORAGE_FULL_PREV",
      "OUTER_CURV_STORAGE_HALF_PREV", "OUTER_CURV_STORAGE_FULL_PREV",
      "OUTER_BANK_PREV", "INNER_BANK_PREV",
      "MAM_NEAR_CHANNEL_PREV", "MAM_OUTER_REACT_EXPOSED_PREV", "MAM_OUTER_CURV_REACT_PREV",
      "MAM_NEAR_BANK_STORAGE_PREV", "MAM_INNER_STORAGE_EXPOSED_PREV", "MAM_INNER_CURV_STORAGE_PREV",
      "MAM_OUTER_STORAGE_EXPOSED_PREV", "MAM_OUTER_CURV_STORAGE_PREV"
    ))
    for (nm in intersect(numeric_candidates, names(risk))) risk[[nm]] <- num(risk[[nm]])

    # [FRAF archive / Prediction function: binary_from]
    # Convert an observed risk/event field to a consistent binary target.
    binary_from <- function(x) {
      y <- int01(x)
      y[!is.finite(num(x))] <- 0L
      y
    }

    # Recreate v17.8d canonical Mamoré fields when the Risk Table contains the raw
    # local-geometry fields but not the already-canonical aliases.
    react_near_source <- if (identical(react_exposure, "Half-width channel-margin zone")) {
      "NEAR_CHANNEL_HALF_PREV"
    } else {
      "NEAR_CHANNEL_FULL_PREV"
    }
    react_curv_source <- if (identical(react_exposure, "Half-width channel-margin zone")) {
      "OUTER_CURV_REACT_HALF_PREV"
    } else {
      "OUTER_CURV_REACT_FULL_PREV"
    }
    storage_near_source <- if (identical(storage_exposure, "Full-width bank-adjacent zone")) {
      "NEAR_BANK_FULL_PREV"
    } else {
      "NEAR_BANK_HALF_PREV"
    }
    inner_storage_source <- if (identical(storage_exposure, "Full-width bank-adjacent zone")) {
      "INNER_CURV_STORAGE_FULL_PREV"
    } else {
      "INNER_CURV_STORAGE_HALF_PREV"
    }
    outer_storage_source <- if (identical(storage_exposure, "Full-width bank-adjacent zone")) {
      "OUTER_CURV_STORAGE_FULL_PREV"
    } else {
      "OUTER_CURV_STORAGE_HALF_PREV"
    }

    if (!"MAM_NEAR_CHANNEL_PREV" %in% names(risk) && react_near_source %in% names(risk)) {
      risk$MAM_NEAR_CHANNEL_PREV <- binary_from(risk[[react_near_source]])
    }
    if (!"MAM_OUTER_CURV_REACT_PREV" %in% names(risk) && react_curv_source %in% names(risk)) {
      risk$MAM_OUTER_CURV_REACT_PREV <- num(risk[[react_curv_source]])
    }
    if (!"MAM_OUTER_REACT_EXPOSED_PREV" %in% names(risk)) {
      if (all(c("MAM_NEAR_CHANNEL_PREV", "OUTER_BANK_PREV") %in% names(risk))) {
        risk$MAM_OUTER_REACT_EXPOSED_PREV <- int01(risk$MAM_NEAR_CHANNEL_PREV == 1 & num(risk$OUTER_BANK_PREV) == 1)
      } else if ("MAM_OUTER_CURV_REACT_PREV" %in% names(risk)) {
        risk$MAM_OUTER_REACT_EXPOSED_PREV <- int01(is.finite(risk$MAM_OUTER_CURV_REACT_PREV) & abs(risk$MAM_OUTER_CURV_REACT_PREV) > 0)
      }
    }
    if (!"MAM_NEAR_BANK_STORAGE_PREV" %in% names(risk) && storage_near_source %in% names(risk)) {
      risk$MAM_NEAR_BANK_STORAGE_PREV <- binary_from(risk[[storage_near_source]])
    }
    if (!"MAM_INNER_CURV_STORAGE_PREV" %in% names(risk) && inner_storage_source %in% names(risk)) {
      risk$MAM_INNER_CURV_STORAGE_PREV <- num(risk[[inner_storage_source]])
    }
    if (!"MAM_OUTER_CURV_STORAGE_PREV" %in% names(risk) && outer_storage_source %in% names(risk)) {
      risk$MAM_OUTER_CURV_STORAGE_PREV <- num(risk[[outer_storage_source]])
    }
    if (!"MAM_INNER_STORAGE_EXPOSED_PREV" %in% names(risk)) {
      if (all(c("MAM_NEAR_BANK_STORAGE_PREV", "INNER_BANK_PREV") %in% names(risk))) {
        risk$MAM_INNER_STORAGE_EXPOSED_PREV <- int01(risk$MAM_NEAR_BANK_STORAGE_PREV == 1 & num(risk$INNER_BANK_PREV) == 1)
      } else if ("MAM_INNER_CURV_STORAGE_PREV" %in% names(risk)) {
        risk$MAM_INNER_STORAGE_EXPOSED_PREV <- int01(is.finite(risk$MAM_INNER_CURV_STORAGE_PREV) & abs(risk$MAM_INNER_CURV_STORAGE_PREV) > 0)
      }
    }
    if (!"MAM_OUTER_STORAGE_EXPOSED_PREV" %in% names(risk)) {
      if (all(c("MAM_NEAR_BANK_STORAGE_PREV", "OUTER_BANK_PREV") %in% names(risk))) {
        risk$MAM_OUTER_STORAGE_EXPOSED_PREV <- int01(risk$MAM_NEAR_BANK_STORAGE_PREV == 1 & num(risk$OUTER_BANK_PREV) == 1)
      } else if ("MAM_OUTER_CURV_STORAGE_PREV" %in% names(risk)) {
        risk$MAM_OUTER_STORAGE_EXPOSED_PREV <- int01(is.finite(risk$MAM_OUTER_CURV_STORAGE_PREV) & abs(risk$MAM_OUTER_CURV_STORAGE_PREV) > 0)
      }
    }

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Transition recipes: candidate spatial/history terms and risk populations
    # depend on source state, river and observed training support.
    # [FRAF archive / code note]
    # Spatial recipes are intentionally river- and transition-specific;
    # their coefficient estimates are not assumed transferable across reaches.
    # 2. Predictor recipes and transition specifications
    # -----------------------------------------------------------------------------

    # A recipe maps the v17.8d model term to its unscaled Risk Table source.
    recipe <- list(
      ASM_DOM_RATIO_PREV_Z = list(source = "ASM_DOM_RATIO_PREV", transform = "z"),
      ASM_N_EPISODES_PREV_Z = list(source = "ASM_N_EPISODES_PREV", transform = "z"),
      ASM_MAX_QUIET_PREV_Z = list(source = "ASM_MAX_QUIET_PREV", transform = "z"),
      ASM_COV_FRAC_Z = list(source = "ASM_COV_FRAC", transform = "z"),
      ASM_N_REACTIVATE_PREV_Z = list(source = "ASM_N_REACTIVATE_PREV", transform = "z"),
      ASM_STORAGE_FRAC_PREV_Z = list(source = "ASM_STORAGE_FRAC_PREV", transform = "z"),
      ASM_N_STORAGE_EVT_PREV_Z = list(source = "ASM_N_STORAGE_EVT_PREV", transform = "z"),
      ASM_STAB_FP_FRAC_PREV_Z = list(source = "ASM_STAB_FP_FRAC_PREV", transform = "z"),
      ASM_QUIET_SINCE_PREV_Z = list(source = "ASM_QUIET_SINCE_PREV", transform = "z"),
      ASM_N_STABILISE_PREV_Z = list(source = "ASM_N_STABILISE_PREV", transform = "z"),
      DIST_ACTIVE_CURR_LOGKM_Z = list(source = "DIST_ACTIVE_CURR", transform = "logkm_z"),
      DIST_ACTIVE_CURR_LINEAR_Z = list(source = "DIST_ACTIVE_CURR", transform = "z"),
      DIST_CHANNEL_PREV_LINEAR_Z = list(source = "DIST_CHANNEL_PREV", transform = "z"),
      DIST_CL_REF_LOGKM_Z = list(source = "DIST_CL_REF", transform = "logkm_z"),
      DIST_CL_CURR_LOGKM_Z = list(source = "DIST_CL_CURR", transform = "logkm_z"),
      DIST_WATER_CURR_LOGKM_Z = list(source = "DIST_WATER_CURR", transform = "logkm_z"),
      DIST_CHANNEL_PREV_LOGKM_Z = list(source = "DIST_CHANNEL_PREV", transform = "logkm_z"),
      REL_CHANNEL_POS_PREV_Z = list(source = "REL_CHANNEL_POS_PREV", transform = "z"),
      MAM_OUTER_CURV_REACT_PREV_Z = list(source = "MAM_OUTER_CURV_REACT_PREV", transform = "z"),
      MAM_INNER_CURV_STORAGE_PREV_Z = list(source = "MAM_INNER_CURV_STORAGE_PREV", transform = "z"),
      MAM_OUTER_CURV_STORAGE_PREV_Z = list(source = "MAM_OUTER_CURV_STORAGE_PREV", transform = "z"),
      MAM_NEAR_CHANNEL_PREV = list(source = "MAM_NEAR_CHANNEL_PREV", transform = "binary"),
      MAM_OUTER_REACT_EXPOSED_PREV = list(source = "MAM_OUTER_REACT_EXPOSED_PREV", transform = "binary"),
      MAM_NEAR_BANK_STORAGE_PREV = list(source = "MAM_NEAR_BANK_STORAGE_PREV", transform = "binary"),
      MAM_INNER_STORAGE_EXPOSED_PREV = list(source = "MAM_INNER_STORAGE_EXPOSED_PREV", transform = "binary"),
      MAM_OUTER_STORAGE_EXPOSED_PREV = list(source = "MAM_OUTER_STORAGE_EXPOSED_PREV", transform = "binary")
    )

    history_core <- c(
      "ASM_DOM_RATIO_PREV_Z",
      "ASM_N_EPISODES_PREV_Z",
      "ASM_MAX_QUIET_PREV_Z",
      "ASM_COV_FRAC_Z"
    )
    # Final Jamuna SF->AD / DS->AD history set from J3D. Broad FP->AD and
    # all unaffected models retain the baseline history_core.
    history_core_no_episodes <- setdiff(history_core, "ASM_N_EPISODES_PREV_Z")

    # v17.10.15.1: final Step-3D Mamore DS->AD reduced-history set. This is
    # deliberately identical to the Historic-mode Mamore DS->AD history set.
    mamore_storage_rework_history_core <- c(
      "ASM_DOM_RATIO_PREV_Z",
      "ASM_COV_FRAC_Z"
    )

    required_local_geom <- c(
      "GEOM_SUPPORT_PREV", "DIST_CHANNEL_PREV", "INSIDE_CHANNEL_PREV",
      "MAM_NEAR_CHANNEL_PREV", "MAM_OUTER_CURV_REACT_PREV",
      "REL_CHANNEL_POS_PREV", "MAM_INNER_CURV_STORAGE_PREV"
    )
    has_local_geom <- !identical(reach_label, "Jamuna") &&
      all(required_local_geom %in% names(risk)) &&
      any(num(risk$GEOM_SUPPORT_PREV) == 1, na.rm = TRUE)

    # [FRAF archive / code note]
    # Fallback terms are compatibility options, not post-hoc evidence that
    # a missing primary spatial measurement was observed.
    # [FRAF archive / Prediction function: fallback_distance_term]
    # Resolve a compatible spatial distance predictor without inventing an unavailable covariate.
    fallback_distance_term <- function(dat) {
      candidates <- c(
        "DIST_ACTIVE_CURR_LOGKM_Z",
        "DIST_CL_REF_LOGKM_Z",
        "DIST_CL_CURR_LOGKM_Z",
        "DIST_WATER_CURR_LOGKM_Z"
      )
      for (tm in candidates) {
        rc <- recipe[[tm]]
        if (!is.null(rc) && rc$source %in% names(dat)) {
          x <- num(dat[[rc$source]])
          if (sum(is.finite(x)) > 1L && stats::sd(x[is.finite(x)]) > 0) return(tm)
        }
      }
      character(0)
    }

    if (has_local_geom) {
      # Mamore SF->AD and Expanded FP->AD retain the validated v17.10.13
      # local-geometry prediction recipe. Only DS->AD is changed in v17.10.14.2.
      react_spatial <- c("MAM_NEAR_CHANNEL_PREV", "MAM_OUTER_REACT_EXPOSED_PREV", "MAM_OUTER_CURV_REACT_PREV_Z")
      react_broad_spatial <- if ("DIST_ACTIVE_CURR" %in% names(risk) &&
        sum(is.finite(num(risk$DIST_ACTIVE_CURR))) > 1L &&
        stats::sd(num(risk$DIST_ACTIVE_CURR)[is.finite(num(risk$DIST_ACTIVE_CURR))]) > 0) {
        "DIST_ACTIVE_CURR_LOGKM_Z"
      } else {
        react_spatial
      }
      storage_full_spatial <- character(0)
      storage_local_spatial <- c(
        "REL_CHANNEL_POS_PREV_Z", "MAM_NEAR_BANK_STORAGE_PREV",
        "MAM_INNER_STORAGE_EXPOSED_PREV", "MAM_INNER_CURV_STORAGE_PREV_Z",
        "MAM_OUTER_STORAGE_EXPOSED_PREV", "MAM_OUTER_CURV_STORAGE_PREV_Z"
      )
      stabilise_spatial <- "DIST_CHANNEL_PREV_LOGKM_Z"
      # v17.10.15.1: ordinary Mamore DS->AD is organised by linear distance
      # from the previous channel margin. Curvature is optionally promoted by the
      # shared Historic/Prediction selector only after Step-3D triage.
      storage_rework_spatial <- c(
        "DIST_CHANNEL_PREV_LINEAR_Z",
        if (isTRUE(mamore_dsad_use_curvature)) "MAM_OUTER_CURV_REACT_PREV_Z" else character(0)
      )
      spatial_frameworks <- c(
        react = "lagged_local_outer_bank_reactivation",
        react_broad = "lagged_local_outer_bank_broad_floodplain_reactivation",
        storage_full = "full_event_assemblage_history_storage",
        storage_local = "lagged_within_channel_position_subset",
        stabilise = "lagged_channel_margin_stabilisation",
        storage_rework = ifelse(
          isTRUE(mamore_dsad_use_curvature),
          "linear_previous_channel_margin_plus_curvature_storage_reworking",
          "linear_previous_channel_margin_storage_reworking"
        )
      )
    } else {
      fb <- fallback_distance_term(risk)
      # FINAL STEP-3 SPECIFICATION for Jamuna SF->AD and DS->AD: linear
      # active-domain-margin distance. Expanded FP->AD deliberately retains the
      # v17.10.13 broad predictive recipe (normally log active-margin distance).
      jamuna_linear_active <- if ("DIST_ACTIVE_CURR" %in% names(risk) &&
        sum(is.finite(num(risk$DIST_ACTIVE_CURR))) > 1L &&
        stats::sd(num(risk$DIST_ACTIVE_CURR)[is.finite(num(risk$DIST_ACTIVE_CURR))]) > 0) {
        "DIST_ACTIVE_CURR_LINEAR_Z"
      } else {
        fb
      }
      react_spatial <- jamuna_linear_active
      react_broad_spatial <- fb
      storage_full_spatial <- fb
      storage_local_spatial <- character(0)
      stabilise_spatial <- fb
      storage_rework_spatial <- jamuna_linear_active
      spatial_frameworks <- c(
        react = ifelse(identical(jamuna_linear_active, "DIST_ACTIVE_CURR_LINEAR_Z"), "linear_active_domain_margin", ifelse(length(fb), sub("_LOGKM_Z$", "", fb), "no_spatial_predictor")),
        react_broad = ifelse(length(fb), paste0(sub("_LOGKM_Z$", "", fb), "_broad_floodplain_baseline"), "no_spatial_predictor"),
        storage_full = ifelse(length(fb), sub("_LOGKM_Z$", "", fb), "no_spatial_predictor"),
        storage_local = "not_applicable_non_mamore",
        stabilise = ifelse(length(fb), sub("_LOGKM_Z$", "", fb), "no_spatial_predictor"),
        storage_rework = ifelse(identical(jamuna_linear_active, "DIST_ACTIVE_CURR_LINEAR_Z"), "linear_active_domain_margin_storage_reworking", ifelse(length(fb), sub("_LOGKM_Z$", "", fb), "no_spatial_predictor"))
      )
    }

    transition_specs <- list(
      list(
        model = "active_domain_reactivation",
        transition = "Stabilised Floodplain -> Active Domain",
        scope = "full_risk_set",
        risk_field = "REACTIVATE_RISK_MODEL",
        event_field = "REACTIVATE_EVT_MODEL",
        candidates = unique(c(react_spatial, if (identical(reach_label, "Jamuna")) history_core_no_episodes else history_core)),
        framework = spatial_frameworks[["react"]],
        local_only = FALSE
      ),
      list(
        model = "floodplain_reactivation_broad",
        transition = "Eligible Floodplain -> Active Domain",
        scope = "broad_floodplain_risk_set",
        risk_field = "FP_REACTIVATE_RISK_MODEL",
        event_field = "FP_REACTIVATE_EVT_MODEL",
        candidates = unique(react_broad_spatial),
        framework = spatial_frameworks[["react_broad"]],
        local_only = FALSE
      ),
      list(
        model = "depositional_storage_full_event",
        transition = "Active Domain -> Depositional Storage",
        scope = "full_event",
        risk_field = "STORAGE_RISK_MODEL",
        event_field = "STORAGE_EVT_MODEL",
        candidates = unique(c(storage_full_spatial, history_core, "ASM_STORAGE_FRAC_PREV_Z", "ASM_N_STORAGE_EVT_PREV_Z")),
        framework = spatial_frameworks[["storage_full"]],
        local_only = FALSE
      ),
      list(
        model = "floodplain_stabilisation",
        transition = "Depositional Storage -> Stabilised Floodplain",
        scope = "full_risk_set",
        risk_field = "STABILISE_RISK_MODEL",
        event_field = "STABILISE_EVT_MODEL",
        candidates = unique(c(
          stabilise_spatial, history_core, "ASM_STORAGE_FRAC_PREV_Z",
          "ASM_STAB_FP_FRAC_PREV_Z", "ASM_QUIET_SINCE_PREV_Z", "ASM_N_STABILISE_PREV_Z"
        )),
        framework = spatial_frameworks[["stabilise"]],
        local_only = FALSE
      ),
      list(
        model = "depositional_storage_reworking",
        transition = "Depositional Storage -> Active Domain",
        scope = "full_risk_set",
        risk_field = "STORAGE_REWORK_RISK_MODEL",
        event_field = "STORAGE_REWORK_EVT_MODEL",
        candidates = unique(c(
          storage_rework_spatial,
          if (identical(reach_label, "Jamuna")) history_core_no_episodes else mamore_storage_rework_history_core,
          "ASM_STORAGE_FRAC_PREV_Z",
          "ASM_QUIET_SINCE_PREV_Z",
          "ASM_N_STORAGE_EVT_PREV_Z"
        )),
        framework = spatial_frameworks[["storage_rework"]],
        local_only = FALSE
      )
    )
    # v17.10.14.2 frozen-specification QA: write the exact production candidate
    # recipes before rolling-origin fitting so provenance is explicit.
    spec_qa <- do.call(rbind, lapply(transition_specs, function(sp) {
      data.frame(
        reach = reach_label, model = sp$model, transition = sp$transition,
        model_scope = sp$scope, spatial_framework = unname(sp$framework),
        candidate_terms = paste(sp$candidates, collapse = " | "),
        stringsAsFactors = FALSE
      )
    }))
    utils::write.csv(spec_qa, file.path(out_dir, "20a_v17_10_15_1_frozen_prediction_specifications.csv"), row.names = FALSE)

    # Remove optional broad prediction spec when disabled or unsupported.
    if (!run_broad_prediction) {
      transition_specs <- Filter(function(s) !identical(s$model, "floodplain_reactivation_broad"), transition_specs)
    }

    if (has_local_geom) {
      transition_specs <- append(transition_specs, list(list(
        model = "depositional_storage_local_position_subset",
        transition = "Active Domain -> Depositional Storage",
        scope = "local_geometry_subset",
        risk_field = "STORAGE_RISK_MODEL",
        event_field = "STORAGE_EVT_MODEL",
        candidates = unique(c(storage_local_spatial, history_core, "ASM_STORAGE_FRAC_PREV_Z", "ASM_N_STORAGE_EVT_PREV_Z")),
        framework = spatial_frameworks[["storage_local"]],
        local_only = TRUE
      )), after = 3L)
    }

    # Keep only terms whose raw source exists. Variation and missingness are handled
    # separately within each training window.
    for (i in seq_along(transition_specs)) {
      transition_specs[[i]]$candidates <- transition_specs[[i]]$candidates[
        vapply(transition_specs[[i]]$candidates, function(tm) {
          !is.null(recipe[[tm]]) && recipe[[tm]]$source %in% names(risk)
        }, logical(1))
      ]
    }

    spec_table <- bind_rows(lapply(transition_specs, function(s) {
      tibble::tibble(
        reach = reach_label,
        model = s$model,
        transition = s$transition,
        model_scope = s$scope,
        spatial_framework = s$framework,
        candidate_terms = paste(s$candidates, collapse = "; "),
        local_geometry_required = s$local_only
      )
    }))
    write_csv(spec_table, file.path(out_dir, "20_model_specifications.csv"))

    # Retain only the columns needed by the prediction models. This is important for
    # the multi-million-row Jamuna Risk Table and preserves the memory-safe intent of
    # v17.8d.
    #
    # v17.9.7: risk/event fields are derived dynamically from transition_specs rather
    # than maintained as a hard-coded list. This prevents a newly added transition
    # (e.g. Depositional Storage -> Active Domain) from having its model fields
    # accidentally discarded before rolling-origin fitting.
    all_model_terms <- unique(unlist(lapply(transition_specs, function(s) s$candidates)))
    all_model_sources <- unique(vapply(all_model_terms, function(tm) recipe[[tm]]$source, character(1)))
    all_spec_risk_event_fields <- unique(unlist(lapply(
      transition_specs,
      function(s) c(s$risk_field, s$event_field)
    )))

    compact_fields <- unique(c(
      "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
      "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "ASM_BLOCK_AREA_M2",
      all_spec_risk_event_fields,
      "GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV",
      all_model_sources
    ))

    missing_compact_model_fields <- setdiff(all_spec_risk_event_fields, names(risk))
    if (length(missing_compact_model_fields) > 0L) {
      stop(
        "[Compact-field QA] Required transition risk/event field(s) missing before ",
        "memory reduction: ", paste(missing_compact_model_fields, collapse = ", ")
      )
    }

    risk <- risk[, intersect(compact_fields, names(risk)), drop = FALSE]

    missing_after_compact <- setdiff(all_spec_risk_event_fields, names(risk))
    if (length(missing_after_compact) > 0L) {
      stop(
        "[Compact-field QA] Transition risk/event field(s) were lost during memory ",
        "reduction: ", paste(missing_after_compact, collapse = ", ")
      )
    }

    message(
      "[Compact-field QA] retained transition fields: ",
      paste(all_spec_risk_event_fields, collapse = ", ")
    )

    gc(verbose = FALSE)

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Leakage boundary: learn every centring/scaling step on the training window;
    # freeze it when scoring held-out and genuine future intervals.
    # [FRAF archive / code note]
    # Keep all transformations of prospective scoring data frozen to training
    # parameters; this is essential for an unbiased held-out comparison.
    # 3. Train-only transformations and robust Cox fitting
    # -----------------------------------------------------------------------------

    # [FRAF archive / Prediction function: raw_transform]
    # Apply the frozen raw-scale or nonlinear transformation specified in a model recipe.
    raw_transform <- function(x, type) {
      x <- num(x)
      if (identical(type, "logkm_z")) {
        x[x < 0] <- NA_real_
        return(log1p(x / 1000))
      }
      if (identical(type, "binary")) return(as.numeric(int01(x)))
      x
    }

    # [FRAF archive / Prediction function: build_transformed]
    # Apply train-derived transforms to both training and held-out/future frames without leakage.
    build_transformed <- function(train, target, terms, model_name, forecast_label) {
      tr <- train
      tg <- target
      scaler_rows <- list()

      for (tm in terms) {
        rc <- recipe[[tm]]
        source <- rc$source
        type <- rc$transform
        x_train <- raw_transform(tr[[source]], type)
        x_target <- raw_transform(tg[[source]], type)

        if (type %in% c("z", "logkm_z")) {
          ok <- is.finite(x_train)
          centre <- if (any(ok)) mean(x_train[ok]) else NA_real_
          scale <- if (sum(ok) > 1L) stats::sd(x_train[ok]) else NA_real_
          if (!is.finite(scale) || scale <= 0) scale <- NA_real_
          # v17.10.14.2: zero-row-safe assignment. In FINAL_FULL_RECORD fit-only
          # mode tg deliberately has zero rows. A scalar NA assignment to a
          # zero-row data.frame raises: "replacement has 1 row, data has 0".
          # Always return vectors whose lengths match their respective frames.
          tr[[tm]] <- if (is.finite(scale)) {
            (x_train - centre) / scale
          } else {
            rep(NA_real_, nrow(tr))
          }
          tg[[tm]] <- if (is.finite(scale)) {
            (x_target - centre) / scale
          } else {
            rep(NA_real_, nrow(tg))
          }
        } else {
          centre <- 0
          scale <- 1
          tr[[tm]] <- x_train
          tg[[tm]] <- x_target
        }

        scaler_rows[[length(scaler_rows) + 1L]] <- tibble::tibble(
          reach = reach_label,
          model = model_name,
          forecast_label = forecast_label,
          term = tm,
          source_field = source,
          transform = type,
          centre = centre,
          scale = scale
        )
      }
      list(train = tr, target = tg, scalers = bind_rows(scaler_rows))
    }

    # [FRAF archive / Prediction function: varying_terms]
    # Discard constant or otherwise non-informative candidate model terms in training.
    varying_terms <- function(dat, terms) {
      keep <- character(0)
      for (tm in terms) {
        if (!tm %in% names(dat)) next
        x <- num(dat[[tm]])
        x <- x[is.finite(x)]
        if (length(x) > 1L && is.finite(stats::sd(x)) && stats::sd(x) > 0) keep <- c(keep, tm)
      }
      unique(keep)
    }

    # [FRAF archive / Prediction function: iterative_complete_case]
    # Rebuild a complete-case training set and adjust terms when sparse events/missingness prevent
    # fitting.
    iterative_complete_case <- function(dat, terms, event_field, min_events) {
      current <- varying_terms(dat, terms)
      drop_log <- list()

      repeat {
        if (length(current) == 0L) {
          cc <- rep(TRUE, nrow(dat))
        } else {
          cc <- stats::complete.cases(dat[, current, drop = FALSE])
        }
        n_evt <- sum(dat[[event_field]][cc] == 1L, na.rm = TRUE)
        n_rows <- sum(cc)
        if (n_rows > 0L && n_evt >= min_events) break
        if (length(current) == 0L) break

        event_rows <- dat[[event_field]] == 1L
        losses <- vapply(current, function(tm) {
          sum(event_rows & !is.finite(num(dat[[tm]])), na.rm = TRUE)
        }, numeric(1))
        missing_rows <- vapply(current, function(tm) {
          sum(!is.finite(num(dat[[tm]])), na.rm = TRUE)
        }, numeric(1))
        ord <- order(losses, missing_rows, decreasing = TRUE)
        drop_tm <- current[ord[1]]
        drop_log[[length(drop_log) + 1L]] <- tibble::tibble(
          dropped_term = drop_tm,
          event_rows_missing = losses[drop_tm],
          all_rows_missing = missing_rows[drop_tm],
          reason = "insufficient complete-case training events"
        )
        current <- setdiff(current, drop_tm)
      }

      cc <- if (length(current) == 0L) rep(TRUE, nrow(dat)) else stats::complete.cases(dat[, current, drop = FALSE])
      list(
        terms = current,
        data = dat[cc, , drop = FALSE],
        complete = cc,
        drop_log = bind_rows(drop_log)
      )
    }

    # [FRAF archive / code note]
    # Fit duration-time models for next-interval absolute risk; this differs
    # from the total-time interpretive historic Cox estimand.
    # [FRAF archive / Prediction function: fit_cox_model]
    # Fit a transition-specific duration-time Cox model, recording terms, scalers and baseline
    # hazard.
    fit_cox_model <- function(train, target = NULL, spec, forecast_label, fit_only = FALSE) {
      # Hard schema QA before narrowing. This gives an informative error rather than
      # silently creating zero-length vectors downstream.
      missing_spec_fields <- setdiff(c(spec$risk_field, spec$event_field), names(train))
      missing_target_fields <- if (isTRUE(fit_only)) {
        character(0)
      } else if (is.null(target)) {
        c(spec$risk_field, spec$event_field)
      } else {
        setdiff(c(spec$risk_field, spec$event_field), names(target))
      }
      if (length(missing_spec_fields) > 0L || length(missing_target_fields) > 0L) {
        stop(
          "[Model schema QA] ", spec$model, " is missing required risk/event field(s). ",
          "Training missing: ", paste(missing_spec_fields, collapse = ", "),
          "; target missing: ", paste(missing_target_fields, collapse = ", ")
        )
      }

      # Work with a narrow model frame rather than copying every Risk Table field.
      raw_sources <- unique(vapply(spec$candidates, function(tm) recipe[[tm]]$source, character(1)))
      model_fields <- unique(c(
        "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
        "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "ASM_BLOCK_AREA_M2",
        spec$risk_field, spec$event_field, "GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV",
        raw_sources
      ))
      train_narrow <- train[, intersect(model_fields, names(train)), drop = FALSE]
      # FINAL_FULL_RECORD fitting does not need a second copy of the million-row
      # Risk Table merely to create prediction statuses. A zero-row target preserves
      # the transformation schema while avoiding that duplicate allocation.
      target_all <- if (isTRUE(fit_only)) {
        train_narrow[0, , drop = FALSE]
      } else {
        target[, intersect(model_fields, names(target)), drop = FALSE]
      }

      # Prediction-specific gap-time scale. Resetting each interval to zero allows
      # the training baseline hazard to be evaluated at a future interval duration
      # without extrapolating the total-time baseline beyond the forecast origin.
      train_narrow$PRED_TSTART <- rep(0, nrow(train_narrow))
      train_narrow$PRED_TSTOP <- num(train_narrow$tstop_yr) - num(train_narrow$tstart_yr)
      # v17.10.12: fit_only deliberately supplies a zero-row target. Assign a
      # zero-length vector, not scalar 0, so data.frame replacement remains valid.
      target_all$PRED_TSTART <- rep(0, nrow(target_all))
      target_all$PRED_TSTOP <- if (nrow(target_all) > 0L) {
        num(target_all$tstop_yr) - num(target_all$tstart_yr)
      } else {
        numeric(0)
      }

      # Apply risk set and local support before estimating scalers.
      train_risk <- train_narrow[train_narrow[[spec$risk_field]] == 1L, , drop = FALSE]
      target_risk <- target_all[[spec$risk_field]] == 1L
      local_supported_target <- rep(TRUE, nrow(target_all))

      if (isTRUE(spec$local_only)) {
        local_train <- num(train_risk$GEOM_SUPPORT_PREV) == 1 & num(train_risk$INSIDE_CHANNEL_PREV) == 1
        local_train[is.na(local_train)] <- FALSE
        train_risk <- train_risk[local_train, , drop = FALSE]
        local_supported_target <- num(target_all$GEOM_SUPPORT_PREV) == 1 & num(target_all$INSIDE_CHANNEL_PREV) == 1
        local_supported_target[is.na(local_supported_target)] <- FALSE
        target_risk <- target_risk & local_supported_target
      }

      status <- rep("not_in_risk_set", nrow(target_all))
      if (isTRUE(spec$local_only)) {
        status[target_all[[spec$risk_field]] == 1L & !local_supported_target] <- "not_modelled_local_geometry"
      }

      if (nrow(train_risk) == 0L || sum(train_risk[[spec$event_field]] == 1L, na.rm = TRUE) < MinimumTrainingEvents) {
        status[target_risk] <- "model_not_fitted_insufficient_events"
        return(list(
          model = NULL, terms = character(0), transformed_target = target_all,
          scalers = tibble::tibble(), coefficients = tibble::tibble(), baseline = tibble::tibble(),
          metadata = tibble::tibble(
            reach = reach_label, model = spec$model, forecast_label = forecast_label,
            transition = spec$transition, model_scope = spec$scope,
            spatial_framework = spec$framework, prediction_time_scale = "interval_gap_time", status = "insufficient training events",
            training_rows = nrow(train_risk), training_events = sum(train_risk[[spec$event_field]] == 1L, na.rm = TRUE),
            training_concordance = NA_real_,
            terms = "",
            warnings = ""
          ),
          target_status = status,
          target_risk = target_risk,
          drop_log = tibble::tibble()
        ))
      }

      transformed <- build_transformed(train_risk, target_all, spec$candidates, spec$model, forecast_label)
      prep <- iterative_complete_case(transformed$train, spec$candidates, spec$event_field, MinimumTrainingEvents)

      if (nrow(prep$data) == 0L || sum(prep$data[[spec$event_field]] == 1L, na.rm = TRUE) < MinimumTrainingEvents) {
        status[target_risk] <- "model_not_fitted_complete_case_events"
        return(list(
          model = NULL, terms = prep$terms, transformed_target = transformed$target,
          scalers = transformed$scalers, coefficients = tibble::tibble(), baseline = tibble::tibble(),
          metadata = tibble::tibble(
            reach = reach_label, model = spec$model, forecast_label = forecast_label,
            transition = spec$transition, model_scope = spec$scope,
            spatial_framework = spec$framework, prediction_time_scale = "interval_gap_time", status = "insufficient complete-case events",
            training_rows = nrow(prep$data), training_events = sum(prep$data[[spec$event_field]] == 1L, na.rm = TRUE),
            training_concordance = NA_real_,
            terms = paste(prep$terms, collapse = "; "),
            warnings = ""
          ),
          target_status = status,
          target_risk = target_risk,
          drop_log = prep$drop_log
        ))
      }

      rhs <- if (length(prep$terms) > 0L) paste(prep$terms, collapse = " + ") else "1"
      form <- stats::as.formula(paste0(
        "survival::Surv(PRED_TSTART, PRED_TSTOP, ", spec$event_field, ") ~ ",
        rhs, " + cluster(PLACE_ID)"
      ))
      # Prevent the fitted model's terms/formula from retaining this function's
      # environment, which contains large training/target data objects.
      environment(form) <- asNamespace("survival")

      fit_warnings <- character(0)
      mod <- tryCatch(
        withCallingHandlers(
          survival::coxph(
            form, data = prep$data, ties = "efron",
            # x is needed transiently by basehaz()/survfit.coxph; model=FALSE
            # avoids retaining the much larger model frame. x/y are stripped after
            # baseline/concordance extraction and are not retained in frozen fits.
            x = TRUE, y = TRUE, model = FALSE,
            control = survival::coxph.control(iter.max = 50)
          ),
          warning = function(w) {
            fit_warnings <<- c(fit_warnings, conditionMessage(w))
            invokeRestart("muffleWarning")
          }
        ),
        error = function(e) {
          fit_warnings <<- c(fit_warnings, conditionMessage(e))
          NULL
        }
      )

      if (is.null(mod) || any(!is.finite(stats::coef(mod)))) {
        status[target_risk] <- "model_fit_failed"
        return(list(
          model = NULL, terms = prep$terms, transformed_target = transformed$target,
          scalers = transformed$scalers, coefficients = tibble::tibble(), baseline = tibble::tibble(),
          metadata = tibble::tibble(
            reach = reach_label, model = spec$model, forecast_label = forecast_label,
            transition = spec$transition, model_scope = spec$scope,
            spatial_framework = spec$framework, prediction_time_scale = "interval_gap_time", status = "fit failed",
            training_rows = nrow(prep$data), training_events = sum(prep$data[[spec$event_field]] == 1L, na.rm = TRUE),
            training_concordance = NA_real_,
            terms = paste(prep$terms, collapse = "; "),
            warnings = paste(unique(fit_warnings), collapse = " | ")
          ),
          target_status = status,
          target_risk = target_risk,
          drop_log = prep$drop_log
        ))
      }

      bh <- survival::basehaz(mod, centered = FALSE) %>%
        transmute(
          reach = reach_label,
          model = spec$model,
          forecast_label = forecast_label,
          time = num(time),
          baseline_cumulative_hazard = num(hazard)
        )

      beta <- stats::coef(mod)
      coef_tab <- tibble::tibble(
        reach = reach_label,
        model = spec$model,
        forecast_label = forecast_label,
        term = names(beta),
        coefficient = as.numeric(beta),
        hazard_ratio = exp(as.numeric(beta))
      )

      needed <- prep$terms
      target_complete <- target_risk
      if (length(needed) > 0L) {
        target_complete <- target_complete & stats::complete.cases(transformed$target[, needed, drop = FALSE])
      }
      status[target_risk & !target_complete] <- "missing_predictor"
      status[target_complete] <- "predicted"

      conc <- tryCatch(summary(mod)$concordance[1], error = function(e) NA_real_)
      metadata <- tibble::tibble(
        reach = reach_label,
        model = spec$model,
        forecast_label = forecast_label,
        transition = spec$transition,
        model_scope = spec$scope,
        spatial_framework = spec$framework,
        prediction_time_scale = "interval_gap_time",
        status = "fitted",
        training_rows = nrow(prep$data),
        training_events = sum(prep$data[[spec$event_field]] == 1L, na.rm = TRUE),
        training_concordance = as.numeric(conc),
        terms = paste(prep$terms, collapse = "; "),
        warnings = paste(unique(fit_warnings), collapse = " | ")
      )

      # basehaz(), coefficients and concordance have now been extracted. The
      # retained/frozen model only needs the structural components required by
      # predict.coxph(newdata=...). Removing row-length fitted vectors materially
      # reduces memory retained across transition models.
      mod$x <- NULL
      mod$y <- NULL
      mod$linear.predictors <- NULL
      mod$residuals <- NULL

      list(
        model = mod,
        terms = prep$terms,
        transformed_target = transformed$target,
        scalers = transformed$scalers %>% filter(term %in% prep$terms),
        coefficients = coef_tab,
        baseline = bh,
        metadata = metadata,
        target_status = status,
        target_risk = target_risk,
        drop_log = prep$drop_log
      )
    }

    # Prepare a new target against an already-fitted frozen full-record model.
    # This applies exactly the stored training transformations/scalers and selected
    # terms. It performs no Cox fitting and therefore makes Tn+1 a genuine reuse of
    # the frozen model rather than a second full-record fit.
    # [FRAF archive / Prediction function: prepare_frozen_target]
    # Recreate the final model design on a new target from saved terms and training scalers.
    prepare_frozen_target <- function(fit_obj, target, spec, forecast_label) {
      missing_target_fields <- setdiff(c(spec$risk_field, spec$event_field), names(target))
      if (length(missing_target_fields) > 0L) {
        stop(
          "[Frozen model target QA] ", spec$model, " target is missing required field(s): ",
          paste(missing_target_fields, collapse = ", ")
        )
      }

      selected_terms <- fit_obj$terms
      raw_sources <- unique(vapply(selected_terms, function(tm) recipe[[tm]]$source, character(1)))
      model_fields <- unique(c(
        "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
        "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "ASM_BLOCK_AREA_M2",
        spec$risk_field, spec$event_field, "GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV",
        raw_sources
      ))
      dat <- target[, intersect(model_fields, names(target)), drop = FALSE]

      # Preserve missing predictor semantics: do not replace absent future/model
      # sources by zero. They remain NA and become model_status=missing_predictor.
      for (src in raw_sources) {
        if (!src %in% names(dat)) dat[[src]] <- NA_real_
      }

      dat$PRED_TSTART <- rep(0, nrow(dat))
      dat$PRED_TSTOP <- if (nrow(dat) > 0L) {
        num(dat$tstop_yr) - num(dat$tstart_yr)
      } else {
        numeric(0)
      }

      target_risk <- dat[[spec$risk_field]] == 1L
      target_risk[is.na(target_risk)] <- FALSE
      local_supported_target <- rep(TRUE, nrow(dat))
      if (isTRUE(spec$local_only)) {
        local_supported_target <- num(dat$GEOM_SUPPORT_PREV) == 1 & num(dat$INSIDE_CHANNEL_PREV) == 1
        local_supported_target[is.na(local_supported_target)] <- FALSE
        target_risk <- target_risk & local_supported_target
      }

      status <- rep("not_in_risk_set", nrow(dat))
      if (isTRUE(spec$local_only)) {
        status[dat[[spec$risk_field]] == 1L & !local_supported_target] <- "not_modelled_local_geometry"
      }

      if (is.null(fit_obj$model)) {
        status[target_risk] <- "model_not_fitted_final_full_record"
      } else {
        for (tm in selected_terms) {
          rc <- recipe[[tm]]
          src <- rc$source
          type <- rc$transform
          x <- raw_transform(dat[[src]], type)
          sc <- fit_obj$scalers[fit_obj$scalers$term == tm, , drop = FALSE]

          if (type %in% c("z", "logkm_z")) {
            centre <- if (nrow(sc) > 0L) num(sc$centre[1]) else NA_real_
            scale <- if (nrow(sc) > 0L) num(sc$scale[1]) else NA_real_
            dat[[tm]] <- if (is.finite(centre) && is.finite(scale) && scale > 0) {
              (x - centre) / scale
            } else {
              NA_real_
            }
          } else {
            dat[[tm]] <- x
          }
        }

        target_complete <- target_risk
        if (length(selected_terms) > 0L) {
          target_complete <- target_complete & stats::complete.cases(dat[, selected_terms, drop = FALSE])
        }
        status[target_risk & !target_complete] <- "missing_predictor"
        status[target_complete] <- "predicted"
      }

      out <- fit_obj
      out$transformed_target <- dat
      out$target_status <- status
      out$target_risk <- target_risk
      out$metadata <- fit_obj$metadata %>% mutate(forecast_label = forecast_label)
      out
    }

    # Baseline cumulative hazard evaluated at an interval horizon.
    #
    # Gap-time event times derived from calendar dates can differ by fractions of
    # a day/year (leap years, decimal-year conversion). A genuine nominal one-year
    # forecast such as 2025->2026 can therefore be fractionally earlier than the
    # first training event-time step and otherwise receive H0 increment = 0.
    #
    # Use a two-day tolerance. This is training-baseline information only; it does
    # not introduce Tn+1 covariates or outcomes. It simply treats near-identical
    # annual horizons as the same prediction horizon.
    # [FRAF archive / Prediction function: hazard_at]
    # Interpolate/read cumulative baseline hazard at the requested follow-up duration.
    hazard_at <- function(bh, t, tolerance_yr = 2 / 365.25) {
      if (nrow(bh) == 0L || !is.finite(t)) return(0)
      x <- bh$time <= t + tolerance_yr
      if (!any(x)) return(0)
      max(bh$baseline_cumulative_hazard[x], na.rm = TRUE)
    }

    # [FRAF archive / Prediction function: risk_class]
    # Assign an interpretable ranked susceptibility class only to successfully scored places.
    risk_class <- function(percentile, status) {
      out <- rep(NA_character_, length(percentile))
      out[status == "not_in_risk_set"] <- "Not in risk set"
      out[status == "not_modelled_local_geometry"] <- "Not modelled: local geometry unavailable"
      out[status == "missing_predictor"] <- "Not modelled: missing predictor"
      out[grepl("^prediction_failed", status)] <- "Prediction failed"
      out[grepl("model_not_fitted|model_fit_failed", status)] <- "Model not fitted"
      ok <- status == "predicted" & is.finite(percentile)
      out[ok & percentile <= 0.20] <- "Very low"
      out[ok & percentile > 0.20 & percentile <= 0.40] <- "Low"
      out[ok & percentile > 0.40 & percentile <= 0.60] <- "Moderate"
      out[ok & percentile > 0.60 & percentile <= 0.80] <- "High"
      out[ok & percentile > 0.80] <- "Very high"
      out
    }

    # [FRAF archive / code note]
    # Predictions are computed for risk-set members with model support only;
    # out-of-risk and unscored records retain explicit status flags.
    # [FRAF archive / Prediction function: apply_fitted_model]
    # Apply an already-fitted Cox model to eligible target intervals and calculate event
    # probabilities.
    apply_fitted_model <- function(fit_obj, target, spec, forecast_label, origin_rank = NA_integer_) {
      dat <- fit_obj$transformed_target
      n <- nrow(dat)
      status <- fit_obj$target_status

      # Defensive fixed-length vectors. A non-estimable model must still return one
      # archive row per target interval; missing/narrowed fields must never create a
      # zero-length tibble column.
      if (length(status) != n) {
        status <- rep("model_not_fitted_internal_status_mismatch", n)
      }

      # [FRAF archive / Prediction function: safe_int_col]
      # Create fixed-length integer risk/QA columns when target schemas omit a field.
      safe_int_col <- function(dat, name, fallback = NULL, default = 0L) {
        if (!is.null(name) && name %in% names(dat)) {
          out <- int01(dat[[name]])
          if (length(out) == n) return(out)
        }
        if (!is.null(fallback) && length(fallback) == n) {
          out <- as.integer(fallback)
          out[is.na(out)] <- default
          return(out)
        }
        rep(as.integer(default), n)
      }

      # [FRAF archive / Prediction function: safe_num_col]
      # Create fixed-length numeric model columns while preserving NA for absent values.
      safe_num_col <- function(dat, name, default = NA_real_) {
        if (!is.null(name) && name %in% names(dat)) {
          out <- num(dat[[name]])
          if (length(out) == n) return(out)
        }
        rep(default, n)
      }

      risk_vec <- safe_int_col(
        dat, spec$risk_field,
        fallback = fit_obj$target_risk,
        default = 0L
      )
      event <- safe_int_col(dat, spec$event_field, fallback = NULL, default = 0L)

      lp <- rep(NA_real_, n)
      rh <- rep(NA_real_, n)
      prob <- rep(NA_real_, n)

      if (!is.null(fit_obj$model)) {
        idx <- which(status == "predicted")
        if (length(idx) > 0L) {
          newdat <- dat[idx, , drop = FALSE]

          # v17.10.12: all production predictor terms are already numeric transformed
          # columns. For a Cox model the reference-zero linear predictor is X beta.
          # Computing it directly avoids predict.coxph() depending on row-level fitted
          # components deliberately stripped from the frozen model for memory safety.
          beta <- stats::coef(fit_obj$model)
          lp_i <- if (length(fit_obj$terms) == 0L || length(beta) == 0L) {
            rep(0, length(idx))
          } else if (!all(fit_obj$terms %in% names(beta))) {
            rep(NA_real_, length(idx))
          } else {
            xmat <- as.matrix(newdat[, fit_obj$terms, drop = FALSE])
            storage.mode(xmat) <- "double"
            as.numeric(xmat %*% beta[fit_obj$terms])
          }

          bad_lp <- !is.finite(lp_i)
          if (any(bad_lp)) {
            status[idx[bad_lp]] <- "prediction_failed_linear_predictor"
          }
          good_idx <- idx[!bad_lp]
          good_lp <- lp_i[!bad_lp]

          if (length(good_idx) > 0L) {
            lp[good_idx] <- good_lp
            rh[good_idx] <- exp(pmax(pmin(good_lp, 700), -700))
            bh <- fit_obj$baseline
            h_inc <- vapply(good_idx, function(j) {
              duration <- num(dat$tstop_yr[j]) - num(dat$tstart_yr[j])
              max(0, hazard_at(bh, duration) - hazard_at(bh, 0))
            }, numeric(1))
            prob[good_idx] <- 1 - exp(-h_inc * rh[good_idx])
            prob[good_idx] <- pmax(0, pmin(1, prob[good_idx]))
          }
        }
      }

      percentile <- rep(NA_real_, n)

      # Rank spatial risk from the Cox linear predictor rather than from absolute
      # interval probability. For a common forecast horizon:
      #
      #   P = 1 - exp(-DeltaH0 * exp(LP))
      #
      # is monotonic in LP whenever DeltaH0 > 0, so LP and probability have exactly
      # the same ordering. LP ranking remains well-defined if a tiny timing mismatch
      # makes DeltaH0 numerically zero and all absolute probabilities tie at zero.
      ok_rank <- which(status == "predicted" & is.finite(lp))
      if (length(ok_rank) > 0L) {
        percentile[ok_rank] <- rank(lp[ok_rank], ties.method = "average") / length(ok_rank)
      }

      area <- if ("ASM_BLOCK_AREA_M2" %in% names(dat)) num(dat$ASM_BLOCK_AREA_M2) else rep(NA_real_, n)
      if (length(area) != n) area <- rep(NA_real_, n)
      area[!is.finite(area) | area <= 0] <- 1

      # Other archive columns are also protected against a narrow non-fitted target.
      place_id <- if ("PLACE_ID" %in% names(dat)) clean_key(dat$PLACE_ID) else rep(NA_character_, n)
      block_id <- if ("BLOCK_ID" %in% names(dat)) clean_key(dat$BLOCK_ID) else rep(NA_character_, n)
      y1 <- if ("y1" %in% names(dat)) as.character(dat$y1) else rep(NA_character_, n)
      y2 <- if ("y2" %in% names(dat)) as.character(dat$y2) else rep(NA_character_, n)
      tstart <- safe_num_col(dat, "tstart_yr")
      tstop <- safe_num_col(dat, "tstop_yr")
      state1 <- if ("STATE1_ONTOLOGY" %in% names(dat)) as.character(dat$STATE1_ONTOLOGY) else rep(NA_character_, n)

      tibble::tibble(
        reach = reach_label,
        model = spec$model,
        transition = spec$transition,
        model_scope = spec$scope,
        spatial_framework = spec$framework,
        forecast_label = forecast_label,
        origin_rank = origin_rank,
        PLACE_ID = place_id,
        BLOCK_ID = block_id,
        interval_start_label = y1,
        interval_end_label = y2,
        tstart_yr = tstart,
        tstop_yr = tstop,
        interval_duration_yr = tstop - tstart,
        starting_state = state1,
        risk_set = risk_vec,
        model_status = status,
        observed_event = event,
        linear_predictor = lp,
        relative_hazard = rh,
        predicted_probability = prob,
        risk_percentile = percentile,
        risk_class = risk_class(percentile, status),
        prediction_residual = ifelse(is.finite(prob), event - prob, NA_real_),
        cell_area_m2 = area
      )
    }

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Validation distinguishes ranking (AUC/AP), absolute probabilities (Brier,
    # calibration) and practical spatial prioritisation (top-area capture).
    # [FRAF archive / code note]
    # Observed-event AUC and AP address ranking; baseline event prevalence
    # must be considered when comparing AP across transition targets.
    # 4. Out-of-sample validation functions
    # -----------------------------------------------------------------------------

    # [FRAF archive / Prediction function: binary_auc]
    # Compute ROC AUC from held-out scores and observed binary events.
    binary_auc <- function(y, score) {
      ok <- y %in% c(0, 1) & is.finite(score)
      y <- y[ok]
      score <- score[ok]
      n1 <- sum(y == 1)
      n0 <- sum(y == 0)
      if (n1 == 0L || n0 == 0L) return(NA_real_)
      r <- rank(score, ties.method = "average")
      (sum(r[y == 1]) - as.double(n1) * (as.double(n1) + 1) / 2) / (as.double(n1) * as.double(n0))
    }

    # [FRAF archive / Prediction function: average_precision]
    # Summarise held-out precision-recall performance, sensitive to low event prevalence.
    average_precision <- function(y, score) {
      ok <- y %in% c(0, 1) & is.finite(score)
      y <- y[ok]
      score <- score[ok]
      if (sum(y == 1) == 0L) return(NA_real_)
      ord <- order(score, decreasing = TRUE)
      yy <- y[ord]
      precision <- cumsum(yy) / seq_along(yy)
      sum(precision[yy == 1]) / sum(yy == 1)
    }

    # [FRAF archive / Prediction function: calibration_stats]
    # Calculate Brier error and calibration intercept/slope from observed outcomes and forecast
    # probabilities.
    calibration_stats <- function(y, p) {
      ok <- y %in% c(0, 1) & is.finite(p)
      y <- y[ok]
      p <- p[ok]
      if (length(y) < 10L || length(unique(y)) < 2L) {
        return(c(intercept = NA_real_, slope = NA_real_))
      }
      eps <- 1e-8
      lp <- qlogis(pmax(eps, pmin(1 - eps, p)))
      mod <- tryCatch(stats::glm(y ~ lp, family = stats::binomial()), error = function(e) NULL)
      if (is.null(mod)) return(c(intercept = NA_real_, slope = NA_real_))
      cf <- stats::coef(mod)
      c(intercept = unname(cf[1]), slope = unname(cf[2]))
    }

    # [FRAF archive / Prediction function: calibration_deciles]
    # Aggregate predicted and observed event probabilities into score/area strata.
    calibration_deciles <- function(pred) {
      x <- pred %>% filter(model_status == "predicted", is.finite(predicted_probability))
      if (nrow(x) == 0L) return(tibble::tibble())
      # ntile handles tied probabilities and keeps approximately equal counts.
      x <- x %>% mutate(risk_decile = dplyr::ntile(predicted_probability, 10L))
      x %>%
        group_by(reach, model, transition, model_scope, forecast_label, origin_rank, risk_decile) %>%
        summarise(
          n = n(),
          events = sum(observed_event == 1L, na.rm = TRUE),
          mean_predicted_probability = mean(predicted_probability, na.rm = TRUE),
          observed_event_fraction = mean(observed_event, na.rm = TRUE),
          .groups = "drop"
        )
    }

    # [FRAF archive / code note]
    # Ranked-area capture evaluates where observed transitions occur among
    # top-scored places and is not identical to total physical erosion area.
    # [FRAF archive / Prediction function: top_area_capture]
    # Assess how much observed event count/area falls in top-ranked susceptible area fractions.
    top_area_capture <- function(pred) {
      x <- pred %>% filter(model_status == "predicted", is.finite(predicted_probability))
      if (nrow(x) == 0L) return(tibble::tibble())
      x <- x %>% arrange(desc(predicted_probability))
      total_area <- sum(x$cell_area_m2, na.rm = TRUE)
      total_event_area <- sum(x$cell_area_m2 * x$observed_event, na.rm = TRUE)
      total_events <- sum(x$observed_event, na.rm = TRUE)
      x$cumulative_area_share <- cumsum(x$cell_area_m2) / total_area

      bind_rows(lapply(c(0.10, 0.20, 0.30), function(thr) {
        keep <- x$cumulative_area_share <= thr
        if (!any(keep)) keep[1] <- TRUE
        tibble::tibble(
          reach = x$reach[1], model = x$model[1], transition = x$transition[1],
          model_scope = x$model_scope[1], forecast_label = x$forecast_label[1],
          origin_rank = x$origin_rank[1], top_area_fraction = thr,
          selected_area_m2 = sum(x$cell_area_m2[keep], na.rm = TRUE),
          event_count_captured = sum(x$observed_event[keep], na.rm = TRUE),
          event_count_capture_fraction = ifelse(total_events > 0, sum(x$observed_event[keep], na.rm = TRUE) / total_events, NA_real_),
          event_area_captured_m2 = sum(x$cell_area_m2[keep] * x$observed_event[keep], na.rm = TRUE),
          event_area_capture_fraction = ifelse(total_event_area > 0, sum(x$cell_area_m2[keep] * x$observed_event[keep], na.rm = TRUE) / total_event_area, NA_real_)
        )
      }))
    }

    # [FRAF archive / Prediction function: validation_summary]
    # Collect prediction-model metadata, discrimination, calibration and other held-out metrics.
    validation_summary <- function(pred, fit_meta) {
      # Defensive metadata accessor. Some legitimate non-fit branches (for example
      # too few events at an early rolling origin) do not have fitted-model
      # diagnostics. They must be reported, not allowed to terminate the workflow.
      # [FRAF archive / Prediction function: meta_scalar]
      # Read a scalar field from a metadata record with a stable fallback.
      meta_scalar <- function(name, default = NA) {
        if (is.null(fit_meta) || nrow(fit_meta) == 0L || !name %in% names(fit_meta)) return(default)
        z <- fit_meta[[name]][1]
        if (length(z) == 0L) default else z
      }

      x <- pred %>% filter(model_status == "predicted", is.finite(predicted_probability))

      # Preserve the actual forecast-origin/test-interval identifiers even where a
      # model cannot be estimated at that origin.
      pred_origin <- if (nrow(pred) > 0L && any(is.finite(pred$origin_rank))) {
        as.integer(pred$origin_rank[which(is.finite(pred$origin_rank))[1]])
      } else NA_integer_
      pred_start <- if (nrow(pred) > 0L && any(is.finite(pred$tstart_yr))) min(pred$tstart_yr[is.finite(pred$tstart_yr)]) else NA_real_
      pred_end <- if (nrow(pred) > 0L && any(is.finite(pred$tstop_yr))) max(pred$tstop_yr[is.finite(pred$tstop_yr)]) else NA_real_

      if (nrow(x) == 0L) {
        return(tibble::tibble(
          reach = as.character(meta_scalar("reach", if (nrow(pred) > 0L) pred$reach[1] else reach_label)),
          model = as.character(meta_scalar("model", if (nrow(pred) > 0L) pred$model[1] else NA_character_)),
          transition = as.character(meta_scalar("transition", if (nrow(pred) > 0L) pred$transition[1] else NA_character_)),
          model_scope = as.character(meta_scalar("model_scope", if (nrow(pred) > 0L) pred$model_scope[1] else NA_character_)),
          forecast_label = as.character(meta_scalar("forecast_label", if (nrow(pred) > 0L) pred$forecast_label[1] else NA_character_)),
          origin_rank = pred_origin,
          interval_start = pred_start,
          interval_end = pred_end,
          n_predictions = 0L,
          observed_events = 0L,
          auc = NA_real_,
          average_precision = NA_real_,
          brier_score = NA_real_,
          calibration_intercept = NA_real_,
          calibration_slope = NA_real_,
          training_rows = as.integer(meta_scalar("training_rows", 0L)),
          training_events = as.integer(meta_scalar("training_events", 0L)),
          training_concordance = as.numeric(meta_scalar("training_concordance", NA_real_)),
          model_status = as.character(meta_scalar("status", "not fitted"))
        ))
      }

      cal <- calibration_stats(x$observed_event, x$predicted_probability)
      tibble::tibble(
        reach = x$reach[1],
        model = x$model[1],
        transition = x$transition[1],
        model_scope = x$model_scope[1],
        forecast_label = x$forecast_label[1],
        origin_rank = x$origin_rank[1],
        interval_start = min(x$tstart_yr, na.rm = TRUE),
        interval_end = max(x$tstop_yr, na.rm = TRUE),
        n_predictions = nrow(x),
        observed_events = sum(x$observed_event == 1L, na.rm = TRUE),
        auc = binary_auc(x$observed_event, x$predicted_probability),
        average_precision = average_precision(x$observed_event, x$predicted_probability),
        brier_score = mean((x$observed_event - x$predicted_probability)^2, na.rm = TRUE),
        calibration_intercept = cal[["intercept"]],
        calibration_slope = cal[["slope"]],
        training_rows = as.integer(meta_scalar("training_rows", 0L)),
        training_events = as.integer(meta_scalar("training_events", 0L)),
        training_concordance = as.numeric(meta_scalar("training_concordance", NA_real_)),
        model_status = as.character(meta_scalar("status", "unknown"))
      )
    }

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Origin T ranks refer to observation sequences or elapsed study years according
    # to the explicit QGIS parameter; do not equate ranks with calendar years.
    # 5. Resolve T10, T20 and T30 forecast origins
    # -----------------------------------------------------------------------------

    origin_values <- suppressWarnings(as.numeric(trimws(unlist(strsplit(ForecastOrigins, "[,; ]+")))))
    origin_values <- unique(origin_values[is.finite(origin_values)])
    if (length(origin_values) == 0L) stop("ForecastOrigins contains no usable values.")

    origin_table <- risk %>%
      distinct(tstart_yr, y1) %>%
      arrange(tstart_yr) %>%
      mutate(origin_rank = row_number())

    if (identical(origin_mode, "Unique interval-start rank")) {
      origins <- origin_table %>% filter(origin_rank %in% as.integer(origin_values))
    } else {
      t0 <- min(origin_table$tstart_yr, na.rm = TRUE)
      origins <- bind_rows(lapply(origin_values, function(v) {
        target <- t0 + v
        origin_table %>% slice(which.min(abs(tstart_yr - target))) %>% mutate(requested_elapsed_year = v)
      })) %>% distinct(origin_rank, .keep_all = TRUE)
    }

    if (nrow(origins) == 0L) {
      write_csv(origin_table, file.path(out_dir, "20_available_forecast_origins.csv"))
      stop("None of the requested origins is available. See 10_available_forecast_origins.csv")
    }
    write_csv(origin_table, file.path(out_dir, "20_available_forecast_origins.csv"))
    write_csv(origins, file.path(out_dir, "20_selected_forecast_origins.csv"))

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # For each origin, train on previously completed intervals and score the next
    # held-out interval; a non-risk row must never be interpreted as low risk.
    # [FRAF archive / code note]
    # Every rolling evaluation uses an origin-specific training cut-off;
    # the target interval is fully held out during model fitting.
    # 6. Rolling-origin fitting and prediction
    # -----------------------------------------------------------------------------

    # Build one narrow prediction table containing only fields used by any enabled
    # transition model/archive. The historic Risk Table can be very wide; retaining
    # it while creating rolling training copies materially increases peak RAM.
    prediction_raw_sources <- unique(vapply(
      unique(unlist(lapply(transition_specs, function(s) s$candidates))),
      function(tm) recipe[[tm]]$source, character(1)
    ))
    prediction_risk_event_fields <- unique(unlist(lapply(
      transition_specs, function(s) c(s$risk_field, s$event_field)
    )))
    prediction_fields <- unique(c(
      "PLACE_ID", "BLOCK_ID", "y1", "y2", "tstart_yr", "tstop_yr",
      "STATE1_ONTOLOGY", "STATE2_ONTOLOGY", "ASM_BLOCK_AREA_M2",
      "GEOM_SUPPORT_PREV", "INSIDE_CHANNEL_PREV",
      prediction_risk_event_fields, prediction_raw_sources
    ))
    risk_prediction <- risk[, intersect(prediction_fields, names(risk)), drop = FALSE]
    message(
      "[Memory] Model-ready prediction table narrowed from projected input ", ncol(risk), " to ",
      ncol(risk_prediction), " columns for ", format(nrow(risk_prediction), big.mark = ","), " rows."
    )
    rm(risk)
    invisible(gc(full = TRUE))

    # v17.10.5: stream the large row-level archive directly to gzip rather than
    # retaining every model/origin prediction and then duplicating it in bind_rows().
    rolling_prediction_path <- file.path(out_dir, "20_rolling_prediction_archive.csv.gz")
    rolling_prediction_con <- gzfile(rolling_prediction_path, open = "wb")
    rolling_prediction_header_written <- FALSE

    all_validation <- list()
    all_calibration <- list()
    all_capture <- list()
    all_coefficients <- list()
    all_baselines <- list()
    all_scalers <- list()
    all_metadata <- list()
    all_dropped <- list()

    for (oi in seq_len(nrow(origins))) {
      origin_start <- origins$tstart_yr[oi]
      origin_rank <- origins$origin_rank[oi]
      forecast_label <- paste0("T", origin_rank)

      train <- risk_prediction %>% filter(tstop_yr <= origin_start + 1e-10)
      test <- risk_prediction %>% filter(abs(tstart_yr - origin_start) <= 1e-10)

      message("[Rolling] ", forecast_label, ": training rows = ", nrow(train), ", test rows = ", nrow(test))
      if (nrow(test) == 0L) {
        rm(train, test)
        invisible(gc(FALSE))
        next
      }

      for (spec in transition_specs) {
        message(sprintf("  [Model] %s | %s", spec$model, spec$transition))
        fit_obj <- fit_cox_model(train, test, spec, forecast_label)
        message(sprintf("    status=%s; training risk rows=%s; training events=%s",
                        as.character(fit_obj$metadata$status[1]),
                        format(fit_obj$metadata$training_rows[1], big.mark = ",", scientific = FALSE),
                        format(fit_obj$metadata$training_events[1], big.mark = ",", scientific = FALSE)))
        pred <- apply_fitted_model(fit_obj, test, spec, forecast_label, origin_rank)
        n_status_pred <- sum(pred$model_status == "predicted", na.rm = TRUE)
        n_finite_prob <- sum(pred$model_status == "predicted" & is.finite(pred$predicted_probability), na.rm = TRUE)
        n_pred_fail <- sum(grepl("^prediction_failed", pred$model_status), na.rm = TRUE)
        message(sprintf(
          "    predicted status rows=%s; finite probability rows=%s; prediction failures=%s",
          format(n_status_pred, big.mark = ",", scientific = FALSE),
          format(n_finite_prob, big.mark = ",", scientific = FALSE),
          format(n_pred_fail, big.mark = ",", scientific = FALSE)
        ))
        if (n_status_pred > 0L && n_finite_prob == 0L) {
          warning(
            "[Rolling prediction QA] ", spec$model, " ", forecast_label,
            " has rows marked predicted but no finite probabilities."
          )
        }

        readr::write_csv(
          pred, rolling_prediction_con, na = "",
          col_names = !rolling_prediction_header_written
        )
        rolling_prediction_header_written <- TRUE

        all_validation[[length(all_validation) + 1L]] <- validation_summary(pred, fit_obj$metadata)
        all_calibration[[length(all_calibration) + 1L]] <- calibration_deciles(pred)
        all_capture[[length(all_capture) + 1L]] <- top_area_capture(pred)
        all_coefficients[[length(all_coefficients) + 1L]] <- fit_obj$coefficients
        all_baselines[[length(all_baselines) + 1L]] <- fit_obj$baseline
        all_scalers[[length(all_scalers) + 1L]] <- fit_obj$scalers
        all_metadata[[length(all_metadata) + 1L]] <- fit_obj$metadata %>% mutate(origin_rank = origin_rank, origin_time = origin_start)
        if (nrow(fit_obj$drop_log) > 0L) {
          all_dropped[[length(all_dropped) + 1L]] <- fit_obj$drop_log %>%
            mutate(reach = reach_label, model = spec$model, forecast_label = forecast_label, .before = 1)
        }

        # The row-level prediction has already been streamed and all small summaries
        # extracted. Release the fitted object before fitting the next transition.
        rm(fit_obj, pred)
        invisible(gc(FALSE))
      }
      rm(train, test)
      invisible(gc(FALSE))
    }
    close(rolling_prediction_con)

    # Zero-event training windows are valid rolling-origin outcomes; retain them as not estimable.
    # The row-level prediction archive is already on disk and is intentionally not
    # rebound into a second million-row in-memory object.

    validation_table <- bind_rows(all_validation)
    calibration_table <- bind_rows(all_calibration)
    capture_table <- bind_rows(all_capture)
    coefficient_table <- bind_rows(all_coefficients)
    baseline_table <- bind_rows(all_baselines)
    scaler_table <- bind_rows(all_scalers)
    metadata_table <- bind_rows(all_metadata)
    dropped_table <- bind_rows(all_dropped)

    write_csv(validation_table, file.path(out_dir, "20_rolling_validation_summary.csv"))
    write_csv(calibration_table, file.path(out_dir, "20_rolling_calibration_deciles.csv"))
    write_csv(capture_table, file.path(out_dir, "20_rolling_top_area_capture.csv"))
    write_csv(coefficient_table, file.path(out_dir, "20_rolling_model_coefficients.csv"))
    write_csv_gz(baseline_table, file.path(out_dir, "20_rolling_baseline_cumulative_hazard.csv.gz"))
    write_csv(scaler_table, file.path(out_dir, "20_rolling_training_scalers.csv"))
    write_csv(metadata_table, file.path(out_dir, "20_rolling_model_metadata.csv"))
    if (nrow(dropped_table) > 0L) write_csv(dropped_table, file.path(out_dir, "20_rolling_dropped_terms.csv"))

    if (isTRUE(WriteParquet)) {
      message(
        "[Parquet] 20_rolling_prediction_archive is retained as streamed CSV.gz in v17.10.5; ",
        "materialising a single row-level Parquet object is suppressed to protect peak memory."
      )
    }
    invisible(write_optional_parquet(baseline_table, file.path(out_dir, "20_rolling_baseline_cumulative_hazard.parquet")))

    # Validation figures.
    if (nrow(calibration_table) > 0L) {
      p_cal <- ggplot(calibration_table, aes(mean_predicted_probability, observed_event_fraction)) +
        geom_abline(slope = 1, intercept = 0, linetype = 2) +
        geom_point() +
        geom_line() +
        # Free facet scales are retained because absolute probabilities can differ
        # substantially among transition processes. A fixed aspect ratio is incompatible
        # with free facet scales in recent ggplot2 releases.
        facet_grid(model ~ forecast_label, scales = "free") +
        labs(
          title = paste0(reach_label, ": rolling-origin probability calibration"),
          x = "Mean predicted interval probability",
          y = "Observed transition fraction"
        ) +
        theme_bw(base_size = 10)
      safe_ggsave(file.path(out_dir, "20_rolling_calibration.png"), p_cal, width = 11, height = 8, dpi = 300, bg = "white")
      safe_ggsave(file.path(out_dir, "20_rolling_calibration.pdf"), p_cal, width = 11, height = 8)
    }

    if (nrow(validation_table) > 0L) {
      val_long <- validation_table %>%
        select(model, forecast_label, auc, average_precision, brier_score) %>%
        tidyr::pivot_longer(c(auc, average_precision, brier_score), names_to = "metric", values_to = "value")
      p_val <- ggplot(val_long, aes(forecast_label, value, group = metric, shape = metric)) +
        geom_point(size = 2.2) + geom_line() +
        facet_wrap(~ model, scales = "free_y") +
        labs(
          title = paste0(reach_label, ": T10/T20/T30 rolling-origin validation"),
          x = "Forecast origin", y = "Metric value", shape = "Metric"
        ) + theme_bw(base_size = 10)
      safe_ggsave(file.path(out_dir, "20_rolling_validation_metrics.png"), p_val, width = 11, height = 7, dpi = 300, bg = "white")
      safe_ggsave(file.path(out_dir, "20_rolling_validation_metrics.pdf"), p_val, width = 11, height = 7)
    }

    # All rolling figures/tables have now been written. Release their backing lists
    # and assembled summaries before the million-row final full-record fit.
    rm(
      all_validation, all_calibration, all_capture, all_coefficients,
      all_baselines, all_scalers, all_metadata, all_dropped,
      validation_table, calibration_table, capture_table, coefficient_table,
      baseline_table, scaler_table, metadata_table, dropped_table
    )
    invisible(gc(full = TRUE))
    message("[Memory] Rolling-origin objects released before final full-record fitting.")

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Final fits use the full available record after rolling tests and are distinct
    # from held-out origin performance. Coefficients/scalers/baselines are exported.
    # [FRAF archive / code note]
    # Full-record models are frozen only after independent-origin testing;
    # their in-sample output must not be relabelled as held-out skill.
    # 7. Final frozen models and optional full fitted archive
    # -----------------------------------------------------------------------------

    final_coeff <- list()
    final_base <- list()
    final_scalers <- list()
    final_meta <- list()
    final_models <- list()
    final_fit_objects <- list()

    full_fitted_con <- NULL
    full_fitted_header_written <- FALSE
    if (isTRUE(WriteFullFittedPredictions)) {
      full_fitted_con <- gzfile(
        file.path(out_dir, "21_full_record_fitted_prediction_archive.csv.gz"),
        open = "wb"
      )
    }

    for (spec in transition_specs) {
      message("[Final model] fitting frozen full-record model: ", spec$model)
      fit_obj <- fit_cox_model(
        risk_prediction, target = NULL, spec = spec,
        forecast_label = "FINAL_FULL_RECORD", fit_only = TRUE
      )
      final_coeff[[length(final_coeff) + 1L]] <- fit_obj$coefficients
      final_base[[length(final_base) + 1L]] <- fit_obj$baseline
      final_scalers[[length(final_scalers) + 1L]] <- fit_obj$scalers
      final_meta[[length(final_meta) + 1L]] <- fit_obj$metadata
      final_models[[spec$model]] <- fit_obj$model

      # Keep only the compact frozen components needed for optional fitted values
      # and genuine Tn+1 reuse. transformed_target/status are zero-length in fit-only mode.
      frozen_obj <- fit_obj
      frozen_obj$transformed_target <- NULL
      frozen_obj$target_status <- NULL
      frozen_obj$target_risk <- NULL
      final_fit_objects[[spec$model]] <- frozen_obj

      if (isTRUE(WriteFullFittedPredictions)) {
        fitted_target <- prepare_frozen_target(
          frozen_obj, risk_prediction, spec, "FINAL_FULL_RECORD"
        )
        ff_chunk <- apply_fitted_model(
          fitted_target, risk_prediction, spec, "FINAL_FULL_RECORD", NA_integer_
        )
        readr::write_csv(
          ff_chunk, full_fitted_con, na = "",
          col_names = !full_fitted_header_written
        )
        full_fitted_header_written <- TRUE
        rm(fitted_target, ff_chunk)
      }

      rm(fit_obj, frozen_obj)
      invisible(gc(FALSE))
    }

    if (!is.null(full_fitted_con)) close(full_fitted_con)

    final_coeff_table <- bind_rows(final_coeff)
    final_base_table <- bind_rows(final_base)
    final_scaler_table <- bind_rows(final_scalers)
    final_meta_table <- bind_rows(final_meta)

    write_csv(final_coeff_table, file.path(out_dir, "21_final_model_coefficients.csv"))
    write_csv_gz(final_base_table, file.path(out_dir, "21_final_baseline_cumulative_hazard.csv.gz"))
    write_csv(final_scaler_table, file.path(out_dir, "21_final_training_scalers.csv"))
    write_csv(final_meta_table, file.path(out_dir, "21_final_model_metadata.csv"))
    saveRDS(final_models, file.path(out_dir, "21_final_frozen_cox_models.rds"), compress = "xz")

    if (isTRUE(WriteFullFittedPredictions) && isTRUE(WriteParquet)) {
      message(
        "[Parquet] 21_full_record_fitted_prediction_archive is retained as streamed CSV.gz; ",
        "single-file row-level Parquet materialisation is suppressed in memory-safe mode."
      )
    }

    # Small final summary lists are no longer needed once written. The compact
    # final_fit_objects and final_models are retained for Tn+1 reuse / RDS output.
    rm(final_coeff, final_base, final_scalers, final_meta)
    invisible(gc(full = TRUE))

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Prospective forecast mode: score a supplied present-time risk population
    # without any observed next-interval event or unseen next-interval geometry.
    # [FRAF archive / code note]
    # Future input contains no outcome by definition. Its temporary event
    # placeholders are never evidence of no transition in Tn+1.
    # 8. Optional genuine Tn+1 forecast from a separate Tn covariate table
    # -----------------------------------------------------------------------------

    future_raw <- if (length(FutureCovariateTable) == 0L || is.na(FutureCovariateTable[1])) "" else as.character(FutureCovariateTable[1])
    future_path <- trimws(future_raw)
    # Backward-compatible placeholders sometimes entered because older QGIS dialogs
    # incorrectly required this optional parameter. They mean: no prospective Tn+1 run.
    if (tolower(future_path) %in% c("temp", "none", "null", "na", "<none>")) future_path <- ""

    if (nzchar(future_path)) {
      future <- read_future_table_any(future_path, FutureLayerName)
      future_source_layer <- attr(future, "future_source_layer")
      message(
        "[Future QA] Future table loaded | layer=", future_source_layer,
        "; rows=", format(nrow(future), big.mark = ","),
        "; columns=", ncol(future)
      )
      message(
        "[Future QA] Future PRIMARY risk fields present: ",
        paste(intersect(future_schema_fields, names(future)), collapse = ", ")
      )

      if (!"PLACE_ID" %in% names(future) && "BLOCK_ID" %in% names(future)) future$PLACE_ID <- future$BLOCK_ID
      if (!"BLOCK_ID" %in% names(future) && "PLACE_ID" %in% names(future)) future$BLOCK_ID <- future$PLACE_ID
      if (!all(c("PLACE_ID", "BLOCK_ID") %in% names(future))) stop("Future table requires PLACE_ID or BLOCK_ID.")
      future$PLACE_ID <- clean_key(future$PLACE_ID)
      future$BLOCK_ID <- clean_key(future$BLOCK_ID)

      # ---------------------------------------------------------------------------
      # Future event/risk fields
      # ---------------------------------------------------------------------------
      # A genuine forecast has no observed Tn+1 event. Event columns are placeholders
      # only and are deliberately forced to zero before prediction; the exported
      # future archive later resets observed_event to NA.
      future$FP_REACTIVATE_EVT_MODEL <- rep(0L, nrow(future))
      future$REACTIVATE_EVT_MODEL <- rep(0L, nrow(future))
      future$STORAGE_EVT_MODEL <- rep(0L, nrow(future))
      future$STABILISE_EVT_MODEL <- rep(0L, nrow(future))
      future$STORAGE_REWORK_EVT_MODEL <- rep(0L, nrow(future))

      broad_future_candidates <- c("FP_REACTIVATE_RISK_SET_PRIMARY", "FP_REACTIVATE_RISK_SET")
      future_risk_map <- list(
        REACTIVATE_RISK_MODEL = c("REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET"),
        STORAGE_RISK_MODEL = c("STORAGE_RISK_SET_PRIMARY", "STORAGE_RISK_SET"),
        STABILISE_RISK_MODEL = c("STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET"),
        STORAGE_REWORK_RISK_MODEL = c("STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET")
      )
      if (run_broad_prediction && any(broad_future_candidates %in% names(future))) {
        future_risk_map <- c(list(FP_REACTIVATE_RISK_MODEL = broad_future_candidates), future_risk_map)
      } else {
        future$FP_REACTIVATE_RISK_MODEL <- rep(0L, nrow(future))
      }

      if (run_broad_prediction && !any(broad_future_candidates %in% names(future))) {
        warning(
          "[Future QA] Broad floodplain risk field is absent from the future table; ",
          "the broad model will be skipped for this Tn+1 application. Other transition forecasts continue."
        )
      }

      available_future_risk_sources <- intersect(
        unique(unlist(future_risk_map, use.names = FALSE)),
        names(future)
      )
      if (length(available_future_risk_sources) == 0L) {
        stop(
          "[Future QA] The loaded future layer contains none of the expected risk-set fields. ",
          "This is not a valid Module 5e future covariate table. Loaded layer='",
          future_source_layer, "'. First fields: ",
          paste(head(names(future), 30), collapse = ", ")
        )
      }

      for (out_nm in names(future_risk_map)) {
        present <- future_risk_map[[out_nm]][future_risk_map[[out_nm]] %in% names(future)]
        if (length(present) > 0L) {
          counts <- vapply(present, function(nm) sum(int01(future[[nm]]) == 1L, na.rm = TRUE), numeric(1))
          informative <- present[counts > 0]
          chosen <- if (length(informative) > 0L) informative[1] else present[1]
          future[[out_nm]] <- int01(future[[chosen]])
          message(
            "[Future QA] ", out_nm, " source=", chosen,
            "; risk rows=", format(sum(future[[out_nm]] == 1L, na.rm = TRUE), big.mark = ",")
          )
        } else {
          future[[out_nm]] <- rep(0L, nrow(future))
          message("[Future QA] ", out_nm, ": no source field found; initialised to zero.")
        }
      }

      # Both competing exits originate in Depositional Storage. If a legacy future
      # table lacks the dedicated reworking risk field, use the stabilisation risk
      # population. If both are present they must agree exactly.
      if (
        sum(future$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE) == 0L &&
        sum(future$STABILISE_RISK_MODEL == 1L, na.rm = TRUE) > 0L
      ) {
        warning(
          "[Future QA] Storage-reworking risk set is empty; using the stabilisation ",
          "risk set as the common Depositional-Storage starting population."
        )
        future$STORAGE_REWORK_RISK_MODEL <- future$STABILISE_RISK_MODEL
      }

      future_storage_risk_mismatch <- sum(
        future$STORAGE_REWORK_RISK_MODEL != future$STABILISE_RISK_MODEL,
        na.rm = TRUE
      )
      if (future_storage_risk_mismatch > 0L) {
        stop(
          "[Future QA] ", future_storage_risk_mismatch,
          " rows disagree between storage-reworking and stabilisation risk sets. ",
          "Both transitions must use the same Tn Depositional-Storage population."
        )
      }

      future_risk_counts <- c(
        broad_floodplain_reactivation = sum(future$FP_REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE),
        strict_reactivation = sum(future$REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE),
        storage_formation = sum(future$STORAGE_RISK_MODEL == 1L, na.rm = TRUE),
        stabilisation = sum(future$STABILISE_RISK_MODEL == 1L, na.rm = TRUE),
        storage_reworking = sum(future$STORAGE_REWORK_RISK_MODEL == 1L, na.rm = TRUE)
      )
      message(
        "[Future QA] transition risk rows | broad FP reactivation=",
        format(future_risk_counts[["broad_floodplain_reactivation"]], big.mark = ","),
        "; strict SF reactivation=",
        format(future_risk_counts[["strict_reactivation"]], big.mark = ","),
        "; storage formation=",
        format(future_risk_counts[["storage_formation"]], big.mark = ","),
        "; stabilisation=",
        format(future_risk_counts[["stabilisation"]], big.mark = ","),
        "; storage reworking=",
        format(future_risk_counts[["storage_reworking"]], big.mark = ",")
      )
      if (sum(future_risk_counts) == 0L) {
        stop(
          "[Future QA] All enabled future transition risk sets are empty. ",
          "Do not write a future prediction archive. Check the selected Module 5e layer."
        )
      }
      if (!"STATE1_ONTOLOGY" %in% names(future)) future$STATE1_ONTOLOGY <- NA_character_
      if (!"STATE2_ONTOLOGY" %in% names(future)) future$STATE2_ONTOLOGY <- NA_character_
      if (!"y1" %in% names(future)) future$y1 <- FutureStartTime
      if (!"y2" %in% names(future)) future$y2 <- FutureStopTime
      if (!"tstart_yr" %in% names(future) || all(!is.finite(num(future$tstart_yr)))) future$tstart_yr <- num(FutureStartTime)
      if (!"tstop_yr" %in% names(future) || all(!is.finite(num(future$tstop_yr)))) future$tstop_yr <- num(FutureStopTime)
      future$tstart_yr <- num(future$tstart_yr)
      future$tstop_yr <- num(future$tstop_yr)
      if (any(!is.finite(future$tstart_yr)) || any(!is.finite(future$tstop_yr)) || any(future$tstop_yr <= future$tstart_yr)) {
        stop("Future forecast requires valid FutureStartTime and FutureStopTime, or valid tstart_yr/tstop_yr fields.")
      }

      future_required_model_fields <- c(
        "FP_REACTIVATE_RISK_MODEL", "FP_REACTIVATE_EVT_MODEL",
        "REACTIVATE_RISK_MODEL", "REACTIVATE_EVT_MODEL",
        "STORAGE_RISK_MODEL", "STORAGE_EVT_MODEL",
        "STABILISE_RISK_MODEL", "STABILISE_EVT_MODEL",
        "STORAGE_REWORK_RISK_MODEL", "STORAGE_REWORK_EVT_MODEL"
      )
      missing_future_model_fields <- setdiff(future_required_model_fields, names(future))
      if (length(missing_future_model_fields) > 0L) {
        stop(
          "[Future QA] Missing required future model field(s): ",
          paste(missing_future_model_fields, collapse = ", ")
        )
      }

      # Numeric conversion and canonical local aliases are repeated for the future
      # table using the same selected exposure definitions.
      for (nm in intersect(numeric_candidates, names(future))) future[[nm]] <- num(future[[nm]])
      if (!"MAM_NEAR_CHANNEL_PREV" %in% names(future) && react_near_source %in% names(future)) future$MAM_NEAR_CHANNEL_PREV <- binary_from(future[[react_near_source]])
      if (!"MAM_OUTER_CURV_REACT_PREV" %in% names(future) && react_curv_source %in% names(future)) future$MAM_OUTER_CURV_REACT_PREV <- num(future[[react_curv_source]])
      if (!"MAM_NEAR_BANK_STORAGE_PREV" %in% names(future) && storage_near_source %in% names(future)) future$MAM_NEAR_BANK_STORAGE_PREV <- binary_from(future[[storage_near_source]])
      if (!"MAM_INNER_CURV_STORAGE_PREV" %in% names(future) && inner_storage_source %in% names(future)) future$MAM_INNER_CURV_STORAGE_PREV <- num(future[[inner_storage_source]])
      if (!"MAM_OUTER_CURV_STORAGE_PREV" %in% names(future) && outer_storage_source %in% names(future)) future$MAM_OUTER_CURV_STORAGE_PREV <- num(future[[outer_storage_source]])
      if (!"MAM_OUTER_REACT_EXPOSED_PREV" %in% names(future)) {
        future$MAM_OUTER_REACT_EXPOSED_PREV <- if (all(c("MAM_NEAR_CHANNEL_PREV", "OUTER_BANK_PREV") %in% names(future))) {
          int01(future$MAM_NEAR_CHANNEL_PREV == 1 & num(future$OUTER_BANK_PREV) == 1)
        } else rep(0L, nrow(future))
      }
      if (!"MAM_INNER_STORAGE_EXPOSED_PREV" %in% names(future)) {
        future$MAM_INNER_STORAGE_EXPOSED_PREV <- if (all(c("MAM_NEAR_BANK_STORAGE_PREV", "INNER_BANK_PREV") %in% names(future))) {
          int01(future$MAM_NEAR_BANK_STORAGE_PREV == 1 & num(future$INNER_BANK_PREV) == 1)
        } else rep(0L, nrow(future))
      }
      if (!"MAM_OUTER_STORAGE_EXPOSED_PREV" %in% names(future)) {
        future$MAM_OUTER_STORAGE_EXPOSED_PREV <- if (all(c("MAM_NEAR_BANK_STORAGE_PREV", "OUTER_BANK_PREV") %in% names(future))) {
          int01(future$MAM_NEAR_BANK_STORAGE_PREV == 1 & num(future$OUTER_BANK_PREV) == 1)
        } else rep(0L, nrow(future))
      }

      # Missing future predictors remain explicitly unavailable; they are never
      # imputed to zero and will receive model_status = missing_predictor.
      future_sources <- unique(vapply(
        unique(unlist(lapply(transition_specs, function(s) s$candidates))),
        function(tm) recipe[[tm]]$source, character(1)
      ))
      for (src in future_sources) {
        if (!src %in% names(future)) future[[src]] <- NA_real_
      }

      future_specs <- transition_specs
      if (!("FP_REACTIVATE_RISK_MODEL" %in% names(future)) || sum(future$FP_REACTIVATE_RISK_MODEL == 1L, na.rm = TRUE) == 0L) {
        future_specs <- Filter(function(s) !identical(s$model, "floodplain_reactivation_broad"), future_specs)
      }
      future_prediction_path <- file.path(out_dir, "22_future_Tn_plus_1_prediction_archive.csv.gz")
      future_prediction_con <- gzfile(future_prediction_path, open = "wb")
      future_prediction_header_written <- FALSE
      future_meta <- list()
      for (spec in future_specs) {
        frozen_obj <- final_fit_objects[[spec$model]]
        if (is.null(frozen_obj)) {
          stop("[Future prediction] Frozen final model object unavailable for ", spec$model)
        }
        message("[Future prediction] reusing frozen FINAL_FULL_RECORD model: ", spec$model)
        fit_obj <- prepare_frozen_target(frozen_obj, future, spec, "FUTURE_TN_PLUS_1")
        pred <- apply_fitted_model(fit_obj, future, spec, "FUTURE_TN_PLUS_1", NA_integer_)

        # Future prediction QA: distinguish a genuinely non-varying model from an
        # absolute-probability collapse caused by the baseline-horizon lookup.
        pred_ok <- pred$model_status == "predicted"
        lp_ok <- pred$linear_predictor[pred_ok & is.finite(pred$linear_predictor)]
        pr_ok <- pred$predicted_probability[pred_ok & is.finite(pred$predicted_probability)]
        pc_ok <- pred$risk_percentile[pred_ok & is.finite(pred$risk_percentile)]
        message(
          "[Future prediction QA] ", spec$model,
          " | predicted=", sum(pred_ok, na.rm = TRUE),
          "; finite LP=", length(lp_ok),
          "; unique LP=", length(unique(signif(lp_ok, 12))),
          "; LP range=",
          if (length(lp_ok)) paste0(signif(min(lp_ok), 6), "..", signif(max(lp_ok), 6)) else "NA",
          "; finite probability=", length(pr_ok),
          "; unique probability=", length(unique(signif(pr_ok, 12))),
          "; probability range=",
          if (length(pr_ok)) paste0(signif(min(pr_ok), 6), "..", signif(max(pr_ok), 6)) else "NA",
          "; percentile range=",
          if (length(pc_ok)) paste0(signif(min(pc_ok), 6), "..", signif(max(pc_ok), 6)) else "NA"
        )

        if (length(lp_ok) > 1L && length(unique(signif(lp_ok, 12))) > 1L &&
            length(pr_ok) > 0L && length(unique(signif(pr_ok, 12))) == 1L) {
          warning(
            "[Future prediction QA] ", spec$model,
            " has varying linear predictors but tied absolute probabilities. ",
            "Percentile risk remains valid because it is ranked from LP."
          )
        }

        # Observed event is intentionally unavailable for a genuine forecast.
        pred$observed_event <- NA_integer_
        pred$prediction_residual <- NA_real_
        readr::write_csv(
          pred, future_prediction_con, na = "",
          col_names = !future_prediction_header_written
        )
        future_prediction_header_written <- TRUE
        future_meta[[length(future_meta) + 1L]] <- fit_obj$metadata
        rm(fit_obj, pred, frozen_obj)
        invisible(gc(FALSE))
      }
      close(future_prediction_con)
      write_csv(bind_rows(future_meta), file.path(out_dir, "22_future_Tn_plus_1_model_metadata.csv"))
      if (isTRUE(WriteParquet)) {
        message(
          "[Parquet] 22_future_Tn_plus_1_prediction_archive is retained as streamed CSV.gz; ",
          "single-file row-level Parquet materialisation is suppressed in memory-safe mode."
        )
      }
      rm(future_meta)
      invisible(gc(full = TRUE))
    }

    # Final prediction objects are no longer needed after the optional future run.
    # Release them before the review-package stage, which reads outputs from disk.
    rm(
      final_fit_objects, final_models, risk_prediction,
      final_coeff_table, final_base_table, final_scaler_table, final_meta_table,
      prediction_raw_sources, prediction_risk_event_fields, prediction_fields
    )
    invisible(gc(full = TRUE))

    # -----------------------------------------------------------------------------
    # [FRAF archive / workflow]
    # Write a machine-readable inventory of prediction artifacts; the separate
    # completion marker and review pack document whether a branch finished.
    # [FRAF archive / code note]
    # The prediction manifest labels compressed event archives, scalers,
    # baseline hazards and frozen models for downstream verification.
    # 9. Manifest and completion message
    # -----------------------------------------------------------------------------

    manifest <- tibble::tribble(
      ~file, ~purpose,
      "20_rolling_prediction_archive.csv.gz", "Row-level T10/T20/T30 out-of-sample predictions, including non-risk and non-modelled statuses",
      "20_rolling_validation_summary.csv", "AUC, average precision, Brier score and calibration intercept/slope",
      "20_rolling_calibration_deciles.csv", "Observed-versus-predicted calibration by risk decile",
      "20_rolling_top_area_capture.csv", "Observed event count and area captured by the highest-risk 10%, 20% and 30% of area",
      "20_rolling_model_coefficients.csv", "Rolling-window Cox coefficients",
      "20_rolling_baseline_cumulative_hazard.csv.gz", "Uncentred baseline cumulative hazards for absolute interval probability",
      "20_rolling_training_scalers.csv", "Training-window predictor centres and scales",
      "21_final_model_coefficients.csv", "Final full-record coefficients",
      "21_final_baseline_cumulative_hazard.csv.gz", "Final uncentred baseline cumulative hazards",
      "21_final_training_scalers.csv", "Final predictor centres and scales",
      "21_final_frozen_cox_models.rds", "Frozen final Cox model objects",
      "22_future_Tn_plus_1_prediction_archive.csv.gz", "Optional genuine Tn+1 forecast for the enabled transition models, including DS->AD storage reworking and optional broad eligible-floodplain reactivation"
    )
    write_csv(manifest, file.path(out_dir, "20_prediction_output_manifest.csv"))

    message("Prediction workflow completed. Outputs written to: ", out_dir)
    })
    NULL
  }, error = function(e) {
    msg <- conditionMessage(e)
    failure_path <- file.path(out_dir, "00_PREDICTION_BRANCH_FAILED.txt")
    writeLines(
      c(
        "FRAF v17.10.14.2 PREDICTION BRANCH FAILED",
        paste0("Time: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
        paste0("Reach: ", reach_label),
        paste0("Error: ", msg),
        "Any existing historic outputs and prediction outputs written before failure are retained.",
        "The review-pack stage will still run before the error is re-raised."
      ),
      failure_path, useBytes = TRUE
    )
    warning(
      "[Prediction] Branch failed but execution will continue to review-package assembly: ",
      msg
    )
    msg
  })
} else {
  message("[Mode] Historic-only selected; predictive branch intentionally skipped. Start a new QGIS/R run with AnalysisMode=Prediction only for prediction.")
}

run_complete <- if (isTRUE(run_prediction_mode)) is.null(prediction_error_message) else TRUE
run_marker <- if (run_complete) "00_RUN_COMPLETED.txt" else "00_RUN_INCOMPLETE.txt"
writeLines(
  c(
    paste0("FRAF KM/AG/Cox v17.10.15.1 status: ", ifelse(run_complete, "COMPLETED", "INCOMPLETE")),
    paste0("Time: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
    paste0("Reach: ", reach_label),
    paste0("Analysis mode: ", analysis_mode),
    paste0("Historic interpretive branch: ", ifelse(isTRUE(run_historic_mode), "completed", "skipped by Prediction-only mode")),
    if (isTRUE(run_historic_mode)) paste0("DS->AD interpretive branch: ", ifelse(isTRUE(RunStorageReworkInterpretive), "enabled", "disabled")) else NULL,
    paste0("Prediction branch: ", ifelse(isTRUE(run_prediction_mode), ifelse(run_complete, "completed", "FAILED"), "skipped by Historic-only mode")),
    if (!run_complete) paste0("Prediction error: ", prediction_error_message) else NULL,
    if (isTRUE(run_prediction_mode)) paste0("Broad floodplain prediction requested: ", ifelse(isTRUE(RunBroadFloodplainPrediction), "yes", "no")) else NULL,
    paste0("Outputs written to: ", out_dir)
  ),
  file.path(out_dir, run_marker), useBytes = TRUE
)

mode_marker <- if (isTRUE(run_historic_mode)) {
  "00_HISTORIC_MODE_COMPLETED.txt"
} else if (run_complete) {
  "00_PREDICTION_MODE_COMPLETED.txt"
} else {
  "00_PREDICTION_MODE_INCOMPLETE.txt"
}
writeLines(
  c(
    paste0("FRAF v17.10.15.1 mode status: ", ifelse(run_complete, "COMPLETED", "INCOMPLETE")),
    paste0("Analysis mode: ", analysis_mode),
    paste0("Reach: ", reach_label),
    paste0("Time: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
    paste0("Output directory: ", out_dir)
  ),
  file.path(out_dir, mode_marker), useBytes = TRUE
)

# [FRAF archive / logic boundary]
# Branch-level success markers are distinct from individual model fit status.
if (run_complete) {
  message("FRAF v17.10.14.2 ", analysis_mode, " mode complete for ", reach_label, ". Outputs: ", out_dir)
} else {
  message("FRAF v17.10.14.2 Prediction-only run incomplete; proceeding to failure-safe review-pack assembly.")
}

# >>> FRAF_AUTOMATIC_CHATGPT_REVIEW_PACKAGE_V2 >>>
# [FRAF archive / code note]
# Post-run archive deliberately reads files on disk, allowing useful
# diagnostics to survive even when a prediction fit fails.
# =============================================================================
# [FRAF archive / workflow]
# File-based audit export only: bundle written summaries and selected QA logs
# without refitting models or keeping multi-million-row data in memory.
# FINAL STAGE — automatic ChatGPT review package
# =============================================================================
# This stage does not modify any scientific output. It reads the CSV/TXT/LOG
# outputs already written to out_dir and creates compact thematic bundles in:
#
#   <out_dir>/CHATGPT_REVIEW_PACK/
#
# Upload REVIEW_PRIORITY.txt + REVIEW_00_MANIFEST.txt first. Upload thematic
# bundles only when deeper comparison is required.
# =============================================================================

# [FRAF archive / Review pack function: fraf_review_safe_text]
# Provide size-bounded readback of a text result for compact review artifacts.
fraf_review_safe_text <- function(path, max_lines = 20000L) {
  # Compatibility helper for rare callers. v17.10.12 deliberately caps the
  # materialised text to prevent accidental whole-file duplication in RAM.
  con <- file(path, open = "rt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)
  x <- tryCatch(readLines(con, n = max_lines, warn = FALSE), error = function(e) character(0))
  if (length(x) == 0L) return("[EMPTY OR UNREADABLE FILE]")
  paste(x, collapse = "\n")
}

# [FRAF archive / Review pack function: fraf_review_append_file]
# Append large text outputs to thematic bundles in bounded chunks rather than whole-file reads.
fraf_review_append_file <- function(source_path, bundle_path, chunk_lines = 4000L) {
  # Stream one source file into an already-open review bundle without ever
  # holding the complete source file or complete bundle in memory.
  in_con <- file(source_path, open = "rt", encoding = "UTF-8")
  on.exit(close(in_con), add = TRUE)

  repeat {
    lines <- tryCatch(
      readLines(in_con, n = chunk_lines, warn = FALSE),
      error = function(e) {
        cat(
          paste0("[UNABLE TO READ REMAINDER: ", conditionMessage(e), "]\n"),
          file = bundle_path, append = TRUE
        )
        character(0)
      }
    )
    if (length(lines) == 0L) break
    cat(lines, file = bundle_path, append = TRUE, sep = "\n")
    cat("\n", file = bundle_path, append = TRUE)
  }
  invisible(TRUE)
}

# [FRAF archive / Review pack function: fraf_review_theme]
# Classify analysis outputs into review topics (QA, historic models, prediction, sensitivity).
fraf_review_theme <- function(name) {
  # Prediction and final-model outputs take precedence over numeric prefixes.
  if (
    grepl("^(20|21)_", name, ignore.case = TRUE) ||
    grepl(
      "(rolling_validation|rolling_model|final_model|model_specifications|forecast|prediction|verification|brier|average_precision)",
      name, ignore.case = TRUE
    )
  ) return("05_PREDICTION_VALIDATION")

  # Explicit sensitivity / robustness products.
  if (
    grepl(
      "(sensitivity|strict|pure_state|primary_strict|negative_control|full_vs_union|union_extent|previous_observation)",
      name, ignore.case = TRUE
    )
  ) return("06_SENSITIVITY")

  # Cox / PH outputs.
  if (
    grepl("^08", name, ignore.case = TRUE) ||
    grepl("^09", name, ignore.case = TRUE) ||
    grepl("(cox|proportional.?hazard|PH_)", name, ignore.case = TRUE)
  ) return("04_COX_PH")

  # Spatial organisation.
  if (
    grepl("^04", name, ignore.case = TRUE) ||
    grepl(
      "(event_non_event_distance|spatial_bin|spatial_KM|distance_summary|local_centreline|centreline_.*distance|active_domain_.*distance|landmark_distance|episode_entry_spatial)",
      name, ignore.case = TRUE
    ) ||
    grepl("^00_spatial_", name, ignore.case = TRUE)
  ) return("03_SPATIAL_ORGANISATION")

  # Transition regime / KM / AG / matrices.
  if (
    grepl("^(01|02|03|10|11|12)[A-Za-z0-9_-]*_", name) ||
    grepl(
      "(KM_|AG_|transition_probabilities|transition_matrix|competing_state|first_event_summary)",
      name, ignore.case = TRUE
    )
  ) return("02_TRANSITIONS_KM_AG")

  # Remaining 00_ outputs are core diagnostics/QA.
  if (grepl("^00_", name, ignore.case = TRUE)) {
    return("01_CORE_QA")
  }

  NA_character_
}

# [FRAF archive / Review pack function: fraf_review_priority_rank]
# Identify high-value review artifacts and their recommended inspection order.
fraf_review_priority_rank <- function(name) {
  patterns <- c(
    "00_Run_Incomplete" = "^00_(PREDICTION_BRANCH_FAILED|RUN_INCOMPLETE)\\.txt$",
    "01_Run_Diagnostics" = "^00_run_diagnostics\\.csv$",
    "02_Semantic_QA" = "^00_module3_semantic_anomaly_summary\\.csv$",
    "03_Module3_Module4a_QA" = "^00_module3_vs_module4a_disagreement_summary\\.csv$",
    "04_Temporal_Alignment_QA" = "^00_spatial_temporal_alignment_QA\\.csv$",
    "05_State_Clock_QA" = "^00_state_partition_storage_clock_summary\\.csv$",
    "06_Transition_Matrix_QA" = "^11_state_transition_matrix_eligibility_QA\\.csv$",
    "07_Transition_Probabilities" = "^11_state_transition_probabilities\\.csv$",
    "08_Cox_Summary" = "^08_cox_model_summary\\.csv$",
    "09_Significant_Predictors" = "^08_cox_significant_predictors\\.csv$",
    "10_Primary_Strict_Pure" = "^08s_primary_strict_pure_model_summary\\.csv$",
    "11_Temporal_Sensitivity" = "^08t_previous_observation_temporal_sensitivity\\.csv$",
    "12_PH_All_Models" = "^09_PH_all_models_tests\\.csv$",
    "13_PH_Direction" = "^09_PH_period_direction_summary\\.csv$",
    "14_Model_Specifications" = "^20_model_specifications\\.csv$",
    "15_Rolling_Metadata" = "^20_rolling_model_metadata\\.csv$",
    "16_Rolling_Validation" = "^20_rolling_validation_summary\\.csv$",
    "17_Final_Model_Metadata" = "^21_final_model_metadata\\.csv$",
    "18_Final_Model_Coefficients" = "^21_final_model_coefficients\\.csv$"
  )

  for (nm in names(patterns)) {
    if (grepl(patterns[[nm]], name, ignore.case = TRUE)) return(nm)
  }
  NA_character_
}

# [FRAF archive / code note]
# Review package prioritisation is a reporting utility only and does not
# select events, fit models or amend coefficients.
# [FRAF archive / Review pack function: fraf_build_review_package]
# Construct thematic review bundles, a manifest and completion markers from written results.
fraf_build_review_package <- function(
  output_dir,
  reach = "Unknown",
  max_individual_kb = 2048
) {
  review_dir <- file.path(output_dir, "CHATGPT_REVIEW_PACK")
  dir.create(review_dir, recursive = TRUE, showWarnings = FALSE)

  all_paths <- list.files(
    output_dir,
    full.names = TRUE,
    recursive = FALSE,
    include.dirs = FALSE
  )

  # Do not ingest an earlier review package or non-text/binary analysis products.
  all_paths <- all_paths[
    !grepl("^REVIEW_", basename(all_paths), ignore.case = TRUE)
  ]

  if (length(all_paths) == 0L) {
    warning("[Review package] No top-level outputs found.")
    return(invisible(NULL))
  }

  finfo <- file.info(all_paths)
  manifest <- data.frame(
    reach = reach,
    name = basename(all_paths),
    path = normalizePath(all_paths, winslash = "/", mustWork = FALSE),
    extension = tolower(tools::file_ext(all_paths)),
    size_kb = round(finfo$size / 1024, 1),
    last_modified = format(finfo$mtime, "%Y-%m-%d %H:%M:%S"),
    stringsAsFactors = FALSE
  )

  text_ok <- manifest$extension %in% c("csv", "txt", "tsv", "log", "md")
  manifest$theme <- vapply(
    manifest$name,
    fraf_review_theme,
    character(1)
  )

  # High-volume row-level and sample outputs remain in the normal output folder
  # but are omitted from the upload bundle.
  excluded_pattern <- grepl(
    paste0(
      "(",
      "_QGIS_spotcheck_sample|",
      "_alignment_sample|",
      "fp_condition_QA\\.csv$|",
      "row[_-]?level|",
      "raw[_-]?prediction|",
      "prediction[_-]?rows|",
      "person[_-]?period|",
      "place[_-]?interval[_-]?long|",
      "_coordinates\\.csv$",
      ")"
    ),
    manifest$name,
    ignore.case = TRUE
  )

  canonical <- !is.na(vapply(
    manifest$name,
    fraf_review_priority_rank,
    character(1)
  ))

  manifest$included <- (
    text_ok &
    !is.na(manifest$theme) &
    !excluded_pattern &
    (manifest$size_kb <= max_individual_kb | canonical)
  )

  manifest$reason <- ifelse(
    !text_ok,
    "non-text/binary output",
    ifelse(
      excluded_pattern,
      "row-level/sample/coordinate output excluded",
      ifelse(
        is.na(manifest$theme),
        "no thematic match",
        ifelse(
          manifest$size_kb > max_individual_kb & !canonical,
          paste0("exceeds ", max_individual_kb, " KB review limit"),
          "included"
        )
      )
    )
  )

  utils::write.csv(
    manifest,
    file.path(review_dir, "REVIEW_00_MANIFEST.csv"),
    row.names = FALSE,
    na = ""
  )

  manifest_txt <- c(
    "FRAF CHATGPT REVIEW MANIFEST",
    paste0("Reach: ", reach),
    if (exists("analysis_mode", inherits = TRUE)) paste0("Analysis mode: ", analysis_mode) else NULL,
    paste0("Generated: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
    "",
    paste(
      "name", "size_kb", "included", "theme", "reason",
      sep = "\t"
    ),
    apply(
      manifest[, c("name", "size_kb", "included", "theme", "reason")],
      1,
      function(z) paste(z, collapse = "\t")
    )
  )
  writeLines(
    manifest_txt,
    file.path(review_dir, "REVIEW_00_MANIFEST.txt"),
    useBytes = TRUE
  )

  theme_names <- c(
    "01_CORE_QA",
    "02_TRANSITIONS_KM_AG",
    "03_SPATIAL_ORGANISATION",
    "04_COX_PH",
    "05_PREDICTION_VALIDATION",
    "06_SENSITIVITY"
  )

  bundle_summary <- data.frame(
    theme = character(0),
    files = integer(0),
    size_kb = numeric(0),
    stringsAsFactors = FALSE
  )

  for (th in theme_names) {
    rows <- manifest[
      manifest$included & !is.na(manifest$theme) & manifest$theme == th,
      ,
      drop = FALSE
    ]
    rows <- rows[order(rows$name), , drop = FALSE]

    bundle_path <- file.path(review_dir, paste0("REVIEW_", th, ".txt"))

    header <- c(
      "FRAF THEMATIC REVIEW BUNDLE",
      paste0("Reach: ", reach),
      paste0("Theme: ", th),
      paste0("Generated: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
      paste0("Included files: ", nrow(rows)),
      ""
    )
    writeLines(header, bundle_path, useBytes = TRUE)

    if (nrow(rows) > 0L) {
      for (ii in seq_len(nrow(rows))) {
        p <- rows$path[ii]
        header_block <- c(
          "",
          "============================================================",
          paste0("FILE: ", rows$name[ii]),
          paste0("SIZE_KB: ", rows$size_kb[ii]),
          "============================================================"
        )
        cat(header_block, file = bundle_path, append = TRUE, sep = "\n")
        cat("\n", file = bundle_path, append = TRUE)
        fraf_review_append_file(p, bundle_path)
      }
    }

    bsize <- if (file.exists(bundle_path)) {
      round(file.info(bundle_path)$size / 1024, 1)
    } else 0

    bundle_summary <- rbind(
      bundle_summary,
      data.frame(
        theme = th,
        files = nrow(rows),
        size_kb = bsize,
        stringsAsFactors = FALSE
      )
    )
    invisible(gc(FALSE))
  }

  # Priority bundle: deliberately compact, equivalent high-level outputs across
  # Mamoré and Jamuna for first-pass comparative evaluation.
  priority <- manifest
  priority$priority <- vapply(
    priority$name,
    fraf_review_priority_rank,
    character(1)
  )
  priority$text_ok <- priority$extension %in% c("csv", "txt", "tsv", "log", "md")
  priority <- priority[
    !is.na(priority$priority) & priority$text_ok,
    ,
    drop = FALSE
  ]
  priority <- priority[order(priority$priority, priority$name), , drop = FALSE]

  priority_path <- file.path(review_dir, "REVIEW_PRIORITY.txt")
  writeLines(
    c(
      "FRAF PRIORITY REVIEW BUNDLE",
      paste0("Reach: ", reach),
      paste0("Generated: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
      "Purpose: first-pass Mamoré/Jamuna comparative evaluation.",
      ""
    ),
    priority_path,
    useBytes = TRUE
  )

  if (nrow(priority) > 0L) {
    for (ii in seq_len(nrow(priority))) {
      header_block <- c(
        "",
        "============================================================",
        paste0("SECTION: ", priority$priority[ii]),
        paste0("FILE: ", priority$name[ii]),
        "============================================================"
      )
      cat(header_block, file = priority_path, append = TRUE, sep = "\n")
      cat("\n", file = priority_path, append = TRUE)
      fraf_review_append_file(priority$path[ii], priority_path)
    }
  }

  excluded <- manifest[!manifest$included, , drop = FALSE]
  utils::write.csv(
    excluded,
    file.path(review_dir, "REVIEW_EXCLUDED_FILES.csv"),
    row.names = FALSE,
    na = ""
  )

  utils::write.csv(
    bundle_summary,
    file.path(review_dir, "REVIEW_BUNDLE_SUMMARY.csv"),
    row.names = FALSE,
    na = ""
  )

  guide <- c(
    "FRAF CHATGPT REVIEW-PACK UPLOAD GUIDE",
    paste0("Reach: ", reach),
    "",
    "UPLOAD FIRST:",
    "  REVIEW_PRIORITY.txt",
    "  REVIEW_00_MANIFEST.txt",
    "",
    "FOR DEEPER COMPARISON, UPLOAD THE SAME THEMATIC BUNDLE FROM BOTH RIVERS:",
    "  REVIEW_01_CORE_QA.txt",
    "  REVIEW_02_TRANSITIONS_KM_AG.txt",
    "  REVIEW_03_SPATIAL_ORGANISATION.txt",
    "  REVIEW_04_COX_PH.txt",
    "  REVIEW_05_PREDICTION_VALIDATION.txt",
    "  REVIEW_06_SENSITIVITY.txt",
    "",
    "Large row-level, coordinate and binary outputs remain in the normal R output",
    "folder and are indexed in REVIEW_00_MANIFEST.csv / REVIEW_EXCLUDED_FILES.csv."
  )
  writeLines(
    guide,
    file.path(review_dir, "REVIEW_UPLOAD_GUIDE.txt"),
    useBytes = TRUE
  )

  writeLines(
    c(
      "FRAF CHATGPT REVIEW PACKAGE COMPLETED",
      paste0("Completed: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
      paste0("Reach: ", reach),
      paste0("Source output directory: ", output_dir),
      paste0("Review directory: ", review_dir)
    ),
    file.path(review_dir, "REVIEW_RUN_COMPLETED.txt"),
    useBytes = TRUE
  )

  message(
    "[Review package] Completed: ",
    normalizePath(review_dir, winslash = "/", mustWork = FALSE)
  )
  message("[Review package] Upload first: REVIEW_PRIORITY.txt + REVIEW_00_MANIFEST.txt")

  invisible(manifest)
}

# [FRAF archive / workflow]
# Failure-safe archive: still attempt review-package creation on an incomplete
# prediction run, then surface the model failure as an actual QGIS error.
# Run the review-package stage only after the normal production outputs exist.
# [FRAF archive / logic boundary]
# The review pack reads completed/partial files from disk, avoiding an in-memory
# copy of historic risk tables or full prediction archives.
if (exists("out_dir") && dir.exists(out_dir)) {
  review_reach <- if (exists("reach_label")) {
    as.character(reach_label)[1]
  } else if (exists("reach")) {
    as.character(reach)[1]
  } else {
    "Unknown"
  }

  review_build_error <- tryCatch({
    # v17.10.12: force a full collection before file-based bundling and use a
    # lean 1-MiB non-canonical threshold. Canonical summary files remain eligible
    # regardless of size; large row-level outputs remain in the normal folder.
    invisible(gc(full = TRUE))
    fraf_build_review_package(
      output_dir = out_dir,
      reach = review_reach,
      max_individual_kb = 1024
    )
    NULL
  }, error = function(e) {
    msg <- conditionMessage(e)
    review_dir <- file.path(out_dir, "CHATGPT_REVIEW_PACK")
    dir.create(review_dir, recursive = TRUE, showWarnings = FALSE)
    writeLines(
      c(
        "FRAF REVIEW PACKAGE ASSEMBLY FAILED",
        paste0("Time: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
        paste0("Reach: ", review_reach),
        paste0("Error: ", msg),
        paste0("Source output directory: ", out_dir)
      ),
      file.path(review_dir, "REVIEW_PACK_FAILED.txt"), useBytes = TRUE
    )
    warning("[Review package] Assembly failed: ", msg)
    msg
  })
} else {
  review_build_error <- "out_dir unavailable"
  warning(
    "[Review package] out_dir was not available at final stage; ",
    "scientific outputs are unchanged but no review package was built."
  )
}

# Preserve QGIS failure semantics, but only after the diagnostic review package has
# been assembled from all outputs successfully written before a prediction failure.
if (!is.null(prediction_error_message)) {
  stop(
    "Prediction branch failed: ", prediction_error_message,
    ". CHATGPT_REVIEW_PACK was assembled from the outputs available before failure."
  )
}
# <<< FRAF_AUTOMATIC_CHATGPT_REVIEW_PACKAGE_V2 <<<
