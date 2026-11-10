# Runtime qualification of bounded local Misty

This health check has two games against unchanged v38, both colors, with no
candidate and no score condition. The exposed population cap is fixed at
200,000, matching our engine's ceiling. Clock manager remains enabled and
fixed budget unset. The installed package and all strategic profile options
are unchanged. This is a local bounded deployment, not verified arena bytes.

Qualification requires two normal, fault-free 180+2 games; real clock and
population-cap startup assertions; no adapter fallback or stderr warning;
verified off-turn freezing; and logged post-update P no greater than 200,000.
Own and opponent wins, losses and draws all qualify equally. The component
replay already exercised the cap at the problematic endgame prefix. Telemetry
is enabled in this health check to inspect population and phase cost. This
is not a claim that the cap preserves every world or playing strength.

Two reserved lanes use cores 0–1 and 2–3. Each first attempt has a 2,450-second
wall bound; both launch together under a 2,700-second batch allowance. No
started game is repeated. Owned groups are cleaned by the audited helper.
A final independent referee/process audit is required before qualification
is treated as complete. The one-turn full-clock probe passes: legal g8f6 in
5.03 seconds, both startup markers and no remaining child processes.

The final source, queue and 207 pinned dependencies publish before launch.
An explicit non-normal-result rejection was added before any match; the
preflight-only initial plan is retained. No candidate game, new arena version,
GPU work, model update or ingestion is part of this step.
# Completed qualification

Original session 19465 exited 0. Both unchanged-v38 games finished normally
without technical faults, warnings or adapter fallbacks. Independent course
audit checks all **171 frames**, moves, observations, clocks, normal outcomes,
turn-control events, telemetry and source/result hashes. Host cleanup finds
no owned native, Misty or evaluator actor remaining.

| Health game | Plies | Max post-update states | Cap events | Max raw successors | Max update |
|---|---:|---:|---:|---:|---:|
| Native White | 110 | 200,000 | 38 | 4,933,981 | 443 ms |
| Native Black | 59 | 5,061 | 0 | 13,957 | 2.15 ms |

The cap is exercised on a substantial hidden-state expansion. This checks
the bounded deployment's runtime in these two games. It does not promise
that every future game is fault-free or reproduce the current arena team's
settings. Both native wins are incidental: scores were absent from the
qualification gate, and no candidate played.

This deployment now qualifies for the separately frozen candidate/control
panel. See [audit.json](audit.json), [cleanup.json](cleanup.json) and the
per-game replays. No arena or model change follows from qualification alone.
