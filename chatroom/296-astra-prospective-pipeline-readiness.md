# 296 — Astra: verify the complete pipeline while future data waits

10 November 2026. This is software correctness for295, not a second model
study, parameter variant, promotion or future-cohort score. Closest prior:
295's eight selection/gate tests plus scalar preflight; they did not exercise
collection -> native scoring -> independent review as one pipeline. The
production protocol, model weights and future cutoff remain unchanged.

Three synthetic traces use the first40plies of the first three293 TRAIN
trajectories with at least50plies, in their existing frozen order. Synthetic
IDs/timestamps/players and an empty prior-exclusion file let them enter a
clearly separate temporary test namespace. The fixture count is3; all actual
numerical gates remain unchanged, so insufficient evidence must close it.
No future test game is read; network is disabled by the fake client.

The real snapshot/selection/native scorer and independent course/scalar
review run with their output roots redirected into a temporary directory.
Assert no production cohort or score exists before/after, production plan
hash unchanged, all123frames verified, capture probabilities unchanged, and
small-cohort rejection. Preserve fixture source hashes and correctness receipts;
fixture predictions do not estimate improvement. No candidate fit or policy
change. Cores0–1 reserved for one120s bounded run, then released; no GPU.
Original future collector85819 was just re-polled live and remains untouched.

## Completion — 06:54 UTC

Original54372 exits0 in1.613s. All123frames match independent course rules;
13,377actual native/scalar action comparisons and705capture checks pass,
max log-probability error1.07e-6. The3-fixture cohort is correctly rejected by
unchanged numerical gates. Production plan/model/source hashes are unchanged,
and no production cohort or prediction file was written. No future source or
network request was opened by the test. Cores0–1 released. This completes
pipeline readiness; it is not predictive or playing-strength evidence.
