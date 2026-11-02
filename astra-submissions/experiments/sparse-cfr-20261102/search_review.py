from collections import Counter
import importlib.util
import json
from pathlib import Path
from search_common import ROOT,OUT,now,sha,unique


def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'paired-summary.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(ROOT/p)==h,p
    assert sha(OUT/'paired-results.jsonl')==summary['results_sha256']
    spec=importlib.util.spec_from_file_location('qexp_referee',ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py')
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);ref=oracle.ref
    cache={};frames=transitions=choices=0;rows=[json.loads(s) for s in (OUT/'paired-results.jsonl').read_text().splitlines()]
    assert len(rows)==len(plan['cases'])
    totals={a:Counter() for a in ('off','on')}
    for row,c in zip(rows,plan['cases']):
        assert row['case']==c;side=('white','black').index(c['side'])
        if c['game'] not in cache:
            rp=json.loads(Path(c['replay_path']).read_text());assert sha(Path(c['replay_path']))==c['replay_sha256']
            b=ref.FowBoard();history=Counter({ref.position_key(b):1});seq=[]
            for i,f in enumerate(rp['frames']):
                if i:b.push_uci(f['move']);history[ref.position_key(b)]+=1
                actual=ref.make_frame(b,f['clocks']);assert all(actual[k]==f[k] for k in ('board','white','black'))
                seq.append((b.copy(),history.copy()));frames+=1
            cache[c['game']]=seq
        board,hist=cache[c['game']][c['ply']];answers={}
        for arm,r in row['arms'].items():
            if r['move'] not in answers:
                answer,n=oracle.probe(board,hist,r['move'],side);answers[r['move']]=answer;transitions+=n;choices+=1
            answer=answers[r['move']]
            for k in ('legal','fatal','terminal','exchange_loss','queen_exchange_loss','forced_king_loss_after_capture'):assert answer[k]==r[k],(c['game'],c['ply'],arm,k)
            totals[arm]['fatal']+=answer['fatal'];totals[arm]['material_ge2']+=(answer['exchange_loss'] or 0)>=2;totals[arm]['queen_ge4']+=(answer['queen_exchange_loss'] or 0)>=4
    assert {k:dict(v) for k,v in totals.items()}==summary['totals']
    import statistics
    ratios=[r['arms']['on']['nodes']/r['arms']['off']['nodes'] for r in rows if r['exercised']]
    assert statistics.median(ratios)==summary['median_node_ratio']
    unique(OUT/'independent-review.json',dict(at=now(),frames=frames,choices=choices,transitions=transitions,
        summary_sha256=sha(OUT/'paired-summary.json'),referee_sha256=sha(oracle.REFPATH),labels_match=True,scope='Independent tactical correctness; not strength.'))
    print(json.dumps(dict(frames=frames,choices=choices,transitions=transitions,labels_match=True)))


if __name__=='__main__':main()
