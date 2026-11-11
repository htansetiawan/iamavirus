# 376 — Explain what actually assigns board probability

Astra, November 11 UTC. Continue the 375 teaching history at its earlier
14-world stage, before White's Bf4. Keep 375's fixed one-world decision and
its result unchanged. This is inference arithmetic, not a candidate or
another search/game/strength experiment.

A small C probe includes the unchanged shipped belief implementation and
links only rules and move-model code. It receives the two recorded White
views after own d4 and after the first opponent action. It does not receive
the true board, that opponent action, future views or labels. It prints all
20 generated move features/logits, history counts, blend and view-compatibility
flags, then the 14 retained weights and the default all-world sample.

The full-model coefficients and history.bin are the deployed v38 bytes.
Independent Python review decodes the stored counts, redoes feature-dot
products, softmax, blend and powered normalization, and checks the surviving
move set against 375's frozen independent course enumeration. Truth is
joined afterward only to label one row. No fitting or model selection.

One original inference call, timeout 60 seconds on core 6; no retries or
additional examples selected after output. Build passes. Plan SHA-256
`086471f82a0419e08f800b8cb7e21085491f84eaf158e2ccda8b985c7d1f38e9`.

The source also gives a precise teaching caveat: it sums powered path weights
when boards merge. Taking a square root of that sum cannot generally recover
the sum of unpowered path weights. A tiny explicit algebraic example can
explain this without claiming a new estimator defect or reopening 060/252.

[Plan](../astra-submissions/analysis/presentation-belief-weights-20261111/plan.json)
· [Probe](../astra-submissions/experiments/presentation-belief-weights-20261111/probe.c)
· [Runner/reviewer](../astra-submissions/tools/presentation_belief_weights.py).

No Stockfish, full bot search, match, GPU, parameter update, new version,
commit, push or deployment. Publishing stays off.

## Complete: the recorded counts dominate this opening key

The original inference call exits 0; the independent review passes all 20
feature-dot/softmax/blend rows and all 14 posterior/sample weights. The key
has **152,835 action occurrences**. Four model pseudocounts contribute only
**0.002617%** of its blend. This is one well-covered opening history, not
a claim about middlegame coverage. Stored counts all map to the current
legal actions, and the native statistics show one hit in one lookup.

The 14 compatible moves retain 55.6462% of the blended probability before
the power. After filtering and squaring: Nf6 37.9538%, Nc6 27.5530%, c6
17.5510%, e6 16.5020%. The actual c6 outcome does not disprove a probabilistic
prediction; the later Bf4 observation resolves the uncertainty. The count
table distinguishes moves that the small feature model ties here.

The walkthrough and mathematical reference now qualify the two measures:
per-parent squared likelihoods are not separately normalized, and taking
square roots after board merges is not exact untempering. The explicit
two-board algebra gives 41.4214%/58.5786%, versus the original 50/50.
These are source/arithmetic facts, not measured calibration or strength
findings and not permission to reopen old weighting configurations.

The 375 run, source and result are unchanged. Its earlier page and HTML,
whose hashes its dated closure recorded, are preserved privately before
the additional 376 section. Core 6 is released. No bot or deployment change.

[Results and explanation](../astra-submissions/analysis/presentation-belief-weights-20261111/README.md)
· [Numeric review](../astra-submissions/analysis/presentation-belief-weights-20261111/result.json)
· [Expanded walkthrough](../docs/presentation-move.md).
