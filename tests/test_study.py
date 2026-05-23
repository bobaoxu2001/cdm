from src.apply_cdm_mapping import build_study_rows, transform_openneuro


def test_study_rows_have_required_fields():
    rows = build_study_rows()
    assert rows, "expected study rows from committed raw data"
    for row in rows:
        for field in ["study_id", "data_source_id", "study_title", "source_system"]:
            assert row.get(field), f"missing {field} in study row"


def test_openneuro_subjects_reference_existing_study():
    study_ids = {row["study_id"] for row in build_study_rows()}
    subjects, _, _obs = transform_openneuro(None)
    assert subjects, "expected OpenNeuro subjects from committed raw data"
    assert all(subject["study_id"] in study_ids for subject in subjects)


def test_clinical_observations_emitted_for_openneuro():
    _subjects, _assays, observations = transform_openneuro(None)
    assert observations, "expected clinical observation rows from OpenNeuro participants"
    obs_types = {obs["observation_type"] for obs in observations}
    assert obs_types, "clinical observations must have an observation_type"
    valid_types = {"age", "gender", "clinical_scale_score", "group_assignment"}
    assert obs_types.issubset(valid_types), f"unexpected observation types: {obs_types - valid_types}"


def test_clinical_observations_reference_subjects():
    subjects, _assays, observations = transform_openneuro(None)
    subject_ids = {s["subject_id"] for s in subjects}
    for obs in observations:
        assert obs["subject_id"] in subject_ids, f"orphaned observation for subject {obs['subject_id']}"


def test_clinical_observations_have_required_fields():
    _subjects, _assays, observations = transform_openneuro(None)
    for obs in observations:
        for field in ["observation_id", "subject_id", "observation_type", "observation_name", "source_system", "source_record_id"]:
            assert obs.get(field) is not None, f"missing {field} in clinical observation"
