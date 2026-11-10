"""Bounded oracle material census on previously frozen own TRAIN games only."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/endgame-opportunity-20261110'
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')


def setup():
    OUT.mkdir(exist_ok=False)
    old=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
    source=json.loads(old.read_text())
    games=[g for g in source['games'] if g['split']=='train' and 'IAmAVirus' in (g['white'],g['black'])]
    assert len(games)==302
    plan=dict(at=datetime.now(timezone.utc).isoformat(),games=games,
        dependencies={str(p):sha(p) for p in (old,HERE/'census.py',ROOT.parent/'fow-starter/referee.py')},
        cores=[4,5],max_seconds=120,
        classification='At nonterminal positions before our move, exactly kings plus Q, R or RR for either side; the other side has only its king. Record first entry by side/family.',
        outcomes='Course-referee terminal result at final recorded frame only. Nonterminal endings remain unknown, never zero-filled or inferred from material.',
        priority_threshold=10,
        scope='Oracle descriptive opportunity census on old302 own TRAIN games, not a runtime trigger, strategy test, current-v38 estimate, held-out prediction or strength result. No295future game/model opened.',
        decision='Only at least10 known nonwins plus unresolved cases after an own QK/RRK entry earns a separate metadata-and-policy feasibility design. Otherwise close bare-king conversion as a primary strength track on this panel. Not a theorem about all future endgames.')
    write(OUT/'plan.json',plan)
    print(json.dumps(dict(prepared=True,games=len(games),plan_sha256=sha(OUT/'plan.json'))),flush=True)


def census():
    start=time.monotonic();plan=json.loads((OUT/'plan.json').read_text())
    assert not (OUT/'execution.json').exists(),'one attempt only'
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    os.sched_setaffinity(0,set(plan['cores']))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('120-second bound')))
    signal.alarm(plan['max_seconds'])
    receipt=dict(started_at=datetime.now(timezone.utc).isoformat(),status='running');write(OUT/'execution.json',receipt)
    rows=[];frames=0
    try:
        for g in plan['games']:
            assert hashlib.sha256(' '.join(g['moves']).encode()).hexdigest()==g['sequence_sha256']
            board=ref.FowBoard();repetitions=Counter({ref.position_key(board):1});entries={}
            own=g['white']=='IAmAVirus'
            terminal=None
            for ply in range(len(g['moves'])+1):
                frames+=1;terminal=ref.outcome(board,repetitions)
                assert terminal is None or ply==len(g['moves']),(g['game'],ply,'recorded continuation after course terminal',terminal)
                if terminal is None and board.turn==own:
                    for strong in (True,False):
                        a=Counter(p.symbol().upper() for s,p in board.piece_map().items() if p.color==strong)
                        b=Counter(p.symbol().upper() for s,p in board.piece_map().items() if p.color!=strong)
                        family=next((name for name,pattern in [('QK',Counter(K=1,Q=1)),('RK',Counter(K=1,R=1)),('RRK',Counter(K=1,R=2))] if a==pattern),None)
                        if family and b==Counter(K=1):
                            key=('own' if strong==own else 'opponent')+'-'+family
                            entries.setdefault(key,dict(ply=ply,halfmove_clock=board.halfmove_clock,fen=board.fen()))
                if ply==len(g['moves']):break
                action=ref.chess.Move.from_uci(g['moves'][ply]);assert action in ref.fow_moves(board),(g['game'],ply,'illegal move')
                board.push(action);repetitions[ref.position_key(board)]+=1
            point=None if terminal is None else (.5 if terminal[0]=='1/2-1/2' else float((terminal[0]=='1-0')==own))
            rows.append(dict(game=g['game'],white=g['white'],black=g['black'],white_version=g['white_version'],black_version=g['black_version'],
                             plies=len(g['moves']),entries=entries,course_terminal=terminal,own_score=point))
        families={}
        for key in ('own-QK','own-RK','own-RRK','opponent-QK','opponent-RK','opponent-RRK'):
            group=[r for r in rows if key in r['entries']]
            families[key]=dict(games=len(group),known_wins=sum(r['own_score']==1 for r in group),known_draws=sum(r['own_score']==.5 for r in group),
                               known_losses=sum(r['own_score']==0 for r in group),unknown=sum(r['own_score'] is None for r in group),
                               game_ids=[r['game'] for r in group])
        potential=[r for r in rows if any(k in r['entries'] for k in ('own-QK','own-RRK')) and r['own_score']!=1]
        ceiling=sum(1-r['own_score'] if r['own_score'] is not None else 1 for r in potential)
        write(OUT/'games.json',rows)
        result=dict(at=datetime.now(timezone.utc).isoformat(),games=len(rows),frames=frames,families=families,
            own_QK_or_RRK_nonwins_plus_unknown=len(potential),optimistic_missing_game_points=ceiling,
            optimistic_score_ceiling=ceiling/len(rows),
            decision='separate_metadata_and_policy_design_only' if len(potential)>=plan['priority_threshold'] else 'close_primary_conversion_track_on_this_panel',
            scope=plan['scope'],plan_sha256=sha(OUT/'plan.json'),games_sha256=sha(OUT/'games.json'),
            caution='Material and true-state labels are oracle analysis. They do not establish the bot can certify a bare king from its information or force a win before repetition/50-move draws.')
        write(OUT/'result.json',result);print(json.dumps(result,indent=2),flush=True);receipt.update(status='complete',decision=result['decision'])
    except BaseException as exc:
        receipt.update(status='failed',error=repr(exc),completed_games=len(rows));raise
    finally:
        signal.alarm(0);receipt.update(ended_at=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-start)
        (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--prepare':setup()
    else:census()
