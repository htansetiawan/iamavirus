# Local field snapshot: collection and independent review complete

This is an independent local cache after the shared external archive became
unavailable. Website publishing remains disabled at Henry's request. No
model, candidate, training split or arena submission is changed.

## What is verified

The [listing audit](listing-review.json) checks all 60 saved public pages,
their fixed-cursor query chain and their exact concatenation into **6,000
unique completed-game IDs**. Timestamp order is checked at nanosecond
precision. Selection covers every team and outcome within the newest-first
limit, rather than filtering for interesting losses.

The window runs from **November 9, 10:57 a.m. to November 10, 8:51 p.m.
Boston time**, about 33.90 hours. Exact UTC timestamps are retained in JSON.
The cohort is a recent window, not the full archive or a balanced schedule.

IAmAVirus v38 played **345** of these games: **184W–17D–144L**, 55.8% score,
with 173 White and 172 Black seats. Selected opponent-version results:

| Opponent | Played version | W–D–L | White / Black seats |
| --- | --- | --- | --- |
| Instructors | 4 | 8–1–7 | 8 / 8 |
| HYPOTHERMIA | 4 | 6–0–6 | 6 / 6 |
| HYPOTHERMIA | 10 | 5–0–3 | 4 / 4 |
| duck | 11 | 2–4–12 | 9 / 9 |
| Greek Gift | 25 | 1–0–11 | 6 / 6 |
| Mist Opportunities | 2 | 10–1–3 | 7 / 7 |

These small descriptive cells do not establish an Elo change or identify a
cause. In particular, the two HYPOTHERMIA versions should not be treated as
one unchanged opponent. The recorded leaderboard fetch is a separate
snapshot at November 10, 8:51 p.m. Boston, not a continuously current rating.

## Completed collection and independent replay review

Original collector **32307** exited 0 at 03:52 UTC after accepting all
**6,000 replays / 459,622 frames**, with zero quarantines. It reports
**5,872 distinct complete move sequences**. Its C++ pass and the independent
second pass remain separate instruments. Original waiter **7861** then ran
the prepared review once and recorded child exit **0**. The independent
review finished at **04:15:15 UTC**, after **1,363.37 seconds** (22 minutes
43 seconds), within its original 30-minute bound. Its core-6 lease is
released. The prepared timeout continuation was not needed or launched.

The completed [transport review](transport-review.json) reconciles all
**5,808 HTTP attempts** with saved fetch metadata, below the 6,500 bound.
5,598 replays came from the public API and 402 from the planned caches;
every cached source hash matches its original file. Saved JSON totals about
163 MiB. Original HTTP response bytes are not independently retained, and
the audit does not claim to rehash them or verify request-start timestamps.

The [review plan](review-plan.json) pins the listing, old reconstructed cache,
independent C++ validator, course referee and audit source. Its two-game
preflight verifies **143 frames** with both rules implementations. The full
review required the original collector to complete all 6,000 accepted
replays with zero quarantines. It used core 6 with a 30-minute cap and
verified:

- Saved-byte hashes, accepted/validation journals and played metadata.
- Every true board and both recorded private views under C++ and course rules.
- Clock schema, with timing anomalies reported separately rather than repaired.
- Whole-move-sequence duplicates and overlap with the old 336 cache's splits.

All **459,622 frames** passed the independent course-referee walk and the
pinned C++ validator. Both private views, true boards, moves and normal
termination results were checked; technical terminations were classified
separately. No negative clock values, nonmoving-clock changes or inferred
elapsed times below −2 ms were flagged. This does not independently measure
how long the arena actually ran each move.

The [final reconciliation](closure-review.json) rehashes every saved replay,
all pinned review dependencies and the final journal, then recomputes its
counts. The original result and scope are preserved in
[review-result.json](review-result.json).

## Duplicates and prior-data overlap

The 6,000 distinct game IDs contain **128 extra IDs sharing complete move
sequences**, leaving 5,872 unique trajectories. Against the specific old
336 reconstructed cache, which holds one representative game per sequence:

| Prior split | Unique complete sequences also in this snapshot | Current game IDs with those sequences |
| --- | --- | --- |
| Train | 107 | 221 |
| Validation | 7 | 12 |
| Test | 474 | 474 |

The original review field `game_ids_overlapping_old_336_split` counts current
IDs whose **sequence** matches; it is not an exact game-ID join. A separate
exact-ID join finds 471 IDs matching that cache's representative IDs, all
in its test split. Since the old cache deduplicates trajectories, that is
not a complete count of overlapping original source IDs.

The remaining **5,284 sequences** are absent from that one cache. This does
not establish an untouched holdout: shared prefixes, other experiments and
the planned reuse of 402 cached replays are not excluded by this audit.

No training split is assigned. Even a valid replay can overlap old training
or tests, and valid moves are not necessarily good moves. The snapshot does
not restore the shared daily pipeline or certify an untouched holdout.

Eight additional [review-contract checks](review-contract-checks.json) pass
on in-memory copies of one source game: valid replay acceptance, corrupted
board/view/move rejection, non-finite clock rejection, wrong played-version
rejection, mutable-current-version tolerance and descriptive timing-anomaly
reporting. No stored replay or frozen review condition changed.

[Listing audit source](../../tools/audit_field_listing.py)
· [Full-review source](../../tools/verify_field_replays.py)
· [Preflight](review-preflight.json)
· [Original collection plan](plan.json).
