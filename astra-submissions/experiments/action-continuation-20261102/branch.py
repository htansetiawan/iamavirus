"""One explicit action intervention, followed by ordinary reconstructed policies.

The referee owns truth. Actor commands receive only their own historical moves
and clocks, plus the chosen actor's intervention. A measured proposal cost is
charged identically to all actions compared from the same prefix.
"""
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / 'private-continuation-20261102'
sys.path.insert(0, str(PRIOR))
import continuation as base
from build import BASE


def commands(prefix, action, charge, seed, binary=None):
    assert math.isfinite(charge) and 0 <= charge < prefix['frames'][-1]['clocks'][prefix['branch_ply'] % 2]
    actor = prefix['branch_ply'] % 2
    post = prefix['frames'][-1]['clocks'][actor] - charge + prefix['timeControl']['incrementSeconds']
    result = []
    for side in (0, 1):
        a = base.actor_prefix(prefix, side)
        moves = a['moves'] + ([action] if side == actor else [])
        clocks = a['post_clocks'] + ([post] if side == actor else [])
        result.append(['/usr/bin/env', f'FOW_SEED={seed+side}',
                       'MIST_FORCE_MOVES='+','.join(moves), 'ASTRA_PREFIX_CONTINUE=1',
                       'ASTRA_PREFIX_CLOCKS='+','.join(map(str, clocks)),
                       f'MIST_STOCKFISH={BASE/"bin/stockfish"}',
                       f'MIST_HISTORY_TABLE={BASE/"data/history.bin"}',
                       'MIST_MAX_SECONDS=10', str(binary or PRIOR/'build/mist')])
    return result


def run(prefix, actor_commands, action, charge, directory, max_plies=64):
    """Replay from the initial board, substituting only the intervention's cost."""
    assert math.isfinite(charge) and 0 <= charge < prefix['frames'][-1]['clocks'][prefix['branch_ply'] % 2]
    state = base.validate_prefix(prefix)
    ref = base.referee()
    board = ref.FowBoard(state['fen'])
    assert action in {m.uci() for m in ref.fow_moves(board)}, 'proposed action is illegal in environment'
    ply = prefix['branch_ply']
    original_factory = base.referee
    calls = []

    def factory():
        r = original_factory()
        original_bot = r.Bot

        class InterventionBot(original_bot):
            def move(self, remaining):
                move, elapsed = super().move(remaining)
                if self.timeline.ply == ply:
                    assert move == action, 'engine did not apply specified intervention'
                    calls.append(dict(ply=ply, side=0 if self.side else 1,
                                      action=move, actual_elapsed=elapsed, charged_elapsed=charge))
                    return move, charge
                return move, elapsed

        r.Bot = InterventionBot
        return r

    # Every job owns a process. This scoped factory is never shared by threads.
    base.referee = factory
    try:
        game = base.run(prefix, actor_commands, directory, max_plies)
    finally:
        base.referee = original_factory
    assert len(calls) == 1
    step = game['continuation']['steps'][ply]
    assert step['move'] == action and step['actual_elapsed'] == charge
    step['actual_elapsed'] = calls[0]['actual_elapsed']
    step['charged_elapsed'] = charge
    game['continuation']['intervention'] = calls[0]
    game['continuation']['historical_clock_policy'] += (
        ' The intervention uses the proposal run cost for every compared action; '
        'actual execution cost is retained separately. Subsequent moves use actual time.')
    game['continuation']['policy_scope'] += (
        ' The root action is externally specified from a permitted-input proposal. '
        'This is an action-conditional rollout, not a match or an exact live-process clone.')
    return game


def inspect(game, prefix, action, charge):
    sys.path.insert(0, str(ROOT))
    from learning import ingest
    states, errors = ingest.validate_replay(game)
    assert not errors, errors
    assert not game.get('failedSide') and not game.get('warnings') and not game['protocol']['truncated']
    frames = game['frames']; branch = prefix['branch_ply']; steps = game['continuation']['steps']
    assert len(steps) == len(frames)-1 and frames[branch+1]['move'] == action
    assert all(f[k] == prefix['frames'][i][k] for i, f in enumerate(frames[:branch+1])
               for k in ('move', 'board', 'white', 'black', 'clocks'))
    for i, step in enumerate(steps):
        side = i % 2
        assert step['move'] == frames[i+1]['move'] and step['ply'] == i and step['side'] == side
        assert abs(step['reported_clock'] - frames[i]['clocks'][side]) < 2e-6
        assert abs(frames[i+1]['clocks'][1-side] - frames[i]['clocks'][1-side]) < 2e-6
        if i >= branch:
            elapsed = charge if i == branch else step['actual_elapsed']
            assert abs(frames[i+1]['clocks'][side] - frames[i]['clocks'][side] + elapsed
                       - game['timeControl']['incrementSeconds']) < 2e-6
    for side, key in enumerate(('white', 'black')):
        last = max((s['ply'] for s in steps if s['side'] == side), default=-1)
        inputs = [e for e in game['protocol']['events'] if e['side'] == key and e['direction'] == 'input']
        views = [e for e in inputs if len(e['text']) == 64]
        assert [e['ply'] for e in views] == list(range(last+1))
        assert all(e['text'] == frames[e['ply']][key] for e in views)
        clocks = [e for e in inputs if len(e['text']) != 64 and e['text'] != 'fow'
                  and not e['text'].startswith(('w ', 'b '))]
        assert [e['ply'] for e in clocks] == list(range(side, last+1, 2))
        assert all(abs(float(e['text']) - frames[e['ply']]['clocks'][side]) < 2e-6 for e in clocks)
    if game['censored']:
        assert game['result'] == '*' and states[-1].outcome() is None
    else:
        assert states[-1].outcome() == (game['result'], game['reason'])
    return dict(passed=True, frames=len(frames), new_plies=len(frames)-1-branch,
                result=None if game['censored'] else game['result'], censored=game['censored'],
                root_action=action, common_charge=charge, root_post_clocks=frames[branch+1]['clocks'],
                wall_seconds=game['continuation']['wall_seconds'])
