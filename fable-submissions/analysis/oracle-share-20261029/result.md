# Sharpness curve: result

29 October 2026. Diagnostic from note 181 (not a candidate). Question: how much of the
belief's sampling weight does the true world need for the v35 search to reach the 80% bar
against v35? The oracle side is mist-c e748d5c with `MIST_ORACLE_SHARE` (zip
`data/candidates/mist-c-v22-share.zip`, sha256 07fbadfa08cf): on each of its own decisions the
sampled belief is kept and the true world's weight is set to exactly the lane's share
(appended if the belief had lost it); share 0 only logs the truth's natural share. The
opponent is the frozen v35 zip. 180+2 clocks, cores 2 to 5, seeds 402000 to 405000, 20
games (10 colour-swapped pairs) per lane. Queue `data/arena_local/queue-oracle-share.json`,
receipt `data/arena_local/receipts/queue-oracle-share.json`: 80 of 80 games, 0 failed,
15:46Z to 20:54Z. The 1.0 point is the oracle result of note 179 on the same harness.

## Score by lane

| Truth share | Games | W-D-L | Score | White | Black | Pair bootstrap 95% | Exact lower 95% | Reasons |
|---|---|---|---|---|---|---|---|---|
| natural (0.003 median) | 20 | 6-1-13 | 0.325 | 5.0/10 | 1.5/10 | 0.13 to 0.55 | | king capture 19, repetition 1 |
| 0.05 | 20 | 11-1-8 | 0.575 | 5.5/10 | 6.0/10 | 0.40 to 0.75 | 0.39 | king capture 19, repetition 1 |
| 0.20 | 20 | 16-0-4 | 0.800 | 9.0/10 | 7.0/10 | 0.65 to 0.95 | 0.60 | king capture 20 |
| 0.50 | 20 | 20-0-0 | 1.000 | 10/10 | 10/10 | 1.00 to 1.00 | 0.86 | king capture 20 |
| 1.0 (oracle, note 179) | 40 | 40-0-0 | 1.000 | 20/20 | 20/20 | 1.00 to 1.00 | 0.93 | king capture 40 |

Exact lower 95% is the one-sided binomial bound on wins over games (draws counted as
losses). Pair bootstraps are over the 10 complete pairs of each lane, 2000 resamples.

Clocks and forfeits. No forfeit in any lane. End clocks (s) on the oracle side, min /
median: natural 20.9 / 41.2, 0.05 19.9 / 30.6, 0.20 20.6 / 35.5, 0.50 20.9 / 41.0; v35's
21.2 / 42.4, 20.0 / 31.8, 26.3 / 37.9, 21.7 / 39.7. Nobody came near zero. Win lengths in
the 0.5 lane 43 to 139 plies (median 80); in the 0.2 lane 52 to 112 (median 85), losses 53
to 120.

## Did the dose apply

From each replay's private diagnostics (`readout.py`, `readout.json`):

- Forced lanes: the truth was in the belief on every logged decision (603, 537 and 540
  lines), never lost, never appended, zero "belief kept" failures, zero oracle lines on
  v35's side.
- Every logged forced share equals the lane's share except at decisions where the belief
  already held exactly one world (20, 35 and 50 decisions): there the function leaves the
  weight alone and logs 1.0, which is what the share is. All 105 off-target lines have
  |P| = 1; none has |P| > 1.
- The stderr excerpt in a replay is capped at 16384 characters, so 17 or 18 games per lane
  are checked on their first part only (about 27 decisions each); 8 to 10 games per lane are
  covered end to end. The smoke games (note 181) were complete and clean.
- The forcing persists: the function shifts the log-weights in place, the next belief
  update propagates them, so the "natural" share logged in a forced lane is the truth's
  share after the previous dose, not the untouched belief's. Medians 0.035 / 0.172 / 0.416
  in the 0.05 / 0.2 / 0.5 lanes against 0.003 untouched. The dose itself is still exact at
  every decision, so each lane remains a clean point on the curve; only the natural lane
  measures the belief as it is.

## The natural belief

The natural lane (share 0, observe only) logged 558 decisions (570 seen in the excerpts):

| Statistic | Value |
|---|---|
| truth in the belief | 552 of 558 decisions; lost at 6 (one game, pair 4 as White, after P hit the 200,000 cap; the game was still won) |
| truth's share of the sampling weight, median | 0.0030 |
| mean | 0.107 |
| below 0.001 | 40.7% |
| below 0.01 | 60.9% |
| at least 0.2 | 13.6% |
| at least 0.5 | 9.0% |
| printed as 0.00000 (below 5e-6) | 14.7% of decisions with the truth in P and more than one world |
| share relative to uniform over the live worlds (|P| > 1) | median 1.7 times uniform; 47% of decisions below uniform, 24% below a tenth of it, 19% at ten times or more |
| live worlds at the logged decisions | median 537, mean 10,752 |

Coverage is not the problem (one loss of the truth in 20 games, at the cap). Weight is:
on six decisions in ten the truth carries under 1% of the belief, and on four in ten it
carries under 0.1%. The move model ranks the truth only 1.7 times above an uninformed
weighting at the median, and below uniform nearly half the time.

The natural lane is the same engine as v35 up to the logging, and scored 0.325 (6.5 of 20
points). A 0.5 engine produces 6.5 points or fewer in about one run in ten (binomial on 20
games: 6 or fewer 0.058, 7 or fewer 0.132), so this is within noise, with the Black side
(1.5 of 10) carrying the deficit as it does in the arena. It is not evidence that the
logging changes play, and the forced lanes carry their own dose, but the baseline is noisier
than 20 games can settle.

## Target share

Rule from note 181: the lowest lane whose score reaches 0.8 sets the target. That is the
0.2 lane, at exactly 0.800 (16-0-4). Honest uncertainty at 20 games: the pair bootstrap
spans 0.65 to 0.95 and the exact lower bound is 0.60; a 0.5 engine makes 16 of 20 wins with
probability 0.006, so the lane is clearly far above v35, but "at or above 0.8" is a point
estimate, not a confirmed bound. The 0.5 lane is the first whose lower bound (0.86) clears
the bar by itself. The curve is monotone and steep between 0.05 and 0.5:

| share | 0.003 (natural) | 0.05 | 0.2 | 0.5 | 1.0 |
|---|---|---|---|---|---|
| score | 0.33 | 0.58 | 0.80 | 1.00 | 1.00 |

Reading: a belief that holds the truth at about a fifth of its weight on each decision
reaches the bar; at half the weight the search wins everything; a twentieth of the weight
(already 17 times the natural median) is worth about 50 Elo over v35. The target for the
belief build is a truth share of 0.2 per decision as the floor, 0.5 as the comfortable
figure.

## What it means for the belief build

- The gap is a factor of about 60 at the median share (0.003 to 0.2), and the mass below
  0.01 (61% of decisions) has to move to above 0.2. The piece-square refit of the move
  model (memory: ×1.9 on the truth's share over the v35 traces, 0.623 nats over uniform on
  the held-out set) is a step in the right direction and an order of magnitude short of it on
  its own. It stays worth doing as the pipeline check, not as the candidate.
- The share is a product of the move model's odds over the opponent's unobserved moves
  since the worlds diverged, so per-move sharpness compounds. The model that gets there must
  be far sharper per move than a pooled 26% top-1 imitation model. Two directions have that
  leverage and have not been tried: an opponent-specific model (the arena opponents are fixed
  programs with 176,785 games on record under their names; their moves given their observation
  are close to deterministic, so a per-opponent fit should rank the true move far higher than
  the pooled model does, and the bot knows who it is playing), and conditioning the model on
  what the opponent can see in the world (the opponent moves on its own observation, which the
  world determines, and the current features do not encode it).
- The natural lane is now the cheap yardstick for any belief build: run the new belief with
  `MIST_ORACLE_SHARE=0` on this harness, read the truth-share distribution, and compare with
  the table above. No bench is needed until the median is near 0.2 and the mass below 0.01
  has mostly gone; a candidate whose distribution matches the 0.2 lane's dose is expected
  to score about 0.8 against v35, and one matching the 0.5 lane's about 1.0.
- Confirmation of a candidate stays Astra's frozen protocol (100 games, 50 pairs). If a
  build lands near the 0.2 point, the 20-game lane is not precise enough to call 0.8 and the
  full protocol decides.

## Files

`readout.py`, `readout.json` (per lane: score, colour, pairs, clocks, reasons, plies,
`oracle_applied`, `natural_share`), queue and receipt as above, games in
`data/arena_local/games.jsonl` (matchups `natural-vs-v35`, `share05-vs-v35`,
`share20-vs-v35`, `share50-vs-v35`), replays under `data/arena_local/builds/`. mist-c
e748d5c (`MIST_ORACLE_SHARE`, `belief_force_board_share`, `tests/test_oracle.c`).

## Addendum (29 October, 22:00Z): the base engine had the piece guard on

Checked after the read-out: the zip `mist-c-v22-share.zip` is built from the current mist-c
source, whose default for `MIST_PIECE_GUARD` is the v20 value 0.758, and no lane turned it
off. The piece guard printed on 414 of the natural lane's 570 logged decisions and 460 of
547 in the 0.2 lane. So every lane's engine is v35 plus the piece guard plus the dose, that
is the withdrawn v36 (v20 B2) configuration, not v35's bytes.

Consequences:

- The natural lane is a direct 20-game screen of the v20 piece guard against v35, with the
  same bytes otherwise: 6-1-13, score 0.325 (White 5/10, Black 1.5/10). It matches v36's
  arena score of 0.330 over 50 games and adds to the case that the piece guard loses games.
- The dose curve is measured from that base. If the piece guard costs points on its own,
  the same doses on v35's bytes would score higher at every share, and the target share of
  0.2 is conservative rather than optimistic. The oracle result (179) is not affected: 1.00
  at share 1.0 under either base.
- Fix: rerun the 0.2 lane (and the natural lane) with `MIST_PIECE_GUARD=-1`, 20 games each,
  before the target share is used as a gate. Queued behind the guard-margin grid on the
  suite; about two hours on two slots.
