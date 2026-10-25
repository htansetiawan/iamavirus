# Initial CNN evaluation: hidden attacks remain the weak point

2026-10-25. **No fitting, GPU work, or model change.** The pinned v6-l supervised
CNN was evaluated on all 128 frozen recent v35 games, covering 5,843 own
decisions. This completes the baseline measurement for the proposed PPO
comparison; it is not a trained candidate or evidence of improved playing strength.

## What the baseline actually does

| True position before the choice | Decisions | Policy argmax fatal | Minimum predicted risk fatal | Recorded v35 move fatal | Mean within-decision AUC |
|---|---:|---:|---:|---:|---:|
| No current king attack | 5,630 | 86 | 46 | 26 | 0.941 |
| At least one current attacker visible | 100 | 15 | 10 | 8 | 0.974 |
| All current king attackers hidden | 113 | 60 | 69 | 34 | 0.557 |
| All positions | 5,843 | 161 | 125 | 68 | 0.923 |

Higher AUC means fatal candidates receive higher danger logits than safe ones.
It is averaged only over decisions containing both safe and fatal moves.
There were 1,953 such decisions overall, including 102 hidden-attack decisions.
The 22 positions with no immediate escape contribute unavoidable fatal choices
to all selectors; excluding these gives 139 policy and 103 minimum-risk fatal
choices, versus 46 for the recorded v35 actions.

The recorded moves and the two neural selectors are scored on the **same fixed
histories**. The neural choices were not played and do not generate subsequent
positions. These counts are not head-to-head wins/losses or an Elo comparison.
This CNN and cohort also differ from the earlier 80-case attention diagnostic;
their metrics do not establish a CNN-versus-attention architecture comparison.

Decision-weighted candidate log loss is 0.11092 and Brier score is 0.03114.
The hidden-attack slice has log loss **1.74452** and Brier score **0.50642**.
Only 1.93% of these decisions are in that slice, so aggregate quality can conceal
the failure we most need to address. The current head is not ready to replace
the deployed C selector or unmask its root actions blindly.

## The measurement contract

For candidate a at decision t, let y_ta indicate immediate king exposure on
the true replay board and z_ta be the observation-conditioned risk logit. For
each game g, the primary score is

\[
\ell_g(\theta)=\frac1{T_g}\sum_t\frac1{M_t}\sum_a
  [\log(1+\exp(z_{ta}))-y_{ta}z_{ta}].
\]

It is evaluated with numerically stable `logaddexp`. The initial model's
**game-weighted** log loss is 0.11822; this differs from the decision-weighted
summary because games have different lengths. The future comparison uses
paired differences `ell_g(candidate) - ell_g(control)` and resamples whole
games. One realized hidden board does not imply a calibrated model should have
assigned probability one to that world; calibration is evaluated across the
recorded cases, not demanded from a single observation.

The comparison tool enforces identical panel, source, replay and actor-input
hashes. It reports log loss, Brier score, policy fatal probability mass, actual
argmax/minimum-risk fatal counts, and within-position ranking. Its gate can
advance only to a **C-search integration test**, never to release. The hidden
slice is reported explicitly without changing the frozen training coefficients
or starting a new sweep. The arena slice frequencies must not be assumed to
match the imitated-opponent PPO league; that exposure still needs measurement.

## Correctness and runtime

- Reconstructed every actor history from the initial position. Features and
  candidate lists use observations and past own moves only. Native features
  match this separate reconstruction exactly on the panel.
- Verified all **170,648 candidate danger labels** with the Python referee.
  Future recorded own moves enter history only after the current input is built.
- Four games covering both colors and 221 decisions give the same choices
  with batch size one or four. Maximum logit difference: 6.68e-6.
- Three analytic/gate-contract tests pass. The real whole-panel self-comparison
  produces zero differences and correctly refuses to claim improvement.
- Full evaluation took **99.61 CPU wall seconds** on cores 0–1: 8.61 seconds
  preparation, 88.84 seconds inference, and the remainder startup/output. This
  is evaluation timing, not arena inference latency or training throughput.

Artifacts: [complete baseline summary](initial-model-evaluation.json),
[correctness receipt](evaluation-validation.json),
[evaluator](../evaluate_risk_panel.py), [paired comparator](../compare_risk_panels.py).
Compressed predictions and pilot outputs are retained on the authorized disk
at `/media/henrytan/seagate1/iamavirus/astra/rl-risk-20261025/evaluation-initial/`
and adjacent `evaluation-pilot-batch1/` / `evaluation-pilot-batch4/` directories.
The summary records their hashes. These are evaluation artifacts; no training
arm directory, GPU lease, optimizer run or candidate ZIP was created.

```sh
taskset -c 0,1 .venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/evaluate_risk_panel.py \
  --batch-games 4 --wall-cap 600 --output-dir /tmp/risk-panel-fresh-evaluation
```

Use a fresh output directory. For a later checkpoint, provide both `--checkpoint`
and its explicit `--expected-checkpoint-sha256`; the same frozen panel and
source checks remain in force.
