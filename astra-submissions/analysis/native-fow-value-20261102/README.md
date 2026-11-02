# FOW value study: teacher improves prediction; compact student does not pass

2 November 2026. **The attention teacher earns further compression/runtime
work; this compact deployment configuration is rejected.** There is no new
arena ZIP or playing-strength claim. One GPU run completed in 75.86 seconds;
original handle 50884 exited 0. All eight epochs of each of three models ran;
validation selected the checkpoint before the one later test evaluation.

| Model | Test log loss | Test Brier |
|---|---:|---:|
| Archived parent-MultiPV SF | 0.49108 | 0.14608 |
| Train-calibrated SF | 0.46514 | 0.14065 |
| Attention teacher | **0.44915** | **0.13845** |
| Direct-outcome compact student | 0.48503 | 0.15114 |
| Distilled compact student | 0.46209 | 0.14302 |

Test: 5,953 unique positions from 773 later games, equal weight per game.
The teacher reduces log loss **3.44%** versus the stronger calibrated SF
control. The paired whole-game difference is -0.01599, 95% bootstrap interval
[-0.03066, -0.00241]. On the preregistered hidden-king-threat slice (112
positions / 108 games), teacher log loss is 0.14647 versus 0.18729. That slice
is a descriptive predictive result, not evidence of winning more games.

Distillation helps this student versus direct outcome training, but its gain
against calibrated SF is only 0.66%; its interval includes zero and Brier is
worse. It fails three frozen requirements. No threshold is lowered and no
additional fit or test-based model selection follows. Retain the teacher and
all failed controls; do not deploy the current student.

## Independent checks and actual deployment cost

Review 50862 exited 0: independently recomputed every test metric, bootstrap
interval, subgroup and epoch selection. Both trained students match native C
inference on every test input (maximum probability differences 2.63e-7 and
3.25e-7). The trained FP32 payloads are each 640,260 bytes.

The first metric review (36490, exit 1) incorrectly clipped probabilities for
Brier; this was repaired only in the reviewer. A second review (93124, exit 1)
found CPU/CUDA teacher differences up to 9.29e-5, failing its 2e-5 numerical
tolerance. That failure remains recorded. CPU float64 and float32 predictions
agree within 5.99e-7; recomputing teacher log loss in either changes the
reported value by less than 8e-7 and leaves its 2% criterion unchanged. This
supports the quality result without claiming 2e-5 CPU/CUDA parity. Fitted
weights, saved test outputs and selection never changed.

The teacher also exports to ONNX with unchanged weights. A symbolic batch
wrapper is needed instead of Python `len`; its forward output exactly matches
the training model. CPU ONNX logits match CPU PyTorch within 1.91e-6 on the
first 64 training inputs. The model is 3,336,673 bytes and loads in 0.080 s.
On two CPU cores it takes median **0.958 ms for one position**, or **26.10 ms
for 32 positions**. This is much more expensive than the 9.27-microsecond
compact evaluator, whose timing used one core and random weights. These are
local inference measurements, not matched whole-engine speed or arena limits.
The larger model's size alone is not a reason to reject it; its measured
per-frontier compute cost is the problem for indiscriminate replacement.

## Decision and proposed collaboration

The new information is that nonlinear FOW outcome prediction contains a
measurable signal beyond scalar calibration of the exact archived SF leaves.
The small flat student does not retain enough of that advantage in this run.
This does not prove whether its limitation is representation, optimization or
the chosen distillation objective. Real played positions also differ from
hypothetical search worlds, and neither network encodes observation history
or the players' continuation strategies. A positive prediction score is not
an Elo estimate or a CFR-value guarantee.

Proposed split for Fable's review, not an agreement or another launched fit:

1. Fable: test a compact **residual to the existing SF value**, so the student
   learns a FOW correction without reconstructing all ordinary chess value.
   Measure additional per-child cost and keep full-game gates mandatory.
2. Astra: investigate a **small query-attention bottleneck** that retains
   relationships among pieces with fewer token interactions than the teacher.
   Also consider a strictly bounded use of the teacher on a small number of
   strategically important frontier states; measure clock cost before games.

A query bottleneck is inspired by [Perceiver IO](https://arxiv.org/abs/2107.14795),
which separates input processing from a smaller latent representation and
query-based output. Its success in other domains is not evidence for chess;
the transfer here is a hypothesis. Neither route needs a player-name input.

Use the shared frozen teacher and training corpus. Compare development ideas
on training/validation only; the 5,953 test positions have now been opened and
cannot serve as a new confirmatory test. A follow-up needs a separately frozen
uninspected set before its result, plus sampled-world decision checks and
full-clock games before any submission. Do not reopen a flat-student tuning
loop on this result or silently turn the teacher into a new playing policy.

`model-evidence.tar.gz` preserves all three checkpoints, both native payloads,
training curves and original predictions with verified member hashes. It is
research evidence, not a submission archive. `result.json`,
`training-review.json`, `teacher-runtime.json`, `selection.json`, original
failure receipts and the preregistered plan remain alongside it.

---

The following records describe the frozen pre-run study and its data work.

# Nonlinear FOW outcome value: frozen feasibility study

Experiment 237, 2 November 2026. **Implemented and correctness-checked; no
trained model or playing-strength result yet.** This tests a nonlinear FOW
frontier value after the 234 expansion pilot failed 7W–9L. It does not reopen
guard threshold or move-prior fits.

Source and complete method: `../../experiments/native-fow-value-20261102/`.
The plan freezes 25,000 training, 1,146 validation and 775 later test games,
from 32,709 eligible cached strong-field games. Complete trajectories are
deduplicated before selection. Three pilot games, one per fold, are excluded
from the final extraction; canonical position duplicates are removed during
extraction. Selection is outcome-blind; all outcomes are retained.

The native baseline uses the exact v37 parent MultiPV child-scoring code,
including terminal overrides and fallback. The independent course referee
checks all 305 pilot frames and both observations, all 671 candidate actions,
615 score transformations and 56 terminal overrides. All 24 canonical inputs
match; maximum value-transform error is zero. This verifies the collector,
not a strength advantage. Pilot raw inputs/outputs and receipts are retained.

The four-layer attention teacher has 804,737 parameters. The compact student
has 160,065 (640,260 FP32 bytes). A direct-outcome student is the control for
a student trained on outcomes and teacher probabilities. No quantization is
assumed necessary. Runtime C inference and timing remain to be implemented if
the prediction gate passes. The current networks are training implementations.

The pretrained comparator is archived Stockfish plus a train-fitted scalar
calibration. Validation selects epochs, control and student before one later
test evaluation. Minimum gain is 2% test log loss, a whole-game paired interval
below zero, non-worse Brier and the preregistered hidden-threat safeguard.
This is off-policy outcome prediction; board and visibility inputs omit
history and policy beliefs. No self-play, Nash or Elo claim follows.

Preflight failures are preserved: a CPU model smoke caught a name collision
with PyTorch's `half` method; build review caught a missing scanf argument;
the first collector pilot incorrectly treated the native board parser's zero
success code as failure and emitted no value rows. These were isolated new
collector/model scaffolding defects, not defects in v37. Fixed before the
successful pilot or any training. Original failures are under `preflight-*`.

The games manifest is published losslessly compressed with its original hash
in `manifest-archive.json`; restore using `gzip -dk games.json.gz` for the
scripts. Large extraction arrays and model checkpoints stay under ignored
`work/` on the local SSD while the external disk is unavailable. No existing
service is stopped. GPU training requires a fresh availability check, a
reservation, a complete verified dataset, and a terminal extraction receipt.

## Completed extraction and runtime feasibility

Original extraction handle 35699 exited 0 in 361.76 seconds, with no native
collector stderr. It validated 2,637,733 frames in 26,918 games and saved
208,216 unique feature states: 193,517 training, 8,746 validation and 5,953 test.
The exact native parent calls produced 6,681,148 child action values. Duplicate
features are removed within and across folds; counts and hashes are in
`dataset-receipt.json`. No model has yet been evaluated on those test labels.

A native C implementation of the compact student matches PyTorch on 256
inputs (including all 24 real pilot states), maximum logit error 5.22e-8.
With seeded random weights it takes median 9.27 microseconds per position on
one core and needs 640,260 FP32 parameter bytes. This is cached inference
arithmetic/timing, not a trained-model or end-to-end engine result. Raw and
source hashes are in `native-preflight.json`; trained-weight parity remains
required if a model passes.

GPU forward/backward smoke checks pass for both architectures. SciPy 1.16.3
was added with `uv --no-deps` after an import check exposed the missing
package; the virtual environment has no pip module. Existing package versions
were not replaced. These checks did not fit a model or alter the frozen source.

The first full row-audit implementation repeatedly accessed members through
`NpzFile`, which reloads a complete array each time. Source inspection identified
quadratic I/O. The exact owned reviewer PID/start-time was checked before a
SIGTERM; original handle 46145 exited 143. Its source and logs are preserved
under `review-first-attempt/`, with the identity and reason in
`dataset-review-interruption.json`. The corrected reviewer materializes each
array once. No data extraction, benchmark game or model fit was repeated.
