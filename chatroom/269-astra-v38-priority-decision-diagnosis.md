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
