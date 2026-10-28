# Oracle decomposition: result

28 October 2026. Diagnostic from note 178 (not a candidate). Question: with the search
unchanged, how much is a correct belief worth? The oracle side is the v35 engine with its
belief replaced by the true board on every one of its turns (`MIST_ORACLE_FILE`, mist-c
3b5b255); the control is the same bytes without the flag (both zips sha256 3b6ab5311069).
Referee wrapper `learning/oracle_referee.py` writes the truth next to the replay; the kit is
untouched. 180+2 clocks, cores 2 to 5, seeds 400000 and 401000.

## Score

The runner stopped at 20:22Z after 47 of the 80 planned games when the root disk filled
("No space left on device" while writing the receipt; the cause was not one of our files, see
below). Every recorded game is valid. The remaining 33 games were relaunched from the ledger
at 23:13Z and are folded in at the bottom when done; they cannot change the reading.

| Matchup | Games | W-D-L | Score | White | Black | Pairs (complete) | Reasons |
|---|---|---|---|---|---|---|---|
| oracle vs control | 23 | 23-0-0 | 1.000 | 12/12 | 11/11 | 11, all 2-0 | king capture 23 |
| oracle vs v35 | 24 | 24-0-0 | 1.000 | 12/12 | 12/12 | 12, all 2-0 | king capture 24 |

Uncertainty. The pair bootstrap is degenerate at [1.00, 1.00] because every pair is a sweep.
Exact one-sided 95% lower bounds: game level 0.878 (23/23) and 0.883 (24/24); pair-sweep
probability 0.76 (11 pairs) and 0.78 (12 pairs). Both thresholds of the reading rule sit
below every bound.

Clocks and length. No forfeit on either side. End clocks (s): oracle min 28.9 / median 61.3
against control (control 20.3 / 49.4); oracle 43.4 / 64.4 against v35 (v35 41.4 / 60.8). The
oracle side spends less time because a one-world belief has nothing to sample. Win lengths:
26 to 113 plies against control (median 58), 19 to 81 against v35 (median 56). Shortest win
19 plies (`builds/oracle-vs-v35-p3-a-white.json` family; see readout.json for the list).

## Oracle-applied check

From each replay's private diagnostics (`readout.py`): every oracle-side decision ran with
|P| = 1 and "truth in P" (47 of 47 games), zero "belief kept" failures, zero "truth placed"
fallbacks, zero oracle lines on the control or v35 side. Eleven control-game and ten
v35-game stderr excerpts hit the 16384-character cap, so the check covers the first part of
those games only; the smoke games (note 178) were complete and clean.

## Reading under the 170 rule

Rule: oracle vs control at or above 0.85 means the belief is the bottleneck (belief route);
at or below 0.65 the search is (search route); between, both. Observed 1.00 with a lower
bound of 0.88: **belief route**. The same search on a correct belief beats the identical
engine and v35 in every game, as White and as Black.

Against the 80% bar (note 177): oracle vs v35 is the ceiling of a perfect belief with this
search, and it is 1.00 (lower bound 0.88), above the bar. The search does not have to change
to reach 80%; the belief does. How far along the way a realistic belief gets is the open
number.

## What the oracle does and does not measure

- It collapses the belief to one world, so it bundles two things: the truth is in the
  belief (coverage) and it carries all the weight (sharpness). Our blunder audit
  (`docs/top3-reanalysis-20261027.md`: the truth was in the belief in 68 of 71 blunders at a
  median share of 0.06%) says coverage is already mostly there and sharpness is the gap.
- With one world the CFR over worlds degenerates and the full time budget goes to that
  world; the oracle also spends less clock. Part of the gain is search depth bought by
  sharpness, which a real belief also buys as it concentrates.
- It does not say how much sharpness is enough. That is the next measurement.

## Next

1. Sharpness curve (same harness, one day): keep the sampled belief but force the true world
   into P with a fixed share s in {0.05, 0.2, 0.5}, 20 games each vs v35. Gives the share the
   search needs to convert, which is the target for the belief build.
2. First build on the belief route: a learned opponent model for world weights (note 170,
   M4 plus opponent model), measured first by the truth's share at the audited blunder
   decisions, then by the direct matchup under Astra's frozen protocol (177).

## Disk

Root filesystem at 99% (7.7 GB free at 23:10Z, 456 GB total). No file over 100 MB of ours
was written in the window; the replays of this run total 4.1 MB. Whatever filled the last
gigabytes was transient. Nothing was deleted.

## Files

`readout.json` (this read-out), `readout.py`, rows `oracle-vs-control` and `oracle-vs-v35`
in `data/arena_local/games.jsonl`, replays `data/arena_local/builds/oracle-vs-*-white.json`
with `.truth` sidecars, receipt `data/arena_local/receipts/queue-oracle.json` (rewritten by the
relaunch), logs `data/logs/bench-oracle.log` and `bench-oracle-2.log`.
