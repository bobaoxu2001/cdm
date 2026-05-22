from __future__ import annotations

import math
import re
from difflib import SequenceMatcher

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils import load_yaml, project_path, write_csv

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - fallback keeps the project runnable without optional dependency.
    fuzz = None


def normalize(text: str) -> str:
    text = re.sub(r"^(Metadata_|Cells_|Cytoplasm_|Nuclei_)", "", str(text))
    return text.replace("_", " ").replace("-", " ").lower().strip()


def vocabulary_terms() -> list[dict]:
    vocab = load_yaml(project_path("config", "controlled_vocabularies.yaml"))
    rows = []
    for category, terms in vocab.items():
        for term in terms:
            rows.append({"term": term, "category": category})
    return rows


def rapid_score(a: str, b: str) -> float:
    if fuzz:
        return float(fuzz.token_sort_ratio(a, b))
    return SequenceMatcher(None, a, b).ratio() * 100


def tfidf_scores(source_value: str, terms: list[str]) -> list[float]:
    if not source_value or not terms:
        return [0.0 for _ in terms]
    vectorizer = TfidfVectorizer().fit([source_value] + terms)
    matrix = vectorizer.transform([source_value] + terms)
    return cosine_similarity(matrix[0:1], matrix[1:]).ravel().tolist()


def best_match(source_value: str) -> dict:
    terms = vocabulary_terms()
    norm = normalize(source_value)
    term_names = [normalize(row["term"]) for row in terms]
    tfidf = tfidf_scores(norm, term_names)
    scored = []
    for row, term_norm, cosine in zip(terms, term_names, tfidf):
        fuzzy = rapid_score(norm, term_norm)
        score = max(fuzzy, cosine * 100)
        method = "rapidfuzz_token_sort" if fuzzy >= cosine * 100 else "tfidf_cosine"
        scored.append((score, method, row))
    score, method, row = max(scored, key=lambda x: x[0]) if scored else (0, "none", {"term": "", "category": ""})
    rules = load_yaml(project_path("config", "terminology_mapping_rules.yaml"))["matching"]
    status = "auto_mapped" if score >= rules["auto_map_threshold"] else "review_required" if score >= rules["review_threshold"] else "terminology_gap"
    return {
        "recommended_standard_term": row["term"],
        "standard_term_category": row["category"],
        "match_score": round(float(score), 2) if not math.isnan(score) else 0,
        "match_method": method,
        "status": status,
        "remediation_recommendation": "Accept mapping" if status == "auto_mapped" else "Review with data steward" if status == "review_required" else "Add term or synonym to controlled vocabulary",
    }


def run() -> list[dict]:
    mapping_path = project_path("data", "outputs", "source_to_cdm_mapping_catalog.csv")
    if not mapping_path.exists():
        from src.build_mapping_catalog import build_catalog

        build_catalog()
    catalog = pd.read_csv(mapping_path)
    rows: list[dict] = []
    for _, row in catalog.iterrows():
        value = str(row.get("source_field", ""))
        match = best_match(value)
        rows.append(
            {
                "source_system": row.get("source_system", ""),
                "source_dataset": row.get("source_dataset", ""),
                "source_field": row.get("source_field", ""),
                "source_value": value,
                **match,
            }
        )
    write_csv(rows, project_path("data", "outputs", "terminology_alignment_report.csv"))
    summary = pd.DataFrame(rows).groupby(["standard_term_category", "status"], dropna=False).size().reset_index(name="field_count")
    summary.to_csv(project_path("data", "outputs", "terminology_gap_summary.csv"), index=False)
    write_doc(rows, summary)
    return rows


def write_doc(rows: list[dict], summary: pd.DataFrame) -> None:
    lines = [
        "# Terminology Alignment and Gap Analysis",
        "",
        "This project uses simplified UMLS/SNOMED/LOINC-style controlled vocabulary examples. It does not claim licensed vocabulary integration.",
        "",
        "## Summary",
    ]
    for _, row in summary.iterrows():
        lines.append(f"- {row['standard_term_category']} / {row['status']}: {row['field_count']} source fields")
    lines.extend(["", "## Remediation Workflow", "", "1. Auto-mapped terms can be accepted during steward review.", "2. Review-required terms need contributor or domain expert confirmation.", "3. Terminology gaps become vocabulary backlog items with proposed synonyms and source examples."])
    project_path("docs", "Terminology_Alignment_and_Gap_Analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
