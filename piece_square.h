// Copyright 2026. Fog of War chess engine.
//
// Piece values and piece-square tables.
//
// These live in their own header because Position maintains a running
// material-plus-placement total as pieces are added and removed, which makes
// that part of the evaluation O(1) per move instead of a loop over all 32 pieces
// on every call.

#ifndef FOW_PIECE_SQUARE_H_
#define FOW_PIECE_SQUARE_H_

#include <array>

#include "bitboard.h"

namespace fow {

inline constexpr std::array<int, kNumPieceTypes> kPieceValue = {
    100,  // pawn
    325,  // knight
    335,  // bishop
    500,  // rook
    950,  // queen
    0,    // king: never counted, it is the win condition instead
};

namespace internal {

using SquareScores = std::array<int, kNumSquares>;

inline constexpr SquareScores kPawnTable = {
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 18, 18,  0,  0,  0,
     5,  5, 12, 27, 27, 12,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    55, 55, 55, 55, 55, 55, 55, 55,
     0,  0,  0,  0,  0,  0,  0,  0,
};

inline constexpr SquareScores kKnightTable = {
   -50,-35,-30,-30,-30,-30,-35,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 12, 16, 16, 12,  5,-30,
   -30,  0, 16, 20, 20, 16,  0,-30,
   -30,  5, 16, 20, 20, 16,  5,-30,
   -30,  0, 12, 16, 16, 12,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
};

inline constexpr SquareScores kBishopTable = {
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  8,  0,  0,  0,  0,  8,-10,
   -10, 12, 12, 12, 12, 12, 12,-10,
   -10,  0, 12, 12, 12, 12,  0,-10,
   -10,  5,  8, 12, 12,  8,  5,-10,
   -10,  0,  8, 12, 12,  8,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
};

inline constexpr SquareScores kRookTable = {
     0,  0,  4,  8,  8,  4,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    12, 18, 18, 18, 18, 18, 18, 12,
     0,  0,  0,  5,  5,  0,  0,  0,
};

inline constexpr SquareScores kQueenTable = {
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  4,  0,  0,  0,  0,-10,
   -10,  4,  4,  4,  4,  4,  0,-10,
     0,  0,  4,  4,  4,  4,  0, -5,
    -5,  0,  4,  4,  4,  4,  0, -5,
   -10,  0,  4,  4,  4,  4,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
};

// A fog king is safest tucked into a corner behind its own pawns, and that stays
// true deeper into the game than in orthodox chess: there is no mating net to
// walk into, only a single fatal discovery.
inline constexpr SquareScores kKingTable = {
    18, 32, 16,  0,  0, 12, 34, 20,
    16, 18,  0, -8, -8,  0, 18, 16,
   -14,-22,-22,-28,-28,-22,-22,-14,
   -28,-34,-34,-42,-42,-34,-34,-28,
   -42,-48,-48,-56,-56,-48,-48,-42,
   -50,-56,-56,-62,-62,-56,-56,-50,
   -56,-60,-60,-66,-66,-60,-60,-56,
   -60,-64,-64,-70,-70,-64,-64,-60,
};

// Flattened to [piece][color][square], with the mirroring for Black and the
// piece's material value already folded in, so one lookup gives the whole
// contribution of a piece standing on a square.
constexpr std::array<std::array<SquareScores, kNumColors>, kNumPieceTypes>
MakePieceSquareTables() {
  const std::array<SquareScores, kNumPieceTypes> source = {
      kPawnTable, kKnightTable, kBishopTable,
      kRookTable, kQueenTable,  kKingTable};
  std::array<std::array<SquareScores, kNumColors>, kNumPieceTypes> tables{};
  for (int piece = 0; piece < kNumPieceTypes; ++piece) {
    for (int square = 0; square < kNumSquares; ++square) {
      tables[piece][kWhite][square] = kPieceValue[piece] + source[piece][square];
      tables[piece][kBlack][square] =
          kPieceValue[piece] + source[piece][square ^ 56];
    }
  }
  return tables;
}

}  // namespace internal

// Material value plus placement bonus for `piece_type` of `color` on `square`.
inline constexpr auto kPieceSquareValue = internal::MakePieceSquareTables();

}  // namespace fow

#endif  // FOW_PIECE_SQUARE_H_
