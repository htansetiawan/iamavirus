// Copyright 2026. Fog of War chess engine.

#include "regret.h"

#include <algorithm>
#include <cstddef>
#include <numeric>
#include <vector>

namespace fow {
namespace {

// Converts accumulated positive regrets into a strategy. Where no action has
// positive regret yet, nothing has been learned, so play uniformly.
void RegretsToStrategy(const std::vector<double>& regrets,
                       std::vector<double>* strategy) {
  double total = 0.0;
  for (std::size_t i = 0; i < regrets.size(); ++i) {
    (*strategy)[i] = regrets[i] > 0.0 ? regrets[i] : 0.0;
    total += (*strategy)[i];
  }
  if (total <= 0.0) {
    const double uniform = 1.0 / static_cast<double>(regrets.size());
    std::fill(strategy->begin(), strategy->end(), uniform);
    return;
  }
  for (double& probability : *strategy) probability /= total;
}

}  // namespace

MixedStrategy SolveMatrixGame(const MatrixGame& game, int iterations) {
  MixedStrategy result;
  if (game.rows <= 0 || game.columns <= 0) return result;

  const int rows = game.rows;
  const int columns = game.columns;
  std::vector<double> row_regret(rows, 0.0);
  std::vector<double> column_regret(columns, 0.0);
  std::vector<double> row_strategy(rows, 1.0 / rows);
  std::vector<double> column_strategy(columns, 1.0 / columns);
  std::vector<double> row_total(rows, 0.0);
  std::vector<double> column_total(columns, 0.0);
  std::vector<double> row_utility(rows, 0.0);
  std::vector<double> column_utility(columns, 0.0);

  for (int iteration = 0; iteration < iterations; ++iteration) {
    RegretsToStrategy(row_regret, &row_strategy);
    RegretsToStrategy(column_regret, &column_strategy);
    for (int row = 0; row < rows; ++row) row_total[row] += row_strategy[row];
    for (int column = 0; column < columns; ++column) {
      column_total[column] += column_strategy[column];
    }

    // Utility of each of our moves against the opponent's current mixture, and
    // of each hypothesis against ours. The game is zero sum, so the column
    // player's payoff is the negation of ours.
    for (int row = 0; row < rows; ++row) {
      double utility = 0.0;
      for (int column = 0; column < columns; ++column) {
        utility += column_strategy[column] * game.at(row, column);
      }
      row_utility[row] = utility;
    }
    for (int column = 0; column < columns; ++column) {
      double utility = 0.0;
      for (int row = 0; row < rows; ++row) {
        utility += row_strategy[row] * game.at(row, column);
      }
      column_utility[column] = -utility;
    }

    double row_value = 0.0;
    for (int row = 0; row < rows; ++row) {
      row_value += row_strategy[row] * row_utility[row];
    }
    const double column_value = -row_value;

    // Counterfactual regret: what each action would have gained over what the
    // current mixture actually gained.
    for (int row = 0; row < rows; ++row) {
      row_regret[row] += row_utility[row] - row_value;
    }
    for (int column = 0; column < columns; ++column) {
      column_regret[column] += column_utility[column] - column_value;
    }
  }

  // The average strategy is the one with the convergence guarantee, not the
  // final iterate.
  const double row_sum = std::accumulate(row_total.begin(), row_total.end(), 0.0);
  const double column_sum =
      std::accumulate(column_total.begin(), column_total.end(), 0.0);
  result.row_probability.resize(rows);
  result.column_probability.resize(columns);
  for (int row = 0; row < rows; ++row) {
    result.row_probability[row] =
        row_sum > 0.0 ? row_total[row] / row_sum : 1.0 / rows;
  }
  for (int column = 0; column < columns; ++column) {
    result.column_probability[column] =
        column_sum > 0.0 ? column_total[column] / column_sum : 1.0 / columns;
  }
  for (int row = 0; row < rows; ++row) {
    for (int column = 0; column < columns; ++column) {
      result.value += result.row_probability[row] *
                      result.column_probability[column] * game.at(row, column);
    }
  }
  return result;
}

}  // namespace fow
