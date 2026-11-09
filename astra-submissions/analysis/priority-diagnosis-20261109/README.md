# V38 priority-decision diagnosis

Frozen development cohort:26 losses to duck/Greek Gift from v38's first318
games, plus the preceding own decision for the10 final positions that were
already immediately lost.36 decisions, two seeds, at most30minutes on cores0–1.
This studies causes of failure; it is not a playing-strength experiment.

The source is the exact uploaded ZIP ba6610f299c1, with unchanged C/model,
history table and modified Stockfish. The instrumented copy adds two read-only
exports: teacher targets after the solver selects, and belief-wide king risk (the deployed 20,000-board cap),
combined exclusions and placement support after the protocol move is emitted.
The truth placement is first read in that last block. Old pre-decision risk
and truth instrumentation is disabled. Output work adds runtime after the
choice; no claim of a zero-cost instrumented executable is made.

Both-color initial-position control/diagnostic preflight passes (White d4,
Black d5; no faults), as recorded in preflight.json. That checks integration,
not byte-identical wall-clock search trajectories. The old teacher exporter
and conditional-value calculation are reused from the tested prior audit.

Readouts distinguish:

- Full-placement support and weight versus presence among32 sampled worlds.
- True-safe actions absent from the observation-derived move set versus
  present actions removed by guard/repetition exclusions.
- True-safe retained actions versus the selected action and its root policy
  probability/conditional continuation value.

Truth labels use the course referee outside the actor. Placement agreement
does not verify castling/en-passant rights; it overestimates full-state
support. Prior own moves are forced and do not warm Stockfish as the arena
did; the original clocks are supplied, but clock-sensitive belief thinning
can differ from the actual game. Findings are conditional on the reconstructed
belief. They cannot prove that the exact same arena decision had that belief.

plan.json pins the36cases,72attempts,seeds,code and dependencies. A review-logic
correction before any actor run is preserved in preflight-plan-initial.json:
missing safe moves and excluded safe moves must not be conflated. Each case
has a120-second timeout; the batch stops on a technical failure or global
wall bound, retaining missing cells explicitly. No replay is restarted to
replace a failed first attempt. Runtime outliers include post-choice readout.

Sources: [prepare](../../experiments/priority-diagnosis-20261109/prepare.py),
[runner](../../experiments/priority-diagnosis-20261109/run.py),
[review](../../experiments/priority-diagnosis-20261109/review.py).
No GPU, network ingest, model fit or new release is launched by this study.

## Completed result

All72 first attempts complete, no technical failures or illegal choices.
Original exec82514 exited0. Independent audit verifies all files and source
edits, all72 root exports, consistent own reach, normalized strategies,
excluded actions absent from the tree, and emitted moves matching solver
selection. No true-safe retained action is missing from the tree.

The terminal cases give:

| Opponent | Replays | Replayed fatal move | True placement absent from belief | Present but absent from search sample | Safe move exists | Every safe move excluded |
|---|---:|---:|---:|---:|---:|---:|
| duck | 20 | 17 | 2 | 13 | 16 | 12 |
| Greek Gift | 32 | 29 | 3 | 24 | 16 | 6 |

Counts combine two seeds on each of26 source games; they are not independent
games. Truth placement is present in47/52 terminal replays and sampled in10.
This does not establish calibrated or miscalibrated probabilities: the cohort
is selected on losses, and a low probability for one realized board is not by
itself evidence of a defective posterior.

Of32 terminal decisions with a true-safe move,18 exclude them all. Another20
terminal decisions have no immediately safe move even before filtering.
Therefore **38/52 terminal replays cannot be saved by any choice among the
current retained actions**, even given the true board. Actual replay loses46;
a perfect selector on those fixed action sets could save at most8 more.
This is an action-support ceiling on this cohort, not an Elo bound or an
argument for globally removing the guards.

The20 preceding decisions all select immediately safe moves. Their later
survival is unmeasured; an immediate-safe label cannot establish that a trap
or material deficit has been repaired.

## One cheap hypothesis worth testing next

Current filtering usually requires a move to be within0.02 of the minimum
combined king/queen risk under **both** the fitted and sharper weighting.
An alternative keeps it when that holds under **either** weighting, allowing
search to resolve disagreement. This changes how uncertainty is handled,
without another numerical threshold fit. It enlarges the action set and can
also expose the king more often; it has no safety guarantee.

Using the same0.02 margin and0.9queen coefficient on the fixed readouts,
this alternative restores at least one safe action in8/18 all-excluded
decisions. Merely adding nondominated two-risk actions restores2/18. These
are hindsight opportunity counts, not chosen moves or wins. They justify a
bounded candidate test; neither earns promotion.

Next validation must include outcome-blind new cases and non-losing controls,
compare masks on the same belief, and check actual selected moves at equal
time. Full-clock games against exactv38 and the relevant opponents remain
necessary. Retain the original guards if the enlarged set materially worsens
king survival. Do not tune the margin on these losses or count this cohort
as a fresh confirmation set.

Receipts: completion.json, review.json, audit.json, mask-opportunity.json.
The [mask calculation](../../experiments/priority-diagnosis-20261109/mask_opportunity.py)
reproduces its original receipt; no actor is rerun.
