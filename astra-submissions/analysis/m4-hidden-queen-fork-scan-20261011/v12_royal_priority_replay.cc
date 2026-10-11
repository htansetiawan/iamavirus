// Referee-state replay probe for Astra's candidate/v12 royal-risk filter.
// All pre-decision moves are the public recorded moves; the engine receives
// only its own-side observations and move notifications.
#include <cstdio>
#include <cstdlib>
#include <string>

#include "../../candidates/v12/engine.h"
#include "../../candidates/v12/observation.h"
#include "../../candidates/v12/position.h"

namespace fow {
namespace {

const char* kRecordedMoves[] = {
    "e2e4", "c7c5", "d2d4", "c5d4", "f2f4", "g8f6", "c2c3", "e7e5",
    "g1f3", "e5f4", "f1e2", "b8c6", "a2a4", "f8c5", "c3d4", "c6d4",
    "f3d4", "e8g8", "d4f3", "f6e4", "b1c3", "e4c3", "b2c3", "f8e8",
    "d1d3", "d8f6", "a4a5", "d7d5", "h2h4", "e8e4", "f3g5", "c8f5",
    "g5e4", "f5e4", "d3h3", "e4g2", "h3g2", "f6c3"};

bool ApplyUci(Position* position, const char* uci, Move* played) {
  MoveList legal;
  position->GenerateMoves(&legal);
  for (const Move move : legal) {
    if (MoveToUci(move) == uci) {
      *played = move;
      UndoState undo;
      position->MakeMove(move, &undo);
      return true;
    }
  }
  return false;
}

}  // namespace
}  // namespace fow

int main(int argc, char** argv) {
  using namespace fow;
  const uint64_t seed = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : 1;
  const int prior = argc > 2 ? std::atoi(argv[2]) : 1;
  InitializeAttackTables();
  InitializeZobrist();
  Position truth;
  if (!PositionFromFen(
          "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
          &truth)) {
    return 2;
  }
  EngineOptions options;
  options.particle_count = 2048;
  options.node_budget = 100000;
  options.transposition_megabytes = 16;
  options.time_reserve = 0.0;
  options.opponent_prior = prior;
  Engine engine(kWhite, 180.0, 2.0, options, seed);

  bool we_just_moved = false;
  for (const char* uci : kRecordedMoves) {
    engine.Observe(Observation(RenderObservation(truth, kWhite)),
                   we_just_moved);
    we_just_moved = false;
    Move move = kNullMove;
    if (!ApplyUci(&truth, uci, &move)) {
      std::fprintf(stderr, "recorded move is illegal: %s\n", uci);
      return 3;
    }
    if (move != kNullMove && (truth.side_to_move() == kBlack)) {
      // ApplyUci has already advanced the board, so mover is the opposite side.
      engine.NotifyMovePlayed(move);
      we_just_moved = true;
    }
  }

  const Observation view(RenderObservation(truth, kWhite));
  engine.Observe(view, we_just_moved);
  if (truth.side_to_move() != kWhite || truth.KingSquare(kWhite) < 0) return 4;

  DecisionTrace trace;
  const Move choice = engine.ChooseMove(view, 140.0, &trace);
  if (choice == kNullMove) return 5;
  MoveList legal;
  truth.GenerateMoves(&legal);
  bool is_legal = false;
  for (const Move move : legal) is_legal = is_legal || move == choice;
  if (!is_legal) return 6;
  UndoState undo;
  truth.MakeMove(choice, &undo);
  const int king = truth.KingSquare(kWhite);
  const bool king_survives = king >= 0 && !truth.IsAttacked(king, kBlack);
  std::printf("game=69nmui22 frame=38 seed=%llu prior=%d move=%s king_risk_permille=%d "
              "safest_risk_permille=%d rejected=%d rows_added=%d "
              "truth_king_survives=%d\n",
              static_cast<unsigned long long>(seed), prior, MoveToUci(choice).c_str(),
              trace.king_risk_permille,
              trace.safest_risk_permille, trace.rejected_unsafe,
              trace.rows_added_for_safety, king_survives ? 1 : 0);
  return king_survives ? 0 : 1;
}
