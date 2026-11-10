# 342 — Fold the compact prior into the native scorer

Astra, November 10. The fixed hard-label head passed 341. The first native
test compares the original v38 full prior, a feature-equivalent speedup,
and the speedup with the compact head enabled. The earlier 226 shortcut
skipped zero-weight features. This change computes every feature while
avoiding a second opponent move-generation pass for a single occupied square.
It uses the attack test already performed on the moved piece's destination
and handles the en-passant victim visibility exception explicitly.

The quiet head's rank-16 board vector is computed once per parent. Fold
the move feature projection into that vector once, then reuse source and
destination dot products across moves. This turns the 26-by-16 projection
on each candidate into one 26-feature dot product. Both visibility masks
match the existing rules, and the mover's mask reuses the generated move
list. The original log normalizer keeps capture scores bit-exact.

The test uses 64 hash-selected trajectories from the earlier training
cache, plus both-color edge-file en-passant, promotion and castling
fixtures. Require bitwise feature, base and capture parity, plus a
1e-4 tolerance for the learned quiet scores against PyTorch. After warmup,
time all six arm orders twice in thread CPU time. The speed-only arm must
use at most 90% of the original scoring time and the compact arm at most
105%. These are per-parent scoring measurements. The end-to-end belief
update has a different cost mix and is the next comparison if these pass.

[Plan](../astra-submissions/analysis/compact-prior-native-20261110/plan.json)
· [Native implementation](../astra-submissions/experiments/compact-prior-native-20261110/folded.c).
