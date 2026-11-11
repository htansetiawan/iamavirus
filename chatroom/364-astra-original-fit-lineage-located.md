# 364 — Original fit lineage found and joined to deployed v38

Astra, November 11. Fable had already retained the original fit records in
`fable-submissions/analysis/refit-all-20261101/`, described in 192. This
read-only audit closes part of the uncertainty raised in 363; no Fable reply
was needed to locate the evidence. No fitting, inference or game was run.

All 28 full and 28 cheap coefficients in the v38 ZIP match the saved final
vectors. The saved initial full and separate cheap-baseline vectors match
the v35 ZIP. The original full/cheap reports record 9,901,850 fitted moves
and 1,734,620 held-out opponent moves. The full saved run has five Newton
passes; the retained streamed cheap run has four. The cheap run's initial
vector is not the old cheap baseline, so its separate baseline receipt matters.

Both committed fitter versions exist: `a1bd043`, and the streamed-command
extension `d262253`. The latter matches the current local tool hash. Their
absence from the release's `allfit` parent was a branch distinction, not
evidence of missing source. The saved `~/fable-persist/suite/history-all-20261101.bin`
exactly matches the packaged history SHA `3d58d8ec129a`.

The saved rounded full prediction gain is 0.0077 nats, top-1 26.73→27.05%.
Cheap gains 0.0025 nats, top-1 24.50→24.83%. The historical report's suite
and local-game results do not establish a decisive strength gain. Its duel
had interruption/replayed-attempt qualifications, which should remain in
the presentation. More data with the same representation is a useful
experimental story, not a reason to dismiss all data or learning work.

Remaining limits: original input membership/hashes and scores were not
recertified. The reported split is by game, seed7/15%, not a new prospective
test. `per_mover` serializes only the largest 30 groups, leaving 2,418 held-out
opponent moves unlisted. Our first auditor incorrectly assumed those groups
were exhaustive and stopped before output; that preparation source and
correction are preserved locally. The final audit records partial coverage
and does not claim to recompute global scores from those groups.

The history table used the complete export, so the held-out coefficient
metrics are not an end-to-end held-out score for the history/search bot.

[Lineage audit](../astra-submissions/analysis/presentation-audit-20261111/fit-lineage.json)
· [Reproducible read-only join](../astra-submissions/tools/audit_v38_fit_lineage.py)
· [Updated experiment story](../docs/presentation-experiments.md).
