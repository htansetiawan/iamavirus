"""Differential test of learning.rules against referee.py over random play.

Every move, observation, repetition key and terminal verdict the simulator
produces must match the arena's own implementation, because every label and
every reward in this package is derived from them.
"""
import random
from collections import Counter

import pytest

from learning import rules


def play_random_game(referee, seed, max_plies=200):
    import chess

    rng = random.Random(seed)
    truth = referee.FowBoard()
    repetitions = Counter({referee.position_key(truth): 1})
    ours = rules.GameState(max_plies=1000)
    steps = 0
    while steps < max_plies:
        expected = referee.outcome(truth, repetitions)
        actual = ours.outcome()
        assert actual == expected, (seed, steps, truth.fen())
        if expected is not None:
            return steps, expected
        for side, color in ((chess.WHITE, rules.WHITE), (chess.BLACK, rules.BLACK)):
            assert ours.board.observation(color) == referee.observation(truth, side)
        want = sorted(m.uci() for m in referee.fow_moves(truth))
        got = sorted(ours.board.legal_moves())
        assert got == want, (seed, steps, truth.fen())
        assert ours.board.board_string() == "".join(
            truth.piece_at(sq).symbol() if truth.piece_at(sq) else "-" for sq in range(64))
        assert ours.board.halfmove_clock == truth.halfmove_clock
        move = rng.choice(want)
        truth.push(chess.Move.from_uci(move))
        repetitions[referee.position_key(truth)] += 1
        ours.push(move)
        # Repetition keys must identify the same positions as the referee's.
        assert ours.repetitions[ours.board.repetition_key()] == repetitions[referee.position_key(truth)]
        steps += 1
    return steps, None


def test_random_games_agree_with_referee(referee):
    terminal = Counter()
    for seed in range(60):
        _, outcome = play_random_game(referee, seed)
        if outcome:
            terminal[outcome[1]] += 1
    assert terminal["King capturable"] > 0


def test_fifty_move_and_repetition_draws(referee):
    import chess

    # Two kings shuffling: a repetition arrives first.
    truth = referee.FowBoard("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    ours = rules.GameState(board=rules.Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1"))
    repetitions = Counter({referee.position_key(truth): 1})
    line = ["e1e2", "e8e7", "e2e1", "e7e8"] * 2
    for move in line:
        assert ours.outcome() == referee.outcome(truth, repetitions)
        truth.push(chess.Move.from_uci(move))
        repetitions[referee.position_key(truth)] += 1
        ours.push(move)
    assert ours.outcome() == ("1/2-1/2", "Threefold repetition")

    # The halfmove clock: 100 plies of knight wandering with no repetition.
    ours = rules.GameState(board=rules.Board.from_fen("4k3/8/8/8/8/8/8/4K2N w - - 0 1"))
    ours.board.halfmove_clock = 99
    ours.push("h1g3")
    assert ours.outcome() == ("1/2-1/2", "50-move rule")


def test_en_passant_only_counts_in_the_key_when_capturable(referee):
    import chess

    # A double push next to nothing: the key must ignore the en passant square,
    # exactly as referee.position_key does.
    truth = referee.FowBoard()
    ours = rules.GameState()
    for move in ["e2e4", "a7a6", "e4e5", "d7d5"]:
        truth.push(chess.Move.from_uci(move))
        ours.push(move)
    assert ours.board.en_passant == rules.square_index("d6")
    assert any(truth.generate_pseudo_legal_ep())
    truth2 = referee.FowBoard()
    ours2 = rules.GameState()
    for move in ["a2a3", "a7a6", "a3a4", "d7d5"]:
        truth2.push(chess.Move.from_uci(move))
        ours2.push(move)
    assert not any(truth2.generate_pseudo_legal_ep())
    # Same board reached with and without an irrelevant ep square must collide.
    plain = rules.Board.from_fen("rnbqkbnr/1pp1pppp/p7/3p4/P7/8/1PPPPPPP/RNBQKBNR w KQkq - 0 3")
    assert plain.repetition_key() == ours2.board.repetition_key()


def test_king_loss_label_matches_referee_outcome(referee):
    import chess

    rng = random.Random(7)
    checked = 0
    for _ in range(200):
        truth = referee.FowBoard()
        ours = rules.Board()
        for _ in range(rng.randint(0, 30)):
            moves = referee.fow_moves(truth)
            if not moves or referee.outcome(truth, Counter()) is not None:
                break
            move = rng.choice(moves).uci()
            truth.push(chess.Move.from_uci(move))
            ours.push(move)
        if referee.outcome(truth, Counter()) is not None:
            continue
        for move in referee.fow_moves(truth):
            truth.push(move)
            king = truth.king(not truth.turn)
            lost = king is None or truth.is_attacked_by(truth.turn, king)
            truth.pop()
            assert ours.move_loses_king(move.uci()) == lost
            checked += 1
    assert checked > 1000
