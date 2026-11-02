"""Select unused games and exclude all experiment237 canonical states.

The older-unused and new-date cohorts are reported separately. This is not a
claim that the older cohort is a forward-in-time test. No model scores enter
selection. Baselines use the original validated parent MultiPV collector.
"""
from collections import Counter
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
from common import HERE, ROOT, OUT, OLD, OLDOUT, digest, now, sha, write_new

spec=importlib.util.spec_from_file_location('old_data',OLD/'data.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def freeze():
    previous=json.loads((OLDOUT/'games.json').read_text())
    ids={g['row']['id'] for g in previous};trajectories={g['row']['moves_sha256'] for g in previous}
    snapshot=ROOT/'astra-submissions/analysis/arena-refresh-20261102-search/standings.json'
    teams={p['id'] for p in json.loads(snapshot.read_text())['players'] if p['rank']<=12}
    index=ROOT/'data/raw/accepted.jsonl';payload=index.read_bytes()
    rows={r['id']:r for r in map(json.loads,payload.splitlines())}
    eligible=[r for r in rows.values() if r['id'] not in ids and r['moves_sha256'] not in trajectories
        and r.get('termination')=='normal' and r.get('whitePlayerId') in teams and r.get('blackPlayerId') in teams
        and ('2026-10-25'<=r.get('createdAt','')<'2026-10-31' or '2026-11-02'<=r.get('createdAt','')<'2026-11-03')]
    groups={'older_unused':[],'new_date':[]};seen=set(trajectories)
    for r in sorted(eligible,key=lambda r:(r['createdAt'],r['id'])):
        if r['moves_sha256'] in seen:continue
        seen.add(r['moves_sha256'])
        groups['older_unused' if r['createdAt']<'2026-11-02' else 'new_date'].append(r)
    games=[]
    for group,limit in [('older_unused',1000),('new_date',500)]:
        chosen=sorted(groups[group],key=lambda r:digest(('238-holdout:'+r['id']).encode()))[:limit]
        for row in sorted(chosen,key=lambda r:(r['createdAt'],r['id'])):
            path=ROOT/'data/raw/games'/row['id']/'replay.json'
            games.append(dict(group=group,row=row,path=str(path.relative_to(ROOT)),sha256=sha(path)))
    assert len(groups['new_date'])>=100 and len(games)>=1000
    write_new(OUT/'games.json',games)
    dependencies=[Path(__file__),OLD/'data.py',OLD/'build/leaf_collect',old.BASE/'bin/stockfish',
        OLD/'work/dataset/data.npz',OLD/'work/pilot/data.npz',OLDOUT/'games.json',OLDOUT/'plan.json',
        OLDOUT/'dataset-review.json']
    plan=json.loads((OLDOUT/'plan.json').read_text())
    pins={str(p):sha(p) for p in dependencies}
    pins.update(plan['dependencies'])
    write_new(OUT/'holdout-selection.json',dict(at=now(),selection='Hash selected games, no outcome or model score filter.',
        eligible=len(eligible),available={k:len(v) for k,v in groups.items()},selected=dict(Counter(g['group'] for g in games)),
        games_sha256=sha(OUT/'games.json'),index_sha256=digest(payload),snapshot_sha256=sha(snapshot),dependencies=pins,
        source_corpus_games=len(rows),prior_games_excluded=len(ids),prior_trajectories_excluded=len(trajectories),
        feature_rule='Exclude canonical states from all 237 train, validation, opened test and pilot rows; deduplicate new cohorts jointly.',
        primary='Pooled equal-game prediction loss; require nonworse point loss on new-date cohort separately.',
        scope='Unused cached older games plus disjoint new-date cohort. No claim of prospective arena evaluation.'))
    print(json.dumps({'selected':dict(Counter(g['group'] for g in games)),'manifest_sha256':sha(OUT/'games.json')}),flush=True)


def load():
    plan=json.loads((OUT/'holdout-selection.json').read_text())
    assert sha(OUT/'games.json')==plan['games_sha256']
    for name,h in plan['dependencies'].items():assert sha(ROOT/name)==h,name
    return plan,json.loads((OUT/'games.json').read_text())


def extract():
    plan,games=load();target=HERE/'work/holdout';target.mkdir(parents=True,exist_ok=False)
    begin=time.monotonic();seen={};old_rows=0
    for path in (OLD/'work/dataset/data.npz',OLD/'work/pilot/data.npz'):
        with np.load(path) as d:x=d['x'];h=d['half']
        for row,v in zip(x,h):seen[digest(row.tobytes()+bytes([int(v)]))]='237';old_rows+=1
    # Read only old feature arrays, never its labels or predictions.
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','OMP_','MKL_'))}
    env.update(MIST_SF_WORKERS='1',MIST_SF_MULTIPV='256',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    stderr=(target/'collector.stderr').open('x')
    proc=subprocess.Popen([str(OLD/'build/leaf_collect'),str(old.BASE/'bin/stockfish')],stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1,env=env,start_new_session=True)
    write_new(target/'started.json',dict(at=now(),pid=os.getpid(),collector_pid=proc.pid,selection_sha256=sha(OUT/'holdout-selection.json')))
    arrays={k:[] for k in ('x','half','y','sf','game','group','hidden_threat')};skips=Counter();frames=0;actions=0
    try:
        with gzip.open(target/'rows.jsonl.gz','wt') as rows,gzip.open(target/'native.jsonl.gz','wt') as native:
            for gi,g in enumerate(games):
                path=ROOT/g['path'];assert sha(path)==g['sha256'];r=json.loads(path.read_text())
                assert old.ingest.replay_hash(r)==g['row']['moves_sha256']
                states,errors=old.ingest.validate_replay(r);assert not errors,(r['id'],errors);frames+=len(states)
                for ply in old.chosen_frames(r['id'],states):
                    board=states[ply].board;parent=states[ply-1].board;x,half,key=old.encode(board)
                    if key in seen:skips[seen[key]]+=1;continue
                    seen[key]=g['group'];ident=f"{r['id']}:{ply}";move=r['frames'][ply]['move']
                    proc.stdin.write(f'{ident} {parent.board_string()} {parent.side} {parent.castling:x} {parent.en_passant} {parent.halfmove_clock} {move}\n');proc.stdin.flush()
                    response=proc.stdout.readline();assert response,('collector EOF',ident,proc.poll())
                    v=json.loads(response);assert v['id']==ident and not v['terminal']
                    for k in ('board','white','black'):assert v[k]==r['frames'][ply][k],(ident,k)
                    assert v['side']==board.side and int(v['castle'],16)==board.castling and v['ep']==board.en_passant and v['halfmove']==board.halfmove_clock
                    action=next(a for a in v['actions'] if a['move']==move)
                    if action['found']:assert abs(v['value']+math.tanh(action['cp']/400))<1e-12
                    label=.5 if r['result']=='1/2-1/2' else float((r['result']=='1-0')==(board.side==0))
                    hidden=False
                    for attacker in (0,1):
                        king=board.king_square(attacker^1)
                        if board.is_attacked(king,attacker):
                            import chess
                            from learning.move_taxonomy import fen
                            b=chess.Board(fen(board.board_string()));colour=chess.WHITE if attacker==0 else chess.BLACK
                            hidden|=any(board.observation(attacker^1)[sq]=='?' for sq in b.attackers(colour,king))
                    values=dict(x=x,half=half,y=label,sf=(v['value']+1)/2,game=gi,
                        group=('older_unused','new_date').index(g['group']),hidden_threat=hidden)
                    for name,value in values.items():arrays[name].append(value)
                    row=dict(id=ident,game=r['id'],game_index=gi,ply=ply,group=g['group'],label=label,feature_sha256=key,
                        native_probability=(v['value']+1)/2,hidden_king_threat=hidden,replay_sha256=g['sha256'])
                    rows.write(json.dumps(row)+'\n');native.write(response);actions+=len(v['actions'])
                if (gi+1)%250==0:print(json.dumps({'games':gi+1,'positions':len(arrays['x']),'seconds':time.monotonic()-begin}),flush=True)
                if time.monotonic()-begin>600:raise TimeoutError('ten-minute extraction cap')
        proc.stdin.close();rc=proc.wait(timeout=10);assert rc==0,rc
        dtypes={'x':np.uint8,'half':np.uint8,'y':np.float32,'sf':np.float32,'game':np.int32,'group':np.uint8,'hidden_threat':np.bool_}
        result={k:np.asarray(v,dtype=dtypes[k]) for k,v in arrays.items()};np.savez(target/'data.npz',**result)
        receipt=dict(at=now(),status='complete',collector_exit=rc,seconds=time.monotonic()-begin,frames=frames,
            positions=len(arrays['x']),source_games=len(games),games_with_positions=len(set(arrays['game'])),
            groups=dict(Counter(map(str,arrays['group']))),prior_rows_excluded=old_rows,duplicate_skips=dict(skips),
            action_values=actions,artifacts={p.name:sha(p) for p in target.iterdir() if p.is_file()},
            scope='Frozen disjoint outcome holdout; no predictions evaluated. All trajectories validated by existing rules engine.')
        write_new(OUT/'holdout-receipt.json',receipt);print(json.dumps(receipt),flush=True)
    except BaseException as e:
        write_new(target/'failure.json',dict(at=now(),error=repr(e)));raise
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        stderr.close()


if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='extract':extract()
    else:raise ValueError(sys.argv[1])
