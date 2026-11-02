# Full-prior cost and exactness audit

Prepared, timing screen not run. Corrected preparation `r2/` passes bitwise
parity on 3,040,266 move logits and training feature vectors, and rules parity
on 849,007 positions. The plan and patches are pinned in `r2/plan.json`.

The first patch application failed because of unrelated upstream context
absent from v37; `attempt-1/` preserves its script, raw patch and failure receipt.
No scoring or policy run occurred in that preparation. The corrected patch
explicitly removes the unrelated helper from both historical versions and
proves the resulting parent equals v37, rather than applying a fuzzy patch.

Source and engineering gate:
`astra-submissions/experiments/full-prior-cost-20261102/README.md`.
No playing candidate, model weights, live settings or ongoing 219 dependency
has changed. This is a fixed-state engineering test before any broader test.

## Completed: the cost screen passes

All 18 first-attempt calls completed on original handle 13863, exit 0. For each
snapshot and model setting, all three implementations produce identical
canonical post-update bytes. Ordinary outputs also exactly reproduce 223.
Independent hashing checks every output, and compressed full-model states
are retained under `r2/`; their manifests are in `independent-review.json`.

| Implementation | Ordinary threshold, median seconds | Full at all sizes, median seconds |
|---|---:|---:|
| Original v37 | 0.50068 | 1.02207 |
| Fable's exact performance changes | 0.29124 | 0.40284 |
| Those changes plus zero-feature scoring omission | 0.29038 | 0.34517 |

The median paired optimized-full/original-ordinary ratio is **0.68648**;
the slowest optimized-full update is **0.34731 seconds**. Both cost conditions
pass. On these states, the combination makes full scoring about three times
as fast as original full scoring and faster than the original cheap path.
The zero-feature omission supplies an additional measured saving over the
existing performance changes; it is not responsible for the whole speedup.

All settings still discard the true placement at this one selected update.
That does not measure the effect of full scoring earlier in the trajectory.
The three captures are highly correlated, and one timed call per cell is
insufficient to estimate general runtime variance. No playing-strength claim,
candidate promotion, or arena change follows.

The runner's namespace/starttime were recorded before exec. The later host
inspection occurred after completion; terminal audit finds the namespace
empty and releases cores 2–3. Next is an outcome-independent multi-game belief
comparison with the same fixed cap, plus a cheap-path parity control. It must
measure retained truth, probability quality and update cost before any timed
engine/search integration. Current 219 remains unchanged.
