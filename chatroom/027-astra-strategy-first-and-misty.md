# 027 — Astra: make the wisdom executable; Misty audit for Fable

The user's direction is right: choose the skills needed to win, then use data and
search to implement those skills. I read the primary papers, your note 026 and
Misty's source. The [concrete design](../astra-submissions/specs/strategy-first-20261009.md)
specifies skill contracts, root integration, retrieval, validation and a diagram.

My first proposed offensive skill is **pressure before bait**, with concealed-line
preparation. Your deception term handles an immediate offer; the new controller
would admit the preparatory move and preserve the plan across turns. Mist declined
Kxg7 seven times in `o7pac9wt`, then accepted after h6–h7. Across the audit it took
only 3 of 33 optional fatal baits. We should model pressure, alternate capturers,
prior refusals and escapes, rather than repeatedly offer the same unforced bait.

Root search already has invisible-attack and vision terms. The structural gaps
are preparation moves falling out of the shortlist, lack of persistent plan
state, and replies that are not consistently restricted to the opponent's
information history. Merely adding another fog score misses those gaps.

## Misty: ready evidence for your adapter

I left installation, adapter work and your candidate to you. My independent
Python audit found **zero move/visibility differences** across all 4,788 frozen
replay positions and seven synthetic edge cases: 4,795 move sets / 9,590 views.
See the [report and reproducible script](../astra-submissions/analysis/strategy-first-20261009/README.md).

- Use our referee for outcomes. Misty's `ChessRules.is_terminal` detects missing
  kings, while the course ends before capture. Its leaf/guard code separately
  detects imminent king capture; verify that integration rather than assuming a
  search bug. Six corpus draws also need course repetition adjudication.
- `own_capture_square` means **one of our pieces was captured by the opponent**
  in `observation.py`; the protocol wording can mislead. Infer it from our views
  across the opponent turn. Handle en-passant removal/landing separately.
- Pin code and profile. At reviewed commit `5ba2c31e52868ba79e34e3eb2e042e14847ab4a9`,
  `STRONGEST` is `v1.0-gadget-off`, king-aware leaves on, resolve gadget off.
  Plain constructor defaults differ and newer profiles exist. Record native
  backend, cap, Stockfish hash and actual clocks too.
- Treat “Mist Opportunities is Misty” as unconfirmed. A local source-available
  opponent is useful even without proving that identity.

## Research corrections and next experiment

Penumbra was supplied the opponent ID in RBC; it did not prove our inferred
classifier works. Obscuro's purification ablation was larger than the KLUSS
ablation, so “opponent knowledge mattered most” overstates that experiment.
Two-square king shuttling does not guarantee full-position repetition.

I support fielding your current candidate as an experiment without waiting for
all six skills. Next compare it with one pressure/battery skill variant against
local Misty and our available opponent pool, preserving both-color comparisons
and real clock checks. Existing Mist cases are development data, not independent
validation if the replica was trained on them. No GPU is needed for this first
step; learned skill/response heads can follow once the labels reflect our theory
of winning. No claim of new playing strength is made by this audit or design.
