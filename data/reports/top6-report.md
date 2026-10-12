# Against the top six

Updated 2026-10-12 16:40 UTC; leaderboard fetched 2026-10-12T16:39. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2162 | +335 |
| Knight Vision | 2104 | +277 |
| Decent Chess Bot | 2047 | +220 |
| Strongly Invisible | 2056 | +228 |
| **duck** | 1965 | +138 |
| **Instructors** | 1939 | +111 |
| TA Baseline S | 1709 | -118 |
| **IAmAVirus** | 1827 |  |
| TA Baseline A | 1522 | -305 |
| TA Baseline P | 1440 | -387 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 4-0-26 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 13-0-41 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 7-0-33 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 8-1-29 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 14-1-27 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 10-0-26 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 25-0-1 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 36-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 29-0-9 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 33.7 | 32.1 | 35.9 | 35.8 | 31.6 | 32.3 |
|  | vision-gaining moves | 19.3 | 21.9 | 20.0 | 23.6 | 23.0 | 18.8 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.39 | 0.44 | 0.40 | 0.52 | 0.33 | 0.39 |
|  | captures from unseen squares | 9.7 | 9.8 | 10.0 | 11.7 | 13.8 | 8.0 | 7.7 |
|  | captures after a route the other side never saw | 15.0 | 17.0 | 16.2 ⚠ | 20.5 | 19.5 | 15.2 | 14.2 |
|  | long slider strikes | 5.1 | 5.2 | 5.3 | 5.6 | 6.1 | 5.2 | 4.1 |
| King pressure | moves that attack the enemy king | 4.0 | 4.8 | 3.9 ⚠ | 5.3 | 5.0 | 3.6 | 3.2 |
|  | ...with an attacker the king's side cannot see | 2.0 | 2.2 | 1.5 ⚠ | 3.1 | 2.9 | 1.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.2 | 0.4 | 0.5 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.4 | 4.6 | 3.0 | 5.1 | 5.2 | 1.8 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.7 ⚠ | 1.8 | 4.6 ⚠ | 1.6 | 1.6 | 3.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.0 | 3.6 ⚠ | 2.2 | 1.6 | 4.4 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.2 | 0.4 | 0.3 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 8.4 ⚠ | 4.5 | 9.7 ⚠ | 2.3 | 4.7 | 5.7 | 4.7 |
| King handling | king moves | 15.2 | 14.2 | 16.2 | 9.3 | 9.0 | 14.1 | 16.1 |
|  | king moves beyond the second rank | 2.9 | 3.4 | 3.5 | 1.7 | 1.7 | 3.2 | 5.2 |
|  | castling | 2.0 | 2.0 | 2.4 | 2.2 | 2.2 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 56-2-182; 182 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 73 | 18 |
| king already attacked by an unseen piece | 43 | 12 |
| king walked into an unseen attacker after taking the bait (king capture) | 33 | 9 |
| king already attacked by an unseen piece (no safe move existed) | 19 | 8 |
| king left to an attacker we could see (no safe move existed) | 10 | 3 |
| our move opened a line from an unseen attacker | 4 | 3 |

Pieces that took our king: r 82, q 75, n 9, b 8, k 3, p 2, nq 1, qr 1, bq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 93, opening (ply < 30) 66, late (70+) or never 3 down 23.
- Down 3 or more at some point in 171 of 182 losses; median first ply 36.
- Down 5 or more in 165; median first ply 42.
- Lost although we had led by 3 or more: 12 of 182.
- Our clock at 15 s or less: 0 of 182.
- Median length 75.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 55 |
| capturer unseen when we moved, piece had just moved there (r) | 36 |
| capturer unseen when we moved, piece had just moved there (n) | 23 |
| capturer unseen when we moved, piece had just moved there (b) | 19 |
| capturer unseen when we moved (q) | 10 |
| capturer unseen when we moved (b) | 7 |
| capturer unseen when we moved (r) | 5 |
| capturer visible when we moved, piece had just moved there (n) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| other | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved (r) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer visible when we moved (q) | 1 |

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
