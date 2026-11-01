# Compressed context mixtures: correct representation, insufficient predictor gain

1 November 2026. **The temporal predictor does not pass the recorded advancement
test. No larger-cap trial, policy trial, ZIP or deployment follows.** The new
representation is useful, independently checked infrastructure; that is not
evidence of improved playing strength.

18 new games, 650 decisions, three arms: original static model with board-only
merging; the same model with compressed context mixtures; temporal model with
compressed mixtures. All use cap 20,000, temperature 2, seed 11012026, full
features and no empirical history table. All 54 processes exited successfully.
Sixteen observer seats are ours. Both Instructors observer seats belong to
other teams because no remaining qualifying IAmAVirus seats were available.
The own-seat-only result is separately reported and has the same gate outcome.

| Arm | True board present | Mean truth NLL, clip 1e-12 | King-event Brier | Update seconds |
|---|---:|---:|---:|---:|
| Original static merge | 642/650 | 5.647517 | 0.009475 | 18.44 |
| Compressed static mixture | 642/650 | 5.647517 | 0.009475 | 31.22 |
| Compressed temporal mixture | 644/650 | 5.583970 | 0.010252 | 32.92 |

The required NLL improvement was >=0.1 nat against both controls. Actual gain
is 0.06355. It is 0.04256 at clip 1e-9 and 0.08480 at 1e-15, so clipping does
not change the decision. The own-seat-only gain is 0.07536. Support and runtime
requirements pass; king Brier worsens within the allowed 0.002 margin. There
are only eight positive king-loss events, insufficient to validate safety.
No belief empties, so all 650 decisions enter the risk comparison.

Do not compare these coverage percentages with the preceding experiment's
88.79%/84.49%: they are different games. The relevant representation control
is **within this panel**. At all 650 decisions, compressed static has exactly
the same board count and truth presence as the original. Maximum absolute
truth-probability difference is 6.59e-7, and king-risk difference 1.25e-7.

## Engineering result

A physical board occupies 232 bytes including offsets/metadata; each recent
context adds eight bytes. About five contexts per board are retained on
average; the largest observed set is 74 contexts for one board. Temporal peak
retained storage is 7,864,512 bytes; peak process RSS is 75,836 KiB. Generated
successors remain 24-byte records until board-level selection. Static features
are reused per board; six radix passes group board/context keys.

Temporal updates cost 1.785x the original static reference. Most overhead is
keeping history mixtures: static mixture alone costs 1.693x. This implementation
is single-threaded while the original may use two threads. No general speed
or arena-clock advantage is claimed.

The native implementation matches independent exhaustive joint-history
enumeration at temperatures 1 and 2 for both models, including multiple own
and opponent moves, cap preservation of every retained board's contexts,
empty updates and const diagnostics. Optimized and ASan/UBSan checks pass.
An entire fresh case also passes through the sanitized ctypes library. The
private-input pilot produces identical posterior/RNG checksums and risks
with truth labels redacted.

`summary.json` audits all 54 first outputs, pinned source/dependency/library
hashes, input/truth hashes, labels and decision alignment. Independent
aggregation reproduces the table (`static-parity.json`). Source and frozen
plan were committed as `4a7eddb` before the full comparison.

## Decision

Keep the compression implementation and its oracle tests for future work.
Close the current recent-action predictor's promotion path here. Do not tune
its coefficients, temperature or cap on the inspected panels. The isolated
filter also lacks complete opponent information-history integration for CFR,
empirical history blending, cheap feature fallback, arena-clock thinning and
post-collapse reconstruction. Passing this small screen would not have been
sufficient for a release even if the predictor had met its threshold.
