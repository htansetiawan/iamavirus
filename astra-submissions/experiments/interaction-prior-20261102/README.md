# 228: compact nonlinear move priors from learned feature interactions

Question: can a small learned table distinguish tactical combinations that a
linear sum prices badly? Note065 records a winning rook check whose forward and
centre penalties outweigh its check bonus. Recent predictors did not beat the
actual v37 prior on surprise captures; more search alone does not repair those
weights. This test uses the existing per-world features, not another observable
policy, and does not enable the full-prior switch closed by 226.

For each legal action with existing features x and exact v37 logit z0, fit

    z = z0 + delta_theta dot x + sum_{i<j} W_ij x_i x_j
             + selected continuous-feature square terms.
    pi(a | world, previous own move) = softmax(z)_a.

Full uses the first 26 features; cheap uses the first 18. The two previously
zero-weight visibility features stay absent. A matched linear residual has the
same data, optimizer and base logits, but W=0. Thus a gain from merely adapting
to recent strong players is distinguished from a gain due to interactions.
These are supervised conditional-choice models, not RL or SSL. At runtime
sparse active-feature products and a few hundred float coefficients suffice;
there is no large neural network. Model probability quality must still earn
actual capped-posterior, decision and match gates before a submission.

Freeze 4,000 training games completed Oct20–Oct31, 300 validation games Nov1
00:00–10:00 UTC, and up to300 test games Nov1 20:00–Nov2 02:45 UTC (minimum150).
Use nine existing reference teams, all outcomes and a salted ID order. Exclude
the named fresh-taxonomy, 224 and 226 panels; deduplicate complete move sequences
across splits and those excluded panels. The v37 base was fitted through Oct31;
validation/test are later. This is not a claim that every training game is new.
For fitting take at most24 actor decisions per training game by salted ply hash;
validation and test use all actor decisions. No team ID, outcome or future state
is an input. Native reconstructed boards/views must match every recorded frame.

Fit full and cheap independently. Linear residual: ridge0.001. Quadratic
residual: ridge0.001 and0.01. Start residuals at zero, Adam learning rate0.03,
batch512,12 epochs, one fixed seed. Choose epoch and quadratic ridge on validation
NLL after own move eight, excluding the terminal self-capturable target moves
that cannot be transitions in a continuing belief. Train on all sampled moves;
evaluate all-move and early-game scores separately. Test stays unopened until
all models are selected and their hashes written. No architecture/test sweep.

Primary test uses the same empirical-history blend as v37 (min3, n0=4). Require
quadratic improvement over v37 >=0.05 nats full and >=0.03 cheap, both whole-game
bootstrap95% lower bounds >0; improvement over matched linear >=0.02 for both;
at least100 surprise captures and mean surprise-capture degradation no worse
than0.02 nats in either mode; no all-move NLL regression. Bootstrap resamples
whole games,2000 fixed draws. All conditions must pass to permit designing a
capped-filter test. Passing is not promotion or Elo. No threshold changes or
new games are appended after evaluation.

Native/Python scoring parity and zero-residual parity are required. Log all
validation curves and score all fixed baselines. Dataset lives in memory because
the external disk is mounted read-only; save immutable game manifests, source,
small coefficients and per-decision scores, not large feature/checkpoint files.
GPU only after a fresh idle check, two CPU cores, a45-minute combined bound,
no existing service stopped. Publish plan and executable source before fitting.
