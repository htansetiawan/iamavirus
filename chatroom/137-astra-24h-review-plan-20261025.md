# Astra 137 — 24-hour checkpoint and committee review

**Date:** 2026-10-25 17:06 UTC; revised after Henry’s review
**Audience:** Henry, Fable, Astra
**Purpose:** Stop open-ended experimentation and submit the current evidence plus one bounded next-step proposal for review.

## Current evidence

### Existing fixed gates

- **King-guard screen:** v35 versus a one-parameter candidate that changes `MIST_KING_GUARD` from `0.02` to `0.0001`. This is a narrow heuristic-parameter screen, not the strategic direction. The fixed 20-pair run has completed 20/40 games at this checkpoint; the candidate has 9/20 game points (0.45). One recorded regression is the pair-8 hidden rook attack; both binaries choose the same fatal move, and the actual board ranks 158/392 in the belief. This is neither a promotion result nor evidence that further guard tuning will fix the posterior miss.
- **En-passant history screen:** v35 versus the observation+history action-availability patch has completed 4/40 games and scored 3/4. It has had one actionable candidate-side EP option: after `d3d5`, candidate Black had `c5d4` available but chose `d8d5`. A second apparent option came on the terminal frame after `a2a4`, when the game had already ended by king capture, so Black never received a turn. No candidate choice has changed to EP so far; the 3/4 score is not evidence for this action-availability treatment.

Both are already-running, pre-existing 180+2 local comparisons on separate CPU pairs. They use no GPU. Do not extend either gate beyond its registered 20 pairs.

### Replay evidence for a composable attack pattern

A new scan covers **123,251 cached public games** matching the top-team name filter. It found 326,940 moves that changed the board from no direct attack on the king to a direct attack. Among events with a recorded defender reply:

- A **fully hidden** attacking set remained attacking after the reply in 50,802/144,766 cases (**35.1%**).
- A **visible** attacking set remained attacking in 22,568/174,151 cases (**13.0%**).
- Events without a recorded reply are excluded from both denominators.

The hidden-visible difference is **+22.1 percentage points** (game-clustered approximate 95% interval +21.8 to +22.4 points; 112,148 games contained at least one classified event). By attacker, the same descriptive survival rates are:

| Attacker | Hidden attack survives reply | Visible attack survives reply |
|---|---:|---:|
| Greek Gift | 3,885/12,312 (31.6%) | 1,826/12,032 (15.2%) |
| Instructors | 10,780/27,186 (39.7%) | 4,282/30,880 (13.9%) |
| Knight Vision | 5,583/18,586 (30.0%) | 1,895/16,573 (11.4%) |
| Decent Chess Bot | 3,618/11,366 (31.8%) | 1,731/11,346 (15.3%) |
| Strongly Invisible | 10,991/29,337 (37.5%) | 5,888/32,388 (18.2%) |
| duck | 2,807/8,350 (33.6%) | 1,140/9,093 (12.5%) |

This is a large descriptive association, not causal evidence that concealment wins games. The interval accounts for repeated events within a game, but not corpus selection, player strength, opportunity mix, or strategy confounding. The scan uses true replay boards as offline labels and the victim’s recorded observation for visibility. The hidden-arrival loss in pair 8 is a concrete motivating case, not a representative sample.

Artifacts: `astra-submissions/analysis/hidden-slider-zone-20261025/scan_hidden_king_arrivals.py`, `top-opponents-hidden-king-arrivals-summary.json`, and `top-opponents-hidden-king-arrivals.jsonl.gz`. The script’s basic attack detector was checked on rook, pawn, and color cases; this is not yet an exhaustive differential rules validation.

The current shell cannot communicate with the NVIDIA driver (`nvidia-smi` failure). No GPU training has run in this checkpoint.

## Revised recommendation: learn the search strategy and its value table

Henry’s steering is to invest in DeepRL that improves the information-set strategy table and guides the search tree. The hidden-attack census is now a *training/evaluation target source*, not the primary proposed feature patch. The king-guard scalar remains a narrow control only; it does not justify more heuristic tuning.

### Mathematical target

Let the acting player’s information state be the observation/action history
\(I_t=(o_0,a_0,\ldots,o_t)\), and let \(B_t(s)=P(s\mid I_t)\) be the hidden-board belief. The deployed actor must be \(\pi_\theta(a\mid I_t)\); it must not depend on which sampled hidden board \(s\in B_t\) happened to be used by the search. That constraint prevents strategy fusion.

At a searched information set \(I\), CFR supplies an all-action counterfactual value \(q_t(I,a)\), its current policy value \(v_t(I)=\sum_a\sigma_t(a\mid I)q_t(I,a)\), and instantaneous regret
\[
 r_t(I,a)=q_t(I,a)-v_t(I),\qquad R_T(I,a)=\sum_{t=1}^T r_t(I,a).
\]
Regret matching uses \([R_T(I,a)]_+\); the behavioral target for deployment is the reach-weighted *average strategy*, not a hidden-state-specific best move. The network should approximate the strategy table and its action values, while online search continues to correct those approximations.

### Proposed finite work sequence

1. **Instrument the existing Obscuro-inspired tree.** On a frozen corpus of public histories plus a bounded simulator sample, export information-state inputs, legal actions, visits, counterfactual action values/regrets, average-strategy probabilities, terminal outcomes, and exact search budget. Assert that indistinguishable hidden worlds produce identical actor inputs/action distributions. Public replays alone cannot provide counterfactual action labels; the simulator/search teacher must generate them.
2. **Train one search-distilled network, then one RL fine-tune.** Add an action-value/advantage head to the existing recurrent policy/value/belief model (or an attention variant only as a matched-compute comparison). A concrete loss is
   \[
   L=\lambda_\pi\,CE(\bar\sigma_{search},\pi_\theta)
     +\lambda_A\,Huber(\hat A_\theta,q-v)
     +\lambda_V(V_\phi-z)^2
     +\lambda_B L_{belief}+\lambda_D L_{danger}.
   \]
   Then fine-tune with self-play PPO/actor-critic against a frozen opponent league, retaining a KL anchor to the search-distilled policy and using a critic for variance reduction. If the actor is trained under a different move selector than deployment, correct the behavior-probability mismatch or keep PPO as a separate experiment; never call raw PPO progress a deployed-policy gain.
3. **Use the learned outputs to improve the tree.** At inference, use \(\pi_\theta\) to order candidate actions and seed the information-set regret strategy; use \(V_\phi(I)\) as a partial-information frontier value; use \(\hat A_\theta(I,a)\) and uncertainty to prioritize CFR expansion. Keep the final move selected by the information-set solver. Allocate extra nodes to high posterior entropy / high value uncertainty / hidden-king-risk states, and few nodes when the strategy and value estimates agree. Compare all arms at the same node or clock budget.
4. **Use the replay attack census as a focused slice.** First independently validate its attack labels and report game-clustered confidence intervals plus rates by top opponent. Train/measure posterior mass and danger calibration on held-out newly hidden attacks, visible-attack controls, and ordinary moves. This directs learning toward a proven recurring pattern without making a player-name-specific policy.
5. **Run fixed evaluation gates.** (a) held-out strategy cross-entropy and counterfactual value error; (b) exploitability / NashConv on small exact imperfect-information games and tractable Fog subgames; (c) held-out true-board rank/mass, fatal-action recall at fixed false-positive rate, and tactical controls; (d) one preregistered paired full-clock comparison against pinned v35. Stop after one teacher-distillation run and at most two RL seeds unless a preregistered gate improves. No budget extension based on a promising partial result.
6. **GPU and release.** GPU is currently inaccessible from this shell (`nvidia-smi` cannot reach the driver), so start no training until access is restored. First profile whether the simulator/feature pipeline or network update is the bottleneck; a GPU will not speed a serial CPU referee automatically. Keep large data/checkpoints on the mounted Seagate. Package only if learned search outputs change deployed choices, clear the tactical and matched-budget gates, and show no protocol regression. The next Astra release is v36 only if Fable’s latest numbered submission remains v35; verify mapping and hashes immediately before packaging. Repository publication and arena upload remain separate.

### Why the existing PPO table has not been enough

`FogPolicy` currently predicts candidate policy logits plus danger, a scalar value, and per-square belief marginals. The PPO collector samples directly from that policy and learns from terminal/GAE returns. In contrast, the archived v35 move path chooses through its search/GT-CFR controller and frozen history prior. Therefore PPO’s logged reward improves the *sampled standalone actor*; it does not show that the deployed information-set strategy table or tree improved. Also, a terminal return is a high-variance label for each of many legal alternatives, while search can supply counterfactual values for every explored action.

The data record we need per training example is thus not just `(observation, chosen_move, result)`. It should be `(game_id, I, legal_actions, search_policy, cf_action_values/regrets, value_target, visit_count, sampling_probability, solver_version, budget)`. Public replay actions remain valuable for behavior cloning and opponent modeling, but cannot fill in the counterfactual columns by themselves. Entire games, not plies, must define train/validation/test partitions.

To improve throughput, profile before redesign: split wall time into C/C++ rules simulation, observation/history construction, inference, CFR/search and optimizer. If simulation or Python/C calls dominate, batch many independent games behind a bulk C API and avoid per-ply language crossings; if neural inference dominates, batch policy/value calls and use the GPU; if tree expansion dominates, reduce duplicate worlds and prioritize expansion by learned prior plus regret/value uncertainty. Compare examples-per-second and *search-improved decisions per GPU-hour*, not raw training steps. The driver is currently unavailable, so this is a measurement plan rather than a claim that the RTX is training.

## Review decision requested

Please review this DeepRL/search-table plan and its stop criteria. The human steering now makes the algorithmic priority clear: learn the information-set regret/strategy table and use it to make the tree more selective, then fine-tune on fresh self-play. The guard screen is a small, already-running parameter ablation; its 20/40 score is not significant and no further guard variants are proposed. Astra will let only the two already-registered gates proceed to their fixed stopping points and document their results. No additional model, training, or tournament branch starts without a dated 24-hour plan and review.
