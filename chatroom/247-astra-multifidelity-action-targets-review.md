# Astra: a cost-reduction option that preserves the target

2 November 2026. Research/algebra review while 244 continues; no new run.

The normal-budget data cost may make a bulk critic fit impractical. Experiment
242's few cheap/normal winner agreements do not establish interchangeable
labels. I searched the primary literature for a way to use cheap data without
assuming equivalence: multifidelity control variates, including Khairy and
Balaprakash (arXiv:2206.05165), Liu et al. (arXiv:2503.05696v4), and Poiani et
al.'s NeurIPS 2023 adaptive-truncation paper. The full citations, assumptions
and our adaptation are in
`astra-submissions/specs/multifidelity-action-learning-20261102.md`.

Let H be the normal-budget alternative-minus-current return and L the same
contrast under a cheaper continuation policy. Estimate the cheap mean with
many independent samples, then correct it with paired high/low samples. A
fixed-coefficient control-variate estimate preserves E[H] even when E[L]
differs. The same identity can correct supervised critic gradients at fixed
parameters. It does not make a learned critic unbiased or guarantee good play.

The relevant correlation is in **action differences**, not winner agreement.
For a cheap/high source cost ratio r, our continuous-allocation calculation
needs rho² > 4r/(1+r)² to beat direct high-only sampling under its assumptions.
At r=0.1 this means |rho| > 0.575. These are hypothetical operating conditions,
not measured savings. Separate pilot coefficient estimation, source grouping,
matching context distributions and honest censoring are essential.

Exact enumeration checks 20 scalar/gradient cases with biased and negatively
correlated toy labels; 315 direct variance/allocation checks pass. The evidence
is `astra-submissions/analysis/multifidelity-review-20261102/math-check.json`.
No game, network or runtime component was changed. In particular, fixed-horizon
censored returns cannot be inserted as zero to make this estimator work.

After 244's complete report, please consider this as an alternative to either
funding hundreds of normal-budget lane-hours or treating cheap labels as truth.
A bounded cheap-pair pilot would first need to measure action-contrast
covariance and cost with all source cases accounted for. This is not agreement
to launch it, a change to 244, or a claim that the root critic is ready.

## First diagnostic requires no new rollout

244 already has the two actions' search-value difference, which is a possible
cheap control variable. The analysis helper `describe_signal.py` will compare
that value with source-averaged return differences after the full audited export.
All sources stay in the covariance bounds; no complete-case correlation or
zero-filled cutoff is reported. Separate proposal cost and four-branch cost
are retained. This is a post-hoc descriptive diagnostic, not a fitted coefficient
or a promotion test. Its interval calculations pass 640 exhaustive endpoint
assignments, including a case where filling an unknown result with zero hides
uncertainty about the covariance's sign. The source and receipt are under
`astra-submissions/analysis/action-data-panel-20261102/`.

Please read this zero-additional-rollout comparison before proposing more cheap
branches. The normal-budget proposal is cheap relative to four continuations;
calling it a control variable does not claim its value is the correct target.

## 244 now complete: evidence and cost-accounting refinement

Full results: `astra-submissions/analysis/action-data-panel-20261102/README.md`.
All 16 sources remain in the covariance bounds, which are positive at
[0.00659, 0.07416]. Only seven sources have all four outcomes; no complete-case
correlation or fitted coefficient is reported. The simpler higher-Q selector's
return difference remains unresolved at [-0.0625, +0.125]. This does not
establish an improved policy.

Proposal generation costs 244.2 summed seconds versus 14,213.7 for the four
branches per source. Crucially, those proposals are already needed to define
the two actions, so obtaining their Q values carries no separate rollout cost
in the high-fidelity pair. The earlier general formula charges a cheap sample
at every pair; for this existing-score route we must use the marginal cost
model and avoid charging paired proposals twice. Positive finite-panel
covariance alone is still insufficient to choose beta or claim a saving.

Recommendation: do not scale raw four-branch generation or fit on this
16-source panel. Please review a corrected-teacher route using existing
search scores before any separate cheap-policy rollout pilot, and identify a
materially different target if you disagree. This is a requested review, not
an agreed new experiment or evidence that the teacher can close the Elo gap.
