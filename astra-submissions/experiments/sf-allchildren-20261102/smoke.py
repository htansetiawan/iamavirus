"""Check exact production launchers before any full game starts."""
import json
import os
import subprocess
import sys
from build import HERE,ROOT,OUT,sha,write
sys.path.insert(0,str(ROOT))
from learning.rules import Board

def main():
    os.sched_setaffinity(0,{0,1});records=[];path=OUT/'full-games/production-smoke.json'
    assert not path.exists()
    try:
        for arm in ('base','candidate'):
            for side in (0,1):
                b=Board();feed=['fow',('w' if side==0 else 'b')+' 180 2',b.observation(side)]
                if side:b.push('d2d4');feed.append(b.observation(side))
                feed.append('180')
                env={k:v for k,v in os.environ.items() if not k.startswith(('ASTRA_','MIST_','FOW_'))}
                env.update(MIST_MAX_SECONDS='.1',FOW_SEED='2561200')
                launcher=HERE/'build'/arm/'run.sh'
                r=subprocess.run(['bash',str(launcher)],input='\n'.join(feed)+'\n',capture_output=True,text=True,env=env,timeout=30)
                records.append(dict(arm=arm,side=side,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,launcher_sha256=sha(launcher)))
                moves=[s[5:] for s in r.stdout.splitlines() if s.startswith('move ')]
                assert r.returncode==0 and len(moves)==1 and moves[0] in b.legal_moves(),records[-1]
                assert 'mist: stockfish ready' in r.stderr and 'astra-solver-pair' not in r.stderr
        write(path,dict(passed=True,records=records,source_sha256=sha(__file__)))
        print(json.dumps(dict(passed=True,processes=len(records))),flush=True)
    except BaseException as exc:write(path,dict(passed=False,error=repr(exc),records=records,source_sha256=sha(__file__)));raise

if __name__=='__main__':main()
