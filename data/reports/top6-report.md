# Against the top six

Updated 2026-10-14 11:19 UTC; leaderboard fetched 2026-10-14T11:18. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2232 | +387 |
| Knight Vision | 2144 | +299 |
| Decent Chess Bot | 2016 | +171 |
| Strongly Invisible | 2095 | +250 |
| **duck** | 1964 | +119 |
| **Instructors** | 1918 | +72 |
| TA Baseline S | 1630 | -216 |
| **IAmAVirus** | 1845 |  |
| TA Baseline A | 1534 | -312 |
| TA Baseline P | 1473 | -372 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-4 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 2-0-4 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 2-0-6 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 1-0-5 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 4-0-8 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 9-0-1 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.6 | 34.3 | 32.0 | 33.5 | 35.5 | 31.5 | 33.2 |
|  | vision-gaining moves | 21.3 | 21.6 | 21.4 | 21.8 | 22.3 | 17.9 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.39 | 0.45 | 0.47 | 0.42 | 0.45 | 0.41 | 0.39 |
|  | captures from unseen squares | 8.5 ⚠ | 11.1 | 10.6 | 10.5 | 10.6 | 9.4 | 8.1 |
|  | captures after a route the other side never saw | 15.2 | 16.6 | 15.4 | 18.2 | 17.6 | 14.7 | 14.7 |
|  | long slider strikes | 4.3 ⚠ | 6.1 | 5.6 | 5.2 | 4.5 | 5.2 | 4.2 |
| King pressure | moves that attack the enemy king | 3.1 ⚠ | 5.1 | 3.5 ⚠ | 4.9 | 4.7 | 2.7 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.5 ⚠ | 2.8 | 1.3 ⚠ | 2.7 | 2.9 | 0.7 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.1 | 0.0 | 0.4 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.3 | 3.6 | 2.1 | 3.6 | 3.6 | 1.6 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.2 ⚠ | 0.9 | 2.2 ⚠ | 1.2 | 1.6 | 3.0 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 2.1 | 2.2 | 3.9 ⚠ | 2.9 | 1.5 | 3.2 | 3.0 |
|  | queen left attacked by an unseen piece | 0.4 | 0.1 | 0.4 | 0.0 | 0.0 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 5.7 ⚠ | 3.1 | 7.5 | 6.5 | 3.9 | 4.5 | 5.3 |
| King handling | king moves | 15.7 | 10.9 | 16.0 | 12.4 | 8.7 | 14.1 | 15.1 |
|  | king moves beyond the second rank | 4.0 | 2.1 | 4.0 | 5.3 | 2.5 | 5.9 | 4.6 |
|  | castling | 1.7 | 2.3 | 2.1 | 2.1 | 1.7 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 9-0-27; 27 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 17 | 11 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 1 |
| king already attacked by an unseen piece | 3 | 1 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |

Pieces that took our king: r 16, q 6, k 2, n 1, b 1, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 16, opening (ply < 30) 6, late (70+) or never 3 down 5.
- Down 3 or more at some point in 24 of 27 losses; median first ply 45.0.
- Down 5 or more in 20; median first ply 54.0.
- Lost although we had led by 3 or more: 3 of 27.
- Our clock at 15 s or less: 0 of 27.
- Median length 80 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 6 |
| capturer unseen when we moved, piece had just moved there (q) | 5 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (b) | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
| 61bzys3l | Instructors | W | win | 98 | King capturable |
| c5cnjewf | Strongly Invisible | W | win | 124 | King capturable |
| h2u89knk | Instructors | B | win | 113 | King capturable |
| gt1mghiq | Instructors | W | win | 80 | King capturable |
| tlaqq2oz | Strongly Invisible | W | win | 120 | King capturable |
| dwyhzuvv | Instructors | W | win | 48 | King capturable |
| 9dlc0mgv | Knight Vision | W | win | 76 | King capturable |
| sjvstkmq | Knight Vision | B | win | 65 | King capturable |
