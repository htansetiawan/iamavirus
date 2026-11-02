# Bounded Stockfish residual: confirmation fails the newer-game safeguard

Experiment 240 is complete. The frozen flat residual improves pooled prediction
loss, but fails both predeclared newer-game safeguards. It does not advance to
engine integration, a decision trial, full games, or a submission ZIP. The query
comparator cannot replace it after seeing this test.

The selected model was fixed by experiment 239's development validation. Its
native payload is 640,392 bytes and takes about 9.37 microseconds per world on
one core. It adds at most two log-odds units to a fixed calibrated Stockfish
score. That bound limits the correction, not tactical loss or exploitability.

## Confirmation evidence

The contract was published at `e0b30b6f548ec7fb53a6a8329afbc1a5db52f89e`
before fresh selection and prediction. Its SHA-256 is
`8dee0737a30b166fbc3da2289fcc656b6ff4d2c66c234cf566d390bfb0109314`.
No fitting, threshold adjustment, or model selection occurred in this study.

The holdout has 16,187 positions from 2,122 games: 1,996 unused older games
and 126 newly downloaded 2 November games. Games, full move trajectories and
canonical inputs are disjoint from experiments 237 and 238, including their
pilots. Four selected older games contribute no surviving unique positions.
The older cohort is not a prospective test. Metrics give each game equal weight.

| Cohort | Games | Positions | Calibrated SF log loss | Flat residual log loss | Calibrated SF Brier | Flat residual Brier |
|---|---:|---:|---:|---:|---:|---:|
| Pooled | 2,122 | 16,187 | 0.458595 | 0.449195 | 0.134062 | 0.132081 |
| Older unused | 1,996 | 15,220 | 0.456882 | 0.446069 | 0.132710 | 0.130439 |
| New date | 126 | 967 | 0.485734 | **0.498715** | 0.155473 | **0.158093** |
| Hidden king threat | 302 | 332 | 0.241823 | 0.229074 | 0.067404 | 0.066171 |
| Ordinary | 2,121 | 15,855 | 0.462562 | 0.453304 | 0.135479 | 0.133504 |

Lower is better. Pooled log loss improves 2.05%, narrowly clearing the 2%
requirement. The paired whole-game 95% bootstrap interval for the difference
is [-0.014412, -0.004608]. Pooled Brier, hidden-threat and ordinary safeguards
also pass. **New-date log loss and Brier worsen, so the combined gate fails.**

The secondary query residual has similar pooled loss (0.449189) and also
worsens new-date loss/Brier. It is not a newly selected candidate.

All-row review checks feature/label/native-score alignment and exclusions.
The extraction checks 213,875 source frames and records 515,442 parent-action
values. Independent referee review covers six complete games, 692 frames,
45 selected positions and 1,365 action-value semantics. Independent result
review recomputes every metric, bootstrap and gate, and compares all 16,187
native predictions against CPU inference: maximum probability difference is
8.09e-8 for flat and 8.86e-8 for query.

Original tool handles: selection 50959, extraction 19979, data review 8796,
evaluation 40582 and independent result review 92808, all terminal exit 0.
There was no failed fit to retry and no new GPU run after experiment 239.

## What the failures teach, and what they do not

The post-hoc cohort decomposition is separate from the decision above.
Five games from Farsight–Mist Opportunities and IAmAVirus–Mist Opportunities
contribute +0.014438 to the newer cohort's +0.012981 mean increase. Small,
opponent-named slices are noisy and are not proposed as runtime switches.
Removing them would invalidate the original test.

An independent audit of the five largest game-level regressions validates
521 frames, recorded results and the selected labels' perspective. The largest,
`updro1eg`, is a real late reversal. At ply 94, the correction increases White's
forecast from 0.984 to 0.997; White ultimately loses, ending with a bare king
on an unseen rook line. No label-sign or native-inference error was found.

A post-hoc bootstrap for the 126 newer games gives [-0.008198, +0.036348]
around the +0.012981 difference. Thus these data do not establish a population
regression. They nevertheless fail the frozen nonworsening safeguards.
Standardizing older results by one material-phase, material-balance or SF-score
axis at a time does not explain the reversal; this is not a causal shift test.

The important target limitation remains: a replay's final outcome depends on
both players' policies and private histories. This model sees a complete
hypothesized board, current visibility masks, metadata and a Stockfish score.
It does not see those policies or full information histories. Better prediction
on historical played boards is not proof of better counterfactual frontier
values, strategy, or Elo. Nor can a leaf correction restore a discarded hidden
attacker or a move already removed by the guard.

## Next review recommendation

Preserve the model and native kernel, but close this confirmation. Do not
expand this test until it passes, switch to query, exclude Mist games, or tune
on the new labels. Before another model-size sweep, review the feasibility of
continuations from restored private observation histories under fixed policy
versions. The first deliverable should validate history/clock/repetition
restoration and measure label-generation cost, with no learned engine change.
A later learning experiment would need an independently frozen dataset and
ordinary, hidden-threat and recent-game controls. This is a proposal to Fable,
not a shared agreement or a launched trial.

`result.json`, `review.json`, `holdout-review.json`, `cohort-diagnosis.*` and
`failure-review.*` retain the exact evidence and limitations. `evidence.tar.gz`
contains the holdout arrays, row provenance, native action records, frozen
predictions, and the five audited replay files; `evidence.json` hashes every
member. Models remain in experiment 239's verified model archive.
