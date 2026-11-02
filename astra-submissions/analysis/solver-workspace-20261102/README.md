# Exact solver optimization: 1.121x faster on eight frozen search trees

2 November 2026. The implemented workspace/cache optimization preserves the
solver's results and improves measured solver speed. It misses the frozen
**1.20x** advancement condition, so no equal-clock policy run, full-game batch
or new release follows. Retain it as a reviewable engineering improvement;
do not claim a measured Elo gain.

| Actual v37 tree | Original / optimized solver time |
|---|---:|
| 4zy248z7, ply 16 | 1.163x |
| 807otaeb, ply 24 | 1.113x |
| jg8arl68, ply 35 | 1.082x |
| u66jmz73, ply 16 | 1.139x |
| e9ap0123, ply 48 | 1.121x |
| 465co8me, ply 26 | 1.119x |
| o3b5wvz1, ply 41 | 1.137x |
| axvqi3b1, ply 59 | 1.099x |
| **Geometric mean** | **1.12149x** |

Total measured solver time is 3.6590 versus 3.2675 seconds. Each row uses the
same immutable tree and starting regret arrays for both arms: 200 iterations,
five measured repetitions after one warmup pair, rotating timing order. Exact
regrets, predictions, weighted strategy sums and current strategies match at
every measured comparison. The tree remains fixed; this measures neither
allocation cost during growth nor complete move latency or playing strength.
The eight decisions were previously selected for belief-population cost in
experiment 227, not sampled to estimate population-wide speed.

## Implementation and correctness

The solver reuses its strategy/scratch arrays, grows storage geometrically,
and recalculates only the changed player's strategy after each alternating
update. Growth and pending initialization invalidate the cached strategy.
All current v37 callers were checked for direct writes to regret arrays;
none exist outside cfr.c. M4 or another client copying/mutating these arrays
would require a separate invalidation audit.

Native tests compare 6,263,272 doubles at 9,569 checkpoints over 8,193 updates,
bit-for-bit with original v37. Coverage includes shared infosets, both players,
unequal/zero chance probabilities, 257 actions, changing terminal values,
growing trees and pending initialization without growth. Host address,
undefined-behavior and leak sanitizers pass. A separate sanitized real-tree
load/solve test also passes.

The real-tree audit checks binary layout, all edges/action offsets, finite
solver arrays, hashes and lossless compression. All eight input reconstructions
pass hidden-field redaction tests. The course referee verifies 273 historical
frames and both observations, and all eight captured baseline moves are legal.
This is a cost experiment; there is no candidate move-quality comparison.

Geometric capacity retains extra memory. `tree-review.json` reports persistent
solver storage and iteration storage separately: the original solver adds two
temporary arrays during each iteration, whereas the new persistent count
already includes scratch. Do not compare those two different categories as
if they were peak process memory.

## Next algorithmic opportunity, measured but not implemented

A read-only follow-up counts the information sets reached in each player's
counterfactual traversal, plus unreached sets with a prior instantaneous
regret that must be cleared. At these saved profiles, the median required
action-slot fraction is **37.0%**, ranging from 22.2% to 60.4%.

That motivates investigating exact sparse regret/prediction updates instead
of sweeping every information set. It does not establish a speedup: tracking
the active set has a cost, player 1's profile changes after player 0 updates,
and weighted average strategies must still receive their correct accounting.
Skipping all unseen sets without clearing the previous prediction is wrong.
`activity.py` and `activity.json` preserve this exploratory evidence. It does
not reopen or change experiment 253's failed 1.20x advancement gate.

## Receipts and storage

Original collection **44709 exit 0**, independent audit **50241 exit 0**.
All eight capture/benchmark pairs completed on first attempts in 46.15 seconds.
Host process audit confirms no remaining owned jobs; cores 0–1 are released.
No GPU, fitting, model/guard change or arena operation occurred.

Preparation commit `f9c6e00909e309e6ee2590279840217a4dda763b` was verified on
both remotes before measurement. Plan hash:
`08d70e9e5d59d6ad83ad9640ca50c9d21c9d22d0184b4c5d52b114ced72382ad`.
Original v37 rebuild:
`14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`.
Optimized production binary:
`aae58d99224917d16280298be0ffed7c19ec80b68f89af405571450e55374eeb`.

The 35.6 MB raw trees and 5.05 MB compressed copies are on the external store
at `/media/henrytan/seagate/git/iamavirus-data/astra/solver-workspace-20261102/`.
They are not in Git; paths and hashes are in `receipt.json`. Source, patches,
inputs' provenance, capture output, native/sanitizer results and benchmark
receipts are committed. Recollection can produce different timed trees;
use the stored trees to reproduce this exact fixed-work comparison.
