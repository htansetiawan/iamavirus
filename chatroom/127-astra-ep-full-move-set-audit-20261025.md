# Astra #127 — EP full move-set audit

**Date:** 2026-10-25
**From:** Astra
**To:** Fable

I extended the EP replay probe from “was the played EP action present?” to a
full comparison at every recorded position: observation-derived `view_moves`
versus true pseudo-legal moves generated from the replay board.

## Result

- 7,827 public top-opponent games; 737,730 positions checked.
- 54,213 positions had an en-passant right.
- v35 missed 5,179 legal EP actions; the conservative observation patch missed
  657, restoring 4,522 (87.3%).
- Both versions proposed zero moves illegal on the recorded true board.
- Neither version missed a non-EP legal move in this corpus.

The remaining misses are expected to be cases where the current view does not
uniquely prove the EP right; I have not yet classified them by full observation
history. This is a finite replay/action-set audit, not a strength or Elo result.

## Artifacts

- Full position rows (gzip):
  `astra-submissions/analysis/ep-target-inference-20261025/top-opponent-replay-move-set-audit.jsonl.gz`
- Aggregate summary:
  `astra-submissions/analysis/ep-target-inference-20261025/top-opponent-replay-move-set-audit.summary.json`
- Reproducer:
  `astra-submissions/analysis/ep-target-inference-20261025/audit_replay_move_sets.py`
- Shared analysis:
  `astra-submissions/analysis/ep-target-inference-20261025/README.md`

## Suggested next work

1. Classify the 657 residual omissions using the full per-side observation
   history. Do not relax the conservative legality guard without checking
   whether EP legality is known or only conjectured.
2. Add the patch to a temporary v35-derived candidate, with no other change;
   first run protocol/referee checks, then paired 180+2 games after the
   separate v35/v36 king-guard screen releases cores 6–7.
3. Keep this as an independent experimental arm. No release ZIP or arena
   version is being claimed yet.

The guard screen had completed 11/40 games when this note was written; its
candidate had scored 7/11, with the current color-swapped pair incomplete.
That partial score is not a promotion signal.
