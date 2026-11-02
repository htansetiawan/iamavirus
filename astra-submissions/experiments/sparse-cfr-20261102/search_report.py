"""Post-run receipt/input audit and a plain-language summary of the frozen gate."""
from collections import defaultdict
import hashlib
import json
import statistics
from pathlib import Path
from search_common import OUT, ROOT, sha, unique, now


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    summary=json.loads((OUT/'paired-summary.json').read_text())
    review=json.loads((OUT/'independent-review.json').read_text())
    assert review['labels_match'] and review['summary_sha256']==sha(OUT/'paired-summary.json')
    assert json.loads((OUT/'terminal.json').read_text())['status']=='complete'
    rows=[json.loads(s) for s in (OUT/'paired-results.jsonl').read_text().splitlines()]
    privacy=0; buckets=defaultdict(list)
    for i,(row,c) in enumerate(zip(rows,plan['cases'])):
        assert row['case']==c
        replay=json.loads(Path(c['replay_path']).read_text())
        side=('white','black').index(c['side']);tc=replay.get('timeControl',{})
        expected=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
        forced=[]
        for ply in range(c['ply']+1):
            expected.append(replay['frames'][ply][c['side']])
            if ply%2==side:
                expected.append(str(replay['frames'][ply]['clocks'][side]))
                if ply<c['ply']:forced.append(replay['frames'][ply+1]['move'])
        feed='\n'.join(expected)+'\n';stem=f"{i:02d}-{c['game']}-{c['ply']}"
        assert (OUT/'paired-logs'/(stem+'.input')).read_text()==feed
        assert hashlib.sha256(feed.encode()).hexdigest()==row['actor_protocol_sha256']
        assert forced==row['prefix_forced']
        if row['exercised']:
            recs=[json.loads(s) for s in (OUT/'paired-logs'/(stem+'.targets.jsonl')).read_text().splitlines()]
            assert len(recs)==2 and recs[0]['samples']==recs[1]['samples']
            assert recs[0]['avoid_moves']==recs[1]['avoid_moves']
            assert [a['uci'] for a in recs[0]['actions']]==[a['uci'] for a in recs[1]['actions']]
            assert all(r['search_budget_seconds']==2.5 for r in recs)
        privacy+=1;buckets[c['opponent']].append(row)
    assert privacy==len(plan['cases'])==51
    unique(OUT/'input-review.json',dict(at=now(),cases=privacy,actor_inputs_match=True,
                                      paired_worlds_and_exclusions_match=True,
                                      results_sha256=sha(OUT/'paired-results.jsonl')))
    totals=summary['totals']
    lines=['# Equal-clock search: selective CFR', '',
           f"Declared gate: **{'PASS' if summary['gate_pass'] else 'FAIL'}**. "
           f"Median node ratio {summary['median_node_ratio']:.3f}x at the same 2.5-second search budget.", '',
           '| Metric | Original v37 | Exact solver optimization |', '|---|---:|---:|']
    for key,label in [('fatal','Immediate king loss'),('material_ge2','Two-point material loss in limited exchange probe'),('queen_ge4','Four-point queen loss in probe')]:
        lines.append(f"| {label} | {totals['off'][key]} | {totals['on'][key]} |")
    lines+=['', '| Opponent cohort | Decisions | Median nodes ratio | Fatal baseline / candidate |', '|---|---:|---:|---:|']
    for name,group in sorted(buckets.items()):
        ratios=[r['arms']['on']['nodes']/r['arms']['off']['nodes'] for r in group if r['exercised']]
        lines.append(f"| {name} | {len(group)} | {statistics.median(ratios):.3f}x | "
                     f"{sum(r['arms']['off']['fatal'] for r in group)} / {sum(r['arms']['on']['fatal'] for r in group)} |")
    lines+=['', f"All {privacy} protocol histories independently reconstructed from own observations, own moves and clocks. "
             'World samples, root actions and guard exclusions match between arms. Course-referee review agrees with every tactical label.', '',
             'The cases are the same development supplement used by earlier experiments, not fresh held-out games. '
             'No posterior, guard, expansion rule, root selector or leaf model changes. Different search trees and moves '
             'can arise from timing, extra work and asynchronous Stockfish responses. Shared Stockfish state introduces '
             'order effects; first arm alternates by case. This result is not an Elo estimate.', '',
             f"Median node ratios by first arm: {json.dumps(summary['node_ratio_by_order'],sort_keys=True)} "
             '(0 = baseline first; 1 = candidate first).', '',
             'Full games are conditional on the frozen diagnostic gate; this report does not authorize promotion.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(input_cases=privacy,gate_pass=summary['gate_pass'],median_node_ratio=summary['median_node_ratio'])))


if __name__=='__main__':main()
