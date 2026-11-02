"""Observable input contract for a future root-action critic; no fitted model."""
import hashlib
import json
import math

SYMBOLS='-?PNBRQKpnbrqk'
VERSION='astra-root-action-observable-v1'


def actor_history(prefix):
    ply=prefix['branch_ply'];side=ply%2;key=('white','black')[side];frames=prefix['frames']
    assert len(frames)==ply+1
    views=[f[key] for f in frames]
    assert all(len(v)==64 and all(c in SYMBOLS for c in v) for v in views)
    own_moves=[frames[i+1]['move'] for i in range(side,ply,2)]
    clocks=[frames[i]['clocks'][side] for i in range(side,ply+1,2)]
    post=[frames[i+1]['clocks'][side] for i in range(side,ply,2)]
    assert all(math.isfinite(c) and c>=0 for c in clocks+post)
    tc={k:prefix['timeControl'][k] for k in ('baseSeconds','incrementSeconds')}
    return dict(side=key,ply=ply,observations=views,own_moves=own_moves,
                own_turn_clocks=clocks,own_post_move_clocks=post,time_control=tc)


def critic_input(prefix, candidate, proposal):
    """Whitelist only quantities available after the current root search."""
    h=actor_history(prefix)
    row=next(r for r in proposal['rows'] if r['move']==candidate)
    assert candidate in proposal['view_legal'] and len(candidate) in (4,5)
    charge=proposal['common_charge'];remaining=h['own_turn_clocks'][-1]-charge
    assert math.isfinite(charge) and charge>=0 and remaining>0
    assert math.isfinite(row['value']) and 0<=row['probability']<=1
    return dict(schema=VERSION,actor=h,candidate=candidate,
                search_probability=row['probability'],search_tree_value=row['value'],
                proposal_seconds=charge,own_seconds_after_proposal=remaining)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
