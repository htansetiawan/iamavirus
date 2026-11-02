# Equal-clock native decision screen: all-child Stockfish

Frozen gate: **PASS**. Median node ratio **1.384x** at 2.5 seconds per arm.

| Diagnostic | Original v37 scorer | All-child scorer |
|---|---:|---:|
| Immediate king loss | 12 | 12 |
| Two-point material loss in bounded exchange probe | 6 | 5 |
| Four-point queen loss in probe | 0 | 0 |

51/51 pairs exercised. 15 choices changed. By-first-arm median node ratios: {"0": 1.3822846151913706, "1": 1.383653875492001} (0 baseline first, 1 candidate first; different case subsets).

Collector completed all 51 first attempts in 386.8 seconds. Course referee agrees on every label (2193 frames, 6149 tactical transitions). Independent audit reconstructs all 51 private input histories and checks 19 copied source files against the exact v37 archive.

Both calls share belief, guard exclusions, root actions and world samples. Each starts fresh Stockfish workers, so TT/history cannot transfer from the first arm to the second. Startup is excluded from each search budget. The actual scorer and its tactical approximation change; the native belief, guard, CFR and root-selection implementations do not. More nodes can reflect both cheaper evaluations and different tree choices. These are reused development cases, not Elo evidence.

A full-game pilot is conditional on this gate and the audits. No ZIP or arena promotion follows from this screen alone.
