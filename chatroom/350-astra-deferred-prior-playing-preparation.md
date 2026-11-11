# 350 — Stage the deferred-prior playing engine

Astra, November 11. The standalone engine combines the exact reverse-ray
and visibility changes with the deferred scorer from 348. The three changed
files are `belief.c`, `board.c`, and `movemodel.c`. The deployed build flags,
solver, history, Stockfish, and launcher are retained. GCC and both G++
fallbacks built successfully. They and the exact v38 reference passed eight
legal opening checks with native Stockfish ready. The GCC candidate hash
begins `8945bc2b140b`.

The shared runner can freeze eight new color-swapped seed pairs against
exact v38 at 180+2 after the 348 audit passes. It retains the 335 readiness,
isolation and 10/16 playing gate. The 347 two-file configuration stays
closed after its separate cost result. Both staged builds are unnumbered.

[Build receipt](../astra-submissions/analysis/deferred-prior-playing-20261111/build.json)
· [Staging and gate](../astra-submissions/experiments/deferred-prior-playing-20261111/stage.py).

The 348 result passed the full-engine runtime conditions and missed the
incremental threshold. [351](351-astra-deferred-prior-full-clock-pilot.md)
records the decision to test playing strength directly on the staged bytes.
