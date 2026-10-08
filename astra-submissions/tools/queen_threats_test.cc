#include <iostream>
#include <stdexcept>
#include "queen_threats.h"
using namespace fow;
static int checks = 0;

static void Check(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
  ++checks;
}

int main() {
  InitializeAttackTables(); InitializeZobrist();
  Position truth;
  Check(PositionFromFen("4k3/8/8/r7/4Q3/8/8/7K w - - 0 1", &truth), "base FEN");
  Move own;
  Check(astra::FindUci(truth, "e4e5", &own), "queen move");
  auto q = astra::MeasureQueenThreats(truth, own, "a5e5", kWhite, -1, {truth});
  Check(q.exact_capturer_occupancy == 1 && q.own_move_allowed == 1 && q.geometric_threat == 1 &&
        q.queen_capture_survives == 1 && q.actual_capture_survives == 1, "safe recorded queen capture");

  Position pinned;
  Check(PositionFromFen("4R1rk/8/8/8/7Q/8/8/K7 w - - 0 1", &pinned), "pinned FEN");
  Move interpose;
  Check(astra::FindUci(pinned, "h4g4", &interpose), "pinned setup move");
  q = astra::MeasureQueenThreats(pinned, interpose, "g8g4", kWhite, -1, {pinned});
  Check(q.own_move_loses_king == 0 && q.geometric_threat == 1 && q.queen_capture_allowed == 1 &&
        q.queen_capture_survives == 0 && q.actual_capture_survives == 0, "capture allowed but loses opponent king");

  Position own_lost = truth;
  own_lost.RemovePiece(7); own_lost.PutPiece(0, kWhite, kKing);
  q = astra::MeasureQueenThreats(truth, own, "a5e5", kWhite, -1, {own_lost});
  Check(q.own_move_loses_king == 1 && q.geometric_threat == 1 && q.queen_capture_allowed == 0,
        "no opponent turn after our immediate king loss");

  Position unsupported = truth;
  unsupported.PutPiece(36, kWhite, kPawn);
  q = astra::MeasureQueenThreats(truth, own, "a5e5", kWhite, -1, {unsupported});
  Check(q.exact_capturer_occupancy == 1 && q.own_move_allowed == 0, "own move support denominator");

  Position other_type = truth;
  other_type.RemovePiece(32); other_type.PutPiece(32, kBlack, kQueen);
  q = astra::MeasureQueenThreats(truth, own, "a5e5", kWhite, -1, {other_type});
  Check(q.exact_capturer_occupancy == 0 && q.queen_capture_survives == 1 && q.actual_capture_allowed == 0,
        "same capture coordinates with a different piece are not the actual capturer");

  q = astra::MeasureQueenThreats(truth, own, "a5e5", kWhite, -1, {truth, other_type, unsupported});
  Check(q.particles == 3 && q.exact_capturer_occupancy == 2 && q.own_move_allowed == 2 &&
        q.queen_capture_survives == 2 && q.actual_capture_survives == 1, "particle multiplicity and counts");
  std::cout << checks << " checks passed across six queen-threat cases\n";
}
