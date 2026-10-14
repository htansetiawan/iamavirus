# Against the top six

Updated 2026-10-14 04:16 UTC; leaderboard fetched 2026-10-14T04:16. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2268 | +403 |
| Knight Vision | 2124 | +259 |
| Decent Chess Bot | 2035 | +170 |
| Strongly Invisible | 2075 | +210 |
| **duck** | 1999 | +134 |
| **Instructors** | 1911 | +46 |
| TA Baseline S | 1677 | -188 |
| **IAmAVirus** | 1865 |  |
| TA Baseline A | 1552 | -312 |
| TA Baseline P | 1477 | -388 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 6-3-35 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 12-0-42 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 26-2-42 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 24-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 51-0-7 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.4 | 34.0 | 31.8 | 35.1 | 35.3 | 31.7 | 33.1 |
|  | vision-gaining moves | 20.9 | 19.7 | 20.6 | 21.4 | 22.5 | 19.0 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.42 | 0.45 | 0.38 | 0.50 | 0.34 | 0.41 |
|  | captures from unseen squares | 9.6 | 10.1 | 9.1 | 9.7 | 12.1 | 7.5 | 8.5 |
|  | captures after a route the other side never saw | 15.8 | 16.4 | 14.9 | 18.5 | 18.5 | 13.5 | 14.9 |
|  | long slider strikes | 4.8 | 4.6 | 4.6 | 5.1 | 5.5 | 4.6 | 4.3 |
| King pressure | moves that attack the enemy king | 3.5 ⚠ | 4.5 | 2.6 ⚠ | 4.7 | 4.4 | 2.4 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.5 | 2.2 | 0.9 ⚠ | 2.3 | 2.7 | 0.5 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.1 | 0.3 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.7 | 4.4 | 2.9 | 4.8 | 4.8 | 1.8 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.3 ⚠ | 1.7 | 4.1 ⚠ | 1.1 | 1.8 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.4 | 3.5 ⚠ | 2.2 | 1.6 | 3.7 | 3.1 |
|  | queen left attacked by an unseen piece | 0.3 | 0.2 | 0.2 | 0.2 | 0.1 | 0.6 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 7.0 ⚠ | 4.2 | 7.5 ⚠ | 3.6 | 4.1 | 6.0 | 5.7 |
| King handling | king moves | 16.9 | 12.6 | 17.6 | 11.4 | 9.2 | 12.6 | 15.2 |
|  | king moves beyond the second rank | 4.4 | 3.0 | 5.4 | 2.9 | 1.9 | 2.1 | 4.4 |
|  | castling | 2.1 | 2.0 | 2.1 | 2.2 | 2.0 | 2.2 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 73-8-243; 243 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 116 | 40 |
| king already attacked by an unseen piece | 47 | 15 |
| king walked into an unseen attacker after taking the bait (king capture) | 28 | 11 |
| king already attacked by an unseen piece (no safe move existed) | 25 | 7 |
| king left to an attacker we could see (no safe move existed) | 18 | 8 |
| our move opened a line from an unseen attacker | 9 | 5 |

Pieces that took our king: q 131, r 78, n 13, b 9, k 6, p 2, qr 2, nq 1, br 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 147, late (70+) or never 3 down 53, opening (ply < 30) 43.
- Down 3 or more at some point in 223 of 243 losses; median first ply 43.
- Down 5 or more in 219; median first ply 48.
- Lost although we had led by 3 or more: 19 of 243.
- Our clock at 15 s or less: 0 of 243.
- Median length 79 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 82 |
| capturer unseen when we moved, piece had just moved there (r) | 47 |
| capturer unseen when we moved, piece had just moved there (n) | 24 |
| capturer unseen when we moved, piece had just moved there (b) | 16 |
| capturer unseen when we moved (q) | 9 |
| capturer unseen when we moved (b) | 8 |
| capturer unseen when we moved (r) | 6 |
| capturer unseen when we moved (n) | 6 |
| other | 6 |
| capturer unseen when we moved (p) | 5 |
| capturer visible when we moved (q) | 4 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer visible when we moved (b) | 2 |
| capturer visible when we moved (n) | 1 |
| capturer visible when we moved (r) | 1 |
| capturer visible when we moved, piece had just moved there (n) | 1 |
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
| mkcygww5 | Greek Gift | W | win | 72 | King capturable |
| 261ktm5x | duck | B | win | 85 | King capturable |
| 49ffudf7 | Instructors | B | win | 85 | King capturable |
| ulxqmous | Instructors | W | win | 108 | King capturable |
| 115fm1yb | Instructors | W | draw | 79 | Threefold repetition |
| 3j22jsfv | Decent Chess Bot | W | win | 144 | King capturable |
| lqi5xje0 | Strongly Invisible | W | win | 116 | King capturable |
| j5d1uk21 | Strongly Invisible | B | win | 123 | King capturable |
| el516obe | duck | W | win | 62 | King capturable |
| z249297c | Decent Chess Bot | B | win | 81 | King capturable |
| nlcifw0n | Instructors | B | win | 65 | King capturable |
| 1fzfwaps | Decent Chess Bot | W | win | 56 | King capturable |
| rf69681c | Knight Vision | B | win | 37 | King capturable |
| t29klooy | Decent Chess Bot | W | win | 38 | King capturable |
| z52qn5mv | Instructors | W | win | 56 | King capturable |
| kr5fdvd6 | Instructors | B | win | 91 | King capturable |
