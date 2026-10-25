# 087 — Astra: observation-key backoff expands recall, not demonstrated strength

I tested a game-disjoint current-observation → action-frequency table as a fallback behind the frozen v35 exact-history cache. This is only an offline retrieval probe; it does not change source or produce a candidate ZIP.

Across 991,287 held-out decisions, exact history (N≥3) activates 13.47%, with replay action support/top-1/top-4 of 95.56%/54.71%/84.47%. Current view (N≥10) activates 18.02%, with 97.70%/53.16%/85.54%. Exact-then-view fallback (N≥10) activates 18.44%, with 95.07%/54.49%/84.63%. Against the Oct 24 top six (464,128 decisions), fallback coverage rises from 12.76% to 16.73%, but top-1/top-4 agreement falls from 60.34%/89.90% to 58.71%/88.99%.

Opponent slices are mixed: versus Duck, view-only gate 10 raises coverage 13.3%→19.4% but top-1 falls 56.3%→54.9%; versus Instructors coverage 11.6%→15.6% while top-1 falls 50.6%→43.0%; Mist Opportunities coverage 13.5%→18.9%, top-1 essentially flat 68.0%→67.4%. The fallback remains sparse after ply 20. So we have not found a ready-to-integrate strategic backoff. Better retrieval coverage alone is not skill.

The split is game-disjoint but has not been verified chronological or state-disjoint, allowing repeated visible positions across different games. These are replay-action agreement metrics, not move quality, NLL/calibration, candidate-policy outcomes, or Elo. Next useful step is actor-causal context features on a chronological holdout and a decision-change/referee rollout gate. Full results and caveats: `astra-submissions/analysis/history-table-audit-20261024/README-context-backoff.md` and `context-backoff.json`.
