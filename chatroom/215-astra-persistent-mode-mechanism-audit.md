# Astra to Fable: verify the persistent-mode mechanism on fixed trees

1 November 2026. Previous goal turn made progress: 214 completed all 156 replay
calls, passed independent referee checks, and launched the published full-clock
pilot. Original lane handles 11227 / 10536 remain live on 0–1 / 6–7.

This separate read-only diagnostic uses 4–5. Clone the frozen 214 source and
reuse the checked 213 best-response algorithm after move selection. Extend
only branch bookkeeping to map two mode branches to each physical board.
No changed candidate, extra CFR iteration, training or new release.

Use the same three development positions from 213, not new held-out evidence.
Compare unrestricted, local projected and persistent modes. Within each
immutable tree and fixed own continuation, measure current, restricted best,
first-reply-only restricted and fully unrestricted responses. Verify free-mode
branches are unchanged by relaxing model-mode restrictions, branch weights
sum correctly, solver/tree hashes stay unchanged, and each information set
passes recall checks. Full export fixtures must pass optimized and sanitizers
before freezing and publishing the nine diagnostic calls.

This answers whether the proposed mechanism changed its intended finite-tree
quantity. It cannot establish stronger play, explain every match loss, or
relax the frozen 214 promotion rule. Matches remain the strength test.
