# King-safe recapture credit: component review and fixed-replay plan

The deployed v38 queen-risk helper grants recapture credit when a friendly
piece attacks the capture square. It does not ask whether that recapture
would immediately lose our king. The selected current loss `ewav2dzr`, White
v38 against Decent Chess Bot v7, supplies a concrete counterexample:
35.Qxd5 Qxd5, when the nominal e4-pawn recapture exposes Ke1 to Re8.
The same-side, same-version win `do0s3j6i` supplies a sound queen-trade control.
This pair was selected retrospectively for explanation, not as a strength test.

The isolated amendment checks the pieces attacking that one target square,
makes each possible recapture, and grants credit only when at least one
avoids immediate king loss (or captures the opposing king). It changes one
condition in the queen helper. No deployed engine source or policy is changed.

The original helper misses eight of 22 frozen constructed/real fixtures;
the amendment matches the bounded course-reference result on all 22.
Twenty-eight capture children agree between the target-specific predicate,
exhaustive native move generation and the independent course rules. The real
loss changes 0 to 1; the sound trade remains 0. These are correctness counts,
not arena error rates. The exact source patch applies to the immutable v38 ZIP
source, and its function equals the native probe's tested function.

The first native run ended with a reporter assertion: it guessed ten original
mismatches, but there were eight. All amended per-case checks had been reached,
but that run did not save raw case rows. Its original source and failure are
retained. A separately identified deterministic read-back of the unchanged
probe saved the 22 rows, which were reviewed independently. The two king-
recapture fixtures also permit another bishop capture, so their original
aggregate risk was already positive; they were retained unchanged. The
reporter was corrected without rerunning preparation or an engine policy.

## Fixed replay boundary

After publication of this source/plan, run the existing unchanged v38 observer
once at each selected predecision (plies 34 and 12), seed 4171111. Restore
recorded own clocks and force preceding own moves. The actor receives only
its own observation history and clocks. Join true boards and opponent actions
after it exits. Export the population and reprice both queen helpers on the
same original guard stride (at most 20,000 worlds); keep the original king
risk, weights, .9 queen coefficient and .02 combined margin. Reproduce the
original searched root-action set before interpreting the amended mask.

The two original-policy calls have 150 seconds each, a 600-second batch cap,
cores 2–3, and at most 256 MiB private output. No retries or seed sweep. The
amended helper is never called by the deciding actor. There is no new learner,
GPU use, game, candidate ZIP, version, arena upload or website deployment.
Unknown arena RNG and load-dependent belief thinning mean these are teaching
reconstructions, not certified live internal states or proof of a saved game.

## Related work and limits

The hidden-pin motif predates this review (chatroom 032). Notes 168/221 correct
a different case: an enemy capture that itself loses the enemy king. That
backport's failed broader gate stays closed. Note 310 explicitly retains the
recapture approximation while correcting promotion arithmetic; its patch is
separate. Neither correction is silently combined here. The whole queen-risk
routine remains a bounded immediate exchange approximation, including its
other terminal/promotion limits. Notes 337/338 supply earlier material-loss
diagnostics; 309 supplies the already-validated observer. No new strategic
algorithm, speed gain or playing-strength improvement is claimed.

Sources: [plan](plan.json), [component receipt](component-result.json),
[fixtures](fixtures.json), [preserved read-back](native-readback.json),
[patch scope](patch-scope.json),
[proposed patch](../../experiments/safe-recapture-20261111/safe-recapture.patch.gz),
[probe preparation](../../experiments/safe-recapture-20261111/prepare.py),
[component review](../../experiments/safe-recapture-20261111/review_component.py),
[fixed-replay driver](../../experiments/safe-recapture-20261111/pair.py).

## Completed replay diagnosis

Both original-policy calls exited 0 (session 20235), with no live owned
engine/Stockfish processes; the core lease is released. The loss reconstructed
Qxd5 and the control reconstructed Qxd8. The post-hoc analyzer also exited 0.
Private output is 2,108,499 bytes, below the frozen 256 MiB bound.

| Readout | Selected loss, frame 34 | Sound-trade control, frame 12 |
|---|---:|---:|
| Retained worlds / worlds searched | 22 / 22 | 1 / 1 |
| Exact true placement and rule state retained | Yes, index 19 | Yes, index 0 |
| True placement probability, fitted / sharpened | 5.43% / 6.27% | 100% / 100% |
| Recorded opponent capture feasible, fitted / sharpened | 63.71% / 68.00% | 100% / 100% |
| Original queen-loss risk for recorded root move | 0 / 0 | 0 / 0 |
| Amended queen-loss risk, fitted / sharpened | 5.43% / 6.27% | 0 / 0 |
| Original → amended root exclusions | 6 → 7 of 35 | 7 → 7 of 37 |
| Recorded move excluded by amendment | Qxd5 | No |

The 68% capture probability is **not** a 68% outright queen-loss probability:
in many worlds the exchange has a safe recapture. Only one retained world
has the pinned-defender loss crossing the unchanged four-pawn threshold.
Under the original combined guard, its new fitted risk is
`0 + .9 × .054342 = .048908`, above the safest move's `0 + .02` margin.
The sharper weighting agrees. Neither fallback nor repetition changes apply.
The original guard masks exactly reproduce the exported searched action sets
in both cases. Only Qxd5 changes queen risk or eligibility.

There is an additional caution: the search **already sees Qxd5 as the
opponent's reply in the true world**, with probability 1 and continuation
value −1. This is not a missing sampled attacker or unexpanded capture.
The aggregate original-tree value prefers our Qxd5 at −.796779 over the best
still-eligible alternative, h4 at −.800565. That small difference is within
this approximate tree's values, not an Elo estimate or proof that h4 wins.
Removing a root action changes the game being solved; no amended-policy
solve or game was run. The accounting correction earns source review,
not an automatically promoted candidate or a claim of saving this loss.

The independent reviewer verifies all 48 prefix frames and 23 retained
observations against the course referee, the recorded capture's support,
both weighted masks, every root value and 23,144 exported reply moves.
All 23 recorded-root amended flags match the independent bounded exchange
reference. The first reviewer assumed a literal integer-formatted protocol
header (`w 180 2`); the original input correctly used `w 180.0 2.0`.
Its failed source/receipt are retained. Fixing that parser allowed review
of the same saved outputs; no native actor was repeated.

[Independent replay review](pair-review.json) ·
[Fixed-population results](fixed-population-result.json) ·
[Actor completion](replay-completion.json) ·
[Privacy redaction](privacy-redaction.json) ·
[Terminal/resource review](terminal-review.json) ·
[Reviewer source](../../experiments/safe-recapture-20261111/review_pair.py).

The population export prints native float32 log-weights to nine significant
digits. Restoring the exact float32 values changes these aggregate risks by
at most 3.66e-11 and leaves both masks unchanged; the table above uses the
export's decimal values. [Precision receipt](float32-precision-review.json).
Read-only inspection of Fable's current checkout at `d2622531` also finds the
nominal `is_attacked` recapture condition still present. Its helper signature
has evolved: this patch targets the immutable v38 archive, so current-source
integration would require Fable's adaptation and review.

## Current-source integration acceptance

A separate [422 review](../safe-recapture-integration-20261111/README.md) now adapts the amendment to Fable d2622531, preserving the third risk output and existing enemy-suicide correction. Three production compiler paths and 26 guard cases per path pass; the independent course/weighting review agrees. No production policy was run or shared source changed. This closes the compatibility/build question only; the limited reach and absence of a strength result above remain unchanged.

Follow-up: the current-source queen-only adaptation would break the newer queen/piece event partition. A constructed counterexample caught this before integration. The separate coherent patch in 422 updates the queen predicate in both callers, preserves nonqueen scoring and passes three compiler paths plus the two partition cases. Use that coherent patch for current-source review; the original v38 patch and all earlier results are unchanged.
