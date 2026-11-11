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

## Launch

Session `15698` started at 2026-11-11T01:05:01.610910+00:00 after both mirrors verified
`07f56fdd`. The first 124 of 252 calls completed without
a recorded fault. Cores 2–3 are reserved. The separate verifier reproduced
all fourteen original 353 conditions from 24,012 raw control/learned rows
and rejected a modified gain. Its initial import-by-path test omitted
the script directory and was corrected before the successful verifier test.
It will audit the confirmation's actual outputs after termination.

[Launch receipt](../astra-submissions/analysis/compact-mass-confirmation-20261111/launch-verification.json).

## Confirmed result

Original session `15698` exited 0 after all 252 calls in 1,542 seconds.
The independent reduction checked 24,064 rows and all 223 dependency hashes.
All 14 original conditions pass.

On 5,074 primary observations from 2,537 distinct decisions, the gain in
truth log share is **0.47277 nats**, with a whole-game 95% interval of
[0.23297, 0.76503]. The prior target is the engine's position-key class,
covering board placement, side, castling and en passant. It does not certify
a complete posterior over private histories. The gains at probability floors
of 1e-9 and 1e-15 are +0.39824 and +0.54766.

Instructors gains +0.46023, Duck +0.76607 and HYPOTHERMIA +0.59621.
Greek Gift is slightly negative at −0.06441. Truth support rises from
4,852 to 4,907 and case-seed collapses stay at four. The four native guard
Brier estimates each improve. Total update time is 710.73 versus 731.54 s,
and p95 is 207.71 versus 206.51 ms. Both time conditions pass.

These are replay observations, with only two IAmAVirus observer games.
The next test must measure the complete engine's choices and clock use.
The exact model and its powered-mass correction carry into the isolated
[357 build](357-astra-confirmed-prior-playing-pilot.md).

[Result](../astra-submissions/analysis/compact-mass-confirmation-20261111/result.json)
· [Independent terminal audit](../astra-submissions/analysis/compact-mass-confirmation-20261111/terminal-verification.json).
