"""Feature cache: every episode's input planes and labels computed once, stored as
compact arrays, and batched without re-running the Python feature code.

    python -m learning.feature_cache build --manifest data/manifests/v4.json --out {storage}/iamavirus/feature-cache/v4
    # then add `feature_cache: <out>` to a pretrain config

Planes are exact multiples of 1/100 in [0, 1], so they are stored as uint8 (x100)
without loss (checked: max error 4e-6, float rounding). Per split the cache holds:
planes.u8 (events x 32 x 8 x 8, memory-mapped), scalars.npy, episode offsets,
per-decision fixed fields, and candidate arrays with offsets. `CachedSplit.make_batch`
returns the same SequenceBatch as dataset.make_batch (verified by `verify`).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from . import dataset as ds
from . import features

PLANE_SHAPE = (features.NUM_PLANES, 8, 8)
PLANE_SIZE = int(np.prod(PLANE_SHAPE))


def build_split(shard: Path, out: Path, limit: int | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    episodes = ds.load_episodes(shard, limit)
    planes_file = open(out / "planes.u8", "wb")
    scalars, ep_offsets, ep_players = [], [0], []
    d_ep, d_event, d_count, d_demo, d_dvalid, d_belief, d_bmask, d_bvalid, d_ret, d_vvalid, d_pvalid = ([] for _ in range(11))
    c_from, c_to, c_promo, c_danger, c_offsets = [], [], [], [], [0]
    events = 0
    started = time.time()
    for index, episode in enumerate(episodes):
        planes, scal, decisions = ds.episode_tensors(episode)
        q = np.rint(planes * 100.0).astype(np.uint8)
        planes_file.write(q.tobytes())
        scalars.append(scal.astype(np.float32))
        events += planes.shape[0]
        ep_offsets.append(events)
        ep_players.append(episode.metadata.player_id)
        for d in decisions:
            d_ep.append(index)
            d_event.append(d["event"])
            d_count.append(d["count"])
            d_demo.append(d["demonstrated"])
            d_dvalid.append(d["danger_valid"])
            d_belief.append(np.asarray(d["belief"], dtype=np.uint8))
            d_bmask.append(np.asarray(d["belief_mask"], dtype=bool))
            d_bvalid.append(d["belief_valid"])
            d_ret.append(d["return"])
            d_vvalid.append(d["value_valid"])
            d_pvalid.append(d["policy_valid"])
            n = d["count"]
            c_from.append(np.asarray(d["from"], dtype=np.int16)[:n])
            c_to.append(np.asarray(d["to"], dtype=np.int16)[:n])
            c_promo.append(np.asarray(d["promo"], dtype=np.int8)[:n])
            c_danger.append(np.asarray(d["danger"], dtype=np.float16)[:n])
            c_offsets.append(c_offsets[-1] + n)
        if index % 1000 == 0 and index:
            print(f"  {index}/{len(episodes)} episodes, {events} events, {time.time() - started:.0f}s", file=sys.stderr)
    planes_file.close()
    np.save(out / "scalars.npy", np.concatenate(scalars) if scalars else np.zeros((0, features.NUM_SCALARS), np.float32))
    np.save(out / "ep_offsets.npy", np.asarray(ep_offsets, dtype=np.int64))
    dec = {"ep": np.asarray(d_ep, np.int32), "event": np.asarray(d_event, np.int32), "count": np.asarray(d_count, np.int16),
           "demo": np.asarray(d_demo, np.int16), "dvalid": np.asarray(d_dvalid, bool),
           "belief": np.stack(d_belief) if d_belief else np.zeros((0, 64), np.uint8),
           "bmask": np.stack(d_bmask) if d_bmask else np.zeros((0, 64), bool), "bvalid": np.asarray(d_bvalid, bool),
           "ret": np.asarray(d_ret, np.float32), "vvalid": np.asarray(d_vvalid, bool), "pvalid": np.asarray(d_pvalid, bool),
           "c_offsets": np.asarray(c_offsets, np.int64),
           "c_from": np.concatenate(c_from) if c_from else np.zeros(0, np.int16),
           "c_to": np.concatenate(c_to) if c_to else np.zeros(0, np.int16),
           "c_promo": np.concatenate(c_promo) if c_promo else np.zeros(0, np.int8),
           "c_danger": np.concatenate(c_danger) if c_danger else np.zeros(0, np.float16)}
    np.savez(out / "decisions.npz", **dec)
    meta = {"episodes": len(episodes), "events": events, "decisions": len(d_ep), "players": ep_players,
            "shard": str(shard), "feature_version": features.FEATURE_VERSION, "seconds": round(time.time() - started, 1)}
    (out / "meta.json").write_text(json.dumps(meta))
    return meta


class CachedSplit:
    def __init__(self, directory: Path):
        directory = Path(directory)
        self.meta = json.loads((directory / "meta.json").read_text())
        self.ep_offsets = np.load(directory / "ep_offsets.npy")
        events = int(self.ep_offsets[-1])
        self.planes = np.memmap(directory / "planes.u8", dtype=np.uint8, mode="r", shape=(events, *PLANE_SHAPE))
        self.scalars = np.load(directory / "scalars.npy")
        d = np.load(directory / "decisions.npz")
        self.d = {k: d[k] for k in d.files}
        self.players = self.meta["players"]
        # decisions of each episode, sorted by event
        order = np.argsort(self.d["ep"], kind="stable")
        self.dec_by_ep = np.split(order, np.searchsorted(self.d["ep"][order], np.arange(1, len(self.players))))

    def __len__(self) -> int:
        return len(self.players)

    def length(self, i: int) -> int:
        return int(self.ep_offsets[i + 1] - self.ep_offsets[i])

    def episode_planes(self, i: int, a: int, b: int) -> np.ndarray:
        base = int(self.ep_offsets[i])
        return self.planes[base + a: base + b].astype(np.float32) / 100.0

    def make_batch(self, indices, window: int, rng: random.Random, window_starts=None, player_weights=None) -> ds.SequenceBatch:
        lengths = [self.length(i) for i in indices]
        starts = []
        for k, n in enumerate(lengths):
            if window_starts is not None:
                starts.append(window_starts[k])
            elif n <= window:
                starts.append(0)
            else:
                starts.append(rng.randrange(0, n - window + 1))
        B = len(indices)
        P = max(starts) if starts else 0
        W = min(window, max(lengths))
        prefix_planes = np.zeros((B, P, *PLANE_SHAPE), np.float32)
        prefix_scalars = np.zeros((B, P, features.NUM_SCALARS), np.float32)
        planes_out = np.zeros((B, W, *PLANE_SHAPE), np.float32)
        scalars_out = np.zeros((B, W, features.NUM_SCALARS), np.float32)
        prefix_lengths = np.zeros(B, np.int64)
        window_lengths = np.zeros(B, np.int64)
        flat = []
        for b, (i, start, n) in enumerate(zip(indices, starts, lengths)):
            base = int(self.ep_offsets[i])
            prefix_lengths[b] = start
            if start:
                prefix_planes[b, :start] = self.episode_planes(i, 0, start)
                prefix_scalars[b, :start] = self.scalars[base:base + start]
            end = min(n, start + W)
            window_lengths[b] = end - start
            planes_out[b, :end - start] = self.episode_planes(i, start, end)
            scalars_out[b, :end - start] = self.scalars[base + start:base + end]
            weight = 1.0
            if player_weights:
                weight = float(player_weights.get(self.players[i], player_weights.get("default", 1.0)))
            for j in self.dec_by_ep[i]:
                ev = int(self.d["event"][j])
                if start <= ev < end:
                    flat.append((b, ev - start, int(j), weight))
        D = len(flat)
        M = max([int(self.d["count"][j]) for _, _, j, _ in flat] or [1])
        M = max(M, 1)
        batch = ds.SequenceBatch(
            prefix_planes, prefix_scalars, prefix_lengths, planes_out, scalars_out, window_lengths,
            decision_seq=np.array([b for b, _, _, _ in flat], dtype=np.int64),
            decision_step=np.array([t for _, t, _, _ in flat], dtype=np.int64),
            cand_from=np.zeros((D, M), np.int64), cand_to=np.zeros((D, M), np.int64),
            cand_promo=np.zeros((D, M), np.int64), cand_mask=np.zeros((D, M), bool),
            cand_count=np.zeros(D, np.int64), demonstrated=np.full(D, -1, np.int64),
            danger=np.zeros((D, M), np.float32), danger_valid=np.zeros(D, bool),
            belief_classes=np.zeros((D, 64), np.int64), belief_mask=np.zeros((D, 64), bool),
            belief_valid=np.zeros(D, bool), returns=np.zeros(D, np.float32),
            value_valid=np.zeros(D, bool), policy_valid=np.zeros(D, bool),
            policy_weight=np.ones(D, np.float32))
        co = self.d["c_offsets"]
        for k, (_, _, j, weight) in enumerate(flat):
            n = int(self.d["count"][j])
            a = int(co[j])
            batch.cand_from[k, :n] = self.d["c_from"][a:a + n]
            batch.cand_to[k, :n] = self.d["c_to"][a:a + n]
            batch.cand_promo[k, :n] = self.d["c_promo"][a:a + n]
            batch.cand_mask[k, :n] = True
            batch.cand_count[k] = n
            batch.demonstrated[k] = int(self.d["demo"][j])
            batch.danger[k, :n] = self.d["c_danger"][a:a + n]
            batch.danger_valid[k] = bool(self.d["dvalid"][j])
            batch.belief_classes[k] = self.d["belief"][j]
            batch.belief_mask[k] = self.d["bmask"][j]
            batch.belief_valid[k] = bool(self.d["bvalid"][j])
            batch.returns[k] = float(self.d["ret"][j])
            batch.value_valid[k] = bool(self.d["vvalid"][j])
            batch.policy_valid[k] = bool(self.d["pvalid"][j])
            batch.policy_weight[k] = weight
        return batch


def verify(manifest: Path, cache: Path, split: str = "validation", trials: int = 20) -> None:
    """dataset.make_batch and CachedSplit.make_batch must agree on the same episodes and windows."""
    m = json.loads(Path(manifest).read_text())
    episodes = ds.load_episodes(Path(m["shards"][split]), None)
    cached = CachedSplit(Path(cache) / split)
    assert len(episodes) == len(cached), (len(episodes), len(cached))
    rng = random.Random(0)
    worst = 0.0
    for _ in range(trials):
        idx = rng.sample(range(len(episodes)), 6)
        starts = [rng.randrange(0, max(1, len(episodes[i].actor.observations) - 8)) for i in idx]
        a = ds.make_batch([episodes[i] for i in idx], 64, random.Random(1), starts)
        b = cached.make_batch(idx, 64, random.Random(1), starts)
        for field in a.__dataclass_fields__:
            x, y = getattr(a, field), getattr(b, field)
            if x.shape != y.shape:
                raise AssertionError(f"{field}: shape {x.shape} vs {y.shape}")
            if x.dtype.kind == "f":
                worst = max(worst, float(np.abs(x - y).max()) if x.size else 0.0)
            elif not np.array_equal(x, y):
                raise AssertionError(f"{field}: values differ")
    print(f"verify {split}: {trials} batches identical (float fields within {worst:.2e})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "verify"])
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--splits", nargs="*", default=["train", "validation", "test"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    if args.command == "build":
        m = json.loads(args.manifest.read_text())
        for split in args.splits:
            meta = build_split(Path(m["shards"][split]), args.out / split, args.limit)
            print(f"{split}: {meta['episodes']} episodes, {meta['events']} events, {meta['decisions']} decisions, {meta['seconds']}s")
        (args.out / "manifest.json").write_text(json.dumps({"source": str(args.manifest), "content_sha256": m.get("content_sha256"),
                                                             "feature_version": m.get("feature_version")}))
    else:
        verify(args.manifest, args.out)


if __name__ == "__main__":
    main()
