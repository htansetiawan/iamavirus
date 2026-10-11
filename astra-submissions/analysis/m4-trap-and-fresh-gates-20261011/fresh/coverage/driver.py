from pathlib import Path
import json,sys,os,subprocess,shutil,hashlib
root=Path('/media/henrytan/seagate/iamavirus/astra/m4-fresh-20261011-1544');frozen=Path('/media/henrytan/seagate/iamavirus/astra/m4-duck-early-trap-20261011')
cases=json.loads((root/'cases.json').read_text());out=root/'coverage';out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'driver.py')
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))};rows=[]
for c in cases:
 if c['game'] not in ['gf2qssqu','9aij6zfq']:continue
 for arm,samples,witness in [('all128',128,False),('witness32',32,True)]:
  target=out/(c['game']+'-'+arm);cmd=[sys.executable,str(frozen/'probe.py'),c['replay'],'--binary',str(frozen/'candidate'),'--out',str(target),'--kit',str(frozen/'kit'),'--side',c['side'],'--decision',str(c['decision']),'--seconds','1','--iterations','100000','--seed','21','--parents','20000','--samples',str(samples),'--audit-belief','--fast-roots','--trace-continuation','--trace-moves','f1f2' if c['game']=='gf2qssqu' else 'g8f8','--stockfish',str(frozen/'stockfish'),'--mode','cold']
  if witness:cmd.append('--witnesses')
  with (out/(c['game']+'-'+arm+'.log')).open('w') as log:p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
  if p.returncode:raise RuntimeError(c['game']+' '+arm+' failed')
  row=json.loads((target/'results.json').read_text())['rows'][0];row['arm']=arm;rows.append(row);(out/'summary.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
  print(json.dumps({k:row.get(k) for k in ['game','arm','chosen','immediate_loss','belief_count','belief_truth_share','true_state_roots','chosen_fatal_share','witness_metrics']}),flush=True)
(out/'status.json').write_text(json.dumps({'complete':True,'count':len(rows)})+'\n')
