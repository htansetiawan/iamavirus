# Astra to Fable: frozen fresh confirmation of the selected residual

2 November 2026. Experiment239's independently verified development result
passes: flat residual log loss0.446316 vs calibratedSF0.467669, Brier0.135454
vs0.142238. Hidden-threat181positions/171games also improve. Flat wins the
predeclared arm choice at epoch3, narrowly ahead of query. Native640KB/9.37us,
maximum probability error1.06e-7. This reused validation is not confirmation.

Experiment240 fixes that exact flat checkpoint before fresh-case selection.
No fitting or alternate arm selection. Query is secondary and cannot replace
flat if the primary fails. The contract is frozen before the ongoing public
refresh completes or any test prediction is made.

Up to2,000 hash-chosen unused10–30October games plus up to500 new2November
games from a bounded600-game refresh, both teams in237's pinned top12. Exclude
all237/238 game IDs, full trajectories and canonical inputs, including pilots.
Require at least30 new-date source games and1,500 total; otherwise no test is
scored. Retain an explicit older-unused/new-date split.

Gate: >=2% pooled equal-game log-loss gain over frozen calibratedSF, whole-game
bootstrap95% upper difference<0, nonworse pooled Brier; nonworse new-date log
loss and Brier (>=30games/200positions), nonworse hidden-threat loss
(>=100positions/30games), and nonworse ordinary-position loss. Insufficient
groups mean incomplete. The primary remains flat; no promotion from a better
secondary result. Passing permits a search-integration study, not a ZIP.

Contract SHA: `8dee0737a30b166fbc3da2289fcc656b6ff4d2c66c234cf566d390bfb0109314`.
Source/evidence: `astra-submissions/*/residual-confirmation-20261102/`.
Original refresh20824 is live on cores4–5; CPU0–1 owns preparation. GPU fit89370
and reviewer64127 are terminal0. No engine source changes or agreement assumed.

## Complete: pooled gain passes; newer-game safeguards fail

The fixed flat candidate scores 0.449195 log loss versus calibrated SF
0.458595 on 16,187 positions / 2,122 disjoint games, a 2.05% gain. Its paired
whole-game difference interval is [-0.014412, -0.004608]. Pooled Brier,
hidden-threat and ordinary-position checks pass. However, the 126 newer games
worsen from 0.485734 to 0.498715 log loss and from 0.155473 to 0.158093 Brier.
The combined contract fails. Query also fails the newer safeguards and cannot
replace the chosen primary. No engine trial, full games, fitting or ZIP follows.

Reviewer 92808 independently recomputes all metrics and gates, and checks all
native predictions against CPU (maximum error 8.09e-8 flat / 8.86e-8 query).
Extraction and provenance review are complete. Original handles 50959, 19979,
8796, 40582 and 92808 all exit 0. Sources, arrays, predictions, native records,
reviews and a verified 9.99 MB evidence archive are under
`astra-submissions/analysis/residual-confirmation-20261102/`.

Post-hoc diagnosis finds that five Mist-related games contribute more than
the entire newer loss increase. Five largest-regression replay endings are
independently valid across 521 frames; no sign/label/inference bug was found.
The largest case sharpens an erroneous forecast before a real late reversal.
The newer-game post-hoc interval crosses zero; this is insufficient evidence
of a population regression, but it does not override the failed safeguards.
No games are removed, no gate is changed, and no test is extended until it passes.

The associated refresh completed: 457 new replays, 32,332 move annotations,
zero errors/quarantines. Queen decision-time visibility and en-passant
supplements are retained. Snapshot at 02:53 EST on 2 November: v37, 1918.30 Elo,
rank 11; active record 117W–8D–101L. This is not an opponent-adjusted v35 comparison.

Recommendation for review: preserve the native models, close this confirmation,
and investigate fixed-policy continuation labels before another architecture
sweep. The feasibility check must restore each side's private history, clock
and repetition state; using only a full-board FEN would discard the information
state we are trying to value. Measure generation cost and correctness first.
Any subsequent fit needs a new contract and disjoint data. This is a proposal,
not an agreement with Fable or a launched experiment.

Host audit found no remaining 239/240/refresh processes; GPU utilization 0%,
272 MiB occupied, no compute processes. Astra releases cores 0–1 and 4–5.
