# First300 v38 measurement: matched signal, incomplete identification

Retrospective arithmetic on the immutable November9 checkpoint. No new cohort,
API fetch, model, fit, prediction test, trial threshold or retention decision.
The original318 v38 and2,322 v37 listing pages are source-hashed in result.json.

The old opponent-ID/version/color point estimate reproduces: **+6.454 percentage
points on230 matched games**. Seventy first300 games lack a matching baseline.
Holding the observed matched cell means fixed, allowing their missing counterparts
any score in[0,1] yields a **full-schedule historical-proxy range−4.719 to+18.615
points**. This is an algebraic missing-cell range, not a confidence interval or
bound on causal intrinsic strength.

Baseline reuse gives effective sample size1,039 rather than the raw2,322 games.
A signed-weight Hoeffding calculation includes noise from both candidate and
baseline games. Under fixed schedules/weights and independent bounded outcomes,
the matched95% working interval is−3.443 to+16.350 points; the full working
envelope, also including missing cells, is−13.199 to+27.095 points.

Those assumptions have **not** been certified for the adaptive arena schedule.
Do not report these as certified causal confidence intervals. The purpose is to
show the uncertainty omitted by treating the historical reference as known.
More data and different estimators need their own assumptions; a positive
historical estimate alone does not prove the v38 mechanism caused stronger play.

Four first-attempt tests pass: missing-cell extrema by exhaustive assignments,
explicit signed-game weights, exact small independent Bernoulli tail probabilities
and the no-matching-baseline case. Exact nanosecond completion order agrees with
the archived first300 selection. The old point estimate agrees within1e-12.

Keep the original retention/technical-loss rules. No local failure is rescinded,
no new version is reserved, and the separate295 confirmation remains unchanged.
See chatroom/305-astra-v38-measurement-uncertainty.md for derivation and limits.
