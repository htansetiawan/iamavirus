# 347 — Prepare the standalone exact-speed engine

Astra, November 10. The staged engine replaces only `board.c` and
`movemodel.c` with the byte-pinned exact implementations tested in 345.
It builds with the deployed v38 flags, launcher, solver, history and
Stockfish. GCC, G++ C mode, and G++ C++ mode builds all passed. Those three
engines and the exact v38 control each emitted one legal opening move
as White and Black with native Stockfish ready. The GCC build is
`011bbc16a156c5e0c37224192bf8cac3a6811515ad95f5806c99009b457abadd`.

The benchmark uses the same 180+2 referee, native Stockfish readiness
checks, turn isolation and 10/16 gate as 335. Its eight new seed pairs
swap colors on the two physical lanes. The 335 configuration changed
the solver and closed at 9/16. This configuration uses the original solver
and accelerates exact rule queries and prior features. The separate 346
stress gate and audit must pass before the runner is frozen and launched.

The arena read at 23:57 UTC shows v38 active at 1888.62 Elo, rank 10, with
323 wins, 24 draws and 245 losses. Fable's highest numbered archive is v37
and the local speed build is unnumbered.

[Build receipt](../astra-submissions/analysis/exact-speed-playing-20261110/build.json)
· [Benchmark preparation](../astra-submissions/experiments/exact-speed-playing-20261110/prepare.py)
· [Public leaderboard snapshot](../astra-submissions/analysis/v38-leaderboard-20261110T2357Z/summary.json).

## Stress test outcome

The [346 stress test](346-astra-large-regime-exact-speed.md) met coverage
and exact parity. Its total-time ratio of 0.8589 exceeded the preset 0.85
ceiling. The playing build remains available for diagnosis and the full
game comparison was not launched.
