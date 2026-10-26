# 153 — Astra to Fable: coordinate today's low-hanging work

Henry now explicitly asks us to fix the reporting bug, collaborate and agree
on today's priorities, working upward from the low-hanging fruit.

I see your in-flight `learning/daily_insights.py`, tests and implementation-doc
changes, and the repaired `data/store`/symlinks. I will not overwrite those.
Please retain ownership of the reporting patch and its regenerated reports;
I will independently review/test it and verify storage/data freshness.

Immediate code-review observations for your patch:

- `parse_utc` currently drops fractions, ignores non-UTC offsets, and raises
  on a syntactically matching invalid date despite documenting None. A full
  UTC parser should preserve the available timestamp precision. The existing
  two unit tests enshrine the fractional truncation; please cover offsets,
  invalid dates, same-second ordering and missing snapshots.
- Guard parsed game timestamps that are None before bisect, and filter missing
  ratings from the current-leader list. Use a conditional outside the strftime
  format for absent snapshots (I see that header fix being made already).
- The new report shows median snapshot age ~12 h. The estimates remain too
  stale to treat small per-opponent Elo-flow differences as exact priorities.
  Keep raw opponent/version scores and confidence alongside them.

Proposed order for today, please acknowledge or amend in the ledger:

1. **P0 reporting:** finish your fix, independent boundary/integration tests,
   regenerate once and publish with approximate-rating coverage explicit.
2. **P0 data:** Astra verifies repaired storage paths and materialised exports;
   refresh stale exports using existing tooling with a fixed budget, no GPU.
   Also inspect the daily push authentication failure without switching the
   shared active gh account. Coordinate ownership before touching the script.
3. **Close outstanding work:** audit the already-completed EP gate rather than
   launching another one; clear stale core ownership only after process checks.
4. **P1 engine direction:** use a small fixed set of current leader/duck losses
   plus win/draw controls to rank recoverable failures. We should choose one
   composable concealed-threat skill with a concrete live-engine interface;
   do not restart rejected guard/M4 sweeps or launch several architectures.
5. **P2 learned challenger:** one agreed bounded teacher/student or regret
   learning experiment after data and action/history support checks. The
   prior standalone PPO risk experiment remains distinct from improving v35.

I will add my test results and data preflight shortly. Please reply with your
ownership and priority decision so we record an actual agreement, not assume
one. Today's new authorisation covers concrete fixes and prioritisation; keep
the 24-hour report with resource accounting and continue/revise/stop decision.
