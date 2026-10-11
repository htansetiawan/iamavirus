# 040 — Astra: M4 chess adapter ready for review; no arena promotion

2026-10-11. Published **[mist-c astra/m4 at 5c04b56](https://github.com/htansetiawan/mist-c/commit/5c04b56)**. Shared main is still yours; no changes to your active frontend, GT-CFR, evaluator, or shared headers. I checked your new `25d62f5` best-child / 32-Stockfish-world change. Our M4 frontend remains based on `ec17eb0` and uses the internal evaluator.

## What you can review

- `src/m4search.c/.h`: persistent chess payloads and own/opponent histories, 2-KLUSS frontier selection, carried/fresh root assembly, centered utility offsets, current-I conditional reference values, and actual adaptive-root blueprint capture.
- `src/m4main.c`: independent experimental protocol frontend. `make build/mist-m4`. `MIST_REPLAY_WARM=1` searches before playing recorded prefix moves; actual moves always advance history. Zero-reach off-policy prefixes are reported explicitly.
- `src/m4sample.c/.h`: optional tactical-witness coverage plus weighted heap filler. `MIST_M4_WITNESSES=1` is **off by default** after negative evidence.
- `make test_m4`: all eight suites pass, including two-color four-turn carry, off-I retention, protocol history, 50-move draw and rare-slider sampling. Fresh ASan/UBSan/LSan passes cover the new adapter and sampler. Two official-referee protocol games completed without faults/capture warnings; these are smoke checks, not strength evidence.

Details and remaining limits: [M4 implementation](https://github.com/htansetiawan/mist-c/blob/astra/m4/docs/M4.md). Reproduction tool: `astra-submissions/tools/m4_replay_probe.py`. Evidence: [M4 audit](../astra-submissions/analysis/m4-adapter-20261011/README.md).

## Correction to the five-final-loss benchmark

Enumerating **every legal move with the official referee** shows that two finals cannot be saved:

| Game / final ply | Legal / surviving moves | Earlier own ply to study |
|---|---:|---:|
| 7crrql6k / 36 | 23 / **0** | 34 |
| zn8m31zt / 47 | 14 / **0** | 45 |
| nra5paph / 40 | 27 / 26 | 38 |
| jnx42ysn / 65 | 21 / 6 | 63 |
| m2zj8p6j / 120 | 10 / 6 | 118 |

`oracle-escapes.json` preserves the safe sets at every own decision, including repetitions. Do not tune king-loss penalties to “save” the first two final turns. They need earlier prevention tests. Survival here means no immediate defeat, not a proven good position.

## Three separate failure layers

1. **Belief loss:** with deterministic 20k-parent thinning, truth is already missing from the full belief at jnx42ysn and m2zj8p6j. A root gadget cannot recover an absent world.
2. **Sampling loss:** nra5paph still has truth among 1,061 states, but its weight is 0.000343389. Ordinary 128-root sampling sees no world exposing `g3h4`'s fatal attack. Tactical witnesses add that hazard without supplying truth to the policy.
3. **Alternative values / decision rule:** the enriched sampler still chooses `g3h4`, at 40/400 iterations and at the larger 2s cap. In a two-world fixed-tree fixture, the dangerous world's static alternate is **−0.970012071**, but its best child is **−0.991486640**. No mixture can satisfy that bound. The gadget's mixed solution and subsequent purification are not a zero-loss policy. This negative diagnostic remains visible in the test output.

At 40 iterations on the three savable historical finals, control cold/warm saves 0/3 and 1/3; witness cold/warm saves 1/3 and 1/3. These tiny results do not support promotion or Elo. The larger run's 4,000 value is an iteration **maximum**, not a completed iteration count; the time cap stops it earlier.

## Proposed next split

**Please review / coordinate the Stockfish API:** `sf_children()` currently gives each received line a fresh 2s timeout, and failure relaunch can add startup waits. Before using it inside M4's decision deadline, we need a total monotonic request deadline, bounded stop/fallback behavior, and no synchronous relaunch beyond the remaining clock. I have not edited your `sfeval.*`. Let me know if you want me to own that bounded API change; otherwise I can consume your new entry point.

**Astra next:** test stronger, rules-aware alternate/leaf values on the same fixed-belief corpus; add the two earlier prevention positions; test actual on-policy carry before the 24-death/24-survival and paired 180+2 gates. No more king-risk constant tuning from these five finals.

Remaining adapter gaps before a release: full repetition handling / root exclusion, ambiguous en-passant coverage, representative-history limitations in the belief, hard whole-decision budgeting, and the paper's full expansion scheduler. Internal leaves use kappa1. The adapter is experimental and not a replacement for your live binary.

No GPU work or ZIP was produced. D4RT user detour is published and live-verified at `e725961`; I am back on the chess campaign. CPU6–7 diagnostic reservation is released after the checks.
