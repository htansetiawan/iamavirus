"""Bounded component replay: Misty belief updates from observations/own moves.

Historical searches are skipped; one final search is optional. This is a
component diagnostic, not a counterfactual game or a reproduction of search
values/carryover. The original adapter's capture inference is used verbatim.
"""
import argparse
import faulthandler
import importlib.util
import json
import os
from pathlib import Path
import resource
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--side', choices=('white', 'black'), required=True)
    parser.add_argument('--cap', default='none')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--search-last', action='store_true')
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    faulthandler.enable()
    faulthandler.dump_traceback_later(15, repeat=True)
    here = Path(__file__).resolve().parent
    original = here.parent/'obscuro-fidelity-20261108/misty_adapter.py'
    spec = importlib.util.spec_from_file_location('belief_trace_adapter', original)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    import chess
    from fow_chess.engine_profile import PROFILES
    from fow_chess.observation import Observation
    from fow_chess.selfplay import PerspectiveView
    color = args.side == 'white'
    cap = None if args.cap == 'none' else int(args.cap)
    strategy = PROFILES['v1.6'].build_strategy(seed=2752003, time_budget_seconds=None,
                                            p_max_size=cap, capture_telemetry=True)
    strategy.reset(color)
    strategy.set_telemetry_sink(str(args.out.with_suffix('.telemetry.jsonl')))
    game = json.loads(args.replay.read_text())
    previous, pending = None, None
    tracker = adapter.ObservationTracker(color)
    start = time.monotonic()
    with args.out.open('x') as output:
        def emit(kind, **fields):
            output.write(json.dumps(dict(kind=kind, elapsed=time.monotonic()-start,
                cap=cap, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, **fields))+'\n')
            output.flush()
        emit('start', side=args.side, search_skipped=True, memory_limit_bytes=4 << 30,
             clock_enabled=strategy._clock_time_enabled)
        try:
            for index, frame in enumerate(game['frames']):
                text = frame[args.side]
                tracker.observe(text)
                visible, pieces = adapter.parse_view(text)
                if previous is not None:
                    phase = 'own' if pending is not None else 'opponent'
                    before = strategy._engine.enumerator.size
                    emit('enter', frame=index, phase=phase, positions=before)
                    then = time.monotonic()
                    if pending is not None:
                        strategy.observe_own_move(pending, Observation(visibility_mask=visible, visible_pieces=pieces))
                        pending = None
                    else:
                        lost = adapter.own_squares(previous, color)-adapter.own_squares(text, color)
                        captured = next(iter(lost)) if len(lost) == 1 else None
                        landing = captured if captured in pieces and pieces[captured].color != color else None
                        strategy.observe_opp_move(Observation(visibility_mask=visible, visible_pieces=pieces,
                            own_capture_square=captured, opp_capture_landing_square=landing))
                    emit('exit', frame=index, phase=phase, seconds=time.monotonic()-then,
                         positions=strategy._engine.enumerator.size)
                previous = text
                if (index % 2 == 0) == color and index+1 < len(game['frames']):
                    # This is the mover's recorded own action, not the opponent's
                    # hidden move. choose_move does not mutate P (engine contract).
                    pending = chess.Move.from_uci(game['frames'][index+1]['move'])
                    tracker.record_move(pending)
            if args.search_last:
                frame = game['frames'][-1]
                assert (frame['ply'] % 2 == 0) == color
                visible, pieces = adapter.parse_view(frame[args.side])
                clock = frame['clocks'][0 if color else 1]
                emit('enter', frame=frame['ply'], phase='final_search',
                     positions=strategy._engine.enumerator.size, sent_clock=clock)
                then = time.monotonic()
                legal = tracker.legal_moves()
                view = PerspectiveView(perspective=color, own_legal_moves=legal,
                    visible_squares=visible, visible_piece_map=pieces,
                    clock_remaining_ms=int(clock*1000), increment_ms=2000)
                chosen = strategy.pick_move(view)
                emit('exit', frame=frame['ply'], phase='final_search', seconds=time.monotonic()-then,
                     positions=strategy._engine.enumerator.size, move=chosen.uci(), legal=chosen in legal)
            emit('complete', frames=len(game['frames']), positions=strategy._engine.enumerator.size)
        finally:
            faulthandler.cancel_dump_traceback_later()
            strategy.close()


if __name__ == '__main__':
    main()
