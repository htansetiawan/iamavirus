"""Replay permitted observations/own moves only; no search and no true board input."""
import argparse
import faulthandler
import importlib.util
import json
from pathlib import Path
import resource
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--cap', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    faulthandler.enable()
    faulthandler.dump_traceback_later(15, repeat=True)
    source = Path(__file__).resolve().parents[1]/'obscuro-fidelity-20261108/misty_adapter.py'
    spec = importlib.util.spec_from_file_location('empty_belief_adapter', source)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    import chess
    from fow_chess.engine_profile import PROFILES
    from fow_chess.observation import Observation
    payload = json.loads(args.input.read_text())
    assert set(payload) == {'side', 'seed', 'observations'}
    cap = None if args.cap == 'none' else int(args.cap)
    color = payload['side'] == 'white'
    strategy = PROFILES['v1.6'].build_strategy(seed=payload['seed'], time_budget_seconds=None,
                p_max_size=cap, capture_telemetry=True)
    strategy.reset(color)
    strategy.set_telemetry_sink(str(args.out.with_suffix('.telemetry.jsonl')))
    tracker = adapter.ObservationTracker(color)
    previous, pending = None, None
    started = time.monotonic()
    with args.out.open('x') as output:
        def emit(kind, **fields):
            output.write(json.dumps(dict(kind=kind, elapsed=time.monotonic()-started, cap=cap,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, **fields))+'\n')
            output.flush()
        emit('start', seed=payload['seed'], search_skipped=True, address_space_limit=4 << 30)
        try:
            for item in payload['observations']:
                assert set(item) == {'ply', 'view', 'own_move_after'}
                text = item['view']
                tracker.observe(text)
                visible, pieces = adapter.parse_view(text)
                if previous is not None:
                    phase = 'own' if pending is not None else 'opponent'
                    emit('enter', ply=item['ply'], phase=phase,
                         positions=strategy._engine.enumerator.size,
                         own_move=pending.uci() if pending is not None else None)
                    if pending is not None:
                        strategy.observe_own_move(pending, Observation(visibility_mask=visible, visible_pieces=pieces))
                        pending = None
                    else:
                        lost = adapter.own_squares(previous, color)-adapter.own_squares(text, color)
                        captured = next(iter(lost)) if len(lost) == 1 else None
                        landing = captured if captured in pieces and pieces[captured].color != color else None
                        strategy.observe_opp_move(Observation(visibility_mask=visible, visible_pieces=pieces,
                            own_capture_square=captured, opp_capture_landing_square=landing))
                    emit('exit', ply=item['ply'], phase=phase, positions=strategy._engine.enumerator.size)
                previous = text
                if item['own_move_after'] is not None:
                    pending = chess.Move.from_uci(item['own_move_after'])
                    assert pending in tracker.legal_moves()
                    tracker.record_move(pending)
            emit('complete', frames=len(payload['observations']), positions=strategy._engine.enumerator.size)
        except BaseException as error:
            emit('exception', ply=item['ply'], error=repr(error), positions=strategy._engine.enumerator.size)
            raise
        finally:
            faulthandler.cancel_dump_traceback_later()
            strategy.close()


if __name__ == '__main__':
    main()
