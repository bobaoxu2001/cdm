# Role Alignment: Data Harmonization Analyst / Data Science Analyst

| Role responsibility | Project evidence | File/output | Skill demonstrated |
|---|---|---|---|
| NAMs/source data profiling | Profiles GEO, Cell Painting, and OpenNeuro public research data | `src/profile_source_data.py`, `data/outputs/source_profile_*` | Large-scale metadata and source quality assessment |
| Source-to-CDM mapping | Config-driven, field-level mapping catalog with status, confidence, rules, and edge cases | `config/mapping_rules.yaml`, `src/build_mapping_catalog.py`, `docs/Source_to_CDM_Mapping_Spec.md` | Harmonization analysis and steward review workflow |
| ETL functional requirements | Formal FR IDs for ingestion through reporting | `docs/ETL_Functional_Requirements.md` | Engineering handoff and reproducibility |
| Data quality QA | Rule-driven QA with pass/fail counts, thresholds, and remediation | `config/qa_rules.yaml`, `src/run_qa_checks.py` | Acceptance criteria and release readiness |
| Terminology alignment | Fuzzy/TF-IDF matching to simplified controlled terms | `src/terminology_matcher.py` | Vocabulary normalization and gap management |
| FAIR principles | Manifest, public access, interoperability, and reuse documentation | `docs/FAIR_Principles_Alignment.md` | Metadata standards and responsible reuse |
| Contributor documentation | Contributor-facing metadata and remediation guide | `docs/Contributor_Onboarding_Guide.md` | Cross-functional standards communication |
