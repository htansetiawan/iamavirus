# Frozen recurrent risk: reuse experiment closed

2 November 2026. The recovered attention/GRU danger head does not pass its
predeclared complementarity screen against mist-c's existing risk estimates.
It earns no fresh confirmation run or integration. This result closes reuse
of these frozen weights under this protocol, not neural risk learning in general.

The experiment uses only the earlier calibration dataset's 80 TRAIN games:
the first 50 chronologically fit small calibrators and the last 30 provide a
reused-development comparison. Network weights and v35 risk estimates stay
fixed. The older validation and test games are not scored. These are not fresh
held-out generalization results or measurements of playing strength.

| Development metric; lower is better | Calibrated belief risk | Belief plus frozen neural risk |
|---|---:|---:|
| All-candidate log loss | 0.062094 | 0.062184 |
| All-candidate Brier score | 0.018654 | 0.018863 |
| Played-move log loss | 0.029621 | 0.029380 |
| Played-move Brier score | 0.007937 | 0.008051 |
| Within-decision ranking error | 0.026189 | 0.026408 |

The readout covers 1,295 decisions, including 413 with both safe and fatal
candidate moves. One historical played move is absent from the original
candidate collection, leaving 1,294 played-move scores; the omission is
preserved rather than silently changing the candidate set.

The neural coefficient is positive and played-move log loss improves. The
required 2% overall log-loss gain, lower Brier and lower ranking error all
fail. Whole-game bootstrap intervals for fusion minus baseline include zero:
log loss [-0.001969, 0.002253], Brier [-0.000587, 0.001003]. The point estimates
do not justify advancement; they also do not establish statistically reliable
harm. No subgroup replaces the recorded gate and no parameter sweep follows.

Execution completed in 18.87 seconds on CPU core 6, with one inference thread.
No GPU or neural training was used. Core 6 has been released. Experiment 244's
ongoing continuations on cores 0–1 and 4–5 are independent and unchanged.

`audit.json` verifies all 106,671 candidate labels across 80 games against the
original TRAIN data, exact parity on 3,345 preflight predictions, independent
scalar recomputation of the reported metrics, and exhaustive pairwise ranking
checks on all 413 mixed-label development decisions. The audit passes.

The plan was published before execution in commit
`bc10a15f56155f8dd2d8ecbb46e55996862b31de`; its SHA256 is
`947fdbb906d17ec9f904063b2a93365e82a55f60e3e9b1a280fed4e61d8b0f52`.
Source, model, input and output hashes are retained in `plan.json`,
`collection.json`, `report.json`, and the recovery receipt in
`../neural-risk-recovery-20261102/`.

No model, belief weights, guard thresholds, engine source, ZIP or arena
activation changes follow this result.
