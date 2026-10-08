// Research root selector: chance-weighted hypotheses, not a new game solver.
#ifndef ASTRA_POSTERIOR_ROOT_H_
#define ASTRA_POSTERIOR_ROOT_H_

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

#include "regret.h"

namespace fow {

// A resampled population carries posterior mass in entry multiplicities. Keep
// those entries, including identical boards. Uniform draws with replacement
// give an unbiased column mean; inserting a representative would bias it.
// Enumerate the complete population when it fits, avoiding needless noise.
inline std::vector<std::size_t> PosteriorSampleIndices(
    std::size_t population, int wanted, std::mt19937_64* rng) {
  if (population == 0 || wanted <= 0) return {};
  const std::size_t count = std::min(population, static_cast<std::size_t>(wanted));
  std::vector<std::size_t> indices(count);
  if (count == population) {
    std::iota(indices.begin(), indices.end(), 0);
  } else {
    std::uniform_int_distribution<std::size_t> pick(0, population - 1);
    for (std::size_t& index : indices) index = pick(*rng);
  }
  return indices;
}

// Columns are equally weighted draws from the posterior (or all population
// entries). Existing row-level safety costs remain inside every payoff. This
// maximizes expected utility; it is neither minimax nor extensive-form CFR.
// Exact ties share probability uniformly; dominated rows receive none.
inline MixedStrategy SolvePosteriorMean(const MatrixGame& game) {
  MixedStrategy result;
  if (game.rows <= 0 || game.columns <= 0) return result;
  if (game.payoff.size() != static_cast<std::size_t>(game.rows) * game.columns) {
    throw std::invalid_argument("posterior payoff dimensions do not match");
  }
  result.column_probability.assign(game.columns, 1.0 / game.columns);
  std::vector<double> means(game.rows, 0.0);
  double best = -std::numeric_limits<double>::infinity();
  for (int row = 0; row < game.rows; ++row) {
    for (int column = 0; column < game.columns; ++column) {
      const double value = game.at(row, column);
      if (!std::isfinite(value)) {
        throw std::invalid_argument("posterior payoff is not finite");
      }
      means[row] += value / game.columns;
    }
    best = std::max(best, means[row]);
  }
  const int ties = static_cast<int>(std::count(means.begin(), means.end(), best));
  result.row_probability.resize(game.rows);
  for (int row = 0; row < game.rows; ++row) {
    result.row_probability[row] = means[row] == best ? 1.0 / ties : 0.0;
  }
  result.value = best;
  return result;
}

}  // namespace fow
#endif  // ASTRA_POSTERIOR_ROOT_H_
