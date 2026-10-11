#!/usr/bin/env python3
"""Freeze and probe the six counterfactual trap families; no strength claim.

Preparation uses paced public GETs for diagnostics and cached completed replays.
The search receives protocol observations, never the oracle structural labels.
Run with the fow-starter Python so the independent replay referee is available.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from monitor_arena import Client


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(args):
    args.out.mkdir(parents=True, exist_ok=False)
    for name in ('positions.json', 'positives.json', 'labels.jsonl'):
        shutil.copyfile(args.corpus/name, args.out/name)
    shutil.copyfile(Path(__file__), args.out/'driver.py')
    for name in ('candidate','stockfish','probe.py'):
        shutil.copy2(args.frozen/name, args.out/name)
    shutil.copytree(args.frozen/'kit', args.out/'kit')
    positives=json.loads((args.out/'positives.json').read_text())
    ids={r['position'] for r in positives if r['information_conflict_groups']}
    positions=json.loads((args.out/'positions.json').read_text())
    cases=[]
    client=Client()
    replay_dir=args.out/'replays';replay_dir.mkdir()
    for position in sorted(positions,key=lambda r:r['position']):
        if position['position'] not in ids:continue
        origin=position['origins'][0]
        game_id=origin['game']
        path=replay_dir/(game_id+'.json')
        if not path.exists():
            source=args.cache/game_id/'replay.json'
            game=json.loads(source.read_text())
            diagnostics,meta=client.get('/api/games/'+game_id+'/diagnostics')
            save(replay_dir/(game_id+'.diagnostics.json'),diagnostics)
            save(replay_dir/(game_id+'.metadata.json'),dict(**meta,source=str(source),source_sha256=digest(source)))
            game['protocol']=diagnostics['protocol']
            save(path,game)
        game=json.loads(path.read_text())
        assert game['id']==game_id
        protocol=game.get('protocol')
        if not protocol or protocol['truncated']:
            raise ValueError('Complete protocol unavailable: '+game_id)
        case=dict(position=position['position'],fen=position['fen'],**origin,
                  side_name=['white','black'][origin['side']],decision=origin['ply']//2+1,
                  replay=str(path),replay_sha256=digest(path))
        case['information_conflicts']=[r['move'] for r in positives if r['position']==position['position'] and r['information_conflict_groups']]
        case['any_conflicts']=[r['move'] for r in positives if r['position']==position['position']]
        cases.append(case)
        print(json.dumps({'prepared':case['position'],'game':game_id,'ply':origin['ply']}),flush=True)
    assert len(cases)==6 and sum(len(c['information_conflicts']) for c in cases)==29
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'cases':cases,
              'files':{str(p.relative_to(args.out)):digest(p) for p in args.out.rglob('*') if p.is_file()},
              'scope':'Counterfactual setup regression. No full-game or Elo inference.'}
    save(args.out/'manifest.json',manifest)


def run(args):
    manifest=json.loads((args.out/'manifest.json').read_text())
    for name,sha in manifest['files'].items():
        if digest(args.out/name)!=sha:raise ValueError('Changed frozen input: '+name)
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
    root=args.out/args.tag;root.mkdir(exist_ok=False)
    rows=[]
    save(root/'configuration.json',dict(seed=args.seed,seconds=args.seconds,parents=20000,samples=32,
        modes='cold,warm',iterations=100000,experimental_treatments='all disabled',
        manifest_sha256=digest(args.out/'manifest.json')))
    labels={(r['position'],r['move']):r for r in map(json.loads,(args.out/'labels.jsonl').read_text().splitlines())}
    for case in manifest['cases']:
        out=root/case['position']
        cmd=[sys.executable,str(args.out/'probe.py'),case['replay'],'--binary',str(args.out/'candidate'),
            '--out',str(out),'--kit',str(args.out/'kit'),'--side',case['side_name'],'--decision',str(case['decision']),
            '--seconds',str(args.seconds),'--iterations','100000','--seed',str(args.seed),'--parents','20000',
            '--samples','32','--audit-belief','--fast-roots','--trace-continuation',
            '--stockfish',str(args.out/'stockfish'),'--mode','both']
        with (root/(case['position']+'.log')).open('w') as log:
            result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        if result.returncode:raise RuntimeError('Probe failed; retained log for '+case['position'])
        for row in json.loads((out/'results.json').read_text())['rows']:
            profile=row['action_profiles']
            info=case['information_conflicts'];any_conflict=case['any_conflicts']
            selected=labels[(case['position'],row['chosen'])]
            summary=dict(position=case['position'],game=case['game'],ply=case['ply'],mode=row['mode'],
                chosen=row['chosen'],chosen_information_conflict=row['chosen'] in info,
                chosen_any_conflict=row['chosen'] in any_conflict,
                information_policy=sum(p['policy'] for p in profile if p['move'] in info),
                information_played=sum(p['played'] for p in profile if p['move'] in info),
                all_conflict_policy=sum(p['policy'] for p in profile if p['move'] in any_conflict),
                full_profile_sum=sum(p['policy'] for p in profile),
                true_state_roots=row['true_state_roots'],true_state_reach=row['true_state_reach'],
                chosen_fatal_share=row['chosen_fatal_share'],prefix_exact=row['prefix_exact'],
                legal=row.get('legal'),immediate_loss=row.get('immediate_loss'),
                evaluation=row.get('evaluation'),belief=row.get('belief'),
                selected_label=selected,result_path=str(out/'results.json'))
            rows.append(summary)
            save(root/'summary.json',{'rows':rows})
            print(json.dumps({k:v for k,v in summary.items() if k not in ('selected_label','belief','evaluation')}),flush=True)
    save(root/'status.json',{'complete':True,'rows':len(rows)})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['prepare','run'])
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--corpus',type=Path)
    ap.add_argument('--cache',type=Path)
    ap.add_argument('--frozen',type=Path)
    ap.add_argument('--tag',default='seed21')
    ap.add_argument('--seed',type=int,default=21)
    ap.add_argument('--seconds',type=float,default=1)
    args=ap.parse_args();args.out=args.out.resolve()
    if args.stage=='prepare':
        if not all((args.corpus,args.cache,args.frozen)):ap.error('Preparation needs corpus, cache and frozen inputs')
        prepare(args)
    else:run(args)


if __name__=='__main__':main()
