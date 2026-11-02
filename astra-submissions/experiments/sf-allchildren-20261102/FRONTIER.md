# Search-frontier follow-up, frozen after the played-parent gate

Keep exactly the candidate source, build, flags and fidelity/cost gates of
experiment 256. Capture Stockfish input FENs from v37's actual search in the
eight prior 227/253/255 cost cases, 2.5 search seconds each. A copied native
engine adds only a stderr FEN trace at successful supported submissions.
Trace overhead changes which nodes the search reaches: this is a workload
sample, not an identical-work performance comparison or strength test.

Validate replay input hashes and earlier forced moves. Keep all first-attempt
captures. Select 32 unique supported parents per decision by salted FEN hash,
with no scoring/outcome selection; report exact exclusions. Each case has equal
weight. Captured FENs are hypothesized complete worlds constructed inside search,
not the referee's true board. No true-board input is given to the playing engine.

Use the same 4-arm, 3-pass cold/warm comparison, for 256 parents total. All root
moves must be scored. Both regimes need MAE <=0.08, reference regret <=0.05,
large-regret rate <=1%, speedup >=1.5 versus rebuilt and >=1.2 versus shipped.
No changes to scoring based on the played-parent results. Each capture has a
120-second timeout and the full capture stage 15 minutes. CPU cores 0–1 only.

Only a pass earns a separate equal-clock full-engine decision screen. No match
or ZIP is authorized by this evaluator-fidelity result alone.
