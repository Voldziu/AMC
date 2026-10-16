"""Build ``domains.csv`` (the sampling frame) from a plain-text list of domains.

Usage:
    uv run python -m news_detector.scripts.build_csv_domains

Domains found in the Tranco table keep their stratum and rank; all others go
to stratum ``S3``. Rows already present in ``domains.csv`` are preserved.
"""

import csv
from pathlib import Path

from pydantic import BaseModel

from news_detector.config import settings
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

OTHER_STRATUM = "S3"
OTHER_NOTE = "other"


class TrancoEntry(BaseModel):
    """Rank and stratum of a domain in the Tranco table."""

    rank: str
    stratum: str


class DomainRow(BaseModel):
    """One row of the sampling frame."""

    domain: str
    stratum: str
    rank_tranco: str


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def load_domains(path: Path) -> list[str]:
    """Read unique, lower-cased domains from a text file, keeping their order.

    Args:
        path: Text file with one domain per line.

    Returns:
        Domains without blank lines and duplicates.
    """
    with path.open(encoding="utf-8-sig") as file:
        domains = (_normalize(line) for line in file)
        return list(dict.fromkeys(domain for domain in domains if domain))


def load_tranco(path: Path) -> dict[str, TrancoEntry]:
    """Read the Tranco table into a lookup by domain.

    Args:
        path: CSV with ``domain``, ``rank`` and ``stratum`` columns.

    Returns:
        Mapping from lower-cased domain to its rank and stratum.
    """
    tranco: dict[str, TrancoEntry] = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            domain = _normalize(row.get("domain"))
            if domain:
                tranco[domain] = TrancoEntry(
                    rank=(row.get("rank") or "").strip(),
                    stratum=(row.get("stratum") or "").strip(),
                )
    return tranco


def load_existing(path: Path) -> dict[str, DomainRow]:
    """Read the current frame, if it exists.

    Args:
        path: Path of ``domains.csv``.

    Returns:
        Mapping from domain to its row; empty when the file does not exist.
    """
    existing: dict[str, DomainRow] = {}
    if not path.exists():
        return existing
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            domain = _normalize(row.get("domain"))
            if domain:
                existing[domain] = DomainRow(
                    domain=domain,
                    stratum=row.get("stratum") or "",
                    rank_tranco=row.get("rank_tranco") or "",
                    source_note=row.get("source_note") or "",
                )
    return existing


def build_row(domain: str, tranco: dict[str, TrancoEntry]) -> DomainRow:
    """Create a frame row for a domain.

    Args:
        domain: Lower-cased domain name.
        tranco: Lookup produced by ``load_tranco``.

    Returns:
        A row with Tranco data, or stratum ``S3`` when the domain has none.
    """
    entry = tranco.get(domain)
    if entry is not None and entry.stratum and entry.rank:
        return DomainRow(
            domain=domain,
            stratum=entry.stratum,
            rank_tranco=entry.rank,
            source_note=f"tranco review_{entry.stratum}",
        )
    return DomainRow(
        domain=domain,
        stratum=OTHER_STRATUM,
        rank_tranco="",
        source_note=OTHER_NOTE,
    )


def write_frame(path: Path, rows: list[DomainRow]) -> None:
    """Write the frame as CSV, creating the parent directory if needed.

    Args:
        path: Output path of ``domains.csv``.
        rows: Rows to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(DomainRow.model_fields))
        writer.writeheader()
        writer.writerows(row.model_dump() for row in rows)


def main() -> None:
    """Merge the domain list into ``domains.csv``."""
    domains = load_domains(settings.domain_list_txt)
    tranco = load_tranco(settings.tranco_csv)
    frame = load_existing(settings.domains_csv)

    for domain in domains:
        frame[domain] = build_row(domain, tranco)

    write_frame(settings.domains_csv, list(frame.values()))
    logger.info(
        "Saved %s: %d rows (%d from list)",
        settings.domains_csv,
        len(frame),
        len(domains),
    )


if __name__ == "__main__":
    main()
