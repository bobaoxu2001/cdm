from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(*parts: str | Path) -> Path:
    return PROJECT_ROOT.joinpath(*map(Path, parts))


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def runtime_config() -> dict[str, Any]:
    return load_yaml(project_path("config", "runtime.yaml"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_parent(path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def sha256_file(path: str | Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(block_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_file_type(path: str | Path) -> str:
    name = Path(path).name.lower()
    if name.endswith(".csv") or name.endswith(".csv.gz"):
        return "csv"
    if name.endswith(".tsv") or name.endswith(".tsv.gz"):
        return "tsv"
    if name.endswith(".json"):
        return "json"
    if name.endswith(".parquet"):
        return "parquet"
    if "series_matrix" in name:
        return "geo_series_matrix"
    return "other"


def read_tabular_sample(path: str | Path, nrows: int | None = None) -> pd.DataFrame:
    path = Path(path)
    file_type = infer_file_type(path)
    if file_type == "parquet":
        return pd.read_parquet(path)
    if file_type == "tsv":
        return pd.read_csv(path, sep="\t", nrows=nrows)
    if file_type == "csv":
        return pd.read_csv(path, nrows=nrows)
    raise ValueError(f"Unsupported tabular file type for {path}")


def iter_tabular_chunks(path: str | Path, chunksize: int, nrows: int | None = None) -> Iterable[pd.DataFrame]:
    path = Path(path)
    file_type = infer_file_type(path)
    kwargs: dict[str, Any] = {"chunksize": chunksize}
    if nrows:
        kwargs["nrows"] = nrows
    if file_type == "csv":
        yield from pd.read_csv(path, **kwargs)
    elif file_type == "tsv":
        yield from pd.read_csv(path, sep="\t", **kwargs)
    elif file_type == "parquet":
        frame = pd.read_parquet(path)
        if nrows:
            frame = frame.head(nrows)
        for start in range(0, len(frame), chunksize):
            yield frame.iloc[start : start + chunksize]
    else:
        raise ValueError(f"Unsupported chunked file type for {path}")


def parse_geo_series_matrix(path: str | Path, sample_rows: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    metadata: dict[str, list[str]] = {}
    expression_rows: list[list[str]] = []
    in_table = False
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("!Sample_"):
                parts = next(csv.reader([line], delimiter="\t"))
                metadata[parts[0].replace("!Sample_", "")] = parts[1:]
            elif line.startswith("!series_matrix_table_begin"):
                in_table = True
            elif line.startswith("!series_matrix_table_end"):
                break
            elif in_table:
                expression_rows.append(next(csv.reader([line], delimiter="\t")))
                if sample_rows and len(expression_rows) >= sample_rows + 1:
                    break
    sample_ids = metadata.get("geo_accession", [])
    sample_meta = pd.DataFrame({"sample_id": sample_ids})
    for key, values in metadata.items():
        if len(values) == len(sample_meta):
            sample_meta[key] = values
    if expression_rows:
        header = expression_rows[0]
        expr = pd.DataFrame(expression_rows[1:], columns=header)
    else:
        expr = pd.DataFrame()
    return sample_meta, expr


def parse_geo_series_metadata(path: str | Path) -> dict[str, str]:
    """Read study-level !Series_ header lines from a GEO Series Matrix file."""
    metadata: dict[str, str] = {}
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("!series_matrix_table_begin"):
                break
            if line.startswith("!Series_"):
                parts = next(csv.reader([line.rstrip("\n")], delimiter="\t"))
                key = parts[0].replace("!Series_", "")
                metadata.setdefault(key, parts[1] if len(parts) > 1 else "")
    return metadata


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out = ensure_parent(path)
    frame = pd.DataFrame(rows)
    frame.to_csv(out, index=False)


def stable_id(*parts: Any) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
