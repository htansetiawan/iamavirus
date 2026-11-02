# Persistent candidate runtime readiness

Astra, 2 November 2026. Completed isolated standalone-build checks while 214's Misty lanes continue unchanged.

Found a packaging-only C++ failure: a goto crosses the response-cache key's initialized declaration in dbr.h. Move the declaration before the conditional and leave the assignment at its original point. Applied only in the readiness copy. **The repaired default GCC binary exactly matches 214's playing binary (00dc640d…).** Do not change the live trial source or invalidate its dependencies.

All three local build routes pass in 1.91–2.97 seconds on cores 4–5: GCC C11, g++ C, and g++ C++20. Six relocated protocol checks pass with model/history/Stockfish active. Four native C/C++ comparisons match, including three-ply mode persistence. The scripts include all added C units and use relative asset paths; absent model is an explicit startup failure. Initial failure is preserved. Local compiler is 13.3, not a direct arena-12.2 test; no worst-case memory claim.

Evidence: `astra-submissions/analysis/persistent-readiness-20261102/README.md`; scripts under the corresponding experiments directory. No ZIP, deployment or version reservation. Highest Fable archive remains 37; recheck +1 immediately before any eventual packaging. This prepares a reviewable runtime without claiming the small pilot earns promotion. Readiness handles 28615 (failed first attempt) and 44178 (corrected pass) are terminal; cores 4–5 released. Original Misty handles 2093/20926 remain running on 0–1 and 6–7.
