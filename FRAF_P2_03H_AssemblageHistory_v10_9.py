# -*- coding: utf-8 -*-
# =============================================================================
# FRAF | PAPER 2 | 03H — ASSEMBLAGE HISTORY RECONSTRUCTION (PyQGIS)
# Archive filename : FRAF_P2_03H_AssemblageHistory_v10_9.py
# Based on        : FRAF Module 4a Assemblage Builder v10.9 (2026 source)
# Change scope     : COMMENT-ONLY archival annotation; NO behavioural edits.
#
# PURPOSE AND SCIENTIFIC POSITION
# Reconstruct the spatial assemblage and its observed history from dated
# erosion–accretion (EA) polygons. This is the PLANAR-FABRIC/HISTORY pathway,
# separate from the fixed-place sampling/transition-risk pathway in 03P.
# EA_Class_i represents direct process/source evidence; ONTO_STATE_i describes
# the retrospectively reconstructed three-state sequence for fabric cells.
#
# SOURCE LINEAGE / AUTHORSHIP
# Channel-shifting and erosion–accretion GIS lineage: Rusnák et al. (2025).
# Rusnák, M., Opravil, Š., Dunesme, S., Afzali, H., Rey, L., Parmentier, H.,
# Piégay, H. (2025). A channel shifting GIS toolbox for exploring floodplain
# dynamics through channel erosion and deposition. Geomorphology 477, 109688.
# DOI: https://doi.org/10.1016/j.geomorph.2025.109688
# This specific assemblage-history implementation is a FRAF extension developed
# by Martin Dawson with ChatGPT-assisted PyQGIS code development; this does not
# attribute the v10.9 state-history algorithm to the cited paper's authors.
#
# KEY INTERPRETIVE DEFINITIONS
# AD = ACTIVE_DOMAIN: observed/reconstructed active occupation.
# DS = DEPOSITIONAL_STORAGE: recent/stored material outside active occupation;
# storage onset/reworking and the storage-clock rule matter.
# SF = STABILISED_FLOODPLAIN: inherited or subsequently stabilised surfaces.
# UNRESOLVED = evidence/provenance limitation, NOT a fourth assemblage state.
# T0 non-active surfaces may pre-date observation and are LEFT-CENSORED; no
# undocumented earlier formation date or event is created by the code.
# Stable islands are SF with an island-context attribute, not another state.
# DS -> SF follows the configurable Module-3B-consistent 20-year/evidence rule;
# N_EPISODES describes historical reworking and does NOT gate that transition.
#
# PIPELINE MAP (see processAlgorithm and named helper methods)
# [1] Check input polygons, class/period fields, temporal gaps and CRS.
# [2] Prepare corridor, historical active belt, background mask and T0 layer.
# [3] Prepare one dated, class-bearing EA layer per observed interval.
# [4] Polygonize all relevant boundaries ONCE into a stationary planar fabric.
# [5] Attribute each fabric cell from each EA source via point-on-surface join;
# rescue unresolved/ambiguous assignments by area intersections as needed.
# [6] Count source support BEFORE filling background/unresolved assignments.
# [7] Apply explicit background policy and provenance-aware T0 seed.
# [8] Reconstruct sequential states, transitions, ages and history metrics.
# [9] Run hard QA for continuity, semantic transitions and stable background.
# [10] Persist full analytical outputs, QA table, lightweight display and
# optional dissolved/statistical layer(s) in a multi-layer GeoPackage.
#
# OUTPUTS / IMPORTANT FIELD CONTRACTS
# Assemblage_Units_FULL_ATTRS: complete dated evidence, states and metrics.
# Assemblage_Display: lightweight mapped output returned by the algorithm.
# Assemblage_QA_Summary: support/state/provenance area diagnostic table.
# Optional Assemblage_Dissolved and Assemblage_StatsFabric.
# INIT_STATE/INIT_PROV/LEFT_CENS: state/provenance before reliable chronology.
# SURFACE_AGE_EST: recorded persistence since last mapped disturbance;
# AGE_CENSORED indicates a MINIMUM observed age, not full formation age.
# STORAGE_AGE_YR / SINCE_STORAGE_YR: elapsed age of current storage-derived
# surface, distinct from SINCE_STORAGE_STATE_YR (last DS occupancy).
# N_ASM_*_TRANS: descriptive reconstructions; DO NOT substitute for 03P
# transition-specific, eligible risk-set/event definitions used by Cox.
#
# METHOD-AND-RUNTIME CAVEATS
# Observation time is bracketed by the supplied dates; polygon classes and
# geometry reflect the source mapping and threshold choices. Mixed/unsupported
# source classes must not be silently treated as stable floodplain. Mask and
# T0 precedence matters; avoid assuming absence of mapped EA is positive SF.
# Area and lengths use the input projected coordinate system / QGIS geometry.
# Intermediate file-backed SHP/GPKG layers are performance and field-fidelity
# protections for long records; ensure adequate disk space for large runs.
# All original QGIS Processing algorithm identifiers and parameter defaults
# are intentionally unchanged despite this archival filename change.
# Python source parsing is checked, but execution in a live QGIS installation
# is not implied by these comment-only changes.
# =============================================================================
"""
Module 4a — Floodplain Assemblage (QGIS / SCS Toolbox) — v10.9 generic T0 provenance / Module-3B-consistent stabilisation / state continuity

Changes in this corridor-aware version
--------------------------------------
- v10.9: adds generic, provenance-aware T0 initialisation without river-name branches. Optional T0 classification can seed Active Domain, Depositional Storage, Stabilised Floodplain, stable-island context, or prior unknown states. Initial non-active surfaces are explicitly left-censored and no pre-record formation event is invented. Adds INIT_STATE/INIT_PROV/INIT_CONTEXT/LEFT_CENS/SF_PROV/AGE_CENSORED fields and storage-reworking/floodplain-to-storage transition counts. Stable islands remain within the three-state framework as Stabilised Floodplain with island context. Depositional Storage -> Stabilised Floodplain now follows the Module 3B elapsed-year/explicit-evidence rule (modes: years only, years OR stable evidence, years AND stable evidence); the former <3-episode gate is removed from state transition logic and retained only as a descriptive reworking classification.
- v10.8: separates storage-state occupancy from storage-entry age. SINCE_STORAGE/SINCE_STORAGE_YR now mean elapsed time since the most recent entry/re-entry into the currently preserved storage-derived surface; legacy last-storage occupancy timing is retained in SINCE_STORAGE_STATE_YR. Adds FIRST_STORAGE_ENTRY, LAST_STORAGE_ENTRY, LAST_STORAGE_STATE, STORAGE_AGE_YR and STORAGE_AGE_STEP. PRIMARY_STATE now follows the reconstructed final assemblage state rather than the historical event style.
- v10.7: separates source support from geomorphic state. EA_Class_i remains the direct EA evidence field; ONTO_STATE_i now carries the last resolved state through reworked_unresolved support gaps. Depositional Storage was promoted sequentially to Stabilised Floodplain using the former 20-year persistence / <3-episode rule (superseded by v10.9 Module-3B-consistent stabilisation). Adds state-carry diagnostics and hard propagation QA so a known state cannot silently revert to UNRESOLVED solely because later EA support is absent; also prevents zero-state/zero-event cells from being mislabeled as stable_floodplain through a 0=0 tie.
- v10.6: validates CLASS_FIELD before the expensive fabric build. Provider-ID fields,
  numeric fields, and string fields dominated by numeric-like values are rejected
  because the assemblage logic requires textual EA classes (for example erosion,
  deposition, stable_channel, stable_island, and stable_floodplain).
- v10.5: builds Assemblage_Display by reducing to the lightweight field schema before adding ASM_ID, preventing long ONTO_TRANS_SUM values from being rewritten through a stale 120-character source width. Retains the v10.4 long-text schema fix, QA imports, runtime-symbol preflight and early core-layer write.
- v10.2: restores the @staticmethod decorator on _norm_date_txt (accidentally lost during v10.1 integration), accepts the existing PeriodEnd YYYY_MM_DD values correctly, defaults PERIOD_FIELD to PeriodEnd, and rejects provider ID fields as chronology fields with a clear message.
- v10.1: requires one consistent period per EA layer, validates calendar dates and user-defined year limits, rejects duplicate/non-increasing timesteps and excessive gaps, and writes Period_i only from the validated chronology.
- v9.2 fix: writes every validated zero-source background timestep explicitly as stable_floodplain and populates every Period_i value, including QGIS NULL/QVariant-null inputs.
- Adds hard post-fill and post-metric QA checks so invalid background histories cannot be silently saved.
- Prevents unresolved raw histories from being promoted to Persistent/Reworked Floodplain.
- Classifies zero recognised states as unresolved rather than single_state.
- v9.1 fix: constructs corridor residual explicitly as Analysis Corridor minus the combined EA footprint, then merges it with EA-supported fabric cells.
- Adds corridor-completion QA/debug layers so the buffer cannot disappear solely because polygonize omitted the outer residual polygon.
- Adds an optional fixed Analysis Corridor used as the outer planar-fabric envelope.
- Adds an optional Valid Background Floodplain Mask for observed undisturbed floodplain.
- Keeps corridor-only residual cells unresolved by default; they become stable floodplain only when explicitly validated.
- Adds source-support, early/middle/late coverage, valid-observation, background-floodplain, and zero-episode QA fields.
- Allows an explicit opt-in to treat all corridor-only residual cells as observed background floodplain when no mask is supplied.
- Preserves the v8.1 QGIS FID fix and performance-optimized reassignment/output logic.

Retained v8.1 changes
- QGIS compatibility fix: batched QgsFeatureRequest.setFilterFids() calls now receive lists rather than Python sets.
- Retains the v7 merged multi-layer output, Shannon-diversity, persistence, event, and output-verification logic.
- Replaces per-timestep full-fabric rewrites with in-place provider batch updates.
- Builds one narrow geometry/ID fabric and one representative-point layer for all timesteps.
- Uses the already prepared and spatially indexed EA sources directly; no per-step source copies.
- Removes repeated full-table null scans and derives unresolved IDs from the cached fabric index.
- Restricts overlap rescue to a narrow geometry/ID subset and eliminates per-step dissolved footprints.
- Performs geometry cleanup once before reassignment and once at the end, rather than every 10 steps.
- Adds stage timers and a configurable minimum fabric-cell area (default 50 m²).
- Uses provider-level batch writes for neutral filling and assemblage metrics.
- Corrected final GeoPackage writing so output layers are added to one dataset
  instead of later save operations replacing earlier layers.
- Uses QgsVectorFileWriter CreateOrOverwriteFile for the first output layer and
  CreateOrOverwriteLayer for all subsequent layers.
- Verifies every written GeoPackage layer before the algorithm completes.
- HACH / CHM / segment-stats functionality removed
- Faster assemblage fabric build:
    * polygon boundaries from all EA layers
    * merge once
    * polygonize once
    * keep cells inside combined EA footprint
- Revised assemblage metrics:
    * state-aware ACTIVE_DOMAIN / DEPOSITIONAL_STORAGE / STABILISED_FLOODPLAIN histories
    * per-place Shannon state diversity (ASM_SHANNON / ASM_H_NORM / ASM_RICHNESS / ASM_H_CLASS)
    * persistence-promotion of long-lived depositional storage to floodplain condition
    * FP_STAB / FP_CONDITION fields for recent, persistent, and reworked floodplain mapping
    * storage and stabilisation event counts for Step 3 / R compatibility
    * island processes merged into broader erosion/deposition dominance
    * island retained as secondary context via ISL_FRAC / ISLAND_CTX
    * N_EPISODES / QUIET_MAX / EP_LEN_MAX retained
- Performance controls:
    * permanent undissolved SRCMASK used for fabric retention
    * conditional ambiguous-overlap rescue
    * stable geometry throughout timestep reassignment
    * cached representative points and narrow geometry/ID rescue layer
    * provider-level attribute batches instead of per-feature updates
    * no per-step full-fabric GeoPackage copies or geometry checkpoints
    * lightweight display layer returned by default

Outputs
-------
- Assemblage_Units
- optional Assemblage_Dissolved
- optional Assemblage_StatsFabric
"""

# Imports are runtime dependencies of the QGIS Processing script; no third-party pip install is implied.
import gc
import os
import re
import math
import time
import tempfile
import uuid
from datetime import date, datetime


from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorDestination,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsProcessingUtils,
    QgsField,
    QgsFields,
    QgsFeature,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsVectorFileWriter,
)

import processing


# The registered algorithm class and its stable QGIS ID remain unchanged.
class ChronologicalOverwriteEA(QgsProcessingAlgorithm):
    # The parameter names are the external API used by Processing and saved QGIS models.
    # Changing labels/ordering is outside a comment-only archival revision.
    # Core parameters
    PARAM_LAYERS = "EA_LAYERS"
    PARAM_CLASS_FIELD = "CLASS_FIELD"
    PARAM_PERIOD_FIELD = "PERIOD_FIELD"
    PARAM_DISSOLVE = "DISSOLVE_BY_FINAL"
    PARAM_OUTPUT = "OUTPUT"
    PARAM_MIN_FABRIC_AREA = "MIN_FABRIC_AREA"
    PARAM_CORRIDOR = "ANALYSIS_CORRIDOR"
    PARAM_BACKGROUND_MASK = "VALID_BACKGROUND_MASK"
    PARAM_HISTORICAL_BELT = "HISTORICAL_ACTIVE_BELT"
    PARAM_ASSUME_CORRIDOR_FP = "ASSUME_CORRIDOR_BACKGROUND_FP"
    PARAM_MIN_VALID_FRAC = "MIN_VALID_ASSIGNMENT_FRAC"
    PARAM_MIN_VALID_YEAR = "MIN_VALID_YEAR"
    PARAM_MAX_VALID_YEAR = "MAX_VALID_YEAR"
    PARAM_MAX_INTERVAL_YEARS = "MAX_INTERVAL_YEARS"

    # T0 policy affects initial provenance only; it is not a fourth observed EA interval.
    # Generic T0 initial-state / provenance options (v10.9)
    PARAM_INITIAL_MODE = "INITIAL_STATE_MODE"
    PARAM_INITIAL_LAYER = "INITIAL_STATE_LAYER"
    PARAM_INITIAL_STATE_FIELD = "INITIAL_STATE_FIELD"
    PARAM_INITIAL_CONTEXT_FIELD = "INITIAL_CONTEXT_FIELD"
    PARAM_INITIAL_ACTIVE_VALUES = "INITIAL_ACTIVE_VALUES"
    PARAM_INITIAL_STORAGE_VALUES = "INITIAL_STORAGE_VALUES"
    PARAM_INITIAL_STABLE_VALUES = "INITIAL_STABLE_VALUES"

    # Storage-to-SF threshold and evidence mode should be aligned with 03P for comparison.
    # Module-3B-consistent storage stabilisation options (v10.9)
    PARAM_STABILISATION_YEARS = "STABILISATION_YEARS"
    PARAM_STABILISATION_MODE = "STABILISATION_MODE"
    PARAM_STABLE_EVIDENCE_CLASSES = "STABLE_EVIDENCE_CLASSES"

     # Cartographic refinement and diagnostics do not alter the primary state-transition rule.
     # Phase B options
    PARAM_MAX_QUIET = "MAX_QUIET"
    PARAM_REFINE_STYLE = "REFINE_STYLE"
    PARAM_SAVE_STATS_FABRIC = "SAVE_STATS_FABRIC"
    PARAM_SAVE_DEBUG = "SAVE_DEBUG"
    PARAM_DEBUG_FOLDER = "DEBUG_FOLDER"

    

    # Translate UI-facing text through the existing SCS Toolbox translation context.
    def tr(self, text):
        return QCoreApplication.translate("SCS Module 4a Floodplain Assemblage", text)

    # QGIS Processing factory: provide a new instance of this algorithm when registered.
    def createInstance(self):
        return ChronologicalOverwriteEA()

    # Stable Processing registry ID; retained despite the repository filename change.
    def name(self):
        return "module4a_floodplain_assemblage_v10_9"

    # Human-readable name shown in QGIS Processing Toolbox and dialog.
    def displayName(self):
        return self.tr("Module 4a — Floodplain Assemblage (v10.9 generic T0 provenance / Module 3B stabilisation / state continuity)")

    # Processing Toolbox category displayed to a user.
    def group(self):
        return self.tr("SCS Toolbox")

    # Stable non-translated Processing Toolbox group key.
    def groupId(self):
        return "scs_ea_utils"

    # Explain the analysis, input provenance and storage rules within the QGIS UI.
    def shortHelpString(self):
        return self.tr(
            "Build a chronological floodplain assemblage from sequential EA layers.\n"
            "The optional Analysis Corridor makes the assemblage population consistent with\n"
            "place-based transition and hazard analyses. A generic T0 initial-state layer can\n"
            "distinguish inherited Active Domain, Depositional Storage, Stabilised Floodplain,\n"
            "stable-island context and prior-unknown surfaces without river-specific code.\n"
            "Pre-existing non-active surfaces are left-censored: their formative event is not\n"
            "invented at T0 and age fields are flagged as minimum observed persistence where appropriate.\n"
            "Depositional Storage -> Stabilised Floodplain follows the same configurable elapsed-year /\n"
            "explicit-stable-evidence rule as Module 3B; episode count remains descriptive only.\n"
            "EA_Class_i retains direct source support while ONTO_STATE_i is the reconstructed state sequence.\n"
            "Each EA layer must contain one consistent period; duplicate, out-of-range, non-increasing\n"
            "and excessive-gap dates stop processing."
        )

    # Declare QGIS Processing inputs and defaults, without running geometry work.
    # Grouping: dated EA; analysis corridor/background/belt; T0 provenance;
    # stabilisation and evidence settings; fabric/observation limits; outputs.
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_LAYERS,
                self.tr("EA polygon layers (one per period; order not required)"),
                layerType=QgsProcessing.TypeVectorPolygon,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_CORRIDOR,
                self.tr("Analysis corridor polygon (optional; use the same fixed corridor as Module 3B/hazard analysis)"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_BACKGROUND_MASK,
                self.tr("Valid observed background-floodplain mask (optional; must lie inside the analysis corridor)"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_HISTORICAL_BELT,
                self.tr("Historical Active Domain belt (dissolved union; protected from background assignment)"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_ASSUME_CORRIDOR_FP,
                self.tr("Treat all corridor-only residual cells as observed stable floodplain when no background mask is supplied"),
                defaultValue=False,
            )
        )

        # A user-supplied T0 layer can mark inherited states with known class and context.
        # Mode 2 is an explicit assumption, not a consequence of absent EA activity.
        # --------------------------------------------------------------
        # Generic T0 initial-state / provenance configuration
        # --------------------------------------------------------------
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PARAM_INITIAL_MODE,
                self.tr("T0 initial-state policy"),
                options=[
                    "Conservative / evidence-led (background + optional explicit T0 classes; otherwise Prior Unknown)",
                    "Explicit T0 classification required",
                    "Floodplain-default for unclassified T0 terrestrial fabric (generic single-thread option)",
                ],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_INITIAL_LAYER,
                self.tr("Optional T0 surface/state classification polygon layer"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_INITIAL_STATE_FIELD,
                self.tr("T0 classification state field"),
                defaultValue="INIT_STATE",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_INITIAL_CONTEXT_FIELD,
                self.tr("Optional T0 surface-context field (blank = derive from state value)"),
                defaultValue="",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_INITIAL_ACTIVE_VALUES,
                self.tr("T0 values mapped to Active Domain (comma-separated)"),
                defaultValue="active_domain,active,active_channel,channel,water,inchannel_surface",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_INITIAL_STORAGE_VALUES,
                self.tr("T0 values mapped to Depositional Storage (comma-separated)"),
                defaultValue="depositional_storage,storage,bar,bar_storage,new_bar,deposition",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_INITIAL_STABLE_VALUES,
                self.tr("T0 values mapped to Stabilised Floodplain (comma-separated; stable islands remain a context of this state)"),
                defaultValue="stabilised_floodplain,stabilized_floodplain,stable_floodplain,inactive_floodplain,floodplain,stable_island,vegetated_island",
            )
        )

        # Use the Module 3B elapsed-year rule for state promotion.
        # The default 20-year value is a modelling definition, not a remotely sensed date.
        # --------------------------------------------------------------
        # Module-3B-consistent Depositional Storage -> Stabilised Floodplain
        # --------------------------------------------------------------
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_STABILISATION_YEARS,
                self.tr("Elapsed storage years required for Stabilised Floodplain"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=20.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PARAM_STABILISATION_MODE,
                self.tr("Stabilisation evidence rule (match Module 3B)"),
                options=[
                    "Elapsed years only (recommended comparative rule)",
                    "Elapsed years OR explicit stable-floodplain evidence",
                    "Elapsed years AND explicit stable-floodplain evidence",
                ],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_STABLE_EVIDENCE_CLASSES,
                self.tr("EA classes providing explicit stable-surface evidence (comma-separated)"),
                defaultValue="stable_floodplain,inactive_floodplain",
            )
        )

        # VALID_OBS measures quality of dated source support, before inferred fill.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MIN_VALID_FRAC,
                self.tr("Minimum source-assignment fraction for VALID_OBS (EA-supported cells)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.75,
                minValue=0.0,
                maxValue=1.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.PARAM_CLASS_FIELD,
                self.tr("Class field (e.g. EA or EA_Class)"),
                parentLayerParameterName=self.PARAM_LAYERS,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.PARAM_PERIOD_FIELD,
                self.tr("Period field (e.g. PeriodEnd, yyyy_mm_dd, yyyyMMdd, or a date range)"),
                parentLayerParameterName=self.PARAM_LAYERS,
                defaultValue="PeriodEnd",
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MIN_VALID_YEAR,
                self.tr("Minimum valid observation year"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1800,
                minValue=1000,
                maxValue=2500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MAX_VALID_YEAR,
                self.tr("Maximum valid observation year"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=date.today().year,
                minValue=1000,
                maxValue=2500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MAX_INTERVAL_YEARS,
                self.tr("Maximum permitted interval between EA observations (years)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=50.0,
                minValue=0.01,
                maxValue=500.0,
            )
        )

        # Discard sliver cells only at the configured area threshold; results are scale-sensitive.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MIN_FABRIC_AREA,
                self.tr("Minimum planar-fabric cell area (map units²; 0 keeps all slivers)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=50.0,
                minValue=0.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_DISSOLVE,
                self.tr("Save cartographic dissolved layer (Assemblage_Dissolved)"),
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_REFINE_STYLE,
                self.tr("Refine ASM_STYLE using episodes + quiet periods"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MAX_QUIET,
                self.tr("Maximum quiet gap to merge into one episode (steps)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_SAVE_STATS_FABRIC,
                self.tr("Save stats-friendly dissolved layer (Assemblage_StatsFabric)"),
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_SAVE_DEBUG,
                self.tr("Save debug layers for fabric/reassignment diagnosis"),
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_DEBUG_FOLDER,
                self.tr("Debug output folder (used only if Save debug layers is checked)"),
                defaultValue=r"D:\QGIS_TEMP\debug_layers",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.PARAM_OUTPUT,
                self.tr("Composite EA output (GeoPackage)"),
                type=QgsProcessing.TypeVectorPolygon,
            )
        )
        
        

        
    # Helpers below isolate QGIS provider and geometry failure modes.
    # ------------------------------------------------------------------
    # basic helpers
    # ------------------------------------------------------------------
    # Log the feature count for an intermediate spatial layer during QA/debugging.
    def _log_fc(self, src, context, feedback, label):
        lyr = self._resolve_vector_layer(src, context, label)
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[COUNT] {label}: invalid")
            return
        feedback.pushInfo(f"[COUNT] {label}: {lyr.featureCount()} features")
    
    # Log field names/types to diagnose schema loss after QGIS processing steps.
    def _log_fields(self, src, context, feedback, label):
        lyr = self._resolve_vector_layer(src, context, label)
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[FIELDS] {label}: invalid layer")
            return
        desc = [f"{f.name()}<{f.typeName()}>" for f in lyr.fields()]
        feedback.pushInfo(f"[FIELDS] {label}: " + ", ".join(desc))
    
    # Execute a child Processing algorithm without the safe-difference guard.
    def _run_raw(self, alg_id, params, context, feedback, tag):
        # The child-algorithm flag permits use in the QGIS Processing script provider.
        return processing.run(
            alg_id,
            params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

    # Standard child-algorithm wrapper; forbid direct native:difference calls.
    # Use _safe_polygon_difference for fragile overlay geometries instead.
    # Do not use unguarded GEOS polygon differences directly from application code.
    # The safe wrapper preserves a reconstruction fallback for complex polygons.
    def _run(self, alg_id, params, context, feedback, tag):
        if alg_id == "native:difference":
            raise QgsProcessingException(
                "[Guard] Direct call to native:difference is not allowed. "
                "Use _safe_polygon_difference(...) instead."
            )
        return self._run_raw(alg_id, params, context, feedback, tag)
    
    # Persist an optional diagnostic snapshot in a separate named GeoPackage.
    def _save_debug_layer(self, src, debug_root_path, layer_name, context, feedback, tag="dbg_save"):
        """
        Save each debug layer as its own standalone GPKG.
        """
        lyr = self._resolve_vector_layer(src, context, f"{tag}_{layer_name}")
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[DEBUG SAVE] Invalid layer for {layer_name}")
            return None

        debug_dir = os.path.splitext(debug_root_path)[0] + "_debug_layers"
        os.makedirs(debug_dir, exist_ok=True)

        # Debug layers are separate GPKGs so they cannot overwrite final analysis layers.
        out_path = os.path.join(debug_dir, f"{layer_name}.gpkg")
        self._safe_delete_gpkg(out_path)

        try:
            self._run_raw(
                "native:savefeatures",
                {
                    "INPUT": lyr,
                    "OUTPUT": out_path,
                    "LAYER_NAME": layer_name,
                    "DATASOURCE_OPTIONS": "",
                    "LAYER_OPTIONS": "",
                },
                context,
                feedback,
                f"{tag}_{layer_name}",
            )
            out_uri = f"{out_path}|layername={layer_name}"
            feedback.pushInfo(f"[DEBUG SAVE] {layer_name}: {out_uri}")
            return out_uri
        except Exception as e:
            feedback.reportError(f"[DEBUG SAVE] Could not save {layer_name}: {e}")
            return None
        
    # Remove an existing GeoPackage and SQLite sidecars before overwriting.
    # SQLite journaling sidecars may survive interrupted GeoPackage writes.
    def _safe_delete_gpkg(self, path):
        for p in (path, path + "-shm", path + "-wal"):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    # Write/reopen a named result layer; preserve earlier layers in the same file.
    # The overwrite_file flag is true only for the first layer of a new GPKG.
    def _write_output_gpkg_layer(
        self,
        src,
        gpkg_path,
        layer_name,
        context,
        feedback,
        overwrite_file=False,
    ):
        """
        Write one named layer into the final multi-layer GeoPackage.

        The first output uses CreateOrOverwriteFile. Every later output uses
        CreateOrOverwriteLayer, which preserves all other layers in the same
        GeoPackage while safely replacing a same-named layer if necessary.
        """
        lyr = self._resolve_vector_layer(src, context, f"output_{layer_name}")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(
                f"[Output] Invalid source layer for {layer_name}."
            )

        # OGR write action must preserve all other named layers for subsequent outputs.
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"
        options.layerName = layer_name
        options.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteFile
            if overwrite_file
            else QgsVectorFileWriter.CreateOrOverwriteLayer
        )

        if hasattr(options, "feedback"):
            options.feedback = feedback

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            lyr,
            gpkg_path,
            context.transformContext(),
            options,
        )

        if isinstance(result, tuple):
            error_code = result[0]
            error_message = result[1] if len(result) > 1 else ""
            new_filename = result[2] if len(result) > 2 else gpkg_path
            new_layer = result[3] if len(result) > 3 else layer_name
        else:
            error_code = result
            error_message = ""
            new_filename = gpkg_path
            new_layer = layer_name

        if error_code != QgsVectorFileWriter.NoError:
            raise QgsProcessingException(
                f"[Output] Could not write {layer_name} to {gpkg_path}. "
                f"Writer error {error_code}: {error_message}"
            )

        # A successful writer status is insufficient; reopen through QGIS/OGR to check.
        output_uri = f"{gpkg_path}|layername={layer_name}"
        written = QgsVectorLayer(output_uri, layer_name, "ogr")
        if written is None or not written.isValid():
            raise QgsProcessingException(
                f"[Output] Writer reported success, but layer {layer_name} "
                f"could not be reopened from {gpkg_path}. "
                f"Writer returned file={new_filename}, layer={new_layer}."
            )

        feedback.pushInfo(
            f"[Output] Wrote {layer_name}: {written.featureCount():,} feature(s)"
        )
        return output_uri

    # Hard-check that every expected output layer is visible to the OGR provider.
    # Final registration check is mandatory even for optional output branches.
    def _verify_output_gpkg_layers(self, gpkg_path, layer_names, feedback):
        """Confirm that every expected final layer exists in the GeoPackage."""
        missing = []
        for layer_name in layer_names:
            uri = f"{gpkg_path}|layername={layer_name}"
            lyr = QgsVectorLayer(uri, layer_name, "ogr")
            if lyr is None or not lyr.isValid():
                missing.append(layer_name)

        if missing:
            raise QgsProcessingException(
                "[Output] Final GeoPackage verification failed. Missing layer(s): "
                + ", ".join(missing)
            )

        feedback.pushInfo(
            "[Output] GeoPackage verification passed: "
            + ", ".join(layer_names)
        )

    # Resolve a layer object, Processing result, or provider URI as a valid vector layer.
    def _resolve_vector_layer(self, src, context, name="tmp"):
        if isinstance(src, QgsVectorLayer):
            if src.isValid():
                return src
            raise QgsProcessingException(f"[resolve] Invalid QgsVectorLayer: {name}")

        lyr = None
        try:
            lyr = QgsProcessingUtils.mapLayerFromString(str(src), context)
        except Exception:
            lyr = None

        if lyr is None or not lyr.isValid():
            try:
                lyr = context.getMapLayer(str(src))
            except Exception:
                lyr = None

        if lyr is None or not lyr.isValid():
            lyr = QgsVectorLayer(str(src), name, "ogr")

        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"[resolve] Cannot load layer from: {src}")

        return lyr
    
    # Recognise Python/Qt null chronology values without interpreting them as dates.
    @staticmethod
    def _period_value_is_blank(raw):
        if raw is None:
            return True
        try:
            if hasattr(raw, "isNull") and raw.isNull():
                return True
        except Exception:
            pass
        txt = str(raw).strip()
        return txt == "" or txt.upper() in {"NULL", "NONE", "<NULL>"}

    # Convert validated canonical YYYY_MM_DD text into a Python calendar date.
    @staticmethod
    def _period_text_to_date(txt):
        return datetime.strptime(str(txt).replace("_", "-"), "%Y-%m-%d").date()

    # Format integer YYYYMMDD chronology values as canonical YYYY_MM_DD text.
    @staticmethod
    def _period_int_to_text(value):
        s = f"{int(value):08d}"
        return f"{s[0:4]}_{s[4:6]}_{s[6:8]}"

    # Validate one and only one date/period for all polygons in an EA source.
    # Inconsistent dates are an error, not a reason to pick the latest feature.
    # Canonical period validation avoids misaligning evidence between interval layers.
    def _layer_period_value(self, vlyr, period_field, feedback, min_year, max_year):
        """Return one validated end-date integer (YYYYMMDD) for an EA layer.

        Every nonblank parseable feature must describe the same canonical period.
        A rogue later value is therefore rejected rather than promoted by max().
        """
        idx = vlyr.fields().indexFromName(period_field)
        if idx == -1:
            raise QgsProcessingException(
                f"Field '{period_field}' not found in layer '{vlyr.name()}'"
            )

        canonical_periods = set()
        blank_count = 0
        invalid_examples = []
        total = 0

        # Reject mixed period values within one source; using max() would hide bad dates.
        for f in vlyr.getFeatures():
            total += 1
            raw = f[period_field]
            if self._period_value_is_blank(raw):
                blank_count += 1
                continue

            st, en = self._parse_period_value(raw)
            if en is None:
                if len(invalid_examples) < 5:
                    invalid_examples.append(repr(str(raw)))
                continue

            try:
                en_dt = self._period_text_to_date(en)
                st_dt = self._period_text_to_date(st) if st is not None else None
            except Exception as exc:
                if len(invalid_examples) < 5:
                    invalid_examples.append(f"{raw!r} ({exc})")
                continue

            if not (min_year <= en_dt.year <= max_year):
                raise QgsProcessingException(
                    f"[DATE QA] Layer '{vlyr.name()}' contains end date {en_dt} "
                    f"outside the permitted range {min_year}–{max_year}."
                )
            if st_dt is not None:
                if not (min_year <= st_dt.year <= max_year):
                    raise QgsProcessingException(
                        f"[DATE QA] Layer '{vlyr.name()}' contains start date {st_dt} "
                        f"outside the permitted range {min_year}–{max_year}."
                    )
                if en_dt <= st_dt:
                    raise QgsProcessingException(
                        f"[DATE QA] Layer '{vlyr.name()}' has a non-positive period: "
                        f"{st_dt} to {en_dt}."
                    )

            # The canonical date pair includes start/end if present, so conflicting ranges fail.
            canonical_periods.add((st, en))

        if invalid_examples:
            raise QgsProcessingException(
                f"[DATE QA] Layer '{vlyr.name()}' contains nonblank unparseable "
                f"values in '{period_field}'. Examples: " + ", ".join(invalid_examples)
            )

        if not canonical_periods:
            raise QgsProcessingException(
                f"No valid parseable dates found in '{period_field}' for layer '{vlyr.name()}'"
            )

        if len(canonical_periods) > 1:
            examples = ", ".join(
                f"{st or '<none>'}->{en}"
                for st, en in sorted(canonical_periods, key=lambda item: (item[1], item[0] or ""))[:10]
            )
            raise QgsProcessingException(
                f"[DATE QA] Layer '{vlyr.name()}' contains conflicting periods in "
                f"'{period_field}': {examples}. Each EA layer must represent one period."
            )

        # End date defines the sort key for successive EA intervals.
        st, en = next(iter(canonical_periods))
        if blank_count:
            feedback.reportError(
                f"[DATE QA] Layer '{vlyr.name()}': {blank_count:,} of {total:,} "
                f"feature(s) have blank '{period_field}' values; using the one "
                f"consistent nonblank period {st or '<none>'}->{en}."
            )
        feedback.pushInfo(
            f"[DATE QA] Layer '{vlyr.name()}': canonical period="
            f"{st or '<none>'}->{en}"
        )
        return int(en.replace("_", ""))
    
    # Safe count helper for optional or intermediate QGIS vector datasets.
    def _feature_count(self, src, context, tag="fc"):
        lyr = self._resolve_vector_layer(src, context, tag)
        if lyr is None or not lyr.isValid():
            return 0
        try:
            return lyr.featureCount()
        except Exception:
            return 0

    # Persist topology-only intermediates to Shapefile where field fidelity is not critical.
    # Strip feature-ID fields that can collide with regenerated provider identifiers.
    def _freeze_to_shp(self, layer, context, feedback, tag="freeze"):
        if isinstance(layer, QgsVectorLayer):
            v = layer
        else:
            v = None
            try:
                v = QgsProcessingUtils.mapLayerFromString(str(layer), context)
            except Exception:
                v = None

            if v is None or not v.isValid():
                try:
                    v = context.getMapLayer(str(layer))
                except Exception:
                    v = None

            if v is None or not v.isValid():
                v = QgsVectorLayer(str(layer), "freeze_src", "ogr")

            if v is None or not v.isValid():
                raise QgsProcessingException(
                    f"[freeze] Cannot load layer in _freeze_to_shp from: {layer}"
                )

        shp = os.path.join(tempfile.gettempdir(), f"{tag}_{uuid.uuid4().hex[:8]}.shp")

        # Source provider-ID fields are dropped to avoid conflicts after field refactoring.
        drop_names = set()
        try:
            flds = v.fields()
            for name in ("fid", "FID", "ogc_fid", "OGC_FID", "OBJECTID", "objectid"):
                if flds.indexFromName(name) != -1:
                    drop_names.add(name)
        except Exception:
            drop_names = set()

        if drop_names:
            mapping = []
            for f in v.fields():
                if f.name() in drop_names:
                    continue
                mapping.append(
                    {
                        "name": f.name(),
                        "type": f.type(),
                        "length": f.length() if hasattr(f, "length") else 254,
                        "precision": f.precision() if hasattr(f, "precision") else 0,
                        "expression": f'"{f.name()}"',
                    }
                )
            v_ref = self._run(
                "native:refactorfields",
                {
                    "INPUT": v,
                    "FIELDS_MAPPING": mapping,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"{tag}_dropfid",
            )["OUTPUT"]
        else:
            v_ref = v

        res = self._run(
            "native:savefeatures",
            {"INPUT": v_ref, "OUTPUT": shp},
            context,
            feedback,
            f"{tag}_save",
        )
        return res["OUTPUT"]
    
    # Freeze an intermediate with its full field widths and optional spatial index.
    # Use when later joins/metrics depend on exact schemas and long string fields.
    def _freeze_to_gpkg(
        self,
        layer,
        context,
        feedback,
        tag="freeze",
        layer_name=None,
        create_spatial_index=True,
    ):
        """
        Freeze a layer to a file-backed GeoPackage layer.

        Important:
        - write using plain .gpkg path + separate LAYER_NAME
        - reload using gpkg_path|layername=...
        - use this for helper-field / join-critical intermediates
        """
        if isinstance(layer, QgsVectorLayer):
            v = layer
        else:
            v = None
            try:
                v = QgsProcessingUtils.mapLayerFromString(str(layer), context)
            except Exception:
                v = None

            if v is None or not v.isValid():
                try:
                    v = context.getMapLayer(str(layer))
                except Exception:
                    v = None

            if v is None or not v.isValid():
                v = QgsVectorLayer(str(layer), "freeze_src", "ogr")

            if v is None or not v.isValid():
                raise QgsProcessingException(
                    f"[freeze_gpkg] Cannot load layer in _freeze_to_gpkg from: {layer}"
                )

        # Unique temporary paths prevent collisions among concurrent processing runs.
        gpkg = os.path.join(tempfile.gettempdir(), f"{tag}_{uuid.uuid4().hex[:8]}.gpkg")
        lyr_name = layer_name or re.sub(r"[^A-Za-z0-9_]+", "_", tag)[:40] or "layer"

        self._safe_delete_gpkg(gpkg)

        # Optionally strip provider PK baggage before writing
        drop_names = set()
        try:
            flds = v.fields()
            for name in ("fid", "FID", "ogc_fid", "OGC_FID", "OBJECTID", "objectid"):
                if flds.indexFromName(name) != -1:
                    drop_names.add(name)
        except Exception:
            drop_names = set()

        if drop_names:
            mapping = []
            for f in v.fields():
                if f.name() in drop_names:
                    continue
                mapping.append(
                    {
                        "name": f.name(),
                        "type": f.type(),
                        "length": f.length() if hasattr(f, "length") else 254,
                        "precision": f.precision() if hasattr(f, "precision") else 0,
                        "expression": f'"{f.name()}"',
                    }
                )
            v = self._run_raw(
                "native:refactorfields",
                {
                    "INPUT": v,
                    "FIELDS_MAPPING": mapping,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"{tag}_dropfid",
            )["OUTPUT"]
            v = self._resolve_vector_layer(v, context, f"{tag}_dropfid_rl")

        # Use a plain file path for writing and a |layername URI only for reading.
        # WRITE: plain gpkg path, layer name separate
        self._run_raw(
            "native:savefeatures",
            {
                "INPUT": v,
                "OUTPUT": gpkg,
                "LAYER_NAME": lyr_name,
                "DATASOURCE_OPTIONS": "",
                "LAYER_OPTIONS": "",
            },
            context,
            feedback,
            f"{tag}_save_gpkg",
        )

        # RELOAD: use provider URI
        out_uri = f"{gpkg}|layername={lyr_name}"
        frozen = QgsVectorLayer(out_uri, lyr_name, "ogr")

        if frozen is None or not frozen.isValid():
            try:
                frozen = QgsProcessingUtils.mapLayerFromString(out_uri, context)
            except Exception:
                frozen = None

        if frozen is None or not frozen.isValid():
            raise QgsProcessingException(
                f"[freeze_gpkg] Failed to reload frozen layer: {out_uri}"
            )

        # An index speeds downstream location joins; an index error is non-fatal here.
        if create_spatial_index:
            try:
                self._run_raw(
                    "native:createspatialindex",
                    {"INPUT": frozen},
                    context,
                    feedback,
                    f"{tag}_spatial_index",
                )
                frozen = QgsVectorLayer(out_uri, lyr_name, "ogr")
            except Exception as e:
                feedback.pushInfo(
                    f"[freeze_gpkg] Spatial index creation skipped/failed for {lyr_name}: {e}"
                )

        return out_uri
    
    # Dispatch intermediate storage to SHP or GPKG according to field-fidelity needs.
    def _freeze_intermediate(
        self,
        layer,
        context,
        feedback,
        tag,
        prefer_gpkg=False,
        layer_name=None,
        create_spatial_index=True,
    ):
        """
        Route freezing to GPKG or SHP depending on whether field fidelity matters.
        """
        if prefer_gpkg:
            return self._freeze_to_gpkg(
                layer,
                context,
                feedback,
                tag=tag,
                layer_name=layer_name,
                create_spatial_index=create_spatial_index,
            )

        shp = self._freeze_to_shp(layer, context, feedback, tag=tag)

        if create_spatial_index:
            try:
                self._run_raw(
                    "native:createspatialindex",
                    {"INPUT": shp},
                    context,
                    feedback,
                    f"{tag}_spatial_index",
                )
            except Exception as e:
                feedback.pushInfo(f"[freeze_intermediate] Spatial index creation skipped/failed for {tag}: {e}")

        return shp

    # Remove one stale helper column without failing when it is already absent.
    def _delete_field_if_exists(self, layer, field_name, context, feedback, tag="delfield"):
        lyr = self._resolve_vector_layer(layer, context, f"{tag}_chk")
        if field_name not in lyr.fields().names():
            return layer

        return self._run_raw(
            "native:deletecolumn",
            {
                "INPUT": layer,
                "COLUMN": [field_name],
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_{field_name}",
        )["OUTPUT"]

    # Remove previous EA step columns/temporary fields before reassignment.
    def _drop_fields_matching(self, layer, patterns, context, feedback, tag="dropmatch"):
        lyr = self._resolve_vector_layer(layer, context, f"{tag}_src")
        names = lyr.fields().names()

        to_drop = []
        for nm in names:
            for pat in patterns:
                if re.match(pat, nm):
                    to_drop.append(nm)
                    break

        if not to_drop:
            return layer

        feedback.pushInfo(f"[{tag}] Dropping fields: {to_drop}")
        return self._run_raw(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": to_drop,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_delete",
        )["OUTPUT"]

    # Add a named QGIS field only if it does not already exist.
    def _ensure_field(self, layer, name, qvariant_type, length=0, precision=0):
        from qgis.core import QgsField

        if layer.fields().indexOf(name) == -1:
            fld = QgsField(name, qvariant_type)
            if length:
                fld.setLength(length)
            if precision:
                fld.setPrecision(precision)
            layer.dataProvider().addAttributes([fld])
            layer.updateFields()
            
    # Count blank EA class values as a mapping/support diagnostic.
    # Use null counting for QA only; do not reinterpret missing class as a geomorphic state.
    def _count_nulls(self, layer_src, ea_field, context, label):
        lyr = self._resolve_vector_layer(layer_src, context, label)

        if lyr is None or not lyr.isValid():
            return 0, 0

        total = 0
        nulls = 0

        for ft in lyr.getFeatures():
            total += 1
            v = ft[ea_field]

            if v is None or str(v).strip() == "":
                nulls += 1

        return total, nulls     

    # ------------------------------------------------------------------
    # geometry sanitation / difference fallback
    # ------------------------------------------------------------------

    # Keep non-empty polygonal geometry, attempt QGIS geometry repair, split multipart.
    # The min_area filter is optional: zero preserves small polygons for topology.
    def _sanitize_polygon_layer(self, src, context, feedback, tag, min_area=0.0):
        """
        Safer polygon sanitation for assemblage workflows.
        Does not apply area filtering unless min_area > 0.
        Returns a temporary layer, not a forced SHP freeze.
        """
        lyr = self._resolve_vector_layer(src, context, f"{tag}_src")

        # Filtering retains only polygon geometry; min_area=0 does not remove small cells.
        expr = (
            "geometry_type($geometry) IN ('Polygon','MultiPolygon') "
            "AND $geometry IS NOT NULL "
            "AND NOT is_empty($geometry)"
        )
        if min_area is not None and min_area > 0:
            expr += f" AND $area > {min_area}"

        a = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": lyr,
                "EXPRESSION": expr,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_poly0",
        )["OUTPUT"]

        # Fix geometries before multipart splitting; process result remains temporary.
        b = self._run_raw(
            "native:fixgeometries",
            {"INPUT": a, "METHOD": 1, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_fix0",
        )["OUTPUT"]

        c = self._run_raw(
            "native:multiparttosingleparts",
            {"INPUT": b, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_single",
        )["OUTPUT"]

        d = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": c,
                "EXPRESSION": expr,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_poly1",
        )["OUTPUT"]

        return d

    # Reconstruct INPUT minus OVERLAY from a polygonized shared boundary network.
    # Use spatial membership tests when GEOS difference fails; restore source fields.
    # Slow contingency path for difference: polygonize combined boundaries then
    # classify representative points as inside input and outside overlay.
    def _fallback_polygonized_difference(self, in_src, ov_src, context, feedback, tag, min_area=0.0):
        # Choose a non-provider attribute for spatial membership joins in the fallback.
        def _first_real_field(layer_src, label):
            lyr = self._resolve_vector_layer(layer_src, context, label)
            names = [
                f.name() for f in lyr.fields()
                if f.name().lower() not in ("fid", "objectid", "ogc_fid")
            ]
            if not names:
                raise QgsProcessingException(
                    f"[{tag} fallback] No usable attribute fields found on {label}."
                )
            return names[0]

        # Try a persistent geometry index; fall back to the original layer on failure.
        def _safe_spatial_index(src, stage_name):
            try:
                shp = self._freeze_to_shp(src, context, feedback, f"{tag}_{stage_name}_idxsrc")
                self._run_raw(
                    "native:createspatialindex",
                    {"INPUT": shp},
                    context, feedback, f"{tag}_{stage_name}_idx",
                )
                return shp
            except Exception:
                return src

        # Polygon boundaries from both inputs delineate the complete subtraction fabric.
        in_lines = self._run_raw(
            "native:polygonstolines",
            {"INPUT": in_src, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_fb_in_lines",
        )["OUTPUT"]

        ov_lines = self._run_raw(
            "native:polygonstolines",
            {"INPUT": ov_src, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_fb_ov_lines",
        )["OUTPUT"]

        in_lyr = self._resolve_vector_layer(in_src, context, f"{tag}_in_src")
        ref_crs = in_lyr.crs() if in_lyr and in_lyr.isValid() else None

        merged_lines = self._run(
            "native:mergevectorlayers",
            {
                "LAYERS": [in_lines, ov_lines],
                "CRS": ref_crs,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_merge_lines",
        )["OUTPUT"]

        merged_lines = self._freeze_to_shp(merged_lines, context, feedback, f"{tag}_fb_lines_f")

        poly_all = self._run_raw(
            "native:polygonize",
            {
                "INPUT": merged_lines,
                "KEEP_FIELDS": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_polygonize",
        )["OUTPUT"]

        poly_all = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": poly_all,
                "EXPRESSION": (
                    "$geometry IS NOT NULL "
                    "AND NOT is_empty($geometry) "
                    "AND geometry_type($geometry) IN ('Polygon','MultiPolygon') "
                    f"AND $area > {min_area}"
                ),
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_poly_clean",
        )["OUTPUT"]

        poly_chk = self._resolve_vector_layer(poly_all, context, f"{tag}_fb_poly_chk")
        feedback.pushInfo(f"[Diff fallback] {tag}: polygonized pieces kept = {poly_chk.featureCount()}")

        if poly_chk.featureCount() == 0:
            return poly_all

        poly_id = self._run_raw(
            "native:addautoincrementalfield",
            {
                "INPUT": poly_all,
                "FIELD_NAME": "_PID",
                "START": 1,
                "GROUP_FIELDS": [],
                "SORT_EXPRESSION": "",
                "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_poly_id",
        )["OUTPUT"]

        # Point-on-surface avoids centroid positions lying outside concave polygons.
        pos = self._run_raw(
            "native:pointonsurface",
            {
                "INPUT": poly_id,
                "ALL_PARTS": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_pos",
        )["OUTPUT"]

        in_src_idx = _safe_spatial_index(in_src, "fb_in")
        ov_src_idx = _safe_spatial_index(ov_src, "fb_ov")

        in_field = _first_real_field(in_src_idx, "in_src")
        ov_field = _first_real_field(ov_src_idx, "ov_src")

        pos_in = self._run_raw(
            "native:joinattributesbylocation",
            {
                "INPUT": pos,
                "JOIN": in_src_idx,
                "PREDICATE": [5],
                "JOIN_FIELDS": [in_field],
                "METHOD": 0,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "IN_",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_join_in",
        )["OUTPUT"]

        pos_both = self._run_raw(
            "native:joinattributesbylocation",
            {
                "INPUT": pos_in,
                "JOIN": ov_src_idx,
                "PREDICATE": [5],
                "JOIN_FIELDS": [ov_field],
                "METHOD": 0,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "OV_",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_join_ov",
        )["OUTPUT"]

        pos_layer = self._resolve_vector_layer(pos_both, context, f"{tag}_fb_pos_both")
        pos_names = pos_layer.fields().names()

        expected_in = f"IN_{in_field}"
        expected_ov = f"OV_{ov_field}"

        in_join_actual = next((n for n in pos_names if n == expected_in or n.startswith("IN_")), None)
        ov_join_actual = next((n for n in pos_names if n == expected_ov or n.startswith("OV_")), None)

        if in_join_actual is None or ov_join_actual is None:
            raise QgsProcessingException(
                f"[{tag} fallback] Expected joined fields not found. Fields present: {pos_names}"
            )

        # Keep polygons inside original INPUT but not inside the subtraction OVERLAY.
        keep_pts = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": pos_both,
                "EXPRESSION": f"\"{in_join_actual}\" IS NOT NULL AND \"{ov_join_actual}\" IS NULL",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_keep_pts",
        )["OUTPUT"]

        keep_chk = self._resolve_vector_layer(keep_pts, context, f"{tag}_fb_keep_chk")
        if keep_chk.featureCount() == 0:
            return self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": poly_id,
                    "EXPRESSION": "0 = 1",
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_fb_empty",
            )["OUTPUT"]

        kept_polys = self._run_raw(
            "native:joinattributestable",
            {
                "INPUT": poly_id,
                "FIELD": "_PID",
                "INPUT_2": keep_pts,
                "FIELD_2": "_PID",
                "FIELDS_TO_COPY": ["_PID"],
                "METHOD": 1,
                "DISCARD_NONMATCHING": True,
                "PREFIX": "K_",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_joinback",
        )["OUTPUT"]

        kept_pos = self._run_raw(
            "native:pointonsurface",
            {
                "INPUT": kept_polys,
                "ALL_PARTS": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_kept_pos",
        )["OUTPUT"]

        rejoined_pts = self._run_raw(
            "native:joinattributesbylocation",
            {
                "INPUT": kept_pos,
                "JOIN": in_src_idx,
                "PREDICATE": [5],
                "JOIN_FIELDS": [],
                "METHOD": 0,
                "DISCARD_NONMATCHING": True,
                "PREFIX": "",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_rejoin_input_attrs",
        )["OUTPUT"]

        restored_polys = self._run_raw(
            "native:joinattributestable",
            {
                "INPUT": kept_polys,
                "FIELD": "_PID",
                "INPUT_2": rejoined_pts,
                "FIELD_2": "_PID",
                "FIELDS_TO_COPY": [],
                "METHOD": 1,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_fb_restore_attrs",
        )["OUTPUT"]

        cleaned_restore = restored_polys
        for fld in ["_PID", "K__PID", "_PID_2", "K__PID_2"]:
            cleaned_restore = self._delete_field_if_exists(
                cleaned_restore, fld, context, feedback, f"{tag}_cleanup"
            )

        return cleaned_restore

    # Sanitize both geometries, attempt native difference, then polygonized fallback.
    # The fallback is a geometry workaround, not independent map validation.
    # GEOS difference fails can be topology-related; both inputs are repaired first.
    def _safe_polygon_difference(self, input_src, overlay_src, context, feedback, tag):
        min_area = 0.0

        # Canonicalise polygon geometry before attempting a robust subtraction.
        def _sanitize(src, stage):
            expr = (
                "geometry_type($geometry) IN ('Polygon','MultiPolygon') "
                "AND $geometry IS NOT NULL "
                "AND NOT is_empty($geometry)"
            )
            if min_area is not None and min_area > 0:
                expr += f" AND $area > {min_area}"

            a = self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": src,
                    "EXPRESSION": expr,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_{stage}_poly0",
            )["OUTPUT"]

            b = self._run_raw(
                "native:fixgeometries",
                {"INPUT": a, "METHOD": 1, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                context, feedback, f"{tag}_{stage}_fix0",
            )["OUTPUT"]

            c = self._run_raw(
                "native:multiparttosingleparts",
                {"INPUT": b, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                context, feedback, f"{tag}_{stage}_single",
            )["OUTPUT"]

            d = self._run_raw(
                "native:buffer",
                {
                    "INPUT": c,
                    "DISTANCE": 0.0,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "DISSOLVE": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_{stage}_buf0",
            )["OUTPUT"]

            e = self._run_raw(
                "native:fixgeometries",
                {"INPUT": d, "METHOD": 1, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                context, feedback, f"{tag}_{stage}_fix1",
            )["OUTPUT"]

            f = self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": e,
                    "EXPRESSION": expr,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_{stage}_poly1",
            )["OUTPUT"]

            return self._freeze_to_shp(f, context, feedback, f"{tag}_{stage}_frozen")

        # Both input and overlay must use consistent geometry sanitation before subtraction.
        fixed_in_poly = _sanitize(input_src, "in")
        fixed_ov_poly = _sanitize(overlay_src, "ov")

        in_lyr = self._resolve_vector_layer(fixed_in_poly, context, f"{tag}_in_chk")
        ov_lyr = self._resolve_vector_layer(fixed_ov_poly, context, f"{tag}_ov_chk")

        if not in_lyr.isValid() or in_lyr.featureCount() == 0:
            return fixed_in_poly
        if not ov_lyr.isValid() or ov_lyr.featureCount() == 0:
            return fixed_in_poly

        # Fast path: ordinary native:difference on sanitized polygon geometry.
        try:
            diff_tmp = self._run_raw(
                "native:difference",
                {
                    "INPUT": fixed_in_poly,
                    "OVERLAY": fixed_ov_poly,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_diff",
            )["OUTPUT"]

            diff_poly = _sanitize(diff_tmp, "out")
            return diff_poly

        # If fast subtraction fails, try boundary-network subtraction and write diagnostics on failure.
        except Exception as e:
            feedback.reportError(
                f"[Diff] native:difference failed for {tag}; trying fallback. Error: {e}"
            )

        try:
            fb = self._fallback_polygonized_difference(
                fixed_in_poly, fixed_ov_poly, context, feedback, tag, min_area=min_area
            )
            fb = _sanitize(fb, "fb_out")
            return fb
        except Exception as e2:
            dbg_in = self._freeze_to_shp(fixed_in_poly, context, feedback, f"{tag}_FAIL_INPUT")
            dbg_ov = self._freeze_to_shp(fixed_ov_poly, context, feedback, f"{tag}_FAIL_OVERLAY")
            raise QgsProcessingException(
                f"[Diff] Both native:difference and fallback polygonized difference FAILED for {tag}\n"
                f"Debug layers written:\n  INPUT: {dbg_in}\n  OVERLAY: {dbg_ov}\n"
                f"Fallback error: {e2}"
            )
    # Fill missing EA columns in bounded provider-update batches.
    # Existing source-assigned values and geometry are not replaced.
    def _fill_remaining_step_nulls_neutral(self, fabric_src, ea_fields, context, feedback, fill_value="stable_floodplain"):
        """
        Fill residual blank EA fields using provider-level attribute batches.

        Geometry and already assigned values are unchanged. The file-backed
        working fabric is updated in place, so no additional full GeoPackage
        copy is created. Features are read in bounded FID chunks so SQLite does
        not hold a long read cursor while an attribute batch is written.
        """
        lyr = self._resolve_vector_layer(fabric_src, context, "neutral_null_fill")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException("[NeutralFill] invalid fabric")

        valid_fields = [f for f in ea_fields if lyr.fields().indexFromName(f) >= 0]
        if not valid_fields:
            feedback.pushInfo("[NeutralFill] no EA fields found; nothing to fill")
            return fabric_src

        field_indices = {name: lyr.fields().indexFromName(name) for name in valid_fields}
        provider = lyr.dataProvider()
        batch_size = 5000
        changed_features = 0
        changed_values = 0
        t0 = time.perf_counter()

        # Collect stable provider feature IDs so each batch can read then write safely.
        fid_request = QgsFeatureRequest()
        fid_request.setNoAttributes()
        fid_request.setFlags(QgsFeatureRequest.NoGeometry)
        feature_ids = [feature.id() for feature in lyr.getFeatures(fid_request)]

        for offset in range(0, len(feature_ids), batch_size):
            chunk_ids = feature_ids[offset:offset + batch_size]
            request = QgsFeatureRequest()
            request.setFilterFids(list(chunk_ids))
            request.setSubsetOfAttributes(valid_fields, lyr.fields())
            request.setFlags(QgsFeatureRequest.NoGeometry)

            # Only true unassigned values are filled; geometry and already mapped classes persist.
            changes_by_fid = {}
            for feat in lyr.getFeatures(request):
                changes = {}
                for name in valid_fields:
                    value = feat[name]
                    if value is None or str(value).strip() == "":
                        changes[field_indices[name]] = fill_value

                if changes:
                    changes_by_fid[feat.id()] = changes
                    changed_features += 1
                    changed_values += len(changes)

            if changes_by_fid and not provider.changeAttributeValues(changes_by_fid):
                raise QgsProcessingException("[NeutralFill] provider batch update failed")

        lyr.updateFields()
        feedback.pushInfo(
            f"[NeutralFill] filled {changed_values:,} blank values in "
            f"{changed_features:,} features as {fill_value} "
            f"({time.perf_counter() - t0:.1f} s)"
        )
        return fabric_src

    # Measure DIRECT temporal EA coverage before inferred classes are introduced.
    # VALID_OBS additionally requires evidence across early, middle and late record.
    def _add_assignment_support_fields(
        self,
        layer,
        context,
        feedback,
        min_valid_fraction=0.75,
        tag="assign_support",
    ):
        """
        Add source-assignment diagnostics before any background or unresolved
        values are filled.

        N_ASSIGNED / P_ASSIGNED describe direct support from the source EA layers,
        not values subsequently inferred from the corridor. VALID_OBS requires the
        requested minimum source-assignment fraction and at least one supported
        observation in each non-empty early, middle and late third of the record.
        """
        lyr = self._resolve_vector_layer(layer, context, f"{tag}_src")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"[{tag}] invalid layer")

        # Identify EA_Class_i fields and their true chronological order.
        ea_fields = sorted(
            [f.name() for f in lyr.fields() if re.match(r"^EA_Class_\d+$", f.name(), re.IGNORECASE)],
            key=lambda x: int(re.search(r"\d+$", x).group()),
        )
        if not ea_fields:
            raise QgsProcessingException(f"[{tag}] No EA_Class_i fields found.")

        min_valid_fraction = min(1.0, max(0.0, float(min_valid_fraction)))
        n_steps = len(ea_fields)
        # Even sampling-count thirds are QA periods, not geomorphic process regimes.
        b1 = max(1, int(math.ceil(n_steps / 3.0)))
        b2 = max(b1, int(math.ceil((2.0 * n_steps) / 3.0)))
        b2 = min(n_steps, b2)
        slices = [(0, b1), (b1, b2), (b2, n_steps)]

        field_defs = [
            ("N_ASSIGNED", QVariant.Int, 0, 0),
            ("P_ASSIGNED", QVariant.Double, 20, 6),
            ("VALID_FRAC", QVariant.Double, 20, 6),
            ("FULL_SUPP", QVariant.Int, 0, 0),
            ("SUPP_EARLY", QVariant.Int, 0, 0),
            ("SUPP_MID", QVariant.Int, 0, 0),
            ("SUPP_LATE", QVariant.Int, 0, 0),
            ("EA_EVER", QVariant.Int, 0, 0),
            ("VALID_OBS", QVariant.Int, 0, 0),
            ("N_SC_SUPP", QVariant.Int, 0, 0),
            ("N_SI_SUPP", QVariant.Int, 0, 0),
            ("N_FP_SUPP", QVariant.Int, 0, 0),
            ("N_ER_SUPP", QVariant.Int, 0, 0),
            ("N_DEP_SUPP", QVariant.Int, 0, 0),
            ("N_NULL_SUPP", QVariant.Int, 0, 0),
        ]
        new_fields = []
        existing = set(lyr.fields().names())
        for name, typ, length, precision in field_defs:
            if name in existing:
                continue
            fld = QgsField(name, typ)
            if length:
                fld.setLength(length)
            if precision:
                fld.setPrecision(precision)
            new_fields.append(fld)
        if new_fields and not lyr.dataProvider().addAttributes(new_fields):
            raise QgsProcessingException(f"[{tag}] Could not add support fields")
        lyr.updateFields()

        idx = {f.name(): i for i, f in enumerate(lyr.fields())}
        provider = lyr.dataProvider()
        batch_size = 5000
        fid_request = QgsFeatureRequest()
        fid_request.setNoAttributes()
        fid_request.setFlags(QgsFeatureRequest.NoGeometry)
        feature_ids = [ft.id() for ft in lyr.getFeatures(fid_request)]
        processed = 0

        # Normalise EA class labels solely for source-support counting.
        def clean(value):
            if value is None:
                return ""
            return str(value).strip().lower().replace(" ", "_").replace("-", "_")

        # Return false for explicit no-data tokens, not simply empty geometry.
        def assigned(value):
            return value not in {"", "null", "none", "nan", "no_data", "nodata"}

        # Compute support fractions directly from raw values; no background inference yet.
        for offset in range(0, len(feature_ids), batch_size):
            req = QgsFeatureRequest()
            req.setFilterFids(list(feature_ids[offset:offset + batch_size]))
            req.setSubsetOfAttributes(ea_fields, lyr.fields())
            req.setFlags(QgsFeatureRequest.NoGeometry)
            changes = {}

            for ft in lyr.getFeatures(req):
                vals = [clean(ft[name]) for name in ea_fields]
                flags = [assigned(v) for v in vals]
                n_assigned = sum(flags)
                n_null = n_steps - n_assigned
                p_assigned = float(n_assigned) / float(max(1, n_steps))
                # VALID_OBS combines total fraction and temporal spread of supported classes.
                third_counts = [sum(flags[a:b]) if b > a else 0 for a, b in slices]
                temporal_ok = all(count > 0 for count, (a, b) in zip(third_counts, slices) if b > a)
                valid_obs = 1 if p_assigned >= min_valid_fraction and temporal_ok else 0

                n_sc = sum(v in {"stable_channel", "channel", "channel_surface", "active_channel", "water", "inchannel_surface"} for v in vals)
                n_si = sum(v in {"stable_island", "island", "island_surface"} for v in vals)
                n_fp = sum(v in {"stable_floodplain", "inactive_floodplain", "persistent_floodplain", "floodplain", "stable_fp"} for v in vals)
                n_er = sum(v in {"erosion", "island_erosion", "island_ero", "isl_erosion"} for v in vals)
                n_dep = sum(v in {"deposition", "island_deposition", "island_dep", "isl_deposition", "migration_deposition", "infill_deposition"} for v in vals)

                changes[ft.id()] = {
                    idx["N_ASSIGNED"]: n_assigned,
                    idx["P_ASSIGNED"]: p_assigned,
                    idx["VALID_FRAC"]: p_assigned,
                    idx["FULL_SUPP"]: 1 if n_assigned == n_steps else 0,
                    idx["SUPP_EARLY"]: third_counts[0],
                    idx["SUPP_MID"]: third_counts[1],
                    idx["SUPP_LATE"]: third_counts[2],
                    idx["EA_EVER"]: 1 if n_assigned > 0 else 0,
                    idx["VALID_OBS"]: valid_obs,
                    idx["N_SC_SUPP"]: n_sc,
                    idx["N_SI_SUPP"]: n_si,
                    idx["N_FP_SUPP"]: n_fp,
                    idx["N_ER_SUPP"]: n_er,
                    idx["N_DEP_SUPP"]: n_dep,
                    idx["N_NULL_SUPP"]: n_null,
                }
                processed += 1

            if changes and not provider.changeAttributeValues(changes):
                raise QgsProcessingException(f"[{tag}] Provider batch update failed")

        feedback.pushInfo(
            f"[{tag}] Source support calculated for {processed:,} cells; "
            f"VALID_OBS threshold={min_valid_fraction:.2f} with early/middle/late support."
        )
        return self._freeze_to_gpkg(
            lyr,
            context,
            feedback,
            tag=f"{tag}_frozen",
            layer_name="support_checked",
            create_spatial_index=True,
        )

    # Use explicit background evidence to classify residual corridor fabric safely.
    # Prevent background overwrite within historical belt or active/storage support.
    def _apply_corridor_background_policy(
        self,
        layer,
        period_values,
        context,
        feedback,
        analysis_corridor_enabled=False,
        background_mask=None,
        historical_active_belt=None,
        assume_corridor_background=False,
        tag="corridor_support",
    ):
        """Apply explicit background and historical-belt protection.

        The explicit background mask is authoritative for background assignment;
        zero EA support is retained only as a QA diagnostic. Cells in the dissolved
        historical Active Domain belt are never assigned as background. A mask cell
        containing active/storage EA evidence is preserved and flagged BG_CONFLICT.
        """
        # Attach a temporary ID for joining spatial support masks back to unchanged fabric.
        tagged = self._run_raw(
            "native:addautoincrementalfield",
            {
                "INPUT": layer, "FIELD_NAME": "_SUPP_ID", "START": 1,
                "GROUP_FIELDS": [], "SORT_EXPRESSION": "", "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_addid",
        )["OUTPUT"]
        tagged = self._freeze_to_gpkg(
            tagged, context, feedback, tag=f"{tag}_tagged",
            layer_name="corridor_support_work", create_spatial_index=True,
        )
        lyr = self._resolve_vector_layer(tagged, context, f"{tag}_rl")
        ea_fields = sorted(
            [f.name() for f in lyr.fields() if re.match(r"^EA_Class_\d+$", f.name(), re.IGNORECASE)],
            key=lambda x: int(re.search(r"\d+$", x).group()),
        )
        period_fields = [f"Period_{i}" for i in range(1, len(ea_fields) + 1)]
        if len(period_values) != len(period_fields):
            raise QgsProcessingException(
                f"[{tag}] Chronology length mismatch: {len(period_values)} values for {len(period_fields)} state fields."
            )
        period_lookup = dict(zip(period_fields, period_values))

        # Representative points allow cheap first-pass testing against mask polygons.
        points = self._run_raw(
            "native:pointonsurface",
            {"INPUT": tagged, "ALL_PARTS": False, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_points",
        )["OUTPUT"]

        # Select fabric representative points falling within an evidence mask.
        def ids_inside(mask, label):
            if mask is None:
                return set()
            inside = self._run_raw(
                "native:extractbylocation",
                {"INPUT": points, "PREDICATE": [0], "INTERSECT": mask,
                 "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                context, feedback, f"{tag}_{label}",
            )["OUTPUT"]
            ilyr = self._resolve_vector_layer(inside, context, f"{tag}_{label}_rl")
            req = QgsFeatureRequest()
            req.setSubsetOfAttributes(["_SUPP_ID"], ilyr.fields())
            req.setFlags(QgsFeatureRequest.NoGeometry)
            return {int(ft["_SUPP_ID"]) for ft in ilyr.getFeatures(req) if ft["_SUPP_ID"] is not None}

        # A cell inside the historical active belt must not be assigned inherited SF by default.
        background_ids = ids_inside(background_mask, "inside_background")
        belt_ids = ids_inside(historical_active_belt, "inside_historical_belt")
        if background_ids:
            feedback.pushInfo(f"[{tag}] Explicit background-mask candidates: {len(background_ids):,}")
        if belt_ids:
            feedback.pushInfo(f"[{tag}] Historical Active Domain protected cells: {len(belt_ids):,}")

        for name, typ in [
            ("IN_CORRIDOR", QVariant.Int), ("BG_FP", QVariant.Int),
            ("ZERO_SOURCE", QVariant.Int), ("BG_CONFLICT", QVariant.Int),
            ("BELT_PROTECTED", QVariant.Int), ("SUPPORT_CL", QVariant.String),
            ("BG_SOURCE", QVariant.String),
        ]:
            if lyr.fields().indexFromName(name) < 0:
                fld = QgsField(name, typ)
                if typ == QVariant.String:
                    fld.setLength(48)
                if not lyr.dataProvider().addAttributes([fld]):
                    raise QgsProcessingException(f"[{tag}] Could not add {name}")
        lyr.updateFields()
        idx = {f.name(): i for i, f in enumerate(lyr.fields())}
        attrs = ["_SUPP_ID", "N_ASSIGNED", "P_ASSIGNED", "VALID_OBS"] + ea_fields + [p for p in period_fields if p in idx]

        # Avoid treating a QGIS null placeholder as meaningful EA evidence.
        def blank(value):
            if value is None:
                return True
            try:
                if value.isNull():
                    return True
            except (AttributeError, TypeError):
                pass
            return str(value).strip().upper() in {"", "NULL", "<NULL>", "NONE"}

        # Translate raw EA classes into coarse support-state categories for conflict tests.
        # These raw-class associations are a conflict screen, not the final state chronology.
        def canonical(value):
            v = "" if blank(value) else str(value).strip().lower().replace("-", "_").replace(" ", "_")
            if v in {"erosion", "bank_erosion", "channel_erosion", "island_erosion", "stable_channel", "channel", "water", "inchannel_surface", "active_domain", "active_channel"}:
                return "ACTIVE_DOMAIN"
            if v in {"deposition", "bank_deposition", "channel_deposition", "island_deposition", "depositional_storage", "storage", "new_bar", "bar", "bar_storage"}:
                return "DEPOSITIONAL_STORAGE"
            if v in {"stable_floodplain", "inactive_floodplain", "persistent_floodplain", "stabilised_floodplain", "stabilized_floodplain", "floodplain", "stable_island", "vegetated_island"}:
                return "STABILISED_FLOODPLAIN"
            return "UNRESOLVED"

        provider = lyr.dataProvider()
        req0 = QgsFeatureRequest(); req0.setNoAttributes(); req0.setFlags(QgsFeatureRequest.NoGeometry)
        fids = [ft.id() for ft in lyr.getFeatures(req0)]
        qa = {}
        for offset in range(0, len(fids), 5000):
            req = QgsFeatureRequest(); req.setFilterFids(list(fids[offset:offset + 5000]))
            req.setSubsetOfAttributes(attrs, lyr.fields()); req.setFlags(QgsFeatureRequest.NoGeometry)
            changes = {}
            # Apply precedence: belt and process support can veto background assignment.
            for ft in lyr.getFeatures(req):
                sid = int(ft["_SUPP_ID"])
                n_assigned = int(ft["N_ASSIGNED"] or 0)
                p_assigned = float(ft["P_ASSIGNED"] or 0.0)
                zero_source = 1 if n_assigned == 0 else 0
                in_belt = sid in belt_ids
                in_mask = sid in background_ids
                recognised = [canonical(ft[name]) for name in ea_fields]
                has_active_storage = any(x in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"} for x in recognised)
                # Explicit background is accepted only where belt/process evidence does not conflict.
                # Corridor-only residual stays unresolved unless the user explicitly opts in.
                bg_conflict = 1 if in_mask and (in_belt or has_active_storage) else 0
                is_bg = False
                bg_source = "none"
                if in_mask and not in_belt and not has_active_storage:
                    is_bg = True
                    bg_source = "explicit_background_mask"
                elif background_mask is None and analysis_corridor_enabled and assume_corridor_background and zero_source and not in_belt:
                    is_bg = True
                    bg_source = "corridor_assumption"

                valid_obs = int(ft["VALID_OBS"] or 0)
                if is_bg:
                    support_class = "background_floodplain"
                    valid_obs = 1
                elif in_belt:
                    support_class = "historical_belt_supported" if not zero_source else "historical_belt_unresolved"
                elif bg_conflict:
                    support_class = "background_mask_conflict"
                elif zero_source and analysis_corridor_enabled:
                    support_class = "corridor_unresolved"
                elif zero_source:
                    support_class = "unassigned"
                elif valid_obs == 1:
                    support_class = "ea_supported_valid"
                else:
                    support_class = "ea_supported_partial"

                # Record evidence source and conflict status before any EA null class replacement.
                row = {
                    idx["IN_CORRIDOR"]: 1 if analysis_corridor_enabled else 0,
                    idx["BG_FP"]: 1 if is_bg else 0,
                    idx["ZERO_SOURCE"]: zero_source,
                    idx["BG_CONFLICT"]: bg_conflict,
                    idx["BELT_PROTECTED"]: 1 if in_belt else 0,
                    idx["SUPPORT_CL"]: support_class,
                    idx["BG_SOURCE"]: bg_source,
                    idx["VALID_OBS"]: valid_obs,
                    idx["VALID_FRAC"]: 1.0 if is_bg else p_assigned,
                }
                # Fill a validated background as stable across each dated EA step; otherwise mark gaps.
                for i, ea_name in enumerate(ea_fields):
                    pd_name = period_fields[i]
                    if is_bg:
                        row[idx[ea_name]] = "stable_floodplain"
                        if pd_name in idx:
                            row[idx[pd_name]] = period_lookup[pd_name]
                    elif blank(ft[ea_name]):
                        row[idx[ea_name]] = "reworked_unresolved"
                changes[ft.id()] = row
                qa[support_class] = qa.get(support_class, 0) + 1
            if changes and not provider.changeAttributeValues(changes):
                raise QgsProcessingException(f"[{tag}] Provider batch update failed")

        for key in sorted(qa):
            feedback.pushInfo(f"[{tag}] {key}: {qa[key]:,} cells")
        if qa.get("background_mask_conflict", 0):
            feedback.pushWarning(
                f"[{tag}] {qa['background_mask_conflict']:,} cells intersect the background mask but contain historical-belt or active/storage evidence; they were not overwritten."
            )
        if analysis_corridor_enabled and background_mask is None and not assume_corridor_background:
            feedback.pushInfo(f"[{tag}] No explicit background mask: corridor residual remains unresolved (safe main-analysis setting).")

        cleaned = self._delete_field_if_exists(tagged, "_SUPP_ID", context, feedback, f"{tag}_cleanup")
        final_path = self._freeze_to_gpkg(
            cleaned, context, feedback, tag=f"{tag}_final",
            layer_name="corridor_support_final", create_spatial_index=True,
        )
        return final_path

    # Seed independent T0 state and provenance; preserve original EA evidence columns.
    # Inherited non-active states are left-censored, with no invented past event.
    # T0 is a pre-record provenance seed, separate from observed process transitions.
    def _apply_initial_state_policy(
        self, layer, context, feedback, *, initial_mode=0, initial_layer=None,
        initial_state_field="INIT_STATE", initial_context_field="",
        active_values=None, storage_values=None, stable_values=None,
        tag="initial_state",
    ):
        """Attach a generic T0 state/provenance seed without modifying EA_Class_i.

        The historical Active Domain union is deliberately not used as a T0 state
        classifier. Explicit background cells remain prior Stabilised Floodplain.
        An optional T0 classification can distinguish prior storage and stable islands.
        In conservative mode all other T0 surfaces remain Prior Unknown; the
        floodplain-default mode is an explicit user assumption suitable only where
        that geomorphic interpretation is defensible.
        """
        tagged = self._run_raw(
            "native:addautoincrementalfield",
            {
                "INPUT": layer, "FIELD_NAME": "_INIT_ID", "START": 1,
                "GROUP_FIELDS": [], "SORT_EXPRESSION": "", "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_addid",
        )["OUTPUT"]
        tagged = self._freeze_to_gpkg(
            tagged, context, feedback, tag=f"{tag}_tagged",
            layer_name="initial_state_work", create_spatial_index=True,
        )
        lyr = self._resolve_vector_layer(tagged, context, f"{tag}_rl")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"[{tag}] Could not resolve assemblage fabric.")

        # Normalise T0 labels while preserving original source text in INIT_SOURCE.
        def norm(v):
            if v is None:
                return ""
            try:
                if hasattr(v, "isNull") and v.isNull():
                    return ""
            except Exception:
                pass
            return str(v).strip().lower().replace("-", "_").replace(" ", "_")

        # Parse the user-configured comma-separated T0 class dictionary.
        def csvset(values):
            return {norm(x) for x in str(values or "").split(",") if norm(x)}

        # Set values are user-configurable; class mapping is not guessed from river names.
        active_set = csvset(active_values)
        storage_set = csvset(storage_values)
        stable_set = csvset(stable_values)

        # Resolve user-described T0 classes into three-state labels or UNRESOLVED.
        def classify(raw):
            v = norm(raw)
            if v in active_set:
                return "ACTIVE_DOMAIN"
            if v in storage_set:
                return "DEPOSITIONAL_STORAGE"
            if v in stable_set:
                return "STABILISED_FLOODPLAIN"
            return "UNRESOLVED"

        # Retain island/bar/channel/floodplain context separately from primary state.
        def context_from(raw_state, raw_context, state):
            c = norm(raw_context)
            if c:
                return c
            v = norm(raw_state)
            if "island" in v:
                return "island"
            if "bar" in v or "storage" in v or "deposition" in v:
                return "bar_storage"
            if "channel" in v or "water" in v or state == "ACTIVE_DOMAIN":
                return "channel"
            if "floodplain" in v or state == "STABILISED_FLOODPLAIN":
                return "floodplain"
            return "unknown"

        # Use one spatial index of T0 polygons rather than full polygon overlays per cell.
        # Spatially index the optional T0 classification once. Fabric boundaries
        # include this layer, so a representative point gives an unambiguous class
        # when the input partition itself is non-overlapping.
        init_lyr = self._resolve_vector_layer(initial_layer, context, f"{tag}_input") if initial_layer is not None else None
        state_idx = context_idx = -1
        spatial_index = None
        if init_lyr is not None and init_lyr.isValid():
            state_idx = init_lyr.fields().indexFromName(str(initial_state_field or "").strip())
            if state_idx < 0:
                raise QgsProcessingException(
                    f"[{tag}] T0 state field '{initial_state_field}' was not found in '{init_lyr.name()}'."
                )
            cfield = str(initial_context_field or "").strip()
            if cfield:
                context_idx = init_lyr.fields().indexFromName(cfield)
                if context_idx < 0:
                    feedback.pushWarning(
                        f"[{tag}] T0 context field '{cfield}' not found; context will be derived from state values."
                    )
            spatial_index = QgsSpatialIndex(init_lyr.getFeatures())
        elif int(initial_mode) == 1:
            raise QgsProcessingException(
                f"[{tag}] 'Explicit T0 classification required' was selected but no valid T0 polygon layer was supplied."
            )

        # INIT_* schema tracks first defensible state, confidence, source and censoring.
        for name, typ, length in [
            ("INIT_STATE", QVariant.String, 32),
            ("INIT_PROV", QVariant.String, 48),
            ("INIT_CONTEXT", QVariant.String, 48),
            ("INIT_CONF", QVariant.String, 16),
            ("INIT_SOURCE", QVariant.String, 120),
            ("LEFT_CENS", QVariant.Int, 0),
            ("INIT_SF_PROV", QVariant.String, 48),
            ("INIT_STORAGE", QVariant.Int, 0),
        ]:
            if lyr.fields().indexFromName(name) < 0:
                fld = QgsField(name, typ)
                if typ == QVariant.String:
                    fld.setLength(length)
                if not lyr.dataProvider().addAttributes([fld]):
                    raise QgsProcessingException(f"[{tag}] Could not add field {name}.")
        lyr.updateFields()
        fld_idx = {f.name(): i for i, f in enumerate(lyr.fields())}

        points = self._run_raw(
            "native:pointonsurface",
            {"INPUT": tagged, "ALL_PARTS": False, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context, feedback, f"{tag}_points",
        )["OUTPUT"]
        plyr = self._resolve_vector_layer(points, context, f"{tag}_points_rl")
        explicit_by_id = {}
        overlap_conflicts = 0
        if spatial_index is not None:
            preq = QgsFeatureRequest()
            preq.setSubsetOfAttributes(["_INIT_ID"], plyr.fields())
            for pf in plyr.getFeatures(preq):
                g = pf.geometry()
                if g is None or g.isEmpty():
                    continue
                matches = []
                # Conflicting overlapping T0 classes require input repair, not arbitrary priority.
                for cand in spatial_index.intersects(g.boundingBox()):
                    sf = init_lyr.getFeature(cand)
                    sg = sf.geometry()
                    if sg is not None and not sg.isEmpty() and sg.intersects(g):
                        raw_state = sf[state_idx]
                        st = classify(raw_state)
                        raw_context = sf[context_idx] if context_idx >= 0 else ""
                        matches.append((cand, raw_state, raw_context, st))
                if not matches:
                    continue
                # Different overlapping classifications are not safely resolvable.
                resolved_states = {m[3] for m in matches}
                if len(resolved_states) > 1:
                    overlap_conflicts += 1
                    continue
                matches.sort(key=lambda x: x[0])
                explicit_by_id[int(pf["_INIT_ID"])] = matches[0][1:]

        if overlap_conflicts:
            raise QgsProcessingException(
                f"[{tag}] {overlap_conflicts:,} fabric cells intersect overlapping T0 polygons with conflicting state classes. "
                "Resolve overlaps in the T0 classification before running Module 4a."
            )

        attrs = ["_INIT_ID"]
        for nm in ("BG_FP", "BG_SOURCE", "BELT_PROTECTED"):
            if nm in fld_idx:
                attrs.append(nm)
        provider = lyr.dataProvider()
        req0 = QgsFeatureRequest(); req0.setNoAttributes(); req0.setFlags(QgsFeatureRequest.NoGeometry)
        fids = [ft.id() for ft in lyr.getFeatures(req0)]
        summary = {}
        bg_explicit_conflicts = 0

        for offset in range(0, len(fids), 5000):
            req = QgsFeatureRequest(); req.setFilterFids(list(fids[offset:offset + 5000]))
            req.setSubsetOfAttributes(attrs, lyr.fields()); req.setFlags(QgsFeatureRequest.NoGeometry)
            changes = {}
            for ft in lyr.getFeatures(req):
                sid = int(ft["_INIT_ID"])
                bg = int(ft["BG_FP"] or 0) if "BG_FP" in fld_idx else 0
                explicit = explicit_by_id.get(sid)

                # Unknown T0 remains left-censored; there is no evidence of a prior formation date.
                state = "UNRESOLVED"
                prov = "prior_unknown"
                ctxt = "unknown"
                conf = "low"
                source = "none"
                left_cens = 1

                # Priority: explicit T0 class, then validated background, then optional floodplain default.
                if explicit is not None:
                    raw_state, raw_context, exp_state = explicit
                    state = exp_state
                    ctxt = context_from(raw_state, raw_context, state)
                    source = str(raw_state)[:120]
                    # Dated active occupation can be observed at T0; inherited storage and SF
                    # are left-censored even when their state category is supported.
                    conf = "high" if state != "UNRESOLVED" else "low"
                    if state == "ACTIVE_DOMAIN":
                        prov = "observed_t0_active"
                        left_cens = 0
                    elif state != "UNRESOLVED":
                        prov = "explicit_prior_left_censored"
                        left_cens = 1
                    else:
                        prov = "explicit_unmapped_prior"
                        left_cens = 1
                    if bg and state in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE"}:
                        bg_explicit_conflicts += 1
                elif bg:
                    state = "STABILISED_FLOODPLAIN"
                    prov = "explicit_background_prior"
                    ctxt = "floodplain"
                    conf = "high"
                    source = "VALID_BACKGROUND_MASK"
                    left_cens = 1
                elif int(initial_mode) == 2:
                    state = "STABILISED_FLOODPLAIN"
                    prov = "inferred_prior_floodplain"
                    ctxt = "floodplain"
                    conf = "moderate"
                    source = "FLOODPLAIN_DEFAULT_POLICY"
                    left_cens = 1

                # State provenance and secondary island context remain separate fields.
                if state == "STABILISED_FLOODPLAIN":
                    init_sf_prov = "prior_stable_island" if ctxt == "island" else "prior_floodplain"
                else:
                    init_sf_prov = "not_applicable"

                row = {
                    fld_idx["INIT_STATE"]: state,
                    fld_idx["INIT_PROV"]: prov,
                    fld_idx["INIT_CONTEXT"]: ctxt,
                    fld_idx["INIT_CONF"]: conf,
                    fld_idx["INIT_SOURCE"]: source,
                    fld_idx["LEFT_CENS"]: left_cens,
                    fld_idx["INIT_SF_PROV"]: init_sf_prov,
                    fld_idx["INIT_STORAGE"]: 1 if state == "DEPOSITIONAL_STORAGE" else 0,
                }
                changes[ft.id()] = row
                summary[state] = summary.get(state, 0) + 1
            if changes and not provider.changeAttributeValues(changes):
                raise QgsProcessingException(f"[{tag}] Provider batch update failed.")

        if bg_explicit_conflicts:
            raise QgsProcessingException(
                f"[{tag}] {bg_explicit_conflicts:,} cells are classified as T0 Active Domain/Depositional Storage "
                "inside the explicit background-floodplain mask. Correct one of the inputs before analysis."
            )
        for key in sorted(summary):
            feedback.pushInfo(f"[{tag}] INIT_STATE {key}: {summary[key]:,} cells")
        feedback.pushInfo(
            f"[{tag}] Policy mode={int(initial_mode)}; explicit classified cells={len(explicit_by_id):,}. "
            "The historical Active Domain belt was not used to infer T0 state."
        )

        cleaned = self._delete_field_if_exists(tagged, "_INIT_ID", context, feedback, f"{tag}_cleanup")
        return self._freeze_to_gpkg(
            cleaned, context, feedback, tag=f"{tag}_final",
            layer_name="initial_state_final", create_spatial_index=True,
        )

    # Validate a year/month/day tuple and produce YYYY_MM_DD text.
    @staticmethod
    def _norm_date_txt(y, m, d):
        # Constructing a date validates month/day combinations, including leap years.
        dt = date(int(y), int(m), int(d))
        return dt.strftime("%Y_%m_%d")

    # Parse allowed year, calendar-day or interval text into start/end dates.
    # Year-only values use 1 January as a parsing convention, not dated survey proof.
    # Date parsing supports calendar-day observations and bounded interpretation of year-only.
    def _parse_period_value(self, raw):
        if self._period_value_is_blank(raw):
            return (None, None)
        s = str(raw).strip()
        s2 = re.sub(r"[-/]", "_", s).strip()

        patterns = [
            (r"^((?:18|19|20)\d{2})(\d{2})(\d{2})_((?:18|19|20)\d{2})(\d{2})(\d{2})$", True),
            (r"^((?:18|19|20)\d{2})_(\d{2})_(\d{2})_+((?:18|19|20)\d{2})_(\d{2})_(\d{2})$", True),
            (r"^((?:18|19|20)\d{2})(\d{2})(\d{2})$", False),
            (r"^((?:18|19|20)\d{2})_(\d{2})_(\d{2})$", False),
        ]
        for pattern, is_range in patterns:
            m = re.fullmatch(pattern, s2)
            if not m:
                continue
            try:
                if is_range:
                    st = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
                    en = self._norm_date_txt(m.group(4), m.group(5), m.group(6))
                    return (st, en)
                en = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
                return (None, en)
            except (TypeError, ValueError):
                return (None, None)

        m = re.fullmatch(r"^((?:18|19|20)\d{2})$", s2)
        if m:
            try:
                return (None, self._norm_date_txt(m.group(1), "01", "01"))
            except (TypeError, ValueError):
                return (None, None)

        return (None, None)

    

    # ------------------------------------------------------------------
    # faster fabric build
    # ------------------------------------------------------------------

    # Form the immutable geometric partition by polygonizing combined EA/mask boundaries.
    # When a corridor exists, explicitly retain source-supported cells PLUS residual.
    # This is a SINGLE-PASS geometry partition, not repeated iterative fabric overlay.
    def _build_planar_fabric_from_boundaries(
        self,
        prepped_layers,
        context,
        feedback,
        tag="asmfabric",
        min_area=0.0,
        debug_gpkg_path=None,
        analysis_corridor=None,
        extra_boundary_layers=None,
    ):
        """
        Robust planar fabric builder without the self-snap bottleneck.

        Key design choices
        ------------------
        - NO self-snap of merged lines
        - build boundary network from all prepared layers plus optional corridor/background boundaries
        - strip attributes before topology-heavy steps
        - dissolve duplicate/coincident segments before polygonize
        - polygonize only once
        - retain cells inside the supplied analysis corridor, or the legacy EA footprint when no corridor is supplied
        - minimal post-polygonize cleaning only
        - optional debug outputs

        Debug layers written if debug_gpkg_path is provided
        ---------------------------------------------------
        - DBG_lines_1 ... DBG_lines_n
        - DBG_merged_lines
        - DBG_dissolved_lines
        - DBG_poly_all
        - DBG_footprint
        - DBG_kept
        """

        if not prepped_layers:
            raise QgsProcessingException("[Fabric] No prepped layers supplied.")

        # Build boundaries from every dated EA layer AND masks/T0 when available.
        # Later state classification cannot invent a boundary absent from this partition.
        boundary_layers = list(prepped_layers)
        if analysis_corridor is not None:
            boundary_layers.append(analysis_corridor)
        if extra_boundary_layers:
            boundary_layers.extend([x for x in extra_boundary_layers if x is not None])

        # Inner count logger limited to the planar-fabric build.
        def _log_fc(src, label):
            lyr = self._resolve_vector_layer(src, context, label)
            if lyr is None or not lyr.isValid():
                feedback.reportError(f"[COUNT] {label}: invalid")
                return 0
            fc = lyr.featureCount()
            feedback.pushInfo(f"[COUNT] {label}: {fc}")
            return fc

        # Optional fabric-stage diagnostic, disabled without debug destination.
        def _debug_save(src, name):
            if not debug_gpkg_path:
                return
            try:
                self._save_debug_layer(
                    src,
                    debug_gpkg_path,
                    f"DBG_{name}",
                    context,
                    feedback,
                    tag=f"{tag}_{name}",
                )
            except Exception as e:
                feedback.reportError(f"[DEBUG] Could not save {name}: {e}")

        # Construct polygon-and-area filtering expression for fabric intermediates.
        def _expr_valid_poly():
            expr = (
                "geometry_type($geometry) IN ('Polygon','MultiPolygon') "
                "AND $geometry IS NOT NULL "
                "AND NOT is_empty($geometry)"
            )
            if min_area is not None and min_area > 0:
                expr += f" AND $area > {min_area}"
            return expr

        # File-back boundary lines for reliable polygonization/indexing.
        def _freeze_lines(src, name):
            # Geometry-only topology intermediates are safer/faster as SHP
            out = self._freeze_to_shp(src, context, feedback, f"{tag}_{name}")
            try:
                self._run_raw(
                    "native:createspatialindex",
                    {"INPUT": out},
                    context,
                    feedback,
                    f"{tag}_{name}_idx",
                )
            except Exception as e:
                feedback.pushInfo(f"[Fabric] Spatial index skipped for {name}: {e}")
            return out

        # File-back polygon intermediates with complete GPKG schema.
        def _freeze_polys(src, name, layer_name):
            return self._freeze_to_gpkg(
                src,
                context,
                feedback,
                tag=f"{tag}_{name}",
                layer_name=layer_name,
                create_spatial_index=True,
            )

        # Remove EA attributes from topology network; boundaries alone define fabric.
        def _strip_all_fields(src, name):
            lyr = self._resolve_vector_layer(src, context, f"{tag}_{name}_src")
            if lyr is None or not lyr.isValid():
                raise QgsProcessingException(f"[Fabric] Invalid layer at {name}")
            return self._run_raw(
                "native:refactorfields",
                {
                    "INPUT": lyr,
                    "FIELDS_MAPPING": [],
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"{tag}_{name}_stripfields",
            )["OUTPUT"]

        expr_valid = _expr_valid_poly()

        # One EA polygon layer needs no combined-boundary polygonization.
        # --------------------------------------------------------------
        # Special case: one input layer only
        # --------------------------------------------------------------
        if len(prepped_layers) == 1 and analysis_corridor is None and not extra_boundary_layers:
            feedback.pushInfo("[Fabric] Only one layer supplied; using it directly as fabric.")

            single = self._resolve_vector_layer(prepped_layers[0], context, f"{tag}_single_src")
            if single is None or not single.isValid():
                raise QgsProcessingException("[Fabric] Single input layer invalid.")

            single = self._run_raw(
                "native:fixgeometries",
                {
                    "INPUT": single,
                    "METHOD": 1,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_single_fix",
            )["OUTPUT"]

            single = self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": single,
                    "EXPRESSION": expr_valid,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_single_keep",
            )["OUTPUT"]

            single = _freeze_polys(single, "single_frozen", "fabric_single")
            _log_fc(single, "fabric_single")
            _debug_save(single, "fabric_single")
            return single

        # --------------------------------------------------------------
        # 1) Convert each prepared polygon layer to boundary lines
        # --------------------------------------------------------------
        # Stage 1: convert each polygon boundary to line geometry.
        line_layers = []
        for i, src in enumerate(boundary_layers, start=1):
            feedback.pushInfo(f"[Fabric] Converting boundary layer {i}/{len(boundary_layers)} to lines")

            lines = self._run_raw(
                "native:polygonstolines",
                {
                    "INPUT": src,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_lines_{i}",
            )["OUTPUT"]

            lines = self._run_raw(
                "native:fixgeometries",
                {
                    "INPUT": lines,
                    "METHOD": 1,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_lines_fix_{i}",
            )["OUTPUT"]

            lines = _strip_all_fields(lines, f"lines_{i}")
            lines = _freeze_lines(lines, f"linesf_{i}")

            _debug_save(lines, f"lines_{i}")
            line_layers.append(lines)

        # Stage 2: merge prepared boundaries; these determine all planar cell edges.
        # --------------------------------------------------------------
        # 2) Merge all boundary lines
        # --------------------------------------------------------------
        feedback.pushInfo("[Fabric] Merging all boundary lines")
        merged_lines = self._run_raw(
            "native:mergevectorlayers",
            {
                "LAYERS": line_layers,
                "CRS": None,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_merge_lines",
        )["OUTPUT"]

        merged_lines = _strip_all_fields(merged_lines, "merged_lines")
        merged_lines = _freeze_lines(merged_lines, "merged_lines")

        _log_fc(merged_lines, "merged_lines")
        _debug_save(merged_lines, "merged_lines")

        # No self-snap: it is prohibitively expensive in densely segmented 40-layer records.
        # --------------------------------------------------------------
        # 3) NO self-snap: too slow on dense networks
        # --------------------------------------------------------------
        feedback.pushInfo("[Fabric] Skipping self-snap before polygonize")

        # Dissolving coincident linework limits duplication before polygonization.
        # --------------------------------------------------------------
        # 4) Dissolve duplicate / coincident segments
        # --------------------------------------------------------------
        # This is the lighter-weight topology cleanup replacing self-snap.
        feedback.pushInfo("[Fabric] Dissolving merged lines before polygonize")
        dissolved_lines = self._run_raw(
            "native:dissolve",
            {
                "INPUT": merged_lines,
                "FIELD": [],
                "SEPARATE_DISJOINT": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_dissolve_lines",
        )["OUTPUT"]

        dissolved_lines = self._run_raw(
            "native:multiparttosingleparts",
            {
                "INPUT": dissolved_lines,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_dissolve_singleparts",
        )["OUTPUT"]

        dissolved_lines = _strip_all_fields(dissolved_lines, "dissolved_lines")
        dissolved_lines = _freeze_lines(dissolved_lines, "dissolved_lines")

        _log_fc(dissolved_lines, "dissolved_lines")
        _debug_save(dissolved_lines, "dissolved_lines")

        # Only ONE polygonize operation is performed for the merged boundary network.
        # --------------------------------------------------------------
        # 5) Polygonize once
        # --------------------------------------------------------------
        feedback.pushInfo("[Fabric] Polygonizing dissolved linework")
        poly_all = self._run_raw(
            "native:polygonize",
            {
                "INPUT": dissolved_lines,
                "KEEP_FIELDS": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_polygonize",
        )["OUTPUT"]

        poly_all = self._run_raw(
            "native:fixgeometries",
            {
                "INPUT": poly_all,
                "METHOD": 1,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_poly_fix",
        )["OUTPUT"]

        poly_all = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": poly_all,
                "EXPRESSION": expr_valid,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_poly_keep_valid",
        )["OUTPUT"]

        poly_all = _freeze_polys(poly_all, "poly_all_frozen", "poly_all")

        _log_fc(poly_all, "poly_all_before_footprint_filter")
        _debug_save(poly_all, "poly_all")

        # SRCMASK records source polygon coverage; footprint aids filtering and QA.
        # --------------------------------------------------------------
        # 6) Build permanent undissolved source mask plus diagnostic dissolved footprint
        # --------------------------------------------------------------
        feedback.pushInfo("[Fabric] Building permanent undissolved SRCMASK and diagnostic dissolved footprint")
        merged_src = self._run_raw(
            "native:mergevectorlayers",
            {
                "LAYERS": prepped_layers,
                "CRS": None,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_merge_src",
        )["OUTPUT"]

        merged_src = self._freeze_to_gpkg(
            merged_src,
            context,
            feedback,
            tag=f"{tag}_merged_src",
            layer_name="SRCMASK",
            create_spatial_index=True,
        )

        footprint = self._run_raw(
            "native:dissolve",
            {
                "INPUT": merged_src,
                "FIELD": [],
                "SEPARATE_DISJOINT": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_dissolve_src",
        )["OUTPUT"]

        footprint = self._run_raw(
            "native:fixgeometries",
            {
                "INPUT": footprint,
                "METHOD": 1,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_footprint_fix",
        )["OUTPUT"]

        footprint = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": footprint,
                "EXPRESSION": expr_valid,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_footprint_keep_valid",
        )["OUTPUT"]

        footprint = _freeze_polys(footprint, "footprint_frozen", "footprint")

        footprint_fc = _log_fc(footprint, "footprint")
        _debug_save(merged_src, "SRCMASK")
        _debug_save(footprint, "footprint")

        if footprint_fc == 0:
            raise QgsProcessingException("[Fabric] Dissolved footprint is empty.")
        
        # --------------------------------------------------------------
        # 6b) Optional support-based repair of missing polygons inside footprint
        # --------------------------------------------------------------
        # Missing-patch repair remains disabled by a code constant; changing it alters behaviour.
        # Production 39-layer runs have shown missing_large = 0 after the expensive
        # footprint - dissolved(poly_all) check. Keep this off by default to avoid
        # a heavy native:difference operation on dense 35-39 layer fabrics.
        ENABLE_FABRIC_REPAIR = False

        if ENABLE_FABRIC_REPAIR:
            # --------------------------------------------------------------
            # 6b) Support-based repair of missing polygons inside footprint
            # --------------------------------------------------------------
            feedback.pushInfo("[Fabric] Detecting large missing patches inside footprint")

            # Tunable thresholds
            # The optional repair uses minimum patch area AND sufficient temporal source support.
            MIN_REPAIR_AREA = 100000.0   # m²; ignore tiny polygonization misses
            MIN_SUPPORT_FRAC = 0.70      # require support from >= 70% of source layers
            MIN_SUPPORT_COUNT = max(1, int(math.ceil(len(prepped_layers) * MIN_SUPPORT_FRAC)))

            # Dissolve the polygonized fabric to identify holes relative to footprint
            poly_all_diss = self._run_raw(
                "native:dissolve",
                {
                    "INPUT": poly_all,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_poly_all_dissolve",
            )["OUTPUT"]

            poly_all_diss = self._run_raw(
                "native:fixgeometries",
                {
                    "INPUT": poly_all_diss,
                    "METHOD": 1,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_poly_all_dissolve_fix",
            )["OUTPUT"]

            # Missing = footprint - dissolved(poly_all)
            missing = self._safe_polygon_difference(
                footprint,
                poly_all_diss,
                context,
                feedback,
                f"{tag}_missing_from_poly_all",
            )

            missing = self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": missing,
                    "EXPRESSION": (
                        "geometry_type($geometry) IN ('Polygon','MultiPolygon') "
                        "AND $geometry IS NOT NULL "
                        "AND NOT is_empty($geometry) "
                        f"AND $area >= {MIN_REPAIR_AREA}"
                    ),
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_missing_large",
            )["OUTPUT"]

            missing = self._freeze_to_gpkg(
                missing,
                context,
                feedback,
                tag=f"{tag}_missing_large",
                layer_name="missing_large",
                create_spatial_index=True,
            )

            _log_fc(missing, "missing_large")
            _debug_save(missing, "missing_large")

            missing_lyr = self._resolve_vector_layer(missing, context, f"{tag}_missing_large_chk")
            do_repair = missing_lyr is not None and missing_lyr.isValid() and missing_lyr.featureCount() > 0

            if do_repair:
                feedback.pushInfo(
                    f"[Fabric] Evaluating support for missing patches "
                    f"(min_support_count={MIN_SUPPORT_COUNT}/{len(prepped_layers)})"
                )

                # Add IDs to missing polygons
                missing_id = self._run_raw(
                    "native:addautoincrementalfield",
                    {
                        "INPUT": missing,
                        "FIELD_NAME": "_MISS_ID",
                        "START": 1,
                        "GROUP_FIELDS": [],
                        "SORT_EXPRESSION": "",
                        "SORT_ASCENDING": True,
                        "SORT_NULLS_FIRST": False,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"{tag}_missing_addid",
                )["OUTPUT"]

                missing_id = self._freeze_to_gpkg(
                    missing_id,
                    context,
                    feedback,
                    tag=f"{tag}_missing_id",
                    layer_name="missing_id",
                    create_spatial_index=True,
                )

                # Point-on-surface for each missing polygon
                missing_pts = self._run_raw(
                    "native:pointonsurface",
                    {
                        "INPUT": missing_id,
                        "ALL_PARTS": False,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"{tag}_missing_pts",
                )["OUTPUT"]

                missing_pts = self._freeze_to_gpkg(
                    missing_pts,
                    context,
                    feedback,
                    tag=f"{tag}_missing_pts",
                    layer_name="missing_pts",
                    create_spatial_index=True,
                )

                # Build support counts across source layers
                support_counts = {}

                for i, src in enumerate(prepped_layers, start=1):
                    pts_join = self._run_raw(
                        "native:joinattributesbylocation",
                        {
                            "INPUT": missing_pts,
                            "JOIN": src,
                            "PREDICATE": [0],  # intersects
                            "JOIN_FIELDS": [],
                            "METHOD": 0,
                            "DISCARD_NONMATCHING": False,
                            "PREFIX": f"S{i}_",
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context, feedback, f"{tag}_missing_support_join_{i}",
                    )["OUTPUT"]

                    pts_join_lyr = self._resolve_vector_layer(
                        pts_join, context, f"{tag}_missing_support_join_{i}_lyr"
                    )
                    if pts_join_lyr is None or not pts_join_lyr.isValid():
                        continue

                    join_names = pts_join_lyr.fields().names()
                    join_hit_fields = [n for n in join_names if n.startswith(f"S{i}_")]

                    # If there are no joined fields, then nothing matched for this layer
                    if not join_hit_fields:
                        continue

                    for ft in pts_join_lyr.getFeatures():
                        miss_id = ft["_MISS_ID"]
                        if miss_id is None:
                            continue

                        hit = False
                        for jf in join_hit_fields:
                            val = ft[jf]
                            if val is not None and str(val).strip() != "":
                                hit = True
                                break

                        if hit:
                            support_counts[miss_id] = support_counts.get(miss_id, 0) + 1

                # Select only well-supported missing polygons
                supported_ids = [mid for mid, cnt in support_counts.items() if cnt >= MIN_SUPPORT_COUNT]

                feedback.pushInfo(
                    f"[Fabric] Supported missing patches retained: {len(supported_ids)} "
                    f"of {missing_lyr.featureCount()}"
                )

                repaired = None
                if supported_ids:
                    id_list = ",".join(str(x) for x in supported_ids)

                    repaired = self._run_raw(
                        "native:extractbyexpression",
                        {
                            "INPUT": missing_id,
                            "EXPRESSION": f"\"_MISS_ID\" IN ({id_list})",
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context, feedback, f"{tag}_missing_supported",
                    )["OUTPUT"]

                    repaired = self._run_raw(
                        "native:fixgeometries",
                        {
                            "INPUT": repaired,
                            "METHOD": 1,
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context, feedback, f"{tag}_missing_supported_fix",
                    )["OUTPUT"]

                    repaired = self._run_raw(
                        "native:extractbyexpression",
                        {
                            "INPUT": repaired,
                            "EXPRESSION": expr_valid,
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context, feedback, f"{tag}_missing_supported_keep",
                    )["OUTPUT"]

                    repaired = self._freeze_to_gpkg(
                        repaired,
                        context,
                        feedback,
                        tag=f"{tag}_missing_supported",
                        layer_name="missing_supported",
                        create_spatial_index=True,
                    )

                    _log_fc(repaired, "missing_supported")
                    _debug_save(repaired, "missing_supported")

                    repaired_lyr = self._resolve_vector_layer(repaired, context, f"{tag}_missing_supported_chk")
                    if repaired_lyr is not None and repaired_lyr.isValid() and repaired_lyr.featureCount() > 0:
                        feedback.pushInfo("[Fabric] Merging supported repair patches back into poly_all")

                        poly_all = self._run_raw(
                            "native:mergevectorlayers",
                            {
                                "LAYERS": [poly_all, repaired],
                                "CRS": None,
                                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                            },
                            context, feedback, f"{tag}_poly_all_repaired_merge",
                        )["OUTPUT"]

                        poly_all = self._run_raw(
                            "native:fixgeometries",
                            {
                                "INPUT": poly_all,
                                "METHOD": 1,
                                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                            },
                            context, feedback, f"{tag}_poly_all_repaired_fix",
                        )["OUTPUT"]

                        poly_all = self._run_raw(
                            "native:extractbyexpression",
                            {
                                "INPUT": poly_all,
                                "EXPRESSION": expr_valid,
                                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                            },
                            context, feedback, f"{tag}_poly_all_repaired_keep",
                        )["OUTPUT"]

                        poly_all = _freeze_polys(poly_all, "poly_all_repaired", "poly_all")
                        _log_fc(poly_all, "poly_all_after_repair")
                        _debug_save(poly_all, "poly_all_repaired")

        else:
            feedback.pushInfo(
                "[Fabric] Skipping missing-patch repair "
                "(ENABLE_FABRIC_REPAIR=False; production 39-layer mode)"
            )

        # --------------------------------------------------------------
        # 7) Keep cells inside the analysis envelope
        # --------------------------------------------------------------
        # Corridor-backed run: append the corridor-minus-footprint residual explicitly.
        # Polygonize alone may omit the large polygon between source belts and corridor edge.
        if analysis_corridor is not None:
            # Do not rely on polygonize to create the large outer-corridor residual.
            # With dense nested EA boundary networks, polygonize can return the internal
            # EA cells but omit (or inconsistently represent) the polygon between the
            # combined EA footprint and the corridor boundary.  Build that residual
            # explicitly so the final fabric always covers the complete corridor.
            feedback.pushInfo(
                "[Fabric] Building corridor-complete fabric: EA-supported cells plus explicit corridor residual"
            )

            # Restrict the combined EA footprint to the corridor first.  This is the
            # source-supported part of the analysis population.
            footprint_in_corridor = self._run_raw(
                "native:clip",
                {
                    "INPUT": footprint,
                    "OVERLAY": analysis_corridor,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_footprint_clip_corridor",
            )["OUTPUT"]
            footprint_in_corridor = self._sanitize_polygon_layer(
                footprint_in_corridor,
                context,
                feedback,
                f"{tag}_footprint_in_corridor",
                min_area=0.0,
            )
            footprint_in_corridor = _freeze_polys(
                footprint_in_corridor,
                "footprint_in_corridor_frozen",
                "footprint_in_corridor",
            )
            _debug_save(footprint_in_corridor, "footprint_in_corridor")

            # Clip source-supported cells first to prevent double-counting corridor residual.
            # Keep polygonized EA cells only within the source-supported footprint.
            # The outer background zone is added separately below, preventing it from
            # being lost during polygonization and preventing duplicate residual cells.
            source_cells = self._run_raw(
                "native:clip",
                {
                    "INPUT": poly_all,
                    "OVERLAY": footprint_in_corridor,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_clip_source_cells",
            )["OUTPUT"]
            source_cells = self._sanitize_polygon_layer(
                source_cells,
                context,
                feedback,
                f"{tag}_source_cells_clean",
                min_area=0.0,
            )
            _log_fc(source_cells, "source_cells_inside_corridor")
            _debug_save(source_cells, "source_cells_inside_corridor")

            # Corridor residual is geometry only. Its true state depends on later mask QA;
            # absence of EA mapping is not automatically evidence of SF.
            # Explicit background/residual geometry = corridor minus all EA-supported
            # geometry.  These polygons initially have no EA assignments; the later
            # corridor-background policy marks them as validated background floodplain
            # or unresolved according to VALID_BACKGROUND_MASK / the explicit override.
            corridor_residual = self._safe_polygon_difference(
                analysis_corridor,
                footprint_in_corridor,
                context,
                feedback,
                f"{tag}_corridor_residual",
            )
            corridor_residual = self._sanitize_polygon_layer(
                corridor_residual,
                context,
                feedback,
                f"{tag}_corridor_residual_clean",
                min_area=0.0,
            )
            residual_fc = _log_fc(corridor_residual, "corridor_residual_cells")
            _debug_save(corridor_residual, "corridor_residual")

            if residual_fc > 0:
                kept = self._run_raw(
                    "native:mergevectorlayers",
                    {
                        "LAYERS": [source_cells, corridor_residual],
                        "CRS": None,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"{tag}_merge_source_residual",
                )["OUTPUT"]
            else:
                kept = source_cells

            # A final clip controls small numeric slivers introduced along corridor edges.
            # Final exact clip is defensive against numerical slivers introduced by
            # difference/merge operations at the corridor boundary.
            kept = self._run_raw(
                "native:clip",
                {
                    "INPUT": kept,
                    "OVERLAY": analysis_corridor,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_clip_completed_corridor",
            )["OUTPUT"]
            _log_fc(kept, "kept_raw_after_corridor_completion")
            _debug_save(analysis_corridor, "analysis_corridor")
        # Without a corridor, source footprint defines the analysed domain (legacy behaviour).
        else:
            # Legacy behaviour: retain only cells intersecting the permanent,
            # undissolved union of the EA source polygons.
            feedback.pushInfo("[Fabric] No corridor supplied; keeping cells that INTERSECT permanent undissolved SRCMASK")
            kept = self._run_raw(
                "native:extractbylocation",
                {
                    "INPUT": poly_all,
                    "PREDICATE": [0],
                    "INTERSECT": merged_src,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"{tag}_extract_intersects_src",
            )["OUTPUT"]
            _log_fc(kept, "kept_raw_after_source_filter")

            # Diagnostic only: compare strict legacy containment against the
            # dissolved footprint. This is not used to decide which cells survive.
            try:
                kept_within = self._run_raw(
                    "native:extractbylocation",
                    {
                        "INPUT": poly_all,
                        "PREDICATE": [5],
                        "INTERSECT": footprint,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"{tag}_extract_within_dbg",
                )["OUTPUT"]
                _log_fc(kept_within, "kept_within_dbg")
                _debug_save(kept_within, "kept_within")
            except Exception as e:
                feedback.pushInfo(f"[Fabric] Debug WITHIN filter skipped/failed: {e}")

        kept = self._run_raw(
            "native:fixgeometries",
            {
                "INPUT": kept,
                "METHOD": 1,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_kept_fix",
        )["OUTPUT"]

        kept = self._run_raw(
            "native:extractbyexpression",
            {
                "INPUT": kept,
                "EXPRESSION": expr_valid,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_kept_keep_valid",
        )["OUTPUT"]

        kept = _freeze_polys(kept, "kept_frozen", "fabric")

        kept_fc = _log_fc(kept, "final_fabric_cells")
        _debug_save(kept, "kept")

        if kept_fc == 0:
            raise QgsProcessingException(
                "[Fabric] Analysis-envelope filtering produced 0 cells. "
                "Inspect DBG_poly_all, DBG_footprint, and DBG_kept."
            )

        return kept

    # Refactor one date pair to compact EAi/PDi field names for targeted joins.
    # Short-lived EAi/PDi fields are deliberately narrow for join performance.
    def _make_short_step_fields(self, src, step_i, context, feedback, tag):
        ea_src = f"EA_Class_{step_i}"
        pd_src = f"Period_{step_i}"
        ea_short = f"EA{step_i}"
        pd_short = f"PD{step_i}"

        src_lyr = self._resolve_vector_layer(src, context, f"{tag}_src")
        src_names = src_lyr.fields().names()

        if ea_src not in src_names or pd_src not in src_names:
            raise QgsProcessingException(
                f"[{tag}] Expected fields {ea_src} and {pd_src} not found. Fields present: {src_names}"
            )

        out = self._run_raw(
            "native:refactorfields",
            {
                "INPUT": src_lyr,
                "FIELDS_MAPPING": [
                    {
                        "expression": f'"{ea_src}"',
                        "length": 254,
                        "name": ea_short,
                        "precision": 0,
                        "type": 10,
                    },
                    {
                        "expression": f'"{pd_src}"',
                        "length": 254,
                        "name": pd_short,
                        "precision": 0,
                        "type": 10,
                    },
                ],
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, tag,
        )["OUTPUT"]

        return out

    # Reattribute every date to the same planar cells without copying the whole fabric.
    # Unique point joins are fast; ambiguous/missing cells may need overlap rescue.
    def _reassign_ea_fields_from_sources(
        self,
        fabric_src,
        prepped_layers,
        context,
        feedback,
        debug_gpkg_path=None,
        min_fabric_area=50.0,
    ):
        """
        High-performance timestep reassignment for large 35–40 layer runs.

        Performance design
        ------------------
        - Geometry is cleaned once before the loop and remains unchanged.
        - One narrow polygon layer (_FAB_ID + geometry) is reused for rescue.
        - One representative-point layer (_FAB_ID + point) is reused for every step.
        - Prepared source layers are used directly; no per-step source copies.
        - Attribute writes use provider.changeAttributeValues() in large batches.
        - Unresolved IDs are derived from cached IDs, avoiding full null scans.
        - No full-fabric GeoPackage is rewritten inside the timestep loop.
        - No geometry checkpoint occurs inside the timestep loop.
        """
        n_steps = len(prepped_layers)
        if n_steps == 0:
            raise QgsProcessingException("[Reassign-fast] No prepared EA layers supplied")

        # Hard-coded overlap thresholds affect small rescued cells and deserve recording
        # in reproducibility notes; they are unchanged in this comment-only release.
        MIN_FABRIC_AREA = max(0.0, float(min_fabric_area or 0.0))
        MIN_OVERLAP_AREA = 50.0
        MIN_AMBIG_OVERLAP_AREA = 0.0
        ENABLE_AMBIG_RESCUE = True
        AMBIG_RESCUE_MIN_COUNT = 500
        AMBIG_RESCUE_MIN_FRAC = 0.0025
        UPDATE_BATCH_SIZE = 25000

        total_t0 = time.perf_counter()

        # Store optional date-specific joins only when debugging is enabled.
        def _debug_save(src, name):
            if not debug_gpkg_path:
                return
            try:
                self._save_debug_layer(
                    src,
                    debug_gpkg_path,
                    f"DBG_{name}",
                    context,
                    feedback,
                    tag=f"reattr_{name}",
                )
            except Exception as exc:
                feedback.reportError(f"[DEBUG] Could not save {name}: {exc}")

        # Distinguish populated join payloads from absent class/period values.
        def _usable_text(value):
            return value is not None and str(value).strip() != ""

        # Apply large ID-to-field updates in bounded chunks; fail on provider errors.
        # Chunked provider edits avoid a wide in-memory copy of the full fabric.
        def _apply_provider_changes(layer, changes_iter, label):
            provider = layer.dataProvider()
            pending = {}
            total = 0

            for fid, attrs in changes_iter:
                if not attrs:
                    continue
                pending[int(fid)] = attrs
                if len(pending) >= UPDATE_BATCH_SIZE:
                    if not provider.changeAttributeValues(pending):
                        raise QgsProcessingException(
                            f"[Reassign-fast] Provider update failed during {label}"
                        )
                    total += len(pending)
                    pending = {}

            if pending:
                if not provider.changeAttributeValues(pending):
                    raise QgsProcessingException(
                        f"[Reassign-fast] Provider update failed during {label}"
                    )
                total += len(pending)

            return total

        # --------------------------------------------------------------
        # 1) Build one stable file-backed working fabric
        # --------------------------------------------------------------
        # Geometry remains fixed while chronological EA fields are attached step by step.
        setup_t0 = time.perf_counter()
        feedback.pushInfo(
            f"[Reassign-fast] Preparing stable fabric; minimum cell area = "
            f"{MIN_FABRIC_AREA:g} map-units²"
        )

        fabric = self._sanitize_polygon_layer(
            fabric_src,
            context,
            feedback,
            "reattr_fast_fabric",
            min_area=MIN_FABRIC_AREA,
        )

        fabric = self._drop_fields_matching(
            fabric,
            [
                r"^EA_Class(_\d+.*)?$",
                r"^Period(_\d+.*)?$",
                r"^layer$",
                r"^path$",
                r"^_FAB_ID$",
            ],
            context,
            feedback,
            tag="reattr_fast_strip_old",
        )

        fabric = self._run_raw(
            "native:addautoincrementalfield",
            {
                "INPUT": fabric,
                "FIELD_NAME": "_FAB_ID",
                "START": 1,
                "GROUP_FIELDS": [],
                "SORT_EXPRESSION": "",
                "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            "reattr_fast_addid",
        )["OUTPUT"]

        schema_layer = self._resolve_vector_layer(fabric, context, "reattr_fast_schema")
        if schema_layer is None or not schema_layer.isValid():
            raise QgsProcessingException("[Reassign-fast] Invalid fabric during schema creation")

        # Predeclare one EA_Class_i and one Period_i field per input interval.
        existing_names = set(schema_layer.fields().names())
        new_fields = []
        for step_i in range(1, n_steps + 1):
            for name in (f"EA_Class_{step_i}", f"Period_{step_i}"):
                if name not in existing_names:
                    field = QgsField(name, QVariant.String)
                    field.setLength(254)
                    new_fields.append(field)
                    existing_names.add(name)

        if new_fields and not schema_layer.dataProvider().addAttributes(new_fields):
            raise QgsProcessingException("[Reassign-fast] Could not add timestep fields")
        schema_layer.updateFields()

        fabric = self._freeze_to_gpkg(
            schema_layer,
            context,
            feedback,
            tag="reattr_fast_working",
            layer_name="fabric_working",
            create_spatial_index=True,
        )
        working_layer = self._resolve_vector_layer(fabric, context, "reattr_fast_working_rl")
        if working_layer is None or not working_layer.isValid():
            raise QgsProcessingException("[Reassign-fast] File-backed working fabric is invalid")

        # Provider FIDs can change after freezing; store a stable _FAB_ID mapping.
        # Cache the stable relationship between _FAB_ID and provider feature ID.
        id_request = QgsFeatureRequest()
        id_request.setSubsetOfAttributes(["_FAB_ID"], working_layer.fields())
        id_request.setFlags(QgsFeatureRequest.NoGeometry)
        fabid_to_fid = {}
        all_fab_ids = set()
        for feature in working_layer.getFeatures(id_request):
            raw_id = feature["_FAB_ID"]
            if raw_id is None:
                continue
            fab_id = int(raw_id)
            fabid_to_fid[fab_id] = feature.id()
            all_fab_ids.add(fab_id)

        if not all_fab_ids:
            raise QgsProcessingException("[Reassign-fast] Working fabric contains no _FAB_ID values")

        # Narrow polygon geometry reused for both point creation and overlap rescue.
        fabric_geom = self._run_raw(
            "native:refactorfields",
            {
                "INPUT": working_layer,
                "FIELDS_MAPPING": [
                    {
                        "expression": '"_FAB_ID"',
                        "length": 0,
                        "name": "_FAB_ID",
                        "precision": 0,
                        "type": QVariant.LongLong,
                    }
                ],
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            "reattr_fast_geom_id",
        )["OUTPUT"]
        fabric_geom = self._freeze_to_gpkg(
            fabric_geom,
            context,
            feedback,
            tag="reattr_fast_geom_id",
            layer_name="fabric_geom_id",
            create_spatial_index=True,
        )

        # The same representative-point geometry is reused for every EA observation.
        fabric_points = self._run_raw(
            "native:pointonsurface",
            {
                "INPUT": fabric_geom,
                "ALL_PARTS": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            "reattr_fast_points",
        )["OUTPUT"]
        fabric_points = self._freeze_to_gpkg(
            fabric_points,
            context,
            feedback,
            tag="reattr_fast_points",
            layer_name="fabric_points",
            create_spatial_index=True,
        )

        feedback.pushInfo(
            f"[Reassign-fast] Stable fabric ready: {len(all_fab_ids):,} cells; "
            f"setup {time.perf_counter() - setup_t0:.1f} s"
        )
        if debug_gpkg_path:
            _debug_save(fabric_geom, "fabric_geom_id")
            _debug_save(fabric_points, "fabric_points_cached")

        # --------------------------------------------------------------
        # 2) Assign every timestep without changing geometry or copying fabric
        # --------------------------------------------------------------
        # One loop iteration corresponds to ONE dated EA layer; no fabric geometry rebuild.
        for step_i, source in enumerate(prepped_layers, start=1):
            if feedback.isCanceled():
                raise QgsProcessingException("[Reassign-fast] Processing cancelled")

            step_t0 = time.perf_counter()
            ea_field = f"EA_Class_{step_i}"
            pd_field = f"Period_{step_i}"
            source_layer = self._resolve_vector_layer(source, context, f"reattr_fast_source_{step_i}")
            if source_layer is None or not source_layer.isValid():
                raise QgsProcessingException(f"[Reassign-fast] Step {step_i}: invalid source layer")
            source_names = source_layer.fields().names()
            if ea_field not in source_names or pd_field not in source_names:
                raise QgsProcessingException(
                    f"[Reassign-fast] Step {step_i}: source lacks {ea_field}/{pd_field}"
                )

            feedback.pushInfo(
                f"[Reassign-fast] Step {step_i}/{n_steps}: cached-point join"
            )

            # Try representative-point intersection first to minimise full geometry overlays.
            join_t0 = time.perf_counter()
            pts_join = self._run_raw(
                "native:joinattributesbylocation",
                {
                    "INPUT": fabric_points,
                    "JOIN": source_layer,
                    "PREDICATE": [0],
                    "JOIN_FIELDS": [ea_field, pd_field],
                    "METHOD": 0,
                    "DISCARD_NONMATCHING": False,
                    "PREFIX": "PT_",
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"reattr_fast_pts_join_{step_i}",
            )["OUTPUT"]

            join_layer = self._resolve_vector_layer(
                pts_join, context, f"reattr_fast_pts_join_{step_i}_rl"
            )
            pt_ea = f"PT_{ea_field}"
            pt_pd = f"PT_{pd_field}"
            join_names = join_layer.fields().names()
            if "_FAB_ID" not in join_names or pt_ea not in join_names or pt_pd not in join_names:
                raise QgsProcessingException(
                    f"[Reassign-fast] Step {step_i}: expected joined fields not found"
                )

            # Collect multiple hits to detect ambiguous joined classes, not merely first match.
            point_hits = {}
            raw_join_rows = 0
            join_request = QgsFeatureRequest()
            join_request.setSubsetOfAttributes(["_FAB_ID", pt_ea, pt_pd], join_layer.fields())
            join_request.setFlags(QgsFeatureRequest.NoGeometry)
            for feature in join_layer.getFeatures(join_request):
                raw_join_rows += 1
                raw_id = feature["_FAB_ID"]
                if raw_id is None:
                    continue
                ea_value = feature[pt_ea]
                pd_value = feature[pt_pd]
                if not _usable_text(ea_value) and not _usable_text(pd_value):
                    continue
                fab_id = int(raw_id)
                point_hits.setdefault(fab_id, []).append((ea_value, pd_value))

            # Unique point hits can be assigned; duplicates are candidates for area-based rescue.
            point_map = {}
            ambiguous_ids = set()
            duplicate_rows = 0
            for fab_id, hits in point_hits.items():
                if len(hits) == 1:
                    point_map[fab_id] = hits[0]
                else:
                    ambiguous_ids.add(fab_id)
                    duplicate_rows += len(hits) - 1

            unique_ids = set(point_map)
            unresolved_ids = all_fab_ids.difference(unique_ids).difference(ambiguous_ids)
            ambiguous_frac = float(len(ambiguous_ids)) / float(max(1, len(all_fab_ids)))
            # Ambiguous rescue activates only above the code-defined count/fraction guard.
            do_ambiguous_rescue = (
                ENABLE_AMBIG_RESCUE
                and ambiguous_ids
                and (
                    len(ambiguous_ids) >= AMBIG_RESCUE_MIN_COUNT
                    or ambiguous_frac >= AMBIG_RESCUE_MIN_FRAC
                )
            )
            ambiguous_for_rescue = set(ambiguous_ids) if do_ambiguous_rescue else set()

            ea_idx = working_layer.fields().indexFromName(ea_field)
            pd_idx = working_layer.fields().indexFromName(pd_field)
            if ea_idx < 0 or pd_idx < 0:
                raise QgsProcessingException(
                    f"[Reassign-fast] Step {step_i}: destination fields missing"
                )

            # Yield unique point-join updates without building an extra full-table copy.
            def _point_change_iter():
                for fab_id, values in point_map.items():
                    fid = fabid_to_fid.get(fab_id)
                    if fid is None:
                        continue
                    yield fid, {ea_idx: values[0], pd_idx: values[1]}

            point_written = _apply_provider_changes(
                working_layer,
                _point_change_iter(),
                f"step {step_i} point assignments",
            )

            feedback.pushInfo(
                f"[Reassign-fast] Step {step_i}: rows={raw_join_rows:,}; "
                f"unique={point_written:,}; ambiguous={len(ambiguous_ids):,}; "
                f"unresolved={len(unresolved_ids):,}; duplicates={duplicate_rows:,}; "
                f"join/read/write={time.perf_counter() - join_t0:.1f} s"
            )

            if ambiguous_ids and not do_ambiguous_rescue:
                feedback.pushInfo(
                    f"[Reassign-fast] Step {step_i}: ambiguous rescue skipped "
                    f"(count={len(ambiguous_ids):,}, fraction={ambiguous_frac:.5f})"
                )

            # Rescue also covers cells without a usable point assignment but touching EA polygons.
            rescue_ids = unresolved_ids.union(ambiguous_for_rescue)
            rescue_written = 0
            if rescue_ids:
                rescue_t0 = time.perf_counter()

                # Spatially restrict the narrow geometry/ID layer first. This avoids
                # copying the wide working table or dissolving the source footprint.
                touching = self._run_raw(
                    "native:extractbylocation",
                    {
                        "INPUT": fabric_geom,
                        "INTERSECT": source_layer,
                        "PREDICATE": [0],
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context,
                    feedback,
                    f"reattr_fast_touching_{step_i}",
                )["OUTPUT"]
                touching_layer = self._resolve_vector_layer(
                    touching, context, f"reattr_fast_touching_{step_i}_rl"
                )

                selected_fids = []
                touch_request = QgsFeatureRequest()
                touch_request.setSubsetOfAttributes(["_FAB_ID"], touching_layer.fields())
                touch_request.setFlags(QgsFeatureRequest.NoGeometry)
                for feature in touching_layer.getFeatures(touch_request):
                    raw_id = feature["_FAB_ID"]
                    if raw_id is not None and int(raw_id) in rescue_ids:
                        selected_fids.append(feature.id())

                if selected_fids:
                    touching_layer.selectByIds(selected_fids)
                    rescue_subset = self._run_raw(
                        "native:saveselectedfeatures",
                        {
                            "INPUT": touching_layer,
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context,
                        feedback,
                        f"reattr_fast_rescue_subset_{step_i}",
                    )["OUTPUT"]
                    touching_layer.removeSelection()

                    # Full polygon intersections are restricted to selected rescue candidates only.
                    intersection = self._run_raw(
                        "native:intersection",
                        {
                            "INPUT": rescue_subset,
                            "OVERLAY": source_layer,
                            "INPUT_FIELDS": ["_FAB_ID"],
                            "OVERLAY_FIELDS": [ea_field, pd_field],
                            "OVERLAY_FIELDS_PREFIX": "",
                            "GRID_SIZE": None,
                            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                        },
                        context,
                        feedback,
                        f"reattr_fast_intersection_{step_i}",
                    )["OUTPUT"]

                    intersection_layer = self._resolve_vector_layer(
                        intersection, context, f"reattr_fast_intersection_{step_i}_rl"
                    )
                    value_map = {}
                    intersection_pieces = 0
                    rejected_small = 0

                    for feature in intersection_layer.getFeatures():
                        intersection_pieces += 1
                        raw_id = feature["_FAB_ID"]
                        geometry = feature.geometry()
                        if raw_id is None or geometry is None or geometry.isEmpty():
                            continue
                        fab_id = int(raw_id)
                        area = geometry.area()
                        threshold = (
                            MIN_AMBIG_OVERLAP_AREA
                            if fab_id in ambiguous_for_rescue
                            else MIN_OVERLAP_AREA
                        )
                        if area <= threshold:
                            rejected_small += 1
                            continue
                        ea_value = feature[ea_field]
                        pd_value = feature[pd_field]
                        if not _usable_text(ea_value) and not _usable_text(pd_value):
                            continue
                        # For rescue, choose the source assignment with greatest overlap area per fabric ID.
                        current = value_map.get(fab_id)
                        if current is None or area > current[0]:
                            value_map[fab_id] = (area, ea_value, pd_value)

                    # Yield area-dominant rescue assignments for ambiguous/missing cells.
                    def _rescue_change_iter():
                        for fab_id, values in value_map.items():
                            fid = fabid_to_fid.get(fab_id)
                            if fid is None:
                                continue
                            yield fid, {ea_idx: values[1], pd_idx: values[2]}

                    rescue_written = _apply_provider_changes(
                        working_layer,
                        _rescue_change_iter(),
                        f"step {step_i} overlap rescue",
                    )
                    feedback.pushInfo(
                        f"[Reassign-fast] Step {step_i}: rescue candidates touching source="
                        f"{len(selected_fids):,}; pieces={intersection_pieces:,}; "
                        f"assigned={rescue_written:,}; rejected_small={rejected_small:,}; "
                        f"rescue={time.perf_counter() - rescue_t0:.1f} s"
                    )
                else:
                    feedback.pushInfo(
                        f"[Reassign-fast] Step {step_i}: no unresolved/ambiguous cells "
                        f"touch the source; rescue skipped"
                    )

            feedback.pushInfo(
                f"[Reassign-fast] Step {step_i}/{n_steps} complete in "
                f"{time.perf_counter() - step_t0:.1f} s "
                f"(point={point_written:,}, rescue={rescue_written:,})"
            )

            # Save only strategically useful debug outputs on long runs.
            if debug_gpkg_path and step_i in {1, n_steps}:
                _debug_save(pts_join, f"pts_join_{step_i}")

            del join_layer
            del pts_join
            gc.collect()

        # --------------------------------------------------------------
        # 3) One final geometry cleanup and one final full write
        # --------------------------------------------------------------
        # Clean geometry only after completing all timestep assignments to reduce runtime.
        final_t0 = time.perf_counter()
        feedback.pushInfo("[Reassign-fast] All timestep attributes assigned; final geometry cleanup")

        del working_layer
        gc.collect()

        fabric_final = self._delete_field_if_exists(
            fabric,
            "_FAB_ID",
            context,
            feedback,
            "reattr_fast_cleanup_id",
        )
        fabric_final = self._sanitize_polygon_layer(
            fabric_final,
            context,
            feedback,
            "reattr_fast_final",
            min_area=MIN_FABRIC_AREA,
        )
        fabric_final = self._freeze_to_gpkg(
            fabric_final,
            context,
            feedback,
            tag="reattr_fast_final_frozen",
            layer_name="fabric_final",
            create_spatial_index=True,
        )

        final_layer = self._resolve_vector_layer(
            fabric_final, context, "reattr_fast_final_check"
        )
        if final_layer is None or not final_layer.isValid() or final_layer.featureCount() == 0:
            raise QgsProcessingException("[Reassign-fast] Final fabric is invalid or empty")

        _debug_save(fabric_final, "fabric_final")
        feedback.pushInfo(
            f"[Reassign-fast] Final cleanup {time.perf_counter() - final_t0:.1f} s; "
            f"total reassignment {time.perf_counter() - total_t0:.1f} s; "
            f"final cells={final_layer.featureCount():,}"
        )
        return fabric_final

    # Find EA fields dynamically and return them in chronological numeric order.
    # Input EA field naming is normalized at discovery, not during source editing.
    def _discover_ea_step_fields(self, layer, context, feedback):
        """
        Discover chronological EA step fields dynamically.

        Supported names:
        EA1, EA2, EA3
        EA_1, EA_2
        EA01, EA02
        EA_Class_1, EA_Class_2
        EA_CLASS_1, EA_CLASS_2

        Returns:
        list[str] of field names sorted by timestep number.
        """
        import re

        lyr = self._resolve_vector_layer(layer, context, "discover_ea_fields")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException("[ASM] Could not resolve layer for EA field discovery")

        patterns = [
            r"^EA(\d+)$",
            r"^EA_(\d+)$",
            r"^EA_Class_(\d+)$",
            r"^EA_CLASS_(\d+)$",
        ]

        candidates = {}
        for f in lyr.fields():
            name = f.name()
            step_num = None

            for pat in patterns:
                m = re.match(pat, name, flags=re.IGNORECASE)
                if m:
                    try:
                        step_num = int(m.group(1))
                        break
                    except Exception:
                        step_num = None

            if step_num is not None:
                # Keep first match per timestep to avoid duplicates
                if step_num not in candidates:
                    candidates[step_num] = name
                else:
                    feedback.reportError(
                        f"[ASM] Duplicate EA timestep detected for step {step_num}: "
                        f"keeping '{candidates[step_num]}', ignoring '{name}'"
                    )

        if not candidates:
            raise QgsProcessingException(
                "[ASM] No EA step fields found. Expected names like EA1, EA_1, EA_Class_1."
            )

        ea_fields = [candidates[k] for k in sorted(candidates.keys())]

        feedback.pushInfo(f"[ASM] Discovered {len(ea_fields)} EA fields")
        feedback.pushInfo(f"[ASM] EA sequence: {', '.join(ea_fields)}")

        return ea_fields



    # Advance AD/DS/SF state histories and derive chronological/area-independent metrics.
    # Separate T0 provenance, EA evidence, state history, surface age and conditions.
    # History metrics are computed AFTER both source support and initial provenance.
    def _build_assemblage_metrics_from_ea_fields(
        self, layer, ea_fields, period_values, context, feedback,
        stabilisation_years=20.0, stabilisation_mode=0, stable_evidence_classes=None,
    ):
        """Build timestep states and elapsed-year assemblage-history metrics.

        v10.8 state-continuity and storage-age correction
        ---------------------------------
        EA_Class_i remains the direct source/evidence field for timestep i.
        ONTO_STATE_i is now the reconstructed geomorphic state.

        A source-support gap written as ``reworked_unresolved`` no longer erases
        a previously established state. Instead, the last resolved state is
        carried forward until a later observed class changes it. Genuine
        unrecognised nonblank source classes still break state certainty and
        remain UNRESOLVED.

        Depositional Storage is promoted sequentially to Stabilised Floodplain
        using the Module 3B rule selected by the user: elapsed storage years only,
        elapsed years OR explicit stable-surface evidence, or elapsed years AND
        explicit evidence. Episode count is not part of the state-transition rule.
        A resolved INIT_STATE seeds the pre-record T0 condition without fabricating
        a formation or transition event before the observational record.

        Module 4a describes histories only. It does not create authoritative
        risk-table events; transition counts are exported with N_ASM_*_TRANS
        names.
        """
        if layer is None or not layer.isValid():
            raise QgsProcessingException("[Assemblage metrics] Invalid layer supplied.")

        ea_fields = sorted(
            [f.name() for f in layer.fields() if re.match(r"^EA_Class_\d+$", f.name())],
            key=lambda x: int(re.search(r"\d+$", x).group()),
        )
        if not ea_fields:
            raise QgsProcessingException("[Assemblage metrics] No EA_Class_i fields found.")
        if len(period_values) != len(ea_fields):
            raise QgsProcessingException("[Assemblage metrics] EA-state and chronology lengths differ.")

        # Calendar gaps determine age; equal-weight timestep frequency uses observation counts.
        dates = [self._period_text_to_date(v) for v in period_values]
        if any(b <= a for a, b in zip(dates, dates[1:])):
            raise QgsProcessingException("[Assemblage metrics] Period_i dates are not strictly increasing.")
        record_span = (dates[-1] - dates[0]).days / 365.2425 if len(dates) > 1 else 0.0

        # The metrics schema preserves both direct process counts and derived state history.
        existing = {f.name() for f in layer.fields()}
        out_fields = [
            ("N_STEPS", QVariant.Int), ("RECORD_SPAN_YR", QVariant.Double),
            ("N_EVENTS", QVariant.Int), ("N_EROSION", QVariant.Int), ("N_DEPOSITION", QVariant.Int),
            ("N_ISL_ERO", QVariant.Int), ("N_ISL_DEP", QVariant.Int),
            ("N_ST_CH", QVariant.Int), ("N_ST_IS", QVariant.Int), ("N_ST_FP", QVariant.Int),
            ("N_INACTIVE", QVariant.Int), ("N_RAW_UNRES", QVariant.Int),
            ("N_STATE_CARRY", QVariant.Int), ("N_STATE_PROMOTE", QVariant.Int),
            ("LAST_RES_STEP", QVariant.Int), ("LAST_RES_STATE", QVariant.String),
            ("FINAL_CARRIED", QVariant.Int),
            ("N_ACTIVE_DOM", QVariant.Int), ("ACTIVE_DOM_FREQ", QVariant.Double),
            ("N_STAB_FP", QVariant.Int), ("STAB_FP_FREQ", QVariant.Double),
            ("N_STORAGE", QVariant.Int), ("STORAGE_FREQ", QVariant.Double),
            ("N_ASM_REACTIVATE_TRANS", QVariant.Int), ("N_ASM_STORAGE_TRANS", QVariant.Int),
            ("N_ASM_STABILISE_TRANS", QVariant.Int), ("N_ASM_STORAGE_REWORK_TRANS", QVariant.Int),
            ("N_ASM_FP_STORAGE_TRANS", QVariant.Int), ("N_ASM_ANY_TRANS", QVariant.Int),
            ("FIRST_STORAGE", QVariant.Int), ("LAST_STORAGE", QVariant.Int),
            ("LAST_STORAGE_STATE", QVariant.Int),
            ("FIRST_STORAGE_ENTRY", QVariant.Int), ("LAST_STORAGE_ENTRY", QVariant.Int),
            ("STORAGE_AGE_YR", QVariant.Double), ("STORAGE_AGE_STEP", QVariant.Int),
            ("SINCE_STORAGE_STATE_YR", QVariant.Double), ("SINCE_STORAGE_STATE_STEP", QVariant.Int),
            ("SINCE_STORAGE", QVariant.Double), ("SINCE_STORAGE_YR", QVariant.Double), ("SINCE_STORAGE_STEP", QVariant.Int),
            ("FINAL_ONTO_RAW", QVariant.String), ("FINAL_ONTO_STATE", QVariant.String), ("ONTO_STATE", QVariant.String),
            ("FP_CONDITION", QVariant.String), ("FP_STAB", QVariant.Int), ("FP_RECENT", QVariant.Int),
            ("FP_REWORKED", QVariant.Int), ("SURFACE_AGE_EST", QVariant.Double),
            ("AGE_CENSORED", QVariant.Int), ("MIN_PERSIST_YR", QVariant.Double),
            ("SURFACE_AGE_TYPE", QVariant.String), ("STORAGE_AGE_CENS", QVariant.Int),
            ("SF_PROV", QVariant.String), ("STATE_DETAIL", QVariant.String),
            ("ASM_STAB_YEARS", QVariant.Double), ("ASM_STAB_MODE", QVariant.Int),
            ("SINCE_DISTURB_YR", QVariant.Double), ("SINCE_DISTURB_STEP", QVariant.Int),
            ("ONTO_TRANS_SUM", QVariant.String),
            ("ASM_SHANNON", QVariant.Double), ("ASM_H_NORM", QVariant.Double),
            ("ASM_RICHNESS", QVariant.Int), ("ASM_H_CLASS", QVariant.String),
            ("DIST_COUNT", QVariant.Int), ("DIST_FREQ", QVariant.Double),
            ("DOM_RATIO", QVariant.Double), ("NET_BAL", QVariant.Double),
            ("N_EPISODES", QVariant.Int), ("ZERO_EPISODE", QVariant.Int),
            ("MAX_QUIET", QVariant.Double), ("MAX_QUIET_YR", QVariant.Double), ("MAX_QUIET_STEP", QVariant.Int),
            ("QUIET_RATIO", QVariant.Double),
            ("FIRST_ACTIVE", QVariant.Int), ("LAST_ACTIVE", QVariant.Int),
            ("SINCE_ACTIVE", QVariant.Double), ("SINCE_ACTIVE_YR", QVariant.Double), ("SINCE_ACTIVE_STEP", QVariant.Int),
            ("ASM_FREQ", QVariant.String), ("ASM_STYLE", QVariant.String),
            ("STRUCTURE_CL", QVariant.String), ("ASM_LABEL", QVariant.String),
            ("ACTIVITY_CL", QVariant.String), ("DOMINANCE_CL", QVariant.String),
            ("PRIMARY_STATE", QVariant.String), ("DOMAIN_CLASS", QVariant.String),
            ("DOMAIN_STATE", QVariant.String), ("DEPO_INTERP", QVariant.String),
            ("ASM_ONTOLOGY", QVariant.String), ("ASM_CLASS", QVariant.String),
            ("ISLAND_CONTEXT", QVariant.String),
        ]
        # ONTO_STATE_i fields store reconstructed states, one for each dated EA source.
        for i in range(1, len(ea_fields) + 1):
            out_fields.append((f"ONTO_STATE_{i}", QVariant.String))

        provider = layer.dataProvider()
        new_fields = []
        for name, typ in out_fields:
            if name not in existing:
                fld = QgsField(name, typ)
                if typ == QVariant.String:
                    if name == "ONTO_TRANS_SUM":
                        history_len = min(65535, max(4096, 64 * max(1, len(ea_fields) - 1)))
                        fld.setLength(history_len)
                    else:
                        fld.setLength(120)
                new_fields.append(fld)
        if new_fields:
            if not provider.addAttributes(new_fields):
                raise QgsProcessingException("[Assemblage metrics] Could not add metric fields.")
            layer.updateFields()

        field_index = {f.name(): i for i, f in enumerate(layer.fields())}

        # Normalise raw evidence strings without changing source EA_Class_i columns.
        # The evidence dictionaries intentionally include historical class aliases.
        def clean(v):
            if v is None:
                return ""
            try:
                if hasattr(v, "isNull") and v.isNull():
                    return ""
            except Exception:
                pass
            return str(v).strip().lower().replace(" ", "_").replace("-", "_")

        # Recognise erosion evidence, including island erosion, from EA classes.
        def is_erosion(v):
            return v in {
                "erosion", "bank_erosion", "channel_erosion",
                "island_erosion", "island_ero", "isl_erosion",
            }

        # Recognise mapped deposition evidence, including island deposition.
        def is_deposition(v):
            return v in {
                "deposition", "bank_deposition", "channel_deposition",
                "migration_deposition", "infill_deposition",
                "island_deposition", "island_dep", "isl_deposition",
            }

        # Identify channel/active persistence classes in raw evidence.
        def is_stable_channel(v):
            return v in {
                "stable_channel", "channel", "channel_surface",
                "active_channel", "water", "inchannel_surface",
            }

        # Recognise only explicitly stabilised/vegetated islands as SF support.
        def is_stable_island(v):
            # Only explicitly stable/vegetated island classes are treated as
            # Stabilised Floodplain. A generic ``island`` label is not sufficient
            # provenance to distinguish stable island from transient bar/storage.
            return v in {
                "stable_island", "vegetated_island",
            }

        # Recognise direct stable-floodplain classes from EA evidence.
        def is_stable_fp(v):
            return v in {
                "stable_floodplain", "inactive_floodplain",
                "persistent_floodplain", "floodplain", "stable_fp",
                "stabilised_floodplain", "stabilized_floodplain",
            }

        # Map direct EA class to its evidence-supported ontology state.
        # Raw EA evidence and the reconstructed chronological state need not coincide.
        def onto_raw(v):
            if (
                is_deposition(v)
                or v in {
                    "depositional_storage", "active_storage", "storage",
                    "bar_deposition", "new_bar", "bar", "bar_storage",
                }
            ):
                return "DEPOSITIONAL_STORAGE"
            if (
                is_erosion(v)
                or is_stable_channel(v)
                or v in {
                    "active_domain", "active_braidplain",
                    "active_zone", "active_water",
                }
            ):
                return "ACTIVE_DOMAIN"
            if is_stable_fp(v) or is_stable_island(v) or v in {"vegetated_floodplain"}:
                return "STABILISED_FLOODPLAIN"
            return "UNRESOLVED"

        # Identify unsupported intervals where last recognised state may be carried.
        def is_carry_gap(v):
            # This value is inserted by _apply_corridor_background_policy where
            # the timestep has no direct EA assignment. It is a support status,
            # not positive evidence that the geomorphic state disappeared.
            return v in {
                "reworked_unresolved",
                "unsupported_non_event",
                "state_carry_gap",
            }

        # Return elapsed years since most recent recognised occurrence in a date-index list.
        # Elapsed years derive from actual observation dates; step count is separate.
        def elapsed_since(indices):
            if not indices:
                return record_span
            return max(0.0, (dates[-1] - dates[indices[-1]]).days / 365.2425)

        # Report elapsed observation steps, not elapsed calendar years.
        def steps_since(indices):
            return len(ea_fields) if not indices else len(ea_fields) - 1 - indices[-1]

        # Count contiguous runs of disturbances, distinct from individual EA events.
        def count_episodes(flags):
            return sum(
                1
                for i, flag in enumerate(flags)
                if flag and (i == 0 or not flags[i - 1])
            )

        # Find longest uninterrupted run of nondisturbance observations.
        def longest_false_run_steps(flags):
            best = cur = 0
            for flag in flags:
                if not flag:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
            return best

        # Find longest quiet interval in elapsed calendar years, respecting irregular gaps.
        def longest_quiet_years(flags):
            if len(dates) <= 1:
                return 0.0
            best = cur = 0.0
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i - 1]).days / 365.2425
                if not flags[i]:
                    cur += gap
                    best = max(best, cur)
                else:
                    cur = 0.0
            return best

        # Classify normalised three-state Shannon diversity; zero richness is unresolved.
        def shannon_class(h_norm, richness):
            if richness <= 0:
                return "unresolved"
            if richness == 1 or h_norm <= 1e-9:
                return "single_state"
            if h_norm < 0.33:
                return "low_diversity"
            if h_norm < 0.66:
                return "moderate_diversity"
            return "high_diversity"

        # Episode count is descriptive; it cannot independently promote DS to SF.
        PERSISTENCE_YEARS = max(0.0, float(stabilisation_years))
        STABILISATION_MODE = int(stabilisation_mode)
        if STABILISATION_MODE not in (0, 1, 2):
            raise QgsProcessingException("[Assemblage metrics] STABILISATION_MODE must be 0, 1 or 2.")
        stable_evidence_set = {
            clean(v) for v in (stable_evidence_classes or []) if clean(v)
        }
        REWORKED_EPISODES_FOR_CONDITION = 3

        # Check direct EA stable-surface support against the configured class set.
        def stable_evidence(v):
            return clean(v) in stable_evidence_set

        # Implement configurable elapsed-time and stable-evidence stabilisation decision.
        def stabilisation_met(age_yr, evidence_ok):
            age_ok = age_yr is not None and float(age_yr) + 1e-9 >= PERSISTENCE_YEARS
            ev_ok = bool(evidence_ok)
            if STABILISATION_MODE == 1:
                return age_ok or ev_ok
            if STABILISATION_MODE == 2:
                return age_ok and ev_ok
            return age_ok

        VALID_STATES = {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}

        # Read metric inputs as geometry-free feature batches to reduce IO and memory.
        req0 = QgsFeatureRequest()
        req0.setNoAttributes()
        req0.setFlags(QgsFeatureRequest.NoGeometry)
        fids = [ft.id() for ft in layer.getFeatures(req0)]

        processed = 0
        total_carried_steps = 0
        total_promoted_steps = 0
        final_raw_unresolved_but_resolved = 0

        for offset in range(0, len(fids), 5000):
            req = QgsFeatureRequest()
            req.setFilterFids(list(fids[offset:offset + 5000]))
            initial_attr_names = [
                n for n in ["INIT_STATE", "INIT_PROV", "INIT_CONTEXT", "INIT_CONF",
                            "INIT_SOURCE", "LEFT_CENS", "INIT_SF_PROV", "INIT_STORAGE"]
                if layer.fields().indexFromName(n) >= 0
            ]
            req.setSubsetOfAttributes(ea_fields + initial_attr_names, layer.fields())
            req.setFlags(QgsFeatureRequest.NoGeometry)
            batch = {}

            # Per fabric cell: read direct evidence and advance one history from its T0 seed.
            for feat in layer.getFeatures(req):
                vals = [clean(feat[n]) for n in ea_fields]
                raw_states = [onto_raw(v) for v in vals]
                n_steps = len(vals)

                # Erosion/deposition evidence marks disturbances, not eligible transition-risk events.
                er = [is_erosion(v) for v in vals]
                dep = [is_deposition(v) for v in vals]
                disturbance = [a or b for a, b in zip(er, dep)]

                # ------------------------------------------------------
                # Reconstruct a continuous state chronology from a separate T0 seed.
                # The transition semantics mirror Module 3B wherever the polygon
                # EA evidence can express the same process distinction.
                # ------------------------------------------------------
                # Do not equate previous mapped EA class with prior state: use INIT_STATE first.
                init_state = str(feat["INIT_STATE"] or "UNRESOLVED").strip().upper() if "INIT_STATE" in initial_attr_names else "UNRESOLVED"
                if init_state not in VALID_STATES:
                    init_state = "UNRESOLVED"
                init_left_cens = int(feat["LEFT_CENS"] or 0) if "LEFT_CENS" in initial_attr_names else 0
                init_context = clean(feat["INIT_CONTEXT"]) if "INIT_CONTEXT" in initial_attr_names else "unknown"
                init_sf_prov = str(feat["INIT_SF_PROV"] or "not_applicable") if "INIT_SF_PROV" in initial_attr_names else "not_applicable"

                states = []
                carried_flags = []
                promoted_flags = []
                # A current storage-derived surface is tracked separately from temporary DS
                # occupancy; T0 storage is censored because the start date is unknown.
                current_state = init_state if init_state in VALID_STATES else None
                storage_clock_age = 0.0 if current_state == "DEPOSITIONAL_STORAGE" else None
                surface_storage_origin_index = 0 if current_state == "DEPOSITIONAL_STORAGE" else None
                storage_origin_censored = bool(current_state == "DEPOSITIONAL_STORAGE" and init_left_cens)
                surface_age_censored = bool(current_state in {"DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"} and init_left_cens)
                last_disturbance_index = None
                episodes_so_far = 0
                previous_was_disturbance = False
                last_resolved_step = 0
                last_resolved_state = init_state if init_state in VALID_STATES else "UNRESOLVED"

                # Transition decisions are sequential and condition on the last reconstructed state.
                for i, (v, raw_state) in enumerate(zip(vals, raw_states)):
                    if disturbance[i]:
                        if not previous_was_disturbance:
                            episodes_so_far += 1
                        last_disturbance_index = i
                    previous_was_disturbance = disturbance[i]

                    carried = False
                    promoted = False
                    previous_state = current_state
                    # Age accrued per timestep uses elapsed calendar years, not an assumed annual step.
                    interval_years = 0.0 if i == 0 else max(0.0, (dates[i] - dates[i - 1]).days / 365.2425)
                    active_signal = raw_state == "ACTIVE_DOMAIN"
                    storage_signal = raw_state == "DEPOSITIONAL_STORAGE"
                    stable_signal = raw_state == "STABILISED_FLOODPLAIN"
                    stable_ev = stable_evidence(v)
                    gap = is_carry_gap(v)

                    # Observed Active Domain occupancy resets storage and current surface-age inference.
                    if active_signal:
                        current_state = "ACTIVE_DOMAIN"
                        storage_clock_age = None
                        surface_storage_origin_index = None
                        storage_origin_censored = False
                        surface_age_censored = False

                    # Leaving AD enters DS; a direct AD -> SF jump is prohibited.
                    elif previous_state == "ACTIVE_DOMAIN":
                        if gap:
                            # No positive evidence that Active Domain occupation ended.
                            current_state = "ACTIVE_DOMAIN"
                            carried = True
                        elif storage_signal or stable_signal or dep[i]:
                            # Module 3B invariant: Active Domain cannot jump directly
                            # to Stabilised Floodplain. Departure enters Storage first.
                            current_state = "DEPOSITIONAL_STORAGE"
                            storage_clock_age = 0.0
                            surface_storage_origin_index = i
                            storage_origin_censored = False
                            surface_age_censored = False
                        else:
                            current_state = None
                            storage_clock_age = None
                            surface_storage_origin_index = None
                            storage_origin_censored = False
                            surface_age_censored = False

                    # Continued DS accrues time; fresh deposition restarts its storage clock.
                    elif previous_state == "DEPOSITIONAL_STORAGE":
                        if dep[i]:
                            # Fresh deposition/reworking resets the storage clock.
                            current_state = "DEPOSITIONAL_STORAGE"
                            storage_clock_age = 0.0
                            surface_storage_origin_index = i
                            storage_origin_censored = False
                            surface_age_censored = False
                        elif storage_signal or stable_signal or gap:
                            storage_clock_age = float(storage_clock_age or 0.0) + interval_years
                            current_state = "DEPOSITIONAL_STORAGE"
                            carried = bool(gap)
                            # Only then test whether elapsed time and/or stable evidence permits promotion.
                            if stabilisation_met(storage_clock_age, stable_ev):
                                current_state = "STABILISED_FLOODPLAIN"
                                promoted = True
                        else:
                            current_state = None
                            storage_clock_age = None
                            surface_storage_origin_index = None
                            storage_origin_censored = False
                            surface_age_censored = False

                    # An established SF can become storage following new deposition or remain stable.
                    elif previous_state == "STABILISED_FLOODPLAIN":
                        if dep[i] or storage_signal:
                            current_state = "DEPOSITIONAL_STORAGE"
                            storage_clock_age = 0.0
                            surface_storage_origin_index = i
                            storage_origin_censored = False
                            surface_age_censored = False
                        elif stable_signal or gap:
                            current_state = "STABILISED_FLOODPLAIN"
                            carried = bool(gap)
                        else:
                            current_state = None
                            storage_clock_age = None
                            surface_storage_origin_index = None
                            storage_origin_censored = False
                            surface_age_censored = False

                    else:
                        # Without prior resolved state, derive only what positive evidence supports.
                        # No recognised prior state: use direct positive evidence only.
                        if storage_signal or dep[i]:
                            current_state = "DEPOSITIONAL_STORAGE"
                            storage_clock_age = 0.0
                            surface_storage_origin_index = i
                            storage_origin_censored = False
                            surface_age_censored = False
                        elif stable_signal:
                            current_state = "STABILISED_FLOODPLAIN"
                            storage_clock_age = None
                            surface_storage_origin_index = None
                            storage_origin_censored = False
                            surface_age_censored = False
                        else:
                            current_state = None

                    # Keep UNKNOWN rather than converting a missing state to stable floodplain.
                    state = current_state if current_state is not None else "UNRESOLVED"
                    if state != "UNRESOLVED":
                        last_resolved_step = i + 1
                        last_resolved_state = state
                    states.append(state)
                    carried_flags.append(carried)
                    promoted_flags.append(promoted)

                n_state_carry = sum(carried_flags)
                n_state_promote = sum(promoted_flags)
                total_carried_steps += n_state_carry
                total_promoted_steps += n_state_promote

                # Time fractions count dated observation steps; they are not duration-weighted.
                active_occ = [st == "ACTIVE_DOMAIN" for st in states]
                storage = [st == "DEPOSITIONAL_STORAGE" for st in states]
                stab = [st == "STABILISED_FLOODPLAIN" for st in states]
                recognized = [st for st in states if st != "UNRESOLVED"]

                n_erosion = sum(er)
                n_deposition = sum(dep)
                n_events = sum(disturbance)
                n_isl_ero = sum(
                    v in {"island_erosion", "island_ero", "isl_erosion"}
                    for v in vals
                )
                n_isl_dep = sum(
                    v in {"island_deposition", "island_dep", "isl_deposition"}
                    for v in vals
                )
                n_st_ch = sum(is_stable_channel(v) for v in vals)
                n_st_is = sum(is_stable_island(v) for v in vals)
                n_st_fp = sum(is_stable_fp(v) for v in vals)

                # N_INACTIVE remains the legacy unresolved-count field, but now
                # refers to the reconstructed state chronology. N_RAW_UNRES
                # preserves the direct source-to-state unresolved count.
                n_inactive = sum(st == "UNRESOLVED" for st in states)
                n_raw_unres = sum(st == "UNRESOLVED" for st in raw_states)

                n_active = sum(active_occ)
                n_storage = sum(storage)
                n_stab = sum(stab)
                active_freq = n_active / n_steps if n_steps else 0.0
                storage_freq = n_storage / n_steps if n_steps else 0.0
                stab_freq = n_stab / n_steps if n_steps else 0.0

                # The T0 initial state participates in historical transition counting,
                # but pre-record genesis is never explicitly invented.
                transition_states = [init_state] + states
                transition_pairs = list(zip(transition_states, transition_states[1:]))
                trans = [f"{a}_to_{b}" for a, b in transition_pairs]
                n_react = sum(a == "STABILISED_FLOODPLAIN" and b == "ACTIVE_DOMAIN" for a, b in transition_pairs)
                n_store = sum(a == "ACTIVE_DOMAIN" and b == "DEPOSITIONAL_STORAGE" for a, b in transition_pairs)
                n_stabilise = sum(a == "DEPOSITIONAL_STORAGE" and b == "STABILISED_FLOODPLAIN" for a, b in transition_pairs)
                n_storage_rework = sum(a == "DEPOSITIONAL_STORAGE" and b == "ACTIVE_DOMAIN" for a, b in transition_pairs)
                n_fp_storage = sum(a == "STABILISED_FLOODPLAIN" and b == "DEPOSITIONAL_STORAGE" for a, b in transition_pairs)
                n_any = sum(
                    a != b and a in VALID_STATES and b in VALID_STATES
                    for a, b in transition_pairs
                )

                # Indices distinguish first and last active evidence from the age calculations.
                active_idx = [i for i, x in enumerate(active_occ) if x]
                storage_idx = [i for i, x in enumerate(storage) if x]
                disturb_idx = [i for i, x in enumerate(disturbance) if x]

                first_active = active_idx[0] + 1 if active_idx else 0
                last_active = active_idx[-1] + 1 if active_idx else 0

                # Storage occupancy and storage entry are deliberately separate.
                # FIRST_STORAGE/LAST_STORAGE retain reconstructed state-occupancy
                # semantics. A new entry is recorded when the reconstructed state
                # becomes Depositional Storage after another state, or when a new
                # deposition event reworks an already-storage surface.
                # Storage occupancy is not interchangeable with new storage entry/re-entry.
                first_storage = storage_idx[0] + 1 if storage_idx else 0
                last_storage = storage_idx[-1] + 1 if storage_idx else 0
                last_storage_state = last_storage

                # T0 left-censored storage is not counted as a new observed formation event.
                storage_entry_idx = []
                for j, st in enumerate(states):
                    if st != "DEPOSITIONAL_STORAGE":
                        continue
                    previous_st = states[j - 1] if j > 0 else init_state
                    # A T0 left-censored storage seed is occupancy, not an observed
                    # Active->Storage formation event. Only a later entry/re-entry or
                    # deposition reset is recorded as FIRST/LAST_STORAGE_ENTRY.
                    if previous_st != "DEPOSITIONAL_STORAGE" or dep[j]:
                        storage_entry_idx.append(j)

                first_storage_entry = storage_entry_idx[0] + 1 if storage_entry_idx else 0
                last_storage_entry = storage_entry_idx[-1] + 1 if storage_entry_idx else 0

                # Elapsed active/disturbance recency uses the calendar chronology.
                since_active_yr = elapsed_since(active_idx)
                since_disturb_yr = elapsed_since(disturb_idx)
                since_active_step = steps_since(active_idx)
                since_disturb_step = steps_since(disturb_idx)

                # Legacy DS occupancy recency is zero when the endpoint still occupies DS.
                # Legacy occupancy timing: zero while storage occupies the endpoint.
                since_storage_state_yr = elapsed_since(storage_idx)
                since_storage_state_step = steps_since(storage_idx)

                # Storage-derived age persists into SF after DS promotion when origin known.
                # Current storage-derived surface age. It remains valid after
                # persistence promotion to Stabilised Floodplain, but is zero when
                # the final state is Active Domain or no storage entry is known.
                if (
                    surface_storage_origin_index is not None
                    and states
                    and states[-1] in {"DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}
                ):
                    last_entry_idx = int(surface_storage_origin_index)
                    storage_age_yr = max(
                        0.0,
                        (dates[-1] - dates[last_entry_idx]).days / 365.2425,
                    )
                    storage_age_step = len(ea_fields) - 1 - last_entry_idx
                    storage_age_cens = 1 if storage_origin_censored else 0
                else:
                    storage_age_yr = 0.0
                    storage_age_step = 0
                    storage_age_cens = 0

                # Compatibility aliases keep downstream surface-age scripts readable.
                # Compatibility aliases used by the surface-age workflow.
                since_storage_yr = storage_age_yr
                since_storage_step = storage_age_step

                # Episode structure and quiet duration describe history; they do not define states.
                n_episodes = count_episodes(disturbance)
                max_quiet_step = longest_false_run_steps(disturbance)
                max_quiet_yr = longest_quiet_years(disturbance)
                quiet_ratio = (
                    max_quiet_yr / record_span
                    if record_span > 0
                    else (1.0 if n_events == 0 else 0.0)
                )
                dist_freq = n_events / n_steps if n_steps else 0.0
                dom_ratio = (
                    abs(n_erosion - n_deposition) / n_events
                    if n_events
                    else 0.0
                )
                net_bal = (
                    (n_deposition - n_erosion) / n_steps
                    if n_steps
                    else 0.0
                )

                # Shannon diversity uses proportions of recognised 3-state observation counts.
                counts = {
                    st: recognized.count(st)
                    for st in {
                        "ACTIVE_DOMAIN",
                        "DEPOSITIONAL_STORAGE",
                        "STABILISED_FLOODPLAIN",
                    }
                }
                positive = [c for c in counts.values() if c > 0]
                richness = len(positive)
                if positive:
                    probs = [c / sum(positive) for c in positive]
                    H = -sum(p * math.log(p) for p in probs)
                    Hn = H / math.log(3.0)
                else:
                    H = Hn = 0.0

                # The final raw evidence may be unresolved while historical continuity is resolved.
                final_raw = raw_states[-1] if raw_states else "UNRESOLVED"
                final_state = states[-1] if states else "UNRESOLVED"
                final_carried = 1 if (carried_flags[-1] if carried_flags else False) else 0

                if final_raw == "UNRESOLVED" and final_state != "UNRESOLVED":
                    final_raw_unresolved_but_resolved += 1

                # FP_CONDITION is a descriptive within-SF reworking category, not a fourth state.
                if final_state == "ACTIVE_DOMAIN":
                    fp_condition = "active domain"
                elif final_state == "DEPOSITIONAL_STORAGE":
                    fp_condition = "depositional storage"
                elif final_state == "STABILISED_FLOODPLAIN":
                    if n_episodes >= REWORKED_EPISODES_FOR_CONDITION:
                        fp_condition = "reworked floodplain"
                    elif since_disturb_yr >= PERSISTENCE_YEARS:
                        fp_condition = "persistent floodplain"
                    else:
                        fp_condition = "recent floodplain"
                else:
                    fp_condition = "unresolved"

                # Age censoring denotes inherited T0 provenance; check it before interpreting ages.
                fp_stab = 1 if final_state == "STABILISED_FLOODPLAIN" else 0
                fp_recent = 1 if fp_condition == "recent floodplain" else 0
                fp_reworked = 1 if fp_condition == "reworked floodplain" else 0

                age_censored = 1 if (surface_age_censored and final_state in {"DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}) else 0
                min_persist_yr = since_disturb_yr if age_censored else since_disturb_yr
                surface_age_type = "minimum_observed_persistence" if age_censored else "observed_since_last_disturbance"
                if final_state == "STABILISED_FLOODPLAIN":
                    if age_censored and init_state == "STABILISED_FLOODPLAIN":
                        sf_prov = init_sf_prov if init_sf_prov not in {"", "not_applicable"} else ("prior_stable_island" if init_context == "island" else "prior_floodplain")
                    elif age_censored and init_state == "DEPOSITIONAL_STORAGE":
                        sf_prov = "prior_storage_stabilised"
                    elif surface_storage_origin_index is not None:
                        sf_prov = "assembled_after_t0"
                    else:
                        sf_prov = "observed_stable_evidence"
                else:
                    # SF provenance distinguishes prior surfaces, assembled surfaces, and direct evidence.
                    sf_prov = "not_stabilised"

                if final_state == "STABILISED_FLOODPLAIN" and sf_prov == "prior_stable_island":
                    state_detail = "stable_island"
                elif final_state == "STABILISED_FLOODPLAIN":
                    state_detail = "stabilised_floodplain"
                elif final_state == "DEPOSITIONAL_STORAGE":
                    state_detail = "bar_storage" if init_context in {"bar", "bar_storage"} and age_censored else "depositional_storage"
                elif final_state == "ACTIVE_DOMAIN":
                    state_detail = "active_domain"
                else:
                    state_detail = "unresolved"

                if not recognized:
                    # A zero-event cell with no resolved state is genuinely
                    # unresolved. Do not let the 0 >= max(0, 0) tie classify it
                    # as stable_floodplain.
                    asm_freq = "unresolved"
                elif n_events == 0:
                    asm_freq = "stable"
                elif dist_freq < 0.10:
                    asm_freq = "low"
                elif dist_freq < 0.30:
                    asm_freq = "moderate"
                else:
                    # History-frequency classes must not mislabel never-resolved cells as stable.
                    asm_freq = "high"

                # PRIMARY_STATE is an endpoint-state field. Historical
                # disturbance/process character remains in ASM_STYLE and
                # DOMINANCE_CL.
                primary = {
                    "ACTIVE_DOMAIN": "active_domain",
                    "DEPOSITIONAL_STORAGE": "depositional_storage",
                    "STABILISED_FLOODPLAIN": "stabilised_floodplain",
                }.get(final_state, "unresolved")

                if not recognized:
                    asm_style = "unresolved"
                    structure = "unresolved"
                elif n_events == 0:
                    # Historical process-style label; PRIMARY_STATE remains tied
                    # to the final reconstructed state.
                    if counts["STABILISED_FLOODPLAIN"] >= max(
                        counts["ACTIVE_DOMAIN"],
                        counts["DEPOSITIONAL_STORAGE"],
                    ):
                        asm_style = "stable_floodplain"
                    elif counts["ACTIVE_DOMAIN"] >= counts["DEPOSITIONAL_STORAGE"]:
                        asm_style = "stable_channel"
                    else:
                        asm_style = "stable_island"
                    structure = "stable"
                else:
                    ef = n_erosion / max(1, n_events)
                    df = n_deposition / max(1, n_events)
                    asm_style = (
                        "erosion_dominated"
                        if ef >= 0.6
                        # ASM_STYLE is a process-dominance descriptor; PRIMARY_STATE is the final ontology state.
                        else ("deposition_dominated" if df >= 0.6 else "mixed")
                    )
                    structure = (
                        "single_episode"
                        if n_episodes == 1
                        else (
                            "continuous"
                            if quiet_ratio <= 0.20
                            else (
                                "episodic"
                                if quiet_ratio <= 0.50 and n_episodes <= 3
                                else "intermittent"
                            )
                        )
                    )

                label = (
                    "unresolved"
                    if not recognized
                    else (
                        f"{asm_freq}_{asm_style}_{structure}"
                        if n_events
                        else asm_style
                    )
                )
                domain_state = {
                    "ACTIVE_DOMAIN": "active_domain",
                    "DEPOSITIONAL_STORAGE": "depositional_storage",
                    "STABILISED_FLOODPLAIN": "stabilised_floodplain",
                }.get(final_state, "unresolved")

                updates = {
                    "N_STEPS": n_steps,
                    "RECORD_SPAN_YR": record_span,
                    "N_EVENTS": n_events,
                    "N_EROSION": n_erosion,
                    "N_DEPOSITION": n_deposition,
                    "N_ISL_ERO": n_isl_ero,
                    "N_ISL_DEP": n_isl_dep,
                    "N_ST_CH": n_st_ch,
                    "N_ST_IS": n_st_is,
                    "N_ST_FP": n_st_fp,
                    "N_INACTIVE": n_inactive,
                    "N_RAW_UNRES": n_raw_unres,
                    "N_STATE_CARRY": n_state_carry,
                    "N_STATE_PROMOTE": n_state_promote,
                    "LAST_RES_STEP": last_resolved_step,
                    "LAST_RES_STATE": last_resolved_state,
                    "FINAL_CARRIED": final_carried,
                    "N_ACTIVE_DOM": n_active,
                    "ACTIVE_DOM_FREQ": active_freq,
                    "N_STAB_FP": n_stab,
                    "STAB_FP_FREQ": stab_freq,
                    "N_STORAGE": n_storage,
                    "STORAGE_FREQ": storage_freq,
                    "N_ASM_REACTIVATE_TRANS": n_react,
                    "N_ASM_STORAGE_TRANS": n_store,
                    "N_ASM_STABILISE_TRANS": n_stabilise,
                    "N_ASM_STORAGE_REWORK_TRANS": n_storage_rework,
                    "N_ASM_FP_STORAGE_TRANS": n_fp_storage,
                    "N_ASM_ANY_TRANS": n_any,
                    "FIRST_STORAGE": first_storage,
                    "LAST_STORAGE": last_storage,
                    "LAST_STORAGE_STATE": last_storage_state,
                    "FIRST_STORAGE_ENTRY": first_storage_entry,
                    "LAST_STORAGE_ENTRY": last_storage_entry,
                    "STORAGE_AGE_YR": storage_age_yr,
                    "STORAGE_AGE_STEP": storage_age_step,
                    # The updates mapping exposes field meanings without modifying raw evidence columns.
                    "SINCE_STORAGE_STATE_YR": since_storage_state_yr,
                    "SINCE_STORAGE_STATE_STEP": since_storage_state_step,
                    "SINCE_STORAGE": since_storage_yr,
                    "SINCE_STORAGE_YR": since_storage_yr,
                    "SINCE_STORAGE_STEP": since_storage_step,
                    "FINAL_ONTO_RAW": final_raw,
                    "FINAL_ONTO_STATE": final_state,
                    "ONTO_STATE": final_state,
                    "FP_CONDITION": fp_condition,
                    "FP_STAB": fp_stab,
                    "FP_RECENT": fp_recent,
                    "FP_REWORKED": fp_reworked,
                    "SURFACE_AGE_EST": since_disturb_yr,
                    "AGE_CENSORED": age_censored,
                    "MIN_PERSIST_YR": min_persist_yr,
                    "SURFACE_AGE_TYPE": surface_age_type,
                    "STORAGE_AGE_CENS": storage_age_cens,
                    "SF_PROV": sf_prov,
                    "STATE_DETAIL": state_detail,
                    "ASM_STAB_YEARS": PERSISTENCE_YEARS,
                    "ASM_STAB_MODE": STABILISATION_MODE,
                    "SINCE_DISTURB_YR": since_disturb_yr,
                    "SINCE_DISTURB_STEP": since_disturb_step,
                    "ONTO_TRANS_SUM": ";".join(trans),
                    "ASM_SHANNON": round(H, 6),
                    "ASM_H_NORM": round(Hn, 6),
                    "ASM_RICHNESS": richness,
                    "ASM_H_CLASS": shannon_class(Hn, richness),
                    "DIST_COUNT": n_events,
                    "DIST_FREQ": dist_freq,
                    "DOM_RATIO": dom_ratio,
                    "NET_BAL": net_bal,
                    "N_EPISODES": n_episodes,
                    "ZERO_EPISODE": 1 if n_episodes == 0 else 0,
                    "MAX_QUIET": max_quiet_yr,
                    "MAX_QUIET_YR": max_quiet_yr,
                    "MAX_QUIET_STEP": max_quiet_step,
                    "QUIET_RATIO": quiet_ratio,
                    "FIRST_ACTIVE": first_active,
                    "LAST_ACTIVE": last_active,
                    "SINCE_ACTIVE": since_active_yr,
                    "SINCE_ACTIVE_YR": since_active_yr,
                    "SINCE_ACTIVE_STEP": since_active_step,
                    "ASM_FREQ": asm_freq,
                    "ASM_STYLE": asm_style,
                    "STRUCTURE_CL": structure,
                    "ASM_LABEL": label,
                    "ACTIVITY_CL": asm_freq,
                    "DOMINANCE_CL": asm_style,
                    "PRIMARY_STATE": primary,
                    "DOMAIN_CLASS": domain_state,
                    "DOMAIN_STATE": domain_state,
                    "DEPO_INTERP": "deposition_is_storage_until_module3b_stabilisation_rule",
                    "ASM_ONTOLOGY": "active_domain_storage_stabilised_floodplain",
                    "ASM_CLASS": label,
                    "ISLAND_CONTEXT": (
                        "island_present"
                        if n_isl_ero + n_isl_dep + n_st_is > 0
                        else "none"
                    ),
                }

                for i, state in enumerate(states, 1):
                    updates[f"ONTO_STATE_{i}"] = state

                batch[feat.id()] = {
                    field_index[k]: v
                    for k, v in updates.items()
                }
                processed += 1

            if batch and not provider.changeAttributeValues(batch):
                raise QgsProcessingException(
                    "[Assemblage metrics] Provider batch update failed."
                )
            feedback.pushInfo(
                f"[Assemblage metrics] Processed {processed:,}/{len(fids):,} cells"
            )

        feedback.pushInfo(
            "[Assemblage metrics] v10.9 state continuity: EA_Class_i retains direct "
            "source evidence; INIT_STATE seeds T0 provenance; ONTO_STATE_i carries "
            "resolved states through reworked_unresolved support gaps."
        )
        feedback.pushInfo(
            "[Assemblage metrics] Storage timing: FIRST/LAST_STORAGE describe state "
            "occupancy; FIRST/LAST_STORAGE_ENTRY describe entry/re-entry; "
            "SINCE_STORAGE and STORAGE_AGE_YR are elapsed years since the most recent "
            "entry into the current storage-derived surface."
        )
        feedback.pushInfo(
            "[Assemblage metrics] PRIMARY_STATE follows FINAL_ONTO_STATE; process "
            "dominance remains in ASM_STYLE/DOMINANCE_CL."
        # Batch-write computed history metrics via QGIS provider rather than a full table rewrite.
        )
        feedback.pushInfo(
            f"[Assemblage metrics] Carried state assignments={total_carried_steps:,}; "
            f"storage-to-floodplain persistence promotions={total_promoted_steps:,}; "
            f"cells with unresolved final raw evidence but resolved final state="
            f"{final_raw_unresolved_but_resolved:,}."
        )
        feedback.pushInfo(
            f"[Assemblage metrics] Storage stabilisation matches Module 3B: "
            f"threshold={PERSISTENCE_YEARS:g} years; mode={STABILISATION_MODE}; "
            f"stable-evidence classes={sorted(stable_evidence_set)}. Episode count is not a stabilisation gate."
        )
        feedback.pushInfo(
            "[Assemblage metrics] SURFACE_AGE_EST remains time since the last "
            "erosion/deposition disturbance; AGE_CENSORED=1 marks inherited T0 surfaces "
            "for which that value is a minimum observed persistence rather than true formation age."
        )
        return layer


    # Hard QA: a missing-support timestep cannot erase an established state.
    # The final ONTO_STATE_i must equal FINAL_ONTO_STATE.
    # Hard QA validates the rule used to carry states through missing-support gaps.
    def _validate_state_continuity(self, layer, context, feedback):
        """Hard QA for the v10.9 support/state separation.

        A ``reworked_unresolved`` timestep is a support gap, not a positive
        state observation. Once a state has been established, such a gap must
        not revert ONTO_STATE_i to UNRESOLVED. Genuine unrecognised source
        classes may still break certainty.
        """
        lyr = self._resolve_vector_layer(layer, context, "asm_state_continuity_qa")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(
                "[State continuity QA] Could not resolve metric layer."
            )

        ea_fields = sorted(
            [n for n in lyr.fields().names() if re.match(r"^EA_Class_\d+$", n)],
            key=lambda n: int(n.rsplit("_", 1)[1]),
        )
        state_fields = sorted(
            [n for n in lyr.fields().names() if re.match(r"^ONTO_STATE_\d+$", n)],
            key=lambda n: int(n.rsplit("_", 1)[1]),
        )
        if not ea_fields or len(ea_fields) != len(state_fields):
            raise QgsProcessingException(
                "[State continuity QA] EA_Class_i / ONTO_STATE_i field counts differ."
            )

        required = ea_fields + state_fields + [
            "FINAL_ONTO_RAW",
            "FINAL_ONTO_STATE",
            "N_STATE_CARRY",
            "FINAL_CARRIED",
        ]
        if "INIT_STATE" in lyr.fields().names():
            required.append("INIT_STATE")
        missing = [n for n in required if n not in lyr.fields().names()]
        if missing:
            raise QgsProcessingException(
                "[State continuity QA] Missing fields: " + ", ".join(missing)
            )

        req = QgsFeatureRequest()
        req.setSubsetOfAttributes(required, lyr.fields())
        req.setFlags(QgsFeatureRequest.NoGeometry)

        bad = 0
        final_resolved_from_gap = 0
        carried_cells = 0
        examples = []

        # Normalise field values for the carry-forward QA comparison.
        def clean(value):
            if value is None:
                return ""
            try:
                if hasattr(value, "isNull") and value.isNull():
                    return ""
            except Exception:
                pass
            return str(value).strip().lower().replace(" ", "_").replace("-", "_")

        for ft in lyr.getFeatures(req):
            prior_state = (
                str(ft["INIT_STATE"] or "UNRESOLVED").strip().upper()
                if "INIT_STATE" in required else "UNRESOLVED"
            )
            if prior_state not in {"ACTIVE_DOMAIN", "DEPOSITIONAL_STORAGE", "STABILISED_FLOODPLAIN"}:
                prior_state = "UNRESOLVED"
            local_bad = []

            for i, (ea_name, state_name) in enumerate(
                zip(ea_fields, state_fields), start=1
            ):
                ea_value = clean(ft[ea_name])
                state_value = str(ft[state_name] or "UNRESOLVED").strip().upper()

                # A genuine unknown class can interrupt certainty; an explicit support gap cannot.
                if (
                    ea_value in {
                        "reworked_unresolved",
                        "unsupported_non_event",
                        "state_carry_gap",
                    }
                    and prior_state != "UNRESOLVED"
                    and state_value == "UNRESOLVED"
                ):
                    local_bad.append(
                        f"step {i}: support gap erased prior {prior_state}"
                    )

                # A genuine unresolved source class can break certainty. A support
                # gap cannot; otherwise use the reconstructed state as the prior.
                if ea_value in {
                    "reworked_unresolved",
                    "unsupported_non_event",
                    "state_carry_gap",
                }:
                    if state_value != "UNRESOLVED":
                        prior_state = state_value
                elif state_value == "UNRESOLVED":
                    prior_state = "UNRESOLVED"
                else:
                    prior_state = state_value

            final_state = str(
                ft["FINAL_ONTO_STATE"] or "UNRESOLVED"
            ).strip().upper()
            last_state = str(
                ft[state_fields[-1]] or "UNRESOLVED"
            ).strip().upper()
            if final_state != last_state:
                local_bad.append(
                    f"FINAL_ONTO_STATE={final_state} but {state_fields[-1]}={last_state}"
                )

            if int(ft["N_STATE_CARRY"] or 0) > 0:
                carried_cells += 1
            if (
                str(ft["FINAL_ONTO_RAW"] or "UNRESOLVED").strip().upper()
                == "UNRESOLVED"
                and final_state != "UNRESOLVED"
            ):
                final_resolved_from_gap += 1

            if local_bad:
                bad += 1
                if len(examples) < 8:
                    examples.append(
                        f"fid={ft.id()}: " + "; ".join(local_bad)
                    )

        feedback.pushInfo(
            f"[State continuity QA] cells with carried states={carried_cells:,}; "
            f"cells resolved at endpoint despite unresolved raw final evidence="
            f"{final_resolved_from_gap:,}; violations={bad:,}"
        )
        if bad:
            raise QgsProcessingException(
                f"[State continuity QA] {bad:,} cells violate the carry-forward "
                f"rule. Examples: {' | '.join(examples)}"
            )


    # Hard QA: reject forbidden direct AD -> SF transitions in reconstructed history.
    # A history should not contain AD -> SF without intervening DS.
    def _validate_module3b_transition_semantics(self, layer, context, feedback):
        """Hard QA for the shared three-state transition semantics.

        In particular, Active Domain -> Stabilised Floodplain is forbidden: an
        Active-Domain departure must pass through Depositional Storage.
        """
        lyr = self._resolve_vector_layer(layer, context, "asm_m3b_semantic_qa")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException("[Module 3B semantic QA] Could not resolve metric layer.")
        state_fields = sorted(
            [n for n in lyr.fields().names() if re.match(r"^ONTO_STATE_\d+$", n)],
            key=lambda n: int(n.rsplit("_", 1)[1]),
        )
        attrs = [n for n in ["INIT_STATE"] + state_fields if n in lyr.fields().names()]
        if not state_fields:
            raise QgsProcessingException("[Module 3B semantic QA] No ONTO_STATE_i fields found.")
        req = QgsFeatureRequest(); req.setSubsetOfAttributes(attrs, lyr.fields()); req.setFlags(QgsFeatureRequest.NoGeometry)
        forbidden = 0; examples = []
        for f in lyr.getFeatures(req):
            init = str(f["INIT_STATE"] or "UNRESOLVED").strip().upper() if "INIT_STATE" in attrs else "UNRESOLVED"
            seq = [init] + [str(f[n] or "UNRESOLVED").strip().upper() for n in state_fields]
            for a, b in zip(seq, seq[1:]):
                if a == "ACTIVE_DOMAIN" and b == "STABILISED_FLOODPLAIN":
                    forbidden += 1
                    if len(examples) < 5:
                        examples.append(f"fid={f.id()}")
                    break
        feedback.pushInfo(f"[Module 3B semantic QA] forbidden Active Domain -> Stabilised Floodplain transitions={forbidden:,}")
        if forbidden:
            raise QgsProcessingException(
                f"[Module 3B semantic QA] {forbidden:,} cells contain a forbidden Active Domain -> Stabilised Floodplain jump. "
                f"Examples: {', '.join(examples)}"
            )

    # Hard QA: independently validated background must remain SF throughout history.
    # Validated background should be stable at every step, with age >= observed span.
    def _validate_background_metrics(self, layer, context, feedback):
        """Fail fast if explicit background cells did not retain complete stable histories."""
        lyr=self._resolve_vector_layer(layer,context,"asm_background_metric_qa")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException("[Background QA] Could not resolve metric layer.")
        state_fields=sorted([n for n in lyr.fields().names() if re.match(r"^ONTO_STATE_\d+$",n)],key=lambda n:int(n.rsplit("_",1)[1]))
        required={"BG_FP","BELT_PROTECTED","BG_CONFLICT","FINAL_ONTO_RAW","FINAL_ONTO_STATE","FP_STAB","ASM_RICHNESS","RECORD_SPAN_YR","SURFACE_AGE_EST"}.union(state_fields)
        missing=sorted(required.difference(lyr.fields().names()))
        if missing: raise QgsProcessingException("[Background QA] Missing fields: "+", ".join(missing))
        req=QgsFeatureRequest(); req.setSubsetOfAttributes(sorted(required),lyr.fields()); req.setFlags(QgsFeatureRequest.NoGeometry)
        total=bad=belt_bg=0; examples=[]
        for f in lyr.getFeatures(req):
            bg=int(f["BG_FP"] or 0); belt=int(f["BELT_PROTECTED"] or 0)
            if bg and belt: belt_bg+=1
            if not bg: continue
            total+=1; failures=[]
            if any(str(f[n]).strip().upper()!="STABILISED_FLOODPLAIN" for n in state_fields): failures.append("ONTO_STATE_i")
            if str(f["FINAL_ONTO_RAW"]).strip().upper()!="STABILISED_FLOODPLAIN": failures.append("FINAL_ONTO_RAW")
            if str(f["FINAL_ONTO_STATE"]).strip().upper()!="STABILISED_FLOODPLAIN": failures.append("FINAL_ONTO_STATE")
            if int(f["FP_STAB"] or 0)!=1: failures.append("FP_STAB")
            if int(f["ASM_RICHNESS"] or 0)!=1: failures.append("ASM_RICHNESS")
            try:
                if abs(float(f["SURFACE_AGE_EST"])-float(f["RECORD_SPAN_YR"]))>1e-5: failures.append("SURFACE_AGE_EST")
            except Exception: failures.append("elapsed_years")
            if failures:
                bad+=1
                if len(examples)<5: examples.append(f"fid={f.id()}:{','.join(failures)}")
        feedback.pushInfo(f"[Background QA] explicit background={total:,}; invalid={bad:,}; background-in-belt={belt_bg:,}")
        if belt_bg: raise QgsProcessingException("[Background QA] Historical Active Domain belt received background assignment.")
        if bad: raise QgsProcessingException(f"[Background QA] {bad:,} background cells failed history QA. Examples: {'; '.join(examples)}")

    # Aggregate count/area by source support, T0 provenance and reconstructed state.
    # This is a diagnostic table, not a Cox risk/transition table.
    # QA reports area as well as counts, because small slivers should not dominate interpretation.
    def _build_assemblage_qa_table(self, layer, period_values, context, feedback):
        """Return a no-geometry QA table for support, background and timestep state areas."""
        lyr=self._resolve_vector_layer(layer,context,"asm_qa_source")
        fields=QgsFields()
        for name,typ,length in [
            ("QA_GROUP",QVariant.String,32),("TIMESTEP",QVariant.Int,0),("PERIOD",QVariant.String,16),
            ("CATEGORY",QVariant.String,64),("N_CELLS",QVariant.Int,0),("AREA_M2",QVariant.Double,0),
            ("AREA_KM2",QVariant.Double,0),("AREA_FRAC",QVariant.Double,0)]:
            fld=QgsField(name,typ); fld.setLength(length); fields.append(fld)
        table=QgsVectorLayer("None","Assemblage_QA_Summary","memory")
        prov=table.dataProvider(); prov.addAttributes(list(fields)); table.updateFields()
        total_area=0.0; support={}; bg={}; states={}; raw_to_final={}; carry_summary={}; initial_summary={}; provenance_summary={}
        state_fields=sorted([n for n in lyr.fields().names() if re.match(r"^ONTO_STATE_\d+$",n)],key=lambda n:int(n.rsplit("_",1)[1]))
        qa_extra=["FINAL_ONTO_RAW","FINAL_ONTO_STATE","FINAL_CARRIED","N_STATE_CARRY","N_STATE_PROMOTE"]
        attrs=[n for n in ["SUPPORT_CL","BG_FP","BG_CONFLICT","BELT_PROTECTED","INIT_STATE","INIT_PROV","INIT_CONTEXT","LEFT_CENS","SF_PROV","AGE_CENSORED"]+qa_extra+state_fields if n in lyr.fields().names()]
        req=QgsFeatureRequest(); req.setSubsetOfAttributes(attrs,lyr.fields())
        for f in lyr.getFeatures(req):
            g=f.geometry(); area=0.0 if g is None or g.isEmpty() else g.area(); total_area+=area
            sc=str(f["SUPPORT_CL"] or "<NULL>") if "SUPPORT_CL" in attrs else "unknown"
            support.setdefault(sc,[0,0.0]); support[sc][0]+=1; support[sc][1]+=area
            for name in ["BG_FP","BG_CONFLICT","BELT_PROTECTED"]:
                if name in attrs:
                    key=f"{name}={int(f[name] or 0)}"; bg.setdefault(key,[0,0.0]); bg[key][0]+=1; bg[key][1]+=area
            for name in ["INIT_STATE","INIT_PROV","INIT_CONTEXT","LEFT_CENS"]:
                if name in attrs:
                    key=f"{name}={f[name]}"; initial_summary.setdefault(key,[0,0.0]); initial_summary[key][0]+=1; initial_summary[key][1]+=area
            for name in ["SF_PROV","AGE_CENSORED"]:
                if name in attrs:
                    key=f"{name}={f[name]}"; provenance_summary.setdefault(key,[0,0.0]); provenance_summary[key][0]+=1; provenance_summary[key][1]+=area
            for i,n in enumerate(state_fields,1):
                st=str(f[n] or "UNRESOLVED").strip().upper(); key=(i,st); states.setdefault(key,[0,0.0]); states[key][0]+=1; states[key][1]+=area
            if "FINAL_ONTO_RAW" in attrs and "FINAL_ONTO_STATE" in attrs:
                raw=str(f["FINAL_ONTO_RAW"] or "UNRESOLVED").strip().upper()
                final=str(f["FINAL_ONTO_STATE"] or "UNRESOLVED").strip().upper()
                key=f"{raw} -> {final}"
                raw_to_final.setdefault(key,[0,0.0]); raw_to_final[key][0]+=1; raw_to_final[key][1]+=area
            if "FINAL_CARRIED" in attrs:
                key=f"FINAL_CARRIED={int(f['FINAL_CARRIED'] or 0)}"
                carry_summary.setdefault(key,[0,0.0]); carry_summary[key][0]+=1; carry_summary[key][1]+=area
            if "N_STATE_CARRY" in attrs:
                key="ANY_STATE_CARRY=1" if int(f["N_STATE_CARRY"] or 0)>0 else "ANY_STATE_CARRY=0"
                carry_summary.setdefault(key,[0,0.0]); carry_summary[key][0]+=1; carry_summary[key][1]+=area
            if "N_STATE_PROMOTE" in attrs:
                key="ANY_STORAGE_PROMOTION=1" if int(f["N_STATE_PROMOTE"] or 0)>0 else "ANY_STORAGE_PROMOTION=0"
                carry_summary.setdefault(key,[0,0.0]); carry_summary[key][0]+=1; carry_summary[key][1]+=area
        feats=[]
        # Construct an area- and cell-count QA row with whole-corridor area fraction.
        def add(group,step,period,category,count,area):
            ft=QgsFeature(table.fields()); ft.setAttributes([group,step,period,category,count,area,area/1e6,area/total_area if total_area>0 else None]); feats.append(ft)
        for k,(n,a) in sorted(support.items()): add("SUPPORT",None,None,k,n,a)
        for k,(n,a) in sorted(bg.items()): add("BACKGROUND",None,None,k,n,a)
        for k,(n,a) in sorted(initial_summary.items()): add("INITIAL_STATE",None,None,k,n,a)
        for k,(n,a) in sorted(provenance_summary.items()): add("PROVENANCE",None,None,k,n,a)
        for k,(n,a) in sorted(raw_to_final.items()): add("FINAL_RAW_TO_STATE",None,None,k,n,a)
        for k,(n,a) in sorted(carry_summary.items()): add("STATE_CONTINUITY",None,None,k,n,a)
        for (i,st),(n,a) in sorted(states.items()): add("TIMESTEP_STATE",i,period_values[i-1] if i<=len(period_values) else None,st,n,a)
        prov.addFeatures(feats); table.updateExtents()
        feedback.pushInfo(f"[Assemblage QA] Built {len(feats):,} support/background/state-continuity/timestep-state area rows.")
        return table

    # Log final assemblage class counts without expanding polygon geometry in memory.
    # Quick QA counts do not establish area balance; use Assemblage_QA_Summary for area.
    def _report_assemblage_summary(self, layer, context, feedback):
        """
        Report summary counts of final assemblage classes for quick QA.
        """
        lyr = self._resolve_vector_layer(layer, context, "asm_summary")
        if lyr is None or not lyr.isValid():
            feedback.reportError("[ASM SUMMARY] Invalid layer")
            return

        fld = "ASM_CLASS"
        if fld not in lyr.fields().names():
            feedback.reportError("[ASM SUMMARY] ASM_CLASS field not found")
            return

        counts = {}
        total = 0
        summary_request = QgsFeatureRequest()
        summary_request.setSubsetOfAttributes([fld], lyr.fields())
        summary_request.setFlags(QgsFeatureRequest.NoGeometry)
        for ft in lyr.getFeatures(summary_request):
            total += 1
            v = ft[fld]
            key = str(v).strip() if v is not None and str(v).strip() != "" else "<NULL>"
            counts[key] = counts.get(key, 0) + 1

        feedback.pushInfo(f"[ASM SUMMARY] Total features: {total}")
        for k in sorted(counts.keys()):
            feedback.pushInfo(f"[ASM SUMMARY] {k}: {counts[k]}")
    # ------------------------------------------------------------------
    # main processAlgorithm
    # ------------------------------------------------------------------

    # Cheap preflight catches late-stage QGIS API symbols before expensive fabrication.
    # Preflight saves wasted runtime from late failures after long fabric builds.
    def _preflight_runtime_symbols(self, feedback):
        """Exercise late-stage QA/output classes before long processing begins."""
        try:
            test_fields = QgsFields()
            test_fields.append(QgsField("_QA_TEST", QVariant.Int))
            test_feature = QgsFeature(test_fields)
            test_feature.setAttributes([1])
            if len(test_fields) != 1 or test_feature.attribute(0) != 1:
                raise RuntimeError("QGIS QA-table symbol test returned an unexpected result")
        except Exception as exc:
            raise QgsProcessingException(
                f"[PREFLIGHT] Required QGIS QA/output classes are unavailable: {exc}"
            )
        feedback.pushInfo("[PREFLIGHT] QA/output runtime-symbol check passed (QgsFields, QgsField, QgsFeature).")

    # QGIS Processing entry point and authoritative workflow orchestration.
    # The stages below keep evidence, inferred states and final outputs separate.
    # Original v10.9 geometry and state logic is preserved exactly below.
    def processAlgorithm(self, parameters, context, feedback):
        # Check dependent QGIS symbols before any time-consuming geometry work.
        self._preflight_runtime_symbols(feedback)
        layers = self.parameterAsLayerList(parameters, self.PARAM_LAYERS, context)
        corridor_input = self.parameterAsVectorLayer(parameters, self.PARAM_CORRIDOR, context)
        background_input = self.parameterAsVectorLayer(parameters, self.PARAM_BACKGROUND_MASK, context)
        historical_belt_input = self.parameterAsVectorLayer(parameters, self.PARAM_HISTORICAL_BELT, context)
        initial_state_input = self.parameterAsVectorLayer(parameters, self.PARAM_INITIAL_LAYER, context)
        initial_mode = int(self.parameterAsEnum(parameters, self.PARAM_INITIAL_MODE, context))
        initial_state_field = self.parameterAsString(parameters, self.PARAM_INITIAL_STATE_FIELD, context).strip()
        initial_context_field = self.parameterAsString(parameters, self.PARAM_INITIAL_CONTEXT_FIELD, context).strip()
        initial_active_values = self.parameterAsString(parameters, self.PARAM_INITIAL_ACTIVE_VALUES, context)
        initial_storage_values = self.parameterAsString(parameters, self.PARAM_INITIAL_STORAGE_VALUES, context)
        initial_stable_values = self.parameterAsString(parameters, self.PARAM_INITIAL_STABLE_VALUES, context)
        stabilisation_years = float(self.parameterAsDouble(parameters, self.PARAM_STABILISATION_YEARS, context))
        stabilisation_mode = int(self.parameterAsEnum(parameters, self.PARAM_STABILISATION_MODE, context))
        stable_evidence_classes = [
            x.strip() for x in self.parameterAsString(parameters, self.PARAM_STABLE_EVIDENCE_CLASSES, context).split(",")
            if x.strip()
        ]
        assume_corridor_background = self.parameterAsBoolean(parameters, self.PARAM_ASSUME_CORRIDOR_FP, context)
        if assume_corridor_background:
            feedback.pushWarning("[MAIN ANALYSIS] ASSUME_CORRIDOR_BACKGROUND_FP=True is an opt-in sensitivity setting. Use False with the explicit BACKGROUND_FLOODPLAIN mask for the principal analysis.")
        else:
            feedback.pushInfo("[MAIN ANALYSIS] ASSUME_CORRIDOR_BACKGROUND_FP=False; only the explicit background mask can assign corridor background.")
        if initial_mode == 1 and (initial_state_input is None or not initial_state_input.isValid()):
            raise QgsProcessingException("Explicit T0 classification is required by INITIAL_STATE_MODE but no valid layer was supplied.")
        feedback.pushInfo(
            f"[T0] initial-state mode={initial_mode}; explicit layer="
            f"{initial_state_input.name() if initial_state_input is not None and initial_state_input.isValid() else '<none>'}"
        )
        # Users should run conservative background assignment unless justified by evidence.
        feedback.pushInfo(
            f"[STABILISATION] Module-3B rule: years={stabilisation_years:g}; mode={stabilisation_mode}; "
            f"stable-evidence classes={stable_evidence_classes}"
        )
        min_valid_fraction = self.parameterAsDouble(parameters, self.PARAM_MIN_VALID_FRAC, context)
        class_field = self.parameterAsString(parameters, self.PARAM_CLASS_FIELD, context)
        period_field = self.parameterAsString(parameters, self.PARAM_PERIOD_FIELD, context)
        reserved_id_fields = {"fid", "ogc_fid", "rowid", "objectid", "object_id"}
        if str(period_field or "").strip().lower() in reserved_id_fields:
            raise QgsProcessingException(
                f"[DATE QA] '{period_field}' is a provider ID field, not a chronology field. "
                "Select PeriodEnd (recommended) or the intended period/date field."
            )
        min_valid_year = int(self.parameterAsInt(parameters, self.PARAM_MIN_VALID_YEAR, context))
        max_valid_year = int(self.parameterAsInt(parameters, self.PARAM_MAX_VALID_YEAR, context))
        max_interval_years = float(self.parameterAsDouble(parameters, self.PARAM_MAX_INTERVAL_YEARS, context))
        if max_valid_year < min_valid_year:
            raise QgsProcessingException(
                f"Maximum valid year ({max_valid_year}) is earlier than minimum valid year ({min_valid_year})."
            # Date field cannot be a provider ID: that produces nonsensical chronology.
            )
        feedback.pushInfo(
            f"[DATE QA] permitted years={min_valid_year}–{max_valid_year}; "
            f"maximum interval={max_interval_years:g} years"
        )
        do_dissolve = self.parameterAsBoolean(parameters, self.PARAM_DISSOLVE, context)
        min_fabric_area = self.parameterAsDouble(parameters, self.PARAM_MIN_FABRIC_AREA, context)

        refine_style = self.parameterAsBoolean(parameters, self.PARAM_REFINE_STYLE, context)
        max_quiet = self.parameterAsInt(parameters, self.PARAM_MAX_QUIET, context)
        save_stats_fabric = self.parameterAsBoolean(parameters, self.PARAM_SAVE_STATS_FABRIC, context)
        save_debug = self.parameterAsBoolean(parameters, self.PARAM_SAVE_DEBUG, context)
        debug_folder = self.parameterAsString(parameters, self.PARAM_DEBUG_FOLDER, context)

        raw_out = self.parameterAsOutputLayer(parameters, self.PARAM_OUTPUT, context)
        base_path = raw_out.split("|")[0]
        root, ext = os.path.splitext(base_path)
        if ext.lower() != ".gpkg":
            base_path = root + ".gpkg"
        os.makedirs(os.path.dirname(base_path) or ".", exist_ok=True)

        # The output destination is replaced intentionally; archive older runs first.
        # Main output
        self._safe_delete_gpkg(base_path)

        # Optional debug output.  Debug is intentionally OFF by default because
        # full 39/40-layer runs can take many hours and can generate many files.
        # When enabled, _save_debug_layer writes each diagnostic layer as a
        # standalone GPKG inside <debug_gpkg_path_without_ext>_debug_layers.
        base_name = os.path.splitext(os.path.basename(base_path))[0]
        debug_gpkg_path = None
        if save_debug:
            debug_dir = debug_folder or r"D:\QGIS_TEMP\debug_layers"
            os.makedirs(debug_dir, exist_ok=True)
            debug_gpkg_path = os.path.join(debug_dir, f"{base_name}_DEBUG.gpkg")
            self._safe_delete_gpkg(debug_gpkg_path)
            feedback.pushInfo(f"[DEBUG] Debug enabled. Root path: {debug_gpkg_path}")
            feedback.pushInfo(
                "[DEBUG] Individual diagnostic layers will be written to: "
                f"{os.path.splitext(debug_gpkg_path)[0]}_debug_layers"
            )
        else:
            feedback.pushInfo("[DEBUG] Debug layer saving disabled.")

        if not layers or len(layers) < 1:
            raise QgsProcessingException("Provide at least one polygon EA layer.")
        if len(layers) > 40:
            raise QgsProcessingException("This tool supports up to 40 layers.")
        if background_input is not None and corridor_input is None:
            raise QgsProcessingException("A Valid Background Floodplain Mask requires an Analysis Corridor.")
        if historical_belt_input is not None and corridor_input is None:
            raise QgsProcessingException("A Historical Active Domain belt requires an Analysis Corridor.")
        # Validate structural/mask input dependencies before generating a large fabric.
        if background_input is not None and historical_belt_input is None:
            feedback.pushWarning(
                "[Corridor] No Historical Active Domain belt supplied. The explicit background mask will still be used, "
                "but belt-protection QA cannot be guaranteed. Supply the corridor script's historical belt input for the main analysis."
            )
        if assume_corridor_background and corridor_input is None:
            feedback.reportError(
                "[Corridor] Residual-background assumption ignored because no Analysis Corridor was supplied."
            )
            assume_corridor_background = False

        for v in layers:
            if QgsWkbTypes.geometryType(v.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException(f"Layer {v.name()} is not a polygon layer.")
        if initial_state_input is not None and initial_state_input.isValid():
            if QgsWkbTypes.geometryType(initial_state_input.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException("T0 initial-state classification must be a polygon layer.")
            if initial_state_input.fields().indexFromName(initial_state_field) < 0:
                raise QgsProcessingException(
                    f"T0 state field '{initial_state_field}' was not found in '{initial_state_input.name()}'."
                )

        
        ref_crs_obj = None
        for v in layers:
            if v is not None and v.isValid() and v.crs().isValid():
                ref_crs_obj = v.crs()
                break

        if ref_crs_obj is None or not ref_crs_obj.isValid():
            raise QgsProcessingException("Could not determine reference CRS from input layers.")

        feedback.pushInfo(f"[CRS] Using reference CRS: {ref_crs_obj.authid()}")

        # Reproject, repair, optionally dissolve and freeze spatial-mask inputs.
        # All optional masks are brought into the same source CRS and made valid.
        def _prepare_analysis_mask(input_layer, label, dissolve=True):
            if input_layer is None:
                return None
            if QgsWkbTypes.geometryType(input_layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException(f"{label} must be a polygon layer.")
            src = input_layer
            if input_layer.crs().isValid() and input_layer.crs() != ref_crs_obj:
                feedback.pushInfo(
                    f"[Corridor] Reprojecting {label} from {input_layer.crs().authid()} "
                    f"to {ref_crs_obj.authid()}"
                )
                src = self._run_raw(
                    "native:reprojectlayer",
                    {
                        "INPUT": input_layer,
                        "TARGET_CRS": ref_crs_obj,
                        "CONVERT_CURVED_GEOMETRIES": False,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"prep_{label}_reproject",
                )["OUTPUT"]
            src = self._sanitize_polygon_layer(
                src, context, feedback, f"prep_{label}", min_area=0.0
            )
            if dissolve:
                src = self._run_raw(
                    "native:dissolve",
                    {
                        "INPUT": src,
                        "FIELD": [],
                        "SEPARATE_DISJOINT": False,
                        "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                    },
                    context, feedback, f"prep_{label}_dissolve",
                )["OUTPUT"]
                src = self._sanitize_polygon_layer(
                    src, context, feedback, f"prep_{label}_dissolved", min_area=0.0
                )
            return self._freeze_to_gpkg(
                src,
                context,
                feedback,
                tag=f"prep_{label}_frozen",
                layer_name=label,
                create_spatial_index=True,
            )

        # Dissolve corridor, background and belt; preserve T0 classification categories.
        analysis_corridor = _prepare_analysis_mask(corridor_input, "analysis_corridor")
        background_mask = _prepare_analysis_mask(background_input, "valid_background_mask")
        historical_active_belt = _prepare_analysis_mask(historical_belt_input, "historical_active_belt")
        initial_state_layer = _prepare_analysis_mask(initial_state_input, "initial_state_classification", dissolve=False)
        if historical_active_belt is not None:
            historical_active_belt = self._run_raw(
                "native:clip", {"INPUT": historical_active_belt, "OVERLAY": analysis_corridor,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}, context, feedback, "prep_belt_clip_corridor"
            )["OUTPUT"]
            historical_active_belt = self._sanitize_polygon_layer(
                historical_active_belt, context, feedback, "prep_belt_clipped", min_area=0.0
            )
            historical_active_belt = self._freeze_to_gpkg(
                historical_active_belt, context, feedback, tag="prep_belt_frozen",
                layer_name="historical_active_belt", create_spatial_index=True
            )
        # Background must be confined to the same corridor as the analysis fabric.
        if background_mask is not None:
            # Enforce the same outer population used by the fabric.
            background_mask = self._run_raw(
                "native:clip",
                {
                    "INPUT": background_mask,
                    "OVERLAY": analysis_corridor,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, "prep_background_clip_corridor",
            )["OUTPUT"]
            background_mask = self._sanitize_polygon_layer(
                background_mask, context, feedback, "prep_background_clipped", min_area=0.0
            )
            background_mask = self._freeze_to_gpkg(
                background_mask, context, feedback,
                tag="prep_background_clipped_frozen",
                layer_name="valid_background_mask",
                create_spatial_index=True,
            )
            if historical_active_belt is not None:
                # Historical active occupation protects against incorrect inherited-SF assignment.
                feedback.pushInfo("[Corridor] Subtracting historical Active Domain belt from explicit background mask.")
                background_mask = self._safe_polygon_difference(
                    background_mask, historical_active_belt, context, feedback, "background_minus_historical_belt"
                )
                background_mask = self._freeze_to_gpkg(
                    background_mask, context, feedback, tag="background_minus_belt_frozen",
                    layer_name="valid_background_mask_protected", create_spatial_index=True
                )

        # The classified T0 polygons add fine boundary context before fabric construction.
        if initial_state_layer is not None and analysis_corridor is not None:
            initial_state_layer = self._run_raw(
                "native:clip",
                {"INPUT": initial_state_layer, "OVERLAY": analysis_corridor, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                context, feedback, "prep_initial_state_clip_corridor",
            )["OUTPUT"]
            initial_state_layer = self._sanitize_polygon_layer(
                initial_state_layer, context, feedback, "prep_initial_state_clipped", min_area=0.0
            )
            initial_state_layer = self._freeze_to_gpkg(
                initial_state_layer, context, feedback, tag="prep_initial_state_frozen",
                layer_name="initial_state_classification", create_spatial_index=True,
            )

        if analysis_corridor is not None:
            feedback.pushInfo("[Corridor] Fixed Analysis Corridor will define the full assemblage fabric extent.")
            if background_mask is not None:
                feedback.pushInfo("[Corridor] The explicit Background Floodplain Mask is authoritative; historical Active Domain belt cells are protected and active/storage conflicts are not overwritten.")
            elif assume_corridor_background:
                feedback.reportError("[Corridor] No mask supplied: all zero-source corridor residual will be assumed stable floodplain.")
            else:
                feedback.pushInfo("[Corridor] Zero-source corridor residual will remain unresolved (safe default).")
        else:
            feedback.pushInfo("[Corridor] No Analysis Corridor supplied; legacy EA-footprint extent will be used.")

        # Source order in the QGIS dialog is irrelevant: dates determine chronology.
        # --------------------------------------------------------------
        # 1) Sort layers oldest -> newest by period field
        # --------------------------------------------------------------
        scored = []
        # Read canonical end-date from every EA input and reject contradictory source dates.
        for v in layers:
            pval = self._layer_period_value(
                v, period_field, feedback, min_valid_year, max_valid_year
            )
            scored.append((pval, v))

        # Duplicate dates are not valid separate timesteps. Reject them before
        # sorting so the user sees both implicated layer names.
        by_date = {}
        for pval, v in scored:
            by_date.setdefault(pval, []).append(v.name())
        duplicates = {pval: names for pval, names in by_date.items() if len(names) > 1}
        if duplicates:
            details = "; ".join(
                f"{self._period_int_to_text(pval)}: {', '.join(names)}"
                for pval, names in sorted(duplicates.items())
            )
            raise QgsProcessingException(
                f"[DATE QA] Duplicate EA timestep end dates detected: {details}"
            )

        scored.sort(key=lambda t: t[0])

        # Sort by validated time; reject duplicates, reversals and implausibly long gaps.
        chronology = []
        for pval, v in scored:
            txt = self._period_int_to_text(pval)
            dt = self._period_text_to_date(txt)
            chronology.append((dt, v))

        for (prev_dt, prev_v), (next_dt, next_v) in zip(chronology, chronology[1:]):
            if next_dt <= prev_dt:
                raise QgsProcessingException(
                    f"[DATE QA] Chronology is not strictly increasing: "
                    f"{prev_v.name()}[{prev_dt}] then {next_v.name()}[{next_dt}]."
                )
            gap_years = (next_dt - prev_dt).days / 365.2425
            if gap_years > max_interval_years:
                raise QgsProcessingException(
                    f"[DATE QA] Interval from {prev_v.name()}[{prev_dt}] to "
                    f"{next_v.name()}[{next_dt}] is {gap_years:.2f} years, exceeding "
                    f"the permitted maximum of {max_interval_years:g} years."
                )

        feedback.pushInfo(
            "Order (oldest→newest): " +
            " < ".join(
                f"{v.name()}[{self._period_int_to_text(p)}]" for p, v in scored
            )
        )
        feedback.pushInfo(
            "[DATE QA] Validated EA chronology: " +
            " < ".join(dt.strftime("%Y-%m-%d") for dt, _ in chronology)
        )

        # Period_i comes from the validated sequence, not unchecked feature attributes.
        # Build Period_i exclusively from the chronology that passed QA.
        layer_period_txt = {
            lyr.id(): self._period_int_to_text(pval)
            for pval, lyr in scored
        }

        # --------------------------------------------------------------
        # 2) Prepare source layers with EA_Class_i / Period_i
        # --------------------------------------------------------------
        prepped = []
        for i, (pval, v) in enumerate(scored, start=1):
            # Every source must be cleaned before extracting class and period fields.
            feedback.pushInfo(f"[Prep] {v.name()} — sanitize geometries")
            #Block removeed for debugs
            '''san = self._sanitize_polygon_layer(
                v, context, feedback, f"prep_{i}", min_area=0.0
            )'''
            #Block for debug
            san = self._run_raw(
                "native:fixgeometries",
                {
                    "INPUT": v,
                    "METHOD": 1,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"prep_{i}_fix",
            )["OUTPUT"]

            san = self._run_raw(
                "native:extractbyexpression",
                {
                    "INPUT": san,
                    "EXPRESSION": (
                        "geometry_type($geometry) IN ('Polygon','MultiPolygon') "
                        "AND $geometry IS NOT NULL "
                        "AND NOT is_empty($geometry)"
                    ),
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context, feedback, f"prep_{i}_keep",
            )["OUTPUT"]
            #End debug block
            class_new = f"EA_Class_{i}"
            # Use canonical descriptive field names: EA_Class_i and Period_i.
            period_new = f"Period_{i}"

            src_layer = self._resolve_vector_layer(san, context, f"prep_{i}_resolved")
            src_field_names = [f.name() for f in src_layer.fields()]

            selected_idx = src_layer.fields().indexFromName(class_field)
            if selected_idx < 0:
                raise QgsProcessingException(
                    f"[Prep] User-selected EA class field '{class_field}' is absent from {v.name()}. "
                    f"Available fields: {', '.join(src_field_names)}"
                )
            selected_field = src_layer.fields()[selected_idx]
            selected_name = selected_field.name()
            selected_key = selected_name.strip().casefold()

            provider_id_names = {
                "fid", "ogc_fid", "objectid", "object_id", "rowid",
                "_fab_id", "fab_id", "asm_id", "place_id", "block_id",
                "unit_id", "feature_id",
            }
            if selected_key in provider_id_names:
                raise QgsProcessingException(
                    f"[CLASS QA] '{selected_name}' in {v.name()} is an ID field, not "
                    "an EA class field. Select the textual field containing values such "
                    "as erosion, deposition, stable_channel, stable_island, or "
                    "stable_floodplain."
                )

            numeric_types = {
                QVariant.Int, QVariant.UInt, QVariant.LongLong,
                QVariant.ULongLong, QVariant.Double,
            }
            try:
                selected_is_numeric = selected_field.isNumeric()
            except Exception:
                selected_is_numeric = selected_field.type() in numeric_types
            if selected_is_numeric:
                raise QgsProcessingException(
                    f"[CLASS QA] '{selected_name}' in {v.name()} is numeric. Module 4a "
                    "does not contain a numeric-code lookup and requires textual EA "
                    "class labels. Select the actual class-name field before running."
                )

            # Prevent accidentally selecting FID or numeric code instead of EA class labels.
            # Catch IDs/codes stored as text. Sample nonblank values before the
            # expensive planar-fabric build and reject fields dominated by numbers.
            sample_nonblank = 0
            sample_numeric_like = 0
            sample_examples = []
            sample_request = QgsFeatureRequest()
            sample_request.setSubsetOfAttributes([selected_name], src_layer.fields())
            sample_request.setFlags(QgsFeatureRequest.NoGeometry)
            for sample_feature in src_layer.getFeatures(sample_request):
                raw_sample = sample_feature[selected_name]
                if raw_sample is None:
                    continue
                sample_text = str(raw_sample).strip()
                if not sample_text:
                    continue
                sample_nonblank += 1
                if len(sample_examples) < 8 and sample_text not in sample_examples:
                    sample_examples.append(sample_text)
                if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", sample_text):
                    sample_numeric_like += 1
                if sample_nonblank >= 5000:
                    break

            if sample_nonblank == 0:
                raise QgsProcessingException(
                    f"[CLASS QA] '{selected_name}' in {v.name()} contains no nonblank "
                    "class values in the validation sample."
                )

            numeric_like_fraction = sample_numeric_like / float(sample_nonblank)
            if numeric_like_fraction >= 0.90:
                raise QgsProcessingException(
                    f"[CLASS QA] '{selected_name}' in {v.name()} is text-typed but "
                    f"{numeric_like_fraction:.1%} of sampled nonblank values are numeric-like. "
                    "This appears to be an ID/code field, and Module 4a has no lookup "
                    "mapping for numeric codes. Sample values: "
                    + ", ".join(sample_examples)
                )

            escaped_name = selected_name.replace('"', '""')
            expr_class = f'nullif("{escaped_name}", \'\')'
            feedback.pushInfo(
                f"[Prep] {v.name()}: validated textual class field {selected_name} "
                f"({sample_nonblank:,} sampled nonblank; "
                f"{numeric_like_fraction:.1%} numeric-like) -> {class_new}"
            )

            period_text = layer_period_txt[v.id()]
            expr_period = f"'{period_text}'"

            # Refactor each source to only needed fields before expensive geometry processing.
            ref = self._run(
                "native:refactorfields",
                {
                    "INPUT": san,
                    "FIELDS_MAPPING": [
                        {
                            "expression": expr_class,
                            "length": 254,
                            "name": class_new,
                            "precision": 0,
                            "type": 10,
                        },
                        {
                            "expression": expr_period,
                            "length": 254,
                            "name": period_new,
                            "precision": 0,
                            "type": 10,
                        },
                    ],
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"refactor_{i}",
            )["OUTPUT"]

            ref = self._sanitize_polygon_layer(
                ref, context, feedback, f"prep_ref_{i}", min_area=0.0
            )

            # GPKG freeze protects column length/type fidelity across dozens of EA dates.
            # keep prepped layers file-backed; gpkg is safer for downstream field fidelity
            ref = self._freeze_to_gpkg(
                ref,
                context,
                feedback,
                tag=f"prepped_{i}",
                layer_name=f"prepped_{i}",
                create_spatial_index=True,
            )
            if debug_gpkg_path:
                self._save_debug_layer(
                    ref,
                    debug_gpkg_path,
                    f"DBG_prepped_{i}",
                    context,
                    feedback,
                    tag=f"dbg_prepped_{i}",
                )
            prepped.append(ref)
            
        # --------------------------------------------------------------
        # 2b) No channel-based interpretation in Module 4a
        # --------------------------------------------------------------
        feedback.pushInfo(
            "[Assemblage] Skipping channel lookup: Module 4a now treats Module 3 EA layers as authoritative."
        )
        # History assembly is source-EA based; it does not rerun centreline/channel models.
        # --------------------------------------------------------------
        # 3) Build planar fabric
        # --------------------------------------------------------------
        # The planar partition uses one combined boundary network, not iterative overlays.
        feedback.pushInfo("[Assemblage] Building planar fabric from all prepared EA boundaries.")
        union_path = self._build_planar_fabric_from_boundaries(
            prepped,
            context,
            feedback,
            tag="asm_union_fast",
            min_area=min_fabric_area,
            debug_gpkg_path=debug_gpkg_path,
            analysis_corridor=analysis_corridor,
            extra_boundary_layers=[x for x in (background_mask, historical_active_belt, initial_state_layer) if x is not None] or None,
        )

        # --------------------------------------------------------------
        # 4) Reassign timestep EA fields onto fabric
        # --------------------------------------------------------------
        # Attribute the permanent fabric from source evidence at each ordered timestep.
        feedback.pushInfo("[Assemblage] Reassigning EA fields from source layers onto final fabric.")
        union_path = self._reassign_ea_fields_from_sources(
            union_path,
            prepped,
            context,
            feedback,
            debug_gpkg_path=debug_gpkg_path,
            min_fabric_area=min_fabric_area,
        )

        # Do not discard corridor residual merely because it lacks a source EA class.
        # --------------------------------------------------------------
        # 5) Drop unsupported fabric cells before metrics
        # --------------------------------------------------------------
        #feedback.pushInfo("[Assemblage] Dropping fabric cells with no timestep assignment.")
        #union_path = self._drop_unassigned_fabric_cells(
        #    union_path, context, feedback, tag="asm_drop_unassigned"
        #)

                # --------------------------------------------------------------
        # 6) Build assemblage metrics
        # --------------------------------------------------------------
        feedback.pushInfo("[Assemblage] Building disturbance counts and assemblage classes.")

        assembled = self._resolve_vector_layer(union_path, context, "asm_union_final_rl")
        if assembled is None or not assembled.isValid():
            raise QgsProcessingException(
                "Assemblage union layer is invalid before metrics build."
            )

        # Support validation must precede any fill, otherwise inferred SF inflates coverage.
        # Discover EA step fields dynamically so this scales to long records.
        # Source-support diagnostics are calculated before any inferred background
        # or unresolved values are filled.
        ea_fields = self._discover_ea_step_fields(assembled, context, feedback)
        union_path = self._add_assignment_support_fields(
            union_path,
            context,
            feedback,
            min_valid_fraction=min_valid_fraction,
            tag="asm_source_support",
        )
        ordered_period_values = [layer_period_txt[v.id()] for _, v in scored]
        # Background assignment is explicit and includes overlap/conflict diagnostics.
        union_path = self._apply_corridor_background_policy(
            union_path,
            ordered_period_values,
            context,
            feedback,
            analysis_corridor_enabled=analysis_corridor is not None,
            background_mask=background_mask,
            historical_active_belt=historical_active_belt,
            assume_corridor_background=assume_corridor_background,
            tag="asm_corridor_policy",
        )

        # Apply prior-state metadata independently of later EA evidence.
        union_path = self._apply_initial_state_policy(
            union_path, context, feedback,
            initial_mode=initial_mode,
            initial_layer=initial_state_layer,
            initial_state_field=initial_state_field,
            initial_context_field=initial_context_field,
            active_values=initial_active_values,
            storage_values=initial_storage_values,
            stable_values=initial_stable_values,
            tag="asm_initial_state",
        )
        assembled = self._resolve_vector_layer(union_path, context, "asm_union_corridor_filled")

        if not ea_fields:
            raise QgsProcessingException(
                "No EA step fields found before assemblage metrics build."
            )

        feedback.pushInfo(
            f"[Assemblage] Found {len(ea_fields)} EA timestep fields"
        )

        # Only now compute state histories, elapsed ages, diversity and disturbance metrics.
        assembled = self._build_assemblage_metrics_from_ea_fields(
            assembled,
            ea_fields,
            ordered_period_values,
            context,
            feedback,
            stabilisation_years=stabilisation_years,
            stabilisation_mode=stabilisation_mode,
            stable_evidence_classes=stable_evidence_classes,
        )

        # All three hard-QA procedures must pass before release of analytical geometry.
        self._validate_state_continuity(assembled, context, feedback)
        self._validate_module3b_transition_semantics(assembled, context, feedback)
        self._validate_background_metrics(assembled, context, feedback)
        self._report_assemblage_summary(assembled, context, feedback)

        assembled = self._sanitize_polygon_layer(
            assembled,
            context,
            feedback,
            "asm_metrics_final",
            min_area=0.0,
        )

        assembled_units = self._freeze_to_gpkg(
            assembled,
            context,
            feedback,
            tag="assembled_units_clean",
            layer_name="assembled_units_clean",
            create_spatial_index=True,
        )

        assembled_units_lyr = self._resolve_vector_layer(
            assembled_units, context, "assembled_units_chk"
        )
        if assembled_units_lyr is None or not assembled_units_lyr.isValid():
            raise QgsProcessingException(
                "Final Assemblage_Units layer is invalid before save."
            )

        if assembled_units_lyr.featureCount() == 0:
            raise QgsProcessingException(
                "Final Assemblage_Units has 0 features before save."
            )

        # Write expensive core attributes first as recovery protection on long runs.
        # Write the completed analytical fabric before building secondary QA/display
        # products. This preserves the expensive core result if a later optional
        # output step fails.
        feedback.pushInfo(
            "[Output] Early core write: saving Assemblage_Units_FULL_ATTRS before QA/display products"
        )
        full_units_path = self._write_output_gpkg_layer(
            assembled_units,
            base_path,
            "Assemblage_Units_FULL_ATTRS",
            context,
            feedback,
            overwrite_file=True,
        )
        expected_output_layers = ["Assemblage_Units_FULL_ATTRS"]

        # QA summary output records area by support/provenance/state and supports audit.
        qa_summary_table = self._build_assemblage_qa_table(
            assembled_units_lyr, ordered_period_values, context, feedback
        )
        self._write_output_gpkg_layer(
            qa_summary_table, base_path, "Assemblage_QA_Summary",
            context, feedback, overwrite_file=False,
        )
        expected_output_layers.append("Assemblage_QA_Summary")

        if debug_gpkg_path:
            self._save_debug_layer(
                assembled_units,
                debug_gpkg_path,
                "DBG_final_assembled_units_pre_save",
                context,
                feedback,
                tag="dbg_final_assembled_units",
            )

        # --------------------------------------------------------------
        # 7) Write outputs
        # --------------------------------------------------------------
        # IMPORTANT FOR 35-39 LAYER RUNS
        # -----------------------------
        # The full assemblage table can be very wide:
        #   ~180k polygons x (2 fields per timestep + many metrics)
        # QGIS may appear to hang when it auto-loads/renders this full layer.
        #
        # Therefore the production output is split:
        #   1) Assemblage_Units_FULL_ATTRS : complete 39-layer analytical table
        #   2) Assemblage_Display          : lightweight display / QA layer
        #
        # The returned Processing output is the lightweight display layer, so QGIS
        # loads that by default. The full table remains in the same GeoPackage and
        # can be opened manually when needed.
        feedback.pushInfo(
            "[Output] Core analytical layer and Assemblage_QA_Summary already written; building display and optional products"
        )

        # Display output is narrow to keep the QGIS project responsive on large runs.
        # Build lightweight display/QA layer with a small, stable field set.
        feedback.pushInfo("[Output] Building lightweight Assemblage_Display layer")

        # Reduce the full analytical table to the lightweight display schema
        # BEFORE adding ASM_ID. Long history fields such as ONTO_TRANS_SUM are not
        # required for display; adding the ID first forces QGIS to rewrite those
        # fields using any stale narrow provider width and can fail on long records.
        display_source_lyr = self._resolve_vector_layer(
            assembled_units, context, "asm_display_source"
        )
        display_names = set(display_source_lyr.fields().names())

        preferred_display_fields = [
            "N_STEPS",
            "IN_CORRIDOR",
            "SUPPORT_CL",
            "BG_FP",
            "BG_SOURCE",
            "INIT_STATE",
            "INIT_PROV",
            "INIT_CONTEXT",
            "INIT_CONF",
            "INIT_SOURCE",
            "LEFT_CENS",
            "INIT_SF_PROV",
            "INIT_STORAGE",
            "ZERO_SOURCE",
            "N_ASSIGNED",
            "P_ASSIGNED",
            "VALID_FRAC",
            "FULL_SUPP",
            "SUPP_EARLY",
            "SUPP_MID",
            "SUPP_LATE",
            "EA_EVER",
            "VALID_OBS",
            "N_INACTIVE",
            "N_RAW_UNRES",
            "N_STATE_CARRY",
            "N_STATE_PROMOTE",
            "LAST_RES_STEP",
            "LAST_RES_STATE",
            "FINAL_CARRIED",
            "N_ACTIVE_DOM",
            "ACTIVE_DOM_FREQ",
            "N_STAB_FP",
            "STAB_FP_FREQ",
            "N_STORAGE",
            "STORAGE_FREQ",
            "N_ASM_REACTIVATE_TRANS",
            "N_ASM_STORAGE_TRANS",
            "N_ASM_STABILISE_TRANS",
            "N_ASM_STORAGE_REWORK_TRANS",
            "N_ASM_FP_STORAGE_TRANS",
            "N_ASM_ANY_TRANS",
            "FINAL_ONTO_RAW",
            "FINAL_ONTO_STATE",
            "ONTO_STATE",
            "FP_CONDITION",
            "FP_STAB",
            "FP_RECENT",
            "FP_REWORKED",
            "SURFACE_AGE_EST",
            "AGE_CENSORED",
            "MIN_PERSIST_YR",
            "SURFACE_AGE_TYPE",
            "STORAGE_AGE_CENS",
            "SF_PROV",
            "STATE_DETAIL",
            "ASM_STAB_YEARS",
            "ASM_STAB_MODE",
            "SINCE_DISTURB_YR",
            "SINCE_ACTIVE_YR",
            "SINCE_STORAGE_YR",
            "RECORD_SPAN_YR",
            "ASM_SHANNON",
            "ASM_H_NORM",
            "ASM_RICHNESS",
            "ASM_H_CLASS",
            "DIST_COUNT",
            "DIST_FREQ",
            "N_EVENTS",
            "N_EROSION",
            "N_DEPOSITION",
            "N_EPISODES",
            "ZERO_EPISODE",
            "MAX_QUIET",
            "DOM_RATIO",
            "NET_BAL",
            "ASM_CLASS",
            "ASM_LABEL",
            "ASM_FREQ",
            "ASM_STYLE",
            "ACTIVITY_CL",
            "DOMINANCE_CL",
            "STRUCTURE_CL",
            "DOMAIN_CLASS",
            "DOMAIN_STATE",
            "PRIMARY_STATE",
            "DEPO_INTERP",
            "ASM_ONTOLOGY",
            "FIRST_ACTIVE",
            "LAST_ACTIVE",
            "SINCE_ACTIVE",
            "FIRST_STORAGE",
            "LAST_STORAGE",
            "LAST_STORAGE_STATE",
            "FIRST_STORAGE_ENTRY",
            "LAST_STORAGE_ENTRY",
            "STORAGE_AGE_YR",
            "STORAGE_AGE_STEP",
            "SINCE_STORAGE_STATE_YR",
            "SINCE_STORAGE_STATE_STEP",
            "SINCE_STORAGE",
        ]

        display_mapping = []
        for nm in preferred_display_fields:
            if nm not in display_names:
                continue
            fld = display_source_lyr.fields().field(
                display_source_lyr.fields().indexFromName(nm)
            )
            display_mapping.append(
                {
                    "expression": f'"{nm}"',
                    "length": fld.length() if hasattr(fld, "length") else 254,
                    "name": nm,
                    "precision": fld.precision() if hasattr(fld, "precision") else 0,
                    "type": fld.type(),
                }
            )

        if not display_mapping:
            raise QgsProcessingException(
                "[Output] Could not build lightweight display mapping; no expected fields found."
            )

        display_narrow = self._run_raw(
            "native:refactorfields",
            {
                "INPUT": assembled_units,
                "FIELDS_MAPPING": display_mapping,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            "asm_display_refactor_first",
        )["OUTPUT"]

        display_layer = self._run_raw(
            "native:addautoincrementalfield",
            {
                "INPUT": display_narrow,
                "FIELD_NAME": "ASM_ID",
                "START": 1,
                "GROUP_FIELDS": [],
                "SORT_EXPRESSION": "",
                "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            "asm_display_add_id_after_refactor",
        )["OUTPUT"]

        display_layer = self._sanitize_polygon_layer(
            display_layer,
            context,
            feedback,
            "asm_display_clean",
            min_area=0.0,
        )

        final_path = self._write_output_gpkg_layer(
            display_layer,
            base_path,
            "Assemblage_Display",
            context,
            feedback,
            overwrite_file=False,
        )
        expected_output_layers.append("Assemblage_Display")

        feedback.pushInfo("[Output] Default loaded output is Assemblage_Display. Full table is Assemblage_Units_FULL_ATTRS.")

        # Dissolved and StatsFabric layers use the complete analytical fabric, not display.
        # Keep assembled_units as the full analytical layer for optional dissolved/stat outputs below.
        if do_dissolve:
            feedback.pushInfo("[Assemblage] Dissolving cartographic layer by ASM_CLASS")

            dissolved = self._run(
                "native:dissolve",
                {
                    "INPUT": assembled_units,
                    "FIELD": ["ASM_CLASS"],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                "asm_dissolve",
            )["OUTPUT"]

            dissolved = self._sanitize_polygon_layer(
                dissolved,
                context,
                feedback,
                "asm_dissolved",
                min_area=0.0,
            )

            dissolved = self._freeze_to_gpkg(
                dissolved,
                context,
                feedback,
                tag="asm_dissolved_clean",
                layer_name="asm_dissolved_clean",
                create_spatial_index=True,
            )

            self._write_output_gpkg_layer(
                dissolved,
                base_path,
                "Assemblage_Dissolved",
                context,
                feedback,
                overwrite_file=False,
            )
            expected_output_layers.append("Assemblage_Dissolved")

        if save_stats_fabric:
            feedback.pushInfo("[Assemblage] Building stats-friendly dissolved layer")

            stats_diss = self._run(
                "native:dissolve",
                {
                    "INPUT": assembled_units,
                    "FIELD": [
                        "ASM_CLASS",
                        "ASM_LABEL",
                        "ASM_FREQ",
                        "ASM_STYLE",
                        "ACTIVITY_CL",
                        "DOMINANCE_CL",
                        "STRUCTURE_CL",
                        "PRIMARY_STATE",
                        "IN_CORRIDOR",
                        "SUPPORT_CL",
                        "BG_FP",
                        "BG_SOURCE",
                        "ZERO_SOURCE",
                        "VALID_OBS",
                        "N_STEPS",
                        "N_EVENTS",
                        "N_RAW_UNRES",
                        "N_STATE_CARRY",
                        "N_STATE_PROMOTE",
                        "FINAL_CARRIED",
                        "N_EROSION",
                        "N_DEPOSITION",
                        "N_STORAGE",
                        "STORAGE_FREQ",
                        "FIRST_STORAGE",
                        "LAST_STORAGE",
                        "LAST_STORAGE_STATE",
                        "FIRST_STORAGE_ENTRY",
                        "LAST_STORAGE_ENTRY",
                        "STORAGE_AGE_YR",
                        "STORAGE_AGE_STEP",
                        "SINCE_STORAGE_STATE_YR",
                        "SINCE_STORAGE_STATE_STEP",
                        "SINCE_STORAGE",
                        "SINCE_STORAGE_YR",
                        "SINCE_STORAGE_STEP",
                        "N_ASM_REACTIVATE_TRANS",
                        "N_ASM_STORAGE_TRANS",
                        "N_ASM_STABILISE_TRANS",
                        "N_ASM_STORAGE_REWORK_TRANS",
                        "N_ASM_FP_STORAGE_TRANS",
                        "FINAL_ONTO_RAW",
                        "FINAL_ONTO_STATE",
                        "FP_CONDITION",
                        "FP_STAB",
                        "FP_RECENT",
                        "FP_REWORKED",
                        "SURFACE_AGE_EST",
                        "AGE_CENSORED",
                        "SF_PROV",
                        "STATE_DETAIL",
                        "ASM_SHANNON",
                        "ASM_H_NORM",
                        "ASM_RICHNESS",
                        "ASM_H_CLASS",
                        "N_ISL_ERO",
                        "N_ISL_DEP",
                        "N_EPISODES",
                        "ZERO_EPISODE",
                        "MAX_QUIET",
                        "QUIET_RATIO",
                        "DIST_COUNT",
                        "DIST_FREQ",
                        "DOM_RATIO",
                        "NET_BAL",
                        "FIRST_ACTIVE",
                        "LAST_ACTIVE",
                        "SINCE_ACTIVE",
                    ],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                "asm_stats_dissolve",
            )["OUTPUT"]

            stats_diss = self._sanitize_polygon_layer(
                stats_diss,
                context,
                feedback,
                "asm_stats_dissolved",
                min_area=0.0,
            )

            stats_diss = self._freeze_to_gpkg(
                stats_diss,
                context,
                feedback,
                tag="asm_stats_dissolved_clean",
                layer_name="asm_stats_dissolved_clean",
                create_spatial_index=True,
            )

            self._write_output_gpkg_layer(
                stats_diss,
                base_path,
                "Assemblage_StatsFabric",
                context,
                feedback,
                overwrite_file=False,
            )
            expected_output_layers.append("Assemblage_StatsFabric")

        self._verify_output_gpkg_layers(
            base_path, expected_output_layers, feedback
        )

        feedback.pushInfo(
            f"[Output] Final multi-layer GeoPackage: {base_path}"
        )
        feedback.pushInfo(
            "[Output] Default returned layer: Assemblage_Display"
        )

        if debug_gpkg_path:
            feedback.pushInfo(
                "[DEBUG] Inspect debug layers in: "
                f"{os.path.splitext(debug_gpkg_path)[0]}_debug_layers"
            )
        return {self.PARAM_OUTPUT: final_path}