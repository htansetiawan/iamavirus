# Attention and useful compression

The user's direction is better learned representations and useful compression,
not a requirement to use DC-AE. The goal is a stronger observation-history
predictor that fits CPU inference. A compact model which loses hidden attackers
is a failed experiment, even if it reconstructs the visible board well.

## Controlled comparison

| Arm | Encoder | Recurrent input | Shared parts |
| --- | --- | --- | --- |
| CNN control | Existing four residual CNN blocks, unchanged | 4,096 spatial values + 8 scalars | GRU256, policy, danger, belief, value heads |
| Attention | 64 square tokens, width 64, two pre-norm blocks, four heads; learned square position and geometric bias | 4,096 spatial values + 8 scalars | Same GRU and heads |
| Compressed attention | Same attention encoder, residual space-to-channel bottleneck | 512 latent values + 8 scalars | Same GRU and heads; spatial heads use decoded latent |

The geometry bias uses only public square geometry, including ranks, files,
diagonals and knight offsets. It begins at zero and is learned. It does not
receive privileged attack maps. Every actor input comes from the existing
observation/history feature builder. Truth remains in supervised targets.

The third arm has a real information bottleneck: 64×8×8 features become 32×4×4
and are decoded for the candidate and hidden-piece heads. There is no spatial
skip around the bottleneck. The recurrent state still carries history. The
8× figure counts intermediate feature elements only; it is not a model size,
compression of the complete history, or inference speed claim. Its smaller GRU
input projection is an additional capacity change and must be reported.

[DC-AE](https://arxiv.org/abs/2410.10733) motivates a fixed space-to-channel
path with learned residual projections. This is an adaptation to board
features, not a reproduction of its high-resolution image autoencoder. No
image reconstruction loss or diffusion model is needed for this experiment.

## Data and training budget

Freeze `data/manifests/v3.json` (content SHA-256
`6350501c86729a079fdd9b71d46493c63bf66dfebc5e44a74981b9ca3ec58a86`):
3,766 training games, 472 validation games, 469 test games. Preserve whole-game
and duplicate-trajectory splits. Both colors of a game stay together. Do not
touch the test shard during architecture selection. Record actual shard hashes
and source hashes in each run. Later corpus revisions are new experiments.

First prove shape, gradient, input-boundary, candidate-order and ONNX parity.
Then run a bounded pilot for the CNN and attention arms: same 1,000 updates,
seed 253, four sequences of 32 observation events per batch, AdamW at 3e-4,
weight decay 1e-4, gradient clip 1, full precision. Reconstruct the complete
prefix at sampled window cuts. Use the existing task loss weights and player
weights in all arms. Compare learning curves at 250/500/1,000 updates and
measure actual valid decisions and elapsed training time, not steps alone.
This shorter window/batch is a pilot choice applied equally to both arms, not
a claim to reproduce Fable's longer CNN training run.

The compression arm follows only if the attention representation is worth
keeping, or if an explicitly measured efficiency tradeoff motivates it. A
later teacher/student run may distill policy, hidden-piece and danger outputs;
that is a separate experiment, not an unreported change to this pilot.

## Quality gates

- Stop on label/input leakage, nonfinite loss or gradient, split overlap,
  recurrent event mismatch, or ONNX parity failure.
- Evaluate every selected held-out decision once, with full recurrent history.
  Do not replay the last event of short episodes to pad an evaluation group.
- Report policy NLL/accuracy, hidden-piece NLL separately from empty squares,
  per-piece recall and Brier, and natural-frequency danger Brier and recall at
  fixed false-positive rates. Break down by opponent and opening/middle/late
  phase. An all-empty classifier must not look like a good belief model.
- The 1,000-update pilot is a resource-allocation decision. Continue attention
  if it improves a primary task metric without a material tactical regression,
  or clearly improves learning/CPU efficiency with comparable quality. Show
  the paired game-level uncertainty rather than claiming Elo from loss.
- Before any danger veto, select a calibration/threshold on a separate
  calibration subset and assess it on held-out games. During these pilots the
  danger head remains diagnostic.
- Before release, require trained ONNX parity over complete histories,
  candidate/decision parity, two-core latency and 180+2 clock checks, the
  tactical replay gate, and color-swapped matches against the active archive.
  Compression earns promotion only with preserved tactical information and a
  measured resource advantage. No release merely because a new model exists.

GPU training waits for the current owner to release its lease and for the
actual device to be free. CPU development and checks use cores 2–5; Fable's
real-clock lanes keep cores 0–1 and 6–7. Large checkpoints and traces go to the
Seagate drive. All experimental source stays under `astra-submissions`.
