#!/usr/bin/env python3
"""Curate structural opening labels from a pre-existing held-out game split.

The rules tracker consumes observation histories, not truth, to establish
singleton support. Oracle boards validate that support and supply offline
counterfactual labels only afterward. No runtime policy or strength claim.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser()
    for name in ['manifest','tracker','labeler','kit','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--split',default='validation',choices=['train','validation','test'])
    args=ap.parse_args();args.out.mkdir(exist_ok=False)
    sys.path.insert(0,str(args.kit));import referee,chess
    from m4_information_dilemma import analyze
    sources=json.loads(args.manifest.read_text())['games'][args.split]
    frozen=[];replays={};start=time.perf_counter()
    for name in ['tracker','labeler']:
        shutil.copyfile(getattr(args,name),args.out/name);(args.out/name).chmod(0o755)
    shutil.copyfile(__file__,args.out/'curator.py')
    shutil.copyfile(referee.__file__,args.out/'referee.py')
    shutil.copyfile(Path(__file__).with_name('m4_information_dilemma.py'),args.out/'forensic-labeler.py')
    with (args.out/'tracker-input.txt').open('w') as target:
        for item in sorted(sources,key=lambda r:r['id']):
            path=Path(item['source']);assert sha(path)==item['sha256']
            replay=json.loads(path.read_text());assert replay['rulesVersion']=='fow-v1'
            replays[replay['id']]=replay
            for side in [0,1]:
                target.write(f"game {replay['id']} {side}\n")
                for f in replay['frames'][1:14]:
                    target.write(' '.join([f['move'],f['board'],f['white'],f['black']])+'\n')
            frozen.append({k:replay.get(k) for k in ['id','white','black','createdAt','result']}|
                          dict(source_sha256=item['sha256'],prefix_plies=min(13,len(replay['frames'])-1)))
    # We disable the prior entirely. Its text file is only the frozen runner's
    # required interface; no move_logits call should occur.
    (args.out/'unused-model.txt').write_text('26\n'+' '.join(['0']*26)+'\n')
    manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),games=frozen,
        selection=f'All {args.split} games from the pre-existing SHA256 game-ID split, both seats, first 13 plies; no result filter.',
        criterion='2<=decision ply<=12; worlds=1, no overflow, no collapse or rebuild, truth supported, all views consistent',
        manifest_source_sha256=sha(args.manifest),tracker_sha256=sha(args.out/'tracker'),labeler_sha256=sha(args.out/'labeler'),
        referee_sha256=sha(Path(referee.__file__)),python_chess_version=chess.__version__,curator_sha256=sha(Path(__file__)),
        classification='Offline corpus discovery and rules validation; no train/validation strength estimate or Elo inference.')
    write(args.out/'manifest.json',manifest)
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_'))}
    env.update(MIST_MODEL='0',MIST_PRUNE_CAPTURABLE='1',MIST_M4_CAP_MODE='0')
    begin=time.perf_counter()
    with (args.out/'tracker-rows.jsonl').open('w') as out,(args.out/'tracker.stderr').open('w') as err:
        run=subprocess.run([str(args.out/'tracker'),str(args.out/'tracker-input.txt'),str(args.out/'unused-model.txt'),'10000','41'],stdout=out,stderr=err,env=env,timeout=900)
    write(args.out/'tracker-status.json',dict(returncode=run.returncode,elapsed_seconds=time.perf_counter()-begin))
    if run.returncode:raise RuntimeError('Tracker failed; preserve partial output, do not label it.')
    states={};eligible=0;total=0
    for row in map(json.loads,(args.out/'tracker-rows.jsonl').read_text().splitlines()):
        total+=1
        assert not row['inconsistent'] and not row['full_calls'] and not row['cheap_calls']
        if not (2<=row['ply']<=12 and row['worlds']==1 and row['truth_present'] and
                not row['overflowed'] and not row['collapses'] and not row['rebuilds']):continue
        eligible+=1;g=replays[row['game']];b=referee.FowBoard()
        for f in g['frames'][1:row['ply']+1]:b.push_uci(f['move'])
        encoded=''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
        assert encoded==g['frames'][row['ply']]['board'] and int(not b.turn)==row['side']
        key=(encoded,int(b.turn),int(b.clean_castling_rights()),b.ep_square,b.halfmove_clock)
        identifier=hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        if identifier not in states:states[identifier]=dict(board=b,origins=[])
        states[identifier]['origins'].append(dict(game=g['id'],ply=row['ply'],side=row['side'],move=row['move']))
    with (args.out/'label-input.txt').open('w') as out:
        for identifier,s in sorted(states.items()):
            b=s['board'];text=''.join(b.piece_at(q).symbol() if b.piece_at(q) else '-' for q in range(64))
            out.write(f'{identifier} {int(not b.turn)} {int(b.clean_castling_rights()):x} {b.ep_square if b.ep_square is not None else -1} {b.halfmove_clock} {text}\n')
    begin=time.perf_counter()
    with (args.out/'labels.jsonl').open('w') as out,(args.out/'labels.stderr').open('w') as err,(args.out/'label-input.txt').open() as inp:
        run=subprocess.run([str(args.out/'labeler')],stdin=inp,stdout=out,stderr=err,timeout=300)
    write(args.out/'label-status.json',dict(returncode=run.returncode,elapsed_seconds=time.perf_counter()-begin))
    if run.returncode:raise RuntimeError('Native labels failed')
    counts=Counter();positive=[];actions=Counter();seen=set()
    for row in map(json.loads,(args.out/'labels.jsonl').read_text().splitlines()):
        identifier=row['position'];b=states[identifier]['board'];m=chess.Move.from_uci(row['move'])
        key=(identifier,row['move']);assert key not in seen;seen.add(key)
        assert m in referee.fow_moves(b)
        counts['actions']+=1;actions[identifier]+=1
        if 'immediate_outcome' in row:counts['immediate_terminals']+=1;continue
        if not row['groups_with_no_universal_survival']:continue
        # Every native positive is independently regenerated, exposing whether
        # the conflict is information-only or a physically forced loss.
        check=analyze(b,m,referee,chess)
        for field in ['opponent_legal_replies','continuing_replies','observation_groups','groups_with_no_universal_survival','uniform_reply_min_risk']:
            assert row[field]==check[field],(identifier,field)
        groups=[g for g in check['groups'] if g['minimum_fatal_worlds']]
        info=[g for g in groups if all(g['safe_by_reply'][r] for r in g['replies'])]
        counts['positive_setup_actions']+=1;counts['information_conflict_actions']+=bool(info)
        proof=dict(position=identifier,fen=b.fen(),origins=states[identifier]['origins'],analysis=check)
        dest=args.out/f'{identifier}-{row["move"]}.json.gz'
        dest.write_bytes(gzip.compress(json.dumps(proof).encode(),mtime=0))
        positive.append(dict(position=identifier,fen=b.fen(),move=row['move'],groups=len(groups),
                             information_conflict_groups=len(info),exact_half_loss_proofs=sum('one_response_minimax_proof' in g for g in groups),
                             historical_times_played=sum(o['move']==row['move'] for o in states[identifier]['origins']),sha256=sha(dest)))
    for identifier,s in states.items():assert actions[identifier]==len(referee.fow_moves(s['board']))
    write(args.out/'positions.json',[dict(position=k,fen=v['board'].fen(),origins=v['origins']) for k,v in sorted(states.items())])
    write(args.out/'positives.json',positive)
    report=dict(games=len(frozen),decisions=total,eligible_singleton_decisions=eligible,unique_positions=len(states),
                **counts,elapsed_seconds=time.perf_counter()-start,positive_positions=len({p['position'] for p in positive}),
                caveat='Counterfactual immediate-response labels, not observed trap win rates. Full truth is used only after singleton validation; repetitions not modeled.')
    write(args.out/'complete.json',report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
