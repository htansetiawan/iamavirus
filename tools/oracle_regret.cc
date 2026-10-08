// Perfect-information regret of candidate moves, for the gym.
//
//   build/oracle_regret NODES < positions.txt > regrets.txt
//
// Each input line: <board64> <side 0|1> <castling rook-square bits> <en passant square or -1> <uci> [<uci> ...]
// Each output line: <best uci> <best value> then, for every input move, <uci>:<regret> where
// regret = value(best) - value(move) in centipawns from the mover's side, measured by a
// node-limited search of the true position with the fog term off (the opponent sees
// everything too). A move that leaves our king capturable scores the loss value; regrets
// are capped at 3000 so a single lost king does not swamp an average.
//
// This prices every trade-off in one number, which the single-capability corpora
// (strike, giveaway) could not: a strike that hangs a rook shows up as regret here.
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "../bitboard.h"
#include "../observation.h"
#include "../evaluation.h"
#include "../move.h"
#include "../position.h"
#include "../search.h"
#include "../transposition.h"

using namespace fow;

namespace {

Move FindUci(const Position& position, const std::string& uci) {
  MoveList legal;
  position.GenerateMoves(&legal);
  for (const Move m : legal) {
    if (MoveToUci(m) == uci) return m;
  }
  return kNullMove;
}

// Value of `move` for the side to move in `root`, by searching the opponent's replies.
int ValueAfter(Searcher* searcher, TranspositionTable* table, const Position& root, Move move, uint64_t nodes) {
  const int side = root.side_to_move();
  Position after = root;
  UndoState undo;
  after.MakeMove(move, &undo);
  if (after.PreviousMoverIsLost()) return -kWinConfirmed;
  MoveList replies;
  after.GenerateMoves(&replies);
  if (replies.empty()) return 0;
  table->NewGeneration();
  searcher->SetContext(side ^ 1, true, FogContext::None());
  SearchLimits limits;
  limits.seconds = 600.0;
  limits.max_nodes = nodes;
  const SearchResult result = searcher->Search(&after, replies, limits);
  return -result.score;
}

}  // namespace

int main(int argc, char** argv) {
  InitializeAttackTables();
  InitializeZobrist();
  const uint64_t nodes = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : 2000000;
  TranspositionTable table;
  table.Resize(64);
  Searcher searcher(&table);
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream in(line);
    std::string board;
    int side = 0, ep = -1;
    unsigned long long castling = 0;
    in >> board >> side >> castling >> ep;
    std::vector<std::string> moves;
    std::string uci;
    while (in >> uci) moves.push_back(uci);
    if (board.size() != 64) {
      std::printf("error bad-board\n");
      continue;
    }
    Position root;
    root.Clear();
    for (int sq = 0; sq < 64; ++sq) {
      const char c = board[static_cast<std::size_t>(sq)];
      if (c == '-' || c == '?') continue;
      const int type = SymbolToPieceType(c);
      if (type == kNoPiece) continue;
      root.PutPiece(sq, (c >= 'A' && c <= 'Z') ? kWhite : kBlack, type);
    }
    root.set_side_to_move(side);
    root.set_castling_rights(static_cast<Bitboard>(castling));
    root.set_en_passant_square(ep);
    MoveList legal;
    root.GenerateMoves(&legal);
    if (legal.empty()) {
      std::printf("error no-moves\n");
      continue;
    }
    // The oracle's choice: a root search over every legal move.
    table.NewGeneration();
    searcher.SetContext(side, true, FogContext::None());
    SearchLimits limits;
    limits.seconds = 600.0;
    limits.max_nodes = nodes;
    Position copy = root;
    const SearchResult best = searcher.Search(&copy, legal, limits);
    const int best_value = ValueAfter(&searcher, &table, root, best.best_move, nodes);
    std::printf("%s %d", MoveToUci(best.best_move).c_str(), best_value);
    for (const std::string& m : moves) {
      const Move move = FindUci(root, m);
      if (move == kNullMove) {
        std::printf(" %s:illegal", m.c_str());
        continue;
      }
      const int value = move == best.best_move ? best_value : ValueAfter(&searcher, &table, root, move, nodes);
      const int regret = std::min(3000, std::max(0, best_value - value));
      std::printf(" %s:%d", m.c_str(), regret);
    }
    std::printf("\n");
    std::fflush(stdout);
  }
  return 0;
}
