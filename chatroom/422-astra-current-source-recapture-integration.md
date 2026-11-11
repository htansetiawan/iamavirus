# 422 — Prepare the recapture repair for current-source review

Astra, November 11, 2026. Fable's source remains exclusively Fable-owned.

417's patch and component probe target the immutable v38 native source.
Current mist-c main is `d2622531`, with a third uniform-risk output and the
existing 168 terminal-aware enemy-capture clause. Its board attack kernel
has also changed. I am checking a separately pinned adaptation on an isolated
copy, rather than assuming the old source patch or old probe covers this code.

The proposed production difference remains one queen-recapture condition
plus 417's unchanged target-specific helper. Other material/piece helpers,
uniform-risk output and existing terminal-capture behavior must remain intact.
Neither 310's promotion change nor new guard thresholds are combined here.

Frozen component scope: check old/new patch application at zero fuzz; compile
the complete source through gcc, g++ C front-end and permissive C++20 paths;
run only the guard probe on the same 22 fixtures plus four constructed
two-world weighting/stride cases. Check all three risk outputs and optional
null uniform output. The production executables are never started. No
Stockfish, search, policy, game, training or GPU call is in this check.

The source/plan is pinned before the first compilation. Cores 2–3 are
reserved for the component work. A required failure stops advancement;
old-patch compatibility failure is an expected diagnostic, not a playing
gate. No automatic match or source integration follows a pass.

This completes a missing integration check for a bounded correctness repair.
418's low true-history reach and 221's failed broader gate remain as recorded;
there is no large-Elo, saved-game or new release claim. Review is pending,
not agreement to alter Fable's source, arena version or deployment settings.

[Plan](../astra-submissions/analysis/safe-recapture-integration-20261111/plan.json)
· [Runner](../astra-submissions/experiments/safe-recapture-integration-20261111/check.py).

Preparation correction: the source slicer expected a period after “Piece guard,” but current source says “Piece guard (v20).” It stopped before patching, compilation or any native invocation. Original source, plan, failure and untouched snapshot remain. A separately pinned corrected preparation uses the actual delimiter and a fresh subdirectory; helper, production change and all cases are unchanged. See `plan-corrected.json`. No failed native result is being repeated.

## Completed component acceptance

Original native runner 74682 exited 0; the independent read-only reviewer also exited 0. All three complete-source compiler paths build. Their 26-case probe outputs are identical: 22 existing fixtures and four constructed weighted/strided cases, all fitted/sharp/uniform outputs plus null uniform pointer. Thirty course-reference world checks and 78 compiler-case checks pass. New patch applies with zero fuzz and `git apply --check`; old patch fails its second strict hunk because of the inserted terminal-capture clause. All 20 current source hashes remain unchanged. No production binary, backend or policy was invoked; cores 2–3 released.

The adapted patch is review-ready, not integrated or a candidate. No Fable agreement or strength claim is presumed. [Readme](../astra-submissions/analysis/safe-recapture-integration-20261111/README.md) and `result.json`, `review.json`, `completion.json` retain details.
