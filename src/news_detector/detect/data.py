"""Read texts for the detectors and key them by content.

Scores depend only on the text, so every text is keyed by its SHA-1. Duplicate
articles are scored once and any CSV with a ``text`` column can be scored.
"""

import csv
import hashlib
from collections.abc import Iterable
from pathlib import Path

from news_detector.pipeline.build import SPLIT_NAMES

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_INPUTS = tuple(PROCESSED_DIR / f"{split}.csv" for split in SPLIT_NAMES)
SCORES_DIR = PROJECT_ROOT / "data" / "detect"

# Article bodies are longer than the csv module's default 128 KiB field limit
_FIELD_SIZE_LIMIT = 2**31 - 1


class DetectError(ValueError):
    """Detector input, configuration or output cannot be used safely."""


def text_key(text: str) -> str:
    """Return the key that links a text to its scores."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_texts(paths: Iterable[Path]) -> dict[str, str]:
    """Read the ``text`` column of CSV files, without empty texts or duplicates.

    Args:
        paths: CSV files with a header that contains ``text``.

    Returns:
        Text key -> text, in the order the texts first appear.

    Raises:
        DetectError: When a file cannot be read or has no ``text`` column.
    """
    csv.field_size_limit(_FIELD_SIZE_LIMIT)
    texts: dict[str, str] = {}
    for path in paths:
        try:
            handle = path.open(encoding="utf-8", newline="")
        except OSError as exc:
            raise DetectError(f"Cannot read {path}: {exc}") from exc
        with handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or "text" not in reader.fieldnames:
                raise DetectError(f"{path}: expected a CSV with a 'text' column")
            for row in reader:
                text = row["text"]
                if text and text.strip():
                    texts.setdefault(text_key(text), text)
    return texts
