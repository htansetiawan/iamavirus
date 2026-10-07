import os,sys,json,time,subprocess
from pathlib import Path
candidate,baseline,kit,out,core,seed=sys.argv[1:];a,b,k,o=map(Path,[candidate,baseline,kit,out]);seed=int(seed);games=[]
env={key:value for key,value in os.environ.items() if not key.startswith('FOW_')}
for index,(white,black) in enumerate([(a,b),(b,a)]):
 path=o/f"pair-{seed}-{index}.json"
 command=['taskset','-c',core,str(k/'.venv/bin/python'),str(k/'referee.py'),'--trusted-local','--white',f'env FOW_SEED={seed} bash {white/"run.sh"}','--black',f'env FOW_SEED={seed+1} bash {black/"run.sh"}','--white-name','Astra_exposure' if white==a else 'Arena10','--black-name','Astra_exposure' if black==a else 'Arena10','--base-time','180','--increment','2','--max-plies','1000','--output',str(path)]
 started=time.monotonic()
 with (o/f'pair-{seed}-{index}.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1300)
 replay=json.loads(path.read_text());result=replay['result'];win='1-0' if index==0 else '0-1';score=0.5 if result=='1/2-1/2' else float(result==win)
 games.append(dict(replay=path.name,result=result,reason=replay['reason'],plies=len(replay['frames'])-1,candidate_color='white' if index==0 else 'black',score=score,seconds=time.monotonic()-started,clocks=replay['frames'][-1]['clocks']))
 print(json.dumps(games[-1]),flush=True)
(o/f'pair-{seed}-summary.json').write_text(json.dumps(dict(seed=seed,cores=core,games=games,paired_score=sum(g['score'] for g in games)/2),indent=2)+'\n')
