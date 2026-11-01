# Data-biased search: correct solver, opening-limited history coverage

1 November 2026. **No new submission, full-game trial or default change.**
The exact-history response model changes early decisions, but offers too little
coverage later to advance under the recorded contract. Preserve the tested
solver interface for a response model that generalizes to unseen histories.
This experiment does not establish that DBR is weak or that the changed
opening moves are better or worse.

## What changed

An isolated copy of the immutable v37 ZIP constrains an opponent information
set's policy to `c*q + (1-c)*free`, where `q` is the existing history table's
action frequency and `c=.5*N/(20+N)`. No match, fewer than three observations,
or any counted action outside the legal set means zero confidence. The
opponent optimizes the free part; our policy remains unrestricted. Belief,
Stockfish, guards, clock settings and root argmax remain the v37 settings.

The constrained player's regret is scaled by `1-c` and centered on the free
policy's value. This implements the local constraint of
[Johanson and Bowling, AISTATS 2009](https://bowlingmh.github.io/papers/09aistats.pdf),
not a game-level Restricted Nash Response coin. The full-game theoretical
guarantees do not apply to this truncated, sampled, last-iterate, purified
search. Sample counts are not a calibrated confidence model for changing
opponents; the confidence curve is one frozen experimental setting.

## Numerical evidence

- 60 normal-form matrix games agree with independent linear programs; maximum
  row value gap is 2.78e-16. Includes confidence zero and one.
- 180 iteration-level comparisons agree with the equivalent chance-mixture
  payoff transformation, including shared information sets and hidden worlds.
- Feature off is bit-identical to original CFR on 48 fixed-tree comparisons
  and 1,680 solver-array values across 20 reachable tree-growth steps.
- Five constrained Kuhn variants agree with independent 64-by-64 normal-form
  linear programs, including restrictions on both players across decisions.
- Ordinary Kuhn and AddressSanitizer/UndefinedBehaviorSanitizer runs pass.

These are solver correctness checks, not strength evidence. See
`numeric-tests.json`, `extensive-tests.json`, and `sanitizer-tests.json`.

## Frozen policy screen

Eight Nov1 v37 games, four per colour, selected by ID hash without outcomes.
The selection contains six losses and two wins against Strongly Invisible,
Crimson Fog, duck and Instructors. Four prefixes per game, own turns 1, 5, 9,
13. Original v37, patched-off and enabled each run at a 2.5-second search cap,
the same seed, rotated arm order, cores 0–1. Earlier own moves are forced;
the engine receives only its recorded observations and clocks. Full boards
and counterfactual labels enter only after each process exits.

All **96 distinct executions finish with exit zero and legal protocol moves**.
The independent C++ rules validate all 872 replay frames. None of the three
arms has an immediate king loss, a two-point loss under the bounded exchange
probe, or a four-point queen loss in these 32 selected decisions. There are
therefore no positive safety events from which to infer a guard improvement.
The probe excludes non-capture forcing continuations; it is not a search
oracle or a game outcome.

Enabled changes 9/32 choices relative to original; patched-off changes 1/32.
Eight enabled changes have at least one constrained information set. One
changes despite zero constraints, demonstrating remaining wall-clock search
variation. Do not attribute every move difference to the response model.

| Our decision | Positions | Any constrained opponent set | Mean first-reply coverage | Mean reach-weighted confidence |
|---|---:|---:|---:|---:|
| Move 1 | 8 | 8 | 99.77% | 0.49860 |
| Move 5 | 8 | 4 | 49.84% | 0.17037 |
| Move 9 | 8 | 1 | 11.33% | 0.00944 |
| Move 13 | 8 | 0 | 0% | 0 |

The one move-nine match concerns a possible search continuation. It does not
mean the actual opponent history matches the table. Coverage depends on the
searched worlds, hypothetical actions and current strategy. Each figure is
descriptive of this small panel; no Elo or population-rate inference.

## Independent actual-history coverage

Reconstructing the opponent's own observation/action hash over the complete
same eight games yields 431 decisions. Python hashing agrees with the pinned
native functions in 2,175 checks; eight move-codec cases include promotions,
castling and en passant.

| Opponent's own move number | Decisions | Supported histories | Recorded action also present |
|---|---:|---:|---:|
| 1–4 | 32 | 31 | 29 |
| 5–8 | 32 | 9 | 6 |
| 9–12 | 32 | 0 | 0 |
| 13–20 | 64 | 0 | 0 |
| 21 onward | 271 | 0 | 0 |

Thus all 367 actual decisions from move nine onward lack a supported entry.
This supports closing this exact-history-only implementation before full
games. More records alone do not guarantee meaningful middlegame coverage.
It does not rule out an opening-only benefit, which was not this experiment's
promotion claim. See `actual-history-coverage.json` for every decision.

## Provenance and recovery

Source, numerical results and plan were pushed and API-verified at `588246b`
before policy execution. The first original-v37 process returned valid
`ready` / `move d2d4`, but my parser expected bare UCI and stopped. The failed
decoding receipt and raw streams remain in place. `recovery-plan.json`
verifies and adopts that original result without rerunning it. The corrected
parser and recovery were published at `d117b66` before the 95 remaining
executions. `receipts-recovered.jsonl` contains exactly one row per planned
cell. The initial harness failure is not an engine fault or a hidden retry.

- v37 ZIP: `41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c`
- Original binary: `14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`
- Enabled/off binary: `02ecfd97a996a038f976bbcda0ec0e7330900fbb17ca1d8ca12bcec0fa0a0f8d`
- Stockfish and history hashes, source pins, replay/input hashes: `plan.json`.
- `summary.json`, `labelled.json` and each stdout/stderr retain the full result.

For reproduction, extract the pinned v37 ZIP to
`astra-submissions/experiments/stable-mix-20261101/build/base/` and run its
`build.sh` first. The experiment's `build.py` creates its own source copy and
links those baseline data/binary assets. Numerical scripts require NumPy and
SciPy (the host environment used SciPy 1.18.1); the replay harness uses the
project environment. Frozen input text is published. Recreating the initial
selection requires the recorded raw archive snapshot; do not silently select
new games or overwrite first-run receipts.

## Data and next question

A separate public refresh accepted 52 new replays from 60 listings, reused
eight cached games, and recorded zero final errors or quarantines. It did not
change the frozen panel or history table. No GPU was used; no other service
was changed. The GPU was free when inspected during this experiment.

The next modelling question is an **information-set-realizable response
policy**: predict actions from the acting side's permitted observation/history,
sharing one prediction across worlds it cannot distinguish. Evaluate beyond
the opening on chronologically held-out games and measure inference cost
before putting it into this solver. This is distinct from the previous
full-board transition priors, which need not be realizable by a player with
limited information. No new model has been trained or promoted here.
