SELECT status, severity, COUNT(*) AS check_count
FROM read_csv_auto('data/outputs/qa_results.csv')
GROUP BY status, severity
ORDER BY severity, status;

SELECT qa_rule_id, cdm_table, field_name, pass_rate, status, remediation_guidance
FROM read_csv_auto('data/outputs/qa_results.csv')
WHERE status <> 'pass'
ORDER BY severity, pass_rate;
