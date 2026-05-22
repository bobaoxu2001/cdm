from __future__ import annotations

from functools import lru_cache

from src.infer_schema import run as infer_schema_run
from src.utils import load_yaml, project_path, write_csv


@lru_cache(maxsize=1)
def _mapping_rules() -> dict:
    return load_yaml(project_path("config", "mapping_rules.yaml"))


MAPPING_OUTPUT_KEYS = (
    "target_cdm_table",
    "target_cdm_field",
    "transformation_rule",
    "value_set_crosswalk",
    "unit_standardization",
    "edge_case_handling",
    "qa_rule_id",
    "mapping_status",
    "mapping_confidence",
)


def _rule_matches(rule: dict, lower_field: str) -> bool:
    if lower_field in rule.get("field_exact", []):
        return True
    return any(token in lower_field for token in rule.get("field_tokens", []))


def _resolve_target_field(rule: dict, lower_field: str) -> str:
    if "target_cdm_field" in rule:
        return rule["target_cdm_field"]
    by_token = rule.get("target_cdm_field_by_token", {})
    for token, target in by_token.items():
        if token != "default" and token in lower_field:
            return target
    return by_token.get("default", "")


def choose_mapping(field: str, dtype: str) -> dict:
    """Resolve a source field to a CDM target using config/mapping_rules.yaml."""
    config = _mapping_rules()
    mapping = dict(config["default"])
    lower = field.lower()
    for rule in config["rules"]:
        if _rule_matches(rule, lower):
            for key in MAPPING_OUTPUT_KEYS:
                if key in rule:
                    mapping[key] = rule[key]
            mapping["target_cdm_field"] = _resolve_target_field(rule, lower)
            return mapping
    if dtype.startswith(("float", "int")):
        for key in MAPPING_OUTPUT_KEYS:
            if key in config["numeric_fallback"]:
                mapping[key] = config["numeric_fallback"][key]
    return mapping


def build_catalog() -> list[dict]:
    schema_rows = infer_schema_run()
    rows: list[dict] = []
    for item in schema_rows:
        source_file = item["source_file"]
        field = item["field_name"]
        source_system = "NCBI GEO" if "geo" in source_file.lower() else "Broad Institute Cell Painting Gallery" if "cell_painting" in source_file.lower() else "OpenNeuro"
        dataset = "GSE2034" if source_system == "NCBI GEO" else "cpg0000-jump-pilot/source_4/BR00116991" if source_system.startswith("Broad") else "ds004504"
        mapping = choose_mapping(field, item["inferred_dtype"])
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
