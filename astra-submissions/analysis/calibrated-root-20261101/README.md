# Calibrated root-risk integrations: no promotion

1 November 2026. **Both variants fail the recorded development gate. No new
ZIP, full-game trial or deployment follows this result.** Better held-out risk
calibration has not yet translated into a better decision rule.

## What was tested

The same frozen 51 decisions from 25 v35 games against Instructors, duck and
HYPOTHERMIA: both colours, wins and losses, king/queen/material cohorts and
ordinary controls. Four arms, 204 completed runs, rotated order, seed 11012026,
2.5-second cap, exclusive cores 0–1. Only own observations, own forced moves
and clocks were supplied. Labels were computed after the process exited; no
recorded opponent reply was followed after a changed choice.

- **v35:** immutable reference ZIP.
- **Off:** new binary with the feature disabled.
- **Mixture:** `L*q + (1-q)*V_safe`, rescaling continuation utilities through
  tree growth and both players' regret calculations.
- **Residual:** `V_sample + L*(q-p_sample)`, replacing the sampled immediate
  loss component but leaving surviving mass unchanged.

The trained calibration curve was frozen. Guards, move model, history table,
Stockfish and v35's L=-2 root-loss utility were unchanged. This is an inspected
development set, not held-out strength evidence. `development/pins.json`
records the exact archives, binaries, source hashes and acceptance rule.

| Diagnostic | v35 | Off | Mixture | Residual |
|---|---:|---:|---:|---:|
| Immediate fatal choice | 10 | 10 | 11 | 10 |
| Net material loss >=2 in limited exchange probe | 5 | 6 | 7 | 5 |
| Queen net loss >=4 | 0 | 0 | 0 | 0 |
| Capture with no king-safe response | 1 | 1 | 1 | 1 |
| Combined adverse event | 16 | 17 | 19 | 16 |
| Protocol errors / illegal choices | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

The combined event includes the first, second and fourth rows and is a union,
not a sum. Residual fixes one fatal choice and breaks one versus v35. Mixture
breaks one fatal choice, fixes none, and adds two material cases; one material
case also regresses in Off. Off changes nine moves despite the disabled
feature. Consequently these few flips are not a precise strength estimate.

Median paired elapsed ratio against Off is 1.0005 for Mixture and 1.0035 for
Residual; node ratios 1.0000 and 0.9955. There is no large cost signal in this
screen. Elapsed time includes forced-prefix reconstruction, not just search.

## Diagnostic traces, separate from the gate

Five print-only reruns are in `traces.json` and `traces/`; none are added to the
204-run comparison. Logging and wall-clock belief thinning can change choices.

- **i3xv2i71:79:** both variants again play fatal Kg6-h6 instead of safe Kg6-h5.
  The larger-belief risks are 1.026% for h6 and 1.666% for h5, mapped to 7.637%
  and 9.741%. The sampled risks had the opposite ordering (6.25% and 3.125%).
  Substituting the larger estimate favours the fatal move in this replay.
  A single realized board does not prove the correct posterior should assign
  probability one to its attacker; it identifies a mechanism to audit on
  fresh, representative cases, not a reason to memorize this position.
- **d28cm7j9:75:** Residual again avoids fatal Kh7-g7 by playing h5-h4. Its
  sampled loss risk for h5-h4 was 9.375%, versus calibrated 8.419%; correcting
  that sampled excess helps this decision.
- **71a47kt0:38 / zhjr2fp8:49:** the material regressions do not repeat in the
  traces. Relevant moves all have raw and sampled loss risk zero and receive
  identical corrections. The reruns choose safe alternatives. These are
  unstable outcomes, not established effects of a move-specific risk penalty.

## What this does and does not establish

The separate held-out calibration result remains valid. These integrations,
with the v35 guards and L=-2 retained, do not earn promotion. A monotone curve
cannot change the ranking of the larger-belief risk estimates. It also cannot
correct Stockfish's continuation values or reconstruct missing hidden boards.

There is an unresolved interaction: v35's doubled root-loss utility was itself
introduced to compensate for underestimated hidden danger (`gtcfr.h`). Holding
it fixed isolates the probability correction, but may retain overlapping
compensation. On the calibration test's historically played moves, raw mean
risk was 0.459%, fitted 0.909%; the old multiplier already roughly doubles the
raw immediate-loss contribution. This observation motivates a controlled
comparison, not a claim that it caused the measured regressions.

The principled next test is a fixed 2x2 comparison of raw/calibrated probability
and L=-1/L=-2, with an immutable-v35 control. L=-1 is the actual win/loss payoff,
not another fitted multiplier. No intermediate constants or curve retuning.
This should separate replacing the old compensation from stacking on it.
It remains development work and would still need independent confirmation and
full games. See `followup-plan.md`; it has not been launched by this report.

## Correctness and reproducibility

Five optimized/sanitized checks passed before the screen. An independent
terminal-payoff oracle verifies both colours, zero/all/partial sampled loss,
calibration endpoints, tiny survival mass, two generations of tree growth,
both players' best responses and 300 PCFR iterations. Entry-reward equivalence
and Kuhn poker remain covered. The initial sanitizer sandbox/ptrace failure
was resolved by running the same checks outside that restriction.

Source: `../../experiments/calibrated-root-20261101/`. `audit_gate.py` checks
all 51 cases occur once in each arm and reconstructs the recorded summary;
`audit.json` contains its acceptance decision and file hashes. No Fable source
or submission was edited.
