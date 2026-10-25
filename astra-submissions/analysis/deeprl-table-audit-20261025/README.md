# Learn a persistent strategy model that improves bounded GT-CFR search

2026-10-25. Astra proposal for Henry/Fable review. This replaces the mathematical
and integration assumptions in chatroom notes 137–138. The C files here are a
tested, read-only target-export prototype; no trained model or arena improvement
is claimed. The archived engine remains unchanged.

**Latest evidence:** the completed [80-position teacher-readiness gate](teacher-readiness-report.md)
found 10 immediate-fatal base choices versus 11 at 4× search budget, with five
positions where the guard excluded every true escape. Bulk distillation is not
justified by a safety improvement in this test. Read that report before acting
on the earlier proposed training schedule below.

**Follow-up:** [risk-head evidence and a tested PPO auxiliary patch](risk-learning-report.md)
identify a shared-representation training gap and derive an O(M) action-ranking
loss. The patch is ready for review but unapplied; no model/arena improvement
is claimed, and it does not bypass the teacher or deployment gates.

[Native label validation and recorded-training overlap](native-risk-readiness.md)
now confirm 163,946 candidate labels against the independent referee and identify
four training-overlap cases in the old-head diagnostic. This closes the native
label prerequisite; a training run and deployed-strength evidence remain pending.

[Persistent teacher collection](persistent-teacher-report.md) now reuses a
game-side history across queried decisions. The six-query pilot took 6.87 s
versus 18.56 s for fresh processes, with matching input/support checks and three
different timed-search choices. This is producer evidence, not teacher-quality
or playing-strength evidence.

## What we actually need to improve

There are three different objects called a “table” in this project:

1. The frozen history-keyed **opponent prior** reweights hidden opponent moves.
   It needs predictive training and held-out calibration, not our own terminal
   reward blindly applied to the opponent's move frequencies.
2. The **PCFR+ regret/strategy arrays** are optimized during one search and then
   freed (`src/gtcfr.c:425–427` in the v35 archive). They do not accumulate a
   persistent cross-game DeepRL strategy.
3. A **learned information-state model** can retain useful decision structure
   across searches and generalize beyond an exact history hash. This is the
   proposed durable replacement for repeatedly starting search without that
   learned knowledge. It guides the solver; it is not a perfect-board cache.

The current modern trainer is `learning/rl_train.py`, with an existing C++
`BatchEnv`, batched network opponents, stored-state recurrent PPO, and a separate
training-only true-board critic. Rebuilding that simulator is not the proposal.
`learning/train_ppo.py`, cited in note 138, is an older path. The arena v35 search
selector is a different policy from the standalone PPO actor.

## The mathematical learning target

Let `I` be one player's observation/action history, `b(s|I)` its estimated hidden
state distribution, and `σ` a strategy profile in a frozen search tree. For a
history `h` in infoset `I`, let `ρ_-i(h)` include chance and the other player's
reach, excluding player `i`'s own reach. Define

\[
 m(I)=\sum_{h\in I}\rho_{-i}(h),\quad
 q_{cf}(I,a)=\sum_{h\in I}\rho_{-i}(h)\,U_i^\sigma(ha),\quad
 Q(I,a)=q_{cf}(I,a)/m(I).
\]

For positive `m`, the normalized action advantage is

\[
 A(I,a)=Q(I,a)-\sum_b\sigma(b|I)Q(I,b).
\]

An action advantage is a more comparable supervised target across positions
than an unnormalized accumulated regret whose scale changes with reach and
iteration count. Zero-mass rows are marked unsupported, never divided by zero
or silently assigned a meaningful zero-value label. These are action values
under the teacher's continuation policy, sampled worlds, and frontier evaluator;
they are not exact full-game minimax values or independently observed outcomes.

The archived solver specifically implements predictive CFR+:

\[
 r_t(I,a)=q_{cf,t}(I,a)-\sum_b\sigma_t(b|I)q_{cf,t}(I,b),\quad
 R_t=[R_{t-1}+r_t]_+,\quad
 \sigma_{t+1}(a|I)\propto[R_t(I,a)+r_t(I,a)]_+.
\]

Use uniform action probability if the denominator is zero. This differs from
the plain signed cumulative-regret formula in note 138. Export `R`, `last`,
iteration count, infoset creation iteration and tree version separately if we
want to inspect or learn the solver state. Do not initialize these arrays from
an arbitrary neural advantage and assume a convergence guarantee.

For a fixed perfect-recall game, a realization-equivalent average policy is

\[
 \bar\sigma_i(a|I)=
 \frac{\sum_t w_t\rho_i^t(I)\sigma_i^t(a|I)}
      {\sum_t w_t\rho_i^t(I)}.
\]

Here `ρ_i` is **own** reach, counted once per infoset, not multiplied by the
number of sampled histories. The archive's accumulator uses only `t*σ_t`, so it
does not give this average at deeper decisions. The compiled counterexample
returns 0.366667 rather than 0.754545 at its child infoset. The root has own
reach one and does not exhibit this particular weighting error.

Crucially, v35 deploys the **last iterate's highest-probability action**, not
`pcfr_average`. This is not evidence that the averaging defect caused arena
losses. Obscuro itself uses last-iterate strategies and purification, with
explicit qualifications about the theory. For our first teacher, export both
last-iterate root probabilities and the actual selected move. Distill the
root distribution as a search prior; evaluate the final deployed selector.
Do not silently switch deployment to averaging. Growing trees change the game
being solved, so fixed-game average-strategy claims do not automatically apply.
[Obscuro, sections 3.2 and C.7–C.8](https://arxiv.org/html/2506.01242v2).

## One improvement loop, connected to deployment

The first experiment is search-guided policy iteration, with the belief model
and Stockfish frontier held fixed to identify what the learned prior changes:

\[
 \text{search self-play}\to(I,\mu_{4B},A_{4B},z)
 \to\text{train }(\pi_\theta,\widehat A_\theta)
 \to\text{search at budget }B\to\text{fresh self-play}.
\]

`μ_4B` is the stronger-budget teacher's root distribution, not an omniscient
best move. Offline replay truth may label errors, but the teacher receives only
the actor's legal observation stream and belief reconstructed from that stream.
Use the same actor input for indistinguishable worlds. Include action identity,
pre-guard candidates, the guard mask and which alternatives actually received
search evaluation. Never label an unexplored/filtered action as bad just because
its column is absent.

Record utility units as well: this archive maps nonterminal centipawn estimates
through `tanh(cp/400)`. A value learned in those units is not a calibrated win
probability. Keep terminal outcome labels and frontier estimates distinguishable.
The root additionally uses a shaped loss of `-MIST_KING_RISK` (default **-2**)
for immediately fatal own moves. Consequently normalized root Q can be below
-1; do not silently force this target into a ±1 value head. Export that shaping
parameter separately from actual terminal win/loss labels.

For the first student use the existing deployable history encoder and add an
action-advantage head. Proposed objective, with each term normalized and its
coefficient fixed before the run:

\[
 L=\mathbb E_D[\mathrm{CE}(\mu_{4B},\pi_\theta)
       +\lambda_A\,\mathrm{Huber}(\widehat A_\theta,A_{4B})].
\]

Log terminal returns for the future critic; do not change the frontier in this
same experiment. Search-generated labels give action comparisons, whereas one
terminal result supervises only the trajectory that happened. Stronger-budget
labels can still be wrong: validate root recommendations under independently
sampled beliefs and report teacher disagreement.

Initially use the prior only to allocate **root expansion work**, retaining
solver selection and existing deeper expansion. This is an integrated, narrow
test of the learning loop. It avoids pretending a 64-bit history hash is a
usable recurrent-model input at every internal node. Internal neural expansion
requires stored observation events or incremental recurrent states per branch;
the current tree only stores hashes and positions. That is a later extension
if the root experiment earns it.

One proposed allocation score is

\[
 P_{mix}(a)=(1-\eta)\sigma_{CFR}(a)+\eta\pi_\theta(a),\qquad
 S(a)=\widehat A_\theta(a)+
 c\,P_{mix}(a)\frac{\sqrt{1+\sum_bN_b}}{1+N_a}.
\]

This is a compute-allocation proposal, not a theorem or a replacement regret
update. Reserve the existing exploration path so an early wrong prior cannot
permanently starve alternatives. Compare against the current expansion score
(`σ_CFR(a)+sqrt(total+1)/(1+N_a)`) under matched wall time **and** report node,
leaf-call and CFR-iteration counts. Freeze `η,c` for one experiment; no sweep.

Do not apply PPO's `π_new/π_old` ratio to actions chosen by search. Those actions
have search behavior policy `μ`, not the network's `π`. Merely logging `μ`
does not make the search controller differentiable or make standalone-actor PPO
optimize it. Teacher-policy cross-entropy needs no fabricated on-policy ratio.
The existing PPO remains a separate actor experiment until its training and
deployment selector agree.

Deep CFR establishes the precedent of replacing enormous regret tables with
function approximation. Our bounded, growing-tree distillation is an engineering
adaptation, not an implementation of that algorithm's full sampling/training
procedure or its equilibrium theorem.
[Deep CFR, ICML 2019](https://proceedings.mlr.press/v97/brown19b.html).

## Why more search and a bigger network can both fail

For a fixed continuation policy with utility in `[-1,1]`, if the true belief is
`b` and ours is `b_hat`, then

\[
 |Q_b(a)-Q_{\hat b}(a)|\le2\,TV(b,\hat b).
\]

If our approximate action values also have uniform error at most `ε`, choosing
their largest value incurs at most `4 TV(b,b_hat)+2ε` action-value loss. This is
a simple fixed-continuation bound, not a full equilibrium guarantee. It shows
why spending more nodes on the wrong posterior can leave the main error intact.
For the archive's shaped utility range `[-κ,1]`, replace this bound by
`2(κ+1) TV(b,b_hat)+2ε`; with the default `κ=2` the belief term is `6 TV`.
For independent samples, an attacker hypothesis with mass `p=.004` is missed
by all 32 samples with probability `(1-p)^32≈.88`. Stratification can improve
coverage but cannot resurrect a world the belief filter already discarded.

Therefore the fixed evaluation panel also tracks true-state support, attacker
square mass, calibration, and held-out opponent-move likelihood. The next
posterior investment is a calibrated opponent transition model trained from
observation-compatible replay decisions; it is distinct from this first search
prior experiment. Learning square marginals alone does not model correlated
joint boards. Importance sampling requires recording actual proposal
probabilities rather than applying arbitrary likelihood multipliers.

Likewise a scalar `V(I)` copied across every hidden leaf is not automatically
a valid imperfect-information subgame evaluator. Continuation values depend on
the strategy-induced ranges and what each player knows. ReBeL handles this with
public-belief states; directly enumerating those states is difficult in Fog.
A future learned frontier must explicitly specify belief/range and continuation
policy conditioning, or evaluate a set of continuation strategies. Retaining
the present frontier in experiment one makes that unresolved issue explicit.
[ReBeL, NeurIPS 2020](https://arxiv.org/html/2007.13544).

## Faster means more useful decisions per second

- Reuse `BatchEnv`; measure simulation, feature construction, inference, search,
  data transfer and optimization separately. `rl_train.py` already logs rollout
  and update time. Search-teacher generation needs separate counters.
- Batch independent histories for GPU training. Run teacher search on CPU with
  a bounded producer queue; avoid unbounded in-memory replay histories. Keep
  games as the train/validation split unit, with a later-time holdout.
- Keep the compact runtime student; a larger attention teacher or latent
  compression is justified by decision quality per CPU millisecond. Board-pixel
  reconstruction quality is not the objective: a compressed representation
  must preserve rare lethal distinctions and action ranking.
- A full CFR traversal still costs `O(edges)` in the traversed tree. A heap does
  not remove that dependence. Its `O(log frontier)` selection cost helps only
  if selection dominates and priorities can be updated cheaply. With a few
  dozen root actions, a contiguous scan is a sensible initial implementation.
  Profile before replacing it with a heap or changing all tree data structures.

The GPU was checked outside the sandbox on 2026-10-25: RTX PRO 5000, 0% busy,
1126/48935 MiB used. The earlier driver-unavailable diagnosis was incorrect;
it was a sandbox visibility issue. No GPU service was interrupted, and this
audit started no training.

## Finite next 24 hours, starting after committee review

One proposal, one student, one integration, one gate. No architecture sweep.

| Window | Deliverable | Stop/decision |
|---|---|---|
| Hours 0–4 | Fable reviews the exporter; Astra connects root history and action identities in an isolated engine copy | Stop if targets depend on hidden truth, masks mismatch, or analytic checks fail |
| Hours 4–10 | At most 2,000 teacher decisions from at least 250 whole games, capped at six CPU wall-clock hours on agreed free cores | Freeze completed data at the cap; record unsupported rows and independent-teacher disagreement |
| Hours 10–13 | One student training run, at most two GPU hours plus export/CPU checks | Stop on nonfinite loss, history leakage or worse validation action-value error |
| Hours 13–16 | Pinned-root comparison: unmodified search at B, student-guided search at B, and teacher at 4B | Advance only if at least 10% lower mean held-out teacher-relative decision regret, paired game-cluster interval excludes zero, and no increase in audited immediate-fatal choices |
| Hours 16–24 | If the preceding gate passes, start one preregistered 20-pair full-clock comparison | Review at hour 24 even if incomplete; never extend because the partial score looks good |

The 10% threshold is a proposed engineering gate, not an Elo conversion.
Teacher-relative regret uses a frozen independent evaluation of action values;
it is not computed from the student's own predictions. Also report candidate
and control against unseen opponent styles. Forty games are only a screen,
not reliable evidence of a modest Elo gain. No ZIP promotion from validation
loss alone. Review records include failures, compute consumed and a continue,
change or stop recommendation. Henry's 24-hour review requirement remains in
force even if an experiment is running.

## Reproduce the completed correctness work

```sh
python3 astra-submissions/analysis/deeprl-table-audit-20261025/run_probe.py
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/audit_ep.py \
  --manifest astra-submissions/analysis/ep-target-inference-20261025/v35-ep-history-paired-20pairs-seed20261080.json \
  --referee-dir /home/henrytan/git/fow-starter
```

`run_probe.py` checks the archive hash, extracts only `cfr.c/h` into a temporary
directory, and compiles the reference extractor against them. Tests cover the
two-decision averaging counterexample, shared hidden-world infosets,
counterfactual opponent/chance reach, player-1 utility sign, zero support, and
unchanged solver arrays. The exporter costs `O(edges + action slots)` per frozen
snapshot, with linear output storage plus traversal stack. It is not optimized
for export on every CFR iteration. Production integration still needs schema,
action/history plumbing and serialization; this prototype does not claim those
are complete.

`probe-result.json` records the result and archive hash. `ep-audit-result.json`
records six completed games and checks all 547 frames against the independent
referee's full board and observations. It finds **zero actionable candidate EP
turns**. `d3d5` was a white rook move, not a pawn push. The terminal `a2a4` frame
offered no further turn. This retracts notes 137/139's claimed EP exposure.

## Real-tree export validation and teacher-readiness finding

Additional work on 2026-10-25 validated the exporter on the actual v35 GT-CFR
path. `run_engine_probe.py` extracts the pinned archive into a temporary folder,
adds a callback **after** search chooses its move, and compiles the unchanged
policy implementation with the export code. No archive or Fable source changes.
The four prefixes are frames 0, 1, 12 and 54 of the already recorded guard-pair-8
game. This is a small correctness/teacher sanity panel, not a playing-strength
sample or a training run. It uses the shipped Stockfish and history table.

All four pass the checks for normalized world and action probabilities, root
counterfactual mass, equal own reach within each represented infoset, action
identity, finite values, zero policy-weighted advantage, agreement with the
solver's independently computed `game_value`, and agreement between the raw
solver move and final protocol move. The latter matters because the front end
can otherwise replace a move after search. These checks are necessary, not
proof that every internal infoset has perfect recall or aligned action labels.

`engine-probe-result.json` stores the exact actor protocol, target rows, sampled
hypotheses and archive/binary hashes. Hypotheses are diagnostic **output**; the
engine receives no replay truth. `audit_teacher_choices.py` subsequently uses
the independent referee and full replay solely to produce offline safety labels.
Those labels are separate in `engine-probe-labels.json`. Clocks and CPU scheduling
make this time-limited search nondeterministic even with the same random seed.

The frame-54 hidden-rook case was then checked at 0.4 and 1.6 seconds, with the
same input history, seed and sampled worlds:

| Search budget | Tree nodes | CFR iterations | Selected move | Actual outcome of that move |
|---|---:|---:|---|---|
| 0.4 s | 23,523 | 400 | c7e6 | Immediate king exposure |
| 1.6 s | 67,713 | 1,120 | c7a8 | Immediate king exposure |

Both sampled 22 distinct worlds from a 392-entry belief. Neither the true board
nor **any world with the existing king attack** was sampled. Both assign zero
root probability to the two actual escapes, `f1e2` and `f1g2`. At 1.6 seconds,
the shaped Q for the selected fatal move is -0.943953; the safe escapes are
ranked below it at -0.945102 and -0.945049. Of the 17 evaluated candidates, 15
are immediately fatal on the true board. All 17 are pseudo-legal; illegality
does not explain this failure.

Artifacts: `teacher-budget-probe-result.json` and `teacher-budget-labels.json`.
This single selected counterexample does **not** establish that stronger-budget
distillation is useless overall. It establishes that higher search budget is
not a sufficient definition of a better teacher, and that these particular
labels would teach the known error confidently.

**Revision for committee review:** before the proposed bulk generation/training
phase, require a fixed teacher-readiness panel of known failure families plus
ordinary controls. Report which targets genuinely improve under stronger
search, which remain unsupported by the sampled belief, and which are unstable.
Keep failure examples and their privileged offline labels in the audit set;
do not drop them to improve a metric or inject the true board into a teacher's
live belief. For unsupported hidden attacks, the next candidate must address
the learned posterior or observation-conditioned danger estimates and clear
held-out calibration checks. More scalar guard sweeps are not proposed. This
panel is a prerequisite to spending the GPU budget, not an open-ended addition
to the 24-hour review schedule.

Reproduce the extra checks:

```sh
taskset -c 0,1 python3 astra-submissions/analysis/deeprl-table-audit-20261025/run_engine_probe.py
taskset -c 0,1 python3 astra-submissions/analysis/deeprl-table-audit-20261025/run_engine_probe.py --frames 54 --seconds 0.4 1.6
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/audit_teacher_choices.py \
  astra-submissions/analysis/deeprl-table-audit-20261025/teacher-budget-probe-result.json \
  --referee-dir /home/henrytan/git/fow-starter
```

Claim cores in `chatroom/cores.json` before rerunning; these audit runs released
cores 0–1 when they finished. No GPU use or new game tournament was started.
