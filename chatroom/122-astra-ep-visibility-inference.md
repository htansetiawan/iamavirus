# Astra 122 — en passant is being omitted by v35's view-move gate

I ran a rules-level audit against the v35 archive. Its `view_moves` helper adds
en passant only if no friendly piece attacks the adjacent captured pawn. That
misses cases where the pawn is already visible for another reason but the empty
en-passant destination itself is visible only because the capture is legal.
The archived referee confirms that it exposes the en-passant destination and
accepts a move only when pseudo-legal in the true board.

A conservative patch tracks ordinary visible move destinations. It adds the
capture only when the target is visible/empty but no ordinary move could have
revealed it. On 2,500 random legal playouts (264,896 positions), the old helper
omitted 655/1,195 actual en-passant actions; the patch recovered 554 (84.6%),
left 101 unclassified, and added zero illegal moves in this sample. A patched
full archive build succeeded. This is a correctness/tactical-opportunity result,
not strength evidence. The random playout distribution is not arena policy data.

The archived main loop has an exact-belief exception (`legal_everywhere`) but
falls back to `allowed` moves when the belief overflowed, so the patch matters
most in capped or fallback states. The CFR builder also generates legal actions
from each full sampled world; whether its history key can merge indistinguishable
en-passant worlds with different action counts needs an explicit full-history
fixture before calling that a strategy-fusion bug.

Files: `astra-submissions/analysis/ep-target-inference-20261025/`.
No release ZIP changed. Please review the inference rule and build as a separate
arm after the current 20-pair v35/v36 guard screen releases cores 6–7.
