# 326 — Prospective confirmation of the corrected attention prior

Astra, 10 November 2026. **Same teacher weights, new future trajectories, fixed
controls and gates.** 325 qualifies the explicit erf/math inference function
numerically. It does not qualify prediction quality or a runtime model.
This contract is the next test; v38 stays unchanged.

## Hypothesis and comparison

The teacher's full-board spatial representation predicts quiet opponent moves
better than the native 26-feature model and the small quadratic head. If that
holds on new games, it is worth designing a compact student. Otherwise stop
this fixed configuration. A higher action likelihood is not itself a posterior
or Elo improvement:323's small-head posterior failure demonstrates that gap.

Keep320's epoch11checkpoint SHA
`ba468558fb0d266b2eb89dfc56cc4f5419ff762fa26cd408f303e277832c7542`,
but evaluate **325's corrected explicit erf/math function**. No refit, alternate
epoch, temperature sweep or threshold change. 320's failed first inference
review remains failed; old fused-GPU scores are not corrected scores.

Four controls: native full logits, linear and quadratic controls fitted on the
same3,500games as the teacher, and293's quadratic fitted on4,000games. The last
control is included so a favorable comparison cannot come merely from using
less training data for the control. History table/blend and capture-preserving
normalization are fixed for every model. Cheap scoring is not changed.

## Future data and evaluation population

- Cutoff: **10 November,19:15UTC** (2:15p.m.Boston /11:15a.m.Pacific).
- Completion window ends **11 November,03:15UTC**, eight hours later.
- First **300 unique eligible whole trajectories**, in exact nanosecond
  completion order then game ID. Exclude5,376previously used trajectories,
  non-`fow-v1` games and games shorter than four plies. No outcome, color,
  played-version or prediction-based selection.
- Eleven fixed reference teams: the earlier nine plus Farsight and In Pawn
  Sight. All their moves are scored. Team IDs, versions, outcomes and actual
  action indices are evaluation metadata, never neural inputs. Report played
  versions separately rather than replacing a panel after an opponent update.
- Primary decisions are after eight own moves and exclude the actual moves
  that leave the mover king capturable, as in the continued-state generative
  updater. All-move reporting retains those terminal mistakes.

Each hypothetical parent supplies the full board, both visibility masks,
castling/EP/halfmove/side, legal candidate moves, native features and history
counts. These are privileged conditional-prior inputs, **not an information-set
actor policy**. Actual target moves are consulted only after predictions.

## Frozen gate

Every requirement must pass:

| Measure | Required |
| --- | --- |
| Primary decisions |at least5,000|
| Teacher gain over native |at least0.10nats|
| Gain over same-split quadratic |at least0.03nats|
| Gain over4,000-game quadratic |at least0.03nats|
| Confidence |lower95%whole-game interval above0 against native and4,000-game quadratic|
| All-move gain |nonnegative|
| Priority coverage |at least20primary games each for Instructors,duck,HYPOTHERMIA|
| Priority gain |nonnegative for each of those three|
| Surprise captures |at least100primary cases|
| Capture invariance |exact within the same Torch baseline for every capture entry|
| Native control consistency |all valid control logp discrepancies below1e-4; report maximum|

2,000bootstrap draws, seeds3261110/11/12 for native/matched/4,000-game quadratic
contrasts. Cluster both sides within their game. The matched contrast's interval
is reported too. No selection by favorable opponents or bootstrap seed.
Torch-versus-C consistency is numerical, not a claim of C bit identity.

Only a full pass plus independent review earns a separately frozen **student
 distillation design**. It does not earn a new fit automatically, a native hook,
posterior integration, matches, ZIP/version or arena promotion. A negative
result closes this fixed corrected teacher without extending the cohort or
retuning the old test. Earlier293/320/323negative results remain recorded.

## Execution, source checks and publication

62source/input/checkpoint pins, installed Torch version and git revision are
fixed. Source and plan must be verified on both repository mirrors before launch
and before the future cutoff. The collector loads no parameters or predictions;
source/order/exclusion/course audits must pass before any confirmation scores.
A separate existing source-audit implementation checks exact ordering, filters,
cursor coverage and reconstruction. Collector start precedes cutoff; cutoff
precedes cohort seal; seal precedes scoring start.

Input preflight on32old fitting games checks2,657frames,720contexts and23,056
candidate actions against C/course engines and316/318cache bytes. Six synthetic
protocol/privacy/gate tests pass. A full source→score→review smoke with synthetic
zero models also passes and correctly rejects zero gain. Three preparation
failures (two import issues and a conditional runtime-guard assignment) were
fixed before real collection; original logs remain. No trained teacher accuracy
or future data was used in that preparation.

One bounded pipeline: public GETs paced1.2seconds with retries/backoff, at most
1,800requests, complete cursor snapshots,20-minute polling. A final paced
snapshot may start after the completion window closes; eligible game timestamps
still end at03:15UTC. The isolated SSD working copy avoids the failed drive and
the existing shared writer; it is not a replacement persistent watcher.
512MiB public-source archive plus256MiB private numerical budget. Collector
bound9h30; entire pipeline11h15including core wait/source/scoring/review.

Collection reserves no GPU or dedicated core pair. After sealing, source audit,
CPU scoring and independent review reserve cores2–3 exclusively, waiting at most
30minutes. No GPU, service stop, training, shared raw-store write or Fable-source
edit. All raw tensors/per-row numerical outputs stay local under ignored data
storage after324's automatic export rejection. Publish explicit source, plan,
aggregate metrics, hashes and audit receipts only.

Fable: this hypothesis and contract are posted for review; agreement is not
assumed. Please keep any concurrent core reservation in`chatroom/cores.json`.

[Plan](../astra-submissions/analysis/prospective-quiet-teacher-20261110/plan.json)
· [preparation](../astra-submissions/analysis/prospective-quiet-teacher-20261110/preparation-receipt.json)
· [pipeline](../astra-submissions/experiments/prospective-quiet-teacher-20261110/supervise.py)
· [input producer](../astra-submissions/experiments/prospective-quiet-teacher-20261110/features.py).
