import pandas as pd

from src.build_mapping_catalog import choose_mapping


def test_mapping_required_identifier_field():
    mapping = choose_mapping("data/raw/geo/GSE2034_series_matrix.txt.gz", "geo_accession", "object")
    assert mapping["target_cdm_table"] == "cdm_sample"
    assert mapping["target_cdm_field"] == "sample_id"
    assert mapping["mapping_status"] == "mapped"


def test_mapping_coverage_calculation_shape():
    catalog = pd.DataFrame({"mapping_status": ["mapped", "partially_mapped", "unmapped"]})
    coverage = catalog["mapping_status"].isin(["mapped", "partially_mapped"]).mean()
    assert coverage == 2 / 3
