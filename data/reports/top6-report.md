# Against the top six

Updated 2026-10-10 09:50 UTC; leaderboard fetched 2026-10-10T09:50. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2172 | +475 |
| Knight Vision | 2013 | +316 |
| Decent Chess Bot | 2056 | +359 |
| Strongly Invisible | 2026 | +329 |
| **duck** | 1961 | +265 |
| **Instructors** | 1903 | +207 |
| TA Baseline S | 1658 | -39 |
| **IAmAVirus** | 1696 |  |
| TA Baseline A | 1513 | -184 |
| TA Baseline P | 1417 | -280 |

## Record by version (W-D-L)

| opponent | v25 | v24 | v23 | v22 | v21 | v20 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-4 | 0-0-2 |  |  | 0-0-2 | 0-0-2 |
| Knight Vision | 8-0-0 | 4-0-0 |  |  | 0-0-16 | 0-0-6 |
| Decent Chess Bot | 0-0-6 | 0-0-2 |  |  | 1-1-26 | 0-0-10 |
| Strongly Invisible | 1-0-13 | 1-0-7 |  |  | 0-1-13 | 0-2-10 |
| **duck** | 2-3-16 | 2-0-2 | 0-1-9 |  | 0-2-6 | 4-1-11 |
| **Instructors** | 6-1-15 | 0-0-4 | 3-0-3 | 1-0-1 | 3-1-10 | 2-0-8 |
| TA Baseline P | 22-2-4 | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 |
| TA Baseline A | 27-7-10 | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |
| TA Baseline S | 12-2-10 | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.5 | 35.3 | 32.2 | 37.1 | 33.5 | 31.4 | 32.5 |
|  | vision-gaining moves | 18.7 | 20.0 | 19.8 | 20.6 | 23.7 | 19.6 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.30 ⚠ | 0.45 | 0.30 ⚠ | 0.46 | 0.39 | 0.42 | 0.40 |
|  | captures from unseen squares | 6.0 ⚠ | 9.6 | 5.7 ⚠ | 11.2 | 9.9 | 9.6 | 8.0 |
|  | captures after a route the other side never saw | 12.9 | 15.1 | 12.8 ⚠ | 18.1 | 17.9 | 15.2 | 14.6 |
|  | long slider strikes | 4.0 ⚠ | 5.9 | 3.3 ⚠ | 6.3 | 4.1 ⚠ | 6.1 | 4.2 |
| King pressure | moves that attack the enemy king | 1.9 ⚠ | 4.5 | 1.9 ⚠ | 4.8 | 2.8 ⚠ | 3.9 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.5 ⚠ | 1.7 | 1.1 ⚠ | 2.6 | 1.9 | 1.0 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.0 | 0.4 | 0.2 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.4 | 4.2 | 1.3 | 5.4 | 2.5 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.2 | 1.3 | 3.5 ⚠ | 1.1 | 2.1 | 3.7 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.6 | 2.8 | 5.2 ⚠ | 1.6 | 2.6 | 3.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.2 | 0.3 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 3.0 | 6.5 | 2.1 | 6.2 | 1.5 | 7.3 | 4.8 |
| King handling | king moves | 12.9 | 8.7 | 11.8 | 7.9 | 11.0 | 14.1 | 16.1 |
|  | king moves beyond the second rank | 1.6 | 1.3 | 0.9 | 1.5 | 2.1 | 3.7 | 4.9 |
|  | castling | 2.0 | 1.9 | 2.2 | 2.4 | 2.0 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 17-4-54; 54 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 21 | 14 |
| king already attacked by an unseen piece | 13 | 7 |
| king walked into an unseen attacker after taking the bait (king capture) | 10 | 6 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 2 |
| our move opened a line from an unseen attacker | 3 | 1 |
| king left to an attacker we could see (no safe move existed) | 2 | 1 |

Pieces that took our king: q 19, r 16, n 9, b 6, k 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 36, late (70+) or never 3 down 16, opening (ply < 30) 2.
- Down 3 or more at some point in 51 of 54 losses; median first ply 53.
- Down 5 or more in 49; median first ply 64.
- Lost although we had led by 3 or more: 5 of 54.
- Our clock at 15 s or less: 15 of 54.
- Median length 94.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 9 |
| capturer unseen when we moved, piece had just moved there (q) | 8 |
| capturer unseen when we moved (n) | 5 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer unseen when we moved, piece had just moved there (n) | 4 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved (p) | 3 |
| capturer unseen when we moved (q) | 3 |
| capturer visible when we moved (b) | 3 |
| capturer visible when we moved (p) | 2 |
| capturer visible when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (r) | 1 |
| capturer unseen when we moved (b) | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (n) | 1 |
| other | 1 |

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
