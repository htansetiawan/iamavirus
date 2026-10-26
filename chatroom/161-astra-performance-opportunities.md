# 161 — Astra: concrete algorithmic speed opportunities

Henry asks whether 2x–10x faster computation can improve strength, and where
the complexity reductions are. Yes: saved turn time can fund more consistent
worlds, stronger leaf evaluation or more search. It must be measured on the
whole move and then spent on a decision bottleneck. A faster kernel is not an
Elo result. This is a source audit of mist-c 539d4e3, with hashes in
`astra-submissions/analysis/performance-opportunities-20261026/audit.json`;
no new performance run or candidate change was made.

## First implementation opportunities

| Priority | Source finding | Proposed change | Preservation requirement |
|---|---|---|---|
| 1 | `main.c`: king, queen and new piece guards walk the belief separately for each move; each repeats weights, board copies, make-move and king tests | Fuse classifications per world/move; precompute the two weights and denominators once per sampled world; reuse captures and attack information | Same strided world sets even when caps differ; same disjoint event definitions, thresholds and numerical tolerances |
| 2 | `board.c:107`: `is_attacked` scans every enemy piece, generating each piece's attacks; sliders walk rays | Target-centric attack detection: reverse pawn masks, knight/king tables, bishop/rook rays from the target intersected with enemy slider bitboards; then benchmark table-based slider lookup | Exhaustive square/colour differential checks on referee traces, promotions, missing kings and en passant; no orthodox-check restrictions |
| 3 | `cfr.c:82`: four arrays resize to exact size on growth; `pcfr_iteration` allocates two full scratch arrays each iteration | Geometric capacity, persistent scratch buffers and fewer redundant strategy copies | Identical regret/strategy updates under a fixed expansion/iteration trace; allocator copying is a worst-case opportunity, not a measured bottleneck yet |
| 4 | `belief.c:573`: pre-update shrinking fully sorts N exponential sampling keys to keep K | Selection plus sorting only retained indices: expected O(N + K log K), instead of O(N log N); use a bounded fallback for pathological partitions | Same exponential keys, selected worlds and retained order; current quickselect has expected-linear rather than worst-case-linear cost |
| 5 | `belief.c:327`: model logits are calculated before discovering that a parent has no observation-consistent successor; survivor keys recompute all pieces | Filter first, skip model evaluation for zero-survivor parents; incremental position keys; evaluate radix/hash dedup only if sorting is material in a profile | For every surviving parent, normalise likelihood over ALL original legal moves, not only observation-consistent moves; preserve parent evidence and weight merging |
| 6 | `board.c:212`: visibility builds a full move list just to OR destinations, repeatedly in the belief and tree | Direct visibility bitboards, reuse generated move destinations where already available | Pawn pushes versus attacks, blocked double pushes, castling and EP reveal rules must match exactly |

For a fixed 64-square board, the attack/visibility changes mostly improve
constants, not asymptotic complexity in belief population size. That does not
make them minor: those constants repeat across worlds, candidate moves and
tree expansions. At 30 root moves and a 20,000-world guard cap, there are up to
600,000 world/move classifications before considering repeated guard passes.

## Larger algorithmic opportunity: repeated full CFR passes

`pcfr_iteration` rebuilds strategies for all slots and traverses reachable tree
branches for each player. Each iteration is O(S + visited nodes), with S the
number of action slots. Growing-tree search performs iterations repeatedly
while growing the tree. If tree size and iteration count grow roughly with E
expansions, cumulative work can scale as O(E²) in the worst case. This is a
source-level bound, not a measurement of the current wall-time exponent.

Lazy-CFR avoids updating the whole information-set collection each round;
MCCFR samples traversals with correctly weighted updates. They are credible
larger changes, but neither is a drop-in heap replacement or automatically
valid for our growing-tree predictive-CFR+ implementation. Test convergence on
small games, information-set correctness, rare-event variance and equal-clock
decision quality before a playing candidate.

Primary sources: [Lazy-CFR](https://arxiv.org/abs/1810.04433),
[MCCFR, NeurIPS 2009](https://papers.nips.cc/paper_files/paper/2009/hash/00411460f7c92d2124a67ea0f4cb5f85-Abstract.html).

## Existing work and evidence that prevent wasted effort

- Note 051 already measured two-thread belief expansion: 2.29 s to 1.24 s at the
  cap, reducing the need to thin worlds. Its profile was v9-era, not current v20.
- Its compiler-flag trials were within noise; pipelining already exists.
- `belief_sample` already builds a cumulative distribution in O(N), then
  draws by binary search in O(log N) each. A heap/Fenwick tree is not an
  automatic improvement when most weights change at every update.
- The opponent-update cap already uses expected-linear selection; only the
  separate pre-update `belief_shrink` still fully sorts the rank array.
- Infoset lookup already uses an open-addressed hash map.
- Note 055 measured only 5.78% repeated evaluator FENs, with context-dependent
  Stockfish scores. A simple evaluator cache is not a plausible 10x win on that
  stream. Do not merge information sets merely because the boards match.
- Reducing MultiPV increased calls per second historically but changed leaf
  quality and worsened some tactical measures. Preserve calculations first.

## How to turn this into strength this week

Profile a fixed small set after a reserved lane is free. Split actual turn
wall time into belief, guards, CFR and evaluator/waiting, count calls and memory
traffic, and sample opening/midgame/endgame with small and capped beliefs.
Use `MIST_TIMING`, not `MIST_RISK`: the latter enables an otherwise inactive
material scan and would distort arena timing. Worker elapsed times overlap;
their sum is not the turn's Stockfish wall-time fraction.

First try fused guard work and target-centric attacks, one reversible branch,
with identical fixed-work outputs. Then measure whole-turn speed and keep the
arena clock unchanged to test how the extra budget affects decisions. Do not
change the binaries underneath the running depth or material gates.

For illustration, speeding 80% of a turn by 10x gives only
1/(0.2+0.8/10)=3.57x overall. At a true dangerous-world mass of 1%, increasing
iid samples from 32 to 64 raises the chance of seeing it from 27.5% to 47.4%; at 256
it is 92.4%. More computation can help, but wrong posterior mass remains a
separate limitation. These are mathematical examples, not measured Elo gains.
