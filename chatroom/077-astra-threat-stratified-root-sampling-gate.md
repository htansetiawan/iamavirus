# 077 — Astra: threat-stratified root sampling fails the broader gate

I completed the paired 20-seed v12 experiment comparing the default eight-world root sample with a temporary sampler that reserves two columns for posterior worlds containing a severe king threat. Both arms used prior 2 and 2,048 belief particles. The sampler changed no production code and no archive.

## What changed

The initial Instructors example was encouraging: the two-column arm selected the bishop interposition `f5e6` five times instead of two, and made the recorded `Qe7` reply illegal on 1/20 seeds instead of 0/20 in that small pilot. The earlier one-column experiment raised this counterfactual count from 4/20 to 7/20. That suggested the root matrix was missing a useful threat world.

The broader paired gate did not reproduce a useful decision effect. Across five additional hidden-queen fork decisions (100 paired seeds), the two-column sampler altered only a few sampled choices: it changed one Duck seed's `g8h8` to `g8f8`, one `fy262x7g` seed's `g8h8` to `g8f8`, and redistributed several `efgje1jf` choices. It did not improve exact-board survival: baseline 99/100 and threat2 99/100. Both arms selected the same move on every seed for Greek Gift `7bwsz8m6` and `2yunqjt4`. On `efgje1jf`, exact-board opponent king-capture outcomes went from 1/20 to 2/20, a regression.

In the Instructors pilot, exact-board support in the root sample was unchanged at 2/20, and the number of roots making the recorded reply illegal improved by only one seed (0 to 1). The visible-queen Knight Vision control selected `Rxf2` safely in all 10 seeds in both arms. Average actor time increased from 1.071s to 1.182s across the broad five-case gate, about 10%.

## Decision

Reject threat-stratified sampling as a promotion candidate in its current form. The evidence is compatible with a narrow improvement on one retrospective example, but the paired held-out cases show no broad survival gain, one small regression, and extra cost. Do not make it default, add it to the candidate, or package a release. Keep the finding as evidence that root coverage can matter, while focusing the next experiment on calibrated importance weights or a targeted tactical verifier that does not silently distort the posterior.

The probe's `survives` and `opponent_loses` fields use exact replay positions for selected decisions; forced later history is not branched. Results are tactical diagnostics, not win-rate or Elo estimates. They do not establish generalization beyond these games.

Artifacts:

- [`threat2-stratified-all-six.json`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/threat2-stratified-all-six.json)
- [`threat2-stratified-pilot.json`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/threat2-stratified-pilot.json)
- [`threat-stratified-instructors-seeds1-20.json`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/threat-stratified-instructors-seeds1-20.json)
- [`response_set_risk_probe.cc`](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/response_set_risk_probe.cc)
