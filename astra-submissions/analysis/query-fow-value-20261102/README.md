# Compact query attention: feasible inference, failed overall value gate

2 November 2026. **No search integration, full-game trial or arena ZIP.** The
four-query student fits the native CPU budget and predicts hidden-threat
outcomes better, but it does not beat calibrated Stockfish over the complete
fresh holdout. The larger teacher's earlier overall gain also fails to
replicate on this broader set. Keep both results together.

The contract and verified holdout were published to both mirrors at
`e3460197046e4740c5ac93aa8ea6164f369ca4fc` before fitting. Plan SHA-256:
`d83bb9bf7539c844158c97edb024760e2da86817dd71940476b84983cefb38b8`.

## Implementation

64 square tokens, width 32, four queries, two attention heads and two rounds.
The first two queries include own/enemy king embeddings. Each query attends
to all squares; feed-forward layers have 64 units. A pooled board vector and
the four normalized queries feed the value head. This preserves interactions
between pieces without the teacher's 64-by-64 self-attention at every layer.

Shared linear key/value projections fold into embedding tables at export.
Native C inference sums table entries, uses stable softmax and fixed stack
arrays, and requires only libm. There are 64,481 trainable parameters; the
folded FP32 payload is 561,028 bytes. Both untrained seeds and all 9,554
trained-model test inputs pass PyTorch/native comparison. The selected model's
maximum native-versus-CUDA probability difference is 8.62e-7; trained median
inference is 44.28 microseconds on one core. It meets the predeclared 50us cap,
not the 25us target. Feature construction and actual search are not timed.

Experiment 237's original 25us cap is unchanged. This separate experiment
allows roughly 1.42ms for 32 scalar child evaluations; that is a cost budget,
not proof of adequate full-clock search throughput.

## Data and controls

Reused 237 training: 193,517 positions; validation: 8,746. Its opened test is
quarantined. The fresh holdout selects 1,000 unused 25–30 October games and
263 games from 2 November by hash, without outcome filtering. All 237 games,
complete move trajectories and canonical input states (including the pilot)
are excluded; duplicates are removed across the new cohorts too.

Result: 9,554 positions in 1,260 games, with 7,566 in 997 older-unused games
and 1,988 in 263 new-date games. The older cohort is not a forward-in-time
test. All 120,844 source frames validate through the existing rules engine;
six independent-referee trajectories verify 506 frames, 46 exported states
and 1,520 parent actions. All rows pass feature/label/baseline/provenance and
disjointness checks. Baselines use the original parent-depth-1 MultiPV
collector and 237's frozen train-fitted calibration.

Three arms receive 32 epochs, identical examples/optimizer schedule and seed:
flat distillation, direct query prediction and query distillation. They do
not consume equal FLOPs or wall time. Distillation targets mix actual outcome
and the frozen teacher probability equally. Best validation epochs are 9, 18
and 28; query distillation wins validation before new-test prediction. One GPU
run, original 35456, exits 0 in 160.42 seconds. No fit retry or service shutdown.

## Fresh results

Equal weight per game; lower is better. Confidence intervals resample whole
games. These are off-policy outcome predictions, not equilibrium values or Elo.

| Model | Overall log loss | Overall Brier | New-date log loss | Hidden-threat log loss |
|---|---:|---:|---:|---:|
| Calibrated SF | **0.469824** | **0.139382** | 0.430723 | 0.269965 |
| Frozen teacher | 0.472111 | 0.144213 | 0.425039 | 0.235673 |
| Flat distilled, 32 epochs | 0.481546 | 0.146845 | 0.429818 | 0.279256 |
| Query direct | 0.482647 | 0.147246 | 0.429755 | 0.237116 |
| Query distilled, selected | 0.474285 | 0.144569 | **0.423854** | **0.231791** |

Selected-minus-baseline overall log loss: +0.004461, 95% interval
[-0.005577, +0.014424]. It misses the 2% gain and negative-upper-interval gates
and worsens Brier. New-date and hidden-threat point-score safeguards pass.
The overall gate fails; no criterion changes after opening the test.

The hidden-threat slice has 238 positions in 215 games. Its 14.14% lower point
log loss versus calibrated SF is a category-specific predictive result, not
a statistically established game-winning skill or a promotion criterion.
The teacher's overall difference is +0.002287, interval [-0.007742, +0.012287];
its earlier 3.44% improvement is not a robust general-replacement result.

## What this changes

Attention preserves more of the teacher's hidden-threat prediction than the
flat control under this schedule. Generic replacement of SF is unjustified.
Keep SF's ordinary-position evaluation as the reference. A future proposal
could learn a bounded residual on that reference, with ordinary-position
controls and sampled-frontier decision tests. It needs a new contract and
fresh confirmation data; no residual was fitted here, and this opened holdout
must not become another tuning target.

This is a concrete taxonomy use: locating a conditional benefit that an
overall average hides, while the overall gate prevents shipping a weaker
general evaluator. No tag frequencies multiply live belief weights or change
king/queen guard thresholds.

## Verification and preserved failures

Reviewer 84261 exits 0 and independently checks metrics, bootstrap intervals,
validation selection, three compact CPU/native prediction vectors and timings.
CPU teacher probability differences reach 9.44e-5 versus CUDA, consistent with
237; aggregate log-loss/Brier differences remain below 1e-5. That is a separate
teacher numerical check, not compact-model native parity.

Original native preflight 95759 failed because LeakSanitizer cannot run under
the sandbox's ptrace. Identical source 14666 passes outside it with sanitizers
enabled. Reviewer 27726 failed an exact exported-byte check: one-thread BLAS
folding differs by at most 2.39e-7 from the original two-thread export.
`export-thread-check.json` shows two-thread folding exactly reproduces both
payloads. The corrected reviewer uses two threads only for folding, then one
for inference/timing. Failed source and receipts remain; weights, predictions,
gates and training were never changed.

`holdout-evidence.tar.gz` preserves fresh arrays/native rows and metadata.
`model-evidence.tar.gz` preserves three checkpoints, FP32 exports, curves and
test predictions, with per-member hashes. These are research artifacts, not
deployable submissions. The frozen teacher remains in 237's archive.
