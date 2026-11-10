# 339 — The attention prior passes independent prediction confirmation

The original [326](326-astra-corrected-teacher-future-contract.md) run passed
all 12 gates on its first 300 eligible future trajectories. Source audit
verified 26,285 frames before scoring. The independent reviewer regenerated
17,384 contexts and their metrics, including 14,080 primary decisions.
The model retained its epoch 11 weights and the corrected arithmetic.

| Comparison | Gain in nats per primary decision | 95% whole-game interval |
| --- | ---: | ---: |
| Native v38 prior | 0.14883 | [0.13455, 0.16341] |
| Same-split quadratic | 0.09530 | [0.08317, 0.10730] |
| Quadratic fitted on 4,000 games | 0.09443 | [0.08188, 0.10680] |

The gains against Duck, Instructors and HYPOTHERMIA were 0.168, 0.103 and
0.131 nats. The audit checks 31,297 unchanged capture-action probabilities,
1,449 primary surprise captures, native-control error below 3.82e-6, and a
64-context FP64 comparison. Original session `37602` exited 0 and released
cores 2–3. All 62 source pins match. Raw rows remain in the private spool.

The result supports distilling the quiet-move prior into a model small enough
for the belief update. The next fit needs a matched hard-label control and a
full-clock runtime budget. The earlier 320 arithmetic failure and 323
sequential posterior result retain their original decisions. Any future fit
using the recovered cache must respect the sealed trajectory hashes when
choosing its independent tests.

[Metrics](../astra-submissions/analysis/prospective-quiet-teacher-20261110/result.json)
· [Independent review](../astra-submissions/analysis/prospective-quiet-teacher-20261110/independent-review.json)
· [Execution receipt](../astra-submissions/analysis/prospective-quiet-teacher-20261110/terminal-verification.json).
