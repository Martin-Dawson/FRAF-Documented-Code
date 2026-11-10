# -*- coding: utf-8 -*-
"""FRAF — 5D–EA outside-scored-risk attribution reconciliation v1.0 (2026-10-21).

QGIS 3.44.9 Processing script; one invocation processes Mamore T35 and Jamuna T35.
Can be reused for other origins if matching audit interval and 5D–EA GPKGs exist.

INDEPENDENT AXES (NEVER CONFLATE):
  A) EA–PLACE audit: physical EA erosion polygons labelled by contemporaneous
     PLACE nominal/effective state sequence / event mask.
  B) Module 5D–EA: all observed EA erosion, erosion inside and outside the
     union of antecedently eligible AND ACTUALLY SCORED FP->AD and DS->AD cells.
The two EA input footprints must be checked geometrically, not merely by area.

Modes:
  STRICT: attribute only rivers with coincident EA erosion geometry.
          On mismatch, export geometry differences and report BLOCKED; do not
          silently interpret output as exact. The other river may still pass.
  DIAGNOSTIC: additionally attribute the overlapping outside-risk footprint,
          keep the unreconciled portion explicit; outputs are PROVISIONAL.

Neither 'outside event masks' nor effective AD->AD automatically means physical
AD persistence or outside scored populations. FP eligibility means eligible
pre-existing floodplain + SF, explicitly excluding DS. DS has its own model.

All input files are read-only. Outputs are NEW timestamped directory.
"""
# [P2 ARCHIVE] FRAF PAPER 2 / PUBLICATION SOURCE ANNOTATIONS — two-river T35 reconciliation.
# [P2 ARCHIVE] Archive alias: FRAF_P2_DIAG_OutsideScoredRiskReconciliation_v1_0.py
# [P2 ARCHIVE] Original: FRAF_5D_EA_Outside_Risk_Attribution_Reconciliation_v1_0.py
# [P2 ARCHIVE] Role: independent EA–PLACE audit versus 5D–EA scored-population partition.
# [P2 ARCHIVE] Outputs: 01_erosion_geometry_comparison, 02_outside_risk_attribution,
# [P2 ARCHIVE] 03_scored_population_exclusions, 04_annual_area_QA, 05_two_river_comparison
# [P2 ARCHIVE] and 06_reconciliation_maps (original suffixes preserved in executable).
# [P2 ARCHIVE] STRICT geometry mismatch: block attribution for the affected river.
# [P2 ARCHIVE] DIAGNOSTIC mismatch: classify common footprint; retain unmatched erosion
# [P2 ARCHIVE] and flag results PROVISIONAL. Do not equate diagnostic status with a QA PASS.
# [P2 ARCHIVE] Outside scored FP/DS support is not equivalent to outside event-cell masks.
# [P2 ARCHIVE] Archive action: COMMENTS ONLY. No change to script ID, Processing
# [P2 ARCHIVE] parameters, geometry logic, thresholds, output names or model populations.

from __future__ import annotations

import collections
import csv
import json
import math
import re
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature, QgsFeatureRequest, QgsField, QgsFields, QgsGeometry,
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingOutputFile, QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum, QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterNumber,
    QgsProcessingParameterString, QgsUnitTypes, QgsVectorFileWriter,
    QgsVectorLayer, QgsWkbTypes,
)

# [P2 ARCHIVE] Require the full EA footprint, scored subset, outside subset and separate
# [P2 ARCHIVE] FP and DS risk masks from the original 5D–EA reconciliation outputs.
REQUIRED_5DEA = ('ea_all', 'ea_all_eligible', 'ea_outside_risks', 'risk_FP', 'risk_DS')
# [P2 ARCHIVE] The v1.1.1 EA–PLACE attribution layer supplies independent geometry.
AUDIT_LAYER = 'ea_erosion_by_place_annual'


# [P2 ARCHIVE] Normalize and validate observation-date strings for exact interval joins.
def normdate(raw):
    s = re.sub(r'[^0-9]', '', str(raw or ''))
    if len(s) == 4:
        s += '0101'
    if len(s) != 8:
        raise ValueError('Expected YYYYMMDD: %r' % raw)
    return s


# [P2 ARCHIVE] Treat common NULL markers as missing rather than category evidence.
def textval(raw):
    if raw is None:
        return ''
    s = str(raw).strip()
    return '' if s.upper() in ('NULL', 'NONE', 'NA', 'NAN') else s


# [P2 ARCHIVE] Locate required field-name variants in the input GeoPackage schema.
def firstfield(layer, options, required=True):
    lookup = {n.upper(): n for n in layer.fields().names()}
    for opt in options:
        if opt.upper() in lookup:
            return lookup[opt.upper()]
    if required:
        raise QgsProcessingException(
            '%s lacks expected field %s; available: %s' %
            (layer.name(), options, layer.fields().names()[:35]))
    return None


# [P2 ARCHIVE] Classify nominal/effective PLACE sequences and event-mask evidence.
# [P2 ARCHIVE] AD→AD and recognised masks are descriptive, not inferred scour causes.
def history_class(event_mask, nominal_seq, effective_seq, map_class):
    """Mutually exclusive audit classification, not physical source proof."""
    ev = textval(event_mask).upper()
    nominal = textval(nominal_seq).upper()
    effective = textval(effective_seq).upper()
    mapc = textval(map_class).upper()
    if ev == 'FP_EVENT':
        return 'FP_EVENT_MASK_OUTSIDE_SCORED'
    if ev == 'DS_EVENT':
        return 'DS_EVENT_MASK_OUTSIDE_SCORED'
    if nominal == 'AD_TO_AD':
        return 'NOMINAL_AD_TO_AD'
    if effective == 'AD_TO_AD':
        return 'EFFECTIVE_AD_TO_AD_OTHER_NOMINAL'
    if 'THRESHOLD' in mapc:
        return 'BELOW_AD_STATE_THRESHOLD'
    if 'UNRESOLVED' in nominal or 'UNRESOLVED' in effective:
        return 'OTHER_UNRESOLVED_STATE_HISTORY'
    if effective:
        return 'OTHER_CLASSIFIED_SEQUENCE'
    return 'STATE_HISTORY_MISSING'


# [P2 ARCHIVE] Contrast original eligible FP/DS metadata with actual scoring support.
# [P2 ARCHIVE] An eligible-but-unscored cell must not be silently relabelled ineligible.
def antecedent_class(effective_seq, fp_model_eligible='', ds_model_eligible='',
                     fp_source='', fp_exclusion='', ds_exclusion=''):
    """Do not call an unscored surface 'ineligible' without separate evidence.

    Eligibility flags from original Stage 4 risk are not equivalent to actual
    5c model scoring. An UNKNOWN flag remains UNKNOWN. Pre-existing FP may have
    unresolved primary nominal state; source metadata is therefore retained.
    """
    effective = textval(effective_seq).upper()
    t1 = effective.split('_TO_')[0] if '_TO_' in effective else 'UNRESOLVED'
    fp = textval(fp_model_eligible)
    ds = textval(ds_model_eligible)
    source = textval(fp_source)
    if t1 == 'AD':
        cat = 'T1_AD_OUTSIDE_FP_DS_POPULATIONS_BY_DESIGN'
    elif ds in ('1', '1.0'):
        cat = 'DS_ORIGINAL_ELIGIBLE_BUT_NOT_SCORED'
    elif fp in ('1', '1.0'):
        cat = 'FP_ORIGINAL_ELIGIBLE_BUT_NOT_SCORED'
    elif t1 == 'DS':
        cat = 'T1_DS_UNSCORED_ELIGIBILITY_UNRESOLVED'
    elif t1 == 'SF':
        cat = 'T1_SF_UNSCORED_ELIGIBILITY_UNRESOLVED'
    elif source and ('PREEXIST' in source.upper() or 'FLOODPLAIN' in source.upper()):
        cat = 'PREEXISTING_FP_CANDIDATE_UNSCORED'
    else:
        cat = 'T1_UNRESOLVED_OR_OTHER_UNSCORED'
    reason = textval(ds_exclusion) if t1 == 'DS' else textval(fp_exclusion)
    return cat, t1, reason or 'NOT_AVAILABLE'


# [P2 ARCHIVE] QGIS Processing algorithm for paired Mamoré/Jamuna T35 geometry
# [P2 ARCHIVE] and outside-scored FP/DS risk population attribution.
class FRAFOutsideRiskAttributionReconciliation(QgsProcessingAlgorithm):
    # [P2 ARCHIVE] Retain original QGIS algorithm identifier after archive filename change.
    def name(self):
        return 'fraf_5d_ea_outside_risk_attribution_reconciliation_v1_0'

    # [P2 ARCHIVE] Retain original visible QGIS Processing algorithm name.
    def displayName(self):
        return 'FRAF — 5D–EA Outside-Risk Attribution Reconciliation v1.0 (both rivers)'

    # [P2 ARCHIVE] Retain QGIS toolbox grouping.
    def group(self):
        return 'FRAF Floodplain Reassemblage'

    # [P2 ARCHIVE] Retain stable Processing group identifier.
    def groupId(self):
        return 'fraf_floodplain_reassemblage'

    # [P2 ARCHIVE] Produce original algorithm implementation without behavioural changes.
    def createInstance(self):
        return FRAFOutsideRiskAttributionReconciliation()

    # [P2 ARCHIVE] Expose strict versus diagnostic geometry support qualifications to users.
    def shortHelpString(self):
        return (
            'Reconciles T35 EA–PLACE attributed erosion against original 5D–EA '
            'actual erosion and physically outside-scored-risk footprints, for '
            'Mamoré and Jamuna in a single run. Select each river\'s audit '
            '09_annual_erosion_attribution_maps.gpkg and 5D–EA '
            'EA_Susceptibility_Correspondence.gpkg (P1; optionally P2). '
            'Requires per-run EA_Susceptibility_manifest.json unless explicitly '
            'overridden. Checks geometric symdiff and inside/outside partition. '
            'Strict mode prevents attribution for mismatched EA geometry; diagnostic '
            'mode retains unmatched area and marks it PROVISIONAL. '
            'May also join optional 01_place_interval_attribution.csv to distinguish '
            'original-eligible but unscored locations from unknown eligibility. '
            'Outputs per-river and comparison CSVs plus polygon QA GeoPackage. '
            'All data remain read-only. T35 interval defaults: Mamoré 2020–2021, '
            'Jamuna 2023–2024.')

    # [P2 ARCHIVE] Receive per-river EA audit and 5D–EA GeoPackages, optional P2
    # [P2 ARCHIVE] and risk-detail sources, origin dates and geometry tolerance parameters.
    def initAlgorithm(self, config=None):
        # [P2 ARCHIVE] Read frozen run inputs per river; optionally compare P1 and P2 scored
        # [P2 ARCHIVE] geometries without altering the model outputs.
        for p,title in (
            ('M_AUDIT', 'Mamoré — audit 09_annual_erosion_attribution_maps.gpkg'),
            ('M_5DEA_P1', 'Mamoré — T35 P1 5D–EA EA_Susceptibility_Correspondence.gpkg'),
            ('J_AUDIT', 'Jamuna — audit 09_annual_erosion_attribution_maps.gpkg'),
            ('J_5DEA_P1', 'Jamuna — T35 P1 5D–EA EA_Susceptibility_Correspondence.gpkg'),
        ):
            self.addParameter(QgsProcessingParameterFile(
                p, title, behavior=QgsProcessingParameterFile.File,
                fileFilter='GeoPackage (*.gpkg)'))
        # [P2 ARCHIVE] Read frozen run inputs per river; optionally compare P1 and P2 scored
        # [P2 ARCHIVE] geometries without altering the model outputs.
        for p,title in (
            ('M_5DEA_P2', 'Mamoré — matching T35 P2 5D–EA GeoPackage (optional P1/P2 geometry QA)'),
            ('J_5DEA_P2', 'Jamuna — matching T35 P2 5D–EA GeoPackage (optional P1/P2 geometry QA)'),
        ):
            self.addParameter(QgsProcessingParameterFile(
                p,title,behavior=QgsProcessingParameterFile.File,
                fileFilter='GeoPackage (*.gpkg)',optional=True))
        # [P2 ARCHIVE] Read frozen run inputs per river; optionally compare P1 and P2 scored
        # [P2 ARCHIVE] geometries without altering the model outputs.
        for p,title in (
            ('M_DETAIL', 'Mamoré — audit 01_place_interval_attribution.csv (optional exclusion evidence)'),
            ('J_DETAIL', 'Jamuna — audit 01_place_interval_attribution.csv (optional exclusion evidence)'),
        ):
            self.addParameter(QgsProcessingParameterFile(
                p,title,behavior=QgsProcessingParameterFile.File,
                fileFilter='CSV (*.csv)',optional=True))
        # [P2 ARCHIVE] T35 native intervals differ by river: Mamoré 2020–2021, Jamuna
        # [P2 ARCHIVE] 2023–2024. These are one-interval reconciliation windows.
        for code, default1, default2 in (('M','20200101','20210101'),('J','20230101','20240101')):
            self.addParameter(QgsProcessingParameterString(code+'_Y1',code+' observation start YYYYMMDD',defaultValue=default1))
            self.addParameter(QgsProcessingParameterString(code+'_Y2',code+' observation end YYYYMMDD',defaultValue=default2))
        self.addParameter(QgsProcessingParameterString('FORECAST','Forecast label',defaultValue='T35'))
        # [P2 ARCHIVE] Strict geometry comparison is the publication-grade default.
        # [P2 ARCHIVE] Diagnostic mode preserves an explicit provisional alternative.
        self.addParameter(QgsProcessingParameterEnum(
            'GEOMETRY_POLICY','Geometry mismatch policy',options=[
                'STRICT — block attribution for a river with EA geometry mismatch',
                'DIAGNOSTIC — explicitly report unmatched and classify matched intersection (PROVISIONAL)',
            ],defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(
            'ABS_TOL_M2','Area/conservation/geometry tolerance (m²)',
            type=QgsProcessingParameterNumber.Double,defaultValue=1.0,minValue=0.0))
        self.addParameter(QgsProcessingParameterNumber(
            'REL_TOL','Maximum relative conservation tolerance (fraction)',
            type=QgsProcessingParameterNumber.Double,defaultValue=1e-9,minValue=0.0))
        self.addParameter(QgsProcessingParameterBoolean(
            'REQUIRE_5DEA_MANIFEST','Require interval- and river-matching sibling 5D–EA JSON manifest',defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            'PRESERVE_WORKING','Retain intermediate overlay GeoPackages (large)',defaultValue=False))
        self.addParameter(QgsProcessingParameterFolderDestination(
            'OUTPUT_FOLDER','Existing parent output directory (creates timestamped subfolder)'))
        for key in ('MANIFEST','GEOMETRY_CSV','ATTRIBUTION_CSV','EXCLUSIONS_CSV','QA_CSV','TWO_RIVER_CSV','OUTPUT_GPKG','RUN_STATUS'):
            self.addOutput(QgsProcessingOutputFile(key,key.replace('_',' ').title()))

    # [P2 ARCHIVE] Open an exact named polygon layer; reject wrong geometry and missing input.
    @staticmethod
    def _vec(path, layername, label, allow_empty=False):
        p = Path(path)
        if not p.is_file():
            raise QgsProcessingException('%s not found: %s' % (label,p))
        l = QgsVectorLayer(str(p)+'|layername='+layername,label,'ogr')
        if not l.isValid():
            raise QgsProcessingException('%s: GPKG missing polygon layer [%s]: %s' % (label,layername,p))
        if QgsWkbTypes.geometryType(l.wkbType()) != QgsWkbTypes.PolygonGeometry:
            raise QgsProcessingException('%s [%s] not polygonal' % (label,layername))
        if not allow_empty and l.featureCount() == 0:
            raise QgsProcessingException('%s [%s] has zero features' % (label,layername))
        if l.crs().isGeographic() or l.crs().mapUnits() != QgsUnitTypes.DistanceMeters:
            raise QgsProcessingException('%s requires projected metre CRS' % label)
        return l

    # [P2 ARCHIVE] Sum positive polygon areas without treating null geometries as erosion.
    @staticmethod
    def _area(layer):
        if layer is None:
            return 0.0
        s=0.0
        for f in layer.getFeatures(QgsFeatureRequest().setNoAttributes()):
            g=f.geometry()
            if g and not g.isEmpty():
                a=g.area()
                if not math.isfinite(a) or a < -1e-4:
                    raise QgsProcessingException('Invalid/nonfinite geometry area')
                s+=max(0.0,a)
        return s

    # [P2 ARCHIVE] Write fixed-schema, UTF-8 QA and provenance reports.
    @staticmethod
    def _writecsv(path, rows, fields):
        with open(path,'w',encoding='utf-8-sig',newline='') as h:
            w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore')
            w.writeheader();w.writerows(rows)

    # [P2 ARCHIVE] Run a child QGIS native algorithm to a new scratch GeoPackage.
    @staticmethod
    def _emitnative(alg,parameters,context,feedback,outfile):
        parameters=dict(parameters);parameters['OUTPUT']=str(outfile)
        result=processing.run(alg,parameters,context=context,feedback=feedback,is_child_algorithm=True)
        name=result['OUTPUT']
        l=QgsVectorLayer(str(name),outfile.stem,'ogr')
        if not l.isValid():
            raise QgsProcessingException('Could not open %s output %s' %(alg,name))
        return l

    # [P2 ARCHIVE] Extract the interval matching frozen T35 observation dates, not
    # [P2 ARCHIVE] the complete five-year cumulative footprint.
    @classmethod
    def _filter_year(cls,l,y1,y2,scratch,context,feedback):
        fy1=firstfield(l,['Y1']);fy2=firstfield(l,['Y2'])
        expr=('regexp_replace(to_string("%s"),\'[^0-9]\',\'\') = \'%s\' AND '
              'regexp_replace(to_string("%s"),\'[^0-9]\',\'\') = \'%s\'' %
              (fy1,y1,fy2,y2))
        output=cls._emitnative('native:extractbyexpression',{'INPUT':l,'EXPRESSION':expr},
                              context,feedback,scratch/'attribution_interval.gpkg')
        if output.featureCount()==0:
            raise QgsProcessingException('Audit has no eroded fragments for interval %s–%s' %(y1,y2))
        return output

    # [P2 ARCHIVE] Perform explicit polygon overlay in temporary reproducible files.
    @classmethod
    def _overlay(cls,alg,a,b,label,scratch,context,feedback):
        if a is None or a.featureCount()==0:
            return None
        if b is None or b.featureCount()==0:
            return a if alg=='difference' else None
        f=scratch/(label+'.gpkg')
        params={'INPUT':a,'OVERLAY':b}
        return cls._emitnative('native:'+alg,params,context,feedback,f)

    # [P2 ARCHIVE] Write difference, matched and unmatched support geometries for review.
    @classmethod
    def _export_layer(cls,layer,gpkg,name,context):
        if layer is None or layer.featureCount()==0:
            return False
        opts=QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName='GPKG';opts.layerName=name
        opts.actionOnExistingFile=(QgsVectorFileWriter.CreateOrOverwriteLayer if gpkg.exists()
                                   else QgsVectorFileWriter.CreateOrOverwriteFile)
        result=QgsVectorFileWriter.writeAsVectorFormatV3(layer,str(gpkg),context.transformContext(),opts)
        if result[0]!=QgsVectorFileWriter.NoError:
            raise QgsProcessingException('Unable to export %s: %s' %(name,result))
        return True

    # [P2 ARCHIVE] Preserve exact eroded fragments and attach mutually exclusive history,
    # [P2 ARCHIVE] scoring support and original eligibility/exclusion labels.
    @classmethod
    def _write_enriched(cls,overlay, gpkg,layername,context,detail):
        """Streaming output of exact fragments, with exclusive provenance labels."""
        if overlay is None or overlay.featureCount()==0:
            return collections.Counter(),collections.Counter(),collections.Counter(),0.0,0
        opts=QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName='GPKG';opts.layerName=layername
        opts.actionOnExistingFile=(QgsVectorFileWriter.CreateOrOverwriteLayer if gpkg.exists()
                                   else QgsVectorFileWriter.CreateOrOverwriteFile)
        # Never carry a GeoPackage provider FID into another GeoPackage: a
        # spatial intersection can split one source feature into several output
        # fragments, and inherited primary keys can then collide.
        # [P2 ARCHIVE] Construct a new output schema without inheriting source GeoPackage FIDs.
        fields=QgsFields()
        source_indices=[]
        for i, field in enumerate(overlay.fields()):
            if field.name().lower() == 'fid':
                continue
            fields.append(field)
            source_indices.append(i)
        for fname,ftype in (('OUT_HISTORY',QVariant.String),('OUT_RISK',QVariant.String),
                            ('OUT_T1',QVariant.String),('OUT_EXCLUSION',QVariant.String),
                            ('DETAIL_STATUS',QVariant.String),('OUT_ERODED_M2',QVariant.Double)):
            if fname in fields.names():
                raise QgsProcessingException('Output column collision: '+fname)
            fields.append(QgsField(fname,ftype))
        wr=QgsVectorFileWriter.create(str(gpkg),fields,QgsWkbTypes.MultiPolygon,
                                     overlay.crs(),context.transformContext(),opts)
        if wr is None or wr.hasError()!=QgsVectorFileWriter.NoError:
            raise QgsProcessingException('Cannot create attributed outside-risk map '+layername)
        count=0;total=0.0
        history=collections.Counter();risk=collections.Counter();hist_risk=collections.Counter()
        try:
            fs={k:firstfield(overlay,[k],required=False) for k in
                ('Y1','Y2','BLOCK_ID','EA_SOURCE','EVENT_MASK','NOMINAL_SEQ',
                 'EFFECTIVE_SEQ','MAP_CLASS')}
            # [P2 ARCHIVE] Attribute each clipped outside-scored erosion fragment, not its whole cell.
            for src in overlay.getFeatures():
                g=QgsGeometry(src.geometry())
                if not g or g.isEmpty() or g.area()<1e-12:
                    continue
                if not g.isMultipart():
                    g.convertToMultiType()
                orig={name:textval(src[fld]) if fld else '' for name,fld in fs.items()}
                hk=history_class(orig['EVENT_MASK'],orig['NOMINAL_SEQ'],
                                 orig['EFFECTIVE_SEQ'],orig['MAP_CLASS'])
                key=(normdate(orig['Y1']),normdate(orig['Y2']),orig['BLOCK_ID'],
                     orig['EA_SOURCE'].upper(),orig['EVENT_MASK'].upper())
                dr=detail.get(key)
                status='MATCHED_DETAIL' if dr is not None else 'NO_DETAIL_OR_NO_JOIN_MATCH'
                dr=dr or {}
                rk,t1,reason=antecedent_class(orig['EFFECTIVE_SEQ'],
                           dr.get('FP_MODEL_ELIGIBLE',''),dr.get('DS_MODEL_ELIGIBLE',''),
                           dr.get('FP_SOURCE_PRIMARY',''),dr.get('FP_EXCLUSION',''),
                           dr.get('DS_EXCLUSION',''))
                area=g.area()
                new=QgsFeature(fields)
                new.setGeometry(g)
                new.setAttributes([src.attributes()[i] for i in source_indices]+
                                  [hk,rk,t1,reason,status,float(area)])
                if not wr.addFeature(new):
                    raise QgsProcessingException('Cannot append mapped erosion fragment')
                history[hk]+=area;risk[rk]+=area;hist_risk[(hk,rk,reason,status)]+=area
                total+=area;count+=1
        finally:
            del wr
        return history,risk,hist_risk,total,count

    # [P2 ARCHIVE] Join optional antecedent eligibility evidence on interval and BLOCK_ID
    # [P2 ARCHIVE] together with EA source/mask; never invent missing eligibility.
    @staticmethod
    def _read_detail(path,y1,y2,feedback):
        if not path:
            return {}
        p=Path(path)
        if not p.is_file():
            raise QgsProcessingException('Optional detail CSV not found: '+str(p))
        wanted=('Y1','Y2','BLOCK_ID','EA_SOURCE','EVENT_MASK')
        target={};n=0
        # [P2 ARCHIVE] Read optional Stage 4 eligibility evidence as an immutable reference.
        with open(p,encoding='utf-8-sig',newline='') as h:
            r=csv.DictReader(h)
            missing=[x for x in wanted if x not in (r.fieldnames or [])]
            if missing:
                raise QgsProcessingException('Audit detail CSV missing '+str(missing))
            for row in r:
                try:
                    if normdate(row['Y1'])!=y1 or normdate(row['Y2'])!=y2:
                        continue
                except ValueError:
                    continue
                k=(y1,y2,textval(row['BLOCK_ID']),textval(row['EA_SOURCE']).upper(),
                   textval(row['EVENT_MASK']).upper())
                if k in target:
                    raise QgsProcessingException('Duplicate audit detail join key '+str(k))
                target[k]=row;n+=1
        feedback.pushInfo('Loaded %s interval-specific original risk/eligibility detail records' %n)
        return target

    # [P2 ARCHIVE] Verify each 5D–EA source is the expected river, interval, forecast
    # [P2 ARCHIVE] and has both FP and DS scored risk pathways.
    @staticmethod
    def _manifest_check(gpkg,river,forecast,y1,y2,required):
        # [P2 ARCHIVE] Check the sibling manifest to guard against mixing forecasts or rivers.
        p=Path(gpkg).parent/'EA_Susceptibility_manifest.json'
        if not p.is_file():
            if required:
                raise QgsProcessingException('5D–EA companion manifest required: '+str(p))
            return {'status':'UNATTESTED_MANIFEST_MISSING','path':str(p)}
        data=json.loads(p.read_text(encoding='utf-8-sig'))
        rv=textval(data.get('river')).lower()
        if rv not in (river.lower(),river.lower().replace('é','e')):
            raise QgsProcessingException('%s 5D–EA manifest river mismatch: %r' %(river,data.get('river')))
        if textval(data.get('forecast')).upper()!=forecast.upper():
            raise QgsProcessingException('%s 5D–EA manifest forecast mismatch: %r' %(river,data.get('forecast')))
        if normdate(data.get('y1'))!=y1 or normdate(data.get('y2'))!=y2:
            raise QgsProcessingException('%s 5D–EA manifest date mismatch' %river)
        if not {'FP','DS'}.issubset(set(data.get('pathways',{}))):
            raise QgsProcessingException('%s 5D–EA run lacks scored FP and DS populations' %river)
        return {'status':'PASS','path':str(p),'ea_input':data.get('EA_input'),
                'erosion_classes':data.get('erosion_classes'),
                'EA_total_area_m2':data.get('EA_total_area_m2'),
                'scored_cells_FP':data['pathways']['FP'].get('scored_cell_count'),
                'scored_cells_DS':data['pathways']['DS'].get('scored_cell_count')}

    # [P2 ARCHIVE] Reconcile one river independently so a Jamuna geometry mismatch does
    # [P2 ARCHIVE] not change or overwrite the separate Mamoré status or attribution.
    def _river(self,code,river,params,context,feedback,folder,mapgpkg,abs_tol,rel_tol,
               strict,manifest_required,keep):
        get=lambda key:textval(self.parameterAsFile(params,code+'_'+key,context))
        audit_p=get('AUDIT');p1_p=get('5DEA_P1');p2_p=get('5DEA_P2');detail_p=get('DETAIL')
        y1=normdate(self.parameterAsString(params,code+'_Y1',context))
        y2=normdate(self.parameterAsString(params,code+'_Y2',context))
        forecast=textval(self.parameterAsString(params,'FORECAST',context)).upper()
        if y1>=y2:
            raise QgsProcessingException('%s invalid year order' %river)
        # [P2 ARCHIVE] Scratch geometry is per river and per run; original input geometry is untouched.
        scratch=folder/('working_'+code)
        scratch.mkdir(parents=True,exist_ok=False)
        feedback.pushInfo('[%s] %s–%s %s' %(river,y1,y2,forecast))
        rm={'river':river,'forecast':forecast,'Y1':y1,'Y2':y2,
            'audit':audit_p,'5DEA_P1':p1_p,'5DEA_P2':p2_p or None,'detail':detail_p or None,
            'scratch':str(scratch),'geometry_policy':'STRICT' if strict else 'DIAGNOSTIC'}
        geometry=[];attribution=[];exclusions=[];qas=[];comparison=[]

        def qa(check, value, tol, note=''):
            status='PASS' if value<=tol else 'FAIL'
            qas.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                             check=check,value_m2=value,tolerance_m2=tol,status=status,note=note))
            return status=='PASS'

        try:
            # [P2 ARCHIVE] Obtain the independent audit and verified 5D–EA scored/outside layers.
            attribution_source=self._vec(audit_p,AUDIT_LAYER,river+' audit')
            for mandatory in ('Y1','Y2','BLOCK_ID','EVENT_MASK','EA_SOURCE',
                              'NOMINAL_SEQ','EFFECTIVE_SEQ','AD_SUBCLASS','MAP_CLASS'):
                firstfield(attribution_source,[mandatory])
            l={name:self._vec(p1_p,name,river+' P1 '+name) for name in REQUIRED_5DEA}
            sources=[attribution_source]+list(l.values())
            if any(a.crs()!=l['ea_all'].crs() for a in sources):
                raise QgsProcessingException('%s audit / 5D–EA CRS differ; reproject inputs first (no silent on-the-fly transform)'%river)
            rm['crs']=l['ea_all'].crs().authid()
            if rm['crs'] not in (('EPSG:32720',) if code=='M' else ('EPSG:32646',)):
                feedback.pushWarning('[%s] CRS differs from expected: %s' %(river,rm['crs']))
            rm['P1_manifest']=self._manifest_check(p1_p,river,forecast,y1,y2,manifest_required)
            if p2_p:
                rm['P2_manifest']=self._manifest_check(p2_p,river,forecast,y1,y2,manifest_required)
            audit=self._filter_year(attribution_source,y1,y2,scratch,context,feedback)
            base=l['ea_all'];eligible=l['ea_all_eligible'];outside=l['ea_outside_risks']
            sum_a=self._area(audit);sum_e=self._area(base);sum_el=self._area(eligible);sum_out=self._area(outside)
            tol=lambda a,b: max(abs_tol,rel_tol*max(a,b))
            # [P2 ARCHIVE] Erosion inside and outside the scored union must account for all 5D EA.
            qa('EA_ELIGIBLE_PLUS_OUTSIDE_CLOSURE',abs(sum_e-sum_el-sum_out),tol(sum_e,sum_el),
               'Must equal full 5D–EA source erosion area')
            risk_full={}
            risk_full['FP']=self._area(l['risk_FP'])
            risk_full['DS']=self._area(l['risk_DS'])
            feedback.pushInfo('[%s] audit %.6f km²; 5D–EA %.6f km²; outside %.6f km²' %
                              (river,sum_a/1e6,sum_e/1e6,sum_out/1e6))

            # Independently test actual polygon differences (not just net area).
            # [P2 ARCHIVE] Symmetric difference checks spatial coincidence, not just equal total area.
            a_only=self._overlay('difference',audit,base,'audit_only',scratch,context,feedback)
            e_only=self._overlay('difference',base,audit,'5DEA_only',scratch,context,feedback)
            aonly=self._area(a_only);eonly=self._area(e_only)
            intersection_a=sum_a-aonly
            intersection_e=sum_e-eonly
            mismatch=aonly+eonly
            geo_pass=qa('EA_GEOMETRY_SYMMETRIC_DIFFERENCE',mismatch,tol(sum_a,sum_e),
                        'Audit-only + 5D-only. Net area discrepancy is NOT the symmetric difference')
            qa('EA_COMMON_FOOTPRINT_MASS_BALANCE',abs(intersection_a-intersection_e),
               tol(sum_a,sum_e),'Audit/E common intersection computed from independent differences')
            # [P2 ARCHIVE] Log both unmatched directions; no cancellation of opposite errors.
            geometry.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                     audit_area_m2=sum_a,fived_ea_area_m2=sum_e,
                     net_5d_minus_audit_m2=sum_e-sum_a,
                     audit_only_m2=aonly,fived_only_m2=eonly,
                     symmetric_difference_m2=mismatch,
                     common_area_from_audit_m2=intersection_a,
                     common_area_from_5d_m2=intersection_e,
                     geometry_status='PASS' if geo_pass else 'MISMATCH',
                     tolerance_m2=tol(sum_a,sum_e),
                     outside_scored_m2=sum_out,eligible_scored_m2=sum_el,
                     fp_scored_risk_area_m2=risk_full['FP'],ds_scored_risk_area_m2=risk_full['DS']))
            self._export_layer(a_only,mapgpkg,code+'_audit_only',context)
            self._export_layer(e_only,mapgpkg,code+'_5DEA_only',context)

            # Internal scorer masks: provenance verification beyond total areas.
            # [P2 ARCHIVE] Recheck the scorer's inside/outside mask partition and containment.
            ov=self._overlay('intersection',eligible,outside,'eligible_outside_overlap',scratch,context,feedback)
            qa('ELIGIBLE_OUTSIDE_OVERLAP',self._area(ov),tol(sum_e,sum_el),
               '5D–EA inside and outside masks must be spatially disjoint')
            extra=self._overlay('difference',outside,base,'outside_not_in_ea_all',scratch,context,feedback)
            qa('OUTSIDE_FOOTPRINT_NOT_IN_EA_ALL',self._area(extra),tol(sum_e,sum_out))
            el_extra=self._overlay('difference',eligible,base,'eligible_not_in_ea_all',scratch,context,feedback)
            qa('ELIGIBLE_FOOTPRINT_NOT_IN_EA_ALL',self._area(el_extra),tol(sum_e,sum_el))
            rem_ea=self._overlay('difference',base,outside,'EA_minus_outside',scratch,context,feedback)
            rem_after=self._overlay('difference',rem_ea,eligible,'EA_not_in_either_mask',scratch,context,feedback)
            qa('EA_NOT_COVERED_BY_ELIGIBLE_OR_OUTSIDE',self._area(rem_after),tol(sum_e,sum_el))
            for pathway in ('FP','DS'):
                leak=self._overlay('intersection',outside,l['risk_'+pathway],
                                    'outside_leaks_'+pathway,scratch,context,feedback)
                qa('OUTSIDE_LEAKAGE_IN_SCORED_'+pathway,self._area(leak),tol(sum_e,sum_out))

            # [P2 ARCHIVE] P2 comparisons, when supplied, test equivalent frozen scored support.
            p2check='NOT_REQUESTED'
            if p2_p:
                p2check='PASS'
                p2ea=self._vec(p2_p,'ea_all',river+' P2 ea_all')
                if p2ea.crs()!=base.crs():
                    raise QgsProcessingException('%s P2 EA CRS differs from P1' %river)
                pae=self._overlay('difference',base,p2ea,'EA_P1_not_P2',scratch,context,feedback)
                eap=self._overlay('difference',p2ea,base,'EA_P2_not_P1',scratch,context,feedback)
                if not qa('P1_P2_EA_ALL_SOURCE_SYMDIFF',self._area(pae)+self._area(eap),
                          tol(sum_e,self._area(p2ea))):
                    p2check='MISMATCH'
                self._export_layer(pae,mapgpkg,code+'_EA_P1_only',context)
                self._export_layer(eap,mapgpkg,code+'_EA_P2_only',context)
                for pathway in ('FP','DS'):
                    p2layer=self._vec(p2_p,'risk_'+pathway,river+' P2 risk '+pathway)
                    if p2layer.crs()!=base.crs():
                        raise QgsProcessingException('%s P2 risk CRS differs from P1' %river)
                    d12=self._overlay('difference',l['risk_'+pathway],p2layer,
                                      pathway+'_P1_not_P2',scratch,context,feedback)
                    d21=self._overlay('difference',p2layer,l['risk_'+pathway],
                                      pathway+'_P2_not_P1',scratch,context,feedback)
                    sym=self._area(d12)+self._area(d21)
                    if not qa('P1_P2_'+pathway+'_SCORED_MASK_SYMDIFF',sym,
                              tol(self._area(p2layer),risk_full[pathway])):
                        p2check='MISMATCH'
                    self._export_layer(d12,mapgpkg,code+'_'+pathway+'_P1_only',context)
                    self._export_layer(d21,mapgpkg,code+'_'+pathway+'_P2_only',context)
            rm['P1_P2_populations_geometry_status']=p2check
            # [P2 ARCHIVE] All internal mass-balance and mask-overlap failures remain blocking.
            fatal=[q for q in qas if q['status']=='FAIL' and q['check'] != 'EA_GEOMETRY_SYMMETRIC_DIFFERENCE']
            if fatal:
                rm['status']='BLOCKED_INTERNAL_QA'
                rm['blocking_checks']=[q['check'] for q in fatal]
                return geometry,attribution,exclusions,qas,comparison,rm
            # [P2 ARCHIVE] In STRICT mode an EA geometric mismatch blocks this river's attribution.
            if not geo_pass and strict:
                rm['status']='BLOCKED_EA_GEOMETRY_MISMATCH'
                comparison.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                     EA_5D_area_km2=sum_e/1e6,EA_audit_area_km2=sum_a/1e6,
                     EA_outside_scored_km2=sum_out/1e6,
                     EA_inside_scored_km2=sum_el/1e6,
                     EA_outside_pct_of_total=(100*sum_out/sum_e if sum_e else ''),
                     matched_outside_km2='',unmatched_outside_km2='',
                     nominal_AD_AD_outside_km2='',
                     effective_AD_AD_other_nominal_outside_km2='',
                     nominal_AD_AD_pct_of_outside='',all_effective_AD_AD_pct_of_outside='',
                     attribution_status=rm['status'],
                     EA_source_symmetric_diff_m2=mismatch,
                     P1_P2_scored_masks_geometry=p2check))
                return geometry,attribution,exclusions,qas,comparison,rm

            # Inside this extent, each output polygon is *physical erosion*,
            # not a whole 150m cell. Residual outside not in audit is explicit.
            # [P2 ARCHIVE] Optional original Risk Table detail refines but does not redefine scored support.
            detail=self._read_detail(detail_p,y1,y2,feedback)
            # [P2 ARCHIVE] Restrict attribution to the common outside-scored physical erosion footprint.
            clip=self._overlay('intersection',audit,outside,'audit_attributed_outside',scratch,context,feedback)
            # [P2 ARCHIVE] Explicitly retain outside-scored erosion absent from the audit geometry.
            residual=self._overlay('difference',outside,audit,'outside_unmatched',scratch,context,feedback)
            gap_area=self._area(residual)
            self._export_layer(residual,mapgpkg,code+'_outside_unmatched',context)
            history,risk,joined,classified_area,nfrags=self._write_enriched(
                clip,mapgpkg,code+'_outside_attributed',context,detail)
            qa('OUTSIDE_ATTRIBUTED_PLUS_UNMATCHED_CLOSURE',
               abs(sum_out-(classified_area+gap_area)),tol(sum_out,sum_e),
               'Outside risk = attributed within physical source match + unmatched')
            qa('ATTRIBUTED_SUBSET_OF_OUTSIDE',max(0.0,classified_area-sum_out),tol(sum_out,sum_e))
            rm['matched_attribution_fragment_count']=nfrags
            rm['unmatched_outside_m2']=gap_area
            # [P2 ARCHIVE] DIAGNOSTIC mismatches retain PROVISIONAL status; never QA PASS.
            rm['status']='VERIFIED' if geo_pass else 'PROVISIONAL_SOURCE_GEOMETRY_MISMATCH'
            # In diagnostic mode ONLY the source-geometry mismatch is allowed.
            # Every other conservation or overlap failure remains blocking.
            if any(q['status']=='FAIL' and q['check'] != 'EA_GEOMETRY_SYMMETRIC_DIFFERENCE'
                   for q in qas):
                rm['status']='BLOCKED_INTERNAL_QA'
            status=rm['status']
            # [P2 ARCHIVE] Populate outside-risk history classification in 02_outside_risk_attribution.
            for label,area in sorted(history.items()):
                attribution.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                    outcome='EA_OUTSIDE_SCORED_FP_DS',grouping='STATE_HISTORY',category=label,
                    area_m2=area,area_km2=area/1e6,
                    percent_of_outside=100*area/sum_out if sum_out else '',
                    unclassified_outside_m2=gap_area,
                    interpretation_status=status))
            attribution.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                    outcome='EA_OUTSIDE_SCORED_FP_DS',grouping='STATE_HISTORY',
                    category='UNMATCHED_EROSION_GEOMETRY',area_m2=gap_area,
                    area_km2=gap_area/1e6,percent_of_outside=100*gap_area/sum_out if sum_out else '',
                    unclassified_outside_m2=gap_area,interpretation_status=status))
            # [P2 ARCHIVE] Write exclusion and eligibility categories to 03_scored_population_exclusions.
            for label,area in sorted(risk.items()):
                exclusions.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                    risk_coverage_class=label,row_type='COVERAGE_TOTAL',exclusion_reason='ALL',detail_status='ALL',
                    area_m2=area,area_km2=area/1e6,
                    pct_outside=100*area/sum_out if sum_out else '',
                    interpretation_status=status))
            exclusions.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                    risk_coverage_class='UNMATCHED_EROSION_GEOMETRY',row_type='COVERAGE_TOTAL',exclusion_reason='UNMATCHED',
                    detail_status='UNMATCHED',area_m2=gap_area,area_km2=gap_area/1e6,
                    pct_outside=100*gap_area/sum_out if sum_out else '',interpretation_status=status))
            for (hk,rk,reason,joinstat),area in sorted(joined.items()):
                exclusions.append(dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                    risk_coverage_class=rk,row_type='CROSS_TAB_DETAIL',exclusion_reason=reason,
                    detail_status='BREAKDOWN:%s;%s' %(hk,joinstat),
                    area_m2=area,area_km2=area/1e6,
                    pct_outside=100*area/sum_out if sum_out else '',interpretation_status=status))
            cmp=dict(river=river,forecast=forecast,Y1=y1,Y2=y2,
                     EA_5D_area_km2=sum_e/1e6,EA_audit_area_km2=sum_a/1e6,
                     EA_outside_scored_km2=sum_out/1e6,
                     EA_inside_scored_km2=sum_el/1e6,
                     EA_outside_pct_of_total=100*sum_out/sum_e if sum_e else '',
                     matched_outside_km2=classified_area/1e6,
                     unmatched_outside_km2=gap_area/1e6,
                     nominal_AD_AD_outside_km2=history.get('NOMINAL_AD_TO_AD',0.0)/1e6,
                     effective_AD_AD_other_nominal_outside_km2=history.get('EFFECTIVE_AD_TO_AD_OTHER_NOMINAL',0.0)/1e6,
                     nominal_AD_AD_pct_of_outside=(100*history.get('NOMINAL_AD_TO_AD',0.0)/sum_out if sum_out else ''),
                     all_effective_AD_AD_pct_of_outside=(100*(history.get('NOMINAL_AD_TO_AD',0.0)+history.get('EFFECTIVE_AD_TO_AD_OTHER_NOMINAL',0.0))/sum_out if sum_out else ''),
                     attribution_status=status,EA_source_symmetric_diff_m2=mismatch,
                     P1_P2_scored_masks_geometry=p2check)
            # [P2 ARCHIVE] Record river-comparison metrics with original per-river QA status.
            comparison.append(cmp)
            return geometry,attribution,exclusions,qas,comparison,rm
        finally:
            if not keep:
                # On Windows GDAL/OGR may hold open SQLite connections. Therefore
                # best-effort cleanup; failure is recorded, never destroys output.
                try:
                    shutil.rmtree(str(scratch))
                    rm['scratch_deleted']=True
                except OSError as e:
                    rm['scratch_deleted']=False
                    rm['scratch_cleanup_note']=str(e)

    # [P2 ARCHIVE] Run both reach-specific investigations; write all CSVs and maps
    # [P2 ARCHIVE] with per-river verification statuses and the overall QA disposition.
    def processAlgorithm(self,params,context,feedback):
        base=Path(self.parameterAsString(params,'OUTPUT_FOLDER',context))
        if not base.is_dir():
            raise QgsProcessingException('Select an existing output parent folder')
        when=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        out=base/('FRAF_5D_EA_Outside_Risk_Reconciliation_'+when)
        out.mkdir(exist_ok=False)
        # [P2 ARCHIVE] Preserve original result filenames used by Supplementary S9 and Table S1.
        names={
            'MANIFEST':'00_manifest.json',
            'GEOMETRY_CSV':'01_erosion_geometry_comparison.csv',
            'ATTRIBUTION_CSV':'02_outside_risk_attribution.csv',
            'EXCLUSIONS_CSV':'03_scored_population_exclusions.csv',
            'QA_CSV':'04_annual_area_QA.csv',
            'TWO_RIVER_CSV':'05_two_river_comparison.csv',
            'OUTPUT_GPKG':'06_reconciliation_maps.gpkg',
            'RUN_STATUS':'00_RUN_STATUS.txt',
        }
        targets={k:out/f for k,f in names.items()}
        targets['RUN_STATUS'].write_text('STARTED\n',encoding='utf-8')
        abs_tol=self.parameterAsDouble(params,'ABS_TOL_M2',context)
        rel_tol=self.parameterAsDouble(params,'REL_TOL',context)
        strict=self.parameterAsEnum(params,'GEOMETRY_POLICY',context)==0
        require=self.parameterAsBool(params,'REQUIRE_5DEA_MANIFEST',context)
        keep=self.parameterAsBool(params,'PRESERVE_WORKING',context)
        # [P2 ARCHIVE] Original model/filename provenance is kept in the runtime manifest even
        # [P2 ARCHIVE] though the publication archive file is renamed.
        manifest=dict(script='FRAF_5D_EA_Outside_Risk_Attribution_Reconciliation_v1_0.py',
                      created_utc=when,status='STARTED',
                      geometry_policy='STRICT' if strict else 'DIAGNOSTIC_WITH_UNMATCHED',
                      absolute_tolerance_m2=abs_tol,relative_tolerance=rel_tol,
                      require_5dea_manifest=require,code_expected_crs={'Mamore':'EPSG:32720','Jamuna':'EPSG:32646'},
                      rivers={},caveats=[
                          'The audited outcome is observed physical EA erosion within scored or unscored PLACE support.',
                          'An FP risk surface includes eligible pre-existing floodplain and SF, but excludes DS.',
                          'Original transition mask (FP_EVENT/DS_EVENT/NEITHER) differs from actual scored-population support.',
                          'Effective and nominal AD->AD classify a PLACE interval, not necessarily the geometry of eroded surface material.',
                          'Original risk-eligible cells may not have valid 5c scores; missing detail flags do not mean zero eligibility.',
                          'EA geometry mismatch cannot be interpreted as model failure; DIAGNOSTIC mode is not publication verified.',
                          'A physical EA erosion footprint is not a probability-of-erosion forecast.',
                      ])
        geometry=[];attribution=[];exclusions=[];qa=[];comparison=[]
        try:
            # [P2 ARCHIVE] Handle each river independently; a failed river does not become an
            # [P2 ARCHIVE] implicitly verified result because the other river passes.
            for code,river in (('M','Mamore'),('J','Jamuna')):
                if feedback.isCanceled():
                    raise QgsProcessingException('User cancelled — outputs INCOMPLETE')
                try:
                    rr=self._river(code,river,params,context,feedback,out,targets['OUTPUT_GPKG'],
                                   abs_tol,rel_tol,strict,require,keep)
                    for bag,r in zip((geometry,attribution,exclusions,qa,comparison),rr[:5]):
                        bag.extend(r)
                    manifest['rivers'][river]=rr[5]
                    feedback.pushInfo('[%s] status %s' %(river,rr[5].get('status')))
                except Exception as ex:
                    feedback.reportError('[%s] %s: %s' %(river,type(ex).__name__,str(ex)))
                    manifest['rivers'][river]={'status':'FAILED_EXCEPTION','error':str(ex),
                                               'traceback':traceback.format_exc()}
            # [P2 ARCHIVE] Fix the result columns for geometry, attribution, exclusions and QA.
            fields={
                'GEOMETRY_CSV':['river','forecast','Y1','Y2','audit_area_m2','fived_ea_area_m2',
                   'net_5d_minus_audit_m2','audit_only_m2','fived_only_m2','symmetric_difference_m2',
                   'common_area_from_audit_m2','common_area_from_5d_m2','geometry_status',
                   'tolerance_m2','outside_scored_m2','eligible_scored_m2',
                   'fp_scored_risk_area_m2','ds_scored_risk_area_m2'],
                'ATTRIBUTION_CSV':['river','forecast','Y1','Y2','outcome','grouping','category',
                   'area_m2','area_km2','percent_of_outside','unclassified_outside_m2','interpretation_status'],
                'EXCLUSIONS_CSV':['river','forecast','Y1','Y2','risk_coverage_class','row_type','exclusion_reason',
                   'detail_status','area_m2','area_km2','pct_outside','interpretation_status'],
                'QA_CSV':['river','forecast','Y1','Y2','check','value_m2','tolerance_m2','status','note'],
                'TWO_RIVER_CSV':['river','forecast','Y1','Y2','EA_5D_area_km2','EA_audit_area_km2',
                   'EA_outside_scored_km2','EA_inside_scored_km2','EA_outside_pct_of_total',
                   'matched_outside_km2','unmatched_outside_km2','nominal_AD_AD_outside_km2',
                   'effective_AD_AD_other_nominal_outside_km2','nominal_AD_AD_pct_of_outside',
                   'all_effective_AD_AD_pct_of_outside','attribution_status',
                   'EA_source_symmetric_diff_m2','P1_P2_scored_masks_geometry'],
            }
            for key,cols in fields.items():
                data={'GEOMETRY_CSV':geometry,'ATTRIBUTION_CSV':attribution,
                      'EXCLUSIONS_CSV':exclusions,'QA_CSV':qa,'TWO_RIVER_CSV':comparison}[key]
                self._writecsv(targets[key],data,cols)
            # [P2 ARCHIVE] Both rivers must be VERIFIED for overall COMPLETED_VERIFIED status.
            statuses=[manifest['rivers'].get(r,{}).get('status') for r in ('Mamore','Jamuna')]
            manifest['status']=('COMPLETED_VERIFIED' if statuses==['VERIFIED','VERIFIED']
                                else 'DIAGNOSTIC_OR_INCOMPLETE')
            manifest['river_statuses']=statuses
            manifest['outputs']={k:str(v) for k,v in targets.items()}
            targets['MANIFEST'].write_text(json.dumps(manifest,indent=2,ensure_ascii=False,default=str),
                                           encoding='utf-8')
            targets['RUN_STATUS'].write_text(manifest['status']+'\n'+ '\n'.join(
                '%s=%s' %(r,manifest['rivers'].get(r,{}).get('status')) for r in ('Mamore','Jamuna'))+'\n',
                encoding='utf-8')
            return {key:str(path) for key,path in targets.items()}
        except Exception:
            manifest['status']='FAILED_OR_INCOMPLETE'
            targets['MANIFEST'].write_text(json.dumps(manifest,indent=2,ensure_ascii=False,default=str),
                                           encoding='utf-8')
            targets['RUN_STATUS'].write_text('FAILED_OR_INCOMPLETE\n',encoding='utf-8')
            raise
