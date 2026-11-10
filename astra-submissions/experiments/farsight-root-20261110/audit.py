"""Join replay truth after actor exit; independently review course rules and sums."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/farsight-root-20261110'
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def board_string(b): return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
def mover_lost(b):
    king=b.king(not b.turn)
    return king is None or b.is_attacked_by(b.turn,king)


def world_board(w):
    rows=[]
    for rank in range(7,-1,-1):
        row='';empty=0
        for c in w['board'][rank*8:rank*8+8]:
            if c=='-':empty+=1
            else:
                if empty:row+=str(empty);empty=0
                row+=c
        if empty:row+=str(empty)
        rows.append(row)
    b=ref.FowBoard('/'.join(rows)+' '+('w' if w['side']==0 else 'b')+' - - 0 1')
    b.castling_rights=int(w['castle'],16)
    b.ep_square=None if w['ep']<0 else w['ep']
    b.halfmove_clock=w['halfmove']
    return b


def main():
    plan=read(OUT/'plan.json');done=read(OUT/'completion.json');assert done['status']=='complete'
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    folder=Path(plan['spool'])/'actor'
    assert read(folder/'terminal.json')['exit_code']==0
    assert read(folder/'terminal.json')['live_owned_members']==[]
    for name,h in done['files'].items():assert sha(folder/name)==h,name
    replay=read(plan['replay_path']);root_ply=plan['root_ply'];side=plan['side'];key=('white','black')[side]
    feed=[];forced=[];clocks=[]
    truth=ref.FowBoard()
    for ply,f in enumerate(replay['frames'][:root_ply+1]):
        if ply:
            move=ref.chess.Move.from_uci(f['move']);assert move in ref.fow_moves(truth);truth.push(move)
        assert board_string(truth)==f['board']
        assert ref.observation(truth,True)==f['white'] and ref.observation(truth,False)==f['black']
        feed.append(f[key])
        if ply%2==side:
            feed.append(str(f['clocks'][side]))
            if ply<root_ply:
                forced.append(replay['frames'][ply+1]['move']);clocks.append(replay['frames'][ply+1]['clocks'][side])
    delivered=(folder/'input.txt').read_text().splitlines()
    assert delivered[0]=='fow'
    header=delivered[1].split();tc=replay.get('timeControl',{})
    assert header[0]=='b' and list(map(float,header[1:]))==[tc.get('baseSeconds',180),tc.get('incrementSeconds',2)]
    assert delivered[2:]==feed
    settings=read(folder/'settings.json')
    assert settings['MIST_FORCE_MOVES']==','.join(forced)
    assert settings['ASTRA_POST_CLOCKS']==','.join(map(str,clocks))
    assert 'MIST_TRUTH_SEQ' not in settings and settings['ASTRA_SF_ALLCHILDREN']=='1'
    assert settings['FOW_SEED']==str(plan['seed'])
    pop=read(folder/'population.json');targets=[json.loads(s) for s in (folder/'targets.jsonl').read_text().splitlines()]
    assert len(targets)==1;target=targets[0]
    assert pop['count']==target['belief_count']==len(pop['worlds'])
    assert target['own_reach_consistent']
    samples=pop['samples'];worlds=pop['worlds']
    assert [(s['index'],s['weight']) for s in samples]==[(s['belief_index'],s['weight']) for s in target['samples']]
    assert abs(math.fsum(s['weight'] for s in samples)-1)<1e-12
    assert abs(math.fsum(a['probability'] for a in target['actions'])-1)<1e-12
    assert all(w['index']==i and math.isfinite(w['logw']) for i,w in enumerate(worlds))
    top=max(w['logw'] for w in worlds);weights=[math.exp(w['logw']-top) for w in worlds];den=math.fsum(weights)
    placement=[w['index'] for w in worlds if w['board']==board_string(truth)]
    exact=[i for i in placement if worlds[i]['side']==side and int(worlds[i]['castle'],16)==truth.castling_rights
           and worlds[i]['ep']==(truth.ep_square if truth.ep_square is not None else -1) and worlds[i]['halfmove']==truth.halfmove_clock]
    rook=ref.chess.F8;queen=ref.chess.F7
    family=[w['index'] for w in worlds if w['board'][rook]=='R' and w['board'][queen]=='Q']
    validate=worlds if len(worlds)<=20000 else sorted(worlds,key=lambda w:hashlib.sha256(('309-world-'+str(w['index'])+'-'+w['board']).encode()).digest())[:1024]
    for w in validate:
        b=world_board(w);assert board_string(b)==w['board'];assert ref.observation(b,side==0)==replay['frames'][root_ply][key]
    expected_actions=[a['uci'] for a in target['actions']];q={a:0. for a in expected_actions}
    sampled_traps=[];reply_records=[];reply_count=0
    for s in samples:
        w=worlds[s['index']];b=world_board(w)
        assert board_string(b)==next(t['hypothesis_board'] for t in target['samples'] if t['belief_index']==s['index'])
        assert [a['move'] for a in s['actions']]==expected_actions
        legal={m.uci() for m in ref.fow_moves(b)}
        for a in s['actions']:
            q[a['move']]+=s['weight']*a['value']
            assert a['move'] in legal
            if a['replies']:
                after=b.copy();after.push_uci(a['move'])
                assert {m.uci() for m in ref.fow_moves(after)}=={v['move'] for v in a['replies']}
                assert abs(math.fsum(v['probability'] for v in a['replies'])-1)<1e-12
                assert abs(math.fsum(v['probability']*v['value'] for v in a['replies'])-a['value'])<1e-10
                reply_count+=len(a['replies'])
            if a['move']=='a2a1r':
                rr=next((v for v in a['replies'] if v['move']=='f7g8'),None)
                reply_records.append(dict(index=s['index'],weight=s['weight'],pieces_present=s['index'] in family,
                    branch_value=a['value'],branch_frontier=a['frontier'],recorded_reply=rr))
        # Whether the recorded two-move net is valid in THIS sampled hypothesis.
        probe=b.copy();actual=ref.chess.Move.from_uci('a2a1r');reply=ref.chess.Move.from_uci('f7g8')
        if actual in ref.fow_moves(probe):
            probe.push(actual)
            if not mover_lost(probe) and reply in ref.fow_moves(probe):
                probe.push(reply)
                if not mover_lost(probe):
                    safe=[]
                    for move in ref.fow_moves(probe):
                        after=probe.copy();after.push(move)
                        if not mover_lost(after):safe.append(move.uci())
                    if not safe:sampled_traps.append(s['index'])
    for a in target['actions']:assert abs(q[a['uci']]-a['q'])<1e-9
    assert abs(math.fsum(a['probability']*q[a['uci']] for a in target['actions'])-target['root_value'])<1e-9
    assert abs(target['root_value']-pop['root_value'])<1e-9
    assert max(target['actions'],key=lambda a:a['probability'])['uci']==target['solver_move']
    def share(indices): return math.fsum(weights[i] for i in indices)/den
    sample_share=lambda ids:math.fsum(s['weight'] for s in samples if s['index'] in ids)
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,game=plan['game'],root_ply=root_ply,
        actor_input_verified_private=True,historical_post_clocks_verified=True,course_prefix_frames=root_ply+1,
        population=pop['count'],population_observations_checked=len(validate),all_population_observations_checked=len(validate)==len(worlds),
        true_placement_indices=placement,true_rule_state_indices=exact,true_placement_share=share(placement),true_rule_state_share=share(exact),
        rook_f8_queen_f7_worlds=len(family),rook_f8_queen_f7_share=share(family),
        sampled_worlds=len(samples),sampled_true_share=sample_share(exact),sampled_piece_family_share=sample_share(family),
        sampled_actual_net_share=sample_share(sampled_traps),sampled_actual_net_indices=sampled_traps,
        all_exported_reply_sets_verified=reply_count,recorded_reply_in_sampled_branches=reply_records,
        actions=target['actions'],avoid_moves=target['avoid_moves'],solver_move=target['solver_move'],frontend_move=done['move'],
        frontend_changed_move=target['solver_move']!=done['move'],root_value=target['root_value'],nodes=target['nodes'],iterations=target['iterations'],
        search_seconds=target['search_budget_seconds'],
        limitation='One selected reconstruction with restored historical post-clocks. Unknown arena RNG, historical load and timing thinning are not reproduced. No candidate or Elo effect; raw piece-family mass alone is not a forced-net probability.',
        source_hashes=dict(plan=sha(OUT/'plan.json'),completion=sha(OUT/'completion.json'),population=sha(folder/'population.json'),targets=sha(folder/'targets.jsonl'),auditor=sha(__file__)))
    with (OUT/'audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('actions','recorded_reply_in_sampled_branches')},indent=2),flush=True)


if __name__=='__main__':main()
