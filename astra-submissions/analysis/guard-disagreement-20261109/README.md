# Guard disagreement: opt-in prototype

This implements the next concrete mechanism from diagnosis269. Exactv38
sources and weights are retained. A single native predicate changes action
support when ASTRA_GUARD_EITHER=1; default off preserves the old predicate.
There is no new archive or arena change.

Let r and s be combined king/queen risk under the fitted and sharper
weightings, and let delta=0.02. The deployed ordinary pass keeps actions in
both sets {r <= min(r)+delta} and {s <= min(s)+delta}; if their intersection is
empty it falls back to the sharper set. The prototype keeps their union.
Thus search may arbitrate disagreement rather than having either weighting
veto the move. This liberalizes action support and can worsen king safety.
It does not minimize worst-case risk or provide a safety guarantee.

For fixed input risks the union is nonempty and contains the deployed set.
When both weightings agree, their sets and both policies coincide. The rule
is O(A), with the same existing risk calculations and numerical constants.
The separate post-hoc Pareto diagnostic sorts risks in O(A log A); it is not
part of this implementation.

The actual compiled C predicate passes10,000 independent set-based fixtures
and executes on all72 frozen diagnostic risk vectors. It adds54 action
instances across those vectors. These are arithmetic/support checks, not
new selected moves or wins. Both-color native protocol checks pass with
the flag off and on. No paired tactical or playing-strength gate has run.

The prototype is motivated by restoring a true-safe option in8/18
all-excluded terminal replays, on a loss-conditioned development cohort.
This is a hindsight ceiling. Fresh non-losing controls, same-belief paired
search and full-clock games must decide whether exposing these alternatives
helps or harms. No margin sweep is justified by this result.

Source: [native predicate](../../experiments/guard-disagreement-20261109/guard_envelope.h),
[build and independent C checks](../../experiments/guard-disagreement-20261109/prepare.py).
Receipts: build.json, correctness.json, protocol-smoke.json.
