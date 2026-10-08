# Broader training data before model compression

Expanding the training pool improves both completed models' held-out metrics.
The full CNN's actual hybrid decisions are nevertheless tied with the existing
v4 model. Small attention improves policy safety but is also tied in the
completed engine comparison. Large attention is still training. None is an
arena release, a demonstrated stronger teacher, or an Elo gain.

The [predeclared design](full-data-design.json) expands 512 training games to
all 3,766 games in the same frozen v4 training shard. Source `09fd15f`, seed 253,
feature version 2, optimizer and architecture definitions stay fixed. Each arm
runs 6,000 updates from a fresh initialization. Validation remains the same
64 games / 5,179 decisions; 5,167 decisions have a safe legal alternative.
The test split is neither copied nor used. This is supervised training,
separate from EMA self-supervision and teacher-to-student distillation.

| Model and pool | Policy NLL, lower is better | Hidden-enemy NLL | Avoidable fatal top-1 proposals / 5,167 | Demonstration hit@4 |
| --- | ---: | ---: | ---: | ---: |
| CNN, 512 games, 6,000 updates | 2.6979 | 1.2476 | 170 | 57.54% |
| CNN, 3,766 games, 6,000 updates | 2.4094 | 1.1136 | 157 | 59.84% |
| Small attention, 512 games, 6,000 updates | 2.6277 | 1.1644 | 163 | 55.40% |
| Small attention, 3,766 games, 6,000 updates | 2.4657 | 1.1310 | 137 | 57.58% |

Full-pool runs each saw 372,874 training decisions versus 374,435 in the
512-game runs: equal updates do not imply exactly equal decisions. Recorded
training-loop time was 1,171.7 seconds for CNN and 1,578.5 for small attention.
These shared-host timings include intermediate validation and are not GPU
FLOP counts or an equal-compute architecture comparison.

Within CNN, the policy-NLL change is -0.2886 with a paired game-bootstrap 95%
interval [-0.3310, -0.2478]. The avoidable-fatal change of 170 to 157 remains
inconclusive, interval [-0.651, +0.171] percentage points. Against the earlier
2,000-update small-pool CNN, fatalities fall from 182 to 157, interval
[-0.805, -0.174] points; that comparison also changes the update budget.

Within small attention, policy NLL improves by 0.1620 and avoidable fatalities
fall from 163 to 137, interval [-0.835, -0.183] points. Against its earlier
4,000-update small-pool checkpoint, fatalities fall from 181 to 137, interval
[-1.393, -0.370] points, again with different update budgets. Broader data
therefore helps beyond simply beating the older overfit final checkpoints.

With the full pool, small attention has 20 fewer fatal policy proposals than
CNN, interval [-0.734, -0.060] points. Its danger Brier score improves from
0.03605 to 0.03303, while policy NLL and demonstration hit@4 worsen. Recall at
a validation-derived 5% false-positive rate is 59.91% versus CNN's 51.66%; these
are descriptive operating points, not calibrated deployment thresholds.
The result supports testing actual engine behavior, not declaring attention
universally better. The paired intervals cover validation games, not variation
across training seeds. Repeated use of this development validation set is a
further limitation.

## Full CNN inside the hybrid engine

The CNN export matches PyTorch over 321 recurrent decisions: zero parity
failures, maximum absolute difference 3.82e-6. Graphs total 7,508,085 bytes.
The [engine design](cnn-hybrid-design.json) fixes one features-v2 binary,
2,048 particles, 400,000 nodes, seed 777, prior 1, prediction/history/root/frontier
0 and book off. Only the model changes from Fable's v4 graphs to the full CNN.

| Model | Terminal fatal / 432 | Avoidable fatal / 364 |
| --- | ---: | ---: |
| Existing Fable v4 | 165 | 97 |
| Full-data CNN | 164 | 96 |

Only 20 of 432 terminal moves change, including six of the 364 avoidable
positions. Two fatalities are saved and one is introduced. The fatal-rate
difference is -0.23 percentage points, interval [-1.16, +0.46]: inconclusive.
All 906 initial moves match. Better prediction metrics alone have not improved
this engine's choices. These repeatedly used histories are not a sealed test,
and neither model has been compared here with the active arena's features-v1
model. Full report: [cnn-hybrid-comparison.json](cnn-hybrid-comparison.json).

The r10d archive has a features-v1 observation tracker. Swapping these
features-v2 graphs into that archive would violate the input contract. Any
later clocked integration needs a matching tracker and input-parity checks.

## Small attention inside the same hybrid

The small-attention export also passes all 321 recurrent decisions, maximum
absolute difference 4.89e-6. Its two graphs total 6,706,328 bytes. The
[attention design](attention-hybrid-design.json) uses the same frozen binary,
corpus and settings as the CNN comparison; the existing control is reused with
every input hash verified.

Small attention makes 164 terminal fatal choices and 96 avoidable ones: the
same counts as full-data CNN. Relative to Fable v4, 26 terminal moves change,
including 13 avoidable positions; two fatalities are saved and one introduced.
Its rate difference and interval are therefore the same inconclusive values
as the CNN comparison. Relative to full-data CNN, 24 terminal moves change,
one fatality is saved and one introduced; the rate difference is zero with
interval [-0.69, +0.69] percentage points. All 906 initial moves still match.
Receipts are [attention-hybrid-comparison.json](attention-hybrid-comparison.json)
and [full3766-cnn-vs-attention-hybrid.json](full3766-cnn-vs-attention-hybrid.json).

The policy-only safety improvement has not transferred to fewer fatal engine
choices in this gate. This does not test offensive play over complete games
or ordinary middlegame decisions: terminal positions and initial moves are a
limited sample. It does mean neither completed model has demonstrated the
downstream advantage required to promote it or start compressing it for release.
Training larger models remains a measured experiment; using their belief/value
heads in search would require a separate design and evaluation.

## Implications for larger teachers and INT8

Training capacity, learned representation size, and numerical precision are
separate choices. A larger model may be deployed directly, or supply soft
targets to a smaller student; either deployed model can then be quantized.
Current weight storage is small relative to arena memory. The useful gain is
better moves within the CPU clock budget.

The earlier partial-INT8 audit reduced graph bytes from 7.51 MB to 2.87 MB but
introduced one fatal policy proposal without saving another. It remains an
experiment. The [precision specification](../../specs/teacher-student-precision.md)
requires recurrent-state, tactical-choice, full-engine and clocked validation.
Distillation and another precision audit wait for a demonstrated model benefit.

The JSON comparison files in this directory retain metric denominators,
intervals and experiment identity checks. Full training/export files are under
`/media/henrytan/seagate/iamavirus/astra/representations/capacity-v4-full3766-20261008/`.
