# Temporal opponent prior: bounded predictive pilot

1 November 2026. No engine candidate or strength claim.

Hypothesis: the mover's recent own actions help predict otherwise
observationally indistinguishable moves. The current static 39-feature model
already includes visibility; the exact history table cannot smoothly
generalize to unseen sequences.

Freeze 1,200 training games (Oct20–27), 300 validation (Oct28–29), and 600 test
(Oct30–31), selected by a fixed game-ID hash from reference/strong opponents.
Use both colours, no outcome selection, no our-team training actions. Dedup
complete move sequences across splits. Inputs record provenance and exact
move/view/board traces. Compare models fitted on the identical training set:

- Static: current 39 features plus from/to piece-square tables.
- Temporal: static plus previous own piece × current piece, same-piece move,
  same piece after capture, return to its previous square, continuing a
  repeated-piece sequence, consecutive captures, and previous capture value.

Both are conditional logits normalized over **all legal actions**. Fixed
L2 = 1e-4, zero initialization, convex L-BFGS fit (maximum 150 iterations).
No hyperparameter selection or codebook in this pilot. Hash frozen parameters
before touching test scores. Validation may close a clearly negative line;
positive validation requires >=0.02 nats improvement on ambiguous conditional
move likelihood and no >0.005-nat all-move regression to earn test evaluation.
Test confirmation requires a positive whole-game bootstrap lower bound on the
ambiguous improvement, no >0.005-nat all-move regression, and no >0.01-nat
regression on pooled Instructors/duck/HYPOTHERMIA ambiguous moves.

The conditional metric renormalizes over moves producing the same next view
for the other side **only at evaluation**, excluding terminal actual moves.
Also report the unconditional probability of the actual move and of its
observation class. Training never conditions its denominator on the observed
next view. Report singleton vs ambiguous classes, by opponent and colour.

All histories here are known training trajectories. This is a true-parent
predictive experiment, not a belief filter or a deployable oracle. A positive
result earns a separate hypothesized-history implementation and capped-belief
test. Histories merged into one board require explicit approximation or a
mixture; a rebuild must mark history unknown. No hidden recorded moves may be
fed to an online engine.

Native feature state contains only the previous own action for each side,
its post-promotion piece type, captured value, and whether it continued the
same piece. The most recent action of the *other* side continues to feed the
existing recapture feature. Captures, en passant, castling, promotion, both
colours, initial/unknown histories and chronology are tested. Full replay
boards and both observations must match the native reconstruction.

Reserve cores0–1 and the free GPU for at most two hours; no service is stopped.
Raw pilot features are temporary, capped at1.5GB, because external drives are
unmounted and SSD space is limited. Retain compact source, input traces,
manifest, fitted coefficients and per-decision scores for reproduction.

Before fitting or scoring, the initial split audit found two validation and
five test games overlapping the earlier king-calibration corpus. `data-v2/`
excludes every game and complete sequence in that 140-game plan, then fills
the original counts by the same deterministic hash order. The initial
manifest/extraction receipts remain as an audit record; no model was trained
or evaluated on that initial validation/test split. Training input is
unchanged. Use `data-v2/` for this experiment's fit and evaluation.
