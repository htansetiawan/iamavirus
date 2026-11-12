"""Independent course enumeration, sampler replay and shared-root arithmetic."""
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
NAME = 'presentation-multistate-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME
BUILD = ROOT / 'astra-submissions/experiments/presentation-real-decision-20261111'


def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def close(a, b): assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), (a, b)


def main():
    plan = read(OUT / 'plan.json'); selection = read(OUT / 'selection.json')
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    assert selection['plan_sha256'] == sha(OUT / 'plan.json')
    assert selection['input_sha256'] == sha(STORE / 'input.txt')
    previous = read(ROOT / 'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    differences = {}
    for member, expected in previous['source_members'].items():
        control, traced = (BUILD / arm / member for arm in ('control', 'trace'))
        assert sha(control) == expected
        a, b = control.read_text().splitlines(), traced.read_text().splitlines()
        operations = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
        assert all(tag in ('equal', 'insert') for tag, *_ in operations)
        inserted = sum(end - start for tag, _, _, start, end in operations if tag == 'insert')
        if inserted: differences[Path(member).name] = inserted
    assert sorted(differences) == ['cfr.c', 'gtcfr.c', 'main.c']
    text, protocol = {}, {}
    for arm in ('probe', 'control', 'trace'):
        execution = read(OUT / (arm + '-execution.json'))
        assert execution['status'] == 'complete' and execution['code'] == 0
        assert execution['plan_sha256'] == sha(OUT / 'plan.json')
        for suffix in ('stdout', 'stderr'):
            assert sha(STORE / (arm + '.' + suffix)) == execution[suffix + '_sha256']
        text[arm] = (STORE / (arm + '.stderr')).read_text()
        protocol[arm] = (STORE / (arm + '.stdout')).read_text().splitlines()
        assert 'belief empty' not in text[arm] and 'thinned' not in text[arm] and '(capped)' not in text[arm]
        if arm != 'probe': assert 'mist: stockfish ready' in text[arm]
    counts = [int(s) for s in re.findall(r'mist: played \S+ risk [\d.]+ least [\d.]+ \|P\|=(\d+)', text['probe'])]
    assert counts == selection['observed_population_counts']
    eligible = [(2 * i, n) for i, n in enumerate(counts) if 2 * i >= plan['earliest_ply'] and plan['minimum_worlds'] <= n <= plan['maximum_worlds']]
    assert eligible[0] == (selection['selected_ply'], selection['selected_count'])
    replay_path = next(Path(p) for p in plan['dependencies'] if p.endswith('/c8ozqj0m.json'))
    replay = read(replay_path); frames = replay['frames']; ply = selection['selected_ply']
    expected_input = ['fow', 'w 180 2', frames[0]['white'], str(frames[0]['clocks'][0])]
    for p in range(2, ply + 1, 2):
        expected_input += [frames[p - 1]['white'], frames[p]['white'], str(frames[p]['clocks'][0])]
    assert (STORE / 'input.txt').read_text().splitlines() == expected_input
    assert selection['forced'] == [frames[p + 1]['move'] for p in range(0, ply, 2)]
    for arm in ('control', 'trace'):
        assert protocol[arm][:-1] == ['ready'] + ['move ' + m for m in selection['forced']]
    rows = [json.loads(line[7:]) for line in text['trace'].splitlines() if line.startswith('@astra ')]
    grouped = defaultdict(list)
    for row in rows: grouped[row['kind']].append(row)
    assert len(grouped['belief']) == 1
    belief = grouped['belief'][0]; worlds = grouped['world']; samples = grouped['sample']
    assert belief['count'] == selection['selected_count'] == len(worlds) and not belief['overflowed']
    assert [w['index'] for w in worlds] == list(range(len(worlds)))
    assert all(w['view'] == frames[ply]['white'] for w in worlds)
    cumulative, total = [], 0.0
    for world in worlds:
        total += math.exp(world['logw']); cumulative.append(total)
    for world in worlds: close(world['weight'], math.exp(world['logw']) / total)
    close(sum(w['weight'] for w in worlds), 1)
    # Independent SplitMix64 plus inverse CDF: replay all 32 native draws.
    mask = (1 << 64) - 1
    state = (plan['seed'] + selection['decision'] - 1) ^ 0x5eed
    draws, uniforms = [], []
    for _ in range(32):
        state = (state + 0x9E3779B97F4A7C15) & mask
        value = ((state ^ (state >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        value ^= value >> 31
        uniform = ((value >> 11) + .5) / (1 << 53)
        uniforms.append(uniform); draws.append(bisect_left(cumulative, uniform * total))
    draw_counts = Counter(draws)
    assert [s['index'] for s in samples] == sorted(draw_counts)
    for sample in samples:
        assert sample['requested'] == 32 and sample['distinct'] == len(samples)
        close(sample['chance_weight'], draw_counts[sample['index']] / 32)
    close(sum(s['chance_weight'] for s in samples), 1)
    # Enumerate complete course positions; compare the native position projection.
    # Its key omits halfmove clock, so retain all counters until after enumeration.
    referee_path = next(Path(p) for p in previous['dependencies'] if p.endswith('/fow-starter/referee.py'))
    assert sha(referee_path) == previous['dependencies'][str(referee_path)]
    spec = importlib.util.spec_from_file_location('multistate_course_referee', referee_path)
    referee = importlib.util.module_from_spec(spec); spec.loader.exec_module(referee)
    def board_string(board): return ''.join(p.symbol() if (p := board.piece_at(s)) else '-' for s in range(64))
    def position(board): return (board_string(board), 0 if board.turn else 1, int(board.castling_rights), board.ep_square if board.ep_square is not None else -1)
    def fullkey(board): return position(board) + (board.halfmove_clock,)
    states = [referee.FowBoard()]; population_counts, complete_counts = [1], [1]
    for p in range(1, ply + 1):
        following = {}
        for board in states:
            options = referee.fow_moves(board)
            for move in options:
                if board.turn and move.uci() != frames[p]['move']: continue
                child = board.copy(stack=False); child.push(move)
                king = child.king(not child.turn)
                if king is None or child.is_attacked_by(child.turn, king): continue
                if referee.observation(child, True) != frames[p]['white']: continue
                following[fullkey(child)] = child
        states = list(following.values())
        assert len(states) <= 20000, 'teaching enumeration exceeded its fixed small-prefix bound'
        population_counts.append(len({position(b) for b in states})); complete_counts.append(len(states))
    clocks_by_position = defaultdict(set)
    for board in states: clocks_by_position[position(board)].add(board.halfmove_clock)
    native = {(w['board'], w['side'], w['castle'], w['ep']) for w in worlds}
    assert native == set(clocks_by_position)
    for world in worlds:
        assert world['halfmove'] in clocks_by_position[(world['board'], world['side'], world['castle'], world['ep'])]
    transitions = [int(after) for _, _, after in re.findall(r'mist: timing (own|opp) update [\d.]+ s \|P\| (\d+) -> (\d+)', text['trace'])]
    assert transitions == population_counts[1:]
    guards = grouped['guard']; roots = sorted(grouped['root'], key=lambda r: r['action'])
    n = len(roots)
    assert [r['action'] for r in roots] == list(range(n)) and {r['root_infoset'] for r in roots} == {0}
    excluded = {g['move'] for g in guards if g['excluded']}
    low, sharp_low = min(g['combined'] for g in guards), min(g['combined_sharp'] for g in guards)
    for g in guards:
        close(g['combined'], g['king'] + .9 * g['queen'])
        close(g['combined_sharp'], g['king_sharp'] + .9 * g['queen_sharp'])
        assert bool(g['excluded']) == (g['combined'] > low + .02 or g['combined_sharp'] > sharp_low + .02)
    for board in states:
        legal = {m.uci() for m in referee.fow_moves(board)}
        assert {g['move'] for g in guards} == legal
        assert {r['move'] for r in roots} == legal - excluded
    children = {}
    # The pinned root builder calls build_children once per sampled index,
    # sequentially. Board strings alone can alias different EP/castling states.
    assert len(grouped['initial_child']) == n * len(samples)
    for k, sample in enumerate(samples):
        block = grouped['initial_child'][k * n:(k + 1) * n]
        assert all(child['board'] == worlds[sample['index']]['board'] for child in block)
        assert [child['action'] for child in block] == list(range(n))
        children[sample['index']] = block
    for child in grouped['initial_child']:
        assert child['sf_scored'] and child['frontier'] and child['matched_scores'] == n and not child['ranked_floor']
        close(child['utility'], math.tanh(child['sf_cp'] / 400))
    assert set(children) == set(draw_counts)
    for index, values in children.items():
        values.sort(key=lambda r: r['action'])
        assert [r['move'] for r in values] == [r['move'] for r in roots]
    values = [sum(sample['chance_weight'] * children[sample['index']][a]['utility'] for sample in samples) for a in range(n)]
    previous_update, means = None, []
    for iteration in (1, 2):
        updates = sorted([r for r in grouped['cfr_update'] if r['iteration'] == iteration], key=lambda r: r['action'])
        assert [r['action'] for r in updates] == list(range(n))
        positive = [max(r['regret_before'] + r['last_before'], 0) for r in updates]
        z = sum(positive); strategy = [p / z if z else 1 / n for p in positive]
        mean = sum(p * v for p, v in zip(strategy, values)); means.append(mean)
        for a, row in enumerate(updates):
            close(row['strategy'], strategy[a]); close(row['instantaneous'], values[a] - mean)
            if previous_update is not None:
                close(row['regret_before'], max(previous_update[a]['regret_before'] + previous_update[a]['instantaneous'], 0))
                close(row['last_before'], previous_update[a]['instantaneous'])
        previous_update = updates
    positive = [max(r['regret'] + r['last'], 0) for r in roots]; z = sum(positive)
    for row, p in zip(roots, positive): close(row['probability'], p / z if z else 1 / n)
    selected = max(roots, key=lambda r: r['probability'])
    assert [r['move'] for r in roots if r['selected']] == [selected['move']]
    assert protocol['trace'][-1] == 'move ' + selected['move']
    assert not any(r['owner'] == 'astra-' + NAME for r in read(ROOT / 'chatroom/cores.json')['allocation'])
    true_position = referee.FowBoard()
    for frame in frames[1:ply + 1]:
        move = true_position.parse_uci(frame['move'])
        assert move in referee.fow_moves(true_position)
        true_position.push(move)
        assert board_string(true_position) == frame['board']
    actual = [w for w in worlds if (w['board'], w['side'], w['castle'], w['ep']) == position(true_position)]
    assert len(actual) == 1
    selected_worlds = [dict(world=w['index'], belief_weight=w['weight'], draws=draw_counts[w['index']],
                            chance_weight=draw_counts[w['index']] / 32, board=w['board']) for w in worlds if w['index'] in draw_counts]
    result = dict(at=datetime.now(timezone.utc).isoformat(), status='complete', plan_sha256=sha(OUT / 'plan.json'),
                  reviewer_sha256=sha(Path(__file__)), source_annotation_lines=differences,
                  selected_ply=ply, population_counts=population_counts, complete_counter_state_counts=complete_counts,
                  projected_positions_with_multiple_counters=sum(len(v) > 1 for v in clocks_by_position.values()),
                  retained_worlds=len(worlds), distinct_piece_boards=len({w['board'] for w in worlds}),
                  draws=32, distinct_sampled_worlds=len(samples), sampled_worlds=selected_worlds,
                  draw_order=draws, draw_uniforms=uniforms,
                  unsampled_belief_mass=sum(w['weight'] for w in worlds if w['index'] not in draw_counts),
                  truth_index=actual[0]['index'], truth_belief_weight=actual[0]['weight'],
                  guard_actions=len(guards), excluded_moves=sorted(excluded), root_actions=n,
                  shared_root_infoset=0, initial_weighted_action_values=[dict(move=r['move'], value=v) for r, v in zip(roots, values)],
                  first_strategy_value=means[0], second_strategy_value=means[1], first_two_updates=grouped['cfr_update'],
                  initial_children=grouped['initial_child'], final_strategy=roots,
                  selected_move=selected['move'], recorded_arena_move=selection['recorded_move'],
                  same_as_control=protocol['trace'][-1] == protocol['control'][-1],
                  logs={arm: next(s for s in text[arm].splitlines() if s.startswith('mist: n=')) for arm in ('control', 'trace')},
                  checks=['Frozen source/binary/input/output hashes match; control source matches all19 archived members and trace contains output-only insertions.',
                          'Size-only selection and private-only prefix input reconcile to recorded views/clocks/own actions.',
                          'Course enumeration matches the complete native position projection and each retained counter has a consistent history.',
                          'All32 SplitMix64 and inverse-CDF draws reproduce exact indices/counts/chance shares.',
                          'Guard mask, legal action sets and all78 initial scored-child conversions reconcile.',
                          'First two shared-root CF updates reproduce sample-weighted utilities, baseline and clipped/predictive regrets.',
                          'Final normalized positive regret-plus-last probabilities and argmax match the emitted action; core lease released.'],
                  limitations=plan['limitations'] + ['Native deduplication keys exclude halfmove/repetition history; enumeration checks its position projection, not lossless game histories.',
                                                    'Correct weight arithmetic and this single truth join do not establish population calibration or full-game information-set completeness.'])
    with (OUT / 'result.json').open('x') as stream: stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'population_counts', 'complete_counter_state_counts', 'retained_worlds',
                     'distinct_sampled_worlds', 'sampled_worlds', 'unsampled_belief_mass', 'first_strategy_value', 'selected_move', 'recorded_arena_move')}, indent=2))


if __name__ == '__main__': main()
