# Astra 141 — Real-tree exporter works; 4× search still teaches the hidden-rook loss

2026-10-25. To Henry and Fable. Follow-up instrumentation for the plan in 140;
no new model training or tournament.

The C target exporter now runs on the real archived v35 GT-CFR path. Four
observation-only replay prefixes pass numerical and action checks, including
agreement with the original solver's `game_value` and the final protocol move.
The callback runs after move selection and emits to a separate offline file.
Source archive and Fable code remain unchanged.

The crucial sanity result is on guard-pair-8, White's decision at frame 54:

| Budget | Nodes | Iterations | Chosen | Referee label |
|---|---:|---:|---|---|
| 0.4 s | 23,523 | 400 | c7e6 | Fatal |
| 1.6 s | 67,713 | 1,120 | c7a8 | Fatal |

The input history and sampled worlds are the same. Both samples contain 22
distinct hypotheses from the 392-entry belief. **None contains the existing
king attack.** Both put zero strategy mass on the two safe king moves, f1e2 and
f1g2. The longer search rates them slightly below the chosen fatal move.

This is one selected counterexample, not an aggregate rejection of distillation.
But it means “4× budget” cannot by itself certify a better teacher. Training
blindly on this row would confidently copy the known mistake. Add a fixed
teacher-readiness panel before bulk generation, covering known failure families
and ordinary controls. Keep failures in the audit set; don't hide them or feed
truth to the solver. Unsupported attack cases require improving posterior or
observation-conditioned danger estimation, with held-out calibration evidence.

Another target contract detail: default root fatal utility is **-2**, not -1.
The teacher learns a shaped search objective, not a win probability. The export
now records `root_loss_value`, exact root action values, probabilities, avoided
moves and diagnostic sampled hypotheses. Actor inputs and post-hoc truth labels
are kept separate. The full production data contract still needs per-action
evaluation provenance and guard reasons; the prototype does not claim those.

Reviewable code, commands and recorded evidence:
[DeepRL target audit](../astra-submissions/analysis/deeprl-table-audit-20261025/README.md),
[four-prefix result](../astra-submissions/analysis/deeprl-table-audit-20261025/engine-probe-result.json),
[budget comparison labels](../astra-submissions/analysis/deeprl-table-audit-20261025/teacher-budget-labels.json).

No Fable response or human plan review had arrived when this check ran. The
proposed training branch remains pending that review. The two older game gates
are still running at their existing fixed caps; this audit released cores 0–1.
