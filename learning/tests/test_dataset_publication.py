"""A failed daily rebuild must never damage the dataset a reader already has."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from learning import dataset, histories


@pytest.fixture
def raw(tmp_path):
    raw = tmp_path / "raw"
    game = raw / "games" / "test0001"
    game.mkdir(parents=True)
    moves = ["e2e4", "f7f6", "d1h5", "g7g5"]
    replay = histories.replay_from_moves("test0001", moves, "1-0", "King capturable")
    (game / "replay.json").write_text(json.dumps(replay))
    (raw / "accepted.jsonl").write_text(json.dumps({
        "id": "test0001", "moves_sha256": "one-game", "createdAt": "2026-10-25T12:00:00Z"
    }) + "\n")
    return raw


def published_bytes(manifest):
    return {name: Path(path).read_bytes() for name, path in manifest["shards"].items()}


def test_generations_preserve_existing_readers_and_symlink(raw, tmp_path):
    target = tmp_path / "store" / "latest.json"
    first = dataset.build_dataset(raw, target, "latest")
    before = published_bytes(first)
    alias = tmp_path / "manifest-link.json"
    alias.symlink_to(target)
    second = dataset.build_dataset(raw, alias, "latest")
    assert alias.is_symlink()
    assert json.loads(alias.read_text()) == second
    assert first["shards"] != second["shards"]
    assert first["content_sha256"] == second["content_sha256"]
    assert published_bytes(first) == before
    assert sum(s.get("episodes", 0) for s in second["counts"].values()) == 2
    for split, path in second["shards"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == second["shard_sha256"][split]
        with gzip.open(path, "rt") as f:
            records = [json.loads(line) for line in f]
        assert len(records) == second["counts"][split].get("episodes", 0)


@pytest.mark.parametrize("failure", ["episode", "trailer", "manifest_replace"])
def test_failed_rebuild_keeps_old_manifest_and_shards(raw, tmp_path, monkeypatch, failure):
    path = tmp_path / "store" / "latest.json"
    old = dataset.build_dataset(raw, path, "latest")
    manifest_before = path.read_bytes()
    shards_before = published_bytes(old)
    generations_before = set(path.parent.joinpath("latest").iterdir())
    if failure == "episode":
        original = histories.build_episode
        calls = 0

        def interrupt(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated interrupted export after first episode")
            return original(*args, **kwargs)

        monkeypatch.setattr(histories, "build_episode", interrupt)
    elif failure == "trailer":
        original = dataset._build_dataset_generation

        def truncate(*args, **kwargs):
            result = original(*args, **kwargs)
            shard = Path(result["shards"]["train"])
            shard.write_bytes(shard.read_bytes()[:-8])
            return result

        monkeypatch.setattr(dataset, "_build_dataset_generation", truncate)
    else:
        def deny_replace(*args):
            raise OSError("simulated manifest publication failure")

        monkeypatch.setattr(dataset.os, "replace", deny_replace)
    with pytest.raises((OSError, EOFError)):
        dataset.build_dataset(raw, path, "latest")
    assert path.read_bytes() == manifest_before
    assert published_bytes(old) == shards_before
    assert set(path.parent.joinpath("latest").iterdir()) == generations_before
    assert list(path.parent.glob(".latest.json-*")) == []
