from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import load_yaml, project_path, write_csv


def read_cdm_table(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def result(rule: dict, pass_count: int, fail_count: int, table: str | None = None, field: str | None = None) -> dict:
    total = pass_count + fail_count
    pass_rate = pass_count / total if total else 1.0
    threshold = float(rule.get("acceptance_threshold", 1.0))
    status = "pass" if pass_rate >= threshold else "warning" if pass_rate >= threshold * 0.9 else "fail"
    return {
        "qa_rule_id": rule["qa_rule_id"],
        "qa_dimension": rule["qa_dimension"],
        "cdm_table": table or rule["cdm_table"],
        "field_name": field or rule["field_name"],
        "severity": rule["severity"],
        "check_description": rule["check_type"],
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": round(pass_rate, 4),
        "acceptance_threshold": threshold,
        "status": status,
        "remediation_guidance": rule["remediation_guidance"],
    }


def non_null_check(frame: pd.DataFrame, field: str) -> tuple[int, int]:
    if field not in frame.columns:
        return 0, len(frame)
    ok = frame[field].notna() & (frame[field].astype(str).str.len() > 0)
    return int(ok.sum()), int((~ok).sum())


def unique_check(frame: pd.DataFrame, pk: str) -> tuple[int, int]:
    if pk not in frame.columns:
        return 0, len(frame)
    duplicates = frame[pk].duplicated(keep=False)
    return int((~duplicates).sum()), int(duplicates.sum())


def referential_integrity_check(frame: pd.DataFrame, field: str, parent_keys: set[str]) -> tuple[int, int]:
    """Count non-empty foreign key values that do (and do not) resolve to a parent key."""
    if field not in frame.columns:
        return 0, 0
    values = frame[field].dropna().astype(str)
    values = values[values.str.len() > 0]
    resolved = values.isin(parent_keys)
    return int(resolved.sum()), int((~resolved).sum())


def referential_integrity_results(rule: dict, schema: dict, frames: dict[str, pd.DataFrame]) -> list[dict]:
    rows: list[dict] = []
    for table, table_def in schema.items():
        child = frames.get(table)
        if child is None or child.empty:
            continue
        for field in table_def.get("fields", []):
            foreign_key = str(field.get("foreign_key", ""))
            if "." not in foreign_key:
                continue
            parent_table, parent_field = foreign_key.split(".", 1)
            parent = frames.get(parent_table)
            if parent is None or parent.empty or parent_field not in parent.columns:
                continue
            parent_keys = set(parent[parent_field].dropna().astype(str))
            pc, fc = referential_integrity_check(child, field["field_name"], parent_keys)
            rows.append(result(rule, pc, fc, table=table, field=field["field_name"]))
    return rows


def run() -> list[dict]:
    rules = load_yaml(project_path("config", "qa_rules.yaml"))["rules"]
    schema = load_yaml(project_path("config", "cdm_schema.yaml"))["tables"]
    rows: list[dict] = []
    cdm_files = {
        p.stem: p
        for p in project_path("data", "cdm").glob("cdm_*.csv")
        if p.stem != "cdm_data_quality_result"
    }
    frames = {table: read_cdm_table(path) for table, path in cdm_files.items()}
    for table, frame in frames.items():
        for rule in rules:
            if rule["cdm_table"] not in {"*", table}:
                continue
            if table in rule.get("exclude_tables", []):
                continue
            if rule["check_type"] == "referential_integrity":
                continue
            if rule["check_type"] == "non_null":
                pc, fc = non_null_check(frame, rule["field_name"])
                rows.append(result(rule, pc, fc, table=table))
            elif rule["check_type"] == "unique":
                pk = schema.get(table, {}).get("primary_key", "primary_key")
                pc, fc = unique_check(frame, pk)
                rows.append(result(rule, pc, fc, table=table, field=pk))
            elif rule["check_type"] == "allowed_values" and rule["field_name"] in frame.columns:
                allowed = set(load_yaml(project_path("config", "controlled_vocabularies.yaml")).get("assay_type", []))
                ok = frame[rule["field_name"]].isin(allowed)
                rows.append(result(rule, int(ok.sum()), int((~ok).sum()), table=table))
            elif rule["check_type"] == "non_negative" and rule["field_name"] in frame.columns:
                vals = pd.to_numeric(frame[rule["field_name"]], errors="coerce")
                ok = vals.ge(0) | vals.isna()
                rows.append(result(rule, int(ok.sum()), int((~ok).sum()), table=table))
    ref_rule = next((r for r in rules if r["check_type"] == "referential_integrity"), None)
    if ref_rule:
        rows.extend(referential_integrity_results(ref_rule, schema, frames))
    mapping_path = project_path("data", "outputs", "source_to_cdm_mapping_catalog.csv")
    if mapping_path.exists():
        catalog = pd.read_csv(mapping_path)
        mapped = catalog["mapping_status"].isin(["mapped", "partially_mapped"])
        rule = next(r for r in rules if r["qa_rule_id"] == "QA-MAP-001")
        rows.append(result(rule, int(mapped.sum()), int((~mapped).sum()), table="mapping_catalog", field="mapping_status"))
    write_csv(rows, project_path("data", "outputs", "qa_results.csv"))
    qa_cdm_rows = [{**row, "qa_result_id": f"QA-{idx:05d}"} for idx, row in enumerate(rows, start=1)]
    write_csv(qa_cdm_rows, project_path("data", "cdm", "cdm_data_quality_result.csv"))
    write_summary(rows)
    return rows


def write_summary(rows: list[dict]) -> None:
    frame = pd.DataFrame(rows)
    lines = ["# QA Summary", "", "QA checks cover completeness, conformance, plausibility, uniqueness, referential integrity, lineage traceability, and mapping coverage.", ""]
    if not frame.empty:
        for status, count in frame["status"].value_counts().items():
            lines.append(f"- {status}: {count} checks")
        lines.extend(["", "## High Severity Exceptions", ""])
        high = frame[(frame["severity"] == "high") & (frame["status"] != "pass")]
        if high.empty:
            lines.append("No high-severity failing checks in the current run.")
        else:
            for _, row in high.iterrows():
                lines.append(f"- {row['qa_rule_id']} on {row['cdm_table']}.{row['field_name']}: {row['status']} ({row['pass_rate']})")
    project_path("data", "outputs", "qa_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
