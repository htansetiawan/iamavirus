# Against the top six

Updated 2026-10-13 10:16 UTC; leaderboard fetched 2026-10-13T10:15. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2254 | +345 |
| Knight Vision | 2120 | +210 |
| Decent Chess Bot | 2070 | +161 |
| Strongly Invisible | 2050 | +141 |
| **duck** | 1987 | +78 |
| **Instructors** | 1956 | +47 |
| TA Baseline S | 1690 | -219 |
| **IAmAVirus** | 1909 |  |
| TA Baseline A | 1539 | -371 |
| TA Baseline P | 1468 | -441 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-14 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 3-1-10 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 5-0-21 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 5-0-13 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 6-1-19 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 13-0-13 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 10-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 26-2-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 28-0-2 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 34.3 | 31.8 | 35.1 | 35.0 | 31.1 | 32.4 |
|  | vision-gaining moves | 22.4 | 20.2 | 21.1 | 21.5 | 21.7 | 18.1 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.40 | 0.48 | 0.40 | 0.49 | 0.34 | 0.39 |
|  | captures from unseen squares | 9.9 | 9.7 | 9.5 | 10.1 | 11.5 | 7.2 | 7.9 |
|  | captures after a route the other side never saw | 16.4 | 16.4 | 14.7 ⚠ | 18.4 | 17.9 | 12.7 | 14.3 |
|  | long slider strikes | 5.1 | 4.9 | 4.7 | 5.8 | 5.0 | 4.5 | 4.1 |
| King pressure | moves that attack the enemy king | 3.6 | 4.2 | 2.4 ⚠ | 5.2 | 4.7 | 2.3 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.6 | 2.2 | 0.5 ⚠ | 2.7 | 3.1 | 0.5 | 1.5 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.1 | 0.4 | 0.7 | 0.0 | 0.1 |
| Queen activity | queen moves into the enemy half | 4.7 | 5.0 | 3.4 | 4.0 | 4.7 | 1.9 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.2 ⚠ | 1.4 | 4.3 ⚠ | 1.4 | 1.7 | 3.4 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.3 | 3.0 | 2.2 | 1.6 | 3.9 | 2.8 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.3 | 0.2 | 0.1 | 0.5 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 5.9 ⚠ | 4.5 | 7.3 ⚠ | 3.2 | 4.8 | 5.3 | 5.0 |
| King handling | king moves | 16.4 | 12.0 | 17.5 | 10.6 | 10.2 | 14.8 | 15.9 |
|  | king moves beyond the second rank | 5.1 | 3.1 | 6.7 | 2.4 | 2.4 | 2.9 | 5.0 |
|  | castling | 2.3 | 2.3 | 2.1 | 2.2 | 1.8 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 32-2-90; 90 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 35 | 15 |
| king already attacked by an unseen piece | 19 | 6 |
| king already attacked by an unseen piece (no safe move existed) | 12 | 5 |
| king walked into an unseen attacker after taking the bait (king capture) | 11 | 2 |
| king left to an attacker we could see (no safe move existed) | 9 | 3 |
| our move opened a line from an unseen attacker | 4 | 1 |

Pieces that took our king: q 50, r 27, n 5, b 4, k 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 55, late (70+) or never 3 down 20, opening (ply < 30) 15.
- Down 3 or more at some point in 82 of 90 losses; median first ply 43.5.
- Down 5 or more in 78; median first ply 48.0.
- Lost although we had led by 3 or more: 8 of 90.
- Our clock at 15 s or less: 0 of 90.
- Median length 76.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 33 |
| capturer unseen when we moved, piece had just moved there (r) | 16 |
| capturer unseen when we moved, piece had just moved there (b) | 7 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved (b) | 4 |
| capturer unseen when we moved (q) | 3 |
| capturer visible when we moved (q) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved (b) | 2 |
| capturer unseen when we moved (r) | 2 |
| other | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v34's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| gzj7ox1o | Instructors | W | win | 66 | King capturable |
| y4qk2v2b | Instructors | B | win | 9 | King capturable |
| np6c6tub | Instructors | B | win | 61 | King capturable |
| 05l0ejxw | Instructors | W | win | 66 | King capturable |
| 19pwd8n9 | Knight Vision | W | win | 50 | King capturable |
| sdr3y95n | Decent Chess Bot | W | win | 138 | King capturable |
| znv5996o | duck | W | win | 44 | King capturable |
| u5hyxqe5 | duck | B | win | 61 | King capturable |
| sjyd7bcw | duck | W | win | 86 | King capturable |
| wnso8ft4 | duck | B | win | 107 | King capturable |
| n3e191mm | Instructors | B | win | 45 | King capturable |
| p5k8pu4u | Instructors | W | win | 68 | King capturable |
| n9entvtq | duck | B | win | 101 | King capturable |
| frmdez59 | Instructors | W | win | 66 | King capturable |
| bd2qdd48 | Instructors | B | win | 87 | King capturable |
| qo7iigz9 | Strongly Invisible | B | win | 9 | King capturable |
| fkt72pd8 | Instructors | W | win | 102 | King capturable |
| wz467mbn | Instructors | W | win | 96 | King capturable |
| dgdbtyya | Decent Chess Bot | W | win | 96 | King capturable |
| tbbl82pn | Decent Chess Bot | W | win | 50 | King capturable |
| 17fl1nq7 | Decent Chess Bot | B | win | 79 | King capturable |
| iwo0axp7 | Strongly Invisible | B | win | 153 | King capturable |
| mqfh05o1 | Knight Vision | B | draw | 160 | Threefold repetition |
| jo0cu337 | Strongly Invisible | W | win | 60 | King capturable |
| bq2vio40 | Strongly Invisible | B | win | 101 | King capturable |
| e1v2pu2s | Knight Vision | B | win | 29 | King capturable |
| pdsihv7f | Knight Vision | W | win | 58 | King capturable |
| 4nun0itq | Instructors | B | win | 93 | King capturable |
| 90qk1vsr | duck | W | draw | 101 | Threefold repetition |
| gted2lyt | Strongly Invisible | B | win | 125 | King capturable |
| o1zk47ek | duck | B | win | 75 | King capturable |
| 8qruqdt1 | Decent Chess Bot | B | win | 61 | King capturable |
| bhyq3nht | Instructors | W | win | 40 | King capturable |
| np3pbx8c | Instructors | B | win | 91 | King capturable |
