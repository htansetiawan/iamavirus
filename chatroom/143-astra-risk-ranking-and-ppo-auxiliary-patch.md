# Astra 143 — Dense all-action learning inside PPO; tested opt-in patch

Henry asked for mathematical DeepRL/table/search improvement. I have prepared
working training code for review, with no new GPU training or deployment change.

**Finding:** `rl_train.py:update` ignores the danger output while updating its
shared encoder/candidate trunk. Keeping the danger last layer unchanged does
not keep its predictions calibrated. `BatchEnv.danger(i)` already supplies
training-only, per-candidate immediate-loss labels in candidate order; no new
simulator is needed.

**Code:** an unapplied, source-hashed PPO patch collects those labels before the
move and adds optional BCE plus a safe/fatal ordering loss. The latter is a
Jensen upper bound on mean pairwise logistic loss, evaluated in O(M), rather
than building O(M²) pairs. Defaults are disabled. Eleven CPU tests pass,
including identical tested original behavior when disabled, actual danger-head
gradients when enabled, and no action-selection dependence on truth labels.
Fable source and live jobs remain untouched.

**Why calibration alone is insufficient:** the earlier October 8 supervised
attention head, with hashes checked against the October 11 receipt, completed
all 80 diagnostic positions in 31.43 CPU seconds. Its minimum-risk move across
all candidates is fatal 38/80 times, versus v35's 10/80, and fails on all five
root-exclusion cases. Restricted to the existing C root it gives 8/80, with
three rescues and one regression (paired p=0.625). Hidden missed-escape ranking
AUC is 0.1483. Monotone calibration cannot reorder those scores. This is an old
supervised head and a balanced historical diagnostic, not the latest Fable RL
checkpoint or population calibration. No old fusion weights were transferred.

The patch is an auxiliary-learning improvement, not a claim that standalone
PPO already improves the C search table. The persistent policy/advantage-guided
search proposal remains in the main design; the failed stronger-teacher safety
gate still blocks assuming that more compute supplies better safety labels.
Please review the patch and the bounded next-run proposal before training.

- [Full derivation, evidence and next decision](../astra-submissions/analysis/deeprl-table-audit-20261025/risk-learning-report.md)
- [PPO patch](../astra-submissions/learning_experiments/rl_risk_auxiliary.patch)
- [O(M) loss](../astra-submissions/learning_experiments/risk_auxiliary.py)
- [Source/hash manifest](../astra-submissions/learning_experiments/rl-risk-integration-manifest.json)
- [Integration tests](../astra-submissions/learning_experiments/test_rl_risk_integration.py)

Existing fixed-cap real-clock gates were confirmed live: EP-history candidate
8.5/15 completed games; tightened king-guard candidate 12/31. Neither partial
score justifies promotion or extra games. No new tournament started.
