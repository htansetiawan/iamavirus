# Refit of the move model on every arena game, 1 November 2026 (v37)

Question (the user, 31 October and 1 November): v35's belief weights were fitted on 2,029 games
from 30 September to 10 October. Since then the arena has played far more. "Why only 2,029 ...
fit in more games ... you cannot make a conclusion it did not matter without testing in the
arena." This file records the refit on all games, the regression-suite arms, the 100-game lane
against v35, and what is left for the arena trial.

## What was refitted

The move model is the formula in Appendix F of the book: 28 yes/no or small-number facts about a
move (is it a capture, what it takes, which piece moves, does it castle, does it leave a piece
hanging, ...), each with a weight, summed and turned into a probability over the mover's legal
moves. The weights are found by asking which values make the moves the bots actually played
most likely (a conditional logit fitted by Newton's method). The full model uses all 28 facts;
the cheap model, used when the belief holds more than 10,000 boards, uses the first 18.

Data: every arena game downloaded by 31 October, 174,386 games from 1 September on, split by
game into 148,357 for fitting and 26,029 held out (seed 7, 15%). Our own moves are left out of
the fit and reported separately. Fitted positions 9,901,850; held-out positions 1,734,620 (plus
77,825 of ours). Feature extraction `tools/move_features.c` (v35 tree), fitter
`tools/fit_move_model_stream.py` (mist-c a1bd043), which streams the 35 GB feature file in
512 MB chunks and converges in four Newton passes.

Earlier step on the way here (31 October): the same 28 facts refitted on 6,776 games scored
0.631 nats / 26.5% top-1 against v35's 0.623 / 26.1% on the 29 October held-out file (a
different test set from the one below).

## Fit result

Held-out score: nats per move over a uniform guess (higher is better) and how often the most
likely move under the model is the one played (top-1).

| Weights | Fitted on | Nats over uniform | Top-1 | Held-out positions |
|---|---|---:|---:|---:|
| v35 full (10 Oct) | 2,029 games | 0.6375 | 26.73% | 1,734,620 |
| all-games full | 148,357 games | 0.6452 | 27.05% | 1,734,620 |
| v35 cheap (10 Oct) | 2,029 games | 0.4718 | 24.50% | 1,734,620 |
| all-games cheap | 148,357 games | 0.4743 | 24.83% | 1,734,620 |

Seventy-three times the games moved the full model by 0.008 nats and 0.3 points of top-1. For
scale, the oracle experiment (`fable-submissions/analysis/oracle-*`, 29 October) put the gap
between the natural belief and the one that wins at about 60 times in weight on the true board;
0.008 nats is a 0.8% change in the odds the formula gives the played move.

Per opponent, the bots that matter most:

| Opponent | Held-out positions | v35 nats / top-1 | all-games nats / top-1 |
|---|---:|---|---|
| Strongly_Invisible | 272,166 | 0.657 / 26.2% | 0.672 / 26.6% |
| Instructors | 268,452 | 0.602 / 24.8% | 0.612 / 25.1% |
| Knight_Vision | 148,706 | 0.733 / 27.2% | 0.748 / 27.5% |
| TA_Baseline_S | 103,975 | 0.726 / 33.9% | 0.743 / 34.3% |
| Decent_Chess_Bot | 102,979 | 0.702 / 26.0% | 0.717 / 26.4% |
| Greek_Gift | 94,683 | 0.658 / 25.3% | 0.677 / 25.7% |
| duck | 88,207 | 0.668 / 26.5% | 0.681 / 27.0% |
| Mist_Opportunities | 71,079 | 0.618 / 25.8% | 0.628 / 26.2% |
| HYPOTHERMIA | 59,991 | 0.580 / 23.4% | 0.598 / 23.9% |
| IAmAVirus (ours, not fitted) | 77,825 | 0.589 / 24.5% | 0.593 / 24.9% |
| Apricot_Squad | 44,072 | 0.041 / 14.9% | −0.030 / 15.1% |

Every large opponent gains a little; the near-random bots (Apricot_Squad, Czechmate,
Bit_Gambit, Resting_Bishop_Faces) lose a little, as a fit to the average must.

Weights that moved most (index: fact, v35 → all games): 1 captured value 4.22 → 6.16;
10 promote to queen 1.67 → 2.88; 11 underpromote −0.53 → −1.19; 21 value left hanging
−1.21 → −1.55; 22 moving piece left capturable −2.56 → −3.24; 23 moving piece left undefended
−2.41 → −3.12; 0 capture 1.09 → 0.83. The field of late October takes more and hangs less than
the field of early October did. Facts 2, 26 and 27 stay at 0 as in v35.

Full arrays: `fit-all-full.json`, `fit-all-cheap.json` beside this file (key `final.c_array`; `refit-eval-v35cheap.json` is v35's cheap weights scored on the same games); candidate source `mist-c` branch `allfit` (from 97b60f1, v35's tree).

## History table

The same export gives a new history table (`tools/history_table.c`, min 2 games, our own games
left out): 359,889 records against v35's 151,316 (13 October). It is the second half of the
candidate: the formula gives the prior, the table replaces it where the exact opponent view and
move sequence has been seen three or more times.

## Regression suite

Three arms, 09:00 to 10:05Z on 1 November, cores 2 to 5, each paired with the v35 baseline arm (`worlds-32-cf.json`: exact v35 bytes, v35's table, 32 worlds, 2.5 s a decision, seed 1, the suite's 487 check-and-fatal decisions, 399 with a safe move). A fatal decision leaves our king capturable on the true board while a safe move existed. The noise floor between identical runs is about five flips each way; the gate for a candidate bench is net +10.

| Arm | Fatal of 399 | Fixed vs v35 | Broke | Net | Centipawn loss, mean |
|---|---:|---:|---:|---:|---:|
| v35 baseline | 107 | — | — | — | 88.6 |
| v37: new weights + all-games table | 106 | 12 | 11 | +1 | 89.4 |
| New weights, v35's table | 106 | 9 | 8 | +1 | 82.7 |
| v35's bytes, all-games table | 108 | 5 | 6 | −1 | 93.6 |

By kind (fatal where a safe move existed): check kind, 300 decisions: 61 / 59 / 57 / 62; fatal kind, 99 decisions: 46 / 47 / 49 / 46. Centipawn differences per decision: +0.8, −5.9 and +5.1 against v35, each inside what two reruns of the same setting show.

Reading: every arm is within the noise floor. Neither the refitted weights nor the larger table changes which of these 487 decisions the engine gets right. The gate is not met; v37 is v35 on the suite. Files `refit-{both,theta,table35}-cf.json` beside this file.

## 100 games against v35

Queue `data/arena_local/queue-v37.json`: 100 unforced games, 50 colour-swapped pairs, 180+2, seed 420000 (held out), both core pairs. Started 10:07Z on 1 November; the machine was rebooted at about 14:40Z with 73 games recorded; the runner resumed from its ledger at 14:57Z and finished the remaining pairs by 17:05Z (three games of pairs 36 and 39 were replayed after the interruption; the table counts the first recorded game per pair and colour, 100 games). The runner exited without marking its receipt complete; the ledger holds every game, all attempts `ok`.

| | Games | W-D-L | Score | White | Black | Pairs (sweeps v37 / v35 / split) | Pair bootstrap 95% |
|---|---:|---|---:|---|---|---|---|
| v37 vs v35 | 100 | 56-2-42 | 0.570 | 32.5/50 | 24.5/50 | 50 (18 / 10 / 20, two with a draw) | 0.47 to 0.68 |

Every game ended by king capture except two threefold repetitions; no forfeit; no loss under 40 plies; lowest end clock 19.9 s for v37 and 20.0 s for v35. Before the reboot v37 scored 0.534 over 73 games, after it 18-0-9 over 27; nothing in the setup changed between the two stretches that I can point to, so the split is reported, not explained. A level engine scores 57 or more out of 100 about one time in twelve; the bar for a candidate is about 80. So: probably a little better than v35, far from the bar, and the same engine on the suite.

## In the arena

Uploaded by the lead at about 14:40Z on 1 November as arena version 37. First read at 17:06Z, 32 games: 16-1-15 (0.516), White 8.5/16, Black 8.0/16; rating 1890.8 before the first game, 1889.7 after 32 (K = 8), rank 10. v35's lifetime arena score was 0.517, so v37 is holding v35's pace. Losses: Decent Chess Bot 0-4, Strongly Invisible 1-3, duck 0-2, Crimson Fog 0-2; wins over HYPOTHERMIA 2-0, TA Baseline S 3-1, TA Baseline P, RATIRL, Sausage, Mu1tip13 2-0 each. One queen lost to an unseen capturer in 32 games, no clock under 15 s, no loss under 12 plies (`data/reports/v37-watch.md`). The fail-fast point of the v36 trial (48 games, 0.323 then) passed at 18:26Z: 50 games, 25-3-22 (0.530), White 13/25, Black 13.5/25, rating 1901.9 (+11 since the upload), rank 10. Worst opponents so far: Strongly Invisible 1-0-5, duck 0-0-4, Decent Chess Bot 1-1-4. v37 stays live; the tracker (`~/fable-persist/v37/track.sh`, tallies in `track.log`) wakes on a bad turn (two standard deviations under v35's pace, or rating under 1870) or every two hours. At 21:49Z, 109 games: 58-4-47 (0.550), White 30.5/54, Black 29.5/55, rating 1896.8, rank 10; worst opponents Crimson Fog 1-0-5, Knight Vision 0-0-4, duck 1-1-8.

## What this says

More data did not make a stronger bot. Refitting the formula on 73 times the games moved its held-out score by one percent, left the suite's 487 decisions unchanged within noise, and gave a 100-game lane score of 0.570 against v35 (0.47 to 0.68), with the arena's first 32 games at v35's own pace. The 29 October refit that changed the form of the formula (more facts, piece-square tables) moved the held-out score twenty times further and was level in play; this one moved it a little and is level to slightly better. Either way the belief's weighting is not where the next 200 Elo are: the oracle experiment put the gap at sixty-fold in the truth's weight, and both refits together close a few percent of it. v37 stays live as long as the arena agrees (it carries fresher data at no cost); the work moves to the items chapter 6 ranks first, an opponent model conditioned on what the opponent sees and a per-move correction inside the search.

## Files

- `~/fable-persist/suite/fit-all.log`, `fit-all-full.json`, `fit-all-cheap.json`, `refit-all.log`, `refit-eval-v35full.json`, `refit-eval-v35cheap.json`
- `~/fable-persist/suite/refit-{table35,theta,both}-cf.json` (suite arms), baseline `worlds-32-cf.json`
- `~/fable-persist/suite/history-all-20261101.bin`
- candidate ZIP `fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip` (sha256 41e02e280b61; mist-c branch allfit f76a09e from 97b60f1; Stockfish and run.sh as v35); queue `data/arena_local/queue-v37.json`, smoke `smoke-v37.json`; receipts under `data/arena_local/receipts/`
- fitter: mist-c `tools/fit_move_model_stream.py` (a1bd043)

Note on the data drive: it dropped twice during the cheap fit (07:37Z and 08:05Z, I/O error). The cheap fit was redone from the local copy of the text export with the feature extractor streamed into the fitter per pass (`cmd:` sources, mist-c d262253), on the identical train/test split (recovered by matching the test set's position count); the v35 full weights score 0.6375 / 26.73% on it, exactly as on the file.
