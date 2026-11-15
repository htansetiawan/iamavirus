# Opponent-knowledge search (Astra's M4) on the v38 base: 18 local games

Curiosity build (Henry, 14 Nov: "implement 2 nothing to lose ... just for
curiousity"). v38 stays the arena bot. Item 2 of
`astra-submissions/obscuro-comparison-20261108.md`: the paper's 2-KLUSS
subgame with Resolve/Maxmargin gadgets and a tree carried between moves.

## Build

- mist-c branch `fable/kluss` = `allfit` (v37 source) + merge of `astra/m4`
  + `MIST_SEARCH=m4` in the v37 front end (commit 55ab8e7). The king, queen,
  material and repetition guards still apply: barred moves are removed from
  the M4 strategy and the rest renormalised. GT-CFR remains the fallback when
  M4 fails or under 20 s on the clock. `make test_m4`: 17 suites pass.
- Package `kluss-a.zip` (sha256 8e019e1e26c8...): the v38 ZIP with these
  sources and `MIST_SEARCH=m4` in `run.sh`. Same Stockfish binary as v38.

## Result: level with v38, not better

180+2 games on the course referee, colour-swapped, one game per core pair
(cores 4-7), against the v38 ZIP.

| Set | Games | New search score |
|---|---|---|
| Smoke | 2 | 1-0-1 |
| Match (seed 440000) | 16 | 7-0-9 (White 3/8, Black 4/8) |
| All | 18 | 8-0-10, 0.444 (z -0.47 against 0.5) |

No crash, time forfeit or illegal move. Every game ended by king capture.
Lowest clock left at the end of a game: 20.7 s.

Search diagnostics (from the 16 KiB stderr tail of each replay, so the
later moves of each game; 484 decisions):

- M4 returned a move every time; never over its budget.
- Started from scratch (no carried tree) on 15 decisions, zero own reach on 2;
  the rest carried the tree forward (median 279 carried nodes, max 39,099).
- A guard restricted the M4 move 88 times.
- It used 75% of its time budget (median), max 78%: the prototype's
  solve deadline. One Stockfish process against v38's two.

## Reading

Eighteen games cannot separate the two: 0.444 is half a standard deviation
below even. The search works end to end, but this local test does not show
it beating v38. Known gaps that cost it strength: a quarter of the budget
unused, half the Stockfish throughput, kappa = 1, no repetition modelling
inside the search. Local games against v38 do not predict results against
the top teams (v36, October), so an arena trial would be the only real test;
not proposed, as Henry is not pursuing further changes.
