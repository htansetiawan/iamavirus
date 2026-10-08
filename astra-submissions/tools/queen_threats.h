// Offline measurements only. Truth labels must never enter BeliefState.
#ifndef ASTRA_QUEEN_THREATS_H_
#define ASTRA_QUEEN_THREATS_H_

#include <string>
#include <vector>
#include "position.h"

namespace astra {
using namespace fow;

struct QueenThreats {
  int particles = 0;
  int exact_capturer_occupancy = 0;
  int true_attacker_union_occupancy = 0;
  int own_move_allowed = 0;
  int own_move_loses_king = 0;
  int geometric_threat = 0;
  int queen_capture_allowed = 0;
  int queen_capture_survives = 0;
  int actual_capture_allowed = 0;
  int actual_capture_survives = 0;
};

inline bool FindUci(const Position& p, const std::string& uci, Move* found) {
  MoveList moves;
  p.GenerateMoves(&moves);
  for (Move move : moves) {
    if (MoveToUci(move) == uci) { *found = move; return true; }
  }
  return false;
}

// Count equal-weight particles. Own legality uses the same observed EP override
// as the engine. Captures that lose the capturing side's king are allowed by
// the move generator but are NOT surviving threats. Worlds where our own move
// already loses our king cannot continue to the opponent's capture.
inline QueenThreats MeasureQueenThreats(const Position& truth, Move own,
    const std::string& capture_uci, int side, int observed_ep,
    const std::vector<Position>& particles) {
  Position after_truth = truth;
  UndoState undo;
  after_truth.MakeMove(own, &undo);
  Move capture = kNullMove;
  if (!FindUci(after_truth, capture_uci, &capture)) return {};
  const int target = MoveTo(capture), source = MoveFrom(capture);
  const int type = after_truth.piece_at(source);
  const Bitboard actual_attackers = after_truth.AttackersTo(target, side ^ 1);
  QueenThreats out;
  out.particles = static_cast<int>(particles.size());
  for (Position p : particles) {
    out.exact_capturer_occupancy += p.piece_at(source) == type && p.color_at(source) == (side ^ 1);
    Bitboard attackers = actual_attackers;
    bool union_held = false;
    while (attackers) {
      const int sq = PopLsb(&attackers);
      union_held |= p.piece_at(sq) == after_truth.piece_at(sq) && p.color_at(sq) == (side ^ 1);
    }
    out.true_attacker_union_occupancy += union_held;
    p.set_side_to_move(side);
    p.set_en_passant_square(observed_ep);
    Move supported = kNullMove;
    if (!FindUci(p, MoveToUci(own), &supported)) continue;
    ++out.own_move_allowed;
    p.MakeMove(supported, &undo);
    const bool own_lost = p.PreviousMoverIsLost();
    out.own_move_loses_king += own_lost;
    if (p.piece_at(target) != kQueen || p.color_at(target) != side) continue;
    out.geometric_threat += p.AttackersTo(target, side ^ 1) != 0;
    if (own_lost) continue;
    MoveList captures;
    p.GenerateCaptures(&captures);
    bool any = false, survives = false, actual = false, actual_survives = false;
    for (Move m : captures) {
      if (MoveTo(m) != target) continue;
      any = true;
      const bool recorded = MoveToUci(m) == capture_uci && p.piece_at(MoveFrom(m)) == type;
      actual |= recorded;
      UndoState response_undo;
      p.MakeMove(m, &response_undo);
      const bool safe = !p.PreviousMoverIsLost();
      p.UnmakeMove(m, response_undo);
      survives |= safe;
      actual_survives |= recorded && safe;
    }
    out.queen_capture_allowed += any;
    out.queen_capture_survives += survives;
    out.actual_capture_allowed += actual;
    out.actual_capture_survives += actual_survives;
  }
  return out;
}
}  // namespace astra
#endif
