# Cap-weight audit: measurable distortion, correction has a variance cost

The estimator audit completes and independently verifies all304,096 draws.
No playing engine, belief weight, model, guard or arena version changed.
This is a concrete sampling issue, with no strength result or promotion.

| Fixed subset | Full-input probability | Old estimate, mean | Corrected estimate, mean |
|---|---:|---:|---:|
| Toy heavy item, K2/3 | 80.000% | 85.282% | 80.881% |
| Toy rare item, K2/3 | 5.000% | 1.831% | 4.570% |
| Frozen root: g7f6 fatality, K32/2344 | 11.651% | 1.893% | 11.876% |
| Frozen root: g7h6 fatality, K32/2344 | 10.005% | 1.280% | 10.195% |
| Frozen root: g7g8 fatality, K32/2344 | 0.013895% | 0.0000404% | 0.013764% |

The toy has an exact independent ordered-without-replacement calculation:
old expected heavy probability is85.2012%, and rare is1.8421%. The empirical
native means agree within the fixed sanity checks. Equal-weight population
is an unchanged control: normalized old and corrected estimates coincide.
The normalized correction still has finite-sample bias; the heavy toy mean
is80.881%, not exactly80%. All corrected unnormalized mass means satisfy
the frozen six empirical-standard-error checks. These checks are diagnostic,
not rigorous confidence guarantees or a proof of unbiasedness.

The rare root risk shows why a mean correction is insufficient. At K32,
its old MSE is1.92e-8 and corrected MSE3.86e-6, about201 times higher. For
f6/h6, MSE improves from0.00972/0.00770 to0.00301/0.00257. At K2048,
correction also lowers the rare-risk MSE. The complete K32/128/512/2048
results, all15 root-risk subsets and toy-coordinate regressions are retained
in [audit.json](audit.json). No K was selected after seeing the outcomes.

These K values are artificial thinning experiments on one known2,344-world
population, not the deployed200,000 cap or arena-frequency estimates. Mean
discarded mass in this population is83.86%,54.74%,18.87% and0.116% at the
four K values. The next relevant diagnostic is actual discarded mass at
native cap and paid-thinning events on real histories. Later conditioning
can amplify a one-step distribution change; the dropped-mass fraction is
not a whole-game error bound.

## Implementation and checks

The wrapper includes the immutable deployed belief.c and directly reuses
its rank RNG, comparators, partition and native shrink. The correction reads
the first excluded rank; sampled indices, native RNG state and metadata are
unchanged. It does not append worlds or invent opponent histories, and it
cannot recover a true state that selection discarded. The
implemented estimator follows [Kool et al. §5.3, appendices B–C](https://jmlr.org/papers/volume21/19-985/19-985.pdf#page=25).
The independent NumPy audit uses the scalar native uniform stream, then
recomputes every rank, cutoff, corrected value and subset aggregate. It
shares the PRNG, not the weighting or aggregation code. Small toys also
receive exact permutation enumeration independent of Monte Carlo.

Preflight checks64 native shrink/partition/NumPy selection cases and60
high-precision numerical/scale cases, full-retention identity and address/
undefined sanitizers. The data run uses three100,000-repetition toys plus
four1,024-repetition frozen-population cases. Native1.37s; independent
review0.97s. These are audit runtimes, not an engine speedup claim.

Source/plan commit81ee1f2a165d4900d06c463c20ca227e826ca718 was published to
both mirrors before original37895 (exit0). Independent reviewer exits0.
A prepublication whitespace check removed one blank EOF line and updated
its unpublished source pin; no experimental result or binary was changed.
All14 dependencies match. No worker/scorer process was created; CPU6 is
released after terminal receipts. No GPU, refit, new game, release or upload.

Do not plug corrected log-weights into the current fitted-guard power rule
and call it a calibrated alternate posterior. That operation also raises
the correction factor to1/temperature, while the alternate target needs its
own weighting semantics. Closed dual-measure252, prior fits231/232 and the
qsort-only cost track remain closed. A sequential candidate must define
these semantics and pass belief-quality, tactical-decision and playing gates.

See [plan.json](plan.json), [preflight.json](preflight.json),
[completion.json](completion.json) and [audit.json](audit.json).
