// Offline diagnostic, compiled against an immutable submission's source.
// Replay truth only generates the recorded observations and scores hypotheses.
// No true board or opponent move is passed to the belief tracker.
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <set>
#include <string>
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

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: probe_belief MOVES_FILE SIDE(0|1) SEED PARTICLES\n";
    return 2;
  }
  InitializeAttackTables();
  InitializeZobrist();
  const int side = std::atoi(argv[2]);
  const uint64_t seed = std::strtoull(argv[3], nullptr, 10);
  BeliefState belief(side, std::atoi(argv[4]), seed ^ 0x9E3779B97F4A7C15ULL, 1);
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
  for (std::size_t ply = 0; ply <= moves.size(); ++ply) {
    const Observation observation(RenderObservation(truth, side));
    const auto report = belief.Observe(observation, own_move);
    const auto& particles = belief.particles();
    const std::string true_board = BoardText(truth);
    std::set<std::string> unique_boards;
    int matches = 0, f1_enemy = 0, b2_pawn = 0, renders_match = 0, capture_supported = 0;
    for (const Position& p : particles) {
      const auto board = BoardText(p);
      unique_boards.insert(board);
      matches += board == true_board;
      f1_enemy += board[5] >= 'a' && board[5] <= 'z';
      b2_pawn += board[9] == 'p';
      renders_match += RenderObservation(p, side) == observation.squares();
      capture_supported += capture_landing >= 0 && p.color_at(capture_landing) == (side ^ 1);
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
              << ",\"true_capture_landing\":" << capture_landing
              << ",\"true_capture_was_ep\":" << (capture_was_ep ? "true" : "false")
              << ",\"true_capture_landing_support\":" << capture_supported;
    CaptureDiagnostics(report);
    if (ply < moves.size() && truth.side_to_move() == side) {
      const Move actual = FindMove(truth, moves[ply]);
      int loses = 0;
      for (Position p : particles) {
        p.set_side_to_move(side);
        // Diagnostic scoring on replay truth's EP/right metadata is not needed:
        // the tested game's critical moves are ordinary moves, not castling/EP.
        UndoState undo;
        p.MakeMove(actual, &undo);
        const int king = p.KingSquare(side);
        loses += king < 0 || p.IsAttacked(king, side ^ 1);
      }
      std::cout << ",\"actual_move\":\"" << moves[ply]
                << "\",\"actual_move_king_loss_particles\":" << loses;
    }
    std::cout << "}\n";
    if (ply == moves.size()) break;
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
