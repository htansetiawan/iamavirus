"""Stage B: recurrent PPO in the simulator, initialised from replay pretraining.

    python -m learning.train_ppo --init checkpoints/pretrain/best.pt \
        --config learning/configs/replay_ppo.yaml --output checkpoints/ppo

Per iteration: freeze the actor, collect `rollout_decisions` learner decisions
against the league (finishing every game), compute GAE over same-player
transitions, then run `epochs_per_batch` passes of clipped-ratio updates over
contiguous 64-event windows with the recurrent prefix reconstructed under the
current parameters. Replays never enter the ratio; they are not on-policy data.

    rho = exp(log pi_new(a|h) - logp_old)
    L = -mean(min(rho A, clip(rho, 0.8, 1.2) A)) + 0.5 L_value - 0.01 entropy
        + 0.1 L_belief + 0.1 L_danger
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from . import dataset as ds
from . import rollouts
from .model import FogPolicy, masked_entropy, masked_log_softmax
from .pretrain import Checkpointer, burn_in, load_config, load_model, run_sequence, to_device


def ppo_batch(episodes: list[rollouts.RolloutEpisode], window: int, rng: random.Random, gamma, lam):
    """A SequenceBatch plus the PPO arrays aligned with its decisions."""
    batch = ds.make_batch([e.episode for e in episodes], window, rng)
    # Recover window starts to align per-decision PPO arrays.
    starts = batch.prefix_lengths
    action, old_logp, old_value, adv, ret = [], [], [], [], []
    per_episode = [rollouts.compute_gae(e, gamma, lam) for e in episodes]
    for b, episode in enumerate(episodes):
        events = episode.episode.actor.decision_event_indices
        advantages, returns = per_episode[b]
        start, length = int(starts[b]), int(batch.window_lengths[b])
        for k, event in enumerate(events):
            if start <= event < start + length:
                action.append(episode.action_index[k])
                old_logp.append(episode.old_log_prob[k])
                old_value.append(episode.old_value[k])
                adv.append(advantages[k])
                ret.append(returns[k])
    extras = {"action": np.array(action, dtype=np.int64), "old_logp": np.array(old_logp, dtype=np.float32),
              "old_value": np.array(old_value, dtype=np.float32), "advantage": np.array(adv, dtype=np.float32),
              "ppo_return": np.array(ret, dtype=np.float32)}
    assert len(action) == batch.decision_seq.shape[0]
    return batch, extras


def ppo_losses(model: FogPolicy, batch: dict, cfg: dict):
    hidden0 = burn_in(model, batch)
    hiddens, spatials, beliefs, values = run_sequence(
        model, batch["planes"], batch["scalars"], batch["window_lengths"], hidden0)
    seq, step = batch["decision_seq"], batch["decision_step"]
    D = seq.shape[0]
    if D == 0:
        zero = torch.zeros((), device=hiddens.device)
        return zero, {"decisions": 0}
    h, sp, bl, v = hiddens[seq, step], spatials[seq, step], beliefs[seq, step], values[seq, step]
    mask = batch["cand_mask"]
    policy_logits, danger_logits = model.score(h, sp, batch["cand_from"], batch["cand_to"], batch["cand_promo"])
    log_probs = masked_log_softmax(policy_logits, mask)
    new_logp = log_probs.gather(1, batch["action"].unsqueeze(1)).squeeze(1)
    ratio = torch.exp(new_logp - batch["old_logp"])
    adv = batch["advantage"]
    adv = (adv - adv.mean()) / (adv.std() + 1e-8) if D > 1 else adv
    clip = cfg["clip_ratio"]
    actor_loss = -torch.min(ratio * adv, torch.clamp(ratio, 1 - clip, 1 + clip) * adv).mean()
    value_loss = F.mse_loss(v, batch["ppo_return"])
    entropy = masked_entropy(log_probs, mask).mean()
    # Auxiliary heads, same definitions as stage A.
    bm = batch["belief_mask"]
    ce = F.cross_entropy(bl.reshape(-1, 7), batch["belief_classes"].reshape(-1), reduction="none").reshape(D, 64)
    per = (ce * bm).sum(1) / bm.sum(1).clamp(min=1)
    belief_loss = per[bm.any(1)].mean() if bm.any() else torch.zeros((), device=h.device)
    bce = F.binary_cross_entropy_with_logits(danger_logits, batch["danger"], reduction="none")
    danger_loss = ((bce * mask).sum(1) / mask.sum(1).clamp(min=1)).mean()
    total = (actor_loss + cfg["value_coefficient"] * value_loss - cfg["entropy_coefficient"] * entropy
             + cfg["belief_coefficient"] * belief_loss + cfg["danger_coefficient"] * danger_loss)
    with torch.no_grad():
        approx_kl = (batch["old_logp"] - new_logp).mean().item()
        clip_fraction = ((ratio - 1).abs() > clip).float().mean().item()
        var_y = batch["ppo_return"].var()
        explained = 1 - (batch["ppo_return"] - v).var() / (var_y + 1e-8) if D > 1 else torch.zeros(())
    metrics = {"decisions": D, "loss": total.item(), "actor_loss": actor_loss.item(),
               "value_loss": value_loss.item(), "entropy": entropy.item(), "belief_loss": belief_loss.item(),
               "danger_loss": danger_loss.item(), "approx_kl": approx_kl, "clip_fraction": clip_fraction,
               "value_explained_variance": float(explained)}
    return total, metrics


def train(init: Path, config_path: Path, output: Path, iterations: int, rollout_decisions: int | None,
          games_in_flight: int | None, opponents: list[str] | None, seed: int = 1) -> Path:
    cfg = load_config(config_path)["ppo"]
    if rollout_decisions:
        cfg["rollout_decisions"] = rollout_decisions
    if games_in_flight:
        cfg["games_in_flight"] = games_in_flight
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model, payload = load_model(init, device)
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"])
    checkpointer = Checkpointer(output)
    log = open(output / "ppo_log.jsonl", "a")
    # The league starts with the pretrained checkpoint as the recent opponent.
    frozen: dict[str, FogPolicy] = {"ckpt0": copy.deepcopy(model).eval()}
    league = rollouts.League(recent=["ckpt0"], older=[],
                             fixed=opponents or cfg["league"]["fixed_opponents"],
                             recent_share=cfg["league"]["recent_share"],
                             older_share=cfg["league"]["older_share"],
                             fixed_share=cfg["league"]["fixed_share"])
    total_decisions = 0
    manifest = {"content_sha256": payload.get("dataset_manifest_sha256"),
                "feature_version": payload.get("feature_version"), "action_version": payload.get("action_version"),
                "rules_fingerprint": payload.get("rules_fingerprint")}
    for iteration in range(iterations):
        actor = copy.deepcopy(model).eval()
        collector = rollouts.Collector(actor, frozen, device, league, cfg["games_in_flight"], cfg["max_plies"])
        episodes, stats = collector.collect(cfg["rollout_decisions"], seed * 1000 + iteration)
        total_decisions += stats["decisions"]
        print(f"iter {iteration}: {stats['games']} games, {stats['decisions']} decisions, "
              f"{stats['decisions_per_second']:.1f} dec/s, score {stats['score_rate']:.3f} "
              f"by opponent {json.dumps(stats['by_opponent'])}", file=sys.stderr)
        episodes = [e for e in episodes if len(e.action_index) > 0]
        model.train()
        updates = 0
        stop = False
        for epoch in range(cfg["epochs_per_batch"]):
            order = list(range(len(episodes)))
            rng.shuffle(order)
            for start in range(0, len(order), cfg["sequences_per_minibatch"]):
                group = [episodes[i] for i in order[start:start + cfg["sequences_per_minibatch"]]]
                batch, extras = ppo_batch(group, cfg["window"], rng, cfg["gamma"], cfg["gae_lambda"])
                tensors = to_device(batch, device)
                for k, v in extras.items():
                    tensors[k] = torch.from_numpy(v).to(device)
                loss, metrics = ppo_losses(model, tensors, cfg)
                if metrics["decisions"] == 0:
                    continue
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
                optimizer.step()
                updates += 1
                metrics.update({"iteration": iteration, "epoch": epoch, "update": updates,
                                "grad_norm": float(grad_norm), "total_decisions": total_decisions})
                log.write(json.dumps(metrics) + "\n")
                if metrics["approx_kl"] > cfg["target_kl"]:
                    print(f"  early stop: kl {metrics['approx_kl']:.4f} > {cfg['target_kl']}", file=sys.stderr)
                    stop = True
                    break
            if stop:
                break
        log.write(json.dumps({"iteration": iteration, "rollout": stats, "updates": updates}) + "\n")
        log.flush()
        # League maintenance: the new actor becomes the recent opponent, the
        # previous recent one joins the older pool.
        key = f"ckpt{iteration + 1}"
        frozen[key] = copy.deepcopy(model).eval()
        league.older = league.older + league.recent
        league.recent = [key]
        if len(league.older) > 6:
            drop = league.older.pop(0)
            frozen.pop(drop, None)
        checkpointer.save(model, optimizer, total_decisions, iteration + 1, cfg, manifest, "latest",
                          {"rollout": stats, "updates": updates, "parent": str(init)})
        checkpointer.save(model, None, total_decisions, iteration + 1, cfg, manifest, f"iter{iteration + 1}",
                          {"rollout": stats, "updates": updates, "parent": str(init)})
    log.close()
    return output / "latest.pt"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--init", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("learning/configs/replay_ppo.yaml"))
    parser.add_argument("--output", type=Path, default=Path("checkpoints/ppo"))
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--rollout-decisions", type=int, default=None)
    parser.add_argument("--games-in-flight", type=int, default=None)
    parser.add_argument("--opponents", nargs="*", default=None, help="fixed opponents, e.g. capture-greedy cpp:20000")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    path = train(args.init, args.config, args.output, args.iterations, args.rollout_decisions,
                 args.games_in_flight, args.opponents, args.seed)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
