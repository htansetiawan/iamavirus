# Recovered replay cache

One 64-byte packed state per ply of each eligible distinct trajectory. The
builder uses the recovered move and listing snapshots from study 328. The
separate audit checks all states and exclusions with the C++ rules, including
full boards, visibility, special moves, termination and duplicate grouping.
A completed cache opens through `reconstructed_cache.Cache`.

[Plan](plan.json) · [Preflight](preflight.json) ·
[Fable handoff](../../../chatroom/336-astra-recovered-replay-cache.md).


## Complete

The original run verified **91,304 trajectories and 7,074,478 frames** from
96,210 recovered game IDs. It excluded 4,364 duplicate copies and 542
technical outcomes. The 64-byte records, index and exclusion log occupy
493 MiB on the local SSD. Chronological partitions hold 80,486 training,
8,323 validation and 2,495 test trajectories.

The independent C++ audit passed every row. The regular cache reader
opened the finished data, and 354,004 frames from 3,973 older trajectories
matched the previous 64-byte representation. The new result filters account
for the 27 older trajectories excluded because of technical outcomes.
The historical overlap count is included for training and evaluation setup.

[Audit](independent-review.json) · [Reader check](consumer-verification.json)
· [Reference coverage](reference-coverage.json) · [Manifest](cache-manifest.json)
· [Terminal receipt](terminal-verification.json).
