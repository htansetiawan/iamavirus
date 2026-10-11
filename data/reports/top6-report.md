# Against the top six

Updated 2026-10-11 00:19 UTC; leaderboard fetched 2026-10-11T00:15. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2114 | +436 |
| Knight Vision | 2052 | +374 |
| Decent Chess Bot | 2056 | +378 |
| Strongly Invisible | 2044 | +366 |
| **duck** | 1916 | +238 |
| **Instructors** | 1941 | +262 |
| TA Baseline S | 1675 | -3 |
| **IAmAVirus** | 1678 |  |
| TA Baseline A | 1569 | -109 |
| TA Baseline P | 1434 | -244 |

## Record by version (W-D-L)

| opponent | v27 | v26 | v25 | v24 | v23 | v22 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  |  | 0-0-18 | 0-0-2 |  |  |
| Knight Vision | 0-0-2 | 0-0-4 | 27-0-3 | 4-0-0 |  |  |
| Decent Chess Bot |  | 0-0-4 | 0-1-21 | 0-0-2 |  |  |
| Strongly Invisible |  |  | 2-0-34 | 1-0-7 |  |  |
| **duck** |  |  | 9-9-42 | 2-0-2 | 0-1-9 |  |
| **Instructors** |  | 0-0-2 | 12-5-41 | 0-0-4 | 3-0-3 | 1-0-1 |
| TA Baseline P | 1-0-1 |  | 47-4-7 | 1-1-2 | 4-0-0 | 3-1-0 |
| TA Baseline A | 1-0-1 | 2-1-1 | 56-12-26 | 1-0-1 | 3-0-3 | 4-2-0 |
| TA Baseline S |  | 2-0-2 | 30-8-30 | 0-0-4 | 2-0-0 | 0-1-1 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.4 | 35.4 | 31.2 | 36.3 | 33.3 | 31.8 | 32.5 |
|  | vision-gaining moves | 19.2 | 20.3 | 19.5 | 21.3 | 22.9 | 19.2 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.27 ⚠ | 0.49 | 0.30 ⚠ | 0.46 | 0.38 | 0.42 | 0.40 |
|  | captures from unseen squares | 5.4 ⚠ | 10.5 | 5.6 ⚠ | 10.7 | 9.8 | 9.9 | 8.0 |
|  | captures after a route the other side never saw | 13.0 | 15.4 | 12.7 ⚠ | 16.8 | 17.8 | 15.7 | 14.6 |
|  | long slider strikes | 3.5 ⚠ | 5.8 | 3.2 ⚠ | 6.3 | 4.2 ⚠ | 6.4 | 4.2 |
| King pressure | moves that attack the enemy king | 2.1 ⚠ | 4.3 | 1.6 ⚠ | 4.9 | 3.1 | 3.7 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.8 | 1.7 | 0.8 ⚠ | 2.5 | 1.9 | 0.8 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.7 | 0.2 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.2 | 4.4 | 1.2 | 5.1 | 2.2 | 2.5 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.3 ⚠ | 1.2 | 2.9 ⚠ | 1.3 | 2.0 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 4.0 ⚠ | 2.3 | 4.4 ⚠ | 1.9 | 2.4 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.1 | 0.4 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.1 | 6.2 | 2.1 | 5.4 | 1.9 | 7.3 | 4.8 |
| King handling | king moves | 12.7 | 9.3 | 16.3 | 8.7 | 10.9 | 12.9 | 16.1 |
|  | king moves beyond the second rank | 1.6 | 1.9 | 1.9 | 2.0 | 2.0 | 3.0 | 4.9 |
|  | castling | 2.0 | 1.9 | 2.0 | 2.3 | 2.1 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 50-15-159; 159 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 62 | 35 |
| king walked into an unseen attacker after taking the bait (king capture) | 44 | 19 |
| king already attacked by an unseen piece | 32 | 18 |
| king already attacked by an unseen piece (no safe move existed) | 11 | 6 |
| our move opened a line from an unseen attacker | 6 | 4 |
| king left to an attacker we could see (no safe move existed) | 4 | 1 |

Pieces that took our king: q 53, r 49, b 23, n 19, p 8, k 4, qr 1, bq 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 100, late (70+) or never 3 down 49, opening (ply < 30) 10.
- Down 3 or more at some point in 150 of 159 losses; median first ply 52.0.
- Down 5 or more in 140; median first ply 66.0.
- Lost although we had led by 3 or more: 16 of 159.
- Our clock at 15 s or less: 51 of 159.
- Median length 95 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 31 |
| capturer unseen when we moved, piece had just moved there (r) | 25 |
| capturer unseen when we moved, piece had just moved there (n) | 17 |
| capturer unseen when we moved, piece had just moved there (b) | 14 |
| capturer unseen when we moved (p) | 10 |
| capturer unseen when we moved (n) | 10 |
| capturer unseen when we moved (r) | 8 |
| capturer unseen when we moved, piece had just moved there (p) | 6 |
| capturer unseen when we moved (q) | 6 |
| capturer visible when we moved (q) | 5 |
| capturer visible when we moved (b) | 5 |
| other | 3 |
| capturer unseen when we moved (b) | 3 |
| capturer visible when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (p) | 2 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved (r) | 1 |
| capturer visible when we moved (n) | 1 |

## What worked: v25's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| 58swoa7s | Strongly Invisible | W | win | 104 | King capturable |
| 7he7y2og | Instructors | B | win | 83 | King capturable |
| iulfzm41 | duck | B | draw | 94 | Threefold repetition |
| g7dmwdvn | duck | W | draw | 72 | Threefold repetition |
| 5l7pvcjk | Knight Vision | W | win | 22 | King capturable |
| 8zci6wzz | Knight Vision | B | win | 35 | King capturable |
| 1rjlk96m | duck | W | win | 80 | King capturable |
| z3m0u3zj | Instructors | B | win | 129 | King capturable |
| csa1wuak | Knight Vision | W | win | 22 | King capturable |
| vc1m3gkc | Knight Vision | B | win | 35 | King capturable |
| p9i1favd | Instructors | B | win | 79 | King capturable |
| 1wqopcj0 | Knight Vision | W | win | 22 | King capturable |
| 7ggh71kn | Knight Vision | B | win | 35 | King capturable |
| j8xwm0zq | duck | W | win | 106 | King capturable |
| vrpwws6h | duck | B | draw | 141 | Threefold repetition |
| iz8so4mg | Instructors | B | win | 117 | King capturable |
| 24dmzuv1 | Instructors | B | win | 93 | King capturable |
| y32l71dj | Instructors | W | win | 92 | King capturable |
| bpzzpjix | Instructors | W | draw | 106 | Threefold repetition |
| zle0t440 | Knight Vision | B | win | 35 | King capturable |
| tjvquuy6 | Knight Vision | W | win | 22 | King capturable |
| 8on7taet | duck | B | win | 69 | King capturable |
| kopm8qtu | Instructors | B | draw | 113 | Threefold repetition |
| cvv14buw | Instructors | W | draw | 147 | Threefold repetition |
| wa5t2ja1 | Instructors | W | win | 88 | King capturable |
| uc8t62cs | duck | B | win | 117 | King capturable |
| ptl8f2fd | Instructors | B | win | 95 | King capturable |
| dh3nxxbt | Instructors | W | win | 78 | King capturable |
| pyug7byl | Knight Vision | W | win | 22 | King capturable |
| y1uef2x3 | Knight Vision | B | win | 35 | King capturable |
| 8ttl9pma | Knight Vision | W | win | 22 | King capturable |
| egckbis8 | Knight Vision | B | win | 35 | King capturable |
| 1ihnamqq | Strongly Invisible | W | win | 130 | King capturable |
| lsgr1vx0 | Decent Chess Bot | B | draw | 117 | Threefold repetition |
| yul2h05g | Instructors | W | win | 78 | King capturable |
| cv246ppn | Instructors | W | draw | 79 | Threefold repetition |
| x2anl889 | duck | B | draw | 85 | Threefold repetition |
| rabyoq9x | duck | W | win | 98 | King capturable |
| ina50sic | duck | W | win | 116 | King capturable |
| z5lqcyun | duck | W | win | 80 | King capturable |
| mp41dreh | Instructors | W | win | 178 | King capturable |
| jrgnqz49 | duck | B | draw | 97 | Threefold repetition |
| ybf862oz | Knight Vision | W | win | 22 | King capturable |
| fnuab72w | Knight Vision | W | win | 22 | King capturable |
| bnlf82l8 | Knight Vision | B | win | 35 | King capturable |
| ipyppoos | Knight Vision | B | win | 35 | King capturable |
| cb1fsmpi | Knight Vision | W | win | 22 | King capturable |
| xbq59b4i | Knight Vision | B | win | 35 | King capturable |
| 9f7ty6j7 | duck | B | draw | 51 | Threefold repetition |
| xjf6nsl5 | duck | W | win | 130 | King capturable |
| hobvcluu | Knight Vision | W | win | 22 | King capturable |
| ablgmd0m | Knight Vision | B | win | 35 | King capturable |
| 1fvscrm5 | Knight Vision | W | win | 22 | King capturable |
| 8wi59r3g | Knight Vision | B | win | 35 | King capturable |
| 4kap27db | Instructors | W | win | 92 | King capturable |
| e02qx9i1 | Knight Vision | W | win | 22 | King capturable |
| x6026j8q | Knight Vision | B | win | 35 | King capturable |
| je22ktq7 | Knight Vision | W | win | 22 | King capturable |
| 06f2om5b | Knight Vision | B | win | 35 | King capturable |
| 1thx7r9u | duck | W | draw | 79 | Threefold repetition |
| feko1vw4 | duck | B | win | 79 | King capturable |
| n8n5sd4u | duck | W | draw | 89 | Threefold repetition |
| ht1mu1id | Instructors | B | draw | 104 | Threefold repetition |
| 7ob34ism | Knight Vision | W | win | 22 | King capturable |
| gmftz0yf | duck | B | draw | 93 | Threefold repetition |
