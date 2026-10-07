// Copyright 2026. Fog of War chess engine.
//
// Tests for regret matching, checked against games whose equilibria are known in
// closed form. If this converges on rock-paper-scissors and on a game with a
// dominated action, it is solving matrix games correctly.

#include "../regret.h"

#include <cmath>
#include <utility>
#include <vector>

#include "testing.h"

namespace fow {
namespace {

MatrixGame MakeGame(int rows, int columns, std::vector<double> payoff) {
  MatrixGame game;
  game.rows = rows;
  game.columns = columns;
  game.payoff = std::move(payoff);
  return game;
}

bool Near(double actual, double expected, double tolerance) {
  return std::fabs(actual - expected) <= tolerance;
}

// Rock paper scissors: the unique equilibrium is uniform and the value is zero.
void SolvesRockPaperScissors() {
  const MatrixGame game = MakeGame(3, 3, {
      0, -1,  1,
      1,  0, -1,
     -1,  1,  0,
  });
  const MixedStrategy solution = SolveMatrixGame(game, 20000);
  FOW_EXPECT_TRUE(Near(solution.value, 0.0, 0.02));
  for (int i = 0; i < 3; ++i) {
    FOW_EXPECT_TRUE(Near(solution.row_probability[i], 1.0 / 3.0, 0.03));
    FOW_EXPECT_TRUE(Near(solution.column_probability[i], 1.0 / 3.0, 0.03));
  }
}

// A strictly dominant row must take essentially all the probability.
void FindsADominantStrategy() {
  const MatrixGame game = MakeGame(2, 2, {
      10, 10,
       0,  0,
  });
  const MixedStrategy solution = SolveMatrixGame(game, 5000);
  FOW_EXPECT_TRUE(solution.row_probability[0] > 0.95);
  FOW_EXPECT_TRUE(Near(solution.value, 10.0, 0.5));
}

// A saddle point: row 1, column 1 is optimal for both, so the solution should be
// pure and the value should be the saddle entry.
void SolvesAGameWithAPureEquilibrium() {
  const MatrixGame game = MakeGame(2, 2, {
      4, 5,
      2, 1,
  });
  // Row player prefers row 0; given row 0 the column player prefers column 0.
  const MixedStrategy solution = SolveMatrixGame(game, 20000);
  FOW_EXPECT_TRUE(solution.row_probability[0] > 0.9);
  FOW_EXPECT_TRUE(solution.column_probability[0] > 0.9);
  FOW_EXPECT_TRUE(Near(solution.value, 4.0, 0.3));
}

// Matching pennies scaled up: still uniform, value zero.
void SolvesMatchingPennies() {
  const MatrixGame game = MakeGame(2, 2, {
      100, -100,
     -100,  100,
  });
  const MixedStrategy solution = SolveMatrixGame(game, 20000);
  FOW_EXPECT_TRUE(Near(solution.value, 0.0, 2.0));
  FOW_EXPECT_TRUE(Near(solution.row_probability[0], 0.5, 0.05));
}

// The behaviour the engine actually relies on: a row that is excellent against
// one hypothesis but disastrous against another must lose out to a row that is
// merely good against both. This is the whole reason for solving a game rather
// than taking an argmax over the likeliest hypothesis.
void PrefersRobustnessOverAGambleAcrossHypotheses() {
  const MatrixGame game = MakeGame(2, 2, {
       500, -3000,  // brilliant against one hidden position, fatal against the other
       120,    80,  // solid whatever is actually there
  });
  const MixedStrategy solution = SolveMatrixGame(game, 20000);
  FOW_EXPECT_TRUE(solution.row_probability[1] > 0.9);
  FOW_EXPECT_TRUE(solution.value > 0.0);
}

void HandlesDegenerateShapes() {
  const MixedStrategy none = SolveMatrixGame(MakeGame(0, 0, {}), 100);
  FOW_EXPECT_TRUE(none.row_probability.empty());
  const MixedStrategy single = SolveMatrixGame(MakeGame(1, 1, {7}), 100);
  FOW_EXPECT_EQ(static_cast<int>(single.row_probability.size()), 1);
  FOW_EXPECT_TRUE(Near(single.row_probability[0], 1.0, 1e-9));
  FOW_EXPECT_TRUE(Near(single.value, 7.0, 1e-9));
}

// Probabilities must always form a distribution.
void StrategiesAreDistributions() {
  const MatrixGame game = MakeGame(4, 3, {
      1, -2,  3,
     -1,  4,  0,
      2,  2, -5,
      0,  1,  1,
  });
  const MixedStrategy solution = SolveMatrixGame(game, 5000);
  double row_sum = 0.0;
  for (const double probability : solution.row_probability) {
    FOW_EXPECT_TRUE(probability >= 0.0);
    row_sum += probability;
  }
  double column_sum = 0.0;
  for (const double probability : solution.column_probability) {
    FOW_EXPECT_TRUE(probability >= 0.0);
    column_sum += probability;
  }
  FOW_EXPECT_TRUE(Near(row_sum, 1.0, 1e-6));
  FOW_EXPECT_TRUE(Near(column_sum, 1.0, 1e-6));
}

}  // namespace
}  // namespace fow

int main() {
  FOW_RUN_TEST(fow::SolvesRockPaperScissors);
  FOW_RUN_TEST(fow::FindsADominantStrategy);
  FOW_RUN_TEST(fow::SolvesAGameWithAPureEquilibrium);
  FOW_RUN_TEST(fow::SolvesMatchingPennies);
  FOW_RUN_TEST(fow::PrefersRobustnessOverAGambleAcrossHypotheses);
  FOW_RUN_TEST(fow::HandlesDegenerateShapes);
  FOW_RUN_TEST(fow::StrategiesAreDistributions);
  return fow::testing::Summarize("regret_test");
}
