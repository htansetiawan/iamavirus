# 167 — Astra: r3 regression and confirmed capture-risk bug

27 October 2026, investigation beginning 06:15 UTC. Henry asked why r3 loses
more than v35 against Misty and whether this is a bug. Fable is investigating
alongside this read-only review. The running candidate and queue remain frozen.

## Results at the 72-game snapshot

| Comparison | W–D–L | Points |
| --- | --- | --- |
| r3 vs Misty | 14–3–7 | 15.5/24 (64.6%) |
| v35 vs Misty, same seed/color assignments | 17–3–4 | 18.5/24 (77.1%) |
| r3 vs v35 | 7–1–16 | 7.5/24 (31.3%) |

Direct r3-v35 results are particularly poor as Black: 1 win, 11 losses.
The Misty difference is −12.5 percentage points. Resampling the 12 complete
four-game seed blocks gives an approximate 95% interval of −37.5 to +12.5
points; this is an interim descriptive interval, not a sequential significance
test. The score gap alone cannot distinguish a bug from a bad policy change.

The [independent interim audit](../astra-submissions/analysis/v36-execution-20261027/interim-audit-0615.json)
found no changed inputs, invalid jobs or inconsistent replay frames. It flags
one time forfeit for attribution: `v36r3-vs-misty`, pair 6, r3 Black. The replay
explicitly records `failedSide: white`, which is **Misty**. r3 won that game.
That is not an r3 time failure. The auditor's conservative `rejected` status
at this point means a non-board ending needs review; it is not a causal finding
about r3 or a completed score-gate verdict.

## Confirmed defect in the actual frozen C code

`best_capture_net()` makes an opponent capture and estimates material exchange,
but does not check whether that capture immediately loses the opponent's king.
It therefore treats some losing opponent moves as credible material wins. A
king capturing a defended rook is a particularly clear counterexample: the
helper subtracts the king's zero material value and counts a five-pawn loss,
even though the referee ends that continuation in our favor.

This is not just a hypothetical example. In
`data/arena_local/builds/v36r3-vs-misty-p0-a-white.json`, White decision 28,
the true position is:

```text
2r1k3/1p1R1p2/q5p1/2b5/4PB1p/7P/P4PP1/1R4K1 w - - 1 28
```

The captured stderr explicitly says **`piece veto b1d1`**; r3 played `d7b7`.
Rb1–d1 would defend the rook on d7. The only charged piece-loss reply on this
true board is Ke8×d7, which exposes Black's king to the rook on d1 and loses
immediately under the course rules.

I compiled a small fixture including the **actual frozen r3 `main.c` and
`board.c`**, verified against the ZIP member hashes. With this one-board belief
and the two candidate moves, the actual functions produce:

| Quantity | Actual r3 result |
| --- | --- |
| Piece-loss probability assigned to Rd1 | 1.0 |
| Piece-loss probability assigned to Rxb7 | 0.0 |
| v35 king/queen filter excludes Rd1 | No |
| r3 filter excludes Rd1 | Yes |
| Black immediately loses after …Kxd7 | Yes |

Fixture and result: [reproduce_capture_risk.c](../astra-submissions/analysis/v36-execution-20261027/misty-regression/reproduce_capture_risk.c),
[native-reproduction.json](../astra-submissions/analysis/v36-execution-20261027/misty-regression/native-reproduction.json).
This establishes a real event-calculation defect and shows it changes the
filter on the true world. It does **not** establish the true world's weight in
the played posterior, or prove that choosing Rd1 would have won the game.

The older v35 `queen_risks()` and disabled `material_risk()` use the same
terminal-blind pattern. r3 extends this problem to rooks and minor pieces;
it is not evidence that every difference between v35 and r3 comes from a
newly introduced implementation error.

## How widespread, and what remains uncertain

The read-only [analysis](../astra-submissions/analysis/v36-execution-20261027/misty-regression/analyze.py)
examined the captured diagnostic tails and actual boards of all 72 games.
It found logged piece vetoes for which the true-board piece event consists
solely of opponent captures that immediately lose:

- Against Misty: **92 candidate-move vetoes**, in 56 decisions across 14 games;
  three of those games were losses.
- Against v35: **115 candidate-move vetoes**, in 43 decisions across 11 games;
  four of those games were losses.

These counts are not 207 proven losing moves. Several are alternative moves
at one decision, many occur in games r3 won, and a correct different hidden
world can still justify a veto. The stderr capture keeps only a 16 KiB tail,
so early decisions are incompletely observed. The first truncated block is
excluded from counterexample extraction.

All seven r3 losses to Misty end with an attacker hidden in r3's immediately
preceding observation: six rook/queen attackers and one pawn. The bot
was already behind on true material in all seven (−2 to −14). This describes
the final failure, not the earlier causal mistake. A posterior failure and
an overly restrictive material guard can coexist.

Available search summaries do not show an order-of-magnitude throughput
collapse. In the captured middle-phase decisions, median nodes are about
206,536 for r3 vs 208,668 for v35 against Misty; later, 134,012 vs 134,488.
r3 leaves fewer root choices (middle median 25 vs 34, later 12 vs 20).
These are different positions and truncated samples, so neither comparison is
a controlled estimate of overhead. Exact guard timing needs separate logs.

## Action sent to Fable

1. Reproduce the real position and add regression fixtures for both a king
   taking a defended piece and a non-king capture that ignores a king attack.
2. Make hypothetical capture scoring terminal-aware before treating a reply
   as material danger. Review the older queen/material helpers explicitly;
   avoid silently conflating a broader fix with the piece-only candidate.
3. Preserve r3 and its results. Any correction gets new immutable bytes and
   a documented revised validation plan; do not mix corrected games into
   the present gate or reuse its holdout as fresh evidence.
4. Inspect actual-posterior effects and tactical compensation after the fix.
   A terminal-aware one-ply material veto can still reject a useful sacrifice.

Fable independently confirmed the missing terminal test and reported that
new fixtures fail on the original helper in both colors while the controls
pass. A correction is being developed separately. Astra also raised a
partition edge case: `piece_risks()` uses `best_capture_net()` to decide which
worlds belong to the queen term, but `queen_risks()` has its own capture loop.
Changing only the former can make the two disagree and double-count a world
with a suicidal queen capture and a separate real rook loss. Their event
definitions must agree; any correction to both guards must be declared as
such and tested, rather than described as a piece-only change.

**Conclusion:** a real calculation bug is confirmed and is a credible
contributor to r3's regression. The complete score difference has not been
causally explained. The current r3 should not be recommended for upload with
this known defect, even if its remaining games improve the aggregate score.
