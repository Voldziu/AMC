"""Score texts with Pangram's EditLens classifier (Thai et al., ICLR 2026).

EditLens is Llama-3.2-3B with a LoRA adapter and a classification head over
``n`` buckets, from 0 (human) to ``n - 1`` (AI). The score is the expected
bucket scaled to [0, 1]; higher means more machine-like. The model is trained
on English text only. Both the base model and the adapter are gated on the
Hugging Face Hub: accept their licences and log in before the first run.

The output CSV has one row per distinct text and resumes like ``score.py``.
"""

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import torch
from huggingface_hub import hf_hub_download
from peft import PeftModel
from safetensors import safe_open
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
)

from news_detector.detect.data import DetectError, read_texts
from news_detector.detect.score import (
    Dtype,
    Quantize,
    _batches,
    _check_meta,
    _devices,
    _pad,
    _scored_keys,
    _torch_dtype,
    _write_meta,
)
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

BASE_MODEL = "meta-llama/Llama-3.2-3B"
ADAPTER = "pangram/editlens_Llama-3.2-3B"
PANGRAM_FIELDS = ("text_key", "pangram_score", "pangram_bucket")


@dataclass(frozen=True)
class PangramConfig:
    """Everything that changes the value of a score."""

    base_model: str
    adapter: str
    max_tokens: int
    dtype: str
    quantize: str


class NormedLinear(torch.nn.Module):
    """The head EditLens was trained with: LayerNorm followed by a bias-free Linear."""

    def __init__(
        self,
        hidden_size: int,
        num_labels: int,
        device: torch.device | str,
    ) -> None:
        super().__init__()
        self.norm = torch.nn.LayerNorm(hidden_size, device=device)
        self.linear = torch.nn.Linear(
            hidden_size,
            num_labels,
            bias=False,
            device=device,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # The head stays in float32 whatever the precision of the backbone
        return cast(torch.Tensor, self.linear(self.norm(x.float())))


def prepare_text(text: str) -> str:
    """Lower-case and collapse whitespace, as EditLens's ``clean_text`` does."""
    return " ".join(text.lower().split())


def bucket_scores(logits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Expected bucket scaled to [0, 1] and the most likely bucket of each row."""
    probabilities = torch.softmax(logits.float(), dim=-1)
    buckets = torch.arange(logits.shape[-1], device=logits.device, dtype=torch.float32)
    score = (probabilities @ buckets) / (logits.shape[-1] - 1)
    return score, probabilities.argmax(dim=-1)


def _n_buckets() -> int:
    """Read the head size from the adapter, as the EditLens inference script does."""
    path = hf_hub_download(ADAPTER, "adapter_model.safetensors")
    with safe_open(path, framework="pt") as handle:
        for key in handle.keys():  # noqa: SIM118  safe_open is not iterable
            if "score" in key and "linear.weight" in key:
                return int(handle.get_slice(key).get_shape()[0])
    raise DetectError(f"No classification head found in the adapter {ADAPTER}")


def _load_model(
    n_buckets: int,
    pad_id: int,
    device: str,
    dtype: torch.dtype,
    quantize: Quantize,
) -> Any:
    logger.info("Loading %s + %s on %s (%s)", BASE_MODEL, ADAPTER, device, quantize)
    options: dict[str, Any] = {"num_labels": n_buckets, "dtype": dtype}
    if quantize != "none":
        if not device.startswith("cuda"):
            raise DetectError("8-bit and 4-bit loading needs an NVIDIA GPU")
        options["quantization_config"] = BitsAndBytesConfig(  # type: ignore[no-untyped-call]
            load_in_8bit=quantize == "8bit",
            load_in_4bit=quantize == "4bit",
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,
        )
        options["device_map"] = {"": device}
    base = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, **options)
    base.config.pad_token_id = pad_id
    # The adapter's saved head weights only fit this architecture
    base.score = NormedLinear(
        base.config.hidden_size,
        n_buckets,
        next(base.parameters()).device,
    )
    model = PeftModel.from_pretrained(base, ADAPTER)
    if quantize == "none":
        model = model.to(device)
    model.eval()
    return model


def score_pangram(
    inputs: list[Path],
    output: Path,
    *,
    max_tokens: int = 1024,
    batch_size: int = 4,
    dtype: Dtype = "auto",
    quantize: Quantize = "none",
    limit: int | None = None,
) -> int:
    """Score every not-yet-scored text of ``inputs`` and append rows to ``output``.

    Args:
        inputs: CSV files with a ``text`` column.
        output: CSV with ``pangram_score`` and ``pangram_bucket``; created or extended.
        max_tokens: Texts are cut to their first ``max_tokens`` tokens.
        batch_size: Texts per forward pass; lower it when memory runs out.
        dtype: Precision of the weights; ``auto`` picks one for the device.
        quantize: Load the weights in 8 or 4 bits (NVIDIA GPUs only).
        limit: Score at most this many new texts, e.g. for a trial run.

    Returns:
        The number of texts scored in this call.

    Raises:
        DetectError: On invalid input, settings that differ from an earlier run
            into ``output``, or non-finite scores.
    """
    device = _devices()[0]
    torch_dtype = _torch_dtype(dtype, device)
    config = PangramConfig(
        base_model=BASE_MODEL,
        adapter=ADAPTER,
        max_tokens=max_tokens,
        dtype=str(torch_dtype).removeprefix("torch."),
        quantize=quantize,
    )
    meta_path = output.with_suffix(".meta.json")
    _check_meta(meta_path, config)

    texts = read_texts(inputs)
    done = _scored_keys(output)
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

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded = tokenizer(
        [prepare_text(texts[key]) for key in pending],
        truncation=True,
        max_length=max_tokens,
    )["input_ids"]
    # Longest first: an out-of-memory error shows up in the first batch
    items = sorted(
        zip(pending, cast(list[list[int]], encoded), strict=True),
        key=lambda item: -len(item[1]),
    )

    if device.startswith("cuda"):
        torch.cuda.empty_cache()
    model = _load_model(
        _n_buckets(),
        cast(int, tokenizer.pad_token_id),
        device,
        torch_dtype,
        quantize,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output.exists()
    _write_meta(meta_path, config, (device, device))
    with (
        output.open("a", encoding="utf-8", newline="") as handle,
        tqdm(total=len(items), unit="text") as progress,
        torch.inference_mode(),
    ):
        writer = csv.DictWriter(handle, fieldnames=PANGRAM_FIELDS)
        if write_header:
            writer.writeheader()
        for batch in _batches(items, batch_size):
            input_ids, attention_mask = _pad(batch, cast(int, tokenizer.pad_token_id))
            logits = model(
                input_ids=input_ids.to(device),
                attention_mask=attention_mask.to(device),
            ).logits
            scores, buckets = bucket_scores(logits)
            for (key, _), score, bucket in zip(
                batch,
                scores.tolist(),
                buckets.tolist(),
                strict=True,
            ):
                if not math.isfinite(score):
                    raise DetectError(
                        f"Non-finite score for text {key}; the {config.dtype} "
                        "weights probably overflowed, try --dtype float32 or bfloat16",
                    )
                writer.writerow(
                    {"text_key": key, "pangram_score": score, "pangram_bucket": bucket},
                )
            handle.flush()
            progress.update(len(batch))
    return len(items)
