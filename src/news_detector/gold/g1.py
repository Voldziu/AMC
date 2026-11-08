"""Draw the G1 gold-standard set: human articles of 2020, certainly pre-LLM.

Usage:
    uv run python -m news_detector.gold [--size 100] [--year 2020]

Candidates are the kept articles of ``settings.raw_dir(year)``. Each is cleaned
(``news_detector.gold.clean``), flagged, and dropped when it looks like advertising,
a legal notice, a list or a data table, or is too short or too long. The rest is
drawn round robin over domains in a seeded order, so no domain dominates. Texts go to
``settings.gold_private_dir`` (git-ignored); the review sheet with ids, URLs and
flags, but no text, goes to ``settings.gold_derived_dir``.
"""

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import BaseModel

from news_detector.config import settings
from news_detector.fetch.store import read_articles
from news_detector.gold.clean import prepare
from news_detector.models import Article
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

MIN_WORDS = 200
MAX_WORDS = 1500
EXCLUDED_DOMAINS = frozenset({"pap.pl"})  # old trial files mix in pages without markup


class GoldArticle(BaseModel):
    """An article of the gold standard, with its cleaned text."""

    gold_set: str
    article_id: str
    domain: str
    stratum: str
    url: str
    title: str | None
    pub_date: str | None
    pub_year: int | None
    n_words: int
    n_words_original: int
    text: str


def _order_key(article: Article) -> str:
    """Seeded, reproducible order within a domain."""
    return hashlib.md5(
        f"{settings.seed}:{article.article_id}".encode(), usedforsecurity=False
    ).hexdigest()


def _manual_exclusions() -> set[str]:
    """Ids of articles removed by hand after reading them (``config/g1_exclusions.csv``)."""
    path = settings.gold_exclusions_file
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as file:
        return {row["article_id"] for row in csv.DictReader(file)}


def select(
    year: int, size: int
) -> tuple[list[GoldArticle], Counter[str], dict[str, int]]:
    """Pick the articles of the set.

    Args:
        year: Publication year to draw from.
        size: Number of articles wanted.

    Returns:
        The selected articles, how many candidates each exclusion reason removed, and
        the number of eligible candidates per domain.
    """
    eligible: dict[str, list[GoldArticle]] = defaultdict(list)
    reasons: Counter[str] = Counter()
    excluded_by_hand = _manual_exclusions()
    for path in sorted(settings.raw_dir(year).glob("*.jsonl")):
        if path.stem in EXCLUDED_DOMAINS:
            continue
        for article in sorted(read_articles(path), key=_order_key):
            if article.article_id in excluded_by_hand:
                reasons["manual"] += 1
                continue
            if article.pub_year != year:
                reasons["wrong_year"] += 1
                continue
            prepared = prepare(article.text, article.title)
            if prepared.flags:
                for flag in prepared.flags:
                    reasons[flag] += 1
                continue
            if not MIN_WORDS <= prepared.n_words <= MAX_WORDS:
                reasons["length"] += 1
                continue
            eligible[article.domain].append(
                GoldArticle(
                    gold_set="G1",
                    article_id=article.article_id,
                    domain=article.domain,
                    stratum=article.stratum,
                    url=article.url,
                    title=article.title,
                    pub_date=article.pub_date,
                    pub_year=article.pub_year,
                    n_words=prepared.n_words,
                    n_words_original=article.n_words,
                    text=prepared.text,
                )
            )
    counts = {domain: len(items) for domain, items in eligible.items()}
    picked: list[GoldArticle] = []
    queues = {domain: list(items) for domain, items in sorted(eligible.items())}
    while len(picked) < size and any(queues.values()):
        for domain in sorted(queues):
            if queues[domain] and len(picked) < size:
                picked.append(queues[domain].pop(0))
    return picked, reasons, counts


def write(picked: list[GoldArticle], year: int) -> tuple[Path, Path]:
    """Write the texts and the review sheet.

    Args:
        picked: Selected articles.
        year: Publication year, used in the file names.

    Returns:
        Paths of the private JSONL file and the review CSV.
    """
    private = settings.gold_private_dir / f"g1_{year}.jsonl"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text(
        "".join(article.model_dump_json() + "\n" for article in picked),
        encoding="utf-8",
    )
    sheet = settings.gold_derived_dir / f"g1_{year}_review.csv"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    with sheet.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "article_id",
                "domain",
                "stratum",
                "pub_date",
                "n_words",
                "title",
                "url",
                "is_article",
                "note",
            ]
        )
        for article in picked:
            writer.writerow(
                [
                    article.article_id,
                    article.domain,
                    article.stratum,
                    article.pub_date,
                    article.n_words,
                    article.title,
                    article.url,
                    "",
                    "",
                ]
            )
    return private, sheet


def main() -> None:
    """Draw the set and report what was excluded."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--year", type=int, default=2020)
    args = parser.parse_args()
    picked, reasons, counts = select(args.year, args.size)
    private, sheet = write(picked, args.year)
    logger.info("Excluded candidates by reason: %s", dict(reasons))
    logger.info("Eligible per domain: %s", dict(sorted(counts.items())))
    logger.info(
        "Selected %d of %d wanted from %d domains: %s",
        len(picked),
        args.size,
        len({a.domain for a in picked}),
        dict(sorted(Counter(a.domain for a in picked).items())),
    )
    logger.info("Texts: %s | review sheet (no text): %s", private, sheet)


if __name__ == "__main__":
    main()
