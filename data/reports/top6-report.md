# Against the top six

Updated 2026-10-10 06:04 UTC; leaderboard fetched 2026-10-10T06:04. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2146 | +489 |
| Knight Vision | 2078 | +421 |
| Decent Chess Bot | 2078 | +421 |
| Strongly Invisible | 2054 | +397 |
| **duck** | 1968 | +310 |
| **Instructors** | 1870 | +213 |
| TA Baseline S | 1612 | -45 |
| **IAmAVirus** | 1657 |  |
| TA Baseline A | 1517 | -140 |
| TA Baseline P | 1447 | -210 |

## Record by version (W-D-L)

| opponent | v25 | v24 | v23 | v22 | v21 | v20 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 |  |  | 0-0-2 | 0-0-2 |
| Knight Vision | 2-0-0 | 4-0-0 |  |  | 0-0-16 | 0-0-6 |
| Decent Chess Bot | 0-0-4 | 0-0-2 |  |  | 1-1-26 | 0-0-10 |
| Strongly Invisible | 1-0-9 | 1-0-7 |  |  | 0-1-13 | 0-2-10 |
| **duck** | 1-2-11 | 2-0-2 | 0-1-9 |  | 0-2-6 | 4-1-11 |
| **Instructors** | 2-0-6 | 0-0-4 | 3-0-3 | 1-0-1 | 3-1-10 | 2-0-8 |
| TA Baseline P | 11-0-3 | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 |
| TA Baseline A | 16-3-5 | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |
| TA Baseline S | 8-0-6 | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.7 | 35.9 | 31.9 | 37.0 | 33.6 | 31.1 | 32.5 |
|  | vision-gaining moves | 18.0 | 18.7 | 18.5 | 19.3 | 25.2 | 19.2 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.32 ⚠ | 0.46 | 0.28 ⚠ | 0.42 | 0.39 | 0.43 | 0.40 |
|  | captures from unseen squares | 6.3 ⚠ | 10.0 | 4.9 ⚠ | 9.4 | 10.0 | 10.1 | 8.0 |
|  | captures after a route the other side never saw | 12.6 | 15.1 | 12.2 ⚠ | 17.0 | 18.6 | 15.3 | 14.6 |
|  | long slider strikes | 3.5 ⚠ | 5.9 | 3.1 ⚠ | 5.7 | 4.7 ⚠ | 6.1 | 4.2 |
| King pressure | moves that attack the enemy king | 1.5 ⚠ | 4.6 | 1.7 ⚠ | 4.3 | 3.3 | 3.8 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.3 ⚠ | 1.8 | 1.0 ⚠ | 2.2 | 2.2 | 1.2 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.5 | 0.1 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.2 | 4.3 | 1.0 | 5.4 | 2.6 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.6 ⚠ | 1.3 | 3.7 ⚠ | 1.1 | 2.3 | 4.1 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 1.6 | 4.4 ⚠ | 1.8 | 2.5 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.1 | 0.0 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 0.9 | 5.5 | 2.8 | 4.8 | 0.9 | 7.0 | 4.8 |
| King handling | king moves | 11.3 | 7.9 | 12.3 | 7.8 | 10.1 | 15.5 | 16.1 |
|  | king moves beyond the second rank | 2.5 | 1.3 | 0.6 | 1.4 | 2.2 | 4.9 | 4.9 |
|  | castling | 2.0 | 1.9 | 2.1 | 2.2 | 2.1 | 2.2 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 6-2-32; 32 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 12 | 9 |
| king already attacked by an unseen piece | 9 | 4 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 3 |
| king left to an attacker we could see (no safe move existed) | 2 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 2 | 0 |
| our move opened a line from an unseen attacker | 1 | 0 |

Pieces that took our king: q 12, r 8, n 8, k 2, b 2

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 21, late (70+) or never 3 down 10, opening (ply < 30) 1.
- Down 3 or more at some point in 30 of 32 losses; median first ply 55.5.
- Down 5 or more in 28; median first ply 66.0.
- Lost although we had led by 3 or more: 2 of 32.
- Our clock at 15 s or less: 8 of 32.
- Median length 96.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 7 |
| capturer unseen when we moved (n) | 4 |
| capturer unseen when we moved, piece had just moved there (q) | 4 |
| capturer unseen when we moved (p) | 3 |
| capturer unseen when we moved (q) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
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
