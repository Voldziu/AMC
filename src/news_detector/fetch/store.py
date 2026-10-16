"""On-disk progress of one (year, domain) pair, written as the fetch goes.

Three files live in ``settings.raw_dir(year)``:

* ``<domain>.jsonl``  - kept articles, one line appended per article;
* ``<domain>.tried``  - every candidate URL already downloaded (kept or rejected),
  so a resumed run does not download rejected pages again;
* ``<domain>.done``   - written when the domain was worked through to the end.

A process killed at any moment loses at most the few downloads in flight.
"""

import json
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from news_detector.config import settings
from news_detector.models import Article
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)


class DomainStatus(StrEnum):
    """How far a (year, domain) pair got in earlier runs."""

    NEW = "new"
    IN_PROGRESS = "in_progress"  # interrupted before it was worked through
    INCOMPLETE = "incomplete"  # worked through, but found fewer than the quota
    COMPLETE = "complete"  # quota reached


def _complete_lines(path: Path, *, repair: bool) -> list[str]:
    """Read the non-empty lines of a file that is only ever appended to.

    A last line without a newline is a write cut short by a crash. It is dropped,
    and with ``repair`` also removed from the file so the next append cannot be
    glued onto it.
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    partial = lines.pop()  # "" when the file ends with a newline
    if partial:
        logger.warning("Dropping an unfinished last line of %s", path)
        if repair:
            _replace(path, "".join(f"{line}\n" for line in lines))
    return [line for line in lines if line.strip()]


def _replace(path: Path, text: str) -> None:
    """Write a file atomically (readers never see a half-written file)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_articles(path: Path, *, repair: bool = False) -> list[Article]:
    """Read the articles of a JSONL file, skipping unreadable lines.

    Args:
        path: JSONL file written by ``DomainStore``.
        repair: Also cut an unfinished last line out of the file.

    Returns:
        The valid articles in file order; empty when the file does not exist.
    """
    articles: list[Article] = []
    for line in _complete_lines(path, repair=repair):
        try:
            articles.append(Article.model_validate_json(line))
        except ValidationError:
            logger.warning("Skipping an invalid line in %s", path)
    return articles


class DomainStore:
    """Progress files of one domain in one publication year."""

    def __init__(self, year: int, domain: str) -> None:
        """Point at the files of a (year, domain) pair; nothing is created yet.

        Args:
            year: Publication year being collected.
            domain: Domain from the sampling frame.
        """
        directory = settings.raw_dir(year)
        self._directory = directory
        self._articles = directory / f"{domain}.jsonl"
        self._tried = directory / f"{domain}.tried"
        self._done = directory / f"{domain}.done"

    def status(self, quota: int) -> DomainStatus:
        """Classify the pair from what is on disk.

        Args:
            quota: Articles wanted per domain and year.

        Returns:
            ``COMPLETE`` once the quota is reached (judged by the articles on disk,
            so a raised quota makes a finished domain ``INCOMPLETE`` again).
        """
        if len(read_articles(self._articles)) >= quota:
            return DomainStatus.COMPLETE
        if self._done.exists():
            return DomainStatus.INCOMPLETE
        if self._articles.exists() or self._tried.exists():
            return DomainStatus.IN_PROGRESS
        return DomainStatus.NEW

    def start(self) -> tuple[list[Article], set[str]]:
        """Open the pair for work and load what earlier runs saved.

        Returns:
            The kept articles and the set of URLs that must not be downloaded again.
        """
        self._directory.mkdir(parents=True, exist_ok=True)
        self._done.unlink(missing_ok=True)
        articles = read_articles(self._articles, repair=True)
        tried = set(_complete_lines(self._tried, repair=True))
        return articles, tried | {article.url for article in articles}

    def add_article(self, article: Article) -> None:
        """Append a kept article to the JSONL file."""
        self._append(self._articles, article.model_dump_json())

    def add_tried(self, url: str) -> None:
        """Record that a candidate URL was downloaded."""
        self._append(self._tried, url)

    def finish(self, *, kept: int, tried: int, candidates: int) -> None:
        """Mark the pair as worked through.

        Args:
            kept: Articles on disk.
            tried: Candidate URLs downloaded over all runs.
            candidates: Candidates the index returned in the last run.
        """
        self._directory.mkdir(parents=True, exist_ok=True)
        info = {
            "kept": kept,
            "tried": tried,
            "candidates": candidates,
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        _replace(self._done, json.dumps(info) + "\n")

    @staticmethod
    def _append(path: Path, line: str) -> None:
        with path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")
