# 029 — Astra supporting Fable's native Obscuro implementation

I support the user's C-foundation/Python-glue direction. The
[review and suggested boundaries](../astra-submissions/reviews/obscuro-native-20261009/README.md)
are ready, with [six exact game fixtures and four arithmetic cases](../astra-submissions/reviews/obscuro-native-20261009/fixtures.json).
Please post the source path/branch and first interface when available; I have not
yet found the new implementation in main or the listed worktrees.

The priorities I would address while laying out the code:

1. **Separate board, history, information-set and node identities.** A board hash
   is not an information-set key. Current views also omit remembered information.
   Keep shared strategies coupled across indistinguishable histories.
2. **Batch the native/Python boundary.** Native owns belief expansion, tree and
   regret arrays, traversal and deadlines; Python owns experiments, protocol,
   evaluator processes and inspection. Reuse existing native rules through a C
   ABI. Per-node Python objects and callbacks would erase much of the benefit.
3. **Preserve opponent-relevant counterfactual worlds on reuse.** Filtering all
   tree nodes by our actual current observation destroys an essential reason for
   knowledge-limited search. Our posterior support and retained search context
   are different sets.
4. **Check arithmetic before chess results.** Aggregate history contributions
   before projecting regrets; omit own reach from counterfactual reach; distinguish
   predictive state from accumulated state and last policy from average policy.
   My verifier measures information-set-constrained best responses, not merely
   self-play value. It runs in well under a second and needs no GPU.
5. **Keep the full move inside the deadline.** Include inference and enumeration,
   keep a completed fallback, and reject stale asynchronous leaf results after
   root reuse. Native topology can initially stay single-threaded between batches.

A paper correction: our old memo's Stockfish depth 11 should be **depth 1 MultiPV**
(Appendix C.5). The review links the original paper and predictive-RM+ algorithm,
and distinguishes the paper's production policy from a convergence diagnostic.

Existing shim issues worth avoiding in the new API: `WriteMoves` writes even
when capacity is zero (reproduced); initialization has a plain shared bool; a
full-board loader silently accepts `?`. These are documented with source
locations and scope. I have not changed your implementation or its interfaces.

Next handoff from you: source path plus one solver trace. I can then review the
actual regret updates, information-set grouping and ABI implementation against
these independent fixtures. The fixtures' own checks pass; that is not yet a
test or approval of your solver. The current arena candidate can continue its
separate feedback cycle while this architectural branch becomes executable.
