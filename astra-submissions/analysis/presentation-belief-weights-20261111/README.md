# Where the fourteen board weights come from

November 11 UTC. A fixed-parameter calculation on the earlier stage of the
[375 teaching history](../presentation-real-decision-20261111/README.md),
after White d4 and the first hidden Black move. This probe runs inference
only. It does not run Stockfish, a search, a game or a new candidate.

## Two learned objects, then a rules filter

There are 20 generated Black moves. The deployed 28-feature model gives
each a softmax probability. The hypothesized opponent-history key
`46a80500cad2fa61` also has **152,835 recorded action occurrences** in the
shipped table. These are counts for a private-history key, not 152,835
examples of this exact complete board or a player-name lookup.

For each move, the native blend is:

```text
q = (recorded_move_count + 4 × fitted_model_probability) / (152835 + 4)
```

The four model pseudocounts give the model **0.002617%** of this blend.
That is specific to this heavily observed opening key. An unknown or
insufficient-count history falls back to the model; at the minimum accepted
count of three, the model would supply 4/7 of the blend.

The received White view rules out six moves, including c5 and d5. The 14
compatible moves contain **55.6462%** of the blended probability before
sharpening. The parent has weight one and the default temperature is two,
so each retained child gets `q² / sum_over_compatible_moves(q²)`.

| Hidden Black move | Stored count | Fitted model probability | Blended probability before filtering | Retained weight after filtering and power |
| --- | ---: | ---: | ---: | ---: |
| Nf6 | 24,424 | 12.5825% | 15.9805% | 37.9538% |
| Nc6 | 20,810 | 12.5825% | 13.6160% | 27.5530% |
| c6 | 16,609 | 5.2105% | 10.8671% | 17.5510% |
| e6 | 16,105 | 5.2105% | 10.5374% | 16.5020% |
| Other ten compatible moves | — | — | — | 0.4401% |

The stored `logw` values are relative: the update subtracts the largest log
weight. Thus Nf6 has stored log weight zero, meaning relative weight one,
not probability one. Dividing by the sum of all fourteen relative weights
gives its 37.9538% normalized share.

The feature model ties Nf6 with Nc6 here; history counts distinguish them.
The same is true of c6 and e6. This illustrates the separate roles of the
small fitted representation and the larger exact-key count table; it does
not establish their strength contributions.

The actual move, joined only in the later review, is c6. Its 17.5510% weight
is not disproved by its occurrence. Calibration requires a population of
predictions and outcomes. The later Bf4 observation eliminates the other
possibilities and produces 375's unique retained board.

The native default sampler returns **all 14 worlds with these weights**
because their count is below 32. This is a sample-function check, not a
reconstruction of the original arena's second search or a selection of the
"best" boards. The earlier third-decision reconstruction remains unchanged.

## Two mathematical qualifications

More generally, the source adds `2 × log(q)` to the parent's log weight for
each compatible continuing transition, then sums weights for duplicate
boards. It does not first divide `q²` by a separate normalizer for every
parent. This is a powered inference weight, not simply an ordinary Bayesian
update using a normalized temperature-adjusted move policy.

For example, take two equally weighted parent worlds whose moves all produce
the same observation. One has two moves with probabilities (1/2, 1/2); the
other has a single move with probability 1. Their sums of squared
probabilities are 1/2 and 1, so the native
rule assigns their descendant groups weights 1/3 and 2/3. A separately
normalized policy per parent would preserve 1/2 and 1/2. This is an
algebraic illustration of the rule, not a measured arena defect or a new
estimator proposal. Earlier mass-preservation and dual-weight tests stand.

Also, merging and undoing the power do not commute. If paths of probability
1/4 and 1/4 reach board A while a path of probability 1/2 reaches board B,
the unpowered board masses are 1/2 and 1/2. Summing squared path weights
gives normalized masses 1/3 and 2/3. Taking square roots afterward and
normalizing gives **41.4214% and 58.5786%**, not 50/50. Thus the guard's
inverse-temperature weighting is not an exact recovery of the original
unpowered history distribution after merges. Capping and representative
history retention add separate approximations.

Neither calculation establishes a calibration failure on current games,
explains the Elo gap, or qualifies a replacement weighting rule.

## Verification

The probe uses unchanged v38 inference/rules/move-model sources. The single
original call exits zero. Independent Python review decodes history.bin,
matches every count and denominator, recomputes all 20 feature-dot logits,
softmax and blends, and checks all 14 powered normalized weights. All stored
counts for this queried history map to the current legal moves. The native
history statistics show one hit in one lookup.

The compatible move set matches 375's existing course-referee enumeration
on the identical source views. All fourteen native sampler weights match
the retained weights. Inputs, sources and raw logs are hash-bound; the
two recorded White views contain no injected opponent action or truth.

[Plan](plan.json) · [Build](build.json) · [Execution](execution.json) ·
[Arithmetic result](result.json) ·
[C probe](../../experiments/presentation-belief-weights-20261111/probe.c) ·
[Runner/reviewer](../../tools/presentation_belief_weights.py).

Raw rows are local under `data/astra-spool/presentation-belief-weights-20261111/`.
No new weights, history file, guard, training split, GPU job, candidate,
package, commit, push or deployment results from this explanation.
