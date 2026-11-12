# One fixed-history v38 decision for the presentation

The [human walkthrough](../../../docs/presentation-move.md) connects the
private input, exact early belief reduction, root guards, Stockfish values,
first two regret updates and final action on the same decision. This is a
teaching reconstruction, not a new candidate or the original arena trace.

The two original calls completed once in 4.77 seconds total. All 19 control
C/header members, scorer and history bytes match the v38 ZIP. The trace
copy inserts output-only annotations in main.c, gtcfr.c and cfr.c; no
original source lines are removed or replaced. Both builds have no compiler
diagnostics. Read-only review independently checks the course-rule state
enumeration, all 32 initial utility conversions, first two root updates
and normalization/argmax of the final strategy.

The fixed early history reduces **1 → 1 → 14 → 1 → 1**. It therefore searches
one world, not 32, with 32 legal root actions and no guard exclusions.
The final largest-probability action is e3 at 53.1496%; both control and
trace choose it. This does not establish equivalence under other timings
or seeds, a quality improvement, full common knowledge, or an equilibrium.

The case was fixed before either output. Its one-world result is retained
rather than replacing it with a more visually uncertain case. The existing
[weighted-sampling explanation](../../../docs/presentation-tables.md) and
[two-world numerical fixture](../presentation-pcfr-20261111/README.md)
answer different questions.

[Plan](plan.json) · [Execution](execution.json) ·
[Checked numerical result](result.json) · [Source annotations](trace-annotations.patch) ·
[Runner](../../tools/trace_presentation_decision.py) ·
[Independent reviewer](../../tools/review_presentation_decision.py).

Raw input and logs remain in
`data/astra-spool/presentation-real-decision-20261111/`. Only recorded White
views, clocks and the two forced earlier own moves reach the engine. Truth
is used afterward by the reviewer. Search is shortened to two seconds, and
annotation overhead can change its work. No model fit, match, GPU run,
package, version reservation, commit, push or deployment occurred.
