# Versions over time

*Every arena version, what changed against its parent, and what happened. Quoted phrases are the registry's own wording from `MUTATIONS.md`; dates are UTC. Scores are wins-draws-losses from the arena record where the version played enough games to count.*

[TOC]

## 7 October: the C++ engine

| v | time | change | outcome |
| --- | --- | --- | --- |
| 1 | 03:53 | the pre-session C++ engine | no games |
| 2 | 04:15 | "C++ engine": bitboards, exact legal moves from the view, particle-filter belief, alpha-beta per particle, root matrix game by regret matching | 4-0-10 |
| 3 | 04:51 | "belief consistency": our own pieces become an exact constraint on every particle | 10-0-14 |
| 4 | 05:47 | "king safety (cpp)": king-loss risk charged over the whole particle population before the shortlist | 103-6-153 over 262 (0.41) |

What we learned: the rules implementation was right (47,875 of 47,875 checks against the referee) and the harness was usable, but losses were belief failures, not search failures: the king was taken by pieces the belief did not hold.

## 7 to 10 October: the neural hybrid

| v | time | change | outcome |
| --- | --- | --- | --- |
| 5 | 14:44 | "first neural hybrid": imitation network v1 (1.87M parameters, CNN with a GRU memory) proposes candidate rows for the matrix game | 26-2-8 over 36 (0.75) on an easy schedule |
| 6 | 14:46 | the C++-only control of v5 | 2-0-6 |
| 7 | 14:47 | "opponent prior + turn deadline (cpp)" | 2-0-10; one illegal-move forfeit from a castling-rights bug |
| 8 | 16:08 | "v6.1 repairs": the fatal-cell payoff fix | 9-0-15 |
| 9 | 17:08 | "fatal-cell risk charge, safety rows, harmless deadline" | 7-0-3 |
| 10 | 17:29 | "safety rows reserved in the union, node-capped deadline fallback" | 81-3-86 over 170; the fallback version that night |
| 11 | 20:35 | Astra's "exposure-only runtime" | 0-0-2 |
| 12 | 20:45 | "population-wide exposure, pawn visibility deductions, clock scaling, underpromotion rule" | 7-1-8 |
| 13 | 22:33 | "two-ply hidden-threat term, clock defaults, matrix cells on both cores" | 68-10-76 over 154 |
| 14 | 8 Oct 04:40 | "caution engine (two-ply king threat 0.6, repetition charge, 10 s reserve) + frequency-sampled opening book" | 26-1-29; the book carried a 6-ply queen trap |
| 15 | 8 Oct 07:10 | "booked moves gated by the king-safety filter" | 241-15-318 over 574 (0.43); a 24-hour observation freeze |
| 16 | 8 Oct 11:20 | an unknown upload | 8-1-15 |
| 17 | 9 Oct 04:38 | "seen-gift charge x3, king sighting 300, 8,192 particles, 16 hypotheses x 16 rows" | 19-2-21 (0.48; predicted 0.41 to 0.53) |
| 18 | 9 Oct 05:51 | "deep RL network (regularised PPO, 40 iterations) proposes rows" | 32-4-48 over 84 (0.41) |
| 19 | 9 Oct 09:29 | the RL network after 120 iterations | 4-0-0, replaced after four games |
| 20 | 9 Oct 09:37 | "RL policy as the matrix-game prior, 100 cp per nat" | 61-10-69 over 140; rating 1586 to 1622 |
| 21 | 9 Oct 14:38 | the same bytes uploaded again | 85-21-116 over 222 |
| 22 | 9 Oct 22:40 | the RL network after 240 iterations | 16-5-3 on an easy schedule; lost 3-7-6 to v20 locally |
| 23 | 9 Oct 23:20 | "king-only belief fusion": the network's belief head reweights the enemy-king squares of the particles | 11-2-14 |
| 24 | 10 Oct 00:20 | "Knight Vision replay book": Knight Vision's bot is a pure strategy, so its games are replayed against it | 9-2-33: 8 of 8 against Knight Vision, 0 of 17 as Black against everyone else |
| 25 | 10 Oct 01:54 | "safe Knight Vision replay": the book forces only 1.d4 and 1...d5 | 243-52-261 over 556 (0.48), the best hybrid |
| 27 | 10 Oct 22:02 | "hard-turn cap: at most 8 s (was 12)" | 2-0-6; the cap was not the cause |

What we learned: the network mattered only through the decision rule. On its own the RL policy played even with v17; as a prior inside the matrix game it scored 11-4-1 locally. The hybrid's ceiling was the belief: against the top five it failed to escape a hidden check 32% of the time, and it did not convert leads.

## 10 to 11 October: the first mist-c trial and Misty

| v | time | change | outcome |
| --- | --- | --- | --- |
| 26 | 10 Oct 21:12 | **mist-c v5**: "our clean-room C Obscuro: exact belief weighted by an opponent move model, GT-CFR over 128 to 256 sampled worlds, legality guard, no third repetition when ahead, belief updates paid from the clock" | 4-1-15 over 20; every loss to an unseen piece |
| 28 | 11 Oct 00:11 | **Misty**: "Brian Liou's Misty behind our protocol adapter" | 11-0-6 over 17 (0.65) with two time forfeits |
| 29 | 11 Oct 00:51 | "arena time settings: a 3 s search cap, Misty's commit guards on 200 belief boards (was 1,000), the belief capped at 500,000, and crash recovery" | cancelled before play |
| 30 | 11 Oct 01:05 | "4 s search cap" | 209-29-226 over 464 (0.47); +0.12 a game over v25 on the same schedule; top six 0.22; one time forfeit |
| 31 | 11 Oct 01:10 | probably a re-upload of v30 | never active |

What we learned: the Obscuro method beat everything we had built, with the same evaluator (Stockfish at depth 1) and the same belief idea, because it solves for a strategy over information sets instead of best-responding to sampled boards. Misty's own weak points in the arena were the clock and repetition draws when far ahead.

## 11 to 13 October: mist-c

| v | time | change | outcome |
| --- | --- | --- | --- |
| 32 | 11 Oct 04:26 | **mist-c v7**: "Stockfish 19 scores the search's leaves (one depth-1 MultiPV call per expanded node)" | 9 of 23; top six 2 of 14; shelved |
| 33 | 11 Oct 22:37 | **mist-c v9**: "32 worlds with Stockfish (was 128 to 256) + king guard (root moves more than 2 points above the least king risk on all of P are left out)" | 323.5 of 663 (0.49); +0.04 a game over v25 (z 2.3); top six 0.26; no forfeit |
| 34 | 13 Oct 00:20 | **mist-c v12**: v10 (Stockfish on worker processes scored in waves, an empirical opponent prior keyed by the opponent's information history, belief updates on two threads) + v11 (the move model's log-likelihood sharpened by 2, time divisor 20) + "the king guard's rule under both the sharpened and the fitted weighting" | 220 of 440 (0.50); +0.09 over v25 (z 4.0), +0.05 over v30 (z 2.6), +0.025 over v33 (z 1.3); top six 0.24; Instructors 0.39; Greek Gift 0 of 32; no forfeit |

Withdrawn between v33 and v34: **mist-c v11** alone (the sharpened belief without the two-weighting guard) lost two 7-to-9-ply games to our own v10 in the bench, both to the queen check on a5 after 1.d4, because the sharpened weights dropped a 3% check world under the guard's 2% margin.

What we learned so far: the gain of v34 over v33 sits on Mist Opportunities (0.45 against 0.29) and Instructors (0.39 against 0.30) while the top six as a group is unchanged; the remaining losses are belief failures of a specific kind, where the opponent's non-captures argue the belief out of a hidden attacker.

## 14 October to 8 November: guards, a refit and a faster scorer

| v | time | change | outcome |
| --- | --- | --- | --- |
| 35 | 14 Oct 06:41 | **mist-c v14: the queen guard**. Queen danger is folded into the king guard's rule as one risk, king + 0.9 × queen, under the same 2-point margin. Why: our queen was lost outright in 43% of v34's games against the top six, against 10% for them | About 7,800 games at 0.52 over three weeks, the long-running baseline. No time forfeit in 7,198 games. 400-game reading: 209-16-175 (0.54), top six 0.27 |
| 36 | 27 Oct 23:23 | **mist-c v20 r4: the piece guard**. A move's share of worlds in which it loses 3+ pawns net on the next ply is folded into the guard; an enemy capture that leaves its own king capturable counts as a won game | Withdrawn by the user 28 Oct ~02:05 after 48 games: 15-1-32 (0.32) against v35's expected 0.51, z −2.88. Its 104-game local bench later passed. **Local tests did not predict the arena** |
| 37 | 1 Nov 14:29 | **v35's engine with the opponent model refitted on 148,357 games** (was 2,029) and the history table rebuilt to 359,889 records | 2,322 games, 1219-65-1038, 0.539. Held-out prediction gain +0.0077 nats (top-1 26.7% → 27.1%) |
| 38 | 8 Nov 16:53 | **Astra's all-child scorer**: a modified Stockfish 19 scores all of a position's moves in one pass; same engine, model and table as v37 | 1.57–1.68× scoring speed, 38% more search nodes at equal time. Passed its 300-game keep rule (318 games, 0.582). 2,588 games to 21 Nov: 1387-93-1108 (0.554); no time loss, crash or illegal move |

What we learned: guard rules bought at most about 30 Elo each, and the piece guard cost more than it saved. The oracle experiments of 28 to 30 October showed why. Told the true board, the bot won 81 of 81 games. Normally the true board holds a median of about 1% of the weight, so the gap is how boards are weighted, not the search. The v37 refit added 73 times more data to the same 28 features and barely moved prediction.

v38's extra search paid off where rank is decided. Head-to-head, v37 then v38:

- Mist Opportunities: 0.48 then 0.71;
- Instructors: 0.40 then 0.52;
- Knight Vision: 0.30 then 0.41;
- Crimson Fog: 0.18 then 0.38.

From 8 to 14 November, v38 spent 82% of the time above the Instructors' bot and Mist Opportunities; v37 managed 14% and 5%.

## 8 to 20 November: research, then a freeze

No new arena version. The research of this stretch is catalogued in [Everything built and tested](status-20261120.html). In short:

- A compact opponent model passed every prediction test, then lost 1–8 to v38 at full clock.
- The paper's opponent-knowledge search (M4), placed behind v38's guards, went 8–10 against v38.
- A recapture defect in the queen guard was found and an isolated fix verified, but not shipped.

On 14 November the human lead stopped development: v38 stays in the arena until submission. A reading of v38's arena record is taken every three days for the final report.

## Reading the registry

`MUTATIONS.md` at the repository root is the registry of record: every arena version, its parent, the exact change, the zip hash, the prediction written before the first game, and the fate. `fable-submissions/README.md` holds the submission log with each checkpoint. The mermaid lineage in the registry shows which versions descend from which.
