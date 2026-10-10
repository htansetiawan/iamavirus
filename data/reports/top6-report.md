# Against the top six

Updated 2026-10-10 05:23 UTC; leaderboard fetched 2026-10-10T05:23. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2141 | +486 |
| Knight Vision | 2080 | +425 |
| Decent Chess Bot | 2072 | +416 |
| Strongly Invisible | 2056 | +401 |
| **duck** | 1961 | +305 |
| **Instructors** | 1876 | +221 |
| TA Baseline S | 1613 | -42 |
| **IAmAVirus** | 1655 |  |
| TA Baseline A | 1530 | -125 |
| TA Baseline P | 1451 | -204 |

## Record by version (W-D-L)

| opponent | v25 | v24 | v23 | v22 | v21 | v20 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 |  |  | 0-0-2 | 0-0-2 |
| Knight Vision | 2-0-0 | 4-0-0 |  |  | 0-0-16 | 0-0-6 |
| Decent Chess Bot | 0-0-4 | 0-0-2 |  |  | 1-1-26 | 0-0-10 |
| Strongly Invisible | 1-0-7 | 1-0-7 |  |  | 0-1-13 | 0-2-10 |
| **duck** | 1-2-9 | 2-0-2 | 0-1-9 |  | 0-2-6 | 4-1-11 |
| **Instructors** | 2-0-6 | 0-0-4 | 3-0-3 | 1-0-1 | 3-1-10 | 2-0-8 |
| TA Baseline P | 11-0-3 | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 |
| TA Baseline A | 8-1-3 | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |
| TA Baseline S | 6-0-4 | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.6 | 35.6 | 32.5 | 37.9 | 33.7 | 30.4 | 32.5 |
|  | vision-gaining moves | 17.5 | 18.2 | 18.8 | 19.2 | 25.0 | 18.1 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.31 ⚠ | 0.46 | 0.29 ⚠ | 0.40 | 0.41 | 0.43 | 0.40 |
|  | captures from unseen squares | 6.0 ⚠ | 9.7 | 4.9 ⚠ | 8.7 | 10.6 | 9.8 | 8.0 |
|  | captures after a route the other side never saw | 12.2 | 14.7 | 11.6 ⚠ | 15.9 | 18.8 | 15.2 | 14.6 |
|  | long slider strikes | 3.3 ⚠ | 5.7 | 3.0 ⚠ | 5.7 | 5.2 | 6.2 | 4.2 |
| King pressure | moves that attack the enemy king | 1.5 ⚠ | 4.5 | 1.6 ⚠ | 4.3 | 3.2 | 3.6 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.3 ⚠ | 1.8 | 1.3 ⚠ | 2.4 | 2.1 | 1.1 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.2 | 0.0 | 0.3 | 0.2 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.2 | 4.0 | 0.9 | 5.4 | 2.8 | 2.2 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.6 ⚠ | 1.3 | 3.8 ⚠ | 1.1 | 2.4 | 4.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 1.6 | 4.5 ⚠ | 1.9 | 2.4 | 2.6 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.2 | 0.0 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 1.0 | 5.8 | 1.9 | 3.9 | 0.7 | 5.6 | 4.8 |
| King handling | king moves | 11.4 | 7.9 | 10.0 | 6.9 | 10.6 | 17.1 | 16.1 |
|  | king moves beyond the second rank | 2.6 | 1.3 | 0.5 | 0.6 | 2.5 | 6.2 | 4.9 |
|  | castling | 1.9 | 1.9 | 2.0 | 2.2 | 2.2 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 6-2-26; 26 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 10 | 8 |
| king already attacked by an unseen piece | 9 | 4 |
| king walked into an unseen attacker after taking the bait (king capture) | 3 | 2 |
| king left to an attacker we could see (no safe move existed) | 2 | 1 |
| our move opened a line from an unseen attacker | 1 | 0 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |

Pieces that took our king: q 11, r 8, n 5, k 1, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 16, late (70+) or never 3 down 9, opening (ply < 30) 1.
- Down 3 or more at some point in 25 of 26 losses; median first ply 55.
- Down 5 or more in 24; median first ply 67.0.
- Lost although we had led by 3 or more: 2 of 26.
- Our clock at 15 s or less: 6 of 26.
- Median length 103.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved (n) | 4 |
| capturer unseen when we moved, piece had just moved there (q) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (q) | 2 |
| capturer visible when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer unseen when we moved (b) | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |

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
