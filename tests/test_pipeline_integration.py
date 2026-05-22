"""End-to-end integration test: runs the mapping, transform, and QA stages
against the committed public raw data and asserts the CDM is populated and
internally consistent. Uses a reduced row sample to keep the test fast."""

from src.apply_cdm_mapping import run as transform_run
from src.build_mapping_catalog import build_catalog
from src.run_qa_checks import run as qa_run


EXPECTED_NON_EMPTY = [
    "cdm_data_source",
    "cdm_study",
    "cdm_subject",
    "cdm_sample",
    "cdm_assay",
    "cdm_measurement",
    "cdm_morphology_profile",
    "cdm_terminology_concept",
    "cdm_lineage",
]


def test_pipeline_produces_consistent_cdm(monkeypatch):
    fast_config = {"mode": "sample", "sample_rows": 3000, "chunk_size": 100000}
    monkeypatch.setattr("src.infer_schema.runtime_config", lambda: fast_config)
    monkeypatch.setattr("src.apply_cdm_mapping.runtime_config", lambda: fast_config)

    build_catalog()
    counts = transform_run()
    for table in EXPECTED_NON_EMPTY:
        assert counts.get(table, 0) > 0, f"{table} should not be empty"

    qa_rows = qa_run()
    high_failures = [r for r in qa_rows if r["severity"] == "high" and r["status"] == "fail"]
    assert not high_failures, f"high-severity QA failures: {high_failures}"

    ref_checks = [r for r in qa_rows if r["qa_rule_id"] == "QA-REF-001"]
    assert ref_checks, "referential integrity checks should run"
    assert all(r["status"] == "pass" for r in ref_checks), "every foreign key must resolve to a parent record"
