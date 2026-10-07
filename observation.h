// Copyright 2026. Fog of War chess engine.
//
// Turning a 64-character observation into facts.
//
// The arena's visibility rule has a consequence worth stating plainly, because
// the whole engine rests on it: our own legal move list is exactly computable
// from a single observation. A legal move's destination is always visible,
// because the rule says we see the destination of every move we may make. And
// every square a slider passes through is visible too, since each such square
// is itself the destination of a shorter move by the same piece. So discarding
// any move that touches an unseen square discards nothing legal and admits
// nothing illegal -- the filter is exact, not conservative. A move taken from
// LegalMovesFromObservation() can therefore never be rejected by the referee.

#ifndef FOW_OBSERVATION_H_
#define FOW_OBSERVATION_H_

#include <string>

#include "bitboard.h"
#include "move.h"
#include "position.h"

namespace fow {

inline constexpr char kUnseen = '?';
inline constexpr char kEmpty = '-';

// An observation as delivered by the arena: 64 characters in a1..h8 order.
class Observation {
 public:
  Observation() { squares_.assign(kNumSquares, kUnseen); }
  explicit Observation(const std::string& squares) : squares_(squares) {}

  static bool IsValid(const std::string& squares);

  inline char at(int square) const { return squares_[square]; }
  inline const std::string& squares() const { return squares_; }
  inline bool IsUnseen(int square) const { return squares_[square] == kUnseen; }
  inline bool IsVisibleEmpty(int square) const {
    return squares_[square] == kEmpty;
  }

  // Bitboard of unseen squares. Having this as a mask turns per-square belief
  // checks into single bitwise operations.
  Bitboard UnseenMask() const;
  // Bitboard of squares holding a piece of `color` that we can actually see.
  Bitboard VisiblePieces(int color) const;
  // Bitboard of visible pieces of `color` and `piece_type`.
  Bitboard VisiblePieces(int color, int piece_type) const;

 private:
  std::string squares_;
};

// Maps an observation character to a piece type, or kNoPiece.
int SymbolToPieceType(char symbol);
// The character the arena would use for a piece.
char PieceTypeToSymbol(int piece_type, int color);

// Builds a position containing only the pieces we can see. That is all the
// legal-move computation needs, by the argument at the top of this file.
void VisiblePositionFromObservation(const Observation& observation, int side,
                                    Bitboard castling_rights,
                                    int en_passant_square, Position* position);

// Appends our exact legal moves. `visible` must come from
// VisiblePositionFromObservation with the same observation.
void LegalMovesFromObservation(const Position& visible,
                               const Observation& observation, MoveList* list);

// The squares `color` can see in `position`, computed exactly as referee.py's
// observation() does. Used to judge whether an attacker is visible to the
// opponent, which is what makes an attack on their king lethal.
Bitboard VisibleSquares(const Position& position, int color);

// Renders `position` as `color` would observe it, exactly as referee.py's
// observation() does: visible squares show the truth, the rest are unseen.
std::string RenderObservation(const Position& position, int color);

// Facts the visibility rule proves about unseen squares, from one observation:
// squares that must hold an enemy piece and squares that must be empty.
//
// A move's destination is always visible, so an unseen square that would be
// a destination if it were empty cannot be empty: the first unseen square
// along a ray from one of our sliders, and the square in front of one of our
// pawns (or two in front, when the first is visibly empty and the pawn is on
// its start rank), each hold an enemy piece. Conversely a pawn's capture
// square that is unseen cannot hold an enemy piece (the capture would have
// been a move), and our own pieces are always visible, so it is empty.
struct Deductions {
  Bitboard must_hold_enemy = 0;
  Bitboard must_be_empty = 0;
};
Deductions DeduceFromObservation(const Observation& observation, int side);

// Infers the en passant target from the two observations bracketing the
// opponent's move, which is the one piece of state a single observation cannot
// carry. Returns -1 when nothing can be concluded. Ported from the course
// starter's reasoning: a capturable enemy pawn is always visible, so its
// arrival from the start rank can be deduced, and any alternative explanation
// would have disturbed a square visible in both observations.
int InferEnPassant(const Observation* previous, const Observation& current,
                   int side);

}  // namespace fow

#endif  // FOW_OBSERVATION_H_
