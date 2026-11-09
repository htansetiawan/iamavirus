# V38 first 300 games and current checkpoint

Snapshot: 9 November 2026, 3:45 p.m. America/New_York (20:45 UTC).
All 318 v38 listings and all 2,322 v37 listings were fetched with sequential
snapshot cursors. Counts and W–D–L agree with each first page's search summary.
The [analysis script](../../tools/v38_checkpoint.py) records source hashes and
uses played opponent IDs/versions and our color for standardization.

**Retain v38 under the declared trial rule.** First 48: 30W–1D–17L,
63.54%, z=+1.28 against the frozen 54.3% reference. First 300: 170W–10D–120L,
58.33%. Current: 179W–12D–127L, 58.18%; White 107–6–46, Black 72–6–81.
These are operational checks; they do not establish an Elo gain.

The only non-board ending is kfeknzh8, our win against Next. Its public
diagnostics identify Next/Black as the time-limit failure. None of our 127
losses is a recorded technical failure.

| Opponent, played version | V38 W–D–L | Score | V37 expected score on matched colors/version |
|---|---|---:|---:|
| Greek Gift v25 | 0–0–16 | 0.0% | 3.3% |
| duck v11 | 3–1–10 | 25.0% | No matching version |
| Instructors v4 | 9–1–8 | 52.8% | 40.2% |
| HYPOTHERMIA v4 | 11–0–7 | 61.1% | 46.3% |
| Knight Vision v36 | 9–0–7 | 56.3% | 29.9% |
| Mist Opportunities v2 | 6–2–2 | 70.0% | 47.6% |
| Decent Chess Bot v7 | 1–3–8 | 20.8% | 32.3% |
| Strongly Invisible v41 | 4–1–7 | 37.5% | 21.8% |

Across all matching cells, v38 scores 58.26% on 242 games against a v37
reweighted expectation of 52.18%; 76 games are unmatched. For the fixed first
300, 230 match: 58.26% versus 51.81%. Cells are historical and sometimes small;
this adjustment does not remove drift or establish significance. In
particular, duck v11 is new relative to v37's games, so its 25% cannot be called
a v38 regression from a same-version comparison.

## What the priority losses show

All 26 losses against duck and Greek Gift were replayed through the course
referee, checking each move and both observations. The final losing decision
has the following shape:

| Loss group | King moves into attack | Ignores existing attack | Hidden attacker | No immediately safe move on the true board |
|---|---:|---:|---:|---:|
| duck, 10 games | 10 (2 captures) | 0 | 10 | 2 |
| Greek Gift, 16 games | 9 (2 captures) | 7 | 14 | 8 |

None ends within 20 plies. The minimum clock across these games is 17.39s.
This points to hidden tactical danger and earlier position deterioration,
without proving a posterior or solver defect. Eight duck endings have a safe
true-board alternative; half the Greek Gift endings are already immediately
unavoidable. Safe alternatives here use hidden truth and cannot be fed to the
playing policy. The next useful diagnostic is to locate the first critical
decision and separate absent belief support, low weight, guard exclusions and
searched value before choosing a repair.

## Monitoring and data

The previous Fable tracker had no live process at this check; its last written
poll was 8 November 18:29 UTC. Historical 48/300 checkpoints above were
reconstructed from completion order rather than claimed as real-time alerts.
A bounded replacement started at 9 November 20:49 UTC: 24 hours, polls every
20 minutes, public GET only, caches new replays and writes notable results to
the shared ledger. Its original exec handle is 54279. Process liveness and
latest successful poll are verified separately; a state file alone is not
proof it is running. It does not change the active arena version.

Fable subsequently resumed his own tracker (verified live PID602403, start
ticks13525163, command track.sh1 1 1). Astra's temporary watcher was then
stopped deliberately, original exec54279 exit143, to leave one collector.
The [handoff](watch-handoff.json) and [terminal receipt](watch-terminal.json)
preserve that transition. Fable's tracker polls every20minutes and wakes on
technical losses, its rating-floor alarm or its timer; no instant-notification
claim is made.

A fresh shared ingest fetched and accepted 31 replays, 369 cached, zero errors
or quarantines. The earlier replay recovery accepted 8,335 and passed coverage
checks; today's daily job also logged 4,367 newly accepted replays. The daily
log had reached the move-export step; downstream training/report completion
has not been inferred from that. No new model was trained in this review.

Fable found31 duplicate accepted-index rows from the overlapping ingests and
repaired his tally to deduplicate by game ID. Our API checkpoint also counts
unique IDs and agrees with the leaderboard. All318 snapshot replay files are
now present. A shared writer lock/idempotent ingestion is still needed to
prevent recurrence; the daily-report reader already deduplicates, while
RawStore.accepted_replays does not. No training should count repeated IDs as
independent games.

Evidence under [20261109T204526Z](20261109T204526Z/): original pages and fetch
metadata, checkpoint.json, kfeknzh8-diagnostics.json, priority-losses.json.
The [release manifest](../../v38-manifest.json) links the exact package to the
human-authorized trial without changing the failed local test.
