# -*- coding: utf-8 -*-
"""
FRAF Module 5c2 — Verification Input Builder v1.4
AUTHORITATIVE PRIMARY-EVENT + BROAD FLOODPLAIN ALIGNED

Purpose
-------
Prepare spatial inputs for Module 5d using exactly the same observed-event
definition as the Stage 4 / R prediction models.

This version replaces the earlier requirement to manually choose an
ONTO_STATE_i field for the forecast origin. Instead, it uses the authoritative
Stage 4 Risk Table and the transition-specific PRIMARY event/risk fields.

For erosion/deposition transitions:
    actual footprint =
        mapped interval EA/process geometry
        INTERSECT
        fixed place cells where the matching *_EVT_PRIMARY == 1

For stabilisation:
    there is no direct mapped EA erosion/deposition footprint, so the
    authoritative STABILISE_EVT_PRIMARY cells themselves are used as the
    observed spatial support.

Supported transitions
---------------------
0. Stabilised Floodplain -> Active Domain
   Event: REACTIVATE_EVT_PRIMARY
   Risk:  REACTIVATE_RISK_SET_PRIMARY
   Process geometry: erosion

1. Depositional Storage -> Active Domain
   Event: STORAGE_REWORK_EVT_PRIMARY
   Risk:  STORAGE_REWORK_RISK_SET_PRIMARY
   Process geometry: erosion

2. Active Domain -> Depositional Storage
   Event: STORAGE_EVT_PRIMARY
   Risk:  STORAGE_RISK_SET_PRIMARY
   Process geometry: deposition

3. Depositional Storage -> Stabilised Floodplain
   Event: STABILISE_EVT_PRIMARY
   Risk:  STABILISE_RISK_SET_PRIMARY
   Process geometry: none; primary event cells are used

4. Eligible Floodplain -> Active Domain
   Event: FP_REACTIVATE_EVT_PRIMARY
   Risk:  FP_REACTIVATE_RISK_SET_PRIMARY
   Process geometry: erosion
   Includes strict Stabilised Floodplain plus eligible pre-existing floodplain.

Outputs
-------
- Percentile risk cells (PCTL_GE identifies the minimum relative-risk percentile)
- Dissolved percentile transition-risk zones
- Authoritative observed event cells
- Observed process-specific transition polygons
- Dissolved observed transition footprint
- QA CSV

The module is generic and contains no Jamuna/Mamoré-specific logic.
"""
# FRAF PAPER 2 | REPOSITORY MODULE 09 | VERIFICATION INPUTS | v1.4
# Archive filename: FRAF_P2_09_VerificationInputs_v1_4.py
# Original implementation: FRAF Module 5c2 Verification Input Builder v1.4.
#
# WORKFLOW / PROVENANCE
#   Input A: continuous prediction polygons from Module 5c / archive step 08M.
#   Input B: Stage 4 / step 05 non-spatial interval Risk Table, whose
#            event/risk fields define the authoritative observation population.
#   Input C: fixed KM_blocks / PLACE polygons, the single spatial key geometry.
#   Input D: observed, interval-matched EA/process polygons (except DS->SF).
#   Output: predicted percentile-cell/zone supports; actual transition cells;
#           process-clipped observed transition polygons; dissolved footprints;
#           and an audit CSV for downstream Module 5d spatial verification.
#
# SCIENTIFIC INTERPRETATION
#   ACTIVE_DOMAIN (AD), DEPOSITIONAL_STORAGE (DS) and STABILISED_FLOODPLAIN
#   (SF) are the three organisational states. Eligible Floodplain (FP) in
#   FP->AD prediction is a broader risk population, NOT a fourth state:
#   it includes eligible pre-existing floodplain and SF, and excludes DS.
#   Transition labels and event flags describe changes in organisational state;
#   mapped EA erosion/deposition provides physical process support, not an
#   interchangeable event definition. DS->SF has no directly mapped EA event
#   footprint, so observed event-cell polygons remain its spatial target.
#   Percentiles rank relative susceptibility within the prediction population;
#   a >=90th-percentile selection is not a >=90% event-probability prediction.
#   Formal verification is limited to the requested interval and transition.
#
# REPRODUCIBILITY / SCOPE
#   This module constructs inputs for spatial-capture/overlap verification;
#   it does NOT refit Cox models, estimate probabilities, or compute IoU/recall.
#   Users must supply the correct forecast interval's EA polygons and ensure
#   that Risk Table, prediction archive and KM-block keys refer to the same
#   analysis corridor, observation chronology, and event definition.
#   Area calculations use layer coordinates squared (usually m2 in projected
#   metric CRS). The code warns, but does not stop, on a geographic CRS.
#   Commentary is documentary only: QGIS algorithm identifiers, field names,
#   thresholds, output signatures and computational statements are unchanged.

from __future__ import annotations

import csv
import math
import os
import re
from typing import Dict, List, Optional, Set, Tuple

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingUtils,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)


class FRAFModule5c2VerificationInputBuilder(QgsProcessingAlgorithm):
    # Parameter names are public keys in saved QGIS Processing runs and models.
    # Do not rename them when archiving a script under a different filename.
    PREDICTION = "PREDICTION"
    PCTL_THRESHOLDS = "PCTL_THRESHOLDS"
    TRANSITION_TYPE = "TRANSITION_TYPE"

    # The risk table is non-spatial: observed events are joined to the fixed
    # place grid by ID rather than inferred from mapped prediction classes.
    RISK_TABLE = "RISK_TABLE"
    RISK_KEY_FIELD = "RISK_KEY_FIELD"
    EVENT_FIELD_OVERRIDE = "EVENT_FIELD_OVERRIDE"
    RISK_FIELD_OVERRIDE = "RISK_FIELD_OVERRIDE"

    PLACE_POLYGONS = "PLACE_POLYGONS"
    PLACE_KEY_FIELD = "PLACE_KEY_FIELD"

    # EA/process polygons are required for erosion and deposition events;
    # they are optional for DS->SF because stabilisation lacks an EA footprint.
    PROCESS_POLYGONS = "PROCESS_POLYGONS"
    PROCESS_CLASS_FIELD = "PROCESS_CLASS_FIELD"
    PROCESS_CLASSES_OVERRIDE = "PROCESS_CLASSES_OVERRIDE"

    MIN_OBS_AREA = "MIN_OBS_AREA"
    MIN_ZONE_AREA = "MIN_ZONE_AREA"

    # Six deliverables are kept separate so subsequent verification can
    # compare ranked predicted areas with precisely defined observed support.
    OUTPUT_RISK_CELLS = "OUTPUT_RISK_CELLS"
    OUTPUT_RISK_ZONES = "OUTPUT_RISK_ZONES"
    OUTPUT_EVENT_CELLS = "OUTPUT_EVENT_CELLS"
    OUTPUT_OBSERVED = "OUTPUT_OBSERVED"
    OUTPUT_OBSERVED_FOOTPRINT = "OUTPUT_OBSERVED_FOOTPRINT"
    OUTPUT_QA = "OUTPUT_QA"

    # Order of this enumeration determines the parallel EVENT_CANDIDATES,
    # RISK_CANDIDATES and PROCESS_KIND selections. Do not reorder alone.
    TRANSITIONS = [
        "Stabilised Floodplain -> Active Domain",
        "Depositional Storage -> Active Domain",
        "Active Domain -> Depositional Storage",
        "Depositional Storage -> Stabilised Floodplain",
        "Eligible Floodplain -> Active Domain",
    ]

    # Preferred event columns are the ambiguity-bridged PRIMARY fields.
    # Strict fields are compatibility fallbacks, not identical event definitions.
    EVENT_CANDIDATES = [
        ["REACTIVATE_EVT_PRIMARY", "REACTIVATE_EVT"],
        ["STORAGE_REWORK_EVT_PRIMARY", "STORAGE_REWORK_EVT"],
        ["STORAGE_EVT_PRIMARY", "STORAGE_EVT"],
        ["STABILISE_EVT_PRIMARY", "STABILISE_EVT"],
        ["FP_REACTIVATE_EVT_PRIMARY", "FP_REACTIVATE_EVT"],
    ]

    # Each event must occur inside its corresponding interval-start risk set.
    # The risk-population definition is transition-specific, never universal.
    RISK_CANDIDATES = [
        ["REACTIVATE_RISK_SET_PRIMARY", "REACTIVATE_RISK_SET"],
        ["STORAGE_REWORK_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET"],
        ["STORAGE_RISK_SET_PRIMARY", "STORAGE_RISK_SET"],
        ["STABILISE_RISK_SET_PRIMARY", "STABILISE_RISK_SET"],
        ["FP_REACTIVATE_RISK_SET_PRIMARY", "FP_REACTIVATE_RISK_SET"],
    ]

    # Only DS->SF uses direct event-cell geometry; other transitions use
    # mapped EA erosion or deposition clipped by authoritative event cells.
    PROCESS_KIND = ["EROSION", "EROSION", "DEPOSITION", None, "EROSION"]

    # Stable internal QGIS Processing algorithm ID. Repository filenames do not
    # change the ID, which is needed for processing-model compatibility.
    def name(self):
        return "fraf_module5c2_verification_input_builder_v1_4_percentile_rank"

    # User-facing Processing Toolbox name remains the original v1.4 label.
    def displayName(self):
        return "Module 5c2 — Verification Input Builder v1.4 (percentile-rank terminology)"

    # Display grouping is retained to avoid altering QGIS Toolbox registration.
    def group(self):
        return "FRAF Floodplain Reassemblage"

    # The QGIS group identifier remains backward compatible.
    def groupId(self):
        return "fraf_floodplain_reassemblage"

    # QGIS uses this factory method when instantiating Processing algorithms.
    def createInstance(self):
        return FRAFModule5c2VerificationInputBuilder()

    # Toolbox guidance summarising the event/risk-field selection and the
    # percentile-rank convention used in maps and verification outputs.
    def shortHelpString(self):
        return (
            "Builds Module 5d inputs using the authoritative Stage 4 PRIMARY event "
            "definition. The prediction layer supplies forecast date/transition and "
            "percentile risk. The Risk Table supplies actual event cells. For "
            "reactivation/storage-reworking, mapped erosion is clipped to the matching "
            "PRIMARY event cells; for storage formation mapped deposition is clipped; "
            "for stabilisation the PRIMARY event cells are the observed spatial support. "
            "The broad Eligible Floodplain -> Active Domain option uses FP_REACTIVATE_*_PRIMARY. "
            "Risk thresholds are entered as percentile ranks (for example 90,80,70), "
            "rather than as top-10/top-20/top-30 percentages. A >=90th-percentile zone is the highest-risk "
            "10% of eligible cells; it does not imply a 90% absolute probability."
        )

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------
    # Declare required and optional datasets, choice of event/risk definition,
    # percentile thresholds, geometric minimum-area filters and six outputs.
    # Blank field overrides select PRIMARY definitions when present, with
    # strict-field compatibility fallbacks if those PRIMARY columns are absent.
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                # Continuous mapping includes scored and unscored cells; only scored
                # P_STATUS=predicted polygons are ranked and included in risk zones.
                self.PREDICTION,
                "Module 5c continuous prediction polygons",
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                # Thresholds represent minimum percentile RANK, not top-area percentage.
                # For equal-area eligible places, >=90 approximately selects the highest tenth.
                self.PCTL_THRESHOLDS,
                "Minimum relative-risk percentiles to build (comma-separated; e.g. 90,80,70)",
                defaultValue="90,80,70",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                # The selected transition sets the observed event/risk columns and the
                # physical EA process used to form its observed polygon footprint.
                self.TRANSITION_TYPE,
                "Transition to verify",
                options=self.TRANSITIONS,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                # The Stage 4 Risk Table must contain rows for the forecast interval,
                # including a fixed-place key and transition-specific primary event/risk fields.
                self.RISK_TABLE,
                "Authoritative Stage 4 Risk Table",
                [QgsProcessing.TypeVector],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.RISK_KEY_FIELD,
                "Risk Table place key field",
                parentLayerParameterName=self.RISK_TABLE,
                defaultValue="BLOCK_ID",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                # An explicit override is for deliberate sensitivity or compatibility
                # checks and can change the analysed event population.
                self.EVENT_FIELD_OVERRIDE,
                "Event field override (blank = PRIMARY field for selected transition)",
                defaultValue="",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                # Always pair a manually overridden risk field with the matching
                # event definition; otherwise event/risk mismatch QA may stop the run.
                self.RISK_FIELD_OVERRIDE,
                "Risk-set field override (blank = PRIMARY field for selected transition)",
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                # This layer supplies physical geometry for events; the Risk Table
                # does not create or duplicate fixed-place polygons.
                self.PLACE_POLYGONS,
                "Fixed place/KM block polygons",
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PLACE_KEY_FIELD,
                "Place polygon key field",
                parentLayerParameterName=self.PLACE_POLYGONS,
                defaultValue="BLOCK_ID",
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                # Supply EA polygons for the single y1->y2 interval being verified,
                # not a pooled time-span layer or all-erosion aggregate.
                self.PROCESS_POLYGONS,
                "Observed interval EA/process polygons (not required for stabilisation)",
                [QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PROCESS_CLASS_FIELD,
                "Observed process class field (e.g. EA)",
                parentLayerParameterName=self.PROCESS_POLYGONS,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                # When nonempty, the override matches cleaned source class names
                # exactly; it bypasses the automatic EROSION/DEPOSITION category mapping.
                self.PROCESS_CLASSES_OVERRIDE,
                "Observed process classes override (comma-separated; blank = automatic erosion/deposition classes)",
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                # Removing small observed parts changes the observed footprint and must
                # be reported as an analytical filter if nonzero.
                self.MIN_OBS_AREA,
                "Minimum observed transition polygon area (map units²)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                # Zone minimum-area filtering affects each dissolved predicted part,
                # not the cell-level risk scores or selection thresholds.
                self.MIN_ZONE_AREA,
                "Minimum dissolved predicted-zone part area (map units²)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                # The output repeats eligible polygons for EACH threshold they meet;
                # PCTL_GE identifies the threshold-specific selection.
                self.OUTPUT_RISK_CELLS,
                "Percentile risk cells",
                QgsProcessing.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                # Dissolved percentile zones represent predicted spatial priority,
                # not observed erosion or actual event probability.
                self.OUTPUT_RISK_ZONES,
                "Dissolved percentile transition-risk zones",
                QgsProcessing.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                # Event cells reproduce the authoritative interval flags on the
                # fixed polygon grid before any process-geometry intersection.
                self.OUTPUT_EVENT_CELLS,
                "Authoritative actual transition event cells",
                QgsProcessing.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                # Process-specific observed polygons are clipped to actual event cells;
                # for DS->SF, they are the event cells themselves.
                self.OUTPUT_OBSERVED,
                "Observed process-specific transition polygons",
                QgsProcessing.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                # A dissolved version of observed transition geometry avoids counting
                # overlap among observed parts more than once.
                self.OUTPUT_OBSERVED_FOOTPRINT,
                "Dissolved observed transition footprint",
                QgsProcessing.TypeVectorPolygon,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                # The QA CSV records threshold areas, event/risk counts and observation
                # method so inputs to downstream verification can be audited.
                self.OUTPUT_QA,
                "Verification-input QA summary CSV",
                fileFilter="CSV files (*.csv)",
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    # Normalise process labels for tolerant matching: strip whitespace, convert
    # to lowercase, replace punctuation/spacing with underscores. This is
    # classification convenience, not an ontology-state inference engine.
    @staticmethod
    def _clean(value) -> str:
        if value is None:
            return ""
        try:
            if hasattr(value, "isNull") and value.isNull():
                return ""
        except Exception:
            pass
        # The normalised class string is used only for matching process labels.
        s = str(value).strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return re.sub(r"_+", "_", s).strip("_")

    # Standardise PLACE/BLOCK identifiers for joins without altering source
    # features. Integral-looking numeric strings are converted to integer text;
    # non-numeric identifiers are preserved as supplied.
    @staticmethod
    def _key(value) -> str:
        if value is None:
            return ""
        # PLACE/BLOCK key normalisation helps tolerate CSV integer formatting.
        s = str(value).strip()
        if not s:
            return ""
        try:
            f = float(s)
            if math.isfinite(f) and abs(f - int(f)) < 1e-9:
                return str(int(f))
        except Exception:
            pass
        return s

    # Convert event/risk flags into strict 0/1. Only numeric 1 is true;
    # common textual TRUE/YES alternatives are accepted.
    @staticmethod
    def _int01(value) -> int:
        try:
            # A positive number other than 1 is NOT interpreted as event=1.
            x = int(float(value))
            return 1 if x == 1 else 0
        except Exception:
            v = str(value or "").strip().lower()
            return 1 if v in {"true", "yes", "y", "t"} else 0

    # Reject non-finite predictor/threshold values instead of propagating NaN.
    @staticmethod
    def _float(value):
        try:
            x = float(value)
            return x if math.isfinite(x) else None
        except Exception:
            return None

    # Convert date labels from the prediction and Risk Table to an 8-digit
    # YYYYMMDD comparison key. Year-only labels become January 1 by convention;
    # this must match the chronology used when the Risk Table was built.
    @staticmethod
    def _ymd(value):
        """Normalise date-like Risk Table labels to YYYYMMDD."""
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None

        # Year-to-date conversion has a documented January-1 convention;
        # month-specific imagery needs correctly dated labels upstream.
        # Direct numeric YYYYMMDD.
        m = re.search(r"(?<!\d)((?:18|19|20)\d{6})(?!\d)", s)
        if m:
            return m.group(1)

        # YYYY-MM-DD / YYYY_MM_DD / YYYY/MM/DD.
        m = re.search(
            r"(?<!\d)((?:18|19|20)\d{2})[-_/ ](\d{1,2})[-_/ ](\d{1,2})(?!\d)",
            s,
        )
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return f"{y:04d}{mo:02d}{d:02d}"

        # Year only: use Jan 1, matching the annual Jamuna chronology.
        m = re.search(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", s)
        if m:
            return f"{int(m.group(1)):04d}0101"
        return None

    # Require percentile values strictly between 0 and 100, remove duplicates,
    # and process largest threshold first (usually 90,80,70). Division by 100
    # occurs only when comparing against fractional P_PCTL values.
    @staticmethod
    def _parse_percentile_thresholds(text: str) -> List[float]:
        vals = []
        for token in re.split(r"[,; ]+", str(text or "").strip()):
            if not token:
                continue
            try:
                x = float(token)
            except Exception:
                raise QgsProcessingException(
                    f"Invalid percentile threshold '{token}'. Use values such as 90,80,70."
                )
            if not 0.0 < x < 100.0:
                raise QgsProcessingException(
                    f"Percentile threshold must be >0 and <100; got {x}."
                )
            vals.append(x)
        # Deduplication avoids producing duplicate risk features for one cutoff.
        vals = sorted(set(vals), reverse=True)
        if not vals:
            raise QgsProcessingException("Provide at least one relative-risk percentile threshold.")
        return vals

    # Omit FID/ROWID provider keys when copying QGIS attributes so GeoPackage
    # feature identifiers are regenerated rather than carried from input layers.
    @staticmethod
    def _drop_provider_id_fields(fields: QgsFields):
        # GeoPackage identifiers are provider-managed; copying them can trigger
        # unique-index conflicts on output.
        reserved = {"fid", "ogc_fid", "rowid", "objectid", "object_id"}
        out = QgsFields()
        names = []
        for fld in fields:
            if fld.name().strip().lower() in reserved:
                continue
            out.append(fld)
            names.append(fld.name())
        return out, names

    # Resolve a temporary Processing result into a feature-readable layer.
    # Accept an existing vector layer/feature source or look up a result URI.
    @staticmethod
    def _resolve_layer(src, context):
        if src is None:
            return None
        # Temporary Processing layers can be passed as objects or path strings.
        if isinstance(src, QgsVectorLayer):
            try:
                return src if src.isValid() else None
            except Exception:
                return None
        if all(hasattr(src, a) for a in ("getFeatures", "fields", "featureCount")):
            return src
        try:
            lyr = QgsProcessingUtils.mapLayerFromString(str(src), context)
            if lyr is not None and lyr.isValid():
                return lyr
        except Exception:
            pass
        return None

    # Classify recognised EA process descriptions into EROSION, DEPOSITION
    # or OTHER. The expected process type depends on transition, not river type.
    @classmethod
    def _process_kind(cls, value) -> str:
        v = cls._clean(value)
        # Classification recognises EA aliases; unknown classes remain OTHER
        # and are excluded when an automatic process filter is used.
        if v in {
            "erosion", "bank_erosion", "channel_erosion",
            "island_erosion", "island_ero", "isl_erosion",
        }:
            return "EROSION"
        if v in {
            "deposition", "bank_deposition", "channel_deposition",
            "migration_deposition", "infill_deposition",
            "island_deposition", "island_dep", "isl_deposition",
            "channel_legacy_deposition",
        }:
            return "DEPOSITION"
        return "OTHER"

    # Choose a reasonable existing EA/process class column if the user leaves
    # PROCESS_CLASS_FIELD blank; priority is given to conventional EA names.
    @staticmethod
    def _auto_process_field(source):
        # Process-field resolution is based on an explicit name priority list.
        names = source.fields().names()
        preferred = [
            "EA", "EA_Class", "EA_CLASS", "EA_class", "EA_clean",
            "PROCESS", "Process", "process",
            "CLASS", "Class", "class",
            "EA_TYPE", "EA_TYPE_CLEAN",
        ]
        for name in preferred:
            if name in names:
                return name
        lower = {n.lower(): n for n in names}
        for candidate in ("ea", "ea_class", "ea_clean", "process", "class", "ea_type"):
            if candidate in lower:
                return lower[candidate]
        return None

    # Select the first available field from an ordered compatibility list.
    # PRIMARY event/risk fields are preferred but strict fallback remains allowed;
    # check which specific fields are reported before publication.
    @staticmethod
    def _first_existing(names: List[str], candidates: List[str], label: str):
        # First-found ordering implements the preference for PRIMARY fields.
        for candidate in candidates:
            if candidate in names:
                return candidate
        raise QgsProcessingException(
            f"Could not find {label}. Tried: {', '.join(candidates)}"
        )

    # Scan P_STATUS=predicted records to collect forecast/transition labels,
    # interval start/end labels and the number of scored P_EVENT=1 cells.
    # The latter is a diagnostic, not an independent source of actual events.
    @staticmethod
    def _prediction_metadata(prediction):
        names = prediction.fields().names()
        wanted = [x for x in ("P_FORECAST", "P_TRANS", "P_Y1", "P_Y2") if x in names]
        out = {x: set() for x in wanted}
        # Diagnostic count of event flags from scored predictions; actual event
        # geometry always comes from the interval Risk Table instead.
        pred_event_count = 0

        subset = list(wanted)
        for extra in ("P_STATUS", "P_EVENT"):
            if extra in names:
                subset.append(extra)

        # Read only needed attributes with NoGeometry for inexpensive metadata QA.
        req = QgsFeatureRequest()
        req.setSubsetOfAttributes(subset, prediction.fields())
        req.setFlags(QgsFeatureRequest.NoGeometry)

        for ft in prediction.getFeatures(req):
            status = str(ft["P_STATUS"] or "").strip() if "P_STATUS" in names else ""
            # Unscored places are excluded from prediction metadata and ranked zones.
            if status != "predicted":
                continue
            if "P_EVENT" in names and FRAFModule5c2VerificationInputBuilder._int01(ft["P_EVENT"]) == 1:
                pred_event_count += 1
            for field in wanted:
                val = ft[field]
                if val is None:
                    continue
                s = str(val).strip()
                if s and s.upper() not in {"NULL", "NONE", "NA"}:
                    out[field].add(s)

        return out, pred_event_count

    # Write a selected polygon subset into a temporary in-memory MultiPolygon
    # layer, transforming to prediction CRS when needed. Batched feature inserts
    # bound Python feature-list size but the finished memory layer remains in RAM.
    @staticmethod
    def _materialise_polygon_source(source, target_crs, name, feedback, filter_func=None):
        """Create a clean memory polygon layer in target CRS."""
        # Source process geometry is copied into the target CRS before overlay;
        # the temporary memory layer is not an archive deliverable.
        layer = QgsVectorLayer(
            f"MultiPolygon?crs={target_crs.authid()}",
            name,
            "memory",
        )
        if not layer.isValid():
            raise QgsProcessingException(f"Could not create memory layer '{name}'.")

        # Coordinate transformation is conditional on an actual CRS mismatch.
        transform = None
        src_crs = source.sourceCrs()
        if src_crs.isValid() and src_crs != target_crs:
            transform = QgsCoordinateTransform(src_crs, target_crs, QgsProject.instance())
            feedback.pushInfo(
                f"[5c2] Reprojecting {name}: {src_crs.authid()} -> {target_crs.authid()}"
            )

        provider = layer.dataProvider()
        batch = []
        n = 0
        for ft in source.getFeatures():
            if filter_func is not None and not filter_func(ft):
                continue
            geom = ft.geometry()
            if geom is None or geom.isEmpty():
                continue
            g = QgsGeometry(geom)
            if transform is not None:
                try:
                    g.transform(transform)
                except Exception as exc:
                    raise QgsProcessingException(
                        f"Could not transform geometry in {name}: {exc}"
                    )
            # Reject non-polygons rather than passing incompatible geometry to overlay.
            if QgsWkbTypes.geometryType(g.wkbType()) != QgsWkbTypes.PolygonGeometry:
                continue
            if not g.isMultipart():
                try:
                    g.convertToMultiType()
                except Exception:
                    pass
            nf = QgsFeature(layer.fields())
            nf.setGeometry(g)
            batch.append(nf)
            n += 1
            # Flush feature batches, but retain the accumulated geometry in the
            # QGIS memory provider. Dense EA layers can still be memory-intensive.
            if len(batch) >= 5000:
                provider.addFeatures(batch, QgsFeatureSink.FastInsert)
                batch = []
        if batch:
            provider.addFeatures(batch, QgsFeatureSink.FastInsert)

        layer.updateExtents()
        feedback.pushInfo(f"[5c2] Materialised {name}: {n:,} polygon(s)")
        return layer

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    # Main orchestration: validate forecast metadata; build predicted risk
    # cells and dissolved zones; identify actual events in the authoritative
    # interval Risk Table; transfer those event flags to fixed polygon supports;
    # intersect with mapped process polygons where appropriate; dissolve actual
    # footprint and export a QA summary for the subsequent verification stage.
    def processAlgorithm(self, parameters, context, feedback):
        # A. Read the three required inputs and the optional observed-process layer.
        prediction = self.parameterAsSource(parameters, self.PREDICTION, context)
        risk_table = self.parameterAsSource(parameters, self.RISK_TABLE, context)
        places = self.parameterAsSource(parameters, self.PLACE_POLYGONS, context)
        process_src = self.parameterAsSource(parameters, self.PROCESS_POLYGONS, context)

        if prediction is None or risk_table is None or places is None:
            raise QgsProcessingException(
                "Prediction polygons, authoritative Risk Table and fixed place polygons are required."
            )

        # Require scored status and relative-risk percentile in the prediction polygons.
        pred_names = prediction.fields().names()
        for required in ("P_STATUS", "P_PCTL"):
            if required not in pred_names:
                raise QgsProcessingException(
                    f"Prediction layer is missing '{required}'. "
                    "Use the continuous polygon output from Module 5c."
                )

        # Typical cutoffs are 90,80,70: nested high- to elevated-risk sets.
        pctl_thresholds = self._parse_percentile_thresholds(
            self.parameterAsString(parameters, self.PCTL_THRESHOLDS, context)
        )
        # Index ties all five transition definitions to matching event/risk columns.
        transition_idx = self.parameterAsEnum(parameters, self.TRANSITION_TYPE, context)
        transition = self.TRANSITIONS[transition_idx]
        required_process = self.PROCESS_KIND[transition_idx]

        # Risk Table and polygon identifiers may have different column names,
        # but their key VALUES must refer to the same fixed cells.
        risk_key_field = self.parameterAsString(
            parameters, self.RISK_KEY_FIELD, context
        ).strip()
        place_key_field = self.parameterAsString(
            parameters, self.PLACE_KEY_FIELD, context
        ).strip()

        if risk_key_field not in risk_table.fields().names():
            raise QgsProcessingException(
                f"Risk Table key field '{risk_key_field}' is not present."
            )
        if place_key_field not in places.fields().names():
            raise QgsProcessingException(
                f"Place polygon key field '{place_key_field}' is not present."
            )

        # An override is not a new ontology: it only changes which existing
        # Risk Table columns supply the event/risk flags.
        event_override = self.parameterAsString(
            parameters, self.EVENT_FIELD_OVERRIDE, context
        ).strip()
        risk_override = self.parameterAsString(
            parameters, self.RISK_FIELD_OVERRIDE, context
        ).strip()

        risk_names = risk_table.fields().names()
        # Select preferred PRIMARY event and risk-set columns if available.
        # The chosen names are echoed in feedback and recorded in outputs.
        event_field = (
            event_override if event_override
            else self._first_existing(
                risk_names, self.EVENT_CANDIDATES[transition_idx], "transition event field"
            )
        )
        risk_field = (
            risk_override if risk_override
            else self._first_existing(
                risk_names, self.RISK_CANDIDATES[transition_idx], "transition risk-set field"
            )
        )

        if event_field not in risk_names:
            raise QgsProcessingException(f"Event field '{event_field}' is not present.")
        if risk_field not in risk_names:
            raise QgsProcessingException(f"Risk field '{risk_field}' is not present.")

        # Risk-table interval fields.
        # Match both START and END dates: a shared end year alone is insufficient
        # when observation intervals have irregular spacing.
        y1_field = self._first_existing(
            risk_names,
            ["y1", "Y1", "Start_ymd", "START_YMD", "interval_start_label"],
            "Risk Table interval-start field",
        )
        y2_field = self._first_existing(
            risk_names,
            ["y2", "Y2", "End_ymd", "END_YMD", "interval_end_label"],
            "Risk Table interval-end field",
        )

        # Process-class overrides control which physical EA polygons enter the
        # observed footprint; they do not change the selected event cells.
        process_field = self.parameterAsString(
            parameters, self.PROCESS_CLASS_FIELD, context
        ).strip()
        override_text = self.parameterAsString(
            parameters, self.PROCESS_CLASSES_OVERRIDE, context
        ).strip()
        override_values = {
            self._clean(x)
            for x in re.split(r"[,;]+", override_text)
            if x.strip()
        }

        min_obs_area = float(
            self.parameterAsDouble(parameters, self.MIN_OBS_AREA, context)
        )
        min_zone_area = float(
            self.parameterAsDouble(parameters, self.MIN_ZONE_AREA, context)
        )

        # All derived polygon geometry and map-unit areas use prediction CRS.
        # For area in m2/km2 a suitable projected metric CRS is essential.
        target_crs = prediction.sourceCrs()
        if not target_crs.isValid():
            raise QgsProcessingException("Prediction layer has no valid CRS.")
        if target_crs.isGeographic():
            feedback.pushWarning(
                "Prediction CRS is geographic. Area-based validation should normally use a projected CRS."
            )

        # ------------------------------------------------------------------
        # A. Prediction metadata / interval
        # ------------------------------------------------------------------
        # Prediction metadata is used to identify the unique held-out interval.
        meta, prediction_event_count = self._prediction_metadata(prediction)
        for field, vals in meta.items():
            feedback.pushInfo(
                f"[Prediction metadata] {field}: "
                + (", ".join(sorted(vals)) if vals else "<blank>")
            )

        # Prevent accidental comparison of, e.g., DS->AD predictions with an
        # SF->AD observed-event population.
        expected_transition = transition.strip().lower()
        pred_trans = {x.strip().lower() for x in meta.get("P_TRANS", set())}
        if pred_trans and expected_transition not in pred_trans:
            raise QgsProcessingException(
                f"Selected transition '{transition}' does not match prediction P_TRANS={sorted(meta.get('P_TRANS', set()))}."
            )

        # One output run represents ONE forecast interval; mixed-date prediction
        # layers must be separated before building verification inputs.
        if len(meta.get("P_Y1", set())) != 1 or len(meta.get("P_Y2", set())) != 1:
            raise QgsProcessingException(
                "Prediction layer must contain exactly one forecast interval among P_STATUS='predicted' rows."
            )
        # All Risk Table row matching below uses this parsed y1->y2 interval.
        y1 = next(iter(meta["P_Y1"]))
        y2 = next(iter(meta["P_Y2"]))
        y1_ymd = self._ymd(y1)
        y2_ymd = self._ymd(y2)
        if not y1_ymd or not y2_ymd:
            raise QgsProcessingException(
                f"Could not parse forecast interval from P_Y1={y1}, P_Y2={y2}."
            )

        # Preserve a single forecast label for output provenance if available.
        forecast_label = (
            next(iter(meta["P_FORECAST"]))
            if len(meta.get("P_FORECAST", set())) == 1
            else ""
        )

        feedback.pushInfo(
            f"[Authoritative event] transition={transition}; "
            f"forecast={forecast_label}; interval={y1_ymd}->{y2_ymd}; "
            f"event field={event_field}; risk field={risk_field}"
        )

        # ------------------------------------------------------------------
        # B. Prediction percentile cells
        # ------------------------------------------------------------------
        # B. Copy prediction attributes without inherited provider FIDs, then
        # append fields identifying the percentile threshold for each copy.
        clean_pred_fields, pred_copy_names = self._drop_provider_id_fields(
            prediction.fields()
        )
        # PCTL_GE stores e.g. 90; PCTL_MIN stores the fractional 0.90
        # used to select P_PCTL>=0.90. Both describe a relative-rank cutoff.
        risk_cell_fields = QgsFields(clean_pred_fields)
        risk_cell_fields.append(QgsField("PCTL_GE", QVariant.Double, len=10, prec=3))
        risk_cell_fields.append(QgsField("PCTL_MIN", QVariant.Double, len=12, prec=8))
        risk_cell_fields.append(QgsField("PCTL_LABEL", QVariant.String, len=40))

        risk_cell_sink, risk_cell_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_RISK_CELLS,
            context,
            risk_cell_fields,
            prediction.wkbType(),
            target_crs,
        )
        if risk_cell_sink is None:
            raise QgsProcessingException("Could not create percentile risk-cell sink.")

        # Keep counts/areas separately for each ranked selection; overlapping
        # thresholds are expected and should NOT be summed as disjoint zones.
        pred_total = 0
        pred_valid = 0
        threshold_cell_counts = {p: 0 for p in pctl_thresholds}
        threshold_cell_areas = {p: 0.0 for p in pctl_thresholds}

        # Only P_STATUS=predicted with finite P_PCTL and polygon geometry
        # contribute to percentile selections; other places remain outside these zones.
        for ft in prediction.getFeatures():
            pred_total += 1
            if str(ft["P_STATUS"] or "").strip() != "predicted":
                continue
            pctl = self._float(ft["P_PCTL"])
            if pctl is None:
                continue
            geom = ft.geometry()
            if geom is None or geom.isEmpty():
                continue
            pred_valid += 1
            area = float(geom.area())
            attrs_lookup = {name: ft[name] for name in pred_copy_names}

            # The same highly ranked polygon can enter multiple nested thresholds.
            # This is intentional for comparing top 10/20/30% ranked subsets.
            for p in pctl_thresholds:
                cutoff = p / 100.0
                # Small epsilon protects against floating-point comparison jitter at cutoff.
                if pctl + 1e-12 < cutoff:
                    continue
                nf = QgsFeature(risk_cell_fields)
                nf.setGeometry(geom)
                attrs = [attrs_lookup.get(name) for name in pred_copy_names]
                attrs.extend([float(p), cutoff, f">={p:g}th percentile"])
                nf.setAttributes(attrs)
                if not risk_cell_sink.addFeature(nf, QgsFeatureSink.FastInsert):
                    raise QgsProcessingException(
                        f"Failed to write >={p:g}th-percentile risk cell."
                    )
                threshold_cell_counts[p] += 1
                threshold_cell_areas[p] += area

        # Release the sink handle before reopening its output as a layer.
        del risk_cell_sink

        feedback.pushInfo(
            f"[Predicted] polygons={pred_total:,}; valid predicted={pred_valid:,}; "
            f"prediction event cells={prediction_event_count:,}"
        )
        # Create a separate set of dissolved polygons for each percentile cutoff.
        for p in pctl_thresholds:
            feedback.pushInfo(
                f"[Predicted] >={p:g}th percentile: cells={threshold_cell_counts[p]:,}; "
                f"area={threshold_cell_areas[p] / 1e6:.3f} km²"
            )

        # ------------------------------------------------------------------
        # C. Dissolved percentile risk zones
        # ------------------------------------------------------------------
        # C. Dissolved zones have a clean, short schema rather than inheriting
        # the prediction attributes and provider-managed IDs.
        zone_fields = QgsFields()
        zone_fields.append(QgsField("TRANSITION", QVariant.String, len=100))
        zone_fields.append(QgsField("FORECAST", QVariant.String, len=40))
        zone_fields.append(QgsField("Y1", QVariant.String, len=30))
        zone_fields.append(QgsField("Y2", QVariant.String, len=30))
        zone_fields.append(QgsField("PCTL_GE", QVariant.Double, len=10, prec=3))
        zone_fields.append(QgsField("PCTL_MIN", QVariant.Double, len=12, prec=8))
        zone_fields.append(QgsField("PCTL_LABEL", QVariant.String, len=40))
        zone_fields.append(QgsField("ZONE_AREA", QVariant.Double, len=20, prec=3))

        risk_zone_sink, risk_zone_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_RISK_ZONES,
            context,
            zone_fields,
            QgsWkbTypes.MultiPolygon,
            target_crs,
        )
        if risk_zone_sink is None:
            raise QgsProcessingException("Could not create percentile risk-zone sink.")

        # The risk-cell sink is the input for QGIS dissolve operations.
        risk_cells_layer = self._resolve_layer(risk_cell_id, context)
        if risk_cells_layer is None:
            raise QgsProcessingException(
                "Could not resolve percentile risk-cell output for dissolving."
            )

        threshold_zone_counts = {p: 0 for p in pctl_thresholds}
        threshold_zone_areas = {p: 0.0 for p in pctl_thresholds}

        for p in pctl_thresholds:
            # Extract ONLY records marked with the current PCTL_GE selection.
            selected = processing.run(
                "native:extractbyexpression",
                {
                    "INPUT": risk_cells_layer,
                    "EXPRESSION": f'"PCTL_GE" = {float(p)}',
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            # Dissolving merges adjacent/intersecting selected cells into zones.
            # No smoothing or buffering of the predicted footprint occurs here.
            dissolved = processing.run(
                "native:dissolve",
                {
                    "INPUT": selected,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            # Split multipart dissolves to count/filter individual connected parts.
            single = processing.run(
                "native:multiparttosingleparts",
                {
                    "INPUT": dissolved,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            single_lyr = self._resolve_layer(single, context)
            if single_lyr is None:
                raise QgsProcessingException(
                    f"Could not resolve >={p:g}th-percentile dissolved risk zones."
                )

            cutoff = p / 100.0
            for zf in single_lyr.getFeatures():
                geom = zf.geometry()
                if geom is None or geom.isEmpty():
                    continue
                area = float(geom.area())
                # Zone size filter is applied AFTER dissolve and multipart splitting.
                if area < min_zone_area:
                    continue
                nf = QgsFeature(zone_fields)
                nf.setGeometry(geom)
                nf.setAttributes([
                    transition, forecast_label, y1_ymd, y2_ymd,
                    float(p), cutoff, f">={p:g}th percentile", area,
                ])
                if not risk_zone_sink.addFeature(nf, QgsFeatureSink.FastInsert):
                    raise QgsProcessingException(
                        f"Could not write >={p:g}th-percentile risk-zone part."
                    )
                threshold_zone_counts[p] += 1
                threshold_zone_areas[p] += area

        del risk_zone_sink

        for p in pctl_thresholds:
            feedback.pushInfo(
                f"[Predicted zones] >={p:g}th percentile: parts={threshold_zone_counts[p]:,}; "
                f"area={threshold_zone_areas[p] / 1e6:.3f} km²"
            )

        # ------------------------------------------------------------------
        # D. Authoritative Risk Table event/risk keys for forecast interval
        # ------------------------------------------------------------------
        # D. Authoritative event/risk sets are read ONLY from Risk Table rows
        # whose y1 and y2 exactly match the forecast interval.
        risk_event_keys: Set[str] = set()
        risk_set_keys: Set[str] = set()
        duplicate_event_rows = 0
        selected_interval_rows = 0
        event_rows = 0
        risk_rows = 0
        event_outside_risk_rows = 0

        # Use explicit interval-start and interval-end equality, not row position
        # or feature order, when extracting observed events.
        for ft in risk_table.getFeatures():
            ft_y1 = self._ymd(ft[y1_field])
            ft_y2 = self._ymd(ft[y2_field])
            if ft_y1 != y1_ymd or ft_y2 != y2_ymd:
                continue

            selected_interval_rows += 1
            key = self._key(ft[risk_key_field])
            if not key:
                continue
            ev = self._int01(ft[event_field])
            rr = self._int01(ft[risk_field])

            # Risk population identifies where the transition was eligible to occur.
            if rr == 1:
                risk_rows += 1
                risk_set_keys.add(key)
            # Collect unique event PLACE IDs independently from the prediction model.
            # Also count repeated rows and reject events outside the risk set.
            if ev == 1:
                event_rows += 1
                if key in risk_event_keys:
                    duplicate_event_rows += 1
                risk_event_keys.add(key)
                if rr != 1:
                    event_outside_risk_rows += 1

        # Fail when dates do not match rather than verify against the wrong year.
        if selected_interval_rows == 0:
            raise QgsProcessingException(
                f"No Risk Table rows matched forecast interval {y1_ymd}->{y2_ymd}. "
                f"Check fields {y1_field}/{y2_field} and the prediction interval."
            )
        # An event outside its own risk set signals contradictory upstream
        # transition semantics and invalidates verification for this configuration.
        if event_outside_risk_rows > 0:
            raise QgsProcessingException(
                f"{event_outside_risk_rows:,} authoritative event row(s) fall outside "
                f"the selected risk set {risk_field}. Upstream Stage 4 QA is required."
            )
        # The current implementation rejects zero-event intervals rather than
        # producing empty observed footprints.
        if not risk_event_keys:
            raise QgsProcessingException(
                f"No actual events were found in {event_field} for "
                f"{y1_ymd}->{y2_ymd}."
            )

        feedback.pushInfo(
            f"[Authoritative event] interval rows={selected_interval_rows:,}; "
            f"risk rows={risk_rows:,}; event rows={event_rows:,}; "
            f"unique event places={len(risk_event_keys):,}; "
            f"duplicate event rows={duplicate_event_rows:,}"
        )

        # This is a WARNING, not proof of an error: scored predictions may
        # exclude eligible actual event places with missing model predictors.
        if prediction_event_count != len(risk_event_keys):
            feedback.pushWarning(
                f"Prediction layer reports {prediction_event_count:,} P_EVENT=1 predicted cells, "
                f"while the authoritative Risk Table contains {len(risk_event_keys):,} "
                f"unique {event_field}=1 places. This can occur if an actual event cell "
                "was not modelled because a predictor was unavailable; inspect QA before publication."
            )

        # ------------------------------------------------------------------
        # E. Authoritative event cells from fixed place polygons
        # ------------------------------------------------------------------
        # E. Build actual-event fixed-place cells from KM_blocks and event IDs;
        # these are the denominator/reference support for process-specific clipping.
        event_fields = QgsFields()
        event_fields.append(QgsField("PLACE_KEY", QVariant.String, len=80))
        event_fields.append(QgsField("TRANSITION", QVariant.String, len=100))
        event_fields.append(QgsField("FORECAST", QVariant.String, len=40))
        event_fields.append(QgsField("Y1", QVariant.String, len=20))
        event_fields.append(QgsField("Y2", QVariant.String, len=20))
        event_fields.append(QgsField("EVENT_FLD", QVariant.String, len=80))
        event_fields.append(QgsField("RISK_FLD", QVariant.String, len=80))
        event_fields.append(QgsField("CELL_AREA", QVariant.Double, len=20, prec=3))

        event_sink, event_cells_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_EVENT_CELLS,
            context,
            event_fields,
            QgsWkbTypes.MultiPolygon,
            target_crs,
        )
        if event_sink is None:
            raise QgsProcessingException("Could not create authoritative event-cell sink.")

        event_mem = QgsVectorLayer(
            f"MultiPolygon?crs={target_crs.authid()}",
            "authoritative_event_cells",
            "memory",
        )
        event_mem_provider = event_mem.dataProvider()

        # Place polygons are reprojected to the prediction CRS for overlay.
        place_transform = None
        if places.sourceCrs().isValid() and places.sourceCrs() != target_crs:
            place_transform = QgsCoordinateTransform(
                places.sourceCrs(), target_crs, QgsProject.instance()
            )

        matched_event_keys = set()
        event_cell_count = 0
        event_cell_area = 0.0

        # Only fixed polygons whose IDs occur among authoritative event keys
        # are emitted; do not infer events from high model percentile alone.
        for ft in places.getFeatures():
            key = self._key(ft[place_key_field])
            if key not in risk_event_keys:
                continue
            geom = ft.geometry()
            if geom is None or geom.isEmpty():
                continue
            g = QgsGeometry(geom)
            if place_transform is not None:
                g.transform(place_transform)
            if not g.isMultipart():
                try:
                    g.convertToMultiType()
                except Exception:
                    pass

            matched_event_keys.add(key)
            area = float(g.area())

            # Write an auditable event-cell polygon layer with event/risk column
            # names and interval provenance.
            # Persistent clean output.
            nf = QgsFeature(event_fields)
            nf.setGeometry(g)
            nf.setAttributes([
                key, transition, forecast_label, y1_ymd, y2_ymd,
                event_field, risk_field, area,
            ])
            if not event_sink.addFeature(nf, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(
                    f"Could not write authoritative event cell for {key}."
                )

            # A second attribute-free in-memory copy supports intersection;
            # it is not itself the persistent event-cell output.
            # Minimal memory geometry for overlay.
            mf = QgsFeature(event_mem.fields())
            mf.setGeometry(g)
            event_mem_provider.addFeature(mf, QgsFeatureSink.FastInsert)

            event_cell_count += 1
            event_cell_area += area

        del event_sink
        event_mem.updateExtents()

        # Stop if a Risk Table event cannot be located in KM_blocks, since
        # missing event geometry would bias spatial capture/recall.
        unmatched_event_keys = sorted(risk_event_keys.difference(matched_event_keys))
        if unmatched_event_keys:
            raise QgsProcessingException(
                f"{len(unmatched_event_keys):,} authoritative event places have no matching "
                f"fixed polygon using {risk_key_field}->{place_key_field}. Examples: "
                + ", ".join(unmatched_event_keys[:10])
            )

        feedback.pushInfo(
            f"[Authoritative event cells] cells={event_cell_count:,}; "
            f"area={event_cell_area / 1e6:.6f} km²"
        )

        # ------------------------------------------------------------------
        # F. Build actual process-specific footprint
        # ------------------------------------------------------------------
        # F. Build observed transition support. For most transitions this is
        # EA process geometry intersected with actual event-place cells.
        observed_method = ""
        observed_source_for_cleaning = None
        process_selected_count = 0

        # Erosion/deposition transitions require the corresponding EA polygons.
        # This does not include all physical erosion in the Active Domain.
        if required_process is not None:
            if process_src is None:
                raise QgsProcessingException(
                    f"{transition} requires the observed interval EA/process polygon layer."
                )

            # If the user did not specify an EA class field, attempt standard names.
            if not process_field:
                process_field = self._auto_process_field(process_src)
                if process_field:
                    feedback.pushInfo(
                        f"[Observed process] class field auto-selected: {process_field}"
                    )
                else:
                    raise QgsProcessingException(
                        "Observed process class field was blank and could not be auto-detected. "
                        "Available fields: " + ", ".join(process_src.fields().names())
                    )

            if process_field not in process_src.fields().names():
                raise QgsProcessingException(
                    f"Observed process field '{process_field}' does not exist. "
                    "Available fields: " + ", ".join(process_src.fields().names())
                )

            # Local predicate for EA polygon selection: an explicit class override
            # takes precedence over automatic erosion/deposition classification.
            # Local classifier respects explicit user-supplied process-class values.
            def keep_process(ft):
                raw = self._clean(ft[process_field])
                if override_values:
                    return raw in override_values
                return self._process_kind(raw) == required_process

            # Select only the physically relevant process geometry and
            # transform it into the prediction CRS before QGIS intersection.
            process_mem = self._materialise_polygon_source(
                process_src,
                target_crs,
                "observed_process_subset",
                feedback,
                filter_func=keep_process,
            )
            process_selected_count = process_mem.featureCount()
            if process_selected_count == 0:
                raise QgsProcessingException(
                    f"No {required_process.lower()} process polygons were selected from "
                    f"field '{process_field}'."
                )

            # Persist the exact intersection recipe as metadata for interpretation.
            observed_method = (
                f"{required_process.lower()}_intersect_authoritative_"
                f"{event_field.lower()}_cells"
            )

            # The intersection restricts observed geometry to BOTH: (1) the
            # process class (erosion or deposition) and (2) event=1 fixed places.
            observed_source_for_cleaning = processing.run(
                "native:intersection",
                {
                    "INPUT": process_mem,
                    "OVERLAY": event_mem,
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

        # DS->SF stabilisation is observed as a state transition; it has no
        # unique erosion/deposition polygon in the EA process map.
        else:
            # No direct mapped EA process represents stabilisation. Keep the
            # authoritative event-cell support as the spatially honest observed
            # target rather than inventing a sub-cell footprint.
            observed_method = f"authoritative_{event_field.lower()}_event_cells"
            observed_source_for_cleaning = event_mem

        observed_src = self._resolve_layer(observed_source_for_cleaning, context)
        if observed_src is None:
            raise QgsProcessingException(
                "Could not resolve the authoritative observed-transition geometry."
            )

        # Repair output geometry before area filtering and persistence;
        # this is a geometrical clean-up, not a different event definition.
        observed_fixed = processing.run(
            "native:fixgeometries",
            {
                "INPUT": observed_src,
                "METHOD": 1,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        observed_fixed_lyr = self._resolve_layer(observed_fixed, context)
        if observed_fixed_lyr is None:
            raise QgsProcessingException("Could not resolve fixed observed geometry.")

        # ------------------------------------------------------------------
        # G. Clean observed transition polygons
        # ------------------------------------------------------------------
        # G. Output actual process-specific transition polygons using a clean
        # schema, preserving the observational method and event field.
        obs_fields = QgsFields()
        obs_fields.append(QgsField("TRANSITION", QVariant.String, len=100))
        obs_fields.append(QgsField("FORECAST", QVariant.String, len=40))
        obs_fields.append(QgsField("Y1", QVariant.String, len=20))
        obs_fields.append(QgsField("Y2", QVariant.String, len=20))
        obs_fields.append(QgsField("OBS_METHOD", QVariant.String, len=160))
        obs_fields.append(QgsField("EVENT_FLD", QVariant.String, len=80))
        obs_fields.append(QgsField("RISK_FLD", QVariant.String, len=80))
        obs_fields.append(QgsField("OBS_AREA", QVariant.Double, len=20, prec=3))

        obs_sink, obs_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_OBSERVED,
            context,
            obs_fields,
            QgsWkbTypes.MultiPolygon,
            target_crs,
        )
        if obs_sink is None:
            raise QgsProcessingException("Could not create observed-transition sink.")

        obs_count = 0
        obs_area = 0.0
        # MIN_OBS_AREA applies to each fixed individual observed part.
        for ft in observed_fixed_lyr.getFeatures():
            geom = ft.geometry()
            if geom is None or geom.isEmpty():
                continue
            area = float(geom.area())
            if area < min_obs_area:
                continue
            nf = QgsFeature(obs_fields)
            nf.setGeometry(geom)
            nf.setAttributes([
                transition, forecast_label, y1_ymd, y2_ymd,
                observed_method, event_field, risk_field, area,
            ])
            if not obs_sink.addFeature(nf, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(
                    "Could not write observed process-specific transition polygon."
                )
            obs_count += 1
            obs_area += area
        del obs_sink

        # Do not silently report a zero-footprint comparison as successful.
        if obs_count == 0:
            raise QgsProcessingException(
                "The authoritative event-cell/process intersection produced zero "
                "observed transition area. Check EA interval/process class and event fields."
            )

        feedback.pushInfo(
            f"[Observed transition] method={observed_method}; "
            f"parts={obs_count:,}; area={obs_area / 1e6:.6f} km²"
        )

        # ------------------------------------------------------------------
        # H. Dissolved observed footprint
        # ------------------------------------------------------------------
        # H. Dissolve observed transition parts to a non-overlapping footprint.
        # Downstream Module 5d uses the actual area, not individual piece counts.
        obs_out_layer = self._resolve_layer(obs_id, context)
        if obs_out_layer is None:
            raise QgsProcessingException(
                "Could not resolve observed-transition output for dissolving."
            )

        # Unioning observed parts prevents duplicate area where source features
        # overlap and establishes a single physical footprint per transition.
        obs_diss = processing.run(
            "native:dissolve",
            {
                "INPUT": obs_out_layer,
                "FIELD": [],
                "SEPARATE_DISJOINT": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        obs_single = processing.run(
            "native:multiparttosingleparts",
            {
                "INPUT": obs_diss,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        obs_single_lyr = self._resolve_layer(obs_single, context)
        if obs_single_lyr is None:
            raise QgsProcessingException(
                "Could not resolve dissolved observed footprint."
            )

        # The final footprint retains only interval/transition/method metadata.
        foot_fields = QgsFields()
        foot_fields.append(QgsField("TRANSITION", QVariant.String, len=100))
        foot_fields.append(QgsField("FORECAST", QVariant.String, len=40))
        foot_fields.append(QgsField("Y1", QVariant.String, len=20))
        foot_fields.append(QgsField("Y2", QVariant.String, len=20))
        foot_fields.append(QgsField("OBS_METHOD", QVariant.String, len=160))
        foot_fields.append(QgsField("EVENT_FLD", QVariant.String, len=80))
        foot_fields.append(QgsField("OBS_AREA", QVariant.Double, len=20, prec=3))

        foot_sink, foot_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_OBSERVED_FOOTPRINT,
            context,
            foot_fields,
            QgsWkbTypes.MultiPolygon,
            target_crs,
        )
        if foot_sink is None:
            raise QgsProcessingException(
                "Could not create dissolved observed-footprint sink."
            )

        foot_count = 0
        foot_area = 0.0
        for ft in obs_single_lyr.getFeatures():
            geom = ft.geometry()
            if geom is None or geom.isEmpty():
                continue
            area = float(geom.area())
            nf = QgsFeature(foot_fields)
            nf.setGeometry(geom)
            nf.setAttributes([
                transition, forecast_label, y1_ymd, y2_ymd,
                observed_method, event_field, area,
            ])
            if not foot_sink.addFeature(nf, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(
                    "Could not write dissolved observed-footprint part."
                )
            foot_count += 1
            foot_area += area
        del foot_sink

        feedback.pushInfo(
            f"[Observed footprint] parts={foot_count:,}; "
            f"area={foot_area / 1e6:.6f} km²"
        )

        # ------------------------------------------------------------------
        # I. QA CSV
        # ------------------------------------------------------------------
        # I. Write the source-and-area QA CSV. Provenance includes which
        # PRIMARY/strict columns were used and how the observed footprint arose.
        qa_path = self.parameterAsFileOutput(parameters, self.OUTPUT_QA, context)
        if not qa_path:
            raise QgsProcessingException("A QA CSV output path is required.")
        os.makedirs(os.path.dirname(qa_path) or ".", exist_ok=True)

        with open(qa_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            # The QA CSV begins with a common schema. Later rows describe
            # threshold selections, event/risk populations and observed footprints.
            writer.writerow([
                "qa_group", "transition", "forecast", "y1", "y2",
                "risk_percentile_ge", "pctl_min", "n_features", "area_m2", "area_km2",
                "event_field", "risk_field", "method",
            ])

            # Report nested prediction cells and polygon-zone totals by cutoff;
            # these overlapping totals must be compared separately, not summed.
            for p in pctl_thresholds:
                writer.writerow([
                    "PREDICTED_RISK_CELLS", transition, forecast_label,
                    y1_ymd, y2_ymd, p, p / 100.0,
                    threshold_cell_counts[p], threshold_cell_areas[p],
                    threshold_cell_areas[p] / 1e6,
                    event_field, risk_field,
                    "P_STATUS=predicted and P_PCTL threshold",
                ])
                writer.writerow([
                    "PREDICTED_RISK_ZONES", transition, forecast_label,
                    y1_ymd, y2_ymd, p, p / 100.0,
                    threshold_zone_counts[p], threshold_zone_areas[p],
                    threshold_zone_areas[p] / 1e6,
                    event_field, risk_field,
                    "dissolved percentile cells",
                ])

            writer.writerow([
                "AUTHORITATIVE_RISK_ROWS", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                risk_rows, "", "",
                event_field, risk_field,
                "Risk Table rows with risk_set=1 in selected interval",
            ])
            writer.writerow([
                "AUTHORITATIVE_EVENT_ROWS", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                event_rows, "", "",
                event_field, risk_field,
                "Risk Table rows with event=1 in selected interval",
            ])
            writer.writerow([
                "AUTHORITATIVE_EVENT_CELLS", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                event_cell_count, event_cell_area, event_cell_area / 1e6,
                event_field, risk_field,
                "fixed place polygons matched to authoritative event places",
            ])
            writer.writerow([
                "PREDICTION_EVENT_CELLS", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                prediction_event_count, "", "",
                event_field, risk_field,
                "P_EVENT=1 among P_STATUS=predicted prediction rows",
            ])
            if required_process is not None:
                writer.writerow([
                    "OBSERVED_PROCESS_POLYGONS", transition, forecast_label,
                    y1_ymd, y2_ymd, "", "",
                    process_selected_count, "", "",
                    event_field, risk_field,
                    f"selected {required_process.lower()} geometry from {process_field}",
                ])
            writer.writerow([
                "OBSERVED_TRANSITION", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                obs_count, obs_area, obs_area / 1e6,
                event_field, risk_field,
                observed_method,
            ])
            writer.writerow([
                "OBSERVED_FOOTPRINT", transition, forecast_label,
                y1_ymd, y2_ymd, "", "",
                foot_count, foot_area, foot_area / 1e6,
                event_field, risk_field,
                "dissolved " + observed_method,
            ])

        feedback.pushInfo(f"[QA] Summary written: {qa_path}")
        feedback.setProgress(100)

        # Return layer destination IDs and QA CSV for downstream Module 5d.
        return {
            self.OUTPUT_RISK_CELLS: risk_cell_id,
            self.OUTPUT_RISK_ZONES: risk_zone_id,
            self.OUTPUT_EVENT_CELLS: event_cells_id,
            self.OUTPUT_OBSERVED: obs_id,
            self.OUTPUT_OBSERVED_FOOTPRINT: foot_id,
            self.OUTPUT_QA: qa_path,
        }
