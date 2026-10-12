# Against the top six

Updated 2026-10-12 11:49 UTC; leaderboard fetched 2026-10-12T11:48. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2115 | +280 |
| Knight Vision | 2129 | +295 |
| Decent Chess Bot | 2067 | +232 |
| Strongly Invisible | 2065 | +231 |
| **duck** | 1948 | +113 |
| **Instructors** | 1919 | +85 |
| TA Baseline S | 1693 | -142 |
| **IAmAVirus** | 1835 |  |
| TA Baseline A | 1513 | -322 |
| TA Baseline P | 1433 | -401 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 4-0-22 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 10-0-32 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 7-0-27 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 6-1-21 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 9-1-20 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 6-0-19 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 17-0-1 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 30-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 21-0-5 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 34.3 | 32.2 | 35.8 | 35.7 | 31.1 | 32.3 |
|  | vision-gaining moves | 19.2 | 21.8 | 19.9 | 23.3 | 21.9 | 18.7 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.41 | 0.45 | 0.41 | 0.52 | 0.34 | 0.39 |
|  | captures from unseen squares | 9.9 | 10.2 | 10.2 | 11.8 | 13.8 | 8.1 | 7.7 |
|  | captures after a route the other side never saw | 15.0 | 17.1 | 16.4 | 20.4 | 19.5 | 15.0 | 14.2 |
|  | long slider strikes | 5.2 | 5.4 | 5.2 | 5.7 | 5.8 | 5.1 | 4.1 |
| King pressure | moves that attack the enemy king | 4.1 | 4.9 | 4.1 ⚠ | 5.3 | 4.7 | 3.3 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.9 | 2.5 | 1.6 ⚠ | 3.2 | 2.7 | 0.8 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.2 | 0.4 | 0.6 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.8 | 5.1 | 3.0 | 5.2 | 4.9 | 1.7 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.8 ⚠ | 1.5 | 4.7 ⚠ | 1.7 | 1.7 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.2 | 3.7 ⚠ | 2.3 | 1.6 | 4.2 | 3.0 |
|  | queen left attacked by an unseen piece | 0.4 | 0.2 | 0.4 | 0.3 | 0.2 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 9.0 ⚠ | 4.1 | 9.5 ⚠ | 2.6 | 4.9 | 6.1 | 4.7 |
| King handling | king moves | 15.9 | 12.5 | 16.0 | 9.4 | 8.9 | 15.3 | 16.1 |
|  | king moves beyond the second rank | 2.7 | 4.4 | 3.7 | 1.7 | 1.7 | 3.7 | 5.2 |
|  | castling | 2.1 | 1.9 | 2.3 | 2.2 | 2.2 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 42-2-141; 141 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 58 | 11 |
| king already attacked by an unseen piece | 35 | 10 |
| king walked into an unseen attacker after taking the bait (king capture) | 21 | 6 |
| king already attacked by an unseen piece (no safe move existed) | 16 | 8 |
| king left to an attacker we could see (no safe move existed) | 8 | 2 |
| our move opened a line from an unseen attacker | 3 | 2 |

Pieces that took our king: r 68, q 56, n 7, b 4, p 2, k 2, nq 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 72, opening (ply < 30) 51, late (70+) or never 3 down 18.
- Down 3 or more at some point in 133 of 141 losses; median first ply 37.
- Down 5 or more in 128; median first ply 42.0.
- Lost although we had led by 3 or more: 10 of 141.
- Our clock at 15 s or less: 0 of 141.
- Median length 74 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 41 |
| capturer unseen when we moved, piece had just moved there (r) | 29 |
| capturer unseen when we moved, piece had just moved there (n) | 19 |
| capturer unseen when we moved, piece had just moved there (b) | 11 |
| capturer unseen when we moved (q) | 10 |
| capturer unseen when we moved (b) | 6 |
| capturer unseen when we moved (r) | 4 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| other | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer unseen when we moved (p) | 1 |
| capturer visible when we moved (r) | 1 |
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
