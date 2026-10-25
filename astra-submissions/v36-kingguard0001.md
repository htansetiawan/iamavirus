# Astra v36: reduced king-risk guard (exploratory)

**Status, 2026-10-25:** **do not promote**. The completed fixed 20-pair test
against v35 finished **16W–0D–24L (40%)**. The archive remains an immutable
experimental artifact; Astra has not uploaded it. Keep v35 as the reference.
See the [completed report](analysis/hidden-slider-zone-20261025/guard0001-fixed-20pairs-report.md).

## Change

The archive is copied from Fable's v35 archive (`fable-submissions/iamavirus-v35-mist-c-v14.zip`, SHA-256 `24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`). The only source change is in `src/main.c`: the default `MIST_KING_GUARD` changes from `0.02` to `0.0001`. Runtime environment override behavior remains available.

Artifact: [`iamavirus-v36-kingguard0001.zip`](iamavirus-v36-kingguard0001.zip), SHA-256 `7051566ed218b790d2b925f23bc1d905bb26ae83f0dcbba13cd71d0f0266e436`. The packaged archive builds successfully. Both the source-worktree build and extracted-archive build produced executable SHA-256 `eed0257297be608d093ae328d81cc3a2108b8e720d72d2b9f52dd61311a8dc17`.

## Evidence

- On 91 held-out, loss-selected hidden-arrival decisions at a fixed 5-second budget, fatal choices fell from 83 to 61: 26 baseline-fatal cases were avoided and 4 cases regressed. This is a selected diagnostic set, not a random sample of games.
- Across 23 curated nonfatal controls, both versions made zero immediate-fatal choices. Six decisions changed; the controls are small and curated.
- On a second, outcome/color-stratified sample of 138 nonfatal decisions from 138 distinct v35 games (top six from the Oct. 25 table plus duck), both versions again made zero immediate-fatal choices; the guard changed 26 decisions. The sample is random within opponent × result × color strata, excludes the previous target/control sets (114 distinct game IDs), and is not representative of deployment frequencies. Crimson Fog had only three eligible v35 Black wins, so its cell is short by two. See the [control manifest](analysis/hidden-slider-zone-20261025/random-v35-guard-controls-20261025.json) and [replay comparison](analysis/hidden-slider-zone-20261025/random-v35-guard-controls-compare-20261025.json).
- Of those 26 changed decisions, 22 had no immediate capture with either choice; two preserved the same pawn capture, one gave up a pawn capture, and one improved a pawn capture to a bishop capture. This checks only the immediate destination occupancy, not downstream tactical/material value.
- A true-board one-ply reply audit of all 229 tested positions found that, in the 138 ordinary controls, six candidate choices added a visible immediately capturable piece and five removed one; cumulative exposed piece value changed by +2 pawn-equivalents. In the four loss-target cases where both choices were nonfatal, the count was unchanged. This is a threat tally, not expected material loss or a reply policy; see [`guard-reply-tactics-229.json`](analysis/hidden-slider-zone-20261025/guard-reply-tactics-229.json).
- Paired color-swapped local self-play at 180+2 finished **8/16 = 0.50** (initial four pairs 4/8; additional four pairs 4/8). This is neutral and not an Elo estimate.
- The subsequent fixed **20-pair** run completed **16W–0D–24L = 0.40**. All
  3,348 replay frames and 40 terminal results passed the integrity audit. The
  approximate pair-bootstrap 95% score interval is [0.25, 0.575]. Earlier
  exploratory matches are not pooled into this result.

## Recommendation

Do not submit this candidate as an improvement. The completed full-game screen
does not support the earlier optional-trial recommendation, despite the
selected replay improvement. The interval still includes equal strength, so
do not claim a proven Elo regression either. Close this threshold experiment
at its fixed cap and keep the learning/posterior investigation separate.
