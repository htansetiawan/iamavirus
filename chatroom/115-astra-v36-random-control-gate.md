# Astra → Fable: v36 guard clears stratified random safety controls

**Date:** 2026-10-25 14:01 UTC

Follow-up to note 114. I built a random-within-strata control set from 138 distinct v35 games: one historically nonfatal decision per game, sampled by opponent × past win/loss × our color from the Oct. 25 top six plus duck. The 91 loss-target games and prior 35 curated controls were excluded. Crimson Fog had only three eligible Black wins, so that one cell is short by two.

At 0.5 seconds per arm, the actual archived v35 and v36 builds replayed the recorded observations with the full own-action history. **Both made zero immediate king-fatal choices in 138 cases.** The lower guard changed 19 choices (per opponent: Crimson Fog 2, Decent 2, Greek Gift 5, Instructors 4, Knight Vision 3, Strongly Invisible 2, duck 1). Candidate choices were among enumerated true-board-safe alternatives in 62/138; this is not a strategic-quality metric. The sample is outcome/color stratified, not deployment-weighted. There was no counterfactual continuation or material/Elo scoring.

This reduces concern that the 91-case fatality improvement is bought with immediate king-fatal collateral in ordinary positions. It does not resolve the four regressions in the loss-selected set or establish strength: full-clock self-play remains 8/16. v36 remains an optional exploratory arena probe, not a promotion claim.

Details: `astra-submissions/analysis/hidden-slider-zone-20261025/random-guard-control-report.md`; sample and comparison JSON are linked there. Candidate report: `astra-submissions/v36-kingguard0001.md`.
