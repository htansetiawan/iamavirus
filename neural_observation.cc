// Copyright 2026. Fog of War chess engine.

#include "neural_observation.h"

#include <algorithm>
#include <cstring>

namespace fow {
namespace {

constexpr int kClassEmpty = 12;
constexpr int kClassNever = -1;

}  // namespace

int PromotionCode(Move move) {
  switch (PromotionType(move)) {
    case kQueen: return 1;
    case kRook: return 2;
    case kBishop: return 3;
    case kKnight: return 4;
    default: return 0;
  }
}

NeuralTracker::NeuralTracker(int side) : side_(side) {
  last_seen_.fill(static_cast<int8_t>(kClassNever));
  last_seen_ply_.fill(-1);
  ever_seen_.fill(false);
  const int rank = side == kWhite ? 0 : 7;
  king_home_ = MakeSquare(4, rank);
  rook_home_queenside_ = MakeSquare(0, rank);
  rook_home_kingside_ = MakeSquare(7, rank);
  own_king_ = PieceTypeToSymbol(kKing, side);
  own_rook_ = PieceTypeToSymbol(kRook, side);
}

// 0..5 own piece, 6..11 enemy piece, 12 visible empty, -1 unknown.
int NeuralTracker::RelativeClass(char symbol) const {
  if (symbol == kUnseen) return kClassNever;
  if (symbol == kEmpty) return kClassEmpty;
  const bool is_white = symbol >= 'A' && symbol <= 'Z';
  const bool own = is_white == (side_ == kWhite);
  return SymbolToPieceType(symbol) + (own ? 0 : 6);
}

void NeuralTracker::Observe(const Observation& view, int phase, int ply) {
  previous_ = current_;
  have_previous_ = have_current_;
  current_ = view;
  have_current_ = true;
  previous_phase_ = phase_;
  phase_ = phase;
  ply_ = ply;
  ++events_;
  // Sticky castling rights: once gone, never restored by a returning rook.
  if (view.at(king_home_) != own_king_) kingside_ = queenside_ = false;
  if (view.at(rook_home_queenside_) != own_rook_) queenside_ = false;
  if (view.at(rook_home_kingside_) != own_rook_) kingside_ = false;
  for (int raw = 0; raw < kNumSquares; ++raw) {
    const char symbol = view.at(raw);
    if (symbol == kUnseen) continue;
    const int c = CanonicalSquare(raw, side_);
    last_seen_[c] = static_cast<int8_t>(RelativeClass(symbol));
    last_seen_ply_[c] = ply;
    ever_seen_[c] = true;
  }
}

void NeuralTracker::RecordOwnMove(Move move) {
  const int from = MoveFrom(move);
  last_own_from_ = CanonicalSquare(from, side_);
  last_own_to_ = CanonicalSquare(MoveTo(move), side_);
  if (from == king_home_ && have_current_ && current_.at(from) == own_king_) {
    kingside_ = queenside_ = false;
  }
  if (from == rook_home_queenside_) queenside_ = false;
  if (from == rook_home_kingside_) kingside_ = false;
}

Bitboard NeuralTracker::CastlingRights() const {
  Bitboard rights = 0;
  if (queenside_) rights |= SquareBB(rook_home_queenside_);
  if (kingside_) rights |= SquareBB(rook_home_kingside_);
  return rights;
}

int NeuralTracker::EnPassant() const {
  if (!our_turn() || !have_current_) return -1;
  if (phase_ != kPhaseAfterOpponentMove || !have_previous_) return -1;
  if (previous_phase_ == kPhaseAfterOpponentMove) return -1;
  return InferEnPassant(&previous_, current_, side_);
}

void NeuralTracker::LegalCandidates(MoveList* list) const {
  list->clear();
  if (!have_current_ || !our_turn()) return;
  Position visible;
  VisiblePositionFromObservation(current_, side_, CastlingRights(), EnPassant(),
                                 &visible);
  LegalMovesFromObservation(visible, current_, list);
}

std::vector<NeuralCandidate> NeuralTracker::MakeCandidates(
    const MoveList& moves) const {
  std::vector<NeuralCandidate> out;
  out.reserve(static_cast<std::size_t>(moves.size()));
  for (const Move move : moves) {
    NeuralCandidate candidate;
    candidate.move = move;
    candidate.from = CanonicalSquare(MoveFrom(move), side_);
    candidate.to = CanonicalSquare(MoveTo(move), side_);
    candidate.promotion = PromotionCode(move);
    out.push_back(candidate);
  }
  return out;
}

void NeuralTracker::Planes(float* out) const {
  std::memset(out, 0, sizeof(float) * kNeuralPlanes * kNumSquares);
  auto plane = [out](int index) { return out + index * kNumSquares; };
  if (have_current_) {
    for (int raw = 0; raw < kNumSquares; ++raw) {
      const int c = CanonicalSquare(raw, side_);
      const int klass = RelativeClass(current_.at(raw));
      plane(klass == kClassNever ? 12 : klass)[c] = 1.0f;
    }
  }
  for (int c = 0; c < kNumSquares; ++c) {
    if (ever_seen_[c]) {
      plane(14 + last_seen_[c])[c] = 1.0f;
      plane(27)[c] = 1.0f;
      const int age = std::min(ply_ - last_seen_ply_[c], kAgeCap);
      plane(28)[c] = static_cast<float>(age) / static_cast<float>(kAgeCap);
    } else {
      plane(28)[c] = 1.0f;
    }
  }
  if (last_own_from_ >= 0) {
    plane(29)[last_own_from_] = 1.0f;
    plane(30)[last_own_to_] = 1.0f;
  }
  const int ep = EnPassant();
  if (ep >= 0) plane(31)[CanonicalSquare(ep, side_)] = 1.0f;
}

void NeuralTracker::Scalars(float* out) const {
  out[0] = static_cast<float>(side_);
  out[1] = our_turn() ? 1.0f : 0.0f;
  out[2] = kingside_ ? 1.0f : 0.0f;
  out[3] = queenside_ ? 1.0f : 0.0f;
  out[4] = phase_ == kPhaseInitial ? 1.0f : 0.0f;
  out[5] = phase_ == kPhaseAfterOwnMove ? 1.0f : 0.0f;
  out[6] = phase_ == kPhaseAfterOpponentMove ? 1.0f : 0.0f;
  out[7] = static_cast<float>(std::min(ply_, kPlyCap)) / static_cast<float>(kPlyCap);
}

}  // namespace fow
