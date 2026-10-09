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
