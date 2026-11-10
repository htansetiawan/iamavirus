"""Read raw zero-ply receipts and independently classify each startup."""
from collections import Counter,defaultdict
import json
from pathlib import Path
from statistics import median

from probe import OUT, PLAN, directory, load, now, referee, save, sha
from test_trace import trace_rows

def main():
    plan=load();state=json.loads((OUT/'execution.json').read_text())
    assert state['status']=='observed' and state['worker_exits']==16 and state['cleanup_verified']
    assert state['plan_sha256']==sha(PLAN)
    ref=referee();initial=ref.make_frame(ref.FowBoard(),[180.,180.]);rows=[]
    assert {p.name for p in Path(plan['store']).iterdir()}=={j['id'] for j in plan['jobs']}
    for job in plan['jobs']:
        path=directory(plan,job);terminal=json.loads((path/'terminal.json').read_text())
        begin=json.loads((path/'started.json').read_text())
        assert terminal['job']==begin['job']==job and begin['plan_sha256']==sha(PLAN)
        assert terminal['code']==0 and not terminal['timed_out'] and not terminal['cleanup_unverified']
        raw=path/'startup.json';game=json.loads(raw.read_text())
        assert game['id']==job['id'] and game['frames']==[initial]
        assert game['timeControl']==dict(baseSeconds=180,incrementSeconds=2)
        assert not game['warnings'] and not game['protocol']['truncated']
        if not game.get('failedSide'):
            assert game['reason']=='Move limit reached' and game['result']=='1/2-1/2'
        events=game['protocol']['events'];assert all(e['ply']==0 for e in events)
        assert not any(e['text'].startswith('move ') for e in events)
        assert [e['atMs'] for e in events]==sorted(e['atMs'] for e in events)
        controls=game['localTurnControl']['controls'];assert 1<=len(controls)<=2
        for side in ('white','black'):
            selected=[e for e in events if e['side']==side]
            text=game.get('privateDiagnostics',{}).get(side,'');trace=trace_rows(text)
            arm='diagnostic' if side==job['diagnostic_side'] else 'reference'
            phase=None;worker_index=None;duration=None;timings=[]
            if not selected:
                assert game.get('failedSide')=='white' and side=='black' and not text
                status='not_started'
            else:
                assert [(e['direction'],e['text']) for e in selected[:2]]==[
                    ('input','fow'),('input',side[0]+' 180 2')]
                ready=[e for e in selected if e['direction']=='output' and e['text']=='ready']
                assert len(ready)<=1 and (ready or game.get('failedSide')==side)
                if ready:duration=ready[0]['atMs']-selected[1]['atMs']
                ready_marker='mist: stockfish ready' in text
                fallback_marker='mist: stockfish failed to start; our evaluator scores the leaves' in text
                assert not (ready_marker and fallback_marker)
                status='stockfish_ready' if ready and ready_marker else 'fallback' if ready and fallback_marker else 'referee_startup_fault'
                if ready: assert ready_marker or fallback_marker
                if arm=='reference':assert not trace
                else:
                    for w in (0,1):
                        records=[r for r in trace if r['worker']==w]
                        assert len(records)<=72
                        ts=[r['elapsed_ms'] for r in records];assert ts==sorted(ts) and all(t>=0 for t in ts)
                        phases=[r for r in records if r['event']=='matched']
                        for r in phases:assert bytes.fromhex(r['line_hex']) in (b'uciok',b'readyok')
                        if status=='stockfish_ready':
                            assert [(r['phase'],bytes.fromhex(r['line_hex'])) for r in phases]==[('uci',b'uciok'),('ready',b'readyok')]
                            assert records[-1]['event']=='success'
                        for r in phases:
                            starts=[x['elapsed_ms'] for x in records if x['event']=='begin' and x['phase']==r['phase']]
                            assert len(starts)==1
                            timings.append(dict(worker=w,phase=r['phase'],ms=r['elapsed_ms']-starts[0]))
                    failed=[r for r in trace if r['event']=='failed' or r['event'].endswith('-failed')]
                    if status=='fallback':assert len(failed)==1
                    if failed:phase=failed[-1]['phase'];worker_index=failed[-1]['worker']
            rows.append(dict(job=job['id'],lane=job['lane'],side=side,arm=arm,status=status,
                initialization_ms=duration,failed_phase=phase,failed_worker=worker_index,
                traced_phases=timings,trace_events=len(trace),source_sha256=sha(raw)))
    totals={a:dict(Counter(r['status'] for r in rows if r['arm']==a)) for a in ('reference','diagnostic')}
    grouped=defaultdict(list)
    for row in rows:
        if row['initialization_ms'] is not None:grouped[row['arm']].append(row['initialization_ms'])
    stats={a:dict(n=len(xs),min=min(xs),median=median(xs),max=max(xs)) for a,xs in grouped.items()}
    result=dict(at=now(),complete=True,pins=len(plan['dependencies']),attempts=16,bot_slots=32,plies=0,
        totals=totals,protocol_initialization_ms=stats,cleanup_verified=True,rows=rows,
        reproduced_stockfish_fallback=any(r['status']=='fallback' for r in rows),
        strength_evidence=False,scope='A small startup-only diagnostic; no full pilot load, cold-cache guarantee, root-cause claim for the historic failure, or playing result.')
    save(OUT/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)

if __name__=='__main__':main()
