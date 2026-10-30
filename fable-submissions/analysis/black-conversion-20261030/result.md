# Black conversion lane: the lead at ply 30 was an artifact; Black converts a stable lead like White

30 October 2026. Astra asked for a falsifiable lane on Black's conversion: freeze a matched set
of v35 Black leads (>= 3 at ply 30) against the same opponent versions, locate the first
lasting reversal in each loss, and classify the decision that allowed it as truth absent /
truth present with tiny weight / sampled-world miss / search-or-value failure. Scripts:
`matched_set.py` (set and reversals), `replay_classify.py` (decision replays through mist-c with
the truth's share, rank and whether the true board was among the search's sampled worlds, a
new diagnostic line on mist-c branch `truth-sampled-log`, commit d21bd11 in the worktree
`fowsearch-c-diag`), `see_check.py` (static exchange evaluation on the true board, recomputing
attackers after each capture). Data: the compact store and the raw replays.

## 1. The lead at frame 30 is not a lead

The first set (net material >= +3 at frame 30, piece values 1/3/3/5/9) held 224 games: 105
losses, 106 wins, 13 draws, a 50% conversion. Their "reversal" came at ply 31 in a quarter of
the losses, and in the matched wins the median dip was at ply 31 too. Replaying the 105
decisions showed why: at frame 30 Black has just moved, and the lead often consists of a
capture White recaptures at ply 31. Our move "loses material" by exchange evaluation in only
28 of the 105; in 54 the engine repeats the recorded move and that move keeps the material by
SEE, because it was the first half of an exchange.

Requiring the lead to hold through frames 30, 31 and 32 (after White's reply and our next
move) removes the artifact:

| our colour, v35 vs the top nine (1,200-game samples) | lead >= +3 at frame 30 | its conversion | stable lead (frames 30-32) | its conversion | lost from a stable lead |
|---|---|---|---|---|---|
| White | 82 games | 0.817 | 76 games | 0.829 | 12 (1.0% of games) |
| Black | 118 games | 0.475 | 41 games | **0.780** | 7 (0.6% of games) |

The earlier reading (Addendum 2 of `black-losses-20261030/result.md`: Black converts 0.45,
White 0.81) compared White's lead measured after the opponent's reply with Black's measured
mid-exchange. On an equal definition Black converts a lead as well as White. What remains
true is that Black reaches a stable three-point lead half as often as White (41 against 76),
which is the early-material story, not a conversion one. Astra's "Black has better material
at ply 30 but a lower score" is the same artifact: Black's frame-30 material is inflated by
captures in progress.

## 2. The stable set and its reversals

Stable set: 79 games (14 losses, 60 wins, 5 draws), matched wins 14 (same opponent versions,
seed 1). Losses: 13 have a lasting material reversal (first ply p >= 33 with net <= lead - 2 for
every later ply), one was lost by king capture while still ahead.

| statistic | 13 reversals in losses | 13 dips in matched wins |
|---|---|---|
| ply, quartiles | 45 / 79 / 93 (at 59-80% of the game) | 39 / 47 / 57 |
| recovered | never (by definition) | 13 of 13 |
| piece lost | R 4, Q 4, N 2, B 1, P 1, none 1 | |
| capturer | P 4, K 3, R 2, Q 2, N 1, B 1 | |
| we had just moved the piece there | 9 of 13 | |
| capturer's square visible at our decision | 1 of 13 | |
| a winning recapture existed and was not taken | 0 | |

These are late, often endgame events (median ply 79 of 100): a rook or queen moved next to
an unseen pawn or king. Not a kingside king hunt: the king is first attacked from the fog at a
median ply of 81 in these games, after the material went.

## 3. Classes of the decision that allowed the reversal (14 losses, 2 seeds, 4 s)

| class | count | note |
|---|---|---|
| a: truth absent from the belief | 0 | |
| b: truth present, share < 1%, not among the sampled worlds | 7 | shares 0.00004 to 0.005, ranks 56 to 37,235; the engine repeats the recorded move on every seed |
| c: truth share >= 1% but not sampled | 0 | |
| d: truth sampled, engine's move still loses material on the true board | 1 | l99cng3h ply 50, truth share 0.19 sampled, engine plays d8e7/d8d7, a rook is lost to a pawn either way |
| d-guard: truth sampled, the king guard left <= 2 moves, the move loses | 2 | cxew39q1 (final move, king taken), hgu0iloy ply 56 (truth share 0.17, guard left 1 move) |
| e: truth sampled, engine's move keeps the material by SEE | 4 | the loss came two or more plies deeper than a one-ply exchange (e.g. 13i6l0iu: queen to f3 with the truth at share 0.014, rank 2 of 2, then Kxf3 at ply 99) |

On the earlier, artifact-laden set of 105 the same classifier gave b 32, d 7, d-guard 3, e 54,
a 4, c 4 (`reversals.json`, field `cls_see`), with the same shape: belief weight (b) and
"keeps by SEE" (e) dominate, search-with-the-truth-sampled failures are rare.

## 4. Reading

- The Black-conversion lane is falsified as a separate mechanism. Black converts a stable
  lead at 0.78 against White's 0.83 (41 and 76 games; the difference is inside noise). The
  colour gap is in reaching the lead, which is the early-material bleed already identified.
- Among the few real losses from a stable lead, the decision class is belief weight (7 of 14:
  truth present at a tiny share, not sampled) or a loss deeper than one ply (4), not a search
  failure with the truth in hand (1 plus 2 guard-forced). This points to belief calibration
  and sampling coverage, the same levers as the early-bleed lane, not to a fog-aware frontier
  or value fix, and not to another king-move guard.
- The engine replays faithfully: on 166 of 210 seed runs it repeats the recorded move, so the
  recorded blunders are the engine's choices, not seed noise (class e by SEE is not "the engine
  would have avoided it": it means the loss was not a one-ply exchange).
- Method caution for everyone: a material lead must be read after the exchange in progress is
  complete. Any ply-parity snapshot biases Black against White.

Files: `matched-set.json` (frame-30 set, 224 games, with reversal fields), `matched-set-stable.json`
(stable set, 79 games), `stable-classified.json` (the 14 losses with replay results),
`reversals.json` (105 replays, two seeds each, all fields), `replay.log`. Run time of the 105
replays: 2.6 h on one core (late-game belief replays at the cap).
