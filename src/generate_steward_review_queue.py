from __future__ import annotations

import pandas as pd

from src.utils import project_path, write_csv


_MAPPING_SCORE = {"review_required": 3, "unmapped": 2, "partially_mapped": 1, "mapped": 0}
_TERM_SCORE = {"terminology_gap": 2, "review_required": 1, "auto_mapped": 0}
_PRIORITY = {(4, 5): "HIGH", (2, 3): "MEDIUM", (0, 1): "LOW"}


def _priority_label(total: int) -> str:
    if total >= 4:
        return "HIGH"
    if total >= 2:
        return "MEDIUM"
    return "LOW"


def _recommended_action(mapping_status: str, term_status: str) -> str:
    if mapping_status == "unmapped" and term_status == "terminology_gap":
        return "Define CDM target field and add controlled vocabulary term"
    if mapping_status == "unmapped":
        return "Assign CDM target table and field; update mapping_rules.yaml"
    if mapping_status == "review_required":
        return "Confirm numeric cast and CDM field assignment with domain expert"
    if mapping_status == "partially_mapped":
        return "Complete mapping rule; verify transformation_rule covers all source values"
    if term_status == "terminology_gap":
        return "Add source term or synonym to controlled_vocabularies.yaml"
    if term_status == "review_required":
        return "Validate recommended standard term with domain expert"
    return "Accept mapping and close review item"


def run() -> list[dict]:
    mapping_path = project_path("data", "outputs", "source_to_cdm_mapping_catalog.csv")
    terminology_path = project_path("data", "outputs", "terminology_alignment_report.csv")

    if not mapping_path.exists():
        return []

    mapping = pd.read_csv(mapping_path)
    terminology = pd.read_csv(terminology_path) if terminology_path.exists() else pd.DataFrame()

    term_index: dict[tuple[str, str, str], dict] = {}
    if not terminology.empty:
        for _, row in terminology.iterrows():
            key = (str(row.get("source_system", "")), str(row.get("source_dataset", "")), str(row.get("source_field", "")))
            term_index[key] = row.to_dict()

    queue: list[dict] = []
    for _, row in mapping.iterrows():
        mapping_status = str(row.get("mapping_status", "unmapped"))
        if mapping_status == "mapped":
            continue

        key = (str(row.get("source_system", "")), str(row.get("source_dataset", "")), str(row.get("source_field", "")))
        term_row = term_index.get(key, {})
        term_status = str(term_row.get("status", "terminology_gap"))

        m_score = _MAPPING_SCORE.get(mapping_status, 2)
        t_score = _TERM_SCORE.get(term_status, 2)
        total_score = m_score + t_score

        queue.append({
            "priority": _priority_label(total_score),
            "priority_score": total_score,
            "source_system": row.get("source_system", ""),
            "source_dataset": row.get("source_dataset", ""),
            "source_field": row.get("source_field", ""),
            "source_data_type": row.get("source_data_type", ""),
            "observed_values_sample": row.get("observed_values_or_range", ""),
            "mapping_status": mapping_status,
            "current_cdm_target": f"{row.get('target_cdm_table', '')}.{row.get('target_cdm_field', '')}".strip("."),
            "terminology_status": term_status,
            "recommended_standard_term": term_row.get("recommended_standard_term", ""),
            "recommended_action": _recommended_action(mapping_status, term_status),
            "qa_rule_id": row.get("qa_rule_id", ""),
        })

    queue.sort(key=lambda x: (-x["priority_score"], x["source_system"], x["source_field"]))
    write_csv(queue, project_path("data", "outputs", "steward_review_queue.csv"))
    _write_report(queue)
    return queue


def _write_report(queue: list[dict]) -> None:
    frame = pd.DataFrame(queue) if queue else pd.DataFrame()
    lines = [
        "# Steward Review Queue",
        "",
        "Prioritized list of source fields that require data steward review before the mapping can be accepted.",
        "Fields with `mapped` status and `auto_mapped` terminology are excluded.",
        "",
        "## Summary",
        "",
    ]
    if not frame.empty:
        for priority in ("HIGH", "MEDIUM", "LOW"):
            count = int((frame["priority"] == priority).sum())
            lines.append(f"- {priority}: {count} fields")
        lines.extend(["", "## High Priority Items", ""])
        high = frame[frame["priority"] == "HIGH"]
        if high.empty:
            lines.append("No high-priority review items.")
        else:
            for _, row in high.iterrows():
                lines.append(
                    f"- **{row['source_system']} / {row['source_field']}** "
                    f"(mapping: `{row['mapping_status']}`, terminology: `{row['terminology_status']}`): "
                    f"{row['recommended_action']}"
                )
    else:
        lines.append("No fields requiring steward review.")

    project_path("data", "outputs", "steward_review_queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
