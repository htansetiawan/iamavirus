# Fixed full prior: whole-history result, 10 November 2026

**Closed for promotion.** All 288 original calls and the independent audit finish
successfully; two quantitative conditions fail. No replacement ZIP, version
reservation, duel or arena change follows. The already uploaded v38 stays active.

Original session 43303 ran once from 17:24:39 to 17:48:58 UTC (24m19s), including
the independent review. Its terminal exit is 0; the runner distinguishes successful
execution from the negative research decision. Cores 2–3 are released.
Source/plan publication: `7fbcb96386b24241a7019ea94a97763b0ed95c7c`.

| Fixed measure | Original | Learned | Gate / decision |
| --- | ---: | ---: | --- |
| Primary seed/decision rows | 3,520 | 3,520 | 1,760 distinct game/ply pairs; covered |
| Mean truth NLL | 6.927142 | 6.824795 | Gain **0.102347 < 0.15**: fails |
| Game-clustered 95% gain interval | | [-0.003363, 0.218712] | Lower bound not above zero: fails |
| Supported truth rows | 3,393 | 3,405 | Pass |
| Collapsed game/seed traces | 2 | 2 | Pass; no pre-cap truth loss |
| Total native update seconds | 451.781 | 454.533 | Ratio 1.006090, below 1.20 |
| Update p95, seconds | 0.167510 | 0.170289 | Below max(0.1, 1.5×baseline) |

No-clock-thinning forced trajectories, not whole-turn timings or games played by
our policy. Of 48 observer seats, only two are IAmAVirus. The games came from 321's
already one-step-evaluated cohort, so this is a sequential development test, not
independent posterior confirmation. Both explicit belief sampler states are
clustered within game for the bootstrap. Original and zero-head controls agree
on every non-timing field and ordered population/history/weight/RNG fingerprint.
All 166 frozen dependencies and 25,374 raw emitted rows pass the audit.

The three priority groups have nonnegative gain: Instructors +0.349981, duck
+0.237631 and HYPOTHERMIA +0.064614, eight games each. Greek Gift is +0.056562,
Knight Vision -0.079876 and Strongly Invisible -0.001092. These are diagnostics,
not a basis to select opponents or rescue the failed aggregate. Gains at mass
floors 1e-9 / 1e-12 / 1e-15 are +0.078563 / +0.102347 / +0.125896.

## Literal native guard diagnostics

All 3,520 primary risk rows stay in the score, including unavailable predictions
at the fixed 0.5 fallback. Availability is 3,502 for both arms. There are 33
distinct positive king events and 25 queen events. Targets are the deployed
single-board king and queen exchange predicates, including their known promotion
limit; they are **not actual future material-loss or win labels**. Negative Brier
deltas are better. The four observed tolerances pass; that is not a statistical
no-harm guarantee.

| Predicate / weighting | Brier delta | Paired game 95% interval |
| --- | ---: | --- |
| King, recovered weights | -0.000713928 | [-0.001511747, -0.000037881] |
| King, sharpened weights | -0.000200247 | [-0.002042033, 0.001637843] |
| Queen, recovered weights | -0.000248008 | [-0.000693296, 0.000112149] |
| Queen, sharpened weights | -0.000594457 | [-0.001433278, 0.000044719] |

Diagnostics leave P and its RNG unchanged; zero illegal sampled actions. Both
arms have 3,307 full updates, and 39 baseline games reach the large regime.
Cheap/full cutoff, history, temperature, cap, pruning and guards stay unchanged.
No speed backport, search, GPU, fit, failed-disk access or recovery after collapse.

## Consequence

321's future action-prediction pass and 322's native correctness pass remain
valid. This test does not establish enough sequential benefit for the next
clocked decision study. Close this fixed configuration without a seed, threshold,
temperature, opponent subset or full-at-all-sizes retry. It does not prove learned
priors cannot help; prediction gains need not turn into enough posterior gain.
The separately failed 320 teacher portability requirement remains failed too.

[Result](result.json) · [independent audit](independent-review.json) ·
[terminal receipt](terminal-receipt.json) · [contract](../../../chatroom/323-astra-fixed-prior-sequential-contract.md).
