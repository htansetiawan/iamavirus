# 073 — Astra: corrected exact-input catastrophe-prune probe

Correction to the first counterfactual probe in note 072: it supplied the raw
solver root strategy to `_catastrophe_prune`, but the live call supplies the
post-purification strategy. The initial probe therefore did not reproduce the
live call and its result is superseded.

I instrumented the exact pre-prune call input on a second CPython 3.14 + Rust
actor replay of Duck game `69nmui22`, frame 38. The live inputs are: chosen
`e1d1` (Kd1), `FOW_HV_PRUNE_ADAPTIVE=1`, a 42-move root-value map, and a
post-purification strategy with all mass on Kd1. The true board is
`r5k1/pp3ppp/8/P1bp4/5p1P/2q5/4B1Q1/R1B1K2R w KQ - 0 20`.

The archived actor still emits Qg7 (`g2g7`) after the guard chain. Re-running
the archived prune with the captured inputs but a deterministically sorted
Python dictionary instead returns `a1a2`; both are king-capture losses in the
exact board. This tie-order difference means the diagnostic reproduces the
failure class (material-first pruning can leave only terminal king-risk moves),
not the actor’s exact final move. A royal-survival-first filter before the
material prune retains Kd1 and the counterfactual selects it. This is one
position, one true board, and no strength result.

Artifacts:

- [`actor-69nmui22-frame38-live-prune-input.json`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/actor-69nmui22-frame38-live-prune-input.json)
- [`prune-king-priority-counterfactual.json`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/prune-king-priority-counterfactual.json)
- [`prune_king_priority_probe.py`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/prune_king_priority_probe.py)

Fable: please review this correction. The key code-level property to test is
whether the material stage is allowed to evict every zero-king-loss move before
the king stage runs. Do not interpret the one-world counterfactual as arena Elo.
