# Astra review: the next step against duck and Instructors

2026-10-09. Requested by the user; review and diagnostic work only. Fable owns
the root engine/trainer. No training, match lanes, GPU job or new submission was
started. A separate Greek Gift comparison follows this note.

## What is actually deployed

Arena v21 reuses v20's archive, SHA256
`fb7449edded55cf5b4021254926d5d2be9041981c127fe863f9fe8bc740c3ce7`.
I inspected the archive's source, not just `main`: the active engine includes
`policy_prior=100`, while the root `engine.cc` does not contain that addition.
Its CNN/GRU RL policy contributes a log-probability charge to every matrix row;
search, the particle belief, risk charges and root mixture still choose the move.

The public snapshot ends at **14:39:52 UTC**. Elo was **1620.68**, v21 had no
completed games, and v20 had **61W–9D–67L / 137**. Final assigned v20 games can
complete after activation changes. Records against the important opponents:

| Opponent | v20 W–D–L | Score including half a draw |
|---|---:|---:|
| duck v5 | 4–1–11 | 28.1% |
| Instructors v4 | 2–0–7 | 22.2% |
| TA Baseline S v3 | 5–3–6 | 46.4% |
| TA Baseline A v5 | 11–3–12 | 48.1% |
| TA Baseline P v5 | 15–0–3 | 83.3% |

Duck plus Instructors: **26% / 25 games**. The other four leaders:
**0W–2D–28L**. These samples establish the remaining gap, not a precise estimate
of any candidate's improvement. Source and game IDs:
[`arena-snapshot.json`](../astra-submissions/analysis/top-six-review-20261009/arena-snapshot.json).

Fable's top-six loss report provides the right starting point: in its 45-loss
snapshot, 42 games reached a sustained material deficit of at least three,
27 first collapsed in plies 30–69, and 16 finished with a king walking into an
unseen attack. Material loss and fatal king moves are linked; studying only the
last move misses much of the damage. The taxonomy is descriptive: its two-ply
material-loss tag also counts some intentional sacrifices.

## New findings from the trainer review

### 1. A reproducible cutoff-target error — fix before another long run

`learning/rl_train.py:217` bootstraps an unfinished trajectory from the value
of its **last pre-action state**, rather than its successor. With configured
gamma=1 and a zero intermediate reward, the final TD residual is always zero.
For synthetic values V(current)=0.2, V(successor)=0.8, the current function gives
advantage **0.0**, instead of **0.6**. The wrong tail also affects preceding GAE
terms. Terminal win and loss controls produce the correct targets.

The CPU-only reproducer
[`audit_rl_review.py`](../astra-submissions/tools/audit_rl_review.py) extracts
the actual function through AST without initializing Torch, the simulator or
the GPU. Its six cases include interleaved games and reused episode slots:
**four cutoff cases reproduce the mismatch; two terminal controls pass**.
[`rl-audit.json`](../astra-submissions/analysis/top-six-review-20261009/rl-audit.json)
records source hashes and expected/actual arrays. This is correctness evidence,
not an Elo estimate or a measurement of how often the defect affects play.

Repair contract: retain the real bootstrap state and episode/terminal identity.
Because the rollout alternates players, a raw batch-ending board can be an
opponent-turn state: either complete that opponent reply before taking the
same-player bootstrap, or explicitly model whose turn it is. Do not just pass
the arbitrary final board to the existing side-relative critic. Verify split
versus unsplit trajectories with frozen values, terminal reward once, and reset
isolation.

### 2. The training league loses focus on our target opponents

The three inspected RL configs omit **Instructors**. They include duck, but new
snapshots each receive another full unit of weight in a flat pool. Actual logs:

| Training window | duck completed games | Snapshot share of completions |
|---|---:|---:|
| iterations 1–20 | 1,041 / 10,359 = 10.0% | 13.2% |
| iterations 81–120 | 845 / 19,277 = 4.4% | 65.6% |
| iterations 201–240 | 574 / 17,848 = 3.2% | 75.4% |

Completed-game share is not assignment or decision share, but the config also
proves dilution: the continued run ends with 30 snapshot members and duck's
new-game selection weight falls to 1/38. Instructors has zero direct exposure.
Replica quality remains a limitation: merely adding a neural replica does not
make it a faithful instructor/search opponent.

Use fixed **group** weights, then sample within a bounded snapshot reservoir.
One proposed initial allocation, not an optimized prescription: 40% duck plus
Instructors, 25% TA controls, 20% other leaders, 15% self-play snapshots. Log
assignments, decisions and completions separately. Admit target replicas only
after move prediction, failure-pattern and archive-panel calibration; label
unvalidated ones as training diversity, not promotion instruments.

### 3. PPO is optimizing a different controller from the deployed one

Rollouts execute the sampled neural action. Deployment executes the hybrid
matrix/search decision. Iteration 240's network-only gains have not transferred:
the updated local ledger has **3W–7D–6L / 16** against v20, score **0.406**.
That is inconclusive, but it does not earn promotion. Fable's hypothesis about
network-only opponents is plausible; learner/controller mismatch is an
additional explanation, not yet a proven cause.

The next strategic experiment should collect **hybrid decisions and outcomes**
against calibrated target opponents. Use these initially for policy
distillation/ranking and danger calibration. For a later PPO stage, sample from
and record the actual hybrid behavior distribution; substituting a search move
while recording a neural log-probability would invalidate the PPO ratio.

Additional limitations worth tracking: gradients currently cover only each
decision's 1–2 new observation events; longer recurrent learning needs sequence
windows and burn-in. The resume path reloads actor weights but restarts the
critic and optimizers, so iteration 120→240 is not an exact training continuation.
These are documented design/reproducibility limitations, not measured causes of
the arena gap.

## What to do next, in order

1. **Repair and verify cutoff targets.** Persist the critic, optimizer states and
   RNG states for resumable comparisons. Keep the current deployed bytes as the
   control. This should precede expensive training.
2. **Finish the promising existing control before inventing more variants.**
   Prior=200 with the iteration-120 model scored **12W–3D–2L / 17 vs v17** in the
   local ledger. Prior=100 scored 11–7–3 / 21; imitation+prior100 scored 8–1–7 / 16.
   Different samples and a weak shared opponent prevent a winner declaration.
   Test exact prior200 bytes directly against v20 and calibrated duck,
   Instructors and TA-S opponents. Do not promote solely on its v17 score.
3. **Build a current-version surprise-event curriculum.** Sample ordinary
   middlegames as well as hidden captures, slider routes, failed recaptures and
   king walks. Freeze game/trajectory-disjoint splits. Target the first sustained
   material loss and the preceding 2–4 own decisions, not only terminal plies.
   Keep a natural-frequency evaluation set so event oversampling cannot inflate
   the apparent gain.
4. **Improve the hidden-state update on that corpus.** Distill a cheap opponent
   move model from observation-history teachers; measure hidden-slider and king
   localization, missing-support frequency and calibrated move danger. Evaluate
   persistence after a hidden capture as a learned feature, not a rule that the
   piece cannot move. Runtime predictions must use reconstructed opponent
   observations/history within hypotheses; the replay's actual private opponent
   history is not available to our bot. Grouping equivalent histories can save
   inference, but cannot assume every particle shares one opponent information set.
5. **Connect improved information to conversion.** Compare decisions on the
   same candidate set with prior/search/risk contributions logged. Record whether
   a good move was absent, incorrectly ranked, or vetoed by a bad belief. Use a
   short observation-branching planner only after this attribution shows a search
   limitation. Neither more alpha-beta nodes nor a wholesale CFR rewrite is the
   first experiment supported by today's evidence.

The larger teacher deserves a fresh look **with the larger dataset**. Fable's
v6 report has 8.5M versus 1.9M parameters at top-six top-1 **36.97% vs 33.91%**,
and policy NLL **2.1724 vs 2.2670**, on its reported test evaluation. That changes
the earlier small-data capacity conclusion. It still needs deployment and
fresh holdout evidence; distillation should preserve measured capabilities,
and quantization should come after a better teacher earns its place.

## Bounded experimental program for Fable

| Stage | Deliverable | Continue only if |
|---|---|---|
| First 0–4 hours | Trainer regression fix; frozen duck/Instructors/TA panel; prior200 comparison queued | Correct bootstrap/episode boundaries and exact archive identities |
| 4–12 hours | Fixed-mixture league and target-corpus diagnostics | Target exposure persists; replicas reproduce relevant failures |
| 12–24 hours | One corrected RL control and one hybrid-distillation variant | Improvements survive held-out ordinary middlegames and target games |
| 24–48 hours, if justified | More paired games; inference optimization; candidate packaging | Target gain with uncertainty reported, TA-P/A/S regression checks, clock/rules/package checks |

These are proposed work blocks, not jobs started by Astra. An engineering target
is to lift the combined duck/Instructors score from the current 26% toward 35%
while keeping TA performance. **That is a target, not a forecast.** Pre-register
the game budget and stopping rule; retain inconclusive outcomes. Do not treat
50 games as a universal +100-Elo proof, especially after testing several variants.

### Coordination with Fable's concurrent note 020

I read `020-fable-why-we-lose-to-the-top-six.md` after it landed. Its proposed
fog-ray risk and bait correction addresses the same hidden-slider failure
family and is Fable's next implementation. Keep that candidate separate from
the trainer repair and policy-prior experiment so outcomes are attributable.
One measurement caution: capture rates of **moves our bot actually chose** are
not automatically calibrated probabilities for **every legal alternative**.
Fit ray-risk calibration on whole-game training partitions, then evaluate both
chosen and alternative moves against replay truth on disjoint games. Include
false alarms and lost attacking opportunities, not just refused losing moves.
That guard should prevent another cautious candidate from winning a fatal-ply
exam while reducing full-game strength.
