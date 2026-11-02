# 231: compare move-likelihood and posterior-likelihood training

230 verified the transition objective and exporter. Now keep the model capacity
fixed: a26-parameter linear residual on v37's full move prior, initialized at
zero. Compare ordinary recorded-move likelihood with one-step posterior
likelihood. Same games, cases, regularization choices and optimizer. History
blend, transition temperature2, cheap prior, cap and all guards remain fixed.
No228 fitted weights are reused.

Use400 training games from20–31 October,80 validation games from1 November
00:00–20:00UTC, and up to80 later test games from20:00UTC through the frozen
refresh snapshot (minimum30). Games must contain one of nine reference teams.
The reference team is the predicted actor; choose the other colour as observer.
When both are reference teams, a salted hash chooses the observer. No team ID
is a model input. This tests a general prior from permitted replay histories,
not IAmAVirus's policy or arena head-to-head performance.

All outcomes, salted selection and complete-sequence deduplication. Exclude
228/226/224/230/fresh-panel games and sequences. One observer per game. Reuse
230's exact-prefix rule: export1–256-parent updates, stop when the baseline
exceeds4,096 worlds, caps or empties. Keep at most12 hash-selected cases per
training game; all eligible validation/test cases. This does not represent
capped middlegames. Do not insert missing truth; disclose unsupported cases
and retain them with a1e-12 probability floor in evaluation.

Ordinary move loss averages the recorded action probability across naturally
retained true-parent histories. Posterior loss sums every consistent transition
to the true successor merge class. All legal moves remain in each parent's
normalizer. Incoming baseline weights are fixed: this is one-step training,
not differentiation through whole trajectories. Give games equal total
training weight. Both heads have exactly26 coefficients; no network/codebook.

Fit Adam, learning rate0.03,60 full-batch steps, seed2311102, ridge0.001 and0.01
for each objective. Select checkpoint/ridge on validation posterior NLL over
nontrivial updates; write selected coefficients and hashes before extracting
test cases. Log every five steps and preserve all curves. Test is evaluated
once. CUDA when a fresh check finds no competing compute process; otherwise
CPU, with the selected backend shared by all fits and recorded before fitting.

Frozen predictive gate: primary test uses nontrivial updates (multiple
contributing parents and multiple successor worlds), equal weight per game.
Require posterior-trained gain over v37>=0.10nats, a positive whole-game
bootstrap95% lower bound, gain over the matched move-trained model>=0.05,
no more than0.02nats degradation on late updates(ply>=16) or at least20 surprise
captures in the primary set, no all-update posterior regression and no support
failures. Report ordinary action likelihood as a diagnostic, not a new
post-hoc gate.2000 bootstrap draws, one seed. All conditions apply.

A pass permits a separate actual sequential-filter experiment. It does not
permit a ZIP, arena upload, clock/guard changes or a strength claim. A failed
gate is not reopened by retaining a subgroup or fitting to its test set.

Native baseline probability parity<=5e-6 and log parity<=5e-5, vectorized versus
loop gradients and independent actor-loss checks precede training. Feature
arrays stay in memory, bounded2GiB per split; retain manifests, hashes, small
coefficients and scored rows. Max45minutes, cores2–3, no service interrupted.
Publish source and the exact game manifest before the single run.
