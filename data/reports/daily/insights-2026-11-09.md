# Arena insights, 2026-11-09 22:18 UTC

> Recovery after the November 9 service timeout. Local own-game feed through 2026-11-09T21:54:14.304001+00:00; other-team feed through 2026-11-09T10:15:01.901273+00:00; leaderboard snapshot 2026-11-09T21:51:47.277729+00:00. Rolling archive views; API completeness is not established. Taxonomy changes compare the November 2 reference. A separate move export is running; no playing model was refitted.

Our active version: v38. Window: 7 days (29312 games of all teams).

Current leaders at the latest snapshot (2026-11-09 22:12 UTC): Greek Gift, Knight Vision, Strongly Invisible, Decent Chess Bot, duck, Crimson Fog. Sections 3 and 4 use the fixed 13 October top six (Greek Gift, Knight Vision, Strongly Invisible, Decent Chess Bot, duck, Instructors), kept fixed for comparison over time; not in today's top six: Instructors; in today's but not the cohort: Crimson Fog.

## 1. Opponents' versions in the window, and our score against each

| opponent | versions seen (games) | our score by version |
|---|---|---|
| Lost Signal **changed** | v24 (405), v25 (332), v26 (1380) | v24: 27/34, v25: 11/16, v26: 34/62 |
| Mu1tip13 @g3nt$ | v6 (2072) | v6: 79/100 |
| Gravel Road **changed** | v4 (786), v5 (1283) | v4: 16/36, v5: 15/42 |
| HYPOTHERMIA **changed** | v4 (1371), v7 (238), v8 (30), v9 (398) | v4: 42/82, v7: 5/8, v8: 3/4, v9: 10/26 |
| Mist Opportunities | v2 (2027) | v2: 51/116 |
| Foggy Fischer | v4 (2021) | v4: 70/96 |
| TA Baseline S | v3 (2020) | v3: 69/82 |
| RATIRL | v2 (2008) | v2: 83/122 |
| duck **changed** | v6 (1536), v8 (54), v9 (80), v10 (12), v11 (310) | v6: 36/94, v8: 0/2, v9: 2/4, v10: 0/2, v11: 4/14 |
| Instructors | v4 (1984) | v4: 52/128 |
| Resting Bishop Faces **changed** | v3 (232), v4 (306), v5 (128), v6 (818), v7 (470) | v3: 3/4, v4: 6/6, v6: 22/26, v7: 12/18 |
| Trojan Horse **changed** | v1 (714), v4 (92), v5 (1130) | v1: 14/14, v4: 2/2, v5: 13/14 |
| Farsight **changed** | v11 (8), v12 (104), v13 (164), v14 (92), v15 (244), v16 (590), v17 (74), v18 (26), v19 (62), v20 (236), v21 (12), v22 (4), v23 (80), v24 (118), v25 (120) | v12: 4/6, v13: 3/6, v14: 0/4, v15: 4/10, v16: 27/52, v17: 2/2, v18: 1/6, v19: 2/4, v20: 4/18, v24: 1/4, v25: 8/16 |
| Cranberry Lemon **changed** | v8 (292), v9 (699), v10 (822), v11 (98) | v8: 10/24, v9: 24/48, v10: 17/40, v11: 1/2 |
| In Pawn Sight **changed** | v5 (600), v6 (211), v7 (6), v8 (40), v9 (428), v10 (614), v11 (2) | v5: 12/14, v6: 9/10, v9: 12/16, v10: 24/34, v11: 1/2 |
| TA Baseline A | v5 (1895) | v5: 55/60 |
| Decent Chess Bot | v7 (1886) | v7: 32/114 |
| Strongly Invisible | v41 (1873) | v41: 20/84 |
| Sausage | v1 (1844) | v1: 40/42 |
| Crimson Fog | v4 (1830) | v4: 20/80 |
| TA Baseline P | v5 (1812) | v5: 50/50 |
| baseline.py | v1 (1784) | v1: 6/6 |
| Knight Vision | v36 (1780) | v36: 32/84 |
| Czechmate | v3 (1764) | v3: 12/12 |
| Apricot Squad | v9 (1763) | v9: 12/12 |
| Bit Gambit | v9 (1680) | v9: 4/4 |
| Unicorns | v1 (1551) | v1: 10/10 |
| Greek Gift | v25 (1280) | v25: 2/88 |
| Fogitos **changed** | v3 (997), v4 (170) | v3: 18/34, v4: 16/18 |
| ADARSH **changed** | v1 (32), v2 (1056) | v2: 6/6 |
| Beyond Visibility **changed** | v1 (36), v2 (130), v3 (364), v4 (216), v5 (8), v6 (60), v7 (74), v11 (18), v12 (40) | v5: 2/2 |
| Ex Republics **changed** | v2 (2), v3 (2), v4 (10), v10 (16), v12 (8), v13 (2), v14 (12), v15 (6), v16 (10), v17 (4), v18 (24), v19 (2), v20 (20), v21 (16), v22 (20), v23 (34), v24 (18), v25 (80), v26 (10), v27 (8), v28 (10), v29 (6), v30 (4), v32 (10) | v10: 4/4, v25: 2/4, v30: 3/4, v32: 5/10 |
| Next | v1 (88) | v1: 4/6 |
| TUM **changed** | v3 (64), v4 (2) | v3: 2/2, v4: 1/2 |

## 2. Rating point flow per opponent, v38 (Elo, K = 8; an approximation)

Each game is scored against both players' ratings in the latest leaderboard snapshot before it (328 games; snapshot age median 5.9 h, max 15.5 h; 2 games skipped with no earlier snapshot). Until 26 October this table used the latest snapshot for every game, so earlier totals are not historical flows. Cohort: hist = the fixed 13 October top six, now = today's top six.

| opponent | games | score | Elo expects | net points | cohort |
|---|---|---|---|---|---|
| Foggy Fischer | 14 | 0.57 | 0.77 | -23 |  |
| Gravel Road | 10 | 0.40 | 0.59 | -15 |  |
| Ex Republics | 18 | 0.56 | 0.66 | -15 |  |
| duck | 14 | 0.25 | 0.37 | -14 | hist, now |
| Next | 4 | 0.50 | 0.88 | -12 |  |
| Greek Gift | 18 | 0.00 | 0.07 | -11 | hist, now |
| Decent Chess Bot | 14 | 0.18 | 0.27 | -10 | hist, now |
| Trojan Horse | 6 | 0.83 | 0.97 | -7 |  |
| Mu1tip13 @g3nt$ | 20 | 0.75 | 0.79 | -6 |  |
| TUM | 4 | 0.75 | 0.87 | -4 |  |
| Unicorns | 2 | 1.00 | 1.00 | +0 |  |
| baseline.py | 2 | 1.00 | 1.00 | +0 |  |
| Apricot Squad | 2 | 1.00 | 0.99 | +0 |  |
| Sausage | 2 | 1.00 | 0.94 | +1 |  |
| RATIRL | 14 | 0.71 | 0.69 | +3 |  |
| Lost Signal | 8 | 0.62 | 0.58 | +3 |  |
| TA Baseline P | 6 | 1.00 | 0.93 | +3 |  |
| Resting Bishop Faces | 6 | 0.83 | 0.74 | +4 |  |
| TA Baseline S | 10 | 0.90 | 0.84 | +5 |  |
| HYPOTHERMIA | 18 | 0.61 | 0.56 | +8 |  |
| Cranberry Lemon | 16 | 0.56 | 0.50 | +8 |  |
| Strongly Invisible | 12 | 0.38 | 0.28 | +9 | hist, now |
| Farsight | 18 | 0.47 | 0.40 | +10 |  |
| Instructors | 20 | 0.53 | 0.46 | +10 | hist |
| Fogitos | 20 | 0.82 | 0.76 | +11 |  |
| In Pawn Sight | 16 | 0.69 | 0.60 | +12 |  |
| Crimson Fog | 8 | 0.50 | 0.31 | +12 | now |
| Mist Opportunities | 10 | 0.70 | 0.48 | +17 |  |
| Knight Vision | 16 | 0.56 | 0.23 | +42 | hist, now |
| **total** | 328 | | | +44 | |

## 3. First queen event against the fixed 13 October top six, v38, last 3 days (94 games)

| event | games | share | our score |
|---|---|---|---|
| trade, we took first | 33 | 35% | 0.21 |
| no queen event | 18 | 19% | 0.53 |
| we lose the queen | 16 | 17% | 0.00 |
| trade, they took first | 15 | 16% | 0.17 |
| they lose the queen | 12 | 13% | 0.92 |

## 4. King moves per 100 moves by phase, last 3 days, in our games against the fixed 13 October top six (both sides from the same games)

| side | opening | middle | late |
|---|---|---|---|
| IAmAVirus | 6.2 | 11.2 | 32.3 |
| the fixed top six | 6.0 | 6.7 | 17.8 |

## 5. Our king captured within four plies of our move, by fog lines from the king (last 3 days)

| phase | 0 lines | 1 | 2 | 3+ |
|---|---|---|---|---|
| middle | 0.4% of 6316 | 2.0% of 2481 | 11.1% of 432 | 40.2% of 224 |
| late | 0.8% of 766 | 2.0% of 1420 | 2.9% of 1120 | 8.4% of 1467 |

## 6. Our losses in 20 plies or fewer, last 3 days

- none
