// Copyright 2026. Fog of War chess engine.
//
// How well do we see through the fog? Replays real games from our side's
// observations and, at every one of our decisions, scores three guessers of the
// hidden enemy pieces against the true board:
//
//   particles  the engine's belief (the population the search and risk use)
//   network    the neural belief head (per-square enemy class after the latest
//              observation; computed in the arena every move, unused so far)
//   fused      the particles reweighted by the network: w_i = exp(beta * sum
//              over hidden squares of log p_net(particle i's class there))
//
// For every enemy piece on a square we cannot see: the probability each guesser
// puts on that piece type being on that square, averaged by piece type; and
// "lost" = the particles put no mass at all there (the truth fell out of the
// population, which no reweighting can repair).
//
//   belief_eval SEATS MODEL_DIR [max_seats] [particles] [online_beta]
//
// With online_beta > 0 the engine's own fusion (Engine::FuseNetworkBelief) is
// applied after every scored decision, as in play, so "particles" then measures
// the fused population that the search would have used.
//
// Seat lines as for benchmark_corpus (id w|b result reason label moves...); the
// whole move list is replayed and every own decision is scored.
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "../engine.h"
#include "../neural_inference.h"
#include "../neural_observation.h"
#include "../observation.h"
#include "../position.h"

using namespace fow;

namespace {

constexpr int kNoEnemyClass = 6;  // belief classes: enemy P N B R Q K, none
constexpr double kBetas[] = {0.25, 0.5, 1.0};
constexpr int kNumBetas = 3;
const char* kTypeNames[6] = {"pawn", "knight", "bishop", "rook", "queen", "king"};

int ClassOfPiece(int piece_type) {
  switch (piece_type) {
    case kPawn: return 0;
    case kKnight: return 1;
    case kBishop: return 2;
    case kRook: return 3;
    case kQueen: return 4;
    case kKing: return 5;
    default: return kNoEnemyClass;
  }
}

struct Tally {
  double particle = 0.0, network = 0.0, fused[kNumBetas] = {0, 0, 0};
  long count = 0, lost = 0;
};

}  // namespace

int main(int argc, char** argv) {
  if (argc < 3) {
    std::fprintf(stderr, "usage: belief_eval SEATS MODEL_DIR [max_seats] [particles]\n");
    return 2;
  }
  InitializeAttackTables();
  InitializeZobrist();
  const std::string seats_path = argv[1], model_dir = argv[2];
  const int max_seats = argc > 3 ? std::atoi(argv[3]) : 1000000;
  const int particles = argc > 4 ? std::atoi(argv[4]) : 8192;
  const double online_beta = argc > 5 ? std::atof(argv[5]) : 0.0;

  std::ifstream seats(seats_path);
  std::string line;
  std::map<std::string, Tally> tally;  // key: phase|type
  int seat_count = 0;
  long decisions = 0;
  while (std::getline(seats, line) && seat_count < max_seats) {
    std::istringstream fields(line);
    std::string id, side_text, result, reason, label;
    if (!(fields >> id >> side_text >> result >> reason >> label)) continue;
    std::vector<std::string> moves;
    for (std::string uci; fields >> uci;) moves.push_back(uci);
    const int side = side_text == "w" ? kWhite : kBlack;
    ++seat_count;

    EngineOptions options;
    options.particle_count = particles;
    options.transposition_megabytes = 8;
    Engine engine(side, 180.0, 2.0, options, 1234567 + seat_count);
    NeuralTracker tracker(side);
    NeuralModel model;
    std::string error;
    if (!model.Load(model_dir, 1, &error)) {
      std::fprintf(stderr, "model load failed: %s\n", error.c_str());
      return 1;
    }
    Position truth;
    PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth);
    bool reflects_own = false;
    for (std::size_t ply = 0; ply <= moves.size(); ++ply) {
      const Observation view(RenderObservation(truth, side));
      engine.Observe(view, reflects_own);
      tracker.Observe(view, ply == 0 ? kPhaseInitial : reflects_own ? kPhaseAfterOwnMove : kPhaseAfterOpponentMove,
                      static_cast<int>(ply));
      float planes[kNeuralPlanes * kNumSquares];
      float scalars[kNeuralScalars];
      tracker.Planes(planes);
      tracker.Scalars(scalars);
      if (!model.Observe(planes, scalars, &error)) {
        std::fprintf(stderr, "observe failed: %s\n", error.c_str());
        return 1;
      }
      if (ply == moves.size()) break;
      MoveList legal;
      truth.GenerateMoves(&legal);
      Move move = kNullMove;
      for (const Move candidate : legal) {
        if (MoveToUci(candidate) == moves[ply]) move = candidate;
      }
      if (move == kNullMove) break;  // the recorded move ended the game or did not parse

      if (truth.side_to_move() == side) {
        // Score the guessers at this decision.
        ++decisions;
        const Bitboard unseen = view.UnseenMask();
        const std::vector<float>& logits = model.belief_logits();
        // log p_net(class | square) for every square and class.
        std::array<std::array<double, 7>, 64> log_net{};
        for (int square = 0; square < 64; ++square) {
          const int canonical = side == kBlack ? (square ^ 56) : square;
          double top = -1e30;
          for (int c = 0; c < 7; ++c) top = std::max(top, static_cast<double>(logits[canonical * 7 + c]));
          double total = 0.0;
          for (int c = 0; c < 7; ++c) total += std::exp(logits[canonical * 7 + c] - top);
          for (int c = 0; c < 7; ++c) log_net[square][c] = logits[canonical * 7 + c] - top - std::log(total);
        }
        const std::vector<Position>& population = engine.belief().particles();
        const int enemy = side ^ 1;
        // Particle log-weights under the network, over the unseen squares.
        std::vector<double> log_weight(population.size(), 0.0);
        for (std::size_t i = 0; i < population.size(); ++i) {
          double sum = 0.0;
          for (Bitboard scan = unseen; scan;) {
            const int square = PopLsb(&scan);
            const int cls = population[i].color_at(square) == enemy
                                ? ClassOfPiece(population[i].piece_at(square)) : kNoEnemyClass;
            sum += log_net[square][cls];
          }
          log_weight[i] = sum;
        }
        double top = -1e300;
        for (const double w : log_weight) top = std::max(top, w);
        std::vector<std::vector<double>> weight(kNumBetas, std::vector<double>(population.size()));
        double weight_total[kNumBetas] = {0, 0, 0};
        for (int b = 0; b < kNumBetas; ++b) {
          for (std::size_t i = 0; i < population.size(); ++i) {
            weight[b][i] = std::exp(kBetas[b] * (log_weight[i] - top));
            weight_total[b] += weight[b][i];
          }
        }
        const char* phase = ply < 30 ? "opening" : ply < 70 ? "middle" : "late";
        for (Bitboard scan = unseen; scan;) {
          const int square = PopLsb(&scan);
          if (truth.color_at(square) != enemy) continue;
          const int type = truth.piece_at(square);
          const int cls = ClassOfPiece(type);
          double particle_mass = 0.0;
          double fused[kNumBetas] = {0, 0, 0};
          for (std::size_t i = 0; i < population.size(); ++i) {
            if (population[i].color_at(square) == enemy && population[i].piece_at(square) == type) {
              particle_mass += 1.0;
              for (int b = 0; b < kNumBetas; ++b) fused[b] += weight[b][i];
            }
          }
          particle_mass /= static_cast<double>(population.size());
          for (const std::string& key : {std::string(phase) + "|" + kTypeNames[cls], std::string("all|") + kTypeNames[cls]}) {
            Tally& t = tally[key];
            t.particle += particle_mass;
            t.network += std::exp(log_net[square][cls]);
            for (int b = 0; b < kNumBetas; ++b) t.fused[b] += fused[b] / weight_total[b];
            t.count += 1;
            t.lost += particle_mass == 0.0 ? 1 : 0;
          }
        }
        if (online_beta > 0.0) {
          std::vector<float> belief_log(64 * 7);
          for (int square = 0; square < 64; ++square) {
            for (int c = 0; c < 7; ++c) {
              // log_net is per raw square; the engine expects canonical squares
              const int canonical = side == kBlack ? (square ^ 56) : square;
              belief_log[static_cast<std::size_t>(canonical * 7 + c)] = static_cast<float>(log_net[square][c]);
            }
          }
          engine.FuseNetworkBelief(belief_log, view, online_beta);
        }
        engine.NotifyMovePlayed(move);
        tracker.RecordOwnMove(move);
        reflects_own = true;
      } else {
        reflects_own = false;
      }
      UndoState undo;
      truth.MakeMove(move, &undo);
    }
  }
  std::printf("seats %d, our decisions %ld, online fusion beta %.2f; probability on the true square of each hidden enemy piece\n",
              seat_count, decisions, online_beta);
  std::printf("%-8s %-7s %7s %9s %8s %8s %8s %8s %7s\n", "phase", "piece", "count", "particles", "network",
              "fused.25", "fused.5", "fused1", "lost");
  for (const auto& [key, t] : tally) {
    const std::size_t bar = key.find('|');
    std::printf("%-8s %-7s %7ld %9.3f %8.3f %8.3f %8.3f %8.3f %6.1f%%\n", key.substr(0, bar).c_str(),
                key.substr(bar + 1).c_str(), t.count, t.particle / t.count, t.network / t.count,
                t.fused[0] / t.count, t.fused[1] / t.count, t.fused[2] / t.count, 100.0 * t.lost / t.count);
  }
  return 0;
}
