"""Project settings loaded from environment variables and the ``.env`` file."""

from functools import cached_property
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import (
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CrawlId = Annotated[str, StringConstraints(pattern=r"^CC-MAIN-\d{4}-\d{2}$")]
_CRAWL_MAP = TypeAdapter(dict[Annotated[int, Field(ge=1990, le=2100)], CrawlId])


class CrawlMapError(ValueError):
    """The year -> crawl YAML file is missing or invalid."""


def load_crawl_map(path: Path) -> dict[int, str]:
    """Read the publication year -> crawl mapping from a YAML file.

    Args:
        path: YAML file with lines such as ``2020: CC-MAIN-2020-50``.

    Returns:
        The mapping ordered by year, oldest first.

    Raises:
        CrawlMapError: When the file is missing, empty or malformed.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CrawlMapError(f"Cannot read crawl map {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CrawlMapError(f"Invalid YAML in {path}: {exc}") from exc
    if not raw:
        raise CrawlMapError(f"Crawl map {path} is empty")
    try:
        mapping = _CRAWL_MAP.validate_python(raw)
    except ValidationError as exc:
        raise CrawlMapError(f"Invalid crawl map {path}: {exc}") from exc
    return dict(sorted(mapping.items()))


class Settings(BaseSettings):
    """Application settings.

    Every value has a default and can be overridden by an environment variable
    of the same name (case-insensitive) or by an entry in ``.env``.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Common Crawl
    data_host: str = "https://data.commoncrawl.org"
    # Primary language of a capture in the index (CLD2, ISO 639-3)
    index_language: str = "pol"

    # HTTP client
    user_agent_name: str = "AMC-student-research/0.1"
    contact_email: str = ""
    request_timeout_seconds: float = Field(default=90.0, gt=0)
    max_retries: int = Field(default=5, ge=0)
    retry_backoff_seconds: float = Field(default=1.0, ge=0)
    warc_delay_seconds: float = Field(default=0.5, ge=0)
    workers: int = Field(default=4, ge=1)
    # DuckDB threads reading the Parquet index; the CDN throttles above ~4
    index_threads: int = Field(default=2, ge=1)
    # Threads for the one-off read of the 300 Parquet footers of a crawl
    layout_threads: int = Field(default=8, ge=1)

    # Sampling and filtering
    # Quota per domain and publication year (each year is fetched from its own crawl)
    articles_per_domain_year: int = Field(default=20, ge=1)
    max_fetch_per_domain: int = Field(default=600, ge=1)
    min_url_path_length: int = Field(default=25, ge=0)
    min_words: int = Field(default=150, ge=1)
    # Domains exempt from the og:type/schema.org article-markup test (comma-separated
    # in .env). Their pages must still have enough words and a detectable date.
    relaxed_domains: Annotated[frozenset[str], NoDecode] = frozenset()
    html_sniff_chars: int = Field(default=300_000, ge=1)
    seed: int = 42

    # Paths
    data_dir: Path = PROJECT_ROOT / "data"
    # YAML mapping publication year -> crawl id
    crawls_file: Path = PROJECT_ROOT / "config" / "crawls.yaml"

    @field_validator("relaxed_domains", mode="before")
    @classmethod
    def _split_domains(cls, value: object) -> object:
        """Accept ``a.pl, B.pl`` from the environment; normalise to lower case."""
        if isinstance(value, str):
            return frozenset(
                item.strip().lower() for item in value.split(",") if item.strip()
            )
        return value

    @property
    def user_agent(self) -> str:
        """User-Agent header, with the contact address when configured."""
        if self.contact_email:
            return f"{self.user_agent_name} (+{self.contact_email})"
        return self.user_agent_name

    @cached_property
    def crawl_map(self) -> dict[int, str]:
        """Publication year -> crawl id, read from ``crawls_file`` on first use."""
        return load_crawl_map(self.crawls_file)

    @property
    def cache_dir(self) -> Path:
        """Directory for reusable downloads (e.g. the Parquet file layout)."""
        return self.data_dir / "cache"

    @property
    def domains_csv(self) -> Path:
        """CSV with the sampling frame of domains."""
        return self.data_dir / "frame" / "domains.csv"

    @property
    def tranco_csv(self) -> Path:
        """CSV with all Polish domains from the Tranco list."""
        return self.data_dir / "frame" / "tranco_pl_all.csv"

    @property
    def domain_list_txt(self) -> Path:
        """Plain-text list of domains (one per line) to build the frame from."""
        return self.data_dir / "domains.txt"

    def raw_dir(self, year: int) -> Path:
        """Directory with private per-domain JSONL files (including text).

        Args:
            year: Publication year the files were collected for.
        """
        return self.data_dir / "raw_private" / str(year)

    @property
    def clean_dir(self) -> Path:
        """Directory with only the JSONL files copied from ``raw_private``."""
        return self.data_dir / "clean"

    @property
    def derived_dir(self) -> Path:
        """Directory for derived, shareable files."""
        return self.data_dir / "derived"

    @property
    def meta_csv(self) -> Path:
        """Public metadata file (without article text), all years together."""
        return self.derived_dir / "meta.csv"


settings = Settings()
