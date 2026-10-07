# Fog of War bot — IAmAVirus (C++)

Alpha-beta search over an explicit belief distribution, with the root move chosen
by solving a matrix game rather than by taking a best response to a single guess.

`build.sh` compiles it; `run.sh` starts it; `test.sh` runs every test.

## Why this is not a chess engine with the lights off

`referee.py` decides a game in `outcome()`: if the side that just moved left its
king capturable, it has already lost. There is no check, no checkmate, no
warning. Two consequences drive every design choice here:

* **Losing is one mistake.** Every local test game ended by a king being
  captured, median 20 plies, never by grinding out material. King safety is not a
  positional refinement; it is the win condition.
* **A threat the opponent cannot see is not a threat, it is a win.** Visibility is
  your own pieces plus the destinations of your own legal moves, so a rook
  attacking a king from three squares away is normally invisible to its owner —
  and invisibility implies safety, because if they could capture the attacker its
  square would be one of their move destinations and therefore visible.

## Structure

| file | role |
|---|---|
| `bitboard.h/.cc` | magic bitboards; O(1) slider attacks |
| `position.h/.cc` | board state, Fog of War move generation, incremental hashing |
| `observation.h/.cc` | exact legal moves from one observation; the visibility rule |
| `evaluation.h/.cc` | material, placement, activity, and the fog term |
| `transposition.h/.cc` | fixed open-addressed table, 16-byte entries |
| `search.h/.cc` | alpha-beta with the referee's terminal rule |
| `belief.h/.cc` | particle filter over the opponent's position |
| `regret.h/.cc` | regret matching for the root matrix game |
| `engine.h/.cc` | the decision procedure |
| `bot.cc` | the arena protocol |

## The three ideas that matter

**Legal moves are exactly computable from one observation.** A legal move's
destination is always visible, and so is every square a slider crosses, since
each is the destination of a shorter move by the same piece. So discarding
anything that touches an unseen square discards nothing legal and admits nothing
illegal. An illegal-move forfeit is therefore *structurally impossible*, not
merely unlikely.

**The opponent is a distribution, not a board.** Each particle is a complete legal
game state. On the opponent's move, every particle's legal moves are enumerated,
those incompatible with the new observation are dropped, each particle is
reweighted by how much of its probability mass survived, and the population is
resampled. Compatibility is a handful of bitwise operations: restricted to the
squares we can see, a particle's pieces of each type must equal exactly what we
observe. Several inferences then fall out for free that hand-written rules get
wrong — if one of our pieces vanishes, only hypotheses containing a piece that
could have captured it survive, so the capturer's identity is *inferred*; piece
counts stay exact; a piece that walks out of view is still somewhere.

**The root is a game, not an optimisation.** Rows are our candidate moves, columns
are hypotheses about the hidden position, payoffs come from searching each pair.
Regret matching solves it and we sample from the equilibrium mixture. Nature is
allowed to concentrate on whichever hypothesis hurts us most, so a move that is
brilliant against the likely board but fatal against a plausible one does not
survive. Playing a mixture also leaves a repeat opponent nothing to predict.

Search scores wins and losses **asymmetrically**: our king's position is known
exactly, so a line losing it is real, whereas a line taking theirs rests on a
guess. Pricing the win lower makes the engine decline speculative king hunts.

## Verification

`test.sh` builds and runs everything. Highlights:

* Magic tables checked **exhaustively** against a ray-walking reference —
  112,219 assertions, every square and every relevant blocker pattern.
* Fog of War perft against values produced by `referee.py`; these differ from
  orthodox chess precisely because there is no check restriction (197,742 at
  depth four, not 197,281). Make/unmake round-tripping and the Zobrist key are
  verified at every node.
* A **differential test against `referee.py` itself**, the arena's own rules:
  move lists, perft, both sides' observations, exact legal moves from an
  observation, and en passant inference over positions reached by random play.
  47,875 of 47,875 checks agree.
* Belief invariants audited over whole games: no hypothesis ever contradicts an
  observation, material is never invented or lost, and ~76% of enemy pieces are
  located exactly.
* Regret matching checked against closed-form equilibria.
* Every move the engine returns in whole games is verified legal, and the clock
  budget is never overrun.

One caveat the tests make explicit: **exact state tracking is impossible here, not
merely hard.** Measurement showed roughly twenty of the opponent's thirty moves
are typically invisible, so the consistent-position set grows by that factor each
ply. The filter represents the posterior; it does not chase the truth.

## Performance

~11 M nodes/sec, depth 11 in one second and depth 12 in four, measured on the
author's machine. For comparison, a Python implementation of the same algorithm
reached 44 k nodes/sec and depth 6. The gain came from doing less work rather
than from micro-optimisation: an incremental material/placement accumulator, one
fused activity pass instead of eighteen `AttackersTo` calls, and pawn pressure as
two bitboard shifts. `-O3` measured *slower* than `-O2`.
