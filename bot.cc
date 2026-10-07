// Copyright 2026. Fog of War chess engine.
//
// The arena protocol loop.
//
// Contract, from the course documentation: read "fow" and a colour and time
// control, initialise, then write "ready" within fifteen seconds. Thereafter a
// 64-character observation arrives before every ply, and a bare number arrives
// on our own turn, which is the cue to answer with "move <uci>".
//
// stdout carries nothing but "ready" and "move ...", because any other line
// forfeits the game. Everything else goes to stderr.
//
// Nothing here is allowed to throw its way out of the process: an exception
// escaping would end the game as a crash, so failures fall back to the first
// legal move instead, which is always better than not moving.

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iostream>
#include <sstream>
#include <string>

#include "bitboard.h"
#include "engine.h"
#include "move.h"
#include "observation.h"
#include "position.h"

namespace fow {
namespace {

bool LooksLikeANumber(const std::string& line) {
  if (line.empty()) return false;
  bool digit_seen = false;
  for (std::size_t i = 0; i < line.size(); ++i) {
    const char c = line[i];
    if (c >= '0' && c <= '9') {
      digit_seen = true;
    } else if (c == '.' || c == '-' || c == '+' || c == 'e' || c == 'E') {
      continue;
    } else {
      return false;
    }
  }
  return digit_seen;
}

std::string Trim(const std::string& line) {
  std::size_t begin = 0;
  std::size_t end = line.size();
  while (begin < end && (line[begin] == ' ' || line[begin] == '\t' ||
                         line[begin] == '\r' || line[begin] == '\n')) {
    ++begin;
  }
  while (end > begin && (line[end - 1] == ' ' || line[end - 1] == '\t' ||
                         line[end - 1] == '\r' || line[end - 1] == '\n')) {
    --end;
  }
  return line.substr(begin, end - begin);
}

// A guaranteed-legal move for when the decision procedure fails, preferring the
// most valuable capture available.
Move FallbackMove(const Observation& view, int side) {
  Position visible;
  VisiblePositionFromObservation(view, side, 0, -1, &visible);
  MoveList legal;
  LegalMovesFromObservation(visible, view, &legal);
  Move best = kNullMove;
  int best_gain = -1;
  for (const Move move : legal) {
    const int victim = visible.piece_at(MoveTo(move));
    const int gain = victim == kNoPiece ? 0 : kPieceValue[victim];
    if (gain > best_gain) {
      best_gain = gain;
      best = move;
    }
  }
  return best;
}

uint64_t SeedFromEnvironmentOrClock() {
  if (const char* text = std::getenv("FOW_SEED")) {
    return static_cast<uint64_t>(std::strtoull(text, nullptr, 10));
  }
  // Unpredictability is deliberate: a deterministic strategy in an
  // imperfect-information game is exploitable by an opponent who has seen one
  // game and can replay our every answer.
  return static_cast<uint64_t>(
      std::chrono::steady_clock::now().time_since_epoch().count());
}

int Run() {
  std::ios::sync_with_stdio(false);

  std::string line;
  if (!std::getline(std::cin, line)) return 0;
  if (Trim(line) != "fow") {
    std::cerr << "unexpected greeting\n";
    return 0;
  }
  if (!std::getline(std::cin, line)) return 0;
  const std::string header = Trim(line);
  if (header.empty()) return 0;
  const int side = header[0] == 'w' || header[0] == 'W' ? kWhite : kBlack;
  double base = 180.0;
  double increment = 2.0;
  {
    std::istringstream stream(header);
    std::string colour;
    stream >> colour >> base >> increment;
  }

  InitializeAttackTables();
  InitializeZobrist();
  const EngineOptions options = EngineOptionsFromEnvironment();
  Engine engine(side, base, increment, options,
                SeedFromEnvironmentOrClock());

  std::cout << "ready" << std::endl;

  bool reflects_our_own_move = false;
  Observation latest;
  bool have_observation = false;

  while (std::getline(std::cin, line)) {
    const std::string text = Trim(line);
    if (text.size() == static_cast<std::size_t>(kNumSquares) &&
        Observation::IsValid(text)) {
      latest = Observation(text);
      have_observation = true;
      try {
        engine.Observe(latest, reflects_our_own_move);
      } catch (const std::exception& error) {
        std::cerr << "observe failed: " << error.what() << "\n";
      }
      reflects_our_own_move = false;
      continue;
    }
    if (!LooksLikeANumber(text)) continue;
    if (!have_observation) continue;

    const double remaining = std::strtod(text.c_str(), nullptr);
    Move move = kNullMove;
    DecisionTrace trace;
    const auto started = std::chrono::steady_clock::now();
    try {
      move = engine.ChooseMove(latest, remaining, &trace);
    } catch (const std::exception& error) {
      std::cerr << "decision failed: " << error.what() << "\n";
      move = kNullMove;
    }
    if (move == kNullMove) move = FallbackMove(latest, side);
    if (move == kNullMove) {
      // No legal move at all, which under the course rules is a loss already.
      std::cerr << "no legal move available\n";
      return 0;
    }
    trace.spent = std::chrono::duration<double>(
                      std::chrono::steady_clock::now() - started)
                      .count();

    try {
      engine.NotifyMovePlayed(move);
    } catch (const std::exception& error) {
      std::cerr << "bookkeeping failed: " << error.what() << "\n";
    }
    reflects_our_own_move = true;

    std::cerr << "depth=" << trace.depth << " score=" << trace.score
              << " nodes=" << trace.nodes << " legal=" << trace.legal_moves
              << " short=" << trace.shortlisted
              << " hyp=" << trace.hypotheses
              << " unsafe=" << trace.rejected_unsafe
              << " skipped=" << trace.cells_skipped
              << " p=" << trace.chosen_probability
              << " gv=" << trace.game_value << " fog=" << trace.unseen_squares
              << " budget=" << trace.budget << " spent=" << trace.spent
              << " clock=" << remaining << " move=" << MoveToUci(move) << "\n";

    std::cout << "move " << MoveToUci(move) << std::endl;
  }
  return 0;
}

}  // namespace
}  // namespace fow

int main() {
  try {
    return fow::Run();
  } catch (const std::exception& error) {
    std::cerr << "fatal: " << error.what() << "\n";
    return 0;
  } catch (...) {
    std::cerr << "fatal: unknown error\n";
    return 0;
  }
}
