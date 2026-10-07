"""The C++ opponent-move features must equal the Python ones on real positions."""
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import pytest

from learning import opponent_model, rules

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / "build" / "opponent_features"
SOURCES = ["opponent_model.cc", "observation.cc", "position.cc", "move.cc", "bitboard.cc"]


@pytest.fixture(scope="module")
def harness():
    if not (ROOT / "opponent_weights.h").exists():
        pytest.skip("opponent_weights.h not generated yet")
    BINARY.parent.mkdir(exist_ok=True)
    sources = [str(ROOT / "tools" / "opponent_features_main.cc")] + [str(ROOT / s) for s in SOURCES]
    subprocess.run(["g++", "-O2", "-std=c++20", "-o", str(BINARY)] + sources, check=True, cwd=ROOT)
    return BINARY


def fen_of(board: rules.Board) -> str:
    rows = []
    text = board.board_string()
    for rank in range(7, -1, -1):
        row, empty = "", 0
        for file in range(8):
            c = text[rank * 8 + file]
            if c == "-":
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += c
        if empty:
            row += str(empty)
        rows.append(row)
    rights = board.castling
    castle = "".join(s for bit, s in ((1 << 7, "K"), (1, "Q"), (1 << 63, "k"), (1 << 56, "q")) if rights & bit) or "-"
    ep = rules.square_name(board.en_passant) if board.en_passant >= 0 else "-"
    return f"{'/'.join(rows)} {'w' if board.side == 0 else 'b'} {castle} {ep} 0 1"


def test_features_agree_on_random_play(harness):
    rng = random.Random(5)
    requests, expected = [], []
    for seed in range(30):
        state = rules.GameState()
        for _ in range(rng.randint(2, 60)):
            if state.outcome() is not None:
                break
            legal = state.board.legal_moves()
            for uci in legal:
                requests.append(f"{fen_of(state.board)};{uci}")
                expected.append(opponent_model.move_features(state.board, uci))
            state.push(rng.choice(legal))
    out = subprocess.run([str(harness)], input="\n".join(requests) + "\n", capture_output=True, text=True, check=True)
    lines = out.stdout.splitlines()
    assert len(lines) == len(expected)
    bad = 0
    for req, want, line in zip(requests, expected, lines):
        assert line not in ("BADFEN", "BADMOVE"), req
        got = np.array(line.split(), dtype=np.float32)
        if not np.allclose(got, want, atol=1e-5):
            bad += 1
            if bad <= 3:
                print(req, "\n  py ", want, "\n  cc ", got)
    assert bad == 0
    assert len(expected) > 5000
