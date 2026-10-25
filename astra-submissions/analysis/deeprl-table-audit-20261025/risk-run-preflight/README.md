# Concrete next-run proposal: preserve and improve risk learning during PPO

2026-10-25. Prepared for Henry/Fable review. **Not launched.**

## Fixed experiment

| Setting | Both arms |
|---|---|
| Initial actor/reference | Existing v6-l supervised best, step 15030, 20,363,530 parameters |
| Architecture | CNN 192 channels × 10 blocks, GRU 768, candidate width 384 |
| Initial critic | Existing `critic-vs/best.pt`; both arms start from identical weights |
| Optimizers | Fresh for both arms; no actor-only continuation/resume |
| Training | 60 iterations, 16,384 rollout decisions/iteration, 256 games, two PPO epochs |
| Seed | 20261025 |
| League | Existing fixed group quotas: target opponents .40, TA .25, other leaders .20, self-play .15 |
| Hard resource cap | One GPU hour per arm, sequential; two GPU hours total |
| Checkpoint comparison | Largest common complete snapshot at a multiple of 10 iterations |

The control retains the current PPO objective. The candidate adds exactly
`0.1 * (BCE_risk + 0.25 * separation_loss)`. These coefficients are a fixed
experimental hypothesis, not a measured optimum; there is no sweep. Both arms
share all remaining configuration. Candidate risk labels are training-only.

The current PPO loader accepts the CNN checkpoint schema. The older attention
checkpoint used in the diagnostic cannot be dropped into it unchanged. This
comparison therefore tests the auxiliary-training mechanism on the compatible
Fable CNN; it is not an attention-versus-CNN experiment.

## Completed preflight

- Ten distinct actor/league checkpoint files passed strict CPU model loading,
  feature/action version checks, finite forward passes and expected output shapes.
- The critic passed strict loading and a finite forward pass.
- Reconstructed the dataset builder's **interleaved content hash** from all
  v6 shards in accepted-source order. All 25,070 games / 50,140 episodes match
  the initial checkpoint's recorded content SHA-256. That checkpoint's field
  `dataset_manifest_sha256` stores a content digest, not the JSON file digest.
- Froze 128 recent arena-v35 IAmAVirus games (5,843 own decisions) from 680
  eligible games, with 68 White and 60 Black seats. They have no game-ID or full
  move-sequence overlap with any v6 train/validation/test partition. Every
  selected replay passed independent board, observation and terminal validation.
- Prepared 73 pinned source files in an isolated directory. Applied the reviewed
  PPO patch there and built its own native simulator. Full module import and
  `--help` succeeded. Fable's source, library and running jobs are untouched.

The validation sample follows hash order and includes 12 duck, 11 Instructors,
12 Knight Vision, 14 Strongly Invisible and 3 Greek Gift games, among others.
It is a recent own-game validation distribution, not balanced per opponent.
The small per-opponent counts do not support separate strength claims.
Shorter shared prefixes/transpositions remain possible. The cohort is not a
final untouched promotion test and was not checked against every past experiment.

## Gates and stop conditions

Use terminal-return PPO for the strategy objective; the auxiliary predicts
immediate danger. Training reward against imitated league models is a proxy,
not arena Elo or evidence of beating the real opponents.

Before looking at validation outcomes, retain the fixed comparison above.
Report per-game candidate-risk log loss and Brier score, within-position
safe/fatal ordering, and immediate-fatal choices under both policy argmax and
minimum-risk selection. Bootstrap by game, not by individual move. Compare the
candidate with the common-step control and the initial actor.

Advance to **C-search integration testing only** if risk log loss improves over
control with a paired game-bootstrap 95% interval below zero, and neither
within-position ordering nor audited policy-choice safety worsens. Report
terminal-return/league results separately. Better auxiliary loss alone cannot
justify a release. A learned head still needs inference integration and testing
through the actual C selector, including its root exclusions.

Stop on nonfinite training, input/label misalignment, source/hash changes, or
the time/iteration cap. If only one arm reaches the next snapshot, use the last
valid common snapshot. Do not extend or resume to obtain a favorable result.
Record incomplete jobs and return to the committee at the 24-hour checkpoint.

## Reviewable artifacts and commands

- [Control config](control.yaml), [candidate config](auxiliary.yaml)
- [All checkpoint/source/config hashes and preparation receipt](preflight.json)
- [Frozen validation games](validation-games.json)
- [Preparer](../prepare_risk_run.py), [bounded launcher](../launch_risk_arm.py)
- [Mathematical loss and patch evidence](../risk-learning-report.md)

The launcher defaults to validation/command preview. `--run` is the separate
launch action, after plan review and CPU 0–1 reservation. It rechecks pins,
requires a free GPU and an unclaimed GPU lease, creates fresh output directories
on `seagate1`, and enforces the per-arm process-group deadline. It never stops
another service. GPU training has not started.

```sh
.venv/bin/python astra-submissions/analysis/deeprl-table-audit-20261025/launch_risk_arm.py --arm control
.venv/bin/python astra-submissions/analysis/deeprl-table-audit-20261025/launch_risk_arm.py --arm auxiliary
```

**Scope decision for review:** this is a concrete standalone-PPO auxiliary
comparison. It does not train the deployed C search's regret tables directly.
If the committee prioritizes the persistent C-search policy/advantage model
instead, keep this prepared comparison unlaunched and redirect to that
integration; do not silently call this the completed search-learning campaign.
