"""Copy only the ``.jsonl`` files from ``data/raw_private`` to ``data/clean``.

Usage:
    uv run python -m news_detector.scripts.materilize_jsons

Bookkeeping files (``.done``, ``.tried``) are skipped. The ``<year>/<domain>.jsonl``
layout is preserved; existing files in the target are overwritten.
"""

import shutil

from news_detector.config import settings
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

JSONL_SUFFIX = ".jsonl"


def main() -> None:
    """Copy every ``raw_private/<year>/*.jsonl`` into ``clean/<year>/``."""
    source = settings.data_dir / "raw_private"
    target = settings.clean_dir
    copied = 0
    for path in sorted(source.glob(f"*/*{JSONL_SUFFIX}")):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied += 1
    logger.info("Copied %d files from %s to %s", copied, source, target)


if __name__ == "__main__":
    main()
