# -*- coding: utf-8 -*-
# PAPER 2 ARCHIVE | PUBLICATION-SUPPORT SOURCE (PUB)
# Archive filename: FRAF_P2_PUB_AssemblageMetrics_v3_5.py
# Original source: FRAF_Module4d_Assemblage_Metrics_v3_5_M4A_v10_9_COMPATIBLE(1).py
# Original QGIS Processing ID and class are deliberately unchanged.
# Only Python comments have been inserted. No algorithm, parameter, field name,
# constant, source expression, data type, output filename, or runtime path is changed.
#
# ROLE AND DATA LINEAGE
#   Module 4a v10.9 Assemblage_Units_FULL_ATTRS (complete EA_Class_i / Period_i
#   and ONTO_STATE_i histories, INIT_STATE and FINAL_ONTO_STATE) is the input.
#   This post-processor reports unit, reach, class, neighbourhood and support
#   summaries; it does not reconstruct the planar fabric or fit Cox models.
#   Publication-support outputs should not be mistaken for the authoritative
#   longitudinal fixed-place risk table or subsequent transition forecasts.
#
# ANALYTICAL INTERPRETATION
#   State sequence: Active Domain (AD), Depositional Storage (DS), Stabilised
#   Floodplain (SF); unresolved evidence is not a fourth geomorphic state.
#   Process-event metrics come from EA_Class_i; state occupancy, transitions
#   and Shannon diversity come from ONTO_STATE_i. T0 INIT_STATE is used for
#   the first transition but not counted as an additional occupancy observation.
#   BG_FP indicates validated background support; N_ASSIGNED records direct EA
#   assignment, even where the background-fill obscures raw timestep classes.
#   Outside-EA-support intervals remain known non-events in disturbance rates.
#   Observation-weighted frequencies are not time-standardised hazard estimates.
#
# SURFACE AGE CAUTION
#   PERSIST_YRS_4D and SINCE_DISTURB_YR describe time since the last mapped
#   erosion/deposition disturbance or a bounded no-disturbance record. They
#   are NOT interchangeable with publication surface-continuity SURFACE_AGE
#   from the separate Surface Age State Mapper v3.4, which resets on active/
#   erosional occupation rather than every depositional reworking episode.
#   The episode threshold (default 3) describes an SF condition only; it does
#   NOT alter the upstream v10.9 DS->SF stabilisation determination.
#
# UNIT CONVENTIONS AND QUALIFICATIONS
#   Use a projected, preferably metre-based CRS. Radius and MIN_AREA are in
#   coordinate-system units, while area conversion uses CRS-to-metre factors.
#   Local activity is area-weighted over polygon representative points within
#   the specified radius (not polygon-edge distance or a hydraulic kernel).
#   AREA_TIME audit measures sum area once per observed timestep; it is not
#   area multiplied by elapsed years. Irregular observation gaps remain relevant.
#   The analysis start is the earliest parseable Period_i *endpoint*; it does
#   not necessarily represent the actual first mapped T0 channel observation.
#   The full source history and complete output GeoPackage may be memory/disk
#   intensive: per-feature records, point index and all audit totals are cached.
#
# REPRODUCIBILITY AND DESTRUCTIVE OUTPUT
#   The destination GeoPackage is REPLACED, never written over Module 4a input.
#   Validate the source class field, Period_i dates, T0 metadata, final states,
#   geographic units and Module 4a mismatch diagnostics before publication.
#   This archive edition does not constitute a fresh QGIS runtime validation.
#
"""
FRAF Module 4d — Assemblage Metrics v3.5
========================================

Purpose
-------
Post-process the full-history analytical layer produced by FRAF Module 4a v10.9
without rebuilding the planar assemblage fabric.

Required Module 4a v10.9 input
---------------------------
Use:

    Assemblage_Units_FULL_ATTRS

The layer must contain matching EA_Class_i and Period_i history fields.

Do not use Assemblage_Display, Assemblage_StatsFabric, or Assemblage_Dissolved;
those layers omit the complete EA_Class_i / Period_i history.

Module 4a v10.9 support and state model
----------------------------------------
Module 4a v10.9 preserves the original evidence/state separation and adds a
provenance-aware T0 seed, state continuity across recognised support gaps, and
Module-3B-consistent storage stabilisation. The principal information streams are:

1. EA_Class_i records mapped process/class evidence. Source-unsupported values are
   written as reworked_unresolved, while validated background cells are filled as
   stable_floodplain.
2. N_ASSIGNED / P_ASSIGNED retain direct EA-source support before those fills.
3. ONTO_STATE_i preserves the complete Module 4a state interpretation used for
   state composition, diversity, and transition metrics.

This script therefore uses EA_Class_i for erosion/deposition events, N_ASSIGNED
for direct support totals, BG_FP for validated background, and ONTO_STATE_i for
the state history.

Main revisions in v3.5 (Module 4a v10.9 compatibility)
-------------------------------------------------------
- Treats FINAL_ONTO_STATE as the authoritative endpoint assemblage state. Module 4d
  no longer independently promotes Depositional Storage to Stabilised Floodplain.
- Removes the former disturbance-episode gate from DS -> SF state classification;
  REWORKED_EPISODES is retained only for descriptive floodplain-condition classes.
- Includes INIT_STATE as the T0 seed when counting state transitions, matching v10.9.
  T0 is not added to state occupancy or Shannon diversity, matching Module 4a.
- Carries v10.9 provenance/censoring fields into the unit metrics (INIT_STATE,
  INIT_PROV, INIT_CONTEXT, LEFT_CENS, AGE_CENSORED, SF_PROV, SURFACE_AGE_TYPE,
  STORAGE_AGE_YR and STORAGE_AGE_CENS).
- Aligns raw fallback ontology with v10.9: stable/vegetated islands are Stabilised
  Floodplain with island context; generic island labels remain unresolved.
- Adds DS -> AD storage-reworking and SF -> DS floodplain-to-storage transition counts.
- Retains EA_Class_i for disturbance/event metrics and ONTO_STATE_i for state
  composition and Shannon diversity.

Retained v3.4 revisions (schema collision and support auditing)
-------------------------------------------------------------
- Rebuilds the spatial-output schema from non-4d source fields plus one canonical
  copy of every Module 4d metric field. Spatial area metrics use AREA_MAP2_4D and
  AREA_KM2_4D, preserving any source AREA_MAP2 / AREA_KM2 fields and preventing
  exact-name or case-variant collisions.
- Detects and omits case-insensitive duplicate source fields that GeoPackage/SQLite
  cannot store, while preserving the first source occurrence.
- Fails with a clear message when an existing output GeoPackage cannot be deleted
  because it is open or locked.
- Emits a stronger QA warning when unrecognised EA_Class_i values are numeric,
  because this usually indicates that an ID/code field was used as the Module 4a
  class field.
- Uses matching ONTO_STATE_i fields as the primary state-history source, while
  retaining EA_Class_i for process-event and direct EA-support audits.
- Retains FINAL_ONTO_RAW for raw endpoint QA while FINAL_ONTO_STATE is the
  authoritative endpoint assemblage state.
- Treats Module 4a reworked_unresolved values as outside direct EA support and as
  known non-event opportunities, matching Module 4a disturbance calculations.
- Separates validated background-floodplain histories (BG_FP) from direct EA
  support and reports their contribution explicitly.
- Uses Module 4a v10.9 storage/stabilisation state history directly; episode count
  is descriptive and does not gate DS -> SF stabilisation.
- Renames valid/missing audit concepts as EA support/outside EA support.
- Adds N_EA_SUPPORT_4D, N_OUTSIDE_EA_4D, EA_SUPPORT_FRAC_4D, and
  OUTSIDE_EA_FRAC_4D.
- Adds N_EVENT_OBS_4D and EVENT_OBS_FRAC_4D.
- DIST_FREQ_4D is now the all-known-opportunity disturbance frequency:
  disturbance observations / event-observed intervals.
- Adds EA_COND_FREQ_4D: disturbance observations / intervals inside EA support.
- Activity, episode, quiet-time, and local reworking metrics use the complete
  known event-opportunity sequence rather than compressing to EA-supported rows.
- State frequencies, Shannon diversity, and state transitions use ONTO_STATE_i
  and are labelled with STATE_BASIS_4D.
- Final state uses FINAL_ONTO_STATE and is checked against the final ONTO_STATE_i;
  FINAL_ONTO_RAW is retained separately for raw endpoint auditing.
- Prevents persistence from promoting an unresolved final state to floodplain.
- Produces three EA-support audit tables in the GeoPackage and as CSV.

Important definitions
---------------------
- Disturbance means erosion or deposition process observations, including island
  erosion/deposition aliases. It is not identical to Active Domain occupation.
- PERSIST_YRS_4D is elapsed time since the last mapped disturbance. If no
  disturbance is observed and final state is resolved, it is the full observed
  record duration.
- EA-support AREA_TIME fields repeat polygon area once per timestep. They are
  observation-weighted, not duration-weighted.
- Legacy fields N_VALID_4D, N_MISSING_4D, and VALID_FRAC_4D are retained as
  aliases of N_EA_SUPPORT_4D, N_OUTSIDE_EA_4D, and EA_SUPPORT_FRAC_4D.

Recommended smoothing radius
----------------------------
Mamoré: 300 m (approximately half a channel width).
Use a projected CRS. Radius and minimum area are interpreted in map units.
"""

import csv
import math
import os
import re
from collections import defaultdict
from datetime import date

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputFile,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsSpatialIndex,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)


# Module 4d metadata below is the existing QGIS algorithm class; the
# archive filename changes neither discovery nor run-time registration.
class FRAFModule4dAssemblageMetricsV35(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    RADIUS = "RADIUS"
    MIN_AREA = "MIN_AREA"
    END_YEAR = "END_YEAR"
    PERSISTENCE_YEARS = "PERSISTENCE_YEARS"
    REWORKED_EPISODES = "REWORKED_EPISODES"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    TABLE_FOLDER = "TABLE_FOLDER"

    OUTPUT_LAYER = "OUTPUT_LAYER"
    UNIT_TABLE = "UNIT_TABLE"
    REACH_TABLE = "REACH_TABLE"
    CLASS_TABLE = "CLASS_TABLE"
    ASSIGN_STEP_CLASS_TABLE = "ASSIGN_STEP_CLASS_TABLE"
    ASSIGN_REACH_TABLE = "ASSIGN_REACH_TABLE"
    ASSIGN_STEP_STATUS_TABLE = "ASSIGN_STEP_STATUS_TABLE"

    # Stable names for the seven GeoPackage layers: one geometry layer, three
    # metrics tables and three evidence-support audit tables.
    SPATIAL_LAYER_NAME = "Assemblage_Metrics_4d"
    UNIT_LAYER_NAME = "Unit_Metrics_4d"
    REACH_LAYER_NAME = "Reach_Metrics_4d"
    CLASS_LAYER_NAME = "Class_Summary_4d"
    ASSIGN_STEP_CLASS_LAYER_NAME = "EA_Support_By_Step_Class_4d"
    ASSIGN_REACH_LAYER_NAME = "EA_Support_Reach_Summary_4d"
    ASSIGN_STEP_STATUS_LAYER_NAME = "EA_Support_By_Step_Status_4d"

    # Disturbance alias dictionaries operate on raw EA_Class_i labels, not on
    # organisational transition flags from the separate risk-table pipeline.
    EROSION_CLASSES = {
        "erosion",
        "bank_erosion",
        "channel_erosion",
        "island_erosion",
        "island_ero",
        "isl_erosion",
    }

    DEPOSITION_CLASSES = {
        "deposition",
        "bank_deposition",
        "channel_deposition",
        "migration_deposition",
        "infill_deposition",
        "island_deposition",
        "island_dep",
        "isl_deposition",
    }

    # AD aliases represent mapped active/channel occupation; do not equate
    # these labels directly with every erosional footprint.
    ACTIVE_DOMAIN_CLASSES = {
        "stable_channel",
        "channel",
        "channel_surface",
        "active_channel",
        "water",
        "inchannel_surface",
        "active_domain",
        "active_braidplain",
        "active_zone",
        "active_water",
    }

    # Storage aliases indicate non-active deposition/storage evidence when raw
    # fallback classification is used; primary state history comes from 4a.
    STORAGE_CLASSES = {
        "depositional_storage",
        "active_storage",
        "storage",
        "bar_deposition",
        "new_bar",
        "bar",
        "bar_storage",
    }

    # Stable island is assigned to SF when explicitly labelled as stable,
    # while a generic unqualified island is unresolved.
    STABILISED_FLOODPLAIN_CLASSES = {
        "stable_floodplain",
        "inactive_floodplain",
        "persistent_floodplain",
        "floodplain",
        "stable_fp",
        "stabilised_floodplain",
        "stabilized_floodplain",
        "vegetated_floodplain",
        "stable_island",
        "vegetated_island",
    }

    UNRESOLVED_CLASSES = {
        "",
        "none",
        "null",
        "nan",
        "no_data",
        "nodata",
        "undefined",
        "undefined_surface",
        "unresolved",
        "reworked_unresolved",
        "inactive",
        "island",
        "island_surface",
    }

    # Thresholds classify descriptive disturbance structure and neighbourhood
    # activity; they are not calibrated event probabilities or hazard cutoffs.
    INTERMITTENT_MAX = 0.25
    EPISODIC_MAX = 0.45

    LOCAL_LOW_MAX = 0.12
    LOCAL_MODERATE_MAX = 0.25
    LOCAL_HIGH_MAX = 0.45

    # name: The stable internal Processing algorithm ID is deliberately retained.
    def name(self):
        return "fraf_module4d_assemblage_metrics_v3_5_module4a_v10_9_compatible"

    # displayName: User-facing QGIS Toolbox label, not an archive-version control.
    def displayName(self):
        return "FRAF Module 4d — Assemblage Metrics v3.5 (Module 4a v10.9 compatible)"

    # group: Original Toolbox grouping is retained for project compatibility.
    def group(self):
        return "FRAF"

    # groupId: Original provider-group identifier must not change in a comment-only release.
    def groupId(self):
        return "fraf"

    # createInstance: Required QGIS Processing factory for repeatable algorithm instantiation.
    def createInstance(self):
        return FRAFModule4dAssemblageMetricsV35()

    # shortHelpString: Summarises v10.9 input requirements and derived metrics for users.
    def shortHelpString(self):
        return (
            "Recalculate disturbance, elapsed-year persistence, ONTO_STATE_i state "
            "composition, transition, QA, and local-neighbourhood metrics from "
            "Module 4a v10.9 Assemblage_Units_FULL_ATTRS. Direct EA support uses "
            "N_ASSIGNED, validated background uses BG_FP, and reworked_unresolved "
            "timesteps remain non-event opportunities without inventing a state. "
            "The spatial layer writes recalculated area metrics as AREA_MAP2_4D and "
            "AREA_KM2_4D so source area fields are preserved. The output GeoPackage "
            "contains a spatial layer, three metric tables, and three EA-support audit tables; all "
            "tables are also written as CSV."
        )

    # initAlgorithm: Declare all input parameters and output contracts with existing IDs.
    # The recommended 300 m radius is reach-specific, not a universal scale.
    # Input is the full-history polygon layer, not an aggregated stats/display
    # fabric that has dropped EA_Class_i and Period_i columns.
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                "Module 4a v10.9 full-history layer: Assemblage_Units_FULL_ATTRS",
                [QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                "Representative-point neighbourhood radius (map units; Mamoré: 300 m)",
                QgsProcessingParameterNumber.Double,
                defaultValue=300.0,
                minValue=0.0,
            )
        )

        # MIN_AREA filters *neighbours* from local averaging, except the focal unit.
        # It does not delete small assemblage polygons from the output.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_AREA,
                "Ignore neighbouring polygons smaller than this area (square map units; 0 = include all)",
                QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )

        # END_YEAR=0 chooses the final observed Period_i endpoint; specifying a
        # year can extend elapsed-time metrics beyond the last observed step.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.END_YEAR,
                "Analysis end year (0 = latest Period_i date; requested year uses the same month/day)",
                QgsProcessingParameterNumber.Integer,
                defaultValue=0,
                minValue=0,
                maxValue=9999,
            )
        )

        # This persistence threshold describes condition within authoritative SF
        # and must not be mistaken for a new DS->SF eligibility rule.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PERSISTENCE_YEARS,
                "Floodplain-condition persistence threshold (years; does not reclassify v10.9 final state)",
                QgsProcessingParameterNumber.Double,
                defaultValue=20.0,
                minValue=0.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.REWORKED_EPISODES,
                "Minimum disturbance episodes for descriptive Reworked Floodplain condition (not a stabilisation gate)",
                QgsProcessingParameterNumber.Integer,
                defaultValue=3,
                minValue=1,
            )
        )

        # Target GeoPackage is overwritten; choose a path distinct from source and
        # retain a separate archived copy if older results must be reproducible.
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_GPKG,
                "Output multi-layer GeoPackage",
                "GeoPackage (*.gpkg)",
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.TABLE_FOLDER,
                "Folder for CSV metric tables",
            )
        )

        # The outputs include separate table paths because both GeoPackage and
        # machine-readable CSV are part of the audit/reproduction contract.
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT_LAYER,
                "Assemblage_Metrics_4d spatial layer",
            )
        )
        self.addOutput(QgsProcessingOutputFile(self.UNIT_TABLE, "Per-unit metrics CSV"))
        self.addOutput(QgsProcessingOutputFile(self.REACH_TABLE, "Reach metrics CSV"))
        self.addOutput(QgsProcessingOutputFile(self.CLASS_TABLE, "Class summary CSV"))
        self.addOutput(
            QgsProcessingOutputFile(
                self.ASSIGN_STEP_CLASS_TABLE,
                "EA support by timestep and raw class CSV",
            )
        )
        self.addOutput(
            QgsProcessingOutputFile(
                self.ASSIGN_REACH_TABLE,
                "Reach-wide EA-support audit CSV",
            )
        )
        self.addOutput(
            QgsProcessingOutputFile(
                self.ASSIGN_STEP_STATUS_TABLE,
                "EA support by timestep and status CSV",
            )
        )

    # GENERAL UTILITIES: field compatibility, date parsing, output safety and
    # input ID handling are kept separate from the geomorphic metrics.
    # ------------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------------
    # _cancel_if_requested: Stop long-running loops explicitly rather than returning partial metrics.
    @staticmethod
    def _cancel_if_requested(feedback):
        if feedback.isCanceled():
            raise QgsProcessingException("Processing cancelled by user.")

    # _field_names: Return the source schema in provider order for field discovery.
    @staticmethod
    def _field_names(layer):
        return [field.name() for field in layer.fields()]

    # _field_index_case_insensitive: GeoPackage field-name uniqueness is effectively case-insensitive.
    # Prefer exact matches, then allow aliases differing only by case.
    @staticmethod
    def _field_index_case_insensitive(fields, name):
        """Return an exact or case-insensitive field index, or -1 when absent."""
        exact_index = fields.indexFromName(name)
        if exact_index >= 0:
            return exact_index
        target = str(name).casefold()
        for index, field in enumerate(fields):
            if field.name().casefold() == target:
                return index
        return -1

    # _add_field_if_missing: Add a field only when there is no exact/case-variant name collision.
    @classmethod
    def _add_field_if_missing(cls, fields, name, qvariant, length=0, precision=0):
        """Append a field only when no exact or case-variant name exists."""
        index = cls._field_index_case_insensitive(fields, name)
        if index < 0:
            fields.append(QgsField(name, qvariant, "", length, precision))
            index = len(fields) - 1
        return index

    # _clean_class: Normalise EA labels for consistent ontology/process alias comparisons.
    @staticmethod
    def _clean_class(value):
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "_").replace("-", "_")

    # _safe_float: Convert values to finite floats; treat NULL, NaN and infinity as missing.
    @staticmethod
    def _safe_float(value):
        if value is None:
            return None
        try:
            output = float(value)
            if math.isnan(output) or math.isinf(output):
                return None
            return output
        except (TypeError, ValueError):
            return None

    # _years_between: Express dated durations as elapsed days / 365.25, clamped at zero.
    @staticmethod
    # Elapsed years are calculated from actual parsed dates, while many event
    # frequency and diversity values count sampled timesteps equally.
    def _years_between(start_date, end_date):
        if start_date is None or end_date is None:
            return None
        return max(0.0, float((end_date - start_date).days) / 365.25)

    # _parse_period_end_date: Recover the last date in a paired Period_i string; year-only becomes 1 Jan.
    # Values that cannot be interpreted are returned as missing.
    @staticmethod
    def _parse_period_end_date(value):
        """Return the last parseable date in a Module 4a Period_i value."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None

        compact = text.replace("/", "_").replace("-", "_")

        # Pick all full yyyy-mm-dd matches from a compound period label and use
        # the *last* match as interval endpoint.
        matches = re.findall(
            r"((?:18|19|20)\d{2})_?(\d{2})_?(\d{2})",
            compact,
        )
        parsed = []
        for year_text, month_text, day_text in matches:
            try:
                parsed.append(date(int(year_text), int(month_text), int(day_text)))
            except ValueError:
                continue
        if parsed:
            return parsed[-1]

        years = re.findall(r"(?:18|19|20)\d{2}", compact)
        if years:
            try:
                return date(int(years[-1]), 1, 1)
            except ValueError:
                return None
        return None

    # _date_with_year: Apply an optional explicit end year while preserving the source month/day.
    # Shorten invalid late-month dates (e.g., leap day) where necessary.
    @staticmethod
    def _date_with_year(template_date, requested_year):
        if template_date is None:
            return date(requested_year, 1, 1)
        month = template_date.month
        day = template_date.day
        while day > 28:
            try:
                return date(requested_year, month, day)
            except ValueError:
                day -= 1
        return date(requested_year, month, day)

    # _safe_delete_gpkg: Replacing the output GeoPackage can delete earlier results.
    # Refuse to continue if its file/SQLite sidecars cannot be removed.
    @staticmethod
    # This is deliberately a destructive output-file operation; QGIS layers
    # holding the destination open may cause an informative failure.
    def _safe_delete_gpkg(path):
        """Delete an existing GeoPackage and fail clearly if it remains locked."""
        failures = []
        for candidate in (path, path + "-shm", path + "-wal"):
            try:
                if os.path.exists(candidate):
                    os.remove(candidate)
            except OSError as exc:
                failures.append(f"{candidate}: {exc}")

        remaining = [
            candidate
            for candidate in (path, path + "-shm", path + "-wal")
            if os.path.exists(candidate)
        ]
        if remaining:
            detail = "; ".join(failures) if failures else ", ".join(remaining)
            raise QgsProcessingException(
                "Could not replace the output GeoPackage because it is open, locked, "
                f"or otherwise undeletable: {path}. Close/remove the existing output "
                f"and rerun. Details: {detail}"
            )

    # _normalise_gpkg_path: Turn a Processing destination URI into a filesystem GeoPackage path.
    @staticmethod
    def _normalise_gpkg_path(path):
        value = str(path or "").strip()
        if "|" in value:
            value = value.split("|", 1)[0]
        if not value.lower().endswith(".gpkg"):
            value += ".gpkg"
        return os.path.abspath(value)

    # _value_for_csv: Serialize None as blank in QA and publication CSV tables.
    @staticmethod
    def _value_for_csv(value):
        return "" if value is None else value

    # _create_writer: Create GIS and no-geometry table writers with explicit overwrite semantics.
    # A writer error is treated as fatal to avoid incomplete archives.
    # QgsVectorFileWriter is used for both polygon features and attribute-only
    # tables, with provider errors checked before returning the writer.
    def _create_writer(
        self,
        gpkg_path,
        layer_name,
        fields,
        wkb_type,
        crs,
        context,
        overwrite_file=False,
    ):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"
        options.layerName = layer_name
        options.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteFile
            if overwrite_file
            else QgsVectorFileWriter.CreateOrOverwriteLayer
        )

        writer = QgsVectorFileWriter.create(
            gpkg_path,
            fields,
            wkb_type,
            crs,
            context.transformContext(),
            options,
        )

        if writer is None:
            raise QgsProcessingException(
                f"Could not create GeoPackage writer for layer {layer_name}."
            )
        if writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if hasattr(writer, "errorMessage") else "unknown writer error"
            raise QgsProcessingException(
                f"Could not create {layer_name} in {gpkg_path}: {message}"
            )
        return writer

    # _verify_gpkg_layer: Reopen a completed GeoPackage layer and report the provider feature count.
    @staticmethod
    def _verify_gpkg_layer(gpkg_path, layer_name):
        uri = f"{gpkg_path}|layername={layer_name}"
        layer = QgsVectorLayer(uri, layer_name, "ogr")
        if layer is None or not layer.isValid():
            raise QgsProcessingException(
                f"GeoPackage verification failed for layer {layer_name}."
            )
        return uri, layer.featureCount()

    # _discover_unit_id_field: Find an existing stable identifier; assemblage FAB IDs are preferred.
    # PLACE_ID/BLOCK_ID are acceptable only if that is the source schema.
    @staticmethod
    # Distinct assemblage-unit IDs may differ from the separate fixed-place
    # PLACE_ID lattice; do not assume units and risk cells are interchangeable.
    def _discover_unit_id_field(layer):
        names = [field.name() for field in layer.fields()]
        lower_lookup = {name.lower(): name for name in names}
        for candidate in (
            "_FAB_ID",
            "FAB_ID",
            "ASM_ID",
            "PLACE_ID",
            "BLOCK_ID",
            "UNIT_ID",
        ):
            actual = lower_lookup.get(candidate.lower())
            if actual:
                return actual
        return None

    # _make_unit_id: Use the selected ID, falling back to provider feature ID if unavailable.
    # Provider-generated IDs may be unstable across re-exports.
    @staticmethod
    def _make_unit_id(feature, id_field):
        if id_field:
            value = feature[id_field]
            if value is not None and str(value).strip() != "":
                return str(value)
        return str(feature.id())

    # STATE/EPISODE METRICS: primary state series is categorical ONTO_STATE_i;
    # EA_Class_i only supplies physical-process evidence and disturbance runs.
    # ------------------------------------------------------------------
    # State, diversity, and run metrics
    # ------------------------------------------------------------------
    # _onto_state: Legacy raw-class fallback classifier. v3.5 primary state analyses use
    # authoritative ONTO_STATE_i and FINAL_ONTO_STATE, not this shortcut.
    def _onto_state(self, cleaned):
        if cleaned in self.DEPOSITION_CLASSES or cleaned in self.STORAGE_CLASSES:
            return "DEPOSITIONAL_STORAGE"
        if cleaned in self.EROSION_CLASSES or cleaned in self.ACTIVE_DOMAIN_CLASSES:
            return "ACTIVE_DOMAIN"
        if cleaned in self.STABILISED_FLOODPLAIN_CLASSES:
            return "STABILISED_FLOODPLAIN"
        return "UNRESOLVED"

    # _class_status: Separate mapped disturbance events, supported non-events and unresolved
    # or outside-EA-support values without inventing extra states.
    def _class_status(self, value):
        cleaned = self._clean_class(value)
        if cleaned in self.EROSION_CLASSES or cleaned in self.DEPOSITION_CLASSES:
            return "event", cleaned, self._onto_state(cleaned)
        state = self._onto_state(cleaned)
        if state != "UNRESOLVED":
            return "valid_non_event", cleaned, state
        if cleaned in {"", "none", "null", "nan", "reworked_unresolved"}:
            return "outside_support", cleaned, "UNRESOLVED"
        if cleaned in self.UNRESOLVED_CLASSES:
            return "unresolved", cleaned, "UNRESOLVED"
        return "unknown", cleaned, "UNRESOLVED"

    # _assignment_audit_category: Translate raw-class status into mutually defined audit categories.
    # Background floodplain is applied separately in the main loop.
    @staticmethod
    def _assignment_audit_category(cleaned, status):
        """Return support-aware categories without inventing a state outside support."""
        if status == "event":
            return "event"
        if status == "valid_non_event":
            return "supported_non_event"
        if status == "outside_support":
            return "outside_ea_support"
        if status == "unknown":
            return "unknown"
        if cleaned == "inactive":
            return "explicit_inactive"
        if cleaned in {"no_data", "nodata"}:
            return "no_observation"
        return "processing_unresolved"

    # _audit_raw_label: Represent genuinely empty EA labels explicitly in QA tables.
    @staticmethod
    def _audit_raw_label(cleaned):
        return cleaned if cleaned else "<blank>"

    # _audit_state_label: Human-readable AD/DS/SF/unresolved labels for audit outputs.
    @staticmethod
    def _audit_state_label(state):
        return {
            "ACTIVE_DOMAIN": "Active Domain",
            "DEPOSITIONAL_STORAGE": "Depositional Storage",
            "STABILISED_FLOODPLAIN": "Stabilised Floodplain",
            "UNRESOLVED": "Unresolved",
        }.get(state, "Unresolved")

    # _normalise_final_state: Translate Module 4a endpoint aliases to its three-state vocabulary.
    # Stable/vegetated island is SF; unspecified island remains unresolved.
    @staticmethod
    def _normalise_final_state(value):
        cleaned = "" if value is None else str(value).strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned in {
            "active_domain", "active", "channel", "stable_channel",
            "active_channel", "active_braidplain", "active_zone",
        }:
            return "active_domain"
        if cleaned in {
            "depositional_storage", "storage", "active_storage",
            "bar", "bar_storage", "bar_deposition", "new_bar",
        }:
            return "depositional_storage"
        if cleaned in {
            "stabilised_floodplain", "stabilized_floodplain", "floodplain",
            "stable_floodplain", "persistent_floodplain", "recent_floodplain",
            "reworked_floodplain", "inactive_floodplain",
            "stable_island", "vegetated_island",
        }:
            return "stabilised_floodplain"
        return "unresolved"

    # _normalise_onto_history_state: Map each authoritative ONTO_STATE_i value to the canonical state.
    # Unknown and unclassifiable values remain UNRESOLVED.
    @staticmethod
    def _normalise_onto_history_state(value):
        cleaned = "" if value is None else str(value).strip().upper().replace(" ", "_").replace("-", "_")
        if cleaned in {"ACTIVE_DOMAIN", "ACTIVE", "CHANNEL", "STABLE_CHANNEL"}:
            return "ACTIVE_DOMAIN"
        if cleaned in {"DEPOSITIONAL_STORAGE", "STORAGE", "BAR", "BAR_STORAGE"}:
            return "DEPOSITIONAL_STORAGE"
        if cleaned in {
            "STABILISED_FLOODPLAIN", "STABILIZED_FLOODPLAIN",
            "STABLE_FLOODPLAIN", "FLOODPLAIN", "STABLE_ISLAND", "VEGETATED_ISLAND"
        }:
            return "STABILISED_FLOODPLAIN"
        return "UNRESOLVED"

    # _run_metrics: Summarise contiguous disturbance episodes, quiet runs and temporal density.
    # Gaps in the supplied step numbers break runs; output counts steps not years.
    @staticmethod
    # An event run consists of consecutive observed step indexes flagged as
    # erosion/deposition; intervening non-events break the run.
    def _run_metrics(observed_sequence):
        """
        observed_sequence is [(step_index, is_event), ...]. Outside-EA-support
        intervals are included as known non-events. Genuine no-observation,
        processing-unresolved, and unknown intervals are omitted; a gap in step
        indices therefore breaks an event run and a quiet run.
        """
        if not observed_sequence:
            return 0, 0, 0, 0, 0.0

        # Zero-event units retain zero episode density and zero quiet-run length
        # under this existing definition, rather than accruing a full-span quiet run.
        n_events = sum(1 for _, is_event in observed_sequence if is_event)
        if n_events == 0:
            return 0, 0, 0, 0, 0.0

        n_episodes = 0
        longest_event_run = 0
        current_event_run = 0
        max_quiet_steps = 0
        quiet_run = 0
        first_event_position = None
        last_event_position = None
        previous_step = None
        previous_event = False

        # Step index discontinuities signal missing calendar observations; the
        # algorithm breaks an event/quiet run rather than treating gaps as evidence.
        for position, (step_index, is_event) in enumerate(observed_sequence):
            consecutive = previous_step is not None and step_index == previous_step + 1
            if not consecutive:
                previous_event = False
                current_event_run = 0
                quiet_run = 0

            if is_event:
                if first_event_position is None:
                    first_event_position = position
                last_event_position = position
                current_event_run = current_event_run + 1 if consecutive else 1
                longest_event_run = max(longest_event_run, current_event_run)
                if not previous_event:
                    n_episodes += 1
                quiet_run = 0
            else:
                current_event_run = 0
                if first_event_position is not None and consecutive:
                    quiet_run += 1
                    max_quiet_steps = max(max_quiet_steps, quiet_run)
                else:
                    quiet_run = 0

            previous_event = is_event
            previous_step = step_index

        # Density measures event prevalence over the indexed first-to-last event
        # span, not per-year recurrence frequency.
        observed_span = (
            last_event_position - first_event_position + 1
            if first_event_position is not None and last_event_position is not None
            else 0
        )
        density = float(n_events) / float(observed_span) if observed_span > 0 else 0.0
        return n_episodes, max_quiet_steps, longest_event_run, observed_span, density

    # _shannon_from_states: Calculate recognised-state occupancy and Shannon H.
    # H/ln(3) normalises against the three supported organisational states.
    # Unresolved steps and the T0 state are excluded from occupancy.
    @staticmethod
    # A recognised-state count is an occupancy count per timestep; because
    # irregular observation intervals are not time weighted, compare carefully.
    def _shannon_from_states(states):
        counts = {
            "ACTIVE_DOMAIN": 0,
            "DEPOSITIONAL_STORAGE": 0,
            "STABILISED_FLOODPLAIN": 0,
        }
        for state in states:
            if state in counts:
                counts[state] += 1

        n_valid = sum(counts.values())
        richness = sum(1 for value in counts.values() if value > 0)
        if n_valid <= 0:
            return counts, 0.0, 0.0, 0, "unresolved"

        shannon = 0.0
        for count in counts.values():
            if count > 0:
                probability = float(count) / float(n_valid)
                shannon -= probability * math.log(probability)
        h_norm = shannon / math.log(3.0)

        if richness <= 1 or h_norm <= 0.000001:
            h_class = "single_state"
        elif h_norm < 0.33:
            h_class = "low_diversity"
        elif h_norm < 0.66:
            h_class = "moderate_diversity"
        else:
            h_class = "high_diversity"

        return counts, shannon, h_norm, richness, h_class

    # _transition_counts: Count recognised changes between successive states, including T0 seed.
    # Track SF->AD, AD->DS, DS->SF, DS->AD, SF->DS separately.
    # Any UNRESOLVED endpoint prevents a transition from being counted.
    @staticmethod
    # Transition counts are descriptive path summaries. A direct SF->DS
    # movement is counted even though it is not a principal Cox transition.
    def _transition_counts(states_all):
        """Count v10.9 three-state transitions, including the optional T0 seed."""
        reactivation = 0
        storage = 0
        stabilisation = 0
        storage_reworking = 0
        floodplain_to_storage = 0
        total = 0

        for previous, current in zip(states_all[:-1], states_all[1:]):
            if previous == "UNRESOLVED" or current == "UNRESOLVED" or previous == current:
                continue
            total += 1
            if previous == "STABILISED_FLOODPLAIN" and current == "ACTIVE_DOMAIN":
                reactivation += 1
            elif previous == "ACTIVE_DOMAIN" and current == "DEPOSITIONAL_STORAGE":
                storage += 1
            elif previous == "DEPOSITIONAL_STORAGE" and current == "STABILISED_FLOODPLAIN":
                stabilisation += 1
            elif previous == "DEPOSITIONAL_STORAGE" and current == "ACTIVE_DOMAIN":
                storage_reworking += 1
            elif previous == "STABILISED_FLOODPLAIN" and current == "DEPOSITIONAL_STORAGE":
                floodplain_to_storage += 1

        return (
            reactivation, storage, stabilisation, storage_reworking,
            floodplain_to_storage, total
        )

    # _activity_class: Descriptive disturbance-frequency class based on event opportunities.
    # These bins are not inferential hazard or transition-rate estimates.
    def _activity_class(self, n_valid, n_events, frequency):
        if n_valid <= 0 or frequency is None:
            return "unresolved"
        if n_events == 0:
            return "stable"
        if n_events == 1:
            return "single"
        if frequency < self.INTERMITTENT_MAX:
            return "intermittent"
        if frequency < self.EPISODIC_MAX:
            return "episodic"
        return "continuous"

    # _structure_class: Describe repeated, continuous or separated disturbance episodes.
    # Thresholds are empirical categories over observations, not years.
    @staticmethod
    def _structure_class(
        n_valid,
        n_events,
        n_episodes,
        max_quiet_steps,
        longest_event_run,
        density,
    ):
        if n_valid <= 0:
            return "unresolved"
        if n_events == 0:
            return "stable"
        if n_events == 1:
            return "single_activity"
        if density >= 0.75 and max_quiet_steps <= 1:
            return "continuous"
        if longest_event_run >= 2:
            return "episodic"
        if n_episodes >= 2:
            return "intermittent"
        return "episodic"

    # _local_activity_class: Convert continuous neighbourhood disturbance frequency to classes.
    def _local_activity_class(self, frequency):
        value = self._safe_float(frequency)
        if value is None:
            return "unresolved"
        if value <= 0.0:
            return "none"
        if value < self.LOCAL_LOW_MAX:
            return "low"
        if value < self.LOCAL_MODERATE_MAX:
            return "moderate"
        if value < self.LOCAL_HIGH_MAX:
            return "high"
        return "very_high"

    # _state_label: Convert uppercase internal ontology keys into lower-case output labels.
    @staticmethod
    def _state_label(state):
        return {
            "ACTIVE_DOMAIN": "active_domain",
            "DEPOSITIONAL_STORAGE": "depositional_storage",
            "STABILISED_FLOODPLAIN": "stabilised_floodplain",
            "UNRESOLVED": "unresolved",
        }.get(state, "unresolved")

    # _v109_state_and_condition: Preserve Module 4a v10.9 final state and add descriptive FP condition.
    # Episode history labels reworked SF, but never demotes SF to DS.
    # This helper does not infer new SF eligibility and does not recalculate
    # the original stabilisation clock maintained by Module 4a v10.9.
    def _v109_state_and_condition(
        self,
        authoritative_final_state,
        persistence_years,
        n_episodes,
        persistence_threshold,
        reworked_episode_threshold,
    ):
        """Keep the Module 4a v10.9 endpoint state; classify condition descriptively.

        The episode threshold may label an already-stabilised surface as reworked,
        but it never prevents or reverses DS -> SF stabilisation.
        """
        fp_stab = 0
        fp_recent = 0
        fp_reworked = 0
        final_state = authoritative_final_state

        if final_state == "unresolved":
            return "unresolved", "Unclassified", fp_stab, fp_recent, fp_reworked

        if final_state == "active_domain":
            return "active_domain", "Active Domain", fp_stab, fp_recent, fp_reworked

        if final_state == "depositional_storage":
            return (
                "depositional_storage",
                "Depositional Storage",
                fp_stab,
                fp_recent,
                fp_reworked,
            )

        if final_state == "stabilised_floodplain":
            fp_stab = 1
            if n_episodes >= reworked_episode_threshold:
                fp_reworked = 1
                return (
                    "stabilised_floodplain",
                    "Reworked Floodplain",
                    fp_stab,
                    fp_recent,
                    fp_reworked,
                )
            if persistence_years is not None and persistence_years >= persistence_threshold:
                return (
                    "stabilised_floodplain",
                    "Persistent Floodplain",
                    fp_stab,
                    fp_recent,
                    fp_reworked,
                )
            fp_recent = 1
            return (
                "stabilised_floodplain",
                "Recent Floodplain",
                fp_stab,
                fp_recent,
                fp_reworked,
            )

        return "unresolved", "Unclassified", fp_stab, fp_recent, fp_reworked

    # TABULAR CONTRACT: output schemas are explicitly fixed and should not be
    # renamed during source documentation or re-archiving.
    # ------------------------------------------------------------------
    # Table helpers
    # ------------------------------------------------------------------
    # _unit_table_specs: Authoritative field order/types for per-unit attributes and flat CSV.
    # Legacy support aliases are retained alongside explicit v3.5 definitions.
    @staticmethod
    def _unit_table_specs():
        return [
            ("UNIT_ID_4D", QVariant.String, 80, 0),
            ("AREA_MAP2", QVariant.Double, 0, 3),
            ("AREA_KM2", QVariant.Double, 0, 6),
            ("START_YEAR_4D", QVariant.Int, 0, 0),
            ("END_YEAR_4D", QVariant.Int, 0, 0),
            ("ANALYSIS_YRS", QVariant.Double, 0, 3),
            ("N_STEPS_4D", QVariant.Int, 0, 0),
            ("N_EA_SUPPORT_4D", QVariant.Int, 0, 0),
            ("N_OUTSIDE_EA_4D", QVariant.Int, 0, 0),
            ("EA_SUPPORT_FRAC_4D", QVariant.Double, 0, 6),
            ("OUTSIDE_EA_FRAC_4D", QVariant.Double, 0, 6),
            ("N_BG_VALID_4D", QVariant.Int, 0, 0),
            ("BG_VALID_FRAC_4D", QVariant.Double, 0, 6),
            ("N_STATE_OBS_4D", QVariant.Int, 0, 0),
            ("STATE_OBS_FRAC_4D", QVariant.Double, 0, 6),
            ("N_EVENT_OBS_4D", QVariant.Int, 0, 0),
            ("EVENT_OBS_FRAC_4D", QVariant.Double, 0, 6),
            ("N_UNRES_4D", QVariant.Int, 0, 0),
            ("N_UNKNOWN_4D", QVariant.Int, 0, 0),
            ("N_INACTIVE_4D", QVariant.Int, 0, 0),
            # Legacy aliases retained for existing styles/tables.
            ("N_VALID_4D", QVariant.Int, 0, 0),
            ("N_MISSING_4D", QVariant.Int, 0, 0),
            ("VALID_FRAC_4D", QVariant.Double, 0, 6),
            # DIST_FREQ_4D uses N_STEPS (all known opportunities) as denominator;
            # EA_COND_FREQ_4D uses N_EA_SUPPORT instead.
            ("INACTIVE_FRAC_4D", QVariant.Double, 0, 6),
            ("DIST_COUNT_4D", QVariant.Int, 0, 0),
            ("DIST_FREQ_4D", QVariant.Double, 0, 6),
            ("EA_COND_FREQ_4D", QVariant.Double, 0, 6),
            ("N_EPISODES_4D", QVariant.Int, 0, 0),
            ("MAX_QUIET_4D", QVariant.Int, 0, 0),
            ("MAX_QUIET_YRS", QVariant.Double, 0, 3),
            ("FIRST_DIST_STEP", QVariant.Int, 0, 0),
            ("LAST_DIST_STEP", QVariant.Int, 0, 0),
            ("FIRST_DIST_YEAR", QVariant.Int, 0, 0),
            ("LAST_DIST_YEAR", QVariant.Int, 0, 0),
            # Time since mapped disturbance is separate from geomorphic surface
            # continuity age in the later publication Surface Age Mapper.
            ("YEARS_SINCE_DIST", QVariant.Double, 0, 3),
            ("PERSIST_YRS_4D", QVariant.Double, 0, 3),
            ("PERSIST_BASIS", QVariant.String, 48, 0),
            ("PERSIST_THR_YR", QVariant.Double, 0, 3),
            ("DIST_SPAN_STEPS", QVariant.Int, 0, 0),
            ("DIST_SPAN_YRS", QVariant.Double, 0, 3),
            ("DIST_DENSITY", QVariant.Double, 0, 6),
            # Occupancy fractions use recognised ONTO_STATE_i labels, divided by all
            # timesteps; unresolved intervals consequently reduce their sum.
            ("N_ACTIVE_4D", QVariant.Int, 0, 0),
            ("N_STORAGE_4D", QVariant.Int, 0, 0),
            ("N_STAB_FP_4D", QVariant.Int, 0, 0),
            ("ACTIVE_FRQ_4D", QVariant.Double, 0, 6),
            ("STORAGE_FRQ_4D", QVariant.Double, 0, 6),
            ("STAB_FP_FRQ_4D", QVariant.Double, 0, 6),
            # Transition counts use an INIT_STATE seed plus sampled state sequence;
            # the prefix 4D identifies this independent metrics post-processing.
            ("STATE_BASIS_4D", QVariant.String, 40, 0),
            ("N_REACT_4D", QVariant.Int, 0, 0),
            ("N_STORAGE_EVT_4D", QVariant.Int, 0, 0),
            ("N_STAB_EVT_4D", QVariant.Int, 0, 0),
            ("N_STORAGE_REWORK_4D", QVariant.Int, 0, 0),
            ("N_FP_STORAGE_4D", QVariant.Int, 0, 0),
            ("N_TRANS_4D", QVariant.Int, 0, 0),
            ("FINAL_RAW_4D", QVariant.String, 40, 0),
            ("FINAL_SOURCE_4D", QVariant.String, 40, 0),
            ("FINAL_STATE_4D", QVariant.String, 40, 0),
            # T0 provenance/censoring fields are carried from Module 4a so publication
            # interpretation can distinguish pre-observation surfaces from dated origins.
            ("INIT_STATE_4D", QVariant.String, 40, 0),
            ("INIT_PROV_4D", QVariant.String, 80, 0),
            ("INIT_CONTEXT_4D", QVariant.String, 80, 0),
            ("LEFT_CENS_4D", QVariant.Int, 0, 0),
            ("AGE_CENS_4D", QVariant.Int, 0, 0),
            ("SF_PROV_4D", QVariant.String, 80, 0),
            ("SURFACE_AGE_TYPE_4D", QVariant.String, 80, 0),
            ("STORAGE_AGE_YR_4D", QVariant.Double, 0, 3),
            ("STORAGE_AGE_CENS_4D", QVariant.Int, 0, 0),
            ("FP_COND_4D", QVariant.String, 40, 0),
            ("FP_STAB_4D", QVariant.Int, 0, 0),
            ("FP_RECENT_4D", QVariant.Int, 0, 0),
            ("FP_REWORK_4D", QVariant.Int, 0, 0),
            ("SHANNON_4D", QVariant.Double, 0, 6),
            ("H_NORM_4D", QVariant.Double, 0, 6),
            ("RICHNESS_4D", QVariant.Int, 0, 0),
            ("H_CLASS_4D", QVariant.String, 32, 0),
            ("H_NORM_DIFF", QVariant.Double, 0, 6),
            ("M4A_N_EVENTS", QVariant.Int, 0, 0),
            ("N_EVENTS_DIFF", QVariant.Int, 0, 0),
            ("M4A_N_EPISODES", QVariant.Int, 0, 0),
            ("N_EPISODES_DIFF", QVariant.Int, 0, 0),
            ("M4A_SINCE_DIST_YR", QVariant.Double, 0, 3),
            ("SINCE_DIST_DIFF_YR", QVariant.Double, 0, 3),
            ("STATE_CHANGED", QVariant.Int, 0, 0),
            ("ACTIVITY_CL_R", QVariant.String, 32, 0),
            ("STRUCTURE_CL_R", QVariant.String, 32, 0),
            ("LOCAL_DIST_FREQ", QVariant.Double, 0, 6),
            ("LOCAL_ACTIVITY_CL", QVariant.String, 32, 0),
            ("LOCAL_METHOD", QVariant.String, 40, 0),
        ]

    # _reach_table_specs: Dictionary-style reach summary schema with units and weighting metadata.
    @staticmethod
    def _reach_table_specs():
        return [
            ("METRIC_ID", QVariant.String, 64, 0),
            ("METRIC", QVariant.String, 100, 0),
            ("VALUE", QVariant.Double, 0, 6),
            ("UNIT", QVariant.String, 40, 0),
            ("WEIGHTING", QVariant.String, 40, 0),
            ("DEFINITION", QVariant.String, 254, 0),
        ]

    # _class_table_specs: Area and feature-count summaries by descriptive output class.
    @staticmethod
    # Descriptive class shares use final output labels, not intermediate
    # Process EA codes.
    def _class_table_specs():
        return [
            ("DIMENSION", QVariant.String, 40, 0),
            ("CLASS", QVariant.String, 80, 0),
            ("FEATURES", QVariant.Int, 0, 0),
            ("AREA_MAP2", QVariant.Double, 0, 3),
            ("AREA_KM2", QVariant.Double, 0, 6),
            ("AREA_PCT", QVariant.Double, 0, 6),
        ]

    # _assignment_step_class_specs: EA assignment evidence cross-tabulated by step, class and support status.
    @staticmethod
    # Per-step/class support audit allows validation of raw EA assignments
    # against interpreted state and inferred observation support.
    def _assignment_step_class_specs():
        return [
            ("STEP", QVariant.Int, 0, 0),
            ("EA_FIELD", QVariant.String, 80, 0),
            ("PERIOD_FIELD", QVariant.String, 80, 0),
            ("PERIOD_END", QVariant.String, 20, 0),
            ("RAW_CLASS", QVariant.String, 100, 0),
            ("STATUS", QVariant.String, 32, 0),
            ("SUPPORT_CATEGORY", QVariant.String, 40, 0),
            ("INTERPRETED_STATE", QVariant.String, 40, 0),
            ("EA_SUPPORT_FLAG", QVariant.Int, 0, 0),
            ("BACKGROUND_VALID_FLAG", QVariant.Int, 0, 0),
            ("STATE_OBS_FLAG", QVariant.Int, 0, 0),
            ("EVENT_OBS_FLAG", QVariant.Int, 0, 0),
            ("ASSIGNMENTS", QVariant.Int, 0, 0),
            ("AREA_MAP2", QVariant.Double, 0, 3),
            ("AREA_KM2", QVariant.Double, 0, 6),
            ("AREA_PCT_STEP", QVariant.Double, 0, 6),
        ]

    # _assignment_reach_specs: Whole-record area-time and assignment shares by evidence category.
    @staticmethod
    # Reach-level area-time shares repeat each unit area for each timestep;
    # they must not be read as km2-years if the intervals vary in duration.
    def _assignment_reach_specs():
        return [
            ("RAW_CLASS", QVariant.String, 100, 0),
            ("STATUS", QVariant.String, 32, 0),
            ("SUPPORT_CATEGORY", QVariant.String, 40, 0),
            ("INTERPRETED_STATE", QVariant.String, 40, 0),
            ("EA_SUPPORT_FLAG", QVariant.Int, 0, 0),
            ("BACKGROUND_VALID_FLAG", QVariant.Int, 0, 0),
            ("STATE_OBS_FLAG", QVariant.Int, 0, 0),
            ("EVENT_OBS_FLAG", QVariant.Int, 0, 0),
            ("ASSIGNMENTS", QVariant.Int, 0, 0),
            ("ASSIGNMENT_PCT", QVariant.Double, 0, 6),
            ("AREA_TIME_MAP2", QVariant.Double, 0, 3),
            ("AREA_TIME_KM2", QVariant.Double, 0, 6),
            ("AREA_TIME_PCT", QVariant.Double, 0, 6),
        ]

    # _assignment_step_status_specs: Timestep-specific audit of observed/unsupported/background shares.
    @staticmethod
    # This audit is the basis for identifying blank/unsupported/background
    # observations rather than silently assuming complete source coverage.
    def _assignment_step_status_specs():
        return [
            ("STEP", QVariant.Int, 0, 0),
            ("EA_FIELD", QVariant.String, 80, 0),
            ("PERIOD_FIELD", QVariant.String, 80, 0),
            ("PERIOD_END", QVariant.String, 20, 0),
            ("TOTAL_ASSIGNMENTS", QVariant.Int, 0, 0),
            ("EA_SUPPORT_ASSIGNMENTS", QVariant.Int, 0, 0),
            ("BACKGROUND_VALID_ASSIGNMENTS", QVariant.Int, 0, 0),
            ("STATE_OBS_ASSIGNMENTS", QVariant.Int, 0, 0),
            ("EVENT_OBS_ASSIGNMENTS", QVariant.Int, 0, 0),
            ("EA_SUPPORT_AREA_PCT", QVariant.Double, 0, 6),
            ("BACKGROUND_VALID_AREA_PCT", QVariant.Double, 0, 6),
            ("STATE_OBS_AREA_PCT", QVariant.Double, 0, 6),
            ("OUTSIDE_EA_AREA_PCT", QVariant.Double, 0, 6),
            ("EVENT_OBS_AREA_PCT", QVariant.Double, 0, 6),
            ("INACTIVE_AREA_PCT", QVariant.Double, 0, 6),
            ("NO_OBS_AREA_PCT", QVariant.Double, 0, 6),
            ("PROC_UNRES_AREA_PCT", QVariant.Double, 0, 6),
            ("UNKNOWN_AREA_PCT", QVariant.Double, 0, 6),
            ("EVENT_AREA_PCT", QVariant.Double, 0, 6),
            ("SUPPORTED_NONEVENT_AREA_PCT", QVariant.Double, 0, 6),
        ]

    # _build_fields: Materialise the declared output schema in QGIS QgsFields order.
    @staticmethod
    def _build_fields(specs):
        fields = QgsFields()
        for name, qvariant, length, precision in specs:
            fields.append(QgsField(name, qvariant, "", length, precision))
        return fields

    # _record_to_unit_row: Translate cached analytical record keys to canonical output names.
    # The same mapping drives spatial metrics and Unit_Metrics_4d tables.
    @staticmethod
    # Unit row values are derived from cached records created in the main loop,
    # not by sampling the fixed-place prediction archive.
    def _record_to_unit_row(record):
        return {
            "UNIT_ID_4D": record["unit_id"],
            "AREA_MAP2": record["area"],
            "AREA_KM2": record["area_km2"],
            "START_YEAR_4D": record["start_year"],
            "END_YEAR_4D": record["end_year"],
            "ANALYSIS_YRS": record["analysis_years"],
            "N_STEPS_4D": record["n_steps"],
            "N_EA_SUPPORT_4D": record["n_ea_support"],
            "N_OUTSIDE_EA_4D": record["n_outside_ea"],
            "EA_SUPPORT_FRAC_4D": record["ea_support_fraction"],
            "OUTSIDE_EA_FRAC_4D": record["outside_ea_fraction"],
            "N_BG_VALID_4D": record["n_bg_valid"],
            "BG_VALID_FRAC_4D": record["bg_valid_fraction"],
            "N_STATE_OBS_4D": record["n_state_observations"],
            "STATE_OBS_FRAC_4D": record["state_observation_fraction"],
            "N_EVENT_OBS_4D": record["n_event_observations"],
            "EVENT_OBS_FRAC_4D": record["event_observation_fraction"],
            "N_UNRES_4D": record["n_unresolved"],
            "N_UNKNOWN_4D": record["n_unknown"],
            "N_INACTIVE_4D": record["n_inactive"],
            # N_VALID / N_MISSING and VALID_FRAC are backward-compatible aliases;
            # new terminology should prefer EA_SUPPORT / OUTSIDE_EA in publication.
            "N_VALID_4D": record["n_ea_support"],
            "N_MISSING_4D": record["n_outside_ea"],
            "VALID_FRAC_4D": record["ea_support_fraction"],
            "INACTIVE_FRAC_4D": record["inactive_fraction"],
            "DIST_COUNT_4D": record["n_events"],
            "DIST_FREQ_4D": record["disturbance_frequency"],
            "EA_COND_FREQ_4D": record["ea_conditional_frequency"],
            "N_EPISODES_4D": record["n_episodes"],
            "MAX_QUIET_4D": record["max_quiet_steps"],
            "MAX_QUIET_YRS": record["max_quiet_years"],
            "FIRST_DIST_STEP": record["first_dist_step"],
            "LAST_DIST_STEP": record["last_dist_step"],
            "FIRST_DIST_YEAR": record["first_dist_year"],
            "LAST_DIST_YEAR": record["last_dist_year"],
            # This persistence remains last-disturbance time: deposition contributes
            # to the reset sequence, unlike surface-continuity SURFACE_AGE.
            "YEARS_SINCE_DIST": record["years_since_dist"],
            "PERSIST_YRS_4D": record["persistence_years"],
            "PERSIST_BASIS": record["persistence_basis"],
            "PERSIST_THR_YR": record["persistence_threshold"],
            "DIST_SPAN_STEPS": record["original_step_span"],
            "DIST_SPAN_YRS": record["disturbance_span_years"],
            "DIST_DENSITY": record["disturbance_density"],
            "N_ACTIVE_4D": record["n_active"],
            "N_STORAGE_4D": record["n_storage"],
            "N_STAB_FP_4D": record["n_stabilised"],
            "ACTIVE_FRQ_4D": record["active_frequency"],
            "STORAGE_FRQ_4D": record["storage_frequency"],
            "STAB_FP_FRQ_4D": record["stabilised_frequency"],
            "STATE_BASIS_4D": record["state_basis"],
            # History-derived state transitions are already reconstructed upstream;
            # Module 4d only counts them as descriptive summary fields.
            "N_REACT_4D": record["n_reactivation"],
            "N_STORAGE_EVT_4D": record["n_storage_events"],
            "N_STAB_EVT_4D": record["n_stabilisation_events"],
            "N_STORAGE_REWORK_4D": record["n_storage_reworking_events"],
            "N_FP_STORAGE_4D": record["n_fp_storage_events"],
            "N_TRANS_4D": record["n_transitions"],
            "FINAL_RAW_4D": record["final_raw"],
            "FINAL_SOURCE_4D": record["final_source"],
            "FINAL_STATE_4D": record["final_state"],
            "INIT_STATE_4D": record["init_state"],
            "INIT_PROV_4D": record["init_prov"],
            "INIT_CONTEXT_4D": record["init_context"],
            "LEFT_CENS_4D": record["left_censored"],
            "AGE_CENS_4D": record["age_censored"],
            "SF_PROV_4D": record["sf_prov"],
            "SURFACE_AGE_TYPE_4D": record["surface_age_type"],
            "STORAGE_AGE_YR_4D": record["storage_age_years"],
            "STORAGE_AGE_CENS_4D": record["storage_age_censored"],
            "FP_COND_4D": record["fp_condition"],
            "FP_STAB_4D": record["fp_stab"],
            "FP_RECENT_4D": record["fp_recent"],
            "FP_REWORK_4D": record["fp_reworked"],
            "SHANNON_4D": record["shannon"],
            "H_NORM_4D": record["h_norm"],
            "RICHNESS_4D": record["richness"],
            "H_CLASS_4D": record["h_class"],
            "H_NORM_DIFF": record["h_norm_diff"],
            "M4A_N_EVENTS": record["source_n_events"],
            "N_EVENTS_DIFF": record["n_events_diff"],
            "M4A_N_EPISODES": record["source_n_episodes"],
            "N_EPISODES_DIFF": record["n_episodes_diff"],
            "M4A_SINCE_DIST_YR": record["source_since_disturb_years"],
            "SINCE_DIST_DIFF_YR": record["since_disturb_diff_years"],
            "STATE_CHANGED": record["state_changed"],
            "ACTIVITY_CL_R": record["activity_class"],
            "STRUCTURE_CL_R": record["structure_class"],
            "LOCAL_DIST_FREQ": record["local_disturbance_frequency"],
            "LOCAL_ACTIVITY_CL": record["local_activity_class"],
            "LOCAL_METHOD": "rep_point_area_weighted_all_event_obs",
        }

    # _weighted_mean: Compute area-weighted means over eligible non-null per-unit values.
    # Areas act as weights; observation duration does not.
    @staticmethod
    # No value should be interpreted as area weighted if the record lacks
    # valid positive geometry area; those records are excluded from the mean.
    def _weighted_mean(records, value_key, filter_function=None):
        weighted_sum = 0.0
        weight_sum = 0.0
        for record in records.values():
            if filter_function is not None and not filter_function(record):
                continue
            value = record.get(value_key)
            weight = record.get("area", 0.0)
            if value is None or weight is None or weight <= 0.0:
                continue
            weighted_sum += float(value) * float(weight)
            weight_sum += float(weight)
        return weighted_sum / weight_sum if weight_sum > 0.0 else None

    # _build_reach_rows: Summarise reach area, final state composition, support and disturbances.
    # Each row records its metric definition and weight convention.
    def _build_reach_rows(
        self,
        records,
        total_area,
        total_area_km2,
        analysis_start_date,
        analysis_end_date,
        persistence_threshold,
    ):
        state_area = defaultdict(float)
        unknown_total = 0
        max_persistence = None
        changed_area = 0.0

        for record in records.values():
            area = record["area"]
            state_area[record["final_state"]] += area
            unknown_total += record["n_unknown"]
            persistence = record["persistence_years"]
            if persistence is not None:
                max_persistence = persistence if max_persistence is None else max(max_persistence, persistence)
            if record["state_changed"] == 1:
                changed_area += area

        # area_pct: Compute final-state areal share of the full classified corridor.
        def area_pct(state):
            return 100.0 * state_area.get(state, 0.0) / total_area if total_area > 0.0 else 0.0

        # The code defines preserved_area via final SF condition only. This
        # specific reporting quantity is not identical to total age-resolved area.
        preserved_area = sum(record["area"] for record in records.values() if record["fp_stab"] == 1)
        rows = []

        # add: Append a reach metric with units, weighting and interpretive definition.
        def add(metric_id, metric, value, unit, weighting, definition):
            rows.append({
                "METRIC_ID": metric_id,
                "METRIC": metric,
                "VALUE": value,
                "UNIT": unit,
                "WEIGHTING": weighting,
                "DEFINITION": definition,
            })

        add("feature_count", "Assemblage unit count", float(len(records)), "count", "none", "Number of spatial assemblage units written.")
        add("total_area", "Total analysis area", total_area_km2, "km2", "none", "Total polygon area after conversion from CRS map units.")
        add("analysis_start", "Analysis start year", float(analysis_start_date.year), "year", "none", "Earliest valid Period_i date.")
        add("analysis_end", "Analysis end year", float(analysis_end_date.year), "year", "none", "Common endpoint used for elapsed-year metrics.")
        add("analysis_duration", "Observed analysis duration", self._years_between(analysis_start_date, analysis_end_date), "years", "none", "Elapsed time between earliest Period_i date and common endpoint.")
        # AD / DS / SF extents are the final authoritative 4a states weighted by
        # polygon area, not physical erosion area per observation interval.
        add("active_extent", "Active-Domain Extent", area_pct("active_domain"), "percent_area", "area", "Final-state area; Module 4a final state is preferred over sparse EA support.")
        add("storage_extent", "Depositional Storage Extent", area_pct("depositional_storage"), "percent_area", "area", "Final-state area; Module 4a final state is preferred over sparse EA support.")
        add("stabilised_extent", "Stabilised Floodplain Extent", area_pct("stabilised_floodplain"), "percent_area", "area", "Final-state area from authoritative Module 4a v10.9 FINAL_ONTO_STATE.")
        add("unresolved_extent", "Unresolved Extent", area_pct("unresolved"), "percent_area", "area", "Area lacking a resolved Module 4a final state and lacking final-timestep EA support.")
        add("preserved_area", "Preserved Surface Area", 100.0 * preserved_area / total_area if total_area > 0.0 else 0.0, "percent_area", "area", "Area with FP_STAB_4D = 1.")
        add("shannon", "State Diversity (Shannon H)", self._weighted_mean(records, "shannon"), "index", "area", "Area-weighted Shannon diversity from the Module 4a ONTO_STATE_i history.")
        add("shannon_norm", "Normalised State Diversity", self._weighted_mean(records, "h_norm"), "index_0_1", "area", "Area-weighted ONTO_STATE_i Shannon H divided by ln(3).")
        add("richness", "Mean State Richness", self._weighted_mean(records, "richness"), "states", "area", "Area-weighted number of recognised states in the Module 4a ONTO_STATE_i history.")
        # Event episodes and persistence refer to mapped disturbance evidence;
        # Shannon values refer instead to the interpreted three-state history.
        add("episodes", "Mean Disturbance Episodes", self._weighted_mean(records, "n_episodes"), "episodes", "area", "Area-weighted disturbance runs across all known event-opportunity intervals; outside EA support is a known non-event.")
        add("persistence", "Mean Persistence", self._weighted_mean(records, "persistence_years"), "years", "area", "Elapsed persistence since last mapped disturbance, restricted to units with a resolved final state.")
        add("preserved_persistence", "Mean Preserved-Surface Persistence", self._weighted_mean(records, "persistence_years", lambda record: record["fp_stab"] == 1), "years", "area", "Persistence for units with FP_STAB_4D = 1.")
        add("max_persistence", "Maximum Persistence", max_persistence, "years", "none", "Maximum non-null PERSIST_YRS_4D.")
        add("reworking_rate", "Reworking Rate", self._weighted_mean(records, "disturbance_frequency"), "proportion", "area", "Area-weighted disturbance frequency across known event opportunities, including outside-EA-support intervals as non-events.")
        add("ea_conditional_reworking", "Conditional EA-Support Disturbance Frequency", self._weighted_mean(records, "ea_conditional_frequency"), "proportion", "area", "Area-weighted disturbance frequency conditional on the unit lying inside pairwise EA support.")
        add("local_reworking", "Mean Local Reworking Rate", self._weighted_mean(records, "local_disturbance_frequency"), "proportion", "area", "Neighbourhood average of all-known-opportunity DIST_FREQ_4D.")
        add("ea_support_fraction", "Mean EA Support Fraction", self._weighted_mean(records, "ea_support_fraction"), "proportion", "area", "Area-weighted fraction of timesteps inside the intentional current/previous-channel EA footprint.")
        add("outside_ea_fraction", "Mean Outside-EA-Support Fraction", self._weighted_mean(records, "outside_ea_fraction"), "proportion", "area", "Area-weighted fraction of blank/none/null/nan EA_Class_i values interpreted as outside pairwise EA support.")
        add("event_observation_fraction", "Mean Event-Opportunity Fraction", self._weighted_mean(records, "event_observation_fraction"), "proportion", "area", "Fraction of Module 4a timesteps included in disturbance calculations; v10.9 uses the complete timestep sequence.")
        add("background_valid_fraction", "Mean Validated-Background Fraction", self._weighted_mean(records, "bg_valid_fraction"), "proportion", "area", "Area-weighted fraction of timesteps represented by an explicit or assumed Module 4a background-floodplain history.")
        add("state_observation_fraction", "Mean Resolved-State Fraction", self._weighted_mean(records, "state_observation_fraction"), "proportion", "area", "Area-weighted fraction of recognised Module 4a ONTO_STATE_i values.")
        add("inactive_fraction", "Mean Explicit-Inactive Fraction", self._weighted_mean(records, "inactive_fraction"), "proportion", "area", "Area-weighted fraction explicitly coded inactive; not treated as outside support.")
        add("unknown_assignments", "Unknown Class Assignments", float(unknown_total), "count", "none", "Total non-empty unrecognised EA_Class_i values.")
        add("persistence_threshold", "Persistence Threshold", persistence_threshold, "years", "none", "Threshold used only to describe persistent versus recent floodplain condition; it does not reclassify the v10.9 final state.")
        add("state_change", "Endpoint-State Disagreement Area", 100.0 * changed_area / total_area if total_area > 0.0 else 0.0, "percent_area", "area", "Area where final ONTO_STATE_i disagrees with Module 4a v10.9 FINAL_ONTO_STATE; expected to be approximately zero.")
        add("shannon_difference", "Mean Normalised-Shannon Difference", self._weighted_mean(records, "h_norm_diff"), "index", "area", "H_NORM_4D minus Module 4a ASM_H_NORM; should be approximately zero when ONTO_STATE_i is complete.")
        add("event_count_difference", "Mean Event-Count Difference", self._weighted_mean(records, "n_events_diff"), "events", "area", "Recalculated event count minus Module 4a N_EVENTS.")
        add("episode_count_difference", "Mean Episode-Count Difference", self._weighted_mean(records, "n_episodes_diff"), "episodes", "area", "Recalculated episode count minus Module 4a N_EPISODES.")
        add("persistence_difference", "Mean Persistence Difference", self._weighted_mean(records, "since_disturb_diff_years"), "years", "area", "Recalculated persistence minus Module 4a SINCE_DISTURB_YR.")
        return rows

    # _build_class_rows: Aggregate counts/area by final state, floodplain condition and activity class.
    @staticmethod
    # The class summary includes several alternative descriptive dimensions.
    # Do not sum percentages across dimensions as if classes were disjoint.
    def _build_class_rows(records, total_area):
        dimensions = [
            ("final_state", "FINAL_STATE_4D"),
            ("floodplain_condition", "FP_COND_4D"),
            ("activity", "ACTIVITY_CL_R"),
            ("temporal_structure", "STRUCTURE_CL_R"),
            ("local_activity", "LOCAL_ACTIVITY_CL"),
            ("state_diversity", "H_CLASS_4D"),
        ]

        summaries = defaultdict(lambda: {"count": 0, "area": 0.0})
        for record in records.values():
            for key, label in dimensions:
                class_value = {
                    "final_state": record["final_state"],
                    "floodplain_condition": record["fp_condition"],
                    "activity": record["activity_class"],
                    "temporal_structure": record["structure_class"],
                    "local_activity": record["local_activity_class"],
                    "state_diversity": record["h_class"],
                }[key]
                summary = summaries[(label, class_value)]
                summary["count"] += 1
                summary["area"] += record["area"]

        rows = []
        for (dimension, class_value), summary in sorted(summaries.items()):
            rows.append(
                {
                    "DIMENSION": dimension,
                    "CLASS": class_value,
                    "FEATURES": summary["count"],
                    "AREA_MAP2": summary["area"],
                    "AREA_KM2": summary["area_km2"] if "area_km2" in summary else None,
                    "AREA_PCT": 100.0 * summary["area"] / total_area if total_area > 0.0 else 0.0,
                }
            )
        return rows

    # _build_assignment_audit_rows: Build three complementary EA-support audits using event, non-event,
    # background, unknown and outside-support categories.
    # AREA_TIME sums polygon area across timesteps, not across years.
    # Raw EA classes and interpreted ONTO_STATE_i are deliberately both
    # retained in audit records to diagnose source/ontology mismatches.
    def _build_assignment_audit_rows(
        self,
        step_class_stats,
        reach_class_stats,
        step_category_stats,
        ea_pairs,
        period_date_by_step,
        total_area,
        area_to_km2,
        feature_count,
    ):
        pair_by_step = {step: (ea_field, period_field) for step, ea_field, period_field in ea_pairs}
        period_end = {step: (value.isoformat() if value is not None else "") for step, value in period_date_by_step.items()}

        support_statuses = {"event", "valid_non_event"}
        background_statuses = {"validated_background"}
        state_observed_statuses = {"event", "valid_non_event", "validated_background"}
        # Every Module 4a timestep is treated as an event opportunity, so labels
        # outside direct EA coverage contribute as known non-event observations.
        # Module 4a v10.9 treats every timestep as an event opportunity;
        # unresolved/outside-support classes are non-events rather than dropped rows.
        event_observed_statuses = {
            "event", "valid_non_event", "validated_background",
            "outside_support", "unresolved", "unknown"
        }

        step_class_rows = []
        for key, summary in sorted(step_class_stats.items(), key=lambda item: (item[0][0], item[0][1], item[0][2], item[0][3])):
            step, raw_class, status, category, interpreted_state = key
            ea_field, period_field = pair_by_step.get(step, ("", ""))
            area = summary["area"]
            step_class_rows.append({
                "STEP": step,
                "EA_FIELD": ea_field,
                "PERIOD_FIELD": period_field,
                "PERIOD_END": period_end.get(step, ""),
                "RAW_CLASS": raw_class,
                "STATUS": status,
                "SUPPORT_CATEGORY": category,
                "INTERPRETED_STATE": interpreted_state,
                "EA_SUPPORT_FLAG": 1 if status in support_statuses else 0,
                "BACKGROUND_VALID_FLAG": 1 if status in background_statuses else 0,
                "STATE_OBS_FLAG": 1 if status in state_observed_statuses else 0,
                "EVENT_OBS_FLAG": 1 if status in event_observed_statuses else 0,
                "ASSIGNMENTS": summary["assignments"],
                "AREA_MAP2": area,
                "AREA_KM2": area * area_to_km2,
                "AREA_PCT_STEP": 100.0 * area / total_area if total_area > 0.0 else 0.0,
            })

        # Total area-time equals the sum of polygon areas per observation step.
        # A temporal gap between steps does not multiply its contribution.
        total_steps = len(ea_pairs)
        total_assignments = feature_count * total_steps
        total_area_time = total_area * total_steps
        reach_rows = []
        for key, summary in sorted(reach_class_stats.items(), key=lambda item: (item[0][2], item[0][0], item[0][1], item[0][3])):
            raw_class, status, category, interpreted_state = key
            area_time = summary["area"]
            reach_rows.append({
                "RAW_CLASS": raw_class,
                "STATUS": status,
                "SUPPORT_CATEGORY": category,
                "INTERPRETED_STATE": interpreted_state,
                "EA_SUPPORT_FLAG": 1 if status in support_statuses else 0,
                "BACKGROUND_VALID_FLAG": 1 if status in background_statuses else 0,
                "STATE_OBS_FLAG": 1 if status in state_observed_statuses else 0,
                "EVENT_OBS_FLAG": 1 if status in event_observed_statuses else 0,
                "ASSIGNMENTS": summary["assignments"],
                "ASSIGNMENT_PCT": 100.0 * summary["assignments"] / total_assignments if total_assignments > 0 else 0.0,
                "AREA_TIME_MAP2": area_time,
                "AREA_TIME_KM2": area_time * area_to_km2,
                "AREA_TIME_PCT": 100.0 * area_time / total_area_time if total_area_time > 0.0 else 0.0,
            })

        # The support categories form an exhaustive timestep QA partition.
        # Warnings identify nonclosure due to incomplete or inconsistent inputs.
        categories = (
            "event", "supported_non_event", "validated_background", "outside_ea_support",
            "explicit_inactive", "no_observation", "processing_unresolved", "unknown",
        )
        step_status_rows = []
        for step, ea_field, period_field in ea_pairs:
            stats = {category: step_category_stats.get((step, category), {"assignments": 0, "area": 0.0}) for category in categories}
            ea_support_assignments = stats["event"]["assignments"] + stats["supported_non_event"]["assignments"]
            background_valid_assignments = stats["validated_background"]["assignments"]
            state_obs_assignments = ea_support_assignments + background_valid_assignments
            event_obs_assignments = feature_count

            # pct: Convert summed category area to within-step percentage.
            def pct(category):
                area = stats[category]["area"]
                return 100.0 * area / total_area if total_area > 0.0 else 0.0

            support_pct = pct("event") + pct("supported_non_event")
            background_pct = pct("validated_background")
            state_obs_pct = support_pct + background_pct
            outside_pct = pct("outside_ea_support")
            step_status_rows.append({
                "STEP": step,
                "EA_FIELD": ea_field,
                "PERIOD_FIELD": period_field,
                "PERIOD_END": period_end.get(step, ""),
                "TOTAL_ASSIGNMENTS": feature_count,
                "EA_SUPPORT_ASSIGNMENTS": ea_support_assignments,
                "BACKGROUND_VALID_ASSIGNMENTS": background_valid_assignments,
                "STATE_OBS_ASSIGNMENTS": state_obs_assignments,
                "EVENT_OBS_ASSIGNMENTS": event_obs_assignments,
                "EA_SUPPORT_AREA_PCT": support_pct,
                "BACKGROUND_VALID_AREA_PCT": background_pct,
                "STATE_OBS_AREA_PCT": state_obs_pct,
                "OUTSIDE_EA_AREA_PCT": outside_pct,
                "EVENT_OBS_AREA_PCT": 100.0,
                "INACTIVE_AREA_PCT": pct("explicit_inactive"),
                "NO_OBS_AREA_PCT": pct("no_observation"),
                "PROC_UNRES_AREA_PCT": pct("processing_unresolved"),
                "UNKNOWN_AREA_PCT": pct("unknown"),
                "EVENT_AREA_PCT": pct("event"),
                "SUPPORTED_NONEVENT_AREA_PCT": pct("supported_non_event"),
            })
        return step_class_rows, reach_rows, step_status_rows

    # _write_rows_to_csv: Write a fixed ordered schema and preserve blank missing values.
    # CSV outputs are standalone copies of the GeoPackage tabular summaries;
    # UTF-8 with BOM improves compatibility with common spreadsheet readers.
    def _write_rows_to_csv(self, path, field_names, rows):
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=field_names, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({name: self._value_for_csv(row.get(name)) for name in field_names})

    # _write_rows_to_gpkg_table: Persist a no-geometry tabular layer into the multi-layer GeoPackage.
    def _write_rows_to_gpkg_table(self, gpkg_path, layer_name, specs, rows, context):
        fields = self._build_fields(specs)
        writer = self._create_writer(
            gpkg_path,
            layer_name,
            fields,
            QgsWkbTypes.NoGeometry,
            QgsCoordinateReferenceSystem(),
            context,
            overwrite_file=False,
        )
        field_names = [field.name() for field in fields]
        for row in rows:
            feature = QgsFeature(fields)
            feature.setAttributes([row.get(name) for name in field_names])
            if not writer.addFeature(feature, QgsFeatureSink.FastInsert):
                del writer
                raise QgsProcessingException(
                    f"Failed writing a row to GeoPackage table {layer_name}."
                )
        del writer

    # MAIN EXECUTION: first derive metrics without changing planar geometry;
    # then calculate local spatial context and finally write outputs.
    # ------------------------------------------------------------------
    # Main algorithm
    # ------------------------------------------------------------------
    # processAlgorithm: Orchestrate input validation, historical reconstruction, local metrics,
    # spatial output and six accompanying tabular products.
    # The algorithm is a descriptive post-processor, not a model fit.
    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        radius = self.parameterAsDouble(parameters, self.RADIUS, context)
        min_area = self.parameterAsDouble(parameters, self.MIN_AREA, context)
        requested_end_year = self.parameterAsInt(parameters, self.END_YEAR, context)
        persistence_threshold = self.parameterAsDouble(
            parameters, self.PERSISTENCE_YEARS, context
        )
        reworked_episode_threshold = self.parameterAsInt(
            parameters, self.REWORKED_EPISODES, context
        )
        gpkg_path = self._normalise_gpkg_path(
            self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context)
        )
        table_folder = self.parameterAsString(parameters, self.TABLE_FOLDER, context)
        table_folder = os.path.abspath(str(table_folder).strip())

        # Require projected polygons because radius/distance and planar area are
        # meaningless in unconverted latitude/longitude degrees.
        if layer is None or not layer.isValid():
            raise QgsProcessingException("Input layer is invalid.")
        if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
            raise QgsProcessingException("Input must be a polygon layer.")
        if not layer.crs().isValid():
            raise QgsProcessingException("Input layer has no valid CRS.")
        if layer.crs().isGeographic():
            raise QgsProcessingException(
                "Input must use a projected CRS. Radius, area, and local metrics "
                "cannot be interpreted safely in latitude/longitude coordinates."
            )

        # Protection against accidentally deleting/replacing the authoritative
        # upstream 4a database through an identical destination path.
        input_source_path = str(layer.source() or "").split("|", 1)[0]
        if input_source_path:
            input_source_path = os.path.normcase(os.path.abspath(input_source_path))
            if input_source_path == os.path.normcase(os.path.abspath(gpkg_path)):
                raise QgsProcessingException(
                    "Output GeoPackage must differ from the Module 4a input GeoPackage. "
                    "The output writer replaces its destination and must never target "
                    "Assemblage_Units_FULL_ATTRS in place."
                )

        os.makedirs(os.path.dirname(gpkg_path), exist_ok=True)
        os.makedirs(table_folder, exist_ok=True)

        names = self._field_names(layer)
        name_lookup = {name.lower(): name for name in names}

        # Only valid matched EA_Class_i / Period_i columns are scanned. Missing
        # steps are warned about but do not automatically abort the run.
        ea_pairs = []
        for actual_name in names:
            match = re.match(r"^EA_Class_(\d+)$", actual_name, re.IGNORECASE)
            if not match:
                continue
            step_index = int(match.group(1))
            period_actual = name_lookup.get(f"period_{step_index}".lower())
            if period_actual:
                ea_pairs.append((step_index, actual_name, period_actual))

        ea_pairs.sort(key=lambda item: item[0])
        if not ea_pairs:
            layer_name = layer.name() or "selected layer"
            raise QgsProcessingException(
                f"No matching EA_Class_i / Period_i pairs were found in '{layer_name}'. "
                "For Module 4a v10.9, select Assemblage_Units_FULL_ATTRS. "
                "Assemblage_Display, Assemblage_StatsFabric, and "
                "Assemblage_Dissolved do not retain the complete histories."
            )

        step_indices = [item[0] for item in ea_pairs]
        expected_indices = list(range(step_indices[0], step_indices[-1] + 1))
        missing_indices = sorted(set(expected_indices) - set(step_indices))
        if missing_indices:
            feedback.reportError(
                "[4d QA] Non-contiguous timestep fields detected; missing steps: "
                + ", ".join(str(value) for value in missing_indices)
            )

        feedback.pushInfo(
            f"[4d] Module 4a v10.9 history detected: {len(ea_pairs)} EA_Class_i / Period_i pairs "
            f"(steps {step_indices[0]}-{step_indices[-1]})."
        )
        feedback.pushInfo(
            f"[4d] Input: {layer.name()} | features: {layer.featureCount():,} | "
            f"CRS: {layer.crs().authid() or layer.crs().description()}"
        )

        # --------------------------------------------------------------
        # Resolve one global Period_i date per step.
        # --------------------------------------------------------------
        # Resolve one date per observation step by scanning the source layer;
        # the memory cost is mainly per-feature pass, not date-array storage.
        period_dates_by_step = {step: set() for step, _, _ in ea_pairs}
        total_features = max(1, layer.featureCount())

        for counter, feature in enumerate(layer.getFeatures()):
            self._cancel_if_requested(feedback)
            for step_index, _, period_field in ea_pairs:
                parsed_date = self._parse_period_end_date(feature[period_field])
                if parsed_date is not None:
                    period_dates_by_step[step_index].add(parsed_date)
            if counter % 5000 == 0:
                feedback.setProgress(int(10.0 * counter / total_features))

        # If dates disagree between features for a step, the latest is used and
        # QA reports the conflict rather than redefining the chronology.
        period_date_by_step = {}
        for step_index, _, period_field in ea_pairs:
            values = period_dates_by_step.get(step_index, set())
            if not values:
                feedback.reportError(
                    f"[4d QA] No parseable date found for step {step_index} ({period_field})."
                )
                period_date_by_step[step_index] = None
                continue
            if len(values) > 1:
                feedback.reportError(
                    f"[4d QA] Conflicting dates in {period_field}: "
                    f"{sorted(value.isoformat() for value in values)}. Using the latest."
                )
            period_date_by_step[step_index] = max(values)

        observed_dates = [value for value in period_date_by_step.values() if value is not None]
        if not observed_dates:
            raise QgsProcessingException("No parseable dates were found in Period_i fields.")

        # The earliest Period_i date is an interval endpoint and can postdate T0.
        # It should not be labelled the earliest channel observation without QA.
        analysis_start_date = min(observed_dates)
        observed_end_date = max(observed_dates)
        analysis_end_date = (
            self._date_with_year(observed_end_date, requested_end_year)
            if requested_end_year > 0
            else observed_end_date
        )
        if analysis_end_date < observed_end_date:
            raise QgsProcessingException(
                f"Requested analysis endpoint {analysis_end_date.isoformat()} is earlier "
                f"than the latest observed Period_i date {observed_end_date.isoformat()}."
            )

        # Elapsed duration for each step is based on adjacent endpoint dates.
        # The first observed step has zero duration in this implementation.
        step_duration_years = {}
        previous_date = None
        for step_index in step_indices:
            current_date = period_date_by_step.get(step_index)
            if current_date is None:
                step_duration_years[step_index] = 0.0
            elif previous_date is None:
                step_duration_years[step_index] = 0.0
                previous_date = current_date
            else:
                step_duration_years[step_index] = self._years_between(previous_date, current_date) or 0.0
                previous_date = current_date

        feedback.pushInfo(
            f"[4d] Elapsed-year analysis: {analysis_start_date.isoformat()} to "
            f"{analysis_end_date.isoformat()} | persistence threshold={persistence_threshold:g} years."
        )

        # Area-to-km2 conversion depends on the CRS distance-unit conversion.
        # Projected non-metre CRS are supported if QGIS resolves unit metadata.
        try:
            linear_to_metres = QgsUnitTypes.fromUnitToUnitFactor(
                layer.crs().mapUnits(), QgsUnitTypes.DistanceMeters
            )
            if not linear_to_metres or linear_to_metres <= 0:
                linear_to_metres = 1.0
        except Exception:
            linear_to_metres = 1.0
            feedback.reportError(
                "[4d QA] CRS unit conversion to metres could not be resolved; "
                "AREA_KM2 assumes map units are metres."
            )
        area_to_km2 = (linear_to_metres * linear_to_metres) / 1000000.0

        id_field = self._discover_unit_id_field(layer)
        if id_field:
            feedback.pushInfo(f"[4d] Per-unit table identifier: {id_field}")
        else:
            feedback.pushInfo("[4d] No stable unit-ID field found; using provider feature IDs.")

        # Source 4a ONTO_STATE_i is indispensable for state composition;
        # EA_Class_i cannot provide a methodologically equivalent replacement.
        # Module 4a v10.9 state histories, T0 provenance, and source-QA fields.
        onto_field_by_step = {
            step_index: name_lookup.get(f"onto_state_{step_index}")
            for step_index in step_indices
        }
        onto_fields_present = [name for name in onto_field_by_step.values() if name]
        if len(onto_fields_present) == len(step_indices):
            use_onto_history = True
            feedback.pushInfo(
                f"[4d] Using {len(onto_fields_present)} Module 4a ONTO_STATE_i fields "
                "for state composition, diversity, and transitions."
            )
        elif not onto_fields_present:
            raise QgsProcessingException(
                "No ONTO_STATE_i fields found. Module 4d v3.5 requires the full "
                "Module 4a v10.9 Assemblage_Units_FULL_ATTRS history and will not "
                "reconstruct state metrics from EA_Class_i alone."
            )
        else:
            missing_onto = [
                str(step) for step, field_name in onto_field_by_step.items() if not field_name
            ]
            raise QgsProcessingException(
                "Partial ONTO_STATE_i history detected. Missing steps: "
                + ", ".join(missing_onto)
            )

        # These upstream provenance and summary fields support independent QA of
        # the recalculated metric streams and origin/censoring assumptions.
        source_h_norm_field = name_lookup.get("asm_h_norm")
        source_final_raw_field = name_lookup.get("final_onto_raw")
        source_init_state_field = name_lookup.get("init_state")
        source_init_prov_field = name_lookup.get("init_prov")
        source_init_context_field = name_lookup.get("init_context")
        source_left_cens_field = name_lookup.get("left_cens")
        source_age_censored_field = name_lookup.get("age_censored")
        source_sf_prov_field = name_lookup.get("sf_prov")
        source_surface_age_type_field = name_lookup.get("surface_age_type")
        source_storage_age_field = name_lookup.get("storage_age_yr")
        source_storage_age_cens_field = name_lookup.get("storage_age_cens")
        source_stab_years_field = name_lookup.get("asm_stab_years")
        source_stab_mode_field = name_lookup.get("asm_stab_mode")
        # Use FINAL_ONTO_STATE first, with specifically supported aliases only;
        # do not reconstruct final state solely from last mapped EA process.
        source_final_state_field = None
        for candidate in ("final_onto_state", "final_state_corr", "final_state"):
            actual = name_lookup.get(candidate)
            if actual:
                source_final_state_field = actual
                break
        source_n_events_field = name_lookup.get("n_events")
        source_n_episodes_field = name_lookup.get("n_episodes")
        source_since_disturb_field = name_lookup.get("since_disturb_yr")
        source_n_assigned_field = name_lookup.get("n_assigned")
        source_bg_fp_field = name_lookup.get("bg_fp")
        source_bg_source_field = name_lookup.get("bg_source")
        source_support_class_field = name_lookup.get("support_cl")

        if source_final_raw_field:
            feedback.pushInfo(f"[4d] Raw endpoint-state source: {source_final_raw_field}")
        else:
            feedback.reportError(
                "[4d QA] FINAL_ONTO_RAW is absent. Raw endpoint state will fall back "
                "to the final ONTO_STATE_i value."
            )
        if source_final_state_field:
            feedback.pushInfo(
                f"[4d] Module 4a authoritative final-state source: {source_final_state_field}"
            )
        else:
            feedback.reportError(
                "[4d QA] No Module 4a interpreted final-state field found."
            )
        if source_n_assigned_field:
            feedback.pushInfo(
                f"[4d] Direct EA-support count source: {source_n_assigned_field}"
            )

        # Strict requirement for T0 INIT_STATE prevents incorrect omission of
        # first observed transitions from the historical summary.
        if not source_final_state_field:
            raise QgsProcessingException(
                "Module 4a v10.9 FINAL_ONTO_STATE (or supported final-state alias) is required "
                "for authoritative endpoint-state metrics."
            )
        if not source_init_state_field:
            raise QgsProcessingException(
                "Module 4a v10.9 INIT_STATE is required so T0-to-first-step transitions are counted correctly."
            )
        feedback.pushInfo(
            f"[4d] v10.9 T0 transition seed: {source_init_state_field}; final state: {source_final_state_field}."
        )
        if source_stab_years_field:
            feedback.pushInfo(f"[4d] Module 4a stabilisation threshold field: {source_stab_years_field}")
        if source_stab_mode_field:
            feedback.pushInfo(f"[4d] Module 4a stabilisation mode field: {source_stab_mode_field}")

        analysis_years = self._years_between(analysis_start_date, analysis_end_date)
        endpoint_extension_years = self._years_between(observed_end_date, analysis_end_date) or 0.0

        # Pass 1 builds in-memory per-unit records and point locations; performance
        # is sensitive to planar fabric feature count and chronicle width.
        # --------------------------------------------------------------
        # First analytical pass: Module 4a-compatible event and state metrics.
        # --------------------------------------------------------------
        records = {}
        representative_points = {}
        point_index = QgsSpatialIndex()
        unknown_value_counts = defaultdict(int)
        step_class_stats = defaultdict(lambda: {"assignments": 0, "area": 0.0})
        reach_class_stats = defaultdict(lambda: {"assignments": 0, "area": 0.0})
        step_category_stats = defaultdict(lambda: {"assignments": 0, "area": 0.0})

        for counter, feature in enumerate(layer.getFeatures()):
            self._cancel_if_requested(feedback)

            geometry = feature.geometry()
            area = geometry.area() if geometry and not geometry.isEmpty() else 0.0
            area_km2 = area * area_to_km2

            event_sequence = []
            event_step_indices = []
            states_all = []
            recognised_states = []

            # T0 INIT_STATE enters the transition sequence but not Shannon occupancy;
            # LEFT_CENS and related fields preserve observation-window provenance.
            init_state_upper = self._normalise_onto_history_state(feature[source_init_state_field])
            init_state = self._state_label(init_state_upper)
            init_prov = str(feature[source_init_prov_field] or "unknown") if source_init_prov_field else "unknown"
            init_context = str(feature[source_init_context_field] or "unknown") if source_init_context_field else "unknown"
            left_censored = int(self._safe_float(feature[source_left_cens_field]) or 0) if source_left_cens_field else 0
            age_censored = int(self._safe_float(feature[source_age_censored_field]) or 0) if source_age_censored_field else 0
            sf_prov = str(feature[source_sf_prov_field] or "not_available") if source_sf_prov_field else "not_available"
            surface_age_type = str(feature[source_surface_age_type_field] or "not_available") if source_surface_age_type_field else "not_available"
            storage_age_years = self._safe_float(feature[source_storage_age_field]) if source_storage_age_field else None
            storage_age_censored = int(self._safe_float(feature[source_storage_age_cens_field]) or 0) if source_storage_age_cens_field else 0
            n_unresolved = 0
            n_unknown = 0
            n_inactive = 0
            derived_direct_support = 0

            # BG_FP indicates validated background floodplain, with upstream fill
            # replacing raw timestep label contents in some units.
            bg_valid = (
                bool(int(self._safe_float(feature[source_bg_fp_field]) or 0))
                if source_bg_fp_field
                else False
            )
            bg_source = (
                str(feature[source_bg_source_field] or "none")
                if source_bg_source_field
                else ("module4a_background" if bg_valid else "none")
            )
            support_class = (
                str(feature[source_support_class_field] or "")
                if source_support_class_field
                else ""
            )

            # At each timestep, track raw EA process evidence and the independently
            # interpreted 4a state side-by-side.
            for step_index, ea_field, _ in ea_pairs:
                status, cleaned_value, ea_state = self._class_status(feature[ea_field])
                if use_onto_history:
                    state = self._normalise_onto_history_state(
                        feature[onto_field_by_step[step_index]]
                    )
                else:
                    state = ea_state

                # A validated background flag changes the audit class to background but
                # does not on its own alter a recognised ONTO_STATE_i sequence here.
                if bg_valid:
                    audit_status = "validated_background"
                    category = "validated_background"
                else:
                    audit_status = status
                    category = self._assignment_audit_category(cleaned_value, status)

                raw_label = self._audit_raw_label(cleaned_value)
                interpreted_state = self._audit_state_label(state)
                states_all.append(state)
                if state != "UNRESOLVED":
                    recognised_states.append(state)

                step_class_key = (
                    step_index, raw_label, audit_status, category, interpreted_state
                )
                reach_class_key = (
                    raw_label, audit_status, category, interpreted_state
                )
                step_class_stats[step_class_key]["assignments"] += 1
                step_class_stats[step_class_key]["area"] += area
                reach_class_stats[reach_class_key]["assignments"] += 1
                reach_class_stats[reach_class_key]["area"] += area
                step_category_stats[(step_index, category)]["assignments"] += 1
                step_category_stats[(step_index, category)]["area"] += area

                if category == "explicit_inactive":
                    n_inactive += 1
                if status == "unresolved":
                    n_unresolved += 1
                elif status == "unknown":
                    n_unknown += 1
                    unknown_value_counts[cleaned_value] += 1

                if status in {"event", "valid_non_event"}:
                    derived_direct_support += 1

                # Disturbance counts erosion/deposition event classes only, including island
                # aliases; stable or active occupation without process event is not enough.
                is_event = status == "event"
                # Module 4a v10.9 uses the complete chronological sequence:
                # unresolved/outside-support rows are retained as non-events.
                event_sequence.append((step_index, is_event))
                if is_event:
                    event_step_indices.append(step_index)

            # N_ASSIGNED is preferred over reconstructed support count because
            # Module 4a background fill may obscure original raw EA assignments.
            n_steps = len(ea_pairs)
            if source_n_assigned_field:
                source_n_assigned = int(
                    max(0, min(n_steps, self._safe_float(feature[source_n_assigned_field]) or 0))
                )
                n_ea_support = source_n_assigned
            else:
                n_ea_support = derived_direct_support
            n_outside_ea = max(0, n_steps - n_ea_support)
            n_bg_valid = n_steps if bg_valid else 0
            # The event-opportunity denominator is all temporal steps, whereas state
            # occupancy separately excludes unresolved ONTO_STATE_i categories.
            n_state_observations = len(recognised_states)
            n_event_observations = n_steps
            n_events = len(event_step_indices)

            ea_support_fraction = float(n_ea_support) / float(n_steps) if n_steps > 0 else 0.0
            outside_ea_fraction = float(n_outside_ea) / float(n_steps) if n_steps > 0 else 0.0
            bg_valid_fraction = float(n_bg_valid) / float(n_steps) if n_steps > 0 else 0.0
            state_observation_fraction = (
                float(n_state_observations) / float(n_steps) if n_steps > 0 else 0.0
            )
            event_observation_fraction = 1.0 if n_steps > 0 else 0.0
            inactive_fraction = float(n_inactive) / float(n_steps) if n_steps > 0 else 0.0
            # DIST_FREQ and EA_COND_FREQ differ by denominator; neither is an
            # elapsed person-place-year or hazard-rate calculation.
            disturbance_frequency = float(n_events) / float(n_steps) if n_steps > 0 else None
            ea_conditional_frequency = (
                float(n_events) / float(n_ea_support) if n_ea_support > 0 else None
            )

            (
                n_episodes,
                max_quiet_steps,
                longest_event_run,
                observed_first_last_span,
                disturbance_density,
            ) = self._run_metrics(event_sequence)

            first_dist_step = event_step_indices[0] if event_step_indices else None
            last_dist_step = event_step_indices[-1] if event_step_indices else None
            original_step_span = (
                last_dist_step - first_dist_step + 1
                if first_dist_step is not None and last_dist_step is not None
                else 0
            )

            # Entropy uses recognised AD/DS/SF observations. Summed occupancy
            # fractions can be less than 1 when some steps are unresolved.
            counts, shannon, h_norm, richness, h_class = self._shannon_from_states(
                recognised_states
            )
            n_state_supported = sum(counts.values())
            active_frequency = (
                float(counts["ACTIVE_DOMAIN"]) / float(n_steps) if n_steps > 0 else None
            )
            storage_frequency = (
                float(counts["DEPOSITIONAL_STORAGE"]) / float(n_steps) if n_steps > 0 else None
            )
            stabilised_frequency = (
                float(counts["STABILISED_FLOODPLAIN"]) / float(n_steps) if n_steps > 0 else None
            )

            # Prepending the T0 state permits first interval transitions to count,
            # without falsely treating the seed as another measured period.
            transition_states = [init_state_upper] + states_all
            (
                n_reactivation,
                n_storage_events,
                n_stabilisation_events,
                n_storage_reworking_events,
                n_fp_storage_events,
                n_transitions,
            ) = self._transition_counts(transition_states)

            # Endpoint state is taken from v10.9 when available; fallback on final
            # ONTO_STATE_i is explicitly recorded if the source is unresolved.
            final_step_state = states_all[-1] if states_all else "UNRESOLVED"
            final_step_raw = self._state_label(final_step_state)
            source_raw = (
                self._normalise_final_state(feature[source_final_raw_field])
                if source_final_raw_field
                else "unresolved"
            )
            source_interpreted_state = (
                self._normalise_final_state(feature[source_final_state_field])
                if source_final_state_field
                else "unresolved"
            )
            if source_raw != "unresolved":
                final_raw = source_raw
            else:
                final_raw = final_step_raw

            if source_interpreted_state != "unresolved":
                authoritative_final_state = source_interpreted_state
                final_source = "module4a_final_onto_state"
            elif final_step_raw != "unresolved":
                authoritative_final_state = final_step_raw
                final_source = "final_onto_timestep_fallback"
            else:
                authoritative_final_state = "unresolved"
                final_source = "unresolved"

            activity_class = self._activity_class(
                n_event_observations, n_events, disturbance_frequency
            )
            structure_class = self._structure_class(
                n_event_observations,
                n_events,
                n_episodes,
                max_quiet_steps,
                longest_event_run,
                disturbance_density,
            )

            # Point-on-surface yields a point inside each spatial unit for local
            # neighbourhood lookup; it is not a centreline or measured channel margin.
            representative_geometry = (
                geometry.pointOnSurface()
                if geometry and not geometry.isEmpty()
                else QgsGeometry()
            )

            source_h_norm = (
                self._safe_float(feature[source_h_norm_field])
                if source_h_norm_field
                else None
            )
            h_norm_diff = h_norm - source_h_norm if source_h_norm is not None else None

            # Periods are converted to elapsed years only for temporal descriptors;
            # observation-frequency metrics use counts rather than elapsed exposure.
            first_date = (
                period_date_by_step.get(first_dist_step)
                if first_dist_step is not None
                else None
            )
            last_date = (
                period_date_by_step.get(last_dist_step)
                if last_dist_step is not None
                else None
            )
            first_dist_year = first_date.year if first_date is not None else None
            last_dist_year = last_date.year if last_date is not None else None
            years_since_dist = (
                self._years_between(last_date, analysis_end_date)
                if last_date is not None
                else None
            )

            source_since_disturb_years = (
                self._safe_float(feature[source_since_disturb_field])
                if source_since_disturb_field
                else None
            )
            # The independent elapsed-since-disturbance calculation supports QA
            # against the v10.9 SINCE_DISTURB_YR metric.
            independent_since_disturb_years = None
            if authoritative_final_state != "unresolved":
                if last_date is not None:
                    independent_since_disturb_years = years_since_dist
                else:
                    independent_since_disturb_years = analysis_years

            # Unresolved final states cannot acquire a persistence duration or be
            # promoted into an SF condition from observation length alone.
            if authoritative_final_state == "unresolved":
                persistence_years = None
                persistence_basis = "no_resolved_final_state"
            elif source_since_disturb_years is not None:
                persistence_years = max(
                    0.0, source_since_disturb_years + endpoint_extension_years
                )
                persistence_basis = (
                    "module4a_since_disturb_yr_left_censored"
                    if age_censored else "module4a_since_disturb_yr"
                )
            elif independent_since_disturb_years is not None:
                persistence_years = independent_since_disturb_years
                persistence_basis = (
                    "since_last_disturbance"
                    if last_date is not None
                    else ("full_record_no_disturbance_left_censored" if age_censored else "full_record_no_disturbance")
                )
            else:
                persistence_years = None
                persistence_basis = "unresolved"

            disturbance_span_years = (
                self._years_between(first_date, last_date)
                if first_date is not None and last_date is not None
                else 0.0
            )

            # Quiet-year runs sum durations between observed consecutive endpoints
            # after a recorded event; gaps in numbered steps reset the run.
            max_quiet_years = 0.0
            quiet_years = 0.0
            event_seen = False
            previous_observed_step = None
            for observed_step_index, is_event in event_sequence:
                consecutive = (
                    previous_observed_step is not None
                    and observed_step_index == previous_observed_step + 1
                )
                if not consecutive:
                    quiet_years = 0.0
                if is_event:
                    if event_seen:
                        max_quiet_years = max(max_quiet_years, quiet_years)
                    event_seen = True
                    quiet_years = 0.0
                elif event_seen and consecutive:
                    quiet_years += step_duration_years.get(observed_step_index, 0.0)
                    max_quiet_years = max(max_quiet_years, quiet_years)
                previous_observed_step = observed_step_index

            # Descriptive FP condition depends on final authoritative state and
            # activity history; no state transition is altered.
            final_state, fp_condition, fp_stab, fp_recent, fp_reworked = (
                self._v109_state_and_condition(
                    authoritative_final_state,
                    persistence_years,
                    n_episodes,
                    persistence_threshold,
                    reworked_episode_threshold,
                )
            )

            state_changed = (
                1
                if source_interpreted_state != "unresolved"
                and final_step_raw != "unresolved"
                and source_interpreted_state != final_step_raw
                else 0
            )
            # Mismatch terms are meant to reveal discrepancies from the upstream
            # Module 4a reference, not justify overwriting it.
            source_n_events = (
                int(self._safe_float(feature[source_n_events_field]))
                if source_n_events_field
                and self._safe_float(feature[source_n_events_field]) is not None
                else None
            )
            source_n_episodes = (
                int(self._safe_float(feature[source_n_episodes_field]))
                if source_n_episodes_field
                and self._safe_float(feature[source_n_episodes_field]) is not None
                else None
            )
            n_events_diff = (
                n_events - source_n_events if source_n_events is not None else None
            )
            n_episodes_diff = (
                n_episodes - source_n_episodes
                if source_n_episodes is not None
                else None
            )
            since_disturb_diff_years = (
                independent_since_disturb_years
                - (source_since_disturb_years + endpoint_extension_years)
                if independent_since_disturb_years is not None
                and source_since_disturb_years is not None
                else None
            )

            # Full records are cached by provider feature ID for subsequent spatial
            # smoothing and one-pass output attribute writing.
            records[feature.id()] = {
                "unit_id": self._make_unit_id(feature, id_field),
                "n_steps": n_steps,
                "n_ea_support": n_ea_support,
                "n_outside_ea": n_outside_ea,
                "n_bg_valid": n_bg_valid,
                "n_state_observations": n_state_observations,
                "n_event_observations": n_event_observations,
                "n_unresolved": n_unresolved,
                "n_unknown": n_unknown,
                "n_inactive": n_inactive,
                "ea_support_fraction": ea_support_fraction,
                "outside_ea_fraction": outside_ea_fraction,
                "bg_valid_fraction": bg_valid_fraction,
                "state_observation_fraction": state_observation_fraction,
                "event_observation_fraction": event_observation_fraction,
                "inactive_fraction": inactive_fraction,
                "n_events": n_events,
                "disturbance_frequency": disturbance_frequency,
                "ea_conditional_frequency": ea_conditional_frequency,
                "n_episodes": n_episodes,
                "max_quiet_steps": max_quiet_steps,
                "max_quiet_years": max_quiet_years,
                "first_dist_step": first_dist_step,
                "last_dist_step": last_dist_step,
                "original_step_span": original_step_span,
                "disturbance_density": disturbance_density,
                "activity_class": activity_class,
                "structure_class": structure_class,
                "area": area,
                "area_km2": area_km2,
                "n_active": counts["ACTIVE_DOMAIN"],
                "n_storage": counts["DEPOSITIONAL_STORAGE"],
                "n_stabilised": counts["STABILISED_FLOODPLAIN"],
                "active_frequency": active_frequency,
                "storage_frequency": storage_frequency,
                "stabilised_frequency": stabilised_frequency,
                "state_basis": (
                    "module4a_onto_state_history"
                    if use_onto_history
                    else "ea_class_fallback"
                ),
                "n_reactivation": n_reactivation,
                "n_storage_events": n_storage_events,
                "n_stabilisation_events": n_stabilisation_events,
                "n_storage_reworking_events": n_storage_reworking_events,
                "n_fp_storage_events": n_fp_storage_events,
                "n_transitions": n_transitions,
                "final_raw": final_raw,
                "final_source": final_source,
                "init_state": init_state,
                "init_prov": init_prov,
                "init_context": init_context,
                "left_censored": left_censored,
                "age_censored": age_censored,
                "sf_prov": sf_prov,
                "surface_age_type": surface_age_type,
                "storage_age_years": storage_age_years,
                "storage_age_censored": storage_age_censored,
                "shannon": shannon,
                "h_norm": h_norm,
                "richness": richness,
                "h_class": h_class,
                "h_norm_diff": h_norm_diff,
                "source_state": source_interpreted_state,
                "start_year": analysis_start_date.year,
                "end_year": analysis_end_date.year,
                "analysis_years": analysis_years,
                "first_dist_year": first_dist_year,
                "last_dist_year": last_dist_year,
                "years_since_dist": years_since_dist,
                "persistence_years": persistence_years,
                "persistence_basis": persistence_basis,
                "persistence_threshold": persistence_threshold,
                "disturbance_span_years": disturbance_span_years,
                "final_state": final_state,
                "fp_condition": fp_condition,
                "fp_stab": fp_stab,
                "fp_recent": fp_recent,
                "fp_reworked": fp_reworked,
                "state_changed": state_changed,
                "source_n_events": source_n_events,
                "n_events_diff": n_events_diff,
                "source_n_episodes": source_n_episodes,
                "n_episodes_diff": n_episodes_diff,
                "source_since_disturb_years": source_since_disturb_years,
                "since_disturb_diff_years": since_disturb_diff_years,
                "bg_source": bg_source,
                "support_class": support_class,
            }

            # Spatial indexing representative points avoids repeated full-polygon
            # intersection tests, but is still potentially heavy on dense planar fabric.
            if representative_geometry and not representative_geometry.isEmpty():
                point = QgsPointXY(representative_geometry.asPoint())
                representative_points[feature.id()] = point
                index_feature = QgsFeature()
                index_feature.setId(feature.id())
                index_feature.setGeometry(QgsGeometry.fromPointXY(point))
                point_index.addFeature(index_feature)

            if counter % 5000 == 0:
                feedback.setProgress(10 + int(35.0 * counter / total_features))

        # Unknown numeric class values may indicate accidental use of an ID field
        # as CLASS_FIELD in upstream Module 4a and must be investigated.
        if unknown_value_counts:
            unknown_total = sum(unknown_value_counts.values())
            examples = sorted(
                unknown_value_counts.items(), key=lambda item: (-item[1], item[0])
            )[:12]
            feedback.reportError(
                f"[4d QA] {unknown_total:,} non-empty unrecognised class assignments "
                "were retained as non-event opportunities but excluded from state metrics. "
                "Most frequent: "
                + ", ".join(
                    f"{value or '<blank>'}={count:,}" for value, count in examples
                )
            )

            numeric_unknown_total = sum(
                count
                for value, count in unknown_value_counts.items()
                if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", str(value).strip())
            )
            if numeric_unknown_total:
                total_history_assignments = max(1, len(records) * len(ea_pairs))
                numeric_pct = 100.0 * numeric_unknown_total / total_history_assignments
                feedback.reportError(
                    f"[4d QA — IMPORTANT] {numeric_unknown_total:,} unrecognised "
                    f"EA_Class_i assignments ({numeric_pct:.2f}% of all unit-step "
                    "opportunities) are numeric. Module 4d expects textual process/class "
                    "labels such as erosion, deposition, stable_channel, stable_island, "
                    "or stable_floodplain. This commonly means that Module 4a was run "
                    "with an ID/code field selected as CLASS_FIELD. Outputs based on "
                    "ONTO_STATE_i can still be written, but may be incomplete or biased "
                    "because Module 4a derived those states from the same EA_Class_i "
                    "history. Do not interpret state, erosion/deposition event, frequency, "
                    "episode, persistence-since-disturbance, or dominance outputs until "
                    "the source class field is verified."
                )
        else:
            feedback.pushInfo("[4d QA] No non-empty unrecognised EA class values found.")

        # Cross-check Shannon, event count, episodes and elapsed disturbance time
        # against Module 4a. Non-zero mismatches are diagnostic, not refits.
        # Cross-check the reconstructed histories against Module 4a fields.
        # _count_nonzero_difference: Count analytical units whose recomputed quantity diverges from Module 4a.
        def _count_nonzero_difference(key, tolerance=0.0):
            count = 0
            for record in records.values():
                value = record.get(key)
                if value is None:
                    continue
                if abs(float(value)) > tolerance:
                    count += 1
            return count

        h_mismatch = _count_nonzero_difference("h_norm_diff", 0.000002)
        event_mismatch = _count_nonzero_difference("n_events_diff", 0.0)
        episode_mismatch = _count_nonzero_difference("n_episodes_diff", 0.0)
        persistence_mismatch = _count_nonzero_difference(
            "since_disturb_diff_years", 0.002
        )
        feedback.pushInfo(
            "[4d/M4a QA] mismatching units: "
            f"H_NORM={h_mismatch:,}; N_EVENTS={event_mismatch:,}; "
            f"N_EPISODES={episode_mismatch:,}; SINCE_DISTURB_YR={persistence_mismatch:,}."
        )

        # Pass 2: area-weighted neighbourhood event frequency from representative
        # points; the focal feature can contribute to its own local average.
        # --------------------------------------------------------------
        # Local representative-point neighbourhood metric.
        # --------------------------------------------------------------
        feedback.pushInfo(
            f"[4d] Calculating all-opportunity LOCAL_DIST_FREQ with radius={radius:g} map units "
            f"and neighbour minimum area={min_area:g}."
        )

        record_ids = list(records.keys())
        for counter, feature_id in enumerate(record_ids):
            self._cancel_if_requested(feedback)

            focal_record = records[feature_id]
            focal_point = representative_points.get(feature_id)

            # Radius zero is a documented no-smoothing path: local rate becomes
            # the focal unit disturbance frequency.
            if radius <= 0 or focal_point is None:
                local_frequency = focal_record["disturbance_frequency"]
            else:
                # The spatial index bounds candidate search by rectangle first; exact
                # point-to-point Euclidean distance then enforces the circular radius.
                search_geometry = QgsGeometry.fromPointXY(focal_point)
                search_rectangle = search_geometry.boundingBox()
                search_rectangle.grow(radius)
                candidate_ids = point_index.intersects(search_rectangle)

                weighted_sum = 0.0
                total_weight = 0.0

                for neighbour_id in candidate_ids:
                    neighbour_record = records.get(neighbour_id)
                    neighbour_point = representative_points.get(neighbour_id)
                    if neighbour_record is None or neighbour_point is None:
                        continue
                    neighbour_frequency = neighbour_record["disturbance_frequency"]
                    if neighbour_frequency is None:
                        continue
                    # MIN_AREA is applied only to neighbouring (non-focal) polygons.
                    # Weights use max(1, polygon area) in map units.
                    if (
                        neighbour_id != feature_id
                        and min_area > 0
                        and neighbour_record["area"] < min_area
                    ):
                        continue
                    if focal_point.distance(neighbour_point) > radius:
                        continue

                    weight = max(1.0, float(neighbour_record["area"]))
                    weighted_sum += float(neighbour_frequency) * weight
                    total_weight += weight

                local_frequency = (
                    weighted_sum / total_weight
                    if total_weight > 0.0
                    else focal_record["disturbance_frequency"]
                )

            focal_record["local_disturbance_frequency"] = local_frequency
            focal_record["local_activity_class"] = self._local_activity_class(local_frequency)

            if counter % 5000 == 0:
                feedback.setProgress(45 + int(25.0 * counter / total_features))

        # Pass 3: create collision-safe combined source + canonical metric schema,
        # preserving non-4d source attributes and its original geometry.
        # --------------------------------------------------------------
        # Build output field schema and write spatial GeoPackage layer.
        # --------------------------------------------------------------
        unit_specs = self._unit_table_specs()
        # Existing AREA_MAP2/AREA_KM2 are preserved, while recalculated
        # geometric area is labelled AREA_MAP2_4D/AREA_KM2_4D.
        spatial_name_overrides = {
            "AREA_MAP2": "AREA_MAP2_4D",
            "AREA_KM2": "AREA_KM2_4D",
        }
        spatial_specs = [
            (
                spatial_name_overrides.get(field_name, field_name),
                field_type,
                length,
                precision,
                field_name,
            )
            for field_name, field_type, length, precision in unit_specs
        ]
        metric_spec_by_key = {
            spatial_name.casefold(): (
                spatial_name, field_type, length, precision, row_name
            )
            for spatial_name, field_type, length, precision, row_name in spatial_specs
        }

        # Build a GeoPackage-safe schema. Any pre-existing spatial Module 4d field
        # is deliberately omitted here and then re-added once using the canonical
        # v3.5 name/type. AREA_MAP2 and AREA_KM2 from the source are preserved;
        # recalculated spatial metrics are written as AREA_MAP2_4D / AREA_KM2_4D.
        output_fields = QgsFields()
        source_to_output_indices = []
        source_name_by_key = {}
        replaced_metric_fields = []
        omitted_duplicate_fields = []

        # Casefold comparisons prevent SQLite fields differing only by case from
        # causing constraint conflicts in a large reproducibility export.
        for source_index, source_field in enumerate(layer.fields()):
            source_name = source_field.name()
            source_key = source_name.casefold()

            if source_key in metric_spec_by_key:
                replaced_metric_fields.append(source_name)
                continue

            if source_key in source_name_by_key:
                omitted_duplicate_fields.append(
                    (source_name, source_name_by_key[source_key])
                )
                continue

            output_index = len(output_fields)
            output_fields.append(QgsField(source_field))
            source_to_output_indices.append((source_index, output_index))
            source_name_by_key[source_key] = source_name

        output_indices = {}
        for spatial_name, field_type, length, precision, row_name in spatial_specs:
            output_index = len(output_fields)
            output_fields.append(
                QgsField(spatial_name, field_type, "", length, precision)
            )
            output_indices[row_name] = output_index

        if replaced_metric_fields:
            feedback.pushInfo(
                "[4d] Replacing pre-existing/case-variant spatial Module 4d fields "
                "with canonical recalculated fields: "
                + ", ".join(replaced_metric_fields[:20])
                + (" ..." if len(replaced_metric_fields) > 20 else "")
            )

        if omitted_duplicate_fields:
            examples = ", ".join(
                f"{duplicate} (kept {kept})"
                for duplicate, kept in omitted_duplicate_fields[:12]
            )
            feedback.reportError(
                f"[4d QA] Omitted {len(omitted_duplicate_fields):,} "
                "case-insensitive duplicate source field(s) that GeoPackage cannot "
                f"store. Examples: {examples}"
            )

        # GeoPackage destination is cleared before writing; successful execution
        # creates all seven layers, rather than updating selected layers in place.
        self._safe_delete_gpkg(gpkg_path)
        spatial_writer = self._create_writer(
            gpkg_path,
            self.SPATIAL_LAYER_NAME,
            output_fields,
            layer.wkbType(),
            layer.sourceCrs(),
            context,
            overwrite_file=True,
        )

        # The source geometry is written without topology alteration. This
        # post-processor does not perform new planar assemblage reconstruction.
        written = 0
        for counter, feature in enumerate(layer.getFeatures()):
            self._cancel_if_requested(feedback)
            record = records.get(feature.id())
            if record is None:
                feedback.reportError(
                    f"[4d QA] Missing cached metrics for feature ID {feature.id()}; skipped."
                )
                continue

            row = self._record_to_unit_row(record)
            output_feature = QgsFeature(output_fields)
            output_feature.setGeometry(feature.geometry())
            source_attributes = feature.attributes()
            attributes = [None] * len(output_fields)
            for source_index, output_index in source_to_output_indices:
                if source_index < len(source_attributes):
                    attributes[output_index] = source_attributes[source_index]
            for field_name, value in row.items():
                attributes[output_indices[field_name]] = value
            output_feature.setAttributes(attributes)

            if not spatial_writer.addFeature(output_feature, QgsFeatureSink.FastInsert):
                del spatial_writer
                raise QgsProcessingException(
                    f"Spatial output insertion failed for feature ID {feature.id()}."
                )
            written += 1

            if counter % 5000 == 0:
                feedback.setProgress(70 + int(15.0 * counter / total_features))

        del spatial_writer
        spatial_uri, verified_count = self._verify_gpkg_layer(
            gpkg_path, self.SPATIAL_LAYER_NAME
        )
        feedback.pushInfo(
            f"[4d] Spatial layer written and verified: {verified_count:,} features."
        )

        # One table row is written for every cached assemblage feature, using
        # the canonical schema employed by the spatial layer.
        # --------------------------------------------------------------
        # Per-unit table: GPKG attributes + CSV.
        # --------------------------------------------------------------
        base_name = os.path.splitext(os.path.basename(gpkg_path))[0]
        unit_csv = os.path.join(table_folder, f"{base_name}_unit_metrics.csv")
        reach_csv = os.path.join(table_folder, f"{base_name}_reach_metrics.csv")
        class_csv = os.path.join(table_folder, f"{base_name}_class_summary.csv")
        assign_step_class_csv = os.path.join(
            table_folder, f"{base_name}_ea_support_by_step_class.csv"
        )
        assign_reach_csv = os.path.join(
            table_folder, f"{base_name}_ea_support_reach_summary.csv"
        )
        assign_step_status_csv = os.path.join(
            table_folder, f"{base_name}_ea_support_by_step_status.csv"
        )

        unit_fields = self._build_fields(unit_specs)
        unit_field_names = [field.name() for field in unit_fields]
        unit_writer = self._create_writer(
            gpkg_path,
            self.UNIT_LAYER_NAME,
            unit_fields,
            QgsWkbTypes.NoGeometry,
            QgsCoordinateReferenceSystem(),
            context,
            overwrite_file=False,
        )

        with open(unit_csv, "w", newline="", encoding="utf-8-sig") as handle:
            csv_writer = csv.DictWriter(
                handle, fieldnames=unit_field_names, extrasaction="ignore"
            )
            csv_writer.writeheader()
            for counter, record in enumerate(records.values()):
                row = self._record_to_unit_row(record)
                table_feature = QgsFeature(unit_fields)
                table_feature.setAttributes([row.get(name) for name in unit_field_names])
                if not unit_writer.addFeature(table_feature, QgsFeatureSink.FastInsert):
                    del unit_writer
                    raise QgsProcessingException("Failed writing Unit_Metrics_4d table.")
                csv_writer.writerow(
                    {
                        name: self._value_for_csv(row.get(name))
                        for name in unit_field_names
                    }
                )
                if counter % 10000 == 0:
                    feedback.setProgress(85 + int(7.0 * counter / total_features))
        del unit_writer

        # --------------------------------------------------------------
        # Reach/class summaries are descriptive and area weighted; class dimensions
        # can overlap by design (e.g. final state vs local activity).
        # Reach and class summary tables.
        # --------------------------------------------------------------
        total_area = sum(record["area"] for record in records.values())
        total_area_km2 = sum(record["area_km2"] for record in records.values())

        reach_rows = self._build_reach_rows(
            records,
            total_area,
            total_area_km2,
            analysis_start_date,
            analysis_end_date,
            persistence_threshold,
        )
        class_rows = self._build_class_rows(records, total_area)
        for row in class_rows:
            row["AREA_KM2"] = row["AREA_MAP2"] * area_to_km2

        # Reconstruct three EA-support audits after per-unit metrics and local
        # statistics have been calculated.
        (
            assign_step_class_rows,
            assign_reach_rows,
            assign_step_status_rows,
        ) = self._build_assignment_audit_rows(
            step_class_stats,
            reach_class_stats,
            step_category_stats,
            ea_pairs,
            period_date_by_step,
            total_area,
            area_to_km2,
            len(records),
        )

        # Area-partition closure is checked per timestep, with warnings where
        # derived classifications do not sum to the full mapped area.
        for row in assign_step_status_rows:
            category_total = (
                row["EA_SUPPORT_AREA_PCT"]
                + row["BACKGROUND_VALID_AREA_PCT"]
                + row["OUTSIDE_EA_AREA_PCT"]
                + row["INACTIVE_AREA_PCT"]
                + row["NO_OBS_AREA_PCT"]
                + row["PROC_UNRES_AREA_PCT"]
                + row["UNKNOWN_AREA_PCT"]
            )
            if abs(category_total - 100.0) > 0.01:
                feedback.reportError(
                    f"[4d QA] Step {row['STEP']} EA-support categories sum "
                    f"to {category_total:.6f}% rather than 100%."
                )

        # Independent QA compares directly auditable EA support with N_ASSIGNED;
        # BG_FP may prevent direct reconstruction from filled EA_Class_i labels.
        audit_support_pct = sum(
            row["AREA_TIME_PCT"]
            for row in assign_reach_rows
            if row["EA_SUPPORT_FLAG"] == 1
        )
        audit_background_pct = sum(
            row["AREA_TIME_PCT"]
            for row in assign_reach_rows
            if row["BACKGROUND_VALID_FLAG"] == 1
        )
        metric_support = self._weighted_mean(records, "ea_support_fraction")
        metric_support_pct = 100.0 * metric_support if metric_support is not None else 0.0
        if audit_background_pct <= 0.000001:
            if abs(audit_support_pct - metric_support_pct) > 0.0001:
                feedback.reportError(
                    "[4d QA] Reach audit EA-support percentage does not reproduce "
                    f"Mean EA Support Fraction: audit={audit_support_pct:.6f}%, "
                    f"metric={metric_support_pct:.6f}%."
                )
            else:
                feedback.pushInfo(
                    f"[4d QA] EA-support audit reproduces Mean EA Support Fraction: "
                    f"{metric_support_pct:.6f}%."
                )
        else:
            feedback.pushInfo(
                "[4d QA] Direct per-step EA support cannot be reconstructed inside "
                "BG_FP cells because Module 4a replaces their timestep values with "
                "stable_floodplain. N_EA_SUPPORT_4D therefore uses Module 4a "
                f"N_ASSIGNED; the audit separately reports validated background "
                f"({audit_background_pct:.6f}% area-time)."
            )

        # A complete publication archive should retain these no-geometry GPKG
        # tables and matching CSV rather than only the spatial colour map.
        reach_specs = self._reach_table_specs()
        class_specs = self._class_table_specs()
        assign_step_class_specs = self._assignment_step_class_specs()
        assign_reach_specs = self._assignment_reach_specs()
        assign_step_status_specs = self._assignment_step_status_specs()
        self._write_rows_to_gpkg_table(
            gpkg_path,
            self.REACH_LAYER_NAME,
            reach_specs,
            reach_rows,
            context,
        )
        self._write_rows_to_gpkg_table(
            gpkg_path,
            self.CLASS_LAYER_NAME,
            class_specs,
            class_rows,
            context,
        )
        self._write_rows_to_gpkg_table(
            gpkg_path,
            self.ASSIGN_STEP_CLASS_LAYER_NAME,
            assign_step_class_specs,
            assign_step_class_rows,
            context,
        )
        self._write_rows_to_gpkg_table(
            gpkg_path,
            self.ASSIGN_REACH_LAYER_NAME,
            assign_reach_specs,
            assign_reach_rows,
            context,
        )
        self._write_rows_to_gpkg_table(
            gpkg_path,
            self.ASSIGN_STEP_STATUS_LAYER_NAME,
            assign_step_status_specs,
            assign_step_status_rows,
            context,
        )

        self._write_rows_to_csv(
            reach_csv,
            [name for name, _, _, _ in reach_specs],
            reach_rows,
        )
        self._write_rows_to_csv(
            class_csv,
            [name for name, _, _, _ in class_specs],
            class_rows,
        )
        self._write_rows_to_csv(
            assign_step_class_csv,
            [name for name, _, _, _ in assign_step_class_specs],
            assign_step_class_rows,
        )
        self._write_rows_to_csv(
            assign_reach_csv,
            [name for name, _, _, _ in assign_reach_specs],
            assign_reach_rows,
        )
        self._write_rows_to_csv(
            assign_step_status_csv,
            [name for name, _, _, _ in assign_step_status_specs],
            assign_step_status_rows,
        )

        # Reopen six attribute-only layers to verify successful GeoPackage write;
        # the spatial polygon layer was independently reopened earlier.
        for expected_layer in (
            self.UNIT_LAYER_NAME,
            self.REACH_LAYER_NAME,
            self.CLASS_LAYER_NAME,
            self.ASSIGN_STEP_CLASS_LAYER_NAME,
            self.ASSIGN_REACH_LAYER_NAME,
            self.ASSIGN_STEP_STATUS_LAYER_NAME,
        ):
            _, count = self._verify_gpkg_layer(gpkg_path, expected_layer)
            feedback.pushInfo(
                f"[4d] GeoPackage table verified: {expected_layer} ({count:,} rows)."
            )

        # Final output logs report counts and paths; a successful QGIS runtime
        # run is still needed to verify actual datasets, geometries and QA.
        feedback.setProgress(100)
        feedback.pushInfo(
            f"[4d] Completed: {written:,} spatial features, three metric tables, "
            "and three EA-support audit tables."
        )
        feedback.pushInfo(f"[4d] Multi-layer GeoPackage: {gpkg_path}")
        feedback.pushInfo(f"[4d] Per-unit CSV: {unit_csv}")
        feedback.pushInfo(f"[4d] Reach metrics CSV: {reach_csv}")
        feedback.pushInfo(f"[4d] Class summary CSV: {class_csv}")
        feedback.pushInfo(f"[4d QA] EA support by step/class CSV: {assign_step_class_csv}")
        feedback.pushInfo(f"[4d QA] Reach EA-support summary CSV: {assign_reach_csv}")
        feedback.pushInfo(f"[4d QA] EA support by step/status CSV: {assign_step_status_csv}")
        feedback.pushInfo(
            "[4d] Persistence fields are elapsed years: PERSIST_YRS_4D, "
            "MAX_QUIET_YRS, DIST_SPAN_YRS, and YEARS_SINCE_DIST."
        )

        return {
            self.OUTPUT_GPKG: gpkg_path,
            self.OUTPUT_LAYER: spatial_uri,
            self.UNIT_TABLE: unit_csv,
            self.REACH_TABLE: reach_csv,
            self.CLASS_TABLE: class_csv,
            self.ASSIGN_STEP_CLASS_TABLE: assign_step_class_csv,
            self.ASSIGN_REACH_TABLE: assign_reach_csv,
            self.ASSIGN_STEP_STATUS_TABLE: assign_step_status_csv,
        }
