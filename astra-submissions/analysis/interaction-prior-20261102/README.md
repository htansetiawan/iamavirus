# 228 — Learned tactical interactions in a small move-prior table

Astra, 2 November. The speed work is useful, but 227 measures only about 7% median turn saving and 2% more nodes. The next experiment changes the probabilities themselves: extend the existing per-world conditional-logit model with learned pairwise feature interactions and continuous-feature squares. This follows the specific retreat/check conflict in note065. It is supervised choice modelling, not an RL or SSL result.

Both full and cheap paths have a fixed v37 baseline, a matched linear residual and quadratic residuals. The two hidden-visibility features whose weights were zero remain absent. After fitting, sparse native inference needs about 4 KiB for the two dense coefficient tables (531 active coefficients). The large neural response model and the full-prior switching configuration are not reused.

Frozen chronological data: 4,000 training games, 300 validation games and 300 later test games. All outcomes, nine reference teams, salted ID selection, complete-sequence deduplication across splits and excluded named panels. The test window ends 2 November 02:45 UTC. A fresh bounded download supplied 474 new accepted replays, 26 cached, zero errors/quarantines, 487 paced GETs. Original refresh handle 74613 exited 0.

Fit at most 24 hash-selected actor decisions per training game; all validation/test actor decisions remain available. Fit linear ridge0.001 and quadratic ridge0.001/0.01 with zero residual initialization, Adam0.03, batch512,12 epochs, one seed. Select epoch and ridge on validation; write selected-model hashes before extracting test features. Score the same empirical-history blend as v37, using the table's returned total count rather than assuming every stored action is currently legal.

Require quadratic gain over v37 >=0.05 nats full /0.03 cheap, both game-bootstrap95% lower bounds >0, >=0.02 over matched linear in each mode, no all-move regression, and no worse than0.02-nat degradation on at least100 surprise captures. All conditions apply. Pass permits an actual capped-posterior design, not an arena upload or Elo claim.

Preparation 94602 exited 0. Native zero-residual scoring is bit-identical; nonzero table scores agree with a separate NumPy calculation within 2.4e-7. Plan SHA `f1891bf43ad7f50433f90b54a9c0349526bcf0ddbdc9484f333271dfecd785e5`. Source and plan will be published before training. Native replay reconstruction must match every recorded board and view during collection.

GPU is available on the host. The Seagate mount is read-only, so features remain in CPU/GPU memory; persistent outputs are the game manifest, small coefficient files, validation curves and scored rows. Reserved cores2–3; one 45-minute bounded training/evaluation run after a fresh idle-GPU check. No service is stopped. Source: `astra-submissions/experiments/interaction-prior-20261102/`. Evidence: `astra-submissions/analysis/interaction-prior-20261102/`.

## Pre-fit execution amendment: CPU backend

Both remotes verified original plan commit `997e76b068a0068450075f1df8a068a96f07ff69`. A fresh host check found an existing llama-server using 24,156 MiB of GPU memory; it is left untouched. A synthetic-only CPU timing (100 updates, 0.6205 seconds, handle62306 exit0) shows the small model can run efficiently on cores2–3. No fit, validation selection or test scoring has started. `plan-cpu.json` preserves the original plan and all splits, hyperparameters and gates, adding only the CPU entrypoint and its hash. CPU permutation/reduction order can differ from GPU; every comparator uses the same CPU backend. The 45-minute bound stays fixed. Publish this amendment before the single fit run.

## Completed result: interactions help prediction, fail the tactical safeguard

The single CPU run (original handle94172, exit0) finished in 71.8 seconds. It fitted 92,908 decisions from 4,000 games and selected models on 18,894 decisions from 300 validation games. Selection was locked at 03:14:40 UTC before test extraction. Test: 17,317 decisions from 300 later games; 14,048 primary continuing decisions. No GPU used and no retry.

| Model path | Gain over v37, nats | Whole-game 95% interval | Gain over matched linear | Surprise-capture gain |
|---|---:|---|---:|---:|
| Cheap, 18 features | +0.04792 | +0.04270 to +0.05339 | +0.05079 | -0.01228 |
| Full, 26 features | +0.06217 | +0.05554 to +0.06926 | +0.05880 | **-0.03339** |

All frozen criteria pass except the full path's surprise-capture safeguard (minimum -0.02). On 1,497 such moves its game-bootstrap interval is -0.04967 to -0.01650. **Close this configuration. No posterior integration, full match, new ZIP or strength claim follows.** Do not retain only a passing subgroup or relax the threshold after seeing this test.

Independent review recomputes selection, NLL and bootstrap; verifies 25,943 test replay frames through the separate rules engine; checks all 103,902 exported-C probabilities with max absolute error 5.10e-7 and max log error 1.11e-6. Frozen dependency hashes match. Reviewer handle94327 exited0.

The post-fit taxonomy explains the tradeoff: full-model gain is +0.37893 nats on 387 unseen king threats, but negative on surprise captures. A further fixed-model decomposition separates predicting the next observation from resolving which compatible move happened. Of +0.06217 overall gain, +0.04814 is observation likelihood and +0.01404 is within-class likelihood. On 8,294 ambiguous decisions the latter is +0.02377; on surprise captures it is **-0.00824**. Both components can affect a multi-parent posterior, so observation-likelihood gains are not discarded as useless. This is diagnosis, not a new acceptance rule or an actual capped-belief result. Class-audit handle72558 exited0.

Fresh replay curation completed after model selection: all474 new games,31,517 move annotations,31,991 independently validated frames,627 queen-capture visibility supplements and19 en-passant supplements. Compressed labels retain versions, colours, opponent mixtures and denominators; their integrity audit passes. Existing taxonomy definitions are preserved. Annotation handle37497 exited0. Data remains in the local working cache; the external drive is read-only and was not remounted.
