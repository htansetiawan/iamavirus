# 019 — v18: deep RL, and where the network gets a say

*Fable, 2026-10-09. Provisional: games are still running; numbers below are from the local arena ledger (`data/arena_local/games.jsonl`, real bots, 180+2, two dedicated cores per game).*

## What was trained

The v4 imitation network, fine-tuned by regularised PPO in the batched C++ simulator: a pull toward the imitation policy (reverse KL, the "magnet" of MMD/R-NaD), a training-only critic that sees the true board, and a league of the imitation reference, six team replicas and our own snapshots. 120 iterations, about 2M learner decisions. Network alone, in the simulator: 0.93 against its starting point, 0.76 against iteration 40, 0.63 / 0.50 / 0.80 against the TA Baseline P / A / S replicas.

## Three ways to put it in the engine

v17's engine uses the network only to propose 8 of the matrix rows; the matrix game (our moves × 16 sampled boards, minimax) then decides. Note 017 already showed that proposals matter less than the decision rule.

| variant vs v17 | games | W-D-L | score |
| --- | --- | --- | --- |
| RL network proposes rows only (v17 behaviour, iteration 40) | 11 | 4-2-5 | 0.455 |
| same, iteration 120 | 18 | see ledger | ~0.53 |
| **RL network alone, no search** (`FOW_MODE=neural`) | 17 | 8-1-8 | 0.50 |
| RL alone + king-safety veto | 17 | 7-2-8 | 0.47 |
| **RL policy as a prior in the matrix game, 100 cp per nat** (`FOW_POLICY_PRIOR=100`) | 16 | **11-4-1** | **0.81** |
| v17 engine with 70% mean / 30% worst-case aggregation (StrangeFish2's rule) | 16 | 6-1-9 | 0.41 |

Readings so far:
- **The RL policy with no search at all plays even with v17**, which searches for most of its 180 seconds.
- **The prior is what lets RL matter.** Each matrix row is charged 100 centipawns per nat of log-probability below the policy's favourite, so the search still vetoes what it can see is bad while the RL policy, trained on outcomes, chooses among moves the search cannot separate under fog.
- Softening the minimax toward the belief mean, which the RBC winners use, made v17 worse here.

## Still running (to credit the gain correctly)

- The same prior with the **imitation** network (control): if it scores as well, the gain comes from the prior, not from RL.
- Prior weights 50 and 200 cp per nat.
- The prior variant against the validated TA Baseline P replica, on the seeds where v17 scored 0.484 and v15 0.688.

## Update 09:40 UTC

- **Arena v18** is the archive the user uploaded, `iamavirus-v18-hybrid.zip` (was `iamavirus-v18-candidate-rl120-hybrid.zip`): the RL network proposing rows only, 7–6–5 vs v17 locally. Prediction (GYM.md §7): 0.49 (0.42–0.56) over its first 50 arena games.
- **The best variant is packaged:** `fable-submissions/iamavirus-v19-candidate-rl120-prior100-hybrid.zip` (`fb7449edded5`), the same network with the prior on by default. Unpacked, built and smoke-tested in hybrid mode.
- Gates now also run these exact bytes against the v18 bytes and against the TA Baseline P replica.

## Update 10:20 UTC — v19 live; v20 candidate built

- **Arena v19** = `iamavirus-v19-hybrid.zip` (`fb7449edded5`), the RL policy as matrix prior. Prediction (GYM.md §7): 0.60 (0.48–0.72) over its first 50 arena games. Watch report: `data/reports/v19-watch.md`, every 30 minutes.
- **RL continued** from iteration 120 to 240 with the same recipe (35 minutes on the GPU). Pooled over each run's last 40 iterations, against the same fixed opponents:

| opponent | v19's network (it 81–120) | new network (it 201–240) |
| --- | --- | --- |
| imitation start | 0.857 | 0.900 |
| TA Baseline P replica | 0.586 | 0.657 |
| TA Baseline A replica | 0.588 | 0.630 |
| TA Baseline S replica | 0.755 | 0.833 |
| v19's network | — | 0.568 (518 games) |

- **v20 candidate** = `iamavirus-v20-candidate-rl240-prior100-hybrid.zip` (`522f1d99d0f5`): v19's engine and prior, only the network changed. Gate against the v19 bytes is running.
- Early and small: the imitation network with the same prior has won its first 3 games against v17, so the prior itself may carry much of the gain. That gate keeps running.

## Correction 11:50 UTC — the arena's numbering, and the first 50 games

The arena's own game listings number our uploads one higher than this note did:

| arena version | what it is | arena games | record | score |
| --- | --- | --- | --- | --- |
| v18 (from 05:51) | an upload Fable was not told about, most likely the rl40 candidate | 84 | 32–4–48 | 0.405 |
| v19 (09:29) | rl120 hybrid, the network only proposes rows | 4 | 4–0–0 | — |
| **v20 (from 09:37)** | **rl120 + RL policy as matrix prior** (`iamavirus-v20-hybrid.zip`) | 50 | 23–3–24 | 0.490 |

Files are renamed to match; the rl240 candidate is now the v21 candidate. Please confirm what was uploaded at about 05:50 UTC.

**v20 against its prediction (0.60, range 0.48–0.72):** inside the range, well below the point. By opponent class it did what the gym said: TA baselines **0.674** over 23 (v15: 0.447 over 264), top six 0.100 over 20 (v15: 0.035), everyone else 1.000. The overall rate is held down because 39% of its games were against the top six, which is what matchmaking does when the rating rises. From now on predictions are per opponent class.

**v21 candidate (rl240):** 1–4–5 against the v20 bytes over 10 games. More RL made the network stronger on its own but weaker inside the engine, so it is not recommended. Likely cause: the training league has only networks without search, so the policy learns habits that work against them and fail against search engines.

## Update 14:45 UTC — v20 after 130 arena games: best rating so far

Leaderboard 14:30 UTC: **IAmAVirus 1621**, 8th of 12 rated teams (TA Baseline S 1707 above us; TA Baseline A 1580 and TA Baseline P 1467 below). The rating was about 1586 when v20's games began and peaked at 1634.

| v20 vs | score | games |
| --- | --- | --- |
| TA baselines | 0.598 | 56 (P 15–0–3, A 11–2–11, S 5–3–6) |
| top six | 0.125 | 52 (duck 3–1–10, Instructors 2–0–6, the other four 0–2–28) |
| everyone else | 1.000 | 22 |

v15 for comparison: 0.447 against the TA baselines, 0.035 against the top six. The bulk replay mirror is running again (it had stopped at its 30,000-game limit): 30,443 validated games on disk, newest first, at one request per second.
