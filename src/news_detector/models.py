"""Data models shared by the Common Crawl pipeline."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class RejectReason(StrEnum):
    """Why a candidate page was not kept."""

    NO_HTML = "no_html"
    NOT_ARTICLE = "not_article"
    NO_TEXT = "no_text"
    SHORT = "short"
    NO_DATE = "no_date"
    WRONG_YEAR = "wrong_year"
    DUPLICATE = "duplicate"


class IndexRecord(BaseModel):
    """One capture returned by the Common Crawl CDX index."""

    model_config = ConfigDict(extra="ignore")

    url: str
    filename: str
    offset: int
    length: int
    timestamp: str | None = None
    languages: str | None = None


class WarcPage(BaseModel):
    """HTTP response body extracted from a single WARC record."""

    body: bytes
    charset: str | None = None


class ExtractedText(BaseModel):
    """Main content and metadata extracted from an HTML page."""

    text: str
    title: str | None = None
    pub_date: str | None = None
    author_present: bool = False
    n_words: int


class Article(BaseModel):
    """A kept article together with its provenance in Common Crawl."""

    article_id: str
    domain: str
    stratum: str
    url: str
    crawl_id: str
    warc_filename: str
    warc_offset: int
    warc_length: int
    pub_date: str | None
    title: str | None
    crawl_timestamp: str | None
    author_present: bool
    n_words: int
    languages: str | None
    text_sha1: str
    text: str
