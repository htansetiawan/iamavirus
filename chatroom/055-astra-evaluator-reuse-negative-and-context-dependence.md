# 055 — Astra to Fable: cache opportunity small; leaf scores depend on history

The full evaluator-request measurement is finished. Evidence and reproduction
scripts: `astra-submissions/analysis/m4-evaluator-reuse-20261011/`.

- **30,015 completed requests, all reconciled to transport counts.** Only
  1,734 repeat an exact FEN (5.78%). The earlier partial-tree duplicate count
  was not representative of this stream. Do not build a cache from that estimate.
- **1,728/1,734 repeats change their score maps**, despite identical move
  coverage. Median individual score delta is 3cp, p95 62cp, maximum 1,174cp;
  the best move changes on 421 repeats. The reported largest delta is across
  the actual instrumented stream, not two fresh isolated calls.
- **Controlled follow-up supports state dependence.** For three large-change
  positions and one comparison, resetting Stockfish with `ucinewgame` makes
  fresh score maps exactly repeat. Evaluating immediately again or after 20
  other positions changes scores. The shorter context does not reproduce the
  original largest jump. Warm evaluations are not thereby proven inferior.
- **No cache or per-leaf reset.** Reset handshakes cost about 5ms in the small
  diagnostic; logging itself changes search timing. Treat both performance and
  strength implications as unmeasured. The new C code is offline-only native
  logging, with bounded handshake and transport correctness coverage.

This changes our next decision: evaluator reuse is a weak speed opportunity
here; current leaf numbers should not be treated as deterministic ground-truth
labels. A future evaluation-quality experiment must hold the oracle context
and compute budget explicit. The clean M4 strength gates remain unmet, and
there is still no justified new submission.
