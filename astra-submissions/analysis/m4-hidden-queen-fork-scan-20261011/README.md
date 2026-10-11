# Hidden-source queen forks in the v30 top-six cohort

This is a retrospective discovery scan, not an Elo test or a runtime feature.
It asks a narrow, composable question: did an opponent move a queen from a
square hidden to v30 into a move that attacked v30's king and a rook/queen, and
was there a legal earlier king move that removed that same king attack?

## Cohort and rule validation

The scanner selected all v30 decisive `King capturable` losses against the
current top six from the local public-replay cache: **145 games / 11,026
frames**. It checked each recorded move, full board, and both side observations
against the course referee before searching. Six games in six separate
histories contained an actual queen move from a hidden source that forked the
king and a major piece. Four did not cause an immediate terminal loss on the
historical reply, so they are leads rather than confirmed fatal examples.

For a negative control, the same scan checked **31 v30 wins** against those
opponents (2,927 frames). One contained a hidden-source queen fork. The bot
captured the revealed queen safely and won. This is a useful counterexample to
an unconditional king-move rule.

## Two exact terminal examples

In `4bkwxxng` against Instructors v4, at ply 53 before `...Qg6`, White's queen
on e3 was hidden from Black. The actual next White move `Qe7` forked Black's
king and rook. After the fork, Black had **1 immediate-survival move among 37**
legal replies (`...Kg8`); the recorded `...Kxe7` ended the game. If Black had
played `...Kg8` at the earlier decision, the same `Qe7` no longer attacked the
king, and **40 of 41** legal replies survived one ply. This does not clear
every queen-fork square: another geometric queen fork remains after `...Kg8`.
The claim is specifically that it preempts the realized `Qe7` attack.

In `69nmui22` against duck v5, at ply 36 White's queen on f6 was hidden. After
White's `Qxg2`, `...Qc3` attacked the king on e1 and rook on a1. White had **3
immediate-survival replies among 23**; the actual `Qg7` lost by king capture.
The earlier legal `Kd1` would leave `...Qc3` legal, but it would no longer
attack the king; **35 of 36** replies then survive one ply. This example has
two decision failures: the earlier prophylactic option was missed, and after
the queen appeared White selected a move that ignored its king attack. The
candidate king move also leaves other possible queen-fork patterns, so this
does not justify an unconditional king-safety bonus.

The win control `b4c61fg2` against Knight Vision v36 had a similar `...Qf2`
fork against the king and rook. White's `Rxf2` safely captured the queen and
the game was won. The exact response set therefore matters: king evacuation,
capturing the queen, and other replies must be evaluated against the actual
belief and continuation.

## Interpretation and next gate

The filter is deliberately stricter than a geometric attack count: the queen
must already have a hidden source at the earlier decision, its actual move
must be a fork in the referee position, and the same fork must be available
before the defender's recorded move. The report preserves six hits and the
win control; four of the six loss-cohort hits did not end on the historical
reply. Do not count those as forced losses.

These full-board labels do **not** establish that v30's belief assigned useful
mass to the hidden queen, nor that a king move is better across that belief.
The decision-time support and response-set gate is now available in
[`belief-response-set-gate.json`](belief-response-set-gate.json). In 20
resampling seeds per setting, prior 2 retained the exact Duck board in 17/20
populations and produced a king-safe move in 19/20, versus 2/20 and 16/20 for
prior 1. On the Instructors example, prior 2 retained the true board in 13/20
populations but placed it in the search's eight-board root sample in only 2/20.
The engine chose the preemptive `Kg8` only 3/20 times; on the exact recorded
`Qe7` fork, that move leaves 40 safe replies, while most other legal replies
leave only 1–3. The visible-queen positive control still selects `Rxf2` in
20/20 seeds for both priors. These results make prior 2 a promising belief
support lead and root-sample coverage a likely bottleneck; they do not establish
strength or justify a default change. The decision harness receives the actual
move sequence as forced history; it does not let its chosen actions alter later
states.

The next engine experiment should preserve broad posterior support for
probability estimates while ensuring the root response-set search sees
low-mass, high-consequence threat worlds. Evaluate the opponent's immediate
king-attacking responses and the number of safe defensive replies after each
candidate. This is a two-ply tactical risk term, not a blanket king-move bonus.
Test it on the six-game hidden-queen cohort and safe-capture controls before
making any source or release change.

## Reproduction

Run inside the starter environment, which provides `python-chess`:

```sh
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/m4_scan_hidden_queen_forks.py \
  --outcome loss --limit 500 \
  --out astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/v30-top6-losses.json

/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/m4_scan_hidden_queen_forks.py \
  --outcome win --limit 500 \
  --out astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/v30-top6-wins.json

/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/test_m4_scan_hidden_queen_forks.py
```

The two JSON reports contain per-game replay hashes, the referee hash, exact
candidate moves and survival reply sets. Current scanner SHA-256:
`092346aae909e58907f684e92eb5a3be0d3fc6224434e2ae89a90f133fb86074`.

The belief-support gate is reproducible with the candidate-v12 sources and the
three cached public replays:

```sh
g++ -O2 -std=c++20 -Wall -Wextra -Werror \
  astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief_support_replay.cc \
  astra-submissions/candidates/v12/{engine,belief,search,evaluation,observation,transposition,regret,position,move,bitboard,neural_observation,neural_inference,opponent_model}.cc \
  -o /tmp/v12-belief-support-replay

python3 astra-submissions/tools/m4_belief_support_gate.py \
  --engine /tmp/v12-belief-support-replay --seeds 20 --particles 2048 \
  --priors 1 2 \
  --out astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief-response-set-gate.json
```
