PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

download:
	$(PYTHON) -m src.download_public_data

manifest:
	$(PYTHON) -m src.build_data_manifest

profile:
	$(PYTHON) -m src.profile_source_data

mapping:
	$(PYTHON) -m src.build_mapping_catalog

transform:
	$(PYTHON) -m src.apply_cdm_mapping

terminology:
	$(PYTHON) -m src.terminology_matcher

qa:
	$(PYTHON) -m src.run_qa_checks

validate:
	$(PYTHON) -m src.validate_cdm_schema

steward-queue:
	$(PYTHON) -m src.generate_steward_review_queue

reports:
	$(PYTHON) -m src.generate_reports

test:
	$(PYTHON) -m pytest

all-sample: download manifest profile mapping transform terminology qa validate steward-queue reports

all-full:
	@echo "Set config/runtime.yaml mode: full and enable_full_download: true after reviewing large file warnings."
	$(PYTHON) -m src.download_public_data
	$(PYTHON) -m src.build_data_manifest
	$(PYTHON) -m src.profile_source_data
	$(PYTHON) -m src.build_mapping_catalog
	$(PYTHON) -m src.apply_cdm_mapping
	$(PYTHON) -m src.terminology_matcher
	$(PYTHON) -m src.run_qa_checks
	$(PYTHON) -m src.validate_cdm_schema
	$(PYTHON) -m src.generate_steward_review_queue
	$(PYTHON) -m src.generate_reports
