"""Freeze and review the completed own-team stage of the original daily refresh.

Reuses existing rules, taxonomy and material diagnostics. No network, fitting,
bot search, new games, shared raw writes, split assignment or deployment.
"""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/daily-own-cohort-20261111'
STORE = ROOT / 'data/astra-spool/daily-own-cohort-20261111'
RAW = ROOT / 'data/raw'
OURS = 'a2c35173659545c99752376a70418438'
PRIOR = ROOT / 'astra-submissions/analysis/training-artifact-readiness-20261111/plan.json'
LOG = ROOT / 'data/logs/daily/2026-11-11.log'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    with path.open('x') as stream:
        stream.write(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prepare():
    # Check the unchanged previous journal prefix, rather than infer novelty
    # from mutable mtimes or look at the cohort's results to choose its members.
    old = read(PRIOR)['journal']
    with (RAW / '.writer.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        with (RAW / 'accepted.jsonl').open('rb') as stream:
            assert hashlib.sha256(stream.read(old['bytes'])).hexdigest() == old['sha256']
            suffix = b''.join(stream.readline() for _ in range(30))
        fcntl.flock(lock, fcntl.LOCK_UN)
    rows = [json.loads(line) for line in suffix.splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == 30
    assert all(OURS in (r['whitePlayerId'], r['blackPlayerId']) for r in rows)
    log = LOG.read_bytes()
    start = log.index(b'== 10:04:33 ingest ours\n')
    end = log.index(b'== 10:05:43 ingest all teams\n')
    stage = log[start:end]
    assert b"'accepted': 30" in stage and b"'errors': 0" in stage
    OUT.mkdir(exist_ok=False)
    STORE.mkdir(exist_ok=False)
    (STORE / 'journal-tail.jsonl').write_bytes(suffix)
    (STORE / 'own-stage.log').write_bytes(stage)
    listing, hashes, fetch_times = [], {}, []
    for row in rows:
        target = STORE / 'games' / row['id']
        target.mkdir(parents=True)
        for name in ('listing.json', 'replay.json', 'fetch_metadata.json'):
            source = RAW / 'games' / row['id'] / name
            payload = source.read_bytes()
            (target / name).write_bytes(payload)
            hashes[str((target / name).relative_to(ROOT))] = hashlib.sha256(payload).hexdigest()
        meta = read(target / 'fetch_metadata.json')['replay']
        fetched = datetime.fromisoformat(meta['fetched_at'])
        assert datetime.fromisoformat('2026-11-11T10:04:33+00:00') <= fetched < datetime.fromisoformat('2026-11-11T10:05:43+00:00')
        assert meta['status'] == 200 and meta['url'].endswith('/api/games/' + row['id'])
        assert sha(target / 'replay.json') == meta['sha256']
        current = read(target / 'listing.json')
        assert all(current[k] == row[k] for k in ('id', 'whitePlayerId', 'blackPlayerId', 'whiteVersion', 'blackVersion', 'result', 'reason', 'plies', 'createdAt'))
        listing.append(current)
        fetch_times.append(meta['fetched_at'])
    save(STORE / 'listing.json', listing)
    save(STORE / 'journal-rows.json', rows)
    sources = [Path(__file__), PRIOR, ROOT / 'astra-submissions/tools/verify_field_replays.py',
               ROOT / 'astra-submissions/tools/field_taxonomy_report.py',
               ROOT / 'astra-submissions/tools/field_material_onsets.py',
               ROOT / 'astra-submissions/experiments/taxonomy-en-passant-20261111/baseline.py',
               ROOT / 'astra-submissions/experiments/taxonomy-en-passant-20261111/move_taxonomy.py',
               ROOT / 'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so',
               ROOT.parent / 'fow-starter/referee.py', ROOT / 'learning/ingest.py', ROOT / 'learning/rules.py',
               ROOT / 'learning/_native.py', STORE / 'listing.json', STORE / 'journal-rows.json',
               STORE / 'journal-tail.jsonl', STORE / 'own-stage.log']
    hashes.update({str(p): sha(p) for p in sources})
    plan = dict(at=now(), games=30, game_ids=[r['id'] for r in rows], core=6, wall_seconds=300,
                selection='All first 30 complete appended journal records after the unchanged 379 byte prefix. Every ID is our real team ID and its replay fetch is within the completed own-stage interval; all outcomes retained.',
                prior_journal=old, daily_invocation='1259dc943bb6484fa9cafeab41117926',
                fetch_min=min(fetch_times), fetch_max=max(fetch_times), dependencies=hashes,
                antecedents=['369 full replay validator', '370 EP-corrected taxonomy', '373 five-frame material onset', '379 frozen journal audit'],
                scope='Descriptive monitoring on exposed replay data, not a new candidate gate or untouched holdout. No fit, search, GPU, new game, split assignment, shared-report edit, commit, push or deployment.')
    save(OUT / 'plan.json', plan)
    print(json.dumps(dict(plan_sha256=sha(OUT / 'plan.json'), games=30, fetch_min=plan['fetch_min'], fetch_max=plan['fetch_max'])), flush=True)


def run():
    plan = read(OUT / 'plan.json')
    for p, digest in plan['dependencies'].items():
        assert sha(ROOT / p) == digest, p
    listing, journal = read(STORE / 'listing.json'), read(STORE / 'journal-rows.json')
    validator = load('daily_own_rules_review', ROOT / 'astra-submissions/tools/verify_field_replays.py')
    taxonomy = load('daily_own_taxonomy_review', ROOT / 'astra-submissions/tools/field_taxonomy_report.py')
    material = load('daily_own_material_review', ROOT / 'astra-submissions/tools/field_material_onsets.py')
    taxonomy.OWNER = 'astra-daily-own-cohort-20261111'
    ingest, referee = validator.load_rules()
    baseline, fixed = taxonomy.labelers()
    os.sched_setaffinity(0, {plan['core']})
    def timeout(*_):
        raise TimeoutError('daily own-cohort review reached its original wall limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan['wall_seconds'])
    began = time.monotonic()
    state = dict(at=now(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', state)
    rows, labels, material_rows = [], [], []
    try:
        with taxonomy.lease([plan['core']]):
            for meta, accepted in zip(listing, journal, strict=True):
                replay = read(STORE / 'games' / meta['id'] / 'replay.json')
                checked = validator.verify_game(replay, meta, ingest, referee)
                assert checked['sequence_sha256'] == accepted['moves_sha256']
                tagged, _, eps, changes = taxonomy.checked_labels(replay, baseline, fixed)
                side = 'white' if meta['whitePlayerId'] == OURS else 'black'
                other = 'black' if side == 'white' else 'white'
                outcome = 'draws' if meta['result'] == '1/2-1/2' else 'wins' if meta['result'] == ('1-0' if side == 'white' else '0-1') else 'losses'
                terminal = taxonomy.terminal_context(replay, meta, fixed)
                # The existing material scanner is explicitly scoped to v38.
                onset = material.scan(meta, replay, tagged, fixed) if meta[side + 'Version'] == 38 else None
                if onset is not None:
                    material_rows.append(onset)
                rows.append(dict(game=meta['id'], created_at=meta['createdAt'], side=side, version=meta[side + 'Version'],
                                 opponent_id=meta[other + 'PlayerId'], opponent=meta[other], opponent_version=meta[other + 'Version'],
                                 outcome=outcome, reason=meta['reason'], **checked, ep_captures=eps, ep_label_changes=len(changes),
                                 own_tags=tagged['counts'][side], terminal=terminal))
                labels.append(tagged)
        save(STORE / 'review-rows.json', rows)
        save(STORE / 'labels.json', labels)
        save(STORE / 'material-rows.json', material_rows)
        groups = defaultdict(list)
        for row in rows:
            groups[(row['version'], row['opponent_id'], row['opponent_version'], row['side'])].append(row)
        cells = []
        for (version, opponent_id, opponent_version, side), values in groups.items():
            counts = Counter(r['outcome'] for r in values)
            cells.append(dict(version=version, opponent_id=opponent_id, opponent=values[0]['opponent'],
                              opponent_version=opponent_version, side=side, games=len(values), **counts))
        cells.sort(key=lambda c: (c['version'], c['opponent'], c['opponent_version'], c['side']))
        terminal = [r['terminal'] for r in rows if r['outcome'] == 'losses' and r['terminal']]
        for p, digest in plan['dependencies'].items():
            assert sha(ROOT / p) == digest, p
        result = dict(at=now(), plan_sha256=sha(OUT / 'plan.json'), games=len(rows), frames=sum(r['frames'] for r in rows),
                      outcomes=dict(Counter(r['outcome'] for r in rows)), versions=dict(Counter(r['version'] for r in rows)),
                      unique_trajectories=len({r['sequence_sha256'] for r in rows}),
                      termination=dict(Counter(r['termination'] for r in rows)),
                      clock_flags=dict(sum((Counter(r['clocks']) for r in rows), Counter())),
                      cells=cells, ep_captures=sum(r['ep_captures'] for r in rows),
                      loss_terminal_mechanisms=dict(Counter(r['mechanism'] for r in terminal)),
                      loss_terminal_hidden=sum(r['any_attacker_hidden_in_decision_view'] for r in terminal),
                      material=material.summarize(material_rows),
                      material_by_outcome={outcome: material.summarize([r for r in material_rows if r['score'] == score]) for outcome, score in [('wins', 1), ('draws', .5), ('losses', 0)]},
                      artifacts={str(p.relative_to(ROOT)): sha(p) for p in (STORE / 'review-rows.json', STORE / 'labels.json', STORE / 'material-rows.json')},
                      scope=plan['scope'], limitations=['Thirty newly cached games are a scheduling-dependent descriptive cohort, not a randomized test.',
                      'Retrospective truth and tags are labels, not actor inputs or an automatic deployed-model update.',
                      'Material thresholds and terminal geometry do not prove the first mistake, a safe alternative or causal strength.',
                      'The full daily pipeline is still unverified until its original process terminates and outputs are checked.'])
        save(OUT / 'result.json', result)
        state.update(status='complete', completed=len(rows), result_sha256=sha(OUT / 'result.json'))
        print(json.dumps({k: result[k] for k in ('games', 'frames', 'outcomes', 'versions', 'termination', 'material', 'loss_terminal_mechanisms')}, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - began)
        temporary = OUT / 'execution.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(OUT / 'execution.json')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.command]()
