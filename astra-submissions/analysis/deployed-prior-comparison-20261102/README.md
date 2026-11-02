# Deployed-prior comparison

Prepared, not scored. The frozen plan selects 222 later opponent games and
retains 233 exclusions. It compares the existing actor-visible response model
with v37's actual full and cheap move priors, each using the same history table.
The main candidate is fixed in advance; taxonomy slices cannot select another
winner after the test. No fit, posterior integration, live engine change or
strength claim is part of this screen.

See the [design](../../experiments/deployed-prior-comparison-20261102/README.md),
`plan.json`, `preflight.json` and `build.log`. The native bridge uses the exact
v37 extraction under experiment221; all sources, binary, table and student
weights are hashed before execution. Build artifacts are local and ignored.

## Result: blanket belief-prior replacement rejected

All 222 games complete on the first execution, handle 53975 exit0, in about 12
seconds. Course referee, extracted native rules and recorded frames agree on
19,829 positions; actor-history legal sets agree and all 8,465 positive visible
king-loss proofs are verified against the true board. Native/Python history
hashes agree throughout. The host launch-PID inspection happened after this
short run ended and found no process; no restart was made. A subsequent host
audit confirms no owned processes remain and releases cores 2–3.

Primary panel: 10,747 non-suicidal decisions after own move eight, from 221 games.
Every arm uses the same empirical-history blend; only 227 decisions hit it.

| Prior | Mean NLL (lower better) | Top-1 accuracy |
|---|---:|---:|
| v37 full | 2.67574 | 25.28% |
| v37 cheap | 2.90995 | 22.28% |
| Raw student | 2.71856 | 26.00% |
| Projected student, frozen primary candidate | 2.69962 | 26.22% |

Candidate log-likelihood gain versus full is **-0.02387 nats**, whole-game
bootstrap 95% interval **[-0.04460,-0.00253]**. On 1,084 surprise captures from 217
games the gain is **-0.25524**, interval **[-0.31638,-0.19324]**. Both fail the
frozen gate. Primary targets have no zero probabilities. All-move diagnostics
include the projection's visibly suicidal terminal targets and explicitly
report zeros; their NLL uses the documented 1e-300 numerical floor.

The student beats the cheap model overall but still predicts surprise captures
worse than that model (NLL 1.71484 versus 1.64606). Choosing the cheap comparator
after seeing this result would not rescue the predeclared tactical condition.
Better top-1 accuracy also does not imply better belief weights: the filter
needs probabilities on the whole action distribution.

The earlier positive result against the research linear model remains valid;
it did not establish superiority to v37's actual full prior. This comparison
does not test whether the student is useful inside search, the question of
the separate, unchanged 219 trial. It closes blanket prior replacement with
these weights. No posterior integration, training, threshold change or ZIP.

`decisions.jsonl.gz` preserves all 13,143 prediction rows, not just primary or
successful cases. `archive.json` pins raw/compressed hashes. `result.json`
contains every frozen arm, team breakdown and diagnostic tags. Independent
aggregation checks in `aggregation-review.json` reproduce the means and
eligibility counts; they are not a second implementation of neural inference.

Next priority to investigate: why the full prior is abandoned above 10,000
worlds, and whether Fable's existing bitboard/model-filtering accelerations
make its tactical features affordable there. The measured full–cheap gap is
much larger than v37's refit gain. A fixed-state throughput/posterior test is
needed before a full-clock trial; no such change has been launched here.
