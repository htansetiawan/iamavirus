// Copyright 2026. Fog of War chess engine.
//
// Offline benchmark against real arena games.
//
// Self-play cannot see the weaknesses that lose rated games: a bot playing itself
// shares its own blind spots, so a flaw both sides have cancels out in the score.
// Three changes measured +33, -47 and +51 Elo that way, none of them conclusive.
//
// This replays real games instead. For each game it rebuilds the truth by
// applying the recorded moves, renders the observations the seated player
// actually received -- a renderer that agrees with referee.py on 47,875 checks --
// and drives the engine's belief through them. At selected plies it asks the
// engine what it would play, then checks against the true board whether that move
// leaves our king capturable.
//
// The engine's answer is discarded and the game's real move is played instead, so
// the position stays on the rails of the real game and later plies remain genuine.
//
// This gives thousands of labelled decisions from opponents several hundred Elo
// stronger, which is a far better signal than any number of self-play games.
//
// Corpus line: <id> <side w|b> <result> <reason> <opponent> <uci moves...>

#include <cstdio>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "../belief.h"
#include "../bitboard.h"
#include "../engine.h"
#include "../observation.h"
#include "../position.h"
#include "../neural_inference.h"

namespace fow {
namespace {

struct Seat {
  std::string id;
  int side = kWhite;
  std::string result;
  std::string reason;
  std::string opponent;
  std::vector<std::string> moves;
};

struct Tally {
  int seats = 0;
  int decisions = 0;
  int blunders = 0;          // engine's move loses the king on the true board
  int fatal_positions = 0;   // plies where the real player lost the game
  int fatal_saved = 0;       // ...and the engine would not have
  int matched = 0;           // engine chose the same move as the real player
  int unsafe_rejected = 0;
};

Move FindMove(const Position& position, const std::string& uci) {
  MoveList legal;
  position.GenerateMoves(&legal);
  for (const Move candidate : legal) {
    if (MoveToUci(candidate) == uci) return candidate;
  }
  return kNullMove;
}

// Does `move` leave the mover's king capturable on the true board?
bool LosesKing(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  const int king = after.KingSquare(side);
  return king < 0 || after.IsAttacked(king, side ^ 1);
}

void RunSeat(const Seat& seat, const EngineOptions& options, int stride,
             Tally* tally, bool verbose, NeuralModel* model) {
  Position truth;
  if (!PositionFromFen(
          "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth)) {
    return;
  }
  Engine engine(seat.side, 180.0, 2.0, options, 777);
  NeuralTracker tracker(seat.side);
  if (model != nullptr) model->Reset();
  ++tally->seats;

  // The last ply played by our seat is the one that ended the game when we lost.
  int last_own_ply = -1;
  for (size_t ply = 0; ply < seat.moves.size(); ++ply) {
    const int mover = (ply % 2 == 0) ? kWhite : kBlack;
    if (mover == seat.side) last_own_ply = static_cast<int>(ply);
  }
  const bool we_lost = (seat.result == "1-0" && seat.side == kBlack) ||
                       (seat.result == "0-1" && seat.side == kWhite);
  const bool fatal_is_ours = we_lost && seat.reason == "King_capturable";

  bool we_just_moved = false;
  for (size_t ply = 0; ply < seat.moves.size(); ++ply) {
    const Observation view(RenderObservation(truth, seat.side));
    engine.Observe(view, we_just_moved);
    if (model != nullptr) {
      const int phase = ply == 0 ? kPhaseInitial
                        : we_just_moved ? kPhaseAfterOwnMove : kPhaseAfterOpponentMove;
      tracker.Observe(view, phase, static_cast<int>(ply));
      float planes[kNeuralPlanes * kNumSquares];
      float scalars[kNeuralScalars];
      tracker.Planes(planes);
      tracker.Scalars(scalars);
      std::string error;
      if (!model->Observe(planes, scalars, &error)) {
        std::fprintf(stderr, "replay inference failed: %s\n", error.c_str());
        std::exit(1);
      }
    }
    we_just_moved = false;

    const Move actual = FindMove(truth, seat.moves[ply]);
    if (actual == kNullMove) {
      std::fprintf(stderr, "  %s: illegal recorded move %s at ply %zu\n",
                   seat.id.c_str(), seat.moves[ply].c_str(), ply);
      return;
    }

    if (truth.side_to_move() == seat.side) {
      const bool is_fatal_ply =
          fatal_is_ours && static_cast<int>(ply) == last_own_ply;
      // Sample each color by its own decision count. Global even-ply strides
      // otherwise query White only, apart from the separately forced finals.
      const bool sampled = ((ply / 2) % static_cast<size_t>(stride)) == 0;
      if (is_fatal_ply || sampled) {
        DecisionTrace trace;
        NeuralAdvice advice;
        if (model != nullptr) {
          MoveList candidates;
          tracker.LegalCandidates(&candidates);
          const auto packed = tracker.MakeCandidates(candidates);
          std::vector<float> logits, dangers;
          std::string error;
          if (packed.empty() || !model->Score(packed, &logits, &dangers, &error)) {
            std::fprintf(stderr, "replay scoring failed: %s\n", error.c_str());
            std::exit(1);
          }
          const float peak = *std::max_element(logits.begin(), logits.end());
          double total = 0.0;
          for (std::size_t i = 0; i < packed.size(); ++i) {
            advice.moves.push_back(packed[i].move);
            advice.policy.push_back(std::exp(static_cast<double>(logits[i] - peak)));
            advice.danger.push_back(1.0 / (1.0 + std::exp(-static_cast<double>(dangers[i]))));
            total += advice.policy.back();
          }
          for (double& p : advice.policy) p /= total;
          advice.value = model->value();
          advice.available = true;
        }
        const Move choice = engine.ChooseMove(view, 150.0, &trace,
                                              advice.available ? &advice : nullptr);
        if (choice != kNullMove) {
          ++tally->decisions;
          tally->unsafe_rejected += trace.rejected_unsafe;
          const bool bad = LosesKing(truth, choice, seat.side);
          if (bad) ++tally->blunders;
          if (choice == actual) ++tally->matched;
          if (is_fatal_ply) {
            ++tally->fatal_positions;
            if (!bad) ++tally->fatal_saved;
            if (verbose) {
              std::printf("  %-10s vs %-20s ply %3zu  real played %-6s (lost)  "
                          "engine plays %-6s  %s\n",
                          seat.id.c_str(), seat.opponent.c_str(), ply,
                          seat.moves[ply].c_str(), MoveToUci(choice).c_str(),
                          bad ? "ALSO LOSES" : "survives");
            }
          }
        }
      }
      engine.NotifyMovePlayed(actual);
      if (model != nullptr) tracker.RecordOwnMove(actual);
      we_just_moved = true;
    }
    UndoState undo;
    truth.MakeMove(actual, &undo);
    if (truth.KingSquare(kWhite) < 0 || truth.KingSquare(kBlack) < 0) break;
  }
}

}  // namespace
}  // namespace fow

int main(int argc, char** argv) {
  using namespace fow;
  if (argc < 2) {
    std::fprintf(stderr,
                 "usage: %s CORPUS [stride] [node_budget] [verbose]\n", argv[0]);
    return 2;
  }
  const int stride = argc > 2 ? std::atoi(argv[2]) : 6;
  if (stride < 1) {
    std::fprintf(stderr, "stride must be positive (measured in own decisions)\n");
    return 2;
  }
  const uint64_t nodes = argc > 3 ? std::strtoull(argv[3], nullptr, 10) : 1000000;
  const bool verbose = argc > 4;

  InitializeAttackTables();
  InitializeZobrist();
  EngineOptions options = EngineOptionsFromEnvironment();
  options.node_budget = nodes;
  options.time_reserve = 0.0;
  NeuralModel model;
  NeuralModel* advisor = nullptr;
  if (options.mode != EngineMode::kCpp) {
    const char* directory = std::getenv("FOW_MODEL_DIR");
    std::string error;
    if (!model.Load(directory ? directory : "model", 1, &error)) {
      std::fprintf(stderr, "benchmark requires the requested model: %s\n", error.c_str());
      return 1;
    }
    advisor = &model;
  }

  std::ifstream input(argv[1]);
  if (!input) {
    std::fprintf(stderr, "cannot open %s\n", argv[1]);
    return 2;
  }
  Tally tally;
  std::string line;
  while (std::getline(input, line)) {
    if (line.empty()) continue;
    std::istringstream stream(line);
    Seat seat;
    std::string side;
    stream >> seat.id >> side >> seat.result >> seat.reason >> seat.opponent;
    seat.side = side == "w" ? kWhite : kBlack;
    std::string uci;
    while (stream >> uci) seat.moves.push_back(uci);
    if (seat.moves.size() < 4) continue;
    RunSeat(seat, options, stride, &tally, verbose, advisor);
  }

  std::printf("\ncorpus: %s   own-decision stride %d   %llu nodes/decision\n", argv[1],
              stride, static_cast<unsigned long long>(nodes));
  std::printf("  seats replayed            : %d\n", tally.seats);
  std::printf("  decisions evaluated       : %d\n", tally.decisions);
  std::printf("  immediate king losses     : %d (%.2f%%)\n", tally.blunders,
              tally.decisions ? 100.0 * tally.blunders / tally.decisions : 0.0);
  std::printf("  matched the real move     : %d (%.1f%%)\n", tally.matched,
              tally.decisions ? 100.0 * tally.matched / tally.decisions : 0.0);
  std::printf("  real losing positions     : %d\n", tally.fatal_positions);
  std::printf("  ...the engine survives    : %d (%.0f%%)\n", tally.fatal_saved,
              tally.fatal_positions
                  ? 100.0 * tally.fatal_saved / tally.fatal_positions : 0.0);
  std::printf("  unsafe moves rejected     : %d (%.1f per decision)\n",
              tally.unsafe_rejected,
              tally.decisions
                  ? static_cast<double>(tally.unsafe_rejected) / tally.decisions
                  : 0.0);
  return 0;
}
