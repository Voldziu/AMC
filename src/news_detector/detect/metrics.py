"""Zero-shot detector scores computed from next-token log-probabilities.

The helper functions take tensors shaped ``(batch, positions, vocab)`` that are
already aligned with ``targets``: position ``i`` predicts ``targets[:, i]``.
``mask`` is 1.0 for real tokens and 0.0 for padding.

References:
    Hans et al. (2024), "Spotting LLMs With Binoculars", ICML.
    Bao et al. (2024), "Fast-DetectGPT", ICLR.
"""

import torch

# Columns written for every text, in this order
SCORE_COLUMNS = (
    "logppl_observer",
    "logppl_performer",
    "xppl",
    "binoculars",
    "fastdetectgpt_observer",
    "fastdetectgpt_performer",
)


def _masked_mean(values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return (values * mask).sum(dim=1) / mask.sum(dim=1)


def _target_log_probs(log_probs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    return log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)


def log_perplexity(
    log_probs: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Mean negative log-likelihood of the observed tokens, per text."""
    return _masked_mean(-_target_log_probs(log_probs, targets), mask)


def cross_perplexity(
    observer_log_probs: torch.Tensor,
    performer_log_probs: torch.Tensor,
    mask: torch.Tensor,
) -> torch.Tensor:
    """Mean cross-entropy of the performer under the observer's predictions.

    This follows the reference Binoculars code: at every position the observer's
    next-token distribution weights the performer's log-probabilities.
    """
    cross_entropy = -(observer_log_probs.exp() * performer_log_probs).sum(dim=-1)
    return _masked_mean(cross_entropy, mask)


def fast_detectgpt(
    log_probs: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """Analytic Fast-DetectGPT curvature, one model for sampling and scoring.

    The observed log-likelihood is compared with its expectation under the
    model's own distribution and divided by the standard deviation. Machine
    text sits near the mode of the model, so higher values mean "more AI".
    """
    probs = log_probs.exp()
    expected = (probs * log_probs).sum(dim=-1)
    variance = (probs * log_probs.square()).sum(dim=-1) - expected.square()
    observed = _target_log_probs(log_probs, targets)
    discrepancy = ((observed - expected) * mask).sum(dim=1)
    return discrepancy / (variance * mask).sum(dim=1).sqrt()


def score_logits(
    observer_logits: torch.Tensor,
    performer_logits: torch.Tensor,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """Compute every column of ``SCORE_COLUMNS`` for one batch.

    Args:
        observer_logits: Raw logits of the observer, ``(batch, tokens, vocab)``.
        performer_logits: Raw logits of the performer, same shape and device.
        input_ids: Token ids, right-padded, ``(batch, tokens)``.
        attention_mask: 1 for real tokens, 0 for padding, ``(batch, tokens)``.

    Returns:
        Column name -> float32 tensor of shape ``(batch,)``. Binoculars and the
        log-perplexities are lower for machine text; Fast-DetectGPT is higher.
    """
    # Instruction-tuned models sometimes append chat tokens to the vocabulary
    vocab = min(observer_logits.size(-1), performer_logits.size(-1))
    observer = torch.log_softmax(observer_logits[:, :-1, :vocab].float(), dim=-1)
    performer = torch.log_softmax(performer_logits[:, :-1, :vocab].float(), dim=-1)
    targets = input_ids[:, 1:]
    mask = attention_mask[:, 1:].float()

    logppl_performer = log_perplexity(performer, targets, mask)
    xppl = cross_perplexity(observer, performer, mask)
    return {
        "logppl_observer": log_perplexity(observer, targets, mask),
        "logppl_performer": logppl_performer,
        "xppl": xppl,
        "binoculars": logppl_performer / xppl,
        "fastdetectgpt_observer": fast_detectgpt(observer, targets, mask),
        "fastdetectgpt_performer": fast_detectgpt(performer, targets, mask),
    }
