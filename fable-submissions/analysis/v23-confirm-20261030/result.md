# v23 confirmation against v35: level, not ahead

30 October 2026, 04:39Z to 10:47Z, cores 2 to 5. Astra's protocol (177): 100 unforced games,
50 colour-swapped pairs, 180+2, each game on its own core pair, frozen bytes, a held-out seed
(410000), no oracle referee. `data/candidates/mist-c-v23-obs.zip` (sha256 a63ac2f00d58:
mist-c b31c54e, the bitboard belief update and the fitted piece-square + observation move
model, v35's history table, r4 Stockfish, `MIST_PIECE_GUARD=-1`) against
`fable-submissions/iamavirus-v35-mist-c-v14.zip`. 100 of 100 played, 0 failed, no forfeit.

| | Games | W-D-L | Score | White | Black | Pairs (sweeps v23 / v35 / split) | Pair bootstrap 95% | Exact lower 95% on wins |
|---|---|---|---|---|---|---|---|---|
| v23 vs v35 | 100 | 52-1-47 | 0.525 | 28.5/50 (28-1-21) | 24.0/50 (24-0-26) | 50 (15 / 13 / 21) | 0.43 to 0.63 | 0.43 |

A 0.5 engine scores 52.5 or more in 100 games about three times in ten. Reasons: king capture
99, threefold repetition 1. End clocks (s), min / median: v23 20.4 / 40.8, v35 20.0 / 40.0.
Shortest losses 40, 48, 49 and 50 plies; median win 82 plies, median loss 83.

## What it shows

v23 is level with v35 in direct play. The 20-game screen of note 184 (14-0-6, with the smoke
16-0-6) was the high end of noise: the first ten pairs of this run scored 13/20 and the next
forty pairs 39.5/80. Against the user's bar of 80% in direct games, v23 is at 52%, and the
pair bootstrap's upper end is 0.63. Nothing in the protocol's reading makes it a candidate.

What did not fail: no forfeit or crash in 100 games, clocks never under 20 s, no loss under
40 plies. The bitboard update and the fitted model are safe to carry forward as the base; they
are not a gain against v35 that a hundred games can see.

## What it does not show

The model's training set has v35 as its most frequent mover, so if self-knowledge were worth
anything in play it would have shown here, and it did not; the screen's eight-fold rise in the
truth's share (184) did not translate into games. Nothing here measures the arena's opponents.
The sharpness curve still stands: a belief with the truth at a fifth of its weight scores
about 0.75 against v35, and no model built so far moves the natural share by more than a
factor of about 1.4 against arena opponents (183 and its corrections).

## Options

1. Arena trial of v23 under the 20-game fail-fast rule. The downside is small (level with v35
   head to head, no forfeits, faster belief), the upside is unmeasured and the bench gives no
   reason to expect one; it would spend arena games to learn the model's effect on other
   opponents, which the local store cannot tell us.
2. Keep v35 live and move the work off belief sharpening: the search's behaviour under a
   wrong belief (more sampled worlds now that they are cheap, measured against Misty, not
   against ourselves) and the opponent-specific angles the compact game store supports.

Files: queue `data/arena_local/queue-v23-confirm.json`, receipt
`data/arena_local/receipts/queue-v23-confirm.json`, rows in `data/arena_local/games.jsonl`
(matchup `v23-vs-v35-confirm`), replays under `data/arena_local/builds/`.
