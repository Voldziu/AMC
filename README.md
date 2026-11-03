# AMC – news detector

Fetches Polish news articles from Common Crawl, year by year.

## Setup

We use [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # optional, every value has a default
```

## Build the domain list

`fetch` reads `data/frame/domains.csv`, which you generate first:

1. Put the domains (one per line) in `data/domains.txt`. Lines starting with
   `#` are treated as comments.
2. Run the scripts:

```bash
make frame     # downloads the Tranco list
make domains   # builds data/frame/domains.csv
```

## Run

Which crawl each year is taken from: `config/crawls.yaml`.

```bash
make fetch     # all years
make retry     # also continue domains that ended below the quota
```

One domain or one year (for a test):

```bash
uv run python -m news_detector.fetch --only tvn24.pl --year 2022
```

Results go to `data/raw_private/<year>/` (article texts, git-ignored) and
`data/derived/meta.csv`. An interrupted run resumes where it stopped.

`make` lists all shortcuts; `make check` runs ruff and mypy.

## Build the training datasets

The dataset pipeline reads every `data/clean/<year>/*.jsonl` file and writes `data/processed/train.csv`, `data/processed/dev.csv`, and `data/processed/test.csv`.
The default split is 80/10/10 with seed 42 and is stratified by publication year, domain, and source stratum.
Rows that share an article ID or text hash always stay in the same split.

The output keeps all source fields and adds `label`.
Articles published in 2020-2022 receive label `0`; articles from 2023-2025 have an empty label for later annotation.

```bash
make pipeline
```

The command is deterministic and replaces the three generated CSV files.
Custom paths, ratios, and seed are available through the module CLI:

```bash
uv run python -m news_detector.pipeline --help
```

## Run the zero-shot detectors

Binoculars and Fast-DetectGPT score every text with a pair of Polish Bielik models.
They need no training data.
Thresholds are calibrated on the 2020-2022 articles, which we assume are human-written.
The step-by-step guide, including running the larger model on a GPU in Google Colab, is in [docs/detektory.md](docs/detektory.md) (in Polish).

```bash
make detect          # PRESET=bielik-1.5b by default -> data/detect/bielik-1.5b.csv
make detect-report   # -> data/detect/reports/bielik-1.5b/
make smigiel         # labelled Polish sanity check (PolEval 2025 Śmigiel)
```

Scoring needs the optional `detect` dependency group (torch, transformers, peft); see the guide.

`detect score` also runs Pangram's EditLens classifier (Llama-3.2-3B + LoRA adapter, English-only, CC BY-NC-SA) and writes `data/detect/pangram.csv`, independent of the preset.
Both models are gated on Hugging Face: accept their licences first.
Use `--no-pangram` to skip it.

The comparison of the detectors and models (Śmigiel check, placebo test, per-year and per-domain results, power, threshold-free comparison, Pangram analyses, candidates for manual review) is in `src/notebooks/detect-compare.ipynb`.
It only reads the files in `data/detect/`, so it needs no GPU.
