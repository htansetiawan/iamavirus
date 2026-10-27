# v36 decision contract

Agreed planning contract, 26 October 2026 PDT / 27 October UTC. Astra owns this
document; Fable's explicit ACK of the numeric gates is appended to
[note 164](../../../chatroom/164-fable-v36-analysis-and-plan.md). The human-facing
recommendation is [docs/v36-plan.md](../../../docs/v36-plan.md).

**Execution update, October 27 UTC:** Henry moved this reviewed plan into
execution; Fable and Astra are carrying out their assigned steps. See
[note 166](../../../chatroom/166-astra-v36-execution.md). The numerical gates,
cutoffs and deadline below are unchanged. The planning-only language records
the original freeze, not a new approval requirement.

This is an evaluation and release plan, not a passed gate or an arena upload.
The earlier local bench was already authorized and is now stopped because its
candidate was superseded after source review. No further experiment is launched
by publishing this document. Henry's requested committee review remains the next
planning checkpoint. There is one candidate design, B2 plus the required fallback
correction, and no automatic behavior fallback or next-version reservation.

## 1. Candidate identity and mechanism

| Role | Artifact | Source | SHA-256 prefix |
| --- | --- | --- | --- |
| Superseded pre-correction candidate | `data/candidates/iamavirus-v36-candidate-mist-c-v20.zip` | mist-c `be26b1a` | `49f65e1d93e5` |
| Corrected candidate, not benched | `data/candidates/iamavirus-v36-candidate-mist-c-v20-r2.zip` | mist-c `a71035e` | `b2a2000c48da` |
| Baseline | `fable-submissions/iamavirus-v35-mist-c-v14.zip` | mist-c `97b60f1` | `24791ca64a42` |
| Local opponent wrapper | `data/zoo/misty-v16.zip` | installed Misty package, distinct from our engine | `62d8d389c2ed` |

[artifacts.json](artifacts.json) records full hashes, source revisions, queue
contents and ZIP-member hashes. Candidate and baseline use identical Stockfish
19 and history-table bytes. The B2 replay source was `7cf0727` with
`MIST_PIECE_GUARD=0.758`; `be26b1a` makes that same value the default. Candidate
`run.sh` requires no local bench environment to activate B2.

Fable has separately corrected the two fallback paths in `a71035e`, with
both-color helper unit tests. Finish the remaining guard-rule tests before
freezing the final artifact (planned label r3). That final hash, executable and
queue are not yet available. Earlier replay results and three stopped-bench
games do not certify the corrected or final artifact.

The opponent ZIP is a small wrapper, **not a complete frozen opponent**. Its
external virtual environment contains `misty-chess 0.1.3`; it uses an external
Stockfish binary. [opponent-environment.json](opponent-environment.json) pins
package contents and that binary. No Misty engine source was inspected for this
review. Keep the environment unchanged throughout both matched arms; record the
interpreter, transitive runtime dependencies and effective settings in the bench
receipt. An arena team name does not establish equivalence to this local build.

For each available move, estimate king-loss risk K, queen-loss risk Q, and
rook/minor-loss risk P over at most 20,000 strided belief boards. P counts an
immediate opponent capture losing at least three pawns net, excluding worlds
already charged to K or Q. The guard uses both the fitted and sharpened weights.

First apply v35's rule to `K + 0.9 Q`, giving S35. Then, **only among S35**, apply
the existing margin/fallback rule to `K + 0.9 Q + 0.758 P`. This gives S36, a
subset of S35 at this filter. Freeze lambda 0.758, threshold 3, margin 0.02,
32 root draws, belief cap, history/move models, Stockfish depth, search policy
and clock policy. Old uniform/material/fog-hazard experiments remain disabled.

The coefficient is fitted from observational game cohorts. It is not a causal
loss probability, an equilibrium guarantee or a learned replacement for search.

## 2. Gate 1: correctness, effective settings and timing

Fable implements and runs the targeted checks; Astra independently reviews the
results. Existing legality tests do not by themselves test this new risk policy.
The correction's [test receipt](../../../fable-submissions/analysis/v20-material-guard-20261027/gate1-receipt-a71035e.md)
records a successful `make test` for `a71035e`, including the new both-color
fallback helpers. It is not a final release receipt. Fable's bounded next step
is a behavior-preserving extraction of the risk-array rule into a callable
function and targeted rule tests, estimated at two hours, then one final artifact
freeze. If that scope expands, report the blocker instead of adding a redesign.

- Reproduce the three recorded B1 fatal counterexamples as regressions. Cover
  both colors, king/queen/piece event disjointness, immediate king capture,
  promotion and en-passant accounting where relevant to the risk routines.
- Check fixed-belief risk values, empty-intersection fallback and filter
  membership against v35. With the piece term disabled, preserve v35 risk
  exclusions; do not demand identical wall-clock search trajectories.
- **Check the move actually emitted.** In the superseded source, `gtcfr_decide` restores
  every root move if repetition plus risk exclusions remove them all. The final
  `front_best_allowed` legality fallback also ignores risk exclusions. Example:
  available `{a,b,c}`, S35 `{a,b}`, repetition excludes `{a}`, B2 keeps `{a}`;
  the combined exclusion can restore `c`, whereas v35 could still play `b`.
  The subset proof for the local risk filter does not protect this path. Cover
  this interaction and fallback legality before release. Commit `a71035e`
  corrects the main path by giving risk exclusions priority over repetition and
  respecting exclusions in the legality fallback when alternatives remain.
  Review the integration as well as the helper tests. This behavior correction
  requires a new artifact and its gates within the same deadline.
- Check the exact ZIP builds under the supported toolchain/fallbacks, completes
  initialization within the arena limit and plays legal games as both colors.
  Record build command and executable hash. Source hashes alone are insufficient.
- Record effective `MIST_*` and `FOW_*` settings, with no unrelated environment
  secrets. Source reads `MIST_ITERS` only when `MIST_ASYNC` is active. Neither
  enabling async nor changing iterations belongs to B2. Fable confirmed async is
  unset in the replays, bench and launcher: the active round loop uses ten
  iterations per up to 32 expansions. The baseline and candidate must retain
  that same search mode.
- Measure complete turn cost, including belief updates and all guards. The
  current search allowance is computed before guards; nominal search seconds
  are not the turn's wall time. Fable's existing profile reports about 5 ms
  typical extra piece-guard cost and 1.1 s at 200,000 boards; these are profile
  observations, not a guaranteed overhead bound. Full-game clocks are decisive.

## 3. Gate 2: fresh confirmation decisions

Freeze and commit the selected IDs and selection-code hash **before running
either replay arm**. Window: game completion strictly after
`2026-10-26T10:12:00Z` and before `2026-10-27T11:30:00Z`. A late ingest must not
extend that endpoint. Cohort: IAmAVirus v35 against Greek Gift, Knight Vision,
Strongly Invisible, Decent Chess Bot, duck, Instructors and Crimson Fog, with
played opponent versions retained in the manifest.

Exclude the union of game IDs in all four previous sets. Exclude exact duplicate
full move trajectories across old and new data; within the new window retain
the earliest `(completion timestamp, game ID)` per trajectory. Correlated
decisions from one remaining game stay together when estimating uncertainty.

Use the existing `build_split.py` decision definitions, with the new explicit
window/cohort/dedup arguments. Take the first eligible clean rook/minor loss in
each lost game, pre-move material lead at least −3, nonfatal recorded move and
available truth. Select ordinary win/draw decisions and ordinary pre-material-
event loss decisions separately: from decision six, spaced by at least four
decisions, at most three per game. Keep chronological selection and the existing
deterministic loss-game subsampling; cap each control group at 100 decisions.
Do not select on candidate outputs. Report omissions and coverage by color,
opponent/version and game phase.

Minimum sample: 80 failure decisions, 50 win/draw controls and 50 loss controls.
Use A = B2 source with piece guard disabled; B = same source/default B2, with
identical Stockfish/history and effective search settings. The later local games
compare against the actual immutable v35 ZIP. Replay at 2.5 s, seed 1, one lane
per reserved core pair, after the full-game bench. Compare jointly scored CP
losses only; require at least 80% jointly scored in each group and report why
the remainder are missing. Protocol/runtime errors must be investigated, not
dropped from denominators.

Every condition below is required:

| Cohort | Required direction/bound |
| --- | --- |
| Failure decisions | Paired mean CP loss B − A < 0; recorded-losing-move repeat rate B − A ≤ −0.08 |
| Each ordinary control group | Paired mean CP loss B − A ≤ +10 cp; piece-only veto of the recorded move on ≤ 8% of decisions |
| All three groups | Zero new fatal decisions: no B-fatal/A-nonfatal case when a safe legal move exists |

Missing minimum sample, insufficient paired scoring or incomplete replay arms
means **incomplete**, not pass. A numerical criterion failing means reject.
Report game-cluster uncertainty; these are direction/regression screens, not
statistical proof of a win-rate gain. No coefficient sweep, new threshold or
additional data window after seeing the result.

The four existing sets are development evidence because B2 was revised after
observing B1's failures in the later loss set. They do not become untouched
confirmation again by renaming them.

## 4. Gate 3: full-game regression and direction screen

The earlier `queue-v36c.json` started at `2026-10-27T00:24:22Z` and was stopped
around 00:40 UTC after the fallback correction superseded its bytes. Three games
remain as diagnostics, not a completed gate. Preserve that queue, results and
artifact. **No replacement bench is running.**

After plan review and the final artifact freeze, create a new queue/matchup ID
set referencing the final ZIP. Pin it before launch; never merge the three old
games into its totals. Use the allocations and seeds below, two lanes on cores
2–3 and 4–5, the course referee at 180+2, no GPU, and a **12-hour hard cap from
the logged launch time**. Target launch by October 27, 20:00 UTC, to finish by
October 28, 08:00 UTC; elapsed time does not approve a launch. If review or
correctness blocks this schedule, report incomplete at the checkpoint, without
moving the October 29 release decision deadline. Freeze the queue during the run.

| Matchup | Games | Pair seeds |
| --- | --- | --- |
| B2 vs immutable v35 | 40, 20 per color | `200000 + 2*pair`, pair 0–19 |
| B2 vs frozen local Misty | 32, 16 per color | `201000 + 2*pair`, pair 0–15 |
| v35 vs the same Misty | 32, same colors | same 16 seeds |

Both color-swapped games use their pair's seed parameter; the harness assigns
the White bot that seed and the Black bot seed + 1. Use the earlier queue's very
small SPRT alpha/beta to disable early stopping; this is a **fixed 104-game
screen**, not a claimed SPRT acceptance. Matched Misty estimates use complete
four-game blocks: two candidate and two baseline games for each seed.

Let H be B2's points in its 40 games against v35; M and B be B2's and v35's
points in their 32 Misty games. Draws count half. Require:

- H ≥ 18, with at least 7/20 points in each color.
- M − B ≥ −4.
- **D = 0.5 × ((H/40 − 0.5) + (M − B)/32) > 0.** This equally weights two
  comparison tasks to require positive overall direction. It is a screening
  statistic, not an Elo estimator or a confidence bound.
- Zero attributable crashes, illegal moves or time forfeits. Every B2 end
  clock ≥ 10 s; median end clock no more than 10 s below the v35 comparator,
  reported separately for direct games and matched Misty games. Inspect every
  move's clocks too; a final clock can hide a transient low clock.

Report W/D/L and paired uncertainty by color and opponent, piece-loss events,
fatal outcomes, runtime and remaining clocks. A mechanism change is useful
explanation, not permission to override a failed score or reliability gate.

Reconcile all 104 expected `(matchup,pair,color)` jobs against stdout, replay
files and result rows. `arena_local.py` currently skips unrecognized result
strings, so ledger absence cannot be treated as a successful or unplayed job.
Attributable failures count as losses and reject. Infrastructure-invalid or
unfinished jobs and their partial blocks stay in the record; missing required
totals makes the gate incomplete. No selective retries or invisible replacement
seeds. Stop at the cap and report what completed.

If B2 fails for strength, stop and return to the committee. If it fails **only**
on timing, one guard-fusion change may be considered, with fixed-work identical
risk arrays and exclusions, a new hash, and its own clock/playing gate before
the unchanged release deadline. Faster fixed-work semantics can still alter a
wall-clock search; replay equivalence alone cannot establish equal strength.

## 5. Release and arena evidence

All preceding gates must pass on the proposed release. Fable packages; Astra
audits the receipt. A result belongs to its bytes, source, environment and
dataset. Do not transfer a pass to a silently rebuilt or revised candidate.

The old `iamavirus-v36-kingguard0001.zip` is withdrawn, not overwritten. The
authoritative map is `fable-submissions/README.md`. Check the live version list
before upload: 36 is the expected next arena number; engine v20 and archive
aliases are separate labels. Henry receives the exact ZIP, full hash, source,
effective settings, validation report, prediction and rollback rule to submit.

Freeze the v35 arena reference from October 20–26 before viewing v36 results.
For each v36 opponent-version/color stratum with baseline support, compare its
points with v35's mean score in that same stratum. Report the supported subset
and missing strata separately; do not invent a baseline for a newly updated
opponent. Bootstrap candidate games and baseline games within strata to include
uncertainty from both sides. Report first clean rook/minor-loss incidence,
king losses and clock failures alongside score. Do not convert replay CP gains
into a promised Elo gain.

Review reliability at 20 games; any attributable crash, illegal move or time
forfeit triggers a rollback recommendation. At 100 and 200 games, review the
schedule-adjusted score and uncertainty. Recommend rollback for strength if
the upper end of its 95% interval is below zero relative to v35; an interval
spanning zero is **unresolved**, not an improvement claim. Every 24 hours,
deliver a human-readable checkpoint even if a target game count is not reached.

## 6. Owners and deadline

Fable: source changes if required, fresh-set construction, reserved local runs,
runtime receipt and ZIP. Astra: independent source/artifact review, manifest
audit, paired analysis and decision write-up. Henry: plan review, committee
decisions and arena submission. Do not launch overlapping copies of a gate.

- **October 27, 20:00 UTC / 1 pm PDT:** first committee report, fresh manifest,
  local-screen status or explicit incomplete status, correctness blockers.
- **October 28, 20:00 UTC / 1 pm PDT:** confirmation/local evidence or rejection.
- **October 29, 20:00 UTC / 1 pm PDT:** submit-ready artifact and evidence, or
  documented rejection/incomplete result. No silent extension.

Deferred hypotheses—solver convergence/allocation, history-preserving belief,
restricted mixing, common-knowledge subgames, in-process evaluation and learned
Fog of War values—are not automatically scheduled by this plan. A new experiment
requires a new committee decision based on what v36 taught us.
