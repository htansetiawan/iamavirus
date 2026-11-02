"""Freeze outcome-independent chronological games and all executable sources."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from config import HERE, ROOT, OUT, PREVIOUS, now, sha, unique


def signature(replay):
    return hashlib.sha256(' '.join(f['move'] for f in replay['frames'][1:]).encode()).hexdigest()


def main():
    os.sched_setaffinity(0, {2, 3})
    OUT.mkdir(exist_ok=False)
    previous = ROOT / 'astra-submissions/analysis'
    paths = [previous / name for name in (
        'interaction-prior-20261102/plan.json', 'full-prior-posterior-20261102/plan.json',
        'deployed-prior-comparison-20261102/plan.json', 'posterior-objective-20261102/plan.json',
        'fresh-taxonomy-20261101/cases.json')]
    excluded = set(); sequences = set()
    for path in paths:
        data = json.loads(path.read_text())
        excluded.update(r['game'] for r in data.get('games', data.get('cases', [])))
    for gid in sorted(excluded):
        replay = json.loads((ROOT / 'data/raw/games' / gid / 'replay.json').read_text())
        sequences.add(signature(replay))
    refresh = previous / 'arena-refresh-20261102-posterior-fit/execution.json'
    refresh_record = json.loads(refresh.read_text()); assert refresh_record['status'] == 'complete'
    snapshots = sorted((ROOT / 'data/raw/snapshots').glob('*/leaderboard.json'))
    snapshot = next(p for p in reversed(snapshots) if '2026-11-02T035' in str(p))
    cutoff = '2026-11-02T03:50:55'
    teams = {'Greek Gift', 'Knight Vision', 'Strongly Invisible', 'Decent Chess Bot',
             'Crimson Fog', 'Instructors', 'Mist Opportunities', 'duck', 'HYPOTHERMIA'}
    accepted = ROOT / 'data/raw/accepted.jsonl'
    index = {r['id']: r for r in map(json.loads, accepted.read_text().splitlines())}
    windows = [('train', '2026-10-20', '2026-11-01', 400),
               ('validation', '2026-11-01', '2026-11-01T20:00', 80),
               ('test', '2026-11-01T20:00', cutoff, 80)]
    games = []; inventory = {}
    for split, lower, upper, wanted in windows:
        candidates = [r for r in index.values() if lower <= (r.get('createdAt') or '') < upper
                      and r['id'] not in excluded and any(r.get(k) in teams for k in ('white', 'black'))]
        candidates.sort(key=lambda r: hashlib.sha256(('posterior231:' + r['id']).encode()).digest())
        chosen = []; duplicate = 0
        for row in candidates:
            path = ROOT / 'data/raw/games' / row['id'] / 'replay.json'
            replay = json.loads(path.read_text()); sig = signature(replay)
            if sig in sequences:
                duplicate += 1; continue
            sequences.add(sig)
            sides = [s for s, name in enumerate(('white', 'black')) if replay[name] in teams]
            salt = hashlib.sha256(('observer231:' + row['id']).encode()).digest()
            actor_side = sides[int.from_bytes(salt[:8], 'little') % len(sides)]
            chosen.append(dict(game=row['id'], us=1-actor_side, actor=replay[('white', 'black')[actor_side]],
                split=split, created_at=replay['createdAt'], replay_sha256=sha(path), sequence_sha256=sig,
                white=replay['white'], black=replay['black'],
                white_version=replay.get('whiteVersion'), black_version=replay.get('blackVersion')))
            if len(chosen) == wanted:
                break
        inventory[split] = dict(candidates=len(candidates), duplicate_sequences_skipped=duplicate, selected=len(chosen))
        assert len(chosen) == wanted if split != 'test' else len(chosen) >= 30, inventory
        games.extend(chosen)
    # A previous terminal-only preflight result was lost at context compaction.
    # Host process audit found no live invocation; this is an explicit verification repeat, not a fit.
    test = subprocess.run([str(ROOT / '.venv/bin/python'), str(HERE / 'test_model.py')],
                          capture_output=True, text=True, timeout=90)
    (OUT / 'preflight.stdout').write_text(test.stdout); (OUT / 'preflight.stderr').write_text(test.stderr)
    test.check_returncode()
    previous_plan = previous / 'posterior-objective-20261102/plan.json'
    dependencies = json.loads(previous_plan.read_text())['dependencies']
    dependencies.update(json.loads((previous / 'posterior-objective-20261102/reference-pins.json').read_text()))
    # 230's README gained result text after its original freeze; pin the executable dependencies.
    dependencies = {p: h for p, h in dependencies.items() if not p.endswith('README.md')}
    for path, expected in dependencies.items():
        assert sha(Path(path)) == expected, path
    for p in list(HERE.glob('*.py')) + [HERE / 'README.md', refresh, snapshot] + paths:
        dependencies[str(p)] = sha(p)
    plan = dict(at=now(), games=games, inventory=inventory, excluded_ids=sorted(excluded),
        accepted_sha256=sha(accepted), dependencies=dependencies, snapshot=str(snapshot), test_cutoff=cutoff,
        source_parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        seed=2311102, bootstrap_samples=2000, steps=60, learning_rate=.03, ridges=[.001, .01],
        train_cases_per_game=12, max_feature_bytes=2 * 1024**3, wall_seconds=2700, cores=[2, 3],
        validation_every=5, probability_floor=1e-12, max_parents=256, stop_worlds=4096,
        gate=dict(baseline_gain=.10, baseline_ci_lower=0., actor_comparator_gain=.05,
                  late_min_gain=-.02, surprise_min_gain=-.02, min_surprise=20,
                  all_min_gain=0., max_support_failures=0),
        scope='One-step posterior fit on uncapped exact prefixes; same incoming baseline weights for both objectives.',
        preflight=json.loads(test.stdout), preflight_repeat_reason='Prior terminal result unavailable; host audit found no live preflight.')
    unique(OUT / 'plan.json', plan)
    print(json.dumps({'plan_sha256': sha(OUT / 'plan.json'), 'inventory': inventory, 'preflight': plan['preflight']}), flush=True)


if __name__ == '__main__':
    main()
