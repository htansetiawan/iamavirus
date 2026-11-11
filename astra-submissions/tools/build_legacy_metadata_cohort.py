"""Materialize all 164 recovered legacy games in isolated before/after exports.

Uses saved originals only. A separate shard reader checks metadata correction
and actor/target preservation. No model training or production publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_episodes(manifest):
    records = {}
    for split, name in manifest["shards"].items():
        path = Path(name)
        require(sha(path.read_bytes()) == manifest["shard_sha256"][split], "shard hash differs")
        with gzip.open(path, "rt") as stream:
            for line in stream:
                record = json.loads(line)
                key = (record["metadata"]["game_id"], record["actor"]["side"])
                require(key not in records and record["metadata"]["split"] == split,
                        "episode identity or fold differs")
                records[key] = record
    return records


def build(root, out, native, report):
    started = time.monotonic()
    from learning import _native, dataset, ingest
    from learning.metadata_overlay import load_metadata_overlay

    require(sha(native.read_bytes()) == "ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3",
            "native library differs")
    require(_native._library is None, "native library already initialized")
    _native.ensure_built = lambda verbose=True: native
    require(sha(Path(dataset.__file__).read_bytes()) ==
            "3e76dec9391e72db259c4123f911ebb8cb130af71311a7b64540a859a8850560",
            "dataset implementation differs from the tested overlay source")
    bundle = root / "data/astra-spool/corpus-metadata-recovery-20261111"
    source_bytes = (bundle / "sources.json").read_bytes()
    require(sha(source_bytes) == "c20e8535e3e9eb23dbb015de8fb0a6b562855e6cc019459350e27be806ffec97",
            "frozen source inventory differs")
    sources = json.loads(source_bytes)
    overlay_path = root / "astra-submissions/analysis/corpus-metadata-overlay-20261111/overlay.json"
    overlay = load_metadata_overlay(overlay_path)
    require(overlay.sha256 == "cf894da62d06b1da39dccae2cfe635b08301fe4efaf21ee93bbd7c0d3701ae5b",
            "overlay asset differs")
    require(len(sources) == len(overlay.records) == 164, "legacy cohort size differs")
    out.mkdir(parents=True, exist_ok=False)
    raw = out / "raw"
    rows, original_hashes, frame_count = [], {}, 0
    for source in sources:
        row = source["row"]
        game = row["id"]
        payload = (bundle / "originals" / f"{game}.json").read_bytes()
        replay = json.loads(payload)
        record = overlay.records[game]
        require(sha(payload) == source["sha256"] == record["original_sha256"], "original source differs")
        require(ingest.replay_hash(replay) == row["moves_sha256"] == record["moves_sha256"],
                "original moves differ")
        require(game not in original_hashes, "duplicate source ID")
        folder = raw / "games" / game
        folder.mkdir(parents=True)
        (folder / "replay.json").write_bytes(payload)
        rows.append(row)
        original_hashes[game] = sha(payload)
        frame_count += len(replay["frames"])
    require(frame_count == 14228, "legacy frame count differs")
    journal = raw / "accepted.jsonl"
    journal_bytes = ("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)).encode()
    journal.write_bytes(journal_bytes)
    print(f"Prepared {len(rows)} sources / {frame_count} frames", flush=True)
    before = dataset.build_dataset(raw, out / "before.json", "before", split_policy="trajectory-hash-v1")
    print("Baseline cohort exported", flush=True)
    after = dataset.build_dataset(raw, out / "corrected.json", "corrected", split_policy="trajectory-hash-v1",
                                  metadata_overlay=overlay_path)
    print("Corrected cohort exported", flush=True)
    old, new = read_episodes(before), read_episodes(after)
    expected = {(game, side) for game in original_hashes for side in (0, 1)}
    require(old.keys() == new.keys() == expected, "missing/extra color episodes")
    allowed = {"player_id", "opponent_id", "played_version", "opponent_version"}
    actor_targets = hashlib.sha256()
    for key in sorted(expected):
        game, side = key
        left, right = old[key], new[key]
        require(left["actor"] == right["actor"] and left["targets"] == right["targets"],
                f"actor/target changed: {key}")
        require({k: v for k, v in left["metadata"].items() if k not in allowed} ==
                {k: v for k, v in right["metadata"].items() if k not in allowed}, f"other metadata changed: {key}")
        metadata = overlay.records[game]["metadata"]
        own, other = ("white", "black") if side == 0 else ("black", "white")
        for field, value in {"player_id": metadata[f"{own}PlayerId"],
                             "opponent_id": metadata[f"{other}PlayerId"],
                             "played_version": metadata[f"{own}Version"],
                             "opponent_version": metadata[f"{other}Version"],
                             "source_hash": original_hashes[game]}.items():
            require(right["metadata"][field] == value, f"corrected metadata differs: {key}/{field}")
        actor_targets.update(json.dumps([key, right["actor"], right["targets"]],
                                       sort_keys=True, separators=(",", ":")).encode() + b"\n")
    require(before["undated_source_games"] == 164 and after["undated_source_games"] == 0,
            "missing dates were not restored")
    require(before["counts"] == after["counts"] and before["source_journal"] == after["source_journal"],
            "counts or original journal changed")
    require(before["candidate_mismatches"] == after["candidate_mismatches"], "candidate mismatches changed")
    require(Path(after["metadata_overlay"]["path"]).read_bytes() == overlay_path.read_bytes(),
            "retained metadata snapshot differs")
    require(after["metadata_overlay"]["applied_games"] == 164 and
            after["metadata_overlay"]["unused_records"] == 0, "overlay application count differs")
    require(journal.read_bytes() == journal_bytes and (bundle / "sources.json").read_bytes() == source_bytes,
            "journal or frozen source inventory changed")
    for game, digest in original_hashes.items():
        for path in (raw / "games" / game / "replay.json", bundle / "originals" / f"{game}.json"):
            require(sha(path.read_bytes()) == digest, f"source bytes changed: {game}")
    total_bytes = sum(path.stat().st_size for path in out.rglob("*") if path.is_file())
    require(total_bytes <= 64 * 1024 * 1024, "completed review artifact exceeds its bound")
    corpus_bytes = (root / "corpus/corpus-all.txt").read_bytes()
    require(sha(corpus_bytes) == "2a9b9eced517c21cc300a6fc110ee4a36250a0fdb9f6e550c5526dac9f77030a",
            "original selected-seat corpus differs")
    sides = {line.split()[0]: line.split()[1] for line in corpus_bytes.decode().splitlines() if line.strip()}
    actual_ours = sum(overlay.records[game]["metadata"]["white" if sides[game] == "w" else "black"] == "IAmAVirus"
                      for game in original_hashes)
    result = {
        "at": datetime.now(timezone.utc).isoformat(), "kind": "isolated data curation, not model/playing evidence",
        "games": len(rows), "frames": frame_count, "episodes": len(new),
        "distinct_trajectories": len({row["moves_sha256"] for row in rows}),
        "decisions": sum(len(record["actor"]["decision_event_indices"]) for record in new.values()),
        "fold_games": {split: int(counts.get("games", 0)) for split, counts in after["counts"].items()},
        "selected_seats_actual_IAmAVirus": actual_ours, "selected_seats_other_teams": len(rows) - actual_ours,
        "baseline_and_corrected_actor_target_sha256": actor_targets.hexdigest(),
        "all_actor_targets_other_metadata_and_stable_folds_equal": True, "all_original_bytes_unchanged": True,
        "candidate_mismatch_episodes": len(after["candidate_mismatches"]),
        "undated_before": 164, "undated_after": 0, "overlay_applied": 164, "overlay_unused": 0,
        "artifact_bytes": total_bytes, "elapsed_seconds": time.monotonic() - started,
        "before_manifest": str(out / "before.json"), "corrected_manifest": str(out / "corrected.json"),
        "manifest_sha256": {name: sha((out / name).read_bytes()) for name in ("before.json", "corrected.json")},
        "overlay_sha256": overlay.sha256, "source_inventory_sha256": sha(source_bytes),
        "producer_sha256": sha(Path(__file__).read_bytes()),
        "limits": ["A selected-loss historical cohort; not representative arena sampling or an untouched model holdout.",
                   "Fresh validation uses the existing native rules code; it is not an independent all-corpus referee recertification.",
                   "No canonical raw/journal, daily options, production generation, model, GPU, match, ZIP/version or website changed."],
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("games", "episodes", "decisions", "artifact_bytes", "elapsed_seconds")}), flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    build(args.root.resolve(), args.out.resolve(), args.native.resolve(), args.report.resolve())


if __name__ == "__main__":
    main()
