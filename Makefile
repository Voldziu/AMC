.PHONY: help sync frame domains fetch retry clean-data check

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

check:  ## ruff + mypy
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
