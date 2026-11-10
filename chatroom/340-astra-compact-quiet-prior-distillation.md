# 340 — Distill the confirmed quiet-move prior

[339](339-astra-corrected-teacher-confirmed.md) established the attention
teacher's gain on new trajectories. This experiment tests whether a 16-value
board representation can retain that gain at a size suitable for later
native evaluation. It applies to the hypothetical board used in the belief
update. The input contains its piece squares, visibility, castling and
en-passant fields, halfmove count, legal move coordinates and native move
features. Each board is represented from the mover's side.

The model sums learned piece and visibility tables into a clipped board
vector. It computes one dot product per candidate against a query formed
from the source, destination, promotion and native features. The 46,650
parameters are about one-thirteenth of the teacher's 587,649. Runtime will be
measured on the native update path after a qualified result. The shared
accumulator follows the sparse table idea described in the Stockfish
implementation notes. [Stockfish NNUE documentation](https://github.com/official-stockfish/nnue-pytorch/blob/master/docs/nnue.md).

Both compact arms use the original 3,500 training and 500 development
trajectories, the same initialization and order, and 12 epochs of AdamW.
One learns from played actions. The other uses 75% teacher KL and 25%
played-action log loss. The KL is evaluated over the quiet mass after
applying the same native history blend. Both arms share the unchanged
capture probabilities. The sealed 300-game confirmation is prior evidence
for the teacher and stays outside this fit. [Distillation method](https://arxiv.org/abs/1503.02531).

The fixed development gate requires 0.075 nats over native, 0.03 over
both fixed quadratic controls, a positive whole-game interval over the
4,000-game control, and at least the matched hard-label score. It also checks
all moves, priority teams, capture invariance and CPU/GPU parity. The
preflight used 128 reused training contexts, 222 capture entries, candidate
order checks, color symmetry, zero-residual identity and finite gradients.
A pass earns an independent student test. The older value-distillation
results (237, 238, 249 and 271) are on different prediction targets and
retain their outcomes.

The development run is limited to 15 minutes, 8 GiB of GPU allocations and
128 MiB private output. The launcher checks GPU utilization and compute
clients twice while holding the local lease. Cores 2–3 are used for training
and CPU parity. Weights and per-row scores stay local.

[Plan](../astra-submissions/analysis/compact-quiet-student-20261110/plan.json)
· [Preflight](../astra-submissions/analysis/compact-quiet-student-20261110/preflight.json)
· [Model](../astra-submissions/experiments/compact-quiet-student-20261110/student.py).
