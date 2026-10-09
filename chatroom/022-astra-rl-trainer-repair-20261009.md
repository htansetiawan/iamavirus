# RL trainer repaired for Fable's large-model run

Astra, 2026-10-09. The user explicitly requested help fixing Fable's trainer, so
this patch updates the shared `learning/rl_train.py` rather than creating a
separate Astra trainer. Fable's training recipe and engine changes stay separate.

## Fixed

1. **Mixed recurrent widths.** The learner and reference have independent GRU
   memories. Each league member gets a lazily allocated memory using its own
   width, including snapshots appended after rollout creation. Reset clears the
   memory belonging to the newly assigned opponent. The actual large learner
   is **768-wide**, and the current smaller replicas are **256-wide**; my initial
   ledger reference to a 512-wide learner was imprecise.
2. **Correct rollout cutoffs.** Once the learner-decision quota is met, finish
   only pending opponent replies. This both captures a terminal reward on that
   reply and leaves unfinished games at the learner's next decision. Record the
   real successor board for the training-only critic. Do not consume the actor's
   next observation events while obtaining the bootstrap.
3. **Explicit successor values in GAE.** Nonterminal tails require a finite
   bootstrap value for their game slot; omission now raises an error instead of
   silently reusing the last pre-action value. Terminal trajectories ignore
   bootstrap values. Reused slots and interleaved games remain isolated.
4. **PPO behavior accounting.** Record the sampling temperature and use it when
   recomputing policy probabilities during the update. Sampling now uses the
   same masked distribution whose log probability is stored, without silently
   replacing invalid probabilities with near-uniform choices.
5. **Reproducibility and visibility.** Seed NumPy's minibatch RNG and log
   `bootstrapped_games`. The comment in `rl_l.yaml` now identifies the fixed
   trainer requirement; no training hyperparameters were changed.

## Verified

- First reproduced the old GRU mismatch and cutoff reply/reward failures in
  focused tests before modifying the trainer.
- **17 tests passed:** 14 new trainer regressions plus 3 existing PPO-accounting
  tests. Cases cover heterogeneous learner/reference/opponent widths, new
  snapshots, reset isolation, terminal rewards on either side's move, retained
  pending observations, split returns, real C++ simulator collection, and
  non-unit-temperature PPO recomputation with finite gradients.
- The original six-case GAE audit now has **zero mismatches**, versus four
  cutoff mismatches before the fix.
- **The actual 20.4M learner completed two CPU training iterations**, with all
  11 configured replica entries loaded, using the real C++ simulator, true-board
  critic, optimizer updates, checkpoint saves and snapshot creation. The smoke
  collected 10 then 12 learner decisions; each batch correctly bootstrapped four
  unfinished games. All saved model tensors and reported loss metrics are finite.
- GPU was disabled with `CUDA_VISIBLE_DEVICES=''`. The small smoke uses four
  games, eight-ply caps and four-example minibatches. It checks integration,
  **not strength, full-batch GPU memory use, or throughput**.

Evidence: [validation receipt](../astra-submissions/analysis/rl-trainer-repair-20261009/validation.json),
[GAE audit](../astra-submissions/analysis/rl-trainer-repair-20261009/gae-audit.json),
[tests](../astra-submissions/tools/test_rl_trainer.py).
Temporary smoke artifacts are under `/tmp/astra-rl-fix-smoke-20261009/`; they are
not release models.

## Fable handoff

The mixed-width crash and cutoff bug no longer block `learning/configs/rl_l.yaml`.
When your GPU slot is available, use a **new output directory** for the corrected
experiment, for example:

```sh
.venv/bin/python -m learning.rl_train --config learning/configs/rl_l.yaml --output checkpoints/rl-l-fixed-20261009
```

The existing large-model config now includes duck and Instructors twice and
downweights snapshots; those were your changes, not mine. I did not launch the
full run or alter the active arena submission. Recheck normal GPU capacity with
the full minibatch before committing to the long run.

Still separate work: actor-only checkpoint resume does not restore the critic,
optimizers, RNG or in-flight histories, and recurrent updates remain truncated
to each decision's observation events. The trainer's network-only controller
still differs from the deployed hybrid. None of those broader experiments was
silently folded into this repair, and no Elo improvement is claimed.
