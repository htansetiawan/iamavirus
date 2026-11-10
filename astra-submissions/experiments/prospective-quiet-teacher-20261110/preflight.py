"""C/course/cache input equivalence on old fit-TRAIN only; no network scoring."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from protocol import ROOT,OUT
from features import Producer,batch
sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from reconstructed_cache import Cache,fields,decode_move
from prior_training_cache import PriorCache
sys.path.insert(0,str(ROOT/'astra-submissions/experiments/world-quiet-attention-20261110'))
from data import CONTEXT,FRAME


def main():
    old=json.loads((ROOT/'astra-submissions/analysis/world-quiet-fit-20261110/plan.json').read_text())
    world=Cache(old['state_cache']);prior=PriorCache(old['feature_cache'])
    context=np.frombuffer(prior.contexts,dtype=CONTEXT);frames=np.frombuffer(world.data,dtype=FRAME)
    byrecord={int(row['record']):row for row in context}
    wanted=set(old['split']['train']);games=[g for g in world.games if g['game'] in wanted][:32]
    producer=Producer(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so')
    count=actions=states=0;digest=hashlib.sha256()
    for game in games:
        sequence=[decode_move(fields(world.record(game['start']+ply))[7]) for ply in range(game['moves'])]
        g=dict(game,frames=game['records'],moves=sequence)
        for inputs,meta in producer.game(g):
            index=game['start']+meta['ply'];row=byrecord[index];start=int(row['start']);n=int(row['count']);expected=prior.rows[start:start+n]
            assert np.array_equal(inputs['x'],expected['x']) and np.array_equal(inputs['base'],expected['base'][:,1])
            assert np.array_equal(inputs['counts'],expected['history'].astype(np.float32))
            assert np.array_equal(inputs['moves'],expected['move']) and inputs['history_n']==np.float32(row['total'])
            assert meta['target']==int(row['target'])
            source=frames[index];piece=np.empty(64,np.int64);piece[0::2]=source['board']&15;piece[1::2]=source['board']>>4
            square=np.arange(64,dtype=np.uint64)
            values=[piece,(((source['white']>>square)&1)|(((source['black']>>square)&1)<<1)).astype(np.int64),
                ((source['castle']>>square)&1).astype(np.int64),(source['ep']==np.arange(64)).astype(np.int64),
                np.float32(source['half']),np.int64(source['side'])]
            assert all(np.array_equal(a,b) for a,b in zip(inputs['board'],values))
            decoded=batch([inputs]);assert decoded['moves'].shape==(1,n) and decoded['valid'].all()
            for v in inputs['board']+[inputs['x'],inputs['base'],inputs['counts'],inputs['moves']]:digest.update(np.asarray(v).tobytes())
            count+=1;actions+=n
        states+=game['records']
    result=dict(passed=True,games=len(games),frames=states,contexts=count,actions=actions,input_sha256=digest.hexdigest(),
        scope='Old320fit-TRAIN source parity only: native C/course full states/metadata/both views, native features/base/history/candidate codec and typed board tensors match318/316cache. No teacher or control predictions, new data, API or fitting.')
    with (OUT/'input-preflight.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
