SELECT source_system, COUNT(*) AS profiled_files, SUM(row_count) AS profiled_rows
FROM read_csv_auto('data/outputs/source_profile_summary.csv')
GROUP BY source_system;

SELECT source_system, source_file, column_name, missingness_pct, distinct_value_count, warnings
FROM read_csv_auto('data/outputs/source_column_profile.csv')
WHERE missingness_pct > 0.5 OR warnings <> ''
ORDER BY missingness_pct DESC;
