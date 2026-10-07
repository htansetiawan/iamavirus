// Copyright 2026. Fog of War chess engine.

#include "engine.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstddef>
#include <cstdint>
#include <random>
#include <string>
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

// Value of the piece standing on `square`, or zero for an empty square.
int ValueAt(const Position& position, int square) {
  const int piece = position.piece_at(square);
  return piece == kNoPiece ? 0 : kPieceValue[piece];
}

bool ListContains(const MoveList& list, Move move) {
  for (const Move candidate : list) {
    if (candidate == move) return true;
  }
  return false;
}

}  // namespace

// Expected material handed over by a move, judged across every hypothesis.
//
// The sampled columns of the matrix game cannot see a danger that only a small
// share of hypotheses contain: with eight columns, a threat present in one
// hypothesis in twenty is usually absent from all of them. That is exactly how
// three rated games were lost -- a queen captured by a knight that no sampled
// hypothesis had placed on the board. This scans the whole population instead,
// which is affordable because it needs no search: one attack test per hypothesis.
//
// The exchange is evaluated one capture deep. If the opponent can take on the
// destination square, they will use their cheapest attacker; we recapture if we
// can. What is left over, when it is a loss, is averaged over the population.
double Engine::ExpectedMaterialRisk(Move move, int en_passant) const {
  const std::vector<Position>& population = belief_.particles();
  if (population.empty()) return 0.0;
  const int enemy_side = our_side_ ^ 1;
  const int to = MoveTo(move);

  double total_loss = 0.0;
  int counted = 0;
  for (Position hypothesis : population) {
    hypothesis.set_side_to_move(our_side_);
    hypothesis.set_en_passant_square(en_passant);
    if (IsCastle(move)) {
      // Only castling can be illegal in a hypothesis, when a rebuilt one
      // disagrees about rights.
      MoveList available;
      hypothesis.GenerateMoves(&available);
      if (!ListContains(available, move)) continue;
    }
    const int gained = MoveFlagOf(move) == kFlagEnPassant ? kPieceValue[kPawn]
                                                        : ValueAt(hypothesis, to);
    UndoState undo;
    hypothesis.MakeMove(move, &undo);
    ++counted;

    const Bitboard attackers = hypothesis.AttackersTo(to, enemy_side);
    if (attackers != 0) {
      // Cheapest attacker: the one they would actually use.
      int cheapest = kPieceValue[kQueen] + 1;
      Bitboard scan = attackers;
      while (scan) {
        const int value = kPieceValue[hypothesis.piece_at(PopLsb(&scan))];
        if (value < cheapest) cheapest = value;
      }
      const int exposed = kPieceValue[hypothesis.piece_at(to)];
      const bool can_recapture =
          hypothesis.AttackersTo(to, our_side_) != 0;
      const int net = gained + (can_recapture ? cheapest : 0) - exposed;
      if (net < 0) total_loss += -net;
    }
    hypothesis.UnmakeMove(move, undo);
  }
  return counted > 0 ? total_loss / counted : 0.0;
}

namespace {

// Reads an override, leaving the default in place when the variable is absent or
// unparseable. A malformed value is reported rather than ignored silently.
template <typename T>
void Override(const char* name, T* value) {
  const char* text = std::getenv(name);
  if (text == nullptr || *text == '\0') return;
  char* end = nullptr;
  const double parsed = std::strtod(text, &end);
  if (end == text || (end != nullptr && *end != '\0')) {
    std::fprintf(stderr, "ignoring malformed %s=%s\n", name, text);
    return;
  }
  *value = static_cast<T>(parsed);
}

void OverrideFlag(const char* name, bool* value) {
  const char* text = std::getenv(name);
  if (text == nullptr || *text == '\0') return;
  *value = !(text[0] == '0' || text[0] == 'n' || text[0] == 'f');
}

}  // namespace

const char* EngineModeName(EngineMode mode) {
  switch (mode) {
    case EngineMode::kNeural: return "neural";
    case EngineMode::kHybrid: return "hybrid";
    default: return "cpp";
  }
}

EngineOptions EngineOptionsFromEnvironment() {
  EngineOptions options;
  if (const char* mode = std::getenv("FOW_MODE")) {
    const std::string text(mode);
    if (text == "neural") options.mode = EngineMode::kNeural;
    else if (text == "hybrid") options.mode = EngineMode::kHybrid;
    else if (text == "cpp" || text.empty()) options.mode = EngineMode::kCpp;
    else std::fprintf(stderr, "ignoring unknown FOW_MODE=%s\n", mode);
  }
  Override("FOW_HYBRID_POLICY_TOP", &options.hybrid_policy_top);
  Override("FOW_HYBRID_SEARCH_TOP", &options.hybrid_search_top);
  Override("FOW_HYBRID_RISK_TOP", &options.hybrid_risk_top);
  Override("FOW_HYBRID_MAX_ROWS", &options.hybrid_max_rows);
  Override("FOW_NEURAL_TEMPERATURE", &options.neural_temperature);
  Override("FOW_PARTICLES", &options.particle_count);
  Override("FOW_SHORTLIST", &options.shortlist_size);
  Override("FOW_HYPOTHESES", &options.hypothesis_count);
  Override("FOW_REGRET_ITERATIONS", &options.regret_iterations);
  OverrideFlag("FOW_MATRIX_GAME", &options.use_matrix_game);
  Override("FOW_KING_LOSS_TOLERANCE", &options.king_loss_tolerance);
  Override("FOW_KING_RISK_PRICE", &options.king_risk_price);
  Override("FOW_PIECE_RISK", &options.piece_risk_weight);
  Override("FOW_TIME_CAP", &options.time_cap);
  Override("FOW_TIME_RESERVE", &options.time_reserve);
  Override("FOW_TIME_DIVISOR", &options.time_divisor);
  Override("FOW_HASH_MB", &options.transposition_megabytes);
  Override("FOW_NODE_BUDGET", &options.node_budget);
  OverrideFlag("FOW_OPPONENT_PRIOR", &options.use_opponent_prior);
  Override("FOW_SPECULATIVE_WIN", &options.search.speculative_win_score);
  OverrideFlag("FOW_LMR", &options.search.use_late_move_reductions);
  OverrideFlag("FOW_ASPIRATION", &options.search.use_aspiration_windows);
  // Guard against a value that would break the engine rather than tune it.
  if (options.particle_count < 1) options.particle_count = 1;
  if (options.shortlist_size < 1) options.shortlist_size = 1;
  if (options.hypothesis_count < 1) options.hypothesis_count = 1;
  if (options.transposition_megabytes < 1) options.transposition_megabytes = 1;
  if (options.hybrid_max_rows < 1) options.hybrid_max_rows = 1;
  if (options.neural_temperature <= 0.0) options.neural_temperature = 1.0;
  return options;
}

namespace {

// Index of `move` in `advice.moves`, or -1.
int AdviceIndex(const NeuralAdvice& advice, Move move) {
  for (std::size_t i = 0; i < advice.moves.size(); ++i) {
    if (advice.moves[i] == move) return static_cast<int>(i);
  }
  return -1;
}

}  // namespace

Move Engine::SampleNeural(const MoveList& legal, const NeuralAdvice& advice,
                          DecisionTrace* trace) {
  // Probabilities for the legal moves only, renormalised; a legal move the
  // adapter did not score gets nothing, which can only happen if the two
  // candidate derivations disagree -- and that is logged by the caller.
  std::vector<double> weights(static_cast<std::size_t>(legal.size()), 0.0);
  double total = 0.0;
  for (int i = 0; i < legal.size(); ++i) {
    const int at = AdviceIndex(advice, legal[i]);
    if (at < 0) continue;
    double p = advice.policy[static_cast<std::size_t>(at)];
    if (options_.neural_temperature != 1.0) {
      p = std::pow(std::max(p, 1e-12), 1.0 / options_.neural_temperature);
    }
    weights[static_cast<std::size_t>(i)] = p;
    total += p;
  }
  if (total <= 0.0) return kNullMove;
  std::uniform_real_distribution<double> uniform(0.0, 1.0);
  double draw = uniform(rng_) * total;
  int picked = legal.size() - 1;
  for (int i = 0; i < legal.size(); ++i) {
    draw -= weights[static_cast<std::size_t>(i)];
    if (draw <= 0.0) {
      picked = i;
      break;
    }
  }
  trace->chosen_probability = weights[static_cast<std::size_t>(picked)] / total;
  trace->mode_used = EngineMode::kNeural;
  return legal[picked];
}

std::vector<double> Engine::KingLossProbabilities(const MoveList& moves,
                                                 int en_passant) const {
  std::vector<double> probability(static_cast<std::size_t>(moves.size()), 0.0);
  const std::vector<Position>& population = belief_.particles();
  if (population.empty()) return probability;
  const int enemy_side = our_side_ ^ 1;

  std::vector<int> losses(static_cast<std::size_t>(moves.size()), 0);
  std::vector<int> counted(static_cast<std::size_t>(moves.size()), 0);
  // Hypothesis outside, move inside: each hypothesis is copied once and every
  // candidate is tested on it with a make, one attack test and an unmake.
  for (Position hypothesis : population) {
    hypothesis.set_side_to_move(our_side_);
    hypothesis.set_en_passant_square(en_passant);
    MoveList available;
    hypothesis.GenerateMoves(&available);
    for (int i = 0; i < moves.size(); ++i) {
      if (!ListContains(available, moves[i])) continue;
      UndoState undo;
      hypothesis.MakeMove(moves[i], &undo);
      const int king = hypothesis.KingSquare(our_side_);
      if (king < 0 || hypothesis.IsAttacked(king, enemy_side)) {
        ++losses[static_cast<std::size_t>(i)];
      }
      hypothesis.UnmakeMove(moves[i], undo);
      ++counted[static_cast<std::size_t>(i)];
    }
  }
  for (int i = 0; i < moves.size(); ++i) {
    const std::size_t index = static_cast<std::size_t>(i);
    probability[index] = counted[index] > 0
        ? static_cast<double>(losses[index]) / counted[index]
        : 1.0;  // a move no hypothesis can make is treated as unavailable
  }
  return probability;
}

Engine::Engine(int our_side, double base_seconds, double increment_seconds,
               const EngineOptions& options, uint64_t seed)
    : our_side_(our_side),
      increment_(increment_seconds),
      options_(options),
      rng_(seed),
      belief_(our_side, options.particle_count, seed ^ 0x9E3779B97F4A7C15ULL,
              options.use_opponent_prior),
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
  before_latest_view_ = latest_view_;
  latest_view_ = view;
  ++views_seen_;
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
                        DecisionTrace* trace, const NeuralAdvice* advice) {
  // One deadline for the whole turn. The matrix game runs dozens of small
  // searches, and each one overshoots its own slice slightly by finishing an
  // iteration; summed over forty-eight cells that was half a second past the
  // budget, which in a long game is how a bot flags. Individual slices are still
  // used to pace the work, but this is what actually stops it.
  const auto turn_start = std::chrono::steady_clock::now();
  const int enemy_side = our_side_ ^ 1;
  const bool advised = advice != nullptr && advice->available;
  if (advised) trace->neural_value = advice->value;
  trace->mode_used = EngineMode::kCpp;
  // The view before the latest one is the one taken after our own move, so the
  // pair spans exactly the opponent's move. At White's first decision there is
  // no earlier view and nothing to infer.
  const int en_passant = InferEnPassant(
      views_seen_ >= 2 ? &before_latest_view_ : nullptr, view, our_side_);

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

  // King safety is decided here, over every legal move and the whole population,
  // before any shortlist exists. Doing it after the shortlist means a move that
  // is the only safe reply can be discarded by a search of one guessed board and
  // never considered again.
  const std::vector<double> king_risk = KingLossProbabilities(legal, en_passant);
  // Records the chosen move's own risk, whichever path returns it. Without this
  // the early returns left the field at zero, which reads as "perfectly safe".
  const auto note_choice = [&](Move chosen) {
    for (int i = 0; i < legal.size(); ++i) {
      if (legal[i] == chosen) {
        trace->king_risk_permille =
            static_cast<int>(king_risk[static_cast<std::size_t>(i)] * 1000.0);
        return chosen;
      }
    }
    return chosen;
  };
  // Compact per-candidate estimates for the log: the leading moves by policy
  // (or by particle risk without advice), each with policy, neural danger and
  // particle king-loss probability, kept as separate numbers on purpose.
  {
    std::vector<int> order(static_cast<std::size_t>(legal.size()));
    for (int i = 0; i < legal.size(); ++i) order[static_cast<std::size_t>(i)] = i;
    auto policy_of = [&](int i) {
      if (!advised) return 0.0;
      const int at = AdviceIndex(*advice, legal[i]);
      return at < 0 ? 0.0 : advice->policy[static_cast<std::size_t>(at)];
    };
    auto danger_of = [&](int i) {
      if (!advised) return 0.0;
      const int at = AdviceIndex(*advice, legal[i]);
      return at < 0 ? 0.0 : advice->danger[static_cast<std::size_t>(at)];
    };
    std::stable_sort(order.begin(), order.end(), [&](int a, int b) {
      if (advised) return policy_of(a) > policy_of(b);
      return king_risk[static_cast<std::size_t>(a)] < king_risk[static_cast<std::size_t>(b)];
    });
    char buffer[64];
    for (std::size_t k = 0; k < order.size() && k < 5; ++k) {
      const int i = order[k];
      std::snprintf(buffer, sizeof(buffer), "%s%s:%.2f/%.2f/%.2f",
                    k > 0 ? "," : "", MoveToUci(legal[i]).c_str(), policy_of(i),
                    danger_of(i), king_risk[static_cast<std::size_t>(i)]);
      trace->candidates += buffer;
    }
    if (advised) {
      for (const Move move : legal) {
        if (AdviceIndex(*advice, move) < 0) {
          trace->candidates += ",unscored:" + MoveToUci(move);
          break;
        }
      }
    }
  }

  if (advised && options_.mode == EngineMode::kNeural) {
    const Move sampled = SampleNeural(legal, *advice, trace);
    if (sampled != kNullMove) {
      const int at = AdviceIndex(*advice, sampled);
      trace->chosen_policy = at < 0 ? 0.0 : advice->policy[static_cast<std::size_t>(at)];
      trace->chosen_danger = at < 0 ? 0.0 : advice->danger[static_cast<std::size_t>(at)];
      trace->shortlisted = legal.size();
      return note_choice(sampled);
    }
  }

  MoveList safe;
  double lowest = 2.0;
  int safest = 0;
  (void)safest;
  for (int i = 0; i < legal.size(); ++i) {
    const double risk = king_risk[static_cast<std::size_t>(i)];
    if (risk < options_.king_loss_tolerance) safe.Add(legal[i]);
    if (risk < lowest) {
      lowest = risk;
      safest = i;
    }
  }
  trace->rejected_unsafe = legal.size() - safe.size();
  trace->safest_risk_permille = static_cast<int>(lowest * 1000.0);
  if (safe.empty()) {
    // Every move carries real risk. Keep them all and let the price below decide;
    // discarding on a threshold here is what previously let the fatal move back
    // in through a fallback.
    trace->forced_risky = true;
    for (int i = 0; i < legal.size(); ++i) safe.Add(legal[i]);
    trace->rejected_unsafe = 0;
  }
  // Risk of each surviving move, indexed alongside `safe`, so the payoff can be
  // charged for it.
  std::vector<double> safe_risk;
  safe_risk.reserve(static_cast<std::size_t>(safe.size()));
  for (int i = 0; i < safe.size(); ++i) {
    for (int j = 0; j < legal.size(); ++j) {
      if (legal[j] == safe[i]) {
        safe_risk.push_back(king_risk[static_cast<std::size_t>(j)]);
        break;
      }
    }
  }

  const FogContext fog = belief_.MakeFogContext(view);
  searcher_.SetContext(our_side_, belief_.EnemyKingVisible(view), fog);

  // Step one: a full search of the likeliest hypothesis, to shortlist.
  Position likely = belief_.Representative();
  likely.set_side_to_move(our_side_);
  likely.set_en_passant_square(en_passant);
  SearchLimits shortlist_limits;
  shortlist_limits.seconds = trace->budget * kShortlistShare;
  if (options_.node_budget > 0) {
    // Measurement mode: bound by nodes, with a generous clock as a safety net.
    shortlist_limits.seconds = 600.0;
    shortlist_limits.max_nodes =
        static_cast<uint64_t>(options_.node_budget * kShortlistShare);
  }
  const SearchResult primary =
      searcher_.Search(&likely, safe, shortlist_limits);
  trace->depth = primary.depth;
  trace->score = primary.score;
  trace->nodes = primary.nodes;

  std::vector<RootMoveValue> ranked = primary.root_values;
  if (ranked.empty()) {
    for (const Move move : safe) ranked.push_back({move, 0});
  }
  std::stable_sort(ranked.begin(), ranked.end(),
                   [](const RootMoveValue& a, const RootMoveValue& b) {
                     return a.score > b.score;
                   });
  int shortlist =
      std::min<int>(options_.shortlist_size, static_cast<int>(ranked.size()));
  if (advised && options_.mode == EngineMode::kHybrid) {
    // The union of the search's own top moves, the policy's top moves and the
    // lowest particle-risk moves, so that a single representative board can
    // never eliminate every defensive option. Trimmed to the affordable row
    // count in that priority order; neural danger only breaks ties here.
    trace->mode_used = EngineMode::kHybrid;
    std::vector<RootMoveValue> chosen;
    auto add = [&](Move move) {
      for (const RootMoveValue& row : chosen) {
        if (row.move == move) return;
      }
      if (static_cast<int>(chosen.size()) >= options_.hybrid_max_rows) return;
      for (const RootMoveValue& row : ranked) {
        if (row.move == move) {
          chosen.push_back(row);
          return;
        }
      }
    };
    const int search_top = std::min<int>(options_.hybrid_search_top,
                                         static_cast<int>(ranked.size()));
    for (int i = 0; i < search_top; ++i) add(ranked[static_cast<std::size_t>(i)].move);
    std::vector<int> by_policy;
    for (int i = 0; i < safe.size(); ++i) by_policy.push_back(i);
    auto policy_of = [&](int i) {
      const int at = AdviceIndex(*advice, safe[i]);
      return at < 0 ? -1.0 : advice->policy[static_cast<std::size_t>(at)];
    };
    std::stable_sort(by_policy.begin(), by_policy.end(),
                     [&](int a, int b) { return policy_of(a) > policy_of(b); });
    for (int k = 0; k < options_.hybrid_policy_top && k < static_cast<int>(by_policy.size()); ++k) {
      add(safe[by_policy[static_cast<std::size_t>(k)]]);
    }
    std::vector<int> by_risk;
    for (int i = 0; i < safe.size(); ++i) by_risk.push_back(i);
    auto danger_of = [&](int i) {
      const int at = AdviceIndex(*advice, safe[i]);
      return at < 0 ? 1.0 : advice->danger[static_cast<std::size_t>(at)];
    };
    const Position& reference = belief_.Representative();
    auto is_king_move = [&](int i) {
      return reference.piece_at(MoveFrom(safe[i])) == kKing;
    };
    std::stable_sort(by_risk.begin(), by_risk.end(), [&](int a, int b) {
      const double ra = safe_risk[static_cast<std::size_t>(a)];
      const double rb = safe_risk[static_cast<std::size_t>(b)];
      if (ra != rb) return ra < rb;
      // Ties at the minimum: king moves first, then the neural danger
      // estimate, so defensive options survive the trim.
      if (is_king_move(a) != is_king_move(b)) return is_king_move(a);
      return danger_of(a) < danger_of(b);
    });
    for (int k = 0; k < options_.hybrid_risk_top && k < static_cast<int>(by_risk.size()); ++k) {
      add(safe[by_risk[static_cast<std::size_t>(k)]]);
    }
    ranked = chosen;
    shortlist = static_cast<int>(ranked.size());
  }
  ranked.resize(shortlist);
  trace->shortlisted = shortlist;

  if (!options_.use_matrix_game || shortlist == 1) {
    return note_choice(ranked.front().move);
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

  // Measured over the whole population, so a danger present in a small fraction
  // of hypotheses is still priced in.
  std::vector<double> risk(shortlist, 0.0);
  for (int row = 0; row < shortlist; ++row) {
    // The dominant term: probability of losing the king times the price of the
    // king. Charged on every cell, so no later stage can be blind to it.
    for (int i = 0; i < safe.size(); ++i) {
      if (safe[i] == ranked[row].move && i < static_cast<int>(safe_risk.size())) {
        risk[row] += safe_risk[static_cast<std::size_t>(i)] *
                     options_.king_risk_price;
        break;
      }
    }
  }
  if (options_.piece_risk_weight > 0.0) {
    for (int row = 0; row < shortlist; ++row) {
      risk[row] += options_.piece_risk_weight *
                   ExpectedMaterialRisk(ranked[row].move, en_passant);
    }
  }
  for (int row = 0; row < shortlist; ++row) {
    if (static_cast<int>(risk[row]) > trace->worst_risk) {
      trace->worst_risk = static_cast<int>(risk[row]);
    }
  }
  const double cell_budget =
      std::max(0.004, trace->budget * (1.0 - kShortlistShare) /
                          std::max(1, shortlist * columns));

  const auto matrix_deadline =
      turn_start + std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                       std::chrono::duration<double>(trace->budget));
  bool out_of_time = false;
  for (int column = 0; column < columns; ++column) {
    for (int row = 0; row < shortlist; ++row) {
      const Move move = ranked[row].move;
      if (out_of_time || std::chrono::steady_clock::now() >= matrix_deadline) {
        // Fall back on the shortlist search's own verdict for this cell rather
        // than spending time we no longer have.
        out_of_time = true;
        ++trace->cells_skipped;
        game.set(row, column,
                 static_cast<double>(ranked[row].score) - risk[row]);
        continue;
      }
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
        continue;
      }

      Position root = *hypotheses[column];
      root.set_side_to_move(our_side_);
      root.set_en_passant_square(en_passant);
      MoveList single;
      single.Add(move);
      SearchLimits limits;
      // Never ask for more time than the turn has left.
      const double left = std::chrono::duration<double>(
                              matrix_deadline - std::chrono::steady_clock::now())
                              .count();
      limits.seconds = std::min(cell_budget, std::max(0.002, left));
      if (options_.node_budget > 0) {
        limits.seconds = 600.0;
        const uint64_t cells =
            static_cast<uint64_t>(shortlist) * static_cast<uint64_t>(columns);
        limits.max_nodes = std::max<uint64_t>(
            256, static_cast<uint64_t>(options_.node_budget *
                                       (1.0 - kShortlistShare)) /
                     std::max<uint64_t>(1, cells));
      }
      const SearchResult result = searcher_.Search(&root, single, limits);
      trace->nodes += result.nodes;
      game.set(row, column,
               static_cast<double>(result.score) + bonus - risk[row]);
    }
  }

  // King safety was already settled over the whole population, so every row
  // here is one we are willing to play; the matrix decides between them.
  std::vector<int> safe_rows;
  for (int row = 0; row < shortlist; ++row) safe_rows.push_back(row);

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
  const Move final_move = ranked[safe_rows[picked]].move;
  if (advised) {
    const int at = AdviceIndex(*advice, final_move);
    trace->chosen_policy = at < 0 ? 0.0 : advice->policy[static_cast<std::size_t>(at)];
    trace->chosen_danger = at < 0 ? 0.0 : advice->danger[static_cast<std::size_t>(at)];
  }
  return note_choice(final_move);
}

}  // namespace fow
