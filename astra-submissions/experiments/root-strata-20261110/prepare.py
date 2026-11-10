"""Build a frozen-population native diagnostic; no training or strength claims."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = HERE/'build'
OUT = ROOT/'astra-submissions/analysis/root-strata-20261110'
PRIOR = ROOT/'astra-submissions/analysis/root-population-20261110'
SOURCE = HERE.parent/'guard-controls-20261109/build/src'
SOURCES = ['board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr',
           'front', 'sfeval', 'teacher_targets', 'teacher_dump']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def population_input(population, path, budget=32):
    lines = [f"{population['count']} {population['us']} {budget} {len(population['moves'])}"]
    lines += [f"{m['uci']} {int(m.get('base_kept', True))}" for m in population['moves']]
    for w in population['worlds']:
        lines.append(f"{w['board']} {w['side']} {w['castle']} {w['ep']} "
                     f"{w['halfmove']} {w['hist']} {w['logw']:.17g}")
    path.write_text('\n'.join(lines)+'\n')


def command(mode, path, seed=2851000, binary=None):
    return [str(binary or BUILD/'driver'), mode, str(path), str(seed)]


def describe(path, seed=2851000, binary=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
    env['MIST_MODEL_TEMP'] = '2'
    result = subprocess.run(command('describe', path, seed, binary), capture_output=True, text=True,
                            env=env, timeout=15)
    assert result.returncode == 0, (result.returncode, result.stderr)
    return json.loads(result.stdout)


def synthetic(worlds, us, ep=None):
    """Native canonical moves come from the independent course rules here."""
    sys.path.insert(0, str(ROOT.parent/'fow-starter'))
    import referee as ref
    boards = []
    for placement in worlds:
        b = ref.FowBoard(None)
        for square, symbol in placement.items():
            b.set_piece_at(ref.chess.parse_square(square), ref.chess.Piece.from_symbol(symbol))
        b.turn = us == 0
        b.castling_rights = 0
        b.ep_square = None if ep is None else ref.chess.parse_square(ep)
        boards.append(b)
    output = dict(count=len(boards), us=us,
                  moves=[dict(uci=m.uci(), base_kept=True) for m in ref.fow_moves(boards[0])], worlds=[])
    for i, b in enumerate(boards):
        board = ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
        output['worlds'].append(dict(board=board, side=us, castle='0', ep=b.ep_square if b.ep_square is not None else -1,
                                     halfmove=0, hist=f'{i+1:016x}', logw=0))
    return output


def verify_sampling(pop, row):
    assert row['eligible'] and row['belief_unchanged']
    assert set(row['group_of']) == set(range(row['groups']))
    raw = [math.exp(w['logw']) for w in pop['worlds']]
    total = math.fsum(raw)
    expected = [math.fsum(raw[i] for i, g in enumerate(row['group_of']) if g == group)/total
                for group in range(row['groups'])]
    for got, want in zip(row['group_mass'], expected):
        assert abs(got-want) < 2e-9, (got, want)  # float log-weights round-trip in C
    for kind in ['ordinary_samples', 'stratified_samples']:
        samples = row[kind]
        assert len({w['index'] for w in samples}) == len(samples) <= row['budget']
        assert all(w['weight'] > 0 for w in samples)
        assert abs(math.fsum(w['weight'] for w in samples)-1) < 1e-12
    observed = [math.fsum(s['weight'] for s in row['stratified_samples'] if row['group_of'][s['index']] == group)
                for group in range(row['groups'])]
    assert max(abs(a-b) for a, b in zip(observed, row['group_mass'])) < 1e-12


def main():
    BUILD.mkdir(exist_ok=False)
    OUT.mkdir(exist_ok=False)
    shutil.copytree(SOURCE, BUILD/'src')
    gtcfr = BUILD/'src/gtcfr.c'
    source = gtcfr.read_text()
    anchor = 'const int K = belief_sample(b, draws, &draw_rng, idx, share);'
    assert source.count(anchor) == 1
    source = source.replace('#include "gtcfr.h"', '#include "gtcfr.h"\n#include "strata.h"')
    gtcfr.write_text(source.replace(anchor, 'const int K = astra_root_sample(b, draws, &draw_rng, idx, share);'))
    flags = ['gcc', '-std=c11', '-pthread', '-D_POSIX_C_SOURCE=199309L', '-I', str(BUILD/'src'), '-I', str(HERE)]
    inputs = [*[str(BUILD/'src'/f'{name}.c') for name in SOURCES], str(HERE/'strata.c'), str(HERE/'driver.c')]
    commands = []
    for name, options in [('driver', ['-O2', '-Wall', '-Wextra']),
                          ('driver-sanitize', ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
        cmd = [*flags, *options, *inputs, '-lm', '-o', str(BUILD/name)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr
        commands.append(dict(command=cmd, stderr=result.stderr))
    pop = json.loads((PRIOR/'case/population.json').read_text())
    population_input(pop, OUT/'population.txt')
    audit = json.loads((PRIOR/'audit.json').read_text())
    assert sha(PRIOR/'case/population.json') == audit['population_sha256']
    rows = []
    for seed in range(2851000, 2851032):
        row = describe(OUT/'population.txt', seed)
        verify_sampling(pop, row)
        assert row['groups'] == 6
        for got, old in zip(row['actions'], audit['risks']):
            assert got['uci'] == old['move'] and abs(got['loss']-old['sharpened']) < 2e-9
            assert abs(got['fitted_loss']-old['fitted']) < 2e-9
        kept = {m['uci'] for m in pop['moves']}-{*row['bounded_avoid']}
        assert kept == {'g7f6', 'g7h6', 'g7g8'}
        rows.append(row)
    write(OUT/'preflight-samples.json', rows)
    tests = dict(full_population_32_seeds=True, group_mass_exact=True,
                 risks_match_independent_prior_audit=True, interval_retains_three_king_choices=True)
    fixtures = []
    for budget in [1, 4]:
        path = OUT/f'overflow-{budget}.txt'
        population_input(pop, path, budget)
        row = describe(path)
        assert not row['eligible'] and row['reason'] == 'signature count exceeds sample budget'
        assert row['ordinary_samples'] == row['stratified_samples']
        assert row['bounded_avoid'] == row['old_avoid']
        fixtures.append(path)
    tests['overflow_preserves_original_sampler_and_mask'] = True
    queen = json.loads((PRIOR/'preflight/population.json').read_text())
    path = OUT/'queen-present.txt'; population_input(queen, path)
    row = describe(path)
    assert not row['eligible'] and row['reason'] == 'own queen present'
    assert row['ordinary_samples'] == row['stratified_samples'] and row['bounded_avoid'] == row['old_avoid']
    fixtures.append(path); tests['queen_present_fallback'] = True

    fixture = synthetic([{'a1': 'K', 'a4': 'R', 'a8': 'r', 'h4': 'k'}], 0)
    path = OUT/'king-capture-precedence.txt'; population_input(fixture, path)
    row = describe(path)
    capture = next(a for a in row['actions'] if a['uci'] == 'a4h4')
    assert row['eligible'] and capture['win'] == 1 and capture['loss'] == 0
    assert 'a4h4' not in row['bounded_avoid']
    fixtures.append(path); tests['king_capture_terminal_precedence'] = True

    fixture = synthetic([{'c5': 'K', 'e5': 'P', 'd5': 'p', 'h8': 'k'}]*2, 0, 'd6')
    fixture['worlds'][1]['ep'] = -1
    path = OUT/'ep-legality-differs.txt'; population_input(fixture, path)
    row = describe(path)
    assert not row['eligible'] and row['reason'] == 'legal move sets differ'
    assert row['ordinary_samples'] == row['stratified_samples'] and row['bounded_avoid'] == row['old_avoid']
    fixtures.append(path); tests['ep_ambiguity_fallback'] = True

    for path in [OUT/'population.txt', *fixtures]:
        sanitized = describe(path, binary=BUILD/'driver-sanitize')
        assert sanitized['belief_unchanged']
    tests['address_and_undefined_sanitizers'] = True
    write(OUT/'preflight.json', dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                                   tests=tests, commands=commands,
                                   median_census_seconds=sorted(r['census_seconds'] for r in rows)[len(rows)//2]))
    deps = [Path(__file__), HERE/'strata.c', HERE/'strata.h', HERE/'driver.c', HERE/'run.py', HERE/'audit.py',
            BUILD/'driver', *[p for p in (BUILD/'src').iterdir() if p.is_file()],
            PRIOR/'case/population.json', PRIOR/'audit.json', OUT/'population.txt',
            SOURCE.parent/'bin/stockfish', ROOT.parent/'fow-starter/referee.py']
    write(OUT/'plan.json', dict(at=datetime.now(timezone.utc).isoformat(),
          source_census_sha256=sha(PRIOR/'case/population.json'),
          seeds=list(range(2851100, 2851104)), seconds_per_arm=2.5, process_seconds=45, total_seconds=190,
          cores=[0, 1], samples=32, dependencies={str(p): sha(p) for p in deps},
          arms=['ordinary-old', 'stratified-old', 'ordinary-bounded', 'stratified-bounded'],
          criteria='All four seeds complete without failure; immutable belief/history hashes; exact full-belief '
                   'tactical risks in stratified chances; correct root masks and independent rule checks. '
                   'Report every move/value/Q without selecting a winning seed. Any error stops the study.',
          scope='Four-arm native GT-CFR diagnostic on one already-selected frozen population, not strength. '
                'Each arm has a fresh v38 scorer. Equal search time, census cost measured separately. '
                'No reconstruction, truth input, model fit, new games, candidate ZIP, version or promotion. '
                'No discarded probability mass; unsupported inputs preserve original sampler/pruning.'))
    print(json.dumps(dict(prepared=True, tests=tests, dependencies=len(deps))), flush=True)


if __name__ == '__main__':
    main()
