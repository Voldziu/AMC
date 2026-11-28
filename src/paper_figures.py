"""Publication figures for the preprint (docs/paper/overleaf/preprint.tex).

Run from the repository root:

    uv run python src/paper_figures.py            # all figures
    uv run python src/paper_figures.py fig06 fig07  # selected figures

Writes vector PDFs to docs/paper/overleaf/figures/ under the same basenames as the
PNGs used so far (fig01_coverage.pdf, ...). The numbers come from the same
computation as src/notebooks/main-results.ipynb (same seeds and the same order of
random draws), so every plotted value equals the one in the paper tables.

Requires data/processed/*.csv (`make pipeline`), data/detect/*.csv and
docs/results/gold_eval/gold_scores.csv.

Every figure is drawn at its final print width (\\linewidth = 16 cm = 6.3 in) and
should be included without scaling: \\includegraphics[width=\\linewidth]{fig04_yearly}.
"""

from __future__ import annotations

import glob
import os
import sys
from functools import cache
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

from news_detector.detect.data import text_key  # noqa: E402
from news_detector.detect.report import DIRECTIONS, threshold_at_fpr, wilson_interval  # noqa: E402
from news_detector.pipeline.build import GOLD_YEARS  # noqa: E402

# ---------------------------------------------------------------------------
# Paths and analysis settings (identical to main-results.ipynb, cell 4)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DETECT = ROOT / "data" / "detect"
GOLD_SCORES = ROOT / "docs" / "results" / "gold_eval" / "gold_scores.csv"
OUT = ROOT / "docs" / "paper" / "overleaf" / "figures"

MAIN_FPR = 0.05
ROBUST_FPRS = (0.01, 0.05, 0.10, 0.20)
MASS_SHARE = 0.20
MIN_N = 50
PLACEBO_Q = 0.95
DOMAIN_CI = (5, 95)
N_BOOT = 5000
SEED = 42
SCORE = "pangram_score"
GOLD_NAMES = {
    "pangram": "pangram_score",
    "binoculars": "binoculars",
    "fdgpt_observer": "fastdetectgpt_observer",
    "fdgpt_performer": "fastdetectgpt_performer",
    "logppl_observer": "logppl_observer",
}
CATEGORIES = ["masowo: mocne dowody", "masowo: prawdopodobnie", "nadwyżka poniżej progu", "brak nadwyżki ponad dryf"]

# AUC on the Śmigiel set (PolEval 2025). The labelled sample (data/external/smigiel/sample.csv)
# is not in the repository, so these values are taken from tab:auc of the paper.
SMIGIEL_AUC = {
    "pangram": 0.80, "binoculars": 0.84, "fdgpt_observer": 0.79,
    "fdgpt_performer": 0.80, "logppl_observer": 0.71,
}

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
TEXT_WIDTH = 6.3  # in; \linewidth of the preprint (A4, margin 2.5 cm)

# Semantic colours, the same meaning in every figure (Okabe-Ito).
C_MAIN = "#0072B2"    # Pangram, 2023–2025, pi_gold, gold
C_ALT = "#D55E00"     # comparison series: constant panel, Śmigiel, Binoculars
C_THIRD = "#009E73"   # third series: Fast-DetectGPT
C_HUMAN = "#7f7f7f"   # human texts, placebo, 2020–2022
C_INK = "#000000"     # reference lines (threshold, delta, 20%, FPR)
C_MUTED = "#555555"   # secondary text
# Domain groups (fig06, fig07, fig08): one sequential blue ramp, dark = strongest evidence.
C_GROUP = {CATEGORIES[0]: "#08306b", CATEGORIES[1]: "#4292c6", CATEGORIES[2]: "#c6dbef", CATEGORIES[3]: "#ffffff"}
GROUP_SHORT = {CATEGORIES[0]: "masowo: mocne dowody", CATEGORIES[1]: "masowo: prawdopodobnie",
               CATEGORIES[2]: "nadwyżka poniżej progu", CATEGORIES[3]: "brak nadwyżki ponad dryf"}

REF_LINE = dict(color=C_INK, ls=(0, (1, 1.5)), lw=0.7)  # dotted black reference line


def _latin_modern() -> str | None:
    """Register Latin Modern Roman (OTF from the TeX/tectonic tree) and return its family name."""
    patterns = [
        os.path.expanduser("~/Library/Caches/TectonicProject.Tectonic/bundles/data/*/lmroman10-regular.otf"),
        os.path.expanduser("~/.cache/Tectonic/bundles/data/*/lmroman10-regular.otf"),
        "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf",
        "/usr/local/texlive/*/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
        os.path.expanduser("~/Library/Fonts/lmroman10-regular.otf"),
    ]
    for pattern in patterns:
        for path in glob.glob(pattern):
            fm.fontManager.addfont(path)
            return fm.FontProperties(fname=path).get_name()
    return None


def set_style() -> None:
    family = _latin_modern()
    mpl.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "font.serif": ([family] if family else []) + ["CMU Serif", "cmr10", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True,
        "font.size": 9,
        "axes.labelsize": 9, "axes.titlesize": 8.5, "axes.titleweight": "normal",
        "axes.titlelocation": "left", "axes.titlepad": 4,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "savefig.transparent": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "axes.edgecolor": "#333333", "axes.labelcolor": "black",
        "xtick.color": "#333333", "ytick.color": "#333333",
        "xtick.labelcolor": "black", "ytick.labelcolor": "black",
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "axes.grid": False, "grid.color": "#e6e6e6", "grid.linewidth": 0.5,
        "lines.linewidth": 1.2, "lines.markersize": 4, "errorbar.capsize": 0,
        "legend.frameon": False, "legend.handlelength": 1.8, "legend.borderaxespad": 0.2,
        "legend.handletextpad": 0.5, "legend.columnspacing": 1.4,
    })


def num(value: float, decimals: int = 0) -> str:
    """Polish number format: decimal comma, thin space as thousands separator (mathtext)."""
    text = f"{value:,.{decimals}f}".replace(",", "\u0000").replace(".", ",")
    return text.replace("\u0000", r"$\,$").replace("-", "−")


def axis_formatter(decimals: int = 0, suffix: str = "") -> FuncFormatter:
    return FuncFormatter(lambda v, _: num(v, decimals) + suffix)


def save(fig: plt.Figure, name: str, width: float | None = TEXT_WIDTH) -> Path:
    """Save as PDF. With ``width`` set, the figure is resized so that its tight bounding box
    (what ends up in the PDF) is exactly ``width`` inches wide: no scaling in LaTeX, fonts print
    at their nominal size."""
    if width is not None:
        for _ in range(6):
            fig.canvas.draw()
            actual = fig.get_tightbbox(fig.canvas.get_renderer()).width + 2 * mpl.rcParams["savefig.pad_inches"]
            if abs(actual - width) < 0.005:
                break
            fig.set_figwidth(fig.get_figwidth() + (width - actual))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.pdf"
    fig.savefig(path, metadata={"Creator": "src/paper_figures.py"})
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")
    return path


def chatgpt_divider(ax: plt.Axes, label: bool = True, y: float = 0.98) -> None:
    """Thin vertical line between 2022 and 2023 (ChatGPT release: 30 XI 2022)."""
    ax.axvline(2022.5, color=C_HUMAN, lw=0.6, zorder=0)
    if label:
        ax.text(2022.56, y, "ChatGPT (XI 2022)", transform=ax.get_xaxis_transform(),
                ha="left", va="top", fontsize=7.5, color=C_MUTED)


# ---------------------------------------------------------------------------
# Computation (main-results.ipynb, cells 5–58)
# ---------------------------------------------------------------------------
def auc(pos: np.ndarray, neg: np.ndarray) -> float:
    ranks = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    n1, n0 = len(pos), len(neg)
    return float((ranks[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def share(r, b, tpr):
    r, b, tpr = np.broadcast_arrays(np.asarray(r, float), np.asarray(b, float), np.asarray(tpr, float))
    with np.errstate(divide="ignore", invalid="ignore"):
        value = (r - b) / (tpr - b)
    value = np.where(tpr <= b, np.where(r > b, 1.0, 0.0), value)
    return np.clip(value, 0.0, 1.0)


def draw_rate(k, n, rng):
    return rng.beta(k + 0.5, n - k + 0.5, N_BOOT)


def roc_points(pos: np.ndarray, neg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    is_ai = np.r_[np.ones(len(pos)), np.zeros(len(neg))][np.argsort(-np.concatenate([pos, neg]), kind="stable")]
    return np.r_[0, np.cumsum(1 - is_ai) / len(neg)], np.r_[0, np.cumsum(is_ai) / len(pos)]


class Analysis:
    """The notebook's computation, kept in the notebook's order."""

    def __init__(self) -> None:
        # cell 7
        columns = ["article_id", "domain", "stratum", "pub_date", "pub_year", "n_words", "text"]
        frames = [pd.read_csv(PROCESSED / f"{s}.csv", usecols=columns).assign(split=s) for s in ("train", "dev", "test")]
        articles = pd.concat(frames, ignore_index=True)
        articles = articles[articles["text"].fillna("").str.strip() != ""].copy()
        articles["text_key"] = articles["text"].map(text_key)
        articles = articles.drop(columns="text").drop_duplicates("text_key").reset_index(drop=True)
        articles["human"] = articles["pub_year"].isin(GOLD_YEARS)
        data = articles.merge(pd.read_csv(DETECT / "pangram.csv"), on="text_key", how="inner")
        assert len(data) == len(articles)
        self.articles, self.data = articles, data
        self.stratum_of = articles.groupby("domain")["stratum"].first()

        # cell 9
        n_period = (pd.crosstab(articles["domain"], articles["human"]).reindex(columns=[True, False], fill_value=0)
                    .set_axis(["n0", "n1"], axis=1))
        self.eligible = n_period.index[(n_period["n0"] >= MIN_N) & (n_period["n1"] >= MIN_N)]
        self.excluded = n_period.drop(index=self.eligible)

        # cell 12–13
        gold = pd.read_csv(GOLD_SCORES)
        self.gold = gold
        rng = np.random.default_rng(SEED)
        self.gold_auc = {}
        for name in GOLD_NAMES:
            pairs = gold[gold["detector"] == name].pivot(index="pair_id", columns="label", values="score")
            boot = [auc(*pairs.sample(len(pairs), replace=True, random_state=rng)[["ai", "human"]].T.to_numpy())
                    for _ in range(1000)]
            self.gold_auc[name] = (auc(pairs["ai"], pairs["human"]), np.percentile(boot, 2.5), np.percentile(boot, 97.5))

        # cell 17
        self.calibration = data["human"] & data["split"].isin(["train", "dev"])
        gold_pg = gold[gold["detector"] == "pangram"]
        self.gold_ai = gold_pg[gold_pg["label"] == "ai"].set_index("pair_id")["score"]
        self.gold_human = gold_pg[gold_pg["label"] == "human"].set_index("pair_id")["score"]

        # cell 22
        self.flags_main = data[SCORE] > self.threshold(MAIN_FPR)
        per_year_n = pd.crosstab(data["domain"], data["pub_year"])
        self.balanced = per_year_n.index[(per_year_n >= 30).all(axis=1)]

        # cell 24
        self.placebo = self.placebo_changes(self.flags_main)
        self.delta = float(np.quantile(self.placebo, PLACEBO_Q))
        self.real = self.domain_rates(self.flags_main)["nadwyżka"]

        # cell 30
        self.k_tpr, self.n_tpr = self.gold_tpr(MAIN_FPR)
        self.domains = self.domain_shares(self.flags_main, self.k_tpr, self.n_tpr, self.delta)

    # --- helpers -----------------------------------------------------------
    def threshold(self, fpr: float) -> float:
        return threshold_at_fpr(self.data.loc[self.calibration, SCORE], fpr)

    def gold_tpr(self, fpr: float) -> tuple[int, int]:
        return int((self.gold_ai > self.threshold(fpr)).sum()), len(self.gold_ai)

    def placebo_changes(self, flags: pd.Series) -> np.ndarray:
        changes = []
        for _, group in self.data[self.data["human"]].groupby("domain"):
            f = flags[group.index]
            for year in sorted(GOLD_YEARS):
                this = (group["pub_year"] == year).to_numpy()
                if this.sum() >= MIN_N and (~this).sum() >= MIN_N:
                    changes.append(f[this].mean() - f[~this].mean())
        return np.array(changes)

    def domain_rates(self, flags: pd.Series) -> pd.DataFrame:
        data = self.data
        sub = data[data["domain"].isin(self.eligible)]
        table = (pd.DataFrame({"domain": sub["domain"], "human": sub["human"], "flag": flags[sub.index]})
                 .groupby(["domain", "human"])["flag"].agg(["sum", "size"]).unstack("human"))
        out = pd.DataFrame({
            "stratum": self.stratum_of[table.index],
            "n0": table[("size", True)], "k0": table[("sum", True)],
            "n1": table[("size", False)], "k1": table[("sum", False)],
        })
        out["b"] = out["k0"] / out["n0"]
        out["r"] = out["k1"] / out["n1"]
        out["nadwyżka"] = out["r"] - out["b"]
        return out

    def domain_shares(self, flags, tpr_k, tpr_n, delta, mass=MASS_SHARE, seed=SEED) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        table = self.domain_rates(flags)
        tpr_draws = draw_rate(tpr_k, tpr_n, rng)
        rows = []
        for _, row in table.iterrows():
            b_draws = draw_rate(row["k0"], row["n0"], rng)
            r_draws = draw_rate(row["k1"], row["n1"], rng)
            p_min, p_gold = share(r_draws, b_draws, 1.0), share(r_draws, b_draws, tpr_draws)
            rows.append({
                "π_min": float(share(row["r"], row["b"], 1.0)),
                "π_min low": np.percentile(p_min, DOMAIN_CI[0]), "π_min high": np.percentile(p_min, DOMAIN_CI[1]),
                "π_gold": float(share(row["r"], row["b"], tpr_k / tpr_n)),
                "π_gold low": np.percentile(p_gold, DOMAIN_CI[0]), "π_gold high": np.percentile(p_gold, DOMAIN_CI[1]),
                # unclipped point estimate, to mark values clipped at 100%
                "π_gold raw": float((row["r"] - row["b"]) / (tpr_k / tpr_n - row["b"])),
            })
        table = table.join(pd.DataFrame(rows, index=table.index))
        table["grupa"] = np.select(
            [table["nadwyżka"] <= delta, table["π_min low"] >= mass, table["π_gold low"] >= mass],
            [CATEGORIES[3], CATEGORIES[0], CATEGORIES[1]], default=CATEGORIES[2])
        return table.sort_values(["π_gold", "π_min"], ascending=False)

    def rate_by_year(self, flags: pd.Series, mask: pd.Series) -> pd.DataFrame:
        data = self.data
        rows = []
        for year, idx in data[mask].groupby("pub_year").groups.items():
            k, n = int(flags[idx].sum()), len(idx)
            low, high = wilson_interval(k, n)
            rows.append({"rok": year, "k": k, "n": n, "odsetek": k / n, "low": low, "high": high})
        return pd.DataFrame(rows).set_index("rok")

    # --- robustness (cells 40, 44, 47, 50) ----------------------------------
    @cache
    def robustness(self) -> pd.DataFrame:
        data = self.data
        variants: dict[str, pd.DataFrame] = {}
        for fpr in ROBUST_FPRS:
            flags = data[SCORE] > self.threshold(fpr)
            k, n = self.gold_tpr(fpr)
            delta = float(np.quantile(self.placebo_changes(flags), PLACEBO_Q))
            variants[f"FPR {int(round(100 * fpr))}%"] = self.domain_shares(flags, k, n, delta)
        # length-dependent threshold (cell 43–44)
        edges = np.quantile(data["n_words"], np.linspace(0, 1, 9))
        edges[0], edges[-1] = -np.inf, np.inf
        len_bin = pd.cut(data["n_words"], edges, labels=False)
        gold_len = pd.Series(len_bin.to_numpy(), index=data.index).groupby(data["article_id"]).first()
        gold_bins = gold_len.reindex(self.gold_ai.index)
        flags = pd.Series(False, index=data.index)
        gold_flags = pd.Series(False, index=self.gold_ai.index)
        for b in range(8):
            in_bin = len_bin == b
            t = threshold_at_fpr(data.loc[self.calibration & in_bin, SCORE], MAIN_FPR)
            flags[in_bin] = data.loc[in_bin, SCORE] > t
            gold_flags[gold_bins == b] = self.gold_ai[gold_bins == b] > t
        delta_len = float(np.quantile(self.placebo_changes(flags), PLACEBO_Q))
        variants["długość"] = self.domain_shares(flags, int(gold_flags.sum()), len(gold_flags), delta_len)
        for q, label in ((0.90, "P90"), (0.99, "P99")):
            d = float(np.quantile(self.placebo, q))
            variants[f"δ {label}"] = self.domain_shares(self.flags_main, self.k_tpr, self.n_tpr, d)
        for mass in (0.10, 0.30):
            variants[f"masowo {int(round(100 * mass))}"] = self.domain_shares(
                self.flags_main, self.k_tpr, self.n_tpr, self.delta, mass=mass)
        return pd.DataFrame({name: t["grupa"] for name, t in variants.items()})

    # --- other detectors (cell 56) -----------------------------------------
    @cache
    def detector_years(self) -> dict[str, pd.DataFrame]:
        data = self.data
        bielik45 = data[["text_key"]].merge(pd.read_csv(DETECT / "bielik-4.5b.csv"), on="text_key", how="left")
        bielik45.index = data.index
        assert bielik45["binoculars"].notna().all()
        out = {}
        for column in (SCORE, "binoculars", "fastdetectgpt_observer"):
            m = data[SCORE] if column == SCORE else DIRECTIONS[column] * bielik45[column]
            flags = m > threshold_at_fpr(m[self.calibration], MAIN_FPR)
            out[column] = self.rate_by_year(flags, data["domain"].notna())
        return out


@cache
def analysis() -> Analysis:
    return Analysis()


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def fig01_coverage() -> None:
    A = analysis()
    t = A.articles.groupby("pub_year").agg(n=("article_id", "size"), serwisy=("domain", "nunique"))
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.3))
    colors = [C_HUMAN if y in GOLD_YEARS else C_MAIN for y in t.index]
    ax.bar(t.index, t["n"], width=0.62, color=colors, lw=0)
    for year, n in t["n"].items():
        ax.text(year, n + 120, num(n), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(t.index, [f"{y}\n{s} serwisów" if s != 1 else f"{y}\n1 serwis" for y, s in t["serwisy"].items()])
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, 8000)
    ax.yaxis.set_major_locator(MultipleLocator(2000))
    ax.yaxis.set_major_formatter(axis_formatter())
    ax.set_ylabel("liczba artykułów")
    ax.legend(handles=[Patch(color=C_HUMAN, lw=0, label="2020–2022: poziom bazowy (teksty ludzkie)"),
                       Patch(color=C_MAIN, lw=0, label="2023–2025: okres badany")],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, handlelength=1.0)
    save(fig, "fig01_coverage")


def fig01b_coverage_heatmap() -> None:
    A = analysis()
    counts = pd.crosstab(A.articles["domain"], A.articles["pub_year"])
    order = sorted(counts.index, key=lambda d: (A.stratum_of[d], d))
    counts = counts.loc[order]
    values = counts.to_numpy()
    n_rows = len(counts)
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 0.142 * n_rows + 0.55))
    cmap = mpl.colormaps["Blues"]
    ax.imshow(values, cmap=cmap, vmin=0, vmax=200, aspect="auto", interpolation="nearest")
    for i in range(n_rows):
        for j in range(values.shape[1]):
            v = values[i, j]
            ax.text(j, i, str(v) if v else "–", ha="center", va="center", fontsize=6,
                    color="white" if v > 120 else ("black" if v else C_MUTED))
    # stratum separators and labels
    strata = [A.stratum_of[d] for d in counts.index]
    for i in range(1, n_rows):
        if strata[i] != strata[i - 1]:
            ax.axhline(i - 0.5, color="black", lw=0.8)
    ax.axvline(2.5, color="black", lw=0.8)
    ax.set_xticks(range(values.shape[1]), counts.columns)
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0)
    ax.set_yticks(range(n_rows), counts.index, fontsize=7)
    for s in sorted(set(strata)):
        rows = [i for i, x in enumerate(strata) if x == s]
        ax.text(values.shape[1] - 0.5 + 0.15, (rows[0] + rows[-1]) / 2, s, ha="left", va="center", fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # keep the matrix compact: about 0.45 in per year column
    fig.subplots_adjust(left=0.5 - 3 * 0.45 / TEXT_WIDTH + 0.08, right=0.5 + 3 * 0.45 / TEXT_WIDTH + 0.08)
    save(fig, "fig01b_coverage_heatmap", width=None)


AUC_ROWS = [  # (gold detector key, label)
    ("pangram", "Pangram EditLens"),
    ("binoculars", "Binoculars"),
    ("fdgpt_observer", "Fast-DetectGPT, bazowy"),
    ("fdgpt_performer", "Fast-DetectGPT, instrukcyjny"),
    ("logppl_observer", "zwykła perplexity"),
]


def fig02_instrument_auc() -> None:
    A = analysis()
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.1))
    y = np.arange(len(AUC_ROWS))[::-1]
    for yi, (key, _) in zip(y, AUC_ROWS):
        g, lo, hi = A.gold_auc[key]
        s = SMIGIEL_AUC[key]
        ax.plot([s, g], [yi, yi], color="#cfcfcf", lw=2.2, solid_capstyle="butt", zorder=1)
        ax.hlines(yi, lo, hi, color=C_MAIN, lw=0.9, zorder=2)
        ax.plot(s, yi, "o", ms=5, mfc="white", mec=C_ALT, mew=1.2, zorder=3)
        ax.plot(g, yi, "o", ms=5, mfc=C_MAIN, mec=C_MAIN, zorder=3)
    ax.axvline(0.5, **REF_LINE)
    ax.text(0.505, y.max() + 0.55, "brak sygnału (AUC 0,5)", fontsize=7.5, color=C_MUTED, va="center")
    ax.set_yticks(y, [label for _, label in AUC_ROWS])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(y.min() - 0.5, y.max() + 0.9)
    ax.xaxis.set_major_formatter(axis_formatter(1))
    ax.set_xlabel("AUC (0,5 = brak rozróżnienia, 1 = idealne rozróżnienie AI od człowieka)")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="none", ms=5, mfc="white", mec=C_ALT, mew=1.2,
               label="Śmigiel (krótkie teksty, modele open-source)"),
        Line2D([], [], marker="o", ls="-", lw=0.9, ms=5, color=C_MAIN,
               label="gold (przeróbki GPT newsów) z 95% CI"),
    ], loc="lower right", bbox_to_anchor=(1.0, 1.0), ncols=2)
    save(fig, "fig02_instrument_auc")


def fig02b_roc() -> None:
    """ROC on the gold set (G2 vs G1). Śmigiel curves need the labelled sample, which is not in the repo."""
    A = analysis()
    curves = [
        ("pangram", "Pangram EditLens", C_MAIN, "-"),
        ("binoculars", "Binoculars (Bielik 1,5B)", C_ALT, "--"),
        ("fdgpt_observer", "Fast-DetectGPT, bazowy (Bielik 1,5B)", C_THIRD, ":"),
    ]
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.9))
    ax.plot([0, 100], [0, 100], color=C_HUMAN, lw=0.6, ls="-", zorder=0)
    for key, label, color, style in curves:
        pairs = A.gold[A.gold["detector"] == key].pivot(index="pair_id", columns="label", values="score")
        x, yv = roc_points(pairs["ai"].to_numpy(), pairs["human"].to_numpy())
        ax.plot(100 * x, 100 * yv, color=color, ls=style, lw=1.2,
                label=f"{label}, AUC {num(A.gold_auc[key][0], 2)}")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.set_major_locator(MultipleLocator(20))
    ax.set_xlabel("FPR: oznaczone oryginały G1 [%]")
    ax.set_ylabel("TPR: oznaczone przeróbki G2 [%]")
    ax.legend(loc="center left", bbox_to_anchor=(1.06, 0.5), handlelength=2.4)
    save(fig, "fig02b_roc", width=None)


def fig03_threshold_hist() -> None:
    """Survival curves 1 − F(s): share of texts scoring above s."""
    A = analysis()
    cut = A.threshold(MAIN_FPR)
    groups = [
        (A.data.loc[A.data["human"], SCORE].to_numpy(), f"nasze teksty 2020–2022 ($n$ = {num(A.data['human'].sum())})",
         "black", "-", 1.1),
        (A.gold_human.to_numpy(), "G1: ludzkie oryginały ($n$ = 100)", C_HUMAN, "--", 1.2),
        (A.gold_ai.to_numpy(), "G2: przeróbki GPT ($n$ = 100)", C_MAIN, "-", 1.4),
    ]
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.6))
    for values, label, color, style, lw in groups:
        s = np.sort(values)
        x = np.r_[0, s, 1]
        surv = np.r_[1, 1 - np.arange(1, len(s) + 1) / len(s), 0]
        ax.step(x, 100 * surv, where="post", color=color, ls=style, lw=lw, label=label)
    ax.axvline(cut, **REF_LINE)
    ax.text(cut + 0.012, 48, f"próg {num(cut, 2)}\n(FPR 5%)", fontsize=8, va="center")
    for values, color, dy in ((A.gold_ai.to_numpy(), C_MAIN, 0), (A.gold_human.to_numpy(), C_HUMAN, 1)):
        p = 100 * (values > cut).mean()
        ax.plot(cut, p, "o", ms=3.5, color=color, zorder=4)
        ax.annotate(f"{num(p)}%", (cut, p), xytext=(5, 3 + dy), textcoords="offset points",
                    ha="left", va="bottom", fontsize=8, color=color if color != C_HUMAN else C_MUTED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(axis_formatter(1))
    ax.yaxis.set_major_locator(MultipleLocator(20))
    ax.set_xlabel("wynik Pangrama $s$ (0 = ludzki, 1 = AI)")
    ax.set_ylabel("teksty z wynikiem $> s$ [%]")
    ax.legend(loc="upper right")
    save(fig, "fig03_threshold_hist")


def _year_series(ax, table, color, marker, ls, shift, label, mfc=None, ms=4.2):
    x = table.index.to_numpy() + shift
    yv = 100 * table["odsetek"].to_numpy()
    ax.plot(x, yv, color=color, ls=ls, lw=1.1, zorder=2)
    ax.vlines(x, 100 * table["low"], 100 * table["high"], color=color, lw=0.9, zorder=2)
    ax.plot(x, yv, marker, ls="none", ms=ms, color=color, mfc=mfc or color, mec=color, mew=0.9, zorder=3,
            label=label)
    return x[-1], yv[-1]


def fig04_yearly() -> None:
    A = analysis()
    data = A.data
    t_all = A.rate_by_year(A.flags_main, data["domain"].notna())
    t_bal = A.rate_by_year(A.flags_main, data["domain"].isin(A.balanced))
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.6))
    ax.hlines(100 * MAIN_FPR, 2019.55, 2025.45, **REF_LINE)
    ax.text(2025.55, 100 * MAIN_FPR, "FPR 5%", fontsize=7.5, va="center", color=C_MUTED)
    chatgpt_divider(ax)
    x1, y1 = _year_series(ax, t_all, C_MAIN, "o", "-", -0.05, None)
    x2, y2 = _year_series(ax, t_bal, C_ALT, "s", "--", 0.05, None, ms=3.8)
    ax.text(x1 + 0.16, y1, f"wszystkie serwisy ({data['domain'].nunique()})", color="black", fontsize=8, va="center")
    ax.text(x2 + 0.16, y2, f"stały skład ({len(A.balanced)})", color="black", fontsize=8, va="center")
    ax.set_xlim(2019.55, 2026.2)
    ax.set_xticks(range(2020, 2026))
    ax.spines["bottom"].set_bounds(2019.55, 2025.45)
    ax.set_ylim(0, 13)
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.set_ylabel("oznaczone przez Pangram [%]")
    save(fig, "fig04_yearly")


def fig05_placebo() -> None:
    """Empirical CDFs of the placebo changes (110) and of the post-2022 excess (37 domains)."""
    A = analysis()
    placebo = 100 * np.sort(A.placebo)
    real = 100 * np.sort(A.real.to_numpy())
    delta = 100 * A.delta
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.5))
    lo, hi = -10, 36
    for values, color, lw, label in (
        (placebo, C_HUMAN, 1.3, f"bez AI: jeden rok 2020–22 vs dwa pozostałe ({len(placebo)} porównań)"),
        (real, C_MAIN, 1.3, f"po 2022 r.: 2023–25 vs 2020–22 ({len(real)} serwisów)"),
    ):
        x = np.r_[lo, values, hi]
        yv = np.r_[0, np.arange(1, len(values) + 1) / len(values), 1]
        ax.step(x, 100 * yv, where="post", color=color, lw=lw, label=label)
    ax.axvline(delta, **REF_LINE)
    ax.text(delta + 0.4, 4, f"margines dryfu $\\delta$ = {num(delta, 1)} pp", fontsize=8, va="bottom")
    n_above = int((A.real > A.delta).sum())
    frac_below = 100 * (1 - n_above / len(real))
    ax.annotate(f"{n_above} z {len(real)} serwisów powyżej $\\delta$", (delta, frac_below),
                xytext=(14, -2), textcoords="offset points", fontsize=8, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.5, color=C_MUTED, shrinkA=0, shrinkB=2))
    z = A.real.idxmax()
    ax.annotate(z, (100 * A.real.max(), 100), xytext=(-30, -22), textcoords="offset points", ha="right",
                fontsize=7.5, color=C_MUTED,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=C_MUTED, shrinkA=0, shrinkB=1))
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 102)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_formatter(axis_formatter())
    ax.yaxis.set_major_locator(MultipleLocator(25))
    ax.set_xlabel("zmiana odsetka oznaczonych w serwisie [pp]")
    ax.set_ylabel("skumulowany odsetek [%]")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.12))
    save(fig, "fig05_placebo")


def _group_marker(group: str) -> dict:
    face = C_GROUP[group]
    edge = "#08306b" if group != CATEGORIES[3] else C_HUMAN
    return dict(mfc=face, mec=edge, mew=0.8)


def fig06_forest() -> None:
    A = analysis()
    shown = A.domains.iloc[::-1]
    y = np.arange(len(shown))
    fig, (ax_min, ax_gold) = plt.subplots(
        1, 2, figsize=(TEXT_WIDTH, 7.4), sharey=True, gridspec_kw={"width_ratios": [1, 1.55], "wspace": 0.07})
    panels = (
        (ax_min, "π_min", 40, r"$\pi_{\mathrm{min}}$: dolna granica (TPR = 100%)", "s", 3.4),
        (ax_gold, "π_gold", 100, r"$\pi_{\mathrm{gold}}$: TPR z przeróbek G2 (26%)", "o", 3.8),
    )
    for ax, col, xmax, title, marker, ms in panels:
        for yi, (domain, row) in zip(y, shown.iterrows()):
            if yi % 2 == 0:
                ax.axhspan(yi - 0.5, yi + 0.5, color="#f4f4f4", lw=0, zorder=0)
            clipped = row[f"{col} raw"] > 1 if col == "π_gold" else False
            if clipped:
                ax.annotate("", xy=(xmax, yi), xytext=(xmax - 7, yi),
                            arrowprops=dict(arrowstyle="-|>", lw=1.0, color="#08306b", mutation_scale=7))
                ax.text(xmax - 8, yi, "$>$100% (obcięte)", ha="right", va="center", fontsize=7)
                continue
            ax.hlines(yi, 100 * row[f"{col} low"], 100 * row[f"{col} high"], color="#333333", lw=0.9, zorder=2)
            ax.plot(100 * row[col], yi, marker, ms=ms, zorder=3, **_group_marker(row["grupa"]))
        ax.axvline(100 * MASS_SHARE, color=C_INK, ls=(0, (4, 2)), lw=0.7, zorder=1)
        ax.set_xlim(0, xmax)
        ax.xaxis.set_major_locator(MultipleLocator(10 if xmax == 40 else 20))
        ax.xaxis.set_major_formatter(axis_formatter())
        ax.set_xlabel(f"{title} [%]", fontsize=8.5)
        ax.tick_params(axis="y", length=0)
        ax.set_ylim(-0.6, len(shown) - 0.4)
        ax.spines["left"].set_visible(False)
        ax.xaxis.set_ticks_position("bottom")
        top = ax.secondary_xaxis("top")
        top.xaxis.set_major_locator(MultipleLocator(10 if xmax == 40 else 20))
        top.xaxis.set_major_formatter(axis_formatter())
        top.tick_params(labelsize=7, length=2)
        top.spines["top"].set_linewidth(0.6)
    ax_min.set_yticks(y, [f"{d}  {s}" for d, s in zip(shown.index, shown["stratum"])], fontsize=7.5)
    handles = [Line2D([], [], marker="o", ls="none", ms=4.5, label=GROUP_SHORT[g], **_group_marker(g))
               for g in CATEGORIES]
    handles.append(Line2D([], [], color=C_INK, ls=(0, (4, 2)), lw=0.7, label="próg „masowo” (20%)"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.012), ncols=3, fontsize=7.5,
               columnspacing=1.0, handletextpad=0.3)
    fig.subplots_adjust(bottom=0.095)
    save(fig, "fig06_forest")


def fig07_timelines() -> None:
    A = analysis()
    data, domains = A.data, A.domains
    highlight = list(domains.index[domains["grupa"].isin(CATEGORIES[:2])])
    post_rate = {d: A.flags_main[(data["domain"] == d) & ~data["human"]].mean()
                 for d in A.excluded.index if A.excluded.loc[d, "n1"] >= 100}
    highlight.append(max(post_rate, key=post_rate.get))
    fig, axes = plt.subplots(2, 3, figsize=(TEXT_WIDTH, 4.3), sharey=True,
                             gridspec_kw={"hspace": 0.85, "wspace": 0.12})
    for ax, domain in zip(axes.ravel(), highlight):
        mask = data["domain"] == domain
        t = A.rate_by_year(A.flags_main, mask).reindex(range(2020, 2026))
        ax.axvline(2022.5, color=C_HUMAN, lw=0.6, zorder=0)
        if domain in domains.index:
            b = 100 * domains.loc[domain, "b"]
            ax.hlines(b, 2019.6, 2022.4, color="black", lw=0.8, zorder=1)
            ax.hlines(b, 2022.6, 2025.4, color="black", lw=0.6, ls=(0, (1, 1.5)), zorder=1)
            status = GROUP_SHORT[domains.loc[domain, "grupa"]]
        else:
            status = "bez poziomu bazowego"
        ok = t["n"].notna()
        for year, row in t[ok].iterrows():
            small = row["n"] < 30
            ax.vlines(year, 100 * row["low"], 100 * row["high"], color=C_MAIN, lw=0.9, zorder=2)
            ax.plot(year, 100 * row["odsetek"], "o", ms=4.2, color=C_MAIN, mec=C_MAIN, mew=0.9,
                    mfc="white" if small else C_MAIN, zorder=3)
        ax.set_title(f"{domain} ({A.stratum_of[domain]})\n{status}", fontsize=8, linespacing=1.15)
        n_year = t["n"].fillna(0).astype(int)
        ax.set_xticks(range(2020, 2026), [f"’{y % 100}\n{n if n else '–'}" for y, n in n_year.items()], fontsize=7.5)
        ax.tick_params(axis="x", length=0)
        ax.set_xlim(2019.5, 2025.5)
        ax.set_ylim(0, 85)
        ax.yaxis.set_major_locator(MultipleLocator(20))
    fig.supylabel("oznaczone przez Pangram [%]", fontsize=9, x=0.035)
    for ax in axes.ravel()[len(highlight):]:
        ax.axis("off")
    axes[0, 0].text(2019.6, 100 * domains.loc[highlight[0], "b"] + 2.5, "$b$", fontsize=8, va="bottom")
    handles = [
        Line2D([], [], marker="o", color=C_MAIN, lw=0.9, ms=4.2, label="$n \\geq 30$"),
        Line2D([], [], marker="o", color=C_MAIN, mfc="white", lw=0.9, ms=4.2, label="$n < 30$"),
        Line2D([], [], color="black", lw=0.8, label="poziom bazowy $b$ (2020–2022)"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.11, 0.955), ncols=3, fontsize=7.5)
    save(fig, "fig07_timelines")


ROBUST_COLUMNS = [  # (variant key, header line 1, header line 2, family)
    ("FPR 1%", "1%", "", 0), ("FPR 5%", "5%", "(główna)", 0), ("FPR 10%", "10%", "", 0), ("FPR 20%", "20%", "", 0),
    ("długość", "osobny", "w 8 klasach", 1),
    ("δ P90", "P90", "", 2), ("δ P99", "P99", "", 2),
    ("masowo 10", r"$\geq$10%", "", 3), ("masowo 30", r"$\geq$30%", "", 3),
]
FAMILY_LABELS = ["próg FPR", "długość", r"margines $\delta$", "„masowo”"]


def fig08_robustness() -> None:
    A = analysis()
    grid = A.robustness()
    code = {c: i for i, c in enumerate(CATEGORIES)}
    mass = grid.isin(CATEGORIES[:2]).any(axis=1)
    sub = grid[mass]
    order = sorted(sub.index, key=lambda d: (sum(code[g] for g in sub.loc[d]), d))
    sub = sub.loc[order, [c[0] for c in ROBUST_COLUMNS]]
    gap = 0.35
    xs, x = [], 0.0
    for i, (_, _, _, fam) in enumerate(ROBUST_COLUMNS):
        if i and fam != ROBUST_COLUMNS[i - 1][3]:
            x += gap
        xs.append(x)
        x += 1
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 3.5))
    for i, domain in enumerate(sub.index):
        for xj, (key, *_rest) in zip(xs, ROBUST_COLUMNS):
            g = sub.loc[domain, key]
            ax.add_patch(mpl.patches.Rectangle((xj + 0.04, i - 0.42), 0.92, 0.84, facecolor=C_GROUP[g],
                                               edgecolor="#9e9e9e" if g == CATEGORIES[3] else "none", lw=0.5))
            if g == CATEGORIES[0]:
                ax.plot([xj + 0.38, xj + 0.62], [i, i], "o", ms=2.6, color="white", mec="none")
            elif g == CATEGORIES[1]:
                ax.plot(xj + 0.5, i, "o", ms=2.6, color="white", mec="none")
    ax.set_xlim(-0.05, xs[-1] + 1.05)
    ax.set_ylim(len(sub) - 0.5, -0.5)
    ax.set_yticks(range(len(sub)), [f"{d}  {A.stratum_of[d]}" for d in sub.index], fontsize=7.5)
    ax.set_xticks([xj + 0.5 for xj in xs],
                  [h1 + ("\n" + h2 if h2 else "") for _, h1, h2, _ in ROBUST_COLUMNS], fontsize=7.5)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for fam, label in enumerate(FAMILY_LABELS):
        cols = [xj for xj, c in zip(xs, ROBUST_COLUMNS) if c[3] == fam]
        x0, x1 = cols[0] + 0.06, cols[-1] + 0.94
        ax.plot([x0, x1], [1.115, 1.115], color="black", lw=0.6, transform=ax.get_xaxis_transform(), clip_on=False)
        ax.text((x0 + x1) / 2, 1.135, label, ha="center", va="bottom", fontsize=8, transform=ax.get_xaxis_transform())
    from matplotlib.legend_handler import HandlerLine2D, HandlerTuple
    patches = [Patch(facecolor=C_GROUP[g], edgecolor="#9e9e9e" if g == CATEGORIES[3] else "none", lw=0.5)
               for g in CATEGORIES]
    dots2 = Line2D([], [], marker="o", ls="none", ms=2.2, color="white", mec="none")
    dots1 = Line2D([], [], marker="o", ls="none", ms=2.2, color="white", mec="none")
    handles = [(patches[0], dots2), (patches[1], dots1), patches[2], patches[3]]
    fig.legend(handles=handles, labels=[GROUP_SHORT[g] for g in CATEGORIES], loc="upper center",
               bbox_to_anchor=(0.56, 0.035), ncols=4, fontsize=7.5, handlelength=1.6, columnspacing=1.0,
               handler_map={tuple: HandlerTuple(ndivide=1, pad=0), dots2: HandlerLine2D(numpoints=2),
                            dots1: HandlerLine2D(numpoints=1)})
    save(fig, "fig08_robustness")


def fig09_detectors_yearly() -> None:
    A = analysis()
    years = A.detector_years()
    series = [
        (SCORE, "Pangram EditLens", C_MAIN, "o", "-", -0.08),
        ("binoculars", "Binoculars (Bielik 4,5B)", C_ALT, "s", "--", 0.0),
        ("fastdetectgpt_observer", "Fast-DetectGPT (Bielik 4,5B)", C_THIRD, "^", ":", 0.08),
    ]
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH, 2.6))
    ax.hlines(100 * MAIN_FPR, 2019.55, 2025.45, **REF_LINE)
    chatgpt_divider(ax)
    ends = [(None, 100 * MAIN_FPR, "FPR 5%")]
    for column, label, color, marker, ls, shift in series:
        x, yv = _year_series(ax, years[column], color, marker, ls, shift, label, ms=4.0)
        ends.append((x, yv, label))
    # direct labels at the line ends, nudged apart
    ends.sort(key=lambda e: e[1])
    placed = []
    for x, yv, label in ends:
        ly = yv if not placed else max(yv, placed[-1] + 0.95)
        placed.append(ly)
        ax.text(2025.32, ly, label, fontsize=8 if x is not None else 7.5, va="center",
                color="black" if x is not None else C_MUTED)
    ax.set_xlim(2019.55, 2026.75)
    ax.spines["bottom"].set_bounds(2019.55, 2025.45)
    ax.set_xticks(range(2020, 2026))
    ax.set_ylim(0, 13)
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.set_ylabel("oznaczone teksty [%]")
    save(fig, "fig09_detectors_yearly")


FIGURES = {
    "fig01": fig01_coverage, "fig01b": fig01b_coverage_heatmap,
    "fig02": fig02_instrument_auc, "fig02b": fig02b_roc,
    "fig03": fig03_threshold_hist, "fig04": fig04_yearly, "fig05": fig05_placebo,
    "fig06": fig06_forest, "fig07": fig07_timelines, "fig08": fig08_robustness,
    "fig09": fig09_detectors_yearly,
}


def main(argv: list[str]) -> None:
    set_style()
    selected = argv or list(FIGURES)
    for key in selected:
        FIGURES[key]()


if __name__ == "__main__":
    main(sys.argv[1:])
