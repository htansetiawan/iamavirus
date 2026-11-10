# 345 — Measure exact speed changes in the whole belief update

Astra, November 10. Compare the original v38 updater, the target-centric
attack query from 344, and that query combined with 342's exact moved-piece
visibility calculation. All three use v38's native likelihood weights.
The compact head is measured separately in 343. This test makes the two
kernel improvements accountable for their actual cost at the ordinary
10,000-parent cutoff and 200,000-world cap.

Use the first and fifth frozen 343 game in each of the eight strata, 16
games and 1,145 updates per arm. Rotate all six run orders and reuse the
deployed sampler state. Require identical populations, weights, RNG,
and native guard outputs. Time the belief update separately from the
read-only guard diagnostics. Full and large populations must each have
at least 100 timed opponent updates. The combined arm must use at most
85% of total update time and 90% at the median paired game, with update
p95 at most 110% of original. The gate uses cores 0–1, separate from
the compact study on 2–3, with a 20-minute bound.

Passing supports a real-clock engine comparison. Fixed replay performs
the same work across arms. A real turn may change the work done by clock
thinning and search, so the replay ratio is a narrower measurement.

[Frozen summary](../astra-submissions/analysis/exact-updater-speed-20261110/plan-summary.json)
· [Runner](../astra-submissions/experiments/exact-updater-speed-20261110/run.py).

## Result

Original session `81422` completed all 48 calls in 68.1 seconds and released
cores 0–1. Every population, weight, RNG fingerprint and guard output
matched over 1,145 updates per arm. Reverse attack alone cost 0.793× v38.
The combined build cost 0.710× overall, 0.386× across 511 full-mode updates
and 0.897× across 64 large-population updates. It was faster in all 16 games.

The panel fell short of the frozen 100 large-update minimum. Its cost and
parity results stand at the measured coverage. A separate panel selected
from prior baseline population counts can answer the large-regime question.

[Result](../astra-submissions/analysis/exact-updater-speed-20261110/result.json)
· [Terminal verification](../astra-submissions/analysis/exact-updater-speed-20261110/terminal-verification.json).
