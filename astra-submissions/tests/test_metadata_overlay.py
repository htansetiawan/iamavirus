"""Real historical seats, immutable source binding and metadata-only export."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning import dataset, histories, ingest
from learning.metadata_overlay import FIELDS, load_metadata_overlay

ASSET = ROOT / "astra-submissions/analysis/corpus-metadata-overlay-20261111/overlay.json"
ASSET_SHA256 = "cf894da62d06b1da39dccae2cfe635b08301fe4efaf21ee93bbd7c0d3701ae5b"
GAMES = ("13r3tgga", "1b8luqb3")
POLICY = "trajectory-hash-v1"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def source(tmp_path):
    # Reconstruct the EXACT legacy bytes from the committed genuine move lists.
    # No private recovery directory or network is needed by these tests.
    raw = tmp_path / "raw"
    rows = []
    for line in (ROOT / "corpus/corpus-all.txt").read_text().splitlines():
        fields = line.split()
        if not fields or fields[0] not in GAMES:
            continue
        game, side, result, reason, opponent = fields[:5]
        opponent = opponent.replace("_", " ")
        replay = histories.replay_from_moves(
            game, fields[5:], result, reason.replace("_", " "),
            opponent if side == "b" else "IAmAVirus",
            "IAmAVirus" if side == "b" else opponent)
        replay.update(whitePlayerId=replay["white"], blackPlayerId=replay["black"], source="corpus")
        payload = json.dumps(replay, indent=1, sort_keys=True).encode()
        record = load_metadata_overlay(ASSET).records[game]
        assert sha(payload) == record["original_sha256"]
        folder = raw / "games" / game
        folder.mkdir(parents=True)
        (folder / "replay.json").write_bytes(payload)
        rows.append({"id": game, "moves_sha256": ingest.replay_hash(replay), "createdAt": None,
                     "white": replay["white"], "black": replay["black"],
                     "whitePlayerId": replay["whitePlayerId"], "blackPlayerId": replay["blackPlayerId"],
                     "whiteVersion": None, "blackVersion": None})
    assert {row["id"] for row in rows} == set(GAMES)
    journal = raw / "accepted.jsonl"
    journal.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return raw, rows


def episodes(manifest):
    result = {}
    for split, path in manifest["shards"].items():
        with gzip.open(path, "rt") as stream:
            for line in stream:
                episode = json.loads(line)
                assert episode["metadata"]["split"] == split
                key = (episode["metadata"]["game_id"], episode["actor"]["side"])
                assert key not in result
                result[key] = episode
    return result


def test_portable_asset_contains_only_verified_metadata():
    overlay = load_metadata_overlay(ASSET)
    assert overlay.sha256 == ASSET_SHA256 and len(overlay.records) == 164
    assert all(set(record["metadata"]) == FIELDS for record in overlay.records.values())
    assert overlay.records["13r3tgga"]["metadata"]["black"] == "TA Baseline P"
    assert overlay.records["1b8luqb3"]["metadata"]["white"] == "duck"


def test_actual_export_corrects_metadata_preserves_actors_targets_and_raw(tmp_path):
    raw, rows = source(tmp_path)
    source_bytes = {path: path.read_bytes() for path in raw.rglob("*") if path.is_file()}
    target = tmp_path / "published/latest.json"
    first = dataset.build_dataset(raw, target, "latest", split_policy=POLICY)
    old_shards = {Path(path): Path(path).read_bytes() for path in first["shards"].values()}
    second = dataset.build_dataset(raw, target, "latest", split_policy=POLICY, metadata_overlay=ASSET)
    before, after = episodes(first), episodes(second)
    assert len(before) == len(after) == 4
    assert first["undated_source_games"] == 2 and second["undated_source_games"] == 0
    assert first["source_journal"] == second["source_journal"]
    assert "metadata_overlay" not in first
    assert first["content_sha256"] != second["content_sha256"]
    overlay = load_metadata_overlay(ASSET)
    effective, applied = overlay.apply_rows(rows)
    assert set(applied) == set(GAMES) and all(row["createdAt"].endswith("+00:00") for row in effective)
    for row in effective:
        assert row["createdAt"] == overlay.records[row["id"]]["metadata"]["createdAt"]
        assert len(row["createdAt"].split(".")[1].split("+")[0]) == 9
    allowed_changes = {"player_id", "opponent_id", "played_version", "opponent_version"}
    for (game, side), episode in after.items():
        prior = before[(game, side)]
        assert episode["actor"] == prior["actor"] and episode["targets"] == prior["targets"]
        metadata = overlay.records[game]["metadata"]
        color, other = ("white", "black") if side == 0 else ("black", "white")
        assert episode["metadata"]["player_id"] == metadata[f"{color}PlayerId"]
        assert episode["metadata"]["opponent_id"] == metadata[f"{other}PlayerId"]
        assert episode["metadata"]["played_version"] == metadata[f"{color}Version"]
        assert episode["metadata"]["opponent_version"] == metadata[f"{other}Version"]
        assert episode["metadata"]["source_hash"] == overlay.records[game]["original_sha256"]
        assert {key: value for key, value in episode["metadata"].items() if key not in allowed_changes} == {
            key: value for key, value in prior["metadata"].items() if key not in allowed_changes}
    info = second["metadata_overlay"]
    assert (info["records"], info["applied_games"], info["unused_records"]) == (164, 2, 162)
    assert info["sha256"] == ASSET_SHA256
    assert Path(info["path"]).read_bytes() == ASSET.read_bytes()
    assert all(path.read_bytes() == payload for path, payload in source_bytes.items())
    assert all(path.read_bytes() == payload for path, payload in old_shards.items())


def test_date_recovery_changes_adaptive_method_without_claiming_old_holdout(tmp_path):
    raw, _ = source(tmp_path)
    target = tmp_path / "published/latest.json"
    old = dataset.build_dataset(raw, target, "latest")
    new = dataset.build_dataset(raw, target, "latest", metadata_overlay=ASSET)
    assert old["split_method"] == "seeded_duplicate_groups_missing_timestamps"
    assert new["split_method"] == "chronological_duplicate_groups"


@pytest.mark.parametrize("change", [
    "format", "duplicate", "record-type", "id", "original-hash", "moves-hash", "response-hash",
    "forbidden-frames", "forbidden-current-version", "bad-version", "boolean-version",
    "bad-name", "bad-player-id", "naive-date", "invalid-date", "empty-metadata",
])
def test_invalid_overlays_are_rejected(tmp_path, change):
    data = json.loads(ASSET.read_text())
    record = data["records"][0]
    metadata = record["metadata"]
    if change == "format":
        data["format"] = "unsupported"
    elif change == "duplicate":
        data["records"].append(deepcopy(record))
    elif change == "record-type":
        data["records"][0] = None
    elif change == "id":
        record["id"] = "../other"
    elif change.endswith("-hash"):
        record[{"original-hash": "original_sha256", "moves-hash": "moves_sha256",
                "response-hash": "response_sha256"}[change]] = "not-a-hash"
    elif change == "forbidden-frames":
        metadata["frames"] = []
    elif change == "forbidden-current-version":
        metadata["whiteCurrentVersion"] = 100
    elif change == "bad-version":
        metadata["whiteVersion"] = -1
    elif change == "boolean-version":
        metadata["blackVersion"] = True
    elif change == "bad-name":
        metadata["white"] = ""
    elif change == "bad-player-id":
        metadata["blackPlayerId"] = 12
    elif change == "naive-date":
        metadata["createdAt"] = "2026-10-07T05:00:00"
    elif change == "invalid-date":
        metadata["createdAt"] = "2026-99-07T05:00:00Z"
    elif change == "empty-metadata":
        record["metadata"] = {}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_metadata_overlay(path)


@pytest.mark.parametrize("change", ["raw-bytes", "journal-moves", "overlay-moves"])
def test_stale_source_rejection_preserves_published_generation(tmp_path, change):
    raw, rows = source(tmp_path)
    target = tmp_path / "published/latest.json"
    first = dataset.build_dataset(raw, target, "latest", metadata_overlay=ASSET)
    original_manifest = target.read_bytes()
    referenced = [Path(path) for path in first["shards"].values()] + [Path(first["metadata_overlay"]["path"])]
    original_files = {path: path.read_bytes() for path in referenced}
    generations = set((target.parent / "latest").iterdir())
    overlay_path = ASSET
    if change == "raw-bytes":
        path = raw / "games" / GAMES[0] / "replay.json"
        path.write_bytes(path.read_bytes() + b"\n")
    elif change == "journal-moves":
        rows[0]["moves_sha256"] = "0" * 64
        (raw / "accepted.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    else:
        data = json.loads(ASSET.read_text())
        next(r for r in data["records"] if r["id"] == GAMES[0])["moves_sha256"] = "0" * 64
        overlay_path = tmp_path / "stale.json"
        overlay_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="raw source differs|journal move hash differs"):
        dataset.build_dataset(raw, target, "latest", metadata_overlay=overlay_path)
    assert target.read_bytes() == original_manifest
    assert all(path.read_bytes() == payload for path, payload in original_files.items())
    assert set((target.parent / "latest").iterdir()) == generations
    assert not list(target.parent.glob(".latest.json-*"))


def test_real_cli_and_snapshot_remain_bound_after_input_changes(tmp_path):
    raw, _ = source(tmp_path)
    target = tmp_path / "published/cli.json"
    portable = tmp_path / "input-overlay.json"
    portable.write_bytes(ASSET.read_bytes())
    assert dataset.main(["--raw", str(raw), "--manifest", str(target),
                         "--metadata-overlay", str(portable), "--split-policy", POLICY]) == 0
    manifest = json.loads(target.read_text())
    assert manifest["metadata_overlay"]["applied_games"] == 2 and len(episodes(manifest)) == 4
    snapshot = Path(manifest["metadata_overlay"]["path"])
    assert snapshot.read_bytes() == portable.read_bytes()
    portable.write_text("replacement input")
    assert sha(snapshot.read_bytes()) == manifest["metadata_overlay"]["sha256"] == ASSET_SHA256


def test_overlay_replay_binding_and_unmatched_sources():
    overlay = load_metadata_overlay(ASSET)
    record = overlay.records[GAMES[0]]
    with pytest.raises(ValueError, match="raw source differs"):
        overlay.apply_replay(GAMES[0], {"id": "bad-id"}, record["original_sha256"])
    with pytest.raises(ValueError, match="replay move hash differs"):
        overlay.apply_replay(GAMES[0], {"id": GAMES[0], "frames": []}, record["original_sha256"])
    unmatched = {"id": "newgame0", "moves_sha256": "1" * 64}
    assert overlay.apply_rows([unmatched]) == ([unmatched], [])
    assert overlay.apply_replay("newgame0", unmatched, "0" * 64) is unmatched
