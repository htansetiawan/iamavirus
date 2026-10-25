# Public standings and target-replica provenance

Snapshot: **October 25, 2026, 15:54 America/New_York**. Three paced public GETs
captured the leaderboard, our version list, and the newest 100 completed team
games. The one-shot monitor exited successfully; no watcher or arena write was
started. Raw response provenance is retained under `snapshots/20261025T195443Z/`.

## Current arena position

IAmAVirus is **1894.11 Elo, rank 9 among visible rated teams**, still on arena
**v35**. Its active-version record is 2,884 wins, 149 draws, and 2,698 losses
over 5,731 games. These are live-team observations, not results of Astra's
unsubmitted candidates or prepared training experiment.

| Rank | Team | Elo | Active version |
|---|---|---:|---:|
| 1 | Greek Gift | 2334.96 | 25 |
| 2 | Knight Vision | 2177.88 | 36 |
| 3 | Decent Chess Bot | 2112.57 | 7 |
| 4 | Strongly Invisible | 2105.54 | 37 |
| 5 | Crimson Fog | 2039.37 | 3 |
| 6 | Instructors | 1972.68 | 4 |
| 7 | duck | 1966.64 | 6 |
| 8 | Mist Opportunities | 1942.98 | 2 |
| 9 | IAmAVirus | 1894.11 | 35 |

The newest 100 games all used our v35 and span 10:04–15:52 Boston time. Record:
**50W–2D–48L (51% score)**. Selected opponent records in this chronological
sample are duck v6 **6W–4L**, Instructors v4 **5W–3L**, Crimson Fog v3 **1W–10L**,
Strongly Invisible v37 **1W–7L**, Decent Chess Bot v7 **1W–5L**, Knight Vision v36
**0W–1D–3L**, and Greek Gift v25 **0W–2L**. Small unequal samples do not establish
version improvements or separate opponent strength estimates.

The earlier morning report had us at approximately 1881 Elo/rank 10. No new
version explains this snapshot change; v35 remains active.

## What the PPO target replicas were trained to imitate

Both target replicas name dataset content digest
`5215c31612d70236d03983e50c663d9a8f6d28b669b5ef2d2c834963518dfac0`.
Reconstructing the dataset builder's interleaved content stream confirms that
digest against the actual v4 shards: **4,707 games / 9,414 episodes**. The audit
then applies each checkpoint's recorded player filter to the training split.

| Replica | Current opponent | Eligible training episodes by played version | Most recent dated training game |
|---|---|---|---|
| duck | v6 | 585 × v4; 38 × v5; 4 unknown | Oct. 7, 17:20 Boston |
| Instructors | v4 | 558 × v4 | Oct. 7, 17:23 Boston |

There are **zero explicitly labeled duck-v6 training episodes**, with four
unknown-version cases. Do not claim the Instructors version is obsolete: its
recorded version matches the currently active v4. Neither matching version
numbers nor absence of current-version examples measures actual imitation
fidelity; old patterns can generalize and same-version policies can still be
poorly approximated.

The selected checkpoints are the small `cnn64x4-gru256` models, not the 20.36M
learner: duck best is step 158 / epoch 2; Instructors best is step 70 / epoch 1.
Their checkpoint-recorded validation top-1 policy accuracies are approximately
42.5% and 32.2%, respectively, on their older validation procedure. Those are
not current-arena accuracy measurements or estimates of policy total variation.

Counts describe eligibility under the stored dataset/filter. They do not prove
that every episode was sampled or reconstruct unrecorded command-line limits.
The checkpoint hashes match the ones pinned for the proposed PPO comparison.

## Consequence for learning and evaluation

The fixed A/B comparison can still test whether risk supervision preserves or
improves the learner under a common league. Keep the two arms' league identical
to isolate that change. **A win against this duck replica is not evidence of a
win against current arena duck.** Crimson Fog, now rank 5, also has no replica
in the prepared `rl_l.yaml` league. The existing models may cover related
patterns, but that coverage is unmeasured.

For a fixed learner and the same initial-state/rules distribution, suppose an
opponent model q differs from the real policy p by at most epsilon in total
variation at every reachable history. Coupling their opponent decisions over
H turns gives a hypothetical terminal-return bound for rewards in [-1,1]:

\[
  |J(\pi,p)-J(\pi,q)|\le 2\min(1,H\epsilon).
\]

The reason is simple: the chance that the coupled games ever take different
actions is at most H epsilon, and terminal returns can differ by at most two.
This is not an estimated numerical error bar: we have **not measured epsilon**,
and top-1 imitation accuracy cannot be substituted for it. The bound explains
why optimizing a weak opponent model harder can fail to transfer over long
games.

Before interpreting league returns as a competitive advance, review current
version held-out move likelihood, hidden-attack coverage, and full games
against the actual C selector. This finding does not silently change the
frozen experiment, start replica retraining, or open another model sweep.
The training/scope decision requested in chatroom note 146 remains pending.

## Evidence

- [Captured latest summary](latest.json) and the timestamped snapshot directory
- [Checkpoint metadata and hashes](target-replica-provenance.json)
- [Verified dataset/version coverage](target-replica-data-audit.json)
- [Read-only reproducible audit](audit_replica_data.py)
- Public sources: [leaderboard](https://6s890.lids.mit.edu/api/leaderboard),
  [our versions](https://6s890.lids.mit.edu/api/leaderboard/a2c35173659545c99752376a70418438/versions),
  [our newest completed games](https://6s890.lids.mit.edu/api/games?player=a2c35173659545c99752376a70418438&sort=played&order=desc&limit=100).
