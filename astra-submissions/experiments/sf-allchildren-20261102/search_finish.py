"""Audit permitted inputs and source changes; report the frozen search gate."""
import hashlib
import json
from pathlib import Path
import statistics
import zipfile
from search import HERE,ROOT,OUT,DEST,sha,write,now

def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'paired-summary.json').read_text())
    review=json.loads((OUT/'independent-review.json').read_text())
    assert review['labels_match'] and review['summary_sha256']==sha(OUT/'paired-summary.json')
    assert json.loads((OUT/'terminal.json').read_text())['status']=='complete'
    rows=[json.loads(s) for s in (OUT/'paired-results.jsonl').read_text().splitlines()]
    assert len(rows)==len(plan['cases'])==51
    pairs=0
    for i,(row,c) in enumerate(zip(rows,plan['cases'])):
        assert row['case']==c;rp=Path(c['replay_path']);assert sha(rp)==c['replay_sha256']
        replay=json.loads(rp.read_text());side=('white','black').index(c['side']);tc=replay.get('timeControl',{})
        expected=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"];forced=[]
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
            assert len(recs)==2
            for k in ('samples','avoid_moves','belief_count','search_budget_seconds'):assert recs[0][k]==recs[1][k]
            assert [a['uci'] for a in recs[0]['actions']]==[a['uci'] for a in recs[1]['actions']]
            assert all(r['search_budget_seconds']==2.5 for r in recs);pairs+=1
    verified=0
    with zipfile.ZipFile(ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip') as z:
        for name in z.namelist():
            if not name.startswith('src/') or name.endswith('/'):continue
            expected=z.read(name).decode()
            if name=='src/main.c':
                expected=expected.replace('#include "gtcfr.h"','#include "gtcfr.h"\nint astra_solver_pair(const Belief *, const GtcfrParams *, SearchResult *);')
                expected=expected.replace('gtcfr_decide(&b, &gp, &r)','astra_solver_pair(&b, &gp, &r)')
            elif name=='src/gtcfr.c':
                expected=expected.replace('#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"')
                anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
                expected=expected.replace(anchor,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor)
            assert (DEST/name).read_text()==expected,name;verified+=1
    ratios=[r['arms']['on']['nodes']/r['arms']['off']['nodes'] for r in rows if r['exercised']]
    g=plan['gate'];t=summary['totals']
    checks=dict(exercised=pairs>=g['min_exercised_pairs'],fatal=t['on']['fatal']<=t['off']['fatal']+g['max_additional_fatal'],
                material=t['on']['material_ge2']<=t['off']['material_ge2']+g['max_additional_material_ge2'],
                throughput=statistics.median(ratios)>=g['min_median_node_ratio'])
    assert checks==summary['checks'] and summary['gate_pass']==all(checks.values())
    write(OUT/'input-source-review.json',dict(at=now(),actor_inputs=51,exercised_pairs=pairs,source_files=verified,
          changes='Only diagnostic wrapper and output dump in copied native sources; candidate changes external scorer.',
          fresh_scorer_workers_per_arm=True,checks=checks,passed=True,summary_sha256=sha(OUT/'paired-summary.json')))
    lines=['# Equal-clock native decision screen: all-child Stockfish','',
           f"Frozen gate: **{'PASS' if summary['gate_pass'] else 'FAIL'}**. Median node ratio **{summary['median_node_ratio']:.3f}x** at 2.5 seconds per arm.",'',
           '| Diagnostic | Original v37 scorer | All-child scorer |','|---|---:|---:|']
    for k,label in [('fatal','Immediate king loss'),('material_ge2','Two-point material loss in bounded exchange probe'),('queen_ge4','Four-point queen loss in probe')]:lines.append(f"| {label} | {t['off'][k]} | {t['on'][k]} |")
    lines+=['',f"{pairs}/51 pairs exercised. {sum(r['arms']['off']['move']!=r['arms']['on']['move'] for r in rows)} choices changed. "
            f"By-first-arm median node ratios: {json.dumps(summary['node_ratio_by_order'])} (0 baseline first, 1 candidate first; different case subsets).",'',
            f"Collector completed all 51 first attempts in {summary['elapsed']:.1f} seconds. "
            f"Course referee agrees on every label ({review['frames']} frames, {review['transitions']} tactical transitions). "
            f"Independent audit reconstructs all 51 private input histories and checks {verified} copied source files against the exact v37 archive.",'',
            'Both calls share belief, guard exclusions, root actions and world samples. Each starts fresh Stockfish workers, so TT/history '
            'cannot transfer from the first arm to the second. Startup is excluded from each search budget. The actual scorer and its '
            'tactical approximation change; the native belief, guard, CFR and root-selection implementations do not. More nodes can '
            'reflect both cheaper evaluations and different tree choices. These are reused development cases, not Elo evidence.','',
            'A full-game pilot is conditional on this gate and the audits. No ZIP or arena promotion follows from this screen alone.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(gate_pass=summary['gate_pass'],median_node_ratio=summary['median_node_ratio'],totals=t,pairs=pairs)),flush=True)

if __name__=='__main__':main()
