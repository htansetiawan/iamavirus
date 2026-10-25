# Astra v36: reduced king-risk guard (exploratory)

**Status:** built and reproducibly packaged; not uploaded. This is an optional arena probe, not a demonstrated strength upgrade. The active v35 should remain the reference until arena evidence says otherwise.

## Change

The archive is copied from Fable's v35 archive (`fable-submissions/iamavirus-v35-mist-c-v14.zip`, SHA-256 `24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`). The only source change is in `src/main.c`: the default `MIST_KING_GUARD` changes from `0.02` to `0.0001`. Runtime environment override behavior remains available.

Artifact: [`iamavirus-v36-kingguard0001.zip`](iamavirus-v36-kingguard0001.zip), SHA-256 `7051566ed218b790d2b925f23bc1d905bb26ae83f0dcbba13cd71d0f0266e436`. The packaged archive builds successfully. Both the source-worktree build and extracted-archive build produced executable SHA-256 `eed0257297be608d093ae328d81cc3a2108b8e720d72d2b9f52dd61311a8dc17`.

## Evidence

- On 91 held-out, loss-selected hidden-arrival decisions at a fixed 5-second budget, fatal choices fell from 83 to 61: 26 baseline-fatal cases were avoided and 4 cases regressed. This is a selected diagnostic set, not a random sample of games.
- Across 23 curated nonfatal controls, both versions made zero immediate-fatal choices. Six decisions changed; the controls are small and curated.
- On a second, outcome/color-stratified sample of 138 nonfatal decisions from 138 distinct v35 games (top six from the Oct. 25 table plus duck), both versions again made zero immediate-fatal choices; the guard changed 26 decisions. The sample is random within opponent × result × color strata, excludes the previous target/control sets (114 distinct game IDs), and is not representative of deployment frequencies. Crimson Fog had only three eligible v35 Black wins, so its cell is short by two. See the [control manifest](analysis/hidden-slider-zone-20261025/random-v35-guard-controls-20261025.json) and [replay comparison](analysis/hidden-slider-zone-20261025/random-v35-guard-controls-compare-20261025.json).
- Paired color-swapped local self-play at 180+2 finished **8/16 = 0.50** (initial four pairs 4/8; additional four pairs 4/8). This is neutral and not an Elo estimate.

## Recommendation

If submitted, use it as a bounded arena information-gathering trial and keep v35 ready to reactivate. Do not describe it as stronger based on these results. The broader replay control reduces concern about immediate-fatal collateral, but says nothing about strategic or material regressions. Arena games or full-game matches against diverse opponents remain necessary before promotion.
