# -*- coding: utf-8 -*-
# =============================================================================
# FRAF PAPER 2 | 04 — COVARIATE ATTRIBUTION
# =============================================================================
# Script:  FRAF_P2_04_CovariateAttribution_v6_4.py
# Source:  FRAF_Stage4_Step2_Covariate_Lookup_v6_4_UNION_DOMAIN_GENERIC_RIVER_STYLE.py
# Version: 6.4 (comment-only publication-archive edition; calculations unchanged)
# Runtime: QGIS Processing / PyQGIS, with polygon overlays in a common CRS.
#
# PURPOSE AND PLACE IN THE FRAF WORKFLOW
# --------------------------------------
# This stage attributes reconstructed assemblage characteristics and spatial
# exposures to the stable PLACE/BLOCK grid.  It does not reconstruct the
# assemblage (the preceding Assemblage History stage does that), nor does it
# construct an outcome-specific risk set (the following risk/covariate stage
# combines these lookups with the authoritative PLACE_interval_long history).
#
# Principal inputs:
#   ASM                         Planar Assemblage_Units or corresponding polygon
#                               output with per-step state/EA history and metrics.
#   PLACE                       KM_blocks: exactly one polygon per BLOCK_ID.
#   UNION_CHANNEL_LAYER         Dissolved historical Active Domain union (optional).
#   ACTIVE / WATER / CENTRELINE Current/reference geometry (optional).
#   TIMESTEP_CHANNELS           Standardised channel polygons with GEOM_YMD.
#   TIMESTEP_SEGMENTS           Dated centreline segments with GEOM_YMD and
#                               local width, tangent and curvature attributes.
#
# Principal outputs (separate sinks to avoid repeating PLACE geometry):
#   OUTPUT_POLY             One polygon per PLACE; mapped QA and transferred data.
#   OUTPUT_LOOKUP           One attribute row per PLACE; static/reference lookup.
#   OUTPUT_TIMESTEP_LOOKUP  One row per PLACE x matched GEOM_YMD; time-varying
#                           geometry is stored in a non-spatial table.
#   OUTPUT_UNION_QA         Single-row reconciliation of historical-union area.
#
# ATTRIBUTION RULES
# -----------------
# 1. Numerics are intersection-area-weighted means of covered assemblage cells.
# 2. Text/state/history fields use the category with maximum intersected area.
# 3. State fractions use *total PLACE area*, including unsampled/unresolved area;
#    they are separate from a dominant categorical state label.
# 4. Historical-union weights compare the full PLACE/corridor with the nested
#    union domain; they do not identify a transition-specific eligibility set.
# 5. GEOM_YMD covariates are calculated independently for each matching dated
#    channel/centreline geometry pair; subsequent modelling must choose only
#    geometry and assemblage history available at the relevant interval origin.
#
# INTERPRETATION / LIMITS
# -----------------------
# - A complete-history ASM_* metric is retrospective unless a later stage
#   reconstructs its antecedent-only counterpart.  Never insert final-history
#   quantities directly as prospective predictors without temporal restriction.
# - AREA and distance measurements follow the input projected CRS; coordinate
#   units must be metres for '_M2', distance-bin and width interpretations.
# - This script does NOT derive REACTIVATE_EVT / STORAGE_EVT / STABILISE_EVT, and
#   does not collapse interval event/risk flags into a static PLACE attribute.
# - Operational broad FP prediction eligibility is a later selection: eligible
#   existing floodplain plus SF, excluding DS.  It is not the initial FP cohort.
# - The code is preserved exactly, including existing state-alias conventions.
#
# SCIENTIFIC LINEAGE (methodological context, not authorship of this script)
# -----------------------------------------------------------------------
# Rusnak, M., Opravil, S., Dunesme, S., Afzali, H., Rey, L., Parmentier, H.,
# Piegay, H. (2025). A channel shifting GIS toolbox for exploring floodplain
# dynamics through channel erosion and deposition. Geomorphology 477, 109688.
# https://doi.org/10.1016/j.geomorph.2025.109688
# This file is the later FRAF PLACE-covariate attribution implementation.
# =============================================================================


# State terminology: STABILISED_FLOODPLAIN -> ACTIVE_DOMAIN is REACTIVATE_EVT.
# v6.4: adds full-analysis-area versus union-channel domain weights and QA.
# Retains the v6.3 unrestricted-text split
# table-geometry architecture. Use KM_blocks as the fixed
# one-row-per-BLOCK_ID geometry; keep interval history in PLACE_interval_long; write
# static and timestep covariate lookup tables without duplicating interval geometry.
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsSpatialIndex,
    QgsFeatureSink,
    QgsWkbTypes,
    QgsGeometry,
)
from qgis.PyQt.QtCore import QVariant
import re
import math


# PROCESSING ALGORITHM: the QGIS identifier, parameter names and field contracts are retained for
# backward compatibility.
class Stage4_Step2_CovariateLookup_v6_4(QgsProcessingAlgorithm):
    """
    Stage 4 Step 2 — PLACE covariate lookup, split table-geometry version v6.4.

    Predecessor is the direct Module 4a assemblage/fabric output, not the old
    separate Step 1 statistics script.

    Transfers Module 4a polygon metrics to PLACE/BLOCK polygons using
    area-weighted overlap. Numeric metrics are area-weighted means. Categorical
    metrics are dominant-overlap classes.

    Important interval-history addition:
      EA_Class_i, Period_i and raw assemblage-state/transition-history
      fields are transferred to the PLACE lookup as dominant-overlap or
      area-weighted fields. Stage 4 Step 3 can then build no-leakage interval-specific
      ASM_*_PREV covariates and state-aware reactivation/storage/stabilisation
      histories for KM/AG/Cox modelling.

    v4 addition:
      Preserve static initial-floodplain cohort fields written by Module 3b
      in the non-spatial PLACE-level lookup table. Interval-specific event and
      risk-set fields are deliberately excluded: Stage 4 Step 3 must obtain those from
      PLACE_interval_long so they cannot be collapsed to one value per PLACE.

    v5 addition:
      Transfer revised Module 4a persistence-promotion fields: FINAL_ONTO_RAW,
      FP_CONDITION, FP_STAB, FP_RECENT, FP_REWORKED and SURFACE_AGE_EST.

    v5.3 corrections:
      - BASE_REACTIVATE_RISK_SET is no longer treated as a static PLACE field.
      - Interval-specific event/risk fields remain in PLACE_interval_long and
        are carried/derived by Stage 4 Step 3.
      - The script rejects an interval-long layer supplied as the static PLACE
        geometry input and warns about interval-only fields.
      - Additional state/period history aliases are recognised.

    v6.3 output-schema correction:
      - categorical and history fields use unrestricted text width instead of
        a hard 120-character limit;
      - preserves long ASM_ONTO_TRANS_SUM and related history strings in
        GeoPackage or temporary outputs;
      - every sink insertion is checked so partial outputs cannot be reported
        as successful.


    v6.4 union-domain addition:
      - accepts a dissolved union of all dated Active Domain/channel polygons;
      - calculates exact union overlap, outside-union area and union fraction for
        every fixed BLOCK_ID;
      - writes those static weights to the QA polygons and PLACE lookup;
      - writes a one-row union-domain area-balance QA table.
      The same tool is applicable to Meandering/Anabranching and Braided river styles.

    v6.0 timestep-geometry addition:
      - accepts standardised channel polygons and sampled centreline segments
        from the Meandering/Anabranching timestep channel-geometry preparation tool;
      - writes a separate PLACE x GEOM_YMD no-geometry lookup;
      - measures distance to channel and bank, local centreline position, bend
        side, and curvature exposure without collapsing time-varying values
        into the static PLACE lookup.
    """

    # Input keys used by the processing interface; ASM supplies histories, PLACE supplies the fixed
    # spatial subjects.
    ASM = "ASM"
    PLACE = "PLACE"

    # Historical-union overlay is an optional STATIC domain diagnostic, not the active state at any one
    # observation.
    CALC_UNION_DOMAIN = "CALC_UNION_DOMAIN"
    UNION_CHANNEL_LAYER = "UNION_CHANNEL_LAYER"

    # Reference/final geometries generate static descriptive distances; temporal prediction must avoid
    # using future reference layers.
    CALC_ACTIVE = "CALC_ACTIVE"
    ACTIVE_LAYER = "ACTIVE_LAYER"
    CALC_WATER = "CALC_WATER"
    WATER_LAYER = "WATER_LAYER"
    CALC_CENTRELINE = "CALC_CENTRELINE"
    CENTRELINE_LAYER = "CENTRELINE_LAYER"
    CALC_CURVATURE = "CALC_CURVATURE"
    CURV_WINDOW = "CURV_WINDOW"
    CHANNEL_WIDTH = "CHANNEL_WIDTH"

    # Dated channel and segment inputs define the optional longitudinal geometry lookup, keyed by
    # GEOM_YMD.
    CALC_TIMESTEP_GEOM = "CALC_TIMESTEP_GEOM"
    TIMESTEP_CHANNELS = "TIMESTEP_CHANNELS"
    TIMESTEP_SEGMENTS = "TIMESTEP_SEGMENTS"
    NEAR_HALF_MULT = "NEAR_HALF_MULT"
    NEAR_FULL_MULT = "NEAR_FULL_MULT"
    MIXED_STATE_MIN_FRAC = "MIXED_STATE_MIN_FRAC"

    # Four output sinks have distinct cardinalities: PLACE polygons, PLACE table, PLACE x date table,
    # and one QA row.
    OUTPUT_POLY = "OUTPUT_POLY"
    OUTPUT_LOOKUP = "OUTPUT_LOOKUP"
    OUTPUT_TIMESTEP_LOOKUP = "OUTPUT_TIMESTEP_LOOKUP"
    OUTPUT_UNION_QA = "OUTPUT_UNION_QA"

    # Each recognised numeric fabric metric is averaged over its intersected assemblage area, not summed
    # between cells.
    # Static numeric Module 4a metrics to area-weight onto PLACE polygons.
    NUMERIC_METRICS = [
        "N_STEPS",
        "N_EVENTS",
        "N_EROSION",
        "N_DEPOSITION",
        "N_ISL_ERO",
        "N_ISL_DEP",
        "N_ST_CH",
        "N_ST_IS",
        "N_ST_FP",
        "N_INACTIVE",
        "N_ACTIVE_DOM",
        "ACTIVE_DOM_FREQ",
        "N_STORAGE",
        "STORAGE_FREQ",
        "N_STAB_FP",
        "STAB_FP_FREQ",
        "N_ASM_REACTIVATE_TRANS",
        "N_ASM_STORAGE_TRANS",
        "N_ASM_STABILISE_TRANS",
        "N_ASM_ANY_TRANS",
        "DIST_COUNT",
        "DIST_FREQ",
        "DOM_RATIO",
        "NET_BAL",
        "N_EPISODES",
        "MAX_QUIET",
        "QUIET_RATIO",
        "FIRST_ACTIVE",
        "LAST_ACTIVE",
        "SINCE_ACTIVE",
        "ISL_FRAC",
        "LAST_ACT_STEP",
        "LAST_ACT_YR",
        "QUIET_SINCE",
        # These surface-age and persistence fields describe complete histories unless reconstructed from
        # antecedent steps later.
        # v5: revised 4a persistence-promotion / floodplain-condition fields
        "FP_STAB",
        "FP_RECENT",
        "FP_REWORKED",
        "SURFACE_AGE_EST",
        "RECORD_SPAN_YR",
        "SINCE_DISTURB_YR",
        "SINCE_DISTURB_STEP",
        "SINCE_ACTIVE_YR",
        "SINCE_ACTIVE_STEP",
        "SINCE_STORAGE_YR",
        "SINCE_STORAGE_STEP",
        "MAX_QUIET_YR",
        "MAX_QUIET_STEP",
    ]

    # For qualitative fabric characteristics, the class covering the greatest intersection area wins for
    # the PLACE.
    # Static categorical Module 4a fields to transfer by dominant overlap.
    CATEGORICAL_BASE_FIELDS = [
        "ASM_FREQ",
        "ASM_STYLE",
        "STRUCTURE_CL",
        "ASM_LABEL",
        "ACTIVITY_CL",
        "DOMINANCE_CL",
        "PRIMARY_STATE",
        "DOMAIN_CLASS",
        "DOMAIN_STATE",
        "DEPO_INTERP",
        "ASM_ONTOLOGY",
        "ASM_CLASS",
        "FINAL_ONTO_STATE",
        "ONTO_STATE",
        "ONTOLOGY_STATE",
        "ONTO_TRANS_SUM",
        "STORAGE_CLASS",
        "STABILISATION_CLASS",
        "ISLAND_CONTEXT",
        "LAST_ACT_PD",
        # v5: revised 4a persistence-promotion / floodplain-condition fields
        "FINAL_ONTO_RAW",
        "FP_CONDITION",
    ]

    # Initial cohort indicators belong to a static PLACE and are copied without reinterpreting their
    # definitions.
    # Static PLACE/BLOCK fields to preserve in the one-row-per-PLACE lookup.
    # These fields describe baseline cohort membership and do not vary by interval.
    # Transition-specific events/risk sets must remain in PLACE_interval_long.
    PLACE_LOOKUP_PASSTHROUGH_FIELDS = [
        "INIT_FP",
        "INIT_FP_AREA",
        "INIT_FP_PROP",
        "INIT_FP_COHORT",
        "BASE_RISK",
        "BASE_RISK_DEF",
        "INITIAL_FP",
        "INITIAL_FP_AREA",
        "INITIAL_FP_PROP",
        "INIT_FP_SOURCE",
        "INIT_FP_DEF",
        "BASE_COHORT",
        "BASE_COHORT_DEF",
    ]

    # Interval outcomes and eligibility must NEVER be transferred from a longitudinal table to this
    # one-row lookup.
    # Fields that vary by PLACE x interval. They are intentionally NOT copied
    # to the static lookup, even if they are present on an incorrectly supplied
    # PLACE layer. Stage 4 Step 3 reads them from PLACE_interval_long.
    INTERVAL_ONLY_PLACE_FIELDS = [
        "y1", "y2", "tstart_yr", "tstop_yr",
        "A_E", "A_D", "P_E", "P_D", "E_evt", "D_evt",
        "A_C1", "A_C2", "P_C1", "P_C2", "C1", "C2",
        "state1", "state2", "ACTIVE_T1", "ACTIVE_T2",
        "DOMAIN_T1", "DOMAIN_T2", "DOMAIN_TRANS",
        "ONTO_STATE_T1", "ONTO_STATE_T2", "ONTO_TRANS",
        "STATE1_ONTOLOGY", "STATE2_ONTOLOGY",
        "REACTIVATE_EVT", "STORAGE_EVT", "STABILISE_EVT", "ANY_ONTO_EVT",
        "REACTIVATE_RISK_SET", "STORAGE_RISK_SET", "STABILISE_RISK_SET",
        "BASE_REACTIVATE_RISK_SET",
        "E_RISK_SET", "D_RISK_SET", "RISK_SET", "at_risk",
    ]

    # QGIS registry methods: preserve the existing processing ID, menu labels and toolbox grouping.
    def name(self):
        return "stage4_step2_covariate_lookup_v6_4_union_domain"

    def displayName(self):
        return "Stage 4 Step 2 — Covariate Lookup v6.4 — union domain + generic river style"

    def group(self):
        return "SCS Toolbox"

    def groupId(self):
        return "scs_toolbox"

    # The QGIS help text enforces the separation between spatial reference, static covariates and
    # interval outcomes.
    def shortHelpString(self):
        return (
            "Stage 4 Step 2 links the direct Module 4a assemblage output to the fixed "
            "KM_blocks geometry. KM_blocks must contain one unique polygon per BLOCK_ID "
            "(PLACE_ID is accepted only as a legacy fallback). The tool writes: (1) a "
            "one-row-per-BLOCK_ID static covariate lookup, (2) an optional BLOCK_ID x "
            "GEOM_YMD timestep-geometry lookup, and (3) a one-row-per-BLOCK_ID QA polygon "
            "layer. It must not receive PLACE_interval_long; interval events, risk sets and "
            "states remain authoritative in that non-spatial Module 3B table and are joined "
            "later by Stage 4 Step 3. Optionally, a dissolved union-channel polygon is "
            "intersected with each BLOCK_ID to provide full-area and union-area weights. "
            "River-style terminology is generic: Meandering/Anabranching and Braided."
        )

    # QGIS clones the algorithm using a new instance of this class when a processing run is started.
    def createInstance(self):
        return Stage4_Step2_CovariateLookup_v6_4()

    # Register user-editable inputs and output sinks; default values are unchanged from the production
    # v6.4 script.
    def initAlgorithm(self, config=None):
        # Required data: chronological assemblage polygons and one fixed geometry polygon per place.
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.ASM,
            "Direct Module 4a assemblage polygon output",
            [QgsProcessing.TypeVectorPolygon],
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.PLACE,
            "KM_blocks / fixed PLACE geometry (one polygon per BLOCK_ID)",
            [QgsProcessing.TypeVectorPolygon],
        ))

        # The historical union is used only if CALC_UNION_DOMAIN is enabled (default True).
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_UNION_DOMAIN,
            "Calculate full-analysis-area versus union-channel overlap weights",
            defaultValue=True,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.UNION_CHANNEL_LAYER,
            "Dissolved union of all dated Active Domain/channel polygons",
            [QgsProcessing.TypeVectorPolygon],
            optional=True,
        ))

        # Current active-domain distance predictors are optional and off by default.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_ACTIVE,
            "Add current active-domain distance predictors to QA Place Poly",
            defaultValue=False,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.ACTIVE_LAYER,
            "Current/final active-domain polygon layer for prediction covariates",
            [QgsProcessing.TypeVectorPolygon],
            optional=True,
        ))

        # Water-mask distances are kept separate from Active Domain geometry and off by default.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_WATER,
            "Add current water-mask distance predictors to QA Place Poly",
            defaultValue=False,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.WATER_LAYER,
            "Current/final water polygon layer for prediction covariates",
            [QgsProcessing.TypeVectorPolygon],
            optional=True,
        ))

        # The reference centreline can be used for a point-to-centreline distance and local curvature
        # estimate.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_CENTRELINE,
            "Add current centreline distance predictors to QA Place Poly",
            defaultValue=True,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.CENTRELINE_LAYER,
            "Current/final or reference centreline layer for prediction covariates",
            [QgsProcessing.TypeVectorLine],
            optional=True,
        ))

        # Curvature is computed across a line-length half-window, then optionally multiplied by a
        # reference width.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_CURVATURE,
            "Add centreline curvature predictors to QA Place Poly",
            defaultValue=True,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.CURV_WINDOW,
            "Curvature half-window distance in layer units",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=5500.0,
            minValue=1.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.CHANNEL_WIDTH,
            "Representative channel width for dimensionless curvature scaling",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=11000.0,
            minValue=0.0,
        ))

        # The dated-geometry lookup is enabled by default and requires both channel polygons and segment
        # layers.
        self.addParameter(QgsProcessingParameterBoolean(
            self.CALC_TIMESTEP_GEOM,
            "Create PLACE x timestep channel-geometry covariate lookup",
            defaultValue=True,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.TIMESTEP_CHANNELS,
            "Standardised timestep channel polygons (geometry-preparation output)",
            [QgsProcessing.TypeVectorPolygon],
            optional=True,
        ))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.TIMESTEP_SEGMENTS,
            "Standardised timestep centreline segments (geometry-preparation output)",
            [QgsProcessing.TypeVectorLine],
            optional=True,
        ))
        # Near-channel/near-bank cut-offs are expressed as fractions of the corresponding locally
        # estimated width.
        self.addParameter(QgsProcessingParameterNumber(
            self.NEAR_HALF_MULT,
            "Half exposure threshold multiplier",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.5,
            minValue=0.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.NEAR_FULL_MULT,
            "Full exposure threshold multiplier",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1.0,
            minValue=0.0,
        ))

        # A PLACE is marked spatially mixed when at least two supported state fractions exceed this
        # threshold.
        self.addParameter(QgsProcessingParameterNumber(
            self.MIXED_STATE_MIN_FRAC,
            "Minimum PLACE-area fraction for a state to count toward mixed-state QA",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.10,
            minValue=0.0,
            maxValue=0.5,
        ))

        # Polygon sink: geometry plus all original fixed-grid attributes and attributed covariates.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_POLY,
            "QA KM_blocks polygons with Stage 4 Step 2 covariates",
        ))
        # Static table sink: one row per fixed place, with no polygon geometry duplication.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_LOOKUP,
            "PLACE_static_covariates lookup table (one row per BLOCK_ID)",
        ))
        # Dynamic table sink: independent dated geometric exposures, one row per PLACE x GEOM_YMD.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_TIMESTEP_LOOKUP,
            "PLACE_dynamic_geometry_covariates lookup (BLOCK_ID x GEOM_YMD)",
        ))
        # Union QA sink: single reconciliation row, not a cell-by-cell history.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_UNION_QA,
            "PLACE_union_overlap_QA summary table",
        ))

    # NAME CONVENTION: source fields already starting ASM_ retain their name; other fabric fields gain
    # this prefix.
    def _out_name(self, src_name):
        """Prefix non-ASM fields but avoid ASM_ASM_* double-prefixing."""
        return src_name if src_name.startswith("ASM_") else f"ASM_{src_name}"

    # Prefer BLOCK_ID as the fixed-grid join key, accepting PLACE_ID as a legacy-compatible alternative.
    def _best_key_field(self, layer):
        fields = layer.fields()
        for candidate in ["BLOCK_ID", "PLACE_ID"]:
            if fields.indexOf(candidate) != -1:
                return candidate
        return None

    # PREFLIGHT QA: reject null keys, repeated keys and absent/empty polygon geometry before any spatial
    # attribution.
    def _validate_fixed_place_geometry(self, layer, feedback):
        """Require one valid polygon geometry for every unique PLACE/BLOCK key."""
        key = self._best_key_field(layer)
        if key is None:
            raise QgsProcessingException(
                "KM_blocks must contain BLOCK_ID (preferred) or PLACE_ID."
            )

        # Using a set enforces one-to-one geometry-to-PLACE correspondence for later no-geometry joins.
        seen = set()
        missing_ids = 0
        duplicate_ids = 0
        empty_geometries = 0
        for feat in layer.getFeatures():
            value = feat[key]
            if value is None or str(value).strip() == "":
                missing_ids += 1
                continue
            skey = str(value)
            if skey in seen:
                duplicate_ids += 1
            else:
                seen.add(skey)
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                empty_geometries += 1

        # The diagnostic is emitted even on failed preflight to help identify the fault in the source
        # grid.
        feedback.pushInfo(
            f"[Stage 4 Step 2] KM_blocks preflight | key={key}; "
            f"features={layer.featureCount():,}; unique IDs={len(seen):,}; "
            f"missing IDs={missing_ids:,}; duplicates={duplicate_ids:,}; "
            f"empty geometries={empty_geometries:,}."
        )
        if missing_ids or duplicate_ids or empty_geometries:
            raise QgsProcessingException(
                "KM_blocks failed fixed-geometry QA. It must contain exactly one valid "
                "polygon for each non-null BLOCK_ID/PLACE_ID. Correct the geometry layer "
                "before Stage 4 covariate or risk-table construction."
            )
        if not seen:
            raise QgsProcessingException("KM_blocks contains no usable PLACE geometries.")
        return key, len(seen)

    # Chronological field discovery: return suffixed values ordered by numeric step rather than
    # alphabetically.
    def _sort_step_fields(self, names, prefix):
        pat = re.compile(rf"^{re.escape(prefix)}_(\d+)$", re.IGNORECASE)
        out = []
        for n in names:
            m = pat.match(n)
            if m:
                out.append((int(m.group(1)), n))
        return [n for _, n in sorted(out)]
    # Accept several historical field naming conventions while preserving preferred-prefix tie order.
    def _sort_step_fields_any(self, names, prefixes):
        """Return step-indexed fields for any accepted prefix, sorted by step then prefix order."""
        order = {p.upper(): i for i, p in enumerate(prefixes)}
        out = []
        for n in names:
            for p in prefixes:
                m = re.match(rf"^{re.escape(p)}_(\d+)$", n, re.IGNORECASE)
                if m:
                    out.append((int(m.group(1)), order[p.upper()], n))
                    break
        return [n for _, _, n in sorted(out)]


    # STATE NORMALISATION: convert raw ONTO_STATE_i labels into the three FRAF states or UNRESOLVED.
    @staticmethod
    def _canonical_state(value):
        if value is None:
            return "UNRESOLVED"
        v = str(value).strip().upper().replace("-", "_").replace(" ", "_")
        if v in {"ACTIVE_DOMAIN", "ACTIVE", "CHANNEL", "WATER", "ACTIVE_CHANNEL"}:
            return "ACTIVE_DOMAIN"
        # Current v6.4 behaviour maps the literal STABLE_ISLAND alias to DS; this is retained,
        # but differs from the v10.9 Assemblage History interpretation of an explicitly stable island as
        # SF.
        if v in {"DEPOSITIONAL_STORAGE", "STORAGE", "ISLAND", "BAR", "STABLE_ISLAND"}:
            return "DEPOSITIONAL_STORAGE"
        if v in {"STABILISED_FLOODPLAIN", "STABILIZED_FLOODPLAIN", "FLOODPLAIN", "STABLE_FLOODPLAIN", "INACTIVE_FLOODPLAIN"}:
            return "STABILISED_FLOODPLAIN"
        return "UNRESOLVED"

    # Merge every feature of a reference geometry layer for a single distance/containment target.
    def _combine_layer_geometry(self, layer, feedback=None, label="source"):
        """Safely combine a polygon/line layer into one geometry for distance tests."""
        if layer is None or not layer.isValid():
            return None
        # The input may contain many pieces; empty geometries are skipped rather than poisoning the
        # union.
        geoms = []
        try:
            fc = layer.featureCount()
        except Exception:
            fc = -1
        if feedback:
            feedback.pushInfo(f"[Stage 4 Step 2] Combining {label}: {layer.name()} | features={fc:,}")
        for i, feat in enumerate(layer.getFeatures()):
            g = feat.geometry()
            if g is None or g.isEmpty():
                continue
            geoms.append(QgsGeometry(g))
            if feedback and i > 0 and i % 5000 == 0:
                feedback.pushInfo(f"[Stage 4 Step 2]   read {i:,} geometries from {layer.name()}...")
        if not geoms:
            return None
        if len(geoms) == 1:
            return geoms[0]
        # Prefer GEOS unaryUnion; fall back to sequential combine when unary union fails.
        try:
            out = QgsGeometry.unaryUnion(geoms)
            if feedback:
                feedback.pushInfo(f"[Stage 4 Step 2] Combined {label}: unaryUnion complete ({len(geoms):,} geometries).")
            return out
        except Exception as e:
            if feedback:
                feedback.pushWarning(f"[Stage 4 Step 2] unaryUnion failed for {label}; falling back to iterative combine: {e}")
        out = None
        for i, g in enumerate(geoms):
            out = g if out is None else out.combine(g)
            if feedback and i > 0 and i % 1000 == 0:
                feedback.pushInfo(f"[Stage 4 Step 2]   iterative combine {i:,}/{len(geoms):,} for {label}...")
        return out

    # Use a guaranteed interior point for each polygon so reference distances are reproducible for
    # irregular cells.
    def _representative_geometry(self, geom):
        """Use a point-on-surface for polygon PLACE cells so distances match Stage 4 Step 3 behaviour."""
        if geom is None or geom.isEmpty():
            return None
        if geom.type() == QgsWkbTypes.PolygonGeometry:
            try:
                return geom.pointOnSurface()
            except Exception:
                return geom.centroid()
        return geom

    # Return distance and inside flag relative to a supplied polygon or line reference geometry.
    def _distance_covariates(self, place_point_geom, source_geom):
        if place_point_geom is None or place_point_geom.isEmpty() or source_geom is None or source_geom.isEmpty():
            return None, None
        # Containment/intersection has priority: a point inside a polygon is assigned zero distance.
        try:
            inside = 1 if source_geom.contains(place_point_geom) or source_geom.intersects(place_point_geom) else 0
        except Exception:
            inside = 0
        try:
            dist = float(place_point_geom.distance(source_geom))
        except Exception:
            dist = None
        if inside:
            dist = 0.0
        return dist, inside

    # Static distance classes use fixed metre-named bands, independent of channel-width-normalised
    # classes.
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

    # Approximate signed local centreline curvature using the circle through three spaced line points.
    def _line_measure_and_curvature(self, point_geom, line_geom, half_window, width):
        """Replicates the lightweight Stage 4 Step 3 centreline distance/curvature predictors."""
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
            # Distance along the line is truncated at line ends to avoid extrapolation beyond observed
            # geometry.
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
            # The cross-product sign defines bend orientation; multiplying by width yields dimensionless
            # curvature.
            cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            k = 2.0 * cross / (ab * bc * ac)
            k_scaled = k * width if width and width > 0 else k
            return dist, m, k_scaled
        except Exception:
            return dist, None, None


    # Safely convert numeric covariate values and preserve missing/non-finite values as missing.
    def _as_float(self, value, default=None):
        try:
            if value is None or value == "":
                return default
            out = float(value)
            return out if math.isfinite(out) else default
        except Exception:
            return default

    # Integer conversion is conservative for invalid or blank QGIS provider attributes.
    def _as_int(self, value, default=None):
        try:
            if value is None or value == "":
                return default
            return int(float(value))
        except Exception:
            return default

    # Read date-like fields with YYYYMMDD, separated YYYY-MM-DD, or year-only fallback to 1 January.
    def _date_from_text(self, value):
        if value is None:
            return None
        s = str(value)
        m = re.search(r"(?<!\d)((?:18|19|20)\d{2})(\d{2})(\d{2})(?!\d)", s)
        if m:
            return int(m.group(1) + m.group(2) + m.group(3))
        m = re.search(r"((?:18|19|20)\d{2})[_\- /](\d{1,2})[_\- /](\d{1,2})", s)
        if m:
            return int(f"{int(m.group(1)):04d}{int(m.group(2)):02d}{int(m.group(3)):02d}")
        m = re.search(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", s)
        return int(m.group(1)) * 10000 + 101 if m else None

    # Index observed channel geometry by date and union its polygon parts once per date.
    def _index_timestep_channels(self, layer, feedback):
        by_date = {}
        for feat in layer.getFeatures():
            ymd = self._as_int(feat["GEOM_YMD"], None) if layer.fields().indexFromName("GEOM_YMD") >= 0 else None
            if ymd is None:
                ymd = self._date_from_text(feat["GEOM_YEAR"]) if layer.fields().indexFromName("GEOM_YEAR") >= 0 else None
            if ymd is None:
                continue
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            by_date.setdefault(ymd, []).append(QgsGeometry(geom))
        out = {}
        # Per-date union avoids repeated geometry aggregation in the much larger PLACE loop.
        for ymd, geoms in by_date.items():
            try:
                geom = QgsGeometry.unaryUnion(geoms) if len(geoms) > 1 else geoms[0]
            except Exception:
                geom = geoms[0]
                for g in geoms[1:]:
                    try:
                        geom = geom.combine(g)
                    except Exception:
                        pass
            # The polygon boundary is precomputed for bank-distance measurements.
            try:
                boundary = geom.boundary()
            except Exception:
                boundary = None
            out[ymd] = {"geom": geom, "boundary": boundary}
        feedback.pushInfo(f"[Stage 4 Step 2] Indexed {len(out):,} timestep channel dates.")
        return out

    # Build a separate spatial index of individual centreline segments for each geometry date.
    def _index_timestep_segments(self, layer, feedback):
        by_date = {}
        for feat in layer.getFeatures():
            ymd = self._as_int(feat["GEOM_YMD"], None) if layer.fields().indexFromName("GEOM_YMD") >= 0 else None
            if ymd is None:
                continue
            entry = by_date.setdefault(ymd, {"index": QgsSpatialIndex(), "features": {}})
            entry["index"].addFeature(feat)
            entry["features"][feat.id()] = QgsFeature(feat)
        feedback.pushInfo(f"[Stage 4 Step 2] Indexed {len(by_date):,} timestep centreline dates.")
        return by_date

    # Search up to 12 nearby candidate segments and retain the one with the smallest exact distance.
    def _nearest_segment(self, point_geom, segment_entry):
        if point_geom is None or point_geom.isEmpty() or not segment_entry:
            return None, None
        # The index narrows candidate inspection; geometry distance, not only bounding-box rank, selects
        # the segment.
        try:
            point = point_geom.asPoint()
            ids = segment_entry["index"].nearestNeighbor(point, 12)
        except Exception:
            return None, None
        best = None
        best_dist = None
        for fid in ids:
            feat = segment_entry["features"].get(fid)
            if feat is None:
                continue
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            try:
                dist = float(point_geom.distance(geom))
            except Exception:
                continue
            if best_dist is None or dist < best_dist:
                best = feat
                best_dist = dist
        return best, best_dist

    # Read a centreline segment attribute only if the named field exists; otherwise return a default.
    def _feature_value(self, feat, name, default=None):
        if feat is None or feat.fields().indexFromName(name) < 0:
            return default
        value = feat[name]
        return default if value is None or value == "" else value

    # Compute one PLACE/date exposure record from a representative point and dated channel/segment pair.
    def _timestep_covariates(self, point_geom, channel_entry, segment_entry, half_mult, full_mult):
        # All requested output keys are initialised as NULL to preserve absent-support diagnostics.
        names = [
            "DIST_CHANNEL", "DIST_BANK", "BANK_SETBACK", "INSIDE_CHANNEL",
            "DIST_CL", "CL_MEASURE", "CURV_SIGNED", "CURV_ABS", "CURV_SCALED",
            "POINT_SIDE", "BANK_SIDE", "OUTER_BANK", "INNER_BANK",
            "LOCAL_HALF_WIDTH", "LOCAL_WIDTH", "REL_CHANNEL_POS",
            "NEAR_CHANNEL_HALF", "NEAR_CHANNEL_FULL", "NEAR_BANK_HALF", "NEAR_BANK_FULL",
            "OUTER_CURV_REACT_HALF", "OUTER_CURV_REACT_FULL",
            "INNER_CURV_STORAGE_HALF", "INNER_CURV_STORAGE_FULL",
            "OUTER_CURV_STORAGE_HALF", "OUTER_CURV_STORAGE_FULL",
            "GEOM_SEG_ID", "GEOM_SUPPORT",
        ]
        result = {name: None for name in names}
        # No dated channel polygon: record unavailable geometry rather than fabricating exposure
        # metrics.
        if point_geom is None or point_geom.isEmpty() or not channel_entry:
            result["GEOM_SUPPORT"] = 0
            return result

        channel_geom = channel_entry.get("geom")
        boundary = channel_entry.get("boundary")
        if channel_geom is None or channel_geom.isEmpty():
            result["GEOM_SUPPORT"] = 0
            return result
# An interior point has zero distance to channel polygon but may lie away from the bank boundary.

        try:
            inside = 1 if channel_geom.contains(point_geom) or channel_geom.intersects(point_geom) else 0
        except Exception:
            inside = 0
        try:
            dist_channel = float(point_geom.distance(channel_geom))
        except Exception:
            dist_channel = None
        if inside:
            dist_channel = 0.0
        try:
            dist_bank = float(point_geom.distance(boundary)) if boundary is not None and not boundary.isEmpty() else None
        except Exception:
            dist_bank = None
        bank_setback = 0.0 if inside else dist_channel

        # If a channel is mapped but no centreline segment is found, keep polygon distances and flag
        # lack of full support.
        seg, dist_cl = self._nearest_segment(point_geom, segment_entry)
        if seg is None:
            result.update({
                "DIST_CHANNEL": dist_channel, "DIST_BANK": dist_bank,
                "BANK_SETBACK": bank_setback, "INSIDE_CHANNEL": inside,
                "GEOM_SUPPORT": 0,
            })
            return result

        # Local centreline attributes come from the nearest dated segment: curvature, width, tangent and
        # chainage.
        curv_signed = self._as_float(self._feature_value(seg, "CURV_RAW"), None)
        curv_abs = self._as_float(self._feature_value(seg, "CURV_ABS"), None)
        curv_scaled = self._as_float(self._feature_value(seg, "CURV_SCL"), None)
        half_width = self._as_float(self._feature_value(seg, "HALF_WIDTH"), None)
        local_width = self._as_float(self._feature_value(seg, "LOCAL_WIDTH"), None)
        cl_measure = self._as_float(self._feature_value(seg, "MEASURE"), None)
        tan_x = self._as_float(self._feature_value(seg, "TAN_X"), None)
        tan_y = self._as_float(self._feature_value(seg, "TAN_Y"), None)
        center_x = self._as_float(self._feature_value(seg, "CENTER_X"), None)
        center_y = self._as_float(self._feature_value(seg, "CENTER_Y"), None)
        turn_side = str(self._feature_value(seg, "TURN_SIDE", "STRAIGHT")).upper()
        seg_id = self._feature_value(seg, "SEG_ID", None)

        # The signed tangent-to-point cross product locates the PLACE on the left or right of the
        # directed centreline.
        point_side = "AXIS"
        if None not in (tan_x, tan_y, center_x, center_y):
            p = point_geom.asPoint()
            cross = tan_x * (p.y() - center_y) - tan_y * (p.x() - center_x)
            tolerance = max(0.01, (local_width or 1.0) * 1e-5)
            if cross > tolerance:
                point_side = "LEFT"
            elif cross < -tolerance:
                point_side = "RIGHT"

        # INNER and OUTER require both the place side and the local turn side; straight reaches use
        # AXIS.
        bank_side = "UNRESOLVED"
        if point_side == "AXIS" or turn_side == "STRAIGHT":
            bank_side = "AXIS"
        elif point_side in ("LEFT", "RIGHT") and turn_side in ("LEFT", "RIGHT"):
            bank_side = "INNER" if point_side == turn_side else "OUTER"

        outer_bank = 1 if bank_side == "OUTER" else 0
        inner_bank = 1 if bank_side == "INNER" else 0
        # Relative channel position is defined only for points within the channel and where half-width
        # is positive.
        rel_pos = None
        if inside == 1 and dist_cl is not None and half_width is not None and half_width > 0:
            rel_pos = float(dist_cl) / float(half_width)

        # Two proximity bands are computed separately for channel setback (full width) and bank distance
        # (half width).
        near_channel_half = near_channel_full = near_bank_half = near_bank_full = None
        if local_width is not None and local_width > 0 and bank_setback is not None:
            near_channel_half = 1 if bank_setback <= half_mult * local_width else 0
            near_channel_full = 1 if bank_setback <= full_mult * local_width else 0
        if half_width is not None and half_width > 0 and dist_bank is not None:
            near_bank_half = 1 if dist_bank <= half_mult * half_width else 0
            near_bank_full = 1 if dist_bank <= full_mult * half_width else 0

        # Scaled absolute curvature is preferred; raw absolute curvature is used when scaling is
        # unavailable.
        # Prefer dimensionless curvature scaled by local channel width.
        # Fall back to raw absolute curvature only where local-width support is absent.
        exposure_mag = abs(curv_scaled) if curv_scaled is not None else curv_abs

        # Exposure terms are curvature magnitudes gated by geometric context, not transition event
        # labels.
        def exp_if(condition):
            return exposure_mag if condition and exposure_mag is not None else 0.0

        # Return the complete distance, bend-side and curvature-exposure vector with GEOM_SUPPORT=1.
        result.update({
            "DIST_CHANNEL": dist_channel,
            "DIST_BANK": dist_bank,
            "BANK_SETBACK": bank_setback,
            "INSIDE_CHANNEL": inside,
            "DIST_CL": dist_cl,
            "CL_MEASURE": cl_measure,
            "CURV_SIGNED": curv_signed,
            "CURV_ABS": curv_abs,
            "CURV_SCALED": curv_scaled,
            "POINT_SIDE": point_side,
            "BANK_SIDE": bank_side,
            "OUTER_BANK": outer_bank,
            "INNER_BANK": inner_bank,
            "LOCAL_HALF_WIDTH": half_width,
            "LOCAL_WIDTH": local_width,
            "REL_CHANNEL_POS": rel_pos,
            "NEAR_CHANNEL_HALF": near_channel_half,
            "NEAR_CHANNEL_FULL": near_channel_full,
            "NEAR_BANK_HALF": near_bank_half,
            "NEAR_BANK_FULL": near_bank_full,
            "OUTER_CURV_REACT_HALF": exp_if(inside == 0 and outer_bank == 1 and near_channel_half == 1),
            "OUTER_CURV_REACT_FULL": exp_if(inside == 0 and outer_bank == 1 and near_channel_full == 1),
            "INNER_CURV_STORAGE_HALF": exp_if(inside == 1 and inner_bank == 1 and near_bank_half == 1),
            "INNER_CURV_STORAGE_FULL": exp_if(inside == 1 and inner_bank == 1 and near_bank_full == 1),
            "OUTER_CURV_STORAGE_HALF": exp_if(inside == 1 and outer_bank == 1 and near_bank_half == 1),
            "OUTER_CURV_STORAGE_FULL": exp_if(inside == 1 and outer_bank == 1 and near_bank_full == 1),
            "GEOM_SEG_ID": str(seg_id) if seg_id is not None else None,
            "GEOM_SUPPORT": 1,
        })
        return result


    # MAIN WORKFLOW: validate input contracts -> discover fields -> build output schemas -> spatially
    # attribute PLACE records -> QA.
    def processAlgorithm(self, parameters, context, feedback):
        # Resolve the two mandatory layers from QGIS Processing parameters before allocating large
        # spatial indexes.
        asm = self.parameterAsVectorLayer(parameters, self.ASM, context)
        place = self.parameterAsVectorLayer(parameters, self.PLACE, context)

        # Historical union comparison uses the full, retrospective union of mapped Active Domain
        # polygons.
        calc_union_domain = self.parameterAsBool(parameters, self.CALC_UNION_DOMAIN, context)
        union_channel_layer = self.parameterAsVectorLayer(parameters, self.UNION_CHANNEL_LAYER, context)

        # Reference geometry switches are independent of the dated channel-geometry switch.
        calc_active = self.parameterAsBool(parameters, self.CALC_ACTIVE, context)
        calc_water = self.parameterAsBool(parameters, self.CALC_WATER, context)
        calc_centreline = self.parameterAsBool(parameters, self.CALC_CENTRELINE, context)
        calc_curvature = self.parameterAsBool(parameters, self.CALC_CURVATURE, context)
        active_layer = self.parameterAsVectorLayer(parameters, self.ACTIVE_LAYER, context)
        water_layer = self.parameterAsVectorLayer(parameters, self.WATER_LAYER, context)
        centreline_layer = self.parameterAsVectorLayer(parameters, self.CENTRELINE_LAYER, context)
        half_window = self.parameterAsDouble(parameters, self.CURV_WINDOW, context)
        channel_width = self.parameterAsDouble(parameters, self.CHANNEL_WIDTH, context)

        # Dated geometry is indexed by GEOM_YMD and never collapsed into the static PLACE row.
        calc_timestep_geom = self.parameterAsBool(parameters, self.CALC_TIMESTEP_GEOM, context)
        timestep_channels = self.parameterAsVectorLayer(parameters, self.TIMESTEP_CHANNELS, context)
        timestep_segments = self.parameterAsVectorLayer(parameters, self.TIMESTEP_SEGMENTS, context)
        near_half_mult = self.parameterAsDouble(parameters, self.NEAR_HALF_MULT, context)
        near_full_mult = self.parameterAsDouble(parameters, self.NEAR_FULL_MULT, context)
        mixed_state_min_frac = self.parameterAsDouble(parameters, self.MIXED_STATE_MIN_FRAC, context)

        # FATAL INPUT VALIDATION: prevent invalid layers and mismatched reference systems from
        # generating bogus distances.
        if asm is None or not asm.isValid():
            raise QgsProcessingException("Invalid direct Module 4a assemblage layer.")
        if place is None or not place.isValid():
            raise QgsProcessingException("Invalid KM_blocks / fixed PLACE geometry layer.")
        if asm.crs() != place.crs():
            raise QgsProcessingException(
                "CRS mismatch. Reproject one layer first so Module 4a and PLACE polygons use the same CRS."
            )
        # Union-area intersection is meaningful only with a valid union layer in the same CRS as the
        # fixed grid.
        if calc_union_domain:
            if union_channel_layer is None or not union_channel_layer.isValid():
                raise QgsProcessingException(
                    "Union-domain comparison is enabled but no valid dissolved union-channel polygon was supplied."
                )
            if union_channel_layer.crs() != place.crs():
                raise QgsProcessingException(
                    "CRS mismatch. Reproject the union-channel polygon to match KM_blocks before running Step 2."
                )
        # Check enabled reference geometries only; disabled options do not require their corresponding
        # layer.
        for label, enabled, lyr in [
            ("active-domain", calc_active, active_layer),
            ("water", calc_water, water_layer),
            ("centreline", calc_centreline, centreline_layer),
        ]:
            if enabled:
                if lyr is None or not lyr.isValid():
                    raise QgsProcessingException(f"{label} predictors enabled but no valid {label} layer was supplied.")
                if lyr.crs() != place.crs():
                    raise QgsProcessingException(f"CRS mismatch. Reproject the {label} layer to match the PLACE polygons first.")

        # Both dated inputs are compulsory when date-specific geometry is requested, including an exact
        # date-key field.
        if calc_timestep_geom:
            if timestep_channels is None or not timestep_channels.isValid():
                raise QgsProcessingException(
                    "Timestep geometry lookup enabled but no valid standardised channel polygon layer was supplied."
                )
            if timestep_segments is None or not timestep_segments.isValid():
                raise QgsProcessingException(
                    "Timestep geometry lookup enabled but no valid standardised centreline segment layer was supplied."
                )
            for label, lyr in [("timestep channels", timestep_channels), ("timestep segments", timestep_segments)]:
                if lyr.crs() != place.crs():
                    raise QgsProcessingException(f"CRS mismatch: {label} must match PLACE polygons.")
            for required, lyr in [("GEOM_YMD", timestep_channels), ("GEOM_YMD", timestep_segments)]:
                if lyr.fields().indexFromName(required) < 0:
                    raise QgsProcessingException(f"{lyr.name()} is missing required field {required}.")

        # Record input field names once; all later schema decisions refer to this original input
        # structure.
        asm_fields = asm.fields()
        place_fields = place.fields()
        asm_names = asm_fields.names()

        # Critically, KM_blocks has one row per place; PLACE_interval_long has multiple rows and must be
        # read elsewhere.
        # The PLACE input must be the static grid/KM_blocks layer, not the
        # PLACE_interval_long table. Collapsing interval rows here would destroy
        # transition-specific risk-set and event histories.
        if (place_fields.indexOf("tstart_yr") != -1 and
                place_fields.indexOf("tstop_yr") != -1):
            raise QgsProcessingException(
                "The PLACE input appears to be PLACE_interval_long. Supply the "
                "KM_blocks fixed polygon grid instead. Stage 4 Step 3 receives "
                "PLACE_interval_long separately and preserves interval-specific "
                "REACTIVATE/STORAGE/STABILISE event and risk-set fields."
            )

        # Legacy interval-only attributes found on KM_blocks are reported and excluded rather than taken
        # as predictors.
        interval_fields_present = [
            f for f in self.INTERVAL_ONLY_PLACE_FIELDS
            if place_fields.indexOf(f) != -1
        ]
        if interval_fields_present:
            feedback.pushWarning(
                "[Stage 4 Step 2] Interval-specific fields detected on the static PLACE "
                "layer and intentionally excluded from the lookup: "
                + ", ".join(interval_fields_present)
            )
        feedback.pushInfo(
            "[Stage 4 Step 2] Transition-specific event/risk fields are not generated or "
            "collapsed here; Stage 4 Step 3 reads them from PLACE_interval_long."
        )

        # Check the one-place/one-polygon invariant before retaining any spatial lookup result.
        place_id_field, place_id_count = self._validate_fixed_place_geometry(place, feedback)
        feedback.pushInfo(
            f"[Stage 4 Step 2] Authoritative fixed geometry accepted: {place_id_count:,} PLACE/BLOCK IDs."
        )

        # Find chronological EA class and observation-date fields, accommodating legacy aliases.
        ea_fields = self._sort_step_fields_any(
            asm_names, ["EA_Class", "EA", "CLASS"]
        )
        period_fields = self._sort_step_fields_any(
            asm_names, ["Period", "PeriodEnd", "END_DATE", "DATE"]
        )

        # Raw historical states/transitions are categorical values; this transfer selects dominant area
        # per timestep.
        # State/transition histories written by Module 4a v3 and related
        # scripts.  These are categorical, dominant-overlap transfers.
        state_history_fields = self._sort_step_fields_any(
            asm_names,
            ["ONTO_STATE", "ONTOLOGY_STATE", "DOMAIN_STATE", "STATE_ONTOLOGY", "STATE"],
        )
        transition_history_fields = self._sort_step_fields_any(
            asm_names,
            ["ONTO_TRANS", "ONTOLOGY_TRANS", "DOMAIN_TRANS", "STATE_TRANS"],
        )

        # ONTO_STATE_i is mandatory because the algorithm also computes per-step *area fractions*,
        # which cannot be reconstructed from the final assemblage class alone.
        raw_state_by_step = {}
        for name in asm_names:
            match = re.match(r"^ONTO_STATE_(\d+)$", name, re.IGNORECASE)
            if match:
                raw_state_by_step[int(match.group(1))] = name
        state_steps = sorted(raw_state_by_step)
        if not state_steps:
            raise QgsProcessingException(
                "Module 4a output contains no raw ONTO_STATE_i fields. Run Module 4a v10.0 or later; "
                "dominant states and state-area fractions cannot be reconstructed safely from final classes."
            )
        feedback.pushInfo(f"[Stage 4 Step 2] Raw ONTO_STATE_i timesteps available for area fractions: {len(state_steps)}")

        # Optional numeric step flags complement categorical histories so the following stage can form
        # lagged measures.
        # Per-step flags are numeric proportions after area-weighted transfer.
        # They allow Stage 4 Step 3 to build lagged active/storage/stabilisation histories
        # without relying only on a single dominant categorical cell.
        state_flag_fields = self._sort_step_fields_any(
            asm_names,
            [
                "ACTIVE_i",       # defensive: accepted if a script wrote this literal pattern
                "ACT",
                "ACTIVE",
                "ACTIVE_DOM",
                "STORAGE",
                "STAB_FP",
                "STABILISED_FP",
            ],
        )

        # Retain only the fields actually present on the chosen Module 4a output; absent optional
        # metrics are skipped.
        available_numeric = [f for f in self.NUMERIC_METRICS if asm_fields.indexOf(f) != -1]
        available_cat = [f for f in self.CATEGORICAL_BASE_FIELDS if asm_fields.indexOf(f) != -1]

        # Per-step binary/proportion fields are numeric.
        for f in state_flag_fields:
            if f not in available_numeric:
                available_numeric.append(f)

        # Append EA, date, state and transition histories to categorical transfer without duplicate
        # columns.
        # Add interval-history fields as dominant-overlap categorical transfers.
        for f in ea_fields + period_fields + state_history_fields + transition_history_fields:
            if f not in available_cat:
                available_cat.append(f)

        if not available_numeric and not available_cat:
            raise QgsProcessingException(
                "No recognised Module 4a fields found. Expected Module 4a metrics/classes (including active-domain/state fields) or EA_Class_i/Period_i history fields."
            )

        # Log which metrics and timestep columns can be attributed for audit of source-version
        # compatibility.
        feedback.pushInfo(f"[Stage 4 Step 2] Using ID field: {place_id_field}")
        feedback.pushInfo(f"[Stage 4 Step 2] Numeric metrics found: {available_numeric}")
        feedback.pushInfo(f"[Stage 4 Step 2] Static categorical fields found: {[f for f in available_cat if f not in ea_fields and f not in period_fields]}")
        feedback.pushInfo(f"[Stage 4 Step 2] EA_Class history fields transferred: {len(ea_fields)}")
        feedback.pushInfo(f"[Stage 4 Step 2] Period history fields transferred: {len(period_fields)}")
        feedback.pushInfo(f"[Stage 4 Step 2] State history fields transferred: {len(state_history_fields)}")
        feedback.pushInfo(f"[Stage 4 Step 2] Transition history fields transferred: {len(transition_history_fields)}")
        # Pass through baseline cohort membership only; these are fixed-place attributes, not interval
        # risk sets.
        # PLACE/BLOCK static pass-through fields retained in lookup output.
        passthrough_place_fields = [
            f for f in self.PLACE_LOOKUP_PASSTHROUGH_FIELDS
            if place_fields.indexOf(f) != -1
            and f not in [place_id_field, "PLACE_ID", "BLOCK_ID"]
        ]

        feedback.pushInfo(f"[Stage 4 Step 2] State numeric flag fields transferred: {len(state_flag_fields)}")
        feedback.pushInfo(f"[Stage 4 Step 2] PLACE lookup pass-through fields retained: {passthrough_place_fields}")

        # Combine static reference geometries once outside the PLACE loop; avoid repeated union at every
        # grid cell.
        active_geom = self._combine_layer_geometry(active_layer, feedback, "current active-domain") if calc_active else None
        water_geom = self._combine_layer_geometry(water_layer, feedback, "current water") if calc_water else None
        centreline_geom = self._combine_layer_geometry(centreline_layer, feedback, "current/reference centreline") if calc_centreline else None

        # The union polygon defines a nested spatial denominator for area comparisons only, never an
        # outcome mask.
        union_channel_geom = self._combine_layer_geometry(
            union_channel_layer, feedback, "union-channel domain"
        ) if calc_union_domain else None
        if calc_union_domain and (union_channel_geom is None or union_channel_geom.isEmpty()):
            raise QgsProcessingException(
                "The supplied union-channel layer contains no usable polygon geometry."
            )
        union_source_area_m2 = float(union_channel_geom.area()) if union_channel_geom is not None else None

        # Match channel and segment layers by their common GEOM_YMD values; unmatched dates are not
        # exported.
        timestep_channel_index = self._index_timestep_channels(timestep_channels, feedback) if calc_timestep_geom else {}
        timestep_segment_index = self._index_timestep_segments(timestep_segments, feedback) if calc_timestep_geom else {}
        timestep_dates = sorted(set(timestep_channel_index).intersection(timestep_segment_index))
        if calc_timestep_geom and not timestep_dates:
            raise QgsProcessingException(
                "No common GEOM_YMD values were found between timestep channels and centreline segments."
            )

        # OUTPUT SCHEMAS: keep polygon and no-geometry lookup columns in identical covariate order.
        # Output field schemas.
        # The QA polygon begins with the original KM_blocks field schema, preserving its geometry and
        # identifiers.
        poly_fields = QgsFields()
        for f in place_fields:
            poly_fields.append(f)

        # The static lookup uses text-valued IDs for provider compatibility; original numeric/static
        # attributes follow.
        lookup_fields = QgsFields()
        lookup_fields.append(QgsField(place_id_field, QVariant.String, len=80))
        if place_fields.indexOf("PLACE_ID") != -1 and place_id_field != "PLACE_ID":
            lookup_fields.append(QgsField("PLACE_ID", QVariant.String, len=80))
        if place_fields.indexOf("BLOCK_ID") != -1 and place_id_field != "BLOCK_ID":
            lookup_fields.append(QgsField("BLOCK_ID", QVariant.String, len=80))

        # Local helper prevents duplicate output field names when multiple source aliases yield the same
        # ASM_ prefix.
        def _append_unique(fields, qgs_field):
            if fields.indexOf(qgs_field.name()) < 0:
                fields.append(qgs_field)

        # Preserve selected static PLACE/BLOCK fields in the lookup table.
        # Use the source field definition so numeric/string types are retained.
        for f in passthrough_place_fields:
            _append_unique(lookup_fields, place_fields[place_fields.indexOf(f)])

        # All available numeric fabric metrics receive double-precision ASM_-prefixed output fields.
        for f in available_numeric:
            out = self._out_name(f)
            _append_unique(poly_fields, QgsField(out, QVariant.Double))
            _append_unique(lookup_fields, QgsField(out, QVariant.Double))

        # Unrestricted strings protect long ONTO_TRANS_SUM and other full-history text from silent
        # truncation.
        # Do not impose a fixed width on categorical/history text. Module 4a
        # summary fields such as ONTO_TRANS_SUM can legitimately exceed 1,000
        # characters. A hard width caused QGIS to reject complete PLACE rows.
        # Length 0 is unrestricted for GeoPackage and temporary QGIS sinks.
        for f in available_cat:
            out = self._out_name(f)
            _append_unique(poly_fields, QgsField(out, QVariant.String, len=0))
            _append_unique(lookup_fields, QgsField(out, QVariant.String, len=0))

        feedback.pushInfo(
            "[Stage 4 Step 2] Categorical/history outputs use unrestricted text width; "
            "GeoPackage output is recommended."
        )

        # Coverage diagnostics: intersection area, fraction of PLACE covered by assemblage polygons, and
        # match count.
        for name, typ in [
            ("ASM_OVERLAP", QVariant.Double),
            ("ASM_COV_FRAC", QVariant.Double),
            ("ASM_MATCH_N", QVariant.Int),
        ]:
            _append_unique(poly_fields, QgsField(name, typ))
            _append_unique(lookup_fields, QgsField(name, typ))

        # Nested-union diagnostics are STATIC: full cell area, inside/outside union area and boundary
        # indicators.
        # Static nested-domain weights used by the R full-area versus union-area
        # descriptive comparison. These fields contain no interval outcome information.
        for name, typ in [
            ("ASM_BLOCK_AREA_M2", QVariant.Double),
            ("ASM_UNION_OVERLAP_M2", QVariant.Double),
            ("ASM_UNION_FRAC", QVariant.Double),
            ("ASM_OUTSIDE_UNION_M2", QVariant.Double),
            ("ASM_UNION_CONTACT", QVariant.Int),
            ("ASM_UNION_BOUNDARY", QVariant.Int),
            ("ASM_UNION_CORE50", QVariant.Int),
        ]:
            _append_unique(poly_fields, QgsField(name, typ))
            _append_unique(lookup_fields, QgsField(name, typ))

        # Each timestep has four state-area fractions plus explicit sum, dominance and mixed-state
        # checks.
        # Per-timestep PLACE-area fractions. Uncovered PLACE area is included
        # in ASM_UNRESOLVED_FRAC_i, so aggregation QA is explicit.
        for step in state_steps:
            for name, typ in [
                (f"ASM_ACTIVE_FRAC_{step}", QVariant.Double),
                (f"ASM_STORAGE_FRAC_{step}", QVariant.Double),
                (f"ASM_STAB_FP_FRAC_{step}", QVariant.Double),
                (f"ASM_UNRESOLVED_FRAC_{step}", QVariant.Double),
                (f"ASM_STATE_SUM_FRAC_{step}", QVariant.Double),
                (f"ASM_STATE_MAX_FRAC_{step}", QVariant.Double),
                (f"ASM_STATE_MIXED_{step}", QVariant.Int),
            ]:
                _append_unique(poly_fields, QgsField(name, typ))
                _append_unique(lookup_fields, QgsField(name, typ))
        # Summary QA fields count mixed timesteps and departures from fraction conservation for each
        # PLACE.
        for name, typ in [
            ("ASM_TIMESTEP_N", QVariant.Int),
            ("ASM_MIXED_STEP_N", QVariant.Int),
            ("ASM_BADSUM_STEP_N", QVariant.Int),
            ("ASM_MAX_SUM_DEV", QVariant.Double),
        ]:
            _append_unique(poly_fields, QgsField(name, typ))
            _append_unique(lookup_fields, QgsField(name, typ))

        # The static geometric predictors here are snapshots; downstream forecast covariates must
        # respect origin dates.
        # Current/final spatial predictors required by Module 4d.
        # These are written to both outputs so either QA Place Poly or the
        # no-geometry lookup can be used downstream.
        for name, typ in [
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
        ]:
            _append_unique(poly_fields, QgsField(name, typ))
            _append_unique(lookup_fields, QgsField(name, typ))

        # The separate timestep schema is keyed by fixed PLACE ID and the dated geometry key GEOM_YMD.
        timestep_fields = QgsFields()
        timestep_fields.append(QgsField(place_id_field, QVariant.String, len=80))
        if place_fields.indexOf("PLACE_ID") != -1 and place_id_field != "PLACE_ID":
            timestep_fields.append(QgsField("PLACE_ID", QVariant.String, len=80))
        if place_fields.indexOf("BLOCK_ID") != -1 and place_id_field != "BLOCK_ID":
            timestep_fields.append(QgsField("BLOCK_ID", QVariant.String, len=80))
        # Geometry fields describe signed/absolute curvature, lateral side, local width and exposure
        # gating.
        for name, typ, length in [
            ("GEOM_YMD", QVariant.Int, 0), ("GEOM_YEAR", QVariant.Int, 0),
            ("DIST_CHANNEL", QVariant.Double, 0), ("DIST_BANK", QVariant.Double, 0),
            ("BANK_SETBACK", QVariant.Double, 0), ("INSIDE_CHANNEL", QVariant.Int, 0),
            ("DIST_CL", QVariant.Double, 0), ("CL_MEASURE", QVariant.Double, 0),
            ("CURV_SIGNED", QVariant.Double, 0), ("CURV_ABS", QVariant.Double, 0),
            ("CURV_SCALED", QVariant.Double, 0), ("POINT_SIDE", QVariant.String, 12),
            ("BANK_SIDE", QVariant.String, 16), ("OUTER_BANK", QVariant.Int, 0),
            ("INNER_BANK", QVariant.Int, 0), ("LOCAL_HALF_WIDTH", QVariant.Double, 0),
            ("LOCAL_WIDTH", QVariant.Double, 0), ("REL_CHANNEL_POS", QVariant.Double, 0),
            ("NEAR_CHANNEL_HALF", QVariant.Int, 0), ("NEAR_CHANNEL_FULL", QVariant.Int, 0),
            ("NEAR_BANK_HALF", QVariant.Int, 0), ("NEAR_BANK_FULL", QVariant.Int, 0),
            ("OUTER_CURV_REACT_HALF", QVariant.Double, 0),
            ("OUTER_CURV_REACT_FULL", QVariant.Double, 0),
            ("INNER_CURV_STORAGE_HALF", QVariant.Double, 0),
            ("INNER_CURV_STORAGE_FULL", QVariant.Double, 0),
            ("OUTER_CURV_STORAGE_HALF", QVariant.Double, 0),
            ("OUTER_CURV_STORAGE_FULL", QVariant.Double, 0),
            ("GEOM_SEG_ID", QVariant.String, 100), ("GEOM_SUPPORT", QVariant.Int, 0),
        ]:
            timestep_fields.append(QgsField(name, typ, len=length))

        # A single nonspatial row summarises area balance, union coverage and invalid percentage counts.
        union_qa_fields = QgsFields()
        for name, typ in [
            ("UNION_ENABLED", QVariant.Int),
            ("UNION_SOURCE_AREA_M2", QVariant.Double),
            ("BLOCK_COVERAGE_AREA_M2", QVariant.Double),
            ("SUM_BLOCK_UNION_OVERLAP_M2", QVariant.Double),
            ("AREA_DIFFERENCE_M2", QVariant.Double),
            ("RELATIVE_DIFFERENCE", QVariant.Double),
            ("BLOCKS_TOTAL", QVariant.Int),
            ("BLOCKS_FULLY_INSIDE", QVariant.Int),
            ("BLOCKS_BOUNDARY", QVariant.Int),
            ("BLOCKS_OUTSIDE", QVariant.Int),
            ("INVALID_FRACTIONS", QVariant.Int),
            ("MIN_UNION_FRAC", QVariant.Double),
            ("MAX_UNION_FRAC", QVariant.Double),
        ]:
            union_qa_fields.append(QgsField(name, typ))

        # Allocate all four QGIS sinks with explicit geometry types to prevent silent field/geometry
        # conflation.
        poly_sink, poly_dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_POLY, context, poly_fields, place.wkbType(), place.sourceCrs()
        )
        lookup_sink, lookup_dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_LOOKUP, context, lookup_fields, QgsWkbTypes.NoGeometry, place.sourceCrs()
        )
        timestep_sink, timestep_dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_TIMESTEP_LOOKUP, context,
            timestep_fields, QgsWkbTypes.NoGeometry, place.sourceCrs()
        )
        union_qa_sink, union_qa_dest_id = self.parameterAsSink(
            parameters, self.OUTPUT_UNION_QA, context,
            union_qa_fields, QgsWkbTypes.NoGeometry, place.sourceCrs()
        )
        # Fail immediately if a requested sink could not be created, before starting the expensive PLACE
        # iteration.
        if poly_sink is None:
            raise QgsProcessingException("Could not create QA polygon output sink.")
        if timestep_sink is None:
            raise QgsProcessingException("Could not create PLACE x timestep geometry lookup sink.")
        if lookup_sink is None:
            raise QgsProcessingException("Could not create PLACE lookup output sink.")
        if union_qa_sink is None:
            raise QgsProcessingException("Could not create union-domain QA output sink.")

        # Build a bounding-box index and a feature cache of the assemblage fabric for exact overlap
        # calculations.
        # Build ASM spatial index and cache.
        asm_index = QgsSpatialIndex()
        asm_cache = {}
        for af in asm.getFeatures():
            g = af.geometry()
            if g is None or g.isEmpty():
                continue
            asm_index.addFeature(af)
            asm_cache[af.id()] = QgsFeature(af)

        # Initialise counters for duplicate/missing keys, per-step state fractions and total
        # historical-union areas.
        total = place.featureCount()
        seen_ids = set()
        duplicate_id_count = 0
        missing_id_count = 0
        mixed_place_steps_total = 0
        badsum_place_steps_total = 0
        max_sum_deviation_global = 0.0

        # Union QA accumulates block areas and intersection areas independently of any ASM metric
        # transfer.
        block_coverage_area_m2 = 0.0
        sum_block_union_overlap_m2 = 0.0
        union_blocks_total = 0
        union_blocks_fully_inside = 0
        union_blocks_boundary = 0
        union_blocks_outside = 0
        union_invalid_fractions = 0
        union_frac_min = None
        union_frac_max = None

        # PRIMARY PLACE LOOP: one fixed polygon is the subject for static metrics and zero or more dated
        # records.
        for i, pf in enumerate(place.getFeatures()):
            # Cancellation checks are per place; processed portions may exist in output sinks after
            # interruption.
            if feedback.isCanceled():
                break
            if total and i % 100 == 0:
                feedback.setProgress(int(100 * i / total))

            # Read geometry and identifier before fetching candidate assemblage polygons.
            pgeom = pf.geometry()
            place_id = pf[place_id_field]
            place_id_valid = place_id is not None and str(place_id).strip() not in ("", "NULL")
            place_id_key = str(place_id) if place_id_valid else None
            if not place_id_valid:
                missing_id_count += 1

            # Numeric accumulation stores sum(value x overlap area); categorical accumulation stores
            # area by class.
            weighted = {m: 0.0 for m in available_numeric}
            cat_area = {c: {} for c in available_cat}
            # Store direct ONTO_STATE_i intersection areas separately from the categorical
            # dominant-overlap transfer.
            state_area = {
                step: {"ACTIVE_DOMAIN": 0.0, "DEPOSITIONAL_STORAGE": 0.0,
                       "STABILISED_FLOODPLAIN": 0.0, "UNRESOLVED": 0.0}
                for step in state_steps
            }
            overlap_total = 0.0
            match_n = 0

            # Spatial index returns bounding-box candidates only: confirm a true polygon intersection
            # and positive area.
            if pgeom is not None and not pgeom.isEmpty():
                for aid in asm_index.intersects(pgeom.boundingBox()):
                    af = asm_cache.get(aid)
                    if af is None:
                        continue
                    ageom = af.geometry()
                    if ageom is None or ageom.isEmpty() or not pgeom.intersects(ageom):
                        continue
                    inter = pgeom.intersection(ageom)
                    if inter is None or inter.isEmpty():
                        continue
                    a = inter.area()
                    if a <= 0:
                        continue

                    # Only positive intersected area contributes to numeric weights, categorical voting
                    # or state-area fractions.
                    overlap_total += a
                    match_n += 1

                    # Numeric NULL values contribute no numerator but the final mean still uses all
                    # nonzero ASM overlap;
                    # this is the preserved v6.4 treatment of partially missing numeric source
                    # attributes.
                    for m in available_numeric:
                        val = af[m]
                        if val is None or val == "":
                            continue
                        try:
                            weighted[m] += float(val) * a
                        except Exception:
                            pass

                    # Categorical tie-breaking follows dictionary encounter order; the maximum
                    # intersection-area total wins.
                    for c in available_cat:
                        val = af[c]
                        if val is None or str(val).strip() == "":
                            continue
                        sval = str(val)
                        cat_area[c][sval] = cat_area[c].get(sval, 0.0) + a

                    # Per-state area is based on each raw ONTO_STATE_i, not the cross-time
                    # PRIMARY_STATE.
                    for step in state_steps:
                        state_name = self._canonical_state(af[raw_state_by_step[step]])
                        state_area[step][state_name] += a

            # Normalise numeric accumulated values by total ASM overlap, *not* full PLACE area.
            metric_attrs = []
            for m in available_numeric:
                metric_attrs.append(weighted[m] / overlap_total if overlap_total > 0 else None)
            # Select the largest-area category separately for each categorical/history column.
            for c in available_cat:
                if cat_area[c]:
                    dominant = max(cat_area[c].items(), key=lambda kv: kv[1])[0]
                    metric_attrs.append(dominant)
                else:
                    metric_attrs.append(None)

            # ASM_COV_FRAC measures assemblage coverage of the full PLACE; uncovered remainder is not
            # fabricated evidence.
            cov_frac = None
            if pgeom is not None and not pgeom.isEmpty() and pgeom.area() > 0:
                cov_frac = overlap_total / pgeom.area()
            metric_attrs.extend([overlap_total, cov_frac, match_n])

            # Store the full PLACE area separately because union comparison and state fractions use that
            # denominator.
            place_area = pgeom.area() if pgeom is not None and not pgeom.isEmpty() else 0.0

            # Compute exact historical-union intersection per PLACE. The union may cross a cell
            # boundary.
            # Exact static overlap with the retrospective union-channel footprint.
            # The full analysis area and union-channel footprint are nested domains.
            union_overlap_m2 = None
            union_frac = None
            outside_union_m2 = None
            union_contact = None
            union_boundary = None
            union_core50 = None
            # The expensive exact intersection runs only with CALC_UNION_DOMAIN enabled.
            if calc_union_domain:
                union_blocks_total += 1
                block_coverage_area_m2 += place_area
                union_overlap_m2 = 0.0
                if (place_area > 0 and pgeom is not None and not pgeom.isEmpty() and
                        union_channel_geom is not None and not union_channel_geom.isEmpty()):
                    try:
                        if pgeom.intersects(union_channel_geom):
                            union_intersection = pgeom.intersection(union_channel_geom)
                            if union_intersection is not None and not union_intersection.isEmpty():
                                union_overlap_m2 = max(0.0, float(union_intersection.area()))
                    except Exception as exc:
                        feedback.pushWarning(
                            f"[Stage 4 Step 2] Union intersection failed for {place_id_field}={place_id}: {exc}"
                        )
                        union_overlap_m2 = 0.0

                # Cap tiny numerical overflows at the actual block area before calculating union
                # fractions.
                # Clamp geometry precision artefacts to the fixed block area.
                if place_area > 0:
                    union_overlap_m2 = min(max(union_overlap_m2, 0.0), place_area)
                    union_frac = union_overlap_m2 / place_area
                    outside_union_m2 = max(0.0, place_area - union_overlap_m2)
                    # A boundary cell overlaps both the historical union and its exterior above a small
                    # area tolerance.
                    tolerance = max(1.0e-6, place_area * 1.0e-9)
                    union_contact = 1 if union_overlap_m2 > tolerance else 0
                    union_boundary = 1 if (union_overlap_m2 > tolerance and outside_union_m2 > tolerance) else 0
                    union_core50 = 1 if union_frac >= 0.5 else 0
                    if union_frac < -1.0e-9 or union_frac > 1.0 + 1.0e-9:
                        union_invalid_fractions += 1
                    union_frac_min = union_frac if union_frac_min is None else min(union_frac_min, union_frac)
                    union_frac_max = union_frac if union_frac_max is None else max(union_frac_max, union_frac)
                    # Count full-inside / boundary / outside cells for the single-row union
                    # reconciliation.
                    if union_boundary == 1:
                        union_blocks_boundary += 1
                    elif union_contact == 1:
                        union_blocks_fully_inside += 1
                    else:
                        union_blocks_outside += 1
                else:
                    union_invalid_fractions += 1
                sum_block_union_overlap_m2 += union_overlap_m2 or 0.0

            # Append union variables in the same order as the schema fields added above.
            # Field order must match the union fields appended after ASM_MATCH_N.
            metric_attrs.extend([
                place_area if place_area > 0 else None,
                union_overlap_m2, union_frac, outside_union_m2,
                union_contact, union_boundary, union_core50,
            ])

            # Reconstruct how much of this PLACE belonged to each geomorphic state at each observation
            # step.
            state_fraction_attrs = []
            mixed_steps = 0
            badsum_steps = 0
            max_sum_dev = 0.0
            # Unlike numeric ASM means, these fractions divide by FULL cell area, making uncovered area
            # unresolved.
            for step in state_steps:
                denom = place_area if place_area > 0 else None
                active_frac = state_area[step]["ACTIVE_DOMAIN"] / denom if denom else None
                storage_frac = state_area[step]["DEPOSITIONAL_STORAGE"] / denom if denom else None
                stab_frac = state_area[step]["STABILISED_FLOODPLAIN"] / denom if denom else None
                # Residual area is explicitly unresolved; overlapping source polygons can still generate
                # >1 totals and QA flags.
                if denom:
                    unresolved_frac = max(0.0, 1.0 - (active_frac + storage_frac + stab_frac))
                    sum_frac = active_frac + storage_frac + stab_frac + unresolved_frac
                    max_frac = max(active_frac, storage_frac, stab_frac, unresolved_frac)
                    # Mixed-state indicator requires at least two AD/DS/SF fractions at or above the
                    # user threshold.
                    mixed = 1 if sum(x >= mixed_state_min_frac for x in [active_frac, storage_frac, stab_frac]) >= 2 else 0
                    sum_dev = abs(sum_frac - 1.0)
                else:
                    unresolved_frac = sum_frac = max_frac = None
                    mixed = 0
                    sum_dev = 1.0
                # Count problematic timesteps and track the worst fraction-sum error for diagnostics.
                if mixed:
                    mixed_steps += 1
                if sum_dev > 1e-6:
                    badsum_steps += 1
                max_sum_dev = max(max_sum_dev, sum_dev)
                state_fraction_attrs.extend([
                    active_frac, storage_frac, stab_frac, unresolved_frac,
                    sum_frac, max_frac, mixed,
                ])
            state_fraction_attrs.extend([len(state_steps), mixed_steps, badsum_steps, max_sum_dev])
            metric_attrs.extend(state_fraction_attrs)
            mixed_place_steps_total += mixed_steps
            badsum_place_steps_total += badsum_steps
            max_sum_deviation_global = max(max_sum_deviation_global, max_sum_dev)

            # A stable point-on-surface supplies the reference location for all current and dated
            # geometry distances.
            ppoint = self._representative_geometry(pgeom)

            # DYNAMIC ROWS: for every matched geometry date, calculate and insert one non-spatial PLACE
            # x GEOM_YMD record.
            if calc_timestep_geom and place_id_key is not None:
                for geom_ymd in timestep_dates:
                    # Distance, curvature and bank-side terms are computed from that date only, not from
                    # a union of years.
                    cov = self._timestep_covariates(
                        ppoint,
                        timestep_channel_index.get(geom_ymd),
                        timestep_segment_index.get(geom_ymd),
                        near_half_mult,
                        near_full_mult,
                    )
                    # PLACE identifiers are written before the date-specific covariate vector in the
                    # declared schema order.
                    row = [str(place_id)]
                    if place_fields.indexOf("PLACE_ID") != -1 and place_id_field != "PLACE_ID":
                        row.append(str(pf["PLACE_ID"]))
                    if place_fields.indexOf("BLOCK_ID") != -1 and place_id_field != "BLOCK_ID":
                        row.append(str(pf["BLOCK_ID"]))
                    row.extend([
                        geom_ymd, int(geom_ymd // 10000),
                        cov["DIST_CHANNEL"], cov["DIST_BANK"], cov["BANK_SETBACK"], cov["INSIDE_CHANNEL"],
                        cov["DIST_CL"], cov["CL_MEASURE"], cov["CURV_SIGNED"], cov["CURV_ABS"],
                        cov["CURV_SCALED"], cov["POINT_SIDE"], cov["BANK_SIDE"], cov["OUTER_BANK"],
                        cov["INNER_BANK"], cov["LOCAL_HALF_WIDTH"], cov["LOCAL_WIDTH"], cov["REL_CHANNEL_POS"],
                        cov["NEAR_CHANNEL_HALF"], cov["NEAR_CHANNEL_FULL"], cov["NEAR_BANK_HALF"], cov["NEAR_BANK_FULL"],
                        cov["OUTER_CURV_REACT_HALF"], cov["OUTER_CURV_REACT_FULL"],
                        cov["INNER_CURV_STORAGE_HALF"], cov["INNER_CURV_STORAGE_FULL"],
                        cov["OUTER_CURV_STORAGE_HALF"], cov["OUTER_CURV_STORAGE_FULL"],
                        cov["GEOM_SEG_ID"], cov["GEOM_SUPPORT"],
                    ])
                    # Checking every addFeature call is essential: output sinks may reject long fields
                    # or provider types.
                    timestep_feat = QgsFeature(timestep_fields)
                    timestep_feat.setAttributes(row)
                    if not timestep_sink.addFeature(timestep_feat, QgsFeatureSink.FastInsert):
                        raise QgsProcessingException(
                            f"Could not write timestep-covariate row for {place_id_field}={place_id}; "
                            "use a GeoPackage or temporary output and inspect field/provider limits."
                        )

            # REFERENCE SNAPSHOT ATTRIBUTION: active and water distances are independent optional
            # inputs.
            active_dist = active_inside = None
            if calc_active:
                active_dist, active_inside = self._distance_covariates(ppoint, active_geom)

            water_dist = water_inside = None
            if calc_water:
                water_dist, water_inside = self._distance_covariates(ppoint, water_geom)

            # Distance to reference centreline and local scaled curvature are derived from the same
            # PLACE point.
            cl_dist = cl_measure = curv = curv_erosion = dist_x_curv = None
            if calc_centreline:
                if calc_curvature:
                    cl_dist, cl_measure, curv = self._line_measure_and_curvature(ppoint, centreline_geom, half_window, channel_width)
                else:
                    cl_dist, _inside = self._distance_covariates(ppoint, centreline_geom)
                curv_erosion = curv
                if cl_dist is not None and curv_erosion is not None:
                    dist_x_curv = (float(cl_dist) / 1000.0) * float(curv_erosion)

            # Append the requested reference-distance bins and curvature interaction to both static
            # output forms.
            spatial_attrs = [
                active_dist,
                active_inside,
                self._bin_distance(active_dist),
                self._bin_distance(active_dist),
                water_dist,
                water_inside,
                self._bin_distance(water_dist),
                self._bin_distance(water_dist),
                cl_dist,
                self._bin_distance(cl_dist),
                cl_measure,
                curv,
                curv_erosion,
                dist_x_curv,
            ]
            metric_attrs_with_spatial = metric_attrs + spatial_attrs

            # Write QA polygons with their original attributes followed by all newly constructed
            # covariates.
            poly_feat = QgsFeature(poly_fields)
            poly_feat.setGeometry(pgeom)
            poly_feat.setAttributes(pf.attributes() + metric_attrs_with_spatial)
            if not poly_sink.addFeature(poly_feat, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(
                    f"Could not write QA polygon for {place_id_field}={place_id}; "
                    "use a GeoPackage or temporary output and inspect field/provider limits."
                )

            # Static lookup emits one row per unique PLACE; input geometry should already have passed
            # uniqueness QA.
            if place_id_key is not None and place_id_key not in seen_ids:
                seen_ids.add(place_id_key)
                lookup_attrs = [str(place_id)]
                if place_fields.indexOf("PLACE_ID") != -1 and place_id_field != "PLACE_ID":
                    lookup_attrs.append(str(pf["PLACE_ID"]))
                if place_fields.indexOf("BLOCK_ID") != -1 and place_id_field != "BLOCK_ID":
                    lookup_attrs.append(str(pf["BLOCK_ID"]))
                # Only baseline cohort fields are copied verbatim; longitudinal outcomes remain with
                # Stage 4 Step 3.
                for f in passthrough_place_fields:
                    lookup_attrs.append(pf[f])
                lookup_attrs.extend(metric_attrs_with_spatial)
                lookup_feat = QgsFeature(lookup_fields)
                lookup_feat.setAttributes(lookup_attrs)
                if not lookup_sink.addFeature(lookup_feat, QgsFeatureSink.FastInsert):
                    raise QgsProcessingException(
                        f"Could not write static-covariate lookup row for {place_id_field}={place_id}; "
                        "use a GeoPackage or temporary output and inspect field/provider limits."
                    )
            elif place_id_key is not None:
                duplicate_id_count += 1

        # Post-loop diagnostics catch unexpected empty or duplicate PLACE IDs, even though preflight
        # should reject them.
        if missing_id_count:
            feedback.pushWarning(
                f"[Stage 4 Step 2] {missing_id_count:,} PLACE features had a null/blank "
                "PLACE_ID/BLOCK_ID and were omitted from the no-geometry lookup."
            )
        if duplicate_id_count:
            feedback.pushWarning(
                f"[Stage 4 Step 2] {duplicate_id_count:,} duplicate PLACE_ID/BLOCK_ID features were encountered unexpectedly."
            )

        # Compare union polygon area to sum of exact PLACE intersections; equality requires matching
        # analysis extent.
        union_area_difference_m2 = None
        union_relative_difference = None
        if calc_union_domain and union_source_area_m2 is not None:
            union_area_difference_m2 = sum_block_union_overlap_m2 - union_source_area_m2
            union_relative_difference = (
                union_area_difference_m2 / union_source_area_m2
                if union_source_area_m2 > 0 else None
            )

        # Create one feature with reconciliation totals, overlap proportions and within/boundary/outside
        # cell counts.
        union_qa_feat = QgsFeature(union_qa_fields)
        union_qa_feat.setAttributes([
            1 if calc_union_domain else 0,
            union_source_area_m2,
            block_coverage_area_m2 if calc_union_domain else None,
            sum_block_union_overlap_m2 if calc_union_domain else None,
            union_area_difference_m2,
            union_relative_difference,
            union_blocks_total if calc_union_domain else 0,
            union_blocks_fully_inside if calc_union_domain else 0,
            union_blocks_boundary if calc_union_domain else 0,
            union_blocks_outside if calc_union_domain else 0,
            union_invalid_fractions if calc_union_domain else 0,
            union_frac_min, union_frac_max,
        ])
        if not union_qa_sink.addFeature(union_qa_feat, QgsFeatureSink.FastInsert):
            raise QgsProcessingException("Could not write union-domain QA summary row.")

        # Union QA distinguishes geometrical mismatch warnings from impossible fractions, which cause a
        # fatal error.
        if calc_union_domain:
            feedback.pushInfo(
                "[Stage 4 Step 2] Union-domain QA | "
                f"source area={union_source_area_m2:,.3f} m²; "
                f"summed block overlap={sum_block_union_overlap_m2:,.3f} m²; "
                f"relative difference={union_relative_difference:.6g}; "
                f"blocks full/boundary/outside={union_blocks_fully_inside:,}/"
                f"{union_blocks_boundary:,}/{union_blocks_outside:,}; "
                f"invalid fractions={union_invalid_fractions:,}."
            )
            if union_invalid_fractions:
                raise QgsProcessingException(
                    "Union-domain QA failed: invalid block areas or overlap fractions were detected."
                )
            # Large area discrepancies are warned, not silently corrected; common cause is a union
            # extending outside the grid.
            if union_relative_difference is not None and abs(union_relative_difference) > 0.01:
                feedback.pushWarning(
                    "[Stage 4 Step 2] The union polygon area differs from the sum of block overlaps by more than 1%. "
                    "Confirm that the union polygon is clipped to the same analysis envelope and that KM_blocks cover it without gaps."
                )

        # Final diagnostic reports what was attributed; risk tables and origin-specific predictors are
        # built downstream.
        feedback.pushInfo(
            "[Stage 4 Step 2] Finished static Module 4a lookup, per-timestep PLACE state-area fractions, "
            "and separate PLACE x timestep channel-geometry lookup."
        )
        feedback.pushInfo(
            f"[Stage 4 Step 2] State aggregation QA | timesteps={len(state_steps)}; "
            f"mixed PLACE×timesteps={mixed_place_steps_total:,}; "
            f"fraction-sum failures={badsum_place_steps_total:,}; "
            f"maximum sum deviation={max_sum_deviation_global:.3g}."
        )
        if badsum_place_steps_total:
            feedback.pushWarning(
                "[Stage 4 Step 2] Some state fractions do not sum to one within tolerance. Inspect overlap/sliver QA before modelling."
            )
        # Return all four Processing sink IDs unchanged, so existing QGIS models can resolve the
        # outputs.
        return {
            self.OUTPUT_POLY: poly_dest_id,
            self.OUTPUT_LOOKUP: lookup_dest_id,
            self.OUTPUT_TIMESTEP_LOOKUP: timestep_dest_id,
            self.OUTPUT_UNION_QA: union_qa_dest_id,
        }
