# -*- coding: utf-8 -*-
"""
Module 4b — Visual Stratigraphic Overlay / Chronicle v3.2 FINAL
Unified QGIS Processing script for meandering, braided and mixed river styles.

Replaces earlier separate Module 4b chronology scripts.

Core design
-----------
- Date-based matching restored: EA interval PeriodEnd -> matching channel date.
- Supports normal n EA intervals + n+1 channel dates.
- Uses the channel at PeriodStart as previous_channel when available.
- Builds a STACKED chronicle layer: EA surfaces + legacy channel surfaces + channel surfaces.
- Aligns fields with Module 4a-style deterministic classification.

Output fields
-------------
EA_class      : raw / chronicle class, e.g. erosion, deposition, migration_deposition,
                infill_deposition, channel_legacy_deposition, channel_surface
ChronType     : geometry role only: ea_surface or channel_surface
PeriodStart   : interval start date text yyyy_mm_dd where known
PeriodEnd     : interval/channel end date text yyyy_mm_dd
Start_ymd     : integer yyyymmdd where known
End_ymd       : integer yyyymmdd
Year          : year from PeriodEnd
Step          : chronological step, oldest to newest
DrawOrder     : feature rendering order; larger draws later/on top
EA_clean      : lower-case cleaned EA_class
Depo_Type     : migration / infill / legacy_channel / generic / island / NULL
Surface_Type  : channel / island / floodplain
is_channel    : 1/0
is_depo       : 1/0
is_ero        : 1/0

Recommended styling
-------------------
Use categorized renderer on: coalesce("Depo_Type", "EA_clean")
Enable feature rendering order by DrawOrder ascending.
"""

# PAPER 2 SOURCE ARCHIVE | PUB: Dated Chronicle v3.2 (publication support).
# Archive filename: FRAF_P2_PUB_DatedChronicle_v3_2.py.
# Original QGIS Processing algorithm ID: scs_module4b_chronicle_v32 (unchanged).
# Documentation-only archive copy: execution order, expressions, parameter
# defaults, output fields, class name and algorithm behaviour are unmodified.
# Purpose and dependency boundary:
# This script stacks dated EA-process evidence with dated channel polygons
# for chronological display and interpretation. It is not the authoritative
# Module 4a assemblage-history reconstruction and does not construct the
# fixed-place risk table, age estimates, Cox models or held-out predictions.
# Chronicle class names are descriptive/cartographic, not substitutes for
# the AD / DS / SF organisational states and their transition risk sets.
# Source inputs and sequence:
# Supply one polygon layer per EA interval and dated channel snapshots,
# normally n EA intervals and n+1 channel dates. Each EA interval is attached
# to its PeriodEnd channel; a PeriodStart channel supports legacy outlines.
# Input geometry, date naming, coordinate reference systems and period coverage
# must have been quality-checked upstream; this module is not an EA classifier.
# Outputs and interpretation:
# The single stacked GeoPackage combines EA surfaces, derived legacy areas
# and channel-surface overlays. DrawOrder encodes display precedence only;
# overlapping features are expected and must not be summed as planar area.
# Derived deposition subtypes/legacy geometry are display interpretations,
# not independently measured sedimentary bodies or dated surface ages.
# Reproducibility / operational cautions:
# Run within QGIS with its Processing providers enabled. The script makes
# many temporary overlay layers and can require substantial memory/disk.
# The writer replaces the requested output GeoPackage: use a dedicated path.
# This archive revision has not been independently executed in QGIS.
import os
import re
import processing

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessingUtils,
    QgsVectorLayer,
    QgsWkbTypes,
)


# QgsProcessingAlgorithm provides Toolbox parameters, descriptions and a
# single vector destination; retain this class and its registration ID.
class SCS_Module4b_Chronicle_v32(QgsProcessingAlgorithm):
    PARAM_EA_LAYERS = "EA_LAYERS"
    PARAM_CHANNEL_LAYERS = "CHANNEL_LAYERS"
    PARAM_CLASS_FIELD = "CLASS_FIELD"
    PARAM_PERIOD_FIELD = "PERIOD_FIELD"
    PARAM_CHANNEL_DATE_FIELD = "CHANNEL_DATE_FIELD"
    PARAM_DISSOLVE_PER_STEP = "DISSOLVE_PER_STEP"
    PARAM_SPLIT_DEPOSITION = "SPLIT_DEPOSITION"
    PARAM_MIGRATION_BUFFER = "MIGRATION_BUFFER"
    PARAM_OUTPUT_STACKED = "OUTPUT_STACKED"

    # Translate human-facing labels through the existing SCS context.
    def tr(self, text):
        return QCoreApplication.translate("SCS Module 4b Chronicle v3.2", text)

    # QGIS instantiates a fresh algorithm object via this factory method.
    def createInstance(self):
        return SCS_Module4b_Chronicle_v32()

    # Processing ID is an existing external interface; do not change for archive renaming.
    def name(self):
        return "scs_module4b_chronicle_v32"

    # Display label retains historic Module 4b branding for existing QGIS users.
    def displayName(self):
        return self.tr("Module 4b — Chronicle / Visual stratigraphic overlay v3.2 FINAL")

    # Retain the original SCS Toolbox group/groupId for backward compatibility.
    def group(self):
        return self.tr("SCS Toolbox")

    def groupId(self):
        return "scs_ea_utils"

    # Toolbox help describes the stacking mechanism, not a statistical analysis.
    def shortHelpString(self):
        return self.tr(
            "Unified Module 4b chronicle builder. Date-matches EA interval layers to channel "
            "layers by PeriodEnd, supports n EA intervals + n+1 channel dates, creates a single "
            "STACKED chronicle layer with deterministic Module 4a-compatible classification fields."
        )

    # ---------------- parameters ---------------- #

    # Register the exact existing user-facing parameters and one vector output.
    # Defaults control interpretation, especially class field, date source,
    # per-step dissolve, deposition splitting and optional buffer distance.
    def initAlgorithm(self, config=None):
        # EA layers may carry interval dates in the chosen period field or layer name.
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_EA_LAYERS,
                self.tr("EA polygon layers / interval layers"),
                layerType=QgsProcessing.TypeVectorPolygon,
            )
        )
        # Channel snapshots supply end-state geometry at each matched EA end date.
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_CHANNEL_LAYERS,
                self.tr("Channel polygon layers / dated states"),
                layerType=QgsProcessing.TypeVectorPolygon,
            )
        )
        # CLASS_FIELD defaults to EA, although the EA field has hard-coded priority below.
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_CLASS_FIELD,
                self.tr("EA class field name"),
                defaultValue="EA",
            )
        )
        # PERIOD_FIELD is expected to contain a date or an interval label.
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_PERIOD_FIELD,
                self.tr("EA period field name"),
                defaultValue="period",
            )
        )
        # When blank, channel date is extracted from the layer name.
        self.addParameter(
            QgsProcessingParameterString(
                self.PARAM_CHANNEL_DATE_FIELD,
                self.tr("Channel date field name; leave blank to parse from layer name"),
                defaultValue="",
            )
        )
        # Dissolve changes visual geometry grouping; individual feature identity is lost.
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_DISSOLVE_PER_STEP,
                self.tr("Dissolve EA layer per class before stacking"),
                defaultValue=True,
            )
        )
        # Optional spatial split distinguishes end-channel overlap from other deposition.
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_SPLIT_DEPOSITION,
                self.tr("Split deposition into migration_deposition and infill_deposition"),
                defaultValue=True,
            )
        )
        # Buffer units follow layer CRS; 0 means no buffer around the end channel.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MIGRATION_BUFFER,
                self.tr("Migration buffer distance for splitting deposition"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )
        # The sole persistent output is a stacked polygon vector destination.
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.PARAM_OUTPUT_STACKED,
                self.tr("Stacked chronicle output"),
                type=QgsProcessing.TypeVectorPolygon,
            )
        )

    # ---------------- generic helpers ---------------- #
    # Remove pre-existing derived columns before recalculating them.
    # This prevents provider duplicate-field suffixes on merged intermediate data.
    def _drop_existing_fields(self, layer, field_names, context, feedback):
        lyr = self._as_layer(layer, context)
        existing = [f for f in field_names if lyr.fields().indexFromName(f) != -1]

        # If no conflicting columns exist, pass through unchanged.
        if not existing:
            return layer

        # Use native:deletecolumn and return its temporary output reference.
        return self._run(
            "native:deletecolumn",
            {
                "INPUT": layer,
                "COLUMN": existing,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            f"drop_existing_{'_'.join(existing)}",
        )["OUTPUT"]
    
    # Centralised Processing child-algorithm wrapper; logs a descriptive tag.
    # All overlays inherit the parent processing context and feedback channel.
    def _run(self, alg_id, params, context, feedback, tag):
        feedback.pushInfo(f"Running {alg_id} [{tag}] ...")
        return processing.run(
            alg_id,
            params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

    # Resolve a QGIS layer object, temporary output or OGR-backed path.
    # Raise promptly if a Processing output cannot be reopened.
    def _as_layer(self, src, context, name="tmp"):
        if isinstance(src, QgsVectorLayer):
            return src
        lyr = QgsProcessingUtils.mapLayerFromString(str(src), context)
        if lyr is None or not lyr.isValid():
            lyr = QgsVectorLayer(str(src), name, "ogr")
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"Cannot load layer from: {src}")
        return lyr

    # Feature count is used to skip null/empty overlay branches safely.
    def _feature_count(self, src, context):
        if src is None:
            return 0
        lyr = self._as_layer(src, context)
        return lyr.featureCount() if lyr and lyr.isValid() else 0

    # Repair polygon geometry before potentially fragile difference/intersection.
    # METHOD=1 is the original QGIS native:fixgeometries method setting.
    def _fix(self, layer, context, feedback, tag):
        return self._run(
            "native:fixgeometries",
            {"INPUT": layer, "METHOD": 1, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            tag,
        )["OUTPUT"]

    # Combine nonempty parts; ignore empty geometries and unnecessary one-layer merges.
    # CRS=None is inherited from the original implementation: inspect mixed-CRS
    # inputs before execution rather than assuming that output reprojection occurs.
    def _merge_layers(self, layers, context, feedback, tag):
        good = [lyr for lyr in layers if lyr is not None and self._feature_count(lyr, context) > 0]
        if not good:
            return None
        if len(good) == 1:
            return good[0]
        return self._run(
            "native:mergevectorlayers",
            {"LAYERS": good, "CRS": None, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"merge_{tag}",
        )["OUTPUT"]

    # Return INPUT minus OVERLAY; used to identify former channel area and other
    # outside-channel parts. Empty overlays intentionally leave INPUT unchanged.
    def _difference(self, input_src, overlay_src, context, feedback, tag):
        if input_src is None or self._feature_count(input_src, context) == 0:
            return input_src
        if overlay_src is None or self._feature_count(overlay_src, context) == 0:
            return input_src
        return self._run(
            "native:difference",
            {"INPUT": input_src, "OVERLAY": overlay_src, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"diff_{tag}",
        )["OUTPUT"]

    # Delegate provider-backed expression selection to native:extractbyexpression.
    def _extract_by_expression(self, layer, expr, context, feedback, tag):
        return self._run(
            "native:extractbyexpression",
            {"INPUT": layer, "EXPRESSION": expr, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"extract_{tag}",
        )["OUTPUT"]

    # Normalise destination to .gpkg and create the containing directory.
    # The default internal GeoPackage layer name is EA_chronicle_stacked.
    def _normalize_output_path(self, raw_out, default_layer_name):
        if not raw_out:
            return None, default_layer_name
        out_path = raw_out.split("|")[0]
        root, ext = os.path.splitext(out_path)
        if ext.lower() != ".gpkg":
            out_path = root + ".gpkg"
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        return out_path, default_layer_name

    # Persist the entire STACKED chronology as one vector dataset.
    # IMPORTANT: this function deletes existing GeoPackage and WAL/SHM paths
    # before calling savefeatures with OVERWRITE=True. It is not append-safe.
    def _save_output(self, src, out_path, out_layername, context, feedback, tag):
        if src is None or self._feature_count(src, context) == 0:
            raise QgsProcessingException(f"No features were produced for output '{out_layername}'.")

        # Existing lock-sidecar deletion is best-effort, not a concurrency safeguard.
        # Avoid stale GeoPackage lock sidecars where possible.
        for p in (out_path, out_path + "-shm", out_path + "-wal"):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

        # Use the original native:savefeatures parameter contract without alterations.
        params = {"INPUT": src, "OUTPUT": out_path}
        # Some QGIS versions ignore LAYER_NAME for generic vector destinations, but it is harmless.
        params["LAYER_NAME"] = out_layername
        params["OVERWRITE"] = True

        return self._run("native:savefeatures", params, context, feedback, f"save_{tag}")["OUTPUT"]

    # ---------------- date helpers ---------------- #

    @staticmethod
    # Build the yyyy_mm_dd label used across chronicle attribute fields.
    def _norm_date_txt(y, m, d):
        return f"{y}_{m}_{d}"

    # Parse a date or interval string into (start_date, end_date) labels.
    # Supported formats: YYYYMMDD_YYYYMMDD, separated full intervals,
    # single YYYYMMDD / YYYY_MM_DD, and year-only YYYY.
    # For end-date-only input the start remains unknown (None).
    def _parse_period_value(self, raw):
        if raw is None:
            return (None, None)
        s = str(raw).strip()
        if not s:
            return (None, None)

        # Standardise common date separators; other formats return (None, None).
        s2 = s.replace("-", "_").replace("/", "_").strip()

        # Full compact interval with two YYYYMMDD endpoints.
        # yyyymmdd_yyyymmdd
        m = re.match(r"^((?:18|19|20)\d{2})(\d{2})(\d{2})_+((?:18|19|20)\d{2})(\d{2})(\d{2})$", s2)
        if m:
            st = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
            en = self._norm_date_txt(m.group(4), m.group(5), m.group(6))
            return (st, en)

        # Full interval with underscores and double-underscore boundary allowed.
        # yyyy_mm_dd_yyyy_mm_dd, allowing repeated separators between dates
        m = re.match(r"^((?:18|19|20)\d{2})_(\d{2})_(\d{2})_+((?:18|19|20)\d{2})_(\d{2})_(\d{2})$", s2)
        if m:
            st = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
            en = self._norm_date_txt(m.group(4), m.group(5), m.group(6))
            return (st, en)

        # Single compact date supplies PeriodEnd but not PeriodStart.
        # yyyymmdd
        m = re.match(r"^((?:18|19|20)\d{2})(\d{2})(\d{2})$", s2)
        if m:
            en = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
            return (None, en)

        # Separated standalone date supplies only the end date.
        # yyyy_mm_dd
        m = re.match(r"^((?:18|19|20)\d{2})_(\d{2})_(\d{2})$", s2)
        if m:
            en = self._norm_date_txt(m.group(1), m.group(2), m.group(3))
            return (None, en)

        # A bare year is conventionally mapped to 1 January of that year.
        # yyyy only
        m = re.match(r"^((?:18|19|20)\d{2})$", s2)
        if m:
            en = self._norm_date_txt(m.group(1), "01", "01")
            return (None, en)

        return (None, None)

    # Choose one canonical period per whole EA input layer, not per individual
    # feature. Mixed intervals inside a single EA layer are not split.
    # The code takes the latest parsable end and latest parsable start, so users
    # must provide interval-pure EA layers to avoid cross-period misassignment.
    def _layer_canonical_period(self, vlyr, period_field, feedback):
        idx = vlyr.fields().indexFromName(period_field)
        ends, starts = [], []
        bad = 0

        # Prefer the configured attribute; skip rows with unreadable dates.
        if idx != -1:
            for f in vlyr.getFeatures():
                st, en = self._parse_period_value(f[period_field])
                if en is None:
                    bad += 1
                    continue
                ends.append(en)
                if st is not None:
                    starts.append(st)

        # If attributes yield no dates, try the EA layer name.
        if not ends:
            st, en = self._parse_period_value(vlyr.name())
            if en is None:
                raise QgsProcessingException(
                    f"No parseable period values in field '{period_field}' and none parseable from layer name '{vlyr.name()}'"
                )
            feedback.pushInfo(f"[Info] Using EA layer name for period: {vlyr.name()} -> {en}")
            end_txt = en
            start_txt = st
        # Warn about malformed rows while retaining parsable dates.
        else:
            if bad:
                feedback.reportError(
                    f"[Warn] {bad} feature(s) in '{vlyr.name()}' had unparseable {period_field}; ignored."
                )
            # Sort dates as canonical yyyy_mm_dd text; the maximum is selected.
            end_txt = sorted(ends)[-1]
            start_txt = sorted(starts)[-1] if starts else None

        # Store numeric YYYYMMDD integer keys for precise channel-date lookup.
        end_ymd = int(end_txt.replace("_", ""))
        start_ymd = int(start_txt.replace("_", "")) if start_txt else None
        return start_txt, end_txt, start_ymd, end_ymd

    # Extract the observation date of an entire channel snapshot layer.
    # As for EA, the maximum parsable attribute date is used if multiple occur;
    # otherwise the layer name must contain a recognised date.
    def _channel_layer_date(self, vlyr, date_field, feedback):
        idx = vlyr.fields().indexFromName(date_field) if date_field else -1
        dates = []
        bad = 0

        # If a date field was supplied and exists, read its per-feature values.
        if idx != -1:
            for f in vlyr.getFeatures():
                _, en = self._parse_period_value(f[date_field])
                if en is None:
                    bad += 1
                    continue
                dates.append(en)

        # Without a usable date attribute, parse the channel layer name.
        if not dates:
            _, en = self._parse_period_value(vlyr.name())
            if en is None:
                raise QgsProcessingException(
                    f"No parseable date values in channel field '{date_field}' and none parseable from layer name '{vlyr.name()}'"
                )
            feedback.pushInfo(f"[Info] Using channel layer name for date: {vlyr.name()} -> {en}")
            end_txt = en
        # Warn about invalid date attributes but retain the selected canonical date.
        else:
            if bad:
                feedback.reportError(
                    f"[Warn] {bad} feature(s) in channel layer '{vlyr.name()}' had unparseable {date_field}; ignored."
                )
            end_txt = sorted(dates)[-1]

        end_ymd = int(end_txt.replace("_", ""))
        return end_txt, end_ymd

    # ---------------- refactor / classification ---------------- #

    # Convert an EA interval to a consistent chronicle field schema.
    # Uses native:refactorfields to preserve a deterministic column set.
    # The EA source class describes process evidence, not a final AD/DS/SF state.
    def _refactor_ea_step(self, fixed, source_layer, step, st_txt, en_txt, st_ymd, en_ymd,
                          class_field, period_field, context, feedback):
        fixed_lyr = self._as_layer(fixed, context)
        names = fixed_lyr.fields().names()

        # Class lookup deliberately prefers literal EA over the configurable
        # CLASS_FIELD, then EA_Class; missing classes propagate as NULL.
        if "EA" in names:
            expr_class = 'nullif(trim(to_string("EA")), \'\')'
        elif class_field and class_field in names:
            expr_class = f'nullif(trim(to_string("{class_field}")), \'\')'
        elif "EA_Class" in names:
            expr_class = 'nullif(trim(to_string("EA_Class")), \'\')'
        else:
            expr_class = "NULL"
            feedback.reportError(
                f"[Warn] No usable EA class field found in '{source_layer.name()}'. Checked EA, {class_field}, EA_Class."
            )

        # Insert interval metadata as expressions constant across the EA layer.
        expr_pstart = "NULL" if st_txt is None else f"'{st_txt}'"
        expr_pend = f"'{en_txt}'"
        expr_start_ymd = "NULL" if st_ymd is None else str(int(st_ymd))
        expr_end_ymd = str(int(en_ymd))
        expr_year = f"to_int(substr('{en_txt}',1,4))"
        # Each chronological step gets a base DrawOrder of step*10 + 5.
        # Channel and derived deposition variants receive later offsets.
        expr_step = str(int(step))
        expr_draw = str(int(step * 10 + 5))

        # Carry optional EA direction/migration/duration fields when available.
        expr_direction = 'nullif(trim(to_string("direction")), \'\')' if "direction" in names else "NULL"
        expr_migration = 'nullif(trim(to_string("migration")), \'\')' if "migration" in names else "NULL"
        expr_period = f'nullif(trim(to_string("{period_field}")), \'\')' if period_field in names else expr_pend
        expr_span_days = '"span_days"' if "span_days" in names else "NULL"
        expr_span_years = '"span_years"' if "span_years" in names else ('"Span_yr"' if "Span_yr" in names else "NULL")

        # Boolean flags follow the listed EA text aliases; the mapping is intentionally
        # simpler than a full reconstructed assemblage-state ontology.
        expr_is_channel = "CASE WHEN lower(coalesce({0},'')) IN ('stable_channel','channel','water','active_channel','channel_surface') THEN 1 ELSE 0 END".format(expr_class)
        expr_is_depo = "CASE WHEN lower(coalesce({0},'')) IN ('deposition','island_deposition','migration_deposition','infill_deposition','channel_legacy_deposition') THEN 1 ELSE 0 END".format(expr_class)
        expr_is_ero = "CASE WHEN lower(coalesce({0},'')) IN ('erosion','island_erosion') THEN 1 ELSE 0 END".format(expr_class)

        # Mapping declares standard process/date/rendering fields and QGIS field types.
        # Original attribute expressions, field names and field order are preserved.
        fields_mapping = [
            {"name": "EA_class",    "type": 10, "length": 254, "precision": 0, "expression": expr_class},
            {"name": "ChronType",   "type": 10, "length": 32,  "precision": 0, "expression": "'ea_surface'"},
            {"name": "PeriodStart", "type": 10, "length": 32,  "precision": 0, "expression": expr_pstart},
            {"name": "PeriodEnd",   "type": 10, "length": 32,  "precision": 0, "expression": expr_pend},
            {"name": "Start_ymd",   "type": 1,  "length": 10,  "precision": 0, "expression": expr_start_ymd},
            {"name": "End_ymd",     "type": 1,  "length": 10,  "precision": 0, "expression": expr_end_ymd},
            {"name": "Year",        "type": 2,  "length": 4,   "precision": 0, "expression": expr_year},
            {"name": "Step",        "type": 1,  "length": 10,  "precision": 0, "expression": expr_step},
            {"name": "DrawOrder",   "type": 1,  "length": 10,  "precision": 0, "expression": expr_draw},
            {"name": "direction",   "type": 10, "length": 128, "precision": 0, "expression": expr_direction},
            {"name": "migration",   "type": 10, "length": 128, "precision": 0, "expression": expr_migration},
            {"name": "period",      "type": 10, "length": 64,  "precision": 0, "expression": expr_period},
            {"name": "span_days",   "type": 6,  "length": 20,  "precision": 6, "expression": expr_span_days},
            {"name": "span_years",  "type": 6,  "length": 20,  "precision": 6, "expression": expr_span_years},
            {"name": "is_channel",  "type": 1,  "length": 1,   "precision": 0, "expression": expr_is_channel},
            {"name": "is_depo",     "type": 1,  "length": 1,   "precision": 0, "expression": expr_is_depo},
            {"name": "is_ero",      "type": 1,  "length": 1,   "precision": 0, "expression": expr_is_ero},
        ]

        # Refactor via QGIS child algorithm instead of modifying the source layer.
        return self._run(
            "native:refactorfields",
            {"INPUT": fixed, "FIELDS_MAPPING": fields_mapping, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"refactor_ea_{step}",
        )["OUTPUT"]

    # Reclassify an already prepared polygon component (e.g. a channel outline,
    # a legacy channel footprint, or an interpreted deposition subtype).
    # Date metadata are assigned to the current EA end-step for display.
    def _reclassify_layer(self, layer, ea_class_value, chron_type_value, step, en_txt, en_ymd,
                          context, feedback, tag, draw_offset=6):
        expr_pend = f"'{en_txt}'"
        expr_end_ymd = str(int(en_ymd))
        expr_year = f"to_int(substr('{en_txt}',1,4))"
        expr_step = str(int(step))
        # draw_offset differentiates feature stacking within the same time step.
        expr_draw = str(int(step * 10 + draw_offset))
        # Set role flags from the explicit reclassification label, not geometry.
        is_channel = 1 if chron_type_value == "channel_surface" or ea_class_value == "channel_surface" else 0
        is_depo = 1 if ea_class_value in ("deposition", "island_deposition", "migration_deposition", "infill_deposition", "channel_legacy_deposition") else 0
        is_ero = 1 if ea_class_value in ("erosion", "island_erosion") else 0

        # Write the same schema as the main EA step to enable mergevectorlayers.
        fields_mapping = [
            {"name": "EA_class",    "type": 10, "length": 254, "precision": 0, "expression": f"'{ea_class_value}'"},
            {"name": "ChronType",   "type": 10, "length": 32,  "precision": 0, "expression": f"'{chron_type_value}'"},
            {"name": "PeriodStart", "type": 10, "length": 32,  "precision": 0, "expression": "NULL"},
            {"name": "PeriodEnd",   "type": 10, "length": 32,  "precision": 0, "expression": expr_pend},
            {"name": "Start_ymd",   "type": 1,  "length": 10,  "precision": 0, "expression": "NULL"},
            {"name": "End_ymd",     "type": 1,  "length": 10,  "precision": 0, "expression": expr_end_ymd},
            {"name": "Year",        "type": 2,  "length": 4,   "precision": 0, "expression": expr_year},
            {"name": "Step",        "type": 1,  "length": 10,  "precision": 0, "expression": expr_step},
            {"name": "DrawOrder",   "type": 1,  "length": 10,  "precision": 0, "expression": expr_draw},
            {"name": "direction",   "type": 10, "length": 128, "precision": 0, "expression": "NULL"},
            {"name": "migration",   "type": 10, "length": 128, "precision": 0, "expression": "NULL"},
            {"name": "period",      "type": 10, "length": 64,  "precision": 0, "expression": expr_pend},
            {"name": "span_days",   "type": 6,  "length": 20,  "precision": 6, "expression": "NULL"},
            {"name": "span_years",  "type": 6,  "length": 20,  "precision": 6, "expression": "NULL"},
            {"name": "is_channel",  "type": 1,  "length": 1,   "precision": 0, "expression": str(is_channel)},
            {"name": "is_depo",     "type": 1,  "length": 1,   "precision": 0, "expression": str(is_depo)},
            {"name": "is_ero",      "type": 1,  "length": 1,   "precision": 0, "expression": str(is_ero)},
        ]

        # Apply the constant-value schema through native:refactorfields.
        return self._run(
            "native:refactorfields",
            {"INPUT": layer, "FIELDS_MAPPING": fields_mapping, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"reclass_{tag}",
        )["OUTPUT"]

    # Represent the observed end-of-interval channel as a channel_surface.
    # Offset +9 draws channel above EA +5 and derived components +6.
    def _refactor_channel_step(self, fixed, step, en_txt, en_ymd, context, feedback):
        return self._reclassify_layer(
            fixed,
            "channel_surface",
            "channel_surface",
            step,
            en_txt,
            en_ymd,
            context,
            feedback,
            f"channel_{step}",
            draw_offset=9,
        )

    # Optional dissolve is controlled by DISSOLVE_PER_STEP.
    # The large grouping-field set means dissolution is by each unique
    # combination of retained attributes, not necessarily one geometry per class.
    def _maybe_dissolve_ea(self, layer, dissolve_per_step, context, feedback, tag):
        if not dissolve_per_step:
            return layer
        lyr = self._as_layer(layer, context)
        names = lyr.fields().names()
        # Only group by columns that actually exist in this intermediate layer.
        dissolve_fields = [
            nm for nm in [
                "EA_class", "ChronType", "direction", "migration", "period", "span_days", "span_years",
                "PeriodStart", "PeriodEnd", "Start_ymd", "End_ymd", "Year", "Step", "DrawOrder",
                "is_channel", "is_depo", "is_ero"
            ] if nm in names
        ]
        # Dissolve geometries without requesting separate disjoint components.
        return self._run(
            "native:dissolve",
            {"INPUT": layer, "FIELD": dissolve_fields, "SEPARATE_DISJOINT": False, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            feedback,
            f"diss_{tag}",
        )["OUTPUT"]

    # Derive cartographic classification columns for QGIS styling.
    # Delete existing copies before adding new EA_clean, Depo_Type,
    # Surface_Type and Chron_Class fields to avoid naming collisions.
    # These classes support presentation, not statistical event adjudication.
    def _add_chronicle_class_fields(self, layer, context, feedback, tag):
        layer = self._drop_existing_fields(
            layer,
            ["EA_clean", "Depo_Type", "Surface_Type", "Chron_Class"],
            context,
            feedback
        )

        # Normalise raw EA_class text to lower-case EA_clean.
        layer = self._run(
            "native:fieldcalculator",
            {
                "INPUT": layer,
                "FIELD_NAME": "EA_clean",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 64,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "lower(trim(coalesce(\"EA_class\",'')))",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_ea_clean",
        )["OUTPUT"]

        # Depo_Type separates the five named depositional display subclasses.
        layer = self._run(
            "native:fieldcalculator",
            {
                "INPUT": layer,
                "FIELD_NAME": "Depo_Type",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": """
    CASE
    WHEN "EA_clean" = 'migration_deposition' THEN 'migration'
    WHEN "EA_clean" = 'infill_deposition' THEN 'infill'
    WHEN "EA_clean" = 'channel_legacy_deposition' THEN 'legacy_channel'
    WHEN "EA_clean" = 'island_deposition' THEN 'island'
    WHEN "EA_clean" = 'deposition' THEN 'generic'
    ELSE NULL
    END
    """,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_depo_type",
        )["OUTPUT"]

        # Surface_Type distinguishes channel / island / floodplain context.
        # The fallback floodplain label does not assert a stable floodplain state.
        layer = self._run(
            "native:fieldcalculator",
            {
                "INPUT": layer,
                "FIELD_NAME": "Surface_Type",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": """
    CASE
    WHEN "is_channel" = 1 OR "ChronType" = 'channel_surface' OR "EA_clean" = 'channel_surface' THEN 'channel'
    WHEN "EA_clean" LIKE '%island%' THEN 'island'
    ELSE 'floodplain'
    END
    """,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_surface_type",
        )["OUTPUT"]

        # Chron_Class gives a single legend grouping across channel and EA parts.
        # Channels take precedence, followed by erosion and deposition subclasses.
        # stable_island and stable_floodplain are grouped as stable_inactive;
        # this is a visual category and not the formal DS->SF threshold rule.
        layer = self._run(
            "native:fieldcalculator",
            {
                "INPUT": layer,
                "FIELD_NAME": "Chron_Class",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": """
    CASE
    WHEN "ChronType" = 'channel_surface' OR "EA_clean" = 'channel_surface' THEN 'channel'
    WHEN "EA_clean" IN ('erosion','island_erosion') THEN 'erosion'
    WHEN "Depo_Type" = 'migration' THEN 'migration_deposition'
    WHEN "Depo_Type" = 'infill' THEN 'infill_deposition'
    WHEN "Depo_Type" = 'legacy_channel' THEN 'legacy_channel_deposition'
    WHEN "Depo_Type" = 'island' THEN 'island_deposition'
    WHEN "Depo_Type" = 'generic' THEN 'generic_deposition'
    WHEN "EA_clean" = 'stable_channel' THEN 'stable_channel'
    WHEN "EA_clean" IN ('stable_floodplain','inactive_floodplain','inchannel_surface','stable_island') THEN 'stable_inactive'
    ELSE 'other'
    END
    """,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context, feedback, f"{tag}_chron_class",
        )["OUTPUT"]

        # Return a temporary layer carrying all four publication classification fields.
        return layer

    # Spatially split general deposition relative to the interval end channel.
    # Only raw deposition and island_deposition are selected for this branch.
    # Intersection is labelled migration_deposition; remainder infill_deposition.
    # This is an overlay-derived convention, NOT independent sedimentological
    # identification or the formal organisational storage-event definition.
    def _split_deposition_by_channel(self, ea_ref, ch_ref, step, en_txt, en_ymd,
                                     split_deposition, migration_buffer, context, feedback):
        # When disabled, preserve EA class categories without reinterpretation.
        if not split_deposition:
            return ea_ref

        # Extract deposition features; all other recognised classes are separated.
        depo = self._extract_by_expression(
            ea_ref,
            'lower("EA_class") IN (\'deposition\', \'island_deposition\')',
            context,
            feedback,
            f"depo_{step}",
        )
        # The NOT IN expression may exclude NULL EA_class entries under QGIS SQL
        # three-valued logic; missing source classes should be resolved upstream.
        other = self._extract_by_expression(
            ea_ref,
            'lower("EA_class") NOT IN (\'deposition\', \'island_deposition\')',
            context,
            feedback,
            f"other_{step}",
        )

        # Return the unmodified EA step if no splittable deposition is present.
        if self._feature_count(depo, context) == 0:
            return ea_ref

        # A positive buffer increases the area counted as near/end-channel migration.
        if migration_buffer > 0:
            cutter = self._run(
                "native:buffer",
                {
                    "INPUT": ch_ref,
                    "DISTANCE": migration_buffer,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "DISSOLVE": True,
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                },
                context,
                feedback,
                f"dep_buffer_{step}",
            )["OUTPUT"]
        else:
            cutter = ch_ref

        # Intersect selected deposition with end-channel geometry (or its buffer).
        # A deposition component need not be physically preserved within the channel;
        # treat the result strictly as a cartographic overlay interpretation.
        mig_dep = self._run(
            "native:intersection",
            {
                "INPUT": depo,
                "OVERLAY": cutter,
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": "",
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            feedback,
            f"mig_dep_{step}",
        )["OUTPUT"]

        # Classify selected deposition outside the cutter as infill_deposition.
        infill_dep = self._difference(depo, cutter, context, feedback, f"infill_dep_{step}")

        # Rebuild the intersecting subset using the standard chronicle field schema.
        mig_dep = self._reclassify_layer(
            mig_dep,
            "migration_deposition",
            "ea_surface",
            step,
            en_txt,
            en_ymd,
            context,
            feedback,
            f"mig_dep_{step}",
            draw_offset=6,
        ) if self._feature_count(mig_dep, context) > 0 else None

        # Rebuild the out-of-channel subset using the same schema and draw offset.
        infill_dep = self._reclassify_layer(
            infill_dep,
            "infill_deposition",
            "ea_surface",
            step,
            en_txt,
            en_ymd,
            context,
            feedback,
            f"infill_dep_{step}",
            draw_offset=6,
        ) if self._feature_count(infill_dep, context) > 0 else None

        # Merge unchanged EA pieces with the two derived deposition subtypes.
        return self._merge_layers([other, mig_dep, infill_dep], context, feedback, f"ea_rebuilt_{step}")

    # ---------------- main ---------------- #

    # MAIN WORKFLOW: order EA intervals, match channel snapshots by date,
    # build three potential visual components per step and merge the stack.
    # Output is a mapped chronology, not a mutually exclusive planar fabric.
    def processAlgorithm(self, parameters, context, feedback):
        # Read the original QGIS Processing parameters; no archive-specific values.
        ea_layers = self.parameterAsLayerList(parameters, self.PARAM_EA_LAYERS, context)
        channel_layers = self.parameterAsLayerList(parameters, self.PARAM_CHANNEL_LAYERS, context)
        class_field = self.parameterAsString(parameters, self.PARAM_CLASS_FIELD, context)
        period_field = self.parameterAsString(parameters, self.PARAM_PERIOD_FIELD, context)
        channel_date_field = self.parameterAsString(parameters, self.PARAM_CHANNEL_DATE_FIELD, context)
        dissolve_per_step = self.parameterAsBoolean(parameters, self.PARAM_DISSOLVE_PER_STEP, context)
        split_deposition = self.parameterAsBoolean(parameters, self.PARAM_SPLIT_DEPOSITION, context)
        migration_buffer = self.parameterAsDouble(parameters, self.PARAM_MIGRATION_BUFFER, context)

        # Require nonempty EA and channel inputs, with an upper cap on EA layers.
        if not ea_layers:
            raise QgsProcessingException("Provide at least one EA polygon layer.")
        if not channel_layers:
            raise QgsProcessingException("Provide dated channel polygon layers.")
        if len(ea_layers) > 80:
            raise QgsProcessingException("This tool supports up to 80 EA interval layers in one run.")
        # At least n dated channel layers must be supplied for n EA intervals.
        # The expected n+1 count is descriptive, not strictly enforced here.
        if len(channel_layers) < len(ea_layers):
            raise QgsProcessingException(
                "You need at least as many channel layers as EA interval layers. "
                "Normally n EA intervals use n+1 channel dates."
            )

        # Validate polygon geometry type; no matching-CRS or coverage check is done.
        for v in ea_layers:
            if QgsWkbTypes.geometryType(v.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException(f"EA layer {v.name()} is not a polygon layer.")
        for v in channel_layers:
            if QgsWkbTypes.geometryType(v.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException(f"Channel layer {v.name()} is not a polygon layer.")

        # Resolve the output destination; writes a single GeoPackage path.
        raw_out_stacked = self.parameterAsOutputLayer(parameters, self.PARAM_OUTPUT_STACKED, context)
        out_stacked_path, out_stacked_name = self._normalize_output_path(raw_out_stacked, "EA_chronicle_stacked")

        # Build ordered EA interval metadata using each layer canonical PeriodEnd.
        # Order is chronological even if the selected GUI layer order is not.
        # Parse EA interval dates.
        ea_scored = []
        ea_canonical = {}
        for v in ea_layers:
            st_txt, en_txt, st_ymd, en_ymd = self._layer_canonical_period(v, period_field, feedback)
            ea_scored.append((en_ymd, v))
            ea_canonical[v.id()] = (st_txt, en_txt, st_ymd, en_ymd)
        ea_scored.sort(key=lambda t: t[0])

        # Index channel snapshots by observation date (YYYYMMDD).
        # If several inputs use one date, the last supplied layer overwrites the
        # earlier dictionary entry; the code warns but does not merge them.
        # Parse channel dates and index by end_ymd.
        channel_by_ymd = {}
        for ch in channel_layers:
            en_txt, en_ymd = self._channel_layer_date(ch, channel_date_field, feedback)
            if en_ymd in channel_by_ymd:
                feedback.reportError(
                    f"[Warn] More than one channel layer parsed to {en_txt}; later one will overwrite earlier one."
                )
            channel_by_ymd[en_ymd] = (ch, en_txt)

        # Log the dated analysis order to help reconcile input provenance.
        feedback.pushInfo(
            "EA order (oldest→newest): " +
            "  <  ".join([f"{v.name()}[{ea_canonical[v.id()][0]}→{ea_canonical[v.id()][1]}]" for _, v in ea_scored])
        )

        # Accumulate full per-step geometries; legacy reference tracks prior end channel.
        stacked_parts = []
        last_end_channel_ref = None

        # Each loop iteration corresponds to one dated erosion-accretion interval.
        for step, (_, ea_v) in enumerate(ea_scored, start=1):
            st_txt, en_txt, st_ymd, en_ymd = ea_canonical[ea_v.id()]
            feedback.pushInfo(f"[Step {step}] EA {ea_v.name()} -> {st_txt} to {en_txt}")

            # Require a matching end-of-interval channel snapshot for every EA layer.
            if en_ymd not in channel_by_ymd:
                raise QgsProcessingException(
                    f"No channel layer matched EA PeriodEnd {en_txt} ({ea_v.name()})."
                )

            ch_v, ch_txt = channel_by_ymd[en_ymd]
            feedback.pushInfo(f"[Step {step}] End-state channel {ch_v.name()} matched to {ch_txt}")

            # Use the true PeriodStart channel as the preferred prior outline.
            # When unavailable, the previous EA iteration end-channel is a fallback;
            # if neither exists, the legacy part for that step is omitted.
            # Prefer true start-date channel for previous_channel. Fall back to previous loop's end channel.
            previous_channel_raw = None
            if st_ymd is not None and st_ymd in channel_by_ymd:
                previous_channel_raw = channel_by_ymd[st_ymd][0]
                feedback.pushInfo(f"[Step {step}] Start-state channel matched by PeriodStart {st_txt}")
            elif last_end_channel_ref is not None:
                previous_channel_raw = last_end_channel_ref
                feedback.reportError(
                    f"[Warn] No start-state channel matched {st_txt}; using previous EA end-state channel."
                )
            else:
                feedback.reportError(
                    f"[Warn] No previous/start channel available for Step {step}; legacy surface skipped for first step."
                )

            # Repair both EA-process and matched end-state channel polygons.
            ea_fixed = self._fix(ea_v, context, feedback, f"fix_ea_{step}")
            ch_fixed = self._fix(ch_v, context, feedback, f"fix_ch_end_{step}")

            # Write common EA classification, period, step and draw-order attributes.
            ea_ref = self._refactor_ea_step(
                ea_fixed,
                ea_v,
                step,
                st_txt,
                en_txt,
                st_ymd,
                en_ymd,
                class_field,
                period_field,
                context,
                feedback,
            )
            # Optionally dissolve the EA component on its retained field values.
            ea_ref = self._maybe_dissolve_ea(ea_ref, dissolve_per_step, context, feedback, f"ea_{step}")

            # Reclassify the observed end channel at offset +9 for visual prominence.
            ch_ref = self._refactor_channel_step(ch_fixed, step, en_txt, en_ymd, context, feedback)

            # Construct the former channel footprint as previous_channel MINUS end_channel.
            # Label that geometry channel_legacy_deposition for chronicle presentation.
            # The difference alone does not demonstrate depositional mechanism,
            # storage duration or preserved surface formation.
            legacy_channel = None
            if previous_channel_raw is not None and self._feature_count(previous_channel_raw, context) > 0:
                # Convert start-state channel geometry into compatible step fields.
                prev_fixed = self._fix(previous_channel_raw, context, feedback, f"fix_ch_start_{step}")
                prev_ref_for_diff = self._refactor_channel_step(prev_fixed, step, en_txt, en_ymd, context, feedback)
                # Only non-overlapping former-channel geometry becomes a legacy part.
                legacy_geom = self._difference(prev_ref_for_diff, ch_ref, context, feedback, f"legacy_geom_{step}")
                if self._feature_count(legacy_geom, context) > 0:
                    legacy_channel = self._reclassify_layer(
                        legacy_geom,
                        "channel_legacy_deposition",
                        "ea_surface",
                        step,
                        en_txt,
                        en_ymd,
                        context,
                        feedback,
                        f"legacy_{step}",
                        draw_offset=6,
                    )

            # Optionally split generic deposition using the end-channel spatial test.
            ea_ref = self._split_deposition_by_channel(
                ea_ref,
                ch_ref,
                step,
                en_txt,
                en_ymd,
                split_deposition,
                migration_buffer,
                context,
                feedback,
            )

            # Apply the four descriptive mapping fields to each component independently.
            ea_ref = self._add_chronicle_class_fields(ea_ref, context, feedback, f"ea_{step}")
            ch_ref = self._add_chronicle_class_fields(ch_ref, context, feedback, f"ch_{step}")
            if legacy_channel is not None:
                legacy_channel = self._add_chronicle_class_fields(legacy_channel, context, feedback, f"legacy_{step}")

            # Stack EA, legacy and end-channel surfaces without erasing overlaps.
            # Use DrawOrder ascending when presenting the output in QGIS.
            stacked_parts.extend([part for part in [ea_ref, legacy_channel, ch_ref] if part is not None])
            last_end_channel_ref = ch_v

        # Merge all nonempty steps into one stacked layer and persist to GeoPackage.
        # The result is useful for dated graphics and qualitative interpretation;
        # it does not supply a fixed-place event history or surface-age estimate.
        stacked_merged = self._merge_layers(stacked_parts, context, feedback, "stacked_all")
        saved_stacked = self._save_output(stacked_merged, out_stacked_path, out_stacked_name, context, feedback, "stacked")

        # Expose the unchanged Processing output key for downstream QGIS access.
        return {self.PARAM_OUTPUT_STACKED: saved_stacked}