# V38: latest-ten operational health snapshot

At11:46UTC10November, the fixed latest10 completed v38 games are **4W–1D–5L**.
No technical loss appears: nine end with king capturable, one by repetition.
All892frames match both native rules and the independent course referee.
The public version record is264W–18D–186L/468 (58.33%); leaderboard snapshot
is1936.85Elo,rank9,v38active. The leaderboard and listing are separate instants.
These are monitoring observations, not a strength comparison or a new gate.

| Game | Opponent played version | Our side | Result | Plies | Material before final loss | True-board safe final alternatives |
|---|---|---|---|---:|---:|---:|
| [v7db05uf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=v7db05uf) | Resting Bishop Faces v8 | black | win | 129 | — | — |
| [0kzcsyma](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0kzcsyma) | Resting Bishop Faces v8 | white | win | 52 | — | — |
| [i1rh0t76](https://www.mit.edu/~6.7980/fow/?tab=arena&game=i1rh0t76) | Knight Vision v36 | white | loss | 121 | -28 | 3 |
| [dtrqn6dx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dtrqn6dx) | Foggy Fischer v4 | black | win | 117 | — | — |
| [2vlo0g4q](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2vlo0g4q) | Foggy Fischer v4 | white | draw | 106 | — | — |
| [yvdanhyy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yvdanhyy) | Knight Vision v36 | black | win | 63 | — | — |
| [b1ytfdk7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=b1ytfdk7) | Farsight v27 | white | loss | 77 | -8 | 3 |
| [0xe4vmwz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0xe4vmwz) | Farsight v27 | black | loss | 68 | -1 | 0 |
| [nxraw4an](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nxraw4an) | Greek Gift v25 | black | loss | 90 | -10 | 0 |
| [t3dl0bfj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=t3dl0bfj) | Greek Gift v25 | white | loss | 59 | -8 | 6 |

## What deserves attention

The five losses are king-capture terminations, but their final moves have
different meanings. Farsight Black `0xe4vmwz` and Greek Gift Black `nxraw4an`
have **zero** safe legal moves on the true board at that final turn; the course
referee independently confirms both. A final-turn guard cannot save them.
The other three have true-board one-ply escapes, with every final attacker
hidden before our move. This does not show that the runtime belief retained
those worlds, priced the threat, or could certify a common safe action.

Four losses are already8+ material points behind before their final move.
Against Knight Vision, our only remaining piece is the king, facing two
promoted queens plus other pieces. Its three safe king moves postpone the
terminal event; counting that as an ordinary avoidable final blunder would
misplace the improvement priority. Farsight Black is only one point behind
but in a forced immediate loss. The useful next diagnostic is the earlier
formation of that net, and the earlier material swings in the other losses.
This does not reopen the failed hazard, generic king-walk or guard sweeps.

We beat Knight Vision as Black in the paired recent games and lose as White;
one game each is insufficient to attribute the difference to color or policy.
Two recent Farsight losses used opponent v27; the leaderboard now lists v28
at1988Elo/rank7. Preserve that played/current-version distinction. Farsight is
not a frozen reference ID in307. That test's scope stays unchanged; it cannot
be advertised as a direct validation of this rising opponent's behavior.
This snapshot contains no Duck, Instructors or HYPOTHERMIA games.

There are three first-own-queen-loss events: two exchanges within three plies
on either side, and one with no opponent queen loss in the next three plies.
The queen-exchange label is a bounded piece-count description, not a tactical
judgment. The lowest recorded own clock is19.17seconds; there is no observed
time forfeit, which does not prove the time policy is optimal.

## Integrity and storage

Source/plan8df520ef was verified on both mirrors before original handle49045.
It exited0 after13GET attempts (one replay required a second attempt), with
1.2s minimum spacing. Ten first-page IDs were sealed before replay reads,
without outcome/opponent filtering. Each replay hash matches its API receipt.
A fresh course reconstruction independently verifies every frame, terminal
result and the five final-turn safe-move sets. Two old synthetic fixtures
check hidden-queen attribution and a queen exchange before the network run.

The bounded private working archive is on the root SSD, not the unstable
Seagate. No shared raw journal, daily report, training export or persistent
replay watcher was modified. This does not repair the shared drive. All these
completions precede307's12:00UTC cutoff; no307future data or model scores are
opened. No fit, GPU, runtime change, successor ZIP or arena action follows.

Evidence: [fixed plan](plan.json), [result](result.json),
[independent review](independent-review.json), [material context](terminal-context.json),
[unchanged shared taxonomy labels](taxonomy.json), [execution](execution.json).
Raw replay paths and hashes are in the plan/result; they remain a private
bounded working cache rather than a replacement shared corpus.

## Concrete earlier-turn witness — exploratory

In Farsight Black's loss, at ply66 we promote `a2a1r`; White replies `f7g8`,
then our king captures that queen and loses to the rook on f8. Checking the
true position one turn earlier separates the mechanism from the final guard:
among36 legal black moves, five immediately lose the king; the recorded
`Qg8` reply traps all responses after28 others, including our promotion.
`Qd5` and `Qc4` retain a queen capture on g8 against that recorded reply;
`Qxf2` instead makes the recorded `Qg8` lose White's king. These are oracle
counterfactuals against **one reply**, not certified good moves against other
responses or recommendations available from Black's view.

The composable motif is a guarded adjacent-square bait against a boxed king,
with a non-king recapture or a forcing counter-threat as possible resources.
A promotion's material gain can leave that next-turn net intact. The useful
runtime question is whether the f8 defender/king region was represented and
whether the earlier search priced the net. This snapshot does not run the
engine or measure belief membership, weights or search allocation.

[Counterfactual source](counterfactual.py) and [all36 results](counterfactual.json)
preserve the exploratory selection and limited scope. The existing256 tests
already checked mate-label parity on their played/frontier panels, and266
already proposed selective rescoring. Neither is a new discovery here. No
paired scorer evidence in this game blames v38's approximate evaluator or
reopens that pending proposal.
