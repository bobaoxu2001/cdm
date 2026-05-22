from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.utils import (
    load_yaml,
    parse_geo_series_matrix,
    parse_geo_series_metadata,
    project_path,
    read_tabular_sample,
    runtime_config,
    stable_id,
    utc_now,
    write_csv,
)


MAPPING_VERSION = "v0.1-spec-oriented"


def lineage(source_system: str, dataset: str, source_file: str, source_record_id: str) -> dict:
    return {
        "source_system": source_system,
        "source_dataset": dataset,
        "source_file": source_file,
        "source_record_id": source_record_id,
        "ingestion_timestamp": utc_now(),
        "mapping_version": MAPPING_VERSION,
    }


def build_data_source_rows() -> list[dict]:
    sources = load_yaml(project_path("config", "data_sources.yaml"))["sources"]
    return [
        {
            "data_source_id": stable_id(key),
            "source_system": cfg["source_name"],
            "source_dataset": cfg["dataset_accession_or_id"],
            "public_url": cfg["public_url"],
            "citation_note": cfg["citation_note"],
        }
        for key, cfg in sources.items()
    ]


def study_id_for(source_key: str) -> str:
    return stable_id(f"{source_key}-study")


def build_study_rows() -> list[dict]:
    rows: list[dict] = []
    geo_path = project_path("data", "raw", "geo", "GSE2034_series_matrix.txt.gz")
    if geo_path.exists():
        series = parse_geo_series_metadata(geo_path)
        sample_meta, _ = parse_geo_series_matrix(geo_path, sample_rows=1)
        organism = ""
        if "organism_ch1" in sample_meta.columns and len(sample_meta):
            organism = str(sample_meta["organism_ch1"].iloc[0])
        rows.append(
            {
                "study_id": study_id_for("geo"),
                "data_source_id": stable_id("geo"),
                "study_title": series.get("title", ""),
                "organism": organism,
                **lineage("NCBI GEO", "GSE2034", str(geo_path), series.get("geo_accession", "GSE2034")),
            }
        )
    openneuro_desc = project_path("data", "raw", "openneuro", "dataset_description.json")
    if openneuro_desc.exists():
        desc = json.loads(openneuro_desc.read_text(encoding="utf-8"))
        rows.append(
            {
                "study_id": study_id_for("openneuro"),
                "data_source_id": stable_id("openneuro"),
                "study_title": desc.get("Name", ""),
                "organism": "Homo sapiens",
                **lineage("OpenNeuro", "ds004504", str(openneuro_desc), "ds004504"),
            }
        )
    cp_path = project_path("data", "raw", "cell_painting", "BR00116991.csv.gz")
    if cp_path.exists():
        rows.append(
            {
                "study_id": study_id_for("cell_painting"),
                "data_source_id": stable_id("cell_painting"),
                "study_title": "JUMP Cell Painting pilot (cpg0000) plate BR00116991",
                "organism": "Homo sapiens (U2OS cell line)",
                **lineage("Broad Institute Cell Painting Gallery", "cpg0000-jump-pilot/source_4/BR00116991", str(cp_path), "BR00116991"),
            }
        )
    return rows


def transform_geo(rows_limit: int | None) -> tuple[list[dict], list[dict], list[dict]]:
    path = project_path("data", "raw", "geo", "GSE2034_series_matrix.txt.gz")
    if not path.exists():
        return [], [], []
    sample_meta, expr = parse_geo_series_matrix(path, sample_rows=rows_limit)
    samples, assays, measurements = [], [], []
    for _, row in sample_meta.iterrows():
        sid = str(row.get("sample_id") or row.get("geo_accession"))
        sample_id = stable_id("geo", sid)
        samples.append({"sample_id": sample_id, "subject_id": "", "sample_type": row.get("type", ""), **lineage("NCBI GEO", "GSE2034", str(path), sid)})
        assays.append({"assay_id": stable_id("geo-assay", sid), "sample_id": sample_id, "assay_type": "microarray", "platform": row.get("platform_id", ""), "source_file": str(path), **lineage("NCBI GEO", "GSE2034", str(path), sid)})
    value_cols = [c for c in expr.columns if c != "ID_REF"][:5]
    for i, row in expr.head(1000 if rows_limit else len(expr)).iterrows():
        for sample_col in value_cols:
            val = pd.to_numeric(row.get(sample_col), errors="coerce")
            measurements.append({"measurement_id": stable_id("geo-meas", i, sample_col), "assay_id": stable_id("geo-assay", sample_col), "measurement_name": row.get("ID_REF", ""), "measurement_value": val, "unit": "processed expression value", **lineage("NCBI GEO", "GSE2034", str(path), f"{i}:{sample_col}")})
    return samples, assays, measurements


def transform_cell_painting(rows_limit: int | None) -> tuple[list[dict], list[dict], list[dict]]:
    path = project_path("data", "raw", "cell_painting", "BR00116991.csv.gz")
    if not path.exists():
        return [], [], []
    frame = read_tabular_sample(path, nrows=rows_limit or 500000)
    samples, assays, morph = [], [], []
    feature_cols = [c for c in frame.columns if c.startswith(("Cells_", "Cytoplasm_", "Nuclei_"))][:8]
    for idx, row in frame.iterrows():
        well = str(row.get("Metadata_Well", row.get("Well", idx)))
        plate = str(row.get("Metadata_Plate", "BR00116991"))
        sample_id = stable_id("cp", plate, well)
        samples.append({"sample_id": sample_id, "subject_id": "", "sample_type": "well", **lineage("Broad Institute Cell Painting Gallery", "cpg0000-jump-pilot/source_4/BR00116991", str(path), f"{plate}:{well}")})
        assays.append({"assay_id": stable_id("cp-assay", plate, well), "sample_id": sample_id, "assay_type": "Cell Painting", "platform": "microscopy morphology profiling", "source_file": str(path), **lineage("Broad Institute Cell Painting Gallery", "cpg0000-jump-pilot/source_4/BR00116991", str(path), f"{plate}:{well}")})
        for col in feature_cols:
            morph.append({"morphology_profile_id": stable_id("cp-morph", idx, col), "sample_id": sample_id, "feature_name": col, "feature_value": pd.to_numeric(row.get(col), errors="coerce"), **lineage("Broad Institute Cell Painting Gallery", "cpg0000-jump-pilot/source_4/BR00116991", str(path), f"{idx}:{col}")})
    return samples, assays, morph


def transform_openneuro(rows_limit: int | None) -> tuple[list[dict], list[dict]]:
    path = project_path("data", "raw", "openneuro", "participants.tsv")
    if not path.exists():
        return [], []
    frame = read_tabular_sample(path, nrows=rows_limit)
    subjects, assays = [], []
    for _, row in frame.iterrows():
        participant = str(row.get("participant_id", row.iloc[0]))
        subject_id = stable_id("openneuro", participant)
        subjects.append({"subject_id": subject_id, "study_id": study_id_for("openneuro"), "subject_type": "human", **lineage("OpenNeuro", "ds004504", str(path), participant)})
        assays.append({"assay_id": stable_id("eeg-assay", participant), "sample_id": "", "assay_type": "EEG", "platform": "BIDS EEG metadata", "source_file": str(path), **lineage("OpenNeuro", "ds004504", str(path), participant)})
    return subjects, assays


def build_terminology_concept_rows() -> list[dict]:
    vocab_path = project_path("config", "controlled_vocabularies.yaml")
    vocab = load_yaml(vocab_path)
    rows: list[dict] = []
    for category, terms in vocab.items():
        for term in terms:
            rows.append(
                {
                    "concept_id": stable_id("concept", category, term),
                    "concept_name": term,
                    "concept_category": category,
                    **lineage("controlled vocabulary", "project controlled vocabularies", str(vocab_path), f"{category}:{term}"),
                }
            )
    return rows


def build_lineage_rows(tables: dict[str, list[dict]], schema: dict) -> list[dict]:
    rows: list[dict] = []
    for table, records in tables.items():
        primary_key = schema.get(table, {}).get("primary_key", "")
        for record in records:
            record_id = str(record.get(primary_key, "")) if primary_key else ""
            rows.append(
                {
                    "lineage_id": stable_id("lineage", table, record_id),
                    "cdm_table": table,
                    "cdm_record_id": record_id,
                    "source_system": record.get("source_system", ""),
                    "source_file": record.get("source_file", ""),
                    "processing_script": "src/apply_cdm_mapping.py",
                }
            )
    return rows


def run() -> dict[str, int]:
    config = runtime_config()
    schema = load_yaml(project_path("config", "cdm_schema.yaml"))["tables"]
    row_limit = config.get("sample_rows") if config.get("mode") == "sample" else None
    data_sources = build_data_source_rows()
    studies = build_study_rows()
    geo_samples, geo_assays, measurements = transform_geo(row_limit)
    cp_samples, cp_assays, morph = transform_cell_painting(row_limit)
    subjects, eeg_assays = transform_openneuro(row_limit)
    concepts = build_terminology_concept_rows()
    content_tables = {
        "cdm_data_source": data_sources,
        "cdm_study": studies,
        "cdm_subject": subjects,
        "cdm_sample": geo_samples + cp_samples,
        "cdm_assay": geo_assays + cp_assays + eeg_assays,
        "cdm_measurement": measurements,
        "cdm_morphology_profile": morph,
        "cdm_terminology_concept": concepts,
    }
    tables = {**content_tables, "cdm_lineage": build_lineage_rows(content_tables, schema)}
    counts = {}
    for table, rows in tables.items():
        write_csv(rows, project_path("data", "cdm", f"{table}.csv"))
        counts[table] = len(rows)
    lines = ["# CDM Transformation Summary", "", f"Mapping version: {MAPPING_VERSION}", ""]
    lines.extend(f"- {table}: {count} rows" for table, count in counts.items())
    lines.append("")
    lines.append("All CDM tables preserve source_system, source_dataset, source_file, source_record_id, ingestion_timestamp, and mapping_version where row-level lineage is available.")
    project_path("data", "outputs", "cdm_transformation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return counts


if __name__ == "__main__":
    run()
