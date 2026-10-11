# SSL downstream transfer: useful at equal fine-tuning, insufficient at comparable time

**Do not scale or deploy this SSL recipe based on this pilot.** Its equal
fine-tuning gains do not justify its extra pretraining cost for the combined
policy/belief/danger objective. The experiment also identifies harmful recurrent
state dependence in the hidden-piece head. No arena ZIP or runtime changed.

## Experiment identity

The existing actor-only teacher/student checkpoint received 1,000 supervised
updates. A fresh supervised-only model received 2,500 updates. Both used the
same frozen 34-file source snapshot, model, data, native rules, seed 253,
batch four, 32-event training windows, complete causal prefixes and AdamW
settings. Exact hashes are retained in each `run.json` and `inventory.json`.
The source was recovered from commit `063e87d` and every recorded file hash
verified. No test shard was loaded.

This is deliberately a **features-v1** historical allocation experiment.
Those features conflate visible-empty and hidden squares in one channel.
Current features-v2 models and runtime contracts remain unchanged. This result
does not establish that SSL will behave identically after that feature fix.

All reports cover the same **64 validation games, 5,179 decisions, 49,330
hidden enemy squares and 158,105 candidate danger labels**. Games are held out
from training, but this validation set has been reused in architecture research.
The 10,000-sample paired game bootstrap measures game variation, not training
seed variation or selection across experiments.

The first attempt to resume the old supervised checkpoint correctly failed
the source guard. That checkpoint predates six file-hash/presence changes.
Rather than bypass the guard, the control was retrained from scratch using the
SSL-transfer source. Failed status/logs and original checkpoints remain intact.

## Main task metrics

Lower is better in all three columns. Times are training-loop wall seconds,
including intermediate validation but excluding setup and final validation.

| Training allocation | Loop time | Policy NLL | Hidden-enemy NLL | Danger Brier |
| --- | ---: | ---: | ---: | ---: |
| Supervised 1,000 | 299.17 | 2.66143 | 1.36804 | 0.041086 |
| SSL 1,000 + supervised 1,000 | 704.99 | 2.62605 | 1.22418 | 0.042371 |
| Supervised 2,250 | 694.18 | 2.59420 | 1.24255 | 0.038482 |
| Supervised 2,500 | 773.26 | 2.60037 | 1.18775 | 0.036731 |

Use the retained logs for exact times; the 1,000-step control time is rounded
in this table. SSL pretraining contributes 408.97 seconds and fine-tuning
296.01. Fresh control process wall time was 808.28 seconds including setup
and final validation. Separate CPU memory probes used cores 4–5 during some
control training on cores 6–7, so these timings are not isolated throughput.

At equal downstream updates, SSL minus control:

- Policy NLL **−0.03538**, game-bootstrap interval [−0.04588, −0.02506].
- Hidden-enemy NLL **−0.14386**, [−0.16035, −0.12759].
- Danger Brier **+0.001285**, [+0.000874, +0.001728] — worse.

Before the longer control reached the SSL time budget, the recorded rule was:
use the first 250-update checkpoint at or above the 704.99-second total. That
selects **2,500 updates**, about 9.7% more loop time; this is not exact compute
equality. SSL is worse on all three main metrics at that checkpoint:

- Policy NLL **+0.02568**, [+0.00491, +0.04577].
- Hidden-enemy NLL **+0.03642**, [+0.02126, +0.05225].
- Danger Brier **+0.005640**, [+0.004051, +0.007297].

The adjacent lower-time checkpoint is shown to expose the tradeoff. At 2,250
updates, just 1.5% below SSL's loop time, SSL still improves hidden-enemy NLL
by 0.01838 but loses on policy and danger. Thus this is not evidence that
supervised-only dominates SSL at every equal-compute point or for every piece
type. The full learning curves and per-piece comparisons are retained.

At 5% empirical false-positive rate, danger recall is **51.34%** for the
2,500-update control versus **34.78%** for SSL. These are descriptive ROC
points, not calibrated deployment thresholds or evidence for a veto.

## What the recurrent state contributes

`ssl_memory_probe.py` runs two CPU passes using each frozen checkpoint:
normal recurrence, then GRU state reset before every observation. It keeps
the exact same current observations, explicit last-seen/age planes, public
scalars and legal candidate arrays. Truth labels score outputs only. It does
**not** remove all history, retrain a memoryless model, or demonstrate that
memory is unimportant in Fog of War.

| Checkpoint | Hidden-enemy NLL, normal | Reset | Reset minus normal, 95% game interval |
| --- | ---: | ---: | --- |
| Supervised 1,000 | 1.36804 | 1.15322 | −0.21482 [−0.23449, −0.19544] |
| SSL + supervised 1,000 | 1.22418 | 1.03516 | −0.18901 [−0.20155, −0.17651] |
| Supervised 2,500 | 1.18775 | 0.97484 | −0.21292 [−0.23208, −0.19338] |

The hidden-piece head gets worse with its trained recurrent state in all
three checkpoints. Policy changes are small; the longer control's danger
change is indistinguishable from zero (+0.000080, interval −0.000958 to
+0.001062). Normal CPU metrics match stored GPU metrics within 1e-5 for all
reported aggregate fields, ruling out that device difference as the source of
these large hidden-piece changes.

This calls for repeating the diagnostic on the current features-v2 model and
then inspecting recurrent training/state use. Do not remove runtime recurrence
from this legacy intervention alone. The explicit last-seen planes still
provide memory even in the reset arm.

## Reproduction and disposition

- Tools: `../../tools/ssl_transfer_report.py`, `ssl_memory_probe.py` and the
  report-boundary tests. Tests cover weighted game aggregation and rejection
  of different games, denominators, feature source, native source and seed.
- `inventory.json` verifies 38 copied source artifacts, including every
  validation checkpoint report and both training traces. Compressed copies
  have hashes for both stored and decompressed bytes.
- `checkpoint-hashes.json` identifies five immutable checkpoints on Seagate.
- `timing-comparison-plan.json` records the comparison rule before the time
  threshold was reached. Source identity remains strict throughout.
- `memory-comparison.json` retains game-level intervals and CPU/GPU checks.

The GPU experiment and all CPU diagnostics completed successfully; the GPU
claim was released. This pilot does not pass a playing-strength gate and is
not packaged. Next: reproduce the memory diagnosis with features-v2 before
allocating a larger SSL run; test any resulting change on full search games.
