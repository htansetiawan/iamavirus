// Copyright 2026. Fog of War chess engine.
//
// Tests for the static evaluation. The properties checked here are the ones a
// bug would quietly break: symmetry (so neither colour is systematically
// favoured), monotonicity in material, and the sign and shape of the fog term.

#include "../evaluation.h"

#include <string>

#include "../bitboard.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

constexpr char kStartFen[] =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

Position Parse(const std::string& fen) {
  Position position;
  FOW_EXPECT_TRUE(PositionFromFen(fen, &position));
  return position;
}

Bitboard RanksFiveToEight() {
  Bitboard mask = 0;
  for (int square = 32; square < 64; ++square) mask |= SquareBB(square);
  return mask;
}

FogContext WhiteFacingFog() {
  FogContext fog;
  fog.unseen = RanksFiveToEight();
  fog.side = kWhite;
  fog.rook_like = 3;
  fog.bishop_like = 3;
  fog.knights = 2;
  fog.pawns = 8;
  return fog;
}

void StartingPositionIsBalanced() {
  const Position start = Parse(kStartFen);
  FOW_EXPECT_EQ(Evaluate(start, kWhite, FogContext::None()), 0);
  FOW_EXPECT_EQ(Evaluate(start, kBlack, FogContext::None()), 0);
}

// Evaluating from the two points of view must give exactly opposite numbers,
// which is what lets negamax negate scores as it unwinds.
void EvaluationIsAntisymmetric() {
  const char* fens[] = {
      kStartFen,
      "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
      "8/PPPk4/8/8/8/8/4Kppp/8 w - - 0 1",
      "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
  };
  for (const char* fen : fens) {
    const Position position = Parse(fen);
    FOW_EXPECT_EQ(Evaluate(position, kWhite, FogContext::None()),
                  -Evaluate(position, kBlack, FogContext::None()));
  }
}

// Mirroring a position colour-for-colour must negate its score. This catches an
// asymmetric table or a sign slip in any term.
void MirroredPositionsScoreOppositely() {
  const Position white_rook = Parse("4k3/8/8/8/8/8/8/R3K3 w - - 0 1");
  const Position black_rook = Parse("r3k3/8/8/8/8/8/8/4K3 w - - 0 1");
  FOW_EXPECT_EQ(Evaluate(white_rook, kWhite, FogContext::None()),
                Evaluate(black_rook, kBlack, FogContext::None()));
}

void MaterialDominatesAndIsSigned() {
  const Position balanced = Parse(kStartFen);
  const Position down_a_rook =
      Parse("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1");
  const int delta = Evaluate(down_a_rook, kWhite, FogContext::None()) -
                    Evaluate(balanced, kWhite, FogContext::None());
  // Losing a rook must cost close to a rook; placement terms shift it a little.
  FOW_EXPECT_TRUE(delta < -400);
  FOW_EXPECT_TRUE(delta > -600);
}

// The opening king sits behind its own pawns, so no fog line reaches it and the
// penalty must be zero. If this ever becomes non-zero the bot will start
// shuffling its king for no reason.
void ShelteredKingHasNoFogDanger() {
  const Position start = Parse(kStartFen);
  FOW_EXPECT_EQ(FogDanger(start, kWhite, WhiteFacingFog()), 0);
}

// A king on an open file facing unseen territory must be penalised, and more so
// the more fog bears on it.
void ExposedKingIsPenalisedInProportionToFog() {
  // e-file torn open in front of the king.
  const Position exposed =
      Parse("rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNBQKBNR w - - 0 1");
  const int danger = FogDanger(exposed, kWhite, WhiteFacingFog());
  FOW_EXPECT_TRUE(danger > 0);

  // A king marched into the middle of the board sees far more fog.
  const Position marched = Parse("rnbqkbnr/pppppppp/8/8/4K3/8/PPPPPPPP/RNBQ1BNR w - - 0 1");
  FOW_EXPECT_TRUE(FogDanger(marched, kWhite, WhiteFacingFog()) > danger);

  // And the penalty is capped so a maybe never outweighs real material.
  FOW_EXPECT_TRUE(FogDanger(marched, kWhite, WhiteFacingFog()) <=
                  kFogPenaltyCap);
}

// With no enemy sliders left there is nothing to hide on those lines, so the
// corresponding penalty must vanish.
void FogDangerRespectsTheRemainingEnemyArmy() {
  const Position exposed =
      Parse("rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNBQKBNR w - - 0 1");
  FogContext fog = WhiteFacingFog();
  const int full = FogDanger(exposed, kWhite, fog);
  fog.rook_like = 0;
  fog.bishop_like = 0;
  fog.knights = 0;
  fog.pawns = 0;
  FOW_EXPECT_EQ(FogDanger(exposed, kWhite, fog), 0);
  FOW_EXPECT_TRUE(full > 0);
}

// An empty fog mask must disable the term entirely.
void NoFogMeansNoFogTerm() {
  const Position marched =
      Parse("rnbqkbnr/pppppppp/8/8/4K3/8/PPPPPPPP/RNBQ1BNR w - - 0 1");
  FOW_EXPECT_EQ(FogDanger(marched, kWhite, FogContext::None()), 0);
  FogContext fog = WhiteFacingFog();
  fog.unseen = 0;
  FOW_EXPECT_EQ(FogDanger(marched, kWhite, fog), 0);
}

// The fog term must lower our own score, never raise it. A sign error here
// would make the bot walk its king into the open on purpose.
void FogExposureLowersOurOwnScore() {
  const Position marched =
      Parse("rnbqkbnr/pppppppp/8/8/4K3/8/PPPPPPPP/RNBQ1BNR w - - 0 1");
  const int without = Evaluate(marched, kWhite, FogContext::None());
  const int with = Evaluate(marched, kWhite, WhiteFacingFog());
  FOW_EXPECT_TRUE(with < without);

  // Symmetrically for Black.
  FogContext black_fog = WhiteFacingFog();
  black_fog.side = kBlack;
  black_fog.unseen = ~RanksFiveToEight();
  const Position black_marched =
      Parse("rnbq1bnr/pppppppp/8/4k3/8/8/PPPPPPPP/RNBQKBNR w - - 0 1");
  FOW_EXPECT_TRUE(Evaluate(black_marched, kBlack, black_fog) <
                  Evaluate(black_marched, kBlack, FogContext::None()));
}

void KingPressureRewardsAttackingTheEnemyKing() {
  // A rook bearing down the seventh rank next to the enemy king.
  const Position pressing = Parse("4k3/R7/8/8/8/8/8/4K3 w - - 0 1");
  const Position idle = Parse("4k3/8/8/8/8/8/R7/4K3 w - - 0 1");
  FOW_EXPECT_TRUE(Evaluate(pressing, kWhite, FogContext::None()) >
                  Evaluate(idle, kWhite, FogContext::None()));
}

void PassedPawnsAreRewardedByAdvancement() {
  const Position far = Parse("4k3/8/8/8/8/8/P7/4K3 w - - 0 1");
  const Position near_promotion = Parse("4k3/P7/8/8/8/8/8/4K3 w - - 0 1");
  FOW_EXPECT_TRUE(Evaluate(near_promotion, kWhite, FogContext::None()) >
                  Evaluate(far, kWhite, FogContext::None()));
}

void BishopPairIsRewarded() {
  const Position pair = Parse("4k3/8/8/8/8/8/8/2BBK3 w - - 0 1");
  const Position mixed = Parse("4k3/8/8/8/8/8/8/2BNK3 w - - 0 1");
  // Two bishops beat bishop plus knight by roughly the pair bonus plus the
  // small material difference.
  FOW_EXPECT_TRUE(Evaluate(pair, kWhite, FogContext::None()) >
                  Evaluate(mixed, kWhite, FogContext::None()));
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::StartingPositionIsBalanced);
  FOW_RUN_TEST(fow::EvaluationIsAntisymmetric);
  FOW_RUN_TEST(fow::MirroredPositionsScoreOppositely);
  FOW_RUN_TEST(fow::MaterialDominatesAndIsSigned);
  FOW_RUN_TEST(fow::ShelteredKingHasNoFogDanger);
  FOW_RUN_TEST(fow::ExposedKingIsPenalisedInProportionToFog);
  FOW_RUN_TEST(fow::FogDangerRespectsTheRemainingEnemyArmy);
  FOW_RUN_TEST(fow::NoFogMeansNoFogTerm);
  FOW_RUN_TEST(fow::FogExposureLowersOurOwnScore);
  FOW_RUN_TEST(fow::KingPressureRewardsAttackingTheEnemyKing);
  FOW_RUN_TEST(fow::PassedPawnsAreRewardedByAdvancement);
  FOW_RUN_TEST(fow::BishopPairIsRewarded);
  return fow::testing::Summarize("evaluation_test");
}
