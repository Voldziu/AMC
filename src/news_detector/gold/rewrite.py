"""Build the AI-written counterpart of the G1 set (G2): each article rewritten by an LLM.

Usage:
    uv run python -m news_detector.gold.rewrite [--mode {light,strong}] [--dry-run]
                                                [--limit N]

Every G1 article is sent to the OpenAI model ``settings.openai_model``. The reply is a
text that is certainly machine-written, on the same topic and with the same facts as
the human original. Two modes exist and are kept apart in the data:

* ``light``: correct and reformat; much of the original wording remains;
* ``strong`` (default): write the article again in new words and a new structure.

Both are *rewrites* of human articles, not texts written from nothing. The share of
5-grams copied from the original is stored with every text (``ngram_overlap``), so a
"strong" rewrite that stays close to its source is visible and flagged.

Results are appended one by one (resumable), with the model, the prompt hash and the
token counts. The article texts leave the machine: run ``--dry-run`` first, it needs no
key and shows the cost. The key is read from ``.env`` only.
"""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import requests
from pydantic import BaseModel

from news_detector.config import settings
from news_detector.gold.g1 import GoldArticle
from news_detector.utils.logger import get_logger

# Not ``__name__``: this module runs as ``__main__``, whose logger is not configured.
logger = get_logger("news_detector.gold.rewrite")

API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODE = "strong"
SYSTEM_PROMPT = (
    "Jesteś doświadczonym redaktorem polskiego serwisu informacyjnego. Odpowiadasz "
    "wyłącznie gotowym tekstem artykułu."
)
USER_PROMPTS = {
    "light": (
        "Popraw językowo i stylistycznie poniższy artykuł oraz sformatuj go w czytelne "
        "akapity. Zachowaj wszystkie fakty, nazwiska, liczby i cytaty; niczego nie "
        "dodawaj ani nie pomijaj. Zachowaj zbliżoną długość. Nie dodawaj tytułu, "
        "nagłówków, list, pogrubień ani komentarza od siebie; zwróć sam tekst w zwykłych "
        "akapitach.\n\nARTYKUŁ:\n{text}"
    ),
    "strong": (
        "Napisz poniższy artykuł od nowa, własnymi słowami, jak dla redakcji, która "
        "przerabia cudzy materiał na własny. Zmień konstrukcję zdań i kolejność "
        "informacji, użyj innego słownictwa, zacznij od nowego leadu i podziel tekst na "
        "logiczne akapity. Nie przepisuj zdań z oryginału. Zachowaj wszystkie fakty, "
        "nazwiska, liczby i daty; cytaty wypowiedzi osób zostaw bez zmian. Niczego nie "
        "dodawaj spoza tekstu. Zachowaj długość 80-120% oryginału. Styl: rzeczowy, "
        "neutralny, profesjonalny serwis informacyjny. Nie dodawaj tytułu, nagłówków, "
        "list, pogrubień ani komentarza od siebie; zwróć sam tekst w zwykłych "
        "akapitach.\n\nARTYKUŁ:\n{text}"
    ),
}
TOKENS_PER_WORD = 2.2  # Polish, rough; only for the dry-run estimate
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 5
META_STARTS = ("oto ", "poniżej ", "jasne", "oczywiście", "poprawiony", "tytuł:")
MIN_LENGTH_RATIO = 0.5
MAX_LENGTH_RATIO = 1.6
NGRAM = 5
# Share of the reply's 5-grams copied from the source above which a strong rewrite is
# not strong enough (names, numbers and quotations stay verbatim, so some overlap is normal)
MAX_STRONG_OVERLAP = 0.25


class RewrittenArticle(BaseModel):
    """An AI-rewritten article of the G2 set."""

    gold_set: str
    task: str
    mode: str
    source_article_id: str
    domain: str
    generator: str
    prompt_sha1: str
    temperature: float
    response_id: str | None
    prompt_tokens: int
    completion_tokens: int
    created_at: str
    n_words: int
    n_words_source: int
    ngram_overlap: float
    flags: list[str]
    text: str


class RewriteError(RuntimeError):
    """The API refused or kept failing."""


def prompt_sha1(mode: str = DEFAULT_MODE) -> str:
    """Hash of the instruction, so a changed prompt is visible in the data."""
    return hashlib.sha1(
        (SYSTEM_PROMPT + USER_PROMPTS[mode]).encode(), usedforsecurity=False
    ).hexdigest()


def ngram_overlap(source: str, text: str) -> float:
    """Share of the reply's word 5-grams that also occur in the source.

    Args:
        source: Original article.
        text: Rewritten article.

    Returns:
        A value from 0 (nothing copied) to 1 (everything copied); 0 for a very short reply.
    """

    def grams(value: str) -> set[tuple[str, ...]]:
        words = [word.strip('.,;:!?"„”()-–').lower() for word in value.split()]
        return {tuple(words[i : i + NGRAM]) for i in range(len(words) - NGRAM + 1)}

    produced = grams(text)
    return len(produced & grams(source)) / len(produced) if produced else 0.0


def load_sources(limit: int | None = None) -> list[GoldArticle]:
    """Read the G1 articles.

    Args:
        limit: Take only the first ones (for a test run).

    Returns:
        The articles in file order.

    Raises:
        FileNotFoundError: When G1 has not been drawn yet (``make gold``).
    """
    path = settings.gold_private_dir / "g1_2020.jsonl"
    rows = [
        GoldArticle.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return rows[:limit] if limit else rows


def estimate(sources: list[GoldArticle]) -> tuple[int, int, float]:
    """Estimate the tokens and the cost of rewriting the sources.

    Args:
        sources: Articles to rewrite.

    Returns:
        Input tokens, output tokens and the cost in USD at the configured prices.
    """
    words = sum(a.n_words for a in sources)
    overhead = len(sources) * 200  # the instruction
    tokens_in = int(words * TOKENS_PER_WORD) + overhead
    tokens_out = int(words * TOKENS_PER_WORD)
    cost = (
        tokens_in * settings.openai_price_input_per_m
        + tokens_out * settings.openai_price_output_per_m
    ) / 1e6
    return tokens_in, tokens_out, cost


def _post(
    session: requests.Session, article: GoldArticle, mode: str
) -> dict[str, object]:
    """Call the API with a few retries on rate limits and server errors."""
    key = settings.openai_api_key
    if key is None:
        raise RewriteError("OPENAI_API_KEY is not set; add it to .env")
    body = {
        "model": settings.openai_model,
        "temperature": settings.openai_temperature,
        "max_tokens": settings.openai_max_output_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPTS[mode].format(text=article.text)},
        ],
    }
    headers = {"Authorization": f"Bearer {key.get_secret_value()}"}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.post(
                API_URL,
                json=body,
                headers=headers,
                timeout=settings.openai_timeout_seconds,
            )
        except requests.RequestException as exc:
            logger.warning("Request failed (attempt %d): %s", attempt, exc)
            time.sleep(2**attempt)
            continue
        if response.status_code == 200:
            payload: dict[str, object] = response.json()
            return payload
        if response.status_code in RETRY_STATUSES and attempt < MAX_ATTEMPTS:
            wait = float(response.headers.get("retry-after", 2**attempt))
            logger.warning("HTTP %d, waiting %.0fs", response.status_code, wait)
            time.sleep(wait)
            continue
        # The body of an error never contains the key; it explains quota or model problems.
        raise RewriteError(f"HTTP {response.status_code}: {response.text[:300]}")
    raise RewriteError("the API kept failing")


def check(source: GoldArticle, text: str, mode: str = DEFAULT_MODE) -> list[str]:
    """Flag replies that are not a clean rewrite.

    Args:
        source: The original article.
        text: The model's reply.
        mode: ``light`` or ``strong``; only a strong rewrite is held to the overlap limit.

    Returns:
        Flag names; empty when the reply looks like the requested article.
    """
    flags: list[str] = []
    ratio = len(text.split()) / max(source.n_words, 1)
    if not MIN_LENGTH_RATIO <= ratio <= MAX_LENGTH_RATIO:
        flags.append("length")
    if text.lower().lstrip().startswith(META_STARTS):
        flags.append("meta_comment")
    if any(mark in text for mark in ("**", "\n#", "\n- ", "\n* ")):
        flags.append("markdown")
    if mode == "strong" and ngram_overlap(source.text, text) > MAX_STRONG_OVERLAP:
        flags.append("too_similar")
    return flags


def rewrite_one(
    session: requests.Session, article: GoldArticle, mode: str = DEFAULT_MODE
) -> RewrittenArticle:
    """Rewrite one article.

    Args:
        session: HTTP session.
        article: A G1 article.
        mode: ``light`` or ``strong``.

    Returns:
        The rewritten article with its provenance.

    Raises:
        RewriteError: When the API fails or returns nothing.
    """
    payload = _post(session, article, mode)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RewriteError("empty reply")
    text = str(choices[0]["message"]["content"] or "").strip()
    if not text:
        raise RewriteError("empty text")
    usage = payload.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    return RewrittenArticle(
        gold_set="G2",
        task=f"rewrite_{mode}",
        mode=mode,
        source_article_id=article.article_id,
        domain=article.domain,
        generator=str(payload.get("model") or settings.openai_model),
        prompt_sha1=prompt_sha1(mode),
        temperature=settings.openai_temperature,
        response_id=str(payload["id"]) if payload.get("id") else None,
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        n_words=len(text.split()),
        n_words_source=article.n_words,
        ngram_overlap=round(ngram_overlap(article.text, text), 4),
        flags=check(article, text, mode),
        text=text,
    )


def output_path(mode: str = DEFAULT_MODE) -> Path:
    """Private file of the rewritten texts, named after the mode and the model."""
    safe = settings.openai_model.replace("/", "-")
    return settings.gold_private_dir / f"g2_rewrite_{mode}_{safe}_2020.jsonl"


def run(
    sources: list[GoldArticle], session: requests.Session, mode: str = DEFAULT_MODE
) -> int:
    """Rewrite the articles that are not in the output file yet.

    Args:
        sources: G1 articles.
        session: HTTP session.
        mode: ``light`` or ``strong``.

    Returns:
        The number of articles written in this run.
    """
    out = output_path(mode)
    out.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out.exists():
        done = {
            json.loads(line)["source_article_id"]
            for line in out.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    todo = [a for a in sources if a.article_id not in done]
    written = 0
    for number, article in enumerate(todo, 1):
        result = rewrite_one(session, article, mode)
        with out.open("a", encoding="utf-8") as file:
            file.write(result.model_dump_json() + "\n")
        written += 1
        logger.info(
            "%d/%d %s: %d -> %d words, overlap=%.2f, flags=%s",
            number,
            len(todo),
            article.domain,
            article.n_words,
            result.n_words,
            result.ngram_overlap,
            result.flags or "none",
        )
    return written


def main() -> None:
    """Estimate the cost or rewrite the G1 articles."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(USER_PROMPTS), default=DEFAULT_MODE)
    parser.add_argument(
        "--dry-run", action="store_true", help="only estimate tokens and cost"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="only the first N articles"
    )
    args = parser.parse_args()
    sources = load_sources(args.limit)
    tokens_in, tokens_out, cost = estimate(sources)
    logger.info(
        "%d articles, mode %s, %s: about %d input and %d output tokens, about %.2f USD "
        "(rough estimate at the configured prices)",
        len(sources),
        args.mode,
        settings.openai_model,
        tokens_in,
        tokens_out,
        cost,
    )
    if args.dry_run:
        return
    with requests.Session() as session:
        written = run(sources, session, args.mode)
    logger.info("Wrote %d rewritten articles to %s", written, output_path(args.mode))


if __name__ == "__main__":
    main()
