##FRAF Step3D v1.4.2 - Mamore DSAD Period Curvature Check=name
##Input_table=file
##Output_directory=folder
##MamoreReactivationExposure=selection Full-width channel-margin zone;Half-width channel-margin zone
# [FRAF P2 ARCHIVE / DIAG-MC / source identity]
# Publication archive name: FRAF_P2_DIAG_MamoreDSADPeriodCurvature_v1_4_2.rsx
# Exact supplied executable: Step3D_v1_4_2_DSAD_Curvature(2).rsx
# Original QGIS Processing declaration, parameter names, run labels, formulas,
# thresholds and output filenames are deliberately unchanged.
# All additions in this archive copy are documentation-only R comments.
# Analytical role: a Mamoré DS->AD historical curvature/period sensitivity,
# not a new general Cox framework and not a forecast verification model.
# The source itself explicitly refers to the final reduced v17.10.15.1 model;
# numerical identity with published results requires checking its run outputs.
##Use_robust_SE=boolean TRUE

# FRAF Step 3D v1.4.2 — Mamore DS->AD period curvature check
# -----------------------------------------------------------------------------
# PURPOSE
#   A deliberately narrow final diagnostic for the Mamore depositional-storage
#   reworking model. It does NOT run KM, AG, generic Cox triage, distance-form
#   selection, prediction, or any other transition.
#
#   It fits only the FINAL REDUCED v17.10.15.1 DS->AD specification with
#   curvature:
#
#     M2 all history:
#       DIST_CHANNEL_PREV_LINEAR_Z + MAM_OUTER_CURV_REACT_PREV_Z +
#       ASM_DOM_RATIO_PREV_Z + ASM_COV_FRAC_Z +
#       ASM_STORAGE_FRAC_PREV_Z + ASM_QUIET_SINCE_PREV_Z +
#       ASM_N_STORAGE_EVT_PREV_Z
#
#     M4 no-cutoff:
#       identical model after removing the four fixed Step-3D exceptional
#       intervals.
#
#   Each model is refitted for Early / Middle / Late thirds of the observed
#   record. The decision evidence is the direction and stability of CURVATURE,
#   with previous-margin DISTANCE reported alongside it for context.
#
# IMPORTANT
#   * Scaling mirrors v17.10.15.1 production behaviour: z-scores are learned
#     from the complete input table before DS->AD risk-set filtering.
#   * The principal/all-history model retains every observed interval.
#   * The no-cutoff sensitivity removes EXACTLY these four intervals:
#       2.002740 -> 4.002740
#       7.005479 -> 8.005479
#       15.010959 -> 16.010959
#       29.021918 -> 30.021918
#   * If any fixed interval is absent, the script stops rather than silently
#     substituting threshold-detected intervals.
#   * No automatic scientific choice is made. Output 04 records the evidence.
# -----------------------------------------------------------------------------

# [FRAF P2 / execution controls]
# Keep warning delivery and CSV output behaviour identical to the original.
# Output_directory is a caller-provided folder: files are written there using
# original Step3D142-prefixed names for provenance and reproducible comparison.
options(stringsAsFactors = FALSE, warn = 1)
dir.create(Output_directory, recursive = TRUE, showWarnings = FALSE)

msg <- function(...) { cat(paste0(...), "\n"); flush.console() }
num <- function(x) suppressWarnings(as.numeric(as.character(x)))
write_csv <- function(x, fn) utils::write.csv(x, file.path(Output_directory, fn),
                                               row.names = FALSE, na = "")

if (!requireNamespace("survival", quietly = TRUE))
  stop("Package 'survival' is required.")

# [FRAF P2 / input formats]
# Input_table may be CSV/TXT, RDS, or a spatial file handled through sf.
# For a GeoPackage, st_read(path) selects its default layer; this source does
# not expose an explicit layer-selection parameter. Confirm the supplied layer.
# Geometry is dropped: this analysis uses precomputed spatial covariates.
read_input <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("csv", "txt")) return(utils::read.csv(path, check.names = FALSE))
  if (ext == "rds") return(readRDS(path))
  if (ext %in% c("gpkg", "shp", "geojson", "sqlite")) {
    if (!requireNamespace("sf", quietly = TRUE))
      stop("Package 'sf' is required to read spatial input.")
    return(sf::st_drop_geometry(sf::st_read(path, quiet = TRUE)))
  }
  stop("Unsupported input type: .", ext)
}

# [FRAF P2 / source-field resolution]
# Case-insensitive name matching; the first available candidate wins.
# Missing required source fields cause an early stop, not silent imputation.
resolve_field <- function(nms, candidates, required = TRUE) {
  up <- toupper(nms)
  for (cand in candidates) {
    j <- match(toupper(cand), up)
    if (!is.na(j)) return(nms[j])
  }
  if (required) stop("Required field not found. Tried: ", paste(candidates, collapse = ", "))
  NA_character_
}

# [FRAF P2 / exposure standardisation]
# Mean and SD are estimated once from ALL rows in Input_table, before any
# STORAGE_REWORK_RISK_SET, event or complete-case filtering below.
# Thus a one-unit model coefficient is per input-table SD, NOT a river-wide
# physical unit or a within-risk-set SD; zero-variance fields return zeros.
zscore_production <- function(x) {
  x <- num(x)
  s <- stats::sd(x, na.rm = TRUE)
  m <- mean(x, na.rm = TRUE)
  if (!is.finite(s) || s == 0) return(rep(0, length(x)))
  (x - m) / s
}

fmt6 <- function(z) sprintf("%.6f", round(num(z), 6))

msg("[Step 3D v1.4.2] Mamore DS->AD period curvature diagnostic started.")
d <- read_input(Input_table)
nms <- names(d)

# Hard guards for the final production transition semantics.
# [FRAF P2 / transition ontology]
# DS->AD denotes reworking of Depositional Storage back into Active Domain.
# This is specifically STORAGE_REWORK_EVT within STORAGE_REWORK_RISK_SET.
# It must not be conflated with broad FP->AD prediction or SF->AD reactivation.
event_f <- resolve_field(nms, c("STORAGE_REWORK_EVT"), TRUE)
risk_f  <- resolve_field(nms, c("STORAGE_REWORK_RISK_SET"), TRUE)
id_f    <- resolve_field(nms, c("PLACE_ID"), TRUE)
dist_f  <- resolve_field(nms, c("DIST_CHANNEL_PREV"), TRUE)
start_f <- resolve_field(nms, c("TSTART_YR", "TSTART", "START_TIME",
                                "INTERVAL_START_RANK", "START_RANK"), TRUE)
stop_f  <- resolve_field(nms, c("TSTOP_YR", "TSTOP", "STOP_TIME",
                                "INTERVAL_END_RANK", "END_RANK"), TRUE)

# Final reduced raw history sources used by v17.10.15.1.
# [FRAF P2 / antecedent assemblage history]
# These five histories are treated as prior/lagged covariates, alongside
# previous-channel distance and local outer-bank curvature.
# Do not interpret these indicators as directly observed sediment properties.
history_sources <- c(
  ASM_DOM_RATIO_PREV_Z     = "ASM_DOM_RATIO_PREV",
  ASM_COV_FRAC_Z           = "ASM_COV_FRAC",
  ASM_STORAGE_FRAC_PREV_Z  = "ASM_STORAGE_FRAC_PREV",
  ASM_QUIET_SINCE_PREV_Z   = "ASM_QUIET_SINCE_PREV",
  ASM_N_STORAGE_EVT_PREV_Z = "ASM_N_STORAGE_EVT_PREV"
)
resolved_history <- vapply(history_sources, function(z) resolve_field(nms, z, TRUE), character(1))

# Mirror the production full-width / half-width curvature selector.
# [FRAF P2 / curvature-source selector: interpret with care]
# QGIS selection 0 requests full-width fallback; selection 1 requests
# half-width fallback. In BOTH branches the first candidate is the shared
# MAM_OUTER_CURV_REACT_PREV field. If that generic field exists, it will be
# selected regardless of the chosen width option. Confirm actual curv_f in
# 01_STEP3D142_input_scope_audit.csv before interpreting a width comparison.
use_half <- suppressWarnings(as.integer(MamoreReactivationExposure)[1]) == 1L
curv_candidates <- if (isTRUE(use_half)) {
  c("MAM_OUTER_CURV_REACT_PREV", "OUTER_CURV_REACT_HALF_PREV")
} else {
  c("MAM_OUTER_CURV_REACT_PREV", "OUTER_CURV_REACT_FULL_PREV")
}
curv_f <- resolve_field(nms, curv_candidates, TRUE)

# -----------------------------------------------------------------------------
# Production-aligned transformations: learn z-scores from the complete input.
# -----------------------------------------------------------------------------
# [FRAF P2 / production-aligned predictors]
# DIST_CHANNEL_PREV is a previous-channel-margin distance from the supplied
# Risk Table, not a distance recalculated from endpoint (T2) geometry here.
# Covariate timing is inherited from the supplied table, not independently
# validated by this script. Keep timing QA with the underlying Risk Table.
d$DIST_CHANNEL_PREV_LINEAR_Z <- zscore_production(d[[dist_f]])
d$MAM_OUTER_CURV_REACT_PREV_Z <- zscore_production(d[[curv_f]])
for (tm in names(history_sources)) {
  d[[tm]] <- zscore_production(d[[resolved_history[[tm]]]])
}

# Compact final-analysis table.
# [FRAF P2 / compact model data]
# One PLACE may contribute multiple chronological intervals; rows are not
# independent individual sites. IDs remain available for cluster-robust SE.
# The source reuses precomputed outcome and risk-set fields unmodified.
x <- data.frame(
  PLACE_ID = d[[id_f]],
  tstart = num(d[[start_f]]),
  tstop = num(d[[stop_f]]),
  event = num(d[[event_f]]),
  risk = num(d[[risk_f]]),
  DIST_CHANNEL_PREV_LINEAR_Z = num(d$DIST_CHANNEL_PREV_LINEAR_Z),
  MAM_OUTER_CURV_REACT_PREV_Z = num(d$MAM_OUTER_CURV_REACT_PREV_Z),
  ASM_DOM_RATIO_PREV_Z = num(d$ASM_DOM_RATIO_PREV_Z),
  ASM_COV_FRAC_Z = num(d$ASM_COV_FRAC_Z),
  ASM_STORAGE_FRAC_PREV_Z = num(d$ASM_STORAGE_FRAC_PREV_Z),
  ASM_QUIET_SINCE_PREV_Z = num(d$ASM_QUIET_SINCE_PREV_Z),
  ASM_N_STORAGE_EVT_PREV_Z = num(d$ASM_N_STORAGE_EVT_PREV_Z),
  stringsAsFactors = FALSE
)
x$.INTERVAL_KEY <- paste(fmt6(x$tstart), fmt6(x$tstop), sep = " -> ")

# [FRAF P2 / fixed model specification]
# The same seven terms are used in overall M2/M4 and all period-specific
# refits: one distance, one curvature, and five antecedent history terms.
# There is no automatic term selection or curvature-distance interaction.
final_terms <- c(
  "DIST_CHANNEL_PREV_LINEAR_Z",
  "MAM_OUTER_CURV_REACT_PREV_Z",
  "ASM_DOM_RATIO_PREV_Z",
  "ASM_COV_FRAC_Z",
  "ASM_STORAGE_FRAC_PREV_Z",
  "ASM_QUIET_SINCE_PREV_Z",
  "ASM_N_STORAGE_EVT_PREV_Z"
)

# DS->AD eligible state and valid counting-process intervals.
# [FRAF P2 / eligible risk population]
# Restrict to DS->AD exposure intervals with binary events, finite time
# coordinates and positive-length intervals. This is not a new event builder.
x <- x[is.finite(x$risk) & x$risk == 1 &
       is.finite(x$event) & x$event %in% c(0, 1) &
       is.finite(x$tstart) & is.finite(x$tstop) & x$tstop > x$tstart,
       , drop = FALSE]

# Same complete-case population for M2 and M4.
# [FRAF P2 / complete cases]
# The all-history starting population requires all seven fixed predictors.
# M4 will subsequently be a SUBSET of M2, not a separate matched-population
# model: model-fit statistics across M2 versus M4 have different sample sizes.
cc <- complete.cases(x[, final_terms, drop = FALSE]) & !is.na(x$PLACE_ID)
x <- x[cc, , drop = FALSE]
if (!nrow(x) || sum(x$event == 1, na.rm = TRUE) < 5L)
  stop("Too few complete-case Mamore DS->AD events after final-model filtering.")

# [FRAF P2 / exceptional interval sensitivity]
# The four exceptional intervals are fixed fractional-year/rank endpoints,
# formatted to six decimals. Exclusion is by (tstart,tstop) interval, not by
# selecting individual exceptional PLACE events or recomputing cutoffs.
# The analysis of all history retains these intervals by construction.
fixed_exceptional <- c(
  "2.002740 -> 4.002740",
  "7.005479 -> 8.005479",
  "15.010959 -> 16.010959",
  "29.021918 -> 30.021918"
)
# [FRAF P2 / fail-closed exceptional set]
# A missing interval may indicate a different source Risk Table or time basis.
# Deliberately stop instead of substituting differently detected events.
missing_fixed <- setdiff(fixed_exceptional, unique(x$.INTERVAL_KEY))
if (length(missing_fixed)) {
  stop("Fixed Step-3D exceptional interval(s) absent from the complete-case DS->AD population: ",
       paste(missing_fixed, collapse = "; "),
       ". Refusing to substitute another cutoff definition.")
}

# [FRAF P2 / M4 analysis scope]
# M4 excludes all eligible complete-case DS->AD records belonging to the four
# enumerated intervals, while M2 includes the complete observed record.
# M4 tests ordinary margin-controlled behaviour without these exceptional
# old-loop/cutoff reoccupation intervals; it is a sensitivity, not new history.
x_nocut <- x[!(x$.INTERVAL_KEY %in% fixed_exceptional), , drop = FALSE]

# Use common record thirds for both M2 and M4, anchored to the all-history
# complete-case population. This keeps period boundaries identical across scope.
# [FRAF P2 / temporal thirds]
# Early/Middle/Late cut points are equal elapsed-time thirds of the observed
# complete-case all-history time span. M2 and M4 use the same boundaries;
# these are not equal-event-count bins and not necessarily calendar-year thirds.
record_start <- min(x$tstart, na.rm = TRUE)
record_stop  <- max(x$tstop, na.rm = TRUE)
cuts <- seq(record_start, record_stop, length.out = 4L)
period_names <- c("Early", "Middle", "Late")

# [FRAF P2 / run provenance export]
# The first CSV documents resolved input columns, complete-case/event counts,
# curvature field and selected exposure width, removed intervals, and cuts.
# The original 'Step3D_v1.4.2' label is deliberately preserved as executable
# output provenance despite the publication-archive filename change.
input_audit <- data.frame(
  item = c("script_version", "event_field", "risk_field", "id_field", "start_field",
           "stop_field", "distance_field", "curvature_field", "curvature_exposure",
           "final_terms", "all_history_rows", "all_history_events",
           "no_cutoff_rows", "no_cutoff_events", "fixed_intervals_removed",
           "early_range", "middle_range", "late_range"),
  value = c(
    "Step3D_v1.4.2",
    event_f, risk_f, id_f, start_f, stop_f, dist_f, curv_f,
    if (use_half) "Half-width channel-margin zone" else "Full-width channel-margin zone",
    paste(final_terms, collapse = "; "),
    nrow(x), sum(x$event == 1), nrow(x_nocut), sum(x_nocut$event == 1),
    paste(fixed_exceptional, collapse = "; "),
    paste0(sprintf("%.6f", cuts[1]), " -> ", sprintf("%.6f", cuts[2])),
    paste0(sprintf("%.6f", cuts[2]), " -> ", sprintf("%.6f", cuts[3])),
    paste0(sprintf("%.6f", cuts[3]), " -> ", sprintf("%.6f", cuts[4]))
  ),
  stringsAsFactors = FALSE
)
write_csv(input_audit, "01_STEP3D142_input_scope_audit.csv")

# -----------------------------------------------------------------------------
# Fitting helpers.
# -----------------------------------------------------------------------------
# [FRAF P2 / fitted model]
# Cox counting-process Surv(tstart,tstop,event), Efron ties. If selected,
# PLACE_ID cluster-robust covariance handles repeated intervals at a PLACE,
# but does not remove spatial autocorrelation between neighbouring PLACEs.
# Fitting warnings are captured, exported, and should be reviewed with models.
fit_model <- function(dat, label) {
  rhs <- paste(final_terms, collapse = " + ")
  if (isTRUE(Use_robust_SE)) rhs <- paste0(rhs, " + survival::cluster(PLACE_ID)")
  ff <- stats::as.formula(paste0("survival::Surv(tstart, tstop, event) ~ ", rhs))
  ww <- character()
  fit <- tryCatch(
    withCallingHandlers(
      survival::coxph(
        ff, data = dat, ties = "efron", x = TRUE,
        control = survival::coxph.control(iter.max = 50, eps = 1e-8, toler.inf = 1e-8)
      ),
      warning = function(w) {
        ww <<- c(ww, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) e
  )
  list(label = label, fit = fit, warnings = paste(unique(ww), collapse = " | "), formula = ff)
}

# [FRAF P2 / coefficient reporting]
# Exponentiate beta for the hazard ratio; Wald intervals use +/-1.96 SE,
# preferring robust SE when available. This code reports only the requested
# terms; null estimates mean failed fit or term not present, not zero effect.
coef_row <- function(obj, term) {
  if (inherits(obj$fit, "error")) {
    return(data.frame(term = term, beta = NA_real_, HR = NA_real_, CI_low = NA_real_,
                      CI_high = NA_real_, SE = NA_real_, p = NA_real_, stringsAsFactors = FALSE))
  }
  sm <- try(summary(obj$fit), silent = TRUE)
  if (inherits(sm, "try-error") || is.null(sm$coefficients) ||
      !term %in% rownames(sm$coefficients)) {
    return(data.frame(term = term, beta = NA_real_, HR = NA_real_, CI_low = NA_real_,
                      CI_high = NA_real_, SE = NA_real_, p = NA_real_, stringsAsFactors = FALSE))
  }
  cf <- sm$coefficients
  beta <- as.numeric(cf[term, "coef"])
  se_col <- if ("robust se" %in% colnames(cf)) "robust se" else "se(coef)"
  se <- as.numeric(cf[term, se_col])
  p_col <- if ("Pr(>|z|)" %in% colnames(cf)) "Pr(>|z|)" else tail(colnames(cf), 1)
  p <- suppressWarnings(as.numeric(cf[term, p_col]))
  data.frame(
    term = term, beta = beta, HR = exp(beta),
    CI_low = exp(beta - 1.96 * se), CI_high = exp(beta + 1.96 * se),
    SE = se, p = p, stringsAsFactors = FALSE
  )
}

# [FRAF P2 / overall-fit QA]
# Concordance, likelihood and AIC are descriptive QA for each fit. M2 and M4
# have different populations and SHOULD NOT be interpreted as an ordinary
# same-risk-set nested likelihood/AIC comparison.
model_stat <- function(obj, scope, dat) {
  if (inherits(obj$fit, "error")) {
    return(data.frame(model = obj$label, scope = scope, status = "FAILED",
                      n = nrow(dat), events = sum(dat$event == 1),
                      logLik = NA_real_, AIC = NA_real_, concordance = NA_real_,
                      warnings = paste(conditionMessage(obj$fit), obj$warnings, sep = " | "),
                      stringsAsFactors = FALSE))
  }
  sm <- try(summary(obj$fit), silent = TRUE)
  conc <- if (!inherits(sm, "try-error") && !is.null(sm$concordance)) as.numeric(sm$concordance[1]) else NA_real_
  data.frame(model = obj$label, scope = scope, status = "OK",
             n = nrow(dat), events = sum(dat$event == 1),
             logLik = as.numeric(logLik(obj$fit)), AIC = AIC(obj$fit), concordance = conc,
             warnings = obj$warnings, stringsAsFactors = FALSE)
}

# Overall QA refits: these should reproduce the production M2/M4 direction and
# be close to its AIC/concordance, subject only to input-table equivalence.
msg("[Step 3D v1.4.2] Fitting overall M2 and M4 QA models...")
# [FRAF P2 / overall scope pair]
# M2 = all eligible observed DS->AD intervals; M4 = same specification after
# omitting the four fixed exceptional intervals. Model terms are identical.
# Overall coefficients check sign and approximate production fit consistency;
# they do not independently establish manuscript numerical reproduction.
M2 <- fit_model(x, "M2_all_history_linear_margin_plus_curvature")
M4 <- fit_model(x_nocut, "M4_no_cutoff_linear_margin_plus_curvature")
overall_stats <- rbind(model_stat(M2, "all_history", x), model_stat(M4, "no_cutoff", x_nocut))
write_csv(overall_stats, "02_STEP3D142_overall_M2_M4_QA.csv")

# [FRAF P2 / primary contextual coefficients]
# Output 03 limits reporting to previous-margin distance and outer curvature;
# the five controls remain included in both fitted Cox models.
overall_coef <- rbind(
  cbind(model = M2$label, scope = "all_history", coef_row(M2, "DIST_CHANNEL_PREV_LINEAR_Z"), stringsAsFactors = FALSE),
  cbind(model = M2$label, scope = "all_history", coef_row(M2, "MAM_OUTER_CURV_REACT_PREV_Z"), stringsAsFactors = FALSE),
  cbind(model = M4$label, scope = "no_cutoff", coef_row(M4, "DIST_CHANNEL_PREV_LINEAR_Z"), stringsAsFactors = FALSE),
  cbind(model = M4$label, scope = "no_cutoff", coef_row(M4, "MAM_OUTER_CURV_REACT_PREV_Z"), stringsAsFactors = FALSE)
)
write_csv(overall_coef, "03_STEP3D142_overall_distance_curvature_coefficients.csv")

# -----------------------------------------------------------------------------
# Decisive Early / Middle / Late diagnostic.
# -----------------------------------------------------------------------------
# [FRAF P2 / period-specific refits]
# Six planned fits: M2 Early/Middle/Late and M4 Early/Middle/Late.
# Every fit retains the same seven terms. This checks temporal stability of
# coefficient directions without assuming global proportional hazards.
period_rows <- list()
ri <- 0L
scopes <- list(all_history = x, no_cutoff = x_nocut)
model_labels <- c(all_history = "M2", no_cutoff = "M4")

for (scope_name in names(scopes)) {
  base <- scopes[[scope_name]]
  for (j in 1:3) {
    a <- cuts[j]; b <- cuts[j + 1L]
    dd <- base[base$tstart < b & base$tstop > a, , drop = FALSE]
    if (!nrow(dd)) next

    # Clip exposure to the third; retain an event only when the original event
    # time falls inside the current third.
# [FRAF P2 / interval clipping]
# A PLACE-interval can contribute exposure time to more than one third if it
# crosses a cut point. The event is allocated to the third containing its
# interval-end time. This avoids counting the same event twice across thirds.
    dd$tstart3 <- pmax(dd$tstart, a)
    dd$tstop3 <- pmin(dd$tstop, b)
    dd$event3 <- as.integer(dd$event == 1 & dd$tstop > a & dd$tstop <= b)
    dd <- dd[dd$tstop3 > dd$tstart3, , drop = FALSE]
    dd$tstart <- dd$tstart3
    dd$tstop <- dd$tstop3
    dd$event <- dd$event3

    label <- paste0(model_labels[[scope_name]], "_", period_names[j])
# [FRAF P2 / minimum support]
# Record insufficient event support as TOO_FEW_EVENTS, not an unstable estimate.
# Passing this 3-event threshold does not establish reliable seven-term fits.
    if (sum(dd$event == 1, na.rm = TRUE) < 3L) {
      ri <- ri + 1L
      period_rows[[ri]] <- data.frame(
        model = model_labels[[scope_name]], scope = scope_name, period = period_names[j],
        period_start = a, period_stop = b, n = nrow(dd), events = sum(dd$event == 1),
        fit_status = "TOO_FEW_EVENTS", warnings = "Fewer than 3 events",
        curvature_beta = NA_real_, curvature_HR = NA_real_, curvature_CI_low = NA_real_,
        curvature_CI_high = NA_real_, curvature_p = NA_real_,
        distance_beta = NA_real_, distance_HR = NA_real_, distance_CI_low = NA_real_,
        distance_CI_high = NA_real_, distance_p = NA_real_, stringsAsFactors = FALSE
      )
      next
    }

    msg("[Step 3D v1.4.2] Fitting ", label, "...")
    oo <- fit_model(dd, label)
    cur <- coef_row(oo, "MAM_OUTER_CURV_REACT_PREV_Z")
    dst <- coef_row(oo, "DIST_CHANNEL_PREV_LINEAR_Z")
    failed <- inherits(oo$fit, "error")

    ri <- ri + 1L
    period_rows[[ri]] <- data.frame(
      model = model_labels[[scope_name]], scope = scope_name, period = period_names[j],
      period_start = a, period_stop = b, n = nrow(dd), events = sum(dd$event == 1),
      fit_status = if (failed) "FAILED" else "OK",
      warnings = if (failed) paste(conditionMessage(oo$fit), oo$warnings, sep = " | ") else oo$warnings,
      curvature_beta = cur$beta, curvature_HR = cur$HR,
      curvature_CI_low = cur$CI_low, curvature_CI_high = cur$CI_high, curvature_p = cur$p,
      distance_beta = dst$beta, distance_HR = dst$HR,
      distance_CI_low = dst$CI_low, distance_CI_high = dst$CI_high, distance_p = dst$p,
      stringsAsFactors = FALSE
    )
  }
}
# [FRAF P2 / decisive period output]
# Output 04 contains six candidate period estimates, their event support,
# warnings, and distance/curvature beta, HR and confidence intervals.
# Review fit warnings and possible separation, especially in sparse periods.
period_tab <- do.call(rbind, period_rows)
write_csv(period_tab, "04_STEP3D142_M2_M4_early_middle_late_curvature_distance.csv")

# Compact evidence summary. This deliberately does not choose the final model.
# [FRAF P2 / direction-only summary]
# Sign patterns are useful for judging period stability. They are not proof
# of a constant physical curvature effect, nor a replacement for PH testing.
# The summary intentionally does not choose the production model.
summarise_scope <- function(sc) {
  z <- period_tab[period_tab$scope == sc & period_tab$fit_status == "OK", , drop = FALSE]
  cb <- z$curvature_beta[is.finite(z$curvature_beta)]
  db <- z$distance_beta[is.finite(z$distance_beta)]
  data.frame(
    scope = sc,
    periods_fitted = nrow(z),
    curvature_positive_all_periods = length(cb) == 3L && all(cb > 0),
    curvature_negative_all_periods = length(cb) == 3L && all(cb < 0),
    curvature_sign_pattern = if (length(cb)) paste(ifelse(cb > 0, "+", ifelse(cb < 0, "-", "0")), collapse = "/") else NA_character_,
    curvature_HR_pattern = if (nrow(z)) paste(sprintf("%.4f", z$curvature_HR), collapse = "/") else NA_character_,
    curvature_p_pattern = if (nrow(z)) paste(format(z$curvature_p, digits = 4, scientific = TRUE), collapse = "/") else NA_character_,
    distance_negative_all_periods = length(db) == 3L && all(db < 0),
    distance_HR_pattern = if (nrow(z)) paste(sprintf("%.4f", z$distance_HR), collapse = "/") else NA_character_,
    any_fit_warning = any(nzchar(z$warnings)),
    stringsAsFactors = FALSE
  )
}
summary_tab <- rbind(summarise_scope("all_history"), summarise_scope("no_cutoff"))
write_csv(summary_tab, "05_STEP3D142_curvature_direction_stability_summary.csv")

# [FRAF P2 / analyst interpretation aid]
# Output 06 describes the evidence to inspect; M4 is the ordinary-process
# sensitivity after removing exceptional cutoff/old-loop intervals.
# Retain the original source-specific language and output name.
writeLines(c(
  "MAMORE DS->AD PERIOD CURVATURE CHECK — STEP 3D v1.4.2",
  "",
  "Question:",
  "Does local outer-bank curvature exert a directionally persistent control on",
  "Mamore DS->AD reworking independent of previous-margin distance and exceptional",
  "cutoff/reorganisation intervals?",
  "",
  "Decision evidence:",
  "1. Read output 04 for the six Early/Middle/Late fits (M2 and M4).",
  "2. M4 is the decisive ordinary-process sensitivity.",
  "3. If curvature beta/HR remains positive (>0 / >1) in Early, Middle and Late",
  "   for M4, curvature is directionally stable after cutoff exclusion.",
  "4. A sign reversal or confinement to one period supports retaining curvature",
  "   as a time-varying sensitivity rather than a principal constant predictor.",
  "5. Significance alone is not the decision rule.",
  "",
  paste0("Fixed no-cutoff intervals: ", paste(fixed_exceptional, collapse = "; ")),
  paste0("Curvature source: ", curv_f),
  paste0("Common period cuts: ", paste(sprintf("%.6f", cuts), collapse = ", "))
), file.path(Output_directory, "06_STEP3D142_README.txt"))

# [FRAF P2 / output inventory and publication status]
# Files: 01 input scope; 02 overall M2/M4 fit QA; 03 overall distance/curvature
# coefficients; 04 period-specific estimates; 05 sign-stability summary;
# 06 interpretation README. No published result is recalculated in this archive.
# Numerical matching against the run output and supplementary text remains QA.
msg("[Step 3D v1.4.2] Complete. Primary result: 04_STEP3D142_M2_M4_early_middle_late_curvature_distance.csv")
