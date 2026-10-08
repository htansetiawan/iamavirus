# Actual capturer targets for the queen-loss investigation

All **240 selected queen-loss decisions** in Fable's frozen
`data/queen-loss-seats.txt` now have targets recovered from cached public
replays. No records were rejected. These identify the **recorded next-ply
capturer**, including its piece type, starting square, capture move, and whether
it was visible before or after our move. They are a diagnostic dataset, not a
new engine, training run, or arena release.

The frozen corpus and JSONL targets are under
`/media/henrytan/seagate/iamavirus/astra/belief/queen-capturer-targets-20261008/`.
The checked-in `targets-manifest.json` records source, tool and output hashes.
Run `tools/prepare_queen_targets.py` with `--corpus`, `--cache` and a new
`--output` directory to reproduce the extraction. The tool refuses to overwrite
an existing output directory.

| Arena version | Events | Capturer unseen before our move | Newly visible after our move | Our queen moved |
| --- | ---: | ---: | ---: | ---: |
| 4 | 105 | 85 | 63 | 68 |
| 10 | 52 | 44 | 32 | 36 |
| 13 | 37 | 34 | 32 | 27 |

These are server-assigned arena versions. They are not Astra/Fable archive
labels. Older versions supply the remaining 46 events.

`ply` is the zero-based **decision position before our move**. The original
replay frame at `ply` is the observation available to us; `ply + 1` is after our
move; `ply + 2` is after the opponent captures our queen. The manifest's `early`
count means `ply < 30`. It must not be compared directly with a count defined
using the later capture frame: this boundary accounts for 3 versus 2 early
events in version 13, for example.

The extractor verifies the game ID, side-to-move parity, complete recorded move
prefix, three frame indices and encodings, queen occupancy before the capture,
capturing piece occupancy afterward (including promotion), and played version.
It has not yet independently replayed the sequence through the native referee.
Synthetic result/reason fields used to make the old harness visit these seats
are deliberately absent from the target output. They must never become outcome
supervision.

The next belief audit should report three separate quantities:

1. The particle mass on this exact capturer's piece type and starting square.
2. The particle mass on any geometric attacker of the queen after our move,
   which is the union metric in Fable's current `QueenCapturerMass` harness.
3. The probability of a legal queen capture after conditioning on our candidate
   move, including the capturing side's own-king survival rule.

An occupied square, a geometric attack, and a legal capture are different
events. Exchange profitability needs a further check and is not implied by any
of these. The initial audit must reconstruct the actor's observation history
and keep replay truth solely on the diagnostic side; it must not insert the
known capturer into the belief being measured.

These examples were selected because a queen was lost. Better true-attacker
coverage is useful diagnostic evidence, but calibration requires representative
negatives as well. The already inspected examples are development data; reserve
new games for confirmation and retain the king-fatality corpus as a regression
check before promoting a belief change.
