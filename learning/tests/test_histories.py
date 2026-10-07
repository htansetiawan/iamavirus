import random

import numpy as np

from learning import features, histories, ingest, labels, rules


def _episode(moves, result="1-0", reason="King capturable", side=0):
    replay = histories.replay_from_moves("test0001", moves, result, reason)
    states, problems = ingest.validate_replay(replay)
    assert not problems, problems
    return histories.build_episode(replay, states, side, "fow-v1")


# A real terminal line: 1. e4 f6 2. Qh5 g5?? leaves Black's king capturable
# (there is no checkmate here; the losing move is the one that ignores Qh5).
FOOLS_MATE = ["e2e4", "f7f6", "d1h5", "g7g5"]


def test_white_and_black_event_rhythm():
    white = _episode(FOOLS_MATE, result="1-0", side=0)
    black = _episode(FOOLS_MATE, result="1-0", side=1)
    # Five frames; the terminal frame is not delivered under a normal ending.
    assert len(white.actor.observations) == 4
    assert white.actor.phases == [features.PHASE_INITIAL, features.PHASE_AFTER_OWN,
                                  features.PHASE_AFTER_OPPONENT, features.PHASE_AFTER_OWN]
    assert white.actor.decision_event_indices == [0, 2]
    assert white.actor.own_actions == ["e2e4", "d1h5"]
    assert black.actor.phases == [features.PHASE_INITIAL, features.PHASE_AFTER_OPPONENT,
                                  features.PHASE_AFTER_OWN, features.PHASE_AFTER_OPPONENT]
    assert black.actor.decision_event_indices == [1, 3]
    assert black.actor.own_actions == ["f7f6", "g7g5"]


def test_frame_action_alignment_predicts_the_following_frames_move():
    moves = FOOLS_MATE
    ep = _episode(moves, result="1-0", side=0)
    for index, t in enumerate(ep.actor.decision_event_indices):
        assert ep.actor.own_actions[index] == moves[t]
        assert ep.actor.own_actions[index] in ep.actor.legal_actions[index]


def test_technical_forfeit_masks_policy_and_value_but_keeps_belief():
    moves = ["e2e4", "e7e5"]
    ep = _episode(moves, result="0-1", reason="Time forfeit", side=0)
    assert ep.metadata.termination == histories.TERMINATION_TIME
    # The failed decision at frame 2 has no move and so is not a demonstration;
    # the delivered views still include frame 2.
    assert len(ep.actor.observations) == 3
    assert ep.num_decisions == 1
    assert ep.targets.policy_valid == [False]
    assert ep.targets.value_valid == [False]
    assert ep.targets.belief_valid == [True]
    assert ep.targets.terminal_return == 0.0


def test_king_loss_labels_and_terminal_return():
    white = _episode(FOOLS_MATE, result="1-0", side=0)
    assert white.targets.terminal_return == 1.0
    black = _episode(FOOLS_MATE, result="1-0", side=1)
    assert black.targets.terminal_return == -1.0
    # At Black's second decision (frame 3, after Qh5) g7g5 loses the king on
    # the spot while g7g6 blocks; the label is one-move, from the true board.
    i = black.actor.decision_event_indices.index(3)
    legal = black.actor.legal_actions[i]
    assert black.targets.king_loss_by_action[i][legal.index("g7g5")] == 1
    assert black.targets.king_loss_by_action[i][legal.index("g7g6")] == 0
    assert black.targets.demonstrated_actions[i] == "g7g5"


def test_information_isolation_features_ignore_truth():
    moves = FOOLS_MATE
    replay = histories.replay_from_moves("iso00001", moves, "1-0", "King capturable")
    states, _ = ingest.validate_replay(replay)
    ep = histories.build_episode(replay, states, 0, "fow-v1")
    own = {i: m for i, m in zip(ep.actor.decision_event_indices, ep.actor.own_actions)}
    planes, scalars = features.replay_events(0, ep.actor.observations, ep.actor.phases, ep.actor.plies, own)
    # Alter truth and metadata; the actor record is untouched, so features match.
    ep.targets.boards = ["-" * 64] * len(ep.targets.boards)
    ep.targets.terminal_return = 0.0
    ep.metadata.opponent_id = "someone-else"
    planes2, scalars2 = features.replay_events(0, ep.actor.observations, ep.actor.phases, ep.actor.plies, own)
    assert np.array_equal(planes, planes2) and np.array_equal(scalars, scalars2)
    # One active channel per square among the current-observation planes.
    assert np.all(planes[:, :14].sum(axis=1) == 1.0)


def test_candidate_parity_over_random_games():
    rng = random.Random(11)
    total = 0
    for seed in range(40):
        state = rules.GameState()
        moves = []
        while state.outcome() is None and len(moves) < 120:
            legal = state.board.legal_moves()
            moves.append(rng.choice(legal))
            state.push(moves[-1])
        result, reason = state.outcome() or ("1/2-1/2", "Move limit reached")
        replay = histories.replay_from_moves(f"rand{seed:04d}", moves, result, reason)
        states, problems = ingest.validate_replay(replay)
        assert not problems
        for side in (0, 1):
            ep = histories.build_episode(replay, states, side, "fow-v1")
            assert ep.metadata.candidate_mismatches == []
            total += ep.num_decisions
    assert total > 500


def test_castling_rights_are_sticky_and_en_passant_is_inferred():
    tracker = features.FeatureTracker(0)
    tracker.observe(rules.START_BOARD.replace("p", "?").replace("r", "?").replace("n", "?").replace("b", "?").replace("q", "?").replace("k", "?"), features.PHASE_INITIAL, 0)
    assert tracker.kingside and tracker.queenside
    tracker.record_own_move("h1h2")
    assert not tracker.kingside and tracker.queenside
    # Rook back home never restores the right.
    tracker.observe(rules.START_BOARD, features.PHASE_AFTER_OPPONENT, 2)
    assert not tracker.kingside
    # En passant: ...d5 next to our e5 pawn.
    state = rules.GameState()
    t = features.FeatureTracker(0)
    t.observe(state.board.observation(0), features.PHASE_INITIAL, 0)
    for i, m in enumerate(["e2e4", "a7a6", "e4e5", "d7d5"]):
        if i % 2 == 0:
            t.record_own_move(m)
        state.push(m)
        t.observe(state.board.observation(0), features.PHASE_AFTER_OWN if i % 2 == 0 else features.PHASE_AFTER_OPPONENT, i + 1)
    assert t.en_passant() == rules.square_index("d6")
    assert "e5d6" in t.legal_candidates()
    assert sorted(t.legal_candidates()) == sorted(state.board.legal_moves())


def test_hidden_enemy_classes():
    board = rules.Board()
    classes, hidden = labels.hidden_enemy_classes(board.board_string(), board.observation(0), 0)
    assert hidden.sum() == 32 and classes[rules.square_index("e8")] == 5
    assert classes[rules.square_index("e1")] == labels.NO_ENEMY
