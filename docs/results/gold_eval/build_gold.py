import csv, json, sys
from pathlib import Path
root = Path(sys.argv[1]); out = Path(sys.argv[2])
rows = []
for line in (root / "data/raw_private/gold/g1_2020.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line); rows.append(("human", r["article_id"], r["article_id"], r["domain"], r["text"]))
for line in (root / "data/raw_private/gold/g2_rewrite_strong_gpt-4.1-mini_2020.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line); rows.append(("ai", "ai-" + r["source_article_id"], r["source_article_id"], r["domain"], r["text"]))
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["label", "item_id", "pair_id", "domain", "text"]); w.writerows(rows)
print(len(rows))
