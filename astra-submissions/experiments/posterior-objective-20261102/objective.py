"""One-step filter loss with a frozen incoming belief and all-action normalizers."""
import torch


def edge_scores(x, base, counts, history_n, parent_weight, offsets, theta):
    pieces = []
    for i, (lo, hi) in enumerate(zip(offsets[:-1], offsets[1:])):
        logits = base[lo:hi] + x[lo:hi] @ theta
        logp = logits.log_softmax(0)
        if history_n[i] >= 3:
            h = counts[lo:hi]
            # logaddexp with -inf keeps the derivative finite at count zero.
            logh = torch.where(h > 0, h.clamp_min(1).log(), torch.full_like(h, -torch.inf))
            logp = torch.logaddexp(logh, logp + theta.new_tensor(4.).log()) - (history_n[i] + 4).log()
        pieces.append(parent_weight[i] + 2 * logp)
    return torch.cat(pieces)


def loss(x, base, counts, history_n, parent_weight, offsets, consistent, positive, theta):
    assert torch.all(~positive | consistent)
    if not bool(positive.any()):
        raise ValueError('No natural positive; do not append a true world.')
    s = edge_scores(x, base, counts, history_n, parent_weight, offsets, theta)
    return torch.logsumexp(s[consistent], 0) - torch.logsumexp(s[positive], 0)
