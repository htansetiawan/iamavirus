#!/usr/bin/env python3
"""Independent exhaustive pure-free-policy oracle; native layered BR is not reused."""
import hashlib,itertools,json,os,resource,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'astra-submissions/analysis/response-best-reply-r2-20261101'
OUT.mkdir(parents=True,exist_ok=True)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def value(g,x,id=None):
    n=g['nodes'][g['root'] if id is None else id]
    if n['type']==2:return n['value']
    weights=n['chance'] if n['type']==0 else x[g['infosets'][n['infoset']]['offset']:][:n['count'] if 'count' in n else len(n['children'])]
    return sum(p*value(g,x,c) for p,c in zip(weights,n['children']))
def first_sets(g,player):
    result=set()
    def visit(id,seen):
        n=g['nodes'][id]
        if n['type']==1 and n['player']==player:
            if not seen:result.add(n['infoset'])
            seen=True
        for c in n['children']:visit(c,seen)
    visit(g['root'],False);return result
def oracle(g,player,mode):
    infos=[i for i,s in enumerate(g['infosets']) if s['player']==player];first=first_sets(g,player);scores=[]
    for actions in itertools.product([0,1],repeat=len(infos)):
        x=g['x'].copy()
        for i,a in zip(infos,actions):
            s=g['infosets'][i];c=s['confidence'] if mode==1 or mode==2 and i in first else 0
            x[s['offset']:s['offset']+2]=[c*q+(1-c)*(a==j) for j,q in enumerate(s['q'])]
        scores.append(value(g,x))
    return (max(scores) if player==0 else min(scores)),len(scores)
records=[];enumerated=0
for name,flags in [('optimized',['-O2']),('sanitized',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    binary=HERE/'build'/('test-'+name)
    cmd=['gcc',*flags,'-std=c11','-I'+str(HERE/'build/src'),str(HERE/'test_br.c'),str(HERE/'build/src/cfr.c'),'-lm','-o',str(binary)]
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    r=subprocess.run([str(binary)],capture_output=True,text=True);assert r.returncode==0,r.stderr
    fixtures=json.loads(r.stdout);assert len(fixtures)==6;checks=0
    for g in fixtures:
        assert abs(value(g,g['x'])-g['original_value'])<1e-12
        for s in g['solutions']:
            expected,number=oracle(g,s['player'],s['mode']);enumerated+=number
            assert abs(expected-s['value'])<1e-10,(name,g['seed'],s,expected)
            assert abs(value(g,s['strategy'])-expected)<1e-10
            for i,info in enumerate(g['infosets']):
                if info['player']!=s['player']:
                    o=info['offset'];assert s['strategy'][o:o+2]==g['x'][o:o+2]
            checks+=1
    invalid=subprocess.run([str(binary),'imperfect-recall'],capture_output=True,text=True)
    assert invalid.returncode!=0 and 'b.iprev[I]==prev[id]' in invalid.stderr,invalid.stderr
    evidence=OUT/(name+'-fixtures.json');evidence.write_text(json.dumps(fixtures,indent=2)+'\n')
    records.append(dict(mode=name,command=cmd,returncode=r.returncode,br_comparisons=checks,fixture_sha256=sha(evidence),invalid_recall_exit=invalid.returncode,invalid_recall_stderr=invalid.stderr))
out=dict(tests=records,enumerated_strategies=enumerated,source_sha256={str(p):sha(p) for p in [Path(__file__),HERE/'test_br.c',HERE/'br.h']},
         covers=['Shared information sets across unequal worlds','Two responding decisions with remembered own action','Fixed opponent mixed and pure policies','Zero chance reach','Confidence 0, .25, .75, 1','Constrained, first-only and unrestricted feasible sets','Both responding-player signs','Imperfect recall rejection'],
         oracle='Independent Python exhaustive enumeration of every pure free policy, including all shared infosets jointly; evaluated with an independent recursive value function.')
(OUT/'correctness.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'tests':len(records),'br_comparisons':sum(r['br_comparisons'] for r in records),'enumerated_strategies':enumerated}))
