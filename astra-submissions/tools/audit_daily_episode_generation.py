"""Audit the newly published daily episode generation; no export or fitting.

Reuses 379's bounded gzip reader and lease. Only the changed episode shards
are scanned. The already-verified move export is a separate data product.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import math
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import audit_training_artifacts as shared
from learning.dataset import dataset_source_rows

NAME = "daily-episode-generation-20261111"
OUT = ROOT / "astra-submissions/analysis" / NAME
PRIVATE = ROOT / "data/astra-spool" / NAME
RAW = ROOT / "data/raw"
MANIFEST = ROOT / "data/manifests/arena-latest.json"
PROJECTION = ROOT / "data/astra-spool/episode-split-lineage-20261111/projected-folds.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        stream.write(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def prepare():
    payload = MANIFEST.read_bytes()
    manifest = json.loads(payload)
    if datetime.fromisoformat(manifest["created_at"]) < datetime.fromisoformat("2026-11-11T10:49:13+00:00"):
        print(json.dumps({"status": "waiting_for_publication", "published_created_at": manifest["created_at"]}))
        return 75
    projection_plan = read(ROOT / "astra-submissions/analysis/episode-split-lineage-20261111/plan.json")
    expected = projection_plan["journal"]
    journal = manifest["source_journal"]
    for key in ("bytes", "sha256", "unique_games", "duplicate_lines"):
        assert journal[key] == expected[key], (key, journal[key], expected[key])
    assert manifest["source_games"] == 234911
    OUT.mkdir(exist_ok=False)
    PRIVATE.mkdir(exist_ok=False)
    (PRIVATE / "manifest.json").write_bytes(payload)
    with (RAW / ".writer.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        with (RAW / "accepted.jsonl").open("rb") as source, (PRIVATE / "journal-prefix.jsonl").open("xb") as target:
            remaining = journal["bytes"]
            while remaining:
                chunk = source.read(min(remaining, 1024**2))
                assert chunk, "raw journal shrank below the published source prefix"
                target.write(chunk)
                remaining -= len(chunk)
    assert sha(PRIVATE / "journal-prefix.jsonl") == journal["sha256"]
    rows, snapshot = dataset_source_rows(PRIVATE / "journal-prefix.jsonl")
    for key in ("bytes", "sha256", "unique_games", "duplicate_lines", "accepted_lines"):
        assert snapshot[key] == journal[key]
    files = []
    for split, path in manifest["shards"].items():
        p = Path(path); stat = p.stat()
        files.append({"split": split, "path": str(p), "bytes": stat.st_size,
                      "sha256": manifest["shard_sha256"][split], "device": stat.st_dev, "inode": stat.st_ino})
    assert {r["split"] for r in files} == {"train", "validation", "test"}
    assert sum(r["bytes"] for r in files) <= 2 * 1024**3
    sources = [Path(__file__), Path(shared.__file__), ROOT / "learning/dataset.py",
               PRIVATE / "manifest.json", PRIVATE / "journal-prefix.jsonl", PROJECTION,
               ROOT / "astra-submissions/analysis/episode-split-lineage-20261111/result.json"]
    plan = {"at": now(), "core": 6, "wall_seconds": 900, "max_compressed_read_bytes": 2 * 1024**3,
            "max_decompressed_bytes": 64 * 1024**3, "max_line_bytes": 64 * 1024**2,
            "max_episode_rows": 1000000, "files": files, "source_journal": snapshot,
            "manifest_created_at": manifest["created_at"], "source_games": len(rows),
            "source_sha256": {str(p): sha(p) for p in sources},
            "scope": "All three new episode-shard file hashes, gzip/JSON, dimensions, color pairing, complete demonstrated-move hashes, technical masks and saved fold projection. No rules/feature recomputation, global interleaved content-digest recomputation, fitting or playing-strength claim."}
    save(OUT / "plan.json", plan)
    print(json.dumps({"status": "prepared", "plan_sha256": sha(OUT / "plan.json"),
                      "source_games": len(rows), "compressed_bytes": sum(r["bytes"] for r in files)}), flush=True)
    return 0


def run():
    plan = read(OUT / "plan.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    manifest = read(PRIVATE / "manifest.json")
    rows, _ = dataset_source_rows(PRIVATE / "journal-prefix.jsonl")
    raw = {r["id"]: r for r in rows}
    projection = {r["id"]: r for r in (json.loads(line) for line in PROJECTION.open())}
    assert raw.keys() == projection.keys()
    declared_mismatches = {r["game"] for r in manifest["candidate_mismatches"]}
    state = {"at": now(), "status": "running", "episode_rows": 0, "completed_files": 0,
             "plan_sha256": sha(OUT / "plan.json")}
    save(OUT / "execution.json", state)
    shared.NAME = NAME
    started = time.monotonic()
    def timeout(*_):
        raise TimeoutError("original 900-second daily episode audit cap reached")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan["wall_seconds"])
    budget, decoded, seen = [0], 0, {}
    split_stats, file_receipts, groups = {}, [], defaultdict(set)
    verified_moves = skipped_moves = 0
    try:
        with shared.lease(), (PRIVATE / "episode-index.jsonl").open("x") as index:
            for spec in sorted(plan["files"], key=lambda r: r["bytes"]):
                split, stats, pending = spec["split"], Counter(), None
                with Path(spec["path"]).open("rb") as stream:
                    tracked = shared.Reader(stream, budget, plan["max_compressed_read_bytes"])
                    with gzip.GzipFile(fileobj=tracked, mode="rb") as zipped:
                        while True:
                            line = zipped.readline(plan["max_line_bytes"] + 1)
                            if not line:
                                break
                            assert len(line) <= plan["max_line_bytes"] and line.endswith(b"\n")
                            decoded += len(line); assert decoded <= plan["max_decompressed_bytes"]
                            obj = json.loads(line)
                            actor, target, meta = obj["actor"], obj["targets"], obj["metadata"]
                            game, side = meta["game_id"], actor["side"]
                            assert game in raw and side in (0, 1)
                            assert meta["split"] == split == projection[game]["projected_split"]
                            assert raw[game]["moves_sha256"] == projection[game]["moves_sha256"]
                            for key in ("feature_version", "action_version", "rules_fingerprint"):
                                assert meta[key] == manifest[key]
                            n = len(actor["decision_event_indices"])
                            for key in ("own_actions", "legal_actions", "inferred_en_passant", "castling_rights"):
                                assert len(actor[key]) == n
                            for key in ("boards", "king_loss_by_action", "demonstrated_actions", "policy_valid", "value_valid", "belief_valid", "danger_valid"):
                                assert len(target[key]) == n
                            assert len(actor["observations"]) == len(actor["phases"]) == len(actor["plies"])
                            assert target["demonstrated_actions"] == actor["own_actions"]
                            assert math.isfinite(target["terminal_return"])
                            if meta["termination"] != "normal":
                                assert not any(target["policy_valid"]) and not any(target["value_valid"])
                                assert target["terminal_return"] == 0
                            events = actor["decision_event_indices"]
                            assert events == sorted(set(events)) and all(e % 2 == side for e in events)
                            assert all(0 <= e < len(actor["observations"]) for e in events)
                            moves = dict(zip(events, actor["own_actions"], strict=True))
                            if side == 0:
                                assert pending is None and game not in seen
                                pending = (game, meta["source_hash"], moves)
                            else:
                                assert pending and pending[:2] == (game, meta["source_hash"])
                                combined = dict(pending[2]); assert not combined.keys() & moves.keys()
                                combined.update(moves)
                                if game in declared_mismatches:
                                    skipped_moves += 1
                                else:
                                    assert set(combined) == set(range(len(combined)))
                                    sequence = " ".join(combined[e] for e in range(len(combined)))
                                    assert hashlib.sha256(sequence.encode()).hexdigest() == raw[game]["moves_sha256"]
                                    verified_moves += 1
                                seen[game] = split
                                pending = None
                            stats.update(episodes=1, decisions=n, events=len(actor["observations"]))
                            stats["color_white" if side == 0 else "color_black"] += 1
                            stats["outcome_" + meta["result"]] += 1
                            stats["termination_" + meta["termination"]] += 1
                            stats["value_valid_" + meta["termination"]] += sum(target["value_valid"])
                            groups[raw[game]["moves_sha256"]].add(split)
                            index.write(json.dumps({"id": game, "side": side, "split": split,
                                "moves_sha256": raw[game]["moves_sha256"], "source_hash": meta["source_hash"]}, separators=(",", ":")) + "\n")
                            state["episode_rows"] += 1; assert state["episode_rows"] <= plan["max_episode_rows"]
                            if state["episode_rows"] % 20000 == 0:
                                shared.update(OUT / "execution.json", state)
                                print(json.dumps({"split": split, "episode_rows": state["episode_rows"]}), flush=True)
                    assert pending is None
                    assert tracked.bytes == spec["bytes"] and tracked.digest.hexdigest() == spec["sha256"]
                actual = Path(spec["path"]).stat()
                assert (actual.st_dev, actual.st_ino, actual.st_size) == (spec["device"], spec["inode"], spec["bytes"])
                for key, count in manifest["counts"][split].items():
                    if key == "games":
                        assert stats["episodes"] / 2 == count
                    elif key.startswith(("outcome_", "termination_")):
                        assert stats[key] / 2 == count
                    else:
                        assert stats[key] == count, (split, key)
                split_stats[split] = dict(stats)
                file_receipts.append({"split": split, "bytes": tracked.bytes, "sha256": tracked.digest.hexdigest()})
                state["completed_files"] += 1
                shared.update(OUT / "execution.json", state)
        assert seen.keys() == raw.keys() and len(seen) == manifest["source_games"]
        assert verified_moves + skipped_moves == len(seen)
        for path, expected in plan["source_sha256"].items():
            assert sha(Path(path)) == expected
        overlap = {key: sorted(value) for key, value in groups.items() if len(value) > 1}
        save(PRIVATE / "cross-fold-groups.json", overlap)
        result = {"at": now(), "status": "complete", "plan_sha256": sha(OUT / "plan.json"),
                  "manifest_created_at": manifest["created_at"], "source_games": len(seen),
                  "episode_rows": state["episode_rows"], "split_statistics": split_stats,
                  "complete_move_hashes_verified": verified_moves, "declared_mismatch_games_not_move_reconstructed": skipped_moves,
                  "candidate_mismatch_episodes": len(manifest["candidate_mismatches"]),
                  "distinct_trajectories": len(groups), "cross_fold_trajectory_groups": len(overlap),
                  "all_saved_projected_folds_match": True, "file_receipts": file_receipts,
                  "compressed_bytes_read": budget[0], "decompressed_bytes": decoded,
                  "index_sha256": sha(PRIVATE / "episode-index.jsonl"),
                  "undated_source_games": manifest["undated_source_games"], "split_method": manifest["split_method"],
                  "global_interleaved_content_digest_recomputed": False, "scope": plan["scope"],
                  "limitations": ["Existing original-import identity/date corrections remain a separate sidecar, not a repaired generation.",
                                  "All new shard files are checked, not all rules, feature values, hidden-board targets or model quality.",
                                  "Saved projection match does not make moved historical holdouts untouched.",
                                  "Archive completion and device health are separate claims."]}
        save(OUT / "result.json", result)
        state.update(status="complete", result_sha256=sha(OUT / "result.json"))
        print(json.dumps({k: result[k] for k in ("status", "source_games", "episode_rows", "complete_move_hashes_verified", "candidate_mismatch_episodes", "cross_fold_trajectory_groups", "all_saved_projected_folds_match")}, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        shared.update(OUT / "execution.json", state)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("prepare", "run")
    sys.exit(globals()[sys.argv[1]]())
