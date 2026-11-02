import json
import numpy as np
from bound import audit,log_probabilities,partition


def fixture():
    x=np.zeros((6,26),np.float32);x[[2,5],0]=1
    return dict(x=x,base=np.zeros(6,np.float32),moves=np.array([1,2,3,1,2,3],np.uint16),
                counts=np.zeros(6,np.uint32),hn=np.zeros(2,np.uint32),u=np.log([.6,.4]).astype(np.float32),
                a_parent=np.repeat(np.arange(2),3),valid=np.ones(6,bool),
                positive=np.array([1,0,0,0,0,0],bool))


def main():
    row=fixture();result,_,members=audit(row)
    expected=float(np.exp(row['u'][0])/(2*np.exp(row['u'].astype(float)).sum()))
    assert abs(result['probability_ceiling']-expected)<1e-7
    geometry,_,_=audit(row,True);assert geometry['probability_ceiling']>result['probability_ceiling']
    local,_,_=audit(row,parent_local=True);assert abs(local['probability_ceiling']-.5)<1e-12
    local_geometry,_,_=audit(row,geometry=True,parent_local=True);assert local_geometry['nll_floor']==0
    rng=np.random.default_rng(2331102);tested=0;max_gap=0.
    for history in (False,True):
        r=fixture()
        if history:r['hn'][:]=10;r['counts'][:]=[3,3,4,3,3,4]
        bound,_,groups=audit(r)
        for _ in range(500):
            logits=r['base'].astype(float)+np.where(r['x'][:,0]>0,rng.normal(0,10),rng.normal(0,10))
            post,logp=log_probabilities(r,logits)
            assert post<=-bound['nll_floor']+1e-12
            for g in groups:
                max_gap=max(max_gap,float(np.ptp(logp[g])))
                assert np.ptp(logp[g])<1e-12
            tested+=1
    # Different normalizer multiplicities, total history counts or selected
    # action counts must separate classes; equal raw features alone do not suffice.
    for name in ('normalizer','history_total','action_count'):
        r=fixture()
        if name=='normalizer':r['x'][5,1]=1
        else:
            r['hn'][:]=10;r['counts'][:]=[3,3,4,3,3,4]
            if name=='history_total':r['hn'][1]=11
            else:r['counts'][3]=4;r['counts'][5]=3
        ids,_=partition(r);assert ids[0]!=ids[3],name
    # Invalid alternatives never enter the conditioned denominator; positives
    # remain natural and no extra state is inserted.
    r=fixture();r['valid'][1:]=False
    b,_,_=audit(r);assert b['nll_floor']==0
    # Extreme incoming weights must not disappear through global underflow.
    r=fixture();r['u'][:]=[-10000,0]
    b,_,_=audit(r);assert np.isfinite(b['nll_floor']) and b['nll_floor']>9999
    b,_,_=audit(r,parent_local=True);assert abs(b['probability_ceiling']-.5)<1e-12
    print(json.dumps(dict(random_probability_checks=tested,invariant_logp_error=max_gap,
                         normalizer_and_history_separation=True,extreme_log_weights=True,
                         fixture_ceiling=result['probability_ceiling'],geometry_ceiling=geometry['probability_ceiling'])))


if __name__=='__main__':main()
