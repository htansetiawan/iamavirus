# 008 — Fable: an outside review (Kimi K3, via the human) and what we take from it

The human pasted a review of the repo from another model. Point by point,
what is right, what is already done, what is not feasible, and who takes what.

| # | Claim | Assessment | Action / owner |
|---|---|---|---|
| 1 | Defence has an asymptote; add an offensive term for attacks on the enemy king region that the opponent cannot see | Half right. The matrix cells already carry `kInvisibleKingAttackBonus` (500 cp for an attacker the opponent cannot see) and the search's asymmetric win scores deliberately under-price speculative hunts. What is missing is the *positional* version: sliders on lines that run into the opponent's fog toward their king before any attack exists, which is exactly how duck beats us (39/52 punishing captures from far-half sliders). Measurable only by paired games, not the loss benchmark. | Fable, after the exposure gate: an "invisible line pressure" term in evaluation, gated by `compare_archives.py` vs the archived v5 bytes. |
| 2a | Make the learned opponent prior the default and gate it in the arena | Measured, not assumed: offline it predicts top-team moves far better (NLL 2.75 vs 3.09) but does not move king losses or en-prise rate on 634 real losing seats; the Greek Gift trap is taken 7/8 under it. It stays optional until a benchmark line moves. | Fable (benchmark of the memory prior running now), then belief is Astra's. |
| 2b | Persistence feature for pieces that just captured | Done this hour: per-particle last-move memory and two features; the data says the *last-moved* piece moves again 1.5× more often (+0.44), the just-captured-piece term is small (+0.08). Benchmark running. | Fable → hand-off to Astra. |
| 2c | Track truth-in-population as the KPI; keep the exhaustive consistent set while it is small (Obscuro / StrangeFish2) | Agreed; this is the structural belief change worth building. Opening/midgame consistent sets are small enough to be exact. | **Astra** (belief/recovery/successor coverage is its lane). |
| 3 | Opponent-specific priors selected by opponent id | **Not feasible as stated**: the protocol gives the bot only its colour and clock, never the opponent's identity. A prior conditioned on *observed play style* would need to be inferred within the game; parked. | — |
| 4 | Danger-head veto only after calibration | Agreed and already our stance; log-only until a calibrator and a benchmark line exist. | Fable, later. |
| 5 | Spend the clock where the decision is hard (entropy-scaled budget) | Good and cheap. Our games end with 60–150 s unused; the matrix game could get 8 s on plies where candidate risks are close or the posterior is diffuse, and 1 s where one row dominates. The "median 20-ply game" premise is stale (ours run 45–110 plies) but the conclusion holds. | Fable: implement after the v11 gate, measure by paired games and clock usage. |
| 6 | Upload the v11 exposure candidate; arena games are cheap information | Agreed; the human decides. Its paired lanes vs v5 (8 pairs, real clocks) are running and will give the controlled number either way. | Human. |

Net: nothing here changes the plan's order, two items are already done, one is
infeasible, and two (exact small-set belief; invisible line pressure) are the
right next structural experiments, one per lane.
