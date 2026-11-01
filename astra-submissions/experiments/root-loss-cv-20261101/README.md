# Root terminal-loss correction experiment

1 November 2026. Astra-owned, isolated from Fable's source checkout. This is
an experiment based on the immutable v35 archive, not a release or an arena
upload. `implementation-origin.json` and `build-provenance.json` pin its source
and executable. The feature defaults off; enable with `MIST_ROOT_CV=1`.

## Question and mechanism

The king guard scans a much larger portion of the belief than the 32 worlds
usually searched. Can that scan improve the search's estimate of immediate
king loss without another veto or another risk penalty?

For root action a, let L be the existing terminal-loss utility (normally -2),
p_B its loss probability from the guard scan under the actual search-draw
weights, and p_S its sampled chance mass. The adjusted value is

    V_corrected(a) = V_sampled(a) + L * (p_B(a) - p_S(a)).

The subtraction replaces the sampled immediate-loss component. It does not
charge it a second time. The exact toy in
`../../tools/test_root_loss_control_variate.py` establishes the fixed-policy
calculation; it does not establish a playing-strength gain or a guarantee for
an adaptively grown CFR tree. Variance reduction is not universal when the
remaining continuation value covaries with the loss event.

## Implementation

- `main.c`: reuse the king guard traversal to cache immediate-loss probability
  using `exp(logw)`, the same weighting as `belief_sample`. Keep existing guard
  risks, thresholds and removals unchanged. The cache respects root move
  legality and opposing-king-capture precedence. CV-on incurs extra legality
  checks on losing worlds; runtime cost must be measured.
- `gtcfr.c`: sum sampled chance shares, including frequencies of merged
  duplicate draws. Add the same action correction in every sampled world.
  Preserve that entry reward when its initial leaf becomes an internal node.
- `cfr.c`: support additive rewards at nonterminal nodes. The reward cancels
  from that node's own action regrets and reaches ancestor action values with
  the correct player sign. Existing internal rewards are zero when CV is off.
- `gtcfr.h`, `cfr.h`: document the optional cache and entry-reward semantics.

The cache is available only when the existing king guard scan runs. Missing
cache keys receive no correction. Above 20,000 boards the strided scan is an
approximation, not an exact posterior marginal. This cannot repair an absent
world, a wrongly weighted posterior, or material losses unrelated to immediate
king capture. No queen or material correction is included.

## Checks and comparison

`run_checks.py` builds native tests for equivalent entry/terminal rewards,
both players' regrets and best responses, Kuhn poker, draw weighting, both
colours, root loss precedence, duplicate shares, full enumeration and growing
frontiers. It also runs address/undefined-behaviour sanitizers. LeakSanitizer
needs execution outside this environment's ptrace-based sandbox. Raw outputs
and source hashes belong in `correctness.json`.

`run_replay_gate.py` compares immutable v35, the patched feature-off control,
and CV-on on the frozen 51-case fresh-taxonomy **development** set. Rotated
order, seed 11012026, 2.5-second cap, one reserved core pair (0–1), same
observations/clocks and forced own history. Ground truth is used only by the
scorer; recorded opponent replies are never applied after a different move.
The harness stops on any protocol error or illegal move and records both
failure labels and runtime/search-node counts. No full matches are justified
without a useful replay signal and separate confirmation.

Run from the repository root:

```sh
taskset -c 0,1 python3 astra-submissions/experiments/root-loss-cv-20261101/build_experiment.py
taskset -c 0,1 python3 astra-submissions/experiments/root-loss-cv-20261101/run_checks.py
.venv/bin/python astra-submissions/experiments/root-loss-cv-20261101/run_replay_gate.py --out NEW_DIRECTORY
```

Results are separate under `astra-submissions/analysis/root-loss-cv-20261101/`.
The development sample deliberately overrepresents failure categories, has
correlated decisions from the same games, and scores material with a limited
omniscient exchange probe. It cannot estimate Elo or overall probability
calibration. The old frozen regression suite remains untouched.

## First screen result

Completed 153 policy runs: original v35 / patched-off / patched-on each made
10 fatal choices and 5 net material-loss choices. CV-on fixes two king-loss
decisions and breaks two; no errors or illegal moves. Native and sanitizer
checks pass. The feature is **not promoted**, and no full-game lane is spent
on this null. See the [result and diagnostic traces](../../analysis/root-loss-cv-20261101/README.md).
