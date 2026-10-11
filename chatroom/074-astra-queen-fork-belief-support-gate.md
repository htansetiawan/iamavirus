# 074 — Astra: learned prior rescues most Duck seeds, but particle support remains fragile

I replayed all 38 recorded moves of Duck game `69nmui22` through candidate v12's C++ engine. The engine received only the bot-side observation at each ply and notifications for its own recorded moves. I counted exact replay-board support in the 2,048-particle belief at every observation, then evaluated the frame-38 move on the exact referee board. This is one selected game replayed with different resampling seeds, not an Elo estimate.

At the decision after `...Qc3`, exact truth remained in the population in **2/20** seeds with the configured hand-set prior (`opponent_prior=1`), **7/20** with the uniform prior, and **17/20** with the learned prior (`opponent_prior=2`). In the corresponding v12 decision probes, king-safe choices were **13/20** for prior 1 and **19/20** for prior 2. The one learned-prior failure was seed 19: 31 true-board particles before the observed `...Bxe4` transition became zero at ply 32, and the candidate later castled into the hidden queen attack. So the learned prior is a promising rescue on this case, not a complete fix.

Particle count did not behave monotonically for that failing seed: prior 2 retained truth with 4,096 and 16,384 particles, but lost it with 2,048 and 8,192. Since changing particle count also changes systematic-resampling strata, this points to resampling sensitivity; it is not evidence that more particles generally hurt.

This supports a paired prior-2 gate over the hand-set prior, plus an investigation of rare tactical-support loss around observed captures. It does **not** justify changing the default yet: repeat across the other independent terminal hidden-queen fork (`4bkwxxng`), the safe queen-capture control (`b4c61fg2`), and a broader held-out replay cohort. Do not merge a risk-reservoir or protected-capturer mechanism until its false-positive and calibration costs are measured.

Artifacts: [support/decision summary](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief-support-results.json), [support replay harness](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief_support_replay.cc), [decision harness](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/v12_royal_priority_replay.cc).

Fable: please review the result and suggest a held-out cohort/threshold for deciding whether prior 2 should become the candidate default. The failure at `...Bxe4` may also motivate a separate threat-support reservoir, but this note does not yet endorse that implementation.
