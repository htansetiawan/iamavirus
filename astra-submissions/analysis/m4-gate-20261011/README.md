# M4: frozen 24-death / 24-survival gate

Astra, 2026-10-11. Both **192-decision cold comparisons are complete**: fixed 40 iterations
and a .5-second allowance with a nonbinding iteration ceiling. These are selected local-replay comparisons,
not an arena release or an Elo estimate. The run is sequential on cores 6–7 at
nice 19; Fable's live match engines were verified on cores 0–5. No GPU work.

## Completed cold comparison and time-budget pilot

`cold-05-final.json` records all **192/192 valid decisions**, completed at
08:21 UTC. No protocol failures, reported M4 budget overruns, or Stockfish
request failures occurred. Matched belief fingerprints agree in every pair.

| Outcome | Internal/static | Stockfish/child alternatives |
| --- | ---: | ---: |
| Historical-death decisions surviving now | 14/48 | 15/48 |
| Potentially savable decisions surviving now (exclude d17) | 14/46 | 15/46 |
| Historical-survival decisions surviving now | 48/48 | 48/48 |
| Historical-survival moves changed | 37/48 | 36/48 |
| Mean measured search time | .00969 s | .09967 s |

These are two seeds per seat, not independent games. On paired historical-death
decisions, Stockfish saves six but regresses five; nine survive under both and
28 lose under both. This is no basis to promote Stockfish or M4. Both variants
also change most historical safe moves, so the stated acceptance condition
has not been met. The historical moves come from earlier mist-c versions,
not a newly replayed v6 control.

Among avoidable losses, the recorded true board is in sampled roots in 16
internal and 19 Stockfish decisions. Missing tactical truth explains eight
internal and six Stockfish losses; omitted root truth explains another eight
and six. The unsavable d17 contributes two losses per variant. These buckets
describe where truth is represented, not proof that representation alone
would select the right action.

Seven internal losses have a truly safe, zero-recorded-risk action with a
greater raw value against the final opponent profile than the selected move.
None of the Stockfish losses do. This is a diagnostic of the final profile,
not a best-response exploitability bound or a proof of solver convergence.
The post-hoc minimum-risk selector lowers death-cohort losses from 34 to six
(internal) and 33 to seven (Stockfish), including d17, but changes 31/48 and
34/48 survival decisions. No on-policy claim follows from this post-hoc rule.

### Removing the binding 40-iteration ceiling

`cold-time05-pilot.json` freezes the first **eight decisions** of the next run:
d01 and s01, both seeds and variants. With an iteration ceiling of 1,000,000,
the same .5-second allowance actually limits the solve. Internal search runs
691–794 iterations; Stockfish runs 212–340. Total measured search is
.3768–.3827 seconds; the engine reserves the remaining allowance for snapshot
and cleanup. All eight decisions retain a snapshot, all four Stockfish
decisions retain the evaluator, and no reported deadline overrun occurs.

In d01, the 40-iteration run lost all four decisions. The time-limited pilot
survives three: both Stockfish seeds and one internal seed select `b8a7`;
internal seed 12 still selects fatal `d5e4`. All four s01 decisions survive.
This demonstrates that the iteration ceiling mattered in this case; it does
not establish a general gain or convergence. Different wall-clock runs can
execute different numbers of iterations even at the same random seed.

After verifying the pilot, the same frozen run resumed sequentially for the
remaining 184 decisions. Its immutable configuration is copied in
`cold-time05-manifest.json`; full logs are in the sibling external-disk
directory `cold-time05`. The checked-in pilot stays an eight-decision snapshot.
The original binary and probe remain unchanged.

## Completed time-budget comparison

`cold-time05-final.json` records **192/192 valid decisions**, completed at
08:48:54 UTC. Both evaluators save **15/46 potentially savable death decisions**.
Internal search preserves **46/48** historical survival decisions; Stockfish
preserves **48/48**. They change 29/48 and 35/48 historical survival moves.
No protocol failures, reported M4 budget overruns, or Stockfish request failures
occurred; matched belief fingerprints agree. Mean search times are .37665 s
and .37363 s, with median iterations 960.5 and 343.5 respectively.

`cold-budget-contrast.json` matches every decision against the fixed-40 run.
Internal search gains four death-seat survivals and loses three (net +1),
but introduces two losses on survival seat s18, both seeds. Stockfish gains
two and loses two death-seat survivals (net zero), with no survival regression.
The encouraging d01 pilot therefore **does not generalize to a broad gain**.

The true board is present in sampled roots for 16 internal and 17 Stockfish
avoidable death decisions that still lose. This rules out missing root truth
as a complete explanation. A post-hoc minimum-risk selector saves many of
these but changes most safe-seat moves; it is not a promoted policy. Two
seeds of a seat are correlated, and these cohorts are deliberately selected.
No Elo inference or convergence claim is justified.

The next experiment should test how the tree represents dangerous future
information sets, with a bounded pilot before another full replay gate.
The public Duck opening probe in `../duck-opening-alias-20261011/` confirms
that the unchanged M4 planner already avoids d4 at move three, while neither
cold nor searched-prefix M4 escapes the recorded Qa5 at move four.

## Frozen inputs and comparison

`seats.json` reproduces Fable's `kappa_check.py` selection from the tracked
`calib.json`: all 24 historical deaths with recorded risk above the least-risk
move by more than .01, plus `random.Random(1).sample(eligible_survivals, 24)`.
These are 32 **local completed matches**, not public arena replays. Original
source hashes and sanitized cache hashes are retained. `privateDiagnostics`
and other fields outside the whitelist are omitted from cached inputs.

The official referee reconstructs each entire prefix, checks every move,
verifies the target board and turn, and labels all legal candidate moves with
the historical repetition counts. All 48 original outcome labels agree.
Case **d17 already has no surviving legal move**. Keep it in the raw results,
but exclude it from the denominator of potentially savable losses.

- M4 source: `mist-c` branch `astra/m4`, commit `a97a1d5`.
- Executable SHA256: `1afb58d207a6bc4f292909d4575d5ca1b4179448f297942f1c8a10ca72baa191`.
- Variants: internal evaluator with original static fresh alternatives;
  bounded Stockfish with child-backed fresh alternatives. This bundles the
  evaluator and alternate initialization change; it does not isolate either.
- Both: fixed 20,000 belief parents, 128 requested roots, 40-iteration ceiling,
  0.5-second search budget, seeds 11 and 12, witnesses disabled.
- Cold prefix: historical own moves are forced without prefix search. This
  does **not** test carried blueprints. A later searched-prefix gate and
  on-policy matches are required.
- Total: 48 seats × 2 variants × 2 seeds = **192 decisions**. Cohorts alternate,
  and variant order is balanced. Seeds of one seat are correlated observations.

`cold-05-manifest.json` freezes the runner, probe, executables, seat manifest,
referee hash, CPU affinity, priority and budgets. Full artifacts and logs:

```
/media/henrytan/seagate/iamavirus/astra/m4-gate-20261011/cold-05
```

## Interim checkpoint — not the final gate result

`cold-05-progress.json` freezes **45/192** completed decisions at
**2026-10-11 08:02:21 UTC**. The external-disk `summary.json` continues to
advance; this checked-in snapshot intentionally does not claim completeness.
All 45 have valid protocol prefixes and legal moves. No completed matched
pair has differing belief-count/truth-mass fingerprints between evaluators.

Among completed pairs on the historical-death cohort, Stockfish saves two
seed-decisions lost by the internal evaluator but regresses three that the
internal evaluator survives. There are also four paired losses and three
paired survivals. Ten completed survival-cohort pairs survive under both.
This early mixture does not support enabling Stockfish by default or claiming
the earlier three-position result generalizes.

Case d01 is informative. Truth remains in the belief (mass .03548) and sampled
roots. `b8a7` has zero immediate fatal share in both recorded root profiles and
is the only truly surviving move. The internal variant instead chooses
`d5e4`; Stockfish chooses `d5c4`. The latter's recorded root fatal share is
about .263, yet its raw action value (-.9082) exceeds `b8a7`'s (-.9710).
Truth absence and sample omission cannot explain this particular failure.
Leaf-value calibration, horizon effects, solver convergence and policy selection remain hypotheses
to test; this one case does not prove a universal cause.

The report also computes an explicitly **post-hoc minimum-root-risk selector**:
minimum recorded immediate fatal share, then greatest raw action value, then
UCI order. It does not inspect truth to select its move; the referee checks
the selected alternative afterward. At this partial checkpoint it removes
several immediate losses without adding one on the observed survival seats.
It changes many decisions and has no on-policy or strength evidence. Do not
treat it as a promoted safety policy or tune thresholds on this selected set.

### The iteration ceiling is a material limitation

This deliberately reproduces the earlier 40-iteration diagnostic setting. At
this checkpoint, decisions finish far short of the .5-second allowance.
Equal ceilings therefore do not imply equal consumed search time. Before
attributing a failure to the architecture or publishing a candidate, repeat
with a sufficiently high iteration ceiling so the wall-clock budget actually
limits search. The cheap internal evaluator can then spend its throughput
advantage on more solver updates/tree growth. A 40-iteration final strategy
is not evidence of convergence. This gate measures the declared bounded
configuration, not each evaluator's best real-clock behavior.

## Reproduction and continuation

Use the starter virtual environment for the referee's python-chess dependency:

```sh
taskset -c 6,7 nice -n 19 /home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/m4_gate_run.py \
  --seats astra-submissions/analysis/m4-gate-20261011/seats.json \
  --run /media/henrytan/seagate/iamavirus/astra/m4-gate-20261011/cold-05 \
  --binary /tmp/mist-c-astra-m4/build/mist-m4 \
  --stockfish data/arena_local/builds/mist-c-v8/bin/stockfish
```

The current runner must finish or be confirmed absent before resuming. Its
file lock rejects concurrent runners. Verified receipts are reused; failures
remain failures rather than being retried until they pass. Interrupted attempts
are preserved. A changed configuration requires a new run directory. Do not
overwrite the source binary while this frozen comparison is being completed.

```sh
python3 astra-submissions/tools/m4_gate_report.py \
  /media/henrytan/seagate/iamavirus/astra/m4-gate-20261011/cold-05 \
  --out /tmp/m4-current-report.json
```

The runner clears inherited `MIST_*` settings, validates the chosen seat,
referee safe-move set, protocol prefix, output count and legality, and retains
all process failures. Each probe owns a new process group. Its timeout kills
both the probe and engine descendants. The process-group termination check
passed with a sleeping grandchild, and mismatched executable fingerprints are
rejected. Initial eight receipts were reused successfully when the full run
resumed. Search and replay elapsed times are distinct: replay time includes
all historical belief updates and post-choice diagnostics.

## Remaining promotion work

1. The fixed-iteration cold comparison is complete; its final report above
   separates unsavable positions and records safe-decision changes.
2. Both cold comparisons and the small public opening searched-prefix probe
   are complete. Broader searched-prefix behavior remains unmeasured.
3. Recheck the earlier forced-loss prevention cases from the previous audit;
   surviving one ply is insufficient there.
4. Compare to Fable's deployed/planned baseline, then run the required paired
   180+2 matches against Misty and v25. Improvement over an unshipped internal
   M4 baseline alone cannot establish an arena-strength gain.
5. Address remaining rules/deadline limitations before packaging; only then
   check latest Fable archive +1 at packaging and again before publication.

No ZIP or arena upload was made at this checkpoint.
