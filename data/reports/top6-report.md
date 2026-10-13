# Against the top six

Updated 2026-10-13 11:59 UTC; leaderboard fetched 2026-10-13T11:59. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2261 | +336 |
| Knight Vision | 2093 | +168 |
| Decent Chess Bot | 2065 | +140 |
| Strongly Invisible | 2069 | +144 |
| **duck** | 1990 | +65 |
| **Instructors** | 1966 | +41 |
| TA Baseline S | 1685 | -240 |
| **IAmAVirus** | 1925 |  |
| TA Baseline A | 1530 | -395 |
| TA Baseline P | 1461 | -464 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-20 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 3-3-12 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 6-0-24 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 7-0-15 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 9-1-20 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 15-0-17 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 10-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 26-2-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 32-0-2 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.1 | 34.3 | 31.5 | 34.9 | 35.0 | 31.3 | 33.1 |
|  | vision-gaining moves | 22.4 | 20.1 | 20.8 | 21.1 | 21.6 | 18.2 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.41 | 0.47 | 0.39 | 0.49 | 0.34 | 0.41 |
|  | captures from unseen squares | 9.8 | 9.9 | 9.5 | 9.8 | 11.4 | 7.3 | 8.5 |
|  | captures after a route the other side never saw | 15.9 | 15.9 | 14.8 ⚠ | 18.5 | 17.8 | 12.9 | 14.9 |
|  | long slider strikes | 5.2 | 4.7 | 4.5 ⚠ | 5.8 | 5.2 | 4.5 | 4.3 |
| King pressure | moves that attack the enemy king | 3.7 | 4.2 | 2.6 ⚠ | 5.0 | 4.9 | 2.3 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.7 | 2.2 | 0.8 ⚠ | 2.7 | 3.1 | 0.4 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.1 | 0.4 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.9 | 4.8 | 3.3 | 4.7 | 4.6 | 1.9 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.1 ⚠ | 1.4 | 4.1 ⚠ | 1.3 | 1.8 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 | 2.6 | 3.0 | 2.2 | 1.7 | 3.8 | 3.1 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.2 | 0.1 | 0.1 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 5.7 ⚠ | 4.5 | 7.7 ⚠ | 3.1 | 4.7 | 5.5 | 5.7 |
| King handling | king moves | 15.9 | 12.0 | 18.4 | 11.9 | 9.9 | 14.6 | 15.2 |
|  | king moves beyond the second rank | 4.9 | 3.2 | 7.3 | 2.9 | 2.3 | 2.7 | 4.4 |
|  | castling | 2.3 | 2.2 | 2.1 | 2.2 | 1.8 | 2.1 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 40-4-108; 108 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 42 | 16 |
| king already attacked by an unseen piece | 23 | 8 |
| king already attacked by an unseen piece (no safe move existed) | 15 | 6 |
| king walked into an unseen attacker after taking the bait (king capture) | 14 | 3 |
| king left to an attacker we could see (no safe move existed) | 10 | 3 |
| our move opened a line from an unseen attacker | 4 | 1 |

Pieces that took our king: q 62, r 32, n 6, b 4, k 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 65, late (70+) or never 3 down 25, opening (ply < 30) 18.
- Down 3 or more at some point in 98 of 108 losses; median first ply 43.0.
- Down 5 or more in 94; median first ply 48.0.
- Lost although we had led by 3 or more: 9 of 108.
- Our clock at 15 s or less: 0 of 108.
- Median length 76.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 39 |
| capturer unseen when we moved, piece had just moved there (r) | 19 |
| capturer unseen when we moved, piece had just moved there (b) | 8 |
| capturer unseen when we moved, piece had just moved there (n) | 7 |
| capturer unseen when we moved (b) | 4 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved (p) | 3 |
| capturer visible when we moved (q) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved (b) | 2 |
| other | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
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
| wvb70h0v | Knight Vision | W | draw | 97 | Threefold repetition |
| nt4qf9fl | Knight Vision | B | draw | 138 | Threefold repetition |
| cw96qyk8 | duck | B | win | 47 | King capturable |
| iso3xl9u | Instructors | B | win | 97 | King capturable |
| fziyxy3g | Instructors | W | win | 92 | King capturable |
| iephcpwl | duck | B | win | 5 | King capturable |
| m9sg9bhc | Decent Chess Bot | B | win | 85 | King capturable |
| y8vbimyh | duck | W | win | 148 | King capturable |
| 0jl9lbsc | Strongly Invisible | W | win | 96 | King capturable |
| 2befnpma | Strongly Invisible | B | win | 135 | King capturable |
