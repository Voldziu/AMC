"""Cleaning, content flags and the draw of the G1 set, on synthetic articles."""

from pathlib import Path

import pytest

from news_detector.config import settings
from news_detector.fetch.store import DomainStore
from news_detector.gold import g1
from news_detector.gold.clean import clean_text, content_flags, prepare
from news_detector.models import Article

PROSE = " ".join(
    f"zdanie{i} to jest zwykły tekst redakcyjny o wydarzeniach w mieście."
    for i in range(40)
)


def test_tail_box_is_cut() -> None:
    text = f"{PROSE}\nCzytaj także: Inny artykuł o czymś zupełnie innym"
    assert "Czytaj" not in clean_text(text)
    assert clean_text(text).startswith("zdanie0")


def test_inline_box_removes_only_its_line() -> None:
    text = f"Początek tekstu.\nCzytaj także: coś\n{PROSE}"
    cleaned = clean_text(text)
    assert "Czytaj" not in cleaned
    assert "zdanie39" in cleaned


def test_repeated_lines_credits_and_title_are_removed() -> None:
    line = "Ta sama dłuższa linia powtórzona w artykule dwa razy."
    text = f"Tytuł artykułu\n{line}\nFot. Jan Kowalski\n{line}\nKoniec."
    cleaned = clean_text(text, "Tytuł artykułu")
    assert cleaned.count(line) == 1
    assert "Fot." not in cleaned
    assert not cleaned.startswith("Tytuł")


@pytest.mark.parametrize(
    ("text", "flag"),
    [
        ("Materiał powstał we współpracy z firmą X.\n" + PROSE, "sponsored"),
        (
            "W treści tego artykułu umieszczone są linki afiliacyjne.\n" + PROSE,
            "affiliate",
        ),
        (
            "Informujemy, że wchodzi w życie Rozporządzenie Parlamentu Europejskiego.\n"
            + PROSE,
            "legal",
        ),
        ("\n".join(f"Pozycja {i}" for i in range(30)), "list_like"),
        ("1 2 3 4 5 6 7 8 9 " * 40, "data_heavy"),
        (PROSE + " https://a.pl https://b.pl https://c.pl", "embeds"),
    ],
)
def test_flags(text: str, flag: str) -> None:
    assert flag in prepare(text).flags


def test_plain_prose_has_no_flags() -> None:
    assert content_flags(PROSE, PROSE) == ()


def _article(i: int, domain: str, text: str) -> Article:
    return Article(
        article_id=f"{domain}-{i}",
        domain=domain,
        stratum="S1",
        url=f"https://{domain}/artykul-numer-{i}",
        crawl_id="CC-MAIN-2021-04",
        warc_filename="f",
        warc_offset=0,
        warc_length=1,
        pub_date="2020-05-04",
        pub_year=2020,
        title=None,
        crawl_timestamp=None,
        author_present=False,
        n_words=len(text.split()),
        languages="pol",
        text_sha1=f"{domain}{i}",
        text=text,
    )


def test_draw_is_balanced_and_skips_non_articles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    for domain, count in (("a.pl", 8), ("b.pl", 8), ("c.pl", 2)):
        store = DomainStore(2020, domain)
        store.start()
        for i in range(count):
            store.add_article(_article(i, domain, PROSE))
        store.add_article(_article(99, domain, "Materiał sponsorowany.\n" + PROSE))
    picked, reasons, counts = g1.select(2020, 12)
    assert len(picked) == 12
    assert reasons["sponsored"] == 3
    by_domain = {d: sum(a.domain == d for a in picked) for d in counts}
    # Round robin: the small domain is used up, the others share the rest evenly.
    assert by_domain == {"a.pl": 5, "b.pl": 5, "c.pl": 2}
    assert not any("sponsorowany" in a.text for a in picked)
    private, sheet = g1.write(picked, 2020)
    assert private.exists()
    assert "zdanie0" not in sheet.read_text(encoding="utf-8")  # the sheet holds no text
