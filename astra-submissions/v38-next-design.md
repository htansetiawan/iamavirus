# After the v38 gate: one design choice for review

8 November 2026. **Proposal only; no new experiment or candidate launched.**
The existing v38 scorer and its failed promotion gate remain unchanged.

The current candidate won 11½/16 against v37 but scored 9/14 clean points
against Misty, compared with v37's 10½/14. This is insufficient to distinguish
sampling noise, matchup effects and a harmful evaluation change. Do not claim
the cause is known. An explicitly experimental arena trial of the existing
bytes remains a separate human choice in [the review](v38-review.md).

## The distinct implementation worth considering

Use the original scorer for selected consequential expansions and the fast
all-child scorer for the rest. Select the scorer before installing the new
children's values. Do not overwrite a child's value after it has become an
internal search node; that would erase its searched continuation. This requires
a copied native engine experiment under Astra, with Fable reviewing the search
interface; Fable's checkout remains untouched.

The rationale is measured, though the benefit is unproven:

- Stockfish calls consume 82.2% of v37's search wall time. Optimizing the CFR
  kernel alone already failed to buy substantial additional whole-engine work.
- The packaged fast scorer is 1.57–1.68× faster. More search did reach the solver.
- The fast scorer is an approximation: the warmed frontier panel had 74.2%
  top-choice agreement, including a reference-value regret of 0.503 in one
  position. Its low average error does not ensure harmless decision errors.
- The existing compact MultiPV student failed badly; this proposal keeps the
  working native tactical scorers and requires no neural training.

The original scorer is a comparison target, **not a Fog of War oracle**. Warm
transposition tables and move ordering also depend on the query stream. Routing
only some queries to it cannot be described as reproducing v37's exact scores.
Nor does this fix belief support, guard exclusions or omniscient leaf bias.

## Cost and the first question

Let the fast scorer have speed ratio `s` and let fraction `f` of otherwise
similar-cost parent queries go to the original scorer. If routing occurs before
scoring, normalized scorer cost is `(1-f)/s + f`. If every query is scored fast
first and a fraction is then rescored, the more conservative cost is `1/s + f`.
These assume comparable query costs; actual measurements must sum time, not
just count queries.

At `s = 1.6` and `f = 0.1`, with the measured 0.822 scorer wall share, those
models predict whole-search fixed-work speed ratios of approximately **1.38×**
and **1.29×**, respectively, before routing overhead. They are feasibility
calculations, not measured performance or Elo estimates.

The useful question is therefore: **can a small portion of original-scorer
work correct most consequential approximation errors?** Simply rescoring
random parents, all root moves or every king move has not earned that claim.

For a fixed tree and fixed strategy, the change to one root action's value is
`sum(reach(leaf | action) * leaf_value_error)`. That identity can locate large
contributions. Sum the absolute contributions separately for each root action,
then average those action totals equally for the diagnostic. Group current
frontier children by the parent query that supplied their values; do not count
an earlier value that has already been replaced by deeper search. The signed
root-value differences and rare dangerous branches must also be reported.
This contribution measure is not a bound on the re-solved CFR strategy: the
strategy, tree growth and opponent responses can all change.

## Small feasibility study to agree before execution

1. Freeze 24 recent, previously unused source games by game-ID hash, selected
   without results. Use our v37 seats against the instructor, duck, HYPOTHERMIA,
   Mist Opportunities and the leading teams. Publish IDs, versions and color
   counts before computing scores. Keep complete games grouped.
2. Capture the native parent queries and their tree context using only actor
   observations and forced own moves. True boards may label errors afterwards;
   they must not enter routing inputs. Compare the two scorers with pinned
   cold/warm stream controls and record missing or unsupported calls.
3. On the fixed captured trees, first measure an **oracle diagnostic ceiling**:
   how much absolute error contribution could a 10% original-scorer time budget
   remove? Use the fractional-knapsack upper bound: sort parents by contribution
   divided by measured original cost, allowing a fractional final parent. This
   gives an optimistic ceiling, not an executable routing policy or the exact
   integer optimum. It uses both scorers' outputs. If even that ceiling removes
   less than half the contribution measure, stop before fitting a selector or
   launching games. Removing half this bound does not promise to halve the
   signed error, improve a move, or improve the re-solved strategy.
4. If the ceiling is useful, bring its results back for review. A later selector
   must use available pre-call information, survive fresh held-out games, and
   demonstrate a real clock advantage. The oracle selection itself cannot be
   shipped. No automatic full-game gate follows the diagnostic.

Proposed bound: 30 minutes of CPU collection/analysis on one reserved core pair,
no GPU, no parameter sweep, all first attempts retained. Instrumentation parity
and the number of captured parents determine whether that bound is achievable;
if it is not, report insufficient evidence instead of silently extending it.
The historical v38 Misty panel stays closed and is not reused for promotion.

This is a proposed next mechanism, not an agreement with Fable and not a
promise of a replacement ZIP today. The alternative is a transparently labelled
arena experiment of the already validated v38 bytes, with the failed local
gate and withdrawal rule disclosed.

Evidence: [whole-search cost](../chatroom/255-astra-whole-search-cost.md),
[frontier fidelity](analysis/sf-allchildren-20261102/frontier/README.md),
[failed learned substitute](../chatroom/249-astra-amortized-multipv.md),
[final v38 review](v38-review.md).
