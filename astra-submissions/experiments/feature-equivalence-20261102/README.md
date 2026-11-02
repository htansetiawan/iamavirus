# 233: audit what the move features cannot distinguish

232's 357-coefficient expansion gained little beyond its linear control. Check
whether some hidden transitions are forced to have equal move probability for
every scorer using the same 26 inputs. This is a conditional representation
audit, not training, a belief repair, or an Elo estimate.

For each development update, enumerate the same observation-consistent edges.
Group edges only when they share:

1. the complete multiset of legal-move feature vectors and fixed base logits;
2. the candidate feature vector and base logit;
3. the active history total and candidate history count (ignored below the
   production minimum count of three).

Consequently every function f(x) gives all edges in a group the same normalized
and history-blended move probability p_g. With incoming parent weights w_e
fixed, define B_g=sum(w_e) over compatible group edges and A_g=sum(w_e) over
edges reaching the true successor. Then

```
P(true successor | observation) = sum(A_g * p_g^2) / sum(B_g * p_g^2)
                               <= max_g A_g / B_g.
NLL >= -log(max_g A_g / B_g).
```

Compute the fractions in log space. Allowing groups independent probabilities
relaxes the real model constraints: this bound may be loose and is not an
attainable oracle. Incoming weights and history table are fixed; this does not
bound a retrained sequential filter or a model using additional inputs. A zero
bound does not prove that the feature representation is sufficient.

Also compute a weaker **parent-local bound**: only group edges from the same
parent. Each group's positive fraction is then its positive count divided by
its compatible count, independent of the parent's weight. This bound remains
valid for arbitrary incoming weights on the same support. It still assumes
the same history table, legal transitions and observed view; changing support
or history counts is outside that statement. Report both bounds separately so
that an incoming-weight limitation is not mislabeled a feature limitation.

Repeat the bound with source/destination/promotion added to the candidate
encoding and legal-normalizer signatures. This measures removal of forced
ties by information already available for each hypothetical legal move. It
does not determine learned probabilities or remove genuine observation
ambiguity. Keep the previous observation-alias analyses distinct from this
scoring-feature equivalence.

Use the same 80 development-validation games as232, no new or old test export.
Preserve original feature hashes; the augmented exporter adds move codes,
successor keys and parent snapshots only. Report game-weighted bounds overall,
on nontrivial updates, later decisions and surprise captures. Check all five
fixed232 models against the bound. Retain up to six unique-game witnesses
with the largest bound reduction from geometry, and up to six additional
surprise witnesses. Independently replay those parent/action alternatives
through the separate rules engine and verify unchanged observations and
identical scoring inputs.

Synthetic tests cover unequal incoming weights, duplicate actions, hidden
alternatives, history-count and normalizer separation, and extreme log weights.
No new model, parameter selection or promotion gate is involved. CPU cores2–3,
20-minute bound, at most2GiB arrays. Publish sources and plan before extraction.
