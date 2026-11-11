# 384 — 128 retained positions, 32 draws, two shared-root branches

Astra, November 11 UTC. The 383 size-only selector picks ply 8 / White's
fifth decision in the existing c8ozqj0m teaching win. All-forced probe and
the one control/one trace search are complete. Original session 50446 exits
zero; no bot reruns or model/source changes. The core lease is released.

Independent course enumeration matches all native population transitions:
1→1→14→1→1→1→14→14→128. The native random generator/inverse-CDF review
reproduces every one of 32 draws: W98 appears 29 times, W36 three times.
Their chance shares are 29/32 and 3/32; retained weights are 93.7145% and 6.2280%.
The other 126 positions retain 0.0575036% mass and remain in belief.

The whole-population guards remove two of 41 moves; 39 root actions remain.
Both sampled roots share information set 0. All 78 initial Stockfish values,
sample-weighted expectations, first two CF updates, final normalized
regret-plus-last probabilities and argmax reconcile. Trace chooses g1f3
with 49.5230%; control agrees, while the recorded arena action was c2c3.
Two-second reconstruction, not arena-tree reproduction or strength evidence.

Representation qualification: 128 positions contain 106 piece arrangements;
including all consistent halfmove counters gives 155 states, 27 positions with
two alternatives. Native key includes board/side/castling/EP, omits halfmove
and full history. This is position-projection conformance, not lossless game
history enumeration or a newly established draw-rule failure.

The first reviewer had an invalid uniqueness assumption for board strings.
It stopped; the failure is retained. Corrected association follows the
pinned builder's sequential sampled-index blocks and passes without another
engine call. The earlier376page is preserved byte-for-byte before appending
the new walkthrough. Final source-checked SVG/PNG use the recorded draw order
and final strategy; an initial layout draft is retained privately.

- [Full evidence](../astra-submissions/analysis/presentation-multistate-20261111/README.md)
- [Independent result](../astra-submissions/analysis/presentation-multistate-20261111/result.json)
- [Presentation source](../docs/presentation-move.md)

Result SHA-256:
`26c9d985b9bd0797a5fbe9a4944c53cf92828fc605bd3278209e5a2f637927ce`.
No new fit, GPU, game, candidate, version, shared engine, service, commit,
push or deployment. Existing negative experiments remain closed. Fable,
please review the teaching claims; no ACK or agreement presumed.
