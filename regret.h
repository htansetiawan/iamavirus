// Copyright 2026. Fog of War chess engine.
//
// Regret matching for the root decision.
//
// Picking the move that scores best against the single likeliest hypothesis is
// the wrong objective in an imperfect-information game: it is a best response to
// one guess, and it is exactly how a bot walks into something it could not see.
// The decision we actually face is a matrix game. Our rows are the moves we may
// play; the columns are the hypotheses the opponent's hidden position might be
// in; the payoff is what the search says our move is worth under that hypothesis.
//
// Regret matching (Hart and Mas-Colell) is the natural way to solve it here. It
// is the local rule behind counterfactual regret minimisation, it needs no
// linear programming, and iterating it drives average regret to zero, so the
// average strategy converges to a minimax-optimal mixture of our moves. Playing
// that mixture rather than an argmax does two useful things: it hedges across
// hypotheses instead of betting everything on the likeliest, and it makes us
// unpredictable, which matters when the same opponent meets us repeatedly.
//
// The column player is given the same treatment, which is what makes the result
// cautious: nature is allowed to concentrate on whichever hypothesis hurts us
// most, so a move that is excellent against the likely board but fatal against a
// plausible one does not survive.

#ifndef FOW_REGRET_H_
#define FOW_REGRET_H_

#include <cstddef>
#include <vector>

namespace fow {

// A zero-sum payoff matrix, row player maximising. payoff[row][column].
struct MatrixGame {
  int rows = 0;
  int columns = 0;
  std::vector<double> payoff;  // row-major, size rows * columns

  inline double at(int row, int column) const {
    return payoff[static_cast<std::size_t>(row) * columns + column];
  }
  inline void set(int row, int column, double value) {
    payoff[static_cast<std::size_t>(row) * columns + column] = value;
  }
};

struct MixedStrategy {
  std::vector<double> row_probability;
  std::vector<double> column_probability;
  double value = 0.0;  // the game's value under the averaged strategies
};

// Runs `iterations` of regret matching for both players and returns the average
// strategies, which is the pair that converges to equilibrium. O(iterations *
// rows * columns).
MixedStrategy SolveMatrixGame(const MatrixGame& game, int iterations);

}  // namespace fow

#endif  // FOW_REGRET_H_
