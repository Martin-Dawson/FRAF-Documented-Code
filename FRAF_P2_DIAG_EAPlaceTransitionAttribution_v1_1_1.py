# -*- coding: utf-8 -*-
"""FRAF EA -> PLACE Transition Attribution Audit v1.1.1, 2026-10-18.

QGIS Processing script for 3.40+ / intended for 3.44.9.

Uses the ANNUAL (not cumulative) polygons from FRAF EA-to-PLACE Erosion
Reconciliation v2.x. Spatially intersects those polygons with the authoritative
fixed KM_blocks PLACE grid; links each eroded PLACE-interval to the *original*
nonspatial Stage 4 Risk Table, without restricting to model-eligible rows.

Area-weighted outputs diagnose why an EA erosion polygon can lie outside
PRIMARY FP->AD or DS->AD event-cell masks. No modification of input data,
no cumulative geometry union, and no claim that a non-event is physical AD
persistence without explicit antecedent/end-state evidence.

The primary mapping audit can use ALL original EA erosion (full annual
reconciliation matrix); NEITHER-only is a residual diagnostic. EA geometric source and PLACE three-state history remain
SEPARATE axes; neither is substituted for the other.
"""
# [P2 ARCHIVE] FRAF PAPER 2 / PUBLICATION SOURCE ANNOTATIONS — diagnostic EA–PLACE attribution.
# [P2 ARCHIVE] Archive alias: FRAF_P2_DIAG_EAPlaceTransitionAttribution_v1_1_1.py
# [P2 ARCHIVE] Original source: FRAF_EA_PLACE_Transition_Attribution_Audit_v1_1_1.py
# [P2 ARCHIVE] Role: annual physical EA erosion geometry reconciled to fixed-place state
# [P2 ARCHIVE] histories, source labels, recognised FP→AD / DS→AD events and exclusions.
# [P2 ARCHIVE] Table S1 / S9: writes 02_area_attribution_summary.csv and accompanying QA.
# [P2 ARCHIVE] Five-year option: annual erosion areas are summed; repeated erosion of the
# [P2 ARCHIVE] same location in different years is not a dissolved five-year footprint.
# [P2 ARCHIVE] The PLACE grid supports attribution but does NOT convert the physical
# [P2 ARCHIVE] eroded fragments into whole-cell erosion polygons.
# [P2 ARCHIVE] Archive action: COMMENTS ONLY. Original Python statements, classes, method
# [P2 ARCHIVE] names, QGIS parameter IDs, data sources, outputs, and classification unchanged.

from __future__ import annotations

import csv
import heapq
import json
import math
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry,
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterBoolean, QgsProcessingParameterEnum,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterNumber,
    QgsProcessingParameterString, QgsProcessingParameterVectorLayer,
    QgsProject, QgsSpatialIndex, QgsVectorFileWriter, QgsVectorLayer,
    QgsWkbTypes, QgsUnitTypes,
)


# [P2 ARCHIVE] Accept exact observed EA interval dates while rejecting malformed calendar values.
def normal_date(v):
    if v is None:
        return None
    s = str(v).strip()
    m = re.fullmatch(r'((?:18|19|20)\d{6})(?:\.0+)?', s)
    if m:
        candidate = m.group(1)
    else:
        m = re.match(r'^((?:18|19|20)\d{2})[-_/ .](\d{1,2})[-_/ .](\d{1,2})(?:[ T].*)?$', s)
        candidate = (f'{int(m.group(1)):04}{int(m.group(2)):02}{int(m.group(3)):02}'
                     if m else None)
    if candidate:
        try:
            datetime.strptime(candidate, '%Y%m%d')
            return candidate
        except ValueError:
            pass
    return None


# [P2 ARCHIVE] Canonicalise numerical-looking BLOCK_ID values for spatial/Risk joins.
def norm_key(v):
    """Mirror the v2 reconciliation's integer-like BLOCK_ID normalization."""
    if v is None:
        return ''
    s = str(v).strip()
    if not s:
        return ''
    try:
        n = float(s)
        if math.isfinite(n) and n.is_integer() and abs(n) < 9e15:
            return str(int(n))
    except (ValueError, OverflowError):
        pass
    return s


# [P2 ARCHIVE] Interpret 0/1 and boolean-like Risk Table values without assuming missing equals false.
def value01(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ('1', '1.0', 'true', 'yes', 't'):
        return 1
    if s in ('0', '0.0', 'false', 'no', 'f'):
        return 0
    return None


# [P2 ARCHIVE] Convert optional numeric observation fields; retain missingness as None.
def as_float(v):
    if v is None or str(v).strip().lower() in ('', 'null', 'none', 'nan'):
        return None
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


# [P2 ARCHIVE] Resolve Stage 4 nominal/effective labels to AD, DS, SF, or UNRESOLVED.
def state(v):
    if v is None:
        return 'UNRESOLVED'
    s = re.sub(r'[^A-Z0-9]+', '_', str(v).strip().upper()).strip('_')
    if s in ('ACTIVE_DOMAIN', 'AD', 'CHANNEL', 'ACTIVE'):
        return 'AD'
    if s in ('DEPOSITIONAL_STORAGE', 'DS', 'STORAGE'):
        return 'DS'
    if s in ('STABILISED_FLOODPLAIN', 'STABILIZED_FLOODPLAIN', 'SF', 'STABLE_FLOODPLAIN'):
        return 'SF'
    return 'UNRESOLVED'


# [P2 ARCHIVE] Diagnostic EA geomorphic source versus fixed-PLACE T1 state.
# [P2 ARCHIVE] An EA island/floodplain source is not ontologically synonymous with DS/SF.
def source_comparison(ea_source, t1):
    """Diagnostic juxtaposition, not ontological validation."""
    s = ea_source.upper()
    if t1 == 'UNRESOLVED':
        return 'PLACE_T1_UNRESOLVED'
    if s == 'ISLAND':
        return 'EA_ISLAND_PLACE_DS' if t1 == 'DS' else 'EA_ISLAND_OTHER_PLACE_STATE'
    if s == 'FLOODPLAIN':
        return 'EA_FLOODPLAIN_PLACE_SF' if t1 == 'SF' else 'EA_FLOODPLAIN_OTHER_PLACE_STATE'
    return 'EA_SOURCE_NO_DIRECT_STATE_EQUIVALENT'


# [P2 ARCHIVE] Assign one mutually exclusive explanatory evidence category to each
# [P2 ARCHIVE] eroded polygon × PLACE × interval, without inferring a physical mechanism.
def attribution(d):
    """One mutually exclusive PRIMARY evidence class, plus independent facets.

    d is a dict with fields assembled below. All classifications describe the
    PLACE interval intersecting an EA erosion polygon, not the physical cause
    of a geomorphic event. Evidence limitations are explicit.
    """
    mask, fp, ds = d['mask'], d['fp_evt'], d['ds_evt']
    t1, t2 = d['t1'], d['t2']
    a2, thr = d['active_t2'], d['active_thr']
    if d['missing']:
        return 'MISSING_RISK_ROW'
    if (mask == 'NEITHER' and (fp == 1 or ds == 1)) or \
            (mask == 'FP_EVENT' and fp != 1) or \
            (mask == 'DS_EVENT' and ds != 1):
        return 'MASK_EVENT_FLAG_CONFLICT'
    if mask == 'FP_EVENT':
        return 'FLAGGED_FP_TO_AD'
    if mask == 'DS_EVENT':
        return 'FLAGGED_DS_TO_AD'
    # From this point: only the NEITHER residual, no event flag.
    if t1 == 'AD' and t2 == 'AD':
        return d.get('ad_persistence_subclass', 'AD_AD_NOMINAL_FIELDS_MISSING')
    if t1 == 'DS' and t2 == 'AD':
        return 'DS_TO_AD_UNFLAGGED'
    if t1 == 'SF' and t2 == 'AD':
        return 'SF_TO_AD_UNFLAGGED'
    if d['fp_risk'] == 1 and t2 == 'AD':
        return 'BROAD_FP_TO_AD_UNFLAGGED'
    if t1 != 'AD' and t1 != 'UNRESOLVED' and t2 == 'AD':
        return 'NONAD_TO_AD_UNFLAGGED'
    if a2 is not None and thr is not None and 0 < a2 < thr and t2 != 'AD':
        return 'T2_BELOW_AD_STATE_THRESHOLD'
    if a2 is not None and abs(a2) <= 1e-9 and t2 != 'AD':
        return 'T2_ZERO_MAPPED_AD_FRACTION'
    if t1 == 'UNRESOLVED' or t2 == 'UNRESOLVED':
        return 'STATE_UNRESOLVED'
    if t1 == t2:
        return 'SAME_NONAD_PLACE_STATE'
    return 'OTHER_STATE_SEQUENCE'


# [P2 ARCHIVE] Quote SQLite column/table identifiers defensively.
def qident(v):
    return '"' + str(v).replace('"', '""') + '"'


# [P2 ARCHIVE] Resolve Risk Table schema variants without silently creating missing fields.
def find_name(names, candidates, required=False):
    lookup = {str(s).lower(): s for s in names}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    if required:
        raise ValueError('Required field absent; expected one of ' + ', '.join(candidates))
    return None


# [P2 ARCHIVE] Resolve the original disk-based Risk Table for read-only SQLite access.
def layer_gpkg_parts(layer):
    source = layer.source()
    path = source.split('|')[0]
    m = re.search(r'(?:^|\|)layername=([^|]+)', source, re.I)
    table = m.group(1) if m else layer.name()
    if Path(path).suffix.lower() not in ('.gpkg', '.sqlite', '.db') or not Path(path).is_file():
        raise QgsProcessingException(
            'Risk Table must be a local, disk-backed GeoPackage/SQLite layer. '
            'Select the original Risk Table inside its source .gpkg (not a virtual/memory layer).')
    return Path(path), table


# [P2 ARCHIVE] Expose an explicit T1→T2 state-pair label for diagnostics.
def sequence(t1, t2):
    return f'{t1}_TO_{t2}'


# [P2 ARCHIVE] Subdivide effective AD→AD by original nominal endpoint evidence.
# [P2 ARCHIVE] These are PLACE-history labels, not proof of persistent exposed material.
def ad_persistence_class(t1, t2, n1, n2, nominal_fields_present=True):
    """Split effective AD->AD by the *nominal* Module 3 endpoint evidence.

    These labels are statements about PLACE state records, NOT proof that
    individual eroded surface patches were previously occupied by AD.
    """
    if t1 != 'AD' or t2 != 'AD':
        return 'NOT_EFFECTIVE_AD_AD'
    if not nominal_fields_present:
        return 'AD_AD_NOMINAL_FIELDS_MISSING'
    return {
        ('AD', 'AD'): 'AD_AD_NOMINAL_AD_AD',
        ('UNRESOLVED', 'AD'): 'AD_AD_NOMINAL_UNRESOLVED_AD',
        ('UNRESOLVED', 'UNRESOLVED'): 'AD_AD_NOMINAL_UNRESOLVED_UNRESOLVED',
        ('AD', 'UNRESOLVED'): 'AD_AD_NOMINAL_AD_UNRESOLVED',
    }.get((n1,n2),'AD_AD_OTHER_NOMINAL_PAIR')


# [P2 ARCHIVE] Check mapped active fraction against the native AD threshold when available.
def observed_ad_support(active_fraction, threshold):
    """Mapped AD fraction meets native PLACE threshold: 1/0/None.

    This is a fractional mapping indicator, not direct source-geometry proof.
    """
    f, t = as_float(active_fraction), as_float(threshold)
    if f is None or t is None or t <= 0:
        return None
    return 1 if f + 1e-10 >= t else 0


# [P2 ARCHIVE] Group detailed erosion attribution into stable cartographic legend classes.
def map_class(mask, attrib, ad_sub, nominal_u_ad):
    """Publication-map grouping, separate from the exhaustive diagnostic flags."""
    if attrib == 'MISSING_RISK_ROW':
        return 'RISK_MISSING_' + mask
    if attrib == 'MASK_EVENT_FLAG_CONFLICT':
        return 'EVENT_FLAG_CONFLICT_' + mask
    if mask == 'FP_EVENT':
        return 'FP_AD_RECOGNISED'
    if mask == 'DS_EVENT':
        return 'DS_AD_RECOGNISED'
    if attrib.startswith('AD_AD_'):
        return 'UNMATCHED_' + ad_sub
    if nominal_u_ad:
        return 'UNMATCHED_NOMINAL_UNRESOLVED_AD_OTHER'
    if attrib == 'T2_BELOW_AD_STATE_THRESHOLD':
        return 'UNMATCHED_AD_THRESHOLD'
    return 'UNMATCHED_OTHER'


# [P2 ARCHIVE] Retain only positive-area polygon components after spatial intersection.
def polygon_components(geometry):
    """Retain positive-area polygon components from GEOS geometry collections."""
    if not geometry or geometry.isEmpty():
        return
    flat = QgsWkbTypes.flatType(geometry.wkbType())
    if flat == QgsWkbTypes.GeometryCollection:
        for component in geometry.asGeometryCollection():
            yield from polygon_components(component)
    elif QgsWkbTypes.geometryType(geometry.wkbType()) == QgsWkbTypes.PolygonGeometry:
        g = QgsGeometry(geometry)
        if not g.isMultipart():
            g.convertToMultiType()
        if not g.isEmpty() and g.area() > 0:
            yield g


# [P2 ARCHIVE] QGIS Processing wrapper: all original inputs read-only;
# [P2 ARCHIVE] writes new dated audit tables, mapped footprints and area QA.
class FRAFEAPlaceTransitionAttributionAudit(QgsProcessingAlgorithm):
    EA = 'ANNUAL_EROSION_POLYGONS'
    GRID = 'KM_BLOCKS'
    RISK = 'ORIGINAL_RISK_TABLE'
    MODE = 'MASK_SELECTION'
    START = 'START_YMD'
    END = 'END_YMD'
    GKEY = 'KM_KEY'
    RKEY = 'RISK_KEY'
    TOL = 'AREA_CLOSURE_TOL_M2'
    REVIEW = 'MAX_REVIEW_CELLS_PER_REASON'
    OUTPUT = 'OUTPUT_PARENT_FOLDER'
    KEEP_DB = 'KEEP_AUDIT_SQLITE'
    MAP_EROSION = 'EXPORT_ALL_EROSION_FOOTPRINTS'
    MAP_CELLS = 'EXPORT_ALL_ERODED_PLACE_CELLS'

    # [P2 ARCHIVE] Specify the authoritative Stage 4 source-field candidates for nominal,
    # [P2 ARCHIVE] effective, event, eligibility and quality evidence. Missing optional fields
    # [P2 ARCHIVE] are diagnosed rather than silently recoded.
    FIELDS = {
        't1': ['M3_EFFECTIVE_STATE_T1_PRIMARY', 'M3_EFFECTIVE_STATE_T1', 'M3_STATE_T1', 'ONTO_STATE_T1'],
        't2': ['M3_EFFECTIVE_STATE_T2_PRIMARY', 'M3_EFFECTIVE_STATE_T2', 'M3_STATE_T2', 'ONTO_STATE_T2'],
        'm3_t1': ['M3_STATE_T1', 'ONTO_STATE_T1'],
        'm3_t2': ['M3_STATE_T2', 'ONTO_STATE_T2'],
        'source_t1': ['M3_STATE_SOURCE_T1', 'STATE_SOURCE_T1'],
        'source_t2': ['M3_STATE_SOURCE_T2', 'STATE_SOURCE_T2'],
        'latent_t1': ['M3_LATENT_STATE_T1'],
        'latent_t2': ['M3_LATENT_STATE_T2'],
        'active_t1': ['M3_ACTIVE_FRAC_T1'],
        'active_t2': ['M3_ACTIVE_FRAC_T2'],
        'pc1': ['P_C1'],
        'pc2': ['P_C2'],
        'active_thr': ['M3_ACTIVE_STATE_THR'],
        'fp_evt': ['FP_REACTIVATE_EVT_PRIMARY'],
        'ds_evt': ['STORAGE_REWORK_EVT_PRIMARY'],
        'strict_sf_evt': ['REACTIVATE_EVT_PRIMARY'],
        'fp_risk': ['FP_REACTIVATE_RISK_SET_PRIMARY'],
        'ds_risk': ['STORAGE_REWORK_RISK_SET_PRIMARY'],
        'fp_eligible': ['FP_REACTIVATE_MODEL_ELIGIBLE_PRIMARY'],
        'ds_eligible': ['STORAGE_REWORK_MODEL_ELIGIBLE_PRIMARY'],
        'fp_exclude': ['FP_REACTIVATE_EXCLUSION_REASON_PRIMARY'],
        'ds_exclude': ['STORAGE_REWORK_EXCLUSION_REASON_PRIMARY'],
        'fp_source': ['FP_REACTIVATE_SOURCE_PRIMARY'],
        'initial': ['INIT_FP_COHORT'],
        'preexisting': ['PREEXISTING_FP_START_PRIMARY'],
        'state_chain_ok': ['M3_STATE_CHAIN_OK'],
        'bridged': ['M3_BRIDGED_TRANS'],
        'mixed_t1': ['M3_MIXED_T1'],
        'mixed_t2': ['M3_MIXED_T2'],
        'qa_severity': ['M3_ANOMALY_SEVERITY'],
        'qa_flags': ['M3_ANOMALY_FLAGS'],
        'qa_process_mismatch': ['QA_PROCESS_DOMAIN_MISMATCH'],
        'qa_unresolved': ['QA_UNRESOLVED_ENDPOINT'],
        'qa_background_overlap': ['QA_BACKGROUND_ACTIVE_OVERLAP'],
    }
    # [P2 ARCHIVE] Declare flags separately from measured active-fraction covariates.
    INTEGER_FIELDS = {'fp_evt', 'ds_evt', 'strict_sf_evt', 'fp_risk', 'ds_risk',
                      'fp_eligible', 'ds_eligible', 'initial', 'preexisting',
                      'state_chain_ok', 'bridged', 'mixed_t1', 'mixed_t2',
                      'qa_process_mismatch', 'qa_unresolved', 'qa_background_overlap'}
    FLOAT_FIELDS = {'active_t1', 'active_t2', 'pc1', 'pc2', 'active_thr'}
    # [P2 ARCHIVE] Define the reproducible full-detail record layout used by the audit CSV.
    DETAIL_FIELDS = [
        'Y1', 'Y2', 'BLOCK_ID', 'EA_SOURCE', 'EVENT_MASK', 'EA_AREA_M2',
        'N_COMPONENTS', 'PLACE_AREA_M2', 'EA_SHARE_OF_PLACE_PCT',
        'ATTRIBUTION', 'EA_SOURCE_VS_T1',
        'T1_PRIMARY', 'T2_PRIMARY', 'M3_T1', 'M3_T2',
        'EFFECTIVE_SEQUENCE','NOMINAL_SEQUENCE','AD_PERSISTENCE_SUBCLASS',
        'ATTRIBUTION_BROAD','MAP_CLASS','NOMINAL_UNRESOLVED_TO_AD',
        'AD_SUPPORT_T1','AD_SUPPORT_T2',
        'M3_STATE_SOURCE_T1', 'M3_STATE_SOURCE_T2',
        'ACTIVE_FRAC_T1', 'ACTIVE_FRAC_T2', 'P_C1', 'P_C2', 'AD_THRESHOLD',
        'FP_EVT_PRIMARY', 'DS_EVT_PRIMARY', 'STRICT_SF_EVT_PRIMARY',
        'FP_RISK_PRIMARY', 'DS_RISK_PRIMARY', 'FP_MODEL_ELIGIBLE', 'DS_MODEL_ELIGIBLE',
        'FP_EXCLUSION', 'DS_EXCLUSION', 'FP_SOURCE_PRIMARY',
        'INIT_FP_COHORT', 'PREEXISTING_FP_START', 'STATE_CHAIN_OK',
        'M3_BRIDGED_TRANS', 'MIXED_T1', 'MIXED_T2',
        'QA_SEVERITY', 'QA_FLAGS', 'QA_PROCESS_MISMATCH', 'QA_UNRESOLVED',
        'QA_BACKGROUND_OVERLAP', 'RISK_ROW_STATUS',
    ]

    # [P2 ARCHIVE] Stable internal QGIS algorithm identifier: retained for project compatibility.
    def name(self):
        return 'fraf_ea_place_transition_attribution_audit_v1_1_1'

    # [P2 ARCHIVE] Human-readable toolbox label; preserved from production source.
    def displayName(self):
        return 'FRAF — EA-to-PLACE Transition Attribution Audit v1.1.1 (complete map + nominal states)'

    # [P2 ARCHIVE] QGIS toolbox grouping (no change in the publication archive copy).
    def group(self):
        return 'FRAF Floodplain Reassemblage'

    # [P2 ARCHIVE] QGIS processing provider grouping (preserved).
    def groupId(self):
        return 'fraf_floodplain_reassemblage'

    # [P2 ARCHIVE] Create the same algorithm class used in the source script.
    def createInstance(self):
        return FRAFEAPlaceTransitionAttributionAudit()

    # [P2 ARCHIVE] Describe input semantics and the attribution limits in the toolbox UI.
    def shortHelpString(self):
        return (
            'Area-weighted cause/observability triage of EA erosion vs PLACE PRIMARY '
            'transitions. Inputs: annual ea_erosion_matrix_annual OR ea_erosion_neither_annual '
            'from reconciliation v2, KM_blocks, ORIGINAL full Risk Table. Does not need '
            'dated EA layers or the new sensitivity Risk Table. Writes source/state/event '
            'audit, PLACE-level detail, area checks, and prioritised map review cells. '
            'Includes full eroded-fragment and PLACE maps, nominal/effective state sequences, '
            'and AD-persistence subtypes. Maps describe observed polygon erosion, not '
            'vertical scour or a fourth geomorphic state.')

    # [P2 ARCHIVE] Declare EA, grid, original Risk Table, date, QA and mapping parameters.
    # [P2 ARCHIVE] The ALL masks choice includes FP_EVENT, DS_EVENT and NEITHER erosion.
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.EA, 'Annual polygons: ea_erosion_matrix_annual OR ea_erosion_neither_annual (v2.x)',
            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.GRID, 'Original fixed KM_blocks polygon grid (150 m)',
            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.RISK, 'Original complete Stage 4 Risk Table (not sensitivity-only)',
            [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterEnum(
            self.MODE, 'EA EVENT_MASK categories to investigate',
            ['NEITHER only (residual diagnosis)', 'ALL EA erosion: FP_EVENT + DS_EVENT + NEITHER (complete map)'], defaultValue=1))
        self.addParameter(QgsProcessingParameterString(
            self.START, 'First interval start YYYYMMDD (blank = all available)',
            optional=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterString(
            self.END, 'Final interval end YYYYMMDD (blank = all available)',
            optional=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterString(
            self.GKEY, 'KM_blocks key', defaultValue='BLOCK_ID'))
        self.addParameter(QgsProcessingParameterString(
            self.RKEY, 'Risk Table key', defaultValue='BLOCK_ID'))
        self.addParameter(QgsProcessingParameterNumber(
            self.TOL, 'Maximum absolute spatial area closure discrepancy (m2)',
            type=QgsProcessingParameterNumber.Double, defaultValue=1.0, minValue=0.0))
        self.addParameter(QgsProcessingParameterNumber(
            self.REVIEW, 'Largest intersected PLACE cells to map PER attribution category',
            type=QgsProcessingParameterNumber.Integer, defaultValue=100, minValue=0, maxValue=5000))
        self.addParameter(QgsProcessingParameterBoolean(
            self.MAP_EROSION, 'Write COMPLETE actual eroded polygon footprints with PLACE-state attribution',
            defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.MAP_CELLS, 'Write ALL eroded 150 m PLACE cells (state, area and fraction; distinct from erosion)',
            defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.KEEP_DB, 'Retain intermediate SQLite audit database (advanced)', defaultValue=False))
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT, 'Parent folder (creates timestamped NEW output subfolder)'))

    # [P2 ARCHIVE] Resolve a required input field or terminate with an explicit schema error.
    @staticmethod
    def _f(layer, candidates, required=True):
        name = find_name(layer.fields().names(), candidates)
        if required and not name:
            raise QgsProcessingException(f'Missing field {candidates}; got {layer.fields().names()[:65]}')
        return name

    # [P2 ARCHIVE] Stop on user cancellation before treating incomplete outputs as valid.
    @staticmethod
    def _cancel(feedback):
        if feedback.isCanceled():
            raise QgsProcessingException('Cancelled; partial outputs are not validated.')

    # [P2 ARCHIVE] Create UTF-8 CSV files using fixed columns for reproducible QA tables.
    @staticmethod
    def _open_csv(path, fields):
        f = open(path, 'w', encoding='utf-8-sig', newline='')
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        return f, w

    # [P2 ARCHIVE] Open the original Risk Table via a read-only SQLite URI.
    @staticmethod
    def _risk_conn(path):
        return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=180)

    # [P2 ARCHIVE] Create a dedicated polygon GeoPackage layer using production schema.
    @staticmethod
    def _new_writer(path, layername, fields, crs, first):
        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = 'GPKG'
        opts.layerName = layername
        opts.fileEncoding = 'UTF-8'
        opts.actionOnExistingFile = (QgsVectorFileWriter.CreateOrOverwriteFile if first else
                                     QgsVectorFileWriter.CreateOrOverwriteLayer)
        writer = QgsVectorFileWriter.create(
            str(path), fields, QgsWkbTypes.MultiPolygon, crs,
            QgsProject.instance().transformContext(), opts)
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            raise QgsProcessingException('Cannot create map layer: '+layername+' '+
                                         (writer.errorMessage() if writer else 'NULL WRITER'))
        return writer

    # [P2 ARCHIVE] Stream two distinct spatial representations from staged exact overlays:
    # [P2 ARCHIVE] the true eroded fragments and the whole PLACE cells containing erosion.
    # [P2 ARCHIVE] A full PLACE footprint is a locator, never eroded-area geometry.
    @classmethod
    def _write_full_maps(cls, db, path, crs, grid_geom, map_erosion, map_cells,
                         tolerance, feedback, mapqa, pairs, input_areas):
        """Exact polygon fragments and full cell locator layer, separately named."""
        # [P2 ARCHIVE] Accumulate independent fragment and PLACE-cell totals for map QA.
        stats = dict(actual_fragments=0, place_cells=0,
                     actual_area_m2=0.0, actual_area_by_pair_m2={},
                     cell_erosion_area_m2=0.0)
        count_by_pair = Counter()
        # [P2 ARCHIVE] Produce actual erosion fragments when full map export is enabled.
        if map_erosion:
            from qgis.core import QgsFields
            fields = QgsFields()
            for name,width in [('Y1',8),('Y2',8),('BLOCK_ID',64),('EA_SOURCE',24),
                               ('EVENT_MASK',18),('ATTRIBUTION',72),('BROAD_CLASS',54),('MAP_CLASS',65),
                               ('EFFECTIVE_SEQ',42),('NOMINAL_SEQ',42),('AD_SUBCLASS',54),
                               ('T1_SOURCE',48),('T2_SOURCE',48)]:
                fields.append(QgsField(name,QVariant.String,len=width))
            for name in ('ERODED_M2','AD_FRAC_T1','AD_FRAC_T2','AD_THR','P_C1','P_C2'):
                fields.append(QgsField(name,QVariant.Double))
            for name in ('NOM_U_AD','AD_SUPPORT_T1','AD_SUPPORT_T2','FP_EVT','DS_EVT'):
                fields.append(QgsField(name,QVariant.Int))
            writer = cls._new_writer(path, 'ea_erosion_by_place_annual', fields, crs, True)
            statement = ("""SELECT f.y1,f.y2,f.bid,f.ea_source,f.mask,f.area,f.wkb,
                           c.attribution,c.broad_class,c.map_class,c.effective_seq,c.nominal_seq,
                           c.ad_subclass,c.nominal_u_ad,c.ad1,c.ad2,c.source_t1,
                           c.source_t2,c.fp_evt,c.ds_evt,c.active1,c.active2,c.ad_thr,
                           c.pc1,c.pc2
                           FROM fragments f JOIN classification c USING(y1,y2,bid,ea_source,mask)
                           ORDER BY f.fid""")
            db.row_factory = sqlite3.Row
            try:
                for n,row in enumerate(db.execute(statement),1):
                    if n % 25000 == 0:
                        if feedback.isCanceled():
                            raise QgsProcessingException('Cancelled during full polygon map write.')
                        feedback.pushInfo(f'[Map] {n:,} exact eroded geometry parts written')
                    geom = QgsGeometry()
                    try:
                        geom.fromWkb(bytes(row['wkb']))
                    except Exception as exc:
                        raise QgsProcessingException(f'WKB read failed for erosion fragment {n}: {exc}')
                    if geom.isEmpty() or QgsWkbTypes.geometryType(geom.wkbType()) != QgsWkbTypes.PolygonGeometry:
                        raise QgsProcessingException(f'Non-polygon in staged fragment {n}')
                    ft=QgsFeature(fields)
                    ft.setGeometry(geom)
                    ft.setAttributes([row['y1'],row['y2'],row['bid'],row['ea_source'],row['mask'],
                                      row['attribution'],row['broad_class'],row['map_class'],row['effective_seq'],
                                      row['nominal_seq'],row['ad_subclass'],
                                      row['source_t1'] or '',row['source_t2'] or '',
                                      float(row['area']),row['active1'],row['active2'],row['ad_thr'],
                                      row['pc1'],row['pc2'],row['nominal_u_ad'],row['ad1'],row['ad2'],
                                      row['fp_evt'],row['ds_evt']])
                    if not writer.addFeature(ft):
                        raise QgsProcessingException('Cannot write eroded fragment to GeoPackage: '+writer.errorMessage())
                    count_by_pair[(row['y1'],row['y2'])] += float(row['area'])
                    stats['actual_fragments'] += 1
            finally:
                del writer
            stats['actual_area_m2'] = sum(count_by_pair.values())
            stats['actual_area_by_pair_m2'] = {'-'.join(p):v for p,v in sorted(count_by_pair.items())}
        # [P2 ARCHIVE] Optionally map whole cells containing erosion as locations, not eroded areas.
        if map_cells:
            from qgis.core import QgsFields
            fields = QgsFields()
            for name,width in [('Y1',8),('Y2',8),('BLOCK_ID',64),
                               ('EFFECTIVE_SEQ',42),('NOMINAL_SEQ',42),
                               ('AD_SUBCLASS',54),('MAP_CLASSES',512),('EVENT_MASKS',70),
                               ('EA_SOURCES',70),('GEOM_ROLE',48)]:
                fields.append(QgsField(name,QVariant.String,len=width))
            for name in ('ERODED_M2','CELL_M2','ERODED_PCT',
                         'AD_FRAC_T1','AD_FRAC_T2','AD_THR','P_C1','P_C2'):
                fields.append(QgsField(name,QVariant.Double))
            fields.append(QgsField('NOM_U_AD',QVariant.Int))
            writer=cls._new_writer(path, 'all_eroded_place_cells_annual',fields,crs,not map_erosion)
            keyed_geo = {key: geo for key,geo in grid_geom.values()}
            sql = ("""SELECT p.y1,p.y2,p.bid,sum(p.area) AS a,g.area AS cell,
                      group_concat(DISTINCT p.mask) AS masks,
                      group_concat(DISTINCT p.ea_source) AS sources,
                      MAX(c.effective_seq) AS eff,MAX(c.nominal_seq) AS nom,
                      MAX(c.ad_subclass) AS adsub,
                      group_concat(DISTINCT c.map_class) AS map_classes,
                      MAX(c.nominal_u_ad) AS nom_u_ad,
                      MAX(c.active1) AS active1,MAX(c.active2) AS active2,
                      MAX(c.ad_thr) AS ad_thr,MAX(c.pc1) AS pc1,MAX(c.pc2) AS pc2
                      FROM pieces p JOIN classification c USING(y1,y2,bid,ea_source,mask)
                      JOIN grid_area g ON g.bid=p.bid GROUP BY p.y1,p.y2,p.bid
                      ORDER BY p.y1,p.y2,p.bid""")
            try:
                for n,row in enumerate(db.execute(sql),1):
                    if n % 25000 == 0:
                        if feedback.isCanceled():
                            raise QgsProcessingException('Cancelled during full PLACE cell map write.')
                    geom=keyed_geo.get(row['bid'])
                    if geom is None:
                        raise QgsProcessingException('Cell geometry missing: '+str(row['bid']))
                    g=QgsGeometry(geom)
                    if not g.isMultipart():
                        g.convertToMultiType()
                    a=float(row['a']); cell=float(row['cell'])
                    if a>cell+tolerance:
                        raise QgsProcessingException('Eroded area exceeds cell area: '+str(row['bid']))
                    ft=QgsFeature(fields);ft.setGeometry(g)
                    ft.setAttributes([row['y1'],row['y2'],row['bid'],row['eff'],row['nom'],
                                      row['adsub'],row['map_classes'],row['masks'],row['sources'],
                                      'WHOLE_PLACE_CELL_NOT_ERODED_POLYGON',
                                      a,cell,100*a/cell if cell>0 else None,
                                      row['active1'],row['active2'],row['ad_thr'],
                                      row['pc1'],row['pc2'],row['nom_u_ad']])
                    if not writer.addFeature(ft):
                        raise QgsProcessingException('Cannot write PLACE cell: '+writer.errorMessage())
                    stats['place_cells'] += 1
                    stats['cell_erosion_area_m2'] += a
            finally:
                del writer
        # [P2 ARCHIVE] Test that mapped annual fragment area closes against the native EA input.
        f,w=cls._open_csv(mapqa,['Y1','Y2','GRID_EROSION_AREA_M2','MAPPED_EROSION_AREA_M2',
                                 'DIFFERENCE_M2','STATUS','NOTE'])
        try:
            for pair in sorted(pairs):
                original=input_areas[pair]
                mapped=count_by_pair[pair] if map_erosion else None
                passed = mapped is None or abs(original-mapped)<=tolerance
                w.writerow(dict(Y1=pair[0],Y2=pair[1],GRID_EROSION_AREA_M2=original,
                                MAPPED_EROSION_AREA_M2=mapped if mapped is not None else '',
                                DIFFERENCE_M2=(mapped-original) if mapped is not None else '',
                                STATUS='PASS' if passed else 'FAIL',
                                NOTE='Exact annual fragments (not cumulative union)' if map_erosion else
                                'Fragment map disabled; only PLACE cells written'))
                if not passed:
                    raise QgsProcessingException('Mapped erosion area failed conservation for '+str(pair))
        finally:
            f.close()
        if map_erosion and stats['actual_fragments']==0:
            raise QgsProcessingException('Fragment mapping produced zero polygons.')
        return stats

    # [P2 ARCHIVE] Orchestrate independent annual EA overlay, risk-state attribution,
    # [P2 ARCHIVE] area closure and bounded-memory export; never refit Cox risk models.
    def processAlgorithm(self, parameters, context, feedback):
        # [P2 ARCHIVE] Resolve the original EA, KM_blocks and Risk Table layers without modification.
        ea = self.parameterAsVectorLayer(parameters, self.EA, context)
        grid = self.parameterAsVectorLayer(parameters, self.GRID, context)
        risk = self.parameterAsVectorLayer(parameters, self.RISK, context)
        mode = self.parameterAsEnum(parameters, self.MODE, context)
        start = self.parameterAsString(parameters, self.START, context).strip()
        end = self.parameterAsString(parameters, self.END, context).strip()
        gkey = self.parameterAsString(parameters, self.GKEY, context).strip()
        rkey = self.parameterAsString(parameters, self.RKEY, context).strip()
        tolerance = float(self.parameterAsDouble(parameters, self.TOL, context))
        review_max = int(self.parameterAsInt(parameters, self.REVIEW, context))
        keep_db = bool(self.parameterAsBoolean(parameters, self.KEEP_DB, context))
        map_erosion = bool(self.parameterAsBoolean(parameters, self.MAP_EROSION, context))
        map_cells = bool(self.parameterAsBoolean(parameters, self.MAP_CELLS, context))
        parent = Path(self.parameterAsString(parameters, self.OUTPUT, context)).expanduser()
        if not all((ea, grid, risk)) or not all(x.isValid() for x in (ea, grid, risk)):
            raise QgsProcessingException('Three valid input layers are required.')
        if start and not normal_date(start):
            raise QgsProcessingException('Invalid START_YMD; use YYYYMMDD or leave blank.')
        if end and not normal_date(end):
            raise QgsProcessingException('Invalid END_YMD; use YYYYMMDD or leave blank.')
        start = normal_date(start) if start else None
        end = normal_date(end) if end else None
        # [P2 ARCHIVE] Guard the observation window before any geometry or eligibility analysis.
        if start and end and start >= end:
            raise QgsProcessingException('START_YMD must precede END_YMD.')
        if not parent.is_dir():
            raise QgsProcessingException('Choose an existing parent output folder.')

        if not ea.crs().isValid() or ea.crs().mapUnits() != QgsUnitTypes.DistanceMeters:
            raise QgsProcessingException('EA layer must be in a valid projected metre-based CRS.')
        if not grid.crs().isValid():
            raise QgsProcessingException('KM_blocks has no valid CRS.')
        if ea.crs() != grid.crs():
            feedback.pushWarning('KM_blocks differs in CRS from EA layer; geometries will be transformed.')
        sfield = self._f(ea, ['EA_SOURCE'])
        mfield = self._f(ea, ['EVENT_MASK'])
        y1f = self._f(ea, ['Y1', 'y1'])
        y2f = self._f(ea, ['Y2', 'y2'])
        gf = self._f(grid, [gkey])
        rp, rt = layer_gpkg_parts(risk)
        # Fail early when users accidentally select cumulative rather than annual data.
        if 'cumulative' in ea.name().lower():
            raise QgsProcessingException('Select an ANNUAL layer, not a cumulative layer.')
        if mode == 1 and 'ea_erosion_neither_annual' in (ea.source()+' '+ea.name()).lower():
            raise QgsProcessingException('Complete-map mode requires ea_erosion_matrix_annual, '
                                         'not ea_erosion_neither_annual (which contains only '
                                         'unmatched erosion).')
        # For predictability, read the source table via read-only SQLite without modifying it.
        src = self._risk_conn(rp)
        try:
            risktables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if rt not in risktables:
                raise QgsProcessingException(f'Risk SQLite table {rt!r} not found in {rp.name}; '
                                             f'tables include {sorted(risktables)[:30]}')
            names = [r[1] for r in src.execute('PRAGMA table_info(' + qident(rt) + ')')]
            rf = find_name(names, [rkey], required=True)
            ry1 = find_name(names, ['y1', 'Y1', 'Start_ymd', 'START_YMD'], required=True)
            ry2 = find_name(names, ['y2', 'Y2', 'End_ymd', 'END_YMD'], required=True)
        except (sqlite3.Error, ValueError) as exc:
            src.close()
            raise QgsProcessingException(f'Risk Table schema preflight failed: {exc}')
        # [P2 ARCHIVE] Freeze a field lookup against the unchanged original Risk Table schema.
        fmap = {logical: find_name(names, choices) for logical, choices in self.FIELDS.items()}
        if fmap['fp_evt'] is None or fmap['ds_evt'] is None:
            src.close()
            raise QgsProcessingException('Original Risk Table lacks PRIMARY FP/DS event fields.')
        if fmap['t1'] is None or fmap['t2'] is None:
            src.close()
            raise QgsProcessingException('Original Risk Table lacks PRIMARY/effective T1 or T2 state fields.')
        nominal_available = fmap['m3_t1'] is not None and fmap['m3_t2'] is not None
        if not nominal_available:
            src.close()
            raise QgsProcessingException('Both nominal Module 3 endpoint states are required for v1.1.1 '
                                         'AD persistence / Unresolved->AD refinement. Original Risk Table '
                                         'must contain M3_STATE_T1/T2 or ONTO_STATE_T1/T2.')
        if fmap['active_t2'] is None or fmap['active_thr'] is None:
            feedback.pushWarning('T2 active fraction/threshold unavailable: below-threshold class will be restricted.')
        feedback.pushInfo(f'[Schema] Risk Table: {rp.name} | {rt} | '
                          f'{len(names)} fields; PRIMARY states={fmap["t1"]},{fmap["t2"]}.')
        src.close()

        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        # [P2 ARCHIVE] Create a new immutable run directory; script does not overwrite prior results.
        out = parent / f'FRAF_Transition_Attribution_Audit_v1_1_1_{run_id}'
        out.mkdir(parents=False, exist_ok=False)
        dbpath = out / 'working_attribution.sqlite'
        db = sqlite3.connect(str(dbpath), timeout=180)
        db.execute('PRAGMA journal_mode=DELETE')
        db.execute('PRAGMA temp_store=FILE')
        db.execute('PRAGMA synchronous=NORMAL')
        db.execute('PRAGMA busy_timeout=180000')
        # [P2 ARCHIVE] Stage exact EA/PLACE clipped areas by annual interval and source/mask.
        db.execute('CREATE TABLE pieces('
                   'y1 TEXT NOT NULL,y2 TEXT NOT NULL, bid TEXT NOT NULL, '
                   'ea_source TEXT NOT NULL, mask TEXT NOT NULL, '
                   'area REAL NOT NULL, n INTEGER NOT NULL, '
                   'PRIMARY KEY(y1,y2,bid,ea_source,mask)) WITHOUT ROWID')
        db.execute('CREATE TABLE wanted(y1 TEXT NOT NULL,y2 TEXT NOT NULL,bid TEXT NOT NULL,'
                   'PRIMARY KEY(y1,y2,bid)) WITHOUT ROWID')
        db.execute('CREATE TABLE grid_area(bid TEXT PRIMARY KEY, area REAL NOT NULL)')
        # [P2 ARCHIVE] Produce actual erosion fragments when full map export is enabled.
        if map_erosion:
            db.execute('CREATE TABLE fragments(fid INTEGER PRIMARY KEY, y1 TEXT, y2 TEXT, '
                       'bid TEXT, ea_source TEXT, mask TEXT, area REAL, wkb BLOB)')
        db.commit()

        # [P2 ARCHIVE] Record original layer paths, selected mode and interpretation limits.
        manifest = dict(version='1.1.1', run_utc=run_id, input_annual_polygons=ea.source(),
                        input_km_blocks=grid.source(), input_original_risk=risk.source(),
                        mode='NEITHER_ONLY' if mode == 0 else 'ALL_MASKS',
                        start=start, end=end, crs=ea.crs().authid(),
                        map_actual_eroded_footprints=map_erosion, map_all_eroded_cells=map_cells,
                        field_mapping=fmap, risk_key=rf, risk_y1=ry1, risk_y2=ry2,
                        limitations=['Area-weighted PLACE intersection, not attribution of a physical erosion mechanism.',
                                     'EA source floodplain/island classes are not identical to PLACE SF/DS states.',
                                     'A PLACE in an event mask may include erosion of more than one EA source class.',
                                     'NEITHER area is physical EA erosion outside two recognised primary event-cell masks.',
                                     'M3 nominal unresolved->AD is a classification sequence, NOT proof of a new geometric transition.',
                                     'Even nominal AD->AD may use inherited T1 evidence: inspect M3_STATE_SOURCE_T1 and AD fractions.',
                                     'Whole cell map represents locations with erosion; only the fragment map depicts eroded ground.',
                                     'Recorded risk fields alone cannot establish complete dated AD mapping coverage.'])
        # [P2 ARCHIVE] Index the complete fixed PLACE lattice; no thinning or sampling here.
        grid_geom = {}
        grid_index = QgsSpatialIndex()
        if grid.crs() != ea.crs():
            transform = QgsCoordinateTransform(grid.crs(), ea.crs(), QgsProject.instance())
        else:
            transform = None
        feedback.pushInfo('[Grid] Indexing fixed KM_blocks (read-only)...')
        ngrid = 0
        # [P2 ARCHIVE] Retain geometry for exact cell intersection and detect duplicate IDs.
        for f in grid.getFeatures():
            self._cancel(feedback)
            key = norm_key(f[gf])
            if not key or key in grid_geom:
                raise QgsProcessingException(f'KM_blocks has null/duplicate BLOCK_ID: {key!r}')
            geo = QgsGeometry(f.geometry())
            if geo.isEmpty():
                raise QgsProcessingException(f'KM_blocks geometry missing: {key}')
            if transform:
                geo.transform(transform)
            if not geo.isGeosValid():
                geo = geo.makeValid()
            if geo.isEmpty() or geo.area() <= 0:
                raise QgsProcessingException(f'KM_blocks invalid/zero area: {key}')
            grid_geom[f.id()] = (key, geo)
            idx_feature = QgsFeature()
            idx_feature.setId(f.id())
            idx_feature.setGeometry(geo)
            grid_index.addFeature(idx_feature)
            db.execute('INSERT INTO grid_area VALUES (?,?)', (key, float(geo.area())))
            ngrid += 1
        db.commit()
        if not ngrid:
            raise QgsProcessingException('Empty KM_blocks.')
        feedback.pushInfo(f'[Grid] Indexed {ngrid:,} PLACE geometries.')

        # [P2 ARCHIVE] Track every observed annual interval independently before summarising.
        selected_pairs = set()
        included_area = Counter()
        matched_area = Counter()
        source_area = Counter()
        n_input = Counter()
        n_fragments = Counter()
        bad_pairs = Counter()
        insert_buffer = []
        frag_buffer = []
        sql_inc = ('INSERT INTO pieces(y1,y2,bid,ea_source,mask,area,n) VALUES(?,?,?,?,?,?,1) '
                   'ON CONFLICT(y1,y2,bid,ea_source,mask) DO UPDATE SET '
                   'area=area+excluded.area,n=n+1')
        source_invalid_count = 0
        feedback.pushInfo('[Overlay] Intersecting ANNUAL EA polygon parts with KM_blocks...')
        total_features = max(1, int(ea.featureCount()))
        # [P2 ARCHIVE] Stream annual EA erosion polygons; intersect by actual area, not centroids.
        for no, f in enumerate(ea.getFeatures(), 1):
            if no % 250 == 0:
                self._cancel(feedback)
                feedback.setProgress(55.0 * min(1, no/total_features))
            y1, y2 = normal_date(f[y1f]), normal_date(f[y2f])
            if not y1 or not y2 or y1 >= y2:
                raise QgsProcessingException(f'Invalid interval in annual polygon feature id={f.id()}: '
                                             f'{f[y1f]!r},{f[y2f]!r}')
            if (start and y1 < start) or (end and y2 > end):
                continue
            mask = str(f[mfield] or '').strip().upper()
            if mask not in ('NEITHER', 'FP_EVENT', 'DS_EVENT'):
                raise QgsProcessingException(f'Unknown EVENT_MASK {mask!r} for fid {f.id()}')
            if mode == 0 and mask != 'NEITHER':
                continue
            s = str(f[sfield] or 'UNKNOWN').strip().upper()
            if s not in ('FLOODPLAIN', 'ISLAND', 'CHANNEL', 'ACTIVE_DRY', 'UNKNOWN'):
                raise QgsProcessingException(f'Unexpected EA_SOURCE {s!r} for feature {f.id()}')
            geo = QgsGeometry(f.geometry())
            if geo.isEmpty():
                continue
            if not geo.isGeosValid():
                fixed = geo.makeValid()
                if fixed.isEmpty() or abs(fixed.area()-geo.area()) > 0.001:
                    raise QgsProcessingException(f'EA annual feature {f.id()} invalid and unsafe to repair.')
                geo = fixed
                source_invalid_count += 1
            if QgsWkbTypes.geometryType(geo.wkbType()) != QgsWkbTypes.PolygonGeometry:
                raise QgsProcessingException(f'Nonpolygon annual erosion feature {f.id()}')
            pair = (y1, y2)
            selected_pairs.add(pair)
            included_area[pair] += geo.area()
            source_area[(pair,s,mask)] += geo.area()
            n_input[pair] += 1
            engine = QgsGeometry.createGeometryEngine(geo.constGet())
            engine.prepareGeometry()
            for gid in grid_index.intersects(geo.boundingBox()):
                key, cell = grid_geom[gid]
                if not engine.intersects(cell.constGet()):
                    continue
                # Intersect exactly, rather than attributing an entire cell on contact.
                piece = geo.intersection(cell)
                if piece.isEmpty():
                    continue
                a = float(piece.area())
                if not math.isfinite(a) or a < 0:
                    raise QgsProcessingException(f'Nonfinite area: annual feature {f.id()} × {key}')
                if a <= 0:
                    continue
                insert_buffer.append((y1,y2,key,s,mask,a))
                matched_area[pair] += a
                n_fragments[pair] += 1
                if map_erosion:
                    polygon_area = 0.0
                    for polygon in polygon_components(piece):
                        part_area = float(polygon.area())
                        polygon_area += part_area
                        frag_buffer.append((y1,y2,key,s,mask,part_area,
                                            sqlite3.Binary(bytes(polygon.asWkb()))))
                    if abs(polygon_area-a) > max(0.001, 1e-8*a):
                        raise QgsProcessingException(
                            f'Polygon extraction lost area: {pair}, BLOCK_ID={key}: '
                            f'{a:.5f} vs {polygon_area:.5f} m2')
                    if len(frag_buffer) >= 1000:
                        with db:
                            db.executemany('INSERT INTO fragments '
                                           '(y1,y2,bid,ea_source,mask,area,wkb) VALUES(?,?,?,?,?,?,?)',
                                           frag_buffer)
                        frag_buffer.clear()
                if len(insert_buffer) >= 1000:
                    with db:
                        db.executemany(sql_inc, insert_buffer)
                    insert_buffer.clear()
        if insert_buffer:
            with db:
                db.executemany(sql_inc, insert_buffer)
            insert_buffer.clear()
        if map_erosion and frag_buffer:
            with db:
                db.executemany('INSERT INTO fragments '
                               '(y1,y2,bid,ea_source,mask,area,wkb) VALUES(?,?,?,?,?,?,?)',
                               frag_buffer)
            frag_buffer.clear()
        # [P2 ARCHIVE] Abort if the chosen EA interval window yields no observed erosion.
        if not selected_pairs:
            raise QgsProcessingException('No annual polygons selected. Check scope/date and the correct layer.')
        # [P2 ARCHIVE] Persist staged records to disk to avoid holding the full cross-product in memory.
        with db:
            db.execute('INSERT INTO wanted SELECT DISTINCT y1,y2,bid FROM pieces')
        # [P2 ARCHIVE] Only source PLACE × interval rows that actually intersect erosion polygons.
        n_wanted = db.execute('SELECT COUNT(*) FROM wanted').fetchone()[0]
        feedback.pushInfo(f'[Overlay] {len(selected_pairs)} observed intervals, '
                          f'{n_wanted:,} eroded PLACE intervals, {sum(n_fragments.values()):,} exact fragments.')
        if n_wanted == 0:
            raise QgsProcessingException('No positive-area polygon×PLACE intersections.')
        # [P2 ARCHIVE] Require per-interval area conservation against the original EA polygon area.
        for pair in sorted(selected_pairs):
            diff = matched_area[pair] - included_area[pair]
            bad_pairs[pair] = diff
            feedback.pushInfo(f'[Area QA] {pair[0]}->{pair[1]}: '
                              f'EA={included_area[pair]/1e6:.6f} km2; '
                              f'within KM_blocks={matched_area[pair]/1e6:.6f} km2; '
                              f'delta={diff:.3f} m2')
            # Both undercoverage and overlapping KM_block support are fatal.
            if abs(diff) > tolerance:
                raise QgsProcessingException(
                    f'AREA CONSERVATION FAILED {pair}: {diff:.3f} m2 exceeds {tolerance:.3f} m2. '
                    'Check KM_blocks coverage/overlap, CRS and input annual polygons. '
                    f'Partial diagnostics in {out}')

        # Spatial stage is finished; join only intersected keys to authoritative risk.
        feedback.setProgress(56)
        feedback.pushInfo('[Risk] Streaming original Risk Table once; retaining matched PLACE/interval rows...')
        db.execute('CREATE TABLE risk_values(y1 TEXT NOT NULL,y2 TEXT NOT NULL,bid TEXT NOT NULL,'
                   + ','.join(qident(k)+' TEXT' for k in self.FIELDS)
                   + ',PRIMARY KEY(y1,y2,bid)) WITHOUT ROWID')
        db.execute('CREATE TABLE classification(y1 TEXT,y2 TEXT,bid TEXT,ea_source TEXT,mask TEXT,'
                   'attribution TEXT, broad_class TEXT, map_class TEXT, effective_seq TEXT, nominal_seq TEXT,'
                   'ad_subclass TEXT, nominal_u_ad INTEGER, ad1 INTEGER, ad2 INTEGER,'
                   'source_t1 TEXT,source_t2 TEXT,fp_evt INTEGER,ds_evt INTEGER,'
                   'active1 REAL,active2 REAL,ad_thr REAL,pc1 REAL,pc2 REAL,'
                   'PRIMARY KEY(y1,y2,bid,ea_source,mask)) WITHOUT ROWID')
        db.commit()
        # All requested columns are projected, avoiding the source's ~350+ wide columns.
        # [P2 ARCHIVE] Project just the required Risk columns for a memory-safe, read-only join.
        projected = [ry1, ry2, rf] + sorted({x for x in fmap.values() if x})
        select = 'SELECT ' + ','.join(qident(z) for z in projected) + ' FROM ' + qident(rt)
        sql_insert = ('INSERT INTO risk_values VALUES (' + ','.join(['?']*(3+len(self.FIELDS))) + ')')
        source_db = self._risk_conn(rp)
        source_db.row_factory = sqlite3.Row
        source_cur = source_db.execute(select)
        desired_dates = set(selected_pairs)
        matched = 0
        visited = 0
        risk_batch = []
        wanted_cur = db.cursor()
        try:
            # [P2 ARCHIVE] Join on both observation dates and BLOCK_ID; no spatial eligibility filter.
            for rr in source_cur:
                visited += 1
                if visited % 100000 == 0:
                    self._cancel(feedback)
                    feedback.pushInfo(f'[Risk] {visited:,} read, {matched:,} matched')
                y1, y2 = normal_date(rr[ry1]), normal_date(rr[ry2])
                if (y1,y2) not in desired_dates:
                    continue
                key = norm_key(rr[rf])
                if not key:
                    continue
                if not wanted_cur.execute('SELECT 1 FROM wanted WHERE y1=? AND y2=? AND bid=?',
                                          (y1,y2,key)).fetchone():
                    continue
                rec = [y1,y2,key] + [None if fmap[k] is None else rr[fmap[k]]
                                      for k in self.FIELDS]
                risk_batch.append(rec)
                matched += 1
                if len(risk_batch) >= 1000:
                    try:
                        with db:
                            db.executemany(sql_insert, risk_batch)
                    except sqlite3.IntegrityError as exc:
                        raise QgsProcessingException('Duplicate original risk row for '
                                                     '(Y1,Y2,BLOCK_ID): '+str(exc))
                    risk_batch.clear()
            if risk_batch:
                with db:
                    db.executemany(sql_insert, risk_batch)
                risk_batch.clear()
        finally:
            source_db.close()
        feedback.pushInfo(f'[Risk] Scanned {visited:,} original Risk Table rows, '
                          f'matched {matched:,} of {n_wanted:,} eroded PLACE intervals.')

        # Area-weighted place-level diagnostic / independent facets.
        feedback.setProgress(79)
        # [P2 ARCHIVE] Write full audit detail and the Table S1-referenced 02_area_attribution_summary.
        # [P2 ARCHIVE] These files derive from this script, not the scored-risk reconciliation.
        path_detail = out / '01_place_interval_attribution.csv'
        path_summary = out / '02_area_attribution_summary.csv'
        path_area = out / '03_area_and_coverage_QA.csv'
        path_review = out / '04_priority_review_cells.csv'
        path_fields = out / '05_input_field_map.csv'
        path_gpkg = out / '06_priority_review_cells.gpkg'
        path_states = out / '07_ea_source_vs_place_states.csv'
        path_exclusions = out / '08_original_risk_exclusion_areas.csv'
        path_maps = out / '09_annual_erosion_attribution_maps.gpkg'
        path_sequence = out / '10_nominal_effective_sequence_areas.csv'
        path_mapqa = out / '11_mapped_area_QA.csv'
        fdetail, wdetail = self._open_csv(path_detail, self.DETAIL_FIELDS)
        area_group = Counter()
        area_state = Counter()
        area_source = Counter()
        area_exclusion = Counter()
        area_sequence = Counter()
        n_cell_group = Counter()
        per_pair_risk_missing = Counter()
        heaps = defaultdict(list)
        counter_seq = 0
        q = ('SELECT p.y1,p.y2,p.bid,p.ea_source,p.mask,p.area,p.n,g.area as cell_area,'
             + 'r.bid AS risk_hit,' + ','.join('r.'+qident(k) for k in self.FIELDS)
             + ' FROM pieces p LEFT JOIN grid_area g ON g.bid=p.bid '
             'LEFT JOIN risk_values r ON r.y1=p.y1 AND r.y2=p.y2 AND r.bid=p.bid '
             'ORDER BY p.y1,p.y2,p.bid,p.ea_source,p.mask')
        db.row_factory = sqlite3.Row
        fetch_cur = db.execute(q)
        nrows = 0
        classified_buffer = []
        try:
            # [P2 ARCHIVE] Classify each exact erosion fragment using nominal and effective state
            # [P2 ARCHIVE] sequences, original event-mask evidence and independent source labels.
            for row in fetch_cur:
                nrows += 1
                if nrows % 25000 == 0:
                    self._cancel(feedback)
                    feedback.pushInfo(f'[Diagnose] {nrows:,} weighted PLACE/source/mask rows')
                dat = {k: row[k] for k in self.FIELDS}
                missing = row['risk_hit'] is None
                nominal_t1 = state(dat['m3_t1'])
                nominal_t2 = state(dat['m3_t2'])
                effective_t1, effective_t2 = state(dat['t1']), state(dat['t2'])
                eff_seq, nom_seq = sequence(effective_t1,effective_t2), sequence(nominal_t1,nominal_t2)
                ad_subclass = ad_persistence_class(effective_t1,effective_t2,nominal_t1,nominal_t2)
                u_to_ad = int(nominal_t1 == 'UNRESOLVED' and nominal_t2 == 'AD')
                ad1 = observed_ad_support(dat['active_t1'],dat['active_thr'])
                ad2 = observed_ad_support(dat['active_t2'],dat['active_thr'])
                d = dict(mask=row['mask'], missing=missing, ad_persistence_subclass=ad_subclass,
                         fp_evt=value01(dat['fp_evt']), ds_evt=value01(dat['ds_evt']),
                         fp_risk=value01(dat['fp_risk']),
                         t1=effective_t1, t2=effective_t2,
                         active_t2=as_float(dat['active_t2']),
                         active_thr=as_float(dat['active_thr']))
                cls = attribution(d)
                broad_cls = 'PLACE_AD_PERSISTENCE' if cls.startswith('AD_AD_') else cls
                class_for_map = map_class(row['mask'],cls,ad_subclass,u_to_ad)
                classified_buffer.append((row['y1'],row['y2'],row['bid'],row['ea_source'],row['mask'],
                                          cls,broad_cls,class_for_map,eff_seq,nom_seq,ad_subclass,u_to_ad,
                                          ad1,ad2,dat['source_t1'],dat['source_t2'],d['fp_evt'],d['ds_evt'],
                                          as_float(dat['active_t1']),as_float(dat['active_t2']),
                                          as_float(dat['active_thr']),as_float(dat['pc1']),as_float(dat['pc2'])))
                if len(classified_buffer) >= 1500:
                    with db:
                        db.executemany('INSERT INTO classification VALUES ('+','.join(['?']*23)+')',
                                       classified_buffer)
                    classified_buffer.clear()
                contrast = source_comparison(row['ea_source'], d['t1'])
                a = float(row['area'])
                pair = (row['y1'],row['y2'])
                group = (pair[0],pair[1],row['ea_source'],row['mask'],cls)
                area_group[group] += a
                n_cell_group[group] += 1
                area_state[(pair[0],pair[1],row['ea_source'],row['mask'],d['t1'],d['t2'],contrast)] += a
                area_source[(pair[0],pair[1],row['mask'],cls)] += a
                area_sequence[(pair[0],pair[1],row['ea_source'],row['mask'],
                               eff_seq,nom_seq,ad_subclass,cls,str(ad1),str(ad2))] += a
                # Attribute original risk/eligibility/exclusion status by the
                # antecedent PLACE state, not by an EA geometric source label.
                # [P2 ARCHIVE] DS→AD eligibility is separate from broad FP→AD; DS is excluded from FP.
                if d['t1'] == 'DS':
                    candidate = 'DS_TO_AD'
                    eligible = value01(dat['ds_eligible'])
                    risk_flag = value01(dat['ds_risk'])
                    exclusion = dat['ds_exclude']
                # [P2 ARCHIVE] Broad FP includes eligible pre-existing FP and SF only.
                elif d['t1'] == 'SF' or d['fp_risk'] == 1:
                    candidate = 'FP_TO_AD'
                    eligible = value01(dat['fp_eligible'])
                    risk_flag = value01(dat['fp_risk'])
                    exclusion = dat['fp_exclude']
                else:
                    candidate = 'NOT_RESOLVED'
                    eligible = None
                    risk_flag = None
                    exclusion = None
                area_exclusion[(pair[0],pair[1],row['ea_source'],row['mask'],cls,
                                candidate, str(risk_flag),str(eligible),
                                str(exclusion or 'UNKNOWN_OR_NOT_SUPPLIED'))] += a
                if missing:
                    per_pair_risk_missing[pair] += a
                cell_area = float(row['cell_area'])
                if cell_area <= 0 or a > cell_area + tolerance:
                    raise QgsProcessingException(
                        f'Impossible area in {pair} BLOCK_ID={row["bid"]}: '
                        f'EA clipped part {a:.3f} m2, PLACE area {cell_area:.3f} m2. '
                        'Review overlap/duplicate source geometry before interpretation.')
                rec = {
                    'Y1':pair[0],'Y2':pair[1],'BLOCK_ID':row['bid'],
                    'EA_SOURCE':row['ea_source'],'EVENT_MASK':row['mask'],
                    'EA_AREA_M2':a,'N_COMPONENTS':row['n'],
                    'PLACE_AREA_M2':cell_area,
                    'EA_SHARE_OF_PLACE_PCT':100*a/cell_area if cell_area > 0 else '',
                    'ATTRIBUTION':cls,'EA_SOURCE_VS_T1':contrast,
                    'T1_PRIMARY':d['t1'],'T2_PRIMARY':d['t2'],
                    'EFFECTIVE_SEQUENCE':eff_seq,'NOMINAL_SEQUENCE':nom_seq,
                    'AD_PERSISTENCE_SUBCLASS':ad_subclass,'ATTRIBUTION_BROAD':broad_cls,
                    'MAP_CLASS':class_for_map,
                    'NOMINAL_UNRESOLVED_TO_AD':u_to_ad,'AD_SUPPORT_T1':ad1,
                    'AD_SUPPORT_T2':ad2,
                    'M3_T1':nominal_t1, 'M3_T2':nominal_t2,
                    'M3_STATE_SOURCE_T1':dat['source_t1'],
                    'M3_STATE_SOURCE_T2':dat['source_t2'],
                    'ACTIVE_FRAC_T1':dat['active_t1'], 'ACTIVE_FRAC_T2':dat['active_t2'],
                    'P_C1':dat['pc1'],'P_C2':dat['pc2'],
                    'AD_THRESHOLD':dat['active_thr'],
                    'FP_EVT_PRIMARY':d['fp_evt'], 'DS_EVT_PRIMARY':d['ds_evt'],
                    'STRICT_SF_EVT_PRIMARY':value01(dat['strict_sf_evt']),
                    'FP_RISK_PRIMARY':d['fp_risk'],'DS_RISK_PRIMARY':value01(dat['ds_risk']),
                    'FP_MODEL_ELIGIBLE':value01(dat['fp_eligible']),
                    'DS_MODEL_ELIGIBLE':value01(dat['ds_eligible']),
                    'FP_EXCLUSION':dat['fp_exclude'],'DS_EXCLUSION':dat['ds_exclude'],
                    'FP_SOURCE_PRIMARY':dat['fp_source'],
                    'INIT_FP_COHORT':value01(dat['initial']),
                    'PREEXISTING_FP_START':value01(dat['preexisting']),
                    'STATE_CHAIN_OK':value01(dat['state_chain_ok']),
                    'M3_BRIDGED_TRANS':dat['bridged'],
                    'MIXED_T1':value01(dat['mixed_t1']),'MIXED_T2':value01(dat['mixed_t2']),
                    'QA_SEVERITY':dat['qa_severity'],'QA_FLAGS':dat['qa_flags'],
                    'QA_PROCESS_MISMATCH':value01(dat['qa_process_mismatch']),
                    'QA_UNRESOLVED':value01(dat['qa_unresolved']),
                    'QA_BACKGROUND_OVERLAP':value01(dat['qa_background_overlap']),
                    'RISK_ROW_STATUS':'MISSING' if missing else 'MATCHED'
                }
                wdetail.writerow(rec)
                if review_max:
                    counter_seq += 1
                    # Keep top N exact source/mask/PLACE intersection areas per class.
                    heap = heaps[cls]
                    item = (a, counter_seq, dict(rec))
                    if len(heap) < review_max:
                        heapq.heappush(heap, item)
                    elif a > heap[0][0]:
                        heapq.heapreplace(heap, item)
        finally:
            fdetail.close()
        if classified_buffer:
            with db:
                db.executemany('INSERT INTO classification VALUES ('+','.join(['?']*23)+')',
                               classified_buffer)
            classified_buffer.clear()
        feedback.pushInfo(f'[Diagnose] {nrows:,} place/source/mask records, '
                          f'{len(heaps)} attribution categories.')
        if nrows == 0:
            raise QgsProcessingException('No area-attribution records; check inputs.')

        # [P2 ARCHIVE] Annual source × mask × evidence areas feed 02_area_attribution_summary.csv.
        summary_fields = ['Y1','Y2','EA_SOURCE','EVENT_MASK','ATTRIBUTION','AREA_M2',
                          'AREA_KM2','PCT_ANNUAL_SELECTED_EA','PLACE_SOURCE_MASK_RECORDS',
                          'INTERPRETATION_LIMIT']
        fsum, wsum = self._open_csv(path_summary, summary_fields)
        annual_selected = Counter()
        for (y1,y2,s,mask,c),a in area_group.items():
            annual_selected[(y1,y2)] += a
        try:
            for (y1,y2,s,mask,c),a in sorted(area_group.items()):
                wsum.writerow({'Y1':y1,'Y2':y2,'EA_SOURCE':s,'EVENT_MASK':mask,
                               'ATTRIBUTION':c,'AREA_M2':a,'AREA_KM2':a/1e6,
                               'PCT_ANNUAL_SELECTED_EA':100*a/annual_selected[y1,y2]
                                                        if annual_selected[y1,y2] else '',
                               'PLACE_SOURCE_MASK_RECORDS':n_cell_group[y1,y2,s,mask,c],
                               'INTERPRETATION_LIMIT':
                               'PLACE-state evidence only; not independently validated erosion mechanism'})
            for (y1,y2,mask,c),a in sorted(area_source.items()):
                wsum.writerow({'Y1':y1,'Y2':y2,'EA_SOURCE':'ALL_SOURCES',
                               'EVENT_MASK':mask,'ATTRIBUTION':c,'AREA_M2':a,
                               'AREA_KM2':a/1e6,
                               'PCT_ANNUAL_SELECTED_EA':100*a/annual_selected[y1,y2]
                                                       if annual_selected[y1,y2] else '',
                               'PLACE_SOURCE_MASK_RECORDS':'',
                               'INTERPRETATION_LIMIT':'Sum of original geomorphic source classes'})
            # Overall totals (SUM OF OBSERVED INTERVAL AREAS; NOT unique spatial footprints).
            totals = Counter()
            total_all = sum(annual_selected.values())
            for (y1,y2,s,mask,c),a in area_group.items():
                totals[s,mask,c] += a
            for (s,mask,c),a in sorted(totals.items()):
                wsum.writerow({'Y1':'ALL','Y2':'ALL','EA_SOURCE':s,'EVENT_MASK':mask,
                               'ATTRIBUTION':c,'AREA_M2':a,'AREA_KM2':a/1e6,
                               'PCT_ANNUAL_SELECTED_EA':100*a/total_all if total_all else '',
                               'PLACE_SOURCE_MASK_RECORDS':'',
                               'INTERPRETATION_LIMIT':'Summed annual erosion area; repeats across years counted'})
        finally:
            fsum.close()

        # [P2 ARCHIVE] Check both original geometry-to-grid and grid-to-attributed area closures.
        fqa, wqa = self._open_csv(path_area,[
            'Y1','Y2','EA_INPUT_AREA_M2','GRID_INTERSECTION_AREA_M2',
            'ATTRIBUTED_AREA_M2','GRID_MINUS_INPUT_M2','ATTRIBUTED_MINUS_GRID_M2',
            'MISSING_RISK_AREA_M2','INPUT_FEATURES','INTERSECTION_PARTS','STATUS'])
        try:
            for p in sorted(selected_pairs):
                attributed = annual_selected[p]
                delta1 = matched_area[p]-included_area[p]
                delta2 = attributed-matched_area[p]
                status = 'PASS' if abs(delta1) <= tolerance and abs(delta2) <= tolerance else 'FAIL'
                wqa.writerow({'Y1':p[0],'Y2':p[1],
                              'EA_INPUT_AREA_M2':included_area[p],
                              'GRID_INTERSECTION_AREA_M2':matched_area[p],
                              'ATTRIBUTED_AREA_M2':attributed,
                              'GRID_MINUS_INPUT_M2':delta1,
                              'ATTRIBUTED_MINUS_GRID_M2':delta2,
                              'MISSING_RISK_AREA_M2':per_pair_risk_missing[p],
                              'INPUT_FEATURES':n_input[p],
                              'INTERSECTION_PARTS':n_fragments[p],
                              'STATUS':status})
                if status == 'FAIL':
                    raise QgsProcessingException('Post-attribution area mismatch for '+str(p))
        finally:
            fqa.close()

        fmap_file, fmap_csv = self._open_csv(path_fields, ['LOGICAL','RISK_FIELD','AVAILABLE'])
        try:
            for logical, actual in fmap.items():
                fmap_csv.writerow({'LOGICAL':logical,'RISK_FIELD':actual or '',
                                   'AVAILABLE':1 if actual else 0})
        finally:
            fmap_file.close()

        # [P2 ARCHIVE] Retain EA geomorphic source and PLACE state as independent analytical axes.
        fstates, wstates = self._open_csv(path_states, [
            'Y1','Y2','EA_SOURCE','EVENT_MASK','PLACE_T1','PLACE_T2',
            'EA_SOURCE_T1_COMPARISON','AREA_M2','AREA_KM2',
            'WARNING'])
        try:
            for (y1,y2,es,mask,t1,t2,comp),a in sorted(area_state.items()):
                wstates.writerow({'Y1':y1,'Y2':y2,'EA_SOURCE':es,'EVENT_MASK':mask,
                                  'PLACE_T1':t1,'PLACE_T2':t2,
                                  'EA_SOURCE_T1_COMPARISON':comp,'AREA_M2':a,
                                  'AREA_KM2':a/1e6,
                                  'WARNING':'EA source and PLACE three-state categories are non-equivalent'})
        finally:
            fstates.close()
        # [P2 ARCHIVE] Report original model eligibility/exclusion separately from mapped erosion.
        fexc, wexc = self._open_csv(path_exclusions, [
            'Y1','Y2','EA_SOURCE','EVENT_MASK','ATTRIBUTION','POSSIBLE_TRANSITION',
            'RAW_RISK_SET_PRIMARY','MODEL_ELIGIBLE_PRIMARY','EXCLUSION_REASON',
            'AREA_M2','AREA_KM2'])
        try:
            for (y1,y2,es,mask,cls,cand,risk_flag,eligible,excl),a in sorted(area_exclusion.items()):
                wexc.writerow({'Y1':y1,'Y2':y2,'EA_SOURCE':es,'EVENT_MASK':mask,
                               'ATTRIBUTION':cls,'POSSIBLE_TRANSITION':cand,
                               'RAW_RISK_SET_PRIMARY':risk_flag,
                               'MODEL_ELIGIBLE_PRIMARY':eligible,
                               'EXCLUSION_REASON':excl,
                               'AREA_M2':a,'AREA_KM2':a/1e6})
        finally:
            fexc.close()

        # Additional cross-tab: independent effective and nominal sequence axes.
        # [P2 ARCHIVE] Cross-tab effective and nominal state sequences without treating them as
        # [P2 ARCHIVE] interchangeable observation types.
        fseq, wseq = self._open_csv(path_sequence, [
            'Y1','Y2','EA_SOURCE','EVENT_MASK','EFFECTIVE_SEQUENCE','NOMINAL_SEQUENCE',
            'AD_PERSISTENCE_SUBCLASS','ATTRIBUTION','AD_SUPPORT_T1','AD_SUPPORT_T2',
            'AREA_M2','AREA_KM2'])
        try:
            for (y1,y2,es,mask,eff,nom,sub,cls,ad1,ad2),a in sorted(area_sequence.items()):
                wseq.writerow(dict(Y1=y1,Y2=y2,EA_SOURCE=es,EVENT_MASK=mask,
                                  EFFECTIVE_SEQUENCE=eff,NOMINAL_SEQUENCE=nom,
                                  AD_PERSISTENCE_SUBCLASS=sub,ATTRIBUTION=cls,
                                  AD_SUPPORT_T1=ad1,AD_SUPPORT_T2=ad2,
                                  AREA_M2=a,AREA_KM2=a/1e6))
        finally:
            fseq.close()

        # Review geometries depict entire PLACEs for manual checking, never
        # misrepresented as the smaller EA eroded fragment footprints.
        review_fields = ['Y1','Y2','BLOCK_ID','EA_SOURCE','EVENT_MASK','EA_AREA_M2',
                         'ATTRIBUTION','T1_PRIMARY','T2_PRIMARY','ACTIVE_FRAC_T2',
                         'AD_THRESHOLD','FP_EXCLUSION','DS_EXCLUSION','PLACE_AREA_M2']
        # [P2 ARCHIVE] Provide bounded visual review candidates; not a statistical sample.
        fp, wc = self._open_csv(path_review, review_fields)
        review_rows = []
        try:
            for cls, heap in sorted(heaps.items()):
                for a, _, rec in sorted(heap, reverse=True):
                    wc.writerow(rec)
                    review_rows.append(rec)
        finally:
            fp.close()
        # Writer uses a new file and is explicitly closed before returning.
        review_layer = QgsVectorLayer('MultiPolygon?crs=' + ea.crs().authid(),
                                      'priority_review_cells', 'memory')
        review_layer.dataProvider().addAttributes([
            QgsField('Y1', QVariant.String, len=8),
            QgsField('Y2', QVariant.String, len=8),
            QgsField('BLOCK_ID', QVariant.String, len=64),
            QgsField('EA_SOURCE', QVariant.String, len=20),
            QgsField('EVENT_MASK', QVariant.String, len=16),
            QgsField('ATTRIBUTION', QVariant.String, len=48),
            QgsField('T1_STATE', QVariant.String, len=16),
            QgsField('T2_STATE', QVariant.String, len=16),
            QgsField('ERODED_M2', QVariant.Double),
            QgsField('CELL_M2', QVariant.Double),
            QgsField('AD_FRAC_T2', QVariant.Double),
            QgsField('AD_THR', QVariant.Double),
        ])
        review_layer.updateFields()
        # Build one-off BLOCK_ID→geometry lookup only for the selected review set.
        needed_review = {rec['BLOCK_ID'] for rec in review_rows}
        key_to_geom = {k: g for k,g in grid_geom.values() if k in needed_review}
        batch = []
        for rec in review_rows:
            g = key_to_geom.get(rec['BLOCK_ID'])
            if g is None:
                raise QgsProcessingException('Missing grid geometry for review '+rec['BLOCK_ID'])
            piece = QgsGeometry(g)
            if not piece.isMultipart():
                piece.convertToMultiType()
            f = QgsFeature(review_layer.fields())
            f.setGeometry(piece)
            f.setAttributes([rec['Y1'],rec['Y2'],rec['BLOCK_ID'],rec['EA_SOURCE'],
                             rec['EVENT_MASK'],rec['ATTRIBUTION'],rec['T1_PRIMARY'],
                             rec['T2_PRIMARY'],rec['EA_AREA_M2'],rec['PLACE_AREA_M2'],
                             as_float(rec['ACTIVE_FRAC_T2']),as_float(rec['AD_THRESHOLD'])])
            batch.append(f)
            if len(batch) >= 500:
                if not review_layer.dataProvider().addFeatures(batch)[0]:
                    raise QgsProcessingException('Unable to append review geometry')
                batch.clear()
        if batch and not review_layer.dataProvider().addFeatures(batch)[0]:
            raise QgsProcessingException('Unable to append final review geometry')
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'priority_review_PLACE_cells'
        options.fileEncoding = 'UTF-8'
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            review_layer, str(path_gpkg), QgsProject.instance().transformContext(), options)
        if result[0] != QgsVectorFileWriter.NoError:
            raise QgsProcessingException('Writing review GeoPackage failed: '+str(result))

        # Stream BOTH map types from the disk-backed exact overlay and its
        # classified PLACE keys; do not depict an entire cell as eroded ground.
        # [P2 ARCHIVE] Export exact annual erosion fragments and distinct eroded-PLACE locators.
        map_stats = self._write_full_maps(
            db, path_maps, ea.crs(), grid_geom, map_erosion, map_cells,
            tolerance, feedback, path_mapqa, selected_pairs, matched_area)

        # [P2 ARCHIVE] Complete the source and QA manifest only after checks and exports.
        manifest.update(dict(selected_intervals=[list(p) for p in sorted(selected_pairs)],
                             km_blocks=ngrid, eroded_place_intervals=n_wanted,
                             original_risk_rows_scanned=visited, risk_rows_matched=matched,
                             place_source_mask_detail_rows=nrows,
                             ea_input_selected_area_m2=sum(included_area.values()),
                             area_within_grid_m2=sum(matched_area.values()),
                             missing_risk_row_area_m2=sum(per_pair_risk_missing.values()),
                             annual_area_is_sum_not_unique=True,
                             source_geometry_repairs=source_invalid_count,
                             summed_absolute_area_closure_error_m2=sum(abs(x) for x in bad_pairs.values()),
                             review_cells=len(review_rows),
                             map_statistics=map_stats,
                             outputs=[x.name for x in (path_detail,path_summary,path_area,
                                                        path_review,path_fields,path_gpkg,path_states,path_exclusions,
                                                        path_sequence,path_mapqa) +
                                                        ((path_maps,) if (map_erosion or map_cells) else ())]))
        (out / '00_manifest.json').write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        db.close()
        if not keep_db:
            os.unlink(dbpath)
        feedback.setProgress(100)
        feedback.pushInfo('[Completed] Input annual area=%.4f km2, spatially matched=%.4f km2, '
                          'missing Risk Table coverage=%.4f km2; review %s' % (
                            sum(included_area.values())/1e6,
                            sum(matched_area.values())/1e6,
                            sum(per_pair_risk_missing.values())/1e6, str(out)))
        return {self.OUTPUT: str(out), 'OUTPUT_MANIFEST': str(out/'00_manifest.json'),
                'OUTPUT_SUMMARY_CSV': str(path_summary),
                'OUTPUT_DETAIL_CSV': str(path_detail),
                'OUTPUT_AREA_QA_CSV': str(path_area),
                'OUTPUT_REVIEW_GPKG': str(path_gpkg),
                'OUTPUT_ALL_MAPS_GPKG': str(path_maps) if (map_erosion or map_cells) else '',
                'OUTPUT_SEQUENCES_CSV': str(path_sequence),
                'OUTPUT_MAP_QA_CSV': str(path_mapqa)}
