"""Compare published episode folds with the current export's split projection.

Read-only data curation: uses the audited November 2 episode index and a
locked current journal snapshot. Does not rebuild episodes, assign a training
run, alter either dataset, or certify the still-running export as published.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.dataset import assign_splits, dataset_source_rows
import audit_training_artifacts as prior_audit

NAME = "episode-split-lineage-20261111"
OUT = ROOT / "astra-submissions/analysis" / NAME
PRIVATE = ROOT / "data/astra-spool" / NAME
OLD = ROOT / "data/astra-spool/training-artifact-readiness-20261111"
EVIDENCE = ROOT / "astra-submissions/analysis/training-artifact-readiness-20261111"
SPLITS = ("train", "validation", "test")


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def matrix(counts):
    return {a: {b: counts[a, b] for b in SPLITS} for a in SPLITS}


def main():
    OUT.mkdir(exist_ok=False)
    PRIVATE.mkdir(exist_ok=False)
    started = time.monotonic()
    def timeout(*_):
        raise TimeoutError("original 180-second metadata audit cap reached")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    state = {"at": now(), "status": "running", "scope": "metadata projection only"}
    save(OUT / "execution.json", state)
    try:
        # Reuse 379's existing append/release protocol, with a distinct owner.
        prior_audit.NAME = NAME
        with prior_audit.lease():
            baseline = read(EVIDENCE / "result.json")
            baseline_review = read(EVIDENCE / "review.json")
            assert baseline["status"] == baseline_review["status"] == "complete"
            assert sha(EVIDENCE / "result.json") == baseline_review["result_sha256"]
            old_manifest = read(OLD / "episodes.json")
            assert old_manifest["source_games"] == baseline["episode_source_games"]
            assert old_manifest["fractions"] == [0.8, 0.1, 0.1] and old_manifest["seed"] == 0
            daily_review = read(ROOT / "astra-submissions/analysis/daily-refresh-observation-20261111/output-review.json")
            raw = ROOT / "data/raw"
            with (raw / ".writer.lock").open("rb") as lock:
                fcntl.flock(lock, fcntl.LOCK_SH)
                rows, journal = dataset_source_rows(raw / "accepted.jsonl")
            expected = daily_review["raw_snapshot"]
            for key in ("bytes", "sha256", "unique_games", "duplicate_lines"):
                assert journal[key] == expected[key], (key, journal[key], expected[key])
            slim = [{k: row.get(k) for k in ("id", "moves_sha256", "createdAt")} for row in rows]
            del rows
            with (PRIVATE / "journal-split-rows.jsonl").open("x") as stream:
                for row in slim:
                    stream.write(json.dumps(row, separators=(",", ":")) + "\n")
            sources = [Path(__file__), ROOT / "learning/dataset.py",
                       Path(prior_audit.__file__), EVIDENCE / "result.json",
                       EVIDENCE / "review.json", OLD / "episodes.json",
                       ROOT / "tools/daily_refresh.sh",
                       ROOT / "astra-submissions/analysis/daily-refresh-observation-20261111/output-review.json",
                       PRIVATE / "journal-split-rows.jsonl"]
            plan = {"at": now(), "wall_cap_seconds": 180, "journal": journal,
                    "old_index_expected_sha256": baseline["index_sha256"],
                    "source_sha256": {str(p): sha(p) for p in sources},
                    "old_manifest_created_at": old_manifest["created_at"],
                    "current_generation_state": "unfinished; split assignment projection only",
                    "comparison": "All old/new fold cells by game and whole trajectory; no outcome selection or effect-size gate.",
                    "old_subset_reconstruction": "Informational check using current journal order restricted to old IDs, not an assumption that the old journal is available.",
                    "antecedents": "379 verifies the old episode generation and within-generation grouping; 381 pins unresolved original-import metadata. No prior dataset or holdout is rewritten."}
            save(OUT / "plan.json", plan)
            raw_by_id = {r["id"]: r for r in slim}
            old_games = {}
            digest = hashlib.sha256()
            count = 0
            with (OLD / "episode-index.jsonl").open("rb") as stream:
                for line in stream:
                    digest.update(line)
                    r = json.loads(line)
                    game, side = r["id"], r["side"]
                    assert side in (0, 1) and r["split"] in SPLITS
                    assert r["moves_sha256"] == raw_by_id[game]["moves_sha256"]
                    old = old_games.get(game)
                    if old:
                        assert not old[1] & (1 << side)
                        assert (old[0], old[2], old[3]) == (r["split"], r["moves_sha256"], r["source_hash"])
                        old[1] |= 1 << side
                    else:
                        old_games[game] = [r["split"], 1 << side, r["moves_sha256"], r["source_hash"]]
                    count += 1
            assert digest.hexdigest() == plan["old_index_expected_sha256"]
            assert count == baseline["episode_rows"]
            assert len(old_games) == old_manifest["source_games"]
            assert all(r[1] == 3 for r in old_games.values())
            assignment = assign_splits(slim, tuple(old_manifest["fractions"]), old_manifest["seed"])
            old_subset = [r for r in slim if r["id"] in old_games]
            reconstruction = assign_splits(old_subset, tuple(old_manifest["fractions"]), old_manifest["seed"])
            old_reproduction_mismatches = sum(reconstruction[g] != r[0] for g, r in old_games.items())
            game_matrix, group_matrix, new_games, full_counts = Counter(), Counter(), Counter(), Counter()
            group_pairs = defaultdict(set)
            new_group_splits = defaultdict(set)
            old_counts = Counter()
            with (PRIVATE / "projected-folds.jsonl").open("x") as stream:
                for row in slim:
                    game = row["id"]
                    new = assignment[game]
                    full_counts[new] += 1
                    new_group_splits[row["moves_sha256"]].add(new)
                    old = old_games[game][0] if game in old_games else None
                    if old is not None:
                        game_matrix[old, new] += 1
                        old_counts[old] += 1
                        group_pairs[row["moves_sha256"]].add((old, new))
                    else:
                        new_games[new] += 1
                    stream.write(json.dumps({"id": game, "moves_sha256": row["moves_sha256"],
                                             "old_split": old, "projected_split": new}, separators=(",", ":")) + "\n")
            assert all(len(pairs) == 1 for pairs in group_pairs.values())
            assert all(len(folds) == 1 for folds in new_group_splits.values())
            for pairs in group_pairs.values():
                group_matrix[next(iter(pairs))] += 1
            for split in SPLITS:
                assert old_counts[split] == old_manifest["counts"][split]["games"]
            assert sum(game_matrix.values()) == len(old_games)
            assert sum(new_games.values()) == len(slim) - len(old_games)
            assert len(group_pairs) == baseline["episode_distinct_trajectories"]
            for path, expected_sha in plan["source_sha256"].items():
                assert sha(Path(path)) == expected_sha, path
            result = {"at": now(), "status": "complete_projection",
                      "plan_sha256": sha(OUT / "plan.json"),
                      "old_generation": old_manifest["created_at"], "old_games": len(old_games),
                      "old_trajectories": len(group_pairs), "source_games": len(slim),
                      "newly_available_games": sum(new_games.values()),
                      "undated_games": sum(not r["createdAt"] for r in slim),
                      "projected_split_method": "seeded_duplicate_groups_missing_timestamps" if any(not r["createdAt"] for r in slim) else "chronological_duplicate_groups",
                      "old_subset_reconstruction_mismatches": old_reproduction_mismatches,
                      "old_by_projected_game_matrix": matrix(game_matrix),
                      "old_by_projected_trajectory_matrix": matrix(group_matrix),
                      "new_game_counts": dict(new_games), "projected_game_counts": dict(full_counts),
                      "projected_trajectories": len(new_group_splits),
                      "projected_within_generation_cross_fold_groups": 0,
                      "projection_index_sha256": sha(PRIVATE / "projected-folds.jsonl"),
                      "seconds": time.monotonic() - started,
                      "limitations": ["The live export has not published this projection; reconcile actual shard membership when complete.",
                                      "Published old validation/test membership is known; this audit does not establish which training runs consumed it.",
                                      "No replay, date, attribution, split, training model or existing result is repaired or reassigned.",
                                      "No rules/feature/target-semantic certification or playing-strength claim."]}
            save(OUT / "result.json", result)
            state.update(status="complete_projection", result_sha256=sha(OUT / "result.json"))
            print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        prior_audit.update(OUT / "execution.json", state)


if __name__ == "__main__":
    main()
