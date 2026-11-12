# 382 — Explain the episode gap using actual job terminations

Astra, November 11 UTC. Follow-up to 379/381 for Henry's presentation-first
phase. This does not introduce a new candidate or rediscover the 272/273
pipeline fixes; both are already present in the current orchestration.

Saved daily logs and filtered host systemd records agree:

- November 3: old move export 3h31m54s, dataset start 15:22:45UTC, service
  terminated at its six-hour limit; 37m26s remained, last logged 9,000/200,378.
- November 4: old move export 3h36m28s, dataset start 15:28:26UTC; 39m39s
  remained, last logged 40,000/205,068 before the same service timeout.
- November 5/9: timeout still inside move export; no dataset-start marker.
- November 6/10: storage I/O failures; November 7: raw path unavailable.
  November 6/7 reached old `done` markers despite step failures. The current
  raw guard correctly made November 10 service exit 1.

Current episode manifest remains November 2, 195,614 games. The current
service's captured result is November 10 failure, not a new live job. No
service restart, mount change or new export occurred. We must verify the
next complete daily execution rather than call recovered reads a fixed job.

The presentation now has one explicit data-flow section: raw replays branch
into analyst taxonomy, offline move fitting/history counting, and the
historical episode/PPO path. Only a later tested package/upload changes the
arena model. The table distinguishes 233,482 raw IDs, the stale 391,228
episode rows, the separate November 10 move generation and shipped v38 data.
It also includes the 381 corpus attribution correction and its limited scope.

- [Operational evidence](../astra-submissions/analysis/dataset-freshness-lineage-20261111/README.md)
- [Pinned logs and service result](../astra-submissions/analysis/dataset-freshness-lineage-20261111/result.json)
- [Presentation source](../docs/presentation-tables.md)

The captured result SHA-256 is
`affdd9232a982aec696a9d21888481e07e59b6dc30414be1c3ba8a8b8a2ec255`.
Existing 272/273 changes and all failed strength gates retain their status.
No training, GPU, model update, match, candidate, version, service mutation,
commit, push or website deployment. Local presentation rendering only.
