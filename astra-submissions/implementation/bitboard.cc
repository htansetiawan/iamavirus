// Copyright 2026. Fog of War chess engine.
//
// Magic bitboard construction.
//
// For each square the relevant blocker mask excludes board edges, since a
// blocker on the edge never changes which squares are reachable. A magic
// multiplier maps each of the 2^popcount(mask) blocker patterns onto a distinct
// index, giving O(1) attack lookup. Multipliers are searched with a fixed
// xorshift sequence so the tables are bit-identical on every run.

#include "bitboard.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace fow {

std::array<MagicEntry, kNumSquares> g_rook_magics;
std::array<MagicEntry, kNumSquares> g_bishop_magics;

namespace {

// Backing store for every square's attack table. Held by value so the pointers
// in the magic entries stay valid for the process lifetime.
std::vector<Bitboard> g_rook_pool;
std::vector<Bitboard> g_bishop_pool;
bool g_initialized = false;

// Blocker squares that can affect a slider on `square`, excluding the edges of
// each ray.
Bitboard RelevantMask(const std::array<Direction, 4>& directions, int square) {
  Bitboard mask = 0;
  for (const Direction direction : directions) {
    int file = FileOf(square);
    int rank = RankOf(square);
    for (;;) {
      file += internal::kFileStep[direction];
      rank += internal::kRankStep[direction];
      if (!OnBoard(file, rank)) break;
      const int next_file = file + internal::kFileStep[direction];
      const int next_rank = rank + internal::kRankStep[direction];
      if (!OnBoard(next_file, next_rank)) break;  // edge square, irrelevant
      mask |= SquareBB(MakeSquare(file, rank));
    }
  }
  return mask;
}

// Enumerates the subsets of `mask` in index order. O(1) per step.
Bitboard SubsetOf(Bitboard mask, int index) {
  Bitboard subset = 0;
  while (mask) {
    const int square = PopLsb(&mask);
    if (index & 1) subset |= SquareBB(square);
    index >>= 1;
  }
  return subset;
}

uint64_t NextRandom() {
  static uint64_t state = 0x9E3779B97F4A7C15ULL;
  state ^= state >> 12;
  state ^= state << 25;
  state ^= state >> 27;
  return state * 0x2545F4914F6CDD1DULL;
}

// Sparse candidates collide far less often than dense ones.
uint64_t SparseRandom() { return NextRandom() & NextRandom() & NextRandom(); }

void BuildMagics(const std::array<Direction, 4>& directions,
                 std::array<MagicEntry, kNumSquares>* magics,
                 std::vector<Bitboard>* pool) {
  // Reserve once so no reallocation invalidates an already-stored pointer.
  std::size_t total = 0;
  for (int square = 0; square < kNumSquares; ++square) {
    total += std::size_t{1} << PopCount(RelevantMask(directions, square));
  }
  pool->assign(total, 0);

  std::size_t offset = 0;
  std::vector<Bitboard> occupancies;
  std::vector<Bitboard> expected;
  for (int square = 0; square < kNumSquares; ++square) {
    MagicEntry& entry = (*magics)[square];
    entry.mask = RelevantMask(directions, square);
    const int bits = PopCount(entry.mask);
    const std::size_t count = std::size_t{1} << bits;
    entry.shift = 64 - bits;

    occupancies.resize(count);
    expected.resize(count);
    for (std::size_t i = 0; i < count; ++i) {
      occupancies[i] = SubsetOf(entry.mask, static_cast<int>(i));
      expected[i] = ReferenceSliderAttacks(directions, square, occupancies[i]);
    }

    Bitboard* table = pool->data() + offset;
    std::vector<std::size_t> stamp(count, 0);
    for (std::size_t attempt = 1;; ++attempt) {
      const Bitboard candidate = SparseRandom();
      // A magic must spread the high bits of the product; this cheap filter
      // rejects most hopeless candidates before the collision scan.
      if (PopCount((entry.mask * candidate) >> 56) < 6) continue;
      bool ok = true;
      for (std::size_t i = 0; i < count && ok; ++i) {
        const std::size_t index = (occupancies[i] * candidate) >> entry.shift;
        if (stamp[index] != attempt) {
          stamp[index] = attempt;
          table[index] = expected[i];
        } else if (table[index] != expected[i]) {
          ok = false;  // a genuine collision, not a constructive one
        }
      }
      if (ok) {
        entry.multiplier = candidate;
        break;
      }
    }
    entry.attacks = table;
    offset += count;
  }
}

}  // namespace

void InitializeAttackTables() {
  if (g_initialized) return;
  BuildMagics(kRookDirections, &g_rook_magics, &g_rook_pool);
  BuildMagics(kBishopDirections, &g_bishop_magics, &g_bishop_pool);
  g_initialized = true;
}

}  // namespace fow
