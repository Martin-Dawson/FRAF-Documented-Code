# -*- coding: utf-8 -*-
# PAPER 2 PUBLICATION ARCHIVE — DOCUMENTATION-ONLY COPY
# Archive filename: FRAF_P2_10_TransitionFootprintVerification_v1_3_3.py
# Original QGIS source: FRAF_Module5d_Forecast_Verification_v1_3_3_BATCH_NINE_PCTL_GE.py
#
# Position in workflow: R forecast archives -> 5a extraction -> 5c mapping ->
# 5c2 event/EA footprint construction -> THIS 5d spatial overlay verification.
# The inputs here are ALREADY predicted susceptibility zones and ALREADY mapped
# observed transition footprints. No Cox fitting, event reconstruction or
# risk-set selection is performed in this file.
#
# Analysis unit: one river, one forecast origin, one organisational transition,
# one observed y1-to-y2 interval, and one top-ranked prediction threshold.
# Default batch: 3 origins (T25/T30/T35) x 3 transitions (FP->AD, SF->AD,
# DS->AD) = nine origin/transition combinations, each at five thresholds.
#
# Interpretation: intersection-area recall, predicted-area precision and IoU
# measure geometric concordance of transition footprints with ranked zones.
# They differ from event-flag ROC AUC/AP and from physical erosion across the
# entire channel belt. Eligible FP is an operational risk population comprising
# eligible pre-existing FP and SF; it excludes DS, and is not a fourth state.
#
# IMPORTANT: Comments only were added. The original Processing ID, signatures,
# model-matching logic, fields, thresholds and calculations are unchanged.
# The source does not independently prove that input forecasts were held out,
# that all at-risk places were scored, or that the supplied footprints are correct.
# Use upstream 5c2 QA and prediction-run provenance for those checks.
"""
FRAF Module 5d — Forecast Verification v1.3.3 BATCH NINE — 5c2 v1.4 PCTL_GE

Batch version of Module 5d for the Paper 2 headline verification set.

One execution can verify the nine combinations for a single river:
    T25 / T30 / T35 x FP-AD / SF-AD / DS-AD

Inputs may be either:
  * one combined Module 5c2 percentile_zones layer and one combined
    actual_footprint layer containing all combinations; or
  * multiple 5c2 percentile_zones / actual_footprint layers selected together.

The algorithm discovers and pairs combinations from the 5c2 metadata fields
TRANSITION, FORECAST, Y1 and Y2. Current Module 5c2 v1.4 predicted zones use
PCTL_GE (percentile-rank threshold); legacy TOP_PCT inputs are also accepted.
The user-facing thresholds remain top-risk percentages, so 10 means the
>=90th-percentile zone, 20 means >=80th percentile, etc.
It filters the requested forecasts/transitions, checks that the expected number
of matched combinations is present, then runs all requested percentile
thresholds for every combination.

Rather than creating hundreds of GeoPackage layers, results are consolidated
into four layers (actual_inside, actual_missed, risk_unrealised, comparison),
with combination metadata retained as attributes. One CSV contains one row per
combination x percentile threshold.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)


# QGIS Processing algorithm registered under its ORIGINAL internal name.
# Archive renaming changes the source filename only, not the provider algorithm ID.
class FRAFModule5dForecastVerificationBatchNine(QgsProcessingAlgorithm):
    # Parameter keys form the public interface used by saved QGIS models or runs.
    # Keep them stable so previous configurations can still invoke this algorithm.
    PREDICTED_ZONES = "PREDICTED_ZONES"
    OBSERVED_TRANSITIONS = "OBSERVED_TRANSITIONS"
    FORECASTS = "FORECASTS"
    TRANSITIONS = "TRANSITIONS"
    TOP_PCTS = "TOP_PCTS"
    EXPECTED_COMBINATIONS = "EXPECTED_COMBINATIONS"
    LAYER_PREFIX = "LAYER_PREFIX"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    OUTPUT_SUMMARY = "OUTPUT_SUMMARY"

    # Return the unchanged QGIS Processing registry identifier. This is not the archive filename.
    def name(self):
        return "fraf_module5d_forecast_verification_v1_3_3_batch_nine"

    # Return the visible QGIS toolbox title, including the original version and batch scope.
    def displayName(self):
        return "Module 5d — Forecast Verification v1.3.3 (batch T25/T30/T35 × 3 transitions)"

    # Display this algorithm under the existing floodplain-toolbox group.
    def group(self):
        return "FRAF Floodplain Reassemblage"

    # Provide the persistent Processing group identifier.
    def groupId(self):
        return "fraf_floodplain_reassemblage"

    # Create a new algorithm instance when QGIS invokes the processing provider.
    def createInstance(self):
        return FRAFModule5dForecastVerificationBatchNine()

    # Describe accepted 5c2 inputs, nine-combination matching, and threshold conversion.
    def shortHelpString(self):
        return (
            "Batch-verifies the Paper 2 headline prediction set for one river. "
            "Select all relevant Module 5c2 percentile_zones layers as Predicted "
            "and all matching Module 5c2 actual_footprint layers as Observed. "
            "A single combined layer is also valid if it contains all combinations. "
            "The algorithm pairs records using TRANSITION + FORECAST + Y1 + Y2, "
            "filters the requested forecasts/transitions, and by default requires "
            "exactly nine matched combinations: T25/T30/T35 x FP-AD/SF-AD/DS-AD. "
            "Current 5c2 v1.4 PCTL_GE zones and legacy TOP_PCT zones are supported. "
            "Top-risk percentages are converted as PCTL_GE = 100 - top_pct. Results "
            "are consolidated into four GeoPackage layers plus one summary CSV."
        )

    # Declare two polygon-layer collections, selection filters, verification thresholds, an expected-combination check, and two file destinations.
    def initAlgorithm(self, config=None):
        # The predicted input is 5c2 percentile_zones (not 5c continuous cells).
        # Multiple source layers or one combined layer can contain the batch.
        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.PREDICTED_ZONES,
            "Predicted zones — select all Module 5c2 percentile_zones layers for ONE river",
            layerType=QgsProcessing.TypeVectorPolygon,
            optional=False,
        ))
        # Observed input must represent 5c2 actual_footprint, already restricted
        # upstream to the transition-specific authoritative event population.
        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.OBSERVED_TRANSITIONS,
            "Observed footprints — select all matching Module 5c2 actual_footprint layers",
            layerType=QgsProcessing.TypeVectorPolygon,
            optional=False,
        ))
        # Forecast filter is applied to metadata labels; it does not recompute
        # rolling-origin forecasts or alter train/test partitioning.
        self.addParameter(QgsProcessingParameterString(
            self.FORECASTS,
            "Forecast origins to verify (comma separated; blank = all)",
            defaultValue="T25,T30,T35",
            optional=True,
        ))
        # FP-AD is the broad eligible-floodplain forecast target; SF-AD and DS-AD
        # are distinct starting-state transitions. Other codes may be selected.
        self.addParameter(QgsProcessingParameterString(
            self.TRANSITIONS,
            "Transition codes to verify (comma separated; blank = all)",
            defaultValue="FP-AD,SF-AD,DS-AD",
            optional=True,
        ))
        # TOP_PCTS are fractions of the highest-ranked prediction population.
        # For example top 10% means PCTL_GE >= 90, NOT event probability >= 0.90.
        self.addParameter(QgsProcessingParameterString(
            self.TOP_PCTS,
            "Top-risk percentages to verify (comma separated; 10 = >=90th percentile)",
            defaultValue="2.5,5,10,20,30",
        ))
        # The default nine-combination requirement is a fail-fast completeness
        # check, not a validation of scientific correctness of the inputs.
        self.addParameter(QgsProcessingParameterNumber(
            self.EXPECTED_COMBINATIONS,
            "Expected matched combinations (0 = do not enforce)",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=9,
            minValue=0,
        ))
        # Use an output prefix to prevent accidentally mixing or confusing
        # Mamoré and Jamuna export layers within the same directory.
        self.addParameter(QgsProcessingParameterString(
            self.LAYER_PREFIX,
            "Output layer prefix (recommended: Mamore or Jamuna)",
            defaultValue="",
            optional=True,
        ))
        # The GeoPackage combines many verification jobs into four layers.
        # The CSV retains one numerical result per combination x threshold.
        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT_GPKG,
            "Batch verification GeoPackage",
            fileFilter="GeoPackage (*.gpkg)",
        ))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT_SUMMARY,
            "Batch verification summary CSV",
            fileFilter="CSV files (*.csv)",
        ))

    # ------------------------------------------------------------------
    # Parsing / metadata helpers
    # ------------------------------------------------------------------

    # Convert numeric metadata safely; reject missing/non-finite values rather than treating them as valid percentile thresholds.
    @staticmethod
    def _finite_num(value):
        try:
            x = float(value)
            return x if math.isfinite(x) else None
        except Exception:
            return None

    # Make a filesystem/GeoPackage-friendly identifier from a display label. This is for output names, not transition semantics.
    @staticmethod
    def _safe(text):
        s = str(text or "").strip().replace("->", "_to_").replace("→", "_to_")
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s

    # Normalise whitespace before comparing text labels across input layers.
    @staticmethod
    def _norm_space(value):
        return re.sub(r"\s+", " ", str(value or "").strip())

    # Canonicalise case, arrow spellings, and stabilised/stabilized for metadata joins.
    @classmethod
    def _norm_transition(cls, value):
        t = cls._norm_space(value).lower()
        # Only orthographic forms are standardised; the arrow direction remains
        # available so reactivation and storage formation are not interchangeable.
        t = t.replace("→", "->").replace("=>", "->")
        t = t.replace("stabilized", "stabilised")
        return t

    # Normalise a forecast-origin label (e.g. T25), preserving its substantive identity.
    @staticmethod
    def _norm_forecast(value):
        return str(value or "").strip().upper()

    # Canonicalise numeric-looking date labels for matching, else normalise whitespace. Does not infer missing dates.
    @classmethod
    def _norm_year(cls, value):
        n = cls._finite_num(value)
        if n is not None:
            return f"{n:.12g}"
        return cls._norm_space(value)

    # Map descriptive ontology transition labels to compact reporting codes without collapsing broad FP->AD into strict SF->AD.
    @classmethod
    def _transition_code(cls, value):
        """Map 5c/5c2 transition labels to stable Paper 2 codes."""
        t = cls._norm_transition(value)

        # Explicit mappings are preferred to heuristics: FP->AD must stay separate
        # from the strict three-state SF->AD transition in reports and figures.
        explicit = {
            "stabilised floodplain -> active domain": "SF-AD",
            "depositional storage -> active domain": "DS-AD",
            "active domain -> depositional storage": "AD-DS",
            "depositional storage -> stabilised floodplain": "DS-SF",
            "eligible floodplain -> active domain": "FP-AD",
            "broad floodplain -> active domain": "FP-AD",
            "floodplain -> active domain": "FP-AD",
            "eligible_floodplain -> active domain": "FP-AD",
        }
        if t in explicit:
            return explicit[t]

        # The fallback supports older human-readable labels, but unrecognised
        # strings become sanitised codes; inspect the selected combinations in QGIS.
        # Robust broad-FP recognition while keeping SF-AD distinct.
        if "active domain" in t and "floodplain" in t and "stabilised" not in t:
            return "FP-AD"
        if "active domain" in t and "stabilised floodplain" in t:
            return "SF-AD"
        if "depositional storage" in t and "active domain" in t:
            # Direction matters; normal 5c metadata uses an arrow.
            if t.find("depositional storage") < t.find("active domain"):
                return "DS-AD"
            return "AD-DS"
        if "depositional storage" in t and "stabilised floodplain" in t:
            return "DS-SF"

        return cls._safe(value).upper()

    # Read comma/semicolon-separated filters in user order, removing duplicates and optionally uppercasing.
    @staticmethod
    def _parse_list(text, upper=False):
        vals = []
        for token in str(text or "").replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            if upper:
                token = token.upper()
            if token not in vals:
                vals.append(token)
        return vals

    # Read requested TOP-ranked percentages; validate (0,100] and retain supplied order without duplications.
    @classmethod
    def _parse_thresholds(cls, text):
        values = []
        for token in str(text).replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            try:
                v = float(token)
            except Exception:
                raise QgsProcessingException(
                    f"Invalid TOP_PCT value '{token}'. Use e.g. 2.5,5,10,20,30."
                )
            # TOP_PCT=100 is allowed by this parser even though it represents the
            # entire population rather than a highly susceptible subset.
            if not math.isfinite(v) or v <= 0 or v > 100:
                raise QgsProcessingException(
                    f"TOP_PCT must be >0 and <=100; received {token}."
                )
            if not any(abs(v - x) <= 1e-9 for x in values):
                values.append(v)
        if not values:
            raise QgsProcessingException("No valid TOP_PCT thresholds supplied.")
        return values

    # Resolve case-insensitive metadata column names, raising an explicit error if a required field is absent.
    @staticmethod
    def _field_lookup(layer, required, label):
        # Case-insensitive field-name lookup is limited to metadata schemas.
        # It does not change the data in the input layer.
        by_upper = {name.upper(): name for name in layer.fields().names()}
        out = {}
        missing = []
        for wanted in required:
            actual = by_upper.get(wanted.upper())
            if actual is None:
                missing.append(wanted)
            else:
                out[wanted] = actual
        if missing:
            raise QgsProcessingException(
                f"{label} layer '{layer.name()}' is missing required metadata field(s): "
                + ", ".join(missing)
            )
        return out

    # Define the exact join key: canonical transition, forecast origin, interval start and interval end.
    @classmethod
    def _combo_key(cls, transition, forecast, y1, y2):
        # All four components must agree before a predicted group can be paired
        # with an observed footprint; same forecast alone is insufficient.
        return (
            cls._norm_transition(transition),
            cls._norm_forecast(forecast),
            cls._norm_year(y1),
            cls._norm_year(y2),
        )

    # Construct the human-readable combination label written into output attributes and CSV.
    @classmethod
    def _combo_id(cls, meta):
        code = cls._transition_code(meta["transition"])
        # A readable label aids the nine-combination audit and allows downstream
        # selection of individual combinations from one consolidated GeoPackage.
        forecast = cls._norm_forecast(meta["forecast"])
        y1 = cls._safe(meta["y1"])
        y2 = cls._safe(meta["y2"])
        return f"{forecast}_{code}_{y1}-{y2}"

    # ------------------------------------------------------------------
    # Memory-layer builders
    # ------------------------------------------------------------------

    # Allocate a polygon memory layer for one predicted combination. Its internal TOP_PCT field is a normalised threshold, not model probability.
    @staticmethod
    def _new_pred_group_layer(crs, name):
        # The internal TOP_PCT is intentionally uniform even when an upstream
        # v1.4 source supplies a percentile-rank lower bound instead.
        layer = QgsVectorLayer(f"MultiPolygon?crs={crs.authid()}", name, "memory")
        if not layer.isValid():
            raise QgsProcessingException(f"Could not create memory layer '{name}'.")
        layer.dataProvider().addAttributes([QgsField("TOP_PCT", QVariant.Double, len=10, prec=3)])
        layer.updateFields()
        return layer

    # Allocate an un-attributed polygon memory layer for the observed footprint of one combination.
    @staticmethod
    def _new_obs_group_layer(crs, name):
        # Observed geometry alone is used here; event/risk identities must have
        # been reconciled upstream by the 5c2 Verification Input Builder.
        layer = QgsVectorLayer(f"MultiPolygon?crs={crs.authid()}", name, "memory")
        if not layer.isValid():
            raise QgsProcessingException(f"Could not create memory layer '{name}'.")
        return layer

    # Copy and normalise valid polygon geometry to multipart representation; skip null/nonpolygon input.
    @staticmethod
    def _copy_polygon_geometry(ft):
        # Do not mutate the source feature geometry. Multipart normalisation
        # makes subsequent Native Processing polygon overlays more predictable.
        g = ft.geometry()
        if g is None or g.isEmpty():
            return None
        if QgsWkbTypes.geometryType(g.wkbType()) != QgsWkbTypes.PolygonGeometry:
            return None
        cg = QgsGeometry(g)
        try:
            if not QgsWkbTypes.isMultiType(cg.wkbType()):
                cg.convertToMultiType()
        except Exception:
            pass
        return cg

    # Discover valid 5c2 susceptibility-zone layers, standardise current/legacy threshold schemas, and group features by metadata.
    def _build_pred_groups(self, layers, target_crs, feedback):
        # Build a per-combination polygon store to avoid creating a separate
        # on-disk layer for every forecast and threshold during grouping.
        groups = {}
        total = 0

        usable_layers = 0
        current_schema_layers = 0
        legacy_schema_layers = 0
        skipped_layers = []

        # ACCEPT BOTH THRESHOLD CONVENTIONS:
        # PCTL_GE (current v1.4) stores a minimum percentile rank, e.g. 97.5.
        # TOP_PCT (legacy) stores the fraction of places selected, e.g. 2.5.
        # Both become internal TOP_PCT=100-PCTL_GE before verification.
        for layer in layers:
            # Current Module 5c2 v1.4 risk-zone outputs use PCTL_GE, where
            # 90 = highest-risk 10%, 80 = highest-risk 20%, etc.  Older 5c2/5d
            # products used TOP_PCT directly.  Normalise both to an internal
            # TOP_PCT so the overlay code is schema-independent.
            # Skip unrelated layers (such as risk cells, summaries or observed
            # footprints) rather than incorrectly treating them as predicted zones.
            by_upper = {name.upper(): name for name in layer.fields().names()}
            base_required = ["TRANSITION", "FORECAST", "Y1", "Y2"]
            missing_base = [x for x in base_required if x.upper() not in by_upper]
            has_pctl_ge = "PCTL_GE" in by_upper
            has_top_pct = "TOP_PCT" in by_upper

            if missing_base or not (has_pctl_ge or has_top_pct):
                missing = list(missing_base)
                if not (has_pctl_ge or has_top_pct):
                    missing.append("PCTL_GE/TOP_PCT")
                skipped_layers.append((layer.name(), missing))
                feedback.pushInfo(
                    f"[5d batch] Skipping predicted layer '{layer.name()}': "
                    f"not a percentile-zone layer (missing {', '.join(missing)})."
                )
                continue

            # Overlay distances and areas are planar. Require identical CRS across
            # all selected predicted layers; this module does not reproject them.
            if layer.crs() != target_crs:
                raise QgsProcessingException(
                    f"Predicted zone layer '{layer.name()}' CRS {layer.crs().authid()} does not match "
                    f"the batch CRS {target_crs.authid()}. Reproject the zone layers first."
                )

            # When both current and legacy threshold fields exist, current PCTL_GE
            # takes precedence. Source schema counts are recorded in the log.
            fld = {x: by_upper[x.upper()] for x in base_required}
            threshold_field = by_upper["PCTL_GE"] if has_pctl_ge else by_upper["TOP_PCT"]
            schema = "PCTL_GE" if has_pctl_ge else "TOP_PCT"
            usable_layers += 1
            if schema == "PCTL_GE":
                current_schema_layers += 1
            else:
                legacy_schema_layers += 1

            # Read individual zone polygons, ignoring rows with absent or nonnumeric
            # percentile metadata instead of treating them as a valid threshold.
            for ft in layer.getFeatures():
                raw = self._finite_num(ft[threshold_field])
                if raw is None:
                    continue

                # Conversion is from percentile rank to top-area/rank selection label;
                # it is not conversion to an absolute probability.
                if schema == "PCTL_GE":
                    # Current percentile-rank terminology: >=97.5th = top 2.5%,
                    # >=95th = top 5%, >=90th = top 10%, etc.
                    pct = 100.0 - float(raw)
                else:
                    pct = float(raw)

                if not math.isfinite(pct) or pct <= 0 or pct > 100:
                    continue

                # The grouping key includes transition AND the precise forecast interval;
                # these attributes are copied from 5c2 outputs, not inferred from filenames.
                transition = ft[fld["TRANSITION"]]
                forecast = ft[fld["FORECAST"]]
                y1 = ft[fld["Y1"]]
                y2 = ft[fld["Y2"]]
                key = self._combo_key(transition, forecast, y1, y2)
                g = self._copy_polygon_geometry(ft)
                if g is None:
                    continue

                # Create one group on first valid observation, preserving source-layer
                # names for the final CSV provenance columns.
                if key not in groups:
                    meta = {
                        "transition": str(transition),
                        "forecast": str(forecast),
                        "y1": str(y1),
                        "y2": str(y2),
                    }
                    groups[key] = {
                        "layer": self._new_pred_group_layer(target_crs, f"pred_{len(groups)+1}"),
                        "meta": meta,
                        "available_pcts": set(),
                        "source_layers": set(),
                        "buffer": [],
                    }

                # Stage only geometry and normalised threshold in memory; attributes
                # not used in overlays are omitted to reduce processing overhead.
                nf = QgsFeature(groups[key]["layer"].fields())
                nf.setGeometry(g)
                nf.setAttributes([float(pct)])
                groups[key]["buffer"].append(nf)
                groups[key]["available_pcts"].add(float(pct))
                groups[key]["source_layers"].add(layer.name())
                total += 1

                # Flush features in batches of 5,000 rather than appending all source
                # features to one large Python list.
                if len(groups[key]["buffer"]) >= 5000:
                    groups[key]["layer"].dataProvider().addFeatures(
                        groups[key]["buffer"], QgsFeatureSink.FastInsert
                    )
                    groups[key]["buffer"] = []

        # Ensure each group has complete geometry and current extents before
        # Native Processing child algorithms query it.
        for info in groups.values():
            if info["buffer"]:
                info["layer"].dataProvider().addFeatures(info["buffer"], QgsFeatureSink.FastInsert)
                info["buffer"] = []
            info["layer"].updateExtents()

        # No valid predicted layers is a hard error even if unrelated selected
        # layers are merely skipped with warnings.
        if usable_layers == 0:
            skipped = "; ".join(
                f"{name} (missing {', '.join(missing)})" for name, missing in skipped_layers
            )
            raise QgsProcessingException(
                "None of the selected predicted layers is a usable percentile-zone layer. "
                "Current Module 5c2 v1.4 requires TRANSITION, FORECAST, Y1, Y2 and PCTL_GE "
                "(legacy TOP_PCT is also accepted). Selected/skipped: " + skipped
            )

        # Report how much of the supplied layer set was usable, and whether
        # legacy TOP_PCT values entered the comparison.
        feedback.pushInfo(
            f"[5d batch] Predicted input: {len(layers)} selected; {usable_layers} usable "
            f"percentile-zone layer(s) ({current_schema_layers} current PCTL_GE, "
            f"{legacy_schema_layers} legacy TOP_PCT); {len(skipped_layers)} skipped; "
            f"{total:,} usable polygon(s); {len(groups)} metadata combination(s)."
        )
        return groups

    # Discover observed dissolved-footprint layers and pair their spatial records by the same four metadata keys.
    def _build_obs_groups(self, layers, target_crs, feedback):
        # Observed footprints are grouped without threshold: one footprint for
        # each (transition, forecast, y1, y2) is reused across all selected thresholds.
        groups = {}
        total = 0

        usable_layers = 0
        skipped_layers = []
        for layer in layers:
            # Identify actual 5c2 dissolved observed-footprint metadata fields.
            # A layer with only geometric process pieces is not the required target.
            by_upper = {name.upper(): name for name in layer.fields().names()}
            required = ["TRANSITION", "FORECAST", "Y1", "Y2"]
            missing = [x for x in required if x.upper() not in by_upper]

            # 5c2 observed_parts can carry RISK_FLD; the dissolved footprint does
            # not. This code uses that schema distinction as its exclusion rule.
            # 5cv may also expose observed_parts_* (process-specific pieces).
            # Those carry RISK_FLD, whereas the dissolved observed_* footprint does not.
            if "RISK_FLD" in by_upper:
                skipped_layers.append((layer.name(), ["dissolved footprint (RISK_FLD present)"]))
                feedback.pushInfo(
                    f"[5d batch] Skipping observed layer '{layer.name()}': "
                    "process-specific observed_parts layer, not dissolved observed footprint."
                )
                continue

            if missing:
                skipped_layers.append((layer.name(), missing))
                feedback.pushInfo(
                    f"[5d batch] Skipping observed layer '{layer.name()}': "
                    f"not a 5c2 actual_footprint layer (missing {', '.join(missing)})."
                )
                continue

            # Observed polygons must use the same CRS as predicted zones, because
            # intersection and difference use their coordinates directly.
            if layer.crs() != target_crs:
                raise QgsProcessingException(
                    f"Observed 5c2 layer '{layer.name()}' CRS {layer.crs().authid()} does not match "
                    f"the batch CRS {target_crs.authid()}. Reproject the 5c2 layers first."
                )

            fld = {x: by_upper[x.upper()] for x in required}
            usable_layers += 1
            # Group geometries by exactly the same metadata-normalised interval key
            # as the prediction zones. No nearest-interval substitution is performed.
            for ft in layer.getFeatures():
                transition = ft[fld["TRANSITION"]]
                forecast = ft[fld["FORECAST"]]
                y1 = ft[fld["Y1"]]
                y2 = ft[fld["Y2"]]
                key = self._combo_key(transition, forecast, y1, y2)
                g = self._copy_polygon_geometry(ft)
                if g is None:
                    continue

                # Attach only geometry to each observed group: the combination ID is
                # maintained separately and reattached when results are exported.
                if key not in groups:
                    meta = {
                        "transition": str(transition),
                        "forecast": str(forecast),
                        "y1": str(y1),
                        "y2": str(y2),
                    }
                    groups[key] = {
                        "layer": self._new_obs_group_layer(target_crs, f"obs_{len(groups)+1}"),
                        "meta": meta,
                        "source_layers": set(),
                        "buffer": [],
                    }

                nf = QgsFeature(groups[key]["layer"].fields())
                nf.setGeometry(g)
                groups[key]["buffer"].append(nf)
                groups[key]["source_layers"].add(layer.name())
                total += 1

                # Batch-write observed polygons to in-memory layers to avoid materialising
                # large duplicated attribute tables.
                if len(groups[key]["buffer"]) >= 5000:
                    groups[key]["layer"].dataProvider().addFeatures(
                        groups[key]["buffer"], QgsFeatureSink.FastInsert
                    )
                    groups[key]["buffer"] = []

        for info in groups.values():
            if info["buffer"]:
                info["layer"].dataProvider().addFeatures(info["buffer"], QgsFeatureSink.FastInsert)
                info["buffer"] = []
            info["layer"].updateExtents()

        # Zero usable observed footprint layers is an error: verification cannot
        # proceed with predicted zones alone.
        if usable_layers == 0:
            skipped = "; ".join(
                f"{name} (missing {', '.join(missing)})" for name, missing in skipped_layers
            )
            raise QgsProcessingException(
                "None of the selected observed layers is a Module 5c2 actual_footprint "
                "layer. A usable observed layer must contain TRANSITION, FORECAST, Y1 and "
                "Y2. Selected/skipped: " + skipped
            )

        # Emit observed-input counts for audit against upstream 5c2 QA outputs.
        feedback.pushInfo(
            f"[5d batch] Observed input: {len(layers)} selected; {usable_layers} usable "
            f"5c2 actual_footprint layer(s); {len(skipped_layers)} skipped; "
            f"{total:,} usable polygon(s); {len(groups)} metadata combination(s)."
        )
        return groups

    # Sum QGIS planar polygon areas for the supplied geometry collection. Overlay inputs are dissolved before metric calculation.
    @staticmethod
    def _area(source):
        # This is a sum of feature geometry area in source CRS squared units;
        # if polygon parts overlap, naive area sums can double-count overlap.
        total = 0.0
        for ft in source.getFeatures():
            if ft.hasGeometry() and not ft.geometry().isEmpty():
                a = ft.geometry().area()
                if math.isfinite(a):
                    total += a
        return float(total)

    # Resolve child-algorithm temporary output IDs to feature sources without copying results unnecessarily.
    @staticmethod
    def _as_layer(obj, context):
        if hasattr(obj, "getFeatures"):
            # Processing may return either a layer-like object or a temporary layer ID.
            # Resolve the latter through the live Processing context.
            return obj
        lyr = context.getMapLayer(obj)
        if lyr is None:
            raise QgsProcessingException(f"Could not resolve temporary layer: {obj}")
        return lyr

    # Materialise only the features of one matched forecast/transition and one requested top-risk threshold.
    def _materialise_pred_pct(self, group_layer, pct, name, feedback=None):
        # One local memory layer is built for each threshold; this avoids
        # altering the reusable parent predicted group while performing overlays.
        layer = QgsVectorLayer(
            f"MultiPolygon?crs={group_layer.crs().authid()}", name, "memory"
        )
        if not layer.isValid():
            raise QgsProcessingException(f"Could not create memory layer '{name}'.")

        batch = []
        matched = 0
        # Threshold comparison tolerates floating-point conversion noise but
        # does not interpolate an unavailable threshold from other zones.
        for ft in group_layer.getFeatures():
            v = self._finite_num(ft["TOP_PCT"])
            if v is None or abs(v - pct) > 1e-9:
                continue
            g = self._copy_polygon_geometry(ft)
            if g is None:
                continue
            nf = QgsFeature(layer.fields())
            nf.setGeometry(g)
            batch.append(nf)
            matched += 1
            if len(batch) >= 5000:
                layer.dataProvider().addFeatures(batch, QgsFeatureSink.FastInsert)
                batch = []
        if batch:
            layer.dataProvider().addFeatures(batch, QgsFeatureSink.FastInsert)
        layer.updateExtents()

        # Fail on absent threshold geometry rather than silently reporting a
        # zero-prediction area for a requested rank band.
        if matched == 0:
            raise QgsProcessingException(f"No predicted polygons matched TOP_PCT={pct:g}.")
        if feedback:
            feedback.pushInfo(f"[5d batch] Materialised P{pct:g}: {matched:,} polygon(s).")
        return layer

    # ------------------------------------------------------------------
    # Consolidated output layers
    # ------------------------------------------------------------------

    # Define a compact common schema for all four exported overlay layers, including source provenance and threshold information.
    @staticmethod
    def _result_fields():
        # Identical field definitions across four result layers allow one map
        # legend to select categories while filtering by COMBO_ID or TOP_PCT.
        f = QgsFields()
        f.append(QgsField("COMBO_ID", QVariant.String, len=140))
        f.append(QgsField("TRANSITION", QVariant.String, len=120))
        f.append(QgsField("TRANS_CODE", QVariant.String, len=20))
        f.append(QgsField("FORECAST", QVariant.String, len=30))
        f.append(QgsField("Y1", QVariant.String, len=40))
        f.append(QgsField("Y2", QVariant.String, len=40))
        f.append(QgsField("VERIFY_CL", QVariant.String, len=70))
        # Store both percent selected and minimum percentile-rank threshold:
        # TOP_PCT=10 corresponds to PCTL_GE=90.
        f.append(QgsField("TOP_PCT", QVariant.Double, len=10, prec=3))
        f.append(QgsField("PCTL_GE", QVariant.Double, len=10, prec=3))
        f.append(QgsField("AREA_M2", QVariant.Double, len=20, prec=3))
        return f

    # Create an in-memory polygon output collector using the shared verification-result schema.
    def _new_result_layer(self, crs, name):
        # The four geometry categories are built as separate memory layers,
        # then written to one GeoPackage at the end.
        layer = QgsVectorLayer(f"MultiPolygon?crs={crs.authid()}", name, "memory")
        if not layer.isValid():
            raise QgsProcessingException(f"Could not create result layer '{name}'.")
        layer.dataProvider().addAttributes(list(self._result_fields()))
        layer.updateFields()
        return layer

    # Copy overlay geometries into a consolidated output layer and stamp the combination, threshold and geometric category.
    def _append_result(self, target, source_obj, meta, label, pct, context):
        # Each output feature carries its source combination, comparison class,
        # area, and both threshold notations; original model scores are not reattached.
        src = self._as_layer(source_obj, context)
        combo_id = self._combo_id(meta)
        code = self._transition_code(meta["transition"])
        batch = []
        # Geometry is copied rather than referencing temporary overlay output,
        # which may be destroyed when the Processing context closes.
        for ft in src.getFeatures():
            g = ft.geometry()
            if g is None or g.isEmpty():
                continue
            cg = QgsGeometry(g)
            try:
                if not QgsWkbTypes.isMultiType(cg.wkbType()):
                    cg.convertToMultiType()
            except Exception:
                pass
            nf = QgsFeature(target.fields())
            nf.setGeometry(cg)
            # Comparison labels distinguish actual captured, actual missed and
            # predicted-zone area without a mapped transition in this interval.
            nf.setAttributes([
                combo_id,
                str(meta["transition"]),
                code,
                self._norm_forecast(meta["forecast"]),
                str(meta["y1"]),
                str(meta["y2"]),
                label,
                float(pct),
                float(100.0 - pct),
                float(cg.area()),
            ])
            batch.append(nf)
            if len(batch) >= 5000:
                target.dataProvider().addFeatures(batch, QgsFeatureSink.FastInsert)
                batch = []
        if batch:
            target.dataProvider().addFeatures(batch, QgsFeatureSink.FastInsert)
        target.updateExtents()

    # Save one consolidated output layer to GeoPackage; create file on first call and replace individual layers thereafter.
    @staticmethod
    def _write_gpkg(layer, path, layer_name, context, first=False):
        # The first write creates the package; later writes replace only the
        # named layers. Existing file contents should not be treated as immutable.
        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = "GPKG"
        opts.fileEncoding = "UTF-8"
        opts.layerName = layer_name
        # QgsVectorFileWriter action differs by file vs layer to avoid destroying
        # the prior outputs of this same batch.
        opts.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteFile
            if first else QgsVectorFileWriter.CreateOrOverwriteLayer
        )
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, str(path), context.transformContext(), opts
        )
        if result[0] != QgsVectorFileWriter.NoError:
            msg = result[1] if len(result) > 1 else "Unknown writer error"
            raise QgsProcessingException(
                f"Could not write GeoPackage layer '{layer_name}': {msg}"
            )

    # ------------------------------------------------------------------
    # Main algorithm
    # ------------------------------------------------------------------

    # Orchestrate input checks, pairing, percentile overlay, geometric metrics, and consolidated spatial/CSV outputs.
    def processAlgorithm(self, parameters, context, feedback):
        # Both sets of inputs are required. They should belong to ONE river;
        # no automatic river identifier is used to prevent cross-river mixing.
        predicted_layers = self.parameterAsLayerList(parameters, self.PREDICTED_ZONES, context)
        observed_layers = self.parameterAsLayerList(parameters, self.OBSERVED_TRANSITIONS, context)
        if not predicted_layers:
            raise QgsProcessingException("No predicted percentile_zones layer(s) supplied.")
        if not observed_layers:
            raise QgsProcessingException("No observed actual_footprint layer(s) supplied.")

        # Find the CRS of the first valid predicted percentile-zone layer,
        # not simply the first input item (which may be an unrelated map layer).
        # Derive the batch CRS from the first genuine percentile-zone layer.
        # Current 5c2 v1.4 uses PCTL_GE; legacy products may use TOP_PCT.
        target_crs = None
        base_required = {"TRANSITION", "FORECAST", "Y1", "Y2"}
        for lyr in predicted_layers:
            present = {name.upper() for name in lyr.fields().names()}
            if base_required.issubset(present) and (
                "PCTL_GE" in present or "TOP_PCT" in present
            ):
                target_crs = lyr.crs()
                break
        if target_crs is None:
            raise QgsProcessingException(
                "No selected predicted layer contains TRANSITION, FORECAST, Y1, Y2 plus "
                "PCTL_GE (current Module 5c2 v1.4) or TOP_PCT (legacy)."
            )
        # A valid projected CRS is preferable for m^2 metrics; the source does
        # not independently assert that the chosen CRS has metre units.
        if not target_crs.isValid():
            raise QgsProcessingException("The first usable percentile-zone input has no valid CRS.")

        # Examples: top 2.5%=PCTL_GE>=97.5; 5%=95; 10%=90; 20%=80; 30%=70.
        top_pcts = self._parse_thresholds(
            self.parameterAsString(parameters, self.TOP_PCTS, context)
        )
        # Blank filter lists mean ALL available forecasts/transitions; they do
        # not mean no results. Filtering occurs after layer grouping.
        forecast_filter = {
            self._norm_forecast(x)
            for x in self._parse_list(
                self.parameterAsString(parameters, self.FORECASTS, context), upper=True
            )
        }
        transition_filter = {
            x.upper()
            for x in self._parse_list(
                self.parameterAsString(parameters, self.TRANSITIONS, context), upper=True
            )
        }
        # Expected-combination enforcement may be set to zero for a partial
        # batch or sensitivity run without changing other calculations.
        expected = int(self.parameterAsInt(parameters, self.EXPECTED_COMBINATIONS, context))

        # Both destinations are created under their requested parent folders.
        # The GeoPackage write uses overwrite semantics described in _write_gpkg.
        gpkg_path = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context))
        summary_path = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_SUMMARY, context))
        gpkg_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        feedback.pushInfo(
            "[5d batch] Forecast filter: "
            + (", ".join(sorted(forecast_filter)) if forecast_filter else "ALL")
        )
        feedback.pushInfo(
            "[5d batch] Transition filter: "
            + (", ".join(sorted(transition_filter)) if transition_filter else "ALL")
        )
        feedback.pushInfo(
            "[5d batch] Top-risk thresholds: "
            + ", ".join(f"top {x:g}% (PCTL_GE={100.0-x:g})" for x in top_pcts)
        )

        # Build all groups before joining to identify missing observations,
        # inconsistent metadata, and missing requested percentile thresholds.
        pred_groups = self._build_pred_groups(predicted_layers, target_crs, feedback)
        obs_groups = self._build_obs_groups(observed_layers, target_crs, feedback)

        # Keep a grouped combination only when it satisfies the optional forecast and transition code filters.
        def selected(key, info):
            # Local selector filters by metadata. Its selection is independent of
            # whether a given group has valid observed geometry or percentile levels.
            meta = info["meta"]
            forecast = self._norm_forecast(meta["forecast"])
            code = self._transition_code(meta["transition"]).upper()
            if forecast_filter and forecast not in forecast_filter:
                return False
            if transition_filter and code not in transition_filter:
                return False
            return True

        # A selected batch is a subset of all discovered combinations. That
        # subset is the population checked against EXPECTED_COMBINATIONS.
        pred_selected = {k: v for k, v in pred_groups.items() if selected(k, v)}
        obs_selected = {k: v for k, v in obs_groups.items() if selected(k, v)}

        # Set intersection is a STRICT matched comparison: forecast, transition,
        # start and end date must all agree. Do not use cross-interval overlays.
        pred_keys = set(pred_selected)
        obs_keys = set(obs_selected)
        matched_keys = sorted(pred_keys & obs_keys, key=lambda k: (k[1], self._transition_code(pred_selected[k]["meta"]["transition"]), k[2], k[3]))
        missing_obs = sorted(pred_keys - obs_keys)
        missing_pred = sorted(obs_keys - pred_keys)

        # If any requested predicted combination lacks an observed footprint,
        # stop rather than biasing results toward only available observations.
        if missing_obs:
            details = "; ".join(self._combo_id(pred_selected[k]["meta"]) for k in missing_obs)
            raise QgsProcessingException(
                "Selected predicted combination(s) have no matching actual_footprint: " + details
            )
        # Conversely, an observed-only combination is also treated as missing
        # required prediction evidence, not as a zero-susceptibility area.
        if missing_pred:
            details = "; ".join(self._combo_id(obs_selected[k]["meta"]) for k in missing_pred)
            raise QgsProcessingException(
                "Selected observed combination(s) have no matching percentile_zones: " + details
            )
        if not matched_keys:
            raise QgsProcessingException(
                "No matched forecast/transition combinations remain after filtering."
            )
        # A correct count of nine is necessary under default settings, but the
        # labels printed below must also be inspected to detect unexpected combinations.
        if expected > 0 and len(matched_keys) != expected:
            details = "; ".join(self._combo_id(pred_selected[k]["meta"]) for k in matched_keys)
            raise QgsProcessingException(
                f"Expected {expected} matched combinations but found {len(matched_keys)}. "
                f"Matched: {details}"
            )

        feedback.pushInfo(f"[5d batch] Matched combinations: {len(matched_keys)}")
        for i, key in enumerate(matched_keys, start=1):
            feedback.pushInfo(
                f"[5d batch]   {i}. {self._combo_id(pred_selected[key]['meta'])}"
            )

        # Check all five percentile thresholds in every matched combination
        # BEFORE starting costly polygon operations. No synthetic interpolation.
        # Check all requested thresholds before any expensive overlay work.
        missing_pct_messages = []
        for key in matched_keys:
            available = pred_selected[key]["available_pcts"]
            missing = [
                p for p in top_pcts
                if not any(abs(p - a) <= 1e-9 for a in available)
            ]
            if missing:
                missing_pct_messages.append(
                    self._combo_id(pred_selected[key]["meta"]) + ": "
                    + ", ".join(f"P{x:g}" for x in missing)
                )
        if missing_pct_messages:
            raise QgsProcessingException(
                "Requested top-risk percentage(s) are missing from one or more combinations "
                "(current 5c2 mapping is PCTL_GE = 100 - top_pct): "
                + "; ".join(missing_pct_messages)
            )

        # Retain the input prefix or derive it, and append _5d to the output
        # layer names to signal their spatial-verification provenance.
        user_prefix = self.parameterAsString(parameters, self.LAYER_PREFIX, context).strip()
        if user_prefix:
            prefix = self._safe(user_prefix)
        else:
            prefix = self._safe(predicted_layers[0].name()) or "FRAF_5d_batch"
        if not prefix.lower().endswith("5d"):
            prefix = f"{prefix}_5d"

        # Geometric partitions:
        # actual_inside = observed intersection predicted;
        # actual_missed = observed minus predicted;
        # risk_unrealised = predicted minus observed;
        # comparison = all three pieces combined for mapping.
        inside_out = self._new_result_layer(target_crs, "actual_inside")
        missed_out = self._new_result_layer(target_crs, "actual_missed")
        unrealised_out = self._new_result_layer(target_crs, "risk_unrealised")
        comparison_out = self._new_result_layer(target_crs, "comparison")

        # Each row is a unique observed/predicted combination at one requested
        # threshold; default total is 9 combinations x 5 thresholds = 45 rows.
        rows = []
        total_jobs = len(matched_keys) * len(top_pcts)
        completed = 0

        # Outer loop is forecast x transition x interval. The same observed
        # footprint is compared with nested susceptibility zones at several ranks.
        for combo_index, key in enumerate(matched_keys, start=1):
            if feedback.isCanceled():
                break

            # Source provenance is kept for reporting, even though the geometries
            # are copied to temporary working layers for spatial overlay.
            pred_info = pred_selected[key]
            obs_info = obs_selected[key]
            meta = pred_info["meta"]
            combo_id = self._combo_id(meta)
            code = self._transition_code(meta["transition"])

            feedback.pushInfo(
                f"[5d batch] ===== Combination {combo_index}/{len(matched_keys)}: {combo_id} ====="
            )

            # Repair and dissolve the OBSERVED transition footprint only once per
            # combination. This avoids repeating identical expensive geometry operations.
            # Repair and dissolve each observed footprint once, then reuse for all thresholds.
            observed_fixed = processing.run(
                "native:fixgeometries",
                {
                    "INPUT": obs_info["layer"],
                    "METHOD": 1,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]
            # Dissolve removes internal seams among observed parts, preventing
            # intra-footprint overlap from inflating the observed denominator.
            observed_diss = processing.run(
                "native:dissolve",
                {
                    "INPUT": observed_fixed,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]
            # All areas below are derived in the common input CRS; no separate
            # observation-domain or river-belt denominator is introduced here.
            observed_diss_layer = self._as_layer(observed_diss, context)
            observed_area = self._area(observed_diss_layer)
            feedback.pushInfo(
                f"[5d batch] Observed footprint: {observed_area/1e6:.6f} km²"
            )

            # Nested relative-susceptibility thresholds vary only the predicted
            # zone, keeping the observed interval footprint fixed.
            for pct in top_pcts:
                if feedback.isCanceled():
                    break

                feedback.pushInfo(
                    f"[5d batch] --- {combo_id} / P{pct:g} ---"
                )
                # Materialise the selected rank cut-off (e.g. top 10%), then repair and
                # dissolve the predicted polygon selection before overlay.
                predicted = self._materialise_pred_pct(
                    pred_info["layer"], pct, f"{combo_id}_P{pct:g}", feedback
                )
                # Use Native Processing fixgeometries to reduce invalid geometry errors
                # in intersection/difference operations. This is geometry repair only.
                predicted_fixed = processing.run(
                    "native:fixgeometries",
                    {
                        "INPUT": predicted,
                        "METHOD": 1,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]
                # Union selected susceptibility-zone cells into a single geometry so
                # adjacent-cell boundaries do not count as separate event footprints.
                predicted_diss = processing.run(
                    "native:dissolve",
                    {
                        "INPUT": predicted_fixed,
                        "FIELD": [],
                        "SEPARATE_DISJOINT": False,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]

                # INTERSECTION: A_O intersection A_P is the observed transition footprint
                # that falls inside the predicted high-susceptibility zone.
                inter = processing.run(
                    "native:intersection",
                    {
                        "INPUT": observed_diss,
                        "OVERLAY": predicted_diss,
                        "INPUT_FIELDS": [],
                        "OVERLAY_FIELDS": [],
                        "OVERLAY_FIELDS_PREFIX": "",
                        "GRID_SIZE": None,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]
                # MISSED: A_O minus A_P is the observed area not covered by this
                # threshold's selected predicted zone.
                missed = processing.run(
                    "native:difference",
                    {
                        "INPUT": observed_diss,
                        "OVERLAY": predicted_diss,
                        "GRID_SIZE": None,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]
                # UNREALISED: A_P minus A_O is selected high-susceptibility area that
                # has no observed transition footprint in this particular interval.
                # It is not proof that a geomorphic transition will never occur there.
                unrealised = processing.run(
                    "native:difference",
                    {
                        "INPUT": predicted_diss,
                        "OVERLAY": observed_diss,
                        "GRID_SIZE": None,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]

                # QGIS overlay results supply predicted and intersection area; actual
                # area was computed once from the dissolved observed footprint.
                pred_area = self._area(self._as_layer(predicted_diss, context))
                int_area = self._area(self._as_layer(inter, context))
                # Area consistency identities (subject to GIS numeric tolerance):
                # observed = intersection + missed;
                # predicted = intersection + unrealised.
                missed_area = max(0.0, observed_area - int_area)
                unrealised_area = max(0.0, pred_area - int_area)
                # Formal geometric metrics:
                # Recall = |A_O ∩ A_P| / |A_O| (actual-footprint capture).
                # Precision = |A_O ∩ A_P| / |A_P| (selected-zone efficiency).
                # IoU = |A_O ∩ A_P| / |A_O ∪ A_P| (spatial overlap).
                # These are area-based, not the row-level AUC/AP from retrospective validation.
                recall = int_area / observed_area if observed_area > 0 else None
                precision = int_area / pred_area if pred_area > 0 else None
                union = observed_area + pred_area - int_area
                iou = int_area / union if union > 0 else None

                # Export each geometric partition as an independently selectable layer.
                # Keep the original transition label and forecast metadata for comparison.
                self._append_result(
                    inside_out, inter, meta,
                    "Actual transition inside predicted zone", pct, context
                )
                self._append_result(
                    missed_out, missed, meta,
                    "Actual transition outside predicted zone", pct, context
                )
                self._append_result(
                    unrealised_out, unrealised, meta,
                    "Predicted risk zone without actual transition", pct, context
                )
                self._append_result(
                    # Append all three geometric categories to a single comparison layer,
                    # which supports category symbology without recomputing overlays.
                    comparison_out, inter, meta,
                    "Actual inside predicted zone", pct, context
                )
                self._append_result(
                    comparison_out, missed, meta,
                    "Actual outside predicted zone", pct, context
                )
                self._append_result(
                    comparison_out, unrealised, meta,
                    "Predicted risk zone without actual transition", pct, context
                )

                # The CSV keeps raw areas, fractions, names of contributing input
                # layers, and the precise threshold as both top_pct and risk_percentile_ge.
                rows.append({
                    "combination_id": combo_id,
                    "transition": meta["transition"],
                    "transition_code": code,
                    "forecast": self._norm_forecast(meta["forecast"]),
                    "y1": meta["y1"],
                    "y2": meta["y2"],
                    "top_pct": pct,
                    "risk_percentile_ge": 100.0 - pct,
                    "predicted_area_m2": pred_area,
                    "actual_observed_area_m2": observed_area,
                    "actual_area_inside_predicted_m2": int_area,
                    "actual_area_missed_m2": missed_area,
                    "predicted_area_without_actual_transition_m2": unrealised_area,
                    "actual_transition_recall": recall if recall is not None else "",
                    "predicted_area_precision": precision if precision is not None else "",
                    "intersection_over_union": iou if iou is not None else "",
                    "predicted_source_layers": " | ".join(sorted(pred_info["source_layers"])),
                    "observed_source_layers": " | ".join(sorted(obs_info["source_layers"])),
                })

                # Report calculated metrics per threshold to the QGIS Processing log.
                # Undefined denominators are reported as NA rather than converted to zero.
                feedback.pushInfo(
                    f"[5d batch] P{pct:g}: recall={recall if recall is not None else 'NA'}; "
                    f"precision={precision if precision is not None else 'NA'}; "
                    f"IoU={iou if iou is not None else 'NA'}"
                )

                # Progress is counted per successful combination-threshold job.
                completed += 1
                feedback.setProgress(int(round(100 * completed / total_jobs)))

        # No completed job is a hard error. Cancellation after partial work
        # may still leave partially complete rows in the current implementation.
        if not rows:
            raise QgsProcessingException("No batch verification job completed.")

        # Exactly four geometrical output layers are written, regardless of
        # the number of combinations or thresholds analysed.
        # Write a compact four-layer GeoPackage.
        outputs = [
            (inside_out, f"{prefix}_actual_inside"),
            (missed_out, f"{prefix}_actual_missed"),
            (unrealised_out, f"{prefix}_risk_unrealised"),
            (comparison_out, f"{prefix}_comparison"),
        ]
        # File-level overwrite is initiated on the first layer; the remaining
        # three named layers are written into the same package.
        first = True
        for layer, layer_name in outputs:
            self._write_gpkg(layer, gpkg_path, layer_name, context, first=first)
            first = False
            feedback.pushInfo(
                f"[5d batch] Wrote {layer_name}: {layer.featureCount():,} feature(s)."
            )

        # CSV schema is stable across all transition types; combine per-river
        # summaries downstream using forecast/transition/threshold identifiers.
        fields = [
            "combination_id",
            "transition",
            "transition_code",
            "forecast",
            "y1",
            "y2",
            "top_pct",
            "risk_percentile_ge",
            "predicted_area_m2",
            "actual_observed_area_m2",
            "actual_area_inside_predicted_m2",
            "actual_area_missed_m2",
            "predicted_area_without_actual_transition_m2",
            "actual_transition_recall",
            "predicted_area_precision",
            "intersection_over_union",
            "predicted_source_layers",
            "observed_source_layers",
        ]
        # Write a single audit-ready CSV, with one row for each completed
        # forecast-transition-top-percent selection.
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        # Record totals and output locations in the Processing feedback log.
        feedback.pushInfo(
            f"[5d batch] Completed {len(rows)} combination-threshold verification rows "
            f"across {len(matched_keys)} combination(s)."
        )
        feedback.pushInfo(f"[5d batch] GeoPackage: {gpkg_path}")
        feedback.pushInfo(f"[5d batch] Summary CSV: {summary_path}")
        feedback.setProgress(100)

        # Return the two file destinations to QGIS. The GeoPackage contains
        # four layers while the second file is a plain summary table.
        return {
            self.OUTPUT_GPKG: str(gpkg_path),
            self.OUTPUT_SUMMARY: str(summary_path),
        }
