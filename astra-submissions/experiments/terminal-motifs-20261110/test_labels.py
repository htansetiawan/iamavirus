import unittest
from labels import Native,terminal,ref,chess

class Motifs(unittest.TestCase):
    def test_geometry_and_c_safety(self):
        examples=[
            ('7k/8/1q6/8/8/8/5b2/4K3 w - - 0 1','e1f2','king_bait',True),
            ('7k/8/8/8/8/r7/7K/8 w - - 0 1','h2g3','king_walk',True),
            ('7k/8/8/q7/8/8/3N4/4K3 w - - 0 1','d2c4','opened_king_line',True),
            ('4r2k/8/8/8/8/8/P7/4K3 w - - 0 1','a2a3','ignored_check',True),
            ('k7/8/1b6/8/8/8/8/4K2R w K - 0 1','e1g1','castle_into_attack',True),
            ('1r5k/8/8/8/8/8/1q6/K7 w - - 0 1','a1b2','king_bait',False)]
        native=Native()
        for fen,move,kind,avoidable in examples:
            with self.subTest(kind=kind,avoidable=avoidable):
                row=terminal(ref.FowBoard(fen),chess.Move.from_uci(move),native)
                self.assertEqual(row['kind'],kind);self.assertEqual(bool(row['safe_moves']),avoidable)
                if kind=='opened_king_line':self.assertTrue(any(k['own_screen_released'] for k in row['killers']))
                # Color-swapped mirrored geometry must have the same category.
                board=ref.FowBoard(fen).mirror();mirrored=chess.Move(chess.square_mirror(chess.parse_square(move[:2])),chess.square_mirror(chess.parse_square(move[2:4])))
                mirror=terminal(board,mirrored,native)
                self.assertEqual(mirror['kind'],kind);self.assertEqual(bool(mirror['safe_moves']),avoidable)


if __name__=='__main__':unittest.main()
