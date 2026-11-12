# One actual multi-world teaching decision

November 11 UTC. The fixed size-only selector in 383 chose White's fifth
decision, before ply 9 of the already-used v38 win `c8ozqj0m`. Recorded own
moves d4, Bf4, e3, Nd2 are forced; the engine receives only White views/clocks.
The same immutable 375 control and annotation binaries, history file and
Stockfish are reused. No source change, build or new candidate.

| Quantity | Verified value |
| --- | ---: |
| Native retained positions | 128 |
| Distinct piece arrangements among them | 106 |
| Default weighted draws with replacement | 32 |
| Distinct sampled positions | 2 |
| W98: retained weight / draw count / chance share | 93.7145% / 29 / 90.625% |
| W36: retained weight / draw count / chance share | 6.2280% / 3 / 9.375% |
| Other 126 positions: retained mass / chance share | 0.0575036% / 0% |
| Guarded moves / excluded / searched actions | 41 / 2 / 39 |
| Initial child scores, both worlds | 78 |
| Final trace nodes / information sets / PCFR calls | 131,943 / 1,790 / 1,140 |

The default guards use the whole retained population in this small case;
Qd1–g4 and Qd1–h5 are removed by combined king/queen risk. Every remaining
action is legal in every independently enumerated consistent position.
The two initial decision nodes share root information-set ID 0.

## Exact arithmetic reproduced

Independent SplitMix64, cumulative weights and inverse-CDF selection produce
the same 32 indices in order. Repeated indices merge to count/32. Logged
stored weights normalize correctly; the entire eight-ply likelihood model
is not independently refitted or recalibrated by this check.

For g1f3, the initial child scores are +29 cp in W36, +30 cp in W98.
`(3/32)tanh(29/400)+(29/32)tanh(30/400)=0.07462658597900756`.
The first 39-action uniform strategy has value −0.20181080118534167;
instantaneous regret is 0.2764373871643493. Its second strategy probability
is 0.04452570476997496. All actions' first two updates and final positive
`regret + last` normalization reconcile independently.

The final trace executes **g1f3**, probability 0.4952295884785439.
Control also executes g1f3; the recorded arena action is c2c3. This is a
shortened two-second teaching search, not the original arena tree, a policy
equivalence check, performance comparison or playing-strength experiment.
Both search attempts are preserved and the core lease is released.

## State identity qualification

Course enumeration gives native position-projection counts
`1,1,14,1,1,1,14,14,128`. Retaining distinct halfmove counters gives 155
states at the final point, with 27 native positions having two alternatives.
The native key ignores halfmove/repetition and private histories, while
retaining piece placement, side, castling and en-passant. Every stored
native counter is consistent; the representation is not lossless over all
game histories. No new candidate or fifty-move-rule failure is inferred.

Replay truth joins W98 only after execution. One realized high-weight world
does not prove general probability calibration. Search sampling retains
the 126 unsearched positions in the belief for subsequent observations.

The first reviewer stopped because it wrongly required all 128 piece-board
strings to be distinct. That failure is retained in
[first-review-failure.json](first-review-failure.json). Initial child blocks
are now associated by the pinned builder's sequential sample order and
checked against each sampled board/action list. The corrected review passes
without another bot or scorer call.

## Artifacts

- [Frozen plan](plan.json), [selected prefix](selection.json).
- Original [probe](probe-execution.json), [control](control-execution.json)
  and [trace](trace-execution.json) execution records.
- [Independent result](result.json), [figure source hashes](figure.json),
  [closure review](closure-review.json).
- [Runner](../../tools/trace_multistate_presentation.py),
  [reviewer](../../tools/review_multistate_presentation.py),
  [plotter](../../tools/plot_multistate_presentation.py).

Private input, original stdout/stderr and immediate previous page are in
`data/astra-spool/presentation-multistate-20261111/`. The saved previous
Markdown matches the 376 closure hash. The initial cropped-label figure
draft is retained privately; the final figure changes layout only.

No model fit, GPU, match, candidate, release number, shared engine edit,
service, commit, push or website deployment. Earlier negative gates stand.
