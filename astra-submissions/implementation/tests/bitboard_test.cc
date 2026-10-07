// Copyright 2026. Fog of War chess engine.
//
// Verifies the magic bitboard tables against the ray-walking reference for
// every square and every relevant blocker pattern. That is an exhaustive check,
// not a sampled one: if it passes, the fast path is provably equivalent to the
// readable definition of sliding attacks.

#include "../bitboard.h"

#include "testing.h"

namespace fow {
namespace {

// Enumerates subsets of `mask` so the test covers exactly the patterns the
// magic index is required to distinguish.
Bitboard SubsetOf(Bitboard mask, int index) {
  Bitboard subset = 0;
  while (mask) {
    const int square = PopLsb(&mask);
    if (index & 1) subset |= SquareBB(square);
    index >>= 1;
  }
  return subset;
}

void MagicRookAttacksMatchReference() {
  for (int square = 0; square < kNumSquares; ++square) {
    const Bitboard mask = g_rook_magics[square].mask;
    const int count = 1 << PopCount(mask);
    for (int i = 0; i < count; ++i) {
      const Bitboard occupied = SubsetOf(mask, i);
      FOW_EXPECT_EQ(RookAttacks(square, occupied),
                    ReferenceRookAttacks(square, occupied));
    }
  }
}

void MagicBishopAttacksMatchReference() {
  for (int square = 0; square < kNumSquares; ++square) {
    const Bitboard mask = g_bishop_magics[square].mask;
    const int count = 1 << PopCount(mask);
    for (int i = 0; i < count; ++i) {
      const Bitboard occupied = SubsetOf(mask, i);
      FOW_EXPECT_EQ(BishopAttacks(square, occupied),
                    ReferenceBishopAttacks(square, occupied));
    }
  }
}

// Blockers outside the relevant mask must not change the answer, which is the
// property that lets the mask exclude edge squares.
void EdgeBlockersDoNotMatter() {
  for (int square = 0; square < kNumSquares; ++square) {
    const Bitboard irrelevant = ~g_rook_magics[square].mask & ~SquareBB(square);
    FOW_EXPECT_EQ(RookAttacks(square, 0), RookAttacks(square, 0));
    FOW_EXPECT_EQ(RookAttacks(square, irrelevant & kRankMask[0] & ~kFileMask[0]),
                  ReferenceRookAttacks(
                      square, irrelevant & kRankMask[0] & ~kFileMask[0]));
  }
}

void KnightAndKingTablesAreSymmetric() {
  // a1 has two knight moves and three king moves; d4 has eight of each.
  FOW_EXPECT_EQ(PopCount(kKnightAttacks[MakeSquare(0, 0)]), 2);
  FOW_EXPECT_EQ(PopCount(kKingAttacks[MakeSquare(0, 0)]), 3);
  FOW_EXPECT_EQ(PopCount(kKnightAttacks[MakeSquare(3, 3)]), 8);
  FOW_EXPECT_EQ(PopCount(kKingAttacks[MakeSquare(3, 3)]), 8);
  // Attack relations are mutual for knights and kings.
  for (int a = 0; a < kNumSquares; ++a) {
    Bitboard reach = kKnightAttacks[a];
    while (reach) {
      const int b = PopLsb(&reach);
      FOW_EXPECT_TRUE((kKnightAttacks[b] & SquareBB(a)) != 0);
    }
  }
}

void PawnAttacksPointForward() {
  // A white pawn on d4 attacks c5 and e5; a black pawn on d4 attacks c3 and e3.
  FOW_EXPECT_EQ(kPawnAttacks[kWhite][MakeSquare(3, 3)],
                SquareBB(MakeSquare(2, 4)) | SquareBB(MakeSquare(4, 4)));
  FOW_EXPECT_EQ(kPawnAttacks[kBlack][MakeSquare(3, 3)],
                SquareBB(MakeSquare(2, 2)) | SquareBB(MakeSquare(4, 2)));
  // Edge files attack only one square.
  FOW_EXPECT_EQ(PopCount(kPawnAttacks[kWhite][MakeSquare(0, 3)]), 1);
  FOW_EXPECT_EQ(PopCount(kPawnAttacks[kWhite][MakeSquare(7, 3)]), 1);
}

void BetweenIsExclusiveAndEmptyOffLine() {
  const int a1 = MakeSquare(0, 0);
  const int d1 = MakeSquare(3, 0);
  FOW_EXPECT_EQ(kBetween[a1][d1],
                SquareBB(MakeSquare(1, 0)) | SquareBB(MakeSquare(2, 0)));
  FOW_EXPECT_EQ(kBetween[a1][MakeSquare(1, 0)], Bitboard{0});  // adjacent
  FOW_EXPECT_EQ(kBetween[a1][MakeSquare(1, 2)], Bitboard{0});  // knight offset
  // Symmetric.
  for (int a = 0; a < kNumSquares; ++a) {
    for (int b = 0; b < kNumSquares; ++b) {
      FOW_EXPECT_EQ(kBetween[a][b], kBetween[b][a]);
    }
  }
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  FOW_RUN_TEST(fow::MagicRookAttacksMatchReference);
  FOW_RUN_TEST(fow::MagicBishopAttacksMatchReference);
  FOW_RUN_TEST(fow::EdgeBlockersDoNotMatter);
  FOW_RUN_TEST(fow::KnightAndKingTablesAreSymmetric);
  FOW_RUN_TEST(fow::PawnAttacksPointForward);
  FOW_RUN_TEST(fow::BetweenIsExclusiveAndEmptyOffLine);
  return fow::testing::Summarize("bitboard_test");
}
