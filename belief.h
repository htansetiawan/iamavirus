// Copyright 2026. Fog of War chess engine.
//
// Belief state: a particle filter over the opponent's position.
//
// Fog of War chess is an imperfect-information extensive-form game, so the thing
// we actually have to reason about is not a board but a distribution over boards
// consistent with everything we have seen. Each particle is a complete, legal
// game state: our own pieces, which we know exactly, together with one
// hypothesis about the opponent's.
//
// The filter runs the textbook two steps per opponent move:
//
//   Predict   For each particle, enumerate the opponent's legal moves in that
//             hypothesis. Enumerating rather than sampling-and-rejecting matters:
//             only a few of their moves are usually compatible with what we then
//             observe, so rejection sampling would throw away most of its work.
//   Condition Keep only successors compatible with the new observation, reweight
//             each particle by how much of its probability mass survived, and
//             resample back to full population.
//
// Compatibility is the operation this is built around, so it is a handful of
// bitwise operations rather than a loop over squares: restricted to the squares
// we can see, a particle's pieces of each type must equal exactly what we
// observe there. That makes conditioning O(number of piece types) per particle.
//
// Several consequences fall out for free that hand-written inference gets wrong.
// If one of our pieces vanishes, only hypotheses containing a piece that could
// have captured it survive, so the capturer's identity is inferred rather than
// guessed. Piece counts stay exact, because particles are updated by legal moves
// and never invented. And a piece that walks out of view is still somewhere,
// because the hypothesis tracked it.

#ifndef FOW_BELIEF_H_
#define FOW_BELIEF_H_

#include <array>
#include <cstdint>
#include <random>
#include <vector>

#include "evaluation.h"
#include "move.h"
#include "observation.h"
#include "position.h"

namespace fow {

// How the last observation was absorbed, reported for diagnostics.
struct BeliefUpdateReport {
  int surviving_particles = 0;
  int resampled_particles = 0;
  bool collapsed = false;  // nothing survived and the belief had to be rebuilt
  double mean_consistent_moves = 0.0;
};

class BeliefState {
 public:
  // `opponent_prior` selects between weighting the opponent's moves by
  // plausibility and treating them as uniformly likely. Exposed so the choice can
  // be ablated rather than assumed: it is the filter's most consequential
  // modelling assumption, and an earlier hand-tuned heuristic was kept for hours
  // on the strength of a measurement too coarse to support it.
  // `opponent_prior`: 0 uniform over their legal moves, 1 the v5 hand-set
  // constants, 2 the learned conditional-logit prior (opponent_model.h).
  BeliefState(int our_side, int particle_count, uint64_t seed,
              int opponent_prior = 1);

  // Absorbs an observation. `reflects_our_own_move` must be true for the
  // observation the arena sends immediately after our own move, since the only
  // change it reports is one we already know about. The first observation of a
  // game reports no move at all and is conditioned on regardless.
  BeliefUpdateReport Observe(const Observation& view,
                             bool reflects_our_own_move);

  // Applies a move we have decided to play to every hypothesis, and accounts for
  // any enemy piece it captures.
  void ApplyOurMove(Move move);

  inline int our_side() const { return our_side_; }
  inline int particle_count() const { return static_cast<int>(particles_.size()); }
  inline const std::vector<Position>& particles() const { return particles_; }

  // The hypothesis that agrees most with all the others: a real, legal position
  // rather than a square-by-square average, which would often be illegal. This
  // is what the main search runs on.
  const Position& Representative() const;

  // Up to `wanted` distinct hypotheses spread across the population, for
  // evaluating a move against several futures rather than only the likeliest.
  std::vector<const Position*> Sample(int wanted) const;

  // Fog context for evaluation, using the representative hypothesis to count
  // what the opponent still has.
  FogContext MakeFogContext(const Observation& view) const;

  // True when the opponent's king is actually visible, which decides how much a
  // winning line is to be trusted.
  bool EnemyKingVisible(const Observation& view) const;

 private:
  // Squares where `view` shows a piece of `color`, per piece type.
  struct ObservedPieces {
    Bitboard visible = 0;
    std::array<Bitboard, kNumPieceTypes> by_type{};
  };

  static ObservedPieces Summarize(const Observation& view, int color);

  // Does this hypothesis agree with the observation about the opponent? Only
  // visible squares can be compared, since the fog hides the rest.
  // O(number of piece types) bitwise comparisons.
  static bool AgreesAboutEnemy(const Position& position,
                               const ObservedPieces& seen, int color);

  // Does this hypothesis agree about *our own* pieces? This is a strictly
  // stronger test, and the distinction matters enormously.
  //
  // Our pieces are always visible, so the squares the observation shows them on
  // are all of them -- a hypothesis placing one of ours anywhere else is
  // impossible, because that square would then have been visible too. Comparing
  // only visible squares, as for the opponent, silently permits a hypothesis to
  // keep a piece of ours that has just been captured on a square that has since
  // gone dark. It then never concludes that an enemy piece is standing there,
  // which is the one inference that matters most: the piece that just took
  // something of ours is the piece most likely to take our king next.
  static bool AgreesAboutUs(const Position& position,
                            const ObservedPieces& seen, int color);

  // Plausibility of an opponent move, used as the prior in the filter's
  // reweighting. Replaces a uniform prior over their legal moves.
  //
  // The uniform assumption is the filter's weakest point and it is weakest
  // exactly where it matters most: roughly twenty of the opponent's thirty moves
  // are invisible to us, so for those the prior alone decides the posterior.
  // Treating them as equally likely throws away the strongest evidence we have
  // about a hidden board, which is that the opponent is trying to win.
  //
  // This is what refutes a bait. When a piece appears beside our king where we
  // can take it, the hypotheses divide into ones where it is defended and ones
  // where the opponent simply gave it away. Uniformly weighted, the giveaway
  // hypotheses dominate because there are more of them, and the bait looks free.
  // Weighted by plausibility, giving away a bishop for nothing is rare, so the
  // mass moves onto the defended hypotheses -- which is the truth.
  double MovePlausibility(Position* hypothesis, Move move) const;

  void Condition(const Observation& view, BeliefUpdateReport* report);
  void PredictAndCondition(const Observation& view, BeliefUpdateReport* report);
  void Resample(const std::vector<double>& weights,
                const std::vector<Position>& pool, BeliefUpdateReport* report);
  // Rebuilds a plausible population when every hypothesis has been contradicted,
  // which can happen if the opponent does something no particle anticipated.
  void Recover(const Observation& view, BeliefUpdateReport* report);

  int our_side_;
  int target_count_;
  int opponent_prior_;
  std::mt19937_64 rng_;
  std::vector<Position> particles_;
  // Piece counts the opponent is believed to still own.
  //
  // This is tracked authoritatively rather than read back from the particles.
  // Enemy material leaves the board only when we capture it, and a capture
  // always lands on a square we can see, so the count is exact. Deriving it from
  // the population instead lets one under-filled rebuild shrink the census
  // permanently, which then makes every later rebuild wrong too.
  std::array<int, kNumPieceTypes> enemy_census_{};
  // Raised when an observation shows more of a piece type than the census
  // allows, which is how a promotion behind the fog becomes visible to us.
  void ReconcileCensus(const Observation& view);
  // Our own castling rights, tracked from our own history and never from the
  // board: a king or rook that has left its home square and returned does not
  // get its right back. A rebuilt population used to read the rights off the
  // board, which once produced an illegal castle in a simulator game.
  void UpdateOwnRights(const Observation& view);
  Bitboard own_rights_ = 0;
  bool seen_any_ = false;
  mutable int representative_index_ = 0;
  mutable bool representative_valid_ = false;
};

}  // namespace fow

#endif  // FOW_BELIEF_H_
