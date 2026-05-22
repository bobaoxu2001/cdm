from __future__ import annotations

import pandas as pd

from src.utils import project_path


def markdown_table(path, rows=5) -> str:
    if not path.exists():
        return "Not generated yet."
    frame = pd.read_csv(path).head(rows)
    return frame.to_markdown(index=False)


def run() -> None:
    outputs = project_path("data", "outputs")
    report = [
        "# Harmonization Run Report",
        "",
        "## Source Profile Sample",
        markdown_table(outputs / "source_profile_summary.csv"),
        "",
        "## Mapping Catalog Sample",
        markdown_table(outputs / "source_to_cdm_mapping_catalog.csv"),
        "",
        "## Terminology Alignment Sample",
        markdown_table(outputs / "terminology_alignment_report.csv"),
        "",
        "## QA Results Sample",
        markdown_table(outputs / "qa_results.csv"),
    ]
    (outputs / "harmonization_run_report.md").write_text("\n\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
