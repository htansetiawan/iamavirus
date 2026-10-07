// Copyright 2026. Fog of War chess engine.
//
// Parity harness for the learned opponent prior: reads "FEN;UCI" lines and
// prints the feature vector, so learning/tests/test_opponent_parity.py can
// compare it with learning/opponent_model.move_features.

#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>

#include "../bitboard.h"
#include "../move.h"
#include "../opponent_model.h"
#include "../position.h"

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  std::string line;
  while (std::getline(std::cin, line)) {
    const std::size_t split = line.find(';');
    if (split == std::string::npos) continue;
    fow::Position board;
    if (!fow::PositionFromFen(line.substr(0, split), &board)) {
      std::cout << "BADFEN\n";
      continue;
    }
    const std::string uci = line.substr(split + 1);
    fow::MoveList legal;
    board.GenerateMoves(&legal);
    fow::Move move = fow::kNullMove;
    for (const fow::Move candidate : legal) {
      if (fow::MoveToUci(candidate) == uci) move = candidate;
    }
    if (move == fow::kNullMove) {
      std::cout << "BADMOVE\n";
      continue;
    }
    double features[fow::kNumOpponentFeatures];
    fow::OpponentMoveFeatures(&board, move, features);
    for (int i = 0; i < fow::kNumOpponentFeatures; ++i) {
      std::printf("%s%.6f", i ? " " : "", features[i]);
    }
    std::printf("\n");
  }
  return 0;
}
