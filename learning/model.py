"""The recurrent policy: a small CNN, a GRU cell, and four heads.

    observe(planes, scalars, hidden) -> next_hidden, spatial, belief_logits, value
    score(hidden, spatial, candidates) -> policy_logits, danger_logits

The network scores only a packed list of legal candidates; there is no dense
20,480-way head. Belief outputs are per-square marginals used for auxiliary
supervision and diagnostics; they are not a joint distribution over boards.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .features import NUM_PLANES, NUM_SCALARS

CHANNELS = 64
HIDDEN = 256
BLOCKS = 4
BELIEF_CLASSES = 7
CANDIDATE_FEATURES = HIDDEN + 2 * CHANNELS + 4 + 5  # 393
ARCHITECTURE = "cnn64x4-gru256-heads-v1"


class ResidualBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)

    def forward(self, x):
        y = F.relu(self.conv1(x))
        y = self.conv2(y)
        return F.relu(x + y)


def architecture_name(channels: int = CHANNELS, blocks: int = BLOCKS, hidden: int = HIDDEN) -> str:
    return f"cnn{channels}x{blocks}-gru{hidden}-heads-v1"


class FogPolicy(nn.Module):
    """Sizes default to the deployed v1 network (64 channels, 4 blocks, GRU 256);
    larger instances are for the ceiling study and keep the same interface."""

    def __init__(self, channels: int = CHANNELS, blocks: int = BLOCKS, hidden: int = HIDDEN,
                 cand_width: int = 128):
        super().__init__()
        self.channels, self.num_blocks, self.hidden, self.cand_width = channels, blocks, hidden, cand_width
        self.stem = nn.Conv2d(NUM_PLANES, channels, 3, padding=1)
        self.blocks = nn.ModuleList([ResidualBlock(channels) for _ in range(blocks)])
        self.project = nn.Linear(channels * 64 + NUM_SCALARS, hidden)
        self.gru = nn.GRUCell(hidden, hidden)
        # Candidate trunk shared by the policy and danger heads.
        self.cand1 = nn.Linear(hidden + 2 * channels + 4 + 5, cand_width)
        self.cand2 = nn.Linear(cand_width, cand_width // 2)
        self.policy_out = nn.Linear(cand_width // 2, 1)
        self.danger_out = nn.Linear(cand_width // 2, 1)
        self.value1 = nn.Linear(hidden, 128)
        self.value2 = nn.Linear(128, 1)
        self.belief1 = nn.Linear(channels + hidden, 64)
        self.belief2 = nn.Linear(64, BELIEF_CLASSES)

    @property
    def size_config(self) -> dict:
        return {"channels": self.channels, "blocks": self.num_blocks, "hidden": self.hidden,
                "cand_width": self.cand_width}

    @property
    def architecture(self) -> str:
        return architecture_name(self.channels, self.num_blocks, self.hidden)

    # -- one observation event --------------------------------------------
    def observe(self, planes, scalars, hidden):
        """planes [B,32,8,8], scalars [B,8], hidden [B,256] ->
        next_hidden [B,256], spatial [B,64,8,8], belief_logits [B,64,7], value [B,1]"""
        x = F.relu(self.stem(planes))
        for block in self.blocks:
            x = block(x)
        flat = torch.cat([x.flatten(1), scalars], dim=1)
        inp = F.relu(self.project(flat))
        next_hidden = self.gru(inp, hidden)
        value = torch.tanh(self.value2(F.relu(self.value1(next_hidden))))
        # Belief at each square: its spatial features plus the recurrent state.
        per_square = x.flatten(2).transpose(1, 2)                  # [B,64,C]
        h = next_hidden.unsqueeze(1).expand(-1, 64, -1)            # [B,64,H]
        belief = self.belief2(F.relu(self.belief1(torch.cat([per_square, h], dim=2))))
        return next_hidden, x, belief, value

    # -- one decision ----------------------------------------------------------
    def score(self, hidden, spatial, cand_from, cand_to, cand_promo):
        """hidden [B,256], spatial [B,64,8,8], candidates [B,M] (canonical squares,
        promotion codes) -> policy_logits [B,M], danger_logits [B,M].
        Padding is masked by the caller."""
        B, M = cand_from.shape
        per_square = spatial.flatten(2).transpose(1, 2)              # [B,64,C]
        src = torch.gather(per_square, 1, cand_from.unsqueeze(-1).expand(-1, -1, self.channels))
        dst = torch.gather(per_square, 1, cand_to.unsqueeze(-1).expand(-1, -1, self.channels))
        coords = torch.stack([
            (cand_from % 8).float() / 7.0, (cand_from // 8).float() / 7.0,
            (cand_to % 8).float() / 7.0, (cand_to // 8).float() / 7.0], dim=-1)
        promo = F.one_hot(cand_promo.clamp(0, 4), 5).float()
        h = hidden.unsqueeze(1).expand(-1, M, -1)
        feats = torch.cat([h, src, dst, coords, promo], dim=-1)      # [B,M,393]
        t = F.relu(self.cand2(F.relu(self.cand1(feats))))
        return self.policy_out(t).squeeze(-1), self.danger_out(t).squeeze(-1)

    def initial_hidden(self, batch: int, device=None):
        return torch.zeros(batch, self.hidden, device=device)


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def masked_log_softmax(logits, mask):
    """Log-probabilities over the valid candidates only; padding gets -inf."""
    logits = logits.masked_fill(~mask, float("-inf"))
    return F.log_softmax(logits, dim=-1)


def masked_entropy(log_probs, mask):
    """Entropy over the valid candidates. Padding carries -inf log-probabilities,
    and `where` still propagates NaN gradients through the unselected branch,
    so the padded entries are zeroed before any arithmetic touches them."""
    safe = log_probs.masked_fill(~mask, 0.0)
    probs = safe.exp() * mask
    return -(probs * safe).sum(-1)
