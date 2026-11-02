# Private-history continuation generator: feasibility passes

Experiment 241 adds an isolated replay-continuation adapter and a data runner.
Both planned first attempts complete without protocol, legality, clock or
cleanup errors. This is a working data-generation primitive, not a stronger
bot, a new model, or an arena submission.

## What is now implemented

The unmodified course referee runs from the initial board through a recorded
prefix, preserving castling, en passant, halfmove and repetition state. Each
bot receives only its own observations, earlier own actions and own clocks.
Past own actions are forced; after the branch both bots choose new moves.
Recorded elapsed times restore the branch clocks. Thereafter actual measured
time is charged with the recorded increment.

The isolated v37 engine patch enables continuing after the first searched move
and restores its internal post-move clock during forced replay. It does not
change weights, search, guards or Fable's working source. Default one-decision
replay remains available. Both players and their Stockfish workers are frozen
when off turn by the existing process-group controller.

This reconstructs permitted history under the current policy. It does not
reproduce an old process's search/RNG state or measured-cost belief thinning.
Those distinctions remain part of the label's policy definition.

## Validation and cost

The source, fixtures and contract were published before execution at
`a56e26ed3e163688494659b7268ee4840452be41`. Contract SHA-256:
`98214ca175496ff7b121f160a4b03b2a1daadf4e701a9d5be67eb13f35c06c0e`.

Synthetic fixtures pass for castling, en passant, exact prefix clocks, actor
input privacy and threefold repetition. The FEN-only negative control misses
the repetition draw, demonstrating that the earlier history matters. The
actual native engine restores forced clocks correctly for both colours.

Two prefixes were selected by a fixed hash from the completed 457-game refresh,
requiring both teams in its saved top 12 and sufficient prefix length. Selection
did not inspect outcomes. Both policies use the original v37 model/table and
a one-second maximum search budget. Each continuation is capped at 64 new
plies and 300 wall seconds; a horizon cutoff would be censored, never a draw.

| Prefix | Branch ply | New decisions | Reconstruction charged time | Continuation charged time | Total wall time | Result |
|---|---:|---:|---:|---:|---:|---|
| myg7umnl | 32 | 29 | 1.11 s | 25.61 s | 32.37 s | Black wins, king capturable |
| idphh9oj | 33 | 63 | 0.57 s | 55.85 s | 63.17 s | White wins, king capturable |

Original launcher handle 94485 exits 0 after 96.82 seconds for the batch.
Neither job was retried or censored. Host inspection confirms their processes
and Stockfish children are gone. No GPU was used; cores 0–1 are released.

The independent reviewer validates 159 frames with the separate C++ rules
implementation, all 157 clock transitions and prompts, and 312 delivered
observations. It checks complete per-side observation sequences, including
newly generated views after divergence. Recorded engine post-move clocks match
the prefix exactly. Both final outcomes agree with the independent rules.

`label-index.jsonl.gz` exports 92 decision records referencing the two immutable
trajectories. Full histories are stored once per game, avoiding quadratic
copies of observation prefixes. Each record identifies the permitted actor
input, action, outcome perspective, policy and feasibility-only split. **These
are 92 correlated records from two outcome samples, not 92 independent results.**

## Limits and next decision

The measured cost is about 1.05 wall seconds per new decision including setup
and reconstruction, from only two games. It is not a production throughput
estimate. More difficult belief histories, longer games and full-budget search
can cost substantially more.

The one-second policy is deliberately cheaper than the arena policy. Scaling
these labels immediately could simply teach its mistakes. Before bulk data
generation, measure actual arena-budget continuation cost and compare outcomes
on fixed private-history prefixes. Any future dataset must keep all branches
of each source game together in its split, label censored runs separately, and
retain clocks and policy versions. Model inputs must represent the information
state being valued; this generator alone does not fix a board-only predictor's
missing histories.

Proposed next work is a bounded search-budget/target sensitivity pilot, not
another architecture sweep or a model fit on the old confirmation sets. No
new trial or agreement with Fable is claimed by this result.

## Evidence

`plan.json`, `build.json`, `continuation.patch`, `preflight.json`, both job
directories, `summary.json`, `review.json` and the label index preserve the
contract, original attempts and validation. `native-evidence.tar.gz` contains
the exact runner binary and C sources; its manifest hashes every member.
Stockfish and the history table remain pinned to the existing v37 ZIP.
