from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import infer_file_type, parse_geo_series_matrix, project_path, read_tabular_sample, runtime_config, write_csv


def infer_dataframe_schema(frame: pd.DataFrame, source_file: str = "") -> list[dict]:
    rows = []
    for column in frame.columns:
        series = frame[column]
        rows.append(
            {
                "source_file": source_file,
                "field_name": column,
                "inferred_dtype": str(series.dtype),
                "nullable": bool(series.isna().any()),
                "missing_pct": float(series.isna().mean()) if len(series) else 0.0,
                "example_values": "; ".join(map(str, series.dropna().astype(str).head(5).tolist())),
            }
        )
    return rows


def infer_file_schema(path: str | Path) -> list[dict]:
    path = Path(path)
    config = runtime_config()
    if infer_file_type(path) == "geo_series_matrix":
        sample_meta, expr = parse_geo_series_matrix(path, sample_rows=config.get("sample_rows"))
        return infer_dataframe_schema(sample_meta, str(path)) + infer_dataframe_schema(expr, str(path))
    if infer_file_type(path) in {"csv", "tsv", "parquet"}:
        return infer_dataframe_schema(read_tabular_sample(path, nrows=config.get("sample_rows")), str(path))
    return []


def run() -> list[dict]:
    rows: list[dict] = []
    for path in project_path("data", "raw").rglob("*"):
        if path.is_file():
            rows.extend(infer_file_schema(path))
    write_csv(rows, project_path("data", "outputs", "schema_inference.csv"))
    return rows


if __name__ == "__main__":
    run()
