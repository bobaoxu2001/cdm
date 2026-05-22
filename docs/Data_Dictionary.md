# Data Dictionary

The lightweight CDM is defined in `config/cdm_schema.yaml`. It is OMOP-inspired, but this project does not claim full OMOP compliance.

Core lineage fields preserved wherever row-level mapping is available:

| Field | Meaning |
|---|---|
| source_system | Public repository or source platform |
| source_dataset | Dataset accession, plate, or BIDS id |
| source_file | Local source file path |
| source_record_id | Stable record identifier from source row/feature |
| ingestion_timestamp | UTC timestamp for transformation |
| mapping_version | Mapping specification version |
