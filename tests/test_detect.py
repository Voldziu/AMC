"""Tests for the detector scores, threshold calibration and report tables."""

import csv
import importlib.util
import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from news_detector.detect.data import read_texts, text_key
from news_detector.detect.report import (
    benjamini_hochberg,
    build_report,
    fisher_greater,
    threshold_at_fpr,
    wilson_interval,
)

HAS_TORCH = importlib.util.find_spec("torch") is not None


class StatisticsTest(unittest.TestCase):
    def test_fisher_matches_hypergeometric_tail(self) -> None:
        # P(X >= 5) with 5 flagged of 20 and 10 drawn: C(15, 5) / C(20, 10)
        self.assertAlmostEqual(fisher_greater(5, 10, 0, 10), 3003 / 184756)
        self.assertAlmostEqual(fisher_greater(0, 10, 5, 10), 1.0)

    def test_wilson_interval_stays_in_unit_range(self) -> None:
        low, high = wilson_interval(0, 50)
        self.assertAlmostEqual(low, 0.0)
        self.assertGreater(high, 0.0)
        self.assertTrue(math.isnan(wilson_interval(0, 0)[0]))

    def test_benjamini_hochberg(self) -> None:
        q = benjamini_hochberg(pd.Series([0.01, 0.04, 0.03, 0.5]))
        self.assertEqual(q.round(4).tolist(), [0.04, 0.0533, 0.0533, 0.5])

    def test_threshold_flags_at_most_target_share(self) -> None:
        scores = pd.Series(range(100), dtype=float)
        threshold = threshold_at_fpr(scores, 0.05)
        self.assertLessEqual(float((scores > threshold).mean()), 0.05)


def _write_articles(directory: Path) -> list[Path]:
    paths = []
    for split, count in (("train", 80), ("dev", 10), ("test", 10)):
        path = directory / f"{split}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=("domain", "stratum", "pub_year", "label", "text"),
            )
            writer.writeheader()
            for index in range(count):
                year = 2020 + index % 6
                writer.writerow(
                    {
                        "domain": "farm.pl" if index % 2 else "paper.pl",
                        "stratum": "S1",
                        "pub_year": year,
                        "label": "0" if year < 2023 else "",
                        "text": f"{split} text {index}",
                    }
                )
        paths.append(path)
    return paths


class ReportTest(unittest.TestCase):
    def test_duplicate_texts_are_read_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "texts.csv"
            path.write_text("text\nAla ma kota\nAla ma kota\n\n", encoding="utf-8")
            self.assertEqual(list(read_texts([path])), [text_key("Ala ma kota")])

    def test_report_flags_the_domain_that_changed_after_2023(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            inputs = _write_articles(root)
            rows = []
            for path in inputs:
                for article in pd.read_csv(path).itertuples():
                    machine = article.domain == "farm.pl" and article.pub_year >= 2023
                    # Distinct human scores in [1.0, 1.1); machine text scores low
                    rows.append(
                        {
                            "text_key": text_key(article.text),
                            "binoculars": 0.5 if machine else 1.0 + len(rows) / 1000,
                        }
                    )
            scores = root / "scores.csv"
            pd.DataFrame(rows).to_csv(scores, index=False)

            tables = build_report(scores, inputs=inputs, fprs=[0.05])

            calibration = tables["calibration"].iloc[0]
            self.assertEqual(calibration["flag_if"], "below")
            self.assertLessEqual(calibration["fpr_calibration"], 0.05)
            by_domain = tables["by_domain"].set_index("domain")
            self.assertEqual(by_domain.loc["farm.pl", "rate_2023_2025"], 1.0)
            self.assertLess(by_domain.loc["farm.pl", "p_value"], 0.01)
            self.assertLess(by_domain.loc["paper.pl", "rate_2023_2025"], 0.5)


@unittest.skipUnless(HAS_TORCH, "needs the optional 'detect' dependency group")
class MetricsTest(unittest.TestCase):
    def test_vectorised_scores_match_a_plain_loop(self) -> None:
        import torch

        from news_detector.detect.metrics import score_logits

        generator = torch.Generator().manual_seed(0)
        observer_logits = torch.randn(2, 6, 11, generator=generator)
        performer_logits = torch.randn(2, 6, 11, generator=generator)
        input_ids = torch.randint(0, 11, (2, 6), generator=generator)
        attention_mask = torch.tensor([[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 0, 0]])

        scores = score_logits(
            observer_logits, performer_logits, input_ids, attention_mask
        )

        for row in range(2):
            length = int(attention_mask[row].sum())
            observer = torch.log_softmax(observer_logits[row, : length - 1], dim=-1)
            performer = torch.log_softmax(performer_logits[row, : length - 1], dim=-1)
            targets = input_ids[row, 1:length]
            ppl = -sum(float(performer[i, t]) for i, t in enumerate(targets)) / (
                length - 1
            )
            xppl = -sum(
                float((observer[i].exp() * performer[i]).sum())
                for i in range(length - 1)
            ) / (length - 1)
            self.assertAlmostEqual(float(scores["logppl_performer"][row]), ppl, 5)
            self.assertAlmostEqual(float(scores["xppl"][row]), xppl, 5)
            self.assertAlmostEqual(float(scores["binoculars"][row]), ppl / xppl, 5)

            probs = observer.exp()
            expected = (probs * observer).sum(dim=-1)
            variance = (probs * observer.square()).sum(dim=-1) - expected.square()
            observed = observer[torch.arange(length - 1), targets]
            curvature = float((observed - expected).sum() / variance.sum().sqrt())
            self.assertAlmostEqual(
                float(scores["fastdetectgpt_observer"][row]), curvature, 5
            )


if __name__ == "__main__":
    unittest.main()
