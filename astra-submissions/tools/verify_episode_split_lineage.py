"""Independently reduce saved fold projections with set intersections."""
from collections import defaultdict
from datetime import datetime, timezone
from itertools import groupby
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/episode-split-lineage-20261111"
PRIVATE = ROOT / "data/astra-spool/episode-split-lineage-20261111"
OLD = ROOT / "data/astra-spool/training-artifact-readiness-20261111"
SPLITS = ("train", "validation", "test")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    plan, result, execution = (read(OUT / name) for name in ("plan.json", "result.json", "execution.json"))
    assert result["status"] == execution["status"] == "complete_projection"
    assert sha(OUT / "result.json") == execution["result_sha256"]
    assert sha(OUT / "plan.json") == result["plan_sha256"]
    assert execution["seconds"] <= plan["wall_cap_seconds"]
    for path, expected in plan["source_sha256"].items():
        assert sha(Path(path)) == expected
    assert sha(OLD / "episode-index.jsonl") == plan["old_index_expected_sha256"]
    assert sha(PRIVATE / "projected-folds.jsonl") == result["projection_index_sha256"]
    old_rows = sorted((r["id"], r["side"], r["split"], r["moves_sha256"])
                      for r in (json.loads(line) for line in (OLD / "episode-index.jsonl").open()))
    old_games, old_ids, old_groups = {}, defaultdict(set), defaultdict(set)
    for game, group in groupby(old_rows, key=lambda r: r[0]):
        rows = list(group)
        assert len(rows) == 2 and [r[1] for r in rows] == [0, 1]
        assert rows[0][2:] == rows[1][2:]
        fold, sequence = rows[0][2:]
        old_games[game] = (fold, sequence)
        old_ids[fold].add(game)
        old_groups[fold].add(sequence)
    source_rows = [json.loads(line) for line in (PRIVATE / "journal-split-rows.jsonl").open()]
    source = {r["id"]: r for r in source_rows}
    assert len(source) == len(source_rows) == result["source_games"]
    projections = [json.loads(line) for line in (PRIVATE / "projected-folds.jsonl").open()]
    projected = {r["id"]: r for r in projections}
    assert len(projected) == len(projections) and projected.keys() == source.keys()
    new_ids, new_groups = defaultdict(set), defaultdict(set)
    for game, r in projected.items():
        assert r["projected_split"] in SPLITS
        assert r["moves_sha256"] == source[game]["moves_sha256"]
        if game in old_games:
            assert (r["old_split"], r["moves_sha256"]) == old_games[game]
        else:
            assert r["old_split"] is None
        new_ids[r["projected_split"]].add(game)
        new_groups[r["projected_split"]].add(r["moves_sha256"])
    for a in SPLITS:
        for b in SPLITS:
            if a != b:
                assert not (old_groups[a] & old_groups[b])
                assert not (new_groups[a] & new_groups[b])
    game_matrix = {a: {b: len(old_ids[a] & new_ids[b]) for b in SPLITS} for a in SPLITS}
    group_matrix = {a: {b: len(old_groups[a] & new_groups[b]) for b in SPLITS} for a in SPLITS}
    assert game_matrix == result["old_by_projected_game_matrix"]
    assert group_matrix == result["old_by_projected_trajectory_matrix"]
    assert len(old_games) == result["old_games"]
    assert sum(map(len, old_groups.values())) == result["old_trajectories"]
    assert sum(map(len, new_groups.values())) == result["projected_trajectories"]
    assert {s: len(new_ids[s]) for s in SPLITS} == result["projected_game_counts"]
    added = set(projected) - set(old_games)
    assert len(added) == result["newly_available_games"]
    assert {s: len(added & new_ids[s]) for s in SPLITS} == result["new_game_counts"]
    assert sum(not r.get("createdAt") for r in source_rows) == result["undated_games"]
    assert not any(r["owner"] == "astra-episode-split-lineage-20261111"
                   for r in read(ROOT / "chatroom/cores.json")["allocation"])
    review = {"at": datetime.now(timezone.utc).isoformat(), "status": "complete_projection_review",
              "result_sha256": sha(OUT / "result.json"), "review_source_sha256": sha(Path(__file__)),
              "old_games": len(old_games), "source_games": len(source),
              "old_test_games_projected_train": game_matrix["test"]["train"],
              "old_validation_games_projected_train": game_matrix["validation"]["train"],
              "old_train_games_projected_test": game_matrix["train"]["test"],
              "checks": ["Old audited index hash and both-color pairing match.",
                         "Frozen journal metadata and every projected ID/trajectory match.",
                         "All nine game and trajectory cells independently reconcile by set intersection.",
                         "Projected counts and newly available IDs reconcile; no within-generation group straddles folds.",
                         "Original source pins, execution wall cap and released lease verified."],
              "scope": "Independent saved-metadata reduction; not an actual-shard audit or a model-training/strength result."}
    with (OUT / "review.json").open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
