"""Actor-only masked self-distillation with an exponential-moving-average teacher.

This board-history adaptation is inspired by BYOL's online/target networks.
Observed-content reconstruction supplies a second self-supervised signal. It
uses no true boards, game outcomes, danger annotations or expert policy labels.
The teacher sees the same causal observation history, without student masking.
No claim is made that the image-domain result transfers to this game.
"""
from __future__ import annotations

import copy
import gzip
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from learning import features
from learning_experiments.models import ModelConfig, make_model


@dataclass
class ActorHistory:
    game_id: str
    side: int
    observations: list[str]
    phases: list[int]
    plies: list[int]
    own_moves: dict[int, str]

    @classmethod
    def from_record(cls, record):
        # Deliberately select actor fields, never instantiate a target record.
        actor = record["actor"]
        if len(actor["decision_event_indices"]) != len(actor["own_actions"]):
            raise ValueError("own-action/event length mismatch")
        if not (len(actor["observations"]) == len(actor["phases"]) == len(actor["plies"])):
            raise ValueError("observation event length mismatch")
        return cls(record.get("metadata", {}).get("game_id", ""), int(actor["side"]),
                   actor["observations"], actor["phases"], actor["plies"],
                   dict(zip(actor["decision_event_indices"], actor["own_actions"])))

    def tensors(self):
        return features.replay_events(self.side, self.observations, self.phases,
                                      self.plies, self.own_moves)

    def observed_symbols(self):
        """Self-targets from literal observations: -1 fog, 0..11 piece, 12 empty.

        Do not recover these from the legacy current-view planes: features-v1
        encodes both fog and visible empties in plane 12 (plane 13 is unused).
        Both Python and the shipped C++ mirror that historical convention.
        """
        result = np.full((len(self.observations), 64), -1, np.int64)
        canonical = np.arange(64) ^ 56 if self.side == 1 else np.arange(64)
        for t, observation in enumerate(self.observations):
            result[t, canonical] = [features.relative_class(ch, self.side) for ch in observation]
        return result.reshape(-1, 8, 8)


def load_actor_histories(path: Path, limit=None):
    opener = gzip.open if str(path).endswith(".gz") else open
    out = []
    with opener(path, "rt") as handle:
        for line in handle:
            if line.strip():
                out.append(ActorHistory.from_record(json.loads(line)))
                if limit and len(out) >= limit:
                    break
    return out


def mask_observation(planes, mask):
    """Training corruption, not a claim to produce a rules-valid arena view.

    Clear *all* square channels, including last-seen information and own-move
    markers, so the answer cannot be copied from another plane at that square.
    Mark the erased square unknown/never-seen. Public scalars stay unchanged.
    """
    corrupt = planes.masked_fill(mask.unsqueeze(1), 0)
    corrupt[:, 12] = torch.where(mask, 1.0, corrupt[:, 12])
    corrupt[:, 28] = torch.where(mask, 1.0, corrupt[:, 28])
    return corrupt


@torch.no_grad()
def representation_diagnostics(representations):
    """Diversity of normalized history representations on held-out examples."""
    centered = representations.float() - representations.float().mean(0, keepdim=True)
    singular = torch.linalg.svdvals(centered)
    energy = singular.square()
    total = energy.sum()
    if total <= 1e-12:
        return {"effective_covariance_rank": 0.0, "largest_variance_share": 0.0}
    shares = energy / total
    entropy = -(shares * shares.clamp(min=1e-12).log()).sum()
    return {"effective_covariance_rank": float(entropy.exp()),
            "largest_variance_share": float(shares.max())}


class MaskedTeacherStudent(nn.Module):
    def __init__(self, config: ModelConfig, projection_dim=64):
        super().__init__()
        self.config = config
        self.student = make_model(config)
        self.teacher = copy.deepcopy(self.student)
        self.projector = nn.Sequential(nn.Linear(256, 256), nn.LayerNorm(256),
                                       nn.GELU(), nn.Linear(256, projection_dim))
        self.teacher_projector = copy.deepcopy(self.projector)
        self.predictor = nn.Sequential(nn.Linear(projection_dim, 128), nn.GELU(),
                                       nn.Linear(128, projection_dim))
        # Observed classes: 12 relative piece symbols + visibly empty.
        # Hidden ('?') is never an observed-content target.
        self.observed_decoder = nn.Linear(64 + 256, 13)
        self.teacher.requires_grad_(False)
        self.teacher_projector.requires_grad_(False)
        self.teacher.eval()
        self.teacher_projector.eval()

    def train(self, mode=True):
        super().train(mode)
        self.teacher.eval()
        self.teacher_projector.eval()
        return self

    @torch.no_grad()
    def update_teacher(self, momentum=0.996):
        if not 0 <= momentum < 1:
            raise ValueError("EMA momentum must be in [0,1)")
        for target, online in ((self.teacher, self.student),
                               (self.teacher_projector, self.projector)):
            for tp, sp in zip(target.parameters(), online.parameters()):
                tp.mul_(momentum).add_(sp, alpha=1 - momentum)
            for tb, sb in zip(target.buffers(), online.buffers()):
                tb.copy_(sb)

    def window_loss(self, planes, scalars, lengths, student_hidden, teacher_hidden,
                    generator=None, mask_fraction=0.4, reconstruction_weight=1.0,
                    *, observed_symbols):
        """[B,T,...] causal events. Hidden inputs already include the full prefix.

        Teacher and student states are separate; the student never receives the
        teacher hidden state. The EMA update is called *after* optimizer.step.
        Unknown squares provide no reconstruction labels.
        """
        if not 0 < mask_fraction < 1:
            raise ValueError("mask_fraction must be strictly between 0 and 1")
        hs, ht = student_hidden, teacher_hidden
        align_sum = planes.new_zeros(())
        rec_sum = planes.new_zeros(())
        event_count = square_count = 0
        representations = []
        reconstructed_correct = planes.new_zeros(())
        reconstructed_piece_correct = planes.new_zeros(())
        piece_count = 0
        for t in range(planes.shape[1]):
            active = t < lengths
            clean = planes[:, t]
            # Select only currently observed squares; unknown content is not a label.
            observed = observed_symbols[:, t] >= 0
            mask = (torch.rand(observed.shape, generator=generator, device=planes.device)
                    < mask_fraction) & observed & active[:, None, None]
            corrupt = mask_observation(clean, mask)
            nhs, spatial, _, _ = self.student.observe(corrupt, scalars[:, t], hs)
            hs = torch.where(active[:, None], nhs, hs)
            with torch.no_grad():
                nht, _, _, _ = self.teacher.observe(clean, scalars[:, t], ht)
                ht = torch.where(active[:, None], nht, ht)
                target = F.normalize(self.teacher_projector(ht), dim=-1)
            online = self.projector(hs)
            prediction = F.normalize(self.predictor(online), dim=-1)
            align_sum = align_sum + ((2 - 2 * (prediction * target).sum(-1)) * active).sum()
            event_count += int(active.sum())
            if active.any():
                representations.append(F.normalize(online[active], dim=-1).detach())
            per_square = spatial.flatten(2).transpose(1, 2)
            logits = self.observed_decoder(torch.cat([per_square, hs[:, None].expand(-1, 64, -1)], dim=-1))
            target_class = observed_symbols[:, t].flatten(1)
            valid = mask.flatten(1)
            if valid.any():
                rec_sum = rec_sum + F.cross_entropy(logits[valid], target_class[valid], reduction="sum")
                square_count += int(valid.sum())
                reconstructed_correct = reconstructed_correct + (logits[valid].argmax(-1) == target_class[valid]).sum()
                pieces = valid & (target_class < 12)
                piece_count += int(pieces.sum())
                reconstructed_piece_correct = reconstructed_piece_correct + (logits[pieces].argmax(-1) == target_class[pieces]).sum()
        if event_count == 0:
            raise ValueError("SSL window contains no real events")
        alignment = align_sum / event_count
        reconstruction = rec_sum / max(square_count, 1)
        loss = alignment + reconstruction_weight * reconstruction
        rep = torch.cat(representations, 0)
        spread = rep.std(dim=0, unbiased=False).mean().item()
        metrics = {"loss": loss.item(), "alignment_loss": alignment.item(),
                   "observed_reconstruction_loss": reconstruction.item(),
                   "observed_reconstruction_accuracy": reconstructed_correct.item() / max(square_count, 1),
                   "observed_piece_accuracy": reconstructed_piece_correct.item() / max(piece_count, 1),
                   "masked_observed_pieces": piece_count,
                   "events": event_count, "masked_observed_squares": square_count,
                   "normalized_projection_std": spread}
        if not self.training:
            metrics.update(representation_diagnostics(rep))
        return loss, metrics, hs, ht

    @torch.no_grad()
    def burn_prefix(self, planes, scalars, lengths):
        """Rebuild both states from actual permitted prefixes, then detach.

        Prefixes are clean in both arms; only the trained window is masked.
        Reconstructing memory from earlier observations is part of the task.
        """
        hs = self.student.initial_hidden(planes.shape[0], planes.device)
        ht = self.teacher.initial_hidden(planes.shape[0], planes.device)
        for t in range(planes.shape[1]):
            active = (t < lengths)[:, None]
            nhs = self.student.observe(planes[:, t], scalars[:, t], hs)[0]
            nht = self.teacher.observe(planes[:, t], scalars[:, t], ht)[0]
            hs, ht = torch.where(active, nhs, hs), torch.where(active, nht, ht)
        return hs.detach(), ht.detach()


def make_actor_batch(histories, window, rng):
    """Actor-only batch; the function has no parameter carrying truth labels."""
    items = [(*history.tensors(), history.observed_symbols()) for history in histories]
    if not items or any(len(p) == 0 for p, _, _ in items):
        raise ValueError("nonempty histories required")
    starts = [rng.randrange(max(1, len(p) - window + 1)) for p, _, _ in items]
    batch, prefix = len(items), max(starts)
    count = min(window, max(len(p) for p, _, _ in items))
    out = {"prefix_planes": np.zeros((batch, prefix, 32, 8, 8), np.float32),
           "prefix_scalars": np.zeros((batch, prefix, 8), np.float32),
           "prefix_lengths": np.array(starts, np.int64),
           "planes": np.zeros((batch, count, 32, 8, 8), np.float32),
           "scalars": np.zeros((batch, count, 8), np.float32),
           "observed_symbols": np.full((batch, count, 8, 8), -1, np.int64),
           "lengths": np.zeros(batch, np.int64)}
    for b, ((planes, scalars, symbols), start) in enumerate(zip(items, starts)):
        n = min(count, len(planes) - start)
        out["prefix_planes"][b, :start] = planes[:start]
        out["prefix_scalars"][b, :start] = scalars[:start]
        out["planes"][b, :n] = planes[start:start + n]
        out["scalars"][b, :n] = scalars[start:start + n]
        out["observed_symbols"][b, :n] = symbols[start:start + n]
        out["lengths"][b] = n
    return out
