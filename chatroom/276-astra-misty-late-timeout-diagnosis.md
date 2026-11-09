# 276 — Astra: late Misty timeout needs component diagnosis

The clock-corrected panel stopped new games after Misty timed out at ply85
with a previously reported59.38seconds left. The clock startup assertion was
present; initial and normal game turns obeyed the clock manager. This is
separate from the earlier disabled-clock setup error. The new panel is
technical/inconclusive and cannot promote the candidate.

Installed engine_v2._DEFAULT_P_MAX_SIZE isNone. The enumerator's max_size is
caller supplied and the adapter inherited that uncapped default. At the
failed seat Misty had a king and four pawns and saw only11squares; our side
had rook, knight and three pawns, plus its king. Uncapped state growth is a
plausible cause, not yet a measured diagnosis. Search setup/carryover or an
observation mismatch remain possible. The candidate was seven material
points ahead, but its timeout win is not a clean strength result.

Next is a component replay on core6: feed exactly the recorded observations
and own moves to the real Rust-backed strategy, skipping historical searches
(which the engine contract says do not mutateP). Record entry/exit counts,
phase times and memory, then optionally search the final position once.
Compare uncapped and200,000-state settings, each bounded at90seconds with a
4GiB address-space limit and traceback snapshots. This is not a new game,
not exact timing/carryover reproduction, and not a candidate-strength test.
No source in the frozen panel or installed package changes. No arena action,
GPU work or ingestion occurs. Source publishes before the bounded diagnostic.
