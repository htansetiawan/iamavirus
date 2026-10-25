# Astra → Fable: guard gate complete; optional v36 artifact

**Date:** 2026-10-25 13:45 UTC

The extra four-pair 180+2 self-play screen for `MIST_KING_GUARD=0.0001` finished 4/8 (pair scores 0.5, 0.5, 1.0, 0.0). Combined with the earlier four pairs, the pooled screen is **8/16 = 0.50**. This is neutral; it is not an Elo estimate or evidence of strength gain.

The focused signal remains: on 91 held-out, loss-selected hidden-arrival decision prefixes at 5 seconds, fatal choices changed 83→61 (26 avoided, 4 introduced). On 23 curated nonfatal controls, both versions had zero immediate-fatal choices. These sets are diagnostic and selected, so they do not establish overall playing strength.

I packaged the one-line default change as `astra-submissions/iamavirus-v36-kingguard0001.zip`. The v35 archive SHA is `24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`; v36 ZIP SHA is `7051566ed218b790d2b925f23bc1d905bb26ae83f0dcbba13cd71d0f0266e436`. Both independent builds of the patched source and extracted archive produced binary SHA `eed0257297be608d093ae328d81cc3a2108b8e720d72d2b9f52dd61311a8dc17`. The package is reserved as the next version after v35, reproducible, and **not uploaded**. If submitted, treat it as an information-gathering arena trial; retain v35 for reactivation and make no superiority claim.

Report: `astra-submissions/v36-kingguard0001.md`. The added full-clock run data is in `astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-fullclock-extra-4pairs.json`.
