# -*- coding: utf-8 -*-
"""
FRAF / SCS — Assemblage Surface Age + State Mapper v3.4 (publication)
======================================================================

Purpose
-------
Creates publication-ready surface-age and state fields from the current
Module 4a assemblage output.

This consolidated publication version supersedes the separate v3.2 publication
and v3.2 5-year-class mappers. Exact observed ages are binned at 5-year
intervals through 35 years, while inherited T0 surfaces remain left-censored
and are never assigned an exact age.

v3.4 SURFACE-CONTINUITY PUBLICATION VERSION
---------------------
Module 4a v10.9+ is authoritative for reconstructed state and T0 provenance:
    FINAL_ONTO_STATE / FINAL_STATE_CORR
    INIT_STATE / LEFT_CENS
    SINCE_DISTURB_YR

For publication SURFACE_AGE, however, this mapper deliberately does NOT use
Module 4a SURFACE_AGE_EST as a formation age. In v10.9 SURFACE_AGE_EST is an
alias of SINCE_DISTURB_YR and therefore resets after any mapped erosion or
deposition disturbance. That is a disturbance-persistence metric, not the age
of a continuously preserved geomorphic surface.

Publication surface age follows surface continuity:
    * Active-domain / erosion occupation destroys the previous surface and resets age.
    * The current surface begins with the first non-active surface evidence after
      the LAST active/erosional reset.
    * Later deposition or island_deposition on an already non-active surface is
      reworking and does NOT reset surface age unless Active Domain intervenes.
    * stable_island <-> stable_floodplain is a state/context change within the
      same preserved surface and never resets surface age.
    * A non-active surface already present at T0 remains left-censored until an
      observed Active-Domain reset occurs.

Thus SURFACE_AGE and SINCE_DISTURB_YR intentionally differ where an old surface
has experienced later depositional reworking.

Publication interpretation
--------------------------
SURFACE_AGE
    Exact observed age of the current non-active surface. NULL for active,
    left-censored and unresolved surfaces.

AGE_MIN_YR
    Minimum observed persistence for left-censored surfaces. It is NOT mixed
    with exact SURFACE_AGE in publication age statistics.

AGE_CENSORED
    1 where the current non-active surface predates the mapped formation record.

AGE_STATUS
    Exact observed age / Left-censored / Active Domain / Age unresolved.

SURFACE_MAP_CLASS
    Publication figure category. Left-censored pre-observation surfaces have
    their own class and are not placed in an exact numerical age bin.

Compatibility fields
--------------------
FIRST_SURF_YEAR
LAST_RESET_YEAR
CURR_SURF_YEAR

These are retained for QA/legacy downstream use. CURR_SURF_YEAR is populated
only where an observed surface-forming event can be identified.

Recommended input
-----------------
Module 4a v10.9+ Assemblage_Units_FULL_ATTRS (or a layer retaining the
state/T0 provenance fields and complete EA_Class_i / Period_i chronology).
"""

# [FRAF-P2-DOC] FRAF PAPER 2 SOURCE ARCHIVE | PUBLICATION-SUPPORT SCRIPT (PUB).
# [FRAF-P2-DOC] Archive filename: FRAF_P2_PUB_SurfaceAgeStateMapper_v3_4.py.
# [FRAF-P2-DOC] Source lineage: FRAF Assemblage Surface Age + State Mapper v3.4,
# [FRAF-P2-DOC] publication surface-continuity variant, for QGIS Processing.
# [FRAF-P2-DOC] This archival revision adds comments only. The algorithm identifier,
# [FRAF-P2-DOC] processing parameters, field names, classifications and calculations
# [FRAF-P2-DOC] remain those of the unmodified v3.4 source.
# [FRAF-P2-DOC] WORKFLOW: Module 4a v10.9+ Assemblage_Units_FULL_ATTRS -> this
# [FRAF-P2-DOC] publication mapper -> classified surface-age polygons / age maps.
# [FRAF-P2-DOC] This is NOT the Module 4b Dated Chronicle, the separate Module 4d
# [FRAF-P2-DOC] assemblage-metrics workflow, or a Cox-model risk-table generator.
# [FRAF-P2-DOC] Required source history: paired EA_Class_i / Period_i plus a usable
# [FRAF-P2-DOC] final organisational state; INIT_STATE and LEFT_CENS are essential
# [FRAF-P2-DOC] for confident identification of inherited T0 surfaces.
# [FRAF-P2-DOC] Ontology: Active Domain (AD), Depositional Storage (DS), Stabilised
# [FRAF-P2-DOC] Floodplain (SF). Descriptive recent/reworked/persistent labels are
# [FRAF-P2-DOC] conditions of surfaces, not additional organisational states.
# [FRAF-P2-DOC] SURFACE_AGE = observed continuous surface persistence since origin
# [FRAF-P2-DOC] or the last mapped Active-Domain/erosional reset. Later deposition
# [FRAF-P2-DOC] on a preserved non-active surface is not itself a surface-age reset.
# [FRAF-P2-DOC] SINCE_DISTURB_YR measures a different quantity: time since the last
# [FRAF-P2-DOC] mapped disturbance, which may include deposition; do not substitute
# [FRAF-P2-DOC] it for the exact age of the continuously preserved surface.
# [FRAF-P2-DOC] Inherited surfaces without an observed formation event are left-censored:
# [FRAF-P2-DOC] SURFACE_AGE is null and AGE_MIN_YR is only a lower bound.
# [FRAF-P2-DOC] The mapper neither reconstructs Module 4a history nor calculates
# [FRAF-P2-DOC] area-weighted age statistics; those require separate analysis.
# [FRAF-P2-DOC] Only planar input geometry is copied to the output; this tool does
# [FRAF-P2-DOC] not alter polygon geometry, spatial support or underlying chronology.
# [FRAF-P2-DOC] REPRODUCIBILITY: record the supplied FINAL_YEAR and MAX_STEPS values.
# [FRAF-P2-DOC] The default FINAL_YEAR=2024 suits neither every river nor every run;
# [FRAF-P2-DOC] for the Mamore 1984-2025 chronology use FINAL_YEAR=2025.
# [FRAF-P2-DOC] Limitation: event dates are reduced to integer years. Within-year
# [FRAF-P2-DOC] ordering, ambiguous EA labels and incomplete T0 provenance can affect
# [FRAF-P2-DOC] the inferred age origin. A syntax check is not a QGIS runtime test.
import re
import math

# [FRAF-P2-DOC] QGIS Processing API imports: execution requires QGIS Python, not standalone Python.
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFields,
    QgsField,
    QgsFeature,
)


# [FRAF-P2-DOC] QGIS-facing algorithm. Method names below are required plugin hooks;
# [FRAF-P2-DOC] their implementation and registration IDs are preserved for compatibility.
class FRAFAssemblageSurfaceAgeStateMapperV34(QgsProcessingAlgorithm):

    # [FRAF-P2-DOC] Stable Processing parameter/output keys; changing these would break saved
    # [FRAF-P2-DOC] QGIS processing models and scripts that call the existing algorithm.
    INPUT = "INPUT"
    FINAL_YEAR = "FINAL_YEAR"
    MAX_STEPS = "MAX_STEPS"
    PERSISTENCE_YEARS = "PERSISTENCE_YEARS"
    REWORKED_EPISODES = "REWORKED_EPISODES"
    EPISODE_FIELD = "EPISODE_FIELD"
    FINAL_STATE_FIELD = "FINAL_STATE_FIELD"
    OUTPUT = "OUTPUT"

    # [FRAF-P2-DOC] Canonical derived publication schema. Existing fields with these exact
    # [FRAF-P2-DOC] names are populated with newly calculated values, not simply retained.
    # [FRAF-P2-DOC] Other Module 4a attributes, including complete histories, pass through.
    NEW_FIELDS = [
        "FIRST_SURF_YEAR",
        "LAST_RESET_YEAR",
        "CURR_SURF_YEAR",
        "SURFACE_AGE",
        "AGE_MIN_YR",
        "AGE_CENSORED",
        "AGE_STATUS",
        "AGE_CLASS",
        "SURFACE_MAP_CLASS",
        "SURFACE_MAP_ORDER",
        "CORE_STATE",
        "FP_CONDITION",
        "FINAL_STATE_USED",
        "PERSISTENT_FP",
        "REWORKED_FP",
        "RECENT_FP",
        "AGE_SOURCE",
        "AGE_NOTE",
        "SINCE_DISTURB_YR",
    ]

    # [FRAF-P2-DOC] Translate visible labels through the QGIS application translation domain.
    def tr(self, string):
        return QCoreApplication.translate("FRAF", string)

    # [FRAF-P2-DOC] Preserve the original Processing algorithm ID across archive renaming.
    def name(self):
        return "fraf_assemblage_surface_age_state_mapper_v3_4_publication"

    # [FRAF-P2-DOC] The version-specific display label appears in the QGIS Processing Toolbox.
    def displayName(self):
        return "FRAF — Assemblage Surface Age + State Mapper v3.4 (publication; surface continuity; 5-year classes)"

    # [FRAF-P2-DOC] QGIS group caption for the publication mapper.
    def group(self):
        return "FRAF / SCS Toolbox"

    # [FRAF-P2-DOC] Stable toolbox group identifier for model/script references.
    def groupId(self):
        return "fraf_scs"

    # [FRAF-P2-DOC] Processing uses a fresh instance when invoking the algorithm.
    def createInstance(self):
        return FRAFAssemblageSurfaceAgeStateMapperV34()

    # [FRAF-P2-DOC] Help describes the scientific distinction between surface age and
    # [FRAF-P2-DOC] elapsed time since mapped erosion/deposition disturbance.
    def shortHelpString(self):
        return self.tr(
            "Publication mapper aligned with Module 4a v10.9+ state/T0 provenance. "
            "Surface age is derived from continuity since the last Active-Domain/erosion reset; "
            "later deposition on an already non-active surface does not reset surface age. "
            "SINCE_DISTURB_YR is retained separately. Exact ages use 5-year classes through "
            "35 years; T0 inherited surfaces remain left-censored."
        )

    # [FRAF-P2-DOC] Declare the user-facing inputs and destination; these are kept
    # [FRAF-P2-DOC] unchanged to preserve existing QGIS processing configurations.
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT,
            "Module 4a assemblage polygon layer",
            [QgsProcessing.TypeVectorPolygon]
        ))
        # [FRAF-P2-DOC] IMPORTANT: Despite the original parameter label saying compatibility
        # [FRAF-P2-DOC] fields only, FINAL_YEAR also enters the exact age arithmetic below
        # [FRAF-P2-DOC] (FINAL_YEAR - CURR_SURF_YEAR) and the fallback minimum-age calculation.
        # [FRAF-P2-DOC] Supply the last observation year explicitly (Mamoré 2025; Jamuna 2024).
        self.addParameter(QgsProcessingParameterNumber(
            self.FINAL_YEAR,
            "Final observation year (used for compatibility year fields only)",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=2024
        ))
        # [FRAF-P2-DOC] Scan no more than MAX_STEPS chronological EA_Class_i / Period_i pairs.
        # [FRAF-P2-DOC] A value smaller than the full observed record silently omits later steps.
        self.addParameter(QgsProcessingParameterNumber(
            self.MAX_STEPS,
            "Maximum number of EA_Class_i / Period_i fields to scan",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=60,
            minValue=1
        ))
        # [FRAF-P2-DOC] Twenty years is a descriptive persistent-floodplain condition threshold;
        # [FRAF-P2-DOC] it does not reassign the authoritative AD/DS/SF final state.
        self.addParameter(QgsProcessingParameterNumber(
            self.PERSISTENCE_YEARS,
            "Persistent Floodplain descriptive threshold (years)",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=20,
            minValue=1
        ))
        # [FRAF-P2-DOC] Episode-count threshold separates descriptive Reworked Floodplain from
        # [FRAF-P2-DOC] other SF conditions; it does not gate a DS-to-SF state transition.
        self.addParameter(QgsProcessingParameterNumber(
            self.REWORKED_EPISODES,
            "N_EPISODES threshold for Reworked Floodplain descriptive condition",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=3,
            minValue=1
        ))
        # [FRAF-P2-DOC] The selected source field supplies disturbance episode counts, by default
        # [FRAF-P2-DOC] the Module 4a N_EPISODES attribute.
        self.addParameter(QgsProcessingParameterString(
            self.EPISODE_FIELD,
            "Episode-count field",
            defaultValue="N_EPISODES",
            optional=True
        ))
        # [FRAF-P2-DOC] The preferred endpoint-state field can be overridden; later lookup
        # [FRAF-P2-DOC] falls back through named fields if that value is missing.
        self.addParameter(QgsProcessingParameterString(
            self.FINAL_STATE_FIELD,
            "Preferred final-state field",
            defaultValue="FINAL_ONTO_STATE",
            optional=True
        ))
        # [FRAF-P2-DOC] One polygon output retains input geometry and the appended age/state data.
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            "Assemblage with publication surface-age/state fields"
        ))

    # ---------------- helpers ----------------

    # [FRAF-P2-DOC] Normalise QGIS null objects and empty/null-like strings to Python None.
    # [FRAF-P2-DOC] This helper prevents null strings from being misread as valid evidence.
    def _clean(self, value):
        if value is None:
            return None
        try:
            if hasattr(value, "isNull") and value.isNull():
                return None
        except Exception:
            pass
        s = str(value).strip()
        if not s or s.upper() in {"NULL", "NONE", "<NULL>"}:
            return None
        return s

    # [FRAF-P2-DOC] Canonical lower-case class labels, normalising separators for matching.
    def _norm(self, value):
        s = self._clean(value)
        if s is None:
            return ""
        return s.lower().replace("-", "_").replace(" ", "_")

    # [FRAF-P2-DOC] Check schema presence before attempting optional feature-field access.
    def _field_exists(self, fields, name):
        return bool(name) and fields.indexOf(name) >= 0

    # [FRAF-P2-DOC] Read a feature field only when available and non-null; this allows
    # [FRAF-P2-DOC] controlled fallback among Module 4a field variants.
    def _val(self, feat, fields, name, default=None):
        if not self._field_exists(fields, name):
            return default
        v = feat[fields.indexOf(name)]
        return default if self._clean(v) is None else v

    # [FRAF-P2-DOC] Return the first populated value in an explicitly ordered field list;
    # [FRAF-P2-DOC] the ordering establishes the provenance preference.
    def _first_value(self, feat, fields, names, default=None):
        for name in names:
            v = self._val(feat, fields, name, None)
            if v is not None:
                return v
        return default

    # [FRAF-P2-DOC] Reject non-numeric, NaN and infinite values before age calculations.
    def _as_float(self, value, default=None):
        if value is None:
            return default
        try:
            f = float(str(value))
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except Exception:
            return default

    # [FRAF-P2-DOC] Convert numeric flags/counts to integer with the original rounding rule.
    def _as_int(self, value, default=0):
        f = self._as_float(value, None)
        if f is None:
            return default
        try:
            return int(round(f))
        except Exception:
            return default

    # [FRAF-P2-DOC] Read the last recognisable four-digit year from a Period_i label.
    # [FRAF-P2-DOC] The mapped observation resolution is annual: months/days are discarded,
    # [FRAF-P2-DOC] and intervals that share a year cannot be chronologically separated here.
    def _year_from_period(self, value):
        s = self._clean(value)
        if s is None:
            return None
        years = re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)", s)
        if years:
            return int(years[-1])
        m = re.search(r"(?:18|19|20)\d{2}", s)
        return int(m.group(0)) if m else None

    # ---------------- class/state interpretation ----------------

    # [FRAF-P2-DOC] Identify destructive surface-reset evidence: mapped erosion, water,
    # [FRAF-P2-DOC] channel occupation and other Active Domain aliases. Only these labels
    # [FRAF-P2-DOC] reset publication surface continuity; a deposition label alone does not.
    def _is_erosion_or_active(self, cls):
        c = self._norm(cls)
        if not c:
            return False
        if "erosion" in c:
            return True
        if c in {
            "active_domain", "active_channel", "active_channel_surface",
            "active_area", "channel_surface", "stable_channel",
            "water", "channel", "inchannel_surface",
        }:
            return True
        if "active" in c and "storage" not in c and "deposition" not in c:
            return True
        return False

    # [FRAF-P2-DOC] Recognise observed deposition/storage as possible surface formation.
    # [FRAF-P2-DOC] A deposition record may supply a formation origin when no older preserved
    # [FRAF-P2-DOC] surface is evidenced, but later deposition is treated as reworking.
    def _is_surface_forming_event(self, cls):
        """Observed formation/reworking event, not merely stable support."""
        c = self._norm(cls)
        if not c:
            return False
        if "deposition" in c:
            return True
        return c in {
            "depositional_storage", "storage",
            "generic_deposition", "island_deposition",
            "legacy_channel_deposition", "lateral_accretion",
            "bar_deposition",
        }

    # [FRAF-P2-DOC] Broader test for a surviving non-active surface: both depositional
    # [FRAF-P2-DOC] evidence and stable island/floodplain observations qualify.
    # [FRAF-P2-DOC] A stable observation proves presence, not necessarily exact formation.
    def _is_surface_evidence(self, cls):
        """Positive evidence that a non-active preserved surface exists.

        Broader than _is_surface_forming_event(): stable-island and stable-floodplain
        observations can mark the first preserved surface after an Active-Domain reset,
        but subsequent switches among stable surface labels do not reset surface age.
        """
        c = self._norm(cls)
        if not c:
            return False
        if self._is_surface_forming_event(c):
            return True
        return c in {
            "stable_island", "vegetated_island",
            "stable_floodplain", "inactive_floodplain",
            "persistent_floodplain", "stabilised_floodplain",
            "stabilized_floodplain", "stable_inactive_surface",
        }

    # [FRAF-P2-DOC] Reduce disparate Module 4a endpoint labels to the three broad states.
    # [FRAF-P2-DOC] Explicit stable/vegetated island is SF context; generic deposition is DS.
    # [FRAF-P2-DOC] Unrecognised values return None and can remain unclassified.
    def _state_from_label(self, label):
        c = self._norm(label)
        if not c:
            return None
        if c in {"active_domain", "active", "active_channel"}:
            return "Active Domain"
        if c in {"depositional_storage", "storage"}:
            return "Depositional Storage"
        if c in {
            "stabilised_floodplain", "stabilized_floodplain",
            "stable_floodplain", "persistent_floodplain",
            "inactive_floodplain", "stable_inactive_surface",
            "stable_island", "vegetated_island",
        }:
            return "Stabilised Floodplain"
        # conservative fallbacks
        if self._is_erosion_or_active(c):
            return "Active Domain"
        if "deposition" in c:
            return "Depositional Storage"
        return None

    # [FRAF-P2-DOC] Assign five-year bins to *exact observed* ages only. Bin endpoints are
    # [FRAF-P2-DOC] right-closed (e.g. 5 years belongs to 0-5; 10 belongs to 5-10).
    # [FRAF-P2-DOC] Left-censored lower bounds must never be treated as exact bin ages.
    def _age_class(self, age):
        """Classify exact observed surface age into 5-year publication bins.

        Boundary convention is right-closed after the first class:
        0-5 means <=5 yr; 5-10 means >5 to <=10 yr; and so on.
        Left-censored surfaces never enter this function as exact ages.
        """
        if age is None:
            return "No exact surface age"
        if age <= 5:
            return "0-5 yr"
        if age <= 10:
            return "5-10 yr"
        if age <= 15:
            return "10-15 yr"
        if age <= 20:
            return "15-20 yr"
        if age <= 25:
            return "20-25 yr"
        if age <= 30:
            return "25-30 yr"
        if age <= 35:
            return "30-35 yr"
        return ">35 yr"

    # [FRAF-P2-DOC] Publication mapping categories, with independent classes for active,
    # [FRAF-P2-DOC] inherited/left-censored, unresolved and unclassified surfaces.
    # [FRAF-P2-DOC] Percentile susceptibility classes elsewhere in Paper 2 are unrelated.
    def _map_class(self, state, exact_age, censored):
        if state == "Active Domain":
            return "Active Reworking Domain"
        if censored == 1 and state in {"Depositional Storage", "Stabilised Floodplain"}:
            return "Pre-observation / left-censored"
        if exact_age is not None:
            return self._age_class(exact_age)
        if state in {"Depositional Storage", "Stabilised Floodplain"}:
            return "Age unresolved"
        return "Unclassified"

    # [FRAF-P2-DOC] Numeric order for map styling; 80/90/99 reserve positions for surfaces
    # [FRAF-P2-DOC] without exact ages and should not be interpreted as ages or probabilities.
    def _map_order(self, map_class):
        return {
            "Active Reworking Domain": 0,
            "0-5 yr": 1,
            "5-10 yr": 2,
            "10-15 yr": 3,
            "15-20 yr": 4,
            "20-25 yr": 5,
            "25-30 yr": 6,
            "30-35 yr": 7,
            ">35 yr": 8,
            "Pre-observation / left-censored": 80,
            "Age unresolved": 90,
            "Unclassified": 99,
        }.get(map_class, 99)

    # [FRAF-P2-DOC] Descriptive FP condition is orthogonal to the authoritative AD/DS/SF
    # [FRAF-P2-DOC] state. If Module 4a already supplied FP_CONDITION, keep its recognised
    # [FRAF-P2-DOC] label; otherwise infer a condition from age/bound and episode count.
    # [FRAF-P2-DOC] For censored surfaces, age_for_condition is only a minimum persistence.
    def _fp_condition(self, state, exact_age, min_age, episodes,
                      persistence_years, reworked_episodes, existing=None):
        # Prefer Module 4a's descriptive condition where available.
        e = self._clean(existing)
        if e:
            en = self._norm(e)
            mapping = {
                "active_domain": "Active Domain",
                "depositional_storage": "Depositional Storage",
                "recent_floodplain": "Recent Floodplain",
                "reworked_floodplain": "Reworked Floodplain",
                "persistent_floodplain": "Persistent Floodplain",
                "unresolved": "Unresolved",
            }
            if en in mapping:
                return mapping[en]

        if state != "Stabilised Floodplain":
            return state if state else "Unresolved"

        age_for_condition = exact_age if exact_age is not None else min_age
        if episodes >= reworked_episodes:
            return "Reworked Floodplain"
        if age_for_condition is not None and age_for_condition >= persistence_years:
            return "Persistent Floodplain"
        return "Recent Floodplain"

    # ---------------- main ----------------

    # [FRAF-P2-DOC] Main algorithm: validate the full Module 4a chronology, process each
    # [FRAF-P2-DOC] assemblage polygon independently and emit a classified output layer.
    # [FRAF-P2-DOC] No subsequent R model fitting, erosion prediction or statistics occurs here.
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("Invalid input layer.")

        # [FRAF-P2-DOC] Record processing settings. FINAL_YEAR is an age endpoint here (not only
        # [FRAF-P2-DOC] a compatibility label), whereas persistence/episode thresholds affect
        # [FRAF-P2-DOC] descriptive FP condition labels rather than the reconstructed state.
        final_year = self.parameterAsInt(parameters, self.FINAL_YEAR, context)
        max_steps = self.parameterAsInt(parameters, self.MAX_STEPS, context)
        persistence_years = self.parameterAsInt(parameters, self.PERSISTENCE_YEARS, context)
        reworked_episodes = self.parameterAsInt(parameters, self.REWORKED_EPISODES, context)
        episode_field = self.parameterAsString(parameters, self.EPISODE_FIELD, context) or "N_EPISODES"
        preferred_state_field = self.parameterAsString(parameters, self.FINAL_STATE_FIELD, context) or "FINAL_ONTO_STATE"

        # [FRAF-P2-DOC] Read the input schema once; field presence controls provenance safeguards.
        in_fields = source.fields()
        field_names = in_fields.names()

        # [FRAF-P2-DOC] Require the first complete EA_Class_1 / Period_1 pair to establish
        # [FRAF-P2-DOC] that this is a history-bearing Module 4a input, not a display layer.
        has_chronology = (
            self._field_exists(in_fields, "EA_Class_1")
            and self._field_exists(in_fields, "Period_1")
        )
        # [FRAF-P2-DOC] T0 initial-state and censor flags determine whether an inherited non-active
        # [FRAF-P2-DOC] surface is treated as age-censored instead of newly formed.
        has_t0_provenance = self._field_exists(in_fields, "INIT_STATE")
        has_left_cens = self._field_exists(in_fields, "LEFT_CENS")

        # [FRAF-P2-DOC] User feedback records class boundaries and the continuity definition.
        feedback.pushInfo(
            "Publication age classes: 0-5, 5-10, 10-15, 15-20, 20-25, "
            "25-30, 30-35, >35 years. Surface age resets only with Active Domain/erosion; "
            "depositional reworking is retained separately in SINCE_DISTURB_YR."
        )

        # [FRAF-P2-DOC] Abort before creating output if the necessary history columns are absent.
        if not has_chronology:
            raise QgsProcessingException(
                "Publication surface-age mapping requires the full Module 4a chronology "
                "(EA_Class_i and Period_i). Use Assemblage_Units_FULL_ATTRS."
            )

        # [FRAF-P2-DOC] Clone input fields so all upstream Module 4a history and provenance
        # [FRAF-P2-DOC] attributes survive alongside the new publication-only columns.
        fields = QgsFields(in_fields)
        existing_names = fields.names()
        # [FRAF-P2-DOC] Append only missing publication fields, applying output types appropriate
        # [FRAF-P2-DOC] to year/flag, age and cartographic text columns.
        for name in self.NEW_FIELDS:
            if name in existing_names:
                continue
            if name in {"FIRST_SURF_YEAR", "LAST_RESET_YEAR", "CURR_SURF_YEAR",
                        "AGE_CENSORED", "PERSISTENT_FP", "REWORKED_FP", "RECENT_FP",
                        "SURFACE_MAP_ORDER"}:
                fields.append(QgsField(name, QVariant.Int))
            elif name in {"SURFACE_AGE", "AGE_MIN_YR", "SINCE_DISTURB_YR"}:
                fields.append(QgsField(name, QVariant.Double, len=12, prec=3))
            else:
                fields.append(QgsField(name, QVariant.String, len=180))

        # [FRAF-P2-DOC] Use the input polygon WKB type and CRS unchanged; no geometric rework.
        # [FRAF-P2-DOC] The output sink is managed by QGIS Processing.
        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, source.wkbType(), source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException("Could not create output sink.")

        # [FRAF-P2-DOC] Explicit order of endpoint-state authority: selected field,
        # [FRAF-P2-DOC] FINAL_ONTO_STATE, corrected/fallback final states, then weaker aliases.
        # [FRAF-P2-DOC] A raw EA label is used only if none of these yields a state.
        state_candidates = list(dict.fromkeys([
            preferred_state_field, "FINAL_ONTO_STATE", "FINAL_STATE_CORR", "FINAL_STATE",
            "ONTO_STATE", "CORE_STATE", "PRIMARY_STATE",
        ]))

        # [FRAF-P2-DOC] QA counters track interpretation pathways for processing feedback;
        # [FRAF-P2-DOC] these are cell counts, not area-weighted reach statistics.
        count = source.featureCount()
        qa = {
            "exact": 0, "censored": 0, "active": 0, "unresolved": 0,
            "reset_exact": 0, "t0_censored": 0, "first_deposition_exact": 0,
            "disturbance_age_diff": 0,
        }

        # [FRAF-P2-DOC] Each polygon is evaluated against its *own* ordered EA chronology.
        # [FRAF-P2-DOC] The code does not create a new state history or reassign T0 provenance.
        for i, feat in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            # [FRAF-P2-DOC] Collect valid EA class/observation-year pairs up to MAX_STEPS.
            # [FRAF-P2-DOC] Preserve the step index and sort by it rather than calendar year.
            # [FRAF-P2-DOC] Rows lacking either a class label or parseable year are excluded.
            events = []
            for step in range(1, max_steps + 1):
                cn = f"EA_Class_{step}"
                pn = f"Period_{step}"
                if not self._field_exists(in_fields, cn) or not self._field_exists(in_fields, pn):
                    continue
                cls = self._val(feat, in_fields, cn, None)
                yr = self._year_from_period(self._val(feat, in_fields, pn, None))
                if cls is not None and yr is not None:
                    events.append((step, yr, str(cls)))
            events.sort(key=lambda x: x[0])

            # [FRAF-P2-DOC] Extract potential preserved-surface years, deposition years and reset
            # [FRAF-P2-DOC] years separately; the last destructive reset governs surface age.
            # [FRAF-P2-DOC] The deposition_years list is calculated but not subsequently used.
            all_years = [yr for _, yr, _ in events]
            evidence_years = [yr for _, yr, cls in events if self._is_surface_evidence(cls)]
            deposition_years = [yr for _, yr, cls in events if self._is_surface_forming_event(cls)]
            reset_years = [yr for _, yr, cls in events if self._is_erosion_or_active(cls)]
            first_surf_year = min(evidence_years) if evidence_years else None
            last_reset_year = max(reset_years) if reset_years else None

            # [FRAF-P2-DOC] Prefer the supplied Module 4a final state; only if unresolved do
            # [FRAF-P2-DOC] we infer an endpoint from the latest available EA class label.
            # [FRAF-P2-DOC] An unrecognised endpoint remains Unclassified (not automatically SF).
            final_state_used = self._first_value(feat, in_fields, state_candidates, None)
            core_state = self._state_from_label(final_state_used)
            if core_state is None and events:
                core_state = self._state_from_label(events[-1][2])
            if core_state is None:
                core_state = "Unclassified"

            # [FRAF-P2-DOC] Read initial T0 state and left-censor flag from Module 4a provenance.
            # [FRAF-P2-DOC] Missing fields do not become proof that a surface formed after T0.
            init_state_raw = self._val(feat, in_fields, "INIT_STATE", None) if has_t0_provenance else None
            init_state = self._state_from_label(init_state_raw)
            init_left_cens = 1 if (has_left_cens and self._as_int(self._val(feat, in_fields, "LEFT_CENS", 0), 0) == 1) else 0

            # [FRAF-P2-DOC] Copy optional episode and disturbance clock information separately.
            # [FRAF-P2-DOC] SURFACE_AGE_EST is used only as a fallback source for the disturbance clock;
            # [FRAF-P2-DOC] neither clock is used as a substitute for publication surface age.
            episodes = self._as_int(self._val(feat, in_fields, episode_field, 0), 0)
            since_disturb = self._as_float(
                self._first_value(feat, in_fields, ["SINCE_DISTURB_YR", "SURFACE_AGE_EST"], None), None
            )
            # [FRAF-P2-DOC] Prefer explicit RECORD_SPAN_YR for censored lower bounds; fallback
            # [FRAF-P2-DOC] uses FINAL_YEAR minus earliest classed evidence, which may be conservative
            # [FRAF-P2-DOC] or differ from the actual T0 observation span.
            record_span = self._as_float(self._val(feat, in_fields, "RECORD_SPAN_YR", None), None)
            if record_span is None and all_years:
                record_span = max(0.0, float(final_year - min(all_years)))

            # [FRAF-P2-DOC] Initialise mutually exclusive age outcomes: exact, lower-bound
            # [FRAF-P2-DOC] left-censored, active/unresolved; retain an explanatory provenance label.
            exact_age = None
            min_age = None
            censored = 0
            curr_surf_year = None
            age_source = ""
            age_note = ""

            # [FRAF-P2-DOC] Current Active Domain occupation has no preserved non-active
            # [FRAF-P2-DOC] surface age even when historical non-active episodes existed.
            if core_state == "Active Domain":
                age_source = "active_domain"
                age_note = "Active Domain: no preserved non-active surface age assigned."

            # [FRAF-P2-DOC] An observed reset destroys the earlier surface: seek the earliest
            # [FRAF-P2-DOC] non-active surface evidence at/after the final reset and date from it.
            # [FRAF-P2-DOC] Later depositional additions need not destroy the preserved surface.
            # [FRAF-P2-DOC] CAUTION: dates are reduced to years; the >= comparison may include
            # [FRAF-P2-DOC] surface evidence in the same year without within-year ordering.
            elif last_reset_year is not None:
                after = [yr for _, yr, cls in events if yr >= last_reset_year and self._is_surface_evidence(cls)]
                curr_surf_year = min(after) if after else None
                if curr_surf_year is not None:
                    exact_age = max(0.0, float(final_year - curr_surf_year))
                    age_source = "first_surface_after_last_active_reset"
                    age_note = (
                        "Exact surface age from first preserved-surface evidence after the last "
                        "Active-Domain/erosion reset. Later depositional reworking does not reset age."
                    )
                    qa["reset_exact"] += 1
                else:
                    age_source = "reset_without_later_surface"
                    age_note = "Active/erosional reset detected but no later preserved-surface evidence found."

            # [FRAF-P2-DOC] If a non-active T0 surface has no later mapped destructive reset, its
            # [FRAF-P2-DOC] true formation date remains unknown. Store observed persistence as
            # [FRAF-P2-DOC] AGE_MIN_YR and keep SURFACE_AGE null (left-censored), even if deposition
            # [FRAF-P2-DOC] occurred during the observation record.
            elif init_left_cens == 1 and init_state in {"Depositional Storage", "Stabilised Floodplain"}:
                censored = 1
                min_age = record_span
                age_source = "t0_inherited_surface_continuity"
                age_note = (
                    "Surface was already non-active at T0 and no later Active-Domain reset occurred. "
                    "Later deposition/island_deposition records reworking only. AGE_MIN_YR is minimum "
                    "continuous surface persistence; true formation predates the record."
                )
                qa["t0_censored"] += 1

            # [FRAF-P2-DOC] A known Active Domain seed at T0 allows the first subsequent observed
            # [FRAF-P2-DOC] non-active surface to establish an exact formation-year proxy.
            elif init_state == "Active Domain":
                after = [yr for _, yr, cls in events if self._is_surface_evidence(cls)]
                curr_surf_year = min(after) if after else None
                if curr_surf_year is not None:
                    exact_age = max(0.0, float(final_year - curr_surf_year))
                    age_source = "surface_after_t0_active_seed"
                    age_note = "Exact surface age from first preserved-surface evidence after T0 Active Domain."
                    qa["reset_exact"] += 1
                else:
                    age_source = "t0_active_without_surface"
                    age_note = "T0 Active Domain seed but no later preserved-surface evidence found."

            # [FRAF-P2-DOC] With no observed reset and no explicit T0-censor classification, inspect
            # [FRAF-P2-DOC] the earliest non-active surface evidence: formation vs already stable
            # [FRAF-P2-DOC] surface requires different exact/censored interpretations.
            elif first_surf_year is not None and core_state in {"Depositional Storage", "Stabilised Floodplain"}:
                # No Active-Domain reset is known. The nature of the FIRST non-active
                # observation determines whether formation is observed or only bounded.
                first_surface_events = [
                    (yr, cls) for _, yr, cls in events if self._is_surface_evidence(cls)
                ]
                first_surface_events.sort(key=lambda x: x[0])
                first_year, first_cls = first_surface_events[0]
                # [FRAF-P2-DOC] An observed first deposition/storage event is treated as the recorded
                # [FRAF-P2-DOC] surface-formation year, subject to the history completeness assumption.
                if self._is_surface_forming_event(first_cls):
                    curr_surf_year = first_year
                    exact_age = max(0.0, float(final_year - curr_surf_year))
                    age_source = "first_observed_deposition_without_prior_surface"
                    age_note = (
                        "The first non-active evidence is an observed deposition/storage event, used as "
                        "surface formation. Later deposition does not reset surface age."
                    )
                    qa["first_deposition_exact"] += 1
                else:
                    # [FRAF-P2-DOC] An already stable first observation only bounds surface age from below;
                    # [FRAF-P2-DOC] it does not establish the date the surface was originally deposited.
                    censored = 1
                    min_age = max(0.0, float(final_year - first_year))
                    age_source = "first_observed_stable_surface_left_censored"
                    age_note = (
                        "The first non-active observation is already a stable island/floodplain surface, "
                        "with no preceding Active-Domain reset. AGE_MIN_YR is therefore minimum continuous "
                        "surface persistence; later deposition/island_deposition is reworking, not formation."
                    )
            else:
                age_source = "age_unresolved"
                age_note = "No defensible surface-origin or inherited-surface chronology could be identified."

            # [FRAF-P2-DOC] Flag differences between exact surface continuity age and Module 4a
            # [FRAF-P2-DOC] time-since-last-disturbance; such differences may be real reworking,
            # [FRAF-P2-DOC] not a calculation error. The QA is a count of polygons.
            if exact_age is not None and since_disturb is not None and abs(exact_age - since_disturb) > 0.01:
                qa["disturbance_age_diff"] += 1

            # [FRAF-P2-DOC] Assign a mutually exclusive age-status interpretation for reporting.
            # Status and publication classes.
            if core_state == "Active Domain":
                age_status = "Active Domain"
                qa["active"] += 1
            elif censored == 1:
                age_status = "Left-censored"
                qa["censored"] += 1
            elif exact_age is not None:
                age_status = "Exact observed age"
                qa["exact"] += 1
            else:
                age_status = "Age unresolved"
                qa["unresolved"] += 1

            # [FRAF-P2-DOC] Keep exact-age bins separate from left-censored and unresolved classes.
            # [FRAF-P2-DOC] Map classes are produced without modifying the original polygons.
            age_class = self._age_class(exact_age)
            surface_map_class = self._map_class(core_state, exact_age, censored)
            surface_map_order = self._map_order(surface_map_class)

            # [FRAF-P2-DOC] Retain an existing valid Module 4a FP condition where available;
            # [FRAF-P2-DOC] otherwise derive a descriptive category without redefining AD/DS/SF.
            existing_fp_condition = self._val(feat, in_fields, "FP_CONDITION", None)
            fp_condition = self._fp_condition(
                core_state, exact_age, min_age, episodes,
                persistence_years, reworked_episodes, existing_fp_condition
            )

            # [FRAF-P2-DOC] Binary publication-condition indicators describe the FP_CONDITION text.
            # [FRAF-P2-DOC] They are not transition event/risk flags and are not used as Cox outcomes.
            persistent_fp = 1 if fp_condition == "Persistent Floodplain" else 0
            reworked_fp = 1 if fp_condition == "Reworked Floodplain" else 0
            recent_fp = 1 if fp_condition == "Recent Floodplain" else 0

            # [FRAF-P2-DOC] Assemble canonical age, provenance, ontology and map attributes.
            # [FRAF-P2-DOC] AGE_SOURCE and AGE_NOTE provide per-polygon interpretation traceability;
            # [FRAF-P2-DOC] AGE_MIN_YR remains blank except for left-censored observations.
            derived = {
                "FIRST_SURF_YEAR": first_surf_year,
                "LAST_RESET_YEAR": last_reset_year,
                "CURR_SURF_YEAR": curr_surf_year,
                "SURFACE_AGE": exact_age,
                "AGE_MIN_YR": min_age if censored == 1 else None,
                "AGE_CENSORED": censored,
                "AGE_STATUS": age_status,
                "AGE_CLASS": age_class if exact_age is not None else age_status,
                "SURFACE_MAP_CLASS": surface_map_class,
                "SURFACE_MAP_ORDER": surface_map_order,
                "CORE_STATE": core_state,
                "FP_CONDITION": fp_condition,
                "FINAL_STATE_USED": str(final_state_used) if final_state_used is not None else None,
                "PERSISTENT_FP": persistent_fp,
                "REWORKED_FP": reworked_fp,
                "RECENT_FP": recent_fp,
                "AGE_SOURCE": age_source,
                "AGE_NOTE": age_note,
                "SINCE_DISTURB_YR": since_disturb,
            }

            # [FRAF-P2-DOC] Rebuild attributes in output-schema order, inserting new derived values
            # [FRAF-P2-DOC] while preserving unmodified fields from the input history.
            out_attrs = []
            for fld in fields:
                name = fld.name()
                if name in derived:
                    out_attrs.append(derived[name])
                elif name in field_names:
                    out_attrs.append(feat[in_fields.indexOf(name)])
                else:
                    out_attrs.append(None)

            # [FRAF-P2-DOC] Copy original geometry and write the record to the QGIS feature sink.
            # [FRAF-P2-DOC] No geometry simplification, dissolve, buffering or resampling is performed.
            out_feat = QgsFeature(fields)
            out_feat.setGeometry(feat.geometry())
            out_feat.setAttributes(out_attrs)
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            if count:
                feedback.setProgress(int((i + 1) * 100 / count))

        # [FRAF-P2-DOC] Report age-status and chronology-provenance counts after iteration.
        # [FRAF-P2-DOC] These are diagnostic counts, not area-weighted summary results.
        feedback.pushInfo(
            "Age QA | exact={exact:,}; left-censored={censored:,}; active={active:,}; "
            "unresolved={unresolved:,}; exact-after-reset={reset_exact:,}; "
            "T0-censored={t0_censored:,}; first-deposition-exact={first_deposition_exact:,}; "
            "surface-age != disturbance-age={disturbance_age_diff:,}".format(**qa)
        )
        feedback.pushInfo(
            "Publication SURFACE_AGE uses surface continuity since Active-Domain/erosion reset. "
            "SINCE_DISTURB_YR remains the separate time-since-last erosion/deposition metric."
        )
        # [FRAF-P2-DOC] Warn when T0 provenance is incomplete: uncensored classifications may
        # [FRAF-P2-DOC] then be less defensible. Prefer Module 4a v10.9+ FULL_ATTRS for publication.
        if not has_t0_provenance or not has_left_cens:
            feedback.pushWarning(
                "INIT_STATE/LEFT_CENS provenance fields were not both present. T0 censoring is less certain; "
                "use current Module 4a v10.9+ Assemblage_Units_FULL_ATTRS for publication."
            )

        # [FRAF-P2-DOC] Return the QGIS sink identifier; downstream styling or statistics are separate.
        return {self.OUTPUT: dest_id}
