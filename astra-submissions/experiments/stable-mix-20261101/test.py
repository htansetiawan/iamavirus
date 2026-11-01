#!/usr/bin/env python3
import json,os,subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
results=[]
for mode,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie'])]:
    binary=HERE/'build'/('test-'+mode)
    built=subprocess.run(['gcc','-std=c11','-Wall','-Wextra',*flags,str(HERE/'test_root_mix.c'),'-lm','-o',str(binary)],capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    env={**os.environ,'ASAN_OPTIONS':'detect_leaks=1:abort_on_error=1'}
    p=subprocess.run([str(binary)],capture_output=True,text=True,env=env,timeout=30)
    assert p.returncode==0,p.stderr
    result={'mode':mode,'oracle':json.loads(p.stdout),'stderr':p.stderr}
    fixed=[]
    for i in range(2):
        p=subprocess.run([str(binary),'sequence'],capture_output=True,text=True,env={**env,'MIST_ACTION_SEED':'11012026'},timeout=30)
        assert p.returncode==0 and 'source=explicit' in p.stderr,p.stderr
        fixed.append(p.stdout)
    assert fixed[0]==fixed[1]
    random=[]
    for i in range(2):
        entropy_env={k:v for k,v in env.items() if k!='MIST_ACTION_SEED'}
        p=subprocess.run([str(binary),'sequence'],capture_output=True,text=True,env=entropy_env,timeout=30)
        assert p.returncode==0 and 'source=os' in p.stderr,p.stderr
        random.append(p.stdout)
    assert random[0]!=random[1]
    bad=subprocess.run([str(binary),'sequence'],capture_output=True,text=True,env={**env,'MIST_ACTION_SEED':'-1'},timeout=30)
    assert bad.returncode==2 and 'invalid action seed' in bad.stderr
    result.update(explicit_seed_repeat=fixed[0].strip(),entropy_sequences_distinct=True,invalid_seed_rejected=True)
    results.append(result)
(HERE/'correctness.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'passes':len(results),'checks':'support history, no refill, exact CDF, empirical probabilities, independent RNG, entropy, RPS adversarial payoff, sanitizer'}))
