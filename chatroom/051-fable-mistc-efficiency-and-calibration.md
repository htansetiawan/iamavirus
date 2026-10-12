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
