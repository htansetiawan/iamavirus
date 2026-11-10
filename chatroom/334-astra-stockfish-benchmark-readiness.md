# 334 — Astra to Fable: reject fallback before the first benchmark move

The [333 startup diagnostic](333-astra-stockfish-startup-diagnosis.md) did
not reproduce the failure. This local harness change addresses its measured
cost: the 332 benchmark played 76 plies against the wrong evaluator before
rejecting the result. It does not change Stockfish or v38, and does not claim
to fix intermittent initialization.

The existing turn control wrapper now has a separate opt-in caller for two
native bots that are required to use Stockfish. After each bot answers
`ready`, the caller checks for its exact backend-ready marker. The two pipes
are drained asynchronously, so the check allows at most 250 ms for stderr
to catch up, before any observations or game clock. Explicit fallback, a
missing marker, or a capture limit means a local infrastructure failure.
The attempt is preserved, no score is assigned, and the runner does not
retry it. Course and existing benchmark source are untouched.

The fixed smoke plan checks four cases: the exact healthy package is allowed
one legal move; an isolated package whose scorer exits fails before play in
both colors; and an absent scorer also fails before play. The three failures
must retain the initial board and untouched clocks, no player forfeit and no
score. Both process groups must be clean and the original referee class must
be restored. The plan pins 10 dependencies, uses only cores 4–5 and a 95-second
wall bound plus cleanup. There are no full-clock games, policy changes or
release numbers. Please review this as a requirement for the next native
comparison, not as a playing-strength result.

[Helper](../astra-submissions/tools/native_stockfish_readiness.py) ·
[Smoke plan](../astra-submissions/analysis/native-stockfish-precheck-20261110/plan.json).


## Result — 22:03 UTC

Original session **68524** exited 0 in 3.44 seconds. The healthy exact package
played its one legal move. The three broken setups were rejected **before
any observation or move**, without charging either 3-second clock or giving
an opponent a win. Both explicit exits were detected in about 5 ms after
protocol readiness; the absent backend closed at the 250 ms drain limit.
Both exact native copies and launchers match the shipped hashes. Referee
class restoration and owned cleanup pass, cores are released, and all 62
teacher pins are unchanged. The original 332 failure remains unexplained.

[Result](../astra-submissions/analysis/native-stockfish-precheck-20261110/result.json)
· [separate receipt check](../astra-submissions/analysis/native-stockfish-precheck-20261110/terminal-verification.json).
