// Replay truth validates and scores this offline diagnostic. Belief receives
// only actor observations and the actor's recorded own actions.
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "belief.h"
#include "observation.h"
#include "queen_threats.h"

using namespace fow;

struct Frame {
  int ply;
  std::string move, board, white, black;
  int tracked_square;
  char tracked_piece;
};

static bool SameBoard(const Position& a, const Position& b) {
  for (int type = 0; type < kNumPieceTypes; ++type)
    if (a.pieces(type) != b.pieces(type)) return false;
  return a.pieces_of(kWhite) == b.pieces_of(kWhite) && a.pieces_of(kBlack) == b.pieces_of(kBlack);
}

static void Validate(const Position& p, const Frame& frame, bool tracked = true) {
  std::string board(64, '-');
  for (int sq = 0; sq < 64; ++sq)
    if (p.piece_at(sq) != kNoPiece) board[sq] = PieceTypeToSymbol(p.piece_at(sq), p.color_at(sq));
  if (board != frame.board || RenderObservation(p, kWhite) != frame.white ||
      RenderObservation(p, kBlack) != frame.black)
    throw std::runtime_error("native replay board/observation mismatch at ply " + std::to_string(frame.ply));
  if (tracked && (frame.tracked_square < 0 || frame.tracked_square >= 64 ||
                  board[frame.tracked_square] != frame.tracked_piece))
    throw std::runtime_error("invalid tracked piece label");
}

static Move RecordedMove(const Position& p, const std::string& uci) {
  Move move = kNullMove;
  if (!astra::FindUci(p, uci, &move)) throw std::runtime_error("unavailable recorded move " + uci);
  return move;
}

static int Run(int argc, char** argv) {
  if (argc != 8) throw std::runtime_error("usage: probe FRAMES SIDE SEED PARTICLES PRIOR HISTORY PREDICTION");
  const int side = std::stoi(argv[2]), count = std::stoi(argv[4]);
  const uint64_t seed = std::stoull(argv[3]);
  const int prior = std::stoi(argv[5]), history = std::stoi(argv[6]), prediction = std::stoi(argv[7]);
  if ((side != 0 && side != 1) || count < 1 || prior < 0 || prior > 2 || history < 0 || history > 2 || prediction < 0 || prediction > 2)
    throw std::runtime_error("invalid probe argument");
  std::ifstream file(argv[1]);
  if (!file) throw std::runtime_error("cannot open frames");
  std::vector<Frame> frames;
  Frame f;
  while (file >> f.ply >> f.move >> f.board >> f.white >> f.black >> f.tracked_square >> f.tracked_piece) {
    if (f.ply != static_cast<int>(frames.size()) || f.board.size() != 64 || f.white.size() != 64 || f.black.size() != 64)
      throw std::runtime_error("invalid frame sequence");
    frames.push_back(f);
  }
  if (!file.eof() || frames.size() < 3) throw std::runtime_error("malformed frame input");
  const int target_ply = static_cast<int>(frames.size()) - 3;
  if (target_ply % 2 != side) throw std::runtime_error("target is not actor decision");
  InitializeAttackTables();
  InitializeZobrist();
  Position truth;
  if (!PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth)) return 2;
  BeliefState belief(side, count, seed ^ 0x9E3779B97F4A7C15ULL, prior);
  belief.set_visibility_deductions(true);
  belief.set_capture_evidence(true);
  belief.set_history_mode(history);
  belief.set_prediction_mode(prediction);
  bool previous_own = false;
  std::string previous_view;
  std::cout << std::setprecision(17);
  for (int ply = 0; ply <= target_ply; ++ply) {
    if (ply && truth.PreviousMoverIsLost()) throw std::runtime_error("replay continues after terminal position");
    const auto& frame = frames[ply];
    Validate(truth, frame);
    const Observation view(side == 0 ? frame.white : frame.black);
    const auto start = std::chrono::steady_clock::now();
    const auto report = belief.Observe(view, previous_own);
    const double elapsed = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now()-start).count();
    const auto& particles = belief.particles();
    int held = 0, truth_held = 0;
    for (const Position& p : particles) {
      held += p.piece_at(frame.tracked_square) == truth.piece_at(frame.tracked_square) &&
              p.color_at(frame.tracked_square) == (side ^ 1);
      truth_held += SameBoard(p, truth);
    }
    std::cout << "{\"ply\":" << ply << ",\"particles\":" << particles.size()
              << ",\"tracked_square\":" << frame.tracked_square << ",\"tracked_piece\":\"" << frame.tracked_piece
              << "\",\"tracked_visible\":" << (!view.IsUnseen(frame.tracked_square) ? "true" : "false")
              << ",\"tracked_held\":" << held << ",\"truth_board_held\":" << truth_held
              << ",\"collapsed\":" << (report.collapsed ? "true" : "false")
              << ",\"after_own_move\":" << (previous_own ? "true" : "false")
              << ",\"pool\":" << report.surviving_particles
              << ",\"successor_prefix_capped\":" << (report.successor_prefix_capped ? "true" : "false")
              << ",\"history_recovered\":" << (report.history_recovered ? "true" : "false")
              << ",\"history_budget_exhausted\":" << (report.history_budget_exhausted ? "true" : "false")
              << ",\"history_conflict\":" << (report.history_evidence_conflict ? "true" : "false")
              << ",\"observe_ms\":" << elapsed;
    const Move own_or_opponent = RecordedMove(truth, frames[ply + 1].move);
    if (ply == target_ply) {
      const Observation previous(previous_view.empty() ? view.squares() : previous_view);
      const int ep = InferEnPassant(previous_view.empty() ? nullptr : &previous, view, side);
      Position after = truth;
      UndoState undo;
      after.MakeMove(own_or_opponent, &undo);
      Validate(after, frames[ply + 1]);
      if (after.PreviousMoverIsLost()) throw std::runtime_error("queen target own move is already terminal");
      const Move capture = RecordedMove(after, frames[ply + 2].move);
      if (after.piece_at(MoveTo(capture)) != kQueen || after.color_at(MoveTo(capture)) != side)
        throw std::runtime_error("recorded reply is not a queen capture");
      if (MoveFrom(capture) != frame.tracked_square || after.piece_at(MoveFrom(capture)) != truth.piece_at(frame.tracked_square))
        throw std::runtime_error("target identity does not match recorded capturer");
      const auto q = astra::MeasureQueenThreats(truth, own_or_opponent, frames[ply + 2].move, side, ep, particles);
      after.MakeMove(capture, &undo);
      Validate(after, frames[ply + 2], false);
      int view_matches = 0;
      for (const Position& p : particles) view_matches += RenderObservation(p, side) == view.squares();
      std::cout << ",\"queen\":{\"exact_capturer_occupancy\":" << q.exact_capturer_occupancy
                << ",\"true_attacker_union_occupancy\":" << q.true_attacker_union_occupancy
                << ",\"own_move_allowed\":" << q.own_move_allowed
                << ",\"own_move_loses_king\":" << q.own_move_loses_king
                << ",\"geometric_threat\":" << q.geometric_threat
                << ",\"queen_capture_allowed\":" << q.queen_capture_allowed
                << ",\"queen_capture_survives\":" << q.queen_capture_survives
                << ",\"actual_capture_allowed\":" << q.actual_capture_allowed
                << ",\"actual_capture_survives\":" << q.actual_capture_survives
                << ",\"view_matches\":" << view_matches
                << ",\"actual_capturing_side_survived\":" << (!after.PreviousMoverIsLost() ? "true" : "false")
                << ",\"native_frames_validated\":" << frames.size() << '}';
    }
    std::cout << "}\n";
    previous_view = view.squares();
    previous_own = truth.side_to_move() == side;
    if (previous_own) belief.ApplyOurMove(own_or_opponent);
    UndoState undo;
    truth.MakeMove(own_or_opponent, &undo);
  }
  return 0;
}

int main(int argc, char** argv) {
  try { return Run(argc, argv); }
  catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
}
