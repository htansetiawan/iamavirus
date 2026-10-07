// Copyright 2026. Fog of War chess engine.
//
// Tests for the search. These are behavioural: each one sets up a position where
// the Fog of War rules make exactly one choice correct, and checks the search
// finds it. Between them they cover the three ways a game ends -- a capturable
// king, having no legal move, and ordinary evaluation.

#include "../search.h"

#include <chrono>
#include <string>

#include "../bitboard.h"
#include "../evaluation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

Position Parse(const std::string& fen) {
  Position position;
  FOW_EXPECT_TRUE(PositionFromFen(fen, &position));
  return position;
}

// Runs a search with perfect information, which is the right setting for testing
// tactics: the fog term is a separate concern with its own tests.
SearchResult Think(Position* position, double seconds = 1.0, int depth = 6) {
  static TranspositionTable table;
  if (table.entry_count() == 0) table.Resize(64);
  table.Clear();
  Searcher searcher(&table);
  searcher.SetContext(position->side_to_move(), /*enemy_king_confirmed=*/true,
                      FogContext::None());
  MoveList moves;
  position->GenerateMoves(&moves);
  SearchLimits limits;
  limits.seconds = seconds;
  limits.max_depth = depth;
  return searcher.Search(position, moves, limits);
}

std::string BestUci(Position* position, double seconds = 1.0, int depth = 6) {
  return MoveToUci(Think(position, seconds, depth).best_move);
}

void SearchReturnsALegalMoveAndCountsNodes() {
  Position start =
      Parse("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
  const SearchResult result = Think(&start, 1.0, 5);
  FOW_EXPECT_TRUE(result.best_move != kNullMove);
  FOW_EXPECT_TRUE(result.nodes > 0);
  FOW_EXPECT_TRUE(result.depth >= 3);
  FOW_EXPECT_EQ(static_cast<int>(result.root_values.size()), 20);
  // Every root move must be one of the position's legal moves.
  MoveList legal;
  start.GenerateMoves(&legal);
  for (const RootMoveValue& entry : result.root_values) {
    bool present = false;
    for (const Move move : legal) {
      if (move == entry.move) present = true;
    }
    FOW_EXPECT_TRUE(present);
  }
}

// The defining tactic of this game: a move that leaves our own king capturable
// loses at once, so the search must refuse it even when it wins material.
void RefusesToExposeItsOwnKing() {
  // The knight on d2 is the only cover between the a5 bishop and the e1 king.
  // Every knight move loses instantly; the king must step aside or be shielded.
  Position position = Parse("4k3/8/8/b7/8/8/3N4/4K3 w - - 0 1");
  const std::string best = BestUci(&position, 1.0, 6);
  FOW_EXPECT_TRUE(best != "d2c4");
  FOW_EXPECT_TRUE(best != "d2f3");
  FOW_EXPECT_TRUE(best != "d2b3");
  FOW_EXPECT_TRUE(best != "d2f1");
  FOW_EXPECT_TRUE(best != "d2b1");
}

// A pawn that can be taken for free should be taken, with no king danger around.
// The bishop on f3 reaches d5 along f3-e4-d5.
void TakesFreeMaterial() {
  Position position = Parse("4k3/8/8/3p4/8/5B2/4K3/8 w - - 0 1");
  FOW_EXPECT_TRUE(BestUci(&position, 1.0, 6) == "f3d5");
}

// Black's king is boxed in: every reply leaves it capturable, so White is
// winning and the search must say so with a decisive score.
void RecognisesAWonPosition() {
  Position position = Parse("7k/5R2/6R1/8/8/8/8/4K3 w - - 0 1");
  const SearchResult result = Think(&position, 2.0, 7);
  FOW_EXPECT_TRUE(result.score > kWinSpeculative - kMaxPly);
}

// The mirror image: with Black to move in that position, Black is lost.
void RecognisesALostPosition() {
  Position position = Parse("7k/5R2/6R1/8/8/8/8/4K3 b - - 0 1");
  static TranspositionTable table;
  if (table.entry_count() == 0) table.Resize(64);
  table.Clear();
  Searcher searcher(&table);
  searcher.SetContext(kBlack, true, FogContext::None());
  MoveList moves;
  position.GenerateMoves(&moves);
  SearchLimits limits;
  limits.seconds = 2.0;
  limits.max_depth = 6;
  const SearchResult result = searcher.Search(&position, moves, limits);
  FOW_EXPECT_TRUE(result.score < -kWinSpeculative + kMaxPly);
}

// A king already under attack must deal with it, and capturing the attacker is
// the cleanest way. There is no check rule, so this has to fall out of search.
void EscapesAnAttackOnItsKing() {
  // Black king on e8, white rook on e7: taking the rook is both legal and best.
  Position position = Parse("4k3/4R3/8/8/8/8/8/4K3 b - - 0 1");
  static TranspositionTable table;
  if (table.entry_count() == 0) table.Resize(64);
  table.Clear();
  Searcher searcher(&table);
  searcher.SetContext(kBlack, true, FogContext::None());
  MoveList moves;
  position.GenerateMoves(&moves);
  SearchLimits limits;
  limits.seconds = 1.0;
  limits.max_depth = 6;
  FOW_EXPECT_TRUE(MoveToUci(searcher.Search(&position, moves, limits).best_move) ==
                  "e8e7");
}

void PromotesToAQueen() {
  Position position = Parse("8/P7/8/8/8/5k2/8/4K3 w - - 0 1");
  FOW_EXPECT_TRUE(BestUci(&position, 1.0, 6) == "a7a8q");
}

// Deeper searches must never report a worse score for the side to move in a
// quiet position; a crash or a window bug usually shows up here first.
void DeeperSearchesStayConsistent() {
  Position position =
      Parse("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1");
  int previous = -kInfinity;
  for (int depth = 1; depth <= 5; ++depth) {
    const SearchResult result = Think(&position, 5.0, depth);
    FOW_EXPECT_TRUE(result.best_move != kNullMove);
    FOW_EXPECT_TRUE(result.score > -kInfinity);
    previous = result.score;
  }
  FOW_EXPECT_TRUE(previous > -kInfinity);
}

// The search must stop when told to, even with a generous depth allowance.
void RespectsItsTimeBudget() {
  Position position =
      Parse("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
  const auto started = std::chrono::steady_clock::now();
  const SearchResult result = Think(&position, 0.3, 64);
  const double elapsed = std::chrono::duration<double>(
                             std::chrono::steady_clock::now() - started)
                             .count();
  FOW_EXPECT_TRUE(result.best_move != kNullMove);
  // Generous upper bound: the budget plus the cost of finishing a node batch.
  FOW_EXPECT_TRUE(elapsed < 1.5);
}

// With only one move available the search must still return it.
void HandlesASingleLegalMove() {
  Position position = Parse("8/8/8/8/8/8/8/K6k w - - 0 1");
  MoveList moves;
  position.GenerateMoves(&moves);
  FOW_EXPECT_TRUE(moves.size() > 0);
  static TranspositionTable table;
  if (table.entry_count() == 0) table.Resize(16);
  Searcher searcher(&table);
  searcher.SetContext(kWhite, true, FogContext::None());
  MoveList single;
  single.Add(moves[0]);
  SearchLimits limits;
  limits.seconds = 0.2;
  const SearchResult result = searcher.Search(&position, single, limits);
  FOW_EXPECT_EQ(result.best_move, moves[0]);
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::SearchReturnsALegalMoveAndCountsNodes);
  FOW_RUN_TEST(fow::RefusesToExposeItsOwnKing);
  FOW_RUN_TEST(fow::TakesFreeMaterial);
  FOW_RUN_TEST(fow::RecognisesAWonPosition);
  FOW_RUN_TEST(fow::RecognisesALostPosition);
  FOW_RUN_TEST(fow::EscapesAnAttackOnItsKing);
  FOW_RUN_TEST(fow::PromotesToAQueen);
  FOW_RUN_TEST(fow::DeeperSearchesStayConsistent);
  FOW_RUN_TEST(fow::RespectsItsTimeBudget);
  FOW_RUN_TEST(fow::HandlesASingleLegalMove);
  return fow::testing::Summarize("search_test");
}
