from pathlib import Path
import sys,json,gzip,os,subprocess,shutil
repo=Path('/home/henrytan/git/iamavirus');sys.path.insert(0,str(repo/'astra-submissions/tools'));from monitor_arena import Client
root=Path('/media/henrytan/seagate/iamavirus/astra/m4-fresh-20261011-1544');frozen=Path('/media/henrytan/seagate/iamavirus/astra/m4-duck-early-trap-20261011')
gid='e7j8nr8c';g=json.loads(gzip.decompress((root/(gid+'.json.gz')).read_bytes()));diag,meta=Client().get('/api/games/'+gid+'/diagnostics');assert diag['protocol'] and not diag['protocol']['truncated'];g['protocol']=diag['protocol'];(root/(gid+'.json')).write_text(json.dumps(g,indent=2)+'\n');(root/(gid+'.diagnostics.json')).write_text(json.dumps(diag,indent=2)+'\n');(root/(gid+'.metadata.json')).write_text(json.dumps(meta,indent=2)+'\n');out=root/'draw-cold';out.mkdir();shutil.copyfile(__file__,out/'driver.py')
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
cmd=[sys.executable,str(frozen/'probe.py'),str(root/(gid+'.json')),'--binary',str(frozen/'candidate'),'--out',str(out),'--kit',str(frozen/'kit'),'--side','black','--decision','67','--seconds','1','--iterations','100000','--seed','21','--parents','20000','--samples','32','--audit-belief','--fast-roots','--trace-continuation','--stockfish',str(frozen/'stockfish'),'--mode','cold']
with (root/'draw-cold.log').open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
assert r.returncode==0
row=json.loads((out/'results.json').read_text())['rows'][0];print(json.dumps({k:row.get(k) for k in ['game','chosen','played','legal','immediate_loss','true_outcome','belief_count','belief_truth_share','true_state_roots','evaluation']}))
