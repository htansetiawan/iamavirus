// Offline probe: for selected root actions, ask whether a represented world
// lets the opponent create a king attack, and how many safe replies remain.
// Full replay boards are used only to advance the public move history; the
// engine's inference receives only its own-side observations.
#include <algorithm>
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

struct ThreatStats {
  int legal_worlds = 0;
  int immediate_king_losses = 0;
  int root_survivors = 0;
  int worlds_with_attack = 0;
  int worlds_with_severe_attack = 0;
  double inverse_capacity_sum = 0.0;
  int attack_reply_events = 0;
  long long safe_reply_sum = 0;
};

Move ParseLegalMove(const Position& position, const std::string& uci) {
  MoveList legal;
  position.GenerateMoves(&legal);
  for (const Move move : legal) {
    if (MoveToUci(move) == uci) return move;
  }
  return kNullMove;
}

ThreatStats Probe(const std::vector<Position>& population, int our_side,
                  const std::string& uci) {
  ThreatStats result;
  const int enemy = our_side ^ 1;
  for (Position world : population) {
    world.set_side_to_move(our_side);
    const Move root = ParseLegalMove(world, uci);
    if (root == kNullMove) continue;
    ++result.legal_worlds;
    UndoState root_undo;
    world.MakeMove(root, &root_undo);
    const int own_king_after_root = world.KingSquare(our_side);
    if (own_king_after_root < 0 || world.IsAttacked(own_king_after_root, enemy)) {
      ++result.immediate_king_losses;
      continue;
    }
    ++result.root_survivors;

    MoveList opponent_moves;
    world.GenerateMoves(&opponent_moves);
    int worst_safe_reply_count = -1;
    for (const Move reply : opponent_moves) {
      UndoState reply_undo;
      world.MakeMove(reply, &reply_undo);
      const int enemy_king = world.KingSquare(enemy);
      const bool opponent_loses = enemy_king < 0 || world.IsAttacked(enemy_king, our_side);
      const int own_king = world.KingSquare(our_side);
      if (!opponent_loses && own_king >= 0 && world.IsAttacked(own_king, enemy)) {
        world.set_side_to_move(our_side);
        MoveList defenses;
        world.GenerateMoves(&defenses);
        int safe_count = 0;
        for (const Move defense : defenses) {
          UndoState defense_undo;
          world.MakeMove(defense, &defense_undo);
          const int defended_king = world.KingSquare(our_side);
          if (defended_king >= 0 && !world.IsAttacked(defended_king, enemy)) {
            ++safe_count;
          }
          world.UnmakeMove(defense, defense_undo);
        }
        worst_safe_reply_count = worst_safe_reply_count < 0
            ? safe_count : std::min(worst_safe_reply_count, safe_count);
      }
      world.UnmakeMove(reply, reply_undo);
    }
    if (worst_safe_reply_count >= 0) {
      ++result.worlds_with_attack;
      result.safe_reply_sum += worst_safe_reply_count;
      ++result.attack_reply_events;
      result.inverse_capacity_sum += 1.0 / (1.0 + worst_safe_reply_count);
      if (worst_safe_reply_count <= 3) ++result.worlds_with_severe_attack;
    }
  }
  return result;
}

}  // namespace
}  // namespace fow

int main(int argc, char** argv) {
  using namespace fow;
  if (argc < 7) {
    std::fprintf(stderr,
                 "usage: probe SEED PRIOR PARTICLES FRAME SIDE MOVES_CSV\n"
                 "stdin: one line of UCI moves from the initial position\n");
    return 2;
  }
  const uint64_t seed = std::strtoull(argv[1], nullptr, 10);
  const int prior = std::atoi(argv[2]);
  const int particles = std::atoi(argv[3]);
  const int frame = std::atoi(argv[4]);
  const int our_side = std::string(argv[5]) == "black" ? kBlack : kWhite;
  std::vector<std::string> root_moves;
  std::stringstream moves_csv(argv[6]);
  std::string uci;
  while (std::getline(moves_csv, uci, ',')) root_moves.push_back(uci);
  std::string input;
  if (!std::getline(std::cin, input)) return 3;
  std::istringstream moves_stream(input);
  std::vector<std::string> moves;
  while (moves_stream >> uci) moves.push_back(uci);
  if (frame < 0 || frame > static_cast<int>(moves.size())) return 4;

  InitializeAttackTables();
  InitializeZobrist();
  Position truth;
  if (!PositionFromFen(
          "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
          &truth)) return 5;
  EngineOptions options;
  options.particle_count = particles;
  options.node_budget = 100000;
  options.transposition_megabytes = 16;
  options.time_reserve = 0.0;
  options.opponent_prior = prior;
  Engine engine(our_side, 180.0, 2.0, options, seed);
  bool reflects_our_own_move = false;
  for (int ply = 0; ply < frame; ++ply) {
    engine.Observe(Observation(RenderObservation(truth, our_side)), reflects_our_own_move);
    MoveList legal;
    truth.GenerateMoves(&legal);
    Move played = kNullMove;
    for (const Move move : legal) {
      if (MoveToUci(move) == moves[ply]) { played = move; break; }
    }
    if (played == kNullMove) return 6;
    const int mover = truth.side_to_move();
    UndoState undo;
    truth.MakeMove(played, &undo);
    reflects_our_own_move = mover == our_side;
    if (reflects_our_own_move) engine.NotifyMovePlayed(played);
  }
  engine.Observe(Observation(RenderObservation(truth, our_side)), reflects_our_own_move);
  const std::vector<Position>& population = engine.belief().particles();
  if (root_moves.size() == 1 && root_moves.front() == "*") {
    if (population.empty()) return 7;
    MoveList actions;
    population.front().GenerateMoves(&actions);
    root_moves.clear();
    for (const Move move : actions) root_moves.push_back(MoveToUci(move));
  }
  std::printf("game_frame=%d side=%s prior=%d particles=%d worlds=%zu\n",
              frame, our_side == kWhite ? "white" : "black", prior,
              particles, population.size());
  for (const std::string& root_move : root_moves) {
    const ThreatStats stats = Probe(population, our_side, root_move);
    const double n = std::max(1, stats.legal_worlds);
    const double survivors = std::max(1, stats.root_survivors);
    const double threatened = static_cast<double>(stats.worlds_with_attack) / n;
    const double threatened_given_survival =
        static_cast<double>(stats.worlds_with_attack) / survivors;
    const double severe = static_cast<double>(stats.worlds_with_severe_attack) / n;
    const double severe_given_survival =
        static_cast<double>(stats.worlds_with_severe_attack) / survivors;
    const double inverse = stats.worlds_with_attack > 0
        ? stats.inverse_capacity_sum / stats.worlds_with_attack : 0.0;
    const double mean_safe = stats.worlds_with_attack > 0
        ? static_cast<double>(stats.safe_reply_sum) / stats.worlds_with_attack : -1.0;
    std::printf("move=%s legal_worlds=%d immediate_king_losses=%d "
                "root_survivors=%d attack_within_reply_total=%.6f "
                "attack_given_survival=%.6f severe_le3_total=%.6f "
                "severe_le3_given_survival=%.6f "
                "mean_worst_safe_replies=%.3f inverse_capacity=%.6f\n",
                root_move.c_str(), stats.legal_worlds,
                stats.immediate_king_losses, stats.root_survivors,
                threatened, threatened_given_survival, severe,
                severe_given_survival, mean_safe, inverse);
  }
  return 0;
}
