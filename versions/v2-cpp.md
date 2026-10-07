# v2 — C++ engine (`450f11a`)

## Implemented

A full rewrite. Magic bitboards for O(1) slider attacks, generated at startup and
checked exhaustively against a ray-walking reference. Incremental Zobrist
hashing, a fixed open-addressed transposition table with 16-byte entries,
alpha-beta with the referee's terminal rule, a particle filter over the
opponent's position, and regret matching over a root matrix game.

Three design points worth restating:

**The terminal rule replaces check and checkmate.** At every node, if the side to
move can capture the enemy king, the game is already decided. A move exposing our
own king is then simply a losing move the search finds by itself.

**Wins and losses are priced asymmetrically.** Our king's position is known
exactly while theirs is inferred, so a line losing our king is real where a line
taking theirs is a guess. Pricing the win lower declines speculative king hunts.

**The root is a game, not an optimisation.** Rows are our moves, columns are
hypotheses, and regret matching solves it, so a move that is excellent against the
likely board but fatal against a plausible one does not survive.

## Performance

| | v1 | v2 |
|---|---|---|
| nodes/sec | 44 k | **11 M** |
| depth at 1 s | 5 | 9 |
| depth at 4 s | 6 | **12** |

The speedup came from removing work, not micro-optimisation: an incremental
material/placement accumulator, one fused activity pass replacing eighteen
`AttackersTo` calls, and pawn pressure as two bitboard shifts. `Evaluate` went
59 ns → 35 ns. `-O3` measured *slower* than `-O2`.

## Results

10W–0L against `baseline.py` at 180+2 in both colours. Arena Elo settled near
1468 — below both TA baselines, so the baseline sweep proved only that
`baseline.py` (Elo 1000) is weak.

## Known defects at this commit

Found later by review and verified locally: quiescence allows a stand-pat while
the side to move's king is attacked (a 28,000 cp error at the horizon),
transposition entries are reused across different fog contexts, and en-passant
inference is broken in the engine integration (30 legal moves where the referee
has 31). None are fixed as of v5.
