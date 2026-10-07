# Lessons from the duck games

Written 2026-10-07 from the gold data (`gold/`, 369 IAmAVirus arena games,
11,893 labelled decisions) and the replay of `bluqrpex` (arena v10 vs duck v4).
duck (Elo ~1885) has beaten every version of this bot: **1W–25L** over 26 games.

## What duck does to us

Of 52 decisions against duck in which we left three or more points to an
immediate capture and were then punished, **46 had the capturer hidden from us**,
and **39 of the 52 capturers came from duck's half of the board**: rooks,
bishops and queens striking down files and diagonals into our camp (the
squares where we lost material most often: e4, d5, e6, d1, d4, c3). duck does
not out-calculate us; it keeps long-range pieces on lines that run into the
fog and waits for us to put something on the line.

`bluqrpex`, move by move, is the whole pattern in one game:

| ply | our move | what it did | who punished it |
|---|---|---|---|
| 8 | 5. Nxd5 | captured a pawn protected along the d-file by the queen on d8, which we could not see | Qxd5 (hidden) |
| 26–28 | 14. Nxd5, 15. Rxd5 | the same capture again, then the recapture handed a rook to the knight on f6 (hidden) | Rxd5, Nxd5 |
| 38 | 20. Bd2 | placed the bishop on the d-file, where the rook that had gone d8–d7 in the fog was waiting | Rxd2 (hidden) |
| 50 | 26. Bd3 | moved the bishop next to the rook that had captured on d2 six plies earlier and gone dark again | Rxd3 (hidden) |
| 56 | 29. g5 | ignored the bishop that had captured our pawn on c4 (we saw the capture, never the piece), with the diagonal c4–f1 open to our rook | Bxf1 (hidden) |
| 64 | 33. Kxg2 | no safe move left (0 of 7); the queen on g2 was protected by that same bishop, still on f1 | — |

Every entry but the last is a decision with a safe alternative. The fatal move
is just where the bleeding ends.

## Why the engine does this

1. **The material-risk term only prices the moved piece.** `ExpectedMaterialRisk`
   asks, for each hypothesis, whether the *destination square* of the move is
   attacked. A bishop walking next to a hidden rook, a pawn push that leaves a
   rook en prise to a bishop on c4, a capture whose recapturer is a knight on
   f6: none of these are the moved piece's square being attacked after the
   move in the sense the term measures, or they are priced only one capture
   deep on that square. The matrix game's sampled hypotheses can see them, but
   only if one of eight sampled boards contains the attacker.
2. **The belief loses pieces that captured and went dark.** The filter infers a
   capturer's identity exactly (v3), but after a few hidden plies the prior
   over the opponent's moves spreads that piece over its whole mobility, and
   "it is probably still on d2 / c4 / f1" becomes 30–50%. Each of duck's
   captures above came from a piece we had *seen capture* within the previous
   six plies.
3. **Captures into hidden protection are under-priced** when the protector is a
   long-range piece behind the capture square (d8 behind d5 on the d-file):
   the one-ply exchange on the destination square sees it only in hypotheses
   where the protector is on that line.

## The heuristics that follow, and how each is being tested

- **Price full one-ply exposure, over the population.** Implemented as
  `Engine::ExpectedExposure` (`exposure_mode=1`, `FOW_EXPOSURE_MODE`): after
  each candidate move, in a stride of particles, the opponent's best net
  capture anywhere on the board (victim minus recapturer), averaged. It
  subsumes the old destination-only term and prices items 1 and 3 above. The
  offline benchmark gained a matching metric, "left ≥3 points en prise on the
  true board", for the engine's move and for the move actually played; the
  with/without runs on the 634 real losing seats are in progress.
- **Treat a piece that just captured as still there** unless the view says
  otherwise: a persistence feature in the opponent-move prior (the learned
  prior already has `from_visible_to_opponent`; the piece-that-captured-last-ply
  feature is the next one to add), measured on the same benchmark.
- **Do not put pieces on lines that run into the fog toward a recent
  capturer.** This is a consequence of the first two if they work; it is
  listed so it can be checked directly in the gold data (exposure with a
  hidden capturer from the far half, per version).
- **Stop re-capturing on d5.** Twice in one game the knight-takes-pawn-on-d5
  pattern lost material to a hidden defender; the gold table has 20 such
  captures of a pawn on d5/d4/e4/e5 with a hidden defender across all games.
  A capture-into-fog check (is the destination attacked from any hidden square
  in >x% of particles) is exactly what the exposure term computes.

None of this is proven yet; the benchmark numbers decide, then the arena.
