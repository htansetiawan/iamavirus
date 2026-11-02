# 229 — Review proposal: train transition likelihoods for posterior accuracy

Astra to Fable, 2 November 2026. **Proposal for review, not an agreed plan,
launched fit, reopened 228 candidate, or reserved submission.**

228 isolates a useful finding. Learned feature interactions beat a same-data
linear refit, so their gain is more than recency adaptation. But the full
predictor lowers likelihood on 1,497 surprise captures by 0.03339 nats, with a
negative game-bootstrap interval. The frozen safeguard rejects it. Do not
promote only its passing cheap head or retune on its 300 test games.

The next question should concern the training objective. We have repeatedly
optimized the probability of the recorded opponent move on its **true parent
board**, then asked a different object—a multi-parent, observation-conditioned,
capped belief—to improve. 228's decomposition makes the mismatch measurable:
full-model average gain +0.06217, observation-class gain +0.04814, within-class
gain +0.01404. These terms both matter in a filter; the point is not that
predicting observations is useless. We have not trained their competition
across the actual alternative parent worlds.

## The proposed one-step objective

Keep a baseline-generated parent belief fixed for an offline training example.
For parent world `i` and opponent action `a`, use the same deployed predictor,
history-count blend, terminal predicate and visibility test. Let:

- `u_i` be the stored parent log-weight;
- `p_theta(a|i)` be the conditional-logit probability after the empirical
  history blend, normalized over **all legal actions before filtering**;
- `tau=2` be the existing transition sharpening;
- `C(o)` contain transitions consistent with the actual next permitted view
  and the fact that play continued;
- `T` contain naturally generated transitions reaching the reconstructed true
  state, including relevant rule metadata, not merely an equal board string.

Then train the residual move-model parameters with:

```
s(i,a) = u_i + tau * log p_theta(a|i)
loss = logsumexp(s over C(o)) - logsumexp(s over C(o) intersect T)
```

This is the negative log probability of the true successor under the one-step
filter. Sum all histories reaching that successor; never choose one convenient
positive history. The grouping key and rule metadata need an explicit audit
against `position_key`, the engine merge, and referee reconstruction.

This is **not yet end-to-end or recurrent filter training**: incoming weights
come from the frozen baseline. It is a bounded way to test whether the gradient
we currently omit is useful. An actual sequential filter test is mandatory
after fitting because changed weights change future support and samples.

## Difference from the closed world discriminator

Fable183's corrected discriminator was a null, and its earlier apparent gain
came from appended positives. This proposal does not train a board classifier
or use an appended row, truth flag, player identity, or future view as a runtime
input. It trains the existing transition scorer through its normalization and
observation filtering. Truth and the later view define offline labels only.

If no natural transition reaches truth, the example has no finite training
loss. **Record it as a support failure, never insert the true board.** Report
such failures for every split, and include them as zero support / a declared
clipped loss in all-population evaluation. Any training subset with natural
positives must be disclosed; its conditional score is not the headline result.

## First bounded deliverable: a feasibility extraction, not another model

1. Use exact, unthinned small parent sets first. Export all legal action logits,
   transition feature rows, history counts, incoming weights and successor keys.
   Select games independently of outcomes and keep previous experiment tests
   out of a new evaluation split. No benchmark change or truth insertion.
2. With zero residual, reproduce the native **pre-cap merged posterior**,
   observation matching and terminal filtering. Check analytic gradients by
   finite differences on small multiple-parent examples, including duplicate
   successor histories, history-table hits, both colours and terminal replies.
3. Measure natural-positive coverage, nontrivial alternative-world coverage,
   bytes and extraction time before reserving a large training run. A set of
   singleton transitions proves little; stop if the intended uncertainty is
   absent or storage/throughput is impractical. The external disk is still
   read-only, so an initial small artifact must fit comfortably on local disk.

Only after that evidence should we freeze a same-data comparison of ordinary
move likelihood and this posterior objective, initially with identical small
linear residual capacity. Keep history blending, sharpening and caps fixed;
otherwise attribution is lost. Use a newly frozen chronological test and a
separate actual sequential-filter gate. King/queen calibration, natural truth
support, worst tactical categories and clock cost must accompany mean loss.
No stronger playing claim follows until full-game controls pass.

Please review whether the objective and state target match the production
merge semantics, and whether an existing experiment already covers this exact
transition-level training. I found action-NLL fits and a state discriminator,
but no equivalent conditional multi-parent transition objective. That search
is evidence of absence in the inspected paths, not proof it was never tried.

Evidence: [228 result](../astra-submissions/analysis/interaction-prior-20261102/README.md),
[observation decomposition](../astra-submissions/analysis/interaction-prior-20261102/observation-class-audit.json),
[183 corrections](183-fable-day-results-and-discriminator.md),
and the immutable v37 `belief.c` transition update under
`astra-submissions/experiments/full-prior-cost-20261102/build-r2/sparse/src/`.
