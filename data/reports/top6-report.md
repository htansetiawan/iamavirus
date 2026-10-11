# Against the top six

Updated 2026-10-11 21:57 UTC; leaderboard fetched 2026-10-11T21:57. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2161 | +383 |
| Knight Vision | 2075 | +297 |
| Decent Chess Bot | 2036 | +257 |
| Strongly Invisible | 2065 | +287 |
| **duck** | 1972 | +193 |
| **Instructors** | 1908 | +130 |
| TA Baseline S | 1650 | -128 |
| **IAmAVirus** | 1778 |  |
| TA Baseline A | 1518 | -260 |
| TA Baseline P | 1419 | -359 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 2-2-24 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 12-3-25 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 6-1-27 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 4-1-31 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 9-5-36 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 9-3-32 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 47-1-2 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 25-4-15 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.2 | 33.5 | 32.5 | 35.3 | 35.8 | 31.6 | 32.9 |
|  | vision-gaining moves | 21.6 | 21.2 | 20.6 | 23.3 | 23.2 | 18.2 | 19.3 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.39 | 0.44 | 0.42 | 0.39 | 0.52 | 0.36 | 0.40 |
|  | captures from unseen squares | 8.7 | 10.5 | 9.1 | 10.7 | 12.6 | 8.2 | 8.5 |
|  | captures after a route the other side never saw | 14.9 | 16.0 | 15.1 | 18.5 | 17.9 | 14.5 | 15.3 |
|  | long slider strikes | 4.7 | 5.4 | 4.9 | 5.6 | 5.7 | 4.5 | 4.5 |
| King pressure | moves that attack the enemy king | 3.3 ⚠ | 4.4 | 3.2 ⚠ | 5.6 | 4.2 | 2.8 | 3.7 |
|  | ...with an attacker the king's side cannot see | 1.1 ⚠ | 2.3 | 1.2 ⚠ | 2.6 | 2.6 | 0.7 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.1 | 0.2 | 0.4 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.5 | 3.0 | 2.7 | 3.3 | 5.2 | 2.0 | 3.2 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.3 | 1.5 | 2.4 ⚠ | 1.1 | 1.3 | 3.4 | 1.8 |
|  | pieces walked onto squares hit by unseen attackers | 2.5 | 2.2 | 3.5 | 2.5 | 1.8 | 4.3 | 3.1 |
|  | queen left attacked by an unseen piece | 0.1 | 0.3 | 0.3 | 0.3 | 0.0 | 0.5 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 5.4 ⚠ | 3.9 | 8.1 ⚠ | 3.3 | 3.7 | 6.5 | 5.1 |
| King handling | king moves | 17.1 | 14.4 | 15.3 | 10.8 | 9.7 | 11.8 | 15.0 |
|  | king moves beyond the second rank | 5.2 | 4.7 | 3.1 | 2.2 | 1.6 | 1.8 | 4.6 |
|  | castling | 1.9 | 1.9 | 2.1 | 2.1 | 2.1 | 2.2 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 42-15-175; 175 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 80 | 28 |
| king already attacked by an unseen piece | 53 | 21 |
| king walked into an unseen attacker after taking the bait (king capture) | 21 | 9 |
| king already attacked by an unseen piece (no safe move existed) | 12 | 6 |
| king left to an attacker we could see (no safe move existed) | 4 | 2 |
| king left to an attacker we could see | 3 | 1 |
| our move opened a line from an unseen attacker | 2 | 1 |

Pieces that took our king: r 68, q 64, b 18, n 16, p 2, qr 2, k 2, pr 1, nq 1, nr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 81, opening (ply < 30) 54, late (70+) or never 3 down 40.
- Down 3 or more at some point in 151 of 175 losses; median first ply 35.
- Down 5 or more in 141; median first ply 46.
- Lost although we had led by 3 or more: 14 of 175.
- Our clock at 15 s or less: 0 of 175.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 38 |
| capturer unseen when we moved, piece had just moved there (r) | 27 |
| capturer unseen when we moved, piece had just moved there (q) | 20 |
| capturer unseen when we moved, piece had just moved there (b) | 16 |
| capturer unseen when we moved (r) | 8 |
| capturer unseen when we moved, piece had just moved there (p) | 7 |
| other | 6 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved (b) | 4 |
| capturer unseen when we moved (p) | 4 |
| capturer visible when we moved, piece had just moved there (b) | 3 |
| capturer visible when we moved (p) | 3 |
| capturer visible when we moved, piece had just moved there (r) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (b) | 1 |

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
| bzktbcbx | Greek Gift | B | win | 107 | King capturable |
| wr7fk78w | Instructors | W | win | 72 | King capturable |
| th5onbf2 | Knight Vision | W | draw | 92 | Threefold repetition |
| kp3etogz | Instructors | B | win | 121 | King capturable |
| ub3ngrkt | Knight Vision | B | win | 45 | King capturable |
| b4c61fg2 | Knight Vision | W | win | 86 | King capturable |
| fnvg5xnm | Strongly Invisible | W | win | 152 | King capturable |
| up9cuirj | Decent Chess Bot | W | win | 100 | King capturable |
| rykix63s | Knight Vision | W | win | 84 | King capturable |
| jjtyd01f | Knight Vision | B | win | 67 | King capturable |
| 6nz43kad | Knight Vision | W | win | 92 | King capturable |
| y9vrfr4d | Knight Vision | B | win | 45 | King capturable |
| o5es08kx | Instructors | B | win | 63 | King capturable |
| o2nczcra | Instructors | B | draw | 157 | Threefold repetition |
| v0xg1gfc | Knight Vision | W | win | 40 | King capturable |
| atwgxhg1 | Knight Vision | B | win | 99 | King capturable |
| nvibkhlm | Instructors | B | win | 99 | King capturable |
| 0xl3bciw | Instructors | W | draw | 169 | Threefold repetition |
| z38tk7yx | Decent Chess Bot | B | win | 99 | King capturable |
