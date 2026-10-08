# Actual capturer targets and the queen-capture belief audit

All **240 selected queen-loss decisions** in Fable's frozen
`data/queen-loss-seats.txt` now have targets recovered from cached public
replays. No records were rejected. These identify the **recorded next-ply
capturer**, including its piece type, starting square, capture move, and whether
it was visible before or after our move. The subsequent native audit found that
**12 captures immediately won the game for us**, because the opponent exposed
its own king while taking the queen. Keep these as positive counterexamples to
an indiscriminate queen-safety penalty, not harmful-loss targets. The dataset
name describes how the examples were selected; it does not establish that every
queen capture was a bad decision. No new arena release is implied.

The frozen corpus and JSONL targets are under
`/media/henrytan/seagate/iamavirus/astra/belief/queen-capturer-targets-20261008/`.
The checked-in `targets-manifest.json` records source, tool and output hashes.
Run `tools/prepare_queen_targets.py` with `--corpus`, `--cache` and a new
`--output` directory to reproduce the extraction. The tool refuses to overwrite
an existing output directory.

| Arena version | Events | Capturer unseen before our move | Newly visible after our move | Our queen moved |
| --- | ---: | ---: | ---: | ---: |
| 4 | 105 | 85 | 63 | 68 |
| 10 | 52 | 44 | 32 | 36 |
| 13 | 37 | 34 | 32 | 27 |

These are server-assigned arena versions. They are not Astra/Fable archive
labels. Older versions supply the remaining 46 events.

`ply` is the zero-based **decision position before our move**. The original
replay frame at `ply` is the observation available to us; `ply + 1` is after our
move; `ply + 2` is after the opponent captures our queen. The manifest's `early`
count means `ply < 30`. It must not be compared directly with a count defined
using the later capture frame: this boundary accounts for 3 versus 2 early
events in version 13, for example.

The extractor verifies the game ID, side-to-move parity, complete recorded move
prefix, three frame indices and encodings, queen occupancy before the capture,
capturing piece occupancy afterward (including promotion), and played version.
That first extraction did not independently replay the sequence through the
native referee. The completed probe below now does so.
Synthetic result/reason fields used to make the old harness visit these seats
are deliberately absent from the target output. They must never become outcome
supervision.

The native belief audit reports three separate quantities:

1. The particle mass on this exact capturer's piece type and starting square.
2. The particle mass on any geometric attacker of the queen after our move,
   which is the union metric in Fable's current `QueenCapturerMass` harness.
3. The mass of worlds where our move is available, our king survives, and the
   opponent can capture the queen while its own king survives.

An occupied square, a geometric attack, and a surviving capture are different
events. In these rules a move that exposes its own king is allowed but loses
immediately; calling it "illegal" would hide this distinction. Exchange
profitability needs a further check and is not implied by any of these. Raw
counts are retained, and every mean in the report divides by the full
equal-weight population. Own-move support and own immediate king loss are
reported separately. No conditional denominator is silently substituted.

The probe reconstructs the actor's complete observation history. Only its
observations and recorded own actions enter `BeliefState`. Replay truth and
future capturer identity are diagnostic labels. The physical capturer is
followed backward through its earlier squares, including 30 rook-castling and
2 promotion transitions across this corpus. That future-informed trajectory is
never an inference feature.

These examples were selected because a queen was lost. Better true-attacker
coverage is useful diagnostic evidence, but calibration requires representative
negatives as well. The already inspected examples are development data; reserve
new games for confirmation and retain the king-fatality corpus as a regression
check before promoting a belief change.

## Completed first comparison

Frozen native source: `build/grouped-belief-r3`, based on root revision
`097eaecb56b31af1b26bab76587640e35859ac6b`. Both arms use 2,048 particles,
seed 1, hand prior 1, history mode 0, capture evidence and visibility deductions
enabled. Only prediction changes: legacy mode 0 versus grouped mode 1.
This is a belief-only experiment, not a search or move-selection experiment.

All **480 traces** completed without rejection. Native replay validated **10,859
unique game frames**, including both colours' observations and the full board,
through the actual capture. All 240 baseline union masses match Fable's existing
verbose harness within its three-decimal printing precision. A separate parity
check matches the old probe's population size, collapse state, survivor count,
and true-board support over 179 updates in three histories. Ten focused checks
cover six threat cases, including a geometrically valid capture that loses the
capturing king and a different piece making the same UCI capture.

| Diagnostic | Legacy | Grouped |
| --- | ---: | ---: |
| Mean exact capturer mass, all 240 events | .3677 | .3782 |
| Events with exact mass below .05 | 86 | 86 |
| Events with zero exact mass | 34 | 34 |
| Mean exact mass, 228 captures the opponent survives | .3487 | .3589 |
| Mean exact mass, 37 arena-v13 events | .1875 | .2044 |
| Mean mass on any true geometric attacker | .3978 | .4059 |

The paired game-bootstrap interval for the all-event exact-mass difference is
−.0170 to +.0386. The improvement is inconclusive. The surviving-opponent and
v13 breakdowns are also inconclusive. No promotion follows from this result;
the existing action gate likewise did not establish a grouped-prediction gain.
Intervals reflect games, not variation across particle seeds.

The baseline's 86 low-mass cases give a more useful diagnosis:

- 65 capturers were never visible to the actor before the decision.
- 53 cases had no complete particle collapse anywhere in the prefix.
- Only 10 last crossed below .05 during a collapse/rebuild.
- 26 last crossed below .05 after our own move. This combines `ApplyOurMove`
  and subsequent observation conditioning; the current probe does not isolate
  their individual contributions.
- 31 capturers had stayed on the same square for at least ten plies.

These categories overlap. Recovery-only changes cannot directly address the
majority of low-mass cases in this sample. Prediction quality, correlations in
the sampled boards, and loss of diversity under informative own observations
remain live hypotheses. Stationarity alone does not prove an incorrect prior.

One concrete example is `twlle83q` (arena v13 versus TA Baseline P): Black's
queen never moved from d8. In the legacy trace, mass on d8 was 284/2,048 at
ply 34, then fell to zero when the next observation retained only nine
particles. The grouped trace retained twelve particles at that same update,
all with the queen on d8, and ended at mass one. Neither trace collapsed.
Grouping fixes this individual example but fails others; the aggregate result
is the governing evidence. A rejuvenation method should address this loss of
diversity before the population becomes completely empty.

The 12 winning captures are enumerated in `winning-capture-cases.json`; every
case also matches the real replay result and terminal ply. For example,
`3grf5abt` ends after `a5b6 a7b6` at ply 108 with White/IAmAVirus winning.
This does not prove the offer was intentional or the preceding move optimal.
Keep the original 240-event primary report for provenance and report the
228 surviving-capture subset separately rather than silently changing the
benchmark denominator.

Artifacts:

- `grouped-comparison.json`: full counts, denominators, and paired intervals.
- `parity.json`: old-probe and Fable-harness comparisons.
- `probe-build.json`: source, compiler, binary, and test receipt.
- `/media/henrytan/seagate/iamavirus/astra/belief/queen-belief-audit-r1-20261008/`:
  frozen inputs, per-ply traces, and completion journal.

## Existing learned-prior follow-up

The additional 240 traces also completed with no failures. This arm changes
only prior 1 to the existing 26-feature learned prior 2, retaining legacy
prediction and all other settings. No coefficients were fitted on this corpus.

| Diagnostic | Hand prior | Existing learned prior |
| --- | ---: | ---: |
| Mean exact capturer mass, all 240 events | .3677 | .4043 |
| Events with exact mass below .05 | 86 | 68 |
| Events with zero exact mass | 34 | 19 |
| Mean exact mass, 228 captures the opponent survives | .3487 | .3849 |
| Mean exact mass, 37 arena-v13 events | .1875 | .2550 |

The paired game-bootstrap interval for the all-event mass difference is
+.0074 to +.0665. The fraction of cases below .05 falls by 7.5 percentage
points, interval −13.75 to −1.25. The smaller v13 subset is inconclusive.
These are exploratory results from selected losses and one particle seed.
False alarms and the resulting moves are not evaluated by a positive-only
capturer-coverage metric. The previous 453-game king-decision gate found the
prior change inconclusive (165 versus 160 terminal fatal choices), and its
initial small pilot favored the hand prior. Improved coverage is sufficient to
motivate a clocked check, not to change the default.

`learned-prior-comparison.json` records the comparison. The existing training
script shuffles decision examples before its 90/10 split, so its validation
loss does not certify generalization to unseen games. Any new prior must split
complete games and duplicate histories, record overlap, and test downstream
belief and decisions on separate confirmation data.

## Clocked screening

The next experiment uses the same freshly built archive for both players:
Fable's recommended r10c hybrid, SHA-256
`2ae7ee3c6cce97ab788947414dd10976c28c43cf9a2c7eef88309e6b337d90ee`.
Its v1 model, engine and sampled opening book are identical. Only
`FOW_OPPONENT_PRIOR` differs: candidate 2 versus control 1.

The declared screening allocation is four colour-swapped seed pairs, starting
at 12000, at 180 seconds plus 2 seconds per move, on exclusive cores 3–4.
Seeds are shared by colour within each pair. The runner hashes the archive,
referee, model and compiled runtime; checks the runtime remains unchanged;
records each game immediately; and summarizes paired scores after all eight
games. This small screen does not by itself establish strength or authorize a
release. It tests whole-game and time-budget interaction on the current
recommended archive, rather than the older model used in the node-limited gate.

Runner: `tools/run_prior_clock_gate.py`. Match state and traces:
`/media/henrytan/seagate/iamavirus/astra/matches/prior2-vs-prior1-r10c-20261008/`.
Starting the comparison is not a result. No ZIP is produced or activated.
