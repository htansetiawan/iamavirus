#!/usr/bin/env python3
"""Regression: hidden opponent movement must not inherit our own view change.

Run with the starter kit Python (python-chess), passing its referee directory.
"""
import argparse
from collections import Counter
import sys

from m4_match_audit import audit


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kit', required=True)
    args=ap.parse_args()
    sys.path.insert(0,args.kit)
    import referee
    board=referee.FowBoard();frames=[];repetitions=Counter()
    for ply,uci in enumerate([None,'d2d4','e7e6','g1f3','d7d5','e2e4','f8b4','f3e5']):
        if uci:board.push_uci(uci)
        repetitions[referee.position_key(board)]+=1
        frames.append({'ply':ply,'move':uci,'board':''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)),
                       'white':referee.observation(board,True),'black':referee.observation(board,False),'clocks':[180,180]})
    result,reason=referee.outcome(board,repetitions)
    assert (result,reason)==('0-1','King capturable')
    game={'id':'fixture','result':result,'reason':reason,'frames':frames}
    assert frames[0]['white']!=frames[1]['white']  # d4 changes our view.
    assert frames[1]['white']==frames[2]['white']  # ...e6 is invisible.
    report=audit(game,'white',referee)
    assert report['decisions'][1]['ply']==2
    assert report['decisions'][1]['opponent_move_changed_view'] is False
    for side in ['white','black']:
        report=audit(game,side,referee)
        for decision in report['decisions']:
            ply=decision['ply']
            expected=ply==0 or frames[ply-1][side]!=frames[ply][side]
            assert decision['opponent_move_changed_view']==expected,(side,decision)
    print('test_m4_match_audit: actual pre/post-opponent views, both colors, hidden e6 and terminal rules passed')


if __name__=='__main__':main()
