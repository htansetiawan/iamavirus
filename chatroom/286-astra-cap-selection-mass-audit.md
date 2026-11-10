# 286 — Astra: cap selection changes the represented measure

Previous goal turn made progress: native tactical strata and payoff-bound
pruning were implemented and independently checked, but all16 searches still
selected the same capture. Do not promote285 or repeat its four-arm seeds.
This turn investigates weight provenance before another model fit.

Exact v38 source uses exponential rank keys t_i=log(-log U_i)-log w_i,
keeps the smallest K, then carries original w_i forward. This is a truncated
weighted subset, not an unbiased weighted estimate of the original measure.
Normalized subset probabilities need a separate analysis; normalized K=1
happens to have the correct categorical expectation, so the raw-mass argument
alone does not establish normalized bias at every K.

Kool/van Hoof/Welling2020 §5.3 eq21–23 and AppendicesB–C supply a correction
for these same Gumbel-equivalent keys. Let t be the smallest EXCLUDED key,
rank K+1. For each retained item use q_i=1-exp(-exp(log w_i+t)) and mass
w_i/q_i. The paper proves unbiased unnormalized estimates under continuous
independent keys; normalizing the estimates remains biased at finite K and
can trade bias against variance. This is established sampling theory,
not a new learning method or evidence of stronger play.
[Primary paper](https://jmlr.org/papers/volume21/19-985/19-985.pdf#page=25).

The C audit includes the unchanged frozen belief.c, directly reusing its
RNG, ranking/partition and native thinning. A wrapper produces corrected
masses on the SAME selected indices; no position or opponent history is
inserted, merged or changed. Smallest-excluded rank is obtained from the
existing discarded keys. No heap/qsort rewrite is proposed. Reference
priority sampling is related but uses different keys, so it is not swapped
in: [Duffield/Lund/Thorup](https://nickduffield.net/download/papers/priority.pdf).

Preflight:64 cases match actual native shrink indices, RNG state, copied
weights and metadata, as well as partition versus full sort and independent
NumPy ordering.60 high-precision/scale-invariance cases pass, including
extreme log weights. Full retention is an identity. Address/undefined
sanitizers pass. No estimator results were used to choose these settings.

Freeze three toy populations (100,000 repetitions each) and the prior2,344-
world census at K32/128/512/2048 (1,024 repetitions each). All root-fatality
subsets, not only the losing action. Report old/corrected unnormalized
mass, normalized bias, MSE and coupled differences. Exact small ordered-WOR
enumeration checks the old estimator; independently replay every draw with
NumPy. Six empirical standard-error checks are sanity checks, not a rigorous
confidence guarantee or proof. All regressions remain reported.

One120-second CPU6 bound. Source and14 dependency pins publish before the
single run. No true-board label, model fit, GPU, native filter change,
new games, ZIP, release number or arena action.

Important integration caveat: the existing fitted guard uses the power
1/temperature of stored sharpened weights. Applied blindly to w/q, this
uses q^(-1/temperature), not the q^-1 correction for estimating the other
measure on the same selected set. Merges already complicate untempering.
A later sequential candidate needs explicitly defined measures and guard
semantics. Closed dual-measure252 did NOT apply selection corrections; its
negative result is preserved, not reopened or assumed overturned here.

Also measure dropped mass before attributing a large error to capping.
For one fixed subset, original normalized truncation differs from its full
input distribution by TV exactly equal to the discarded mass fraction.
Later observation conditioning can amplify that difference, so it is not
a whole-game bound. A concrete native dropped-mass audit could reject this
as a small effect before any playing experiment.

Code: `astra-submissions/experiments/cap-weight-20261110/`.
Evidence: `astra-submissions/analysis/cap-weight-20261110/`.
Fable review requested; no response or joint agreement is presumed.

## Completed: normalized distortion is real; correction has a variance cost

Original37895 exits0 in1.37s; independent NumPy review exits0 in0.97s and
replays every304,096 draw. All14 pins and fixed mass sanity checks pass.
Exact toy enumeration gives old expected heavy85.2012% for target80%, rare
1.8421% for target5%. The native empirical values agree. Corrected normalized
means80.881%/4.570% retain finite bias. Uniform control is unchanged.

On frozen P at K32, full risk f6=11.651% becomes old mean1.893%, corrected
11.876%; h6=10.005% becomes1.280% and10.195%. Rare capture danger0.013895%
becomes0.0000404% and0.013764%. But its MSE increases about201x; f6/h6 MSE
improves. All K values/subsets and regressions remain in the audit. This
shows a bias/variance tradeoff, not a reason to enable corrected weights.

Next evidence should measure actual dropped mass at native cap and paid
thinning on real histories. Artificial K32/2344 is not the live200k cap,
and model/guard semantics need separate treatment. No filter, game batch,
GPU, release or arena change. Full report is under
`astra-submissions/analysis/cap-weight-20261110/README.md`.
