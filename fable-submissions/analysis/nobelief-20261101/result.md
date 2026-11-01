# Does the belief carry information? Yes: the ranking does, the number of boards does not

1 November 2026 (run 05:05Z to 06:06Z). The user asked, after the worlds sweep and the draw-temperature test both came out null, whether the belief representation carries any information at all: "use 0 boards and test if it even changes anything".

## Setup

Exact v35 bytes (worktree 97b60f1, v35's history table and Stockfish), the frozen suite's check and fatal kinds (487 decisions, 399 with a safe move), 2.5 s a decision, two workers, seed 1, cores 2 to 5. Baseline: the 32-world arm of the worlds sweep (same bytes and settings). Three crippled forms:

- **S1**: one board drawn instead of 32 (`MIST_SAMPLES=1`; zero is not possible, the search needs a board). Formula and table on.
- **M0**: formula and history table off (`MIST_MODEL=0`): every board consistent with the view has the same weight, for the draw and for the guards. 32 boards.
- **M0S1**: both.

## Result, paired with v35

| Form | Fatal of 399 | Fixed / broke | Net | Centipawn loss, mean diff | Same move as v35 |
|---|---:|---:|---:|---:|---:|
| v35 | 107 | | | | |
| S1, one board | 111 | 3 / 7 | −4 | −0.7 | 79% |
| M0, no ranking | 136 | 20 / 49 | −29 | +20.2 | 64% |
| M0S1, both | 137 | 24 / 54 | −30 | +18.8 | 59% |

By kind: check 61 / 61 / 89 / 92; fatal 46 / 50 / 47 / 45.

## Reading

1. The learned ranking carries real information: without it the bot makes 27% more fatal mistakes and loses 20 centipawns more per move, almost all of it on the check kind (hidden checks), where the ranking says which boards hold the attacker.
2. The number of boards adds little: one board is inside the noise of 32 on these decisions (−4 net), as the worlds sweep found upward (16 to 128 all null).
3. So the representation is not void. Its weakness is where the ranking is wrong, on the opponent's surprising moves (the 166 unseen-capturer losses, truth share 0.0019), not in the representation itself. This is consistent with the oracle (perfect ranking wins 81 to 0) and with the forced-share lanes.
4. The 12 October arm on an older engine said the same (uniform belief: 142 fatal against 109).

## Caveats

One seed; 2.5 s a decision; the no-ranking form also strips the guards of their weighting, so M0 measures the whole system without the learned weights, not the draw alone.

## Files

`~/fable-persist/suite/nobelief-{S1,M0,M0S1}-cf.json`, `nobelief-sweep.log`; baseline `worlds-32-cf.json`.
