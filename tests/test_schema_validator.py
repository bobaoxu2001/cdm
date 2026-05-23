import pandas as pd
import pytest

from src.validate_cdm_schema import validate_table


_TABLE_DEF = {
    "primary_key": "obs_id",
    "fields": [
        {"field_name": "obs_id", "data_type": "string", "required_flag": True, "nullable": False, "primary_key": True},
        {"field_name": "subject_id", "data_type": "string", "required_flag": True, "nullable": False},
        {"field_name": "score", "data_type": "float", "required_flag": False, "nullable": True},
        {"field_name": "obs_type", "data_type": "string", "required_flag": True, "nullable": False,
         "allowed_values": ["age", "gender"]},
    ],
}


def test_validator_passes_clean_frame():
    frame = pd.DataFrame({
        "obs_id": ["a", "b", "c"],
        "subject_id": ["s1", "s2", "s3"],
        "score": [1.0, 2.0, 3.0],
        "obs_type": ["age", "gender", "age"],
    })
    results = validate_table("test_table", _TABLE_DEF, frame)
    failed = [r for r in results if r["status"] == "fail"]
    assert not failed, f"unexpected failures: {failed}"


def test_validator_catches_null_in_required_field():
    frame = pd.DataFrame({
        "obs_id": ["a", "b", None],
        "subject_id": ["s1", "s2", "s3"],
        "score": [1.0, 2.0, 3.0],
        "obs_type": ["age", "gender", "age"],
    })
    results = validate_table("test_table", _TABLE_DEF, frame)
    null_fails = [r for r in results if r["check"] == "non_null" and r["status"] == "fail" and r["field"] == "obs_id"]
    assert null_fails, "expected null check failure on obs_id"


def test_validator_catches_duplicate_primary_key():
    frame = pd.DataFrame({
        "obs_id": ["a", "a", "c"],
        "subject_id": ["s1", "s2", "s3"],
        "score": [1.0, 2.0, 3.0],
        "obs_type": ["age", "gender", "age"],
    })
    results = validate_table("test_table", _TABLE_DEF, frame)
    pk_fails = [r for r in results if r["check"] == "primary_key_unique" and r["status"] == "fail"]
    assert pk_fails, "expected primary key uniqueness failure"


def test_validator_catches_invalid_allowed_value():
    frame = pd.DataFrame({
        "obs_id": ["a", "b"],
        "subject_id": ["s1", "s2"],
        "score": [1.0, 2.0],
        "obs_type": ["age", "UNKNOWN_TYPE"],
    })
    results = validate_table("test_table", _TABLE_DEF, frame)
    av_fails = [r for r in results if r["check"] == "allowed_values" and r["status"] == "fail"]
    assert av_fails, "expected allowed_values failure for obs_type"


def test_validator_catches_missing_required_field():
    frame = pd.DataFrame({"obs_id": ["a"], "score": [1.0]})
    results = validate_table("test_table", _TABLE_DEF, frame)
    presence_fails = [r for r in results if r["check"] == "field_presence" and r["status"] == "fail"]
    assert presence_fails, "expected field_presence failure for missing required fields"


def test_validator_warns_on_non_numeric_float_field():
    frame = pd.DataFrame({
        "obs_id": ["a", "b"],
        "subject_id": ["s1", "s2"],
        "score": ["not_a_number", "also_bad"],
        "obs_type": ["age", "gender"],
    })
    results = validate_table("test_table", _TABLE_DEF, frame)
    type_warns = [r for r in results if r["check"] == "data_type_coercion" and r["status"] == "warning"]
    assert type_warns, "expected data_type_coercion warning for non-numeric float field"
