# ============================================================================
# FLOODPLAIN REASSEMBLAGE ANALYSIS FRAMEWORK (FRAF) — PAPER 2 CODE ARCHIVE
# FRAF_P2_05_IntervalRiskTable_v6_7.py
# ============================================================================
#
# PURPOSE
# -------
# Construct the authoritative, NON-SPATIAL fixed-place x observation-interval
# modelling Risk Table from the independent state reconstruction, assemblage
# history and spatial-exposure sources. This is the Stage 4 Step 3 v6.7
# implementation, renamed for the Paper 2 reproducibility archive.
#
# POSITION IN THE REPRODUCIBLE WORKFLOW
# -------------------------------------
#   Module 3B / 03P: KM_blocks and PLACE_interval_long (authoritative states,
#                    transitions, primary ambiguity-bridged risk/event flags).
#   Module 4a / 03H: independent assemblage surface histories (descriptive and QA).
#   Stage 4 Step 2 / 04: one-row-per-place static assemblage attribution,
#                         retrospective union-domain weights, and an optional
#                         PLACE x GEOM_YMD channel-geometry covariate lookup.
#   THIS SCRIPT / 05: combines these sources into one interval risk table.
#   Downstream: R transition-specific history modelling and forecast validation.
#
# REQUIRED DATA SHAPES
# --------------------
#   PLACE_LONG: one row per (BLOCK_ID/PLACE_ID, interval start, interval end),
#               including Module 3 explicit endpoint states and primary fields.
#   PLACE_GEOM: KM_blocks with exactly one valid polygon per fixed place key.
#   ASM_LOOKUP: one non-spatial static-covariate row per matching place key.
#   TIMESTEP_GEOM_LOOKUP (optional): one row per place and exact GEOM_YMD.
#   Dated polygons/centrelines (optional): geometries no later than the interval
#               start are selected for time-varying spatial covariates.
#
# ONTOLOGY AND TRANSITIONS
# ------------------------
#   AD = ACTIVE_DOMAIN                 (current active-channel/active-zone domain)
#   DS = DEPOSITIONAL_STORAGE          (storage surface, NOT mature floodplain)
#   SF = STABILISED_FLOODPLAIN         (stabilised floodplain condition)
#   SF -> AD  REACTIVATE                 AD -> DS  STORAGE
#   DS -> SF  STABILISE                  DS -> AD  STORAGE_REWORK
#   SF -> DS  FP_STORAGE
#   UNRESOLVED denotes uncertain classification, not a fourth geomorphic state.
#
# EVENT AND ELIGIBILITY DISTINCTIONS — SCIENTIFICALLY MATERIAL
# ----------------------------------------------------------
# * Strict events/risk sets: inferred from two recognised Module 3 endpoint states.
# * Primary events/risk sets: read from Module 3's authoritative ambiguity-bridged
#   fields and checked against observed/latent state and event-risk invariants.
# * Broad FP -> AD prediction: combines eligible inherited/pre-existing floodplain
#   with SF; it explicitly does NOT admit DS. FP is a risk population, not a
#   fourth state. It is also NOT identical to the fixed INIT_FP first-event cohort.
# * INITIAL_FP/BASE_RISK: fixed baseline cohort, with separate first-event closure.
# * E_evt/D_evt: legacy aliases; raw observations are retained in E_EVT_RAW /
#   D_EVT_RAW for provenance and disagreement QA.
#
# TEMPORAL INTEGRITY AND INTERPRETATION
# -------------------------------------
# * ASM_*_PREV and the dated spatial covariates are constructed from evidence
#   available at or before the start (T1) of each observation interval.
# * The output ALSO carries static whole-record assemblage descriptors (for
#   descriptive mapping/QA) and optional *_NEXT outcomes. These fields may encode
#   later information and MUST NOT automatically be used as predictors in a
#   historical or held-out forecast; downstream feature selection must prevent
#   temporal leakage. A single reference centreline can likewise be retrospective.
# * The observational intervals may have different elapsed lengths; this script
#   preserves the existing date/duration fields rather than asserting an annual
#   transition frequency from irregularly spaced observations.
# * Fixed grid polygons are only consulted for geometries; output interval rows
#   have no geometry and must be mapped through an explicit ID join.
#
# GEOMETRY, UNITS AND REPRODUCIBILITY
# -----------------------------------
# * Spatial input CRS must match KM_blocks and should be a suitable projected CRS;
#   measured distances are in source-map units and polygon areas are in squared
#   source-map units (the union-field names use M2).
# * v6.7 requires a compatible Module 3 semantic/primary-state field schema.
# * Union-channel static weights describe a retrospective comparison domain,
#   NOT a dynamic interval-start channel mask and NOT a risk-set criterion.
# * Fail-fast checks reject duplicate spatial/static/composite interval keys,
#   missing required states, broken union-area identities and final event-risk QA.
# * Designed for PyQGIS / QGIS Processing. It cannot run in ordinary Python
#   without the QGIS runtime and relevant providers.
#
# CODE LINEAGE AND ATTRIBUTION
# ----------------------------
# FRAF adaptation and Paper 2 archive preparation: Martin Dawson, with
# ChatGPT-assisted code documentation/review. Related SCS methodological lineage:
# Rusnák et al. (2025), 'A channel shifting GIS toolbox for exploring floodplain
# dynamics through channel erosion and deposition', Geomorphology 477, 109688,
# https://doi.org/10.1016/j.geomorph.2025.109688. This reference is to scientific
# background, not a claim that its authors wrote this FRAF v6.7 source.
#
# ARCHIVE-PRESERVATION NOTE
# -------------------------
# This edition adds only Python comments. Algorithm ID, class, parameter names,
# statements, numerical logic, thresholds, schema and QGIS calls are unchanged.
# Syntax-tree and significant-token equivalence are checked during preparation;
# run-specific QGIS data validation remains the responsibility of a full run.
# ============================================================================

# State terminology: STABILISED_FLOODPLAIN -> ACTIVE_DOMAIN is REACTIVATE_EVT.
# v6.7: adds broadened floodplain -> Active Domain prediction eligibility.
#       Undisturbed initial/pre-existing floodplain can enter a separate FP_REACTIVATE
#       risk/event population without changing the strict STABILISED_FLOODPLAIN -> ACTIVE_DOMAIN model.
# v6.6a: adds robust timestep-table field resolution and GeoPackage sublayer diagnostics.
# v6.6: carries and validates full-analysis-area versus union-channel weights.
# Retains the v6.5 Stage 4 split table-geometry architecture. Read authoritative non-spatial
# PLACE_interval_long plus one-row-per-BLOCK_ID KM_blocks separately; preserve Module 3B
# primary ambiguity-bridged events/risk sets; join exact interval-start covariates from
# Stage 4 Step 2 v6.4; write the authoritative modelling Risk Table without geometry.

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsFeatureSink,
    QgsWkbTypes,
    QgsGeometry
)
from qgis.PyQt.QtCore import QVariant
import re
import math


class Stage4_Step3_RiskTableBuilder_v6_7(QgsProcessingAlgorithm):
    """
    Stage 4 Step 3 — State/storage-aware KM/AG/Cox Risk Table Builder v6.7.

    Builds a modelling-ready PLACE_ID x interval table using three core states:

        ACTIVE_DOMAIN
        DEPOSITIONAL_STORAGE
        STABILISED_FLOODPLAIN

    Transition-specific event and risk-set logic:
    
        REACTIVATE_EVT       = STABILISED_FLOODPLAIN -> ACTIVE_DOMAIN
        STORAGE_EVT          = ACTIVE_DOMAIN -> DEPOSITIONAL_STORAGE
        STABILISE_EVT        = DEPOSITIONAL_STORAGE -> STABILISED_FLOODPLAIN
        STORAGE_REWORK_EVT    = DEPOSITIONAL_STORAGE -> ACTIVE_DOMAIN
        FP_STORAGE_EVT        = STABILISED_FLOODPLAIN -> DEPOSITIONAL_STORAGE
        ANY_STATE_EVT        = any valid change between the three states

        REACTIVATE_RISK_SET  = T1 is STABILISED_FLOODPLAIN
        STORAGE_RISK_SET     = T1 is ACTIVE_DOMAIN
        STABILISE_RISK_SET   = T1 is DEPOSITIONAL_STORAGE
        STORAGE_REWORK_RISK_SET = T1 is DEPOSITIONAL_STORAGE
        FP_STORAGE_RISK_SET  = T1 is STABILISED_FLOODPLAIN

    v6.7 broadened prediction population (additional; strict fields unchanged):
        PREEXISTING_FP_START = undisturbed initial floodplain at T1 that is not
                               recognised as ACTIVE_DOMAIN / DEPOSITIONAL_STORAGE /
                               STABILISED_FLOODPLAIN, with negligible active/storage
                               area support at interval start.
        FP_REACTIVATE_RISK_SET = strict SF risk OR PREEXISTING_FP_START
        FP_REACTIVATE_EVT      = eligible floodplain -> ACTIVE_DOMAIN
        *_PRIMARY versions retain Module 3 ambiguity-bridge semantics for strict SF
        and allow pre-existing floodplain to transition to an observed/latent active T2.

    The broadened fields are for erosion forecasting. They do not replace or alter
    REACTIVATE_EVT / REACTIVATE_RISK_SET used for process-specific SF -> AD inference.

    v6.6 union-domain addition:
      - validates static full-area and union-channel overlap weights from Step 2;
      - carries those fields unchanged to every interval row;
      - fails before output when area balance or overlap fractions are invalid;
      - uses generic river-style terminology: Meandering/Anabranching and Braided.

    v6.5 safeguards and semantics:
      - transition events can be confirmed by Module 3B E_evt/D_evt thresholds;
      - source event flags cannot override an incompatible state transition;
      - baseline first-reactivation risk stops after the first event;
      - interval-history fields are not copied as static predictors;
      - *_PREV histories use information available at interval start only;
      - binary non-active occupancy is not silently equated with stabilised floodplain;
      - dated covariates never use a future layer as a fallback.
    """

    # The three inputs below deliberately separate interval history from reusable geometry.
    PLACE_LONG = "PLACE_LONG"
    PLACE_GEOM = "PLACE_GEOM"
    ASM_LOOKUP = "ASM_LOOKUP"
    TIMESTEP_GEOM_LOOKUP = "TIMESTEP_GEOM_LOOKUP"

    # Optionally insist that retrospective union-domain metrics are complete and valid.
    REQUIRE_UNION_DOMAIN_FIELDS = "REQUIRE_UNION_DOMAIN_FIELDS"

    # Dated geometry is distinct from the static assemblage lookup.
    CENTRELINES = "CENTRELINES"
    CENTRELINE_MODE = "CENTRELINE_MODE"
    REFERENCE_CENTRELINE = "REFERENCE_CENTRELINE"
    WATER_LAYERS = "WATER_LAYERS"
    ACTIVE_LAYERS = "ACTIVE_LAYERS"

    # Boolean switches control which spatial predictors are attributed.
    CALC_CENTRELINE = "CALC_CENTRELINE"
    CALC_CURVATURE = "CALC_CURVATURE"
    CALC_WATER = "CALC_WATER"
    CALC_ACTIVE = "CALC_ACTIVE"
    INCLUDE_NEXT = "INCLUDE_NEXT"
    REQUIRE_PROCESS_CONFIRMATION = "REQUIRE_PROCESS_CONFIRMATION"

    CURV_WINDOW = "CURV_WINDOW"
    CHANNEL_WIDTH = "CHANNEL_WIDTH"

    OUTPUT = "OUTPUT"

    # Interval-varying states, timing, source QA, and primary fields remain row-specific.
    # Fields copied from PLACE_interval_long when present.
    BASE_FIELDS = [
        "PLACE_ID", "BLOCK_ID",
        "y1", "y2",
        "tstart_yr", "tstop_yr",
        "A_block",
        "A_E", "A_D",
        "P_E", "P_D",
        "E_evt", "D_evt",
        "A_C1", "A_C2",
        "P_C1", "P_C2",
        "C1", "C2",
        "state1", "state2",
        "at_risk", "Enter", "Exit",
        "ACTIVE_T1", "ACTIVE_T2", "ACTIVE_DOM",
        "DOMAIN_T1", "DOMAIN_T2", "DOMAIN_TRANS",
        "DIST_EVENT", "DIST_TYPE", "DEPO_INTERP",
        "SURFACE_T1", "SURFACE_T2", "ONTOLOGY",
        "M3_AUTHORITATIVE", "M3_STATE_SOURCE_T1", "M3_STATE_SOURCE_T2", "M3_STATE_CHAIN_OK",
        "M3_LATENT_STATE_T1", "M3_LATENT_STATE_T2",
        "M3_AMBIGUITY_RUN_ID", "M3_AMBIGUITY_RUN_LENGTH",
        "M3_AMBIGUITY_START_YMD", "M3_AMBIGUITY_RESOLVED", "M3_BRIDGED_TRANS",
        "REACTIVATE_EVT_PRIMARY", "STORAGE_EVT_PRIMARY", "STABILISE_EVT_PRIMARY",
        "STORAGE_REWORK_EVT_PRIMARY", "FP_STORAGE_EVT_PRIMARY", "ANY_STATE_EVT_PRIMARY",
        "REACTIVATE_BRIDGED", "STORAGE_BRIDGED", "STORAGE_REWORK_BRIDGED", "FP_STORAGE_BRIDGED",
        "REACTIVATE_RISK_SET_PRIMARY", "STORAGE_RISK_SET_PRIMARY",
        "STABILISE_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET_PRIMARY",
        "FP_STORAGE_RISK_SET_PRIMARY", "ANY_STATE_RISK_SET_PRIMARY",
        "BASE_REACTIVATE_RISK_SET_PRIMARY",
        "M3_ACTIVE_FRAC_T1", "M3_ACTIVE_FRAC_T2",
        "M3_STORAGE_FRAC_T1", "M3_STORAGE_FRAC_T2",
        "M3_STAB_FP_FRAC_T1", "M3_STAB_FP_FRAC_T2",
        "M3_UNRESOLVED_FRAC_T1", "M3_UNRESOLVED_FRAC_T2",
        "M3_STATE_SUM_T1", "M3_STATE_SUM_T2",
        "M3_BACKGROUND_FRAC", "M3_STABLE_EVID_FRAC",
        "M3_STATE_SUPPORT_T1", "M3_STATE_SUPPORT_T2", "M3_STATE_CONF_T1", "M3_STATE_CONF_T2",
        "M3_MIXED_T1", "M3_MIXED_T2", "STORAGE_AGE_YR_T1", "STORAGE_AGE_YR_T2",
        "STORAGE_START_YMD_T1", "STORAGE_START_YMD_T2", "STORAGE_CLOCK_RESET_T2",
        "STORAGE_REWORK_EVT", "STORAGE_REWORK_RISK_SET", "FP_STORAGE_EVT", "FP_STORAGE_RISK_SET",
        "REACTIVATE_CONFIRMED", "STORAGE_CONFIRMED", "STABILISE_CONFIRMED",
        "STORAGE_REWORK_CONFIRMED", "FP_STORAGE_CONFIRMED",
        "REACTIVATE_CONFIRMED_PRIMARY", "STORAGE_CONFIRMED_PRIMARY",
        "STABILISE_CONFIRMED_PRIMARY", "STORAGE_REWORK_CONFIRMED_PRIMARY",
        "FP_STORAGE_CONFIRMED_PRIMARY",
        "M3_ACTIVE_STATE_THR", "M3_ACTIVE_CONTACT_THR", "M3_MIXED_FRAC_THR",
        "M3_BG_STATE_THR", "M3_STABILISE_YEARS", "M3_STABILISE_MODE", "M3_STABLE_EVID_THR",
        "M3_BACKGROUND_SOURCE",
        "QA_ACTIVE_BELOW_THRESHOLD", "QA_NONACTIVE_ABOVE_THRESHOLD",
        "QA_ACTIVE_TO_STABLE", "QA_STABILISE_TOO_EARLY", "QA_INITIAL_STABLE_NO_EVIDENCE",
        "QA_STORAGE_WITHOUT_HISTORY", "QA_BACKGROUND_ACTIVE_OVERLAP", "QA_PROCESS_DOMAIN_MISMATCH",
        "QA_UNRESOLVED_ENDPOINT", "QA_MIXED_ENDPOINT", "QA_CLOCK_INCONSISTENT",
        "QA_STATE_SOURCE_INCONSISTENT", "QA_STATE_FRACTION_SUM",
        "QA_LATENT_STATE_INCONSISTENT", "QA_BRIDGED_TRANS_INVALID",
        "M3_ANOMALY_COUNT", "M3_ANOMALY_SEVERITY", "M3_ANOMALY_FLAGS"
    ]

    # Static coordinates/areas are sourced only from unique KM_blocks polygons.
    STATIC_PLACE_FIELDS = [
        "X", "Y",
        "AREA", "A_place",
        "GRID_ID", "ROW_ID", "COL_ID"
    ]

    # Seven nested-domain weights are inherited unchanged from the previous module.
    UNION_DOMAIN_FIELDS = [
        "ASM_BLOCK_AREA_M2",
        "ASM_UNION_OVERLAP_M2",
        "ASM_UNION_FRAC",
        "ASM_OUTSIDE_UNION_M2",
        "ASM_UNION_CONTACT",
        "ASM_UNION_BOUNDARY",
        "ASM_UNION_CORE50",
    ]

    # The fixed first-event baseline cohort is separate from recurrent SF and broad FP eligibility.
    # Initial-floodplain cohort fields from Module 3B and earlier Stage 4 Step 2 outputs.
    # These define the baseline floodplain population:
    #   buffered analysis corridor - first active-domain / first EA-pair footprint.
    INITIAL_COHORT_FIELDS = [
        "INIT_FP",
        "INIT_FP_AREA",
        "INIT_FP_PROP",
        "BASE_RISK",
        "BASE_RISK_DEF",
    ]

    # Expose the pre-existing QGIS algorithm identifier; file renaming does not alter it.
    def name(self):
        return "stage4_step3_risk_table_v6_7_broad_fp_reactivation"

    # Display the legacy Stage 4 Step 3 label in the QGIS Processing toolbox.
    def displayName(self):
        return "Stage 4 Step 3 — Risk Table v6.7 — broad floodplain reactivation"

    # Document the strict/primary and broad FP prediction populations for QGIS users.
    def shortHelpString(self):
        return (
            "Stage 4 Step 3 builds the modelling Risk Table from separate authoritative "
            "inputs: PLACE_interval_long supplies interval states/events/risk sets; KM_blocks "
            "supplies one fixed polygon per BLOCK_ID; Stage 4 Step 2 supplies static and "
            "optional timestep covariate lookups. No PLACE_interval_long polygon copy or "
            "registered spatial view is required. Spatial distances are calculated from the "
            "single KM_blocks geometry for each PLACE, while the output remains a non-spatial "
            "GeoPackage table suitable for R. Primary models use *_EVT_PRIMARY, "
            "*_RISK_SET_PRIMARY and M3_MODEL_ELIGIBLE_PRIMARY; strict fields are retained "
            "for sensitivity analysis. Static union-channel overlap fields from Step 2 are "
            "validated and copied for retrospective full-area versus union-area summaries. "
            "v6.7 also writes a separate FP_REACTIVATE_* prediction population that adds "
            "undisturbed initial/pre-existing floodplain to strict Stabilised Floodplain; "
            "the original REACTIVATE_* process-transition fields are unchanged. "
            "River-style terminology is generic: Meandering/Anabranching and Braided."
        )

    # Keep the original QGIS Processing toolbox group for installation compatibility.
    def group(self):
        return "SCS Toolbox"

    # Preserve the original internal Processing group identifier.
    def groupId(self):
        return "scs_toolbox"

    # Create a new instance of the original Processing algorithm class.
    def createInstance(self):
        return Stage4_Step3_RiskTableBuilder_v6_7()

    # Declare independent interval, geometry, lookup and dated spatial inputs; set output sink.
    def initAlgorithm(self, config=None):
        # Authoritative modelling rows come from non-spatial Module 3B PLACE_interval_long.
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.PLACE_LONG,
            "PLACE_interval_long (authoritative non-spatial table from Module 3B v4.5+)",
            types=[QgsProcessing.TypeVector]
        ))

        # Only KM_blocks supplies the permanent fixed-place geometry.
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.PLACE_GEOM,
            "KM_blocks / fixed PLACE geometry (one polygon per BLOCK_ID)",
            types=[QgsProcessing.TypeVectorPolygon]
        ))

        # One-row-per-place assemblage-history attribution is joined by stable place ID.
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.ASM_LOOKUP,
            "PLACE_static_covariates lookup from Stage 4 Step 2",
            types=[QgsProcessing.TypeVector]
        ))

        # Default requires the full-corridor/union-domain comparison to be available.
        self.addParameter(QgsProcessingParameterBoolean(
            self.REQUIRE_UNION_DOMAIN_FIELDS,
            "Require and validate full-area versus union-channel fields from Step 2",
            defaultValue=True
        ))

        # Optional exact-dated PLACE x GEOM_YMD channel exposures are a separate input.
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.TIMESTEP_GEOM_LOOKUP,
            "Optional PLACE_dynamic_geometry_covariates lookup from Stage 4 Step 2 v6.4",
            types=[QgsProcessing.TypeVector],
            optional=True
        ))

        # Dated Active Domain distances can be enabled independently of channel geometry.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_ACTIVE,
            "Calculate active-zone / active-domain distance covariates",
            defaultValue=True
        ))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.ACTIVE_LAYERS,
            "Dated active-zone / active-domain polygon layers",
            layerType=QgsProcessing.TypeVectorPolygon,
            optional=True
        ))

        # Water masks are optional and do not define the three organisational states.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_WATER,
            "Calculate water-mask distance covariates",
            defaultValue=False
        ))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.WATER_LAYERS,
            "Dated water polygon layers",
            layerType=QgsProcessing.TypeVectorPolygon,
            optional=True
        ))

        # Centreline exposure may use dated or one shared reference geometry.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_CENTRELINE,
            "Calculate centreline distance covariates",
            defaultValue=True
        ))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.CENTRELINES,
            "Dated channel centreline layers",
            layerType=QgsProcessing.TypeVectorLine,
            optional=True
        ))

        # Date-specific lines are preferable where temporal geometry is available.
        self.addParameter(QgsProcessingParameterEnum(
            self.CENTRELINE_MODE,
            "Centreline covariate mode",
            options=[
                "Dated centreline by interval",
                "Single reference centreline"
            ],
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterVectorLayer(
            self.REFERENCE_CENTRELINE,
            "Single reference centreline",
            types=[QgsProcessing.TypeVectorLine],
            optional=True
        ))

        # Curvature is conditional on centreline geometry being enabled.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_CURVATURE,
            "Calculate centreline curvature covariates",
            defaultValue=True
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.CURV_WINDOW,
            "Curvature half-window distance in layer units",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=600.0,
            minValue=1.0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.CHANNEL_WIDTH,
            "Representative channel width for dimensionless curvature scaling",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=600.0,
            minValue=0.0
        ))

        # Legacy confirmation switch is retained but explicitly disabled during execution.
        self.addParameter(QgsProcessingParameterBoolean(
            self.REQUIRE_PROCESS_CONFIRMATION,
            "Require Module 3B E_evt/D_evt confirmation for reactivation/storage events",
            defaultValue=True
        ))

        # NEXT outcome fields are optional TARGETS, not safe contemporary predictors.
        self.addParameter(QgsProcessingParameterBoolean(
            self.INCLUDE_NEXT,
            "Include next-interval state event targets",
            defaultValue=True
        ))

        # Write a single non-spatial (NoGeometry) modelling table.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            "Authoritative non-spatial Stage 4 Risk Table"
        ))

    # ------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------

    # Resolve schema names robustly; field aliases and case variants are supported.
    def _field_index(self, fields_or_layer, name):
        """Resolve a provider field by exact name, case-insensitive name, or alias."""
        try:
            fields = fields_or_layer.fields()
        except Exception:
            fields = fields_or_layer
        try:
            idx = fields.indexFromName(name)
            if idx >= 0:
                return idx
        except Exception:
            pass

        # Casefold handles differences in provider field-capitalisation.
        target = str(name).strip().casefold()
        for i, fld in enumerate(fields):
            try:
                actual = str(fld.name()).strip().casefold()
            except Exception:
                actual = ""
            try:
                alias = str(fld.alias()).strip().casefold()
            except Exception:
                alias = ""
            if actual == target or (alias and alias == target):
                return i
        return -1

    # Use the same resilient field-name resolution for presence checks.
    def _field_exists(self, layer, name):
        return self._field_index(layer, name) >= 0

    # Return the provider's actual spelling, not a requested alias.
    def _resolved_field_name(self, layer, name):
        idx = self._field_index(layer, name)
        return layer.fields()[idx].name() if idx >= 0 else None

    # Read a feature attribute defensively without confusing an absent field with a value.
    # A missing/null-like field maps to the supplied default; downstream QA handles it.
    def _get(self, feat, name, default=None):
        try:
            idx = self._field_index(feat.fields(), name)
            if idx < 0:
                return default
            v = feat[idx]
            if v == "" or v == "NULL":
                return default
            return v
        except Exception:
            return default

    # Parse integer-like flags while preserving a caller-specified missing-value default.
    def _as_int(self, v, default=0):
        try:
            if v is None or v == "":
                return default
            return int(float(v))
        except Exception:
            return default

    # Convert numeric attributes and reject NaN as absent data.
    def _as_float(self, v, default=None):
        try:
            if v is None or v == "":
                return default
            x = float(v)
            if math.isnan(x):
                return default
            return x
        except Exception:
            return default

    # Construct output schemas without adding duplicate field names.
    def _append_unique(self, fields, qgs_field):
        if fields.indexFromName(qgs_field.name()) < 0:
            fields.append(qgs_field)

    # Preserve the source field type/width when passing through existing metadata.
    # Copies types without modifying the source layer itself.
    def _copy_field(self, src_layer, src_name, out_name=None, fallback=QVariant.String):
        out_name = out_name or src_name
        idx = src_layer.fields().indexFromName(src_name)
        if idx >= 0:
            f = src_layer.fields()[idx]
            return QgsField(out_name, f.type(), f.typeName(), f.length(), f.precision())
        return QgsField(out_name, fallback)

    # Prefer BLOCK_ID, falling back to PLACE_ID only for compatible legacy inputs.
    def _best_key_field(self, layer):
        for k in ["BLOCK_ID", "PLACE_ID"]:
            resolved = self._resolved_field_name(layer, k)
            if resolved is not None:
                return resolved
        return None

    # Parse supported filename/attribute date representations to YYYYMMDD integers.
    def _date_from_text(self, txt):
        if txt is None:
            return None
        s = str(txt)

        # Prefer complete observation dates to imputed year-only January 1 anchors.
        # yyyymmdd
        m = re.search(r"(?:18|19|20)\d{6}", s)
        if m:
            return int(m.group(0))

        # yyyy_mm_dd, yyyy-mm-dd, yyyy mm dd
        m = re.search(r"((?:18|19|20)\d{2})[_\- ]?(\d{2})[_\- ]?(\d{2})", s)
        if m:
            return int(m.group(1) + m.group(2) + m.group(3))

        # yyyy only
        m = re.search(r"(?:18|19|20)\d{2}", s)
        if m:
            return int(m.group(0) + "0101")

        return None

    # Use the LAST date in an interval label for period-end identification.
    def _period_end_from_text(self, txt):
        """Parse the last date/year in an interval label as its end date."""
        if txt is None:
            return None
        s = str(txt)

        dates8 = re.findall(r"(?<!\d)(?:18|19|20)\d{6}(?!\d)", s)
        if dates8:
            return int(dates8[-1])

        triples = re.findall(
            r"((?:18|19|20)\d{2})[_\- ](\d{2})[_\- ](\d{2})",
            s,
        )
        if triples:
            y, m, d = triples[-1]
            return int(y + m + d)

        years = re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)", s)
        if years:
            return int(years[-1]) * 10000 + 101

        return None

    # Expand a year-only value to a January 1 YYYYMMDD key when needed.
    def _to_ymd(self, y):
        y = self._as_int(y, None)
        if y is None:
            return None
        if y < 10000:
            return y * 10000 + 101
        return y

    # Identify a dated spatial layer from recognised fields or its filename.
    def _date_from_layer(self, layer):
        # Date search order follows known QGIS/EA field conventions.
        for fld in ["PeriodEnd", "End_ymd", "YMD", "ymd", "DATE", "Date", "date", "Year", "year"]:
            if self._field_exists(layer, fld):
                for f in layer.getFeatures():
                    d = self._date_from_text(f[fld])
                    if d:
                        return d
        return self._date_from_text(layer.name())

    # Use an interior point of each fixed polygon for exposure and distance measures.
    def _representative_geometry(self, geom):
        if geom is None or geom.isEmpty():
            return None
        if geom.type() == QgsWkbTypes.PolygonGeometry:
            try:
                # Points on the polygon interior avoid centroids falling outside concave cells.
                return geom.pointOnSurface()
            except Exception:
                return geom.centroid()
        return geom

    # Unify each date-specific source into one geometry while reporting progress.
    def _combine_layer_geometry(self, layer, feedback=None, label="source"):
        """
        Combine a polygon/line layer into one geometry.

        v5 used iterative geometry.combine(), which can be very slow on complex
        annual channel polygons and gives no feedback while it is working.  This
        version:
          - reports feature counts before combining;
          - returns the single geometry directly when featureCount()==1;
          - uses QgsGeometry.unaryUnion(list_of_geometries) for multi-feature
            layers, with a safe fallback to iterative combine.
        """
        if layer is None or not layer.isValid():
            return None

        try:
            fc = layer.featureCount()
        except Exception:
            fc = -1

        if feedback:
            feedback.pushInfo(f"[Stage 4 Step 3] Combining {label}: {layer.name()} | features={fc:,}")

        # Materialise geometries once for unaryUnion; failure uses an iterative fallback.
        geoms = []
        for i, f in enumerate(layer.getFeatures()):
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            geoms.append(QgsGeometry(g))

            # Give the Processing dialog life-signs on very large layers.
            if feedback and i > 0 and i % 5000 == 0:
                feedback.pushInfo(f"[Stage 4 Step 3]   read {i:,} geometries from {layer.name()}...")

        if not geoms:
            return None

        if len(geoms) == 1:
            if feedback:
                feedback.pushInfo(f"[Stage 4 Step 3] Combined {label}: single geometry used directly.")
            return geoms[0]

        try:
            out = QgsGeometry.unaryUnion(geoms)
            if feedback:
                feedback.pushInfo(f"[Stage 4 Step 3] Combined {label}: unaryUnion complete ({len(geoms):,} geometries).")
            return out
        except Exception as e:
            if feedback:
                feedback.pushWarning(f"[Stage 4 Step 3] unaryUnion failed for {layer.name()}; falling back to iterative combine: {e}")

        out = None
        for i, g in enumerate(geoms):
            if out is None:
                out = g
            else:
                try:
                    out = out.combine(g)
                except Exception:
                    pass
            if feedback and i > 0 and i % 1000 == 0:
                feedback.pushInfo(f"[Stage 4 Step 3]   iterative combine {i:,}/{len(geoms):,} for {layer.name()}...")
        return out

    # Validate one geometry per place and cache representative geometry/static attributes.
    def _build_place_geom_lookup(self, layer, feedback):
        """Index the authoritative fixed KM_blocks geometry and fail on key defects."""
        key = self._best_key_field(layer)
        if key is None:
            raise QgsProcessingException(
                "KM_blocks must contain BLOCK_ID (preferred) or PLACE_ID."
            )

        # A duplicate BLOCK_ID is an error; choosing an arbitrary polygon would bias exposure.
        lookup = {}
        duplicate_n = 0
        missing_n = 0
        empty_n = 0
        for feat in layer.getFeatures():
            pid = self._get(feat, key)
            if pid is None or str(pid).strip() == "":
                missing_n += 1
                continue
            skey = str(pid)
            if skey in lookup:
                duplicate_n += 1
                continue
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                empty_n += 1
                continue
            representative = self._representative_geometry(geom)
            if representative is None or representative.isEmpty():
                empty_n += 1
                continue
            # Store one representative point and the corresponding static feature attributes.
            lookup[skey] = {
                "attrs": {fld.name(): feat[fld.name()] for fld in layer.fields()},
                "geom": representative,
            }

        feedback.pushInfo(
            f"[Stage 4 Step 3] KM_blocks indexed by {key} | "
            f"features={layer.featureCount():,}; usable={len(lookup):,}; "
            f"missing IDs={missing_n:,}; duplicates={duplicate_n:,}; "
            f"empty geometries={empty_n:,}."
        )
        if missing_n or duplicate_n or empty_n:
            raise QgsProcessingException(
                "KM_blocks failed fixed-geometry QA. The layer must contain exactly one "
                "valid polygon for every non-null BLOCK_ID/PLACE_ID; no first-row or "
                "duplicate-geometry fallback is permitted."
            )
        if not lookup:
            raise QgsProcessingException("KM_blocks contains no usable PLACE geometries.")
        return lookup, key

    # Validate one static assemblage row per place: duplicates must fail, not collapse.
    def _build_table_lookup(self, layer, feedback, label):
        """Index a one-row-per-PLACE lookup and fail rather than collapse duplicates."""
        key = self._best_key_field(layer)
        if key is None:
            raise QgsProcessingException(f"{label} must contain BLOCK_ID or PLACE_ID.")

        # Static lookup cardinality is exactly one row per fixed PLACE/BLOCK key.
        lookup = {}
        duplicate_n = 0
        missing_n = 0
        for feat in layer.getFeatures():
            pid = self._get(feat, key)
            if pid is None or str(pid).strip() == "":
                missing_n += 1
                continue
            skey = str(pid)
            if skey in lookup:
                duplicate_n += 1
                continue
            lookup[skey] = {fld.name(): feat[fld.name()] for fld in layer.fields()}

        feedback.pushInfo(
            f"[Stage 4 Step 3] {label} indexed by {key} | "
            f"rows={layer.featureCount():,}; usable={len(lookup):,}; "
            f"missing IDs={missing_n:,}; duplicates={duplicate_n:,}."
        )
        if missing_n or duplicate_n:
            raise QgsProcessingException(
                f"{label} must contain exactly one row per BLOCK_ID/PLACE_ID. "
                "Correct Stage 4 Step 2 output rather than allowing first-row collapse."
            )
        if not lookup:
            raise QgsProcessingException(f"{label} contains no usable rows.")
        return lookup, key

    # Validate and index precise (place key, GEOM_YMD) geometry covariates.
    def _build_timestep_geom_lookup(self, layer, feedback):
        """Index Step 2 rows by the exact PLACE/BLOCK ID + GEOM_YMD key.

        The modelling join is deliberately date-exact. Year-only and nearest-date
        fallbacks are not permitted because they can substitute the wrong channel
        geometry for an interval start.
        """
        if layer is None or not layer.isValid():
            return {"exact": {}, "fields": []}

        field_names = layer.fields().names()
        try:
            source_uri = layer.source()
        except Exception:
            source_uri = "<unavailable>"
        try:
            provider = layer.providerType()
        except Exception:
            provider = "<unknown>"
        try:
            row_count = layer.featureCount()
        except Exception:
            row_count = -1

        # Log provider and GeoPackage sublayer metadata to diagnose wrong-table selection.
        feedback.pushInfo(
            "[Stage 4 Step 3] Timestep geometry input preflight | "
            f"layer='{layer.name()}'; provider={provider}; rows={row_count:,}; "
            f"source={source_uri}; fields={field_names}"
        )

        key = self._best_key_field(layer)
        if key is None:
            raise QgsProcessingException(
                "The layer supplied as Timestep geometry lookup exposes neither BLOCK_ID "
                "nor PLACE_ID. The selected GeoPackage may have been opened without an "
                "explicit sublayer. Select the loaded PLACE_dynamic_geometry_covariates "
                "table, or use a URI ending '|layername=PLACE_dynamic_geometry_covariates'. "
                f"Received layer='{layer.name()}', source='{source_uri}', fields={field_names}."
            )
        geom_ymd_field = self._resolved_field_name(layer, "GEOM_YMD")
        if geom_ymd_field is None:
            raise QgsProcessingException(
                "The selected timestep geometry layer does not expose GEOM_YMD. "
                f"Received layer='{layer.name()}', source='{source_uri}', fields={field_names}."
            )

        feedback.pushInfo(
            f"[Stage 4 Step 3] Timestep geometry fields resolved | ID={key}; "
            f"date={geom_ymd_field}."
        )

        # Composite keys prevent incorrect alignment across different observed channel dates.
        exact = {}
        duplicates = 0
        missing_keys = 0
        for feat in layer.getFeatures():
            pid = self._get(feat, key, None)
            ymd = self._as_int(self._get(feat, geom_ymd_field, None), None)
            if pid is None or str(pid).strip() == "" or ymd is None:
                missing_keys += 1
                continue
            attrs = {name: feat[name] for name in field_names}
            ekey = (str(pid), ymd)
            if ekey in exact:
                duplicates += 1
            else:
                exact[ekey] = attrs
        feedback.pushInfo(
            f"[Stage 4 Step 3] Exact timestep geometry index | rows={layer.featureCount():,}; "
            f"usable BLOCK_ID+GEOM_YMD keys={len(exact):,}; missing keys={missing_keys:,}; "
            f"duplicates={duplicates:,}."
        )
        if missing_keys or duplicates:
            raise QgsProcessingException(
                "Stage 4 Step 2 timestep geometry lookup failed composite-key QA. It must "
                "contain one unique non-null BLOCK_ID/PLACE_ID + GEOM_YMD row."
            )
        return {"exact": exact, "fields": field_names}

    # Retrieve only the row corresponding to the exact interval-start date.
    # A missing exact date remains missing, rather than being substituted by a future date.
    def _select_timestep_geom_attrs(self, lookup, pid, target_ymd):
        if not lookup or target_ymd is None:
            return None
        return lookup.get("exact", {}).get((str(pid), int(target_ymd)))

    # Sort and combine spatial inputs by observation date.
    # Input features of a single date are united before distance calculations.
    def _index_dated_layers(self, layers, feedback, label):
        idx = []
        date_counts = {}
        for lyr in layers or []:
            d = self._date_from_layer(lyr)
            if d is None:
                feedback.pushWarning(f"[Stage 4 Step 3] {label} layer has no parseable date: {lyr.name()}")
                continue
            g = self._combine_layer_geometry(lyr, feedback, label)
            if g is None or g.isEmpty():
                feedback.pushWarning(f"[Stage 4 Step 3] {label} layer has no usable geometry: {lyr.name()}")
                continue
            idx.append((d, g, lyr.name()))
            date_counts[d] = date_counts.get(d, 0) + 1

        # Chronological sorting is necessary for at-or-before date selection.
        idx.sort(key=lambda x: x[0])
        duplicate_dates = [d for d, n in date_counts.items() if n > 1]
        if duplicate_dates:
            feedback.pushWarning(
                f"[Stage 4 Step 3] Duplicate dates among {label} layers: "
                + ", ".join(str(d) for d in sorted(duplicate_dates))
                + ". The last layer at a duplicated date will be selected."
            )
        feedback.pushInfo(f"[Stage 4 Step 3] Indexed {len(idx):,} dated {label} layers.")
        return idx

    # Take the latest geometry at/before T1; never select a future observation.
    # The at-or-before rule supports irregular observation calendars without look-ahead.
    def _select_dated_geometry(self, idx, target_ymd):
        if not idx or target_ymd is None:
            return None, None
        # Use the most recent dated layer at or before interval start.
        # Never substitute a future layer, because that leaks later geometry.
        best = None
        for d, g, nm in idx:
            if d <= target_ymd:
                best = (d, g, nm)
            else:
                break
        if best is None:
            return None, None
        return best[1], best[0]

    # Normalise legacy source labels for controlled ontology matching.
    def _norm_text(self, v):
        if v is None:
            return ""
        s = str(v).strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s

    # Recognise EA and surface aliases that provide Active Domain evidence.
    # Classification is only a fallback for non-authoritative legacy labels.
    def _is_active_domain_class(self, v):
        s = self._norm_text(v)
        return s in {
            "active_domain", "active_surface", "active", "channel", "channel_surface",
            "active_channel", "water", "open_water", "stable_channel", "inchannel_surface",
            "erosion", "island_erosion", "cutbank", "scour", "eroded"
        }

    # Recognise source-class aliases for Depositional Storage.
    # NOTE: legacy stable_island/island aliases are listed as storage in this v6.7 helper.
    def _is_depositional_storage_class(self, v):
        s = self._norm_text(v)
        return s in {
            "depositional_storage", "storage", "active_storage",
            "deposition", "island_deposition", "migration_deposition",
            "infill_deposition", "channel_legacy_deposition",
            "bar", "sand", "sandbar", "braid_bar", "mid_channel_bar",
            "point_bar", "lateral_bar", "stable_island", "island", "inactive_island"
        }

    # Recognise explicitly stabilised or preserved floodplain classes.
    # Explicit STABILISED_FLOODPLAIN labels take precedence via _ontology_state.
    def _is_stabilised_floodplain_class(self, v):
        s = self._norm_text(v)
        return s in {
            "stabilised_floodplain", "stabilized_floodplain",
            "stable_floodplain", "inactive_floodplain",
            "persistent_floodplain", "floodplain", "vegetated_floodplain",
            "older_floodplain", "preserved_floodplain"
        }

    # Resolve three-state terminology, giving explicit state labels precedence.
    def _ontology_state(self, *values):
        """
        Map source state/class fields onto the revised ontology.

        Explicit ontology labels are honoured first. This is important because
        a row may contain both an explicit ONTO_STATE_T* value and older binary
        flags such as ACTIVE_T*=1 or A_C*=1. Older binary flags are only used as
        a fallback when no explicit ontology/state/class value is available.
        """
        vals = [v for v in values if v is not None and str(v).strip() != ""]
        if not vals:
            return "UNRESOLVED"

        # Where an explicit ontology class exists, do not let a legacy binary flag override it.
        # First pass: exact ontology labels or common aliases.
        for v in vals:
            s = self._norm_text(v)
            if s in {"active_domain", "active"}:
                return "ACTIVE_DOMAIN"
            if s in {"depositional_storage", "storage", "active_storage"}:
                return "DEPOSITIONAL_STORAGE"
            if s in {
                "stabilised_floodplain", "stabilized_floodplain",
                "stable_floodplain", "preserved_floodplain",
                "inactive_floodplain"
            }:
                return "STABILISED_FLOODPLAIN"

        # Second pass: process/surface classes.
        if any(self._is_active_domain_class(v) for v in vals):
            return "ACTIVE_DOMAIN"
        if any(self._is_depositional_storage_class(v) for v in vals):
            return "DEPOSITIONAL_STORAGE"
        if any(self._is_stabilised_floodplain_class(v) for v in vals):
            return "STABILISED_FLOODPLAIN"

        # Zero is only non-active occupancy, not proof of stabilised floodplain.
        # Numeric legacy occupancy can identify ACTIVE_DOMAIN when equal to 1.
        # A value of 0 only means non-active and cannot distinguish Depositional
        # Storage from Stabilised Floodplain, so it remains unresolved.
        for v in vals:
            try:
                x = int(float(v))
                if x == 1:
                    return "ACTIVE_DOMAIN"
            except Exception:
                pass

        return "UNRESOLVED"

    # Create a human-readable T1-to-T2 state transition label.
    def _ontology_transition(self, s1, s2):
        return f"{s1}_to_{s2}"

    # Retrieve raw E/D indicators for audit rather than overriding state-defined events.
    def _source_event_value(self, feat, names):
        """Return (value, found) for the first available binary source event field."""
        for name in names:
            if feat is None or feat.fields().indexFromName(name) < 0:
                continue
            raw = self._get(feat, name, None)
            if raw is None:
                continue
            return self._as_int(raw, 0), True
        return None, False

    # Derive strict transition events and their matching T1-specific risk sets.
    def _event_flags(self, s1, s2, feat=None, require_process_confirmation=False):
        """Derive transition events and risk sets only from the resolved T1/T2 states.

        Module 3 E_evt/D_evt and explicit event fields are retained as raw QA
        evidence but never suppress, create or otherwise alter a state-defined event.
        """
        # Every event requires a recognised, compatible T1->T2 pair.
        valid_states={"ACTIVE_DOMAIN","DEPOSITIONAL_STORAGE","STABILISED_FLOODPLAIN"}
        valid_pair=s1 in valid_states and s2 in valid_states
        reactivate=1 if s1=="STABILISED_FLOODPLAIN" and s2=="ACTIVE_DOMAIN" else 0
        storage=1 if s1=="ACTIVE_DOMAIN" and s2=="DEPOSITIONAL_STORAGE" else 0
        stabilise=1 if s1=="DEPOSITIONAL_STORAGE" and s2=="STABILISED_FLOODPLAIN" else 0
        storage_rework=1 if s1=="DEPOSITIONAL_STORAGE" and s2=="ACTIVE_DOMAIN" else 0
        fp_storage=1 if s1=="STABILISED_FLOODPLAIN" and s2=="DEPOSITIONAL_STORAGE" else 0
        # Read legacy E/D flags as evidence but never redefine three-state events from them.
        raw_e,raw_e_found=self._source_event_value(feat,["E_EVT_RAW","E_evt"])
        raw_d,raw_d_found=self._source_event_value(feat,["D_EVT_RAW","D_evt"])
        any_evt=1 if valid_pair and s1!=s2 else 0
        valid_start=1 if s1 in valid_states else 0
        return {
            "REACTIVATE_TRANS":reactivate,"STORAGE_TRANS":storage,"STABILISE_TRANS":stabilise,
            "STORAGE_REWORK_TRANS":storage_rework,"FP_STORAGE_TRANS":fp_storage,
            "REACTIVATE_EVT":reactivate,"STORAGE_EVT":storage,"STABILISE_EVT":stabilise,
            "STORAGE_REWORK_EVT":storage_rework,"FP_STORAGE_EVT":fp_storage,
            "ANY_STATE_EVT":any_evt,"ANY_ONTO_EVT":any_evt,
            "REACTIVATE_RISK_SET":1 if s1=="STABILISED_FLOODPLAIN" else 0,
            "STORAGE_RISK_SET":1 if s1=="ACTIVE_DOMAIN" else 0,
            "STABILISE_RISK_SET":1 if s1=="DEPOSITIONAL_STORAGE" else 0,
            "STORAGE_REWORK_RISK_SET":1 if s1=="DEPOSITIONAL_STORAGE" else 0,
            "FP_STORAGE_RISK_SET":1 if s1=="STABILISED_FLOODPLAIN" else 0,
            "ANY_STATE_RISK_SET":valid_start,"RISK_SET":valid_start,
            "E_EVT_RAW":raw_e if raw_e_found else None,"D_EVT_RAW":raw_d if raw_d_found else None,
            "E_CONFIRM_AVAILABLE":1 if raw_e_found else 0,"D_CONFIRM_AVAILABLE":1 if raw_d_found else 0,
        }

    # Preserve and reconcile Module 3 ambiguity-bridged primary event/risk fields.
    # Primary bridging supports boundary-mixed intervals while keeping strict fields intact.
    def _primary_event_flags(self, feat, strict_ev, observed_t1):
        """Read and independently validate Module 3B v4.3.2 primary fields.

        Primary events are authoritative Module 3B outputs because they can bridge
        one or more boundary-mixed endpoints. They cannot be reconstructed from the
        observed ONTO_STATE_T1/ONTO_STATE_T2 pair alone. Primary risk sets are
        checked against the observed or latent effective T1 state.
        """
        valid_states = {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}
        # Latent states are admitted only when documented boundary-mixed provenance supports them.
        latent_t1 = self._ontology_state(self._get(feat, "M3_LATENT_STATE_T1", None))
        source_t1 = str(self._get(feat, "M3_STATE_SOURCE_T1", "") or "").strip().upper()
        mixed_t1 = self._as_int(self._get(feat, "M3_MIXED_T1", 0), 0)
        boundary_mixed_t1 = (
            observed_t1 == "UNRESOLVED" and
            (source_t1 == "BOUNDARY_MIXED_ACTIVE_CONTACT" or mixed_t1 == 1) and
            latent_t1 in valid_states
        )
        effective_t1 = observed_t1 if observed_t1 in valid_states else (latent_t1 if boundary_mixed_t1 else "UNRESOLVED")

        bridged = {
            "REACTIVATE_BRIDGED": self._as_int(self._get(feat, "REACTIVATE_BRIDGED", 0), 0),
            "STORAGE_BRIDGED": self._as_int(self._get(feat, "STORAGE_BRIDGED", 0), 0),
            "STORAGE_REWORK_BRIDGED": self._as_int(self._get(feat, "STORAGE_REWORK_BRIDGED", 0), 0),
            "FP_STORAGE_BRIDGED": self._as_int(self._get(feat, "FP_STORAGE_BRIDGED", 0), 0),
        }
        # Independently reconstruct expected primary events as a hard consistency check.
        expected_events = {
            "REACTIVATE_EVT_PRIMARY": 1 if strict_ev["REACTIVATE_EVT"] or bridged["REACTIVATE_BRIDGED"] else 0,
            "STORAGE_EVT_PRIMARY": 1 if strict_ev["STORAGE_EVT"] or bridged["STORAGE_BRIDGED"] else 0,
            "STABILISE_EVT_PRIMARY": strict_ev["STABILISE_EVT"],
            "STORAGE_REWORK_EVT_PRIMARY": 1 if strict_ev["STORAGE_REWORK_EVT"] or bridged["STORAGE_REWORK_BRIDGED"] else 0,
            "FP_STORAGE_EVT_PRIMARY": 1 if strict_ev["FP_STORAGE_EVT"] or bridged["FP_STORAGE_BRIDGED"] else 0,
        }
        expected_events["ANY_STATE_EVT_PRIMARY"] = 1 if any(expected_events.values()) else 0
        # The effective T1 state determines the correct risk population for each transition.
        expected_risks = {
            "REACTIVATE_RISK_SET_PRIMARY": 1 if effective_t1 == "STABILISED_FLOODPLAIN" else 0,
            "STORAGE_RISK_SET_PRIMARY": 1 if effective_t1 == "ACTIVE_DOMAIN" else 0,
            "STABILISE_RISK_SET_PRIMARY": 1 if effective_t1 == "DEPOSITIONAL_STORAGE" else 0,
            "STORAGE_REWORK_RISK_SET_PRIMARY": 1 if effective_t1 == "DEPOSITIONAL_STORAGE" else 0,
            "FP_STORAGE_RISK_SET_PRIMARY": 1 if effective_t1 == "STABILISED_FLOODPLAIN" else 0,
            "ANY_STATE_RISK_SET_PRIMARY": 1 if effective_t1 in valid_states else 0,
        }

        # Read original Module 3 values; discrepancies are counted rather than silently repaired.
        source_events = {k: self._as_int(self._get(feat, k, 0), 0) for k in expected_events}
        source_risks = {k: self._as_int(self._get(feat, k, 0), 0) for k in expected_risks}
        event_definition_mismatch = sum(1 for k, v in expected_events.items() if source_events[k] != v)
        risk_definition_mismatch = sum(1 for k, v in expected_risks.items() if source_risks[k] != v)
        # An observed event outside its eligible risk set is an invalid model record.
        event_risk_mismatch = int(
            (source_events["REACTIVATE_EVT_PRIMARY"] and not source_risks["REACTIVATE_RISK_SET_PRIMARY"]) or
            (source_events["STORAGE_EVT_PRIMARY"] and not source_risks["STORAGE_RISK_SET_PRIMARY"]) or
            (source_events["STABILISE_EVT_PRIMARY"] and not source_risks["STABILISE_RISK_SET_PRIMARY"]) or
            (source_events["STORAGE_REWORK_EVT_PRIMARY"] and not source_risks["STORAGE_REWORK_RISK_SET_PRIMARY"]) or
            (source_events["FP_STORAGE_EVT_PRIMARY"] and not source_risks["FP_STORAGE_RISK_SET_PRIMARY"])
        )
        out = {}
        out.update(source_events)
        out.update(source_risks)
        out.update(bridged)
        out.update({
            "M3_EFFECTIVE_STATE_T1_PRIMARY": effective_t1,
            "PRIMARY_EVENT_DEFINITION_MISMATCH": event_definition_mismatch,
            "PRIMARY_RISK_DEFINITION_MISMATCH": risk_definition_mismatch,
            "PRIMARY_EVENT_RISK_MISMATCH": event_risk_mismatch,
        })
        return out

    # Keep a backwards-compatible no-op shim; raw events never create state transitions.
    def _merge_source_event_flags(self, feat, ev):
        """
        Compatibility shim retained for older calls.

        Source event fields are QA/confirmation evidence only. They are never
        allowed to create an event that is incompatible with the T1 -> T2 state
        transition or its transition-specific risk set.
        """
        return dict(ev)

    # Read only explicit authoritative Module 3 endpoint states.
    # This deliberately does not infer DS/SF from a binary non-active indicator.
    def _module3_state_from_feature(self, feat, prefix):
        """Read only explicit Module 3 three-state endpoint fields.

        Legacy binary occupancy and broad class aliases are intentionally excluded
        here. They cannot distinguish Depositional Storage from Stabilised
        Floodplain and therefore cannot define an authoritative endpoint state.
        """
        fields = (
            ["ONTO_STATE_T1", "STATE1_ONTOLOGY", "ONTOLOGY_STATE_T1", "DOMAIN_STATE_T1", "ONTO_STATE_1"]
            if str(prefix) == "1" else
            ["ONTO_STATE_T2", "STATE2_ONTOLOGY", "ONTOLOGY_STATE_T2", "DOMAIN_STATE_T2", "ONTO_STATE_2"]
        )
        for fld in fields:
            v = self._get(feat, fld, None)
            if v is None or str(v).strip() == "":
                continue
            state = self._ontology_state(v)
            if state in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}:
                return state
        return "UNRESOLVED"

    # Legacy flexible state resolver; prefer full ontology over binary occupancy.
    def _state_from_feature(self, feat, prefix):
        """
        prefix = '1' or '2'. Uses explicit ontology fields first, then
        process/surface/state/class fields, and only then legacy binary flags.

        This prevents old ACTIVE_T*/A_C*/P_C* fields from overriding the new
        three-state ontology.
        """
        if prefix == "1":
            explicit_fields = [
                "ONTO_STATE_T1", "STATE1_ONTOLOGY", "ONTOLOGY_STATE_T1",
                "DOMAIN_STATE_T1", "ONTO_STATE_1"
            ]
            class_fields = [
                "DOMAIN_T1", "SURFACE_T1", "STATE_T1", "C1", "state1",
                "CLASS_T1", "EA_T1", "EA_Class_T1"
            ]
            binary_fields = ["ACTIVE_T1", "P_C1", "A_C1"]
        else:
            explicit_fields = [
                "ONTO_STATE_T2", "STATE2_ONTOLOGY", "ONTOLOGY_STATE_T2",
                "DOMAIN_STATE_T2", "ONTO_STATE_2"
            ]
            class_fields = [
                "DOMAIN_T2", "SURFACE_T2", "STATE_T2", "C2", "state2",
                "CLASS_T2", "EA_T2", "EA_Class_T2"
            ]
            binary_fields = ["ACTIVE_T2", "P_C2", "A_C2"]

        # Compatibility fallback is subordinate to an authoritative recognised ontology field.
        # Explicit ontology fields are authoritative if recognised.
        for fld in explicit_fields:
            v = self._get(feat, fld, None)
            if v is not None and str(v).strip() != "":
                s = self._ontology_state(v)
                if s != "UNRESOLVED":
                    return s

        # Process/surface/state classes are next.
        class_vals = []
        for fld in class_fields:
            v = self._get(feat, fld, None)
            if v is not None and str(v).strip() != "":
                class_vals.append(v)
        if class_vals:
            s = self._ontology_state(*class_vals)
            if s != "UNRESOLVED":
                return s

        # Legacy binary flags can identify active occupation only. A zero value
        # cannot distinguish Depositional Storage from Stabilised Floodplain.
        for fld in binary_fields:
            v = self._get(feat, fld, None)
            if v is None or str(v).strip() == "":
                continue
            try:
                x = int(float(v))
                if x == 1:
                    return "ACTIVE_DOMAIN"
            except Exception:
                pass

        return "UNRESOLVED"

    # ------------------------------------------------------------
    # Assemblage-history covariates
    # ------------------------------------------------------------

    # Pair source assemblage state/class series with period-end dates.
    # Module 4a supplies an independent spatial-history record, not replacement endpoints.
    def _asm_class_pairs(self, asm_attrs):
        """
        Return ordered per-step assemblage state/class observations.

        Preference order:
          1. per-step ontology states from Module 4a/Step 2
          2. per-step EA classes
          3. older per-step domain/state aliases

        This allows Step 3 to use explicit DEPOSITIONAL_STORAGE histories when
        Module 4a supplies them, while remaining compatible with older
        EA_Class_i/Period_i-only assemblage lookup tables.
        """
        # Find supported 1-based timesteps without assuming a fixed chronology length.
        step_ids = set()
        patterns = [
            r"^ASM_ONTO_STATE_(\d+)$",
            r"^ASM_ONTOLOGY_STATE_(\d+)$",
            r"^ASM_STATE_(\d+)$",
            r"^ASM_DOMAIN_STATE_(\d+)$",
            r"^ASM_EA_Class_(\d+)$",
            r"^ASM_EA_(\d+)$",
            r"^ASM_CLASS_(\d+)$",
        ]

        for k in asm_attrs.keys():
            for pat in patterns:
                m = re.match(pat, k, re.IGNORECASE)
                if m:
                    step_ids.add(int(m.group(1)))
                    break

        # Use the resolved class and matching period from each available time step.
        pairs = []
        for i in sorted(step_ids):
            v = None
            for name in [
                f"ASM_ONTO_STATE_{i}",
                f"ASM_ONTOLOGY_STATE_{i}",
                f"ASM_STATE_{i}",
                f"ASM_DOMAIN_STATE_{i}",
                f"ASM_EA_Class_{i}",
                f"ASM_EA_{i}",
                f"ASM_CLASS_{i}",
            ]:
                if name in asm_attrs and asm_attrs.get(name) not in (None, ""):
                    v = asm_attrs.get(name)
                    break

            if v is None:
                continue

            period = None
            for pname in [
                f"ASM_Period_{i}",
                f"ASM_PERIOD_{i}",
                f"ASM_PeriodEnd_{i}",
                f"ASM_END_DATE_{i}",
                f"ASM_DATE_{i}",
            ]:
                if pname in asm_attrs and asm_attrs.get(pname) not in (None, ""):
                    period = asm_attrs.get(pname)
                    break

            ymd = self._period_end_from_text(period)
            pairs.append((i, ymd, v))

        # Sort by dated observation when present; indices break ties.
        pairs.sort(key=lambda x: (x[1] if x[1] is not None else 99999999, x[0]))
        return pairs



    # Evaluate independent assemblage history at a date for Module 3 agreement QA.
    def _asm_state_at_or_before(self, asm_attrs, target_ymd, step_fallback=None):
        """
        Return the latest recognised assemblage state available at target_ymd.

        Dated histories are preferred. If the lookup has no usable dates,
        step_fallback supplies a 1-based maximum step index. Future dated
        records are never used.
        """
        pairs = self._asm_class_pairs(asm_attrs or {})
        if not pairs:
            return None

        # Historical comparison must never inspect a later assemblage observation.
        has_dated = any(ymd is not None for _, ymd, _ in pairs)
        candidates = []

        if has_dated and target_ymd is not None:
            candidates = [
                (i, ymd, cls)
                for i, ymd, cls in pairs
                if ymd is not None and ymd <= target_ymd
                and cls is not None and str(cls).strip() != ""
            ]
            candidates.sort(key=lambda x: (x[1], x[0]))
        elif not has_dated and step_fallback is not None:
            candidates = [
                (i, ymd, cls)
                for i, ymd, cls in pairs
                if i <= step_fallback
                and cls is not None and str(cls).strip() != ""
            ]
            candidates.sort(key=lambda x: x[0])
        elif target_ymd is None:
            candidates = [
                (i, ymd, cls)
                for i, ymd, cls in pairs
                if cls is not None and str(cls).strip() != ""
            ]
            candidates.sort(key=lambda x: (x[1] if x[1] is not None else -1, x[0]))

        if not candidates:
            return None

        state = self._ontology_state(candidates[-1][2])
        return state if state != "UNRESOLVED" else None

    # Use Module 3, never Module 4a fallback, to define modelling endpoints.
    # A known Module 4a state never fills a missing Module 3 modelling state.
    def _state_for_interval(self, feat, asm_attrs, y1, y2, prefix, interval_seq=None):
        """Return only the authoritative Module 3 endpoint state.

        Module 4a remains an independent descriptive/history source and is retained
        in ASM_STATE_T*_QA plus disagreement fields. It must not silently replace an
        unresolved Module 3 modelling endpoint.
        """
        return self._module3_state_from_feature(feat, prefix)

    # Define the lagged assemblage-memory predictor output contract.
    # Names ending _PREV represent history attributed at interval start T1.
    def _asm_prev_field_names(self):
        return [
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
            "ASM_STATE_PREV",
            "ASM_CLASS_PREV",
            "ASM_DOM_RATIO_PREV",
            "ASM_NET_BAL_PREV",
            "ASM_STRUCTURE_CL_PREV",
            "ASM_DOMAIN_CLASS_PREV",
            "ASM_DEPO_INTERP_PREV",
            "ASM_ONTOLOGY_PREV"
        ]

    # Summarise assemblage history observed by the interval start, excluding later steps.
    def _asm_prev_metrics(self, asm_attrs, interval_start_ymd, interval_seq=None):
        pairs = self._asm_class_pairs(asm_attrs)
        if not pairs:
            return {k: None for k in self._asm_prev_field_names()}

        # The temporal cutoff is inclusive of T1 (known at the forecast origin).
        # Predictors for interval y1 -> y2 may use history available at y1,
        # but never the current interval outcome at y2.
        # Use real observation dates; only fall back to step order if none are usable.
        has_dated = any(ymd is not None for _, ymd, _ in pairs)
        usable = []
        if has_dated and interval_start_ymd is not None:
            usable = [
                (i, ymd, cls)
                for i, ymd, cls in pairs
                if ymd is not None and ymd <= interval_start_ymd
            ]
        elif not has_dated and interval_seq is not None:
            # Step fields are conventionally 1-based; a zero-based interval
            # sequence j has j completed prior steps at T1.
            usable = [
                (i, ymd, cls)
                for i, ymd, cls in pairs
                if i <= interval_seq
            ]
        elif interval_start_ymd is None:
            usable = []

        # An initial interval with no prior record is coded separately, not from final state.
        n_steps = len(usable)
        if n_steps == 0:
            out = {k: 0 for k in self._asm_prev_field_names()}
            out["ASM_STATE_PREV"] = "none_observed"
            out["ASM_CLASS_PREV"] = "none_observed"
            out["ASM_STRUCTURE_CL_PREV"] = "none"
            out["ASM_DOMAIN_CLASS_PREV"] = "none_observed"
            out["ASM_DEPO_INTERP_PREV"] = "none_observed"
            out["ASM_ONTOLOGY_PREV"] = "active_domain_storage_stabilisation_framework"
            return out

        # Lagged states are computed from the filtered history sequence only.
        states = [self._ontology_state(cls) for _, _, cls in usable]

        n_active = sum(1 for s in states if s == "ACTIVE_DOMAIN")
        n_storage = sum(1 for s in states if s == "DEPOSITIONAL_STORAGE")
        n_stab = sum(1 for s in states if s == "STABILISED_FLOODPLAIN")
        n_events = n_active + n_storage

        # Count transitions between preceding observations, not through the current T1->T2 outcome.
        transitions = list(zip(states[:-1], states[1:]))
        n_reactivate = sum(1 for a, b in transitions if a == "STABILISED_FLOODPLAIN" and b == "ACTIVE_DOMAIN")
        n_store_evt = sum(1 for a, b in transitions if a == "ACTIVE_DOMAIN" and b == "DEPOSITIONAL_STORAGE")
        n_stabilise = sum(1 for a, b in transitions if a == "DEPOSITIONAL_STORAGE" and b == "STABILISED_FLOODPLAIN")

        activeish = [1 if s in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"} else 0 for s in states]
        dist_freq = float(sum(activeish)) / float(max(1, n_steps))
        storage_frac = float(n_storage) / float(max(1, n_steps))
        stab_frac = float(n_stab) / float(max(1, n_steps))

        # Area fractions provide graded prior exposure instead of only dominant-state frequencies.
        # Prefer Step 2 PLACE-area fractions for lagged proportion predictors;
        # dominant-state counts remain available as separate predictors.
        active_fraction_values=[]; storage_fraction_values=[]; stab_fraction_values=[]
        for step, _ymd, _cls in usable:
            af=self._as_float(asm_attrs.get(f"ASM_ACTIVE_FRAC_{step}"),None)
            sf=self._as_float(asm_attrs.get(f"ASM_STORAGE_FRAC_{step}"),None)
            ff=self._as_float(asm_attrs.get(f"ASM_STAB_FP_FRAC_{step}"),None)
            if af is not None: active_fraction_values.append(af)
            if sf is not None: storage_fraction_values.append(sf)
            if ff is not None: stab_fraction_values.append(ff)
        if active_fraction_values or storage_fraction_values:
            active_mean=sum(active_fraction_values)/len(active_fraction_values) if active_fraction_values else 0.0
            storage_frac=sum(storage_fraction_values)/len(storage_fraction_values) if storage_fraction_values else 0.0
            dist_freq=active_mean+storage_frac
        if stab_fraction_values:
            stab_frac=sum(stab_fraction_values)/len(stab_fraction_values)

        # Recency is measured in observation STEPS in this helper, not elapsed calendar years.
        last_active = -1
        for j, a in enumerate(activeish):
            if a == 1:
                last_active = j + 1
        quiet_since = n_steps if last_active < 0 else n_steps - last_active

        # A run of active/storage observations defines one descriptive activity episode.
        n_episodes = 0
        in_ep = False
        ep_len = 0
        max_ep_len = 0
        quiet_run = 0
        max_quiet = 0
        for a in activeish:
            if a == 1:
                if not in_ep:
                    n_episodes += 1
                    in_ep = True
                ep_len += 1
                max_ep_len = max(max_ep_len, ep_len)
                quiet_run = 0
            else:
                in_ep = False
                ep_len = 0
                quiet_run += 1
                max_quiet = max(max_quiet, quiet_run)

        if sum(activeish) == 0:
            structure = "stable"
        elif n_episodes == 1 and max_ep_len <= 1:
            structure = "single_activity"
        elif max_quiet <= max(1, int(0.20 * n_steps)):
            structure = "continuous"
        elif n_episodes <= 3:
            structure = "episodic"
        else:
            structure = "intermittent"

        # Assign dominant organisational condition from the lagged history counts.
        if n_active > n_storage and n_active > n_stab:
            domain_class = "active_domain_dominated"
        elif n_storage > n_active and n_storage > n_stab:
            domain_class = "depositional_storage_dominated"
        elif n_stab > n_active and n_stab > n_storage:
            domain_class = "stabilised_floodplain_dominated"
        elif n_active == 0 and n_storage == 0 and n_stab == 0:
            domain_class = "unresolved_domain"
        else:
            domain_class = "mixed_ontology_states"

        if n_storage > 0 and n_stab == 0:
            depo_interp = "deposition_as_active_domain_storage"
        elif n_storage > 0 and n_stab > 0:
            depo_interp = "storage_with_later_stabilisation_context"
        elif n_stab > 0:
            depo_interp = "stabilised_floodplain_without_recent_storage"
        else:
            depo_interp = "no_storage_recorded"

        dom_ratio = 0.0
        if (n_active + n_storage + n_stab) > 0:
            vals = [n_active, n_storage, n_stab]
            dom_ratio = float(max(vals)) / float(sum(vals))

        # The signed net balance is descriptive; it does not measure sediment volume.
        # Positive means net movement toward stabilised storage/floodplain preservation;
        # negative means net movement toward active-domain occupation.
        net_bal = (n_storage + n_stab) - n_active

        current_state = states[-1]
        asm_class = f"{structure}_{domain_class}"

        return {
            "ASM_N_EVENTS_PREV": n_events,
            "ASM_N_ACTIVE_DOMAIN_PREV": n_active,
            "ASM_N_STORAGE_PREV": n_storage,
            "ASM_N_STAB_FP_PREV": n_stab,
            "ASM_N_REACTIVATE_PREV": n_reactivate,
            "ASM_N_STORAGE_EVT_PREV": n_store_evt,
            "ASM_N_STABILISE_PREV": n_stabilise,
            "ASM_DIST_FREQ_PREV": dist_freq,
            "ASM_STORAGE_FRAC_PREV": storage_frac,
            "ASM_STAB_FP_FRAC_PREV": stab_frac,
            "ASM_LAST_ACTIVE_STEP_PREV": last_active,
            "ASM_QUIET_SINCE_PREV": quiet_since,
            "ASM_N_EPISODES_PREV": n_episodes,
            "ASM_MAX_QUIET_PREV": max_quiet,
            "ASM_STATE_PREV": current_state,
            "ASM_CLASS_PREV": asm_class,
            "ASM_DOM_RATIO_PREV": dom_ratio,
            "ASM_NET_BAL_PREV": net_bal,
            "ASM_STRUCTURE_CL_PREV": structure,
            "ASM_DOMAIN_CLASS_PREV": domain_class,
            "ASM_DEPO_INTERP_PREV": depo_interp,
            "ASM_ONTOLOGY_PREV": "active_domain_storage_stabilisation_framework"
        }

    # Separate static ASM fields from explicit timestep-history columns.
    # IMPORTANT: retained whole-record static ASM descriptors may leak future outcomes if used as predictors.
    def _asm_static_fields(self, asm_lookup_layer):
        """
        Return only genuinely static ASM predictors.

        Per-step state, process, period and event histories must not be copied to
        every risk-table row because they contain future information relative to
        early intervals. Those histories are used internally to derive *_PREV
        fields and current T1/T2 states.
        """
        # Exclude fields with explicit _i suffixes; remaining static fields are copied unchanged.
        names = asm_lookup_layer.fields().names()
        history_pat = re.compile(
            r"^ASM_(?:"
            r"EA_CLASS|EA|CLASS|PERIOD|PERIODEND|END_DATE|DATE|"
            r"ONTO_STATE|ONTOLOGY_STATE|STATE|DOMAIN_STATE|"
            r"ONTO_TRANS|ONTOLOGY_TRANS|DOMAIN_TRANS|"
            r"ACT|ACTIVE|ACTIVE_DOM|STORAGE|STAB_FP|STABILISED_FP|"
            r"ACTIVE_FRAC|STORAGE_FRAC|STAB_FP_FRAC|UNRESOLVED_FRAC|"
            r"STATE_SUM_FRAC|STATE_MAX_FRAC|STATE_MIXED|"
            r"REACTIVATE_EVT|STORAGE_EVT|STABILISE_EVT"
            r")_\d+$",
            re.IGNORECASE,
        )
        # Downstream model formulas must select eligible antecedent covariates explicitly.
        return [
            n for n in names
            if n.startswith("ASM_") and not history_pat.match(n)
        ]

    # Support both prefixed and unprefixed aliases in a static lookup.
    def _asm_get_any(self, asm_attrs, *names):
        """Return the first non-empty value from ASM lookup attributes."""
        if not asm_attrs:
            return None
        for n in names:
            if n in asm_attrs:
                v = asm_attrs.get(n)
                if v is not None and str(v).strip() != "":
                    return v
        return None

    # ------------------------------------------------------------
    # Distance / curvature covariates
    # ------------------------------------------------------------

    # Measure distance and inside/outside status of a fixed-place representative point.
    # Zero denotes contact/inside the source domain; NULL denotes unavailable geometry.
    def _distance_covariates(self, place_geom, source_geom):
        if place_geom is None or place_geom.isEmpty() or source_geom is None or source_geom.isEmpty():
            return None, None
        try:
            inside = 1 if source_geom.contains(place_geom) or source_geom.intersects(place_geom) else 0
        except Exception:
            inside = 0
        try:
            dist = float(place_geom.distance(source_geom))
        except Exception:
            dist = None
        if inside:
            dist = 0.0
        return dist, inside

    # Approximate signed local bend curvature from three centreline points.
    # Signed curvature reflects the source centreline orientation.
    def _line_measure_and_curvature(self, point_geom, line_geom, half_window, width):
        """
        Lightweight curvature approximation for Meandering/Anabranching river covariates.

        It works on the closest segment of the combined centreline geometry and
        estimates signed curvature using three interpolation positions:
        m-half_window, m, m+half_window.  If geometry is multipart or unsuitable,
        returns NULL curvature but still lets distance covariates be written.
        """
        if point_geom is None or point_geom.isEmpty() or line_geom is None or line_geom.isEmpty():
            return None, None, None

        try:
            dist = float(point_geom.distance(line_geom))
        except Exception:
            dist = None

        try:
            m = line_geom.lineLocatePoint(point_geom)
            length = line_geom.length()
            if m is None or length <= 0:
                return dist, None, None

            # The three sampling positions are clipped to the line ends.
            m0 = max(0.0, m - half_window)
            m1 = m
            m2 = min(length, m + half_window)
            if m2 <= m0:
                return dist, None, None

            p0 = line_geom.interpolate(m0).asPoint()
            p1 = line_geom.interpolate(m1).asPoint()
            p2 = line_geom.interpolate(m2).asPoint()

            ax, ay = p0.x(), p0.y()
            bx, by = p1.x(), p1.y()
            cx, cy = p2.x(), p2.y()

            ab = math.hypot(bx - ax, by - ay)
            bc = math.hypot(cx - bx, cy - by)
            ac = math.hypot(cx - ax, cy - ay)
            if ab <= 0 or bc <= 0 or ac <= 0:
                return dist, m, None

            # Signed three-point curvature is scaled by a representative width when nonzero.
            cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            area2 = cross
            k = 2.0 * area2 / (ab * bc * ac)
            k_scaled = k * width if width and width > 0 else k
            return dist, m, k_scaled
        except Exception:
            return dist, None, None

    # ------------------------------------------------------------
    # Output fields
    # ------------------------------------------------------------

    # Build the non-spatial risk-table schema and retain source-specific QA fields.
    # Schema consolidates source history, independent QA, eligibility flags and spatial exposures.
    def _build_output_fields(self, place_long, place_geom, asm_lookup):
        fields = QgsFields()

        # Module 3 interval fields are row-specific and copied at original types.
        for n in self.BASE_FIELDS:
            if self._field_exists(place_long, n):
                self._append_unique(fields, self._copy_field(place_long, n))

        for n in self.STATIC_PLACE_FIELDS:
            if self._field_exists(place_geom, n):
                self._append_unique(fields, self._copy_field(place_geom, n))

        # Some cohort fields may be present only in the static lookup or KM_blocks.
        # Preserve initial-floodplain cohort fields.  Prefer PLACE_long field
        # definitions when present, but also accept fields passed through the
        # Stage 4 Step 2 ASM lookup, because v4 of Step 2 can carry 3b cohort attributes.
        for n in self.INITIAL_COHORT_FIELDS:
            if self._field_exists(place_long, n):
                self._append_unique(fields, self._copy_field(place_long, n))
            elif self._field_exists(asm_lookup, n):
                self._append_unique(fields, self._copy_field(asm_lookup, n))
            elif self._field_exists(place_geom, n):
                self._append_unique(fields, self._copy_field(place_geom, n))

        # Static whole-period descriptors are retained for QA, NOT automatically safe predictors.
        for n in self._asm_static_fields(asm_lookup):
            idx = asm_lookup.fields().indexFromName(n)
            if idx >= 0:
                f = asm_lookup.fields()[idx]
                self._append_unique(fields, QgsField(n, f.type(), f.typeName(), f.length(), f.precision()))

        # Lagged assemblage fields have string, integer or double types as appropriate.
        for n in self._asm_prev_field_names():
            if n.endswith("_PREV") and any(tok in n for tok in ["STATE", "CLASS", "STRUCTURE", "DOMAIN", "DEPO", "ONTOLOGY"]):
                self._append_unique(fields, QgsField(n, QVariant.String))
            elif n in {"ASM_STATE_PREV", "ASM_CLASS_PREV", "ASM_STRUCTURE_CL_PREV", "ASM_DOMAIN_CLASS_PREV", "ASM_DEPO_INTERP_PREV", "ASM_ONTOLOGY_PREV"}:
                self._append_unique(fields, QgsField(n, QVariant.String))
            elif any(tok in n for tok in ["FREQ", "FRAC", "RATIO"]):
                self._append_unique(fields, QgsField(n, QVariant.Double))
            else:
                self._append_unique(fields, QgsField(n, QVariant.Int))

        # Explicit strict, primary and broad-FP transition fields coexist in the same table.
        ontology_fields = [
            ("ONTO_STATE_T1", QVariant.String),
            ("ONTO_STATE_T2", QVariant.String),
            ("ONTO_TRANS", QVariant.String),
            ("ONTOLOGY_TRANS", QVariant.String),
            ("DOMAIN_TRANS_ONTO", QVariant.String),
            ("STATE1_ONTOLOGY", QVariant.String),
            ("STATE2_ONTOLOGY", QVariant.String),
            ("M3_STATE_T1", QVariant.String),
            ("M3_STATE_T2", QVariant.String),
            ("ASM_STATE_T1_QA", QVariant.String),
            ("ASM_STATE_T2_QA", QVariant.String),
            ("STATE_SOURCE_T1", QVariant.String),
            ("STATE_SOURCE_T2", QVariant.String),
            ("M3_ASM_DISAGREE_T1", QVariant.Int),
            ("M3_ASM_DISAGREE_T2", QVariant.Int),
            ("M3_ASM_DISAGREE_ANY", QVariant.Int),
            ("M3_MODEL_ELIGIBLE_STRICT", QVariant.Int),
            ("M3_MODEL_EXCLUSION_REASON", QVariant.String),
            ("M3_EFFECTIVE_STATE_T1_PRIMARY", QVariant.String),
            ("M3_EFFECTIVE_STATE_T2_PRIMARY", QVariant.String),
            ("M3_MODEL_ELIGIBLE_PRIMARY", QVariant.Int),
            ("M3_MODEL_EXCLUSION_REASON_PRIMARY", QVariant.String),
            ("PRIMARY_EVENT_DEFINITION_MISMATCH", QVariant.Int),
            ("PRIMARY_RISK_DEFINITION_MISMATCH", QVariant.Int),
            ("PRIMARY_EVENT_RISK_MISMATCH", QVariant.Int),
            ("EVENT_TYPE_ONTO", QVariant.String),
            ("EVENT_TYPE_PRIMARY", QVariant.String),
            ("STATE_TRANS", QVariant.String),
            ("EVENT_TYPE_STATE", QVariant.String),
            ("ACTIVE_DOMAIN_T1", QVariant.Int),
            ("ACTIVE_DOMAIN_T2", QVariant.Int),
            ("STORAGE_T1", QVariant.Int),
            ("STORAGE_T2", QVariant.Int),
            ("STAB_FP_T1", QVariant.Int),
            ("STAB_FP_T2", QVariant.Int),
            ("REACTIVATE_TRANS", QVariant.Int),
            ("STORAGE_TRANS", QVariant.Int),
            ("STABILISE_TRANS", QVariant.Int),
            ("STORAGE_REWORK_TRANS", QVariant.Int),
            ("FP_STORAGE_TRANS", QVariant.Int),
            ("REACTIVATE_EVT", QVariant.Int),
            ("STORAGE_EVT", QVariant.Int),
            ("STABILISE_EVT", QVariant.Int),
            ("STORAGE_REWORK_EVT", QVariant.Int),
            ("FP_STORAGE_EVT", QVariant.Int),
            ("ANY_STATE_EVT", QVariant.Int),
            ("ANY_ONTO_EVT", QVariant.Int),
            ("REACTIVATE_RISK_SET", QVariant.Int),
            # FP_REACTIVATE admits pre-existing eligible FP plus SF and explicitly excludes DS.
            # v6.7 broadened floodplain-reactivation prediction fields. These deliberately
            # coexist with, rather than redefine, strict REACTIVATE_* fields.
            ("PREEXISTING_FP_START", QVariant.Int),
            ("PREEXISTING_FP_START_PRIMARY", QVariant.Int),
            ("PREEXISTING_FP_SUPPORT_OK", QVariant.Int),
            ("PREEXISTING_FP_DISTURBED_PREV", QVariant.Int),
            ("FP_REACTIVATE_SOURCE", QVariant.String),
            ("FP_REACTIVATE_SOURCE_PRIMARY", QVariant.String),
            ("FP_REACTIVATE_RISK_SET", QVariant.Int),
            ("FP_REACTIVATE_EVT", QVariant.Int),
            ("FP_REACTIVATE_MODEL_ELIGIBLE", QVariant.Int),
            ("FP_REACTIVATE_EXCLUSION_REASON", QVariant.String),
            ("FP_REACTIVATE_RISK_SET_PRIMARY", QVariant.Int),
            ("FP_REACTIVATE_EVT_PRIMARY", QVariant.Int),
            ("FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY", QVariant.Int),
            ("FP_REACTIVATE_EXCLUSION_REASON_PRIMARY", QVariant.String),
            ("STORAGE_RISK_SET", QVariant.Int),
            ("STABILISE_RISK_SET", QVariant.Int),
            ("STORAGE_REWORK_RISK_SET", QVariant.Int),
            ("FP_STORAGE_RISK_SET", QVariant.Int),
            ("ANY_STATE_RISK_SET", QVariant.Int),
            ("RISK_SET", QVariant.Int),
            ("E_RISK_SET", QVariant.Int),
            ("D_RISK_SET", QVariant.Int),
            ("E_EVT_RAW", QVariant.Int),
            ("D_EVT_RAW", QVariant.Int),
            ("E_CONFIRM_AVAILABLE", QVariant.Int),
            ("D_CONFIRM_AVAILABLE", QVariant.Int),
            # First-reactivation risk is tracked separately from recurrent SF and broad FP risk sets.
            ("INIT_FP_COHORT", QVariant.Int),
            ("BASE_REACTIVATE_RISK_SET", QVariant.Int),
            ("BASE_REACTIVATE_RISK_SET_DERIVED", QVariant.Int),
            ("BASE_REACTIVATE_EVT", QVariant.Int),
            ("BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED", QVariant.Int),
            ("BASE_REACTIVATE_EVT_PRIMARY", QVariant.Int),
            ("VALID_NEXT", QVariant.Int),
            ("STATE_MODEL_VERSION", QVariant.String),
            ("ONTOLOGY_VERSION", QVariant.String),
            ("DIST_EVENT_ONTO", QVariant.String),
            ("DEPO_INTERP_ONTO", QVariant.String),
            # Revised Module 4a persistence-promotion fields. These are
            # carried for mapping/interpretation; the KM/AG event engine still
            # uses the three core ontology states.
            ("FINAL_ONTO_RAW", QVariant.String),
            ("FP_CONDITION", QVariant.String),
            ("FP_STAB", QVariant.Double),
            ("FP_RECENT", QVariant.Double),
            ("FP_REWORKED", QVariant.Double),
            ("SURFACE_AGE_EST", QVariant.Double)
        ]

        # These target fields describe FOLLOWING-interval outcomes; exclude them from predictor matrices.
        next_fields = [
            ("ONTO_STATE_NEXT", QVariant.String),
            ("ONTO_TRANS_NEXT", QVariant.String),
            ("REACTIVATE_NEXT", QVariant.Int),
            ("STORAGE_NEXT", QVariant.Int),
            ("STABILISE_NEXT", QVariant.Int),
            ("STORAGE_REWORK_NEXT", QVariant.Int),
            ("FP_STORAGE_NEXT", QVariant.Int),
            ("ANY_STATE_NEXT", QVariant.Int),
            ("ANY_ONTO_NEXT", QVariant.Int),
            ("REACTIVATE_NEXT_PRIMARY", QVariant.Int),
            ("STORAGE_NEXT_PRIMARY", QVariant.Int),
            ("STABILISE_NEXT_PRIMARY", QVariant.Int),
            ("STORAGE_REWORK_NEXT_PRIMARY", QVariant.Int),
            ("FP_STORAGE_NEXT_PRIMARY", QVariant.Int),
            ("ANY_STATE_NEXT_PRIMARY", QVariant.Int)
        ]

        # Time-varying and exact T1 spatial covariates are separate from response labels.
        cov_fields = [
            ("DIST_ACTIVE_CURR", QVariant.Double),
            ("INSIDE_ACTIVE_CURR", QVariant.Int),
            ("DIST_ACTIVE_BIN", QVariant.String),
            ("DIST_ACTIVE_CURR_BIN", QVariant.String),
            ("DIST_WATER_CURR", QVariant.Double),
            ("INSIDE_WATER_CURR", QVariant.Int),
            ("DIST_WATER_BIN", QVariant.String),
            ("DIST_WATER_CURR_BIN", QVariant.String),
            ("DIST_CL_CURR", QVariant.Double),
            ("DIST_CL_CURR_BIN", QVariant.String),
            ("CL_MEASURE_CURR", QVariant.Double),
            ("CURV_CL_CURR", QVariant.Double),
            ("CURV_EROSION_CURR", QVariant.Double),
            ("DIST_X_CURV_EROSION", QVariant.Double),

            # The suffix _PREV refers to geometries observed at interval start.
            # Explicit lagged timestep-channel geometry from Stage 4 Step 2 v6.2.
            ("GEOM_YMD_PREV", QVariant.Int),
            ("GEOM_YEAR_PREV", QVariant.Int),
            ("DIST_CHANNEL_PREV", QVariant.Double),
            ("DIST_BANK_PREV", QVariant.Double),
            ("BANK_SETBACK_PREV", QVariant.Double),
            ("INSIDE_CHANNEL_PREV", QVariant.Int),
            ("DIST_CL_PREV", QVariant.Double),
            ("DIST_CL_PREV_BIN", QVariant.String),
            ("CL_MEASURE_PREV", QVariant.Double),
            ("CURV_SIGNED_PREV", QVariant.Double),
            ("CURV_ABS_PREV", QVariant.Double),
            ("CURV_SCALED_PREV", QVariant.Double),
            ("POINT_SIDE_PREV", QVariant.String),
            ("BANK_SIDE_PREV", QVariant.String),
            ("OUTER_BANK_PREV", QVariant.Int),
            ("INNER_BANK_PREV", QVariant.Int),
            ("LOCAL_HALF_WIDTH_PREV", QVariant.Double),
            ("LOCAL_WIDTH_PREV", QVariant.Double),
            ("REL_CHANNEL_POS_PREV", QVariant.Double),
            ("NEAR_CHANNEL_HALF_PREV", QVariant.Int),
            ("NEAR_CHANNEL_FULL_PREV", QVariant.Int),
            ("NEAR_BANK_HALF_PREV", QVariant.Int),
            ("NEAR_BANK_FULL_PREV", QVariant.Int),
            ("OUTER_CURV_REACT_HALF_PREV", QVariant.Double),
            ("OUTER_CURV_REACT_FULL_PREV", QVariant.Double),
            ("INNER_CURV_STORAGE_HALF_PREV", QVariant.Double),
            ("INNER_CURV_STORAGE_FULL_PREV", QVariant.Double),
            ("OUTER_CURV_STORAGE_HALF_PREV", QVariant.Double),
            ("OUTER_CURV_STORAGE_FULL_PREV", QVariant.Double),
            ("GEOM_SEG_ID_PREV", QVariant.String),
            ("GEOM_SUPPORT_PREV", QVariant.Int)
        ]

        for n, t in ontology_fields + next_fields + cov_fields:
            self._append_unique(fields, QgsField(n, t))

        return fields

    # Encode continuous distances into the existing publication-style distance bins.
    # Distance thresholds remain the unchanged original 250m/500m/1km/2km/5km bins.
    def _bin_distance(self, d):
        if d is None:
            return None
        try:
            d = float(d)
        except Exception:
            return None
        if d < 250:
            return "0-250 m"
        if d < 500:
            return "250-500 m"
        if d < 1000:
            return "0.5-1 km"
        if d < 2000:
            return "1-2 km"
        if d < 5000:
            return "2-5 km"
        return ">5 km"

    # Fail before heavy processing if the required three-state Module 3 schema is absent.
    # This is a strict schema/version preflight, not a state-inference fallback.
    def _require_explicit_module3_state_fields(self, layer):
        names = set(layer.fields().names())
        t1 = {"ONTO_STATE_T1", "STATE1_ONTOLOGY", "ONTOLOGY_STATE_T1", "DOMAIN_STATE_T1", "ONTO_STATE_1"}
        t2 = {"ONTO_STATE_T2", "STATE2_ONTOLOGY", "ONTOLOGY_STATE_T2", "DOMAIN_STATE_T2", "ONTO_STATE_2"}
        if not names.intersection(t1) or not names.intersection(t2):
            raise QgsProcessingException(
                "PLACE_interval_long must retain explicit Module 3 three-state endpoint fields "
                "for both T1 and T2 (prefer ONTO_STATE_T1 and ONTO_STATE_T2). Binary ACTIVE/A_C/P_C "
                "fields are not sufficient because they cannot distinguish Depositional Storage "
                "from Stabilised Floodplain. Revise/rerun the Module 3 PLACE preparation pass-through."
            )
        # The model needs source provenance, storage clocks, boundary ambiguity and QA fields.
        required_semantic = {
            "M3_ACTIVE_FRAC_T1", "M3_ACTIVE_FRAC_T2",
            "M3_STORAGE_FRAC_T1", "M3_STORAGE_FRAC_T2",
            "M3_STAB_FP_FRAC_T1", "M3_STAB_FP_FRAC_T2",
            "M3_UNRESOLVED_FRAC_T1", "M3_UNRESOLVED_FRAC_T2",
            "M3_STATE_SUM_T1", "M3_STATE_SUM_T2",
            "M3_BACKGROUND_FRAC", "M3_STABLE_EVID_FRAC",
            "M3_STATE_SUPPORT_T1", "M3_STATE_SUPPORT_T2", "M3_STATE_CONF_T1", "M3_STATE_CONF_T2",
            "M3_MIXED_T1", "M3_MIXED_T2", "STORAGE_AGE_YR_T1", "STORAGE_AGE_YR_T2",
            "STORAGE_START_YMD_T1", "STORAGE_START_YMD_T2", "STORAGE_CLOCK_RESET_T2",
            "STORAGE_REWORK_EVT", "STORAGE_REWORK_RISK_SET", "FP_STORAGE_EVT", "FP_STORAGE_RISK_SET",
            "REACTIVATE_CONFIRMED", "STORAGE_CONFIRMED", "STABILISE_CONFIRMED",
            "STORAGE_REWORK_CONFIRMED", "FP_STORAGE_CONFIRMED",
            "M3_ACTIVE_STATE_THR", "M3_ACTIVE_CONTACT_THR", "M3_MIXED_FRAC_THR",
            "M3_BG_STATE_THR", "M3_STABILISE_YEARS", "M3_STABILISE_MODE", "M3_STABLE_EVID_THR",
            "QA_STATE_SOURCE_INCONSISTENT", "QA_STATE_FRACTION_SUM",
            "M3_LATENT_STATE_T1", "M3_LATENT_STATE_T2",
            "M3_AMBIGUITY_RUN_ID", "M3_AMBIGUITY_RUN_LENGTH",
            "M3_AMBIGUITY_START_YMD", "M3_AMBIGUITY_RESOLVED", "M3_BRIDGED_TRANS",
            "REACTIVATE_EVT_PRIMARY", "STORAGE_EVT_PRIMARY", "STABILISE_EVT_PRIMARY",
            "STORAGE_REWORK_EVT_PRIMARY", "FP_STORAGE_EVT_PRIMARY", "ANY_STATE_EVT_PRIMARY",
            "REACTIVATE_BRIDGED", "STORAGE_BRIDGED", "STORAGE_REWORK_BRIDGED", "FP_STORAGE_BRIDGED",
            "REACTIVATE_RISK_SET_PRIMARY", "STORAGE_RISK_SET_PRIMARY",
            "STABILISE_RISK_SET_PRIMARY", "STORAGE_REWORK_RISK_SET_PRIMARY",
            "FP_STORAGE_RISK_SET_PRIMARY", "ANY_STATE_RISK_SET_PRIMARY",
            "BASE_REACTIVATE_RISK_SET_PRIMARY",
            "REACTIVATE_CONFIRMED_PRIMARY", "STORAGE_CONFIRMED_PRIMARY",
            "STABILISE_CONFIRMED_PRIMARY", "STORAGE_REWORK_CONFIRMED_PRIMARY",
            "FP_STORAGE_CONFIRMED_PRIMARY",
            "QA_LATENT_STATE_INCONSISTENT", "QA_BRIDGED_TRANS_INVALID",
            "M3_ANOMALY_COUNT", "M3_ANOMALY_SEVERITY", "M3_ANOMALY_FLAGS"
        }
        # Raise a visible error before a costly full-reach risk-table construction.
        missing = sorted(required_semantic - names)
        if missing:
            raise QgsProcessingException(
                "PLACE_interval_long is not the revised Module 3B semantic-state output. Missing fields: "
                + ", ".join(missing)
                + ". Run Module 3B v4.3.2 and Module 3C v4.6.1 before Step 3."
            )

    # ------------------------------------------------------------
    # Main
    # ------------------------------------------------------------

    # Coordinate validation, joins, eligibility, lagged covariates, output and final QA.
    def processAlgorithm(self, parameters, context, feedback):
        # Read separate interval, fixed-place, static-ASM and optional dated-geometry sources.
        place_long = self.parameterAsVectorLayer(parameters, self.PLACE_LONG, context)
        place_geom_layer = self.parameterAsVectorLayer(parameters, self.PLACE_GEOM, context)
        asm_lookup_layer = self.parameterAsVectorLayer(parameters, self.ASM_LOOKUP, context)
        timestep_geom_layer = self.parameterAsVectorLayer(parameters, self.TIMESTEP_GEOM_LOOKUP, context)

        require_union_domain_fields = self.parameterAsBool(
            parameters, self.REQUIRE_UNION_DOMAIN_FIELDS, context
        )

        # First enforce input validity and authoritative Module 3 schema.
        if place_long is None or not place_long.isValid():
            raise QgsProcessingException("PLACE_interval_long table is invalid.")
        self._require_explicit_module3_state_fields(place_long)
        feedback.pushInfo("[Stage 4 Step 3] Explicit Module 3 T1/T2 state fields verified in PLACE_interval_long.")
        if place_long.wkbType() != QgsWkbTypes.NoGeometry:
            feedback.pushWarning(
                "[Stage 4 Step 3] PLACE_interval_long contains geometry. The geometry is ignored; "
                "use the authoritative non-spatial table where available and supply KM_blocks separately."
            )
        if place_geom_layer is None or not place_geom_layer.isValid():
            raise QgsProcessingException("KM_blocks / fixed PLACE geometry layer is invalid.")
        if asm_lookup_layer is None or not asm_lookup_layer.isValid():
            raise QgsProcessingException("Stage 4 Step 2 static covariate lookup is invalid.")

        # Retrospective union-domain fields are used as static comparison weights.
        asm_lookup_names = set(asm_lookup_layer.fields().names())
        union_missing = [n for n in self.UNION_DOMAIN_FIELDS if n not in asm_lookup_names]
        if require_union_domain_fields and union_missing:
            raise QgsProcessingException(
                "The Stage 4 Step 2 lookup is missing required union-domain fields: "
                + ", ".join(union_missing)
                + ". Run Stage 4 Step 2 v6.4 with the dissolved union-channel polygon."
            )
        if not union_missing:
            feedback.pushInfo(
                "[Stage 4 Step 3] Union-domain fields detected and scheduled for static pass-through: "
                + ", ".join(self.UNION_DOMAIN_FIELDS)
            )
        elif not require_union_domain_fields:
            feedback.pushWarning(
                "[Stage 4 Step 3] Union-domain fields are incomplete and will not support the R full-versus-union comparison: "
                + ", ".join(union_missing)
            )

        # Each row must have a start and stop observation date.
        has_start = self._field_exists(place_long, "y1") or self._field_exists(place_long, "tstart_yr")
        has_stop = self._field_exists(place_long, "y2") or self._field_exists(place_long, "tstop_yr")
        if not (has_start and has_stop):
            raise QgsProcessingException(
                "PLACE_interval_long must contain y1/y2 or tstart_yr/tstop_yr. "
                "Do not use the static PLACE grid as PLACE_LONG."
            )

        calc_active = self.parameterAsBool(parameters, self.CALC_ACTIVE, context)
        calc_water = self.parameterAsBool(parameters, self.CALC_WATER, context)
        calc_centreline = self.parameterAsBool(parameters, self.CALC_CENTRELINE, context)
        calc_curvature = self.parameterAsBool(parameters, self.CALC_CURVATURE, context)
        include_next = self.parameterAsBool(parameters, self.INCLUDE_NEXT, context)
        require_process_confirmation = self.parameterAsBool(
            parameters, self.REQUIRE_PROCESS_CONFIRMATION, context
        )
        # v6.7 deliberately ignores legacy process-confirmation filtering; preserve warning.
        if require_process_confirmation:
            feedback.pushWarning(
                "[Stage 4 Step 3 v6.6] Process-confirmation filtering is deprecated and ignored. "
                "Module 3 T1/T2 states alone define transition events and risk sets; E_evt/D_evt remain QA evidence."
            )
        require_process_confirmation = False
        centreline_mode = self.parameterAsEnum(parameters, self.CENTRELINE_MODE, context)
        half_window = self.parameterAsDouble(parameters, self.CURV_WINDOW, context)
        width = self.parameterAsDouble(parameters, self.CHANNEL_WIDTH, context)

        # Read dated sources only for predictor families enabled by the user.
        active_layers = self.parameterAsLayerList(parameters, self.ACTIVE_LAYERS, context) or []
        water_layers = self.parameterAsLayerList(parameters, self.WATER_LAYERS, context) or []
        centreline_layers = self.parameterAsLayerList(parameters, self.CENTRELINES, context) or []
        reference_centreline = self.parameterAsVectorLayer(parameters, self.REFERENCE_CENTRELINE, context)

        # Curvature cannot be evaluated without a chosen centreline geometry.
        if calc_curvature and not calc_centreline:
            feedback.pushWarning(
                "[Stage 4 Step 3] Curvature was requested but centreline covariates are disabled; "
                "curvature calculation has been disabled."
            )
            calc_curvature = False

        # Enforce enabled-layer requirements before building heavy merged geometry.
        if calc_active and not active_layers:
            raise QgsProcessingException(
                "Active-domain covariates are enabled but no dated active-domain layers were supplied."
            )
        if calc_water and not water_layers:
            raise QgsProcessingException(
                "Water covariates are enabled but no dated water layers were supplied."
            )
        if calc_centreline and centreline_mode == 0 and not centreline_layers:
            raise QgsProcessingException(
                "Dated centreline mode is selected but no dated centreline layers were supplied."
            )

        # A common CRS is essential for comparable source-map-unit distances.
        target_crs = place_geom_layer.crs()
        for label, layers_to_check in [
            ("active-domain", active_layers if calc_active else []),
            ("water", water_layers if calc_water else []),
            ("centreline", centreline_layers if calc_centreline and centreline_mode == 0 else []),
        ]:
            for lyr in layers_to_check:
                if lyr.crs() != target_crs:
                    raise QgsProcessingException(
                        f"CRS mismatch: {label} layer '{lyr.name()}' does not match the PLACE geometry CRS."
                    )

        # Fixed geometry and static ASM lookups are keyed once, then reused per interval.
        feedback.pushInfo("[Stage 4 Step 3] Building PLACE geometry lookup...")
        place_geom_lookup, place_geom_key = self._build_place_geom_lookup(place_geom_layer, feedback)
        feedback.pushInfo("[Stage 4 Step 3] Building ASM lookup...")
        asm_lookup, asm_key = self._build_table_lookup(asm_lookup_layer, feedback, "ASM lookup")

        # Per-place area-balance checks detect invalid union weights before output.
        # Validate the static nested-domain weights once, before interval rows are written.
        union_qa = {
            "rows": 0, "missing": 0, "fraction_range": 0,
            "area_balance": 0, "fraction_mismatch": 0, "flag_mismatch": 0,
            "sum_block_area": 0.0, "sum_union_area": 0.0, "sum_outside_area": 0.0,
        }
        # Calculate both area identity and classification-flag consistency.
        if not union_missing:
            for pid, attrs in asm_lookup.items():
                union_qa["rows"] += 1
                block_area = self._as_float(attrs.get("ASM_BLOCK_AREA_M2"), None)
                overlap = self._as_float(attrs.get("ASM_UNION_OVERLAP_M2"), None)
                frac = self._as_float(attrs.get("ASM_UNION_FRAC"), None)
                outside = self._as_float(attrs.get("ASM_OUTSIDE_UNION_M2"), None)
                contact = self._as_int(attrs.get("ASM_UNION_CONTACT"), None)
                boundary = self._as_int(attrs.get("ASM_UNION_BOUNDARY"), None)
                core50 = self._as_int(attrs.get("ASM_UNION_CORE50"), None)
                # Partial union-domain records are invalid under the default strict requirement.
                if None in (block_area, overlap, frac, outside, contact, boundary, core50):
                    union_qa["missing"] += 1
                    continue
                union_qa["sum_block_area"] += block_area
                union_qa["sum_union_area"] += overlap
                union_qa["sum_outside_area"] += outside
                # Use small magnitude-dependent tolerances for geometry precision differences.
                tolerance = max(1.0e-6, abs(block_area) * 1.0e-9)
                if block_area <= 0 or overlap < -tolerance or outside < -tolerance or frac < -1.0e-9 or frac > 1.0 + 1.0e-9:
                    union_qa["fraction_range"] += 1
                if abs((overlap + outside) - block_area) > tolerance:
                    union_qa["area_balance"] += 1
                expected_frac = overlap / block_area if block_area > 0 else None
                if expected_frac is None or abs(frac - expected_frac) > 1.0e-8:
                    union_qa["fraction_mismatch"] += 1
                # Contact, partial boundary overlap and core50 flags must match geometric fractions.
                expected_contact = 1 if overlap > tolerance else 0
                expected_boundary = 1 if overlap > tolerance and outside > tolerance else 0
                expected_core50 = 1 if frac >= 0.5 else 0
                if contact != expected_contact or boundary != expected_boundary or core50 != expected_core50:
                    union_qa["flag_mismatch"] += 1

            feedback.pushInfo(
                "[Stage 4 Step 3] Union-domain lookup QA | "
                f"rows={union_qa['rows']:,}; missing={union_qa['missing']:,}; "
                f"range={union_qa['fraction_range']:,}; balance={union_qa['area_balance']:,}; "
                f"fraction mismatch={union_qa['fraction_mismatch']:,}; flag mismatch={union_qa['flag_mismatch']:,}; "
                f"full/union/outside area={union_qa['sum_block_area']:,.3f}/"
                f"{union_qa['sum_union_area']:,.3f}/{union_qa['sum_outside_area']:,.3f} m²."
            )
            # Do not silently use inconsistent retrospective area weights.
            union_failures = (
                union_qa["missing"] + union_qa["fraction_range"] +
                union_qa["area_balance"] + union_qa["fraction_mismatch"] +
                union_qa["flag_mismatch"]
            )
            if require_union_domain_fields and union_failures:
                raise QgsProcessingException(
                    "Union-domain lookup QA failed. Correct the Step 2 union overlap output before building the Risk Table."
                )

        # Index exact dated channel geometry; absence is allowed only when lookup is omitted.
        timestep_geom_lookup = self._build_timestep_geom_lookup(
            timestep_geom_layer, feedback
        ) if timestep_geom_layer is not None else {"exact": {}, "fields": []}

        # Dated active/water/centreline geometries are combined once per timestamp.
        feedback.pushInfo("[Stage 4 Step 3] Indexing spatial covariate layers...")
        active_idx = self._index_dated_layers(active_layers, feedback, "active-domain") if calc_active else []
        water_idx = self._index_dated_layers(water_layers, feedback, "water") if calc_water else []
        cl_idx = self._index_dated_layers(centreline_layers, feedback, "centreline") if calc_centreline and centreline_mode == 0 else []
        if calc_active and not active_idx:
            raise QgsProcessingException("No usable dated active-domain layers could be indexed.")
        if calc_water and not water_idx:
            raise QgsProcessingException("No usable dated water layers could be indexed.")
        if calc_centreline and centreline_mode == 0 and not cl_idx:
            raise QgsProcessingException("No usable dated centreline layers could be indexed.")
        feedback.pushInfo("[Stage 4 Step 3] Spatial covariate indexing complete.")

        # A shared centreline is intentionally not date-varying; treat as retrospective if applicable.
        reference_cl_geom = None
        if calc_centreline and centreline_mode == 1:
            if reference_centreline is None:
                raise QgsProcessingException("Single reference centreline mode selected but no reference centreline was provided.")
            if reference_centreline.crs() != place_geom_layer.crs():
                raise QgsProcessingException(
                    "CRS mismatch: reference centreline does not match the PLACE geometry CRS."
                )
            reference_cl_geom = self._combine_layer_geometry(reference_centreline, feedback, "reference centreline")
            if reference_cl_geom is None or reference_cl_geom.isEmpty():
                raise QgsProcessingException("Reference centreline has no usable geometry.")

        # Create a no-geometry sink even though underlying fixed-place inputs are polygons.
        out_fields = self._build_output_fields(place_long, place_geom_layer, asm_lookup_layer)
        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            QgsWkbTypes.NoGeometry,
            place_long.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException("Could not create output sink.")

        # Use the same stable key across the three source representations.
        key = self._best_key_field(place_long)
        if key is None:
            raise QgsProcessingException("PLACE_interval_long must contain PLACE_ID or BLOCK_ID.")

        # Load interval records, ensuring a unique place+start+stop primary key.
        rows = []
        interval_keys = set()
        interval_ids = set()
        missing_interval_ids = 0
        missing_interval_dates = 0
        duplicate_intervals = 0
        for feat in place_long.getFeatures():
            pid = self._get(feat, key)
            if pid is None or str(pid).strip() == "":
                missing_interval_ids += 1
                continue
            # Convert legacy year fields to the canonical YYYYMMDD comparison key.
            y1 = self._to_ymd(self._get(feat, "y1", self._get(feat, "tstart_yr", None)))
            y2 = self._to_ymd(self._get(feat, "y2", self._get(feat, "tstop_yr", None)))
            if y1 is None or y2 is None:
                missing_interval_dates += 1
                continue
            skey = str(pid)
            # Repeated intervals for the same PLACE are rejected, not averaged or overwritten.
            composite = (skey, y1, y2)
            if composite in interval_keys:
                duplicate_intervals += 1
                continue
            interval_keys.add(composite)
            interval_ids.add(skey)
            rows.append((skey, y1, y2, feat))

        # Every interval PLACE must match both fixed geometry and static covariates.
        missing_geom_ids = sorted(interval_ids.difference(place_geom_lookup.keys()))
        missing_asm_ids = sorted(interval_ids.difference(asm_lookup.keys()))
        extra_geom_ids = len(set(place_geom_lookup.keys()).difference(interval_ids))
        extra_asm_ids = len(set(asm_lookup.keys()).difference(interval_ids))
        feedback.pushInfo(
            f"[Stage 4 Step 3] Interval-table preflight | key={key}; "
            f"rows accepted={len(rows):,}; PLACE IDs={len(interval_ids):,}; "
            f"missing IDs={missing_interval_ids:,}; missing dates={missing_interval_dates:,}; "
            f"duplicate BLOCK_ID+T1+T2 rows={duplicate_intervals:,}; "
            f"interval IDs without KM_blocks geometry={len(missing_geom_ids):,}; "
            f"interval IDs without static covariates={len(missing_asm_ids):,}; "
            f"extra KM_blocks/static lookup IDs={extra_geom_ids:,}/{extra_asm_ids:,}."
        )
        # A missing join is a fatal data-model mismatch; no null filled fallback.
        if (missing_interval_ids or missing_interval_dates or duplicate_intervals or
                missing_geom_ids or missing_asm_ids):
            geom_sample = ", ".join(missing_geom_ids[:10])
            asm_sample = ", ".join(missing_asm_ids[:10])
            details = []
            if geom_sample:
                details.append(f"missing geometry IDs: {geom_sample}")
            if asm_sample:
                details.append(f"missing static-covariate IDs: {asm_sample}")
            detail = " Samples — " + "; ".join(details) + "." if details else ""
            raise QgsProcessingException(
                "PLACE_interval_long failed Stage 4 composite-key/lookup QA. Required key: "
                "one unique BLOCK_ID/PLACE_ID + interval-start + interval-stop row, with "
                "matching KM_blocks geometry and Stage 4 Step 2 static covariates." + detail
            )
        if not rows:
            raise QgsProcessingException("PLACE_interval_long contains no usable interval rows.")
        if extra_geom_ids or extra_asm_ids:
            feedback.pushWarning(
                f"[Stage 4 Step 3] Extra IDs with no interval rows | "
                f"KM_blocks={extra_geom_ids:,}; static covariates={extra_asm_ids:,}. "
                "These records cannot enter the Risk Table."
            )

        # Sort by PLACE and observation start to make first-event closure deterministic.
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        feedback.pushInfo(f"[Stage 4 Step 3] Processing {len(rows):,} PLACE intervals.")

        # The subsequent-interval target is computed separately and has future information.
        # Build a zero-based interval sequence for undated history fallback.
        # Precompute next-interval targets only when requested.
        next_by_row = {}
        seq_by_row = {}
        by_place = {}
        # Group all observed intervals by their fixed-place ID.
        for idx, (pid, y1, y2, f) in enumerate(rows):
            by_place.setdefault(pid, []).append((idx, y1, y2, f))

        for pid, rr in by_place.items():
            rr.sort(key=lambda x: (x[1] or 0, x[2] or 0))
            for j, (idx, y1, y2, f) in enumerate(rr):
                seq_by_row[idx] = j
                if not include_next:
                    continue
                # NEXT fields are read from the next interval; keep out of training covariates.
                if j + 1 < len(rr):
                    nidx, ny1, ny2, nf = rr[j + 1]
                    n_asm_attrs = asm_lookup.get(pid, {})
                    ns1 = self._state_for_interval(
                        nf, n_asm_attrs, ny1, ny2, "1", interval_seq=j + 1
                    )
                    ns2 = self._state_for_interval(
                        nf, n_asm_attrs, ny1, ny2, "2", interval_seq=j + 1
                    )
                    nev = self._event_flags(
                        ns1, ns2, nf, require_process_confirmation
                    )
                    npev = self._primary_event_flags(nf, nev, ns1)
                    next_by_row[idx] = (
                        ns2,
                        self._ontology_transition(ns1, ns2),
                        nev,
                        npev,
                    )
                else:
                    next_by_row[idx] = (None, None, None, None)

        # Counters below provide transition-specific and provenance-specific run QA.
        total = max(1, len(rows))
        qa = {
            "rows": 0,
            "missing_place_geom": 0,
            "missing_asm_lookup": 0,
            "unresolved_t1": 0,
            "unresolved_t2": 0,
            "reactivate_risk": 0,
            "reactivate_evt": 0,
            "storage_risk": 0,
            "storage_evt": 0,
            "stabilise_risk": 0,
            "stabilise_evt": 0,
            "storage_rework_risk": 0,
            "storage_rework_evt": 0,
            "fp_storage_risk": 0,
            "fp_storage_evt": 0,
            "m3_fatal_anomaly_rows": 0,
            "m3_warning_anomaly_rows": 0,
            "m3_strict_ineligible_rows": 0,
            "m3_primary_ineligible_rows": 0,
            "any_state_evt": 0,
            "any_state_evt_primary": 0,
            "event_risk_mismatch": 0,
            "primary_event_risk_mismatch": 0,
            "primary_event_definition_mismatch": 0,
            "primary_risk_definition_mismatch": 0,
            "reactivate_risk_primary": 0,
            "storage_risk_primary": 0,
            "stabilise_risk_primary": 0,
            "storage_rework_risk_primary": 0,
            "fp_storage_risk_primary": 0,
            "any_state_risk_primary": 0,
            "reactivate_evt_primary": 0,
            "fp_reactivate_risk": 0,
            "fp_reactivate_evt": 0,
            "fp_reactivate_risk_primary": 0,
            "fp_reactivate_evt_primary": 0,
            "preexisting_fp_start": 0,
            "preexisting_fp_start_primary": 0,
            "fp_reactivate_model_ineligible": 0,
            "fp_reactivate_model_ineligible_primary": 0,
            "fp_reactivate_event_risk_mismatch": 0,
            "fp_reactivate_event_risk_mismatch_primary": 0,
            "storage_evt_primary": 0,
            "stabilise_evt_primary": 0,
            "storage_rework_evt_primary": 0,
            "fp_storage_evt_primary": 0,
            "reactivate_bridged": 0,
            "storage_bridged": 0,
            "storage_rework_bridged": 0,
            "fp_storage_bridged": 0,
            "missing_active_date": 0,
            "missing_water_date": 0,
            "missing_centreline_date": 0,
            "missing_timestep_geometry": 0,
            "base_first_evt": 0,
            "base_first_evt_primary": 0,
            "m3_asm_disagree_t1": 0,
            "m3_asm_disagree_t2": 0,
            "m3_asm_disagree_any": 0,
            "m4a_fallback_t1": 0,
            "m4a_fallback_t2": 0,
        }
        # Keep independent per-place first-event histories for strict and primary cohorts.
        base_event_seen = {}
        base_event_seen_primary = {}
        # v6.7 dynamic guard for inherited/pre-existing floodplain. Once a PLACE has
        # shown active-domain/storage occupation or a raw E/D process event, it can no
        # longer be treated as undisturbed initial floodplain in later intervals.
        # Track previously recognised AD/DS occupation for dynamic inherited-FP eligibility.
        prior_disturbance_seen = {}
        # Each iteration writes one non-spatial PLACE interval row.
        for row_idx, (pid, y1, y2, f) in enumerate(rows):
            if feedback.isCanceled():
                break

            if row_idx % 10000 == 0:
                feedback.setProgress(int(100.0 * row_idx / total))

            # Join the static geometry and assemblage descriptors, never a polygon interval copy.
            place_rec = place_geom_lookup.get(pid, {})
            place_geom = place_rec.get("geom", None)
            place_attrs = place_rec.get("attrs", {})
            asm_attrs = asm_lookup.get(pid, {})

            qa["rows"] += 1
            if not place_rec:
                qa["missing_place_geom"] += 1
            if not asm_attrs:
                qa["missing_asm_lookup"] += 1

            # Observation-step index is a fallback only if real assemblage dates are unavailable.
            interval_seq = seq_by_row.get(row_idx, None)

            # Independent Module 4a disagreement flags are diagnostic; Module 3 defines risk.
            # Module 3 is authoritative. Module 4a is retained only as independent QA/history;
            # unresolved Module 3 endpoints remain unresolved for modelling.
            m3_s1 = self._module3_state_from_feature(f, "1")
            m3_s2 = self._module3_state_from_feature(f, "2")
            asm_s1 = self._asm_state_at_or_before(
                asm_attrs, y1, step_fallback=interval_seq if interval_seq is not None else None
            ) or "UNRESOLVED"
            asm_s2 = self._asm_state_at_or_before(
                asm_attrs, y2, step_fallback=(interval_seq + 1) if interval_seq is not None else None
            ) or "UNRESOLVED"
            s1 = self._state_for_interval(f, asm_attrs, y1, y2, "1", interval_seq=interval_seq)
            s2 = self._state_for_interval(f, asm_attrs, y1, y2, "2", interval_seq=interval_seq)
            valid_states={"ACTIVE_DOMAIN","DEPOSITIONAL_STORAGE","STABILISED_FLOODPLAIN"}
            source_t1="MODULE3" if m3_s1 in valid_states else "UNRESOLVED_MODULE3"
            source_t2="MODULE3" if m3_s2 in valid_states else "UNRESOLVED_MODULE3"
            # Flag disagreements only where BOTH sources provide recognised states.
            disagree_t1=1 if m3_s1 in valid_states and asm_s1 in valid_states and m3_s1!=asm_s1 else 0
            disagree_t2=1 if m3_s2 in valid_states and asm_s2 in valid_states and m3_s2!=asm_s2 else 0
            disagree_any=1 if disagree_t1 or disagree_t2 else 0

            # Strict modelling requires two resolved, non-mixed endpoints and valid Module 3 QA.
            strict_exclusion = []
            if s1 not in valid_states or s2 not in valid_states:
                strict_exclusion.append("UNRESOLVED_OR_INVALID_ENDPOINT")
            # Boundary-mixed endpoints are excluded from strict but may enter primary analysis.
            if self._as_int(self._get(f, "M3_MIXED_T1", 0), 0) == 1 or self._as_int(self._get(f, "M3_MIXED_T2", 0), 0) == 1:
                strict_exclusion.append("MIXED_ENDPOINT")
            if str(self._get(f, "M3_ANOMALY_SEVERITY", "NONE") or "NONE").upper() == "FATAL":
                strict_exclusion.append("FATAL_MODULE3_ANOMALY")
            if self._as_int(self._get(f, "M3_STATE_CHAIN_OK", 0), 0) != 1:
                strict_exclusion.append("STATE_CHAIN_FAILURE")
            if self._as_int(self._get(f, "QA_STATE_FRACTION_SUM", 0), 0) != 0:
                strict_exclusion.append("STATE_FRACTION_SUM_FAILURE")
            if self._as_int(self._get(f, "QA_CLOCK_INCONSISTENT", 0), 0) != 0:
                strict_exclusion.append("STORAGE_CLOCK_INCONSISTENT")
            if self._as_int(self._get(f, "QA_STATE_SOURCE_INCONSISTENT", 0), 0) != 0:
                strict_exclusion.append("STATE_SOURCE_INCONSISTENT")
            strict_exclusion = list(dict.fromkeys(strict_exclusion))
            strict_eligible = 1 if not strict_exclusion else 0

            # Derive strict state transitions separately from bridged Module 3 primary events.
            trans = self._ontology_transition(s1, s2)
            ev = self._event_flags(
                s1, s2, f, require_process_confirmation
            )
            pev = self._primary_event_flags(f, ev, s1)

            # Primary eligibility permits source-supported latent endpoints but enforces QA checks.
            primary_exclusion = []
            effective_t1 = pev["M3_EFFECTIVE_STATE_T1_PRIMARY"]
            source_t2_raw = str(self._get(f, "M3_STATE_SOURCE_T2", "") or "").strip().upper()
            # Only supported boundary ambiguity may justify a latent T2 endpoint.
            t2_boundary_mixed = (
                s2 == "UNRESOLVED" and
                (source_t2_raw == "BOUNDARY_MIXED_ACTIVE_CONTACT" or
                 self._as_int(self._get(f, "M3_MIXED_T2", 0), 0) == 1)
            )
            latent_t2 = self._ontology_state(self._get(f, "M3_LATENT_STATE_T2", None))
            # Leave unsupported T2 as unresolved; do not manufacture a destination state.
            effective_t2_primary = (
                s2 if s2 in valid_states
                else (latent_t2 if t2_boundary_mixed and latent_t2 in valid_states else "UNRESOLVED")
            )
            # Primary event models still require a recognised or supported latent starting state.
            if effective_t1 not in valid_states:
                primary_exclusion.append("NO_RECOGNISED_OR_LATENT_T1_STATE")
            if s2 not in valid_states and not t2_boundary_mixed:
                primary_exclusion.append("PROVENANCE_LIMITED_OR_INVALID_T2")
            if str(self._get(f, "M3_ANOMALY_SEVERITY", "NONE") or "NONE").upper() == "FATAL":
                primary_exclusion.append("FATAL_MODULE3_ANOMALY")
            if self._as_int(self._get(f, "M3_STATE_CHAIN_OK", 0), 0) != 1:
                primary_exclusion.append("STATE_CHAIN_FAILURE")
            if self._as_int(self._get(f, "QA_STATE_FRACTION_SUM", 0), 0) != 0:
                primary_exclusion.append("STATE_FRACTION_SUM_FAILURE")
            if self._as_int(self._get(f, "QA_CLOCK_INCONSISTENT", 0), 0) != 0:
                primary_exclusion.append("STORAGE_CLOCK_INCONSISTENT")
            if self._as_int(self._get(f, "QA_STATE_SOURCE_INCONSISTENT", 0), 0) != 0:
                primary_exclusion.append("STATE_SOURCE_INCONSISTENT")
            if self._as_int(self._get(f, "QA_LATENT_STATE_INCONSISTENT", 0), 0) != 0:
                primary_exclusion.append("LATENT_STATE_INCONSISTENT")
            if self._as_int(self._get(f, "QA_BRIDGED_TRANS_INVALID", 0), 0) != 0:
                primary_exclusion.append("INVALID_BRIDGED_TRANSITION")
            # A disagreement between Module 3 primary fields and recomputed definitions excludes the row.
            if pev["PRIMARY_EVENT_DEFINITION_MISMATCH"]:
                primary_exclusion.append("PRIMARY_EVENT_DEFINITION_MISMATCH")
            if pev["PRIMARY_RISK_DEFINITION_MISMATCH"]:
                primary_exclusion.append("PRIMARY_RISK_DEFINITION_MISMATCH")
            if pev["PRIMARY_EVENT_RISK_MISMATCH"]:
                primary_exclusion.append("PRIMARY_EVENT_OUTSIDE_RISK_SET")
            primary_exclusion = list(dict.fromkeys(primary_exclusion))
            primary_eligible = 1 if not primary_exclusion else 0

            # These ASM_PREV variables are recomputed at each interval start T1.
            # No-leakage histories are cut off at interval start (y1).
            asm_prev = self._asm_prev_metrics(
                asm_attrs, y1, interval_seq=interval_seq
            )

            # An absent GEOM_YMD is reported as missing; it never falls forward to T2.
            # Exact lagged channel geometry: predictors for (y1, y2] use the
            # PLACE x GEOM_YMD row at y1. No future-date fallback is allowed.
            ts_geom = self._select_timestep_geom_attrs(
                timestep_geom_lookup, pid, y1
            )
            if timestep_geom_layer is not None and ts_geom is None:
                qa["missing_timestep_geometry"] += 1

            # Spatial exposure is frozen at T1 for the interval (T1,T2].
            # Spatial covariates: current interval uses y1/current exposure.
            active_dist = active_inside = None
            if calc_active:
                # Select the newest active geometry <= T1, not the end-of-interval footprint.
                active_geom, _ = self._select_dated_geometry(active_idx, y1)
                if active_geom is None:
                    qa["missing_active_date"] += 1
                active_dist, active_inside = self._distance_covariates(place_geom, active_geom)

            water_dist = water_inside = None
            if calc_water:
                # Independent water-layer covariates are optional and time-lagged.
                water_geom, _ = self._select_dated_geometry(water_idx, y1)
                if water_geom is None:
                    qa["missing_water_date"] += 1
                water_dist, water_inside = self._distance_covariates(place_geom, water_geom)

            cl_dist = cl_measure = curv = curv_erosion = dist_x_curv = None
            # The reference option uses one line; dated mode selects the newest line at/before T1.
            if calc_centreline:
                if centreline_mode == 1:
                    cl_geom = reference_cl_geom
                else:
                    cl_geom, _ = self._select_dated_geometry(cl_idx, y1)
                    if cl_geom is None:
                        qa["missing_centreline_date"] += 1

                if calc_curvature:
                    cl_dist, cl_measure, curv = self._line_measure_and_curvature(place_geom, cl_geom, half_window, width)
                else:
                    cl_dist, _inside = self._distance_covariates(place_geom, cl_geom)

                curv_erosion = curv
                if cl_dist is not None and curv_erosion is not None:
                    dist_x_curv = (float(cl_dist) / 1000.0) * float(curv_erosion)

            # Assemble all fields into a single row, preserving NULL for unsupported optional data.
            out_feat = QgsFeature(out_fields)
            attrs = {n: None for n in out_fields.names()}

            # Keep Module 3 original state/provenance fields alongside model-derived fields.
            # Copy base long-table fields.
            for n in self.BASE_FIELDS:
                if out_fields.indexFromName(n) >= 0:
                    attrs[n] = self._get(f, n, None)

            # Copy static place attributes.
            for n in self.STATIC_PLACE_FIELDS:
                if out_fields.indexFromName(n) >= 0:
                    attrs[n] = place_attrs.get(n, None)

            # Cohort source precedence is Module 3 interval > ASM lookup > KM_blocks.
            # Copy / recover initial-floodplain cohort fields.  Priority:
            # PLACE_interval_long -> Step 2 lookup -> PLACE geometry.
            for n in self.INITIAL_COHORT_FIELDS:
                if out_fields.indexFromName(n) >= 0:
                    v = self._get(f, n, None)
                    if v is None:
                        v = asm_attrs.get(n, None)
                    if v is None:
                        v = place_attrs.get(n, None)
                    attrs[n] = v

            # FULL-RECORD static ASM fields are descriptive; downstream models must avoid leakage.
            # Copy static ASM fields.
            for n in self._asm_static_fields(asm_lookup_layer):
                if out_fields.indexFromName(n) >= 0:
                    attrs[n] = asm_attrs.get(n, None)

            for n, v in asm_prev.items():
                if out_fields.indexFromName(n) >= 0:
                    attrs[n] = v

            # INIT_FP denotes a baseline first-event cohort, NOT the broad recurrent eligible FP set.
            # Initial-floodplain first-event cohort.
            # Unlike the recurrent REACTIVATE_RISK_SET, this baseline risk set
            # is permanently closed after the first qualifying reactivation.
            base_risk_raw = attrs.get("BASE_RISK", None)
            init_fp_raw = attrs.get("INIT_FP", None)
            base_risk = self._as_int(base_risk_raw, None)
            if base_risk is None:
                base_risk = self._as_int(init_fp_raw, 0)
            init_fp_cohort = 1 if base_risk == 1 else 0

            # The v6.7 broad FP prediction population is an additional model domain, not a state.
            # ------------------------------------------------------------
            # v6.7 broadened floodplain -> Active Domain prediction population
            # ------------------------------------------------------------
            # PREEXISTING_FP_START is deliberately conservative. It is only used to
            # recover initial/baseline floodplain that Module 3 cannot assign to one of
            # the three observed process states. It is NOT allowed to override a
            # recognised Active Domain or Depositional Storage source state.
            #
            # The criterion is dynamic: INIT_FP/BASE_RISK identifies the baseline cohort,
            # while prior activity/storage history and sequential process evidence close
            # the pre-existing status once the PLACE has been geomorphically disturbed.
            # Previous AD/DS history must disqualify inherited pre-existing floodplain status.
            hist_active = self._as_int(asm_prev.get("ASM_N_ACTIVE_DOMAIN_PREV", 0), 0)
            hist_storage = self._as_int(asm_prev.get("ASM_N_STORAGE_PREV", 0), 0)
            disturbed_prev = bool(
                prior_disturbance_seen.get(pid, False)
                or hist_active > 0
                or hist_storage > 0
            )

            # Check evidence that the inherited floodplain is non-active at T1.
            active_frac_t1 = self._as_float(self._get(f, "M3_ACTIVE_FRAC_T1", None), None)
            storage_frac_t1 = self._as_float(self._get(f, "M3_STORAGE_FRAC_T1", None), None)
            c1_raw = self._as_int(self._get(f, "C1", None), None)
            # BASE_RISK/INIT_FP already identifies the inherited floodplain cohort.
            # For the broadened model we therefore require non-active interval-start
            # occupancy, but we do NOT close eligibility merely because a channel edge
            # has begun to overlap a small fraction of the PLACE. Doing so would recreate
            # the white fringe immediately ahead of a migrating bank. If C1 is unavailable,
            # fall back to the Module 3 active-state threshold rather than a hard-coded
            # fractional tolerance.
            active_state_thr = self._as_float(self._get(f, "M3_ACTIVE_STATE_THR", None), None)
            # Prefer the original binary C1 support criterion; threshold is fallback only.
            if c1_raw is not None:
                preexisting_support_ok = 1 if c1_raw == 0 else 0
            elif active_frac_t1 is not None and active_state_thr is not None:
                preexisting_support_ok = 1 if active_frac_t1 < active_state_thr else 0
            else:
                preexisting_support_ok = 0

            # Only initially eligible, previously undisturbed, unresolved T1 places enter this branch.
            preexisting_fp_start = 1 if (
                init_fp_cohort == 1
                and not disturbed_prev
                and s1 == "UNRESOLVED"
                and preexisting_support_ok == 1
            ) else 0
            # Primary broad-FP eligibility uses the effective (observed/latent) T1 status.
            preexisting_fp_start_primary = 1 if (
                init_fp_cohort == 1
                and not disturbed_prev
                and effective_t1 == "UNRESOLVED"
                and preexisting_support_ok == 1
            ) else 0

            # Strict broad FP risk = strict SF risk OR eligible inherited pre-existing FP.
            fp_reactivate_risk = 1 if (
                ev["REACTIVATE_RISK_SET"] == 1 or preexisting_fp_start == 1
            ) else 0
            # Strict broad FP occurrence requires a transition to observed Active Domain at T2.
            fp_reactivate_evt = 1 if (
                fp_reactivate_risk == 1 and s2 == "ACTIVE_DOMAIN"
            ) else 0

            # Primary broad FP risk includes primary SF risk plus eligible inherited FP.
            fp_reactivate_risk_primary = 1 if (
                pev["REACTIVATE_RISK_SET_PRIMARY"] == 1
                or preexisting_fp_start_primary == 1
            ) else 0
            # Primary broad FP outcomes admit compatible bridged transitions/latent T2.
            fp_reactivate_evt_primary = 1 if (
                fp_reactivate_risk_primary == 1
                and (
                    pev["REACTIVATE_EVT_PRIMARY"] == 1
                    or (preexisting_fp_start_primary == 1 and effective_t2_primary == "ACTIVE_DOMAIN")
                )
            ) else 0

            # Source labels distinguish established SF from initial pre-existing floodplain.
            fp_reactivate_source = (
                "STABILISED_FLOODPLAIN" if ev["REACTIVATE_RISK_SET"] == 1
                else ("PREEXISTING_FLOODPLAIN" if preexisting_fp_start == 1 else "NOT_AT_RISK")
            )
            fp_reactivate_source_primary = (
                "STABILISED_FLOODPLAIN" if pev["REACTIVATE_RISK_SET_PRIMARY"] == 1
                else ("PREEXISTING_FLOODPLAIN" if preexisting_fp_start_primary == 1 else "NOT_AT_RISK")
            )

            # Unlike generic eligibility, broad FP can legitimately start unresolved at T1.
            # Separate model-eligibility flags are essential. The generic Module 3
            # eligibility flag rejects an unresolved T1 state by design, whereas the
            # broadened model explicitly admits a tightly guarded pre-existing T1.
            # Remove only the generic unresolved-start exclusion, retaining other fatal QA checks.
            fp_reactivate_exclusion = [
                x for x in strict_exclusion if x != "UNRESOLVED_OR_INVALID_ENDPOINT"
            ]
            if s1 not in valid_states and preexisting_fp_start != 1:
                fp_reactivate_exclusion.append("NO_RECOGNISED_OR_PREEXISTING_T1")
            if s2 not in valid_states:
                fp_reactivate_exclusion.append("UNRESOLVED_OR_INVALID_T2")
            fp_reactivate_exclusion = list(dict.fromkeys(fp_reactivate_exclusion))
            fp_reactivate_model_eligible = 1 if not fp_reactivate_exclusion else 0

            # The primary broad-FP population has its own independent eligibility test.
            fp_reactivate_exclusion_primary = [
                x for x in primary_exclusion if x != "NO_RECOGNISED_OR_LATENT_T1_STATE"
            ]
            if effective_t1 not in valid_states and preexisting_fp_start_primary != 1:
                fp_reactivate_exclusion_primary.append("NO_RECOGNISED_LATENT_OR_PREEXISTING_T1")
            fp_reactivate_exclusion_primary = list(dict.fromkeys(fp_reactivate_exclusion_primary))
            fp_reactivate_model_eligible_primary = 1 if not fp_reactivate_exclusion_primary else 0

            # First-reactivation baseline risk closes permanently after an eligible first event.
            already_reactivated = base_event_seen.get(pid, False)
            base_reactivate_risk = 1 if (
                init_fp_cohort == 1
                and not already_reactivated
                and s1 == "STABILISED_FLOODPLAIN"
            ) else 0
            base_reactivate_evt = 1 if (
                base_reactivate_risk == 1
                and ev.get("REACTIVATE_EVT", 0) == 1
            ) else 0
            if base_reactivate_evt == 1:
                base_event_seen[pid] = True
                qa["base_first_evt"] += 1

            # Primary first-event closure is tracked independently from strict closure.
            already_reactivated_primary = base_event_seen_primary.get(pid, False)
            base_reactivate_risk_primary = 1 if (
                init_fp_cohort == 1
                and not already_reactivated_primary
                and pev["REACTIVATE_RISK_SET_PRIMARY"] == 1
            ) else 0
            base_reactivate_evt_primary = 1 if (
                base_reactivate_risk_primary == 1
                and pev["REACTIVATE_EVT_PRIMARY"] == 1
            ) else 0
            if base_reactivate_evt_primary == 1:
                base_event_seen_primary[pid] = True
                qa["base_first_evt_primary"] += 1

            # Final whole-record assemblage metrics are copied for interpretation, not lagged prediction.
            # Revised 4a persistence-promotion fields from Step 2 lookup.
            # Step 2 prefixes Module 4a fields with ASM_, but accept unprefixed
            # names defensively in case a direct/custom lookup is supplied.
            final_onto_raw = self._asm_get_any(asm_attrs, "ASM_FINAL_ONTO_RAW", "FINAL_ONTO_RAW")
            fp_condition = self._asm_get_any(asm_attrs, "ASM_FP_CONDITION", "FP_CONDITION")
            fp_stab = self._as_float(self._asm_get_any(asm_attrs, "ASM_FP_STAB", "FP_STAB"), None)
            fp_recent = self._as_float(self._asm_get_any(asm_attrs, "ASM_FP_RECENT", "FP_RECENT"), None)
            fp_reworked = self._as_float(self._asm_get_any(asm_attrs, "ASM_FP_REWORKED", "FP_REWORKED"), None)
            surface_age_est = self._as_float(self._asm_get_any(asm_attrs, "ASM_SURFACE_AGE_EST", "SURFACE_AGE_EST"), None)

            # Emit a complete audit trail: endpoints, strict/primary events, eligibility and exclusions.
            # Ontology state/event fields.
            attrs.update({
                "ONTO_STATE_T1": s1,
                "ONTO_STATE_T2": s2,
                "ONTO_TRANS": trans,
                "ONTOLOGY_TRANS": trans,
                "DOMAIN_TRANS_ONTO": trans,
                "STATE1_ONTOLOGY": s1,
                "STATE2_ONTOLOGY": s2,
                "M3_STATE_T1": m3_s1,
                "M3_STATE_T2": m3_s2,
                "ASM_STATE_T1_QA": asm_s1,
                "ASM_STATE_T2_QA": asm_s2,
                "STATE_SOURCE_T1": source_t1,
                "STATE_SOURCE_T2": source_t2,
                "M3_ASM_DISAGREE_T1": disagree_t1,
                "M3_ASM_DISAGREE_T2": disagree_t2,
                "M3_ASM_DISAGREE_ANY": disagree_any,
                "M3_MODEL_ELIGIBLE_STRICT": strict_eligible,
                "M3_MODEL_EXCLUSION_REASON": ";".join(strict_exclusion) if strict_exclusion else "NONE",
                "M3_EFFECTIVE_STATE_T1_PRIMARY": effective_t1,
                "M3_EFFECTIVE_STATE_T2_PRIMARY": effective_t2_primary,
                "M3_MODEL_ELIGIBLE_PRIMARY": primary_eligible,
                "M3_MODEL_EXCLUSION_REASON_PRIMARY": ";".join(primary_exclusion) if primary_exclusion else "NONE",
                "PRIMARY_EVENT_DEFINITION_MISMATCH": pev["PRIMARY_EVENT_DEFINITION_MISMATCH"],
                "PRIMARY_RISK_DEFINITION_MISMATCH": pev["PRIMARY_RISK_DEFINITION_MISMATCH"],
                "PRIMARY_EVENT_RISK_MISMATCH": pev["PRIMARY_EVENT_RISK_MISMATCH"],
                # The descriptive event-type label is selected from the strict transition flags.
                "EVENT_TYPE_ONTO": "active_domain_reactivation" if ev["REACTIVATE_EVT"] else (
                    "depositional_storage_creation" if ev["STORAGE_EVT"] else (
                        "storage_stabilisation" if ev["STABILISE_EVT"] else (
                            "storage_reworking_to_active" if ev["STORAGE_REWORK_EVT"] else (
                                "floodplain_entered_storage" if ev["FP_STORAGE_EVT"] else (
                                    "other_state_transition" if ev["ANY_STATE_EVT"] else "persistence_no_transition"
                                )
                            )
                        )
                    )
                ),
                # The primary descriptive label uses the ambiguity-bridged event flags.
                "EVENT_TYPE_PRIMARY": "active_domain_reactivation" if pev["REACTIVATE_EVT_PRIMARY"] else (
                    "depositional_storage_creation" if pev["STORAGE_EVT_PRIMARY"] else (
                        "storage_stabilisation" if pev["STABILISE_EVT_PRIMARY"] else (
                            "storage_reworking_to_active" if pev["STORAGE_REWORK_EVT_PRIMARY"] else (
                                "floodplain_entered_storage" if pev["FP_STORAGE_EVT_PRIMARY"] else (
                                    "other_state_transition" if pev["ANY_STATE_EVT_PRIMARY"] else "persistence_no_transition"
                                )
                            )
                        )
                    )
                ),
                "STATE_TRANS": trans,
                "EVENT_TYPE_STATE": "active_domain_reactivation" if ev["REACTIVATE_EVT"] else (
                    "depositional_storage_creation" if ev["STORAGE_EVT"] else (
                        "storage_stabilisation" if ev["STABILISE_EVT"] else (
                            "storage_reworking_to_active" if ev["STORAGE_REWORK_EVT"] else (
                                "floodplain_entered_storage" if ev["FP_STORAGE_EVT"] else (
                                    "other_state_transition" if ev["ANY_STATE_EVT"] else "persistence_no_transition"
                                )
                            )
                        )
                    )
                ),
                "ACTIVE_DOMAIN_T1": 1 if s1 == "ACTIVE_DOMAIN" else 0,
                "ACTIVE_DOMAIN_T2": 1 if s2 == "ACTIVE_DOMAIN" else 0,
                "STORAGE_T1": 1 if s1 == "DEPOSITIONAL_STORAGE" else 0,
                "STORAGE_T2": 1 if s2 == "DEPOSITIONAL_STORAGE" else 0,
                "STAB_FP_T1": 1 if s1 == "STABILISED_FLOODPLAIN" else 0,
                "STAB_FP_T2": 1 if s2 == "STABILISED_FLOODPLAIN" else 0,
                "REACTIVATE_TRANS": ev["REACTIVATE_TRANS"],
                "STORAGE_TRANS": ev["STORAGE_TRANS"],
                "STABILISE_TRANS": ev["STABILISE_TRANS"],
                "STORAGE_REWORK_TRANS": ev["STORAGE_REWORK_TRANS"],
                "FP_STORAGE_TRANS": ev["FP_STORAGE_TRANS"],
                "REACTIVATE_EVT": ev["REACTIVATE_EVT"],
                "STORAGE_EVT": ev["STORAGE_EVT"],
                "STABILISE_EVT": ev["STABILISE_EVT"],
                "STORAGE_REWORK_EVT": ev["STORAGE_REWORK_EVT"],
                "FP_STORAGE_EVT": ev["FP_STORAGE_EVT"],
                "ANY_STATE_EVT": ev["ANY_STATE_EVT"],
                "ANY_ONTO_EVT": ev["ANY_ONTO_EVT"],
                "REACTIVATE_RISK_SET": ev["REACTIVATE_RISK_SET"],
                # Keep original FP source/support/eligibility fields separate from strict SF risk fields.
                "PREEXISTING_FP_START": preexisting_fp_start,
                "PREEXISTING_FP_START_PRIMARY": preexisting_fp_start_primary,
                "PREEXISTING_FP_SUPPORT_OK": preexisting_support_ok,
                "PREEXISTING_FP_DISTURBED_PREV": 1 if disturbed_prev else 0,
                "FP_REACTIVATE_SOURCE": fp_reactivate_source,
                "FP_REACTIVATE_SOURCE_PRIMARY": fp_reactivate_source_primary,
                "FP_REACTIVATE_RISK_SET": fp_reactivate_risk,
                "FP_REACTIVATE_EVT": fp_reactivate_evt,
                "FP_REACTIVATE_MODEL_ELIGIBLE": fp_reactivate_model_eligible,
                "FP_REACTIVATE_EXCLUSION_REASON": ";".join(fp_reactivate_exclusion) if fp_reactivate_exclusion else "NONE",
                "FP_REACTIVATE_RISK_SET_PRIMARY": fp_reactivate_risk_primary,
                "FP_REACTIVATE_EVT_PRIMARY": fp_reactivate_evt_primary,
                "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY": fp_reactivate_model_eligible_primary,
                "FP_REACTIVATE_EXCLUSION_REASON_PRIMARY": ";".join(fp_reactivate_exclusion_primary) if fp_reactivate_exclusion_primary else "NONE",
                "STORAGE_RISK_SET": ev["STORAGE_RISK_SET"],
                "STABILISE_RISK_SET": ev["STABILISE_RISK_SET"],
                "STORAGE_REWORK_RISK_SET": ev["STORAGE_REWORK_RISK_SET"],
                "FP_STORAGE_RISK_SET": ev["FP_STORAGE_RISK_SET"],
                "ANY_STATE_RISK_SET": ev["ANY_STATE_RISK_SET"],
                "RISK_SET": ev["RISK_SET"],
                "REACTIVATE_EVT_PRIMARY": pev["REACTIVATE_EVT_PRIMARY"],
                "STORAGE_EVT_PRIMARY": pev["STORAGE_EVT_PRIMARY"],
                "STABILISE_EVT_PRIMARY": pev["STABILISE_EVT_PRIMARY"],
                "STORAGE_REWORK_EVT_PRIMARY": pev["STORAGE_REWORK_EVT_PRIMARY"],
                "FP_STORAGE_EVT_PRIMARY": pev["FP_STORAGE_EVT_PRIMARY"],
                "ANY_STATE_EVT_PRIMARY": pev["ANY_STATE_EVT_PRIMARY"],
                "REACTIVATE_BRIDGED": pev["REACTIVATE_BRIDGED"],
                "STORAGE_BRIDGED": pev["STORAGE_BRIDGED"],
                "STORAGE_REWORK_BRIDGED": pev["STORAGE_REWORK_BRIDGED"],
                "FP_STORAGE_BRIDGED": pev["FP_STORAGE_BRIDGED"],
                "REACTIVATE_RISK_SET_PRIMARY": pev["REACTIVATE_RISK_SET_PRIMARY"],
                "STORAGE_RISK_SET_PRIMARY": pev["STORAGE_RISK_SET_PRIMARY"],
                "STABILISE_RISK_SET_PRIMARY": pev["STABILISE_RISK_SET_PRIMARY"],
                "STORAGE_REWORK_RISK_SET_PRIMARY": pev["STORAGE_REWORK_RISK_SET_PRIMARY"],
                "FP_STORAGE_RISK_SET_PRIMARY": pev["FP_STORAGE_RISK_SET_PRIMARY"],
                "ANY_STATE_RISK_SET_PRIMARY": pev["ANY_STATE_RISK_SET_PRIMARY"],
                # Legacy E/D output aliases reflect strict events; raw E/D inputs are retained separately.
                # Backwards compatibility. E is active-domain reactivation;
                # D is storage production. Stabilisation is retained separately.
                "E_evt": ev["REACTIVATE_EVT"] if out_fields.indexFromName("E_evt") >= 0 else None,
                "D_evt": ev["STORAGE_EVT"] if out_fields.indexFromName("D_evt") >= 0 else None,
                "E_RISK_SET": ev["REACTIVATE_RISK_SET"],
                "D_RISK_SET": ev["STORAGE_RISK_SET"],
                "E_EVT_RAW": ev["E_EVT_RAW"],
                "D_EVT_RAW": ev["D_EVT_RAW"],
                "E_CONFIRM_AVAILABLE": ev["E_CONFIRM_AVAILABLE"],
                "D_CONFIRM_AVAILABLE": ev["D_CONFIRM_AVAILABLE"],
                "INIT_FP_COHORT": init_fp_cohort,
                "BASE_REACTIVATE_RISK_SET": base_reactivate_risk,
                "BASE_REACTIVATE_RISK_SET_DERIVED": base_reactivate_risk,
                "BASE_REACTIVATE_EVT": base_reactivate_evt,
                "BASE_REACTIVATE_RISK_SET_PRIMARY_DERIVED": base_reactivate_risk_primary,
                "BASE_REACTIVATE_EVT_PRIMARY": base_reactivate_evt_primary,
                # Do not include VALID_NEXT or NEXT targets as antecedent predictors.
                "VALID_NEXT": 1 if (include_next and next_by_row.get(row_idx, (None, None, None, None))[0] is not None) else 0,
                "STATE_MODEL_VERSION": "active_domain_storage_clock_stage4_step3_v6_7_broad_fp_reactivation",
                "ONTOLOGY_VERSION": "active_domain_storage_clock_stage4_step3_v6_7_broad_fp_reactivation",
                "DIST_EVENT_ONTO": "active_domain_reactivation" if ev["REACTIVATE_EVT"] else (
                    "depositional_storage_creation" if ev["STORAGE_EVT"] else (
                        "storage_stabilisation" if ev["STABILISE_EVT"] else (
                            "storage_reworking_to_active" if ev["STORAGE_REWORK_EVT"] else (
                                "floodplain_entered_storage" if ev["FP_STORAGE_EVT"] else (
                                    "other_state_transition" if ev["ANY_STATE_EVT"] else "no_state_event"
                                )
                            )
                        )
                    )
                ),
                "DEPO_INTERP_ONTO": "deposition_is_storage_not_floodplain_until_stabilised",
                "FINAL_ONTO_RAW": final_onto_raw,
                "FP_CONDITION": fp_condition,
                "FP_STAB": fp_stab,
                "FP_RECENT": fp_recent,
                "FP_REWORKED": fp_reworked,
                "SURFACE_AGE_EST": surface_age_est
            })

            # The following interval outcomes are response-side conveniences only.
            if include_next:
                ns, nt, nev, npev = next_by_row.get(row_idx, (None, None, None, None))
                attrs["ONTO_STATE_NEXT"] = ns
                attrs["ONTO_TRANS_NEXT"] = nt
                attrs["REACTIVATE_NEXT"] = nev["REACTIVATE_EVT"] if nev else None
                attrs["STORAGE_NEXT"] = nev["STORAGE_EVT"] if nev else None
                attrs["STABILISE_NEXT"] = nev["STABILISE_EVT"] if nev else None
                attrs["STORAGE_REWORK_NEXT"] = nev["STORAGE_REWORK_EVT"] if nev else None
                attrs["FP_STORAGE_NEXT"] = nev["FP_STORAGE_EVT"] if nev else None
                attrs["ANY_STATE_NEXT"] = nev["ANY_STATE_EVT"] if nev else None
                attrs["ANY_ONTO_NEXT"] = nev["ANY_ONTO_EVT"] if nev else None
                attrs["REACTIVATE_NEXT_PRIMARY"] = npev["REACTIVATE_EVT_PRIMARY"] if npev else None
                attrs["STORAGE_NEXT_PRIMARY"] = npev["STORAGE_EVT_PRIMARY"] if npev else None
                attrs["STABILISE_NEXT_PRIMARY"] = npev["STABILISE_EVT_PRIMARY"] if npev else None
                attrs["STORAGE_REWORK_NEXT_PRIMARY"] = npev["STORAGE_REWORK_EVT_PRIMARY"] if npev else None
                attrs["FP_STORAGE_NEXT_PRIMARY"] = npev["FP_STORAGE_EVT_PRIMARY"] if npev else None
                attrs["ANY_STATE_NEXT_PRIMARY"] = npev["ANY_STATE_EVT_PRIMARY"] if npev else None

            # Append interval-start spatial distances and exact Stage 4 Step 2 lagged geometry.
            attrs.update({
                "DIST_ACTIVE_CURR": active_dist,
                "INSIDE_ACTIVE_CURR": active_inside,
                "DIST_ACTIVE_BIN": self._bin_distance(active_dist),
                "DIST_ACTIVE_CURR_BIN": self._bin_distance(active_dist),
                "DIST_WATER_CURR": water_dist,
                "INSIDE_WATER_CURR": water_inside,
                "DIST_WATER_BIN": self._bin_distance(water_dist),
                "DIST_WATER_CURR_BIN": self._bin_distance(water_dist),
                "DIST_CL_CURR": cl_dist,
                "DIST_CL_CURR_BIN": self._bin_distance(cl_dist),
                "CL_MEASURE_CURR": cl_measure,
                "CURV_CL_CURR": curv,
                "CURV_EROSION_CURR": curv_erosion,
                "DIST_X_CURV_EROSION": dist_x_curv,

                # NULL exact-date covariates remain NULL: temporal fallback is prohibited.
                "GEOM_YMD_PREV": self._as_int(ts_geom.get("GEOM_YMD"), None) if ts_geom else None,
                "GEOM_YEAR_PREV": self._as_int(ts_geom.get("GEOM_YEAR"), None) if ts_geom else None,
                "DIST_CHANNEL_PREV": self._as_float(ts_geom.get("DIST_CHANNEL"), None) if ts_geom else None,
                "DIST_BANK_PREV": self._as_float(ts_geom.get("DIST_BANK"), None) if ts_geom else None,
                "BANK_SETBACK_PREV": self._as_float(ts_geom.get("BANK_SETBACK"), None) if ts_geom else None,
                "INSIDE_CHANNEL_PREV": self._as_int(ts_geom.get("INSIDE_CHANNEL"), None) if ts_geom else None,
                "DIST_CL_PREV": self._as_float(ts_geom.get("DIST_CL"), None) if ts_geom else None,
                "DIST_CL_PREV_BIN": self._bin_distance(self._as_float(ts_geom.get("DIST_CL"), None)) if ts_geom else None,
                "CL_MEASURE_PREV": self._as_float(ts_geom.get("CL_MEASURE"), None) if ts_geom else None,
                "CURV_SIGNED_PREV": self._as_float(ts_geom.get("CURV_SIGNED"), None) if ts_geom else None,
                "CURV_ABS_PREV": self._as_float(ts_geom.get("CURV_ABS"), None) if ts_geom else None,
                "CURV_SCALED_PREV": self._as_float(ts_geom.get("CURV_SCALED"), None) if ts_geom else None,
                "POINT_SIDE_PREV": str(ts_geom.get("POINT_SIDE")) if ts_geom and ts_geom.get("POINT_SIDE") is not None else None,
                "BANK_SIDE_PREV": str(ts_geom.get("BANK_SIDE")) if ts_geom and ts_geom.get("BANK_SIDE") is not None else None,
                "OUTER_BANK_PREV": self._as_int(ts_geom.get("OUTER_BANK"), None) if ts_geom else None,
                "INNER_BANK_PREV": self._as_int(ts_geom.get("INNER_BANK"), None) if ts_geom else None,
                "LOCAL_HALF_WIDTH_PREV": self._as_float(ts_geom.get("LOCAL_HALF_WIDTH"), None) if ts_geom else None,
                "LOCAL_WIDTH_PREV": self._as_float(ts_geom.get("LOCAL_WIDTH"), None) if ts_geom else None,
                "REL_CHANNEL_POS_PREV": self._as_float(ts_geom.get("REL_CHANNEL_POS"), None) if ts_geom else None,
                "NEAR_CHANNEL_HALF_PREV": self._as_int(ts_geom.get("NEAR_CHANNEL_HALF"), None) if ts_geom else None,
                "NEAR_CHANNEL_FULL_PREV": self._as_int(ts_geom.get("NEAR_CHANNEL_FULL"), None) if ts_geom else None,
                "NEAR_BANK_HALF_PREV": self._as_int(ts_geom.get("NEAR_BANK_HALF"), None) if ts_geom else None,
                "NEAR_BANK_FULL_PREV": self._as_int(ts_geom.get("NEAR_BANK_FULL"), None) if ts_geom else None,
                "OUTER_CURV_REACT_HALF_PREV": self._as_float(ts_geom.get("OUTER_CURV_REACT_HALF"), None) if ts_geom else None,
                "OUTER_CURV_REACT_FULL_PREV": self._as_float(ts_geom.get("OUTER_CURV_REACT_FULL"), None) if ts_geom else None,
                "INNER_CURV_STORAGE_HALF_PREV": self._as_float(ts_geom.get("INNER_CURV_STORAGE_HALF"), None) if ts_geom else None,
                "INNER_CURV_STORAGE_FULL_PREV": self._as_float(ts_geom.get("INNER_CURV_STORAGE_FULL"), None) if ts_geom else None,
                "OUTER_CURV_STORAGE_HALF_PREV": self._as_float(ts_geom.get("OUTER_CURV_STORAGE_HALF"), None) if ts_geom else None,
                "OUTER_CURV_STORAGE_FULL_PREV": self._as_float(ts_geom.get("OUTER_CURV_STORAGE_FULL"), None) if ts_geom else None,
                "GEOM_SEG_ID_PREV": str(ts_geom.get("GEOM_SEG_ID")) if ts_geom and ts_geom.get("GEOM_SEG_ID") is not None else None,
                "GEOM_SUPPORT_PREV": self._as_int(ts_geom.get("GEOM_SUPPORT"), None) if ts_geom else None
            })

            # Accumulate all QA counters before deciding whether to accept the run.
            qa["m3_asm_disagree_t1"] += disagree_t1
            qa["m3_asm_disagree_t2"] += disagree_t2
            qa["m3_asm_disagree_any"] += disagree_any
            sev = str(self._get(f, "M3_ANOMALY_SEVERITY", "NONE") or "NONE").upper()
            if sev == "FATAL": qa["m3_fatal_anomaly_rows"] += 1
            elif sev == "WARNING": qa["m3_warning_anomaly_rows"] += 1
            if strict_eligible != 1:
                qa["m3_strict_ineligible_rows"] += 1
            if primary_eligible != 1:
                qa["m3_primary_ineligible_rows"] += 1
            if s1 == "UNRESOLVED":
                qa["unresolved_t1"] += 1
            if s2 == "UNRESOLVED":
                qa["unresolved_t2"] += 1
            # Tabulate strict risk/event pairs for each transition separately.
            qa["reactivate_risk"] += ev["REACTIVATE_RISK_SET"]
            qa["reactivate_evt"] += ev["REACTIVATE_EVT"]
            qa["storage_risk"] += ev["STORAGE_RISK_SET"]
            qa["storage_evt"] += ev["STORAGE_EVT"]
            qa["stabilise_risk"] += ev["STABILISE_RISK_SET"]
            qa["stabilise_evt"] += ev["STABILISE_EVT"]
            qa["storage_rework_risk"] += ev["STORAGE_REWORK_RISK_SET"]
            qa["storage_rework_evt"] += ev["STORAGE_REWORK_EVT"]
            qa["fp_storage_risk"] += ev["FP_STORAGE_RISK_SET"]
            qa["fp_storage_evt"] += ev["FP_STORAGE_EVT"]
            qa["any_state_evt"] += ev["ANY_STATE_EVT"]
            # Tabulate the primary ambiguity-bridged transition populations independently.
            qa["reactivate_risk_primary"] += pev["REACTIVATE_RISK_SET_PRIMARY"]
            qa["storage_risk_primary"] += pev["STORAGE_RISK_SET_PRIMARY"]
            qa["stabilise_risk_primary"] += pev["STABILISE_RISK_SET_PRIMARY"]
            qa["storage_rework_risk_primary"] += pev["STORAGE_REWORK_RISK_SET_PRIMARY"]
            qa["fp_storage_risk_primary"] += pev["FP_STORAGE_RISK_SET_PRIMARY"]
            qa["any_state_risk_primary"] += pev["ANY_STATE_RISK_SET_PRIMARY"]
            qa["reactivate_evt_primary"] += pev["REACTIVATE_EVT_PRIMARY"]
            # Tabulate broad FP->AD separately from strict SF->AD to prevent conflation.
            qa["fp_reactivate_risk"] += fp_reactivate_risk
            qa["fp_reactivate_evt"] += fp_reactivate_evt
            qa["fp_reactivate_risk_primary"] += fp_reactivate_risk_primary
            qa["fp_reactivate_evt_primary"] += fp_reactivate_evt_primary
            qa["preexisting_fp_start"] += preexisting_fp_start
            qa["preexisting_fp_start_primary"] += preexisting_fp_start_primary
            if fp_reactivate_model_eligible != 1:
                qa["fp_reactivate_model_ineligible"] += 1
            if fp_reactivate_model_eligible_primary != 1:
                qa["fp_reactivate_model_ineligible_primary"] += 1
            if fp_reactivate_evt and not fp_reactivate_risk:
                qa["fp_reactivate_event_risk_mismatch"] += 1
            if fp_reactivate_evt_primary and not fp_reactivate_risk_primary:
                qa["fp_reactivate_event_risk_mismatch_primary"] += 1
            qa["storage_evt_primary"] += pev["STORAGE_EVT_PRIMARY"]
            qa["stabilise_evt_primary"] += pev["STABILISE_EVT_PRIMARY"]
            qa["storage_rework_evt_primary"] += pev["STORAGE_REWORK_EVT_PRIMARY"]
            qa["fp_storage_evt_primary"] += pev["FP_STORAGE_EVT_PRIMARY"]
            qa["any_state_evt_primary"] += pev["ANY_STATE_EVT_PRIMARY"]
            qa["reactivate_bridged"] += pev["REACTIVATE_BRIDGED"]
            qa["storage_bridged"] += pev["STORAGE_BRIDGED"]
            qa["storage_rework_bridged"] += pev["STORAGE_REWORK_BRIDGED"]
            qa["fp_storage_bridged"] += pev["FP_STORAGE_BRIDGED"]
            qa["primary_event_definition_mismatch"] += pev["PRIMARY_EVENT_DEFINITION_MISMATCH"]
            qa["primary_risk_definition_mismatch"] += pev["PRIMARY_RISK_DEFINITION_MISMATCH"]
            qa["primary_event_risk_mismatch"] += pev["PRIMARY_EVENT_RISK_MISMATCH"]
            if (
                # Strict event-in-risk-set checks must hold for all five transitions.
                (ev["REACTIVATE_EVT"] and not ev["REACTIVATE_RISK_SET"])
                or (ev["STORAGE_EVT"] and not ev["STORAGE_RISK_SET"])
                or (ev["STABILISE_EVT"] and not ev["STABILISE_RISK_SET"])
                or (ev["STORAGE_REWORK_EVT"] and not ev["STORAGE_REWORK_RISK_SET"])
                or (ev["FP_STORAGE_EVT"] and not ev["FP_STORAGE_RISK_SET"])
            ):
                qa["event_risk_mismatch"] += 1

            # Partial geometric contact alone does not end inherited-FP eligibility.
            # Close inherited/pre-existing status for subsequent intervals only after
            # the PLACE has actually entered a recognised Active Domain or Depositional
            # Storage state. Partial bank overlap and raw E/D area evidence alone do not
            # close the floodplain risk period; otherwise a migrating bank could remove
            # a PLACE from the risk set one interval before the state transition is observed.
            # Recognised AD/DS occupancy closes the pre-existing branch for later intervals.
            current_disturbance = bool(
                s1 in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"}
                or s2 in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"}
                or effective_t1 in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"}
                or effective_t2_primary in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"}
            )
            if current_disturbance:
                prior_disturbance_seen[pid] = True

            # Write one ordered non-spatial attribute record for this interval.
            out_feat.setAttributes([attrs.get(n, None) for n in out_fields.names()])
            # Preserve the original sink-insertion call unchanged in this comments-only edition.
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        # Emit aggregate transition counts and data-completeness diagnostics after writing.
        feedback.setProgress(100)
        feedback.pushInfo("[Stage 4 Step 3] Finished state-aware risk table.")
        feedback.pushInfo(
            "[Stage 4 Step 3] QA counts | "
            f"rows={qa['rows']:,}; "
            f"reactivate risk/events={qa['reactivate_risk']:,}/{qa['reactivate_evt']:,}; "
            f"storage risk/events={qa['storage_risk']:,}/{qa['storage_evt']:,}; "
            f"stabilise risk/events={qa['stabilise_risk']:,}/{qa['stabilise_evt']:,}; "
            f"storage-rework risk/events={qa['storage_rework_risk']:,}/{qa['storage_rework_evt']:,}; "
            f"floodplain-storage risk/events={qa['fp_storage_risk']:,}/{qa['fp_storage_evt']:,}; "
            f"any strict state transitions={qa['any_state_evt']:,}; "
            f"baseline strict first reactivations={qa['base_first_evt']:,}."
        )
        # Primary reporting highlights bridged events and their eligible risk sets.
        feedback.pushInfo(
            "[Stage 4 Step 3] Primary ambiguity-bridged events | "
            f"reactivate risk/events={qa['reactivate_risk_primary']:,}/{qa['reactivate_evt_primary']:,} (bridged={qa['reactivate_bridged']:,}); "
            f"storage risk/events={qa['storage_risk_primary']:,}/{qa['storage_evt_primary']:,} (bridged={qa['storage_bridged']:,}); "
            f"stabilise risk/events={qa['stabilise_risk_primary']:,}/{qa['stabilise_evt_primary']:,}; "
            f"storage-rework risk/events={qa['storage_rework_risk_primary']:,}/{qa['storage_rework_evt_primary']:,} (bridged={qa['storage_rework_bridged']:,}); "
            f"floodplain-storage risk/events={qa['fp_storage_risk_primary']:,}/{qa['fp_storage_evt_primary']:,} (bridged={qa['fp_storage_bridged']:,}); "
            f"any primary transitions={qa['any_state_evt_primary']:,}; "
            f"baseline primary first reactivations={qa['base_first_evt_primary']:,}."
        )
        # Broad FP->AD is reported separately because it has a distinct prediction population.
        feedback.pushInfo(
            "[Stage 4 Step 3] v6.7 broadened floodplain reactivation | "
            f"strict-equivalent+pre-existing risk/events={qa['fp_reactivate_risk']:,}/{qa['fp_reactivate_evt']:,}; "
            f"primary risk/events={qa['fp_reactivate_risk_primary']:,}/{qa['fp_reactivate_evt_primary']:,}; "
            f"pre-existing T1 strict/primary={qa['preexisting_fp_start']:,}/{qa['preexisting_fp_start_primary']:,}; "
            f"broad-model ineligible strict/primary={qa['fp_reactivate_model_ineligible']:,}/{qa['fp_reactivate_model_ineligible_primary']:,}."
        )
        feedback.pushInfo(
            "[Stage 4 Step 3] QA coverage | "
            f"unresolved T1/T2={qa['unresolved_t1']:,}/{qa['unresolved_t2']:,}; "
            f"missing PLACE geometry={qa['missing_place_geom']:,}; "
            f"missing ASM lookup={qa['missing_asm_lookup']:,}; "
            f"missing dated active/water/centreline exposure="
            f"{qa['missing_active_date']:,}/{qa['missing_water_date']:,}/{qa['missing_centreline_date']:,}; "
            f"missing exact Stage 4 Step 2 timestep geometry={qa['missing_timestep_geometry']:,}."
        )
        # M3-vs-M4a disagreements qualify state attribution but never change M3 endpoints.
        feedback.pushInfo(
            "[Stage 4 Step 3] Module 3 versus Module 4a state QA | "
            f"disagreement T1/T2/any={qa['m3_asm_disagree_t1']:,}/{qa['m3_asm_disagree_t2']:,}/{qa['m3_asm_disagree_any']:,}; "
            f"Module 4a modelling fallback T1/T2=0/0; "
            f"Module 3 fatal/warning anomaly rows={qa['m3_fatal_anomaly_rows']:,}/{qa['m3_warning_anomaly_rows']:,}; "
            f"strict-model-ineligible rows={qa['m3_strict_ineligible_rows']:,}; "
            f"primary-model-ineligible rows={qa['m3_primary_ineligible_rows']:,}."
        )
        # A strict event outside its risk set indicates invalid modelling data.
        if qa["event_risk_mismatch"]:
            feedback.pushWarning(
                f"[Stage 4 Step 3] Event/risk-set mismatches detected: {qa['event_risk_mismatch']:,}. "
                "This should be zero."
            )
        else:
            feedback.pushInfo("[Stage 4 Step 3] QA passed: every strict transition event is inside its matching strict risk set.")
        # Mismatches in Module 3 primary bridging invalidate historical event definitions.
        if (qa["primary_event_risk_mismatch"] or qa["primary_event_definition_mismatch"] or qa["primary_risk_definition_mismatch"]):
            feedback.pushWarning(
                "[Stage 4 Step 3] Primary-field QA failures | "
                f"event-risk={qa['primary_event_risk_mismatch']:,}; "
                f"event-definition={qa['primary_event_definition_mismatch']:,}; "
                f"risk-definition={qa['primary_risk_definition_mismatch']:,}."
            )
        else:
            feedback.pushInfo("[Stage 4 Step 3] QA passed: Module 3B primary events and latent-state risk sets reconcile exactly.")

        # Broad FP predictions must also obey event-within-risk population inclusion.
        if qa["fp_reactivate_event_risk_mismatch"] or qa["fp_reactivate_event_risk_mismatch_primary"]:
            feedback.pushWarning(
                "[Stage 4 Step 3] Broad floodplain-reactivation event/risk mismatch | "
                f"strict={qa['fp_reactivate_event_risk_mismatch']:,}; "
                f"primary={qa['fp_reactivate_event_risk_mismatch_primary']:,}."
            )
        else:
            feedback.pushInfo(
                "[Stage 4 Step 3] QA passed: every FP_REACTIVATE event is inside its broadened floodplain risk set."
            )

        # Log the intended primary explanatory model fields and their strict sensitivity analogues.
        feedback.pushInfo(
            "[Stage 4 Step 3] In R, principal process-transition models should use *_EVT_PRIMARY, *_RISK_SET_PRIMARY "
            "and M3_MODEL_ELIGIBLE_PRIMARY. Strict fields are retained for sensitivity analysis."
        )
        # Log the distinct broad FP prediction event/risk/eligibility field triplet.
        feedback.pushInfo(
            "[Stage 4 Step 3] For broadened lateral-erosion forecasting use "
            "FP_REACTIVATE_EVT_PRIMARY + FP_REACTIVATE_RISK_SET_PRIMARY + "
            "FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY. FP_REACTIVATE_SOURCE_PRIMARY distinguishes "
            "STABILISED_FLOODPLAIN from PREEXISTING_FLOODPLAIN."
        )
        feedback.pushInfo(
            "[Stage 4 Step 3] Strict sensitivity fields: "
            "REACTIVATE_RISK_SET, STORAGE_RISK_SET, STABILISE_RISK_SET, "
            "or ANY_STATE_RISK_SET."
        )
        feedback.pushInfo(
            "[Stage 4 Step 3] REACTIVATE/STORAGE/STABILISE/STORAGE_REWORK/FP_STORAGE events and risk sets are state-defined. "
            "E_EVT_RAW/D_EVT_RAW retain Module 3 evidence for disagreement QA only."
        )
        # Maps should join output rows back to KM_blocks on PLACE/BLOCK ID.
        feedback.pushInfo(
            "[Stage 4 Step 3] Output architecture: authoritative Risk Table is non-spatial; "
            "KM_blocks remains the single geometry source. Join selected intervals or predictions "
            "back to KM_blocks by BLOCK_ID only when a spatial map is required."
        )
        # Fatal QA anomalies stop completion instead of silently accepting a compromised Risk Table.
        if (qa["event_risk_mismatch"] or qa["primary_event_risk_mismatch"] or
            qa["primary_event_definition_mismatch"] or qa["primary_risk_definition_mismatch"] or
            qa["fp_reactivate_event_risk_mismatch"] or qa["fp_reactivate_event_risk_mismatch_primary"] or
            qa["m3_fatal_anomaly_rows"]):
            raise QgsProcessingException(
                "Stage 4 Step 3 stopped because Module 3 fatal anomalies or strict/primary event-risk definition mismatches were propagated. "
                "Inspect M3_ANOMALY_FLAGS and rerun Module 3B/3C before modelling."
            )

        # Return the original QGIS output sink destination; no additional outputs are added.
        return {self.OUTPUT: dest_id}
