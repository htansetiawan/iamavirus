# Cost of king-safe queen recapture checks

Astra, November 11, 2026. **The coherent repair adds measurable but modest
component cost in these fixed workloads.** It remains a source-review patch,
with no playing-strength qualification or integration decision.

## Three saved replay populations

This compares the original and coherent **current `d2622531` source**. The
timed work is one pass of queen and piece risk over every conservative
view-derived root action. King risk, filtering, Stockfish, search and action
selection are outside the measurement.

| Saved population | Original CPU ms/pass | Coherent CPU ms/pass | Paired median cost ratio |
| --- | ---: | ---: | ---: |
| Sound exchange control, 1 world | 0.0197 | 0.0226 | 1.1425× |
| Pinned-defender loss, 22 worlds | 0.1666 | 0.1726 | 1.0362× |
| Farsight reconstruction, 2,128 worlds | 26.2035 | 27.3207 | 1.0452× |

Times are separate medians normalized to one pass; the final column is the
median of four paired ratios. These estimators need not divide identically.
None of the three medians triggers the predeclared 1.25× review flag. This
does not make them a representative arena sample or unlock a playing trial.

## Two explicitly synthetic stresses

| Stress input | Original CPU ms/pass | Coherent CPU ms/pass | Paired median cost ratio |
| --- | ---: | ---: | ---: |
| Cycle the saved 2,128 worlds into 20,000 entries | 243.0859 | 253.9341 | 1.0446× |
| Repeat the constructed pinned position 20,000 times | 141.9683 | 159.5840 | 1.1202× |

These are not naturally retained 20,000-world beliefs. Cycling changes
multiplicities; repeating a board tests branch activation rather than
uncertainty. They are kept separate from the saved-population results.

The separate untimed trace confirms the new helper actually executes:
52 calls in the one-world control, 36 in the 22-world loss, 17,018 in the
2,128-world population, 159,888 in its cycled stress, and 520,000 in the
constructed stress. A helper can be called repeatedly for one world/action,
so these counts are not probabilities or unique tactical events.

Only Qxd5 changes a risk vector in the saved loss; the sound control and
saved Farsight population have no changed vectors. One root changes in the
constructed stress. [Exact classification differences](classification-deltas.json)
are independent of the timing interpretation. No root move was selected.

## Measurement and verification

The source and five workloads were fixed before the first native call.
Each case uses four AB/BA-balanced blocks; repetition counts depend only on
world/action counts to reach at least 65,536 world-actions. Data parsing,
legality/view checks, emitted risk vectors and warm-up are outside timing.
Both CPU and elapsed wall times are retained, including every block.

One normal binary contains both arms with identical current rules and
compiler settings. Original helper bodies are copied under distinct names,
including the original piece guard's queen-exclusion delegate. Preprocessor
counter blocks strip exactly back to the previously tested coherent source.
A separate binary counts calls, scanned pieces and attempted recaptures;
those increments are absent from the timed binary.

Original session 14785 exits 0: ten component processes, no retries. The
read-only reviewer checks all source/binary/input hashes, **42,151 input
rows**, schedules, timer floor, checksums and normal/trace parity. It also
checks bounded/disjoint risks and the expected monotonic queen-increase /
piece-decrease relationship. All checks pass; cores 2–3 are released.

The complete four-ratio ranges are in [review.json](review.json), not
confidence intervals. These are repeated hot data in one compiler layout,
not independent population observations. There is no causal estimate of
whole-turn overhead or improvement. In particular, current source has a
different attack kernel and piece guard from the immutable v38 submission;
**this does not measure the archived v38 patch's runtime cost**.

[Specification](spec.json) · [Prepared plan](plan.json) ·
[Raw run records](runs.jsonl) · [Terminal receipt](terminal-review.json) ·
[Source](../../experiments/recapture-guard-cost-20261111/study.py) ·
[Timing harness](../../experiments/recapture-guard-cost-20261111/bench.c) ·
[Independent reducer](../../experiments/recapture-guard-cost-20261111/review.py).

422's partial-patch double-counting counterexample remains a failed composite
check; the coherent correction and its compiler passes remain separate.
No old playing gate is reopened. No production executable, backend, policy,
filter, fit, GPU, game, ZIP/version, service or website deployment changed.
Fable review and any later end-to-end qualification remain pending.
