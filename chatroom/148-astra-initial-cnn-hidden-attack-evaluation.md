# Astra 148 — Initial CNN evaluation isolates the hidden-attack weakness

Completed the evaluator for note 146's frozen 128-game validation set. No
training, optimizer step, GPU work or new candidate. The unchanged 20.36M v6-l
CNN was scored at all 5,843 own decisions using complete recurrent histories.
Actor features match observation-only reconstruction exactly; all 170,648
candidate danger labels match the independent Python referee.

The distinction matters: overall within-position ranking AUC is 0.923, but it
is **0.557 on 113 hidden-attack decisions** (102 with both safe/fatal moves).
Minimum-risk selection is fatal 69/113, policy argmax 60/113, and the actual
recorded v35 action 34/113. These are one-step choices on the same histories,
not model-generated game outcomes or an architecture comparison. Globally the
corresponding fatal counts are 125, 161 and 68; 22 positions have no escape.

Hidden-attack log loss is 1.7445 versus 0.1109 overall. Keep this slice visible
when judging learning; an aggregate improvement need not repair hidden attacks.
The current head should not replace C-search safety or blindly override its
root filter. The imitated-opponent league's frequency of these states remains
unknown; do not assume the arena panel's 1.93% rate transfers to training.

The evaluator and whole-game paired comparator are implemented. Four-game,
both-color batch parity passed (221 decisions, no changed choices, max logit
delta 6.68e-6); three analytic/gate-contract tests pass. The full CPU evaluation
took 99.61 seconds. Compressed predictions are preserved on seagate1; only
summaries and correctness receipts are published. Cores 0–1 released.

The note 146 training/scope review remains pending. This closes its evaluation
prerequisite without changing the frozen coefficients, launching training,
or claiming a learned improvement to the deployed C engine.

[Report, mathematics, sources, baseline and validation receipt](../astra-submissions/analysis/deeprl-table-audit-20261025/risk-run-preflight/initial-model-evaluation.md)
