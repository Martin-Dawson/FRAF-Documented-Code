# -*- coding: utf-8 -*-
# ============================================================================
# FRAF PAPER 2 | 02 — EROSION–ACCRETION (EA) ANALYSIS
# ============================================================================
# Archive filename : FRAF_P2_02_EAAnalysis_v15g.py
# Source version   : v15g-authoritative-state-events-risk-QA (2026-07-24)
# Status           : COMMENT-ONLY archival annotation of the supplied source.
#                    All executable statements, parameters, expressions and
#                    numerical defaults remain as supplied; no algorithmic
#                    fixes or changes are implied by this release.
#
# ORIGIN AND ATTRIBUTION
# The EA workflow derives from the Standalone Channel Shifting (SCS) Toolbox
# developed by Miloš Rusnák and colleagues, extending concepts implemented
# in the FluvialCorridor toolbox. The original ArcPy-based SCS methodology was
# adapted for the QGIS Processing framework by Martin Dawson with assistance
# from ChatGPT (initial port November 2025; subsequent development 2026).
#
# Rusnák, M., Opravil, Š., Dunesme, S., Afzali, H., Rey, L., Parmentier, H.,
# Piégay, H. (2025). A channel shifting GIS toolbox for exploring floodplain
# dynamics through channel erosion and deposition. Geomorphology 477, 109688.
# https://doi.org/10.1016/j.geomorph.2025.109688
#
# Related foundation: Roux, C., Alber, A., Bertrand, M., Vaudor, L.,
# Piégay, H. (2015). "FluvialCorridor": A new ArcGIS package for multiscale
# riverscape exploration. Geomorphology 242, 29–37.
# https://doi.org/10.1016/j.geomorph.2014.04.018
#
# SCIENTIFIC ROLE IN FRAF
# This module maps lateral erosion, deposition and persistent surface classes
# between consecutive observed channel dates. The resulting EA_processes
# polygons and accompanying observation tags are spatial evidence for later
# assemblage reconstruction and fixed-place state/event attribution.
# IMPORTANT: EA event/process classes do NOT independently constitute the
# final three-state AD/DS/SF assemblage ontology. In particular, the EA label
# "stable_floodplain" is an interval mapping class, NOT the longitudinal
# stabilised-floodplain (SF) state or proof of 20 years of storage persistence.
# Likewise, the channel / island / floodplain support tags are observation-
# specific spatial categories rather than the final transition-risk populations.
#
# PROCESSING SEQUENCE (existing implementation)
#   1. Validate and order dated channel polygons and matching centrelines.
#   2. Check coordinate systems, geometries and observation-interval limits.
#   3. Prepare channel bodies, envelopes and island support for each date.
#   4. Overlay consecutive observations and retain date-specific T_/y_ tags.
#   5. Repair planar topology; assign support by actual overlap area and
#      recompute the authoritative EA class from supported endpoint tags.
#   6. Generate centreline-relative LEFT/RIGHT masks and migration labels.
#   7. Calculate elapsed intervals, optional segment statistics and rate layers.
#   8. Write date-pair layers into the consolidated output GeoPackage, with
#      optional debug exports and quality diagnostics.
#
# IMPORTANT ANALYTICAL QUALIFICATIONS
# - EA records mapped change between observations; occurrence is interval-
#   censored and does not establish the precise calendar date of a process.
# - Date labels and duration fields must be checked for irregular observation
#   spacing, especially for the smaller-river extensions.
# - The selected SURFACE_MODE determines how optional water/active polygons
#   are interpreted. Do not interchange these surfaces without checking their
#   geomorphic definitions and observational support.
# - All geometric tolerances are in source/projected map units. Reliable area,
#   buffer, length and orientation calculations normally require a suitable
#   projected metric CRS, with channel-width settings adjusted to river scale.
# - Conservative fallback paths are intentional safeguards, not evidence that
#   a repaired geometry or inferred classification matches independent imagery.
# - Large overlay operations and debug GeoPackages may consume significant
#   memory and disk capacity; retain source inputs and QA outputs for audit.
#
# HOW TO RUN
# Load this .py file into the QGIS Processing Script Editor / Scripts provider.
# Provide the input polygons, centrelines, observation date fields, output
# folder and relevant surface-mode options. Inspect final EA and QA layers
# before using them in subsequent FRAF modules.
# ============================================================================


# Module 3 — EA calculation (QGIS) — SCS Toolbox 
# v15g-authoritative-state-events-risk-QA, 2026-07-24
# Refactored for QGIS 3.44.09 by Martin Dawson using ChatGPT, April 2026
# 
# Ported from arcPY to QGIS Processing framework by Martin Dawson using ChatGPT November 2025
# Based on: Standalone channel shifting toolbox (SCS Toolbox)
# Author: Milos Rusnak
#   CNRS - UMR5600 Environnement Ville Societe
#   15 Parvis Rene Descartes, BP 7000, 69342 Lyon Cedex 07, France 
               
# geogmilo@savba.sk
#   Institute of geography SAS
#   Stefanikova 49, 814 73 Bratislava, Slovakia 
               
# Standalone channel shifting toolbox (SCS Toolbox) was developed as extension of the FluvialCorridor toolbox with implemented the centerline 
# extraction approach and segmentation of DGO from FluvialCorridor toolbox.
# For each use of the Channel toolbox leading to a publication, report, presentation or any other
# document, please refer also to the following articles:
#       Rusnák, M., Opravil, Š., Dunesme, S., Afzali, H., Rey, L., Parmentier, H., Piégay, H., 2025 A channel shifting GIS toolbox for exploring
#       floodplain dynamics through channel erosion and deposition. Geomorphology, 477, 109688. 
#       https://doi.org/10.1016/j.geomorph.2025.109688 

#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., 2015. "FluvialCorridor": A new ArcGIS 
#       package for multiscale riverscape exploration. Geomorphology, 242, 29-37.
#       https://doi.org/10.1016/j.geomorph.2014.04.018
#
# QGIS Version(tested using 3.40.11-Bratislava)
"""
Module 3 — EA calculation (QGIS) — SCS Toolbox (v15g-authoritative-state-events-risk-QA, 2026-07-24)
QGIS 3.44.09-compatible; robust field/geometry handling; single GPKG output.

Inputs:
- CHANNEL_POLYGONS: list of channel polygon layers (one per date)
- CENTRELINES: list of centerline layers (one per date)
- FIELD_YEAR: polygon date field (e.g., 'Year' or date)
- CENTERLINE_YEAR_FIELD: centreline date field
- STATISTICS: optional segments layer (line or polygon) for per-segment stats
- INTERVAL: segment spacing (m) used to normalize area->meters/day where needed
- OUTPUT_FOLDER: target directory for outputs
- DELETE_TEMP: bool

Outputs:
- <OUTPUT_FOLDER>/SCS_EA_<first>_<last>.gpkg with sublayers:
    EA_processes_y1_y2
    EAsegments_y1_y2 (if stats)
    EA_rate_y1_y2 (if stats)
"""
WRITE_DEBUG_GPKG = False   # can be overridden by Processing parameter
DEBUG_TRACE = False
DEBUG_SAVE = False
import os
import re
import math
import shutil
import time
import uuid
import processing
from datetime import datetime, date
from datetime import datetime as _dt
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProcessingUtils,
    QgsFeature,
    QgsProject,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsWkbTypes,
)



# ---------------------- Helpers: algorithms, parsing, filenames ----------------------

# PURPOSE: Read the verbose diagnostic switch; false suppresses expensive log-only scans.
def _dbg_enabled():
    return bool(DEBUG_TRACE)

# PURPOSE: Read the optional diagnostic GeoPackage export switch.
def _dbg_gpkg_enabled():
    return bool(WRITE_DEBUG_GPKG)

# PURPOSE: Emit a progress diagnostic only when verbose tracing is enabled.
def _dbg_log(feedback, msg):
    if _dbg_enabled() and feedback is not None:
        feedback.pushInfo(msg)

# PURPOSE: Sanitise arbitrary layer names for safe temporary file and layer identifiers.
def _safe_token(s):
    import re
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(s)).strip("_") or "layer"

def _safe_feature_merge(layer_a, layer_b, layer_name, context, feedback, crs=None):
    """
    Merge two layers feature-by-feature into a new memory layer,
    avoiding native:mergevectorlayers when that produces corrupted extents.
    """
    A = _as_layer(layer_a, context) or layer_a
    B = _as_layer(layer_b, context) or layer_b

    if A is None or not A.isValid():
        raise QgsProcessingException(f"[safe_feature_merge] invalid A: {layer_name}")
    if B is None or not B.isValid():
        raise QgsProcessingException(f"[safe_feature_merge] invalid B: {layer_name}")

    # Resolve CRS
    out_crs = crs
    if out_crs is None or not out_crs.isValid():
        if A.crs().isValid():
            out_crs = A.crs()
        elif B.crs().isValid():
            out_crs = B.crs()
        else:
            out_crs = QgsCoordinateReferenceSystem()

    # Geometry type
    wkb = A.wkbType()
    geom_str = QgsWkbTypes.displayString(wkb)
    mem = QgsVectorLayer(f"{geom_str}?crs={out_crs.authid()}", layer_name, "memory")
    prov = mem.dataProvider()

    # ---------------------------
    # Build output fields safely
    # ---------------------------
    out_fields = QgsFields()
    used_names = set()

    # PURPOSE: Copy source attribute definitions, suffixing names that duplicate earlier fields.
    def _add_fields_from_layer(src_layer, prefix=""):
        for fld in src_layer.fields():
            new_name = f"{prefix}{fld.name()}" if prefix else fld.name()
            base_name = new_name
            i = 2
            while new_name in used_names:
                new_name = f"{base_name}_{i}"
                i += 1

            new_fld = QgsField(fld)
            new_fld.setName(new_name)
            out_fields.append(new_fld)
            used_names.add(new_name)

    _add_fields_from_layer(A)
    _add_fields_from_layer(B)

    prov.addAttributes(list(out_fields))
    mem.updateFields()

    # Build source->dest field maps
    a_map = {}
    b_map = {}

    for i, fld in enumerate(A.fields()):
        a_map[fld.name()] = i

    for fld in B.fields():
        target_name = fld.name()
        idx = out_fields.indexOf(target_name)

        # if duplicated name exists in A, pick the renamed copy after A block
        if idx != -1 and target_name in a_map and idx == a_map[target_name]:
            chosen_idx = -1
            for j in range(len(A.fields()), len(out_fields)):
                if out_fields[j].name().startswith(target_name):
                    chosen_idx = j
                    break
            b_map[fld.name()] = chosen_idx if chosen_idx != -1 else idx
        else:
            b_map[fld.name()] = idx

    feats = []

    # PURPOSE: Append valid geometries and mapped attributes to the in-memory union output.
    def _copy_features(src_layer, fmap):
        for f in src_layer.getFeatures():
            g = f.geometry()
            if g is None or g.isEmpty():
                continue

            new_f = QgsFeature(out_fields)
            new_f.setGeometry(g)

            attrs = [None] * len(out_fields)
            for fld in src_layer.fields():
                src_name = fld.name()
                dst_idx = fmap.get(src_name, -1)
                if dst_idx >= 0:
                    attrs[dst_idx] = f[src_name]

            new_f.setAttributes(attrs)
            feats.append(new_f)

    _copy_features(A, a_map)
    _copy_features(B, b_map)

    if feats:
        prov.addFeatures(feats)
        mem.updateExtents()

    feedback.pushInfo(
        f"[safe_feature_merge] {layer_name}: A={A.featureCount()} B={B.featureCount()} OUT={mem.featureCount()}"
    )
    return mem

# PURPOSE: Ensure geometries use the reference CRS: assign only when missing, reproject when different; validate extents.
def _ensure_layer_crs(layer, target_crs, context, feedback, name="layer"):
    import math

    # PURPOSE: Distinguish a usable assigned CRS from a blank or malformed one.
    def _usable_crs(crs):
        try:
            return (
                crs is not None
                and crs.isValid()
                and bool(crs.authid())
                and str(crs.authid()).strip() != ""
            )
        except Exception:
            return False

    # PURPOSE: Reject invalid/non-finite geometry extents before or after data operations.
    def _extent_is_finite(vlayer):
        if vlayer is None or not vlayer.isValid():
            return False
        try:
            ext = vlayer.extent()
            vals = [ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum()]
            return all(math.isfinite(float(v)) for v in vals)
        except Exception:
            return False

    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[ensure crs] {name} invalid")

    src = lyr.crs() if hasattr(lyr, "crs") else None

    if not _usable_crs(target_crs):
        raise QgsProcessingException(f"[ensure crs] {name} target CRS invalid")

    # Blank / unusable CRS -> assign only
    if not _usable_crs(src):
        lyr.setCrs(target_crs)
        feedback.reportError(
            f"[CRS REPAIR] {name}: blank/unusable CRS assigned as {target_crs.authid()} (no reprojection)"
        )
        return _freeze_to_tmp_gpkg(
            lyr, context, feedback, layer_name=f"{name}_assigned", ref_crs=target_crs
        )

    # Already correct
    if src.authid() == target_crs.authid():
        return _freeze_to_tmp_gpkg(
            lyr, context, feedback, layer_name=f"{name}_match", ref_crs=target_crs
        )

    # Valid and different -> real reprojection
    if not _extent_is_finite(lyr):
        raise QgsProcessingException(
            f"[CRS REPROJECT] {name} input extent invalid before reprojection"
        )

    feedback.reportError(
        f"[CRS REPROJECT] {name}: {src.authid()} -> {target_crs.authid()}"
    )

    reproj = _run(
        "native:reprojectlayer",
        {
            "INPUT": lyr,
            "TARGET_CRS": target_crs,
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]

    reproj = _as_layer(reproj, context) or reproj

    return _freeze_to_tmp_gpkg(
        reproj, context, feedback, layer_name=f"{name}_reproj", ref_crs=target_crs
    )
    
def _normalise_step2_tag_fields(layer, ymd, context, feedback):
    """
    After channel+island merge in Step 2, coalesce duplicate tag fields like:
      y_YYYYMMDD + y_YYYYMMDD_2
      T_YYYYMMDD + T_YYYYMMDD_2
    so downstream code sees one authoritative tag field only.
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[STEP2 TAG NORMALISE] invalid layer for {ymd}")

    y_main = f"y_{ymd}"
    t_main = f"T_{ymd}"
    y_dup  = f"{y_main}_2"
    t_dup  = f"{t_main}_2"

    fns = lyr.fields().names()

    # Coalesce y field
    if y_main in fns and y_dup in fns:
        layer = _run(
            "native:fieldcalculator",
            {
                "INPUT": lyr,
                "FIELD_NAME": y_main,
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"{y_main}\" IS NULL OR trim(to_string(\"{y_main}\")) = '' "
                    f"THEN coalesce(\"{y_dup}\", '{ymd}') "
                    f"ELSE \"{y_main}\" "
                    f"END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        lyr = _as_layer(layer, context) or layer

    # Coalesce T field
    if t_main in fns and t_dup in fns:
        layer = _run(
            "native:fieldcalculator",
            {
                "INPUT": lyr,
                "FIELD_NAME": t_main,
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"{t_main}\" IS NULL OR trim(to_string(\"{t_main}\")) = '' "
                    f"THEN lower(trim(coalesce(\"{t_dup}\", ''))) "
                    f"ELSE lower(trim(to_string(\"{t_main}\"))) "
                    f"END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        lyr = _as_layer(layer, context) or layer

    # Drop duplicate suffixed tag fields after coalescing
    lyr = _as_layer(layer, context) or layer
    drop_cols = [c for c in [y_dup, t_dup] if c in lyr.fields().names()]
    if drop_cols:
        layer = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": drop_cols,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[STEP2 TAG NORMALISE] failed for {ymd}")

    # Debug counts
    try:
        counts = {}
        if t_main in lyr.fields().names():
            for f in lyr.getFeatures():
                v = f[t_main]
                k = "<blank>" if v is None or str(v).strip() == "" else str(v).strip().lower()
                counts[k] = counts.get(k, 0) + 1
            feedback.pushInfo(
                f"[STEP2 TAG NORMALISE] {ymd} {t_main} counts: " +
                ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
            )
    except Exception as e:
        feedback.reportError(f"[STEP2 TAG NORMALISE] debug failed for {ymd}: {e}")

    return layer

# PURPOSE: Return the QGIS CASE expression grouping detailed EA classes into broad process families.
def _proc_group_expr(ea_field="EA"):
    return (
        f"CASE "
        f"WHEN lower(trim(coalesce(\"{ea_field}\",''))) IN ('erosion','island_erosion') THEN 'erosion' "
        f"WHEN lower(trim(coalesce(\"{ea_field}\",''))) IN ('deposition','island_deposition') THEN 'deposition' "
        f"WHEN lower(trim(coalesce(\"{ea_field}\",''))) IN ('stable_channel','stable_island','stable_floodplain','inchannel_surface') THEN 'stable' "
        f"WHEN lower(trim(coalesce(\"{ea_field}\",''))) IN ('inactive_floodplain','undefined_surface') THEN 'inactive' "
        f"ELSE 'unresolved' "
        f"END"
    )

# PURPOSE: Remove an inherited fid column before writing a GeoPackage with its own primary key.
def _drop_fid_field(layer, context, feedback):
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        return layer

    fld_names = [f.name() for f in lyr.fields()]
    if "fid" not in fld_names:
        return lyr

    out = _run(
        "native:deletecolumn",
        {
            "INPUT": lyr,
            "COLUMN": ["fid"],
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]
    return _as_layer(out, context) or out

# PURPOSE: Report feature counts, geometry types, field presence and sample feature IDs when tracing is enabled.
def _dbg_layer(label, layer_or_path, context, feedback, sample_n=3, fields_check=None):
    if not _dbg_enabled():
        return
    """
    Lightweight debug logger for vector layers.
    Never raises, never mutates data.
    """
    try:
        lyr = _as_layer(layer_or_path, context)
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[DBG] {label}: invalid layer")
            return

        fc = lyr.featureCount()
        geom = QgsWkbTypes.displayString(lyr.wkbType())
        flds = lyr.fields().names()

        feedback.pushInfo(
            f"[DBG] {label}: features={fc}, geom={geom}, fields={flds}"
        )

        if fields_check:
            for fn in fields_check:
                feedback.pushInfo(
                    f"[DBG] {label}: has field '{fn}' = {fn in flds}"
                )

        if sample_n > 0 and fc > 0:
            for i, f in enumerate(lyr.getFeatures()):
                if i >= sample_n:
                    break
                feedback.pushInfo(
                    f"[DBG] {label} sample[{i}]: id={f.id()}"
                )

    except Exception as e:
        feedback.reportError(f"[DBG] {label} failed: {e}")
        
# PURPOSE: Optionally persist an intermediate layer for inspection; strip conflicting fid attributes first.
def _dbg_save_layer(lyr, a, b, c=None, d=None, e=None):
    if not _dbg_gpkg_enabled():
        return None
    """
    Supports:
      old: _dbg_save_layer(lyr, outdir, gpkg_name, layer_name, context, feedback)
      new: _dbg_save_layer(lyr, out_path, context, feedback, layer_name="debug")
    """
    import os

    # old style
    if d is not None and e is not None:
        outdir, gpkg_name, layer_name, context, feedback = a, b, c, d, e
        out_path = os.path.join(outdir, gpkg_name)
    # new style
    else:
        out_path, context, feedback = a, b, c
        layer_name = "debug"

    lyr = _as_layer(lyr, context) or lyr
    if lyr is None or not lyr.isValid():
        feedback.reportError(f"[DBG SAVE] invalid layer for {layer_name}")
        return None

    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except Exception:
            pass

    # IMPORTANT: remove source fid field to avoid GPKG UNIQUE constraint failures
    fld_names = [f.name() for f in lyr.fields()]
    if "fid" in fld_names:
        lyr = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": ["fid"],
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context,
            feedback
        )["OUTPUT"]
        lyr = _as_layer(lyr, context) or lyr

    _run(
        "native:savefeatures",
        {
            "INPUT": lyr,
            "OUTPUT": out_path
        },
        context,
        feedback
    )

    feedback.pushInfo(f"[DBG SAVE] wrote {layer_name} -> {out_path}")
    return out_path

# PURPOSE: Log layer bounding-box coordinates to diagnose CRS or overlay problems.
def _dbg_extent(label, layer, context, feedback):
    if not _dbg_enabled():
        return
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        feedback.reportError(f"[{label}] invalid layer")
        return
    try:
        ext = lyr.extent()
        feedback.pushInfo(
            f"[{label}] extent xmin={ext.xMinimum()} xmax={ext.xMaximum()} "
            f"ymin={ext.yMinimum()} ymax={ext.yMaximum()}"
        )
    except Exception as e:
        feedback.reportError(f"[{label}] extent error: {e}")

# PURPOSE: Sample individual geometries for implausible extents or degenerate bounding boxes.
def _dbg_feature_bboxes(label, layer, context, feedback, n=5):
    if not _dbg_enabled():
        return
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        feedback.reportError(f"[{label}] invalid")
        return
    c = 0
    for f in lyr.getFeatures():
        g = f.geometry()
        if g is None or g.isEmpty():
            feedback.reportError(f"[{label}] feature {f.id()} empty geometry")
            continue
        try:
            b = g.boundingBox()
            feedback.pushInfo(
                f"[{label}] feature {f.id()} bbox "
                f"xmin={b.xMinimum()} xmax={b.xMaximum()} "
                f"ymin={b.yMinimum()} ymax={b.yMaximum()}"
            )
        except Exception as e:
            feedback.reportError(f"[{label}] feature {f.id()} bbox error: {e}")
        c += 1
        if c >= n:
            break        

# PURPOSE: Optionally export interior polygon rings as diagnostic island/hole features.
def _dbg_extract_holes(poly_in, outdir, gpkg_name, layer_name, context, feedback):
    if not _dbg_gpkg_enabled():
        return None
    try:
        lyr = _as_layer(poly_in, context) or poly_in
        if lyr is None or not lyr.isValid():
            feedback.pushInfo(f"[DBG HOLES] {layer_name}: invalid, skipping")
            return None

        if lyr.featureCount() == 0:
            feedback.pushInfo(f"[DBG HOLES] {layer_name}: empty, skipping")
            return None

        crs_authid = lyr.crs().authid() if lyr.crs().isValid() else ""
        mem_uri = f"Polygon?crs={crs_authid}" if crs_authid else "Polygon"
        mem = QgsVectorLayer(mem_uri, layer_name, "memory")
        prov = mem.dataProvider()
        prov.addAttributes([QgsField("src_fid", QVariant.Int)])
        mem.updateFields()

        feats_out = []

        for feat in lyr.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue

            if geom.isMultipart():
                polys = geom.asMultiPolygon()
            else:
                p = geom.asPolygon()
                polys = [p] if p else []

            for poly in polys:
                if not poly or len(poly) < 2:
                    continue

                # interior rings only
                for ring in poly[1:]:
                    if ring is None or len(ring) < 4:
                        continue

                    g = QgsGeometry.fromPolygonXY([ring])
                    if g is None or g.isEmpty():
                        continue

                    try:
                        if not g.isGeosValid():
                            g = g.makeValid()
                    except Exception:
                        pass

                    if g is None or g.isEmpty():
                        continue

                    fnew = QgsFeature(mem.fields())
                    fnew.setGeometry(g)
                    try:
                        fnew["src_fid"] = int(feat.id())
                    except Exception:
                        fnew["src_fid"] = -1
                    feats_out.append(fnew)

        if not feats_out:
            feedback.pushInfo(f"[DBG HOLES] {layer_name}: no holes found")
            return None

        prov.addFeatures(feats_out)
        mem.updateExtents()

        out_path = os.path.join(outdir, gpkg_name)
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except Exception:
                pass

        _run(
            "native:savefeatures",
            {
                "INPUT": mem,
                "OUTPUT": out_path
            },
            context,
            feedback
        )

        feedback.pushInfo(f"[DBG HOLES] wrote {layer_name} -> {out_path}")
        return out_path

    except Exception as e:
        feedback.reportError(f"[DBG HOLES ERROR] {layer_name}: {str(e)}")
        return None
                    
# PURPOSE: Count null, empty and zero-area geometries; record extents and geometry type.
def _dbg_geom_stats(label, layer, context, feedback, sample_n=3):
    if not _dbg_enabled():
        return
    """
    Detailed geometry diagnostics for a layer.
    Logs:
      - feature count
      - geometry type
      - CRS
      - extent
      - null / empty geometry counts
      - zero-area counts (for polygons)
      - flat bbox counts
      - sample feature ids
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        feedback.reportError(f"[DBG GEOM] {label}: invalid layer")
        return

    try:
        crs_authid = lyr.crs().authid()
    except Exception:
        crs_authid = "UNKNOWN"

    try:
        ext = lyr.extent()
        ext_txt = (
            f"xmin={ext.xMinimum()} xmax={ext.xMaximum()} "
            f"ymin={ext.yMinimum()} ymax={ext.yMaximum()}"
        )
    except Exception as e:
        ext_txt = f"<extent failed: {e}>"

    try:
        geom_txt = QgsWkbTypes.displayString(lyr.wkbType())
    except Exception:
        geom_txt = str(lyr.wkbType())

    feedback.pushInfo(
        f"[DBG GEOM] {label}: fc={lyr.featureCount()} geom={geom_txt} crs={crs_authid}"
    )
    feedback.pushInfo(f"[DBG GEOM] {label}: extent {ext_txt}")

    null_geom = 0
    empty_geom = 0
    zero_area = 0
    flat_bbox = 0
    sample_ids = []

    try:
        for n, f in enumerate(lyr.getFeatures()):
            if n < sample_n:
                sample_ids.append(str(f.id()))

            g = f.geometry()
            if g is None or g.isNull():
                null_geom += 1
                continue
            if g.isEmpty():
                empty_geom += 1
                continue

            try:
                bb = g.boundingBox()
                if bb.xMinimum() == bb.xMaximum() or bb.yMinimum() == bb.yMaximum():
                    flat_bbox += 1
            except Exception:
                pass

            try:
                a = g.area()
                if abs(a) < 1e-9:
                    zero_area += 1
            except Exception:
                pass

        feedback.pushInfo(
            f"[DBG GEOM] {label}: null={null_geom} empty={empty_geom} "
            f"zero_area={zero_area} flat_bbox={flat_bbox} sample_ids={sample_ids}"
        )
    except Exception as e:
        feedback.reportError(f"[DBG GEOM] {label}: geometry scan failed: {e}")

def _enforce_island_support_on_tags(unionEA, island_src, yy, context, feedback):
    """
    Correct T_yyyy using authoritative same-date island polygons.

    Rule:
      - if a unionEA polygon point-on-surface falls inside a true island polygon
        for year yy -> force T_yy = 'island'
      - otherwise, if T_yy currently says 'island', downgrade it to 'floodplain'

    This prevents edge erosion/deposition being mislabeled as island_* while
    preserving real island processes.
    """
    u = _as_layer(unionEA, context) or unionEA
    isl = _as_layer(island_src, context) or island_src
    if u is None or not u.isValid():
        raise QgsProcessingException(f"[ISLAND SUPPORT] unionEA invalid for {yy}")

    t_field = f"T_{yy}"
    if u.fields().indexOf(t_field) == -1:
        raise QgsProcessingException(f"[ISLAND SUPPORT] missing field {t_field}")

    # No island source -> downgrade any existing 'island' tags to floodplain
    if isl is None or not isl.isValid() or isl.featureCount() == 0:
        feedback.pushInfo(f"[ISLAND SUPPORT] no island polygons for {yy}; downgrading unsupported island tags to floodplain.")
        u = _run(
            "native:fieldcalculator",
            {
                "INPUT": u,
                "FIELD_NAME": t_field,
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN lower(trim(coalesce(\"{t_field}\",''))) = 'island' THEN 'floodplain' "
                    f"ELSE lower(trim(coalesce(\"{t_field}\",''))) "
                    f"END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        return u

    # Keep only polygons and add a marker field
    isl = _polys_only(isl, context, feedback)
    isl = _force_2d_safe(isl, context, feedback)
    isl = _drop_null_tiny_polys(isl, 1e-6, context, feedback)
    isl = _as_layer(isl, context) or isl

    if isl.fields().indexOf("ISL_HIT") == -1:
        isl = _run(
            "native:fieldcalculator",
            {
                "INPUT": isl,
                "FIELD_NAME": "ISL_HIT",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 1,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "1",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
    isl = _as_layer(isl, context) or isl

    # Stable ID on unionEA for join-back
    if u.fields().indexOf("RT_ID") == -1:
        u = _run(
            "native:fieldcalculator",
            {
                "INPUT": u,
                "FIELD_NAME": "RT_ID",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 18,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "$id",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Point-on-surface for robust support check
    pts = _run(
        "native:pointonsurface",
        {"INPUT": u, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    pts = _run(
        "native:joinattributesbylocation",
        {
            "INPUT": pts,
            "JOIN": isl,
            "PREDICATE": [0],   # intersects
            "JOIN_FIELDS": ["ISL_HIT"],
            "METHOD": 0,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    pts = _as_layer(pts, context) or pts

    # Join flag back to polygons by RT_ID
    u = _run(
        "native:joinattributestable",
        {
            "INPUT": u,
            "FIELD": "RT_ID",
            "INPUT_2": pts,
            "FIELD_2": "RT_ID",
            "FIELDS_TO_COPY": ["ISL_HIT"],
            "METHOD": 1,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Apply authoritative island support:
    #   supported -> island
    #   unsupported island -> floodplain
    u = _run(
        "native:fieldcalculator",
        {
            "INPUT": u,
            "FIELD_NAME": t_field,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN coalesce(\"ISL_HIT\",0) = 1 THEN 'island' "
                f"WHEN lower(trim(coalesce(\"{t_field}\",''))) = 'island' THEN 'floodplain' "
                f"ELSE lower(trim(coalesce(\"{t_field}\",''))) "
                f"END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Clean helper
    cols = [c for c in ["ISL_HIT"] if c in u.fields().names()]
    if cols:
        u = _run(
            "native:deletecolumn",
            {"INPUT": u, "COLUMN": cols, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        u = _as_layer(u, context) or u

    # Diagnostics
    try:
        counts = {}
        for f in u.getFeatures():
            v = f[t_field]
            k = "<blank>" if v is None or str(v).strip() == "" else str(v).strip().lower()
            counts[k] = counts.get(k, 0) + 1
        feedback.pushInfo(
            f"[ISLAND SUPPORT] {yy} {t_field} counts after support enforcement: " +
            ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
        )
    except Exception as e:
        feedback.reportError(f"[ISLAND SUPPORT] debug failed for {yy}: {e}")

    return u

def _enforce_surface_support_on_tags_by_overlap(unionEA, channel_src, island_src, yy, context, feedback):
    """
    Force T_yyyy from authoritative same-date support using THREE-WAY AREA VOTING.

    This replaces both fragile earlier rules:
      1) binary intersection: any channel overlap -> channel
      2) two-way area priority: channel area vs island area only

    The corrected rule treats the outside / floodplain part of each fabric cell
    as an explicit competing support class:

        cell_area = area of fabric polygon
        channel_area = total overlap with active/channel support
        island_area  = total overlap with island support
        outside_area = max(cell_area - channel_area - island_area, 0)

    Assignment:
        channel    if channel_area is the largest support
        island     if island_area is the largest support
        floodplain if outside_area is the largest support
        tie        keep the existing meaningful tag; if blank, floodplain

    This is required for cells along the outer active-domain edge. Those cells
    may overlap the active/channel polygon only slightly, while most of the cell
    lies outside the active-domain support. They must become floodplain for that
    date so edge erosion/deposition is retained.
    """
    u = _as_layer(unionEA, context) or unionEA
    ch = _as_layer(channel_src, context) or channel_src
    isl = _as_layer(island_src, context) or island_src

    if u is None or not u.isValid():
        raise QgsProcessingException(f"[SURFACE SUPPORT OVL3] unionEA invalid for {yy}")

    t_field = f"T_{yy}"
    y_field = f"y_{yy}"

    if u.fields().indexOf(t_field) == -1:
        raise QgsProcessingException(f"[SURFACE SUPPORT OVL3] missing {t_field}")
    if u.fields().indexOf(y_field) == -1:
        raise QgsProcessingException(f"[SURFACE SUPPORT OVL3] missing {y_field}")

    # Stable ID for join-back. Use an existing RT_ID if present; otherwise create one.
    if u.fields().indexOf("RT_ID") == -1:
        u = _run(
            "native:fieldcalculator",
            {
                "INPUT": u,
                "FIELD_NAME": "RT_ID",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 18,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "$id",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        u = _as_layer(u, context) or u

    # Cache existing tag and cell area for every fabric cell, not just cells that
    # intersect channel/island support. This is essential for floodplain voting.
    existing = {}
    cell_area = {}
    for f in u.getFeatures():
        try:
            rid = int(f["RT_ID"])
        except Exception:
            continue
        try:
            existing[rid] = "" if f[t_field] is None else str(f[t_field]).strip().lower()
        except Exception:
            existing[rid] = ""
        try:
            g = f.geometry()
            cell_area[rid] = float(g.area()) if g is not None and not g.isEmpty() else 0.0
        except Exception:
            cell_area[rid] = 0.0

    def _support_overlap_areas(base_layer, support_layer, support_name):
        """Return {RT_ID: total_overlap_area} for a support surface."""
        support_layer = _as_layer(support_layer, context) or support_layer
        if support_layer is None or not support_layer.isValid() or support_layer.featureCount() == 0:
            feedback.pushInfo(f"[SURFACE SUPPORT OVL3] no {support_name} support polygons for {yy}")
            return {}

        support_layer = _polys_only(support_layer, context, feedback)
        support_layer = _force_2d_safe(support_layer, context, feedback)
        support_layer = _drop_null_tiny_polys(support_layer, 1e-6, context, feedback)
        support_layer = _as_layer(support_layer, context) or support_layer

        if support_layer is None or not support_layer.isValid() or support_layer.featureCount() == 0:
            feedback.pushInfo(f"[SURFACE SUPPORT OVL3] no usable {support_name} support polygons for {yy}")
            return {}

        inter = _run(
            "native:intersection",
            {
                "INPUT": base_layer,
                "OVERLAY": support_layer,
                "INPUT_FIELDS": ["RT_ID"],
                "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        inter = _as_layer(inter, context) or inter

        if inter is None or not inter.isValid() or inter.featureCount() == 0:
            feedback.pushInfo(f"[SURFACE SUPPORT OVL3] no {support_name} intersections for {yy}")
            return {}

        inter = _run(
            "native:fieldcalculator",
            {
                "INPUT": inter,
                "FIELD_NAME": "OV_A",
                "FIELD_TYPE": 0,
                "FIELD_LENGTH": 20,
                "FIELD_PRECISION": 6,
                "NEW_FIELD": True,
                "FORMULA": "$area",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        inter = _as_layer(inter, context) or inter

        areas = {}
        for f in inter.getFeatures():
            rid = f["RT_ID"]
            if rid is None:
                continue
            try:
                rid_i = int(rid)
            except Exception:
                continue
            try:
                a = float(f["OV_A"] or 0.0)
            except Exception:
                a = 0.0
            if a <= 0.0:
                continue
            # Sum, do not take max: a fabric cell can intersect multiple support parts.
            areas[rid_i] = areas.get(rid_i, 0.0) + a

        feedback.pushInfo(
            f"[SURFACE SUPPORT OVL3] {yy} {support_name} supported cells={len(areas)} "
            f"total_overlap_area={sum(areas.values()):.3f}"
        )
        return areas

    ch_area = _support_overlap_areas(u, ch, "channel")
    isl_area = _support_overlap_areas(u, isl, "island")

    # Build no-geometry support lookup with explicit overlap-area diagnostics.
    mem = QgsVectorLayer(
        "None?field=RT_ID:integer&field=SUPPORT:string(16)&field=CH_A:double&field=ISL_A:double&field=OUT_A:double&field=CELL_A:double",
        f"support_area3_{yy}",
        "memory"
    )
    pr = mem.dataProvider()
    feats = []

    eps = 1.0e-9
    support_counts = {"channel": 0, "island": 0, "floodplain": 0, "keep": 0}

    # Vote for every cell so outside/floodplain can dominate even when there is
    # no channel/island support overlap.
    all_ids = sorted(cell_area.keys())

    for rid in all_ids:
        ca = float(ch_area.get(rid, 0.0))
        ia = float(isl_area.get(rid, 0.0))
        ta = float(cell_area.get(rid, 0.0))

        # Because overlays can produce tiny numerical overlaps or double-count
        # shared boundaries, constrain outside to [0, cell_area].
        out_a = ta - ca - ia
        if out_a < 0.0 and abs(out_a) <= 1.0e-6 * max(1.0, ta):
            out_a = 0.0
        out_a = max(0.0, min(out_a, ta))

        max_a = max(ca, ia, out_a)
        cur = existing.get(rid, "")

        # If all areas are effectively zero, preserve existing tag if meaningful.
        if max_a <= eps:
            support = cur if cur in ("channel", "island", "floodplain") else "floodplain"
        else:
            is_ch = ca >= max_a - eps
            is_isl = ia >= max_a - eps
            is_out = out_a >= max_a - eps
            n_tied = int(is_ch) + int(is_isl) + int(is_out)

            if n_tied == 1:
                if is_ch:
                    support = "channel"
                elif is_isl:
                    support = "island"
                else:
                    support = "floodplain"
            else:
                # Tie: preserve a meaningful existing tag if it is one of the tied
                # support classes; otherwise use a conservative hierarchy that
                # avoids swallowing edge floodplain cells into channel.
                if cur == "channel" and is_ch:
                    support = "channel"
                elif cur == "island" and is_isl:
                    support = "island"
                elif cur == "floodplain" and is_out:
                    support = "floodplain"
                elif is_out:
                    support = "floodplain"
                elif is_isl:
                    support = "island"
                else:
                    support = "channel"

        support_counts[support if support in support_counts else "keep"] = support_counts.get(support if support in support_counts else "keep", 0) + 1

        ft = QgsFeature(mem.fields())
        ft["RT_ID"] = int(rid)
        ft["SUPPORT"] = support
        ft["CH_A"] = ca
        ft["ISL_A"] = ia
        ft["OUT_A"] = out_a
        ft["CELL_A"] = ta
        feats.append(ft)

    pr.addFeatures(feats)
    mem.updateFields()

    feedback.pushInfo(
        f"[SURFACE SUPPORT OVL3] {yy} three-way area assignment: "
        f"channel={support_counts.get('channel',0)}, "
        f"island={support_counts.get('island',0)}, "
        f"floodplain={support_counts.get('floodplain',0)}, "
        f"keep={support_counts.get('keep',0)}"
    )

    u = _run(
        "native:joinattributestable",
        {
            "INPUT": u,
            "FIELD": "RT_ID",
            "INPUT_2": mem,
            "FIELD_2": "RT_ID",
            "FIELDS_TO_COPY": ["SUPPORT", "CH_A", "ISL_A", "OUT_A", "CELL_A"],
            "METHOD": 1,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Assign authoritative type. SUPPORT is now always a three-way vote.
    u = _run(
        "native:fieldcalculator",
        {
            "INPUT": u,
            "FIELD_NAME": t_field,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN lower(trim(coalesce(\"SUPPORT\",''))) IN ('channel','island','floodplain') "
                f"THEN lower(trim(to_string(\"SUPPORT\"))) "
                f"WHEN \"{t_field}\" IS NULL OR trim(to_string(\"{t_field}\")) = '' THEN 'floodplain' "
                f"ELSE lower(trim(to_string(\"{t_field}\"))) "
                f"END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Ensure y field is populated.
    u = _run(
        "native:fieldcalculator",
        {
            "INPUT": u,
            "FIELD_NAME": y_field,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN \"{y_field}\" IS NULL OR trim(to_string(\"{y_field}\")) = '' "
                f"THEN '{yy}' "
                f"ELSE trim(to_string(\"{y_field}\")) "
                f"END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Clean helper columns. For temporary debugging, comment this block out to
    # inspect SUPPORT/CH_A/ISL_A/OUT_A/CELL_A in the debug layers.
    drop_cols = [c for c in ["SUPPORT", "CH_A", "ISL_A", "OUT_A", "CELL_A"] if c in u.fields().names()]
    if drop_cols:
        u = _run(
            "native:deletecolumn",
            {
                "INPUT": u,
                "COLUMN": drop_cols,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        u = _as_layer(u, context) or u

    # Diagnostics.
    try:
        counts = {}
        for f in u.getFeatures():
            v = f[t_field]
            k = "<blank>" if v is None or str(v).strip() == "" else str(v).strip().lower()
            counts[k] = counts.get(k, 0) + 1
        feedback.pushInfo(
            f"[SURFACE SUPPORT OVL3] {yy} {t_field} counts after THREE-WAY area priority: " +
            ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
        )
    except Exception as e:
        feedback.reportError(f"[SURFACE SUPPORT OVL3] debug failed for {yy}: {e}")

    return u

def _enforce_surface_support_on_tags(unionEA, channel_src, island_src, yy, context, feedback):
    """
    Force T_yyyy from authoritative same-date support.

    Priority:
      1) if point-on-surface falls inside same-date channel polygon -> channel
      2) else if inside same-date island polygon -> island
      3) else -> floodplain

    This prevents:
      - false island_* at the active-zone edge
      - missing stable_channel in overlap cores
      - halos caused by indirect island exclusion
    """
    u = _as_layer(unionEA, context) or unionEA
    ch = _as_layer(channel_src, context) or channel_src
    isl = _as_layer(island_src, context) or island_src

    if u is None or not u.isValid():
        raise QgsProcessingException(f"[SURFACE SUPPORT] unionEA invalid for {yy}")

    t_field = f"T_{yy}"
    y_field = f"y_{yy}"

    if u.fields().indexOf(t_field) == -1:
        raise QgsProcessingException(f"[SURFACE SUPPORT] missing {t_field}")
    if u.fields().indexOf(y_field) == -1:
        raise QgsProcessingException(f"[SURFACE SUPPORT] missing {y_field}")

    # stable ID for join-back
    if u.fields().indexOf("RT_ID") == -1:
        u = _run(
            "native:fieldcalculator",
            {
                "INPUT": u,
                "FIELD_NAME": "RT_ID",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 18,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "$id",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        u = _as_layer(u, context) or u

    # point-on-surface for robust support test
    pts = _run(
        "native:pointonsurface",
        {"INPUT": u, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    pts = _as_layer(pts, context) or pts

    # mark channel polygons
    if ch is not None and ch.isValid() and ch.featureCount() > 0:
        ch = _polys_only(ch, context, feedback)
        ch = _force_2d_safe(ch, context, feedback)
        ch = _drop_null_tiny_polys(ch, 1e-6, context, feedback)
        ch = _as_layer(ch, context) or ch

        if ch.fields().indexOf("CH_HIT") == -1:
            ch = _run(
                "native:fieldcalculator",
                {
                    "INPUT": ch,
                    "FIELD_NAME": "CH_HIT",
                    "FIELD_TYPE": 1,
                    "FIELD_LENGTH": 1,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "1",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            ch = _as_layer(ch, context) or ch

        pts = _run(
            "native:joinattributesbylocation",
            {
                "INPUT": pts,
                "JOIN": ch,
                "PREDICATE": [0],  # intersects
                "JOIN_FIELDS": ["CH_HIT"],
                "METHOD": 0,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        pts = _as_layer(pts, context) or pts

    # mark island polygons
    if isl is not None and isl.isValid() and isl.featureCount() > 0:
        isl = _polys_only(isl, context, feedback)
        isl = _force_2d_safe(isl, context, feedback)
        isl = _drop_null_tiny_polys(isl, 1e-6, context, feedback)
        isl = _as_layer(isl, context) or isl

        if isl.fields().indexOf("ISL_HIT") == -1:
            isl = _run(
                "native:fieldcalculator",
                {
                    "INPUT": isl,
                    "FIELD_NAME": "ISL_HIT",
                    "FIELD_TYPE": 1,
                    "FIELD_LENGTH": 1,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "1",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            isl = _as_layer(isl, context) or isl

        pts = _run(
            "native:joinattributesbylocation",
            {
                "INPUT": pts,
                "JOIN": isl,
                "PREDICATE": [0],  # intersects
                "JOIN_FIELDS": ["ISL_HIT"],
                "METHOD": 0,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        pts = _as_layer(pts, context) or pts

    # join support flags back to polygons
    u = _run(
        "native:joinattributestable",
        {
            "INPUT": u,
            "FIELD": "RT_ID",
            "INPUT_2": pts,
            "FIELD_2": "RT_ID",
            "FIELDS_TO_COPY": [c for c in ["CH_HIT", "ISL_HIT"] if c in pts.fields().names()],
            "METHOD": 1,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # Authoritative state assignment
    u = _run(
        "native:fieldcalculator",
        {
            "INPUT": u,
            "FIELD_NAME": t_field,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN coalesce(\"CH_HIT\",0) = 1 THEN 'channel' "
                f"WHEN coalesce(\"ISL_HIT\",0) = 1 THEN 'island' "
                f"ELSE 'floodplain' "
                f"END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # ensure y field is not blank
    u = _run(
        "native:fieldcalculator",
        {
            "INPUT": u,
            "FIELD_NAME": y_field,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN \"{y_field}\" IS NULL OR trim(to_string(\"{y_field}\")) = '' "
                f"THEN '{yy}' "
                f"ELSE trim(to_string(\"{y_field}\")) "
                f"END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    u = _as_layer(u, context) or u

    # clean helper columns
    drop_cols = [c for c in ["CH_HIT", "ISL_HIT"] if c in u.fields().names()]
    if drop_cols:
        u = _run(
            "native:deletecolumn",
            {"INPUT": u, "COLUMN": drop_cols, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        u = _as_layer(u, context) or u

    # diagnostics
    try:
        counts = {}
        for f in u.getFeatures():
            v = f[t_field]
            k = "<blank>" if v is None or str(v).strip() == "" else str(v).strip().lower()
            counts[k] = counts.get(k, 0) + 1
        feedback.pushInfo(
            f"[SURFACE SUPPORT] {yy} {t_field} counts: " +
            ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
        )
    except Exception as e:
        feedback.reportError(f"[SURFACE SUPPORT] debug failed for {yy}: {e}")

    return u

def _collapse_authoritative_ea_fields(layer, y1, y2, context, feedback):
    """
    Collapse duplicated fields created by merge/join steps.

    Keeps one authoritative set:
      EA
      y_<y1>, T_<y1>
      y_<y2>, T_<y2>
      PeriodEnd
      direction
      migration
      period
      span_days
      span_years

    If duplicate *_2 fields exist and the base field is NULL/blank,
    copy from the duplicate. Then delete the duplicate fields.
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException("[EA COLLAPSE] invalid layer")

    pairs = [
        ("EA", "EA_2"),
        (f"y_{y1}", f"y_{y1}_2"),
        (f"T_{y1}", f"T_{y1}_2"),
        (f"y_{y2}", f"y_{y2}_2"),
        (f"T_{y2}", f"T_{y2}_2"),

        ("PeriodEnd", "PeriodEnd_2"),
        ("direction", "direction_2"),
        ("migration", "migration_2"),
        ("period", "period_2"),
        ("span_days", "span_days_2"),
        ("span_years", "span_years_2"),
    ]

    for base, dup in pairs:
        base_idx = lyr.fields().indexOf(base)
        dup_idx = lyr.fields().indexOf(dup)

        if dup_idx == -1:
            continue

        dup_field = lyr.fields().field(dup)

        if base_idx == -1:
            lyr = _run(
                "native:fieldcalculator",
                {
                    "INPUT": lyr,
                    "FIELD_NAME": base,
                    "FIELD_TYPE": dup_field.type(),
                    "FIELD_LENGTH": dup_field.length(),
                    "FIELD_PRECISION": dup_field.precision(),
                    "NEW_FIELD": True,
                    "FORMULA": f"\"{dup}\"",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            lyr = _as_layer(lyr, context) or lyr
        else:
            base_field = lyr.fields().field(base)

            # numeric-ish fields
            if base in ("span_days", "span_years"):
                formula = (
                    f"CASE "
                    f"WHEN \"{base}\" IS NULL THEN coalesce(\"{dup}\", \"{base}\") "
                    f"ELSE \"{base}\" "
                    f"END"
                )
            else:
                formula = (
                    f"CASE "
                    f"WHEN \"{base}\" IS NULL OR trim(to_string(\"{base}\")) = '' "
                    f"THEN coalesce(\"{dup}\", \"{base}\") "
                    f"ELSE \"{base}\" "
                    f"END"
                )

            lyr = _run(
                "native:fieldcalculator",
                {
                    "INPUT": lyr,
                    "FIELD_NAME": base,
                    "FIELD_TYPE": base_field.type(),
                    "FIELD_LENGTH": base_field.length(),
                    "FIELD_PRECISION": base_field.precision(),
                    "NEW_FIELD": False,
                    "FORMULA": formula,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            lyr = _as_layer(lyr, context) or lyr

    drop_cols = [dup for _, dup in pairs if lyr.fields().indexOf(dup) != -1]

    if drop_cols:
        lyr = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": drop_cols,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        lyr = _as_layer(lyr, context) or lyr

    try:
        present = [f.name() for f in lyr.fields()]
        feedback.pushInfo(
            "[EA COLLAPSE] fields now include: " +
            ", ".join(
                [
                    x for x in [
                        "EA",
                        f"y_{y1}", f"T_{y1}",
                        f"y_{y2}", f"T_{y2}",
                        "PeriodEnd", "direction", "migration",
                        "period", "span_days", "span_years"
                    ]
                    if x in present
                ]
            )
        )
    except Exception as e:
        feedback.reportError(f"[EA COLLAPSE] debug failed: {e}")

    return lyr

def _extract_holes_as_layer(poly_in, context, feedback):
    """
    Return interior rings (holes) from polygon/multipolygon input
    as a polygon layer. Used for island extraction in Step 2.
    """
    try:
        lyr = _as_layer(poly_in, context)
        if lyr is None or not lyr.isValid():
            feedback.pushInfo("[HOLES] input invalid")
            return None

        if lyr.featureCount() == 0:
            feedback.pushInfo("[HOLES] input empty")
            return None

        crs_authid = lyr.crs().authid()
        mem = QgsVectorLayer(f"Polygon?crs={crs_authid}", "holes", "memory")
        prov = mem.dataProvider()
        mem.updateFields()

        feats_out = []

        for feat in lyr.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue

            if geom.isMultipart():
                polys = geom.asMultiPolygon()
            else:
                p = geom.asPolygon()
                polys = [p] if p else []

            for poly in polys:
                # poly[0] exterior, poly[1:] interior rings
                if not poly or len(poly) < 2:
                    continue

                for ring in poly[1:]:
                    if ring is None or len(ring) < 4:
                        continue

                    g = QgsGeometry.fromPolygonXY([ring])
                    if g is None or g.isEmpty():
                        continue

                    try:
                        if not g.isGeosValid():
                            g = g.makeValid()
                    except Exception:
                        pass

                    if g is None or g.isEmpty():
                        continue

                    fnew = QgsFeature()
                    fnew.setGeometry(g)
                    feats_out.append(fnew)

        if not feats_out:
            feedback.pushInfo("[HOLES] no holes found")
            return None

        prov.addFeatures(feats_out)
        mem.updateExtents()
        feedback.pushInfo(f"[HOLES] extracted {len(feats_out)} hole polygon(s)")
        return mem

    except Exception as e:
        feedback.reportError(f"[HOLES ERROR] {str(e)}")
        return None
    
def _force_crs(layer, target_crs, context, feedback=None, label="layer"):
    """
    Ensure a layer has a valid CRS assigned.
    Does not reproject coordinates; only assigns CRS metadata if missing/invalid.
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        if feedback:
            feedback.reportError(f"[CRS] {label}: invalid layer, cannot assign CRS.")
        return layer

    try:
        cur = lyr.crs()
        if cur and cur.isValid():
            if target_crs and cur == target_crs:
                if feedback:
                    feedback.pushInfo(f"[CRS] {label}: CRS already {target_crs.authid()}")
                return lyr
    except Exception:
        pass

    try:
        out = _run(
            "native:assignprojection",
            {
                "INPUT": lyr,
                "CRS": target_crs,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        out = _as_layer(out, context) or out
        if feedback and out and out.isValid():
            feedback.pushInfo(f"[CRS] {label}: assigned CRS {target_crs.authid()}")
        return out
    except Exception as e:
        if feedback:
            feedback.reportError(f"[CRS] {label}: assignprojection failed: {e}")
        return lyr
    
# PURPOSE: Reopen a disk output and inspect its geometry/extent rather than trusting the in-memory layer.
def _dbg_written_gpkg(gpkg_path, layer_name, feedback):
    if not _dbg_enabled():
        return
    """
    Reload a written GPKG layer from disk and report geometry diagnostics.
    """
    try:
        lyr = QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", layer_name, "ogr")
        if not lyr.isValid():
            feedback.reportError(f"[DBG WRITE] Could not reload written layer: {layer_name}")
            return

        try:
            geom_txt = QgsWkbTypes.displayString(lyr.wkbType())
        except Exception:
            geom_txt = str(lyr.wkbType())

        ext = lyr.extent()
        feedback.pushInfo(
            f"[DBG WRITE] {layer_name}: fc={lyr.featureCount()} geom={geom_txt} crs={lyr.crs().authid()}"
        )
        feedback.pushInfo(
            f"[DBG WRITE] {layer_name}: extent xmin={ext.xMinimum()} xmax={ext.xMaximum()} "
            f"ymin={ext.yMinimum()} ymax={ext.yMaximum()}"
        )

        null_geom = 0
        empty_geom = 0
        zero_area = 0
        for f in lyr.getFeatures():
            g = f.geometry()
            if g is None or g.isNull():
                null_geom += 1
                continue
            if g.isEmpty():
                empty_geom += 1
                continue
            try:
                if abs(g.area()) < 1e-9:
                    zero_area += 1
            except Exception:
                pass

        feedback.pushInfo(
            f"[DBG WRITE] {layer_name}: null={null_geom} empty={empty_geom} zero_area={zero_area}"
        )

    except Exception as e:
        feedback.reportError(f"[DBG WRITE] Failed to inspect written layer {layer_name}: {e}")

# PURPOSE: Summarise mapped EA classes and area coverage for planar-fabric QA.
def _dbg_EA_coverage(label, layer, context, feedback):
    if not _dbg_enabled():
        return
    """
    Report area coverage by EA class.
    Designed to diagnose planarize / hollow-fill failures.
    """
    try:
        lyr = _as_layer(layer, context, feedback)
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[EA-DIAG] {label}: invalid layer")
            return

        if lyr.fields().indexOf("EA") == -1:
            feedback.reportError(f"[EA-DIAG] {label}: missing EA field")
            return

        total_area = 0.0
        ea_area = 0.0
        bg_area = 0.0
        counts = {}

        for f in lyr.getFeatures():
            a = f.geometry().area() if f.geometry() else 0.0
            total_area += a
            ea = (f["EA"] or "").strip()
            counts[ea] = counts.get(ea, 0) + 1

            if ea == "stable_floodplain":
                bg_area += a
            else:
                ea_area += a

        if total_area > 0:
            pct_ea = 100.0 * ea_area / total_area
            pct_bg = 100.0 * bg_area / total_area
        else:
            pct_ea = pct_bg = 0.0

        feedback.pushInfo(
            f"[EA-DIAG] {label}: "
            f"EA_area={ea_area:.1f} ({pct_ea:.1f}%) | "
            f"BG_area={bg_area:.1f} ({pct_bg:.1f}%) | "
            f"features={lyr.featureCount()}"
        )

        # Optional: top EA classes by count
        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:6]
        feedback.pushInfo(
            "[EA-DIAG] classes: " +
            ", ".join(f"{k or '<NULL>'}={v}" for k, v in top)
        )

    except Exception as e:
        feedback.reportError(f"[EA-DIAG] {label} failed: {e}")
        
# PURPOSE: Use field refactoring to prevent truncation of date-specific surface tags.
def _widen_text_field(layer, field_name, width, context, feedback):
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        return layer

    fields = lyr.fields()
    idx = fields.indexOf(field_name)
    if idx == -1:
        return layer

    # Only run refactor if we actually need to widen the target
    fld = fields[idx]
    if fld.length() >= width:
        return layer

    feedback.pushInfo(f"[SCHEMA] widening {field_name} to {width} (forcing T_/y_ to text)")

    mapping = []
    for f in fields:
        name = f.name()

        # Default: preserve
        f_type = f.type()
        f_len  = f.length()
        f_prec = f.precision()

        # CRITICAL: any T_* or y_* must be TEXT because they store strings like "channel"
        if name.startswith("T_") or name.startswith("y_"):
            f_type = 2                      # String
            f_prec = 0
            # widen any T_/y_ if needed (avoid truncation issues)
            f_len = max(f_len or 0, width)

        # Also widen just the requested field (covers non T_/y_ cases too)
        if name == field_name:
            f_type = 2
            f_prec = 0
            f_len = max(f_len or 0, width)

        mapping.append({
            "expression": f"\"{name}\"",
            "name": name,
            "type": f_type,
            "length": int(f_len) if f_len else 0,
            "precision": int(f_prec) if f_prec else 0,
        })

    return _run(
        "native:refactorfields",
        {
            "INPUT": lyr,
            "FIELDS_MAPPING": mapping,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

# PURPOSE: Ensure y_ and T_ observation tags are stored as strings across QGIS overlay operations.
def _force_tag_fields_text(layer, ymds, width, context, feedback):
    lyr = _as_layer(layer, context)
    if not lyr or not lyr.isValid():
        return layer

    tag_names = set()
    for ymd in ymds:
        tag_names.add(f"y_{ymd}")
        tag_names.add(f"T_{ymd}")

    mapping = []
    for f in lyr.fields():
        name = f.name()

        # If it's one of our tag fields, force STRING and coerce values to string
        if name in tag_names:
            mapping.append({
                "name": name,
                "type": 10,            # String
                "length": int(width),
                "precision": 0,
                "expression": f"to_string(\"{name}\")"
            })
        else:
            # Preserve everything else exactly
            mapping.append({
                "name": name,
                "type": f.type(),
                "length": f.length(),
                "precision": f.precision(),
                "expression": f"\"{name}\""
            })

    feedback.pushInfo(f"[SCHEMA] forcing tags to text: {', '.join(sorted(tag_names))} (len={width})")
    out = _run(
        "native:refactorfields",
        {
            "INPUT": lyr,
            "FIELDS_MAPPING": mapping,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    return out
        
# PURPOSE: Populate missing observation-date labels and conservatively mark unresolved type tags as floodplain.
def _fill_missing_tags(unionEA, ymd, context, feedback):
    yfld = f"y_{ymd}"
    tfld = f"T_{ymd}"

    lyr = _as_layer(unionEA, context)
    if lyr is None or not lyr.isValid():
        feedback.reportError(f"[TAGFILL] Invalid input layer for {ymd}.")
        return unionEA

    if lyr.fields().indexOf(yfld) == -1 or lyr.fields().indexOf(tfld) == -1:
        feedback.reportError(f"[TAGFILL] Missing {yfld}/{tfld}; cannot fill.")
        return unionEA

    # Fill missing date tag with the actual date string
    unionEA = _run(
        "native:fieldcalculator",
        {
            "INPUT": unionEA,
            "FIELD_NAME": yfld,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": f"coalesce(nullif(trim(to_string(\"{yfld}\")), ''), '{ymd}')",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    # Fill missing type tag with floodplain, not stable_floodplain
    unionEA = _run(
        "native:fieldcalculator",
        {
            "INPUT": unionEA,
            "FIELD_NAME": tfld,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": f"coalesce(nullif(lower(trim(to_string(\"{tfld}\"))), ''), 'floodplain')",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    miss = _run(
        "native:extractbyexpression",
        {
            "INPUT": unionEA,
            "EXPRESSION": (
                f"\"{yfld}\" IS NULL OR trim(to_string(\"{yfld}\")) = '' OR "
                f"\"{tfld}\" IS NULL OR trim(to_string(\"{tfld}\")) = ''"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    miss_lyr = _as_layer(miss, context)
    feedback.pushInfo(
        f"[TAGFILL] after fill {ymd}: missing={miss_lyr.featureCount() if miss_lyr and miss_lyr.isValid() else -1}"
    )

    return unionEA
def _recompute_ea_from_tags(layer, y1, y2, context, feedback):
    """
    Rebuild EA from authoritative T_y1 / T_y2 fields after planarize/support enforcement.

    IMPORTANT:
      - always writes to authoritative field EA
      - deletes any pre-existing EA / EA_2 first so QGIS cannot silently create EA_2
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException("[EA REBUILD] invalid layer")

    # ------------------------------------------------------------------
    # Remove stale EA fields first so fieldcalculator cannot create EA_2
    # ------------------------------------------------------------------
    drop_cols = []
    for fld in ["EA", "EA_2"]:
        if lyr.fields().indexOf(fld) != -1:
            drop_cols.append(fld)

    if drop_cols:
        lyr = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": drop_cols,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        lyr = _as_layer(lyr, context) or lyr

    ea_expr = f"""
    WITH_VARIABLE('t1', lower(trim(coalesce(nullif("T_{y1}",''), 'floodplain'))),
    WITH_VARIABLE('t2', lower(trim(coalesce(nullif("T_{y2}",''), 'floodplain'))),

    CASE
        WHEN @t1='island' AND @t2='channel' THEN 'island_erosion'
        WHEN @t1='channel' AND @t2='island' THEN 'island_deposition'
        WHEN @t1='island' AND @t2='island' THEN 'stable_island'

        WHEN @t1='floodplain' AND @t2='channel' THEN 'erosion'
        WHEN @t1='channel' AND @t2='floodplain' THEN 'deposition'
        WHEN @t1='channel' AND @t2='channel' THEN 'stable_channel'
        WHEN @t1='floodplain' AND @t2='floodplain' THEN 'stable_floodplain'

        WHEN @t1='island' AND @t2='floodplain' THEN 'stable_floodplain'
        WHEN @t1='floodplain' AND @t2='island' THEN 'island_deposition'

        ELSE 'stable_floodplain'
    END
    ))
    """.strip()

    lyr = _run(
        "native:fieldcalculator",
        {
            "INPUT": lyr,
            "FIELD_NAME": "EA",
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": True,
            "FORMULA": ea_expr,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    lyr = _as_layer(lyr, context) or lyr
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException("[EA REBUILD] failed to rebuild EA")

    try:
        counts = {}
        for f in lyr.getFeatures():
            v = f["EA"]
            k = "<blank>" if v is None or str(v).strip() == "" else str(v).strip()
            counts[k] = counts.get(k, 0) + 1
        feedback.pushInfo(
            "[EA REBUILD] counts: " +
            ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
        )
    except Exception as e:
        feedback.reportError(f"[EA REBUILD] debug failed: {e}")

    return lyr

def _algo_exists(alg_id):
    """
    Check whether a processing algorithm exists in the current QGIS registry.
    Used to select between native/qgis variants and to avoid calling missing algs.
    """
    from qgis.core import QgsApplication
    try:
        return QgsApplication.processingRegistry().algorithmById(alg_id) is not None
    except Exception:
        return False


# PURPOSE: Execute a QGIS child Processing algorithm with shared context and progress feedback.
def _run(alg, params, context, feedback=None):
    if _dbg_enabled() and feedback is not None:
        feedback.pushInfo(f"Running {alg} ...")
    return processing.run(
        alg, params,
        context=context,
        feedback=feedback,
        is_child_algorithm=True
    )



def _as_layer(obj, context, feedback=None, _depth=0):
    """
    Resolve obj (layer, id, name, URI, path, or arbitrary INPUT param) to a valid QgsVectorLayer.
    """
    if _depth > 1:
        return None

    # 1) Already a QgsVectorLayer
    try:
        if hasattr(obj, "isValid") and obj.isValid():
            return obj
    except Exception:
        pass

    s = str(obj) if obj is not None else ""

    # 2) Try processing resolver
    try:
        lyr = QgsProcessingUtils.mapLayerFromString(s, context)
        if lyr and lyr.isValid():
            return lyr
    except Exception:
        pass

    # 3) Try project-by-id lookup
    try:
        lyr = QgsProject.instance().mapLayer(s)
        if lyr and lyr.isValid():
            return lyr
    except Exception:
        pass

    # 4) Try loading via OGR provider
    try:
        if os.path.exists(s) or "|layername=" in s.lower() or s.lower().startswith("postgres"):
            name = os.path.splitext(os.path.basename(s))[0] if os.path.exists(s) else "layer"
            lyr = QgsVectorLayer(s, name, "ogr")
            if lyr and lyr.isValid():
                return lyr
    except Exception:
        pass

    # 5) Last resort: materialize to TEMPORARY_OUTPUT
    # Only if obj is not a plain string (strings that failed above usually fail savefeatures too)
    if feedback is not None and not isinstance(obj, str):
        try:
            out = _run(
                "native:savefeatures",
                {"INPUT": obj, "OUTPUT": "TEMPORARY_OUTPUT"},
                context,
                feedback
            )["OUTPUT"]
            lyr = _as_layer(out, context, feedback, _depth=_depth + 1)
            if lyr and lyr.isValid():
                return lyr
        except Exception:
            pass

    return None

def _ensure_layer(obj, context, feedback=None, tag="layer"):
    """
    Return a valid QgsVectorLayer (or raise).
    Accepts: layer, path/URI, processing output.
    """
    lyr = _as_layer(obj, context, feedback)
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[{tag}] invalid/None layer | obj={obj}")
    return lyr


# PURPOSE: Report a minimal layer validity/feature count/geometry-type diagnostic.
def _dbg_layer_simple(feedback, prefix, lyr):
    if not _dbg_enabled():
        return
    try:
        if feedback:
            if lyr is None:
                feedback.pushInfo(f"[DBG] {prefix}: None")
            else:
                feedback.pushInfo(
                    f"[DBG] {prefix}: valid={lyr.isValid()} fc={lyr.featureCount()} "
                    f"geom={QgsWkbTypes.displayString(lyr.wkbType())}"
                )
    except Exception:
        pass



def _add_const_field(layer, name, formula, ftype, length, precision, context, feedback):
    """
    Create or update a field using Field Calculator.
    Parameters:
        layer   : input layer or reference
        name    : field name
        formula : QGIS expression (string), e.g. "'text'", "1", etc.
        ftype   : 0=float, 1=int, 2=string
        length  : field length
        precision: field precision
    Returns:
        Updated layer (as layer object or ID) if successful, else original layer.
    """
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        if feedback:
            feedback.reportError(f"[_add_const_field] Invalid layer for field {name}.")
        return layer

    # Determine whether the field already exists; if so we update, else we create
    field_exists = name in lyr.fields().names()
    params = {
        "INPUT": lyr,
        "FIELD_NAME": name,
        "NEW_FIELD": not field_exists,
        "FORMULA": formula,
        "OUTPUT": "TEMPORARY_OUTPUT",
    }
    if not field_exists:
        # Only need to specify type/length/precision when a new field is created
        params.update({
            "FIELD_TYPE": int(ftype),
            "FIELD_LENGTH": int(length),
            "FIELD_PRECISION": int(precision),
        })
    try:
        out = _run("native:fieldcalculator", params, context, feedback)["OUTPUT"]
        return _as_layer(out, context) or out
    except Exception as e:
        if feedback:
            feedback.reportError(f"[_add_const_field] Failed for '{name}': {e}")
        return lyr


# PURPOSE: Strip imported feature identifiers that can collide with GeoPackage primary keys.
def _strip_pk_fields(layer, context, feedback=None):
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        return lyr

    pk_like = []
    for f in lyr.fields():
        nm = f.name().strip()
        if nm.lower() in ("fid", "id", "objectid", "oid", "old_fid"):
            pk_like.append(nm)

    if not pk_like:
        return lyr

    try:
        out = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": pk_like,
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]
        return _as_layer(out, context) or lyr
    except Exception as e:
        if feedback:
            feedback.reportError(f"[strip_pk_fields] failed: {e}")
        return lyr

# PURPOSE: Convert geometries to 2D using the first installed compatible Processing algorithm.
def _force_2d_safe(layer, context, feedback=None):
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        return _as_layer(layer, context)

    # Try force2d variants first
    for alg in ("native:force2d", "qgis:force2d"):
        if _algo_exists(alg):
            try:
                out = _run(alg, {"INPUT": lyr, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
                o = _as_layer(out, context)
                if o and o.isValid():
                    return o
            except Exception:
                pass

    # Then drop M/Z
    for alg in ("native:dropmz", "qgis:dropmz"):
        if _algo_exists(alg):
            try:
                out = _run(
                    alg,
                    {"INPUT": lyr, "DROP_M": True, "DROP_Z": True, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                o = _as_layer(out, context)
                if o and o.isValid():
                    return o
            except Exception:
                pass

    return lyr

def _add_in_corridor_flag(
    cells,
    chan_y1,
    chan_y2,
    channel_width,
    context,
    feedback,
    S,
    ref_crs_obj = None,
    tag=""
):
    """
    Adds integer field IN_CORR to *existing* polygons (cells/unionEA):
      1 = intersects interval channel corridor
      0 = outside

    IMPORTANT:
    - Do NOT dissolve by a hard-coded field like CELLID (unionEA often doesn't have it).
    - Preserve geometry + all attributes on the input layer.
    """
    corr_mult = float(S.get("corridor_mult", 2.0))
    corr_dist = max(0.0, float(channel_width) * corr_mult)

    # merge + dissolve channel footprints
    ch_merge = _run(
        "native:mergevectorlayers",
        {"LAYERS": [chan_y1, chan_y2], "CRS": ref_crs_obj, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    ch_foot = _run(
        "native:dissolve",
        {"INPUT": ch_merge, "FIELD": [], "SEPARATE_DISJOINT": False, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    corridor = _run(
        "native:buffer",
        {
            "INPUT": ch_foot,
            "DISTANCE": corr_dist,
            "SEGMENTS": 8,
            "DISSOLVE": True,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    corridor = _ensure_layer(corridor, context, tag=f"corridor_{tag}")

    cells = _ensure_layer(cells, context, tag=f"cells_incorr_in_{tag}")

    # Pick / create a stable join key
    join_key = None
    for cand in ("CELLID", "EAID", "fid", "id", "ID", "OBJECTID"):
        if cand in cells.fields().names():
            join_key = cand
            break

    if join_key is None:
        # create a temporary UID from $id (safe for in-memory/shp temp outputs)
        cells = _run(
            "native:fieldcalculator",
            {
                "INPUT": cells,
                "FIELD_NAME": "_UID",
                "FIELD_TYPE": 1,      # int
                "FIELD_LENGTH": 10,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "$id",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        cells = _ensure_layer(cells, context, tag=f"cells_uid_{tag}")
        join_key = "_UID"

    # Ensure IN_CORR exists and starts at 0
    if "IN_CORR" not in cells.fields().names():
        cells = _run(
            "native:fieldcalculator",
            {
                "INPUT": cells,
                "FIELD_NAME": "IN_CORR",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 1,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "0",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        cells = _ensure_layer(cells, context, tag=f"cells_incorr0_{tag}")
    else:
        # normalise to 0/1 (keeps existing values if any)
        cells = _run(
            "native:fieldcalculator",
            {
                "INPUT": cells,
                "FIELD_NAME": "IN_CORR",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 1,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": 'coalesce("IN_CORR",0)',
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        cells = _ensure_layer(cells, context, tag=f"cells_incorr_norm_{tag}")

    # Extract intersecting polygons (preserve join_key)
    cells_in = _run(
        "native:extractbylocation",
        {
            "INPUT": cells,
            "PREDICATE": [0],   # intersects
            "INTERSECT": corridor,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    cells_in = _run(
        "native:fieldcalculator",
        {
            "INPUT": cells_in,
            "FIELD_NAME": "IN_CORR",
            "FIELD_TYPE": 1,
            "FIELD_LENGTH": 1,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": "1",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    cells_in = _ensure_layer(cells_in, context, tag=f"cells_incorr1_{tag}")

    # Join IN_CORR back (no geometry change, no dissolve)
    joined = _run(
        "native:joinattributestable",
        {
            "INPUT": cells,
            "FIELD": join_key,
            "INPUT_2": cells_in,
            "FIELD_2": join_key,
            "FIELDS_TO_COPY": ["IN_CORR"],
            "METHOD": 1,           # take the first matching
            "DISCARD_NONMATCHING": False,
            "PREFIX": "J_",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    joined = _ensure_layer(joined, context, tag=f"cells_incorr_join_{tag}")

    # Consolidate: IN_CORR = max(IN_CORR, J_IN_CORR)
    joined = _run(
        "native:fieldcalculator",
        {
            "INPUT": joined,
            "FIELD_NAME": "IN_CORR",
            "FIELD_TYPE": 1,
            "FIELD_LENGTH": 1,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": 'case when coalesce("IN_CORR",0)=1 OR coalesce("J_IN_CORR",0)=1 then 1 else 0 end',
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    # Drop join helper
    joined = _run(
        "native:deletecolumn",
        {
            "INPUT": joined,
            "COLUMN": ["J_IN_CORR"],
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    joined = _ensure_layer(joined, context, tag=f"cells_incorr_done_{tag}")
    return joined


# PURPOSE: Discard line and point by-products of overlay operations; retain polygon geometries only.
def _polys_only(layer, context, feedback=None):
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        return lyr

    out = _run(
        "native:extractbyexpression",
        {
            "INPUT": lyr,
            "EXPRESSION": "geometry_type($geometry) IN ('Polygon','MultiPolygon')",
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]

    return _as_layer(out, context) or out

def _freeze_to_tmp_gpkg(layer, context, feedback, layer_name=None, ref_crs=None, tag=None):
    """
    Save a layer to a temporary GeoPackage and reload it as a file-backed layer.

    Safe behaviour:
      - accepts layer_name or tag
      - resolves to a real QgsVectorLayer
      - assigns CRS if missing (assign only; no reprojection)
      - writes to temp GPKG
      - reloads robustly
      - forces CRS in-memory after reload if provider returns blank CRS
      - hard-fails on invalid/NaN/Inf extent after reload
    """
    import math
    import os

    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException("[freeze gpkg] invalid input layer")

    # PURPOSE: Check that CRS metadata are present and usable.
    def _valid_crs(crs):
        try:
            return (
                crs is not None
                and crs.isValid()
                and bool(crs.authid())
                and str(crs.authid()).strip() != ""
            )
        except Exception:
            return False

    # PURPOSE: Reject invalid/non-finite geometry extents before or after data operations.
    def _extent_is_finite(vlayer):
        if vlayer is None or not vlayer.isValid():
            return False
        try:
            ext = vlayer.extent()
            vals = [ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum()]
            return all(math.isfinite(float(v)) for v in vals)
        except Exception:
            return False

    # PURPOSE: Format an extent for meaningful QA messages.
    def _extent_txt(vlayer):
        try:
            ext = vlayer.extent()
            return (
                f"xmin={ext.xMinimum()} xmax={ext.xMaximum()} "
                f"ymin={ext.yMinimum()} ymax={ext.yMaximum()}"
            )
        except Exception:
            return "<extent unavailable>"

    # PURPOSE: Safely report a feature count without allowing logging to interrupt processing.
    def _fc(vlayer):
        try:
            return vlayer.featureCount()
        except Exception:
            return -1

    try:
        src_name = lyr.name() if hasattr(lyr, "name") else "frozen_layer"
    except Exception:
        src_name = "frozen_layer"

    name = _safe_token(str(layer_name or tag or src_name or "frozen_layer"))

    try:
        lyr_crs = lyr.crs() if hasattr(lyr, "crs") else None
    except Exception:
        lyr_crs = None

    src_crs = lyr_crs if _valid_crs(lyr_crs) else ref_crs

    feedback.pushInfo(
        f"[FREEZE GPKG DBG] {name} "
        f"input_crs={lyr_crs.authid() if _valid_crs(lyr_crs) else '<invalid>'} "
        f"src_crs={src_crs.authid() if _valid_crs(src_crs) else '<invalid>'}"
    )

    if not _valid_crs(src_crs):
        feedback.reportError(f"[FREEZE GPKG] {name} source CRS invalid before save")

    if (not _valid_crs(lyr_crs)) and _valid_crs(src_crs):
        try:
            lyr.setCrs(src_crs)
            feedback.reportError(
                f"[FREEZE GPKG] {name} input had blank CRS; assigned {src_crs.authid()} before write"
            )
        except Exception as e:
            raise QgsProcessingException(
                f"[FREEZE GPKG] {name} could not assign CRS before write: {e}"
            )

    if not _extent_is_finite(lyr):
        raise QgsProcessingException(
            f"[FREEZE GPKG] {name} input extent invalid before save: {_extent_txt(lyr)}"
        )

    feedback.pushInfo(
        f"[FREEZE GPKG] {name} pre-save fc={_fc(lyr)} "
        f"crs={src_crs.authid() if _valid_crs(src_crs) else '<invalid>'} "
        f"extent={_extent_txt(lyr)}"
    )

    out_path = QgsProcessingUtils.generateTempFilename(f"{name}.gpkg")

    try:
        _run(
            "native:savefeatures",
            {
                "INPUT": lyr,
                "OUTPUT": out_path
            },
            context, feedback
        )
    except Exception as e:
        raise QgsProcessingException(f"[FREEZE GPKG] {name} write failed: {e}")

    if not os.path.exists(out_path):
        raise QgsProcessingException(f"[FREEZE GPKG] {name} output not created: {out_path}")

    # Safer with native:savefeatures: open bare path first
    frozen = QgsVectorLayer(out_path, name, "ogr")

    if frozen is None or not frozen.isValid():
        uri_named = f"{out_path}|layername={name}"
        frozen = QgsVectorLayer(uri_named, name, "ogr")

    if frozen is None or not frozen.isValid():
        raise QgsProcessingException(
            f"[freeze gpkg] failed to reload {name} from {out_path}"
        )

    if (not _valid_crs(frozen.crs())) and _valid_crs(src_crs):
        try:
            frozen.setCrs(src_crs)
            feedback.reportError(
                f"[FREEZE GPKG] {name} reloaded with blank CRS; forced in-memory CRS {src_crs.authid()}"
            )
        except Exception as e:
            raise QgsProcessingException(
                f"[FREEZE GPKG] {name} reload CRS repair failed: {e}"
            )

    if (not _valid_crs(frozen.crs())) and _valid_crs(src_crs):
        raise QgsProcessingException(
            f"[FREEZE GPKG] {name} reload CRS still blank after repair"
        )

    try:
        frozen.dataProvider().forceReload()
    except Exception:
        pass

    try:
        frozen.updateExtents()
    except Exception:
        pass

    if not _extent_is_finite(frozen):
        raise QgsProcessingException(
            f"[FREEZE GPKG] {name} reloaded with invalid extent: {_extent_txt(frozen)}"
        )

    feedback.pushInfo(f"[FREEZE GPKG] {name} → {out_path}")
    feedback.pushInfo(
        f"[FREEZE GPKG] {name} reload fc={_fc(frozen)} "
        f"crs={frozen.crs().authid() if _valid_crs(frozen.crs()) else '<invalid>'} "
        f"extent={_extent_txt(frozen)}"
    )

    return frozen

def _buffer0_polys(layer, context, feedback, tag="buf0"):
    """
    GEOS robustness: buffer(0) can repair polygon topology beyond fixgeometries.
    Only apply to polygon layers.
    """
    layer = _ensure_layer(layer, context, tag=tag)
    try:
        return _run(
            "native:buffer",
            {
                "INPUT": layer,
                "DISTANCE": 0.0,
                "SEGMENTS": 5,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2.0,
                "DISSOLVE": False,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
    except Exception as e:
        if feedback:
            feedback.reportError(f"[{tag}] buffer(0) failed: {e}")
        return layer



def _ensure_polygon(layer, context, feedback, tag, tiny=0.01):
    """
    Return a non-empty polygon layer from polygon/line/point input.

    - Polygon: fixgeometries -> force 2D
    - Line: linestopolygons -> polygonize -> tiny buffer fallback
    - Point: tiny buffer
    - Other: raise

    Raises if conversion results in an invalid or empty polygon layer.
    """
    # PURPOSE: Test that a candidate conversion produced non-empty polygon geometry.
    def _usable_polygon(obj, label):
        lyr0 = _as_layer(obj, context) or obj
        if lyr0 is None or not lyr0.isValid():
            return None
        try:
            if lyr0.featureCount() == 0:
                return None
        except Exception:
            return None
        try:
            gt = QgsWkbTypes.geometryType(lyr0.wkbType())
            if gt != QgsWkbTypes.PolygonGeometry:
                return None
        except Exception:
            return None
        return lyr0

    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[{tag}] invalid layer")

    gtype = QgsWkbTypes.geometryType(lyr.wkbType())

    # Case 1: Already polygon / multipolygon
    if gtype == QgsWkbTypes.PolygonGeometry:
        orig = lyr

        # Try cleaning
        try:
            cleaned = _run(
                "native:fixgeometries",
                {"INPUT": lyr, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
        except Exception:
            cleaned = orig

        cleaned = _force_2d_safe(cleaned, context, feedback)
        cleaned_lyr = _as_layer(cleaned, context) or cleaned

        # If cleaned result is valid and non-empty → use it
        if (
            cleaned_lyr is not None
            and cleaned_lyr.isValid()
            and cleaned_lyr.featureCount() > 0
        ):
            return cleaned_lyr

        # Otherwise fallback to original polygon input
        orig_lyr = _as_layer(orig, context) or orig
        if (
            orig_lyr is not None
            and orig_lyr.isValid()
            and orig_lyr.featureCount() > 0
        ):
            if feedback:
                feedback.reportError(
                    f"[{tag}] cleaned polygon became empty; using original polygon input"
                )
            return orig_lyr

        # If both fail → real error
        raise QgsProcessingException(
            f"[{tag}] polygon input became invalid/empty after cleaning"
        )

    # Case 2: line -> polygon
    if gtype == QgsWkbTypes.LineGeometry:
        poly = None

        if _algo_exists("native:linestopolygons"):
            try:
                cand = _run(
                    "native:linestopolygons",
                    {"LINES": lyr, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                cand = _force_2d_safe(cand, context, feedback)
                if _usable_polygon(cand, f"{tag}:linestopolygons") is not None:
                    poly = cand
            except Exception:
                pass

        if poly is None:
            try:
                cand = _run(
                    "native:polygonize",
                    {"INPUT": lyr, "KEEP_FIELDS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                cand = _run(
                    "native:extractbyexpression",
                    {
                        "INPUT": cand,
                        "EXPRESSION": "geometry_type($geometry) IN ('Polygon','MultiPolygon')",
                        "OUTPUT": "TEMPORARY_OUTPUT"
                    },
                    context, feedback
                )["OUTPUT"]
                cand = _force_2d_safe(cand, context, feedback)
                if _usable_polygon(cand, f"{tag}:polygonize") is not None:
                    poly = cand
            except Exception:
                pass

        # last resort: tiny buffer around lines
        if poly is None:
            cand = _run(
                "native:buffer",
                {
                    "INPUT": lyr,
                    "DISTANCE": tiny,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "DISSOLVE": False,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            cand = _force_2d_safe(cand, context, feedback)
            if _usable_polygon(cand, f"{tag}:line_buffer") is not None:
                poly = cand

        if poly is None:
            raise QgsProcessingException(f"[{tag}] could not convert line layer to non-empty polygons")

        try:
            poly = _run(
                "native:dissolve",
                {
                    "INPUT": poly,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
        except Exception:
            pass

        try:
            poly = _run(
                "native:fixgeometries",
                {"INPUT": poly, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
        except Exception:
            pass

        poly = _force_2d_safe(poly, context, feedback)
        poly_lyr = _usable_polygon(poly, f"{tag}:line_final")
        if poly_lyr is None:
            raise QgsProcessingException(f"[{tag}] line-to-polygon result is invalid/empty after cleanup")
        return poly_lyr

    # Case 3: point -> tiny buffer polygon
    if gtype == QgsWkbTypes.PointGeometry:
        poly = _run(
            "native:buffer",
            {
                "INPUT": lyr,
                "DISTANCE": tiny,
                "SEGMENTS": 8,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2.0,
                "DISSOLVE": False,
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]

        try:
            poly = _run(
                "native:fixgeometries",
                {"INPUT": poly, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
        except Exception:
            pass

        poly = _force_2d_safe(poly, context, feedback)
        poly_lyr = _usable_polygon(poly, f"{tag}:point_buffer")
        if poly_lyr is None:
            raise QgsProcessingException(f"[{tag}] point-to-polygon result is invalid/empty")
        return poly_lyr

    raise QgsProcessingException(f"[{tag}] unsupported geometry type for polygon conversion")

def _points_from_polys_safe(poly_layer, context, feedback, tag="um"):
    """
    Create a point layer (1 point per polygon) robustly.
    Prevents: 'Could not add feature with geometry type MultiPolygon to layer of type Point'
    by enforcing polygon-only + singleparts + valid geoms, then using fallback methods.
    """
    # Enforce polygon-only + valid + 2D
    p = _polys_only(poly_layer, context, feedback)
    p = _run(
        "native:multiparttosingleparts",
        {"INPUT": p, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    p = _run(
        "native:fixgeometries",
        {"INPUT": p, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    p = _force_2d_safe(p, context, feedback)

    # Try native:pointonsurface first
    try:
        pts = _run(
            "native:pointonsurface",
            {"INPUT": p, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        pts = _as_layer(pts, context) or pts
        return pts
    except Exception as e:
        if feedback:
            feedback.reportError(f"[{tag}] pointonsurface failed; trying geometrybyexpression. ({e})")

    # Fallback: geometrybyexpression using point_on_surface($geometry)
    if _algo_exists("native:geometrybyexpression"):
        try:
            pts = _run(
                "native:geometrybyexpression",
                {
                    "INPUT": p,
                    "EXPRESSION": "point_on_surface($geometry)",
                    "OUTPUT_GEOMETRY": 1,   # Point
                    "WITH_M": False,
                    "WITH_Z": False,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            pts = _as_layer(pts, context) or pts
            return pts
        except Exception as e:
            if feedback:
                feedback.reportError(f"[{tag}] geometrybyexpression failed; trying centroids. ({e})")

    # Last fallback: centroids (may fall outside polygon, but won’t crash)
    for alg in ("native:centroids", "qgis:centroids"):
        if _algo_exists(alg):
            try:
                pts = _run(
                    alg,
                    {"INPUT": p, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                pts = _as_layer(pts, context) or pts
                return pts
            except Exception as e:
                if feedback:
                    feedback.reportError(f"[{tag}] {alg} failed: {e}")

    raise QgsProcessingException(f"[{tag}] Could not generate point layer from polygons.")


def _fix_geoms(layer, context, feedback=None):
    """
    Conservative geometry cleaning.

    For most workflows:
      1) fixgeometries
      2) if that empties/breaks the layer, fall back to original
      3) optionally force 2D / drop MZ
    Does NOT use buffer(0), because that can destroy valid polygons.
    """
    lyr_in = _as_layer(layer, context) or layer
    if lyr_in is None or not lyr_in.isValid():
        if feedback:
            feedback.reportError("[fix] input not a valid layer; returning as-is.")
        return lyr_in

    # PURPOSE: Confirm a repaired layer remains valid and contains features.
    def _usable(lyr):
        lyr = _as_layer(lyr, context) or lyr
        if lyr is None or not lyr.isValid():
            return None
        try:
            if lyr.featureCount() == 0:
                return None
        except Exception:
            return None
        return lyr

    orig = lyr_in

    # Step 1: fixgeometries
    try:
        fixed = _run(
            "native:fixgeometries",
            {"INPUT": orig, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        fixed = _as_layer(fixed, context) or fixed
    except Exception as e:
        if feedback:
            feedback.reportError(f"[fix] fixgeometries failed: {e}")
        fixed = orig

    if _usable(fixed) is None:
        if feedback:
            feedback.reportError("[fix] fixgeometries emptied/broke layer; using original")
        fixed = orig

    # Step 2: optional makevalid, but only keep it if non-empty
    if _algo_exists("native:makevalid"):
        try:
            mv = _run(
                "native:makevalid",
                {"INPUT": fixed, "METHOD": 0, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            mv = _as_layer(mv, context) or mv
            if _usable(mv) is not None:
                fixed = mv
            elif feedback:
                feedback.reportError("[fix] makevalid emptied/broke layer; keeping previous result")
        except Exception as e:
            if feedback:
                feedback.reportError(f"[fix] makevalid failed: {e}")

    # Step 3: force 2D / drop MZ, but again keep previous if it breaks
    fixed2d = fixed

    for alg in ("native:force2d", "qgis:force2d"):
        if _algo_exists(alg):
            try:
                out = _run(
                    alg,
                    {"INPUT": fixed2d, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                out = _as_layer(out, context) or out
                if _usable(out) is not None:
                    fixed2d = out
                elif feedback:
                    feedback.reportError(f"[fix] {alg} emptied/broke layer; keeping previous result")
                break
            except Exception:
                pass
    else:
        for alg in ("native:dropmz", "qgis:dropmz"):
            if _algo_exists(alg):
                try:
                    out = _run(
                        alg,
                        {"INPUT": fixed2d, "DROP_M": True, "DROP_Z": True, "OUTPUT": "TEMPORARY_OUTPUT"},
                        context, feedback
                    )["OUTPUT"]
                    out = _as_layer(out, context) or out
                    if _usable(out) is not None:
                        fixed2d = out
                    elif feedback:
                        feedback.reportError(f"[fix] {alg} emptied/broke layer; keeping previous result")
                    break
                except Exception:
                    pass

    return _as_layer(fixed2d, context) or fixed2d

def _safe_polygon_difference(A, B, context, feedback, tag="diff", snap_grid=None, min_area=1.0):
    """
    Robust polygon difference A - B.

    - Ensures usable polygon inputs
    - Fixes geometries and forces 2D
    - Optionally uses GRID_SIZE
    - Filters output to polygons only
    - Removes tiny slivers

    Returns a TEMP output suitable for _as_layer().
    Raises on invalid/empty critical inputs.
    """

    A2 = _ensure_polygon(A, context, feedback, f"{tag}:A")
    B2 = _ensure_polygon(B, context, feedback, f"{tag}:B")

    A2 = _as_layer(A2, context) or A2
    B2 = _as_layer(B2, context) or B2

    if A2 is None or not A2.isValid() or A2.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] A invalid/empty after polygon prep")
    if B2 is None or not B2.isValid() or B2.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] B invalid/empty after polygon prep")

    params = {
        "INPUT": A2,
        "OVERLAY": B2,
        "OUTPUT": "TEMPORARY_OUTPUT"
    }
    if snap_grid is not None:
        params["GRID_SIZE"] = float(snap_grid)

    try:
        out = _run("native:difference", params, context, feedback)["OUTPUT"]
    except Exception as e:
        if snap_grid is not None:
            if feedback:
                feedback.reportError(
                    f"[{tag}] difference with GRID_SIZE failed; retrying without GRID_SIZE. Error: {e}"
                )
            out = _run(
                "native:difference",
                {"INPUT": A2, "OVERLAY": B2, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
        else:
            raise QgsProcessingException(f"[{tag}] native:difference failed: {e}")

    out = _run(
        "native:extractbyexpression",
        {
            "INPUT": out,
            "EXPRESSION": "geometry_type($geometry) IN ('Polygon','MultiPolygon')",
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]

    out = _force_2d_safe(_fix_geoms(out, context, feedback), context, feedback)

    out_lyr = _as_layer(out, context) or out
    if out_lyr is None or not out_lyr.isValid():
        raise QgsProcessingException(f"[{tag}] invalid output after difference cleanup")

    try:
        out = _drop_null_tiny_polys(out, float(min_area), context, feedback)
    except Exception as e:
        if feedback:
            feedback.reportError(f"[{tag}] sliver cull failed, keeping unclipped output. Error: {e}")

    out_lyr = _as_layer(out, context) or out
    if out_lyr is None or not out_lyr.isValid():
        raise QgsProcessingException(f"[{tag}] invalid output after sliver cull")

    if feedback:
        feedback.pushInfo(
            f"[{tag}] difference OK: fc={out_lyr.featureCount()} "
            f"geom={QgsWkbTypes.displayString(out_lyr.wkbType())}"
        )

    return out

def _planarize_and_assign_by_max_overlap(env_union, ea_polys, context, feedback, S,
                                         period_end_fmt, tag="planarize"):
    """
    Planarize EA polygons against env_union and assign each planar cell
    to the source polygon with maximum overlap.

    IMPORTANT:
      - preserves EA + PeriodEnd + IN_CORR + all y_* / T_* fields
      - does NOT collapse everything to EA-only
      - fallback fill is conservative
    """
    env_union = _ensure_layer(env_union, context, feedback, tag=f"{tag}:env_union")
    ea_polys  = _ensure_layer(ea_polys,  context, feedback, tag=f"{tag}:ea_polys")

    ea_polys = _safe_clip(ea_polys, env_union, context, feedback)
    ea_polys = _polys_only(ea_polys, context, feedback)
    ea_polys = _drop_null_tiny_polys(ea_polys, S["min_area"] * 0.001, context, feedback)
    ea_polys = _as_layer(ea_polys, context) or ea_polys

    if ea_polys is None or not ea_polys.isValid() or ea_polys.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] ea_polys empty after clip/polygon cleanup")

    # ------------------------------------------------------------------
    # Ensure fields that must survive planarization
    # ------------------------------------------------------------------
    keep_fields = []
    for fn in ea_polys.fields().names():
        fnl = fn.lower()
        if fn in ("EA", "PeriodEnd", "IN_CORR") or fn.startswith("y_") or fn.startswith("T_"):
            keep_fields.append(fn)

    if "EA" not in keep_fields:
        ea_polys = _ensure_text_field(ea_polys, "EA", context, feedback, 32)
        keep_fields.append("EA")

    if "PeriodEnd" not in keep_fields:
        ea_polys = _ensure_text_field(ea_polys, "PeriodEnd", context, feedback, 32)
        keep_fields.append("PeriodEnd")

    if "IN_CORR" not in keep_fields:
        ea_polys = _run(
            "native:fieldcalculator",
            {
                "INPUT": ea_polys,
                "FIELD_NAME": "IN_CORR",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 1,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "0",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        ea_polys = _as_layer(ea_polys, context) or ea_polys
        keep_fields.append("IN_CORR")

    # stable source ID for overlap lookup
    if ea_polys.fields().indexOf("SRC_ID") == -1:
        ea_polys = _run(
            "native:fieldcalculator",
            {
                "INPUT": ea_polys,
                "FIELD_NAME": "SRC_ID",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 18,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "$id",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        ea_polys = _as_layer(ea_polys, context) or ea_polys

    # ------------------------------------------------------------------
    # Build planar cells from boundaries
    # ------------------------------------------------------------------
    b_env = _run(
        "native:boundary",
        {"INPUT": env_union, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    b_ea = _run(
        "native:boundary",
        {"INPUT": ea_polys, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    local_crs_obj = None
    for candidate in (env_union, ea_polys, b_env, b_ea):
        lyr = _as_layer(candidate, context)
        if lyr and lyr.isValid() and lyr.crs().isValid():
            local_crs_obj = lyr.crs()
            break

    b_all = _run(
        "native:mergevectorlayers",
        {
            "LAYERS": [b_env, b_ea],
            "CRS": local_crs_obj if local_crs_obj and local_crs_obj.isValid() else None,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    b_all = _fix_geoms(b_all, context, feedback)

    cells = _run(
        "native:polygonize",
        {"INPUT": b_all, "KEEP_FIELDS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    cells = _safe_clip(cells, env_union, context, feedback)
    cells = _polys_only(cells, context, feedback)
    cells = _drop_null_tiny_polys(cells, S["min_area"] * 0.001, context, feedback)

    cells_lyr = _as_layer(cells, context) or cells
    if cells_lyr is None or not cells_lyr.isValid() or cells_lyr.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] planar cells empty after polygonize/clip")

    cells = _run(
        "native:fieldcalculator",
        {
            "INPUT": cells,
            "FIELD_NAME": "CELLID",
            "FIELD_TYPE": 1,
            "FIELD_LENGTH": 18,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": True,
            "FORMULA": "$id",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    # ------------------------------------------------------------------
    # Intersect planar cells with source EA polygons, preserving needed fields
    # ------------------------------------------------------------------
    overlay_fields = ["SRC_ID"] + [f for f in keep_fields if f != "SRC_ID"]

    inter = _run(
        "native:intersection",
        {
            "INPUT": cells,
            "OVERLAY": ea_polys,
            "INPUT_FIELDS": ["CELLID"],
            "OVERLAY_FIELDS": overlay_fields,
            "OVERLAY_FIELDS_PREFIX": "SRC_",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    inter = _run(
        "native:fieldcalculator",
        {
            "INPUT": inter,
            "FIELD_NAME": "ovA",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 6,
            "NEW_FIELD": True,
            "FORMULA": "$area",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    inter_lyr = _as_layer(inter, context) or inter
    if inter_lyr is None or not inter_lyr.isValid() or inter_lyr.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] planar intersection empty")

    # ------------------------------------------------------------------
    # Best-overlap lookup per CELLID
    # ------------------------------------------------------------------
    best = {}
    for f in inter_lyr.getFeatures():
        cid = f["CELLID"]
        a = float(f["ovA"] or 0.0)
        if cid is None:
            continue
        if cid not in best or a > best[cid]["ovA"]:
            rec = {"ovA": a}
            for fld in keep_fields:
                rec[fld] = f[f"SRC_{fld}"] if f.fields().indexOf(f"SRC_{fld}") != -1 else None
            best[cid] = rec

    # ------------------------------------------------------------------
    # Save cells, reload, add target fields, assign values
    # ------------------------------------------------------------------
    out_path = QgsProcessingUtils.generateTempFilename(f"{tag}_cells.gpkg")
    _run("native:savefeatures", {"INPUT": cells, "OUTPUT": out_path}, context, feedback)

    out_lyr = _as_layer(out_path, context)
    if out_lyr is None or not out_lyr.isValid():
        raise QgsProcessingException(f"[{tag}] failed to reload planar cells: {out_path}")

    # Ensure all required fields exist on output
    for fld in keep_fields:
        if fld == "IN_CORR":
            if out_lyr.fields().indexOf(fld) == -1:
                out_lyr = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": out_lyr,
                        "FIELD_NAME": fld,
                        "FIELD_TYPE": 1,
                        "FIELD_LENGTH": 1,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": True,
                        "FORMULA": "0",
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                out_lyr = _as_layer(out_lyr, context) or out_lyr
        else:
            out_lyr = _ensure_text_field(out_lyr, fld, context, feedback, 32)
            out_lyr = _as_layer(out_lyr, context) or out_lyr

    field_idx = {f.name(): i for i, f in enumerate(out_lyr.fields())}

    if not out_lyr.startEditing():
        raise QgsProcessingException(f"[{tag}] failed to start editing planar cells")

    for f in out_lyr.getFeatures():
        cid = f["CELLID"]

        if cid in best:
            rec = best[cid]
            for fld in keep_fields:
                if fld in field_idx:
                    val = rec.get(fld)
                    if fld == "IN_CORR":
                        out_lyr.changeAttributeValue(f.id(), field_idx[fld], 0 if val is None else val)
                    else:
                        out_lyr.changeAttributeValue(f.id(), field_idx[fld], "" if val is None else val)
        else:
            # conservative fallback
            if "EA" in field_idx:
                out_lyr.changeAttributeValue(f.id(), field_idx["EA"], "stable_floodplain")
            if "PeriodEnd" in field_idx:
                out_lyr.changeAttributeValue(f.id(), field_idx["PeriodEnd"], period_end_fmt)
            if "IN_CORR" in field_idx:
                out_lyr.changeAttributeValue(f.id(), field_idx["IN_CORR"], 0)

    if not out_lyr.commitChanges():
        raise QgsProcessingException(f"[{tag}] failed to commit planar cell assignments")

    out_final = _fix_geoms(out_lyr, context, feedback)
    out_final = _force_2d_safe(out_final, context, feedback)
    out_final = _polys_only(out_final, context, feedback)
    out_final = _drop_null_tiny_polys(out_final, S["min_area"] * 0.001, context, feedback)

    return out_final

# PURPOSE: Create an empty text attribute when absent; preserve the existing field when present.
def _ensure_text_field(layer, name, context, feedback=None, length=32):
    lyr = _as_layer(layer, context, feedback) or layer
    lyr = _ensure_layer(lyr, context, feedback, tag=f"ensure_text_field:{name}")

    if lyr.fields().indexOf(name) != -1:
        return lyr

    out = _run(
        "native:fieldcalculator",
        {
            "INPUT": lyr,
            "FIELD_NAME": name,
            "FIELD_TYPE": 2,  # string
            "FIELD_LENGTH": int(length),
            "FIELD_PRECISION": 0,
            "NEW_FIELD": True,
            "FORMULA": "''",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    return out

# PURPOSE: Delete an optional helper column without failing if it is already absent.
def _delete_field_if_exists(layer, field_name, context, feedback=None):
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        return lyr

    if lyr.fields().indexOf(field_name) == -1:
        return lyr

    try:
        out = _run(
            "native:deletecolumn",
            {
                "INPUT": lyr,
                "COLUMN": [field_name],
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]
        return _as_layer(out, context) or lyr
    except Exception as e:
        if feedback:
            feedback.reportError(f"[delete_field_if_exists] failed for {field_name}: {e}")
        return lyr
    

def _drop_null_tiny_polys(layer, min_area, context, feedback=None):
    """
    Remove:
      - null geometries
      - empty geometries
      - non-polygon geometries
      - polygons with area <= min_area

    Conservative behavior:
      - if filtering empties the layer, return the original layer
      - intended for already-sane polygon layers, not geometry repair
    """
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        return lyr

    expr = (
        "$geometry IS NOT NULL AND "
        "NOT is_empty($geometry) AND "
        "geometry_type($geometry) IN ('Polygon','MultiPolygon') AND "
        f"$area > {float(min_area)}"
    )

    try:
        out = _run(
            "native:extractbyexpression",
            {
                "INPUT": lyr,
                "EXPRESSION": expr,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        out_lyr = _as_layer(out, context) or out
        if out_lyr is None or not out_lyr.isValid():
            if feedback:
                feedback.reportError("[drop_null_tiny] filtered layer invalid; returning original.")
            return lyr

        if out_lyr.featureCount() == 0:
            if feedback:
                feedback.reportError(
                    f"[drop_null_tiny] filtering emptied layer (min_area={min_area}); returning original."
                )
            return lyr

        return out_lyr

    except Exception as e:
        if feedback:
            feedback.reportError(f"[drop_null_tiny] failed ({e}); layer passed unchanged.")
        return lyr

# PURPOSE: Derive width-dependent snap/grid, buffer, minimum-area and extension tolerances in map units.
def _scale_params(channel_width):
    w = float(channel_width or 0.0)
    if w <= 0:
        w = 50.0  # safe fallback (≈ small–medium river)

    tol = max(0.05, w * 0.01)

    return {
        "snap":     tol,
        "grid":     tol,
        "buffer":   max(0.10, w * 0.05),
        "min_area": max(2.0, 0.02 * w * w),
        "side":     max(2.0, w * 0.5),
        "extend":   max(10.0, w * 2.0),
    }




def _snap_to_grid(layer, grid_size, context=None, feedback=None):
    """
    Snap geometries to a uniform grid to stabilize topology and help
    intersection/union succeed.
    Strategy:
      - Prefer native:snap or native:snapgeometries if available.
      - Fallback to native:roundgeometry to reduce coord precision.
    """
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        if feedback:
            feedback.reportError("[snap_to_grid] Invalid layer")
        return layer

    try:
        # Preferred snap algorithm (depending on version)
        alg = "native:snap" if _algo_exists("native:snap") else "native:snapgeometries"
        out = _run(
            alg,
            {
                "INPUT": lyr,
                "REFERENCE_LAYER": lyr,
                "TOLERANCE": grid_size,
                "BEHAVIOR": 0,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context,
            feedback,
        )["OUTPUT"]
        return _as_layer(out, context) or out
    except Exception:
        # Fallback: round coordinates
        try:
            out = _run(
                "native:roundgeometry",
                {
                    "INPUT": lyr,
                    "DECIMALS": max(0, int(round(-1 * (math.log10(grid_size))))),
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context,
                feedback,
            )["OUTPUT"]
            return _as_layer(out, context) or out
        except Exception as e:
            if feedback:
                feedback.reportError(f"[snap_to_grid] Failed: {e}")
            return lyr


def _safe_union(A, B, grid=0.10, context=None, feedback=None, ref_crs_obj=None, tag="union"):
    """
    Polygon-only union via A\\B + B\\A + A∩B, avoiding native:union line junk.
    'grid' kept only for signature compatibility.
    """

    # PURPOSE: Clean a polygon prior to overlay, falling back conservatively if cleaning empties it.
    def _prep_union_input(x, name):
        lyr = _as_layer(x, context) or x
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"[{tag}:{name}] invalid input")

        gt = QgsWkbTypes.geometryType(lyr.wkbType())
        if gt == QgsWkbTypes.PolygonGeometry and lyr.featureCount() > 0:
            try:
                cleaned = _run(
                    "native:fixgeometries",
                    {"INPUT": lyr, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]
                cleaned = _force_2d_safe(cleaned, context, feedback)
                cleaned_lyr = _as_layer(cleaned, context) or cleaned
                if cleaned_lyr and cleaned_lyr.isValid() and cleaned_lyr.featureCount() > 0:
                    return cleaned_lyr
            except Exception:
                pass

            if feedback:
                feedback.reportError(f"[safe_union] {tag}:{name} cleaned polygon emptied; using original polygon input")
            return lyr

        return _ensure_polygon(lyr, context, feedback, f"{tag}_{name}")

    # PURPOSE: Remove non-polygon overlay artefacts while recording intermediate geometry diagnostics.
    def _polys_only_local(layer, name):
        if feedback:
            feedback.pushInfo(f"[safe_union] {tag}:{name} → enforcing polygon-only")

        out = _run(
            "native:extractbyexpression",
            {
                "INPUT": layer,
                "EXPRESSION": "geometry_type($geometry) IN ('Polygon','MultiPolygon')",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        out = _run(
            "native:fixgeometries",
            {"INPUT": out, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]

        out = _force_2d_safe(out, context, feedback)
        out_lyr = _as_layer(out, context) or out

        if feedback and out_lyr and out_lyr.isValid():
            feedback.pushInfo(
                f"[safe_union] {tag}:{name} fc={out_lyr.featureCount()} "
                f"geom={QgsWkbTypes.displayString(out_lyr.wkbType())}"
            )

        return out

    A0 = _prep_union_input(A, "A")
    B0 = _prep_union_input(B, "B")

    try:
        if feedback:
            feedback.pushInfo(f"[safe_union] polygon-only union via difference+intersection on {tag}")

        A_only = _run(
            "native:difference",
            {"INPUT": A0, "OVERLAY": B0, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        A_only = _polys_only_local(A_only, "A_minus_B")

        B_only = _run(
            "native:difference",
            {"INPUT": B0, "OVERLAY": A0, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        B_only = _polys_only_local(B_only, "B_minus_A")

        Both = _run(
            "native:intersection",
            {
                "INPUT": A0,
                "OVERLAY": B0,
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        Both = _polys_only_local(Both, "A_int_B")

        merge_params = {"LAYERS": [A_only, B_only, Both], "OUTPUT": "TEMPORARY_OUTPUT"}
        if ref_crs_obj is not None and ref_crs_obj.isValid():
            merge_params["CRS"] = ref_crs_obj

        out = _run("native:mergevectorlayers", merge_params, context, feedback)["OUTPUT"]
        out = _polys_only_local(out, "merged")
        out = _strip_pk_fields(out, context, feedback)
        out = _force_2d_safe(out, context, feedback)
        out = _drop_null_tiny_polys(out, 1e-8, context, feedback)

        if not is_empty_layer(out, context, feedback, f"{tag}_union_result"):
            return _as_layer(out, context) or out

        if feedback:
            feedback.reportError(f"[safe_union] union empty for {tag}; falling back to merge→dissolve.")

    except Exception as e:
        if feedback:
            feedback.reportError(f"[safe_union] polygon-only union failed on {tag}: {e}")
            feedback.reportError("[safe_union] Falling back to merge→dissolve (attribute-blind).")

    merge_params = {"LAYERS": [A0, B0], "OUTPUT": "TEMPORARY_OUTPUT"}
    if ref_crs_obj is not None and ref_crs_obj.isValid():
        merge_params["CRS"] = ref_crs_obj

    merged = _run("native:mergevectorlayers", merge_params, context, feedback)["OUTPUT"]

    dissolved = _run(
        "native:dissolve",
        {"INPUT": merged, "FIELD": [], "SEPARATE_DISJOINT": False, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    dissolved = _force_2d_safe(dissolved, context, feedback)
    dissolved = _drop_null_tiny_polys(dissolved, 1e-8, context, feedback)
    return _as_layer(dissolved, context) or dissolved

def _envelope_fallback(A, B, context, feedback=None):
    """
    Build an approximate envelope: merge both layers and dissolve.
    Used as a very last fallback for clipping intersections.
    """
    merged = _merge_layers([A, B], context, feedback)
    return _dissolve_all(merged, context, feedback)


def _area_union_envelope(A, B, context, feedback, crs=None):
    """
    Merge two polygon layers, dissolve, and delete holes to form one outer envelope.
    """
    A_lyr = _as_layer(A, context)
    B_lyr = _as_layer(B, context)

    if A_lyr is None or not A_lyr.isValid():
        raise QgsProcessingException("[_area_union_envelope] A is invalid")
    if B_lyr is None or not B_lyr.isValid():
        raise QgsProcessingException("[_area_union_envelope] B is invalid")

    ref_crs = crs
    if ref_crs is None:
        if A_lyr.crs().isValid():
            ref_crs = A_lyr.crs()
        elif B_lyr.crs().isValid():
            ref_crs = B_lyr.crs()
        else:
            raise QgsProcessingException("[_area_union_envelope] Could not determine CRS from inputs")

    if not A_lyr.crs().isValid():
        A_lyr.setCrs(ref_crs)
        feedback.pushInfo(f"[_area_union_envelope] Assigned missing CRS to A: {ref_crs.authid()}")
    if not B_lyr.crs().isValid():
        B_lyr.setCrs(ref_crs)
        feedback.pushInfo(f"[_area_union_envelope] Assigned missing CRS to B: {ref_crs.authid()}")

    if A_lyr.crs() != ref_crs or B_lyr.crs() != ref_crs:
        raise QgsProcessingException(
            f"[_area_union_envelope] CRS mismatch: "
            f"A={A_lyr.crs().authid()} B={B_lyr.crs().authid()} ref={ref_crs.authid()}"
        )

    merged = _run(
        "native:mergevectorlayers",
        {
            "LAYERS": [A_lyr, B_lyr],
            "CRS": ref_crs,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    dissolved = _run(
        "native:dissolve",
        {
            "INPUT": merged,
            "FIELD": [],
            "SEPARATE_DISJOINT": False,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    env = _run(
        "native:deleteholes",
        {
            "INPUT": dissolved,
            "MIN_AREA": 0.0,
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    env = _as_layer(env, context) or env
    return env

def _ensure_string_field(layer, name, context, feedback, length=32):
    """
    Ensure that a string field named 'name' exists.
    If it doesn't, create it with given length and NULL default.
    Returns layer ID or object.
    """
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        return lyr
    if lyr.fields().indexOf(name) != -1:
        return lyr

    return _run(
        "native:fieldcalculator",
        {
            "INPUT": lyr,
            "FIELD_NAME": name,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": length,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": True,
            "FORMULA": "NULL",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

def _prep_geom(layer, context, feedback):
    """
    Geometry-only cleanup: fix + force2d.
    No filtering by area.
    """
    lyr = _fix_geoms(layer, context, feedback)
    lyr = _force_2d_safe(lyr, context, feedback)
    return lyr


# PURPOSE: Apply conservative geometry repair and optional minimum-area filtering.
def _prep_poly(layer, context, feedback, min_area=1e-8):
    lyr = _fix_geoms(layer, context, feedback)
    lyr = _force_2d_safe(lyr, context, feedback)
    if min_area is None:
        return lyr  # ✅ no tiny/sliver filtering at all
    return _drop_null_tiny_polys(lyr, min_area, context, feedback)


def _dissolved_footprint(layer, context, feedback):
    """
    Dissolved polygon footprint of a layer (safer overlay for difference/gap logic).
    """
    fp = _run(
        "native:dissolve",
        {"INPUT": layer, "FIELD": [], "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    return _prep_poly(fp, context, feedback, min_area=None)


def _gapfill_within_env(working, env_union, y1, y2, context, feedback, min_area):
    """
    FINAL conservative gap-fill:
      BG = env_union - dissolve(working)
      tag BG as stable_floodplain with y_/T_ fields present
      merge BG back into working only if BG exists
      if no BG exists, return working unchanged
      avoid destructive cleanup at this late stage

    Notes:
      - This function is intentionally conservative.
      - It should only fill genuine residual gaps, not reinterpret the EA result.
      - It avoids re-clipping/re-cleaning the no-gap case, because that was
        collapsing valid EA outputs before dissolve/write.
    """

    # PURPOSE: Safely report a feature count without allowing logging to interrupt processing.
    def _fc(obj):
        try:
            lyr = _as_layer(obj, context) or obj
            return lyr.featureCount() if lyr and lyr.isValid() else -1
        except Exception:
            return -1

    # PURPOSE: Check layer validity and non-emptiness before committing a fallback.
    def _is_valid_nonempty(obj):
        try:
            lyr = _as_layer(obj, context) or obj
            return lyr is not None and lyr.isValid() and lyr.featureCount() > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Resolve inputs and keep originals as fallback
    # ------------------------------------------------------------------
    working_in = _as_layer(working, context) or working
    env_in = _as_layer(env_union, context) or env_union

    if working_in is None or not working_in.isValid():
        if feedback:
            feedback.reportError("[GAPFILL] Input working layer invalid; returning as-is.")
        return working

    if env_in is None or not env_in.isValid():
        if feedback:
            feedback.reportError("[GAPFILL] Input env_union invalid; returning working unchanged.")
        return working_in

    if feedback:
        feedback.pushInfo(
            f"[GAPFILL] start: working_fc={_fc(working_in)} env_fc={_fc(env_in)}"
        )

    # ------------------------------------------------------------------
    # Prepare only for boolean ops; DO NOT use morphology min_area here
    # ------------------------------------------------------------------
    try:
        env_clean = _prep_poly(env_in, context, feedback, min_area=None)
    except Exception:
        env_clean = env_in

    try:
        working_clean = _prep_poly(working_in, context, feedback, min_area=None)
    except Exception:
        working_clean = working_in

    env_clean = _as_layer(env_clean, context) or env_clean
    working_clean = _as_layer(working_clean, context) or working_clean

    if not _is_valid_nonempty(working_clean):
        if feedback:
            feedback.reportError(
                f"[GAPFILL] working became invalid/empty during prep; using original working (fc={_fc(working_in)})."
            )
        working_clean = working_in

    if not _is_valid_nonempty(env_clean):
        if feedback:
            feedback.reportError("[GAPFILL] env_union became invalid/empty during prep; returning original working.")
        return working_in

    # ------------------------------------------------------------------
    # Build footprint of working
    # ------------------------------------------------------------------
    try:
        work_fp = _dissolved_footprint(working_clean, context, feedback)
        work_fp = _prep_poly(work_fp, context, feedback, min_area=None)
        work_fp = _as_layer(work_fp, context) or work_fp
    except Exception as e:
        if feedback:
            feedback.reportError(f"[GAPFILL] Could not build working footprint; returning working unchanged. ({e})")
        return working_in

    if not _is_valid_nonempty(work_fp):
        if feedback:
            feedback.reportError("[GAPFILL] Working footprint invalid/empty; returning working unchanged.")
        return working_in

    # ------------------------------------------------------------------
    # BG = env_union - footprint(working)
    # ------------------------------------------------------------------
    try:
        bg = _run(
            "native:difference",
            {"INPUT": env_clean, "OVERLAY": work_fp, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        bg = _prep_poly(bg, context, feedback, min_area=None)
        bg = _as_layer(bg, context) or bg
    except Exception as e:
        if feedback:
            feedback.reportError(f"[GAPFILL] Difference failed; returning working unchanged. ({e})")
        return working_in

    # ------------------------------------------------------------------
    # No BG: do absolutely nothing destructive
    # ------------------------------------------------------------------
    if not _is_valid_nonempty(bg):
        if feedback:
            feedback.pushInfo(
                f"[GAPFILL] BG=0 (no gaps); returning working unchanged (fc={_fc(working_in)})."
            )
        return working_in

    # ------------------------------------------------------------------
    # Optional: keep only small residual gaps.
    # This prevents large blanket fills from relabelling the active domain.
    # ------------------------------------------------------------------
    bg_small = bg
    try:
        if min_area is not None:
            # Keep only genuinely small residuals; not large domain chunks.
            bg_max_area = max(float(min_area) * 0.001, 1.0)
            bg_small = _run(
                "native:extractbyexpression",
                {
                    "INPUT": bg,
                    "EXPRESSION": f"$area <= {bg_max_area}",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            bg_small = _as_layer(bg_small, context) or bg_small

            if feedback:
                feedback.pushInfo(
                    f"[GAPFILL] BG residuals: raw={_fc(bg)} kept_small={_fc(bg_small)} max_area={bg_max_area}"
                )
    except Exception as e:
        if feedback:
            feedback.reportError(f"[GAPFILL] Small-gap filter failed; using raw BG. ({e})")
        bg_small = bg

    if not _is_valid_nonempty(bg_small):
        if feedback:
            feedback.pushInfo(
                f"[GAPFILL] BG exists but no small residuals kept; returning working unchanged (fc={_fc(working_in)})."
            )
        return working_in

    # ------------------------------------------------------------------
    # Tag BG as stable_floodplain
    # ------------------------------------------------------------------
    try:
        bg_small = _run(
            "native:fieldcalculator",
            {
                "INPUT": bg_small,
                "FIELD_NAME": "EA",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "'stable_floodplain'",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        bg_small = _run(
            "native:fieldcalculator",
            {
                "INPUT": bg_small,
                "FIELD_NAME": "IN_CORR",
                "FIELD_TYPE": 1,
                "FIELD_LENGTH": 1,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": "0",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        for yy in (y1, y2):
            bg_small = _run(
                "native:fieldcalculator",
                {
                    "INPUT": bg_small,
                    "FIELD_NAME": f"y_{yy}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": f"'{yy}'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            bg_small = _run(
                "native:fieldcalculator",
                {
                    "INPUT": bg_small,
                    "FIELD_NAME": f"T_{yy}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "'floodplain'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

        bg_small = _prep_poly(bg_small, context, feedback, min_area=None)
        bg_small = _as_layer(bg_small, context) or bg_small

    except Exception as e:
        if feedback:
            feedback.reportError(f"[GAPFILL] BG tagging failed; returning working unchanged. ({e})")
        return working_in

    if not _is_valid_nonempty(bg_small):
        if feedback:
            feedback.pushInfo("[GAPFILL] Tagged BG became empty; returning working unchanged.")
        return working_in

    # ------------------------------------------------------------------
    # Merge BG back into working
    # ------------------------------------------------------------------
    try:
        work_crs = (_as_layer(working_in, context) or working_in).crs()

        merged = _run(
            "native:mergevectorlayers",
            {
                "LAYERS": [working_in, bg_small],
                "CRS": work_crs,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        merged = _as_layer(merged, context) or merged

    except Exception as e:
        if feedback:
            feedback.reportError(f"[GAPFILL] Merge failed; returning working unchanged. ({e})")
        return working_in

    if not _is_valid_nonempty(merged):
        if feedback:
            feedback.reportError("[GAPFILL] Merged working+BG is empty; returning original working.")
        return working_in

    # ------------------------------------------------------------------
    # Very light final cleanup only.
    # Do NOT clip and do NOT apply large min_area here.
    # ------------------------------------------------------------------
    try:
        merged_clean = _prep_poly(merged, context, feedback, min_area=None)
        merged_clean = _as_layer(merged_clean, context) or merged_clean

        if _is_valid_nonempty(merged_clean):
            merged = merged_clean
    except Exception:
        pass

    if feedback:
        feedback.pushInfo(
            f"[GAPFILL] BG={_fc(bg_small)} merged; working_out={_fc(merged)}"
        )

    return merged
def _retag_by_max_overlap_for_year(union_layer, src_layer, yy, context, feedback):
    """
    Fill remaining NULL y_/T_ tags on union_layer for one date using
    max-area overlap against the tagged source layer for that date.
    Requires union_layer to have a stable integer RID field.
    """
    u = _as_layer(union_layer, context) or union_layer
    s = _as_layer(src_layer, context) or src_layer
    if u is None or not u.isValid() or s is None or not s.isValid():
        return union_layer

    yfld = f"y_{yy}"
    tfld = f"T_{yy}"

    # only polygons still missing tags for this year
    nulls = _run(
        "native:extractbyexpression",
        {
            "INPUT": u,
            "EXPRESSION": (
                f"\"{yfld}\" IS NULL OR trim(to_string(\"{yfld}\")) = '' OR "
                f"\"{tfld}\" IS NULL OR trim(to_string(\"{tfld}\")) = ''"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    nulls = _as_layer(nulls, context) or nulls
    if nulls is None or not nulls.isValid() or nulls.featureCount() == 0:
        return union_layer

    # intersect null polygons with source polygons
    ov = _run(
        "native:intersection",
        {
            "INPUT": nulls,
            "OVERLAY": s,
            "INPUT_FIELDS": ["RID"],
            "OVERLAY_FIELDS": [yfld, tfld],
            "OVERLAY_FIELDS_PREFIX": "SRC_",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    ov = _as_layer(ov, context) or ov
    if ov is None or not ov.isValid() or ov.featureCount() == 0:
        feedback.pushInfo(f"[RETAG overlap] no overlaps found for year {yy}")
        return union_layer

    # add overlap area
    ov = _run(
        "native:fieldcalculator",
        {
            "INPUT": ov,
            "FIELD_NAME": "OV_A",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 24,
            "FIELD_PRECISION": 6,
            "NEW_FIELD": True,
            "FORMULA": "$area",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]
    ov = _as_layer(ov, context) or ov

    # keep max-overlap record per RID
    best_by_rid = {}
    for f in ov.getFeatures():
        rid = f["RID"]
        a = float(f["OV_A"]) if f["OV_A"] is not None else -1.0
        if rid not in best_by_rid or a > best_by_rid[rid][0]:
            best_by_rid[rid] = (a, f[f"SRC_{yfld}"], f[f"SRC_{tfld}"])

    # make lookup table layer in memory
    crs_authid = u.crs().authid() if u.crs().isValid() else "EPSG:4326"
    lut = QgsVectorLayer(f"None?field=RID:integer&field=J2_Y:string(32)&field=J2_T:string(32)&crs={crs_authid}", "lut", "memory")
    pr = lut.dataProvider()

    feats = []
    for rid, (_, jy, jt) in best_by_rid.items():
        nf = QgsFeature(lut.fields())
        nf["RID"] = int(rid)
        nf["J2_Y"] = "" if jy is None else str(jy)
        nf["J2_T"] = "" if jt is None else str(jt)
        feats.append(nf)
    pr.addFeatures(feats)
    lut.updateFields()

    # join lookup back to union layer
    joined = _run(
        "native:joinattributestable",
        {
            "INPUT": u,
            "FIELD": "RID",
            "INPUT_2": lut,
            "FIELD_2": "RID",
            "FIELDS_TO_COPY": ["J2_Y", "J2_T"],
            "METHOD": 1,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    # fill only missing values
    joined = _run(
        "native:fieldcalculator",
        {
            "INPUT": joined,
            "FIELD_NAME": yfld,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN \"{yfld}\" IS NULL OR trim(to_string(\"{yfld}\")) = '' "
                f"THEN coalesce(\"J2_Y\", \"{yfld}\") "
                f"ELSE \"{yfld}\" END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    joined = _run(
        "native:fieldcalculator",
        {
            "INPUT": joined,
            "FIELD_NAME": tfld,
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 32,
            "FIELD_PRECISION": 0,
            "NEW_FIELD": False,
            "FORMULA": (
                f"CASE "
                f"WHEN \"{tfld}\" IS NULL OR trim(to_string(\"{tfld}\")) = '' "
                f"THEN coalesce(\"J2_T\", \"{tfld}\") "
                f"ELSE \"{tfld}\" END"
            ),
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    joined = _run(
        "native:deletecolumn",
        {
            "INPUT": joined,
            "COLUMN": ["J2_Y", "J2_T"],
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context, feedback
    )["OUTPUT"]

    return joined

def _retag_union_by_dates_only_nulls(unionEA, src_old, y_old, src_yng, y_yng, context, feedback):
    """
    Retag unionEA for EA classification without clobbering existing values.

    Fill ONLY missing y_/T_ fields on unionEA using per-date EA-tagged sources
    (channel + island). Missing means NULL or '' (or whitespace).
    Existing non-empty values are preserved.

    Design:
      • POINT-ON-SURFACE pass first (robust, avoids boundary-touch ambiguity)
      • MAX-OVERLAP pass second for still-missing polygons
      • NO nearest-neighbour fill
      • Remaining nulls are intentionally left null here and should be
        conservatively filled later as floodplain.
    """

    # PURPOSE: Inspect observation-specific source attributes used for state retagging.
    def _dbg_src_fields(label, lyr, yy):
        try:
            lyr = _as_layer(lyr, context) or lyr
            if lyr is None or not lyr.isValid():
                feedback.reportError(f"[DBG retag {label}] invalid")
                return
            fns = lyr.fields().names()
            feedback.pushInfo(f"[DBG retag {label}] year={yy} fields={fns}")
            feedback.pushInfo(
                f"[DBG retag {label}] has y/T for {yy}? "
                f"y={f'y_{yy}' in fns} T={f'T_{yy}' in fns}"
            )
        except Exception as e:
            feedback.reportError(f"[DBG retag {label}] failed: {e}")

    # PURPOSE: Generate a filter for records lacking either a date tag or a surface-type tag.
    def _missing_expr(yy):
        return (
            f"\"y_{yy}\" IS NULL OR trim(to_string(\"y_{yy}\")) = '' OR "
            f"\"T_{yy}\" IS NULL OR trim(to_string(\"T_{yy}\")) = ''"
        )

    def _prep_src(src_layer, yy, label):
        """
        Keep only polygons and create stable join helper fields:
          J_Y, J_T
        """
        src = _as_layer(src_layer, context) or src_layer
        if src is None or not src.isValid():
            raise QgsProcessingException(f"[retag {label}] source invalid for {yy}")

        _dbg_src_fields(label, src, yy)

        src = _polys_only(src, context, feedback)
        src = _force_2d_safe(src, context, feedback)
        src = _drop_null_tiny_polys(src, 1e-6, context, feedback)
        src = _as_layer(src, context) or src

        # Make explicit join fields copied from date-specific fields
        src = _run(
            "native:fieldcalculator",
            {
                "INPUT": src,
                "FIELD_NAME": "J_Y",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": f"coalesce(\"y_{yy}\",'')",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        src = _run(
            "native:fieldcalculator",
            {
                "INPUT": src,
                "FIELD_NAME": "J_T",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": True,
                "FORMULA": f"coalesce(\"T_{yy}\",'')",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        src = _as_layer(src, context) or src
        try:
            fns = src.fields().names()
            feedback.pushInfo(
                f"[DBG retag {label}_prep] year={yy} fields={fns}"
            )
            feedback.pushInfo(
                f"[DBG retag {label}_prep] has y/T/J for {yy}? "
                f"y={f'y_{yy}' in fns} T={f'T_{yy}' in fns} "
                f"J_Y={'J_Y' in fns} J_T={'J_T' in fns}"
            )
        except Exception as e:
            feedback.reportError(f"[DBG retag {label}_prep] failed: {e}")

        return src

    def _join_fill_by_points(u_layer, src_layer, yy, side_idx):
        """
        Fill missing y_/T_ for yy using point-on-surface join against src_layer.
        """
        u = _as_layer(u_layer, context) or u_layer
        src = _as_layer(src_layer, context) or src_layer
        if u is None or not u.isValid():
            raise QgsProcessingException(f"[retag point-pass] union invalid for {yy}")
        if src is None or not src.isValid():
            raise QgsProcessingException(f"[retag point-pass] source invalid for {yy}")

        pts = _run(
            "native:pointonsurface",
            {"INPUT": u, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]

        pts_join = _run(
            "native:joinattributesbylocation",
            {
                "INPUT": pts,
                "JOIN": src,
                "PREDICATE": [0],  # intersects
                "JOIN_FIELDS": ["J_Y", "J_T"],
                "METHOD": 0,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        # diagnostic: how many points actually got helper values
        try:
            matched = _run(
                "native:extractbyexpression",
                {
                    "INPUT": pts_join,
                    "EXPRESSION": "coalesce(\"J_T\",'') <> ''",
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            matched = _as_layer(matched, context)
            feedback.pushInfo(
                f"[DBG] retag join_fill side={side_idx} year={yy}: "
                f"matched_points={matched.featureCount() if matched and matched.isValid() else -1}"
            )
        except Exception as e:
            feedback.reportError(f"[DBG] retag join_fill side={side_idx} year={yy} failed: {e}")

        # stable ID for join-back
        if (_as_layer(pts_join, context) or pts_join).fields().indexOf("RT_ID") == -1:
            pts_join = _run(
                "native:fieldcalculator",
                {
                    "INPUT": pts_join,
                    "FIELD_NAME": "RT_ID",
                    "FIELD_TYPE": 1,
                    "FIELD_LENGTH": 18,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "$id",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

        if (_as_layer(u, context) or u).fields().indexOf("RT_ID") == -1:
            u = _run(
                "native:fieldcalculator",
                {
                    "INPUT": u,
                    "FIELD_NAME": "RT_ID",
                    "FIELD_TYPE": 1,
                    "FIELD_LENGTH": 18,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "$id",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

        u2 = _run(
            "native:joinattributestable",
            {
                "INPUT": u,
                "FIELD": "RT_ID",
                "INPUT_2": pts_join,
                "FIELD_2": "RT_ID",
                "FIELDS_TO_COPY": ["J_Y", "J_T"],
                "METHOD": 1,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        # diagnostic: how many polygons got join helper values
        try:
            tagged = _run(
                "native:extractbyexpression",
                {
                    "INPUT": u2,
                    "EXPRESSION": "coalesce(\"J_T\",'') <> ''",
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            tagged = _as_layer(tagged, context)
            feedback.pushInfo(
                f"[DBG] retag join-back side={side_idx} year={yy}: "
                f"tagged_polygons={tagged.featureCount() if tagged and tagged.isValid() else -1}"
            )
        except Exception as e:
            feedback.reportError(f"[DBG] retag join-back side={side_idx} year={yy} failed: {e}")

        # fill only missing values
        u2 = _run(
            "native:fieldcalculator",
            {
                "INPUT": u2,
                "FIELD_NAME": f"y_{yy}",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"y_{yy}\" IS NULL OR trim(to_string(\"y_{yy}\")) = '' "
                    f"THEN coalesce(\"J_Y\", \"y_{yy}\") "
                    f"ELSE \"y_{yy}\" END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        u2 = _run(
            "native:fieldcalculator",
            {
                "INPUT": u2,
                "FIELD_NAME": f"T_{yy}",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"T_{yy}\" IS NULL OR trim(to_string(\"T_{yy}\")) = '' "
                    f"THEN coalesce(\"J_T\", \"T_{yy}\") "
                    f"ELSE \"T_{yy}\" END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        # clean helpers
        u2 = _run(
            "native:deletecolumn",
            {
                "INPUT": u2,
                "COLUMN": [c for c in ["J_Y", "J_T"] if c in (_as_layer(u2, context) or u2).fields().names()],
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        return u2

    def _fill_by_max_overlap(u_layer, src_layer, yy):
        """
        For polygons still missing tags after point-pass, intersect with source
        polygons and copy the source tag with maximum overlap area.
        """
        u = _as_layer(u_layer, context) or u_layer
        src = _as_layer(src_layer, context) or src_layer
        if u is None or not u.isValid():
            raise QgsProcessingException(f"[retag overlap] union invalid for {yy}")
        if src is None or not src.isValid():
            raise QgsProcessingException(f"[retag overlap] source invalid for {yy}")

        missing = _run(
            "native:extractbyexpression",
            {
                "INPUT": u,
                "EXPRESSION": _missing_expr(yy),
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]
        missing = _as_layer(missing, context) or missing

        if missing is None or not missing.isValid() or missing.featureCount() == 0:
            return u

        # stable ID on missing subset
        if missing.fields().indexOf("RT_ID") == -1:
            missing = _run(
                "native:fieldcalculator",
                {
                    "INPUT": missing,
                    "FIELD_NAME": "RT_ID",
                    "FIELD_TYPE": 1,
                    "FIELD_LENGTH": 18,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "$id",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
        missing = _as_layer(missing, context) or missing

        inter = _run(
            "native:intersection",
            {
                "INPUT": missing,
                "OVERLAY": src,
                "INPUT_FIELDS": ["RT_ID"],
                "OVERLAY_FIELDS": ["J_Y", "J_T"],
                "OVERLAY_FIELDS_PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        inter = _as_layer(inter, context) or inter

        if inter is None or not inter.isValid() or inter.featureCount() == 0:
            return u

        # overlap area
        inter = _run(
            "native:fieldcalculator",
            {
                "INPUT": inter,
                "FIELD_NAME": "OV_A",
                "FIELD_TYPE": 0,
                "FIELD_LENGTH": 20,
                "FIELD_PRECISION": 6,
                "NEW_FIELD": True,
                "FORMULA": "$area",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        inter = _as_layer(inter, context) or inter

        # choose best overlap per RT_ID
        best = {}
        for f in inter.getFeatures():
            rid = f["RT_ID"]
            ova = f["OV_A"] if f["OV_A"] is not None else -1
            if rid not in best or ova > best[rid]["OV_A"]:
                best[rid] = {
                    "OV_A": ova,
                    "J_Y": f["J_Y"],
                    "J_T": f["J_T"],
                }

        # build lookup layer from best matches
        mem = QgsVectorLayer(f"None?field=RT_ID:integer&field=J_Y:string(32)&field=J_T:string(32)", f"best_{yy}", "memory")
        pr = mem.dataProvider()
        feats = []
        for rid, d in best.items():
            ft = QgsFeature(mem.fields())
            ft["RT_ID"] = int(rid)
            ft["J_Y"] = d["J_Y"]
            ft["J_T"] = d["J_T"]
            feats.append(ft)
        pr.addFeatures(feats)
        mem.updateFields()

        u2 = _run(
            "native:joinattributestable",
            {
                "INPUT": u,
                "FIELD": "RT_ID",
                "INPUT_2": mem,
                "FIELD_2": "RT_ID",
                "FIELDS_TO_COPY": ["J_Y", "J_T"],
                "METHOD": 1,
                "DISCARD_NONMATCHING": False,
                "PREFIX": "",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        u2 = _run(
            "native:fieldcalculator",
            {
                "INPUT": u2,
                "FIELD_NAME": f"y_{yy}",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"y_{yy}\" IS NULL OR trim(to_string(\"y_{yy}\")) = '' "
                    f"THEN coalesce(\"J_Y\", \"y_{yy}\") "
                    f"ELSE \"y_{yy}\" END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        u2 = _run(
            "native:fieldcalculator",
            {
                "INPUT": u2,
                "FIELD_NAME": f"T_{yy}",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FIELD_PRECISION": 0,
                "NEW_FIELD": False,
                "FORMULA": (
                    f"CASE "
                    f"WHEN \"T_{yy}\" IS NULL OR trim(to_string(\"T_{yy}\")) = '' "
                    f"THEN coalesce(\"J_T\", \"T_{yy}\") "
                    f"ELSE \"T_{yy}\" END"
                ),
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        u2 = _run(
            "native:deletecolumn",
            {
                "INPUT": u2,
                "COLUMN": [c for c in ["J_Y", "J_T"] if c in (_as_layer(u2, context) or u2).fields().names()],
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]

        feedback.pushInfo(f"[DBG overlap] filled by max overlap for year {yy}: candidates={len(best)}")
        return u2

    # PURPOSE: Report the number of date-specific tags still missing after the retagging passes.
    def _report_missing(label, lyr, yy):
        try:
            miss = _run(
                "native:extractbyexpression",
                {
                    "INPUT": lyr,
                    "EXPRESSION": _missing_expr(yy),
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            miss = _as_layer(miss, context)
            total = (_as_layer(lyr, context) or lyr).featureCount()
            miss_fc = miss.featureCount() if miss and miss.isValid() else -1
            feedback.pushInfo(f"[DBG retag] {label} year={yy}: missing={miss_fc}/{total}")
        except Exception as e:
            feedback.reportError(f"[DBG retag] {label} year={yy} failed: {e}")

    # ------------------------------------------------------------------
    # main
    # ------------------------------------------------------------------
    u = _as_layer(unionEA, context) or unionEA
    if u is None or not u.isValid():
        raise QgsProcessingException("[retag_union] unionEA invalid")

    # ensure the date fields exist on unionEA
    for yy in (y_old, y_yng):
        if (_as_layer(u, context) or u).fields().indexOf(f"y_{yy}") == -1:
            u = _run(
                "native:fieldcalculator",
                {
                    "INPUT": u,
                    "FIELD_NAME": f"y_{yy}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "NULL",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
        if (_as_layer(u, context) or u).fields().indexOf(f"T_{yy}") == -1:
            u = _run(
                "native:fieldcalculator",
                {
                    "INPUT": u,
                    "FIELD_NAME": f"T_{yy}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": "NULL",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

    u = _as_layer(u, context) or u

    S_old = _prep_src(src_old, y_old, "old")
    S_yng = _prep_src(src_yng, y_yng, "yng")

    # point-on-surface pass
    u = _join_fill_by_points(u, S_old, y_old, side_idx=1)
    u = _join_fill_by_points(u, S_yng, y_yng, side_idx=2)

    _report_missing("after point-pass", u, y_old)
    _report_missing("after point-pass", u, y_yng)

    # max-overlap pass
    u = _fill_by_max_overlap(u, S_old, y_old)
    u = _fill_by_max_overlap(u, S_yng, y_yng)

    _report_missing("after overlap-pass", u, y_old)
    _report_missing("after overlap-pass", u, y_yng)

    # IMPORTANT:
    # No nearest-neighbour fill here.
    # Remaining nulls are left intentionally for later conservative
    # floodplain fill in the main processAlgorithm workflow.
    feedback.pushInfo(
        f"[DBG retag] nearest-pass skipped for {y_old}/{y_yng}; remaining nulls left for conservative floodplain fill."
    )

    return u

def _merge_layers(layers, context, feedback, crs=None):
    """
    Merge layers safely.

    Rules:
      - resolve all inputs to valid QgsVectorLayer objects
      - determine reference CRS from `crs` or first valid input CRS
      - if an input CRS is blank, assign the reference CRS only
      - if an input CRS is valid but differs from the reference CRS, fail
        (this function assumes CRS harmonisation was done earlier)
      - fail on invalid extents before merge
    """
    import math

    # PURPOSE: Check that CRS metadata are present and usable.
    def _valid_crs(c):
        return c is not None and c.isValid()

    # PURPOSE: Return a readable CRS identifier for geometry diagnostics.
    def _crs_id(c):
        return c.authid() if _valid_crs(c) else "<blank>"

    # PURPOSE: Reject invalid/non-finite geometry extents before or after data operations.
    def _extent_is_finite(vlayer):
        if vlayer is None or not vlayer.isValid():
            return False
        try:
            ext = vlayer.extent()
            vals = [ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum()]
            return all(math.isfinite(float(v)) for v in vals)
        except Exception:
            return False

    # PURPOSE: Format an extent for meaningful QA messages.
    def _extent_txt(vlayer):
        try:
            ext = vlayer.extent()
            return (
                f"xmin={ext.xMinimum()} xmax={ext.xMaximum()} "
                f"ymin={ext.yMinimum()} ymax={ext.yMaximum()}"
            )
        except Exception:
            return "<extent unavailable>"

    lyr_list = []
    ref_crs = crs if _valid_crs(crs) else None

    # ------------------------------------------------------------------
    # Resolve layers and derive reference CRS if needed
    # ------------------------------------------------------------------
    for i, src in enumerate(layers):
        lyr = _as_layer(src, context) or src
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[_merge_layers] Skipping invalid layer at index {i}: {src}")
            continue

        lyr_list.append(lyr)

        try:
            lyr_crs = lyr.crs() if hasattr(lyr, "crs") else None
        except Exception:
            lyr_crs = None

        if ref_crs is None and _valid_crs(lyr_crs):
            ref_crs = lyr_crs

    if not lyr_list:
        raise QgsProcessingException("[_merge_layers] No valid input layers to merge.")

    if not _valid_crs(ref_crs):
        raise QgsProcessingException("[_merge_layers] Could not determine a valid CRS.")

    # ------------------------------------------------------------------
    # Validate / repair CRS and extents
    # ------------------------------------------------------------------
    fixed_layers = []

    for i, lyr in enumerate(lyr_list):
        try:
            lyr_crs = lyr.crs() if hasattr(lyr, "crs") else None
        except Exception:
            lyr_crs = None

        if not _valid_crs(lyr_crs):
            try:
                lyr.setCrs(ref_crs)
                feedback.reportError(
                    f"[_merge_layers] Assigned blank CRS to layer {i}: {ref_crs.authid()} (no reprojection)"
                )
                lyr_crs = lyr.crs()
            except Exception as e:
                raise QgsProcessingException(
                    f"[_merge_layers] Layer {i} has blank CRS and could not be assigned one: {e}"
                )

        if not _valid_crs(lyr_crs):
            raise QgsProcessingException(
                f"[_merge_layers] Layer {i} CRS is still invalid after repair attempt."
            )

        if lyr_crs.authid() != ref_crs.authid():
            raise QgsProcessingException(
                f"[_merge_layers] CRS mismatch at layer {i}: "
                f"{_crs_id(lyr_crs)} != {_crs_id(ref_crs)}. "
                f"Harmonise CRS before calling _merge_layers()."
            )

        if not _extent_is_finite(lyr):
            raise QgsProcessingException(
                f"[_merge_layers] Layer {i} has invalid extent before merge: {_extent_txt(lyr)}"
            )

        feedback.pushInfo(
            f"[_merge_layers] layer {i}: fc={lyr.featureCount()} "
            f"crs={_crs_id(lyr_crs)} extent={_extent_txt(lyr)}"
        )

        fixed_layers.append(lyr)

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------
    params = {
        "LAYERS": fixed_layers,
        "CRS": ref_crs,
        "OUTPUT": "TEMPORARY_OUTPUT",
    }

    out = _run("native:mergevectorlayers", params, context, feedback)["OUTPUT"]
    out_lyr = _as_layer(out, context) or out

    if out_lyr is None or not out_lyr.isValid():
        raise QgsProcessingException("[_merge_layers] Merge returned invalid output.")

    if not _extent_is_finite(out_lyr):
        raise QgsProcessingException(
            f"[_merge_layers] Merged output has invalid extent: {_extent_txt(out_lyr)}"
        )

    feedback.pushInfo(
        f"[_merge_layers] merged fc={out_lyr.featureCount()} "
        f"crs={_crs_id(out_lyr.crs() if hasattr(out_lyr, 'crs') else None)} "
        f"extent={_extent_txt(out_lyr)}"
    )

    return out

def _dissolve_all(layer, context, feedback=None):
    """
    Dissolve all geometries into one multipart / multipolygon.
    Used to build envelopes and union surfaces.
    """
    try:
        out = _run(
            "native:dissolve",
            {
                "INPUT": layer, "FIELD": [], "SEPARATE_DISJOINT": False,
                "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]
        return _as_layer(out, context)
    except Exception as e:
        if feedback:
            feedback.reportError(f"[dissolve_all] native:dissolve failed: {e}. Returning input as-is.")
        return _as_layer(layer, context)


# PURPOSE: Return the geometry category of a QGIS layer.
def _geom_type(layer, context=None):
    lyr = _as_layer(layer, context)
    if lyr is None or not lyr.isValid():
        return None
    return QgsWkbTypes.geometryType(lyr.wkbType())



def _union_polys(A, B, context, feedback=None, tag="union"):
    """
    Simple polygon union with strict validation.

    - forces both inputs to valid, non-empty polygon layers
    - fixes geometries and forces 2D via _ensure_polygon
    - runs native:union only when both inputs are usable
    """
    A2 = _ensure_polygon(A, context, feedback, f"{tag}:A")
    B2 = _ensure_polygon(B, context, feedback, f"{tag}:B")

    A2 = _as_layer(A2, context) or A2
    B2 = _as_layer(B2, context) or B2

    if A2 is None or not A2.isValid() or A2.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] A is invalid/empty before union")

    if B2 is None or not B2.isValid() or B2.featureCount() == 0:
        raise QgsProcessingException(f"[{tag}] B is invalid/empty before union")

    if QgsWkbTypes.geometryType(A2.wkbType()) != QgsWkbTypes.PolygonGeometry:
        raise QgsProcessingException(f"[{tag}] A is not polygonal before union")

    if QgsWkbTypes.geometryType(B2.wkbType()) != QgsWkbTypes.PolygonGeometry:
        raise QgsProcessingException(f"[{tag}] B is not polygonal before union")

    if feedback is not None:
        feedback.pushInfo(
            f"[{tag}] union inputs: "
            f"A fc={A2.featureCount()} geom={QgsWkbTypes.displayString(A2.wkbType())}; "
            f"B fc={B2.featureCount()} geom={QgsWkbTypes.displayString(B2.wkbType())}"
        )

    out = _run(
        "native:union",
        {
            "INPUT": A2,
            "OVERLAY": B2,
            "OVERLAY_FIELDS_PREFIX": "",
            "GRID_SIZE": 0,
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]

    out = _as_layer(out, context) or out
    if out is None or not out.isValid():
        raise QgsProcessingException(f"[{tag}] union output invalid")

    # keep polygon-only output
    out = _run(
        "native:extractbyexpression",
        {
            "INPUT": out,
            "EXPRESSION": "geometry_type($geometry) IN ('Polygon','MultiPolygon')",
            "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]

    out = _run(
        "native:fixgeometries",
        {"INPUT": out, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]

    out = _force_2d_safe(out, context, feedback)
    out = _as_layer(out, context) or out

    if out is None or not out.isValid():
        raise QgsProcessingException(f"[{tag}] union output invalid after cleanup")

    if out.featureCount() == 0 and feedback is not None:
        feedback.reportError(f"[{tag}] union output empty after cleanup")

    return out


def _safe_clip(A, mask, context, feedback, grid_sequence=(0.10, 0.25, 0.50, 1.0)):
    """
    Robust clipping:
      1) Clean polygons via _prep_poly
      2) (Fast path) If mask is a single polygon, try native:clip first
      3) Buffer(0) robustness pass (repairs topology beyond fixgeometries)
      4) Snap both to a sequence of grid sizes and try native:intersection
      5) If all fail, build an envelope fallback and intersect with it
    Returns intersection (preferred) or original A as last fallback.
    """
    A0 = _prep_poly(A,    context, feedback)
    M0 = _prep_poly(mask, context, feedback)

    # ---------- Fast path: mask is a single polygon -> try native:clip ----------
    try:
        mlyr = _as_layer(M0, context)
        if mlyr and mlyr.isValid() and mlyr.featureCount() == 1:
            out = _run(
                "native:clip",
                {"INPUT": A0, "OVERLAY": M0, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            return _as_layer(out, context) or out
    except Exception as e:
        if feedback:
            feedback.reportError(f"[safe_clip] native:clip fast path failed (continuing): {e}")

    # ---------- Buffer(0) robustness: repairs topology that can crash intersection ----------
    try:
        A0 = _run(
            "native:buffer",
            {
                "INPUT": A0,
                "DISTANCE": 0.0,
                "SEGMENTS": 5,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2.0,
                "DISSOLVE": False,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        M0 = _run(
            "native:buffer",
            {
                "INPUT": M0,
                "DISTANCE": 0.0,
                "SEGMENTS": 5,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2.0,
                "DISSOLVE": False,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context, feedback
        )["OUTPUT"]
        A0 = _as_layer(A0, context) or A0
        M0 = _as_layer(M0, context) or M0
    except Exception as e:
        if feedback:
            feedback.reportError(f"[safe_clip] buffer(0) robustness failed (continuing): {e}")

    # Try intersection with several grid snaps
    for g in grid_sequence:
        try:
            A1 = _snap_to_grid(A0, g, context, feedback)
            M1 = _snap_to_grid(M0, g, context, feedback)
            out = _run(
                "native:intersection",
                {
                    "INPUT": A1, "OVERLAY": M1,
                    "INPUT_FIELDS": [], "OVERLAY_FIELDS": [],
                    "OVERLAY_FIELDS_PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            return _as_layer(out, context) or out
        except Exception as e:
            if feedback:
                feedback.reportError(f"[safe_clip] intersection @GRID={g} failed: {e}")

    # If we get here, attempt intersection with simpler envelope
    if feedback:
        feedback.reportError("[safe_clip] Falling back to merge→dissolve envelope.")
    env = _envelope_fallback(A0, M0, context, feedback)
    try:
        out = _run(
            "native:intersection",
            {
                "INPUT": A0, "OVERLAY": env,
                "INPUT_FIELDS": [], "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"
            },
            context, feedback
        )["OUTPUT"]
        return _as_layer(out, context) or out
    except Exception as e:
        if feedback:
            feedback.reportError(f"[safe_clip] final envelope intersection failed: {e}")
        return _as_layer(A0, context) or A0

def _clip_polys(A, mask, context, feedback):
    """
    Public wrapper around _safe_clip for polygon clipping.
    """
    return _safe_clip(A, mask, context, feedback)


def _intersect_polys(A, B, context, feedback=None):
    """
    Simple intersection:
      - fix + 2D both inputs
      - native:intersection with no field restrictions
    """
    A2 = _as_layer(
        _force_2d_safe(_fix_geoms(A, context, feedback), context=context, feedback=feedback),
        context
    )
    B2 = _as_layer(
        _force_2d_safe(_fix_geoms(B, context, feedback), context=context, feedback=feedback),
        context
    )
    out = _run(
        "native:intersection",
        {
            "INPUT": A2, "OVERLAY": B2,
            "INPUT_FIELDS": [], "OVERLAY_FIELDS": [],
            "OVERLAY_FIELDS_PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"
        },
        context, feedback
    )["OUTPUT"]
    return _as_layer(out, context) or out


def _safe_intersection(A, B, grid=0.10, context=None, feedback=None):
    """
    Robust intersection similar to _safe_union:
      1) fixgeoms both
      2) Snap to several grid sizes and try native:intersection
      3) If all fail, return cleaned A
    """
    A1 = _fix_geoms(A, context, feedback)
    B1 = _fix_geoms(B, context, feedback)

    for g in [grid or 0.10, 0.25, 0.50, 1.00]:
        try:
            A2 = _snap_to_grid(A1, g, context, feedback)
            B2 = _snap_to_grid(B1, g, context, feedback)
            out = _run(
                "native:intersection",
                {
                    "INPUT": A2,
                    "OVERLAY": B2,
                    "INPUT_FIELDS": [],
                    "OVERLAY_FIELDS": [],
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            return _as_layer(out, context) or out
        except Exception as e:
            if feedback:
                feedback.reportError(f"[safe_intersection] GRID={g} failed: {e}")

    if feedback:
        feedback.reportError("[safe_intersection] All attempts failed; returning A unchanged.")
    return _as_layer(A1, context) or A1


def _difference_polys(A, B, context, feedback=None):
    """
    Polygon difference A - B with fix + 2D pre-cleaning on both inputs.
    Used in island detection (envelope minus channel).
    """
    A2 = _as_layer(
        _force_2d_safe(_fix_geoms(A, context, feedback), context=context, feedback=feedback),
        context
    )
    B2 = _as_layer(
        _force_2d_safe(_fix_geoms(B, context, feedback), context=context, feedback=feedback),
        context
    )
    out = _run(
        "native:difference",
        {"INPUT": A2, "OVERLAY": B2, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    return _as_layer(out, context) or out


# --- DATE PARSING HELPERS (lenient) ---

def _coerce_date_yyyy_or_yyyymmdd(val, default_md="0101"):
    """
    Attempt to parse val as either:
      - full YYYYMMDD (numeric or embedded in string)
      - ISO-like YYYY-MM-DD or YYYY/MM/DD
      - bare YYYY (18xx–20xx), in which case default_md is appended.
    Returns:
      (year_int, 'YYYYMMDD', date_object)
    Raises ValueError if nothing can be parsed.
    """
    if val is None:
        raise ValueError("empty date")
    s = str(val).strip()

    # Pattern 1: direct YYYYMMDD (e.g. 19990521)
    m8 = re.search(r"\b(1[89]\d{2}|20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b", s)
    if m8:
        y, mo, da = map(int, m8.groups())
        return y, f"{y:04d}{mo:02d}{da:02d}", date(y, mo, da)

    # Pattern 2: ISO / slash date, e.g. 1999-05-21 or 1999/05/21
    miso = re.search(
        r"\b(1[89]\d{2}|20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b",
        s
    )
    if miso:
        y, mo, da = map(int, miso.groups())
        return y, f"{y:04d}{mo:02d}{da:02d}", date(y, mo, da)

    # Pattern 3: only year, infer default month/day
    m4 = re.search(r"\b(1[89]\d{2}|20\d{2})\b", s)
    if m4:
        y = int(m4.group(1))
        return y, f"{y:04d}{default_md}", date(y, int(default_md[:2]), int(default_md[2:]))

    raise ValueError(f"Cannot parse date/year from: {s!r}")


def _yyyymmdd_from_value_lenient(val):
    """
    Wrapper around _coerce_date_yyyy_or_yyyymmdd that returns YYYYMMDD or None.
    """
    try:
        _, ymd, _ = _coerce_date_yyyy_or_yyyymmdd(val)
        return ymd
    except Exception:
        return None


def _date_object_from_value_lenient(val):
    """
    Wrapper around _coerce_date_yyyy_or_yyyymmdd that returns a date object or None.
    """
    try:
        _, _, dt = _coerce_date_yyyy_or_yyyymmdd(val)
        return dt
    except Exception:
        return None


def _ensure_folder(path):
    """
    Ensure that a folder exists; create if missing (equivalent to mkdir -p).
    """
    os.makedirs(path, exist_ok=True)


def _yyyymmdd_from_text(text):
    """
    Try to extract YYYYMMDD, or infer YYYY0101 from text.
    Returns:
      'YYYYMMDD' or None.
    """
    if not text:
        return None
    s = str(text)

    # Direct 8-digit date with year prefix
    m8 = re.search(r"\b(18|19|20)\d{6}\b", s)
    if m8:
        return m8.group(0)

    # ISO-like date with separators
    m_iso = re.search(r"\b(18|19|20)\d{2}[-/](\d{2})[-/](\d{2})\b", s)
    if m_iso:
        return f"{m_iso.group(1)}{m_iso.group(2)}{m_iso.group(3)}"

    # Bare year
    m4 = re.search(r"\b(18|19|20)\d{2}\b", s)
    if m4:
        return f"{m4.group(0)}0101"

    return None


def _layer_source(layer):
    """
    Safe accessor for layer.source(), returning empty string on error.
    """
    try:
        return layer.source()
    except Exception:
        return ""


def _layer_name(layer):
    """
    Safe accessor for layer.name(), returning empty string on error.
    """
    try:
        return layer.name()
    except Exception:
        return ""


def _yyyymmdd_from_layer_meta(layer):
    """
    Try to get YYYYMMDD from either layer's source path or its name.
    """
    return _yyyymmdd_from_text(f"{_layer_source(layer)} {_layer_name(layer)}")


def _yyyymmdd_from_value(val):
    """
    Strict-ish date parser for layer attributes:
      - QDateTime/QDate-compatible objects
      - datetime/date objects
      - numeric YYYY or YYYYMMDD
      - string formed as YYYYMMDD, YYYY-MM-DD, or bare YYYY
    Returns:
      'YYYYMMDD' or None
    """
    if val is None:
        return None

    # QGIS date/time wrapper types
    try:
        if hasattr(val, "toPyDateTime"):
            dt = val.toPyDateTime()
            return dt.strftime("%Y%m%d")
        if hasattr(val, "toPyDate"):
            d = val.toPyDate()
            return d.strftime("%Y%m%d")
    except Exception:
        pass

    # Python datetime/date objects
    if isinstance(val, datetime):
        return val.strftime("%Y%m%d")
    if isinstance(val, date):
        return val.strftime("%Y%m%d")

    # Numeric types (e.g. 1999 or 19990521)
    if isinstance(val, (int, float)):
        s = str(int(val))
        # pure YYYY
        if re.fullmatch(r"(19|20)\d{2}", s):
            return f"{s}0101"
        # full YYYYMMDD
        if re.fullmatch(r"(19|20)\d{6}", s):
            return s
        return None

    # Strings
    s = str(val).strip()
    if re.fullmatch(r"(19|20)\d{6}", s):
        return s
    if re.fullmatch(r"(19|20)\d{2}[-/]\d{2}[-/]\d{2}", s):
        return f"{s[0:4]}{s[5:7]}{s[8:10]}"
    if re.fullmatch(r"(19|20)\d{2}", s):
        return f"{s}0101"
    return None


def _date_object_from_value(val):
    """
    Convert a value to a Python datetime (YMD) if possible.
    Accepts:
      - QGIS date/time wrappers
      - Python datetime/date
      - numeric/strings recognized by _yyyymmdd_from_value
      - simple yyyy, yyyy-mm-dd, yyyy/mm/dd
    """
    if val is None:
        return None

    # QGIS wrappers
    try:
        if hasattr(val, "toPyDateTime"):
            return val.toPyDateTime()
        if hasattr(val, "toPyDate"):
            d = val.toPyDate()
            return datetime(d.year, d.month, d.day)
    except Exception:
        pass

    # Python types
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)

    # Numeric
    if isinstance(val, (int, float)):
        ymd = _yyyymmdd_from_value(val)
        return datetime.strptime(ymd, "%Y%m%d") if ymd else None

    # Strings with various formats
    s = str(val).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass

    # Bare year -> assume 1 Jan
    if re.fullmatch(r"(19|20)\d{2}", s):
        return datetime.strptime(s + "0101", "%Y%m%d")
    return None


def is_empty_layer(obj, context, feedback=None, label=""):
    """
    Determine whether a layer is "empty" (0 features).
    More robust than simply featureCount() in case of errors.
    Logs debug info if feedback is provided.
    """
    lyr = _as_layer(obj, context)
    if lyr is None or not getattr(lyr, "isValid", lambda: False)():
        if feedback and label:
            feedback.reportError(f"[DEBUG] {label}: not a valid layer; treating as EMPTY.")
        return True

    try:
        cnt = lyr.featureCount()
        if feedback and label:
            feedback.pushInfo(f"[DEBUG] {label} featureCount={cnt}")
        return cnt == 0
    except Exception as e:
        # If featureCount fails, try iterating
        if feedback and label:
            feedback.reportError(f"[DEBUG] {label} featureCount() error: {e}; trying iterator.")
        try:
            next(lyr.getFeatures())
            if feedback and label:
                feedback.pushInfo(f"[DEBUG] {label} has at least 1 feature (iterator).")
            return False
        except StopIteration:
            if feedback and label:
                feedback.pushInfo(f"[DEBUG] {label} iterator found 0 features.")
            return True
        except Exception as e2:
            if feedback and label:
                feedback.reportError(
                    f"[DEBUG] {label} getFeatures() error: {e2}; assuming NOT empty."
                )
            return False


def _ensure_exists(p):
    """
    Return True if path exists and has size > 0.
    """
    try:
        return os.path.exists(p) and os.path.getsize(p) > 0
    except Exception:
        return False


def _suffix_path(path):
    """
    Return a new path adding a timestamp suffix before the extension.
    Used when we can't overwrite a locked file cleanly.
    """
    base, ext = os.path.splitext(path)
    return f"{base}_{_dt.now().strftime('%Y%m%d_%H%M%S')}{ext}"


def _move_with_retry(src, dst, feedback=None, attempts=5, sleep_s=0.4, allow_suffix=True):
    """
    Move src to dst with multiple attempts and delays in between.
    If dst is locked, we optionally write a suffixed version and log.
    Returns the final destination path (or empty string on failure).
    """
    # First attempt: remove existing dst if possible
    try:
        if os.path.exists(dst):
            os.remove(dst)
    except Exception as e:
        if feedback:
            feedback.reportError(f"[WRITE] Could not delete existing {dst}: {e}")

    # Multiple attempts to move
    for i in range(attempts):
        try:
            shutil.move(src, dst)
            return dst if _ensure_exists(dst) else ""
        except Exception as e:
            if feedback:
                feedback.reportError(f"[WRITE] move attempt {i+1}/{attempts} failed: {e}")
            time.sleep(sleep_s)

    # If that fails and suffix is allowed, try suffixed destination
    if allow_suffix:
        alt = _suffix_path(dst)
        try:
            shutil.move(src, alt)
            if feedback:
                feedback.reportError(f"[WRITE] Destination locked; wrote to {alt} instead.")
            return alt if _ensure_exists(alt) else ""
        except Exception as e:
            if feedback:
                feedback.reportError(f"[WRITE] move to suffixed path failed: {e}")

    # Last fallback: try copy
    try:
        shutil.copy2(src, dst)
        return dst if _ensure_exists(dst) else ""
    except Exception as e:
        if feedback:
            feedback.reportError(f"[WRITE] copy failed: {e}")
        return ""


# PURPOSE: Write or append final outputs to the shared GeoPackage, checking layer existence and output integrity.
def _write_gpkg(input_layer, gpkg_path, layer_name, context, overwrite=True, feedback=None):
    import tempfile
    from qgis.core import QgsVectorFileWriter, QgsProject, QgsVectorLayer

    # PURPOSE: Check whether a GeoPackage contains a valid named output layer.
    def _gpkg_layer_ok(path, name):
        try:
            v = QgsVectorLayer(f"{path}|layername={name}", name, "ogr")
            return v.isValid() and v.featureCount() > 0
        except Exception:
            return False

    lyr = _as_layer(input_layer, context)
    if lyr is None or not lyr.isValid():
        if feedback:
            feedback.reportError("[WRITE] Input layer invalid; skipping write.")
        return ""

    try:
        if feedback:
            feedback.pushInfo(f"[WRITE] input featureCount={lyr.featureCount()}")
    except Exception:
        pass

    # Conservative fixgeometries: only keep fixed result if it is non-empty
    orig_lyr = lyr
    try:
        fixed = _run(
            "native:fixgeometries",
            {"INPUT": lyr, "OUTPUT": "TEMPORARY_OUTPUT"},
            context, feedback
        )["OUTPUT"]
        fixed = _as_layer(fixed, context) or fixed

        fixed_ok = False
        try:
            fixed_ok = fixed is not None and fixed.isValid() and fixed.featureCount() > 0
        except Exception:
            fixed_ok = False

        if fixed_ok:
            lyr = fixed
            if feedback:
                feedback.pushInfo(f"[WRITE] fixgeometries kept {lyr.featureCount()} features.")
        else:
            lyr = orig_lyr
            if feedback:
                feedback.pushInfo("[WRITE] fixgeometries produced empty output; using original layer.")
    except Exception as e:
        lyr = orig_lyr
        if feedback:
            feedback.pushInfo(f"[WRITE] fixgeometries failed; using original layer. ({e})")

    lyr = _force_2d_safe(lyr, context, feedback)
    lyr = _strip_pk_fields(lyr, context, feedback)
    lyr = _as_layer(lyr, context) or lyr

    try:
        if feedback:
            feedback.pushInfo(f"[WRITE] pre-save featureCount={lyr.featureCount()}")
        if lyr.featureCount() == 0:
            if feedback:
                feedback.reportError("[WRITE] Layer has 0 features; skipping write.")
            return ""
    except Exception:
        pass

    final_gpkg = gpkg_path
    os.makedirs(os.path.dirname(final_gpkg), exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="scs_ea_write_")
    tmp_gpkg = os.path.join(tmpdir, os.path.basename(final_gpkg))

    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = layer_name
    opts.fileEncoding = "UTF-8"
    opts.datasourceOptions = ["SPATIAL_INDEX=YES"]
    opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

    try:
        try:
            tctx = context.transformContext()
        except Exception:
            tctx = QgsProject.instance().transformContext()

        ret = QgsVectorFileWriter.writeAsVectorFormatV3(lyr, tmp_gpkg, tctx, opts)
        code = ret[0] if isinstance(ret, (list, tuple)) else ret
        msg = ret[1] if isinstance(ret, (list, tuple)) and len(ret) > 1 else ""
        if code != QgsVectorFileWriter.NoError:
            raise Exception(msg or f"Writer error code: {code}")
    except Exception as e:
        if feedback:
            feedback.reportError(f"[WRITE] PyQGIS GPKG write failed: {e}")
        return ""

    if not os.path.exists(final_gpkg):
        try:
            shutil.move(tmp_gpkg, final_gpkg)
            if feedback:
                feedback.pushInfo(f"[WRITE] Final GPKG created: {final_gpkg}")
            return final_gpkg
        except Exception as e:
            if feedback:
                feedback.reportError(f"[WRITE] Move to final GPKG failed: {e}")
            return ""

    try:
        opts2 = QgsVectorFileWriter.SaveVectorOptions()
        opts2.driverName = "GPKG"
        opts2.layerName = layer_name
        opts2.fileEncoding = "UTF-8"
        opts2.datasourceOptions = ["SPATIAL_INDEX=YES"]
        opts2.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        src_layer = _as_layer(f"{tmp_gpkg}|layername={layer_name}", context)
        ret2 = QgsVectorFileWriter.writeAsVectorFormatV3(src_layer, final_gpkg, tctx, opts2)
        code2 = ret2[0] if isinstance(ret2, (list, tuple)) else ret2
        msg2 = ret2[1] if isinstance(ret2, (list, tuple)) and len(ret2) > 1 else ""
        if code2 != QgsVectorFileWriter.NoError:
            raise Exception(msg2 or f"Writer error code: {code2}")

        if not _gpkg_layer_ok(final_gpkg, layer_name):
            raise Exception("Layer validation failed after write.")
        if feedback:
            feedback.pushInfo(f"[WRITE] Wrote/updated layer '{layer_name}' in {final_gpkg}")
        return final_gpkg
    except Exception as e:
        if feedback:
            feedback.reportError(f"[WRITE] Layer copy into final GPKG failed: {e}")
        return ""




# PURPOSE: Reverse feature vertex order to standardise centreline orientation.
def _reverse_line_layer(layer, context, feedback, tag="rev_line"):
    lyr = _as_layer(layer, context) or layer
    if lyr is None or not lyr.isValid():
        raise QgsProcessingException(f"[{tag}] invalid line layer")
    return _run("native:reverselinedirection", {"INPUT": lyr, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]


# PURPOSE: Extract the start/end vertices of a line geometry for orientation comparison.
def _line_endpoints(geom):
    pts = [v for v in geom.vertices()]
    if not pts:
        return None, None
    return pts[0], pts[-1]


# PURPOSE: Reorient a centreline against a reference so LEFT/RIGHT side assignments stay consistent.
def _harmonize_centerline_direction(ref_line, target_line, context, feedback, tag="cen_dir"):
    ref = _as_layer(ref_line, context) or ref_line
    tgt = _as_layer(target_line, context) or target_line
    if ref is None or tgt is None or not ref.isValid() or not tgt.isValid() or ref.featureCount() == 0 or tgt.featureCount() == 0:
        return target_line
    try:
        rg = next(ref.getFeatures()).geometry()
        tg = next(tgt.getFeatures()).geometry()
        if rg is None or tg is None or rg.isEmpty() or tg.isEmpty():
            return target_line
        r0, r1 = _line_endpoints(rg)
        t0, t1 = _line_endpoints(tg)
        if None in (r0, r1, t0, t1):
            return target_line
        same = r0.distance(t0) + r1.distance(t1)
        revd = r0.distance(t1) + r1.distance(t0)
        if revd + 1e-9 < same:
            _dbg_log(feedback, f"[DIR] reversing {tag} to match reference direction")
            return _reverse_line_layer(target_line, context, feedback, tag=tag)
    except Exception as e:
        if feedback and _dbg_enabled():
            feedback.reportError(f"[DIR] harmonize failed for {tag}: {e}")
    return target_line


# PURPOSE: Index date-specific optional surface layers using their parsed observation dates.
def _build_surface_year_map(layers, field_name, ref_crs_obj, context, feedback, tag):
    out = {}
    if not layers:
        return out
    for obj in layers:
        lyr = _as_layer(obj, context) or obj
        if lyr is None or not lyr.isValid() or lyr.featureCount() == 0:
            continue
        feat = next(lyr.getFeatures())
        names = lyr.fields().names()
        ymd = _yyyymmdd_from_value_lenient(feat[field_name]) if field_name in names else None
        if not ymd:
            ymd = _yyyymmdd_from_layer_meta(lyr)
        if not ymd:
            if feedback:
                feedback.reportError(f"[{tag}] Could not parse date for layer {lyr.name()}")
            continue
        out[ymd] = _ensure_layer_crs(lyr, ref_crs_obj, context, feedback, f"{tag}_{ymd}")
    return out


# PURPOSE: Apply the optional water/active-domain surface interpretation to the underlying EA classification.
def _override_ea_from_dual_surface(working, y1, y2, water_old, active_old, water_yng, active_yng, mode, context, feedback):
    if not (water_old and active_old and water_yng and active_yng):
        return working
    lyr = _as_layer(working, context) or working
    if lyr is None or not lyr.isValid() or lyr.featureCount() == 0:
        return working
    if lyr.fields().indexOf("EAID") == -1:
        lyr = _run("native:fieldcalculator", {"INPUT": lyr, "FIELD_NAME": "EAID", "FIELD_TYPE": 1, "FIELD_LENGTH": 18, "FIELD_PRECISION": 0, "NEW_FIELD": True, "FORMULA": "$id", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    pts = _run("native:pointonsurface", {"INPUT": lyr, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]

    # PURPOSE: Construct a side-mask join flag used in orientation tagging.
    def _join_flag(in_pts, join_layer, fname, prefix):
        jlyr = _as_layer(join_layer, context) or join_layer
        if jlyr is None or not jlyr.isValid() or jlyr.featureCount() == 0:
            return in_pts
        if jlyr.fields().indexOf(fname) == -1:
            jlyr = _run("native:fieldcalculator", {"INPUT": jlyr, "FIELD_NAME": fname, "FIELD_TYPE": 1, "FIELD_LENGTH": 1, "FIELD_PRECISION": 0, "NEW_FIELD": True, "FORMULA": "1", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
        return _run("native:joinattributesbylocation", {"INPUT": in_pts, "JOIN": jlyr, "PREDICATE": [0], "JOIN_FIELDS": [fname], "METHOD": 0, "DISCARD_NONMATCHING": False, "PREFIX": prefix, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]

    pts = _join_flag(pts, water_old, "W1", "O_")
    pts = _join_flag(pts, active_old, "A1", "O_")
    pts = _join_flag(pts, water_yng, "W2", "Y_")
    pts = _join_flag(pts, active_yng, "A2", "Y_")
    pts_lyr = _as_layer(pts, context) or pts
    fields_to_copy = [n for n in ["O_W1", "O_A1", "Y_W2", "Y_A2"] if pts_lyr.fields().indexOf(n) != -1]
    if fields_to_copy:
        lyr = _run("native:joinattributestable", {"INPUT": lyr, "FIELD": "EAID", "INPUT_2": pts_lyr, "FIELD_2": "EAID", "FIELDS_TO_COPY": fields_to_copy, "METHOD": 1, "DISCARD_NONMATCHING": False, "PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    mode_expr = "0" if int(mode) == 0 else "1"
    expr = f"""
with_variable('s1', CASE WHEN coalesce("O_W1",0)=1 THEN 'WATER' WHEN coalesce("O_A1",0)=1 THEN 'ACTIVE_DRY' ELSE 'FLOODPLAIN' END,
with_variable('s2', CASE WHEN coalesce("Y_W2",0)=1 THEN 'WATER' WHEN coalesce("Y_A2",0)=1 THEN 'ACTIVE_DRY' ELSE 'FLOODPLAIN' END,
CASE
  WHEN "EA" IN ('island_erosion','island_deposition','stable_island') THEN "EA"
  WHEN {mode_expr}=0 THEN
    CASE
      WHEN @s1='WATER' AND @s2='WATER' THEN 'stable_channel'
      WHEN @s1='WATER' AND @s2 IN ('ACTIVE_DRY','FLOODPLAIN') THEN 'deposition'
      WHEN @s2='WATER' AND @s1 IN ('ACTIVE_DRY','FLOODPLAIN') THEN 'erosion'
      WHEN @s1='ACTIVE_DRY' AND @s2='ACTIVE_DRY' THEN 'inactive_floodplain'
      WHEN @s2='ACTIVE_DRY' THEN 'inactive_floodplain'
      ELSE 'stable_floodplain'
    END
  ELSE
    CASE
      WHEN @s1='WATER' AND @s2='WATER' THEN 'stable_channel'
      WHEN @s1='ACTIVE_DRY' AND @s2='ACTIVE_DRY' THEN 'inchannel_surface'
      WHEN @s1='WATER' AND @s2 IN ('ACTIVE_DRY','FLOODPLAIN') THEN 'deposition'
      WHEN @s2='WATER' AND @s1 IN ('ACTIVE_DRY','FLOODPLAIN') THEN 'erosion'
      WHEN @s1='FLOODPLAIN' AND @s2='ACTIVE_DRY' THEN 'deposition'
      WHEN @s1='ACTIVE_DRY' AND @s2='FLOODPLAIN' THEN 'inactive_floodplain'
      ELSE 'stable_floodplain'
    END
END))
""".strip()
    lyr = _run("native:fieldcalculator", {"INPUT": lyr, "FIELD_NAME": "EA", "FIELD_TYPE": 2, "FIELD_LENGTH": 32, "FIELD_PRECISION": 0, "NEW_FIELD": False, "FORMULA": expr, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    drop = [n for n in ["O_W1", "O_A1", "Y_W2", "Y_A2"] if (_as_layer(lyr, context).fields().indexOf(n) != -1)]
    if drop:
        lyr = _run("native:deletecolumn", {"INPUT": lyr, "COLUMN": drop, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    return lyr


# PURPOSE: Allocate a side label according to the largest overlap area, avoiding touch-only assignments.
def _assign_side_by_max_overlap(poly_layer, side_layer, side_field, context, feedback, prefix="SX"):
    poly = _as_layer(poly_layer, context) or poly_layer
    side = _as_layer(side_layer, context) or side_layer
    if poly is None or side is None or not poly.isValid() or not side.isValid() or poly.featureCount() == 0 or side.featureCount() == 0:
        return poly_layer
    if poly.fields().indexOf("EAID") == -1:
        poly = _run("native:fieldcalculator", {"INPUT": poly, "FIELD_NAME": "EAID", "FIELD_TYPE": 1, "FIELD_LENGTH": 18, "FIELD_PRECISION": 0, "NEW_FIELD": True, "FORMULA": "$id", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    inter = _run("native:intersection", {"INPUT": poly, "OVERLAY": side, "INPUT_FIELDS": ["EAID"], "OVERLAY_FIELDS": [side_field], "OVERLAY_FIELDS_PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    inter = _as_layer(inter, context) or inter
    if inter is None or not inter.isValid() or inter.featureCount() == 0:
        return poly
    best = {}
    for f in inter.getFeatures():
        rid = f["EAID"]
        sval = f[side_field]
        area = f.geometry().area() if f.geometry() and not f.geometry().isEmpty() else 0.0
        if rid is None or sval is None or str(sval).strip()=="" or area <= 0:
            continue
        cur = best.get(rid)
        if cur is None or area > cur[0]:
            best[rid] = (area, str(sval))
    if not best:
        return poly
    mem = QgsVectorLayer(f"None?field=EAID:integer&field={prefix}:string(20)", f"{prefix}_lut", "memory")
    pr = mem.dataProvider()
    feats=[]
    for rid, (_, sval) in best.items():
        ft = QgsFeature(mem.fields())
        ft["EAID"] = int(rid)
        ft[prefix] = sval
        feats.append(ft)
    pr.addFeatures(feats)
    poly = _run("native:joinattributestable", {"INPUT": poly, "FIELD": "EAID", "INPUT_2": mem, "FIELD_2": "EAID", "FIELDS_TO_COPY": [prefix], "METHOD": 1, "DISCARD_NONMATCHING": False, "PREFIX": "", "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    poly = _run("native:fieldcalculator", {"INPUT": poly, "FIELD_NAME": side_field, "FIELD_TYPE": 2, "FIELD_LENGTH": 20, "FIELD_PRECISION": 0, "NEW_FIELD": False, "FORMULA": f'coalesce("{side_field}", "{prefix}")', "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    if (_as_layer(poly, context).fields().indexOf(prefix) != -1):
        poly = _run("native:deletecolumn", {"INPUT": poly, "COLUMN": [prefix], "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    return poly


def _topology_debug_save(layer, outdir, label, y1, y2, context, feedback):
    """Save topology-fabric debug layers when debug GPKG output is enabled."""
    if not DEBUG_SAVE:
        return None
    try:
        lyr = _as_layer(layer, context) or layer
        if lyr is None or not lyr.isValid():
            feedback.reportError(f"[TOPO DEBUG] {label}: invalid; not saved")
            return None
        debug_dir = os.path.join(outdir, "M3A_topology_debug")
        os.makedirs(debug_dir, exist_ok=True)
        safe = _safe_token(f"{label}_{y1}_{y2}")[:80]
        out_path = os.path.join(debug_dir, f"{safe}.gpkg")
        for pp in (out_path, out_path + "-wal", out_path + "-shm"):
            try:
                if os.path.exists(pp):
                    os.remove(pp)
            except Exception:
                pass
        src = lyr
        drop_cols = [c for c in ["fid", "FID", "ogc_fid", "OGC_FID", "OBJECTID", "ObjectID", "id", "ID"] if c in lyr.fields().names()]
        if drop_cols:
            try:
                src = _run("native:deletecolumn", {"INPUT": lyr, "COLUMN": drop_cols, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
            except Exception:
                src = lyr
        _run("native:savefeatures", {"INPUT": src, "OUTPUT": out_path}, context, feedback)
        feedback.pushInfo(f"[TOPO DEBUG] saved {label}: {out_path}")
        return out_path
    except Exception as e:
        feedback.reportError(f"[TOPO DEBUG] failed to save {label}: {e}")
        return None


def _add_empty_tag_fields(layer, y1, y2, context, feedback):
    """Ensure topology fabric has y_/T_ fields before support assignment."""
    out = layer
    for fn, val in [(f"y_{y1}", y1), (f"T_{y1}", ""), (f"y_{y2}", y2), (f"T_{y2}", "")]:
        lyr = _as_layer(out, context) or out
        if lyr is None or not lyr.isValid():
            raise QgsProcessingException(f"[TOPO FABRIC] invalid layer while adding {fn}")
        if lyr.fields().indexOf(fn) == -1:
            formula = f"'{val}'" if fn.startswith("y_") else "''"
            out = _run(
                "native:fieldcalculator",
                {
                    "INPUT": lyr,
                    "FIELD_NAME": fn,
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": formula,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
    return out


def _topology_boundary_fabric(EA1c, EA2c, env_mask, y1, y2, context, feedback, outdir, ref_crs_obj=None, tag="topology_fabric"):
    """
    Build pairwise EA fabric from boundary linework rather than polygon overlay.

    This preserves both years' active-domain margins and island/hole ring boundaries.
    The hole-free combined footprint is used only as a keep-mask after polygonization.
    """
    A = _ensure_layer(EA1c, context, feedback, tag=f"{tag}_EA1")
    B = _ensure_layer(EA2c, context, feedback, tag=f"{tag}_EA2")
    M = _ensure_layer(env_mask, context, feedback, tag=f"{tag}_mask")
    feedback.pushInfo(f"[TOPO FABRIC] Building boundary-derived fabric for {y1}->{y2}")
    feedback.pushInfo(f"[TOPO FABRIC] EA1 fc={A.featureCount()} EA2 fc={B.featureCount()} mask fc={M.featureCount()}")

    A = _polys_only(A, context, feedback)
    B = _polys_only(B, context, feedback)
    M = _polys_only(M, context, feedback)

    # PURPOSE: Extract polygon boundaries needed to build the planar overlay fabric.
    def _boundary(src, label):
        try:
            b = _run("native:boundary", {"INPUT": src, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
        except Exception as e:
            feedback.reportError(f"[TOPO FABRIC] native:boundary failed for {label}; using polygonstolines. Error: {e}")
            b = _run("native:polygonstolines", {"INPUT": src, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
        return _as_layer(b, context) or b

    b1 = _boundary(A, "EA1")
    b2 = _boundary(B, "EA2")
    bm = _boundary(M, "mask_outer")
    _topology_debug_save(b1, outdir, "BND_y1_original", y1, y2, context, feedback)
    _topology_debug_save(b2, outdir, "BND_y2_original", y1, y2, context, feedback)
    _topology_debug_save(bm, outdir, "BND_mask_outer", y1, y2, context, feedback)

    local_crs = ref_crs_obj
    if local_crs is None or not local_crs.isValid():
        for candidate in (A, B, M, b1, b2, bm):
            lyr = _as_layer(candidate, context)
            if lyr and lyr.isValid() and lyr.crs().isValid():
                local_crs = lyr.crs()
                break

    merged_lines = _run(
        "native:mergevectorlayers",
        {"LAYERS": [b1, b2, bm], "CRS": local_crs if local_crs and local_crs.isValid() else None, "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    merged_lines = _as_layer(merged_lines, context) or merged_lines
    _topology_debug_save(merged_lines, outdir, "BND_merged_before_node", y1, y2, context, feedback)

    noded_lines = merged_lines
    if _algo_exists("native:unaryunion"):
        try:
            noded_lines = _run("native:unaryunion", {"INPUT": merged_lines, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
            noded_lines = _as_layer(noded_lines, context) or noded_lines
        except Exception as e:
            feedback.reportError(f"[TOPO FABRIC] native:unaryunion line noding failed; using merged lines. Error: {e}")
            noded_lines = merged_lines
    else:
        feedback.reportError("[TOPO FABRIC] native:unaryunion unavailable; polygonize will use merged linework directly.")
    try:
        noded_lines = _force_2d_safe(_fix_geoms(noded_lines, context, feedback), context, feedback)
    except Exception as e:
        feedback.reportError(f"[TOPO FABRIC] line fix/2D failed; continuing. Error: {e}")
    _topology_debug_save(noded_lines, outdir, "BND_noded", y1, y2, context, feedback)

    cells = _run("native:polygonize", {"INPUT": noded_lines, "KEEP_FIELDS": False, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    cells = _as_layer(cells, context) or cells
    _topology_debug_save(cells, outdir, "FABRIC_polygonized_raw", y1, y2, context, feedback)
    if cells is None or not cells.isValid() or cells.featureCount() == 0:
        raise QgsProcessingException(f"[TOPO FABRIC] polygonize returned empty fabric for {y1}->{y2}")

    cells = _run(
        "native:fieldcalculator",
        {"INPUT": cells, "FIELD_NAME": "CELLID", "FIELD_TYPE": 1, "FIELD_LENGTH": 18, "FIELD_PRECISION": 0, "NEW_FIELD": True, "FORMULA": "$id", "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    cells = _as_layer(cells, context) or cells

    pts = _run("native:pointonsurface", {"INPUT": cells, "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]
    pts = _run(
        "native:joinattributesbylocation",
        {"INPUT": pts, "JOIN": M, "PREDICATE": [0], "JOIN_FIELDS": [], "METHOD": 0, "DISCARD_NONMATCHING": True, "PREFIX": "M_", "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    kept = _run(
        "native:joinattributestable",
        {"INPUT": cells, "FIELD": "CELLID", "INPUT_2": pts, "FIELD_2": "CELLID", "FIELDS_TO_COPY": ["CELLID"], "METHOD": 1, "DISCARD_NONMATCHING": True, "PREFIX": "K_", "OUTPUT": "TEMPORARY_OUTPUT"},
        context, feedback
    )["OUTPUT"]
    kept = _polys_only(kept, context, feedback)
    kept = _drop_null_tiny_polys(kept, 1e-9, context, feedback)
    kept = _add_empty_tag_fields(kept, y1, y2, context, feedback)
    kept = _as_layer(kept, context) or kept
    _topology_debug_save(kept, outdir, "FABRIC_kept_by_extent", y1, y2, context, feedback)
    if kept is None or not kept.isValid() or kept.featureCount() == 0:
        raise QgsProcessingException(f"[TOPO FABRIC] no cells retained inside mask for {y1}->{y2}")
    feedback.pushInfo(f"[TOPO FABRIC] retained fabric cells={kept.featureCount()} for {y1}->{y2}")
    return kept

# ---------------------- The Processing Algorithm ----------------------
class Module3_EAcalculation_QGIS(QgsProcessingAlgorithm):
    """
    Main QGIS Processing algorithm for Module 3 (Erosion/Accumulation).
    Implements the full SCS Toolbox EA logic, including:
      - island-aware and 'stable_floodplain' vs 'inactive_floodplain'
      - LEFT/RIGHT side masks from per-date centrelines
      - direction + migration classification
      - optional per-segment rate statistics
      - all outputs in a single GPKG (one layer per date pair).
    """

    # ---- Parameter keys (used to define and retrieve parameter values) ----
    # Keep these parameter identifiers stable: QGIS saved models and batch jobs depend on them.
    PARAM_OUTFOLDER = "OUTPUT_FOLDER"
    PARAM_CHAN = "CHANNEL_POLYGONS"
    PARAM_CEN = "CENTRELINES"
    PARAM_FIELD_YEAR = "FIELD_YEAR"
    PARAM_FIELD_CENYEAR = "CENTERLINE_YEAR_FIELD"
    PARAM_STATS = "STATISTICS"
    PARAM_INTERVAL = "INTERVAL"
    PARAM_DELETE_TEMP = "DELETE_TEMP"
    PARAM_WATER = "WATER_POLYGONS"
    PARAM_ACTIVE = "ACTIVE_ZONE_POLYGONS"
    PARAM_SURFACE_MODE = "SURFACE_MODE"
    PARAM_DEBUG_VERBOSE = "DEBUG_VERBOSE"
    PARAM_DEBUG_GPKG = "DEBUG_GPKG"
    PARAM_MIN_VALID_YEAR = "MIN_VALID_YEAR"
    PARAM_MAX_VALID_YEAR = "MAX_VALID_YEAR"
    PARAM_MAX_INTERVAL_YEARS = "MAX_INTERVAL_YEARS"
    #
    # ---------- QGIS boilerplate ----------
    # PURPOSE: Stable internal Processing algorithm ID; unchanged for compatibility with existing QGIS models.
    def name(self):
        return "module3a_ea_v15g_authoritative_states"

    # PURPOSE: Visible Processing Toolbox label; retains the established v15g description.
    def displayName(self):
        return "Module 3A — EA calculation (QGIS) – SCS Toolbox v15g authoritative states, events and risk sets"

    # PURPOSE: Visible Processing Toolbox group name.
    def group(self):
        return "SCS Toolbox"

    # PURPOSE: Stable provider-group ID used by QGIS Processing.
    def groupId(self):
        return "scs_toolbox"

    def shortHelpString(self):
        """
        Short help shown in the Processing Toolbox.
        """
        return (
            "Version 15g computes EA between successive dates from channel polygons and centrelines, with optional water + active-zone override.\n"
            "SCS-style island/inactive_floodplain logic, LEFT/RIGHT orientation, optional per-segment rates.\n"
            "Dates are checked across all features in each input layer; conflicting, future/out-of-range, duplicated, non-increasing or excessive-gap dates stop processing.\n"
            "Outputs a single GeoPackage with one layer per date-pair."
        )

    def createInstance(self):
        """
        Required factory method for QGIS Processing.
        """
        return Module3_EAcalculation_QGIS()

    def initAlgorithm(self, config=None):
        """
        Define input parameters and options for the Processing dialog.
        """
        # Output folder for final GeoPackage
        self.addParameter(
            QgsProcessingParameterFolderDestination(self.PARAM_OUTFOLDER, "Output folder")
        )

        # Channel polygon layers (one per date)
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_CHAN, "Channel polygons (one per date)", QgsProcessing.TypeVectorPolygon
            )
        )

        # Centreline layers (one per date)
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_CEN, "Centrelines (one per date)", QgsProcessing.TypeVectorLine
            )
        )

        # Optional low-stage water and active-zone polygons
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_WATER, "Low-stage water polygons (optional, one per date)", QgsProcessing.TypeVectorPolygon, optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.PARAM_ACTIVE, "Active-zone polygons (optional, one per date)", QgsProcessing.TypeVectorPolygon, optional=True
            )
        )

        # Field names for date/year
        self.addParameter(
            QgsProcessingParameterString(self.PARAM_FIELD_YEAR, "Channel year/date field (polygons)")
        )
        self.addParameter(
            QgsProcessingParameterString(self.PARAM_FIELD_CENYEAR, "Centreline year/date field (lines)")
        )

        # Chronology safeguards. These stop syntactically valid but implausible
        # values such as 2099 from entering the EA record unnoticed.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MIN_VALID_YEAR,
                "Minimum valid observation year",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1800,
                minValue=1000,
                maxValue=2500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MAX_VALID_YEAR,
                "Maximum valid observation year",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=date.today().year,
                minValue=1000,
                maxValue=2500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MAX_INTERVAL_YEARS,
                "Maximum permitted interval between observations (years)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=50.0,
                minValue=0.01,
                maxValue=500.0,
            )
        )
        
        self.PARAM_CH_WIDTH = "CHANNEL_WIDTH"
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_CH_WIDTH,
                "Channel width (m) for scaling tolerances (0 = fallback)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=100000.0
            )
        )


        # Optional statistics segments layer (for rates per segment/polygon)
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_STATS, "Statistics/segments layer (optional)", optional=True
            )
        )

        # Segment spacing for normalising area-based rates to linear rates
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_INTERVAL,
                "Interval for rate normalisation",
                QgsProcessingParameterNumber.Double,
                1.0,
            )
        )
        # Digitising tolerance: buffer applied to each channel polygon before EA tagging
        self.PARAM_DIGI_TOL = "DIGITISING_TOLERANCE"
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_DIGI_TOL,
                "Digitising tolerance / mapping gap tolerance (metres)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=100.0
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_DEBUG_VERBOSE, "Verbose debug logging", defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_DEBUG_GPKG, "Write debug GeoPackages", defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_SURFACE_MODE,
                "Surface mode (0=Mamore water-led, 1=Jamuna water+active)",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=0,
                maxValue=1
            )
        )

        # Flag to delete intermediates at the end (currently not deeply used here,
        # but kept for UI/theme compatibility)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARAM_DELETE_TEMP, "Delete debug information/intermediates when done", defaultValue=True
            )
        )
        
    # Execution orchestrates chronology validation, surface preparation, paired EA overlays,
    # state-support reconciliation, lateral orientation, QA and final GeoPackage writing.
    def processAlgorithm(self, parameters, context, feedback):
        """
        Main execution entry point for the EA module.
        Steps:
        0) Resolve inputs
        1) Parse years and pair polygon/centreline by year
        2) Build hole-free envelopes + island-aware EA layers
        3) For each pair of successive years, compute ArcPro-faithful EA classification
           and orientation masks, then direction/migration and per-pair outputs.
        4) (Optional) intersect with segments and compute EA rates.
        """

        # ------------------------------------------------------------------
        # ✅ Correction 1: resolve delete_temp once and set DEBUG_SAVE once
        # ------------------------------------------------------------------
        delete_temp = self.parameterAsBool(parameters, self.PARAM_DELETE_TEMP, context)
        debug_verbose = self.parameterAsBool(parameters, self.PARAM_DEBUG_VERBOSE, context)
        debug_gpkg = self.parameterAsBool(parameters, self.PARAM_DEBUG_GPKG, context)

        global DEBUG_SAVE, DEBUG_TRACE, WRITE_DEBUG_GPKG
        DEBUG_TRACE = bool(debug_verbose)
        # Debug GeoPackages are written to the selected output folder, not to the
        # disposable processing temp folder, so keep them enabled when requested
        # even if DELETE_TEMP is True. DELETE_TEMP should only affect temporary
        # Processing artefacts, not deliberate diagnostics.
        WRITE_DEBUG_GPKG = bool(debug_gpkg)
        DEBUG_SAVE = WRITE_DEBUG_GPKG
        if feedback:
            feedback.pushInfo(f"[DEBUG] verbose={DEBUG_TRACE} debug_gpkg={WRITE_DEBUG_GPKG} delete_temp={bool(delete_temp)}")
            if WRITE_DEBUG_GPKG and delete_temp:
                feedback.pushInfo("[DEBUG] Debug GeoPackages will still be written because DEBUG_GPKG=True; DELETE_TEMP only removes temporary Processing artefacts.")

        # --- Parameter extraction ---
        outdir = self.parameterAsString(parameters, self.PARAM_OUTFOLDER, context)
        raw_water = self.parameterAsLayerList(parameters, self.PARAM_WATER, context)
        raw_active = self.parameterAsLayerList(parameters, self.PARAM_ACTIVE, context)
        surface_mode = int(self.parameterAsInt(parameters, self.PARAM_SURFACE_MODE, context))
        field_year = self.parameterAsString(parameters, self.PARAM_FIELD_YEAR, context)
        field_cen_year = self.parameterAsString(parameters, self.PARAM_FIELD_CENYEAR, context)
        min_valid_year = int(self.parameterAsInt(parameters, self.PARAM_MIN_VALID_YEAR, context))
        max_valid_year = int(self.parameterAsInt(parameters, self.PARAM_MAX_VALID_YEAR, context))
        max_interval_years = float(self.parameterAsDouble(parameters, self.PARAM_MAX_INTERVAL_YEARS, context))
        if max_valid_year < min_valid_year:
            raise QgsProcessingException(
                f"Maximum valid year ({max_valid_year}) is earlier than minimum valid year ({min_valid_year})."
            )
        feedback.pushInfo(
            f"[DATE QA] permitted years={min_valid_year}–{max_valid_year}; "
            f"maximum interval={max_interval_years:g} years"
        )
        stats = self.parameterAsVectorLayer(parameters, self.PARAM_STATS, context)
        interval = self.parameterAsDouble(parameters, self.PARAM_INTERVAL, context)
        buffer_tol = self.parameterAsDouble(parameters, self.PARAM_DIGI_TOL, context)
        feedback.pushInfo(f"[PARAM] Digitising tolerance = {buffer_tol} m")

        channel_width = self.parameterAsDouble(parameters, self.PARAM_CH_WIDTH, context)
        S = _scale_params(channel_width)
        min_area = float(S["min_area"]) 
        feedback.pushInfo(
            f"[PARAM] Width={channel_width}m -> snap={S['snap']} grid={S['grid']} "
            f"min_area={S['min_area']} side={S['side']}"
        )

        _ensure_folder(outdir)   # Make sure output folder exists
        _written_once = set()    # Keep track of which (gpkg, layer) we've written already

        feedback.pushInfo("STEP 0: Resolving inputs...")

        # Resolve multiple polygon and centreline inputs as valid layers
        raw_chans = self.parameterAsLayerList(parameters, self.PARAM_CHAN, context)
        raw_cens  = self.parameterAsLayerList(parameters, self.PARAM_CEN,  context)

        chans, cens = [], []
        # Convert raw channel references to layers, logging result
        for idx, obj in enumerate(raw_chans):
            lyr = _as_layer(obj, context)
            feedback.pushInfo(f"[CHAN {idx}] {obj} → {'OK' if (lyr and lyr.isValid()) else 'INVALID'}")
            if lyr and lyr.isValid():
                chans.append(lyr)
        # Convert raw centreline references to layers, logging result
        for idx, obj in enumerate(raw_cens):
            lyr = _as_layer(obj, context)
            feedback.pushInfo(f"[CEN  {idx}] {obj} → {'OK' if (lyr and lyr.isValid()) else 'INVALID'}")
            if lyr and lyr.isValid():
                cens.append(lyr)

        if not chans or not cens:
            raise QgsProcessingException("Provide at least one channel polygon and one centreline.")
        # ------------------------------------------------------------
        # Establish reference CRS early from original polygon inputs
        # ------------------------------------------------------------
        ref_src = _as_layer(chans[0], context)
        if ref_src is None or not ref_src.isValid():
            raise QgsProcessingException("Could not determine reference CRS from first channel polygon.")

        ref_crs_obj = ref_src.crs()
        if ref_crs_obj is None or not ref_crs_obj.isValid():
            raise QgsProcessingException("First channel polygon has no valid CRS.")

        ref_crs_authid = ref_crs_obj.authid()
        if not ref_crs_authid:
            raise QgsProcessingException("First channel polygon CRS has empty authid.")

        feedback.pushInfo(f"[CRS] Early reference CRS = {ref_crs_authid}")
        # ---- STEP 1: Parse years and pair by YEAR ----
        feedback.pushInfo("STEP 1: Read inputs, parse years, and pair by matching year")

        # PURPOSE: Detect missing or empty observation-date values before chronology validation.
        def _date_value_is_blank(raw):
            if raw is None:
                return True
            try:
                if hasattr(raw, "isNull") and raw.isNull():
                    return True
            except Exception:
                pass
            txt = str(raw).strip()
            return txt == "" or txt.upper() in {"NULL", "NONE", "<NULL>"}

        # PURPOSE: Reject date layers with inconsistent or missing date observations.
        def _validate_layer_ymd(ymd, layer_name, source_description):
            try:
                dt = datetime.strptime(str(ymd), "%Y%m%d")
            except Exception as exc:
                raise QgsProcessingException(
                    f"[DATE QA] {layer_name}: invalid calendar date {ymd!r} "
                    f"from {source_description}: {exc}"
                )
            if not (min_valid_year <= dt.year <= max_valid_year):
                raise QgsProcessingException(
                    f"[DATE QA] {layer_name}: date {dt.strftime('%Y-%m-%d')} from "
                    f"{source_description} falls outside the permitted range "
                    f"{min_valid_year}–{max_valid_year}."
                )
            return dt.strftime("%Y%m%d")

        def _year_ymd_from_layer(layer, fieldname, role):
            """
            Derive one authoritative date from all nonblank feature values.

            A layer is rejected when its selected date field contains conflicting
            parseable dates or nonblank unparseable values. The selected attribute
            field is authoritative; layer names and source paths are never used as
            silent date fallbacks.
            """
            names = layer.fields().names()
            if fieldname not in names:
                raise QgsProcessingException(
                    f"[DATE QA] {role} layer '{layer.name()}' does not contain "
                    f"the selected date field '{fieldname}'."
                )

            unique_ymd = set()
            blank_count = 0
            invalid_examples = []
            feature_count = 0

            for feat in layer.getFeatures():
                feature_count += 1
                raw = feat[fieldname]
                if _date_value_is_blank(raw):
                    blank_count += 1
                    continue
                ymd = _yyyymmdd_from_value_lenient(raw)
                if not ymd:
                    if len(invalid_examples) < 5:
                        invalid_examples.append(repr(str(raw)))
                    continue
                ymd = _validate_layer_ymd(ymd, layer.name(), f"field '{fieldname}'")
                unique_ymd.add(ymd)

            if invalid_examples:
                raise QgsProcessingException(
                    f"[DATE QA] {role} layer '{layer.name()}' contains nonblank "
                    f"unparseable values in '{fieldname}'. Examples: "
                    + ", ".join(invalid_examples)
                )

            if len(unique_ymd) > 1:
                vals = ", ".join(sorted(unique_ymd))
                raise QgsProcessingException(
                    f"[DATE QA] {role} layer '{layer.name()}' contains conflicting "
                    f"dates in '{fieldname}': {vals}. Each input layer must represent "
                    f"one observation date."
                )

            if unique_ymd:
                ymd = next(iter(unique_ymd))
                if blank_count:
                    feedback.reportError(
                        f"[DATE QA] {role} layer '{layer.name()}': {blank_count:,} of "
                        f"{feature_count:,} feature(s) have blank '{fieldname}' values; "
                        f"using the single consistent nonblank date {ymd}."
                    )
                feedback.pushInfo(
                    f"[DATE QA] {role} layer '{layer.name()}': authoritative date={ymd}; "
                    f"unique nonblank dates=1"
                )
                return int(ymd[:4]), ymd

            raise QgsProcessingException(
                f"[DATE QA] {role} layer '{layer.name()}' has no parseable date in "
                f"the selected field '{fieldname}'. Populate that field explicitly; "
                f"dates are not inferred from layer names or source paths."
            )

        poly_by_year, cen_by_year = {}, {}

        for ch in chans:
            year_key, ymd = _year_ymd_from_layer(ch, field_year, "channel polygon")
            if year_key is None:
                feedback.reportError(f"[POLY] No parsable year for {ch.name()}; skipping this layer.")
                continue

            if year_key in poly_by_year:
                prev = poly_by_year[year_key]["name"]
                raise QgsProcessingException(
                    f"Duplicate polygon year detected ({year_key}).\n"
                    f"Already have: {prev}\n"
                    f"Also got   : {ch.name()}\n\n"
                    "Select only ONE reach (A or B) for each year, or rename/split inputs."
                )

            poly_by_year[year_key] = {"layer": ch, "ymd": ymd, "name": ch.name()}

        for ce in cens:
            year_key, ymd = _year_ymd_from_layer(ce, field_cen_year, "centreline")
            if year_key is None:
                feedback.reportError(f"[CEN] No parsable year for {ce.name()}; skipping this layer.")
                continue

            if year_key in cen_by_year:
                prev = cen_by_year[year_key]["name"]
                raise QgsProcessingException(
                    f"Duplicate centreline year detected ({year_key}).\n"
                    f"Already have: {prev}\n"
                    f"Also got   : {ce.name()}\n\n"
                    "Select only ONE reach (A or B) for each year, or rename/split inputs."
                )

            cen_by_year[year_key] = {"layer": ce, "ymd": ymd, "name": ce.name()}

        years_poly = sorted(poly_by_year.keys())
        years_cen  = sorted(cen_by_year.keys())
        common_years = sorted(set(years_poly).intersection(years_cen))

        miss_cen = sorted(set(years_poly) - set(years_cen))
        miss_poly = sorted(set(years_cen) - set(years_poly))
        if miss_cen:
            feedback.reportError(f"Years present in polygons but missing in centrelines: {miss_cen}")
        if miss_poly:
            feedback.reportError(f"Years present in centrelines but missing in polygons: {miss_poly}")
        if len(common_years) < 2:
            raise QgsProcessingException("Need at least two matching years to compute E/A between dates.")

        feedback.pushInfo(f"Years (polys): {years_poly}")
        feedback.pushInfo(f"Years (cens) : {years_cen}")
        feedback.pushInfo(f"Common years : {common_years}")

        # Require the polygon and centreline for each observation to carry the
        # same full date, then validate the complete chronology before any
        # geometry processing begins.
        chronology_dates = []
        for year_key in common_years:
            ch_ymd = poly_by_year[year_key]["ymd"]
            ce_ymd = cen_by_year[year_key]["ymd"]
            if ch_ymd != ce_ymd:
                raise QgsProcessingException(
                    f"[DATE QA] Polygon/centreline date mismatch for {year_key}: "
                    f"polygon={ch_ymd}, centreline={ce_ymd}. The paired layers must "
                    f"represent the same observation date."
                )
            chronology_dates.append(datetime.strptime(ch_ymd, "%Y%m%d"))

        for prev_dt, next_dt in zip(chronology_dates, chronology_dates[1:]):
            if next_dt <= prev_dt:
                raise QgsProcessingException(
                    f"[DATE QA] Observation chronology is not strictly increasing: "
                    f"{prev_dt:%Y-%m-%d} then {next_dt:%Y-%m-%d}."
                )
            gap_years = (next_dt - prev_dt).days / 365.2425
            if gap_years > max_interval_years:
                raise QgsProcessingException(
                    f"[DATE QA] Interval {prev_dt:%Y-%m-%d} to {next_dt:%Y-%m-%d} "
                    f"is {gap_years:.2f} years, exceeding the permitted maximum of "
                    f"{max_interval_years:g} years."
                )

        feedback.pushInfo(
            "[DATE QA] Validated chronology: "
            + " < ".join(dt.strftime("%Y-%m-%d") for dt in chronology_dates)
        )

        CH_list, CEN_list = [], []
        years_polys, years_cens, date_objs_polys = [], [], []

        for year_key in common_years:
            ch_info = poly_by_year[year_key]
            ce_info = cen_by_year[year_key]
            feedback.pushInfo(f"Pairing year {year_key}: {ch_info['name']} ↔ {ce_info['name']}")

            ch_tmp = _freeze_to_tmp_gpkg(
                ch_info["layer"], context, feedback, f"ch_{ch_info['ymd']}", ref_crs_obj
            )
            ce_tmp = _freeze_to_tmp_gpkg(
                ce_info["layer"], context, feedback, f"cen_{ce_info['ymd']}", ref_crs_obj
            )

            # Belt-and-braces CRS enforcement after freeze/reload
            if ch_tmp is None or not ch_tmp.isValid():
                raise QgsProcessingException(f"[PAIRING] frozen channel invalid for {ch_info['ymd']}")
            if ce_tmp is None or not ce_tmp.isValid():
                raise QgsProcessingException(f"[PAIRING] frozen centreline invalid for {ce_info['ymd']}")

            if ch_tmp.crs() is None or not ch_tmp.crs().isValid():
                ch_tmp.setCrs(ref_crs_obj)
                feedback.pushInfo(
                    f"[PAIRING CRS] restored channel CRS for {ch_info['ymd']} -> {ref_crs_obj.authid()}"
                )

            if ce_tmp.crs() is None or not ce_tmp.crs().isValid():
                ce_tmp.setCrs(ref_crs_obj)
                feedback.pushInfo(
                    f"[PAIRING CRS] restored centreline CRS for {ce_info['ymd']} -> {ref_crs_obj.authid()}"
                )

            feedback.pushInfo(
                f"[PAIRING CRS] {ch_info['ymd']} "
                f"CH={ch_tmp.crs().authid() if ch_tmp.crs().isValid() else '<invalid>'} ; "
                f"CEN={ce_tmp.crs().authid() if ce_tmp.crs().isValid() else '<invalid>'}"
            )

            CH_list.append(ch_tmp)
            CEN_list.append(ce_tmp)
            years_polys.append(ch_info["ymd"])
            years_cens.append(ce_info["ymd"])
            date_objs_polys.append(datetime.strptime(ch_info["ymd"], "%Y%m%d"))

        feedback.pushInfo(f"[DEBUG] Step1 lengths: CH={len(CH_list)} CEN={len(CEN_list)} years={len(years_polys)}")
        feedback.pushInfo(f"[DEBUG] years_polys = {years_polys}")

        # ---- STEP 2: Build hole-free envelopes + island-aware layers ----
        feedback.pushInfo("STEP 2: Build hole-free envelopes and island tags")
        POL_list, ISL_list = [], []

        for i, ch_path in enumerate(CH_list):
            ymd = years_polys[i]

            feedback.pushInfo(f"[DEBUG] STEP2 i={i} ymd={ymd} ch_ref={ch_path}")

            ch = _as_layer(ch_path, context)
            if ch is None or not ch.isValid():
                feedback.reportError(f"[STEP2] CH_list[{i}] invalid ({ch_path}); skipping.")
                continue

            if ch.featureCount() == 0:
                feedback.reportError(f"[STEP2] CH_list[{i}] empty ({ch_path}); skipping.")
                continue

            # ------------------------------------------------------------------
            # 1) Clean source channel polygons
            # ------------------------------------------------------------------
            ch_fix = _run(
                "native:fixgeometries",
                {"INPUT": ch, "METHOD": 1, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            ch_fix = _drop_null_tiny_polys(ch_fix, 1e-6, context, feedback)

            ch_fix_lyr = _as_layer(ch_fix, context)
            if ch_fix_lyr is None or not ch_fix_lyr.isValid() or ch_fix_lyr.featureCount() == 0:
                feedback.reportError(f"[STEP2] fixed channel empty/invalid for {ymd}; skipping.")
                continue

            # ------------------------------------------------------------------
            # 2) Dissolve to one multipart channel body
            # ------------------------------------------------------------------
            ch_diss = _run(
                "native:dissolve",
                {
                    "INPUT": ch_fix,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            ch_diss = _drop_null_tiny_polys(ch_diss, 1e-6, context, feedback)

            ch_diss_lyr = _as_layer(ch_diss, context)
            if ch_diss_lyr is None or not ch_diss_lyr.isValid() or ch_diss_lyr.featureCount() == 0:
                feedback.reportError(f"[STEP2] dissolved channel empty/invalid for {ymd}; skipping.")
                continue

            # ------------------------------------------------------------------
            # 2b) DEBUG: dissolved geometry + raw holes
            # ------------------------------------------------------------------
            _dbg_save_layer(
                ch_diss, outdir,
                f"DBG2_DISS_{ymd}.gpkg", f"DISS_{ymd}",
                context, feedback
            )

            _dbg_extract_holes(
                ch_diss,
                outdir,
                f"DBG2_HOLES_{ymd}.gpkg",
                f"HOLES_{ymd}",
                context,
                feedback
            )

            # ------------------------------------------------------------------
            # 3) Build hole-free envelope
            # ------------------------------------------------------------------
            hole_min_area = 0.0

            ch_env = _run(
                "native:deleteholes",
                {
                    "INPUT": ch_diss,
                    "MIN_AREA": hole_min_area,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            ch_env = _drop_null_tiny_polys(ch_env, 1e-6, context, feedback)

            ch_env_lyr = _as_layer(ch_env, context)
            if ch_env_lyr is None or not ch_env_lyr.isValid() or ch_env_lyr.featureCount() == 0:
                feedback.reportError(f"[STEP2] envelope empty/invalid for {ymd}; skipping.")
                continue

            _dbg_save_layer(
                ch_env, outdir,
                f"DBG2_ENV_{ymd}.gpkg", f"ENV_{ymd}",
                context, feedback
            )

            _dbg_save_layer(ch,     outdir, f"DBG2_CH_{ymd}.gpkg",  f"CH_{ymd}",  context, feedback)
            _dbg_save_layer(ch_fix, outdir, f"DBG2_FIX_{ymd}.gpkg", f"FIX_{ymd}", context, feedback)

            feedback.pushInfo(
                f"[STEP2 DBG] {ymd}: ch={ch.featureCount()} "
                f"fix={ch_fix_lyr.featureCount()} "
                f"diss={ch_diss_lyr.featureCount()} "
                f"env={ch_env_lyr.featureCount()} "
                f"hole_min_area={hole_min_area}"
            )

            # ------------------------------------------------------------------
            # 4) Production island semantics
            #
            # Authoritative logic:
            #   - channel tagging uses CORE geometry only
            #   - islands are built by subtraction: envelope - core channel
            #   - raw holes are extracted ONLY for diagnostics / verification
            #
            # Optional tolerance:
            #   if buffer_tol > 0, use it ONLY for island geometry construction
            #   (not for channel tagging)
            # ------------------------------------------------------------------
            ch_core = ch_fix

            # Diagnostic only: actual hole footprint from dissolved geometry
            holes_raw = _extract_holes_as_layer(ch_diss, context, feedback)
            if holes_raw is None:
                feedback.pushInfo(f"[STEP2] No holes found for {ymd}; creating empty holes layer.")
                holes_raw = QgsVectorLayer(
                    f"Polygon?crs={ref_crs_obj.authid()}",
                    f"holes_{ymd}",
                    "memory"
                )
            holes_raw = _drop_null_tiny_polys(holes_raw, 1e-6, context, feedback)

                        # Optional tolerance buffer for ISLAND VALIDATION only
            # IMPORTANT:
            #   - buffer is NOT used to define final island geometry
            #   - final islands come from raw holes only
            if buffer_tol > 0.0:
                ch_island_cut = _run(
                    "native:buffer",
                    {
                        "INPUT": ch_core,
                        "DISTANCE": buffer_tol,
                        "SEGMENTS": 8,
                        "END_CAP_STYLE": 0,
                        "JOIN_STYLE": 0,
                        "MITER_LIMIT": 2.0,
                        "DISSOLVE": True,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                feedback.pushInfo(
                    f"[STEP2] Built {buffer_tol} m tolerance buffer for island validation only ({ymd})."
                )
            else:
                ch_island_cut = ch_core
                feedback.pushInfo(f"[STEP2] No tolerance buffer for {ymd} (tolerance = 0).")

            ch_island_cut = _drop_null_tiny_polys(ch_island_cut, 1e-6, context, feedback)

            # ------------------------------------------------------------------
            # 5) PRODUCTION islands = RAW EXTRACTED HOLES, PRESERVED AS FEATURES
            #
            # Log diagnosis from the Jamuna 1987-1988 test showed that raw hole
            # extraction worked (73 and 84 hole polygons), but the later
            # envelope-minus-core reconstruction collapsed those islands into one
            # MultiPolygon. That multipart reconstruction removed important
            # boundaries from the pairwise fabric and produced missing
            # stable_island / island_erosion / island_deposition areas.
            #
            # Therefore production islands are now the extracted interior rings
            # themselves. Do not rebuild them with envelope - active_core and do
            # not dissolve them. Keeping each hole as an individual polygon is
            # essential for both braided Jamuna inputs and any meandering input
            # with real in-channel islands. If Mamoré has no holes, this simply
            # creates an empty island layer.
            # ------------------------------------------------------------------
            holes_raw_lyr = _as_layer(holes_raw, context)

            if holes_raw_lyr is not None and holes_raw_lyr.isValid() and holes_raw_lyr.featureCount() > 0:
                islands = holes_raw
                islands = _drop_null_tiny_polys(islands, 1e-6, context, feedback)
                # Ensure multipart geometries, if any, are split into separate
                # features. This preserves topology for boundary-line
                # polygonisation and avoids a single island MultiPolygon acting
                # as one coarse support object during tag assignment.
                try:
                    islands = _run(
                        "native:multiparttosingleparts",
                        {"INPUT": islands, "OUTPUT": "TEMPORARY_OUTPUT"},
                        context, feedback
                    )["OUTPUT"]
                    islands = _drop_null_tiny_polys(islands, 1e-6, context, feedback)
                except Exception as e:
                    feedback.reportError(f"[STEP2] multipart-to-singleparts for raw islands failed for {ymd}; continuing with raw holes. Error: {e}")
                feedback.pushInfo(f"[STEP2] Using raw extracted holes as production islands for {ymd}; no envelope-core reconstruction or dissolve.")
            else:
                feedback.pushInfo(f"[STEP2] No island holes available for {ymd}; islands empty.")
                islands = QgsVectorLayer(
                    f"Polygon?crs={ref_crs_obj.authid()}",
                    f"islands_{ymd}",
                    "memory"
                )

            islands_on_holes = islands

            try:
                isl_fc_dbg = (_as_layer(islands, context) or islands).featureCount()
            except Exception:
                isl_fc_dbg = -1
            try:
                holes_fc_dbg = holes_raw_lyr.featureCount() if holes_raw_lyr and holes_raw_lyr.isValid() else 0
            except Exception:
                holes_fc_dbg = -1
            feedback.pushInfo(
                f"[STEP2 ISLANDS] {ymd}: raw_holes={holes_fc_dbg}, production_islands={isl_fc_dbg}"
            )

            _dbg_save_layer(
                holes_raw, outdir,
                f"DBG2_HOLESRAW_{ymd}.gpkg", f"HOLESRAW_{ymd}",
                context, feedback
            )
            _dbg_save_layer(
                ch_island_cut, outdir,
                f"DBG2_CHTOL_{ymd}.gpkg", f"CHTOL_{ymd}",
                context, feedback
            )
            _dbg_save_layer(
                islands, outdir,
                f"DBG2_ISLANDS_{ymd}.gpkg", f"ISLANDS_{ymd}",
                context, feedback
            )
            _dbg_save_layer(
                islands_on_holes, outdir,
                f"DBG2_ISLANDS_ON_HOLES_{ymd}.gpkg", f"ISLANDS_ON_HOLES_{ymd}",
                context, feedback
            )

            # ------------------------------------------------------------------
            # 6) Tag channel as CORE MINUS FINAL ISLANDS
            # ------------------------------------------------------------------
            islands_lyr = _as_layer(islands, context)

            if islands_lyr is not None and islands_lyr.isValid() and islands_lyr.featureCount() > 0:
                ch_tag_geom = _safe_polygon_difference(ch_core, islands, context, feedback)
                ch_tag_geom = _drop_null_tiny_polys(ch_tag_geom, 1e-6, context, feedback)
            else:
                ch_tag_geom = ch_core

            chan_tag = _add_const_field(ch_tag_geom, f"y_{ymd}", f"'{ymd}'", 2, 16, 0, context, feedback)
            chan_tag = _add_const_field(chan_tag, f"T_{ymd}", "'channel'", 2, 16, 0, context, feedback)

            # ------------------------------------------------------------------
            # 7) Tag subtraction-based production islands
            # For Active = low-stage water + reworked sand, enclosed interior
            # holes are treated as island / in-channel land, not floodplain.
            # ------------------------------------------------------------------
            isl_tag = _add_const_field(islands, f"y_{ymd}", f"'{ymd}'", 2, 16, 0, context, feedback)
            isl_tag = _add_const_field(isl_tag, f"T_{ymd}", "'island'", 2, 16, 0, context, feedback)
            
            # ------------------------------------------------------------------
            # 7b) Remove nuisance slivers BEFORE merge
            # ------------------------------------------------------------------
            sliver_min = max(1.0, S["min_area"] * 0.0001)

            chan_tag_before = (_as_layer(chan_tag, context) or chan_tag).featureCount() if (_as_layer(chan_tag, context) or chan_tag) else -1
            isl_tag_before  = (_as_layer(isl_tag, context) or isl_tag).featureCount() if (_as_layer(isl_tag, context) or isl_tag) else -1

            chan_tag = _drop_null_tiny_polys(chan_tag, sliver_min, context, feedback)
            isl_tag  = _drop_null_tiny_polys(isl_tag,  sliver_min, context, feedback)

            chan_tag_after = (_as_layer(chan_tag, context) or chan_tag).featureCount() if (_as_layer(chan_tag, context) or chan_tag) else -1
            isl_tag_after  = (_as_layer(isl_tag, context) or isl_tag).featureCount() if (_as_layer(isl_tag, context) or isl_tag) else -1

            feedback.pushInfo(
                f"[STEP2 SLIVER] {ymd}: min_area={sliver_min} "
                f"chan {chan_tag_before}->{chan_tag_after}, "
                f"isl {isl_tag_before}->{isl_tag_after}"
            )

            # ------------------------------------------------------------------
            # 8) Merge channel + islands into ONE EA base for this date
            #    Safe merge:
            #      - diagnose inputs
            #      - handle one-sided cases directly
            #      - for 2-sided merge, strip PK/provider baggage first
            #      - freeze cleaned inputs to file-backed layers
            #      - then merge
            #      - diagnose merged/clean/final outputs
            # ------------------------------------------------------------------
            chan_tag_lyr = _as_layer(chan_tag, context) or chan_tag
            isl_tag_lyr  = _as_layer(isl_tag, context) or isl_tag

            ch_fc = chan_tag_lyr.featureCount() if chan_tag_lyr and chan_tag_lyr.isValid() else -1
            is_fc = isl_tag_lyr.featureCount()  if isl_tag_lyr  and isl_tag_lyr.isValid()  else -1

            feedback.pushInfo(f"[STEP2 MERGE] {ymd}: chan_tag fc={ch_fc}, isl_tag fc={is_fc}")

            # ---- DEBUG: inspect both inputs before merge ----
            _dbg_layer(f"chan_tag {ymd}", chan_tag_lyr, context, feedback, sample_n=3)
            _dbg_extent(f"chan_tag {ymd}", chan_tag_lyr, context, feedback)
            _dbg_feature_bboxes(f"chan_tag {ymd}", chan_tag_lyr, context, feedback, n=5)

            _dbg_layer(f"isl_tag {ymd}", isl_tag_lyr, context, feedback, sample_n=3)
            _dbg_extent(f"isl_tag {ymd}", isl_tag_lyr, context, feedback)
            _dbg_feature_bboxes(f"isl_tag {ymd}", isl_tag_lyr, context, feedback, n=5)
            # ---- END DEBUG ----

            # Case 1: both invalid/empty
            if (chan_tag_lyr is None or not chan_tag_lyr.isValid() or ch_fc == 0) and \
            (isl_tag_lyr is None or not isl_tag_lyr.isValid() or is_fc == 0):
                feedback.reportError(f"[STEP2] chan_tag and isl_tag both empty/invalid for {ymd}; skipping.")
                continue

            # Case 2a: only channel side has content
            elif chan_tag_lyr is not None and chan_tag_lyr.isValid() and ch_fc > 0 and \
                (isl_tag_lyr is None or not isl_tag_lyr.isValid() or is_fc == 0):
                EA_tagged = _freeze_to_tmp_gpkg(
                    _strip_pk_fields(chan_tag_lyr, context, feedback),
                    context, feedback, f"EA_tagged_{ymd}", ref_crs_obj
                )
                feedback.pushInfo(f"[STEP2 MERGE] {ymd}: using chan_tag only.")

            elif isl_tag_lyr is not None and isl_tag_lyr.isValid() and is_fc > 0 and \
                (chan_tag_lyr is None or not chan_tag_lyr.isValid() or ch_fc == 0):
                EA_tagged = _freeze_to_tmp_gpkg(
                    _strip_pk_fields(isl_tag_lyr, context, feedback),
                    context, feedback, f"EA_tagged_{ymd}", ref_crs_obj
                )
                feedback.pushInfo(f"[STEP2 MERGE] {ymd}: using isl_tag only.")

            # Case 3: both have content -> safe merge
            else:
                # Strip primary-key/provider baggage before merge
                chan_tag_m = _strip_pk_fields(chan_tag_lyr, context, feedback)
                isl_tag_m  = _strip_pk_fields(isl_tag_lyr,  context, feedback)

                # Drop helper/provider fields that can also cause trouble in merged temp outputs
                for fld in ["path", "layer", "OLD_FID"]:
                    chan_tag_m = _delete_field_if_exists(chan_tag_m, fld, context, feedback)
                    isl_tag_m  = _delete_field_if_exists(isl_tag_m,  fld, context, feedback)

                # Freeze both sides as clean file-backed layers before merge
                chan_tag_m = _freeze_to_tmp_gpkg(
                    chan_tag_m, context, feedback, f"chantag_{ymd}", ref_crs_obj
                )
                isl_tag_m = _freeze_to_tmp_gpkg(
                    isl_tag_m, context, feedback, f"isltag_{ymd}", ref_crs_obj
                )

                # Diagnose stripped/frozen inputs too
                _dbg_layer(f"chan_tag merge-ready {ymd}", chan_tag_m, context, feedback, sample_n=3)
                _dbg_extent(f"chan_tag merge-ready {ymd}", chan_tag_m, context, feedback)
                _dbg_feature_bboxes(f"chan_tag merge-ready {ymd}", chan_tag_m, context, feedback, n=5)

                _dbg_layer(f"isl_tag merge-ready {ymd}", isl_tag_m, context, feedback, sample_n=3)
                _dbg_extent(f"isl_tag merge-ready {ymd}", isl_tag_m, context, feedback)
                _dbg_feature_bboxes(f"isl_tag merge-ready {ymd}", isl_tag_m, context, feedback, n=5)

                EA_tagged = _safe_feature_merge(
                    chan_tag_m,
                    isl_tag_m,
                    f"EA_tagged_{ymd}",
                    context,
                    feedback,
                    crs=ref_crs_obj
                )
                EA_tagged = _freeze_to_tmp_gpkg(
                    EA_tagged,
                    context,
                    feedback,
                    f"EA_tagged_merged_{ymd}",
                    ref_crs_obj
                )
            EA_tagged_lyr = _as_layer(EA_tagged, context) or EA_tagged
            pre_fc = EA_tagged_lyr.featureCount() if EA_tagged_lyr and EA_tagged_lyr.isValid() else -1
            feedback.pushInfo(f"[STEP2 MERGE] {ymd}: merged/pre-clean fc={pre_fc}")

            # ---- DEBUG: inspect merged layer before cleaning ----
            _dbg_layer(f"EA_tagged merged {ymd}", EA_tagged_lyr, context, feedback, sample_n=3)
            _dbg_extent(f"EA_tagged merged {ymd}", EA_tagged_lyr, context, feedback)
            _dbg_feature_bboxes(f"EA_tagged merged {ymd}", EA_tagged_lyr, context, feedback, n=5)
            # ---- END DEBUG ----

            if EA_tagged_lyr is None or not EA_tagged_lyr.isValid() or pre_fc == 0:
                feedback.reportError(f"[STEP2] EA_tagged invalid immediately after merge for {ymd}; skipping.")
                continue

            # Conservative clean: if filtering empties layer, helper returns original
            EA_clean = _drop_null_tiny_polys(EA_tagged, 1e-6, context, feedback)
            EA_clean = _freeze_to_tmp_gpkg(
                EA_clean,
                context,
                feedback,
                f"EA_tagged_clean_{ymd}",
                ref_crs_obj
            )
                        
            EA_clean_lyr = _as_layer(EA_clean, context) or EA_clean
            post_fc = EA_clean_lyr.featureCount() if EA_clean_lyr and EA_clean_lyr.isValid() else -1
            feedback.pushInfo(f"[STEP2 MERGE] {ymd}: post-clean fc={post_fc}")

            # ---- DEBUG: inspect cleaned layer ----
            _dbg_layer(f"EA_clean {ymd}", EA_clean_lyr, context, feedback, sample_n=3)
            _dbg_extent(f"EA_clean {ymd}", EA_clean_lyr, context, feedback)
            _dbg_feature_bboxes(f"EA_clean {ymd}", EA_clean_lyr, context, feedback, n=5)
            # ---- END DEBUG ----

            if EA_clean_lyr is not None and EA_clean_lyr.isValid() and post_fc > 0:
                EA_tagged = EA_clean
            else:
                raise QgsProcessingException(
                    f"[STEP2] cleaned EA_tagged invalid/empty for {ymd}; inspect chan_tag / isl_tag / merge"
                )

            EA_tagged_lyr = _as_layer(EA_tagged, context) or EA_tagged
            
            # ------------------------------------------------------------------
            # 8b) NORMALISE duplicate Step 2 tag fields from channel+island merge
            #     e.g. T_19870101 + T_19870101_2 -> one authoritative T_19870101
            # ------------------------------------------------------------------
            EA_tagged = _normalise_step2_tag_fields(EA_tagged, ymd, context, feedback)
            EA_tagged = _freeze_to_tmp_gpkg(
                EA_tagged,
                context,
                feedback,
                layer_name=f"EA_tagged_norm_{ymd}",
                ref_crs=ref_crs_obj
            )
            EA_tagged_lyr = _as_layer(EA_tagged, context) or EA_tagged

            # ---- DEBUG: final chosen layer passed downstream ----
            _dbg_layer(f"EA_tagged final {ymd}", EA_tagged_lyr, context, feedback, sample_n=3)
            _dbg_extent(f"EA_tagged final {ymd}", EA_tagged_lyr, context, feedback)
            _dbg_feature_bboxes(f"EA_tagged final {ymd}", EA_tagged_lyr, context, feedback, n=5)
            # ---- END DEBUG ----

            if EA_tagged_lyr is None or not EA_tagged_lyr.isValid() or EA_tagged_lyr.featureCount() == 0:
                feedback.reportError(f"[STEP2] EA_tagged empty/invalid for {ymd}; skipping.")
                continue

            # ------------------------------------------------------------------
            # 9) Append ONCE only -> keeps lists aligned
            # ------------------------------------------------------------------
            ch_env = _ensure_layer_crs(
                ch_env, ref_crs_obj, context, feedback, f"ENV_{ymd}"
            )
            EA_tagged = _ensure_layer_crs(
                EA_tagged, ref_crs_obj, context, feedback, f"EA_tagged_final_{ymd}"
            )

            POL_list.append(ch_env)
            ISL_list.append(EA_tagged)

            if DEBUG_SAVE:
                debug_ea_path = os.path.join(outdir, f"EA_tagged_{ymd}.shp")
                for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
                    p = os.path.splitext(debug_ea_path)[0] + ext
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception as e:
                            feedback.reportError(f"[DEBUG_SAVE] Could not delete {p}: {e}")
                feedback.pushInfo(f"[DEBUG_SAVE] Writing EA_tagged debug: {debug_ea_path}")
                _run(
                    "native:savefeatures",
                    {"INPUT": EA_tagged, "OUTPUT": debug_ea_path},
                    context, feedback
                )

        feedback.pushInfo(f"[DEBUG] STEP2 outputs: POL_list={len(POL_list)} ISL_list={len(ISL_list)}")

        try:
            raw0 = _as_layer(chans[0], context)
            feedback.pushInfo(f"[CRS DBG] original chans[0] valid={raw0.isValid() if raw0 else False}")
            feedback.pushInfo(
                f"[CRS DBG] original chans[0] CRS="
                f"{raw0.crs().authid() if raw0 and raw0.crs() and raw0.crs().isValid() else '<blank>'}"
            )
        except Exception as e:
            feedback.reportError(f"[CRS DBG] failed reading original channel CRS: {e}")

        try:
            frozen0 = _as_layer(CH_list[0], context)
            feedback.pushInfo(f"[CRS DBG] frozen CH_list[0] valid={frozen0.isValid() if frozen0 else False}")
            feedback.pushInfo(
                f"[CRS DBG] frozen CH_list[0] CRS="
                f"{frozen0.crs().authid() if frozen0 and frozen0.crs() and frozen0.crs().isValid() else '<blank>'}"
            )
        except Exception as e:
            feedback.reportError(f"[CRS DBG] failed reading frozen channel CRS: {e}")

        # ------------------------------------------------------------------
        # Harmonise CRS across all working lists
        # Blank CRS -> assign only
        # Different valid CRS -> reproject
        # ------------------------------------------------------------------
        POL_list_fixed = []
        CEN_list_fixed = []
        ISL_list_fixed = []

        n_triplets = min(len(POL_list), len(CEN_list), len(ISL_list))
        if not (len(POL_list) == len(CEN_list) == len(ISL_list)):
            feedback.reportError(
                f"[PAIRING] Step2 list mismatch before CRS harmonisation: "
                f"POL={len(POL_list)} CEN={len(CEN_list)} ISL={len(ISL_list)}; "
                f"processing first {n_triplets} aligned entries."
            )

        for idx in range(n_triplets):
            po = POL_list[idx]
            ce = CEN_list[idx]
            isl = ISL_list[idx]

            po_lyr = _as_layer(po, context) or po
            ce_lyr = _as_layer(ce, context) or ce
            isl_lyr = _as_layer(isl, context) or isl

            feedback.pushInfo(
                f"[CRS DBG POST-STEP2] i={idx} "
                f"POL={po_lyr.crs().authid() if po_lyr and po_lyr.isValid() and po_lyr.crs().isValid() else '<blank>'} "
                f"CEN={ce_lyr.crs().authid() if ce_lyr and ce_lyr.isValid() and ce_lyr.crs().isValid() else '<blank>'} "
                f"ISL={isl_lyr.crs().authid() if isl_lyr and isl_lyr.isValid() and isl_lyr.crs().isValid() else '<blank>'}"
            )

            po_lyr = _ensure_layer_crs(
                po_lyr, ref_crs_obj, context, feedback, f"pol_{idx}"
            )
            ce_lyr = _ensure_layer_crs(
                ce_lyr, ref_crs_obj, context, feedback, f"cen_{idx}"
            )
            isl_lyr = _ensure_layer_crs(
                isl_lyr, ref_crs_obj, context, feedback, f"isl_{idx}"
            )

            feedback.pushInfo(
                f"[CRS DBG POST-FIX] i={idx} "
                f"POL={po_lyr.crs().authid() if po_lyr and po_lyr.isValid() and po_lyr.crs().isValid() else '<blank>'} "
                f"CEN={ce_lyr.crs().authid() if ce_lyr and ce_lyr.isValid() and ce_lyr.crs().isValid() else '<blank>'} "
                f"ISL={isl_lyr.crs().authid() if isl_lyr and isl_lyr.isValid() and isl_lyr.crs().isValid() else '<blank>'}"
            )

            POL_list_fixed.append(po_lyr)
            CEN_list_fixed.append(ce_lyr)
            ISL_list_fixed.append(isl_lyr)

        POL_list = POL_list_fixed
        CEN_list = CEN_list_fixed
        ISL_list = ISL_list_fixed

        for _i in range(1, len(CEN_list)):
            CEN_list[_i] = _harmonize_centerline_direction(CEN_list[_i - 1], CEN_list[_i], context, feedback, tag=f"cen_{_i}")

        # Ensure all lists are aligned to same length; truncate if needed
        L_pol = len(POL_list)
        L_cen = len(CEN_list)
        L_isl = len(ISL_list)
        L_yp = len(years_polys)
        L_yc = len(years_cens)
        L_dp = len(date_objs_polys)

        k_len = min(L_pol, L_cen, L_isl, L_yp, L_yc, L_dp)

        if not (L_pol == L_cen == L_isl == L_yp == L_yc == L_dp):
            feedback.reportError(
                f"[PAIRING] Lengths differ after CRS harmonisation: "
                f"POL={L_pol} CEN={L_cen} ISL={L_isl} years_polys={L_yp} "
                f"years_cens={L_yc} dates={L_dp}; truncating to {k_len}."
            )

        POL_list = POL_list[:k_len]
        CEN_list = CEN_list[:k_len]
        ISL_list = ISL_list[:k_len]
        years_polys = years_polys[:k_len]
        years_cens = years_cens[:k_len]
        date_objs_polys = date_objs_polys[:k_len]

        if k_len < 2:
            raise QgsProcessingException("Not enough aligned dates after filtering (need ≥ 2).")

        # ---- Output container name/path ----
        gpkg_name = f"SCS_EA_{years_polys[0]}_{years_polys[-1]}.gpkg"
        gpkg_path = os.path.join(outdir, gpkg_name)
        feedback.pushInfo(f"Final GeoPackage: {gpkg_path}")

        if os.path.exists(gpkg_path):
            try:
                os.remove(gpkg_path)
            except Exception as e:
                feedback.reportError(f"[WRITE] Could not delete existing {gpkg_path}: {e}")

        EAprocess_outputs = []
        
        # ------------------------------------------------------------------
        # Pairwise helper functions (Module 4a integration)
        # ------------------------------------------------------------------
        
        def _add_pairwise_summary_fields(layer, y1, y2, pair_mode, surf_mode, context, feedback):
            """
            Add authoritative pairwise ontology fields for Module 4a / KM-AG.

            Design principle:
              - EA remains the generic geometric transition class.
              - Interpretation fields describe whether the surface belongs to the
                active morphodynamic domain or the stabilised/inactive domain.
              - Deposition is NOT treated as floodplain formation by default; it is
                active-domain deposition unless later persistence/stabilisation is
                demonstrated by the assemblage history in Module 4a.

            Requires final EA and T_y1 / T_y2 fields to exist.
            """
            lyr = _as_layer(layer, context) or layer
            if lyr is None or not lyr.isValid():
                raise QgsProcessingException("[PAIR SUMMARY] invalid layer")

            t1 = f"T_{y1}"
            t2 = f"T_{y2}"

            # PURPOSE: Create or update a text-valued QGIS expression field in the pairwise output.
            def _calc_text(src, field_name, formula, length=48):
                src_lyr = _as_layer(src, context) or src
                exists = src_lyr.fields().indexOf(field_name) != -1
                out = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": src_lyr,
                        "FIELD_NAME": field_name,
                        "FIELD_TYPE": 2,  # string
                        "FIELD_LENGTH": length,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": not exists,
                        "FORMULA": formula,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context,
                    feedback
                )["OUTPUT"]
                return _as_layer(out, context) or out

            # PURPOSE: Create or update an integer-valued QGIS expression field in the pairwise output.
            def _calc_int(src, field_name, formula):
                src_lyr = _as_layer(src, context) or src
                exists = src_lyr.fields().indexOf(field_name) != -1
                out = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": src_lyr,
                        "FIELD_NAME": field_name,
                        "FIELD_TYPE": 1,  # integer
                        "FIELD_LENGTH": 8,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": not exists,
                        "FORMULA": formula,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context,
                    feedback
                )["OUTPUT"]
                return _as_layer(out, context) or out

            field_names = lyr.fields().names()
            if t1 not in field_names or t2 not in field_names:
                feedback.reportError(
                    f"[PAIR SUMMARY] Missing tag fields. Expected {t1}, {t2}. "
                    f"Fields present: {field_names}"
                )

            out = lyr

            # Raw surface-state tags normalised for stable downstream use.
            out = _calc_text(out, "STATE_T1", f"lower(trim(coalesce(\"{t1}\", 'unknown')))", 32)
            out = _calc_text(out, "STATE_T2", f"lower(trim(coalesce(\"{t2}\", 'unknown')))", 32)

            # Backward-compatible aliases retained because some earlier styles/scripts used these names.
            out = _calc_text(out, "STATE_1", '"STATE_T1"', 32)
            out = _calc_text(out, "STATE_2", '"STATE_T2"', 32)

            # Active morphodynamic domain membership.
            # channel + island are treated as active-domain states; floodplain is inactive/stabilised domain.
            out = _calc_int(
                out,
                "ACTIVE_T1",
                "CASE WHEN \"STATE_T1\" IN ('channel','island') THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "ACTIVE_T2",
                "CASE WHEN \"STATE_T2\" IN ('channel','island') THEN 1 ELSE 0 END"
            )

            out = _calc_text(
                out,
                "DOMAIN_T1",
                "CASE WHEN \"ACTIVE_T1\" = 1 THEN 'active_morphodynamic_domain' "
                "WHEN \"STATE_T1\" = 'floodplain' THEN 'stabilised_or_inactive_domain' "
                "ELSE 'unknown_domain' END",
                48
            )
            out = _calc_text(
                out,
                "DOMAIN_T2",
                "CASE WHEN \"ACTIVE_T2\" = 1 THEN 'active_morphodynamic_domain' "
                "WHEN \"STATE_T2\" = 'floodplain' THEN 'stabilised_or_inactive_domain' "
                "ELSE 'unknown_domain' END",
                48
            )

            # Backward-compatible aliases retained.
            out = _calc_text(out, "DOMAIN_1", '"DOMAIN_T1"', 48)
            out = _calc_text(out, "DOMAIN_2", '"DOMAIN_T2"', 48)

            # More explicit surface-context labels for planform-neutral interpretation.
            out = _calc_text(
                out,
                "SURFACE_T1",
                "CASE "
                "WHEN \"STATE_T1\" = 'channel' THEN 'active_channel_or_water' "
                "WHEN \"STATE_T1\" = 'island' THEN 'active_bar_or_island' "
                "WHEN \"STATE_T1\" = 'floodplain' THEN 'stabilised_or_inactive_floodplain' "
                "ELSE 'unknown_surface' END",
                48
            )
            out = _calc_text(
                out,
                "SURFACE_T2",
                "CASE "
                "WHEN \"STATE_T2\" = 'channel' THEN 'active_channel_or_water' "
                "WHEN \"STATE_T2\" = 'island' THEN 'active_bar_or_island' "
                "WHEN \"STATE_T2\" = 'floodplain' THEN 'stabilised_or_inactive_floodplain' "
                "ELSE 'unknown_surface' END",
                48
            )

            # ------------------------------------------------------------------
            # Revised three-state ontology fields for Step 3 / R KM-AG-Cox
            # ------------------------------------------------------------------
            # Module 3 can observe interval surface transitions, but it should not
            # assert long-term preservation from one timestep alone.  The fields below
            # therefore make the *event-scale* interpretation explicit:
            #
            #   ACTIVE_DOMAIN          = wet/channel occupation and active reworking
            #   DEPOSITIONAL_STORAGE  = newly deposited or bar/island storage surface
            #   STABILISED_FLOODPLAIN = inactive/preserved candidate surface
            #
            # Module 4a can later refine STABILISED_FLOODPLAIN using persistence,
            # recurrence and quiet-run history.  The important change here is that
            # deposition is never treated as floodplain formation in the same interval.
            out = _calc_text(
                out,
                "ONTO_STATE_T1",
                "CASE "
                "WHEN \"STATE_T1\" = 'channel' THEN 'ACTIVE_DOMAIN' "
                "WHEN \"STATE_T1\" = 'island' THEN 'DEPOSITIONAL_STORAGE' "
                "WHEN \"STATE_T1\" = 'floodplain' THEN 'STABILISED_FLOODPLAIN' "
                "ELSE 'UNRESOLVED' END",
                32
            )
            out = _calc_text(
                out,
                "ONTO_STATE_T2",
                "CASE "
                "WHEN lower(trim(coalesce(\"EA\",''))) IN ('deposition','island_deposition') THEN 'DEPOSITIONAL_STORAGE' "
                "WHEN \"STATE_T2\" = 'channel' THEN 'ACTIVE_DOMAIN' "
                "WHEN \"STATE_T2\" = 'island' THEN 'DEPOSITIONAL_STORAGE' "
                "WHEN \"STATE_T2\" = 'floodplain' THEN 'STABILISED_FLOODPLAIN' "
                "ELSE 'UNRESOLVED' END",
                32
            )

            out = _calc_text(
                out,
                "ONTO_TRANS",
                "\"ONTO_STATE_T1\" || '_to_' || \"ONTO_STATE_T2\"",
                80
            )

            # Authoritative transition events. RECRUIT_EVT is retained only as
            # a backward-compatible alias; downstream scripts use REACTIVATE_EVT.
            out = _calc_int(
                out,
                "REACTIVATE_EVT",
                "CASE WHEN \"ONTO_STATE_T1\" = 'STABILISED_FLOODPLAIN' AND \"ONTO_STATE_T2\" = 'ACTIVE_DOMAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(out, "RECRUIT_EVT", '"REACTIVATE_EVT"')
            out = _calc_int(
                out,
                "STORAGE_EVT",
                "CASE WHEN \"ONTO_STATE_T1\" = 'ACTIVE_DOMAIN' AND \"ONTO_STATE_T2\" = 'DEPOSITIONAL_STORAGE' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STABILISE_EVT",
                "CASE WHEN \"ONTO_STATE_T1\" = 'DEPOSITIONAL_STORAGE' AND \"ONTO_STATE_T2\" = 'STABILISED_FLOODPLAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "ANY_STATE_EVT",
                "CASE WHEN \"ONTO_STATE_T1\" IN ('ACTIVE_DOMAIN','DEPOSITIONAL_STORAGE','STABILISED_FLOODPLAIN') "
                "AND \"ONTO_STATE_T2\" IN ('ACTIVE_DOMAIN','DEPOSITIONAL_STORAGE','STABILISED_FLOODPLAIN') "
                "AND \"ONTO_STATE_T1\" <> \"ONTO_STATE_T2\" THEN 1 ELSE 0 END"
            )
            # Backward-compatible alias. ANY_STATE_EVT includes reverse/skip changes,
            # not only the three named forward transitions.
            out = _calc_int(out, "ANY_ONTO_EVT", '"ANY_STATE_EVT"')

            # Authoritative transition-specific risk sets are defined entirely by
            # the recognised interval-start state.
            out = _calc_int(
                out,
                "REACTIVATE_RISK_SET",
                "CASE WHEN \"ONTO_STATE_T1\" = 'STABILISED_FLOODPLAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STORAGE_RISK_SET",
                "CASE WHEN \"ONTO_STATE_T1\" = 'ACTIVE_DOMAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STABILISE_RISK_SET",
                "CASE WHEN \"ONTO_STATE_T1\" = 'DEPOSITIONAL_STORAGE' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "ANY_STATE_RISK_SET",
                "CASE WHEN \"ONTO_STATE_T1\" IN ('ACTIVE_DOMAIN','DEPOSITIONAL_STORAGE','STABILISED_FLOODPLAIN') THEN 1 ELSE 0 END"
            )

            out = _calc_int(
                out,
                "ACTIVE_DOMAIN_T1",
                "CASE WHEN \"ONTO_STATE_T1\" = 'ACTIVE_DOMAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "ACTIVE_DOMAIN_T2",
                "CASE WHEN \"ONTO_STATE_T2\" = 'ACTIVE_DOMAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STORAGE_T1",
                "CASE WHEN \"ONTO_STATE_T1\" = 'DEPOSITIONAL_STORAGE' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STORAGE_T2",
                "CASE WHEN \"ONTO_STATE_T2\" = 'DEPOSITIONAL_STORAGE' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STAB_FP_T1",
                "CASE WHEN \"ONTO_STATE_T1\" = 'STABILISED_FLOODPLAIN' THEN 1 ELSE 0 END"
            )
            out = _calc_int(
                out,
                "STAB_FP_T2",
                "CASE WHEN \"ONTO_STATE_T2\" = 'STABILISED_FLOODPLAIN' THEN 1 ELSE 0 END"
            )

            # Human-readable labels for diagnostics/plotting; Step 3 still uses
            # ONTO_STATE_T1/T2 as the authoritative machine-readable fields.
            out = _calc_text(
                out,
                "ONTO_LABEL_T1",
                "CASE "
                "WHEN \"ONTO_STATE_T1\" = 'ACTIVE_DOMAIN' THEN 'Active domain' "
                "WHEN \"ONTO_STATE_T1\" = 'DEPOSITIONAL_STORAGE' THEN 'Depositional storage' "
                "WHEN \"ONTO_STATE_T1\" = 'STABILISED_FLOODPLAIN' THEN 'Stabilised floodplain' "
                "ELSE 'Unresolved' END",
                48
            )
            out = _calc_text(
                out,
                "ONTO_LABEL_T2",
                "CASE "
                "WHEN \"ONTO_STATE_T2\" = 'ACTIVE_DOMAIN' THEN 'Active domain' "
                "WHEN \"ONTO_STATE_T2\" = 'DEPOSITIONAL_STORAGE' THEN 'Depositional storage' "
                "WHEN \"ONTO_STATE_T2\" = 'STABILISED_FLOODPLAIN' THEN 'Stabilised floodplain' "
                "ELSE 'Unresolved' END",
                48
            )

            # Process group: generic, planform-neutral, and compatible with Module 4a.
            out = _calc_text(
                out,
                "PROC_GROUP",
                "CASE "
                "WHEN lower(trim(coalesce(\"EA\",''))) IN ('erosion','island_erosion') THEN 'erosion' "
                "WHEN lower(trim(coalesce(\"EA\",''))) IN ('deposition','island_deposition') THEN 'deposition' "
                "WHEN lower(trim(coalesce(\"EA\",''))) IN ('stable_channel','stable_island','stable_floodplain','inchannel_surface') THEN 'stable' "
                "WHEN lower(trim(coalesce(\"EA\",''))) IN ('inactive_floodplain','undefined_surface') THEN 'inactive' "
                "ELSE 'unresolved' END",
                32
            )

            # Domain transition for KM/AG: this is the field that makes the active-domain
            # interpretation explicit without redefining EA classes.
            out = _calc_text(
                out,
                "DOMAIN_TRANS",
                "CASE "
                "WHEN \"ACTIVE_T1\" = 0 AND \"ACTIVE_T2\" = 1 THEN 'inactive_to_active' "
                "WHEN \"ACTIVE_T1\" = 1 AND \"ACTIVE_T2\" = 0 THEN 'active_to_inactive' "
                "WHEN \"ACTIVE_T1\" = 1 AND \"ACTIVE_T2\" = 1 THEN 'active_persistence_or_reworking' "
                "WHEN \"ACTIVE_T1\" = 0 AND \"ACTIVE_T2\" = 0 THEN 'inactive_persistence' "
                "ELSE 'unknown_transition' END",
                48
            )

            out = _calc_int(
                out,
                "DIST_EVENT",
                "CASE WHEN \"ACTIVE_T1\" != \"ACTIVE_T2\" THEN 1 ELSE 0 END"
            )

            out = _calc_text(
                out,
                "DIST_TYPE",
                "CASE "
                "WHEN \"DOMAIN_TRANS\" = 'inactive_to_active' THEN 'active_domain_expansion' "
                "WHEN \"DOMAIN_TRANS\" = 'active_to_inactive' THEN 'active_domain_contraction' "
                "WHEN \"DOMAIN_TRANS\" = 'active_persistence_or_reworking' AND \"STATE_T1\" != \"STATE_T2\" THEN 'within_active_domain_reorganisation' "
                "WHEN \"DOMAIN_TRANS\" = 'active_persistence_or_reworking' THEN 'active_domain_persistence' "
                "WHEN \"DOMAIN_TRANS\" = 'inactive_persistence' THEN 'inactive_domain_persistence' "
                "ELSE 'unknown_disturbance' END",
                48
            )

            # Deposition interpretation: deposition is an active-domain transition/surface
            # unless Module 4a later shows persistence/stabilisation.
            out = _calc_text(
                out,
                "DEPO_INTERP",
                "CASE "
                "WHEN lower(trim(coalesce(\"EA\",''))) = 'deposition' THEN 'active_domain_deposition_not_floodplain_formation' "
                "WHEN lower(trim(coalesce(\"EA\",''))) = 'island_deposition' THEN 'active_bar_or_island_deposition' "
                "WHEN lower(trim(coalesce(\"EA\",''))) = 'stable_floodplain' THEN 'stabilised_or_inactive_surface_persistence' "
                "WHEN lower(trim(coalesce(\"EA\",''))) = 'stable_island' THEN 'active_bar_or_island_persistence' "
                "ELSE 'not_deposition' END",
                64
            )

            # Lightweight boolean used by 4a/KM scripts where a strict active-domain event is wanted.
            out = _calc_int(
                out,
                "ACTIVE_DOM",
                "CASE WHEN \"ACTIVE_T1\" = 1 OR \"ACTIVE_T2\" = 1 THEN 1 ELSE 0 END"
            )

            out = _calc_text(out, "PAIR_MODE", f"'{pair_mode}'", 32)
            out = _calc_text(out, "SURF_MODE", f"'{surf_mode}'", 32)
            out = _calc_text(out, "ONTOLOGY", "'active_domain_storage_v2'", 32)

            try:
                chk = _as_layer(out, context) or out
                feedback.pushInfo(
                    "[PAIR SUMMARY] Added ontology fields: STATE_T1/2, DOMAIN_T1/2, "
                    "SURFACE_T1/2, ONTO_STATE_T1/2, ONTO_TRANS, RECRUIT/STORAGE/STABILISE events, DOMAIN_TRANS, DIST_EVENT, DIST_TYPE, DEPO_INTERP, ACTIVE_DOM"
                )
            except Exception:
                pass

            return out

        # ---------- STEP 3: Pairwise EA (ArcPro-faithful, including islands) ----------
        n_pairs = k_len - 1  # compute once

        for i in range(n_pairs):
            # y1,y2 are year strings 'YYYYMMDD' from polygon years list
            y1, y2 = years_polys[i], years_polys[i + 1]
            # d1,d2 are Python datetime objects for date spans
            d1, d2 = date_objs_polys[i], date_objs_polys[i + 1]
            # Envelope surfaces and centrelines for older/younger
            pol_old, pol_yng = POL_list[i], POL_list[i + 1]
            cen_old, cen_yng = CEN_list[i], CEN_list[i + 1]
            EA1 = ISL_list[i]       # has y_y1, T_y1 tags
            EA2 = ISL_list[i + 1]   # has y_y2, T_y2 tags
            # PURPOSE: Normalise a date object to the string convention required by the EA fields.
            def _fmt_date(val):
                s = str(val)
                m = re.search(r"(18|19|20)\d{6}", s)
                if m:
                    t = m.group(0)
                    return f"{t[0:4]}_{t[4:6]}_{t[6:8]}"
                m4 = re.search(r"(18|19|20)\d{2}", s)
                return m4.group(0) if m4 else s

            formatted_start = _fmt_date(y1)
            formatted_end   = _fmt_date(y2)
            period_str = f"{y1}_{y2}"
            if d1 is None or d2 is None or d2 <= d1:
                raise QgsProcessingException(
                    f"[DATE QA] Invalid pair chronology for {y1}->{y2}: "
                    f"start={d1}, end={d2}."
                )
            span_days = (d2 - d1).days
            span_years = float(span_days) / 365.2425
            if span_years > max_interval_years:
                raise QgsProcessingException(
                    f"[DATE QA] Pair {y1}->{y2} spans {span_years:.2f} years, "
                    f"exceeding the permitted maximum of {max_interval_years:g} years."
                )

            # PURPOSE: Normalise an observation date to its eight-digit YYYYMMDD code.
            def _ymd8(val):
                s = str(val)
                m = re.search(r"(18|19|20)\d{6}", s)
                if m:
                    return m.group(0)
                m = re.search(r"(18|19|20)\d{2}[-/](\d{2})[-/](\d{2})", s)
                if m:
                    return f"{m.group(1)}{m.group(2)}{m.group(3)}"
                m = re.search(r"(18|19|20)\d{2}", s)
                if m:
                    return f"{m.group(0)}0101"
                return s

            y2_ymd = _ymd8(y2)
            digits = "".join(ch for ch in str(y2_ymd).strip() if ch.isdigit())
            if len(digits) >= 8:
                period_end_fmt = f"{digits[0:4]}_{digits[4:6]}_{digits[6:8]}"
            else:
                d2s = "".join(ch for ch in str(y2).strip() if ch.isdigit())
                period_end_fmt = f"{d2s[0:4]}_{d2s[4:6]}_{d2s[6:8]}" if len(d2s) >= 8 else str(y2)[:10]

            period_end_fmt = period_end_fmt[:32]
            
            feedback.pushInfo(f"[PAIR] {y1} → {y2} (idx={i+1}/{n_pairs})")

            _dbg_layer("env_old", pol_old, context, feedback, sample_n=3)
            _dbg_layer("env_yng", pol_yng, context, feedback, sample_n=3)
            _dbg_layer("EA1 (channel+island)", EA1, context, feedback, sample_n=3)
            _dbg_layer("EA2 (channel+island)", EA2, context, feedback, sample_n=3)
            _dbg_layer("cen_old", cen_old, context, feedback, sample_n=3)
            _dbg_layer("cen_yng", cen_yng, context, feedback, sample_n=3)

            # Clean envelopes (fix+2D) for each year
            env_old = _force_2d_safe(_fix_geoms(pol_old, context, feedback), context, feedback)
            env_yng = _force_2d_safe(_fix_geoms(pol_yng, context, feedback), context, feedback)

            # If either envelope is empty, skip this pair
            if is_empty_layer(env_old, context, feedback, f"env_old {y1}") or \
               is_empty_layer(env_yng, context, feedback, f"env_yng {y2}"):
                feedback.reportError(f"[PAIRING] Empty envelope for {y1}→{y2}; skipping.")
                continue

            # Build union envelope for both dates (used for orientation, clipping etc.)
            pair_env = _as_layer(
                _union_polys(env_old, env_yng, context, feedback, tag="pair_env"),
                context
            )

            env_union = _as_layer(
                _run(
                    "native:dissolve",
                    {
                        "INPUT": pair_env,
                        "FIELD": [],
                        "SEPARATE_DISJOINT": False,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"],
                context
            )

            # Clean/stabilise env_union once
            env_union = _ensure_layer(env_union, context, feedback, tag=f"env_union_{y1}_{y2}")
            env_union = _fix_geoms(env_union, context, feedback)
            env_union = _force_2d_safe(env_union, context, feedback)
            env_union = _polys_only(env_union, context, feedback)

            # Critical: freeze before repeated downstream use
            env_union = _freeze_to_tmp_gpkg(
                env_union,
                context,
                feedback,
                layer_name=f"env_union_{y1}_{y2}",
                ref_crs=ref_crs_obj
            )
            env_union = _as_layer(env_union, context) or env_union

            # -------------------------------------------------
            # Build ONE authoritative hole-free outer footprint of env_union
            # Used for gap-fill only, not to collapse the buffered domain.
            # -------------------------------------------------
            env_union_outer = _run(
                "native:dissolve",
                {
                    "INPUT": env_union,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]

            env_union_outer = _run(
                "native:deleteholes",
                {
                    "INPUT": env_union_outer,
                    "MIN_AREA": 0.0,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]

            env_union_outer = _fix_geoms(env_union_outer, context, feedback)
            env_union_outer = _force_2d_safe(env_union_outer, context, feedback)
            env_union_outer = _polys_only(env_union_outer, context, feedback)
            env_union_outer = _drop_null_tiny_polys(env_union_outer, S["min_area"] * 0.001, context, feedback)

            env_union_outer = _freeze_to_tmp_gpkg(
                env_union_outer,
                context,
                feedback,
                layer_name=f"env_union_outer_{y1}_{y2}",
                ref_crs=ref_crs_obj
            )
            env_union_outer = _as_layer(env_union_outer, context) or env_union_outer

            if env_union_outer is None or not env_union_outer.isValid() or env_union_outer.featureCount() == 0:
                raise QgsProcessingException(f"[EA] env_union_outer invalid/empty for {y1}->{y2}")
            
            # Boundary of the combined envelope (for snapping/extension)
            env_boundary = _as_layer(
                _run(
                    "native:boundary",
                    {"INPUT": env_union, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"],
                context
            )

            # Extend & snap centrelines to boundary (ArcPro-like behaviour)
            def _extend_and_snap_to_boundary(line, boundary, tag):
                """
                Extend line ends by a width-scaled distance, then snap to envelope boundary.
                The aim is to ensure centrelines reach the envelope edges for side classification.
                """
                try:
                    line_ext = _run(
                        "native:extendlines",
                        {
                            "INPUT": line,
                            "START_DISTANCE": S["extend"],
                            "END_DISTANCE": S["extend"],
                            "OUTPUT": "TEMPORARY_OUTPUT",
                        },
                        context, feedback
                    )["OUTPUT"]
                except Exception:
                    line_ext = line

                try:
                    # Use snapgeometries if available, else fallback to snap
                    alg = "native:snapgeometries" if _algo_exists("native:snapgeometries") else "native:snap"
                    line_snap = _run(
                        alg,
                        {
                            "INPUT": line_ext,
                            "REFERENCE_LAYER": boundary,
                            "TOLERANCE": S["snap"],
                            "BEHAVIOR": 0,
                            "OUTPUT": "TEMPORARY_OUTPUT",
                        },
                        context, feedback
                    )["OUTPUT"]
                except Exception:
                    if feedback:
                        feedback.pushInfo(
                            f"[snap] snap to boundary not available; using extended only for {tag}."
                        )
                    line_snap = line_ext
                return line_snap

            # Apply extend+snap to both older and younger centrelines
            cen_old = _extend_and_snap_to_boundary(cen_old, env_boundary, "old")
            cen_yng = _extend_and_snap_to_boundary(cen_yng, env_boundary, "young")

            # Prepare EA1 / EA2 as cleaned polygons clipped to env_union
            EA1_base = _polys_only(EA1, context, feedback)
            _dbg_layer("EA1 base polys", EA1_base, context, feedback, sample_n=3)
            _dbg_extent("EA1 base polys", EA1_base, context, feedback)
            _dbg_feature_bboxes("EA1 base polys", EA1_base, context, feedback, n=5)
            EA1_2d = _force_2d_safe(EA1_base, context, feedback)
            EA1_2d = _drop_fid_field(EA1_2d, context, feedback)
            EA1_2d = _freeze_to_tmp_gpkg(EA1_2d, context, feedback, layer_name="EA1_2d", ref_crs=ref_crs_obj)
            _dbg_layer("EA1 after force2d", EA1_2d, context, feedback, sample_n=3)
            _dbg_extent("EA1 after force2d", EA1_2d, context, feedback)
            _dbg_feature_bboxes("EA1 after force2d", EA1_2d, context, feedback, n=5)
            
            env_union_lyr = _as_layer(env_union, context) or env_union
            if env_union_lyr is None or not env_union_lyr.isValid():
                raise QgsProcessingException("[EA prep] env_union invalid before clip")

            if (not env_union_lyr.crs().isValid()) and ref_crs_obj is not None and ref_crs_obj.isValid():
                env_union_lyr.setCrs(ref_crs_obj)
                feedback.reportError(f"[EA prep] env_union had blank CRS; forced {ref_crs_obj.authid()}")

            EA1_lyr = _as_layer(EA1_2d, context) or EA1_2d
            ext = EA1_lyr.extent()
            vals = [ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum()]
            if any(str(v).lower() == "nan" for v in vals):
                raise QgsProcessingException("[EA prep] EA1 has NaN extent before clip")
            if EA1_lyr is None or not EA1_lyr.isValid():
                raise QgsProcessingException("[EA prep] EA1 invalid before clip")

            # ---- NEW: explicit CRS + extent diagnostics before clip ----
            try:
                ea1_crs = EA1_lyr.crs().authid() if EA1_lyr.crs().isValid() else "<invalid>"
            except Exception:
                ea1_crs = "<error>"

            try:
                envu_crs = env_union_lyr.crs().authid() if env_union_lyr.crs().isValid() else "<invalid>"
            except Exception:
                envu_crs = "<error>"

            try:
                ea1_ext = EA1_lyr.extent()
                ea1_ext_txt = (
                    f"xmin={ea1_ext.xMinimum()} xmax={ea1_ext.xMaximum()} "
                    f"ymin={ea1_ext.yMinimum()} ymax={ea1_ext.yMaximum()}"
                )
            except Exception:
                ea1_ext_txt = "<extent error>"

            try:
                envu_ext = env_union_lyr.extent()
                envu_ext_txt = (
                    f"xmin={envu_ext.xMinimum()} xmax={envu_ext.xMaximum()} "
                    f"ymin={envu_ext.yMinimum()} ymax={envu_ext.yMaximum()}"
                )
            except Exception:
                envu_ext_txt = "<extent error>"

            feedback.pushInfo(f"[EA CLIP DBG] EA1 CRS={ea1_crs}")
            feedback.pushInfo(f"[EA CLIP DBG] EA1 extent {ea1_ext_txt}")
            feedback.pushInfo(f"[EA CLIP DBG] env_union CRS={envu_crs}")
            feedback.pushInfo(f"[EA CLIP DBG] env_union extent {envu_ext_txt}")

            # Optional: quick bbox-overlap diagnostic
            try:
                bbox_overlap = EA1_lyr.extent().intersects(env_union_lyr.extent())
                feedback.pushInfo(f"[EA CLIP DBG] bbox overlap = {bbox_overlap}")
            except Exception as e:
                feedback.reportError(f"[EA CLIP DBG] bbox overlap test failed: {e}")
            # ---- END NEW BLOCK ----

            EA1_clip = _run(
                "native:clip",
                {
                    "INPUT": EA1_2d,
                    "OVERLAY": env_union_lyr,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            _dbg_layer("EA1 after direct native:clip", EA1_clip, context, feedback, sample_n=3)

            EA1_trim = _drop_null_tiny_polys(EA1_clip, 1e-6, context, feedback)
            _dbg_layer("EA1 after drop tiny", EA1_trim, context, feedback, sample_n=3)

            EA1c = _polys_only(EA1_trim, context, feedback)
            _dbg_layer("EA1c final", EA1c, context, feedback, sample_n=3)
            
            EA1c_lyr = _as_layer(EA1c, context) or EA1c

            if EA1c_lyr is None or not EA1c_lyr.isValid() or EA1c_lyr.featureCount() == 0:
                EA1_orig_poly = _polys_only(EA1, context, feedback)
                EA1_orig_poly = _safe_clip(EA1_orig_poly, env_union, context, feedback)
                EA1_orig_poly = _drop_null_tiny_polys(EA1_orig_poly, 1e-6, context, feedback)
                EA1_orig_poly_lyr = _as_layer(EA1_orig_poly, context) or EA1_orig_poly

                if EA1_orig_poly_lyr is not None and EA1_orig_poly_lyr.isValid() and EA1_orig_poly_lyr.featureCount() > 0:
                    feedback.reportError("[EA prep] EA1 cleaned path emptied polygons; using original polygon input clipped to env_union.")
                    EA1c = EA1_orig_poly
                else:
                    raise QgsProcessingException("[EA prep] EA1c empty after both cleaned and original polygon prep.")

            
            
            EA2_base = _polys_only(EA2, context, feedback)
            _dbg_layer("EA2 base polys", EA2_base, context, feedback, sample_n=3)
            _dbg_extent("EA2 base polys", EA2_base, context, feedback)
            _dbg_feature_bboxes("EA2 base polys", EA2_base, context, feedback, n=5)
            EA2_2d = _force_2d_safe(EA2_base, context, feedback)
            EA2_2d = _drop_fid_field(EA2_2d, context, feedback)
            EA2_2d = _freeze_to_tmp_gpkg(EA2_2d, context, feedback, layer_name="EA2_2d", ref_crs=ref_crs_obj)
            _dbg_layer("EA2 after force2d", EA2_2d, context, feedback, sample_n=3)
            _dbg_extent("EA2 after force2d", EA2_2d, context, feedback)
            _dbg_feature_bboxes("EA2 after force2d", EA2_2d, context, feedback, n=5)

            EA2_clip = _safe_clip(EA2_2d, env_union, context, feedback)
            _dbg_layer("EA2 after clip", EA2_clip, context, feedback, sample_n=3)

            EA2_trim = _drop_null_tiny_polys(EA2_clip, 1e-6, context, feedback)
            _dbg_layer("EA2 after drop tiny", EA2_trim, context, feedback, sample_n=3)

            EA2c = _polys_only(EA2_trim, context, feedback)
            _dbg_layer("EA2c final", EA2c, context, feedback, sample_n=3)
            EA2c_lyr = _as_layer(EA2c, context) or EA2c

            if EA2c_lyr is None or not EA2c_lyr.isValid() or EA2c_lyr.featureCount() == 0:
                EA2_orig_poly = _polys_only(EA2, context, feedback)
                EA2_orig_poly = _safe_clip(EA2_orig_poly, env_union, context, feedback)
                EA2_orig_poly = _drop_null_tiny_polys(EA2_orig_poly, 1e-6, context, feedback)
                EA2_orig_poly_lyr = _as_layer(EA2_orig_poly, context) or EA2_orig_poly

                if EA2_orig_poly_lyr is not None and EA2_orig_poly_lyr.isValid() and EA2_orig_poly_lyr.featureCount() > 0:
                    feedback.reportError("[EA prep] EA2 cleaned path emptied polygons; using original polygon input clipped to env_union.")
                    EA2c = EA2_orig_poly
                else:
                    raise QgsProcessingException("[EA prep] EA2c empty after both cleaned and original polygon prep.")

            # PURPOSE: Inspect per-date channel/island/floodplain type counts prior to EA classification.
            def _dbg_T_counts(layer, y, label):
                lyr = _as_layer(layer, context)
                if lyr is None or not lyr.isValid():
                    feedback.reportError(f"[DBG] {label} invalid")
                    return
                fnT = f"T_{y}"
                fny = f"y_{y}"
                fns = lyr.fields().names()
                feedback.pushInfo(f"[DBG] {label} fields has {fnT}? {fnT in fns} ; has {fny}? {fny in fns}")

                if fnT not in fns:
                    feedback.reportError(f"[DBG] {label} missing {fnT} (EA tags lost!)")
                    return

                counts = {}
                blanks = 0
                for f in lyr.getFeatures():
                    v = (f[fnT] or "")
                    v = str(v).strip().lower()
                    if v == "":
                        blanks += 1
                        v = "<blank>"
                    counts[v] = counts.get(v, 0) + 1

                feedback.pushInfo(
                    f"[DBG] {label} {fnT} counts: " +
                    ", ".join([f"{k}={counts[k]}" for k in sorted(counts.keys())]) +
                    f" ; blanks={blanks}/{lyr.featureCount()}"
                )

            _dbg_T_counts(EA1c, y1, "EA1c")
            _dbg_T_counts(EA2c, y2, "EA2c")

            # Debug emptiness (mainly for logging)
            _ = is_empty_layer(EA1c, context, feedback, "EA1c_polys_only")
            _ = is_empty_layer(EA2c, context, feedback, "EA2c_polys_only")
            try:
                f1 = _as_layer(EA1c, context).fields().names()
                f2 = _as_layer(EA2c, context).fields().names()
                feedback.pushInfo(f"[DEBUG] EA1c fields include y/T? {('y_'+y1 in f1)} {('T_'+y1 in f1)}")
                feedback.pushInfo(f"[DEBUG] EA2c fields include y/T? {('y_'+y2 in f2)} {('T_'+y2 in f2)}")
            except Exception as e:
                feedback.reportError(f"[DEBUG] field check failed: {e}")

            # --- Topology-first EA fabric classification ---
            # Build pairwise fabric from line boundaries rather than polygon overlay.
            # This preserves combined-extent edge boundaries and island/hole ring boundaries.
            try:
                unionEA = _topology_boundary_fabric(
                    EA1c, EA2c, env_union_outer,
                    y1, y2,
                    context, feedback,
                    outdir=outdir,
                    ref_crs_obj=ref_crs_obj,
                    tag=f"topology_fabric_{y1}_{y2}"
                )
            except Exception as e:
                feedback.reportError(
                    f"[TOPO FABRIC] boundary-derived fabric failed for {y1}->{y2}; "
                    f"falling back to old polygon union. Error: {e}"
                )
                try:
                    unionEA_out = _safe_union(EA1c, EA2c, grid=1.0, context=context, feedback=feedback, ref_crs_obj=ref_crs_obj, tag="unionEA_fallback")
                except Exception as e2:
                    feedback.reportError(f"[EA union fallback] _safe_union raised: {e2}; using simple union fallback.")
                    unionEA_out = _union_polys(EA1c, EA2c, context, feedback, tag="unionEA_fallback_simple")
                unionEA = _as_layer(unionEA_out, context)
                if unionEA is None or not unionEA.isValid():
                    raise QgsProcessingException(f"[EA union fallback] invalid output for {y1}->{y2}")

            unionEA_path = _freeze_to_tmp_gpkg(
                unionEA,
                context,
                feedback,
                layer_name=f"unionEA_topology_fabric_{y1}_{y2}",
                ref_crs=ref_crs_obj
            )
            unionEA = _as_layer(unionEA_path, context)
            if unionEA is None or not unionEA.isValid():
                raise QgsProcessingException("[TOPO FABRIC] unionEA invalid after freeze/reload.")

            # Ensure date/type tag fields exist before support reassignment.
            unionEA = _add_empty_tag_fields(unionEA, y1, y2, context, feedback)
            unionEA = _as_layer(unionEA, context) or unionEA
            _topology_debug_save(unionEA, outdir, "FABRIC_after_empty_tags", y1, y2, context, feedback)

            # ---------------------------------------------------------------------
            # FIX 3b: build a REAL buffered working domain (do not clip it back to env_union_outer)
            # env_union_outer remains the authoritative shell for floodplain gap-fill only.
            # ---------------------------------------------------------------------
            width_eff = float(channel_width) if channel_width and channel_width > 0 else 0.0
            domain_buf = max(10.0 * width_eff, 100.0)
            feedback.pushInfo(f"[DOMAIN] width={width_eff}m -> buffered working domain={domain_buf} m")

            env_union = _as_layer(env_union, context) or env_union
            if env_union is None or not env_union.isValid():
                raise QgsProcessingException("[EA union] env_union invalid before domain buffer")

            env_domain = _run(
                "native:buffer",
                {
                    "INPUT": env_union,
                    "DISTANCE": domain_buf,
                    "SEGMENTS": 12,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "DISSOLVE": True,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]

            env_domain = _fix_geoms(env_domain, context, feedback)
            env_domain = _force_2d_safe(env_domain, context, feedback)
            env_domain = _polys_only(env_domain, context, feedback)
            env_domain = _drop_null_tiny_polys(env_domain, S["min_area"] * 0.001, context, feedback)

            env_domain = _freeze_to_tmp_gpkg(
                env_domain,
                context,
                feedback,
                layer_name=f"env_domain_{y1}_{y2}",
                ref_crs=ref_crs_obj
            )
            env_domain = _as_layer(env_domain, context) or env_domain

            if env_domain is None or not env_domain.isValid() or env_domain.featureCount() == 0:
                raise QgsProcessingException(f"[EA union] env_domain invalid/empty for {y1}->{y2}")

            # Clip EA to the buffered working domain
            unionEA = _ensure_layer(unionEA, context, feedback, tag="EA union pre-domain-clip")
            unionEA = _safe_clip(unionEA, env_domain, context, feedback)
            unionEA = _ensure_layer(unionEA, context, feedback, tag="EA union post-domain-clip")

            if unionEA is None or not unionEA.isValid():
                raise QgsProcessingException(f"[EA union] unionEA invalid after domain clip for {y1}->{y2}")

            feedback.pushInfo(
                f"[FIX3] Buffered working domain retained: env_domain_fc={env_domain.featureCount()} "
                f"unionEA_fc={unionEA.featureCount() if unionEA and unionEA.isValid() else -1}"
            )
            _topology_debug_save(unionEA, outdir, "FABRIC_after_domain_clip", y1, y2, context, feedback)
            # -------------------------------------------------
            # Force tag fields to text, then assign same-date surface states
            # from authoritative support:
            #   channel support -> channel
            #   island support  -> island
            #   otherwise       -> floodplain
            # -------------------------------------------------
            unionEA = _force_tag_fields_text(unionEA, (y1, y2), 32, context, feedback)
            unionEA = _as_layer(unionEA, context) or unionEA
            _topology_debug_save(unionEA, outdir, "FABRIC_after_force_tag_text", y1, y2, context, feedback)

            # authoritative same-date channel / island sources
            chan_old_src = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA1c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y1}\",'')) = 'channel'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            chan_old_src = _as_layer(chan_old_src, context) or chan_old_src

            isl_old_src = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA1c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y1}\",'')) = 'island'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            isl_old_src = _as_layer(isl_old_src, context) or isl_old_src

            chan_yng_src = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA2c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y2}\",'')) = 'channel'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            chan_yng_src = _as_layer(chan_yng_src, context) or chan_yng_src

            isl_yng_src = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA2c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y2}\",'')) = 'island'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            isl_yng_src = _as_layer(isl_yng_src, context) or isl_yng_src

            _topology_debug_save(chan_old_src, outdir, "SRC_y1_channel_support", y1, y2, context, feedback)
            _topology_debug_save(isl_old_src, outdir, "SRC_y1_island_support", y1, y2, context, feedback)
            _topology_debug_save(chan_yng_src, outdir, "SRC_y2_channel_support", y1, y2, context, feedback)
            _topology_debug_save(isl_yng_src, outdir, "SRC_y2_island_support", y1, y2, context, feedback)

            unionEA = _enforce_surface_support_on_tags(unionEA, chan_old_src, isl_old_src, y1, context, feedback)
            unionEA = _as_layer(unionEA, context) or unionEA
            _topology_debug_save(unionEA, outdir, "FABRIC_after_y1_support_POINT", y1, y2, context, feedback)

            unionEA = _enforce_surface_support_on_tags(unionEA, chan_yng_src, isl_yng_src, y2, context, feedback)
            unionEA = _as_layer(unionEA, context) or unionEA
            _topology_debug_save(unionEA, outdir, "FABRIC_after_y2_support_POINT", y1, y2, context, feedback)

            if feedback:
                _dbg_T_counts(unionEA, y1, "unionEA AFTER surface support")
                _dbg_T_counts(unionEA, y2, "unionEA AFTER surface support")
            feedback.pushInfo("[ISLAND EXCL] Skipped; stable_channel/island separation is now handled by authoritative same-date surface support.")
            # -------------------------------------------------
            # NEW: build interval corridor + add IN_CORR to unionEA
            # -------------------------------------------------
            # Derive channel-only polygons for y1 and y2 from EA1c/EA2c (already cleaned/clipped)
            chan_y1 = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA1c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y1}\",'')) = 'channel'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            chan_y1 = _ensure_layer(chan_y1, context, tag=f"chan_only_{y1}_{y2}_y1")

            chan_y2 = _run(
                "native:extractbyexpression",
                {
                    "INPUT": EA2c,
                    "EXPRESSION": f"lower(coalesce(\"T_{y2}\",'')) = 'channel'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            chan_y2 = _ensure_layer(chan_y2, context, tag=f"chan_only_{y1}_{y2}_y2")

            # Add IN_CORR onto unionEA (corridor = buffer(union(chan_y1,chan_y2), corridor_mult * channel_width))
            unionEA = _add_in_corridor_flag(
                unionEA,
                chan_y1,
                chan_y2,
                channel_width,
                context,
                feedback,
                S,
                ref_crs_obj=ref_crs_obj,
                tag=f"{y1}_{y2}"
            )
            unionEA = _ensure_layer(unionEA, context, tag=f"unionEA_with_INCORR_{y1}_{y2}")
            _topology_debug_save(unionEA, outdir, "unionEA_after_corridor_flag_preEA", y1, y2, context, feedback)

            # --- DEBUG: save unionEA for this pair ---
            if DEBUG_SAVE:
                debug_union_path = os.path.join(outdir, f"unionEA_{y1}_{y2}.shp")
                for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
                    p = os.path.splitext(debug_union_path)[0] + ext
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception as e:
                            feedback.reportError(f"[DEBUG_SAVE] Could not delete {p}: {e}")
                feedback.pushInfo(f"[DEBUG_SAVE] Writing {debug_union_path}")
                _run(
                    "native:savefeatures",
                    {"INPUT": unionEA, "OUTPUT": debug_union_path},
                    context, feedback
                )

            # ------------------------------------------------------------------
            # ✅ Correction 2: guard unionEA as layer before fields() use
            # ------------------------------------------------------------------
            unionEA = _as_layer(unionEA, context) or unionEA
            if unionEA is None or not unionEA.isValid():
                raise QgsProcessingException("[EA] unionEA invalid before EA classification.")
            # ------------------------------------------------------------------
            # EA classification from authoritative T_y1 / T_y2 tags
            # ------------------------------------------------------------------
            unionEA = _as_layer(unionEA, context) or unionEA
            if unionEA is None or not unionEA.isValid():
                raise QgsProcessingException("[EA] unionEA invalid before EA classification.")

            # ----------------- STEP 1: DEBUG T_ TAGS BEFORE EA -----------------
            if feedback:
                _dbg_T_counts(unionEA, y1, "unionEA pre-EA")
                _dbg_T_counts(unionEA, y2, "unionEA pre-EA")
            # -------------------------------------------------------------------

            unionEA = _recompute_ea_from_tags(unionEA, y1, y2, context, feedback)
            unionEA = _as_layer(unionEA, context) or unionEA

            if unionEA is None or not unionEA.isValid():
                raise QgsProcessingException("[EA] unionEA invalid after EA classification.")

            
            
            # ----------------- STEP 2: GAP-FILL stable_floodplain within authoritative union envelope -----------------
            # Use the HOLE-FREE authoritative union envelope, not the buffered domain.
            # BG = env_union_outer - dissolve(unionEA)
            ea_diss = _run(
                "native:dissolve",
                {
                    "INPUT": unionEA,
                    "FIELD": [],
                    "SEPARATE_DISJOINT": False,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]
            ea_diss = _fix_geoms(ea_diss, context, feedback)
            ea_diss = _force_2d_safe(ea_diss, context, feedback)
            ea_diss = _polys_only(ea_diss, context, feedback)

            bg = _safe_polygon_difference(
                env_union_outer,
                ea_diss,
                context, feedback,
                tag=f"unionEA_bg_{y1}_{y2}",
                snap_grid=S["grid"],
                min_area=S["min_area"] * 0.001
            )
            bg = _as_layer(bg, context) or bg
            bg = _fix_geoms(bg, context, feedback)
            bg = _force_2d_safe(bg, context, feedback)
            bg = _polys_only(bg, context, feedback)

            # Drop tiny slivers
            bg = _drop_null_tiny_polys(bg, S["min_area"] * 0.001, context, feedback)
            bg = _as_layer(bg, context) or bg

            bg_fc = bg.featureCount() if bg and bg.isValid() else 0

            if bg is not None and bg.isValid() and bg_fc > 0:
                # Tag background polygons
                bg = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": bg,
                        "FIELD_NAME": "EA",
                        "FIELD_TYPE": 2,
                        "FIELD_LENGTH": 32,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": True,
                        "FORMULA": "'stable_floodplain'",
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                bg = _as_layer(bg, context) or bg

                bg = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": bg,
                        "FIELD_NAME": "IN_CORR",
                        "FIELD_TYPE": 1,
                        "FIELD_LENGTH": 1,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": True,
                        "FORMULA": "0",
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                bg = _as_layer(bg, context) or bg

                # Ensure BOTH y_ and T_ tags exist and are consistent
                for yy in (y1, y2):
                    if bg.fields().indexOf(f"y_{yy}") == -1:
                        bg = _run(
                            "native:fieldcalculator",
                            {
                                "INPUT": bg,
                                "FIELD_NAME": f"y_{yy}",
                                "FIELD_TYPE": 2,
                                "FIELD_LENGTH": 32,
                                "FIELD_PRECISION": 0,
                                "NEW_FIELD": True,
                                "FORMULA": f"'{yy}'",
                                "OUTPUT": "TEMPORARY_OUTPUT",
                            },
                            context, feedback
                        )["OUTPUT"]
                        bg = _as_layer(bg, context) or bg

                    if bg.fields().indexOf(f"T_{yy}") == -1:
                        bg = _run(
                            "native:fieldcalculator",
                            {
                                "INPUT": bg,
                                "FIELD_NAME": f"T_{yy}",
                                "FIELD_TYPE": 2,
                                "FIELD_LENGTH": 32,
                                "FIELD_PRECISION": 0,
                                "NEW_FIELD": True,
                                "FORMULA": "'stable_floodplain'",
                                "OUTPUT": "TEMPORARY_OUTPUT",
                            },
                            context, feedback
                        )["OUTPUT"]
                        bg = _as_layer(bg, context) or bg

                # Merge EA + BG => full coverage within authoritative envelope
                unionEA = _safe_feature_merge(
                    unionEA,
                    bg,
                    f"unionEA_bgmerge_{y1}_{y2}",
                    context,
                    feedback,
                    crs=ref_crs_obj
                )

                unionEA = _freeze_to_tmp_gpkg(
                    unionEA,
                    context,
                    feedback,
                    f"unionEA_bgmerge_{y1}_{y2}",
                    ref_crs_obj
                )
                unionEA = _as_layer(unionEA, context) or unionEA

                if feedback:
                    feedback.pushInfo(
                        f"[GAPFILL] BG added: {bg_fc} ; unionEA now: {unionEA.featureCount() if unionEA and unionEA.isValid() else -1}"
                    )
            else:
                if feedback:
                    feedback.pushInfo(f"[GAPFILL] No BG polygons added for {y1}->{y2}")

            
            # --------------------------------------------------------------------------------------------


            # --- DEBUG: EA value counts (helps diagnose "all undefined_surface") ---
            if feedback and unionEA and unionEA.isValid() and unionEA.fields().indexOf("EA") != -1:
                try:
                    counts = {}
                    for f in unionEA.getFeatures():
                        v = f["EA"]
                        ea_key = "NULL/blank" if v is None or str(v).strip() == "" else str(v).strip()
                        counts[ea_key] = counts.get(ea_key, 0) + 1

                    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
                    feedback.pushInfo("[DBG] EA counts: " + ", ".join([f"{ea_key}={n}" for ea_key, n in top]))
                except Exception as e:
                    feedback.reportError(f"[DBG] EA histogram failed: {e}")

            # PeriodEnd field holds the "young" date in a formatted text (YYYY_MM_DD)
            def _ymd8(val):
                """
                Internal helper to coerce a value to 'YYYYMMDD' string where possible.
                """
                s = str(val)
                m = re.search(r"(18|19|20)\d{6}", s)
                if m:
                    return m.group(0)
                m = re.search(r"(18|19|20)\d{2}[-/](\d{2})[-/](\d{2})", s)
                if m:
                    return f"{m.group(1)}{m.group(2)}{m.group(3)}"
                m = re.search(r"(18|19|20)\d{2}", s)
                if m:
                    return f"{m.group(0)}0101"
                return s

            y2_ymd = _ymd8(y2)

            # Always force YYYY_MM_DD format
            s = str(y2_ymd).strip()
            digits = "".join(ch for ch in s if ch.isdigit())

            if len(digits) >= 8:
                period_end_fmt = f"{digits[0:4]}_{digits[4:6]}_{digits[6:8]}"
            else:
                y2s = str(y2).strip()
                d2s = "".join(ch for ch in y2s if ch.isdigit())
                period_end_fmt = f"{d2s[0:4]}_{d2s[4:6]}_{d2s[6:8]}" if len(d2s) >= 8 else y2s[:10]

            period_end_fmt = period_end_fmt[:32]

            # period & spans
            period_str = f"{y1}_{y2}"
            span_days = max(0, (d2 - d1).days if (d1 and d2) else 0)
            span_years = float(span_days) / 365.2425 if span_days > 0 else 0.0

            unionEA = _as_layer(unionEA, context) or unionEA
            
            has_period_end = (unionEA.fields().indexOf("PeriodEnd") != -1)
            # Span_yr (optional but recommended)
            has_span_yr = (unionEA.fields().indexOf("Span_yr") != -1)
            unionEA = _run(
                "native:fieldcalculator",
                {
                    "INPUT": unionEA,
                    "FIELD_NAME": "Span_yr",
                    "FIELD_TYPE": 0,  # float
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 6,
                    "NEW_FIELD": not has_span_yr,
                    "FORMULA": f"{span_years}",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            unionEA = _as_layer(unionEA, context)
            unionEA = _run(
                "native:fieldcalculator",
                {
                    "INPUT": unionEA,
                    "FIELD_NAME": "PeriodEnd",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": not has_period_end,
                    "FORMULA": f"'{period_end_fmt}'",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            unionEA = _as_layer(unionEA, context)

            # -----------------------------------------------------------------------------

            # unionEA already has EA + PeriodEnd at this point.
            # -------------------------
            # -------------------------
            # Base EA surface for planarize
            # Floodplain gap-fill has already been done once, against env_union_outer.
            # Do NOT do a second domain fill here.
            # -------------------------
            baseEA = unionEA
            baseEA = _fix_geoms(baseEA, context, feedback)
            baseEA = _force_2d_safe(baseEA, context, feedback)
            baseEA = _polys_only(baseEA, context, feedback)
            baseEA = _run(
                "native:multiparttosingleparts",
                {"INPUT": baseEA, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            baseEA = _drop_null_tiny_polys(baseEA, S["min_area"] * 0.001, context, feedback)
            baseEA = _ensure_layer(baseEA, context, feedback, tag=f"baseEA_pre_planarize_{y1}_{y2}")
            _topology_debug_save(baseEA, outdir, "baseEA_pre_planarize", y1, y2, context, feedback)

            # --- EA coverage diagnostic BEFORE planarize ---
            _dbg_EA_coverage(
                f"pre-planarize {y1}->{y2}",
                baseEA,
                context, feedback
            )

            # 5) Planarize + max-overlap assignment (FIX 3A)
            baseEA = _planarize_and_assign_by_max_overlap(
                env_union,
                baseEA,
                context, feedback,
                S,
                period_end_fmt=period_end_fmt,
                tag=f"EA_planar_{y1}_{y2}"
            )
            baseEA = _ensure_layer(baseEA, context, feedback, tag=f"baseEA_planar_{y1}_{y2}")
            _topology_debug_save(baseEA, outdir, "baseEA_after_planarize_before_overlap_support", y1, y2, context, feedback)

            # ------------------------------------------------------------------
            # After planarize, use MAX-OVERLAP support (not point support).
            # Point-on-surface is too fragile for tiny planarized cells.
            # ------------------------------------------------------------------
            baseEA = _enforce_surface_support_on_tags_by_overlap(
                baseEA, chan_old_src, isl_old_src, y1, context, feedback
            )
            baseEA = _as_layer(baseEA, context) or baseEA
            _topology_debug_save(baseEA, outdir, "baseEA_after_y1_support_OVERLAP", y1, y2, context, feedback)

            baseEA = _enforce_surface_support_on_tags_by_overlap(
                baseEA, chan_yng_src, isl_yng_src, y2, context, feedback
            )
            baseEA = _as_layer(baseEA, context) or baseEA
            _topology_debug_save(baseEA, outdir, "baseEA_after_y2_support_OVERLAP_preEA", y1, y2, context, feedback)

            if feedback:
                _dbg_T_counts(baseEA, y1, "baseEA AFTER post-planar overlap support")
                _dbg_T_counts(baseEA, y2, "baseEA AFTER post-planar overlap support")

            # Recompute EA from authoritative post-planar support
            baseEA = _recompute_ea_from_tags(baseEA, y1, y2, context, feedback)
            baseEA = _as_layer(baseEA, context) or baseEA
            _topology_debug_save(baseEA, outdir, "baseEA_postEA_rebuild", y1, y2, context, feedback)

            # --- EA coverage diagnostic AFTER planarize/support rebuild ---
            _dbg_EA_coverage(
                f"post-planarize {y1}->{y2}",
                baseEA,
                context, feedback
            )
            baseEA = _ensure_layer(baseEA, context, feedback, tag=f"baseEA_planar_{y1}_{y2}")

            # 6) Do NOT delete holes globally here.
            # True island cut-outs and class void separations must be preserved.
            # Only continue with normal geometry cleanup.
            feedback.pushInfo("[PLANAR POST] Skipping global deleteholes to preserve island cut-outs and class boundaries.")
            # Post-planar cleanup (no extra domain fill)

            baseEA = _fix_geoms(baseEA, context, feedback)

            baseEA = _force_2d_safe(baseEA, context, feedback)

            baseEA = _polys_only(baseEA, context, feedback)

            baseEA = _run("native:multiparttosingleparts", {"INPUT": baseEA, "OUTPUT": "TEMPORARY_OUTPUT"}, context, feedback)["OUTPUT"]

            baseEA = _drop_null_tiny_polys(baseEA, S["min_area"] * 0.001, context, feedback)

            baseEA = _ensure_layer(baseEA, context, tag=f"baseEA_planar_noholes_{y1}_{y2}")
            _dbg_geom_stats(f"baseEA_planar_noholes_{y1}_{y2}", baseEA, context, feedback)

            _dbg_layer_simple(feedback, "baseEA_planar", baseEA)
            # NOTE v11-stabilised:
            # Abandoned-channel override is intentionally NOT applied here.
            # Former-channel candidates should first be inspected as diagnostics
            # before any future merge-back into baseEA.
            # --- DEBUG: interior ring check ---
            rings = _run(
                "native:extractbyexpression",
                {
                    "INPUT": baseEA,
                    "EXPRESSION": "num_interior_rings($geometry) > 0",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]
            rings = _ensure_layer(rings, context, tag=f"debug_interior_rings_{y1}_{y2}")
            feedback.pushInfo(f"[DBG] Polygons with interior rings: {rings.featureCount()}")


            # ---------- Orientation masks (LEFT/RIGHT) ----------
            # Builds side masks for each year, then JOINs side fields onto baseEA (no union!)

            merged_old = _run(
                "native:mergevectorlayers",
                {
                    "LAYERS": [env_boundary, cen_old],
                    "CRS": ref_crs_obj,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]

            merged_old = _fix_geoms(merged_old, context, feedback)

            cells_old = _run(
                "native:polygonize",
                {
                    "INPUT": merged_old,
                    "KEEP_FIELDS": False,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            cells_old = _safe_clip(cells_old, env_union, context, feedback)
            cells_old = _polys_only(cells_old, context, feedback)
            cells_old = _drop_null_tiny_polys(cells_old, S["min_area"] * 0.001, context, feedback)

            merged_yng = _run(
                "native:mergevectorlayers",
                {
                    "LAYERS": [env_boundary, cen_yng],
                    "CRS": ref_crs_obj,
                    "OUTPUT": "TEMPORARY_OUTPUT"
                },
                context, feedback
            )["OUTPUT"]

            merged_yng = _fix_geoms(merged_yng, context, feedback)

            cells_yng = _run(
                "native:polygonize",
                {
                    "INPUT": merged_yng,
                    "KEEP_FIELDS": False,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            cells_yng = _safe_clip(cells_yng, env_union, context, feedback)
            cells_yng = _polys_only(cells_yng, context, feedback)
            cells_yng = _drop_null_tiny_polys(cells_yng, S["min_area"] * 0.001, context, feedback)

            _dbg_layer("cells_old (polys_only)", cells_old, context, feedback, sample_n=3)
            _dbg_layer("cells_yng (polys_only)", cells_yng, context, feedback, sample_n=3)

            cells_old_lyr = _as_layer(cells_old, context) or cells_old
            cells_yng_lyr = _as_layer(cells_yng, context) or cells_yng

            if cells_old_lyr is None or not cells_old_lyr.isValid() or cells_old_lyr.featureCount() == 0:
                raise QgsProcessingException("[ORIENT] cells_old empty after polygonize/clip")

            if cells_yng_lyr is None or not cells_yng_lyr.isValid() or cells_yng_lyr.featureCount() == 0:
                raise QgsProcessingException("[ORIENT] cells_yng empty after polygonize/clip")

            # Side buffer distance (metres)
            SIDE_BUF = S["side"]


            # ---------------- OLD YEAR side masks (robust) ----------------
            left_old = _run(
                "native:singlesidedbuffer",
                {
                    "INPUT": cen_old,
                    "DISTANCE": SIDE_BUF,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "SIDE": 0,  # left
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            right_old = _run(
                "native:singlesidedbuffer",
                {
                    "INPUT": cen_old,
                    "DISTANCE": SIDE_BUF,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "SIDE": 1,  # right
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            # Fix + 2D + polys, then safe clip to authoritative domain
            left_old  = _polys_only(_force_2d_safe(_fix_geoms(left_old,  context, feedback), context, feedback), context, feedback)
            right_old = _polys_only(_force_2d_safe(_fix_geoms(right_old, context, feedback), context, feedback), context, feedback)

            left_old  = _safe_clip(left_old,  env_union, context, feedback)
            right_old = _safe_clip(right_old, env_union, context, feedback)

            left_old  = _drop_null_tiny_polys(left_old,  S["min_area"] * 0.001, context, feedback)
            right_old = _drop_null_tiny_polys(right_old, S["min_area"] * 0.001, context, feedback)

            left_old  = _ensure_layer(left_old,  context, tag=f"left_old_{y1}_{y2}")
            right_old = _ensure_layer(right_old, context, tag=f"right_old_{y1}_{y2}")

            _dbg_layer_simple(feedback, "left_old", left_old)
            _dbg_layer_simple(feedback, "right_old", right_old)


            left_old  = _add_const_field(left_old,  "SIDEL", "'LEFT'",  2, 10, 0, context, feedback)
            right_old = _add_const_field(right_old, "SIDER", "'RIGHT'", 2, 10, 0, context, feedback)

            lr_old = _run(
                "native:mergevectorlayers",
                {"LAYERS": [left_old, right_old], "CRS": ref_crs_obj, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]

            side_old = _run(
                "native:joinattributesbylocation",
                {
                    "INPUT": cells_old,
                    "JOIN": lr_old,
                    "PREDICATE": [0],  # intersects
                    "JOIN_FIELDS": ["SIDEL", "SIDER"],
                    "METHOD": 0,  # first match
                    "DISCARD_NONMATCHING": False,
                    "PREFIX": "",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            side_old = _add_const_field(
                side_old,
                f"S_{y1}",
                "coalesce(\"SIDEL\",'')||coalesce(\"SIDER\",'')",
                2, 20, 0, context, feedback
            )

            side_old = _run(
                "native:deletecolumn",
                {"INPUT": side_old, "COLUMN": ["SIDEL", "SIDER"], "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]

            # ✅ strip PK-like fields early to avoid fid collisions later
            side_old = _strip_pk_fields(side_old, context, feedback)
            side_old = _as_layer(side_old, context) or side_old
        
            # ---------------- YOUNG YEAR side masks (robust) ----------------
            left_yng = _run(
                "native:singlesidedbuffer",
                {
                    "INPUT": cen_yng,
                    "DISTANCE": SIDE_BUF,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "SIDE": 0,  # left
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            right_yng = _run(
                "native:singlesidedbuffer",
                {
                    "INPUT": cen_yng,
                    "DISTANCE": SIDE_BUF,
                    "SEGMENTS": 8,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2.0,
                    "SIDE": 1,  # right
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            # Fix + 2D + polygons, then safe clip to authoritative domain
            left_yng  = _polys_only(_force_2d_safe(_fix_geoms(left_yng,  context, feedback), context, feedback), context, feedback)
            right_yng = _polys_only(_force_2d_safe(_fix_geoms(right_yng, context, feedback), context, feedback), context, feedback)

            left_yng  = _safe_clip(left_yng,  env_union, context, feedback)
            right_yng = _safe_clip(right_yng, env_union, context, feedback)

            left_yng  = _drop_null_tiny_polys(left_yng,  S["min_area"] * 0.001, context, feedback)
            right_yng = _drop_null_tiny_polys(right_yng, S["min_area"] * 0.001, context, feedback)

            left_yng  = _ensure_layer(left_yng,  context, tag=f"left_yng_{y1}_{y2}")
            right_yng = _ensure_layer(right_yng, context, tag=f"right_yng_{y1}_{y2}")

            _dbg_layer_simple(feedback, "left_yng", left_yng)
            _dbg_layer_simple(feedback, "right_yng", right_yng)


            left_yng  = _add_const_field(left_yng,  "SIDEL", "'LEFT'",  2, 10, 0, context, feedback)
            right_yng = _add_const_field(right_yng, "SIDER", "'RIGHT'", 2, 10, 0, context, feedback)

            lr_yng = _run(
                "native:mergevectorlayers",
                {"LAYERS": [left_yng, right_yng], "CRS": ref_crs_obj, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]

            side_yng = _run(
                "native:joinattributesbylocation",
                {
                    "INPUT": cells_yng,
                    "JOIN": lr_yng,
                    "PREDICATE": [0],
                    "JOIN_FIELDS": ["SIDEL", "SIDER"],
                    "METHOD": 0,
                    "DISCARD_NONMATCHING": False,
                    "PREFIX": "",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            side_yng = _add_const_field(
                side_yng,
                f"S_{y2}",
                "coalesce(\"SIDEL\",'')||coalesce(\"SIDER\",'')",
                2, 20, 0, context, feedback
            )

            side_yng = _run(
                "native:deletecolumn",
                {"INPUT": side_yng, "COLUMN": ["SIDEL", "SIDER"], "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]

            # ✅ strip PK-like fields early
            side_yng = _strip_pk_fields(side_yng, context, feedback)
            side_yng = _as_layer(side_yng, context) or side_yng
        
            _dbg_layer("left_old", left_old, context, feedback)
            _dbg_layer("right_old", right_old, context, feedback)
            _dbg_layer("lr_old (merged)", lr_old, context, feedback)

            _dbg_layer("left_yng", left_yng, context, feedback)
            _dbg_layer("right_yng", right_yng, context, feedback)
            _dbg_layer("lr_yng (merged)", lr_yng, context, feedback)


            # --------------------------------------------------------------------
            # IMPORTANT:
            # Do NOT union baseEA with side masks (that’s where MultiLineString leaks happen).
            # Instead, JOIN side fields onto baseEA using PREFixed joins, then coalesce.
            # --------------------------------------------------------------------
            um = _as_layer(baseEA, context)
            if um is None or not um.isValid():
                raise QgsProcessingException("[EA] baseEA invalid before side-join.")

            um = _strip_pk_fields(um, context, feedback)
            um = _as_layer(um, context) or um

            # --------------------------------------------------------------------
            # Robust side join: centroid/point-on-surface join to avoid polygon overlap duplication
            # --------------------------------------------------------------------

            # 0) Ensure um is a valid layer object
            um = _as_layer(um, context) or um
            um = _strip_pk_fields(um, context, feedback)
            um = _as_layer(um, context) or um

            # 1) Add stable ID (EAID) if missing
            if _as_layer(um, context).fields().indexOf("EAID") == -1:
                um = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": um,
                        "FIELD_NAME": "EAID",
                        "FIELD_TYPE": 1,          # int
                        "FIELD_LENGTH": 18,
                        "FIELD_PRECISION": 0,
                        "NEW_FIELD": True,
                        "FORMULA": "$id",
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                um = _as_layer(um, context) or um
            
            _dbg_layer("um before points", um, context, feedback, sample_n=5)
            _dbg_geom_stats(f"um_before_points_{y1}_{y2}", um, context, feedback)

            # 2) Build point-on-surface for um polygons
            um_pts = _points_from_polys_safe(um, context, feedback, tag="um_pts")
            um_pts = _as_layer(um_pts, context) or um_pts



            # Helper: join side field to points, then push back to polygons by EAID
            # PURPOSE: Transfer orientation-side flags from masks to EA polygons via representative interior points.
            def _side_join_via_points(poly_layer, pts_layer, side_layer, side_field, prefix):
                # Join points -> side polygons (intersects is fine for points)
                pts_join = _run(
                    "native:joinattributesbylocation",
                    {
                        "INPUT": pts_layer,
                        "JOIN": side_layer,
                        "PREDICATE": [0],  # intersects
                        "JOIN_FIELDS": [side_field],
                        "METHOD": 0,
                        "DISCARD_NONMATCHING": False,
                        "PREFIX": prefix,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                pts_join = _as_layer(pts_join, context) or pts_join

                # Now join attributes back to polygons by EAID
                poly_join = _run(
                    "native:joinattributestable",
                    {
                        "INPUT": poly_layer,
                        "FIELD": "EAID",
                        "INPUT_2": pts_join,
                        "FIELD_2": "EAID",
                        "FIELDS_TO_COPY": [f"{prefix}{side_field}"],
                        "METHOD": 1,  # take first matching record
                        "DISCARD_NONMATCHING": False,
                        "PREFIX": "",
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]
                poly_join = _as_layer(poly_join, context) or poly_join
                return poly_join

            # 3) Ensure side fields exist on um
            um = _ensure_string_field(um, f"S_{y1}", context, feedback, length=20)
            um = _ensure_string_field(um, f"S_{y2}", context, feedback, length=20)
            um = _as_layer(um, context) or um

            # 4) OLD side join via points
            um = _side_join_via_points(um, um_pts, side_old, f"S_{y1}", prefix="J1_")
            um = _as_layer(um, context) or um

            um = _run(
                "native:fieldcalculator",
                {
                    "INPUT": um,
                    "FIELD_NAME": f"S_{y1}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 20,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": False,
                    "FORMULA": f"coalesce(\"S_{y1}\", \"J1_S_{y1}\")",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            um = _run(
                "native:deletecolumn",
                {"INPUT": um, "COLUMN": [f"J1_S_{y1}"], "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            um = _as_layer(um, context) or um

            _dbg_layer(f"um after join old S_{y1} (via points)", um, context, feedback, fields_check=[f"S_{y1}"], sample_n=3)

            # 5) YOUNG side join via points
            # Recompute point-on-surface after attribute changes (not strictly necessary, but safe)
            um_pts = _points_from_polys_safe(um, context, feedback, tag="um_pts")
            um_pts = _as_layer(um_pts, context) or um_pts



            um = _side_join_via_points(um, um_pts, side_yng, f"S_{y2}", prefix="J2_")
            um = _as_layer(um, context) or um

            um = _run(
                "native:fieldcalculator",
                {
                    "INPUT": um,
                    "FIELD_NAME": f"S_{y2}",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 20,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": False,
                    "FORMULA": f"coalesce(\"S_{y2}\", \"J2_S_{y2}\")",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            um = _run(
                "native:deletecolumn",
                {"INPUT": um, "COLUMN": [f"J2_S_{y2}"], "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            um = _as_layer(um, context) or um

            # Final safety: ensure fields exist even if join yielded nothing
            um = _ensure_string_field(um, f"S_{y1}", context, feedback, length=20)
            um = _ensure_string_field(um, f"S_{y2}", context, feedback, length=20)
            um = _as_layer(um, context) or um

            _dbg_layer(
                f"um after join yng S_{y2} (via points)",
                um, context, feedback,
                fields_check=[f"S_{y1}", f"S_{y2}"], sample_n=3
            )

            try:
                lyr = _as_layer(um, context)
                got1 = sum(1 for f in lyr.getFeatures() if (f[f"S_{y1}"] or "").strip())
                got2 = sum(1 for f in lyr.getFeatures() if (f[f"S_{y2}"] or "").strip())
                feedback.pushInfo(
                    f"[DBG] side coverage: S_{y1} nonblank={got1}/{lyr.featureCount()} ; "
                    f"S_{y2} nonblank={got2}/{lyr.featureCount()}"
                )
            except Exception as e:
                feedback.reportError(f"[DBG] side coverage count failed: {e}")

            # Seed working layer (all subsequent EA ops act on "working")
            working = _run(
                "native:savefeatures",
                {"INPUT": um, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]
            working = _as_layer(working, context) or working

            # ✅ and one last strip after savefeatures (prevents temp OUTPUT.gpkg fid uniqueness failures)
            working = _strip_pk_fields(working, context, feedback)
            working = _as_layer(working, context) or working



            # ---------- Direction (ArcPro-style, adapted) ----------
            # If TRUE, ties for L+R go to LEFT; else assign BOTH
            PREFER_LEFT_ON_TIE = False

            # Determine direction based on side masks:
            #   - For deposition: prefer S_y2 (new bank) then S_y1 if missing
            #   - For erosion / stable_floodplain / inactive_floodplain / island_erosion:
            #       prefer S_y1 (old bank) then S_y2
            #   - If both LEFT and RIGHT appear -> tie; map to LEFT or BOTH.
            dir_expr = (
                "with_variable('pref', "
                "  CASE "
                "    WHEN \"EA\" IN ('deposition','island_deposition') "
                f"      THEN coalesce(\"S_{y2}\", coalesce(\"S_{y1}\",'')) "
                "    WHEN \"EA\" IN ('erosion','stable_floodplain','inactive_floodplain','island_erosion') "
                f"      THEN coalesce(\"S_{y1}\", coalesce(\"S_{y2}\",'')) "
                "    ELSE '' "
                "  END, "
                "  CASE "
                "    WHEN @pref = '' THEN 'in-channel process' "
                "    WHEN regexp_match(@pref, 'LEFT') AND regexp_match(@pref, 'RIGHT') "
                f"      THEN '{'LEFT' if PREFER_LEFT_ON_TIE else 'BOTH'}' "
                "    WHEN regexp_match(@pref, 'LEFT') THEN 'LEFT' "
                "    WHEN regexp_match(@pref, 'RIGHT') THEN 'RIGHT' "
                "    ELSE 'in-channel process' "
                "  END "
                ")"
            )

            # Add or update 'direction' field
            has_dir = (_as_layer(working, context).fields().indexOf("direction") != -1)
            working = _run(
                "native:fieldcalculator",
                {
                    "INPUT": working,
                    "FIELD_NAME": "direction",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 24,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": not has_dir,
                    "FORMULA": dir_expr,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            # ---------- Migration ----------
            # Combine EA and direction labels into a single 'migration' descriptor
            working = _run(
                "native:fieldcalculator",
                {
                    "INPUT": working,
                    "FIELD_NAME": "migration",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 32,
                    "FIELD_PRECISION": 0,
                    "NEW_FIELD": True,
                    "FORMULA": (
                        "CASE "
                        "  WHEN \"EA\"='stable_channel' OR coalesce(\"direction\",'') IN ('','in-channel process') "
                        "    THEN 'in-channel process' "
                        "  WHEN \"EA\" IN ('erosion','stable_floodplain','inactive_floodplain','island_erosion') "
                        "    THEN 'erosion_' || \"direction\" "
                        "  WHEN \"EA\" IN ('deposition','island_deposition') "
                        "    THEN 'deposition_' || \"direction\" "
                        "  ELSE 'in-channel process' "
                        "END"
                    ),
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            # ---------- Period & spans ----------
            # period string: 'YYYYMMDD_YYYYMMDD'
            period_str = f"{y1}_{y2}"
            # Number of days between the two dates
            span_days = max(0, (d2 - d1).days if (d1 and d2) else 0)
            # Span in (approximate) years, used for rate per year
            span_years = float(span_days) / 365.2425 if span_days > 0 else 0.0

            # Add standard period fields
            working = _add_const_field(working, "period",     f"'{period_str}'", 2, 20, 0, context, feedback)
            working = _add_const_field(working, "span_days",  str(int(span_days)), 1, 10, 0, context, feedback)
            working = _add_const_field(working, "span_years", str(span_years),    0, 20, 6, context, feedback)
            # ---------- Trim fields before dissolve ---------- 
            # # Keep only fields needed for EA_processes (everything else is dropped)
            
            keep_fields = [
                f"y_{y1}", f"T_{y1}",
                f"y_{y2}", f"T_{y2}",
                "EA",
                "PROC_GROUP",
                "STATE_T1", "STATE_T2",
                "STATE_1", "STATE_2",
                "ACTIVE_T1", "ACTIVE_T2", "ACTIVE_DOM",
                "DOMAIN_T1", "DOMAIN_T2",
                "DOMAIN_1", "DOMAIN_2",
                "SURFACE_T1", "SURFACE_T2",
                "ONTO_STATE_T1", "ONTO_STATE_T2", "ONTO_TRANS",
                "ONTO_LABEL_T1", "ONTO_LABEL_T2",
                "ACTIVE_DOMAIN_T1", "ACTIVE_DOMAIN_T2",
                "STORAGE_T1", "STORAGE_T2",
                "STAB_FP_T1", "STAB_FP_T2",
                "REACTIVATE_EVT", "RECRUIT_EVT", "STORAGE_EVT", "STABILISE_EVT",
                "ANY_ONTO_EVT", "ANY_STATE_EVT",
                "REACTIVATE_RISK_SET", "STORAGE_RISK_SET", "STABILISE_RISK_SET", "ANY_STATE_RISK_SET",
                "DOMAIN_TRANS", "DIST_EVENT", "DIST_TYPE", "DEPO_INTERP", "ONTOLOGY",
                "PAIR_MODE", "SURF_MODE",
                "direction",
                "period", "span_days", "span_years",
                "migration",
                "PeriodEnd",
]
            try:
                lyr = _as_layer(working, context)
                names = lyr.fields().names() if lyr else []
                drop_fields = [n for n in names if (n not in keep_fields and n.lower() != "fid")]
                if drop_fields:
                    working = _run(
                        "native:deletecolumn",
                        {"INPUT": working, "COLUMN": drop_fields, "OUTPUT": "TEMPORARY_OUTPUT"},
                        context, feedback
                    )["OUTPUT"]
                    feedback.pushInfo(f"[EA TRIM] Removed {drop_fields}")
            except Exception as e:
                feedback.reportError(f"[EA TRIM] Keep-list trimming skipped due to: {e}")

            # ---------- Sanity & dissolve ----------
            lyr_work = _as_layer(working, context)
            if lyr_work is None or not lyr_work.isValid():
                feedback.reportError("[EA] Working layer invalid before dissolve; skipping pair.")
                continue
            cnt = lyr_work.featureCount()
            feedback.pushInfo(f"[EA] Working layer ready for dissolve; features={cnt}")
            if cnt == 0:
                feedback.reportError("[EA] Working layer empty; skipping pair.")
                continue
            # ------------------------------------------------------------
            # Island exclusion fix for stable_channel (SAFE FALLBACK VERSION)
            #
            # Purpose:
            #   Prevent stable_channel from occupying space that is island
            #   at either date, while avoiding catastrophic corruption of
            #   the full working layer.
            #
            # Strategy:
            #   - keep a pre-fix fallback copy of working
            #   - build island_union from both dates
            #   - subtract island_union only from stable_channel polygons
            #   - merge corrected stable_channel back with non_stable
            #   - DO NOT run global fixgeometries on the merged working layer
            #   - if anything looks invalid/empty, revert to original working
            # ------------------------------------------------------------
            try:
                working_before_island_excl = _as_layer(working, context) or working
                if working_before_island_excl is None or not working_before_island_excl.isValid():
                    feedback.reportError("[ISLAND EXCL] working invalid before exclusion; skipping block.")
                else:
                    fc_before_all = working_before_island_excl.featureCount()

                    # 1) Build island union from both dates
                    isl_old = _run(
                        "native:extractbyexpression",
                        {
                            "INPUT": EA1c,
                            "EXPRESSION": f"lower(coalesce(\"T_{y1}\",'')) = 'island'",
                            "OUTPUT": "TEMPORARY_OUTPUT",
                        },
                        context, feedback
                    )["OUTPUT"]
                    isl_old = _as_layer(isl_old, context) or isl_old

                    isl_yng = _run(
                        "native:extractbyexpression",
                        {
                            "INPUT": EA2c,
                            "EXPRESSION": f"lower(coalesce(\"T_{y2}\",'')) = 'island'",
                            "OUTPUT": "TEMPORARY_OUTPUT",
                        },
                        context, feedback
                    )["OUTPUT"]
                    isl_yng = _as_layer(isl_yng, context) or isl_yng

                    fc_old = isl_old.featureCount() if isl_old and isl_old.isValid() else 0
                    fc_yng = isl_yng.featureCount() if isl_yng and isl_yng.isValid() else 0

                    if fc_old + fc_yng == 0:
                        feedback.pushInfo("[ISLAND EXCL] No island polygons found; skipping stable_channel exclusion.")
                    else:
                        island_union = _run(
                            "native:mergevectorlayers",
                            {
                                "LAYERS": [isl_old, isl_yng],
                                "CRS": ref_crs_obj,
                                "OUTPUT": "TEMPORARY_OUTPUT",
                            },
                            context, feedback
                        )["OUTPUT"]

                        island_union = _run(
                            "native:dissolve",
                            {
                                "INPUT": island_union,
                                "FIELD": [],
                                "SEPARATE_DISJOINT": False,
                                "OUTPUT": "TEMPORARY_OUTPUT",
                            },
                            context, feedback
                        )["OUTPUT"]

                        # Clean ONLY the island union, not the full working layer
                        island_union = _fix_geoms(island_union, context, feedback)
                        island_union = _force_2d_safe(island_union, context, feedback)
                        island_union = _polys_only(island_union, context, feedback)
                        island_union = _drop_null_tiny_polys(island_union, 1e-6, context, feedback)
                        island_union = _as_layer(island_union, context) or island_union

                        if island_union is None or not island_union.isValid() or island_union.featureCount() == 0:
                            feedback.pushInfo("[ISLAND EXCL] Island union empty/invalid after cleanup; skipping.")
                        else:
                            # 2) Split working into stable_channel and everything else
                            stable_ch = _run(
                                "native:extractbyexpression",
                                {
                                    "INPUT": working_before_island_excl,
                                    "EXPRESSION": "\"EA\" = 'stable_channel'",
                                    "OUTPUT": "TEMPORARY_OUTPUT",
                                },
                                context, feedback
                            )["OUTPUT"]
                            stable_ch = _as_layer(stable_ch, context) or stable_ch

                            non_stable = _run(
                                "native:extractbyexpression",
                                {
                                    "INPUT": working_before_island_excl,
                                    "EXPRESSION": "\"EA\" <> 'stable_channel'",
                                    "OUTPUT": "TEMPORARY_OUTPUT",
                                },
                                context, feedback
                            )["OUTPUT"]
                            non_stable = _as_layer(non_stable, context) or non_stable

                            fc_stable_before = stable_ch.featureCount() if stable_ch and stable_ch.isValid() else 0
                            fc_nonstable = non_stable.featureCount() if non_stable and non_stable.isValid() else 0

                            if fc_stable_before == 0:
                                feedback.pushInfo("[ISLAND EXCL] No stable_channel polygons found; skipping.")
                            else:
                                # 3) Subtract island union from stable_channel only
                                stable_ch_clean = _safe_polygon_difference(
                                    stable_ch,
                                    island_union,
                                    context, feedback,
                                    tag=f"stable_channel_minus_islands_{y1}_{y2}",
                                    snap_grid=S["grid"],
                                    min_area=1e-6
                                )
                                stable_ch_clean = _as_layer(stable_ch_clean, context) or stable_ch_clean

                                # Clean ONLY the stable_channel result, not the merged full layer
                                if stable_ch_clean and stable_ch_clean.isValid() and stable_ch_clean.featureCount() > 0:
                                    stable_ch_clean = _fix_geoms(stable_ch_clean, context, feedback)
                                    stable_ch_clean = _force_2d_safe(stable_ch_clean, context, feedback)
                                    stable_ch_clean = _polys_only(stable_ch_clean, context, feedback)
                                    stable_ch_clean = _drop_null_tiny_polys(stable_ch_clean, 1e-6, context, feedback)
                                    stable_ch_clean = _as_layer(stable_ch_clean, context) or stable_ch_clean

                                fc_stable_after = (
                                    stable_ch_clean.featureCount()
                                    if stable_ch_clean and stable_ch_clean.isValid()
                                    else 0
                                )

                                # 4) Merge corrected stable_channel back with non_stable
                                merge_layers = []
                                if non_stable and non_stable.isValid() and non_stable.featureCount() > 0:
                                    merge_layers.append(non_stable)
                                if stable_ch_clean and stable_ch_clean.isValid() and stable_ch_clean.featureCount() > 0:
                                    merge_layers.append(stable_ch_clean)

                                if len(merge_layers) == 0:
                                    feedback.reportError(
                                        "[ISLAND EXCL] Merge candidate list empty; reverting to pre-exclusion working."
                                    )
                                    working = working_before_island_excl

                                elif len(merge_layers) == 1:
                                    merged_working = merge_layers[0]
                                    merged_working = _as_layer(merged_working, context) or merged_working

                                    if merged_working is None or not merged_working.isValid():
                                        feedback.reportError(
                                            "[ISLAND EXCL] Single-layer result invalid; reverting to pre-exclusion working."
                                        )
                                        working = working_before_island_excl
                                    elif merged_working.featureCount() == 0 and fc_before_all > 0:
                                        feedback.reportError(
                                            "[ISLAND EXCL] Single-layer result unexpectedly empty; reverting to pre-exclusion working."
                                        )
                                        working = working_before_island_excl
                                    else:
                                        working = merged_working

                                else:
                                    merged_working = _safe_feature_merge(
                                        merge_layers[0],
                                        merge_layers[1],
                                        f"working_island_excl_merge_{y1}_{y2}",
                                        context,
                                        feedback,
                                        crs=ref_crs_obj
                                    )

                                    merged_working = _freeze_to_tmp_gpkg(
                                        merged_working,
                                        context,
                                        feedback,
                                        f"working_island_excl_merge_{y1}_{y2}",
                                        ref_crs_obj
                                    )
                                    merged_working = _as_layer(merged_working, context) or merged_working

                                    # IMPORTANT:
                                    # do NOT run global _fix_geoms() here
                                    # this was the step that emptied the layer before
                                    if merged_working is None or not merged_working.isValid():
                                        feedback.reportError(
                                            "[ISLAND EXCL] Merged working invalid; reverting to pre-exclusion working."
                                        )
                                        working = working_before_island_excl
                                    elif merged_working.featureCount() == 0 and fc_before_all > 0:
                                        feedback.reportError(
                                            "[ISLAND EXCL] Merged working unexpectedly empty; reverting to pre-exclusion working."
                                        )
                                        working = working_before_island_excl
                                    else:
                                        working = merged_working

                                working_chk = _as_layer(working, context) or working
                                fc_after_all = (
                                    working_chk.featureCount()
                                    if working_chk and working_chk.isValid()
                                    else -1
                                )

                                feedback.pushInfo(
                                    "[ISLAND EXCL] stable_channel corrected by subtracting island union "
                                    f"(stable_before={fc_stable_before}, stable_after={fc_stable_after}, "
                                    f"non_stable={fc_nonstable}, total_before={fc_before_all}, "
                                    f"total_after={fc_after_all}, island_union_fc={island_union.featureCount()})"
                                )

            except Exception as e:
                feedback.reportError(
                    f"[ISLAND EXCL] stable_channel island exclusion failed; reverting to pre-exclusion working: {e}"
                )
                try:
                    working = working_before_island_excl
                except Exception:
                    pass
            
            _dbg_geom_stats(f"working_pre_finalpost_{y1}_{y2}", working, context, feedback)
            # (make sure env_union_outer exists earlier, once per pair)
            # env_union_outer = dissolve(env_union) -> deleteholes -> clean

            
                        # FINAL conservative post-processing
            # Preserve upstream EA classification.
            # Do not run heavy clip/cleanup here because it can perturb shared boundaries.
            # Only retain the existing working layer.
            # ------------------------------------------------------------------

            working_in = _as_layer(working, context) or working

            if working_in is None or not working_in.isValid():
                feedback.reportError("[FINAL POST] working invalid before final post-processing; skipping pair.")
                continue

            fc_before = working_in.featureCount()
            working = working_in

            # Collapse duplicate semantic fields created by upstream merges
            working = _collapse_authoritative_ea_fields(
                working, y1, y2, context, feedback
            )
            working = _freeze_to_tmp_gpkg(
                working,
                context,
                feedback,
                f"working_final_collapsed_{y1}_{y2}",
                ref_crs_obj
            )
            working = _as_layer(working, context) or working
            
            # ------------------------------------------------------------
            # B3: Add authoritative pairwise summary fields for Module 4a / 3B
            # ------------------------------------------------------------
            pair_mode = "dual_surface" if (raw_water and raw_active) else "classic_channel"

            if surface_mode == 0:
                surf_mode_label = "mamore"
            elif surface_mode == 1:
                surf_mode_label = "jamuna"
            else:
                surf_mode_label = "none"

            working = _add_pairwise_summary_fields(
                working,
                y1,
                y2,
                pair_mode,
                surf_mode_label,
                context,
                feedback
            )

            working = _freeze_to_tmp_gpkg(
                working,
                context,
                feedback,
                f"working_pair_summary_{y1}_{y2}",
                ref_crs_obj
            )
            working = _as_layer(working, context) or working

            if working is None or not working.isValid():
                feedback.reportError(
                    "[FINAL POST] working invalid after semantic field collapse; skipping pair."
                )
                continue
            _dbg_T_counts(working, y1, "working post-collapse")
            _dbg_T_counts(working, y2, "working post-collapse")
            if feedback:
                feedback.pushInfo(
                    f"[FINAL POST] Heavy final cleanup skipped; using working as-is (fc={fc_before})."
                )
            _dbg_geom_stats(f"working_post_finalpost_{y1}_{y2}", working, context, feedback)

            # ------------------------------------------------------------
            # DEBUG: write undissolved working layer before EA_processes dissolve
            # ------------------------------------------------------------
            formatted_start = _fmt_date(y1)
            formatted_end   = _fmt_date(y2)
            debug_work_layer = f"EA_working_debug_{formatted_start}_{formatted_end}"

            # FORCE CRS BACK BEFORE WRITE
            working = _force_crs(working, ref_crs_obj, context, feedback, f"working_{y1}_{y2}")
            _dbg_geom_stats(f"working_post_forcecrs_{y1}_{y2}", working, context, feedback)

            if DEBUG_SAVE:
                _write_gpkg(
                    working,
                    gpkg_path,
                    debug_work_layer,
                    context,
                    overwrite=True,
                    feedback=feedback
                )
                _dbg_written_gpkg(gpkg_path, debug_work_layer, feedback)

            feedback.pushInfo("[EA] Dissolving to EA_processes…")

            eadiss = _run(
                "native:dissolve",
                {
                    "INPUT": working,
                    "FIELD": [
                        "EA",
                        "PROC_GROUP",
                        "STATE_T1",
                        "STATE_T2",
                        "STATE_1",
                        "STATE_2",
                        "ACTIVE_T1",
                        "ACTIVE_T2",
                        "ACTIVE_DOM",
                        "DOMAIN_T1",
                        "DOMAIN_T2",
                        "DOMAIN_1",
                        "DOMAIN_2",
                        "SURFACE_T1",
                        "SURFACE_T2",
                        "DOMAIN_TRANS",
                        "DIST_EVENT",
                        "DIST_TYPE",
                        "DEPO_INTERP",
                        "ONTOLOGY",
                        "PAIR_MODE",
                        "SURF_MODE",
                        "direction",
                        "period",
                        "span_days",
                        "span_years",
                        "migration",
                        "PeriodEnd"   # ✅ CRITICAL
                    ],
                    "SEPARATE_DISJOINT": True,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
                context, feedback
            )["OUTPUT"]

            eadiss = _run(
                "native:multiparttosingleparts",
                {"INPUT": eadiss, "OUTPUT": "TEMPORARY_OUTPUT"},
                context, feedback
            )["OUTPUT"]

            eadiss = _fix_geoms(eadiss, context, feedback)
            eadiss = _force_2d_safe(eadiss, context, feedback)
            eadiss = _polys_only(eadiss, context, feedback)
            eadiss = _drop_null_tiny_polys(eadiss, 1e-6, context, feedback)
            eadiss = _as_layer(eadiss, context) or eadiss

            if eadiss is None or not eadiss.isValid():
                feedback.reportError("[EA] eadiss invalid after dissolve cleanup; skipping pair.")
                continue

            feedback.pushInfo(f"[EA] EA_processes dissolved featureCount={eadiss.featureCount()}")
            _dbg_geom_stats(f"eadiss_post_cleanup_{y1}_{y2}", eadiss, context, feedback)

            # FORCE CRS BACK BEFORE WRITE
            eadiss = _force_crs(eadiss, ref_crs_obj, context, feedback, f"eadiss_{y1}_{y2}")
            _dbg_geom_stats(f"eadiss_post_forcecrs_{y1}_{y2}", eadiss, context, feedback)

            layer_proc = f"EA_processes_{formatted_start}_{formatted_end}"
            feedback.pushInfo(f"[DEBUG] Attempting to write: {gpkg_path} → {layer_proc}")

            key = (gpkg_path, layer_proc)
            if key in _written_once:
                feedback.pushInfo(f"[WRITE] Skipping duplicate write: {layer_proc}")
                written = gpkg_path
            else:
                written = _write_gpkg(
                    eadiss,
                    gpkg_path,
                    layer_proc,
                    context,
                    overwrite=True,
                    feedback=feedback
                )
                if not written:
                    raise QgsProcessingException(
                        f"[WRITE] Failed to write '{layer_proc}' to {gpkg_path}. "
                        "Check file locks/permissions and that the layer has features."
                    )

                _written_once.add(key)
                feedback.pushInfo(f"[WRITE] Wrote '{layer_proc}' → {gpkg_path}")
                _dbg_written_gpkg(gpkg_path, layer_proc, feedback)
                EAprocess_outputs.append(layer_proc)

            # ---------- Segments + rates (if stats layer provided) ----------
            if stats:
                # EAsegments_y1_y2: intersection of EA_processes with a segments/stats layer
                seg = _intersect_polys(eadiss, stats, context, feedback)
                seg = _run(
                    "native:multiparttosingleparts",
                    {"INPUT": seg, "OUTPUT": "TEMPORARY_OUTPUT"},
                    context, feedback
                )["OUTPUT"]

                # Remove fid fields to avoid PK conflicts in GPKG
                names = _as_layer(seg, context).fields().names()
                drop = [n for n in names if n.lower() == "fid"]
                if drop:
                    seg = _run(
                        "native:deletecolumn",
                        {"INPUT": seg, "COLUMN": drop, "OUTPUT": "TEMPORARY_OUTPUT"},
                        context, feedback
                    )["OUTPUT"]

                feedback.pushInfo(
                    f"[DEBUG] EAsegments {y1}->{y2} count: {_as_layer(seg, context).featureCount()}"
                )
                _write_gpkg(seg, gpkg_path, f"EAsegments_{y1}_{y2}", context,
                            overwrite=True, feedback=feedback)

                # EA_rate: dissolved by period and migration, then intersected with stats
                diss = _run(
                    "native:dissolve",
                    {
                        "INPUT": eadiss,
                        "FIELD": ["period", "span_days", "span_years", "migration", "EA"],
                        "SEPARATE_DISJOINT": False,
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]


                eainter = _intersect_polys(diss, stats, context, feedback)

                # EA_rate_A: area / time (positive for erosion, negative for deposition)
                eainter = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": eainter,
                        "FIELD_NAME": "EA_rate_A",
                        "FIELD_TYPE": 0,
                        "FIELD_LENGTH": 20,
                        "FIELD_PRECISION": 8,
                        "NEW_FIELD": True,
                        "FORMULA": (
                            "CASE "
                            "WHEN \"migration\"='in-channel process' OR \"span_days\"=0 THEN 0 "
                            "WHEN \"migration\" LIKE 'erosion%' THEN $area / \"span_days\" "
                            "WHEN \"migration\" LIKE 'deposition%' THEN -($area / \"span_days\") "
                            "ELSE 0 END"
                        ),
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]

                # EA_rate_m: area-based rate normalized by interval (m per day per interval)
                eainter = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": eainter,
                        "FIELD_NAME": "EA_rate_m",
                        "FIELD_TYPE": 0,
                        "FIELD_LENGTH": 20,
                        "FIELD_PRECISION": 8,
                        "NEW_FIELD": True,
                        "FORMULA": (
                            f"CASE WHEN \"EA_rate_A\" IS NULL THEN 0 "
                            f"ELSE \"EA_rate_A\" / {float(interval)} END"
                        ),
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]

                # EA_disp_m: displacement over the full period (EA_rate_m * span_days)
                eainter = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": eainter,
                        "FIELD_NAME": "EA_disp_m",
                        "FIELD_TYPE": 0,
                        "FIELD_LENGTH": 20,
                        "FIELD_PRECISION": 6,
                        "NEW_FIELD": True,
                        "FORMULA": (
                            "CASE WHEN \"migration\"='in-channel process' THEN 0 "
                            "ELSE \"EA_rate_m\" * \"span_days\" END"
                        ),
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]

                # EA_rate_m_py: per-year rate (EA_rate_m * 365)
                eainter = _run(
                    "native:fieldcalculator",
                    {
                        "INPUT": eainter,
                        "FIELD_NAME": "EA_rate_m_py",
                        "FIELD_TYPE": 0,
                        "FIELD_LENGTH": 20,
                        "FIELD_PRECISION": 6,
                        "NEW_FIELD": True,
                        "FORMULA": (
                            "CASE WHEN \"migration\"='in-channel process' THEN 0 "
                            "ELSE \"EA_rate_m\" * 365.0 END"
                        ),
                        "OUTPUT": "TEMPORARY_OUTPUT",
                    },
                    context, feedback
                )["OUTPUT"]

                # Trim to keep only rate-related fields
                keep_rate = [
                    "migration", "period", "span_days", "span_years",
                    "EA_rate_A", "EA_rate_m", "EA_disp_m", "EA_rate_m_py",
                    "PeriodEnd",
                ]
                names = _as_layer(eainter, context).fields().names()
                drop = [n for n in names if (n not in keep_rate and n.lower() != "fid")]
                if drop:
                    eainter = _run(
                        "native:deletecolumn",
                        {"INPUT": eainter, "COLUMN": drop, "OUTPUT": "TEMPORARY_OUTPUT"},
                        context, feedback
                    )["OUTPUT"]

                feedback.pushInfo(
                    f"[DEBUG] EA_rate {y1}->{y2} count: {_as_layer(eainter, context).featureCount()}"
                )
                _write_gpkg(eainter, gpkg_path, f"EA_rate_{y1}_{y2}", context,
                            overwrite=True, feedback=feedback)
                
        # Return list of process layers written (for QGIS UI / debugging)
        return {"EA_PROCESSES": EAprocess_outputs}


        # QGIS looks for this when loading the script
def classFactory():
    """
    Factory function for QGIS to instantiate the Processing algorithm.
    """
    return Module3_EAcalculation_QGIS()