# Contributor Onboarding Guide

This guide is written for research data contributors preparing files for harmonization.

## Required Metadata

- Study title, accession or dataset id, public landing page, citation, and license/usage notes.
- Sample or participant identifiers that are stable within the source system.
- Assay type, platform/instrument, organism/model system, and collection context where available.
- File-level descriptions for each submitted CSV, TSV, JSON, parquet, or matrix file.

## Preferred File Formats

Use CSV, TSV, parquet, JSON metadata, or BIDS-compliant files. Compress large delimited files with gzip. Avoid spreadsheet-only submissions for large tables.

## Naming and Identifiers

Use stable identifiers such as `participant_id`, `sample_id`, `plate_id`, `well_id`, `channel`, and `event_id`. Do not embed private identifiers or PHI.

## Controlled Vocabulary Expectations

Map assay, tissue/anatomy, imaging channel, electrophysiology, and measurement terms to the simplified project vocabulary when possible. Unknown terms should include definitions and examples.

## QA Feedback Loop

Contributors receive QA exceptions with severity, pass rate, threshold, and remediation guidance. Remediated files should keep the same dataset id and include a version note.
