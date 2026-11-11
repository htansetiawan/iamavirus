# 348 — Defer likelihood work until a parent has a compatible successor

Astra, November 11. The exact attack and visibility build in 346 preserved
all outputs and cost 85.89% of v38 on the large-belief panel, missing the
85% aggregate gate. This follow-up implements item 5 of
[161](161-astra-performance-opportunities.md) as a separate change.

The updater still generates every legal move and checks the same view and
king-capture conditions in the same order. It computes the move likelihoods
once, on the first compatible successor of a parent. Scoring uses the
untouched parent and the full legal list as its denominator. Parent histories
and their counters, empirical blending, cap and sampler keep the same inputs.
The original eager updater and the exact 346 build are controls.

Repeat the 24-game stress panel to measure the incremental effect of the new
mechanism. Keep the original coverage, 85% total-time and tail gates. Require
at least 3% additional savings against the eager exact build in total and in
large-population updates. This is a development comparison on a known stress
panel. The score and technical result from 346 remain recorded separately.

The preflight matched all 216 rows in nine matched cases with the deployed
settings, the history table disabled, or the move model disabled. The frozen
57-pin plan covers 72 calls on cores 0–1.

[Frozen summary](../astra-submissions/analysis/deferred-prior-speed-20261111/plan-summary.json)
· [Source](../astra-submissions/experiments/deferred-prior-speed-20261111/run.py).

## Launch

Session `10788` started at 00:08:33 UTC after both mirrors verified
`2f112595`. The 343 compact replay remains live on cores 2–3.

## Result

All 72 traces completed. The independent audit matched all 6,984 rows across
the three arms. The combined engine used 84.50% of original v38's update
time and was faster in all 24 games. Deferred scoring used 98.42% of the
eager build's time overall and 98.56% on the 397 large updates. The 3%
incremental gate failed. The aggregate, median, p95, parity and coverage
checks passed. The incremental hypothesis stays closed. A separate playing
comparison can measure the complete engine directly.

[Result](../astra-submissions/analysis/deferred-prior-speed-20261111/result.json)
· [Independent verification](../astra-submissions/analysis/deferred-prior-speed-20261111/terminal-verification.json).
