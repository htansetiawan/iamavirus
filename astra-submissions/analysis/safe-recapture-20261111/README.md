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
