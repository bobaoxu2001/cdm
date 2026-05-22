# QA Framework and Acceptance Criteria

## Dimensions

Completeness, conformance, plausibility, uniqueness, referential integrity, lineage traceability, and mapping coverage.

## Severity Levels

| Severity | Meaning |
|---|---|
| high | Blocks trusted harmonized release |
| medium | Requires review before downstream reuse |
| low | Informational quality improvement |

## Rule Inventory

The executable rule set is in `config/qa_rules.yaml`. Examples include required lineage fields, unique primary keys, assay type conformance, non-negative measurement values, schema-driven foreign key resolution, mapping coverage threshold, and source-file traceability.

## Remediation Workflow

1. Review `data/outputs/qa_summary.md` for failed high-severity checks.
2. Open `data/outputs/qa_results.csv` for row counts, thresholds, and remediation guidance.
3. Fix source metadata, mapping logic, or controlled vocabulary configuration.
4. Re-run `make transform terminology qa reports`.

## Sample QA Output

| qa_rule_id | dimension | status | remediation |
|---|---|---|---|
| QA-COMP-001 | completeness | pass/warning/fail | Populate source lineage during ingestion or mapping |
| QA-MAP-001 | mapping_coverage | pass/warning/fail | Prioritize unmapped source fields for steward review |
