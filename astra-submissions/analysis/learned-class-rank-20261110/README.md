# Frozen learned class-ranking development check

Source/plan published to both mirrors at `1cd38b61` before the first run.
Original execution exited zero in 0.477 seconds. No fit, sweep, future295 input,
filter integration or playing candidate.

The primary population is exactly 94 original293 selected training examples,
after eight own moves, across the sixteen previously frozen training prefixes.
The quadratic ranking changes forty examples in fifteen games. Mean conditional
action log-likelihood gain at the deployed temperature two is **0.04142 nats**;
the fixed linear comparator is **−0.00388**. On all640 prefix decisions the
quadratic gain is0.01470. These are training/development values, not held-out
accuracy or a strength estimate. The metric is an action given one parent and
received observation, not the posterior across hidden parents or board states.

All five necessary conditions pass. The only earned next step is a separate
independent-cohort design, with the old gates and the current295 study preserved.
The training result can be optimistic. See concentration.json for per-game and
leave-one-game-out descriptions; no threshold or model was selected from them.

Checks cover22,338 actions,1,156 capture actions,16,445 masked actions,
5,120 powered-sum comparisons and163 entire capture-observation identities.
Both local native libraries agree on640 board/observation/metadata states and
move orders. There are194 active-history contexts; the independent double
history expression differs from native float by at most5.46e-7.

The class core accepts only a hypothetical parent and permitted received view.
Replay truth constructs the offline label/view; it is not a scoring input.
The existing native confidence spectrum is retained. Its post-merge fitted-guard
measure, future caps/support/history and clock cost remain unproved.

See plan.json, result.json, cases.json, execution.json and receipt.json.
