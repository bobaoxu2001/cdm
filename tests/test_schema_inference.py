import pandas as pd

from src.infer_schema import infer_dataframe_schema


def test_schema_inference_reports_required_fields():
    rows = infer_dataframe_schema(pd.DataFrame({"sample_id": ["S1"], "value": [1.2]}), "source.csv")
    fields = {row["field_name"]: row for row in rows}
    assert fields["sample_id"]["nullable"] is False
    assert fields["value"]["inferred_dtype"].startswith("float")
