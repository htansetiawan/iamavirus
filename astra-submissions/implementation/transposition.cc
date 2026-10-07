// Copyright 2026. Fog of War chess engine.

#include "transposition.h"

#include <bit>
#include <cstddef>
#include <vector>

namespace fow {

void TranspositionTable::Resize(std::size_t megabytes) {
  const std::size_t wanted = megabytes * 1024 * 1024 / sizeof(TranspositionEntry);
  std::size_t count = 1;
  while (count * 2 <= wanted) count *= 2;
  entries_.assign(count, TranspositionEntry());
  mask_ = count - 1;
  generation_ = 1;
}

void TranspositionTable::Clear() {
  entries_.assign(entries_.size(), TranspositionEntry());
  generation_ = 1;
}

}  // namespace fow
