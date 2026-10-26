# Out-of-sample replay, first rule (B1), and the three fatal moves

818 first clean rook/minor losses from 20 to 26 October (after the calibration
window), paired, 2.5 s, seed 1, v35 zip's Stockfish and history table.
A = baseline (v35 defaults), B1 = piece term at lambda 0.758, T 3, combined
risk king + 0.9 queen + 0.758 piece measured against all moves.

| | A | B1 |
|---|---|---|
| repeats the recorded losing move | 0.620 | 0.466 |
| cp loss on the true board, mean / median | 164 / 56 | 130 / 45 |
| B1 better by 100+ / worse by 100+ (of 728 scored) | | 107 / 71 |
| fatal (king capturable, a safe move existed) | 0 / 818 | 3 / 818 |
| piece term vetoed the recorded move | | 0.233 |

Per opponent, mean cp loss A -> B1: Strongly Invisible 139 -> 112 (150),
Knight Vision 209 -> 167 (127), duck 166 -> 129 (122), Decent 224 -> 175 (121),
Instructors 143 -> 102 (107), Greek Gift 104 -> 91 (101).

## The three fatal moves

- **05i9doxr:22** (vs duck, lead -3, lost position). The king guard alone left one
  move, g7h8. Under the combined rule the move with the least combined risk was
  c5d7, which carries a 5.7% king risk (the true board, rank 2 in P) but a
  smaller piece risk; g7h8 fell outside the margin and c5d7 was played. The
  piece term re-admitted a move the king rule had excluded. A lost king is the
  game, a lost piece is not: a design fault, not noise.
- **rjaerwc3:25** (vs Instructors, lead +6). The recorded move g8h8 was vetoed
  by the piece term (correctly: it loses a piece). Among the remaining moves the
  search chose d5d6, fatal on a world of share 0.9%. That world is inside the
  king guard's 2% margin by design, in v35 as well.
- **zmikg9zc:17** (vs duck, lead -2). The true board had share 0.007% (rank
  465). No guard can act on it; the baseline's safe move was luck.

## Amendment (mist-c, 26 Oct, after 539d4e3)

v35's rule runs first on king + 0.9 queen; the piece term then only narrows
among its survivors, under the same margin and both weightings. A move v35
excludes stays excluded. With the piece term off the behaviour is v35's
exactly. Replayed on the three cases: 05i9doxr:22 plays g7h8 (the king move),
zmikg9zc:17 plays the baseline's move, rjaerwc3:25 plays a different survivor.
All four sets are being replayed with the amended rule (B2) before the bench.
