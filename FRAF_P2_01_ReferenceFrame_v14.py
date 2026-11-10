# -*- coding: utf-8 -*-
"""FRAF Paper 2 | 01 — Reference Frame | v14.

Purpose
-------
Generate a representative channel centreline from dated channel polygons,
or a single reference centreline from the union of all mapped channel extents.
The latter is a spatial reference geometry; it is not a dated channel position.

Provenance and attribution
--------------------------
Original methodological/software foundation: Standalone Channel Shifting
(SCS) Toolbox, attributed in the inherited source to Miloš Rusnák.
Please cite Rusnák et al. (2025) in publications using this adaptation;
the complete bibliographic details should be verified against the paper.

PyQGIS port/adaptation: Martin Dawson, with ChatGPT assistance (November 2025).
This file documents the inherited v14 implementation; it does not claim
that Rusnák et al. authored the FRAF modifications or this Python port.

Environment
-----------
QGIS Processing (native/GDAL), OSGeo4W on Windows, GRASS GIS 8.x via BAT
launcher. Original source reports QGIS 3.40.11 and GRASS 8.5; launcher
selection preferentially seeks grass84.bat. Compatibility with other
versions requires testing.

Operational modes
-----------------
UNION_MODE=True: dissolve all observations into a combined footprint,
remove holes, optionally simplify, derive and prune skeleton, retain its
longest merged line, and save SegCenterline.gpkg. The assigned Year/cnt
in this mode is a placeholder based on the earliest mapped year, NOT a
physical date for the union geometry.
UNION_MODE=False: group polygons by mapped year and export centro_YYYY0101;
optionally combine them into centerlines_merged.gpkg.

Methodological qualifications
-----------------------------
* Skeletonization uses GRASS v.voronoi -s and v.clean rmdangle; if GRASS
  fails, a QGIS Voronoi-based fallback is attempted.
* Selection of the longest merged line is a heuristic, not a guarantee of
  a hydrologically correct main channel or complete braided network.
* Year-only observations are tagged January 1 for file/attribute naming;
  this does not imply survey occurred on that day.
* Distances, length thresholds, and simplification tolerances use CRS map
  units. Choose a projected CRS in metres when using metre defaults.
* Existing output GeoPackages with the same names may be replaced.
* Temporary intermediate Shapefiles may truncate field names; verify
  resulting schemas before using them downstream.
* The optional GRASS_REGION, VIN_SNAP, and VIN_MINAREA values are accepted
  for interface compatibility but are not applied in the GRASS CLI path.

Preservation policy
-------------------
Documentation-only revision: original v14 execution logic, algorithm ID,
parameters, output names, and numeric defaults are deliberately unchanged.
"""

from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessing, QgsProcessingException,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterString, QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber, QgsProcessingParameterExtent,
    QgsProcessingParameterCrs, QgsProcessingOutputString,
    QgsVectorLayer, QgsWkbTypes, QgsApplication, QgsProject, QgsProcessingUtils,
    QgsSettings
)
from qgis.PyQt.QtCore import QCoreApplication

import processing
import shutil
import glob
import os
import tempfile
import uuid
import re
import subprocess
from datetime import date

# ---------------- globals ---------------- #

_TRACKED_DIRS = []  # temp workspace tracker


# ---------------- helpers ---------------- #

def tr(s):
    """Translate a UI label within the SCS_Centerlines Qt translation context."""
    return QCoreApplication.translate("SCS_Centerlines", s)


def _temp_path_tracked(stem="tmp_", ext=".shp"):
    """
    Create a path to a temporary file in a single tracked temp directory.
    """
    if not _TRACKED_DIRS:
        tmpdir = tempfile.mkdtemp(prefix="scs_mod1_")
        _TRACKED_DIRS.append(tmpdir)
    else:
        tmpdir = _TRACKED_DIRS[0]
    return os.path.join(tmpdir, f"{stem}{uuid.uuid4().hex}{ext}")


def _cleanup_tmp_dirs(feedback=None):
    """
    Remove all tracked temporary directories.
    """
    for path in list(_TRACKED_DIRS):
        try:
            shutil.rmtree(path, ignore_errors=True)
            if feedback:
                feedback.pushInfo(f"[cleanup] removed {path}")
        except Exception as e:
            if feedback:
                feedback.reportError(f"[cleanup] failed to remove {path}: {e}")
        finally:
            try:
                _TRACKED_DIRS.remove(path)
            except Exception:
                pass


def as_layer(x, name_hint="layer"):
    """
    Resolve a QgsVectorLayer from:
      - an existing QgsVectorLayer object,
      - a layer ID / map layer string,
      - or a file path.
    """
    if isinstance(x, QgsVectorLayer):
        if not x.isValid():
            raise QgsProcessingException(f"{name_hint} is invalid")
        return x

    if isinstance(x, str):
        try:
            lyr = QgsProcessingUtils.mapLayerFromString(x, QgsProject.instance())
            if lyr and lyr.isValid():
                return lyr
        except Exception:
            pass

    if isinstance(x, str):
        lyr = QgsVectorLayer(x, name_hint, "ogr")
        if not lyr.isValid():
            raise QgsProcessingException(f"Failed to load {name_hint}: {x}")
        return lyr

    raise QgsProcessingException(f"Unexpected type for {name_hint}: {type(x)}")


def _resolve_field_name(layer_or_path, desired_name):
    """
    Case-insensitive lookup of desired_name in layer fields.
    """
    lyr = as_layer(layer_or_path, "field_resolve")
    want = (desired_name or "").strip().lower()
    for f in lyr.fields():
        nm = f.name()
        if nm.strip().lower() == want:
            return nm
    return None


def runp(alg_id, params, context=None, feedback=None, tag="", expect_key="OUTPUT"):
    """
    Wrapper around processing.run that logs to feedback and returns a best-guess output.
    """
    if feedback:
        try:
            pretty = "; ".join(f"{k}={v}" for k, v in params.items())
            feedback.pushInfo(f"▶ {alg_id}{' ['+tag+']' if tag else ''}: {pretty}")
        except Exception:
            feedback.pushInfo(f"▶ {alg_id}{' ['+tag+']' if tag else ''}")

    res = processing.run(alg_id, params, context=context, feedback=feedback)

    if isinstance(res, dict) and expect_key in res:
        return res[expect_key]

    if isinstance(res, dict):
        for k in ("OUTPUT", "output", "OUTPUT_LAYER", "OUTPUTFILE", "OUTPUT_PATH", "FILE_PATH"):
            if k in res:
                return res[k]
        if len(res) == 1:
            return next(iter(res.values()))
    return res


def freeze_to_shp(input_ref, context=None, feedback=None, tag="freeze"):
    """
    Force any layer/id/URI to a fresh, file-backed ESRI Shapefile.
    """
    tmp_shp = _temp_path_tracked("fz_", ".shp")
    runp("native:savefeatures", {"INPUT": input_ref, "OUTPUT": tmp_shp},
         context, feedback, tag)
    return tmp_shp


def _copy_shp_tree(src_shp_path, dst_shp_path):
    """
    Copy a SHP “tree” (.shp, .shx, .dbf, .prj, etc.) from src to dst.
    """
    src_base, _ = os.path.splitext(src_shp_path)
    dst_base, _ = os.path.splitext(dst_shp_path)
    folder = os.path.dirname(src_shp_path)
    stem = os.path.basename(src_base)
    for extpath in glob.glob(os.path.join(folder, stem + ".*")):
        ext = os.path.splitext(extpath)[1]
        shutil.copy2(extpath, dst_base + ext)


# ---------------- GRASS BAT launcher + env ---------------- #

def _find_grass_bat(prefer_version="84"):
    """
    Return full path to an OSGeo4W GRASS launcher BAT.
    Prefer GRASS 8.4 (grass84.bat) since that's what you have installed.
    """
    root = os.environ.get("OSGEO4W_ROOT", r"C:\OSGeo4W")

    # Prefer explicit version first
    preferred = []
    if prefer_version == "84":
        preferred = ["grass84.bat", "grass.bat"]
    elif prefer_version == "85":
        preferred = ["grass85.bat", "grass.bat"]
    else:
        preferred = [f"grass{prefer_version}.bat", "grass.bat"]

    candidates = []
    for g in preferred + ["grass83.bat", "grass82.bat", "grass81.bat", "grass80.bat", "grass78.bat"]:
        candidates.append(os.path.join(root, "bin", g))

    # Return first existing
    for p in candidates:
        if os.path.exists(p):
            return p

    return None
    


def _guess_gisbase_from_bat(grass_bat, prefer_versions=("84", "83", "82", "81", "80")):
    """
    Infer GISBASE from grassXX.bat -> C:\\OSGeo4W\\apps\\grass\\grassXX.

    For grass.bat (unversioned), prefer_versions controls which installed GRASS
    we choose first (defaults to 8.4 then older).
    """
    root = os.environ.get("OSGEO4W_ROOT", r"C:\OSGeo4W")
    bn = os.path.basename(grass_bat).lower()

    # 1) If explicit versioned launcher (grass84.bat)
    m = re.search(r"grass(\d{2})\.bat$", bn)
    if m:
        ver = m.group(1)  # e.g. "84"
        gisbase = os.path.join(root, "apps", "grass", f"grass{ver}")
        if os.path.isdir(gisbase):
            return gisbase

    # 2) If unversioned grass.bat, choose the best installed version (prefer 84)
    if bn == "grass.bat":
        for v in prefer_versions:
            cand = os.path.join(root, "apps", "grass", f"grass{v}")
            if os.path.isdir(cand):
                return cand

    # 3) Last resort: try to find any grass8* BUT still honour prefer_versions first
    grass_root = os.path.join(root, "apps", "grass")
    if os.path.isdir(grass_root):
        # First try known preferred versions (again)
        for v in prefer_versions:
            cand = os.path.join(grass_root, f"grass{v}")
            if os.path.isdir(cand):
                return cand

        # Then any other grass8* directory (avoid grass85 by default)
        cands = []
        for d in os.listdir(grass_root):
            dl = d.lower()
            if re.match(r"grass8\d", dl) and dl not in {"grass85"}:
                full = os.path.join(grass_root, d)
                if os.path.isdir(full):
                    cands.append(full)
        if cands:
            cands.sort(reverse=True)
            return cands[0]

    return None


def _grass_env_for_osgeo4w(grass_bat):
    """
    Build an env dict for subprocess calls that makes GRASS reliable from PyQGIS.

    Fixes:
      RuntimeError: The grass Python package is missing

    by injecting:
      GISBASE, PYTHONPATH += <GISBASE>\\etc\\python, and PATH additions.
    """
    env = os.environ.copy()
    root = os.environ.get("OSGEO4W_ROOT", r"C:\OSGeo4W")
    gisbase = _guess_gisbase_from_bat(grass_bat)

    if gisbase and os.path.isdir(gisbase):
        env["GISBASE"] = gisbase

        etc_py = os.path.join(gisbase, "etc", "python")
        if os.path.isdir(etc_py):
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (etc_py + (os.pathsep + old if old else ""))

        add_paths = [
            os.path.join(root, "bin"),
            os.path.join(gisbase, "bin"),
            os.path.join(gisbase, "lib"),
        ]
        oldp = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(add_paths + [oldp])

    env.setdefault("GRASS_MESSAGE_FORMAT", "plain")
    env.setdefault("GRASS_GUI", "text")
    return env

def _run_cmd(cmd, feedback=None, cwd=None, env=None, timeout_sec=None):
    """
    Run an external command safely (Windows / GRASS compatible).

    - Captures stdout/stderr
    - Raises QgsProcessingException on failure
    - Optional timeout to prevent hangs
    """
    if feedback:
        feedback.pushInfo("CMD: " + " ".join(map(str, cmd)))

    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=False,
            timeout=timeout_sec  # <-- FIX
        )
    except subprocess.TimeoutExpired:
        raise QgsProcessingException(f"External command timed out after {timeout_sec}s:\n" + " ".join(map(str, cmd)))
    except Exception as e:
        raise QgsProcessingException(f"Failed to run command: {e}")

    if p.stdout and feedback:
        feedback.pushInfo(p.stdout.strip())

    if p.returncode != 0:
        msg = p.stderr.strip() if p.stderr else "Unknown error"
        raise QgsProcessingException(f"External command failed (exit {p.returncode}):\n{msg}")

    return p.stdout

def _grass_exec(grass_bat, mapset_path, args, feedback=None, env=None, timeout_sec=None):
    """
    Execute a GRASS module non-interactively inside a given MAPSET path.
    """
    cmd = [grass_bat, mapset_path, "--exec"] + list(args)
    _run_cmd(cmd, feedback=feedback, env=env, timeout_sec=timeout_sec)


# ---------------- outputs ---------------- #

def save_gpkg_clean(layer_or_id, gpkg_path, context=None, feedback=None,
                    layer_name=None, force_multiline=False):
    """
    Final GPKG writer:
      - freeze to SHP
      - drop fid-like fields
      - gdal:convertformat SHP -> GPKG
    """
    parent = os.path.dirname(gpkg_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    tmp_shp = freeze_to_shp(layer_or_id, context, feedback, tag="freeze_before_final")
    src_layer = as_layer(tmp_shp, "final_for_droptest")

    drop = [f.name() for f in src_layer.fields()
            if f.name().lower() in {"fid", "ogc_fid", "id", "gid", "pk"}]

    shp_for_convert = tmp_shp
    if drop:
        shp_for_convert = _temp_path_tracked("final_drop_", ".shp")
        runp("native:deletecolumn",
             {"INPUT": tmp_shp, "COLUMN": drop, "OUTPUT": shp_for_convert},
             context, feedback, "drop_id")

    if os.path.exists(gpkg_path):
        try:
            os.remove(gpkg_path)
        except Exception:
            pass

    unique_layer = layer_name or f"layer_{uuid.uuid4().hex[:8]}"
    opts = "-nlt MULTILINESTRING" if force_multiline else ""

    runp("gdal:convertformat",
         {"INPUT": shp_for_convert,
          "OPTIONS": opts,
          "OUTPUT": gpkg_path,
          "LAYER_NAME": unique_layer},
         context, feedback, "shp_to_gpkg")
    return gpkg_path


# ---------------- year handling ---------------- #

def _safe_years(layer_or_path, year_field):
    """
    Return sorted list of unique valid years detected in YEAR_FIELD.
    """
    lyr = as_layer(layer_or_path, "year_scan")
    real = _resolve_field_name(lyr, year_field)
    if not real:
        return []

    idx = lyr.fields().indexFromName(real)
    fld = lyr.fields()[idx]
    tname = (fld.typeName() or "").lower()
    years = set()

    for feat in lyr.getFeatures():
        v = feat[real]
        if v is None:
            continue
        try:
            if any(key in tname for key in ("int", "integer", "real", "double", "numeric", "decimal")):
                y = int(v)
            elif "date" in tname or "time" in tname:
                if hasattr(v, "year"):
                    y = int(v.year())
                else:
                    y = int(str(v)[:4])
            else:
                m = re.search(r"(18|19|20)\d{2}", str(v))
                if not m:
                    continue
                y = int(m.group(0))
            if 1800 <= y <= 2100:
                years.add(y)
        except Exception:
            continue

    return sorted(years)


def _subset_by_year(layer_or_path, year_field, yval, context, feedback):
    """
    SHP subset where YEAR_FIELD == yval, returns SHP path or None if empty.
    """
    lyr = as_layer(layer_or_path, "subset_src")
    real = _resolve_field_name(lyr, year_field)
    if not real:
        feedback.pushInfo(f"[subset_by_year] Year field '{year_field}' not found.")
        return None

    idx = lyr.fields().indexFromName(real)
    fld = lyr.fields()[idx]
    tname = (fld.typeName() or "").lower()
    y = int(yval)

    if any(key in tname for key in ("int", "integer", "real", "double", "numeric", "decimal")):
        expr = f"\"{real}\" = {y}"
        if "real" in tname or "double" in tname or "decimal" in tname or "numeric" in tname:
            expr = f"round(\"{real}\") = {y}"

    elif "date" in tname or "time" in tname:
        expr = f"year(\"{real}\") = {y}"

    elif any(k in tname for k in ("string", "text", "char")):
        # robust against trailing spaces
        expr = f"trim(\"{real}\") = '{y}'"

    else:
        expr = f"regexp_substr(coalesce(tostring(\"{real}\"),''), '(18|19|20)\\d{{2}}') = '{y}'"



    subset_shp = _temp_path_tracked(f"subset_{y}_", ".shp")
    runp("native:extractbyexpression",
         {"INPUT": layer_or_path, "EXPRESSION": expr, "OUTPUT": subset_shp},
         context, feedback, "subset_expr_to_file")

    lyr_out = as_layer(subset_shp, f"subset_{y}")
    cnt = lyr_out.featureCount()
    feedback.pushInfo(f"[subset_by_year] year={y} count={cnt}")
    if cnt == 0:
        return None

    return subset_shp


def _reproject_to_target(src_layer, target_crs, context, feedback):
    """
    Reproject only if needed; otherwise freeze to SHP.
    """
    lyr = as_layer(src_layer, "reproj_src")
    try:
        if lyr.crs() == target_crs:
            return freeze_to_shp(lyr, context, feedback, tag="freeze_same_crs")
    except Exception:
        pass

    out_shp = _temp_path_tracked("reproj_", ".shp")
    runp("native:reprojectlayer",
         {"INPUT": lyr, "TARGET_CRS": target_crs, "OPERATION": "", "OUTPUT": out_shp},
         context, feedback, "reproject_to_target_shp")
    return out_shp


# ---------------- attributes ---------------- #

def add_date_field(input_id, date_value, context, feedback):
    """Attach the cnt date attribute to the derived centreline geometry."""
    out_shp = _temp_path_tracked("add_date_", ".shp")
    runp("native:fieldcalculator",
         {"INPUT": input_id, "FIELD_NAME": "cnt", "FIELD_TYPE": 3,
          "FIELD_LENGTH": 0, "FIELD_PRECISION": 0, "NEW_FIELD": True,
          "FORMULA": f"to_date('{date_value}')", "OUTPUT": out_shp},
         context, feedback, "add_date_to_shp")
    return out_shp


def add_length_field(input_id, context, feedback):
    """Calculate a length attribute using QGIS $length in the processing context."""
    out_shp = _temp_path_tracked("add_length_", ".shp")
    runp("native:fieldcalculator",
         {"INPUT": input_id, "FIELD_NAME": "length", "FIELD_TYPE": 0,
          "FIELD_LENGTH": 20, "FIELD_PRECISION": 3, "NEW_FIELD": True,
          "FORMULA": "$length", "OUTPUT": out_shp},
         context, feedback, "add_length_to_shp")
    return out_shp


def add_year_field(input_id, year_value, context, feedback):
    """Replace any existing Year column with an integer observation-year tag."""
    src = as_layer(input_id, "add_year_src")
    fields = [f.name() for f in src.fields()]
    stage = input_id

    if "Year" in fields:
        dropped = _temp_path_tracked("drop_year_", ".shp")
        runp("native:deletecolumn",
             {"INPUT": stage, "COLUMN": ["Year"], "OUTPUT": dropped},
             context, feedback, "drop_existing_Year")
        stage = dropped

    out_shp = _temp_path_tracked("add_year_", ".shp")
    runp("native:fieldcalculator",
         {"INPUT": stage, "FIELD_NAME": "Year", "FIELD_TYPE": 1,
          "FIELD_LENGTH": 10, "FIELD_PRECISION": 0, "NEW_FIELD": True,
          "FORMULA": str(int(year_value)), "OUTPUT": out_shp},
         context, feedback, "add_Year_int")

    try:
        lyr = as_layer(out_shp, "year_check")
        has = "Year" in [f.name() for f in lyr.fields()]
        feedback.pushInfo(f"[add_year_field] Year={year_value} field created: {has}")
    except Exception:
        pass

    return out_shp


def _tag_and_measure(center_path, date_value, context, feedback):
    """Attach centreline class, date, and length attributes in sequence."""
    tagged = _temp_path_tracked("tag_center_", ".shp")
    runp("native:fieldcalculator",
         {"INPUT": center_path, "FIELD_NAME": "Centerln", "FIELD_TYPE": 2,
          "FIELD_LENGTH": 20, "FIELD_PRECISION": 0, "NEW_FIELD": True,
          "FORMULA": "'centerline'", "OUTPUT": tagged},
         context, feedback, "tag_center_to_shp")

    with_date = add_date_field(tagged, date_value, context, feedback)
    return add_length_field(with_date, context, feedback)


# ---------------- cleaning ---------------- #

def _clean_channel(poly_id, context, feedback):
    """Repair polygon geometry and remove interior holes before skeletonization."""
    in_path = freeze_to_shp(poly_id, context, feedback, tag="freeze_before_fix")

    fixed = _temp_path_tracked("fixed_", ".shp")
    runp("native:fixgeometries", {"INPUT": in_path, "OUTPUT": fixed},
         context, feedback, "fixgeom_to_shp")

    cleaned = _temp_path_tracked("cleaned_noholes_", ".shp")
    runp("native:deleteholes",
         {"INPUT": fixed, "MIN_AREA": 0.0, "OUTPUT": cleaned},
         context, feedback, "delholes_to_shp")

    if as_layer(cleaned, "clean_chk").featureCount() == 0:
        raise QgsProcessingException("Empty polygon after cleaning.")
    return cleaned


# ---------------- GRASS skeleton ---------------- #

def _grass_skeleton_from_polygon(poly_id, context, feedback,
                                 factor=None, max_dangle=None, region=None,
                                 vin_snap=None, vin_minarea=None,
                                 flag_skeleton=True, flag_graph=False,
                                 flag_noattr=True):

    # GRASS CLI expects a disk-backed vector; the conversion also isolates provider state.
    # 0) Freeze polygon to SHP
    """Derive a pruned centreline skeleton from a polygon using GRASS CLI.
    
    Create a temporary GRASS location, import the polygon, compute a
    Voronoi skeleton, prune dangles, export, clip and filter short lines.
    The final main-line selection is performed separately."""
    shp_in = freeze_to_shp(poly_id, context, feedback, tag="freeze_poly_for_grass_cli")
    lyr_chk = as_layer(shp_in, "grass_poly_chk")
    if lyr_chk.featureCount() == 0:
        raise QgsProcessingException("GRASS CLI: empty polygon layer after freeze.")

    # 1) Find GRASS launcher (prefer 8.4)
    grass_bat = _find_grass_bat(prefer_version="84")
    if not grass_bat:
            raise QgsProcessingException("Could not find C:\\OSGeo4W\\bin\\grass84.bat")

    grass_env = _grass_env_for_osgeo4w(grass_bat)


    # 2) Dedicated temp workspace for GRASS
    tmpdir = tempfile.mkdtemp(prefix="scs_grass_")
    _TRACKED_DIRS.append(tmpdir)

    gisdbase = os.path.join(tmpdir, "gisdbase")
    os.makedirs(gisdbase, exist_ok=True)
    location = "loc"

    # Copy SHP into tmpdir (short + stable paths)
    shp_local = os.path.join(tmpdir, "poly_in.shp")
    _copy_shp_tree(shp_in, shp_local)

    # 3) Create GRASS location (NON-INTERACTIVE)
    loc_path = os.path.join(gisdbase, location)
    if os.path.isdir(loc_path):
        shutil.rmtree(loc_path, ignore_errors=True)

    # IMPORTANT: use --text and -e to avoid interactive hangs
    _run_cmd([grass_bat, "--text", "-c", shp_local, "-e", loc_path],
         feedback=feedback, env=grass_env, timeout_sec=120)


    mapset_path = os.path.join(loc_path, "PERMANENT")
    if not os.path.isdir(mapset_path):
        raise QgsProcessingException(f"Failed to create GRASS Location (PERMANENT missing): {mapset_path}")

    # 4) Region from polygon extent (CRS-correct)
    ext = lyr_chk.extent()
    pad = max(ext.width(), ext.height()) * 0.02 or 1.0
    w = ext.xMinimum() - pad
    e = ext.xMaximum() + pad
    s = ext.yMinimum() - pad
    n = ext.yMaximum() + pad

    smoothness = float(factor) if factor is not None else 0.25
    thin = -1.0



    shp_out = os.path.join(tmpdir, "skel.shp")

    # 5) g.region
    _grass_exec(grass_bat, mapset_path, ["g.region", f"n={n}", f"s={s}", f"e={e}", f"w={w}"],
            feedback=feedback, env=grass_env, timeout_sec=120)

    # 6) v.import
    
    _grass_exec(grass_bat, mapset_path, ["v.import", f"input={shp_local}", "output=poly_native", "--overwrite"],
            feedback=feedback, env=grass_env, timeout_sec=300)

    # ===================== (1) GRASS: prune skeleton with v.clean rmdangle + export skel_clean =====================
    # Drop-in edits inside _grass_skeleton_from_polygon(), replacing steps 7–8 (and adjusting v.out.ogr input)

    # Skeleton geometry is controlled by smoothness and the -s/-g/-t flags.
    # 7) v.voronoi skeleton
    vv = ["v.voronoi", "input=poly_native",
          f"smoothness={smoothness}", f"thin={thin}",
          "output=skel_raw", "--overwrite"]
    if flag_skeleton:
        vv.insert(1, "-s")
    if flag_graph:
        vv.insert(1, "-g")
    if flag_noattr:
        vv.insert(1, "-t")

    _grass_exec(grass_bat, mapset_path, vv, feedback=feedback, env=grass_env, timeout_sec=900)

    # Dangle threshold is in map units; excessive pruning can remove real branches.
    # 7b) v.clean rmdangle (prune dangling hairs)
    # If max_dangle is None, choose a conservative default.
    try:
        dthresh = float(max_dangle) if max_dangle not in (None, "", "None") else 250.0
    except Exception:
        dthresh = 250.0


    _grass_exec(grass_bat, mapset_path,
                ["v.clean",
                 "input=skel_raw",
                 "output=skel_clean",
                 "tool=rmdangle",
                 f"threshold={dthresh}",
                 "--overwrite"],
                feedback=feedback, env=grass_env, timeout_sec=900)


    # 8) v.out.ogr  (export CLEAN skeleton)
    # NOTE: ESRI_Shapefile is a datasource; GRASS may create a folder, not a single .shp path.
    out_ds = os.path.join(tmpdir, "skel_export")  # datasource folder (safe)
    try:
        if os.path.exists(out_ds):
            shutil.rmtree(out_ds, ignore_errors=True)
    except Exception:
        pass
    os.makedirs(out_ds, exist_ok=True)

    _grass_exec(
        grass_bat, mapset_path,
        ["v.out.ogr",
         "input=skel_clean",          # <- export cleaned
         "type=line",
         f"output={out_ds}",
         "format=ESRI_Shapefile",
         "--overwrite"],
        feedback=feedback, env=grass_env, timeout_sec=180
    )

    # Find the produced .shp (GRASS will name it after the input map, typically skel_clean.shp)
    shp_candidates = glob.glob(os.path.join(out_ds, "*.shp"))
    if not shp_candidates:
        shp_candidates = glob.glob(os.path.join(out_ds, "**", "*.shp"), recursive=True)

    if not shp_candidates:
        raise QgsProcessingException("GRASS v.out.ogr produced no .shp in export datasource.")

    # Prefer shapefile named after map, else newest
    preferred = [p for p in shp_candidates if os.path.basename(p).lower().startswith("skel_clean")]
    shp_out = preferred[0] if preferred else max(shp_candidates, key=os.path.getmtime)

    # Validate exported lines load correctly
    lyr_out = QgsVectorLayer(shp_out, "skel_clean_export", "ogr")
    if not lyr_out.isValid() or lyr_out.featureCount() == 0:
        raise QgsProcessingException(f"Exported skeleton SHP is invalid/empty: {shp_out}")

    # 9) Clip back to polygon
    clipped = _temp_path_tracked("skel_clip_", ".shp")
    clip_res = runp("native:clip",
                    {"INPUT": shp_out, "OVERLAY": shp_in, "OUTPUT": clipped},
                    context, feedback, "clip_skel_to_poly")

    if not clip_res or not os.path.exists(clipped):
        raise QgsProcessingException("native:clip returned no output for skeleton clip.")

    lyr_clip = QgsVectorLayer(clipped, "skel_clip", "ogr")
    if not lyr_clip.isValid() or lyr_clip.featureCount() == 0:
        raise QgsProcessingException("Clipped skeleton is empty/invalid after native:clip.")

    # Fixed 50-unit filter is not scale-neutral; review for small-river applications.
    # 9b) Remove very short segments after clipping (prevents tiny fragments)
    min_len = 50.0  # meters (Mamoré: 50–150 typical)
    filtered = _temp_path_tracked("skel_clip_filt_", ".shp")
    runp("native:extractbyexpression",
        {"INPUT": clipped, "EXPRESSION": f"$length >= {min_len}", "OUTPUT": filtered},
        context, feedback, "clip_len_filter")

    # Prefer filtered if it has features
    try:
        if as_layer(filtered, "filt_chk").featureCount() > 0:
            clipped = filtered
    except Exception:
        pass

    return clipped


# ---------------- fallback + merge ---------------- #

def _voronoi_clip_fallback(poly_id, context, feedback):
    """Attempt a QGIS-native Voronoi-edge network when GRASS skeletonization fails.
    
    This is a fallback geometry, not necessarily equivalent to GRASS output."""
    poly_path = freeze_to_shp(poly_id, context, feedback, tag="freeze_poly_for_fallback")

    verts = _temp_path_tracked("verts_", ".shp")
    runp("native:extractvertices", {"INPUT": poly_path, "OUTPUT": verts},
         context, feedback, "verts_to_shp")

    if as_layer(verts, "verts_chk").featureCount() < 2:
        raise QgsProcessingException("Fallback: less than 2 vertices for Voronoi.")

    ext = as_layer(poly_path, "poly_for_margin").extent()
    margin = max(ext.width(), ext.height()) * 0.5 or 1.0

    vor_alg = "native:voronoipolygons" if QgsApplication.processingRegistry().algorithmById(
        "native:voronoipolygons") else "qgis:voronoipolygons"

    vor = _temp_path_tracked("vor_", ".shp")
    runp(vor_alg, {"INPUT": verts, "BUFFER": float(margin), "OUTPUT": vor},
         context, feedback, "voronoi_to_shp")

    clipv = _temp_path_tracked("clipv_", ".shp")
    runp("native:clip",
         {"INPUT": vor, "OVERLAY": poly_path, "OUTPUT": clipv},
         context, feedback, "clip_voronoi_to_shp")

    lines = _temp_path_tracked("voro_lines_", ".shp")
    runp("native:polygonstolines",
         {"INPUT": clipv, "KEEP_FIELDS": False, "OUTPUT": lines},
         context, feedback, "voro2lines_to_shp")

    interior = _temp_path_tracked("interior_", ".shp")
    runp("native:extractbylocation",
         {"INPUT": lines, "PREDICATE": [7], "INTERSECT": poly_path, "OUTPUT": interior},
         context, feedback, "interior_to_shp")

    return interior


def _to_single_centerline(line_src, context, feedback, tag="single_centerline"):
    """
    Merge a line network and then keep ONLY the longest singlepart line feature.
    This avoids returning polygon-ish fragments / dense webs as the "centreline".
    """
    # 1) Try to merge/linemerge/unaryunion into multipart lines
    merged = _temp_path_tracked(f"{tag}_merged_", ".shp")
    try:
        runp("native:mergelines", {"INPUT": line_src, "OUTPUT": merged},
             context, feedback, f"{tag}_mergelines")
    except Exception:
        try:
            merged = _temp_path_tracked(f"{tag}_linemerge_", ".shp")
            runp("native:linemerge", {"INPUT": line_src, "OUTPUT": merged},
                 context, feedback, f"{tag}_linemerge")
        except Exception:
            merged = _temp_path_tracked(f"{tag}_uunion_", ".shp")
            runp("native:unaryunion", {"INPUT": line_src, "OUTPUT": merged},
                 context, feedback, f"{tag}_unaryunion")

    # 2) Explode to singleparts
    sps = _temp_path_tracked(f"{tag}_sps_", ".shp")
    runp("native:multiparttosingleparts", {"INPUT": merged, "OUTPUT": sps},
         context, feedback, f"{tag}_singleparts")

    # 3) Add length + keep the longest
    sps_len = add_length_field(sps, context, feedback)

    longest = _temp_path_tracked(f"{tag}_longest_", ".shp")
    expr = "\"length\" = aggregate(@layer, 'max', \"length\")"
    runp("native:extractbyexpression",
         {"INPUT": sps_len, "EXPRESSION": expr, "OUTPUT": longest},
         context, feedback, f"{tag}_keep_longest")

    return longest


def _has_area(poly_path, context, feedback):
    """Check whether at least one polygon has non-negligible positive area."""
    try:
        lyr = as_layer(poly_path, "area_chk")
        if lyr.featureCount() == 0:
            return False
        tmp = runp("native:extractbyexpression",
                   {"INPUT": lyr, "EXPRESSION": "$area > 0.0000001",
                    "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
                   context, feedback, "has_area_filter")
        return as_layer(tmp, "area_chk2").featureCount() > 0
    except Exception:
        return False


def _centerline_one(poly_id, context, feedback, grass_opts,
                    already_cleaned=False, name_hint=None):
    """Prepare one polygon and derive a representative line using GRASS or fallback.
    
    Any failure is wrapped with the input name for easier diagnosis."""
    try:
        opts = dict(grass_opts or {})

        # these are YOUR pipeline options, not GRASS opts
        opts.pop("pre_skel_simplify", None)
        opts.pop("pre_skel_tol", None)

        if already_cleaned:
            clean_path = (poly_id if isinstance(poly_id, str)
                          else freeze_to_shp(poly_id, context, feedback, tag="freeze_already_clean"))
        else:
            clean_path = _clean_channel(poly_id, context, feedback)

        try:
            center = _grass_skeleton_from_polygon(clean_path, context, feedback, **opts)
        except Exception as e:
            nh = name_hint or (os.path.basename(clean_path)
                               if isinstance(clean_path, str) else str(poly_id))
            if feedback:
                feedback.reportError(
                    f"GRASS skeleton failed on input: {nh}\n{e}\nFalling back to Voronoi clip."
                )
            center = _voronoi_clip_fallback(clean_path, context, feedback)

        if as_layer(center, "center_chk").featureCount() == 0:
            raise QgsProcessingException("Centerline is empty after skeleton/fallback.")

        center = _to_single_centerline(center, context, feedback,
                                       tag=f"single_{os.path.basename(clean_path)}")
        return center

    except Exception as e:
        raise QgsProcessingException(
            f"Failed on input layer: {name_hint or poly_id}\nError: {e}"
        )


# ---------------- Algorithm ---------------- #

class Modul1CenterlineGrassSHP_QC(QgsProcessingAlgorithm):
    OUTPUTS = "OUTPUTS"

    def name(self):
        """Return stable QGIS Processing algorithm identifier (retained from v14)."""
        return "module1_centerline_channel_outlinesv14"

    def displayName(self):
        """Return the user-facing algorithm name shown in QGIS Processing."""
        return "Module_1_Centerline v14 (using GRASS v8.4)"

    def group(self):
        """Return the human-readable QGIS Processing toolbox group."""
        return "SCS Toolbox"

    def groupId(self):
        """Return the stable machine-readable toolbox group identifier."""
        return "scs_toolbox"

    def shortHelpString(self):
        """Describe inputs, modes, and outputs in the QGIS Processing dialog."""
        return (
            "Generates channel centerlines from channel polygons.\n"
            "- Inputs reprojected to TARGET_CRS only if needed\n"
            "- Per-year centerlines: centro_YYYY0101.gpkg\n"
            "- Optional MERGE_OUTPUT: centerlines_merged.gpkg\n"
            "- UNION_MODE: Channel Zone centerline (SegCenterline) and union layers\n"
            "- YEAR_FIELD may be int, date, or string with 4-digit year"
        )

    def createInstance(self):
        """Create a new Processing algorithm instance for QGIS registration."""
        return Modul1CenterlineGrassSHP_QC()

    def initAlgorithm(self, _config=None):
        """Register all QGIS Processing parameters and output definitions.
        
        Optional legacy GRASS controls remain exposed even when unused by CLI."""
        self.addParameter(QgsProcessingParameterFolderDestination(
            "OUTPUT_FOLDER", tr("Output folder")))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            "INPUT_CHANNELS", tr("Input channel polygons (one or more)"),
            layerType=QgsProcessing.TypeVectorPolygon))

        self.addParameter(QgsProcessingParameterString(
            "YEAR_FIELD", tr("Year/date field name")))

        self.addParameter(QgsProcessingParameterCrs(
            "TARGET_CRS", tr("Target CRS for processing"),
            defaultValue=QgsProject.instance().crs().authid()))

        self.addParameter(QgsProcessingParameterBoolean(
            "UNION_MODE",
            tr("Channel Zone Centreline (union of all inputs) instead of per-year"),
            defaultValue=False))

        self.addParameter(QgsProcessingParameterBoolean(
            "MERGE_OUTPUT",
            tr("Also merge all per-year centrelines to centerlines_merged.gpkg"),
            defaultValue=False))

        self.addParameter(QgsProcessingParameterBoolean(
            "SAVE_UNION_NOHOLES",
            tr("Save union_channel_noholes and union_channel_byYear_noholes (in UNION_MODE)"),
            defaultValue=False))
        
        # --- Pre-skeleton simplification (UNION_MODE heavy polygons) ---
        self.addParameter(QgsProcessingParameterBoolean(
            "PRE_SKEL_SIMPLIFY",
            tr("Pre-skeleton simplify union polygon (recommended for large rivers)"),
            defaultValue=True))

        self.addParameter(QgsProcessingParameterNumber(
            "PRE_SKEL_TOL",
            tr("Pre-skeleton simplify tolerance (map units; metres in EPSG:32720)"),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0,   # Suggested default for Mamore in UTM
            optional=False))


        self.addParameter(QgsProcessingParameterNumber(
            "GRASS_FACTOR",
            tr("GRASS v.voronoi smoothness (higher = smoother/less branches; typical 0.25–1.0)"),
            type=QgsProcessingParameterNumber.Double, defaultValue=None, optional=True))

        self.addParameter(QgsProcessingParameterNumber(
            "GRASS_MAX_DANGLE",
            tr("Max dangle length to remove (meters): applied in v.clean rmdangle (e.g. 150–600; Mamore 250–400)"),
            type=QgsProcessingParameterNumber.Double, defaultValue=None, optional=True))


        self.addParameter(QgsProcessingParameterBoolean(
            "FLAG_SKELETON", tr("Extract skeletons (-s)"), defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            "FLAG_GRAPH", tr("Output as graph (-g)"), defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean(
            "FLAG_NOATTR", tr("Do not create attribute table (-t)"), defaultValue=True))

        self.addParameter(QgsProcessingParameterExtent(
            "GRASS_REGION", tr("GRASS region extent (optional)"), optional=True))

        self.addParameter(QgsProcessingParameterNumber(
            "VIN_SNAP", tr("v.in.ogr snap tolerance (optional)"),
            type=QgsProcessingParameterNumber.Double, defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterNumber(
            "VIN_MINAREA", tr("v.in.ogr min area (optional)"),
            type=QgsProcessingParameterNumber.Double, defaultValue=None, optional=True))

        self.addOutput(QgsProcessingOutputString(self.OUTPUTS, tr("Output path(s)")))

    def _get_optional_double_parameter(self, parameters, name, context):
        """Distinguish a missing optional numeric parameter from a valid number."""
        try:
            val = self.parameterAsDouble(parameters, name, context)
            raw = parameters.get(name, None)
            if raw in (None, "", "None"):
                return None
            return float(val)
        except Exception:
            return None

    def processAlgorithm(self, parameters, context, feedback):
        """Run the complete reference-frame workflow in union or per-year mode.
        
        Validate input polygons, normalise CRS, build centreline geometry,
        write requested outputs, and clean up intermediate workspaces."""
        global _TRACKED_DIRS
        _TRACKED_DIRS.clear()
        output_paths = []

        

        try:
            out_dir = self.parameterAsString(parameters, "OUTPUT_FOLDER", context)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir, exist_ok=True)

            layers = self.parameterAsLayerList(parameters, "INPUT_CHANNELS", context) or []
            polys = [
                lyr for lyr in layers
                if isinstance(lyr, QgsVectorLayer)
                and QgsWkbTypes.geometryType(lyr.wkbType()) == QgsWkbTypes.PolygonGeometry
            ]
            if not polys:
                raise QgsProcessingException("No valid polygon vector layers were provided.")

            year_field = self.parameterAsString(parameters, "YEAR_FIELD", context)
            if not year_field:
                raise QgsProcessingException("The Year/date field name cannot be empty.")

            for lyr in polys:
                if lyr.featureCount() == 0:
                    raise QgsProcessingException(f"Input layer is empty: {lyr.name()}")

            target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)

            # Optional explicit GRASS region from dialog (kept for compatibility; ignored by _grass_skeleton_from_polygon)
            region = None
            ext = self.parameterAsExtent(parameters, "GRASS_REGION", context)
            if ext and not ext.isEmpty():
                region = f"{ext.xMinimum()},{ext.xMaximum()},{ext.yMinimum()},{ext.yMaximum()}"

            # --- read UI params first ---
            pre_skel_simplify = bool(self.parameterAsBoolean(parameters, "PRE_SKEL_SIMPLIFY", context))

            try:
                pre_skel_tol = self.parameterAsDouble(parameters, "PRE_SKEL_TOL", context)
            except Exception:
                pre_skel_tol = None

            # treat 0/None/blank as "off" or "use default"
            if pre_skel_tol is None or pre_skel_tol <= 0:
                pre_skel_tol = 0.5  # suggested default for EPSG:32720 (meters)

            # --- then build grass_opts dict ---
            grass_opts = dict(
                factor=self._get_optional_double_parameter(parameters, "GRASS_FACTOR", context),
                max_dangle=self._get_optional_double_parameter(parameters, "GRASS_MAX_DANGLE", context),
                flag_skeleton=bool(self.parameterAsBoolean(parameters, "FLAG_SKELETON", context)),
                flag_graph=bool(self.parameterAsBoolean(parameters, "FLAG_GRAPH", context)),
                flag_noattr=bool(self.parameterAsBoolean(parameters, "FLAG_NOATTR", context)),
                region=region,
                vin_snap=self._get_optional_double_parameter(parameters, "VIN_SNAP", context),
                vin_minarea=self._get_optional_double_parameter(parameters, "VIN_MINAREA", context),

                # NEW: pre-skeleton prep controls (these are *your* pipeline options, not GRASS)
                pre_skel_simplify=pre_skel_simplify,
                pre_skel_tol=pre_skel_tol,
            )


            union_mode = self.parameterAsBoolean(parameters, "UNION_MODE", context)
            merge_output = self.parameterAsBoolean(parameters, "MERGE_OUTPUT", context)
            save_noholes = self.parameterAsBoolean(parameters, "SAVE_UNION_NOHOLES", context)

            produced = []
            centerlines_for_merge = []

            # 2) Reproject/freeze to TARGET_CRS
            reproj_paths = []
            for lyr in polys:
                rp = _reproject_to_target(lyr, target_crs, context, feedback)
                reproj_paths.append((lyr.name(), rp))

            # collect all years
            all_years = set()
            for _, path in reproj_paths:
                for y in _safe_years(path, year_field):
                    all_years.add(y)
            all_years = sorted(all_years)

            # This is a retrospective footprint-based reference frame, not a channel at one date.
            # ---------------- UNION MODE ----------------
            if union_mode:
                feedback.pushInfo("-> UNION MODE")
                feedback.pushInfo(f"[DEBUG] UNION_MODE={union_mode}  MERGE_OUTPUT={merge_output}  SAVE_UNION_NOHOLES={save_noholes}")


                merged_raw = _temp_path_tracked("merged_raw_", ".shp")
                runp("native:mergevectorlayers",
                     {"LAYERS": [p for _, p in reproj_paths], "OUTPUT": merged_raw},
                     context, feedback, "merge_raw")

                merged_raw_fixed = _temp_path_tracked("merged_raw_fixed_", ".shp")
                runp("native:fixgeometries",
                     {"INPUT": merged_raw, "OUTPUT": merged_raw_fixed},
                     context, feedback, "fix_raw_for_by_year")

                precleaned = []
                for lname, p in reproj_paths:
                    if feedback.isCanceled():
                        break
                    try:
                        pc = _clean_channel(p, context, feedback)
                        precleaned.append(pc)
                    except Exception as e_pc:
                        feedback.reportError(f"Pre-clean failed for {lname}: {e_pc}")

                if not precleaned and not feedback.isCanceled():
                    raise QgsProcessingException("All inputs failed pre-cleaning.")

                merged_clean = _temp_path_tracked("merged_clean_", ".shp")
                runp("native:mergevectorlayers",
                     {"LAYERS": precleaned, "OUTPUT": merged_clean},
                     context, feedback, "merge_clean")

                real_year = _resolve_field_name(merged_raw_fixed, year_field) or year_field
                union_by_year = _temp_path_tracked("union_by_year_", ".shp")
                runp("native:dissolve",
                     {"INPUT": merged_raw_fixed, "FIELD": [real_year],
                      "SEPARATE_DISJOINT": False, "OUTPUT": union_by_year},
                     context, feedback, "dissolve_by_YEAR")

                union_gpkg = os.path.join(out_dir, "union_channel.gpkg")
                save_gpkg_clean(union_by_year, union_gpkg, context, feedback,
                                layer_name="union_channel")
                produced.append(union_gpkg)

                if save_noholes:
                    try:
                        union_by_year_nh = _temp_path_tracked("union_by_year_noholes_", ".shp")
                        runp("native:deleteholes",
                             {"INPUT": union_by_year, "MIN_AREA": 0.0, "OUTPUT": union_by_year_nh},
                             context, feedback, "delholes_by_year")
                        out_nh_by = os.path.join(out_dir, "union_channel_byYear_noholes.gpkg")
                        save_gpkg_clean(union_by_year_nh, out_nh_by, context, feedback,
                                        layer_name="union_channel_byYear_noholes")
                        produced.append(out_nh_by)
                    except Exception as e_nh:
                        feedback.reportError(f"Failed to write union_channel_byYear_noholes: {e_nh}")

                # The dissolved all-years polygon supplies the union reference geometry.
                # all-years noholes surface
                union_diss_all = _temp_path_tracked("union_diss_all_", ".shp")
                runp("native:dissolve",
                     {"INPUT": merged_clean, "FIELD": [],
                      "SEPARATE_DISJOINT": False, "OUTPUT": union_diss_all},
                     context, feedback, "diss_all_years")

                fixed_all = _temp_path_tracked("fixed_all_", ".shp")
                runp("native:fixgeometries", {"INPUT": union_diss_all, "OUTPUT": fixed_all},
                     context, feedback, "fixgeom_all")

                healed_all = _temp_path_tracked("union_healed_buf0_", ".shp")
                runp("native:buffer",
                     {"INPUT": fixed_all, "DISTANCE": 0.0, "SEGMENTS": 8,
                      "END_CAP_STYLE": 0, "JOIN_STYLE": 0, "MITER_LIMIT": 2.0,
                      "DISSOLVE": True, "OUTPUT": healed_all},
                     context, feedback, "heal_buf0_all")

                # Build a robust "polygon for skeleton" (prefer noholes, else healed)
                noholes_all = None
                try:
                    noholes_all = _temp_path_tracked("union_all_noholes_", ".shp")
                    runp("native:deleteholes",
                        {"INPUT": healed_all, "MIN_AREA": 0.0, "OUTPUT": noholes_all},
                        context, feedback, "delholes_all")

                    union_geom_for_skel = noholes_all if _has_area(noholes_all, context, feedback) else healed_all

                except Exception as e:
                    feedback.reportError(f"[UNION] deleteholes failed; using healed polygon: {e}")
                    union_geom_for_skel = healed_all
                    noholes_all = None  # ensure we don't try to save it

                # Optional: write union_channel_noholes.gpkg (only if we actually produced noholes_all)
                if save_noholes and noholes_all and os.path.exists(noholes_all):
                    try:
                        out_nh = os.path.join(out_dir, "union_channel_noholes.gpkg")
                        save_gpkg_clean(noholes_all, out_nh, context, feedback,
                                        layer_name="union_channel_noholes")
                        produced.append(out_nh)
                    except Exception as e_nh2:
                        feedback.reportError(f"Failed to write union_channel_noholes: {e_nh2}")

                # start pre-skeleton pipeline from this polygon
                use_for_skel = union_geom_for_skel



                # 1) Optional simplify to reduce vertex count (topology-preserving), then fix geometries
                #    Controlled by UI: PRE_SKEL_SIMPLIFY (bool) + PRE_SKEL_TOL (double, meters in EPSG:32720)
                try:
                    do_simplify = bool(grass_opts.get("pre_skel_simplify", True))

                    # Suggested default for Mamoré in UTM meters: 0.5–2.0 m
                    tol = grass_opts.get("pre_skel_tol", 0.5)
                    try:
                        tol = float(tol)
                    except Exception:
                        tol = 0.5
                    if tol <= 0:
                        tol = 0.5

                    if do_simplify:
                        simp = _temp_path_tracked("union_simpl_", ".shp")
                        runp("native:simplifygeometries",
                             {"INPUT": use_for_skel,
                              "METHOD": 0,          # Distance
                              "TOLERANCE": tol,
                              "OUTPUT": simp},
                             context, feedback, "pre_skel_simplify")

                        if as_layer(simp, "simp_chk").featureCount() > 0:
                            use_for_skel = simp

                    # Always do a final fix before GRASS (even if simplify disabled)
                    fixed2 = _temp_path_tracked("union_simpl_fix_", ".shp")
                    runp("native:fixgeometries",
                         {"INPUT": use_for_skel, "OUTPUT": fixed2},
                         context, feedback, "pre_skel_fix2")

                    if as_layer(fixed2, "fix2_chk").featureCount() > 0:
                        use_for_skel = fixed2

                except Exception as e:
                    feedback.reportError(f"[pre_skel] simplify/fix skipped: {e}")

                

                # The representative axis is computed from the processed union footprint.
                # ---- NOW ACTUALLY BUILD THE UNION CENTERLINE (SegCenterline) ----
                try:
                    fc = as_layer(use_for_skel, "union_for_skel").featureCount()
                    feedback.pushInfo(f"[UNION] Polygon for skeleton: {fc} feature(s)")
                except Exception:
                    pass

                union_center = _centerline_one(
                    use_for_skel, context, feedback, grass_opts,
                    already_cleaned=True, name_hint="UNION_MODE_polygon"
                )

                # Tag/measure: UNION_MODE does not have a real year; use earliest year if available
                tag_year = all_years[0] if all_years else date.today().year
                tag_date = f"{tag_year}-01-01"

                union_center_final = _tag_and_measure(union_center, tag_date, context, feedback)
                union_center_final = add_year_field(union_center_final, tag_year, context, feedback)

                seg_path = os.path.join(out_dir, "SegCenterline.gpkg")
                save_gpkg_clean(union_center_final, seg_path, context, feedback,
                                layer_name="SegCenterline", force_multiline=True)
                produced.append(seg_path)
                feedback.pushInfo(f"Wrote UNION_MODE centerline: {seg_path}")

                # OPTIONAL: if you also want the union centerline included in "MERGE_OUTPUT"
                # centerlines_for_merge.append(seg_path + "|layername=SegCenterline")

                # CRITICAL: Stop here, do NOT fall through into per-year processing
                output_paths = produced
                _cleanup_tmp_dirs(feedback)
                return {self.OUTPUTS: ";".join(output_paths)}

            # Year groups are independently processed; 1 January is a nominal date.
            # ---------------- PER-YEAR MODE ----------------
            feedback.pushInfo("-> PER-YEAR MODE")

            if not all_years:
                feedback.pushInfo(
                    f"No valid years found in field '{year_field}'. Continuing with a single merged output."
                )
                merged_polys = _temp_path_tracked("merged_all_", ".shp")
                runp("native:mergevectorlayers",
                     {"LAYERS": [p for _, p in reproj_paths], "OUTPUT": merged_polys},
                     context, feedback, "merge_all_no_year")

                center_path = _centerline_one(merged_polys, context, feedback, grass_opts,
                                              already_cleaned=False, name_hint="Merged_Fallback")

                today = date.today()
                date_str = today.isoformat()
                center_final = _tag_and_measure(center_path, date_str, context, feedback)
                center_final = add_year_field(center_final, today.year, context, feedback)

                out_name = f"centro_{today.year}0101.gpkg"
                out_layer = f"centro_{today.year}"
                out_path = os.path.join(out_dir, out_name)
                save_gpkg_clean(center_final, out_path, context, feedback,
                                layer_name=out_layer, force_multiline=True)

                produced.append(out_path)
                centerlines_for_merge.append(out_path + "|layername=" + out_layer)

            else:
                for y in all_years:
                    if feedback.isCanceled():
                        break
                    feedback.pushInfo(f"Processing year: {y}")

                    year_subs = []
                    for lname, reproj_path in reproj_paths:
                        sub_path = _subset_by_year(reproj_path, year_field, y, context, feedback)
                        if sub_path:
                            year_subs.append(sub_path)

                    if not year_subs:
                        feedback.pushInfo(f"Year {y}: no polygons across inputs. Skipping.")
                        continue

                    merged_year = _temp_path_tracked(f"merged_{y}_", ".shp")
                    runp("native:mergevectorlayers",
                         {"LAYERS": year_subs, "OUTPUT": merged_year},
                         context, feedback, f"merge_year_{y}")

                    center_path = _centerline_one(merged_year, context, feedback, grass_opts,
                                                  already_cleaned=False, name_hint=f"year_{y}_poly")

                    date_str = f"{y}-01-01"
                    center_final = _tag_and_measure(center_path, date_str, context, feedback)
                    center_final = add_year_field(center_final, y, context, feedback)

                    out_name = f"centro_{y}0101.gpkg"
                    out_path = os.path.join(out_dir, out_name)
                    layer_name = f"centro_{y}"
                    save_gpkg_clean(center_final, out_path, context, feedback,
                                    layer_name=layer_name, force_multiline=True)

                    produced.append(out_path)
                    centerlines_for_merge.append(out_path + "|layername=" + layer_name)
                    feedback.pushInfo(f"Wrote per-year centerline: {out_name}")

            if merge_output and centerlines_for_merge and not feedback.isCanceled():
                merge_out = os.path.join(out_dir, "centerlines_merged.gpkg")
                runp("native:mergevectorlayers",
                     {"LAYERS": centerlines_for_merge, "OUTPUT": merge_out},
                     context, feedback, "merge_all_finals")
                produced.append(merge_out)
                feedback.pushInfo(f"Wrote merged output: {merge_out}")

            output_paths = produced

        finally:
            _cleanup_tmp_dirs(feedback)

        return {self.OUTPUTS: ";".join(output_paths)}
