"""Stage A: supervised learning from replays.

    python -m learning.pretrain --config learning/configs/replay_ppo.yaml \
        --manifest data/manifests/v1.json --output checkpoints/pretrain

Objective (each term averaged over its own valid labels, then weighted):

    L = 1.0 * CE_policy + 1.0 * CE_hidden_belief + 1.0 * BCE_king_danger
      + 0.25 * MSE_value

A minibatch is `sequences_per_batch` windows of `window` observation events.
At each window boundary the hidden state is reconstructed from the episode's
first event under the current parameters with gradients disabled, detached, and
training proceeds through the window. Memory is never reset at a sampled cut.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml

from . import dataset as ds
from .model import FogPolicy, masked_entropy, masked_log_softmax, parameter_count, ARCHITECTURE


def load_config(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def to_device(batch: ds.SequenceBatch, device) -> dict:
    out = {}
    for name, value in batch.__dict__.items():
        tensor = torch.from_numpy(np.ascontiguousarray(value))
        out[name] = tensor.to(device, non_blocking=True)
    return out


def run_sequence(model: FogPolicy, planes, scalars, lengths, hidden):
    """Steps the recurrence over [B,T,...]; returns hidden per step [B,T,H],
    spatial per step [B,T,C,8,8], belief logits [B,T,64,7], values [B,T]."""
    B, T = planes.shape[:2]
    hiddens, spatials, beliefs, values = [], [], [], []
    for t in range(T):
        active = (t < lengths).float().unsqueeze(1)
        next_hidden, spatial, belief, value = model.observe(planes[:, t], scalars[:, t], hidden)
        # Padded steps keep the previous state untouched.
        hidden = active * next_hidden + (1 - active) * hidden
        hiddens.append(hidden)
        spatials.append(spatial)
        beliefs.append(belief)
        values.append(value.squeeze(-1))
    return (torch.stack(hiddens, 1), torch.stack(spatials, 1),
            torch.stack(beliefs, 1), torch.stack(values, 1))


def burn_in(model: FogPolicy, batch: dict) -> torch.Tensor:
    """Hidden state at the start of each window, from the full episode prefix."""
    B = batch["planes"].shape[0]
    hidden = model.initial_hidden(B, batch["planes"].device)
    P = batch["prefix_planes"].shape[1]
    if P == 0:
        return hidden
    with torch.no_grad():
        hiddens, _, _, _ = run_sequence(model, batch["prefix_planes"], batch["prefix_scalars"],
                                        batch["prefix_lengths"], hidden)
        lengths = batch["prefix_lengths"]
        has_prefix = lengths > 0
        last = (lengths - 1).clamp(min=0)
        picked = hiddens[torch.arange(B, device=hidden.device), last]
        hidden = torch.where(has_prefix.unsqueeze(1), picked, hidden)
    return hidden.detach()


def compute_losses(model: FogPolicy, batch: dict, weights: dict) -> tuple[torch.Tensor, dict]:
    hidden0 = burn_in(model, batch)
    hiddens, spatials, beliefs, values = run_sequence(
        model, batch["planes"], batch["scalars"], batch["window_lengths"], hidden0)
    seq, step = batch["decision_seq"], batch["decision_step"]
    D = seq.shape[0]
    metrics: dict = {}
    zero = torch.zeros((), device=hiddens.device)
    if D == 0:
        return zero, {"decisions": 0}
    h = hiddens[seq, step]                 # [D,H]
    sp = spatials[seq, step]               # [D,C,8,8]
    bl = beliefs[seq, step]                # [D,64,7]
    v = values[seq, step]                  # [D]
    mask = batch["cand_mask"]
    policy_logits, danger_logits = model.score(h, sp, batch["cand_from"], batch["cand_to"], batch["cand_promo"])
    log_probs = masked_log_softmax(policy_logits, mask)

    # Policy: cross-entropy on the demonstrated candidate, valid rows only.
    pv = batch["policy_valid"]
    if pv.any():
        target = batch["demonstrated"].clamp(min=0)
        nll = -log_probs.gather(1, target.unsqueeze(1)).squeeze(1)
        # Weighted by player strength when the config asks for it: cloning the
        # average arena player imitates its blunders too; the top teams' moves
        # are the prior worth having. Weights are normalised so the loss scale
        # does not change with the mixture.
        pw = batch["policy_weight"][pv]
        policy_loss = (nll[pv] * pw).sum() / pw.sum().clamp(min=1e-6)
        with torch.no_grad():
            top = log_probs.argmax(1)
            metrics["policy_accuracy"] = (top[pv] == target[pv]).float().mean().item()
            metrics["policy_entropy"] = masked_entropy(log_probs, mask)[pv].mean().item()
    else:
        policy_loss = zero
    # Belief: CE at hidden squares, averaged within each example, then over examples.
    bv = batch["belief_valid"]
    bm = batch["belief_mask"] & bv.unsqueeze(1)
    if bm.any():
        ce = F.cross_entropy(bl.reshape(-1, 7), batch["belief_classes"].reshape(-1), reduction="none").reshape(D, 64)
        per_example = (ce * bm).sum(1) / bm.sum(1).clamp(min=1)
        has = bm.any(1)
        belief_loss = per_example[has].mean()
        with torch.no_grad():
            pred = bl.argmax(-1)
            truth = batch["belief_classes"]
            enemy = bm & (truth != 6)
            metrics["belief_hidden_accuracy"] = (pred[bm] == truth[bm]).float().mean().item()
            if enemy.any():
                metrics["belief_enemy_recall"] = (pred[enemy] == truth[enemy]).float().mean().item()
    else:
        belief_loss = zero
    # Danger: BCE over legal candidates, averaged within each example.
    dv = batch["danger_valid"]
    dm = mask & dv.unsqueeze(1)
    if dm.any():
        bce = F.binary_cross_entropy_with_logits(danger_logits, batch["danger"], reduction="none")
        per_example = (bce * dm).sum(1) / dm.sum(1).clamp(min=1)
        danger_loss = per_example[dv].mean()
        with torch.no_grad():
            prob = torch.sigmoid(danger_logits)
            metrics["danger_brier"] = ((prob - batch["danger"]) ** 2)[dm].mean().item()
            positives = dm & (batch["danger"] > 0.5)
            metrics["danger_positive_rate"] = positives.sum().item() / max(dm.sum().item(), 1)
            if positives.any():
                metrics["danger_false_negative_rate"] = (prob[positives] < 0.5).float().mean().item()
    else:
        danger_loss = zero
    # Value: MSE on decision states of normal games.
    vv = batch["value_valid"]
    if vv.any():
        value_loss = F.mse_loss(v[vv], batch["returns"][vv])
        metrics["value_mse"] = value_loss.item()
    else:
        value_loss = zero
    total = (weights["policy"] * policy_loss + weights["belief"] * belief_loss
             + weights["danger"] * danger_loss + weights["value"] * value_loss)
    metrics.update({"loss": total.item(), "policy_loss": policy_loss.item(),
                    "belief_loss": belief_loss.item(), "danger_loss": danger_loss.item(),
                    "value_loss": value_loss.item(), "decisions": D})
    return total, metrics


class Checkpointer:
    def __init__(self, output: Path):
        self.output = output
        output.mkdir(parents=True, exist_ok=True)

    def save(self, model, optimizer, step, epoch, config, manifest, name="latest", extra=None) -> Path:
        path = self.output / f"{name}.pt"
        payload = {"state_dict": model.state_dict(), "optimizer": optimizer.state_dict() if optimizer else None,
                   "step": step, "epoch": epoch, "config": config, "architecture": getattr(model, "architecture", ARCHITECTURE),
                   "model_config": getattr(model, "size_config", None),
                   "parameters": parameter_count(model), "dataset_manifest_sha256": manifest.get("content_sha256"),
                   "feature_version": manifest.get("feature_version"), "action_version": manifest.get("action_version"),
                   "rules_fingerprint": manifest.get("rules_fingerprint"), "extra": extra or {}}
        torch.save(payload, path)
        return path


def checkpoint_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: Path, device="cpu") -> tuple[FogPolicy, dict]:
    payload = torch.load(path, map_location=device, weights_only=False)
    model = FogPolicy(**(payload.get("model_config") or {})).to(device)
    model.load_state_dict(payload["state_dict"])
    return model, payload


def evaluate(model, episodes, config, device, rng, limit: int | None = None) -> dict:
    model.eval()
    totals: dict = {}
    count = 0
    window = config["window"]
    batch_size = config["sequences_per_batch"]
    chosen = episodes[:limit] if limit else episodes
    with torch.no_grad():
        for start in range(0, len(chosen), batch_size):
            group = chosen[start:start + batch_size]
            # Deterministic windows for evaluation: walk every window of each episode.
            longest = max(len(e.actor.observations) for e in group)
            for ws in range(0, longest, window):
                starts = [min(ws, max(len(e.actor.observations) - 1, 0)) for e in group]
                batch = to_device(ds.make_batch(group, window, rng, starts), device)
                if batch["decision_seq"].shape[0] == 0:
                    continue
                _, metrics = compute_losses(model, batch, config["loss_weights"])
                n = metrics["decisions"]
                for key, value in metrics.items():
                    if key == "decisions":
                        continue
                    totals[key] = totals.get(key, 0.0) + value * n
                count += n
    model.train()
    return {k: v / max(count, 1) for k, v in totals.items()} | {"decisions": count}


def train(config_path: Path, manifest_path: Path, output: Path, max_steps: int | None = None,
          resume: Path | None = None, limit_episodes: int | None = None) -> Path:
    config = load_config(config_path)["pretrain"]
    manifest = json.loads(Path(manifest_path).read_text())
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(config["seed"])
    rng = random.Random(config["seed"])
    train_episodes = ds.load_episodes(Path(manifest["shards"]["train"]), limit_episodes)
    val_episodes = ds.load_episodes(Path(manifest["shards"]["validation"]), limit_episodes)
    train_episodes = [e for e in train_episodes if e.num_decisions > 0]
    if config.get("players"):
        # Replica training: only the named team's own games, from its seat.
        keep = set(config["players"])
        train_episodes = [e for e in train_episodes if e.metadata.player_id in keep]
        val_episodes = [e for e in val_episodes if e.metadata.player_id in keep]
    print(f"train episodes {len(train_episodes)}, validation {len(val_episodes)}, device {device}", file=sys.stderr)

    model = FogPolicy(**config.get("model", {})).to(device)
    if config.get("init_checkpoint"):
        payload0 = torch.load(config["init_checkpoint"], map_location=device, weights_only=False)
        model.load_state_dict(payload0["state_dict"])
        print(f"initialised from {config['init_checkpoint']}", file=sys.stderr)
    print(f"model {model.architecture}: {parameter_count(model):,} parameters", file=sys.stderr)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"],
                                  weight_decay=config["weight_decay"])
    schedule = None
    if config.get("cosine_steps"):
        schedule = torch.optim.lr_scheduler.LambdaLR(
            optimizer, lambda s: max(0.05, 0.5 * (1 + math.cos(math.pi * min(1.0, s / config["cosine_steps"])))))
    step = epoch = 0
    if resume:
        payload = torch.load(resume, map_location=device, weights_only=False)
        model.load_state_dict(payload["state_dict"])
        if payload.get("optimizer"):
            optimizer.load_state_dict(payload["optimizer"])
        step, epoch = payload["step"], payload["epoch"]
        print(f"resumed from {resume} at step {step}", file=sys.stderr)
    checkpointer = Checkpointer(output)
    log = open(output / "train_log.jsonl", "a")
    best_val = math.inf
    batch_size = config["sequences_per_batch"]
    accumulate = max(1, config.get("accumulation_steps", 1))
    use_amp = bool(config.get("mixed_precision", False)) and device.type == "cuda"
    scaler = torch.amp.GradScaler(enabled=use_amp)
    started = time.time()
    done = False
    while epoch < config["epochs"] and not done:
        order = list(range(len(train_episodes)))
        rng.shuffle(order)
        for start in range(0, len(order), batch_size):
            group = [train_episodes[i] for i in order[start:start + batch_size]]
            batch = to_device(ds.make_batch(group, config["window"], rng,
                                            player_weights=config.get("player_weights")), device)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_amp):
                loss, metrics = compute_losses(model, batch, config["loss_weights"])
            if metrics.get("decisions", 0) == 0:
                continue
            scaler.scale(loss / accumulate).backward()
            if (step + 1) % accumulate == 0:
                scaler.unscale_(optimizer)
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["grad_clip"])
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                if schedule is not None:
                    schedule.step()
                metrics["grad_norm"] = float(grad_norm)
            step += 1
            metrics.update({"step": step, "epoch": epoch, "elapsed": time.time() - started})
            log.write(json.dumps(metrics) + "\n")
            if step % 20 == 0:
                print(f"step {step} loss {metrics['loss']:.3f} policy {metrics['policy_loss']:.3f} "
                      f"belief {metrics['belief_loss']:.3f} danger {metrics['danger_loss']:.3f} "
                      f"value {metrics['value_loss']:.3f} acc {metrics.get('policy_accuracy', 0):.3f}", file=sys.stderr)
            if max_steps and step >= max_steps:
                done = True
                break
        epoch += 1
        validation = evaluate(model, val_episodes, config, device, random.Random(0),
                              config.get("validation_sequences"))
        validation.update({"step": step, "epoch": epoch, "validation": True})
        log.write(json.dumps(validation) + "\n")
        log.flush()
        print(f"epoch {epoch} validation: " + " ".join(f"{k}={v:.4f}" for k, v in validation.items()
                                                        if isinstance(v, float)), file=sys.stderr)
        checkpointer.save(model, optimizer, step, epoch, config, manifest, "latest", validation)
        # Early-stopping signal: belief + danger losses, as the specification asks,
        # rather than imitation accuracy alone.
        if config.get("select_on") == "policy":
            score = validation.get("policy_loss", 0.0)
        else:
            score = validation.get("belief_loss", 0.0) + validation.get("danger_loss", 0.0)
        if score < best_val:
            best_val = score
            checkpointer.save(model, optimizer, step, epoch, config, manifest, "best", validation)
    log.close()
    return output / "latest.pt"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("learning/configs/replay_ppo.yaml"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("checkpoints/pretrain"))
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--limit-episodes", type=int, default=None)
    args = parser.parse_args(argv)
    path = train(args.config, args.manifest, args.output, args.max_steps, args.resume, args.limit_episodes)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
