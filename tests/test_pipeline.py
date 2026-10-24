"""End-to-end tests for the processed-dataset pipeline."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from news_detector.pipeline import PipelineError, build_dataset
from news_detector.pipeline.build import ARTICLE_FIELDS


def _article(year: int, index: int) -> dict[str, object]:
    return {
        "article_id": f"article-{year}-{index}",
        "domain": "example.pl",
        "stratum": "S1",
        "url": f"https://example.pl/{year}/{index}",
        "crawl_id": f"CC-MAIN-{year}-01",
        "warc_filename": "crawl.warc.gz",
        "warc_offset": index,
        "warc_length": 100,
        "pub_date": f"{year}-01-01",
        "pub_year": year,
        "title": f"Article {index}",
        "crawl_timestamp": f"{year}0101000000",
        "author_present": True,
        "n_words": 200,
        "languages": "pol",
        "text_sha1": f"hash-{year}-{index}",
        "text": f"Article body {year} {index}",
    }


def _write_year(input_dir: Path, year: int, rows: list[dict[str, object]]) -> None:
    directory = input_dir / str(year)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "example.pl.jsonl"
    path.write_text("".join(f"{json.dumps(row)}\n" for row in rows), encoding="utf-8")


class PipelineEndToEndTest(unittest.TestCase):
    def test_builds_deterministic_stratified_csvs_with_expected_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_dir = root / "clean"
            output_dir = root / "processed"
            for year in range(2020, 2026):
                _write_year(
                    input_dir, year, [_article(year, index) for index in range(10)]
                )

            summary = build_dataset(input_dir, output_dir)

            self.assertEqual(summary.total, 60)
            self.assertEqual(summary.split_counts, {"train": 48, "dev": 6, "test": 6})
            self.assertEqual(summary.label_counts, {"0": 30, "": 30})

            first_run = {
                split: (output_dir / f"{split}.csv").read_bytes()
                for split in ("train", "dev", "test")
            }
            build_dataset(input_dir, output_dir)
            second_run = {
                split: (output_dir / f"{split}.csv").read_bytes()
                for split in ("train", "dev", "test")
            }
            self.assertEqual(first_run, second_run)

            all_rows: list[dict[str, str]] = []
            for split in ("train", "dev", "test"):
                with (output_dir / f"{split}.csv").open(
                    encoding="utf-8", newline=""
                ) as csv_file:
                    reader = csv.DictReader(csv_file)
                    self.assertEqual(reader.fieldnames, [*ARTICLE_FIELDS, "label"])
                    all_rows.extend(reader)
            self.assertEqual(len(all_rows), 60)
            for row in all_rows:
                expected_label = "0" if int(row["pub_year"]) <= 2022 else ""
                self.assertEqual(row["label"], expected_label)

    def test_keeps_duplicate_articles_in_one_split(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_dir = root / "clean"
            output_dir = root / "processed"
            for year in range(2020, 2026):
                rows = [_article(year, index) for index in range(10)]
                if year in (2020, 2025):
                    rows[0]["article_id"] = "duplicate"
                _write_year(input_dir, year, rows)

            build_dataset(input_dir, output_dir)

            duplicate_splits = []
            for split in ("train", "dev", "test"):
                with (output_dir / f"{split}.csv").open(
                    encoding="utf-8", newline=""
                ) as csv_file:
                    if any(
                        row["article_id"] == "duplicate"
                        for row in csv.DictReader(csv_file)
                    ):
                        duplicate_splits.append(split)
            self.assertEqual(len(duplicate_splits), 1)

    def test_rejects_a_year_that_has_no_label_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_dir = root / "clean"
            output_dir = root / "processed"
            _write_year(input_dir, 2026, [_article(2026, 0)])

            with self.assertRaisesRegex(PipelineError, "unsupported year"):
                build_dataset(input_dir, output_dir)
            self.assertFalse(output_dir.exists())


if __name__ == "__main__":
    unittest.main()
