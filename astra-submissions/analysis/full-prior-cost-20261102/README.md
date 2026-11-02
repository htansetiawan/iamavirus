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
No playing candidate, model weights, live settings or ongoing219 dependency
has changed. This is a fixed-state engineering test before any broader test.
