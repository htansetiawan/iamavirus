# Against the top six

Updated 2026-10-14 17:51 UTC; leaderboard fetched 2026-10-14T17:51. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2268 | +410 |
| Knight Vision | 2110 | +252 |
| Decent Chess Bot | 1966 | +108 |
| Strongly Invisible | 2055 | +197 |
| **duck** | 2024 | +166 |
| **Instructors** | 1949 | +91 |
| TA Baseline S | 1677 | -181 |
| **IAmAVirus** | 1858 |  |
| TA Baseline A | 1525 | -333 |
| TA Baseline P | 1436 | -421 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 2-0-10 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 3-0-11 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot | 2-0-6 | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 5-0-17 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 5-0-21 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 5-0-11 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P | 4-0-0 | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 14-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 17-0-3 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.6 | 35.0 | 32.6 | 35.3 | 35.7 | 31.9 | 33.2 |
|  | vision-gaining moves | 20.2 | 20.3 | 21.1 | 22.8 | 22.3 | 17.6 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.42 | 0.42 | 0.39 | 0.47 | 0.40 | 0.39 |
|  | captures from unseen squares | 8.8 | 10.3 | 9.5 | 10.5 | 11.6 | 9.5 | 8.1 |
|  | captures after a route the other side never saw | 15.2 | 16.8 | 15.5 ⚠ | 19.6 | 18.7 | 14.4 | 14.7 |
|  | long slider strikes | 4.4 ⚠ | 5.7 | 5.1 | 5.7 | 5.4 | 5.5 | 4.2 |
| King pressure | moves that attack the enemy king | 2.9 ⚠ | 4.9 | 3.4 ⚠ | 5.1 | 4.6 | 2.9 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.2 ⚠ | 2.6 | 1.0 ⚠ | 2.7 | 3.1 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.3 | 0.7 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.5 | 5.0 | 2.1 | 3.9 | 3.6 | 1.8 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.3 ⚠ | 1.1 | 2.8 ⚠ | 1.1 | 1.8 | 3.4 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 ⚠ | 2.2 | 3.6 ⚠ | 2.5 | 1.8 | 3.4 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.1 | 0.4 | 0.2 | 0.0 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.9 ⚠ | 3.2 | 8.4 ⚠ | 4.0 | 2.7 | 5.4 | 5.3 |
| King handling | king moves | 16.7 | 10.1 | 14.8 | 9.8 | 8.6 | 13.3 | 15.1 |
|  | king moves beyond the second rank | 3.8 | 2.2 | 3.0 | 2.5 | 1.9 | 4.4 | 4.6 |
|  | castling | 2.0 | 2.2 | 2.2 | 2.2 | 1.8 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 22-0-76; 76 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 41 | 20 |
| king already attacked by an unseen piece | 15 | 4 |
| king walked into an unseen attacker after taking the bait (king capture) | 14 | 6 |
| king left to an attacker we could see (no safe move existed) | 5 | 1 |
| our move opened a line from an unseen attacker | 1 | 1 |

Pieces that took our king: r 42, q 22, n 4, k 3, b 3, p 2

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 51, opening (ply < 30) 14, late (70+) or never 3 down 11.
- Down 3 or more at some point in 72 of 76 losses; median first ply 44.0.
- Down 5 or more in 64; median first ply 54.5.
- Lost although we had led by 3 or more: 5 of 76.
- Our clock at 15 s or less: 0 of 76.
- Median length 79.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 21 |
| capturer unseen when we moved, piece had just moved there (n) | 14 |
| capturer unseen when we moved, piece had just moved there (q) | 9 |
| capturer unseen when we moved, piece had just moved there (b) | 7 |
| capturer unseen when we moved (r) | 4 |
| capturer unseen when we moved (n) | 4 |
| capturer unseen when we moved (p) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer unseen when we moved (b) | 2 |
| capturer visible when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer unseen when we moved (q) | 1 |
| other | 1 |

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
| llxllazf | Decent Chess Bot | W | win | 60 | King capturable |
| f3qhsn1p | Strongly Invisible | W | win | 88 | King capturable |
| hqk1jhep | duck | W | win | 68 | King capturable |
| 9fwegd4g | Instructors | W | win | 70 | King capturable |
| va6pv7uf | Strongly Invisible | B | win | 97 | King capturable |
| 8x4m9ds3 | Decent Chess Bot | W | win | 68 | King capturable |
| 81ad7fm9 | duck | W | win | 86 | King capturable |
