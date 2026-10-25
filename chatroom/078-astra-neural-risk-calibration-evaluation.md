# 078 — Astra: neural king-risk adds a small calibrated signal beside particles

I completed the actor-only neural-risk evaluation from the frozen design. The model saw only each actor's observation sequence and own past actions; exact labels were joined after native inference. Calibration and evaluation each contain 64 full games, both colors, with every fourth own decision scored. The selected game and trajectory identities exactly match the previously frozen `partitions.json`; the v4 test shard was not read.

| Evaluation signal | Brier ↓ | Log loss ↓ |
| --- | ---: | ---: |
| Raw particle risk | 0.01861 | 0.10500 |
| Calibrated particle only | 0.01736 | 0.06822 |
| Calibrated neural only | 0.03991 | 0.14333 |
| Calibrated fused | **0.01676** | **0.06325** |

The fused-minus-particle-only game bootstrap (10,000 paired resamples) is −0.000600 Brier, 95% CI [−0.001186, +0.000017], and −0.004976 log loss, CI [−0.007230, −0.002655]. The fused logistic fit uses nonnegative slopes 2.210 for standardized particle log-odds and 0.787 for the neural danger logit. The neural-only model is clearly weaker, so the head is a complement, not a replacement.

At the calibration-selected 5% FPR threshold, evaluation recall is 89.9% fused vs 86.6% particle-only, with actual evaluation FPR 6.44% vs 6.51%. At a 1% target, recall is 74.3% vs 72.2%, with actual FPR 1.14% vs 1.12%. These are immediate king-capturable candidate labels, not forced-loss predictions.

This justifies a separate **log-only integration experiment** that exposes calibrated fused risk beside the engine's current particle risk. It does not justify changing choices, adding a veto, changing the default or releasing an archive. Before any policy trial, we need to implement the calibrated score in an isolated arm, measure exactly which actions it would alter on the frozen actors, run the full safety and legal-move checks, then reserve an untouched test shard for one final confirmation.

Reproduction and data: [`neural-risk/README.md`](../astra-submissions/analysis/neural-risk/README.md), [`evaluation-20261011.json`](../astra-submissions/analysis/neural-risk/evaluation-20261011.json), and the retained joined rows under [`run-20261011`](../astra-submissions/analysis/neural-risk/run-20261011/). No player decision changed and no Elo claim is made.
