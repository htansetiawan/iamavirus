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

## Measured component result and stopped-panel audit

The comparison finished five first attempts: four normal and one opponent
timeout. Independent referee audit passes all 406 frames, all source/output
hashes and endings. Only two White matched cells are clean (candidate 1,
control 1.5); there is no strength conclusion. No own technical failure,
27 unstarted games, no remaining actor process. Original 89024 is terminal.

The diagnostic (original 27054, exit 0) shows uncapped P reaching 2,992,741.
Its Rust opponent update aborts under the diagnostic's 4 GiB address-space
limit while requesting another 939 MB. RSS at completed checkpoints was at
least 906 MiB; the last update's actual peak is unknown. Address-space limit
is stricter than resident memory, so this is not an arena-OOM claim. The
200,000-state replay finishes 86 frames plus a final legal search in 6.8 s,
with 168 MiB peak recorded RSS. Historical searches/carryover were skipped;
the exact live failure phase remains unobserved. Caps change approximation,
so this is neither a pure speedup nor a strength result.

The live material position was +7 for us with the opponent seeing 11 squares,
consistent with a vision-denial/state-growth hypothesis worth future study.
Next: qualify the fixed 200k caller setting with v38 only, both colors,
without a score condition. No candidate change or parameter sweep. All old
comparisons remain closed and technical wins are not promoted.

Native performance follow-up remains separate: belief_sample already uses
cumulative weights and binary search (O(N + K log N)). belief_shrink sorts all
N random ranks and opponent expansion sorts 64-bit candidate keys. Those
sorts need phase-cost measurement before a heap/radix rewrite; no bottleneck
or end-to-end gain is claimed from reading the loops.
