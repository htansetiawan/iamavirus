// Copyright 2026. Fog of War chess engine.
//
// Tests for observation parsing, visibility and exact legal move extraction.

#include "../observation.h"

#include <cstdio>
#include <random>

#include <string>

#include "../bitboard.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

// What White sees before its first move, quoted from the course documentation.
constexpr char kInitialWhiteView[] =
    "RNBQKBNRPPPPPPPP----------------"
    "????????????????????????????????";

constexpr char kStartFen[] =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

Bitboard RanksOneToFour() {
  Bitboard mask = 0;
  for (int square = 0; square < 32; ++square) mask |= SquareBB(square);
  return mask;
}

MoveList LegalMoves(const Observation& observation, int side,
                    Bitboard castling, int en_passant) {
  Position visible;
  VisiblePositionFromObservation(observation, side, castling, en_passant,
                                 &visible);
  MoveList list;
  LegalMovesFromObservation(visible, observation, &list);
  return list;
}

bool Contains(const MoveList& list, const std::string& uci) {
  for (const Move move : list) {
    if (MoveToUci(move) == uci) return true;
  }
  return false;
}

void ValidationRejectsMalformedObservations() {
  FOW_EXPECT_TRUE(Observation::IsValid(kInitialWhiteView));
  FOW_EXPECT_TRUE(!Observation::IsValid("short"));
  FOW_EXPECT_TRUE(!Observation::IsValid(std::string(64, 'x')));
  FOW_EXPECT_TRUE(Observation::IsValid(std::string(64, '?')));
  FOW_EXPECT_TRUE(Observation::IsValid(std::string(64, '-')));
}

// The documented example: White's initial view is exactly ranks one to four.
// This is also the clearest statement of the visibility rule -- the visible set
// is our own pieces plus every square we could move to.
void InitialVisibilityIsRanksOneToFour() {
  Position start;
  FOW_EXPECT_TRUE(PositionFromFen(kStartFen, &start));
  FOW_EXPECT_EQ(VisibleSquares(start, kWhite), RanksOneToFour());

  const Observation view(kInitialWhiteView);
  FOW_EXPECT_EQ(view.UnseenMask(), ~RanksOneToFour());
  FOW_EXPECT_EQ(PopCount(view.VisiblePieces(kWhite)), 16);
  FOW_EXPECT_EQ(PopCount(view.VisiblePieces(kBlack)), 0);
  FOW_EXPECT_EQ(PopCount(view.VisiblePieces(kWhite, kPawn)), 8);
  FOW_EXPECT_EQ(PopCount(view.VisiblePieces(kWhite, kKing)), 1);
}

// Black's initial view is the mirror image: ranks five to eight.
void InitialVisibilityIsSymmetric() {
  Position start;
  FOW_EXPECT_TRUE(PositionFromFen(kStartFen, &start));
  FOW_EXPECT_EQ(VisibleSquares(start, kBlack), ~RanksOneToFour());
}

void InitialObservationYieldsTwentyLegalMoves() {
  const MoveList list = LegalMoves(Observation(kInitialWhiteView), kWhite, 0, -1);
  FOW_EXPECT_EQ(list.size(), 20);
  FOW_EXPECT_TRUE(Contains(list, "e2e4"));
  FOW_EXPECT_TRUE(Contains(list, "g1f3"));
}

// A destination we cannot see cannot be the target of a legal move, so it must
// never be generated.
void MovesIntoUnseenSquaresAreRejected() {
  // A lone rook on a1 with the a-file visible only as far as a4.
  std::string squares(64, kUnseen);
  squares[MakeSquare(0, 0)] = 'R';
  squares[MakeSquare(4, 0)] = 'K';
  for (int rank = 1; rank <= 3; ++rank) {
    squares[MakeSquare(0, rank)] = kEmpty;
  }
  for (int file = 1; file <= 3; ++file) {
    squares[MakeSquare(file, 0)] = kEmpty;
  }
  const MoveList list = LegalMoves(Observation(squares), kWhite, 0, -1);
  FOW_EXPECT_TRUE(Contains(list, "a1a4"));   // a2, a3 visible and empty
  FOW_EXPECT_TRUE(!Contains(list, "a1a5"));  // a5 itself is unseen
  FOW_EXPECT_TRUE(!Contains(list, "a1a6"));
}

// A slider may not be assumed to pass through fog.
void SlidersMayNotCrossUnseenSquares() {
  std::string squares(64, kUnseen);
  squares[MakeSquare(0, 0)] = 'R';
  squares[MakeSquare(4, 0)] = 'K';
  squares[MakeSquare(0, 1)] = kUnseen;  // a2 hidden
  squares[MakeSquare(0, 2)] = kEmpty;   // a3 somehow visible and empty
  const MoveList list = LegalMoves(Observation(squares), kWhite, 0, -1);
  // a3 is a visible empty square, but reaching it would cross the hidden a2.
  FOW_EXPECT_TRUE(!Contains(list, "a1a3"));
}

// Knights jump, so intervening fog is irrelevant to them.
void KnightsIgnoreInterveningFog() {
  std::string squares(64, kUnseen);
  squares[MakeSquare(1, 0)] = 'N';
  squares[MakeSquare(4, 0)] = 'K';
  squares[MakeSquare(2, 2)] = kEmpty;  // c3 visible and empty
  const MoveList list = LegalMoves(Observation(squares), kWhite, 0, -1);
  FOW_EXPECT_TRUE(Contains(list, "b1c3"));
}

void CastlingNeedsVisiblyEmptySquares() {
  std::string squares(64, kUnseen);
  squares[MakeSquare(4, 0)] = 'K';
  squares[MakeSquare(7, 0)] = 'R';
  const Bitboard rights = SquareBB(MakeSquare(7, 0));
  // f1 and g1 unseen: we cannot claim the castle is available.
  FOW_EXPECT_TRUE(
      !Contains(LegalMoves(Observation(squares), kWhite, rights, -1), "e1g1"));
  squares[MakeSquare(5, 0)] = kEmpty;
  squares[MakeSquare(6, 0)] = kEmpty;
  FOW_EXPECT_TRUE(
      Contains(LegalMoves(Observation(squares), kWhite, rights, -1), "e1g1"));
}

void EnPassantIsInferredFromConsecutiveObservations() {
  // Our pawn on e5; Black's d-pawn appears on d5 having crossed d6, with d7
  // becoming empty. The only consistent explanation is a double push.
  std::string before(64, kUnseen);
  std::string after(64, kUnseen);
  const int e5 = MakeSquare(4, 4);
  const int d5 = MakeSquare(3, 4);
  const int d6 = MakeSquare(3, 5);
  const int e1 = MakeSquare(4, 0);
  for (std::string* view : {&before, &after}) {
    (*view)[e5] = 'P';
    (*view)[e1] = 'K';
  }
  before[d5] = kEmpty;
  before[d6] = kEmpty;
  after[d5] = 'p';
  after[d6] = kEmpty;
  const Observation previous(before);
  const Observation current(after);
  FOW_EXPECT_EQ(InferEnPassant(&previous, current, kWhite), d6);

  // With no previous observation nothing can be inferred.
  FOW_EXPECT_EQ(InferEnPassant(nullptr, current, kWhite), -1);

  // If the pawn was already sitting on d5 beforehand, it did not just arrive.
  std::string settled = before;
  settled.at(static_cast<std::size_t>(d5)) = 'p';
  const Observation settled_view(settled);
  FOW_EXPECT_EQ(InferEnPassant(&settled_view, current, kWhite), -1);
}

// Losing one of our own pieces proves the opponent captured, so the appearance
// of an adjacent enemy pawn is not evidence of a double push.
void EnPassantIsNotInferredAfterACapture() {
  std::string before(64, kUnseen);
  std::string after(64, kUnseen);
  const int e5 = MakeSquare(4, 4);
  const int d5 = MakeSquare(3, 4);
  const int d6 = MakeSquare(3, 5);
  const int b2 = MakeSquare(1, 1);
  const int e1 = MakeSquare(4, 0);
  for (std::string* view : {&before, &after}) {
    (*view)[e5] = 'P';
    (*view)[e1] = 'K';
    (*view)[d6] = kEmpty;
  }
  before[b2] = 'P';     // a pawn of ours...
  after[b2] = kEmpty;   // ...that has vanished
  before[d5] = kEmpty;
  after[d5] = 'p';
  const Observation previous(before);
  const Observation current(after);
  FOW_EXPECT_EQ(InferEnPassant(&previous, current, kWhite), -1);
}

void VisibleSquaresRevealsEnPassantVictim() {
  // With an en passant capture available, the pawn that may be taken is visible
  // even though the capture lands on an empty square behind it.
  Position position;
  FOW_EXPECT_TRUE(PositionFromFen(
      "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 1",
      &position));
  const Bitboard seen = VisibleSquares(position, kWhite);
  FOW_EXPECT_TRUE((seen & SquareBB(MakeSquare(5, 4))) != 0);  // the f5 pawn
  FOW_EXPECT_TRUE((seen & SquareBB(MakeSquare(5, 5))) != 0);  // the f6 target
}

// What the visibility rule proves must be true on the real board, over random
// play: every square deduced to hold an enemy piece does, and every square
// deduced empty is.
void DeductionsHoldOnTheTrueBoard() {
  std::mt19937_64 rng(2026);
  int holds = 0;
  int empties = 0;
  for (int game = 0; game < 60; ++game) {
    Position truth;
    PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth);
    for (int ply = 0; ply < 80; ++ply) {
      for (const int side : {kWhite, kBlack}) {
        const Observation view(RenderObservation(truth, side));
        const Deductions deduced = DeduceFromObservation(view, side);
        Bitboard scan = deduced.must_hold_enemy;
        while (scan) {
          const int square = PopLsb(&scan);
          FOW_EXPECT_TRUE(truth.piece_at(square) != kNoPiece &&
                          truth.color_at(square) == (side ^ 1));
          FOW_EXPECT_TRUE(view.IsUnseen(square));
          ++holds;
        }
        scan = deduced.must_be_empty;
        while (scan) {
          const int square = PopLsb(&scan);
          FOW_EXPECT_TRUE(truth.piece_at(square) == kNoPiece);
          ++empties;
        }
      }
      MoveList legal;
      truth.GenerateMoves(&legal);
      if (legal.empty() || truth.PreviousMoverIsLost()) break;
      UndoState undo;
      truth.MakeMove(legal[rng() % legal.size()], &undo);
    }
  }
  FOW_EXPECT_TRUE(holds > 500);
  FOW_EXPECT_TRUE(empties > 500);
  std::fprintf(stderr, "       %d deduced enemy squares and %d deduced empty squares verified\n",
               holds, empties);
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::ValidationRejectsMalformedObservations);
  FOW_RUN_TEST(fow::InitialVisibilityIsRanksOneToFour);
  FOW_RUN_TEST(fow::InitialVisibilityIsSymmetric);
  FOW_RUN_TEST(fow::InitialObservationYieldsTwentyLegalMoves);
  FOW_RUN_TEST(fow::MovesIntoUnseenSquaresAreRejected);
  FOW_RUN_TEST(fow::SlidersMayNotCrossUnseenSquares);
  FOW_RUN_TEST(fow::KnightsIgnoreInterveningFog);
  FOW_RUN_TEST(fow::CastlingNeedsVisiblyEmptySquares);
  FOW_RUN_TEST(fow::EnPassantIsInferredFromConsecutiveObservations);
  FOW_RUN_TEST(fow::EnPassantIsNotInferredAfterACapture);
  FOW_RUN_TEST(fow::VisibleSquaresRevealsEnPassantVictim);
  FOW_RUN_TEST(fow::DeductionsHoldOnTheTrueBoard);
  return fow::testing::Summarize("observation_test");
}
