# 112 — Astra: hidden slider king-zone feature rejected after full gate

The experimental feature adds a move-model signal for a hidden bishop, rook,
or queen destination that attacks the enemy king's adjacent zone without
necessarily giving check. It was fit on 5,889 games / 59,100 positions after
excluding all 91 targeted loss games. The game-disjoint held-out predictive
gain is small overall: full-prior NLL 2.64202 → 2.64164; cheap-prior NLL
2.81434 → 2.80256. These are move-prediction metrics only.

## Replay gate

At five seconds per decision on 91 game-excluded, loss-selected hidden-arrival
positions, the candidate changed 39 choices. Immediate-fatal choices fell
84 → 81 (8 saved, 5 introduced). For beliefs at or below 10k, the full-prior
branch was even at 60 → 60 (4 saved, 4 introduced); above 10k, the cheap branch
was 24 → 21 (4 saved, 1 introduced). On 12 curated nonfatal king-move controls,
neither build chose an immediately fatal move; choices changed in 3 cases.

## Full-clock result

The 180+2, color-swapped v35 comparison completed eight games. Candidate score
was **3.5/8 = 0.4375**; pair scores: 0.75, 0, 0.5, 0.5. As White it scored
1/4; as Black, 2.5/4. Small sample, no Elo interpretation, but below even and
not a release signal.

Postmortem of its four losses: on the exact terminal prefix, both v35 and the
candidate chose the same fatal move in all four cases. Two positions had no
immediately safe move; two had a safe alternative. The feature did not alter
the losing decision. One illustrative loss ended after a hidden bishop
reached d4 and the candidate king moved f2-g1, where the bishop could capture
it. The terminal-choice replay confirms v35 made the same move. The other
losses included a hidden queen attack and a rook/king exposure.

## Decision and next step

Reject this candidate for v36; no ZIP was made and no arena upload is
recommended. Keep v35 as the tested reference. The experiment indicates that
improving opponent move likelihood alone is not enough: the defender's king
risk policy did not change on its full-game losses. Next, instrument these
four exact prefixes and the 91-position set to measure whether the recent
hidden arrival is represented in the posterior at all; then test a
calibrated tail-risk action gate against matched controls before any feature
is attached to the runtime.

Evidence and exact hashes/results: [`README`](../astra-submissions/analysis/hidden-slider-zone-20261025/README.md),
[`91-position report`](../astra-submissions/analysis/hidden-slider-zone-20261025/exclude-hidden91-prefixes-fullcheap-5s.json),
[`safe controls`](../astra-submissions/analysis/hidden-slider-zone-20261025/safe-controls-5s.json),
[`full-clock games`](../astra-submissions/analysis/hidden-slider-zone-20261025/fullclock-selfplay-4pairs.json),
[`terminal postmortem`](../astra-submissions/analysis/hidden-slider-zone-20261025/fullclock-loss-postmortem.json).
