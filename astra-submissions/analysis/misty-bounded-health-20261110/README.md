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
