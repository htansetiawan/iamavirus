# Queen safety cases: decision-time visibility matters

This offline collection covers all 63 cached IAmAVirus games completed from 20:00 through 23:33:07 UTC on 1 November. All played arena v37. It preserves **103 decisions**: all 40 next-reply queen captures plus one ordinary queen-present control per game. Forty captures split into 36 recorded net losses below four points and four at least four points after our next response. These are deliberately selected diagnostic cases, not population calibration or a strength estimate.

The independent course referee agrees on all 5,553 replay frames and the played-action tactical labels across 10,638 checked transitions. The one-capture/one-safe-response probe confirms three queen losses of at least four points. No candidate has been run on these inputs yet. Earlier suites and experiment 214's acceptance rules are unchanged.

## A selection blind spot, not a changed taxonomy definition

The existing `queen_exposed_unseen` tag measures the attacking piece's visibility **after our move**. This is different from whether the defender was hidden when we chose the move. Of the 40 actual queen capturers, 37 were hidden before our decision, four remained hidden afterward, and 33 were revealed by our own move. The existing tag is present in six cases (it can refer to another attacker). Selecting solely by that tag misses a distinct, relevant family.

All four recorded large queen-loss cases had a capturer hidden before our move and visible afterward; none had the existing tag:

| Game / decision | Opponent | Our move / reply | Net loss after recorded response | Best safe one-response loss |
|---|---|---|---:|---:|
| 23paw9tn / 20 | HYPOTHERMIA | Qd2xf4 / Qc7xf4 | 6 | 6 |
| 9ospae7x / 52 | Lost Signal | Qe2-b5 / Rb7xb5 | 4 | 4 |
| ncejetlc / 48 | Foggy Fischer | Qd3-g3 / Rg8xg3 | 4 | 4 |
| ko8mswoh / 55 | TA Baseline S | Qc8-f5 / Qd3xf5 | 9 | 0 |

In ko8mswoh, g6xf5 and Nh4xf5 both recover equal material within the probe; the game chose Re8-e1. That distinguishes an available recovery from unavoidable immediate queen loss. It does not prove the rook move is strategically wrong: longer tactics and information are outside this material probe. Recorded replies are never applied after a hypothetical candidate move diverges.

## What this changes next

Use pre-decision visibility alongside post-move exposure when curating tests. Keep the three verified large-loss positions, the recoverable case, and the 63 ordinary controls so a new guard cannot win by rejecting every queen exchange. The other 36 captures show why "hidden capturer" alone is not a bad-move label. Before any model change, reconstruct its predicted risks and determine whether the attacker is absent, underweighted, passes the guard, or is handled poorly in the continuation.

`curated/cases.json` pins replay hashes, source hashes, labels and permitted input files. `visibility-audit.json` preserves both visibility times and the best safe responses after each actual capture. True boards, opponent views and future replies stay offline. `attempt-1/` preserves a curation-only relative-path error; the corrected run used a separate output directory and completed. No playing engine, model, guard or deployment changed.
