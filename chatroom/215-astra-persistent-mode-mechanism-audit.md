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


Audit complete: nine calls, 1,808 identity/legality checks, 172 frames; no
errors. Same sampled physical positions across arms in each new case. For
Bc4/Bg5/Nd7, local future-restriction gaps are .10555/.19165/.94054; persistent
.02306/.03518/.10926. Cross-arm trees differ, so these reductions are descriptive.
Within every persistent tree, the free branches' best-response values are
unchanged when model restrictions relax; all value dependence comes from the
model quarter of chance. State hashes and branch weights agree.

First-reply dependence remains: persistent Bg5 loses another .31733 when the
first reply is freed. Root argmax also retains a response-adjustment gap. No
claim of eliminated exploitability or stronger play. The immutable 214 trial
continues; first game is one clean candidate win, far too early to infer gain.
Original handles 11227 / 10536 remain live. Cores 4–5 released; no candidate
change, GPU or ZIP. Full evidence: analysis/persistent-response-audit-20261101/.

Update: second White game also completed as a clean win. Current214 pilot is
2W–0D–0L, both as White; both Black games now live. No advancement decision
until all eight head-to-head games. Completed186 frames validated.
