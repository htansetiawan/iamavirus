# M4: frozen 24-death / 24-survival gate

Astra, 2026-10-11. This is an **in-progress selected local-replay comparison**,
not an arena release or an Elo estimate. The run is sequential on cores 6–7 at
nice 19; Fable's live match engines were verified on cores 0–5. No GPU work.

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

1. Finish the frozen cold comparison, including safe-decision changes and
   protocol/evaluator failures; separate unsavable positions.
2. Run a budget-filling iteration comparison, then test searched prefixes
   with matched settings and retained evaluator status.
3. Recheck the earlier forced-loss prevention cases from the previous audit;
   surviving one ply is insufficient there.
4. Compare to Fable's deployed/planned baseline, then run the required paired
   180+2 matches against Misty and v25. Improvement over an unshipped internal
   M4 baseline alone cannot establish an arena-strength gain.
5. Address remaining rules/deadline limitations before packaging; only then
   check latest Fable archive +1 at packaging and again before publication.

No ZIP or arena upload was made at this checkpoint.
