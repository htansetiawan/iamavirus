"""Bounded offline producer experiment: fresh prefixes vs persistent replay.

Queries return teacher targets BEFORE receiving the recorded continuation move.
The actor receives only its observations, clocks and previously committed own
actions. No replay truth or future-move environment variable is supplied.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from run_engine_probe import check_target
from run_probe import HERE, ROOT, ARCHIVE, EXPECTED


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_once(text, old, new, count=1):
    if text.count(old) != count:
        raise RuntimeError('Archive hook changed: ' + old[:80])
    return text.replace(old, new)


def build(folder):
    if sha(ARCHIVE) != EXPECTED:
        raise RuntimeError('Pinned archive changed')
    with zipfile.ZipFile(ARCHIVE) as archive:
        archive.extractall(folder)
    names = ['teacher_targets.c', 'teacher_targets.h', 'teacher_dump.c',
             'teacher_dump.h', 'teacher_stream.c', 'teacher_stream.h']
    for name in names:
        shutil.copy2(HERE / name, folder / 'src' / name)
    path = folder / 'src/gtcfr.c'
    source = path.read_text()
    source = replace_once(source, '#include "cfr.h"', '#include "cfr.h"\n#include "teacher_dump.h"')
    anchor = '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
    source = replace_once(source, anchor,
        '    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n' + anchor)
    path.write_text(source)
    path = folder / 'src/main.c'
    source = path.read_text()
    source = replace_once(source, '#include <stdio.h>', '#include <stdio.h>\n#include "teacher_stream.h"')
    source = replace_once(source, '    const char *forced = getenv("MIST_FORCE_MOVES");',
        '    const char *forced = getenv("MIST_FORCE_MOVES");\n'
        '    const int astream = getenv("ASTRA_TEACHER_STREAM") != NULL;\n'
        '    char astra_forced[8] = "";\n'
        '    if (astream) forced = NULL;')
    anchor = '        char *end; const double reported = strtod(line, &end);'
    source = replace_once(source, anchor,
        '        if (astream && !astra_stream_line(line, sizeof line, astra_forced, &forced)) {\n'
        '            fprintf(stderr,"astra: invalid replay command\\n"); break;\n'
        '        }\n' + anchor)
    anchor = '        if (remaining < 20) { gp.samples = 32; gp.seconds = 0.3; }'
    source = replace_once(source, anchor, anchor + '\n'
        '        if (astream && !forced) {\n'
        '            gp.seconds = atof(getenv("ASTRA_TEACHER_SECONDS"));\n'
        '            if (!(gp.seconds > 0)) { fprintf(stderr,"astra: invalid budget\\n"); break; }\n'
        '            astra_stream_stamp(&b, views-1, "before");\n'
        '        }')
    anchor = '        printf("move %s\\n", uci); fflush(stdout);'
    source = replace_once(source, anchor, anchor + '\n'
        '        if (astream) {\n'
        '            astra_stream_stamp(&b, views-1, "after");\n'
        '            if (!astra_stream_commit(stdin, &allowed, &b, &r.move)) {\n'
        '                fprintf(stderr,"astra: missing or invalid continuation commit\\n"); break;\n'
        '            }\n'
        '        }')
    # Teacher compute is not elapsed historical thinking time. Give replay-only
    # clock accounting the same value in fresh and persistent reconstruction.
    # Real arena budgeting is unchanged when ASTRA_TEACHER_STREAM is absent.
    source = replace_once(source,
        'clock_left = reported - (now_seconds() - view_at) + increment;',
        'clock_left = astream ? reported + increment : reported - (now_seconds() - view_at) + increment;', 2)
    path.write_text(source)
    sources = [folder / 'src' / name for name in
               ['board.c', 'belief.c', 'movemodel.c', 'cfr.c', 'eval.c', 'search.c',
                'gtcfr.c', 'front.c', 'sfeval.c', 'main.c', 'teacher_targets.c',
                'teacher_dump.c', 'teacher_stream.c']]
    subprocess.run(['cc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L',
                    *map(str, sources), '-lm', '-o', str(folder / 'mist')],
                   check=True, timeout=60)
    (folder / 'bin/stockfish').chmod(0o755)
    return {'binary_sha256': sha(folder / 'mist'),
            'modified_source_sha256': {n: sha(folder / 'src' / n) for n in ['main.c', 'gtcfr.c']},
            'instrument_sha256': {n: sha(HERE / n) for n in names + ['run_stream_probe.py']}}


class PipeReader:
    def __init__(self, pipe):
        self.pipe, self.buffer = pipe, b''

    def line(self, deadline):
        while b'\n' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.pipe], [], [], remaining)[0]:
                raise TimeoutError('teacher protocol timed out')
            data = os.read(self.pipe.fileno(), 8192)
            if not data:
                raise RuntimeError('teacher exited before the expected protocol response')
            self.buffer += data
        line, self.buffer = self.buffer.split(b'\n', 1)
        return line.decode().strip()


def run_replay(source, replay_path, query_frames, seconds, deadline):
    replay = json.loads(replay_path.read_bytes())
    side = query_frames[0] % 2
    color = ('white', 'black')[side]
    assert query_frames == sorted(set(query_frames)) and all(p % 2 == side for p in query_frames)
    assert query_frames[-1] < len(replay['frames']) - 1
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_')) and k != 'FOW_SEED'}
    targets_path = source / 'targets.jsonl'
    targets_path.unlink(missing_ok=True)
    env.update(MIST_STOCKFISH=str(source / 'bin/stockfish'), MIST_HISTORY_TABLE=str(source / 'data/history.bin'),
               MIST_TEACHER_OUT=str(targets_path), MIST_MAX_SECONDS='10', MIST_CAP='200000',
               MIST_SF_WORKERS='2', FOW_SEED='20261025', ASTRA_TEACHER_STREAM='1',
               ASTRA_TEACHER_SECONDS=str(seconds))
    transcript = []
    history = []
    decisions = []
    started = time.monotonic()
    with tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen([str(source / 'mist')], cwd=source, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, bufsize=0)
        reader = PipeReader(process.stdout)

        def send(line):
            transcript.append({'input': line})
            process.stdin.write((line + '\n').encode())

        def receive_move():
            while True:
                line = reader.line(deadline)
                transcript.append({'output': line})
                if line.startswith('move '):
                    return line[5:]

        try:
            send('fow'); send(f'{"w" if side == 0 else "b"} 180 2')
            while True:
                line = reader.line(deadline)
                transcript.append({'output': line})
                if line == 'ready': break
            setup_seconds = time.monotonic() - started
            for ply, frame in enumerate(replay['frames'][:query_frames[-1] + 1]):
                assert frame['ply'] == ply
                send(frame[color]); history.append(['observation', ply, frame[color]])
                if ply % 2 != side: continue
                clock = frame['clocks'][side]
                history.append(['clock', ply, clock])
                if ply in query_frames:
                    began = time.monotonic()
                    send(str(clock))
                    move = receive_move()
                    targets = [json.loads(line) for line in targets_path.read_text().splitlines()]
                    assert len(targets) == len(decisions) + 1, 'missing/extra teacher export'
                    target = targets[-1]
                    check_target(target, move)
                    decisions.append({'frame': ply, 'teacher_move': move, 'target': target,
                                      'query_seconds': time.monotonic() - began,
                                      'actor_history_sha256': hashlib.sha256(json.dumps(history, separators=(',', ':')).encode()).hexdigest()})
                    # The current recorded action is intentionally sent only
                    # AFTER the proposal and completed target were received.
                    committed = replay['frames'][ply + 1]['move']
                    send('commit ' + committed)
                else:
                    committed = replay['frames'][ply + 1]['move']
                    send(f'play {committed} {clock}')
                    assert receive_move() == committed, 'historical action diverged'
                history.append(['own_move', ply, committed])
            process.stdin.close()
            process.wait(timeout=max(.001, deadline - time.monotonic()))
            if process.returncode: raise RuntimeError(f'engine exit {process.returncode}')
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            process.stdout.close()
            if not process.stdin.closed: process.stdin.close()
            stderr.seek(0); diagnostic = stderr.read().decode()
    assert 'mist: stockfish ready' in diagnostic
    assert 'astra: missing' not in diagnostic and 'astra: invalid' not in diagnostic
    stamps = re.findall(r'astra: stream (before|after) ply=(\d+) count=(\d+) hash=([0-9a-f]+)', diagnostic)
    assert len(stamps) == 2 * len(decisions)
    for i, decision in enumerate(decisions):
        before, after = stamps[2*i:2*i+2]
        assert before[0] == 'before' and after[0] == 'after' and before[1:] == after[1:]
        assert int(before[1]) == decision['frame']
        decision['belief_fingerprint'] = before[3]
        decision['belief_count'] = int(before[2])
        decision['belief_unchanged_by_query'] = True
    return {'replay': str(replay_path.relative_to(ROOT)), 'replay_sha256': sha(replay_path),
            'side': color, 'query_frames': query_frames, 'setup_seconds': setup_seconds,
            'wall_seconds': time.monotonic() - started, 'decisions': decisions,
            'transcript': transcript, 'stderr_tail': diagnostic.splitlines()[-10:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=.2)
    parser.add_argument('--wall-cap', type=float, default=180.)
    args = parser.parse_args()
    if not all(math.isfinite(x) and x > 0 for x in (args.seconds, args.wall_cap)):
        parser.error('budgets must be positive and finite')
    cases = [
        (ROOT / 'astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-fullclock-extra-20pairs-seed20261042-pair8-candidate-white.json', [46, 50, 54]),
        (ROOT / 'data/raw/games/5osaf68l/replay.json', [69, 73, 77]),
    ]
    results, failures = [], []
    with tempfile.TemporaryDirectory(prefix='astra-persistent-teacher-') as directory:
        source = Path(directory)
        provenance = build(source)
        started = time.monotonic(); deadline = started + args.wall_cap
        for index, (path, frames) in enumerate(cases):
            try:
                modes = ['fresh', 'persistent'] if index % 2 == 0 else ['persistent', 'fresh']
                runs = {}
                for mode in modes:
                    runs[mode] = ([run_replay(source, path, [frame], args.seconds, deadline) for frame in frames]
                                  if mode == 'fresh' else [run_replay(source, path, frames, args.seconds, deadline)])
                fresh = [r['decisions'][0] for r in runs['fresh']]
                persistent = runs['persistent'][0]['decisions']
                comparisons = []
                for a, b in zip(fresh, persistent):
                    same = {key: a[key] == b[key] for key in ['frame', 'actor_history_sha256', 'belief_count', 'belief_fingerprint']}
                    for key in ['samples', 'avoid_moves']:
                        same[key] = a['target'][key] == b['target'][key]
                    same['root_actions'] = [x['uci'] for x in a['target']['actions']] == [x['uci'] for x in b['target']['actions']]
                    comparisons.append({'frame': a['frame'], 'matches': same,
                                        'same_teacher_move': a['teacher_move'] == b['teacher_move']})
                fresh_seconds = sum(r['wall_seconds'] for r in runs['fresh'])
                reused_seconds = runs['persistent'][0]['wall_seconds']
                row = {'replay': str(path.relative_to(ROOT)), 'mode_order': modes,
                       'runs': runs, 'comparisons': comparisons,
                       'all_input_checks_passed': all(all(c['matches'].values()) for c in comparisons),
                       'fresh_seconds': fresh_seconds, 'persistent_seconds': reused_seconds,
                       'speedup': fresh_seconds / reused_seconds}
                results.append(row)
                print(f'{path.stem}: parity={row["all_input_checks_passed"]}, speedup={row["speedup"]:.2f}x', file=sys.stderr, flush=True)
                if not row['all_input_checks_passed']: break
            except (AssertionError, RuntimeError, TimeoutError, subprocess.TimeoutExpired, FileNotFoundError) as error:
                failures.append({'replay': str(path.relative_to(ROOT)), 'error': str(error)})
                break
    print(json.dumps({'classification': 'bounded offline producer correctness/timing experiment; no training or strength estimate',
                      'archive_sha256': EXPECTED, 'build': provenance, 'search_seconds': args.seconds,
                      'wall_cap_seconds_excluding_build': args.wall_cap, 'results': results, 'failures': failures,
                      'limits': ['Replay mode normalizes post-own clock accounting to reported time plus increment; arena mode is unchanged.',
                                 'Belief thinning still uses measured transition time; input checks detect mismatches on these cases only.',
                                 'Search is time-limited and Stockfish caches may be warm; output strategies need not be identical.',
                                 'Two games with three queries each are a producer pilot, not an arena-strength or corpus-wide speed estimate.']}, indent=2))
    return int(bool(failures) or len(results) != len(cases) or not all(r['all_input_checks_passed'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
