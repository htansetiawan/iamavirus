# 166 — Astra: v36 execution started

27 October 2026 UTC. Henry's message after reviewing the joint plan:
“ok I am downgrading to xhigh now ... since we will be just going into execution mode.”
This advances the agreed plan to execution. No repeated permission question is
needed for its source checks, artifact freeze, fresh-data gate or bounded local
bench. Henry still submits the eventual passing ZIP to the arena.

## Split and constraints

Fable owns the guard-rule extraction/tests, final r3 artifact, runner integrity,
core reservations, games and fresh-set construction. Astra independently reviews
the source and receipt, freezes/checks inputs, audits manifests and analyzes
results. No duplicated match lanes. The prior gate thresholds, fresh cutoff,
12-hour local-run cap and October 29 decision deadline are unchanged.

I notified the existing Fable session of the execution go-ahead. It is preparing
the guard-rule extraction; review so far finds the risk formula and two-pass
filter structure preserved. Final diff and tests remain to be reviewed.

## Independent benchmark audit

[audit_v36_bench.py](../astra-submissions/tools/audit_v36_bench.py) provides:

- Exclusive pre-launch pinning of the three ZIPs, exact 40/32/32 queue, seeds,
  referee and the external Misty environment; it cannot overwrite existing pins.
- Validation of every `(matchup, pair, color)` job, score orientation, seed,
  archive hash and effective environment. Missing/unknown or duplicate jobs
  cannot produce a passing gate.
- Replay board/observation/terminal checks against the referee, all recorded
  clocks, final clocks and both opponent-specific median-clock comparisons.
- The frozen score thresholds and combined direction D, with whole-pair
  bootstrap uncertainty. Misty resampling keeps both candidates' colors together.
- A run receipt check for the 12-hour cap and attempted/failed job counts.

It is read-only except for its own pins/report output and runs no bots. A passing
local screen remains separate from source/fresh-data gates and arena strength.

Validation: all **15 integrity tests passed**. Three superseded diagnostic games
also passed the real replay check: 67, 87 and 63 frames respectively. These are
checks of the auditor, not extra evidence promoting the superseded candidate.

### Fable integration contract

Before launch, from the project root:

```sh
.venv/bin/python astra-submissions/tools/audit_v36_bench.py freeze \
  --queue FINAL_QUEUE --direct DIRECT_MATCHUP \
  --candidate-misty CANDIDATE_MISTY_MATCHUP \
  --baseline-misty BASELINE_MISTY_MATCHUP --out INPUT_PINS
```

After or during the run:

```sh
.venv/bin/python astra-submissions/tools/audit_v36_bench.py audit \
  --pins INPUT_PINS --run-receipt RUN_RECEIPT --out AUDIT_REPORT
```

The receipt uses `queue_sha256`, `state` (`running`, `complete`, `wall_cap` or
`failed`), `started_at`, `finished_at` (UTC or null while running),
`attempted_jobs` and `failed_jobs`. Count attempts when started, not only when a
scored row is written. All unknown results must remain recorded; never silently
reuse a pair ID after an error. A stopped or incomplete run cannot pass.

The existing scheduler silently skips `result="*"`; its count-based pair
allocation can then retry/overwrite a job. I raised this before launch. Fable
is to fix recording/scheduling or agree an audited runner; Astra is not changing
the shared runner or launching a competing experiment.

## r3 review and smoke update

The final r3 ZIP is frozen at SHA-256 `5cdbb9caf8a3c990b63f3338a8501638d746bdf9a5d573f972c3325905e3cf60`.
All 19 source/header members match mist-c `ff89313`; Stockfish/history bytes
match v35. The immutable [input pins](../astra-submissions/analysis/v36-execution-20261027/input-pins.json)
also bind the queue and external Misty environment. See the independent
[r3 review](../astra-submissions/analysis/v36-execution-20261027/review-r3.md).

Both-color smoke completed at 01:39:08 UTC: 1W–1L, no protocol/time failure,
candidate clocks 35.89/24.70 seconds. Astra checked all 194 replay frames against
the referee. These games are outside the strength gate. Combined runner/auditor
tests passed (19 tests, 3 subtests); the auditor alone now has 16 tests, including
an active in-flight job correctly classified as pending.

Fable fixed failure-row recording, per-color deadline checks and fresh-builder
selection issues. Final pre-launch review requested replacing the initial
1,200-second per-game timeout, which is shorter than a legal long 180+2 game.
This is evaluation infrastructure only; no additional candidate behavior is
being introduced. After the complete gate-1 receipt and runner correction,
Fable launches the frozen 104-game gate under Henry's existing go-ahead.

### Launch confirmed

Fable's final runner correction is `63f7265`; the complete source/runtime
receipt is [gate1-receipt-r3.md](../fable-submissions/analysis/v20-material-guard-20261027/gate1-receipt-r3.md).
Astra reviewed both and independently passed **20 tests, 3 subtests**, including
actual cleanup of a grandchild process in its own session. The per-game limit
issue is resolved without changing the candidate ZIP.

Gate 3 started **October 27, 01:40:52 UTC** on cores 2–3 and 4–5; the hard stop
is **13:40:52 UTC**. Astra observed two started jobs and no failures. The
[launch audit](../astra-submissions/analysis/v36-execution-20261027/launch-audit.json)
reports no invalid inputs and correctly remains incomplete. Pre-launch review
passes; fresh-data and playing-strength gates are pending. Fable owns the run
and fresh construction after 11:30 UTC. No additional behavior experiment,
GPU job or automatic arena upload is authorized by this launch record.
