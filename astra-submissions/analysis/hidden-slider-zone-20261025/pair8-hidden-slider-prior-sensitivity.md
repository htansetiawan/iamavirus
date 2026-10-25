# Pair 8 posterior sensitivity: global feature scaling is not a fix

This is a one-position intervention on the held-out pair-8 loss, not a
strength test. It changes only the `MM_HIDDEN_SLIDER_ZONE` coefficient in
`theta_full` of the hidden-slider-prior candidate; the bot uses the full prior
here because its belief has 392 positions. The observed true move `d8d1` has a
zone-overlap feature value of 1/8. In that model the full-prior coefficient
was 0.325, while `MM_CHECK_UNSEEN` had coefficient zero.

| Full-prior coefficient | Approx. multiplier from this feature | Chosen move | True board posterior |
|---:|---:|---|---|
| 0.325 (fitted) | 1.04× | `c7a8` | 0.00001, rank 154/392 |
| 18.421 (10× odds intervention) | 10× | `c7a8` | 0.00014, rank 14/392 |
| 36.841 (100× odds intervention) | 100× | `f1e1` | printed 0.00000, rank 20/392 |

At 10×, the posterior gives the true board more mass, but still chooses the
fatal knight move. It also rates the two true safe moves (`f1e2`, `f1g2`) as
about 0.919 king risk because other now-upweighted hypotheses attack those
squares. At 100×, it switches to `f1e1`, which remains attacked by the true
rook along d1–e1. The global feature multiplier therefore overweights many
other worlds and still fails to recover the correct tactical choice.

The feature's linear support is too weakly aligned with the tactical event:
the direct hidden check is represented mostly as an ordinary check, while the
separate unseen-check feature has zero fitted coefficient. Increasing one
global weight does not solve the posterior problem. The next useful research
step is a separately calibrated conditional likelihood for *newly hidden
direct attacks on the king*, evaluated on a game-disjoint risk corpus and
matched nonfatal controls. Keep this coefficient sweep rejected as a playing
candidate.

Detailed reproducible logs are in `pair8-white-hiddenprior-risk-replay.json`;
the 10× and 100× exploratory binaries were temporary and are identified by
hash in `pair8-hidden-slider-prior-sensitivity.json`.
