# Posterior-objective experiment: a small predictive gain, below the promotion requirement

Astra, 2 November 2026. **The direct posterior objective helps, but this configuration does not advance.** It misses both minimum-effect requirements. There is no sequential-filter integration or playing-strength claim from this result.

Both models have the same 26 residual coefficients and training cases. One optimizes recorded-move likelihood; the other optimizes the probability of the true successor board after the observer's new view. Incoming baseline beliefs, history counts and temperature 2 are fixed. This is one-step learning on exact prefixes, not differentiation through an entire capped game.

| Held-out metric, equal weight per contributing game | Baseline v37 prior | Move-trained residual | Posterior-trained residual |
|---|---:|---:|---:|
| Hidden-board NLL, primary 779 decisions / 80 games | 2.43138 | 2.43910 | 2.41086 |
| Recorded-move NLL, same decisions | 1.70132 | 1.69655 | 1.72292 |
| Hidden-board NLL, 69 surprise captures / 34 games | 1.63107 | 1.62861 | 1.60723 |

Lower NLL is better. Posterior training gains **0.02052 nats** over the baseline, with whole-game 95% bootstrap interval **[0.00073, 0.04173]**. The frozen minimum was 0.10. Its gain over the matched move-trained model is **0.02823**, below 0.05. Later-update gain is 0.03842; surprise-capture gain is 0.02384; all-update gain is 0.01929. No natural support failures occurred in any split. Every safeguard passes except the two minimum gains. Do not promote the late subset or lower the thresholds after this result.

This provides a useful distinction: improving recorded-move prediction slightly worsened hidden-board probabilities; optimizing the posterior reversed that tradeoff. It does not prove that a stronger representation will succeed or that either objective improves Elo.

## Data and execution

Frozen 400 training, 80 validation and 80 later test games, all outcomes, nine reference opponents. Salted selection, complete move-sequence deduplication, excluded prior experiment panels. The predicted actor is a reference team; the observer may be another team. It is not an IAmAVirus head-to-head result.

Training retained 3,058 cases, validation 810, test 1,108. Prefix collection stops above 4,096 worlds, at a cap or an empty belief; export requires at most 256 incoming worlds. Twenty-four thousand or capped middlegame states are outside this test. No true world is added. Actual opponent moves and true boards join only as offline labels after observation-driven reconstruction.

Plan published to both remotes at `de827f52b0f36e7f9158e4b93843238b8be6fb3e`, before fitting. Plan SHA `b9753f0c5c88728daa1f9d044f6a5fcc4ef20e072994472f72f062aaa93a2c7f`. The fresh GPU probe found no competing compute process. The single fit/evaluation run used CUDA, 50.66 seconds in the child; original launcher handle 9949 exited 0 in 52.27 seconds. Selected move fit: ridge 0.01, step 30; posterior fit: ridge 0.001, step 40. Selection locked at 04:08:52 UTC, before test extraction. No retraining or test-based selection.

`execution.json` records startup; `terminal.json` and `launcher-terminal.json` record completion. The first launcher (handle 82074) failed importing a system-Python dependency before creating a training process. Its source/failure are preserved; a standalone process-group launcher started the one actual fit. No existing service was stopped.

## Independent verification and reporting repair

The first reviewer (47159) verified **35,745 parent move lists, 1,101,354 legal transitions and 305,246 consistent successors** through the separate rules engine. All test replay frames were validated, and reconstructed feature bytes match the original extraction exactly. The reviewer then caught a reporting collision: flat key `actor` held model scores, replacing the actor team-name metadata. Training inputs, scores and selection were unaffected; all other metadata matched.

The original score file and failed review remain unchanged. A separate reviewer (94133, exit 0) recovers the team name from the pinned manifest/replays, writes `test-scores-with-metadata.jsonl.gz` with separate metadata and prediction objects, and recomputes every score in NumPy. Maximum log-probability difference is **1.73e-14**. Source pins, validation-only selection, paired metrics, bootstrap and every gate condition verify. Use the nested artifact for future analysis.

No new coefficient file is loaded into the playing engine. The fitted models, curves, receipts and failed checks remain here for review.

## Next review priority

The evidence supports measuring posterior quality directly; average move likelihood is not a sufficient promotion test. This 26-coefficient fit is closed. Before spending more training time, review representational capacity and the fixed-incoming-belief limitation together with the prior interaction-model result. A nonlinear posterior objective would be a new hypothesis needing new data and a separate prospective gate, not a continuation tuned on these 80 games. Missing-world failures remain a separate problem that reweighting cannot repair.
