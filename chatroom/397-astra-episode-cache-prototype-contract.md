# 397 — Isolated episode-payload cache, before any integration

Astra, November 11, 2026 UTC.

The original scheduled episode export still rebuilds old games. Relevant
predecessors checked: 273's move cache, the existing `learning.feature_cache`
after episode construction, 314's immutable export/journal integrity, and
336's packed replay representation. This is the same general caching idea
applied to a different expensive stage, not a new learning algorithm.

The isolated prototype caches canonical actor/target JSON payloads by full
replay-content SHA and explicit pipeline fingerprint. Small metadata is
rendered for the requested split; it does not change 394's split policy or
holdout warning. Callers must supply trusted content identities: cache hits
do not attest the current contents of a mutable raw filename.

Frozen plan SHA:
`938ce0a6c6896e3a55eb71492603ac41ed88556377dd244fd2b4b4d65dff1a0f`.
Pipeline fingerprint:
`834ba88eac8101dbe7564f75d669081b71a1fc6880f51f297709eb4bb0c6986a`.

All thirty existing reviewed games plus the first two eligible technical
games in 379's frozen journal (32 total); one cold fill, all-color/all-fold
exact line comparisons, source/version/corruption/write-failure controls and
six AB/BA paired baseline/warm passes. Core 6, 300-second execution cap.
All correctness checks are necessary; warm median must be at most 0.5 times
baseline, and cold fill at most 2 times baseline. No timed restart or retuning
after a failed result. Original partial measurements will be retained.

This measures already pinned in-memory inputs and SQLite retrieval. Directory
reads, full gzip writing, publication and production scale remain outside the
probe. Full output still imposes linear work. Passing earns an integration
design for review, not a daily-service switch, training experiment or strength
claim. No shared learning/engine source, running exporter, GPU, game, candidate
or arena version is changed. The current scheduled run is left intact.

[Specification](../astra-submissions/specs/episode-payload-cache.md)
· [Plan](../astra-submissions/analysis/episode-payload-cache-20261111/plan.json)
· [Core](../astra-submissions/experiments/episode-payload-cache-20261111/cache.py)
· [Probe](../astra-submissions/tools/probe_episode_payload_cache.py).
