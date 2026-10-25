# Learning candidate risk inside PPO, with an explicit connection to search

2026-10-25. Astra. Concrete code and experiment proposal for Henry/Fable review.
No model training run, deployment change, or new strength claim.

## What the existing learned head actually does

The earlier attention-small checkpoint is available on the newly mounted
`/media/henrytan/seagate1/`. Its native probe, manifest and ONNX files match the
hashes in the October 11 receipt. This is the **October 8 supervised model**,
not evidence about the latest Fable RL checkpoint. No old particle/neural fusion
coefficients were transferred to the current C engine.

On the same fixed historical 80-game diagnostic panel as the search audit:

| Selector | Immediately fatal choices / 80 | Rescues vs v35 | Regressions vs v35 |
|---|---:|---:|---:|
| Actual v35 base search | 10 | — | — |
| Minimum neural risk, all native candidates | 38 | 2 | 30 |
| Maximum neural policy, all native candidates | 35 | — | — |
| Minimum neural risk, restricted to current v35 root | 8 | 3 | 1 |

All 1,925 scored candidates are legal under the independent referee. The neural
candidate list covers every current C root move. Within the current root, the
exact two-sided discordant-pair p-value is 0.625: **a diagnostic signal, not a
promotion result**. The unrestricted selector fails on all five previously
identified positions where the guard excluded every true escape.

For the 16 hidden-attack/missed-escape cases, mean within-decision safe/fatal
ranking AUC is 0.1483 (higher is better); its minimum-risk move is fatal in all
16. A monotone probability calibration cannot repair that ordering. This does
not rule out a better model, history representation or retraining. It rules out
assuming that recalibrating this frozen score alone will recover these escapes.

Collection completed 80/80 cases in 31.43 CPU seconds, with no GPU. The model
received observations and prior **own** moves only. Full truth was used after
inference for referee labels. The balanced, failure-enriched historical panel
is neither an arena-distribution calibration set nor a guaranteed unseen model
test set. Its Brier/log-loss values must not be presented as population risk.

Reproducible artifacts: [collector](collect_existing_danger.py),
[raw predictions and input provenance](existing-danger-80-result.json),
[analyzer](analyze_existing_danger.py),
[per-candidate labels and paired results](existing-danger-80-analysis.json).

## A source-level PPO gap we can fix directly

`learning/model.py` shares the recurrent encoder and candidate trunk between
policy and danger heads. `learning/rl_train.py:update` currently uses
`logits, _ = learner.score(...)`; its actor loss is PPO + reference KL − entropy.
The danger output receives no supervised objective during RL.

For danger logit `z_d(I,a)=w_d^T h_theta(I,a)+b_d`, even if the last-layer weights
stay fixed, updating the shared representation changes the score:

\[
 \Delta z_d \approx w_d^T J_\theta h_\theta\,\Delta\theta.
\]

Thus frozen last-layer weights do not preserve risk calibration. This is a
mechanism to monitor, **not proof that a particular RL run regressed**, and it
does not explain the supervised checkpoint's errors above.

The simulator already implements `BatchEnv.danger(i)` via
`batch_env.cc:fow_batch_danger`. Before moving, it evaluates every candidate
on a copy of the true board and returns immediate-loss labels in candidate
order. Use that existing API for labels, never as an actor input. This provides
all-action immediate feedback without another simulation rollout per action.
It does not provide counterfactual eventual game returns; those still require
search or appropriately sampled continuations.

For actor information history `I`, the desired calibrated prediction is

\[
 p_\theta(I,a)\approx
 \Pr_{s\mid I}[\text{our king is lost immediately after }a].
\]

One realized replay board supplies a binary sample, not certainty conditioned
on `I`. Indistinguishable histories can legitimately have conflicting labels.
Expected binary cross-entropy is minimized at the conditional probability;
the model must not memorize truth as if the player observed it.

## Implemented O(M) action-separation loss

Let `S` and `F` denote safe and fatal candidates in one training position, and
let larger `z_a` mean greater predicted danger. A pairwise ranking loss is

\[
 L_{pair}=\frac{1}{|S||F|}\sum_{s\in S,f\in F}
          \log(1+e^{z_s-z_f}).
\]

Direct evaluation costs `O(|S||F|)`. Concavity of `log` gives the following
upper bound, computed with two stable log-sum-exp reductions:

\[
 L_{pair}\le L_{sep}=
 \operatorname{softplus}\left(
 \operatorname{logmeanexp}_{s\in S}z_s+
 \operatorname{logmeanexp}_{f\in F}(-z_f)\right).
\]

This costs `O(M)` work and storage, where `M=|S|+|F|`; no pair matrix. If the
softplus argument is `g`, its gradients are

\[
 \frac{\partial L_{sep}}{\partial z_s}
   =\operatorname{sigmoid}(g)\operatorname{softmax}_{S}(z)_s>0,
 \qquad
 \frac{\partial L_{sep}}{\partial z_f}
   =-\operatorname{sigmoid}(g)\operatorname{softmax}_{F}(-z)_f<0.
\]

Gradient descent lowers the mistaken high-risk safe scores and raises the
mistaken low-risk fatal scores. The bound focuses more on extreme ordering
errors than the exact pair mean. It is shift-invariant, so BCE remains needed
to learn the probability offset. The ranking term can itself change calibration;
its coefficient is optional, not a new theorem about calibrated probabilities.

The proposed actor objective is

\[
 L=L_{PPO}+\alpha KL(\pi\|\pi_{ref})-\beta H(\pi)
       +\lambda_r\left(L_{BCE}+\lambda_sL_{sep}\right).
\]

This retains terminal-reward learning of winning strategies and adds dense
immediate-risk supervision. No hand-coded tactical pattern or player-name rule
is introduced. The all-action labels are correlated within a position; 1,925
candidates are not 1,925 independent games. Oversampling failure cases changes
the training distribution: use known sampling weights or recalibrate on fresh
representative data, and validate rankings separately.

Implementation: [risk_auxiliary.py](../../learning_experiments/risk_auxiliary.py).
It handles padding, empty/single-class rows, decision weights and mixed precision.
Rows without both classes contribute BCE but no separation loss. The default
separation coefficient is zero.

## Reviewable trainer integration, not just a loss on paper

[rl_risk_auxiliary.patch](../../learning_experiments/rl_risk_auxiliary.patch)
is an **unapplied** patch against a hashed copy of Fable's current PPO trainer.
It collects labels before stepping, preserves candidate order, feeds them only
to the loss, and logs BCE/separation/contrast counts. Both configuration options
default to zero. Enabling `risk_aux_coef` adds BCE; `risk_separation_coef` adds
the optional separation term inside that auxiliary objective.

Fable's source and live jobs remain unchanged. The patch needs
`PYTHONPATH=astra-submissions:.` for the auxiliary import, or Fable can move the
reviewed primitive into its own package when integrating. The source, patch and
expected patched-file hashes are in
[the integration manifest](../../learning_experiments/rl-risk-integration-manifest.json).

Eleven CPU tests pass. They check the mathematical bound, gradient directions,
padding/nonfinite handling, empty batches, decision weighting and FP16/BF16
promotion. Integration tests apply the patch to a temporary copy and execute
the real rollout/update function bodies with the real recurrent actor and a
small simulator double. Disabled behavior matches the tested original rollout
and parameter update exactly. Changing truth labels leaves the sampled action
unchanged; enabling the loss trains the existing danger head. These are
correctness tests, not a new trained checkpoint or native-simulator strength test.

```sh
PYTHONPATH=astra-submissions:. taskset -c 0,1 .venv/bin/python -m unittest \
  learning_experiments.test_risk_auxiliary \
  learning_experiments.test_rl_risk_integration -v
```

## How this fits the larger table/search investment

The [main design](README.md) distinguishes the frozen opponent-history prior,
per-search PCFR+ arrays, and a persistent learned information-state model. A PPO
actor improvement alone does not update the C engine's prior or regret arrays.
This auxiliary patch is a concrete prerequisite if we reuse its risk head;
it is not delivery of the whole search-learning loop.

The durable target remains **search-guided policy iteration**: collect
information histories and supported all-action values; learn root policy and
counterfactual advantage; spend search on promising or unresolved alternatives;
measure the final deployed selector; generate fresh data and repeat. Do not use
actor PPO ratios for actions actually selected by the separate search policy.
Do not train excluded/unsearched moves as negative examples.

The 80-case teacher gate prevents an expensive mistake: 4× compute alone gave
10→11 immediate-fatal choices, including five root sets with no surviving safe
escape. We need to improve information/support and learnable risk before claiming
that this teacher's safety labels are improved. This result does not measure
its nonfatal strategic quality or imply that all its action values are useless.

For speed, 355.8 of 494.3 seconds in that teacher audit were outside search/export.
Persistent engine instances and prefix reuse are the first producer optimization
to measure. A heap cannot repair discarded action support or a missing attacker
hypothesis, and a GPU does not remove process/history-reconstruction overhead.

**Next decision for committee review:** accept or reject the opt-in PPO patch;
choose the current checkpoint and one fixed auxiliary setting before any run.
Use a game-disjoint later-time validation set plus this diagnostic panel. Cap one
training run at two GPU hours, preserve a matched original-loss control, and
report ranking, calibration, policy return and throughput separately. Stop on
input leakage, nonfinite training, or worsening tactical choices. Do not promote
from lower loss alone or remove the C guard on this evidence. The 24-hour review
must end with a continue/change/stop decision even if matches are incomplete.
