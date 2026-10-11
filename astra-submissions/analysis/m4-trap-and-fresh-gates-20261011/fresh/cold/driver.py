from pathlib import Path
import sys,json,os,subprocess,shutil,hashlib
root=Path('/media/henrytan/seagate/iamavirus/astra/m4-fresh-20261011-1544')
frozen=Path('/media/henrytan/seagate/iamavirus/astra/m4-duck-early-trap-20261011')
audit={r['id']:r for r in json.loads((root/'audit.json').read_text())['games']}
cases=json.loads((root/'cases.json').read_text());out=root/'cold';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'driver.py')
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
rows=[]
for c in cases:
 if not audit[c['game']]['decisions'][-1]['safe_moves']:
  print(json.dumps({'skipped':c['game'],'reason':'no physically surviving move'}),flush=True);continue
 assert c['complete_protocol']
 target=out/c['game'];cmd=[sys.executable,str(frozen/'probe.py'),c['replay'],'--binary',str(frozen/'candidate'),'--out',str(target),'--kit',str(frozen/'kit'),'--side',c['side'],'--decision',str(c['decision']),'--seconds','1','--iterations','100000','--seed','21','--parents','20000','--samples','32','--audit-belief','--fast-roots','--trace-continuation','--stockfish',str(frozen/'stockfish'),'--mode','cold']
 with (out/(c['game']+'.log')).open('w') as log:p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
 if p.returncode:raise RuntimeError(c['game']+' failed')
 row=json.loads((target/'results.json').read_text())['rows'][0];rows.append(row)
 (out/'summary.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
 print(json.dumps({k:row[k] for k in ['game','ply','chosen','played','legal','immediate_loss','belief_count','belief_truth_share','true_state_roots','chosen_fatal_share','evaluation']}),flush=True)
(out/'status.json').write_text(json.dumps({'complete':True,'count':len(rows)})+'\n')
