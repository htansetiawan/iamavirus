# Drawing the search's worlds from a flatter weighting: null

1 November 2026 (run 31 October 23:22Z to 1 November 04:28Z). The one belief change proposed after the worlds sweep: draw the 32 worlds from the fitted weighting instead of the sharpened one, with the guards unchanged.

## Why this was the candidate

- v34 raised the belief's weights to the power 2 (`MIST_MODEL_TEMP`, default 2). The suite note in `src/belief.c` records that the gain came through the king guard's risk estimate, and that sharpening only the search's draw, with the guard on the fitted weights, measured the same as no sharpening. The sharp draw has stayed since without a measured benefit of its own.
- The hazard calibration of 30 October found the belief under-confident about an unseen attacker by 2 to 4 times under the fitted weighting and 2 to 7 times under the sharp one. The attacker is always among the worlds, only under-weighted.
- The v35 engine applies the temperature once, when the weights are stored, so the draw and the guards share it; `MIST_MODEL_TEMP=1` would also strip the guards of their sharp rule. The test needed one change.

## The change

Branch `draw-temp` of mist-c, commit a66abb2, one file: `belief_sample` draws with weight^(draw/model) over the stored weights when `MIST_DRAW_TEMP` is set (a scale of draw/model on the stored log-weights). Unset, the scale is 1.0 and the arithmetic is v35's. The guards keep their sharp and fitted weightings. Built from the v35 source (97b60f1) so that the baseline is the 32-world arm of the worlds sweep: same bytes otherwise, same suite, seed 1, 2.5 s a decision, two workers, v35's history table and Stockfish.

## Offline check: the truth's share on the v35 traces

`build/test_belief tests/traces-v35.txt 200000` with the history table, 60 v35 games, 3,327 plies with the belief exact:

| Weighting | Truth's share, geometric mean | x uniform | Truth in a 64-world sample |
|---|---:|---:|---:|
| stored (sharp, v35) | 0.0075 | 2.2 | 60.1% |
| fitted (`MIST_MODEL_TEMP=1`) | 0.0119 | 3.5 | 61.3% |
| draw at 1.0 over the stored weights | 0.0075 (stored) | | 60.9% |
| draw at 0.7 | 0.0075 (stored) | | 58.5% |

The fitted weighting lifts the truth's typical share 1.6x, but the chance that the draw contains the truth moves by less than one point, and a flatter draw lowers it. Flattening lifts the tail and lowers the head by about as much.

## Suite: check and fatal kinds, 487 decisions, 399 with a safe move, paired with v35's draw

| Draw temperature | Fatal of 399 | Fixed | Broke | Net | Centipawn loss, mean diff | Same move as v35 | Distinct worlds, median |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 (v35) | 107 | | | | | | 26 |
| 1.0 | 108 | 5 | 6 | −1 | −0.4 | 86% | 30 |
| 0.7 | 105 | 6 | 4 | +2 | +0.5 | 81% | 31 |
| 0.5 | 109 | 6 | 8 | −2 | −3.4 | 81% | 31 |

By kind: check 61 / 62 / 59 / 59, fatal 46 / 46 / 46 / 50. Every net is inside the noise floor of about five flips; nothing earns the 100-game confirmation. The rise in distinct worlds (26 to 30 or 31) confirms the setting reached the engine; the suite log does not carry the start-up line.

## Reading

1. The draw's sharpness is not a lever, in either direction, at this budget. The sharpened draw adopted in v34 does nothing on its own, and the fitted or flatter draws do nothing either.
2. The reason is the same as for the attack re-weighting (note 187): the belief is under-confident at the losses, but a global change to the weighting moves weight to and from the truth in equal measure across decisions. The truth's typical share rises 1.6x and its presence in the draw does not. What is needed is weight on the right worlds at the right decisions, which only a model that is better on the opponent's surprising moves can supply.
3. Routes now closed on the belief side: more worlds (31 October), sharper or flatter draw (this), state-level attack re-weighting (187), a world discriminator (183 final), a better average-fit linear model (v23, level in 100 games). What remains is the tail objective (a refit that protects unlikely moves, measured at the loss decisions) and opponent-specific models.

## Caveats

- One seed; 2.5 s a decision on the suite against 4 to 8.5 s in the arena; material kind not run.
- The share check is on our own v35 games (the opponent is v35), the arena-opponent figure would be lower, as in 184.
- The draw worktree keeps v35's source otherwise; the change ports to main in the same function if ever wanted.

## Files

- Suite outputs and log: `~/fable-persist/suite/draw-T{1.0,0.7,0.5}-cf.json`, `draw-sweep.log`; baseline `worlds-32-cf.json`.
- Share check: `~/fable-persist/suite/draw-share.txt`.
- Engine: `~/fable-persist/mist-draw` (mist-c branch `draw-temp`, a66abb2, build sha256 7212dcdab76c).
