"""Reject a native-v38 evaluator fallback before a local benchmark plays.

The trusted bot's ready line and its stderr are drained by different referee
threads. Allow a short bounded drain after protocol readiness, outside the
game clock. This does not change the shipped bot or the course referee.
"""
import time

from local_turn_control import run_controlled

READY = b'mist: stockfish ready'
FALLBACK = b'mist: stockfish failed to start; our evaluator scores the leaves'
DRAIN_SECONDS = .25


def run_with_native_stockfish(referee, white, black, **kwargs):
    """Use only for sequential benchmarks where both native bots require SF.

    A fallback or absent marker is an infrastructure failure with no score.
    The caller must retain failed attempts and perform its usual cleanup.
    """
    original = referee.Bot
    checks = []

    class RequireStockfish(original):
        def initialize(self, timeout):
            super().initialize(timeout)
            start = time.monotonic()
            deadline = start + DRAIN_SECONDS
            while True:
                # Ignore a partial final line while the reader thread drains.
                lines = bytes(self.stderr_excerpt).split(b'\n')[:-1]
                if FALLBACK in lines:
                    status = 'fallback'
                    break
                if self.stderr_capture.exceeded:
                    status = 'capture_limit'
                    break
                if lines.count(READY) == 1:
                    status = 'ready'
                    break
                if lines.count(READY) > 1:
                    status = 'ambiguous_ready'
                    break
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    status = 'missing_ready'
                    break
                time.sleep(min(.005, remaining))
            side = 'white' if self.side else 'black'
            checks.append(dict(side=side, status=status,
                drain_seconds=time.monotonic()-start))
            if status != 'ready':
                raise referee.SandboxControlFailure(
                    f'Local benchmark requires native Stockfish: {side} {status}')

    referee.Bot = RequireStockfish
    try:
        result = run_controlled(referee, white, black, **kwargs)
    finally:
        referee.Bot = original
    result['localNativeStockfishReadiness'] = checks
    return result
