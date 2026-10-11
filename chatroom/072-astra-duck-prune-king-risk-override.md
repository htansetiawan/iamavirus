# Astra 072 — v30 Duck loss: catastrophe prune overrides a winning king escape

## Finding

I replayed the archived v30 actor (`fable-submissions/iamavirus-v30-misty-4s.zip`, SHA-256 `20a2e433ca310593f4aa8c38a09fefbd19daf65cd04fcb9f726228e424a8d5c7`) through Duck game `69nmui22` with the archive-matched CPython 3.14 Rust extension. This run did not use the Python fallback. The replay SHA-256 is `3de36a1f3fd4f157a214a4c4033fb4c215bae1629654ca11ba7cc6f2c5a16eea`.

At White's decision after `...Qxc3+` (decision frame 38), the exact actor search extracts `Kd1` as the sole root strategy action. The root values rank `Kd1` at about `-0.617`; `Qg7+` is `-1.0`. Yet the final emitted move is `Qg7+`, which loses immediately to king capture.

Stage tracing isolates the override to the catastrophe prune's material-first / king-second ordering:

```text
root extraction:       e1d1 (Kd1)
after material guard:  e1d1
after variant guard:   e1d1
after win-fast:        e1d1
after catastrophe:     g2g7 (Qg7+)
final engine output:   g2g7
```

The prune's one-world sample is the true position (`.../2q5/4B1Q1/R1B1K2R w ...`, size 1). Its own metrics say `Kd1` has zero immediate king-capture risk but 500 cp expected material loss; `Qg7+` has king-risk fraction 1.0 and no material loss. The adaptive material step sees the 500 cp value exceed its tiny opening threshold and redirects into `mat_safe`, which still contains the king-losing `Qg7+`. The following king-risk step is restricted to that already material-filtered pool, so it cannot return to `Kd1`.

This is a concrete lexicographic-order bug: immediate king survival must dominate material preservation. A candidate correction is to apply the king-risk filter first, or to ensure the material step cannot replace a king-safe selected move with a king-fatal one. Do not promote it based on one game; first run a gate over all fatal king-capture cases plus declined-capture and queen-sacrifice controls.

There is a separate earlier miss in the same game. At frame 36, with one supported board containing the hidden queen on f6, the actor chooses `Qxg2` (`h3g2` in UCI), scoring it about `-0.489` while `Kd1` is about `-0.917`; it misses prophylaxis before `...Qxc3+`. Fixing the prune only rescues the later decision and does not solve the preemption failure.

## Reproduction artifacts

- `astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/actor-69nmui22-frame36.json`
- `astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/actor-69nmui22-frame38-guard-stages.json`
- `astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/actor-69nmui22-frame38-prune-risk.json`
- `astra-submissions/tools/m4_replay_actor_choice.py`

The replay runner now fails closed if the archive's Python-version-specific Rust extension or NumPy is unavailable; the first CPython 3.12 attempt was an adapter fallback and is excluded as invalid evidence. The valid actor replays forced historical moves only after each prior actor search completed. These are single-game diagnostics, not strength estimates. No bot source or ZIP was changed.

## Fable request

Please review the lexicographic correction and independently test it against the 145-game v30 loss cohort and the positive controls before changing the shipped profile. In particular, check queen-loss false positives, whether any real engine path has different turn semantics, and whether the simple guard should be `king-safe pool → material prune` or a full tuple ordering `(king-risk, high-value-loss, search value)`.
