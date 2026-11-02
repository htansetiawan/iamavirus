"""Independent arithmetic/coverage/source audit of the frozen first attempts."""
from collections import defaultdict
import difflib
import gzip
import json
import math
from pathlib import Path
import statistics
import subprocess

import chess
from build import HERE, ROOT, OUT, sha, write

def main():
    plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
    assert receipt['state']=='completed' and len(receipt['batches'])==6
    assert receipt['plan_sha256']==sha(OUT/'plan.json')
    for p,h in plan['pins'].items():assert sha(p)==h,p
    provenance=json.loads((OUT/'provenance.json').read_text());changed=[]
    for name,h in provenance['upstream_files'].items():
        assert sha(HERE/'build/base'/name)==h,name
        if sha(HERE/'build/candidate'/name)!=h:changed.append(name)
    assert set(changed)=={'src/search.h','src/search.cpp'},changed
    patch=''
    for name in ('src/search.h','src/search.cpp'):
        a=(HERE/'build/base'/name).read_text();b=(HERE/'build/candidate'/name).read_text()
        patch+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),'a/'+name,'b/'+name))
    assert patch==(HERE/'stockfish19-allchildren.patch').read_text()
    subprocess.run(['patch','--dry-run','-p1','-d',str(HERE/'build/base'),'-i',str(HERE/'stockfish19-allchildren.patch')],check=True,capture_output=True)
    cases={c['id']:c for c in plan['cases']};results={};coverage=0;control_equal=0;artifacts={}
    for regime in plan['regimes']:
        totals=defaultdict(float);nodes=defaultdict(int);stats=defaultdict(list);batches=[];first=None
        for rep in range(plan['passes']):
            path=OUT/f'{regime}-{rep}.json';data=json.loads(path.read_text());rows=data['rows']
            assert len(rows)==len(cases)*4
            grouped=defaultdict(dict);times=defaultdict(float)
            for r in rows:
                c=cases[r['id']];assert r['arm'] not in grouped[r['id']]
                grouped[r['id']][r['arm']]=r
                legal={m.uci() for m in chess.Board(c['fen']).legal_moves}
                assert set(r['scores'])==legal==set(c['legal']) and r['best'] in legal
                assert r['seconds']>0 and r['nodes']>0
                coverage+=len(legal);totals[r['arm']]+=r['seconds'];times[r['arm']]+=r['seconds'];nodes[r['arm']]+=r['nodes']
                for s in r['scores'].values():assert abs(s['value']-math.tanh(s['cp']/400))<1e-15
            assert set(grouped)==set(cases)
            signature={ident:{a:{k:r[k] for k in ('scores','nodes','best')} for a,r in arms.items()} for ident,arms in grouped.items()}
            if first is None:first=signature
            else:assert signature==first,'repeat nondeterminism'
            for ident,arms in grouped.items():
                assert set(arms)==set(plan['arms'])
                for a in ('shipped','off'):
                    assert all(arms[a][k]==arms['base'][k] for k in ('scores','nodes','best'));control_equal+=1
                ref=arms['shipped'];candidate=arms['on'];rs=ref['scores'];cs=candidate['scores']
                mae=statistics.mean(abs(rs[m]['value']-cs[m]['value']) for m in rs)
                regret=max(s['value'] for s in rs.values())-rs[candidate['best']]['value']
                mate_diff=sum((s['kind']=='mate')!=(cs[m]['kind']=='mate') or
                              (s['kind']=='mate' and cs[m]['kind']=='mate' and (s['raw']>0)!=(cs[m]['raw']>0))
                              for m,s in rs.items())
                stats[ident].append(dict(mae=mae,regret=regret,large=regret>.5,
                         choice_agrees=ref['best']==candidate['best'],mate_disagreements=mate_diff,
                         ref_nodes=ref['nodes'],candidate_nodes=candidate['nodes'],
                         ref_move=ref['best'],candidate_move=candidate['best']))
            batches.append(dict(rep=rep,query_seconds=dict(times),speedup_base=times['base']/times['on'],
                                speedup_shipped=times['shipped']/times['on']))
            # Compress original bytes without discarding original first-attempt files.
            compressed=OUT/(path.name+'.gz')
            with compressed.open('xb') as f:
                with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z:z.write(path.read_bytes())
            with gzip.open(compressed,'rb') as f:assert f.read()==path.read_bytes()
            artifacts[path.name]=dict(raw_sha256=sha(path),gzip_sha256=sha(compressed))
        # Exactly two parents per game and three identical repeats; still compute
        # the game-weighted statistic explicitly, rather than move-weighting.
        games=defaultdict(list);parents=[]
        for ident,items in stats.items():
            row=dict(id=ident,game=cases[ident]['game'],**items[0]);parents.append(row)
            games[row['game']].append(row)
        assert len(games)==plan.get('groups',128)
        assert all(len(g)==plan.get('parents_per_group',2) for g in games.values())
        aggregate={k:statistics.mean(statistics.mean(x[k] for x in g) for g in games.values()) for k in ('mae','regret','large','choice_agrees')}
        aggregate.update(mate_disagreements=sum(p['mate_disagreements'] for p in parents),
                         speedup_base=totals['base']/totals['on'],speedup_shipped=totals['shipped']/totals['on'])
        g=plan['gates'];checks=dict(mae=aggregate['mae']<=g['mae'],regret=aggregate['regret']<=g['regret'],
                    large_regret=aggregate['large']<=g['large_regret_rate'],
                    speedup_base=aggregate['speedup_base']>=g['speedup_base'],
                    speedup_shipped=aggregate['speedup_shipped']>=g['speedup_shipped'])
        results[regime]=dict(aggregate=aggregate,checks=checks,query_seconds=dict(totals),nodes=dict(nodes),
                            batches=batches,parents=parents)
    summary=dict(passed=all(all(r['checks'].values()) for r in results.values()),regimes=results,
                 source_changed=changed,scored_moves_checked=coverage,control_parent_pairs_equal=control_equal,
                 repeat_outputs_identical=True,artifact_hashes=artifacts,receipt_sha256=sha(OUT/'receipt.json'),
                 plan_sha256=sha(OUT/'plan.json'),limitations=[plan['scope'],
                   'Stockfish reference scores are not FoW truth','query wall includes UCI transport',
                   'worker CPU in cold batches includes TT reset costs','no games or Elo estimate'])
    write(OUT/'review.json',summary)
    print(json.dumps(dict(passed=summary['passed'],regimes={k:v['aggregate'] for k,v in results.items()},
                         moves=coverage,controls=control_equal)),flush=True)

if __name__=='__main__':main()
