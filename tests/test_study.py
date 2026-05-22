from src.apply_cdm_mapping import build_study_rows, transform_openneuro


def test_study_rows_have_required_fields():
    rows = build_study_rows()
    assert rows, "expected study rows from committed raw data"
    for row in rows:
        for field in ["study_id", "data_source_id", "study_title", "source_system"]:
            assert row.get(field), f"missing {field} in study row"


def test_openneuro_subjects_reference_existing_study():
    study_ids = {row["study_id"] for row in build_study_rows()}
    subjects, _ = transform_openneuro(None)
    assert subjects, "expected OpenNeuro subjects from committed raw data"
    assert all(subject["study_id"] in study_ids for subject in subjects)
