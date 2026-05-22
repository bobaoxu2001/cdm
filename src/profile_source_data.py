from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.logging_config import configure_logging
from src.utils import infer_file_type, iter_tabular_chunks, parse_geo_series_matrix, project_path, runtime_config, write_csv


LOGGER = configure_logging(__name__)


def profile_frame(frame: pd.DataFrame, source_file: str, source_system: str) -> tuple[dict, list[dict]]:
    summary = {
        "source_file": source_file,
        "source_system": source_system,
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "candidate_identifiers": "; ".join([c for c in frame.columns if "id" in c.lower() or c.lower().endswith("accession")][:10]),
        "candidate_foreign_keys": "; ".join([c for c in frame.columns if c.lower().endswith("_id")][:10]),
        "source_quality_warnings": "",
    }
    column_rows: list[dict] = []
    for col in frame.columns:
        series = frame[col]
        numeric = pd.to_numeric(series, errors="coerce")
        top = series.dropna().astype(str).value_counts().head(5)
        missing_pct = float(series.isna().mean()) if len(series) else 0.0
        warnings = []
        if missing_pct > 0.5:
            warnings.append("high_missingness")
        if series.nunique(dropna=True) == len(series) and len(series) > 0:
            warnings.append("possible_identifier")
        column_rows.append(
            {
                "source_file": source_file,
                "source_system": source_system,
                "column_name": col,
                "inferred_dtype": str(series.dtype),
                "missingness_pct": round(missing_pct, 4),
                "distinct_value_count": int(series.nunique(dropna=True)),
                "top_values": "; ".join(f"{idx}:{val}" for idx, val in top.items()),
                "numeric_min": numeric.min() if numeric.notna().any() else "",
                "numeric_max": numeric.max() if numeric.notna().any() else "",
                "numeric_mean": numeric.mean() if numeric.notna().any() else "",
                "approx_cardinality": int(series.nunique(dropna=True)),
                "warnings": "; ".join(warnings),
            }
        )
    return summary, column_rows


def profile_tabular(path: Path, source_system: str) -> tuple[dict, list[dict]]:
    config = runtime_config()
    sample_limit = config.get("sample_rows") if config.get("mode") == "sample" else None
    chunks = []
    for chunk in iter_tabular_chunks(path, chunksize=config.get("chunk_size", 100000), nrows=sample_limit):
        chunks.append(chunk)
        if sample_limit and sum(len(c) for c in chunks) >= sample_limit:
            break
    frame = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    return profile_frame(frame, str(path.relative_to(project_path())), source_system)


def profile_json(path: Path, source_system: str) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    frame = pd.DataFrame([{"json_key": key, "json_value": str(value)} for key, value in data.items()])
    return profile_frame(frame, str(path.relative_to(project_path())), source_system)


def run() -> tuple[list[dict], list[dict]]:
    summary_rows: list[dict] = []
    column_rows: list[dict] = []
    for path in project_path("data", "raw").rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(project_path()))
        if "geo" in rel:
            source = "NCBI GEO"
        elif "cell_painting" in rel:
            source = "Broad Institute Cell Painting Gallery"
        elif "openneuro" in rel:
            source = "OpenNeuro"
        else:
            source = "unknown"
        try:
            if infer_file_type(path) == "geo_series_matrix":
                sample_meta, expr = parse_geo_series_matrix(path, sample_rows=runtime_config().get("sample_rows"))
                for label, frame in [("sample_metadata", sample_meta), ("expression_matrix", expr)]:
                    summary, cols = profile_frame(frame, f"{rel}::{label}", source)
                    summary_rows.append(summary)
                    column_rows.extend(cols)
            elif infer_file_type(path) in {"csv", "tsv", "parquet"}:
                summary, cols = profile_tabular(path, source)
                summary_rows.append(summary)
                column_rows.extend(cols)
            elif infer_file_type(path) == "json":
                summary, cols = profile_json(path, source)
                summary_rows.append(summary)
                column_rows.extend(cols)
        except Exception as exc:
            LOGGER.warning("Profiling failed for %s: %s", path, exc)
            summary_rows.append({"source_file": rel, "source_system": source, "row_count": "", "column_count": "", "source_quality_warnings": str(exc)})
    write_csv(summary_rows, project_path("data", "outputs", "source_profile_summary.csv"))
    write_csv(column_rows, project_path("data", "outputs", "source_column_profile.csv"))
    write_report(summary_rows, column_rows)
    return summary_rows, column_rows


def write_report(summary_rows: list[dict], column_rows: list[dict]) -> None:
    lines = ["# Source Profile Report", "", "Generated from public biomedical research metadata/profile files using sample-safe chunked profiling.", ""]
    for row in summary_rows:
        lines.append(f"## {row.get('source_file')}")
        lines.append(f"- Source system: {row.get('source_system')}")
        lines.append(f"- Rows profiled: {row.get('row_count')}")
        lines.append(f"- Columns profiled: {row.get('column_count')}")
        lines.append(f"- Candidate identifiers: {row.get('candidate_identifiers', '')}")
        if row.get("source_quality_warnings"):
            lines.append(f"- Warnings: {row.get('source_quality_warnings')}")
        lines.append("")
    project_path("data", "outputs", "source_profile_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
