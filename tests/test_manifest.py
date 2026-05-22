from pathlib import Path

from src.build_data_manifest import infer_source
from src.download_public_data import download_file
from src.utils import sha256_file


def test_manifest_checksum(tmp_path):
    path = tmp_path / "example.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    assert len(sha256_file(path)) == 64


def test_infer_source_geo():
    source_system, dataset = infer_source(Path("data/raw/geo/GSE2034_series_matrix.txt.gz"))
    assert source_system == "NCBI GEO"
    assert dataset == "GSE2034"


def test_no_fake_data_fallback_on_failed_download(monkeypatch, tmp_path):
    def fail_get(*args, **kwargs):
        raise RuntimeError("network blocked")

    monkeypatch.setattr("src.download_public_data.requests.get", fail_get)
    result = download_file("https://example.invalid/data.csv", tmp_path / "data.csv", retries=1)
    assert result["status"] == "failed"
    assert not (tmp_path / "data.csv").exists()
