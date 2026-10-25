# 098 — Astra: two hidden-threat weights change the intended failure family

I patched the v35 `theta_full` array only, using the held-out-training fit
(MM_CHECK_UNSEEN=1.4030843, MM_THREAT_UNSEEN=0.4405588), rebuilt the exact
archive source, and replayed the same 16 targeted fixed prefixes with the same
search settings.

| Metric | Frozen v35 | Two-feature candidate |
|---|---:|---:|
| Exact referee-fatal selected move | 16/16 | 9/16 |
| Selected action in known safe alternatives | 0/16 | 7/16 |
| Median true-board posterior share | 0.0675% | 0.478% |
| Median truth rank | 273.5 | 33 |

Each of the seven changed-to-safe moves is actor-legal and was referee-labeled
nonfatal in the source audit. One other changed choice was still fatal. This
shows the fitted likelihood materially shifts support and choices on these
specific unseen-arrival prefixes; it does not estimate arena Elo. Exact
enumeration found no immediate king-capture reply to any of the seven rescued
moves. On 12 nonfatal king-move controls, baseline and candidate both selected
0 immediately fatal moves and allowed no immediate king-capture replies; the
candidate changed its move on six controls, all still immediately safe. These
are small targeted sets. Next, branch all eight changed failure-case actions,
including the seven rescued choices and the changed fatal choice, through
deeper referee continuations. The submitted ZIP/default remain unchanged.

Trace and exact one-ply comparison are in
`astra-submissions/analysis/move-model-refit-20261025/hidden-two-only-sequential-16.json`
and `hidden-two-only-referee-compare.json`.
