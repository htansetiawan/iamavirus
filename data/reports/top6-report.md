# Against the top six

Updated 2026-10-12 06:36 UTC; leaderboard fetched 2026-10-12T06:36. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2128 | +300 |
| Knight Vision | 2138 | +310 |
| Decent Chess Bot | 2068 | +240 |
| Strongly Invisible | 2065 | +236 |
| **duck** | 1979 | +151 |
| **Instructors** | 1912 | +83 |
| TA Baseline S | 1634 | -194 |
| **IAmAVirus** | 1828 |  |
| TA Baseline A | 1510 | -318 |
| TA Baseline P | 1448 | -380 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 2-0-14 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 6-0-18 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 5-0-19 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 4-1-7 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 7-0-11 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 4-0-14 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 8-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 20-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 12-0-4 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 33.8 | 32.6 | 35.5 | 36.3 | 31.5 | 32.7 |
|  | vision-gaining moves | 19.5 | 21.2 | 19.2 | 23.0 | 22.0 | 18.1 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.42 | 0.45 | 0.41 | 0.54 | 0.34 | 0.40 |
|  | captures from unseen squares | 10.5 | 10.9 | 10.2 | 11.4 | 14.2 | 8.1 | 8.3 |
|  | captures after a route the other side never saw | 15.8 | 18.1 | 16.1 | 19.6 | 19.0 | 15.8 | 15.0 |
|  | long slider strikes | 5.3 | 5.6 | 5.0 | 5.4 | 6.3 | 5.2 | 4.4 |
| King pressure | moves that attack the enemy king | 3.9 | 4.6 | 4.6 | 4.6 | 5.5 | 3.2 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.9 | 2.1 | 2.0 | 2.8 | 3.0 | 0.9 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.4 | 0.2 | 0.3 | 0.6 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.5 | 3.9 | 3.3 | 5.0 | 5.8 | 1.9 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.7 ⚠ | 1.6 | 4.6 ⚠ | 1.6 | 1.7 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.3 | 3.7 | 3.5 | 2.7 | 1.8 | 4.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.4 | 0.2 | 0.4 | 0.3 | 0.3 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 10.5 ⚠ | 3.5 | 9.3 ⚠ | 2.7 | 5.0 | 5.9 | 5.3 |
| King handling | king moves | 13.7 | 13.7 | 15.1 | 10.3 | 7.8 | 15.6 | 15.8 |
|  | king moves beyond the second rank | 2.1 | 5.3 | 3.7 | 1.9 | 1.2 | 3.7 | 5.0 |
|  | castling | 2.1 | 1.9 | 2.4 | 2.1 | 2.3 | 2.3 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 28-1-83; 83 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 31 | 9 |
| king already attacked by an unseen piece | 21 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 13 | 7 |
| king walked into an unseen attacker after taking the bait (king capture) | 13 | 5 |
| king left to an attacker we could see (no safe move existed) | 4 | 0 |
| our move opened a line from an unseen attacker | 1 | 0 |

Pieces that took our king: r 41, q 31, n 4, b 3, k 2, p 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 43, opening (ply < 30) 29, late (70+) or never 3 down 11.
- Down 3 or more at some point in 78 of 83 losses; median first ply 37.5.
- Down 5 or more in 73; median first ply 42.
- Lost although we had led by 3 or more: 7 of 83.
- Our clock at 15 s or less: 0 of 83.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 27 |
| capturer unseen when we moved, piece had just moved there (r) | 16 |
| capturer unseen when we moved, piece had just moved there (n) | 11 |
| capturer unseen when we moved, piece had just moved there (b) | 7 |
| capturer unseen when we moved (q) | 6 |
| capturer unseen when we moved (r) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved (b) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
| capturer unseen when we moved (p) | 1 |
| other | 1 |
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
