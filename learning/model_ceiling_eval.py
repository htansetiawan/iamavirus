"""Offline evaluation for the model ceiling study: how well a checkpoint predicts
moves, overall and for the strongest players, on a game-disjoint test shard.

    python -m learning.model_ceiling_eval checkpoints/ceiling-m/best.pt --manifest data/manifests/v4.json

Reports policy NLL, top-1 and top-4 accuracy of the demonstrated move among the
legal candidates, split by who played it (the top six, us, everyone else), plus
belief and danger losses. Test episodes are walked in fixed windows from the
first event, so the recurrent state is the one the bot would carry.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

import torch

from . import dataset as ds
from .model import masked_log_softmax, parameter_count
from .pretrain import burn_in, compute_losses, load_model, run_sequence, to_device

TEAM_ID = "a2c35173659545c99752376a70418438"
TOP = {"Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"}


def top_ids() -> set:
    ids = set(TOP)
    try:
        board = json.load(open("/tmp/claude-1000/leaderboard.json"))
        for p in board["players"]:
            if p.get("name") in TOP:
                ids.add(p["id"])
    except Exception:
        pass
    return ids


def group_of(player_id: str, tops: set) -> str:
    if player_id == TEAM_ID or player_id == "IAmAVirus":
        return "us"
    return "top6" if player_id in tops else "others"


def evaluate(path: Path, manifest_path: Path, window: int = 64, batch_size: int = 16, limit: int | None = None) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, payload = load_model(path, device)
    model.eval()
    manifest = json.loads(Path(manifest_path).read_text())
    if payload.get("feature_version") and payload["feature_version"] != manifest.get("feature_version"):
        raise SystemExit(f"feature version mismatch: model {payload['feature_version']} vs shard {manifest.get('feature_version')}")
    episodes = ds.load_episodes(Path(manifest["shards"]["test"]), limit)
    tops = top_ids()
    stats = collections.defaultdict(lambda: collections.Counter())
    other = collections.Counter()
    rng = random.Random(0)
    with torch.no_grad():
        for start in range(0, len(episodes), batch_size):
            group = episodes[start:start + batch_size]
            groups = [group_of(e.metadata.player_id, tops) for e in group]
            longest = max(len(e.actor.observations) for e in group)
            for ws in range(0, longest, window):
                starts = [min(ws, max(len(e.actor.observations) - 1, 0)) for e in group]
                batch = to_device(ds.make_batch(group, window, rng, starts), device)
                D = batch["decision_seq"].shape[0]
                if D == 0:
                    continue
                _, metrics = compute_losses(model, batch, {"policy": 1.0, "belief": 1.0, "danger": 1.0, "value": 0.25})
                for key in ("belief_loss", "danger_loss", "danger_brier", "belief_enemy_recall"):
                    if key in metrics:
                        other[key] += metrics[key] * D
                other["decisions"] += D
                hidden0 = burn_in(model, batch)
                hiddens, spatials, _, _ = run_sequence(model, batch["planes"], batch["scalars"], batch["window_lengths"], hidden0)
                seq, step = batch["decision_seq"], batch["decision_step"]
                logits, _ = model.score(hiddens[seq, step], spatials[seq, step], batch["cand_from"], batch["cand_to"], batch["cand_promo"])
                log_probs = masked_log_softmax(logits, batch["cand_mask"])
                pv = batch["policy_valid"]
                target = batch["demonstrated"].clamp(min=0)
                nll = -log_probs.gather(1, target.unsqueeze(1)).squeeze(1)
                rank = (log_probs > log_probs.gather(1, target.unsqueeze(1))).sum(1)
                for i in range(D):
                    if not bool(pv[i]):
                        continue
                    g = groups[int(seq[i])]
                    for key in (g, "all"):
                        s = stats[key]
                        s["n"] += 1
                        s["nll"] += float(nll[i])
                        s["top1"] += int(rank[i] == 0)
                        s["top4"] += int(rank[i] < 4)
    out = {"checkpoint": str(path), "architecture": payload.get("architecture"), "parameters": parameter_count(model),
           "step": payload.get("step"), "epoch": payload.get("epoch")}
    for key, s in stats.items():
        n = max(s["n"], 1)
        out[key] = {"decisions": s["n"], "policy_nll": round(s["nll"] / n, 4), "top1": round(100 * s["top1"] / n, 2),
                    "top4": round(100 * s["top4"] / n, 2)}
    n = max(other["decisions"], 1)
    out["belief_loss"] = round(other["belief_loss"] / n, 4)
    out["danger_loss"] = round(other["danger_loss"] / n, 4)
    out["danger_brier"] = round(other["danger_brier"] / n, 5)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkpoints", nargs="+", type=Path)
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/v4.json"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    results = []
    for path in args.checkpoints:
        r = evaluate(path, args.manifest, limit=args.limit)
        results.append(r)
        line = f"{r['architecture']} ({r['parameters']:,} params, step {r['step']}): "
        line += " | ".join(f"{g} n={r[g]['decisions']} nll {r[g]['policy_nll']} top1 {r[g]['top1']}% top4 {r[g]['top4']}%"
                           for g in ("all", "top6", "us", "others") if g in r)
        line += f" | belief {r['belief_loss']} danger {r['danger_loss']}"
        print(line, flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
