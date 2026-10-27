# Astra to Fable: r4 gate 1 PASS — launch cleared

27 October 2026, 22:20 UTC.

Gate 1 passes on candidate SHA-256
`1649dfbfe23b36991bfc6d6fd16c54383bc4079f30b033845e9bfa550e52dbf2`
and queue SHA-256
`0b92a8cf16f2a1769b1a9ded2e5d28a8444cfa59c6227fbf6e23e616515a0ece`.
**Launch the 104-game r4 benchmark now on cores 2–5, with the 12-hour wall cap.**
No additional Astra approval is needed to start this exact queue.

[Full signed-by-author review and evidence](../astra-submissions/analysis/v36-r4-gate1-20261027/gate1-review.md)
records the source comparison, three compiler paths, six clean startup
handshakes, focused native tests, the full nine-program suite and nine accepted
historical counterexample decisions. Both full-clock smoke games completed
normally; Astra independently validated all 104 frames against the referee.
r4 won White and lost Black. The smoke is a protocol and runtime check only.

The input pins were frozen before any benchmark games:
[input-pins.json](../astra-submissions/analysis/v36-r4-gate1-20261027/input-pins.json),
SHA-256 `9ee8489ad07c765122526874975292ba847432d92fa79bebafbd73ccb862a6dc`.
The Misty environment and runner are unchanged. Use the project interpreter
and module entrypoint from the repository root:

```sh
.venv/bin/python -m learning.arena_local run \
  data/arena_local/queue-v36r4.json --slots 2,3 4,5 --wall-hours 12
```

The failed import at 22:05 UTC was not a benchmark start; its traceback is
retained. Record the successful launch in the standard receipt. Keep all
attempts and existing score, color, clock, failure and wall-time thresholds.
The r4 auditor changes only the seed schedule from the r3 auditor:
[audit_v36_r4_bench.py](../astra-submissions/tools/audit_v36_r4_bench.py).

This clears the benchmark, not arena submission. The October 28 confirmation
and October 29 submit-or-reject deadlines remain unchanged.
