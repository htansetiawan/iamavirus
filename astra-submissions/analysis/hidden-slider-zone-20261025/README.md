# Hidden slider king-zone feature

**Status: research only; no arena release.** This note records a fitted
opponent-move prior feature and its current gates. The feature is a hidden
bishop, rook, or queen destination whose attack map reaches a square adjacent
to the enemy king, whether or not it gives check.

## Fitting evidence

The candidate adds move-model feature 28 to the v35 full and cheap priors.
The 91 target games used for the replay-choice gate were excluded from fitting;
the dataset contains 5,889 games and 59,100 positions, with a game-disjoint
chronological test split of 1,178 games / 11,913 positions. Dataset SHA-256:
`7337fe955a60eb0f1aac6ace120556e1b4e336e284b79398d61a4dca1fa163ae`.

On the held-out test positions, the full prior's NLL changes from 2.64202 to
2.64164 (delta -0.000384); top-1 changes from 26.31% to 26.37%. On the subset
where the true move activates the new feature (n=1,034), NLL changes from
2.51637 to 2.47718 and top-1 from 29.30% to 30.75%.

The cheap prior changes overall held-out NLL from 2.81434 to 2.80256 and top-1
from 23.48% to 23.86%. These are opponent-action prediction metrics, not move
quality or Elo evidence. Exact fitting outputs are in
`exclude-hidden91-fit-report.json` and `exclude-hidden91-cheap-fit-report.json`.

## Replay-choice gates

The frozen v35 binary SHA-256 is
`f8ef3027756da506d7b367e22ff93ec4cb17bd912eca68c4bfaa8fda5bc028ff`; the
candidate binary SHA-256 is
`43125879c397f875d1f69838eaa35bacf82a2b10381349ef007beb68bdedd7f9`.
Both were run at five seconds per decision on the same recorded observations.

| Set | Cases | Changed choice | v35 fatal | Candidate fatal | Saved | Introduced |
|---|---:|---:|---:|---:|---:|---:|
| Selected hidden-arrival losses | 91 | 39 | 84 | 81 | 8 | 5 |
| Of those, belief <=10k | 64 | 23 | 60 | 60 | 4 | 4 |
| Of those, belief >10k | 27 | 16 | 24 | 21 | 4 | 1 |
| Nonfatal king-move controls | 12 | 3 | 0 | 0 | 0 | 0 |

The apparent safety improvement is concentrated in the cheap-prior branch
(beliefs above 10k); the full-prior branch is even on this selected fatality
metric. The 12 controls are a small curated set against Decent Chess Bot,
Strongly Invisible, and duck. They did not expose an immediate-fatal
regression, but they are not enough to establish general non-regression.

These probes replay decisions from the true historical board state while the
bot itself receives only its recorded observations. They measure immediate
king fatality against the recorded truth, not what would happen after the
candidate's changed move against a responding opponent. The loss cases are
selected, not representative, and the safe-control set is small.

## Full-clock gate

The eight-game, color-swapped local v35 comparison at 180+2 finished with
candidate score **3.5/8 (0.4375)**. Pair scores were 0.75, 0, 0.5, and 0.5.
The candidate scored 1/4 as White (one win, three losses) and 2.5/4 as Black
(two wins, one draw, one loss). These four pairs are a small local screen, not
an Elo estimate, but the score is below even and does not support promotion.
Complete game records, seeds, replay hashes, and clocks are in
`fullclock-selfplay-4pairs.json` and the eight referenced replay files.

The candidate lost four games. Replaying each terminal decision from its exact
prefix with both binaries at five seconds produced the **same fatal move** for
v35 and the candidate in all four cases. Two true positions had no immediately
safe move; two had a safe alternative. The feature therefore did not change
the relevant defensive choices in any of these full-game losses. See
`fullclock-loss-postmortem.json`.

## Reproduction

Build the research candidate from the immutable v35 archive:

```sh
.venv/bin/python astra-submissions/tools/build_hidden_slider_zone_candidate.py \
  fable-submissions/iamavirus-v35-mist-c-v14.zip \
  --full-fit-report astra-submissions/analysis/hidden-slider-zone-20261025/exclude-hidden91-fit-report.json \
  --cheap-fit-report astra-submissions/analysis/hidden-slider-zone-20261025/exclude-hidden91-cheap-fit-report.json \
  --dataset-sha256 7337fe955a60eb0f1aac6ace120556e1b4e336e284b79398d61a4dca1fa163ae \
  --output /tmp/iamavirus-v35-hidden-slider-zone-exclude91-cheap-v2
```

The loss and safe-control reports are
`exclude-hidden91-prefixes-fullcheap-5s.json` and `safe-controls-5s.json`;
their source case manifests are `hidden-arrival-cases-ply70.json` in the
standing-trend folder and `hidden-slider-zone-safe-controls.json` in this
folder. C semantic fixtures are in
`astra-submissions/tools/test_hidden_slider_zone.c`.

## Promotion decision

Do not package this as v36. The predictive gain is small overall, the loss-set
fatality gain is only 3/91 net and includes five introduced fatal choices, and
the 8-game full-clock score is 0.4375. Although the 12 safe controls showed
no immediate-fatal move, the terminal-loss postmortem found no changed choice
in any of the candidate's four losses. Keep the archived feature as a rejected
research experiment. The next useful test should connect newly hidden slider
arrival evidence to the defender's king-risk decision, rather than only
changing the opponent move likelihood. The separate Astra v36 archive changes
only the king-guard default; it does not include this rejected hidden-slider
feature. Follow its evidence at `astra-submissions/v36-kingguard0001.md`.

## Census of newly created hidden king attacks

Added 2026-10-25 for the DeepRL/tree review. The reusable scanner is
[`scan_hidden_king_arrivals.py`](scan_hidden_king_arrivals.py). It compares
each replay's true board before and after every move. An event qualifies when
the victim king was not attacked before the move and is attacked afterward.
Attacking pieces are classified using the victim's observation in that frame:
fully hidden means all attacking pieces are on `?` squares; visible means none
are hidden; mixed events are kept separate. The recorded next move is then
checked to see whether the same king remains attacked. The scan does not model
counterfactual best replies.

### Result

On 123,251 cached games matching the top-team name filter, the scan found
326,940 new direct king attacks. Among events with a recorded defender reply:

| Attack visibility | Still attacks after reply | Answered events | Rate |
|---|---:|---:|---:|
| Fully hidden | 50,802 | 144,766 | 35.1% |
| Visible | 22,568 | 174,151 | 13.0% |
| Mixed | 265 | 766 | 34.6% |

The hidden-visible difference is +22.1 percentage points, game-clustered
approximate 95% interval [+21.8, +22.4] across 112,148 games with at least one
classified event. By top attacker:

| Attacker | Hidden | Visible |
|---|---:|---:|
| Greek Gift | 31.6% (3,885/12,312) | 15.2% (1,826/12,032) |
| Instructors | 39.7% (10,780/27,186) | 13.9% (4,282/30,880) |
| Knight Vision | 30.0% (5,583/18,586) | 11.4% (1,895/16,573) |
| Decent Chess Bot | 31.8% (3,618/11,366) | 15.3% (1,731/11,346) |
| Strongly Invisible | 37.5% (10,991/29,337) | 18.2% (5,888/32,388) |
| duck | 33.6% (2,807/8,350) | 12.5% (1,140/9,093) |

This is descriptive association, not causal effect or Elo. The interval accounts
for repeated events within a game, not selection into this cached corpus,
opportunity mix, team strength, or correlated strategies. Events without a
recorded reply are excluded. The output event file is
[`top-opponents-hidden-king-arrivals.jsonl.gz`](top-opponents-hidden-king-arrivals.jsonl.gz);
the aggregate report is
[`top-opponents-hidden-king-arrivals-summary.json`](top-opponents-hidden-king-arrivals-summary.json).

### Reproduction

From the repository root, make the top-team replay list and run on one core:

```sh
rg -l --no-messages --glob replay.json '"(white|black)"\s*:\s*"(Greek Gift|Instructors|Knight Vision|Decent Chess Bot|Strongly Invisible|duck|TA Baseline [ASP])([[:space:]]+v[0-9]+)?"' data/raw/games > /tmp/iamavirus-top-replays.txt
taskset -c 0 python3 astra-submissions/analysis/hidden-slider-zone-20261025/scan_hidden_king_arrivals.py \
  --path-list /tmp/iamavirus-top-replays.txt \
  --events astra-submissions/analysis/hidden-slider-zone-20261025/top-opponents-hidden-king-arrivals.jsonl.gz \
  --summary astra-submissions/analysis/hidden-slider-zone-20261025/top-opponents-hidden-king-arrivals-summary.json
```

The attack detector has basic rook/pawn/color fixtures, but it has not yet been
differentially validated against the referee across a frozen replay sample.
That independent check is a required next gate before fitting a training
feature from these labels.
