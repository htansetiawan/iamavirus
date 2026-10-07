// Copyright 2026. Fog of War chess engine.

#include "search.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <utility>
#include <vector>

namespace fow {
namespace {

// Nodes between clock checks. Frequent enough to respect a tight budget,
// infrequent enough that the clock is not part of the hot loop.
constexpr uint64_t kClockCheckInterval = 2048;

constexpr int kAspirationWindow = 40;

// Late move reductions start only after this many moves have been tried at a
// node, and only for quiet moves at sufficient depth.
constexpr int kLateMoveThreshold = 4;
constexpr int kLateMoveMinDepth = 3;

// Ordering bands, kept far apart so the bands never interleave.
constexpr int kTableMoveScore = 1 << 24;
constexpr int kCaptureScoreBase = 1 << 20;
constexpr int kFirstKillerScore = 1 << 19;
constexpr int kSecondKillerScore = kFirstKillerScore - 1;

}  // namespace

void Searcher::SetContext(int our_side, bool enemy_king_confirmed,
                          const FogContext& fog) {
  our_side_ = our_side;
  win_magnitude_ =
      enemy_king_confirmed ? kWinConfirmed : options_.speculative_win_score;
  fog_ = fog;
  killers_ = {};
  for (auto& by_from : history_) {
    for (auto& by_to : by_from) by_to.fill(0);
  }
}

inline bool Searcher::OutOfTime() {
  if (stopped_) return true;
  if ((nodes_ & (kClockCheckInterval - 1)) != 0) return false;
  if (std::chrono::steady_clock::now() >= deadline_) stopped_ = true;
  return stopped_;
}

bool Searcher::TerminalScore(const Position& position, int ply,
                             int* score) const {
  if (!position.PreviousMoverIsLost()) return false;
  // The side to move has already won, because its opponent's last move left a
  // capturable king. Scores are from the side to move's point of view.
  const int magnitude =
      position.side_to_move() == our_side_ ? win_magnitude_ : kLossMagnitude;
  *score = magnitude - ply;
  return true;
}

int Searcher::CaptureGain(const Position& position, Move move) const {
  const int victim = position.piece_at(MoveTo(move));
  const int attacker = position.piece_at(MoveFrom(move));
  // An en passant capture has no piece on the destination square.
  int gain = victim != kNoPiece ? kPieceValue[victim] : kPieceValue[kPawn];
  if (attacker != kNoPiece) gain -= kPieceValue[attacker] / 10;
  if (IsPromotion(move)) gain += kPieceValue[PromotionType(move)];
  return gain;
}

void Searcher::ScoreMoves(const Position& position, MoveList* moves,
                          Move table_move, int ply,
                          std::array<int, MoveList::kCapacity>* scores) const {
  const std::array<Move, 2>& killers =
      killers_[ply < kMaxPly ? ply : kMaxPly - 1];
  const int side = position.side_to_move();
  for (int i = 0; i < moves->size(); ++i) {
    const Move move = (*moves)[i];
    if (move == table_move) {
      (*scores)[i] = kTableMoveScore;
    } else if (position.piece_at(MoveTo(move)) != kNoPiece ||
               MoveFlagOf(move) == kFlagEnPassant || IsPromotion(move)) {
      (*scores)[i] = kCaptureScoreBase + CaptureGain(position, move);
    } else if (move == killers[0]) {
      (*scores)[i] = kFirstKillerScore;
    } else if (move == killers[1]) {
      (*scores)[i] = kSecondKillerScore;
    } else {
      (*scores)[i] = history_[side][MoveFrom(move)][MoveTo(move)];
    }
  }
}

void Searcher::SelectNext(MoveList* moves,
                          std::array<int, MoveList::kCapacity>* scores,
                          int index) {
  int best = index;
  for (int i = index + 1; i < moves->size(); ++i) {
    if ((*scores)[i] > (*scores)[best]) best = i;
  }
  if (best != index) {
    std::swap((*moves)[index], (*moves)[best]);
    std::swap((*scores)[index], (*scores)[best]);
  }
}

void Searcher::RecordCutoff(const Position& position, Move move, int depth,
                            int ply) {
  if (position.piece_at(MoveTo(move)) != kNoPiece || IsPromotion(move)) return;
  if (ply < kMaxPly) {
    std::array<Move, 2>& killers = killers_[ply];
    if (killers[0] != move) {
      killers[1] = killers[0];
      killers[0] = move;
    }
  }
  int32_t& entry =
      history_[position.side_to_move()][MoveFrom(move)][MoveTo(move)];
  entry += depth * depth;
  // Keep history bounded so old information cannot dominate ordering forever.
  if (entry > (1 << 18)) {
    for (auto& by_from : history_) {
      for (auto& by_to : by_from) {
        for (int32_t& value : by_to) value /= 2;
      }
    }
  }
}

int Searcher::Quiescence(Position* position, int alpha, int beta, int ply) {
  ++nodes_;
  if (OutOfTime()) return 0;

  int decided = 0;
  if (TerminalScore(*position, ply, &decided)) return decided;
  if (ply >= kMaxPly) return Evaluate(*position, position->side_to_move(), fog_);

  const int standing = Evaluate(*position, position->side_to_move(), fog_);
  if (standing >= beta) return standing;
  if (standing > alpha) alpha = standing;

  MoveList captures;
  position->GenerateCaptures(&captures);
  std::array<int, MoveList::kCapacity> scores{};
  for (int i = 0; i < captures.size(); ++i) {
    scores[i] = CaptureGain(*position, captures[i]);
  }

  int best = standing;
  for (int i = 0; i < captures.size(); ++i) {
    SelectNext(&captures, &scores, i);
    const Move move = captures[i];
    UndoState undo;
    position->MakeMove(move, &undo);
    const int score = -Quiescence(position, -beta, -alpha, ply + 1);
    position->UnmakeMove(move, undo);
    if (stopped_) return 0;
    if (score > best) best = score;
    if (score > alpha) alpha = score;
    if (alpha >= beta) break;
  }
  return best;
}

int Searcher::Negamax(Position* position, int depth, int alpha, int beta,
                      int ply) {
  ++nodes_;
  if (OutOfTime()) return 0;

  int decided = 0;
  if (TerminalScore(*position, ply, &decided)) return decided;
  if (ply >= kMaxPly) return Evaluate(*position, position->side_to_move(), fog_);

  // Mate distance pruning: a win found at this ply cannot be improved on by a
  // longer line, so narrow the window before doing any work.
  alpha = std::max(alpha, -kLossMagnitude + ply);
  beta = std::min(beta, win_magnitude_ - ply);
  if (alpha >= beta) return alpha;

  if (depth <= 0) return Quiescence(position, alpha, beta, ply);

  Move table_move = kNullMove;
  int table_score = 0;
  bool usable = false;
  if (table_->Probe(position->key(), depth, alpha, beta, ply, &table_score,
                    &table_move, &usable) &&
      usable && ply > 0) {
    return table_score;
  }

  MoveList moves;
  position->GenerateMoves(&moves);
  if (moves.empty()) {
    // Having no legal move at all is a loss under the course rules.
    const int magnitude =
        position->side_to_move() == our_side_ ? kLossMagnitude : win_magnitude_;
    return -magnitude + ply;
  }

  std::array<int, MoveList::kCapacity> scores{};
  ScoreMoves(*position, &moves, table_move, ply, &scores);

  const int original_alpha = alpha;
  int best_score = -kInfinity;
  Move best_move = kNullMove;

  for (int i = 0; i < moves.size(); ++i) {
    SelectNext(&moves, &scores, i);
    const Move move = moves[i];
    const bool quiet = position->piece_at(MoveTo(move)) == kNoPiece &&
                       !IsPromotion(move) &&
                       MoveFlagOf(move) != kFlagEnPassant;

    UndoState undo;
    position->MakeMove(move, &undo);

    int score;
    int reduction = 0;
    if (options_.use_late_move_reductions && quiet && depth >= kLateMoveMinDepth &&
        i >= kLateMoveThreshold) {
      // Late quiet moves are searched shallower first. The terminal test runs at
      // every node regardless, so a reduced search still notices an immediately
      // capturable king; only deeper hunts could be missed, and those are
      // recovered by the re-search below.
      reduction = 1;
    }
    if (reduction > 0) {
      score = -Negamax(position, depth - 1 - reduction, -alpha - 1, -alpha,
                       ply + 1);
      if (score > alpha) {
        score = -Negamax(position, depth - 1, -beta, -alpha, ply + 1);
      }
    } else {
      score = -Negamax(position, depth - 1, -beta, -alpha, ply + 1);
    }

    position->UnmakeMove(move, undo);
    if (stopped_) return 0;

    if (score > best_score) {
      best_score = score;
      best_move = move;
    }
    if (score > alpha) alpha = score;
    if (alpha >= beta) {
      RecordCutoff(*position, move, depth, ply);
      break;
    }
  }

  const BoundType bound = best_score >= beta      ? kBoundLower
                          : best_score <= original_alpha ? kBoundUpper
                                                         : kBoundExact;
  table_->Store(position->key(), depth, best_score, bound, best_move, ply);
  return best_score;
}

SearchResult Searcher::Search(Position* root, const MoveList& root_moves,
                              const SearchLimits& limits) {
  SearchResult result;
  if (root_moves.empty()) {
    result.score = -kLossMagnitude;
    return result;
  }

  deadline_ = std::chrono::steady_clock::now() +
              std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                  std::chrono::duration<double>(limits.seconds));
  nodes_ = 0;
  stopped_ = false;
  table_->NewGeneration();

  // Working order, improved after each completed iteration.
  std::vector<Move> order(root_moves.begin(), root_moves.end());
  result.best_move = order.front();

  int previous_score = 0;
  for (int depth = 1; depth <= limits.max_depth; ++depth) {
    int alpha = -kInfinity;
    int beta = kInfinity;
    if (options_.use_aspiration_windows && depth >= 3) {
      alpha = previous_score - kAspirationWindow;
      beta = previous_score + kAspirationWindow;
    }

    std::vector<RootMoveValue> values;
    Move iteration_best = kNullMove;
    int iteration_score = -kInfinity;
    bool researched = false;

    for (;;) {
      values.clear();
      iteration_best = kNullMove;
      iteration_score = -kInfinity;
      int window_alpha = alpha;

      for (const Move move : order) {
        UndoState undo;
        root->MakeMove(move, &undo);
        const int score =
            -Negamax(root, depth - 1, -beta, -window_alpha, 1);
        root->UnmakeMove(move, undo);
        if (stopped_) break;
        values.push_back({move, score});
        if (score > iteration_score) {
          iteration_score = score;
          iteration_best = move;
          if (score > window_alpha) window_alpha = score;
        }
      }
      if (stopped_) break;

      // An aspiration window that failed tells us nothing; widen and redo.
      const bool failed_low = iteration_score <= alpha;
      const bool failed_high = iteration_score >= beta;
      if ((failed_low || failed_high) && !researched &&
          options_.use_aspiration_windows && depth >= 3) {
        alpha = -kInfinity;
        beta = kInfinity;
        researched = true;
        continue;
      }
      break;
    }

    if (stopped_) {
      // Scores from different depths are not comparable, so a partial iteration
      // counts only when a later move genuinely overtook the move this same
      // iteration began with -- that is a real improvement at the new depth.
      if (iteration_best != kNullMove && iteration_best != order.front()) {
        result.best_move = iteration_best;
        result.score = iteration_score;
        result.root_values = values;
      }
      break;
    }

    result.best_move = iteration_best;
    result.score = iteration_score;
    result.depth = depth;
    result.root_values = values;
    previous_score = iteration_score;

    // Best first next time; stable so equal scores keep their relative order.
    std::stable_sort(values.begin(), values.end(),
                     [](const RootMoveValue& a, const RootMoveValue& b) {
                       return a.score > b.score;
                     });
    order.clear();
    for (const RootMoveValue& entry : values) order.push_back(entry.move);

    if (std::abs(result.score) >= options_.speculative_win_score - kMaxPly) {
      break;
    }
    if (std::chrono::steady_clock::now() >= deadline_) break;
  }

  result.nodes = nodes_;
  return result;
}

}  // namespace fow
