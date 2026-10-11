# Visibility-conditioned move prior: predictive gain, sequential regression

**Decision: do not promote the 32-feature prior.** It improves held-out action prediction, but its advantage does not reliably survive sequential belief maintenance. A separate audit identifies a probability distortion in the existing weighted cap and supplies a tested standalone sampling prototype. That prototype is not integrated into either bot.

Classification: offline prediction, fixed-history belief evaluation, and sampling mathematics. No playing-strength or Elo estimate. GPU vLLM was not changed. No ZIP, arena upload, active-engine change, or shared belief/CFR header edit.

## Frozen experiment

C source: [`astra/m4` commit a63a4fb](https://github.com/htansetiawan/mist-c/commit/a63a4fb). Python tools live under `astra-submissions/tools/m4_prior_*.py`. Large arrays, executables and immutable attempts are under `/media/henrytan/seagate/iamavirus/astra/m4-visibility-prior-20261011/`.

- 2,400 cached games, completed September 30–October 10. Game-ID hash split: 1,686 train / 352 validation / 362 test. Excludes IAmAVirus, Uniform and baseline move targets; no team-name input feature.
- 109,301 training decisions; 22,757 validation and 23,615 test decisions. Extractor regenerates every move and requires the resulting true board to match the replay. Every emitted row is accounted for against the game manifest.
- The 26-feature control and 32-feature extension use identical data, regularization (L2 = 0.001), optimizer and splitting. No hyperparameter sweep. Completed in 21 seconds on CPU cores 6–7.
- Added channels: hidden-only check, observation-silent check, observation-silent move, concealed mover, new visibility, concealed king-zone attack.
- These features condition on a full hypothesized parent board, as the original model does. They are not an information-set-realizable opponent policy. “Silent” compares the defender's complete before/after observation, not only its visibility mask.
- October 11 games are excluded from fitting. Repeated opening patterns may exist across game splits; later-ply cohorts are reported separately.

## Held-out action prediction

| Test measurement | Control 26 | Visibility 32 |
|---|---:|---:|
| Move negative log likelihood (nats; lower better) | 2.674023 | 2.668717 |
| Top-1 action accuracy | 26.276% | 26.390% |
| Hidden-check Brier score | 0.011458 | 0.011333 |
| Quiet conditional hidden-check Brier | 0.012078 | 0.011782 |
| Quiet conditional mean hidden-check probability | 1.149% | 1.503% |
| Observed hidden checks in quiet cohort | 193/11,415 = 1.691% | same |

Test likelihood gain is 0.005306 nats/move, whole-game bootstrap 95% interval [0.004314, 0.006177]. The validation interval is also positive. Quiet test Brier reduction is 0.000296 [0.000026, 0.000583]; validation's quiet Brier interval crosses zero. Conditioning restricts candidate actions to those leaving the defender's observation unchanged and renormalizes their probabilities. This uses the known parent board for offline evaluation; it is not a sequential posterior.

The six new coefficients are in `fit01/models.json`. The hidden-only-check coefficient is negative while silent-check and concealed-mover coefficients are positive: interpret the joint model, not one coefficient as a tactical rule. Coefficients were not adjusted after these reports.

## Sequential belief test

The standalone driver feeds only own recorded moves and observations into the existing belief updates. It tracks a separate true board exclusively for validation/labels. The cap is fixed at 10,000; both models use full features. There is no search or clock-dependent thinning. Both sides' observations and every board are validated; every own-move risk label agrees with the independently curated Python referee labels.

First batch: 16 seeded random games from the earlier October 11 poll, plus the two explicitly diagnosed traps (one already belongs to the random sample). The following table excludes the extra diagnostic game.

| 631 decisions / 16 games | Control 26 | Visibility 32 |
|---|---:|---:|
| True board present | 536 | 540 |
| Belief collapses / rebuilds | 9 | 8 |
| Current king-attack Brier | 0.014873 | 0.013651 |
| Played-move fatality Brier | 0.007882 | 0.008060 |
| Total belief-update CPU seconds | 18.30 | 34.50 |

All paired bootstrap intervals cross zero. The final driver fixes a promotion-parser portability issue; every non-timing output row matches the retained first attempt (`driver-parity.json`).

The unchanged fitted models were then tested on **all 26 newly downloaded games**, a disjoint batch. No retraining or selection by result:

| 1,019 decisions / 26 fresh games | Control 26 | Visibility 32 |
|---|---:|---:|
| True board present | 850 | 791 |
| Belief collapses / rebuilds | 4 | 14 |
| Current king-attack Brier | 0.013661 | 0.013557 |
| Played-move fatality Brier | 0.011207 | 0.010822 |
| Expected fatal moves / actual 13 | 3.47 | 5.42 |
| Total belief-update CPU seconds | 24.72 | 47.82 |

Again the Brier intervals cross zero. The additional collapses and lost truth support prevent promotion. More accurate action likelihood alone is an inadequate gate.

The two earlier trap probabilities increase, but remain low: Qa4→Ke8 0.833% → 1.245%; Rc8→Kg8 8.064% → 11.493%. That does not establish that the engine would choose an escape. Feature-only benchmark: 4,096 positions, 124,601 actions, six passes; 0.386 versus 0.887 CPU seconds, **2.297×** cost. This is not a real-clock match benchmark.

## Structural finding: weighted capping changes the represented distribution

Both C `belief_after_opponent` and `belief_shrink` select unique boards using an exponential race weighted by posterior mass, then retain those original masses. They do not correct for the selection probabilities. This can suppress low-mass events further when interpreting the retained, renormalized weights as posterior probabilities.

Exact counterexample: weights [0.8, 0.1, 0.1], retain two by weighted sampling without replacement. The expected represented probabilities become **[0.869136, 0.065432, 0.065432]**. This is a mathematical property of the cap, not proof that it caused this experiment's regression. If the intended object is a posterior restricted to a heuristically chosen subset, this is still its calibration tradeoff.

The standalone `m4resample.c` prototype retains the k+1 smallest exponential-race keys in a bounded max-heap, then uses the extra key to compute threshold-conditioned importance weights. Sampling costs O(N log(k+1)) work and O(k+1) auxiliary space, plus sorting only the retained keys. Tests compare selected indices with a full sort, verify weights, exact/no-cap behavior, invalid inputs and a 200k-draw expectation check. Address/undefined-behavior sanitizer run passed (leak checking disabled).

The unnormalized importance estimator follows [Kool et al., ICML 2019 §4.2, equations 13–14](https://proceedings.mlr.press/v97/kool19a/kool19a.pdf). Normalizing those weights remains a biased ratio estimate at finite sample size; the prototype does not claim an exact posterior. The Python diagnostic and C test independently recover approximately 0.800 for the high-mass state's unnormalized expectation and 0.811 after normalization, versus the old 0.869. No active belief code has been changed.

**Next gate:** isolate the cap change with frozen priors, inputs and RNG seeds; preserve the uncapped exact path; compare sequential hazard calibration, support, collapse counts and runtime. Only then test search decisions and paired games. Do not compensate by increasing the new prior's coefficients.

## Fresh arena data

14:07 UTC snapshot: arena v30, 1761.37 Elo, 125W–22D–145L over 292 games. This is the active Misty wrapper per the shared mapping, not the C experiment. New batch: 10W–3D–13L; duck 0W–2D–6L and Knight Vision 0W–0D–6L. All 2,062 frames and 1,019 own decisions validated. Twelve of thirteen king losses have only hidden terminal attackers; nine had an immediate-survival alternative. These are descriptive counts with changing opponents, not strength estimates.

New equal-material early trap `qkb2exm9`: `e4 d5 exd5 Qxd5 d4 Qa5 Be3`, White loses at ply 7 to hidden Qa5. The observation **did change** when the queen left d5, so a rule triggered only by unchanged observations would miss it. Seven immediate-survival alternatives existed.

## Reproduction and checks

Build C tools: `make build/m4_move_features build/m4_move_bench build/m4_prior_replay test_m4_movefeatures test_m4_resample` on the cited C commit. Python fit needs NumPy; it does not require SciPy, PyTorch or a GPU. CLI `--help` describes paths for preparation, paired fitting, sequential replay and reporting. `test_m4_prior_fit.py` checks the known categorical optimum, deterministic tie handling, grouped bootstrap and truncated/misaligned binary records.

`manifest.json.gz` retains game IDs and source hashes; `features.json` pins large arrays; fit artifacts retain coefficients and optimization traces. Sequential manifests pin runner, input and model hashes. Compressed row-level outputs and fresh referee audits permit independent recomputation. `artifacts.json` inventories the retained evidence. All experiment processes finished; the broader bot-improvement goal remains incomplete.
