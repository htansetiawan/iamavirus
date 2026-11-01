# Future modeled mistakes materially inflate these continuation values

1 November 2026. All nine R2 diagnostic calls completed. On each of three
selected positions, beliefs and sampled worlds match across the three arms.
The comparison below holds one projected-response tree and our continuation
strategy fixed. It changes only what the opponent may do in that tree.

| Fixed root move | Current opponent profile V | Best response within all restrictions R | Restrict first reply only F | Unrestricted best response U |
|---|---:|---:|---:|---:|
| Bf1-c4, p0 White ply20 | -0.15725 | -0.26843 | -0.41307 | -0.52510 |
| Be7-g5, p0 Black ply31 | -0.23017 | -0.24150 | -0.45216 | -0.76813 |
| Nb8-d7, p1 Black ply17 | +0.14554 | +0.13853 | -0.80769 | -0.99329 |

These are searched utility units, **not win probabilities or Elo**. Leaf
evaluations, root loss utilities, sample selection and finite-tree coverage
remain approximate. Best response here respects shared information sets; it
does not independently minimize each hidden world.

## What is learned

For Nd7, removing restrictions on **future** replies while retaining the first
reply restriction reduces value by0.94622. Removing the remaining first-reply
restriction costs another0.18559. Only0.00701 separates the current response
from the best feasible restricted response. On this particular finite tree,
the optimistic value principally depends on future model restrictions, rather
than an unconverged opponent response. Raw unprojected responses show the same
pattern: future restriction gap0.92264.

This position is almost fully known: truth has99.8882% of both belief and
sample mass. More worlds or a new king-guard threshold does not address the
observed fixed-tree effect. This does not prove the historical Nd7 move is a
blunder: the earlier short exchange audit favored it over the alternative.
It shows that its favorable *searched continuation value* is fragile.

The first bishop example also has a direct continuation check. In the true
world after Bc4/Bxc4, projected restricted continuation is-0.76831; freeing
future replies gives-0.96972 on the **same tree with the same own policy**.
Thus the discrepancy survives after fixing the first capture. This closes
the specific question left open by212, where different arms had different
trees and continuation strategies.

## A separate root-purification effect

`V-R` is called `solver_slack` in the frozen raw format. For an unchanged
mixed root profile that is an opponent best-response gap. For a root action
forced pure after solving, it additionally includes the opponent's ability
to adjust to that newly fixed action; it must **not** be called evidence that
the original mixed-profile solver failed to converge.

For the unrestricted first-position tree, mixed-profile value is-0.21104 and
best response-0.21612, a gap of0.00508. Forcing its selected Bc4 instead gives
-0.21157 against the old response and-0.52574 against a new best response.
This is a fixed-tree purification vulnerability, not proof that randomizing
the arena bot will gain Elo. The separate stable-mix match pilot already
failed its advancement threshold; it is not silently reopened here.

Timed reconstructions remain variable: unrestricted selected Rd2 in212 but
Bc4 here. Each reported decomposition uses a single immutable tree, so that
cross-run move flip is not used as a causal comparison.

## Consequence for development

Do not continue the constant25%-at-every-opponent-decision configuration just
because the predictor beats an average likelihood baseline. Filtering provable
visible losses did not remove future-response optimism. The211 match pilot
is1W–5L with two original games still live at this report, below the4/8
requirement for a larger trial even if both remaining games win.

Two distinct repairs deserve review: confidence calibrated for searched
information sets, or a persistent learned/adversarial opponent mode at the
subgame root. Neither has been implemented or validated by this audit. A
persistent mode changes the uncertainty model; it does not make a mistaken
opponent predictor correct. Root purification and approximate leaf values
remain separate limitations.

The original RNR formulation mixes whole strategies using reach probabilities,
which differs from constant local interpolation. The DBR paper deliberately
makes confidence depend on evidence at an information set and uses zero when
there are no observations; it also documents RNR overfitting. These papers
motivate alternatives, not a claim that one will improve this bot:
[Computing Robust Counter-Strategies](https://poker.cs.ualberta.ca/publications/NIPS07-rnash.pdf),
[Data Biased Robust Counter Strategies, §5](https://proceedings.mlr.press/v5/johanson09a/johanson09a.pdf).

An illustrative calculation, not an empirical error rate: in a five-reply
abstract trap, suppose the fixed model always makes a decisive mistake and
the adversarial response never does. A local25% fixed component gives trap
utility `1 - 2*(.75**5) = +.52539`; a persistent25% model mode gives
`.25*(+1) + .75*(-1) = -.5`. This explains how a seemingly small *local*
confidence can induce a substantially different planning objective.

## Verification and provenance

- Nine legal first attempts under the **new R2 plan**, published at
  `0a06278706027b654f8ed37ff2cc7d8e82aa571a` before execution.
- 172 replay frames and13,974 aggregation, legal-reply, state/probability and
  nested-value checks pass. True states are joined only after process exit.
- 72 best-response comparisons against19,584 exhaustively enumerated policies
  pass optimized and ASan/UBSan. Four full trace-hook checks cover model off/on.
- Every real tree passes layering and perfect-recall checks. Solver/tree state
  hashes are unchanged after the audit. No extra CFR iteration or tree growth.
- The entire audit, including output for3 root profiles, takes39–72ms here.
  This is diagnostic timing, not a production-search speedup benchmark.
- Original213 failed its first diagnostic call due to an audit-only null-array
  hash read. Original source/build/failed receipt remain in the sibling
  `response-best-reply-20261101` directories; R2 does not erase that failure.
- Three selected development positions cannot estimate population failure
  rates or full-game exploitability. No new policy, model, ZIP or deployment.

`analysis.json`, all `.br.json` and `.trace.json` files, receipts, plans and
native/Python sources preserve the evidence. Cores4–5 are released. No GPU used.
