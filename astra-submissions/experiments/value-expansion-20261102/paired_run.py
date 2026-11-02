import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from build import HERE,ROOT,OUT
from prepare import sha,now,unique
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from learning import ingest
from fresh_taxonomy_gate import protocol,exchange_probe


def target_check(row):
    assert row['own_reach_consistent']
    assert row['root_histories']==len(row['samples'])
    assert abs(sum(w['weight'] for w in row['samples'])-1)<1e-9
    assert abs(row['cf_mass']-1)<1e-9 and abs(row['own_reach']-1)<1e-9
    assert abs(sum(a['probability'] for a in row['actions'])-1)<1e-9
    assert len({a['uci'] for a in row['actions']})==len(row['actions'])
    assert abs(sum(a['probability']*a['q'] for a in row['actions'])-row['root_value'])<1e-9
    assert abs(row['solver_value']-row['root_value'])<1e-9
    assert max(row['actions'],key=lambda a:a['probability'])['uci']==row['solver_move']
    assert all(row['root_loss_value']-1e-9 <= a['q'] <= 1+1e-9 for a in row['actions'])


def main():
    plan=json.loads((OUT/'plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']))
    for p,h in plan['dependencies'].items():assert sha(ROOT/p)==h,p
    unique(OUT/'execution.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    logs=OUT/'paired-logs';logs.mkdir(exist_ok=False);started=time.monotonic();rows=[]
    try:
        with (OUT/'paired-results.jsonl').open('x') as result_file:
            for i,c in enumerate(plan['cases']):
                remaining=plan['wall_cap']-(time.monotonic()-started);assert remaining>1,'global wall cap'
                assert sha(Path(c['replay_path']))==c['replay_sha256']
                replay=json.loads(Path(c['replay_path']).read_text());side=('white','black').index(c['side'])
                states,errors=ingest.validate_replay(replay);assert not errors,errors
                feed,forced=protocol(replay,c['ply'],side);stem=f"{i:02d}-{c['game']}-{c['ply']}";target=logs/(stem+'.targets.jsonl')
                (logs/(stem+'.input')).write_text(feed)
                env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
                env.update(MIST_FORCE_MOVES=','.join(forced),MIST_MAX_SECONDS=str(plan['prefix_max_seconds']),
                    FOW_SEED=str(plan['seed']),MIST_TEACHER_OUT=str(target),ASTRA_EXPANSION_PAIR=str(i%2))
                begin=time.monotonic();p=subprocess.Popen(['bash','run.sh'],cwd=HERE/'build/diagnostic',env=env,
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
                try:
                    stdout,stderr=p.communicate(feed,timeout=min(plan['case_wall_cap'],remaining))
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:stdout,stderr=p.communicate(timeout=3)
                    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
                    (logs/(stem+'.stdout')).write_text(stdout);(logs/(stem+'.stderr')).write_text(stderr)
                    raise RuntimeError(f'case {stem} timeout, process group stopped; no retry')
                (logs/(stem+'.stdout')).write_text(stdout);(logs/(stem+'.stderr')).write_text(stderr)
                assert p.returncode==0,(stem,p.returncode)
                assert 'mist: stockfish ready' in stderr
                moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')];assert moves[:-1]==forced and len(moves)==len(forced)+1
                records=[json.loads(line) for line in target.read_text().splitlines()] if target.exists() else []
                pair_lines=re.findall(r'astra-expansion-pair enabled=(\d) elapsed=([\d.]+) ok=(\d)',stderr)
                row=dict(case=c,elapsed=time.monotonic()-begin,actor_protocol_sha256=hashlib.sha256(feed.encode()).hexdigest(),
                    prefix_forced=forced,order=['on','off'] if i%2 else ['off','on'],exercised=bool(records),arms={})
                if not records:
                    # No search means a front-end forced move. It counts in labels,
                    # but cannot establish that the new expansion rule was tested.
                    assert not pair_lines and 'nodes=0 ' in stderr,(stem,'missing paired export')
                    for arm in ('off','on'):row['arms'][arm]=dict(move=moves[-1],**exchange_probe(states[c['ply']],moves[-1]))
                else:
                    assert len(records)==2 and len(pair_lines)==2
                    for record in records:target_check(record)
                    assert records[0]['samples']==records[1]['samples']
                    assert records[0]['avoid_moves']==records[1]['avoid_moves']
                    assert [a['uci'] for a in records[0]['actions']]==[a['uci'] for a in records[1]['actions']]
                    assert records[0]['belief_count']==records[1]['belief_count']
                    for record,(mode,elapsed,ok) in zip(records,pair_lines):
                        arm='on' if int(mode) else 'off';assert ok=='1' and record['search_budget_seconds']==plan['per_search_seconds']
                        move=record['solver_move'];row['arms'][arm]=dict(move=move,search_elapsed=float(elapsed),nodes=record['nodes'],iterations=record['iterations'],
                            **exchange_probe(states[c['ply']],move))
                    assert row['arms']['off']['move']==moves[-1],(stem,'front-end fallback differs from paired raw selector')
                    telemetry=[s for s in stderr.splitlines() if s.startswith('astra-expansion-q ')];assert len(telemetry)==1
                    stats=dict(re.findall(r'(\w+)=([\d.]+)',telemetry[0]));assert int(stats['recall_failures'])==0
                    row['q_stats']=stats
                assert all(a['legal'] for a in row['arms'].values()),(stem,'illegal candidate')
                rows.append(row);result_file.write(json.dumps(row)+'\n');result_file.flush()
                print(json.dumps(dict(done=len(rows),total=len(plan['cases']),game=c['game'],ply=c['ply'],exercised=row['exercised'],moves={k:v['move'] for k,v in row['arms'].items()})),flush=True)
        totals={arm:dict(fatal=sum(r['arms'][arm]['fatal'] for r in rows),material_ge2=sum((r['arms'][arm]['exchange_loss'] or 0)>=2 for r in rows),
            queen_ge4=sum((r['arms'][arm]['queen_exchange_loss'] or 0)>=4 for r in rows)) for arm in ('off','on')}
        exercised=sum(r['exercised'] for r in rows);g=plan['gate'];checks=dict(exercised=exercised>=g['min_exercised_pairs'],
            fatal=totals['on']['fatal']<=totals['off']['fatal']+g['max_additional_fatal'],
            material=totals['on']['material_ge2']<=totals['off']['material_ge2']+g['max_additional_material_ge2'])
        summary=dict(at=now(),cases=len(rows),games=len({r['case']['game'] for r in rows}),exercised=exercised,totals=totals,
            checks=checks,gate_pass=all(checks.values()),elapsed=time.monotonic()-started,plan_sha256=sha(OUT/'plan.json'),results_sha256=sha(OUT/'paired-results.jsonl'),
            scope='Fixed-input paired development diagnostics, subject to independent referee review; no strength claim.')
        unique(OUT/'paired-summary.json',summary);unique(OUT/'terminal.json',dict(at=now(),status='complete',elapsed=time.monotonic()-started));print(json.dumps(summary),flush=True)
    except BaseException as exc:
        unique(OUT/'terminal.json',dict(at=now(),status='failed',error=repr(exc),completed=len(rows),elapsed=time.monotonic()-started));raise


if __name__=='__main__':main()
