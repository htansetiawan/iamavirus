# Evaluator reuse: reject a cache; measure state dependence

A native Stockfish debug log captures **all 30,015 completed requests** in a
six-decision searched-prefix probe (seed12 White, target d6, 32 initial worlds,
fast roots, scale1, settling off). Request counts exactly match the bounded
transport diagnostics; all searches/snapshots and evaluator exchanges succeed.
The selected target move is Qd4-h4. This is a new instrumented tree, not a
reproduction of the earlier Nc3/Qf4 choices.

## Full-stream result

| Measure | Result |
|---|---:|
| Unique exact FENs | 28,281 |
| Repeated requests | 1,734 / 30,015 = 5.78% |
| Repeats with identical full score maps | 6 |
| Repeats with changed score maps | 1,728 |
| Repeats whose bestmove changes | 421 |
| Repeats with changed move coverage | 0 |
| Compared move scores | 53,339 |
| Absolute score change vs first occurrence, median / p95 | 3 / 62 cp |
| Largest individual score change | 1,174 cp |
| Largest-change-per-repeat, median / p95 | 59 / 296 cp |

An exact FEN includes side to move, castling rights, en-passant state and the
halfmove clock. It does not include Stockfish's mutable search state. A cache
that stores the first score map would often substitute different numbers.
Only 5.8% of requests repeat in this run, so this does not justify cache
implementation or a claimed search-speed gain. No cache has been added.

The earlier 13.8% duplicate estimate sampled nodes in a shallow exported tree;
it did not represent the full request stream. Use this full measurement for
this run rather than extrapolating the earlier subset.

## Controlled context check

Four positions are evaluated with the exact frozen Stockfish19 binary and
production settings (Threads1, Hash16, MultiPV256, depth1). Three are selected
from the largest observed variations and one from a low-change opening case.
For each: reset with `ucinewgame`, evaluate; evaluate again; prime with 20 prior
positions; evaluate; reset and evaluate once more.

| Case | Immediate repeat max difference | After 20 contexts max difference | Fresh-reset mismatch |
|---|---:|---:|---:|
| Prior 1,174cp outlier | 121cp | 118cp; best move changes | 0 |
| Prior 1,154cp outlier | 4cp | 135cp; best move changes | 0 |
| Prior 1,145cp outlier | 3cp | 78cp | 0 |
| Prior 4cp comparison | 2cp | 7cp | 0 |

All four fresh-reset score maps repeat exactly. This supports an engine-state
explanation for variation and is evidence against explaining it solely by
our log parser. The 20-position context is a controlled intervention; it does
**not** reproduce the original 30k-request search history or its largest jump.
State dependence alone does not prove that warm scores are worse than cold
scores. We have not established which improves Fog of War decisions.

Reset handshakes take about **4.9–5.4 ms each** in this diagnostic. That is
substantial relative to individual shallow requests, so resetting on every
leaf is not enabled. Native logging also changes search timing. UCI's
integer-millisecond internal times are not end-to-end transport measurements;
no throughput or playing-strength estimate is claimed from this experiment.

## Implementation and provenance

C diagnostic code: `mist-c`, branch `astra/m4`, commit `359a533`.

The C addition only enables Stockfish's existing `Debug Log File` option when
`MIST_FORCE_MOVES` is present and `MIST_M4_SF_LOG` is explicitly set. Ordinary
arena decisions ignore the logging variable. The setup uses an absolute
bounded handshake, rejects newline injection, and leaves scoring unchanged.
`c-transport-check.txt` records fake-engine deadline/atomic-score/shutdown
checks and a successful real-engine exchange. The parser's synthetic test
covers changed/unchanged repeats, mate conversion, missing pairings and
truncated traces.

The full 109MB log and immutable binaries stay on Seagate at the path in
`bundle.json`; their SHA-256 identities and all compact reports are retained
here. `sf-reuse-audit.json` includes per-decision counts and largest changes;
`sf-context-check.json` retains every controlled score map and priming FEN.

Reproduce with `tools/m4_sf_reuse_audit.py` and
`tools/m4_sf_context_check.py`, passing the immutable run and output paths.
No model, default policy, release ZIP or arena version changes.
