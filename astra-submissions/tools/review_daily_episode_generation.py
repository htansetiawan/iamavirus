"""Independent saved-index/fold reductions after the full daily shard scan."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import groupby
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.dataset import dataset_source_rows

OUT = ROOT / "astra-submissions/analysis/daily-episode-generation-20261111"
PRIVATE = ROOT / "data/astra-spool/daily-episode-generation-20261111"
PROJECTION = ROOT / "data/astra-spool/episode-split-lineage-20261111/projected-folds.jsonl"
SPLITS = ("train", "validation", "test")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    plan, result, execution = (read(OUT / name) for name in ("plan.json", "result.json", "execution.json"))
    assert result["status"] == execution["status"] == "complete" and execution["completed_files"] == 3
    assert sha(OUT / "result.json") == execution["result_sha256"]
    assert sha(OUT / "plan.json") == result["plan_sha256"] == execution["plan_sha256"]
    assert execution["seconds"] <= plan["wall_seconds"]
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    assert sha(PRIVATE / "episode-index.jsonl") == result["index_sha256"]
    raw_rows, journal = dataset_source_rows(PRIVATE / "journal-prefix.jsonl")
    assert journal == plan["source_journal"]
    raw = {r["id"]: r for r in raw_rows}
    index = sorted((r["id"], r["side"], r["split"], r["moves_sha256"], r["source_hash"])
                   for r in (json.loads(line) for line in (PRIVATE / "episode-index.jsonl").open()))
    actual, counts = {}, Counter()
    for game, group in groupby(index, key=lambda row: row[0]):
        rows = list(group)
        assert len(rows) == 2 and [r[1] for r in rows] == [0, 1]
        assert rows[0][2:] == rows[1][2:]
        assert rows[0][3] == raw[game]["moves_sha256"]
        actual[game] = rows[0][2:]
        counts[rows[0][2]] += 1
    assert actual.keys() == raw.keys()
    manifest = read(PRIVATE / "manifest.json")
    assert len(index) == result["episode_rows"] == 2 * len(actual)
    assert len(actual) == result["source_games"] == manifest["source_games"]
    for split in SPLITS:
        assert counts[split] == manifest["counts"][split]["games"]
        assert 2 * counts[split] == manifest["counts"][split]["episodes"]
    trajectory_splits = []
    for sequence, group in groupby(sorted({(row[1], row[0]) for row in actual.values()}), key=lambda r: r[0]):
        folds = {r[1] for r in group}
        trajectory_splits.append((sequence, folds))
    overlaps = {sequence: sorted(folds) for sequence, folds in trajectory_splits if len(folds) > 1}
    assert overlaps == read(PRIVATE / "cross-fold-groups.json")
    assert len(overlaps) == result["cross_fold_trajectory_groups"]
    assert len(trajectory_splits) == result["distinct_trajectories"]
    projected = {r["id"]: r for r in (json.loads(line) for line in PROJECTION.open())}
    assert projected.keys() == actual.keys()
    transition_counts, transition_groups = Counter(), defaultdict(set)
    for game, (fold, sequence, _) in actual.items():
        p = projected[game]
        assert (fold, sequence) == (p["projected_split"], p["moves_sha256"])
        if p["old_split"] is not None:
            transition_counts[p["old_split"], fold] += 1
            transition_groups[sequence].add((p["old_split"], fold))
    group_counts = Counter()
    for pairs in transition_groups.values():
        assert len(pairs) == 1
        group_counts[next(iter(pairs))] += 1
    matrix = lambda values: {a: {b: values[a, b] for b in SPLITS} for a in SPLITS}
    old_review = read(ROOT / "astra-submissions/analysis/episode-split-lineage-20261111/result.json")
    assert matrix(transition_counts) == old_review["old_by_projected_game_matrix"]
    assert matrix(group_counts) == old_review["old_by_projected_trajectory_matrix"]
    for spec in plan["files"]:
        stat = Path(spec["path"]).stat()
        assert (stat.st_dev, stat.st_ino, stat.st_size) == (spec["device"], spec["inode"], spec["bytes"])
        receipt = next(r for r in result["file_receipts"] if r["split"] == spec["split"])
        assert (receipt["bytes"], receipt["sha256"]) == (spec["bytes"], spec["sha256"])
    assert result["complete_move_hashes_verified"] + result["declared_mismatch_games_not_move_reconstructed"] == len(actual)
    assert not any(r["owner"] == "astra-daily-episode-generation-20261111" for r in read(ROOT / "chatroom/cores.json")["allocation"])
    review = {"at": datetime.now(timezone.utc).isoformat(), "status": "complete_index_review",
              "result_sha256": sha(OUT / "result.json"), "review_source_sha256": sha(Path(__file__)),
              "source_games": len(actual), "episode_rows": len(index), "game_counts": dict(counts),
              "distinct_trajectories": len(trajectory_splits), "cross_fold_trajectory_groups": len(overlaps),
              "all_actual_folds_match_saved_projection": True,
              "actual_old_by_new_game_matrix": matrix(transition_counts),
              "actual_old_by_new_trajectory_matrix": matrix(group_counts),
              "scope": "Independent sorted color/index/source coverage and fold reductions, original file-receipt reconciliation and lease release. No second gzip scan or rules/target-feature recertification, archive or strength claim."}
    with (OUT / "review.json").open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
