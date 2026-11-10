# Native class for the received observation — correctness complete

**Implemented and verified an isolated C component. No learned model, actual
belief update, playing policy, runtime-cost trial or strength result.**

The pure function receives a hypothetical parent position, our color and the
already permitted next observation. It uses pinned v38 move generation,
`may_match`, exact visibility and the native king-related pruning predicate.
It returns the original legal-move order, capture flags, observation-consistent
flags and an eligible quiet mask. Only this one received-view class is needed;
there is no all-class hash table or true opponent action in the core API.

This extends228's offline class helper, which derived a view from an oracle
move. Stateful replay stepping here is fixture glue. The real input would be
one existing hypothesis plus our received view. A label in result.json called
received_view_only_core means this interface distinction; it is not an
observation-only policy or a complete inference engine.

The first16existing293TRAIN games with at least60plies supply40plies each.
Fourteen explicit fixtures add en passant, promotions, castling through/into
attack, king capture, king evasion and two views impossible from the supplied
parent. They are fixed without outcome/model score selection. Both colors
are exercised. The plan/source was pushed to both mirrors before the checker.

Original98920exited0 on its first trace-check attempt in2.088s:

| Check coverage | Count |
|---|---:|
| Parent positions |654|
| Independent legal-child/view/capture/mask comparisons |22,569|
| Ambiguous quiet classes |355|
| Classes altered by synthetic reversed rankings |355|
| Capture-observation cases with identity output |167|
| EP alternatives |2|
| Promotion alternatives |32|
| Castling alternatives |110|
| King-capture alternatives |2|
| Mover-king-pruned alternatives |793|
| Empty classes |2|

Counts describe repeated correctness fixtures, not independent game outcomes
or predicted hazards. Synthetic likelihoods/ranks are deliberately artificial;
no fitted model, history table, model prediction or NLL was used. All legal
children match the separate Python course referee. Full-view and optional-view
fast paths agree, parent board/observations/rule metadata remain unchanged,
and invalid inputs leave output buffers unchanged. Generic reassignments retain
per-class powered mass and all ineligible bits. The full capture-class identity
is conditional on common parent/input weights; no whole-sequence claim follows.

The standalone native unit also passes address/undefined/leak sanitizers on20
starting-position targets. The first metadata-preparation command used system
Python, lacked chess, and failed before writes; its dependent publisher failed
before committing. Both are recorded in prepublication-error.json. The corrected
repository interpreter prepared the published plan; no trace check was retried.
Cores0–1 are released. No GPU or arena work occurred.

## Integration boundaries

The test library includes belief.c to access private native helpers. It is not
a drop-in file to link alongside another compiled belief.c. Integration needs
a deliberate interface and removal of test glue. The native filter, merges,
representative histories, caps, clock and full/cheap routing are unchanged.

`consistent` controls child admission. `eligible` only identifies consistent
noncapturing transitions whose likelihood may be reassigned. Unchanged values
outside that mask do not make their children admissible. Input likelihoods for
the rank primitive must be per-move log likelihoods after the existing legal
normalization/history blend, before parent log weight or temperature. Reorder
likelihood values alone; leave moves, boards and history metadata attached to
their original transitions.

This qualifies the default native king filter, not hidden repetition/50-move/
max-ply conditions. It has no learned score adapter, actual capped-posterior
validation or clock-cost evidence. Those remain separate work. The frozen295
future-model test remains independent and unscored.

[Plan](plan.json), [preflight](preflight.json), [result](result.json),
[original receipt](receipt.json), [cases](cases.json),
[core](../../experiments/observed-class-20261110/producer.c),
[independent checker](../../experiments/observed-class-20261110/check.py).
