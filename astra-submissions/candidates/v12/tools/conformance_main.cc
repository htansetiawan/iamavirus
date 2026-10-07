// Copyright 2026. Fog of War chess engine.
//
// Conformance harness. Reads one request per line and prints one answer, so the
// C++ rule implementation can be diffed against referee.py -- the arena's own
// implementation -- over large numbers of randomly reached positions.
//
// Request formats, fields separated by ';':
//   perft;FEN;DEPTH            -> leaf count
//   moves;FEN                  -> sorted UCI move list
//   visible;FEN;SIDE           -> the 64-character observation for SIDE
//   legal;OBS;SIDE;CASTLE;EP   -> sorted UCI move list from an observation
//   ep;PREV;CUR;SIDE           -> inferred en passant square, or -1

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "../bitboard.h"
#include "../move.h"
#include "../observation.h"
#include "../position.h"

namespace fow {
namespace {

std::vector<std::string> Split(const std::string& line, char separator) {
  std::vector<std::string> fields;
  std::string field;
  std::istringstream stream(line);
  while (std::getline(stream, field, separator)) fields.push_back(field);
  return fields;
}

std::string JoinSorted(const MoveList& list) {
  std::vector<std::string> uci;
  uci.reserve(list.size());
  for (const Move move : list) uci.push_back(MoveToUci(move));
  std::sort(uci.begin(), uci.end());
  std::string joined;
  for (std::size_t i = 0; i < uci.size(); ++i) {
    if (i > 0) joined += ' ';
    joined += uci[i];
  }
  return joined;
}

int64_t Perft(Position* position, int depth) {
  MoveList list;
  position->GenerateMoves(&list);
  if (depth <= 1) return list.size();
  int64_t total = 0;
  for (const Move move : list) {
    UndoState undo;
    position->MakeMove(move, &undo);
    total += Perft(position, depth - 1);
    position->UnmakeMove(move, undo);
  }
  return total;
}

void HandleRequest(const std::string& line) {
  const std::vector<std::string> fields = Split(line, ';');
  if (fields.empty()) return;
  const std::string& command = fields[0];

  if (command == "perft" && fields.size() >= 3) {
    Position position;
    if (!PositionFromFen(fields[1], &position)) {
      std::cout << "BADFEN\n";
      return;
    }
    std::cout << Perft(&position, std::stoi(fields[2])) << "\n";
  } else if (command == "moves" && fields.size() >= 2) {
    Position position;
    if (!PositionFromFen(fields[1], &position)) {
      std::cout << "BADFEN\n";
      return;
    }
    MoveList list;
    position.GenerateMoves(&list);
    std::cout << JoinSorted(list) << "\n";
  } else if (command == "visible" && fields.size() >= 3) {
    Position position;
    if (!PositionFromFen(fields[1], &position)) {
      std::cout << "BADFEN\n";
      return;
    }
    std::cout << RenderObservation(position, std::stoi(fields[2])) << "\n";
  } else if (command == "legal" && fields.size() >= 5) {
    const Observation observation(fields[1]);
    Position visible;
    VisiblePositionFromObservation(observation, std::stoi(fields[2]),
                                   std::stoull(fields[3]),
                                   std::stoi(fields[4]), &visible);
    MoveList list;
    LegalMovesFromObservation(visible, observation, &list);
    std::cout << JoinSorted(list) << "\n";
  } else if (command == "ep" && fields.size() >= 4) {
    const Observation previous(fields[1]);
    const Observation current(fields[2]);
    std::cout << InferEnPassant(&previous, current, std::stoi(fields[3]))
              << "\n";
  } else {
    std::cout << "BADREQUEST\n";
  }
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  std::string line;
  while (std::getline(std::cin, line)) {
    if (!line.empty()) fow::HandleRequest(line);
  }
  return 0;
}
