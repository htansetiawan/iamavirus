# 010 — Fable: evening state and plan (2026-10-07, 20:20 UTC)

## Where things stand

- **Arena**: v10 active, 44W–1D–37L; rating 1525 (TA Baseline A 1528, TA Baseline S 1708, duck 1909, Knight Vision 2065, Greek Gift 2165). Records vs duck (1–13), TA-S (2–7), TA-A (8–9) match the rating gaps: overall strength, not one hole. v10 scores 0.59 as White and 0.44 as Black; v5 scored 0.76 both colours; a per-colour benchmark is queued to test for a Black-specific defect.
- **Harness**: `tools/benchmark_corpus.cc` samples each seat's own decisions (`(ply/2) % stride`, Astra's review), takes `FOW_SEED`, and reports a true-board two-ply oracle metric and a per-colour split. Every number before `fa61ad4` was White-biased.
- **Deductions**: pawn rules only (the slider case cannot occur). Both arms from one binary: true attacker held at the fatal ply 0.191 → 0.228, material left en prise 8.21% → 7.70%, fatal-ply survival 352 vs 351 over three seeds (the seed-777 drop was churn). Shipped on. `EngineOptions::visibility_deductions`, `FOW_VISIBILITY_DEDUCTIONS=0` off.
- **Two-ply hidden-threat term** (`Engine::ExpectedHiddenThreat`, weight 1.0): decisions leaving a ≥3-point hidden threat one quiet move away 11.74% → 7.35% (real players 9.60%); nothing else moves.
- **Clock**: every real-clock decision stopped at the 4 s cap; arena games end with a median 121 s unused. New defaults cap 7 s, hard cap 12 s, divisor 20; a 300-ply game still ends with 14 s.
- **Second core**: matrix cells on two threads (`cell_threads` = 2), separate searchers and tables, wall time unchanged.

## The three archives (all "candidate for the next upload"; whichever is uploaded first becomes arena v11)

| archive | sha | content | evidence |
|---|---|---|---|
| `iamavirus-v11-candidate-hybrid.zip` | `68a89006f6c2` | v10 + exposure term + pawn deductions + clock scaling + promotion rule | 10–10 over 20 real-clock games vs archived v5 (paired 0.500, 0.300–0.700); better on every offline instrument |
| `iamavirus-v11-candidate-twoply-hybrid.zip` | `022fd76bb778` | + two-ply term | lanes D/E vs the first candidate running (cores 0–1, 6–7) |
| `iamavirus-v11-candidate-full-hybrid.zip` | `022f45c3afa3` | + clock defaults + two-thread cells | suite with the new defaults queued; lanes F/G vs the two-ply archive queued |

Astra's `astra-submissions/iamavirus-v12-hybrid.zip` (`a5f806d0039f`, exposure-only runtime) is a repository trial candidate, not an arena number.

## Plan for the night

1. Lanes D/E land (~20:50 UTC): if the two-ply archive is not worse than the first candidate, it becomes the recommendation.
2. Suite with the new defaults, then lanes F/G (~21:00–21:50): if clock + threads hold at real clocks (no overruns, not worse), the full archive becomes the recommendation.
3. Per-colour benchmark: if Black seats are worse than White seats relative to the real players, open a Black-specific investigation (feature canonicalisation, opening phase, time use).
4. Belief lane (Astra): previous-mover-survived exactness, bounded history enumerator for unseen pieces (qyzsbfdc), endgame king mobility in the prior (dlhy2zfg).
5. Not started, in priority order: opening book from the top teams' first plies; per-row risk logging in the trace for flipped-seat diagnostics; danger calibrator.

## Process rules kept

Commit only own paths; archives named `v11-candidate-*` until the user reports the arena number, then renamed; `pgrep -x`/flag files instead of `pgrep -f`; timed lanes on dedicated cores (mine 0–1 and 6–7 tonight, Astra's 2–5).
