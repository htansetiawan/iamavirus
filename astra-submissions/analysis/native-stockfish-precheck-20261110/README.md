# Fail fast when a local native benchmark lacks Stockfish

The [opt-in helper](../../tools/native_stockfish_readiness.py) checks the
backend marker after each native bot's protocol `ready` and before either
side sees an observation. It allows a bounded stderr drain because the two
streams use separate reader threads. Missing, ambiguous, excessive, or
fallback output ends the attempt as a local infrastructure fault.

All four [smoke cases](result.json) passed. The healthy exact v38 package
played one legal move. Deliberate scorer exits as White and Black and an
absent scorer as Black all stopped at zero plies with untouched clocks and
no observations or score. The original referee class was restored; owned
processes and the core lease were released. [Receipt](terminal-verification.json).

This prevents wasting clock on that invalid setup. The native binaries,
Stockfish, rules, and live v38 package are unchanged. It does not repair or
explain the intermittent failure, check later runtime relaunches, or show
strength. A fresh playing comparison must explicitly opt in and retain every
started attempt; it must not reuse any of the closed pilot's results.
