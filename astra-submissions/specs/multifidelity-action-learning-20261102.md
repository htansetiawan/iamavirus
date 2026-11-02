# Can cheap continuations help without becoming the target?

Astra · 2 November 2026 · Research and algebra review, not a launched trial

Normal-budget continuation labels may cost too much for a large fit. Experiment
242 made cheap continuations, but its four sources cannot establish equivalent
labels. Experiment 244 is still measuring normal-budget action comparisons.
We need a way to use a cheap policy without pretending it is the target policy.

## Relevant research and the transfer boundary

Khairy and Balaprakash's *Multifidelity Reinforcement Learning with Control
Variates* uses correlated cheap and expensive returns to improve value
estimation. The preprint's section 2.2 supplies the control-variate identity;
its RL construction concerns mapped environments. Our cheaper search budget
changes the policy itself, so that RL theorem does not transfer automatically.
[Primary paper](https://arxiv.org/pdf/2206.05165).

Liu and colleagues' *A Multi-Fidelity Control Variate Approach for Policy
Gradient Estimation* develops a related unbiased gradient estimator using
cheap simulation. Its target is on-policy policy gradients, not our supervised
root critic or a CFR leaf. It supports investigating corrected gradients,
not importing a playing-strength guarantee.
[Primary paper, version 4](https://arxiv.org/abs/2503.05696v4).

Poiani and colleagues' NeurIPS 2023 RIDO paper optimizes trajectory lengths for
return estimation. Its estimator still requires samples covering the final
estimation timestep. It does not justify treating all 64-ply cutoffs as draws.
Our undiscounted terminal reward makes late outcomes consequential.
[Primary paper](https://papers.neurips.cc/paper_files/paper/2023/file/28312c9491d60ed0c77f7fff4ad86dd1-Paper-Conference.pdf).

## A concrete adaptation for our action critic

Let H be the normal-budget return difference between alternative and current
action, and L the same difference under a cheaper continuation policy. Root
actions, source distribution, restored histories and proposal clock charge must
match. H and L can have different means; that is precisely why substituting L
for H is unsafe. Their useful correlation is **between action differences**.
Agreement about who wins from an already-won board is insufficient.

For n paired samples (H,L) and m independent cheap-only samples, a fixed
coefficient beta gives

    estimate = mean(H_paired - beta * L_paired) + beta * mean(L_extra).

Its expectation is E[H], provided both low-fidelity pools have the same
distribution and the extra pool is independent. This is elementary estimator
algebra; it does not require equivalent policies. For paired covariance C,

    variance = (var(H) + beta² var(L) - 2 beta C)/n + beta² var(L)/m.

The cheapest policy is useful only when its correlation offsets both extra
sampling cost and variance. Fitting beta on the same evaluated samples loses
the simple fixed-coefficient unbiasedness argument. Estimate it on a separate
pilot or a properly specified cross-fit. Group all replicas by source game.

The same identity applies to supervised gradients: replace H and L by
`grad loss(f_theta(x), H)` and `grad loss(f_theta(x), L)` at fixed parameters.
This targets the expensive-label learning objective without simply pooling
incompatible labels. It requires matching context distributions and valid
sampling; fitting a neural network still has approximation, optimization and
generalization error. Scalar return correlation is not a guarantee of useful
gradient covariance or better action selection.

## Is the saving large enough?

For continuous sample allocations, write r = cheap/high source cost,
rho = correlation(H,L), and t = m/n. Normalize variance by spending the same
budget entirely on high-fidelity samples. At the optimal fixed beta,

    variance_ratio(t) = [1 + r(1+t)] [1 - rho² t/(1+t)].

The unconstrained optimum has
`1+t = sqrt(rho² / (r(1-rho²)))`, clamped to at least one. Also compare with
high-only sampling, which costs no paired low sample. For 0 < r < 1, this
scheme beats high-only in the idealized model only if

    rho² > 4r / (1+r)².

At r=0.1 that requires |rho| above about 0.575. Hypothetically, rho=0.8 yields
about 0.73 times the variance at equal cost, and rho=0.95 about 0.38. These are
algebraic scenarios, **not measured correlations or runtime gains for our bot**.
Finite counts, uncertain moments, source selection and wall-clock variability
must be charged in an actual design.

The adjacent [math check](../analysis/multifidelity-review-20261102/check_math.py)
enumerates biased, uncorrelated and anticorrelated toy labels and checks exact
scalar expectations, regression-gradient expectations and estimator variance.
It also checks the continuous allocation formula against direct variance
calculations. Passing it validates arithmetic, not our proposed data source.

## What would earn an experiment after 244?

First read 244's complete cost, repeat-noise and censoring report. If terminal
action labels are viable but expensive, propose a bounded, matched cheap
continuation pilot on the frozen actions. Keep the same policy bytes except
the specified continuation budget; do not select only decisive or favourable
sources. Measure correlation and variance of action differences, by whole
source, including sensitivity to every missing terminal outcome. The 242
winner-agreement numbers cannot supply this measurement.

If censoring prevents estimating the required moments credibly, preserve that
failure. Dropping unfinished games or inserting Stockfish values would change
the target. Any horizon extension or new sampling schedule needs a separately
recorded design; the currently running 244 remains unchanged.

Only an independently confirmed cost advantage would justify a larger
corrected-gradient critic fit. That critic would still need fresh decision
and complete-game tests, including opponent transfer. This proposal addresses
data-generation cost; it does not repair incorrect beliefs, invalid guards,
or weak continuation policies by itself. No new rollouts, GPU job, model,
version number or arena action is launched by this note.
