import hashlib,json,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent
m=json.loads((r/'manifest.json').read_text())
for name,a in m['artifacts'].items():
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==a['sha256'],name
for j in m['jobs']:
 out=r/j['id']
 assert not out.exists(), 'Refuse to overwrite an attempted job'
 out.mkdir()
 cmd=[sys.executable,str(r/'probe.py'),str(r/'game.json'),'--binary',str(r/'candidate'),'--stockfish',str(r/'stockfish'),'--kit',str(r/'kit'),'--out',str(out),'--side','white','--decision','6','--seconds','10','--iterations','1000000','--samples','32','--parents','20000','--audit-belief','--fast-roots','--mode','warm','--seed',str(j['seed']),'--settle-fraction',str(j['fraction'])]
 print(json.dumps({'start':j}),flush=True)
 (out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 with (out/'runner.log').open('w') as f: p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 (out/'receipt.json').write_text(json.dumps({'returncode':p.returncode})+'\n')
 if p.returncode: raise RuntimeError('Probe failed; retain this attempt')
 result=json.loads((out/'results.json').read_text())['rows'][0]
 assert result['returncode']==0 and result['prefix_exact'] and result['legal']
 assert all(x['ok']==1 and x['snapshot']==1 and x['over']==0 for x in result['metrics'])
 if j['fraction']>0: assert len(result['settling'])==6 and all(x['iterations']>0 for x in result['settling'])
 print(json.dumps({'completed':j,'move':result['chosen'],'fatal_share':result['chosen_fatal_share'],'truth_share':result.get('belief_truth_share'),'settling':result['settling'][-1:]},sort_keys=True),flush=True)
