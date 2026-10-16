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

1. Put the domains (one per line) in `data/domains.txt`.
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
