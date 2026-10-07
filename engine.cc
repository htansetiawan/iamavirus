// Copyright 2026. Fog of War chess engine.

#include "engine.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <random>
#include <vector>

#include "evaluation.h"
#include "regret.h"

namespace fow {
namespace {

// Share of the move's budget spent shortlisting, the rest going to the matrix
// game. The shortlist search is what sets the depth we report, so it gets the
// larger slice.
constexpr double kShortlistShare = 0.45;

// An extra reward, in centipawns, for a position where our move attacks the
// enemy king with a piece that the opponent cannot see.
//
// Invisibility implies safety here, which is why this is worth so much: if they
// could capture our attacker, its square would be the destination of one of
// their moves and therefore visible to them. So an unseen attacker cannot be
// taken, and with no check announcement they have no reason to move the king.
constexpr double kInvisibleKingAttackBonus = 500.0;
constexpr double kVisibleKingAttackBonus = 40.0;

// Score standing in for "this move loses on the spot", used when a move cannot
// legally be made in a hypothesis or leaves our king capturable in it.
constexpr double kDisasterScore = -static_cast<double>(kLossMagnitude);

bool ListContains(const MoveList& list, Move move) {
  for (const Move candidate : list) {
    if (candidate == move) return true;
  }
  return false;
}

}  // namespace

Engine::Engine(int our_side, double base_seconds, double increment_seconds,
               const EngineOptions& options, uint64_t seed)
    : our_side_(our_side),
      increment_(increment_seconds),
      options_(options),
      rng_(seed),
      belief_(our_side, options.particle_count, seed ^ 0x9E3779B97F4A7C15ULL),
      searcher_(&table_) {
  (void)base_seconds;
  table_.Resize(options.transposition_megabytes);
  searcher_.set_options(options.search);
}

double Engine::TimeBudget(double remaining_seconds) const {
  // Spend roughly the increment per move in the steady state, with a reserve so
  // a long game cannot run the clock out. The cap keeps an early position from
  // eating base time that later moves will need.
  const double spare = remaining_seconds - options_.time_reserve;
  if (spare <= 0.5) {
    return std::max(0.02, std::max(0.0, remaining_seconds) * 0.15);
  }
  const double target =
      spare / options_.time_divisor + increment_ * options_.increment_share;
  return std::max(0.05, std::min({target, options_.time_cap, spare * 0.5}));
}

void Engine::Observe(const Observation& view, bool reflects_our_own_move) {
  belief_.Observe(view, reflects_our_own_move);
  previous_view_ = view;
  have_previous_ = true;
}

void Engine::NotifyMovePlayed(Move move) { belief_.ApplyOurMove(move); }

Bitboard Engine::OurCastlingRights() const {
  // Position::MakeMove already clears a right when the king or rook moves, so
  // the believed state is the record. Masking to our own pieces keeps the
  // opponent's rights, which are only a guess, out of our legal move list.
  const Position& reference = belief_.Representative();
  return reference.castling_rights() & reference.pieces_of(our_side_);
}

Move Engine::ChooseMove(const Observation& view, double remaining_seconds,
                        DecisionTrace* trace) {
  const int enemy_side = our_side_ ^ 1;
  const int en_passant =
      InferEnPassant(have_previous_ ? &previous_view_ : nullptr, view, our_side_);

  Position visible;
  VisiblePositionFromObservation(view, our_side_, OurCastlingRights(),
                                 en_passant, &visible);
  MoveList legal;
  LegalMovesFromObservation(visible, view, &legal);

  trace->legal_moves = legal.size();
  trace->unseen_squares = PopCount(view.UnseenMask());
  trace->budget = TimeBudget(remaining_seconds);
  if (legal.empty()) return kNullMove;
  if (legal.size() == 1) {
    trace->shortlisted = 1;
    return legal[0];
  }

  const FogContext fog = belief_.MakeFogContext(view);
  searcher_.SetContext(our_side_, belief_.EnemyKingVisible(view), fog);

  // Step one: a full search of the likeliest hypothesis, to shortlist.
  Position likely = belief_.Representative();
  likely.set_side_to_move(our_side_);
  likely.set_en_passant_square(en_passant);
  SearchLimits shortlist_limits;
  shortlist_limits.seconds = trace->budget * kShortlistShare;
  const SearchResult primary =
      searcher_.Search(&likely, legal, shortlist_limits);
  trace->depth = primary.depth;
  trace->score = primary.score;
  trace->nodes = primary.nodes;

  std::vector<RootMoveValue> ranked = primary.root_values;
  if (ranked.empty()) {
    for (const Move move : legal) ranked.push_back({move, 0});
  }
  std::stable_sort(ranked.begin(), ranked.end(),
                   [](const RootMoveValue& a, const RootMoveValue& b) {
                     return a.score > b.score;
                   });
  const int shortlist =
      std::min<int>(options_.shortlist_size, static_cast<int>(ranked.size()));
  ranked.resize(shortlist);
  trace->shortlisted = shortlist;

  if (!options_.use_matrix_game || shortlist == 1) {
    return ranked.front().move;
  }

  // Step two: fill the payoff matrix by searching each shortlisted move against
  // each hypothesis.
  const std::vector<const Position*> hypotheses =
      belief_.Sample(options_.hypothesis_count);
  const int columns = static_cast<int>(hypotheses.size());
  trace->hypotheses = columns;

  MatrixGame game;
  game.rows = shortlist;
  game.columns = columns;
  game.payoff.assign(static_cast<std::size_t>(shortlist) * columns, 0.0);

  std::vector<int> king_losses(shortlist, 0);
  const double cell_budget =
      std::max(0.004, trace->budget * (1.0 - kShortlistShare) /
                          std::max(1, shortlist * columns));

  for (int column = 0; column < columns; ++column) {
    for (int row = 0; row < shortlist; ++row) {
      const Move move = ranked[row].move;
      Position hypothesis = *hypotheses[column];
      hypothesis.set_side_to_move(our_side_);
      hypothesis.set_en_passant_square(en_passant);

      MoveList available;
      hypothesis.GenerateMoves(&available);
      if (!ListContains(available, move)) {
        // The move cannot be made in this hypothesis, which only happens when a
        // rebuilt hypothesis disagrees about castling rights. Treat it as lost
        // rather than silently corrupting the board.
        game.set(row, column, kDisasterScore);
        ++king_losses[row];
        continue;
      }

      UndoState undo;
      hypothesis.MakeMove(move, &undo);
      // If our king is capturable now, this move loses in this hypothesis.
      const int our_king = hypothesis.KingSquare(our_side_);
      const bool fatal =
          our_king < 0 || hypothesis.IsAttacked(our_king, enemy_side);
      double bonus = 0.0;
      if (!fatal) {
        const int target = hypothesis.KingSquare(enemy_side);
        if (target >= 0) {
          const Bitboard seen_by_them = VisibleSquares(hypothesis, enemy_side);
          Bitboard attackers = hypothesis.AttackersTo(target, our_side_);
          while (attackers) {
            const int from = PopLsb(&attackers);
            bonus += (seen_by_them & SquareBB(from)) ? kVisibleKingAttackBonus
                                                    : kInvisibleKingAttackBonus;
          }
        }
      }
      hypothesis.UnmakeMove(move, undo);

      if (fatal) {
        game.set(row, column, kDisasterScore);
        ++king_losses[row];
        continue;
      }

      Position root = *hypotheses[column];
      root.set_side_to_move(our_side_);
      root.set_en_passant_square(en_passant);
      MoveList single;
      single.Add(move);
      SearchLimits limits;
      limits.seconds = cell_budget;
      const SearchResult result = searcher_.Search(&root, single, limits);
      trace->nodes += result.nodes;
      game.set(row, column, static_cast<double>(result.score) + bonus);
    }
  }

  // Step three: discard moves that lose our king too often, then solve.
  std::vector<int> safe_rows;
  for (int row = 0; row < shortlist; ++row) {
    const double share = static_cast<double>(king_losses[row]) / columns;
    if (share <= options_.king_loss_tolerance) safe_rows.push_back(row);
  }
  trace->rejected_unsafe = shortlist - static_cast<int>(safe_rows.size());
  if (safe_rows.empty()) {
    // Every candidate is dangerous somewhere; fall back on the search's verdict.
    return ranked.front().move;
  }

  MatrixGame reduced;
  reduced.rows = static_cast<int>(safe_rows.size());
  reduced.columns = columns;
  reduced.payoff.assign(static_cast<std::size_t>(reduced.rows) * columns, 0.0);
  for (int row = 0; row < reduced.rows; ++row) {
    for (int column = 0; column < columns; ++column) {
      reduced.set(row, column, game.at(safe_rows[row], column));
    }
  }

  const MixedStrategy solution =
      SolveMatrixGame(reduced, options_.regret_iterations);
  trace->game_value = solution.value;

  // Step four: sample from the equilibrium mixture. Playing the mixture rather
  // than its most likely action is the point: it hedges across hypotheses we
  // cannot distinguish and leaves a repeat opponent nothing to predict.
  std::uniform_real_distribution<double> uniform(0.0, 1.0);
  double draw = uniform(rng_);
  int picked = 0;
  for (int row = 0; row < reduced.rows; ++row) {
    draw -= solution.row_probability[row];
    if (draw <= 0.0) {
      picked = row;
      break;
    }
    picked = row;
  }
  trace->chosen_probability = solution.row_probability[picked];
  return ranked[safe_rows[picked]].move;
}

}  // namespace fow
