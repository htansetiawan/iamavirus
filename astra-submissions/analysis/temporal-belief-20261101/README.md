# Temporal context did not improve this capped belief

1 November 2026. **Do not advance this implementation to a release or full-game
trial.** The preceding temporal predictor's held-out likelihood improvement did
not transfer to this small posterior screen. The original run also contains an
unresolved process crash. Neither result is hidden by diagnostic completion.

## What was compared

18 new games, nine opponent teams with both observer colours, 651 decisions.
Selection did not use outcomes. Every observer is IAmAVirus. The three arms
share a 20,000-entry cap, seed, temperature 2, full fitted features and no
empirical history table. Earlier experimental games were excluded. This is
a fixed-cap mechanism test, not a comparison with the deployed v35 policy.

Each hypothesis carries recent opponent-action context generated from that
hypothesis's transitions. The update API receives only own views and own
moves. True boards are read by separate const diagnostics afterward. The
private-input pilot verified identical state/RNG checksums and risks with
truth labels redacted. Optimized and ASan/UBSan small-state oracle checks passed.

| Arm | True board present | Mean truth-board NLL (lower is better) | Mean distinct boards |
|---|---:|---:|---:|
| Static model, merge equal boards | 578/651 (88.79%) | 7.36170 | 3,730 |
| Static model, retain distinct recent contexts | 558/651 (85.71%) | 7.79886 | 2,039 |
| Temporal model, retain distinct recent contexts | 550/651 (84.49%) | 8.17962 | 2,015 |

NLL clips zero probabilities at 1e-12. The ordering is unchanged at 1e-9 or
1e-15. Temporal loses 4.30 percentage points of truth support against the
board-merged control, and fails the NLL criterion against both controls.
Excluding the entire game whose process failed leaves the same conclusion.

The common nonempty-risk panel contains 619 decisions but only three actual
king-loss events. Brier scores are 0.004448, 0.004445 and 0.004685 respectively.
This is too little event coverage to validate king safety. It says nothing
about queen guards or new policy choices. Risk is measured for the recorded
own move, not a newly selected move.

Summed update times are 14.38, 15.84 and 15.19 seconds. Empty-belief decisions
number 26, 14 and 32. This experiment does not rebuild after emptiness, so
later planned decisions remain in the support/NLL denominators; runtime can
also fall after collapse. These times are not a general speed claim.

## Runtime failure and provenance

The original `pins.json` remains **failed**: `ze9rzvsl/static_context` exited
with SIGSEGV (-11) after 39 successful cells. It had written a complete output
with all 40 decisions. That original output was retained. The trace frees the
native belief before writing JSON, so the failure occurred after output was
written; this does not establish where the underlying fault originated.

One sanitized replay and 13 optimized diagnostic repeats succeeded. Every
optimized repeat has the original posterior checksums. The fault has **not**
been reproduced or fixed. `diagnostic-completion.json` records that failure
and completes the 14 genuinely missing cells once each. There are 54 retained
first outputs, 53 successful original/completion exits and one failed exit.
Retries are not substituted into the result table.

`summary.json` verifies all 54 output hashes, original source/plan pins,
input/truth hashes, decision alignment, labels, cap and seed. Independent
aggregation reproduces the table. Library SHA-256:
`38a53ba1a7abb3a5a382667301bfca48694ae19c5e424a92494c0626ed130062`.

## What this teaches us

The static-context control already loses support: carrying multiple context
histories as separate full-board entries consumes the cap. This is consistent
with a representation/diversity cost; it is not proof that this is the only
cause. The temporal model then worsens NLL further in the same representation.
Better predictions conditional on the true parent do not guarantee better
inference after repeated resampling over uncertain histories.

A different design worth reviewing is one stored physical board with a small
weighted mixture of recent contexts. Move probability would marginalize over
that mixture, and the cap would apply to physical boards. This would avoid
duplicating each board for every history, but requires its own correctness,
resource and held-out posterior tests. It is **not implemented or validated**
here. No retuning on these 18 games, new ZIP, live change or Elo claim follows
from this result.
