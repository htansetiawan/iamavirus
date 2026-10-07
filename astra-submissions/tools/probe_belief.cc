// Offline diagnostic, compiled against an immutable submission's source.
// Replay truth only generates the recorded observations and scores hypotheses.
// No true board or opponent move is passed to the belief tracker.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

#include "belief.h"
#include "bitboard.h"
#include "observation.h"
#include "position.h"

using namespace fow;

template <class Report>
static void CaptureDiagnostics(const Report& report) {
  // Older immutable archives do not have Astra's new diagnostic fields.
  if constexpr (requires { report.capture_square; }) {
    std::cout << ",\"inferred_capture_square\":" << report.capture_square
              << ",\"capture_constraints_preserved\":" << report.capture_constraints_preserved
              << ",\"capture_evidence_conflict\":" << (report.capture_evidence_conflict ? "true" : "false")
              << ",\"capture_ep_ambiguous\":" << (report.capture_en_passant_ambiguous ? "true" : "false");
  }
  if constexpr (requires { report.visibility_evidence_conflict; }) {
    std::cout << ",\"visibility_evidence_conflict\":"
              << (report.visibility_evidence_conflict ? "true" : "false");
  }
  if constexpr (requires { report.expanded_predecessors; }) {
    std::cout << ",\"expanded_predecessors\":" << report.expanded_predecessors
              << ",\"enumerated_transitions\":" << report.enumerated_transitions
              << ",\"successor_prefix_capped\":" << (report.successor_prefix_capped ? "true" : "false");
  }
  if constexpr (requires { report.continuation_previous_mover; }) {
    std::cout << ",\"continuation_previous_mover\":" << report.continuation_previous_mover
              << ",\"continuation_rejected\":" << report.continuation_rejected
              << ",\"recovery_attempts\":" << report.recovery_attempts
              << ",\"recovery_continuation_rejected\":" << report.recovery_continuation_rejected
              << ",\"continuation_evidence_conflict\":"
              << (report.continuation_evidence_conflict ? "true" : "false");
  }
  if constexpr (requires { report.history_attempted; }) {
    std::cout << ",\"history_attempted\":" << (report.history_attempted ? "true" : "false")
              << ",\"history_recovered\":" << (report.history_recovered ? "true" : "false")
              << ",\"history_full_certified\":" << (report.history_full_certified ? "true" : "false")
              << ",\"history_budget_exhausted\":" << (report.history_budget_exhausted ? "true" : "false")
              << ",\"history_checkpoints_tried\":" << report.history_checkpoints_tried
              << ",\"history_transitions\":" << report.history_transitions
              << ",\"history_rewind_plies\":" << report.history_rewind_plies
              << ",\"history_unique_support\":" << report.history_unique_support;
  }
}

template <class Belief>
static Belief MakeBelief(int side, int count, uint64_t seed,
                         bool capture, bool deductions, bool grouped, bool continuation,
                         bool history) {
  if constexpr (std::is_constructible_v<Belief, int, int, uint64_t, bool, bool, bool, bool, bool, bool>) {
    return Belief(side, count, seed, true, capture, deductions, grouped, continuation, history);
  } else if constexpr (std::is_constructible_v<Belief, int, int, uint64_t, bool, bool, bool, bool, bool>) {
    return Belief(side, count, seed, true, capture, deductions, grouped, continuation);
  } else if constexpr (std::is_constructible_v<Belief, int, int, uint64_t, bool, bool, bool, bool>) {
    return Belief(side, count, seed, true, capture, deductions, grouped);
  } else if constexpr (std::is_constructible_v<Belief, int, int, uint64_t, bool, bool, bool>) {
    return Belief(side, count, seed, true, capture, deductions);
  } else {
    // Immutable earlier submissions expose only their original prior switch.
    Belief belief(side, count, seed, true);
    // Fable's newer four-argument class enables deductions through Engine's
    // setter, not the constructor. Reproduce that setting explicitly.
    if constexpr (requires { belief.set_visibility_deductions(deductions); }) {
      belief.set_visibility_deductions(deductions);
    }
    return belief;
  }
}

static std::string BoardText(const Position& p) {
  std::string result(64, '-');
  for (int sq = 0; sq < 64; ++sq) {
    const int piece = p.piece_at(sq);
    if (piece != kNoPiece) result[sq] = PieceTypeToSymbol(piece, p.color_at(sq));
  }
  return result;
}

static Move FindMove(const Position& p, const std::string& uci) {
  MoveList moves;
  p.GenerateMoves(&moves);
  for (Move m : moves) if (MoveToUci(m) == uci) return m;
  std::cerr << "Illegal recorded move " << uci << '\n';
  std::exit(2);
}

static void PrintAttackers(const Position& truth, int king_side,
                           const Observation& before_view,
                           const std::vector<Position>& particles) {
  const int king = truth.KingSquare(king_side);
  Bitboard attackers = king < 0 ? 0 : truth.AttackersTo(king, king_side ^ 1);
  std::cout << '[';
  bool first = true;
  while (attackers) {
    const int square = PopLsb(&attackers);
    const int type = truth.piece_at(square);
    int held = 0;
    for (const Position& particle : particles) {
      held += particle.piece_at(square) == type && particle.color_at(square) == (king_side ^ 1);
    }
    if (!first) std::cout << ',';
    first = false;
    std::cout << "{\"square\":" << square << ",\"piece\":\""
              << PieceTypeToSymbol(type, king_side ^ 1) << "\",\"hidden_before\":"
              << (before_view.IsUnseen(square) ? "true" : "false")
              << ",\"held_particles\":" << held << '}';
  }
  std::cout << ']';
}

int main(int argc, char** argv) {
  if (argc != 5 && argc != 7 && argc != 8 && argc != 9 && argc != 10) {
    std::cerr << "usage: probe_belief MOVES_FILE SIDE(0|1) SEED PARTICLES [CAPTURE DEDUCTIONS [GROUPED [CONTINUATION [HISTORY]]]]\n";
    return 2;
  }
  if (argc == 7 && !std::is_constructible_v<BeliefState, int, int, uint64_t, bool, bool, bool>) {
    std::cerr << "this source version does not expose both ablation switches\n";
    return 2;
  }
  if (argc == 8 && !std::is_constructible_v<BeliefState, int, int, uint64_t, bool, bool, bool, bool>) {
    std::cerr << "this source version does not expose grouped prediction\n";
    return 2;
  }
  if (argc == 9 && !std::is_constructible_v<BeliefState, int, int, uint64_t, bool, bool, bool, bool, bool>) {
    std::cerr << "this source version does not expose continuation evidence\n";
    return 2;
  }
  if (argc == 10 && !std::is_constructible_v<BeliefState, int, int, uint64_t, bool, bool, bool, bool, bool, bool>) {
    std::cerr << "this source version does not expose history recovery\n";
    return 2;
  }
  InitializeAttackTables();
  InitializeZobrist();
  const int side = std::atoi(argv[2]);
  if (side != kWhite && side != kBlack) return 2;
  std::vector<int> tracked_squares;
  if (const char* requested = std::getenv("ASTRA_PROBE_SQUARES")) {
    std::istringstream stream(requested);
    std::string item;
    while (std::getline(stream, item, ',')) {
      std::size_t used = 0;
      const int square = std::stoi(item, &used);
      if (used != item.size() || square < 0 || square >= 64) return 2;
      tracked_squares.push_back(square);
    }
  }
  const uint64_t seed = std::strtoull(argv[3], nullptr, 10);
  auto belief = MakeBelief<BeliefState>(side, std::atoi(argv[4]),
      seed ^ 0x9E3779B97F4A7C15ULL,
      argc == 5 || std::atoi(argv[5]) != 0, argc == 5 || std::atoi(argv[6]) != 0,
      argc >= 8 && std::atoi(argv[7]) != 0, argc >= 9 && std::atoi(argv[8]) != 0,
      argc >= 10 && std::atoi(argv[9]) != 0);
  Position truth;
  if (!PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth)) return 2;
  if (BoardText(truth) != "RNBQKBNRPPPPPPPP--------------------------------pppppppprnbqkbnr") return 2;
  std::ifstream file(argv[1]);
  if (!file) return 2;
  std::vector<std::string> moves;
  std::string move;
  while (file >> move) moves.push_back(move);
  bool own_move = false;
  int capture_landing = -1;
  bool capture_was_ep = false;
  // Completed replay terminal frames are never delivered to a live bot. The
  // final true move may be labelled, but its resulting frame is not an input.
  for (std::size_t ply = 0; ply < moves.size(); ++ply) {
    if (ply > 0 && truth.PreviousMoverIsLost()) {
      std::cerr << "Recorded moves continue after a terminal king loss\n";
      return 2;
    }
    const Observation observation(RenderObservation(truth, side));
    const auto started = std::chrono::steady_clock::now();
    const auto report = belief.Observe(observation, own_move);
    const double observe_ms = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - started).count();
    const auto& particles = belief.particles();
    const std::string true_board = BoardText(truth);
    std::set<std::string> unique_boards;
    std::array<std::array<int, 7>, 64> hidden_counts{};
    int matches = 0, f1_enemy = 0, b2_pawn = 0, renders_match = 0, capture_supported = 0;
    int continuation_invalid = 0;
    for (const Position& p : particles) {
      const auto board = BoardText(p);
      unique_boards.insert(board);
      matches += board == true_board;
      f1_enemy += board[5] >= 'a' && board[5] <= 'z';
      b2_pawn += board[9] == 'p';
      renders_match += RenderObservation(p, side) == observation.squares();
      capture_supported += capture_landing >= 0 && p.color_at(capture_landing) == (side ^ 1);
      if (ply > 0) {
        const int previous = truth.side_to_move() ^ 1;
        const int king = p.KingSquare(previous);
        continuation_invalid += king < 0 || p.IsAttacked(king, previous ^ 1);
      }
      for (int sq = 0; sq < 64; ++sq) {
        if (!observation.IsUnseen(sq)) continue;
        const int type = p.piece_at(sq);
        ++hidden_counts[sq][type == kNoPiece ? 6 : type];
      }
    }
    double brier = 0.0, log_loss = 0.0, piece_mass = 0.0;
    int hidden_squares = 0, hidden_pieces = 0, zero_true_mass = 0;
    for (int sq = 0; sq < 64; ++sq) {
      if (!observation.IsUnseen(sq)) continue;
      ++hidden_squares;
      const int type = truth.piece_at(sq);
      const int label = type == kNoPiece ? 6 : type;
      const double probability = static_cast<double>(hidden_counts[sq][label]) / particles.size();
      zero_true_mass += hidden_counts[sq][label] == 0;
      log_loss -= std::log(std::max(probability, 1e-12));
      for (int cls = 0; cls < 7; ++cls) {
        const double error = static_cast<double>(hidden_counts[sq][cls]) / particles.size()
                             - (cls == label ? 1.0 : 0.0);
        brier += error * error;
      }
      if (type != kNoPiece) { ++hidden_pieces; piece_mass += probability; }
    }
    std::cout << "{\"seed\":" << seed << ",\"ply\":" << ply
              << ",\"collapsed\":" << (report.collapsed ? "true" : "false")
              << ",\"pool\":" << report.surviving_particles
              << ",\"particles\":" << particles.size()
              << ",\"unique_boards\":" << unique_boards.size()
              << ",\"truth_board_matches\":" << matches
              << ",\"black_f1\":" << f1_enemy
              << ",\"black_pawn_b2\":" << b2_pawn
              << ",\"exact_observation_matches\":" << renders_match
              << ",\"observe_ms\":" << observe_ms
              << ",\"continuation_invalid_particles\":" << continuation_invalid
              << ",\"hidden_squares\":" << hidden_squares
              << ",\"hidden_pieces\":" << hidden_pieces
              << ",\"hidden_brier_sum\":" << brier
              << ",\"hidden_log_loss_sum\":" << log_loss
              << ",\"hidden_piece_mass_sum\":" << piece_mass
              << ",\"zero_true_mass_squares\":" << zero_true_mass
              << ",\"true_capture_landing\":" << capture_landing
              << ",\"true_capture_was_ep\":" << (capture_was_ep ? "true" : "false")
              << ",\"true_capture_landing_support\":" << capture_supported;
    CaptureDiagnostics(report);
    std::cout << ",\"true_attackers_before\":";
    PrintAttackers(truth, side, observation, particles);
    std::cout << ",\"tracked_squares\":[";
    for (std::size_t i = 0; i < tracked_squares.size(); ++i) {
      const int square = tracked_squares[i];
      int held = 0;
      for (const Position& particle : particles) {
        held += particle.piece_at(square) == truth.piece_at(square) &&
                (truth.piece_at(square) == kNoPiece || particle.color_at(square) == truth.color_at(square));
      }
      if (i) std::cout << ',';
      std::cout << "{\"square\":" << square << ",\"truth\":\"" << true_board[square]
                << "\",\"hidden\":" << (observation.IsUnseen(square) ? "true" : "false")
                << ",\"held_particles\":" << held << '}';
    }
    std::cout << ']';
    if (ply < moves.size() && truth.side_to_move() == side) {
      const Move actual = FindMove(truth, moves[ply]);
      int loses = 0, illegal = 0;
      for (Position p : particles) {
        p.set_side_to_move(side);
        // Do not apply a move unsupported by a rebuilt hypothesis. In
        // particular its EP/rights metadata may differ from the actor's.
        MoveList available;
        p.GenerateMoves(&available);
        bool allowed = false;
        for (Move move : available) allowed |= move == actual;
        if (!allowed) { ++illegal; continue; }
        UndoState undo;
        p.MakeMove(actual, &undo);
        const int king = p.KingSquare(side);
        loses += king < 0 || p.IsAttacked(king, side ^ 1);
      }
      std::cout << ",\"actual_move\":\"" << moves[ply]
                << "\",\"actual_move_king_loss_particles\":" << loses
                << ",\"actual_move_illegal_particles\":" << illegal;
      Position after_truth = truth;
      UndoState actual_undo;
      after_truth.MakeMove(actual, &actual_undo);
      std::cout << ",\"true_attackers_after_actual\":";
      PrintAttackers(after_truth, side, observation, particles);
    }
    std::cout << "}\n";
    const Move actual = FindMove(truth, moves[ply]);
    own_move = truth.side_to_move() == side;
    if (own_move) belief.ApplyOurMove(actual);
    UndoState undo;
    truth.MakeMove(actual, &undo);
    // These are offline labels only. They are never passed to Observe().
    capture_landing = !own_move && undo.captured_type != kNoPiece ? MoveTo(actual) : -1;
    capture_was_ep = capture_landing >= 0 && MoveFlagOf(actual) == kFlagEnPassant;
  }
}
