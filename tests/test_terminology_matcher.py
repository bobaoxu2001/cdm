from src.terminology_matcher import best_match


def test_terminology_exact_or_high_match():
    match = best_match("duration")
    assert match["recommended_standard_term"] == "duration"
    assert match["match_score"] >= 90


def test_terminology_gap_threshold():
    match = best_match("unrecognized_custom_lab_phrase")
    assert match["status"] in {"review_required", "terminology_gap"}
