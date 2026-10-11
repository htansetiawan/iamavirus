# Local clock fidelity and M4 startup checks

These are correctness/integration results, not chess-strength measurements.

`correctness.json` records the controlled-counter, clock, exit/timeout and
identity-safe cleanup tests with source and referee hashes. Reproduce with:

```sh
/home/henrytan/git/fow-starter/.venv/bin/python astra-submissions/tools/test_local_turn_control.py
```

The hook leaves the official referee rules unchanged. It pauses each owned bot
process group between turns, including Stockfish, and lets the referee buffer
observations for delivery under the moving bot's clock. It does not reproduce
the arena's memory/security sandbox or guarantee uncontended physical cores.

`initial-smoke/` retains three attempted two-ply games from a planned four.
The third falls back to internal evaluation during Stockfish startup, and the
runner stops. The attempted game still has a normal referee draw at its
artificial move limit. It is **not** valid Stockfish-comparison evidence.

`startup5-smoke/` retains four six-ply games after C commit `567c3df` allows
five seconds for initialization. All four use Stockfish successfully and
complete three M4 decisions, including two carried-blueprint decisions each.
Search request deadlines are unchanged. Both scales and both colors pass.

The initial and corrected smoke runs also differ in base time/move limit:
5+0, two plies versus 30+0, six plies. Do not attribute playing differences to
the startup change from these tests. The longer run exercises repeated turns;
the mocked transport test independently validates a handshake slower than 1s.

Manifests identify the original `/tmp` run directories and every frozen
artifact hash. This directory preserves their small JSON and text evidence,
not executable copies. Temporary process IDs in registry files are historical;
never use archived registries to operate on unrelated processes.

The full-game harness is `tools/m4_clock_run.py`. It uses immutable per-run
copies, per-run locking, explicit seeds/settings, bounded worker lifetime,
process-identity checks for interrupted attempts, and failure receipts without
automatic retries. A fault stops the batch instead of silently dropping games.
