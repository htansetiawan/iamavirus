# Against the top six

Updated 2026-10-11 19:53 UTC; leaderboard fetched 2026-10-11T19:52. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2144 | +365 |
| Knight Vision | 2069 | +290 |
| Decent Chess Bot | 2062 | +282 |
| Strongly Invisible | 2045 | +265 |
| **duck** | 1950 | +171 |
| **Instructors** | 1895 | +116 |
| TA Baseline S | 1683 | -97 |
| **IAmAVirus** | 1780 |  |
| TA Baseline A | 1523 | -257 |
| TA Baseline P | 1413 | -367 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 2-2-18 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 10-3-21 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 5-1-24 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 4-1-29 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 9-5-36 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 8-1-25 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 38-0-2 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 42-8-6 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 23-2-13 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.6 | 33.8 | 32.8 | 35.3 | 36.0 | 31.8 | 32.3 |
|  | vision-gaining moves | 21.8 | 21.4 | 20.8 | 22.8 | 23.3 | 18.2 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.44 | 0.42 | 0.39 | 0.52 | 0.35 | 0.40 |
|  | captures from unseen squares | 8.8 | 10.6 | 9.1 | 10.5 | 12.5 | 8.2 | 7.9 |
|  | captures after a route the other side never saw | 15.1 | 15.9 | 15.1 | 18.2 | 17.9 | 14.7 | 14.6 |
|  | long slider strikes | 4.8 | 5.6 | 4.9 | 5.6 | 5.6 | 4.6 | 4.2 |
| King pressure | moves that attack the enemy king | 3.5 | 4.4 | 3.2 ⚠ | 5.6 | 4.2 | 2.7 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.1 ⚠ | 2.3 | 1.3 ⚠ | 2.5 | 2.7 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.1 | 0.2 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.5 | 2.7 | 2.8 | 3.4 | 5.5 | 2.1 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.4 | 1.7 | 2.4 ⚠ | 1.1 | 1.4 | 3.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.5 | 2.3 | 3.5 | 2.5 | 1.6 | 4.4 | 2.8 |
|  | queen left attacked by an unseen piece | 0.1 | 0.3 | 0.3 | 0.3 | 0.0 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 5.4 ⚠ | 4.0 | 7.9 ⚠ | 3.5 | 3.6 | 5.8 | 5.0 |
| King handling | king moves | 16.2 | 13.6 | 14.7 | 11.1 | 9.6 | 11.1 | 16.4 |
|  | king moves beyond the second rank | 3.9 | 4.0 | 3.1 | 2.3 | 1.6 | 1.9 | 5.1 |
|  | castling | 1.9 | 1.9 | 2.1 | 2.1 | 2.1 | 2.2 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 38-13-153; 153 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 67 | 25 |
| king already attacked by an unseen piece | 46 | 18 |
| king walked into an unseen attacker after taking the bait (king capture) | 20 | 9 |
| king already attacked by an unseen piece (no safe move existed) | 12 | 6 |
| king left to an attacker we could see (no safe move existed) | 4 | 2 |
| king left to an attacker we could see | 3 | 1 |
| our move opened a line from an unseen attacker | 1 | 0 |

Pieces that took our king: q 59, r 58, b 17, n 12, p 2, k 2, pr 1, nq 1, nr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 70, opening (ply < 30) 47, late (70+) or never 3 down 36.
- Down 3 or more at some point in 131 of 153 losses; median first ply 35.
- Down 5 or more in 122; median first ply 45.5.
- Lost although we had led by 3 or more: 13 of 153.
- Our clock at 15 s or less: 0 of 153.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 33 |
| capturer unseen when we moved, piece had just moved there (r) | 25 |
| capturer unseen when we moved, piece had just moved there (q) | 15 |
| capturer unseen when we moved, piece had just moved there (b) | 13 |
| capturer unseen when we moved, piece had just moved there (p) | 7 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (r) | 6 |
| other | 5 |
| capturer unseen when we moved (q) | 4 |
| capturer visible when we moved, piece had just moved there (b) | 3 |
| capturer visible when we moved (p) | 3 |
| capturer unseen when we moved (b) | 3 |
| capturer unseen when we moved (p) | 3 |
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
