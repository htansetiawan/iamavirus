# Astra: the rank swing is real; HYPOTHERMIA changed strength

29 October 2026. Public API snapshot: 15:33 UTC / 08:33 Pacific.

Henry saw IAmAVirus reach #6 and return to #9 and asks whether scheduling
slowness explains it. The data supports a real temporary rating peak and
subsequent losses, not an established server-delay problem.

## Our unchanged v35 rose and fell

The last-200 per-game rating list, aligned to completed games, puts our peak
at **1991.96 on October 29 at 02:28:08 UTC** (October 28, 19:28 Pacific).
The current snapshot is **1904.76, rank 9, v35 active**. All 200 aligned
games used v35. A reconstruction from the sampled histories puts us sixth
at the peak, consistent with Henry's observation. Those samples are not a
synchronized historical leaderboard, so the exact displayed rank is not
independently certified by that reconstruction.

After the peak: **92 wins, 6 draws, 89 losses in 187 games**, 95 points versus
105.90 Elo-expected points, net **−87.20 Elo**. This is why a raw score slightly
above 50% can still lose rating: the opponents' ratings implied a higher score.

| Opponent after our peak | Our W-D-L | Our rating change |
| --- | --- | ---: |
| Gravel Road | 5-0-7 | −23.88 |
| HYPOTHERMIA | 7-1-4 | −18.70 |
| Instructors | 6-1-13 | −17.94 |
| Mist Opportunities | 5-0-11 | −13.88 |
| duck | 4-1-9 | −10.49 |

These are aligned live rating increments, not sums estimated from today's
opponent ratings. Other matchups account for the remaining positive and
negative changes. Even 7 wins and a draw against HYPOTHERMIA lost points
because its rating had already fallen sharply.

Rivals also moved: at our peak Instructors was 1943.26 and duck 1933.45;
now they are 2031.80 and 1970.02. Their versions remained v4 and v6. A short
peak is therefore not evidence that we established sustained top-six strength.

## HYPOTHERMIA is no longer the same benchmark

The team submitted v5 at October 28 12:38 UTC and v6 at 13:43 UTC. At our
October 28 02:09 snapshot it was v4, about 1946 Elo. Now it is **v6, 1629 Elo,
rank 16**. v4 finished 467-52-399 (53.7% score); v6 is 166-24-264 (39.2%).

Matching opponent names **and opponent versions**, requiring at least five
v4 games per matched opponent/version, covers 372 v6 games. v6 scored
**123/372 (33.1%)**, versus **242.86/372 (65.3%)** expected from v4's historical
records against those same opponent versions. This is observational and does
not control colors, every environment change or sampling uncertainty, but the
gap is large and persists after matching the schedule. It strongly suggests
a version regression. There is only one time-forfeit termination across all
454 v6 games; 429 ended by king capture.

Important for the next candidate: Henry's HYPOTHERMIA reference was the v4
opponent near 1946, not this much weaker v6. Beating the team name now must
not silently lower the strength bar. Retain explicit versions in every
comparison and Instructors as an unchanged external reference. Historical
v4 evidence is not a claim that an authentic v4 binary is locally available.

## What we can say about scheduling

K is 8. Results arrive throughout this period, and the rating-history cache
was about 22 seconds old when fetched. The rating drop reconciles to completed
games. Opponent mix, result streaks, completion order and opponents changing
versions can move rankings; Elo already adjusts for opponent ratings, but
those ratings themselves need games to track a new version's strength.
We cannot inspect the server's queue or rule out every display delay, so
there is no supported diagnosis of a slow scheduling engine here.

Evidence: [summary and per-opponent changes](../astra-submissions/analysis/rank-swing-20261029/summary.json),
[compressed API and alignment evidence](../astra-submissions/analysis/rank-swing-20261029/evidence.json.gz).
Sources: [leaderboard](https://6s890.lids.mit.edu/api/leaderboard),
[Elo history](https://6s890.lids.mit.edu/api/leaderboard/history),
[HYPOTHERMIA versions](https://6s890.lids.mit.edu/api/leaderboard/e2f593ca1fea4710b07a8120dd6b3477/versions).

Alignment method: offset the newest completed-game list by its total count
minus the frozen leaderboard's team game count, then pair the previous 200
games with the leaderboard's last 200 ratings. All outcome/delta sign checks
and per-game absolute-delta checks against K=8 passed for IAmAVirus,
Instructors, duck, Mist Opportunities and HYPOTHERMIA. The first aligned
rating has no previous increment. Public lifetime history is reconstructed
and sampled; it is used only for the approximate rank reconstruction and
longer trend, not substituted for those live per-game increments.
