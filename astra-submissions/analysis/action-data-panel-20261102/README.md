# Root-action data: sound collection, expensive and incomplete targets

2 November 2026. Experiment 244 completed all 64 first-attempt branches on
the original handle 95681, exit 0. **Do not scale this four-branch recipe or
train a critic from these sixteen sources yet.** The experiment establishes
data-generation correctness and measures its limitations; it does not show a
stronger playing policy. No new ZIP, model or arena upload results from it.

## What the experiment measured

Sixteen new top-12-vs-top-12 arena games were selected by a salted hash, without
using outcomes or tactical tags, balanced over four phases and both colours.
Each source supplied the current v37 choice and the highest-valued different
view-legal search move, followed by two seeded repeats of each action. Both
bots then used reconstructed v37/v37 play, normal move budgets and restored
private observation histories and clocks. The branch stopped after 64 new
plies if the game had not ended. Reconstructed history is not a clone of the
original process's search/RNG memory. This is a phase-balanced development
panel conditional on reaching those positions, not a population arena sample.

The frozen plan and branch hashes remain `d425672e5f7f` and `8cfcde832163`.
All 64 branches completed without a protocol failure, timeout or retry. The
independent rules/clock/input review checks **5,479 frames** and **128 privacy
invariants**. A host audit finds no remaining experiment workers or members
of its 128 bot process groups; all four reserved cores are released.

## Targets and their limits

| Quantity | Result |
|---|---:|
| Independent source games | 16 |
| Distinct permitted history/action inputs | 32 |
| Branches / naturally ended / censored | 64 / 50 / 14 |
| Action comparisons with both outcomes known | 21 of 32 |
| Sources with all four outcomes known | 7 of 16 |
| Same-action repeat pairs with both outcomes known | 19 of 32 |
| Those repeat pairs with different outcomes | 4 of 19 |

The 21 fully observed comparisons contain 14 ties, two alternative wins,
four alternative losses and one win-to-draw degradation. These are action
comparisons from selected source positions, not a match record. Incomplete
pairs remain in the exported data with loss-to-win bounds. Their exclusion
would particularly distort early positions:

| Branch phase (Black uses the next odd ply) | Censored / branches |
|---|---:|
| 16 | 8 / 16 |
| 32 | 3 / 16 |
| 48 | 1 / 16 |
| 64 | 2 / 16 |

Four observed repeat disagreements are sufficient to reject treating a
single terminal outcome as a certain action label. They are not an unbiased
estimate of the disagreement rate because 13 repeat pairs remain incomplete.
The all-source repeated-contrast product has missing-outcome bounds
**[-1.000, 1.125]**; it does not establish a reliable action-effect signal.
The repeatability diagnostic was added post hoc, with 225 exhaustive
interval-pair checks; it is not a predeclared promotion rule.

## A network must beat the simple selector first

Choosing the higher root search value changes five source actions. Its
mean return difference versus the current choice is bounded by
**[-0.0625, +0.125]** on the [-1,+1] return scale. These are missing-outcome
bounds, not a sampling confidence interval. They admit both harm and benefit.
Choosing the higher root probability changes no action. Neither selector
earns promotion from this panel.

Existing search-value differences have positive empirical covariance with
two-repeat return differences even after allowing every censored outcome:
**[0.00659, 0.07416]**. This is a finite-panel description, not proof of
population correlation or lower-variance learning. Correlation is deliberately
not computed on the seven complete sources alone. The search scores already
exist, so they are a cheaper auxiliary-teacher candidate to investigate before
paying for another rollout policy. Their useful coarse signal does not prove
they distinguish better moves among the close alternatives we need to learn.

## Cost and next decision

The batch took **127.1 wall minutes**. Summed branch time was **14,213.7
seconds**, or **888.4 seconds per independent source** with four branches.
There were 2,759 searched continuation decisions, averaging 5.15 seconds
each. The proposal generators separately cost 244.2 summed seconds. These
are elapsed lane/generator times, not measured CPU-seconds.

At the measured branch rate, 1,000 sources with the same four branches would
cost about **246.8 summed lane-hours**, or **123.4 hours at perfect two-lane
utilization**, before proposal overhead. This is a planning extrapolation,
not guaranteed future throughput. Thousands of intermediate positions share
these few trajectories and outcomes; they do not provide thousands of
independent action comparisons.

Recommendation for Fable/human review: retain this audited panel as a small
development/calibration asset; do not bulk-generate the same targets or fit a
large network on it. First decide whether existing search scores can support
a cheaper teacher with a rigorously corrected terminal signal, or whether a
different learning target is required. Any cost claim needs fresh evidence,
and paired search scores are already available as part of generating these
actions; they must not be charged twice. Experiment 247's paid-cheap-rollout
cost formula is not automatically the right cost model for that case. No
next training run is launched by this report.

## Taxonomy and reproducibility

`taxonomy.json` labels only the 2,823 new continuation moves, excluding shared
prefixes. It separates actor/opponent and action arm, and adds 51 queen-capture
visibility records plus one en-passant record. A queen capture is not labelled
as a net material loss without analysing the exchange. These true-board and
future-dependent annotations are offline diagnostics, separate from learner
inputs. Descriptive tag rates do not establish which action is stronger or
whether a guard is calibrated.

`critic-inputs.jsonl` contains only own observation/move/clock history and
permitted proposal features. `root-targets.jsonl`, `paired-targets.jsonl` and
`seed-variability.json` preserve labels, bounds and grouping. Keep all arms,
repeats and matching observable histories together in future data splits.
`dataset.json` hashes the audited exports; `completion-receipt.json` hashes
the post-hoc reports and records successful execution. All root values are
under reconstructed v37/v37 continuation, not Nash values, CFR frontier
values or evidence of strength against duck/Instructors.
