# Against the top six

Updated 2026-10-14 21:59 UTC; leaderboard fetched 2026-10-14T21:58. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2254 | +377 |
| Knight Vision | 2086 | +209 |
| Decent Chess Bot | 1994 | +116 |
| Strongly Invisible | 2075 | +197 |
| **duck** | 1992 | +114 |
| **Instructors** | 1924 | +47 |
| TA Baseline S | 1698 | -180 |
| **IAmAVirus** | 1878 |  |
| TA Baseline A | 1533 | -345 |
| TA Baseline P | 1388 | -490 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 3-0-13 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 6-0-22 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot | 6-1-11 | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 6-0-22 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 8-0-28 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 6-0-18 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P | 8-0-0 | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 16-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 19-0-3 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.7 | 35.3 | 32.2 | 34.5 | 35.9 | 31.7 | 33.2 |
|  | vision-gaining moves | 20.2 | 21.2 | 20.9 | 21.8 | 22.7 | 17.8 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.41 | 0.42 | 0.37 | 0.47 | 0.40 | 0.39 |
|  | captures from unseen squares | 8.7 | 10.0 | 9.2 | 9.6 | 11.4 | 9.2 | 8.1 |
|  | captures after a route the other side never saw | 15.3 | 16.6 | 15.5 | 18.9 | 18.6 | 14.0 | 14.7 |
|  | long slider strikes | 4.8 | 5.4 | 4.7 | 5.3 | 5.3 | 5.3 | 4.2 |
| King pressure | moves that attack the enemy king | 2.7 ⚠ | 4.9 | 3.1 ⚠ | 5.0 | 4.6 | 2.8 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.2 ⚠ | 2.6 | 1.0 ⚠ | 2.7 | 3.1 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.1 | 0.2 | 0.8 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.7 | 4.6 | 2.1 | 3.6 | 3.4 | 2.0 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.4 ⚠ | 1.3 | 2.7 ⚠ | 1.2 | 1.8 | 3.2 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.5 | 3.5 ⚠ | 2.2 | 1.8 | 3.6 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.1 | 0.3 | 0.2 | 0.0 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 7.7 ⚠ | 3.6 | 8.2 ⚠ | 3.6 | 3.0 | 5.3 | 5.3 |
| King handling | king moves | 18.2 | 9.6 | 15.4 | 11.3 | 8.2 | 13.3 | 15.1 |
|  | king moves beyond the second rank | 3.5 | 1.8 | 3.7 | 3.1 | 1.6 | 4.8 | 4.6 |
|  | castling | 1.9 | 2.1 | 2.2 | 2.1 | 1.9 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 35-1-114; 114 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 61 | 27 |
| king already attacked by an unseen piece | 25 | 7 |
| king walked into an unseen attacker after taking the bait (king capture) | 19 | 9 |
| king left to an attacker we could see (no safe move existed) | 8 | 2 |
| our move opened a line from an unseen attacker | 1 | 1 |

Pieces that took our king: r 54, q 44, n 5, b 4, p 3, k 3, br 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 78, late (70+) or never 3 down 18, opening (ply < 30) 18.
- Down 3 or more at some point in 107 of 114 losses; median first ply 46.
- Down 5 or more in 99; median first ply 55.
- Lost although we had led by 3 or more: 5 of 114.
- Our clock at 15 s or less: 0 of 114.
- Median length 81.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 35 |
| capturer unseen when we moved, piece had just moved there (n) | 17 |
| capturer unseen when we moved, piece had just moved there (b) | 13 |
| capturer unseen when we moved, piece had just moved there (q) | 9 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (r) | 5 |
| capturer unseen when we moved (q) | 4 |
| capturer visible when we moved (p) | 3 |
| capturer unseen when we moved (b) | 3 |
| capturer unseen when we moved (p) | 3 |
| other | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer visible when we moved (n) | 2 |
| capturer visible when we moved, piece had just moved there (p) | 1 |

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
| gt4i6a6q | duck | B | win | 95 | King capturable |
| 3gswuuyj | Strongly Invisible | W | win | 76 | King capturable |
| p9ff21uk | Decent Chess Bot | B | draw | 114 | Threefold repetition |
| i4fx2fc5 | Knight Vision | B | win | 67 | King capturable |
| em1o8ynh | duck | B | win | 79 | King capturable |
| 0oaoht7a | Decent Chess Bot | B | win | 47 | King capturable |
| dak540m5 | Decent Chess Bot | W | win | 140 | King capturable |
| c8blbwsd | duck | W | win | 104 | King capturable |
| n5thcux1 | Decent Chess Bot | W | win | 148 | King capturable |
| sa74ct2b | Decent Chess Bot | B | win | 149 | King capturable |
| 91y36gm2 | Knight Vision | B | win | 61 | King capturable |
| cvlwe3jy | Instructors | W | win | 80 | King capturable |
| em6c5ypk | Knight Vision | B | win | 59 | King capturable |
| 6d37j0ih | Greek Gift | B | win | 129 | King capturable |
