# Bounded replay and taxonomy refresh, 2 November 2026

Original refresh handle 20824 completed with exit 0. It listed the newest 600
completed games, accepted 457 new replays and reused 143 cached games, with no
errors or quarantines. There were 472 public GET requests, paced sequentially
at 1.2 seconds. The run took 587.53 seconds. This is a bounded refresh, not a
claim that the whole public archive was synchronized.

The new replays produce 32,332 move annotations across 32,789 validated frames.
Decision-time queen-capture visibility is retained in 675 supplemental events;
19 en-passant captures have supplements rather than altering the original
taxonomy definitions. There are 450 distinct full trajectories across the 457
games. Actual separate games are retained for descriptive counts; confirmation
240 deduplicates trajectories and canonical model inputs separately.

`taxonomy-integrity.json` verifies game IDs, replay hashes, full-trajectory
hashes, move denominators, version/colour/opponent panels and all supplements.
The taxonomy hash is
`2ca4b5fe7b7e7f7d9998675530f81fd47c66b849a59b54c9dc5acfa0cad555bb`.

The saved leaderboard snapshot at **2 November 2026, 2:53 a.m. EST (Boston)**
records IAmAVirus at **1918.30 Elo, rank 11**, active version 37. That version's
record in the snapshot is **117W–8D–101L**. Rank includes all visible rated
teams. This is a timestamped observation, not a live standing or a controlled
comparison with v35.

No belief weight, history table, guard threshold or deployed model changed
when these labels were generated. Experiment 240's model and acceptance rules
were fixed before this refresh completed. Its newer holdout contributes 126
games from the pinned top-12 cohort after exclusions.

`execution.json`, `manifest.json`, `standings.json`, the compressed taxonomy,
summary and integrity check preserve the evidence. Raw public replays remain
in the ignored local cache, pinned by SHA-256. The currently read-only bulk
drive was not used for this run.
