# Astra independent review: v36 r3

27 October 2026 UTC. Execution of the [agreed decision contract](../v36-plan-20261026/decision-contract.md),
following Henry's execution go-ahead. This is a source/artifact review, not a
playing-strength result or an arena release approval.

## Reviewed artifact

- ZIP: `data/candidates/iamavirus-v36-candidate-mist-c-v20-r3.zip`
- SHA-256: `5cdbb9caf8a3c990b63f3338a8501638d746bdf9a5d573f972c3325905e3cf60`
- Engine source: mist-c `ff893130fb0c0759cb5cab1d9ddb223702a6c07b`.
- Later test-only edge coverage: mist-c `2524f8e9150465f22cbb88d383699858e23be322`.
- Queue: `data/arena_local/queue-v36r3.json`, SHA-256
  `2ee4f745cf1691fe25ad157986c678775f337cca249c897303cf75e02aac4e33`.
- [Input pins](input-pins.json), SHA-256
  `b3835595ea51a4e9711d0748d5b3202a118774cffcb07c3597b2c76ba981730b`.

I compared every one of the ZIP's **19 source/header members** with `ff89313`:
all match. Stockfish and the history-table bytes match the immutable v35 ZIP.
The launcher exports only their paths; B2 is enabled by its C default, without
a local environment override. The fixed queue matches the agreed 40/32/32
allocation, seeds, colors and empty extra environment.

The `guard_rule` extraction preserves the per-move arithmetic and both exclusion
passes on inspection. The existing king/queen verdict remains ORed into every
piece-guard exclusion. The fallback correction gives safety exclusions priority
over repetition and respects them in the final legality fallback when alternatives
remain. None of the deferred async, iteration, hazard or belief changes appears
in this candidate.

I reviewed the rule/fallback tests, including the newly added move-accounting
fixtures for both colors: immediate king capture, en-passant capture credit,
and promotion. The promotion test explicitly records an existing approximation:
the risk heuristic credits captures but not the promotion's material gain. This
review does not silently change that policy.

Fable reports all tests passed, three B1 decision replays over three seeds each
returned no fatal choices, and gcc/g++ fallback builds initialized correctly.
The written complete gate-1 receipt and both-color smoke results remain the
authoritative execution evidence; source review alone does not replace them.

## Independent audit tool

The benchmark auditor's **16 integrity tests passed**, including incomplete
in-flight jobs, duplicate/color omissions, unlogged attempts, artifact/seed
changes, altered replay data, deadline breaches and score/clock regressions.
It also verified all 217 frames of the three superseded diagnostic games using
the actual referee. That validates the audit path, not the old candidate's strength.

The final gate audit uses:

```sh
.venv/bin/python astra-submissions/tools/audit_v36_bench.py audit \
  --pins astra-submissions/analysis/v36-execution-20261027/input-pins.json \
  --run-receipt data/arena_local/receipts/queue-v36r3.json \
  --out astra-submissions/analysis/v36-execution-20261027/bench-audit.json
```

The input pins are immutable. A source, ZIP or queue change needs an explicitly
new gate; it cannot inherit these identifiers or old results.

## Pre-launch findings sent to Fable

The runner now records failed/unknown results, but its first wall-limit patch
checked only before a color pair. It could still start the second game beyond
the deadline and leave in-flight games unbounded. A true deadline check and
safe referee/engine cleanup are required before the 104-game gate launches.
Keep the smoke run and its receipt separate from that gate.

For the later fresh-data construction: completed replay `createdAt` is the API's
recorded completion timestamp; controls must stop at exactly 100 rather than
overshooting by a game's remaining decisions; missing trajectory hashes must
not merge unrelated games into a `None` bucket; final manifests must refuse
overwrite. These were raised before the fixed data window closes. They change
neither the window nor the candidate policy.

## Execution checks

The two-color smoke completed at **01:39:08 UTC**: one win as White and one
loss as Black, both normal king-capturable endings. Candidate final clocks were
35.89 and 24.70 seconds. I independently validated all **194 frames**, including
both observations and terminal states, using the referee; see
[smoke-audit.json](smoke-audit.json). These two games establish protocol/runtime
operation, not an improvement in playing strength. They are excluded from the
104-game gate.

On project commit `ba50da8`, the combined runner/auditor checks passed:
**19 tests, 3 subtests**, using `.venv/bin/python -m pytest`. The default shell's
Python lacks pytest; the project environment was used successfully. The runner
now checks each color separately, records every failed attempt and has process
tree timeout cleanup. Review identified that its initial 1,200-second per-game
limit could truncate a valid long 180+2 game: 1,000 plies can consume 360 + 2,000
seconds of clock, before startup overhead. Fable is correcting this runner-only
limit before launch; the candidate ZIP and input pins remain unchanged.

Fresh-builder fixes are in `ba50da8`: aware completion timestamps, control caps
inside each game's loop, trajectory recomputation/quarantine and refusal to
overwrite a completed manifest. The fresh gate must additionally report zero
old games without a recoverable trajectory before its exclusion coverage can
be accepted. Its cutoff and selection criteria remain unchanged.

**Source/artifact and smoke review: pass.** The complete written gate-1 receipt,
final runner check, fresh confirmation and local playing results remain separate
requirements. Fable has the existing authorization to launch after those
pre-launch checks, without another user permission round.

## Gate launched

Final runner correction `63f7265` uses a 2,450-second scheduling fit budget
and an in-flight timeout against the remaining overall deadline, reserving
30 seconds for cleanup. It also refuses fresh-set construction if any earlier
game lacks an exclusion trajectory. I reviewed these changes and reran the
combined checks: **20 tests, 3 subtests passed**, including a real grandchild
in a separate process session. Fable's complete
[gate-1 receipt](../../../fable-submissions/analysis/v20-material-guard-20261027/gate1-receipt-r3.md)
records the builds, engine tests and nine counterexample replays.

The frozen 104-game queue started **2026-10-27 01:40:52 UTC**, two lanes on
cores 2–3 and 4–5, with a hard cap at **13:40:52 UTC**. Astra observed two
started attempts and zero failures. The independent
[launch audit](launch-audit.json) found no changed inputs or invalid jobs;
its status is correctly **incomplete**, with both games in flight. Runtime
source hashes and the observed receipt are in [launch-runtime.json](launch-runtime.json).

**Pre-launch review: pass. Playing-strength/fresh-data gates: pending.**
Fable owns the running queue and the once-only fresh construction after 11:30 UTC.
The next human review remains October 27 at 20:00 UTC (1 p.m. Pacific), and the
submit-or-reject deadline remains October 29 at the same time. No background
GPU work, automatic arena upload or expansion of the candidate scope was added.
