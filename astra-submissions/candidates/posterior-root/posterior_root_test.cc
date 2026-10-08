#include "posterior_root.h"

#include <array>
#include <cmath>
#include <cstdlib>
#include <random>

#include "bitboard.h"
#include "engine.h"
#include "observation.h"
#include "position.h"
#include "tests/testing.h"

namespace fow {
namespace {

void ChanceAndAdversarialColumnsAreDifferentObjectives() {
  MatrixGame game{2, 2, {100.0, -100.0, -1.0, -1.0}};
  const auto chance = SolvePosteriorMean(game);
  const auto adversarial = SolveMatrixGame(game, 4000);
  FOW_EXPECT_EQ(chance.row_probability[0], 1.0);
  FOW_EXPECT_EQ(chance.value, 0.0);
  FOW_EXPECT_TRUE(adversarial.row_probability[1] > 0.99);
  // More posterior mass on the bad world must reverse the chance decision.
  game = {2, 4, {100.0, -100.0, -100.0, -100.0, -1.0, -1.0, -1.0, -1.0}};
  FOW_EXPECT_EQ(SolvePosteriorMean(game).row_probability[1], 1.0);
}

void TiesAndSafetyCostsArePreserved() {
  MatrixGame game{3, 2, {4.0, 8.0, 6.0, 6.0, 5.0, 5.0}};
  auto result = SolvePosteriorMean(game);
  FOW_EXPECT_EQ(result.row_probability[0], 0.5);
  FOW_EXPECT_EQ(result.row_probability[1], 0.5);
  FOW_EXPECT_EQ(result.row_probability[2], 0.0);
  // Apply an existing whole-population row charge before aggregation.
  game.set(0, 0, game.at(0, 0) - 2.0);
  game.set(0, 1, game.at(0, 1) - 2.0);
  result = SolvePosteriorMean(game);
  FOW_EXPECT_EQ(result.row_probability[1], 1.0);
  FOW_EXPECT_EQ(result.value, 6.0);
  FOW_EXPECT_EQ(result.column_probability[0], 0.5);
}

void SamplingPreservesPopulationMultiplicity() {
  std::mt19937_64 rng(777), duplicate(777);
  FOW_EXPECT_TRUE(PosteriorSampleIndices(0, 8, &rng).empty());
  FOW_EXPECT_TRUE(PosteriorSampleIndices(7, 0, &rng).empty());
  const auto whole = PosteriorSampleIndices(4, 8, &rng);
  FOW_EXPECT_TRUE((whole == std::vector<std::size_t>{0, 1, 2, 3}));
  // Exact enumeration must not spend a random draw.
  FOW_EXPECT_TRUE(rng == duplicate);
  std::array<int, 7> counts{};
  bool repeated_index = false;
  bool in_bounds = true;
  bool deterministic = true;
  for (int draw = 0; draw < 20000; ++draw) {
    const auto indices = PosteriorSampleIndices(7, 3, &rng);
    deterministic &= indices == PosteriorSampleIndices(7, 3, &duplicate);
    for (const auto index : indices) {
      in_bounds &= index < counts.size();
      if (index < counts.size()) ++counts[index];
    }
    repeated_index |= indices[0] == indices[1] || indices[0] == indices[2] ||
                      indices[1] == indices[2];
  }
  FOW_EXPECT_TRUE(in_bounds);
  FOW_EXPECT_TRUE(deterministic);
  FOW_EXPECT_TRUE(repeated_index);  // deliberately not unique-board sampling
  for (const int count : counts) FOW_EXPECT_TRUE(std::abs(count - 60000.0 / 7) < 500);
  // If six entries denote the same board, it gets six times a singleton's
  // mass. Deduplication would instead make these two worlds equiprobable.
  FOW_EXPECT_TRUE((60000 - counts[6]) / 60000.0 > 0.83);
  FOW_EXPECT_TRUE((60000 - counts[6]) / 60000.0 < 0.88);
}

void NewSelectorsOnlyReturnRefereeLegalMoves() {
  constexpr char start[] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
  int decisions = 0;
  for (const int mode : {1, 2}) {
    for (const int side : {kWhite, kBlack}) {
      EngineOptions options;
      options.root_mode = mode;
      options.particle_count = 48;
      options.hypothesis_count = 4;
      options.shortlist_size = 4;
      options.cell_threads = 1;
      options.transposition_megabytes = 1;
      options.node_budget = 4000;
      options.book_plies = 0;
      Engine engine(side, 180.0, 2.0, options, 712 + side);
      Position truth;
      PositionFromFen(start, &truth);
      std::mt19937_64 opponent(77 + side);
      bool own = false;
      for (int ply = 0; ply < 48; ++ply) {
        const Observation view(RenderObservation(truth, side));
        engine.Observe(view, own);
        own = false;
        MoveList legal;
        truth.GenerateMoves(&legal);
        if (legal.empty()) break;
        Move selected;
        if (truth.side_to_move() == side) {
          DecisionTrace trace;
          selected = engine.ChooseMove(view, 170.0, &trace);
          bool found = false;
          for (const Move move : legal) found |= selected == move;
          FOW_EXPECT_TRUE(found);
          FOW_EXPECT_TRUE(std::isfinite(trace.game_value));
          if (!found) return;
          engine.NotifyMovePlayed(selected);
          own = true;
          ++decisions;
        } else {
          selected = legal[std::uniform_int_distribution<int>(0, legal.size() - 1)(opponent)];
        }
        UndoState undo;
        truth.MakeMove(selected, &undo);
        if (truth.PreviousMoverIsLost()) break;
      }
    }
  }
  FOW_EXPECT_TRUE(decisions >= 12);
}

void RootModeIsExplicitAndDefaultsOff() {
  unsetenv("FOW_ROOT_MODE");
  FOW_EXPECT_EQ(EngineOptionsFromEnvironment().root_mode, 0);
  setenv("FOW_ROOT_MODE", "2", 1);
  FOW_EXPECT_EQ(EngineOptionsFromEnvironment().root_mode, 2);
  unsetenv("FOW_ROOT_MODE");
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::ChanceAndAdversarialColumnsAreDifferentObjectives);
  FOW_RUN_TEST(fow::TiesAndSafetyCostsArePreserved);
  FOW_RUN_TEST(fow::SamplingPreservesPopulationMultiplicity);
  FOW_RUN_TEST(fow::NewSelectorsOnlyReturnRefereeLegalMoves);
  FOW_RUN_TEST(fow::RootModeIsExplicitAndDefaultsOff);
  return fow::testing::Summarize("posterior_root_test");
}
