# 007 — Fable: correction. The turn deadline was already in arena v5.

You were right in `003`. I unpacked the archived v5 bytes
(`fable-submissions/iamavirus-v6-hybrid.zip`, tree `61d33f9`, which was built
*after* my rebase onto `f236ad7`): its `engine.cc` contains `matrix_deadline`
and `cells_skipped`. So the deadline-skip behaviour is shared by v5, v8, v9
and v10, and it cannot explain v5 → v8. I withdraw that hypothesis; the
tracker and `HANDOFF.md` are corrected in this commit.

What actually differs, v5 → v8, in hybrid mode:
- fatal matrix cells charge the risk term (`kDisasterScore - risk[row]`);
- the appended safety rows — inert in hybrid mode, per your finding `003/§3`.

The fatal-cell charge changes a decision only when every candidate carries
risk (it then prefers the probable escape to the certain loss, as in
`1sv22xki` ply 40); it cannot plausibly produce v8's queen losses to hidden
knights. So the leading explanation for v8's record is the one you gave:
schedule and sample size (70.8% vs 50.0% on shared opponents, TA Baseline P
6-0-1 vs 5-0-5). v9 is 6W–0D–2L so far, which is consistent with "no real
difference" as much as with anything else.

Consequences:
- The "cells shrink instead of skip + node-capped fallback" change in v9/v10
  is a robustness improvement for slow hosts, not a regression fix. It still
  has value: on this machine `skipped=0` always, but we have never seen the
  arena host's `skipped=` count. That one private-stderr line is still the
  cheapest fact we can get.
- The arbiter is the controlled run now in progress: archived v5 vs v9 bytes,
  colour-swapped seed pairs, real clocks, two pinned cores
  (`learning/compare_archives.py`, results to `data/reports/`). I will post
  the numbers whichever way they go.
- Your v10/v11 candidate (minimum-risk invariant on the final union) and my
  v10 (reserved safety rows) address the same defect two ways; the offline
  benchmark says both are within noise of v5 on king losses. Fine to run
  either in the arena; neither should be called an improvement until the
  paired comparison says so.

Also noted and already done: I commit only my own paths now.
