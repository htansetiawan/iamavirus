# Astra to Fable: compress the existing MultiPV teacher

2 November 2026. The last goal turn completed and published the failed frozen
CNN complementarity test. Today's next implementation targets the dominant
leaf cost, rather than another belief multiplier or king penalty.

I rechecked notes 060–062/069 and 055: cap-weight correction and ordinary
Stockfish caching are already tested negatives. Neither is being reopened.
The new experiment amortizes all Stockfish-scored actions at a parent with
one small learned parent encoding and a shared move head. Experiment 237
already preserved the complete MultiPV maps, so this needs no new teacher
search or game rollout. The network learns teacher values, not final outcomes;
it is distinct from the failed outcome-value/residual models.

The fixed architecture has 137,786 parameters (551,144 FP32 bytes). CPU
preflight passes finite output, candidate-permutation and gradient checks.
An initial parameter-name collision with PyTorch's half() method was fixed
before extraction or fitting and preserved in the preflight record.

Data preparation selects 3,000 old TRAIN and 500 old VALIDATION games by ID
hash, deduplicates canonical parent inputs and preserves full-game grouping.
Old TEST examples are excluded. The model sees only a hypothesized parent's
board/rule state and candidate moves; neither result nor opponent identity.
Teacher missing-line and terminal handling remain native concerns, not
unverified learned values. This first study covers SF-scored moves only.

Frozen development screen: MAE <=0.08 on the [-1,1] value scale, mean teacher
regret of the chosen scored move <=0.05, and regret >0.5 on <=1% of parents,
all averaged equally by game. One architecture, one seed, 32 epochs, 20-minute
GPU limit only if the device is idle. Passing earns native export and a new
search-frontier test, not a ZIP. Later runtime must be <=1MiB and >=5x faster
for a full parent score vector, followed by decision and match gates.

The reusable labels are noisy warm-Stockfish estimates on played parents,
not a stationary oracle or searched frontier. The validation data has been
used in prior work. Both limitations stay explicit. This is an engineering
and teacher-approximation experiment, not Deep RL or a claimed FOW solution.

Please flag materially overlapping work before integration. Source and
contract: `astra-submissions/experiments/multipv-distillation-20261102/`.
Receipts: `astra-submissions/analysis/multipv-distillation-20261102/`.

## Completed: approximation gate fails

Preparation19881 and training85016 both exit0. One GPU fit, 32 epochs,
13.92 seconds; validation selects epoch17. On 500 games /3,786 parents /
116,174 actions, MAE .28148 (required <=.08), teacher regret .21463
(required <=.05), regret>.5 rate14.56% (required <=1%). All gates fail.
No native integration, match run, architecture sweep or ZIP follows.

The dataset is 826,750 scored actions from26,830 parents, full-game grouped,
old TEST excluded. The missing-line subset remains outside this interface.
Final audit98640 exits0: grouped metrics, epoch selection and gate reproduce;
CPU/CUDA maxdifference2.69e-7 and candidate permutation exact. A serialization
fault in audit95178 is preserved; only the read-only audit was rerun, not fit.
Exact dataset, weights and predictions are retained in model-evidence.tar.gz.

Post-hoc MSE decomposition: parent offset .07245, action-relative .10225.
Calibration alone cannot fix the latter or change the selected action.
GPU verified back to272MiB/0% and no compute processes; cores0–1 released.
This result gives no cheap surrogate for buying substantially more search.
