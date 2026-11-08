# Astra: complete the replay recovery before clearing the coverage warning

8 November 2026. V38 stays held after the failed Misty gate. The human review
question is pending; no response or release exception is assumed. No new
playing candidate, fit, search trial or GPU job has started.

Original collector 96269 remains live. Its host PID 40668 and start time
574718 were verified again in namespace pid:[4026531836]. Do not restart it.
The new follow-up is original handle **85349**. It waits for that exact process
to terminate, bounded by the original four-hour limit plus five minutes;
then acquires the same daily-job lock, audits saved coverage and stages reports.
It starts no downloads and publishes no reports itself.

The coverage audit requires a clean cutoff-reaching receipt, the unchanged
collector source, an unbroken saved API cursor/filter sequence, descending
completion order, no duplicate IDs, matching counts, every expected other-team
game in the accepted index, and each corresponding replay's metadata and move
hash. A recent timestamp alone cannot pass. This is content/coverage auditing;
ingestion already validated rules, and the audit does not claim to rerun them.
Our separate watcher and games newer than the historical snapshot stay outside
that completeness claim. Eight adversarial coverage fixtures plus the ten
report-input tests pass; receipt is tests-r2.json.

Cores 4–5 remain reserved through 14:00 UTC for the existing collector and its
closure only. If ingestion stops early, its warning remains and no fresh report
is staged as complete. On success, the follow-up writes coverage-audit.json and
refresh-receipt.json in analysis/report-repair-20261108/closure; inspect these
before publishing, release cores, and check the 03:00 PST daily timer. The
scheduled invocation can skip while our lock is held; exports and archival
must not be described as refreshed merely because taxonomy reports refreshed.

The v38 review and exact ZIP hash remain those in note 264. Your independent
review and concrete hold-versus-experimental recommendation are still welcome.
