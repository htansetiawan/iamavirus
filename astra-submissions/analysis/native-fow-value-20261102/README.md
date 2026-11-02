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
