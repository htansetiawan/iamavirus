# Same-tree opponent best-response audit

1 November 2026. This follows diagnostic212, where the same beliefs and samples
gave different continuation values despite assigning the first punishing
capture high probability. It does not train a model, select a confidence, or
change the currently running211 candidate.

On each freshly reconstructed tree, keep our continuation strategy, all leaf
values, information sets and chance probabilities fixed. Evaluate four values
to us, in this order:

1. Current opponent profile (`V`).
2. Opponent best response within the existing local mixture restrictions (`R`).
3. Opponent best response with that restriction only on its first decision;
   later opponent decisions are unrestricted (`F`).
4. Unrestricted opponent best response (`U`).

Feasible sets are nested, so `V >= R >= F >= U`. The exact decomposition
`V-U = (V-R) + (R-F) + (F-U)` separates current solver slack, the effect of
future response restrictions, and the residual first-response restriction.
It is conditional on this ordering and this finite tree, not a unique
attribution of full-game losses. We do not optimize our continuation again.

The linear-time evaluator first propagates chance/our-policy reach, excluding
the responding player's reach. It then aggregates child utilities across each
responding information set and chooses one free action for all its member
nodes, working backward by depth. Each responding information set is checked
for equal depth and the same previous own information-set/action pair. These
checks validate the layering and perfect recall required here. It never gives
the opponent a different action merely because a hidden world differs.

Space and time are O(nodes + edges + action slots) for one response evaluation;
the same topology index is reused. There is no global sort or repeated
64-pass policy improvement. This is diagnostic efficiency, not a playing
strength improvement or a measured speedup of the production search.

Validation uses six imperfect-information fixtures, unequal/zero chance
weights, both player signs, pure and mixed fixed policies, confidence0/.25/.75/1,
and two responding decisions with remembered own actions. An independent
Python oracle enumerates every deterministic free policy and compares all
three restriction modes. Optimized and ASan/UBSan builds must agree; an
imperfect-recall fixture must be rejected.

After correctness, freeze nine calls: the same three212 positions, unrestricted,
raw and projected arms, original seeds/recorded clocks, maximum10s, cores4–5,
120s per call. The root profiles inspected are the search mixture, its chosen
pure move, and the two previously identified alternatives. A missing root
action is not reinserted through a guard. All variants are evaluated inside
each new tree; cross-run trees may differ. Truth joins only after engine exit.

The post-decision export preserves state hashes and independently recomputes
its values. No extra CFR iteration, tree growth, rule change or neural query
is allowed. Stop on invalid output, failed invariant or changed input. Preserve
failed first attempts; no automatic repeats. Publish plan/source before calls.

This is three selected development cases, not a holdout, strength estimate,
full-game exploitability bound or release. A positive diagnostic is a reason
to choose the next structural experiment, not to ship a ZIP.
