# November 11 episode generation: independent scan complete

The original scheduled refresh published this generation at 14:42:12 UTC.
It contains **234,911 source games, 469,822 player episodes and 16,475,155
demonstrated decisions** in three gzip shards totaling 838,378,498 bytes.
The source is the morning refresh's fixed journal prefix, not a claim about
every completed game in the live arena.

Original audit session 77213 exited zero once, in 294.95 seconds under the
900-second cap. All three file sizes/hashes, gzip EOFs and JSON rows pass.
Outer decision-array alignment, paired colors, declared counts and technical
policy/value masks reconcile. Both actors' moves reconstruct each of the
234,911 complete source move hashes; there are zero candidate mismatches.

The saved index contains **228,748 distinct complete trajectories**, with
zero groups crossing episode folds. Declared and actual game counts are
187,250 training, 23,585 validation and 24,076 test. The index review's
independent sorted reductions reconcile every color pair, ID, trajectory and
fold with the raw prefix and the earlier 394 projection. It does not repeat
the gzip pass or certify every feature/hidden-board target.

## Holdout and metadata boundaries

The projection is now confirmed on actual shard membership: **795 old test
games entered training, 2,555 old validation games entered training, and 813
old training games entered test**. The original projection evidence remains
unchanged. Absence of internal duplicate overlap does not make this new test
fold untouched by models trained on an older generation. Which models
consumed those earlier folds is a separate provenance question.

The generation still has 164 undated original imports and uses the seeded
duplicate-group fallback. The 381 correction of those imports' dates and
identities remains a separate verified sidecar. These byte/count checks do
not repair the 136 games wrongly attributed to IAmAVirus or change prior
experiments' data. Existing technical-game policy/value labels are masked
off; 1,215 source games have non-normal termination labels.

## Evidence and limits

[Generation summary](generation-summary.json) · [Frozen plan](plan.json)
· [Execution](execution.json) · [Result](result.json) · [Index review](review.json)
· [Auditor](../../tools/audit_daily_episode_generation.py)
· [Reviewer](../../tools/review_daily_episode_generation.py).

Private exact manifest, journal-prefix and per-episode index:
`data/astra-spool/daily-episode-generation-20261111/`.
The indexed prefix has 234,942 lines and 31 historical duplicates; the builder
keeps each ID once. The separate native move export was already verified and
was not rescanned here.

This checks the three shard-file digests. The producer's global interleaved
content digest is not independently recomputed. Rules, every feature value,
hidden-board target semantics and device health are not recertified. No model
fit, training quality, new arena package or playing-strength result follows.
