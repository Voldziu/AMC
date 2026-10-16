"""Logging setup. Use ``logger = get_logger(__name__)`` in every module."""

import logging

from tqdm import tqdm

from news_detector.config import settings

ROOT_NAME = "news_detector"


class _TqdmHandler(logging.StreamHandler):  # type: ignore[type-arg]  # generic only in stubs
    """Write records through ``tqdm.write`` so progress bars stay intact."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            tqdm.write(self.format(record), file=self.stream)
        except Exception:
            self.handleError(record)


def _configure_root() -> None:
    root = logging.getLogger(ROOT_NAME)
    if root.handlers:
        return
    handler = _TqdmHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(settings.log_level)
    root.propagate = False


def get_logger(name: str = ROOT_NAME) -> logging.Logger:
    """Return a logger configured once for the whole project.

    Args:
        name: Logger name, normally ``__name__``.

    Returns:
        A logger under the ``news_detector`` hierarchy, writing to the console
        at ``settings.log_level``.
    """
    _configure_root()
    return logging.getLogger(name)
