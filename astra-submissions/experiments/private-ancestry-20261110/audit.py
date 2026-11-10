"""Independent referee and history audit; truth stays in this reviewer only."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import statistics
import sys
import time
from prepare import ROOT,OUT,feed,sha,write
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

MASK=(1<<64)-1
def vh(text):
    h=1469598103934665603
    for c in text:h=((h^ord(c))*1099511628211)&MASK
    return h
def hm(h,x):
    z=(h+0x9e3779b97f4a7c15*(x|1))&MASK
    z=((z^(z>>30))*0xbf58476d1ce4e5b9)&MASK
    z=((z^(z>>27))*0x94d049bb133111eb)&MASK
    return (z^(z>>31))&MASK
def encoded(uci):
    move=ref.chess.Move.from_uci(uci)
    promotion=6 if move.promotion is None else move.promotion-1
    return move.from_square|(move.to_square<<6)|(promotion<<12)
def board(row):
    b=ref.FowBoard();b.clear()
    for sq,c in enumerate(row['board']):
        if c!='-':b.set_piece_at(sq,ref.chess.Piece.from_symbol(c))
    b.turn=row['side']==0;b.castling_rights=int(row['castle'],16)
    b.ep_square=None if row['ep']<0 else row['ep'];b.halfmove_clock=row['halfmove']
    return b
def position(b):
    return dict(board=''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64)),
                side=0 if b.turn else 1,castle=f'{b.castling_rights:016x}',
                ep=-1 if b.ep_square is None else b.ep_square,halfmove=b.halfmove_clock)
def push(b,uci):
    m=ref.chess.Move.from_uci(uci);assert m in ref.fow_moves(b),uci
    mover=b.turn;b.push(m)
    assert b.king(True) is not None and b.king(False) is not None
    assert not b.is_attacked_by(not mover,b.king(mover))
def own_histories(replay,case):
    us=case['side'];side=0 if us=='white' else 1
    h=hm(0,vh(replay['frames'][0][us]));out=[h]
    for ply in range(1,case['ply']+1):
        if (ply-1)%2==side:h=hm(h,encoded(replay['frames'][ply]['move']))
        h=hm(h,vh(replay['frames'][ply][us]));out.append(h)
    return out


def main():
    start=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());completion=json.loads((OUT/'completion.json').read_text())
    assert completion['status']=='complete' and completion['attempted']==completion['expected']==96
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    by_key={(r['context'],r['arm']):r for r in completion['results']}
    contexts=aliases=state_pairs=world_comparisons=0;games=Counter();coverage=[];costs=[];generation=[];base_cpu=track_cpu=0;rss_delta=[]
    examples=[]
    for case in plan['cases']:
        ci=case['context'];outputs={}
        for arm in ('base','track','pair'):
            result=by_key[ci,arm];folder=Path(result['folder'])
            assert result['exit_code']==0 and not result['timed_out']
            text=(folder/'input.txt').read_text();assert text==feed(case) and sha(folder/'input.txt')==result['input_sha256']
            assert sha(folder/'stdout.jsonl')==result['output_sha256']
            outputs[arm]=[json.loads(line) for line in (folder/'stdout.jsonl').read_text().splitlines()]
        states={a:[r for r in rows if r['kind']=='state'] for a,rows in outputs.items()}
        assert states['base']==states['track']==states['pair']
        parity=[r for r in outputs['pair'] if r['kind']=='exact_parity']
        assert len(parity)==len(states['base'])
        assert [(r['seq'],r['worlds']) for r in parity]==[(r['seq'],r['count']) for r in states['base']]
        state_pairs+=len(parity);world_comparisons+=sum(r['worlds'] for r in parity)
        cb=next(r for r in outputs['base'] if r['kind']=='cost');ct=next(r for r in outputs['track'] if r['kind']=='cost')
        base_cpu+=cb['update_cpu'];track_cpu+=ct['update_cpu'];rss_delta.append((ct['maxrss_kib']-cb['maxrss_kib'])*1024)
        assert max(cb['maxrss_kib'],ct['maxrss_kib']) *1024 <plan['address_space_bytes']
        costs.append(dict(context=ci,base=cb,track=ct))
        g=next(r['cpu_seconds'] for r in outputs['track'] if r['kind']=='generator_cost');generation.append(g)
        cov=next(r for r in outputs['track'] if r['kind']=='coverage');assert cov['valid']==cov['count'];coverage.append(dict(context=ci,**cov))
        records=[r for r in outputs['track'] if r['kind']=='context'];assert len(records)==cov['selected']
        replay=json.loads(Path(case['replay_path']).read_text());ours=case['side'];us=ours=='white';them=not us
        h=own_histories(replay,case)
        for row in records:
            contexts+=1;p=board(row['ancestor']);assert p.turn==us
            assert ref.observation(p,us)==replay['frames'][case['ply']-2][ours]
            assert row['own']==replay['frames'][case['ply']-1]['move']
            assert int(row['own_before'],16)==h[-3] and int(row['own_now'],16)==h[-1]
            push(p,row['own']);after=p.copy(stack=False)
            assert ref.observation(p,us)==replay['frames'][case['ply']-1][ours]
            opp_after_own=ref.observation(p,them)
            ph=hm(int(row['opponent_before'],16),vh(opp_after_own))
            push(p,row['hypothesized_reply']);assert position(p)==row['current']
            assert ref.observation(p,us)==replay['frames'][case['ply']][ours]
            opp_now=ref.observation(p,them);ph=hm(hm(ph,encoded(row['hypothesized_reply'])),vh(opp_now))
            assert ph==int(row['opponent_now'],16)
            alternatives=row['alternatives'];assert alternatives[-1] is None
            alternatives=alternatives[:-1];assert len(alternatives)==row['alternatives_count']
            assert len({r['move'] for r in alternatives})==len(alternatives)
            for alt in alternatives:
                q=board(row['ancestor']);assert alt['move']!=row['own'] and alt['reach_known']==0
                push(q,alt['move']);assert ref.observation(q,them)==opp_after_own
                qh=hm(hm(int(row['own_before'],16),encoded(alt['move'])),vh(ref.observation(q,us)))
                push(q,row['hypothesized_reply']);assert position(q)==alt['current']
                assert ref.observation(q,them)==opp_now
                qh=hm(qh,vh(ref.observation(q,us)))
                assert qh==int(alt['own_history'],16) and qh!=int(row['own_now'],16)
                assert int(alt['opponent_history'],16)==ph
                aliases+=1;games[case['game']]+=1
                if len(examples)<4:examples.append(dict(game=case['game'],ply=case['ply'],context=row,alternative=alt))
    criteria=plan['criteria'];ratio=track_cpu/base_cpu;max_payload=max(r['payload_bytes'] for r in coverage)
    gate=dict(correctness=True,natural_coverage=aliases>=criteria['minimum_native_aliases'] and len(games)>=criteria['minimum_games_with_aliases'],
              update_cost=base_cpu>=criteria['min_base_cpu_for_cost'] and ratio<=criteria['max_update_cpu_ratio'],
              memory=max(rss_delta)<=criteria['max_incremental_rss_bytes'] and max_payload<=criteria['max_ancestry_payload_bytes'],
              generation_cost=max(generation)<=criteria['max_generator_cpu_per_context'])
    write(OUT/'audit.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,gate=gate,design_review_earned=all(gate.values()),
          prefixes=len(plan['cases']),exact_state_comparisons=state_pairs,exact_world_comparisons=world_comparisons,
          sampled_native_contexts=contexts,verified_two_step_aliases=aliases,games_with_aliases=dict(games),
          base_update_cpu=base_cpu,track_update_cpu=track_cpu,update_cpu_ratio=ratio,max_incremental_rss_bytes=max(rss_delta),
          max_ancestry_payload_bytes=max_payload,max_generator_cpu=max(generation),median_generator_cpu=statistics.median(generation),
          coverage=coverage,costs=costs,seconds=time.monotonic()-start,
          scope='Development fixed-thinning private-input screen, not arena throughput or strength. Native full-path repetition counts absent; '
                'two-step local legality/history/metadata checked, not complete draw certification. No alternative probabilities, search-policy changes or games.'))
    write(OUT/'examples.json',examples)
    print(json.dumps(dict(contexts=contexts,aliases=aliases,games=len(games),gate=gate,update_ratio=ratio)),flush=True)

if __name__=='__main__':main()
