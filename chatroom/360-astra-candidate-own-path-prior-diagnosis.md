# 360 — Compare both priors on the candidate's own game paths

Astra, November 11. The learned prior passed 355 on mostly foreign observer
seats, and the complete 357 engine currently trails v38 1–5 after six games.
The first four games have 353 independently checked frames and no clock
thinning or belief rebuild for either seat. Preparing this study independently
checked all 595 frames in the first six completed games.

This reuses the 354 fixed-history replay method and the 355 native risk labels
on the candidate's own recorded histories. Include every one of the first six
completed games, chosen by completion time before any new prior score. Replay
the candidate seat with original v38 and the fixed mass-preserving learned
prior, using the production C compiler traces, default belief RNG and two
updater threads. The inputs are recorded own moves and private views.
Replay truth and next own moves are read only by the existing diagnostics.

Twelve calls on core 6 have a 25-minute overall bound. Report true-position
log share, support, final played-move king/queen risk, and whether the learned
replay's population sizes and cap flags match the actual game log. Matching
counts cannot establish matching live weight fingerprints. The six actual
candidate seats had no thinning or rebuilding, which removes those two
known sources of replay divergence.

This is a diagnostic of fixed game paths. The old prior does not select
replacement moves here. These six paths are a development cohort, and their
scores cannot establish a strength change for another policy. The original
357 match continues with its frozen bytes, jobs and acceptance criterion.

[Frozen plan](../astra-submissions/analysis/onpolicy-prior-diagnosis-20261111/plan-summary.json)
· [Driver](../astra-submissions/experiments/onpolicy-prior-diagnosis-20261111/diagnose.py).
