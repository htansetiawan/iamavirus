// Measure whether Astra's particle belief retains the exact replay board.
// The engine receives only White's observations and its own played moves.
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "../../candidates/v12/engine.h"
#include "../../candidates/v12/observation.h"
#include "../../candidates/v12/position.h"

namespace fow {
namespace {
bool SameBoard(const Position& a, const Position& b) {
  if (a.side_to_move() != b.side_to_move()) return false;
  for (int square = 0; square < kNumSquares; ++square) {
    if (a.piece_at(square) != b.piece_at(square) ||
        a.color_at(square) != b.color_at(square)) return false;
  }
  return true;
}

bool ApplyUci(Position* position, const char* uci, Move* played) {
  MoveList legal;
  position->GenerateMoves(&legal);
  for (const Move move : legal) {
    if (MoveToUci(move) != uci) continue;
    *played = move;
    UndoState undo;
    position->MakeMove(move, &undo);
    return true;
  }
  return false;
}
}  // namespace
}  // namespace fow

int main(int argc, char** argv) {
  using namespace fow;
  const uint64_t seed = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : 1;
  const int prior = argc > 2 ? std::atoi(argv[2]) : 1;
  const int particles = argc > 3 ? std::atoi(argv[3]) : 2048;
  const int decision_ply = argc > 4 ? std::atoi(argv[4]) : -1;
  std::string input;
  if (!std::getline(std::cin, input)) return 1;
  std::istringstream stream(input);
  std::string side_name;
  stream >> side_name;
  const int our_side = side_name == "black" ? kBlack : kWhite;
  std::vector<std::string> moves;
  std::string uci;
  while (stream >> uci) moves.push_back(uci);
  if (moves.empty() || (side_name != "white" && side_name != "black")) return 1;
  InitializeAttackTables();
  InitializeZobrist();
  Position truth;
  if (!PositionFromFen(
          "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
          &truth)) return 2;
  EngineOptions options;
  options.particle_count = particles;
  options.node_budget = 20000;
  options.transposition_megabytes = 16;
  options.time_reserve = 0.0;
  options.opponent_prior = prior;
  Engine engine(our_side, 180.0, 2.0, options, seed);
  bool we_just_moved = false;
  bool truth_supported = false;
  int first_lost_ply = -1;
  for (int ply = 0; ply < static_cast<int>(moves.size()); ++ply) {
    engine.Observe(Observation(RenderObservation(truth, our_side)), we_just_moved);
    int support = 0;
    for (const Position& p : engine.belief().particles()) {
      if (SameBoard(p, truth)) ++support;
    }
    if (support > 0) truth_supported = true;
    if (truth_supported && support == 0 && first_lost_ply < 0) first_lost_ply = ply;
    std::printf("seed=%llu prior=%d particles=%d ply=%d move=%s stm=%d support=%d "
                "unique=%zu\n",
                static_cast<unsigned long long>(seed), prior, particles, ply,
                moves[ply].c_str(), truth.side_to_move(), support,
                engine.belief().particles().size());
    if (ply == decision_ply && truth.side_to_move() == our_side) {
      const std::vector<const Position*> search_sample =
          engine.belief().Sample(options.hypothesis_count);
      int true_in_search_sample = 0;
      for (const Position* hypothesis : search_sample) {
        if (SameBoard(*hypothesis, truth)) ++true_in_search_sample;
      }
      DecisionTrace trace;
      const Move choice = engine.ChooseMove(
          Observation(RenderObservation(truth, our_side)), 140.0, &trace);
      MoveList available;
      truth.GenerateMoves(&available);
      bool legal_choice = false;
      for (const Move m : available) legal_choice = legal_choice || m == choice;
      if (!legal_choice) return 4;
      Position candidate = truth;
      UndoState candidate_undo;
      candidate.MakeMove(choice, &candidate_undo);
      const int king = candidate.KingSquare(our_side);
      const bool survives_now = king >= 0 && !candidate.IsAttacked(king, our_side ^ 1);
      bool reply_legal = false;
      int safe_replies_after_recorded_opponent_move = -1;
      bool opponent_loses_immediately = false;
      if (survives_now && ply + 1 < static_cast<int>(moves.size())) {
        Move reply = kNullMove;
        reply_legal = ApplyUci(&candidate, moves[ply + 1].c_str(), &reply);
        if (reply_legal) {
          const int opponent_king = candidate.KingSquare(our_side ^ 1);
          opponent_loses_immediately = opponent_king < 0 ||
              candidate.IsAttacked(opponent_king, our_side);
          if (!opponent_loses_immediately) {
            MoveList our_replies;
            candidate.set_side_to_move(our_side);
            candidate.GenerateMoves(&our_replies);
            safe_replies_after_recorded_opponent_move = 0;
            for (const Move defense : our_replies) {
              UndoState defense_undo;
              candidate.MakeMove(defense, &defense_undo);
              const int king_after_defense = candidate.KingSquare(our_side);
              if (king_after_defense >= 0 &&
                  !candidate.IsAttacked(king_after_defense, our_side ^ 1)) {
                ++safe_replies_after_recorded_opponent_move;
              }
              candidate.UnmakeMove(defense, defense_undo);
            }
          }
        }
      }
      std::printf("DECISION seed=%llu prior=%d game_frame=%d choice=%s "
                  "particle_risk_permille=%d king_survives_now=%d "
                  "recorded_opponent_reply_legal=%d opponent_loses_immediately=%d "
                  "safe_replies_after_recorded_opponent_move=%d "
                  "true_in_search_sample=%d search_sample_size=%zu\n",
                  static_cast<unsigned long long>(seed), prior, ply,
                  MoveToUci(choice).c_str(), trace.king_risk_permille,
                  survives_now ? 1 : 0, reply_legal ? 1 : 0,
                  opponent_loses_immediately ? 1 : 0,
                  safe_replies_after_recorded_opponent_move,
                  true_in_search_sample, search_sample.size());
    }
    Move played = kNullMove;
    if (!ApplyUci(&truth, moves[ply].c_str(), &played)) return 3;
    const int mover = truth.side_to_move() ^ 1;
    if (mover == our_side) {
      engine.NotifyMovePlayed(played);
      we_just_moved = true;
    } else {
      we_just_moved = false;
    }
  }
  engine.Observe(Observation(RenderObservation(truth, our_side)), we_just_moved);
  int final_support = 0;
  for (const Position& p : engine.belief().particles()) {
    if (SameBoard(p, truth)) ++final_support;
  }
  if (final_support == 0 && first_lost_ply < 0) first_lost_ply = 38;
  std::printf("seed=%llu prior=%d particles=%d ply=38 move=END stm=%d support=%d "
              "unique=%zu\n",
              static_cast<unsigned long long>(seed), prior, particles,
              truth.side_to_move(), final_support,
              engine.belief().particles().size());
  std::fprintf(stderr, "SUMMARY seed=%llu prior=%d particles=%d first_lost_ply=%d\n",
               static_cast<unsigned long long>(seed), prior, particles,
               first_lost_ply);
  return 0;
}
