// Copyright 2026. Fog of War chess engine.
//
// Alpha-beta search over a believed position.
//
// The terminal test is the referee's, not orthodox chess's: at every node, if
// the side that just moved left its king capturable, the game is already over.
// That single rule replaces check, checkmate and legality filtering, and it
// means a move that exposes our own king is simply a losing move the search
// finds by itself, with no special-case code.
//
// Wins and losses are scored asymmetrically on purpose. A loss is certain in a
// way a win is not: our own king's position is known exactly, so a line where it
// is captured is real, whereas a line where we capture the enemy king rests on a
// guess about where that king stands. Pricing the win lower makes the engine
// decline speculative king hunts that give up a real king in exchange.

#ifndef FOW_SEARCH_H_
#define FOW_SEARCH_H_

#include <array>
#include <chrono>
#include <cstdint>
#include <vector>

#include "evaluation.h"
#include "move.h"
#include "position.h"
#include "transposition.h"

namespace fow {

inline constexpr int kInfinity = 40000;
inline constexpr int kLossMagnitude = 30000;
// Used when we can actually see the enemy king, so a win line is trustworthy.
inline constexpr int kWinConfirmed = 29000;
// Used when the enemy king's square is a guess.
inline constexpr int kWinSpeculative = 14000;
inline constexpr int kMaxPly = 64;

struct SearchLimits {
  double seconds = 1.0;
  int max_depth = kMaxPly - 2;
  // Hard node ceiling, or zero for no limit. When set, this is what ends the
  // search and the clock becomes only a safety net, which makes a result
  // independent of how busy the machine is.
  uint64_t max_nodes = 0;
};

struct RootMoveValue {
  Move move = kNullMove;
  int score = -kInfinity;
};

struct SearchResult {
  Move best_move = kNullMove;
  int score = -kInfinity;
  int depth = 0;           // deepest fully completed iteration
  uint64_t nodes = 0;
  std::vector<RootMoveValue> root_values;  // from the last usable iteration
};

// Configuration of the engine's search behaviour, exposed so that each choice
// can be measured head to head rather than assumed.
struct SearchOptions {
  bool use_late_move_reductions = true;
  bool use_aspiration_windows = true;
  // Score for a winning line that rests on a guess about where the enemy king
  // stands. Lowering it makes the engine more sceptical of king hunts; raising
  // it towards kWinConfirmed makes it chase them. Exposed because it is the
  // constant most likely to make a deeper search worse rather than better.
  int speculative_win_score = kWinSpeculative;
};

class Searcher {
 public:
  explicit Searcher(TranspositionTable* table) : table_(table) {}

  // `our_side` is the side the engine plays; `enemy_king_confirmed` says whether
  // the enemy king is actually visible this turn, which sets how much a win line
  // is trusted.
  void SetContext(int our_side, bool enemy_king_confirmed, const FogContext& fog);
  void set_options(const SearchOptions& options) { options_ = options; }

  // Searches `root_moves` only, which lets the caller pass the exact legal moves
  // derived from the observation and so guarantees the returned move is legal.
  SearchResult Search(Position* root, const MoveList& root_moves,
                      const SearchLimits& limits);

 private:
  int Negamax(Position* position, int depth, int alpha, int beta, int ply);
  int Quiescence(Position* position, int alpha, int beta, int ply);

  // Returns true and sets `score` when the position is already decided.
  bool TerminalScore(const Position& position, int ply, int* score) const;

  int CaptureGain(const Position& position, Move move) const;
  void ScoreMoves(const Position& position, MoveList* moves, Move table_move,
                  int ply, std::array<int, MoveList::kCapacity>* scores) const;
  // Moves the best remaining move to `index`. O(n) per call, which beats a full
  // sort because alpha-beta usually stops after very few moves.
  static void SelectNext(MoveList* moves,
                         std::array<int, MoveList::kCapacity>* scores,
                         int index);

  void RecordCutoff(const Position& position, Move move, int depth, int ply);
  inline bool OutOfTime();

  TranspositionTable* table_;
  SearchOptions options_;
  int our_side_ = kWhite;
  int win_magnitude_ = kWinSpeculative;
  FogContext fog_;
  // Hash of everything SetContext changes that affects a score. XORed into the
  // transposition key so an entry written under one fog context is never read
  // under another: the fog term changes the evaluation of the same board, so a
  // board key alone identifies the position but not the score.
  uint64_t context_key_ = 0;

  std::chrono::steady_clock::time_point deadline_;
  uint64_t node_ceiling_ = 0;
  uint64_t nodes_ = 0;
  bool stopped_ = false;

  std::array<std::array<Move, 2>, kMaxPly + 2> killers_{};
  // Indexed by [side][from][to]; small enough to stay cache resident.
  std::array<std::array<std::array<int32_t, kNumSquares>, kNumSquares>,
             kNumColors>
      history_{};
};

}  // namespace fow

#endif  // FOW_SEARCH_H_
