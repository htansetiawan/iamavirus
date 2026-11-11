# Canonical episode cache: fast warm path, failed cold-fill gate

The prototype applies 273's general caching idea before episode export.
`learning.feature_cache` instead caches arrays after episodes exist, and 336
stores packed replay states. The shared exporter and current scheduled run
remain unchanged.

The frozen 32-game sample contains all thirty exposed 389 games and the first
two eligible technical games from 379's frozen journal. A cache entry contains
exact actor/target JSON prefixes and small metadata, keyed by full replay SHA
and explicit pipeline fingerprint. Fold assignment is outside the cache.

## Result under the original contract

| Check | Result |
| --- | --- |
| Both colors, all three folds | 192 exact canonical JSON-line comparisons pass |
| Source/version/error controls | All 12 pass |
| Six balanced baseline passes, median | 0.309761 s |
| Six balanced warm passes, median | 0.010487 s; 0.033855× baseline |
| One cold fill | 0.913880 s; **2.950271× baseline**, above the 2× limit |
| Overall integration gate | **Failed** |

Original session 45180 exited zero once; its completed result explicitly sets
`all_gates_pass: false`. The 300-second cap was respected: 3.92 seconds total.
No timed repeat or threshold change followed. Each warm probe reproduces the
same output digest; no reconstruction callback runs on a warm hit.

Controls cover changed pipeline/source keys, malformed keys, an unknown fold,
episode/source disagreement, raised builder interruption, a read-only failed
write, corrupted compressed/raw data, bad framing, metadata source substitution
and the decompression limit. The SQLite database retains exactly 32 records.

Separate read-only review reproduces all twelve timed output digests from an
independently decoded database. It reconciles 64 episodes / 2,734 decisions
against source observations/actions, including both technical games' loss
masks. Database integrity, before/after hashes, all source pins, timing order,
medians, gate arithmetic and released core lease pass. The review does not
repeat native reconstruction, corruption controls or timing.

## What this does and does not tell us

Warm retrieval is about 29.5× faster on this small pinned-input probe. The
current cold path violates the frozen requirement, so this configuration does
not earn integration. Neither result measures raw-identity discovery, full
gzip writing/publication, production storage scale or Elo.

A conditional repeat-workload model is
`relative cost = h * 0.033855 + (1-h) * 2.950271`, where `h` is hit fraction.
Its algebraic break-even is about **66.9% hits**, assuming these measured
per-case costs mix linearly. That is a cost explanation, not a revised gate,
measured production hit rate or end-to-end prediction. The original failed
cold gate remains failed.

## Concrete integration issues for review

The module has one transaction per cold record. A separately designed batched
writer could reduce commit count, but its cost and rollback behavior have not
been tested here. No replacement configuration is run automatically.

Safe reuse also requires a trusted ingestion content-hash manifest and a
complete pipeline fingerprint. A cache hit selects pinned content; it does
not prove that a mutable raw path still contains it. Seeding from old exports
requires provenance of the builder that produced them; matching version labels
alone is insufficient. The current prototype is not a bulk cache seed tool.

For a future reviewed implementation, the work to target is
`N * lookup + new_or_changed * reconstruction + full_output_write`, with cache
miss commits amortized over batches. Full output remains at least linear in
its byte size. Existing fold lineage and used holdouts must remain explicit;
caching does not repair the 394 split warning or 381 original metadata.

[Specification](../../specs/episode-payload-cache.md) · [Frozen plan](plan.json)
· [Result](result.json) · [Read-only review](review.json)
· [Core](../../experiments/episode-payload-cache-20261111/cache.py)
· [Probe](../../tools/probe_episode_payload_cache.py)
· [Reviewer](../../tools/review_episode_payload_cache.py).

Private inputs, measurements and the 299,008-byte database stay under
`data/astra-spool/episode-payload-cache-20261111/`. No shared source, actual
dataset generation, model, GPU, bot search/game, package, arena number,
running service or website deployment was changed.
