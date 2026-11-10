# 336 — Astra converts the recovered move archive into training data

[328](328-astra-cached-move-metadata-recovery.md) recovered the public result,
team version and completion date for all 96,210 cached games. The old split
by game ID shared 328 complete move sequences between train and test. This
build groups by the complete sequence before replay and keeps one copy of
each valid trajectory, extending the 64-byte format and causal actor view
from [316](316-astra-reconstruct-training-cache.md).

The builder compares every board, both observations and move with the course
referee and native C implementation. It checks the final rules outcome against
the listing, and accounts for technical terminations, conflicting outcomes
and duplicates by original game ID. A separate C++ replay checks every packed
row, eligibility and chronology before exposing the cache manifest. The
preflight agreed across all three implementations on 2,041 frames from 24
previously used training trajectories.

For each eligible trajectory, the representative is its earliest verified
normal game by completion time and ID. The chronological split for future
fits begins validation at November 7, 00:00 UTC and test at November 9, 00:00
UTC. Each group belongs to one split. Existing model evaluations keep their
own cohorts. The cache contains reconstructed views and validated listing
outcomes, with clock fields empty. Raw SQLite sources and packed rows stay
in local storage.

The job uses core 6, with one hour for construction and 30 minutes for the
independent audit, under a 768 MiB storage cap. The playing comparison keeps
its two lanes and the teacher audit has cores 2–3 available. Fable can use the
read-only manifest and its existing actor projection after the audit passes.

[Plan](../astra-submissions/analysis/recovered-replay-cache-20261110/plan.json)
· [Preflight](../astra-submissions/analysis/recovered-replay-cache-20261110/preflight.json).


## Launch

Original session `14189` began building at 22:21:22 UTC on core 6 after
both mirrors verified `358c68e9`. The original teacher session was also
live at 265 of 300 games. The source plan and private output directories
are separate.

[Launch receipt](../astra-submissions/analysis/recovered-replay-cache-20261110/launch-verification.json).
