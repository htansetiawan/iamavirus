"""Replay the fixed compact prior through the ordinary v38 belief updater."""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
PRIVATE = ROOT/'data/astra-spool'/HERE.name
BUILD = PRIVATE/'build'
NATIVE = ANALYSIS/'compact-prior-native-20261110'
NATIVE_BUILD = PRIVATE.parent/'compact-prior-native-20261110'
TEACHER = ANALYSIS/'prospective-quiet-teacher-20261110'
SOURCE = PRIVATE.parent/'prospective-quiet-teacher-20261110/cohort.json'
OLD = EXPERIMENTS/'quiet-prior-sequential-20261110'
sys.path.insert(0, str(OLD))
from prepare import BASE, NB, SEEDS, MoveList, inspect_game, load_ref, sha, save
import run as sequential

TEAMS = ('Instructors', 'duck', 'HYPOTHERMIA', 'Greek Gift', 'Knight Vision',
         'Strongly Invisible', 'Crimson Fog', 'Mist Opportunities')
PRIORITY = TEAMS[:3]
OWN = 'a2c35173659545c99752376a70418438'
ARMS = ('original', 'zero', 'learned')  # 'zero' is the feature-equivalent speed arm.
SALT = 'compact-sequential343:'


def read(path):
    return json.loads(Path(path).read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


def hash_pins(paths):
    return {str(p): sha(p) for p in sorted(set(paths))}


def compile_traces():
    previous = read(NATIVE/'result.json')
    receipt = read(NATIVE/'terminal-verification.json')
    assert previous['decision'] == 'sequential_design_allowed' and receipt['result_sha256'] == sha(NATIVE/'result.json')
    for name in ('movemodel.c', 'weights.h'):
        assert sha(NATIVE_BUILD/name) == previous['compiled_hashes'][name]
    base = BASE/'src'
    header = OLD/'build/guard_predicates.h'
    assert sha(header) == read(ANALYSIS/'quiet-prior-sequential-20261110/plan.json')['dependencies'][str(header)]
    source = (base/'belief.c').read_text()
    anchor = '#include "movemodel.h"'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '\n\nvoid compact_full_logp(const Position *, const MoveList *, Move, int, float *, float *);\nstatic int use_compact_prior;')
    anchor = '    const char *e;\n'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '''    if ((e = getenv("ASTRA_CAPTURE_FIXED"))) {
        if (strcmp(e, "2") == 0) use_compact_prior = 1;
        else if (strcmp(e, "1") != 0 && strcmp(e, "0") != 0) {
            fprintf(stderr, "invalid compact-prior comparison mode\\n");
            exit(2);
        }
    }
''')
    old = '''            move_logits(&p, &l, b->last_own, w->full, logit);
            float top = -INFINITY;
            for (int j = 0; j < l.count; ++j) if (logit[j] > top) top = logit[j];
            double z = 0;
            for (int j = 0; j < l.count; ++j) z += exp((double)(logit[j] - top));
            log_z = top + (float)log(z);'''
    assert source.count(old) == 1
    new = '''            if (w->full && use_compact_prior) {
                /* The full head returns log probabilities with the native
                 * global normalizer already applied. */
                compact_full_logp(&p, &l, b->last_own, 1, logit, NULL);
            } else {
'''+ '\n'.join('    '+line for line in old.splitlines()) + '\n            }'
    (BUILD/'belief.c').write_text(source.replace(old, new))
    common = ['gcc', '-O3', '-std=c11', '-pthread', '-ffp-contract=off', '-D_POSIX_C_SOURCE=199309L',
              '-I'+str(base), '-I'+str(header.parent), str(OLD/'trace.c'), str(base/'board.c')]
    commands = [common + [str(base/'belief.c'), str(base/'movemodel.c'), '-lm', '-o', str(BUILD/'trace-original')],
                common + [str(BUILD/'belief.c'), str(NATIVE_BUILD/'movemodel.c'), '-lm', '-o', str(BUILD/'trace-adapter')]]
    for command in commands:
        subprocess.run(command, check=True, timeout=60)
    paths = [*base.glob('*.[ch]'), *BUILD.iterdir(), header, NATIVE_BUILD/'movemodel.c', NATIVE_BUILD/'weights.h', BASE/'data/history.bin']
    return commands, paths


def select_games(ref, frontend):
    sealed = read(SOURCE)
    audited = read(TEACHER/'terminal-verification.json')
    prior = read(ANALYSIS/'compact-prior-holdout-20261110/plan.json')
    assert audited['cohort_sha256'] == sha(SOURCE)
    assert sealed['cutoff'] > prior['last'] and len(sealed['games']) == 300
    old_games = {g['game'] for g in read(ANALYSIS/'quiet-prior-sequential-20261110/plan.json')['games']}
    archive = Path(sealed['source_archive'])
    selected, considered = {}, []
    used = set()
    for team in TEAMS:
        chosen = []
        selected[team] = chosen
        candidates = [row for row in sealed['games'] if (row['white'] == team) ^ (row['black'] == team)]
        candidates.sort(key=lambda row: (OWN not in (row['white_id'], row['black_id']),
                                        hashlib.sha256((SALT+team+':'+row['sequence_sha256']).encode()).digest()))
        for row in candidates:
            game = row['game']
            if row['sequence_sha256'] in used or game in old_games:
                continue
            observer = int(row['white'] == team)
            raw = archive/'games'/game/'replay.json'
            assert sha(raw) == row['replay_sha256']
            replay = read(raw)
            assert replay['id'] == game and replay['rulesVersion'] == 'fow-v1'
            assert [frame['move'] for frame in replay['frames'][1:]] == row['moves']
            assert hashlib.sha256(' '.join(row['moves']).encode()).hexdigest() == row['sequence_sha256']
            lines, bad, frames = inspect_game(ref, frontend, replay, observer)
            considered.append(dict(game=game, team=team, observer=observer, unsupported_count=len(bad)))
            if bad:
                continue
            used.add(row['sequence_sha256'])
            trace = PRIVATE/(game+'.trace')
            trace.write_text('\n'.join(lines)+'\n')
            chosen.append(dict(game=game, team=team, observer=observer,
                               own_observer=row[('white_id', 'black_id')[observer]] == OWN,
                               sequence_sha256=row['sequence_sha256'], trace=str(trace), raw_path=str(raw),
                               frames=frames, rows=len(lines)-1, created_at=row['created_at']))
            if len(chosen) == 8:
                break
        assert len(chosen) == 8, (team, len(chosen))
    games = [selected[team][i] for i in range(8) for team in TEAMS]
    assert len(games)==64 and sum(g['own_observer'] for g in games)>=8
    return games, considered


def test_adapter(ref, frontend):
    board = ref.FowBoard()
    opening = ('e2e4', 'd7d5', 'e4e5', 'f7f5', 'e5f6', 'b8c6', 'g1f3', 'e7e6')
    frames = []
    for ply in range(len(opening)+1):
        text = opening[ply-1] if ply else None
        if text is not None:
            move = ref.chess.Move.from_uci(text)
            assert move in ref.fow_moves(board)
            board.push(move)
        frames.append(dict(ply=ply, move=text,
                           board=''.join(p.symbol() if (p := board.piece_at(s)) else '-' for s in range(64)),
                           white=ref.observation(board, True), black=ref.observation(board, False)))
    calls = updates = learned_signatures_changed = 0
    for observer in (0, 1):
        lines, unsupported, _ = inspect_game(ref, frontend, dict(id='compact0', frames=frames), observer)
        assert not unsupported
        trace = PRIVATE/f'fixture-{observer}.trace'
        trace.write_text('\n'.join(lines)+'\n')
        for seed in SEEDS:
            records = {}
            for arm in ARMS:
                path = BUILD/('trace-original' if arm=='original' else 'trace-adapter')
                result = subprocess.run([str(path), str(trace), str(seed)], env=sequential.environment(arm),
                                        capture_output=True, text=True, timeout=20, check=True)
                rows = [json.loads(line) for line in result.stdout.splitlines()]
                assert len(rows)==len(opening)-1 and all(row['matches'] and not row['guard_bad_moves'] for row in rows)
                records[arm] = rows
                calls += 1
                updates += len(rows)
            assert sequential.stable(records['original']) == sequential.stable(records['zero'])
            learned_signatures_changed += sum(a['signature']!=b['signature'] for a,b in zip(records['zero'], records['learned']))
    assert learned_signatures_changed
    return dict(calls=calls, updates=updates, learned_signatures_changed=learned_signatures_changed, exact_control=True)


def prepare():
    assert not OUT.exists() and not PRIVATE.exists()
    OUT.mkdir(); PRIVATE.mkdir(); BUILD.mkdir()
    commands, sources = compile_traces()
    ref = load_ref()
    frontend = ctypes.CDLL(str(NB/'adapter.so'))
    frontend.fow_init()
    frontend.view_moves.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(MoveList)]
    preflight = test_adapter(ref, frontend)
    games, considered = select_games(ref, frontend)
    jobs = []
    for i, game in enumerate(games):
        for seed in (i%2, (i+1)%2):
            offset = (i+seed)%3
            order = ARMS[offset:]+ARMS[:offset]
            if (i//3+seed)%2:
                order = order[::-1]
            for arm in order:
                jobs.append(dict(name=f"{game['game']}-s{seed}-{arm}", arm=arm, game=game['game'], seed_index=seed))
    assert len(jobs) == 384 and len({j['name'] for j in jobs})==384
    files = [Path(__file__), SOURCE, NB/'adapter.so', ROOT.parent/'fow-starter/referee.py', *sources,
             NATIVE/'plan.json', NATIVE/'result.json', NATIVE/'terminal-verification.json',
             TEACHER/'terminal-verification.json', ANALYSIS/'compact-prior-holdout-20261110/plan.json',
             ANALYSIS/'quiet-prior-sequential-20261110/plan.json', *(OLD/n for n in ('prepare.py','run.py','trace.c'))]
    files.extend(Path(row[key]) for row in games for key in ('trace','raw_path'))
    plan = dict(at=now(), games=games, jobs=jobs, teams=TEAMS, priority=PRIORITY, seeds=SEEDS,
                cores=[2,3], max_seconds=3600, max_child_bytes=3*1024**3, max_output_bytes=128*1024**2,
                child_seconds=120, bootstrap_draws=4000, seed=3431110,
                gate=dict(primary_min=3000, distinct_min=1500, gain=.15, large_games=6, full_updates=300,
                          priority_games=6, total_ratio=1.20, p95_floor=.10, p95_ratio=1.50,
                          risk_rows=500, positive_events=10, brier_tolerance=.002),
                dependencies=hash_pins(files),
                scope='64 later replays, fixed 200k cap and same two sampler states. Original v38 vs feature-equivalent speed-only vs speed-only plus fixed compact. No wall thinning, search, recovery after collapse or truth as actor input.')
    save(PRIVATE/'plan.json', plan)
    save(PRIVATE/'source-selection.json', dict(considered=considered, selected=games))
    summary = dict(at=now(), plan_sha256=sha(PRIVATE/'plan.json'), dependencies=len(plan['dependencies']),
                   source_sha256=sha(SOURCE), source_selection_sha256=sha(PRIVATE/'source-selection.json'),
                   trace_driver_sha256=sha(OLD/'trace.c'), source_frames=sum(g['frames'] for g in games),
                   own_observer=sum(g['own_observer'] for g in games), considered=len(considered),
                   unsupported=sum(bool(g['unsupported_count']) for g in considered),
                   games=len(games), jobs=len(jobs), strata=dict(Counter(g['team'] for g in games)),
                   gate=plan['gate'], max_seconds=plan['max_seconds'], cores=plan['cores'], preflight=preflight,
                   binary_sha256={name:sha(BUILD/name) for name in ('trace-original','trace-adapter')}, scope=plan['scope'])
    save(OUT/'plan-summary.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


def verify():
    plan, result, run = (read(PRIVATE/f) for f in ('plan.json','result.json','execution.json'))
    frozen = read(OUT/'plan-summary.json')
    assert run['status']=='complete' and result['plan_sha256']==frozen['plan_sha256']==sha(PRIVATE/'plan.json')
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    calls = read(PRIVATE/'calls.json')
    assert result['calls_sha256']==sha(PRIVATE/'calls.json') and len(calls)==len(plan['jobs'])
    assert [row['name'] for row in calls]==[job['name'] for job in plan['jobs']]
    cells = {}
    for call in calls:
        assert call['code']==0
        for suffix in ('stdout','stderr'):
            path = PRIVATE/(call['name']+'.'+suffix)
            assert sha(path)==call[suffix+'_sha256']
        cells[call['name']] = [json.loads(row) for row in (PRIVATE/(call['name']+'.stdout')).read_text().splitlines()]
    primary, full = [], []
    for game in plan['games']:
        for seed in range(len(plan['seeds'])):
            a,b,c = (cells[f"{game['game']}-s{seed}-{arm}"] for arm in ARMS)
            assert len(a)==len(b)==len(c)==game['rows']
            assert sequential.stable(a)==sequential.stable(b)
            for x,y,z in zip(a,b,c):
                assert all(r['ever_capped'] or r['matches'] for r in (x,y,z))
                if x['full_update']:
                    full.append((x['update_seconds'], y['update_seconds']))
                if x['decision'] and x['ply']>=16:
                    primary.append((game,x,z))
    nll = lambda rows, index: -math.fsum(math.log(max(r[index]['truth_share'], 1e-12)) for r in rows)/len(rows)
    assert len(primary)==result['primary']
    for arm,index in (('original',1),('learned',2)):
        assert abs(nll(primary,index)-result['mean_truth_nll'][arm])<1e-12
        assert sum(row[index]['matches']>0 for row in primary)==result['support'][arm]
    assert abs(nll(primary,1)-nll(primary,2)-result['gain'])<1e-12
    own = [r for r in primary if r[0]['own_observer']]
    report = dict(at=now(), passed=True, calls=len(calls), verified_rows=sum(map(len,cells.values())),
                  immutable_dependencies=len(plan['dependencies']), exact_control_rows=sum(len(cells[j['name']]) for j in plan['jobs'] if j['arm']=='zero'),
                  full_update_speed_ratio=math.fsum(pair[1] for pair in full)/math.fsum(pair[0] for pair in full),
                  full_update_count=len(full), own_observer=dict(games=len({r[0]['game'] for r in own}),
                                                               decisions=len(own), gain=nll(own,1)-nll(own,2)),
                  source_plan_sha256=sha(PRIVATE/'plan.json'), result_sha256=sha(PRIVATE/'result.json'),
                  scope='Raw hashes and exact-control trajectory equality; independent primary NLL and support reduction. Own observer subgroup is descriptive.')
    save(OUT/'result.json', result)
    save(OUT/'independent-review.json', report)
    print(json.dumps(report), flush=True)


def run():
    sequential.OUT, sequential.BUILD = PRIVATE, BUILD
    assert read(OUT/'plan-summary.json')['plan_sha256']==sha(PRIVATE/'plan.json')
    with lease(read(PRIVATE/'plan.json')['cores']):
        sequential.main()
        verify()


@contextmanager
def lease(cores):
    path = ROOT/'chatroom/cores.json'
    owner = 'astra-'+HERE.name
    def change(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=owner, cores=cores, pid=os.getpid(), at=now(),
                                                purpose='fixed compact sequential comparison and audit'))
            else:
                state['allocation'] = [row for row in state['allocation'] if row['owner']!=owner]
            state['updated'] = now()
            sequential.atomic(path, state)
    change(True)
    try:
        yield
    finally:
        change(False)


if __name__ == '__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
