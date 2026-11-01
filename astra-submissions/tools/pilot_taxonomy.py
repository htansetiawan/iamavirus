#!/usr/bin/env python3
"""Describe all completed planned games; never tune or advance a playing gate."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from learning import move_taxonomy

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--phase',choices=['h2h','misty'],default='h2h');args=ap.parse_args()
    directory=args.directory.resolve();plan=json.loads((directory/'plan.json').read_text())
    jobs=[j for j in plan['jobs'] if j['phase']==args.phase]
    games=[];groups=defaultdict(Counter);pending=[];faults=[];evidence={}
    for job in jobs:
        folder=directory/'jobs'/job['id'];result_path=folder/'result.json'
        if not result_path.exists():pending.append(job['id']);continue
        result=json.loads(result_path.read_text());assert result['job']==job
        if result['faults']:
            faults.append(dict(job=job['id'],faults=result['faults']));continue
        path=folder/'replay.json';assert sha(path)==result['replay_sha256']
        replay=json.loads(path.read_text());assert replay['result']==result['result']
        assert len(replay['frames'])==result['validated_frames']
        labelled=move_taxonomy.label_game(replay)
        expected=[job['arm'],job['opponent']] if job['side']=='white' else [job['opponent'],job['arm']]
        assert [replay['white'],replay['black']]==expected
        for side,name in enumerate(['white','black']):
            actor=expected[side];opponent=expected[1-side];key=(actor,name,opponent)
            c=labelled['counts'][name];g=groups[key];g.update(c);g['games']+=1
            g['wins']+=int(replay['result']==('1-0' if side==0 else '0-1'));g['draws']+=int(replay['result']=='1/2-1/2')
        games.append(dict(job=job['id'],pair=job['pair'],candidate_side=job['side'],result=result['result'],
                          plies=result['plies'],replay_path=str(path.relative_to(ROOT)),replay_sha256=sha(path),
                          counts=labelled['counts'],moves=labelled['moves']))
        evidence[str(result_path.relative_to(ROOT))]=sha(result_path)
    panels=[]
    for (actor,colour,opponent),c in sorted(groups.items()):
        assert c['moves']>0
        panels.append(dict(actor=actor,colour=colour,opponent=opponent,games=c['games'],moves=c['moves'],
                           wins=c['wins'],draws=c['draws'],losses=c['games']-c['wins']-c['draws'],
                           counts={k:c[k] for k in move_taxonomy.KEYS},
                           per_100_moves={k:100*c[k]/c['moves'] for k in move_taxonomy.KEYS}))
    result=dict(created_at=datetime.now(timezone.utc).isoformat(),phase=args.phase,planned=len(jobs),completed=len(games),pending=pending,faults=faults,
                plan_sha256=sha(directory/'plan.json'),script_sha256=sha(Path(__file__)),taxonomy_code_sha256=sha(ROOT/'learning/move_taxonomy.py'),
                evidence_sha256=evidence,panels=panels,games=games,
                scope='Descriptive offline labels for every completed valid game in the frozen phase. Incomplete runs can be colour-imbalanced. Behaviour rates are not strength, causal effects, guard calibration or automatic model updates.')
    destination=directory/f'taxonomy-{args.phase}.json';destination.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    text=[f'# Completed pilot taxonomy: {args.phase}', '',f"{len(games)} of {len(jobs)} planned games complete; {len(pending)} pending; {len(faults)} recorded faults.", '',
          'Includes every completed valid planned game, without selecting wins or losses. An incomplete run can be colour-imbalanced. Rates below are per 100 own moves; they describe behaviour and do not establish playing strength.', '',
          '| Policy | Colour | Opponent | Games | W-D-L | Moves | Hidden captures | Unseen king threats | Queen exposed unseen | King moves |',
          '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for p in panels:
        q=p['per_100_moves'];text.append(f"| {p['actor']} | {p['colour']} | {p['opponent']} | {p['games']} | {p['wins']}-{p['draws']}-{p['losses']} | {p['moves']} | {q['capture_unseen']:.2f} | {q['king_threat_unseen']:.2f} | {q['queen_exposed_unseen']:.2f} | {q['king_move']:.2f} |")
    text+=['','All 19 tags, raw numerators, move denominators, game/policy/colour mappings and per-move annotations are retained in the accompanying JSON. Queen exposure is not a net queen-loss label; some exposed pieces are sound trades. Phase and game-length differences can affect these rates.','',
           'These labels use true boards, both views and sometimes later moves. They are offline analysis only. The candidate, belief weights, guards, test cases and promotion thresholds are unchanged.','',
           'Source games:','']
    text += [f"- [{g['job']}](jobs/{g['job']}/replay.json): {g['result']}, {g['plies']} plies." for g in games]
    (directory/f'taxonomy-{args.phase}.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({'completed':len(games),'pending':len(pending),'faults':faults,'panels':panels},indent=2))

if __name__=='__main__':main()
