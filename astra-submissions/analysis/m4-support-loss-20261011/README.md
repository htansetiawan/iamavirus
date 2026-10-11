# Two distinct failures: losing a board and misvaluing a surviving move

These are offline diagnostics of the experimental C engine, not an arena
strength claim or a reconstruction of arena v30's internal state. No runtime
default, model, ZIP or arena version changes.

## Where the true state first disappears

Read-only instrumentation runs **after** the existing cap selection. It reads
candidate weights and selected indices without changing them or consuming RNG.
The auditor's true-board key is never an input to selection. All **1,680 original
non-timing decision rows match exactly**, across the previous 43-game cohort
(42 primary games plus one diagnostic), cap 10,000 and seed 41.

Of 1,652 traced updates, **21 games first lose support at cap sampling**. Every
first loss retains the true state through expansion and observation filtering,
then discards it at selection. There are zero observed supported-parent filter
failures and zero unexplained first losses. Counting later recoveries and losses
gives 30 supported-parent loss events.

| At the 21 first losses | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Ply | 10 | 43 | 96 |
| Unique candidate states | 13,045 | 63,618 | 114,687 |
| True state's weight rank | 987 | 11,522 | 55,113 |
| True state's pre-cap probability | 1.008e-7 | 1.393e-5 | 1.432e-4 |
| Retained pre-cap mass | 0.5064 | 0.7369 | 0.9899 |
| Pre-cap effective sample size | 1,305 | 4,941 | 9,663 |

Nine first-loss states rank within the top 10,000. Preserving the highest weights
could help those individual updates, but a pure top-K policy could discard other
real states. No alternative cap rule has yet passed a sequential gate.

The mass cross-check covers 1,438 rows. Pre-cap truth mass divided by retained
mass agrees with committed truth probability within 1.455e-8; float32 recentering
explains the small arithmetic discrepancy. The original output parity is exact
apart from timing. `trace/audited-report.json` adds that independent check to the
original run; the updated runner incorporates it for future runs.

This small-cap, one-seed development diagnostic does **not** establish the
frequency of this failure at the live cap, nor that increasing cap improves Elo.

## Protected queen bait: support alone does not fix search

Public game `4bkwxxng`: Instructors v4 versus IAmAVirus arena v30. Black's final
decision is ply 55, with material +100 cp. Historical **Kf8xe7** captures a
visible queen but enters attacks from hidden Re1 and Nd5. **Kf8–g8** is the sole
true-board move that survives immediately. Its eventual game result is unknown.

A forced-history belief-only replica keeps the true board throughout, ending
with 59 states and true-state mass 0.294656. It assigns the historical capture
fatal probability 0.954080. The frozen search binary uses its built-in prior,
rather than this refitted control; its final true-state mass is 0.293618.

The search probes all request Stockfish and verify `ready=1, failed=0`. All
choose the queen capture, even when every retained state is supplied as a root:

| Roots / budget | Kxe7 adaptive fatal share | Kxe7 raw value | Kg8 fatal share | Kg8 raw value |
| --- | ---: | ---: | ---: | ---: |
| 32 / 1 second | 0.70337 | −0.42434 | 0 | −0.90728 |
| All 59 / 1 second | 0.82484 | −0.65811 | 0 | −0.86439 |
| All 59 / 4 seconds | 0.53042 | −0.10339 | 0 | −0.99602 |

These are CFR's adaptive reach-weighted shares and saved-tree values, **not**
posterior probabilities or calibrated win odds. The independently reconstructed
alternative trees cover **5,991 hypothetical node states** and reproduce the
reported weighted action profiles. In the 32-root trace, most of the true-world
Kg8 reply values are frontier estimates, not proven terminal losses.

This case survives both broader roots and a larger search budget. The next
search experiment must address continuation values and opponent information,
rather than attributing this failure solely to missing belief support.

### Reject unintended evaluator fallbacks

The first `bait/cold` probe requested Stockfish but failed startup and silently
used the internal evaluator. It is retained but **excluded from the intended
external-evaluator arm**. `m4_replay_probe.py` now saves an invalid receipt and
fails immediately if requested Stockfish is not ready. The deliberate
`/bin/false` test exits 1, saves the invalid receipt, and creates no results JSON.

## Fresh public data

Snapshot 2026-10-11 17:12:20 UTC: active arena v30 record **155W–24D–177L / 356**.
Six additional cached games yield 2 wins and 4 losses. The independent referee
checks all **467 frames**, both observations, legal moves and terminal results.
These historical results belong to the existing submission, not our diagnostic.

## Retention and reproduction

`inventory.json` verifies each retained compressed artifact against its original
bytes under `/media/henrytan/seagate/iamavirus/astra/m4-support-loss-20261011`.
Native source is stored as `trace/native/` to avoid Git's ignored build-directory
rule. Executables and Python bytecode remain on Seagate; their hashes are listed.
The saved `trace/run.py` is the originally executed driver; `tools/` contains the
later reporting improvements. Original paths inside manifests are provenance.

Build the read-only instrumented replica with `m4_support_trace_build.py` from
the previous experiment's immutable `prior/sequential/build` snapshot; run
`m4_support_trace_run.py` against that experiment's retained sequential inputs.
No shared `belief.c`, `belief.h` or `cfr.h` was edited.
