# Persistent-mode finite-tree response audit

Read-only successor to 213's response diagnosis, built from the frozen 214
playing candidate. No code in the live 214 match trial changes.

The same three earlier development positions get nine diagnostic calls:
unrestricted, local projected response, and persistent projected response.
Private replay inputs and original seeds; max 10-second search, 120-second
process cap, sequential on reserved cores 4–5. The audit runs after move choice
and does not grow the tree or perform additional CFR iterations.

BR code is byte-identical to the independently enumerated 213 solver. New
export code maps each latent-mode branch to its physical board and uses the
actual root chance weights. Eight full-export fixtures pass optimized and
ASan/UBSan: unrestricted, local restriction, two persistent modes, and the
all-model endpoint. They verify weighted sums and analytic restricted gaps,
including shared own root strategy and an unallocated disabled model.

On each fixed tree and own policy, record current opponent value, restricted
best response, first-reply-only restricted best response, and unrestricted
best response. Free-mode branch values must agree across the three best
responses: relaxing restrictions in the other mode cannot change them.
All gap contributions must come from the model-mode quarter of root chance.
With finite leaf utilities bounded by [-2,1], its value effect is at most 0.75;
this is an intentionally loose finite-tree bound, not an arena guarantee.

Report both mixed and forced-pure roots. Changing the root to a pure action
can give the opponent a new adjustment opportunity; its gap is not simply
solver convergence error. Cross-arm trees can differ under the clock, so use
the nested decomposition within each tree, not differences between trees as
causal proof. Outcomes and truth-board membership join only after all calls.

These are reused development examples, not held-out strength evidence. The
ongoing 214 full-clock trial retains its original gate regardless of results.
Any execution/assertion/pin error stops the audit; preserve the failed attempt
and do not silently repeat calls. Publish source and plan before execution.
