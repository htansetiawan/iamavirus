"""Frozen king-location complementarity screen; no search, fitting or promotion."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import zipfile

import numpy as np
import onnxruntime as ort

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/hidden-king-complement-20261102'
sys.path.insert(0, str(ROOT))
from learning import features, ingest

ENGINE = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
NETWORK = ROOT / 'fable-submissions/iamavirus-v23-hybrid.zip'
ENGINE_SHA = '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
GRAPH_SHA = '4e0d7eb9d01226fce5085ff42a9b20fab3ce6df343a61a913c4cc9edd54b055b'
OPPONENTS = ['Instructors', 'duck', 'HYPOTHERMIA', 'Greek Gift', 'Knight Vision',
             'Strongly Invisible', 'Decent Chess Bot', 'Crimson Fog', 'Mist Opportunities']
NAMES = ('sharp', 'flat', 'cnn', 'pool')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def write(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def actor_stream(replay, side):
    """Only data delivered to this player; no opposing actions or truth."""
    key = ('white', 'black')[side]
    plies = list(range(side, len(replay['frames']) - 1, 2))
    assert plies
    tc = replay.get('timeControl', {})
    return dict(side=side, views=[f[key] for f in replay['frames'][:plies[-1]+1]],
                clocks={p: replay['frames'][p]['clocks'][side] for p in plies},
                own_moves={p: replay['frames'][p+1]['move'] for p in plies},
                base=tc.get('baseSeconds', 180), increment=tc.get('incrementSeconds', 2))


def protocol(actor):
    side = actor['side']
    lines = ['fow', f"{('w','b')[side]} {actor['base']} {actor['increment']}"]
    for p, view in enumerate(actor['views']):
        lines.append(view)
        if p in actor['own_moves']:
            lines.append(str(actor['clocks'][p]))
    return '\n'.join(lines) + '\n'


def privacy_check(replay, side):
    altered = copy.deepcopy(replay)
    for p, frame in enumerate(altered['frames']):
        frame['board'] = 'X' * 64
        frame[('black', 'white')[side]] = 'X' * 64
        frame['clocks'][side ^ 1] = -999
        if p and (p - 1) % 2 != side:
            frame['move'] = 'zzzz'
    altered.update(id='redacted', white='redacted', black='redacted', result='redacted')
    assert actor_stream(replay, side) == actor_stream(altered, side)


def king_distribution(logits, view, side):
    assert logits.shape == (64, 7) and np.isfinite(logits).all()
    raw = logits[np.arange(64) ^ (56 if side else 0)].astype(np.float64)
    prob = np.exp(raw - raw.max(axis=1, keepdims=True))
    prob /= prob.sum(axis=1, keepdims=True)
    king = 'k' if side == 0 else 'K'
    if king in view:
        result = np.zeros(64)
        result[view.index(king)] = 1
    else:
        result = prob[:, 5] * np.array([c == '?' for c in view])
        assert result.sum() > 0
        result /= result.sum()
    return result


def session():
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    s = ort.InferenceSession(str(HERE / 'cache/observe.onnx'), sess_options=options,
                             providers=['CPUExecutionProvider'])
    assert s.get_providers() == ['CPUExecutionProvider']
    assert [v.name for v in s.get_outputs()] == ['next_hidden', 'spatial', 'belief_logits', 'value']
    return s


def neural(actor, model):
    side = actor['side']
    tracker = features.FeatureTracker(side)
    hidden = np.zeros((1, 256), dtype=np.float32)
    results = {}
    hashes = []
    for ply, view in enumerate(actor['views']):
        phase = features.PHASE_INITIAL if ply == 0 else (
            features.PHASE_AFTER_OWN if (ply - 1) % 2 == side else features.PHASE_AFTER_OPPONENT)
        tracker.observe(view, phase, ply)
        planes, scalars = tracker.planes()[None], tracker.scalars()[None]
        hashes.append(sha(planes.tobytes() + scalars.tobytes()))
        hidden, spatial, logits, value = model.run(None, dict(planes=planes, scalars=scalars, hidden=hidden))
        assert all(np.isfinite(x).all() for x in (hidden, spatial, logits, value))
        if ply in actor['own_moves']:
            results[ply] = king_distribution(logits[0], view, side).tolist()
            tracker.record_own_move(actor['own_moves'][ply])
    return results, sha(''.join(hashes).encode())


def parse_marginals(stderr):
    rows = []
    for line in stderr.splitlines():
        if not line.startswith('astra-king-location '):
            continue
        parts = line.split()
        assert len(parts) == 132
        rows.append(dict(decision=int(parts[1]), worlds=int(parts[2]), missing=int(parts[3]),
                         sharp=list(map(float, parts[4:68])), flat=list(map(float, parts[68:132]))))
    return rows


def prepare():
    assert file_sha(ENGINE) == ENGINE_SHA
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'plan.json').exists(), 'frozen plan already exists'
    build, cache = HERE / 'build', HERE / 'cache'
    build.mkdir(exist_ok=True)
    cache.mkdir(exist_ok=True)
    with zipfile.ZipFile(ENGINE) as z:
        for name in z.namelist():
            if name.startswith('src/') and not name.endswith('/') or name == 'data/history.bin':
                p = build / name
                p.parent.mkdir(exist_ok=True, parents=True)
                p.write_bytes(z.read(name))
    with zipfile.ZipFile(NETWORK) as z:
        for name in ('observe.onnx', 'model_manifest.json'):
            (cache / name).write_bytes(z.read('model/' + name))
    assert file_sha(cache / 'observe.onnx') == GRAPH_SHA
    manifest = json.loads((cache / 'model_manifest.json').read_text())
    assert manifest['feature_version'] == features.FEATURE_VERSION == 'features-v2'
    assert manifest['hidden_size'] == 256 and manifest['parity']['failure_count'] == 0
    main = build / 'src/main.c'
    source = main.read_text()
    assert source.count('int main(void) {') == 1
    source = source.replace('int main(void) {', '#include "king_marginal.h"\nint main(void) {')
    anchor = '        view_moves(view, us, front.castle, &allowed);'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '\n        if (getenv("ASTRA_KING_LOCATION")) astra_king_marginal(&b, us, decisions, belief_temperature());')
    main.write_text(source)
    (build / 'src/king_marginal.h').write_bytes((HERE / 'king_marginal.h').read_bytes())
    sources = ['board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr', 'front', 'sfeval', 'main']
    command = ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L',
               *[str(build / f'src/{name}.c') for name in sources], '-lm', '-o', str(build / 'mist')]
    subprocess.run(command, check=True, capture_output=True, text=True)
    # Numerical fixture: both colours, known weights, read-only state, empty belief.
    fixture = '''#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "belief.h"
#include "king_marginal.h"
int main(void) {
 Position p[2]; float lw[2]={logf(.2f),logf(.8f)};
 for(int side=0;side<2;side++) {
  for(int i=0;i<2;i++) {pos_clear(&p[i]);pos_put(&p[i],side?i+8:i+48,side^1,KING);}
  Belief b={.items=p,.logw=lw,.count=2,.rng=123};
  Position saved[2]; memcpy(saved,p,sizeof(p)); float w[2];memcpy(w,lw,sizeof(lw));
  astra_king_marginal(&b,side,side,2);
  assert(!memcmp(saved,p,sizeof(p))&&!memcmp(w,lw,sizeof(lw))&&b.rng==123);
 }
 Belief empty={0};astra_king_marginal(&empty,0,2,2);
 return 0;
}
'''
    (build / 'test.c').write_text(fixture)
    subprocess.run(['gcc', '-std=c11', '-O2', '-I', str(build / 'src'), str(build / 'test.c'),
                    str(build / 'src/board.c'), '-lm', '-o', str(build / 'test')], check=True)
    test = subprocess.run([str(build / 'test')], check=True, capture_output=True, text=True)
    rows = parse_marginals(test.stderr)
    for side in (0, 1):
        row = rows[side]
        sq = 8 if side else 48
        np.testing.assert_allclose(np.array(row['sharp'])[[sq, sq+1]], [.2, .8], atol=1e-7)
        np.testing.assert_allclose(np.array(row['flat'])[[sq, sq+1]], [1/3, 2/3], atol=1e-7)
    assert rows[2]['worlds'] == 0 and sum(rows[2]['sharp']) == 0
    for side in (0, 1):
        logits = np.zeros((64, 7))
        logits[19 ^ (56 if side else 0), 5] = 10
        assert int(king_distribution(logits, '?'*64, side).argmax()) == 19
        view = list('?'*64);view[27] = 'k' if side == 0 else 'K'
        assert king_distribution(logits, ''.join(view), side)[27] == 1
    accepted = (ROOT / 'data/raw/accepted.jsonl').read_bytes()
    listings = {r['id']: r for r in map(json.loads, accepted.splitlines())}
    eligible = []; undated = 0
    for r in listings.values():
        date = r.get('createdAt')
        if not isinstance(date, str) or not date:
            undated += 1
            continue
        if not '2026-11-02T05:28' <= date < '2026-11-03':
            continue
        side = next((s for s in (0, 1) if r.get(('white','black')[s]) == 'IAmAVirus'
                     and r.get(('whiteVersion','blackVersion')[s]) == 37), None)
        if side is not None and r.get(('black','white')[side]) in OPPONENTS:
            eligible.append((r['createdAt'], r['id'], side, r[('black','white')[side]]))
    groups = set(); by_side = {0: [], 1: []}
    for date, gid, side, opponent in sorted(eligible):
        path = ROOT / f'data/raw/games/{gid}/replay.json'
        payload = path.read_bytes(); rp = json.loads(payload)
        signature = sha(' '.join(str(f['move']) for f in rp['frames'][1:]).encode())
        if signature in groups:
            continue
        groups.add(signature)
        privacy_check(rp, side)
        by_side[side].append(dict(game=gid, side=side, opponent=opponent, createdAt=date,
                                  replay_path=str(path), replay_sha256=sha(payload), sequence_sha256=signature))
    selected = []
    for side in (0, 1):
        assert len(by_side[side]) >= 8, ('insufficient games', side, len(by_side[side]))
        selected.extend(sorted(by_side[side], key=lambda x: sha(('king-complement-248:'+x['game']).encode()))[:8])
    selected.sort(key=lambda x: (x['createdAt'], x['game']))
    # Real graph smoke test on the initial view only, before inspecting any scores.
    s = session()
    for side in (0, 1):
        case = next(x for x in selected if x['side'] == side)
        actor = actor_stream(json.loads(Path(case['replay_path']).read_text()), side)
        actor['views'] = actor['views'][:side+1]
        actor['own_moves'] = {p:m for p,m in actor['own_moves'].items() if p<=side}
        result, _ = neural(actor, s)
        assert np.isclose(sum(result[side]), 1)
    pins = dict(engine_zip_sha256=ENGINE_SHA, network_zip_sha256=file_sha(NETWORK), graph_sha256=GRAPH_SHA,
                manifest=manifest, binary_sha256=file_sha(build/'mist'), history_sha256=file_sha(build/'data/history.bin'),
                sources={str(p.relative_to(ROOT)):file_sha(p) for p in [Path(__file__), HERE/'king_marginal.h', HERE/'README.md',
                          ROOT/'learning/features.py', ROOT/'learning/action_codec.py', ROOT/'learning/rules.py']},
                patched_main_sha256=file_sha(main), build_command=command)
    write(OUT/'preflight.json', dict(passed=True, native_readonly_fixture=True, both_colour_mapping=True,
                                   visible_king_control=True, redacted_eligible_games=sum(map(len, by_side.values())),
                                   real_graph_initial_views=2, providers=s.get_providers()))
    write(OUT/'plan.json', dict(createdAt=datetime.now(timezone.utc).isoformat(), games=selected, pins=pins,
                              archive_sha256=sha(accepted), eligible_unique={str(k):len(v) for k,v in by_side.items()}, undated_index_rows=undated,
                              opponents=OPPONENTS, lambda_pool=.5, max_seconds=900, per_game_seconds=120,
                              cutoff='2026-11-02T05:28:00Z', selection='salted hash after sequence dedup; eight per colour; no labels'))
    print(json.dumps(dict(prepared=True, games=len(selected), eligible={k:len(v) for k,v in by_side.items()})), flush=True)


def collect():
    plan = json.loads((OUT/'plan.json').read_text())
    for p, digest in plan['pins']['sources'].items():
        assert file_sha(ROOT/p) == digest, p
    assert file_sha(HERE/'build/mist') == plan['pins']['binary_sha256']
    assert file_sha(HERE/'cache/observe.onnx') == GRAPH_SHA
    assert file_sha(HERE/'build/data/history.bin') == plan['pins']['history_sha256']
    model = session()
    started = time.monotonic(); receipt = dict(startedAt=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
        plan_sha256=file_sha(OUT/'plan.json'), completed=[], failures=[], state='running', cpu_affinity=sorted(os.sched_getaffinity(0)))
    write(OUT/'receipt.json', receipt)
    (OUT/'games').mkdir(exist_ok=False)
    def batch_timeout(signum, frame):
        raise TimeoutError('900-second total collection cap')
    signal.signal(signal.SIGALRM, batch_timeout)
    signal.alarm(plan['max_seconds'])
    try:
        for case in plan['games']:
            game_start = time.monotonic(); remaining = plan['max_seconds'] - (game_start - started)
            if remaining <= 0:
                raise TimeoutError('batch cap reached; no retry')
            payload = Path(case['replay_path']).read_bytes()
            assert sha(payload) == case['replay_sha256']
            replay = json.loads(payload); side = case['side']; actor = actor_stream(replay, side)
            privacy_check(replay, side)
            env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
            env.update(ASTRA_KING_LOCATION='1', FOW_SEED='1102248', MIST_MAX_SECONDS='10',
                       MIST_FORCE_MOVES=','.join(actor['own_moves'].values()),
                       MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'))
            proc = subprocess.Popen([str(HERE/'build/mist')], env=env, text=True, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            try:
                stdout, stderr = proc.communicate(protocol(actor), timeout=min(remaining, plan['per_game_seconds']))
            except BaseException:
                os.killpg(proc.pid, signal.SIGKILL)
                stdout, stderr = proc.communicate()
                (OUT/'games'/f"{case['game']}.stderr").write_text(stderr)
                (OUT/'games'/f"{case['game']}.stdout").write_text(stdout)
                raise
            (OUT/'games'/f"{case['game']}.stderr").write_text(stderr)
            (OUT/'games'/f"{case['game']}.stdout").write_text(stdout)
            assert proc.returncode == 0
            assert [line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')] == list(actor['own_moves'].values())
            rows = parse_marginals(stderr)
            assert [r['decision'] for r in rows] == list(range(len(actor['own_moves'])))
            cnn, feature_hash = neural(actor, model)
            # Truth is joined only after both permitted-input predictors finish.
            _, errors = ingest.validate_replay(replay)
            assert not errors, errors
            for row, ply in zip(rows, actor['own_moves']):
                sharp, flat = np.array(row['sharp']), np.array(row['flat'])
                assert row['worlds'] > 0 and row['missing'] == 0
                assert np.isfinite(sharp).all() and np.isfinite(flat).all()
                assert np.isclose(sharp.sum(), 1) and np.isclose(flat.sum(), 1)
                cnn_row = np.array(cnn[ply])
                pooled = np.sqrt(sharp*cnn_row)
                assert pooled.sum() > 0, 'no pool support'
                pooled /= pooled.sum()
                king = 'k' if side == 0 else 'K'
                board = replay['frames'][ply]['board']
                assert board.count(king) == 1
                square = board.index(king)
                row.update(ply=ply, truth=square, hidden=actor['views'][ply][square]=='?',
                           cnn=cnn[ply], pool=pooled.tolist())
                if not row['hidden']:
                    assert min(row[name][square] for name in NAMES) > 1-1e-6
            result = dict(case=case, rows=rows, feature_sequence_sha256=feature_hash, protocol_sha256=sha(protocol(actor).encode()),
                          seconds=time.monotonic()-game_start, thinnings=stderr.count('P thinned from'),
                          rebuilds=stderr.count('belief empty, rebuilt'), stderr_sha256=sha(stderr.encode()),
                          stdout_sha256=sha(stdout.encode()), process_pid=proc.pid, process_returncode=proc.returncode)
            write(OUT/'games'/f"{case['game']}.json", result)
            receipt['completed'].append(case['game'])
            (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
            print(json.dumps(dict(game=case['game'], completed=len(receipt['completed']), decisions=len(rows), seconds=result['seconds'])), flush=True)
        receipt['state'] = 'completed'
    except BaseException as error:
        receipt['state'] = 'failed'
        receipt['failures'].append(dict(type=type(error).__name__, error=str(error)))
        raise
    finally:
        signal.alarm(0)
        receipt.update(endedAt=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started)
        (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def summarize():
    receipt = json.loads((OUT/'receipt.json').read_text())
    assert receipt['state'] == 'completed'
    plan = json.loads((OUT/'plan.json').read_text())
    assert receipt['completed'] == [c['game'] for c in plan['games']]
    games = [json.loads((OUT/'games'/f"{c['game']}.json").read_text()) for c in plan['games']]
    results = {}
    for phase, predicate in [('all_hidden',lambda r:r['hidden']), ('hidden_ply30plus',lambda r:r['hidden'] and r['ply']>=30),
                             ('hidden_early',lambda r:r['hidden'] and r['ply']<30), ('visible',lambda r:not r['hidden'])]:
        scores = {n:[] for n in NAMES}; decisions = 0; eligible = []
        for game in games:
            rows = [r for r in game['rows'] if predicate(r)]
            if not rows:
                continue
            eligible.append(game['case']['game']); decisions += len(rows)
            for name in NAMES:
                vals = []
                for r in rows:
                    prob = np.array(r[name]); ptrue = prob[r['truth']]
                    vals.append([-np.log(max(ptrue,1e-12)), float(prob@prob - 2*ptrue+1), ptrue, float(ptrue>0)])
                scores[name].append(np.mean(vals,axis=0))
        metrics = {n:dict(zip(('nll','brier','truth_mass','nonzero_support'),np.mean(v,axis=0).tolist())) for n,v in scores.items() if v}
        improvements = {}
        if eligible:
            rng = np.random.default_rng(248)
            indices = rng.integers(len(eligible),size=(10000,len(eligible)))
            for name in ('sharp','flat'):
                delta = np.array(scores[name])[:,0]-np.array(scores['pool'])[:,0]
                improvements[name] = dict(mean=float(delta.mean()), descriptive_game_bootstrap_95=np.quantile(delta[indices].mean(axis=1),[.025,.975]).tolist())
        results[phase] = dict(games=len(eligible), decisions=decisions, metrics=metrics, pool_nll_improvement=improvements)
    primary, late = results['all_hidden'], results['hidden_ply30plus']
    gate = bool(late['games'] and all(primary['pool_nll_improvement'][n]['mean']>=.1
        and primary['metrics']['pool']['brier']<=primary['metrics'][n]['brier']
        and late['pool_nll_improvement'][n]['mean']>0 for n in ('sharp','flat')))
    write(OUT/'summary.json',dict(confirmation_proposal_gate=gate, phases=results,
         elapsed_seconds=receipt['elapsed_seconds'], total_decisions=sum(len(g['rows']) for g in games),
         thinnings=sum(g['thinnings'] for g in games), rebuilds=sum(g['rebuilds'] for g in games),
         summary_script_sha256=file_sha(__file__), receipt_sha256=file_sha(OUT/'receipt.json'),
         scope='Frozen development probe. Equal game weighting. Bootstrap is descriptive. No fit, current-engine integration, strength claim or ZIP.'))
    print(json.dumps(dict(gate=gate, primary=primary, late=late)),flush=True)


if __name__ == '__main__':
    os.sched_setaffinity(0, {0, 1})
    {'prepare':prepare, 'collect':collect, 'summarize':summarize}[sys.argv[1]]()
