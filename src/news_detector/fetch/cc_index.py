"""Finding candidate article captures in the Common Crawl columnar (Parquet) index.

The index is published as ~300 static Parquet files on the CDN. They are sorted by
URL, so a query filtered by TLD and registered domain only downloads the small
parts of a few files that can match. All domains are resolved in a single query.
"""

import gzip
import time
from collections.abc import Iterable
from contextlib import closing

import duckdb
import requests
from pydantic import BaseModel, TypeAdapter, ValidationError

from news_detector.config import settings
from news_detector.fetch.http import get
from news_detector.models import IndexRecord
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

# URLs that are certainly not articles (categories, tags, feeds, files); RE2 syntax.
EXCLUDE_PATTERN = (
    r"/(tag|tagi|temat|tematy|kategoria|category|autor|author|page|strona|search|szukaj|"
    r"wp-json|feed|rss|login|kontakt|regulamin|polityka)(/|$)|[?#]|\.(jpg|png|pdf|xml|js|css)$"
)

PATHS_URL = "{host}/crawl-data/{crawl}/cc-index-table.paths.gz"
SUBSET_MARKER = "subset=warc/"

QUERY = """
WITH wanted AS (SELECT unnest($domains::VARCHAR[]) AS domain),
hits AS (
    SELECT
        w.domain,
        p.url,
        p.warc_filename AS filename,
        p.warc_record_offset AS "offset",
        p.warc_record_length AS length,
        strftime(p.fetch_time, '%Y%m%d%H%M%S') AS timestamp,
        p.content_languages AS languages,
        p.fetch_time
    FROM read_parquet($files) AS p
    JOIN wanted AS w
        ON p.url_host_name = w.domain OR ends_with(p.url_host_name, '.' || w.domain)
    WHERE p.url_host_tld IN (SELECT unnest($tlds::VARCHAR[]))
        AND p.url_host_registered_domain IN (SELECT unnest($registered::VARCHAR[]))
        AND p.fetch_status = 200
        AND p.content_mime_detected = 'text/html'
        AND starts_with(p.content_languages, $language)
        AND length(p.url_path) >= $min_path
        AND NOT regexp_matches(p.url, $exclude, 'i')
),
latest AS (
    SELECT * FROM hits
    QUALIFY row_number() OVER (PARTITION BY domain, url ORDER BY fetch_time DESC) = 1
)
SELECT domain, url, filename, "offset", length, timestamp, languages
FROM latest
QUALIFY row_number() OVER (PARTITION BY domain ORDER BY md5(url || $seed)) <= $limit
ORDER BY domain, md5(url || $seed)
"""


class ColumnarIndexError(RuntimeError):
    """The Parquet index could not be listed or queried."""


class ParquetFile(BaseModel):
    """A Parquet file of the index with the range of TLDs it contains."""

    url: str
    tld_min: str | None
    tld_max: str | None

    def may_contain(self, tld: str) -> bool:
        """Tell whether the file can hold rows of a TLD (unknown range: yes)."""
        if self.tld_min is None or self.tld_max is None:
            return True
        return self.tld_min <= tld <= self.tld_max


_FILES = TypeAdapter(list[ParquetFile])


def tld_of(domain: str) -> str:
    """Return the last label of a domain name."""
    return domain.rsplit(".", 1)[-1]


def registered_candidates(domain: str) -> set[str]:
    """List values the ``url_host_registered_domain`` column may have for a domain.

    A public-suffix list would be exact; the last two and three labels cover
    ``example.pl``, ``blog.example.pl`` and ``example.com.pl``.

    Args:
        domain: Domain from the frame, possibly a subdomain.

    Returns:
        The domain itself and its two- and three-label suffixes.
    """
    labels = domain.split(".")
    return {".".join(labels[-n:]) for n in (2, 3) if len(labels) >= n} | {domain}


def _connect() -> duckdb.DuckDBPyConnection:
    """Open DuckDB configured for polite, retrying HTTPS reads."""
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute(f"SET threads = {settings.index_threads}")
    con.execute(f"SET http_retries = {settings.max_retries}")
    con.execute(
        f"SET http_retry_wait_ms = {int(settings.retry_backoff_seconds * 1000)}"
    )
    con.execute(f"SET http_timeout = {int(settings.request_timeout_seconds * 1000)}")
    con.execute(
        "CREATE SECRET user_agent (TYPE http, "
        "EXTRA_HTTP_HEADERS MAP {'User-Agent': $ua})",
        {"ua": settings.user_agent},
    )
    return con


def _list_parquet_urls(session: requests.Session) -> list[str]:
    response = get(
        session,
        PATHS_URL.format(host=settings.data_host, crawl=settings.crawl_id),
    )
    if response is None:
        raise ColumnarIndexError(f"Cannot list index files of {settings.crawl_id}")
    paths = gzip.decompress(response.content).decode().split()
    return [f"{settings.data_host}/{p}" for p in paths if SUBSET_MARKER in p]


def _read_tld_ranges(
    con: duckdb.DuckDBPyConnection, urls: list[str]
) -> list[ParquetFile]:
    """Read only the Parquet footers (min/max of ``url_host_tld``)."""
    rows = con.execute(
        """
        SELECT file_name, min(stats_min_value), max(stats_max_value)
        FROM parquet_metadata($files)
        WHERE path_in_schema = 'url_host_tld'
        GROUP BY file_name
        """,
        {"files": urls},
    ).fetchall()
    return [
        ParquetFile(url=name, tld_min=low, tld_max=high) for name, low, high in rows
    ]


def _load_files(
    con: duckdb.DuckDBPyConnection, session: requests.Session
) -> list[ParquetFile]:
    """Return the file layout of the crawl, cached on disk after the first run."""
    cache = settings.cache_dir / f"parquet_layout_{settings.crawl_id}.json"
    if cache.exists():
        try:
            return _FILES.validate_json(cache.read_bytes())
        except ValidationError:
            logger.warning("Ignoring corrupt cache %s", cache)
    logger.info("Reading the layout of the Parquet index (once per crawl, ~20 s)...")
    files = _read_tld_ranges(con, _list_parquet_urls(session))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(_FILES.dump_json(files))
    return files


def find_candidates(
    session: requests.Session, domains: Iterable[str]
) -> dict[str, list[IndexRecord]]:
    """Sample article-like captures for every domain with a single index query.

    Args:
        session: Session created by ``news_detector.fetch.http.build_session``.
        domains: Lower-case domains (subdomains included in the match).

    Returns:
        For each domain, up to ``settings.max_fetch_per_domain`` unique captures
        in a seeded random order. Domains without captures map to an empty list.

    Raises:
        ColumnarIndexError: When the index cannot be read.
    """
    wanted = sorted(set(domains))
    result: dict[str, list[IndexRecord]] = {domain: [] for domain in wanted}
    if not wanted:
        return result

    tlds = {tld_of(domain) for domain in wanted}
    registered = set().union(*(registered_candidates(domain) for domain in wanted))
    try:
        with closing(_connect()) as con:
            layout = _load_files(con, session)
            files = [f.url for f in layout if any(f.may_contain(t) for t in tlds)]
            logger.info(
                "Querying %d of %d Parquet files for %d domains (TLDs: %s)...",
                len(files),
                len(layout),
                len(wanted),
                ", ".join(sorted(tlds)),
            )
            started = time.monotonic()
            rows = con.execute(
                QUERY,
                {
                    "domains": wanted,
                    "files": files,
                    "tlds": sorted(tlds),
                    "registered": sorted(registered),
                    "language": settings.index_language,
                    "min_path": settings.min_url_path_length,
                    "exclude": EXCLUDE_PATTERN,
                    "seed": str(settings.seed),
                    "limit": settings.max_fetch_per_domain,
                },
            ).fetchall()
    except duckdb.Error as exc:
        raise ColumnarIndexError(f"Index query failed: {exc}") from exc

    for domain, url, filename, offset, length, timestamp, languages in rows:
        result[domain].append(
            IndexRecord(
                url=url,
                filename=filename,
                offset=offset,
                length=length,
                timestamp=timestamp,
                languages=languages,
            )
        )
    logger.info(
        "Index query done in %.1fs: %d candidates for %d/%d domains",
        time.monotonic() - started,
        len(rows),
        sum(1 for records in result.values() if records),
        len(wanted),
    )
    return result
