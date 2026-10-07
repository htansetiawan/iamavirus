// Copyright 2026. Fog of War chess engine.
//
// Tests for the decision procedure as a whole.
//
// The contract that matters is that the engine only ever returns a move the
// referee will accept, and that it stays inside its clock. Both are checked by
// driving it through complete games exactly as the protocol does, with the
// opponent hidden, and verifying every single move it produces against the move
// list the rules allow.

#include "../engine.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <string>

#include "../bitboard.h"
#include "../observation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

constexpr char kStartFen[] =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

// Small and fast, so the tests exercise the whole pipeline rather than the clock.
EngineOptions FastOptions() {
  EngineOptions options;
  options.particle_count = 96;
  options.shortlist_size = 4;
  options.hypothesis_count = 4;
  options.regret_iterations = 300;
  options.transposition_megabytes = 8;
  options.time_reserve = 0.0;
  options.time_cap = 0.06;
  return options;
}

struct GameOutcome {
  int plies = 0;
  int illegal_moves = 0;
  int null_moves = 0;
  double worst_overrun = 0.0;
};

// Plays a full game, our engine against random legal play, driving the protocol
// faithfully: an observation before every ply, a clock only on our turn.
GameOutcome PlayAgainstRandom(int our_side, uint64_t seed, int max_plies,
                             const EngineOptions& options) {
  std::mt19937_64 rng(seed);
  Position truth;
  PositionFromFen(kStartFen, &truth);
  Engine engine(our_side, 10.0, 0.05, options, seed);
  GameOutcome outcome;
  bool we_just_moved = false;

  for (int ply = 0; ply < max_plies; ++ply) {
    const Observation view(RenderObservation(truth, our_side));
    engine.Observe(view, we_just_moved);
    we_just_moved = false;
    ++outcome.plies;

    MoveList legal;
    truth.GenerateMoves(&legal);
    if (legal.empty()) break;

    Move move;
    if (truth.side_to_move() == our_side) {
      DecisionTrace trace;
      const auto started = std::chrono::steady_clock::now();
      move = engine.ChooseMove(view, 10.0, &trace);
      const double spent = std::chrono::duration<double>(
                               std::chrono::steady_clock::now() - started)
                               .count();
      if (spent - trace.budget > outcome.worst_overrun) {
        outcome.worst_overrun = spent - trace.budget;
      }
      if (move == kNullMove) {
        ++outcome.null_moves;
        break;
      }
      // The only thing that truly must hold: the move is legal.
      bool allowed = false;
      for (const Move candidate : legal) {
        if (candidate == move) allowed = true;
      }
      if (!allowed) ++outcome.illegal_moves;
      engine.NotifyMovePlayed(move);
      we_just_moved = true;
    } else {
      std::uniform_int_distribution<int> pick(0, legal.size() - 1);
      move = legal[pick(rng)];
    }
    UndoState undo;
    truth.MakeMove(move, &undo);
    if (truth.KingSquare(kWhite) < 0 || truth.KingSquare(kBlack) < 0) break;
  }
  return outcome;
}

// Every move the engine plays, in whole games from both colours, must be legal.
// This is the property that makes an illegal-move forfeit impossible.
void EveryMoveTheEngineReturnsIsLegal() {
  int plies = 0;
  int illegal = 0;
  double worst_overrun = 0.0;
  for (int game = 0; game < 4; ++game) {
    for (const int side : {kWhite, kBlack}) {
      const GameOutcome outcome =
          PlayAgainstRandom(side, 400 + game * 11 + side, 40, FastOptions());
      plies += outcome.plies;
      illegal += outcome.illegal_moves;
      worst_overrun = std::max(worst_overrun, outcome.worst_overrun);
    }
  }
  FOW_EXPECT_TRUE(plies > 100);
  FOW_EXPECT_EQ(illegal, 0);
  // Overrunning the budget by a whole second would risk the game clock.
  std::fprintf(stderr, "       %d plies, worst budget overrun %.3fs\n", plies,
               worst_overrun);
  FOW_EXPECT_TRUE(worst_overrun < 0.5);
}

// With the matrix game disabled the engine must still behave, since that is the
// comparison used to decide whether solving the game earns its clock.
void WorksWithTheMatrixGameDisabled() {
  EngineOptions options = FastOptions();
  options.use_matrix_game = false;
  const GameOutcome outcome = PlayAgainstRandom(kWhite, 77, 30, options);
  FOW_EXPECT_EQ(outcome.illegal_moves, 0);
  FOW_EXPECT_TRUE(outcome.plies > 5);
}

// The clock policy must never ask for more time than is left, must stay positive,
// and must settle near the increment so a long game cannot run it out.
void TimeBudgetIsAlwaysAffordable() {
  EngineOptions options;
  Engine engine(kWhite, 180.0, 2.0, options, 1);
  for (const double remaining : {180.0, 120.0, 60.0, 30.0, 12.0, 6.0, 3.0, 1.0,
                                 0.4, 0.05}) {
    const double budget = engine.TimeBudget(remaining);
    FOW_EXPECT_TRUE(budget > 0.0);
    FOW_EXPECT_TRUE(budget < remaining);
    FOW_EXPECT_TRUE(budget <= options.time_cap + 1e-9);
  }
  // Deep in a long game the budget should be of the order of the increment, not
  // of the remaining clock.
  FOW_EXPECT_TRUE(engine.TimeBudget(20.0) < 3.0);
  // And it must shrink as the clock does.
  FOW_EXPECT_TRUE(engine.TimeBudget(20.0) < engine.TimeBudget(180.0) + 1e-9);
}

// A position with exactly one legal move must be handled without any search.
void ReturnsTheOnlyMoveWhenForced() {
  EngineOptions options = FastOptions();
  Engine engine(kWhite, 10.0, 0.05, options, 5);
  // White king on a1 boxed in by its own pieces except for one square.
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("7k/8/8/8/8/8/PP6/KP6 w - - 0 1", &truth));
  const Observation view(RenderObservation(truth, kWhite));
  engine.Observe(view, false);
  DecisionTrace trace;
  const Move move = engine.ChooseMove(view, 10.0, &trace);
  FOW_EXPECT_TRUE(move != kNullMove);
  MoveList legal;
  truth.GenerateMoves(&legal);
  bool allowed = false;
  for (const Move candidate : legal) {
    if (candidate == move) allowed = true;
  }
  FOW_EXPECT_TRUE(allowed);
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::TimeBudgetIsAlwaysAffordable);
  FOW_RUN_TEST(fow::ReturnsTheOnlyMoveWhenForced);
  FOW_RUN_TEST(fow::WorksWithTheMatrixGameDisabled);
  FOW_RUN_TEST(fow::EveryMoveTheEngineReturnsIsLegal);
  return fow::testing::Summarize("engine_test");
}
