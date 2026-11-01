"""Command-line entry point for the zero-shot detectors.

Subcommands:
    score          run Binoculars and Fast-DetectGPT with a model pair
    report         calibrate thresholds on 2020-2022 and tabulate flag rates
    smigiel-sample write a labelled Polish sample from PolEval 2025 Śmigiel
    smigiel-eval   AUC and recall of a scored Śmigiel sample
"""

import argparse
from pathlib import Path

from news_detector.detect.data import DEFAULT_INPUTS, SCORES_DIR, DetectError
from news_detector.detect.models import PRESETS, ModelPair
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)


def _pair(args: argparse.Namespace) -> tuple[str, ModelPair]:
    if args.observer:
        performer = args.performer or args.observer
        name = f"{args.observer}--{performer}".replace("/", "_")
        return name, ModelPair(observer=args.observer, performer=performer)
    return args.preset, PRESETS[args.preset]


def _score(args: argparse.Namespace) -> None:
    # torch is imported here so that the other subcommands work without it
    from news_detector.detect.score import score_texts

    name, pair = _pair(args)
    output = args.output or SCORES_DIR / f"{name}.csv"
    scored = score_texts(
        pair,
        args.input,
        output,
        max_tokens=args.max_tokens,
        batch_size=args.batch_size,
        dtype=args.dtype,
        quantize=args.quantize,
        limit=args.limit,
    )
    logger.info("Scored %d texts into %s", scored, output)


def _report(args: argparse.Namespace) -> None:
    from news_detector.detect.report import (
        build_report,
        log_summary,
        report_dir,
        write_report,
    )

    tables = build_report(args.scores, inputs=args.input, fprs=args.fpr)
    output_dir = args.output_dir or report_dir(args.scores)
    write_report(tables, output_dir)
    log_summary(tables)
    logger.info("Report tables written to %s", output_dir)


def _smigiel_sample(args: argparse.Namespace) -> None:
    from news_detector.detect.smigiel import prepare_sample

    path = prepare_sample(size=args.size, seed=args.seed)
    logger.info("Śmigiel sample written to %s", path)


def _smigiel_eval(args: argparse.Namespace) -> None:
    from news_detector.detect.smigiel import evaluate

    table = evaluate(args.scores)
    logger.info("Śmigiel results:\n%s", table.to_string(index=False))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zero-shot machine-generated text detectors (Binoculars, Fast-DetectGPT)."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    score = commands.add_parser("score", help="score texts with a model pair")
    score.add_argument(
        "--preset", choices=sorted(PRESETS), default="bielik-1.5b", help="model pair"
    )
    score.add_argument(
        "--observer", help="Hub name of the observer (overrides --preset)"
    )
    score.add_argument("--performer", help="Hub name of the performer")
    score.add_argument(
        "--input", type=Path, nargs="+", default=list(DEFAULT_INPUTS), help="CSV files"
    )
    score.add_argument("--output", type=Path, help="scores CSV (default: data/detect/)")
    score.add_argument("--max-tokens", type=int, default=512)
    score.add_argument("--batch-size", type=int, default=4)
    score.add_argument(
        "--dtype", choices=("auto", "float32", "float16", "bfloat16"), default="auto"
    )
    score.add_argument("--quantize", choices=("none", "8bit", "4bit"), default="none")
    score.add_argument("--limit", type=int, help="score at most N new texts")
    score.set_defaults(run=_score)

    report = commands.add_parser("report", help="calibrate and tabulate flag rates")
    report.add_argument("--scores", type=Path, required=True)
    report.add_argument("--input", type=Path, nargs="+", default=list(DEFAULT_INPUTS))
    report.add_argument("--fpr", type=float, nargs="+", default=[0.01, 0.05])
    report.add_argument("--output-dir", type=Path)
    report.set_defaults(run=_report)

    sample = commands.add_parser("smigiel-sample", help="labelled Śmigiel sample")
    sample.add_argument("--size", type=int, default=1000)
    sample.add_argument("--seed", type=int, default=42)
    sample.set_defaults(run=_smigiel_sample)

    evaluation = commands.add_parser("smigiel-eval", help="evaluate a Śmigiel run")
    evaluation.add_argument("--scores", type=Path, required=True)
    evaluation.set_defaults(run=_smigiel_eval)
    return parser


def main() -> None:
    """Run one subcommand from the command line."""
    parser = _parser()
    args = parser.parse_args()
    try:
        args.run(args)
    except DetectError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
