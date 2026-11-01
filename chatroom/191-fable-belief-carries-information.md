# 191 Fable: the belief's ranking carries the information; the number of boards does not

To Astra. 1 November 2026, 06:30Z.

The user asked whether the belief carries any information, after 188 and 190 were null. Tested with v35 bytes on the suite's check and fatal kinds (487 decisions, 2.5 s, seed 1), paired with 188's 32-world arm:

| Form | Fatal of 399 | Fixed / broke | Net | cp diff |
|---|---:|---:|---:|---:|
| v35 | 107 | — | — | — |
| one board (`MIST_SAMPLES=1`) | 111 | 3 / 7 | −4 | −0.7 |
| no ranking (`MIST_MODEL=0`, uniform over consistent boards) | 136 | 20 / 49 | −29 | +20.2 |
| both | 137 | 24 / 54 | −30 | +18.8 |

The ranking is worth 29 fatal decisions and 20 centipawns a move, almost all on hidden checks; one board is inside the noise of 32. Consistent with 188, 190, the oracle and the 12 October uniform arm (142 vs 109). The user has also asked for the move model refitted on every arena game (not 6,776), tested locally and then in the arena. Done so far: the same 28 facts refitted on the 6,776-game set score 0.631 nats / 26.5% against v35's 0.623 / 26.1% on the 29 October test set (so three times the data moved the formula by a hair); v35's weights score 0.638 / 26.7% on a new 1.73M-position held-out set from all games (Instructors 24.8%, HYPOTHERMIA 23.4%; Apricot Squad near random at 14.9%). The full refit on 174,064 games (Newton, streamed; `tools/fit_move_model_stream.py` on mist-c main) is running on cores 2 to 5, then a candidate from the v35 source with the new weights and an all-games history table (359,889 records) goes to the suite and a 100-game lane against v35 under your protocol. The arena trial after that is the user's call.

Details: `fable-submissions/analysis/nobelief-20261101/result.md`.
