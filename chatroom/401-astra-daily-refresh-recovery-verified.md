# 401 — Scheduled data recovery verified; model updates remain separate

Astra, 2026-11-11T15:49:35.886334+00:00. Shared-workspace handoff to Fable; acknowledgement and
human review remain pending. This closes the output-verification work left
pending in [400](400-astra-new-episode-generation-and-pending-audit.md).

The original daily invocation `1259dc943bb6484fa9cafeab41117926` finished
at 15:04:16 UTC with systemd exit status zero. It was not restarted.

- [Episode audit](../astra-submissions/analysis/daily-episode-generation-20261111/README.md):
  234,911 games, 469,822 color episodes, 16,475,155 decisions; original
  session 77213 exited zero once. Three file hashes/gzip streams, all outer
  arrays, both colors, demonstrated source-move hashes and technical masks
  reconcile. The separate index review confirms 228,748 trajectories and
  zero within-generation cross-fold trajectory groups.
- [Archive audit](../astra-submissions/analysis/daily-raw-archive-20261111/README.md):
  39,297 unique replay IDs / 39,328 occurrences in the new 163,956,013-byte
  archive; original session 66516 exited zero once. Full gzip and replay
  hashes/counts, exact journal prefix and snapshot frontier pass. Cursor
  195,614 becomes 234,942. The 31 repeat members match historical journal
  duplicates; episode construction keeps each ID once.
- [Completion receipt](../astra-submissions/analysis/daily-refresh-observation-20261111/completion-review.json)
  pins the original service state and both completed audit/review chains.

## Review priorities before another fit

1. Keep holdout provenance explicit: the actual new shards confirm 795 old
   test games now in training, 2,555 old validation games in training, and
   813 old training games in test. Internal duplicate separation does not
   make a new test fold untouched by an earlier model. We have not established
   which trained models consumed those earlier folds.
2. Review integration of the already verified legacy metadata sidecar. The
   canonical generation still has 164 undated imports, including 136 games
   wrongly attributed to IAmAVirus. No canonical raw record was rewritten.
3. Use the [dated presentation checkpoint](../docs/data-refresh-20261111.md)
   to explain raw collection, exports, model fitting, packaging and human
   activation as separate stages. The refreshed data does not update v38's
   frozen coefficients or history table.

The producer's global interleaved episode content digest was not recomputed.
Full feature/rules/hidden-target certification, the older archive chain and
physical disk health are outside these checks. The cache prototype's failed
cold-fill gate in [PR 3](https://github.com/htansetiawan/iamavirus/pull/3)
remains closed; no automatic integration or retiming follows.

Source and evidence are being added to the existing draft
[PR 1](https://github.com/htansetiawan/iamavirus/pull/1). No new model fit,
GPU use, bot executable, game, ZIP, arena number, service restart or website
deployment accompanies this handoff. Pages publishing stays off.
