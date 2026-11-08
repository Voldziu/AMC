"""Cleaning of extracted article text and detection of non-editorial content.

The cleaned text is a copy meant for detectors and the gold standard; the text stored
by the fetch pipeline is never changed. Every rule looks at structure or at fixed
marker phrases, never at style or fluency.
"""

import re
from dataclasses import dataclass

# Boxes and calls to action that follow the article ("Czytaj także ...")
TAIL_MARKER = re.compile(
    r"(czytaj\s+(także|też|więcej|dalej)|zobacz\s+(także|też|więcej|również)|"
    r"przeczytaj\s+(też|także|również)|sprawdź\s+(też|także)|polub\s+nas|"
    r"zapisz\s+się\s+na|zapisz\s+się\s+do|więcej\s+na\s+ten\s+temat|obserwuj\s+nas)",
    re.I,
)
CREDIT_LINE = re.compile(
    r"^\s*(fot\.|foto:|zdjęcie:|źródło:|autor:|tekst:|oprac\.)",
    re.I,
)
# Credits and site widgets glued to the end of the last line
TRAILING_NOISE = re.compile(
    r"\s*(źródło\s+zdjęcia[^\n]*|źródło:[^\n]*|autor:[^\n]*|fot\.[^\n]*|"
    r"radiozet\.pl/\S+|oceń\s+artykuł|\">|formularz\s+zamówienia\s+można\s+pobrać[^\n]*)\s*$",
    re.I,
)
# Site widgets glued to the start; the related-article box makes the text unusable
LEADING_NOISE = re.compile(
    r"^(oceń\s+|z\s+przyczyn\s+technicznych\s+logowanie\s+tymczasowo\s+niedostępne\.?\s*"
    r"(dziękujemy\s+za\s+wyrozumiałość\.?\s*)?)",
    re.I,
)
RELATED_BOX_START = re.compile(r"^najnowszy\s+arty\w+\s+na\s+ten\s+temat", re.I)
MAX_HEADLINE_CHARS = 110  # a last line shorter than this without end punctuation
MAX_QUESTION_CHARS = 80
DIALOGUE = ("-", "–", "„", '"')
SENTENCE_END = (".", "!", "?", '"', "”", "…", ")", "»")
SPONSORED = re.compile(
    r"(materiał\s+(powstał|został\s+przygotowany|przygotowany)\s+(we|przy)?\s*(współpracy|zlecenie)|"
    r"artykuł\s+sponsorowany|materiał\s+sponsorowany|treść\s+sponsorowana|"
    r"materiał\s+(partnera|reklamowy)|artykuł\s+(partnera|reklamowy)|"
    r"współpraca\s+reklamowa|advertorial)",
    re.I,
)
AFFILIATE = re.compile(
    r"(linki\s+afiliacyjn|link\w*\s+partnerskich|kod\w*\s+rabatow)", re.I
)
PROMO = re.compile(
    r"(black\s+friday|cyber\s+monday|w\s+promocji|promocyjn\w+|zniżk\w+|"
    r"zapraszamy\s+do\s+(sklepu|zakupów)|szeroki\w*\s+asortyment|zamów\s+(teraz|online))",
    re.I,
)
LEGAL = re.compile(
    r"(rozporządzeni\w+\s+parlamentu\s+europejskiego|rodo\b|polityk\w+\s+prywatności|"
    r"administratorem\s+danych|regulamin\w*)",
    re.I,
)
POLL = re.compile(r"(^|\n)\s*\d{1,3}\s?%\s", re.M)
TWEET = re.compile(r"(pic\.twitter\.com|twitter\.com/\S+|instagram\.com/\S+)", re.I)
EMBED = re.compile(r"(https?://|www\.|#\w{3,})")

MIN_LINE_CHARS = 20
SHORT_LINE_CHARS = 40
TAIL_ZONE = 0.6  # a marker after this share of the text cuts everything behind it


@dataclass(frozen=True)
class Cleaned:
    """A cleaned text with the editorial-content flags computed on it."""

    text: str
    n_words: int
    flags: tuple[str, ...]


def clean_text(text: str, title: str | None = None) -> str:
    """Remove the parts of an extracted article that are not its body.

    Args:
        text: Text as stored by the fetch pipeline.
        title: Title of the article, removed from the start when the text repeats it.

    Returns:
        The text without trailing "read also" boxes, credit lines, repeated lines and a
        repeated title, with blank lines collapsed.
    """
    while (cut := TAIL_MARKER.search(text)) is not None:
        if cut.start() >= TAIL_ZONE * len(text):
            text = text[: cut.start()]
            break
        # An inline box in the middle: drop the rest of that line only.
        end = text.find("\n", cut.start())
        text = text[: cut.start()] + (text[end:] if end != -1 else "")
    text = LEADING_NOISE.sub("", text.strip())
    while (noise := TRAILING_NOISE.search(text)) is not None and noise.start() > 0:
        text = text[: noise.start()]
    lines = [line.strip() for line in text.splitlines()]
    seen: set[str] = set()
    kept: list[str] = []
    for line in lines:
        if not line or CREDIT_LINE.match(line):
            continue
        if len(line) >= MIN_LINE_CHARS:
            if line in seen:
                continue
            seen.add(line)
        kept.append(line)
    # Headlines of other articles are appended: without end punctuation, or as a question.
    if (
        len(kept) > 1
        and len(kept[-1]) < MAX_QUESTION_CHARS
        and kept[-1].endswith("?")
        and not kept[-1].startswith(DIALOGUE)
    ):
        kept.pop()
    for _ in range(3):
        if (
            len(kept) > 1
            and len(kept[-1]) < MAX_HEADLINE_CHARS
            and not kept[-1].endswith(SENTENCE_END)
        ):
            kept.pop()
    result = "\n".join(kept)
    heading = (title or "").strip()
    if heading and result.startswith(heading):
        result = result[len(heading) :].lstrip(" :\n-")
    return LEADING_NOISE.sub("", result.strip()).strip()


def content_flags(
    original: str,
    text: str,
    *,
    max_digit_share: float = 0.03,
    max_short_lines: float = 0.4,
) -> tuple[str, ...]:
    """Flag text that is probably not editorial prose.

    Args:
        original: Text before cleaning; markers such as "Materiał powstał we
            współpracy" sit in lines that cleaning may remove.
        text: Cleaned text; the structure tests run on it.
        max_digit_share: Share of digit characters above which text counts as data.
        max_short_lines: Share of lines under 40 characters above which text counts as a list.

    Returns:
        Flag names: ``sponsored``, ``affiliate``, ``promo``, ``related_box``,
        ``legal``, ``list_like``, ``data_heavy``, ``embeds``, ``table_markup``, ``truncated``, ``poll``.
        Empty when none applies.
    """
    flags: list[str] = []
    if SPONSORED.search(original):
        flags.append("sponsored")
    if AFFILIATE.search(original):
        flags.append("affiliate")
    if PROMO.search(original):
        flags.append("promo")
    if RELATED_BOX_START.match(original.strip()):
        flags.append("related_box")
    if LEGAL.search(original[:600]) or len(LEGAL.findall(original)) >= 3:
        flags.append("legal")
    lines = [line for line in text.splitlines() if line.strip()]
    if (
        lines
        and sum(len(line) < SHORT_LINE_CHARS for line in lines) / len(lines)
        > max_short_lines
    ):
        flags.append("list_like")
    if text and sum(char.isdigit() for char in text) / len(text) > max_digit_share:
        flags.append("data_heavy")
    if len(EMBED.findall(text)) >= 3:
        flags.append("embeds")
    if TWEET.search(text):
        flags.append("embeds")
    if text.count("|") >= 4:
        flags.append("table_markup")
    if text.rstrip().endswith(("...", "…")):
        flags.append("truncated")
    if POLL.search(text):
        flags.append("poll")
    return tuple(flags)


def prepare(text: str, title: str | None = None) -> Cleaned:
    """Clean a text and flag it.

    Args:
        text: Text as stored by the fetch pipeline.
        title: Title of the article.

    Returns:
        The cleaned text, its word count and its flags.
    """
    cleaned = clean_text(text, title)
    return Cleaned(cleaned, len(cleaned.split()), content_flags(text, cleaned))
