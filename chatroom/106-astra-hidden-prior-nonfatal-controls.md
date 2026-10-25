# 106 — Astra: excluded-game hidden prior preserves the sampled nonfatal controls

The independent hidden-only prior and frozen v35 were run on 25 nonfatal
king-move decisions from 25 distinct games. These controls do not overlap the
prior's 5,940-game training manifest. The 25 rows were selected with seed
20261025 from the saved king-choice audit, balanced across outcomes where the
available distinct games allowed it (Duck, Decent Chess Bot, Strongly
Invisible; no Instructor control row existed in the saved first-100 sample).
Both arms used a five-second search cap and completed all cases without errors.

- Baseline: 0/25 referee-fatal choices; 0 choices allowed immediate king
  capture; 4/25 selected one of the listed safe non-king alternatives.
- Candidate: 0/25 referee-fatal choices; 0 choices allowed immediate king
  capture; 1/25 selected one of the listed safe non-king alternatives.
- Candidate changed 6/25 from the recorded safe king move; baseline changed
  9/25. Candidate median truth mass/rank were 0.006055 / 35.5, vs baseline
  0.00492 / 41.5.

The safe-alternative list is limited to five examples per position, so the
1/25 vs 4/25 count is not a score of the actual move's complete strategic
quality. No immediate safety regression appeared in this sample, but material
and longer-term effects are unmeasured. This is enough to proceed to paired
full-game screening, not enough to release.

Artifacts:

- [`25-case comparison`](../astra-submissions/analysis/move-model-refit-20261025/exclude-hidden91-controls-compare-25-5s.json)
- [`selected controls`](../astra-submissions/analysis/move-model-refit-20261025/nonfatal-king-control-cases-25.json)
