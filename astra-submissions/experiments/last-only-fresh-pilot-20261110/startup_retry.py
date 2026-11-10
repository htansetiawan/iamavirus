"""Permit one replacement of a rejected setup before any game input."""
import json
from pathlib import Path

from native_stockfish_readiness import run_with_native_stockfish


def retryable(game, base):
    checks = game.get('localNativeStockfishReadiness', [])
    if not checks or checks[-1]['status'] not in ('fallback', 'missing_ready'):
        return False
    last = checks[-1]
    expected = f"Infrastructure startup failure: Local benchmark requires native Stockfish: {last['side']} {last['status']}"
    frames = game['frames']
    protocol = game['protocol']
    if (game['result'] != '*' or game.get('failedSide') or game['reason'] != expected
            or game.get('warnings') or len(frames) != 1 or frames[0]['ply'] != 0
            or frames[0]['clocks'] != [base, base] or protocol['truncated']):
        return False
    header = ('fow', f"w {base:g} {game['timeControl']['incrementSeconds']:g}",
              f"b {base:g} {game['timeControl']['incrementSeconds']:g}")
    return all(event['ply'] == 0 and (
        (event['direction'] == 'input' and event['text'] in header)
        or (event['direction'] == 'output' and event['text'] == 'ready'))
        for event in protocol['events'])


def play(referee, white, black, *, verify_cleanup, registry_path, **kwargs):
    game = run_with_native_stockfish(referee, white, black, registry_path=registry_path, **kwargs)
    if not retryable(game, kwargs['base']):
        return game
    registry = Path(registry_path)
    failures = verify_cleanup(registry.parent)
    if failures:
        raise RuntimeError(f'Cannot verify cleanup before replacing rejected setup: {failures}')
    rejected = registry.parent/'rejected-setup'
    rejected.mkdir(exist_ok=False)
    with (rejected/'replay.json').open('x') as file:
        json.dump(game, file, indent=2, allow_nan=False)
        file.write('\n')
    registry.rename(rejected/'processes.json')
    return run_with_native_stockfish(referee, white, black, registry_path=registry_path, **kwargs)


def audit_rejection(directory, job_id, base):
    archived = directory/'rejected-setup'
    if not archived.exists():
        return False
    game = json.loads((archived/'replay.json').read_text())
    if game['id'] != job_id or not retryable(game, base):
        raise ValueError(f'Invalid setup retry for {job_id}')
    registry = json.loads((archived/'processes.json').read_text())
    if not registry:
        raise ValueError(f'Missing process evidence for {job_id}')
    return True
