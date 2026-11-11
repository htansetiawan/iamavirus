"""Stable trajectory partitions, actual shard wiring and atomic failure behavior."""
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning import dataset, histories, ingest

POLICY = "trajectory-hash-v1"
MOVES_A = ["e2e4", "f7f6", "d1h5", "g7g5"]
MOVES_B = ["e2e4", "f7f5", "d1h5", "a7a6"]
MOVES_C = ["e2e3", "f7f6", "d1h5", "g7g5"]


def row(game, moves, date=None):
    return {"id": game, "moves_sha256": hashlib.sha256(" ".join(moves).encode()).hexdigest(),
            "createdAt": date}


def add_source(raw, game, moves, date=None):
    replay = histories.replay_from_moves(game, moves, "1-0", "King capturable")
    assert not ingest.validate_replay(replay)[1], "fixture must finish under the rules"
    folder = raw / "games" / game
    folder.mkdir(parents=True)
    (folder / "replay.json").write_text(json.dumps(replay))
    record = row(game, moves, date)
    with (raw / "accepted.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    return record


def source(tmp_path):
    raw = tmp_path / "raw"
    rows = [add_source(raw, "test0001", MOVES_A),
            add_source(raw, "test0002", MOVES_B, "2026-10-25T12:00:00Z"),
            add_source(raw, "copy0001", MOVES_A, "2026-11-10T12:00:00Z")]
    return raw, rows


def read_shards(manifest):
    records = {}
    for split, path in manifest["shards"].items():
        with gzip.open(path, "rt") as stream:
            for line in stream:
                record = json.loads(line)
                assert record["metadata"]["split"] == split
                key = (record["metadata"]["game_id"], record["actor"]["side"])
                assert key not in records
                records[key] = record
    return records


def test_versioned_hash_vectors_cover_all_three_folds():
    # Pinned namespace/seed/byte-encoding vectors, independent of row order.
    vectors = [
        ("9ddd5e31b0f36d2955fd966f1711289ac24385be9ddb543d23d7b947957f9212", "validation"),
        ("33801790090174eec8c3f26857c026739e137adab1ace82002edad78f521be77", "train"),
        ("63948a61582743bc6e6826b15f395e070a228936d6a226178bd698033452c0aa", "test"),
    ]
    rows = [{"id": str(i), "moves_sha256": digest} for i, (digest, _) in enumerate(vectors)]
    assert dataset.assign_splits(rows, policy=POLICY) == {
        str(i): split for i, (_, split) in enumerate(vectors)
    }


def test_membership_survives_growth_reordering_redating_and_removal():
    rows = [{"id": f"g{i}", "moves_sha256": hashlib.sha256(f"sequence-{i}".encode()).hexdigest()}
            for i in range(200)]
    before = dataset.assign_splits(rows[:100], policy=POLICY)
    grown = [dict(r, createdAt="2030-01-01T00:00:00Z") for r in rows]
    grown.append(dict(grown[0], id="same-trajectory-new-id", createdAt=None))
    random.Random(19).shuffle(grown)
    after = dataset.assign_splits(grown, policy=POLICY)
    assert {game: after[game] for game in before} == before
    assert after["same-trajectory-new-id"] == before["g0"]
    subset = grown[::3]
    assert dataset.assign_splits(subset, policy=POLICY) == {r["id"]: after[r["id"]] for r in subset}


def test_invalid_parameters_and_source_identities_are_rejected():
    valid = [row("game0001", MOVES_A)]
    for fractions in ((0.8, 0.1), (0.8, 0.1, 0.2), (-0.1, 0.1, 1),
                      (float("nan"), 0, 1), (float("inf"), 0, 0), None):
        with pytest.raises(ValueError, match="fractions"):
            dataset.assign_splits(valid, fractions=fractions, policy=POLICY)
    for seed in (True, 0.5, "0"):
        with pytest.raises(ValueError, match="integer seed"):
            dataset.assign_splits(valid, seed=seed, policy=POLICY)
    for bad in (None, "not-a-hash", "a" * 63, "A" * 64):
        with pytest.raises(ValueError, match="SHA-256"):
            dataset.assign_splits([dict(valid[0], moves_sha256=bad)], policy=POLICY)
    with pytest.raises(ValueError, match="game IDs"):
        dataset.assign_splits([dict(valid[0], id="")], policy=POLICY)
    with pytest.raises(ValueError, match="conflicting move hashes"):
        dataset.assign_splits(valid + [row("game0001", MOVES_B)], policy=POLICY)
    with pytest.raises(ValueError, match="unknown split policy"):
        dataset.assign_splits(valid, policy="misspelled")
    assert dataset.assign_splits([], policy=POLICY) == {}


def test_actual_shards_keep_both_colors_and_old_examples_stable(tmp_path):
    raw, rows = source(tmp_path)
    target = tmp_path / "published/latest.json"
    first = dataset.build_dataset(raw, target, "latest", split_policy=POLICY)
    before = read_shards(first)
    old_bytes = {path: Path(path).read_bytes() for path in first["shards"].values()}
    add_source(raw, "test0003", MOVES_C)
    add_source(raw, "copy0002", MOVES_A, "2030-01-01T00:00:00Z")
    second = dataset.build_dataset(raw, target, "latest", split_policy=POLICY)
    after = read_shards(second)
    assert first["split_method"] == second["split_method"] == "trajectory_hash_v1"
    assert first["source_games"] == 3 and second["source_games"] == 5
    assert len(before) == 6 and len(after) == 10
    assert all(after[key] == record for key, record in before.items())
    for game in ("test0001", "test0002", "test0003", "copy0001", "copy0002"):
        assert after[(game, 0)]["metadata"]["split"] == after[(game, 1)]["metadata"]["split"]
    for game in ("copy0001", "copy0002"):
        assert after[(game, 0)]["metadata"]["split"] == after[("test0001", 0)]["metadata"]["split"]
    assert all(Path(path).read_bytes() == payload for path, payload in old_bytes.items())


def test_policy_changes_no_episode_content_when_assignments_are_equal(tmp_path):
    raw, _ = source(tmp_path)
    target = tmp_path / "published/latest.json"
    legacy = dataset.build_dataset(raw, target, "latest", fractions=(0, 0, 1))
    stable = dataset.build_dataset(raw, target, "latest", fractions=(0, 0, 1), split_policy=POLICY)
    assert legacy["split_method"] == "seeded_duplicate_groups_missing_timestamps"
    assert read_shards(legacy) == read_shards(stable)
    assert legacy["content_sha256"] == stable["content_sha256"]


@pytest.mark.parametrize("replacement", ["malformed", "0" * 64])
def test_bad_trajectory_hash_rolls_back_without_damaging_published_data(tmp_path, replacement):
    raw, rows = source(tmp_path)
    target = tmp_path / "published/latest.json"
    old = dataset.build_dataset(raw, target, "latest", split_policy=POLICY)
    manifest_bytes = target.read_bytes()
    shards = {p: Path(p).read_bytes() for p in old["shards"].values()}
    generations = set((target.parent / "latest").iterdir())
    rows[0]["moves_sha256"] = replacement
    (raw / "accepted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="SHA-256|move hash differs"):
        dataset.build_dataset(raw, target, "latest", split_policy=POLICY)
    assert target.read_bytes() == manifest_bytes
    assert all(Path(path).read_bytes() == payload for path, payload in shards.items())
    assert set((target.parent / "latest").iterdir()) == generations
    assert list(target.parent.glob(".latest.json-*")) == []


def test_cli_exposes_policy_and_records_its_parameters(tmp_path):
    raw, _ = source(tmp_path)
    target = tmp_path / "published/cli.json"
    assert dataset.main(["--raw", str(raw), "--manifest", str(target),
                         "--split-policy", POLICY, "--seed", "7"]) == 0
    manifest = json.loads(target.read_text())
    assert manifest["split_method"] == "trajectory_hash_v1" and manifest["seed"] == 7
    assert manifest["fractions"] == [0.8, 0.1, 0.1]
    assert len(read_shards(manifest)) == 6
