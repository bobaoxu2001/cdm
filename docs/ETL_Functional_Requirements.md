# ETL Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| FR-001 | Ingest public GEO, Cell Painting, and OpenNeuro metadata/profile files. | Downloads are logged in `data/manifests/download_manifest.csv`; failures produce manual instructions, not fake data. |
| FR-002 | Support sample and full runtime modes. | `config/runtime.yaml` controls row limits, chunk size, and large raw-file toggles. |
| FR-003 | Profile large source files safely. | CSV/TSV/gzip files are read in chunks and summarized to source profile outputs. |
| FR-004 | Infer source schema. | Field names, dtypes, missingness, and examples are written to schema inference output. |
| FR-005 | Build source-to-CDM mapping catalog. | Each discovered source field receives target, status, confidence, transformation rule, and reviewer notes. |
| FR-006 | Transform mapped source records to lightweight CDM tables. | CDM CSVs are created under `data/cdm/` with lineage columns. |
| FR-007 | Align terminology. | Source fields are matched to simplified controlled vocabularies using fuzzy and TF-IDF matching. |
| FR-008 | Run QA acceptance checks. | QA results include rule id, dimension, severity, pass/fail counts, pass rate, threshold, and remediation guidance. |
| FR-009 | Track file-level lineage. | Manifest includes checksum, row/column count where practical, stage, parent, script, and notes. |
| FR-010 | Generate contributor-facing documentation. | Docs explain required metadata, file formats, naming, identifiers, QA loop, and remediation workflow. |
| FR-011 | Support engineering handoff. | SQL, Makefile commands, config files, tests, and reports are reproducible from a fresh checkout. |
