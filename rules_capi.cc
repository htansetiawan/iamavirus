// Copyright 2026. Fog of War chess engine.
//
// A C interface over the rules, the observation logic and the engine, so that
// the Python learning code reuses the implementation that has been checked
// against referee.py rather than carrying a second copy of the rules.
//
// Everything here is a thin shim: handles are heap-allocated engine objects,
// strings are the arena's own 64-character encodings and UCI, and nothing is
// cached across calls. Built as a shared library by learning/_native.py.

#include <cstdint>
#include <cstring>
#include <memory>
#include <string>

#include "bitboard.h"
#include "engine.h"
#include "move.h"
#include "observation.h"
#include "position.h"

namespace {

using fow::Bitboard;
using fow::Move;
using fow::MoveList;
using fow::Observation;
using fow::Position;

Position* AsPosition(void* handle) { return static_cast<Position*>(handle); }
const Position* AsPosition(const void* handle) {
  return static_cast<const Position*>(handle);
}

Move FindMove(const Position& position, const char* uci) {
  MoveList legal;
  position.GenerateMoves(&legal);
  for (const Move move : legal) {
    if (fow::MoveToUci(move) == uci) return move;
  }
  return fow::kNullMove;
}

int WriteMoves(const MoveList& list, char* out, int capacity) {
  int written = 0;
  for (int i = 0; i < list.size(); ++i) {
    const std::string uci = fow::MoveToUci(list[i]);
    const int needed = static_cast<int>(uci.size()) + (i > 0 ? 1 : 0);
    if (written + needed + 1 > capacity) break;
    if (i > 0) out[written++] = ' ';
    std::memcpy(out + written, uci.data(), uci.size());
    written += static_cast<int>(uci.size());
  }
  out[written] = '\0';
  return list.size();
}

bool initialized = false;

}  // namespace

extern "C" {

void fow_initialize() {
  if (initialized) return;
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  initialized = true;
}

void* fow_position_new() {
  fow_initialize();
  Position* position = new Position();
  fow::PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                       position);
  return position;
}

void* fow_position_clone(const void* handle) {
  return new Position(*AsPosition(handle));
}

void fow_position_free(void* handle) { delete AsPosition(handle); }

int fow_position_set_fen(void* handle, const char* fen) {
  return fow::PositionFromFen(fen, AsPosition(handle)) ? 1 : 0;
}

// Loads an arena board string (a1..h8, '-' for empty), with the side to move,
// castling rights as a bitboard of rook squares, and a raw en passant square.
int fow_position_set_board(void* handle, const char* board, int side,
                           unsigned long long castling, int en_passant) {
  if (std::strlen(board) != static_cast<std::size_t>(fow::kNumSquares)) return 0;
  Position* position = AsPosition(handle);
  position->Clear();
  for (int square = 0; square < fow::kNumSquares; ++square) {
    const char symbol = board[square];
    if (symbol == '-' || symbol == '?') continue;
    const int type = fow::SymbolToPieceType(symbol);
    if (type == fow::kNoPiece) return 0;
    const int color = (symbol >= 'A' && symbol <= 'Z') ? fow::kWhite : fow::kBlack;
    position->PutPiece(square, color, type);
  }
  position->set_side_to_move(side);
  position->set_castling_rights(static_cast<Bitboard>(castling));
  position->set_en_passant_square(en_passant);
  return 1;
}

void fow_position_board(const void* handle, char* out) {
  const Position* position = AsPosition(handle);
  for (int square = 0; square < fow::kNumSquares; ++square) {
    const int type = position->piece_at(square);
    out[square] = type == fow::kNoPiece
                      ? '-'
                      : fow::PieceTypeToSymbol(type, position->color_at(square));
  }
  out[fow::kNumSquares] = '\0';
}

void fow_position_observation(const void* handle, int color, char* out) {
  const std::string view = fow::RenderObservation(*AsPosition(handle), color);
  std::memcpy(out, view.data(), view.size());
  out[view.size()] = '\0';
}

unsigned long long fow_position_visible(const void* handle, int color) {
  return fow::VisibleSquares(*AsPosition(handle), color);
}

int fow_position_side(const void* handle) {
  return AsPosition(handle)->side_to_move();
}
int fow_position_en_passant(const void* handle) {
  return AsPosition(handle)->en_passant_square();
}
unsigned long long fow_position_castling(const void* handle) {
  return AsPosition(handle)->castling_rights();
}
int fow_position_halfmove(const void* handle) {
  return AsPosition(handle)->halfmove_clock();
}
void fow_position_set_halfmove(void* handle, int value) {
  AsPosition(handle)->set_halfmove_clock(value);
}

// Repetition key with the referee's semantics: the en passant square counts
// only when a Fog of War capture of it is actually available. The engine's
// Zobrist key carries the file whenever a double push just happened, so that
// component is removed when no pawn can use it.
unsigned long long fow_position_repetition_key(const void* handle) {
  const Position* position = AsPosition(handle);
  uint64_t key = position->key();
  const int ep = position->en_passant_square();
  if (ep >= 0) {
    const int side = position->side_to_move();
    const Bitboard capturers =
        fow::kPawnAttacks[side ^ 1][ep] & position->pieces(fow::kPawn, side);
    if (capturers == 0) key ^= fow::g_zobrist_en_passant_file[fow::FileOf(ep)];
  }
  return key;
}

int fow_position_legal_moves(const void* handle, char* out, int capacity) {
  MoveList legal;
  AsPosition(handle)->GenerateMoves(&legal);
  return WriteMoves(legal, out, capacity);
}

int fow_position_push(void* handle, const char* uci) {
  Position* position = AsPosition(handle);
  const Move move = FindMove(*position, uci);
  if (move == fow::kNullMove) return 0;
  fow::UndoState undo;
  position->MakeMove(move, &undo);
  return 1;
}

// True when the side that just moved left its king capturable or has no king,
// which is the referee's "King capturable" test for the side to move's win.
int fow_position_mover_lost(const void* handle) {
  return AsPosition(handle)->PreviousMoverIsLost() ? 1 : 0;
}

int fow_position_king_square(const void* handle, int color) {
  return AsPosition(handle)->KingSquare(color);
}

// -1 for empty, otherwise piece type + 6 * color.
int fow_position_piece_at(const void* handle, int square) {
  const Position* position = AsPosition(handle);
  const int type = position->piece_at(square);
  if (type == fow::kNoPiece) return -1;
  return type + 6 * position->color_at(square);
}

int fow_position_is_attacked(const void* handle, int square, int by_color) {
  return AsPosition(handle)->IsAttacked(square, by_color) ? 1 : 0;
}

// Applies `uci` to a copy and reports whether the mover's king is then
// capturable: 1 if so, 0 if not, -1 if the move is not legal here.
int fow_move_loses_king(const void* handle, const char* uci) {
  Position copy = *AsPosition(handle);
  const Move move = FindMove(copy, uci);
  if (move == fow::kNullMove) return -1;
  fow::UndoState undo;
  copy.MakeMove(move, &undo);
  return copy.PreviousMoverIsLost() ? 1 : 0;
}

int fow_legal_from_observation(const char* observation, int side,
                               unsigned long long rights, int en_passant,
                               char* out, int capacity) {
  fow_initialize();
  const std::string text(observation);
  if (!Observation::IsValid(text)) {
    out[0] = '\0';
    return -1;
  }
  const Observation view(text);
  Position visible;
  fow::VisiblePositionFromObservation(view, side, static_cast<Bitboard>(rights),
                                      en_passant, &visible);
  MoveList legal;
  fow::LegalMovesFromObservation(visible, view, &legal);
  return WriteMoves(legal, out, capacity);
}

int fow_infer_en_passant(const char* previous, const char* current, int side) {
  fow_initialize();
  const std::string now(current);
  if (!Observation::IsValid(now)) return -1;
  const Observation view(now);
  if (previous == nullptr || *previous == '\0') {
    return fow::InferEnPassant(nullptr, view, side);
  }
  const std::string before(previous);
  if (!Observation::IsValid(before)) return -1;
  const Observation earlier(before);
  return fow::InferEnPassant(&earlier, view, side);
}

// ---- The engine, for use as a league opponent and as a hybrid baseline.

void* fow_engine_new(int side, double base_seconds, double increment_seconds,
                     unsigned long long seed, unsigned long long node_budget,
                     int particles) {
  fow_initialize();
  fow::EngineOptions options = fow::EngineOptionsFromEnvironment();
  if (node_budget > 0) options.node_budget = node_budget;
  if (particles > 0) options.particle_count = particles;
  return new fow::Engine(side, base_seconds, increment_seconds, options, seed);
}

void fow_engine_free(void* handle) { delete static_cast<fow::Engine*>(handle); }

int fow_engine_observe(void* handle, const char* observation,
                       int reflects_own_move) {
  const std::string text(observation);
  if (!Observation::IsValid(text)) return 0;
  static_cast<fow::Engine*>(handle)->Observe(Observation(text),
                                             reflects_own_move != 0);
  return 1;
}

int fow_engine_choose(void* handle, const char* observation,
                      double remaining_seconds, char* out) {
  const std::string text(observation);
  out[0] = '\0';
  if (!Observation::IsValid(text)) return 0;
  fow::DecisionTrace trace;
  const Move move = static_cast<fow::Engine*>(handle)->ChooseMove(
      Observation(text), remaining_seconds, &trace);
  if (move == fow::kNullMove) return 0;
  const std::string uci = fow::MoveToUci(move);
  std::memcpy(out, uci.data(), uci.size());
  out[uci.size()] = '\0';
  return 1;
}

void fow_engine_notify(void* handle, const char* uci) {
  fow::Engine* engine = static_cast<fow::Engine*>(handle);
  // The engine records moves as its own packed type; recover it from the
  // believed state, where the move is legal by construction.
  const Position& reference = engine->belief().Representative();
  Position copy = reference;
  copy.set_side_to_move(engine->belief().our_side());
  const Move move = FindMove(copy, uci);
  if (move != fow::kNullMove) engine->NotifyMovePlayed(move);
}

}  // extern "C"
