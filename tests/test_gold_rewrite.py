"""AI rewrite of the G1 set, with the OpenAI API replaced by a stub (no network, no key)."""

import time
from pathlib import Path
from typing import Any

import pytest
import requests
from pydantic import SecretStr

from news_detector.config import settings
from news_detector.gold import rewrite
from news_detector.gold.g1 import GoldArticle

SOURCE_TEXT = " ".join(f"słowo{i}" for i in range(300))
# A different text of the same length: a strong rewrite shares no 5-gram with its source.
REWRITTEN = " ".join(f"inne{i}" for i in range(300))


def _article(i: int) -> GoldArticle:
    return GoldArticle(
        gold_set="G1",
        article_id=f"id{i}",
        domain="x.pl",
        stratum="S1",
        url=f"https://x.pl/artykul-{i}",
        title=None,
        pub_date="2020-05-04",
        pub_year=2020,
        n_words=300,
        n_words_original=320,
        text=SOURCE_TEXT,
    )


class FakeResponse:
    def __init__(self, status: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status
        self._payload = payload or {}
        self.headers: dict[str, str] = {}
        self.text = "error body"

    def json(self) -> dict[str, Any]:
        return self._payload


def _ok(text: str) -> FakeResponse:
    return FakeResponse(
        200,
        {
            "id": "chatcmpl-1",
            "model": "gpt-4.1-mini-2025",
            "choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": 700, "completion_tokens": 650},
        },
    )


class FakeSession(requests.Session):
    def __init__(self, replies: list[FakeResponse]) -> None:
        super().__init__()
        self.replies = replies
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> Any:  # type: ignore[override]
        self.calls.append({"url": url, **kwargs})
        return self.replies.pop(0)


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("sk-test-not-real"))
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


def test_estimate_scales_with_words() -> None:
    tokens_in, tokens_out, cost = rewrite.estimate([_article(1)] * 100)
    assert tokens_in > tokens_out > 0
    assert 0 < cost < 5


def test_rewrite_is_written_once_and_resumes() -> None:
    session = FakeSession([_ok(REWRITTEN), _ok(REWRITTEN)])
    sources = [_article(1), _article(2)]
    assert rewrite.run(sources[:1], session) == 1
    # A rerun with both sources only sends the missing one.
    assert rewrite.run(sources, session) == 1
    assert len(session.calls) == 2
    rows = rewrite.output_path().read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    call = session.calls[0]
    assert call["headers"]["Authorization"] == "Bearer sk-test-not-real"
    assert call["json"]["model"] == settings.openai_model


def test_provenance_is_recorded() -> None:
    result = rewrite.rewrite_one(FakeSession([_ok(REWRITTEN)]), _article(1))
    assert result.gold_set == "G2"
    assert result.task == "rewrite_strong"
    assert result.ngram_overlap == 0.0
    assert result.source_article_id == "id1"
    assert result.generator == "gpt-4.1-mini-2025"
    assert (result.prompt_tokens, result.completion_tokens) == (700, 650)
    assert result.prompt_sha1 == rewrite.prompt_sha1("strong")
    assert result.flags == []


@pytest.mark.parametrize(
    ("reply", "flag"),
    [
        ("Oto poprawiony tekst: " + REWRITTEN, "meta_comment"),
        ("krótko", "length"),
        (REWRITTEN + "\n**pogrubione**", "markdown"),
    ],
)
def test_bad_replies_are_flagged(reply: str, flag: str) -> None:
    result = rewrite.rewrite_one(FakeSession([_ok(reply)]), _article(1))
    assert flag in result.flags


def test_rate_limit_is_retried() -> None:
    session = FakeSession([FakeResponse(429), _ok(REWRITTEN)])
    assert rewrite.rewrite_one(session, _article(1)).text == REWRITTEN
    assert len(session.calls) == 2


def test_missing_key_fails_before_any_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    session = FakeSession([])
    with pytest.raises(rewrite.RewriteError, match="OPENAI_API_KEY"):
        rewrite.rewrite_one(session, _article(1))
    assert session.calls == []


def test_error_message_never_contains_the_key() -> None:
    session = FakeSession([FakeResponse(401)])
    with pytest.raises(rewrite.RewriteError) as info:
        rewrite.rewrite_one(session, _article(1))
    assert "sk-test-not-real" not in str(info.value)


def test_strong_rewrite_that_copies_the_source_is_flagged() -> None:
    result = rewrite.rewrite_one(FakeSession([_ok(SOURCE_TEXT)]), _article(1))
    assert result.ngram_overlap == 1.0
    assert "too_similar" in result.flags


def test_light_mode_may_stay_close_to_the_source() -> None:
    result = rewrite.rewrite_one(FakeSession([_ok(SOURCE_TEXT)]), _article(1), "light")
    assert result.task == "rewrite_light"
    assert "too_similar" not in result.flags


def test_modes_use_different_prompts_and_files() -> None:
    assert rewrite.prompt_sha1("light") != rewrite.prompt_sha1("strong")
    assert rewrite.output_path("light") != rewrite.output_path("strong")
    session = FakeSession([_ok(REWRITTEN)])
    rewrite.rewrite_one(session, _article(1), "strong")
    prompt = session.calls[0]["json"]["messages"][1]["content"]
    assert "od nowa" in prompt


def test_overlap_counts_only_copied_five_grams() -> None:
    half = (
        " ".join(f"słowo{i}" for i in range(150))
        + " "
        + " ".join(f"zupełnie{i}" for i in range(150))
    )
    assert 0.4 < rewrite.ngram_overlap(SOURCE_TEXT, half) < 0.6
