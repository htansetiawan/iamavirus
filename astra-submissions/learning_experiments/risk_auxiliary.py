"""Optional candidate-risk supervision; no dependency on an engine or trainer.

Higher logits mean greater probability of immediate king loss. Targets may use
training-only referee truth; model inputs must remain the actor's information.
This module does not modify the deployed guard, policy, or any checkpoint.
"""
from dataclasses import dataclass
import math

import torch
from torch import Tensor
from torch.nn import functional as F


@dataclass(frozen=True)
class RiskLoss:
    total: Tensor
    bce: Tensor
    separation: Tensor
    labelled_decisions: int
    contrast_decisions: int


def _weighted_mean(values: Tensor, weights: Tensor) -> Tensor:
    positive = weights > 0
    if not bool(positive.any()):
        return values[:0].sum()  # Differentiable zero, including an empty batch.
    # Rescale before summation to avoid overflow with large importance weights.
    selected = weights[positive]
    selected = selected / selected.max()
    return (values[positive] * (selected / selected.sum())).sum()


def candidate_risk_loss(
    logits: Tensor,
    fatal_targets: Tensor,
    label_mask: Tensor,
    *,
    separation_coef: float = 0.0,
    decision_weights: Tensor | None = None,
) -> RiskLoss:
    """Return decision-weighted BCE plus an optional O(B*M) ranking surrogate.

    All first three inputs have shape [decisions, candidates]. ``label_mask``
    includes only legal candidates with trustworthy immediate-fatal labels.
    Padded entries may be NaN/inf and are ignored. Valid targets must be binary.
    Rows without labels have no contribution. A row's BCE averages its labelled
    candidates; rows with both safe and fatal candidates also contribute:

        softplus(logmeanexp(z_safe) + logmeanexp(-z_fatal)).

    By Jensen's inequality this upper-bounds the mean pairwise logistic loss
    mean_{s,f} softplus(z_s - z_f), without materializing the pair matrix.
    Both losses normalize decision weights over their own eligible rows.
    All-zero weights produce differentiable zero. Weights are fixed metadata,
    not a learned input. FP16/BF16 computations are promoted to FP32.

    BCE estimates conditional risk, not certainty about a hidden board. The
    extra ranking term is not a proper calibration loss: keep it optional and
    evaluate both ranking and calibration on a separate, representative split.
    Oversampling requires distribution weights if population calibration is the
    objective. The default coefficient zero preserves the BCE objective.
    """
    if logits.ndim != 2 or logits.shape != fatal_targets.shape or logits.shape != label_mask.shape:
        raise ValueError("logits, targets, and mask must have matching [B, M] shapes")
    if not logits.is_floating_point() or label_mask.dtype != torch.bool:
        raise ValueError("logits must be floating point and label_mask boolean")
    if fatal_targets.device != logits.device or label_mask.device != logits.device:
        raise ValueError("logits, targets, and mask must be on the same device")
    if not math.isfinite(separation_coef) or separation_coef < 0:
        raise ValueError("separation_coef must be finite and nonnegative")
    if not bool(torch.isfinite(logits[label_mask]).all()):
        raise ValueError("labelled logits must be finite")
    if not bool(((fatal_targets[label_mask] == 0) | (fatal_targets[label_mask] == 1)).all()):
        raise ValueError("labelled targets must be binary")
    dtype = torch.float64 if logits.dtype == torch.float64 else torch.float32
    z = logits.to(dtype).masked_fill(~label_mask, 0)
    y = fatal_targets.to(dtype).detach().masked_fill(~label_mask, 0)
    if decision_weights is None:
        weights = z.new_ones(z.shape[0])
    else:
        if decision_weights.shape != (z.shape[0],) or decision_weights.device != z.device:
            raise ValueError("decision_weights must have shape [B] on the logits device")
        if decision_weights.requires_grad:
            raise ValueError("decision_weights must be fixed metadata")
        weights = decision_weights.to(dtype)
        if not bool((torch.isfinite(weights) & (weights >= 0)).all()):
            raise ValueError("decision_weights must be finite and nonnegative")

    count = label_mask.sum(1)
    labelled = count > 0
    bce_elements = F.binary_cross_entropy_with_logits(z, y, reduction="none")
    per_decision = bce_elements.masked_fill(~label_mask, 0).sum(1) / count.clamp_min(1)
    bce = _weighted_mean(per_decision[labelled], weights[labelled])

    safe = label_mask & (y == 0)
    fatal = label_mask & (y == 1)
    contrast = safe.any(1) & fatal.any(1)
    # Select eligible rows BEFORE logsumexp: all-masked logsumexp has undefined
    # derivatives even if a later torch.where replaces its result with zero.
    if bool(contrast.any()):
        v, s, f = z[contrast], safe[contrast], fatal[contrast]
        log_safe = v.masked_fill(~s, -torch.inf).logsumexp(1) - s.sum(1).to(dtype).log()
        log_fatal = (-v).masked_fill(~f, -torch.inf).logsumexp(1) - f.sum(1).to(dtype).log()
        separation = _weighted_mean(F.softplus(log_safe + log_fatal), weights[contrast])
    else:
        separation = z[:, :0].sum()
    total = bce if separation_coef == 0 else bce + separation_coef * separation
    return RiskLoss(total, bce, separation, int(labelled.sum()), int(contrast.sum()))
