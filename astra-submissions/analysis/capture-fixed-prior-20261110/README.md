# Capture-fixed learning: positive full result, combined gate fails

The new constrained prior learns useful probabilities while preserving capture
likelihoods. Its **full path meets every predictive condition** on the later
window. The combined cheap/full configuration still fails: cheap interactions
improve0.01858nats over their matched linear control, below the required0.02000.
Preserve that decision. No posterior integration, extra fit, playing batch or
release follows automatically.

| Later-window primary metric | Cheap | Full |
|---|---:|---:|
| v38 baseline NLL | 2.90316 | 2.66530 |
| Capture-fixed linear NLL | 2.89136 | 2.64904 |
| Capture-fixed quadratic NLL | 2.87278 | 2.61409 |
| Gain over baseline, nats | 0.03038 | **0.05120** |
| Whole-game bootstrap95% interval | [0.02667,0.03409] | [0.04665,0.05615] |
| Gain over matched linear | **0.01858 — fails0.02** | 0.03495 |
| All-move gain | 0.02654 | 0.04480 |
| Surprise-capture gain | exactly0 | exactly0 |
| Capture target log-likelihood difference | exactly0 | exactly0 |

Evaluation covers17,846 primary continuing decisions and1,817 surprise captures
from400 later games. Every one of38,933 available capture-action rows retains
its native log-likelihood bits in each mode/model check. Only relative
non-capture probabilities change; total capture/quiet mass and the empirical
history blend stay fixed. This does **not** establish sequential posterior
quality or king safety.

## What was learned, with the limits visible

| Post-hoc primary slice | Decisions / games | Full gain over baseline |
|---|---:|---:|
| Non-captures | 13,620 /397 | +0.06709 |
| Moved piece hidden from victim afterward | 11,024 /396 | +0.08551 |
| Moved piece visible afterward | 2,596 /379 | **−0.01113** |
| Non-capturing check | 453 /267 | +0.64772 |
| Non-capturing check, moved piece hidden | 290 /201 | +0.61909 |
| Non-capturing retreat check | 56 /46 | +0.39623 |

These overlapping slices are descriptions, not extra gates, independent tests
or causal playing evidence. The visible-move regression remains visible.
Full-model mean gains are positive for all nine reference movers: duck+0.05803
over2,766 primary decisions/82games; Instructors+0.03874 over2,035/61; Greek
Gift+0.06172 over2,120/58. Those are **prediction figures, not game scores**.
All teams and coefficient tables are in[descriptive-analysis.json](descriptive-analysis.json).

## Separate an observed event from an ambiguous move

The victim always sees its own pieces. During an opponent turn that count
decreases by one exactly when the opponent captures. Capture versus non-capture
is therefore observable even if the attacker is hidden. A separate check
corroborates the rule on all34,574 moves of these400 sequences:7,437 captures,
27,137 non-captures, zero mismatches.

Given an **identical parent belief, RNG and fixed update schedule**, a view
showing victim-piece loss admits only capturing successors. Their likelihoods
are unchanged, so a correctly integrated head would preserve that entire
one-step capture update. A future implementation could skip the head on those
turns. This is an algebraic deduction, **not an integrated posterior result**:
earlier quiet updates and clock thinning can change the parents. Overall
safety is unproven. It does not justify selecting only a favorable new slice.

## Data and verification

Frozen cohorts:4,000 train games fromNov2–7,400 validation fromNov8 and400
later evaluation fromNov9, complete-sequence deduplicated. Training uses up
to24 hash-selected reference-player decisions/game:92,940 decisions.
Validation has21,932. Four CPU fits, one seed/ridge,12epochs and epoch0 as an
option. All choices are locked before22,040 later decisions are extracted.
Some games may have appeared in taxonomy/intelligence work: this is a
chronological fit holdout, not pristine prospective confirmation. Features
are the existing hypothetical-parent representation, not an information-set-
realizable opponent policy.

Initial preparation read/hashed all4,800 full sources. The same SHA-matching
move sequences were embedded from the SSD SQLite cache before fitting,
preserving the initial compressed plan and all selections. Nine source
replays/677 frames tie reconstruction to recorded data. The simulator then
feeds training without further random raw-directory opens. No controlled
disk speedup is claimed.

Independent review checks splits, selection and bootstraps;4,190,730 scalar
action calculations (max native/scalar log error6.12e-7);233,598 repeated
capture checks; and34,974 C/referee frames reconstructed from immutable
recorded moves. This is not a second fit or a fresh read of every raw replay.
Address/undefined/leak sanitizers pass. Torch checks zero capture gradients,
padding and the deployed history mixture.

Source and34-pin plan were verified on both mirrors at
`6b28258bd60e9747526ac987490faf746dae3c22` before fitting. Original80006 exits0
after91.678s; independent reviewer2824 exits0 after16.921s. No fit, epoch
budget, source case or test is repeated. All experiment processes are terminal;
cores0–1 released, GPU service untouched.

The full model remains a research artifact for Fable/human review. A new
**prospective full-only hypothesis**, with cheap unchanged, would need a
separate reviewed design and later data. It cannot be authorized by declaring
this combined gate passed. No experiment or integration follows automatically.
No arena version is reserved and no strength claim is made.

- [Result](result.json),[independent review](independent-review.json),
  [selection lock](selection-lock.json),[all predictions](decisions.jsonl.gz).
- [Full model](22-quadratic-model.json),[cheap model](14-quadratic-model.json),
  [selected controls](selection.json),[post-hoc descriptions](descriptive-analysis.json).
- [Plan](plan.json),[preflight](preflight.json),
  [cache receipt](sequence-cache-receipt.json),[cleanup](cleanup.json).
- [Design](../../capture-fixed-prior-design-20261110.md),
  [source](../../experiments/capture-fixed-prior-20261110/).
