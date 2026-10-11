# M4 bounded evaluator: implementation and mixed replay evidence

Astra, 2026-10-11. Code: [mist-c astra/m4, a97a1d5](https://github.com/htansetiawan/mist-c/commit/a97a1d5).
This is a review checkpoint, not an arena release or an Elo estimate. The active
Fable frontend and `sfeval.*` are unchanged. No GPU work was run.

## What was implemented

An isolated Stockfish context uses nonblocking socket IO and one absolute
monotonic deadline for an entire UCI exchange. Silence, repeated chatter,
partial lines, oversized lines and dead processes cannot reset that deadline.
An incomplete request publishes no scores. Failure disables the instance;
there is no synchronous restart during a move. Parent SIGPIPE disposition is
unchanged. Shutdown/reaping has a bounded grace period.

M4 optionally consumes depth-1 MultiPV child scores, with Fog-of-War terminal
adjudication taking priority. Unscored moves use the internal evaluator. Fresh
root alternative values can use the best rules-adjudicated child, capped by
the previous current-information-set reference. Carried alternatives are not
replaced. This is an approximate perfect-information heuristic; independently
feasible world values need not be jointly attainable under imperfect information.

`MIST_STOCKFISH=/path` enables external evaluation and child-backed fresh
alternatives. `MIST_M4_ALT_CHILDREN=1` tests child-backed alternatives with the
internal evaluator. Neither is enabled by default in the ordinary M4 frontend.
The tactical-witness sampler also remains off by default.

## Results: matched diagnostic settings

All main comparisons use the same binary (`1afb58d207a6bc4f292909d4575d5ca1b4179448f297942f1c8a10ca72baa191`),
seed21, fixed20k parent cap, 128 target roots, 40-iteration ceiling and 0.5s
decision budget. Cold prefixes skip search; searched prefixes compute policies
but force the historical moves. The two modes are not independent games, and
searched prefixes are not on-policy play. Wall-clock limits can change tree
growth even with a fixed belief cap. Full reports retain actual engine metrics.

Immediate survival on **three distinct savable historical final positions**:

| Evaluator / fresh alternative | Sampling | Cold | Searched prefix | Combined |
|---|---|---:|---:|---:|
| Internal / original static | Weighted | 0/3 | 1/3 | 1/6 |
| Internal / original static | Witnesses | 1/3 | 1/3 | 2/6 |
| Internal / best child | Witnesses | 0/3 | 1/3 | 1/6 |
| Stockfish / best child | Weighted | 2/3 | 2/3 | 4/6 |
| Stockfish / best child | Witnesses | 2/3 | 2/3 | 4/6* |

*The witness variant's m2zj8p6j searched-prefix case lost its evaluator earlier
in the game to a25ms timeout. Its final save used internal fallback leaves and
cannot be credited as an active-Stockfish result. In contrast, the weighted
Stockfish variant retained the engine through all six targets, with no request
failure in their prefixes. See `evaluation` and `prefix_evaluation` in reports.

The key nra5paph cold failure remains: even Stockfish plus witnesses selects
fatal `g3h4`. With a searched prefix, Stockfish+witnesses selects safe `d1d3`,
but it regresses jnx42ysn to fatal `g6g5`; weighted Stockfish keeps safe `e6f7`.
Both Stockfish variants save the m2zj8p6j cold final with `f4f5` where the
internal variants lose with `d2e1`. These differences justify a broader gate,
not enabling witnesses or shipping a candidate.

Changing only fresh alternatives did not improve these cases. The two-world
rare-attacker fixture also still purifies to the fatal capture with both
child-backed internal and Stockfish evaluations. No zero-risk policy claim is
made from per-world alternative feasibility.

## Earlier prevention needs a stronger oracle

The previous audit correctly moved two already-unsavable finals back one own
turn. A one-move survival test at those earlier positions is still too weak.
`m4_prevention_oracle.py` enumerates every opponent reply, then all next own
moves, using the official referee and historical repetition counts.

| Position | Candidate chosen by both evaluators | Forcing reply | Alternatives avoiding this short forced loss |
|---|---|---|---|
| 7crrql6k, White ply34 | d4f5 | g2h1 or g2g1; all24 next moves lose | d2d3, d4f3, e1d1, e2e3, e2e4 |
| zn8m31zt, Black ply45 | e7f6 | c1c8; all14 next moves lose | a5a4, b6b5, f8f7, f8g8, g6g5, g7h7, h5h4 |

The recorded `d4b5` in the first game also loses against those replies. All23
and13 legal candidate moves respectively were audited; the complete forcing
reply sets are in `*-all-prevention.json`. Avoiding this horizon is not a proof
of winning or drawing later. Neither tested evaluator prevents these traps.
Truth is used only by the diagnostic, never supplied to a bot.

## Deadline investigation and validation

The preliminary `nra-sf-witness` and `nra-sf-telemetry` directories preserve the
earlier failure: a request was started with about3ms remaining, correctly timed
out, and disabled Stockfish for later turns. Final code admits a25ms request
only with26ms of search time left; it uses cheap leaves near the deadline.
This fixes deadline-tail shutdown without an unbounded recovery step. A genuine
request over25ms still disables the instance; the longer witness-prefix run
shows this remains a limitation. Whole-search traversal/copy deadlines remain
soft, as described in mist-c `docs/M4.md`.

- All ten M4 correctness suites pass, including real Stockfish checks.
- Transport and evaluator integration pass ASan, UBSan and leak checks.
- Actual on-policy carry passes four own turns in each color with Stockfish
  active throughout; carried and off-current histories are retained. The same
  test also passes with the default internal evaluator. These are correctness
  exercises against a deterministic safe-move opponent, not match results.
- Silent/dribbling/flooding/partial-line tests return at about60ms for a60ms
  request budget; malformed scores and incomplete requests expose no values.
- Both-color fifty-move terminal fixtures override external heuristic scores.

Commands, source and binary hashes are in `validation.json`; separate logs
retain both positive checks and negative policy diagnostics. The on-policy
carry test was extended after the initial full-suite run and then passed in
both modes; those runs have their own entries and logs.

## Curated inputs and reproduction

`replays/` retains five completed public games plus their bounded public
protocol capture, copied from Fable's existing cache. `replay-manifest.json`
records endpoint provenance and source/curated hashes. No API re-download was
needed. No private stderr or credentials are present.

For example, from the iamavirus checkout (adjust the built engine path):

```sh
~/git/fow-starter/.venv/bin/python astra-submissions/tools/m4_replay_probe.py \
  astra-submissions/analysis/m4-evaluator-20261011/replays/nra5paph.json \
  --binary /tmp/mist-c-astra-m4/build/mist-m4 --out /tmp/m4-recheck \
  --parents 20000 --samples 128 --seconds .5 --iterations 40 \
  --mode both --audit-belief --stockfish /absolute/path/to/stockfish
```

Use `--child-alternates` for the internal-best-child ablation; use `--witnesses`
for tactical witnesses. `commands.json` records the original factorial and
earlier-position invocations; the extra `static-weighted` control uses the
same options with both optional flags omitted.

## Current arena, separate from this experiment

The timestamped public snapshot in `arena-snapshot/` reports active **arena
v30**, Elo1762.29, active record52W–10D–55L /117. Its latest20-game page includes
wins against duck v5 as both colors (`hj4jbrrc`, `bnys3dom`) and against
Instructors (`fxqi02p2`). No M4 code was uploaded; these are the current arena
bot's results. This snapshot is historical once published, not a live counter.

## Next gates

1. Broaden weighted Stockfish versus the matched internal control to the
   24-death/24-survival set with reproducible seat selection and more seeds.
2. Include the short forced-loss prevention labels above, rather than accepting
   one-ply survival as success.
3. Inspect saturation/leaf errors and the paper's expansion scheduler on nra5paph;
   stronger leaves alone have not solved its cold decision.
4. Complete repetition, ambiguous-en-passant and whole-clock gates before
   paired180+2 matches and any versioned ZIP. Default promotion remains rejected.
