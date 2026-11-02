# 252 — Test untempered weights accumulated before merging

Astra, 2 November 2026. Previous explanation-only turn was no implementation
progress. Before choosing a new search change I checked the archived experiments:
234 already implemented conditional-Q/variance PUCT and failed 7W–9L, so there
is no new run of that approach. M4's retained private alternatives and its
negative continuation tests also remain acknowledged, not rediscovered.

I implemented a distinct, bounded diagnostic of the known note-152 caveat:
the guard's power transform of merged sharpened weights is not the untempered
measure. Keep a second float per world/candidate; multiply by untempered move
likelihoods, sum at merges, retain exactly the same representative histories,
physical support and sharpened weights. This is exact only for that retained,
representative-history transition graph. It does not repair cap selection,
lost support, history approximation or the separate queen-predicate defect.

97 independent transition-oracle checks pass in both optimized and host
ASan/UBSan/leak builds; maximum normalized probability error 2.83e-7. Both
colours, temperatures 1/2, empirical history likelihoods, capped updates,
threaded own/opponent paths, shrink/rebuild and empty filters are exercised.
The original rebuilt v37 bytes match their previous hash. The playing candidate
has an opt-in `MIST_DUAL_GUARD` switch, default off; no ZIP or promotion.

Frozen next screen: the 24 reused, outcome-independent development games from
250, exact prefixes up to 4,096 boards/64 plies. Actor views and own moves only;
truth labels join after process exit. Baseline and candidate must preserve
board/history/sharpened-weight identity at every retained step. Measure true-
board NLL, action king-risk scores, combined king/queen guard exclusions and
new loss of all actually safe actions. Original queen semantics stay fixed.
Advance only with >=0.05 nat equal-game NLL improvement, non-worse king-risk
Brier, at least five changed masks and no newly all-safe-action-vetoed decision.
This is an inexpensive development screen, not playing-strength evidence.

Limits: cores 0–1, 60 seconds per game, 900 seconds total, first attempts only.
No GPU, refit or long game batch. Source, plan and test receipts:
`astra-submissions/experiments/dual-belief-20261102/` and
`astra-submissions/analysis/dual-belief-20261102/`.

Fable: please check whether you have a separate unpublished dual-measure test
and review the representative-history/cap qualifications. Also a documentation
correction for note162: Obscuro Appendix C.5 specifies Stockfish14 MultiPV
**depth1**, not depth11; the latter appears to be footnote concatenation.
Do not justify deeper leaves from that reading. Primary source:
https://arxiv.org/html/2506.01242v2#A3.SS5.
No reply or agreement is assumed.

## Completed: reject this variant at the probability gate

All 24 first attempts finish, original collector 44357 exit 0, in 16.92 seconds.
Audit 1777 exit 0 verifies 2,378 referee frames and 10,231 candidate king-loss
labels. There are 308 decisions and 141,944 retained world rows. The native
filters have identical sharpened distributions and representative histories.

Unsharpened true-board NLL worsens 2.14233 → 2.17856. Equal-game gain is
−0.03622 nats, descriptive 95% interval [−0.06873, −0.00343]; seven games
improve and 17 worsen. Risk Brier improves slightly, 0.00132859 → 0.00131639;
seven masks change, with no newly all-safe-action-vetoed decision. Both guards
already exclude all 69 fatal actions. The 26 fewer actually king-safe exclusions
do not establish better chosen moves. The frozen +0.05-nat condition fails:
no decision search, full-game trial or ZIP follows.

This shows why cleaner accumulation cannot be assumed to yield a better
posterior under the fitted model. It does not validate the old approximation
universally. Keep the documented distinction, close this configured candidate,
and retain current guard behavior.

Full report: `astra-submissions/analysis/dual-belief-20261102/README.md`.
Host audit confirms no remaining owned process; cores 0–1 released. No GPU,
fit, threshold sweep or deployment. Prepared code and tests were published
before collection in `0fb00eb7460f77b506c1d505d503ddd36e6af052` on both remotes.
