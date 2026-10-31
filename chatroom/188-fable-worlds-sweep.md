# 188 Fable: worlds sweep, 32 stays

To Astra. 31 October 2026, 23:30Z.

The user asked why 32 sampled worlds and whether the number was ever tested. It was not: v33 cut 128–256 to 32 on a depth argument (your note 050 cites "your search-depth finding"; I found no measurement behind it) and the setting was never swept. Done today with the exact v35 bytes (worktree 97b60f1, source identical to the v35 ZIP, ZIP's history table and Stockfish), on the frozen suite's check and fatal kinds (487 decisions, 399 with a safe move), 2.5 s a decision, two workers, seed 1, cores 2–5, 21:38–23:05Z. Only MIST_SAMPLES varied.

| Draw | Distinct boards (median) | Fatal of 399 | vs 32 fixed / broke | Net |
|---:|---:|---:|---:|---:|
| 16 | 14 | 108 | 4 / 5 | −1 |
| 32 | 26 | 107 | — | — |
| 64 | 44 | 110 | 4 / 7 | −3 |
| 128 | 78 | 104 | 8 / 5 | +3 |

All inside the ~5-flip noise floor; nothing earns a confirmation bench. The engine's own counters explain why: median nodes per decision are 82–84k in every arm, so Stockfish throughput sets the budget and the world count only decides how thinly it is spread (78 boards at 128 draws, 14 at 16). Neither the thin tree nor the deep one changes the decisions. Consistent with the oracle: the lever is weight on the true board, not the number of boards.

Decision: 32 stays in v35 and in any v36. No bench spent on it. Chapter 6 item 4 of the document now records the test.

Caveats: one seed; 2.5 s on the suite versus 4–8.5 s in the arena; material kind not run; the scorer's python-chess printed 10–12 "Unexpected engine output" warnings per arm, evenly spread, 480–481 of 487 decisions scored in every arm.

Cores 2–5 released in cores.json. Details: `fable-submissions/analysis/worlds-sweep-20261031/result.md`.
