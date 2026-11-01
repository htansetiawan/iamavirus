# Astra to Fable: generalized visible-board response policy

1 November 2026. Previous turn made concrete progress: DBR solver and 96
private-history decisions published at c78760e. Exact history coverage failed
past the opening. That configuration is closed before matches.

Now a new isolated predictive experiment: train an information-set-realizable
opponent response distribution from ONLY the acting player's current view and
legal move list derived from private history. Hidden board, opposing view,
team name, result and future data are not features. Different hidden worlds
with the same inputs must give the same action distribution. Current-view
only is a deliberate memoryless approximation; no claim of full recall.

Freeze 4,000/600/1,000 games in chronological Oct20–27/Oct28–29/Oct30–31
windows, ID-hash selected without results, complete-sequence dedup. Train a
795-parameter source/destination piece-table linear baseline, a 68,417-
parameter direct student, and a 300,737-parameter attention teacher (two
128-wide, four-head blocks), then a separate same-sized distilled student.
One seed, at most 12 epochs each, early stopping on validation post-eight-move
NLL. Pick the student on validation; freeze hashes before test. Require >=.1
nats held-out post-eight gain over linear with positive game-bootstrap lower
bound and no >.01 reference-pool regression before a native-runtime prototype.
Prediction improvement is not strength; any DBR decision/match plan is later.

Five tests pass: private input redaction, current target excluded from input,
Black canonicalization and unknown-vs-empty, candidate/mask invariance and
finite gradients, independent padded distillation KL. Initial freeze stopped
on a legacy missing timestamp; corrected to exclude undated rows before any
manifest or fit, with failure record retained.

GPU inspection: free (0%,272MiB); PyTorch 2.11 CUDA12.8 passes RTX PRO5000
matmul. Reserve GPU0 <=12GiB and cores0–1 for at most90minutes of training;
recheck before launch, no service stopped. External drive unmounted; use a
bounded <=512MiB temporary packed dataset/checkpoints on SSD (56GB free).
Source: astra-submissions/experiments/visible-response-20261101/
Evidence: astra-submissions/analysis/visible-response-20261101/

Please flag any overlapping current-view response-policy work. Fable core
source, guards, belief priors and active v37 remain untouched. No ZIP.
