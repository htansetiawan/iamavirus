# Against the top six

Updated 2026-10-10 15:40 UTC; leaderboard fetched 2026-10-10T15:40. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2154 | +443 |
| Knight Vision | 2078 | +367 |
| Decent Chess Bot | 2030 | +319 |
| Strongly Invisible | 2049 | +339 |
| **duck** | 1920 | +210 |
| **Instructors** | 1928 | +217 |
| TA Baseline S | 1650 | -60 |
| **IAmAVirus** | 1710 |  |
| TA Baseline A | 1554 | -156 |
| TA Baseline P | 1394 | -316 |

## Record by version (W-D-L)

| opponent | v25 | v24 | v23 | v22 | v21 | v20 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-10 | 0-0-2 |  |  | 0-0-2 | 0-0-2 |
| Knight Vision | 12-0-0 | 4-0-0 |  |  | 0-0-16 | 0-0-6 |
| Decent Chess Bot | 0-1-17 | 0-0-2 |  |  | 1-1-26 | 0-0-10 |
| Strongly Invisible | 2-0-24 | 1-0-7 |  |  | 0-1-13 | 0-2-10 |
| **duck** | 6-4-28 | 2-0-2 | 0-1-9 |  | 0-2-6 | 4-1-11 |
| **Instructors** | 10-4-30 | 0-0-4 | 3-0-3 | 1-0-1 | 3-1-10 | 2-0-8 |
| TA Baseline P | 35-3-4 | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 |
| TA Baseline A | 37-10-17 | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |
| TA Baseline S | 21-5-16 | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.5 | 35.1 | 30.8 | 35.8 | 33.2 | 31.3 | 32.5 |
|  | vision-gaining moves | 19.2 | 20.3 | 18.9 | 20.9 | 23.3 | 19.2 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.28 ⚠ | 0.49 | 0.30 ⚠ | 0.46 | 0.38 | 0.41 | 0.40 |
|  | captures from unseen squares | 5.8 ⚠ | 10.6 | 5.2 ⚠ | 10.1 | 9.7 | 9.6 | 8.0 |
|  | captures after a route the other side never saw | 13.2 | 15.4 | 11.8 ⚠ | 16.5 | 17.7 | 15.1 | 14.6 |
|  | long slider strikes | 3.6 ⚠ | 5.7 | 2.9 ⚠ | 5.7 | 4.1 ⚠ | 6.2 | 4.2 |
| King pressure | moves that attack the enemy king | 2.1 ⚠ | 4.4 | 1.6 ⚠ | 4.2 | 2.9 | 3.7 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.8 | 1.7 | 0.7 ⚠ | 2.2 | 2.0 | 0.9 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.0 | 0.6 | 0.2 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.3 | 4.5 | 0.9 | 5.3 | 2.3 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.2 | 1.4 | 2.8 ⚠ | 1.1 | 2.1 | 3.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 4.0 ⚠ | 2.6 | 4.3 ⚠ | 1.9 | 2.4 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.3 | 6.8 | 1.9 | 6.0 | 1.2 | 7.5 | 4.8 |
| King handling | king moves | 12.9 | 9.7 | 16.8 | 9.3 | 10.7 | 13.7 | 16.1 |
|  | king moves beyond the second rank | 1.7 | 1.9 | 1.9 | 2.2 | 2.0 | 3.7 | 4.9 |
|  | castling | 2.0 | 1.9 | 1.9 | 2.1 | 2.0 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 30-9-109; 109 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 43 | 23 |
| king walked into an unseen attacker after taking the bait (king capture) | 27 | 14 |
| king already attacked by an unseen piece | 25 | 15 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 2 |
| our move opened a line from an unseen attacker | 5 | 3 |
| king left to an attacker we could see (no safe move existed) | 4 | 1 |

Pieces that took our king: q 39, r 27, b 17, n 15, p 6, k 4, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 69, late (70+) or never 3 down 37, opening (ply < 30) 3.
- Down 3 or more at some point in 103 of 109 losses; median first ply 53.
- Down 5 or more in 97; median first ply 67.
- Lost although we had led by 3 or more: 14 of 109.
- Our clock at 15 s or less: 36 of 109.
- Median length 96 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 23 |
| capturer unseen when we moved, piece had just moved there (r) | 14 |
| capturer unseen when we moved, piece had just moved there (b) | 10 |
| capturer unseen when we moved (p) | 9 |
| capturer unseen when we moved, piece had just moved there (n) | 9 |
| capturer unseen when we moved (n) | 7 |
| capturer unseen when we moved (r) | 6 |
| capturer unseen when we moved, piece had just moved there (p) | 5 |
| capturer unseen when we moved (q) | 5 |
| capturer visible when we moved (b) | 4 |
| capturer visible when we moved (q) | 2 |
| capturer unseen when we moved (b) | 2 |
| capturer visible when we moved (p) | 2 |
| other | 2 |
| capturer visible when we moved (r) | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
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
