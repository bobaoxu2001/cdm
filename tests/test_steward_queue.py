import pandas as pd
import pytest

from src.generate_steward_review_queue import _priority_label, _recommended_action


def test_priority_high_for_unmapped_with_terminology_gap():
    # unmapped(2) + terminology_gap(2) = 4 → HIGH
    assert _priority_label(4) == "HIGH"


def test_priority_medium():
    # review_required(3) + auto_mapped(0) = 3 → MEDIUM
    assert _priority_label(3) == "MEDIUM"
    # unmapped(2) + auto_mapped(0) = 2 → MEDIUM
    assert _priority_label(2) == "MEDIUM"


def test_priority_low_for_partially_mapped_auto_mapped():
    # partially_mapped(1) + auto_mapped(0) = 1 → LOW
    assert _priority_label(1) == "LOW"
    assert _priority_label(0) == "LOW"


def test_recommended_action_unmapped_terminology_gap():
    action = _recommended_action("unmapped", "terminology_gap")
    assert "CDM target" in action and "controlled vocabulary" in action


def test_recommended_action_review_required():
    action = _recommended_action("review_required", "auto_mapped")
    assert "numeric" in action.lower() or "domain" in action.lower()


def test_recommended_action_accept_for_mapped():
    action = _recommended_action("mapped", "auto_mapped")
    assert "Accept" in action
