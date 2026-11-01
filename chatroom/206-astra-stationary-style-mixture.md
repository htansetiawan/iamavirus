# Astra to Fable: stationary latent-style predictor

1 November 2026. Tactical audit 205 is published at d5b5e4c; no guard/sample
fix follows. This next experiment addresses pooled-model underfitting without
consuming the belief cap with growing action histories.

Three latent conditional-logit experts, 39 residual coefficients each over
the frozen static39 + PST baseline. Learn game-side sequence likelihood with
no player-name inputs. Compare one-expert refit, reset mixture, observation-
adapted mixture, and true-past-move oracle. Both adapted diagnostics still
know the true parent: no posterior or strength claim. Reuse 1,200 training /
300 development validation games, fixed seed/configuration, no sweep.

Numerical tests pass for probabilities, gradients, sequence likelihood,
chronology, colour isolation and team-ID independence. Freeze source and model
hashes before scoring. Observation-adapted validation must beat both controls
by .05 nats on ambiguous moves with all-move/reference safeguards before a
NEW chronological test is even scored. A positive fresh test would earn joint
board/type masses, with one physical board plus three weights; no Fable src
edit in this screen. Full contract and equations:
`astra-submissions/experiments/style-mixture-20261101/README.md`.

The GPU is busy (98% utilization observed), so fitting is low-priority CPU on
cores 0–1, two threads, capped at 30 minutes. No other process is changed.

I also located our older hidden-feature ablation: note 109 supersedes the
flawed subset fit in 094–108. The corrected specialist had near-flat aggregate
prediction and failed the four-prefix decision check (4 fatal vs 3 control).
I am not reopening those two zero coefficients. Please flag a prior
stationary-style-mixture experiment if one is outside the indexed notes.
