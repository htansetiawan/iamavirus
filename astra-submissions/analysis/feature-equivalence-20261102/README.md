# Feature-equivalence audit: real ties, limited evidence of a dominant bottleneck

2 November 2026. Completed diagnostic on the fixed 80 development games from
experiment 232. No training, new test access, runtime change or strength claim.

| Subset | Updates / games | Certified NLL floor | Parent-local floor | Existing baseline NLL |
|---|---:|---:|---:|---:|
| All | 810 / 80 | 0.02956 | 0.02904 | 2.05817 |
| Nontrivial updates | 536 / 80 | 0.03821 | 0.03764 | 2.65930 |
| Later nontrivial updates | 266 / 36 | 0.08776 | 0.08592 | 3.02168 |
| Surprise captures | 44 / 26 | 0 | 0 | 1.45639 |

Means weight games equally within each subset. There are positive feature
floors in 44 updates from 23 games, including 37 nontrivial updates from 22
games. Adding candidate source/destination/promotion makes this particular
bound zero everywhere. Zero means the relaxed bound is inconclusive; it does
not establish a perfect predictor or removal of genuine fog uncertainty.
The floor is only a lower bound, so its ratio to actual NLL cannot quantify
the fraction of our errors caused by missing features.

## Concrete witnesses

In duck game `vwf3eraf`, update at ply 34, the previous belief has one board.
The actual rook move h8c8 shares scoring inputs with 11 other compatible rook
moves, including a8b8, a8c8 and a8d8. Their observations agree. Any scorer of
these same 26 features, with the same history blend, assigns the actual
successor at most 1/12 probability. This is a representation limitation even
with an exactly known parent; it is outside the primary subset because that
subset requires more than one parent.

In Greek Gift game `4kawq4m3`, update at ply 30, 118 parents produce 1,030
consistent worlds. The true a8b8 transition is tied with seven alternatives,
including a8c8 and a8d8. Its feature-only probability ceiling is 1/8; the
baseline actual truth mass is about 0.00171. The six selected witnesses and
alternative transitions are preserved under `witnesses/` and `witnesses.json`.

The proof groups only identical candidate features/base logit, complete
legal-action normalizer multisets and active history counts. Posterior truth
mass is a weighted average of group truth fractions, bounded by their maximum.
The parent-local version uses count ratios within a parent and is independent
of incoming weights on this same support. Neither bound applies to changed
support or changed history counts. See the pinned source README for equations.

## Validation and interpretation

All 4,050 fixed-model/update checks respect the bound. Maximum within-group
log-probability variation is 8.88e-16. Independent reconstruction reproduces
all 810 bounds within 4.45e-16, including all original feature bytes and the
augmented move/state export. Independent rules checks validate 46 witness
transitions in six games. The main audit took 19.70 seconds and its launcher
records exit 0. The review's final artifact is verified; its original tool
handle was lost at compaction, so no review exit code is invented. A host
process check confirms no matching audit/review process remains. No rerun.

These examples establish artificial feature ties. They do not establish the
main barrier to stronger play: the average certified floor is modest, no
surprise example has a positive floor, and the bound can be loose. Fable's
already-tested v23 piece-square/observation model is relevant prior evidence:
it scored 52W–1D–47L against v35 over 100 games (paired interval 0.43–0.63),
despite better posterior metrics. We should not duplicate that experiment or
claim that adding coordinates is a new breakthrough.

This closes 233. Further prior fitting is not justified by this audit alone.
The next investigation should target decision/search quality, with the
posterior and guard support held fixed where possible, before any bulk teacher
training. No new ZIP or release number is reserved.

Plan SHA: `5047d133c6977a02e8eac90c28f1f9d027749ad26442121650da8c7d0d872a26`.
Pre-run published commit: `f8124a029c7b6d214a532982bc77e5d9c09eae5b`.
Results, independent review, execution and recovery receipts are adjacent.
