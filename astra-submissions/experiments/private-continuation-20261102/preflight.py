"""Meaningful restoration fixtures: repetition, EP, castling and privacy."""
from collections import Counter
import copy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from continuation import HERE,ROOT,REF,actor_prefix,prefix,referee,run,sha,validate_prefix

OUT=ROOT/'astra-submissions/analysis/private-continuation-20261102'


def synthetic(moves):
    ref=referee();b=ref.FowBoard();clocks=[180.,180.]
    frames=[ref.make_frame(b,clocks)]
    for i,move in enumerate(moves):
        assert move in {m.uci() for m in ref.fow_moves(b)}
        b.push_uci(move);clocks[i%2]-=.125*(i+1)
        frames.append(ref.make_frame(b,clocks,move))
    return dict(id='fixture',timeControl=dict(baseSeconds=180,incrementSeconds=2),frames=frames)


def main():
    reports=[]
    fixtures=[('threefold',['g1f3','g8f6','f3g1','f6g8']*2,4),
        ('ep',['e2e4','a7a6','e4e5','d7d5','e5d6','c7d6'],4),
        ('castling',['e2e4','e7e5','g1f3','b8c6','f1c4','g8f6','e1g1','a7a6'],6)]
    for name,moves,branch in fixtures:
        replay=synthetic(moves);p=prefix(replay,branch);directory=OUT/('preflight-'+name)
        directory.mkdir(exist_ok=False)
        commands=[]
        for side in (0,1):
            actor=actor_prefix(p,side)
            commands.append([sys.executable,str(HERE/'fixture_bot.py'),json.dumps(dict(
                moves=moves[side::2],views=actor['views'],clocks=actor['clocks']+[actor['branch_clock']]))])
            redacted=copy.deepcopy(p)
            for i,f in enumerate(redacted['frames']):
                f['board']='x'*64;f[('black','white')[side]]='x'*64
                f['clocks'][1-side]=-999
                if i and (i-1)%2!=side:f['move']='a1a1'
            assert actor_prefix(redacted,side)==actor
        future=copy.deepcopy(replay)
        for f in future['frames'][branch+1:]:f.update(board='x'*64,move='a1a1')
        assert prefix(future,branch)==p
        game=run(p,commands,directory,len(moves)-branch)
        assert not game.get('failedSide') and not game.get('warnings'),game['reason']
        assert [f['move'] for f in game['frames']]==[f['move'] for f in replay['frames']]
        assert game['frames'][branch]['clocks']==p['frames'][-1]['clocks']
        assert all(g[k]==f[k] for g,f in zip(game['frames'],replay['frames']) for k in ('board','white','black'))
        assert all(any(e['op']=='freeze' for e in c['events']) for c in game['localTurnControl']['controls'])
        if name=='threefold':
            assert game['result']=='1/2-1/2' and game['reason']=='Threefold repetition'
            ref=referee();b=ref.FowBoard(p['frames'][-1]['board'] if False else validate_prefix(p)['fen'])
            reps=Counter({ref.position_key(b):1})
            for move in moves[branch:]:b.push_uci(move);reps[ref.position_key(b)]+=1
            assert ref.outcome(b,reps) is None, 'FEN-only control must lose the prior repetition'
        else:
            assert game['censored'] and game['result']=='*'
        (directory/'replay.json').write_text(json.dumps(game,indent=2)+'\n')
        reports.append(dict(fixture=name,passed=True,result=game['result'],reason=game['reason'],
            prefix_clocks_exact=True,all_frames_match=True,privacy_projection=True,
            replay_sha256=sha(directory/'replay.json')))

    # The actual engine consumes only own forced moves and exact own post clocks.
    p=prefix(synthetic(fixtures[0][1]),4)
    engine=[]
    for side in (0,1):
        a=actor_prefix(p,side)
        feed=['fow',f"{('w','b')[side]} 180 2"]
        for ply,f in enumerate(p['frames']):
            feed.append(f[('white','black')[side]])
            if ply<4 and ply%2==side:feed.append(str(f['clocks'][side]))
        env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
        env.update(MIST_FORCE_MOVES=','.join(a['moves']),ASTRA_PREFIX_CONTINUE='1',
            ASTRA_PREFIX_CLOCKS=','.join(map(str,a['post_clocks'])),MIST_MAX_SECONDS='1',FOW_SEED='241')
        proc=subprocess.run([str(HERE/'build/mist')],input='\n'.join(feed)+'\n',capture_output=True,text=True,env=env,timeout=30)
        assert proc.returncode==0
        assert proc.stdout.splitlines()==['ready',*['move '+m for m in a['moves']]]
        parsed=[float(x) for x in re.findall(r'astra-prefix: decision=\d+ clock=([\d.]+)',proc.stderr)]
        assert parsed==a['post_clocks']
        (OUT/f'preflight-engine-{side}.stderr').write_text(proc.stderr)
        engine.append(dict(side=side,exit=proc.returncode,forced_moves=len(a['moves']),clocks_exact=True))
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,fixtures=reports,engine=engine,
        source_sha256=sha(__file__),referee_sha256=sha(REF),binary_sha256=sha(HERE/'build/mist'),
        scope='Synthetic restoration fixtures and real-engine forced-clock handling. No strength, speed or exact historical belief-state claim.')
    (OUT/'preflight.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
