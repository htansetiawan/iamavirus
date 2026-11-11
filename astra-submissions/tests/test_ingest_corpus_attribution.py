"""Corpus attribution and immutable-cache regressions for the real importer."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning import histories, ingest


def corpus_line(game_id):
    return next(line for line in (ROOT / "corpus/corpus-all.txt").read_text().splitlines()
                if line.split()[:1] == [game_id])


def write_fixture(tmp_path, lines):
    path = tmp_path / "corpus.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


@pytest.mark.parametrize("game_id,side,opponent,frames", [
    ("13r3tgga", "b", "Knight Vision", 45),
    ("1b8luqb3", "w", "Greek Gift", 152),
])
def test_real_corpus_seats_preserve_replay_without_inventing_identity(
        tmp_path, game_id, side, opponent, frames):
    line = corpus_line(game_id)
    fields = line.split()
    assert fields[1] == side
    source = write_fixture(tmp_path, [line])
    output = tmp_path / "raw"

    counts = ingest.ingest_from_corpus(output, source)
    assert counts == {"accepted": 1, "quarantined": 0, "skipped": 0, "recovered": 0}
    replay = json.loads((output / "games" / game_id / "replay.json").read_text())
    selected, other = ("white", "black") if side == "w" else ("black", "white")
    assert replay[selected] == "Unknown corpus seat"
    assert replay[other] == opponent
    assert replay["whitePlayerId"] is None and replay["blackPlayerId"] is None
    assert replay["source"] == "corpus" and replay["corpusSeat"] == side

    expected = histories.replay_from_moves(
        game_id, fields[5:], fields[2], fields[3].replace("_", " "))
    assert replay["frames"] == expected["frames"]
    assert len(replay["frames"]) == frames
    for key in ("id", "result", "reason", "rulesVersion"):
        assert replay[key] == expected[key]

    row, = [json.loads(line) for line in (output / "accepted.jsonl").read_text().splitlines()]
    assert row[selected] == "Unknown corpus seat" and row[other] == opponent
    assert row["whitePlayerId"] is None and row["blackPlayerId"] is None
    assert row["moves_sha256"] == hashlib.sha256(" ".join(fields[5:]).encode()).hexdigest()
    assert row["plies"] == frames - 1


def test_explicitly_named_iamavirus_opponent_is_retained(tmp_path):
    source = write_fixture(tmp_path, [
        "knowniam b 1-0 King_capturable IAmAVirus e2e4 f7f6 d1h5 g7g5",
    ])
    output = tmp_path / "raw"
    assert ingest.ingest_from_corpus(output, source)["accepted"] == 1
    replay = json.loads((output / "games/knowniam/replay.json").read_text())
    assert replay["white"] == "IAmAVirus"
    assert replay["black"] == "Unknown corpus seat"
    assert replay["whitePlayerId"] is None and replay["blackPlayerId"] is None
    assert replay["corpusSeat"] == "b"


def test_existing_accepted_corpus_bytes_are_not_rewritten(tmp_path):
    line = corpus_line("13r3tgga")
    fields = line.split()
    source = write_fixture(tmp_path, [line])
    output = tmp_path / "raw"
    store = ingest.RawStore(output)
    legacy = histories.replay_from_moves(
        fields[0], fields[5:], fields[2], fields[3].replace("_", " "),
        "Knight Vision", "IAmAVirus")
    legacy.update(whitePlayerId="Knight Vision", blackPlayerId="IAmAVirus", source="corpus")
    problems = ingest.ingest_replay(store, legacy, None, {"replay": {
        "url": "corpus:corpus.txt", "fetched_at": "2000-01-01T00:00:00Z",
        "sha256": hashlib.sha256(line.encode()).hexdigest(), "status": 0, "attempts": 0,
    }}, None)
    assert not problems
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}

    assert ingest.ingest_from_corpus(output, source) == {
        "accepted": 0, "quarantined": 0, "skipped": 1, "recovered": 0,
    }
    assert {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()} == before
