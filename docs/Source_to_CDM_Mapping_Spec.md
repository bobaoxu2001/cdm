# Source-to-CDM Mapping Spec

## Mapping Principles

- Preserve original source values in profiles and lineage before standardization.
- Prefer explicit source identifiers over generated identifiers; generate stable hashes only when needed.
- Treat CDM outputs as a lightweight research harmonization layer, not a full OMOP implementation.
- Mark uncertain fields as `review_required` instead of forcing low-confidence mappings.

## Source-to-Target Examples

| Source | Source field | Target table.field | Transformation |
|---|---|---|---|
| GEO | geo_accession | cdm_sample.sample_id | Stable hash plus original source_record_id |
| GEO | ID_REF | cdm_measurement.measurement_name | Preserve probe/gene feature id |
| Cell Painting | Metadata_Well | cdm_sample.sample_id | Combine plate and well into stable sample id |
| Cell Painting | Cells_* / Cytoplasm_* / Nuclei_* | cdm_morphology_profile.feature_value | Unpivot wide features to long profile records |
| OpenNeuro | participant_id | cdm_subject.subject_id | Stable participant-linked subject id |

## Mapping Status Definitions

| Status | Meaning |
|---|---|
| mapped | Direct target and transformation rule are available |
| partially_mapped | Target exists but vocabulary, unit, or context needs review |
| unmapped | No current CDM target |
| review_required | Plausible target needs steward confirmation |

## Reviewer Workflow

Reviewers filter `data/outputs/source_to_cdm_mapping_catalog.csv` for `unmapped`, `partially_mapped`, and `review_required`, update reviewer notes, then promote accepted rules into config-driven mapping logic.
