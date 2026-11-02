# Whole-search cost profile: evaluation dominates

**Stockfish calls account for 82.2% of original v37 search wall time across these eight cost-selected decisions.** Solver plus strategy computation account for 12.4%; tree-array growth is 0.03%. This explains why the exact kernel optimization has limited scope for a large whole-search gain.

| Exclusive category | Original wall share | Optimized wall share | Original main-thread CPU seconds |
|---|---:|---:|---:|
| Stockfish calls | 82.194% | 83.692% | 0.9733 |
| Solver traversal/update | 8.962% | 10.428% | 1.5415 |
| Strategy computation/copy | 3.397% | 0.233% | 0.5845 |
| Child construction | 4.943% | 5.144% | 0.8490 |
| Solver-array growth | 0.032% | 0.020% | 0.0055 |
| Tree selection | 0.070% | 0.074% | 0.0121 |
| Other search work | 0.402% | 0.409% | 0.0569 |

Profile totals: original 17.1979 wall seconds / 4.0226 main-thread CPU seconds; optimized 17.1860 / 3.7854. Stockfish workers' CPU is excluded. Stockfish-call wall time includes worker computation, waiting, transport and parsing. The difference from parent CPU is **not pipe overhead**.

Original Stockfish-call fractions span 64.9–88.8% across cases. The engine reports synchronous rounds in every profile; asynchronous search is not the deployed default.

For unchanged work, even eliminating all solver and strategy cost gives an idealized ceiling of 1.141x. Halving the measured Stockfish-call wall cost would give 1.698x under a serial Amdahl model. These are resource-allocation bounds, not predicted node gains or Elo; changed work, worker overlap and policy effects invalidate a literal prediction.

## Verification and scope

32 first-attempt processes completed, original collector handle 48593 exit 0. No retry or dropped case. Nested deterministic timer accounting passes; eight whole-engine fixed-work checks preserve move/result for both colors. Independent source inspection verifies all 20 wrapped original function bodies are unchanged. Referee audit validates 273 replay frames, all 32 choices and eight own-observation/clock/own-move inputs. Bucket sums reconcile with total wall/CPU time.

Profiled/unprofiled median node ratios are 0.9832 for original and 1.0079 for optimized. Individual ratios span approximately 0.938–1.070; two belief counts differ in each arm. Thus these controls show sensitivity to instrumentation, scheduling and adaptive thinning, not a precise timer-overhead estimate. This is a cost study on reused selected decisions, not strength or a promotion gate.

## What follows

Fable note 051 already found expensive Stockfish scoring and inexpensive transport. This current-engine profile adds the solver/strategy/growth breakdown and supports stopping further allocator or selection tuning as the main improvement track. Lower MultiPV and pipelining have already been tested; this result does not reopen those settings.

The next mechanism to assess is scoring all children more directly while retaining tactical search. The [official Stockfish search source](https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp) runs a root search for each MultiPV line. That suggests investigating repeated root work inside evaluation. It does not prove a quadratic runtime bottleneck or that a single-pass replacement preserves scores. The inspected master source is not yet tied to our packaged binary; provenance must be resolved before implementation.

A bounded next feasibility test should compare the existing all-MultiPV scorer with direct per-move depth-1/quiescence scoring on identical complete candidate move sets. First measure native cost and action-value/ranking agreement, including mate/terminal and unsupported-FoW handling. Only an accurate, faster scorer should enter the search. No score-floor shortcut, lower-MultiPV retry, neural training sweep or release follows from this profile.

No new ZIP, reserved arena version, GPU use or arena action. Source and first-attempt evidence remain in this experiment.
