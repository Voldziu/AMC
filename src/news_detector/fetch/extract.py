"""Turning raw HTML into clean article text."""

import re
from datetime import date

import trafilatura
from pydantic import BaseModel, ConfigDict
from trafilatura.utils import decode_file

from news_detector.config import settings
from news_detector.models import ExtractedText, WarcPage

# "This is an article" signals: og:type=article or schema.org (News/Blog)Article.
OG_ARTICLE = re.compile(r'og:type["\'][^>]*content=["\']article', re.I)
LD_ARTICLE = re.compile(r'"@type"\s*:\s*(\[[^\]]*)?"(News|Blog)?Article"', re.I)


class _TrafilaturaOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str | None = None
    title: str | None = None
    date: str | None = None
    author: str | None = None


def decode_html(page: WarcPage) -> str:
    """Decode a page body to text, preferring the charset from HTTP headers.

    Args:
        page: Body and declared charset.

    Returns:
        Decoded HTML. Falls back to charset detection for a missing or wrong
        declaration (common for legacy Polish pages in windows-1250/iso-8859-2).
    """
    if page.charset:
        try:
            return page.body.decode(page.charset)
        except (LookupError, UnicodeDecodeError):
            pass
    return decode_file(page.body)


def has_article_markup(html: str) -> bool:
    """Check the beginning of the document for article metadata.

    Args:
        html: Decoded HTML.

    Returns:
        True when og:type=article or a schema.org Article is declared.
    """
    head = html[: settings.html_sniff_chars]
    return bool(OG_ARTICLE.search(head) or LD_ARTICLE.search(head))


def extract_text(html: str, *, url: str) -> ExtractedText | None:
    """Extract the main text and metadata of an article.

    Args:
        html: Decoded HTML.
        url: Page URL, used by trafilatura for metadata.

    Returns:
        Extracted content, or ``None`` when no text was found.
    """
    output = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        favor_precision=True,
    )
    if not output:
        return None
    parsed = _TrafilaturaOutput.model_validate_json(output)
    text = (parsed.text or "").strip()
    if not text:
        return None
    return ExtractedText(
        text=text,
        title=parsed.title,
        pub_date=parsed.date,
        author_present=bool(parsed.author),
        n_words=len(text.split()),
    )


def parse_pub_date(value: str | None) -> date | None:
    """Parse the publication date reported by trafilatura.

    Args:
        value: ISO date or datetime string, or ``None``.

    Returns:
        The calendar date, or ``None`` when missing or malformed.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
