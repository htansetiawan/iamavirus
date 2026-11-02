# Budget sensitivity: independently verified results

| Prefix | Arm | First move | Outcome | New plies | Wall seconds |
|---|---|---|---|---:|---:|
| 7qu350gu:32 | cheap | f3d4 | 0-1 | 43 | 48.18 |
| 7qu350gu:32 | normal | f3d4 | 0-1 | 43 | 234.41 |
| 7qu350gu:32 | normal_repeat | f3d4 | censored | 64 | 307.17 |
| qpnsjfbm:33 | cheap | e8g8 | 0-1 | 20 | 25.00 |
| qpnsjfbm:33 | normal | e7c6 | censored | 64 | 272.19 |
| qpnsjfbm:33 | normal_repeat | e7c6 | 0-1 | 56 | 241.27 |
| updro1eg:94 | cheap | d6d7 | 1-0 | 10 | 20.30 |
| updro1eg:94 | normal | d6d7 | 1-0 | 8 | 35.12 |
| updro1eg:94 | normal_repeat | d6d7 | 1-0 | 10 | 43.47 |
| g9nruayl:78 | cheap | b7b8 | 0-1 | 25 | 29.34 |
| g9nruayl:78 | normal | b7b8 | 0-1 | 41 | 147.40 |
| g9nruayl:78 | normal_repeat | b7b8 | 0-1 | 25 | 100.83 |

## Costs

| Arm | Natural terminals | Censored | Seconds per new decision | Seconds per natural terminal including censored work |
|---|---:|---:|---:|---:|
| cheap | 4 | 0 | 1.25 | 30.71 |
| normal | 3 | 1 | 4.42 | 229.71 |
| normal_repeat | 3 | 1 | 4.47 | 230.91 |

Independent audit: 1132 frames, 2228 delivered observations, 1120 clock prompts, all transitions and terminal/censor decisions.

Four development prefixes; two selected after prior prediction failures. All planned replicates retained. Censoring is not a draw. Outcome/first-move agreement describes these cases only, not cheap-label equivalence or playing strength.
