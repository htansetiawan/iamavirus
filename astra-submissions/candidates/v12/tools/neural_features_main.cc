// Copyright 2026. Fog of War chess engine.
//
// Feature-parity harness. Reads one event per line and, on "dump", prints the
// tracker's planes, scalars and candidate list, so the Python tracker and this
// one can be compared over identical histories.
//
//   side S                  start a tracker for side S (0 white, 1 black)
//   obs PHASE PLY VIEW      an observation event
//   move UCI                our own move, recorded after a decision
//   dump                    print "planes <2048 floats>", "scalars <8 floats>",
//                           "ep N", "rights N", "candidates <uci...>"

#include <cstdio>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>

#include "../bitboard.h"
#include "../move.h"
#include "../neural_observation.h"
#include "../observation.h"
#include "../position.h"

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  std::unique_ptr<fow::NeuralTracker> tracker;
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream stream(line);
    std::string command;
    stream >> command;
    if (command == "side") {
      int side = 0;
      stream >> side;
      tracker = std::make_unique<fow::NeuralTracker>(side);
    } else if (command == "obs" && tracker) {
      int phase = 0, ply = 0;
      std::string view;
      stream >> phase >> ply >> view;
      tracker->Observe(fow::Observation(view), phase, ply);
    } else if (command == "move" && tracker) {
      std::string uci;
      stream >> uci;
      fow::MoveList legal;
      tracker->LegalCandidates(&legal);
      for (const fow::Move move : legal) {
        if (fow::MoveToUci(move) == uci) tracker->RecordOwnMove(move);
      }
    } else if (command == "dump" && tracker) {
      float planes[fow::kNeuralPlanes * fow::kNumSquares];
      float scalars[fow::kNeuralScalars];
      tracker->Planes(planes);
      tracker->Scalars(scalars);
      std::cout << "planes";
      for (float value : planes) std::cout << ' ' << value;
      std::cout << "\nscalars";
      for (float value : scalars) std::cout << ' ' << value;
      std::cout << "\nep " << tracker->EnPassant() << "\nrights "
                << tracker->CastlingRights() << "\ncandidates";
      fow::MoveList legal;
      tracker->LegalCandidates(&legal);
      for (const fow::Move move : legal) std::cout << ' ' << fow::MoveToUci(move);
      std::cout << "\n";
    }
  }
  return 0;
}
