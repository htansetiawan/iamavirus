# 355 — Confirm the powered-mass prior on later games

Astra, November 11. The [353 development comparison](353-astra-powered-observation-mass.md)
passed its unchanged posterior and guard gates, including the Instructors
condition that failed in 343. This confirmation fixes the original v38 trace
binary and the exact 353 learned trace binary. It uses no new fit or threshold
change. The 349 cohort was sealed independently before any 353 scores.

Select each trajectory at most once, by opponent and observer color.
A deterministic matching fills four per color where available. It sorts
eligible choices by our observer seats first, then by a fixed hash of the
move sequence. The course referee and existing v38 view-only move gate check
all selected prefixes. The sole unavailable Instructors seat uses
`d5e6` en passant on ply 49. The replay is legal under the referee and
omitted by the native view-only gate. This is a fresh instance of the
coverage issue documented in [122](122-astra-ep-visibility-inference.md).
The resulting panel has seven Instructors games and eight in each other
stratum, 63 unique trajectories, 6,142 frames and two IAmAVirus observers.

Run both frozen binaries on each of two fresh sampler states, alternating
which arm runs first. All 252 calls contribute to paired timing. Reuse
the 353 thresholds for overall gain, game-bootstrap interval, support,
collapse, large-update coverage, priority opponents, guard Brier scores
and runtime. The trace replays only the observer's own actions and views
as engine inputs. Replay truth is used for verification and labels.
This is a test of belief quality at fixed update settings. A pass earns
a full-clock integration design. The own-observer count is too small
to infer how the learned prior changes v38's actions or results.

[Implementation](../astra-submissions/experiments/compact-mass-confirmation-20261111/confirm.py)
· [Frozen plan](../astra-submissions/analysis/compact-mass-confirmation-20261111/plan-summary.json).
