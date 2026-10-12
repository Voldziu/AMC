"""Pobiera próbkę artykułów z Common Crawl dla domen z domains.csv."""
import argparse, io, json, hashlib, random, re, time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
import trafilatura
from py3langid.langid import LanguageIdentifier, MODEL_FILE
from warcio.archiveiterator import ArchiveIterator

UA = {"User-Agent": "AMC-student-research/0.1"}
INDEX = "https://index.commoncrawl.org/{crawl}-index"
DATA = "https://data.commoncrawl.org/"
LID = LanguageIdentifier.from_model_file(MODEL_FILE, norm_probs=True)

# Adresy, które na pewno nie są artykułami (kategorie, tagi, feedy, pliki)
EXCLUDE = re.compile(
    r"/(tag|tagi|temat|tematy|kategoria|category|autor|author|page|strona|search|szukaj|"
    r"wp-json|feed|rss|login|kontakt|regulamin|polityka)(/|$)|[?#]|\.(jpg|png|pdf|xml|js|css)$",
    re.I,
)
# Sygnał "to jest artykuł": og:type=article albo schema.org Article/NewsArticle
ART1 = re.compile(r'og:type["\'][^>]*content=["\']article', re.I)
ART2 = re.compile(r'"@type"\s*:\s*(\[[^\]]*)?"(News|Blog)?Article"', re.I)


def get(url, params=None, headers=None, tries=5):
    """GET z ponawianiem; zwraca Response albo None."""
    h = dict(UA)
    if headers:
        h.update(headers)
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=h, timeout=90)
            if r.status_code in (200, 206):
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    return None


def is_candidate_url(u):
    return len(urlparse(u).path) >= 25 and not EXCLUDE.search(u)


def candidates(domain, crawl, n_pages, rng):
    """Losuje strony wyników indeksu i zwraca przetasowaną listę rekordów."""
    url = INDEX.format(crawl=crawl)
    base = {"url": domain, "matchType": "domain", "output": "json"}
    r = get(url, params={**base, "showNumPages": "true"})
    if r is None:
        return []
    pages = r.json().get("pages", 0)
    recs = []
    for p in rng.sample(range(pages), min(n_pages, pages)):
        r = get(url, params={**base, "page": p, "fl": "url,filename,offset,length,timestamp",
                             "filter": ["status:200", "mime:text/html"]})
        if r is None:
            continue
        for line in r.text.splitlines():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        time.sleep(1)
    seen, out = set(), []
    for rec in recs:
        u = rec["url"]
        if u not in seen and is_candidate_url(u):
            seen.add(u)
            out.append(rec)
    rng.shuffle(out)
    return out


def fetch_html(rec):
    """Pobiera z WARC dokładnie jeden rekord (byte-range)."""
    off, ln = int(rec["offset"]), int(rec["length"])
    r = get(DATA + rec["filename"], headers={"Range": f"bytes={off}-{off + ln - 1}"})
    if r is None or r.status_code != 206:
        return None
    for w in ArchiveIterator(io.BytesIO(r.content)):
        if w.rec_type == "response":
            return w.content_stream().read()
    return None


def make_record(rec, domain, stratum, crawl, relaxed):
    html = fetch_html(rec)
    if not html:
        return None, "no_html"
    head = html.decode("utf-8", errors="ignore")[:300000]
    is_art = bool(ART1.search(head) or ART2.search(head))
    if not is_art and not relaxed:
        return None, "not_article"
    out = trafilatura.extract(html, url=rec["url"], output_format="json",
                              with_metadata=True, favor_precision=True)
    if not out:
        return None, "no_text"
    j = json.loads(out)
    text = (j.get("text") or "").strip()
    n_words = len(text.split())
    if n_words < 150:
        return None, "short"
    lang, conf = LID.classify(text[:2000])
    if lang != "pl":
        return None, "not_polish"
    return {
        "article_id": hashlib.sha1(rec["url"].encode()).hexdigest(),
        "domain": domain, "stratum": stratum, "url": rec["url"], "crawl_id": crawl,
        "warc_filename": rec["filename"], "warc_offset": int(rec["offset"]),
        "warc_length": int(rec["length"]),
        "pub_date": j.get("date"), "title": j.get("title"),
        "crawl_timestamp": rec.get("timestamp"),
        "author_present": bool(j.get("author")),
        "n_words": n_words, "lang": lang, "lang_conf": float(conf),
        "text_sha1": hashlib.sha1(text.encode()).hexdigest(),
        "text": text,
    }, None


def run_domain(domain, stratum, crawl, a):
    rng = random.Random(f"{a.seed}-{domain}-{crawl}")
    recs = candidates(domain, crawl, a.n_pages, rng)
    kept, rejects, hashes = [], {}, set()
    for rec in recs[: a.max_fetch]:
        if len(kept) >= a.n:
            break
        row, reason = make_record(rec, domain, stratum, crawl, a.relaxed)
        time.sleep(0.3)
        if row is None:
            rejects[reason] = rejects.get(reason, 0) + 1
            continue
        if row["text_sha1"] in hashes:
            rejects["duplicate"] = rejects.get("duplicate", 0) + 1
            continue
        hashes.add(row["text_sha1"])
        kept.append(row)
    outdir = Path(f"data/raw_private/{crawl}")
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / f"{domain}.jsonl", "w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{domain:35s} {stratum} kandydaci={len(recs):5d} pobrano={len(kept):3d} odrzucone={rejects}")


def rebuild_meta(crawl):
    """Tworzy publiczny plik metadanych (bez tekstów) ze wszystkich jsonl."""
    rows = []
    for f in Path(f"data/raw_private/{crawl}").glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                d.pop("text", None)
                rows.append(d)
    pd.DataFrame(rows).to_csv(f"data/derived/meta_{crawl}.csv", index=False)
    print("Zapisano data/derived/meta_%s.csv (%d wierszy)" % (crawl, len(rows)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crawl", default="CC-MAIN-2026-39", help="crawl z Common Crawl")
    ap.add_argument("--domains", default="data/frame/domains.csv")
    ap.add_argument("--n", type=int, default=20, help="artykułów na domenę")
    ap.add_argument("--max-fetch", type=int, default=100, help="limit prób pobrania na domenę")
    ap.add_argument("--n-pages", type=int, default=3, help="ile losowych stron indeksu")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--relaxed", action="store_true", help="nie wymagaj znacznika article")
    ap.add_argument("--only", default=None, help="tylko jedna domena (test)")
    a = ap.parse_args()

    dom = pd.read_csv(a.domains)
    dom = dom[dom["is_news"] == 1]
    if a.only:
        dom = dom[dom["domain"] == a.only]
    Path("data/derived").mkdir(parents=True, exist_ok=True)
    for _, r in dom.iterrows():
        if Path(f"data/raw_private/{a.crawl}/{r['domain']}.jsonl").exists():
            print(f"{r['domain']}: pomijam (już pobrane)")
            continue
        run_domain(r["domain"], r["stratum"], a.crawl, a)
    rebuild_meta(a.crawl)


if __name__ == "__main__":
    main()