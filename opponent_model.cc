// Copyright 2026. Fog of War chess engine.

#include "opponent_model.h"

#include <cmath>
#include <cstdlib>

#include "bitboard.h"
#include "observation.h"
#include "opponent_weights.h"

namespace fow {
namespace {

constexpr double kValue[kNumPieceTypes] = {1.0, 3.0, 3.0, 5.0, 9.0, 0.0};

int Abs(int x) { return x < 0 ? -x : x; }

// Does the piece on `square` attack `target` on its own, ignoring what the
// other pieces of its colour could do (but with every piece as a blocker)?
bool PieceOnSquareAttacks(const Position& board, int square, int target) {
  const int type = board.piece_at(square);
  const int color = board.color_at(square);
  if (type == kNoPiece) return false;
  return (PieceAttacks(type, square, board.occupied(), color) & SquareBB(target)) != 0;
}

}  // namespace

void OpponentMoveFeatures(Position* board, Move move,
                          double out[kNumOpponentFeatures]) {
  for (int i = 0; i < kNumOpponentFeatures; ++i) out[i] = 0.0;
  const int side = board->side_to_move();
  const int other = side ^ 1;
  const int from = MoveFrom(move);
  const int to = MoveTo(move);
  const int mover = board->piece_at(from);
  const int target = board->piece_at(to);
  const bool en_passant = MoveFlagOf(move) == kFlagEnPassant;
  const double captured =
      target != kNoPiece ? kValue[target] : (en_passant ? 1.0 : 0.0);
  out[0] = (target != kNoPiece || en_passant) ? 1.0 : 0.0;
  out[1] = captured / 9.0;
  out[2 + mover] = 1.0;
  out[8] = IsPromotion(move) ? 1.0 : 0.0;
  out[9] = IsCastle(move) ? 1.0 : 0.0;
  const bool from_attacked = board->IsAttacked(from, other);
  const bool opponent_sees_from =
      (VisibleSquares(*board, other) & SquareBB(from)) != 0;
  const int king_before = board->KingSquare(side);
  const bool king_attacked_before =
      king_before >= 0 && board->IsAttacked(king_before, other);

  UndoState undo;
  board->MakeMove(move, &undo);
  const double moved_value = kValue[board->piece_at(to)];
  const bool attacked = board->IsAttacked(to, other);
  const bool defended = board->IsAttacked(to, side);
  out[10] = attacked ? 1.0 : 0.0;
  out[11] = defended ? 1.0 : 0.0;
  const bool hanging = attacked && !defended;
  out[12] = hanging ? moved_value / 9.0 : 0.0;
  out[13] = (captured - (hanging ? moved_value : 0.0)) / 9.0;
  const int enemy_king = board->KingSquare(other);
  const bool attacks_king = enemy_king >= 0 && PieceOnSquareAttacks(*board, to, enemy_king);
  out[14] = attacks_king ? 1.0 : 0.0;
  out[15] = (from_attacked && !attacked) ? 1.0 : 0.0;
  out[16] = (mover == kKing && king_attacked_before) ? 1.0 : 0.0;
  if (mover == kPawn) {
    const int rank = RankOf(to);
    out[17] = (side == kWhite ? rank : 7 - rank) / 7.0;
  }
  out[18] = 1.0 - (std::fabs(FileOf(to) - 3.5) + std::fabs(RankOf(to) - 3.5)) / 7.0;
  const bool opponent_sees_to = (VisibleSquares(*board, other) & SquareBB(to)) != 0;
  out[19] = opponent_sees_to ? 1.0 : 0.0;
  out[20] = opponent_sees_from ? 1.0 : 0.0;
  out[21] = (attacks_king && !opponent_sees_to) ? 1.0 : 0.0;
  out[22] = moved_value / 9.0;
  if (enemy_king >= 0) {
    const int dx = Abs(FileOf(to) - FileOf(enemy_king));
    const int dy = Abs(RankOf(to) - RankOf(enemy_king));
    out[23] = (dx > dy ? dx : dy) / 7.0;
  }
  board->UnmakeMove(move, undo);
}

double LearnedMovePlausibility(Position* board, Move move) {
  double features[kNumOpponentFeatures];
  OpponentMoveFeatures(board, move, features);
  double logit = 0.0;
  for (int i = 0; i < kNumOpponentFeatures; ++i) {
    logit += kOpponentWeights[i] * features[i];
  }
  return std::exp(logit);
}

}  // namespace fow
