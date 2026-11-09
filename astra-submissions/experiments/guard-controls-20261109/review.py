"""Audit paired artifacts and apply the frozen gross-regression screen."""
from collections import Counter
import json
from pathlib import Path
import sys

from prepare import ROOT,OUT,sha,write
sys.path[:0]=[str(ROOT),'/home/henrytan/git/fow-starter']
import referee as ref


def main():
    plan=json.loads((OUT/'plan.json').read_text());terminal=json.loads((OUT/'terminal.json').read_text())
    assert terminal['state']=='complete' and terminal['completed']==len(plan['cases'])
    for path,digest in plan['dependencies'].items():assert sha(Path(path))==digest,path
    rows=[];counts=Counter();frames=0
    for game in plan['games']:
        assert sha(Path(game['replay_path']))==game['replay_sha256']
        r=json.loads(Path(game['replay_path']).read_text());b=ref.FowBoard()
        for f in r['frames']:
            if f['move']:
                mv=ref.chess.Move.from_uci(f['move']);assert mv in ref.fow_moves(b);b.push(mv)
            assert ref.observation(b,True)==f['white'] and ref.observation(b,False)==f['black'];frames+=1
    for case in plan['cases']:
        folder=OUT/'jobs'/case['id'];r=json.loads((folder/'result.json').read_text())
        for name,digest in r['files'].items():assert sha(folder/name)==digest,(case,name)
        a,b=r['arms']['base'],r['arms']['candidate'];mask_changed=False;added_chosen=False
        assert not r['live_owned_members']
        if r['exercised']:
            ta,tb=a['target'],b['target'];assert ta['samples']==tb['samples'] and a['belief_fingerprint']==b['belief_fingerprint']
            mask_changed=set(ta['avoid_moves'])!=set(tb['avoid_moves'])
            added_chosen=b['move'] in set(ta['avoid_moves'])-set(tb['avoid_moves'])
        rp=json.loads(Path(case['replay_path']).read_text());board=ref.FowBoard()
        for f in rp['frames'][1:case['ply']+1]:board.push_uci(f['move'])
        side=case['side']=='white'
        for name,arm in [('base',a),('candidate',b)]:
            move=ref.chess.Move.from_uci(arm['move']);assert move in ref.fow_moves(board)
            board.push(move);king=board.king(side);fatal=king is None or board.is_attacked_by(not side,king);board.pop()
            assert arm['fatal']==fatal,(case,name)
            counts[name+'_fatal']+=fatal
            counts[name+'_material_ge3']+=arm['exchange_loss'] is not None and arm['exchange_loss']>=3
        counts['mask_changed']+=mask_changed;counts['added_chosen']+=added_chosen;counts['changed_move']+=a['move']!=b['move']
        counts['fatal_broken']+=not a['fatal'] and b['fatal']
        counts['fatal_fixed']+=a['fatal'] and not b['fatal']
        counts['opening_fatal_broken']+=case['kind']=='opening' and not a['fatal'] and b['fatal']
        if a['exchange_loss'] is not None and b['exchange_loss'] is not None:
            counts['material_broken']+=a['exchange_loss']<3 and b['exchange_loss']>=3
        rows.append(dict(case=case,mask_changed=mask_changed,added_chosen=added_chosen,
                         moves=[a['move'],b['move']],fatal=[a['fatal'],b['fatal']],
                         material=[a['exchange_loss'],b['exchange_loss']]))
    gate=plan['gate'];checks=dict(min_mask_changes=counts['mask_changed']>=gate['min_mask_changes'],
         min_added_chosen=counts['added_chosen']>=gate['min_added_actions_chosen'],
         fatal=counts['fatal_broken']<=gate['max_additional_fatal'],
         opening=counts['opening_fatal_broken']==0,
         material=counts['material_broken']<=gate['max_additional_material_ge3'])
    result=dict(gate_pass=all(checks.values()),checks=checks,counts=dict(counts),cases=len(rows),games=len(plan['games']),
       referee_frames=frames,rows=rows,plan_sha256=sha(OUT/'plan.json'),
       scope='Historical control screen with unused source games, not a strength estimate; only authorizes the separately frozen full-game pilot.')
    write(OUT/'review.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
