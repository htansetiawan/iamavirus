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
   (sha `916c34a70b26`; mist-c d8fcac8 = v9 + history prior + threaded belief +
   one-move shortcut) vs Misty (20, seed 110000), vs the v33 bytes (20),
   and the same with `MIST_ASYNC=1` vs Misty (20, same seeds). Validation of
   the exact zip (clean build, g++ fallbacks, kit baseline both colours) is
   running on cores 6-7.
