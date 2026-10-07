// Copyright 2026. Fog of War chess engine.
//
// Static evaluation, in centipawns, from the point of view of a chosen side.
//
// Two rules push this away from an orthodox evaluation. There is no check, so
// the game ends the instant a king stands on an attacked square: king safety is
// not a positional refinement but the entire win condition. And the opponent
// cannot answer a threat it never sees, so pressure on the enemy king is worth
// more than in open chess, while our own king wants to sit behind pieces rather
// than behind a count of attackers it can verify.
//
// The fog term is the piece an ordinary engine has no equivalent for: a clear
// line from our own king into unseen territory is a square an enemy slider may
// be standing on right now, and in this game that is immediately fatal. It is
// scored for our king only, because we have no idea what the opponent can see.

#ifndef FOW_EVALUATION_H_
#define FOW_EVALUATION_H_

#include <array>

#include "bitboard.h"
#include "piece_square.h"
#include "position.h"

namespace fow {

// What we know about the fog at the root of the current search. Passed down
// rather than held globally so that evaluation stays a pure function and can be
// tested directly.
struct FogContext {
  Bitboard unseen = 0;   // squares we cannot see this turn
  int side = kWhite;     // the side whose king is exposed by that fog, i.e. us
  int rook_like = 0;     // enemy rooks plus queens still unaccounted for
  int bishop_like = 0;   // enemy bishops plus queens
  int knights = 0;
  int pawns = 0;

  // A context that disables the fog term, for tests and perfect-information
  // comparisons.
  static FogContext None() { return FogContext(); }
};

// Weights for the fog term, deliberately on the scale of real material because
// the downside being priced is losing the game outright.
inline constexpr int kFogSliderPenalty = 22;
inline constexpr int kFogDiagonalPenalty = 18;
inline constexpr int kFogKnightPenalty = 14;
inline constexpr int kFogPawnPenalty = 26;
inline constexpr int kFogPenaltyCap = 350;

inline constexpr int kKingDirectAttackBonus = 55;
inline constexpr int kKingRingAttackBonus = 14;
inline constexpr int kMobilityBonus = 1;
inline constexpr int kBishopPairBonus = 35;

// Penalty for how much unseen territory bears on `color`'s king, given the
// current occupancy as blockers. O(1): a handful of magic lookups.
int FogDanger(const Position& position, int color, const FogContext& fog);

// Score of `position` from `perspective`'s point of view, in centipawns.
int Evaluate(const Position& position, int perspective, const FogContext& fog);

}  // namespace fow

#endif  // FOW_EVALUATION_H_
