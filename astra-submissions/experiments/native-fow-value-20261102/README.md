# Native FOW outcome value: attention teacher and compact student

Experiment 237, 2 November 2026. This is an offline feasibility study of a
structural replacement for the frontier evaluator. It follows the failed
234 expansion-allocation pilot, not another guard or prior adjustment.
Fable's playing source and every submitted ZIP remain unchanged.

The hypothesis is that a nonlinear model trained on actual FOW outcomes can
value concealment, king vulnerability and conversion better than ordinary
chess leaf scores. First compare predictive quality; only a positive result
earns native inference integration and a separately frozen playing test.

This is **off-policy outcome learning, not self-play RL, CFR distillation,
equilibrium value estimation or a demonstrated strength improvement**. A
board and both views do not identify either player's full observation history
or beliefs. Identical inputs can have different values under different
continuation policies. Wrong beliefs also remain wrong after this change.

## Why this is a distinct experiment

The earlier `m4-fog-value-screen-20261011` used 9,000 positions and a linear
logistic feature model. Fog features did not beat ordinary board features.
The king-hazard integrations also failed. Neither establishes the result of
a nonlinear outcome evaluator or teacher/student compression. They prohibit
presenting another linear hazard penalty as a new idea.

The baseline is the **archived v37 parent-position, depth-1 MultiPV child
value**, with its terminal overrides and missing-line fallback. It is not a
single-PV evaluation of the child. `leaf_collect.c` includes the archived
`gtcfr.c` and calls its original child builder on Stockfish's actual scores.
Every saved row includes its scores, both views and child state. A fresh
collector does not recreate the historical engine's transposition cache or
its searched frontier distribution; that limitation will stay explicit.

## Data and prevention of leakage

Source cohort: normal completed cached games between teams in the top 12 of
the pinned 2 November 05:28 UTC leaderboard snapshot. Team IDs select the
cohort; they are never network inputs. Training: 10–30 October, at most 25,000
games. Validation: 31 October, at most 2,500. Test: 1 November, at most 2,500.
This is a cached subset, and current membership does not prove historical
strength. Some public games have been inspected in previous analyses; the
later split is a temporal test, not an untouched external tournament.

Freeze source bytes and replay hashes first. Deduplicate complete move
sequences across folds, keeping the earliest occurrence. Select at most eight
nonterminal frames per game, ply >=8, using outcome-blind deterministic
stratification across its length. Deduplicate canonical feature states across
folds, keeping the earlier fold. Never replace a rejected/duplicate position
based on its outcome. Verify full trajectories and both views with the rules
engine; independently check the pilot with the course referee. Its three games
are excluded from the final dataset, including the one originally assigned to
each evaluation fold.

Inputs are square tokens: piece, visibility to each side, castling-right rook
flag and raw en-passant target; halfmove count is a separate scalar. Canonical
orientation is side-to-move as White (rank flip plus colour swap for Black).
The label is final score for the side to move (win 1, draw .5, loss 0).
No future move, result, team identity or true hidden history enters features.
At runtime these features would be computed on each hypothesized search world,
never supplied by the arena's hidden true board.

## Frozen model comparison

The machine-readable contract fixes the architecture and training budget.
An attention teacher (64 square tokens plus a global token, width 128, four
layers/four heads) is compared with a compact student consisting of summed
piece-square/visibility/castling/EP embeddings (128 units), clipped activation,
a 32-unit layer and one output. It is inspired by sparse NNUE features, but
does not claim incremental updates: visibility may change along whole rays.

Train the teacher and a direct-outcome student. Then train the same student
with equal outcome and teacher-soft-target loss, to test whether distillation
helps rather than assuming it does. Use per-game weighting, fixed seed and
hyperparameters; select epochs on validation only. Fit a two-parameter
logistic calibration of archived SF values on training data as another
control. Compare both raw and calibrated SF, not just the weaker baseline.

The selected deployable student must reduce game-weighted test log loss by
at least 2% against the better validation-selected SF control, with whole-game
bootstrap upper bound below zero for the log-loss difference, no worse Brier,
and no worse mean log loss in the prespecified hidden-king-threat subgroup
if it contains at least 100 positions from 30 games (otherwise report it as
insufficient). The teacher must independently clear the same overall 2%
threshold; a failed teacher cannot justify endless student tuning. Report all
arms and slices. No test-based refit or architecture change in this run.

The inference stage, if earned, requires <=1 MiB FP32 weights, <=25 microseconds
median unbatched native evaluation on one arena-like core, and C/Python parity
before any search integration. Quantization is deferred until an actual
quality/cost need is measured. Offline prediction is only a feasibility gate;
full-clock paired games and opponent checks still decide whether to package.

## Resources and sources

Use local ignored work files while the bulk drive is unavailable. CPU data
work owns reserved cores only. No existing GPU service is stopped; probe and
reserve a free GPU immediately before training. One training run, at most
one GPU-hour; eight epochs per model, fixed batch 512, AdamW and cosine LR.
No hyperparameter sweep. Preserve failed attempts and terminal receipts.

- [Obscuro, Appendix C.5](https://arxiv.org/html/2506.01242v2): deployed leaf method.
- [Student of Games](https://arxiv.org/abs/2112.03178): search, learning and
  game-theoretic reasoning can be combined. Its self-play and information-state
  machinery are not implemented by this offline experiment.
- [Stockfish NNUE documentation](https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html):
  sparse first layers and small CPU evaluators motivate the compact student.

No claim of implementing the full cited systems or of obtaining their guarantees.
