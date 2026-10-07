// Offline geometry labels. True boards enter only the labeller, not the actor.
#ifndef ASTRA_TACTICAL_LABELS_H_
#define ASTRA_TACTICAL_LABELS_H_

#include <algorithm>
#include <stdexcept>
#include <vector>

#include "observation.h"
#include "position.h"

namespace fow::astra {

struct CaptureOpportunity {
  Move reply = kNullMove;
  int victim_square = -1;
  int victim_type = kNoPiece;
  int capturer_type = kNoPiece;  // Before promotion.
  bool responder_loses_king = false;
  bool fatal_king_bait = false;
  bool visible_king_guard = false;
  bool hidden_king_guard = false;
  bool visible_safe_recapture = false;
  bool hidden_safe_recapture = false;
  bool unsafe_hidden_recapture = false;
  int best_hidden_recapture_net_cp = 0;  // Defined only if hidden_safe_recapture.
  Move best_hidden_recapture = kNullMove;
};

inline int MaterialBalance(const Position& position, int owner) {
  int result = 0;
  for (int type = kPawn; type < kKing; ++type) {
    result += kPieceValue[type] * (PopCount(position.pieces(type, owner)) -
                                  PopCount(position.pieces(type, owner ^ 1)));
  }
  return result;
}

// `position` is after the offering player's move, before the responder acts.
// An unseen defender means unseen IN THAT PRE-RESPONSE VIEW. It can become
// visible after the opponent commits the capture. History may still reveal it.
// Bait geometry does not estimate whether the opponent will choose the reply.
inline std::vector<CaptureOpportunity> CaptureOpportunities(const Position& position) {
  if (position.PreviousMoverIsLost()) {
    throw std::invalid_argument("no reply opportunity after a terminal king loss");
  }
  const int responder = position.side_to_move();
  const int owner = responder ^ 1;
  const Bitboard visible_before_reply = VisibleSquares(position, responder);
  const int material_before = MaterialBalance(position, owner);
  MoveList replies;
  position.GenerateMoves(&replies);
  std::vector<CaptureOpportunity> result;
  for (Move reply : replies) {
    const int destination = MoveTo(reply);
    int victim_square = destination;
    if (MoveFlagOf(reply) == kFlagEnPassant) {
      victim_square += responder == kWhite ? -8 : 8;
    }
    if (position.piece_at(victim_square) == kNoPiece ||
        position.color_at(victim_square) != owner) continue;
    CaptureOpportunity row;
    row.reply = reply;
    row.victim_square = victim_square;
    row.victim_type = position.piece_at(victim_square);
    row.capturer_type = position.piece_at(MoveFrom(reply));
    Position after = position;
    UndoState undo;
    after.MakeMove(reply, &undo);
    row.responder_loses_king = after.PreviousMoverIsLost();
    if (row.responder_loses_king) {
      const int king = after.KingSquare(responder);
      const Bitboard guards = king < 0 ? 0 : after.AttackersTo(king, owner);
      row.hidden_king_guard = (guards & ~visible_before_reply) != 0;
      row.visible_king_guard = (guards & visible_before_reply) != 0;
      row.fatal_king_bait = row.capturer_type == kKing && row.hidden_king_guard &&
                            !row.visible_king_guard;
      // This game ends now. Never score a fictitious recapture after it.
      result.push_back(row);
      continue;
    }
    MoveList recaptures;
    after.GenerateCaptures(&recaptures);
    for (Move recapture : recaptures) {
      if (MoveTo(recapture) != destination) continue;
      const bool hidden = !(visible_before_reply & SquareBB(MoveFrom(recapture)));
      Position after_recapture = after;
      after_recapture.MakeMove(recapture, &undo);
      if (after_recapture.PreviousMoverIsLost()) {
        row.unsafe_hidden_recapture |= hidden;
        continue;
      }
      if (!hidden) {
        row.visible_safe_recapture = true;
        continue;
      }
      // Full material difference handles both players' promotions correctly.
      const int net = MaterialBalance(after_recapture, owner) - material_before;
      if (!row.hidden_safe_recapture || net > row.best_hidden_recapture_net_cp) {
        row.best_hidden_recapture_net_cp = net;
        row.best_hidden_recapture = recapture;
      }
      row.hidden_safe_recapture = true;
    }
    result.push_back(row);
  }
  return result;
}

inline bool ProfitableHiddenRecapture(const CaptureOpportunity& row, int threshold = 300) {
  return !row.responder_loses_king && row.hidden_safe_recapture &&
         !row.visible_safe_recapture && row.best_hidden_recapture_net_cp >= threshold;
}

}  // namespace fow::astra
#endif
