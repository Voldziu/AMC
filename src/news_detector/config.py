"""Project settings loaded from environment variables and the ``.env`` file."""

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    crawl_id: str = Field(default="CC-MAIN-2026-39", pattern=r"^CC-MAIN-\d{4}-\d{2}$")
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

    # Sampling and filtering
    articles_per_domain: int = Field(default=20, ge=1)
    max_fetch_per_domain: int = Field(default=100, ge=1)
    min_url_path_length: int = Field(default=25, ge=0)
    min_words: int = Field(default=150, ge=1)
    pub_year: int | None = Field(default=None, ge=1990, le=2100)
    html_sniff_chars: int = Field(default=300_000, ge=1)
    seed: int = 42

    # Paths
    data_dir: Path = PROJECT_ROOT / "data"

    @property
    def user_agent(self) -> str:
        """User-Agent header, with the contact address when configured."""
        if self.contact_email:
            return f"{self.user_agent_name} (+{self.contact_email})"
        return self.user_agent_name

    @property
    def pub_date_from(self) -> date | None:
        """First accepted publication day (1 January of ``pub_year``)."""
        return date(self.pub_year, 1, 1) if self.pub_year else None

    @property
    def pub_date_to(self) -> date | None:
        """Last accepted publication day (31 December of ``pub_year``)."""
        return date(self.pub_year, 12, 31) if self.pub_year else None

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

    @property
    def raw_dir(self) -> Path:
        """Directory with private per-domain JSONL files (including text)."""
        return self.data_dir / "raw_private" / self.crawl_id

    @property
    def derived_dir(self) -> Path:
        """Directory for derived, shareable files."""
        return self.data_dir / "derived"

    @property
    def meta_csv(self) -> Path:
        """Public metadata file (without article text)."""
        return self.derived_dir / f"meta_{self.crawl_id}.csv"


settings = Settings()
