# Against the top six

Updated 2026-10-12 20:29 UTC; leaderboard fetched 2026-10-12T20:29. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2180 | +321 |
| Knight Vision | 2086 | +228 |
| Decent Chess Bot | 2063 | +204 |
| Strongly Invisible | 2060 | +202 |
| **duck** | 1961 | +103 |
| **Instructors** | 1938 | +79 |
| TA Baseline S | 1674 | -185 |
| **IAmAVirus** | 1859 |  |
| TA Baseline A | 1576 | -283 |
| TA Baseline P | 1480 | -379 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 5-0-31 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 16-0-46 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 7-0-35 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 11-1-42 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 19-1-32 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 13-0-29 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 34-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 42-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 39-1-12 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.9 | 33.7 | 32.1 | 35.8 | 35.5 | 31.7 | 32.3 |
|  | vision-gaining moves | 19.8 | 21.5 | 20.1 | 23.2 | 22.8 | 18.9 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.41 | 0.44 | 0.40 | 0.53 | 0.35 | 0.39 |
|  | captures from unseen squares | 9.8 | 10.2 | 10.0 | 11.5 | 13.9 | 8.5 | 7.7 |
|  | captures after a route the other side never saw | 15.0 | 17.0 | 16.2 ⚠ | 20.3 | 19.5 | 16.0 | 14.2 |
|  | long slider strikes | 5.3 | 5.2 | 5.2 | 5.6 | 6.2 | 5.5 | 4.1 |
| King pressure | moves that attack the enemy king | 4.0 | 4.7 | 3.8 ⚠ | 5.4 | 4.8 | 3.6 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.9 | 2.2 | 1.4 ⚠ | 3.1 | 2.8 | 1.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.1 | 0.5 | 0.5 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.3 | 4.6 | 3.2 | 5.1 | 5.0 | 1.9 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.8 ⚠ | 1.9 | 4.5 ⚠ | 1.6 | 1.7 | 3.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.1 | 3.1 | 3.6 ⚠ | 2.3 | 1.5 | 4.1 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.2 | 0.3 | 0.3 | 0.2 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 7.8 ⚠ | 4.3 | 9.6 ⚠ | 2.5 | 4.4 | 5.8 | 4.7 |
| King handling | king moves | 14.9 | 14.2 | 16.5 | 9.7 | 9.7 | 14.0 | 16.1 |
|  | king moves beyond the second rank | 2.7 | 3.5 | 3.7 | 2.1 | 1.8 | 3.0 | 5.2 |
|  | castling | 2.0 | 2.0 | 2.3 | 2.2 | 2.1 | 2.4 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 71-2-215; 215 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 87 | 20 |
| king already attacked by an unseen piece | 50 | 13 |
| king walked into an unseen attacker after taking the bait (king capture) | 43 | 13 |
| king already attacked by an unseen piece (no safe move existed) | 19 | 8 |
| king left to an attacker we could see (no safe move existed) | 12 | 4 |
| our move opened a line from an unseen attacker | 4 | 3 |

Pieces that took our king: q 93, r 90, b 12, n 11, k 3, p 2, qr 2, nq 1, bq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 109, opening (ply < 30) 79, late (70+) or never 3 down 27.
- Down 3 or more at some point in 203 of 215 losses; median first ply 36.
- Down 5 or more in 194; median first ply 42.0.
- Lost although we had led by 3 or more: 15 of 215.
- Our clock at 15 s or less: 0 of 215.
- Median length 74 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 65 |
| capturer unseen when we moved, piece had just moved there (r) | 40 |
| capturer unseen when we moved, piece had just moved there (n) | 30 |
| capturer unseen when we moved, piece had just moved there (b) | 24 |
| capturer unseen when we moved (q) | 10 |
| capturer unseen when we moved (b) | 8 |
| capturer unseen when we moved (r) | 7 |
| capturer visible when we moved, piece had just moved there (n) | 3 |
| capturer unseen when we moved (n) | 3 |
| capturer visible when we moved (p) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer visible when we moved (q) | 2 |
| other | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (r) | 1 |
| capturer visible when we moved (b) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
| 43dabbw9 | Decent Chess Bot | W | win | 70 | King capturable |
| zu9sjnr6 | duck | W | win | 84 | King capturable |
| drnnxb3e | Decent Chess Bot | W | win | 86 | King capturable |
| vf7pjwhn | duck | W | win | 40 | King capturable |
| q9q9m0xi | duck | B | win | 105 | King capturable |
| feab7fld | duck | W | win | 96 | King capturable |
| aextvnui | Strongly Invisible | W | draw | 105 | Threefold repetition |
| ycvp17p2 | duck | B | win | 101 | King capturable |
| d7s2f6wk | duck | W | win | 178 | King capturable |
| bsau1i07 | Knight Vision | W | win | 68 | King capturable |
| 0q9me0sb | Instructors | B | win | 93 | King capturable |
| 8hp9vs48 | Strongly Invisible | W | win | 48 | King capturable |
| 01an1kft | Strongly Invisible | B | win | 105 | King capturable |
| fwvo8f1r | Instructors | W | win | 92 | King capturable |
| fxr67qwn | Greek Gift | W | win | 112 | King capturable |
| 6uar266x | Decent Chess Bot | B | win | 25 | King capturable |
| cnhm1fuv | Decent Chess Bot | W | win | 54 | King capturable |
| w9qqx1o6 | Instructors | B | win | 119 | King capturable |
| ogi8uqdp | Strongly Invisible | B | win | 145 | King capturable |
| v7ktyiix | Knight Vision | W | win | 52 | King capturable |
| tvvbuxsq | Knight Vision | B | win | 73 | King capturable |
| tlp12p59 | Knight Vision | B | win | 51 | King capturable |
| bhinpotr | Knight Vision | B | win | 63 | King capturable |
| 5czrp3gh | duck | W | win | 46 | King capturable |
| q306dmfl | Greek Gift | B | win | 113 | King capturable |
| tcsvy2wq | Instructors | W | win | 90 | King capturable |
| lt2ti00a | Knight Vision | W | win | 40 | King capturable |
| u1sc59rx | Decent Chess Bot | W | win | 72 | King capturable |
| yrfljayz | Strongly Invisible | W | win | 120 | King capturable |
| k2me7228 | Knight Vision | W | win | 72 | King capturable |
| y525aue6 | Decent Chess Bot | W | win | 112 | King capturable |
| nsolnuo2 | Knight Vision | B | win | 63 | King capturable |
| iu8utd4m | Knight Vision | W | win | 78 | King capturable |
| aia0wnjp | duck | B | win | 39 | King capturable |
| fv8eih1b | duck | W | draw | 139 | Threefold repetition |
| oj97cy55 | Greek Gift | W | win | 80 | King capturable |
| 1wu8gw1v | duck | B | win | 103 | King capturable |
| udvd9eq7 | Instructors | B | win | 75 | King capturable |
| ycpjxbk0 | Instructors | B | win | 115 | King capturable |
| bkts8yup | Greek Gift | B | win | 77 | King capturable |
| ibob3d6l | Knight Vision | W | win | 40 | King capturable |
| ti3yccs0 | Strongly Invisible | B | win | 99 | King capturable |
| vzxywc1m | Knight Vision | B | win | 83 | King capturable |
| 280d7c3u | Instructors | W | win | 88 | King capturable |
| rs19o3ma | Instructors | B | win | 103 | King capturable |
| zjtrybuj | duck | W | win | 62 | King capturable |
| 3xmwlps6 | duck | W | win | 130 | King capturable |
| s9mmji2x | Strongly Invisible | B | win | 51 | King capturable |
| d0l3mrye | Instructors | W | win | 86 | King capturable |
| 3x55fanm | duck | W | win | 134 | King capturable |
| okmifjk2 | duck | W | win | 160 | King capturable |
| au7ihfgk | duck | W | win | 128 | King capturable |
| 06y3h5mi | Instructors | W | win | 78 | King capturable |
| 7t4b3qlq | Strongly Invisible | W | win | 72 | King capturable |
| saci0jzm | Knight Vision | W | win | 76 | King capturable |
| qsxstzsj | Knight Vision | W | win | 86 | King capturable |
| n2eyptp5 | Strongly Invisible | W | win | 126 | King capturable |
| abm6h6px | Instructors | W | win | 88 | King capturable |
| t4zawtbq | Knight Vision | B | win | 109 | King capturable |
| dbv7ceav | Knight Vision | W | win | 120 | King capturable |
| 5vx2aco1 | Strongly Invisible | B | win | 65 | King capturable |
| 0sqg0t38 | Greek Gift | W | win | 78 | King capturable |
| lkw1zuie | duck | W | win | 166 | King capturable |
| xd6avdw0 | duck | W | win | 48 | King capturable |
| mp5g7wby | duck | W | win | 44 | King capturable |
| snf9ls9p | duck | B | win | 79 | King capturable |
| ru93csge | Strongly Invisible | B | win | 113 | King capturable |
| parjia0e | Knight Vision | W | win | 134 | King capturable |
| 01n38mp1 | Instructors | W | win | 138 | King capturable |
| iv8uvt6p | Instructors | B | win | 115 | King capturable |
| ghak3i11 | duck | W | win | 108 | King capturable |
