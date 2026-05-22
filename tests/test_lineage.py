from src.apply_cdm_mapping import lineage


def test_lineage_fields_present():
    row = lineage("NCBI GEO", "GSE2034", "file.txt", "row1")
    for field in ["source_system", "source_dataset", "source_file", "source_record_id", "ingestion_timestamp", "mapping_version"]:
        assert field in row
