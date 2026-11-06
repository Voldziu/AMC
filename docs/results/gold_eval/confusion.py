import csv, hashlib, sys
from pathlib import Path
csv.field_size_limit(2**31 - 1)
S = Path(sys.argv[1]) / "gold"
gold = list(csv.DictReader((S / "gold.csv").open(encoding="utf-8", newline="")))
for g in gold: g["k"] = hashlib.sha1(g["text"].encode()).hexdigest()
def dev(d): return int(hashlib.md5(f"42:{d}".encode(), usedforsecurity=False).hexdigest(), 16) % 2 == 0
specs = [("Pangram","pangram_gold.csv","pangram_score",1),("logppl obs","bielik_gold.csv","logppl_observer",-1),
         ("Binoculars","bielik_gold.csv","binoculars",-1),("FDGPT perf","bielik_gold.csv","fastdetectgpt_performer",1),("FDGPT obs","bielik_gold.csv","fastdetectgpt_observer",1)]
print(f"{'detektor':11} {'prog':>7} | {'ALL AI ok':>9} {'ALL human ok':>12} | {'TEST AI ok':>10} {'TEST human ok':>13}")
for name, f, col, sg in specs:
    sc = {r["text_key"]: sg*float(r[col]) for r in csv.DictReader((S/f).open(encoding="utf-8"))}
    rows = [(g["label"], dev(g["domain"]), sc[g["k"]]) for g in gold]
    P = [s for l,d,s in rows if l=="ai" and d]; N = [s for l,d,s in rows if l=="human" and d]
    best = max(sorted(set(P)|set(N)), key=lambda t: sum(a>=t for a in P)/len(P)+sum(b<t for b in N)/len(N))
    def cnt(sel):
        a=[s for l,d,s in rows if l=="ai" and sel(d)]; h=[s for l,d,s in rows if l=="human" and sel(d)]
        return sum(x>=best for x in a), len(a), sum(x<best for x in h), len(h)
    A=cnt(lambda d:True); T=cnt(lambda d:not d)
    print(f"{name:11} {best:7.3f} | {A[0]:3d}/{A[1]:<3d} {A[0]/A[1]:4.0%} {A[2]:3d}/{A[3]:<3d} {A[2]/A[3]:4.0%} | {T[0]:2d}/{T[1]:<2d} {T[0]/T[1]:4.0%} {T[2]:3d}/{T[3]:<2d} {T[2]/T[3]:4.0%}")
