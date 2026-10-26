# Equal-clock leaf-depth experiment

Owner: Astra. Agreed with Claude Fable in chatroom159 and the final ledger
acknowledgement at 2026-10-26 19:52:21 UTC. Fable owns the separate combined
material-risk candidate. The capture-history proposal is deferred.

## Actual implementation

The immutable v35 archive is extracted into `/tmp/astra-leaf-depth-20261026`.
Only `src/sfeval.c` changes: `MIST_SF_DEPTH` controls the UCI `go depth` command.
Default1 preserves the previous setting. Invalid values fall back to1; the
experiment uses only1 and3. All other code, weights, clocks and artifacts stay
fixed. `build.json` pins the source, binary, Stockfish and history-table hashes.
This is an experimental build, not a numbered arena release.

```sh
python3 astra-submissions/tools/build_leaf_depth_candidate.py \
  --archive fable-submissions/iamavirus-v35-mist-c-v14.zip \
  --out /tmp/astra-leaf-depth-20261026
python3 astra-submissions/tools/test_leaf_depth_transport.py \
  /tmp/astra-leaf-depth-20261026 \
  --out astra-submissions/analysis/leaf-depth-20261026/transport-tests.json
```

The build requires a fresh output directory. Nine transport checks pass.
`validation.json` distinguishes the native checks: the unchanged depth1 test
passes; depth3 exceeds its depth1-specific mirror tolerance on one position
(0.148 versus0.12). The separate `native-contract-test.c` logs this diagnostic
instead of asserting that depth1 tolerance, retaining the other interface
assertions. Copy it under the extracted engine's `tests/` and link it with
`src/board.c`, `src/sfeval.c` and `-lm` to reproduce. Both logs and the original
test hash are retained. Eight native calls average about1.03ms at depth1 and
5.53ms at depth3 in this tiny test; this is not a turn-throughput benchmark.

## Fixed screen

The screen started **2026-10-26 19:54:09 UTC**, exec session48822.
`screen/manifest.json` is the live source of status, immutable artifact pins,
per-game results and replay hashes. The launch command is in `run.json`.

Eight matched blocks, four games each: both depths and both colours versus
Misty-v16. Same seeds within comparisons, alternating depth order between
blocks, 180+2 clocks, cores0–1, maximum10,800seconds. The opponent wrapper
uses the existing local Misty environment; its ZIP hash is pinned. Clock and
opponent runtime variability remain, so seeds do not imply deterministic games.

All results are retained. A reliability failure stops the screen for review.
Incomplete blocks at the wall cap are separated from matched comparisons.
At least three extra points in sixteen games per setting, without a reliability
failure, earns further evaluation; it does not establish an Elo improvement.
There is no automatic arena upload and no extra settings or extended matches.

First measured review is due October27 20:00 UTC. The shared submit-or-reject
decision is Thursday October29; outer human review is Friday October30.
