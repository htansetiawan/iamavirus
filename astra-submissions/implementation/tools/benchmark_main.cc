#include <chrono>
#include <cstdio>
#include "../bitboard.h"
#include "../evaluation.h"
#include "../position.h"
#include "../search.h"
int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  fow::TranspositionTable table;
  table.Resize(128);
  fow::Position start;
  fow::PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &start);
  for (double budget : {1.0, 4.0}) {
    table.Clear();
    fow::Searcher searcher(&table);
    searcher.SetContext(fow::kWhite, true, fow::FogContext::None());
    fow::MoveList moves;
    start.GenerateMoves(&moves);
    fow::SearchLimits limits;
    limits.seconds = budget;
    const auto t0 = std::chrono::steady_clock::now();
    const fow::SearchResult result = searcher.Search(&start, moves, limits);
    const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::printf("budget=%.1fs -> depth %d, %llu nodes, %.0f nps, best %s\n",
                budget, result.depth, (unsigned long long)result.nodes,
                result.nodes / elapsed, fow::MoveToUci(result.best_move).c_str());
  }
  return 0;
}
