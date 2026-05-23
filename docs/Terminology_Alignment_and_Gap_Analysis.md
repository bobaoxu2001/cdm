# Terminology Alignment and Gap Analysis

This project uses simplified UMLS/SNOMED/LOINC-style controlled vocabulary examples. It does not claim licensed vocabulary integration.

## Summary
- anatomy_tissue / terminology_gap: 3 source fields
- assay_type / review_required: 1 source fields
- assay_type / terminology_gap: 162 source fields
- clinical_scale / auto_mapped: 1 source fields
- clinical_scale / terminology_gap: 526 source fields
- demographic_term / auto_mapped: 4 source fields
- demographic_term / terminology_gap: 56 source fields
- electrophysiology_term / review_required: 2 source fields
- electrophysiology_term / terminology_gap: 4 source fields
- genomics_term / terminology_gap: 266 source fields
- imaging_channel / terminology_gap: 2381 source fields
- measurement_term / terminology_gap: 2707 source fields

## Remediation Workflow

1. Auto-mapped terms can be accepted during steward review.
2. Review-required terms need contributor or domain expert confirmation.
3. Terminology gaps become vocabulary backlog items with proposed synonyms and source examples.
