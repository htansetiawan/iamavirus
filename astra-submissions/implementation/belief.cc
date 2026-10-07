// Copyright 2026. Fog of War chess engine.

#include "belief.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <random>
#include <unordered_map>
#include <vector>

namespace fow {
namespace {

// Starting material, used only to seed the census and to rebuild a plausible
// population if every hypothesis is ever contradicted.
constexpr std::array<int, kNumPieceTypes> kInitialCensus = {8, 2, 2, 2, 1, 1};

// A particle whose weight falls below this is treated as dead rather than kept
// around contributing nothing.
constexpr double kNegligibleWeight = 1e-12;

// Opponent-model priors, as multipliers on a move's plausibility.
// Deliberately crude: the point is to be far better than uniform, not exact.
constexpr double kBasePlausibility = 1.0;
// Leaving a piece where we can take it for less than its worth. Opponents do
// this occasionally by blunder or as a deliberate sacrifice, so it is unlikely
// rather than impossible; the value sets how suspicious a free gift looks.
constexpr double kGiveawayFactor = 0.06;
// Captures are over-represented in the moves real opponents choose.
constexpr double kCaptureFactor = 2.5;
// Moving a piece to where it attacks our king is purposeful.
constexpr double kAttacksOurKingFactor = 3.0;

// Ceiling on the enumerated successor pool, so a position with an unusually
// large number of consistent explanations cannot blow up memory or time.
constexpr std::size_t kMaxPoolSize = 20000;
constexpr int kHistoryFrames = 16;
constexpr int kHistoryTransitionsPerAttempt = 250000;
constexpr std::size_t kHistoryPoolLimit = 65536;

Position StartingPosition() {
  Position position;
  PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                  &position);
  return position;
}

// Equality covers all state used by this hand-prior filter, including rights,
// EP and the halfmove clock. Hash collisions are resolved by full equality.
// A future history-dependent opponent model must also key its private metadata.
struct StateIdentity {
  std::array<uint64_t, 9> fields{};
  explicit StateIdentity(const Position& p) {
    for (int type = 0; type < kNumPieceTypes; ++type) fields[type] = p.pieces(type);
    fields[6] = p.pieces_of(kWhite);
    fields[7] = p.castling_rights();
    fields[8] = (static_cast<uint64_t>(p.halfmove_clock()) << 8) |
                (static_cast<uint64_t>(p.en_passant_square() + 1) << 1) |
                static_cast<uint64_t>(p.side_to_move());
  }
  bool operator==(const StateIdentity&) const = default;
};

struct StateIdentityHash {
  std::size_t operator()(const StateIdentity& key) const {
    uint64_t hash = 0x9e3779b97f4a7c15ULL;
    for (uint64_t value : key.fields) {
      value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
      value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
      hash ^= value ^ (value >> 31);
      hash = (hash << 27) | (hash >> 37);
    }
    return static_cast<std::size_t>(hash);
  }
};

// An unbiased allocation of `draws` offspring with low marginal variance.
// Zero-weight entries cannot receive an offspring, even on an exact zero draw.
std::vector<int> SystematicCounts(const std::vector<double>& weights, int draws,
                                  std::mt19937_64* rng) {
  std::vector<int> counts(weights.size(), 0);
  std::vector<std::size_t> order;
  double total = 0.0;
  for (std::size_t i = 0; i < weights.size(); ++i) {
    if (weights[i] > 0.0) { order.push_back(i); total += weights[i]; }
  }
  if (draws <= 0 || total <= kNegligibleWeight || order.empty()) return counts;
  std::shuffle(order.begin(), order.end(), *rng);
  const double step = total / draws;
  double pointer = std::uniform_real_distribution<double>(0.0, 1.0)(*rng) * step;
  std::size_t at = 0;
  double cumulative = weights[order[0]];
  for (int i = 0; i < draws; ++i) {
    while (pointer > cumulative && at + 1 < order.size()) cumulative += weights[order[++at]];
    ++counts[order[at]];
    pointer += step;
  }
  return counts;
}

}  // namespace

BeliefState::BeliefState(int our_side, int particle_count, uint64_t seed,
                         bool use_opponent_prior, bool preserve_capture_evidence,
                         bool use_visibility_deductions, bool use_grouped_prediction,
                         bool use_continuation_evidence, bool use_history_recovery)
    : our_side_(our_side),
      target_count_(std::max(1, particle_count)),
      use_opponent_prior_(use_opponent_prior),
      preserve_capture_evidence_(preserve_capture_evidence),
      use_visibility_deductions_(use_visibility_deductions),
      use_grouped_prediction_(use_grouped_prediction),
      use_continuation_evidence_(use_continuation_evidence),
      use_history_recovery_(use_history_recovery),
      rng_(seed) {
  enemy_census_ = kInitialCensus;
  const int home_rank = our_side == kWhite ? 0 : 7;
  own_rights_ = SquareBB(MakeSquare(0, home_rank)) | SquareBB(MakeSquare(7, home_rank));
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

bool BeliefState::AgreesAboutEnemy(const Position& position,
                                   const ObservedPieces& seen, int color) {
  // Restricted to what we can see, the hypothesis must match the observation
  // exactly, piece type by piece type. Equality per type also forces the visible
  // empty squares to be empty, so no separate check is needed.
  for (int type = 0; type < kNumPieceTypes; ++type) {
    if ((position.pieces(type, color) & seen.visible) != seen.by_type[type]) {
      return false;
    }
  }
  if ((position.pieces_of(color) & seen.must_hold_enemy) != seen.must_hold_enemy) return false;
  if (position.pieces_of(color) & seen.must_be_empty) return false;
  return true;
}

bool BeliefState::AgreesAboutUs(const Position& position,
                                const ObservedPieces& seen, int color) {
  // No visibility mask: every piece of ours is observed, so the observation
  // lists all of them and the hypothesis must match it everywhere.
  for (int type = 0; type < kNumPieceTypes; ++type) {
    if (position.pieces(type, color) != seen.by_type[type]) return false;
  }
  return true;
}

double BeliefState::MovePlausibility(Position* hypothesis, Move move) const {
  if (!use_opponent_prior_) return kBasePlausibility;  // uniform over their moves
  const int enemy_side = our_side_ ^ 1;
  const int to = MoveTo(move);
  double weight = kBasePlausibility;
  const bool is_capture = hypothesis->piece_at(to) != kNoPiece ||
                          MoveFlagOf(move) == kFlagEnPassant;
  const int captured =
      is_capture && hypothesis->piece_at(to) != kNoPiece
          ? kPieceValue[hypothesis->piece_at(to)]
          : (MoveFlagOf(move) == kFlagEnPassant ? kPieceValue[kPawn] : 0);
  if (is_capture) weight *= kCaptureFactor;

  UndoState undo;
  hypothesis->MakeMove(move, &undo);
  const int moved = hypothesis->piece_at(to);
  const int value = moved == kNoPiece ? 0 : kPieceValue[moved];
  // Can we take it, and would that trade favour us? Their own defence of the
  // square is what makes an offer sensible rather than a gift.
  const Bitboard our_attackers = hypothesis->AttackersTo(to, our_side_);
  const bool defended = hypothesis->AttackersTo(to, enemy_side) != 0;
  if (our_attackers != 0 && !defended && value > captured) {
    weight *= kGiveawayFactor;
  }
  const int our_king = hypothesis->KingSquare(our_side_);
  if (our_king >= 0 && (hypothesis->AttackersTo(our_king, enemy_side) &
                        SquareBB(to))) {
    weight *= kAttacksOurKingFactor;
  }
  hypothesis->UnmakeMove(move, undo);
  return weight;
}

void BeliefState::UpdateOwnRights(const Observation& view) {
  const int home_rank = our_side_ == kWhite ? 0 : 7;
  if (view.at(MakeSquare(4, home_rank)) != PieceTypeToSymbol(kKing, our_side_)) {
    own_rights_ = 0;
  }
  for (const int file : {0, 7}) {
    const int rook = MakeSquare(file, home_rank);
    if (view.at(rook) != PieceTypeToSymbol(kRook, our_side_)) {
      own_rights_ &= ~SquareBB(rook);
    }
  }
}

void BeliefState::ApplyOurMove(Move move) {
  if (use_history_recovery_) pending_history_move_ = move;
  own_double_push_square_ = MoveFlagOf(move) == kFlagDoublePush ? MoveTo(move) : -1;
  const int taken = MoveFlagOf(move) == kFlagEnPassant
                        ? MoveTo(move) + (our_side_ == kWhite ? -8 : 8)
                        : MoveTo(move);
  if (taken == capture_square_) capture_square_ = -1;
  const int home_rank = our_side_ == kWhite ? 0 : 7;
  if (MoveFrom(move) == MakeSquare(4, home_rank) && !particles_.empty() &&
      particles_.front().piece_at(MoveFrom(move)) == kKing) {
    own_rights_ = 0;
  }
  own_rights_ &= ~SquareBB(MoveFrom(move));
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
  if (!updated.empty() || use_history_recovery_) {
    particles_.swap(updated);
  }
  representative_valid_ = false;
}

BeliefUpdateReport BeliefState::Observe(const Observation& view,
                                       bool reflects_our_own_move) {
  BeliefUpdateReport report;
  previous_mover_ = seen_any_ ? (reflects_our_own_move ? our_side_ : our_side_ ^ 1) : -1;
  report.continuation_previous_mover = previous_mover_;
  if (seen_any_ && !reflects_our_own_move) {
    capture_square_ = -1;  // an unseen opponent move may relocate the capturer
    if (preserve_capture_evidence_) InferCaptureEvidence(view, &report);
    own_double_push_square_ = -1;
  }
  report.capture_square = capture_square_;
  // The census is brought up to date first, before anything can consult it.
  // Rebuilding a contradicted population reads it to decide how much material to
  // scatter behind the fog, and a census that has not yet noticed a promotion
  // still counts the pawn that was spent as well as the piece it became, handing
  // the opponent one more piece than they own.
  ReconcileCensus(view);
  UpdateOwnRights(view);

  if (!seen_any_) {
    // Nothing has moved yet, so there is nothing to predict.
    seen_any_ = true;
    Condition(view, &report);
  } else if (reflects_our_own_move) {
    Condition(view, &report);
  } else {
    PredictAndCondition(view, &report);
  }
  if (use_history_recovery_) {
    // Matching the visible contents alone does not prove that the visibility
    // mask is possible. Certification checks the complete actor observation.
    HistoryFrame frame;
    frame.view = view;
    frame.ours = Summarize(view, our_side_);
    frame.enemy = Summarize(view, our_side_ ^ 1);
    frame.previous_mover = previous_mover_;
    particles_.erase(std::remove_if(particles_.begin(), particles_.end(),
        [&](const Position& p) { return !MatchesHistoryFrame(p, frame); }),
        particles_.end());
  }
  if (particles_.empty()) {
    report.collapsed = true;
    if (!use_history_recovery_ || !RecoverFromHistory(view, &report)) {
      Recover(view, &report);
      history_full_certified_ = false;
    }
  }
  if (use_history_recovery_) {
    RememberHistory(view);
    report.history_full_certified = history_full_certified_;
    pending_history_move_ = kNullMove;
  }
  representative_valid_ = false;
  previous_view_ = view;
  last_report_ = report;
  return report;
}

bool BeliefState::MatchesHistoryFrame(const Position& position,
                                       const HistoryFrame& frame) const {
  // A legal live history must survive referee adjudication at every step.
  // This is mandatory for history certification even if the separate
  // continuation ablation is disabled on the ordinary filter path.
  if (frame.previous_mover >= 0) {
    const int king = position.KingSquare(frame.previous_mover);
    if (king < 0 || position.IsAttacked(king, frame.previous_mover ^ 1)) return false;
  }
  // Cheap piece constraints before generating the full visibility mask.
  if (!AgreesAboutUs(position, frame.ours, our_side_) ||
      !AgreesAboutEnemy(position, frame.enemy, our_side_ ^ 1)) return false;
  return RenderObservation(position, our_side_) == frame.view.squares();
}

void BeliefState::RememberHistory(const Observation& view) {
  HistoryFrame frame;
  frame.view = view;
  frame.ours = Summarize(view, our_side_);
  frame.enemy = Summarize(view, our_side_ ^ 1);
  frame.previous_mover = previous_mover_;
  frame.own_move = previous_mover_ == our_side_ ? pending_history_move_ : kNullMove;
  frame.full_certified = history_full_certified_;
  std::unordered_map<StateIdentity, std::size_t, StateIdentityHash> index;
  index.reserve(particles_.size());
  for (Position p : particles_) {
    p.set_side_to_move(previous_mover_ < 0 ? kWhite : previous_mover_ ^ 1);
    if (!MatchesHistoryFrame(p, frame)) continue;
    auto [entry, added] = index.emplace(StateIdentity(p), frame.support.size());
    if (added) frame.support.push_back({p, 1.0});
    else frame.support[entry->second].weight += 1.0;
  }
  if (history_.size() == kHistoryFrames) history_.erase(history_.begin());
  history_.push_back(std::move(frame));
}

bool BeliefState::RecoverFromHistory(const Observation& view,
                                      BeliefUpdateReport* report) {
  report->history_attempted = true;
  HistoryFrame current;
  current.view = view;
  current.ours = Summarize(view, our_side_);
  current.enemy = Summarize(view, our_side_ ^ 1);
  current.previous_mover = previous_mover_;
  current.own_move = previous_mover_ == our_side_ ? pending_history_move_ : kNullMove;
  const int count = static_cast<int>(history_.size());
  if (count == 0 || previous_mover_ < 0) return false;
  const int width = std::clamp(2 * target_count_, 64, 8192);
  std::vector<int> distances;
  // Replaying one edge from the same support cannot restore discarded mass.
  // Go back before the last resampling, and progressively farther if needed.
  for (int distance : {2, 4, 8, 16}) if (distance <= count) distances.push_back(distance);
  if (distances.empty() || distances.back() != count) distances.push_back(count);
  for (const int distance : distances) {
    const int anchor_index = count - distance;
    const HistoryFrame& anchor = history_[anchor_index];
    if (anchor.support.empty()) continue;
    ++report->history_checkpoints_tried;
    std::vector<WeightedState> support = anchor.support;
    int remaining = kHistoryTransitionsPerAttempt;
    bool failed = false;
    for (int step = anchor_index + 1; step <= count && !failed; ++step) {
      const HistoryFrame& frame = step == count ? current : history_[step];
      const int mover = frame.previous_mover;
      if (mover < 0 || (mover == our_side_ && frame.own_move == kNullMove)) {
        failed = true;
        break;
      }
      std::vector<WeightedState> next;
      std::unordered_map<StateIdentity, std::size_t, StateIdentityHash> index;
      index.reserve(std::min(kHistoryPoolLimit, support.size() * 16));
      for (const auto& parent : support) {
        Position p = parent.position;
        // The recorded sequence, not a forced side override, determines whose
        // move this is. A malformed history must not create a legal trajectory.
        if (p.side_to_move() != mover) continue;
        MoveList moves;
        p.GenerateMoves(&moves);
        const int cost = mover == our_side_ ? 1 : moves.size();
        if (cost > remaining) {
          report->history_budget_exhausted = failed = true;
          break;  // do not return a population from a partially visited level
        }
        remaining -= cost;
        report->history_transitions += cost;
        std::vector<double> priors(moves.size(), 1.0);
        double total = 1.0;
        if (mover != our_side_) {
          total = 0.0;
          for (int i = 0; i < moves.size(); ++i) {
            priors[i] = MovePlausibility(&p, moves[i]);
            total += priors[i];
          }
        }
        if (total <= 0.0) continue;
        for (int i = 0; i < moves.size(); ++i) {
          const Move move = moves[i];
          if (mover == our_side_ && move != frame.own_move) continue;
          UndoState undo;
          p.MakeMove(move, &undo);
          if (MatchesHistoryFrame(p, frame)) {
            const double weight = parent.weight * priors[i] / total;
            auto [entry, added] = index.emplace(StateIdentity(p), next.size());
            if (added) next.push_back({p, weight});
            else next[entry->second].weight += weight;
          }
          p.UnmakeMove(move, undo);
          if (next.size() > kHistoryPoolLimit) {
            report->history_budget_exhausted = failed = true;
            break;
          }
        }
        if (failed) break;
      }
      if (failed || next.empty()) { failed = true; break; }
      double total = 0.0;
      for (const auto& p : next) total += p.weight;
      if (total <= 0.0) { failed = true; break; }
      for (auto& p : next) p.weight /= total;
      if (next.size() > static_cast<std::size_t>(width)) {
        std::vector<double> weights;
        for (const auto& p : next) weights.push_back(p.weight);
        const auto copies = SystematicCounts(weights, width, &rng_);
        support.clear();
        for (std::size_t i = 0; i < next.size(); ++i) {
          if (copies[i]) support.push_back({next[i].position, static_cast<double>(copies[i]) / width});
        }
      } else {
        support.swap(next);  // keep the entire weighted set when small enough
      }
    }
    if (failed) continue;
    std::vector<double> weights;
    std::vector<Position> pool;
    for (const auto& p : support) { weights.push_back(p.weight); pool.push_back(p.position); }
    Resample(weights, pool, report);
    history_full_certified_ = anchor.full_certified;
    report->history_recovered = true;
    report->history_rewind_plies = distance;
    report->history_unique_support = static_cast<int>(pool.size());
    if (capture_square_ >= 0) {
      for (const auto& p : particles_) {
        report->capture_constraints_preserved += p.color_at(capture_square_) == (our_side_ ^ 1);
      }
    }
    return true;
  }
  return false;
}

bool BeliefState::ConsistentWithContinuation(const Position& position) const {
  if (!use_continuation_evidence_ || previous_mover_ < 0) return true;
  // referee.py adjudicates BEFORE delivering either player's next observation.
  // The previous mover's king must therefore have survived. The current
  // mover may be in a hidden check: do not reject those positions.
  const int king = position.KingSquare(previous_mover_);
  return king >= 0 && !position.IsAttacked(king, previous_mover_ ^ 1);
}

void BeliefState::InferCaptureEvidence(const Observation& view,
                                      BeliefUpdateReport* report) {
  const Bitboard before = previous_view_.VisiblePieces(our_side_);
  const Bitboard after = view.VisiblePieces(our_side_);
  const Bitboard missing = before & ~after;
  // One opponent move cannot relocate our pieces or capture two of them.
  // Existing synthetic observations may be inconsistent; report, don't invent.
  if (missing == 0) return;
  if (PopCount(missing) != 1 || (after & ~before) != 0) {
    report->capture_evidence_conflict = true;
    return;
  }
  const int square = Lsb(missing);
  const char now = view.at(square);
  if (square == own_double_push_square_ &&
      previous_view_.at(square) == PieceTypeToSymbol(kPawn, our_side_) &&
      (now == kUnseen || now == kEmpty)) {
    // It may have been taken en passant: never force a piece onto the victim's
    // vacated square. Keeping a joint normal/EP recovery is a later variant.
    report->capture_en_passant_ambiguous = true;
    return;
  }
  if (now == kEmpty) {
    report->capture_evidence_conflict = true;
    return;
  }
  capture_square_ = square;
}

void BeliefState::Condition(const Observation& view,
                            BeliefUpdateReport* report) {
  ObservedPieces enemy = Summarize(view, our_side_ ^ 1);
  if (use_visibility_deductions_) {
    const Deductions facts = DeduceFromObservation(view, our_side_);
    enemy.must_hold_enemy = facts.must_hold_enemy;
    enemy.must_be_empty = facts.must_be_empty;
  }
  const ObservedPieces ours = Summarize(view, our_side_);
  std::vector<Position> kept;
  kept.reserve(particles_.size());
  for (const Position& particle : particles_) {
    if (AgreesAboutEnemy(particle, enemy, our_side_ ^ 1) &&
        AgreesAboutUs(particle, ours, our_side_)) {
      if (ConsistentWithContinuation(particle)) kept.push_back(particle);
      else ++report->continuation_rejected;
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
  if (use_grouped_prediction_) {
    PredictAndConditionGrouped(view, report);
    return;
  }
  const int enemy_side = our_side_ ^ 1;
  ObservedPieces enemy = Summarize(view, enemy_side);
  if (use_visibility_deductions_) {
    const Deductions facts = DeduceFromObservation(view, our_side_);
    enemy.must_hold_enemy = facts.must_hold_enemy;
    enemy.must_be_empty = facts.must_be_empty;
  }
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
    ++report->expanded_predecessors;
    // Prior over their moves, normalised per hypothesis so that a hypothesis
    // offering many plausible continuations is not thereby favoured.
    double prior_total = 0.0;
    std::vector<double> prior;
    prior.reserve(static_cast<std::size_t>(moves.size()));
    for (const Move move : moves) {
      const double weight = MovePlausibility(&particle, move);
      prior.push_back(weight);
      prior_total += weight;
    }
    if (prior_total <= 0.0) continue;

    int consistent = 0;
    for (int index = 0; index < moves.size(); ++index) {
      if (pool.size() >= kMaxPoolSize) {
        report->successor_prefix_capped = true;
        break;
      }
      ++report->enumerated_transitions;
      const Move move = moves[index];
      UndoState undo;
      particle.MakeMove(move, &undo);
      if (AgreesAboutEnemy(particle, enemy, enemy_side) &&
          AgreesAboutUs(particle, ours, our_side_)) {
        if (ConsistentWithContinuation(particle)) {
          pool.push_back(particle);
          weights.push_back(prior[static_cast<std::size_t>(index)] / prior_total);
          ++consistent;
        } else {
          ++report->continuation_rejected;
        }
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

void BeliefState::PredictAndConditionGrouped(const Observation& view,
                                            BeliefUpdateReport* report) {
  const int enemy_side = our_side_ ^ 1;
  ObservedPieces enemy = Summarize(view, enemy_side);
  const ObservedPieces ours = Summarize(view, our_side_);
  if (use_visibility_deductions_) {
    const auto facts = DeduceFromObservation(view, our_side_);
    enemy.must_hold_enemy = facts.must_hold_enemy;
    enemy.must_be_empty = facts.must_be_empty;
  }
  struct WeightedMove { Move move; double weight; };
  struct Group {
    Position parent;
    int multiplicity = 1;
    std::vector<WeightedMove> children;
  };
  std::vector<Group> groups;
  std::unordered_map<StateIdentity, std::size_t, StateIdentityHash> index;
  index.reserve(particles_.size());
  for (Position parent : particles_) {
    parent.set_side_to_move(enemy_side);
    auto [entry, inserted] = index.emplace(StateIdentity(parent), groups.size());
    if (inserted) groups.push_back({parent, 1, {}});
    else ++groups[entry->second].multiplicity;
  }
  std::vector<double> group_weights(groups.size(), 0.0);
  int64_t weighted_consistent = 0;
  for (std::size_t i = 0; i < groups.size(); ++i) {
    auto& group = groups[i];
    Position parent = group.parent;
    MoveList moves;
    parent.GenerateMoves(&moves);
    ++report->expanded_predecessors;
    double prior_total = 0.0, accepted_total = 0.0;
    for (const Move move : moves) {
      ++report->enumerated_transitions;
      const double prior = MovePlausibility(&parent, move);
      prior_total += prior;  // include inconsistent moves: observation likelihood matters
      UndoState undo;
      parent.MakeMove(move, &undo);
      if (AgreesAboutEnemy(parent, enemy, enemy_side) && AgreesAboutUs(parent, ours, our_side_)) {
        if (ConsistentWithContinuation(parent)) {
          group.children.push_back({move, prior});
          accepted_total += prior;
        } else {
          ++report->continuation_rejected;
        }
      }
      parent.UnmakeMove(move, undo);
    }
    weighted_consistent += static_cast<int64_t>(group.multiplicity) * group.children.size();
    report->surviving_particles += static_cast<int>(group.children.size());
    if (prior_total > 0.0) group_weights[i] = group.multiplicity * accepted_total / prior_total;
  }
  report->mean_consistent_moves = particles_.empty() ? 0.0
      : static_cast<double>(weighted_consistent) / particles_.size();
  // Two-stage resampling visits every unique predecessor and every legal
  // transition, with no successor-prefix cutoff. Multiplicity preserves parent
  // mass. Child sampling uses its conditional weights. Expected child offspring
  // are N * parent_mass * prior(move) / total_consistent_mass.
  const auto offspring = SystematicCounts(group_weights, target_count_, &rng_);
  particles_.clear();
  particles_.reserve(target_count_);
  for (std::size_t i = 0; i < groups.size(); ++i) {
    if (offspring[i] == 0) continue;
    auto& group = groups[i];
    std::vector<double> weights;
    for (const auto& child : group.children) weights.push_back(child.weight);
    const auto copies = SystematicCounts(weights, offspring[i], &rng_);
    for (std::size_t j = 0; j < group.children.size(); ++j) {
      if (copies[j] == 0) continue;
      Position child = group.parent;
      UndoState undo;
      child.MakeMove(group.children[j].move, &undo);
      for (int n = 0; n < copies[j]; ++n) particles_.push_back(child);
    }
  }
  std::shuffle(particles_.begin(), particles_.end(), rng_);
  report->resampled_particles = static_cast<int>(particles_.size());
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
  // The pool is laid out particle-major: every successor of hypothesis 0, then
  // every successor of hypothesis 1, and so on, and each block carries exactly
  // one unit of mass. Systematic resampling with a stride of one unit then
  // lands on the same offset inside every block -- with identical hypotheses
  // it chose the same hidden move for every particle, and the population
  // collapsed to a single guess that the next view contradicted. Visiting the
  // pool in a random order breaks that correlation while keeping the low
  // variance of the stratified draw.
  std::vector<std::size_t> order(weights.size());
  std::iota(order.begin(), order.end(), std::size_t{0});
  std::shuffle(order.begin(), order.end(), rng_);
  // Systematic resampling: one uniform draw, then evenly spaced strata. This has
  // lower variance than drawing each particle independently and is O(n).
  std::uniform_real_distribution<double> uniform(0.0, 1.0);
  const double step = total / target_count_;
  double pointer = uniform(rng_) * step;
  double cumulative = weights[order[0]];
  std::size_t index = 0;
  for (int i = 0; i < target_count_; ++i) {
    while (pointer > cumulative && index + 1 < order.size()) {
      ++index;
      cumulative += weights[order[index]];
    }
    particles_.push_back(pool[order[index]]);
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

  const Deductions facts = use_visibility_deductions_
                                ? DeduceFromObservation(view, our_side_) : Deductions{};
  Bitboard required_mask = facts.must_hold_enemy;
  if (capture_square_ >= 0 && view.IsUnseen(capture_square_)) {
    required_mask |= SquareBB(capture_square_);
  }
  if (required_mask & facts.must_be_empty) {
    report->visibility_evidence_conflict = true;
    report->capture_evidence_conflict = capture_square_ >= 0;
    // A malformed history cannot override a current visibility fact.
    required_mask &= ~facts.must_be_empty;
  }
  std::vector<int> required;
  for (Bitboard scan = required_mask; scan;) required.push_back(PopLsb(&scan));
  std::vector<int> hidden;
  for (int square = 0; square < kNumSquares; ++square) {
    if (view.IsUnseen(square) && !(facts.must_be_empty & SquareBB(square))) {
      hidden.push_back(square);
    }
  }

  // Rebuild castling rights from what the board shows: a right is possible
  // whenever the king and that rook are still on their home squares. Ours is
  // directly observable; for the opponent an unseen home square is treated as
  // still holding the rook, which is the cautious reading.
  Bitboard rebuilt_rights = own_rights_;
  for (const int color : {kWhite, kBlack}) {
    if (color == our_side_) continue;  // ours come from our own history
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
  const int64_t attempt_limit = static_cast<int64_t>(target_count_) *
                                (use_continuation_evidence_ ? 32 : 1);
  Position first_rejected;
  bool have_rejected = false;
  for (int64_t i = 0; i < attempt_limit && static_cast<int>(particles_.size()) < target_count_; ++i) {
    ++report->recovery_attempts;
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
    std::array<int, kNumPieceTypes> remaining = missing;
    Bitboard unplaced_required = required_mask;
    for (const int required_square : required) {
      unplaced_required &= ~SquareBB(required_square);
      // Jointly place capture evidence and pawn deductions. Do not spend the
      // last non-pawn on a middle rank if a required back-rank square needs it,
      // or spend the last available pawn square on a non-pawn.
      const bool pawn_square = RankOf(required_square) != 0 && RankOf(required_square) != 7;
      const int pawn_slots = static_cast<int>(std::count_if(
          available.begin(), available.end(), [](int s) { return RankOf(s) != 0 && RankOf(s) != 7; }));
      int required_back_ranks = 0;
      for (Bitboard scan = unplaced_required; scan;) {
        const int rank = RankOf(PopLsb(&scan));
        required_back_ranks += rank == 0 || rank == 7;
      }
      const int nonpawns = std::accumulate(remaining.begin() + 1, remaining.end(), 0);
      std::vector<int> types;
      for (int type = 0; type < kNumPieceTypes; ++type) {
        if (type == kPawn && !pawn_square) continue;
        // Reserving a non-pawn must not deprive a remaining pawn of its only
        // legal square. Keep the existing population-size/material invariant.
        const int pawns_left = remaining[kPawn] - (type == kPawn ? 1 : 0);
        if (pawns_left > pawn_slots - (pawn_square ? 1 : 0)) continue;
        if (nonpawns - (type != kPawn ? 1 : 0) < required_back_ranks) continue;
        for (int n = 0; n < remaining[type]; ++n) types.push_back(type);
      }
      bool latent_promotion = false;
      if (types.empty() && !pawn_square && remaining[kPawn] > 0) {
        // If only unseen pawns remain, a capturer on a last rank must have
        // promoted. Spend a pawn rather than inventing an extra enemy piece.
        latent_promotion = true;
        types = {kKnight, kBishop, kRook, kQueen};
      }
      if (!types.empty()) {
        const int type = types[std::uniform_int_distribution<std::size_t>(0, types.size() - 1)(rng_)];
        --remaining[latent_promotion ? kPawn : type];
        particle.PutPiece(required_square, enemy_side, type);
        available.erase(std::remove(available.begin(), available.end(), required_square), available.end());
      } else {
        // A contradictory synthetic observation/census can make placement
        // impossible. Keep visibility intact and expose the inconsistency.
        if (required_square == capture_square_) report->capture_evidence_conflict = true;
        if (facts.must_hold_enemy & SquareBB(required_square)) report->visibility_evidence_conflict = true;
      }
    }
    // Pawns are placed first because they are the only constrained piece: they
    // cannot stand on a promotion rank. Placing the free-roaming pieces first
    // can leave a pawn with nothing but promotion-rank squares and so drop it
    // from the rebuild, which is how a hypothesis ended up a piece short.
    // Every hidden pawn really does sit on a non-promotion fog square, so
    // satisfying the constrained type first always succeeds.
    for (const int type : {kPawn, kKnight, kBishop, kRook, kQueen, kKing}) {
      for (int placed = 0; placed < remaining[type]; ++placed) {
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
    particle.set_side_to_move(use_continuation_evidence_ && previous_mover_ >= 0
                                 ? previous_mover_ ^ 1 : our_side_);
    particle.set_castling_rights(rebuilt_rights);
    if (!ConsistentWithContinuation(particle)) {
      ++report->recovery_continuation_rejected;
      if (!have_rejected) { first_rejected = particle; have_rejected = true; }
      continue;
    }
    particles_.push_back(particle);
  }
  if (particles_.empty()) {
    // Bounded failure for malformed input or a proposal family that cannot
    // satisfy the evidence. Never report this degraded fallback as a consistent
    // posterior. Live replay gates must have zero such conflicts before release.
    report->continuation_evidence_conflict = true;
    particles_.push_back(first_rejected);
  }
  const std::size_t survivors = particles_.size();
  while (static_cast<int>(particles_.size()) < target_count_) {
    particles_.push_back(particles_[particles_.size() % survivors]);
  }
  if (capture_square_ >= 0) {
    report->capture_constraints_preserved = 0;
    for (const Position& particle : particles_) {
      report->capture_constraints_preserved += particle.color_at(capture_square_) == enemy_side;
    }
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
