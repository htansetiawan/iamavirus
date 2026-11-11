# Thirty newly cached v38 games: descriptive monitoring

Reviewed 2,557 frames in all 30 games accepted by the original daily refresh's completed own-team stage. The fixed journal suffix and fetch times identify this cohort independently of the results.

The games completed November 11, 05:47–09:47 UTC. All use arena version 38. Their **20 wins, 0 draws and 10 losses** are a scheduling-dependent sample; they do not establish an Elo gain or improvement over v37/v35. All 30 terminations are normal, with no reported negative-clock, nonmoving-clock-change or impossible-elapsed-time flags.

| Opponent | Played version | Wins | Draws | Losses |
| --- | ---: | ---: | ---: | ---: |
| Czechmate | 3 | 2 | 0 | 0 |
| Decent Chess Bot | 7 | 3 | 0 | 1 |
| Farsight | 29 | 1 | 0 | 1 |
| Gravel Road | 5 | 0 | 0 | 2 |
| Greek Gift | 25 | 1 | 0 | 1 |
| HYPOTHERMIA | 10 | 2 | 0 | 0 |
| Knight Vision | 36 | 2 | 0 | 4 |
| RATIRL | 2 | 4 | 0 | 0 |
| TA Baseline P | 5 | 2 | 0 | 0 |
| TUM | 8 | 1 | 0 | 1 |
| Trojan Horse | 5 | 2 | 0 | 0 |

There are **no Duck or Instructors games** here. HYPOTHERMIA v10 is 2–0, Greek Gift v25 is 1–1 and Knight Vision v36 is 2–4. These small cells describe these games only.

## What still deserves attention

Using the unchanged diagnostic from 373—material at least three points down for five consecutive recorded frames—9/10 losses qualify, compared with 1/20 wins. Loss onsets occur at median ply 47, a median 23 plies before the end. Eight of those nine loss onsets are captures from an origin hidden in our observation before the preceding own choice; six take the piece on our preceding UCI destination.

At the final losing move, three kings move into a new attack, three move while already attacked, three nonking moves fail to resolve an attack and one opens an attack. At least one attacker was hidden in the prior decision view in 9/10 losses. This is geometry, not evidence that the posterior omitted the attacker or that a different move would win.

The one win with a sustained deficit never returns to even material before winning. A deficit is therefore not an automatic bad-move label. Nothing here reopens the failed guard or learned-prior configurations.

## Provenance and limits

The selection retains all first 30 records after the unchanged 379 journal prefix (103,619,710 bytes). All actual team IDs match IAmAVirus; each replay fetch falls within the completed 10:04:33–10:05:43 own-team stage. Their cached fetch timestamps are 10:04:39–10:05:22 UTC. The source IDs have no overlap with the earlier frozen 6,000-game field panel, but that does not make these observed outcomes an untouched test set.

The original review ran once and completed in 1.33 seconds. Existing C++ and course-referee validators checked all frames; the existing EP-corrected taxonomy was cross-checked against full move history. A separate reduction reconciled source hashes, all identities/results/cells, material trajectories and onset visibility. Per-game labels and source copies remain under `data/astra-spool/daily-own-cohort-20261111/`.

The full daily refresh is still running separately; this report does not certify its later reports, exports or archive. No extra API collector, model fit, GPU use, bot search, new game, split reassignment, shared-report replacement, package, commit, push or deployment was performed.

[Frozen plan](plan.json) · [Original execution](execution.json) · [Result](result.json) · [Independent reduction](review.json) · [Review source](../../tools/review_daily_own_cohort.py)
