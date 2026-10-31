# Guard candidates: what the v35 losses say (31 October 2026)

Question (the user's): what other guards could we add to lose less? Three scans over
v35's 7,907 arena games (4,052 wins, 209 draws, 3,646 losses; every loss ends by our move
leaving the king capturable), from the replay store, final frames and views.

## Draws one repeat away

| | count | share of losses |
|---|---|---|
| losses where some position had already occurred twice | 401 | 11.0% |
| of those, while we were 2 or more points down | 199 | 5.5% |

v35's 209 draws: 199 by threefold repetition, 10 by the 50-move rule. The engine has no
notion of a draw's value: the tree scores positions by Stockfish, and the repetition rule
only refuses a third arrangement when we lead by 2 or more. A rule "when 2 or more down,
play the move that recreates a twice-seen position" can only trigger in positions we are
losing, so its downside is nil; its upside is bounded by 199 half-points over 7,907 games,
about +0.6% score if every one converted, which they will not (the opponent must repeat too).

## The back rank

| | count | share of losses |
|---|---|---|
| king on its home rank at the end | 1,286 | 35.3% |
| taken along that rank by a rook or queen | 814 | 22.3% |
| of those, no other piece of ours on the rank | 752 | 20.6% |
| of the 814, material still level (3 or better, i.e. >= -2) | 119 | 3.3% |
| of the 814, the attacker's square visible to us before our last move | 23 | |
| of the 814, our last move took a piece off the home rank | 36 | |

Median material at the end of a back-rank loss: -11. So the back-rank capture is the
formality that ends a game already lost: the rook arrives on a rank we cannot see, 791 times
in 814 from a square we could not see. The taxonomy's "back rank bare, last of 15" is mostly
a symptom of being ground down, not a cause. A back-rank guard (keep a piece on the rank,
make an escape square) can address at most the 119 level cases, and in those the blind
spot is still the unseen rook, i.e. the belief.

## Attackers at the end (final board, pieces attacking our king)

rook 1,670, queen 1,476, bishop 220, knight 178, king 80, pawn 76 (a king may have several).

Scripts: inline Python over `data/raw/games/<id>/replay.json` (frame boards are after the
frame's move; the final frame is our fatal move). Related: the hazard calibration of 30
October (losses and trades inseparable on the static risk estimate) and the oracle
(81-0 with the true board), both pointing the lever at the belief, not at another guard.
