"""Recurrent event parity: the C++ tracker and the Python tracker must produce
identical planes, scalars, en passant, castling rights and candidate lists over
the same ordered events, for both colours, on real and random histories."""
import random
import subprocess
from pathlib import Path

import numpy as np
import pytest

from learning import features, histories, ingest, rules

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / "build" / "neural_features"
SOURCES = ["neural_observation.cc", "observation.cc", "position.cc", "move.cc", "bitboard.cc"]


@pytest.fixture(scope="module")
def harness():
    BINARY.parent.mkdir(exist_ok=True)
    sources = [str(ROOT / "tools" / "neural_features_main.cc")] + [str(ROOT / s) for s in SOURCES]
    subprocess.run(["g++", "-O2", "-std=c++20", "-o", str(BINARY)] + sources, check=True, cwd=ROOT)
    return BINARY


def random_replay(seed, max_plies=100):
    rng = random.Random(seed)
    state = rules.GameState()
    moves = []
    while state.outcome() is None and len(moves) < max_plies:
        moves.append(rng.choice(state.board.legal_moves()))
        state.push(moves[-1])
    result, reason = state.outcome() or ("1/2-1/2", "Move limit reached")
    return histories.replay_from_moves(f"par{seed:05d}", moves, result, reason)


def compare(harness, episode):
    actor = episode.actor
    own = dict(zip(actor.decision_event_indices, actor.own_actions))
    script = [f"side {actor.side}"]
    tracker = features.FeatureTracker(actor.side)
    expected = []
    for i, (view, phase, ply) in enumerate(zip(actor.observations, actor.phases, actor.plies)):
        script.append(f"obs {phase} {ply} {view}")
        script.append("dump")
        tracker.observe(view, phase, ply)
        expected.append((tracker.planes().reshape(-1).copy(), tracker.scalars().copy(),
                         tracker.en_passant(), tracker.castling_bitboard(), tracker.legal_candidates()))
        if i in own:
            script.append(f"move {own[i]}")
            tracker.record_own_move(own[i])
    out = subprocess.run([str(harness)], input="\n".join(script) + "\n", capture_output=True, text=True, check=True)
    lines = out.stdout.splitlines()
    assert len(lines) == 5 * len(expected)
    for k, (planes, scalars, ep, rights, cands) in enumerate(expected):
        got_planes = np.array(lines[5 * k].split()[1:], dtype=np.float32)
        got_scalars = np.array(lines[5 * k + 1].split()[1:], dtype=np.float32)
        assert np.array_equal(got_planes, planes), (episode.metadata.game_id, k)
        assert np.allclose(got_scalars, scalars, atol=1e-6), (episode.metadata.game_id, k)
        assert int(lines[5 * k + 2].split()[1]) == ep
        assert int(lines[5 * k + 3].split()[1]) == rights
        assert lines[5 * k + 4].split()[1:] == cands
    return len(expected)


def test_parity_on_random_histories(harness):
    events = 0
    for seed in range(25):
        replay = random_replay(seed)
        states, problems = ingest.validate_replay(replay)
        assert not problems
        for side in (0, 1):
            events += compare(harness, histories.build_episode(replay, states, side, "fow-v1"))
    assert events > 1000


def test_parity_on_corpus_games(harness):
    corpus = ROOT / "corpus" / "corpus-all.txt"
    lines = corpus.read_text().splitlines()[:12]
    for line in lines:
        fields = line.split()
        replay = histories.replay_from_moves(fields[0], fields[5:], fields[2], fields[3].replace("_", " "))
        states, problems = ingest.validate_replay(replay)
        assert not problems, problems
        for side in (0, 1):
            compare(harness, histories.build_episode(replay, states, side, "fow-v1"))


def test_fog_and_visible_empty_are_separate_planes():
    """features-v2: an unseen square lights plane 12, a visibly empty square plane 13."""
    from learning import features, rules
    tracker = features.FeatureTracker(rules.WHITE)
    view = rules.START_BOARD.replace("p", "?").replace("r", "?").replace("n", "?").replace("b", "?").replace("q", "?").replace("k", "?")
    tracker.observe(view, features.PHASE_INITIAL, 0)
    planes = tracker.planes().reshape(features.NUM_PLANES, 64)
    e3 = 2 * 8 + 4   # visibly empty for White at the start
    a7 = 6 * 8 + 0   # unseen for White at the start
    assert planes[13, e3] == 1.0 and planes[12, e3] == 0.0
    assert planes[12, a7] == 1.0 and planes[13, a7] == 0.0
    assert planes[0:14].sum(axis=0).max() == 1.0
