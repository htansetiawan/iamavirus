# Persistent mode passes the decision gate; strength remains unmeasured

1 November 2026. All 156 first-attempt calls completed across 39 decisions
from eight new v37 games. The gate/source were published at
`94acec9c50c8d188f7923de32b414f9613d60690` before execution. The model, prior,
source, seed and thresholds were unchanged during evaluation.

| Diagnostic | Exact v37 | Local projected response | New code disabled | Persistent mode |
|---|---:|---:|---:|---:|
| Immediate king losses | 2 | 2 | 2 | 2 |
| Exchange loss >=2 points | 0 | 0 | 0 | 0 |
| Net queen loss >=4 points | 0 | 0 | 0 | 0 |
| One-point exchange exposures | 1 | 2 | 2 | 3 |
| Median nodes | 89,001 | 83,487 | 91,655 | 85,545 |

Persistent mode changes 17 choices versus disabled code; disabled code changes
four versus exact v37. Both shared king losses have safe alternatives in the
true position. This candidate repairs neither. Zero positive queen-loss cases
do not validate the queen guard. This panel is a mechanism/safety comparison,
not a win-rate estimate; most different choices have identical short labels.

All 39 candidate calls meet the first-reply reach threshold. Median neural
query time is 7.04 ms, peak reported process RSS 321.1 MiB. Median paired node
ratio versus v37 is 0.991, iteration ratio 0.984; median model-mode expansion
share is 0.249. These are finite-time diagnostics, not claims of equal useful
search depth or stronger play. Full-prefix elapsed time reaches 42.5 seconds
in the longest cases, in controls as well as candidate; actual search cap is
2.5 seconds after reconstructing the history.

## Independent review

The course referee independently agrees on all 780 replay frames, legal move
sets and 5,283 transitions across 68 unique candidate moves. It recomputes
bounded king/material/queen labels separately from exchange_probe. Detailed
changed choices are in `referee-review.json`, all labels in `labelled.json`.

A disclosed small regression: against Knight Vision at `hvbdrq3p:48`, `f2f4`
allows a one-pawn exchange loss; original/disabled `h7d3` does not. At
`pd199l82:135`, persistent and disabled both permit a one-point loss that the
original does not. These remain below the predeclared two-point gate; no gate
was relaxed. Quiet forcing continuations and longer exchanges remain outside
the label's horizon. Equal labels are not evidence of equally good moves.

`manual-review.json` admits only a bounded full-clock pilot. It does not
approve a release. All source, checks and initial prototype failures remain
available under experiments/persistent-response-20261101 and this directory.
The low-bit mode-tag collision was caught by the native fixture and fixed
before this replay gate; it is not a defect found in the deployed bot.

## Full-clock plan

`full-games/plan.json` freezes eight first-attempt games against exact v37,
180+2, both colours and two reserved core pairs. A score <=2/8 closes the
configuration. Otherwise eight authentic-local-Misty games compare four
candidate and four v37 games with matched sides/seeds. Only H2H >=4/8 and a
candidate Misty score at least equal to control, without technical faults,
can earn review for a larger trial. Neither small panel earns a ZIP or Elo
claim. Misty's local implementation is authentic, not verified arena bytes.

Three wrapper smoke checks pass. Source/model/history/Stockfish/referee and
Misty dependency hashes are pinned. Plan is published before launch. The
original runner and child-process identities govern waiting and cleanup;
started games are never silently repeated. No GPU is used.
