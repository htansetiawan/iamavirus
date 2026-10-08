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
  field checks. Only elapsed time is excluded.
- The complete action control also matches all 1,338 previous grouped-control
  decisions in every logged JSON field, including 158 fatal choices among 432
  terminal positions. `action-control-parity.json` records that check; the
  frontier action arm has also completed.
- All 480 full diagnostic runs completed, with immutable input hashes checked.
- `comparison.json`, `runtime-parity.json`, `correctness.json`, and both build
  receipts retain the results and source/binary provenance.

The actual hybrid action gate completed with the predeclared
[`action-design.json`](action-design.json): cap 0 versus 8,192, same frozen
453-game development set, both seats, 400,000 nodes, one thread, seed 777,
the same repairs-v4 neural graphs and no opening book. It evaluated 1,338
decisions, including 432 terminal positions. The 906 initial positions are
excluded from the reported terminal fatality rate.

Terminal fatal choices increased **158→164**, with 26 saved and 32 newly fatal
decisions. The paired rate difference is +1.39 percentage points, 95% interval
−2.08 to +4.86. Among 364 terminal positions with an escape, avoidable fatal
choices increased 90→96. This is inconclusive evidence, not a successful
action gate. The candidate remains default-off and is not promoted to a
clocked strength test on these results. Total process time increased
219.1→320.6 seconds on the shared host. These are forced-history decisions,
not complete games or an Elo estimate. See `action-comparison.json`.

A follow-up diagnostic replayed the 58 changed-fatality cases under both
beliefs, measuring both selected moves: 116 probes. Their risk counts agree
exactly with the engine's logged risk permille, and their truth labels agree
with the action comparison. Under the candidate belief, **19 of the 32 newly
fatal choices have higher predicted king-loss risk than the safe move chosen
by the control**. Eleven instead rank the fatal move safer, and two see no risk
in it. Thus posterior support is only part of the problem; selection can also
override useful risk evidence. This selected-case diagnosis does not establish
that always choosing minimum risk is a stronger policy. The next diagnostic
checks whether those safe alternatives reached the matrix and what caused the
final choice. `choice-risk.json` and `choice-probe-build.json` retain provenance.

That row trace is now complete for the three largest risk disagreements:
`hilbnfl9` Black ply 29, `fj3af3mp` Black ply 77 and `tu75n4ra` White ply 58.
Every safe comparator was present in the matrix, and all six reproduced
decisions match the original binary's records. `selected-rows/report.json`
contains the existing rounded trace. A separate diagnostic build preserves
those decisions and prints exact strategy probabilities: `e8d7` receives
51.37% versus 10.76% for the selected fatal `a8b8` in the first case; the last
case assigns 99.93% to fatal `b2d4` and only 0.012% to safe `b2c1`. The row's
combined risk charge is not its immediate king-loss probability: hidden-threat,
material and repetition terms also enter. Search payoffs include future threats.

The [frontier/posterior experiment](../../candidates/frontier-posterior/README.md)
now tests the interaction between retained belief support and chance-weighted
root selection without changing those safety prices. The three inspected cases
remain mixed under the new selectors. They are correctness/diagnostic examples,
not an improvement claim or evidence that immediate survival always wins later.

Large immutable outputs remain on the authorized Seagate drive:

- `belief/weighted-frontier-pilot24-20261008/`
- `belief/weighted-frontier-full-20261008/`
- `belief/weighted-frontier-action453-20261008/`

All paths above are relative to `/media/henrytan/seagate/iamavirus/astra/`.
No ZIP was created and no arena default changed.
