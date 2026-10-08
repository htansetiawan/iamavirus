# Weighted frontier: better support retention, decision gate pending

The first bounded weighted-frontier experiment reduces complete belief
collapses and zero-support queen-capturer cases. It has not yet established
better moves or playing strength. Keep the feature disabled by default.

The [candidate design](../../candidates/weighted-frontier/README.md) retains
weighted joint states across observations separately from the engine's
equal-weight samples. Its first capacity is 8,192 stored states; both arms
supply 2,048 particles to the engine. Both use grouped exhaustive prediction,
the hand opponent prior, history mode 0, visibility deductions, capture evidence
and seed 1. This is a structural storage experiment, not a learned-model change.

The same diagnostic binary ran both arms on all 240 unchanged selected queen
captures. Twelve of these captures actually lose the opponent's king and win
the game for us; they stay in the primary comparison and are excluded only
from the separately labeled 228-event analysis. These are reused development
cases, not naturally sampled calibration data or a sealed test set.

| Measurement | Grouped control | Weighted frontier |
| --- | ---: | ---: |
| Mean mass on actual capturer's piece and square | .3782 | .3941 |
| Capturer mass below 5%, of 240 targets | 86 | 73 |
| Capturer mass exactly zero, of 240 targets | 34 | 17 |
| Complete collapses over 10,379 prefix observations | 142 | 69 |
| Observations whose engine samples contain true piece placement | 4,757 | 5,676 |
| Observe p95, milliseconds | 4.27 | 14.03 |
| Maximum Observe, milliseconds | 7.87 | 29.69 |
| Total process time over 240 prefixes, seconds | 67.3 | 83.9 |

The below-5% event fraction drops 5.42 percentage points, paired game bootstrap
95% interval −9.58 to −1.25 points. The mean-mass gain of .01595 has an interval
of −.00834 to +.04160 and is inconclusive. Surviving queen-capture probability
also has an inconclusive gain. A better occupancy estimate need not imply a
better capture-risk estimate or safer move selection.

Among the 228 captures that the opponent survives, low support drops 83→70,
zero support 32→16 and mean exact mass .3589→.3769. The 37 arena-v13 cases have
low support 22→18 and zero support 10→6. Those subsets are diagnostic; this is
one seed on previously inspected histories, with no adjustment for comparing
multiple metrics or subgroups. It does not measure performance against Duck.

The retained frontier has median 204 distinct states, maximum 8,192, and
requires capacity reduction at 925 observations. Median effective state count
is 113.8. Exact weights are retained only when the current support fits;
capacity reduction and recovery remain approximations. The true-piece-placement
metric ignores rule metadata and does not certify a complete legal history.

The first 24-case runtime pilot preceded the complete run. It was mixed on
support and took 6.86 seconds for control versus 9.01 for the candidate, allowing
the predeclared full comparison to proceed. The full timings above include
native replay validation and diagnostic scoring in process time. `Observe`
timing excludes applying our own move; process time includes it. Runs were
sequential on reserved core 2 of a shared host, not a clean hardware speed test.

## Verification and next gate

- All 5,508 native correctness checks pass, plus 10 queen-threat checks.
- With frontier capacity zero, all old diagnostic fields match the previous
  frozen grouped runtime across 240 games, 10,379 observations and 145,546
  field checks. Only elapsed time is excluded. This is belief parity, not yet
  full engine decision parity.
- All 480 full diagnostic runs completed, with immutable input hashes checked.
- `comparison.json`, `runtime-parity.json`, `correctness.json`, and both build
  receipts retain the results and source/binary provenance.

The actual hybrid action gate is now running with the predeclared
[`action-design.json`](action-design.json): cap 0 versus 8,192, same frozen
453-game development set, both seats, 400,000 nodes, one thread, seed 777,
the same repairs-v4 neural graphs and no opening book. It is expected to
evaluate 1,338 decisions, including 432 terminal positions; 906 initial
positions must not dilute the reported terminal fatality rate. Compare every
control decision with the previous grouped control before interpreting the
candidate. More data about retained possibilities is useful only if it helps
the decisions that consume them.

Large immutable outputs remain on the authorized Seagate drive:

- `belief/weighted-frontier-pilot24-20261008/`
- `belief/weighted-frontier-full-20261008/`
- `belief/weighted-frontier-action453-20261008/`

All paths above are relative to `/media/henrytan/seagate/iamavirus/astra/`.
No ZIP was created and no arena default changed.
