"""Observer/performer language-model pairs for the zero-shot detectors."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPair:
    """Two causal language models that share one tokenizer.

    As in the Binoculars paper, the observer is a base model and the performer
    its instruction-tuned variant. Fast-DetectGPT is computed for each of them.
    """

    observer: str
    performer: str


# Memory figures are for the weights of both models together.
PRESETS: dict[str, ModelPair] = {
    # About 7 GB in 16-bit precision
    "bielik-1.5b": ModelPair(
        observer="speakleash/Bielik-1.5B-v3",
        performer="speakleash/Bielik-1.5B-v3.0-Instruct",
    ),
    # About 19 GB in 16-bit precision; the best unsupervised pair at PolEval 2025
    "bielik-4.5b": ModelPair(
        observer="speakleash/Bielik-4.5B-v3",
        performer="speakleash/Bielik-4.5B-v3.0-Instruct",
    ),
}
