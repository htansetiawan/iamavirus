# Neural and particle danger: measure complementarity before integration

The full-data small-attention model improves unfiltered policy safety, but its
actual hybrid terminal decisions tie the CNN. The current engine uses neural
danger only for some candidate-ranking ties. The next hypothesis is that this
head detects threats absent from the particle population and can improve a
calibrated estimate of immediate king loss.

This first experiment changes no playing decision. It tests prediction quality
and complementarity before adding a penalty or veto. Calibrating one scalar
does not make hidden-piece marginals a legal joint posterior.

Freeze the 6,000-update small-attention model from the full 3,766-game run,
features-v2, prior 1, 2,048 particles, prediction/history/frontier 0, seed 777.
Use the already frozen weighted-frontier runtime with the frontier disabled.
Add only a public diagnostic accessor forwarding to its unchanged king-risk
function. The native process receives actor observations and past own actions;
it never receives replay truth, opponent moves, outcomes or danger labels.
Advance both recurrent and particle states through every delivered observation.
Score every fourth own decision, equally for both colors, without oversampling
losses. Join truth labels afterward by game, side, event and legal move.

Choose 64 calibration games and 64 evaluation games from the frozen v4
validation shard. Exclude the 64 architecture-pilot games and every duplicate
trajectory of those games. Keep whole games together, reject any training
trajectory overlap, and select one representative per remaining trajectory by
a fixed SHA256 ordering with namespace `neural-risk-v1`. The test shard remains
unread. These are development-validation partitions, not a pristine final test
for the whole project. Record the exact selections before fitting anything.

Compare raw particle probabilities and raw neural probabilities with three
small logistic calibrators: particle log-odds alone, neural logit alone, and
both together. Clip particle probabilities to [0.0001, 0.9999], standardize
features using calibration data only, constrain slopes nonnegative, and fit
binary cross-entropy with slope L2 penalty 0.001. Each decision contributes
equal total weight, divided among its legal candidates. Keep the intercept
unpenalized. No hyperparameter sweep or evaluation-driven feature selection.

Primary comparison: fused versus calibrated particle-only decision-weighted
log loss and Brier score on evaluation games, with game-level paired intervals.
Also report calibration-fitted operating thresholds at 1% and 5% false-positive
rates and their actual evaluation false-positive rates and recall. Break down
zero-particle-risk candidates, king moves, and early/middle/late play. These
subgroups are diagnostic, not additional promotion tests. Preserve natural
decision frequencies, invalid-label counts and all denominators.

Only a useful complementary signal earns an engine integration experiment.
That experiment would keep the raw estimates in the log and separately compare
the calibrated risk in root evaluation. It must preserve legal moves and
opening safety, pass new held-out replay decisions and complete clocked games.
No deployment threshold comes from repeatedly inspecting terminal examples,
and no Elo claim follows from a probability metric.
