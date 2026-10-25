# v35 information-set and en-passant action audit

2026-10-25. Read-only audit of the archived Fable v35 Mist-C engine. No
candidate ZIP or arena submission was produced.

## Questions

1. Does `gtcfr.c` assign different action sets to nodes with the same
   acting-player information history in reachable search trees?
2. Does v35's observation-derived root move list contain recorded legal
   en-passant actions in real replay positions?

## Evidence

The v35 archive SHA-256 is
`24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`.
Its `src/gtcfr.c` SHA-256 is
`0bcdbea2d0c903c7245f8dc835647da67baa6a0fed63c0c7c83626a8a6c5b984`.
The temporary audit source's `gtcfr.c` is byte-identical to that archived
file. Instrumentation was added only to temporary copies under `/tmp`.

### Information sets

- Eight forced random games: 288 total plies and 142 searched decisions.
- Six real cached replay positions containing an en-passant move, at which
  the acting bot's belief was audited.
- Zero action-set, action-order, or action-count mismatches in the instrumented
  internal CFR trees in the eight random games or six targeted replay trees.
- At each of the six replay roots, every retained belief board included the
  recorded en-passant right, and the root candidate action signatures agreed
  across all retained belief states.
- The four replay positions with capped belief support had 285–1919 retained
  states; two other positions had exact supports of 10 and 26 states.

This is evidence about these finite, sampled, reachable trees, not a proof of
information-set consistency for all histories. It does not establish that
future own actions are independent of private board states in every tree.

### Root move-generation omission

The instrumented v35 `view_moves` omitted the replayed, legal en-passant action
in four of six positions: `0izeuvgd` (`d4e3`), `8wef0oiw` (`g4h3`), `7gylb8nl`
(`g5f6`), and `3cvzfvz5` (`c5d6`). It included the move in `6v4llaz2`
(`g5h6`) and `jpo6pr7m` (`g4f3`). All six recorded actions were legal in every
retained belief board. In three of the four omission cases, the belief was
capped; v35's final legality fallback then restricts selection to `view_moves`,
so the omitted action is unavailable to the deployed choice path. In the
remaining exact-belief case, the universal-belief legality check can admit it.

The existing conservative inference patch in
`../ep-target-inference-20261025/belief-ep-observation.patch` was applied to a
temporary copy of v35. On the exact pre-move observations from all six replay
positions, patched `view_moves` included all six recorded en-passant actions.
The full patch's separate seeded audit covered 2,500 random legal playouts and
264,896 positions: it recovered 554 of 655 baseline omissions, with zero
additional illegal candidates observed (finite sample only). See that audit's
README for the generator and limitations.

## Interpretation and next gate

The targeted CFR check did not find the hypothesized action-set mismatch. The
root en-passant omission is directly reproduced and the patch fixes the six
selected replay positions. This makes the patch a correctness/action-coverage
candidate, not a strength result. Before release, preserve referee-backed
regressions for the six cases, run the candidate through whole-game protocol
checks, then compare it in paired games after the current v35/v36 full-clock
screen releases cores 6–7. Keep the en-passant patch separate from the king-
guard arm so results remain attributable.

## Reproduction pointers

- Random-game action-list audit: `/tmp/infoset-audit/summary.json`.
- Real replay action-list audit: `/tmp/infoset-audit-ep-flow/summary.json`.
- Temporary source trees: `/tmp/mist-infoset-epflow/` and
  `/tmp/mist-infoset-epflow-patched/`.
- Existing replay-patch audit: `../ep-target-inference-20261025/README.md`.

The temporary audit binaries and logs are not release artifacts. All input
replays are public/local cached copies; no private API was used.
