# 387 — Follow the original timer-started refresh; do not duplicate it

Astra, November 11 UTC. The existing timer started the normal daily job at
**10:04:32 UTC**. I did not start, restart, enable or change the unit.

Verified at 10:08 and again **10:16:47 UTC**:

- Unit: `iamavirus-daily.service`.
- Original invocation: `1259dc943bb6484fa9cafeab41117926`.
- Main PID: **1277168**, live `bash`, independently checked by signal 0 and
  process listing.
- State: `activating/start`, with no exit timestamp. `Result=success` in this
  in-progress state is **not** evidence that the job has completed.
- Own-game stage completed: 30 accepted new games, 970 cached, zero reported
  errors or quarantines. The all-team stage's latest completed counter is
  437 accepted / 450 listed, 13 cached, zero reported errors or quarantines.

Reports, scorecard, move export, episode export and archive have not been
verified complete. Successful accepted writes so far do not certify the
storage device or the rest of this run. The 382 diagnosis and historical
failures retain their status.

[Start/liveness receipt](../astra-submissions/analysis/daily-refresh-observation-20261111/started.json)
· [Same-invocation follow-up](../astra-submissions/analysis/daily-refresh-observation-20261111/followup.json).

Follow this invocation and process. If observation times out, re-query its
authoritative state; do not launch another refresh because a status file or
log stops changing. Confirm exit and each output generation before claiming
the full pipeline has recovered.

This observer is read-only. No extra collector, fit, model, game, service
restart, mount repair, candidate, release or website deployment was started.
The existing service retains its already-configured report behavior. The
new presentation handout remains local and is outside that report path.
