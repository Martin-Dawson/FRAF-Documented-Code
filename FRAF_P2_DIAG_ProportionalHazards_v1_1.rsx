##FRAF Floodplain Reassemblage=group
##Cox PH Model Triage v1.1 - Spatial Sensitivity Integrated=name
##HistoricOutputFolder=folder
##RiskTable=optional file
##RiskLayerName=string Risk Table
##SpatialSensitivityFolder=optional folder
##ReachName=selection Mamoré;Jamuna
##OutputFolder=folder
##PureStateMinSupport=number 0.90
##RunRefits=boolean TRUE
##RunPeriodReruns=boolean TRUE
##PHAlpha=number 0.05
##ExtremeAbsLogHR=number 3
##LargeSE=number 2
##HighCorrelation=number 0.80
##MinEventsPerTerm=number 10
##MinEventsPerPeriod=number 10
# ARCHIVE DOCUMENTATION (comments only)
# Archive file: FRAF_P2_DIAG_ProportionalHazards_v1_1.rsx
# Role: supporting historical-Cox model triage and proportional-hazards (PH)
# diagnostics; not a model-fitting replacement or an independent prediction test.
# Input authority: completed Historic-mode review-pack outputs; optional
# model-specific interval export for diagnostic refitting; optional spatial
# sensitivity v1.5 files for independent spatial robustness evidence.
# The scientific definitions, output names, and processing behavior below
# are unchanged from FRAF_Cox_PH_Model_Triage_v1_1.rsx.
# A model's disposition is a qualitative diagnostic classification; it is
# not a new hypothesis test, a validated PH correction, or a permission to
# substitute a simplified model for the published specification.
# ============================================================
# FRAF Cox / PH Model Triage v1.1
# Companion diagnostic to:
# Floodplain_KM_AG_Cox_STATE_v17.10.10_TWO_MODE_MEMORY_ISOLATED_REVIEW_PACK
#
# PURPOSE
#   Post-process a completed Historic-mode output directory and, when available,
#   refit problematic Cox/PH models using the exact model terms written by the
#   production script. It also reads the authoritative outputs of
#   FRAF_Cox_Spatial_Autocorrelation_Sensitivity_v1_5 and integrates spatial
#   residual dependence, thinning stability, separation and convergence into
#   the final model disposition. This script NEVER changes the scientific
#   specification merely to force convergence. Reduced models are
#   diagnostic/sensitivity fits only.
#
# Preferred data source for refits:
#   08x_cox_interval_PREV_input_table.csv
# written by v17.10.10 Historic mode.
#
# Optional fallback:
#   Stage 4 Step 3 Risk Table (GeoPackage/table). This is used only when the
#   exported 08x interval input table is unavailable. The fallback constructs
#   only model terms whose v17.10.10 transformation recipe is known here.
#
# Main outputs:
#   COX_PH_01_model_inventory.csv
#   COX_PH_02_coefficient_diagnostics.csv
#   COX_PH_03_PH_diagnostics.csv
#   COX_PH_04_event_support.csv
#   COX_PH_05_collinearity.csv
#   COX_PH_06_reduced_model_sequence.csv
#   COX_PH_07_Jamuna_SF_AD_comparison.csv
#   COX_PH_08_DS_SF_separation.csv
#   COX_PH_09_period_refits.csv
#   COX_PH_10_sensitivity_comparison.csv
#   COX_PH_10a_spatial_sensitivity_integration.csv
#   COX_PH_10b_spatial_thinning_term_stability.csv
#   COX_PH_11_MODEL_DISPOSITION.csv
#   COX_PH_12_DISPOSITION_REASONS.csv
#   COX_PH_TRIAGE_REPORT.txt
#
# QGIS Processing header (optional; harmless outside QGIS)
##FRAF Floodplain Reassemblage=group
##Cox PH Model Triage v1.1 - Spatial Sensitivity Integrated=name
##HistoricOutputFolder=folder
##RiskTable=optional file
##RiskLayerName=string Risk Table
##SpatialSensitivityFolder=optional folder
##ReachName=selection Mamoré;Jamuna
##OutputFolder=folder
##PureStateMinSupport=number 0.90
##RunRefits=boolean TRUE
##RunPeriodReruns=boolean TRUE
##PHAlpha=number 0.05
##ExtremeAbsLogHR=number 3.0
##LargeSE=number 2.0
##HighCorrelation=number 0.80
##MinEventsPerTerm=number 10
##MinEventsPerPeriod=number 10
# ============================================================

# Keep strings as text when importing model names, coefficient terms, and
# state-definition labels; factor conversion could alter joins and comparisons.
options(stringsAsFactors = FALSE)

# -----------------------------
# 0. Parameters and packages
# -----------------------------

# QGIS/R Processing exposes input parameters as variables in the execution
# environment. This wrapper supplies explicit defaults for other R contexts.
get_param <- function(nm, default = NULL) {
  if (exists(nm, inherits = TRUE)) get(nm, inherits = TRUE) else default
}

# Resolve GUI parameters and threshold controls. The PH significance level and
# coefficient/SE cutoffs govern flags, not the underlying production models.
# RunRefits and RunPeriodReruns independently control optional diagnostic fits.
HistoricOutputFolder <- as.character(get_param("HistoricOutputFolder", ""))[1]
RiskTable <- get_param("RiskTable", NULL)
RiskLayerName <- as.character(get_param("RiskLayerName", "Risk Table"))[1]
SpatialSensitivityFolder <- as.character(get_param("SpatialSensitivityFolder", ""))[1]
ReachName <- get_param("ReachName", NA)
OutputFolder <- as.character(get_param("OutputFolder", ""))[1]
PureStateMinSupport <- suppressWarnings(as.numeric(get_param("PureStateMinSupport", 0.90))[1])
RunRefits <- isTRUE(as.logical(get_param("RunRefits", TRUE))[1])
RunPeriodReruns <- isTRUE(as.logical(get_param("RunPeriodReruns", TRUE))[1])
PHAlpha <- suppressWarnings(as.numeric(get_param("PHAlpha", 0.05))[1])
ExtremeAbsLogHR <- suppressWarnings(as.numeric(get_param("ExtremeAbsLogHR", 3.0))[1])
LargeSE <- suppressWarnings(as.numeric(get_param("LargeSE", 2.0))[1])
HighCorrelation <- suppressWarnings(as.numeric(get_param("HighCorrelation", 0.80))[1])
MinEventsPerTerm <- suppressWarnings(as.integer(get_param("MinEventsPerTerm", 10))[1])
MinEventsPerPeriod <- suppressWarnings(as.integer(get_param("MinEventsPerPeriod", 10))[1])

# Reject missing or out-of-range threshold inputs and retain conservative
# script defaults. These checks do not alter production-model estimates.
if (!is.finite(PureStateMinSupport)) PureStateMinSupport <- 0.90
if (!is.finite(PHAlpha) || PHAlpha <= 0 || PHAlpha >= 1) PHAlpha <- 0.05
if (!is.finite(ExtremeAbsLogHR) || ExtremeAbsLogHR <= 0) ExtremeAbsLogHR <- 3.0
if (!is.finite(LargeSE) || LargeSE <= 0) LargeSE <- 2.0
if (!is.finite(HighCorrelation) || HighCorrelation <= 0 || HighCorrelation >= 1) HighCorrelation <- 0.80
if (!is.finite(MinEventsPerTerm) || MinEventsPerTerm < 1) MinEventsPerTerm <- 10L
if (!is.finite(MinEventsPerPeriod) || MinEventsPerPeriod < 1) MinEventsPerPeriod <- 10L

# survival supplies counting-process Cox fits and robust clustered covariance;
# broom formats fitted terms. sf is loaded only for a GeoPackage fallback.
required_pkgs <- c("survival", "broom")
missing_pkgs <- required_pkgs[!vapply(required_pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_pkgs)) stop("Missing required R package(s): ", paste(missing_pkgs, collapse = ", "))

# The completed historic output directory is compulsory. The output directory
# is deliberately separate and can be placed under the historic run by default.
if (!nzchar(HistoricOutputFolder) || !dir.exists(HistoricOutputFolder)) {
  stop("HistoricOutputFolder does not exist: ", HistoricOutputFolder)
}
historic_dir <- normalizePath(HistoricOutputFolder, winslash = "/", mustWork = TRUE)

if (!nzchar(OutputFolder)) OutputFolder <- file.path(historic_dir, "COX_PH_TRIAGE")
dir.create(OutputFolder, recursive = TRUE, showWarnings = FALSE)
out_dir <- normalizePath(OutputFolder, winslash = "/", mustWork = TRUE)

# Convert QGIS selection indices or typed reach labels to a stable river name.
# The selection order is Mamore (index 0), Jamuna (index 1); only Jamuna
# triggers the reach-specific SF->AD comparison table.
resolve_reach <- function(x) {
  if (length(x) == 0 || is.null(x) || is.na(x[1])) return(NA_character_)
  idx <- suppressWarnings(as.integer(x[1]))
  if (is.finite(idx)) return(ifelse(idx == 1L, "Jamuna", "Mamoré"))
  txt <- tolower(trimws(as.character(x[1])))
  if (grepl("jamuna", txt, fixed = TRUE)) "Jamuna" else if (grepl("mam", txt)) "Mamoré" else as.character(x[1])
}
reach_label <- resolve_reach(ReachName)

# Write reproducible diagnostic CSV files into the dedicated triage directory;
# keep original column labels and represent R missing values as empty cells.
wcsv <- function(x, fn) {
  utils::write.csv(as.data.frame(x), file.path(out_dir, fn), row.names = FALSE, na = "", fileEncoding = "UTF-8")
}
# Read one named historic-run CSV. Required files stop the diagnostic if absent;
# optional files are allowed to be absent and result in unavailable diagnostics.
rcsv <- function(fn, required = FALSE) {
  p <- file.path(historic_dir, fn)
  if (!file.exists(p)) {
    if (required) stop("Required Historic output missing: ", p)
    return(NULL)
  }
  tryCatch(utils::read.csv(p, check.names = FALSE, stringsAsFactors = FALSE),
           error = function(e) {
             if (required) stop("Could not read ", p, ": ", conditionMessage(e))
             NULL
           })
}
# Construct zero-row outputs with a defined schema so optional diagnostics can
# still write machine-readable files when no comparable evidence exists.
empty_df <- function(...) data.frame(..., stringsAsFactors = FALSE)

message("FRAF Cox/PH Model Triage v1.1")
message("Historic outputs: ", historic_dir)
message("Triage outputs: ", out_dir)

# Prefer an explicitly supplied spatial-sensitivity directory. If absent,
# probe conventional subdirectories or the historic folder itself; discovery
# is only a convenience, not evidence that the matching v1.5 run succeeded.
spatial_dir <- NA_character_
if (nzchar(SpatialSensitivityFolder) && dir.exists(SpatialSensitivityFolder)) {
  spatial_dir <- normalizePath(SpatialSensitivityFolder, winslash = "/", mustWork = TRUE)
} else {
  # Convenience discovery only. Exact v1.5 filenames are still required.
  candidates <- c(
    file.path(historic_dir, "SPATIAL_SENSITIVITY"),
    file.path(historic_dir, "Spatial Sensitivity"),
    file.path(historic_dir, "Spatial_Sensitivity"),
    historic_dir
  )
  required_spatial_probe <- "11_spatial_dependence_overall_summary.csv"
  hit <- candidates[file.exists(file.path(candidates, required_spatial_probe))]
  if (length(hit)) spatial_dir <- normalizePath(hit[1], winslash = "/", mustWork = TRUE)
}
if (is.na(spatial_dir)) {
  message("[Spatial sensitivity] v1.5 output directory not supplied/found. ",
          "Spatial disposition criteria will be recorded as unavailable.")
} else {
  message("[Spatial sensitivity] Reading v1.5 outputs from: ", spatial_dir)
}

# -----------------------------
# 0a. Spatial-sensitivity v1.5 integration
# -----------------------------

# Read exact v1.5 spatial-sensitivity filenames without guessing replacements.
# Missing auxiliary files remain optional, although disposition-level spatial
# evidence requires the aligned overall summary.
read_spatial_csv <- function(fn) {
  if (is.na(spatial_dir)) return(NULL)
  p <- file.path(spatial_dir, fn)
  if (!file.exists(p)) return(NULL)
  tryCatch(utils::read.csv(p, check.names = FALSE, stringsAsFactors = FALSE),
           error = function(e) {
             warning("Could not read spatial sensitivity file ", p, ": ", conditionMessage(e))
             NULL
           })
}

# Load complementary spatial diagnostics: baseline coefficients, Moran-residual
# summaries, cluster and spacing evidence, convergence/separation audits, and
# thinning robustness. Not all loaded tables enter the final disposition rule.
spatial_specs <- read_spatial_csv("00_spatial_sensitivity_model_specifications.csv")
spatial_baseline <- read_spatial_csv("01_baseline_cox_coefficients.csv")
spatial_diag_coef <- read_spatial_csv("01a_spatial_diagnostic_cox_coefficients.csv")
spatial_thin_ref <- read_spatial_csv("01b_thinning_reference_150m_coefficients.csv")
spatial_jamuna_audit <- read_spatial_csv("01c_jamuna_reactivation_diagnostic_model_audit.csv")
spatial_diag_selection <- read_spatial_csv("01d_spatial_diagnostic_model_selection_summary.csv")
spatial_moran <- read_spatial_csv("03_residual_moran_summary.csv")
spatial_clusters <- read_spatial_csv("05_event_cluster_summary_by_interval.csv")
spatial_spacing <- read_spatial_csv("06b_nominal_vs_actual_thinning_spacing.csv")
spatial_sep_audit <- read_spatial_csv("07b_cox_convergence_separation_audit.csv")
spatial_flagged_sep <- read_spatial_csv("07c_cox_flagged_separation_terms.csv")
spatial_thin_stability <- read_spatial_csv("08_thinning_coefficient_stability_summary.csv")
spatial_direction_only <- read_spatial_csv("08b_direction_only_separation_terms.csv")
spatial_overall <- read_spatial_csv("11_spatial_dependence_overall_summary.csv")

# A directory or partial CSV collection alone does not establish usable spatial
# evidence; require a nonempty model-level overall summary.
spatial_available <- !is.null(spatial_overall) && nrow(spatial_overall) > 0L

# Validate that supplied outputs are the aligned v1.5 interface.
# Check the production-model and model-scope schema before attaching spatial
# evidence to a Cox fit. Legacy summaries cannot silently be treated as v1.5.
spatial_alignment_status <- if (!spatial_available) {
  "not_available"
} else if (all(c("production_model", "model_scope") %in% names(spatial_overall))) {
  "v1.5_aligned_interface"
} else {
  "legacy_or_unverified_interface"
}

if (spatial_available && spatial_alignment_status != "v1.5_aligned_interface") {
  warning("Spatial sensitivity outputs were found, but production_model/model_scope ",
          "are absent from 11_spatial_dependence_overall_summary.csv. ",
          "They will not be treated as authoritative v1.5 evidence.")
  spatial_available <- FALSE
}

# Map v1.5 output names directly to production model names. Never infer from
# transition labels when production_model is supplied.
# Normalise model identifiers in auxiliary spatial tables. The explicit
# production_model identifier is authoritative whenever present; the fallback
# alias map is used only by older supplementary files.
normalise_spatial_model <- function(d) {
  if (is.null(d) || !nrow(d)) return(d)
  if (!"production_model" %in% names(d) && "model" %in% names(d)) {
    # Only for older auxiliary files. Main disposition requires v1.5 overall file.
    mp <- c(
      reactivation = "active_domain_reactivation",
      storage_formation_full_event = "depositional_storage_full_event",
      storage_formation_local_position_subset = "depositional_storage_local_position_subset",
      stabilisation = "floodplain_stabilisation",
      storage_reworking = "depositional_storage_reworking"
    )
    d$production_model <- unname(mp[as.character(d$model)])
  }
  d
}
# Apply a common production-model key before later term-level and model-level
# lookups, avoiding joins based solely on broad transition labels.
spatial_baseline <- normalise_spatial_model(spatial_baseline)
spatial_diag_coef <- normalise_spatial_model(spatial_diag_coef)
spatial_thin_ref <- normalise_spatial_model(spatial_thin_ref)
spatial_diag_selection <- normalise_spatial_model(spatial_diag_selection)
spatial_moran <- normalise_spatial_model(spatial_moran)
spatial_clusters <- normalise_spatial_model(spatial_clusters)
spatial_sep_audit <- normalise_spatial_model(spatial_sep_audit)
spatial_flagged_sep <- normalise_spatial_model(spatial_flagged_sep)
spatial_thin_stability <- normalise_spatial_model(spatial_thin_stability)
spatial_direction_only <- normalise_spatial_model(spatial_direction_only)

# Model-level spatial evidence table used by final disposition.
# Build the per-production-model spatial-evidence lookup used for disposition.
# This is a diagnostic synthesis, not a second or pooled Cox fit.
if (spatial_available) {
  spatial_model_evidence <- spatial_overall
  spatial_model_evidence$model <- as.character(spatial_model_evidence$production_model)

  # Clean logical/numeric coercions.
  # Coerce only recognised numeric columns; preserve unknown v1.5 columns for
  # traceability and avoid coercing model names or scope labels.
  num_cols <- intersect(c(
    "baseline_events", "baseline_concordance",
    "descriptive_residual_correlation_extent_m",
    "mean_principal_quantitative_thinning_direction_stability",
    "mean_direction_only_term_thinning_direction_stability",
    "mean_thinning_separation_flag_rate"
  ), names(spatial_model_evidence))
  for (nm in num_cols) spatial_model_evidence[[nm]] <- suppressWarnings(as.numeric(spatial_model_evidence[[nm]]))

  if ("baseline_any_separation_flag" %in% names(spatial_model_evidence)) {
    spatial_model_evidence$baseline_any_separation_flag <-
      as.logical(spatial_model_evidence$baseline_any_separation_flag)
  }

  # Convergence of the selected spatial diagnostic model.
  # The selected spatial diagnostic fit can indicate whether instability is
  # confined to the baseline fit, but does not replace the production coefficients.
  spatial_model_evidence$spatial_diagnostic_clean_convergence <- NA
  spatial_model_evidence$spatial_diagnostic_source <- NA_character_
  if (!is.null(spatial_diag_selection) && nrow(spatial_diag_selection) &&
      all(c("production_model", "spatial_diagnostic_clean_convergence") %in% names(spatial_diag_selection))) {
    ii <- match(spatial_model_evidence$production_model, spatial_diag_selection$production_model)
    spatial_model_evidence$spatial_diagnostic_clean_convergence <-
      as.logical(spatial_diag_selection$spatial_diagnostic_clean_convergence[ii])
    if ("spatial_diagnostic_source" %in% names(spatial_diag_selection)) {
      spatial_model_evidence$spatial_diagnostic_source <-
        as.character(spatial_diag_selection$spatial_diagnostic_source[ii])
    }
  }

  # Quantitative principal-term thinning stability: use the weakest observed
  # direction stability and largest median |delta beta| across thinning scales.
  # For principal quantitative terms, use the least favourable direction-retention
  # proportion and largest absolute median beta shift across available thinning
  # scales. Direction-only separation terms do not supply quantitative beta shifts.
  spatial_model_evidence$spatial_min_direction_stability <- NA_real_
  spatial_model_evidence$spatial_max_abs_median_delta_beta <- NA_real_
  spatial_model_evidence$spatial_principal_terms_tested <- NA_integer_
  if (!is.null(spatial_thin_stability) && nrow(spatial_thin_stability)) {
    for (i in seq_len(nrow(spatial_model_evidence))) {
      pm <- spatial_model_evidence$production_model[i]
      z <- spatial_thin_stability[
        as.character(spatial_thin_stability$production_model) == pm &
        as.character(spatial_thin_stability$predictor_role) == "PRINCIPAL" &
        as.character(spatial_thin_stability$stability_interpretation) == "QUANTITATIVE",
        , drop = FALSE
      ]
      if (nrow(z)) {
        ds <- suppressWarnings(as.numeric(z$proportion_same_direction))
        db <- suppressWarnings(as.numeric(z$median_delta_beta))
        spatial_model_evidence$spatial_min_direction_stability[i] <-
          if (any(is.finite(ds))) min(ds[is.finite(ds)]) else NA_real_
        spatial_model_evidence$spatial_max_abs_median_delta_beta[i] <-
          if (any(is.finite(db))) max(abs(db[is.finite(db)])) else NA_real_
        spatial_model_evidence$spatial_principal_terms_tested[i] <-
          length(unique(as.character(z$term)))
      }
    }
  }

  # Separation frequency from complete convergence/separation audit.
  # Preserve evidence of separation encountered in spatial sensitivity refits;
  # this prompts caution independent of the conventional PH test.
  spatial_model_evidence$spatial_any_flagged_separation <- FALSE
  if (!is.null(spatial_flagged_sep) && nrow(spatial_flagged_sep) &&
      "production_model" %in% names(spatial_flagged_sep)) {
    spatial_model_evidence$spatial_any_flagged_separation <-
      spatial_model_evidence$production_model %in% unique(as.character(spatial_flagged_sep$production_model))
  }

  spatial_model_evidence$spatial_evidence_available <- TRUE
} else {
  spatial_model_evidence <- empty_df(
    model = character(),
    production_model = character(),
    model_scope = character(),
    spatial_evidence_available = logical()
  )
}

# Export the spatial evidence even when optional inputs were missing; a separate
# term-stability export allows an audit of the model-level minimum/maximum rule.
wcsv(spatial_model_evidence, "COX_PH_10a_spatial_sensitivity_integration.csv")
if (!is.null(spatial_thin_stability) && nrow(spatial_thin_stability)) {
  wcsv(spatial_thin_stability, "COX_PH_10b_spatial_thinning_term_stability.csv")
} else {
  wcsv(empty_df(), "COX_PH_10b_spatial_thinning_term_stability.csv")
}

# -----------------------------
# 1. Production-model metadata
# -----------------------------

# Load production model status, exact selected terms, and companion diagnostic
# outputs. The model inventory is anchored to historic-run names rather than
# reconstructing which predictors should have been in each original fit.
model_summary <- rcsv("08_cox_model_summary.csv", required = TRUE)
terms_used <- rcsv("08_cox_terms_used.csv", required = TRUE)
spatial_framework <- rcsv("08_spatial_predictor_framework.csv")
definition_summary <- rcsv("08s_primary_strict_pure_model_summary.csv")
definition_coef <- rcsv("08s_primary_strict_pure_coefficients.csv")
ph_all <- rcsv("09_PH_all_models_tests.csv")
ph_period_summary <- rcsv("09_PH_period_model_summary.csv")
ph_period_hr <- rcsv("09_PH_period_specific_spatial_HR.csv")
ph_direction <- rcsv("09_PH_period_direction_summary.csv")
ph_interactions <- rcsv("09_PH_spatial_period_interaction_tests.csv")
complete_case <- rcsv("08_complete_case_filtering_counts.csv")

# v17.10.10 model naming aliases.
# Explicitly map historic filenames to transitions and definition populations:
# SF->AD, AD->DS (full and local subset), DS->SF, DS->AD, and aggregate transitions.
# The initial-floodplain reactivation model is distinct from the SF->AD model;
# strict and pure-state definitions are sensitivity populations, not new states.
model_alias <- data.frame(
  model = c(
    "active_domain_reactivation",
    "initial_floodplain_reactivation",
    "depositional_storage_full_event",
    "depositional_storage_local_position_subset",
    "floodplain_stabilisation",
    "depositional_storage_reworking",
    "any_named_primary_transition",
    "state_only_active_domain_reactivation",
    "state_only_depositional_storage_full_event",
    "state_only_depositional_storage_local_position_subset",
    "state_only_floodplain_stabilisation",
    "state_only_depositional_storage_reworking",
    "state_only_any_state_transition",
    "state_only_any_transition",
    "pure_state_active_domain_reactivation",
    "pure_state_depositional_storage_full_event",
    "pure_state_depositional_storage_local_position_subset",
    "pure_state_floodplain_stabilisation",
    "pure_state_depositional_storage_reworking",
    "pure_state_any_state_transition",
    "pure_state_any_transition"
  ),
  transition_group = c(
    "SF_AD","INITIAL_FP_AD","AD_DS","AD_DS_LOCAL","DS_SF","DS_AD","ANY",
    "SF_AD","AD_DS","AD_DS_LOCAL","DS_SF","DS_AD","ANY","ANY",
    "SF_AD","AD_DS","AD_DS_LOCAL","DS_SF","DS_AD","ANY","ANY"
  ),
  definition = c(
    "primary","first_event","primary","primary","primary","primary","primary",
    "strict","strict","strict","strict","strict","strict","strict",
    "pure_state","pure_state","pure_state","pure_state","pure_state","pure_state","pure_state"
  ),
  stringsAsFactors = FALSE
)

# Preserve the analytical distinction between full-event storage formation,
# local-geometry subsets, and complete transition-specific risk sets.
model_scope_from_name <- function(m) {
  if (grepl("local_position", m)) return("local_geometry_subset")
  if (grepl("depositional_storage_full_event", m)) return("full_event")
  "full_risk_set"
}

model_summary$model <- as.character(model_summary$model)
# The model inventory combines production fit metadata, ontology labels,
# spatial framework descriptors, and count of terms actually selected.
inventory <- merge(model_summary, model_alias, by = "model", all.x = TRUE)
inventory$model_scope_triage <- vapply(inventory$model, model_scope_from_name, character(1))
inventory$reach <- reach_label
if (!is.null(spatial_framework) && all(c("model","spatial_framework") %in% names(spatial_framework))) {
  sf_keep <- spatial_framework[, intersect(c("model","model_scope","spatial_framework","spatial_terms","predictor_time_basis"), names(spatial_framework)), drop=FALSE]
  inventory <- merge(inventory, sf_keep, by = "model", all.x = TRUE, suffixes = c("", "_production"))
}

if ("model" %in% names(terms_used)) {
  term_counts <- aggregate(term ~ model, terms_used, function(x) sum(!is.na(x) & nzchar(as.character(x))))
  names(term_counts)[2] <- "n_terms"
  inventory <- merge(inventory, term_counts, by = "model", all.x = TRUE)
}

# -----------------------------
# 2. Existing coefficient files
# -----------------------------

# Production coefficient filenames are version-specific. Select the first file
# matching each anchored regular expression; do not merge coefficients across
# ambiguous candidate files without checking the archive manifest.
prefix_map <- data.frame(
  model = c(
    "active_domain_reactivation",
    "initial_floodplain_reactivation",
    "depositional_storage_full_event",
    "depositional_storage_local_position_subset",
    "floodplain_stabilisation",
    "depositional_storage_reworking",
    "any_named_primary_transition",
    "state_only_active_domain_reactivation",
    "state_only_depositional_storage_full_event",
    "state_only_depositional_storage_local_position_subset",
    "state_only_floodplain_stabilisation",
    "state_only_depositional_storage_reworking",
    "state_only_any_state_transition",
    "pure_state_active_domain_reactivation",
    "pure_state_depositional_storage_full_event",
    "pure_state_depositional_storage_local_position_subset",
    "pure_state_floodplain_stabilisation",
    "pure_state_depositional_storage_reworking",
    "pure_state_any_state_transition"
  ),
  prefix_pattern = c(
    "^08_cox_active_domain_reactivation_interval_PREV_model\\.csv$",
    "^08a_cox_initial_floodplain_reactivation_interval_PREV_model\\.csv$",
    "^08b_cox_depositional_storage_interval_PREV_model\\.csv$",
    "^08bl_cox_depositional_storage_local_position_interval_PREV_model\\.csv$",
    "^08c_cox_floodplain_stabilisation_interval_PREV_model\\.csv$",
    "^08d_cox_depositional_storage_reworking_interval_PREV_model\\.csv$",
    "^08e_cox_any.*model\\.csv$",
    "^08.*state_only.*active_domain_reactivation.*model\\.csv$",
    "^08.*state_only.*depositional_storage.*full.*model\\.csv$",
    "^08.*state_only.*depositional_storage.*local.*model\\.csv$",
    "^08.*state_only.*floodplain_stabilisation.*model\\.csv$",
    "^08.*state_only.*storage.*rework.*model\\.csv$",
    "^08.*state_only.*any.*model\\.csv$",
    "^08.*pure_state.*active_domain_reactivation.*model\\.csv$",
    "^08.*pure_state.*depositional_storage.*full.*model\\.csv$",
    "^08.*pure_state.*depositional_storage.*local.*model\\.csv$",
    "^08.*pure_state.*floodplain_stabilisation.*model\\.csv$",
    "^08.*pure_state.*storage.*rework.*model\\.csv$",
    "^08.*pure_state.*any.*model\\.csv$"
  ),
  stringsAsFactors = FALSE
)

all_hist_files <- basename(list.files(historic_dir, full.names = FALSE))
# Read the coefficient table for a particular historic model, retain its source
# filename for provenance, and skip missing/unreadable or term-less tables.
read_model_coef <- function(model, pattern) {
  hits <- all_hist_files[grepl(pattern, all_hist_files, ignore.case = TRUE)]
  if (!length(hits)) return(NULL)
  f <- file.path(historic_dir, hits[1])
  d <- tryCatch(utils::read.csv(f, check.names = FALSE), error = function(e) NULL)
  if (is.null(d) || !"term" %in% names(d)) return(NULL)
  d$model <- model
  d$source_file <- hits[1]
  d
}
# Assemble coefficient rows across all available primary and definition-
# sensitivity fits; subsequent diagnostics tolerate an empty collection.
coef_list <- Map(read_model_coef, prefix_map$model, prefix_map$prefix_pattern)
coefficients_existing <- do.call(rbind, coef_list[!vapply(coef_list, is.null, logical(1))])

# Sensitivity coefficient table is authoritative for strict/pure-state definitions,
# and can also fill primary models if per-model files were not found.
# Use the consolidated strict/pure-state coefficient file as authoritative for
# those definitions. Supplement missing primary combinations without overwriting
# an already discovered model-term row from its own historic-run file.
if (!is.null(definition_coef) && nrow(definition_coef)) {
  sens <- definition_coef
  sens$model <- NA_character_
  if (all(c("definition","transition") %in% names(sens))) {
    # Map human-readable transition, state-definition and local/full scope labels
    # to the exact model identifiers used elsewhere in the archive.
    map_transition <- function(tr, defn, scope) {
      tg <- if (grepl("Stabilised floodplain.*Active", tr, ignore.case=TRUE)) "SF_AD" else
            if (grepl("Active.*Depositional storage", tr, ignore.case=TRUE)) "AD_DS" else
            if (grepl("Depositional storage.*Stabil", tr, ignore.case=TRUE)) "DS_SF" else
            if (grepl("Depositional storage.*Active", tr, ignore.case=TRUE)) "DS_AD" else
            if (grepl("Any", tr, ignore.case=TRUE)) "ANY" else NA_character_
      dd <- if (grepl("strict", defn, ignore.case=TRUE)) "strict" else
            if (grepl("pure", defn, ignore.case=TRUE)) "pure_state" else "primary"
      sc <- if (!is.na(scope) && grepl("local", scope, ignore.case=TRUE)) "local" else "full"
      candidates <- model_alias$model[model_alias$transition_group %in% c(tg, paste0(tg,"_LOCAL")) & model_alias$definition == dd]
      if (tg == "AD_DS" && sc == "local") candidates <- candidates[grepl("local", candidates)]
      if (tg == "AD_DS" && sc == "full") candidates <- candidates[!grepl("local", candidates)]
      if (!length(candidates)) return(NA_character_)
      candidates[1]
    }
    scope_col <- if ("model_scope" %in% names(sens)) sens$model_scope else rep("principal_full_event", nrow(sens))
    sens$model <- mapply(map_transition, sens$transition, sens$definition, scope_col, USE.NAMES=FALSE)
  }
  sens$source_file <- "08s_primary_strict_pure_coefficients.csv"
  sens <- sens[!is.na(sens$model),,drop=FALSE]
  common <- intersect(names(coefficients_existing), names(sens))
  if (is.null(coefficients_existing) || !nrow(coefficients_existing)) {
    coefficients_existing <- sens
  } else if (length(common)) {
    # Add only model-term combinations not already present.
    key_old <- paste(coefficients_existing$model, coefficients_existing$term)
    key_new <- paste(sens$model, sens$term)
    add <- sens[!key_new %in% key_old,,drop=FALSE]
    all_cols <- union(names(coefficients_existing), names(add))
    for (nm in setdiff(all_cols,names(coefficients_existing))) coefficients_existing[[nm]] <- NA
    for (nm in setdiff(all_cols,names(add))) add[[nm]] <- NA
    coefficients_existing <- rbind(coefficients_existing[,all_cols], add[,all_cols])
  }
}

if (is.null(coefficients_existing)) coefficients_existing <- empty_df(model=character(), term=character())

# Harmonise tidy columns: v17.10.10 exponentiated estimate = HR.
# Historic coefficient tables are expected to contain exponentiated estimates:
# estimate is interpreted here as a hazard ratio (HR), not log(HR).
# log_HR, standard error, CI ratio and diagnostic flags are derived from it.
# If an input producer changes coefficient conventions, this mapping requires
# revalidation rather than reinterpretation of the exported numbers.
for (nm in c("estimate","std.error","statistic","p.value","conf.low","conf.high")) {
  if (!nm %in% names(coefficients_existing)) coefficients_existing[[nm]] <- NA_real_
}
coefficients_existing$HR <- suppressWarnings(as.numeric(coefficients_existing$estimate))
coefficients_existing$log_HR <- ifelse(is.finite(coefficients_existing$HR) & coefficients_existing$HR > 0,
                                       log(coefficients_existing$HR), NA_real_)
coefficients_existing$SE <- suppressWarnings(as.numeric(coefficients_existing$std.error))
coefficients_existing$CI_ratio <- with(coefficients_existing,
  ifelse(is.finite(conf.low) & conf.low > 0 & is.finite(conf.high), conf.high/conf.low, NA_real_))
# Flag non-finite HR/SE/confidence limits, extreme |log(HR)|, large SE, and
# very wide confidence intervals. These are estimation warnings; they are not
# independent evidence that a geomorphic mechanism is absent.
coefficients_existing$flag_nonfinite <- !is.finite(coefficients_existing$HR) |
  !is.finite(coefficients_existing$SE) |
  !is.finite(coefficients_existing$conf.low) |
  !is.finite(coefficients_existing$conf.high)
coefficients_existing$flag_extreme <- is.finite(coefficients_existing$log_HR) &
  abs(coefficients_existing$log_HR) >= ExtremeAbsLogHR
coefficients_existing$flag_large_se <- is.finite(coefficients_existing$SE) & coefficients_existing$SE >= LargeSE
coefficients_existing$flag_wide_ci <- is.finite(coefficients_existing$CI_ratio) & coefficients_existing$CI_ratio >= exp(2*1.96*LargeSE)
wcsv(coefficients_existing, "COX_PH_02_coefficient_diagnostics.csv")

# -----------------------------
# 3. Parse PH outputs
# -----------------------------

# Normalise existing production PH-test output (typically Schoenfeld-residual
# based) into model, term, p-value, global-test and violation indicators.
# This script READS prior PH tests; it does not run a fresh cox.zph analysis
# for every production fit.
normalise_ph <- function(ph) {
  if (is.null(ph) || !nrow(ph)) return(empty_df())
  out <- ph
  pcol <- intersect(c("p.value","p","p_value","P"), names(out))
  if (length(pcol)) out$ph_p <- suppressWarnings(as.numeric(out[[pcol[1]]])) else out$ph_p <- NA_real_
  termcol <- intersect(c("term","variable","rowname","predictor"), names(out))
  if (length(termcol)) out$ph_term <- as.character(out[[termcol[1]]]) else out$ph_term <- NA_character_
  if (!"model" %in% names(out)) out$model <- NA_character_
  out$is_global <- toupper(trimws(out$ph_term)) == "GLOBAL"
  out$ph_violation <- is.finite(out$ph_p) & out$ph_p < PHAlpha
  out
}
# A significant global or term-level PH test flags non-proportionality over the
# observed record. Such failure constrains coefficient interpretation but does
# not automatically invalidate held-out predictive performance.
ph_diag <- normalise_ph(ph_all)
if (nrow(ph_diag)) wcsv(ph_diag, "COX_PH_03_PH_diagnostics.csv") else
  wcsv(empty_df(model=character(), ph_term=character(), ph_p=numeric(), is_global=logical(), ph_violation=logical()),
       "COX_PH_03_PH_diagnostics.csv")

# -----------------------------
# 4. Obtain model-level interval data
# -----------------------------

# Prefer the exported, model-ready interval data so the diagnostic refits retain
# production transformations. Loading the full file may be memory intensive;
# RiskTable reconstruction below is a less secure, optional fallback.
input_table_path <- file.path(historic_dir, "08x_cox_interval_PREV_input_table.csv")
cox_input <- NULL
input_source <- NA_character_

if (file.exists(input_table_path)) {
  message("Reading v17.10.10 exported Cox interval input table.")
  cox_input <- utils::read.csv(input_table_path, check.names = FALSE, stringsAsFactors = FALSE)
  input_source <- "08x_cox_interval_PREV_input_table.csv"
}

# Read an optional fallback as CSV or a named GeoPackage layer. Drop geometry
# before model diagnostics; sf is only needed for the spatial-file input format.
# The fallback does not recreate unexported modelling filters by itself.
read_risk_table <- function(x, layer) {
  if (is.null(x) || length(x) == 0L) return(NULL)
  p <- as.character(x)[1]
  if (!nzchar(p)) return(NULL)
  if (grepl("\\.csv$", p, ignore.case=TRUE)) return(utils::read.csv(p, check.names=FALSE))
  if (grepl("\\.gpkg", p, ignore.case=TRUE)) {
    if (!requireNamespace("sf", quietly=TRUE)) stop("Package sf required to read RiskTable GeoPackage fallback.")
    p0 <- sub("\\|.*$", "", p)
    lyr <- layer
    if (grepl("\\|layername=", p, ignore.case=TRUE)) lyr <- sub(".*\\|layername=", "", p, ignore.case=TRUE)
    obj <- suppressWarnings(sf::st_read(p0, layer=lyr, quiet=TRUE, options="LIST_ALL_TABLES=YES"))
    if (inherits(obj,"sf")) obj <- sf::st_drop_geometry(obj)
    return(as.data.frame(obj))
  }
  stop("Unsupported RiskTable fallback type: ", p)
}

# v17.10.10 transformation recipe, used only when 08x export is absent.
# Explicit fallback predictor recipe for selected production terms. PREV fields
# are antecedent histories; current distance fields are converted by log1p(km)
# and within-loaded-data z-scoring. This is a fallback approximation when the
# exact exported table is absent: parameter centring, risk eligibility and
# missing terms must be checked before interpreting fallback refits as comparable.
recipe <- list(
  ASM_DOM_RATIO_PREV_Z=c("ASM_DOM_RATIO_PREV","z"),
  ASM_N_EPISODES_PREV_Z=c("ASM_N_EPISODES_PREV","z"),
  ASM_MAX_QUIET_PREV_Z=c("ASM_MAX_QUIET_PREV","z"),
  ASM_COV_FRAC_Z=c("ASM_COV_FRAC","z"),
  ASM_N_REACTIVATE_PREV_Z=c("ASM_N_REACTIVATE_PREV","z"),
  ASM_STORAGE_FRAC_PREV_Z=c("ASM_STORAGE_FRAC_PREV","z"),
  ASM_N_STORAGE_EVT_PREV_Z=c("ASM_N_STORAGE_EVT_PREV","z"),
  ASM_STAB_FP_FRAC_PREV_Z=c("ASM_STAB_FP_FRAC_PREV","z"),
  ASM_QUIET_SINCE_PREV_Z=c("ASM_QUIET_SINCE_PREV","z"),
  ASM_N_STABILISE_PREV_Z=c("ASM_N_STABILISE_PREV","z"),
  DIST_ACTIVE_CURR_LOGKM_Z=c("DIST_ACTIVE_CURR","logkm_z"),
  DIST_CL_REF_LOGKM_Z=c("DIST_CL_REF","logkm_z"),
  DIST_CL_CURR_LOGKM_Z=c("DIST_CL_CURR","logkm_z"),
  DIST_WATER_CURR_LOGKM_Z=c("DIST_WATER_CURR","logkm_z"),
  DIST_CHANNEL_PREV_LOGKM_Z=c("DIST_CHANNEL_PREV","logkm_z"),
  REL_CHANNEL_POS_PREV_Z=c("REL_CHANNEL_POS_PREV","z"),
  MAM_OUTER_CURV_REACT_PREV_Z=c("MAM_OUTER_CURV_REACT_PREV","z"),
  MAM_INNER_CURV_STORAGE_PREV_Z=c("MAM_INNER_CURV_STORAGE_PREV","z"),
  MAM_OUTER_CURV_STORAGE_PREV_Z=c("MAM_OUTER_CURV_STORAGE_PREV","z"),
  MAM_NEAR_CHANNEL_PREV=c("MAM_NEAR_CHANNEL_PREV","binary"),
  MAM_OUTER_REACT_EXPOSED_PREV=c("MAM_OUTER_REACT_EXPOSED_PREV","binary"),
  MAM_NEAR_BANK_STORAGE_PREV=c("MAM_NEAR_BANK_STORAGE_PREV","binary"),
  MAM_INNER_STORAGE_EXPOSED_PREV=c("MAM_INNER_STORAGE_EXPOSED_PREV","binary"),
  MAM_OUTER_STORAGE_EXPOSED_PREV=c("MAM_OUTER_STORAGE_EXPOSED_PREV","binary")
)

# Standardise the finite predictor values using their sample mean and SD.
# Insufficient observations or zero variance produce NA rather than a fabricated
# value; this may reduce the complete-case risk population of a refit.
z_preserve <- function(x) {
  x <- suppressWarnings(as.numeric(x)); ok <- is.finite(x)
  out <- rep(NA_real_, length(x))
  if (sum(ok) < 2) return(out)
  s <- stats::sd(x[ok]); if (!is.finite(s) || s == 0) return(out)
  out[ok] <- (x[ok]-mean(x[ok]))/s
  out
}
# Create only recognised missing terms. Never silently invent an unsupported
# production transformation, and leave any already supplied terms unchanged.
construct_terms <- function(d, required_terms) {
  for (tm in required_terms) {
    if (tm %in% names(d)) next
    rr <- recipe[[tm]]
    if (is.null(rr) || !rr[1] %in% names(d)) next
    x <- d[[rr[1]]]
    if (rr[2] == "z") d[[tm]] <- z_preserve(x)
    else if (rr[2] == "logkm_z") d[[tm]] <- z_preserve(log1p(pmax(0,suppressWarnings(as.numeric(x)))/1000))
    else if (rr[2] == "binary") d[[tm]] <- as.integer(suppressWarnings(as.numeric(x)) != 0)
  }
  d
}

# Only attempt the RiskTable fallback when refits are requested and the original
# 08x interval export was not found. An absent source leaves coefficient/PH/QA
# summaries available, but prevents model-level diagnostic refitting.
if (is.null(cox_input) && RunRefits) {
  rt <- read_risk_table(RiskTable, RiskLayerName)
  if (!is.null(rt)) {
    required_terms_all <- unique(as.character(terms_used$term))
    required_terms_all <- required_terms_all[!is.na(required_terms_all) & nzchar(required_terms_all)]
    cox_input <- construct_terms(rt, required_terms_all)
    input_source <- "RiskTable fallback"
    rm(rt); invisible(gc())
  }
}

# Event and risk fields by model definition.
# Pin each definition to its own transition-specific risk and event fields.
# For example: SF->AD reactivation, AD->DS storage formation, DS->SF
# stabilisation and DS->AD storage reworking. The first-event initial-FP model
# uses a different base eligibility population from SF->AD and does not imply
# that Depositional Storage belongs to broad eligible FP prediction.
model_spec <- data.frame(
  model=c(
    "active_domain_reactivation","initial_floodplain_reactivation","depositional_storage_full_event",
    "depositional_storage_local_position_subset","floodplain_stabilisation","depositional_storage_reworking",
    "any_named_primary_transition",
    "state_only_active_domain_reactivation","state_only_depositional_storage_full_event",
    "state_only_depositional_storage_local_position_subset","state_only_floodplain_stabilisation",
    "state_only_depositional_storage_reworking","state_only_any_state_transition",
    "pure_state_active_domain_reactivation","pure_state_depositional_storage_full_event",
    "pure_state_depositional_storage_local_position_subset","pure_state_floodplain_stabilisation",
    "pure_state_depositional_storage_reworking","pure_state_any_state_transition"
  ),
  risk_field=c(
    "REACTIVATE_RISK_SET","BASE_REACTIVATE_RISK_SET_DERIVED","STORAGE_RISK_SET",
    "STORAGE_RISK_SET","STABILISE_RISK_SET","STORAGE_REWORK_RISK_SET","ANY_STATE_RISK_SET",
    "REACTIVATE_RISK_SET_STRICT_AUDIT","STORAGE_RISK_SET_STRICT_AUDIT","STORAGE_RISK_SET_STRICT_AUDIT",
    "STABILISE_RISK_SET_STRICT_AUDIT","STORAGE_REWORK_RISK_SET_STRICT_AUDIT","ANY_STATE_RISK_SET_STRICT_AUDIT",
    "REACTIVATE_RISK_SET_STRICT_AUDIT","STORAGE_RISK_SET_STRICT_AUDIT","STORAGE_RISK_SET_STRICT_AUDIT",
    "STABILISE_RISK_SET_STRICT_AUDIT","STORAGE_REWORK_RISK_SET_STRICT_AUDIT","ANY_STATE_RISK_SET_STRICT_AUDIT"
  ),
  event_field=c(
    "REACTIVATE_EVT","BASE_REACTIVATE_EVT","STORAGE_EVT","STORAGE_EVT","STABILISE_EVT",
    "STORAGE_REWORK_EVT","ANY_CONFIRMED_EVT",
    "REACTIVATE_TRANS","STORAGE_TRANS","STORAGE_TRANS","STABILISE_TRANS","STORAGE_REWORK_TRANS","ANY_STATE_EVT",
    "REACTIVATE_TRANS","STORAGE_TRANS","STORAGE_TRANS","STABILISE_TRANS","STORAGE_REWORK_TRANS","ANY_STATE_EVT"
  ),
  definition=c(rep("primary",7),rep("strict",6),rep("pure_state",6)),
  stringsAsFactors=FALSE
)

# -----------------------------
# 5. Event support by predictor strata
# -----------------------------

# Select precisely those predictors used by the historic production model;
# a diagnostic must not infer a different scientific formula from field names.
get_terms <- function(model) {
  z <- terms_used$term[as.character(terms_used$model)==model]
  unique(as.character(z[!is.na(z) & nzchar(as.character(z))]))
}

# Subset the interval table to the model's explicit risk field and, where
# available, strict/pure-state eligibility criteria. Pure-state restrictions
# require five M3 support/mixing fields: if any are absent, the code does not
# apply that additional purity filter. This limitation needs attention when
# interpreting definition-sensitivity comparisons.
get_model_data <- function(model) {
  if (is.null(cox_input)) return(NULL)
  sp <- model_spec[model_spec$model==model,,drop=FALSE]
  if (!nrow(sp)) return(NULL)
  d <- cox_input
  if (!sp$risk_field[1] %in% names(d) || !sp$event_field[1] %in% names(d)) return(NULL)
  keep <- suppressWarnings(as.numeric(d[[sp$risk_field[1]]])) == 1
  keep[is.na(keep)] <- FALSE
  d <- d[keep,,drop=FALSE]
  if (sp$definition[1] == "strict" && "M3_MODEL_ELIGIBLE_STRICT" %in% names(d)) {
    d <- d[suppressWarnings(as.numeric(d$M3_MODEL_ELIGIBLE_STRICT))==1,,drop=FALSE]
  }
  if (sp$definition[1] == "pure_state") {
    req <- c("M3_MODEL_ELIGIBLE_STRICT","M3_MIXED_T1","M3_MIXED_T2","M3_STATE_SUPPORT_T1","M3_STATE_SUPPORT_T2")
    if (all(req %in% names(d))) {
      keep2 <- suppressWarnings(as.numeric(d$M3_MODEL_ELIGIBLE_STRICT))==1 &
        suppressWarnings(as.numeric(d$M3_MIXED_T1))==0 &
        suppressWarnings(as.numeric(d$M3_MIXED_T2))==0 &
        suppressWarnings(as.numeric(d$M3_STATE_SUPPORT_T1))>=PureStateMinSupport &
        suppressWarnings(as.numeric(d$M3_STATE_SUPPORT_T2))>=PureStateMinSupport
      keep2[is.na(keep2)] <- FALSE
      d <- d[keep2,,drop=FALSE]
    }
  }
  d
}

# Construct event-support summaries by predictor strata within each eligible
# model population. Numeric terms use empirical quartiles (or a median split
# when distinct quantile edges are insufficient); categorical terms use labels.
# Small stratum event counts warn of unstable or separated hazard estimates.
support_rows <- list()
if (!is.null(cox_input)) {
  for (m in unique(model_spec$model)) {
    d <- get_model_data(m); if (is.null(d) || !nrow(d)) next
    ev <- model_spec$event_field[model_spec$model==m][1]
    terms <- get_terms(m)
    terms <- terms[terms %in% names(d)]
    for (tm in terms) {
      x <- d[[tm]]
      event <- suppressWarnings(as.numeric(d[[ev]]))==1
      if (is.numeric(x) || all(!is.na(suppressWarnings(as.numeric(as.character(x)))) | is.na(x))) {
        xx <- suppressWarnings(as.numeric(as.character(x)))
        ok <- is.finite(xx)
        if (sum(ok) < 4) next
        br <- unique(stats::quantile(xx[ok], probs=c(0,.25,.5,.75,1), na.rm=TRUE, type=7))
        if (length(br)<3) {
          strata <- ifelse(xx <= median(xx[ok],na.rm=TRUE),"low","high")
        } else {
          strata <- cut(xx, breaks=br, include.lowest=TRUE, ordered_result=TRUE)
        }
      } else {
        strata <- as.character(x)
      }
      # Report both at-risk row counts and observed event counts per stratum; the
      # MinEventsPerTerm flag is a screening threshold, not a statistical test.
      tab <- aggregate(cbind(rows=rep(1,nrow(d)), events=as.integer(event)) ~ strata, FUN=sum, na.action=na.pass)
      tab$model <- m; tab$term <- tm
      tab$sparse_event_support <- tab$events < MinEventsPerTerm
      support_rows[[length(support_rows)+1]] <- tab
    }
  }
}
event_support <- if (length(support_rows)) do.call(rbind,support_rows) else
  empty_df(strata=character(), rows=integer(), events=integer(), model=character(), term=character(), sparse_event_support=logical())
wcsv(event_support, "COX_PH_04_event_support.csv")

# -----------------------------
# 6. Correlation / collinearity
# -----------------------------

# Screen pairwise Pearson correlations among varying numeric predictors in the
# same transition-specific eligible population. High |r| implies possible
# coefficient imprecision; it does not establish a causal relation or prove
# collinearity in the entire multivariate design matrix.
collin_rows <- list()
if (!is.null(cox_input)) {
  for (m in unique(model_spec$model)) {
    d <- get_model_data(m); if (is.null(d) || !nrow(d)) next
    terms <- get_terms(m)
    terms <- terms[terms %in% names(d)]
    numeric_terms <- terms[vapply(terms, function(tm) {
      x <- suppressWarnings(as.numeric(as.character(d[[tm]])))
      sum(is.finite(x)) >= 3 && is.finite(stats::sd(x,na.rm=TRUE)) && stats::sd(x,na.rm=TRUE)>0
    }, logical(1))]
    if (length(numeric_terms)<2) next
    # Each pair is evaluated on its own finite-value overlap; n_complete records
    # the actual support for that correlation rather than the whole risk-set size.
    for (i in seq_len(length(numeric_terms)-1)) for (j in (i+1):length(numeric_terms)) {
      a <- suppressWarnings(as.numeric(as.character(d[[numeric_terms[i]]])))
      b <- suppressWarnings(as.numeric(as.character(d[[numeric_terms[j]]])))
      ok <- is.finite(a)&is.finite(b)
      if (sum(ok)<3) next
      r <- suppressWarnings(stats::cor(a[ok],b[ok]))
      collin_rows[[length(collin_rows)+1]] <- data.frame(
        model=m, term_1=numeric_terms[i], term_2=numeric_terms[j], n_complete=sum(ok),
        pearson_r=r, abs_r=abs(r), high_correlation=is.finite(r) & abs(r)>=HighCorrelation,
        stringsAsFactors=FALSE)
    }
  }
}
collinearity <- if(length(collin_rows)) do.call(rbind,collin_rows) else
  empty_df(model=character(),term_1=character(),term_2=character(),n_complete=integer(),pearson_r=numeric(),abs_r=numeric(),high_correlation=logical())
wcsv(collinearity, "COX_PH_05_collinearity.csv")

# -----------------------------
# 7. Checked Cox fitting
# -----------------------------

# Fit a diagnostic counting-process Cox model with Surv(tstart_yr,tstop_yr,event)
# and PLACE_ID-clustered variance to acknowledge repeated intervals at a fixed
# place. Efron ties match the declared fitting method. This clustering does not
# eliminate dependence between neighbouring places participating in one event.
# All diagnostic refits use complete cases for the selected term set, so
# reduced-model fit statistics may refer to different analysis rows.
fit_checked <- function(d, event_field, terms, iter.max=20L) {
  out <- list(model=NULL,status="not_fitted",warnings="",error="",converged=FALSE,nonfinite=TRUE)
  if (is.null(d) || !nrow(d) || !event_field %in% names(d)) return(out)
  terms <- terms[terms %in% names(d)]
  if (!length(terms)) { out$status <- "no_terms"; return(out) }
  vars <- unique(c("PLACE_ID","tstart_yr","tstop_yr",event_field,terms))
  if (!all(c("PLACE_ID","tstart_yr","tstop_yr") %in% names(d))) { out$status <- "missing_survival_fields"; return(out) }
  cc <- stats::complete.cases(d[,vars,drop=FALSE])
  dd <- d[cc,,drop=FALSE]
  if (!nrow(dd) || sum(suppressWarnings(as.numeric(dd[[event_field]]))==1,na.rm=TRUE)==0) {
    out$status <- "no_events_after_complete_case"; return(out)
  }
  # Remove zero-variation terms within this exact model set.
  # Drop terms that have no variation in the current complete-case subset;
  # retaining them would make the diagnostic design matrix non-estimable.
  # This is diagnostic pruning only and must not rewrite the production formula.
  keep_terms <- terms[vapply(terms,function(tm){
    x<-dd[[tm]]
    if(is.factor(x)||is.character(x)) length(unique(na.omit(as.character(x))))>1
    else {s<-suppressWarnings(stats::sd(as.numeric(x),na.rm=TRUE)); is.finite(s)&&s>0}
  },logical(1))]
  if(!length(keep_terms)){out$status<-"no_varying_terms"; return(out)}
  form <- stats::as.formula(paste0("survival::Surv(tstart_yr,tstop_yr,",event_field,") ~ ",
                                   paste(keep_terms,collapse=" + "), " + survival::cluster(PLACE_ID)"))
  # Capture convergence and infinite-coefficient warnings explicitly; a returned
  # coxph object is not treated as cleanly converged merely because it exists.
  warns <- character()
  err <- ""
  mod <- tryCatch(
    withCallingHandlers(
      survival::coxph(form,data=dd,ties="efron",x=TRUE,control=survival::coxph.control(iter.max=iter.max)),
      warning=function(w){warns<<-c(warns,conditionMessage(w));invokeRestart("muffleWarning")}
    ),
    error=function(e){err<<-conditionMessage(e);NULL}
  )
  out$model <- mod
  out$warnings <- paste(unique(warns),collapse=" | ")
  out$error <- err
  if(is.null(mod)){out$status<-"fit_error";return(out)}
  # Screen non-finite coefficients and warning strings, then retain fit size,
  # event support, and the terms actually estimable in the diagnostic refit.
  beta <- stats::coef(mod)
  nonfinite <- any(!is.finite(beta))
  conv_warn <- grepl("converg|iterations|infinite|beta may be infinite",paste(out$warnings,out$error),ignore.case=TRUE)
  out$nonfinite <- nonfinite
  out$converged <- !nonfinite && !conv_warn
  out$status <- if(nonfinite) "nonfinite_coefficient" else if(conv_warn) "convergence_warning" else "fitted"
  out$data_n <- nrow(dd)
  out$events <- sum(suppressWarnings(as.numeric(dd[[event_field]]))==1,na.rm=TRUE)
  out$terms <- keep_terms
  out
}

# Exponentiate diagnostic model coefficients into HRs with confidence intervals;
# carry the model/variant, counts, warnings and fit status into each export.
tidy_fit <- function(fit,m,variant) {
  if(is.null(fit$model)) return(empty_df())
  z <- broom::tidy(fit$model,exponentiate=TRUE,conf.int=TRUE)
  z$model<-m; z$variant<-variant; z$n<-fit$data_n; z$events<-fit$events
  z$status<-fit$status; z$fit_warning<-fit$warnings; z$fit_error<-fit$error
  z
}

# Reduced sequence rule:
#  A spatial-only (or first production term if no spatial term)
#  B spatial + history_core
#  C B + transition-specific history
#  D full production model
# This is ordered diagnosis, not model selection by p-values.
# Ordered diagnostic reduction adds antecedent assemblage-memory terms to
# spatial predictors in stages. This is an estimation triage sequence, NOT a
# formal nested-memory comparison or a p-value-driven selection procedure.
history_core <- c("ASM_DOM_RATIO_PREV_Z","ASM_N_EPISODES_PREV_Z","ASM_MAX_QUIET_PREV_Z","ASM_COV_FRAC_Z")
# History extras are tailored to each transition; AD->DS appears here as a
# reduced-fit diagnostic even though it is excluded from the separately defined
# formal assemblage-memory comparison used in Paper 2.
transition_extra <- list(
  SF_AD=c("ASM_N_REACTIVATE_PREV_Z"),
  AD_DS=c("ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
  AD_DS_LOCAL=c("ASM_STORAGE_FRAC_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
  DS_SF=c("ASM_STORAGE_FRAC_PREV_Z","ASM_STAB_FP_FRAC_PREV_Z","ASM_QUIET_SINCE_PREV_Z","ASM_N_STABILISE_PREV_Z"),
  DS_AD=c("ASM_STORAGE_FRAC_PREV_Z","ASM_QUIET_SINCE_PREV_Z","ASM_N_STORAGE_EVT_PREV_Z"),
  ANY=c("ASM_DIST_FREQ_PREV_Z")
)

# Prefer the production spatial-framework table to identify spatial predictors.
# If absent, use recognised spatial prefixes and finally the first term so an
# estimation diagnostic can still be attempted; this fallback is not proof that
# the selected term is scientifically spatial.
get_spatial_terms <- function(m, full_terms) {
  z <- character()
  if(!is.null(spatial_framework) && all(c("model","spatial_terms")%in%names(spatial_framework))) {
    s <- spatial_framework$spatial_terms[as.character(spatial_framework$model)==m]
    if(length(s) && !is.na(s[1]) && nzchar(s[1])) z <- trimws(unlist(strsplit(s[1],";",fixed=TRUE)))
  }
  z <- z[z%in%full_terms]
  if(!length(z)) {
    z <- full_terms[grepl("^(DIST_|REL_|MAM_|CURV_)",full_terms)]
  }
  if(!length(z) && length(full_terms)) z <- full_terms[1]
  unique(z)
}

# For primary models, attempt ordered A/B/C/D specifications when requested.
# Skip duplicate term combinations and retain convergence, concordance and
# coefficient exports. A successful reduced fit never replaces the original.
reduced_rows <- list()
reduced_fits <- list()
if(RunRefits && !is.null(cox_input)) {
  primary_models <- model_spec$model[model_spec$definition=="primary"]
  for(m in primary_models) {
    d <- get_model_data(m); if(is.null(d)||!nrow(d)) next
    ev <- model_spec$event_field[model_spec$model==m][1]
    full <- get_terms(m); full <- full[full%in%names(d)]
    if(!length(full)) next
    tg <- model_alias$transition_group[match(m,model_alias$model)]
    sp <- get_spatial_terms(m,full)
    hc <- intersect(history_core,full)
    ex <- intersect(transition_extra[[tg]],full)
    # A: spatial core; B: spatial + generic history; C: B + transition-specific
    # history; D: complete original production terms. Results are descriptive
    # checks for over-parameterisation, sparse support and coefficient instability.
    seq_terms <- list(
      A_spatial_core=unique(sp),
      B_spatial_plus_history_core=unique(c(sp,hc)),
      C_add_transition_history=unique(c(sp,hc,ex)),
      D_full_production=full
    )
    # ensure genuinely ordered unique specifications
    seen <- character()
    for(v in names(seq_terms)) {
      tt <- seq_terms[[v]]
      key <- paste(tt,collapse="|")
      if(!length(tt)||key%in%seen) next
      seen <- c(seen,key)
      invisible(gc())
      ft <- fit_checked(d,ev,tt,iter.max=20L)
      reduced_fits[[paste(m,v,sep="::")]] <- ft
      rr <- data.frame(
        model=m,transition_group=tg,variant=v,
        n=ifelse(is.null(ft$data_n),nrow(d),ft$data_n),
        events=ifelse(is.null(ft$events),sum(suppressWarnings(as.numeric(d[[ev]]))==1,na.rm=TRUE),ft$events),
        n_terms=length(tt),terms=paste(tt,collapse="; "),
        status=ft$status,converged=ft$converged,nonfinite=ft$nonfinite,
        fit_warning=ft$warnings,fit_error=ft$error,
        concordance=if(!is.null(ft$model)) tryCatch(as.numeric(summary(ft$model)$concordance[1]),error=function(e)NA_real_) else NA_real_,
        stringsAsFactors=FALSE
      )
      reduced_rows[[length(reduced_rows)+1]] <- rr
      if(!is.null(ft$model)){
        td<-tidy_fit(ft,m,v)
        wcsv(td,paste0("COX_PH_REDUCED_",gsub("[^A-Za-z0-9_]+","_",m),"_",v,"_coefficients.csv"))
      }
      rm(ft); invisible(gc())
    }
  }
}
reduced_summary <- if(length(reduced_rows)) do.call(rbind,reduced_rows) else
  empty_df(model=character(),transition_group=character(),variant=character(),n=integer(),events=integer(),n_terms=integer(),
           terms=character(),status=character(),converged=logical(),nonfinite=logical(),fit_warning=character(),fit_error=character(),concordance=numeric())
# The summary records failed as well as successful fits, permitting transparent
# review even when one or more stages had zero events or convergence warnings.
wcsv(reduced_summary,"COX_PH_06_reduced_model_sequence.csv")

# -----------------------------
# 8. Jamuna SF->AD comparison
# -----------------------------

# Jamuna-specific reactivation comparison juxtaposes primary, strict and pure-
# state estimates, the best available ordered reduced diagnostic, and v1.5
# spatial thinning evidence. The compared populations/specifications can differ;
# the table is a robustness audit, not a pooled or independent validation fit.
sfad_rows <- list()
if(identical(reach_label,"Jamuna")) {
  target_models <- c("active_domain_reactivation","state_only_active_domain_reactivation","pure_state_active_domain_reactivation")
  for(m in target_models) {
    inv <- inventory[inventory$model==m,,drop=FALSE]
    cf <- coefficients_existing[coefficients_existing$model==m,,drop=FALSE]
    spatial_terms_m <- get_spatial_terms("active_domain_reactivation",get_terms(m))
    spatial_cf <- cf[cf$term%in%spatial_terms_m,,drop=FALSE]
    sfad_rows[[length(sfad_rows)+1]] <- data.frame(
      variant=ifelse(m=="active_domain_reactivation","baseline",
              ifelse(grepl("^state_only",m),"strict_state","pure_state")),
      model=m,
      status=if(nrow(inv)&&"status"%in%names(inv)) as.character(inv$status[1]) else if(nrow(cf))"fitted" else "not_fitted",
      n=if(nrow(inv)&&"n"%in%names(inv))inv$n[1] else NA,
      events=if(nrow(inv)&&"events"%in%names(inv))inv$events[1] else NA,
      spatial_term=if(nrow(spatial_cf))paste(spatial_cf$term,collapse="; ") else paste(spatial_terms_m,collapse="; "),
      spatial_HR=if(nrow(spatial_cf))spatial_cf$HR[1] else NA,
      spatial_CI_low=if(nrow(spatial_cf))spatial_cf$conf.low[1] else NA,
      spatial_CI_high=if(nrow(spatial_cf))spatial_cf$conf.high[1] else NA,
      stringsAsFactors=FALSE)
  }
  # Best successful reduced fit.
  # Select the first converged ordered reduction when one exists, otherwise the
  # first attempted variant; the selection order is diagnostic rather than the
  # highest apparent concordance or lowest p-value.
  rr <- reduced_summary[reduced_summary$model=="active_domain_reactivation",,drop=FALSE]
  if(nrow(rr)) {
    best <- rr[match(TRUE,rr$converged,nomatch=1),,drop=FALSE]
    key<-paste("active_domain_reactivation",best$variant[1],sep="::")
    ft<-reduced_fits[[key]]
    cf<-if(!is.null(ft)&&!is.null(ft$model)) broom::tidy(ft$model,exponentiate=TRUE,conf.int=TRUE) else NULL
    spatial_terms_m<-get_spatial_terms("active_domain_reactivation",best$terms)
    srow<-if(!is.null(cf))cf[cf$term%in%spatial_terms_m,,drop=FALSE] else NULL
    sfad_rows[[length(sfad_rows)+1]]<-data.frame(
      variant="reduced",model=paste0("active_domain_reactivation::",best$variant[1]),status=best$status[1],
      n=best$n[1],events=best$events[1],
      spatial_term=if(!is.null(srow)&&nrow(srow))srow$term[1] else paste(spatial_terms_m,collapse="; "),
      spatial_HR=if(!is.null(srow)&&nrow(srow))srow$estimate[1] else NA,
      spatial_CI_low=if(!is.null(srow)&&nrow(srow))srow$conf.low[1] else NA,
      spatial_CI_high=if(!is.null(srow)&&nrow(srow))srow$conf.high[1] else NA,stringsAsFactors=FALSE)
  }
  # Authoritative v1.5 spatial sensitivity row(s).
  # Append spatial thinning results only when the aligned v1.5 evidence is usable;
  # missing spatial sensitivity is explicitly recorded as unavailable.
  if (spatial_available) {
    so <- spatial_model_evidence[
      as.character(spatial_model_evidence$production_model) == "active_domain_reactivation",
      , drop = FALSE
    ]
    st <- if (!is.null(spatial_thin_stability)) spatial_thin_stability[
      as.character(spatial_thin_stability$production_model) == "active_domain_reactivation" &
      as.character(spatial_thin_stability$predictor_role) == "PRINCIPAL",
      , drop = FALSE
    ] else NULL

    if (nrow(st)) {
      for (k in seq_len(nrow(st))) {
        sfad_rows[[length(sfad_rows)+1]] <- data.frame(
          variant = paste0("spatial_thinning_", st$spacing_m[k], "m"),
          model = "active_domain_reactivation",
          status = if (nrow(so) && isTRUE(so$spatial_diagnostic_clean_convergence[1]))
            "v1.5 diagnostic clean; thinning integrated" else "v1.5 spatial sensitivity available",
          n = if (nrow(so) && "baseline_rows" %in% names(so)) so$baseline_rows[1] else NA,
          events = if (nrow(so) && "baseline_events" %in% names(so)) so$baseline_events[1] else NA,
          spatial_term = as.character(st$term[k]),
          spatial_HR = if ("median_hr" %in% names(st)) suppressWarnings(as.numeric(st$median_hr[k])) else NA,
          spatial_CI_low = NA,
          spatial_CI_high = NA,
          stringsAsFactors = FALSE
        )
      }
    } else if (nrow(so)) {
      sfad_rows[[length(sfad_rows)+1]] <- data.frame(
        variant = "spatial_sensitivity_v1_5",
        model = "active_domain_reactivation",
        status = "v1.5 overall spatial evidence available",
        n = if ("baseline_rows" %in% names(so)) so$baseline_rows[1] else NA,
        events = if ("baseline_events" %in% names(so)) so$baseline_events[1] else NA,
        spatial_term = NA,
        spatial_HR = NA,
        spatial_CI_low = NA,
        spatial_CI_high = NA,
        stringsAsFactors = FALSE
      )
    }
  } else {
    sfad_rows[[length(sfad_rows)+1]] <- data.frame(
      variant = "spatial_sensitivity_v1_5",
      model = "active_domain_reactivation",
      status = "v1.5 spatial-sensitivity outputs not supplied",
      n = NA, events = NA, spatial_term = NA,
      spatial_HR = NA, spatial_CI_low = NA, spatial_CI_high = NA,
      stringsAsFactors = FALSE
    )
  }
}
jamuna_sfad <- if(length(sfad_rows))do.call(rbind,sfad_rows) else
  empty_df(variant=character(),model=character(),status=character(),n=integer(),events=integer(),spatial_term=character(),
           spatial_HR=numeric(),spatial_CI_low=numeric(),spatial_CI_high=numeric())
wcsv(jamuna_sfad,"COX_PH_07_Jamuna_SF_AD_comparison.csv")

# -----------------------------
# 9. DS->SF separation / sparsity
# -----------------------------

# Focus the sparse-stratum and apparent-separation audit on DS->SF stabilisation,
# where event scarcity or a zero-event/all-event predictor stratum can undermine
# coefficient identification. A flagged stratum suggests potential separation;
# it is not a proof of complete multivariable separation.
separation_rows <- list()
if(!is.null(cox_input)) {
  for(m in c("floodplain_stabilisation","state_only_floodplain_stabilisation","pure_state_floodplain_stabilisation")) {
    d<-get_model_data(m); if(is.null(d)||!nrow(d))next
    ev<-model_spec$event_field[model_spec$model==m][1]
    terms<-get_terms(m); terms<-terms[terms%in%names(d)]
    event<-suppressWarnings(as.numeric(d[[ev]]))==1
    for(tm in terms) {
      x<-d[[tm]]
      if(is.numeric(x)||all(!is.na(suppressWarnings(as.numeric(as.character(x))))|is.na(x))){
        xx<-suppressWarnings(as.numeric(as.character(x))); ok<-is.finite(xx)
        if(sum(ok)<4)next
        br<-unique(stats::quantile(xx[ok],c(0,.25,.5,.75,1),na.rm=TRUE))
        if(length(br)>=3)grp<-cut(xx,br,include.lowest=TRUE) else grp<-ifelse(xx<=median(xx[ok],na.rm=TRUE),"low","high")
      } else grp<-as.character(x)
      tab<-aggregate(cbind(rows=rep(1,nrow(d)),events=as.integer(event))~grp,FUN=sum,na.action=na.pass)
      # Zero events or zero non-events within a predictor stratum raise an apparent-
      # separation flag, which contributes to the final caution/disposition reasons.
      tab$non_events<-tab$rows-tab$events
      tab$zero_event_stratum<-tab$events==0
      tab$all_event_stratum<-tab$non_events==0
      tab$apparent_separation<-tab$zero_event_stratum|tab$all_event_stratum
      tab$model<-m;tab$term<-tm
      separation_rows[[length(separation_rows)+1]]<-tab
    }
  }
}
ds_sf_sep<-if(length(separation_rows))do.call(rbind,separation_rows) else
  empty_df(grp=character(),rows=integer(),events=integer(),non_events=integer(),zero_event_stratum=logical(),
           all_event_stratum=logical(),apparent_separation=logical(),model=character(),term=character())
wcsv(ds_sf_sep,"COX_PH_08_DS_SF_separation.csv")

# -----------------------------
# 10. Period models rerun individually
# -----------------------------

# Divide each model's observed tstart/tstop span into three equal elapsed-time
# thirds; assign a row by its interval start. These are NOT equal-event-count
# tertiles and do not split a row crossing a period boundary.
split_periods <- function(d) {
  lo<-min(suppressWarnings(as.numeric(d$tstart_yr)),na.rm=TRUE)
  hi<-max(suppressWarnings(as.numeric(d$tstop_yr)),na.rm=TRUE)
  span<-hi-lo; c1<-lo+span/3;c2<-lo+2*span/3
  d$PH_PERIOD<-ifelse(d$tstart_yr<c1,"Early",ifelse(d$tstart_yr<c2,"Middle","Late"))
  attr(d,"cuts")<-c(lo,c1,c2,hi);d
}
# Rerun the production term set within early, middle and late thirds where
# requested and event support is sufficient. A prior period-summary failure
# narrows the targets; otherwise all primary models are considered.
# This assesses coefficient stability under time restriction; it does not
# establish time-varying causal effects or repair a failed PH assumption.
period_rows<-list()
if(RunPeriodReruns && RunRefits && !is.null(cox_input)) {
  # Target models: failed/warned in prior period summary; if unavailable, all primary models.
  targets<-unique(model_spec$model[model_spec$definition=="primary"])
  if(!is.null(ph_period_summary)&&"model"%in%names(ph_period_summary)){
    bad<-ph_period_summary$model[
      if("status"%in%names(ph_period_summary)) !tolower(ph_period_summary$status)%in%c("fitted","ok","converged") else TRUE
    ]
    if(length(na.omit(bad))) targets<-unique(as.character(na.omit(bad)))
  }
  for(m in targets) {
    d<-get_model_data(m);if(is.null(d)||!nrow(d))next
    ev<-model_spec$event_field[model_spec$model==m][1]
    full<-get_terms(m);full<-full[full%in%names(d)]
    sp<-get_spatial_terms(m,full)
    if(!length(sp))next
    pd<-split_periods(d)
    for(per in c("Early","Middle","Late")) {
      dd<-pd[pd$PH_PERIOD==per,,drop=FALSE]
      nev<-sum(suppressWarnings(as.numeric(dd[[ev]]))==1,na.rm=TRUE)
      invisible(gc())
      # Skip a period with fewer than the configured number of observed events;
      # report it as too_few_events rather than making an unstable estimate.
      if(nev<MinEventsPerPeriod){
        period_rows[[length(period_rows)+1]]<-data.frame(model=m,period=per,n=nrow(dd),events=nev,
          terms=paste(full,collapse="; "),status="too_few_events",converged=FALSE,fit_warning="",fit_error="",
          spatial_HR=NA,spatial_CI_low=NA,spatial_CI_high=NA,stringsAsFactors=FALSE)
        next
      }
      ft<-fit_checked(dd,ev,full,iter.max=20L)
      cf<-if(!is.null(ft$model))broom::tidy(ft$model,exponentiate=TRUE,conf.int=TRUE)else NULL
      sr<-if(!is.null(cf))cf[cf$term%in%sp,,drop=FALSE]else NULL
      period_rows[[length(period_rows)+1]]<-data.frame(model=m,period=per,
        n=ifelse(is.null(ft$data_n),nrow(dd),ft$data_n),events=ifelse(is.null(ft$events),nev,ft$events),
        terms=paste(full,collapse="; "),status=ft$status,converged=ft$converged,
        fit_warning=ft$warnings,fit_error=ft$error,
        spatial_HR=if(!is.null(sr)&&nrow(sr))sr$estimate[1]else NA,
        spatial_CI_low=if(!is.null(sr)&&nrow(sr))sr$conf.low[1]else NA,
        spatial_CI_high=if(!is.null(sr)&&nrow(sr))sr$conf.high[1]else NA,stringsAsFactors=FALSE)
      rm(ft); invisible(gc())
    }
  }
}
period_refits<-if(length(period_rows))do.call(rbind,period_rows)else
  empty_df(model=character(),period=character(),n=integer(),events=integer(),terms=character(),status=character(),
           converged=logical(),fit_warning=character(),fit_error=character(),spatial_HR=numeric(),spatial_CI_low=numeric(),spatial_CI_high=numeric())
wcsv(period_refits,"COX_PH_09_period_refits.csv")

# -----------------------------
# 11. Primary vs sensitivity HR comparison
# -----------------------------

# Compare common coefficient terms across primary, strict and high-support
# pure-state definitions. HR directions are relative to the null HR=1;
# reversals qualify explanatory stability. Matching term names does not by
# itself guarantee identically centred predictors or matched risk populations.
sens_compare_rows<-list()
groups<-unique(na.omit(model_alias$transition_group))
for(tg in groups){
  prim_models<-model_alias$model[model_alias$transition_group==tg & model_alias$definition=="primary"]
  strict_models<-model_alias$model[model_alias$transition_group==tg & model_alias$definition=="strict"]
  pure_models<-model_alias$model[model_alias$transition_group==tg & model_alias$definition=="pure_state"]
  pcf<-coefficients_existing[coefficients_existing$model%in%prim_models,,drop=FALSE]
  scf<-coefficients_existing[coefficients_existing$model%in%strict_models,,drop=FALSE]
  ucf<-coefficients_existing[coefficients_existing$model%in%pure_models,,drop=FALSE]
  common_terms<-Reduce(intersect,list(unique(pcf$term),unique(scf$term),unique(ucf$term)))
  if(!length(common_terms)) common_terms<-intersect(unique(pcf$term),union(unique(scf$term),unique(ucf$term)))
  for(tm in common_terms){
    # Retrieve the first matched HR, retaining NA for any definition without that
    # term; do not manufacture a comparable estimate for an absent coefficient.
    val<-function(d){z<-d[d$term==tm,,drop=FALSE];if(nrow(z))z$HR[1]else NA_real_}
    hp<-val(pcf);hs<-val(scf);hu<-val(ucf)
    dir<-function(h)ifelse(!is.finite(h),"NA",ifelse(h>1,"positive",ifelse(h<1,"negative","null")))
    sens_compare_rows[[length(sens_compare_rows)+1]]<-data.frame(
      transition_group=tg,term=tm,primary_HR=hp,strict_HR=hs,pure_state_HR=hu,
      primary_direction=dir(hp),strict_direction=dir(hs),pure_state_direction=dir(hu),
      direction_stable=length(unique(c(dir(hp),dir(hs),dir(hu))[c(dir(hp),dir(hs),dir(hu))%in%c("positive","negative")]))<=1,
      max_logHR_difference=max(abs(c(if(is.finite(hs)&&is.finite(hp))log(hs/hp)else NA,
                                     if(is.finite(hu)&&is.finite(hp))log(hu/hp)else NA)),na.rm=TRUE),
      stringsAsFactors=FALSE)
  }
}
sens_compare<-if(length(sens_compare_rows))do.call(rbind,sens_compare_rows)else
  empty_df(transition_group=character(),term=character(),primary_HR=numeric(),strict_HR=numeric(),pure_state_HR=numeric(),
           primary_direction=character(),strict_direction=character(),pure_state_direction=character(),
           direction_stable=logical(),max_logHR_difference=numeric())
# Merge independent thinning results at the term level where the v1.5 interface
# marks quantitative evidence. Preserve missing thinning metrics as missing,
# rather than treating them as evidence of stability.
if(nrow(sens_compare)){
  sens_compare$max_logHR_difference[!is.finite(sens_compare$max_logHR_difference)]<-NA_real_

  # Integrate v1.5 spatial thinning at the term level.
  sens_compare$spatial_min_direction_stability <- NA_real_
  sens_compare$spatial_max_abs_median_delta_beta <- NA_real_
  sens_compare$spatial_quantitative_evidence <- FALSE
  if (!is.null(spatial_thin_stability) && nrow(spatial_thin_stability)) {
    for (i in seq_len(nrow(sens_compare))) {
      pm <- model_alias$model[
        model_alias$transition_group == sens_compare$transition_group[i] &
        model_alias$definition == "primary"
      ]
      if (!length(pm)) next
      z <- spatial_thin_stability[
        as.character(spatial_thin_stability$production_model) %in% pm &
        as.character(spatial_thin_stability$term) == sens_compare$term[i] &
        as.character(spatial_thin_stability$stability_interpretation) == "QUANTITATIVE",
        , drop = FALSE
      ]
      if (nrow(z)) {
        ds <- suppressWarnings(as.numeric(z$proportion_same_direction))
        db <- suppressWarnings(as.numeric(z$median_delta_beta))
        sens_compare$spatial_min_direction_stability[i] <-
          if (any(is.finite(ds))) min(ds[is.finite(ds)]) else NA_real_
        sens_compare$spatial_max_abs_median_delta_beta[i] <-
          if (any(is.finite(db))) max(abs(db[is.finite(db)])) else NA_real_
        sens_compare$spatial_quantitative_evidence[i] <- TRUE
      }
    }
  }
}
wcsv(sens_compare,"COX_PH_10_sensitivity_comparison.csv")

# -----------------------------
# 12. Automatic disposition
#
# Spatial rules:
#   - Moran's I/significance alone never demotes a model.
#   - Spatial direction reversal/instability under thinning can demote to
#     Sensitivity only.
#   - Residual correlation extent and coefficient magnitude shift are cautions.
#   - Clean v1.5 diagnostic/thinning evidence can support retaining a
#     non-convergent production specification as Primary with caution when
#     scientific direction is robust across independent sensitivity analyses.
# -----------------------------

# Only primary transition models receive final model dispositions. Strict and
# pure-state fits supply supporting sensitivity evidence but are not elevated
# to additional primary geomorphic transition types.
primary_models <- unique(model_spec$model[model_spec$definition=="primary"])

# Combine production status, coefficient pathology, term/global PH warnings,
# state-definition direction, DS->SF support/separation, reduced diagnostic
# convergence, and aligned v1.5 spatial evidence for each primary model.
# This classification is rule-based and record-conditional, not a formal
# statistical model-selection test or a held-out prediction assessment.
model_diag <- lapply(primary_models,function(m){
  inv<-inventory[inventory$model==m,,drop=FALSE]
  cf<-coefficients_existing[coefficients_existing$model==m,,drop=FALSE]
  phm<-if(nrow(ph_diag))ph_diag[ph_diag$model==m,,drop=FALSE]else NULL
  red<-reduced_summary[reduced_summary$model==m,,drop=FALSE]
  tg<-model_alias$transition_group[match(m,model_alias$model)]
  sc<-sens_compare[sens_compare$transition_group==tg,,drop=FALSE]
  sep<-if(tg=="DS_SF")ds_sf_sep else NULL
  prior_status<-if(nrow(inv)&&"status"%in%names(inv))as.character(inv$status[1])else if(nrow(cf))"fitted"else"not fitted"
  events<-if(nrow(inv)&&"events"%in%names(inv))suppressWarnings(as.numeric(inv$events[1]))else NA_real_
  n<-if(nrow(inv)&&"n"%in%names(inv))suppressWarnings(as.numeric(inv$n[1]))else NA_real_
  nonfinite<-nrow(cf)>0 && any(cf$flag_nonfinite,na.rm=TRUE)
  extreme<-nrow(cf)>0 && any(cf$flag_extreme,na.rm=TRUE)
  large_se<-nrow(cf)>0 && any(cf$flag_large_se,na.rm=TRUE)
  global_ph<-if(!is.null(phm)&&nrow(phm))any(phm$is_global & phm$ph_violation,na.rm=TRUE)else FALSE
  term_ph<-if(!is.null(phm)&&nrow(phm))any(!phm$is_global & phm$ph_violation,na.rm=TRUE)else FALSE
  reduced_success<-nrow(red)>0 && any(red$converged,na.rm=TRUE)
  sensitivity_reversal<-nrow(sc)>0 && any(sc$direction_stable==FALSE,na.rm=TRUE)
  separation<-!is.null(sep)&&nrow(sep)>0&&any(sep$apparent_separation,na.rm=TRUE)
  failed<-grepl("not fitted|fail|non.?converg|warning|infinite",prior_status,ignore.case=TRUE) || nonfinite

  # Spatial-sensitivity v1.5 evidence.
  # Match spatial evidence by the exact production-model identifier so a local
  # subset result cannot automatically stand in for a full-risk-set model.
  sme <- if (spatial_available) spatial_model_evidence[
    as.character(spatial_model_evidence$production_model) == m, , drop = FALSE
  ] else NULL
  spatial_evidence <- !is.null(sme) && nrow(sme) > 0L
  spatial_diag_clean <- if (spatial_evidence && "spatial_diagnostic_clean_convergence" %in% names(sme))
    isTRUE(as.logical(sme$spatial_diagnostic_clean_convergence[1])) else NA
  spatial_corr_extent <- if (spatial_evidence && "descriptive_residual_correlation_extent_m" %in% names(sme))
    suppressWarnings(as.numeric(sme$descriptive_residual_correlation_extent_m[1])) else NA_real_
  spatial_min_dir <- if (spatial_evidence && "spatial_min_direction_stability" %in% names(sme))
    suppressWarnings(as.numeric(sme$spatial_min_direction_stability[1])) else NA_real_
  spatial_max_dbeta <- if (spatial_evidence && "spatial_max_abs_median_delta_beta" %in% names(sme))
    suppressWarnings(as.numeric(sme$spatial_max_abs_median_delta_beta[1])) else NA_real_
  spatial_sep <- if (spatial_evidence && "spatial_any_flagged_separation" %in% names(sme))
    isTRUE(as.logical(sme$spatial_any_flagged_separation[1])) else FALSE
  spatial_baseline_sep <- if (spatial_evidence && "baseline_any_separation_flag" %in% names(sme))
    isTRUE(as.logical(sme$baseline_any_separation_flag[1])) else FALSE

  # Instability is deliberately based on robustness, not Moran significance.
  # A model is spatially direction-unstable when fewer than 80% of available
  # quantitative thinning offsets preserve the principal-term direction.
  # Hard-coded v1.5 integration thresholds: minimum direction retention <0.80
  # indicates sensitivity-only direction instability; |median delta beta| >0.70
  # is a magnitude-change caution (roughly a twofold HR scale difference).
  # These thresholds are not calibrated significance cutoffs.
  spatial_direction_unstable <- is.finite(spatial_min_dir) && spatial_min_dir < 0.80
  # Large change is a diagnostic caution threshold, approximately an HR ratio
  # > exp(0.7) ~ 2 relative to the like-for-like 150 m reference.
  spatial_magnitude_unstable <- is.finite(spatial_max_dbeta) && spatial_max_dbeta > 0.70

  # Disposition hierarchy.
  # Disposition hierarchy: non-estimability first, then direction reversals,
  # failed production fits with/without corroborating sensitivity, PH/precision/
  # separation cautions, otherwise primary. Significant residual Moran's I alone
  # never demotes a model; residual spatial dependence remains a qualification.
  if((is.finite(events)&&events==0) ||
     (failed && !reduced_success && (nonfinite||separation||spatial_baseline_sep))){
    disposition<-"Non-estimable"
  } else if(sensitivity_reversal || spatial_direction_unstable) {
    disposition<-"Sensitivity only"
  } else if(failed && reduced_success) {
    # A failed production fit is not demoted automatically if multiple
    # independent sensitivities retain the same substantive direction.
    if (spatial_evidence && isTRUE(spatial_diag_clean) &&
        !spatial_direction_unstable && !sensitivity_reversal) {
      disposition<-"Primary with caution"
    } else {
      disposition<-"Sensitivity only"
    }
  } else if(global_ph || term_ph || extreme || large_se || separation ||
            spatial_sep || spatial_baseline_sep || spatial_magnitude_unstable) {
    disposition<-"Primary with caution"
  } else if(!failed && nrow(cf)>0) {
    disposition<-"Primary"
  } else {
    disposition<-"Primary with caution"
  }
  # Retain an explicit audit trail for each triggered criterion, including when
  # spatial evidence was unavailable, and de-duplicate repeated reason strings.
  reasons<-character()
  if(failed) reasons<-c(reasons,paste0("production fit status: ",prior_status))
  if(nonfinite) reasons<-c(reasons,"non-finite coefficient/CI")
  if(extreme) reasons<-c(reasons,paste0("|log(HR)| >= ",ExtremeAbsLogHR))
  if(large_se) reasons<-c(reasons,paste0("SE >= ",LargeSE))
  if(global_ph) reasons<-c(reasons,paste0("global PH test p < ",PHAlpha))
  if(term_ph) reasons<-c(reasons,paste0("term-specific PH test p < ",PHAlpha))
  if(separation) reasons<-c(reasons,"sparse/perfect predictor stratum in DS->SF diagnostic")
  if(sensitivity_reversal) reasons<-c(reasons,"HR direction changes across primary/strict/pure-state definitions")
  if(spatial_evidence) {
    if(isTRUE(spatial_diag_clean)) reasons<-c(reasons,"v1.5 spatial diagnostic model converged cleanly")
    if(is.finite(spatial_corr_extent) && spatial_corr_extent > 0)
      reasons<-c(reasons,paste0("residual spatial dependence extends descriptively to ",spatial_corr_extent," m"))
    if(spatial_direction_unstable)
      reasons<-c(reasons,paste0("principal-term thinning direction stability < 0.80 (minimum=",round(spatial_min_dir,3),")"))
    else if(is.finite(spatial_min_dir))
      reasons<-c(reasons,paste0("principal-term thinning direction retained (minimum stability=",round(spatial_min_dir,3),")"))
    if(spatial_magnitude_unstable)
      reasons<-c(reasons,paste0("median thinning coefficient shift exceeds 0.70 (max |delta beta|=",round(spatial_max_dbeta,3),")"))
    if(spatial_sep || spatial_baseline_sep)
      reasons<-c(reasons,"v1.5 spatial sensitivity flags separation/non-finite behaviour")
  } else {
    reasons<-c(reasons,"v1.5 spatial-sensitivity evidence unavailable")
  }
  if(reduced_success && failed) reasons<-c(reasons,"at least one ordered reduced diagnostic model converged")
  if(!length(reasons)) reasons<-"no triage warning criterion triggered"
  data.frame(reach=reach_label,model=m,transition_group=tg,model_scope=model_scope_from_name(m),
             n=n,events=events,production_status=prior_status,
             coefficient_nonfinite=nonfinite,extreme_coefficient=extreme,large_uncertainty=large_se,
             global_PH_violation=global_ph,term_PH_violation=term_ph,
             sensitivity_direction_reversal=sensitivity_reversal,apparent_separation=separation,
             spatial_evidence_available=spatial_evidence,
             spatial_diagnostic_clean_convergence=spatial_diag_clean,
             residual_spatial_correlation_extent_m=spatial_corr_extent,
             spatial_min_direction_stability=spatial_min_dir,
             spatial_max_abs_median_delta_beta=spatial_max_dbeta,
             spatial_direction_unstable=spatial_direction_unstable,
             spatial_magnitude_unstable=spatial_magnitude_unstable,
             spatial_separation_flag=spatial_sep||spatial_baseline_sep,
             reduced_model_success=reduced_success,disposition=disposition,
             reasons=paste(unique(reasons),collapse="; "),stringsAsFactors=FALSE)
})
# Write one disposition per primary model. These labels aid manuscript review:
# Primary; Primary with caution; Sensitivity only; and Non-estimable.
disposition<-do.call(rbind,model_diag)
wcsv(disposition,"COX_PH_11_MODEL_DISPOSITION.csv")

# Normalise the semicolon-separated disposition rationale into individual rows
# for machine-readable review and traceability.
reason_rows<-list()
for(i in seq_len(nrow(disposition))){
  rs<-trimws(unlist(strsplit(disposition$reasons[i],";",fixed=TRUE)))
  for(r in rs) reason_rows[[length(reason_rows)+1]]<-data.frame(
    reach=disposition$reach[i],model=disposition$model[i],transition_group=disposition$transition_group[i],
    disposition=disposition$disposition[i],reason=r,stringsAsFactors=FALSE)
}
reasons_table<-if(length(reason_rows))do.call(rbind,reason_rows)else empty_df()
wcsv(reasons_table,"COX_PH_12_DISPOSITION_REASONS.csv")

# Add diagnostic flags to inventory and write last, so it is the master inventory.
# Append final disposition and diagnostic input provenance to the production
# inventory, which is written last to become the master lookup table.
inventory2<-merge(inventory,disposition[,c("model","disposition","reasons")],by="model",all.x=TRUE)
inventory2$triage_input_source<-input_source
wcsv(inventory2,"COX_PH_01_model_inventory.csv")

# -----------------------------
# 13. Machine-generated report
# -----------------------------

# Generate a human-readable run report with paths, reach identity, evidence
# alignment status, model decisions and the exact thresholds used. Timestamp
# is reporting metadata, not an input to historical analysis.
report <- c(
  "FRAF Cox / PH Model Triage v1.1",
  paste0("Generated: ",format(Sys.time(),"%Y-%m-%d %H:%M:%S %Z")),
  paste0("Reach: ",ifelse(is.na(reach_label),"<not resolved>",reach_label)),
  paste0("Historic output directory: ",historic_dir),
  paste0("Refit data source: ",ifelse(is.na(input_source),"<none; review-pack diagnostics only>",input_source)),
  paste0("Spatial sensitivity directory: ",ifelse(is.na(spatial_dir),"<not supplied>",spatial_dir)),
  paste0("Spatial sensitivity interface: ",spatial_alignment_status),
  "",
  "Interpretation rule:",
  "Reduced fits are diagnostic/sensitivity models only. This script does not replace a production specification merely because a reduced model converges.",
  "",
  "Disposition summary:"
)
# Summarise the final disposition counts and reproduce every per-model reason
# so the CSV can be checked against a compact readable log.
if(nrow(disposition)){
  tt<-table(disposition$disposition)
  report<-c(report,paste(names(tt),as.integer(tt),sep=": "))
  report<-c(report,"","Model decisions:")
  for(i in seq_len(nrow(disposition))){
    report<-c(report,paste0("- ",disposition$model[i]," [",disposition$transition_group[i],"] -> ",
                            disposition$disposition[i],": ",disposition$reasons[i]))
  }
}
report<-c(report,"",
  "Thresholds:",
  paste0("PH alpha = ",PHAlpha),
  paste0("Extreme |log(HR)| = ",ExtremeAbsLogHR),
  paste0("Large SE = ",LargeSE),
  paste0("High predictor correlation |r| = ",HighCorrelation),
  "Spatial thinning direction-instability threshold = <0.80",
  "Spatial median coefficient-shift caution threshold = |delta beta| >0.70",
  paste0("Sparse event support threshold = ",MinEventsPerTerm," events per stratum"),
  paste0("Minimum events for isolated period refit = ",MinEventsPerPeriod),
  "",
  "Key output: COX_PH_11_MODEL_DISPOSITION.csv"
)
# Retain the full diagnostic text and an explicit completion marker; the latter
# indicates this R script reached its final statement, not that every optional
# refit or spatial-sensitivity diagnostic was available or successful.
writeLines(report,file.path(out_dir,"COX_PH_TRIAGE_REPORT.txt"),useBytes=TRUE)

# Completion marker
writeLines(c(
  "FRAF_Cox_PH_Model_Triage_v1_1 completed.",
  paste0("Time: ",format(Sys.time(),"%Y-%m-%d %H:%M:%S %Z")),
  paste0("Historic input: ",historic_dir),
  paste0("Refit data source: ",ifelse(is.na(input_source),"<none>",input_source)),
  paste0("Spatial sensitivity input: ",ifelse(is.na(spatial_dir),"<none>",spatial_dir)),
  paste0("Spatial interface: ",spatial_alignment_status),
  paste0("Output: ",out_dir)
),file.path(out_dir,"COX_PH_TRIAGE_COMPLETED.txt"),useBytes=TRUE)

message("Cox/PH triage complete. Master disposition: ",
        file.path(out_dir,"COX_PH_11_MODEL_DISPOSITION.csv"))
