# Pawn deductions: better beliefs, mixed decisions

2026-10-07. Adapted from Fable commit `8f6953cd5e59883de31c4dfc5e28b389a0ffcad1`, in Astra's independent source. **Opt-in with `FOW_VISIBILITY_DEDUCTIONS=1`; not packaged or uploaded.** Capture recovery has its own `FOW_CAPTURE_EVIDENCE` switch.

Hidden forward pawn destinations prove an enemy blocker; hidden pawn capture diagonals prove emptiness. These facts constrain both ordinary filtering and recovery. The port omits the original slider-ray inference: an unobstructed own slider's empty or enemy-occupied destination would be visible, so a hidden square there is an invalid observation. Fable accepted that correction. Joint recovery reserves enough non-pawns for mandatory back-rank squares and enough middle-rank slots for remaining pawns.

## Belief-only factorial probe

One public development trajectory, `bluqrpex`, was replayed with four seeds and 2,048 particles. The actor received observations and its own actions only. Each arm has 264 updates and 36 ordinary-capture labels. The binary and move-file hashes are in [the full report](duck-belief-ablation/summary.json).

| Metric | Control | Capture only | Deductions only | Combined |
|---|---:|---:|---:|---:|
| Full observation consistency | 36.20% | 36.51% | 100% | 100% |
| Truth present in population, /264 updates | 74 | 74 | 132 | 132 |
| Collapses | 12 | 11 | 4 | 4 |
| Capture occupancy violations, /36 | 3 | 0 | 0 | 0 |
| Hidden-square categorical Brier, lower is better | .3601 | .3605 | .1772 | .1772 |
| Mean probability on true hidden pieces | .4935 | .4948 | .7403 | .7403 |

Deduction-only and combined happen to coincide here because the improved filter avoids the relevant capture-time recoveries. This does not make the temporal capture constraint redundant: matching a single current view cannot recover what disappeared from a previous view. Full observation consistency on this trajectory is not a theorem that every possible EP/castling/history case is covered.

## Paired action tests

All arms use the same 32-game Duck development corpus, hybrid model, seed 777, 100,000 nodes and the corrected per-color decision stride. The new harness records paired moves, reported king risk, true immediate loss, and the number of true survival alternatives. It fails on illegal moves and separates positions already lost from avoidable blunders.

| Result | Control | Deductions only | Combined |
|---|---:|---:|---:|
| Immediate losses, /218 queried decisions | 21 | 21 | 22 |
| Avoidable losses, /205 positions with a survival alternative | 8 | 8 | 9 |
| Survives recorded losing final position, /31 | 11 | 10 | 9 |

Deductions change 112 moves relative to control: two become immediately safe and two become fatal. Capture plus deductions changes 21 moves relative to deductions alone, adding one fatal choice. The pilots do **not** support a strength claim or promotion. See [deduction comparison](duck-decisions/summary.json), [combined comparison](duck-combined/summary.json), and their complete decision logs.

New fatal deduction choices:

- `j8zn0ugw`, ply 46: Kh2, reported risk 2.5%, versus a safest candidate at 0.3%; 25 true survival alternatives exist.
- `nqasg3lh`, ply 46: Re7, reported risk 6.1%, versus a candidate at 0%; four true survival alternatives exist.

Neither update had collapsed. The corresponding two improvements occur in `5ehltaol` ply 43 and `7fma2thl` ply 85. Improved belief support can alter the representative board, shortlist, sampled columns and regret mixture. These flips alone do not isolate which stage is responsible.

## Tests and decision to keep the feature off by default

The pawn facts were checked on random true boards: 1,949 occupied deductions and 8,587 empty deductions, zero contradictions. The combined random-play belief audit retains truth in 805/1,444 updates, with 13 collapses and 79.6% correctly placed pieces; its 727 checks pass. The course differential test passes 18,625/18,625 checks for this run.

With deductions enabled, two historical engine assertions fail in [full-tests.log](full-tests.log). The queen-grab regression declines the pawn in 5/8 seeds instead of 8/8. A Greek Gift assertion expects the risk filter to reject some moves at a position where the updated belief considers every move risky. These are preserved findings, not silently weakened thresholds. Deductions remain disabled by default pending the broader action gate; the unchanged 575-check engine suite passes in [engine-default-tests.log](engine-default-tests.log). The focused belief audit explicitly enables the combined variant. The earlier [A1 checkpoint](../capture-recovery/README.md) retains the baseline test evidence.

`build-manifest.json` identifies the source used for the factorial benchmark, where both switches were passed explicitly. The subsequent source default change does not change those explicit arm settings. `tools/run_belief_ablations.py` reproduces the four-factor probe using the compiled native probe, and `tools/compare_replays.py` records explicit arm environment overrides and model hashes. Run outputs must use a fresh directory.

Future validation uses the [prospective game gate](../../specs/prospective-gate.json). The already inspected Duck games remain development data.
