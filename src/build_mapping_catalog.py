from __future__ import annotations

import pandas as pd

from src.infer_schema import run as infer_schema_run
from src.utils import project_path, write_csv


def choose_mapping(source_file: str, field: str, dtype: str) -> dict:
    lower = field.lower()
    source_system = "NCBI GEO" if "geo" in source_file.lower() else "Broad Institute Cell Painting Gallery" if "cell_painting" in source_file.lower() else "OpenNeuro"
    mapping = {
        "target_cdm_table": "",
        "target_cdm_field": "",
        "transformation_rule": "No direct CDM target; retain in source profile for review.",
        "mapping_status": "unmapped",
        "mapping_confidence": 0.2,
        "qa_rule_id": "",
        "value_set_crosswalk": "",
        "unit_standardization": "",
        "edge_case_handling": "Escalate to data steward if analytically required.",
    }
    if any(token in lower for token in ["geo_accession", "sample", "participant", "subject", "well"]):
        mapping.update(target_cdm_table="cdm_sample" if source_system != "OpenNeuro" else "cdm_subject", target_cdm_field="sample_id" if source_system != "OpenNeuro" else "subject_id", transformation_rule="Use as stable source-linked identifier.", mapping_status="mapped", mapping_confidence=0.9, qa_rule_id="QA-COMP-002")
    elif any(token in lower for token in ["title", "study", "organism", "characteristics"]):
        mapping.update(target_cdm_table="cdm_study", target_cdm_field="study_title" if "title" in lower else "organism", transformation_rule="Normalize text and preserve original source value.", mapping_status="partially_mapped", mapping_confidence=0.7)
    elif lower in {"id_ref", "identifier"} or "gene" in lower:
        mapping.update(target_cdm_table="cdm_measurement", target_cdm_field="measurement_name", transformation_rule="Use feature/gene identifier as measurement_name.", mapping_status="mapped", mapping_confidence=0.85)
    elif "cells_" in lower or "cytoplasm_" in lower or "nuclei_" in lower:
        mapping.update(target_cdm_table="cdm_morphology_profile", target_cdm_field="feature_value", transformation_rule="Unpivot morphology feature columns to long feature_name/feature_value records.", mapping_status="mapped", mapping_confidence=0.85, value_set_crosswalk="measurement_term:morphology feature")
    elif lower in {"onset", "duration", "trial_type"}:
        mapping.update(target_cdm_table="cdm_electrophysiology_event", target_cdm_field=lower, transformation_rule="Cast onset/duration to seconds; preserve trial_type text.", mapping_status="mapped", mapping_confidence=0.9, qa_rule_id="QA-PLAUS-001" if lower == "duration" else "")
    elif "assay" in lower or "platform" in lower or "channel" in lower:
        mapping.update(target_cdm_table="cdm_assay", target_cdm_field="assay_type" if "assay" in lower else "platform", transformation_rule="Map to simplified controlled vocabulary where possible.", mapping_status="partially_mapped", mapping_confidence=0.75, qa_rule_id="QA-CONF-001")
    elif dtype.startswith("float") or dtype.startswith("int"):
        mapping.update(target_cdm_table="cdm_measurement", target_cdm_field="measurement_value", transformation_rule="Cast numeric source value and preserve unit if available.", mapping_status="review_required", mapping_confidence=0.65)
    return mapping


def build_catalog() -> list[dict]:
    schema_rows = infer_schema_run()
    rows: list[dict] = []
    for item in schema_rows:
        source_file = item["source_file"]
        field = item["field_name"]
        source_system = "NCBI GEO" if "geo" in source_file.lower() else "Broad Institute Cell Painting Gallery" if "cell_painting" in source_file.lower() else "OpenNeuro"
        dataset = "GSE2034" if source_system == "NCBI GEO" else "cpg0000-jump-pilot/source_4/BR00116991" if source_system.startswith("Broad") else "ds004504"
        mapping = choose_mapping(source_file, field, item["inferred_dtype"])
        rows.append(
            {
                "source_system": source_system,
                "source_dataset": dataset,
                "source_file": source_file,
                "source_field": field,
                "source_description": item.get("example_values", ""),
                "source_data_type": item["inferred_dtype"],
                "observed_values_or_range": item.get("example_values", ""),
                "target_cdm_table": mapping["target_cdm_table"],
                "target_cdm_field": mapping["target_cdm_field"],
                "target_data_type": "",
                "transformation_rule": mapping["transformation_rule"],
                "value_set_crosswalk": mapping["value_set_crosswalk"],
                "unit_standardization": mapping["unit_standardization"],
                "edge_case_handling": mapping["edge_case_handling"],
                "required_flag": mapping["target_cdm_field"] in {"sample_id", "subject_id", "measurement_name"},
                "qa_rule_id": mapping["qa_rule_id"],
                "mapping_status": mapping["mapping_status"],
                "mapping_confidence": mapping["mapping_confidence"],
                "reviewer_notes": "",
            }
        )
    write_csv(rows, project_path("data", "outputs", "source_to_cdm_mapping_catalog.csv"))
    return rows


if __name__ == "__main__":
    build_catalog()
