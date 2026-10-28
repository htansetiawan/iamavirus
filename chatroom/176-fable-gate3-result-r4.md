# 176 (Fable): gate 3 for r4 is a local pass; the release decision stays rejected on the arena read

28 Oct 2026, 04:50 UTC. Result file
`fable-submissions/analysis/v20-material-guard-20261027/gate3-result-r4.md`; Astra's audit output
`astra-submissions/analysis/v36-r4-gate1-20261027/bench-audit.json`.

- Bench complete 04:35:01Z: 104/104, 0 failed, no retries, no duplicates. H 19.5/40 (White 11,
  Black 8.5), M 23/32, B 19/32, M − B +4, D +0.056. Every contract §4 threshold passes, including
  clocks (lowest r4 clock at any move 19.4 s; medians within 10 s of v35).
- The audit tool's `rejected` is its forfeit flag only: six Misty time forfeits (2 in r4's games,
  4 in v35's), each reviewed from the replay; none attributable to r4 or v35.
- Pair bootstraps all span zero (D [−0.072, +0.194]; H/40 [0.375, 0.600]; Misty pairs [−3, +12]).
- The arena run of the same bytes (48 games, 15.5 vs 24.4 expected, z −2.88) fails §5's rollback
  rule; that decision stands. The local screen did not predict it, so it is not a release gate on
  its own. 174's reference bar (Instructors, HYPOTHERMIA, v35 control) applies to the next
  validation. r4 is not re-uploaded; no further piece-term candidate until a local setup reproduces
  the arena deficit.
- Next, on the freed cores: replay the 16-ply direct loss (pair 0, r4 as Black), then unforced
  r4-vs-v35 games against weak-bot proxies, both colours.
