# Obscuro, Misty, and deployed mist-c: understanding check

Author: Astra. Date: 2026-10-26. Requested by Henry; sent directly to Fable for independent verification.

## Attribution and source boundary

Brian Hu Zhang and Tuomas Sandholm wrote the [Obscuro paper](https://arxiv.org/html/2506.01242v2). Brian H. Liou made [Misty](https://github.com/brianhliou/misty), a separate implementation. Our mist-c is another implementation. Neither the common architecture nor the Misty name establishes the identity of an arena competitor.

The paper's contribution includes knowledge-limited unfrozen subgame solving, improved resolving, and one-sided growing-tree CFR. The abstract structures are a consistent-position set, history tree, information sets with shared action/regret vectors, and a previous-search blueprint. Concrete containers in the original unpublished implementation are unverified.

Misty's [author report](https://brianhliou.com/posts/misty-fog-of-war-engine/) describes its September 1.6 profile, updated October 15. Its settings are not necessarily those of our frozen local Misty ZIP or an arena entrant. Review used public documentation, not Misty implementation source, preserving the agreed clean-room workflow.

## What our deployed engine actually contains

Reference: immutable arena v35 archive, `fable-submissions/iamavirus-v35-mist-c-v14.zip`; its source is the authority, not a specification or an unmerged branch. Current main's relevant structures were inspected; implementation claims below must also match that archive.

| Layer | Concrete representation and behavior in our C engine |
| --- | --- |
| Board | `Position`: 64-bit color/type bitboards plus piece/color arrays, castling rights, en-passant square, side and halfmove count. Moves are 16-bit values. |
| Belief | Position array, log-weights and representative opponent-history hashes; candidate sorting/merging and capped weighted sampling. It is not a guaranteed exact posterior after thinning or history merging. |
| Information sets | Open-addressed table maps player/history hashes to information-set indices. Histories that the player cannot distinguish share action probabilities. Concrete history nodes remain separate. |
| Game tree | Contiguous node/edge arrays with integer indices; nodes refer to shared information-set indices. This is not a binary search tree. |
| Solver | Per-information-set/action arrays for cumulative clipped regret, last regret increment and strategy; alternating predictive CFR+ updates. Opponent zero-probability branches are skipped during traversal; this is not an unconditional whole-tree walk. |
| Expansion | Alternating exploring player. The exploratory score uses current action probability plus a visit bonus; no explicit action-value/uncertainty term in `pick_once`. |
| Evaluation and output | Stockfish MultiPV depth 1; root king/queen guards; highest-probability permitted action. The search tree is freed after each move. |

Source pointers: `~/git/fowsearch-c/src/{fow.h,belief.h,belief.c,cfr.h,cfr.c,gtcfr.c,main.c}`. Archive comparison confirms identical `fow.h`, `belief.h`, `belief.c`, `cfr.h` and `cfr.c`. Current `gtcfr.c` adds later optional hazard terms; its tree structures, information-set lookup and expansion-selection rule described here also appear in the v35 ZIP unchanged.

## Important fidelity gaps

The deployed engine has no active 2-KLUSS construction, prior-tree blueprint, Resolve/Maxmargin gadgets, or their stable-mixing decision. Astra's `astra/m4` work is not merged and is not deployed. Learned move weights, the empirical history prior and root guards are our additions. Consequently, “we implemented Obscuro” means we implemented part of its architecture, not a reproduction of its complete evaluated system.

Our immediate review should separate three failures: truth absent from the belief; truth retained but missed/underweighted by search; or truth represented and the policy still wrong. More iterations cannot recover a world that the retained belief excludes. Faster evaluation and better exploration could help the third category, but that needs fixed-clock measurement.

## Confirmation

Fable independently read the paper, author report and C implementation and returned [its review](162-fable-obscuro-misty-v35-review.md), confirming the architectural comparison. Its first reply introduced two numerical errors; Astra checked and sent corrections with primary evidence:

- Paper Appendix C.5 specifies Stockfish **depth 1**, not depth 11. Search-tree depth and Stockfish leaf-evaluation depth are different quantities.
- Deployed v35 uses **32 draws when Stockfish is ready** (`src/main.c:330` inside the ZIP, before an optional `MIST_SAMPLES` override). The 128/256 fallback does not describe the active Stockfish configuration. Repeated weighted draws can produce fewer distinct worlds.

Fable verified both corrections and appended them to its own note and the ledger at **23:28:42 UTC**. This closes the requested independent confirmation. Read the correction at the bottom of its note; the original mistaken statements remain there for traceability. Also, Resolve/Maxmargin and CFR themselves predate Obscuro; the contribution is the specified modifications and integration, not their invention.
