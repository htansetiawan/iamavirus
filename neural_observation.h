// Copyright 2026. Fog of War chess engine.
//
// Observation-history features for the neural policy, mirroring
// learning/features.py plane for plane. The tracker sees exactly what the bot
// receives -- its colour, the ordered observations and its own moves -- and
// nothing else, so no fact the policy is not entitled to can reach the model.
//
// learning/tests/test_feature_parity.py drives this code and the Python tracker
// over identical event streams through tools/neural_features_main.cc.

#ifndef FOW_NEURAL_OBSERVATION_H_
#define FOW_NEURAL_OBSERVATION_H_

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "bitboard.h"
#include "move.h"
#include "observation.h"

namespace fow {

inline constexpr int kNeuralPlanes = 32;
inline constexpr int kNeuralScalars = 8;
inline constexpr int kAgeCap = 100;
inline constexpr int kPlyCap = 1000;
inline constexpr const char* kFeatureVersion = "features-v2";  // v2: visible empty on plane 13, unknown on 12
inline constexpr const char* kActionVersion = "actions-v1";

enum ObservationPhase : int {
  kPhaseInitial = 0,
  kPhaseAfterOwnMove = 1,
  kPhaseAfterOpponentMove = 2,
};

// Canonical coordinates: Black's board is reflected rank-wise so one network
// serves both colours. An involution, so it is also the inverse.
inline constexpr int CanonicalSquare(int square, int side) {
  return side == kBlack ? square ^ 56 : square;
}

// Promotion code shared with the action codec: none, queen, rook, bishop, knight.
int PromotionCode(Move move);

// One scored candidate, in canonical coordinates, with its raw move.
struct NeuralCandidate {
  Move move = kNullMove;
  int from = 0;        // canonical
  int to = 0;          // canonical
  int promotion = 0;   // code above
};

class NeuralTracker {
 public:
  explicit NeuralTracker(int side);

  // One real observation event; call exactly once per delivered view.
  void Observe(const Observation& view, int phase, int ply);
  // Our chosen move: records known facts, but the recurrent state waits for
  // the real observation that follows.
  void RecordOwnMove(Move move);

  bool our_turn() const { return ply_ % 2 == side_; }
  int side() const { return side_; }
  int ply() const { return ply_; }
  int events() const { return events_; }
  int phase() const { return phase_; }
  bool have_view() const { return have_current_; }
  const Observation& current() const { return current_; }

  Bitboard CastlingRights() const;
  // Raw en passant target inferred from the bracketing views, or -1.
  int EnPassant() const;
  // Exact legal moves from the observation history alone.
  void LegalCandidates(MoveList* list) const;
  // Candidates for the score graph, in the same order as `moves`.
  std::vector<NeuralCandidate> MakeCandidates(const MoveList& moves) const;

  // Writes [32][8][8] floats (2048) and the 8 scalars.
  void Planes(float* out) const;
  void Scalars(float* out) const;

 private:
  int RelativeClass(char symbol) const;

  int side_;
  std::array<int8_t, kNumSquares> last_seen_{};       // by canonical square
  std::array<int32_t, kNumSquares> last_seen_ply_{};
  std::array<bool, kNumSquares> ever_seen_{};
  bool kingside_ = true;
  bool queenside_ = true;
  int last_own_from_ = -1;
  int last_own_to_ = -1;
  Observation current_;
  Observation previous_;
  bool have_current_ = false;
  bool have_previous_ = false;
  int previous_phase_ = kPhaseInitial;
  int phase_ = kPhaseInitial;
  int ply_ = 0;
  int events_ = 0;
  int king_home_;
  int rook_home_queenside_;
  int rook_home_kingside_;
  char own_king_;
  char own_rook_;
};

}  // namespace fow

#endif  // FOW_NEURAL_OBSERVATION_H_
