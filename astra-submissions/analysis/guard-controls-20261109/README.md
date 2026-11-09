# Guard-disagreement control screen

Frozen64decisions from32 unused historical v37games, four each against eight
relevant opponents. Dates November3–7; game-ID hash selects games, ply hash
selects a later own king move. Each game also contributes its third opening
decision. Two late cases use a general-move fallback. Selection uses no
results; it yields32White/32Black decisions and32opening/32later cases.
These are historical development controls, not a confirmatory arena sample.

One actor reconstructs one belief and searches both masks at2.5seconds each,
with the same seed, fresh identical v38 scorers and alternating arm order.
A raw-memory fingerprint and exported sampled worlds/weights verify that the
belief stays unchanged. Only the mask changes. Actor inputs are observations,
own forced moves and recorded clocks; true boards label choices after exit.
Forced replay does not reproduce historical Stockfish state or exact thinning.

Both-color same-mask and candidate-mask preflight passes. Budget overrides
apply only to this offline paired search; actual180+2 behavior requires full
games. Readout cost is outside the search allocation and included in total
recorded runtime. The existing bounded capture/response probe measures3+
material exposure; it is an omniscient diagnostic with a limited horizon.

Advance to the separately frozen16-game pilot only if all cases complete
without technical/illegal errors, at least4masks differ, at least1newly
admitted action is selected, at most1fatal case breaks, zero opening fatal
cases break, and at most2new3+material exposures occur. These are screening
limits, not a significance test. Fixes cannot cancel broken-case counts.

The initial provisional plan is preserved in prelaunch-plan-initial.json.
Before any actor run, the gate clarified broken versus net counts, added
zero opening breakages and verified owned process-group cleanup. The final
plan and all source hashes are published before the control cohort starts.
No failed first attempt is replaced. Case150s/global40min bound, one0–1pair.

Sources: [prepare](../../experiments/guard-controls-20261109/prepare.py),
[paired actor](../../experiments/guard-controls-20261109/pair.c),
[runner](../../experiments/guard-controls-20261109/run.py),
[review](../../experiments/guard-controls-20261109/review.py).

## Completed control result

Original77529 exited0; all64first attempts complete in466.46seconds with no
faults or illegal choices. Independent course-referee checks2,827source
frames and both chosen moves at every decision. The fixed gate passes:

| Metric | Baseline | Candidate |
|---|---:|---:|
| Immediate king loss | 4 | 4 |
| New fatal cases | — | 0 |
| New opening fatal cases | — | 0 |
| Bounded3+point material exposure | 3 | 1 |
| New material exposure | — | 0 |

Masks differ in13cases; one newly admitted action is selected;14moves change
in total. Equal wall-clock budgets do not give identical tree trajectories,
so changes with the same mask are timing/search variation. The3-to-1material
count is descriptive; it is not a demonstrated causal gain from the rule.

This earns the predeclared full-clock pilot, not a release or Elo claim.
The [pilot source](../../experiments/guard-controls-20261109/pilot.py) packages
an unversioned research ZIP from the exactv38archive, replacing only main.c,
adding the guard header and enabling its flag. Native/model/history/scorer
provenance is pinned in full-games/plan.json. Eightcolor-swapped pairs on
0–1and2–3,180+2,seeds2701200onward. All16must be clean and score>=10points
before a further opponent test is considered. Any technical failure on either
side stops new games; the other in-flight legal game may finish. No attempt
is replaced. The3hourglobal bound reserves time for a complete legal game
before starting each one. All missing/unstarted cells stay explicit.

## Full-clock pilot result

All 16 first attempts completed: **10 wins, one draw, five losses**, or
10.5/16 points. The predeclared 10-point gate passes. White scored 5.5/8;
Black scored 5/8. Eight pair totals are 2, 0, 1, 1, 2, 2, 1, 1.5.
No technical failure or unstarted game occurred. Runtime was 3,722 seconds.

The independent course referee rechecks all 1,365 frames, legal moves,
observations, clocks, repetition and terminal results. Archive/source/binary
hashes and all job receipts match. A read-only host process scan finds no
remaining actor processes in either frozen build directory. The original
runner 66642 is terminal with exit 0. Audit and cleanup receipts are in
full-games/audit.json and full-games/cleanup.json.

This small development duel earns the next opponent comparison, not a
release or an Elo estimate. It used the standard trusted-local referee;
the next comparison explicitly freezes off-turn processes and charges
buffered observations. The matched Misty panel has 16 candidate and 16
exact-v38 control games, common seed/color blocks, a repaired observation-only
adapter and the real installed Rust library. No arena action is authorized
by either result alone.
