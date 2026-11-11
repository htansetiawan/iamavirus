# Why the episode export remains at November 2

Read-only reconstruction on November 11 UTC. This explains the operational
gap behind 379; it does not add another pipeline repair or training run.
The current script already contains the 272/273 fixes from November 9.

| Day, UTC | Saved evidence | Consequence |
| --- | --- | --- |
| November 2 | Episode export finished at 11:41:55, 195,614 games | This remains the published episode generation |
| November 3 | Old move export took 3h 31m 54s; dataset began at 15:22:45; systemd terminated the service at its six-hour limit | Dataset had 37m 26s before termination; last progress line is 9,000/200,378 |
| November 4 | Old move export took 3h 36m 28s; dataset began at 15:28:26; another six-hour termination | Dataset had 39m 39s before termination; last progress line is 40,000/205,068 |
| November 5 and 9 | Six-hour termination while the log still says `mist-c move export` | No dataset-start marker in either log |
| November 6 | Ingestion and dataset logs contain storage I/O errors | Script reached `done`; that marker and systemd success do not prove successful exports |
| November 7 | Missing `data/raw/games` / broken storage path | Heavy exports skipped; later report steps also failed |
| November 10 | `fsync` I/O failure during ingestion; current raw guard stops the script | Service exits 1 before reports or heavy exports |

The November 3/4 figures are **last logged counts**, not an exact count of
work completed at the signal. Local log truncation alone would not establish
timeout; the saved host journal explicitly records the six-hour termination.
Different source totals in those old progress logs are preserved as recorded.

## What was already changed

- 272 / commit `cca63ed7` puts reports and their publication before heavy
  exports, so a later exporter timeout cannot prevent their initial publication.
- 273 / commit `a94110fd` replaces the repeated directory-scanning move
  exporter with the cached, bounded exporter and complete-generation pointer.
- The raw-availability guard now fails the service when raw storage is
  unavailable, preserving old reports rather than treating empty inputs as new.

This review confirms their presence in the current script. It does not claim
that the full scheduled job has completed successfully after storage recovery.
The captured current service state remains `failed`, with November 10 exit 1.
No restart, timer change, mount repair, export or publication was performed.

## What the gap means for learning

Raw collection, reports, episode export, move export, model fitting, history
counting and arena upload are separate steps. The 379 audit verifies the
existing episode bytes and identifies 37,868 current raw games absent from
that generation. The separately verified November 10 move export is newer;
it does not automatically update the opponent prior in v38.

The deployed fitted vectors and history table stay frozen until a separately
tested package is built and uploaded. The retired CNN–GRU/PPO path consumes
episode shards; it is not a running learner inside the current bot.

The 381 sidecar recovers dates and true team identities for all 164 old
corpus imports. Current canonical records and the November 2 generation still
have their original metadata. A future generation must explicitly consume
the correction, state its split and preserve previously used holdouts.

## Evidence

[Result and source hashes](result.json) ·
[Auditor](../../tools/audit_dataset_freshness.py).

Private saved log copies, filtered systemd journal and status:
`data/astra-spool/dataset-freshness-lineage-20261111/`.
The result pins the logs, current script, current manifest, prior fixes,
379 export audit and 381 independent provenance review. No model-strength,
feature-label or hardware-health claim follows from this operational audit.
