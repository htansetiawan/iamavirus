# Astra 146 — Pinned, runnable next experiment for review

Prepared the concrete original-loss versus auxiliary-loss PPO comparison:
same 20.36M v6-l CNN and critic, fresh optimizers, 60 iterations per arm, fixed
seed/league, one GPU hour per arm. The candidate adds
`0.1 * (BCE_risk + 0.25 * O(M) separation_loss)`. No sweep or training started.

All ten distinct actor/replica checkpoints and the critic load and run on CPU.
Verified the initial checkpoint's actual v6 dataset content digest over all
25,070 games. Froze 128 recent own-game validation replays (5,843 decisions),
disjoint by game ID/full move sequence from all v6 splits and independently
referee-validated. Prepared an isolated patched trainer/native library; its full
module imports successfully. Hashes, configs and bounded launcher are included.

Compatibility finding: current PPO loads CNN metadata. The old attention model
used in note 143 is not a drop-in training initializer; this proposal explicitly
uses the compatible Fable CNN and tests the auxiliary mechanism.

The GPU was available at the preflight check (0%, 1126/48935 MiB); no service was
interrupted or lease acquired. New training remains pending the requested plan
review. This experiment improves the standalone PPO training path; it does not
by itself improve the deployed C search table. Henry/Fable should choose whether
to run this bounded comparison or prioritize C-search policy/advantage integration.

[Concrete plan, stop criteria, configs, checkpoint/source pins and validation set](../astra-submissions/analysis/deeprl-table-audit-20261025/risk-run-preflight/README.md)
