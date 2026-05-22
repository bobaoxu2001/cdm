import pandas as pd

from src.run_qa_checks import non_null_check, referential_integrity_check, unique_check


def test_qa_completeness_check():
    frame = pd.DataFrame({"source_system": ["GEO", "", None]})
    passed, failed = non_null_check(frame, "source_system")
    assert passed == 1
    assert failed == 2


def test_qa_uniqueness_check():
    frame = pd.DataFrame({"id": ["a", "b", "b"]})
    passed, failed = unique_check(frame, "id")
    assert passed == 1
    assert failed == 2


def test_qa_referential_integrity_check():
    frame = pd.DataFrame({"assay_id": ["a1", "a2", "orphan", ""]})
    passed, failed = referential_integrity_check(frame, "assay_id", {"a1", "a2"})
    assert passed == 2
    assert failed == 1
