# Against the top six

Updated 2026-10-11 16:04 UTC; leaderboard fetched 2026-10-11T16:04. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2145 | +377 |
| Knight Vision | 2080 | +312 |
| Decent Chess Bot | 2083 | +315 |
| Strongly Invisible | 2049 | +280 |
| **duck** | 1907 | +139 |
| **Instructors** | 1887 | +118 |
| TA Baseline S | 1675 | -94 |
| **IAmAVirus** | 1768 |  |
| TA Baseline A | 1513 | -256 |
| TA Baseline P | 1440 | -328 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 1-2-16 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 4-2-16 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 4-1-19 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 3-1-24 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 9-5-32 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 5-1-14 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 29-0-1 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 34-8-4 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 19-1-8 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.0 | 33.8 | 32.7 | 35.4 | 36.1 | 31.5 | 32.5 |
|  | vision-gaining moves | 22.1 | 22.2 | 19.9 | 22.9 | 23.5 | 17.9 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.44 | 0.41 | 0.40 | 0.52 | 0.35 | 0.40 |
|  | captures from unseen squares | 9.0 | 10.6 | 8.9 | 10.9 | 12.4 | 8.0 | 8.0 |
|  | captures after a route the other side never saw | 15.4 | 16.2 | 14.9 | 18.3 | 18.3 | 14.4 | 14.6 |
|  | long slider strikes | 4.8 | 5.9 | 4.9 | 6.1 | 5.2 | 4.4 | 4.2 |
| King pressure | moves that attack the enemy king | 3.4 | 4.1 | 2.6 ⚠ | 5.8 | 4.3 | 2.7 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.2 | 2.1 | 0.8 ⚠ | 2.6 | 2.8 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.1 | 0.3 | 0.4 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.5 | 2.8 | 2.2 | 3.5 | 6.0 | 1.9 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.2 | 1.7 | 2.6 ⚠ | 1.0 | 1.2 | 3.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.8 | 2.2 | 3.3 | 2.6 | 1.5 | 4.5 | 2.9 |
|  | queen left attacked by an unseen piece | 0.1 | 0.4 | 0.4 | 0.4 | 0.1 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 5.5 ⚠ | 4.2 | 7.9 ⚠ | 2.7 | 3.6 | 6.2 | 4.8 |
| King handling | king moves | 15.1 | 13.6 | 14.3 | 10.8 | 9.6 | 11.9 | 16.1 |
|  | king moves beyond the second rank | 2.9 | 3.9 | 3.0 | 2.0 | 1.6 | 2.2 | 4.9 |
|  | castling | 1.9 | 2.0 | 2.2 | 2.0 | 2.0 | 2.2 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 26-12-121; 121 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 51 | 18 |
| king already attacked by an unseen piece | 38 | 13 |
| king walked into an unseen attacker after taking the bait (king capture) | 14 | 6 |
| king already attacked by an unseen piece (no safe move existed) | 11 | 6 |
| king left to an attacker we could see (no safe move existed) | 4 | 2 |
| king left to an attacker we could see | 3 | 1 |

Pieces that took our king: r 45, q 43, b 16, n 11, p 2, k 2, pr 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 53, opening (ply < 30) 40, late (70+) or never 3 down 28.
- Down 3 or more at some point in 105 of 121 losses; median first ply 35.
- Down 5 or more in 99; median first ply 45.
- Lost although we had led by 3 or more: 9 of 121.
- Our clock at 15 s or less: 0 of 121.
- Median length 75 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 30 |
| capturer unseen when we moved, piece had just moved there (r) | 17 |
| capturer unseen when we moved, piece had just moved there (q) | 12 |
| capturer unseen when we moved, piece had just moved there (b) | 9 |
| capturer unseen when we moved, piece had just moved there (p) | 7 |
| capturer unseen when we moved (n) | 5 |
| capturer unseen when we moved (r) | 5 |
| other | 4 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved (b) | 3 |
| capturer visible when we moved, piece had just moved there (b) | 2 |
| capturer visible when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (r) | 2 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved (p) | 1 |

## What worked: v30's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| wq5d0hzo | Instructors | B | win | 101 | King capturable |
| denxaibc | Strongly Invisible | W | win | 42 | King capturable |
| 5h4xih5q | Decent Chess Bot | B | win | 85 | King capturable |
| ykpadh8e | duck | B | draw | 109 | Threefold repetition |
| mzjmy3l6 | Greek Gift | W | draw | 125 | Threefold repetition |
| 7seq6wow | duck | W | win | 114 | King capturable |
| 9cw08jfq | Decent Chess Bot | W | win | 58 | King capturable |
| ry2oejta | duck | W | win | 116 | King capturable |
| cjb3jsbm | duck | B | win | 117 | King capturable |
| 8v8q5fh7 | Strongly Invisible | W | draw | 102 | Threefold repetition |
| 4geubeqf | duck | B | draw | 100 | Threefold repetition |
| gr6iofmo | Knight Vision | W | win | 114 | King capturable |
| ee7u7ywy | Knight Vision | B | draw | 99 | Threefold repetition |
| 1q0b4ac9 | Instructors | B | draw | 61 | Threefold repetition |
| oguoh5me | Knight Vision | W | win | 60 | King capturable |
| bnys3dom | duck | B | win | 63 | King capturable |
| hj4jbrrc | duck | W | win | 102 | King capturable |
| zx2qah3c | Strongly Invisible | W | win | 106 | King capturable |
| fxqi02p2 | Instructors | B | win | 87 | King capturable |
| io7zwfom | Instructors | W | win | 128 | King capturable |
| rezmiay9 | Knight Vision | B | win | 49 | King capturable |
| zf3v2fi1 | Decent Chess Bot | W | draw | 58 | Threefold repetition |
| k64y2ljd | Decent Chess Bot | W | win | 72 | King capturable |
| ao41x2q6 | duck | B | win | 95 | King capturable |
| w50mm8vo | Knight Vision | B | draw | 146 | Threefold repetition |
| 8sms0ahj | duck | B | draw | 118 | Threefold repetition |
| 5h7qkspd | Strongly Invisible | W | win | 118 | King capturable |
| mp3hwwum | Instructors | W | win | 90 | King capturable |
| yow099ae | duck | W | win | 72 | King capturable |
| o0zh5ux9 | Greek Gift | B | draw | 110 | Threefold repetition |
| 062hg0t6 | Knight Vision | B | win | 103 | King capturable |
| ryacjw0u | duck | W | draw | 175 | Threefold repetition |
| ll4ddj8r | Decent Chess Bot | W | win | 118 | King capturable |
| 1mn8a3v2 | duck | W | draw | 116 | Threefold repetition |
| h21bwry5 | duck | W | win | 84 | King capturable |
| po23rp14 | Greek Gift | W | win | 148 | King capturable |
| p63nhuqc | duck | B | win | 93 | King capturable |
| 3dfayxek | Instructors | W | win | 130 | King capturable |
