.PHONY: help sync frame domains fetch retry clean-data pipeline detect detect-report smigiel test check

# Model pair for the detectors: bielik-1.5b (Mac) or bielik-4.5b (GPU)
PRESET ?= bielik-1.5b

help:  ## show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-8s %s\n", $$1, $$2}'

sync:  ## install dependencies
	uv sync

frame:  ## download the Tranco list -> data/frame/tranco_pl_all.csv
	uv run python -m news_detector.scripts.build_frame

domains:  ## data/domains.txt + Tranco -> data/frame/domains.csv
	uv run python -m news_detector.scripts.build_csv_domains

fetch:  ## fetch articles for every year in config/crawls.yaml
	uv run python -m news_detector.fetch

retry:  ## also continue domains that ended below the quota
	uv run python -m news_detector.fetch --retry-incomplete

clean-data:  ## copy only *.jsonl from data/raw_private -> data/clean
	uv run python -m news_detector.scripts.materilize_jsons

pipeline:  ## build stratified train/dev/test CSV files in data/processed
	uv run python -m news_detector.pipeline

detect:  ## Binoculars + Fast-DetectGPT scores -> data/detect/$(PRESET).csv
	uv run --group detect python -m news_detector.detect score --preset $(PRESET)

detect-report:  ## thresholds from 2020-2022, flag rates by year and domain
	uv run python -m news_detector.detect report --scores data/detect/$(PRESET).csv

smigiel:  ## sanity check on labelled Polish texts (PolEval 2025 Śmigiel)
	uv run python -m news_detector.detect smigiel-sample
	uv run --group detect python -m news_detector.detect score --preset $(PRESET) \
		--input data/external/smigiel/sample.csv --output data/detect/smigiel-$(PRESET).csv
	uv run python -m news_detector.detect smigiel-eval --scores data/detect/smigiel-$(PRESET).csv

test:  ## run unit and end-to-end tests
	uv run python -m unittest discover -s tests

check:  ## ruff + mypy
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
