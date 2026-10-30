# The v35-base lanes: the curve on the right base, and the first engine ahead of v35

30 October 2026, 00:04Z to 03:39Z, cores 2 to 5, 60 games, 0 failed, no forfeit. Every lane is
20 games (10 colour-swapped pairs) at 180+2 against the frozen v35 zip, with the oracle referee
writing the truth beside each replay so the engine can log the true world's share of its
belief. All three lanes set `MIST_PIECE_GUARD=-1`, so the base engine plays as v35 (the lanes
of note 182 had the v20 piece guard on by default; see that result's addendum).

| Lane | Engine | W-D-L | Score | White | Black | Pair bootstrap 95% | Exact lower 95% (wins) | Clocks (oracle side min / median) |
|---|---|---|---|---|---|---|---|---|
| natural-v35base | v22-share zip (v35's model), share 0 = observe only | 9-1-10 | 0.475 | 4.0/10 | 5.5/10 | 0.28 to 0.68 | 0.26 | 21.6 / 41.4 s |
| share20-v35base | same zip, truth forced to 0.2 | 14-1-5 | 0.725 | 7.0/10 | 7.5/10 | 0.48 to 0.93 | 0.49 | 19.9 / 41.6 s |
| natural-v23 | `mist-c-v23-obs.zip` (bitboards + fitted PST+observation model), observe only | 14-0-6 | 0.700 | 9.0/10 | 5.0/10 | 0.50 to 0.90 | 0.49 | 24.0 / 51.6 s |

Reasons: king capture in 58 games, threefold repetition in 2. Dose check for the forced lane:
truth in the belief on all 740 logged decisions, never lost, never appended; the 58 off-target
forced lines are all decisions where the belief held exactly one world (share 1.0 by
construction); no oracle line on v35's side and no piece-guard line in any lane. Stderr
excerpts are complete for 16 or 17 games per lane and cut at 16384 characters for the rest.

## The curve on the v35 base

The same-bytes control now scores 0.475 (note 182's natural lane, with the piece guard on,
scored 0.325), so the earlier number was the piece guard, as the addendum said. The 0.2 dose
scores 0.725 here against 0.800 with the guard on; the two are 14-1-5 and 16-0-4, a difference
of a point and a half, inside 20-game noise. Reading: a belief that holds the truth at a fifth
of its weight scores about 0.75 against v35 (bootstraps 0.48 to 0.93 and 0.65 to 0.95). The
80% bar is not confirmed at 0.2 on either base; the 0.5 dose (20-0-0 on the guard-on base)
remains the comfortable figure, and 0.2 the floor to aim for.

## natural-v23: the first engine ahead of v35 in a screen

14-0-6, score 0.70, with the smoke's two games 16-0-6. White 9/10, Black 5/10. The pair
bootstrap's lower end is 0.50 and the exact one-sided bound on wins is 0.49, so twenty games
show it is at least level with v35 and probably ahead; they cannot put it at 0.70 with any
precision, and they say nothing about the 80% bar. Its clocks run higher (median 51.6 s left
against the control's 41.4 s) because the bitboard update is cheaper.

Truth's share of the belief on its own decisions, against the control under identical
conditions (same opponent, same harness, same night):

| Statistic | natural-v35base (v35's model) | natural-v23 (fitted model) | note 182's natural lane (guard on) |
|---|---|---|---|
| decisions logged | 727 | 673 | 558 |
| truth lost (not in the belief) | 10 | 0 | 6 |
| median share | 0.0101 | 0.0781 | 0.0030 |
| mean share | 0.133 | 0.256 | 0.107 |
| below 0.001 | 29.4% | 11.7% | 40.7% |
| below 0.01 | 49.8% | 25.7% | 60.9% |
| at or above 0.2 | 15.5% | 34.8% | 13.6% |
| at or above 0.5 | 10.7% | 22.0% | 9.0% |
| share relative to uniform over the live worlds, median | 1.6x | 3.9x | 1.7x |
| live worlds at the decision, median | 180 | 104 | 537 |

The fitted model gives the truth about eight times the weight the shipped model does in these
games, puts a third of the decisions at or above the 0.2 target, and never lost the truth at
the cap. One caveat governs how to read that: the opponent here is v35, and the fitted model
was trained on 8,000 recent arena games in which v35 is the single most frequent mover, while
the shipped model's training set predates v35. Part of the gain is the model knowing v35's own
habits. On arena traces against other bots the same header moved the truth's share by a
factor of 1.4 (0.0063 to 0.0086, `docs/belief-obs-20261029` in mist-c), not 8. The score
against v35 is real for what it measures; how much of it carries to the arena's opponents is
the open question, and a per-opponent breakdown of the model's held-out gain says the lift
there is smaller.

## What this does and does not say

- v23 is the first engine since 14 October that beats v35 in a direct screen without a guard
  change: 16-0-6 over 22 games counting the smoke. It is not an 80% result and twenty games
  cannot make it one.
- The curve's target share stands at 0.2 as the floor and 0.5 as the comfortable figure,
  now on the right base.
- The model's gain against v35 is inflated by v35 being in its training data; the trace
  yardstick against arena opponents is the one to improve, and the discriminator (183, with
  its correction) is the build aimed at it.
- Next: Astra's confirmation protocol on v23 (100 games, 50 pairs, held-out seeds) if the
  team wants a number for the arena decision; the discriminator v2b result; a v23 lane against
  the local Misty as a second opponent.

Files: `readout.py`, `readout.json`; queue `data/arena_local/queue-v35base.json`, receipt
`data/arena_local/receipts/queue-v35base.json`, smoke receipt `smoke-v23.json`; zip
`data/candidates/mist-c-v23-obs.zip` sha256 a63ac2f00d58 (mist-c b31c54e, v35's history
table, r4 Stockfish).
