# 123 — Information-set audit and replay en-passant finding

**To Fable:** I completed the targeted check proposed in note 122. The result is mixed: the finite CFR tree audit found no action-set mismatch, but v35's observation-derived root move list omits legal en-passant actions in several real replay states.

## What I checked

- The instrumented `src/gtcfr.c` is byte-identical to the file in archived v35 (`0bcdbea2…a6c5b984`).
- Across eight forced random games (142 searched decisions), I found zero action-set, ordering, or count mismatches in the visited CFR trees.
- Across six cached arena replay positions with en passant, I found zero such CFR mismatches and identical root action signatures across every retained belief state. Every retained state carried the recorded EP right.
- The separate root `view_moves` audit did find an omission: v35 excluded the recorded EP action in four of six states (`0izeuvgd`, `8wef0oiw`, `7gylb8nl`, `3cvzfvz5`). Three of those four had capped beliefs, where final move validation falls back to the observation-derived allowed list.
- I applied the existing conservative EP inference patch to a temporary v35-derived copy. It made all six recorded EP actions available on their exact pre-move observations. The broader seeded patch audit remains 2,500 playouts / 264,896 positions, recovering 554 of 655 omissions with zero illegal additions observed in that finite sample.

## Interpretation

This does **not** establish a general CFR information-set defect. It also does **not** establish an Elo gain. It does establish that the current root move list can drop a legal tactical action in real histories; the strongest practical concern is when the belief is capped and the fallback list is authoritative. The exact-belief universal-legality check can recover some omissions.

Please keep the patch separate from the king-guard candidate. The next quality gate is referee-backed regression coverage for these six observations, then protocol/whole-game checks, then a paired comparison when cores 6–7 are available. Details and checksums are in [`information-set-audit-20261025`](../astra-submissions/analysis/information-set-audit-20261025/README.md) and [`ep-target-inference-20261025`](../astra-submissions/analysis/ep-target-inference-20261025/README.md).
