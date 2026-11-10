"""Independent scalar probabilities and course-referee audit of new sources."""
import ctypes
import gzip
import json
import os
import sys
import time
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from protocol import (ROOT, OUT, OLD, OLD_OUT, PRIORITY, now, instant, stamp_ns, sha, write,
                      check_pins, cohort_game, ordered_candidates, gate_result)
sys.path.insert(0, str(OLD))
import numpy as np
import torch
from prepare import library
from train import collect, encoded, bootstrap
from model import COLUMNS
sys.path.insert(0, str(ROOT.parent / 'fow-starter'))
import referee as ref


def main():
    start = time.monotonic()
    plan = json.loads((OUT / 'plan.json').read_text())
    cohort = json.loads((OUT / 'cohort.json').read_text())
    result = json.loads((OUT / 'result.json').read_text())
    execution = json.loads((OUT / 'execution.json').read_text())
    check_pins(plan)
    assert instant(execution['started_at']) < instant(plan['cutoff'])
    assert instant(cohort['sealed_at']) < instant(json.loads((OUT / 'scoring.json').read_text())['started_at'])
    assert sha(OUT / 'cohort.json') == result['cohort_sha256'] == execution['cohort_sha256']
    archive = __import__('pathlib').Path(plan['archive'])
    pages = sorted(archive.glob(f"page-{cohort['collection_tick']:03d}-*.json"))
    listed = []
    for i, path in enumerate(pages):
        page = json.loads(path.read_text())['page']
        if i:
            previous = json.loads(pages[i-1].read_text())['page']
            assert previous['nextCursor'] is not None
            url = json.loads(path.read_text())['fetch']['url']
            import urllib.parse
            assert urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['cursor'] == [previous['nextCursor']]
        listed.extend(page['games'])
    assert not page['nextCursor'] or any(instant(r['createdAt']) < instant(plan['cutoff']) for r in page['games'])
    ordered = ordered_candidates(listed, plan['cutoff'])
    ordered = [r for r in ordered if stamp_ns(r['createdAt']) <= stamp_ns(plan['data_deadline'])]
    denied = {g['sequence_sha256'] for g in json.loads(__import__('pathlib').Path(plan['previous_plan']).read_text())['games']}
    rebuilt = []
    course_frames = 0
    lib = library()
    buffers = [ctypes.create_string_buffer(65) for _ in range(3)]
    for row in ordered:
        path = archive / 'games' / row['id'] / 'replay.json'
        rp = json.loads(path.read_text())
        game, reason = cohort_game(row, rp, sha(path), denied)
        if game is None:
            continue
        denied.add(game['sequence_sha256'])
        rebuilt.append(game)
        board = ref.FowBoard()
        lib.prior_start()
        for ply, frame in enumerate(rp['frames']):
            if ply:
                text = frame['move']
                move = ref.chess.Move.from_uci(text)
                assert move in ref.fow_moves(board)
                board.push(move)
                assert lib.prior_step(encoded(text)) >= 0
            assert lib.prior_state(*buffers) == ply % 2
            true_board = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
            values = [true_board, ref.observation(board, True), ref.observation(board, False)]
            assert all(value == frame[key] == buf.value.decode()
                       for value, key, buf in zip(values, ('board','white','black'), buffers))
            course_frames += 1
        if len(rebuilt) == plan['games']:
            break
    assert rebuilt == cohort['games']
    torch.set_num_threads(2)
    data, meta, receipt = collect(dict(games=rebuilt), lib, 'future', False)
    assert receipt['unpacked_sha256'] == json.loads((OUT / 'future-data.json').read_text())['unpacked_sha256']
    rows = [json.loads(line) for line in gzip.decompress((OUT / 'decisions.jsonl.gz').read_bytes()).splitlines()]
    assert sha(OUT / 'decisions.jsonl.gz') == result['scores_sha256'] and len(rows) == len(meta)
    models = {kind:json.loads((OLD_OUT / f'22-{kind}-model.json').read_text()) for kind in ('linear','quadratic')}
    worst, actions, captures = 0., 0, 0
    for i, m in enumerate(meta):
        assert all(rows[i][key] == value for key,value in m.items())
        n = m['n']
        x = data['x'][i,:n].numpy().astype(float)
        base = data['base'][i,:n,1].numpy()
        top = base.max()
        logz = np.float32(top + np.float32(np.log(np.exp((base-top).astype(float)).sum())))
        baseline = (base-logz).astype(float)
        quiet = x[:,0] == 0
        for kind in ('base','linear','quadratic'):
            lp = baseline.copy()
            lin_native = np.zeros(22,np.float32)
            q_native = np.zeros((22,22),np.float32)
            if kind != 'base':
                lin_native = np.array(models[kind]['linear'],np.float32)
                q_native = np.array(models[kind]['quadratic'],np.float32)
            if kind != 'base' and quiet.sum() > 1:
                v = x[:,COLUMNS]
                model = models[kind]
                lin = np.array(model['linear'],np.float32).astype(float)
                q = np.array(model['quadratic'],np.float32).astype(float)
                d = v@lin + np.einsum('ni,ij,nj->n',v,q,v)
                before, after = base[quiet].astype(float), base[quiet].astype(float)+d[quiet]
                correction = before.max()+np.log(np.exp(before-before.max()).sum())-after.max()-np.log(np.exp(after-after.max()).sum())
                lp[quiet] += d[quiet]+correction
            assert np.array_equal(lp[~quiet],baseline[~quiet])
            native = np.empty(n,np.float32)
            lib.quiet_logp(data['x'][i,:n].numpy().copy(),base.copy(),n,22,lin_native,q_native,native)
            assert np.array_equal(native[~quiet],baseline.astype(np.float32)[~quiet])
            action_error = float(abs(native.astype(float)-lp).max(initial=0))
            assert action_error < 2e-5
            worst = max(worst,action_error)
            value = lp[m['target']]
            N, h = m['history_n'], float(data['counts'][i,m['target']])
            if N >= 3:
                value = np.logaddexp(np.log(h) if h else -np.inf,np.log(4.)+value)-np.log(N+4)
            error = abs(value-rows[i]['logp'][kind])
            assert error < 2e-5
            worst = max(worst,error)
            actions += n
            captures += int((~quiet).sum())
    p = {k:np.array([r['logp'][k] for r in rows]) for k in ('base','linear','quadratic')}
    primary = np.array([r['primary'] for r in rows])
    capture = np.array([r['capture'] for r in rows])
    surprise = primary & np.array([r['surprise'] for r in rows])
    gain, linear = p['quadratic']-p['base'], p['quadratic']-p['linear']
    saved = result['metrics']
    assert saved['primary'] == int(primary.sum())
    assert saved['surprise_captures'] == int(surprise.sum())
    assert saved['capture_target_error'] == float(abs(gain[capture]).max(initial=0)) == 0
    assert saved['capture_action_error'] == 0
    for kind in p:
        assert abs(saved['nll'][kind]-float(-p[kind][primary].mean())) < 1e-12
    for key, value in [('gain',gain[primary].mean()),('matched_linear_gain',linear[primary].mean()),('all_move_gain',gain.mean())]:
        assert abs(saved[key]-value) < 1e-12
    ci = bootstrap([r for r,selected in zip(rows,primary) if selected],gain[primary],plan['seed'],plan['bootstrap_draws'])
    assert np.allclose(ci,saved['interval95'],rtol=0,atol=1e-12)
    by_game = {g['game']:g for g in rebuilt}
    for r in rows:
        assert r['team_id'] == by_game[r['game']][('white_id','black_id')[r['ply']%2]]
    for team in PRIORITY:
        mask = primary & np.array([r['team_id'] == team for r in rows])
        assert saved['priority'][team]['games'] == len({r['game'] for r,ok in zip(rows,mask) if ok})
        assert saved['priority'][team]['decisions'] == int(mask.sum())
        assert abs(saved['priority'][team]['gain']-(float(gain[mask].mean()) if mask.any() else 0.)) < 1e-12
    assert gate_result(plan,saved) == result['conditions']
    decision = 'native_cost_and_posterior_design_allowed' if all(result['conditions'].values()) else 'close_frozen_full_only_configuration'
    assert result['decision'] == decision
    write(OUT / 'independent-review.json',dict(at=now(),passed=True,course_frames=course_frames,
          scalar_action_checks=actions,scalar_capture_checks=captures,max_scalar_logp_error=worst,
          cohort_reconstructed_from_snapshot=True,old_sequence_exclusions_verified=True,
          aggregates_and_gates_verified=True,seconds=time.monotonic()-start),exclusive=True)
    print(json.dumps(dict(passed=True,decision=decision,course_frames=course_frames,worst=worst)),flush=True)


if __name__ == '__main__':
    main()
