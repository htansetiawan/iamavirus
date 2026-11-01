# 190 Fable: drawing the worlds from a flatter weighting is null

To Astra. 1 November 2026, 04:40Z.

After the worlds sweep (188) the user asked what improves the belief weights. The one evidence-backed, untested change was the draw's sharpness: v34's power-2 weighting was kept for the king guard, the belief.c suite note says sharpening the draw alone measured as nothing, and the 30 October calibration says the sharp weighting is the more under-confident one about unseen attackers. In v35 the temperature is applied when the weights are stored, so the draw and the guards cannot be separated by settings. One change on mist-c branch `draw-temp` (a66abb2, from the v35 source): `belief_sample` draws with weight^(draw/model) over the stored weights when `MIST_DRAW_TEMP` is set; unset it is v35's arithmetic; the guards are untouched.

Suite, check and fatal kinds, 487 decisions, 2.5 s, seed 1, paired with the 32-world arm of 188 (same bytes otherwise):

| Draw temperature | Fatal of 399 | Fixed / broke vs v35 | Net | Same move as v35 | Distinct worlds (median) |
|---:|---:|---:|---:|---:|---:|
| 2 (v35) | 107 | — | — | — | 26 |
| 1.0 (fitted) | 108 | 5 / 6 | −1 | 86% | 30 |
| 0.7 | 105 | 6 / 4 | +2 | 81% | 31 |
| 0.5 | 109 | 6 / 8 | −2 | 81% | 31 |

Offline, on the 60-game v35 traces (test_belief, history table on): the fitted weighting lifts the truth's geometric-mean share from 0.0075 to 0.0119, but its presence in a 64-world sample moves from 60.1% to 61.3%, and a 0.7 draw lowers it to 58.5%. Flattening lifts the tail and lowers the head by the same amount; the draw sees the truth no more often. Same shape as 187: a global change to the weighting cannot put weight on the right worlds at the right decisions.

Closed on the belief side now: more worlds (188), draw sharpness (this), state-level attack re-weighting (187), world discriminator (183), better average-fit linear model (v23, 185). Left: a refit with a tail objective measured at the loss decisions, and opponent-specific models. No bench, no deployment change. Cores 2–5 released. Details `fable-submissions/analysis/draw-temp-20261101/result.md`.
