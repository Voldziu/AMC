import csv, hashlib, math, random, sys
from pathlib import Path
csv.field_size_limit(2**31 - 1)
gold, scores = Path(sys.argv[1]), Path(sys.argv[2])
col, sign = sys.argv[3], float(sys.argv[4])
sc = {r["text_key"]: sign * float(r[col]) for r in csv.DictReader(scores.open(encoding="utf-8"))}
rows = []
for r in csv.DictReader(gold.open(encoding="utf-8", newline="")):
    k = hashlib.sha1(r["text"].encode("utf-8")).hexdigest()
    if k in sc:
        rows.append(dict(label=r["label"], item=r["item_id"], pair=r["pair_id"], domain=r["domain"], s=sc[k]))
def is_dev(d):
    return int(hashlib.md5(f"42:{d}".encode(), usedforsecurity=False).hexdigest(), 16) % 2 == 0
def auc(p, n):
    return sum((a > b) + .5 * (a == b) for a in p for b in n) / (len(p) * len(n)) if p and n else math.nan
def youden(p, n):
    best = (math.nan, 0, 0, -9)
    for t in sorted(set(p) | set(n)):
        se = sum(a >= t for a in p) / len(p); sp = sum(b < t for b in n) / len(n)
        if se + sp - 1 > best[3]: best = (t, se, sp, se + sp - 1)
    return best
def at(p, n, t):
    return sum(a >= t for a in p) / len(p), sum(b < t for b in n) / len(n)
ai = [r for r in rows if r["label"] == "ai"]; hu = [r for r in rows if r["label"] == "human"]
print(f"n_human={len(hu)} n_ai={len(ai)}")
P = [r["s"] for r in ai]; N = [r["s"] for r in hu]
med = lambda x: sorted(x)[len(x)//2]
print(f"median human={med(N):.3f} ai={med(P):.3f}  AUC(all)={auc(P,N):.3f}")
byp = {r["pair"]: r["s"] for r in hu}
pairs = [r["s"] > byp[r["pair"]] for r in ai if r["pair"] in byp]
print(f"pairs={len(pairs)} rewrite scores higher in {sum(pairs)/len(pairs):.1%}")
dp = [r["s"] for r in ai if is_dev(r["domain"])]; dn = [r["s"] for r in hu if is_dev(r["domain"])]
tp = [r["s"] for r in ai if not is_dev(r["domain"])]; tn = [r["s"] for r in hu if not is_dev(r["domain"])]
print(f"dev: n_h={len(dn)} n_ai={len(dp)} AUC={auc(dp,dn):.3f}; test: n_h={len(tn)} n_ai={len(tp)}")
t, se, sp, j = youden(dp, dn)
print(f"threshold (dev, Youden) = {t:.3f}: dev sens={se:.3f} spec={sp:.3f} J={j:.3f}")
tse, tsp = at(tp, tn, t)
print(f"TEST (once): sens={tse:.3f} spec={tsp:.3f} J={tse+tsp-1:.3f}  AUC={auc(tp,tn):.3f}")
# thresholds at fixed human FPR from dev humans
for fpr in (0.01, 0.05):
    k = sorted(dn)[min(len(dn)-1, math.ceil(len(dn)*(1-fpr)))]
    a, b = at(tp, tn, k); print(f"FPR~{fpr:.0%} thr(dev)={k:.3f}: test sens={a:.3f} spec={b:.3f}")
# bootstrap CI over domains for AUC(all) and J at the frozen threshold
doms = sorted({r["domain"] for r in rows}); rnd = random.Random(42); aucs = []; js = []
for _ in range(1000):
    pick = [rnd.choice(doms) for _ in doms]
    bp = [r["s"] for d in pick for r in ai if r["domain"] == d]; bn = [r["s"] for d in pick for r in hu if r["domain"] == d]
    if bp and bn:
        aucs.append(auc(bp, bn)); a, b = at(bp, bn, t); js.append(a + b - 1)
q = lambda x, p: sorted(x)[int(p * (len(x) - 1))]
print(f"bootstrap over {len(doms)} domains: AUC 95% CI [{q(aucs,.025):.3f}, {q(aucs,.975):.3f}]; J@thr [{q(js,.025):.3f}, {q(js,.975):.3f}]")
print("STOP RULE:", "J<0.2 -> negative" if tse + tsp - 1 < 0.2 else "J>=0.2 -> passes")
