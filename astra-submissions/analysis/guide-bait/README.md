# Hidden defended bait: first experiment

Requested by the user on October 7 after the Fog of War YouTube guide.
Fable owns the separate vision/scouting evaluation experiment. Astra owns
this search-candidate experiment. Neither relies on a claim that unseen
pieces cannot be inferred from history.

## Hypothesis and implementation

A search over one representative board can omit a quiet move that places a
cheap piece where an opponent can capture it, with a defender hidden in that
opponent's current view. We test whether admitting one such omitted move into
the root matrix improves the available tactical choices.

The variant is based on the immutable Astra archive SHA256
`a5f806d0039f514006f3af902767557ad35137d9d02e2779181d438eb5b47cf3`
(arena v11), not Fable's concurrently changing root engine. The published ZIP
is unchanged. Source construction is reproducible with `tools/build_bait_runtime.py`.

- `FOW_BAIT_ROWS=0` is the default. The first experimental arm sets it to 1.
- Rank excluded legal moves using 32 evenly spaced belief particles. This
  sample estimates opportunity; existing king safety still uses the full population.
- Only consider a move whose estimated immediate king risk is no greater than
  the safest move already retained. This is a belief comparison, not proof of safety.
- In each particle, identify either a king capture onto a square guarded only
  by hidden pieces, or a safe hidden recapture gaining at least 300 cp overall.
- Classify defenders using the opponent's view **before** committing the capture.
- Reject recaptures leaving our king attacked. Account for en passant and both
  players' promotions by comparing total material, not the promoted victim's value alone.
- Rank by fraction of particles offering king bait, then average best conditional
  material gain. This is a ranking heuristic, not a calibrated capture probability.
- Append at most one row in this arm. Existing search, policy, and defensive rows
  remain. All rows share the same total search-node budget.
- Apply no extra payoff bonus. The existing matrix/search/material/king-risk
  evaluation decides whether to play the admitted move.

The diagnostic computes the same geometry on the replay's true board **after
the actor chooses**. It records all-legal opportunity coverage before/after
admission and the chosen move's opportunity. No true board enters the actor.

## Gate fixed before examining the arm

1. Compile against the frozen engine and pass synthetic geometry tests covering
   both colors, visible/hidden defenders, unsafe recaptures, en passant, and promotion.
2. With the flag off, match the frozen release's choices on the existing five-game,
   40-decision parity fixture at 400,000 nodes/decision, hybrid model v1, seed 777.
3. Compare flag 0 versus 1 on the frozen latest-ten arena-v12 seats, own-decision
   stride 6 plus losing terminal decisions, same nodes/model/seed. These games
   are diagnostic data we have already examined, not an untouched holdout.
4. Stop this first arm if it creates any newly fatal decision, or changes no
   actions in the latest-ten fixture. Record a negative/null result without tuning
   the same positions to manufacture a pass.
5. Otherwise run the existing 37-seat Duck/TA-A/TA-S target gate. Report immediate
   king losses, newly fatal/safe decisions, material exposure, bait coverage, and
   chosen opportunities separately. None alone proves playing strength.
6. A release still needs correctness checks and subsequent color-swapped 180+2
   play. The active arena-v10 reference is separate from the feature-isolation
   baseline (arena v11); eventual promotion must compare against active v10 too.

No node-limited comparison made while sharing CPU cores will be cited as runtime
throughput or clock-cost evidence. The queue waits for Fable's real-clock matches
on cores 2–3 before building/testing. The GPU service is untouched.

## First result — mostly neutral; keep default off

Completed 21:30:46 UTC. Native geometry/admission checks: **48 passed**. Default-off
parity: **40/40 identical choices** versus the frozen release. Experimental binary
SHA256: `0f2908c7610f14a4af52ae2d19cfb83e873fdf69d5d09a9e128c8d78e8dba125`.

| Fixed-node fixture | Decisions | Changed choices | Immediate king losses, off → on | ≥300 cp material exposure on nonfatal decisions | Chosen profitable bait opportunities |
|---|---:|---:|---:|---:|---:|
| Latest ten arena-v12 seats | 72 | 3 | 3 → 3 | 1 → 1 of 69 | 23 → 23 |
| Historical Duck/TA-A/TA-S seats | 274 | 8 | 20 → 20 | 12 → 11 of 254 | 66 → 67 |

There were **zero newly fatal and zero newly saved decisions** in either fixture.
The historical material improvement is one changed choice, `4x4pomtj`, White,
pre-move ply 36: Ra1-d1 (335 cp exposure) → Ba7-e3 (0 cp). This is one label
improvement, not a robust material or strength estimate. Mean exposure rose
23.33 → 23.62 cp on the latest-ten fixture and fell 41.36 → 40.04 on the historical
fixture. Chosen king-bait opportunities stayed 0 and 1, respectively.

Admission found many opportunities but rarely changed behavior: one row was
added on 43/72 and 163/274 decisions. Of these 206 added rows, 96 had bait geometry
on the true board (21 + 75), increasing coverage from 897 to 993 of 2,271 legal
truth-board bait moves. A move can preserve an existing bait opportunity; this
label does not prove it *created* a new trap. Uncertain particles also nominate
bait absent on the true board. These limitations make reply modeling and belief
quality more useful next steps than increasing a raw feature bonus.

Changing the number of rows also changes search depth per cell and the matrix
mixture. The current logs do not distinguish selecting the added row from a
different choice among existing rows; the 11 changed decisions cannot all be
credited to playing bait. Nothing here measures the opponent's willingness to
take a sacrifice or its subsequent response. The oracle labels do not prove
that the two-ply material gain survives a longer exchange.
These are local capture-geometry labels with an immediate king-safety check;
they do not reconstruct repetition histories or certify that play continues
past a draw condition. A deployable bait policy needs that terminal handling too.

**Decision:** preserve the implementation and negative/null evidence; do not
enable by default or package a new release on this result. Keep active arena
v10 as requested. Return priority to continuation/persistence and the visible
queen/pawn failure. A future offensive arm should distinguish newly created
opportunities and estimate acceptance from actor-visible history before spending
real-clock gates on it. No real-clock bait match was run in this first experiment.

## Evidence locations

- `run-v1/state.json`: live phase and any error; prepared/queued does not mean tested.
- `build/v1/integration-manifest.json`: immutable basis and source hashes (build output ignored by Git).
- `build/v1/test.log`: native check result, once run.
- `run-v1/off-parity/`: flag-off comparison.
- `run-v1/latest-ten/`: first causal replay comparison.
- `run-v1/historical-targets/`: conditional second gate, only if reached.
- `latest-ten-seats.txt`: frozen ten-game forced histories.

Do not upload this staging directory as a submission or describe it as an Elo gain.
