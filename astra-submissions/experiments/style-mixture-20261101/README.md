# Stationary style mixture: predictive screen

1 November 2026. This is an isolated model experiment, not a submission.

The pooled move model averages different habits. Test three latent experts
whose identity persists for one game-side. Learn the experts without player
names or hand-labelled strategies. Each expert adds 39 coefficients to a
shared frozen static39 + piece-square model. Training maximizes the marginal
likelihood of complete game-side action sequences:

```
p_z(a | B) = softmax_a(base(B,a) + delta_z . features(B,a))
loss = -sum_sequences logsumexp_z(log prior_z + sum_t log p_z(a_t | B_t)) / N
       + 0.5 * 0.001 * sum(delta_z^2)
```

Normalize over all legal actions. No conditioning the training denominator
on the next observation. Compare the frozen static baseline, a one-expert
residual refit, a three-expert mixture reset each move, a mixture adapted on
previous observation classes, and an explicitly oracle mixture adapted on
previous true moves. No current/future observation enters the prediction;
the observation class is used afterward to update the next prediction.

The observation-adapted diagnostic still knows the true parent board at
every step. It is NOT a deployed filter or a policy test. Distinguishing this
from the true-action oracle is necessary but does not remove that limitation.
If it succeeds, the actual filter must propagate joint board/type masses:

```
w_next(B', z) = sum_(B,a -> B') w(B,z) * p_z(a | B) * consistent(B', view)
```

Store one board and a fixed three-component mass vector; merge histories by
componentwise addition, cap by marginal board mass, then normalize. Unlike
the earlier recent-action model, this requires no growing history/context
entries. Search can use the marginal board weights. The style affects belief
weighting only; it does not yet model exploitable responses inside CFR.

## Frozen choices and stop rules

- Reuse the temporal-prior experiment's 1,200 training games and 300 validation
  games. These are development data already used for another model family;
  explicitly label results accordingly. Use only the 39 static features.
- Fixed three experts, seed 11012027, residual initialization N(0, .05),
  uniform initial priors; train priors jointly. L2 .001, L-BFGS at most 120
  iterations / 160 evaluations, one start. No seed or coefficient sweeps.
- Train a one-expert residual control with the same features/regularizer.
- Freeze all model hashes before validation. Advance only if the observation-
  adapted mixture beats BOTH static and one-expert control by >= .05 nats on
  ambiguous moves, loses <= .005 nats over all moves, and has nonnegative
  ambiguous gain on pooled Instructors/duck/HYPOTHERMIA. Report reset and
  true-action-oracle arms regardless; do not substitute them for this gate.
- If validation fails, close this configuration without test evaluation or
  filter implementation. If it passes, freeze a new 300-game chronological
  test from 1 November, deduplicated/excluded against prior experiment
  manifests, before scoring. Require a positive whole-game bootstrap lower
  bound and the same all-move/reference constraints before integration.
- Numerical tests must check action normalization, no future leakage, the
  sequence-marginal/online-prediction identity, and independent finite-
  difference gradients. Leave the occupied GPU and other services untouched;
  CPU fit on cores 0–1, two threads, low priority, maximum 30 minutes.

This screen reuses existing extracted replay data. A failure rejects this
small stationary mixture, not all opponent adaptation. A positive predictor
result earns a posterior experiment, not an Elo claim or ZIP.

The research motivation is separating uncertainty about hidden state from
uncertainty about opponent strategy, as in
[Bayes' Bluff](https://poker.cs.ualberta.ca/publications/UAI05.pdf). That paper
studies poker; neither its results nor the exact-algorithm guarantees in
[Ganzfried and Sun](https://arxiv.org/abs/1603.03491) establish that this
approximation improves Fog of War chess.
