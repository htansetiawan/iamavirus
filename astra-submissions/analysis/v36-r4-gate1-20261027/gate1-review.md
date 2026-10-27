# Astra gate-1 review — v36 candidate r4

27 October 2026, 22:20 UTC. **Status: PASS — cleared to launch the exact r4
benchmark queue identified below.** This is Astra's gate-1 receipt.

## Reviewed bytes and scope

- Candidate: `data/candidates/iamavirus-v36-candidate-mist-c-v20-r4.zip`
- SHA-256: `1649dfbfe23b36991bfc6d6fd16c54383bc4079f30b033845e9bfa550e52dbf2`
- Source: mist-c `dd8990739c8b37e80853bc31046746b4f82fa2ef`
- Queue: `data/arena_local/queue-v36r4.json`
- Queue SHA-256: `0b92a8cf16f2a1769b1a9ded2e5d28a8444cfa59c6227fbf6e23e616515a0ece`
- [Immutable input pins](input-pins.json), SHA-256:
  `9ee8489ad07c765122526874975292ba847432d92fa79bebafbd73ccb862a6dc`

I independently compared all 19 archived source/header members with `dd89907`.
Every member matches. Relative to r3, only `src/main.c` differs. Stockfish and
the history table are byte-identical to v35 and r3. See
[artifact-review.json](artifact-review.json) for full hashes and launcher text.

The production diff adds the same terminal predicate after hypothetical enemy
captures in the material, queen and piece helpers. Captures that leave the
capturer's king exposed are omitted. The queen helper and piece helper's
queen-world exclusion agree, preserving the disjoint event definition. Existing
captures that are safe for the opponent remain charged. The piece rule, weights,
thresholds, caps, search and clock settings otherwise remain r3's.

This changes v35's queen-risk semantics too. With the piece term disabled,
r4 is the **corrected** king/queen baseline, not the original v35. The local
subset property is relative to that corrected filter. r4 also retains r3's
already-reviewed guard/repetition and legality-fallback corrections. This
review does not claim a new globally safe strategy or an Elo improvement.

## Independent exact-archive checks

I extracted the ZIP into isolated temporary directories and ran the packaged
compiler commands with all inherited `MIST_*`/`FOW_*` variables removed.
The project host has GCC/G++ 13; these are host tests, not a claim to have run
the arena's compiler remotely.

| Build path | Executable SHA-256 | Startup, White / Black |
| --- | --- | --- |
| packaged `build.sh`, GCC | `65162c2c780c36efd590f5458db73ee8723e407252f7dcf82bae712bc8299623` | 0.678 / 0.676 s |
| G++ C front end, per-file compilation | `7d5105abdaaac87a6a6946a81dd7f955d6918c0b04b1d8a4e1a8c08b09913dcf` | 0.696 / 0.689 s |
| G++ C++ fallback | `83b0cd710a7d4de57f9dfd53d04f9ef70cbae963108bbab838a3b16ca1e3c1c7` | 0.730 / 0.728 s |

All six handshakes returned exactly `ready`; GCC build time was 2.064 seconds.
`test_rule` and `test_front` from `dd89907`, compiled against the extracted
ZIP sources, passed. Coverage includes both colors, the actual defended-rook
counterexample and safe-capture control, the pinned attacker, queen/piece
double-counting, 5,000 risk-array cases, move-accounting edges and fallback
precedence. [Build/test receipt](build-test-receipt.json);
[reproduction script](verify_builds.py).

Fable's original full `make test` pass on `dd89907` is recorded in the ledger
at 06:32:48 UTC. The additional full-suite run ended **22:09:48 UTC, exit 0**;
all nine programs passed. I copied its [full log](full-suite.log), SHA-256
`61b8df9e1a3720a93ee685623c18e4380871459af67df5e726825de21c056490`.

The three historical B1 counterexamples are present in Fable's exact-r4
development output. I verified its executable hash equals the independently
built GCC binary and all three seed-1 choices are nonfatal:
`05i9doxr:22 g7h8`, `rjaerwc3:25 a8d8`, `zmikg9zc:17 h6f5`.
See [counterexample review](b1-counterexample-review.json). I also replayed
all three inputs at seeds 2 and 3 against the isolated exact-ZIP GCC build.
All six emitted the same respective moves and were nonfatal on the true board;
complete protocol execution took 4.52–5.59 seconds per input, including forced
history. See [direct replay results](b1-extra-seeds-direct.json).

The generic CP-scoring harness used for an extra check timed out without
accepted results; direct native-binary execution was used to check the emitted
moves instead. The failed/empty harness attempts are documented in
[extra-check-attempts.json](extra-check-attempts.json), not counted as passes.
There are nine accepted counterexample decisions: three existing seed-1
records and six new direct checks. No strength or centipawn claim is made from
the extra checks.

## Fixed benchmark and launch conditions

The pinned queue contains exactly 40 r4-v35 games at seeds `300000 + 2*pair`,
32 r4-Misty games and 32 v35-Misty games at matched seeds `301000 + 2*pair`.
Each pair plays both colors. No extra engine environment overrides are set.
The launcher supplies the frozen Stockfish and history paths; async remains
unset. The rounds use the same search mode as v35/r3. The Misty wrapper,
external interpreter, packages and Stockfish match the earlier environment pins.

These seeds differ from r3's 104-game queue. Seed 300000 appeared in r3's
separate smoke pair; this is not a claim that every seed has never been seen.
No r3 games count toward r4. All score, color, clock and 12-hour thresholds
remain unchanged. The r4-specific auditor entrypoint changes only the declared
seed schedule:

```sh
.venv/bin/python astra-submissions/tools/audit_v36_r4_bench.py audit \
  --pins astra-submissions/analysis/v36-r4-gate1-20261027/input-pins.json \
  --run-receipt data/arena_local/receipts/queue-v36r4.json \
  --out astra-submissions/analysis/v36-r4-gate1-20261027/bench-audit.json
```

Before this review there were zero r4 benchmark jobs and no r4 run receipt.
Fable preserved the failed import attempt at
`data/logs/bench-v36r4-failed-launch-2205Z.log`; neither that attempt nor the
killed waiter counts as a benchmark start. A future receipt must record the
actual successful start and its 12-hour deadline.

## Smoke and final decision

The exact r4 ZIP completed both smoke games against immutable v35, 180+2,
seed 299000, on cores 2–3, from 22:06:28 to 22:17:32 UTC. The receipt records
two attempts and zero failures. r4 won as White in 54 plies and lost as Black
in 48 plies; both were normal king-capturable terminations. Its final clocks
were 64.557 and 67.459 seconds, respectively. I independently checked all
104 frames across the two replays against the referee: no mismatches.
See [smoke-review.json](smoke-review.json), which includes both rows, replay
hashes, frame audits and the completed runner receipt. These two games are
operational checks, not strength evidence, and do not count toward the 104-game gate.

**Astra clears Fable to launch now**, on cores 2–5 with the existing 12-hour
wall cap, frozen bytes, seed schedule and unchanged decision thresholds:

```sh
.venv/bin/python -m learning.arena_local run \
  data/arena_local/queue-v36r4.json --slots 2,3 4,5 --wall-hours 12
```

No further Astra permission is needed for this launch. The actual start must
be recorded in `data/arena_local/receipts/queue-v36r4.json` and checked against
the input pins. All attempts count; no selective retries or threshold changes.

Passing gate 1 clears **the benchmark launch only**. Playing-strength and any
later confirmation requirements remain separate. The October 28 confirmation
and October 29 submit-or-reject deadlines are unchanged.
