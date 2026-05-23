-- QA status rollup: count checks by status and severity
SELECT status, severity, COUNT(*) AS check_count
FROM read_csv_auto('data/outputs/qa_results.csv')
GROUP BY status, severity
ORDER BY severity, status;

-- Failing and warning checks with remediation guidance
SELECT qa_rule_id, cdm_table, field_name, pass_rate, status, remediation_guidance
FROM read_csv_auto('data/outputs/qa_results.csv')
WHERE status <> 'pass'
ORDER BY severity, pass_rate;

-- CDM table row counts across all core tables
SELECT 'cdm_data_source'        AS cdm_table, COUNT(*) AS row_count FROM read_csv_auto('data/cdm/cdm_data_source.csv')
UNION ALL SELECT 'cdm_study',              COUNT(*) FROM read_csv_auto('data/cdm/cdm_study.csv')
UNION ALL SELECT 'cdm_subject',            COUNT(*) FROM read_csv_auto('data/cdm/cdm_subject.csv')
UNION ALL SELECT 'cdm_sample',             COUNT(*) FROM read_csv_auto('data/cdm/cdm_sample.csv')
UNION ALL SELECT 'cdm_assay',              COUNT(*) FROM read_csv_auto('data/cdm/cdm_assay.csv')
UNION ALL SELECT 'cdm_measurement',        COUNT(*) FROM read_csv_auto('data/cdm/cdm_measurement.csv')
UNION ALL SELECT 'cdm_morphology_profile', COUNT(*) FROM read_csv_auto('data/cdm/cdm_morphology_profile.csv')
UNION ALL SELECT 'cdm_clinical_observation', COUNT(*) FROM read_csv_auto('data/cdm/cdm_clinical_observation.csv')
UNION ALL SELECT 'cdm_terminology_concept', COUNT(*) FROM read_csv_auto('data/cdm/cdm_terminology_concept.csv')
UNION ALL SELECT 'cdm_lineage',            COUNT(*) FROM read_csv_auto('data/cdm/cdm_lineage.csv')
ORDER BY row_count DESC;

-- Assay type distribution
SELECT assay_type, COUNT(*) AS assay_count
FROM read_csv_auto('data/cdm/cdm_assay.csv')
GROUP BY assay_type
ORDER BY assay_count DESC;

-- Clinical observations by type with summary statistics
SELECT
    observation_type,
    observation_name,
    COUNT(*) AS subject_count,
    ROUND(AVG(observation_value_numeric), 2) AS mean_value,
    MIN(observation_value_numeric) AS min_value,
    MAX(observation_value_numeric) AS max_value
FROM read_csv_auto('data/cdm/cdm_clinical_observation.csv')
GROUP BY observation_type, observation_name
ORDER BY observation_type, observation_name;

-- Gender / group distribution in clinical observations
SELECT observation_type, observation_value_text, COUNT(*) AS n
FROM read_csv_auto('data/cdm/cdm_clinical_observation.csv')
WHERE observation_value_text <> ''
GROUP BY observation_type, observation_value_text
ORDER BY observation_type, n DESC;

-- Terminology alignment: count by match status
SELECT status, COUNT(*) AS field_count
FROM read_csv_auto('data/outputs/terminology_alignment_report.csv')
GROUP BY status
ORDER BY field_count DESC;

-- Mapping coverage: mapped vs unmapped source fields
SELECT mapping_status, COUNT(*) AS field_count
FROM read_csv_auto('data/outputs/source_to_cdm_mapping_catalog.csv')
GROUP BY mapping_status
ORDER BY field_count DESC;

-- Source field lineage: which source files contributed most CDM records
SELECT source_system, COUNT(*) AS lineage_records
FROM read_csv_auto('data/cdm/cdm_lineage.csv')
GROUP BY source_system
ORDER BY lineage_records DESC;
