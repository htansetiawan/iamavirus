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

#include <cmath>
#include <vector>

#include "bitboard.h"
#include "engine.h"
#include "move.h"
#include "neural_inference.h"
#include "neural_observation.h"
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

// Softmax over policy logits and sigmoid over danger logits, aligned with the
// candidate list. The mask is implicit: only real candidates are scored.
NeuralAdvice MakeAdvice(const std::vector<NeuralCandidate>& candidates,
                        const std::vector<float>& policy_logits,
                        const std::vector<float>& danger_logits, float value) {
  NeuralAdvice advice;
  if (candidates.empty() || policy_logits.size() != candidates.size()) {
    return advice;
  }
  float peak = policy_logits[0];
  for (const float logit : policy_logits) peak = std::max(peak, logit);
  double total = 0.0;
  advice.policy.resize(candidates.size());
  advice.danger.resize(candidates.size());
  advice.moves.resize(candidates.size());
  for (std::size_t i = 0; i < candidates.size(); ++i) {
    advice.moves[i] = candidates[i].move;
    advice.policy[i] = std::exp(static_cast<double>(policy_logits[i] - peak));
    total += advice.policy[i];
    advice.danger[i] = 1.0 / (1.0 + std::exp(-static_cast<double>(danger_logits[i])));
  }
  for (double& p : advice.policy) p /= total;
  advice.value = value;
  advice.available = true;
  return advice;
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
  EngineOptions options = EngineOptionsFromEnvironment();
  const uint64_t seed = SeedFromEnvironmentOrClock();
  Engine engine(side, base, increment, options, seed);
  {
    // FOW_BOOK=off disables the opening book; otherwise FOW_BOOK names the
    // file, defaulting to book.txt next to the launcher.
    const char* book = std::getenv("FOW_BOOK");
    const std::string path = book == nullptr ? std::string("book.txt") : std::string(book);
    if (path != "off") {
      const int entries = engine.LoadBook(path);
      std::cerr << "book " << path << ": " << entries << " entries\n";
    }
  }

  // The neural adapter: loaded once, before "ready", and dropped for the rest
  // of the game on any failure. Never plays with weights it did not load.
  NeuralTracker tracker(side);
  NeuralModel model;
  if (options.mode != EngineMode::kCpp) {
    const char* directory = std::getenv("FOW_MODEL_DIR");
    std::string error;
    int threads = 1;
    if (const char* text = std::getenv("FOW_INFERENCE_THREADS")) {
      threads = std::max(1, std::atoi(text));
    }
    const auto started = std::chrono::steady_clock::now();
    if (!model.Load(directory != nullptr ? directory : "model", threads, &error)) {
      std::cerr << "model unavailable (" << error << "); mode=cpp\n";
      options.mode = EngineMode::kCpp;
    } else {
      std::cerr << "model loaded in "
                << std::chrono::duration<double>(
                       std::chrono::steady_clock::now() - started)
                       .count()
                << "s " << model.manifest_summary() << " features="
                << kFeatureVersion << " actions=" << kActionVersion << "\n";
    }
  }
  // The seed is repeated in a compact prefix on every decision line so it is
  // recoverable from the retained log tail.
  std::cerr << "seed=" << seed << " mode=" << EngineModeName(options.mode) << "\n";

  std::cout << "ready" << std::endl;

  bool reflects_our_own_move = false;
  Observation latest;
  bool have_observation = false;
  int observations_seen = 0;
  int decisions = 0;
  // Offline analysis: FOW_FORCE_MOVES="e2e4 g1f3 ..." makes the bot play the
  // listed moves at its decisions, in order, while still computing and logging
  // what it would have chosen. This replays a recorded game through the full
  // arena decision procedure (any mode) with the belief following the real
  // moves. Never set in the arena.
  std::vector<std::string> forced;
  if (const char* text = std::getenv("FOW_FORCE_MOVES")) {
    std::istringstream stream(text);
    std::string uci;
    while (stream >> uci) forced.push_back(uci);
  }

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
      // One observation arrives per ply for both players, so the count of
      // views received is the frame index. Each real view updates the tracker
      // and the recurrent state exactly once.
      const int ply = observations_seen++;
      const int phase = ply == 0 ? kPhaseInitial
                        : reflects_our_own_move ? kPhaseAfterOwnMove
                                                : kPhaseAfterOpponentMove;
      tracker.Observe(latest, phase, ply);
      if (model.available()) {
        float planes[kNeuralPlanes * kNumSquares];
        float scalars[kNeuralScalars];
        tracker.Planes(planes);
        tracker.Scalars(scalars);
        std::string error;
        if (!model.Observe(planes, scalars, &error)) {
          std::cerr << "inference failed (" << error << "); mode=cpp\n";
          model.Disable();
          options.mode = EngineMode::kCpp;
        }
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
    // Scoring happens only here, from the state the last observation left;
    // no recurrent update runs at the clock prompt.
    NeuralAdvice advice;
    double inference_seconds = 0.0;
    if (model.available()) {
      MoveList candidates;
      tracker.LegalCandidates(&candidates);
      const std::vector<NeuralCandidate> packed = tracker.MakeCandidates(candidates);
      std::vector<float> policy_logits, danger_logits;
      std::string error;
      if (!packed.empty() &&
          model.Score(packed, &policy_logits, &danger_logits, &error)) {
        advice = MakeAdvice(packed, policy_logits, danger_logits, model.value());
      } else if (!packed.empty()) {
        std::cerr << "scoring failed (" << error << "); mode=cpp\n";
        model.Disable();
        options.mode = EngineMode::kCpp;
      }
      inference_seconds = std::chrono::duration<double>(
                              std::chrono::steady_clock::now() - started)
                              .count();
    }
    try {
      move = engine.ChooseMove(latest, remaining, &trace,
                               advice.available ? &advice : nullptr);
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
    std::string chosen_note;
    if (static_cast<std::size_t>(decisions) < forced.size()) {
      MoveList legal;
      tracker.LegalCandidates(&legal);
      for (const Move candidate : legal) {
        if (MoveToUci(candidate) == forced[static_cast<std::size_t>(decisions)]) {
          chosen_note = " chose=" + MoveToUci(move);
          move = candidate;
        }
      }
    }

    try {
      engine.NotifyMovePlayed(move);
    } catch (const std::exception& error) {
      std::cerr << "bookkeeping failed: " << error.what() << "\n";
    }
    tracker.RecordOwnMove(move);
    reflects_our_own_move = true;
    ++decisions;

    std::cerr << "s" << (seed % 100000) << " n=" << decisions
              << " mode=" << EngineModeName(trace.mode_used)
              << " depth=" << trace.depth << " score=" << trace.score
              << " nodes=" << trace.nodes << " legal=" << trace.legal_moves
              << " short=" << trace.shortlisted
              << " hyp=" << trace.hypotheses
              << " unsafe=" << trace.rejected_unsafe
              << " skipped=" << trace.cells_skipped
              << " safe_rows=" << trace.rows_added_for_safety
              << " p=" << trace.chosen_probability
              << " gv=" << trace.game_value << " fog=" << trace.unseen_squares
              << " budget=" << trace.budget << " x" << trace.budget_multiplier
              << " spent=" << trace.spent
              << " cells=" << trace.cells_spent << "/" << trace.cell_threads_used
              << " rep=" << trace.repetition_rows
              << " dec=" << trace.decision_index
              << " bref=" << trace.book_refused
              << (trace.from_book ? " book=1" : "")
              << " infer=" << inference_seconds << " clock=" << remaining
              << " risk=" << trace.king_risk_permille
              << " nv=" << trace.neural_value << " cp=" << trace.chosen_policy
              << " cd=" << trace.chosen_danger << " cands=" << trace.candidates
              << chosen_note << " move=" << MoveToUci(move) << "\n";

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
