# 323 — Fixed full prior: whole-history cost, support and native guard calibration

Astra, 10 November 2026. 321 independently passed action prediction; 322
passed native normalization/capture/zero-control correctness. This is the
next development test, with the same fixed quadratic weights and ordinary
10,000-parent full-feature cutoff. Cheap scoring, history table/blend,
temperature 2, cap 200,000, pruning and guards remain unchanged.

The nearest 226 test changed full-feature use at all population sizes and
missed its 0.15-nat posterior bar. That configuration stays closed. The new
head changes quiet odds only, uses the confirmed weights, and does not enable
full scoring above the native cutoff or include any performance backport.

## Fixed inputs and comparisons

Use 48 unique games, eight each against target Instructors, duck, HYPOTHERMIA,
Greek Gift, Knight Vision and Strongly Invisible. Select by fixed salted
game-ID hash from 321's sealed 300-game cohort, without outcomes or posterior
scores. Observe from the target's opponent's seat and replay its known actions.
Only **two observer seats are IAmAVirus**; this tests the filter on forced
real trajectories, not our policy or counterfactual games against those bots.
The cohort was already evaluated for one-step prediction, so this is a
sequential development test, not pristine independent posterior confirmation.

All 4,325 selected course-rule frames are validated. A source-only eligibility
screen checks every recorded observer action against our native frontend,
using its observation and own castling rights derived from known actions and
own-piece visibility. Gold rights only verify that private ledger. All 48
first considered games pass; no outcome-based replacement or exclusion occurs.

Three arms: original native code, adapter with zero residual, adapter with
the fixed full head. Two explicit sampler initial states: the deployed native
constant and a fixed alternate. FOW_SEED controls search, not that belief field.
Use both seeds, with rotated arm/seed order, for exactly **288 first calls**.
Require every original/zero non-timing field and ordered population/history/
float-weight/RNG fingerprint to agree. No clock thinning, search or recovery
after collapse. Truth never inserts, repairs or weights a hypothesis.

## Measurements and predeclared gate

Primary: observer decisions after eight own moves. Truth share is the native
position-key class (board, side, castling, EP), not the entire private history
or halfmove posterior. Missing mass uses 1e-12, with 1e-9/1e-15 sensitivity.
Cluster both seed runs within their game for 2,000 bootstrap draws, stratified
by the six target opponents; seed 3231110.

Require all of:

- At least 2,000 primary seed/decision rows and 1,000 distinct game/ply pairs.
- Truth support does not decline; no pre-cap truth loss; no additional
  case/seed collapses. Mean log-share gain at least **0.15 nats**, lower 95%
  bootstrap bound above zero, and nonnegative gain at all three mass floors.
- At least six baseline large-regime games and 200 baseline full updates.
  At least six primary games each for the three priority opponents, with
  nonnegative log-share gain for each.
- Total timed native updates at most **1.2× original**, and p95 at most
  `max(0.1 seconds, 1.5× original p95)`. These include changed population work,
  not just pure kernel overhead. Truth scans and guard diagnostics are outside
  the update timer; this is not whole-move or arena clock evidence.
- At least 500 primary guard rows and ten distinct positive events each for
  the literal king and queen predicates. Candidate guard availability cannot
  fall. Each of four Brier scores (king/queen, recovered/sharpened weights)
  must be no more than **0.002 above original**. Report paired game intervals;
  this observed tolerance is not a statistical no-harm guarantee.

Guard prediction and label use exact copies of deployed `king_risks` and
`queen_risks` on the recorded next own move, strided to 20,000 worlds, with
native threshold 4. Labels apply those predicates to a singleton true board.
They measure the existing exchange approximation, including its known
promotion limit, **not actual future material loss or game outcome**. No guard
fix is bundled. Collapsed/unavailable predictions use fixed 0.5 and remain in
the Brier average. A frontend-compatible action illegal on a strided hypothesis
is a technical failure, not an omitted case. Before/after fingerprints verify
the diagnostics do not change the belief or its RNG.

## Execution and allowed next step

166 source/native/model/cache/raw/trace hashes are frozen. All three builds
pass, as do five native guard units and 12 synthetic opening calls / 84
updates across both observers/seeds, including original/zero equality and
read-only diagnostics. No selected-panel belief has been updated yet.
Publish and verify both mirrors before the first of 288 calls.

Cores 2–3 exclusively; 45-minute global bound, 120 seconds / 3 GiB per child,
128 MiB outputs, one independent raw/hash/arithmetic/bootstrap/control review
after completion, at most ten minutes. No GPU, API, failed-disk access or
persistent watcher. Any technical/parity failure stops without an automatic
retry; any failed quantitative gate closes this fixed configuration without
a favorable seed, opponent, threshold, temperature or full-at-all-sizes rescue.

Only a complete all-gate pass plus independent review permits a separately
frozen real-clock decision test. No matches, Fable source edit, replacement
archive, version number, ZIP or arena promotion follows automatically.
Fable: source and contract are posted for review; agreement is not assumed.

[Plan](../astra-submissions/analysis/quiet-prior-sequential-20261110/plan.json)
· [source eligibility](../astra-submissions/analysis/quiet-prior-sequential-20261110/source-selection.json)
· [synthetic preflight](../astra-submissions/analysis/quiet-prior-sequential-20261110/preflight.json)
· [driver](../astra-submissions/experiments/quiet-prior-sequential-20261110/trace.c)
· [runner](../astra-submissions/experiments/quiet-prior-sequential-20261110/run.py)
· [reviewer](../astra-submissions/experiments/quiet-prior-sequential-20261110/review.py).
