# Guard-margin grid on the regression suite

29 October 2026, 22:00 to 23:45Z, cores 2 to 4. Question (the user's): were other values of the
king margin (0.02) and the queen margin (0.05) ever tried? Not as a grid, so here is one. Engine
mist-c b31c54e-era build/mist (2803b68 source at run time) with `MIST_PIECE_GUARD=-1`, so it
plays as v35; v35's history table; Stockfish r4 build; 2.5 s per decision, seed 1; the suite's
632 check-and-fatal decisions (`~/fable-persist/suite/suite.json`, kinds check and fatal; 487
scored), 2 workers. Paired against a fresh baseline under the same load (`compare.py`). The
noise floor between identical runs is about five flips each way.

| setting | fatal (all, of 399 with a safe move) | fixed / broke | check kind | fatal kind | cp loss mean (all) |
|---|---|---|---|---|---|
| base: king 0.02, queen 0.05 | 109 | | 61/300 | 48/99 | 91.4 |
| king 0.01 | 104 | 8 / 3 | 58 (3/0) | 46 (5/3) | 85.4 |
| king 0.05 | 115 | 10 / 16 | 68 (4/11) | 47 (6/5) | 88.5 |
| queen 0.03 | 105 | 4 / 0 | 60 (1/0) | 45 (3/0) | 85.9 |
| queen 0.10 | 106 | 6 / 3 | 61 (1/1) | 45 (5/2) | 86.9 |

Reading. Every setting is inside the noise floor on the fatal count. The one clear direction is
that a looser king margin (0.05) breaks more than it fixes (16 broke, 11 of them hidden checks),
so 0.02 is not too tight. Tightening the king margin to 0.01 and the queen margin to 0.03 each
net four or five decisions, which is the size of the noise, and the earlier record says gains
of this kind on the suite did not survive whole games (the uniform clause of v16, Astra's
0.0001 king margin). Queen 0.10 is as good as 0.05. Verdict: the margins are not a lever; no
bench is warranted on these numbers. Files: the five result JSONs here; the engine knobs are
`MIST_KING_GUARD`, `MIST_QUEEN_GUARD`.
