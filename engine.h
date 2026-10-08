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
#include <unordered_map>
#include <utility>
#include <vector>

#include "belief.h"
#include "observation.h"
#include "search.h"
#include "transposition.h"

namespace fow {

// How a move is chosen once the legal list and the belief are in hand.
//   cpp     the search and matrix game alone (the reviewed baseline)
//   neural  a sample from the trained legal policy; no search
//   hybrid  neural ordering and danger estimates feeding the repaired search
enum class EngineMode : int { kCpp = 0, kNeural = 1, kHybrid = 2 };

const char* EngineModeName(EngineMode mode);

// The opponent's best immediate net capture on `hypothesis` with the opponent
// to move: victim value minus the capturer's value when `our_side` can
// recapture. One-ply exchange arithmetic; used by the exposure term and, on
// the true board, as the offline benchmark's material label.
int BestNetCapture(Position* hypothesis, int our_side);

// What the neural adapter knows about the legal moves this turn. Aligned by
// move, not by index, because the engine derives its own legal list. Particle
// risk and neural danger are estimates kept separately; neither is a
// certificate and they are never blended into one number.
struct NeuralAdvice {
  bool available = false;
  std::vector<Move> moves;
  std::vector<double> policy;   // probabilities over `moves`, sum to one
  std::vector<double> danger;   // sigmoid probabilities of immediate king loss
  double value = 0.0;           // the recurrent value head, for the log only
};

struct EngineOptions {
  EngineMode mode = EngineMode::kCpp;
  // Hybrid candidate budget: the union of these three sets, deduplicated, is
  // what the matrix game considers.
  int hybrid_policy_top = 8;
  int hybrid_search_top = 6;
  int hybrid_risk_top = 8;
  // Rows the matrix game can afford; the union is trimmed to this in the
  // order search, policy, lowest risk. Twelve is what arena v5 played with;
  // since cells now shrink with the clock instead of being skipped, more rows
  // cost depth per cell, never coverage of hypotheses.
  int hybrid_max_rows = 12;
  double neural_temperature = 1.0;
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
  // What that expectation covers: 0 = only the moved piece on its destination
  // square (v2-v10); 1 = the opponent's best immediate net capture anywhere
  // on the board after the move, so a piece left en prise to a hidden
  // attacker, or a move that unblocks a line onto one, is priced too. The
  // gold data (reports/IAmAVirus replay analysis.md) says 90% of the material
  // we lose goes to a hidden capturer and most of it is not the moved piece.
  int exposure_mode = 1;
  // Particles sampled for the exposure term (stride over the population),
  // since it costs a move generation per particle and candidate.
  int exposure_stride = 4;
  // Enforce in the belief what the visibility rule proves about unseen
  // squares (pawn deductions). On the 634 real losing seats, balanced
  // sampling, one binary: the population gets more honest (true attacker held
  // at the fatal ply 0.191 -> 0.228) and less material is left en prise
  // (8.2% -> 7.7%). Survival of the real fatal ply looked worse at one seed
  // (368 -> 341) and better at the next (345 -> 365); three seeds average
  // 352 off vs 351 on, so that was churn on near-tied decisions (HANDOFF.md).
  bool visibility_deductions = true;
  int history_mode = 0;
  // Capture evidence in the belief (see BeliefState::set_capture_evidence):
  // twlle83q lost a queen and a bishop to a knight standing on the square
  // where it had just taken ours, unseen. FOW_CAPTURE_EVIDENCE=0 disables.
  bool capture_evidence = true;
  // Two plies deep: weight on the material a hidden quiet move could win on
  // the opponent's next turn (ExpectedHiddenThreat). A rook sliding behind
  // the fog onto the open file our knight sits on is invisible to the one-ply
  // terms, and to the search, which lets us answer a move we would never
  // observe. Measured on the 634 real losing seats (balanced, deductions on,
  // 400k nodes): decisions that leave the opponent a >= 3-point two-ply
  // hidden threat on the true board fall 11.74% -> 8.34% (weight 0.5) ->
  // 7.35% (weight 1.0) against the real players' 9.60%, with king losses,
  // one-ply en prise and fatal-ply survival unchanged, at no measurable time
  // cost at stride 16.
  double hidden_threat_weight = 1.0;
  // The king version of the same two-ply blindness (tr0gwrvf: our king went
  // to g4 beside a queen last seen on e3; she moved to e4 unseen and the next
  // move left the king en prise): the share of hypotheses in which one quiet
  // enemy move to a square we would not see puts an unseen attacker on our
  // king, charged at this weight times the king price. Off until measured.
  double hidden_king_threat_weight = 0.6;
  // Repetition. The referee calls threefold and the engine had no notion of
  // it (eucmjl12: a knight for two pawns up, we shuffled to a draw). When the
  // current view has been seen before at one of our decisions, the moves we
  // played from it are charged this many centipawns per earlier occurrence,
  // unless the shortlist search already says we are losing by more than
  // `repetition_losing_margin` (then a draw is welcome).
  // Unseen attack surface of the moved piece, scaled by its value. In 55 of
  // v10's 69 arena games the queen was lost for less, 48 times to a capturer
  // we could not see and 44 times by moving her onto the square; the
  // particle terms only see that attacker when the population holds it
  // there. This charges, per square, every unseen empty square along a ray
  // from the destination that an enemy slider of the matching type could
  // stand on (the hypothesis says empty, the view says unseen), plus unseen
  // knight and pawn-attack squares, when the enemy still has such pieces.
  // Centipawns per square for a queen; other pieces in proportion to value.
  double surface_charge = 0.0;
  int surface_ray_cap = 3;
  int surface_stride = 4;
  // Opening book: our decisions in the first `book_plies` plies of the game
  // follow the strongest teams' most common move from the identical
  // observation, when the book has one and it is legal. They open 1.d4 in 80%
  // of their White games and answer 1...d5 or 1...c5; 18 of v10's 55 queen
  // losses came before ply 30, theirs 4-9% of games.
  int book_plies = 10;
  double repetition_penalty = 120.0;
  double repetition_losing_margin = 100.0;
  int hidden_threat_stride = 16;
  // Matrix cells on more than one thread. The arena gives two cores and the
  // search is single-threaded, so one core idles through the cell phase; the
  // cells are independent searches, so columns are split across threads, each
  // with its own transposition table and searcher. Wall time is unchanged
  // and every cell searches `cell_threads` times longer. Suite-checked for
  // legality and overrun; real-clock lanes pending (2026-10-07 20:40 UTC).
  int cell_threads = 2;
  // Vision, the Fog of War guide's first rule: squares we would see after the
  // move minus squares they would see, with extra weight on our pieces and
  // king being invisible to them; averaged over a stride of the population
  // and credited against the row's risk. Units are centipawns per square /
  // per piece / for the king. Off until measured.
  double vision_weight = 0.0;
  double vision_square = 2.0;
  double vision_piece = 10.0;
  double vision_king = 30.0;
  int vision_stride = 4;
  // Clock policy, in seconds. The per-move target is scaled by how hard the
  // decision looks once the king risks are known: a turn where the safest
  // move still carries real risk, or the fog is deep, gets up to
  // `hard_turn_multiplier` times the target (capped by `time_cap_hard`); a
  // turn with one safe move, or where a single row dominates, gets
  // `easy_turn_multiplier`. Games end with 60-150 s unused, so this moves
  // depth from easy plies to the few that decide the game.
  double hard_turn_multiplier = 2.0;
  double easy_turn_multiplier = 0.4;
  double hard_risk_threshold = 0.03;   // safest move's king risk
  double time_cap_hard = 12.0;
  // Reserve: the full candidate's lowest clock over 16 real-clock games was
  // 11 s with a 6 s reserve; 10 s keeps a slower arena host out of trouble
  // and costs nodes only in very long games.
  double time_reserve = 10.0;
  // Arena games (v5, v9, v10: 115 games) ended with a median 121 s unused on
  // our clock and never below 40 s; every decision stopped at the old 4 s
  // cap. With divisor 20 and cap 7 the budget formula spends about 6 s per
  // move in a 60-ply game and 5 s in a 100-ply game, tapers with the clock,
  // and still ends a 300-ply game with 14 s (simulation in HANDOFF.md).
  double time_divisor = 20.0;
  double time_cap = 7.0;
  double increment_share = 0.8;
  int transposition_megabytes = 192;
  // When non-zero, a decision is bounded by nodes rather than by the clock.
  // Used for measurement, never in a rated game, where the clock is what counts.
  uint64_t node_budget = 0;
  // Prior over the opponent's moves in the belief update: 0 uniform, 1 the v5
  // hand-set constants (default), 2 the learned conditional-logit prior
  // (measured: no decision gain, so not the default).
  int opponent_prior = 1;
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
  int cells_skipped = 0;   // matrix cells abandoned because the turn ran out
  int rows_added_for_safety = 0;  // low-risk moves appended to the shortlist
  int unseen_squares = 0;
  bool collapsed = false;
  double pieces_located = 0.0;
  // Which procedure actually decided, and compact per-candidate estimates for
  // the log: "uci:policy/danger/particle" for the leading candidates.
  EngineMode mode_used = EngineMode::kCpp;
  std::string candidates;
  double neural_value = 0.0;
  double chosen_policy = 0.0;
  double chosen_danger = 0.0;
  double budget_multiplier = 1.0;  // hard/easy turn scaling applied this turn
  double cells_spent = 0.0;        // seconds in the matrix cells
  int repetition_rows = 0;         // shortlist rows charged for repeating
  bool from_book = false;          // the move came from the opening book
  int cell_threads_used = 1;
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
  // `advice` carries the neural policy and danger estimates for this turn, or
  // null; without it every mode reduces to `cpp`.
  Move ChooseMove(const Observation& view, double remaining_seconds,
                  DecisionTrace* trace, const NeuralAdvice* advice = nullptr);

  // Records the move actually played, so the belief follows it.
  void NotifyMovePlayed(Move move);

  double TimeBudget(double remaining_seconds) const;

  inline const BeliefState& belief() const { return belief_; }
  // Opening book: (colour, observation) -> move, from the strongest teams'
  // own choices (gold/opening-book.json, learning/book.py). Returns the number
  // of entries loaded; an empty or missing file leaves the engine without one.
  int LoadBook(const std::string& path);
  inline int book_size() const { return static_cast<int>(book_.size()); }
  // Two plies deep, over a stride of the population: `material` is the best
  // net capture the opponent can *prepare* with one quiet move to a square
  // our post-move view would not show, beyond what they can already take;
  // `king` is the share of hypotheses in which such a move puts an unseen
  // attacker on our king.
  struct HiddenThreats {
    double material = 0.0;
    double king = 0.0;
  };
  HiddenThreats ExpectedHiddenThreats(Move move, int en_passant) const;
  double ExpectedHiddenThreat(Move move, int en_passant) const {
    return ExpectedHiddenThreats(move, en_passant).material;
  }
  // Expected vision balance after `move` (see EngineOptions::vision_weight):
  // positive when we see more and they see less of us.
  double ExpectedVision(Move move, int en_passant) const;
  // Unseen attack surface of the moved piece after `move`, in queen-weighted
  // squares, averaged over a stride of the population (EngineOptions::
  // surface_charge).
  double ExpectedHiddenSurface(Move move, int en_passant) const;

 private:
  // Our own castling rights, read from the believed state where MakeMove has
  // been maintaining them.
  Bitboard OurCastlingRights() const;

  // Expected material, in centipawns, that `move` hands over immediately,
  // averaged over every hypothesis in the population (destination square only).
  double ExpectedMaterialRisk(Move move, int en_passant) const;
  // Expected best immediate net capture the opponent has after `move`,
  // anywhere on the board, averaged over a stride of the population.
  double ExpectedExposure(Move move, int en_passant) const;

  // For each move, the share of hypotheses in which it leaves our king
  // capturable. Computed over the entire population rather than the sampled
  // columns of the matrix game, because the thing being measured is rare by
  // nature: a danger present in one hypothesis in twelve is usually absent from
  // all eight samples, which reports zero risk for a move that loses outright.
  std::vector<double> KingLossProbabilities(const MoveList& moves,
                                            int en_passant) const;

  // A sample from the neural policy restricted to `legal`.
  Move SampleNeural(const MoveList& legal, const NeuralAdvice& advice,
                    DecisionTrace* trace);

  int our_side_;
  double increment_;
  EngineOptions options_;
  std::mt19937_64 rng_;
  BeliefState belief_;
  TranspositionTable table_;
  Searcher searcher_;
  TranspositionTable worker_table_;  // the second thread's, when cell_threads > 1
  Searcher worker_searcher_;
  // The two most recent observations. En passant is inferred from the pair
  // bracketing the opponent's move: the view after our own move and the view
  // after theirs. An earlier version overwrote the previous view with the
  // current one on every observation, so the inference always compared two
  // identical strings and never found anything. Measured: 30 legal moves where
  // the referee had 31.
  Observation latest_view_;
  // (view at our decision, move played) for every move we have made, for
  // the repetition charge.
  std::vector<std::pair<std::string, Move>> history_;
  // "colour|view" -> (uci, games) alternatives, most played first; a move is
  // sampled in proportion to games so the opening is not a fixed line.
  std::unordered_map<std::string, std::vector<std::pair<std::string, int>>> book_;
  Observation before_latest_view_;
  int views_seen_ = 0;
};

}  // namespace fow

#endif  // FOW_ENGINE_H_
