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
