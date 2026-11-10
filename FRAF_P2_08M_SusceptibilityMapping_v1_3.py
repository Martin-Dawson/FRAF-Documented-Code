# -*- coding: utf-8 -*-
# FRAF Paper 2 archive module: 08M — Susceptibility Mapping (source v1.3).
# Source lineage: FRAF_Module5c_Spatial_Forecast_v1_3_PERCENTILE_RANK_TERMINOLOGY.py.
# Release policy: documentation-only renaming; QGIS algorithm ID and logic retained.
#
# PURPOSE AND POSITION IN THE WORKFLOW
# - Input: a fixed-place polygon geometry and an extracted R prediction archive.
# - Select one fitted model and forecast origin, then restore the prediction
#   scores and eligibility statuses to the same fixed-place spatial framework.
# - Output: scored/classified PLACE polygons; >=70th-percentile PLACE polygons;
#   connected dissolved risk zones derived from that selected upper-rank subset.
# - This is a mapping operation, not a Cox model, prediction refit, calibration
#   test, observed-event reconciliation, or physical erosion footprint overlay.
#
# SCIENTIFIC INTERPRETATION
# - P_PCTL is the relative rank supplied by the prediction archive (0..1);
#   a 0.90 rank is NOT a 90% probability of geomorphic transition.
# - P_PROB is a different quantity: the archive's predicted probability, when
#   available and suitable for the fitted model and forecast interval.
# - Risk classes and boundaries apply only to scored, eligible predictions;
#   'Not in risk set' and modelling failures must not be treated as low risk.
# - The 70th percentile threshold prioritises an upper-ranked portion of the
#   modelled risk population. It is not an externally calibrated hazard cutoff.
#
# INPUT/REPRODUCIBILITY CONDITIONS
# - PLACE_ID / BLOCK_ID keys must represent the same fixed-place lattice in
#   the polygon layer and prediction archive; inspect duplicate-key warnings.
# - Model, forecast label, scope and transition should isolate one prediction
#   population. The script does NOT provide an independent reach-name filter.
# - Geometries should be in an appropriate projected CRS if MIN_ZONE_AREA is
#   to be interpreted in square metres; this tool uses the layer's map units.
# - Keep source archive, origin, prediction population, thresholds and output
#   layer names in the run manifest for provenance and comparison across rivers.
"""FRAF Module 5c — Tn+1 Spatial Forecast Mapping — v1.3.

Joins one selected model/forecast from the compact prediction archive to fixed
place polygons. Produces a continuous/classified polygon layer, high-risk cells,
and dissolved generalised transition-risk zones. It does not require or use a
future observed transition overlay.

v1.3 retains the v1.2 percentile/class safeguards but presents relative risk as
percentile rank. A 90th-percentile cell is riskier than about 90% of eligible
cells; it is not interpreted as a 90% absolute transition probability.
Classes are <70th Lower, 70th-<80th Elevated, 80th-<90th High, and >=90th
Very high. The separate elevated-or-higher output contains cells at or above the 70th
percentile, matching the outer >=70th-percentile verification zone.
"""

from __future__ import annotations

import csv
import gzip
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingUtils,
    QgsWkbTypes,
)


class FRAFModule5cSpatialForecast(QgsProcessingAlgorithm):
    PLACE_POLYGONS = "PLACE_POLYGONS"
    KEY_FIELD = "KEY_FIELD"
    PREDICTION_ARCHIVE = "PREDICTION_ARCHIVE"
    MODEL_NAME = "MODEL_NAME"
    FORECAST_LABEL = "FORECAST_LABEL"
    MODEL_SCOPE = "MODEL_SCOPE"
    TRANSITION = "TRANSITION"
    MIN_ZONE_AREA = "MIN_ZONE_AREA"
    OUTPUT_CONTINUOUS = "OUTPUT_CONTINUOUS"
    OUTPUT_HIGH_CELLS = "OUTPUT_HIGH_CELLS"
    OUTPUT_ZONES = "OUTPUT_ZONES"

    # Stable QGIS Processing registry ID retained from Module 5c v1.3.
    # Renaming this archive file does not rename the registered algorithm.
    def name(self) -> str:
        return "fraf_module5c_spatial_forecast_v1_3_percentile_rank"

    # Human-readable Processing Toolbox label. The legacy module name
    # is deliberately retained for exact backward compatibility.
    def displayName(self) -> str:
        return "Module 5c — Tn+1 Spatial Forecast Mapping (v1.3 percentile-rank terminology)"

    # Processing Toolbox display group; does not affect prediction data.
    def group(self) -> str:
        return "FRAF Floodplain Reassemblage"

    # QGIS group ID used to organise this script in the toolbox.
    def groupId(self) -> str:
        return "fraf_floodplain_reassemblage"

    # QGIS requests a fresh algorithm instance for each Processing run.
    def createInstance(self):
        return FRAFModule5cSpatialForecast()

    # User-facing guidance: percentile rank is relative and only >=70th
    # percentile scored cells enter the zone-building stage.
    def shortHelpString(self) -> str:
        return (
            "Maps one process-specific prediction using relative-risk percentile rank. "
            "A 90th-percentile cell is riskier than about 90% of eligible cells; "
            "it is not a 90% absolute probability. Elevated, High and Very high "
            "cells (>=70th percentile) are dissolved into generalised predicted "
            "transition-risk zones. Places outside the risk set remain visible "
            "as 'Not in risk set'."
        )

    # Declare fixed-place polygons, join-key choice, compact prediction
    # archive, required selection labels, optional scope/transition selectors,
    # minimum zone area, and three vector outputs; do not change IDs/defaults.
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PLACE_POLYGONS,
                "Fixed place polygons",
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.KEY_FIELD,
                "Place key field",
                parentLayerParameterName=self.PLACE_POLYGONS,
                defaultValue="PLACE_ID",
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.PREDICTION_ARCHIVE,
                "Compact prediction archive (CSV or CSV.GZ)",
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Prediction archives (*.csv *.csv.gz);;All files (*.*)",
            )
        )
        # The model name and forecast label are mandatory exact-match filters.
        # Typical forecast labels may be rolling hold-out or future Tn+1 origins.
        self.addParameter(QgsProcessingParameterString(self.MODEL_NAME, "Model name"))
        self.addParameter(QgsProcessingParameterString(self.FORECAST_LABEL, "Forecast label (e.g. T10 or FUTURE_TN_PLUS_1)"))
        # Blank optional filters accept any model_scope / transition, so paired
        # archives must be checked for duplicate PLACE_ID keys before mapping.
        self.addParameter(QgsProcessingParameterString(self.MODEL_SCOPE, "Model scope (blank = any)", defaultValue=""))
        self.addParameter(QgsProcessingParameterString(self.TRANSITION, "Transition label (blank = any)", defaultValue=""))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_ZONE_AREA,
                "Minimum dissolved risk-zone area (map units squared)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )
        # Continuous output covers ALL source polygons, including non-risk-set and
        # unmatched cells; upper-rank and dissolved outputs are separately selected.
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CONTINUOUS, "Continuous and classified prediction polygons"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_HIGH_CELLS, ">=70th percentile relative-risk cells (Elevated + High + Very high)"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_ZONES, "Generalised predicted transition-risk zones"))

    # Open CSV or gzip-compressed CSV as UTF-8 with BOM-safe decoding.
    # The archive is read as text rows rather than as a spatial layer.
    @staticmethod
    def _open(path: Path):
        # Compressed and uncompressed prediction archives share identical CSV semantics.
        if path.name.lower().endswith(".gz"):
            return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
        return path.open("r", encoding="utf-8-sig", newline="")

    # Canonicalise PLACE/BLOCK identifiers for an exact text dictionary join.
    # The numeric-looking suffix ".0" is trimmed only when convertible to int;
    # non-numeric identifiers remain strings.
    @staticmethod
    def _key(value) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        # CSV export may turn numeric lattice keys into strings such as "42.0".
        # This defensively permits matching them to QGIS numeric key "42".
        if text.endswith(".0"):
            try:
                return str(int(float(text)))
            except Exception:
                pass
        return text

    # Convert candidate archive values to finite floats; return None for
    # missing, non-numeric, NaN or infinite values instead of mapping them.
    @staticmethod
    def _float(value):
        try:
            x = float(value)
            # Invalid numeric prediction values are NULL, not zero probabilities.
            return x if math.isfinite(x) else None
        except Exception:
            return None

    # Convert numeric archive flags (risk-set / observed-event) to integers.
    # Unavailable or invalid values are retained as NULL in output fields.
    @staticmethod
    def _int(value):
        try:
            return int(float(value))
        except Exception:
            return None

    # Map an existing prediction status and archive percentile to a label.
    # Status exclusions take precedence over all percentile cutoffs; classes
    # are relative rankings, not absolute probability bands.
    @staticmethod
    def _class_from_percentile(percentile, status):
        # An excluded PLACE is not evidence of low transition susceptibility.
        # Distinguish these states before testing the numerical rank thresholds.
        if status == "not_in_risk_set":
            return "Not in risk set"
        if status == "not_modelled_local_geometry":
            return "Not modelled: local geometry unavailable"
        if status == "missing_predictor":
            return "Not modelled: missing predictor"
        # Non-predicted statuses and missing ranks are excluded from ranking classes.
        if status != "predicted" or percentile is None:
            return "Model not fitted"
        # Thresholds are ordered lower-to-upper on the archive's fractional
        # percentile scale. Changing them would change the mapped risk-zone extent.
        if percentile < 0.70:
            return "Lower relative risk (<70th percentile)"
        if percentile < 0.80:
            return "Elevated relative risk (70th-<80th percentile)"
        if percentile < 0.90:
            return "High relative risk (80th-<90th percentile)"
        return "Very high relative risk (>=90th percentile)"

    # Orchestrate archive filtering, keyed lookup, map attribution, relative
    # rank selection, dissolved zone construction and lightweight join QA.
    # No model fitting or observed polygon verification occurs here.
    def processAlgorithm(self, parameters, context, feedback):
        # Read source polygon geometry once. Output scores are reattached to this
        # lattice; no geometry is taken from the non-spatial prediction archive.
        source = self.parameterAsSource(parameters, self.PLACE_POLYGONS, context)
        # Reject absent/invalid polygon sources before any archive processing.
        if source is None:
            raise QgsProcessingException("Invalid place polygon source.")
        # Capture the chosen key, archive/model selection, and minimum-zone area
        # parameter exactly as supplied to this Processing run.
        key_field = self.parameterAsString(parameters, self.KEY_FIELD, context)
        archive = Path(self.parameterAsFile(parameters, self.PREDICTION_ARCHIVE, context))
        model_name = self.parameterAsString(parameters, self.MODEL_NAME, context).strip()
        forecast_label = self.parameterAsString(parameters, self.FORECAST_LABEL, context).strip()
        model_scope = self.parameterAsString(parameters, self.MODEL_SCOPE, context).strip()
        transition = self.parameterAsString(parameters, self.TRANSITION, context).strip()
        min_zone_area = self.parameterAsDouble(parameters, self.MIN_ZONE_AREA, context)

        # The join cannot proceed unless the polygon key actually exists.
        if key_field not in source.fields().names():
            raise QgsProcessingException(f"Key field '{key_field}' is not present in place polygons.")

        # Keep the selected forecast rows in a key -> CSV-row dictionary. The
        # CSV file is scanned sequentially, but all SELECTED rows stay in memory;
        # for very large archives the selected subset determines RAM demand.
        predictions: Dict[str, Dict[str, str]] = {}
        duplicate_archive_keys = 0
        duplicate_archive_examples = []

        # Use the archive field corresponding to the user-selected polygon key.
        # Earlier versions always preferred PLACE_ID when it existed, even when
        # KEY_FIELD=BLOCK_ID, which could create subtle one-record mismatches.
        # Prefer the archive key with the same semantics as the polygon key.
        # This prevents BLOCK_ID-vs-PLACE_ID mismatch when both are available.
        key_upper = key_field.strip().upper()
        preferred_archive_key = (
            "BLOCK_ID" if key_upper == "BLOCK_ID"
            else ("PLACE_ID" if key_upper == "PLACE_ID" else key_field)
        )

        # Read the archive with DictReader so changing column order does not
        # change the meaning of named probability/rank/status fields.
        with self._open(archive) as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            # These four fields are mandatory for this mapping implementation.
            # Other attributes, including risk_percentile, may be missing/NULL, but
            # missing ranks cannot yield elevated/high risk polygon classes.
            required = {"model", "forecast_label", "model_status", "predicted_probability"}
            missing = required.difference(fieldnames)
            if missing:
                raise QgsProcessingException(
                    f"Prediction archive is missing: {', '.join(sorted(missing))}"
                )

            # The archive may use a legacy ID key. Warn when falling back so the
            # operator can confirm that identifiers still refer to identical places.
            if preferred_archive_key not in fieldnames:
                # Generic fallback only when the exact selected field is unavailable.
                fallback_key = (
                    "BLOCK_ID" if "BLOCK_ID" in fieldnames
                    else ("PLACE_ID" if "PLACE_ID" in fieldnames else None)
                )
                if fallback_key is None:
                    raise QgsProcessingException(
                        f"Prediction archive does not contain selected key '{key_field}', "
                        "BLOCK_ID, or PLACE_ID."
                    )
                feedback.pushWarning(
                    f"Selected polygon key '{key_field}' is not present in the archive; "
                    f"using archive key '{fallback_key}'."
                )
                preferred_archive_key = fallback_key

            feedback.pushInfo(
                f"Prediction archive key: {preferred_archive_key}; polygon key: {key_field}"
            )

            # Filter to the requested scenario before allocating dictionary entries.
            # No reach filter is provided: when several reaches share IDs, isolate
            # files or choose selectors that uniquely identify the intended model.
            for row in reader:
                # Exact-match model selection avoids mixing scores across model families.
                if row.get("model", "").strip() != model_name:
                    continue
                if row.get("forecast_label", "").strip() != forecast_label:
                    continue
                # Blank scope/transition parameters intentionally disable those filters.
                if model_scope and row.get("model_scope", "").strip() != model_scope:
                    continue
                if transition and row.get("transition", "").strip() != transition:
                    continue

                # Store only rows with usable fixed-place IDs. Dictionary overwrites
                # mean that the final duplicate row wins (with a QA warning afterwards).
                key = self._key(row.get(preferred_archive_key))
                if not key:
                    continue
                if key in predictions:
                    duplicate_archive_keys += 1
                    if len(duplicate_archive_examples) < 8:
                        duplicate_archive_examples.append(key)
                predictions[key] = row

        # Stop if selectors identify no rows; an empty spatial map must not be
        # misrepresented as a negative susceptibility result.
        if not predictions:
            raise QgsProcessingException(
                "No prediction rows matched the selected model, forecast label, scope and transition."
            )
        feedback.pushInfo(f"Prediction records selected: {len(predictions):,}")
        # Duplicate keys can signal mixed reaches/origins or inconsistent exports.
        # The code reports them but does not reconcile conflicting records.
        if duplicate_archive_keys:
            feedback.pushWarning(
                f"Duplicate prediction keys encountered: {duplicate_archive_keys:,}; "
                f"examples: {', '.join(duplicate_archive_examples)}. "
                "The last matching row for each duplicate key was retained."
            )

        # Retain the original polygon attributes; append only missing P_* fields.
        # This makes the output join-back compatible with the source grid.
        out_fields = QgsFields(source.fields())
        # P_STATUS records eligibility/modelling state; P_RISKSET/P_EVENT carry
        # archive flags; P_LP/P_RELHAZ/P_PROB store model values; P_PCTL and
        # P_PCTL_PC encode fractional and 0..100 relative percentile ranks.
        # P_CLASS is recalculated rather than copied from archive risk_class.
        additions = [
            QgsField("P_MODEL", QVariant.String, len=80),
            QgsField("P_FORECAST", QVariant.String, len=40),
            QgsField("P_TRANS", QVariant.String, len=100),
            QgsField("P_SCOPE", QVariant.String, len=50),
            QgsField("P_STATUS", QVariant.String, len=60),
            QgsField("P_RISKSET", QVariant.Int),
            QgsField("P_EVENT", QVariant.Int),
            QgsField("P_LP", QVariant.Double, len=20, prec=8),
            QgsField("P_RELHAZ", QVariant.Double, len=20, prec=8),
            QgsField("P_PROB", QVariant.Double, len=20, prec=8),
            QgsField("P_PCTL", QVariant.Double, len=20, prec=8),
            QgsField("P_PCTL_PC", QVariant.Double, len=10, prec=3),
            QgsField("P_CLASS", QVariant.String, len=80),
            QgsField("P_RESID", QVariant.Double, len=20, prec=8),
            QgsField("P_Y1", QVariant.String, len=30),
            QgsField("P_Y2", QVariant.String, len=30),
        ]
        # Do not duplicate a pre-existing field, but set its value when mapping.
        # The existing type will be reused if the source already has that name.
        for field in additions:
            if field.name() not in out_fields.names():
                out_fields.append(field)

        # Create (1) an all-PLACE scored/classified geometry layer and (2) an
        # upper-rank cell layer; the dissolved zone layer is created later.
        continuous_sink, continuous_id = self.parameterAsSink(
            parameters, self.OUTPUT_CONTINUOUS, context,
            out_fields, source.wkbType(), source.sourceCrs()
        )
        high_sink, high_id = self.parameterAsSink(
            parameters, self.OUTPUT_HIGH_CELLS, context,
            out_fields, source.wkbType(), source.sourceCrs()
        )
        # Explicitly reject missing sinks; individual feature write statuses to
        # these two sinks are not checked by the original v1.3 implementation.
        if continuous_sink is None or high_sink is None:
            raise QgsProcessingException("Could not create output sinks.")

        # Cache output field order and initialise join coverage, rank-class and
        # ID-uniqueness QA counters for the present Processing run.
        field_names = out_fields.names()
        total = source.featureCount() or 1
        matched = high_count = 0
        predicted_count = finite_pctl_count = 0
        class_counts = {}
        matched_prediction_keys = set()
        seen_source_keys = set()
        duplicate_source_keys = 0
        duplicate_source_examples = []

        # Visit every polygon, including places for which the model did not
        # produce a scored prediction; retain source geometry unchanged.
        for index, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break
            # Normalise the polygon identifier identically to archive identifiers.
            # Repeated source keys cause repeated mapping and a warning, not collapse.
            source_key = self._key(feature[key_field])
            if source_key in seen_source_keys:
                duplicate_source_keys += 1
                if len(duplicate_source_examples) < 8:
                    duplicate_source_examples.append(source_key)
            else:
                seen_source_keys.add(source_key)

            # Dictionary lookup is exact by fixed-place key; it performs no spatial
            # intersection and does not infer scores from neighbouring cells.
            row = predictions.get(source_key)
            # Start from the source attribute list and extend it for each P_* field;
            # position-based setAttributes requires exact correspondence with schema.
            values = list(feature.attributes())
            # Ensure source fields occupy the original positions.
            values.extend([None] * (len(out_fields) - len(values)))
            # Matched prediction records can be either predicted or explicitly
            # excluded / not fitted. Their model_status determines map category.
            if row:
                matched += 1
                matched_prediction_keys.add(source_key)
                # Use the archive's modelled-status flag and relative rank. The rank
                # is NOT calculated again within this GIS module.
                status = row.get("model_status", "")
                percentile = self._float(row.get("risk_percentile"))

                # v1.2: P_CLASS is always derived locally from P_PCTL/status.
                # Do not trust archive risk_class text for spatial selection.
                # This guarantees consistency for retrospective and genuine
                # FUTURE_TN_PLUS_1 archives and prevents valid percentile
                # predictions from producing empty High/Very-high outputs.
                # Generate P_CLASS from numeric rank/status to keep map styles and the
                # >=70th-percentile selection consistent even with stale archive labels.
                risk_class = self._class_from_percentile(percentile, status)
                # Map selected forecast metadata and scoring fields into P_* names.
                # P_PROB and P_PCTL must remain conceptually distinct quantities.
                mapped = {
                    "P_MODEL": row.get("model", ""),
                    "P_FORECAST": row.get("forecast_label", ""),
                    "P_TRANS": row.get("transition", ""),
                    "P_SCOPE": row.get("model_scope", ""),
                    "P_STATUS": status,
                    "P_RISKSET": self._int(row.get("risk_set")),
                    "P_EVENT": self._int(row.get("observed_event")),
                    "P_LP": self._float(row.get("linear_predictor")),
                    "P_RELHAZ": self._float(row.get("relative_hazard")),
                    "P_PROB": self._float(row.get("predicted_probability")),
                    "P_PCTL": percentile,
                    "P_PCTL_PC": (100.0 * percentile) if percentile is not None else None,
                    "P_CLASS": risk_class,
                    "P_RESID": self._float(row.get("prediction_residual")),
                    "P_Y1": row.get("interval_start_label", ""),
                    "P_Y2": row.get("interval_end_label", ""),
                }
                # Count actual model predictions separately from archive joins; a join
                # match does not guarantee usable percentile information.
                if status == "predicted":
                    predicted_count += 1
                    if percentile is not None:
                        finite_pctl_count += 1
                class_counts[risk_class] = class_counts.get(risk_class, 0) + 1
            else:
                mapped = {
                    "P_MODEL": model_name, "P_FORECAST": forecast_label,
                    "P_TRANS": transition, "P_SCOPE": model_scope,
                    "P_STATUS": "no_prediction_record", "P_CLASS": "No prediction record",
                }
            # Populate only the fields present in the mapped dict. Unset P_*
            # values remain NULL, especially for places without a prediction record.
            for name, value in mapped.items():
                values[field_names.index(name)] = value

            # Geometry and original place attributes are passed through unchanged.
            # There is no generalisation/simplification at individual-cell level.
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(values)
            # All fixed PLACE polygons enter the continuous map, even if they are
            # not in the selected risk population or lack a prediction.
            continuous_sink.addFeature(out_feature)
            # v1.3: Elevated + High + Very high means >=70th percentile of eligible predicted cells.
            # Percentile rank expresses relative position, not absolute probability.
            # Upper-rank selection requires BOTH predicted status and a numeric
            # rank >=0.70; it never uses P_PROB to choose this footprint.
            pctl_for_high = mapped.get("P_PCTL")
            if (
                mapped.get("P_STATUS") == "predicted"
                and pctl_for_high is not None
                and pctl_for_high >= 0.70
            ):
                # The upper-rank layer contains individual polygons for >=70th rank.
                # Selection is ordinal; it does not claim a 70% event probability.
                high_sink.addFeature(out_feature)
                high_count += 1
            # Allocate approximately 65% of Processing progress to the lattice join;
            # zone geometry operations consume the remaining run stage.
            feedback.setProgress(65.0 * (index + 1) / total)

        feedback.pushInfo(
            f"Place polygons matched: {matched:,}; predicted={predicted_count:,}; "
            f"finite P_PCTL={finite_pctl_count:,}; >=70th-percentile cells={high_count:,}"
        )
        # Summarise assigned classes to diagnose an unexpectedly empty elevated
        # subset or an inappropriate archive/model selection.
        if class_counts:
            feedback.pushInfo(
                "P_CLASS counts: " +
                "; ".join(f"{k}={v:,}" for k, v in sorted(class_counts.items()))
            )

        # A valid fixed-place lattice should normally have one feature per ID.
        # This QA warning is not itself a hard failure in original v1.3.
        if duplicate_source_keys:
            feedback.pushWarning(
                f"Duplicate polygon keys encountered: {duplicate_source_keys:,}; "
                f"examples: {', '.join(duplicate_source_examples)}."
            )

        # Check archive IDs absent from the supplied geometry. This can signal
        # mismatched grids, corridors, or an incorrectly selected population.
        unmatched_prediction_keys = sorted(
            set(predictions.keys()).difference(matched_prediction_keys)
        )
        if unmatched_prediction_keys:
            feedback.pushWarning(
                f"Prediction keys with no matching polygon: "
                f"{len(unmatched_prediction_keys):,}; examples: "
                f"{', '.join(unmatched_prediction_keys[:8])}"
            )

        # Conversely report grid polygons absent from the selected prediction
        # archive, which remain explicitly unpredicted on the continuous map.
        polygon_keys_without_prediction = seen_source_keys.difference(predictions.keys())
        if polygon_keys_without_prediction:
            feedback.pushInfo(
                f"Polygon keys with no prediction record: "
                f"{len(polygon_keys_without_prediction):,}; examples: "
                f"{', '.join(sorted(polygon_keys_without_prediction)[:8])}"
            )

        # Release completed sink handles before using the high-cell output in
        # QGIS child Processing operations.
        del continuous_sink
        del high_sink

        # Write zones through a clean sink rather than sending inherited fields
        # directly to a GeoPackage. Dissolve/multipart intermediates can carry a
        # provider FID (including QGIS temporary sentinel IDs), which caused
        # UNIQUE constraint failures when written as a GeoPackage primary key.
        # The risk-zone output has a clean schema independent of PLACE IDs and
        # provider FID values, preventing duplicate primary-key collisions.
        zone_fields = QgsFields()
        zone_fields.append(QgsField("ZONE_CLASS", QVariant.String, len=80))
        zone_fields.append(QgsField("PCTL_GE", QVariant.Double, len=10, prec=3))
        zone_fields.append(QgsField("ZONE_AREA", QVariant.Double, len=20, prec=3))

        # Create MultiPolygon risk-zone destination in the source CRS.
        # Areas are calculated in CRS squared map units, not automatically m².
        zone_sink, zone_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_ZONES,
            context,
            zone_fields,
            QgsWkbTypes.MultiPolygon,
            source.sourceCrs(),
        )
        if zone_sink is None:
            raise QgsProcessingException("Could not create risk-zone output sink.")

        zone_count = 0
        # Skip dissolve when there are no elevated/high/very-high cells.
        # The empty zone sink is still returned as an explicit output.
        if high_count > 0:
            # Dissolve selected >=70th-percentile polygons into a unified geometry.
            # No predicted physical erosion footprint or observed outcome is required.
            # Despite the label "generalised", this performs a dissolve, NOT a
            # buffer-based smoothing or cartographic simplification.
            dissolved = processing.run(
                "native:dissolve",
                {
                    "INPUT": high_id,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            # Split a potentially multipart dissolved output into separate polygon
            # components so each disconnected zone can be measured/filtered.
            single = processing.run(
                "native:multiparttosingleparts",
                {
                    "INPUT": dissolved,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            # Resolve the child algorithm output back to a feature source; the
            # fallback also supports a layer-like return object.
            single_source = QgsProcessingUtils.mapLayerFromString(str(single), context)
            if single_source is None:
                # Processing outputs may already be feature sources/layers.
                single_source = single

            # Measure each disconnected component independently. Small zones are
            # removed using MIN_ZONE_AREA, with no alternative ranking threshold.
            for zone_feature in single_source.getFeatures():
                geometry = zone_feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                # QGIS planar geometry area uses layer CRS units squared. In a metric
                # projected CRS, the result is square metres.
                zone_area = geometry.area()
                # The threshold is inclusive at equality (zones below it are dropped).
                # If MIN_ZONE_AREA=0, every non-empty polygon component is kept.
                if zone_area < float(min_zone_area):
                    continue

                # Rebuild the polygon and its three attributes, deliberately omitting
                # intermediate FIDs and cell-level scores after aggregation.
                clean_zone = QgsFeature(zone_fields)
                clean_zone.setGeometry(geometry)
                clean_zone.setAttributes([
                    "Elevated or higher relative risk (>=70th percentile)",
                    70.0,
                    float(zone_area),
                ])
                # GeoPackage write failures for dissolved zones are hard errors, unlike
                # the unchecked addFeature return values for cell-level sinks.
                if not zone_sink.addFeature(clean_zone):
                    raise QgsProcessingException(
                        "Failed while writing a cleaned transition-risk zone feature."
                    )
                zone_count += 1

        feedback.pushInfo(
            f"Generalised transition-risk zones written: {zone_count:,} "
            f"(minimum area={float(min_zone_area):g} map units²)"
        )
        del zone_sink

        # Mark completion after zone writing. No event/footprint verification or
        # held-out performance statistic is calculated by this mapping module.
        feedback.setProgress(100)
        # Return destination IDs for the full raster-like PLACE mosaic,
        # >=70th-percentile subset and dissolved susceptibility zones.
        return {
            self.OUTPUT_CONTINUOUS: continuous_id,
            self.OUTPUT_HIGH_CELLS: high_id,
            self.OUTPUT_ZONES: zone_id,
        }
