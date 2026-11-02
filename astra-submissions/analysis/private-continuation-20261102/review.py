"""Independent replay, delivered-input, clock and label review after the pilot."""
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from learning import ingest


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    assert summary['passed'] and summary['attempted']==2
    for path,h in plan['deps'].items():assert sha(path)==h,path
    rows=[];labels=[]
    for case in plan['cases']:
        directory=OUT/case['id'];game=json.loads((directory/'replay.json').read_text())
        receipt=json.loads((directory/'result.json').read_text());p=json.loads((ROOT/case['prefix']).read_text())
        assert sha(directory/'replay.json')==receipt['replay_sha256']
        states,problems=ingest.validate_replay(game);assert not problems
        b=case['branch_ply'];frames=game['frames'];steps=game['continuation']['steps'];inc=game['timeControl']['incrementSeconds']
        assert len(steps)==len(frames)-1
        for ply,(step,before,after) in enumerate(zip(steps,frames,frames[1:])):
            side=ply%2
            assert step['ply']==ply and step['side']==side and step['move']==after['move']
            assert abs(step['reported_clock']-before['clocks'][side])<2e-6
            assert abs(after['clocks'][1-side]-before['clocks'][1-side])<2e-6
            if ply>=b:
                assert abs(after['clocks'][side]-(before['clocks'][side]-step['actual_elapsed']+inc))<2e-6
            else:assert after['clocks']==p['frames'][ply+1]['clocks']
        delivered=0;prompts=0
        for side,key in enumerate(('white','black')):
            events=[e for e in game['protocol']['events'] if e['side']==key and e['direction']=='input']
            views=[e for e in events if len(e['text'])==64]
            last=max(s['ply'] for s in steps if s['side']==side)
            assert [e['ply'] for e in views]==list(range(last+1))
            for e in views:assert e['text']==frames[e['ply']][key]
            clock_events=[e for e in events if len(e['text'])!=64 and e['text']!='fow' and not e['text'].startswith(('w ','b '))]
            assert [e['ply'] for e in clock_events]==list(range(side,last+1,2))
            for e in clock_events:assert abs(float(e['text'])-frames[e['ply']]['clocks'][side])<2e-6
            delivered+=len(views);prompts+=len(clock_events)
        assert not game['protocol']['truncated'] and not game.get('failedSide') and not game.get('warnings')
        terminal=states[-1].outcome()
        if game['censored']:assert terminal is None and game['result']=='*'
        else:assert terminal==(game['result'],game['reason'])
        # Use references into a single immutable trajectory, not quadratic
        # copies of full observation histories at every decision.
        white_score=None if game['censored'] else {'1-0':1.,'0-1':0.,'1/2-1/2':.5}[game['result']]
        for ply in range(b,len(frames)-1):
            side=ply%2
            labels.append(dict(episode=case['id'],source_game=case['game'],branch_ply=b,ply=ply,
                actor=('white','black')[side],observation_prefix_last_ply=ply,
                permitted_input='actor observation at frames 0..ply, earlier own actions, own clocks; no board/opponent view/future move',
                replay_sha256=receipt['replay_sha256'],action=frames[ply+1]['move'],
                outcome=None if white_score is None else white_score if side==0 else 1-white_score,
                censored=game['censored'],policy='reconstructed-v37-v37-max1s',split='feasibility_only_no_model_confirmation'))
        rows.append(dict(case=case['id'],cxx_rules_frames=len(states),delivered_observations=delivered,
            clock_prompts=prompts,checked_clock_transitions=len(steps),natural_outcome=terminal,
            censored=game['censored'],new_decisions=len(frames)-1-b))
    with gzip.open(OUT/'label-index.jsonl.gz','wt') as f:
        for row in labels:f.write(json.dumps(row)+'\n')
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=rows,
        labelled_decisions=sum(r['outcome'] is not None for r in labels),censored_decisions=sum(r['outcome'] is None for r in labels),
        summary_sha256=sha(OUT/'summary.json'),labels_sha256=sha(OUT/'label-index.jsonl.gz'),
        source_sha256=sha(__file__),rules_source_sha256=sha(ROOT/'learning/ingest.py'),
        scope='Independent C++ rules validation, complete delivered observation sequences, all clocks and terminal/censor labels. Linear-size history references. Feasibility only; correlated decisions are not independent labels or strength samples.')
    with (OUT/'review.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main()
