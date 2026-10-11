# Same-tree continuation evidence and a negative settling screen

These are retrospective diagnostics and four local screening games, **not an
Elo estimate or a release candidate**. C diagnostics are published as
`mist-c` branch `astra/m4`, commit `da4d88b`; the search policy is unchanged.

## The queen capture was expanded

A searched-prefix replay of seed12 White decision 6 chose **Qd4-f4**. After
selection, the new read-only exporter inspected Nc3, Qc3, Qd2 and Qf4 in the
same saved tree. All four exports contain identical 91 root states, values and
reaches. The independent referee checked 10,759 hypothetical node states.

| Alternative | Root policy probability | Immediate king-loss share | Weighted continuation value |
|---|---:|---:|---:|
| Na4-c3 | 0.171816 | 0 | -0.360252 |
| Qd4-c3 | 0.189116 | 0 | -0.367024 |
| Qd4-d2 | 0.011496 | 0 | -0.369758 |
| Qd4-f4 — actually selected | 0.463423 | 0.092835 | -0.385222 |

These are four nominated actions, so their policy probabilities need not sum
to one. Values and risks use the saved gadget's normalized effective reach;
that distribution is **not** the particle posterior or a calibrated probability
of the true board. A continuation value is not a solved action value.

The actual board is root 17. After hypothetical Nc3, **Nc6xd4 is expanded and
has opponent probability 1**; Nc3's continuation there is -0.9770. Qd2's is
-0.1805. This directly rejects a missing-expansion explanation of that branch.
It does not reproduce the earlier run's selected move: this run selected Qf4.

Why can Nc3 still outrank Qd2 overall? Root 183 has 26.714% effective weight
and a hidden bishop on d7 attacking Na4. Qd2 leaves the knight capturable;
Nc3 saves it. Its contribution to Nc3 minus Qd2 is +0.29104, larger than the
net difference +0.00951. Another 6.116%-weight world has Qa5 attacking Na4.
The search is making a cross-world tradeoff, not simply overlooking the queen.
The trace does not establish that these world weights or leaf values are right.

## The earlier recapture is almost tied

A separate searched-prefix run at White decision 5 inspected Nf3xd4 and Qd1xd4
in one 10-root tree. All 608 hypothetical states validate. The bot selected
Qxd4 with policy probability 0.500908 versus 0.499092 for Nxd4, despite final
weighted continuation values -0.385621 and -0.346645 respectively. The true
root's values are -0.543005 versus -0.310391.

The near tie and final pure selection motivate measuring solver scheduling;
they do not prove that using the largest current continuation value is a safe
improvement. Opponent policies can change in response to our strategy.

## Full-clock settling comparison: reject promotion

A new seed13 four-game screen compares `MIST_M4_SETTLE=0` and `0.2`, each as
White and Black, against the same frozen Fable mist-c v8. Both arms use the
same candidate bytes, 32 initial worlds, fast carried-root initialization,
180+2 clocks, maximum 10 seconds and the same existing total search deadline.
Execution order reverses by color. Historical moves are not supplied to bots.

| Arm | White | Black | Record | Recorded faults |
|---|---|---|---|---:|
| settle 0 | loss, 61 plies | win, 99 plies | 1W–1L | 0 |
| settle 0.2 | loss, 61 plies | loss, 22 plies | 0W–2L | 0 |

All 122 M4 decisions report successful searches/snapshots and evaluator
exchanges. All 42 treatment decisions record fixed-tree iterations. The
independent referee reconstructed all **247 frames**, both observations and
terminal results. Process cleanup receipts are clean. These trusted local
matches enforce clocks and turn suspension, not the arena's complete security
and memory sandbox.

The control White ending has no one-move escape. Treatment White captures a
rook covered by hidden Be4 while Kd1/Kb1 survive one move, already down 940cp
before that capture. Treatment Black plays Nc6-a5, uncovering Qa4's diagonal
to Ke8; it has many one-move alternatives and is only down 90cp. The two White
openings diverge at White's second turn; Black diverges on its first turn.
The screen is not an identical-tree extra-iterations comparison.

The intervention has no positive strength evidence. Keep settling off; do not
launch a larger promotion benchmark or package a release on this result.
The earlier two-seed forced-prefix failure remains in `../m4-settle-20261011/`.

## Reproducibility

`bundle.json` maps every retained raw artifact to its SHA-256 and compressed
repository copy. `queen/` and `recapture/` retain original manifests, probe
receipts, output, source patches and all alternative traces. Binaries and full
immutable run directories remain on the user-authorized Seagate drive.

Frozen candidate SHA-256:
`5892c2a9015395de2f541f954d3d3edc06b9217d9c7291913fd01d9d23949ab0`.
Frozen opponent SHA-256:
`8a14e1c8d32d434539d3fe7210e1a1fbc8d9002cadfbcee235b4b2dbb4a4067a`.
Full-game manifest SHA-256:
`fe2af9029fddaf73685223373220f756bdf6b12bb4edbb0b61c947b4ca10c9a7`.

Auditors: `tools/m4_compare_alternatives.py` and `tools/m4_match_audit.py`.
`c-correctness.txt` records the C fixture: exporting a different action leaves
the selected-action trace byte-identical. `test_m4_clock_report.py` checks
exact diagnostic coverage and keeps settling arms separate in summaries.
# Audit correction, 2026-10-11 13:25 UTC

The original `full-game-audit.json` observation-change field spanned our move
and the opponent's together. Use the corrected copy and comparison in
[`../m4-live-corpus-20261011/`](../m4-live-corpus-20261011/README.md).
All other audit fields and the strength-screen conclusion are unchanged.
