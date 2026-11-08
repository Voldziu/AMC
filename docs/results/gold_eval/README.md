# Detectors on the gold standard (pilot)

Evaluation of five zero-shot / classifier scores on the pilot gold standard:
G1 = 100 human articles from 2020, G2 = 100 rewrites of the same articles by
`gpt-4.1-mini` (mode `rewrite_strong`). 24 domains split into dev/test by hash
(seed 42); the threshold is the Youden maximum on dev, frozen, then applied to test
(read once). Higher score = more machine-like (Binoculars is negated).

| Detector | AUC (95% CI, bootstrap over domains) | Test sens. / spec. | Test J | Stop rule (J >= 0.2) |
|---|---|---|---|---|
| Pangram EditLens (Llama-3.2-3B) | 0.879 (0.839-0.920) | 0.958 / 0.729 | 0.688 | passes |
| logppl (observer, Bielik-1.5B) | 0.765 (0.718-0.815) | 0.854 / 0.604 | 0.458 | passes |
| Binoculars (Bielik-1.5B) | 0.560 (0.498-0.612) | 0.229 / 0.854 | 0.083 | negative |
| Fast-DetectGPT performer | 0.560 (0.493-0.632) | 0.250 / 0.708 | -0.042 | negative |
| Fast-DetectGPT observer | 0.494 (0.415-0.563) | 0.917 / 0.125 | 0.042 | negative |

Limits: small set, one year, one generator and one rewrite mode; rewriting an existing
article is not generating one from scratch. Fast-DetectGPT (observer) at AUC ~0.5 was
not cross-checked on a labelled Polish set (Smigiel), so an implementation issue is not ruled out.
Descriptive result for this pilot only; not evidence about any domain.

## Files
- `gold_scores.csv`: one row per detector and text (ids, domain, split, score; no article text).
- `dashboard.html`: page body of the interactive dashboard (confusion matrices, ROC, movable
  threshold). It needs the Claude dashboard runtime (`dash` API) and is not a standalone page.
- `build_gold.py`, `make_csv.py`, `eval_gold.py`, `confusion.py`: scripts used (stdlib only).
  They read private gold texts from `data/raw_private/gold/` and detector outputs, so they
  cannot be re-run from the repo alone; paths are passed as arguments.
- Scores were produced with `python -m news_detector.detect score` (Pangram: `--only-pangram`,
  bf16, batch 1; Bielik-1.5B: `--preset bielik-1.5b --dtype float16 --max-tokens 1024`).

AI use: scripts, analysis and the dashboard were written with Claude Code (session logs kept).
