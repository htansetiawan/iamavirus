"""Restore permitted prefixes through the unmodified course referee runner.

The environment owns the real board. Each bot gets only its observations,
earlier own actions, and own clocks. Recorded moves stop exactly at the branch.
"""
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REF = ROOT.parent / 'fow-starter/referee.py'
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from local_turn_control import run_controlled


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def referee():
    spec = importlib.util.spec_from_file_location('continuation_referee', REF)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    return ref


def prefix(replay, ply):
    assert 0 <= ply < len(replay['frames'])
    return dict(id=replay['id'], timeControl=copy.deepcopy(replay['timeControl']),
                frames=copy.deepcopy(replay['frames'][:ply+1]), branch_ply=ply)


def actor_prefix(p, side):
    key = ('white', 'black')[side]
    frames = p['frames']
    return dict(side=key, views=[f[key] for f in frames],
        moves=[frames[i+1]['move'] for i in range(side,p['branch_ply'],2)],
        clocks=[frames[i]['clocks'][side] for i in range(side,p['branch_ply'],2)],
        post_clocks=[frames[i+1]['clocks'][side] for i in range(side,p['branch_ply'],2)],
        branch_clock=frames[-1]['clocks'][side], timeControl=p['timeControl'])


def validate_prefix(p):
    ref=referee();b=ref.FowBoard();reps=Counter({ref.position_key(b):1})
    for ply,f in enumerate(p['frames']):
        if ply:
            assert not ref.outcome(b,reps), 'terminal before branch'
            assert f['move'] in {m.uci() for m in ref.fow_moves(b)}
            b.push_uci(f['move']);reps[ref.position_key(b)]+=1
        made=ref.make_frame(b,f['clocks'],f['move'])
        assert all(made[k]==f[k] for k in ('ply','board','white','black','move'))
    assert not ref.outcome(b,reps), 'branch is terminal'
    return dict(fen=b.fen(en_passant='fen'),halfmove=b.halfmove_clock,
        castling=int(b.clean_castling_rights()),ep=b.ep_square,
        repetitions=sorted([(repr(k),v) for k,v in reps.items()]),
        clocks=p['frames'][-1]['clocks'])


def run(p, commands, directory, continuation_plies=64):
    """Rebuild from start; substitute only historical elapsed times before branch."""
    ref=referee();state=validate_prefix(p);original=ref.Bot
    branch=p['branch_ply'];inc=p['timeControl']['incrementSeconds'];events=[]
    audit_views=[];started=time.monotonic()

    class PrefixBot(original):
        def observe(self, value, ply):
            side=0 if self.side else 1
            if ply<=branch:
                assert value==p['frames'][ply][('white','black')[side]]
                audit_views.append((side,ply,hashlib.sha256(value.encode()).hexdigest()))
            return super().observe(value,ply)

        def move(self, remaining):
            ply=self.timeline.ply;side=0 if self.side else 1
            if ply<=branch:
                assert abs(remaining-p['frames'][ply]['clocks'][side])<2e-6
            move,elapsed=super().move(remaining)
            event=dict(ply=ply,side=side,move=move,actual_elapsed=elapsed,reported_clock=remaining,
                       prefix=ply<branch)
            events.append(event)
            if ply<branch:
                assert move==p['frames'][ply+1]['move'], 'forced history diverged'
                restored=p['frames'][ply+1]['clocks'][side]
                other=1-side
                assert abs(p['frames'][ply]['clocks'][other]-p['frames'][ply+1]['clocks'][other])<2e-6
                historic_elapsed=remaining+inc-restored
                assert historic_elapsed>=-2e-6
                return move,historic_elapsed
            return move,elapsed

    ref.Bot=PrefixBot
    try:
        game=run_controlled(ref,*commands,registry_path=directory/'processes.json',retain_stderr=True,
            base=p['timeControl']['baseSeconds'],increment=inc,match_id='continuation-'+p['id'],
            white_name='v37-prefix',black_name='v37-prefix',max_plies=branch+continuation_plies)
    finally:
        ref.Bot=original
    game['continuation']=dict(source_game=p['id'],branch_ply=branch,restored_state=state,
        steps=events,prefix_observations=audit_views,wall_seconds=time.monotonic()-started,
        prefix_cpu_charged_seconds=sum(e['actual_elapsed'] for e in events if e['prefix']),
        continuation_charged_seconds=sum(e['actual_elapsed'] for e in events if not e['prefix']),
        historical_clock_policy='Recorded clocks replace elapsed time only before branch; actual referee timing thereafter.',
        policy_scope='v37 weights/search with continuation-only replay adapter. Forced replay skips historical searches; timed thinning and RNG state need not match the historical arena bot.')
    if game['reason']=='Move limit reached' and branch+continuation_plies<1000:
        game['censored']=True
        game.update(result='*',reason='Continuation horizon reached; censored, not a draw')
    else:
        game['censored']=False
    return game
