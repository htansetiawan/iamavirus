# A1: ordinary capture evidence survives recovery

2026-10-07. Implemented in Astra's source copy; **experimental, not packaged or uploaded**. An observation-only correctness improvement has passed tests, but the first decision benchmark does not show a gain.

## Change and scope

An own piece disappearing during the opponent's turn ordinarily proves that an enemy now occupies its square. Legal belief transitions already respect this. The old recovery path discarded the fact when every particle was contradicted. A1 retains the capture square and reserves one compatible enemy from the remaining census there before scattering other pieces. The capturer's type remains unknown; the true replay move is never a live input.

The constraint survives the after-own-move observation, clears if our move captures the enemy, and expires at the next opponent move, when that enemy could relocate. If our just-double-pushed pawn disappears with its square hidden or empty, en passant is possible and this prototype declines to impose an ordinary-capture square. It does not yet implement the joint en-passant disjunction or a multi-turn recovery backlog. Contradictory histories/census are reported rather than made into certainty. `FOW_CAPTURE_EVIDENCE=0` disables the change for ablations.

Trace fields: `capture_sq`, `capture_kept`, `capture_conflict`, `capture_ep_ambiguous`, and actual collapse status. The proposal over compatible piece types is a recovery heuristic, not a calibrated posterior.

## Evidence

| Check | Before | A1 |
|---|---:|---:|
| Ordinary capture occupancy violations, `bluqrpex` × four seeds | 3 / 36 events | 0 / 36 |
| Enemy occupancy on f1 at ply 58, seed 3 | 418 / 2048 particles | 2048 / 2048 |
| Enemy occupancy on f1 at ply 58, seed 777 | 433 / 2048 | 2048 / 2048 |
| Mean full-observation consistency over 264 updates | 36.20% | 36.51% |
| Random-play truth present, 1,444 plies | 621 | 621 |
| Random-play collapses | 19 | 20 |

The probes compare the exact arena-v10 archive with A1. See [probe-summary.json](probe-summary.json) and the full per-update JSONL files. Low full-observation consistency is a separate defect: matching only visible cells ignores some consequences of which squares are hidden. Fable's pinned `8f6953c` deduction patch addresses that complementary issue and will be tested separately and in combination.

All nine C++ unit suites pass, including 726 belief checks and cases for both colors of en passant, visible ordinary capture of a double-pushed pawn, recapture, and constraint expiration. [full-tests.log](full-tests.log) records those passes and a subsequent test-runner path error (`referee` import). With `FOW_KIT=/home/henrytan/git/fow-starter` set, the differential check then passed **30,100 / 30,100** in [conformance.log](conformance.log). The initial failing regression and first passing run remain in `before.log` and `after.log`.

## Paired decision pilot: no improvement yet

The fixed 32-game Duck development snapshot was replayed with the hybrid ONNX model, seed 777, 100,000 nodes per queried decision, and two CPU workers. Control is the immutable **Astra v11 archive**, so this comparison isolates A1 from Astra's earlier shortlist repair. It is not an arena-v10 playing-strength comparison.

| Result | Control | A1 |
|---|---:|---:|
| Queried decisions | 218 | 218 |
| Immediate king losses | 21 (9.63%) | 22 (10.09%) |
| Survives the recorded losing final position | 11 / 31 | 11 / 31 |

[Build provenance](benchmark-build.json) and [pilot report](duck-pilot/summary.json) identify the archive, sources, corpus and binary hashes. Both binaries use the corrected sampling rule `(ply / 2) % stride`, which samples each color by its own decision count. The former `ply % 6` sampled only White, apart from forced losing finals. Therefore these rates are not directly comparable with the older benchmark rates.

This is a selected development corpus with forced public histories. One additional loss does not establish a regression, and exact evidence retention does not establish a playing-strength gain. Keep A1 experimental; next compare deductions-only and combined variants under the same harness, then run paired complete games before recommending an arena upload.

## Reproduce the paired pilot

```bash
.venv/bin/python astra-submissions/tools/compare_replays.py \
  --baseline astra-submissions/analysis/capture-recovery/build/benchmark-baseline \
  --candidate astra-submissions/analysis/capture-recovery/build/benchmark-candidate \
  --corpus astra-submissions/analysis/capture-recovery/duck-seats.txt \
  --model astra-submissions/implementation/model \
  --output astra-submissions/analysis/capture-recovery/duck-pilot \
  --workers 2 --nodes 100000 --mode hybrid
```

The untracked binaries can be rebuilt with the commands in `benchmark-build.json`; extract the specified archive and copy the corrected benchmark harness into it first. This command consumes no GPU and makes no network requests.
