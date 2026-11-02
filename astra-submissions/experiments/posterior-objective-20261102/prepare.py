from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from common import HERE, ROOT, OUT, BASE, HISTORY, sha


def main():
    os.sched_setaffinity(0, {2, 3})
    OUT.mkdir(exist_ok=False); (HERE / 'build').mkdir(exist_ok=False)
    old = ROOT / 'astra-submissions/analysis'
    excluded = set(); sequences = set()
    for name in ('interaction-prior-20261102/plan.json', 'full-prior-posterior-20261102/plan.json',
                 'deployed-prior-comparison-20261102/plan.json', 'fresh-taxonomy-20261101/cases.json'):
        data = json.loads((old / name).read_text())
        excluded.update(r['game'] for r in data.get('games', data.get('cases', [])))
    for gid in excluded:
        replay = json.loads((ROOT / 'data/raw/games' / gid / 'replay.json').read_text())
        sequences.add(hashlib.sha256(' '.join(f['move'] for f in replay['frames'][1:]).encode()).hexdigest())
    accepted = ROOT / 'data/raw/accepted.jsonl'
    index = {r['id']: r for r in map(json.loads, accepted.read_text().splitlines())}
    teams = {'Greek Gift', 'Knight Vision', 'Strongly Invisible', 'Decent Chess Bot',
             'Crimson Fog', 'Instructors', 'Mist Opportunities', 'duck', 'HYPOTHERMIA'}
    candidates = [r for r in index.values() if '2026-11-01T10:00' <= (r.get('createdAt') or '') < '2026-11-01T20:00'
                  and 'IAmAVirus' in (r.get('white'), r.get('black'))
                  and any(r.get(k) in teams for k in ('white', 'black')) and r['id'] not in excluded]
    games = []
    for us, side in enumerate(('white', 'black')):
        rows = sorted((r for r in candidates if r[side] == 'IAmAVirus'),
                      key=lambda r: hashlib.sha256(('posterior230:' + r['id']).encode()).digest())
        n = 0
        for row in rows:
            path = ROOT / 'data/raw/games' / row['id'] / 'replay.json'
            replay = json.loads(path.read_text())
            signature = hashlib.sha256(' '.join(f['move'] for f in replay['frames'][1:]).encode()).hexdigest()
            if signature in sequences:
                continue
            sequences.add(signature)
            games.append(dict(game=row['id'], us=us, opponent=replay[('black', 'white')[us]],
                created_at=replay['createdAt'], replay_sha256=sha(path), sequence_sha256=signature))
            n += 1
            if n == 12:
                break
        assert n == 12, (side, n)
    command = ['gcc', '-O3', '-std=c11', '-shared', '-fPIC', '-pthread', '-I' + str(BASE),
               str(HERE / 'bridge.c'), str(BASE / 'board.c'), str(BASE / 'movemodel.c'), '-lm',
               '-o', str(HERE / 'build/bridge.so')]
    build = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (OUT / 'build.log').write_text(build.stdout + build.stderr); build.check_returncode()
    test = subprocess.run([str(ROOT / '.venv/bin/python'), str(HERE / 'test_objective.py')],
                          capture_output=True, text=True, timeout=60)
    (OUT / 'preflight.stdout').write_text(test.stdout); (OUT / 'preflight.stderr').write_text(test.stderr)
    test.check_returncode()
    dependencies = list(HERE.glob('*.py')) + [HERE / 'bridge.c', HERE / 'README.md', HERE / 'build/bridge.so', HISTORY]
    dependencies += list(BASE.glob('*.[ch]')) + [ROOT / 'learning/rules.py', ROOT / 'learning/ingest.py']
    plan = dict(at=datetime.now(timezone.utc).isoformat(), games=games, excluded_ids=sorted(excluded),
        accepted_sha256=sha(accepted), dependencies={str(p): sha(p) for p in dependencies},
        cores=[2, 3], wall_seconds=1200, max_parents=256, stop_worlds=4096, max_bytes=256 * 1024**2,
        gate={'minimum_nontrivial_cases': 100, 'minimum_nontrivial_games': 12,
              'probability_tolerance': 5e-6, 'log_probability_tolerance': 5e-5, 'gradient_tolerance': 2e-6},
        scope='Exact-small-belief data/gradient feasibility only; no training or strength claim.')
    with (OUT / 'plan.json').open('x') as f:
        json.dump(plan, f, indent=2); f.write('\n')
    print(json.dumps({'games': len(games), 'plan_sha256': sha(OUT / 'plan.json'), 'preflight': json.loads(test.stdout)}))


if __name__ == '__main__':
    main()
