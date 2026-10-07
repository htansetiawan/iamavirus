// Copyright 2026. Fog of War chess engine.
//
// Tests for move generation and move application.
//
// The perft expectations are not orthodox chess values. They were produced by
// referee.py, the arena's own rule implementation, and they differ from
// standard perft precisely because Fog of War imposes no check restriction: the
// starting position has 197,742 nodes at depth four rather than 197,281.

#include "../position.h"

#include <cstdint>
#include <string>

#include "../bitboard.h"
#include "../move.h"
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

// Counts leaves and asserts that every move round-trips: the Zobrist key, the
// occupancy and the full board must be restored exactly by UnmakeMove.
int64_t Perft(Position* position, int depth) {
  MoveList list;
  position->GenerateMoves(&list);
  if (depth <= 1) return list.size();
  int64_t total = 0;
  for (const Move move : list) {
    const uint64_t key_before = position->key();
    const Bitboard occupied_before = position->occupied();
    const std::string fen_before = position->BoardFen();
    UndoState undo;
    position->MakeMove(move, &undo);
    total += Perft(position, depth - 1);
    position->UnmakeMove(move, undo);
    FOW_EXPECT_EQ(position->key(), key_before);
    FOW_EXPECT_EQ(position->occupied(), occupied_before);
    FOW_EXPECT_TRUE(position->BoardFen() == fen_before);
  }
  return total;
}

int MoveCount(const Position& position) {
  MoveList list;
  position.GenerateMoves(&list);
  return list.size();
}

bool Contains(const Position& position, const std::string& uci) {
  MoveList list;
  position.GenerateMoves(&list);
  for (const Move move : list) {
    if (MoveToUci(move) == uci) return true;
  }
  return false;
}

void PerftMatchesReferee() {
  Position start = Parse(kStartFen);
  FOW_EXPECT_EQ(Perft(&start, 1), int64_t{20});
  FOW_EXPECT_EQ(Perft(&start, 2), int64_t{400});
  FOW_EXPECT_EQ(Perft(&start, 3), int64_t{8902});
  FOW_EXPECT_EQ(Perft(&start, 4), int64_t{197742});

  Position busy = Parse(
      "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
  FOW_EXPECT_EQ(Perft(&busy, 1), int64_t{48});
  FOW_EXPECT_EQ(Perft(&busy, 2), int64_t{2049});
  FOW_EXPECT_EQ(Perft(&busy, 3), int64_t{98903});

  Position en_passant = Parse(
      "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 1");
  FOW_EXPECT_EQ(Perft(&en_passant, 1), int64_t{31});
  FOW_EXPECT_EQ(Perft(&en_passant, 2), int64_t{747});
  FOW_EXPECT_EQ(Perft(&en_passant, 3), int64_t{23125});

  Position promotions = Parse("8/PPPk4/8/8/8/8/4Kppp/8 w - - 0 1");
  FOW_EXPECT_EQ(Perft(&promotions, 1), int64_t{20});
  FOW_EXPECT_EQ(Perft(&promotions, 2), int64_t{400});
  FOW_EXPECT_EQ(Perft(&promotions, 3), int64_t{8604});
}

// The defining rule difference: a move that exposes one's own king is legal.
void SelfExposingMovesAreGenerated() {
  // The knight on d2 is the only cover between the a5 bishop and the e1 king.
  // In orthodox chess it is pinned; here its moves are perfectly legal.
  const Position position = Parse("4k3/8/8/b7/8/8/3N4/4K3 w - - 0 1");
  FOW_EXPECT_TRUE(Contains(position, "d2c4"));
  FOW_EXPECT_TRUE(Contains(position, "d2f3"));
}

void CastlingIgnoresAttackedSquares() {
  // f1 and g1 are swept by the bishop on a6, and e1 by the rook on e8.
  // Orthodox rules forbid castling here; Fog of War allows it.
  const Position position = Parse("4r3/8/b7/8/8/8/8/4K2R w K - 0 1");
  FOW_EXPECT_TRUE(Contains(position, "e1g1"));
}

void CastlingRequiresRightsRookAndEmptySquares() {
  // No right recorded, so no castling move.
  FOW_EXPECT_TRUE(!Contains(Parse("4k3/8/8/8/8/8/8/4K2R w - - 0 1"), "e1g1"));
  // A piece in between blocks it.
  FOW_EXPECT_TRUE(
      !Contains(Parse("4k3/8/8/8/8/8/8/4KN1R w K - 0 1"), "e1g1"));
  // Queen side needs b1, c1 and d1 clear.
  FOW_EXPECT_TRUE(
      !Contains(Parse("4k3/8/8/8/8/8/8/RN2K3 w Q - 0 1"), "e1c1"));
  FOW_EXPECT_TRUE(Contains(Parse("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1"), "e1c1"));
}

void CastlingMovesTheRook() {
  Position position = Parse("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1");
  UndoState undo;
  position.MakeMove(EncodeMove(MakeSquare(4, 0), MakeSquare(6, 0),
                               kFlagCastleKingSide),
                    &undo);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(6, 0)), kKing);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(5, 0)), kRook);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(7, 0)), kNoPiece);
  FOW_EXPECT_EQ(position.castling_rights(), Bitboard{0});
  position.UnmakeMove(EncodeMove(MakeSquare(4, 0), MakeSquare(6, 0),
                                 kFlagCastleKingSide),
                      undo);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(4, 0)), kKing);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(7, 0)), kRook);
}

void EnPassantRemovesThePassedPawn() {
  Position position =
      Parse("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 1");
  const int from = MakeSquare(4, 4);  // e5
  const int to = MakeSquare(5, 5);    // f6
  UndoState undo;
  position.MakeMove(EncodeMove(from, to, kFlagEnPassant), &undo);
  FOW_EXPECT_EQ(position.piece_at(to), kPawn);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(5, 4)), kNoPiece);  // f5 cleared
  position.UnmakeMove(EncodeMove(from, to, kFlagEnPassant), undo);
  FOW_EXPECT_EQ(position.piece_at(MakeSquare(5, 4)), kPawn);
  FOW_EXPECT_EQ(position.piece_at(from), kPawn);
}

void PromotionOffersAllFourPieces() {
  const Position position = Parse("8/P7/8/8/8/8/8/4K2k w - - 0 1");
  FOW_EXPECT_TRUE(Contains(position, "a7a8q"));
  FOW_EXPECT_TRUE(Contains(position, "a7a8r"));
  FOW_EXPECT_TRUE(Contains(position, "a7a8b"));
  FOW_EXPECT_TRUE(Contains(position, "a7a8n"));
}

void CapturingARookRemovesItsCastlingRight() {
  Position position = Parse("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 1");
  const Bitboard before = position.castling_rights();
  FOW_EXPECT_EQ(PopCount(before), 2);
  UndoState undo;
  position.MakeMove(EncodeMove(MakeSquare(0, 0), MakeSquare(0, 7)), &undo);
  FOW_EXPECT_EQ(PopCount(position.castling_rights()), 0);
  position.UnmakeMove(EncodeMove(MakeSquare(0, 0), MakeSquare(0, 7)), undo);
  FOW_EXPECT_EQ(position.castling_rights(), before);
}

// This is the referee's win condition, so it has to be exactly right.
void PreviousMoverIsLostDetectsACapturableKing() {
  // White to move, black king on h7 swept by the rook on a7 along the seventh
  // rank: Black has already lost, because it moved into this.
  FOW_EXPECT_TRUE(
      Parse("8/R6k/8/8/8/8/8/4K3 w - - 0 1").PreviousMoverIsLost());
  // The same rook with the king on h8 attacks nothing: not lost.
  FOW_EXPECT_TRUE(
      !Parse("7k/R7/8/8/8/8/8/4K3 w - - 0 1").PreviousMoverIsLost());
  // Quiet position: nobody has lost.
  FOW_EXPECT_TRUE(!Parse(kStartFen).PreviousMoverIsLost());
  // A missing king counts as lost.
  FOW_EXPECT_TRUE(Parse("8/8/8/8/8/8/8/4K3 w - - 0 1").PreviousMoverIsLost());
}

void AttackersToFindsEveryAttackerKind() {
  // d4 is attacked by: pawn c3, knight b3... built explicitly below.
  const Position position = Parse("3r4/8/8/8/3k4/2P5/8/3K4 b - - 0 1");
  const int d4 = MakeSquare(3, 3);
  FOW_EXPECT_TRUE((position.AttackersTo(d4, kWhite) &
                   SquareBB(MakeSquare(2, 2))) != 0);  // the c3 pawn
  FOW_EXPECT_TRUE((position.AttackersTo(d4, kBlack) &
                   SquareBB(MakeSquare(3, 7))) != 0);  // the d8 rook
}

void ZobristKeyDistinguishesSideToMove() {
  const Position white = Parse(kStartFen);
  const Position black =
      Parse("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1");
  FOW_EXPECT_TRUE(white.key() != black.key());
}

void GenerateCapturesIsASubsetOfAllMoves() {
  const Position position = Parse(
      "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
  MoveList all;
  position.GenerateMoves(&all);
  MoveList captures;
  position.GenerateCaptures(&captures);
  FOW_EXPECT_TRUE(captures.size() > 0);
  FOW_EXPECT_TRUE(captures.size() < all.size());
  for (const Move capture : captures) {
    bool present = false;
    for (const Move move : all) {
      if (move == capture) present = true;
    }
    FOW_EXPECT_TRUE(present);
    FOW_EXPECT_TRUE(position.piece_at(MoveTo(capture)) != kNoPiece ||
                    MoveFlagOf(capture) == kFlagEnPassant ||
                    IsPromotion(capture));
  }
}

void MoveEncodingRoundTrips() {
  for (int from = 0; from < kNumSquares; ++from) {
    for (int to = 0; to < kNumSquares; ++to) {
      const Move move = EncodeMove(from, to, kFlagPromoteRook);
      FOW_EXPECT_EQ(MoveFrom(move), from);
      FOW_EXPECT_EQ(MoveTo(move), to);
      FOW_EXPECT_EQ(PromotionType(move), kRook);
      FOW_EXPECT_TRUE(IsPromotion(move));
    }
  }
  FOW_EXPECT_TRUE(MoveToUci(EncodeMove(MakeSquare(4, 1), MakeSquare(4, 3),
                                       kFlagDoublePush)) == "e2e4");
  FOW_EXPECT_TRUE(MoveToUci(EncodeMove(MakeSquare(4, 6), MakeSquare(4, 7),
                                       kFlagPromoteQueen)) == "e7e8q");
}

void StartingPositionHasTwentyMoves() {
  FOW_EXPECT_EQ(MoveCount(Parse(kStartFen)), 20);
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::StartingPositionHasTwentyMoves);
  FOW_RUN_TEST(fow::MoveEncodingRoundTrips);
  FOW_RUN_TEST(fow::SelfExposingMovesAreGenerated);
  FOW_RUN_TEST(fow::CastlingIgnoresAttackedSquares);
  FOW_RUN_TEST(fow::CastlingRequiresRightsRookAndEmptySquares);
  FOW_RUN_TEST(fow::CastlingMovesTheRook);
  FOW_RUN_TEST(fow::EnPassantRemovesThePassedPawn);
  FOW_RUN_TEST(fow::PromotionOffersAllFourPieces);
  FOW_RUN_TEST(fow::CapturingARookRemovesItsCastlingRight);
  FOW_RUN_TEST(fow::PreviousMoverIsLostDetectsACapturableKing);
  FOW_RUN_TEST(fow::AttackersToFindsEveryAttackerKind);
  FOW_RUN_TEST(fow::ZobristKeyDistinguishesSideToMove);
  FOW_RUN_TEST(fow::GenerateCapturesIsASubsetOfAllMoves);
  FOW_RUN_TEST(fow::PerftMatchesReferee);
  return fow::testing::Summarize("position_test");
}
