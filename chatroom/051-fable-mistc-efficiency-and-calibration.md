# 051 — mist-c: where the time goes, what sped up, and what the suite says (Fable, 2026-10-12)

Direction from the user (05:00 UTC): focus on the mist-c approach; improve its
computational efficiency, tune hyperparameters, add detection heuristics;
micro-benchmark first, then optimise. This note is the measured record.

## Cost profile of a v9 move (local machine; the arena is ~1.9x slower)

| cost | measured | note |
|---|---|---|
| Stockfish `go depth 1` MultiPV 256 | 0.3 ms (<=20 legal moves) to 1.8 ms (35+) | the pipe is 0.01 ms; the cost is Stockfish scoring every line (~0.05 ms per move) |
| our search thread | 0.1 s CPU of a 2.5 s search | the round loop idles on Stockfish waves, Stockfish idles during the solver's iterations |
| belief update at the 200k cap | 2.3 s per opponent update, single thread | move generation 33%, visibility 23%, then the candidate sort and the capped sample's sort (serial) |
| compiler flags (-O3, LTO, -march=x86-64-v2/v3) | 0 | measured on a 35-update replay: all within noise |

Arena v33 (148 games): median think 6.5 s at decision 1 falling to 3.1 s by
decision 40; median 74 s left on our clock at the end of a 72-ply game.

## What changed in mist-c (commits 519556c..d8fcac8, pushed)

1. **Belief updates on 2 threads** (`MIST_THREADS`, default 2): pass 1 and
   pass 2 of the opponent update and the own-move update split the work;
   each thread sorts its run, the runs merge; the capped sample is a linear
   selection instead of a sort. Belief identical to the single-threaded one
   (same truth share/rank over 71 views). Opponent update at the cap:
   2.29 s -> 1.24 s. Less thinning of P for the same clock.
2. **Pipelined search** (`MIST_ASYNC=1`, off by default): every Stockfish
   worker keeps a leaf in flight, the solver iterates while they think
   (`MIST_ITERS` per expansion), whichever answers first is expanded.
   +15-25% expansions on two cores.
3. **MultiPV cap** (`MIST_SF_MULTIPV`, default 256): Stockfish scores its
   best k lines; a child left out takes the worst scored value as a floor.
   On two cores, opening decision: 1,364 calls (round loop) -> 1,683
   (pipeline) -> 2,911 (MultiPV 16) -> 3,620 (MultiPV 8) in 2.1 s.
4. One allowed move is played without a search. `MIST_TIMING=1` logs the
   update costs. The suite runner tracks the true board (`--truth`).

## What the regression suite says (487 check+fatal decisions, 2.5 s, paired)

| variant | fatal rate (safe move existed) | cp loss mean | fatal fixed / broke vs round loop |
|---|---|---|---|
| round loop (E) | 0.301 | 94 | — |
| pipeline, ITERS 0.3 | 0.323 | 91 | 5 / 14 |
| pipeline + MultiPV 16 | 0.308 | 92 | 8 / 11 |
| pipeline + MultiPV 8 | 0.328 | 96 | 2 / 13 |
| pipeline, ITERS 1, MultiPV 16 | 0.313 | 91 | 3 / 8 |

More search per second did not reduce blunders at this budget; MultiPV 8
hurts. Both stay opt-in. Whether *time* matters at all (1 s vs 2.5 s vs
6 s on the same decisions) is running now; so is a belief calibration
sweep (model temperature 0.5/0.7/1.0/1.5, history n0 1/4/16, model off).

## The residual hidden-check blunders are a belief problem

The 75 check-kind decisions that v9+prior still gets fatally wrong, re-run
with truth tracking: the true board was in P in 68 of 71, at a median
weight share of 0.06% (rank ~440 of thousands), and the move chosen was
the belief's least-risk move (median risk 0.060 vs least 0.059). The king
guard does what it is meant to; the belief is confidently wrong about
where the attacker stands. Across all 343 check decisions the truth's
median rank is 23 (p25 2, top-10 40%), so the blunders are the tail
where the move model is most wrong. Lever: calibration of the weights
(temperature, history prior strength), measured by truth rank on the
suite, then the fatal rate.

## v33 checkpoint at 199 games

0.49 (97.5/199); v25 would have scored 0.45 on the same opponents
(+0.042 a game, ±0.066, z 1.25). TA baselines 0.91 (v25 0.63), rest 0.92,
**top six 0.26 (v25 expected 0.28)**, Mist 0.28 (v25 0.22). No forfeits.
The gain so far is against the baselines, not the teams above us.

## Queued (cores 0-5, in order)

1. Calibration sweep (7 variants, ~08:15 UTC).
2. Time experiment: 1 s and 6 s vs the 2.5 s baseline (~09:15 UTC).
3. v34 candidate bench: `data/candidates/iamavirus-v34-candidate-mist-c-v10.zip`
   (sha `6c4c0235e4b6` (repackaged with the build.sh fallback fix); mist-c d8fcac8 = v9 + history prior + threaded belief +
   one-move shortcut) vs Misty (20, seed 110000), vs the v33 bytes (20),
   and the same with `MIST_ASYNC=1` vs Misty (20, same seeds). Validation of
   the exact zip (clean build, g++ fallbacks, kit baseline both colours) is
   running on cores 6-7.

## Validation of the candidate zip (06:40-06:47 UTC, cores 6-7)

sha `6c4c0235e4b6`: clean unzip, `build.sh` builds with gcc; the bot answers
`ready`, Stockfish starts, the history table loads (2.4 MB, `data/history.bin`);
both fallbacks (g++ C front end per file, g++ as C++) build and answer; kit
baseline beaten as White (76 plies) and as Black (75 plies), 63 s and 75 s
left on our clock. g++ 12 applies `-x c` to the first source only, so the old
C-mode fallback had never built (fixed in mist-c b6d53e0).

## Calibration sweep, first result

Model temperature 0.5 (flatter weights): truth rank median 54 (1.0: 23),
top-10 37% (40%), fatal 0.316 (0.303), cp loss 101 (89). Flatter is worse
on every measure.

## Calibration sweep, full result (06:08-08:10 UTC, 487 check+fatal decisions, 2.5 s, paired)

`MIST_MODEL_TEMP` multiplies the move model's log-likelihood: above 1 the
belief weights are sharper. Paired against temperature 1.0 (the shipped
default); "fixed / broke" counts fatal decisions that a safe move existed for.

| variant | fatal, all (fixed / broke) | fatal, check kind (fixed / broke) | cp loss | truth rank median, check | truth top-10, check |
|---|---|---|---|---|---|
| temp 1.0 (default) | 121/399 | 73/300 | 89 | 23 | 40% |
| temp 0.5 | 126 (24 / 29) | 83 (10 / 20) | 101 | 54 | 37% |
| temp 0.7 | 119 (20 / 18) | 76 (9 / 12) | 98 | 40 | 39% |
| **temp 1.5** | **112 (20 / 11)** | **63 (14 / 4)** | 90 | **20** | **43%** |
| history n0 1 | 122 (6 / 7) | 74 (4 / 5) | 92 | 23 | 41% |
| history n0 16 | 126 (6 / 11) | 79 (3 / 9) | 96 | 25 | 40% |
| model off | 142 (23 / 44) | 92 (9 / 28) | 107 | 161 | 34% |
| **temp 2.0** (cores 6-7, one worker) | **109 (30 / 18)** | **63 (16 / 6)** | **84** | 24 | 43% |
| temp 3.0 (cores 6-7, one worker) | 105 (37 / 21) | 59 (21 / 7) | 85 | 23 | 42% |

The trend is monotone in temperature: sharper is better on the check kind
(fixed 14, broke 4; fatal 73 -> 63), neutral on the fatal kind (6 / 7) and
on cp loss. The history prior strength (n0 1..16) is a null; the model off
is clearly worse (its removal ranks the truth at 161). Temperature 2.0 (09:06 UTC): the same 63 check-kind blunders as 1.5 but the
best centipawn loss of the sweep (84; check kind 69 against 78), and 109
fatal overall. Temperature 3.0 (09:59 UTC): 59 check-kind blunders and 105 overall, but
against 2.0 it is inside the noise (fixed 17 / broke 13; check 10 / 6), its
median centipawn loss creeps up (1 -> 2 -> 3 from 1.0 to 3.0) and it changes
more of the arena moves (repeat rate 0.50 -> 0.40). The curve is flat from
2.0 up; 2.0 is the safer pick unless the material kind says otherwise. The
material kind (892 decisions) runs now for 1.0 and 3.0 on cores 6-7 and for
2.0 on cores 0-5 after the bench.

## Search-time experiment (08:10-08:40 UTC, same 487 decisions, round loop, temperature 1.0)

| seconds per decision | fatal, all | fatal, check kind | fatal, material kind | cp loss mean |
|---|---|---|---|---|
| 1.0 | 124/399 | 73/300 | 51/99 | 96 |
| 2.5 (baseline E) | 120/399 | 71/300 | 49/99 | 94 |
| 6.0 | 117/399 | 73/300 | 44/99 | 87 |

Paired: 1 s -> 6 s fixed 12 / broke 5 overall, 4 / 4 on the check kind, 8 / 1
on the material kind. Two identical 2.5 s runs at different times differ by
4 / 5, so that is the noise floor. Search time buys a slow, steady gain on
material decisions and centipawn loss and nothing on hidden checks, which
matches the throughput results above: the check blunders are a belief
problem (temperature), the material ones respond to time. The arena leaves
74 s unused per game, so the time budget can go up for free; that is a
divisor change in the candidate, not a search change.

Bench of the v34 candidate started 08:40 UTC (three lanes, 20 games each).

## v34 candidate bench (08:41-10:45 UTC, 180+2, three lanes on cores 0-5, 20 games each)

Candidate = mist-c b6d53e0 (v9 + history prior + threaded belief + one-move
shortcut; pipeline off), sha `6c4c0235e4b6`.

| lane | W-D-L | as White | as Black | shortest loss | our clock min / median |
|---|---|---|---|---|---|
| candidate vs Misty v16 | 14-0-6 (0.70) | 8/10 | 6/10 | 52 plies | 37 / 74 s |
| candidate vs the v33 bytes | 12-0-8 (0.60) | 7/10 | 5/10 | 60 plies | 27 / 82 s |
| candidate with `MIST_ASYNC=1` vs Misty | 15-0-5 (0.75) | 8/10 | 7/10 | 49 plies | 52 / 81 s |

No forfeit or crash on our side (Misty forfeited on time once, as in the v9
bench). The history prior + threading is ahead of the v33 bytes (0.60, 20
games, inside the noise) and holds against Misty (v9 scored 0.80 on its own
20). The pipeline is not worse in games (0.75) but the suite put it slightly
behind on the check kind, so it stays off. This zip is not going up as is:
the temperature result above is a larger effect than anything benched
today, so the candidate becomes mist-c v11 = v10 + temperature 2.0 (pending
the material kind) + time divisor 20, benched the same way before upload.

## Material kind and the v11 candidate (13:54-14:30 UTC)

The material-kind runs queued at 10:00 never started (their wait loops
matched their own command line; three hours lost, lesson saved). Re-run
side by side, 892 material decisions at 2.5 s:

| temperature | fatal | cp loss mean | paired vs 1.0 |
|---|---|---|---|
| 1.0 | 1/891 | 145 | — |
| 2.0 | 4/891 | 137 | better on 356, worse on 341; fatal fixed 1 / broke 4 |

Temperature 2.0 is the pick: 73 -> 63 hidden-check losses and 7 cp better
on material, with three extra fatal moves in 891 as the only cost. 3.0 on
the material kind is running (~15:05 UTC) as a check, not a contender.

**mist-c v11 = 4a975db**: temperature 2.0 and time divisor 20 by default
(the defaults reproduce the env-driven belief exactly on replayed
decisions; the first decision now searches 8.6 s of a 10 s budget).
Candidate `data/candidates/iamavirus-v34-candidate-mist-c-v11.zip`, sha
`4a2b369b924c`, same Stockfish binary and history table as v10. Validation
of the exact zip runs on cores 6-7; the bench (vs Misty, vs the v33 bytes,
vs v10; 20 games each, both colours) is queued on cores 0-5 behind the
3.0 run and should end about 17:30 UTC.

Validation of the v11 zip (14:31-14:36 UTC, cores 6-7, sha `4a2b369b924c`):
clean unzip, `build.sh` builds with gcc, both fallbacks (g++ C front end per
file, g++ as C++) build and answer `ready`; Stockfish starts and the history
table loads; kit baseline beaten as White (20 plies, 122 s left) and as Black
(41 plies, 83 s left; the new divisor spends about 2 s more a decision).

Temperature 3.0 on the material kind (14:30-14:54 UTC): cp loss 138 (as 2.0)
but 8 fatal moves in 891 (1.0: 1, 2.0: 4; paired vs 2.0 fixed 1 / broke 5).
The sharper the belief, the more one-ply material blunders: 2.0 stands.
v11 bench started 14:54 UTC.

## v11 bench stopped at 15:50 UTC: the sharper belief switches the king guard off in the opening

After 10 / 9 / 8 games: 6-0-4 vs Misty, 3-0-6 vs the v33 bytes, **1-0-7 vs
v10**, with two losses as White in 7 and 9 plies, both the hidden queen
check on a5 after 1.d4 (`1.d4 c5 2.Nf3 Nf6 3.e4 Qa5+ 4.Bf4??` and
`1.d4 d5 2.Bf4 c6 3.a4 Qb6 4.e3 Qa5+ 5.Bd3??`), the family the history
prior had fixed. Replaying the decisions: at temperature 1.0 the king
guard leaves 8 (6) root moves, all answers to the check, on every seed; at
2.0 the check world's weight falls under the guard's 2% threshold, all 37
(39) moves stay in and the search plays a developing move on 1 of 4 (2 of
3) seeds. Mechanism: the temperature was applied to the whole history
mixture, so a check the table had seen at 3% went to 0.1%; and where the
table has no entry the squared model probability does the same.

Fix 1 (mist-c working tree): the temperature is applied to the model term
only, renormalised, inside the history mixture. It restores the guard in
the first game (8 moves) but not in the second (the table has no entry for
that parent; the guard fires only at 1.0). The next step is to keep two
weights per position: the fitted model's for the king guard's risk (the
calibration v10 had) and the tempered one for the search's sampled worlds
(where the suite gain came from). That is a belief.c change of the weight
arrays, then the suite again (check+fatal, material) before any bench.

In parallel, cores 0-3 bench the divisor-only variant (the v11 zip with
`MIST_MODEL_TEMP=1.0`, which is v10 + divisor 20) vs v10 and vs Misty, 20
games each, as the fallback candidate.

**Split weights (mist-c working tree, 15:50 UTC):** the stored weights are
the fitted probabilities again (v10's belief, the king guard and the truth
diagnostics read them); the search's sampled worlds and the thinning of P
draw by weight^temperature. Replaying both queen-check decisions at
temperature 2.0: the guard narrows the root to 8 and 6 moves and the block
is played on every seed. The suite re-measurement for the split at 2.0
(check+fatal, then material; cores 4-7) runs until about 18:10 UTC; it
goes into a candidate only if the gain holds.

## The temperature gain was the guard (16:47 UTC)

Split belief at 2.0 on check+fatal: 116/399, check 71/300, cp 90, i.e. the
1.0 numbers (fixed 14 / broke 9 vs 1.0; vs the whole-belief 2.0: fixed 20 /
broke 27). On the 16 check decisions that whole-belief 2.0 fixed, the root
after the guard had 17-41 moves at 1.0 and the split, and 1-2 moves at 2.0:
with weight^2 the risk is nearly binary, so the guard keeps only the moves
safe in the dominant world. That is the gain, and the a5 loss is the same
rule ignoring a 3% world. So the lever is the guard's weighting, not the
search's worlds.

**Combined guard (main.c, build/mist-v12):** king risk under both
weightings on the same strided pass of P; a move is out when it is more
than 2% above the safest under either; if that leaves nothing, the sharper
rule alone. Both queen-check replays: 8 and 6 root moves, the block on
every seed. Suite (check+fatal, then material) on cores 4-7 after the split
material run, ~18:40 UTC. Fallback bench (v10 + divisor 20) at 17:00: 3-0-5
vs v10, 5-0-2 vs Misty after 8 and 7 games.

## Fallback bench: v10 + divisor 20 (15:55-18:06 UTC, cores 0-3)

The v11 zip with `MIST_MODEL_TEMP=1.0`, i.e. v10's belief and guard with the
time divisor 20. Two games were killed by my process cleanup at 17:41 and
struck from the log (both lanes 19 games).

| lane | score | as White | as Black | shortest loss | our clock min / median |
|---|---|---|---|---|---|
| vs v10 | 9/19 (0.47) | 6/10 | 3/9 | 30 plies | 21 / 55 s |
| vs Misty v16 | 13/19 (0.68) | 7/10 | 6/9 | 60 plies | 23 / 47 s |

No forfeit on our side (Misty forfeited once, as before); the lowest clock,
21 s, came in a 177-ply game, where the 20 s floor keeps the clock. The
divisor alone is a null in games, as the suite predicted (a few material
decisions in 900): it is safe but not a reason to upload by itself.

## Final design under test: v11's belief + the guard under both weightings

The combined guard on the split belief measured at the 1.0 level (116/399,
check 69): the sharper guard needs the belief's own tempered weights,
merges included, not a power applied afterwards. So the belief is v11's as
measured (weights sharpened at 2.0) and the king guard applies its 2% rule
under those weights and under weight^(1/2), the fitted weighting; a move
is out when either flags it, the sharper rule alone when both would leave
nothing. Both queen-check replays: 8 and 6 root moves, the block on every
seed. Suite started 17:48 UTC on cores 4-7 (check+fatal ~18:15, material
~19:05); it ships only if the 2.0 gain survives the second rule.

## Final design on the suite (17:48-18:13 UTC): the gain holds, with the safety

| variant | fatal, all | check kind (fixed / broke vs 1.0) | cp loss |
|---|---|---|---|
| 1.0 (v10) | 121/399 | 73/300 | 89 |
| whole-belief 2.0 (v11) | 109 | 63 (16 / 6) | 84 |
| split (sampling sharpened only) | 116 | 71 (8 / 6) | 90 |
| combined guard on the split | 116 | 69 | 87 |
| **v11 belief + guard under both weightings (mist-c v12)** | **104** | **59 (16 / 2)** | 88 |

Against v11: fixed 12 / broke 7 on fatal (check 7 / 3), 4 cp worse (the
second rule leaves out some moves the search preferred). Committed as
mist-c v12 (`git log` on origin). The material kind runs until ~19:05; the
provisional bench (same source, sha `dffc8a21a45a`) vs v10 and Misty until
~20:50 UTC.

Material kind for v12 (18:13-18:48 UTC): cp loss 139 (1.0: 146, whole-belief
2.0: 137), fatal 4/891 (1.0: 1, 2.0: 4). Validation of the exact zip
(18:48-18:50, sha `dffc8a21a45a`): clean build, both fallbacks, Stockfish
and the history table load, kit games won as White (10 plies) and Black
(17 plies). Provisional bench at 7 games a lane: 3-4 vs v10 (no loss under
58 plies), 7-0 vs Misty. A second pair of lanes (vs the v33 bytes, vs v10
on new seeds) started 18:52 on cores 4-7. v33 at 500 arena games: 0.49,
+0.041 over v25's schedule (z 1.97), the first checkpoint past the 95%
margin.

Bench state at 19:53 UTC (v12 bytes): vs v10 8-0-8 of 16 (seed 130000) and
5-0-4 of 9 (seed 140000); vs Misty 12-1-3 of 16; vs the v33 bytes 4-0-5 of
9 (lost the first five, won the next four). All 20 losses so far began with
a material swing of 3+ to a capturer we could not see, at plies 9-44 (a
hanging piece under a hidden attacker, e.g. our b5 bishop to an unseen Qa5
in v12-vs-v33 pair 1 White); none was a hidden check, the shortest loss is
53 plies, the lowest clock 22 s in a 110-ply game, no forfeit. v33 at 522
arena games: 0.48, +0.034 over v25 (z 1.69), back under the margin after
three top-six losses in 22 games.

Bench 2 final (21:02 UTC, 20 games a lane): vs the v33 bytes 9-0-11 (White
5-5, Black 4-6), vs v10 on seeds 140000 10-0-10 (White 6-4, Black 4-6).
Combined v12 vs v10: 20-0-20 over 40 games (0.50; the divisor-20 null was
9/19). vs Misty 16-1-3 (0.83; the null 13/19). Lowest clock 21 s, no
forfeit, no bot exit. The third v33 seed set (150000, cores 0-3) stood
10-0-3 at 21:02 with one 23-ply loss (pair 4, White): after Bb5xc6 Bd7xc6
opened the long diagonal we played Nf3-e5 (the g2 defender) with the black
queen unseen on g6, and Qxg2 captured the king next move whatever we did
(Kxg2 Bxg2, Kf1 Qxf1, Kh1 Qxh1). Replayed at 6 s, three seeds: v12 plays
Ne5 once (Nd4 twice), the v33 binary plays Ne5 once (Nd4, cxd4 once each),
so the tactic is a shared weakness of the search, not a v12 regression.
Of note: the sharpened belief samples 3-6 distinct worlds a search at that
decision where v9 samples 25-28 (|P| = 147 in both); the concentration is
what buys the suite gain, and is the lever to revisit if the arena shows
more losses of this kind.

Bench 3 final (21:27 UTC): vs the v33 bytes on seeds 150000 14-1-5 (White
9-1, Black 5-1-4). All benches of the v12 bytes, 120 games at 180+2 on two
cores: 23-1-16 vs v33 (0.59), 20-0-20 vs v10 (0.50), 16-1-3 vs Misty
(0.83); no forfeit, no bot exit, lowest clock 21 s. The v34 row is in the
version map with the prediction and the fail-fast rule; the zip
`data/candidates/iamavirus-v34-candidate-mist-c-v12.zip` (`dffc8a21a45a`)
waits for the user's upload. v33 at 560 arena games: 0.49, +0.043 over v25
(z 2.17), no forfeits.

Arena, 22:13 UTC: v33 lost to Sausage in 12 plies as Black (1.e3 d5 2.Qf3
e5 3.b3 Nc6 4.Nc3 d4 5.Bc4 dxc3?? 6.Qxf7+ and the king is taken next move
whatever it does: Kxf7 Bxf7, Kd7 Qxd7). Queen and bishop were both out of
view. The suite does not hold this decision: dxc3 is neither fatal (no
immediate king capture), nor a material swing, nor a check, so the suite
only records the forced Kxf7 after it (safe = false). Built the dxc3
decision by hand and ran it at 6 s on three seeds: v12 plays dxc3 3/3, the
v33 binary plays dxc3 3/3 (cp loss 1000 = mate). A shared blind spot, not a
v12 regression: a two-ply hidden mate, where the knight is worth 3 in every
world and the mate lives in the few worlds with Qf3 and Bc4 together. The
same shape as the 23-ply bench loss (Ne5 into Qxg2). If this kind recurs,
the next suite kind to add is "allowed a forced king capture within two of
their moves on the true board", and the lever is either a two-ply king
guard (risk of a forced capture after their best reply, on P) or weighting
the mate worlds up, which is what the opponent history prior should learn
for queen-sortie bots like Sausage. Not for tonight.

## v34 in the arena, and a 19-ply loss to the unseen a5 queen (2026-10-13, 13:45 UTC)

v34 (mist-c v12) after 340 arena games: 181/340 (0.53), +0.120 a game over v25 schedule-adjusted (z 4.76), +0.081 over v30 (z 3.80); top six 47.5/182 (0.26), Instructors 19.5/42, Mist 18/36, Greek Gift 0/28 (the one bot it has not beaten); no forfeit or crash; eight draws by threefold repetition, all in games of 97+ plies (three vs Knight Vision).

The prediction "no loss under 20 plies to a hidden check" broke by one ply at game ~335 (cmyf2h7z, White vs Instructors): 1.d4 Nc6 2.c4 d5 3.cxd5 Qxd5 4.e3 Qa5+ (a5 never visible) 5.Nc3 e6 6.Nf3 Bb4 7.a3 Bxc3+ 8.bxc3 e5 9.Bb2 Nf6 10.c4?? Qxe1.

Replayed with the exact v34 bytes (2.5 s local ≈ the 4.8 s the arena spent, seeds 1-3, `--truth`):
- decision 5 (after the unseen check): truth share 0.14, rank 3 of 7; the king guard fires and Nc3 is played on every seed. Belief and guard did their job.
- decision 10 (the fatal c3c4): truth share 0.00016, rank 46 of 88; the guard is silent; locally d1c2 / d1c2 / f1e2 with root p 0.25-0.43, so c3c4 is a plausible draw of the same diffuse policy.

Cause: after bxc3 a queen on a5 has the free Qxc3+; Instructors declined it twice (e5, Nf6). Under the move model, and squared by the 2.0 temperature, those two moves are near-impossible for a queen on a5, so every a5 world fell far below the 2% guard margin although nothing had ever observed a5. This is the same family as the v11 withdrawal (the a5 check after 1.d4) in a new shape: there the belief missed the check; here it found the check, blocked it, and was then argued out of it by the opponent's "irrational" non-captures. Same mechanism as the residual hidden-check blunders in the suite (truth present at a tiny share; chosen move = least risk under the belief).

Mini-suite with the replay: ~/fable-persist/suite/a5-cmyf2h7z/ (README has the run line). Candidate levers, to discuss before building:
1. threat memory in the king guard: a square the guard has already acted on (a believed attacker at ≥ margin) keeps a floor weight until it is observed; cheap, targeted, risk = refusing to move a blocker for the rest of the game.
2. a third guard weighting, uniform over P, in the union of exclusions: asks "fatal in a non-trivial fraction of the consistent worlds?" regardless of the move model; risk = passivity in open positions, measurable on the suite's material kind.
3. an epsilon floor on the move model's per-move likelihood (opponents do decline free captures); likely too weak alone after two declines under temp 2.0.

## The queen guard: mist-c v13 (2026-10-13, 19:30-21:00 UTC)

Why: on a TA-baseline panel v34's behavioural rates match the top six (king threats, unseen threats, queen raids, visibility, lead conversion), but head-to-head our queen is lost outright in 43% of v34's top-six games (score 0.01 in those; v33 41%) against their 10%; trades they start 23% (0.22), trades we start 16% (0.34). In 99 of 100 outright losses the taker stood on a square unseen at decision time, usually the defender of what the queen took; the search's 3-6 sampled worlds held it too rarely. The king capture comes later (178 of 190 king losses had the queen already gone). Clock use is not a differentiator. The user: "queen in general is very vital and so we need to protect the queen with what it takes".

Built (fowsearch-c ae1e31b): `queen_risks` beside `king_risks` in main.c: on all of P (strided to 20,000, fitted weights and weight^temp), the share on which a move loses our queen on the next ply for 4+ pawns net (their best capture of a queen square, 9 less the capturer where we recapture, less what the move took; a world where the move takes the king is won). Exclusion = the king guard's rule with margin `MIST_QUEEN_GUARD` (default 0.05); the king guard has the last word; the existing one-ply material guard stays off.

Labels: a queen "loss" needs a 3-ply net (our move, their capture, our recapture); the 2-ply window counted 98 trades of 162 as losses.

Calibration (64 in-sample losses, truth in P for 55; `~/fable-persist/suite/queen_calib.py`): margin 0.05 vetoes the losing move in 39/55; control (735 material decisions without a queen loss): 1% of the played moves vetoed, 5% of the short search's own choices. 13 held-truth losses show ~0 risk: the truth sits in P at a tiny weight (the hidden-check calibration problem again).

Pitfall found on the way: P is thinned by measured wall-clock cost per position, so oversubscribed cores (2 workers x engine + 2 Stockfish on 2 cores) thin P far harder than the arena would; calibrate with one worker per core pair, compare runs under the same load.

Results, paired against the v12 baseline (h20-*.json), 2.5 s, seed 1:
- hidden-check kind: fatal 59 -> 59 of 300 (fixed 2, broke 2), cp loss 74 -> 69
- fatal kind: 45 -> 49 of 99 (fixed 1, broke 5; the noise floor is ~5 each way), cp loss 122 -> 111
- material kind: fatal 4 -> 5 of 891, cp loss 138 -> 132 (better on 358, worse on 351), the guard fired on 435 of 892
- the one-ply material guard at 2 pawns, for comparison: check 59 -> 64, fatal 45 -> 49, material cp 139 -> 125 but fatal 4 -> 9; stays off
- **out of sample, 114 v34 queen losses the engine had never seen (suite-v34-queen.json):** repeats the losing move 93 -> 16, cp loss on the true board 440 -> 197 (median 447 -> 97), queen-sized losses (400+ cp) 51 -> 21, worse by 300+ in 2, better by 300+ in 36; guard fired in 108

Candidate zip data/candidates/iamavirus-v35-candidate-mist-c-v13.zip (1a7444f488c1; v34's Stockfish and history table). Gates still to pass: validation of the exact zip; 40 games vs the v34 bytes at 180+2 (no forfeit, lowest clock above 20 s, shortest loss not shorter than v34's).
