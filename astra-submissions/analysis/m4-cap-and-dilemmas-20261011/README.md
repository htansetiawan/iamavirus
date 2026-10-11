# Cap correction rejected; a structural hidden-queen trap

This checkpoint records offline belief measurements, forced-decision probes,
and an exact local tactical certificate. It does not establish a stronger bot.
No active engine, submission archive or arena version was changed.

## Weighted-cap experiment

The previous visibility-prior experiment was rejected. This experiment fixes
the refitted 26-feature prior, seed 41, cap 10,000, and historical observations
and moves. A frozen generated `belief-cap.c` changes both cap sites without
editing shared `belief.c` or headers. The actual environment modes are:

- `0`: original full-sort selection and weights;
- `1`: bounded-heap selection, original weights;
- `2`: the same heap with threshold-conditioned importance weights.

Modes 0 and 1 agree on every non-timing field across all 1,680 decisions. All
rule labels agree with the independent referee. The primary cohort excludes
one added diagnostic game: 42 games, 1,650 decisions.

| Primary cohort | Original | Heap only | Corrected weights |
|---|---:|---:|---:|
| True board present | 1,386 | 1,386 | 1,347 |
| Belief collapses | 13 | 13 | 16 |
| Hidden-attack Brier | 0.0141242 | 0.0141242 | 0.0141766 |
| Historical fatal-move Brier | 0.0099352 | 0.0099352 | 0.0098829 |
| Update CPU seconds | 42.971 | 42.546 | 43.452 |

Corrected weighting's Brier differences have whole-game bootstrap intervals
crossing zero. True-board coverage falls and collapses rise. **Reject runtime
integration and further real-clock spending on this variant.** The small
heap-only timing difference is not a meaningful end-to-end speed claim.

The cap mathematics remains valid as a toy-distribution result; it did not
predict a useful replay improvement. See `cap/seed41/report.json`, retained
rows and input manifests. C `ab7eded` adds the shrink integration fixture;
ASan/UBSan checks preserve positions, histories, RNG and compaction across
the first sample, changing only weights in mode 2.

## One observation, incompatible defenses

Public replay [qkb2exm9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qkb2exm9)
is arena v30 White against duck v5:

```text
e4 d5 exd5 Qxd5 d4 Qa5 Be3 — White loses, king capturable
```

After `d4`, eight queen replies produce the same White observation. The queen
can be on a5, e4, e6, d8, c6, d6, f5 or d7. There is no White response that
survives all eight positions.

| Hidden queen | Immediate-survival responses |
|---|---|
| a5 | Ke2, Qd2, Bd2, Nc3, Nd2, c3, b4 |
| e4 or e6 | Be3, Qe2, Kd2, Be2, Ne2 |
| d8, c6, d6, f5, d7 | All 37 legal responses survive immediately |

The first two defense sets are nonempty and disjoint. An equal attacker mixture
over Qa5 and Qe6 forces at least 50% immediate loss in this conditional response
game. An equal defender mixture over Be3 and Nc3 achieves at most 50% against
all eight worlds. This proves the **local one-response minimax loss is 0.5**.
It is not a full-game value, nor an estimate of duck's strategy.

Uniform weighting instead gives a minimum loss fraction of 1/8, favoring the
file-blocking defenses which lose to Qa5. More accurate enumeration alone
cannot supply a universally safe defense. Avoiding the information dilemma
earlier is a separate strategic skill.

The actual observation changed when the queen left d5; a zero-change-only
hidden-check detector would miss this case. The pattern is defined by observed
equivalence and incompatible defenses, not by the player's name.

## What the current C search already does

Frozen candidate `5892c2a9015395de2f541f954d3d3edc06b9217d9c7291913fd01d9d23949ab0`,
Stockfish `0f83d24cc46d2c66c60f16001af5444873bc112b7d028594513426894c12da19`,
seed 21, configured one-second searches, 32 initial roots, fast roots, no
settling/dominance/witness intervention:

| Historical decision | Cold prefix | Warm prefix |
|---|---|---|
| White before d4, exact singleton | Qe2, safe | Qe2, safe |
| Black after d4, exact singleton | Qe6, hidden file check | Qa5, hidden diagonal check |
| White after Qa5, eight worlds | Ne2, fatal on actual board | Be3, fatal on actual board |

The current C search already avoids the setup and finds an offensive trap in
these probes. This is **not a newly repaired bot behavior**. Cold/warm also
differ in prefix search and evaluator state; they do not isolate a carry
mechanism. All forced-prefix probes completed without an evaluator failure.
`queen/` contains the exact observations, results, root traces, defense matrix
and full local proof.

## Structured corpus and faster curation

The first corpus selects all uncapped, truth-supported singleton decisions at
plies 2–12 from the frozen replay batches: 30 eligible decisions, 20 distinct
complete positions, all 719 legal setup actions. Three setup actions have a
group without a common immediate defense: Ke2, d3 and d4, all in the same
position after `e4 d5 exd5 Qxd5`. Eight immediate terminal actions are separate
labels. This is a small regression corpus, not broad strategy-learning evidence.

The new standalone C labeler (`mist-c`, commit `4f2dce8`) matches all relevant
group fields for those 719 actions and ten additional both-color rule fixtures:
30 positions, 807 actions. It takes 0.104550 CPU seconds in the optimized run;
ASan/UBSan produces identical labels. This is a partial-output throughput
measurement, not a like-for-like speed ratio against the richer Python forensic
report. No bot code links the labeler.

Native grouping sorts reply observations, then uses directly indexed move
counts with generation stamps. There is no pairwise scan through all existing
groups, and no full move-table clear per group. The Python layer still recovers
full safe sets and exact minimax witnesses for native positives.

`corpus/provenance-addendum.json` records a post-run check that the originally
imported starter referee matches the independently frozen referee bytes. It
does not pretend the original curator froze that module before running. The
curator now records and copies it for future runs.

## Expanded corpus: completed

The pre-existing 352-game validation split was scanned, both colors and the
first 13 plies, without a result filter. A prior-disabled observation-only
tracker produced 4,517 decision rows. Its 443 eligible singleton decisions had
no previous cap, collapse or recovery and represented 279 distinct positions.
The native tool labeled all 8,839 setup moves in 1.166 wall-clock seconds.
The complete process, including Python regeneration of every positive, took
27.844 seconds. These timings describe this offline workflow, not arena latency.

There are 490 immediate terminal actions and 46 nonterminal setup actions with
at least one future observation group lacking a common survival response.
Of those, **29 are information conflicts where every individual world remains
escapable**, across six distinct positions. The remaining 17 include a
physically forced loss, so they are not evidence of information asymmetry alone.
None of the 29 setup actions was the historical move at its sampled decision;
these are counterfactual structural labels, not 29 observed blunders.

Exact rational certificates cover all 29 information-conflict groups:

- 20 have local immediate-loss value 1/2, with two-action mixtures.
- 9 have value 1/3, with three-action mixtures.

The three-way cases matter: pairwise-compatible defenses can still have an
empty three-way intersection. In position `31bbbb7f484dd46d`, after Kd2,
the queen replies Qg5, Qf5 and Qa5 are indistinguishable. Every pair of reply
worlds has some common safe defense, but all three do not. Uniformly mixing
these attacks forces at least 1/3 loss; a uniform mixture of b4, Kc2 and f4
bounds loss by 1/3 across every world in that observation group. The certificate
checks both bounds over the complete local payoff matrix using exact fractions.
It does not equate this restricted game to the complete chess game.

The first attempted run stopped on game `28ddn2g7`, a legal f5g6 en-passant move
that the one-view conservative move generator cannot establish. All 1,576
history-consistent worlds do establish it. C commit `a521bf8` fixes the
**offline replay guard** to accept such a move only when it is legal in every
retained world, matching the runtime's existing fallback. Truth is not used
by the guard. The first failure and unchanged selection are retained. The
counterfactual f5e6 is rejected; 46 control replay rows remain identical except
timing. Shared belief and runtime source are unchanged.

`expanded/` retains full selection provenance, tracker inputs/rows, native
labels, independently regenerated positives, and `certificates.json`.
`m4_dilemma_certificates.py` searches deduplicated payoff patterns for small
uniform mixtures, then independently verifies rational lower/upper bounds.
Failure to find a certificate would not establish absence of an equilibrium.

Next: probe the current C search on these six structural families before adding
a runtime penalty. The original queen fixture already passes the earlier-move
and attacker-side checks, so its rediscovery alone would not justify a release.
Any detector should cover higher-order conflicts, retain prior/history
provenance, and pass actual games before a strength claim.

## Public arena refresh

At 15:15:45 UTC, the public snapshot reports arena v30 at 1765.24 Elo,
134W–22D–159L/315. The 23 newly cached games are 9W–14L, including duck win
`h21bwry5` and Greek Gift win `po23rp14`. These are results of the currently
submitted v30, not of the offline changes here. The cache is raw public data;
this checkpoint does not claim every newly downloaded frame was independently
audited. See `arena/latest.json` for timestamped records and source locations.

Large frozen binaries and original logs remain under the corresponding
`/media/henrytan/seagate/iamavirus/astra/m4-*-20261011/` directories. Compact
inputs, outputs and provenance are retained here with `inventory.json` hashes.
