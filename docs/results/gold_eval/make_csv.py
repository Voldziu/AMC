import csv, hashlib, sys
from pathlib import Path
csv.field_size_limit(2**31 - 1)
S = Path(sys.argv[1]) / "gold"
gold = list(csv.DictReader((S / "gold.csv").open(encoding="utf-8", newline="")))
def dev(d): return int(hashlib.md5(f"42:{d}".encode(), usedforsecurity=False).hexdigest(), 16) % 2 == 0
specs = [("pangram","Pangram EditLens","pangram_gold.csv","pangram_score",1),
 ("logppl_observer","logppl (observer)","bielik_gold.csv","logppl_observer",-1),
 ("binoculars","Binoculars","bielik_gold.csv","binoculars",-1),
 ("fdgpt_performer","Fast-DetectGPT (performer)","bielik_gold.csv","fastdetectgpt_performer",1),
 ("fdgpt_observer","Fast-DetectGPT (observer)","bielik_gold.csv","fastdetectgpt_observer",1)]
out = S / "gold_scores.csv"
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["detector","detector_name","item_id","pair_id","label","domain","split","score","raw"])
    for det, name, fn, col, sg in specs:
        sc = {r["text_key"]: float(r[col]) for r in csv.DictReader((S/fn).open(encoding="utf-8"))}
        for g in gold:
            raw = sc[hashlib.sha1(g["text"].encode()).hexdigest()]
            w.writerow([det, name, g["item_id"], g["pair_id"], g["label"], g["domain"], "dev" if dev(g["domain"]) else "test", f"{sg*raw:.6f}", f"{raw:.6f}"])
print(out)
