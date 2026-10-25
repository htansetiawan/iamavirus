# Astra 145 — Persistent search-target collection: 2.70× in a bounded pilot

Implemented a reusable offline teacher stream in an isolated copy of v35.
The controller sends an observation and clock, receives the teacher's complete
proposal/targets, and only then commits the recorded own move. This prevents
future replay actions from being available to the queried teacher and lets the
same reconstructed belief continue through multiple queried decisions.

Two games, three queries each, both colors, fixed 0.2-second search budgets:
fresh processes took **18.562 s**, persistent processes **6.868 s** (2.70×).
All six match on actor-history hashes, belief fingerprints/counts, sampled
worlds/weights, root moves and exclusions. Searches leave the belief fingerprint
unchanged. Replay-only post-own clock accounting is normalized identically in
both modes; arena behavior is untouched.

Three selected moves differ: timed search and warm caches are not deterministic.
This proves neither identical teacher labels nor stronger play. Two selected
games are not a corpus-wide speed benchmark. The earlier teacher safety gate
remains failed; no bulk distillation, training or new tournament was launched.

The collector is now available for the reviewed learning loop, so we need not
pay full startup/prefix cost for every label. Keep multiple positions from the
same game in one split and record query order/cache lifecycle in provenance.

[Code, transcripts, targets, input checks and timings](../astra-submissions/analysis/deeprl-table-audit-20261025/persistent-teacher-report.md)
