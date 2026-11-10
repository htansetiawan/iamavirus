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

## Result

Original session `7007` exited successfully in 9.7 seconds. All 28 feature
values, base scores, zero-residual scores and 9,746 capture entries matched
bit for bit on 5,417 replay parents and 169,641 legal actions. The suite
also covered 13 targeted fixtures and 110 fixture actions. Across the
replays and fixtures it exercised 332 promotions, 367 castles and 14
en-passant actions. The learned quiet scores matched PyTorch within 2.87e-6.

On the frozen full-scoring workload, median paired CPU time was 0.662×
v38 for the exact feature optimization and 0.741× for the compact scorer.
The head added 11.9% over the faster exact control. All four gates passed.
The next sequential comparison should include the exact control so the
effect of changed weights can be attributed separately from speed and
resulting clock-based thinning.

[Result](../astra-submissions/analysis/compact-prior-native-20261110/result.json)
· [Terminal verification](../astra-submissions/analysis/compact-prior-native-20261110/terminal-verification.json).
