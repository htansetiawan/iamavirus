# Bounded residual on Stockfish: development screen

Experiment 239. No new holdout is scored in this screen. Experiments 237 and
238's opened tests are quarantined. Earlier linear fog-feature calibration
also failed; this is a nonlinear board-conditioned correction with a direct
Stockfish skip connection, not another linear feature fit.

Let z be 237's frozen calibrated SF log odds. A flat or query-attention board
network produces a and b. Predict sigmoid(z + 2*tanh((a+b*clip(z/4,-1,1))/2)).
The added log odds are bounded by two: the correction changes baseline odds
by at most exp(2). The final two-output layer starts at zero, so the initial
prediction exactly equals the calibrated baseline. This neither guarantees
good decisions nor preserves the live arena's uncalibrated evaluator.
Any later integration requires a separate calibration-only control and must
leave terminal values untouched.

Use the same 193,517 training positions and 8,746 development-validation
positions as 237. Train both architectures from scratch for 32 epochs with
AdamW 1e-3, cosine schedule, batch 512, weight decay 1e-4 and gradient clip 1.
Outcome targets only; the teacher's broad advantage did not replicate, so
there is no teacher distillation. Seed 2391102; one 20-minute GPU bound.

Development gate declared before fitting: selected validation epoch/arm must
improve equal-game log loss by at least 2% over frozen calibrated SF, have no
worse Brier, and have no worse hidden-king-threat log loss when that slice has
at least 100 positions and 30 games. Missing size means incomplete, not pass.
Native payload <=1MiB, one-core median <=50us, probability error <=2e-5.
This validation set has guided prior architecture work: passing earns only
a fresh confirmation experiment, never deployment or a strength claim.

First verify neutral output, bounded correction, nonzero native arithmetic,
gradients and cost. No search source changes, arena upload, player-name input
or runtime hidden truth. Inputs describe hypothesized worlds. Large local
work is ignored while the authorized external mount is unavailable.
