# Larger teacher capacity: first controlled pilot

The larger attention model has not earned deployment or a distillation role.
Small attention improves hidden-piece prediction at the same update count;
extra CNN training closes that gap within a similar time budget. Larger capacity
alone has not improved this short experiment. This does not establish what the
architectures can achieve after convergence or with different objectives/data.

Frozen source: `09fd15f83f7b1cb4ccd7d0aae2d7e6bec7773a82`. Features-v2, seed
253, batch 4, window 32, AdamW at .0003, identical multitask loss and player
weights. Sampled pool: 512 training games. Validation: 64 games / **5,179
decisions**, including 12 decisions with no safe action. The test shard was not
copied into the run. The three initial arms saw the same **62,304 training
decisions**. This is supervised learning, not the separate EMA self-supervision
experiment or teacher-to-student distillation.

| Model | Parameters | Updates | Recorded training-loop seconds | Policy NLL ↓ | Hidden-enemy NLL ↓ | Avoidable fatal top-1 proposals ↓ | All top-4 fatal despite an escape ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CNN | 1.87 M | 1,000 | 170.6 | 2.6062 | 1.4615 | 192 | 46 |
| Small attention | 1.63 M | 1,000 | 251.5 | 2.6960 | 1.2725 | 204 | 57 |
| Large attention | 4.76 M | 1,000 | 499.6 | 2.7249 | 1.2937 | 215 | 46 |
| CNN continuation | 1.87 M | 3,000 | 530.9 | 2.5311 | 1.1940 | 174 | 37 |
| Small attention continuation | 1.63 M | 2,000 | 487.8 | 2.6065 | 1.2175 | 193 | 45 |
| CNN longer continuation | 1.87 M | 6,000 | 1,067.5 | 2.6979 | 1.2476 | 170 | 41 |
| Small attention longer continuation | 1.63 M | 6,000 | 1,466.5 | 2.6277 | 1.1644 | 163 | 39 |

Avoidable-fatal denominators are 5,167. These are **unfiltered policy proposals**;
the hybrid's particle risk filter, search union and final decision can change
them. No game-playing strength or Elo is measured here.

The continuation arms preserve the original runs and optimizer checkpoints.
Their recorded training-loop totals sum across restarts. This wall-time proxy
includes intermediate evaluation and excludes setup/final evaluation. The CNN
budget is 6.3% above large attention and small attention is 2.4% below it; this is
an approximate compute comparison, not a FLOP-matched experiment. Continuations
saw 187,202 and 124,872 decisions respectively.

Paired game bootstrap comparisons are saved alongside this note. At equal
1,000 updates, small attention improves hidden-enemy NLL by .1890, 95% interval
−.2233 to −.1522, but worsens policy NLL by .0898, interval +.0642 to +.1155.
With similar training time, CNN and small attention have an inconclusive
hidden-enemy NLL difference (+.0235 for attention, interval −.0027 to +.0522).
Small attention's danger Brier is .03839 versus CNN's .04060; the task tradeoff
therefore persists. Large attention at 1,000 updates has worse policy and
hidden-enemy likelihood than both continued controls. Its avoidable-fatal rate
versus CNN is inconclusive; versus continued small attention the increase is
.426 percentage points, interval +.074 to +.831. Intervals cover games, not
training-seed variation.

Decision: keep FP32 controls. Quantizing this large checkpoint would test
compression, but it would not yet compress an improved teacher. Continue a
bounded convergence experiment before rejecting capacity: compare all three
at the same longer update count, then repeat a promising result with another
seed. Track learning curves, tactical tails and task tradeoffs; do not select
solely on averaged losses. Any selected model still needs the actual hybrid
decision and clocked-match gates before quantization/distillation promotion.

Large checkpoints and full reports:

- `/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-seed253-20261008/`
- `/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-equal-compute-20261008/`

`provenance.json` records immutable source, dataset, checkpoint and report hashes.
Use `learning_experiments.compare_pilots` with `--control-step` and
`--candidate-step` to reproduce comparisons with different update budgets.

The longer rung in `continuation-design.json` **started at 02:10 UTC on
2026-10-08**, after Fable released the GPU and cores 3–4. It continues all three
models to 6,000 total updates, preserving optimizer state and original outputs,
with evaluation every 2,000 updates. Source/data preflight passed. The launch
tool checks the lease before each arm and releases only its own lease afterward.
Its training code remains the same frozen revision as the first pilot. Live
status and checkpoints are under
`/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-convergence-6000-20261008/`.
Starting this run is not evidence that the larger model is better.

The CNN and small attention arms have now completed 6,000 updates and each saw
374,435 training decisions. The larger attention arm is still running. At the
same update count, small attention has lower policy NLL by .0703 (paired
game-bootstrap 95% interval −.1155 to −.0279) and lower hidden-enemy NLL by
.0832 (−.1138 to −.0505). Its 163 versus 170 avoidable fatal proposals give an
inconclusive rate difference of −.135 percentage points (−.524 to +.253).
The danger-Brier and all-top-four-fatal differences are also inconclusive.
These are the predeclared equal-update results, not equal training-time results.

The learning curves matter: CNN policy NLL was 2.5202 at 2,000 updates and rose
to 2.6979 at 6,000; small attention was 2.5603 at 4,000 and rose to 2.6277 at
6,000. This is consistent with overfitting or increasing overconfidence on the
512-game training pool. Beating the CNN's last checkpoint does not establish
beating an earlier-stopped CNN. Nor do these curves prove which checkpoint
plays stronger games; the different heads and tactical tails peak at different
times. The next allocation decision should consider more distinct training
games and a specified stopping/selection rule, after the large arm completes.

`cnn-vs-attention-6000.json` contains the paired comparison.
`convergence-partial-provenance.json` pins the two completed checkpoints and
their complete recorded validation curves. The test split remains untouched.
