# Against the top six

Updated 2026-10-14 13:02 UTC; leaderboard fetched 2026-10-14T13:02. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2256 | +395 |
| Knight Vision | 2133 | +272 |
| Decent Chess Bot | 2003 | +142 |
| Strongly Invisible | 2064 | +203 |
| **duck** | 1998 | +137 |
| **Instructors** | 1923 | +63 |
| TA Baseline S | 1614 | -247 |
| **IAmAVirus** | 1861 |  |
| TA Baseline A | 1535 | -325 |
| TA Baseline P | 1465 | -395 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 2-0-8 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 3-0-7 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 3-0-7 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 3-0-13 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 4-0-8 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 13-0-1 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.7 | 34.5 | 32.6 | 34.4 | 35.6 | 31.9 | 33.2 |
|  | vision-gaining moves | 21.2 | 21.1 | 20.8 | 21.6 | 23.2 | 17.8 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.44 | 0.46 | 0.39 | 0.45 | 0.40 | 0.39 |
|  | captures from unseen squares | 9.1 | 11.1 | 10.0 | 9.9 | 11.0 | 9.3 | 8.1 |
|  | captures after a route the other side never saw | 16.2 | 17.3 | 15.4 | 18.5 | 18.3 | 14.4 | 14.7 |
|  | long slider strikes | 4.5 ⚠ | 6.1 | 4.9 | 5.4 | 5.2 | 5.3 | 4.2 |
| King pressure | moves that attack the enemy king | 3.6 ⚠ | 5.0 | 3.7 | 4.4 | 5.0 | 2.9 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.6 | 2.6 | 1.6 | 2.4 | 3.5 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.3 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.6 | 4.3 | 2.4 | 3.9 | 4.9 | 1.4 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.9 ⚠ | 0.9 | 2.4 ⚠ | 1.3 | 1.4 | 3.7 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 2.5 | 2.2 | 3.7 | 2.9 | 1.7 | 3.4 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.1 | 0.5 | 0.2 | 0.0 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.4 ⚠ | 3.5 | 8.2 ⚠ | 5.3 | 3.3 | 6.6 | 5.3 |
| King handling | king moves | 16.6 | 11.4 | 14.0 | 11.2 | 8.5 | 13.2 | 15.1 |
|  | king moves beyond the second rank | 3.6 | 2.4 | 3.4 | 4.0 | 2.1 | 5.1 | 4.6 |
|  | castling | 1.9 | 2.2 | 2.0 | 2.0 | 1.9 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 15-0-43; 43 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 25 | 14 |
| king walked into an unseen attacker after taking the bait (king capture) | 10 | 4 |
| king already attacked by an unseen piece | 6 | 3 |
| king left to an attacker we could see (no safe move existed) | 2 | 0 |

Pieces that took our king: r 23, q 12, k 3, p 2, b 2, n 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 28, late (70+) or never 3 down 8, opening (ply < 30) 7.
- Down 3 or more at some point in 39 of 43 losses; median first ply 44.
- Down 5 or more in 34; median first ply 56.0.
- Lost although we had led by 3 or more: 5 of 43.
- Our clock at 15 s or less: 0 of 43.
- Median length 79 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 8 |
| capturer unseen when we moved, piece had just moved there (q) | 7 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved, piece had just moved there (b) | 5 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer unseen when we moved (b) | 2 |
| capturer unseen when we moved (n) | 2 |
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
