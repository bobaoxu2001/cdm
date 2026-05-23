from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.logging_config import configure_logging
from src.utils import infer_file_type, iter_tabular_chunks, parse_geo_series_matrix, project_path, runtime_config, write_csv


LOGGER = configure_logging(__name__)


def profile_frame(frame: pd.DataFrame, source_file: str, source_system: str) -> tuple[dict, list[dict]]:
    total_rows = len(frame)
    col_warnings: list[str] = []
    column_rows: list[dict] = []

    for col in frame.columns:
        series = frame[col]
        numeric = pd.to_numeric(series, errors="coerce")
        top = series.dropna().astype(str).value_counts().head(5)
        null_count = int(series.isna().sum())
        null_rate = round(null_count / total_rows, 4) if total_rows else 0.0
        distinct = int(series.nunique(dropna=True))
        unique_rate = round(distinct / total_rows, 4) if total_rows else 0.0

        # type mismatch: declared object but mostly numeric, or numeric dtype but has non-coercible values
        is_numeric_dtype = str(series.dtype).startswith(("int", "float"))
        non_null_series = series.dropna()
        if is_numeric_dtype:
            type_mismatch_count = 0
        else:
            coerced = pd.to_numeric(non_null_series, errors="coerce")
            numeric_convertible = coerced.notna().sum()
            if len(non_null_series) > 0 and numeric_convertible / len(non_null_series) > 0.8:
                type_mismatch_count = int(coerced.isna().sum())
            else:
                type_mismatch_count = 0

        # outlier count (IQR method): values outside Q1 - 1.5*IQR or Q3 + 1.5*IQR
        outlier_count = 0
        if numeric.notna().sum() >= 4:
            q1 = float(numeric.quantile(0.25))
            q3 = float(numeric.quantile(0.75))
            iqr = q3 - q1
            if iqr > 0:
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outlier_count = int(((numeric < lower) | (numeric > upper)).sum())

        warnings = []
        if null_rate > 0.5:
            warnings.append("high_missingness")
            col_warnings.append(f"{col}:high_missingness")
        if unique_rate == 1.0 and total_rows > 1:
            warnings.append("possible_identifier")
        if type_mismatch_count > 0:
            warnings.append("type_mismatch")
            col_warnings.append(f"{col}:type_mismatch")
        if outlier_count > 0 and numeric.notna().any():
            warnings.append(f"outliers:{outlier_count}")

        column_rows.append(
            {
                "source_file": source_file,
                "source_system": source_system,
                "column_name": col,
                "inferred_dtype": str(series.dtype),
                "null_count": null_count,
                "null_rate": null_rate,
                "distinct_value_count": distinct,
                "unique_rate": unique_rate,
                "type_mismatch_count": type_mismatch_count,
                "outlier_count": outlier_count,
                "top_values": "; ".join(f"{idx}:{val}" for idx, val in top.items()),
                "numeric_min": round(float(numeric.min()), 4) if numeric.notna().any() else "",
                "numeric_max": round(float(numeric.max()), 4) if numeric.notna().any() else "",
                "numeric_mean": round(float(numeric.mean()), 4) if numeric.notna().any() else "",
                "numeric_std": round(float(numeric.std()), 4) if numeric.notna().sum() >= 2 else "",
                "warnings": "; ".join(warnings),
            }
        )

    summary = {
        "source_file": source_file,
        "source_system": source_system,
        "row_count": total_rows,
        "column_count": len(frame.columns),
        "candidate_identifiers": "; ".join([c for c in frame.columns if "id" in c.lower() or c.lower().endswith("accession")][:10]),
        "candidate_foreign_keys": "; ".join([c for c in frame.columns if c.lower().endswith("_id")][:10]),
        "columns_with_warnings": len(col_warnings),
        "source_quality_warnings": "; ".join(col_warnings[:10]),
    }
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
