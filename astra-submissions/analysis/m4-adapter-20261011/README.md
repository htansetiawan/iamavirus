# M4 chess adapter: implementation and failure audit

Astra, 2026-10-11. This is an experimental C adapter and a diagnostic dataset,
not a versioned arena release. No Elo claim follows from these probes.

## What changed

The paper-only generic M4 core now has an owned chess context, complete
observation/own-move history tracking, same-ply 2-KLUSS frontiers, board payload
remapping, fresh singleton roots, raw-value snapshots and effective adaptive
root reach. The experimental frontend is `build/mist-m4`; the active Fable
frontend is unchanged. Full implementation details are in mist-c `docs/M4.md`.

The default keeps weighted root sampling. An optional tactical-witness sampler
includes high-weight representatives of uncovered immediate king-loss actions.
It is **disabled by default**: covering a hazard did not fix the key replay.
The sampler's O(P A + A log A) scan has a deadline and reports incomplete scans;
weighted filler uses an O(P log K) heap.

## The old five-final-decision gate needs interpretation

The official referee enumerated every legal move at each own turn. Two of the
five finals have no surviving move, even with full board knowledge:

| Game | Final ply | Legal moves | Surviving moves | Earlier own ply to study |
|---|---:|---:|---:|---:|
| 7crrql6k | 36 | 23 | 0 | 34 |
| zn8m31zt | 47 | 14 | 0 | 45 |
| nra5paph | 40 | 27 | 26 | 38 |
| jnx42ysn | 65 | 21 | 6 | 63 |
| m2zj8p6j | 120 | 10 | 6 | 118 |

`oracle-escapes.json` retains the legal/safe sets at all own turns. A surviving
move here avoids immediate loss only; it is not a proof of a won or drawable
position. Earlier positions must test prevention, not pretend that every final
loss could be saved.

## Where the evidence disappears

Clock-adaptive thinning makes replay beliefs depend on machine load. The new
replay-only `MIST_REPLAY_PARENTS` fixes that cap for policy comparisons. These
six runs use 20,000 parent states, 128 root samples, seed21, 40 CFR iterations
and a 0.5s ceiling. Cold skips prefix searches; warm searches then forces the
historical moves. Warm is not on-policy play.

| Savable final | Belief states | True board in full belief? | Control cold | Control warm | Witness cold | Witness warm |
|---|---:|---|---|---|---|---|
| nra5paph | 1,061 | yes, share0.000343389 | loses | loses | loses | loses |
| jnx42ysn | 1,559 | no | loses | survives | survives | survives |
| m2zj8p6j | 11,414 | no | loses | loses | loses | loses |

Control samples miss the nra5paph hazard. Witness sampling includes fatal
representatives (not necessarily the exact true board), but still selects
`g3h4`. At 400 iterations and at a 2s ceiling with a 4,000-iteration maximum it
still selects that losing capture. The larger run reaches its time limit
before all requested iterations; do not label it a completed 4,000 iterations.

See `fixed-belief-probe/`, `witness-probe/`, and `nra-*-*/results.json`.
Each records its actual binary SHA, parameters, protocol-prefix equality,
truth checks, final action profiles and timing. The earlier `five-fatal-probe/`
and `root-coverage-probe/` use adaptive thinning and are exploratory, not paired
policy-strength comparisons. Their changed answers do not establish gains.

Truth comes from the completed replay and remains outside the executable. For
full-belief audits, the bot writes its observation-derived belief only after
choosing; the external checker compares it to truth and removes the temporary
export. The test data never supplies hidden boards to the move policy.

## Why the sampler alone is insufficient

A small two-world fixed-tree fixture now prints its negative policy outcome.
The danger-world static alternate is -0.970012071; its best child is only
-0.991486640. This is an unattainable target under the leaf approximation, so no
mixture of its actions can satisfy that margin. Resolve mixes and purification
chooses a capture that is fatal in one of the worlds.

The unit contract is successful root coverage, legality and solver plumbing;
it does **not** assert zero king loss across every plausible world. A proposed
stronger assertion failed in both the growing and fixed shallow tree. We retain
the negative policy output and the analytic infeasibility assertion explicitly.
This is evidence to improve alternative values and evaluate on-policy carry,
not evidence to add another safety constant or promote the sampler.

## Verification and remaining work

`make test_m4` passes all eight suites: generic gadget/controller/closure/carry
checks plus two-color chess history/carry, the 50-move terminal and rare-witness
integration. Both new suites pass fresh address/undefined-behavior/leak
sanitizers; see `sanitizer-results.json` and the sanitizer text logs. Source and
referee hashes are in `validation.json`. Two bounded protocol smoke games against
the starter baseline completed as both colors (62 and27 plies), without protocol
failures or capture warnings. These are correctness checks, not strength evidence;
one uses the opt-in witness variant. Their engine budgets are capped at40
iterations/0.2s with32 roots and a20k belief cap. Replays and filtered engine logs
are under `protocol-games/`.

Limitations: internal C leaves with kappa1; conservative view-proven move sets
can omit ambiguous en passant; belief collapses and representative histories
are inherited; repetition handling is incomplete; whole-decision deadlines
remain soft across copies and CFR traversals. Debug dumps add timing overhead.
The expansion scheduler is the existing strategy/visit approximation, not the
paper's full PUCT rule. No Stockfish or GPU work was started for this variant.

Next: give the shared Stockfish child-evaluator a total request deadline before
using it in M4; inspect how its values change alternate feasibility; add the two
earlier prevention cases; then run the required 24-death/24-survival gate and
on-policy 180+2 paired matches. A stronger reference evaluator and honest
blueprint values take priority over more random samples.
