"""Protocol/rules smoke only, both colours and both expansion schedulers."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from build import HERE,ROOT,OUT
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from learning import ingest
from fresh_taxonomy_gate import protocol


def main():
    os.sched_setaffinity(0,{2,3})
    cases=json.loads((ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json').read_text())['cases']
    replay=json.loads(Path(cases[0]['replay_path']).read_text());states,errors=ingest.validate_replay(replay);assert not errors
    rows=[];directory=HERE/'build/candidate'
    for side in (0,1):
        feed,forced=protocol(replay,side,side);assert not forced
        for asynchronous in (0,1):
            for enabled in (0,1):
                env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
                env.update(MIST_EXPANSION_Q=str(enabled),MIST_ASYNC=str(asynchronous),MIST_MAX_SECONDS='.2',
                    MIST_FORCE_MOVES='',FOW_SEED='2341102')
                r=subprocess.run(['bash','run.sh'],cwd=directory,env=env,input=feed,text=True,capture_output=True,timeout=30)
                stem=f'smoke-{side}-{asynchronous}-{enabled}';(OUT/(stem+'.stderr')).write_text(r.stderr);(OUT/(stem+'.stdout')).write_text(r.stdout)
                assert r.returncode==0,(stem,r.returncode)
                assert 'mist: stockfish ready' in r.stderr
                moves=[s[5:] for s in r.stdout.splitlines() if s.startswith('move ')];assert len(moves)==1
                assert moves[0] in states[side].board.legal_moves()
                q=[s for s in r.stderr.splitlines() if s.startswith('astra-expansion-q ')]
                assert bool(q)==bool(enabled)
                if enabled:
                    m=dict(re.findall(r'(\w+)=([\d.]+)',q[-1]));assert int(m['refreshes'])>0 and int(m['scored'])>0 and int(m['recall_failures'])==0
                rows.append(dict(side=side,asynchronous=asynchronous,enabled=enabled,legal=True,exit=0,diagnostic=q))
    (OUT/'runtime-tests.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'protocol_tests':len(rows),'all_legal':True,'conditional_values_exercised':4}))


if __name__=='__main__':main()
