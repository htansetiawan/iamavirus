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
