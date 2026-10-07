// Copyright 2026. Fog of War chess engine.
//
// The decision procedure: belief, search and the root matrix game.
//
// A move is chosen in four steps.
//
//  1. The exact legal moves are derived from the observation alone, so whatever
//     is played cannot be rejected by the referee.
//  2. A full-depth search of the likeliest hypothesis shortlists the candidates
//     worth thinking about, because solving a matrix game over forty moves would
//     spend the clock on moves no one would play.
//  3. Each shortlisted move is searched against several hypotheses, filling a
//     payoff matrix: rows are our moves, columns are the opponent's possible
//     hidden positions.
//  4. Regret matching solves that matrix and we sample from the resulting
//     mixture, after discarding any move that loses our king under too many
//     hypotheses.
//
// Step 4 is the part that an ordinary chess engine has no analogue for. Taking
// the best move against the single likeliest board is a best response to a
// guess; solving the game hedges across the hypotheses we cannot distinguish,
// and declines moves that are excellent against the likely board but lose
// outright against a plausible one.

#ifndef FOW_ENGINE_H_
#define FOW_ENGINE_H_

#include <cstdint>
#include <random>
#include <string>
#include <vector>

#include "belief.h"
#include "observation.h"
#include "search.h"
#include "transposition.h"

namespace fow {

struct EngineOptions {
  int particle_count = 2048;
  // Moves carried from the shortlist into the matrix game.
  int shortlist_size = 6;
  // Hypotheses used as columns of the matrix game.
  int hypothesis_count = 8;
  int regret_iterations = 4000;
  // Solve the root matrix game at all. Turning this off reduces the engine to a
  // best response against the likeliest hypothesis, which is the comparison that
  // tells us whether the game solving is earning its clock.
  bool use_matrix_game = true;
  // Price of the king, in centipawns, charged in proportion to the probability
  // that a move leaves it capturable.
  //
  // This replaces an earlier threshold, which an offline benchmark against real
  // games showed to be the wrong instrument: it declined the losing capture in
  // only 8 of 15 seeds. A threshold is all-or-nothing, so in a position where
  // every move carries some risk it rejected everything, and the fallback band
  // then re-admitted the fatal move -- at which point nothing inside the
  // surviving set could see the risk any more and a bishop won the argument.
  //
  // Charging the risk continuously is the honest statement of the trade. At this
  // price a one-percent chance of dying costs three pawns, and the eight percent
  // in that game costs far more than the bishop on offer, whatever the seed.
  double king_risk_price = 30000.0;
  // Moves above this probability of losing the king are dropped before the
  // shortlist, purely to stop the search spending time on them. The price above
  // is what actually decides; this only has to be loose enough never to discard
  // the best move in a sharp position.
  double king_loss_tolerance = 0.20;
  // Weight on the expected material a move hands over, measured across the
  // whole population rather than the sampled columns. Set to zero to disable.
  double piece_risk_weight = 1.0;
  // Clock policy, in seconds.
  double time_reserve = 6.0;
  double time_divisor = 30.0;
  double time_cap = 4.0;
  double increment_share = 0.8;
  int transposition_megabytes = 192;
  // When non-zero, a decision is bounded by nodes rather than by the clock.
  // Used for measurement, never in a rated game, where the clock is what counts.
  uint64_t node_budget = 0;
  // Weight the opponent's moves by plausibility when updating the belief, rather
  // than treating them as uniformly likely.
  bool use_opponent_prior = true;
  SearchOptions search;
};

// Diagnostics for one decision, written to stderr by the protocol loop.
struct DecisionTrace {
  int depth = 0;
  int score = 0;
  uint64_t nodes = 0;
  int legal_moves = 0;
  int shortlisted = 0;
  int hypotheses = 0;
  int rejected_unsafe = 0;
  int king_risk_permille = 0;   // king-loss probability of the CHOSEN move
  int safest_risk_permille = 0; // ...and of the safest move available
  bool forced_risky = false;    // every move exceeded the tolerance
  int worst_risk = 0;
  double chosen_probability = 1.0;
  double game_value = 0.0;
  double budget = 0.0;
  double spent = 0.0;
  int unseen_squares = 0;
  bool collapsed = false;
  double pieces_located = 0.0;
};

// Options with any overrides from the environment applied.
//
// Every value here is a judgement call that local play can measure, and some of
// them -- the risk weight above all -- have not been separated from one another
// yet. Reading them from the environment means a configuration can be tested
// head to head without recompiling, which is what the arena harness does.
//
// Recognised variables: FOW_PARTICLES, FOW_SHORTLIST, FOW_HYPOTHESES,
// FOW_REGRET_ITERATIONS, FOW_MATRIX_GAME, FOW_KING_LOSS_TOLERANCE,
// FOW_PIECE_RISK, FOW_TIME_CAP, FOW_TIME_RESERVE, FOW_TIME_DIVISOR,
// FOW_HASH_MB, FOW_SPECULATIVE_WIN, FOW_LMR, FOW_ASPIRATION.
EngineOptions EngineOptionsFromEnvironment();

class Engine {
 public:
  Engine(int our_side, double base_seconds, double increment_seconds,
         const EngineOptions& options, uint64_t seed);

  // Absorbs an observation. `reflects_our_own_move` is true for the observation
  // the arena sends immediately after our own move.
  void Observe(const Observation& view, bool reflects_our_own_move);

  // Chooses a move given the remaining clock. Returns kNullMove when we have no
  // legal move, which under the course rules means the game is already lost.
  Move ChooseMove(const Observation& view, double remaining_seconds,
                  DecisionTrace* trace);

  // Records the move actually played, so the belief follows it.
  void NotifyMovePlayed(Move move);

  double TimeBudget(double remaining_seconds) const;

  inline const BeliefState& belief() const { return belief_; }

 private:
  // Our own castling rights, read from the believed state where MakeMove has
  // been maintaining them.
  Bitboard OurCastlingRights() const;

  // Expected material, in centipawns, that `move` hands over immediately,
  // averaged over every hypothesis in the population.
  double ExpectedMaterialRisk(Move move, int en_passant) const;

  // For each move, the share of hypotheses in which it leaves our king
  // capturable. Computed over the entire population rather than the sampled
  // columns of the matrix game, because the thing being measured is rare by
  // nature: a danger present in one hypothesis in twelve is usually absent from
  // all eight samples, which reports zero risk for a move that loses outright.
  std::vector<double> KingLossProbabilities(const MoveList& moves,
                                            int en_passant) const;

  int our_side_;
  double increment_;
  EngineOptions options_;
  std::mt19937_64 rng_;
  BeliefState belief_;
  TranspositionTable table_;
  Searcher searcher_;
  // The previous observation, needed to infer en passant: it is the one piece of
  // state a single observation cannot carry.
  Observation previous_view_;
  bool have_previous_ = false;
};

}  // namespace fow

#endif  // FOW_ENGINE_H_
