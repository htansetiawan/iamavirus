"""One frozen export/gradient run; never fits or inserts missing truth."""
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import signal
import sys
import time
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np
import torch
from common import HERE, ROOT, OUT, DTYPE, array, encode, library, position_tuple, sha, StateKey
from objective import edge_scores, loss
sys.path.insert(0, str(ROOT))
from learning import ingest


def now():
    return datetime.now(timezone.utc).isoformat()


def unique(p, data):
    with p.open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False); f.write('\n')


def tensors(data):
    action = data['actions']
    return [torch.tensor(action['x'].copy(), dtype=torch.float64),
            torch.tensor(action['base'].copy(), dtype=torch.float64),
            torch.tensor(action['history_count'].copy(), dtype=torch.float64),
            torch.tensor(data['history_n'], dtype=torch.float64),
            torch.tensor(data['parent_weights'], dtype=torch.float64), data['offsets'].tolist()]


def run():
    plan = json.loads((OUT / 'plan.json').read_text())
    os.sched_setaffinity(0, set(plan['cores'])); torch.set_num_threads(2)
    for path, digest in plan['dependencies'].items():
        assert sha(Path(path)) == digest, path
    state = dict(started=now(), status='running', phase='export', plan_sha256=sha(OUT / 'plan.json'))
    unique(OUT / 'execution.json', state)
    def timeout(*_):
        raise TimeoutError('20-minute feasibility bound')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(plan['wall_seconds'])
    started = time.monotonic()
    try:
        lib = library(); key_of = StateKey()
        (HERE / 'build/data').mkdir(exist_ok=False); (OUT / 'inputs').mkdir(exist_ok=False)
        records = []; games = []; total_bytes = 0; probability_error = log_error = 0.
        for game in plan['games']:
            path = ROOT / 'data/raw/games' / game['game'] / 'replay.json'
            assert sha(path) == game['replay_sha256']
            replay = json.loads(path.read_text())
            truth, errors = ingest.validate_replay(replay)
            assert not errors, (game['game'], errors)
            us = game['us']; lib.pl_start(us); feed = []
            stop = 'replay_end'; game_start = time.monotonic(); cases_before = len(records)
            for ply in range(1, len(replay['frames']) - 1):
                parents = lib.pl_count()
                if not parents or parents > plan['stop_worlds'] or lib.pl_capped():
                    stop = 'empty' if not parents else 'cap' if lib.pl_capped() else 'size_limit'
                    break
                frame = replay['frames'][ply]; view = frame[('white', 'black')[us]]
                ours = (ply - 1) % 2 == us
                if ours:
                    feed.append({'kind': 'own', 'move': frame['move'], 'view': view})
                    lib.pl_own(encode(frame['move']), view.encode())
                    continue
                feed.append({'kind': 'opponent', 'view': view})
                eligible = parents <= plan['max_parents']
                before = time.monotonic()
                if eligible:
                    pieces = []; offsets = [0]; weights = []; history_n = []; parent_keys = []
                    key_tuples = {}; merged_halfmoves = {}
                    for i in range(parents):
                        parent = array(lib.pl_position(i), 1)[0]
                        assert key_of(*position_tuple(parent)) == int(parent['key'])
                        parent_keys.append(int(parent['key']))
                        n = ctypes.c_int(); weight = ctypes.c_float(); N = ctypes.c_uint()
                        ptr = lib.pl_parent(i, view.encode(), ctypes.byref(n), ctypes.byref(weight), ctypes.byref(N))
                        assert n.value > 0
                        rows = array(ptr, n.value)
                        assert int(rows['history_count'].sum()) <= N.value
                        for row in rows[rows['key'] != 0]:
                            key = int(row['key']); signature = position_tuple(row)
                            assert key_of(*signature) == key
                            assert key_tuples.setdefault(key, signature) == signature, 'Key collision'
                            merged_halfmoves.setdefault(key, set()).add(int(row['halfmove']))
                        pieces.append(rows); offsets.append(offsets[-1] + n.value)
                        weights.append(weight.value); history_n.append(N.value)
                    data = dict(actions=np.concatenate(pieces), offsets=np.array(offsets, np.int64),
                        parent_weights=np.array(weights, np.float32), history_n=np.array(history_n, np.uint32),
                        parent_keys=np.array(parent_keys, np.uint64))
                lib.pl_opponent(view.encode())
                if not eligible:
                    continue
                assert not lib.pl_capped(), 'Small exported set unexpectedly capped'
                native = np.concatenate([array(lib.pl_position(i), 1) for i in range(lib.pl_count())])
                # Only now join the independent truth label. No true move or
                # true board was an argument to a belief-export function.
                target = truth[ply].board
                target_tuple = (target.board_string(), target.side, target.castling, target.en_passant)
                target_key = key_of(*target_tuple)
                action = data['actions']; consistent = action['key'] != 0
                positive = consistent & (action['key'] == target_key)
                if positive.any():
                    assert key_tuples[target_key] == target_tuple
                with torch.no_grad():
                    scores = edge_scores(*tensors(data), torch.zeros(26, dtype=torch.float64)).numpy()
                keys, inverse = np.unique(action['key'][consistent], return_inverse=True)
                grouped = np.full(len(keys), -np.inf)
                np.logaddexp.at(grouped, inverse, scores[consistent])
                order = np.argsort(native['key']); native = native[order]
                assert np.array_equal(keys, native['key'])
                for row in native:
                    assert key_tuples[int(row['key'])] == position_tuple(row)
                normalizer = lambda z: z - np.logaddexp.reduce(z)
                expected = normalizer(native['base'].astype(float)); got = normalizer(grouped)
                pe = float(np.max(np.abs(np.exp(got) - np.exp(expected))))
                le = float(np.max(np.abs(got - expected)))
                assert pe <= plan['gate']['probability_tolerance'] and le <= plan['gate']['log_probability_tolerance'], (game['game'], ply, pe, le)
                probability_error = max(probability_error, pe); log_error = max(log_error, le)
                data.update(positive=positive, native_keys=native['key'], native_log_weights=native['base'],
                            truth_key=np.array(target_key, np.uint64), truth_halfmove=np.array(target.halfmove_clock, np.int32))
                size = sum(v.nbytes for v in data.values())
                total_bytes += size
                assert total_bytes <= plan['max_bytes'], 'Uncompressed data budget exceeded'
                name = f"{game['game']}-{ply:03d}.npz"; saved = HERE / 'build/data' / name
                with saved.open('xb') as f:
                    np.savez_compressed(f, **data)
                parent_indices = np.repeat(np.arange(parents), np.diff(data['offsets']))
                contributing = len(np.unique(parent_indices[consistent]))
                truth_mass = float(np.exp(got[keys == target_key]).sum())
                record = dict(game=game['game'], us=us, ply=ply, parents=parents,
                    contributing_parents=contributing, native_worlds=len(keys), actions=len(action),
                    consistent_edges=int(consistent.sum()), positive_edges=int(positive.sum()),
                    natural_truth_mass=truth_mass, history_hit_parents=sum(n >= 3 for n in history_n),
                    merged_successors=int(sum(np.bincount(inverse) > 1)),
                    differing_halfmove_merges=sum(len(v) > 1 for v in merged_halfmoves.values()),
                    nontrivial=contributing > 1 and len(keys) > 1 and bool(positive.any()),
                    raw_bytes=size, saved_bytes=saved.stat().st_size, data_path=str(saved), sha256=sha(saved),
                    export_update_audit_seconds=time.monotonic() - before,
                    probability_error=pe, log_probability_error=le)
                records.append(record)
            unique(OUT / 'inputs' / (game['game'] + '.json'), {'us': us, 'inputs': feed})
            games.append(dict(game=game['game'], us=us, stop_reason=stop, stop_ply=ply,
                final_worlds=lib.pl_count(), ever_capped=bool(lib.pl_capped()),
                cases=len(records) - cases_before, validated_frames=len(truth), elapsed=time.monotonic() - game_start))
            print(json.dumps({'game': game['game'], 'cases': len(records), 'raw_bytes': total_bytes, 'stop': stop}), flush=True)
        lib.pl_free()
        unique(OUT / 'cases.json', records); unique(OUT / 'games.json', games)
        state['phase'] = 'gradients'; (OUT / 'execution.json').write_text(json.dumps(state, indent=2) + '\n')
        selected = []
        for us in (0, 1):
            pool = sorted((r for r in records if r['us'] == us and r['nontrivial']),
                          key=lambda r: sha(Path(r['data_path'])))
            seen = set()
            for row in pool:
                if row['game'] in seen:
                    continue
                selected.append(row); seen.add(row['game'])
                if len(seen) == 6:
                    break
        gradients = []; rng = np.random.default_rng(2301102)
        for row in selected:
            with np.load(row['data_path'], allow_pickle=False) as packed:
                data = {k: packed[k] for k in packed.files}
            args = tensors(data)
            valid = torch.tensor(data['actions']['key'] != 0)
            positive = torch.tensor(data['positive'])
            theta = torch.tensor(rng.normal(0, .03, 26), dtype=torch.float64, requires_grad=True)
            actual = loss(*args, valid, positive, theta); actual.backward()
            grad = theta.grad.detach().numpy().copy(); numerical = []
            for i in range(26):
                plus, minus = theta.detach().clone(), theta.detach().clone()
                plus[i] += 1e-5; minus[i] -= 1e-5
                numerical.append(float((loss(*args, valid, positive, plus) - loss(*args, valid, positive, minus)) / 2e-5))
            error = float(np.max(np.abs(grad - numerical)))
            assert error <= plan['gate']['gradient_tolerance'], (row['game'], row['ply'], error)
            gradients.append({'game': row['game'], 'ply': row['ply'], 'us': row['us'], 'max_error': error,
                              'gradient_norm': float(np.linalg.norm(grad))})
        unique(OUT / 'gradient-checks.json', gradients)
        nontrivial = [r for r in records if r['nontrivial']]
        conditions = dict(nontrivial_cases=len(nontrivial) >= plan['gate']['minimum_nontrivial_cases'],
            nontrivial_games=len({r['game'] for r in nontrivial}) >= plan['gate']['minimum_nontrivial_games'],
            both_colours={r['us'] for r in nontrivial} == {0, 1}, gradients=bool(gradients),
            native_posterior_parity=True, missing_natural_truth=sum(r['positive_edges'] == 0 for r in records) == 0)
        result = dict(games=len(games), cases=len(records), nontrivial_cases=len(nontrivial),
            nontrivial_games=len({r['game'] for r in nontrivial}),
            natural_positive_cases=sum(r['positive_edges'] > 0 for r in records),
            cases_with_merged_histories=sum(r['merged_successors'] > 0 for r in records),
            cases_with_history_hits=sum(r['history_hit_parents'] > 0 for r in records),
            cases_with_halfmove_ambiguity=sum(r['differing_halfmove_merges'] > 0 for r in records),
            validated_frames=sum(g['validated_frames'] for g in games), raw_bytes=total_bytes,
            saved_bytes=sum(r['saved_bytes'] for r in records), maximum_probability_error=probability_error,
            maximum_log_probability_error=log_error, gradient_cases=len(gradients),
            elapsed=time.monotonic() - started, conditions=conditions,
            decision='training_plan_review_allowed' if all(conditions.values()) else 'close_this_feasibility_regime',
            scope=plan['scope'])
        unique(OUT / 'result.json', result); print(json.dumps(result, indent=2), flush=True)
        state['status'] = 'complete'; state['phase'] = 'done'
    except BaseException as error:
        state.update(status='failed', error=f'{type(error).__name__}: {error}'); raise
    finally:
        signal.alarm(0); state['ended'] = now()
        (OUT / 'execution.json').write_text(json.dumps(state, indent=2) + '\n')


if __name__ == '__main__':
    run()
