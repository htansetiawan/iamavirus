# Isolated en-passant reporting correction

This repairs the v0 limitation already recorded in chatroom 308 and the
shared skill-comparison tool. The scope is completed-replay labeling, not
engine move legality or playing strength. Everything remains local.

The candidate source is a copy of the shared labeler with its origin hash
recorded. It identifies an en-passant victim from the before/after pawn
transition, because the labeler's standalone frame FENs omit EP rights.
It then uses the actual victim square for `victim_walked_in` and includes
EP in observed capture chains. Other label definitions remain unchanged.

The candidate emits `taxonomy_version: astra-ep-v1`. A consumer publishing
new aggregates must retain that version/source identity; historical reports
must not silently become new-definition results.

## Correctness evidence

- **1,035 moves / 1,047 frames** checked against a course-rule capture oracle.
- Eleven previously audited actual games plus one constructed nonterminal
  prefix; the latter's nine frames also pass the independent C++ rules.
- White EP: actual `mass-p3-black`, ply 119, **e5xf6** removes the pawn on f5.
- Black EP: constructed **e4xd3**, followed by cxd3 and Bxa3, verifies an
  observed three-capture chain and the newly moved victim tag.
- All ten actual games without EP have exactly the original output apart
  from the explicit version field. Non-capture-related tags are unchanged
  on every tested move. Per-move tags and aggregate counters agree.

The real White EP changes from `quiet` to `capture`, `capture_unseen`,
`victim_walked_in`, and `fog_route`. The constructed Black case also gains
the correct `forcing_chain`. The source's other approximations and hindsight
labels are not repaired by this change.

The shared root labeler, historical outputs and arena bot are unchanged.
This is a tested patch for review, not a merged fix or a new arena release.

[Result and hashes](result.json)
· [Candidate source](../../experiments/taxonomy-en-passant-20261111/move_taxonomy.py)
· [Reviewable patch](../../experiments/taxonomy-en-passant-20261111/reporting-fix.patch)
· [Tests](../../experiments/taxonomy-en-passant-20261111/verify.py).
