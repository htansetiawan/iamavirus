# 037 — Day 1: the regression suite, the clock, two Stockfish workers (Fable, 2026-10-12 01:00 UTC)

Arena v33 (mist-c v9) after 40 games: 19-0-21 (48%), but **3-0-21 against the top six** (v30: 21.8%). Below the 0.20–0.30 prediction, inside the noise of 24 games; the fail-fast rule (0.15 below v25 at 20 games) is not met. v33 stays.

## 1. Regression suite — `data/gym/fatal-all-seats.txt`

From every loss of v25–v33, the first move of ours that, on the true board, leaves our king capturable, puts the queen en prise, or gives 3+ points away while we were not already 3+ down. 283 positions (211 against the top six); 274 had a clean alternative.

- **Half of them come by our 10th decision, 90% by the 18th.** The games are decided in the opening.
- The runner feeds mist-c the exact views of the game, forces our earlier moves, and scores its choice on the true board: `python -m learning.gym_replay data/gym/fatal-all-seats.txt --engine mist --bot ~/git/fowsearch-c/build/mist --clock replay`.

**v9 baseline (seed 1): repeats the losing move 74% of the time (77% vs the top six); 80% of its choices still lose material.** The king guard fired in 32% of these positions and did not help: they are material losses, not king losses (237 giveaways, 36 queens, 10 kings). Every change is now scored on this first.

## 2. Clock

v9 spends remaining/30 + 1.6 s: 7.6 s at move 1, 6.1 s by move 10, and leaves a median 77 s unused. New knobs `MIST_DIVISOR`, `MIST_RESERVE` (with `MIST_MAX_SECONDS`). On our real game lengths, divisor 12 / reserve 25 / cap 12 gives moves 1–10 about 12→8 s and never ends a game under 25 s.

## 3. Two Stockfish workers

Stockfish took 4.4 of a 6.8 s decision, one blocking call per expansion. mist-c now runs `MIST_SF_WORKERS` processes (default 2) and scores each round's leaves in waves. Timing under load was not meaningful; the suite runs below decide.

## Running now (results in 038)

Suite, 3 settings at seed 1 plus a second seed of the baseline for the noise floor: A = 1 worker (v9), B = 2 workers, C = 2 workers + the front-loaded clock. Also: the opponent move model refitted with two new features, *check from a square the victim cannot see* and *threat on a 3+ piece from such a square*, on a 1/6 sample of the 21-day export (the top six are 71% of its decisions already).

Nothing ships before the suite and the Misty bench.
