import unittest

from learning import rules
from reference_proxy_readout import exposure, material


class ExposureTests(unittest.TestCase):
    def test_hidden_pawn_can_attack_a_knight_destination(self):
        state = rules.GameState(rules.Board.from_fen('7k/8/4p3/8/8/2N5/8/K7 w - - 0 1'))
        tag = exposure(state, 'c3d5', 0)
        self.assertTrue(tag['hidden_attacked_piece_move'])
        self.assertEqual(tag['hidden_attackers'], ['e6'])

    def test_hidden_attack_and_recapture_can_be_an_equal_trade(self):
        state = rules.GameState(rules.Board.from_fen('7k/8/4p3/3n4/2B5/8/8/K7 w - - 0 1'))
        before = material(state.board.board_string(), 0)
        tag = exposure(state, 'c4d5', 0)
        self.assertTrue(tag['hidden_attacked_piece_move'])
        self.assertEqual(tag['captured_visible_material'], 3)
        state.push('c4d5'); state.push('e6d5')
        self.assertEqual(material(state.board.board_string(), 0)-before, 0)

    def test_visible_attacker_does_not_count_as_hidden(self):
        state = rules.GameState(rules.Board.from_fen('7k/8/4p3/8/8/1BN5/8/K7 w - - 0 1'))
        self.assertEqual(state.board.observation(0)[rules.square_index('e6')], 'p')
        self.assertFalse(exposure(state, 'c3d5', 0)['hidden_attacked_piece_move'])

    def test_pawn_forward_move_is_not_an_attack(self):
        state = rules.GameState(rules.Board.from_fen('7k/8/8/4p3/8/2N5/8/K7 w - - 0 1'))
        # c3-e4 is attacked by d5/f5 pawns, not e5's forward movement.
        tag = exposure(state, 'c3e4', 0)
        self.assertFalse(tag['hidden_attacked_piece_move'])

    def test_our_recapture_can_repair_an_apparent_two_ply_loss(self):
        state = rules.GameState(rules.Board.from_fen('7k/2n5/8/8/2B5/2N5/8/K7 w - - 0 1'))
        before = material(state.board.board_string(), 0)
        self.assertTrue(exposure(state, 'c3d5', 0)['hidden_attacked_piece_move'])
        state.push('c3d5'); state.push('c7d5')
        self.assertEqual(material(state.board.board_string(), 0)-before, -3)
        state.push('c4d5')
        self.assertEqual(material(state.board.board_string(), 0)-before, 0)


if __name__ == '__main__':
    unittest.main()
