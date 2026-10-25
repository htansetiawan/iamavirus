# Teacher-readiness gate: four times the search budget did not improve safety

2026-10-25. Astra. This is a completed, bounded diagnostic of the existing
teacher, not a new learned bot, a tournament, or an Elo estimate.

## Result

The fixed panel has 80 positions from 80 distinct games, with five slices of
16. Both searches use the **same frozen belief, sampled worlds, root action
identities and root exclusions**. The budgets are 0.4 and 1.6 seconds. Each pair
runs in one engine process; order alternates to reduce systematic warm-cache
advantage. Both use the shipped Stockfish and history table. Prefix reconstruction
uses the normal 10-second maximum setting for both, avoiding budget-dependent
belief reconstruction as a confound.

All 80 pairs completed inside the ten-minute cap and passed the export checks.
Offline referee labels found:

| Diagnostic slice | Cases | Base fatal choices | 4× teacher fatal choices | Rescued | Regressed |
|---|---:|---:|---:|---:|---:|
| Hidden attack, recorded escape missed | 16 | 6 | 7 | 0 | 1 |
| Visible attack, recorded escape missed | 16 | 2 | 2 | 0 | 0 |
| Hidden attack, recorded escape succeeded | 16 | 2 | 2 | 1 | 1 |
| Visible attack, recorded escape succeeded | 16 | 0 | 0 | 0 | 0 |
| Ordinary controls, no current king attack | 16 | 0 | 0 | 0 | 0 |
| **Total** | **80** | **10** | **11** | **1** | **2** |

Every selected move was pseudo-legal. “Fatal” means the move leaves our king
capturable immediately under the independent referee. Only three pairs differ
on that binary outcome: the exact two-sided discordant-pair test gives p=1.
This is **no evidence of a safety improvement**, not evidence that longer search
is generally weaker. Nonfatal strategic quality and eventual game outcomes are
not measured by this diagnostic.

## The actionable defect in the proposed learning pipeline

In five cases, every actual safe escape was absent from the root action set.
The exported exclusion list explicitly contains every such escape, and the
engine log identifies the king guard as excluding moves:

| Game | Decision frame | All true escapes excluded | Base selected |
|---|---:|---|---|
| 5osaf68l | 77 | f5g5, f5g4 | f5e4 |
| xg494buf | 99 | g5f6, g5h4 | g5h6 |
| 2w26eevv | 71 | b8c7, b8b7, b8a7 | b8a8 |
| ob3vxglp | 89 | h7g7, h7g6 | h7h6 |
| jeoowbe2 | 168 | h1g2 | h1g1 |

Thus five of the base's ten fatal choices are structurally unavoidable **within
the supplied root action set**. An arbitrary improvement in root ordering
cannot recover those removed moves. In four attack positions across the panel,
the sampled worlds contain no current attack on our king at all; one overlaps
the five exclusion cases. These are different failure mechanisms and should
remain separate labels.

Mathematically, if the deployed action support is fixed by a mask `M(I,a)`,

\[
 \pi_\theta(a\mid I)=
 \frac{M(I,a)e^{f_\theta(I,a)}}{\sum_b M(I,b)e^{f_\theta(I,b)}}.
\]

When `M(I,a)=0`, that action's probability and its derivative with respect to
its own logit are zero. A learned prior behind the same hard mask cannot restore
it. Distilling the masked teacher while treating omitted actions as negative
targets would additionally teach the model to reject the escapes.

The guard estimates risk from an uncertain posterior. Its decisions are not
proofs that excluded moves are fatal. This selected panel does not establish
the guard's net playing-strength effect; it may prevent many other losses.
Disabling it globally is not justified by these five examples. What *is*
justified is revising the learning contract: retain all rule-legal alternatives
and their evaluation provenance in training records, distinguish logical
illegality from estimated risk, and jointly review posterior/danger calibration
and the deployed exclusion mechanism before expecting a new policy to repair
these failures. The existing `FogPolicy` already has a danger head and pretraining
already uses candidate-wise BCE; adding another identically named head is not
the missing implementation.

## Throughput evidence

The 80 pairs consumed **494.3 seconds** of case wall time. The two searches plus
their export callbacks accounted for **138.5 seconds**; **355.8 seconds** was
outside those calls, including engine startup, history-table loading, replaying
observation prefixes, guards on forced moves, and teardown. Median case time
was 3.83 seconds; the nearest-rank 95th percentile was 17.37 seconds.

These measurements do not isolate those individual overhead components, but
they show why a faster GPU alone will not accelerate this producer much.
Production collection should keep engines alive and reuse reconstructed game
prefixes when emitting several decisions from a game. The existing batched
simulator should be reused rather than rebuilt. This audit used no GPU.

## Decision and limits

Do **not** spend the proposed bulk-distillation budget on the assumption that
4× compute makes this a demonstrably safer teacher. Keep the C exporter, the
verified replay labels and the fixed panel. Bring the two concrete bottlenecks
to committee review: posterior/sample coverage and hard exclusion of uncertain
actions. No further scalar guard sweep or training branch was started.

The panel is balanced and historical, not a representative arena sample. Prior
models may have seen its games. The 4× choice is the raw root selector, whereas
the base choice also passes through the real front end; alternative front-end
fallbacks for the teacher are not simulated. The test uses one seed per case
and small budgets. It does not assess a full-game RL policy or prove a global
improvement or regression.

## Reproduce and inspect

`teacher-readiness-80-result.json` stores the raw pairs, exact observation-only
inputs, sampled hypotheses, instrumented-source hashes and per-search runtime.
`teacher-readiness-80-labels.json` contains separately computed privileged labels.
`teacher-readiness-80-summary.json` verifies their hashes and lists all exclusions.
True replay boards are used only by the post-hoc auditor, never by the actor.

```sh
taskset -c 0,1 python3 astra-submissions/analysis/deeprl-table-audit-20261025/run_engine_probe.py \
  --paired --seconds 0.4 --wall-cap 600 \
  --panel astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512/teacher-readiness-panel.json
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/audit_teacher_choices.py \
  astra-submissions/analysis/deeprl-table-audit-20261025/teacher-readiness-80-result.json \
  --referee-dir /home/henrytan/git/fow-starter
python3 astra-submissions/analysis/deeprl-table-audit-20261025/summarize_teacher_readiness.py
```

Save command output to a new artifact when rerunning; do not overwrite the
published result. Reserve cores before rerunning. The audit released cores 0–1
on completion; the two pre-existing full-clock game gates continue separately.
