from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

from src.logging_config import configure_logging
from src.utils import project_path, load_yaml, runtime_config, sha256_file, utc_now, write_csv


LOGGER = configure_logging(__name__)


def download_file(url: str, destination: Path, overwrite: bool = False, retries: int = 3) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        return {"status": "skipped_existing", "error": ""}

    partial = destination.with_suffix(destination.suffix + ".part")
    headers = {}
    if partial.exists():
        headers["Range"] = f"bytes={partial.stat().st_size}-"

    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=60, headers=headers) as response:
                response.raise_for_status()
                mode = "ab" if headers.get("Range") and response.status_code == 206 else "wb"
                with partial.open(mode) as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            partial.replace(destination)
            return {"status": "downloaded", "error": ""}
        except Exception as exc:
            LOGGER.warning("Download attempt %s failed for %s: %s", attempt, url, exc)
            time.sleep(2 * attempt)
    return {"status": "failed", "error": f"Failed after {retries} attempts"}


def run() -> list[dict]:
    data_sources = load_yaml(project_path("config", "data_sources.yaml"))["sources"]
    runtime = runtime_config()
    rows: list[dict] = []

    if not runtime.get("enable_raw_images", False):
        LOGGER.info("Raw microscopy image downloads are disabled by config.")
    if not runtime.get("enable_raw_signal_files", False):
        LOGGER.info("Raw electrophysiology signal downloads are disabled by config.")

    for key, source in data_sources.items():
        for file_cfg in source.get("files", []):
            local_path = project_path(source["local_raw_path"], file_cfg["local_name"])
            LOGGER.info("Downloading %s from %s", source["source_name"], file_cfg["url"])
            result = download_file(file_cfg["url"], local_path, overwrite=runtime.get("overwrite_existing", False))
            checksum = sha256_file(local_path) if local_path.exists() and result["status"] != "failed" else ""
            rows.append(
                {
                    "source_key": key,
                    "source_name": source["source_name"],
                    "source_dataset": source["dataset_accession_or_id"],
                    "url_or_path": file_cfg["url"],
                    "local_path": str(local_path.relative_to(project_path())),
                    "file_type": file_cfg.get("file_type", ""),
                    "file_size": local_path.stat().st_size if local_path.exists() else 0,
                    "download_status": result["status"],
                    "timestamp": utc_now(),
                    "checksum_sha256": checksum,
                    "error": result["error"],
                    "manual_download_instruction": "" if result["status"] != "failed" else f"Download manually from {file_cfg['url']} to {local_path}",
                }
            )

    write_csv(rows, project_path("data", "manifests", "download_manifest.csv"))
    failures = [row for row in rows if row["download_status"] == "failed"]
    if failures:
        report = project_path("data", "outputs", "download_failure_report.md")
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "# Download Failure Report\n\n"
            + "\n".join(f"- {row['source_name']}: {row['manual_download_instruction']} ({row['error']})" for row in failures)
            + "\n",
            encoding="utf-8",
        )
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    run()
