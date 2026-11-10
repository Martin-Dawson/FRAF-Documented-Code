# -*- coding: utf-8 -*-
"""FRAF Module 5b — Retrospective Prediction Validation.

Computes exact rank AUC, threshold-based average precision, Brier score,
calibration intercept/slope, risk-decile calibration and top-area capture for
R rolling-origin prediction archives. Uses SQLite staging so large archives do
not need to be held in memory.
"""


# ARCHIVAL NOTES — FRAF PAPER 2 / MODULE 08E: RETROSPECTIVE VALIDATION
# --------------------------------------------------------------------
# Role in the pipeline
# R transition-model prediction archive(s) -> optional Module 08P compact
# extraction -> this module -> discrimination, calibration and ranked-area
# capture CSVs. The input is a completed prediction archive; this module
# does not refit Cox models, reconstruct place histories, or create maps.
#
# Statistical unit and grouping
# Each eligible archive row is a scored fixed PLACE / observation interval.
# Diagnostics are calculated independently for the tuple:
# (reach, model, transition, model_scope, forecast_label, origin_rank).
# The origin labels come from the input, not from hard-coded forecast years.
# AUC, average precision (AP), Brier score and calibration use one row per
# supplied prediction and are not weighted by PLACE area. Top-area capture
# uses cell_area_m2, defaulting to 1 where no valid area is supplied.
#
# Interpretation and method boundaries
# * Discrimination: AUC uses midranks of tied probability values; AP groups
# ties by exact probability and uses precision after each score group.
# * Probability performance: Brier is mean (observed_event - probability)^2;
# calibration is a binomial-logit recalibration of the supplied probability.
# * Top-area capture: ranks fixed places by probability and counts the event
# rows / event-positive mapped area within top 10, 20 and 30% of scored
# area. These are place-level capture summaries, NOT geometric polygon
# intersections, event-footprint IoU or precision at a spatial boundary.
# * Full-area versus union-channel support, temporal exposure validity,
# training/test separation and state/risk eligibility must already have
# been established upstream; this tool does not independently verify them.
# * Outputs summarise only rows where model_status exactly matches the user-
# selected status and predicted_probability is numeric and finite.
#
# Reproducibility and compatibility
# The existing QGIS Processing algorithm ID, input fields, output column
# names, and CSV destinations are deliberately unchanged. Comments here
# document the original behaviour only: no computation, field-selection,
# error-handling, tie policy, or grouping logic has been modified.
from __future__ import annotations


# Standard-library dependencies: CSV/GZip archive reader, on-disk SQLite
# staging, numeric/statistical helpers, and temporary-file lifecycle.
import csv
import gzip
import math
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


# Only the QGIS Processing interface is required; metrics are calculated
# with Python and SQLite rather than QGIS spatial algorithms.
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputFile,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
)



# QGIS Processing entry point. One invocation reads a prediction archive,
# filters scored rows, aggregates independently by model/forecast group, and
# writes three non-spatial validation tables.
class FRAFModule5bRetrospectiveValidation(QgsProcessingAlgorithm):

    # Stable Processing parameter and result keys: retain for scripted workflows
    # and for compatibility with saved QGIS processing models.
    INPUT_ARCHIVE = "INPUT_ARCHIVE"
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    PREDICTED_STATUS = "PREDICTED_STATUS"
    OUTPUT_SUMMARY = "OUTPUT_SUMMARY"
    OUTPUT_CALIBRATION = "OUTPUT_CALIBRATION"
    OUTPUT_CAPTURE = "OUTPUT_CAPTURE"


    # Stable machine-readable algorithm identifier; not renamed with the
    # publication archive filename.
    def name(self) -> str:
        return "fraf_module5b_retrospective_validation"


    # Human-readable QGIS algorithm title (retained unchanged).
    def displayName(self) -> str:
        return "Module 5b — Retrospective Prediction Validation"


    # Toolbox menu grouping used by the QGIS Processing provider.
    def group(self) -> str:
        return "FRAF Floodplain Reassemblage"


    # Stable provider group ID, independent of the module's archive filename.
    def groupId(self) -> str:
        return "fraf_floodplain_reassemblage"


    # QGIS creates a fresh algorithm instance for each processing invocation.
    def createInstance(self):
        return FRAFModule5bRetrospectiveValidation()


    # Processing-dialog help. Its legacy T10/T20/T30 examples are labels, not
    # a restriction in the implementation: actual forecast_label/origin_rank
    # values are taken from the input rows.
    def shortHelpString(self) -> str:
        return (
            "Validates T10/T20/T30 row-level predictions. Only rows whose "
            "model_status equals the selected predicted status enter probability "
            "metrics. cell_area_m2 is used for mapped-area capture; equal unit "
            "weights are used when that field is absent or invalid."
        )


    # Declare one input archive, one output directory and the exact
    # model_status string used to select rows for statistical evaluation.
    # Three output paths are returned to QGIS after successful processing.
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(

                # A prediction file can be an ordinary UTF-8 CSV or a gzip-compressed CSV.
                # Parquet is not accepted by this module, even if 08P can produce it.
                self.INPUT_ARCHIVE,
                "Prediction archive (CSV or CSV.GZ)",
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Prediction archives (*.csv *.csv.gz);;All files (*.*)",
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "Output folder")
        )
        self.addParameter(
            QgsProcessingParameterString(

                # Only records with an EXACT match to this status are scored. Records
                # marked unavailable, not_predicted, insufficient_events, etc. are ignored.
                self.PREDICTED_STATUS,
                "Value identifying modelled predictions",
                defaultValue="predicted",
            )
        )

        # Outputs are distinct: one row per model/forecast group, multiple
        # calibration-decile rows, and multiple top-area-capture rows.
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_SUMMARY, "Validation summary CSV"))
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_CALIBRATION, "Calibration deciles CSV"))
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_CAPTURE, "Top-area capture CSV"))


    # Static helper methods do not depend on the QGIS algorithm instance.
    # They operate on archive rows and/or a temporary SQLite connection.

    # Open .gz via gzip and other accepted files as plain CSV text.
    # utf-8-sig strips an optional byte-order mark from column headings.
    @staticmethod
    def _open(path: Path):

        # The gzip/plain-text decision uses filename suffix only.
        if path.name.lower().endswith(".gz"):
            return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
        return path.open("r", encoding="utf-8-sig", newline="")


    # Coerce numeric input for prediction probability and area. Non-numeric,
    # non-finite, missing and infinite values fall back to the supplied default.
    @staticmethod
    def _float(value, default=None):
        try:
            x = float(value)

            # Exclude NaN and infinities; neither should enter SQLite score columns.
            return x if math.isfinite(x) else default
        except Exception:
            return default


    # Convert event flags to binary 0/1. This implementation treats any
    # non-zero numeric value as an event; missing/non-numeric values become 0.
    # It does not separately report the count of missing event labels.
    @staticmethod
    def _int01(value):
        try:
            return 1 if float(value) != 0 else 0
        except Exception:
            return 0


    # Build the six-key WHERE clause shared by every metric. SQL placeholders
    # bind group values safely and keep evaluation populations consistent.
    @staticmethod
    def _where_clause(group: Tuple[str, ...]) -> Tuple[str, Tuple[str, ...]]:
        cols = ("reach", "model", "transition", "model_scope", "forecast_label", "origin_rank")
        return " AND ".join(f"{c}=?" for c in cols), group


    # Compute exact, unweighted rank-based ROC AUC using the Mann–Whitney
    # rank-sum identity. Return NULL if one outcome class is absent.
    @staticmethod
    def _auc(conn: sqlite3.Connection, group: Tuple[str, ...]) -> Optional[float]:
        where, args = FRAFModule5bRetrospectiveValidation._where_clause(group)
        counts = conn.execute(
            f"SELECT SUM(y), COUNT(*)-SUM(y) FROM pred WHERE {where}", args
        ).fetchone()

        # AUC requires both observed events (positives) and non-events (negatives).
        n1 = int(counts[0] or 0)
        n0 = int(counts[1] or 0)
        if n1 == 0 or n0 == 0:
            return None

        # SQLite groups identical probabilities so tied predictions share an
        # average rank instead of receiving an arbitrary tie-breaking order.
        cursor = conn.execute(
            f"SELECT p, COUNT(*), SUM(y) FROM pred WHERE {where} GROUP BY p ORDER BY p ASC",
            args,
        )

        # Accumulate the rank sum over event-positive observations without
        # materialising all scored place rows in Python memory.
        rank_start = 1
        positive_rank_sum = 0.0
        for score, n_tie, pos_tie in cursor:
            n_tie = int(n_tie)
            pos_tie = int(pos_tie or 0)

            # Average of the consecutive ranks allocated to this equal-score tie group.
            avg_rank = rank_start + (n_tie - 1) / 2.0
            positive_rank_sum += avg_rank * pos_tie
            rank_start += n_tie

        # Normalise the positive rank sum to an ROC ranking probability in [0,1].
        return (positive_rank_sum - n1 * (n1 + 1) / 2.0) / (n1 * n0)


    # Compute score-grouped average precision (AP), equivalent to the area
    # under a stepwise precision–recall ranking curve under this tie policy.
    # AP is prevalence-sensitive; no AP lift is computed in this module.
    @staticmethod
    def _average_precision(conn: sqlite3.Connection, group: Tuple[str, ...]) -> Optional[float]:
        where, args = FRAFModule5bRetrospectiveValidation._where_clause(group)
        n_pos = conn.execute(f"SELECT SUM(y) FROM pred WHERE {where}", args).fetchone()[0] or 0
        n_pos = int(n_pos)

        # Average precision is undefined with no positive events in the group.
        if n_pos == 0:
            return None
        cursor = conn.execute(
            f"SELECT p, COUNT(*), SUM(y) FROM pred WHERE {where} GROUP BY p ORDER BY p DESC",
            args,
        )

        # Process highest modelled probabilities first, accumulating the number
        # of scored places and observed positive events in the ranked prefix.
        cum_n = 0
        cum_pos = 0
        ap = 0.0
        for score, n_tie, pos_tie in cursor:
            n_tie = int(n_tie)
            pos_tie = int(pos_tie or 0)
            cum_n += n_tie
            cum_pos += pos_tie

            # Precision is evaluated AFTER including the entire probability tie group.
            precision = cum_pos / cum_n

            # Each newly recovered event contributes its fraction of total recall,
            # multiplied by precision at that score threshold.
            ap += (pos_tie / n_pos) * precision
        return ap


    # Fit logistic recalibration: logit P(Y=1) = intercept + slope * logit(p).
    # Ideal values are intercept=0 and slope=1 for a well-calibrated model.
    # This function performs Newton iterations directly over SQLite rows.
    @staticmethod
    def _calibration(conn: sqlite3.Connection, group: Tuple[str, ...]) -> Tuple[Optional[float], Optional[float]]:
        where, args = FRAFModule5bRetrospectiveValidation._where_clause(group)
        distinct = conn.execute(
            f"SELECT COUNT(*), MIN(y), MAX(y) FROM pred WHERE {where}", args
        ).fetchone()

        # Suppress calibration coefficients if fewer than 10 rows or outcomes
        # contain only one class. There is no guarantee of stable estimation otherwise.
        if int(distinct[0] or 0) < 10 or distinct[1] == distinct[2]:
            return None, None


        # Initialise at ideal calibration (intercept zero, slope one).
        b0, b1 = 0.0, 1.0

        # At most 30 Newton–Raphson iterations. Each pass streams all rows for
        # this group; processing time can increase with very large forecasts.
        for _ in range(30):
            g0 = g1 = h00 = h01 = h11 = 0.0
            cursor = conn.execute(f"SELECT y, p FROM pred WHERE {where}", args)
            for y, p in cursor:

                # Clamp 0 and 1 probabilities away from the boundaries before logit().
                # The original archive probability is still used for Brier/AUC/AP.
                p = min(max(float(p), 1e-8), 1 - 1e-8)
                x = math.log(p / (1 - p))

                # Bound linear predictors to avoid overflow in the logistic function.
                eta = max(min(b0 + b1 * x, 35.0), -35.0)
                mu = 1.0 / (1.0 + math.exp(-eta))

                # Binomial variance weight, floored for numerical stability.
                w = max(mu * (1.0 - mu), 1e-12)
                r = float(y) - mu
                g0 += r
                g1 += r * x
                h00 += w
                h01 += w * x
                h11 += w * x * x

            # Solve the two-parameter weighted Hessian system. A near-singular
            # matrix yields unavailable calibration rather than unstable coefficients.
            det = h00 * h11 - h01 * h01
            if abs(det) < 1e-14:
                return None, None
            d0 = (g0 * h11 - g1 * h01) / det
            d1 = (g1 * h00 - g0 * h01) / det
            b0 += d0
            b1 += d1

            # Stop early once both coefficient updates are smaller than tolerance.
            if max(abs(d0), abs(d1)) < 1e-8:
                break

        # Note: the original routine returns the final coefficients even when
        # its iteration limit is reached; it does not emit convergence diagnostics.
        return b0, b1


    # Construct unweighted, equal-count risk deciles for reliability checks.
    # Decile 1 contains the lowest predicted probabilities; decile 10 the highest.
    @staticmethod
    def _deciles(conn: sqlite3.Connection, group: Tuple[str, ...]) -> List[Dict[str, object]]:
        where, args = FRAFModule5bRetrospectiveValidation._where_clause(group)
        n = int(conn.execute(f"SELECT COUNT(*) FROM pred WHERE {where}", args).fetchone()[0])

        # There is nothing to calibrate if no eligible scored rows remain.
        if n == 0:
            return []

        # For each decile retain scored-row count, event count and probability sum.
        agg = {i: [0, 0, 0.0] for i in range(1, 11)}
        cursor = conn.execute(f"SELECT y, p FROM pred WHERE {where} ORDER BY p ASC", args)
        for index, (y, p) in enumerate(cursor):

            # Rank-position assignment, not a probability-value percentile cut.
            # Tied probability values may straddle adjacent deciles.
            decile = min(10, int(index * 10 / n) + 1)
            a = agg[decile]
            a[0] += 1
            a[1] += int(y)
            a[2] += float(p)
        rows = []

        # Report mean predicted risk and observed transition frequency in each
        # non-empty group for comparison with the ideal 1:1 calibration line.
        for decile, (count, events, p_sum) in agg.items():
            if count:
                rows.append(
                    {
                        "reach": group[0], "model": group[1], "transition": group[2],
                        "model_scope": group[3], "forecast_label": group[4],
                        "origin_rank": group[5], "risk_decile": decile,
                        "n": count, "events": events,
                        "mean_predicted_probability": p_sum / count,
                        "observed_event_fraction": events / count,
                    }
                )
        return rows


    # Evaluate event capture when prioritising the highest-probability fixed
    # places by scored area. This is not mapped-footprint intersection/IoU:
    # positive place rows represent subsequent transitions and area*y is a
    # cell-weighted proxy for transition-positive area.
    @staticmethod
    def _capture(conn: sqlite3.Connection, group: Tuple[str, ...]) -> List[Dict[str, object]]:
        where, args = FRAFModule5bRetrospectiveValidation._where_clause(group)

        # Denominators include ONLY rows accepted into this validation group.
        # A larger physical-erosion footprint outside the scored population is
        # not counted in this table.
        total_area, total_event_area, total_events = conn.execute(
            f"SELECT SUM(area), SUM(area*y), SUM(y) FROM pred WHERE {where}", args
        ).fetchone()
        total_area = float(total_area or 0.0)
        total_event_area = float(total_event_area or 0.0)
        total_events = int(total_events or 0)
        if total_area <= 0:
            return []

        # Evaluate top 10%, 20% and 30% of the available scored area.
        thresholds = [0.10, 0.20, 0.30]

        # Per threshold: selected area, event-positive area and event-row count.
        captures = {t: [0.0, 0.0, 0] for t in thresholds}
        cumulative = 0.0

        # Rank by modelled probability. Equal-score ties have no specified
        # secondary ordering for boundary selection in this original code.
        cursor = conn.execute(f"SELECT y, area FROM pred WHERE {where} ORDER BY p DESC", args)
        for y, area in cursor:
            area = float(area)

            # The test is made before adding the next full PLACE area: the cell that
            # crosses a threshold is included completely. Thus selected_area_m2
            # may exceed the nominal 10/20/30% area threshold slightly.
            previous_share = cumulative / total_area
            cumulative += area
            for threshold in thresholds:
                if previous_share < threshold:
                    c = captures[threshold]
                    c[0] += area

                    # An event-positive PLACE contributes all its scored cell area. There is
                    # no partial-event polygon-area or polygon intersection calculation.
                    c[1] += area * int(y)
                    c[2] += int(y)
        rows = []
        for threshold in thresholds:
            selected_area, event_area, event_count = captures[threshold]
            rows.append(
                {
                    "reach": group[0], "model": group[1], "transition": group[2],
                    "model_scope": group[3], "forecast_label": group[4],
                    "origin_rank": group[5], "top_area_fraction": threshold,
                    "selected_area_m2": selected_area,
                    "event_count_captured": event_count,
                    "event_count_capture_fraction": event_count / total_events if total_events else "",
                    "event_area_captured_m2": event_area,
                    "event_area_capture_fraction": event_area / total_event_area if total_event_area else "",
                }
            )
        return rows


    # Main workflow: resolve paths -> create temporary SQLite database -> stream
    # and validate CSV rows -> group -> compute metrics -> write CSVs -> cleanup.
    # The algorithm reads an existing forecast archive; it does not predict.
    def processAlgorithm(self, parameters, context, feedback):
        archive = Path(self.parameterAsFile(parameters, self.INPUT_ARCHIVE, context))
        output_folder = Path(self.parameterAsString(parameters, self.OUTPUT_FOLDER, context))

        # Selection uses case-sensitive, whitespace-trimmed equality against
        # model_status. Change the parameter if an upstream archive uses another label.
        predicted_status = self.parameterAsString(parameters, self.PREDICTED_STATUS, context).strip()
        output_folder.mkdir(parents=True, exist_ok=True)


        # Retain legacy output filenames for run-manifest compatibility. Renaming
        # the Python source file does not rename these generated CSVs.
        summary_path = output_folder / "FRAF_Module5b_validation_summary.csv"
        calibration_path = output_folder / "FRAF_Module5b_calibration_deciles.csv"
        capture_path = output_folder / "FRAF_Module5b_top_area_capture.csv"


        # Stage potentially very large prediction tables on disk to avoid keeping
        # all scored PLACE rows in Python RAM. The temporary database is removed
        # in the finally block, even when processing raises an exception.
        fd, db_path = tempfile.mkstemp(prefix="fraf_m5b_", suffix=".sqlite")
        os.close(fd)
        conn = sqlite3.connect(db_path)
        try:

            # One SQLite record per accepted prediction, with six group keys and:
            # y = binary observed event, p = predicted probability, area = cell weight.
            # The archive's IDs and detailed geometry are NOT stored in this table.
            conn.execute(
                """CREATE TABLE pred (
                reach TEXT, model TEXT, transition TEXT, model_scope TEXT,
                forecast_label TEXT, origin_rank TEXT,
                y INTEGER, p REAL, area REAL
                )"""
            )

            # Use parameterised batched inserts to reduce SQLite transaction overhead.
            insert_sql = "INSERT INTO pred VALUES (?,?,?,?,?,?,?,?,?)"
            batch = []
            with self._open(archive) as handle:
                reader = csv.DictReader(handle)

                # Validate only these mandatory column headers. Other grouping fields
                # (reach, transition, model_scope, origin_rank) default to empty strings.
                required = {"model", "forecast_label", "model_status", "observed_event", "predicted_probability"}
                missing = required.difference(reader.fieldnames or [])
                if missing:
                    raise QgsProcessingException(f"Prediction archive is missing: {', '.join(sorted(missing))}")

                # Read and filter the archive incrementally; no full DataFrame is created.
                for index, row in enumerate(reader, 1):

                    # A QGIS cancellation breaks the input loop. The original implementation
                    # then proceeds to summarise any rows staged so far; it does NOT flag a
                    # partial run as an error or explicitly mark the outputs as incomplete.
                    if feedback.isCanceled():
                        break

                    # Exclude predictions not marked as fitted/scored under the selected status.
                    if str(row.get("model_status", "")).strip() != predicted_status:
                        continue
                    p = self._float(row.get("predicted_probability"))

                    # Non-finite or absent probabilities are excluded from all metrics.
                    if p is None:
                        continue
                    area = self._float(row.get("cell_area_m2"), 1.0)

                    # Missing/nonpositive cell area is replaced by 1.0, so area capture
                    # is an equal-cell approximation for those rows. Confirm area availability
                    # before interpreting capture in square metres.
                    if area is None or area <= 0:
                        area = 1.0
                    batch.append(
                        (
                            row.get("reach", ""), row.get("model", ""), row.get("transition", ""),
                            row.get("model_scope", ""), row.get("forecast_label", ""),
                            row.get("origin_rank", ""), self._int01(row.get("observed_event")),

                            # Defensively clamp otherwise-finite probabilities to the [0,1]
                            # interval before storing them in the validation database.
                            min(max(p, 0.0), 1.0), area,
                        )
                    )

                    # Commit batches of 50,000 archive rows, bounding transient memory use.
                    if len(batch) >= 50000:
                        conn.executemany(insert_sql, batch)
                        conn.commit()
                        batch.clear()

                    # Periodic QGIS progress messages indicate the number of archive rows
                    # encountered (not necessarily the number that passed filtering).
                    if index % 250000 == 0:
                        feedback.pushInfo(f"Staged {index:,} archive rows")
                if batch:
                    conn.executemany(insert_sql, batch)
                    conn.commit()

            # Indexes accelerate repeated group-filtered metrics and score sorting.
            conn.execute(
                "CREATE INDEX idx_pred_group ON pred(reach,model,transition,model_scope,forecast_label,origin_rank)"
            )
            conn.execute("CREATE INDEX idx_pred_score ON pred(p)")
            conn.commit()


            # Each distinct combination is analysed separately. This prevents
            # pooling across rivers, transition types, model scopes and forecast origins.
            groups = list(
                conn.execute(
                    "SELECT DISTINCT reach,model,transition,model_scope,forecast_label,origin_rank FROM pred "
                    "ORDER BY model,forecast_label"
                )
            )
            summary_rows = []
            calibration_rows = []
            capture_rows = []

            # One summary row per group plus its calibration and area-capture rows.
            for gi, group in enumerate(groups):
                where, args = self._where_clause(group)

                # Brier score is the unweighted mean squared probability error.
                # Event prevalence, AP lift and a prevalence-reference Brier skill score are
                # not generated by this version of the script.
                n, events, brier = conn.execute(
                    f"SELECT COUNT(*), SUM(y), AVG((y-p)*(y-p)) FROM pred WHERE {where}", args
                ).fetchone()

                # All metrics use the same SQLite group but their definedness differs:
                # AUC needs two outcome classes, AP needs events, calibration needs >=10
                # rows with both outcomes, and capture needs positive total scored area.
                intercept, slope = self._calibration(conn, group)
                summary_rows.append(
                    {
                        "reach": group[0], "model": group[1], "transition": group[2],
                        "model_scope": group[3], "forecast_label": group[4], "origin_rank": group[5],
                        "n_predictions": int(n or 0), "observed_events": int(events or 0),
                        "auc": self._auc(conn, group),
                        "average_precision": self._average_precision(conn, group),
                        "brier_score": brier,
                        "calibration_intercept": intercept,
                        "calibration_slope": slope,
                    }
                )

                # Accumulate compact result rows in memory, not all individual predictions.
                calibration_rows.extend(self._deciles(conn, group))
                capture_rows.extend(self._capture(conn, group))
                feedback.setProgress(100.0 * (gi + 1) / max(1, len(groups)))


            # Write output as CSV using the assembled row dictionaries. If the
            # result collection is empty, write an empty file rather than a header-only
            # schema; downstream readers should check for that case.
            def write_rows(path: Path, rows: List[Dict[str, object]]):
                if not rows:
                    path.write_text("", encoding="utf-8")
                    return
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)


            # Export three separately interpretable analytical outputs for Paper 2.
            write_rows(summary_path, summary_rows)
            write_rows(calibration_path, calibration_rows)
            write_rows(capture_path, capture_rows)

        # Always close the database before attempting to delete the temp file.
        finally:
            conn.close()
            try:
                os.remove(db_path)
            except OSError:
                pass


        # Return the exact CSV paths to the QGIS Processing framework.
        return {
            self.OUTPUT_SUMMARY: str(summary_path),
            self.OUTPUT_CALIBRATION: str(calibration_path),
            self.OUTPUT_CAPTURE: str(capture_path),
        }
