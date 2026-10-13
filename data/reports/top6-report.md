# Against the top six

Updated 2026-10-13 22:40 UTC; leaderboard fetched 2026-10-13T22:39. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2291 | +461 |
| Knight Vision | 2099 | +269 |
| Decent Chess Bot | 2071 | +241 |
| Strongly Invisible | 2107 | +277 |
| **duck** | 1996 | +166 |
| **Instructors** | 1905 | +75 |
| TA Baseline S | 1643 | -187 |
| **IAmAVirus** | 1830 |  |
| TA Baseline A | 1546 | -284 |
| TA Baseline P | 1474 | -356 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-1-33 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 5-3-30 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 9-1-36 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 10-0-36 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 13-1-34 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 21-1-36 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 18-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 48-2-4 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 46-0-6 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.3 | 34.0 | 31.8 | 35.2 | 35.3 | 31.7 | 33.1 |
|  | vision-gaining moves | 20.8 | 19.9 | 20.9 | 21.4 | 22.3 | 19.0 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.43 | 0.46 | 0.38 | 0.51 | 0.34 | 0.41 |
|  | captures from unseen squares | 9.5 | 10.1 | 9.4 | 9.8 | 12.1 | 7.5 | 8.5 |
|  | captures after a route the other side never saw | 15.6 | 16.4 | 15.1 | 18.5 | 18.3 | 13.5 | 14.9 |
|  | long slider strikes | 4.6 | 4.7 | 4.6 | 5.4 | 5.5 | 4.6 | 4.3 |
| King pressure | moves that attack the enemy king | 3.1 ⚠ | 4.6 | 2.6 ⚠ | 4.8 | 4.5 | 2.4 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.3 ⚠ | 2.3 | 0.8 ⚠ | 2.4 | 2.8 | 0.5 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.1 | 0.4 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.5 | 4.9 | 3.0 | 4.9 | 4.5 | 1.9 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.5 ⚠ | 1.5 | 4.2 ⚠ | 1.2 | 1.8 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.3 | 3.5 ⚠ | 2.2 | 1.5 | 3.7 | 3.1 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.2 | 0.1 | 0.5 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.9 ⚠ | 4.1 | 7.3 ⚠ | 3.4 | 4.0 | 6.1 | 5.7 |
| King handling | king moves | 16.6 | 12.9 | 17.5 | 11.0 | 9.2 | 13.1 | 15.2 |
|  | king moves beyond the second rank | 4.3 | 3.0 | 5.5 | 2.8 | 1.8 | 2.3 | 4.4 |
|  | castling | 2.1 | 2.0 | 2.1 | 2.2 | 1.9 | 2.2 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 58-7-205; 205 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 90 | 30 |
| king already attacked by an unseen piece | 42 | 14 |
| king walked into an unseen attacker after taking the bait (king capture) | 25 | 8 |
| king already attacked by an unseen piece (no safe move existed) | 24 | 6 |
| king left to an attacker we could see (no safe move existed) | 16 | 8 |
| our move opened a line from an unseen attacker | 8 | 4 |

Pieces that took our king: q 118, r 59, n 13, b 6, k 4, p 2, nq 1, br 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 123, late (70+) or never 3 down 45, opening (ply < 30) 37.
- Down 3 or more at some point in 186 of 205 losses; median first ply 43.0.
- Down 5 or more in 182; median first ply 47.0.
- Lost although we had led by 3 or more: 16 of 205.
- Our clock at 15 s or less: 0 of 205.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 73 |
| capturer unseen when we moved, piece had just moved there (r) | 37 |
| capturer unseen when we moved, piece had just moved there (n) | 18 |
| capturer unseen when we moved, piece had just moved there (b) | 13 |
| capturer unseen when we moved (q) | 9 |
| capturer unseen when we moved (b) | 7 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (r) | 5 |
| capturer unseen when we moved (p) | 4 |
| other | 4 |
| capturer visible when we moved (q) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer visible when we moved (b) | 2 |
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
| a9wciyvi | Instructors | W | win | 14 | King capturable |
| qqm0fhjh | Instructors | B | draw | 99 | Threefold repetition |
| ro7jj10j | Instructors | B | win | 95 | King capturable |
| 0r1k86vv | Instructors | W | win | 84 | King capturable |
| 3x8iwche | Strongly Invisible | B | win | 111 | King capturable |
| riym93ih | Instructors | B | win | 101 | King capturable |
| toe238b5 | Strongly Invisible | W | win | 86 | King capturable |
| 98aje6v3 | duck | W | win | 100 | King capturable |
| dzmazevd | duck | B | win | 207 | King capturable |
| p2ggmgpc | Decent Chess Bot | W | draw | 80 | Threefold repetition |
| ppk3o8v8 | Knight Vision | W | win | 68 | King capturable |
| kw938q3t | Knight Vision | W | win | 46 | King capturable |
| 5ytc7zxa | Instructors | W | win | 84 | King capturable |
| o8qo5hn8 | Strongly Invisible | W | win | 104 | King capturable |
| dktsyigf | Decent Chess Bot | B | win | 123 | King capturable |
| bjjjgdns | Decent Chess Bot | B | win | 71 | King capturable |
| 8cmvjx19 | Decent Chess Bot | W | win | 134 | King capturable |
| sc4puuvs | Greek Gift | W | draw | 121 | Threefold repetition |
| zpal1iv1 | duck | B | win | 103 | King capturable |
| spbqputi | duck | W | win | 36 | King capturable |
| szl1j9ku | Instructors | W | win | 104 | King capturable |
