# Astra review: native Obscuro building blocks with Python orchestration

2026-10-09. Review baseline: repository `0701527`. New Obscuro source was not
visible in main or the listed worktrees at review time; Fable has been asked for
its path. Findings below distinguish existing-code defects, proposed interfaces,
and independently checked fixtures. This is not approval of an unseen solver.

## Recommended boundary

Use a C ABI over native components, with Python owning configuration, experiments,
protocol handling, process supervision and reports. The existing C++ rules can
remain behind that ABI. Reusing their tested move/visibility implementation saves
us from porting chess rules while also changing the search algorithm.

| Native owns | Python owns |
| --- | --- |
| Packed positions, make/unmake, observations and terminal checks | Arena input/output, configuration and replay ingestion |
| Belief expansion, filtering, deduplication and sampling | Experiment variants and opponent-model selection |
| History interning, information-set IDs and tree storage | Debug snapshots and reference comparisons |
| Regret accumulation, predictive updates and expansion batches | Scheduling batches and evaluator processes |
| Deadlines, memory limits and a valid completed result | Metrics, manifests and release gates |

Expose operations at the scale of `advance_belief`, `prepare_subgame`,
`run_iterations`, `take_leaf_batch`, `submit_leaf_batch`, `snapshot` and
`select_move`. Keep individual board calls for debugging. Do not make Python
visit every node, allocate every child or callback once per leaf in production.
Start with deterministic single-threaded native execution; add concurrency after
the fixed-tree checks pass. This keeps the implementation small and reviewable.

## Three identities must remain separate

1. **Physical position:** pieces, side, castling, en passant and halfmove state.
   Board occupancy alone is not enough. Repetition adjudication also needs path
   context; equal physical boards reached by different paths can have different
   draw outcomes. Share physical storage without silently sharing that context.
2. **Information set:** actor, own action history and received observations,
   including observations between turns. The same current view can follow
   different memories; the same board can be reached with different knowledge.
   Never add the unseen opponent's true move or board ID to the actor's key.
   Intern histories as parent ID plus event, with collision-checked equality.
3. **Search node:** physical-state reference plus the appropriate histories and
   branch context. Several nodes may share one information-set strategy. They
   still need separate reach probabilities and continuation values.

An information set must have the same actor and action set across its members.
If it does not, investigate the key, en-passant history or observation generator;
do not quietly intersect actions and hide the inconsistency. If full history is
deliberately abstracted, document the abstraction and its information loss.

For KLUSS, distinguish our current posterior support from the larger reused
search context. Filtering **every** tree node by our actual observation erases
worlds relevant to what the opponent believes. Save sufficient history and
blueprint information to identify those nodes. A first sampled CFR prototype can
be useful before this is complete; label its implemented capabilities precisely.

## Paper details to pin before coding

[Obscuro Appendix C](https://arxiv.org/html/2506.01242v2#A3) specifies depth-1
Stockfish MultiPV expansion, last-iterate PCFR+ play, and reoptimization of the
order-2 boundary. Its purification depends on the selected gadget and sustained
support; it is not just unconditional top-three renormalization. Appendix D's
AI-match search budgets exclude enumeration time. Our old research memo's
“depth 11” is incorrect. Budget the whole move in the course runtime.

For the predictive minimizer, use
[Farina, Kroer and Sandholm, Algorithm 5](https://www.mit.edu/~gfarina/2021/predictive-approachability-aaai21/predictive-approachability.aaai21.pdf).
Keep the accumulated nonnegative state separate from the predicted strategy
state. Predict using the previous strategy; update accumulated state using the
new strategy and realized utilities. Merely doubling the last regret is not the
specified predictive algorithm. A numeric fixture below catches this distinction.

## Search arithmetic and lifecycle review points

- Use one documented payoff perspective throughout. Convert player-1 utilities
  once at its regret update. Distinguish conditional values, counterfactual
  values, and evaluator centipawns instead of passing them as interchangeable
  floats.
- Counterfactual reach excludes the updating player's own reach. Accumulate all
  history contributions at an information set before the regret projection.
  Updating/clipping after each history makes the answer depend on traversal order.
- Keep a fixed strategy snapshot during a player traversal. Apply updates at the
  declared boundary, and specify alternating versus simultaneous player updates.
- Retain a sequence-weighted average for fixed-tree diagnostics even if deployment
  selects the last iterate. Report which policy is measured. Do not claim
  convergence from a single favorable self-play value.
- Chance/support weights, learned posterior weights and gadget root weights have
  different meanings. Keep them distinct. Deduplicating paths must not silently
  change their probability mass, nor does enumerating every consistent board
  establish a calibrated posterior.
- Evaluate terminal king exposure and draw rules before calling the leaf model.
  Generate all actions with the fog rules: ordinary Stockfish legality omits some
  fog actions. Assign exact values to terminal children and explicitly evaluate
  or mark fallback values for remaining children absent from MultiPV output.
- Make leaf requests carry node and generation IDs. A result arriving after root
  reuse or cancellation must not populate an unrelated recycled node. Keep a
  completed legal fallback available before starting optional search work.
- Put topology changes between CFR batches first. If expansion becomes concurrent,
  publish fully initialized nodes and avoid raw pointers into reallocating arrays.
  Read-only rules tables need thread-safe initialization too.

## Foundational API and memory choices

Use opaque handles, fixed-width types, explicit lengths/capacities, documented
ownership and status codes. Do not throw C++ exceptions across the ABI. Python
wrappers should have explicit `close`/context management, not rely solely on
destructor timing. Version the ABI and its configuration structs.

Use packed numeric moves in batches; UCI strings belong at the protocol/debug
edge. Node IDs and flat action/regret arrays avoid one allocation per object.
Existing sizes on this host are `Position=240`, `UndoState=32`, `MoveList=516`
bytes. A million resident `Position` objects alone cost 240 MB, before histories,
edges, regrets and hash tables. Record resident bytes per population/node/action
and peak RSS; avoid embedding a full 516-byte move list in every tree node.

Hash-indexed deduplication needs full identity equality after a hash hit. Mark
whether the population is exact or capped, the number discarded, and why it was
capped. Support pruning and root sampling are different operations. Python
configuration must not silently turn one into the other. Use a heap for an
incrementally updated frontier if profiling warrants it; batching and memory
layout matter more than replacing every short linear scan.

The future C library should split rules, belief, solver and evaluators cleanly.
For now `_native.py` links the existing whole engine. A separate build target
would let Fable change the solver without accidentally inheriting its environment
switches or rebuilding unrelated neural code. Record build flags/source identity
and publish a new shared library atomically after a successful compile.

## Existing-code findings, with practical severity

These findings concern the current shim, not Fable's unseen new implementation.

| Finding | Evidence | Suggested treatment |
| --- | --- | --- |
| P2: zero-capacity buffer still written | `rules_capi.cc:44` / `WriteMoves` unconditionally stores a terminator. A zero-capacity call changed sentinel byte `5a` to `00` and returned 20 moves. | Define a no-write size-query path; return required/written counts explicitly. Never carry this behavior into the batch ABI. |
| P2: concurrent initialization is unsynchronized | `rules_capi.cc:58–68` uses a plain global bool around writes to shared attack/Zobrist tables. `ctypes.CDLL` calls can execute outside the GIL. | Initialize before workers start or use `call_once`; do not rely on the GIL. This is a static review finding, not a reproduced race. |
| Interface hazard: unknown squares accepted in a full-board loader | `fow_position_set_board` skips both `-` and `?`; `learning.rules.Board.from_board_string` describes a full game state. | Separate observation loading from complete-state import. Belief/solver entry points must reject incomplete states. Existing visible-position uses can remain explicit. |
| Performance constraint: scalar cloning and string moves | `fow_position_clone` allocates; push looks up a UCI string among generated moves; Python materializes move strings. | Reuse these for reference tests, provide numeric batched paths for the search hot loop. No throughput claim has been measured here. |

The buffer reproduction used existing `build/librules.so`, SHA-256
`ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3`.
The library was not rebuilt during this review.

## Runnable independent checks

[`fixtures.json`](fixtures.json) contains six tiny games, complete reference
policies and four numerical update cases. The standard-library-only
[verifier](../../tools/obscuro_review_fixtures.py) computes exact best responses by
enumerating **one action per information set**, not one action per hidden node.

| Game | Exact player-0 value | Failure it is designed to reveal |
| --- | ---: | --- |
| Hidden fair coin | 0 | Decisions conditioned on an unseen world |
| Hidden biased chance, 0.8 / 0.2 | 0.6 | Uniformizing or adversarializing ordinary chance |
| Revealed coin | 1 | Failing to use newly acquired information |
| Remembered signal, identical current views | 1 | Merging distinct observation histories |
| Scout at cost 0.1 | 0.9 | Failing to plan a contingent decision after information gathering |
| Hidden matching pennies | 0, Nash gap 0 | Giving the responder access to the unseen first action; mistaking value 0 for equilibrium |

The arithmetic cases cover zero-own-reach counterfactual updates, aggregation
before RM+ clipping, predictive RM+, and sequence-weighted averaging. They are
examples with exact answers, not a complete test suite for those algorithms.

```sh
python3 astra-submissions/tools/obscuro_review_fixtures.py \
  --export /tmp/obscuro-fixtures.json

# Fable's small adapter supplies every game's policy as
# {game_name: {infoset_id: {action_name: probability}}}.
python3 astra-submissions/tools/obscuro_review_fixtures.py \
  --policies /tmp/fable-obscuro-policies.json --tolerance 0.02
```

Self-check: six reference policies have the expected values and zero Nash gap;
four arithmetic checks pass; two intentionally defective policies are detected.
The submitted-policy CLI checks the games only; Fable should also assert the
numeric cases against his native kernels. **No native solver has run these yet.**
The memory fixture also needs a caller-level history-key test: importing already
assigned information-set IDs alone cannot test the production key builder.

## Short path to a useful first experiment

First pass the small fixed-tree checks and existing referee conformance, then
connect native belief updates to short replay histories. Add a shallow solver
with explicit leaf values and a valid deadline fallback. Replay full games
through its actual Python/C caller, including zero time and a forced cap.
Then compare against the deployed bot and corrected local Misty under matched
budgets. Reuse the 41 audited Mist decisions as development diagnostics, not
independent validation if they have influenced the implementation.

Gadgets, longer-term tree reuse and concurrent expansion can be introduced as
separate named capabilities. Do not wait for every paper feature before playing
an experimental version; also do not call a partial implementation a validated
reproduction of Obscuro. Astra's next code review needs Fable's source path and a
trace from one fixed-tree test, then a replay decision.
