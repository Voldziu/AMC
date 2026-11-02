"""Run an observer/performer pair over texts and append per-text scores to a CSV.

The output has one row per distinct text (see ``data.text_key``). A run that
stops part-way resumes where it ended: texts already in the CSV are skipped.
A ``<output>.meta.json`` file records the models and settings; resuming with
different settings is refused, because the scores would not be comparable.
"""

import csv
import json
import math
import platform
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

import torch
import transformers
from tqdm import tqdm
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

from news_detector.detect.data import DetectError, read_texts
from news_detector.detect.metrics import SCORE_COLUMNS, score_logits
from news_detector.detect.models import ModelPair
from news_detector.utils.logger import get_logger

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

logger = get_logger(__name__)

OUTPUT_FIELDS = ("text_key", "n_tokens", *SCORE_COLUMNS)

Dtype = Literal["auto", "float32", "float16", "bfloat16"]
Quantize = Literal["none", "8bit", "4bit"]

# Both tokenizers must split this the same way for Binoculars to make sense
_TOKENIZER_PROBE = (
    "Rząd przyjął w czwartek projekt ustawy o ochronie ludności. "
    "Zmiany mają wejść w życie 1 stycznia 2025 r., poinformowało ministerstwo."
)


@dataclass(frozen=True)
class RunConfig:
    """Everything that changes the value of a score."""

    observer: str
    performer: str
    max_tokens: int
    dtype: str
    quantize: str


def _devices() -> tuple[str, str]:
    """Observer and performer devices: two GPUs when there are two."""
    if torch.cuda.is_available():
        second = min(1, torch.cuda.device_count() - 1)
        return "cuda:0", f"cuda:{second}"
    if torch.backends.mps.is_available():
        return "mps", "mps"
    return "cpu", "cpu"


def _torch_dtype(name: Dtype, device: str) -> torch.dtype:
    if name != "auto":
        return cast(torch.dtype, getattr(torch, name))
    if device.startswith("cuda"):
        # T4 GPUs (Kaggle, free Colab) have no native bfloat16
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    if device == "mps":
        return torch.bfloat16
    return torch.float32


def _load_model(
    name: str,
    device: str,
    dtype: torch.dtype,
    quantize: Quantize,
) -> PreTrainedModel:
    logger.info("Loading %s on %s (%s, quantize=%s)", name, device, dtype, quantize)
    if quantize == "none":
        model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype)
        model = model.to(device)  # type: ignore[arg-type]
    else:
        if not device.startswith("cuda"):
            raise DetectError("8-bit and 4-bit loading needs an NVIDIA GPU")
        quantization = BitsAndBytesConfig(  # type: ignore[no-untyped-call]
            load_in_8bit=quantize == "8bit",
            load_in_4bit=quantize == "4bit",
            bnb_4bit_compute_dtype=dtype,
        )
        model = AutoModelForCausalLM.from_pretrained(
            name,
            dtype=dtype,
            quantization_config=quantization,
            device_map={"": device},
        )
    model.eval()  # type: ignore[no-untyped-call]
    return cast(PreTrainedModel, model)


def _load_tokenizer(pair: ModelPair) -> PreTrainedTokenizerBase:
    observer = AutoTokenizer.from_pretrained(pair.observer)
    if pair.performer != pair.observer:
        performer = AutoTokenizer.from_pretrained(pair.performer)
        if (
            observer(_TOKENIZER_PROBE)["input_ids"]
            != performer(_TOKENIZER_PROBE)["input_ids"]
        ):
            raise DetectError(
                f"{pair.observer} and {pair.performer} tokenize text differently; "
                "Binoculars needs two models with one shared tokenizer",
            )
    if observer.pad_token_id is None:
        observer.pad_token = observer.eos_token
    return cast(PreTrainedTokenizerBase, observer)


def _check_meta(meta_path: Path, config: "DataclassInstance") -> None:
    if not meta_path.exists():
        return
    stored = json.loads(meta_path.read_text(encoding="utf-8"))["config"]
    if stored != asdict(config):
        raise DetectError(
            f"{meta_path} was written with different settings ({stored}); "
            "choose another --output or delete the old files",
        )


def _write_meta(
    meta_path: Path,
    config: "DataclassInstance",
    devices: tuple[str, str],
) -> None:
    meta = {
        "config": asdict(config),
        "devices": list(devices),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": platform.python_version(),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _scored_keys(output: Path) -> set[str]:
    if not output.exists():
        return set()
    with output.open(encoding="utf-8", newline="") as handle:
        return {row["text_key"] for row in csv.DictReader(handle)}


def _batches(
    items: list[tuple[str, list[int]]],
    batch_size: int,
) -> Iterator[list[tuple[str, list[int]]]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def _pad(
    batch: list[tuple[str, list[int]]],
    pad_id: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    width = max(len(ids) for _, ids in batch)
    input_ids = torch.full((len(batch), width), pad_id, dtype=torch.long)
    attention_mask = torch.zeros((len(batch), width), dtype=torch.long)
    for row, (_, ids) in enumerate(batch):
        input_ids[row, : len(ids)] = torch.tensor(ids, dtype=torch.long)
        attention_mask[row, : len(ids)] = 1
    return input_ids, attention_mask


def score_texts(
    pair: ModelPair,
    inputs: list[Path],
    output: Path,
    *,
    max_tokens: int = 512,
    batch_size: int = 4,
    dtype: Dtype = "auto",
    quantize: Quantize = "none",
    limit: int | None = None,
) -> int:
    """Score every not-yet-scored text of ``inputs`` and append rows to ``output``.

    Args:
        pair: Observer and performer model names on the Hugging Face Hub.
        inputs: CSV files with a ``text`` column.
        output: CSV with the scores; created or extended.
        max_tokens: Texts are cut to their first ``max_tokens`` tokens.
        batch_size: Texts per forward pass; lower it when memory runs out.
        dtype: Precision of the weights; ``auto`` picks one for the device.
        quantize: Load the weights in 8 or 4 bits (NVIDIA GPUs only).
        limit: Score at most this many new texts, e.g. for a trial run.

    Returns:
        The number of texts scored in this call.

    Raises:
        DetectError: On invalid input, mismatched tokenizers, settings that differ
            from an earlier run into ``output``, or non-finite scores.
    """
    devices = _devices()
    torch_dtype = _torch_dtype(dtype, devices[0])
    config = RunConfig(
        observer=pair.observer,
        performer=pair.performer,
        max_tokens=max_tokens,
        dtype=str(torch_dtype).removeprefix("torch."),
        quantize=quantize,
    )
    meta_path = output.with_suffix(".meta.json")
    _check_meta(meta_path, config)

    texts = read_texts(inputs)
    done = _scored_keys(output)
    # Sorting by key gives a fixed pseudo-random order, so --limit samples
    # across domains and years instead of taking the first file
    pending = sorted(key for key in texts if key not in done)
    if limit is not None:
        pending = pending[:limit]
    logger.info(
        "%d distinct texts, %d already scored, %d to score now",
        len(texts),
        len(done),
        len(pending),
    )
    if not pending:
        return 0

    tokenizer = _load_tokenizer(pair)
    encoded = tokenizer(
        [texts[key] for key in pending],
        truncation=True,
        max_length=max_tokens,
    )["input_ids"]
    # Longest first: an out-of-memory error shows up in the first batch
    items = sorted(
        zip(pending, cast(list[list[int]], encoded), strict=True),
        key=lambda item: -len(item[1]),
    )

    observer = _load_model(pair.observer, devices[0], torch_dtype, quantize)
    performer = (
        observer
        if pair.performer == pair.observer
        else _load_model(pair.performer, devices[1], torch_dtype, quantize)
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output.exists()
    _write_meta(meta_path, config, devices)
    pad_id = cast(int, tokenizer.pad_token_id)
    with (
        output.open("a", encoding="utf-8", newline="") as handle,
        tqdm(total=len(items), unit="text") as progress,
        torch.inference_mode(),
    ):
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        if write_header:
            writer.writeheader()
        for batch in _batches(items, batch_size):
            input_ids, attention_mask = _pad(batch, pad_id)
            observer_logits = observer(
                input_ids=input_ids.to(devices[0]),
                attention_mask=attention_mask.to(devices[0]),
            ).logits
            performer_logits = performer(
                input_ids=input_ids.to(devices[1]),
                attention_mask=attention_mask.to(devices[1]),
            ).logits.to(devices[0])
            scores = score_logits(
                observer_logits,
                performer_logits,
                input_ids.to(devices[0]),
                attention_mask.to(devices[0]),
            )
            values = {name: tensor.tolist() for name, tensor in scores.items()}
            for row, (key, ids) in enumerate(batch):
                record: dict[str, str | int | float] = {
                    "text_key": key,
                    "n_tokens": len(ids),
                }
                for name in SCORE_COLUMNS:
                    value = cast(float, values[name][row])
                    if not math.isfinite(value):
                        raise DetectError(
                            f"Non-finite {name} for text {key}; the {config.dtype} "
                            "weights probably overflowed, try --dtype float32 "
                            "or bfloat16",
                        )
                    record[name] = value
                writer.writerow(record)
            handle.flush()
            progress.update(len(batch))
    return len(items)
