// Copyright 2026. Fog of War chess engine.
//
// Transposition table.
//
// A fixed, power-of-two array indexed by the low bits of the Zobrist key, with
// the full key stored for verification. That gives O(1) probe and store with one
// cache line touched per access, which is what a hash table in a search hot loop
// needs; a node-based map would spend more time chasing pointers than searching.
// Collisions simply replace, preferring deeper entries and entries from older
// searches, because a shallow result is cheap to recompute.
//
// Mate scores are stored relative to the node that found them and translated
// back on probe. Storing them absolutely would report a mate at the wrong
// distance when the same position is reached by a different route.

#ifndef FOW_TRANSPOSITION_H_
#define FOW_TRANSPOSITION_H_

#include <cstddef>
#include <cstdint>
#include <vector>

#include "move.h"

namespace fow {

enum BoundType : uint8_t {
  kBoundNone = 0,
  kBoundExact = 1,   // the score is the true value
  kBoundLower = 2,   // the true value is at least the score (a fail high)
  kBoundUpper = 3,   // the true value is at most the score (a fail low)
};

// Scores at least this large in magnitude are distances to a decided game and
// must be adjusted by the ply they were found at.
inline constexpr int kDecisiveScoreThreshold = 9000;

struct TranspositionEntry {
  // Only the high half of the Zobrist key is stored: the low bits already chose
  // the slot, so verifying the high bits confirms the match without paying for
  // a second word.
  uint32_t key_high = 0;
  int32_t score = 0;
  Move move = kNullMove;
  int8_t depth = -1;
  uint8_t bound = kBoundNone;
  uint8_t generation = 0;
};
static_assert(sizeof(TranspositionEntry) == 16,
              "entry should stay at 16 bytes so four share a cache line");

// The slot-verifying half of a key.
inline constexpr uint32_t KeyHigh(uint64_t key) {
  return static_cast<uint32_t>(key >> 32);
}

class TranspositionTable {
 public:
  // Allocates the nearest power of two of entries that fits in `megabytes`.
  void Resize(std::size_t megabytes);
  void Clear();

  // Marks the start of a new search, so entries from previous searches become
  // preferred replacement candidates without being discarded outright.
  inline void NewGeneration() { ++generation_; }

  // Looks up `key`. On a hit, always reports the stored move for ordering, and
  // reports a usable score only when the stored depth and bound allow a cutoff.
  inline bool Probe(uint64_t key, int depth, int alpha, int beta, int ply,
                    int* score, Move* move, bool* usable) const {
    *usable = false;
    if (entries_.empty()) return false;
    const TranspositionEntry& entry = entries_[key & mask_];
    if (entry.key_high != KeyHigh(key) || entry.bound == kBoundNone) {
      return false;
    }
    *move = entry.move;
    if (entry.depth < depth) return true;
    const int adjusted = FromStorage(entry.score, ply);
    switch (entry.bound) {
      case kBoundExact:
        *score = adjusted;
        *usable = true;
        break;
      case kBoundLower:
        if (adjusted >= beta) {
          *score = adjusted;
          *usable = true;
        }
        break;
      case kBoundUpper:
        if (adjusted <= alpha) {
          *score = adjusted;
          *usable = true;
        }
        break;
      default:
        break;
    }
    return true;
  }

  inline void Store(uint64_t key, int depth, int score, BoundType bound,
                    Move move, int ply) {
    if (entries_.empty()) return;
    TranspositionEntry& entry = entries_[key & mask_];
    const bool same_position = entry.key_high == KeyHigh(key);
    const bool stale = entry.generation != generation_;
    // Keep a deeper result for the same position; otherwise prefer whatever is
    // newest, since an entry from an earlier search is worth less.
    if (same_position && !stale && entry.depth > depth &&
        entry.bound == kBoundExact) {
      return;
    }
    entry.key_high = KeyHigh(key);
    entry.score = static_cast<int32_t>(ToStorage(score, ply));
    entry.move = move != kNullMove || !same_position ? move : entry.move;
    entry.depth = static_cast<int8_t>(depth);
    entry.bound = bound;
    entry.generation = generation_;
  }

  inline std::size_t entry_count() const { return entries_.size(); }

 private:
  // Converts between a score relative to the root and one relative to the node.
  static inline int ToStorage(int score, int ply) {
    if (score >= kDecisiveScoreThreshold) return score + ply;
    if (score <= -kDecisiveScoreThreshold) return score - ply;
    return score;
  }
  static inline int FromStorage(int score, int ply) {
    if (score >= kDecisiveScoreThreshold) return score - ply;
    if (score <= -kDecisiveScoreThreshold) return score + ply;
    return score;
  }

  std::vector<TranspositionEntry> entries_;
  uint64_t mask_ = 0;
  uint8_t generation_ = 1;
};

}  // namespace fow

#endif  // FOW_TRANSPOSITION_H_
