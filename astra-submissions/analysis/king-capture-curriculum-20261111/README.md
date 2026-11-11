# Paired king-capture opportunities: teach the refusal as well as the trap

The existing episode format already labels every legal action for immediate
king loss. This work extracts a focused, source-bound curriculum of **all legal
king captures of non-king enemy pieces** from 414's inspected 368-game export.
It retains safe captures and refusals alongside fatal accepted captures.
It does not train a model or add a runtime strategy.

This reuses 011/413's permitted actor prefixes, the October 9–10 tactical
auditor, 327's opportunity denominators and the existing
`TargetRecord.king_loss_by_action`. It is not a new danger-label algorithm.
Existing failed danger/response/prior/ranker/playing configurations remain
closed. Rich labels and the compressed dataset stay outside Git.

## What was built and checked

| Product or check | Result |
| --- | ---: |
| Source | 368 inspected games, both seats, 31,318 decisions |
| Selected candidate captures | 1,660 in 1,551 decisions |
| Safe capture controls | 811 |
| Fatal capture, all cover hidden before the move | 664 |
| Fatal capture, visible or mixed cover | 185 |
| Actually chosen captures | 304, including 66 fatal |
| Old hidden-cover offers reproduced exactly | All 550 |
| Referee replay frames | 31,686 |
| Counterfactual capture outcomes checked | All 1,660 |
| Complete one-ply safe sets checked | All 1,551 selected decisions |
| Candidate records by retained fold | Train 1,382; validation 99; test 179 |
| Compressed JSONL | 378,358 bytes |

The original session **72312 exits 0**. Each stored C danger target agrees with
the course referee's counterfactual outcome; complete safe alternatives agree
as well, including the actual prefix's repetition counts. The old 550 offers
match on game/seat/predecision/candidate, cover, safe set, chosen/refused and
avoidability. No older counts or source records were rewritten.

## The useful strategic distinction

Across both cohorts, **39 of 614 optional hidden-cover offers were accepted**.
Optional means the true board had at least one immediate non-losing action.
The records include repeated decisions within games, and the sample includes
all teams; these are not independent trials or a proposed strategy's win rate.

A post-hoc context breakdown supports retaining the existing “pressure before
bait” hypothesis:

| Offered piece's relationship to the king | Accepted / offers | Raw share |
| --- | ---: | ---: |
| Piece checks the king | 27 / 120 | 22.5% |
| Quiet piece | 12 / 494 | 2.4% |
| Rook checks the king | 12 / 35 | 34.3% |
| Quiet rook | 4 / 70 | 5.7% |

The rook rows are subsets of the first two rows. Positions, material, opponents
and repeated opportunities differ. This is an observational association, not a
causal pressure effect. All 664 victim-attack flags agree with full-board piece
geometry, including all 550 older check flags. A quiet bait example and a
checking bait example should therefore remain separate teaching contexts.
The piece's checking geometry is observable; its hidden cover is a target.

The learning questions are different:

- **Danger:** `P(king loss | permitted history, proposed capture)`.
- **Response:** `P(capture chosen | permitted history, available choices)`.
- **Strategy value:** whether preparing an offer improves game score after
  accounting for safety, responses and alternative moves.

Existing supervision supplies the first target and recorded choices for the
second. This curriculum does not answer the third. Labelling an offer fatal
does not mean the opponent will accept it.

## Actor/target boundary

Each record has `inputs`, `targets`, `metadata` and a stable `sample_id`.
Inputs contain packed current view, last-seen memory and ages, own rights/EP,
legal moves, side/ply/phase, the proposed capture and its visible victim role.
The feature builder receives only a permitted actor prefix and that proposal.

Targets separately contain stored king-loss risk, hidden-cover geometry, safe
alternatives, chosen/refused and the existing imitation-valid mask. One record
has invalid imitation provenance from a technical game; it remains explicitly
masked. Counterfactual risk validity is checked separately.

Game/source identity, fold, prefix fingerprint and sample ID are bookkeeping;
they must not be fed to a predictor. In particular, the cryptographic history
fingerprint is a lookup key, not a learned latent representation. Current
demonstrated choices, future observations and oracle labels cannot change the
current inputs in the five functional tests; four invalid-input subtests pass.
A test-file parenthesis error was corrected before curation, with its receipt
retained. A subsequent source change moved the prefix checksum out of inputs
and was tested before the implementation was frozen.

## Representation limit, checked rather than assumed

A post-hoc application of 233's feature-equivalence idea finds **eight groups /
38 records** with identical current view, side and proposed capture but mixed
safe/fatal targets. Current-view lookup alone cannot assign every such example
its true-board label. The complete emitted input records and recorded-prefix
keys have no mixed-label ties here, but are almost unique (1,659 groups for
1,660 records). That does not establish learnability or generalization.

No conflicting pair holds all non-memory inputs equal. These data therefore
do not isolate a causal memory benefit. Prefix keys also omit clocks absent
from `ActorRecord`; they are not complete runtime information sets.

The next runtime work still needs observable triggers, calibrated predictions
on untouched grouped data, and rules-exact action/response evaluation. Neither
the new fold names nor this curated subset undo earlier model exposure.
No fitting, risk veto, skill controller, model export or arena version is earned
by these descriptive results alone.

## Evidence and local data

- [Frozen plan](plan.json), [preflight](preflight.json),
  [final functional receipt](functional-final.xml), [original result](result.json),
  [execution](execution.json), [separate record audit](record-audit.json).
- [Offer contexts](offer-contexts.json) and [independent geometry/count audit](offer-context-audit.json).
- [Representation collisions](representation-collisions.json) and
  [controlled-memory contrast result](memory-contrast.json).
- [Selector/input source](../../tools/king_capture_curriculum.py),
  [functional tests](../../tools/test_king_capture_curriculum.py),
  [historical producer](../../experiments/king-capture-curriculum-20261111/run.py),
  [context analysis](../../experiments/king-capture-curriculum-20261111/analyze_contexts.py).

Local data: `data/astra-spool/king-capture-curriculum-20261111/candidates.jsonl.gz`.
Supplemental witness metadata stays private. All source replays, episode
shards and the actor index remain unchanged. The producer records exact local
dependencies rather than promising a one-command fresh-clone reproduction.
No API fetch, GPU, bot search/match, ZIP/version, production dataset generation,
service change or website deployment occurred. No Elo improvement is claimed.
