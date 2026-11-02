# 252 — Preserve the untempered measure through board merges

The current guard uses `exp(logw / temperature)` as its flatter weighting.
This is a known approximation (note 152), not a newly discovered rules bug.
For histories with likelihoods p and q reaching one board, temperature two
stores p²+q²; its square root is not p+q. A board reached by many plausible
histories can therefore receive different relative weight in the guard.

This experiment carries a second log-weight alongside each existing board.
Opponent transitions add log likelihood without tempering; merges sum that
measure independently. The original sharpened weights, representative history,
ordering, cap selections and search samples remain unchanged. The representative
history model is still approximate: this does not retain every private history,
restore dropped states, or recover an exact Bayesian posterior after capping.
After a rebuild both measures restart uniformly over the same reconstructed
boards. Under capping, the second measure is conditional on retained support,
without an inclusion-probability correction. No stronger claim is intended.

Cost is one float per retained board and one float per generated candidate,
plus independent log-sum-exp merges. No new tree, fitted coefficient or GPU.
`MIST_DUAL_GUARD=1` selects this measure for the guard's flatter branch only;
the default remains the original power transform. The full engine is built
for inspection, but no match or release is authorized by this diagnostic gate.

First establish native correctness, legacy sharpened-distribution parity,
history-table and threaded paths, shrinking/rebuild behavior, and sanitizers.
The independent oracle enumerates transitions and accumulates double precision
likelihoods, rather than recovering them from the sharpened weights. Test the
algebraic counterexample and single-path equality explicitly.

Then reuse the 24 outcome-independent selected development games from experiment
250. Stop each prefix before more than 4,096 boards or 64 plies; no thinning or
rebuild in the scored corpus. Both measures share all physical hypotheses and
all transition likelihoods. Export every own decision and all view-legal moves.
True boards, future replies and opponent views stay outside the filter process;
join labels and independent course-referee checks only after exit.

Report equal-game true-board NLL, per-decision king-risk Brier/log loss, changed
guard exclusions, actual fatal actions excluded, and loss of all actually safe
actions. Queen risk retains the original v37 predicate, including its documented
limitation; changing it here would confound the measure comparison. King labels
are independently checked; queen risk is descriptive only in this screen.

Advance to decision testing only if the untempered measure improves equal-game
NLL by at least 0.05 nats, does not worsen king-risk Brier, changes at least five
decision masks, and creates no new decision with every truly safe action vetoed.
These are fail-fast development criteria, not an Elo test or calibration proof.
No threshold sweep or retry of failed collection. Limits: 60 seconds per game,
900 seconds total, exclusive cores 0–1. Preserve every first attempt.

Prior work: 234 already implemented the paper's Q/variance PUCT and failed
7W–9L; do not repeat it. 250's full-history mixture and 251's structural test
remain separate negatives. This change addresses summing two measures over
the *same* deployed transition graph, not another history-replication scheme.
