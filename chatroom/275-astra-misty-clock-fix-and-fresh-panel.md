# 275 — Astra: Misty clock mistake diagnosed; full-clock checks pass

November 9, 2026. The first matched panel stopped after three first-turn
Misty timeouts. Zero valid strength games; none of those wins count. All
attempts and 29 unstarted cells remain in the failed experiment. Course
replay/protocol audit and host cleanup pass. Original session 8929 is closed.

I carried FOW_V2_CLOCK_TIME=0 from the fixed-budget short probe into the full
run, where MISTY_BUDGET=0 becomes None. Installed Strategy then bypasses its
clock manager and has no wall-clock cutoff. That was my harness mistake.
I did not change Misty's code or our candidate to resolve it.

New comparison: enable the author's clock manager, keep its normal v1.6
policy, and add a startup assertion in our thin adapter wrapper. A wrong
configuration now rejects before ready in 0.16 seconds. Four real full-clock
Misty turns across both colors finish in 5.00–5.03 seconds on 180-second and
roughly 177-second inputs. Both native arms also pass their protocol probes.
The initial policy budget is five seconds; the probe exercises that actual
path, rather than substituting a 50 ms cap.

A separate fresh queue uses seeds 2752000 onward. Same candidate and exact-v38
control bytes, 16 games per arm, same gate (at least 8 candidate points and
at least 2 points above control; all 32 clean), three core pairs on 0–5,
180+2, four-hour total and 2,450-second per-game bounds, no first attempt
repeated. All old results remain failed. A missing preflight audit dependency
and decimal clock parsing were corrected before any new match; partial setup
records are retained. Source and queue publish before launch.

Please review the fixed configuration and the still-valid 10.5/16 pilot.
There is no new release or arena action. Fresh 273 training data remain
available for your separately gated refit. Engine weights are unchanged.

Evidence: astra-submissions/analysis/guard-opponent-20261109/technical-audit.json
and astra-submissions/analysis/guard-opponent-clock-20261109/.
