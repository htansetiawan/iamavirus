// Copyright 2026. Fog of War chess engine.

#include "belief.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <random>
#include <vector>

namespace fow {
namespace {

// Starting material, used only to seed the census and to rebuild a plausible
// population if every hypothesis is ever contradicted.
constexpr std::array<int, kNumPieceTypes> kInitialCensus = {8, 2, 2, 2, 1, 1};

// A particle whose weight falls below this is treated as dead rather than kept
// around contributing nothing.
constexpr double kNegligibleWeight = 1e-12;

// Ceiling on the enumerated successor pool, so a position with an unusually
// large number of consistent explanations cannot blow up memory or time.
constexpr std::size_t kMaxPoolSize = 20000;

Position StartingPosition() {
  Position position;
  PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                  &position);
  return position;
}

}  // namespace

BeliefState::BeliefState(int our_side, int particle_count, uint64_t seed)
    : our_side_(our_side),
      target_count_(std::max(1, particle_count)),
      rng_(seed) {
  enemy_census_ = kInitialCensus;
  // The opening position is common knowledge, so the belief starts certain.
  particles_.assign(target_count_, StartingPosition());
  representative_valid_ = false;
}

BeliefState::ObservedPieces BeliefState::Summarize(const Observation& view,
                                                  int color) {
  ObservedPieces seen;
  for (int square = 0; square < kNumSquares; ++square) {
    const char symbol = view.at(square);
    if (symbol == kUnseen) continue;
    seen.visible |= SquareBB(square);
    if (symbol == kEmpty) continue;
    const bool is_white = symbol >= 'A' && symbol <= 'Z';
    if (is_white != (color == kWhite)) continue;
    seen.by_type[SymbolToPieceType(symbol)] |= SquareBB(square);
  }
  return seen;
}

bool BeliefState::Agrees(const Position& position, const ObservedPieces& seen,
                         int color) {
  // Restricted to what we can see, the hypothesis must match observation
  // exactly, piece type by piece type. Equality per type also forces the
  // visible empty squares to be empty, so no separate check is needed.
  for (int type = 0; type < kNumPieceTypes; ++type) {
    if ((position.pieces(type, color) & seen.visible) != seen.by_type[type]) {
      return false;
    }
  }
  return true;
}

void BeliefState::ApplyOurMove(Move move) {
  // Our move touches only squares we can see, and every hypothesis agrees with
  // the observation there, so it is normally legal in all of them. A hypothesis
  // rebuilt after a collapse can nevertheless disagree about castling rights, so
  // legality is verified rather than assumed: applying a move that a position
  // cannot make would corrupt its piece lists.
  if (!particles_.empty()) {
    const Position& reference = particles_.front();
    const int enemy_side = our_side_ ^ 1;
    if (MoveFlagOf(move) == kFlagEnPassant) {
      enemy_census_[kPawn] = std::max(0, enemy_census_[kPawn] - 1);
    } else {
      const int victim = reference.piece_at(MoveTo(move));
      if (victim != kNoPiece && reference.color_at(MoveTo(move)) == enemy_side) {
        enemy_census_[victim] = std::max(0, enemy_census_[victim] - 1);
      }
    }
  }

  std::vector<Position> updated;
  updated.reserve(particles_.size());
  for (Position particle : particles_) {
    particle.set_side_to_move(our_side_);
    MoveList legal;
    particle.GenerateMoves(&legal);
    bool allowed = false;
    for (const Move candidate : legal) {
      if (candidate == move) {
        allowed = true;
        break;
      }
    }
    if (!allowed) continue;
    UndoState undo;
    particle.MakeMove(move, &undo);
    updated.push_back(particle);
  }
  if (!updated.empty()) {
    particles_.swap(updated);
  }
  representative_valid_ = false;
}

BeliefUpdateReport BeliefState::Observe(const Observation& view,
                                       bool reflects_our_own_move) {
  BeliefUpdateReport report;
  // The census is brought up to date first, before anything can consult it.
  // Rebuilding a contradicted population reads it to decide how much material to
  // scatter behind the fog, and a census that has not yet noticed a promotion
  // still counts the pawn that was spent as well as the piece it became, handing
  // the opponent one more piece than they own.
  ReconcileCensus(view);

  if (!seen_any_) {
    // Nothing has moved yet, so there is nothing to predict.
    seen_any_ = true;
    Condition(view, &report);
  } else if (reflects_our_own_move) {
    Condition(view, &report);
  } else {
    PredictAndCondition(view, &report);
  }
  if (particles_.empty()) {
    Recover(view, &report);
  }
  representative_valid_ = false;
  return report;
}

void BeliefState::Condition(const Observation& view,
                            BeliefUpdateReport* report) {
  const ObservedPieces enemy = Summarize(view, our_side_ ^ 1);
  const ObservedPieces ours = Summarize(view, our_side_);
  std::vector<Position> kept;
  kept.reserve(particles_.size());
  for (const Position& particle : particles_) {
    if (Agrees(particle, enemy, our_side_ ^ 1) &&
        Agrees(particle, ours, our_side_)) {
      kept.push_back(particle);
    }
  }
  report->surviving_particles = static_cast<int>(kept.size());
  if (kept.empty()) {
    particles_.clear();
    return;
  }
  // Survivors are equally likely, so refill by cycling through them.
  particles_.resize(target_count_);
  for (int i = 0; i < target_count_; ++i) {
    particles_[i] = kept[i % kept.size()];
  }
  report->resampled_particles = target_count_;
}

void BeliefState::PredictAndCondition(const Observation& view,
                                      BeliefUpdateReport* report) {
  const int enemy_side = our_side_ ^ 1;
  const ObservedPieces enemy = Summarize(view, enemy_side);
  const ObservedPieces ours = Summarize(view, our_side_);

  // Enumerate every successor of every hypothesis that the new observation
  // allows, then resample the population from that pool. Keeping only one
  // successor per particle would throw away most of the posterior's support for
  // no reason: typically around twenty of the opponent's moves are entirely
  // invisible to us and so equally consistent, and a filter that samples one of
  // them per particle loses diversity far faster than it needs to.
  std::vector<Position> pool;
  std::vector<double> weights;
  int64_t consistent_total = 0;
  int considered = 0;

  for (Position particle : particles_) {
    particle.set_side_to_move(enemy_side);
    MoveList moves;
    particle.GenerateMoves(&moves);
    if (moves.empty()) continue;  // this hypothesis could not have moved at all
    ++considered;
    // Probability of any one specific move under a uniform opponent policy.
    const double move_probability = 1.0 / static_cast<double>(moves.size());
    int consistent = 0;
    for (const Move move : moves) {
      if (pool.size() >= kMaxPoolSize) break;
      UndoState undo;
      particle.MakeMove(move, &undo);
      if (Agrees(particle, enemy, enemy_side) &&
          Agrees(particle, ours, our_side_)) {
        pool.push_back(particle);
        weights.push_back(move_probability);
        ++consistent;
      }
      particle.UnmakeMove(move, undo);
    }
    consistent_total += consistent;
  }

  report->surviving_particles = static_cast<int>(pool.size());
  report->mean_consistent_moves =
      considered > 0 ? static_cast<double>(consistent_total) / considered : 0.0;
  if (pool.empty()) {
    particles_.clear();
    return;
  }
  Resample(weights, pool, report);
}

void BeliefState::Resample(const std::vector<double>& weights,
                           const std::vector<Position>& pool,
                           BeliefUpdateReport* report) {
  const double total = std::accumulate(weights.begin(), weights.end(), 0.0);
  particles_.clear();
  particles_.reserve(target_count_);
  if (total <= kNegligibleWeight) {
    // Degenerate weights carry no information; fall back to uniform.
    for (int i = 0; i < target_count_; ++i) {
      particles_.push_back(pool[i % pool.size()]);
    }
    report->resampled_particles = target_count_;
    return;
  }
  // Systematic resampling: one uniform draw, then evenly spaced strata. This has
  // lower variance than drawing each particle independently and is O(n).
  std::uniform_real_distribution<double> uniform(0.0, 1.0);
  const double step = total / target_count_;
  double pointer = uniform(rng_) * step;
  double cumulative = weights[0];
  std::size_t index = 0;
  for (int i = 0; i < target_count_; ++i) {
    while (pointer > cumulative && index + 1 < weights.size()) {
      ++index;
      cumulative += weights[index];
    }
    particles_.push_back(pool[index]);
    pointer += step;
  }
  report->resampled_particles = target_count_;
}

void BeliefState::Recover(const Observation& view,
                          BeliefUpdateReport* report) {
  // Every hypothesis has been contradicted. Rebuild from what we can see,
  // scattering the material the opponent is believed to still own across the
  // squares we cannot. This keeps play going on a defensible guess rather than
  // collapsing, and the filter re-converges as more observations arrive.
  report->collapsed = true;
  const int enemy_side = our_side_ ^ 1;
  Position visible;
  VisiblePositionFromObservation(view, our_side_, 0, -1, &visible);

  std::array<int, kNumPieceTypes> missing{};
  for (int type = 0; type < kNumPieceTypes; ++type) {
    missing[type] = std::max(
        0, enemy_census_[type] - PopCount(visible.pieces(type, enemy_side)));
  }

  std::vector<int> hidden;
  for (int square = 0; square < kNumSquares; ++square) {
    if (view.IsUnseen(square)) hidden.push_back(square);
  }

  // Rebuild castling rights from what the board shows: a right is possible
  // whenever the king and that rook are still on their home squares. Ours is
  // directly observable; for the opponent an unseen home square is treated as
  // still holding the rook, which is the cautious reading.
  Bitboard rebuilt_rights = 0;
  for (const int color : {kWhite, kBlack}) {
    const int rank = color == kWhite ? 0 : 7;
    const int king_square = MakeSquare(4, rank);
    const char king_symbol = PieceTypeToSymbol(kKing, color);
    const char rook_symbol = PieceTypeToSymbol(kRook, color);
    const bool king_home = color == our_side_
                               ? view.at(king_square) == king_symbol
                               : view.at(king_square) != kEmpty;
    if (!king_home) continue;
    for (const int file : {0, 7}) {
      const int rook_square = MakeSquare(file, rank);
      const bool rook_home = color == our_side_
                                 ? view.at(rook_square) == rook_symbol
                                 : view.at(rook_square) != kEmpty;
      if (rook_home && visible.piece_at(rook_square) == kRook) {
        rebuilt_rights |= SquareBB(rook_square);
      }
    }
  }

  particles_.clear();
  for (int i = 0; i < target_count_; ++i) {
    Position particle = visible;
    std::shuffle(hidden.begin(), hidden.end(), rng_);

    // Squares still available in this hypothesis, consumed as pieces are placed.
    //
    // Taking squares from a pool, rather than walking a cursor forward, is what
    // makes this exhaustive. A cursor spends a square even when the piece cannot
    // legally stand there -- a pawn on a promotion rank -- so the heavier pieces
    // placed first could burn through the list and leave pawns with nowhere to
    // go, quietly handing the opponent less material than they have. Every
    // hidden enemy piece occupies a square we cannot see, so the pool is always
    // large enough when no square is wasted.
    std::vector<int> available = hidden;
    // Pawns are placed first because they are the only constrained piece: they
    // cannot stand on a promotion rank. Placing the free-roaming pieces first
    // can leave a pawn with nothing but promotion-rank squares and so drop it
    // from the rebuild, which is how a hypothesis ended up a piece short.
    // Every hidden pawn really does sit on a non-promotion fog square, so
    // satisfying the constrained type first always succeeds.
    for (const int type : {kPawn, kKnight, kBishop, kRook, kQueen, kKing}) {
      for (int placed = 0; placed < missing[type]; ++placed) {
        std::size_t chosen = available.size();
        for (std::size_t index = 0; index < available.size(); ++index) {
          const int square = available[index];
          if (particle.piece_at(square) != kNoPiece) continue;
          if (type == kPawn && (RankOf(square) == 0 || RankOf(square) == 7)) {
            continue;  // a pawn cannot stand on a promotion rank
          }
          chosen = index;
          break;
        }
        if (chosen == available.size()) break;  // nowhere left for this type
        particle.PutPiece(available[chosen], enemy_side, type);
        available.erase(available.begin() + static_cast<std::ptrdiff_t>(chosen));
      }
    }
    particle.set_side_to_move(our_side_);
    particle.set_castling_rights(rebuilt_rights);
    particles_.push_back(particle);
  }
  report->resampled_particles = target_count_;
}

void BeliefState::ReconcileCensus(const Observation& view) {
  // Seeing more of a piece type than we were counting means a pawn promoted
  // behind the fog. We cannot tell which pawn, but we do know a pawn was spent
  // to produce it, so the pawn count must come down by the same amount.
  // Raising the one without lowering the other would inflate the army, and a
  // rebuild would then hand the opponent a piece they never had.
  const int enemy_side = our_side_ ^ 1;
  for (int type = 0; type < kNumPieceTypes; ++type) {
    if (type == kPawn) continue;
    const int visible = PopCount(view.VisiblePieces(enemy_side, type));
    if (visible <= enemy_census_[type]) continue;
    const int promoted = visible - enemy_census_[type];
    enemy_census_[type] = visible;
    enemy_census_[kPawn] = std::max(0, enemy_census_[kPawn] - promoted);
  }
  // A pawn we can see is a pawn that exists, so never let the count fall below
  // what is on display.
  const int visible_pawns = PopCount(view.VisiblePieces(enemy_side, kPawn));
  if (visible_pawns > enemy_census_[kPawn]) {
    enemy_census_[kPawn] = visible_pawns;
  }
}

const Position& BeliefState::Representative() const {
  if (representative_valid_) return particles_[representative_index_];
  const int enemy_side = our_side_ ^ 1;
  // Marginal frequency of each (square, piece type) across the population.
  std::array<std::array<int, kNumSquares>, kNumPieceTypes> frequency{};
  for (const Position& particle : particles_) {
    for (int type = 0; type < kNumPieceTypes; ++type) {
      Bitboard pieces = particle.pieces(type, enemy_side);
      while (pieces) ++frequency[type][PopLsb(&pieces)];
    }
  }
  // Pick the hypothesis that agrees most with those marginals. Unlike a
  // square-by-square consensus board, this is guaranteed to be a real position.
  int best_index = 0;
  int64_t best_score = -1;
  for (std::size_t i = 0; i < particles_.size(); ++i) {
    int64_t score = 0;
    for (int type = 0; type < kNumPieceTypes; ++type) {
      Bitboard pieces = particles_[i].pieces(type, enemy_side);
      while (pieces) score += frequency[type][PopLsb(&pieces)];
    }
    if (score > best_score) {
      best_score = score;
      best_index = static_cast<int>(i);
    }
  }
  representative_index_ = best_index;
  representative_valid_ = true;
  return particles_[representative_index_];
}

std::vector<const Position*> BeliefState::Sample(int wanted) const {
  std::vector<const Position*> chosen;
  if (particles_.empty() || wanted <= 0) return chosen;
  // The representative first, so the likeliest hypothesis is always considered.
  chosen.push_back(&Representative());
  if (wanted == 1) return chosen;
  // Then spread evenly through the population. After resampling the population
  // is already distributed by posterior weight, so even strides sample it fairly
  // and cheaply, with no extra randomness needed.
  const std::size_t stride = std::max<std::size_t>(1, particles_.size() / (wanted - 1));
  for (std::size_t i = 0; i < particles_.size() && static_cast<int>(chosen.size()) < wanted;
       i += stride) {
    if (&particles_[i] != chosen.front()) chosen.push_back(&particles_[i]);
  }
  return chosen;
}

FogContext BeliefState::MakeFogContext(const Observation& view) const {
  const Position& reference = Representative();
  const int enemy_side = our_side_ ^ 1;
  FogContext fog;
  fog.unseen = view.UnseenMask();
  fog.side = our_side_;
  const int queens = PopCount(reference.pieces(kQueen, enemy_side));
  fog.rook_like = PopCount(reference.pieces(kRook, enemy_side)) + queens;
  fog.bishop_like = PopCount(reference.pieces(kBishop, enemy_side)) + queens;
  fog.knights = PopCount(reference.pieces(kKnight, enemy_side));
  fog.pawns = PopCount(reference.pieces(kPawn, enemy_side));
  return fog;
}

bool BeliefState::EnemyKingVisible(const Observation& view) const {
  const char king = PieceTypeToSymbol(kKing, our_side_ ^ 1);
  for (int square = 0; square < kNumSquares; ++square) {
    if (view.at(square) == king) return true;
  }
  return false;
}

}  // namespace fow
