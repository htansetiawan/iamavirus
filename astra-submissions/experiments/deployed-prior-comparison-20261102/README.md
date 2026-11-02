# 224: compare the frozen response student with the deployed move prior

The actor-visible student passed a test against a 795-parameter research
baseline, not v37's move prior. Before paying for belief integration, compare
its predictive probabilities with both v37 models on genuinely later games.
No fitting, parameter selection, live candidate modification or GPU is needed.

Use the 455 opponent-only games acquired in the bounded 1 November evening
refresh, completed 20:36–23:33 UTC. Keep all eligible actors from the same nine
teams as experiment 208; retain all outcomes. Deduplicate complete sequences
within this cohort and against all 208 train/validation/test games. Record
every exclusion. These dates follow the v37 fit/table's 31 October export and
the student's training period. This is a short recent window, not a claim to
represent every opponent or the whole arena. Selection reads no model scores.

Pin the exact v37 extraction from 221, its history table, the fixed 208 native
student, the existing observable-fatal proof, and the course referee. Reuse
native model and history functions directly. Reconstruct the true parent and
both histories through actual moves for this **predictor** test; this is not
an actual capped-posterior test. Independently reconstruct the actor's legal
set from permitted history before scoring the student. Verify all frame boards,
views and legal sets, and verify native history hashes with a Python version.

Four fixed distributions: v37 full, v37 cheap, raw student, and the student
projected away from provably visible immediate king losses when an alternative
exists (the already-fixed projection used in search). Apply the same empirical
history blend, minimum count 3 and n0=4, to each. Save raw and blended scores.
The full model serves beliefs of at most 10,000 worlds; cheap serves larger
beliefs. No guessed dynamic switching is used here. These are untempered
one-step probabilities, not squared whole-trajectory posteriors.

Primary comparison is the **projected student plus history** versus **full
v37 plus history**, on non-suicidal recorded moves after own move eight, with
at least two legal actions. Non-suicidal conditioning matches updates where
the game continued; also report all moves separately. Compute move-weighted
NLL gains and whole-game bootstrap 95% intervals with 2,000 fixed draws.
Other arms, teams and 19 taxonomy slices are diagnostic; do not select a
different winner from the test results.

Advance only to a separately designed capped-posterior experiment if primary
gain is at least 0.05 nats, the interval's lower endpoint exceeds zero, and the
surprise-capture slice has at least 100 moves and mean gain no worse than
-0.02 nats. Otherwise close this model's blanket belief-replacement route.
This predictive gate cannot establish Elo or authorize a release. No automatic
retraining, mixture sweep or substitution follows a failed result.

One first execution, cores 2–3 only, no GPU, 15-minute wall cap, stop on technical
failure with the partial receipt retained. Publish the pinned plan before
scoring. Existing 219 match bytes/settings and frozen gates remain unchanged.
