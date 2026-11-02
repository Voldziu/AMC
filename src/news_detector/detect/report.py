"""Calibrate detector thresholds on pre-LLM articles and tabulate flag rates.

Articles from 2020-2022 (label 0) are treated as human-written. Thresholds are
set so that only a chosen share of them (the target false positive rate) is
flagged, using the train and dev splits; the test split shows whether that
rate holds on unseen articles. The same thresholds are then applied to every
year and domain.

Outputs (CSV, in ``data/detect/reports/<scores file name>/``):
    calibration.csv  threshold and false positive rate per detector
    by_year.csv      flag rate per publication year (2020-2022 = placebo)
    by_domain.csv    flag rate per domain before and after 2023, with p-values
"""

import math
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pandas as pd

from news_detector.detect.data import (
    DEFAULT_INPUTS,
    SCORES_DIR,
    DetectError,
    text_key,
)
from news_detector.pipeline.build import GOLD_YEARS
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

# +1: a higher score means "more machine-like"; -1: a lower score does
DIRECTIONS: dict[str, int] = {
    "binoculars": -1,
    "fastdetectgpt_observer": 1,
    "fastdetectgpt_performer": 1,
    "logppl_observer": -1,
    "pangram_score": 1,
}
DEFAULT_FPRS = (0.01, 0.05)
CALIBRATION_SPLITS = frozenset({"train", "dev"})
HELDOUT_SPLIT = "test"
_ARTICLE_COLUMNS = ["domain", "stratum", "pub_year", "label", "text"]


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion."""
    if total == 0:
        return math.nan, math.nan
    rate = successes / total
    denominator = 1 + z**2 / total
    centre = (rate + z**2 / (2 * total)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / total + z**2 / (4 * total**2))
    return centre - margin / denominator, centre + margin / denominator


def fisher_greater(
    flagged_after: int,
    n_after: int,
    flagged_before: int,
    n_before: int,
) -> float:
    """One-sided Fisher exact test: is the later flag rate higher?"""
    total = n_after + n_before
    flagged = flagged_after + flagged_before
    denominator = math.comb(total, n_after)
    numerator = sum(
        math.comb(flagged, k) * math.comb(total - flagged, n_after - k)
        for k in range(flagged_after, min(flagged, n_after) + 1)
    )
    return numerator / denominator


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """False discovery rate q-values for a family of tests."""
    order = p_values.sort_values()
    count = len(order)
    scaled = order * count / pd.Series(range(1, count + 1), index=order.index)
    adjusted = scaled[::-1].cummin()[::-1].clip(upper=1.0)
    return adjusted.reindex(p_values.index)


def load_articles(inputs: Sequence[Path] = DEFAULT_INPUTS) -> pd.DataFrame:
    """Article metadata from the processed split CSVs, keyed by ``text_key``."""
    frames = []
    for path in inputs:
        try:
            frame = pd.read_csv(path, usecols=_ARTICLE_COLUMNS)
        except (OSError, ValueError) as exc:
            raise DetectError(f"Cannot read articles from {path}: {exc}") from exc
        frames.append(frame.assign(split=path.stem))
    articles = pd.concat(frames, ignore_index=True)
    articles = articles[articles["text"].fillna("").str.strip() != ""]
    articles["text_key"] = articles["text"].map(text_key)
    articles["human"] = articles["pub_year"].isin(GOLD_YEARS)
    return articles.drop(columns="text")


def read_scores(paths: Path | Sequence[Path]) -> pd.DataFrame:
    """Detector score CSVs joined on ``text_key``; a detector's missing texts are NaN."""
    if isinstance(paths, Path):
        paths = [paths]
    merged: pd.DataFrame | None = None
    for path in paths:
        try:
            scores = pd.read_csv(path)
        except (OSError, ValueError) as exc:
            raise DetectError(f"Cannot read scores {path}: {exc}") from exc
        if merged is None:
            merged = scores
        else:
            # n_tokens counts tokens of that file's own tokenizer
            scores = scores.drop(columns="n_tokens", errors="ignore")
            merged = merged.merge(scores, on="text_key", how="outer")
    if merged is None:
        raise DetectError("No scores file given")
    return merged


def _with_scores(
    scores_paths: Path | Sequence[Path],
    articles: pd.DataFrame,
) -> pd.DataFrame:
    merged = articles.merge(read_scores(scores_paths), on="text_key", how="inner")
    missing = len(articles) - len(merged)
    if missing:
        logger.warning("%d articles have no score yet and are left out", missing)
    if merged.empty:
        raise DetectError(f"No article in the inputs has a score in {scores_paths}")
    return merged


def threshold_at_fpr(machine_scores: pd.Series, fpr: float) -> float:
    """Smallest threshold that flags at most ``fpr`` of these human texts."""
    return float(machine_scores.quantile(1 - fpr, interpolation="higher"))


def _rate_row(flags: pd.Series) -> dict[str, float | int]:
    flagged, total = int(flags.sum()), len(flags)
    low, high = wilson_interval(flagged, total)
    return {
        "n": total,
        "flagged": flagged,
        "rate": flagged / total if total else math.nan,
        "ci_low": low,
        "ci_high": high,
    }


def build_report(
    scores_path: Path | Sequence[Path],
    *,
    inputs: Sequence[Path] = DEFAULT_INPUTS,
    fprs: Sequence[float] = DEFAULT_FPRS,
) -> dict[str, pd.DataFrame]:
    """Compute the calibration, per-year and per-domain tables.

    Args:
        scores_path: CSV written by ``news_detector.detect score``, or several
            (e.g. Bielik scores and Pangram scores), joined on ``text_key``.
        inputs: The processed split CSVs (for year, domain and split).
        fprs: Target false positive rates on the 2020-2022 articles.

    Returns:
        Table name (``calibration``, ``by_year``, ``by_domain``) -> table.
    """
    data = _with_scores(scores_path, load_articles(inputs))
    detectors = [name for name in DIRECTIONS if name in data.columns]
    calibration_rows: list[dict[str, object]] = []
    year_rows: list[dict[str, object]] = []
    domain_rows: list[dict[str, object]] = []

    for detector in detectors:
        # Detectors from separate runs may cover different texts, e.g. a partial run
        frame = data[data[detector].notna()]
        calibration_mask = frame["human"] & frame["split"].isin(CALIBRATION_SPLITS)
        heldout_mask = frame["human"] & (frame["split"] == HELDOUT_SPLIT)
        if not calibration_mask.any():
            raise DetectError(
                f"No scored 2020-2022 article in train/dev to calibrate {detector} on",
            )
        machine_score = DIRECTIONS[detector] * frame[detector]
        for fpr in fprs:
            threshold = threshold_at_fpr(machine_score[calibration_mask], fpr)
            flags = machine_score > threshold
            base = {"detector": detector, "target_fpr": fpr}

            heldout = _rate_row(flags[heldout_mask])
            calibration_rows.append(
                {
                    **base,
                    "threshold": DIRECTIONS[detector] * threshold,
                    "flag_if": "below" if DIRECTIONS[detector] < 0 else "above",
                    "n_calibration": int(calibration_mask.sum()),
                    "fpr_calibration": float(flags[calibration_mask].mean()),
                    "n_heldout": heldout["n"],
                    "fpr_heldout": heldout["rate"],
                    "fpr_heldout_ci_low": heldout["ci_low"],
                    "fpr_heldout_ci_high": heldout["ci_high"],
                },
            )

            for year, index in frame.groupby("pub_year").groups.items():
                year_rows.append(
                    {
                        **base,
                        "pub_year": year,
                        **_rate_row(flags[index]),
                        "median_score": float(frame.loc[index, detector].median()),
                    },
                )

            rows = []
            for (domain, stratum), group in frame.groupby(["domain", "stratum"]):
                before = flags[group.index[group["human"]]]
                after = flags[group.index[~group["human"]]]
                flagged_before, flagged_after = int(before.sum()), int(after.sum())
                rows.append(
                    {
                        **base,
                        "domain": domain,
                        "stratum": stratum,
                        "n_2020_2022": len(before),
                        "flagged_2020_2022": flagged_before,
                        "rate_2020_2022": before.mean() if len(before) else math.nan,
                        "n_2023_2025": len(after),
                        "flagged_2023_2025": flagged_after,
                        "rate_2023_2025": after.mean() if len(after) else math.nan,
                        "p_value": (
                            fisher_greater(
                                flagged_after,
                                len(after),
                                flagged_before,
                                len(before),
                            )
                            if len(before) and len(after)
                            else math.nan
                        ),
                    },
                )
            table = pd.DataFrame(rows)
            table["excess"] = table["rate_2023_2025"] - table["rate_2020_2022"]
            tested = table["p_value"].notna()
            table.loc[tested, "q_value"] = benjamini_hochberg(
                table.loc[tested, "p_value"],
            )
            domain_rows.extend(cast(list[dict[str, object]], table.to_dict("records")))

    by_domain = pd.DataFrame(domain_rows).sort_values(
        ["detector", "target_fpr", "excess"],
        ascending=[True, True, False],
    )
    return {
        "calibration": pd.DataFrame(calibration_rows),
        "by_year": pd.DataFrame(year_rows),
        "by_domain": by_domain,
    }


def write_report(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Write each table to ``<output_dir>/<name>.csv``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, float_format="%.6g")


def report_dir(scores_path: Path) -> Path:
    """Default directory for the report of one scores file."""
    return SCORES_DIR / "reports" / scores_path.stem


def log_summary(tables: dict[str, pd.DataFrame]) -> None:
    """Log the held-out false positive rates and the yearly flag rates."""
    for row in tables["calibration"].to_dict("records"):
        logger.info(
            "%-24s target FPR %.0f%%: held-out FPR %.1f%% (n=%d), flag if %s %.4f",
            row["detector"],
            100 * row["target_fpr"],
            100 * row["fpr_heldout"],
            row["n_heldout"],
            row["flag_if"],
            row["threshold"],
        )
    by_year = tables["by_year"]
    for (detector, fpr), group in by_year.groupby(["detector", "target_fpr"]):
        rates = ", ".join(
            f"{year}: {100 * rate:.1f}%"
            for year, rate in zip(group["pub_year"], group["rate"], strict=True)
        )
        logger.info(
            "%-24s FPR %.0f%% flag rate by year: %s",
            detector,
            100 * cast(float, fpr),
            rates,
        )
