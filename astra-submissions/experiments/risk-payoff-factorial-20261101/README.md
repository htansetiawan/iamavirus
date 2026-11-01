# Separate probability calibration from the legacy root-loss penalty

1 November 2026. Follow-up to the negative calibrated-root screen. No engine
source, binary, learned coefficients, guards, history table or evaluator has
changed. This experiment reuses the hash-pinned binary and source from
`../calibrated-root-20261101/`; `origin.json` records its provenance.

The previous integration retained L=-2, which v35 introduced to compensate
for underestimated hidden danger. A calibrated probability and that doubled
loss may be overlapping corrections. This is a hypothesis, not an explanation
established by the earlier null result.

## Frozen arms

| Arm | Engine | Risk treatment | Root loss |
|---|---|---|---:|
| v35 | Immutable reference ZIP | Original sampled loss | -2 |
| raw2 | Patched binary, calibration off | Original sampled loss | -2 |
| cal2 | Patched binary, mixture on | Calibrated larger-belief risk | -2 |
| raw1 | Patched binary, calibration off | Original sampled loss | -1 |
| cal1 | Patched binary, mixture on | Calibrated larger-belief risk | -1 |

L=-1 is the game's ordinary win/loss payoff; -2 is the existing compensation.
No intermediate values, new thresholds or curve fitting are permitted in this
experiment. The treatment includes both the larger-belief estimate and its
calibration; a positive result would not isolate the fitted curve alone from
the change of estimator.

The native terminal-payoff oracle is extended to both loss utilities, both
colours, all integration modes and the previously checked edge cases. Optimized
and ASan/UBSan runs must pass before the screen. Other unchanged correctness
checks are reused through their recorded hashes.

The development screen reuses the inspected 51 decisions, seed 11012026 and
2.5-second cap. All five arms are rerun, rotated per case on exclusive cores
0–1, with no ground truth supplied to the engine. This is 255 runs, not a fresh
held-out evaluation. No recorded reply is followed after a changed move.

Acceptance is fixed before launch: cal1 must reduce combined adverse events
by at least three versus immutable v35, reduce fatalities, and not increase
material or queen losses. It must also have fewer combined adverse events
than raw1 without increasing fatalities/material/queen loss. Inspect raw2
versus v35 to distinguish feature-off variability. Any protocol/legality error
stops the screen. Runtime and node counts are retained, not inferred.

A positive screen earns an independent, newly frozen game cohort and then
actual games if confirmed. A null closes this global-calibration integration
family; keep the calibrated curve as a diagnostic and move to a different
mechanism. No full-game lane, release ZIP or strength claim follows a null.
