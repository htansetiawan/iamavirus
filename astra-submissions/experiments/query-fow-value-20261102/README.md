# Query attention for compact Fog of War value prediction

Experiment 238, Astra. Work in progress; no trained model or release yet.

Experiment 237's attention teacher improved held-out outcome prediction, but
its summed-embedding student did not pass. This model keeps relationships
between squares with four query slots, two tied-key/value cross-attention
rounds, width 32, two heads, and 64-unit feed-forward layers. The first two
queries include the own/enemy king token. A pooled board vector accompanies
the final four query vectors into a 64-unit value head. The inputs are the
same canonical hypothetical-world features as 237; no player identity.

Token key/value projections are linear and shared across rounds. They are
folded into piece-square, visibility-square, castling and en-passant tables
at export. Native inference sums these tables, avoiding 64 dense projections
per call. Attention interactions cost O(64*4*32) per round instead of the
teacher's O(64*64*128); this is a computational comparison, not a strength
claim. C11 inference needs libm, no allocation or neural runtime.

Preflight gate, declared before timing: payload <=1 MiB, CPU/PyTorch logit
error <=2e-5, median <=50 microseconds per world on one reserved core. 25 us
is the target. The separate 237 student gate was 25 us and remains failed.
This experiment allows at most 1.6 ms per 32-child batch before encoding;
actual search throughput and full-clock strength still require testing.

Only if native preflight passes: freeze a new holdout disjoint from all 237
games, trajectories, and canonical input states. Its old test is quarantined.
Use the existing training/validation split and frozen teacher; compare a
32-epoch flat distilled control, a direct query student, and a distilled
query student under the same budget. Select by validation, then open the new
holdout once. Detailed data, optimization and acceptance contract will be
frozen before training; no model selection may use the new holdout.
