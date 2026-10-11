#!/usr/bin/env python3
"""Audit depth-one perfect-information values against public FOW outcomes.

One deterministically selected nonterminal position per distinct game trajectory.
This is a value-calibration diagnostic under recorded player policies, not an
on-policy strength test or a deployable evaluator. No GPU, credentials or API.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

import chess
import chess.engine


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sigmoid(x):
    return 1/(1+math.exp(-max(-40,min(40,x))))


def calibrate(rows):
    """Two-parameter logistic calibration, Newton updates, tiny ridge penalty."""
    a,b = 1.,0.
    for _ in range(30):
        g0,g1,h00,h01,h11 = .001*a,.001*b,.001,0.,.001
        for r in rows:
            x = max(-20,min(20,r['cp']/200))
            p = sigmoid(a*x+b); d = p-r['target']; h = max(1e-9,p*(1-p))
            g0 += d*x; g1 += d; h00 += h*x*x; h01 += h*x; h11 += h
        det=h00*h11-h01*h01
        da=(h11*g0-h01*g1)/det; db=(h00*g1-h01*g0)/det
        # Bounded Newton steps avoid a separable tiny sample diverging.
        scale=max(1,abs(da),abs(db))
        a-=da/scale; b-=db/scale
        if max(abs(da),abs(db))<1e-8: break
    return a,b


def summarize(rows, a, b):
    bins = [[] for _ in range(10)]
    raw_brier=cal_brier=raw_log=cal_log=0.
    for r in rows:
        p=r['expected_score'];q=sigmoid(a*max(-20,min(20,r['cp']/200))+b);y=r['target']
        raw_brier+=(p-y)**2;cal_brier+=(q-y)**2
        for value,name in [(p,'raw'),(q,'cal')]:
            value=max(1e-9,min(1-1e-9,value));loss=-(y*math.log(value)+(1-y)*math.log(1-value))
            if name=='raw':raw_log+=loss
            else:cal_log+=loss
        bins[min(9,int(p*10))].append(r)
    return {'games':len(rows),'raw_brier':raw_brier/len(rows),'calibrated_brier':cal_brier/len(rows),
            'raw_log_loss':raw_log/len(rows),'calibrated_log_loss':cal_log/len(rows),
            'bins':[{'range':[i/10,(i+1)/10],'n':len(rs),
                     'mean_expected_score':sum(r['expected_score'] for r in rs)/len(rs),
                     'mean_recorded_score':sum(r['target'] for r in rs)/len(rs)}
                    for i,rs in enumerate(bins) if rs]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--stockfish',type=Path,required=True)
    p.add_argument('--referee',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--games',type=int,default=1000)
    p.add_argument('--selection-from',type=Path,help='Reuse a frozen candidate order; retain the original run and rescore under the corrected FEN-only protocol')
    args=p.parse_args()
    if args.games<100 or not args.cache.is_dir():p.error('Need at least 100 games and an existing shared cache')
    args.out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('calibration_referee',args.referee)
    referee=importlib.util.module_from_spec(spec);spec.loader.exec_module(referee)
    candidates=sorted((x for x in args.cache.iterdir() if x.is_dir()),key=lambda x:digest(('m4-value-20261011/'+x.name).encode()))
    previous=None
    if args.selection_from:
        previous=json.loads((args.selection_from/'manifest.json').read_text())
        for key,path in [('stockfish_sha256',args.stockfish),('referee_sha256',args.referee)]:
            if digest(path.read_bytes())!=previous[key]:p.error('Frozen dependency changed: '+key)
        if str(args.cache.resolve())!=previous['cache']:p.error('Frozen cache path changed')
        candidates=[args.cache/gid for gid in previous['candidate_ids']]
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'requested_games':args.games,
        'tool_sha256':digest(Path(__file__).read_bytes()),'stockfish_sha256':digest(args.stockfish.read_bytes()),
        'referee_sha256':digest(args.referee.read_bytes()),'cache':str(args.cache.resolve()),
        'selection':'One seeded-uniform nonterminal frame (ply>=2) per unique entire move trajectory; deterministic hash order over cached game IDs.',
        'settings':{'depth':1,'Threads':1,'Hash':16,'input':'current FEN only; no FOW move history','hard_analysis_timeout_seconds':10},'classification':'calibration diagnostic only; no engine or arena change',
        'candidate_ids':[x.name for x in candidates]}
    if previous:
        manifest['previous_run']={'path':str(args.selection_from.resolve()),
            'manifest_sha256':digest((args.selection_from/'manifest.json').read_bytes()),
            'positions_sha256':digest((args.selection_from/'positions.jsonl').read_bytes()),
            'reason':'Original samples retained in place. Rescore the same positions using FEN snapshots because FOW castling histories can be invalid for orthodox Stockfish.'}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    seen=set();rows=[];skips=Counter()
    with chess.engine.SimpleEngine.popen_uci(str(args.stockfish.resolve()),timeout=10) as engine, (args.out/'positions.jsonl').open('w') as output:
        engine.configure({'Threads':1,'Hash':16})
        for directory in candidates:
            path=directory/'replay.json'
            if not path.exists():skips['missing_replay']+=1;continue
            raw=path.read_bytes();game=json.loads(raw);frames=game['frames']
            if game.get('reason') not in ('King capturable','Threefold repetition','50-move rule'):
                skips['other_termination']+=1;continue
            if len(frames)<5:skips['short_game']+=1;continue
            trajectory=digest(' '.join(f['move'] for f in frames[1:]).encode())
            if trajectory in seen:skips['duplicate_trajectory']+=1;continue
            seen.add(trajectory)
            rng=random.Random(int(trajectory[:16],16))
            ply=rng.randrange(2,len(frames)-1)
            board=referee.FowBoard();repetitions=Counter({referee.position_key(board):1})
            for f in frames[1:ply+1]:
                assert referee.outcome(board,repetitions) is None
                board.push_uci(f['move']);repetitions[referee.position_key(board)]+=1
            assert referee.outcome(board,repetitions) is None
            encoded=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
            assert encoded==frames[ply]['board']
            assert all(referee.observation(board,color)==frames[ply][key] for color,key in [(True,'white'),(False,'black')])
            # FOW permits castling through attacked squares. Orthodox engines
            # must not replay that move stack even when the present board is valid.
            snapshot=chess.Board(board.fen())
            if not snapshot.is_valid():
                raise ValueError(f'Unsupported orthodox position: {game["id"]} ply {ply}: {snapshot.status()}')
            try:
                with engine.analysis(snapshot,chess.engine.Limit(depth=1),game=trajectory) as analysis:
                    # Depth-only SimpleEngine.analyse has no whole-search timeout.
                    # Bound the future explicitly without changing the UCI limit.
                    import asyncio
                    future=asyncio.run_coroutine_threadsafe(analysis.inner.wait(),engine.protocol.loop)
                    future.result(timeout=10)
                    score=analysis.info['score'].white()
            except Exception as error:
                (args.out/'failure.json').write_text(json.dumps({'game':game['id'],'ply':ply,
                    'fen':board.fen(),'completed':len(rows),'error':type(error).__name__,'message':str(error)},indent=2)+'\n')
                raise
            cp=score.score(mate_score=10000)
            y={'1-0':1.,'0-1':0.,'1/2-1/2':.5}[game['result']]
            x={'game':game['id'],'path':str(path.resolve()),'sha256':digest(raw),'trajectory':trajectory,
               'split':'test' if int(trajectory[16:24],16)%5==0 else 'train',
               'ply':ply,'plies':len(frames)-1,'white':game['white'],'black':game['black'],
               'white_version':game.get('whiteVersion'),'black_version':game.get('blackVersion'),
               'created_at':game.get('createdAt'),'fen':board.fen(),'cp':cp,'mate':score.mate(),
               'expected_score':sigmoid(cp/200),'target':y,
               'mover_in_check':board.is_attacked_by(not board.turn,board.king(board.turn)),
               'hidden_king_attack':any(frames[ply]['white' if board.turn else 'black'][s]=='?' for s in board.attackers(not board.turn,board.king(board.turn)))}
            output.write(json.dumps(x)+'\n');output.flush();rows.append(x)
            if len(rows)%100==0:print(json.dumps({'collected':len(rows),'skips':dict(skips)}),flush=True)
            if len(rows)>=args.games:break
    train=[r for r in rows if r['split']=='train'];test=[r for r in rows if r['split']=='test']
    if not train or not test:raise ValueError('No train/test split; collection retained')
    a,b=calibrate(train)
    elite={'Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','duck','Instructors','Mist Opportunities'}
    top=[r for r in test if r['white'] in elite and r['black'] in elite]
    result={'classification':manifest['classification'],'positions':len(rows),'skips':dict(skips),
        'calibration_fit':{'a':a,'b':b,'formula':'expected score = sigmoid(a*clip(cp/200,-20,20)+b)'},
        'held_out_games':summarize(test,a,b),'held_out_elite_pairs':summarize(top,a,b) if top else None,
        'limitations':['Recorded outcome depends on player policies and strength; this is not the game-theoretic value of a board.',
          'Single-PV depth-one scores at a position can differ from its parent MultiPV child score in the deployed search.',
          'A game-trajectory split prevents exact game duplicates crossing folds; repeated positions or related player versions may still cross folds.',
          'The fitted scalar calibration is a diagnostic and is not deployed. Better Brier score does not establish stronger play.']}
    (args.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    if previous:
        old={r['game']:r for r in map(json.loads,(args.selection_from/'positions.jsonl').read_text().splitlines())}
        comparison=[{'game':r['game'],'same_position':r['fen']==old[r['game']]['fen'],
                     'old_cp':old[r['game']]['cp'],'fen_cp':r['cp']} for r in rows if r['game'] in old]
        (args.out/'previous-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
