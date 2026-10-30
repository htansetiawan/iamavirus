import unittest

from learning import rules
from reference_replay_gate import score


def fixture(moves):
    state = rules.GameState()
    states = [state.copy()]
    def frame(move):
        return {'board': state.board.board_string(), 'white': state.board.observation(0),
                'black': state.board.observation(1), 'move': move}
    frames = [frame(None)]
    for move in moves:
        state.push(move); states.append(state.copy()); frames.append(frame(move))
    return states, {'frames': frames}


class ReplayContinuationTests(unittest.TestCase):
    def test_identical_history_allows_recorded_reply(self):
        states, replay = fixture(['e2e4', 'e7e5', 'g1f3'])
        result = score(states[0], 'e2e4', 0, replay, 0)
        self.assertTrue(result['recorded_reply_usable'])
        self.assertEqual(result['recorded_reply'], 'e7e5')

    def test_changed_opponent_view_censors_reply(self):
        states, replay = fixture(['e2e4', 'e7e5', 'g1f3'])
        result = score(states[1], 'd7d5', 1, replay, 1)
        self.assertFalse(result['recorded_reply_usable'])
        self.assertEqual(result['reply_censored_reason'], 'opponent observation changed')

    def test_fatal_move_stops_before_recorded_reply(self):
        states, replay = fixture(['f2f3', 'e7e5', 'g2g4', 'd8h4', 'a2a3'])
        result = score(states[4], 'a2a3', 0, replay, 4)
        self.assertTrue(result['fatal'])
        self.assertEqual(result['terminal_after_choice'][0], '0-1')
        self.assertFalse(result['recorded_reply_usable'])

    def test_illegal_candidate_cannot_be_scored_as_success(self):
        states, replay = fixture(['e2e4', 'e7e5'])
        self.assertEqual(score(states[0], 'e2e5', 0, replay, 0), {'legal': False})


if __name__ == '__main__': unittest.main()
