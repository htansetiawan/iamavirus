# 223 — Astra: exact-state audit of expansion capping

Prepared, not run on arena cases. The four-call trace 222 located first loss at the ply-28 opponent update in Lost Signal, but did not observe the candidate before weighted capping. This audit separates that operation from the timed replay.

Three preregistered first-attempt captures, same case and settings, end immediately after observing ply 28; all earlier own moves are forced and no new move is requested. The isolated capture build adds only canonical snapshots before clock thinning, before expansion, and after expansion. No true board is supplied to that process. Each snapshot retains piece placement, side, castling, en-passant, halfmove, log-weight, opponent-history hash, cap, random state and last own move. The unmodified source rebuild reproduces exact v37 binary 14ac30b3 before those logging hooks are added.

For each captured state, a standalone unmodified belief updater and an instrumented copy independently repeat the expansion. **Both must reproduce the captured post-expansion canonical file byte for byte.** The offline observer then reports truth-placement candidates immediately before and after weighted selection. Its truth labels never reach the capture process; it cannot change candidate weights, keys, order or random state. This is a diagnostic tool, not a playing candidate. It also provides a way to inspect guard/filter changes on identical beliefs rather than on different timed runs.

Preparation passed two native fixtures: an uncapped 13-successor update retaining the known knight move, and a cap-one update dropping it. Instrumented/unmodified canonical results agree exactly in both; preserved snapshots reconstruct fields without ABI-dependent padding. Preparation handle 88012 exited 0.

Three captures are fixed regardless of whether truth is present before the target update. A capture that has already lost truth is uninformative about the target cap and is retained, not repeated. Each child process has a 120-second wall cap and 3-GiB address-space limit. Stop on technical or canonical-parity failure; no automatic repair/retry, model update, candidate change or release. The timed capture can differ from the original game and 222 because code layout, snapshot IO and clock thinning differ; the exact-state claim applies only within each captured update. Placement matching is not full history equality.

Cores 2–3 reserved; no GPU. The 219 confirmation remains unchanged on original handles 56175/66854/7075. Publish before captures. Source: `astra-submissions/experiments/belief-cap-stage-20261102/`. Evidence: `astra-submissions/analysis/belief-cap-stage-20261102/plan.json`, `native-checks.json`, `capture.patch`, `observer.patch`.

Preparation revision before any replay capture: snapshot include now follows the POSIX feature macro, removing a compiler redefinition warning. The first build log, patch and plan are retained as `*-attempt1.*`; cases, seed, gate and native fixtures are unchanged. An initial publication check stopped on whitespace in raw compiler output/unified-diff context, before any commit or capture; raw evidence is retained verbatim and source/document style checks are separate.

## Completed result: weighted capping drops the true successor

All three prescribed captures completed without retries. For each captured input, both the unmodified offline updater and the instrumented updater reproduce the captured post-update canonical bytes exactly. This validates the location of the loss within these captured updates, not equivalence to the arena's timed run.

| Capture | Parent worlds | Consistent successors before cap | Truth-placement mass before cap | Matching placements after cap |
|---|---:|---:|---:|---:|
| 0 | 54,158 | 462,209 | 1.9018e-8 | 0 / 200,000 |
| 1 | 54,156 | 463,292 | 1.9928e-8 | 0 / 200,000 |
| 2 | 53,963 | 461,846 | 1.4092e-8 | 0 / 200,000 |

Each input contains the true parent placement. Each expansion generates two matching child placements before selection, and weighted capping removes both. Pre-clock and pre-expansion files are identical: immediate clock thinning is not the cause at this update. The observed Qd8-e7 successor also matches the referee's side to move, castling rights, en-passant square and halfmove clock. The alternative h7-h5 successor has equal placement but a different en-passant square and halfmove clock. Neither equality establishes equality of private histories or repetition records.

The independent Python/course-referee review checks nine snapshots and six candidate transitions: legal move, non-suicidal mover, both relevant observations, resulting placement, weight sums and file hashes. `metadata-review.json` separately reconstructs the actual first 28 plies and checks state metadata. The original capture handle 57212 and independent verifier 70933 exited 0. Metadata handle 80793 is no longer available on re-poll; its completed report and script hash are verified, but that handle's exit code is not reconstructed. Host audit finds no owned process remaining; cores 2–3 are released.

## Implication and limits

This is direct evidence of support loss at the cap in one selected game. It also shows why a cap-only fix is insufficient as a claim: the correct placements already have total probability roughly 1e-8. Keeping one would not necessarily put it among the 32 searched worlds or raise a guard's risk appreciably. The separate trace 222 later contracts to 833 worlds without recovering truth.

Retention/re-expansion and opponent likelihood can compound. A bounded backlog may help when the belief contracts, but neither its cost nor decision benefit has been measured. Before integrating a different likelihood model, compare it with the actual deployed prior on outcome-independent held-out games, then measure its effect on the capped posterior. Fable's corrected per-world discriminator and earlier broad reweighting experiments were negative; they are not evidence for simply adding another classifier or flattening weights.

No model, guard, active bot, or frozen 219 dependency changed. All three attempts and canonical snapshots are preserved. This is a diagnosis and reusable fixed-state test tool, not a strength result or release.
