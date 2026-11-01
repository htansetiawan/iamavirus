#!/usr/bin/env python3
"""Reuse the checked replay runner for eight frozen queen cases; no policy edits."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/queen-screen-20261101'
PARENT=ROOT/'astra-submissions/analysis/persistent-response-20261101'
CASES=ROOT/'astra-submissions/analysis/queen-cases-20261101-evening/curated/cases.json'
RUNNER=ROOT/'astra-submissions/experiments/persistent-response-20261101/run.py'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import exchange_probe


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def save(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    data=json.loads(CASES.read_text());old=json.loads((PARENT/'plan.json').read_text())
    primary=[c for c in data['cases'] if c['cohort']=='recorded_queen_net_ge4']
    ids={c['game'] for c in primary}
    controls=[c for c in data['cases'] if c['game'] in ids and c['cohort']=='ordinary_queen_present_control']
    assert len(primary)==len(controls)==4
    cases=[];provenance={g['game']:g for g in data['games']}
    for c in sorted(primary+controls,key=lambda c:(c['game'],c['ply'])):
        feed=ROOT/c['input_path'];forced=ROOT/c['forced_path']
        assert sha(feed)==c['input_sha256'] and sha(forced)==c['forced_sha256']
        name=f"{c['game']}-{c['ply']}";(OUT/(name+'.input.txt')).write_bytes(feed.read_bytes())
        cases.append(dict(name=name,game=c['game'],ply=c['ply'],side=('white','black').index(c['side']),opponent=c['opponent'],
                          forced=json.loads(forced.read_text()),input_sha256=sha(feed),replay_sha256=provenance[c['game']]['replay_sha256'],
                          cohort=c['cohort'],played=c['played'],recorded_probe=c['played_probe']))
    plan={k:old[k] for k in ['binaries','binary_sha256','runner_sha256','readme_sha256','helper_sha256',
                            'model','model_sha256','history_sha256','stockfish_sha256','seconds','confidence','timeout_seconds']}
    plan['helper_sha256']=dict(plan['helper_sha256'])
    for name,h in old['validation_sha256'].items():plan['helper_sha256'][str(PARENT/name)]=h
    for path in [Path(__file__),CASES,ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py']:
        plan['helper_sha256'][str(path)]=sha(path)
    plan.update(created_at=datetime.now(timezone.utc).isoformat(),cases=cases,games=[provenance[g] for g in sorted(ids)],
                validation_sha256={},arms=['original','off','persistent'],cores='4,5',seed=2161101,
                selection='All four recorded >=4 net queen losses in the completed 63-game collection, plus its already-selected ordinary control in each game. No candidate choices examined before freezing.',
                truth_to_engine=False,
                scope='Supplementary eight-decision diagnostic, not a strength estimate or a replacement of experiment 214. No model, guard, search or acceptance-rule change.',
                gate='Report all 24 first-attempt calls, king and queen/material events, fixed/broken cases and off-control differences. Stop on technical failure. No tuning or promotion from this diagnostic alone.')
    save(OUT/'plan.json',plan)
    print(json.dumps({'cases':len(cases),'calls':3*len(cases),'plan_sha256':sha(OUT/'plan.json')}))


def run():
    mod=load_module('queen_screen_checked_runner',RUNNER)
    mod.OUT=OUT;mod.ARMS=['original','off','persistent']
    mod.run()


def summarize():
    plan=json.loads((OUT/'plan.json').read_text())
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    rows=[json.loads(l) for l in (OUT/'receipts.jsonl').read_text().splitlines()]
    keyed={(r['name'],r['arm']):r for r in rows}
    assert len(rows)==len(keyed)==24
    assert set(keyed)=={(c['name'],a) for c in plan['cases'] for a in plan['arms']}
    oracle=load_module('queen_screen_referee',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
    ref=oracle.ref
    from collections import Counter
    cache={};labels=[];frames_checked=checks=0
    for game in plan['games']:
        path=ROOT/game['replay_path'];assert sha(path)==game['replay_sha256']
        rp=json.loads(path.read_text());states,errors=ingest.validate_replay(rp);assert not errors
        board=ref.FowBoard();history=Counter({ref.position_key(board):1});seq=[]
        for ply,frame in enumerate(rp['frames']):
            if ply:board.push_uci(frame['move']);history[ref.position_key(board)]+=1
            rf=ref.make_frame(board,frame['clocks'])
            assert all(rf[k]==frame[k] for k in ('board','white','black'))
            seq.append((board.copy(),history.copy()));frames_checked+=1
        cache[game['game']]=(states,seq)
    for case in plan['cases']:
        states,seq=cache[case['game']]
        for arm in plan['arms']:
            row=keyed[(case['name'],arm)];assert row['protocol_valid'] and not row['error']
            probe=exchange_probe(states[case['ply']],row['move'])
            independent,n=oracle.probe(*seq[case['ply']],row['move'],case['side']);checks+=n
            for field in ('legal','fatal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture'):
                assert probe.get(field)==independent.get(field),(case['name'],arm,field)
            labels.append(dict(name=case['name'],cohort=case['cohort'],arm=arm,move=row['move'],**probe))
    summary=dict(cases=8,calls=24,independent_frames=frames_checked,independent_transitions=checks,arms={})
    for arm in plan['arms']:
        rr=[r for r in labels if r['arm']==arm]
        summary['arms'][arm]=dict(king_losses=sum(r['fatal'] for r in rr),queen_loss_ge4=sum((r['queen_exchange_loss'] or 0)>=4 for r in rr),
                                  material_loss_ge2=sum((r['exchange_loss'] or 0)>=2 for r in rr))
    save(OUT/'labelled.json',labels);save(OUT/'summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run','summarize')
    globals()[sys.argv[1]]()
