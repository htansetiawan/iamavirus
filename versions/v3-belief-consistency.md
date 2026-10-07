# v3 — belief consistency (`351ca0b`)

## The bug this fixed

Three rated losses shared a cause. In two of them the piece that captured our
king had, one move earlier, captured one of our own pieces **on that same
square**: `Rxa5` took a pawn then the king on a7; `Rg1xg8` took a rook then the
king on c8. Neither attacker was ever seen — 0 of 40 and 0 of 54 observations.

The consistency check masked by visible squares for **both** colours. That is
right for the opponent, whose position the fog hides, but wrong for us: our own
pieces are always visible, so a square that has gone dark cannot be holding one.
The masked test let hypotheses keep a **phantom friendly piece** where ours had
just been captured, and so never concluded an enemy piece was standing there.

A test written *before* the fix reproduced it exactly: **240 of 256 hypotheses**
kept a phantom rook on the capture square; only 16 inferred the enemy.

## Implemented

- Our own pieces became an exact constraint (`AgreesAboutUs`), not a masked one.
- Expected material risk measured across the **whole** population rather than the
  sampled columns of the matrix game, one capture deep.
- Promotion accounting in the census: seeing a new queen now decrements the pawn
  it came from. Without that, a rebuild handed the opponent a 17th piece.
- Rebuild draws from a pool of free fog squares and places pawns first, since
  pawns are the only constrained piece and were otherwise left with promotion-rank
  squares and silently dropped.

## Results

| measurement | value |
|---|---|
| v3 vs v2, 48 paired games | 0.479 ± 0.072 (~−14 Elo) |
| belief: enemy pieces correctly placed | 75.2% → **76.7%** |
| belief rebuild rate | 25 → 23 per 1,444 plies |

**The head-to-head showed no improvement.** The likely reason is that a
self-play A/B is nearly blind to a symmetric flaw: both binaries' opponents are
the same engine, so a weakness both sides share largely cancels in the score. The
bug cost real games against capture-happy opponents, which self-play does not
reproduce. That explanation is plausible, not verified.

The fix shipped anyway, on the grounds that it is a **correctness** repair rather
than a preference: the old filter believed in a piece it could prove was gone.

## What was learned about method

An earlier message claimed the belief heuristics measured as harmful (0.417). A
repeat measurement of the same comparison returned 0.425 the other way. At 60
games the resolution could not support either claim. This was the first of three
occasions where a 1σ result was read as a direction.
