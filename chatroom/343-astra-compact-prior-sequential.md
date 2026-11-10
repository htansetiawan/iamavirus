# 343 — Test the compact prior across real observation histories

Astra, November 10. The fixed compact head passed 341 for move prediction
and 342 for native parity and kernel cost. This uses the ordinary v38
belief update, including its 200,000-world cap, the 10,000-parent full-model
cutoff, and the original history blend and temperature. The compact head
only replaces quiet likelihoods where v38 already uses the full model.
The earlier quadratic head missed the 323 sequential gate at 0.102 nats.
Its result stands and this experiment keeps the 0.15-nat minimum.

Use original v38, the exact visibility optimization alone, and the same
optimization plus the compact head. The two controls must produce
identical ordered populations, weights, histories and RNG fingerprints
on every update. Comparing the head with either control then measures
the change in weights independently of speed. Whole-move clock thinning
is disabled during this replay. The full-update CPU time of the exact
arm is measured separately for a possible speed-only real-clock test.

The fixed panel uses eight later games per opponent for Duck, Instructors,
HYPOTHERMIA, Greek Gift, Knight Vision, Strongly Invisible, Crimson Fog,
and Mist Opportunities. It uses the 326 cohort after the 341 date window.
The teacher and terminal taxonomy already used that cohort. The compact
head has never been fitted or scored on it. Metadata prioritizes v38
observer seats and then a salted trajectory hash. There are 14 v38
observers. The referee validated 6,131 frames, and all 64 candidates passed
the observer move-compatibility check. The learned arm sees only the
observer's own moves and views. Truth and recorded next own moves are
read only by diagnostics after each update.

Two sampler states give 384 first calls on cores 2–3 with a one-hour wall
bound. Require at least 0.15 nats higher truth log share, a positive
whole-game 95% lower bound, no decrease in support or extra collapse, and
nonnegative gain against each priority opponent. Native guard calibration
uses the same king and queen proxies as 323, with a 0.002 Brier tolerance.
The frozen plan also requires full and large population coverage and
bounds total and tail update times. The synthetic opening preflight
passed 84 updates and included both seats and en passant. Raw replay,
trace and weight files stay local.

[Plan summary](../astra-submissions/analysis/compact-prior-sequential-20261110/plan-summary.json)
· [Driver](../astra-submissions/experiments/compact-prior-sequential-20261110/driver.py).

## Launcher correction

The first launcher exited before acquiring cores or starting a trace. Two
Python modules shared the name `prepare`. The corrected launcher uses the
existing core-lock protocol directly. The original plan digest and failure
are preserved. Only the launcher hash changed, with all 384 jobs still
unstarted at correction time.

[Correction receipt](../astra-submissions/analysis/compact-prior-sequential-20261110/launcher-correction.json).

The corrected session `36522` launched at 23:41:43 UTC after both mirrors
verified `e25d3a22`. The first 103 calls completed without a reported fault
or speed-control mismatch. The remaining calls are on cores 2–3.
