"""Episodes, splits, shards and minibatches.

    python -m learning.dataset --raw data/raw --manifest data/manifests/v1.json

Splits are assigned to whole games before any sequence is cut, both colours of
a game share a split, and exact duplicate move sequences are grouped so they
cannot straddle a split. The default is 80/10/10 with the most recent games
held out for validation and test where timestamps exist.

Shards are gzip JSON lines of `PlayerEpisode.to_dict()`, one episode per line:
compact observation strings and action arrays, loadable without unpickling.
Dense planes are built per minibatch by `features.replay_events`.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import datetime
import gzip
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import features, histories, ingest, labels, rules
from .action_codec import encode_action, split_action

SPLITS = ("train", "validation", "test")


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def assign_splits(rows: list[dict], fractions=(0.8, 0.1, 0.1), seed: int = 0,
                  chronological: bool = True) -> dict[str, str]:
    """game id -> split. Duplicate move sequences share a group and a split."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["moves_sha256"]].append(row)
    keys = list(groups)
    if chronological and all(r.get("createdAt") for r in rows):
        keys.sort(key=lambda k: max(r["createdAt"] for r in groups[k]))
    else:
        random.Random(seed).shuffle(keys)
    total = len(keys)
    n_train = int(round(total * fractions[0]))
    n_val = int(round(total * fractions[1]))
    assignment = {}
    for index, key in enumerate(keys):
        split = "train" if index < n_train else "validation" if index < n_train + n_val else "test"
        for row in groups[key]:
            assignment[row["id"]] = split
    return assignment


def build_dataset(raw: Path, manifest_path: Path, version: str, fractions=(0.8, 0.1, 0.1),
                  seed: int = 0, limit: int | None = None) -> dict:
    """Publish a complete immutable generation, preserving the last dataset on failure.

    Resolve an existing manifest symlink before replacing its target. A new
    generation never truncates shards referenced by a published manifest.
    Interrupted builds can leave an unreferenced generation, but readers keep
    the previous manifest and its files until atomic publication succeeds.
    """
    if not version or Path(version).name != version or version in (".", ".."):
        raise ValueError("version must be a single directory name")
    manifest_path = manifest_path.resolve()
    out_dir = manifest_path.parent / version
    out_dir.mkdir(parents=True, exist_ok=True)
    generation = out_dir / f"generation-{uuid.uuid4().hex}"
    generation.mkdir()
    temporary_manifest = None
    published = False
    try:
        manifest = _build_dataset_generation(raw, generation, version, fractions, seed, limit)
        hashes = {}
        for split, path in manifest["shards"].items():
            # Reading through EOF validates gzip trailers, including failures
            # during compression close or writes to removable storage.
            with gzip.open(path, "rt") as handle:
                count = sum(1 for line in handle if line.strip())
            if count != manifest["counts"][split].get("episodes", 0):
                raise ValueError(f"{split} shard count differs from manifest")
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                os.fsync(handle.fileno())
            hashes[split] = digest.hexdigest()
        manifest["shard_sha256"] = hashes
        manifest["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with tempfile.NamedTemporaryFile(mode="w", dir=manifest_path.parent,
                                         prefix=f".{manifest_path.name}-", delete=False) as handle:
            temporary_manifest = Path(handle.name)
            json.dump(manifest, handle, indent=1, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_manifest, manifest_path)
        published = True
        return manifest
    finally:
        if temporary_manifest is not None:
            temporary_manifest.unlink(missing_ok=True)
        if not published:
            shutil.rmtree(generation)


def _build_dataset_generation(raw: Path, out_dir: Path, version: str, fractions, seed, limit) -> dict:
    store = ingest.RawStore(raw)
    rows = [json.loads(line) for line in store.accepted.read_text().splitlines() if line.strip()]
    if limit:
        rows = rows[:limit]
    assignment = assign_splits(rows, fractions, seed)
    stats: dict = {split: Counter() for split in SPLITS}
    by_opponent: dict = {split: Counter() for split in SPLITS}
    mismatches = []
    hasher = hashlib.sha256()
    with ExitStack() as stack:
        writers = {split: stack.enter_context(gzip.open(out_dir / f"{split}.jsonl.gz", "wt"))
                   for split in SPLITS}
        for row_index, row in enumerate(rows, 1):
            replay_path = store.games / row["id"] / "replay.json"
            replay_bytes = replay_path.read_bytes()
            replay = json.loads(replay_bytes)
            states, problems = ingest.validate_replay(replay)
            if problems:
                continue
            split = assignment[row["id"]]
            source_hash = hashlib.sha256(replay_bytes).hexdigest()
            for side in (rules.WHITE, rules.BLACK):
                episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT, source_hash)
                episode.metadata.split = split
                if episode.metadata.candidate_mismatches:
                    mismatches.append({"game": row["id"], "side": side,
                                       "cases": episode.metadata.candidate_mismatches})
                line = json.dumps(episode.to_dict(), separators=(",", ":"))
                writers[split].write(line + "\n")
                hasher.update(line.encode())
                s = stats[split]
                s["episodes"] += 1
                s["games"] += 0.5
                s["decisions"] += episode.num_decisions
                s["events"] += len(episode.actor.observations)
                s[f"color_{'white' if side == 0 else 'black'}"] += 1
                s[f"outcome_{episode.metadata.result}"] += 0.5
                s[f"termination_{episode.metadata.termination}"] += 0.5
                by_opponent[split][f"{episode.metadata.opponent_id}@v{episode.metadata.opponent_version}"] += 1
            if row_index % 1000 == 0:
                print(f"dataset: {row_index}/{len(rows)} source games processed", file=sys.stderr, flush=True)
    manifest = {
        "version": version, "raw": str(raw), "feature_version": features.FEATURE_VERSION,
        "action_version": features.ACTION_VERSION, "rules_fingerprint": ingest.RULES_FINGERPRINT,
        "fractions": list(fractions), "seed": seed, "content_sha256": hasher.hexdigest(),
        "shards": {split: str(out_dir / f"{split}.jsonl.gz") for split in SPLITS},
        "counts": {split: dict(stats[split]) for split in SPLITS},
        "opponents": {split: dict(by_opponent[split]) for split in SPLITS},
        "candidate_mismatches": mismatches,
        "source_games": len(rows),
        "undated_source_games": sum(not row.get("createdAt") for row in rows),
        "split_method": "chronological_duplicate_groups" if all(row.get("createdAt") for row in rows)
                        else "seeded_duplicate_groups_missing_timestamps",
    }
    return manifest


def load_episodes(path: Path, limit: int | None = None) -> list[histories.PlayerEpisode]:
    episodes = []
    with gzip.open(path, "rt") as handle:
        for line in handle:
            if not line.strip():
                continue
            episodes.append(histories.PlayerEpisode.from_dict(json.loads(line)))
            if limit and len(episodes) >= limit:
                break
    return episodes


# ---------------------------------------------------------------------------
# Minibatches
# ---------------------------------------------------------------------------

@dataclass
class SequenceBatch:
    """One minibatch of contiguous event windows, with full prefixes for burn-in.

    Tensors are numpy here; `pretrain.py` moves them to the device. B sequences,
    P = longest prefix (events before the window), W = window length,
    D = decisions in the window, M = widest candidate set among them.
    """
    prefix_planes: np.ndarray      # [B, P, 32, 8, 8]
    prefix_scalars: np.ndarray     # [B, P, 8]
    prefix_lengths: np.ndarray     # [B]
    planes: np.ndarray             # [B, W, 32, 8, 8]
    scalars: np.ndarray            # [B, W, 8]
    window_lengths: np.ndarray     # [B]
    # decisions: flat over the batch, each pointing at (sequence, window step)
    decision_seq: np.ndarray       # [D]
    decision_step: np.ndarray      # [D]
    cand_from: np.ndarray          # [D, M] canonical
    cand_to: np.ndarray            # [D, M]
    cand_promo: np.ndarray         # [D, M]
    cand_mask: np.ndarray          # [D, M] bool
    cand_count: np.ndarray         # [D]
    demonstrated: np.ndarray       # [D] index into candidates, -1 if invalid
    danger: np.ndarray             # [D, M] float, 0/1
    danger_valid: np.ndarray       # [D] bool
    belief_classes: np.ndarray     # [D, 64] canonical squares, 0..6
    belief_mask: np.ndarray        # [D, 64] bool, hidden squares
    belief_valid: np.ndarray       # [D] bool
    returns: np.ndarray            # [D]
    value_valid: np.ndarray        # [D] bool
    policy_valid: np.ndarray       # [D] bool
    policy_weight: np.ndarray      # [D] float, per-player weight for the cloning loss


def episode_tensors(episode: histories.PlayerEpisode):
    """Dense inputs for every event plus per-decision labels, in canonical coordinates."""
    actor = episode.actor
    own = dict(zip(actor.decision_event_indices, actor.own_actions))
    planes, scalars = features.replay_events(actor.side, actor.observations, actor.phases,
                                             actor.plies, own)
    canonical = np.arange(64) ^ 56 if actor.side == rules.BLACK else np.arange(64)
    decisions = []
    for i, event in enumerate(actor.decision_event_indices):
        cands = actor.legal_actions[i]
        ids, froms, tos, promos = features.candidate_arrays(cands, actor.side)
        demonstrated = cands.index(actor.own_actions[i]) if actor.own_actions[i] in cands else -1
        classes, hidden = labels.hidden_enemy_classes(episode.targets.boards[i],
                                                      actor.observations[event], actor.side)
        belief = np.zeros(64, dtype=np.int64)
        mask = np.zeros(64, dtype=bool)
        belief[canonical] = classes
        mask[canonical] = hidden
        decisions.append({
            "event": event, "from": froms, "to": tos, "promo": promos, "count": len(cands),
            "demonstrated": demonstrated if episode.targets.policy_valid[i] else -1,
            "danger": np.array(episode.targets.king_loss_by_action[i], dtype=np.float32),
            "danger_valid": bool(episode.targets.danger_valid[i]) and len(cands) > 0,
            "belief": belief, "belief_mask": mask,
            "belief_valid": bool(episode.targets.belief_valid[i]),
            "return": float(episode.targets.terminal_return),
            "value_valid": bool(episode.targets.value_valid[i]),
            "policy_valid": bool(episode.targets.policy_valid[i]) and demonstrated >= 0,
        })
    return planes, scalars, decisions


def make_batch(episodes: list[histories.PlayerEpisode], window: int, rng: random.Random,
               window_starts: list[int] | None = None,
               player_weights: dict[str, float] | None = None) -> SequenceBatch:
    """Cuts one window per episode. The prefix before each window is kept whole so
    the recurrent state can be reconstructed from the episode's first event."""
    items = [episode_tensors(e) for e in episodes]
    starts = []
    for index, (planes, _, _) in enumerate(items):
        n = planes.shape[0]
        if window_starts is not None:
            starts.append(window_starts[index])
        elif n <= window:
            starts.append(0)
        else:
            starts.append(rng.randrange(0, n - window + 1))
    B = len(items)
    P = max(s for s in starts) if starts else 0
    W = min(window, max(planes.shape[0] for planes, _, _ in items))
    prefix_planes = np.zeros((B, P, features.NUM_PLANES, 8, 8), dtype=np.float32)
    prefix_scalars = np.zeros((B, P, features.NUM_SCALARS), dtype=np.float32)
    prefix_lengths = np.zeros(B, dtype=np.int64)
    planes_out = np.zeros((B, W, features.NUM_PLANES, 8, 8), dtype=np.float32)
    scalars_out = np.zeros((B, W, features.NUM_SCALARS), dtype=np.float32)
    window_lengths = np.zeros(B, dtype=np.int64)
    flat = []
    for b, ((planes, scalars, decisions), start) in enumerate(zip(items, starts)):
        prefix_lengths[b] = start
        prefix_planes[b, :start] = planes[:start]
        prefix_scalars[b, :start] = scalars[:start]
        end = min(planes.shape[0], start + W)
        window_lengths[b] = end - start
        planes_out[b, :end - start] = planes[start:end]
        scalars_out[b, :end - start] = scalars[start:end]
        weight = 1.0
        if player_weights:
            meta = episodes[b].metadata
            weight = float(player_weights.get(meta.player_id, player_weights.get("default", 1.0)))
        for d in decisions:
            if start <= d["event"] < end:
                d = dict(d, policy_weight=weight)
                flat.append((b, d["event"] - start, d))
    D = len(flat)
    M = max((d["count"] for _, _, d in flat), default=1)
    M = max(M, 1)
    batch = SequenceBatch(
        prefix_planes, prefix_scalars, prefix_lengths, planes_out, scalars_out, window_lengths,
        decision_seq=np.array([b for b, _, _ in flat], dtype=np.int64),
        decision_step=np.array([t for _, t, _ in flat], dtype=np.int64),
        cand_from=np.zeros((D, M), dtype=np.int64), cand_to=np.zeros((D, M), dtype=np.int64),
        cand_promo=np.zeros((D, M), dtype=np.int64), cand_mask=np.zeros((D, M), dtype=bool),
        cand_count=np.zeros(D, dtype=np.int64), demonstrated=np.full(D, -1, dtype=np.int64),
        danger=np.zeros((D, M), dtype=np.float32), danger_valid=np.zeros(D, dtype=bool),
        belief_classes=np.zeros((D, 64), dtype=np.int64), belief_mask=np.zeros((D, 64), dtype=bool),
        belief_valid=np.zeros(D, dtype=bool), returns=np.zeros(D, dtype=np.float32),
        value_valid=np.zeros(D, dtype=bool), policy_valid=np.zeros(D, dtype=bool),
        policy_weight=np.ones(D, dtype=np.float32))
    for k, (_, _, d) in enumerate(flat):
        n = d["count"]
        batch.cand_from[k, :n] = d["from"]
        batch.cand_to[k, :n] = d["to"]
        batch.cand_promo[k, :n] = d["promo"]
        batch.cand_mask[k, :n] = True
        batch.cand_count[k] = n
        batch.demonstrated[k] = d["demonstrated"]
        batch.danger[k, :n] = d["danger"]
        batch.danger_valid[k] = d["danger_valid"]
        batch.belief_classes[k] = d["belief"]
        batch.belief_mask[k] = d["belief_mask"]
        batch.belief_valid[k] = d["belief_valid"]
        batch.returns[k] = d["return"]
        batch.value_valid[k] = d["value_valid"]
        batch.policy_valid[k] = d["policy_valid"]
        batch.policy_weight[k] = d.get("policy_weight", 1.0)
    return batch


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--version", default=None, help="defaults to the manifest file stem")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    version = args.version or args.manifest.stem
    manifest = build_dataset(args.raw, args.manifest, version, seed=args.seed, limit=args.limit)
    print(json.dumps({k: manifest[k] for k in ("version", "counts", "content_sha256")}, indent=1))
    if manifest["candidate_mismatches"]:
        print(f"WARNING: {len(manifest['candidate_mismatches'])} episodes with candidate mismatches "
              f"(blocked samples; see manifest)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
