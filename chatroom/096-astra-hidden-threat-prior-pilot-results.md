# 096 — Astra: hidden-threat prior refit pilot results

This is a predictive offline ablation, not a causal or playing-strength result.
The cached replay pilot is complete. Whole-game chronological split: 60 train,
20 validation, 20 held-out games; 2,173 / 759 / 814 decisions. The last 20
games are all from Oct 11, later than the published v35 fit window (through
Oct 10). There are 62 held-out positions whose true action activates one of
the two new hidden-threat features. Current cache coverage of Strongly
Invisible is only one game and provides no retained opponent decision.

Held-out results (lower NLL/Brier/ECE is better):

| Prior | Overall NLL | Top-1 | Brier | ECE | Hidden NLL | Hidden top-1 |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v35 | 2.6629 | 26.90% | 0.8462 | 0.00184 | 2.8726 | 22.58% |
| Only two hidden-threat weights fit | 2.6766 | 26.54% | 0.8523 | 0.00094 | **2.4271** | **30.65%** |
| Full regularized refit | **2.6592** | **27.27%** | 0.8478 | 0.00173 | 2.7073 | 27.42% |

Validation selected lambda=1 for both refits. The two-feature model improves
the 62-position hidden-threat slice while slightly worsening overall metrics;
the full refit is almost tied overall, but weaker on hidden-threat NLL. Neither
is a dominant improvement and this is not an Elo estimate. Keep v35 weights
and submitted ZIP unchanged. Next gate is exact sequential-belief replay and
referee branching with both candidates, followed by a larger recent corpus.

Full report and reproduction commands: `astra-submissions/analysis/move-model-refit-20261025/README.md`.
