# Native risk-label validation and recorded-training overlap

2026-10-25. Astra. Follow-up to the opt-in PPO risk auxiliary in chatroom 143.
These are completed prerequisites, not a new trained model or strength result.

## Native labels agree with an independent referee

The validator freezes the current C++ simulator sources and builds a separate
library under `astra-submissions/build/`. Fable's sources/build are untouched.
It replays the full prefixes of the 80 diagnostic games. At every prefix
position it compares true boards, both observations, complete candidate sets,
turn and termination status, and every candidate's danger label against the
independent Python referee. It also checks that querying labels leaves the
native board and candidate identities unchanged.

| Check | Completed |
|---|---:|
| Game prefixes | 80 / 80 |
| Decision positions | 5,279 |
| White / Black positions | 2,657 / 2,622 |
| Candidate danger labels | 163,946 |
| Fatal candidate labels | 6,746 |
| Castling / promotion / en-passant candidates | 456 / 212 / 7 |
| Mismatches | **0** |

Total wall time was 22.27 seconds, including 14.87 seconds preparing the native
build. All 5,279 native danger queries together took 0.0623 seconds. The latter
includes the Python wrapper call/copy but excludes referee work; it is **not**
end-to-end RL throughput. These prefixes include repeated opening positions,
so 163,946 labels are not independent samples or exhaustive rules coverage.

- [Validator](validate_batch_risk_labels.py)
- [Source/library hashes, per-game counts and target labels](native-risk-label-validation.json)

## The old-model diagnostic is partly, but not wholly, training-overlapped

We checked the actual frozen `run.json`, copied dataset manifest and shard
hashes for the October 8 attention-small model. The frozen manifest refers to
the former `seagate` mount; identical shard hashes were verified at `seagate1`.
The repository's general v4 manifest has different paths and is not substituted
for this run's recorded manifest.

The audit reconstructs complete move sequences from both player episodes and
reproduces the runner's deterministic selection of 3,766 training games and
64 validation games. It checks both game identities and identical complete
move sequences, even under another game ID.

| Diagnostic subset | Games | v35 fatal | Unrestricted min-neural-risk fatal | Current-root min-neural-risk fatal |
|---|---:|---:|---:|---:|
| Recorded training overlap | 4 | 1 | 2 | 1 |
| No recorded training/selected-validation overlap | 76 | 9 | 36 | 7 |

The four training-overlap IDs are `1hcyolra`, `y4ysglxn`, `ecrdf4z2`, and
`7d35omev`. No additional cases overlap the selected validation games.
The unrestricted head's failure persists when those four are excluded.

This does not turn the 76-case subset into a preregistered population holdout:
the panel was selected by tactical outcomes, shorter shared prefixes and
transpositions remain, and other experiments/human analysis are outside this
run's provenance. No calibration coefficient or model was fit here.

- [Overlap auditor](audit_danger_training_overlap.py)
- [Verified partitions and case-level overlap](existing-danger-training-overlap.json)

## Decision

The native candidate-label prerequisite for the proposed PPO auxiliary passes.
There is no justification for replacing the C guard with the frozen old head.
The next proposed investment is still the bounded original-loss versus
auxiliary-loss training comparison in [the review document](risk-learning-report.md),
with a later-time game-disjoint validation set chosen before fitting and a
separate check of the final deployed selector. Do not add another guard-constant
sweep or treat the preceding conformance checks as Elo evidence.

```sh
taskset -c 0,1 .venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/validate_batch_risk_labels.py
taskset -c 0,1 .venv/bin/python \
  astra-submissions/analysis/deeprl-table-audit-20261025/audit_danger_training_overlap.py
```
