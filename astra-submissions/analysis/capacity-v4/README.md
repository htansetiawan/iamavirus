# Larger teacher capacity: completed 6,000-update comparison

The larger attention model improves likelihood on hidden enemy pieces, but it
has not earned deployment or a distillation role. Its policy proposals and
danger estimates do not beat the smaller attention control. The learning curves
also warn against simply training longer on the same 512 games. This experiment
measures one seed and one training recipe; it does not establish a ceiling on
what these architectures can achieve with broader data or different objectives.

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
| Large attention longer continuation | 4.76 M | 6,000 | 3,127.7 | 2.6473 | 1.1399 | 181 | 48 |

Avoidable-fatal denominators are 5,167. These are **unfiltered policy proposals**;
the hybrid's particle risk filter, search union and final decision can change
them. No game-playing strength or Elo is measured here.

The continuation arms preserve the original runs and optimizer checkpoints.
Their recorded training-loop totals sum across restarts. This wall-time proxy
includes intermediate evaluation and excludes setup/final evaluation. The CNN
budget at 3,000 updates is 6.3% above large attention at 1,000, and small
attention at 2,000 is 2.4% below it. That earlier stage is an approximate
compute comparison, not a FLOP-matched experiment. Those continuations saw
187,202 and 124,872 decisions respectively. The final 6,000-update comparison
instead matches updates and training decisions: **374,435 per arm**. Large
attention took approximately 2.13 times small attention's recorded loop time.

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

Decision: keep FP32 controls. Quantization remains a useful deployment
experiment once a model improves the required task. This larger checkpoint
does not yet establish a better policy teacher; a belief-specific teacher role
also needs downstream evidence. Any selected model still needs a second seed,
the actual hybrid decision gate, and clocked matches before promotion.

Large checkpoints and full reports:

- `/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-seed253-20261008/`
- `/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-equal-compute-20261008/`
- `/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-convergence-6000-20261008/`

`provenance.json` records immutable source, dataset, checkpoint and report hashes.
Use `learning_experiments.compare_pilots` with `--control-step` and
`--candidate-step` to reproduce comparisons with different update budgets.

The longer rung in `continuation-design.json` started at 02:10 UTC on
2026-10-08 and all three arms were confirmed complete by 03:23 UTC. It preserved
optimizer state and original outputs, with evaluation every 2,000 updates.
Source/data preflight passed. Training used the same frozen revision as the
first pilot. The runner released its GPU lease on completion; cores 3–4 were
also released in the shared resource ledger.

At 6,000 updates, small attention has lower policy NLL than CNN by .0703 (paired
game-bootstrap 95% interval −.1155 to −.0279) and lower hidden-enemy NLL by
.0832 (−.1138 to −.0505). Its 163 versus 170 avoidable fatal proposals give an
inconclusive rate difference of −.135 percentage points (−.524 to +.253).
The danger-Brier and all-top-four-fatal differences are also inconclusive.
These are the predeclared equal-update results, not equal training-time results.

Large versus small attention improves hidden-enemy NLL by .02445, interval
−.03768 to −.01175. Policy NLL worsens by .01962, interval −.00824 to +.04712;
avoidable fatalities increase from 163 to 181, a difference of +.348 percentage
points with interval −.265 to +1.135. Those latter differences are inconclusive.
Demonstration hit@4 does fall from 55.40% to 53.27%, with a paired interval of
−3.38 to −.81 percentage points; this measures imitation coverage, not the
availability of the objectively best move. Danger recall at a 5% false-positive
rate is 52.83% for small attention and 47.82% for large attention (descriptive
values at validation-derived operating points, not a deployment threshold).

The aggregate belief gain needs care. NLL over **all** hidden squares worsens
from .49946 to .50993, interval +.00641 to +.01433. An exploratory per-piece
breakdown finds lower pawn and king NLL but higher rook NLL (1.41386 to
1.45156, interval +.00535 to +.06904). Bishop and queen differences are
inconclusive. These six post-hoc comparisons have no multiplicity adjustment;
they motivate a targeted investigation and do not establish a stronger slider
belief model. In particular, the aggregate enemy-piece gain does not show that
we have solved the unseen rook/bishop queen-loss pattern.

The learning curves matter: CNN policy NLL was 2.5202 at 2,000 updates and rose
to 2.6979 at 6,000; small attention was 2.5603 at 4,000 and rose to 2.6277 at
6,000; large attention was 2.6217 at 4,000 and rose to 2.6473 at 6,000.
This is consistent with overfitting or increasing overconfidence on the
512-game training pool. Beating the CNN's last checkpoint does not establish
beating an earlier-stopped CNN. Nor do these curves prove which checkpoint
plays stronger games; the different heads and tactical tails peak at different
times. The next allocation decision should consider more distinct training
games and a specified stopping/selection rule. A lower-precision copy of the
last checkpoint would not resolve this training-data or objective problem.

`cnn-vs-attention-6000.json`, `cnn-vs-large-6000.json` and
`attention-vs-large-6000.json` contain the final paired comparisons.
`attention-vs-large-6000-pieces.json` contains the exploratory piece breakdown
in `PNBRQK` order. `convergence-provenance.json` pins all three completed
checkpoints and their recorded validation curves; the earlier partial manifest
is retained as history. Intervals cover held-out games, not training-seed
variation. The test split remains untouched.

A new, separately stored comparison started at 05:16 UTC on 2026-10-08 using
all 3,766 training games, the same 64 validation games and the same frozen
source. It trains each architecture from scratch for 6,000 updates, with curves
every 1,000. See `full-data-design.json` for the predeclared comparison. Its
outputs are in `capacity-v4-full3766-20261008/` on the same drive. CNN and small
attention are complete; large attention is still running. Broader data improves
both completed models. Small attention has 137 avoidable fatal policy proposals
versus CNN's 157, but worse imitation likelihood. Both actual hybrid gates are
tied: v4/CNN/small attention make 165/164/164 terminal fatal choices. See the
[broader-data report](full-data.md)
for comparisons, limitations and next gates. No model has been selected for
deployment.
