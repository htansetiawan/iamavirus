// Copyright 2026. Fog of War chess engine.

#include <array>

#include "evaluation.h"

#include "move.h"

namespace fow {
namespace {

// Bonus by how far a passed pawn has advanced, indexed by rank from its own
// side's point of view.
constexpr std::array<int, 8> kPassedPawnBonus = {0, 8, 14, 26, 46, 76, 120, 0};

// Mobility and pressure on the enemy king, computed in a single pass.
//
// Each piece's attack set is built once and then asked both questions. The
// obvious implementation calls AttackersTo for the king square and each of the
// eight squares around it, which recomputes slider attacks eighteen times per
// evaluation for the same answer; this is the same arithmetic with the work
// shared. Mobility counts non-pawns only, since a pawn's attacked squares say
// little about where it can go.
struct Activity {
  int mobility = 0;
  int pressure = 0;
};

Activity MeasureActivity(const Position& position, int color) {
  Activity activity;
  const Bitboard own = position.pieces_of(color);
  const Bitboard occupied = position.occupied();
  const int target = position.KingSquare(color ^ 1);
  const Bitboard king_bb = target >= 0 ? SquareBB(target) : 0;
  const Bitboard ring = target >= 0 ? kKingAttacks[target] : 0;

  // Pawns are handled as two shifts of the whole pawn bitboard rather than one
  // iteration each. Shifting the set that cannot wrap off the edge keeps each
  // pawn contributing at most one hit per target, so the count still matches
  // attacker by attacker.
  const Bitboard pawns = position.pieces(kPawn, color);
  const Bitboard left = color == kWhite ? (pawns & ~kFileMask[0]) << 7
                                        : (pawns & ~kFileMask[0]) >> 9;
  const Bitboard right = color == kWhite ? (pawns & ~kFileMask[7]) << 9
                                         : (pawns & ~kFileMask[7]) >> 7;
  if (king_bb != 0) {
    activity.pressure +=
        kKingDirectAttackBonus *
        (PopCount(left & king_bb) + PopCount(right & king_bb));
    activity.pressure +=
        kKingRingAttackBonus * (PopCount(left & ring) + PopCount(right & ring));
  }

  Bitboard movers = own & ~pawns;
  while (movers) {
    const int square = PopLsb(&movers);
    const Bitboard attacks =
        PieceAttacks(position.piece_at(square), square, occupied, color);
    activity.mobility += PopCount(attacks & ~own);
    if (king_bb != 0) {
      activity.pressure += kKingDirectAttackBonus * PopCount(attacks & king_bb);
      activity.pressure += kKingRingAttackBonus * PopCount(attacks & ring);
    }
  }
  return activity;
}

int PassedPawns(const Position& position, int color) {
  const Bitboard enemy_pawns = position.pieces(kPawn, color ^ 1);
  Bitboard pawns = position.pieces(kPawn, color);
  int score = 0;
  while (pawns) {
    const int square = PopLsb(&pawns);
    const int file = FileOf(square);
    Bitboard ahead = kFileMask[file];
    if (file > 0) ahead |= kFileMask[file - 1];
    if (file < 7) ahead |= kFileMask[file + 1];
    const int rank = RankOf(square);
    int relative_rank;
    if (color == kWhite) {
      // Only ranks strictly in front of the pawn can stop it.
      ahead &= ~((Bitboard{1} << (8 * (rank + 1))) - 1);
      relative_rank = rank;
    } else {
      ahead &= (Bitboard{1} << (8 * rank)) - 1;
      relative_rank = 7 - rank;
    }
    if (!(ahead & enemy_pawns)) score += kPassedPawnBonus[relative_rank];
  }
  return score;
}

}  // namespace

int FogDanger(const Position& position, int color, const FogContext& fog) {
  if (fog.unseen == 0) return 0;
  const int square = position.KingSquare(color);
  if (square < 0) return 0;
  const Bitboard occupied = position.occupied();
  // Squares we know are occupied are already handled by the search's
  // king-capture test; what is dangerous is fog we cannot account for.
  const Bitboard unseen = fog.unseen & ~occupied;
  if (unseen == 0) return 0;

  int danger = 0;
  if (fog.rook_like > 0) {
    danger += kFogSliderPenalty *
              PopCount(RookAttacks(square, occupied) & unseen);
  }
  if (fog.bishop_like > 0) {
    danger += kFogDiagonalPenalty *
              PopCount(BishopAttacks(square, occupied) & unseen);
  }
  if (fog.knights > 0) {
    danger += kFogKnightPenalty * PopCount(kKnightAttacks[square] & unseen);
  }
  if (fog.pawns > 0) {
    // The squares an enemy pawn would attack this one from.
    danger += kFogPawnPenalty * PopCount(kPawnAttacks[color][square] & unseen);
  }
  return danger < kFogPenaltyCap ? danger : kFogPenaltyCap;
}

int Evaluate(const Position& position, int perspective, const FogContext& fog) {
  // Material and placement are maintained incrementally by Position.
  int score = position.placement_score(kWhite) - position.placement_score(kBlack);

  for (const int color : {kWhite, kBlack}) {
    const int sign = color == kWhite ? 1 : -1;
    if (PopCount(position.pieces(kBishop, color)) >= 2) {
      score += sign * kBishopPairBonus;
    }
    score += sign * PassedPawns(position, color);
  }

  const Activity white = MeasureActivity(position, kWhite);
  const Activity black = MeasureActivity(position, kBlack);
  score += white.pressure - black.pressure;
  score += kMobilityBonus * (white.mobility - black.mobility);

  const int exposure = FogDanger(position, fog.side, fog);
  score += fog.side == kWhite ? -exposure : exposure;

  return perspective == kWhite ? score : -score;
}

}  // namespace fow
