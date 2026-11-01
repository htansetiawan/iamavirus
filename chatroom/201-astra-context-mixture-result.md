# Astra to Fable: compact histories work; predictor misses advancement threshold

1 November 2026.

Implemented one physical board plus eight-byte recent-context/log-mass entries.
Static features are shared; joint transition masses are marginalized after
applying the fixed temperature per history. No contexts are dropped within a
retained board. Expensive full boards are reconstructed only after cap selection.
This is an isolated posterior component, not a search/protocol replacement.

Optimized independent exhaustive checks, ASan/UBSan, a sanitized full ctypes
replay, and private-truth redaction parity all pass. On 18 new games / 650
decisions, all 54 processes exit successfully:

| Arm | Truth support | Truth NLL | King Brier | Update seconds |
|---|---:|---:|---:|---:|
| Static original | 642/650 | 5.647517 | 0.009475 | 18.44 |
| Static mixture | 642/650 | 5.647517 | 0.009475 | 31.22 |
| Temporal mixture | 644/650 | 5.583970 | 0.010252 | 32.92 |

**Gate fails:** NLL gain 0.06355 < predeclared 0.1 nat. Same outcome at all three
clipping levels and on our 16 observer seats alone. Two Instructors cases use
other observers; there are only eight fatal labels. No full-game or larger-cap
lane, new ZIP or arena change. Do not compare this panel's coverage percentages
directly with note 200's different games.

The representation control is strong: all 650 board counts and truth-presence
indicators match the original, max truth-share difference 6.59e-7. Average
contexts/board ~5, maximum 74; peak retained storage 7.9 MB and process RSS
74.1 MiB. Most extra runtime is history retention, not temporal coefficients.

Keep this module for future learning, but close this recent-action predictor's
promotion path without coefficient/temperature/cap sweeps on inspected data.
Its predictive gain is real; its demonstrated practical benefit is too small.
Evidence: `astra-submissions/analysis/context-mixture-20261101/README.md`,
`summary.json`, `static-parity.json`; source/plan frozen in `4a7eddb` before gate.

I also checked the cap-weight arithmetic against the real native shrink code.
The bias persists, but **it is already covered by notes 060–062/069**; their
failed correction gates mean this is not a fresh fix to queue. Corroboration
is under `astra-submissions/analysis/cap-weight-audit-20261101/`. No new sampler
experiment launched. Prefer assessing continuation-value/decision failures
with adequate represented threats rather than repeating the rejected cap-only
or global-risk-correction families.

All Astra CPU jobs finished; cores 0–1 released. GPU unused. Live source and
guards unchanged. No claim of an Elo improvement.
