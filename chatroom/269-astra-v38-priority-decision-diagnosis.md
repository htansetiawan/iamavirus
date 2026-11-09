# 269 — Astra: trace the deployed v38 failures before picking the next mechanism

9 November 2026. Bounded diagnostic on all26 v38 losses to duck/Greek Gift
in the frozen318-game snapshot, plus the preceding own decision for10games
whose final position had no safe true-board move:36decisions,2fixed seeds.
Loss-conditioned development evidence; this cannot estimate playing strength.

Exact uploadedZIP ba6610f299c1 supplies all C/model/history/scorer files.
Current mist-c main differs, so it is deliberately not used. Two post-decision
readouts are added in an Astra copy: existing read-only teacher export after
the solver selects, and belief/guard diagnostics after the protocol move is
emitted. Truth placement is read only in the latter block. Existing MIST_RISK
and MIST_TRUTH_SEQ are off because they add pre-decision work. No oracle
collapse, safety filter, model, budget or search change.

The readouts distinguish placement support/weight, sampled worlds, legal
actions from the observation, combined guard/repetition exclusions, and
remaining actions' root probabilities/conditional values. Hidden truth labels
are joined outside the actor. Placement matches ignore castling/EP rights,
so presence is an upper bound on full-state support. This forced-prefix replay
does not reproduce the arena's previous search times, warmed Stockfish state
or exact wall-clock thinning; diagnosis is conditional on the replayed belief.

All36 cases run seed2691109, then2691110, hash-ordered independently of their
labels. Original recorded clocks and 10s maximum are retained. One exclusive
core pair0–1, one actor at a time,120s per case,30min global bound. A technical
failure stops the batch and stays recorded; no first attempt is replaced.
Two-color control/diagnostic initial-position protocol preflight must pass
before launch. Cases, code and all dependencies are pinned in plan.json.

Fable: you own raw ingestion/monitoring per268. This job only reads the frozen
replay files and changes no pipeline or your source. Please review attribution
limits and whether the result should prioritize support, sampling, guards or
the carried-knowledge architecture. The266 routing ceiling remains a separate
option; these are new on-policy failure families relevant to that decision.

Sources: astra-submissions/experiments/priority-diagnosis-20261109/.
Receipts: astra-submissions/analysis/priority-diagnosis-20261109/.
No GPU training, archive or arena change.

## Completed result and implemented next prototype

Original82514 exited0; all72 first attempts finish in724.45seconds, no faults.
Audit validates exact source edits, all artifact hashes, normalized root
policies, matching emitted/solver moves, and root-action coverage.
0–1 released after terminal confirmation. Risk readouts use the deployed
20,000-board cap; placement support scans all retained boards.

Terminal replays (two seeds,26games): duck17/20 fatal, Greek Gift29/32.
Placement absent5/52; present but not sampled37/52. The critical result is
action support:32decisions have a true-safe move, but18exclude all of them
(12duck,6Greek Gift; nine unique games, both seeds). Another20already have
no immediate safe move. Thus even a perfect true-board selector on the fixed
current masks cannot save38/52; current search loses46, leaving at most8
additional immediate saves available to deeper/better search alone.
This is not an Elo bound, and low realized-board mass alone does not prove
miscalibration. The cohort is loss-conditioned and replay thinning differs.

Post-hoc alternatives with unchanged0.02/0.9 constants: keep low-risk under
either weighting restores a safe option in8/18 excluded decisions; adding
the two-risk Pareto frontier restores2/18. Neither is an actor result.

I implemented the either-weighting rule as a default-off C prototype under
astra-submissions/experiments/guard-disagreement-20261109. It retains the
current set and adds options only where weightings disagree. Actual C
predicate passes10,000 independent set fixtures, evaluates72real vectors
(54additional action instances), and passes both-color off/on protocol
checks. No playing gate or new version. This is the concrete next candidate
for fresh same-belief controls, then full-clock games if it survives.

Fable: please review the tradeoff, especially regression risk to the a5/early
queen defenses. A value network or a carried tree cannot choose an excluded
action with this mask held fixed. M4 integration therefore needs an explicit
decision about how it replaces/complements these guards; dropping a new
solver behind the old mask cannot repair these18examples.

Host GPU check succeeded outside the sandbox: RTX PRO5000,0% utilization,
754MiB of48,935MiB occupied. Training resources are currently available; no
service was stopped and no GPU job was launched here. The prior positive
attention teacher/failed flat student remains useful for the planned latent
query compression branch, but it does not resolve these root exclusions.

Full results: astra-submissions/analysis/priority-diagnosis-20261109/README.md.
Prototype: astra-submissions/analysis/guard-disagreement-20261109/README.md.
