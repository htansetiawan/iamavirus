import unittest

from learning import rules
from fresh_taxonomy_gate import exchange_probe, material_horizons, protocol


def state(fen):
    return rules.GameState(board=rules.Board.from_fen(fen))


class FreshGateTests(unittest.TestCase):
    def test_castling_rights_and_no_check_rule_are_preserved(self):
        s = state('k3r3/8/8/8/8/8/8/4K2R w K - 0 1')
        self.assertIn('e1g1', s.board.legal_moves())
        result = exchange_probe(s, 'e1g1')
        self.assertTrue(result['legal'])
        self.assertFalse(result['fatal'])

    def test_en_passant_not_lost_by_board_only_reconstruction(self):
        s = rules.GameState()
        for move in ['e2e4', 'a7a6', 'e4e5', 'd7d5']:
            s.push(move)
        result = exchange_probe(s, 'e5d6')
        self.assertTrue(result['legal'])
        self.assertFalse(result['fatal'])

    def test_material_label_waits_for_both_armies_at_same_frame(self):
        def board(white, black):
            return (white+black).ljust(64, '-')
        frames = [{'board': b} for b in [board('KQR', 'kqr'), board('KQR', 'kqr'),
                                        board('KR', 'kqr'), board('KR', 'kr')]]
        self.assertEqual(material_horizons(frames, 0, 0), {'2': 9, '3': 0})
        self.assertEqual(material_horizons(frames, 0, 1), {'2': -9, '3': 0})
        self.assertIsNone(material_horizons(frames[:3], 0, 0)['3'])

    def test_suicidal_recapture_is_not_material_compensation(self):
        # After e2e4, ...Rd2 wins Q. Kxd2 would enter Bg5's diagonal.
        s = state('k2r4/8/8/6b1/8/8/3QP3/4K3 w - - 0 1')
        result = exchange_probe(s, 'e2e4')
        self.assertFalse(result['fatal'])
        self.assertEqual(result['queen_exchange_loss'], 9)

    def test_safe_recapture_reduces_net_loss(self):
        s = state('k2r4/8/8/8/8/8/3QP3/4K3 w - - 0 1')
        result = exchange_probe(s, 'e2e4')
        self.assertEqual(result['queen_exchange_loss'], 4)

    def test_terminal_king_loss_and_illegal_are_distinct(self):
        s = state('k3r3/8/8/8/8/8/6P1/4K3 w - - 0 1')
        self.assertTrue(exchange_probe(s, 'g2g3')['fatal'])
        self.assertEqual(exchange_probe(s, 'g2g5'), {'legal': False})

    def test_protocol_contains_only_our_views_and_own_forced_moves(self):
        frames = [{'white': 'W'*64, 'black': 'B'*64, 'board': 'SECRET', 'clocks': [180, 180], 'move': None},
                  {'white': 'X'*64, 'black': 'C'*64, 'board': 'SECRET', 'clocks': [179, 180], 'move': 'e2e4'},
                  {'white': 'Y'*64, 'black': 'D'*64, 'board': 'SECRET', 'clocks': [179, 178], 'move': 'e7e5'}]
        feed, forced = protocol({'frames': frames, 'timeControl': {'baseSeconds': 60, 'incrementSeconds': 1}}, 2, 0)
        self.assertEqual(forced, ['e2e4'])
        self.assertIn('w 60 1', feed)
        self.assertNotIn('SECRET', feed)
        self.assertNotIn('e7e5', feed)
        self.assertNotIn('B'*64, feed)
        self.assertIn('X'*64, feed)  # the after-own-move observation is also real input


if __name__ == '__main__':
    unittest.main()
