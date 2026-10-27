# Scope declaration: corrected candidate r4

Declared 2026-10-27 16:30 UTC by Fable. r3 (zip `5cdbb9caf8a3`, rejected at gate 3 on 27 October,
note 169) is untouched; none of its games or replays count for r4.

## Bytes

- Zip: `data/candidates/iamavirus-v36-candidate-mist-c-v20-r4.zip`, sha256
  `1649dfbfe23b36991bfc6d6fd16c54383bc4079f30b033845e9bfa550e52dbf2` (local, untracked like r3's).
- Source: mist-c `dd89907` = r3's `ff89313` + `2524f8e` (tests only) + `dd89907` (the fix).
  Every member equals r3's except `src/main.c` (`c8916434655c`, r3 `5bb5f9d8f056`).
  `bin/stockfish` `0f83d24cc46d` and `data/history.bin` `5ed8c2b5478d` as in v35 and r3.
- gcc 13 build of the zip: `65162c2c780c`; handshake answers `ready`. `make test` passed on
  `dd89907` before the push (ledger 06:32Z).

## What r4 is

v35 plus two things and nothing else:

1. Terminal-aware capture events in all three risk helpers (`best_capture_net`, `queen_risks`,
   `material_risk`): an enemy capture that leaves the enemy king capturable is a won game, not a
   material loss (notes 167, 168). The referee's `outcome()` ends the game the moment the mover's
   own king is attacked, so this is the rule, not a heuristic. This also changes v35's queen guard
   where such captures occurred.
2. The piece term exactly as in r3: rule B2, lambda 0.758, threshold 3, cap 20,000, on by default.

## Evidence plan

- Gate 1: Astra's review of these bytes (requested in the ledger, 16:30Z).
- Development evidence (not a gate): paired A/B replays, both on the r4 build, A with
  `MIST_PIECE_GUARD=-1` (v35 rules + the terminal-aware events), B defaults; the three fresh sets
  and the four frozen sets, 2.5 s, seed 1, one worker, truth scored; running since 16:22Z on cores
  2-5; report `r4-dev-report.md`. The cross-run columns against the r3/v20 outputs are indicative
  only (different load).
- Gate 3: r4's own bench, the r3 queue structure (40 vs v35, 32 each way vs Misty, 32 v35 vs
  Misty; 180+2; cores 2-5; the gate-3 runner at iamavirus `63f7265`), seeds fixed in the gate-1
  receipt; thresholds unchanged from the contract: M - B >= -4 and D > 0; attributable failures
  reject. Launch after gate 1; about ten hours.
- Decision: the contract's confirmation-or-rejection point (28 October 20:00 UTC) and Henry's
  Thursday submit-or-reject.
