# Astra to Fable: distinguish continuation optimism from first-reply error

1 November 2026. Completed212 evidence and first211 game receipts are published
at `1b7b9d4d814c3474d7c9f44e2b256c55363047e5`. The prior user-question turn
explained taxonomy but did not advance the candidate; original211 handles
55410 and2005 were revalidated live. Its first four games are1W–0D–3L, no
faults. Both lanes continue; no started game is repeated.

New213 is a read-only finite-tree best-response audit. For our fixed continuation
it compares current value, best response under all learned restrictions,
restriction on the first reply only, and unrestricted best response. Nested
sets separate solver slack from reliance on future versus first-reply modeled
errors. This remains conditional on the searched tree and leaf values.

The native evaluator uses counterfactual reach and one action per information
set, with explicit layering/perfect-recall checks. It is linear in tree size,
not a per-world clairvoyant minimum. Independent exhaustive-policy fixtures,
including zero reach, full confidence and both players, precede nine diagnostic
calls on the three212 cases. No new model, confidence sweep, GPU, live-source
change or ZIP. Source, exact call plan and correctness receipts will be
published before running. Cores4–5 reserved separately from the full-game pairs.

Review requested: do these conditional quantities identify the right distinction
before attempting a whole-strategy restricted-response or learned-value design?
The earlier209 review request remains open; I have not inferred your agreement.

Specification: `astra-submissions/experiments/response-best-reply-20261101/README.md`.

## Original diagnostic stopped; R2 correction

Original213 call1 (`unrestricted`, p0 White ply20) exited-11 after writing
the normal212-format trace and before writing its best-response output.
The new state hash wrongly read all slots of `fixed_policy`, which is
unallocated when confidence is disabled and can be shorter than all slots
when enabled. This is my instrumentation defect, not a playing-engine fault.
Original source, binary, plan and failed receipt remain intact.

R2 is a separate source/output directory. It hashes only active restricted
ranges, checks bounds and adds four complete hook fixtures (model off/on,
optimized/sanitized), all passing. The unchanged BR algorithm again passes
72 exhaustive-oracle comparisons. First test-driver failure from sandbox
LeakSanitizer/ptrace is also preserved; unchanged tests passed outside it.
Nine new diagnostic calls retain the same cases, seeds, confidence and
comparisons. R2 plan/source/correctness will be published before execution.
211 is now1W–5L; neither remaining game can make it qualify for the larger
trial. Both original handles are still live, with no playing faults.

## Completed R2: future restrictions explain a large fixed-tree gap

All nine R2 calls completed. With projected Nd7, same-tree values are
V=+.14554 (current), R=+.13853 (best under all restrictions), F=-.80769
(only first reply restricted), U=-.99329 (unrestricted). Future restrictions
contribute+.94622; truth occupies99.8882% of belief and samples. This directly
identifies fragile continuation value on this tree, not a missing attacker.
After Bc4/Bxc4 in the true world, freeing later replies moves-.76831 to-.96972.

All belief/sample sets match across arms. Unrestricted's first-case choice
flips from212 Rd2 to213 Bc4, so do not infer causality across timed runs.
The nested decomposition is within each tree. Raw `solver_slack` means an
opponent-response gap; for forced-pure roots it also includes adjustment to
that newly fixed action, not just failure to converge. An unrestricted mixed
root gap of.00508 becomes.31417 when its Bc4 root is forced pure. This does
not reopen the failed stable-mix pilot or prove a full-game randomization gain.

13,974 post-run checks/172 frames pass; native oracle comparisons and full-hook
sanitizers pass. Audit time39–72ms. Cores4–5 released, no GPU/new ZIP.
Original213 audit failure stays preserved. Please review `NEXT-DESIGN.md`:
persistent model/adversarial mode with shared own information sets, explicit
compute cost and separate root-sampling control. It is a proposal, not an
agreed or launched experiment. The papers also warn RNR can overfit, so no
presumption that it wins. Current constant-local-confidence family is not
earning advancement from its full games.

Final211 result is2W–0D–6L, no faults. Both handles are terminal and all
owned processes gone. No Misty phase or ZIP; every Astra core is released.
