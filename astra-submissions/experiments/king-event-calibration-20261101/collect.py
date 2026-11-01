#!/usr/bin/env python3
"""Freeze outcome-blind chronological games, then collect all root risks.

The engine receives only own observations, clocks, and forced own actions.
Truth labels are joined after the process exits. Collection is diagnostic;
wall-clock belief thinning still depends on runtime load.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from learning import ingest

OPPONENTS=['Instructors','duck','HYPOTHERMIA','Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Crimson Fog','Mist Opportunities']
SPLITS={'train':('2026-10-25','2026-10-29',80),
        'validation':('2026-10-29','2026-10-30',20),
        'test':('2026-10-30','2026-11-01',40)}


def sha(data):return hashlib.sha256(data).hexdigest()


def full_protocol(replay,side):
    tc=replay.get('timeControl',{})
    key=('white','black')[side]
    plies=[p for p in range(len(replay['frames'])-1) if p%2==side]
    feed=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
    forced=[]
    if not plies:return '\n'.join(feed)+'\n',forced,plies
    for p in range(plies[-1]+1):
        frame=replay['frames'][p];feed.append(frame[key])
        if p%2==side:
            feed.append(str(frame['clocks'][side]));forced.append(replay['frames'][p+1]['move'])
    return '\n'.join(feed)+'\n',forced,plies


def freeze(out):
    accepted=(ROOT/'data/raw/accepted.jsonl').read_bytes()
    listings={r['id']:r for r in map(json.loads,accepted.splitlines())}
    eligible=[];undated=0
    for row in listings.values():
        date=row.get('createdAt')
        if not isinstance(date,str) or not date:
            undated+=1;continue
        if not '2026-10-25'<=date<'2026-11-01':continue
        side=next((s for s in ('white','black') if row.get(s)=='IAmAVirus' and row.get(s+'Version')==35),None)
        if side is None:continue
        opponent=row['black' if side=='white' else 'white']
        if opponent not in OPPONENTS:continue
        eligible.append((date,row['id'],side,opponent))
    groups=set();by_split={k:[] for k in SPLITS};duplicates=0;missing=[]
    # Deduplicate BEFORE sampling or splitting, earliest representative only.
    for date,gid,side,opponent in sorted(eligible):
        path=ROOT/f'data/raw/games/{gid}/replay.json'
        try:payload=path.read_bytes();rp=json.loads(payload)
        except (OSError,ValueError):missing.append(gid);continue
        signature=sha(' '.join(str(f.get('move')) for f in rp['frames'][1:]).encode())
        if signature in groups:duplicates+=1;continue
        groups.add(signature)
        split=next(k for k,(start,end,n) in SPLITS.items() if start<=date<end)
        by_split[split].append({'game':gid,'side':side,'opponent':opponent,'createdAt':date,
                               'replay_path':str(path),'replay_sha256':sha(payload),'sequence_sha256':signature,'split':split})
    selected=[]
    for split,(start,end,count) in SPLITS.items():
        group=sorted(by_split[split],key=lambda r:sha(('king-calibration-1101:'+r['game']).encode()))
        if len(group)<count:raise ValueError(f'{split} only {len(group)} unique games, need {count}')
        selected.extend(sorted(group[:count],key=lambda r:(r['createdAt'],r['game'])))
    plan={'createdAt':datetime.now(timezone.utc).isoformat(),'archive_sha256':sha(accepted),
          'selection':'deterministic hash sample, no use of outcomes or labels; full-sequence duplicates assigned only to earliest game',
          'splits':SPLITS,'opponents':OPPONENTS,'eligible_unique':{k:len(v) for k,v in by_split.items()},
          'duplicates_excluded':duplicates,'missing_replays':missing,'undated_index_rows':undated,'games':selected,
          'inference':'own observations/clocks/forced own moves; never truth, opponent moves or opponent observations',
          'fit_plan':'Fit a nonnegative-slope two-parameter logistic calibrator of sharp risk on TRAIN, weighting each decision equally. Compare with raw sharp and flattened risk on VALIDATION; inspect TEST once after choice. Report played-move scores separately and game-cluster uncertainty. No automatic deployment.',
          'limits':'Historical games, capped/strided/time-sensitive belief, selected opponent population. Candidate-action labels are correlated and do not establish Elo.'}
    out.mkdir(parents=True,exist_ok=False)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print({k:len([g for g in selected if g['split']==k]) for k in SPLITS},flush=True)


def collect(out,limit):
    plan=json.loads((out/'plan.json').read_text())
    provenance=json.loads((HERE/'build-provenance.json').read_text())
    assert sha((HERE/'build/mist').read_bytes())==provenance['binary_sha256']
    record={'startedAt':datetime.now(timezone.utc).isoformat(),'provenance':provenance,
            'plan_sha256':sha((out/'plan.json').read_bytes()),'limit':limit,'pid':os.getpid(),
            'collector_script_sha256':sha(Path(__file__).read_bytes()),
            'label_sources':{p:sha((ROOT/p).read_bytes()) for p in ('learning/ingest.py','learning/rules.py')},
            'env':{'MIST_MAX_SECONDS':'10','FOW_SEED':'11012026','ASTRA_KING_CALIB':'1'},'state':'running','completed':[],'failures':[]}
    receipt=out/('receipt-pilot.json' if limit else 'receipt.json')
    if receipt.exists():raise ValueError('receipt exists; refuse implicit restart')
    receipt.write_text(json.dumps(record,indent=2)+'\n');(out/'games').mkdir(exist_ok=True)
    targets=plan['games'][:limit] if limit else plan['games']
    for game in targets:
        dest=out/'games'/f"{game['game']}.jsonl"
        if dest.exists():
            # A pilot is reused only with exact source/model/plan provenance.
            saved=json.loads(dest.with_suffix('.meta.json').read_text())
            assert saved['provenance']==provenance and saved['game']==game
            record['completed'].append(game['game']);continue
        payload=Path(game['replay_path']).read_bytes();assert sha(payload)==game['replay_sha256']
        replay=json.loads(payload);states,errors=ingest.validate_replay(replay)
        if errors:raise ValueError((game['game'],errors))
        side=('white','black').index(game['side']);feed,forced,plies=full_protocol(replay,side)
        env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
        env.update(record['env'],MIST_FORCE_MOVES=','.join(forced),MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'))
        start=time.monotonic()
        proc=subprocess.Popen(['taskset','-c','0,1',str(HERE/'build/mist')],env=env,text=True,
                              stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:stdout,stderr=proc.communicate(feed,timeout=600)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise
        (out/'games'/f"{game['game']}.stderr").write_text(stderr)
        moves=[s[5:].strip() for s in stdout.splitlines() if s.startswith('move ')]
        if proc.returncode or moves!=forced:raise ValueError(f"forced replay failed {game['game']}: exit{proc.returncode} moves{len(moves)}/{len(forced)}")
        rows=[];seen=set();counts=Counter()
        legal_by_ply={p:set(states[p].board.legal_moves()) for p in plies}
        for line in stderr.splitlines():
            if not line.startswith('astra_king '):continue
            _,d,move,flat,sharp,uniform,invalid,worlds,scanned,capped=line.split()
            d=int(d);assert 0<=d<len(plies);ply=plies[d];state=states[ply]
            key=(ply,move);assert key not in seen;seen.add(key);counts[ply]+=1
            if move not in legal_by_ply[ply]:raise ValueError(f"view action illegal on truth: {game['game']} {ply} {move}")
            child=state.copy();child.push(move);outcome=child.outcome()
            lost=bool(outcome and outcome[0]==('0-1','1-0')[side])
            rows.append({'game':game['game'],'split':game['split'],'ply':ply,'side':side,'opponent':game['opponent'],
                         'move':move,'played':move==forced[d],'fatal':int(lost),'flat':float(flat),'sharp':float(sharp),
                         'uniform':float(uniform),'invalid_mass':float(invalid),'worlds':int(worlds),'scanned':int(scanned),
                         'capped':bool(int(capped)),'king_move':replay['frames'][ply][game['side']][(ord(move[0])-97)+8*(int(move[1])-1)].lower()=='k'})
        assert set(counts)==set(plies),f'missing decisions {game["game"]}'
        for row in rows:row['decision_weight']=1/counts[row['ply']]
        covered={r['ply'] for r in rows if r['played']}
        meta={'game':game,'provenance':provenance,'elapsed':time.monotonic()-start,'decisions':len(plies),
              'candidates':len(rows),'played_covered':sum(r['played'] for r in rows),'feed_sha256':sha(feed.encode()),
              'missing_played_plies':[p for p in plies if p not in covered],
              'rebuilds':stderr.count('belief empty, rebuilt'),'clock_thinnings':stderr.count('before the update')}
        temp=dest.with_suffix('.tmp');temp.write_text(''.join(json.dumps(r)+'\n' for r in rows));temp.replace(dest)
        dest.with_suffix('.meta.json').write_text(json.dumps(meta,indent=2)+'\n')
        record['completed'].append(game['game']);receipt.write_text(json.dumps(record,indent=2)+'\n')
        print(len(record['completed']),len(targets),game['game'],len(rows),round(meta['elapsed'],2),flush=True)
    record['state']='complete';record['finishedAt']=datetime.now(timezone.utc).isoformat();receipt.write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['freeze','collect'])
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--limit',type=int,default=0)
    args=ap.parse_args()
    try:
        freeze(args.out) if args.command=='freeze' else collect(args.out,args.limit)
    except BaseException as exc:
        receipt=args.out/('receipt-pilot.json' if args.limit else 'receipt.json')
        if args.command=='collect' and receipt.exists():
            record=json.loads(receipt.read_text())
            if record.get('pid')==os.getpid():
                record.update(state='error',error=repr(exc),finishedAt=datetime.now(timezone.utc).isoformat())
                receipt.write_text(json.dumps(record,indent=2)+'\n')
        raise
