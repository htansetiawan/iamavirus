# Misty compatibility and strategy research

Astra, 2026-10-09. This is a source/rules audit, **not a playing-strength result**.
See the [strategy design](../../specs/strategy-first-20261009.md) for the proposed
skill library and its research sources.

**Later adapter finding:** Fable's newly available local wrapper supplies the
wrong legal-move list in 1,940 of 4,724 nonterminal replay turns. The course
starter's observation tracker matches all 4,724 using observations and own moves
only. See [handoff 028](../../../chatroom/028-astra-misty-adapter-conformance.md)
for the reproducible audit and concrete repair. The source-level result below
does not certify the wrapper's integration.

## Result

Pinned public Misty source at
[`5ba2c31e52868ba79e34e3eb2e042e14847ab4a9`](https://github.com/brianhliou/misty/tree/5ba2c31e52868ba79e34e3eb2e042e14847ab4a9).
Its Python move generation and visibility matched the course referee on:

- all 4,788 frames of the frozen 64-game Mist v1 corpus;
- seven synthetic positions covering castling into/out of/through attack,
  queenside castling, en passant while in check, adjacent kings and promotion;
- **4,795 move sets and 9,590 observations: zero differences**.

This does not test native Rust, search, protocol metadata, memory caps or clocks.
The Python modules were loaded directly; no Misty engine or Stockfish was run.

`ChessRules.is_terminal` only detects missing kings. All 64 course final frames
still contain both kings: 58 end with “King capturable,” six with threefold
repetition. Keep the MIT referee's adjudication in the match harness. Separately,
Misty's `cfr/leaf_eval.py` does implement `king_capture_imminent`; the terminal
method difference does **not** establish a search defect. That path needs an
integration check when Fable's adapter runs.

## Adapter findings sent to Fable

1. **Capture metadata:** `observation.py` derives `own_capture_square` from own
   pieces present before but absent after an opponent move. It means **our piece
   was captured**, despite misleading wording in the protocol documentation.
   Infer it from observations after our last move and after theirs. En-passant
   removal and landing squares differ; never fill metadata from a hidden true
   board. See the [pinned implementation](https://github.com/brianhliou/misty/blob/5ba2c31e52868ba79e34e3eb2e042e14847ab4a9/src/fow_chess/observation.py).
2. **Profile:** the `STRONGEST` alias names `v1.0-gadget-off`, with king-aware
   leaves enabled and the resolve gadget disabled. Other profiles exist; plain
   constructor defaults differ. Log the resolved profile, not just “Misty.” See
   [profile definitions](https://github.com/brianhliou/misty/blob/5ba2c31e52868ba79e34e3eb2e042e14847ab4a9/src/fow_chess/engine_profile.py).
3. **Runtime:** record source revision, Stockfish binary/hash, native backend,
   actual enumeration cap and clocks. The PyPI release and a current GitHub
   checkout need not contain the same code. Rust availability matters for a fair
   real-clock comparison; the README's speed claims are not our measurements.
4. **Identity:** Misty's association with arena “Mist Opportunities” remains an
   unverified hypothesis. Matching dates/name/architecture does not identify the
   submitted binary. Use it as a real local opponent regardless.

The README's reported enumeration-cap and bare-king weaknesses are experimental
leads. They do not show the arena bot has those weaknesses. Two-square king
shuttling also does not guarantee a draw: course repetition checks the complete
position, side to move and relevant rights, while the attacker can keep changing
its position.

## Reproduce

Use a checkout at the pinned commit as `--misty-source`. Python needs
`python-chess`; no model download or GPU is involved.

```sh
.venv/bin/python astra-submissions/tools/audit_misty_rules.py \
  --misty-source /tmp/astra-misty-source-review \
  --referee /home/henrytan/git/fow-starter/referee.py \
  --corpus /media/henrytan/seagate/iamavirus/astra/corpus/mist-v1-20261009 \
  --output astra-submissions/analysis/strategy-first-20261009/misty-rules.json
```

For this run the source directory is a downloaded subset, with the GitHub tree
response in `tree.json`. The tool also accepts a Git checkout. Source hashes and
the course-referee hash are in [misty-rules.json](misty-rules.json); the complete
reviewed-file inventory is in [misty-source-receipt.json](misty-source-receipt.json).
Raw corpus provenance remains in the [earlier audit](../mist-v1-20261009/README.md).

## Corrections to the shared research summary

- Penumbra's RBC environment **provided** opponent identity; its specialized
  policies do not validate our MIT opponent classifier.
- Obscuro's reported purification ablation was larger than its KLUSS ablation;
  we should not call opponent-knowledge modelling the largest measured factor.
- An invisible attack is an advantage to test, not a guaranteed win. The opponent
  may remember the attacker, infer the line or escape without seeing it.

These corrections refine the implementation plan; they do not require waiting
for a universal model before trying an opponent-specific counter-strategy.
