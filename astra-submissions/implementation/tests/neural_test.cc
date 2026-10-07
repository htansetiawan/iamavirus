// Copyright 2026. Fog of War chess engine.
//
// Tests for the neural adapter's observation side. Numerical parity with the
// Python tracker is checked by learning/tests/test_feature_parity.py; this
// suite covers the contracts the protocol loop relies on: one update per real
// event, sticky castling rights, en passant across the opponent's move, and
// the candidate list matching the engine's own legal list.

#include "../neural_observation.h"

#include <string>

#include "../bitboard.h"
#include "../neural_inference.h"
#include "../observation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

void InitialPlanesHaveOneActiveChannelPerSquare() {
  Position start;
  PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &start);
  for (const int side : {kWhite, kBlack}) {
    NeuralTracker tracker(side);
    tracker.Observe(Observation(RenderObservation(start, side)), kPhaseInitial, 0);
    float planes[kNeuralPlanes * kNumSquares];
    tracker.Planes(planes);
    for (int square = 0; square < kNumSquares; ++square) {
      float active = 0.0f;
      for (int plane = 0; plane < 14; ++plane) active += planes[plane * 64 + square];
      FOW_EXPECT_EQ(active, 1.0f);
    }
    // Own king on the canonical e1 for both colours.
    FOW_EXPECT_EQ(planes[5 * 64 + MakeSquare(4, 0)], 1.0f);
    float scalars[kNeuralScalars];
    tracker.Scalars(scalars);
    FOW_EXPECT_EQ(scalars[0], static_cast<float>(side));
    FOW_EXPECT_EQ(scalars[1], side == kWhite ? 1.0f : 0.0f);
    FOW_EXPECT_EQ(scalars[4], 1.0f);
  }
}

void CandidatesMatchTheRulesAndCarryEnPassant() {
  Position truth;
  PositionFromFen("4k3/3p4/8/4P3/8/8/8/4K3 w - - 0 1", &truth);
  NeuralTracker tracker(kWhite);
  tracker.Observe(Observation(RenderObservation(truth, kWhite)), kPhaseInitial, 0);
  UndoState undo;
  const Move king = EncodeMove(MakeSquare(4, 0), MakeSquare(4, 1));
  tracker.RecordOwnMove(king);
  truth.MakeMove(king, &undo);
  tracker.Observe(Observation(RenderObservation(truth, kWhite)), kPhaseAfterOwnMove, 1);
  truth.MakeMove(EncodeMove(MakeSquare(3, 6), MakeSquare(3, 4), kFlagDoublePush), &undo);
  tracker.Observe(Observation(RenderObservation(truth, kWhite)), kPhaseAfterOpponentMove, 2);
  FOW_EXPECT_EQ(tracker.EnPassant(), MakeSquare(3, 5));
  MoveList candidates;
  tracker.LegalCandidates(&candidates);
  MoveList expected;
  truth.GenerateMoves(&expected);
  FOW_EXPECT_EQ(candidates.size(), expected.size());
  // Castling rights are gone for good after the king moved, even though the
  // rooks never did.
  FOW_EXPECT_EQ(tracker.CastlingRights(), Bitboard{0});
}

void CastlingRightsNeverReturn() {
  NeuralTracker tracker(kBlack);
  // Built rather than written as a literal: "??-" is a trigraph.
  const std::string home = std::string(32, '?') + std::string(16, '-') +
                           "pppppppprnbqkbnr";
  tracker.Observe(Observation(home), kPhaseInitial, 0);
  FOW_EXPECT_EQ(tracker.CastlingRights(),
                SquareBB(MakeSquare(0, 7)) | SquareBB(MakeSquare(7, 7)));
  // The h8 rook is away: the kingside right is gone.
  std::string away = home;
  away[MakeSquare(7, 7)] = '-';
  away[MakeSquare(7, 6)] = 'r';
  tracker.Observe(Observation(away), kPhaseAfterOwnMove, 2);
  FOW_EXPECT_EQ(tracker.CastlingRights(), SquareBB(MakeSquare(0, 7)));
  // Back on h8: still gone.
  tracker.Observe(Observation(home), kPhaseAfterOwnMove, 4);
  FOW_EXPECT_EQ(tracker.CastlingRights(), SquareBB(MakeSquare(0, 7)));
}

void ModelWithoutGraphsIsUnavailableAndSaysWhy() {
  NeuralModel model;
  std::string error;
  FOW_EXPECT_TRUE(!model.Load("/nonexistent/model/dir", 1, &error));
  FOW_EXPECT_TRUE(!model.available());
  FOW_EXPECT_TRUE(!error.empty());
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::InitialPlanesHaveOneActiveChannelPerSquare);
  FOW_RUN_TEST(fow::CandidatesMatchTheRulesAndCarryEnPassant);
  FOW_RUN_TEST(fow::CastlingRightsNeverReturn);
  FOW_RUN_TEST(fow::ModelWithoutGraphsIsUnavailableAndSaysWhy);
  return fow::testing::Summarize("neural_test");
}
