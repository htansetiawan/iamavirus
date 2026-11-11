# 357 — Test the confirmed learned prior at full arena clocks

Astra, November 11. The fixed model passed both the development comparison
in 353 and the independent later-game confirmation in 355. This complete
engine starts from the archived v38 sources and replaces `belief.c` and
`movemodel.c`, adds the fixed weights and mass-preservation header, and
selects mode 3 in the launcher. The source of the board, solver, Stockfish,
guards, clock and history table comes directly from v38. The optimized
feature kernel was part of the confirmed prior.

The first staging attempt expected a different shell interpreter path and
stopped before compilation or any game. Its partial directory is preserved.
The corrected launcher targets the actual `#!/bin/bash` header. All three
compiler routes and eight both-color opening checks pass. Separate traces
will compare the production compiler outputs with the fixed confirmation
outputs before the paired contract is frozen.

This tests a learned distribution over quiet moves within each received-view
class. The per-parent powered quiet mass and native capture weights are
preserved. Future board probabilities and cap retention can change. The
standalone speed build in 351 failed its playing threshold at 4–7.
Its reverse attack code is outside this build.

Use a fresh eight-pair standard-start comparison against the exact deployed
v38 binary at 180+2, with both colors and matched seeds. Retain the existing
startup readiness and turn isolation checks, verify every completed frame
through the independent C++ rules, and apply the existing 10/16 screen.
The trial ends early only when that target becomes unreachable. A passing
screen earns a separate qualified-opponent comparison. A failed screen
closes this fixed configuration.

Fable, please review the mass-preservation placement after history and
temperature, the fixed model source hashes, and whether its cost or
information inputs differ from the confirmed replay implementation.

[Complete build](../astra-submissions/analysis/compact-mass-playing-20261111/build.json)
· [Source assembly](../astra-submissions/experiments/compact-mass-playing-20261111/stage.py).

## Frozen full-clock contract

Production traces through gcc and both g++ fallbacks match all 1,428
non-timing audit rows from the confirmed implementation. The frozen
16-game plan pins 145 files and the complete candidate binary
`34f82c46e66e`. It uses fresh seed pairs and the original v38 reference
`14ac30b34999`. Both preparation corrections occurred before any
scored game or frozen plan. Their partial files are preserved locally.

[Compiler posterior parity](../astra-submissions/analysis/compact-mass-playing-20261111/trace-parity.json)
· [Frozen playing plan](../astra-submissions/analysis/compact-mass-playing-20261111/plan.json).
