from __future__ import annotations

import pandas as pd

from src.utils import load_yaml, project_path, write_csv


def _read_cdm(table: str) -> pd.DataFrame:
    path = project_path("data", "cdm", f"{table}.csv")
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _check(table: str, field: str, check: str, status: str, detail: str, severity: str) -> dict:
    return {"table": table, "field": field, "check": check, "severity": severity, "status": status, "detail": detail}


def validate_table(table_name: str, table_def: dict, frame: pd.DataFrame) -> list[dict]:
    results: list[dict] = []
    pk_field = table_def.get("primary_key", "")

    for field_def in table_def.get("fields", []):
        fname = field_def["field_name"]
        required = field_def.get("required_flag", False)
        nullable = field_def.get("nullable", True)
        dtype = field_def.get("data_type", "string")
        allowed = field_def.get("allowed_values", [])
        is_pk = field_def.get("primary_key", False) or fname == pk_field
        severity = "high" if required or is_pk else "medium"

        # field presence
        if fname not in frame.columns:
            if required:
                results.append(_check(table_name, fname, "field_presence", "fail", "Required field absent from CDM output", "high"))
            continue

        col = frame[fname]
        total = len(col)

        # non-null / non-empty for required non-nullable fields
        if not nullable:
            empty = col.isna() | (col.astype(str).str.strip() == "") | (col.astype(str) == "nan")
            null_count = int(empty.sum())
            if null_count:
                results.append(_check(table_name, fname, "non_null", "fail" if required else "warning", f"{null_count}/{total} null or empty values", severity))
            else:
                results.append(_check(table_name, fname, "non_null", "pass", "", severity))

        # primary key uniqueness
        if is_pk:
            dup_count = int(col.duplicated(keep=False).sum())
            if dup_count:
                results.append(_check(table_name, fname, "primary_key_unique", "fail", f"{dup_count} duplicate primary key values", "high"))
            else:
                results.append(_check(table_name, fname, "primary_key_unique", "pass", "", "high"))

        # allowed values
        if allowed:
            non_null = col.dropna()
            non_null = non_null[non_null.astype(str).str.strip() != ""]
            invalid_count = int((~non_null.isin(allowed)).sum())
            if invalid_count:
                invalid_sample = non_null[~non_null.isin(allowed)].unique()[:3].tolist()
                results.append(_check(table_name, fname, "allowed_values", "fail", f"{invalid_count} values outside allowed set; examples: {invalid_sample}", severity))
            else:
                results.append(_check(table_name, fname, "allowed_values", "pass", f"all values in {allowed}", severity))

        # numeric type coercion
        if dtype == "float":
            non_null_vals = col.dropna()
            coerced = pd.to_numeric(non_null_vals, errors="coerce")
            bad = int(coerced.isna().sum())
            if bad:
                results.append(_check(table_name, fname, "data_type_coercion", "warning", f"{bad}/{len(non_null_vals)} non-numeric values in declared float field", severity))

    return results


def run() -> list[dict]:
    schema = load_yaml(project_path("config", "cdm_schema.yaml"))["tables"]
    all_results: list[dict] = []

    for table_name, table_def in schema.items():
        frame = _read_cdm(table_name)
        if frame.empty and table_name not in {"cdm_clinical_observation"}:
            all_results.append(_check(table_name, "", "table_presence", "warning", "CDM table file is empty or missing", "high"))
            continue
        all_results.extend(validate_table(table_name, table_def, frame))

    write_csv(all_results, project_path("data", "outputs", "schema_conformance_report.csv"))
    _write_report(all_results)
    return all_results


def _write_report(results: list[dict]) -> None:
    frame = pd.DataFrame(results) if results else pd.DataFrame(columns=["table", "field", "check", "severity", "status", "detail"])
    status_counts = frame["status"].value_counts().to_dict() if not frame.empty else {}
    lines = [
        "# CDM Schema Conformance Report",
        "",
        "Validates generated CDM CSV outputs against `config/cdm_schema.yaml` field specifications.",
        "Checks: field presence, non-null constraints, primary key uniqueness, allowed value sets, and numeric type coercion.",
        "",
        "## Summary",
        "",
    ]
    for status in ("pass", "warning", "fail"):
        lines.append(f"- {status}: {status_counts.get(status, 0)} checks")

    failures = frame[frame["status"] == "fail"] if not frame.empty else pd.DataFrame()
    lines.extend(["", "## Failures", ""])
    if failures.empty:
        lines.append("No schema conformance failures.")
    else:
        for _, row in failures.iterrows():
            lines.append(f"- **{row['table']}.{row['field']}** [{row['check']}]: {row['detail']}")

    warnings = frame[frame["status"] == "warning"] if not frame.empty else pd.DataFrame()
    lines.extend(["", "## Warnings", ""])
    if warnings.empty:
        lines.append("No schema conformance warnings.")
    else:
        for _, row in warnings.iterrows():
            lines.append(f"- {row['table']}.{row['field']} [{row['check']}]: {row['detail']}")

    project_path("data", "outputs", "schema_conformance_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
