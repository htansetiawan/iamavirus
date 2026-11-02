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
