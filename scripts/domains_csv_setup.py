import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DOMAINS_FILE = BASE_DIR / "data" / "domeny.txt"
TRANCO_FILE = BASE_DIR / "data" / "frame" / "tranco_pl_all.csv"
OUTPUT_FILE = BASE_DIR / "data" / "frame" / "domains.csv"

FIELDS = [
    "domain",
    "stratum",
    "is_news",
    "rank_tranco",
    "source_note",
]


def load_domains(path):
    domains = []

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            domain = line.strip().lower()

            if domain and domain not in domains:
                domains.append(domain)

    return domains


def load_tranco(path):
    tranco = {}

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            domain = (row.get("domain") or "").strip().lower()

            if not domain:
                continue

            tranco[domain] = {
                "rank": (row.get("rank") or "").strip(),
                "stratum": (row.get("stratum") or "").strip(),
            }

    return tranco


def load_existing(path):
    existing = {}

    if not path.exists():
        return existing

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            domain = (row.get("domain") or "").strip().lower()

            if domain:
                existing[domain] = {
                    field: row.get(field, "") or ""
                    for field in FIELDS
                }

    return existing


def main():
    domains = load_domains(DOMAINS_FILE)
    tranco = load_tranco(TRANCO_FILE)
    existing = load_existing(OUTPUT_FILE)

    for domain in domains:
        tranco_data = tranco.get(domain)

        if tranco_data:
            stratum = tranco_data["stratum"]
            rank = tranco_data["rank"]

            if stratum and rank:
                source_note = f"tranco review_{stratum}"
            else:
                stratum = "S3"
                rank = ""
                source_note = "other"
        else:
            stratum = "S3"
            rank = ""
            source_note = "other"

        record = {
            "domain": domain,
            "stratum": stratum,
            "is_news": "1",
            "rank_tranco": rank,
            "source_note": source_note,
        }

        if domain in existing:
            existing[domain].update(record)
        else:
            existing[domain] = record

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing.values())


if __name__ == "__main__":
    main()
