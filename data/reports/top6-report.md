# Against the top six

Updated 2026-10-14 13:23 UTC; leaderboard fetched 2026-10-14T13:22. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2260 | +406 |
| Knight Vision | 2137 | +283 |
| Decent Chess Bot | 2011 | +157 |
| Strongly Invisible | 2065 | +210 |
| **duck** | 1997 | +143 |
| **Instructors** | 1928 | +74 |
| TA Baseline S | 1607 | -248 |
| **IAmAVirus** | 1854 |  |
| TA Baseline A | 1544 | -310 |
| TA Baseline P | 1447 | -407 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 2-0-8 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 3-0-8 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 3-0-9 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 3-0-15 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 4-0-8 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 15-0-1 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.5 | 35.2 | 32.4 | 34.6 | 35.3 | 31.6 | 33.2 |
|  | vision-gaining moves | 20.6 | 20.4 | 20.7 | 21.7 | 23.2 | 18.0 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.42 | 0.45 | 0.46 | 0.40 | 0.44 | 0.40 | 0.39 |
|  | captures from unseen squares | 8.7 ⚠ | 11.1 | 10.0 | 10.4 | 10.6 | 9.1 | 8.1 |
|  | captures after a route the other side never saw | 15.4 | 17.1 | 15.4 | 18.9 | 18.2 | 13.9 | 14.7 |
|  | long slider strikes | 4.3 ⚠ | 5.9 | 5.0 | 5.8 | 5.2 | 5.2 | 4.2 |
| King pressure | moves that attack the enemy king | 3.4 ⚠ | 4.8 | 3.4 | 4.2 | 4.9 | 2.9 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.5 | 2.4 | 1.5 | 2.3 | 3.3 | 0.5 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.3 | 0.4 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.4 | 5.0 | 2.3 | 3.9 | 4.4 | 1.6 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.3 ⚠ | 0.9 | 2.5 ⚠ | 1.2 | 1.3 | 3.5 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 2.9 | 2.3 | 3.7 | 2.8 | 1.9 | 3.1 | 3.0 |
|  | queen left attacked by an unseen piece | 0.4 | 0.1 | 0.4 | 0.1 | 0.0 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 5.8 ⚠ | 3.2 | 8.6 ⚠ | 5.3 | 2.9 | 6.9 | 5.3 |
| King handling | king moves | 16.5 | 10.7 | 13.8 | 10.9 | 8.5 | 14.2 | 15.1 |
|  | king moves beyond the second rank | 3.3 | 2.2 | 3.2 | 3.9 | 2.4 | 5.1 | 4.6 |
|  | castling | 1.9 | 2.2 | 2.0 | 2.0 | 1.9 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 15-0-48; 48 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 28 | 15 |
| king walked into an unseen attacker after taking the bait (king capture) | 11 | 5 |
| king already attacked by an unseen piece | 7 | 3 |
| king left to an attacker we could see (no safe move existed) | 2 | 0 |

Pieces that took our king: r 26, q 12, k 3, n 3, p 2, b 2

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 31, opening (ply < 30) 9, late (70+) or never 3 down 8.
- Down 3 or more at some point in 44 of 48 losses; median first ply 43.0.
- Down 5 or more in 39; median first ply 55.
- Lost although we had led by 3 or more: 5 of 48.
- Our clock at 15 s or less: 0 of 48.
- Median length 79.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 10 |
| capturer unseen when we moved, piece had just moved there (q) | 8 |
| capturer unseen when we moved, piece had just moved there (n) | 7 |
| capturer unseen when we moved, piece had just moved there (b) | 5 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved (n) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer unseen when we moved (b) | 2 |
| capturer unseen when we moved (q) | 1 |
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
| kxkm3ewh | Strongly Invisible | B | win | 67 | King capturable |
| 0yc4k7zr | Greek Gift | W | win | 88 | King capturable |
