# -*- coding: utf-8 -*-
# FRAF PAPER 2 — SOURCE ARCHIVE / MODULE 08P: PREDICTION EXTRACTION
# Repository file: FRAF_P2_08P_PredictionExtraction.py
# Original implementation: FRAF_Module5a_Prediction_Extraction.py (Module 5a).
# Purpose: reduce large row-level R prediction archives to an economical,
# traceable collection of fields for subsequent mapping and verification.
#
# POSITION IN WORKFLOW
# - Upstream: R transition-model prediction archives, which have already been
#   calculated, evaluated or forecast in the Cox/prediction workflow.
# - Here: select matching archive files, retain selected columns, attach a source
#   filename, and concatenate records in one compact output.
# - Downstream: tools that join predictions back to fixed-place geometries and
#   compare ranked susceptibility/observed transition footprints.
# - This extraction step does NOT refit Cox models, create risk sets, compute new
#   probabilities, or perform independent forecast validation.
#
# INPUT / OUTPUT CONTRACT
# - INPUT_FOLDER: one folder (top-level only; no recursive discovery).
# - FILE_PATTERN: fnmatch filename glob, default '*prediction_archive*'.
# - Sources accepted: .csv, .csv.gz and .parquet; filenames containing 'compact'
#   are deliberately excluded to avoid re-ingesting earlier compact archives.
# - KEEP_FIELDS: semicolon/comma-separated fields, in caller-specified order.
# - OUTPUT_FOLDER receives a gzip-compressed CSV, a per-file CSV manifest and,
#   when pyarrow support is enabled, an optional zstd-compressed Parquet copy.
# - The original QGIS Processing algorithm name and its interface remain intact;
#   this repository filename is an archive alias, not a change in registration.
#
# SCIENTIFIC / DATA-PROVENANCE BOUNDARIES
# - 'source_file' records the original basename for each retained row; it is
#   provenance metadata, not a cryptographic checksum or immutable run ID.
# - PLACE_ID/BLOCK_ID fill one another only if one is absent/empty. This is not
#   a spatial join and does not establish identifier equivalence independently.
# - Rows are copied without aggregation, deduplication, statistical estimation,
#   numeric conversion, model-selection checks or population harmonisation.
# - Field selection is literal: absent source columns become empty values, not
#   warnings or errors; users must ensure source schema and forecast provenance.
# - The output schema is a *compact extract*, not an authoritative substitute
#   for the underlying model outputs or independent verification artifacts.
#
# Documentation-only release: original executable behaviour is unmodified.
# QGIS runtime output should be verified against archived source data. 
"""FRAF Module 5a — Prediction Extraction and Compact Archive.

QGIS 3.40+ Processing algorithm. Reads one or more R prediction archives from
an output folder, retains a compact set of mapping/validation fields, and writes
one compressed CSV archive plus a manifest. Parquet is written when pyarrow is
available in the QGIS Python environment.
"""

from __future__ import annotations

# Standard-library readers/writers support CSV and gzip without loading the
# entire prediction table in memory; the optional Parquet branch uses pyarrow.
# Existing imports are retained unchanged to preserve the source verbatim.
import csv
import fnmatch
import gzip
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

# QGIS Processing supplies the parameter UI, feedback channel and output paths.
# The script uses a file-oriented algorithm rather than a vector-layer output.
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
)


# Registration class is retained under its original name for QGIS provider
# compatibility. The file rename does not alter the Processing algorithm ID.
class FRAFModule5aPredictionExtraction(QgsProcessingAlgorithm):
    # Stable Processing parameter/output identifiers; keep these unchanged when
    # migrating the source into the Paper 2 archive.
    INPUT_FOLDER = "INPUT_FOLDER"
    FILE_PATTERN = "FILE_PATTERN"
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    KEEP_FIELDS = "KEEP_FIELDS"
    WRITE_PARQUET = "WRITE_PARQUET"
    OUTPUT_ARCHIVE = "OUTPUT_ARCHIVE"
    OUTPUT_MANIFEST = "OUTPUT_MANIFEST"
    OUTPUT_PARQUET = "OUTPUT_PARQUET"

    # Default projection of the R archive. These columns cover forecast origin,
    # transition/model context, fixed-place identity, interval timing, observed
    # events, predicted values and area support. All are copied as supplied.
    # The list is configurable, and additional provenance columns may be needed
    # when distinct analysis runs share filenames or forecast labels.
    DEFAULT_FIELDS = (
        "reach;model;transition;model_scope;spatial_framework;forecast_label;"
        "origin_rank;PLACE_ID;BLOCK_ID;interval_start_label;interval_end_label;"
        "tstart_yr;tstop_yr;interval_duration_yr;starting_state;risk_set;"
        "model_status;observed_event;linear_predictor;relative_hazard;"
        "predicted_probability;risk_percentile;risk_class;prediction_residual;"
        "cell_area_m2"
    )

    # The algorithm ID is still 'fraf_module5a_prediction_extraction'.
    def name(self) -> str:
        return "fraf_module5a_prediction_extraction"

    # UI label is intentionally unchanged from the original Module 5a.
    def displayName(self) -> str:
        return "Module 5a — Prediction Extraction and Compact Archive"

    # Processing toolbox grouping; independent from repository ordering.
    def group(self) -> str:
        return "FRAF Floodplain Reassemblage"

    # QGIS requires a stable, machine-readable group identifier.
    def groupId(self) -> str:
        return "fraf_floodplain_reassemblage"

    # User-facing Processing help explains the archive-reduction operation.
    def shortHelpString(self) -> str:
        return (
            "Combines R prediction archives using a streaming reader. The output "
            "keeps only fields needed for mapping, validation and forecast checking. "
            "Use pattern *prediction_archive* to include rolling, full-record and "
            "future Tn+1 archives. Existing compact outputs are ignored."
        )

    # Standard QGIS factory hook: each Processing execution gets a new object.
    def createInstance(self):
        return FRAFModule5aPredictionExtraction()

    # Declare a source folder, filename glob, output folder, field selection,
    # and the optional Parquet-output switch.
    def initAlgorithm(self, config=None):
        # The input is a directory holding previously produced R predictions;
        # it is not a GeoPackage or risk-table layer.
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_FOLDER,
                "Folder containing R prediction outputs",
                behavior=QgsProcessingParameterFile.Folder,
            )
        )
        # A glob is applied to each filename in the selected directory.
        # Typical use keeps rolling-origin, full-record and future archives.
        self.addParameter(
            QgsProcessingParameterString(
                self.FILE_PATTERN,
                "Filename pattern",
                defaultValue="*prediction_archive*",
            )
        )
        # Distinct from source folder to limit inadvertent re-ingestion.
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                "Output folder",
            )
        )
        # Users can add/remove columns without editing Python source.
        # Ordering here determines column ordering in the compact output.
        self.addParameter(
            QgsProcessingParameterString(
                self.KEEP_FIELDS,
                "Fields to retain (semicolon separated)",
                defaultValue=self.DEFAULT_FIELDS,
                multiLine=True,
            )
        )
        # If pyarrow is unavailable, CSV output continues but no Parquet copy
        # is generated. Source Parquet reading also depends on this switch.
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.WRITE_PARQUET,
                "Write Parquet when pyarrow is available",
                defaultValue=True,
            )
        )
        # Advertise file paths, not QGIS map layers or geometric sinks.
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_ARCHIVE, "Compact compressed CSV"))
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_MANIFEST, "Archive manifest"))
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_PARQUET, "Optional Parquet archive"))

    # Accept either commas or semicolons; strip whitespace and retain each
    # field only once, preserving first appearance (including original case).
    @staticmethod
    def _parse_fields(text: str) -> List[str]:
        # De-duplication concerns column *names* only; not archive records.
        fields: List[str] = []
        for token in text.replace(",", ";").split(";"):
            token = token.strip()
            if token and token not in fields:
                fields.append(token)
        return fields

    # Encodings are read with utf-8-sig to tolerate optional UTF-8 BOMs.
    # Plain CSV and gzipped CSV share the same record-reading path.
    @staticmethod
    def _open_text(path: Path):
        if path.name.lower().endswith(".csv.gz"):
            return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
        return path.open("r", encoding="utf-8-sig", newline="")

    # Generator yields source rows one at a time. For ordinary CSV, peak
    # memory does not grow with total archive length.
    @staticmethod
    def _iter_csv(path: Path) -> Iterator[Dict[str, str]]:
        # Python's DictReader uses the first CSV row as the column header.
        with FRAFModule5aPredictionExtraction._open_text(path) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield row

    # Harmonise the two key-column aliases when only one is populated.
    # Existing, nonempty keys are NEVER overwritten or checked for agreement.
    @staticmethod
    def _normalise_row(row: Dict[str, object], source_file: str) -> Dict[str, object]:
        out = dict(row)
        if not out.get("PLACE_ID") and out.get("BLOCK_ID"):
            out["PLACE_ID"] = out.get("BLOCK_ID")
        if not out.get("BLOCK_ID") and out.get("PLACE_ID"):
            out["BLOCK_ID"] = out.get("PLACE_ID")
        # Preserve source basename for row-level audit and source tracing.
        out["source_file"] = source_file
        return out

    # Main QGIS entry point: orchestrate discovery, projection, compact export,
    # optional Parquet generation, and the input-file manifest.
    def processAlgorithm(self, parameters, context, feedback):
        # Resolve QGIS parameters without changing the caller's original settings.
        input_folder = Path(self.parameterAsFile(parameters, self.INPUT_FOLDER, context)).expanduser()
        pattern = self.parameterAsString(parameters, self.FILE_PATTERN, context).strip() or "*prediction_archive*"
        output_folder = Path(self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)).expanduser()
        fields = self._parse_fields(self.parameterAsString(parameters, self.KEEP_FIELDS, context))
        write_parquet = self.parameterAsBool(parameters, self.WRITE_PARQUET, context)

        # A missing input folder is fatal; the output folder is created if needed.
        if not input_folder.is_dir():
            raise QgsProcessingException(f"Input folder does not exist: {input_folder}")
        output_folder.mkdir(parents=True, exist_ok=True)

        # Discovery is non-recursive and sorted for repeatable file ordering.
        # Matching depends on fnmatch's platform semantics and user-selected glob.
        candidates = []
        for p in sorted(input_folder.iterdir()):
            low = p.name.lower()
            if p.is_file() and fnmatch.fnmatch(p.name, pattern) and (
                low.endswith(".csv") or low.endswith(".csv.gz") or low.endswith(".parquet")
            ):
                # Exclude previously compacted outputs even if their names
                # otherwise satisfy the user-supplied search pattern.
                if "compact" not in low:
                    candidates.append(p)
        # No synthetic empty archive is created when there are no candidates.
        if not candidates:
            raise QgsProcessingException(
                f"No prediction archives matched '{pattern}' in {input_folder}"
            )

        # Fixed output basenames mean repeat executions to the same folder
        # overwrite the earlier compact CSV and manifest.
        archive_path = output_folder / "FRAF_prediction_archive_compact.csv.gz"
        manifest_path = output_folder / "FRAF_prediction_archive_manifest.csv"
        parquet_path = output_folder / "FRAF_prediction_archive_compact.parquet"

        # Always add source_file once; it supports traceability after merging.
        # No attempt is made to infer aliases beyond PLACE_ID / BLOCK_ID.
        output_fields = fields + (["source_file"] if "source_file" not in fields else [])
        row_count = 0
        file_summaries: List[Dict[str, object]] = []

        # CSV remains the primary stream; Parquet is written in batches when
        # pyarrow is importable AND the parameter is enabled.
        # Optional Parquet batching remains independent of the CSV stream.
        parquet_writer = None
        pa = pq = None
        parquet_batch: List[Dict[str, object]] = []
        # Import pyarrow lazily so QGIS environments without it can still use
        # this tool with CSV/CSV.GZ source archives.
        if write_parquet:
            try:
                import pyarrow as pa  # type: ignore
                import pyarrow.parquet as pq  # type: ignore
            except Exception:
                pa = pq = None
                feedback.pushWarning(
                    "pyarrow is not installed in the QGIS Python environment; Parquet was skipped."
                )

        # The gzip stream is opened once, allowing records from successive
        # source files to be appended under a single canonical header.
        with gzip.open(archive_path, "wt", encoding="utf-8", newline="") as out_handle:
            # extrasaction='ignore' drops unrequested source columns; missing
            # requested columns are filled below with empty strings.
            writer = csv.DictWriter(out_handle, fieldnames=output_fields, extrasaction="ignore")
            writer.writeheader()

            # Process each selected source file in stable filename order.
            for file_index, path in enumerate(candidates):
                # Cancellation stops between files only; existing partial
                # output is still written and may appear in the result paths.
                if feedback.isCanceled():
                    break
                feedback.pushInfo(f"Reading {path.name}")
                # Per-file counts and distinct labels are independent of the
                # total record count and are recorded in the manifest.
                local_rows = 0
                local_models = set()
                local_forecasts = set()

                # Parquet INPUT is read with read_table().to_pylist(), which
                # materialises the entire file: CSV input is streaming, Parquet
                # input is NOT. Large Parquet sources may need more RAM.
                # If WRITE_PARQUET is false / pyarrow unavailable, such inputs
                # are skipped even though the file-matching step selects them.
                if path.name.lower().endswith(".parquet"):
                    if pa is None:
                        feedback.pushWarning(f"Skipped {path.name}: pyarrow unavailable.")
                        continue
                    table = pq.read_table(path)
                    row_iter: Iterable[Dict[str, object]] = table.to_pylist()
                else:
                    row_iter = self._iter_csv(path)

                # Each input row becomes exactly one compact output row.
                # Selection uses literal column names, without transforms or
                # type coercion; the CSV output is effectively a text extract.
                for row in row_iter:
                    # Derive the missing ID alias and attach the source basename.
                    normalised = self._normalise_row(row, path.name)
                    # Requested fields missing in a particular source become ''.
                    # This does not establish comparable schemas across files.
                    compact = {name: normalised.get(name, "") for name in output_fields}
                    writer.writerow(compact)
                    row_count += 1
                    local_rows += 1
                    # Inventory model identifiers and forecast labels for the
                    # source-file manifest, not for filtering or validation.
                    if compact.get("model"):
                        local_models.add(str(compact["model"]))
                    if compact.get("forecast_label"):
                        local_forecasts.add(str(compact["forecast_label"]))

                    # Buffer up to 50,000 compact rows before the Parquet write.
                    # The inferred schema comes from the FIRST written batch;
                    # later batches must remain compatible with that schema.
                    if pa is not None:
                        parquet_batch.append(compact)
                        # Append batches using zstd compression. Existing outputs
                        # are recreated rather than updated as immutable partitions.
                        if len(parquet_batch) >= 50000:
                            table = pa.Table.from_pylist(parquet_batch)
                            if parquet_writer is None:
                                parquet_writer = pq.ParquetWriter(
                                    parquet_path, table.schema, compression="zstd"
                                )
                            parquet_writer.write_table(table)
                            parquet_batch.clear()

                # One manifest record per successfully read source file;
                # it records counts and distinct labels, not row-level hashes.
                file_summaries.append(
                    {
                        "source_file": path.name,
                        "rows_read": local_rows,
                        "models": "; ".join(sorted(local_models)),
                        "forecast_labels": "; ".join(sorted(local_forecasts)),
                    }
                )
                # Progress is file-based, not proportional to input row count.
                feedback.setProgress(100.0 * (file_index + 1) / len(candidates))

        # Flush any final, sub-50,000-row Parquet batch and close the writer.
        # Remove stale Parquet output if no Parquet data was written.
        if parquet_writer is not None or parquet_batch:
            if pa is not None and parquet_batch:
                table = pa.Table.from_pylist(parquet_batch)
                if parquet_writer is None:
                    parquet_writer = pq.ParquetWriter(parquet_path, table.schema, compression="zstd")
                parquet_writer.write_table(table)
            if parquet_writer is not None:
                parquet_writer.close()
        elif parquet_path.exists():
            parquet_path.unlink()

        # Emit a compact input manifest for repeatability and simple QA.
        # For a defensible publication archive, preserve source files and an
        # external run manifest/checksum record as well.
        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            manifest_fields = ["source_file", "rows_read", "models", "forecast_labels"]
            writer = csv.DictWriter(handle, fieldnames=manifest_fields)
            writer.writeheader()
            writer.writerows(file_summaries)

        # Return the generated paths through QGIS Processing; output Parquet
        # is deliberately blank when no Parquet file was created.
        feedback.pushInfo(f"Compact archive rows: {row_count:,}")
        return {
            self.OUTPUT_ARCHIVE: str(archive_path),
            self.OUTPUT_MANIFEST: str(manifest_path),
            self.OUTPUT_PARQUET: str(parquet_path) if parquet_path.exists() else "",
        }
