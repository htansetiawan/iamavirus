# Against the top six

Updated 2026-10-14 12:21 UTC; leaderboard fetched 2026-10-14T12:20. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2252 | +389 |
| Knight Vision | 2136 | +273 |
| Decent Chess Bot | 1999 | +136 |
| Strongly Invisible | 2077 | +214 |
| **duck** | 1975 | +112 |
| **Instructors** | 1915 | +52 |
| TA Baseline S | 1611 | -252 |
| **IAmAVirus** | 1863 |  |
| TA Baseline A | 1551 | -313 |
| TA Baseline P | 1455 | -408 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1-0-5 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 3-0-7 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 2-0-6 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 3-0-9 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 4-0-8 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 11-0-1 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.3 | 34.7 | 32.3 | 34.0 | 35.5 | 31.7 | 33.2 |
|  | vision-gaining moves | 21.7 | 21.6 | 20.7 | 21.9 | 22.8 | 17.2 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.43 | 0.48 | 0.40 | 0.45 | 0.42 | 0.39 |
|  | captures from unseen squares | 9.1 | 10.9 | 10.6 | 10.1 | 10.5 | 9.6 | 8.1 |
|  | captures after a route the other side never saw | 16.1 | 17.2 | 15.6 | 18.7 | 17.9 | 14.3 | 14.7 |
|  | long slider strikes | 4.3 ⚠ | 6.2 | 5.4 | 5.2 | 5.0 | 5.0 | 4.2 |
| King pressure | moves that attack the enemy king | 3.8 ⚠ | 5.1 | 4.0 | 4.5 | 4.9 | 2.8 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.8 ⚠ | 2.8 | 1.5 ⚠ | 2.6 | 3.4 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.2 | 0.0 | 0.3 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.1 | 4.3 | 2.1 | 3.8 | 4.3 | 1.5 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.1 ⚠ | 1.0 | 2.4 ⚠ | 1.2 | 1.4 | 3.3 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 2.4 | 2.4 | 4.0 ⚠ | 2.2 | 1.7 | 3.4 | 3.0 |
|  | queen left attacked by an unseen piece | 0.4 | 0.1 | 0.5 | 0.1 | 0.0 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.2 ⚠ | 4.1 | 6.7 ⚠ | 5.4 | 3.5 | 6.8 | 5.3 |
| King handling | king moves | 15.2 | 10.7 | 15.1 | 11.5 | 8.4 | 13.5 | 15.1 |
|  | king moves beyond the second rank | 3.6 | 2.0 | 3.8 | 4.2 | 2.2 | 5.2 | 4.6 |
|  | castling | 1.9 | 2.2 | 1.9 | 1.9 | 1.8 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 13-0-35; 35 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 22 | 13 |
| king walked into an unseen attacker after taking the bait (king capture) | 7 | 2 |
| king already attacked by an unseen piece | 5 | 2 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |

Pieces that took our king: r 19, q 10, k 2, b 2, n 1, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 21, late (70+) or never 3 down 8, opening (ply < 30) 6.
- Down 3 or more at some point in 31 of 35 losses; median first ply 43.
- Down 5 or more in 27; median first ply 56.
- Lost although we had led by 3 or more: 4 of 35.
- Our clock at 15 s or less: 0 of 35.
- Median length 79 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 7 |
| capturer unseen when we moved, piece had just moved there (q) | 6 |
| capturer unseen when we moved, piece had just moved there (n) | 4 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (n) | 1 |
| capturer unseen when we moved (b) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer unseen when we moved (p) | 1 |

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
| whx4qqln | Greek Gift | B | win | 111 | King capturable |
| 1b9cgn8c | Knight Vision | B | win | 67 | King capturable |
| p4ki6f81 | duck | W | win | 54 | King capturable |
| ypy8cnxv | duck | B | win | 99 | King capturable |
