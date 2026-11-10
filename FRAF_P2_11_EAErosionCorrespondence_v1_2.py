# -*- coding: utf-8 -*-
# ============================================================================
# PAPER 2 REPRODUCIBILITY ARCHIVE — COMMENTED SOURCE (NO LOGIC MODIFICATIONS)
# Archive filename : FRAF_P2_11_EAErosionCorrespondence_v1_2.py
# Source version   : Module 5d–EA Erosion Susceptibility Correspondence v1.2
# Archive role     : Compare retrospective spatial susceptibility rankings with
#                    subsequently mapped physical erosion, not a new hazard fit.
# Environment      : QGIS Python Processing (source specifies QGIS 3.40+).
#
# PLACE IN THE FRAF PAPER 2 ANALYTICAL WORKFLOW
# ----------------------------------------------
# 01–05: Reconstruct channel/EA history, fixed-place states, assemblage histories,
#        antecedent covariates, and transition-specific interval risk sets.
# 06–08: Fit transition models, generate predictions and map scored-place ranks.
# 09–10: Construct and verify *organisational transition* event footprints.
# 11:    THIS SCRIPT independently compares scored T1 rankings with *all mapped*
#        Module 3A physical erosion in the subsequent observation interval.
#
# IMPORTANT POPULATION AND PROCESS DISTINCTIONS
# ---------------------------------------------
# - FP->AD here denotes the eligible broad floodplain prediction population:
#   pre-existing eligible floodplain + Stabilised Floodplain (SF), excluding DS.
# - DS->AD is a separate Depositional Storage reworking population.
# - Neither population is a fourth assemblage state, and their scored place
#   support must be inherited from the correct model at the forecast origin.
# - The script intersects independently mapped EA erosion with susceptibility
#   zones. EA erosion may include in-channel reworking outside both populations.
# - Subsequent EA erosion should never be relabelled automatically as a realised
#   FP->AD or DS->AD state transition or as an extra Cox event.
#
# TEMPORAL DESIGN
# ---------------
# Inputs for ranking: model-labelled, eligible, successfully scored T1 places.
# Evaluation target: EA physical-erosion polygons observed over (Y1, Y2].
# No T2 outcome geometry is used to construct eligibility or susceptibility.
# One river / forecast origin / observation interval is analysed per invocation.
#
# COMPARISON DENOMINATORS
# -----------------------
# * EA eligible capture: area of erosion INSIDE a ranked zone divided by
#   erosion inside that model's full T1 eligible/scored support.
# * Spatial enrichment: EA eligible capture divided by selected scored-area
#   fraction (relative concentration; not transition probability).
# * Total corridor erosion capture: erosion inside that ranked zone divided by
#   ALL selected EA erosion within optional valid-observation support.
# The first two evaluate ranking *within the modelled support*; the third
# contextualises how much overall physical erosion the modelled support covers.
#
# INPUT/PROVENANCE SAFEGUARDS
# ---------------------------
# Prefer complete Module 5c continuous output to an analyst-prepared scored mask;
# the script reconstructs eligibility with P_STATUS='predicted', P_RISKSET=1.
# Verify zone P_PCTL geometry against the same continuous model when possible.
# Select EA interval by TWO metadata dates or explicitly attest a single-interval
# layer; with only one endpoint field, every feature must match that endpoint.
# A timestamped output directory records CSV summaries, QA, a source manifest,
# an optional GeoPackage, and STARTED/COMPLETED/FAILED status. Source untouched.
#
# ARCHIVAL INVARIANTS
# -------------------
# Original QGIS Processing algorithm ID, UI labels, field names, numerical
# tolerances, spatial operations, output schemas, and manifest literals retained.
# Only Python comments have been inserted. See final response for validation.
# ============================================================================
"""FRAF Module 5d–EA Erosion Susceptibility Correspondence v1.2.


Version 1.2 fixes handling of Module 3A EA_processes layers with only one
recognised interval endpoint field. When EA_IS_SINGLE_INTERVAL is checked,
the available endpoint is tested against all selected EA features; the absent
endpoint relies on the explicit single-interval user attestation. Combined
EA layers with both endpoints are still filtered by both dates; partially
dated mixed-interval EA layers are rejected. The correction does not modify
model scores, susceptibility polygons or physical-erosion classification.

QGIS 3.40+ standalone Processing script (intended for QGIS 3.44.9).
Run via Processing Toolbox > Scripts > Open Existing Script.

Single forecast interval per invocation. Analyse FP->AD and/or DS->AD by
intersecting antecedently defined, scored T1 susceptibility zones with the
independent, *subsequent* Module 3A EA physical-erosion polygons. No new Cox
fit, no erosion model, no reinterpretation of 5d transition footprints.

For each pathway supply its top-percentile zones AND one of:
  (preferred) the FULL Module 5c continuous prediction polygon layer;
  (legacy) a manually constructed full T1 eligible and scored risk mask.
The preferred mode internally selects P_STATUS='predicted' and P_RISKSET=1,
checks forecast, interval, transition and model metadata, and reconstructs the
complete scored PLACE support. It never infers support from top-percent zones.
Optionally check high-susceptibility zone geometry against the ranks in the
matching continuous 5c layer to detect accidental P1/P2 mixing.


The script intentionally does not generate risk masks from T2 event labels,
observed transitions, future channel geometry or the historical channel union.

Outputs (timestamped new folder): summary.csv, qa.csv, manifest.json and an
optional GIS GeoPackage with named overlay components. Never overwrites source.

No claim that actual EA erosion is a realised FP->AD or DS->AD transition.
"""
from __future__ import annotations
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import processing
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterVectorLayer, QgsProcessingParameterString,
    QgsProcessingParameterBoolean, QgsProcessingParameterFolderDestination,
    QgsProcessingParameterFile, QgsProcessingOutputFile,
    QgsVectorLayer, QgsWkbTypes, QgsUnitTypes, QgsProject, QgsFeature,
    QgsFeatureRequest, QgsVectorFileWriter, QgsProcessingUtils,
)


# Standardise optional user/attribute text without changing its semantic content.
def _norm(x):
    return str(x if x is not None else '').strip()


# Normalise incoming dates to YYYYMMDD for strict observation-interval matching.
# Year-only labels adopt 1 January, matching the annual observation convention.
def _date(x):
    s = _norm(x)
    if not s:
        return ''
    # Remove any timestamp time-of-day before interpreting an observed date label.
    s = s.split('T')[0].split(' ')[0]
    # Eight-digit YYYYMMDD values are validated against a real calendar date.
    m = re.fullmatch(r'(19|20)\d{6}', s)
    if m:
        try:
            return datetime.strptime(s, '%Y%m%d').strftime('%Y%m%d')
        except ValueError:
            return ''
    # Also accept YYYY-MM-DD, YYYY/MM/DD, and YYYY.MM.DD representations.
    m = re.fullmatch(r'((?:19|20)\d{2})[-/.](\d{1,2})[-/.](\d{1,2})', s)
    if m:
        try:
            return datetime(int(m[1]), int(m[2]), int(m[3])).strftime('%Y%m%d')
        except ValueError:
            return ''
    # Year-only values are explicitly converted to 1 January; others fail closed.
    return (s+'0101' if re.fullmatch(r'(19|20)\d{2}', s) else '')


# Parse top-scored-area percentages, removing duplicates and rejecting invalid values.
# Top 10% corresponds to a >=90th-percentile risk-rank zone.
def _top_list(text):
    vals = []
    # Accept commas, semicolons and whitespace in the threshold input.
    for v in re.split(r'[,;\s]+', text.strip()):
        if not v:
            continue
        # Fractional top-area thresholds are permitted; reject NaN and infinity.
        x = float(v)
        if not math.isfinite(x) or not 0 < x <= 100:
            raise ValueError('Top-area thresholds must lie in (0,100]')
        # Treat near-identical decimal thresholds as duplicates.
        if all(abs(x-a)>1e-8 for a in vals):
            vals.append(x)
    if not vals:
        raise ValueError('Enter at least one top-area threshold')
    return sorted(vals)


# Produce a filesystem-safe identifier for output filenames and GIS layer names.
def _tag(v):
    return re.sub('[^A-Za-z0-9_]+', '_',str(v)).strip('_')[:55] or 'NA'


# Classify a transition label into broad FP->AD or storage DS->AD shorthand.
# Do not treat strict SF->AD as broad FP->AD by implication.
def _pathway(x):
    # Normalise punctuation/case before identifying prediction pathway semantics.
    s = re.sub('[^a-z0-9]+','',_norm(x).lower())
    if 'depositionalstorage' in s and ('active' in s or 'rework' in s):
        return 'DS'
    if 'dsad' in s or 'storage_rework' in s:
        return 'DS'
    if 'fpad' in s or 'fpreactivate' in s or 'eligiblefloodplain' in s or 'floodplainreactivation' in s or 'broadfp' in s:
        return 'FP'
    return ''


# Resolve optional source schema variants by case-insensitive field name.
def _firstfield(layer, names):
    # Use actual provider field casing when building subsequent expressions.
    exact = {n.lower():n for n in layer.fields().names()}
    for n in names:
        if n.lower() in exact:
            return exact[n.lower()]
    return None


# Convert numerical attributes safely; non-finite/missing values remain NULL.
def _num(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None


class FRAFModule5dEAErosionSusceptibilityCorrespondenceV12(QgsProcessingAlgorithm):
    # Preserve the original QGIS Processing registry ID for saved workflow compatibility.
    def name(self):
        return 'fraf_module5d_ea_susceptibility_correspondence_v1_2'

    # Keep the original user-facing QGIS tool label; archive naming is filename-only.
    def displayName(self):
        return 'FRAF 5D–EA: susceptibility vs erosion v1.2 (direct 5c continuous)'

    # Retain the registered QGIS Processing toolbox group.
    def group(self):
        return 'FRAF Floodplain Reassemblage'

    # Retain the original toolbox group identifier.
    def groupId(self):
        return 'fraf_floodplain_reassemblage'

    # QGIS Processing factory must instantiate the same algorithm class.
    def createInstance(self):
        return FRAFModule5dEAErosionSusceptibilityCorrespondenceV12()

    # Expose the original module docstring and user guidance in QGIS Processing help.
    def shortHelpString(self):
        return (__doc__ + '\n\n'
            'Supply one forecast origin (T25/T30/T35) at a time. Use the original '
            'Module 5c2 percentile_zones or their copied 5d version; supply '
            'the matching full Module 5c continuous prediction layer (preferred) or a '
            'separately prepared full T1 scored/eligible mask. Select exactly one '
            'source for each pathway. With continuous input, P_STATUS=predicted '
            'and P_RISKSET=1 are selected automatically. '
            'EA input may be a combined dated layer (y1/y2 are used to filter) '
            'or a prefiltered SINGLE interval layer; partial/missing EA date metadata requires explicit confirmation. A present endpoint date is validated. '
            'Default EA class = erosion (island_erosion may be added explicitly). '
            'The optional 5d CSV appends already computed transition-footprint '
            'capture alongside the NEW physical-erosion metrics.')

    # Declare source layers, interval/model identifiers, QA options, and outputs.
    # A selected FP/DS pathway needs both ranked zones and exactly one full risk source.
    def initAlgorithm(self, config=None):
        # Local helper reduces repeated QGIS polygon parameter declarations.
        p = lambda name, title, optional=False: self.addParameter(
            QgsProcessingParameterVectorLayer(name,title,[QgsProcessing.TypeVectorPolygon],optional=optional))
        # FP->AD input set. FP eligibility includes qualifying pre-existing FP and SF, not DS.
        p('FP_ZONES','FP→AD percentile_zones (one model and origin; optional)',True)
        p('FP_CONTINUOUS','FP→AD FULL Module 5c continuous prediction (preferred; all places)',True)
        p('FP_RISK','FP→AD manually built FULL eligible + scored risk mask (ALTERNATIVE)',True)
        # DS->AD input set. It is a distinct scored population, not a subset of broad FP.
        p('DS_ZONES','DS→AD percentile_zones (one model and origin; optional)',True)
        p('DS_CONTINUOUS','DS→AD FULL Module 5c continuous prediction (preferred; all places)',True)
        p('DS_RISK','DS→AD manually built FULL eligible + scored risk mask (ALTERNATIVE)',True)
        # Subsequent mapped EA erosion is a separate observed geometry target.
        p('EA_EROSION','Module 3A EA erosion polygons (single interval or dated combined)')
        # Support polygon (if supplied) clips the EA target before any denominator is set.
        p('VALID_SUPPORT','Valid EA observation/support corridor (optional; clips ALL erosion)',True)
        self.addParameter(QgsProcessingParameterString('RIVER','River name',defaultValue='Mamore'))
        self.addParameter(QgsProcessingParameterString('FORECAST','Forecast origin',defaultValue='T35'))
        # Use exact Y1/Y2 observation dates rather than assuming a fixed annual lag.
        self.addParameter(QgsProcessingParameterString('Y1','Observed interval start (YYYYMMDD or YYYY)',defaultValue='20200101'))
        self.addParameter(QgsProcessingParameterString('Y2','Observed interval end (YYYYMMDD or YYYY)',defaultValue='20210101'))
        self.addParameter(QgsProcessingParameterString('FP_MODEL','FP model label (AUTO = read P_MODEL from continuous)',defaultValue='AUTO'))
        self.addParameter(QgsProcessingParameterString('DS_MODEL','DS model label (AUTO = read P_MODEL from continuous)',defaultValue='AUTO'))
        # Thresholds describe ranked scored area, not predicted probability values.
        self.addParameter(QgsProcessingParameterString('TOP_PCTS','Top scored-area percentages',defaultValue='10,20,30'))
        self.addParameter(QgsProcessingParameterString('EA_CLASS_FIELD','EA process class field; AUTO searches EA_clean / EA / PROCESS',defaultValue='AUTO'))
        # Only the selected erosion EA classes contribute to physical erosion.
        self.addParameter(QgsProcessingParameterString('EROSION_CLASSES','Allowed EA erosion classes, case-insensitive',defaultValue='erosion'))
        # Single-interval confirmation cannot substitute for conflicting observed dates.
        self.addParameter(QgsProcessingParameterBoolean('EA_IS_SINGLE_INTERVAL','Confirm EA layer is single Y1–Y2 interval if endpoint date metadata is absent or incomplete',defaultValue=False))
        # Recommended QA compares percentile-zone geometry against the 5c model scores.
        self.addParameter(QgsProcessingParameterBoolean('VERIFY_ZONE_RANKS','Check zone geometry against 5c P_PCTL ranks (recommended)',defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean('SAVE_SPATIAL','Write overlay layers to GeoPackage',defaultValue=True))
        # 5d CSV is optional contextual output, never used to define the erosion target.
        self.addParameter(QgsProcessingParameterFile('SUMMARY_5D','Existing 5D verification summary CSV (optional)',behavior=QgsProcessingParameterFile.File,fileFilter='CSV (*.csv)',optional=True))
        # New results are written under a fresh timestamped subdirectory.
        self.addParameter(QgsProcessingParameterFolderDestination('OUTPUT_FOLDER','Directory to contain new, timestamped results'))
        for n in ('SUMMARY','QA','MANIFEST','OUTPUT_GPKG'):
            self.addOutput(QgsProcessingOutputFile(n, n.replace('_',' ').title()))

    # Fail early for absent, empty or non-polygon inputs and non-metric CRS.
    # Area-based diagnostics assume planar square metres, not geographic degrees.
    @staticmethod
    def _require_polygon(layer, label):
        if layer is None or not layer.isValid():
            raise QgsProcessingException(f'{label}: invalid or missing layer')
        if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
            raise QgsProcessingException(f'{label}: polygon layer required')
        if layer.featureCount() == 0:
            raise QgsProcessingException(f'{label}: empty layer')
        if layer.crs().isGeographic() or layer.crs().mapUnits() != QgsUnitTypes.DistanceMeters:
            raise QgsProcessingException(f'{label}: projected metre CRS required (found {layer.crs().authid()})')

    # Run a native QGIS Processing overlay as a child of this algorithm.
    @staticmethod
    def _run(alg, params, context, feedback):
        return processing.run(alg,params,context=context,feedback=feedback,is_child_algorithm=True)['OUTPUT']

    # Resolve either an existing vector layer or a Processing output identifier.
    @staticmethod
    def _aslayer(x, context):
        return x if isinstance(x,QgsVectorLayer) else QgsProcessingUtils.mapLayerFromString(str(x),context)

    # Bring polygon geometry into the common projected CRS and repair invalid shapes.
    # Projection and geometry repair precede every area/overlay calculation.
    @classmethod
    def _prep(cls, layer, crs, context, feedback):
        out=layer
        # Reproject only when input CRS differs from the analysis CRS.
        if layer.crs()!=crs:
            out=cls._aslayer(cls._run('native:reprojectlayer', {
                'INPUT':out,'TARGET_CRS':crs,'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)
        # Repair geometry before native overlay and planar area operations.
        out=cls._aslayer(cls._run('native:fixgeometries', {
            'INPUT':out,'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)
        return out

    # Dissolve overlapping/touching polygons into geometric union support.
    # Empty inputs are returned without invoking an expensive overlay.
    @classmethod
    def _diss(cls, layer, context, feedback):
        # Dissolve is bypassed for truly empty results to avoid processing failures.
        if cls._count(layer)==0:
            return layer
        return cls._aslayer(cls._run('native:dissolve',{
            'INPUT':layer,'FIELD':[],'SEPARATE_DISJOINT':False,
            'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)

    # Return the polygon intersection (A intersect B), including empty handling.
    @classmethod
    def _inter(cls, a,b,context,feedback):
        # Returning an empty polygon layer preserves downstream overlay semantics.
        if cls._count(a)==0 or cls._count(b)==0:
            return cls._empty_like(a,context,feedback)
        return cls._aslayer(cls._run('native:intersection',{
            'INPUT':a,'OVERLAY':b,'INPUT_FIELDS':[],
            'OVERLAY_FIELDS':[],'OVERLAY_FIELDS_PREFIX':'',
            'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)

    # Return polygon difference (A minus B), including empty-overlay shortcuts.
    @classmethod
    def _diff(cls,a,b,context,feedback):
        # An empty minuend remains empty: A minus B is empty when A is empty.
        if cls._count(a)==0:
            return a
        # Subtracting an empty overlay leaves the source unchanged.
        if cls._count(b)==0:
            return a
        return cls._aslayer(cls._run('native:difference',{
            'INPUT':a,'OVERLAY':b,'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)

    # Return a zero-feature layer of the input schema for empty intersections.
    @classmethod
    def _empty_like(cls,layer,context,feedback):
        return cls._aslayer(cls._run('native:extractbyexpression',{
            'INPUT':layer,'EXPRESSION':'false',
            'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)

    # Layer feature-count helper for fast early-exit checks.
    @staticmethod
    def _count(layer):
        return layer.featureCount() if layer else 0

    # Sum actual polygon-geometry area, not nominal hexagon area or row counts.
    # Upstream geometries should be dissolved if overlap would double-count area.
    @staticmethod
    def _area(layer):
        if layer is None:
            return 0.0
        total=0.0
        # Read geometries only; avoid materialising unused attributes during area sums.
        for f in layer.getFeatures(QgsFeatureRequest().setNoAttributes()):
            if f.hasGeometry() and not f.geometry().isEmpty():
                total+=f.geometry().area()
        # Abort rather than publish a non-finite area denominator.
        if not math.isfinite(total):
            raise QgsProcessingException('Nonfinite computed polygon area')
        return total

    # Select features with provider-backed QGIS expressions; reject empty selections.
    # Avoid constructing huge FID lists in Python memory.
    @classmethod
    def _filter(cls,layer,expr,context,feedback,label):
        # Every expected non-empty source selection fails explicitly if no feature matches.
        x=cls._aslayer(cls._run('native:extractbyexpression',{
            'INPUT':layer,'EXPRESSION':expr,
            'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)
        if cls._count(x)==0:
            raise QgsProcessingException(f'{label}: no features after applying filter [{expr}]')
        return x

    # Read attribute text while converting NULL-like strings to missing.
    @staticmethod
    def _fieldvalue(v):
        if v is None:
            return ''
        s=str(v).strip()
        return '' if s.upper() in ('NULL','NONE','NA','') else s

    # Escape user-supplied string literals for safe QGIS expression generation.
    @staticmethod
    def _quoted(x):
        """QGIS expression string literal, escaped safely."""
        return "'" + str(x).replace("'", "''") + "'"

    # Construct a QGIS date predicate tolerating common storage formats.
    # Bare YYYY is a valid proxy only when the requested YYYYMMDD is 1 January.
    @classmethod
    def _date_expr(cls, field, ymd):
        """Match dates expressed as YYYYMMDD, YYYY-MM-DD, year, or timestamp.

        A bare year is accepted only for the Jan 1 interval convention.
        """
        # Quote the actual field name, including names containing embedded quotation marks.
        q='"' + field.replace('"','""') + '"'
        # Strip non-numeric separators so YYYY-MM-DD and YYYYMMDD can be matched.
        digits=f"regexp_replace(to_string({q}), '[^0-9]', '')"
        parts=[f"{digits} LIKE {cls._quoted(ymd+'%')}"]
        # Do not accept YYYY alone when ymd is not 1 January.
        if ymd.endswith('0101'):
            parts.append(f"{digits} = {cls._quoted(ymd[:4])}")
        return '('+' OR '.join(parts)+')'

    # Apply model/origin/date metadata restrictions when relevant fields exist.
    # Absent non-required fields are skipped, so provenance matters for manual layers.
    @classmethod
    def _meta_filter(cls,layer,meta,context,feedback,label,require_date=False):
        """Use native provider-backed filters, not enormous FID IN (...) strings."""
        # Skip a metadata restriction when the source lacks that attribute.
        for k,accepted in meta.items():
            field=_firstfield(layer,[k])
            if not field:
                # If strict date checking is requested, missing interval metadata is fatal.
                if require_date and k in ('Y1','Y2'):
                    raise QgsProcessingException(f'{label}: missing {k}; provide a single-combination input')
                continue
            q='"' + field.replace('"','""') + '"'
            # Normalise Y1/Y2 using date-aware predicates, not lexical equality.
            if k in ('Y1','Y2'):
                expected=_date(accepted)
                expr=cls._date_expr(field,expected)
            else:
                expr=f"lower(trim(to_string({q}))) = {cls._quoted(_norm(accepted).lower())}"
            layer=cls._filter(layer,expr,context,feedback,f'{label} ({k}={accepted})')
        return layer

    # Restrict a multi-transition source to either FP or DS pathway.
    # If no TRANSITION column exists, the analyst's source-layer selection is trusted.
    @classmethod
    def _restrict_pathway(cls,layer,pathway,context,feedback,label):
        """Isolate FP/DS when source has both TRANSITION values; fail on ambiguity."""
        # Some legacy single-purpose layers are identified only by analyst selection.
        tf=_firstfield(layer,['TRANSITION'])
        if not tf:
            # Single-combination layer supplied explicitly; there is no field
            # with which to verify its declared pathway.
            return layer
        # Enumerate labels to check the chosen process pathway is actually present.
        vals={cls._fieldvalue(f[tf]) for f in layer.getFeatures()}
        vals.discard('')
        # Never silently accept a layer that contains only the opposite pathway.
        recognised={v for v in vals if _pathway(v)==pathway}
        if not recognised:
            raise QgsProcessingException(f'{label}: TRANSITION field has no {pathway} values (found {sorted(vals)[:8]})')
        q='"'+tf.replace('"','""')+'"'
        expr=f"to_string({q}) IN ("+','.join(cls._quoted(v) for v in sorted(recognised))+')'
        return cls._filter(layer,expr,context,feedback,f'{label} ({pathway} transition)')

    # Extract the ranked-zone polygon for one pathway/model/origin/interval/threshold.
    # Accept current PCTL_GE and older TOP_PCT threshold schemas.
    @classmethod
    def _zone(cls, raw, pathway, model, forecast, y1, y2, top, crs,context,feedback):
        # Requested model, forecast and dates are applied when carried as zone fields.
        layer=cls._meta_filter(raw,{'FORECAST':forecast,'MODEL':model,'Y1':y1,'Y2':y2},
                              context,feedback,f'{pathway} zones')
        layer=cls._restrict_pathway(layer,pathway,context,feedback,f'{pathway} zones')
        # PCTL_GE is a minimum percentile rank, e.g. 90 means highest 10% of scores.
        pctl=_firstfield(layer,['PCTL_GE'])
        topfield=_firstfield(layer,['TOP_PCT']) if not pctl else None
        if not pctl and not topfield:
            raise QgsProcessingException(f'{pathway}: neither PCTL_GE nor TOP_PCT exists')
        # Legacy TOP_PCT encodes the same selection as a top-area percentage.
        field=pctl or topfield
        value=100.0-top if pctl else top
        q='"'+field.replace('"','""')+'"'
        # Float tolerance avoids rejection due to common decimal storage precision.
        expr=f'abs(to_real({q}) - {value:.12g}) < 0.000001'
        out=cls._filter(layer,expr,context,feedback,f'{pathway} top {top:g}%')
        # Transform and repair the selected zone before dissolving its geometry.
        out=cls._prep(out,crs,context,feedback)
        return cls._diss(out,context,feedback)

    # Select true Module 3A physical-erosion geometry for the analysis interval.
    # v1.2 differentiates two-endpoint metadata from an explicitly attested single layer.
    @classmethod
    def _ea(cls, layer, y1,y2, cls_field, values, confirmed, crs,context,feedback):
        # Search recognised interval-start fields, including Module 3A aliases.
        f1=_firstfield(layer,['Y1','YEAR_START','PeriodStart','Start_ymd','INTERVAL_START'])
        # Search recognised interval-end fields; some EA layers contain only PeriodEnd.
        f2=_firstfield(layer,['Y2','YEAR_END','PeriodEnd','End_ymd','INTERVAL_END'])
        # Module 3A often stores each interval as a SEPARATE dated layer.
        # Such EA layers can contain just one recognised endpoint-date field.
        # v1.1 rejected these layers even if the user correctly confirmed that
        # the input was already restricted to the requested observation pair.
        # Do NOT silently treat a partially dated combined layer as a single interval.
        # Both endpoints known: enforce BOTH Y1 and Y2 for a combined EA dataset.
        if f1 and f2:
            expr=cls._date_expr(f1,y1)+' AND '+cls._date_expr(f2,y2)
            layer=cls._filter(layer,expr,context,feedback,'EA interval')
            # Record that exact two-endpoint filtering established the interval.
            provenance='EA_METADATA_FILTERED_BOTH_ENDPOINTS'
        # One endpoint only: analyst must attest that the selected EA layer is single-interval.
        elif f1 or f2:
            # Use the present field to identify whether the documented endpoint is start or end.
            present=f1 or f2
            side='start' if f1 else 'end'
            expected=y1 if f1 else y2
            # The confirmation flag is required; do not silently include mixed-year features.
            if not confirmed:
                raise QgsProcessingException(
                    f'EA layer has only the recognised interval {side} field '
                    f'{present!r} (fields: {layer.fields().names()}). '
                    'If this is the single Y1–Y2 interval EA layer, tick '
                    'EA_IS_SINGLE_INTERVAL; the available date will be verified. '
                    'Otherwise supply a layer with both endpoint dates.')
            # Confirm ALL source features bear the requested date on the side
            # whose metadata exists. A mere subset match is not enough: it may
            # disguise a combined multi-interval EA layer.
            # Demand that the available endpoint matches on every source feature.
            date_match=cls._filter(layer,cls._date_expr(present,expected),
                                   context,feedback,f'EA single-interval {side} date')
            # Compare the filtered count against the entire selected EA layer.
            source_count=layer.featureCount()
            matched_count=date_match.featureCount()
            # A partial match means potentially mixed intervals, even with attestation.
            if matched_count!=source_count:
                raise QgsProcessingException(
                    f'EA layer has only {side} date field {present!r} and '
                    f'{matched_count}/{source_count} features match {expected}. '
                    'A partial-date combined layer cannot be used as a '
                    'confirmed single interval. Select the correct single '
                    'Y1–Y2 EA layer or provide both endpoint date fields.')
            # The warning documents that only one endpoint was checked independently.
            feedback.pushWarning(
                f'[EA DATE] Single-interval selection attested: '
                f'{side}={expected} checked in {present!r} '
                f'for all {source_count:,} features; the other endpoint '
                'is supported by the user-selected, dated single-interval '
                'layer rather than a second attribute.')
            layer=date_match
            # Persist explicit provenance distinguishing date-checked single-layer input.
            provenance=f'SINGLE_INTERVAL_ATTESTED_{side.upper()}_DATE_CHECKED'
        # No date fields: require an analyst-attested single-interval source.
        elif not confirmed:
            raise QgsProcessingException(
                'EA layer has no recognised interval endpoint fields. '
                'Select a single-interval EA layer and tick '
                'EA_IS_SINGLE_INTERVAL; do not use a multi-interval layer.')
        else:
            # Attestation is logged because metadata cannot independently verify Y1/Y2.
            feedback.pushWarning(
                '[EA DATE] No endpoint metadata fields detected; '
                'the 1-interval attribution relies on the selected '
                'EA layer and explicit user attestation.')
            # Preserve this reduced-strength date provenance in outputs and manifest.
            provenance='SINGLE_INTERVAL_USER_ATTESTED_NO_DATE_FIELDS'
        # Resolve process-class field automatically only if requested.
        if cls_field.upper()=='AUTO':
            field=_firstfield(layer,['EA_clean','EA','EA_CLASS','PROCESS','CLASS'])
        else:
            field=_firstfield(layer,[cls_field])
        if not field:
            raise QgsProcessingException('EA: process class field not found. Use EA_CLASS_FIELD or a recognised EA classification field.')
        # Class selection is explicit; generic deposition or all EA processes are not used.
        selected=set(re.sub(r'\s+',' ',x.strip().lower()) for x in values.split(',') if x.strip())
        if not selected:
            raise QgsProcessingException('At least one erosion EA class must be set')
        q='"'+field.replace('"','""')+'"'
        # Apply a case-insensitive exact-match filter for selected erosion classes.
        expr=f"lower(trim(to_string({q}))) IN (" + ','.join(cls._quoted(x) for x in sorted(selected)) + ')'
        layer=cls._filter(layer,expr,context,feedback,'EA erosion class')
        # Dissolve the dated, classified erosion polygons to a non-overlapping area mask.
        return cls._diss(cls._prep(layer,crs,context,feedback),context,feedback),provenance

    # Legacy alternative: accept an analyst-supplied COMPLETE T1 scored-risk mask.
    # It must cover the modelled denominator, not only the top-ranked cells.
    @classmethod
    def _risk(cls,raw,crs,y1,forecast,model,pathway,context,feedback,label):
        # Only filter if metadata fields exist. The analyst must supply a full,
        # single-origin, T1-scored risk layer (not the entire PLACE grid).
        # Legacy manual mask is filtered by metadata only when fields are supplied.
        layer=cls._meta_filter(raw,{'FORECAST':forecast,'MODEL':model,'Y1':y1},
                               context,feedback,label)
        # Require corresponding FP/DS semantics whenever TRANSITION is present.
        layer=cls._restrict_pathway(layer,pathway,context,feedback,label)
        return cls._diss(cls._prep(layer,crs,context,feedback),context,feedback)

    # Preferred: reconstruct the full model-specific, eligible AND scored T1 support.
    # Require status/risk, transition, forecast dates, model ID and percentile ranks.
    @classmethod
    def _continuous_scored(cls, raw, pathway, desired_model, forecast, y1, y2,
                           crs, context, feedback):
        """Build a complete T1 scored PLACE population from an untruncated 5c layer.

        The strong metadata requirements avoid accidentally using strict SF->AD
        for broad FP->AD, a different Txx origin or P1 vs P2 continuous output.
        """
        # Required fields distinguish a FULL scored prediction from a zone-only export.
        required=('P_STATUS','P_RISKSET','P_PCTL','P_MODEL','P_FORECAST',
                  'P_TRANS','P_Y1','P_Y2')
        # Resolve case-insensitive attributes but require every key metadata field.
        fields={k:_firstfield(raw,[k]) for k in required}
        absent=[k for k,v in fields.items() if v is None]
        if absent:
            raise QgsProcessingException(
                f'{pathway} continuous layer lacks {absent}. Select full Module 5c '
                'OUTPUT_CONTINUOUS / pred_ layer, NOT a zones_ or riskcells_ layer.')
        # QGIS expression helper uses resolved provider field spellings.
        q=lambda field:'"'+fields[field].replace('"','""')+'"'
        # Exclude rows not successfully modelled; they cannot enter scored-area fractions.
        expr=(f"lower(trim(to_string({q('P_STATUS')}))) = 'predicted' "
              # Restrict the denominator to the model-defined T1 risk set.
              f"AND to_int({q('P_RISKSET')}) = 1 "
              # Use only the supplied forecast origin and observation pair.
              f"AND lower(trim(to_string({q('P_FORECAST')}))) = {cls._quoted(forecast.lower())} "
              f"AND {cls._date_expr(fields['P_Y1'],y1)} "
              f"AND {cls._date_expr(fields['P_Y2'],y2)}")
        # Build the scored-place subset BEFORE inspecting any subsequent EA erosion.
        scored=cls._filter(raw,expr,context,feedback,f'{pathway} continuous scored {forecast}/{y1}-{y2}')

        # The P_TRANS values are part of the model provenance. Never substitute
        # SF->AD for the broader eligible-FP->AD model or vice versa.
        # Inspect recorded transition provenance; FP must remain distinct from SF.
        values=set()
        for f in scored.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)):
            v=cls._fieldvalue(f[fields['P_TRANS']])
            if v:
                values.add(v)
        # Reject any continuous archive missing the specified FP/DS transition.
        allowed={v for v in values if _pathway(v)==pathway}
        if not allowed:
            raise QgsProcessingException(
                f'{pathway}: continuous P_TRANS={sorted(values)}; expected '
                'Eligible Floodplain -> Active Domain or Depositional Storage -> Active Domain')
        # Keep exactly the requested pathway when multiple transitions occur in one layer.
        trans_expr='to_string('+q('P_TRANS')+') IN (' + ','.join(cls._quoted(v) for v in sorted(allowed))+')'
        scored=cls._filter(scored,trans_expr,context,feedback,f'{pathway} correct transition')

        # Collect candidate models and percentile-rank bounds among scored places.
        models=set()
        minimum_rank=None
        maximum_rank=None
        n=0
        # Check every scored rank is finite and in the expected zero-to-one range.
        for f in scored.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)):
            model=cls._fieldvalue(f[fields['P_MODEL']]);rank=_num(f[fields['P_PCTL']])
            if not model or rank is None or not 0 <= rank <= 1.000001:
                raise QgsProcessingException(f'{pathway}: blank P_MODEL or invalid P_PCTL in scored row')
            models.add(model);n+=1
            minimum_rank=rank if minimum_rank is None else min(rank,minimum_rank)
            maximum_rank=rank if maximum_rank is None else max(rank,maximum_rank)
        if not n:
            raise QgsProcessingException(f'{pathway}: no scored cells in continuous input')
        # An explicit model label, when supplied, must match one unique archive model.
        if _norm(desired_model).upper() not in ('','AUTO'):
            matches=[m for m in models if m.casefold()==desired_model.casefold()]
            if len(matches)!=1:
                raise QgsProcessingException(f'{pathway}: selected model {desired_model!r} not present; P_MODEL values: {sorted(models)}')
            model=matches[0]
        # AUTO is allowed only if the filtered input contains exactly one model.
        elif len(models)==1:
            model=next(iter(models))
        else:
            raise QgsProcessingException(f'{pathway}: multiple P_MODEL values {sorted(models)}; set model label explicitly')
        # If a model is selected, further subset before constructing its geometry.
        if len(models)>1:
            scored=cls._filter(scored,
                f"lower(trim(to_string({q('P_MODEL')}))) = {cls._quoted(model.lower())}",
                context,feedback,f'{pathway} selected P_MODEL')
            # Recalculate rank bounds after an explicit P_MODEL restriction.
            # Recompute extrema for selected model; the earlier aggregate may
            # have included additional models.
            ranks=[_num(f[fields['P_PCTL']]) for f in scored.getFeatures()]
            minimum_rank=min(ranks);maximum_rank=max(ranks);n=len(ranks)

        # Sanity check that the full scored population includes low-risk ranks.
        if minimum_rank is None or minimum_rank>0.65:
            raise QgsProcessingException(
                f'{pathway}: continuous input contains no low-ranked scored locations '
                f'(minimum P_PCTL={minimum_rank}). Perhaps selected a top-percentile '
                'riskcells layer instead of FULL OUTPUT_CONTINUOUS.')
        # Also require some high-risk ranks: reject sparse/truncated/non-modelled input.
        if maximum_rank is None or maximum_rank<0.70:
            raise QgsProcessingException(f'{pathway}: continuous scored population lacks >=70th percentile scores')

        feedback.pushInfo(f'[5c continuous] {pathway} {forecast}/{model}: '
                          f'{n:,} scored cells, P_PCTL range {minimum_rank:.5f}-{maximum_rank:.5f}')
        # Convert all selected scored-place polygons into a dissolved full support mask.
        geom=cls._diss(cls._prep(scored,crs,context,feedback),context,feedback)
        return geom,scored,model,n,minimum_rank,maximum_rank

    # Check that supplied percentile-zone polygons agree with the continuous model.
    # Area of symmetric difference detects wrong P1/P2/origin combinations.
    @classmethod
    def _zone_rank_alignment(cls, zone, scored, top, crs, context, feedback):
        """Symmetric-difference area between 5c scores and selected 5c2 zones.

        Catches P1/P2 layer confusion even if those models used exactly the
        same eligible/scored mask. Does not need T2 events or EA observations.
        """
        # Compare the continuous P_PCTL field, not the textual map class.
        pf=_firstfield(scored,['P_PCTL'])
        if not pf:
            raise QgsProcessingException('Continuous scored layer lacks P_PCTL')
        # Top-k% is the >=(1-k/100) threshold of rank values.
        cutoff=1.0-top/100.0
        q='"'+pf.replace('"','""')+'"'
        ranked=cls._filter(scored,
            f'to_real({q}) >= {cutoff:.12g} - 0.0000000001',
            context,feedback,f'Continuous top {top:g}% P_PCTL comparison')
        # Dissolve selected ranked cells, independent of the externally supplied zones.
        ranked=cls._diss(cls._prep(ranked,crs,context,feedback),context,feedback)
        # Area of symmetric difference without relying on one large
        # QgsGeometry union in Python memory.
        # First symmetric-difference component: supplied zone outside ranked support.
        loss=cls._area(cls._diff(zone,ranked,context,feedback))
        # Second component: ranked support omitted from the supplied zone.
        excess=cls._area(cls._diff(ranked,zone,context,feedback))
        return loss+excess,loss,excess

    # Union the FP and DS scored-support polygons when both pathways are analysed.
    # Joint FP + DS support is constructed only when both pathways were provided.
    @classmethod
    def _union(cls, layers, context,feedback):
        if len(layers)==1:
            return layers[0]
        a,b=layers
        # Native merge and dissolve builds a union without Python mega-geometries.
        combined=cls._aslayer(cls._run('native:mergevectorlayers',{
            'LAYERS':[a,b],'CRS':a.crs(),'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT},context,feedback),context)
        return cls._diss(combined,context,feedback)

    # Write a non-empty overlay layer to the new output GeoPackage.
    # Use file creation only for the first layer and layer creation thereafter.
    @staticmethod
    def _save(layer,gpkg,name,context,first):
        # Skip empty diagnostic layers to avoid spurious GeoPackage outputs.
        if layer is None or layer.featureCount()==0:
            return False
        options=QgsVectorFileWriter.SaveVectorOptions()
        options.driverName='GPKG';options.layerName=name
        # Do not overwrite the entire output GeoPackage when adding later layers.
        options.actionOnExistingFile=(QgsVectorFileWriter.CreateOrOverwriteFile if first
                                      else QgsVectorFileWriter.CreateOrOverwriteLayer)
        # Use native writer to preserve polygon geometry and projection metadata.
        result=QgsVectorFileWriter.writeAsVectorFormatV3(layer,str(gpkg),context.transformContext(),options)
        if result[0]!=QgsVectorFileWriter.NoError:
            raise QgsProcessingException(f'Cannot save GIS layer {name}: {result}')
        return True

    # Optionally attach an already-computed *transition footprint* verification row.
    # This juxtaposition is descriptive; 5d transitions and EA erosion differ.
    # Read pre-existing 5d summary for contextual TRANSITION capture only.
    # Compatibility note: matcher expects columns river, model, recall, observed_area_m2.
    # The archived 5d v1.3.3 batch CSV instead uses actual_transition_recall and
    # actual_observed_area_m2 and lacks river/model; it will not match unmodified.
    @staticmethod
    def _match_5d(csvpath,river,forecast,model,pathway,y1,y2,top):
        if not csvpath:
            return {}
        try:
            # Import rows with UTF-8 BOM tolerance. This optional file is not an EA mask.
            with open(csvpath,encoding='utf-8-sig',newline='') as h:
                rows=list(csv.DictReader(h))
        except Exception as e:
            raise QgsProcessingException(f'Cannot read 5d summary: {e}')
        matches=[]
        # Filter by user-specified river and rolling-origin label.
        for r in rows:
            if _norm(r.get('river')).lower()!=river.lower() or _norm(r.get('forecast')).lower()!=forecast.lower():
                continue
            # Match model and transition pathway, not just forecast interval.
            if _norm(r.get('model')).lower()!=model.lower() or _pathway(r.get('transition'))!=pathway:
                continue
            # Compare normalised interval start/stop dates.
            if _date(r.get('y1'))!=y1 or _date(r.get('y2'))!=y2:
                continue
            # Require the same top-scored-area threshold used in this correspondence run.
            t=_num(r.get('top_pct'))
            if t is None or abs(t-top)>1e-6:
                continue
            matches.append(r)
        # Ambiguous duplicate rows should not be silently averaged or chosen.
        if len(matches)>1:
            raise QgsProcessingException(f'Ambiguous 5d summary records for {pathway} {forecast} {model} {top}%')
        return matches[0] if matches else {}

    # Safe ratio returning NULL when the denominator is non-positive.
    @staticmethod
    def _pct(n,d):
        return n/d if d>0 else None

    # Run one interval's FP/DS correspondence analysis with strict input QA.
    # Keep model-scored support separate from subsequently observed erosion geometry.
    def processAlgorithm(self, params, context, feedback):
        # Retrieve the paired FP and DS zone/risk/continuous layers from QGIS UI.
        get=lambda n:self.parameterAsVectorLayer(params,n,context)
        fpz, fpr, fpc, dsz, dsr, dsc=[get(n) for n in
            ('FP_ZONES','FP_RISK','FP_CONTINUOUS','DS_ZONES','DS_RISK','DS_CONTINUOUS')]
        ea=get('EA_EROSION');support=get('VALID_SUPPORT')
        # Record a separate source mode for each transition pathway.
        paths={};risk_modes={}
        for code,z,manual,continuous,model_field in (
                # A pathway is omitted entirely if no member of its input triple was supplied.
                ('FP',fpz,fpr,fpc,'FP_MODEL'),('DS',dsz,dsr,dsc,'DS_MODEL')):
            if z is None and manual is None and continuous is None:
                continue
            # If any source for a pathway is present, its ranked zone layer is required.
            if z is None:
                raise QgsProcessingException(f'{code}: percentile zones are required when a risk source is supplied')
            # Exactly one of FULL continuous output and FULL manually scored mask is allowed.
            if (manual is None)==(continuous is None):
                raise QgsProcessingException(
                    f'{code}: select exactly ONE risk source: full 5c continuous prediction '
                    'OR manually built full scored mask (not both)')
            source=continuous if continuous is not None else manual
            # Do not accept an unlabeled manual mask; there is no automatic model provenance.
            mode='5C_CONTINUOUS_AUTO_FILTER' if continuous is not None else 'MANUAL_FULL_MASK'
            model=_norm(self.parameterAsString(params,model_field,context))
            if mode=='MANUAL_FULL_MASK' and model.upper() in ('','AUTO'):
                raise QgsProcessingException(
                    f'{code}: enter an explicit model label when using a manual risk mask')
            # Validate selected zones and their full supporting populations before overlays.
            self._require_polygon(z,f'{code} zones')
            self._require_polygon(source,f'{code} '+mode)
            paths[code]=(z,source,model)
            risk_modes[code]=mode
        # At least one of FP->AD / DS->AD must be included.
        if not paths:
            raise QgsProcessingException('Select FP_ZONES and/or DS_ZONES with matching full 5c continuous input or full mask')
        # EA erosion layer and optional support area must both be projected polygon data.
        self._require_polygon(ea,'EA erosion')
        if support:self._require_polygon(support,'valid EA support')
        # Read river, origin, observation dates and threshold choices for one run.
        river=_norm(self.parameterAsString(params,'RIVER',context))
        forecast=_norm(self.parameterAsString(params,'FORECAST',context))
        y1=_date(self.parameterAsString(params,'Y1',context))
        y2=_date(self.parameterAsString(params,'Y2',context))
        # A temporally ordered interval is required: Y1 < Y2.
        if not y1 or not y2 or y1>=y2:
            raise QgsProcessingException('Y1/Y2 must be valid, ascending observation dates')
        try: tops=_top_list(self.parameterAsString(params,'TOP_PCTS',context))
        except ValueError as e:raise QgsProcessingException(str(e))
        if not river or not forecast:
            raise QgsProcessingException('River/forecast labels must be supplied')
        # Retain options to export the geometry and cross-check zone ranks.
        save=self.parameterAsBool(params,'SAVE_SPATIAL',context)
        check_zone_ranks=self.parameterAsBool(params,'VERIFY_ZONE_RANKS',context)
        # Optional 5d summary cannot affect this run’s GIS erosion calculations.
        csv_5d=_norm(self.parameterAsFile(params,'SUMMARY_5D',context))
        # The destination base folder must already exist; the script creates a child.
        outbase=Path(self.parameterAsString(params,'OUTPUT_FOLDER',context))
        if not outbase.exists() or not outbase.is_dir():
            raise QgsProcessingException('Output folder must be an existing directory')
        # UTC microsecond timestamp keeps runs separate and identifiable.
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        out=outbase/f'FRAF_5d_EA_{_tag(river)}_{_tag(forecast)}_{stamp}'
        out.mkdir(parents=False,exist_ok=False)
        # Output filenames are original executable literals for archive compatibility.
        summaryfile=out/'EA_Susceptibility_Correspondence.csv'
        combinedfile=out/'EA_Susceptibility_Combined.csv'
        qafile=out/'EA_Susceptibility_QA.csv'
        manifestfile=out/'EA_Susceptibility_manifest.json'
        gpkg=out/'EA_Susceptibility_Correspondence.gpkg'
        # STARTED marker enables detection of interrupted or incomplete runs.
        status=out/'00_RUN_STATUS.txt'
        status.write_text('STARTED\n',encoding='utf-8')
        # All side effects are inside try/except so failures leave an explicit marker.
        qa=[]; rows=[]; written=[]; first=True
        try:
            # Use the selected ranked-zone CRS for all geometry comparisons.
            crs=next(iter(paths.values()))[0].crs()
            # Filter independent EA source to the exact interval and erosion class(es).
            E,provenance=self._ea(ea,y1,y2,
                self.parameterAsString(params,'EA_CLASS_FIELD',context),
                self.parameterAsString(params,'EROSION_CLASSES',context),
                self.parameterAsBool(params,'EA_IS_SINGLE_INTERVAL',context),
                crs,context,feedback)
            # If supplied, the valid observation/support polygon clips TOTAL EA erosion.
            if support:
                sup=self._diss(self._prep(support,crs,context,feedback),context,feedback)
                E=self._diss(self._inter(E,sup,context,feedback),context,feedback)
            # Total physical erosion is a separate denominator from model eligible erosion.
            total=self._area(E)
            if total<=0: raise QgsProcessingException('EA physical erosion has zero area inside selected support')
            feedback.pushInfo(f'EA erosion {y1}–{y2}: {total/1e6:.6f} km² ({provenance})')
            # Optionally persist the independent full-area EA erosion mask.
            if save:
                first=not self._save(E,gpkg,'ea_all',context,first)
                written.append('ea_all')
            # Keep per-pathway masks, scored rows, event intersections and zones distinct.
            risks={}
            scored_continuous={}
            scored_counts={}
            eroded={}
            zones={}
            # Build the model-scored population for each requested pathway.
            for path,(raw_z,raw_r,model) in list(paths.items()):
                # Preferred path: derive complete T1 scored support from FULL continuous output.
                if risk_modes[path]=='5C_CONTINUOUS_AUTO_FILTER':
                    r,scored,model,n,rmin,rmax=self._continuous_scored(
                        raw_r,path,model,forecast,y1,y2,crs,context,feedback)
                    scored_continuous[path]=scored
                    scored_counts[path]=n
                    paths[path]=(raw_z,raw_r,model)
                    # Record observed model-specific scored cell count for QA and audit.
                    qa.append(dict(scope=f'{path}_CONTINUOUS_SCORED_ROWS',value_m2=n,
                        tolerance_m2=0,status='PASS',
                        note=f'P_STATUS=predicted AND P_RISKSET=1; model={model}; P_PCTL min={rmin:.8f} max={rmax:.8f}'))
                else:
                    # Alternative path: accept manual full T1 risk support after metadata filtering.
                    r=self._risk(raw_r,crs,y1,forecast,model,path,context,feedback,f'{path} risk')
                    scored_counts[path]=None
                # The resulting risk polygon is a denominator, not an observed event footprint.
                risks[path]=r
                # EA intersect T1 risk determines physical erosion within this pathway population.
                eroded[path]=self._inter(E,r,context,feedback)
                if save:
                    if self._save(r,gpkg,f'risk_{path}',context,first):first=False;written.append(f'risk_{path}')
                    if self._save(eroded[path],gpkg,f'ea_eligible_{path}',context,first):first=False;written.append(f'ea_eligible_{path}')
                # Log full scored support and its subsequent eroded area in square kilometres.
                feedback.pushInfo(f'{path}: T1 risk area {self._area(r)/1e6:.4f} km², EA within risk {self._area(eroded[path])/1e6:.5f} km²')
            # When both pathways are present, their T1 risk polygons must not overlap.
            if len(paths)==2:
                # Area of FP intersect DS should be zero apart from numerical geometry tolerance.
                overlap=self._area(self._inter(risks['FP'],risks['DS'],context,feedback))
                tol=max(1.0,1e-7*min(self._area(risks['FP']),self._area(risks['DS'])))
                # Store this mutual-exclusivity QA explicitly, and fail if overlap is material.
                qa.append(dict(scope='FP_DS_RISK_OVERLAP',value_m2=overlap,tolerance_m2=tol,status='PASS' if overlap<=tol else 'FAIL',note='T1 FP and DS are mutually exclusive PLACE risk populations'))
                if overlap>tol:
                    raise QgsProcessingException(f'FP and DS T1 risk masks overlap by {overlap:.3f} m²; supply nonoverlapping risk masks')
            # The union is the combined eligible and successfully scored exposure domain.
            eligible_union=self._union(list(risks.values()),context,feedback)
            # Partition all observed erosion into inside versus outside modelled support.
            E_eligible=self._inter(E,eligible_union,context,feedback)
            E_other=self._diff(E,eligible_union,context,feedback)
            a_eligible=self._area(E_eligible);a_other=self._area(E_other)
            # Closure checks erosion totals: within + outside = all erosion.
            closure=abs((a_eligible+a_other)-total)
            tol=max(1.0,1e-6*total)
            # Tolerance scales with the total eroded area while allowing sub-metre slivers.
            qa.append(dict(scope='EA_ELIGIBILITY_PARTITION',value_m2=closure,tolerance_m2=tol,status='PASS' if closure<=tol else 'FAIL',note=f'EA total {total:.3f} m2; eligible {a_eligible:.3f}; outside {a_other:.3f}'))
            if closure>tol:raise QgsProcessingException('EA partition into eligible/outside does not conserve area')
            # If FP and DS are disjoint, their eroded areas should sum to joint eligible erosion.
            if len(paths)==2:
                group_err=abs(sum(self._area(v) for v in eroded.values())-a_eligible)
                qa.append(dict(scope='FP_DS_EROSION_SUM',value_m2=group_err,tolerance_m2=tol,status='PASS' if group_err<=tol else 'FAIL',note='FP + DS erosion matches union eligible erosion'))
                if group_err>tol:raise QgsProcessingException('FP + DS eligible erosion sum does not close')
            # Persist eligible and non-eligible erosion layers for geomorphic comparison.
            if save:
                for l,n in [(E_eligible,'ea_all_eligible'),(E_other,'ea_outside_risks')]:
                    if self._save(l,gpkg,n,context,first):first=False;written.append(n)
            # Construct each pathway’s ranked zones and compute capture by threshold.
            all_zones={}
            for path,(raw_z,raw_r,model) in paths.items():
                # Obtain the pathway-specific eligible/scored denominator area.
                r=risks[path]
                rarea=self._area(r)
                # Numerator target is EA erosion within that same pathway risk population.
                ea_r=eroded[path]
                erarea=self._area(ea_r)
                if rarea<=0:raise QgsProcessingException(f'{path} risk mask has zero area')
                # Top scores are evaluated at the requested 10/20/30% (or custom) cut-offs.
                for top in tops:
                    # Read zone geometry for the same model, forecast, interval and threshold.
                    z=self._zone(raw_z,path,model,forecast,y1,y2,top,crs,context,feedback)
                    zone_area_raw=self._area(z)
                    # Rank-alignment QA detects accidental mismatch between 5c scores and zones.
                    if path in scored_continuous and check_zone_ranks:
                        sym,loss,excess=self._zone_rank_alignment(
                            z,scored_continuous[path],top,crs,context,feedback)
                        # Symmetric difference is accepted only within the configured area tolerance.
                        align_tol=max(2.0,0.005*zone_area_raw)
                        qa.append(dict(scope=f'{path}_top{top:g}_ZONE_SCORE_ALIGNMENT',
                            value_m2=sym,tolerance_m2=align_tol,
                            status='PASS' if sym<=align_tol else 'FAIL',
                            note=(f'5c P_PCTL vs supplied 5c2 zone; '
                                  f'zone_only_m2={loss:.3f}; 5c_only_m2={excess:.3f}. '
                                  'Mismatches may mean P1/P2 mix, zone simplification or wrong origin.')))
                        # Disallow material zone/continuous mismatch rather than publish mixed models.
                        if sym>align_tol:
                            raise QgsProcessingException(
                                f'{path} {forecast} {model} top {top:g}% zones differ from '
                                f'the selected continuous 5c ranks by {sym:.2f} m² '
                                f'(tolerance {align_tol:.2f}). Check P1/P2 and zone layer provenance.')
                    # Ranked zones should have NO geographic area outside full T1 scored support.
                    leakage=self._area(self._diff(z,r,context,feedback))
                    lt=max(1.0,1e-6*zone_area_raw)
                    # Record leakage as the area of zone minus full scored risk.
                    qa.append(dict(scope=f'{path}_top{top:g}_ZONE_LEAKAGE',value_m2=leakage,
                                   tolerance_m2=lt,status='PASS' if leakage<=lt else 'FAIL',
                                   note='Area ranked as high susceptibility outside specified T1 scored risk mask'))
                    if leakage>lt:
                        raise QgsProcessingException(f'{path} top {top:g}%: zone outside T1 scored support by {leakage:.2f} m2; wrong mask/forecast?')
                    # Clip the zone to the scored risk mask after passing leakage QA.
                    z=self._inter(z,r,context,feedback)
                    za=self._area(z)
                    # Measure the selected area fraction from geometry, not nominal top-k%.
                    cov=self._pct(za,rarea)
                    # A small departure from nominal coverage is logged for diagnostics.
                    if cov is not None and abs(cov-top/100.0)>max(0.01,0.15*top/100.0):
                        qa.append(dict(scope=f'{path}_top{top:g}_AREA_COVERAGE_WARNING',value_m2=za,
                            tolerance_m2=rarea*max(0.01,0.15*top/100.0),status='WARN',note=f'Actual scored-area share {100*cov:.3f}% vs nominal top {top:g}%. Check identical scored support / 5c2 zone geometry.'))
                    # A large coverage error usually indicates a truncated/mismatched risk mask.
                    if cov is not None and abs(cov-top/100.0)>0.05:
                        raise QgsProcessingException(f'{path} top {top:g}% occupies {100*cov:.2f}% of supplied risk mask. This likely is not the FULL scored T1 risk population.')
                    # Erosion captured: subsequent EA erosion INSIDE ranked zone and pathway risk.
                    inside=self._inter(ea_r,z,context,feedback)
                    ia=self._area(inside)
                    # Erosion missed: eligible subsequent EA erosion OUTSIDE that zone.
                    missed=self._diff(ea_r,z,context,feedback)
                    ma=self._area(missed)
                    # Geometric conservation demands captured + missed = eligible erosion.
                    err=abs((ia+ma)-erarea)
                    mtol=max(1.0,1e-6*max(erarea,za))
                    qa.append(dict(scope=f'{path}_top{top:g}_EA_CAPTURE_CLOSURE',value_m2=err,tolerance_m2=mtol,status='PASS' if err<=mtol else 'FAIL',note='Inside + outside ranked zone = EA erosion within pathway risk'))
                    if err>mtol:raise QgsProcessingException(f'{path} top {top:g}%: overlay area closure failure')
                    # Append optional matching 5d transition-footprint result as context.
                    d5=self._match_5d(csv_5d,river,forecast,model,path,y1,y2,top)
                    rec=_num(d5.get('recall'))
                    label=f'{path}_top{_tag(f"{top:g}").replace("_", "p")}'
                    # GIS exports are diagnostic and never replace the source prediction polygons.
                    if save:
                        for l,n in [(z,f'zone_{label}'),(inside,f'ea_inside_{label}'),(missed,f'ea_outside_{label}')]:
                            if self._save(l,gpkg,n,context,first):first=False;written.append(n)
                    # Record full/eligible EA denominators and captured polygon areas per threshold.
                    row=dict(river=river,forecast=forecast,model=model,transition='FP->AD' if path=='FP' else 'DS->AD',
                        y1=y1,y2=y2,top_pct=top,
                        risk_source=risk_modes[path],scored_cell_count=scored_counts[path],
                        eligible_area_m2=rarea,nominal_top_fraction=top/100.0,
                        zone_area_m2=za,zone_area_fraction=cov,
                        ea_all_area_m2=total,ea_eligible_area_m2=erarea,
                        ea_inside_zone_m2=ia,ea_eligible_outside_zone_m2=ma,
                        # Eligible EA capture = captured erosion / EA erosion in pathway scored support.
                        ea_capture_fraction=self._pct(ia,erarea),
                        # Enrichment compares the captured fraction to fraction of scored area selected.
                        spatial_enrichment=(self._pct(ia,erarea)/cov if erarea>0 and cov and cov>0 else None),
                        # Full-corridor capture uses ALL clipped EA physical erosion as denominator.
                        total_corridor_erosion_capture_fraction=self._pct(ia,total),
                        # 5d verification metric describes organisational events, not total EA erosion.
                        fived_transition_footprint_capture=rec,
                        fived_observed_transition_area_m2=_num(d5.get('observed_area_m2')),
                        # VERIFIED indicates completed geometric correspondence, not forecast causality.
                        ea_date_provenance=provenance,verification_status='VERIFIED' if erarea>0 else 'NO_ELIGIBLE_EROSION')
                    rows.append(row)
                    # Retain each pathway/threshold zone for a possible combined calculation.
                    all_zones[(path,top)]=z
                    feedback.pushInfo(f'{path} top {top:g}%: eligible EA capture={row["ea_capture_fraction"]}, enrichment={row["spatial_enrichment"]}; 5d transition capture={rec}')
            # Combined outputs are produced only when both disjoint FP and DS are supplied.
            if len(paths)==2:
                rarea=self._area(eligible_union)
                # Joint scored support has a different area denominator from either pathway.
                for top in tops:
                    # Merge ranked FP and DS zones for corresponding top-area thresholds.
                    z=self._union([all_zones[('FP',top)],all_zones[('DS',top)]],context,feedback)
                    za=self._area(z);cov=self._pct(za,rarea)
                    # Joint capture uses the union of the two eligible/scored populations.
                    inside=self._inter(E_eligible,z,context,feedback)
                    ia=self._area(inside)
                    missed=self._diff(E_eligible,z,context,feedback)
                    ma=self._area(missed)
                    # Check the combined EA capture partition conserves the joint eligible area.
                    err=abs(ia+ma-a_eligible)
                    mtol=max(1.0,1e-6*max(a_eligible,za))
                    qa.append(dict(scope=f'COMBINED_top{top:g}_EA_CAPTURE_CLOSURE',value_m2=err,tolerance_m2=mtol,status='PASS' if err<=mtol else 'FAIL',note='Joint eligible EA capture closure'))
                    if err>mtol:raise QgsProcessingException(f'Combined top {top:g}%: geometry closure failure')
                    if save:
                        t=_tag(f'{top:g}').replace('_','p')
                        for l,n in [(z,f'zone_COMBINED_top{t}'),(inside,f'ea_inside_COMBINED_top{t}'),(missed,f'ea_outside_COMBINED_top{t}')]:
                            if self._save(l,gpkg,n,context,first):first=False;written.append(n)
                    # Combined record reports FP + DS coverage and erosion capture; no joint Cox fit.
                    rows.append(dict(river=river,forecast=forecast,model=f"FP:{paths['FP'][2]}+DS:{paths['DS'][2]}",transition='FP+DS combined',
                        y1=y1,y2=y2,top_pct=top,risk_source='COMBINED',scored_cell_count=None,
                        eligible_area_m2=rarea,nominal_top_fraction=top/100.0,
                        zone_area_m2=za,zone_area_fraction=cov,ea_all_area_m2=total,
                        ea_eligible_area_m2=a_eligible,ea_inside_zone_m2=ia,ea_eligible_outside_zone_m2=ma,
                        ea_capture_fraction=self._pct(ia,a_eligible),
                        spatial_enrichment=(self._pct(ia,a_eligible)/cov if a_eligible>0 and cov and cov>0 else None),
                        total_corridor_erosion_capture_fraction=self._pct(ia,total),
                        fived_transition_footprint_capture=None,fived_observed_transition_area_m2=None,
                        ea_date_provenance=provenance,verification_status='VERIFIED' if a_eligible>0 else 'NO_ELIGIBLE_EROSION'))
            # Use one stable CSV schema for pathway and combined rows.
            cols=['river','forecast','model','transition','y1','y2','top_pct','risk_source','scored_cell_count','eligible_area_m2','nominal_top_fraction',
                  'zone_area_m2','zone_area_fraction','ea_all_area_m2','ea_eligible_area_m2',
                  'ea_inside_zone_m2','ea_eligible_outside_zone_m2','ea_capture_fraction','spatial_enrichment',
                  'total_corridor_erosion_capture_fraction','fived_transition_footprint_capture',
                  'fived_observed_transition_area_m2','ea_date_provenance','verification_status']
            # Write complete, audit-ready correspondence summary.
            with summaryfile.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
            # Also write the combined-only subset when both pathways are analysed.
            with combinedfile.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
                w.writerows([r for r in rows if r['transition']=='FP+DS combined'])
            # Persist PASS/WARN/FAIL diagnostics with numerical tolerances and explanations.
            with qafile.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['scope','value_m2','tolerance_m2','status','note']);w.writeheader();w.writerows(qa)
            # Manifest uses original source script name as provenance literal (unchanged).
            manifest={'script':'FRAF_Module5d_EA_Erosion_Susceptibility_Correspondence_v1_2.py',
                      'created_utc':stamp,'river':river,'forecast':forecast,'y1':y1,'y2':y2,
                      # Capture each pathway’s source layer, model label and scored source mode.
                      'pathways':{k:{'model':v[2],'zones':v[0].source(),
                                    'risk_input':v[1].source(), 'risk_source_mode':risk_modes[k],
                                    'scored_cell_count':scored_counts.get(k)} for k,v in paths.items()},
                      'EA_input':ea.source(),'valid_support':support.source() if support else None,
                      'EA_class_field':self.parameterAsString(params,'EA_CLASS_FIELD',context),
                      'erosion_classes':self.parameterAsString(params,'EROSION_CLASSES',context),
                      # Record EA dating method and requested thresholds to prevent interval ambiguity.
                      'EA_provenance':provenance,'thresholds_top_pct':tops,
                      'verify_zone_ranks':check_zone_ranks,'5d_summary':csv_5d or None,
                      'combined_CSV':str(combinedfile),
                      # Record inside/outside risk erosion areas and the geometry area unit.
                      'EA_total_area_m2':total,'EA_within_model_union_m2':a_eligible,
                      'EA_outside_model_union_m2':a_other,'spatial_layers':written,
                      'geometry_area_units':'square metres; planar projected CRS '+crs.authid(),
                      # Document the T1-only scored eligibility and held-out evaluation assumptions.
                      'assumptions':['In continuous mode T1 risk is extracted from P_STATUS=predicted AND P_RISKSET=1.',
                                     'The model label, transition, forecast and observation dates are verified against the continuous fields.',
                                     'Risk masks are T1 eligible AND scored/valid and use same PLACE support as the 5c2 zones.',
                                     # EA geometry is the observed physical process, not automatically a state event.
                                     'EA erosion is subsequently observed, not the transition actual_footprint.',
                                     'EA polygon area within eligible PLACE support is not necessarily erosion derived from the labelled start state.',
                                     'A high-susceptibility zone not eroded is not a false erosion forecast.',
                                     'All analysed model/forecast/interval combinations are held out when used for independent assessment.']}
            # Write JSON manifest only after calculations and CSV outputs are available.
            manifestfile.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
            # COMPLETED marker denotes successful progress through the output-writing path.
            status.write_text('COMPLETED\n',encoding='utf-8')
            feedback.pushInfo(f'COMPLETE: {len(rows)} results, {len(qa)} QA records → {out}')
        # Failures retain a FAILED_OR_INCOMPLETE marker with the underlying exception.
        except Exception as e:
            status.write_text('FAILED_OR_INCOMPLETE\n'+str(e)+'\n',encoding='utf-8')
            raise
        # Return paths of the generated files to QGIS Processing.
        return {'SUMMARY':str(summaryfile),'QA':str(qafile),'MANIFEST':str(manifestfile),
                'OUTPUT_GPKG':str(gpkg) if save and gpkg.exists() else ''}
