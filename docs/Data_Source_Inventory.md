# Data Source Inventory

This project uses only public biomedical research data and excludes PHI, private clinical records, and protected patient-level records.

| Source | Dataset | Data used | Default exclusion | Why selected |
|---|---|---|---|---|
| NCBI GEO | GSE2034 | GEO Series Matrix metadata and processed expression values | Raw submitter files | Manageable public gene expression matrix with many samples/features |
| Broad Cell Painting Gallery | cpg0000 JUMP pilot plate BR00116991 | Well-level morphology profile CSV | Raw microscopy images | Real microscopy-derived morphology features without image storage burden |
| OpenNeuro | ds004504 | BIDS dataset metadata and participant files | Raw EEG signal files | Public electrophysiology dataset organized under BIDS conventions |
