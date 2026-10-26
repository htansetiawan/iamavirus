# Arena insights, 2026-10-26 14:58 UTC

Our active version: v35. Window: 7 days (28673 games of all teams).

Current leaders at the latest snapshot (2026-10-26 10:13 UTC): Greek Gift, Knight Vision, Strongly Invisible, Decent Chess Bot, Crimson Fog, duck. Sections 3 and 4 use the fixed 13 October top six (Greek Gift, Knight Vision, Strongly Invisible, Decent Chess Bot, duck, Instructors), kept fixed for comparison over time; not in today's top six: Instructors; in today's but not the cohort: Crimson Fog.

## 1. Opponents' versions in the window, and our score against each

| opponent | versions seen (games) | our score by version |
|---|---|---|
| HYPOTHERMIA **changed** | v1 (504), v2 (546), v3 (2264) | v1: 19/30, v2: 31/54, v3: 102/180 |
| Gravel Road | v4 (3294) | v4: 142/246 |
| Lost Signal **changed** | v19 (3021), v20 (90), v21 (24), v22 (32), v23 (126) | v19: 136/220, v20: 4/4, v21: 2/2, v22: 2/2, v23: 3/4 |
| Decent Chess Bot **changed** | v4 (420), v5 (149), v6 (958), v7 (1748) | v4: 11/38, v5: 3/6, v6: 20/74, v7: 30/144 |
| Mist Opportunities | v2 (3266) | v2: 114/244 |
| TA Baseline S | v3 (3263) | v3: 178/214 |
| TA Baseline A | v5 (3182) | v5: 136/150 |
| duck | v6 (3164) | v6: 80/252 |
| Instructors | v4 (3156) | v4: 106/252 |
| In Pawn Sight **changed** | v3 (2036), v4 (1112) | v3: 102/110, v4: 46/48 |
| Sausage | v1 (3033) | v1: 107/114 |
| TA Baseline P | v5 (3025) | v5: 88/94 |
| Strongly Invisible **changed** | v37 (2811), v40 (40) | v37: 44/242, v40: 1/2 |
| Knight Vision | v36 (2839) | v36: 52/236 |
| Apricot Squad | v9 (2667) | v9: 48/48 |
| baseline.py | v1 (2349) | v1: 18/18 |
| Greek Gift | v25 (2317) | v25: 6/142 |
| Czechmate | v3 (1494) | v3: 20/20 |
| Crimson Fog **changed** | v1 (276), v2 (218), v3 (646) | v1: 4/8, v2: 6/22, v3: 15/56 |

## 2. Rating point flow per opponent, v35 (Elo, K = 8; an approximation)

Each game is scored against both players' ratings in the latest leaderboard snapshot before it (3264 games; snapshot age median 12.3 h, max 23.9 h; 12 games skipped with no earlier snapshot). Until 26 October this table used the latest snapshot for every game, so earlier totals are not historical flows. Cohort: hist = the fixed 13 October top six, now = today's top six.

| opponent | games | score | Elo expects | net points | cohort |
|---|---|---|---|---|---|
| Strongly Invisible | 244 | 0.18 | 0.24 | -107 | hist, now |
| Crimson Fog | 84 | 0.29 | 0.43 | -95 | now |
| duck | 252 | 0.32 | 0.37 | -92 | hist, now |
| Decent Chess Bot | 262 | 0.24 | 0.28 | -76 | hist, now |
| Gravel Road | 246 | 0.58 | 0.59 | -30 |  |
| Greek Gift | 142 | 0.04 | 0.06 | -18 | hist, now |
| Instructors | 252 | 0.42 | 0.43 | -12 | hist |
| TA Baseline P | 94 | 0.94 | 0.94 | -3 |  |
| Czechmate | 10 | 1.00 | 1.00 | +0 |  |
| baseline.py | 18 | 1.00 | 0.99 | +1 |  |
| Apricot Squad | 48 | 1.00 | 0.99 | +5 |  |
| Sausage | 114 | 0.94 | 0.93 | +12 |  |
| TA Baseline A | 150 | 0.91 | 0.88 | +27 |  |
| In Pawn Sight | 158 | 0.94 | 0.91 | +39 |  |
| Knight Vision | 236 | 0.22 | 0.20 | +41 | hist, now |
| HYPOTHERMIA | 264 | 0.58 | 0.55 | +57 |  |
| Mist Opportunities | 244 | 0.47 | 0.42 | +105 |  |
| TA Baseline S | 214 | 0.83 | 0.76 | +126 |  |
| Lost Signal | 232 | 0.63 | 0.54 | +166 |  |
| **total** | 3264 | | | +146 | |

## 3. First queen event against the fixed 13 October top six, v35, last 3 days (560 games)

| event | games | share | our score |
|---|---|---|---|
| trade, we took first | 195 | 35% | 0.17 |
| trade, they took first | 140 | 25% | 0.20 |
| we lose the queen | 84 | 15% | 0.06 |
| they lose the queen | 80 | 14% | 0.76 |
| no queen event | 61 | 11% | 0.30 |

## 4. King moves per 100 moves by phase, last 3 days, in our games against the fixed 13 October top six (both sides from the same games)

| side | opening | middle | late |
|---|---|---|---|
| IAmAVirus | 5.2 | 13.6 | 35.3 |
| the fixed top six | 6.0 | 6.5 | 18.3 |

## 5. Our king captured within four plies of our move, by fog lines from the king (last 3 days)

| phase | 0 lines | 1 | 2 | 3+ |
|---|---|---|---|---|
| middle | 0.4% of 25423 | 2.5% of 8589 | 13.0% of 1994 | 40.1% of 1247 |
| late | 1.0% of 2818 | 1.8% of 5370 | 4.9% of 4106 | 8.0% of 6553 |

## 6. Our losses in 20 plies or fewer, last 3 days

- 4itcuzke vs Knight Vision as black, 18 plies: `e2e4 b8c6 c2c4 e7e5 d1a4 f8c5 d2d3 d8f6 g1f3 g8e7 b1c3 d7d6 c1e3 c8g4 c3d5 e7d5 c4d5 c6e7`
- dt9ltrgk vs Knight Vision as black, 8 plies: `e2e4 c7c6 c2c3 d7d5 e4d5 c6d5 d1a4 g8f6`
- fk3vej9b vs Gravel Road as white, 15 plies: `d2d4 c7c5 g1f3 g8f6 b1c3 e7e6 e2e4 c5d4 f3d4 b8c6 a2a3 d8a5 c1e3 f6e4 c3e4`
- 97yemx0g vs TA Baseline P as white, 9 plies: `d2d4 e7e6 h2h4 c7c5 a2a3 d8a5 c2c3 c5d4 c3d4`
- 998mlunc vs TA Baseline P as white, 11 plies: `d2d4 g8f6 c2c3 e7e6 e2e3 c7c5 f1e2 d8a5 h2h3 c5d4 c3d4`
- s2zc32s3 vs In Pawn Sight as white, 13 plies: `d2d4 d7d5 g1f3 f7f5 e2e3 b8c6 a2a4 d8d6 c1d2 f5f4 e3f4 d6e6 f1d3`
- x44hflhd vs In Pawn Sight as white, 13 plies: `d2d4 d7d5 e2e3 f7f5 f1d3 b8c6 b2b3 d8d6 c2c3 f5f4 e3f4 d6e6 g1f3`
