# Course optimism and the actual local learner

November 11 UTC. The missing S4 source check is complete using the official
course repository at `f7c4d29fd95e5629c65e0d2c9d38f71867c8ed49` (November 9).
The full pinned S4 source was read, including its proofs and convergence
qualifications. The web fetcher still times out on the HTML page. This is not a new
claim of reading every lecture or unpublished slide deck.

Primary references:

- [S4 official source](https://github.com/gabrfarina/MIT-6.7980-Topics-in-Multiagent-Learning/blob/f7c4d29fd95e5629c65e0d2c9d38f71867c8ed49/content/learning2.typ).
- [L5 RM/RM+ source](https://github.com/gabrfarina/MIT-6.7980-Topics-in-Multiagent-Learning/blob/f7c4d29fd95e5629c65e0d2c9d38f71867c8ed49/content/learning1.typ#L127).
- [L8 CFR source](https://github.com/gabrfarina/MIT-6.7980-Topics-in-Multiagent-Learning/blob/f7c4d29fd95e5629c65e0d2c9d38f71867c8ed49/content/learning_efg.typ).
- [Original PRM+ paper, Algorithm 5](https://www.mit.edu/~gfarina/2021/predictive-approachability-aaai21/predictive-approachability.aaai21.pdf#page=5),
  visually checked on page 5, with the experiment's averaging rule on page 6.

The conceptual course connection is prediction of feedback. The direct
algorithm match is to PRM+ in loss notation, after converting our local
utility vector to its negative. It does not identify PRM+ with OMWU/OGD or
transfer their convergence rates to our bot.

## Small native-source correspondence check

The shipped `cfr.c` and header match the immutable v38 source hashes.
Only a standalone driver is new. Its one local information set has three
actions; utility signals are **invented**:
`(1,0,−1)`, `(−1,1,0)`, `(−1,0,1)`. No FoW game or Stockfish runs.

An independent reference uses Algorithm 5's loss notation with rational
arithmetic and previous-loss prediction. It constructs its predicted vector
from losses and previous strategies, without reading native `last` values.

| Round | Current strategy | Clipped accumulated regret after feedback | Next strategy |
| --- | --- | --- | --- |
| 1 | `(1/3,1/3,1/3)` | `(1,0,0)` | `(1,0,0)` |
| 2 | `(1,0,0)` | `(1,2,1)` | `(1/7,4/7,2/7)` |
| 3 | `(1/7,4/7,2/7)` | `(0,13/7,13/7)` | `(0,12/31,19/31)` |

Native strategy, accumulated regret, last instantaneous regret and next
strategy agree on all rounds. The root's unused linear average is
`(29/63,43/126,25/126)`. **39 scalar comparisons pass**. The single first
native call exits zero, and source bytes remain unchanged. This verifies
local update correspondence on the fixture; it is not a convergence or
playing-strength experiment.

## Qualifications and prior work

The deployed caller uses the last/current strategy and root argmax. It does
not select the unused average. The original PCFR+ experiment averages
sequence-form strategies quadratically. Note 140 already identified the
separate missing-own-reach issue in the native local average; no new discovery
or automatic average-policy switch is claimed. This root-only check does
not validate whole-tree strategy averaging.

Antecedents: 140 (target/average audit), 162 (Obscuro's conditional
purification and last iterate), 330 (unused averages), 371/375/384
(native arithmetic and real traces). Obscuro's later use of a last iterate
is distinct from the older PRM+ benchmark's output rule. None of those
negative playing gates is reopened.

The saved previous course-map Markdown matches the 377 closure hash; the
mutable current page is updated with the primary references and qualifications.
No parameter, source implementation, model, rule, strategy selection, game,
GPU training, candidate, version, service, commit, push or deployment changed.

[Source receipts](sources.json) · [Paper receipt](paper.json) ·
[Plan](plan.json) · [Build](build.json) · [Execution](execution.json) ·
[Result](result.json) · [Closure review](closure-review.json) ·
[Driver](../../experiments/course-optimism-source-20261111/probe.c) ·
[Verifier](../../tools/verify_course_prm_mapping.py).

The third-party source files and PDF remain privately cached in
`data/astra-spool/course-optimism-source-20261111/`; their original URLs,
commit and content hashes are retained. Only our explanation and small
independently checked fixture are prepared for the repository.
