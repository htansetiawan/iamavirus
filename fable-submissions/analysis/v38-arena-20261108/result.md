# v38 arena trial: the 300-game reading

v38 = ZIP ba6610f299c1 (v37 plus Astra's all-child Stockfish scorer),
uploaded by Henry, first game 8 Nov 16:53Z. Rule fixed in note 267 before
upload. Reading taken 9 Nov 20:48Z.

## Result: keep v38

- 318 games, 179-12-127, score 0.582. Same count and record as the
  leaderboard's `activeRecord`.
- No time forfeit, crash or illegal move. Every loss ended on the board.
- Rule at 300 games: keep v38 if its score is at least 0.543. 0.582 passes
  (z +1.38 against 0.543).
- Rating 1915, rank 10 (v37 ended near 1920, rank 11).

## Counting correction

`data/raw/accepted.jsonl` holds 31 duplicate rows, all v38 games, written when
two ingests overlapped. The first count (348 games, 0.578) included them. The
tally now skips repeated ids. With duplicates removed, v37's own record is
2,322 games, 1219-65-1038, 0.539. The rule kept 0.543, the stricter figure.

## Against the same opponents as v37

v37's per-opponent scores (opponents with at least 5 v37 games), weighted by
how often v38 met each opponent:

| Stretch | Games (comparable) | v38 | v37, same opponents | Difference |
|---|---|---|---|---|
| Games 1-127, to the rating peak | 127 (123) | 0.663 | 0.540 | +0.122 (2.7 SD) |
| Games 128-318, since the peak | 191 (171) | 0.518 | 0.517 | +0.000 |
| All | 318 (294) | 0.578 | 0.527 | +0.051 (1.8 SD) |

The rating rose from about 1920 to 2006 (9 Nov 03:18Z, game 127), then fell
back to 1915. All of the gain over v37 came in the first 127 games; since then
v38 has scored exactly what v37 scored against the same teams. The overall
+0.05 is suggestive, not proven.

| Opponents | v38 | v37 |
|---|---|---|
| Top six (Greek Gift, Strongly Invisible, Knight Vision, duck, Crimson Fog, Decent Chess Bot) | 21-5-52, 0.301 | 144-20-468, 0.244 |
| Everyone else | 158-7-75, 0.673 | 1075-45-570, 0.649 |
| Greek Gift alone | 0-0-16 | 3-0-87 |

By colour: White 107-6-46 (0.692), Black 72-6-81 (0.472). v37: White 0.585,
Black 0.493.

## Where this leaves the target

Third place is Knight Vision at 2104, about 190 points above us. The top six
sit at 2074-2352; v38 scores 0.30 against them. Reaching rank 3 needs roughly
0.5 against that group.

Tracking continues (`track.sh 1 1 1`): wake on any technical loss, a rating
below 1850, or daily.

## 620 games (11 Nov 03:27Z)

339-27-254, score 0.569; still no technical losses. Rating 1909, rank 9.

| Stretch | Games | v38 | v37, same opponents | Difference | Top six |
|---|---|---|---|---|---|
| 1-127 | 127 | 0.663 | 0.540 | +0.122 | 0.338 |
| 128-318 | 191 | 0.518 | 0.517 | +0.000 | 0.273 |
| 319-620 | 302 | 0.545 | 0.539 | +0.006 | 0.257 |
| All | 620 | 0.563 | 0.533 | +0.030 (1.4 SD) | 0.280 |

Since game 127, 493 games, v38 has played at v37's level. The early edge
looks like a good run, not a lasting gain. v38 is no worse than v37, so the
keep decision stands; it should not be described as stronger. Against the top
six it is at 0.28 (v37 0.244). Greek Gift 1-0-27.

## Correction (14 Nov, 1,298 games): v38 is stronger where rank is decided

The same-opponent average above was dominated by games against weaker teams,
where v38 and v37 score alike. Split by opponent strength (current ratings):

| Opponents | v37 | v38 |
|---|---|---|
| Rated 2000+ | 0.27 (418 games) | 0.34 (198 games) |
| Rated 1850-2000 | 0.40 (784 games) | 0.45 (458 games) |
| Rated below 1850 | 0.74 (1,120 games) | 0.75 (642 games) |

Head-to-head, v37 then v38: Mist Opportunities 0.48 then 0.71; Knight Vision
0.30 then 0.48; Crimson Fog 0.18 then 0.36; Cranberry Lemon 0.43 then 0.59;
HYPOTHERMIA 0.46 then 0.56; Instructors 0.40 then 0.43. Lower against duck
(0.35 then 0.27) and Farsight (0.43 then 0.39).

Standing, from the arena's rating history sampled every 15 minutes:

| | v37 (1-8 Nov) | v38 (8-14 Nov) |
|---|---|---|
| Time above Instructors | 14% | 82% |
| Time above Mist Opportunities | 5% | 82% |
| Median rank | 11 | 9 |
| Our average rating | 1917 | 1927 |
| Average gap to Knight Vision | -206 | -141 |

Our own rating rose about 10 points on average while the teams around and
above us fell about 60, partly from losing more often to v38. Opponents also
changed versions over the period. Reading for the report: v38 searches 38%
more positions in the same time and converts that into better results against
teams at or above our level; against weaker teams it was already near its
ceiling.
