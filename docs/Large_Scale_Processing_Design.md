# Large-Scale Processing Design

The platform is designed for real public biomedical files that can be larger than laptop memory.

## Chunked Processing

CSV, TSV, and gzip files are read with configurable chunks. Sample mode limits rows for fast demonstrations; full mode removes the row cap after the user reviews large-file warnings.

## Memory-Safe Profiling

Profiling computes row/column counts, inferred types, missingness, distinct counts, top values, numeric ranges, identifiers, foreign key candidates, and warnings without requiring raw image or signal loading.

## Parquet Support

Parquet is supported for interim/full-mode workflows where columnar reads are more efficient than repeated CSV parsing.

## Resumable Downloads and Caching

Downloads skip existing files unless overwrite is enabled. Partial files use `.part` staging and are retried before a failure report is written.

## Manifest and Lineage Strategy

Every discovered raw, interim, CDM, or output file is tracked with checksum, size, stage, row/column counts where practical, source system, source dataset, script, and notes. CDM rows preserve source lineage columns.

## Raw Images and Signals

Raw microscopy images and raw EEG signal files are excluded by default because they can be extremely large and are not necessary to demonstrate metadata harmonization, mapping design, terminology alignment, and QA acceptance criteria.
