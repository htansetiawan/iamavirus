# Eight queen decisions: no repair and no new regression

All 24 frozen calls completed successfully: eight decisions, three arms, exclusive cores 4–5, 2.5-second search cap and original recorded clocks. The checked 214 replay runner was reused with frozen v37, feature-off and persistent-mode binaries. True positions were joined only after the engines exited. Independent referee checks agree on 341 frames and 3,063 counterfactual transitions.

| Arm | Immediate king losses | Queen net loss >=4 | Material loss >=2 |
|---|---:|---:|---:|
| Exact v37 | 0 | 3 | 3 |
| Persistent binary, feature off | 0 | 3 | 3 |
| Persistent candidate | 0 | 3 | 3 |

All three arms choose the same move in all four recorded large-loss cases. The off control also matches v37 on all four ordinary controls. The candidate changes those four control choices without changing their tested failure labels. It does **not** repair these queen losses; it also introduces no new labelled loss on this small panel. These are selected diagnostics, not a win-rate estimate or a replacement of experiment 214's frozen match gate.

## Two different mechanisms survive unchanged

Existing stderr, captured during the original calls, shows:

- `23paw9tn:20`, HYPOTHERMIA: v37 assigns Qd2xf4 queen-loss risk 0.694 under fitted weights and 0.857 under sharper weights. The combined king/queen guard leaves only this move among 35 candidates. Search cannot choose an alternative once the guard has removed it. This is not an example of the queen risk being missed; the combined risk rule considers the alternatives worse. Whether the posterior/rule is appropriate requires a separate diagnosis.
- `9ospae7x:52`, Lost Signal: Qe2-b5 has logged risk 0.001/0.000; it survives the guard. The printed zero is rounded and is not proof of absent support.
- `ncejetlc:48`, Foggy Fischer: Qd3-g3 has logged risk 0.005/0.000 and also survives. Here the belief has 11 worlds and all 11 are searched, so merely increasing the number of sampled worlds cannot add support missing from this belief or fix its probabilities.

`guard-evidence.json` retains these lines for every arm. They are original run diagnostics, not extra instrumented reruns. The recovered fourth case, `ko8mswoh:55`, has equal-material recaptures in the limited probe; this screen tests the move before the queen exchange, not the later decision to decline recapture.

The full-clock 214 pilot separately finished 7W–1L against exact v37 and has advanced to its already-planned Misty control comparison. That match result does not erase these inherited queen weaknesses. No source, model, guard threshold or acceptance rule changed during this screen. No ZIP or deployment follows this diagnostic.

Published source/plan commit before execution: `4d1a09d7510cfc760109a5fc91a0e57d2ec80e80`. Original handle 51601 exited 0; independent summary handle 99988 exited 0. `terminal.json` verifies no remaining screen engine workers on cores 4–5. Inputs, raw receipts/stdout/stderr, labels and hashes are retained for review.
