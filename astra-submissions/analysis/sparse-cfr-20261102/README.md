# Exact selective CFR: fixed-work result

**1.252x geometric-mean solver speedup**, passing the declared 1.20x condition for an equal-clock search test.

All eight saved-tree comparisons are bit-identical. This is an execution optimization, not playing-strength evidence.

| Case | Baseline seconds | Candidate seconds | Speedup |
|---|---:|---:|---:|
| 4zy248z7-16 | 0.4133 | 0.2858 | 1.446x |
| 807otaeb-24 | 0.3989 | 0.3237 | 1.233x |
| jg8arl68-35 | 0.3802 | 0.3385 | 1.123x |
| u66jmz73-16 | 0.3378 | 0.2584 | 1.307x |
| e9ap0123-48 | 0.6165 | 0.5287 | 1.166x |
| 465co8me-26 | 0.4725 | 0.3747 | 1.261x |
| o3b5wvz1-41 | 0.3967 | 0.2912 | 1.362x |
| axvqi3b1-59 | 0.6402 | 0.5578 | 1.148x |

Times sum five measured repeats of 200 iterations after an excluded warmup. Order alternates; all first attempts are retained. The sanitized real-tree run is excluded from performance.

Native/growing checks compare 9,569 checkpoints and 6,263,272 doubles across 8,193 iterations, including 496 stale-prediction clears. ASan/UBSan/LSan pass. A deliberately omitted prediction clear fails the equality check.

The audit verifies the frozen source/binary/tree hashes, output arithmetic and tree dimensions. Only cfr.c and cfr.h differ from original v37. The prior experiment already checked the saved trees against replay inputs and the referee.

The candidate retains geometric-capacity storage and sparse index lists. Corrected solver-array memory is recorded in summary.json; the raw benchmark storage field omits sparse lists. This is not a total-process memory measurement.

Next: compare whole searches on identical beliefs, allowed moves and world draws at the same 2.5-second budget, then full games only if that diagnostic passes. No new ZIP or Elo claim.
