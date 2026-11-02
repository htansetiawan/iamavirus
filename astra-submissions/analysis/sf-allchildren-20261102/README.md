# One-pass all-child evaluator: first feasibility gate passes

The isolated Stockfish 19 modification scores every legal child in one root
pass with full-window PV searches. It retains native NNUE and quiescence, but
changes pruning/history and is **not** score-equivalent MultiPV optimization.

| Development measurement | Cold table | Warmed stream |
|---|---:|---:|
| Speedup versus shipped universal PGO binary | 1.619x | 1.883x |
| Speedup versus same-build original source | 1.637x | 1.869x |
| Mean absolute tanh(cp/400) error | 0.01052 | 0.01424 |
| Shipped-value regret of candidate's best move | 0.00000 | 0.00122 |
| Regret greater than 0.5 | 0 / 256 | 0 / 256 |
| Exact top-move agreement | 255 / 256 | 247 / 256 |
| Mate-label/sign disagreements | 0 | 0 |

All six frozen requirements pass in both regimes. Native speed numbers are
total query wall ratios across three passes, excluding per-parent reset and
startup. They include UCI transport. Cold batch worker CPU includes reset
work, so it must not be interpreted as query-only CPU cost.

Selection: 256 played parents from 128 existing development games, two parents
per game, salted IDs without score/outcome selection. Referee reconstruction
verified 12,733 frames; one unsupported parent was recorded and skipped before
scoring. This is reused development data, not untouched test data or searched
leaves. Stockfish scores measure fidelity, not true Fog of War value or Elo.

Collector handle 15708 exited 0. All 6,144 scored queries completed on their
first attempts. Independent coverage/arithmetic/source review checked 188,424
scored moves, 3,072 control pairs, complete legal-move coverage, and identical
outputs across repeats. Shipped, rebuilt base and patched-off controls match
scores, nodes and best moves. The 96-call preflight also covers promotion,
castling, en passant, check, mate-in-one, mate/stalemate, and flag isolation at
depth 2 / restricted MultiPV. No changed scoring window was selected afterward.

Provenance: all compiled source files in official `sf_19` match the local
release distribution. Its universal binary is byte-identical to the v37
packaged evaluator. The 98,511,183-byte embedded network was exported and
hash-verified. The initial preparation stopped on a metadata-only missing
`.gitattributes`, retained in `preparation-failure.json`; no measurement was
discarded. Only `search.h` and `search.cpp` differ in the candidate. Licence
and source pins are retained; patch applies cleanly to the pinned source.

Compressed first-attempt JSON files preserve exact uncompressed bytes;
`review.json` records both hashes. Large build/network files are ignored.

**Next: a separately frozen search-frontier fidelity test.** Only a pass there
earns an equal-clock mist-c decision comparison and later full games. There
is no new submission, version reservation, GPU use or strength claim.
