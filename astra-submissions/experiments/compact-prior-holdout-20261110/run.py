"""Fixed hard-label checkpoint qualification on grouped replay data."""
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import signal
import sys
import time

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
SPOOL = ROOT/'data/astra-spool'
CACHE = SPOOL/'recovered-replay-cache-20261110'
FIT = ANALYSIS/'compact-quiet-student-20261110'
CONFIRM = ANALYSIS/'prospective-quiet-teacher-20261110'
EXPERIMENTS = HERE.parent
sys.path[:0] = [str(EXPERIMENTS/'prospective-quiet-teacher-20261110'),
                str(EXPERIMENTS/'compact-quiet-student-20261110')]
from protocol import PRIORITY, TEAMS, bootstrap, now, relevant, stamp_ns, write
from features import Producer, batch
from score import ScalarResidual, quiet_logp
from student import CompactQuietPrior
from reconstructed_cache import AFTER_EIGHT, CAPTURE, FATAL, Cache, decode_move, fields
from experience_index import unpack_view

MODELS = ('base', 'quadratic', 'production', 'hard')
OWNER = 'astra-'+HERE.name
SEQUENCE_EXCLUSIONS = (
    CONFIRM/'previous-exclusions.json',
    SPOOL/'prospective-quiet-teacher-20261110/cohort.json',
    ANALYSIS/'capture-fixed-prior-20261110/plan.json',
    SPOOL/'reconstructed-train-20261110/games.json',
)
CASE_EXCLUSIONS = (
    ANALYSIS/'priority-diagnosis-20261109/plan.json',
    ANALYSIS/'duck-v11-belief-20261110/plan.json',
    ANALYSIS/'duck-v11-matchup-20261110/result.json',
)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def select(games, omitted):
    excluded = set()
    for path in SEQUENCE_EXCLUSIONS:
        data = read(path)
        excluded.update(row['sequence_sha256'] for row in (data if isinstance(data, list) else data['games']))
    cases = set()
    for path in CASE_EXCLUSIONS:
        data = read(path)
        cases.update(row['game'] for row in data.get('cases', []))
        cases.update(data.get('source_replay_sha256', {}))
    excluded.update(row['sequence_sha256'] for row in (*games, *omitted) if row['game'] in cases)
    counts = Counter()
    selected = []
    for row in games:
        if row['split'] != 'test':
            continue
        counts['test'] += 1
        if row['metadata']['plies'] < 4 or not relevant(row['metadata']):
            counts['irrelevant_or_short'] += 1
        elif row['game'] in cases or row['sequence_sha256'] in excluded:
            counts['previously_used'] += 1
        else:
            selected.append(row)
    selected.sort(key=lambda row: (stamp_ns(row['metadata']['createdAt']), row['game']))
    assert len(selected) == len({row['sequence_sha256'] for row in selected})
    counts.update(eligible=len(selected), frames=sum(row['records'] for row in selected))
    ids = [row['sequence_sha256'] for row in selected]
    return selected, dict(counts), hashlib.sha256('\n'.join(ids).encode()).hexdigest()


def inventory(games):
    omitted = [json.loads(line) for line in (CACHE/'excluded.jsonl').read_text().splitlines()]
    return select(games, omitted)


def load_models(plan):
    models = {'quadratic': ScalarResidual('quadratic'), 'production': ScalarResidual('quadratic'),
              'hard': CompactQuietPrior(plan['rank'])}
    for key in ('quadratic', 'hard'):
        models[key].load_state_dict(torch.load(plan['weights'][key], map_location='cpu', weights_only=True))
    original = read(plan['weights']['production'])
    with torch.no_grad():
        models['production'].linear.copy_(torch.tensor(original['linear']))
        models['production'].quadratic.copy_(torch.tensor(original['quadratic']))
    return {key: value.eval() for key, value in models.items()}


def freeze():
    assert not (OUT/'plan.json').exists()
    fit, confirmed = read(FIT/'plan.json'), read(CONFIRM/'plan.json')
    result, review = read(FIT/'result.json'), read(FIT/'independent-review.json')
    verified = read(ANALYSIS/'recovered-replay-cache-20261110/terminal-verification.json')
    hard = SPOOL/'compact-quiet-student-20261110/hard.pt'
    assert review['passed'] and review['result_sha256'] == sha(FIT/'result.json')
    assert result['decision'] == 'close_student_configuration' and result['arms']['hard']['best_epoch'] == 8
    assert sha(hard) == result['arms']['hard']['checkpoint_sha256']
    assert sha(CACHE/'manifest.json') == verified['manifest_sha256'] and verified['reader_verified']
    weights = {key: confirmed['weights'][key] for key in ('quadratic', 'production')}
    assert all(sha(path) == confirmed['dependencies'][path] for path in weights.values())
    weights['hard'] = str(hard)
    chosen, counts, cohort_sha = inventory(read(CACHE/'games.json'))
    assert counts['eligible'] >= 800 and counts['frames'] <= 150_000
    deps = [Path(__file__), FIT/'plan.json', FIT/'result.json', FIT/'independent-review.json',
            CONFIRM/'plan.json', ANALYSIS/'recovered-replay-cache-20261110/terminal-verification.json',
            EXPERIMENTS/'compact-quiet-student-20261110/student.py',
            *map(Path, confirmed['dependencies']), *map(Path, weights.values()),
            *SEQUENCE_EXCLUSIONS, *CASE_EXCLUSIONS,
            *(CACHE/name for name in ('manifest.json', 'games.json', 'records.bin', 'excluded.jsonl'))]
    assert all(sha(path) == digest for path, digest in confirmed['dependencies'].items())
    plan = dict(at=now(), cohort_sha256=cohort_sha, counts=counts, first=chosen[0]['metadata']['createdAt'],
                last=chosen[-1]['metadata']['createdAt'], cache=str(CACHE), weights=weights, rank=fit['rank'],
                native_state_library=confirmed['native_state_library'], cores=[2, 3], max_seconds=900,
                batch=256, bootstrap_draws=4000, seed=3411110, scalar_stride=257,
                gates=dict(native_gain=.075, quadratic_gain=.03, primary_min=20_000,
                           surprise_min=100, priority_games_min=40, numeric_tolerance=.0001),
                torch_version=torch.__version__, torch_git=torch.version.git_version,
                scope='Retrospective, grouped Nov 9–10 held-out per-world action prediction. Fixed epoch-8 hard-label head; no refit, posterior inference or playing-strength comparison.',
                dependencies={str(path): sha(path) for path in sorted(set(deps))})
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json', plan, exclusive=True)
    print(json.dumps(dict(cohort=counts, pins=len(plan['dependencies']), plan_sha256=sha(OUT/'plan.json'))))


def packed_game(cache, row, all_seats=False):
    listing = row['metadata']
    items = [fields(cache.record(row['start']+i)) for i in range(row['records'])]
    moves = [decode_move(item[7]) for item in items[:-1]]
    assert len(moves) == listing['plies'] and items[-1][7] == 65535
    assert hashlib.sha256(' '.join(moves).encode()).hexdigest() == row['sequence_sha256']
    game = dict(game=row['game'], frames=row['records'], moves=moves)
    for side in ('white', 'black'):
        game.update({side: listing[side], side+'_id': listing[side+'PlayerId'],
                     side+'_version': listing[side+'Version']})
    game['selected_plies'] = [i for i in range(len(moves))
                              if all_seats or game[('white_id', 'black_id')[i%2]] in TEAMS]
    frames = []
    for i, item in enumerate(items):
        board = unpack_view(item[0])
        views = [''.join(piece if mask>>s&1 else '?' for s, piece in enumerate(board)) for mask in item[1:3]]
        assert item[6] == i%2
        frames.append(dict(ply=i, board=board, white=views[0], black=views[1], move=moves[i-1] if i else None))
    return game, {'frames': frames}, items


def contexts(producer, cache, row, all_seats=False):
    game, replay, items = packed_game(cache, row, all_seats)
    seen = []
    for inputs, meta in producer.game(game, replay):
        ply = meta['ply']
        full, white, black, castle, ep, half, side, move, selection, flags = items[ply]
        del full, white, black
        _, _, castling, en_passant, halfmove, actor = inputs['board']
        assert (producer.native.castle.value, producer.native.ep.value, int(halfmove), actor) == (castle, ep, half, side)
        assert sum(int(on)<<s for s, on in enumerate(castling)) == castle
        assert np.flatnonzero(en_passant).tolist() == ([] if ep == -1 else [ep])
        assert inputs['moves'][meta['target']] == move
        assert meta['capture'] == bool(flags&CAPTURE)
        assert meta['primary'] == (bool(selection&AFTER_EIGHT) and not flags&FATAL)
        assert meta['surprise'] == (bool(flags&CAPTURE) and replay['frames'][ply][('black', 'white')[side]][move&63]=='?')
        seen.append(ply)
        yield inputs, meta
    assert seen == game['selected_plies']


def scalar_hard(weights, row):
    """Float64 calculation independent of Torch embedding, batching and normalization."""
    piece, views, castle, ep, half, side = row['board']
    squares = np.arange(64)
    flip = 56*side
    order = squares ^ flip
    piece, views, castle, ep = (value[order] for value in (piece, views, castle, ep))
    if side:
        piece = np.where(piece, (piece+5)%12+1, 0)
        views = ((views&1)<<1) | (views>>1)
    context = weights['piece.weight'][13*squares+piece].sum(0)
    context += weights['visibility.weight'][4*squares+views].sum(0)
    context += weights['castling.weight'][castle.astype(bool)].sum(0)
    context += weights['en_passant.weight'][ep@(squares+1)]
    context += weights['halfmove.weight'][:, 0]*np.clip(half, 0, 100)/100 + weights['halfmove.bias']
    source = (row['moves']&63)^flip
    target = ((row['moves']>>6)&63)^flip
    query = weights['source.weight'][13*source+piece[source]] + weights['target.weight'][13*target+piece[target]]
    query += weights['promotion.weight'][row['moves']>>12] + row['x']@weights['move_features.weight'].T
    residual = query@np.clip(context, -1, 1) + (row['x']@weights['scalar.weight'].T)[:, 0]
    base = row['base'].astype(float)
    quiet = row['x'][:, 0] == 0
    adjusted = base-np.logaddexp.reduce(base)
    if quiet.sum() > 1:
        adjusted[quiet] += residual[quiet] + np.logaddexp.reduce(base[quiet]) - np.logaddexp.reduce((base+residual)[quiet])
    return native_history(adjusted, row), residual


def native_history(logp, row):
    total = float(row['history_n'])
    if total < 3:
        return logp
    with np.errstate(divide='ignore'):
        return np.logaddexp(np.log(row['counts'].astype(float)), np.log(4.)+logp)-np.log(total+4.)


class Scorer:
    def __init__(self, plan):
        self.producer = Producer(plan['native_state_library'])
        self.models = load_models(plan)
        self.weights = {key: value.numpy().astype(float) for key, value in self.models['hard'].state_dict().items()}
        self.control_weights = {'base': (np.zeros(22, np.float32), np.zeros((22, 22), np.float32))}
        for key in ('quadratic', 'production'):
            model = self.models[key]
            self.control_weights[key] = (model.linear.detach().numpy(), (model.quadratic*model.mask).detach().numpy())
        self.tolerance = plan['gates']['numeric_tolerance']
        self.stride = plan['scalar_stride']
        self.count = self.captures = self.scalar_contexts = 0
        self.native_error = self.scalar_error = self.residual_error = 0.

    @torch.no_grad()
    def score(self, rows, metadata):
        b = batch(rows)
        residuals = {'base': torch.zeros_like(b['base']), **{key: model(b) for key, model in self.models.items()}}
        values = {key: quiet_logp(b['base'], residual, b['valid'], b['capture'], b['counts'], b['history_n'])
                  for key, residual in residuals.items()}
        capture = b['valid'] & b['capture']
        self.captures += int(capture.sum())
        for logp in values.values():
            assert torch.equal(logp[capture], values['base'][capture])
            assert torch.isfinite(logp[b['valid']]).all()
        for i, (row, meta) in enumerate(zip(rows, metadata)):
            n = len(row['moves'])
            for key, (linear, quadratic) in self.control_weights.items():
                expected = np.empty(n, np.float32)
                self.producer.lib.quiet_logp(row['x'], row['base'], n, 22, linear, quadratic, expected)
                self.native_error = max(self.native_error, float(abs(native_history(expected.astype(float), row)-values[key][i, :n].numpy()).max()))
            if self.count % self.stride == 0:
                expected, residual = scalar_hard(self.weights, row)
                self.scalar_error = max(self.scalar_error, float(abs(expected-values['hard'][i, :n].numpy()).max()))
                self.residual_error = max(self.residual_error, float(abs(residual-residuals['hard'][i, :n].numpy()).max()))
                self.scalar_contexts += 1
            self.count += 1
            meta['logp'] = {key: float(values[key][i, meta['target']]) for key in MODELS}
        assert max(self.native_error, self.scalar_error, self.residual_error) < self.tolerance


def summarize(plan, rows):
    primary = np.array([row['primary'] for row in rows])
    capture = np.array([row['capture'] for row in rows])
    probability = {key: np.array([row['logp'][key] for row in rows]) for key in MODELS}
    assert primary.any() and (~capture & primary).any()
    selected = [row for row in rows if row['primary']]
    gain = {key: probability['hard']-probability[key] for key in MODELS[:-1]}

    def panel(team, version=None, per_version=False):
        take = primary & np.array([row['team_id']==team and (not per_version or row['version']==version) for row in rows])
        return dict(games=len({row['game'] for row, ok in zip(rows, take) if ok}), decisions=int(take.sum()),
                    gains={key: float(value[take].mean()) if take.any() else None for key, value in gain.items()})

    versions = {(row['team_id'], row['version']) for row in selected}
    metrics = dict(decisions=len(rows), primary=int(primary.sum()), primary_quiet=int((~capture & primary).sum()),
                   surprise_captures=sum(row['primary'] and row['surprise'] for row in rows),
                   capture_target_error=float(abs(gain['base'][capture]).max(initial=0)),
                   nll={key: float(value[primary].mean()*-1) for key, value in probability.items()},
                   gain={key: float(value[primary].mean()) for key, value in gain.items()},
                   quiet_gain={key: float(value[~capture & primary].mean()) for key, value in gain.items()},
                   interval95={key: bootstrap(selected, value[primary], plan['seed']+i, plan['bootstrap_draws'])
                               for i, (key, value) in enumerate(gain.items())},
                   all_move_gain=float(gain['base'].mean()), priority={TEAMS[team]: panel(team) for team in PRIORITY},
                   by_played_version=[dict(team=TEAMS[team], version=version, **panel(team, version, True))
                                      for team, version in sorted(versions, key=lambda p: (p[0], -1 if p[1] is None else p[1]))])
    g = plan['gates']
    conditions = dict(primary=metrics['primary']>=g['primary_min'], native_gain=metrics['gain']['base']>=g['native_gain'],
                      matched_quadratic_gain=metrics['gain']['quadratic']>=g['quadratic_gain'],
                      four_thousand_quadratic_gain=metrics['gain']['production']>=g['quadratic_gain'],
                      production_confidence=metrics['interval95']['production'][0]>0,
                      all_moves=metrics['all_move_gain']>=0,
                      capture_coverage=metrics['surprise_captures']>=g['surprise_min'],
                      capture_identity=metrics['capture_target_error']==0,
                      priority_coverage=all(p['games']>=g['priority_games_min'] for p in metrics['priority'].values()),
                      priority_nonregression=all(p['games'] and p['gains']['base']>=0 and p['gains']['production']>=0 for p in metrics['priority'].values()))
    return metrics, conditions


@contextmanager
def lease(cores):
    path = ROOT/'chatroom/cores.json'
    def change(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            current = read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in current['allocation'])
                current['allocation'].append(dict(owner=OWNER, cores=cores, pid=os.getpid(), at=now(), purpose='CPU held-out prior scoring'))
            else:
                current['allocation'] = [row for row in current['allocation'] if row['owner'] != OWNER]
            current['updated'] = now()
            write(path, current)
    change(True)
    try:
        yield
    finally:
        change(False)


def execute(preflight=False):
    plan = read(OUT/'plan.json')
    assert (torch.__version__, torch.version.git_version) == (plan['torch_version'], plan['torch_git'])
    for name, digest in plan['dependencies'].items():
        assert sha(name) == digest, name
    os.sched_setaffinity(0, {6} if preflight else set(plan['cores']))
    torch.set_num_threads(len(os.sched_getaffinity(0)))
    torch.set_float32_matmul_precision('highest')
    cache = Cache(CACHE)
    try:
        if preflight:
            # Old fitted trajectories only, excluding every holdout row.
            old = {row['sequence_sha256'] for row in read(SEQUENCE_EXCLUSIONS[-1])}
            games = [row for row in cache.games if row['split']=='train' and row['sequence_sha256'] in old][:8]
            assert len(games) == 8
        else:
            games, counts, cohort = inventory(cache.games)
            assert counts == plan['counts'] and cohort == plan['cohort_sha256']
        scorer = Scorer(plan)
        pending, metadata, results = [], [], []
        for number, game in enumerate(games, 1):
            for x, row in contexts(scorer.producer, cache, game, preflight):
                pending.append(x)
                metadata.append(row)
                if len(pending) == plan['batch']:
                    scorer.score(pending, metadata)
                    results.extend(metadata)
                    pending, metadata = [], []
            if not preflight and number%200 == 0:
                print(json.dumps(dict(games=number, total=len(games), scored=len(results))), flush=True)
        if pending:
            scorer.score(pending, metadata)
            results.extend(metadata)
        checks = dict(games=len(games), frames=sum(game['records'] for game in games), decisions=len(results),
                      capture_entries=scorer.captures, native_control_max_error=scorer.native_error,
                      scalar_contexts=scorer.scalar_contexts, scalar_logp_max_error=scorer.scalar_error,
                      scalar_residual_max_error=scorer.residual_error, plan_sha256=sha(OUT/'plan.json'))
        if preflight:
            assert scorer.scalar_contexts >= 2 and scorer.captures > 100
            write(OUT/'preflight.json', dict(passed=True, **checks), exclusive=True)
        else:
            metrics, conditions = summarize(plan, results)
            conditions['numeric'] = scorer.scalar_contexts >= 100 and max(scorer.native_error, scorer.scalar_error, scorer.residual_error)<scorer.tolerance
            decision = 'native_cost_design_allowed' if all(conditions.values()) else 'close_fixed_hard_label_head'
            write(OUT/'result.json', dict(at=now(), metrics=metrics, checks=checks, conditions=conditions,
                                        decision=decision, cohort_sha256=plan['cohort_sha256']), exclusive=True)
        print(json.dumps(checks), flush=True)
    finally:
        cache.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('freeze', 'preflight', 'score'))
    stage = parser.parse_args().stage
    if stage == 'freeze':
        freeze()
    elif stage == 'preflight':
        execute(preflight=True)
    else:
        plan = read(OUT/'plan.json')
        assert read(OUT/'preflight.json')['plan_sha256'] == sha(OUT/'plan.json')
        receipt = dict(status='running', started_at=now(), plan_sha256=sha(OUT/'plan.json'))
        with lease(plan['cores']):
            write(OUT/'execution.json', receipt, exclusive=True)
            start = time.monotonic()
            def timeout(*_):
                raise TimeoutError('held-out scoring exceeded its bound')
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(plan['max_seconds'])
            try:
                execute()
                receipt.update(status='complete', result_sha256=sha(OUT/'result.json'))
            except BaseException as exc:
                receipt.update(status='failed', error=repr(exc))
                raise
            finally:
                signal.alarm(0)
                receipt.update(ended_at=now(), seconds=time.monotonic()-start)
                write(OUT/'execution.json', receipt)


if __name__ == '__main__':
    main()
