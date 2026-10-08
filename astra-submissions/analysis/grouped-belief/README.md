# Grouped prediction: correctness and first replay pilot

The 20,000-successor cutoff can discard whole posterior branches because they
occur later in population order. Analytic tests now reproduce that failure and
verify grouped resampling against independently computed posterior masses.
Correctness counts and source hashes are in `correctness.json`; the final
integration update is recorded separately in `integration-r3.json`.

The replay pilot used the **24 newest novel games** from the frozen 500-game
refresh, both seats and all outcomes. Selection, hashes and five arms were
recorded before observing results in `recent-pilot-design.json`. Each arm uses
48 seats, priors 1 and 2, seed 777 and 2,048 particles. All 480 runs completed;
each arm/prior covers 3,364 observation updates and 22 terminal king losses.
Only actor observations and recorded own moves enter the filter.

Results for the learned prior (2):

| Prediction / history | Truth held | Hidden Brier ↓ | Rebuilds ↓ | Terminal losses assigned zero risk ↓ | Transitions enumerated |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy / 0 | 1,728 / 3,364 | .21852 | 41 | 3 / 22 | 79.08 M |
| Grouped / 0 | 1,877 / 3,364 | .21290 | 41 | 1 / 22 | 26.72 M |
| Legacy / 1 | 1,707 / 3,364 | .22003 | 52 | 3 / 22 | 78.55 M |
| Grouped / 1 | 1,904 / 3,364 | .21146 | 38 | 1 / 22 | 25.13 M |
| Preconditioned grouped / 1 | 1,831 / 3,364 | .21251 | 40 | 1 / 22 | 25.35 M |

Grouping removed all successor-prefix truncations (legacy prior 2: 754 updates).
It assigned nonzero risk to the terminal losing moves in `gzbi50j4` and
`mutyxz6j`, with no new zero-risk terminal cases in this sample. All terminal
recorded moves were legal in every sampled particle, so unsupported moves do
not explain this result. The control and grouped hand-prior arms both miss
1/22 terminal threats; this sample does not establish a tactical gain there.

Paired bootstrap intervals cluster both seats by game. Grouped/history-0 truth
coverage rises 4.43 percentage points, 95% interval **−0.07 to +9.33**; the Brier
change's interval also crosses zero. Grouped/history-1 truth coverage rises
5.23 points, interval **+1.42 to +9.47**. Five variants and one seed make these
exploratory results. The terminal sample is especially small: the interval for
its zero-risk reduction reaches zero. Do not infer Elo or promote strict mode
from these averages; the older, larger fatal-move gate rejected strict mode.

Transition counts measure actual work avoided, independently of host timing.
Observed runtimes share a CPU with compilation and cannot establish an isolated
speedup. A fixed-node move-selection comparison and the established larger
fatal-move corpus are the next gates.

Reproduce the aggregation (verifies every trace and matched arm identity):

```sh
.venv/bin/python astra-submissions/tools/summarize_grouped_probes.py \
  --root /media/henrytan/seagate/iamavirus/astra/belief/grouped-current-recent24-20261008 \
  --output /tmp/grouped-pilot-results.json
```

`recent-pilot-results.json` includes all hand-prior results, paired intervals,
per-game terminal threats and input hashes. Large traces remain on Seagate.

## Actual hybrid decisions on the same pilot

The four-arm follow-up freezes the final r3 benchmark and the neural graphs from
Fable's repairs-plus-v4 archive. Each arm uses 400,000 nodes, one search thread,
history mode 0, book disabled and seed 777. All **70 decisions** comprise
48 initial decisions and **22 terminal losing decisions**; they must not be
reported as 70 independent fatal positions.

| Opponent prior | Prediction | Fatal choices | Avoidable fatal choices | Terminal positions survived |
| --- | --- | ---: | ---: | ---: |
| Hand | Legacy | 4 | 0 | 18 / 22 |
| Hand | Grouped | 4 | 0 | 18 / 22 |
| Learned | Legacy | 8 | 4 | 14 / 22 |
| Learned | Grouped | 6 | 2 | 16 / 22 |

Grouping changes four hand-prior moves without changing fatal outcomes. With
the learned prior it changes ten moves, saving `o3z99fug` Black ply 29 and
`mwixva2o` White ply 38, with no new fatal choices. These differ from the games
whose recorded-move risk improved in the belief probe: predicted risk and the
engine's selected move are different measurements. The hand prior remains best
on this small sample. Improved truth coverage alone therefore does not justify
switching the default to the learned prior.

`recent-action-results.json` pins inputs and contains every compared decision.
The broader gate completed on all **453 remaining novel games / 906 seats**,
excluding these first 24 games. Its selection is frozen in
`remaining-453-design.json`. There are 1,338 evaluated decisions: 906 initial
positions and **432 terminal positions**, of which 68 have no safe legal move.

| Opponent prior | Prediction | Terminal fatal choices / 432 | Avoidable fatal choices / 364 |
| --- | --- | ---: | ---: |
| Hand | Legacy | 165 | 97 |
| Hand | Grouped | 158 | 90 |
| Learned | Legacy | 160 | 92 |
| Learned | Grouped | 162 | 94 |

With the hand prior, grouping saves 36 positions and introduces 29 fatalities.
The paired fatal-rate change is −1.62 percentage points, with a game-bootstrap
95% interval of **−5.32 to +2.08**. With the learned prior, it saves 32 and
introduces 34: +0.46 points, interval **−3.24 to +4.17**. Switching between
priors is also inconclusive under either prediction method. All four reports
are saved as `remaining453-*-comparison.json`.

This larger decision gate does not establish an improvement. The hand-grouped
IAmAVirus-only subset improves 20→17 fatalities, but contains only 33 terminal
positions and its interval crosses zero. There are only two Duck terminal
positions in that subset; neither changed outcome. It cannot support a claim
about beating Duck. Wall times were recorded under shared host load, so they
do not establish an isolated speedup.

[The choice audit](choice-audit.md) separates missed threats from cases where
the engine knowingly trades immediate risk for its estimated future value.
A single predeclared follow-up doubled grouped particles to 4,096 while keeping
the model and search budget fixed (`density4096-design.json`). It completed with
**174 fatal terminal choices versus 158** at 2,048 particles: 21 saves and 37 new
fatalities. The paired change is +3.70 percentage points, 95% interval
**+0.23 to +7.18**. Avoidable losses rose 90→106/364. The corresponding report is
`density4096-comparison.json`; its cross-campaign comparison verifies identical
binary, model graphs, corpus, node budget and decision sampling.

This density arm fails the replay gate. Increasing the population changes the
belief and the sampled search worlds together, so the result does not isolate
a single mechanism or prove that a larger population is inherently worse.
These 453 games are now development data; reuse is explicitly not another
independent holdout. One seed does not cover resampling variance. No new arena
artifact has been produced, and the defaults remain unchanged.
