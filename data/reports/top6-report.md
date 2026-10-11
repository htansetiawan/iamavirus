# Against the top six

Updated 2026-10-11 01:01 UTC; leaderboard fetched 2026-10-11T01:00. Active version: v28. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2110 | +425 |
| Knight Vision | 2065 | +380 |
| Decent Chess Bot | 2045 | +359 |
| Strongly Invisible | 2066 | +380 |
| **duck** | 1906 | +220 |
| **Instructors** | 1935 | +249 |
| TA Baseline S | 1659 | -26 |
| **IAmAVirus** | 1685 |  |
| TA Baseline A | 1574 | -111 |
| TA Baseline P | 1419 | -266 |

## Record by version (W-D-L)

| opponent | v28 | v27 | v26 | v25 | v24 | v23 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  |  |  | 0-0-18 | 0-0-2 |  |
| Knight Vision | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 | 4-0-0 |  |
| Decent Chess Bot | 0-0-2 |  | 0-0-4 | 0-1-23 | 0-0-2 |  |
| Strongly Invisible | 0-0-2 |  |  | 2-0-34 | 1-0-7 |  |
| **duck** | 1-0-3 |  |  | 9-9-42 | 2-0-2 | 0-1-9 |
| **Instructors** | 1-0-1 |  | 0-0-2 | 12-5-41 | 0-0-4 | 3-0-3 |
| TA Baseline P | 2-0-0 | 1-0-1 |  | 47-4-7 | 1-1-2 | 4-0-0 |
| TA Baseline A | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 | 1-0-1 | 3-0-3 |
| TA Baseline S | 2-0-0 |  | 2-0-2 | 30-8-30 | 0-0-4 | 2-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v28. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.2 | 31.8 | 31.2 | 37.6 | 37.7 | 33.2 | 32.5 |
|  | vision-gaining moves | 21.8 | 19.5 | 22.9 | 27.8 | 24.8 | 20.2 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.37 | 0.39 | 0.54 | 0.42 | 0.52 | 0.34 | 0.40 |
|  | captures from unseen squares | 8.6 | 8.6 | 11.9 | 13.0 | 13.4 | 8.1 | 8.0 |
|  | captures after a route the other side never saw | 17.5 | 15.2 | 17.0 | 20.4 | 20.5 | 14.0 | 14.6 |
|  | long slider strikes | 4.3 | 5.1 | 6.0 | 6.0 | 5.9 | 5.0 | 4.2 |
| King pressure | moves that attack the enemy king | 3.9 ⚠ | 5.4 | 4.6 ⚠ | 6.5 | 3.1 | 2.3 | 3.3 |
|  | ...with an attacker the king's side cannot see | 2.3 | 1.9 | 1.8 | 2.8 | 2.0 | 0.4 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.0 | 0.5 | 1.2 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.7 | 3.1 | 2.8 | 5.1 | 5.5 | 0.8 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 1.6 | 1.6 | 3.2 ⚠ | 0.9 | 1.6 | 3.1 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 4.3 ⚠ | 3.1 | 0.9 | 2.8 | 1.2 | 7.0 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.0 | 0.9 | 0.0 | 0.0 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 6.2 ⚠ | 4.7 | 7.8 ⚠ | 2.3 | 7.9 ⚠ | 5.0 | 4.8 |
| King handling | king moves | 11.3 | 21.4 | 17.0 | 6.9 | 7.5 | 7.8 | 16.1 |
|  | king moves beyond the second rank | 3.1 | 11.7 | 2.3 | 0.5 | 0.0 | 0.4 | 4.9 |
|  | castling | 2.3 | 2.3 | 2.8 | 2.3 | 2.4 | 2.7 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v28 against the top six

Record 2-0-10; 10 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece | 5 | 2 |
| Time forfeit | 2 | 1 |
| king walked into an unseen attacker | 1 | 1 |
| our move opened a line from an unseen attacker | 1 | 0 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |

Pieces that took our king: q 5, n 2, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: late (70+) or never 3 down 4, opening (ply < 30) 4, middlegame (30-69) 2.
- Down 3 or more at some point in 7 of 10 losses; median first ply 27.
- Down 5 or more in 6; median first ply 43.5.
- Lost although we had led by 3 or more: 1 of 10.
- Our clock at 15 s or less: 3 of 10.
- Median length 72.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer visible when we moved (n) | 1 |
| capturer unseen when we moved (r) | 1 |

## What worked: v28's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| sxihhw6v | Instructors | W | win | 160 | King capturable |
| hbis6yll | duck | W | win | 72 | King capturable |
