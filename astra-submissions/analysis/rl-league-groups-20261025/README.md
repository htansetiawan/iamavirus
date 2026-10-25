# Fixed-group opponent sampling for the recurrent PPO trainer

## Change

`learning/rl_train.py` now supports an optional two-stage league sampler:
choose an opponent group at a configured rate, then sample a member within
that group using its existing relative weight. Configurations without
`group_weights` retain the prior flat weighted sampler.

`learning/configs/rl_l.yaml` opts into a proposed curriculum:

| Opponent group | Share |
| --- | ---: |
| duck + Instructors | 40% |
| TA Baseline P/A/S | 25% |
| other leaders plus the imitation reference | 20% |
| self-play snapshots | 15% |

The imitation reference remains the KL target; it is also sampled as an
opponent within the 20% group at twice a single replica's within-group weight.
That is an explicit initial choice, not an experimentally optimized ratio.

A self-play actor snapshot is included at initialization so the 15% group is
available from the first batch. `snapshot_sample_capacity: 6` restricts new
assignments to the newest six snapshots. Old member indices and models remain
available while games already assigned to them finish; the setting bounds the
sampling pool, not model-memory use. The trainer logs `league_decisions` per
member for every iteration, so actual learner-decision exposure can be audited
instead of inferring it from game assignment or completion counts.

## Verification

- New sampler tests: **7 passed**. They check 40/25/20/15 group rates over
  100,000 synthetic selections, weighted sampling within groups, empty-group
  renormalization, flat-sampler compatibility, snapshot eligibility and invalid
  config rejection.
- Existing real-simulator trainer regressions: **15 passed**, including the
  grouped rollout's actual decision-exposure log.
- Config preflight confirmed every reference/replica has a group, group weights
  sum to one, and the six-snapshot sample cap is valid.
- `py_compile` passed for the trainer and new test file.
- No GPU training or playing-strength experiment was run. This session's
  `nvidia-smi` could not connect to the NVIDIA driver. No release ZIP or arena
  version changed.

## Limits and next gate

This controls opponent-group sampling, not the bigger deployment mismatch:
PPO samples the neural policy while the deployed bot lets the search/matrix
controller choose. It also does not repair actor-only resume or serialize
in-flight C++ game slots. Do not interpret the group quotas as Elo evidence.

When GPU access returns, the next run should use a new output directory and
log the observed `league_decisions`. Compare against the prior flat sampler
with the same initial model, update budget, seed set, fixed replicas, and
held-out opponent panel. First validate the sampled group shares and model
memory at the full batch size; then require downstream hybrid decisions and
clocked games before promoting any model.

## Source hashes

- `learning/rl_train.py`: `a8f2f5e89a289c720ac73a27acef2ddcb6ae15b00fde0d41d4bcd171ae2e06b5`
- `learning/configs/rl_l.yaml`: `107371d712dfe844c564146b29c07054751f2a97b8b886be27adab65863e52af`
- `learning/tests/test_rl_league_sampling.py`: `5a87ce784b3c24d29b1f0ba64ec9ca3bfbda918c7cb56de025e58d4ca55b8d4f`
- `astra-submissions/tools/test_rl_trainer.py`: `e519f62f28c6584e04fc514b8524dea9acd564624f66010ace469d41bc1fd279`
