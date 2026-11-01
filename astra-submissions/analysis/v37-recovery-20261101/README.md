# v37 versus v35: recovered match complete

1 November 2026. **v37 scored 56 wins, 2 draws and 42 losses in 100 unique
games (50 colour-swapped pairs): 57%.** A 20,000-resample whole-pair bootstrap
gives a 95% score interval of 46.5–67.0%. The local Elo-equivalent estimate is
+49, with interval -24 to +123; this is not a forecast of arena Elo.

The result is compatible with a modest gain and with no gain. It does not
establish superiority over v35, reach the requested 80% score, or demonstrate
strength against Instructors, duck, HYPOTHERMIA or the top six.

| v37 colour | W | D | L | Score |
|---|---:|---:|---:|---:|
| White | 32 | 1 | 17 | 65% |
| Black | 24 | 1 | 25 | 49% |

All 100 results were normal terminations: 98 king-capturable and two threefold
repetitions. There were no failed recorded cells. The two archives and queue
match their frozen hashes (`final-audit.json`); no parameters changed during
recovery. v37 is Fable's all-games move-model/history refresh, not an Astra
release or the calibrated-root experiment.

## Recovery and evidence limits

The earlier resumed scheduler counted rows rather than missing pair/colour
cells. It replayed pair 36 White and pair 39 both colours. The raw shared ledger
therefore contains 103 rows. The audit preserves that ledger and uses the
**first recorded result** for every cell, excluding the three later duplicates
regardless of their result. No best-result selection or overwrite is used.

The scoped recovery scheduled the remaining 22 cells once each. The existing
service finished successfully before its original 17:57:10 UTC deadline and
was verified inactive with MainPID 0 and exit status 0. Its status, original
plan, receipts, and individual recovery replays are under `reconciliation/`.
Cores 2–5 were released after the final audit.

`audit_results.py` checks the full 100-cell seed/archive/environment manifest
and reproduces boards, both observations, legality and final outcomes for
98 available original replays. Pair 36 White uses the preserved pre-overwrite
copy. The original replays for pair 39 White and Black are unavailable after
the earlier overwrite; their original ledger outcomes remain, but the later
duplicates' replay files must not be presented as those originals. This is a
two-game provenance gap, not a rules-validation pass for all 100 replays.

`canonical-games.jsonl` freezes the 100 retained rows. `final-audit.json` holds
their digest, excluded duplicate rows, interval calculation, per-replay hashes
and the exact provenance exceptions. Reproduce the audit from the repository
root using `.venv/bin/python astra-submissions/analysis/v37-recovery-20261101/audit_results.py`.
