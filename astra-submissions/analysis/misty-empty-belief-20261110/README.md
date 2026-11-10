# Empty Misty belief: cap-dependent failure reproduced

Original component runner 87639 completes; no new games are played. Both
cases use White's own 24 observations and past own moves from the stopped
comparison, seed 2802007, with historical searches skipped. No true board,
opponent view or hidden move appears in the actor's redacted input.

| Belief cap | Outcome | Maximum states | Peak RSS | Total time |
|---|---|---:|---:|---:|
| 200,000 | Same empty-P exception after own Qa4, ply 23 | 200,000 | 127 MiB | 1.12 s |
| None | All 24 observations processed; six states remain | 447,682 | 153 MiB | 1.27 s |

The independent audit checks every redacted frame/own action against the
course referee, source/output hashes and both diagnostic outcomes. No case
times out; recorded process cleanup is verified. This supports loss of
consistent support under the cap in this component. It is not an exact live
set/search/carryover reproduction or a promise of reliable uncapped full games.
The 4 GiB address-space limit is a diagnostic bound, not the arena RSS limit.

The initial two-game health test established that the bounded configuration
worked on those seeds. The subsequent failure stops its use for another
automatic strength panel. The failed guard candidate is not promoted, and
the opponent-exit win is excluded from clean paired strength evidence.

No installed package was modified, and no fourth match batch starts. A
history-preserving recovery needs separate design/qualification; raising or
removing the cap is not established as a full-game solution by this trace.
The upstream project already documents cap-related true-board loss.
[Upstream limitation](https://github.com/brianhliou/misty).

See [audit.json](audit.json), [plan.json](plan.json) and the two event traces.
