import random

from learning import action_codec, rules


def test_every_legal_move_round_trips_for_both_colours():
    rng = random.Random(3)
    seen_castle = seen_ep = seen_promotion = 0
    for _ in range(150):
        state = rules.GameState()
        for _ in range(rng.randint(0, 60)):
            if state.outcome() is not None:
                break
            for uci in state.board.legal_moves():
                side = state.board.side
                action = action_codec.encode_action(uci, side)
                assert 0 <= action < action_codec.NUM_ACTIONS
                assert action_codec.decode_action(action, side) == uci
                if uci in ("e1g1", "e1c1", "e8g8", "e8c8") and state.board.piece_at(action_codec.square_index(uci[:2])) % 6 == 5:
                    seen_castle += 1
                if len(uci) == 5:
                    seen_promotion += 1
                if state.board.en_passant >= 0 and uci[2:4] == action_codec.square_name(state.board.en_passant) and state.board.piece_at(action_codec.square_index(uci[:2])) % 6 == 0:
                    seen_ep += 1
            state.push(rng.choice(state.board.legal_moves()))
    assert seen_castle > 0 and seen_ep > 0 and seen_promotion > 0


def test_promotions_are_distinct_and_black_is_reflected():
    ids = {action_codec.encode_action("e7e8" + s, 0) for s in "qrbn"}
    assert len(ids) == 4
    # e7e8 for White and e2e1 for Black map to the same canonical pair.
    assert action_codec.encode_action("e7e8q", 0) == action_codec.encode_action("e2e1q", 1)
    assert action_codec.canonical_square(action_codec.square_index("a1"), 1) == action_codec.square_index("a8")
    assert action_codec.canonical_bitboard(0xFF, 1) == 0xFF << 56
    assert action_codec.canonical_bitboard(action_codec.canonical_bitboard(0x123456789ABCDEF0, 1), 1) == 0x123456789ABCDEF0
