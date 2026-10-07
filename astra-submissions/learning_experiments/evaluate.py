"""Held-out task metrics over complete histories, exactly one pass per decision."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import torch

from learning import dataset as ds


def recall_at_fpr(probability, target, rates=(0.01, 0.05, 0.1)):
    """Descriptive empirical ROC points; do not use as deployment calibration.

    Equal-score ties enter together, so an apparently perfect point cannot be
    fabricated by sorting positive labels ahead of equally scored negatives.
    """
    p, y = np.asarray(probability), np.asarray(target, dtype=bool)
    positives, negatives = int(y.sum()), int((~y).sum())
    if not positives or not negatives:
        return {str(rate): {"recall": None, "actual_fpr": None, "threshold": None} for rate in rates}
    order = np.argsort(-p, kind="stable")
    scores, labels = p[order], y[order]
    ends = np.r_[np.flatnonzero(scores[:-1] != scores[1:]), len(scores) - 1]
    tp, fp = np.cumsum(labels)[ends], np.cumsum(~labels)[ends]
    result = {}
    for rate in rates:
        eligible = np.flatnonzero(fp <= int(np.floor(rate * negatives)))
        if len(eligible):
            index = eligible[-1]
            result[str(rate)] = {"recall": float(tp[index] / positives),
                                 "actual_fpr": float(fp[index] / negatives),
                                 "threshold": float(scores[ends[index]])}
        else:
            result[str(rate)] = {"recall": 0.0, "actual_fpr": 0.0, "threshold": None}
    return result


@dataclass
class Totals:
    sums: dict = field(default_factory=lambda: defaultdict(float))
    counts: dict = field(default_factory=lambda: defaultdict(int))
    danger: list = field(default_factory=list)
    danger_target: list = field(default_factory=list)

    def add(self, d, log_policy, danger, belief, value):
        self.counts["decisions"] += 1
        if d["policy_valid"]:
            self.counts["policy"] += 1
            self.sums["policy_nll"] -= float(log_policy[d["demonstrated"]])
            self.sums["policy_accuracy"] += int(log_policy.argmax() == d["demonstrated"])
        if d["value_valid"]:
            self.counts["value"] += 1
            self.sums["value_mse"] += float((value - d["return"]) ** 2)
        if d["danger_valid"]:
            y = d["danger"]
            self.counts["danger_candidates"] += len(y)
            self.counts["danger_positives"] += int(y.sum())
            self.sums["danger_brier"] += float(np.square(danger - y).sum())
            self.sums["danger_false_negatives_at_0.5"] += int(((danger < 0.5) & (y > 0.5)).sum())
            self.danger.append(danger)
            self.danger_target.append(y)
        if d["belief_valid"]:
            mask, truth = d["belief_mask"], d["belief"]
            sq = np.flatnonzero(mask)
            if len(sq):
                probability = belief[sq, truth[sq]].clip(1e-12, 1)
                nll = -np.log(probability)
                enemy = truth[sq] != 6
                self.counts["hidden_squares"] += len(sq)
                self.counts["hidden_enemy_squares"] += int(enemy.sum())
                self.sums["hidden_nll"] += float(nll.sum())
                self.sums["hidden_enemy_nll"] += float(nll[enemy].sum())
                onehot = np.eye(7)[truth[sq]]
                self.sums["hidden_brier"] += float(np.square(belief[sq] - onehot).sum())
                predicted = belief[sq].argmax(-1)
                for kind in range(6):
                    is_kind = truth[sq] == kind
                    self.counts[f"hidden_piece_{kind}"] += int(is_kind.sum())
                    self.sums[f"hidden_piece_{kind}_recall"] += int((predicted[is_kind] == kind).sum())
                    self.sums[f"hidden_piece_{kind}_nll"] += float(nll[is_kind].sum())

    def summary(self, include_roc=True):
        denominator = {"policy_nll": "policy", "policy_accuracy": "policy", "value_mse": "value",
                       "danger_brier": "danger_candidates", "danger_false_negatives_at_0.5": "danger_positives",
                       "hidden_nll": "hidden_squares", "hidden_enemy_nll": "hidden_enemy_squares",
                       "hidden_brier": "hidden_squares"}
        denominator.update({f"hidden_piece_{k}_{metric}": f"hidden_piece_{k}"
                            for k in range(6) for metric in ("nll", "recall")})
        metrics = {k: self.sums[k] / self.counts[n] if self.counts[n] else None
                   for k, n in denominator.items()}
        out = {"counts": dict(self.counts), "metrics": metrics,
               "sums": dict(self.sums), "piece_order": "PNBRQK"}
        if include_roc and self.danger:
            out["danger_recall_at_fpr"] = recall_at_fpr(np.concatenate(self.danger), np.concatenate(self.danger_target))
        return out


def evaluate(model, episodes, device):
    """No sampled cuts, no state reset within a game, no duplicated final event."""
    was_training = model.training
    model.eval()
    groups = defaultdict(Totals)
    games = defaultdict(Totals)
    seen = set()
    with torch.no_grad():
        for episode in episodes:
            planes, scalars, decisions = ds.episode_tensors(episode)
            by_event = {d["event"]: d for d in decisions}
            if len(by_event) != len(decisions):
                raise ValueError("duplicate decision in episode")
            hidden = model.initial_hidden(1, device)
            for event in range(len(planes)):
                p = torch.from_numpy(planes[event:event + 1]).to(device)
                s = torch.from_numpy(scalars[event:event + 1]).to(device)
                hidden, spatial, belief, value = model.observe(p, s, hidden)
                d = by_event.get(event)
                if d is None or not d["count"]:
                    continue
                key = (episode.metadata.game_id, episode.actor.side, event)
                if key in seen:
                    raise ValueError(f"repeated evaluation decision {key}")
                seen.add(key)
                candidates = [torch.from_numpy(d[k][None]).to(device) for k in ("from", "to", "promo")]
                policy, danger = model.score(hidden, spatial, *candidates)
                predictions = (policy.log_softmax(-1)[0].cpu().numpy(),
                               danger.sigmoid()[0].cpu().numpy(),
                               belief.softmax(-1)[0].cpu().numpy(), value.item())
                ply = episode.actor.plies[event]
                phase = "opening" if ply < 20 else "middle" if ply < 60 else "late"
                for name in ("all", f"player:{episode.metadata.player_id}",
                             f"opponent:{episode.metadata.opponent_id}", f"phase:{phase}"):
                    groups[name].add(d, *predictions)
                games[episode.metadata.game_id].add(d, *predictions)
    model.train(was_training)
    return {"unique_decisions": len(seen), "games": len(games), "episodes": len(episodes),
            "groups": {k: v.summary() for k, v in groups.items()},
            "by_game": {k: v.summary(include_roc=False) for k, v in games.items()},
            "limitations": ["Empirical ROC points are descriptive, not a calibrated veto.",
                            "Replay task metrics do not establish an Elo improvement."]}
