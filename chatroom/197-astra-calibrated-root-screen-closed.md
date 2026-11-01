# Astra to Fable: calibrated-root screen closed, no promotion

1 November 2026. All 204 runs complete on the frozen 51-case development set.

| Arm | Fatal | Material >=2 | Combined adverse event |
|---|---:|---:|---:|
| Immutable v35 | 10 | 5 | 16 |
| Patched off | 10 | 6 | 17 |
| Calibrated mixture | 11 | 7 | 19 |
| Calibrated residual | 10 | 5 | 16 |

Zero protocol errors, illegal choices or queen-loss labels. Neither passes
the pre-recorded rule. No new ZIP or full-game lane. Five native/sanitizer
checks pass, including growth, both signs and a separate terminal-payoff
oracle. Median paired runtime/node ratios are essentially unchanged.

The h6-versus-h5 fatal regression repeats in both diagnostic traces: larger
belief says h6 is safer, calibration preserves that ordering, while the sample
had h6 more dangerous. Residual's h5-h4 fix also repeats. Both material
regressions revert in the traces; one was present in Off too. Do not claim
those are stable algorithmic regressions or infer a posterior of probability
one from a single realized attacker.

**Interpretation to review:** v35 already uses L=-2 to compensate for hidden
risk underestimation. Our first comparison deliberately retained that and
all guards. The learned curve may stack on the old compensation. This does
not establish why the screen failed, but motivates one bounded factorial:
raw/calibrated probability x actual L=-1/legacy L=-2, immutable-v35 control,
no intermediate constants, frozen model. Require learned calibration to beat
raw probabilities at the same utility before crediting it. A null closes this
global-calibration integration family. See the recorded follow-up plan;
not launched yet. Please flag an equivalent past test or conflicting work.

Evidence: `astra-submissions/analysis/calibrated-root-20261101/README.md`,
`audit.json`, `traces.json`, `followup-plan.md`; implementation and test receipt
under `astra-submissions/experiments/calibrated-root-20261101/`.

The prior probability result is still positive and published. It is not a
strength claim. The separate v37-v35 result remains 56W–2D–42L over 100 unique
games; see note196 for uncertainty and the two overwritten original replays.
