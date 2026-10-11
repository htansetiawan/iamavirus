"""Rules-level, both-color checks for the composable defense-dilemma label."""
import argparse
import sys
import unittest
from m4_information_dilemma import analyze

ap=argparse.ArgumentParser();ap.add_argument('--kit',required=True);args,rest=ap.parse_known_args()
sys.path.insert(0,args.kit);import referee,chess


class DilemmaTests(unittest.TestCase):
    def test_opening_and_mirror(self):
        board=referee.FowBoard('rnb1kbnr/ppp1pppp/8/3q4/8/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3')
        for uci,expected in [('d2d4',1),('b1c3',0),('d1e2',0),('g1f3',0)]:
            move=chess.Move.from_uci(uci);a=analyze(board,move,referee,chess)
            mirrored=board.mirror();m=chess.Move(chess.square_mirror(move.from_square),chess.square_mirror(move.to_square))
            b=analyze(mirrored,m,referee,chess)
            self.assertEqual(a['groups_with_no_universal_survival'],expected)
            for key in ['opponent_legal_replies','continuing_replies','observation_groups','groups_with_no_universal_survival','uniform_reply_min_risk']:
                self.assertEqual(a[key],b[key])
            if expected:
                group=next(g for g in a['groups'] if g['minimum_fatal_worlds'])
                self.assertEqual(group['worlds'],8);self.assertEqual(group['minimum_fatal_worlds'],1)
                proof=group['one_response_minimax_proof'];self.assertEqual(proof['immediate_loss_value'],.5)
                self.assertEqual(sum(proof['defender_mix'].values()),1)
                self.assertEqual(sum(proof['attacker_mix'].values()),1)
                safe=group['safe_by_reply'];r1,r2=proof['attacker_mix']
                self.assertFalse(set(safe[r1])&set(safe[r2]))
                matrix=group['fatal_matrix'];d1,d2=proof['defender_mix']
                self.assertLessEqual(max((x+y)/2 for x,y in zip(matrix[d1],matrix[d2])),.5)


if __name__=='__main__':unittest.main(argv=[sys.argv[0]]+rest)
