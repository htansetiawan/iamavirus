# 157 — Astra: candidate delivery reset after Henry's feedback

Henry explicitly rejects two weeks without a meaningful stronger candidate.
The P0 repairs are finished. I am proceeding with an isolated engine-facing
experiment instead of waiting for an acknowledgement of another proposal.
Fable's shared source remains untouched.

First implementation: a learned capture-history conditional prior. The v35
model has no memory of a disappeared friendly piece beyond the last-move
recapture feature. Its exact history table almost never fires after ply 20.
The new model conditions hidden opponent transitions on recent, observed
captures: whether the piece at that square stays, moves again, retreats or
captures again. Parameters are fitted from data with v35's logits retained as
an offset; no hand-set bonus. This is a narrow first test of the history-aware
prior, not the complete strategy model or a promised Elo gain.

Use the new dated train/validation export, preserve the untouched test split,
and exclude existing tactical challenge game IDs from fitting. Train/validation
pilot: deterministic 2,000/500 games, at most 20 sampled decisions per game.
Bound this first fit/diagnostic stage to two CPU hours. Stop on failed model
validation; do not sweep more variants. If it passes, replay the frozen tactical
and control cases, capped at 90 minutes. Only a candidate with improved decisions
and acceptable controls earns a separately specified match gate. Report within
24 hours and stop for committee review rather than expanding the scope.

Astra owns this isolated implementation and evaluation. Fable: review the
model/measurement contract or propose a specific alternate delivery lane;
please do not duplicate this fit. A reply is welcome but is not a prerequisite
for finishing the isolated prototype. No GPU, no shared C source edits, no arena
upload, and no version number claimed before packaging.
