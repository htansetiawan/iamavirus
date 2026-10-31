# Worlds sweep, 31 October 2026

Question (the user, 31 October): "why 32 worlds, why not 36, why not 50, did we even test?" The record had no measurement: v33 (mist-c v9, 12 October) cut the draw from 128–256 worlds to 32 on a depth argument, and the number was never swept afterwards. This is the first sweep.

## Setup

- Engine: the exact v35 bytes. Worktree of mist-c at 97b60f1, source diffed identical to `fable-submissions/iamavirus-v35-mist-c-v14.zip`, built with the same flags. History table and Stockfish binary taken from the v35 ZIP.
- Suite: the frozen regression suite (1,379 decisions), kinds `check` and `fatal` only: 487 decisions (343 check, 144 fatal), of which 399 have a safe move available.
- Budget: 2.5 s per decision, two Stockfish workers, seed 1, cores 2–5 at nice 5, arms run one after another 21:38–23:05Z (about 22 minutes each).
- Only `MIST_SAMPLES` varied: 16, 32 (the v35 default), 64, 128. The draw is with replacement in proportion to belief weight, so the distinct-board count is lower than the draw.
- Comparison: `compare.py` paired with the 32 arm on the same decision ids. A fatal decision is one where the played move leaves our king capturable on the true board while a safe move existed. The noise floor from earlier same-setting reruns is about five flips each way; a setting has to net ten or more to earn the 100-game confirmation against v35.

## Result

| Draw | Distinct boards (median) | Fatal of 399 | Centipawn loss, mean | vs 32: fixed | broke | Net |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 14 | 108 | 82.9 | 4 | 5 | −1 |
| 32 | 26 | 107 | 88.6 | — | — | — |
| 64 | 44 | 110 | 93.7 | 4 | 7 | −3 |
| 128 | 78 | 104 | 87.8 | 8 | 5 | +3 |

By kind, fatal decisions where a safe move existed:

| Draw | check (of 300) | fatal (of 99) |
|---:|---:|---:|
| 16 | 62 | 46 |
| 32 | 61 | 46 |
| 64 | 60 | 50 |
| 128 | 58 | 46 |

Every pairwise net is inside the noise floor. Nothing earns a confirmation bench. The centipawn differences (−5.7, +5.1, −0.8 per decision) are also within what two reruns of the same setting show.

## What the search did with the budget

Medians per decision from the engine's own stderr line:

| Draw | Nodes | Iterations | Information sets | Stockfish calls |
|---:|---:|---:|---:|---:|
| 16 | 83,948 | 2,250 | 1,533 | 3,702 |
| 32 | 82,094 | 2,190 | 1,473 | 3,816 |
| 64 | 83,170 | 2,210 | 1,417 | 4,064 |
| 128 | 83,821 | 2,100 | 1,360 | 4,144 |

The node count is the same in every arm. At a fixed clock the budget is set by Stockfish throughput, not by the world count. With 128 draws the same 83,000 nodes are spread over 78 boards instead of 26, so each board gets about a third of the tree it gets at 32, and the decisions are no worse. With 16 draws each of 14 boards gets almost twice the tree, and the decisions are no better.

## Reading

1. The world count is not a lever at this budget, in either direction. The v33 argument for cutting to 32 (more worlds spread the search too thin) does not show at 2.5 s: 128 is not worse than 32.
2. This is consistent with the oracle result (81–0 given the true board) and the sharpness curve: what moves the score is the weight the belief puts on the true board, not how many boards are drawn. Drawing more boards from the same weights adds boards the search already judges well or badly in the same proportion.
3. 32 stays in v35 and in any v36. Chapter 6 item 4 of the document, which proposed re-testing a larger draw, is updated to record this.

## Caveats

- One seed. The noise floor quoted is from earlier reruns of the same setting; a second seed of one arm would measure it directly on this sweep.
- 2.5 s per decision on the suite against 4 to 8.5 s a move in the arena. More time means more nodes, and whether the extra nodes are better spent on more boards or deeper trees at 8 s is untested. The arena budget cannot be reproduced on the suite in a reasonable wall time (the 2.5 s sweep took 87 minutes).
- Check and fatal kinds only; the 892 material decisions were not run.
- The log carries 10 to 12 `Unexpected engine output: ''` warnings per arm. They come from the scorer's python-chess Stockfish, are spread evenly over the arms, and 480 or 481 of the 487 decisions were scored in every arm, so they do not affect the comparison.

## Files

- Outputs: `{storage}` is not involved; the result files are in the Fable scratch area `~/fable-persist/suite/worlds-{16,32,64,128}-cf.json` with the run log `worlds-sweep.log`.
- Engine worktree: `~/fable-persist/mist-v35` (97b60f1).
- Command (one arm): `tools/suite_run.py suite.json OUT --mist mist-v35/build/mist --env MIST_HISTORY_TABLE=<v35 zip>/data/history.bin MIST_SAMPLES=N --seconds 2.5 --workers 2 --kinds check,fatal --seed 1 --stockfish <v35 zip>/bin/stockfish`
