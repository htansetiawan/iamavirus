// Copyright 2026. Fog of War chess engine.
//
// Bitboard primitives and attack generation.
//
// Squares are numbered 0..63 as a1, b1, ..., h8, which is deliberately the same
// order the arena uses for its 64-character observations, so an observation
// index is a square index with no translation.
//
// Slider attacks use magic bitboards: one multiply, one shift and one table
// lookup, i.e. O(1) with no branches and no loop over ray directions. The magic
// multipliers are searched for at initialization with a deterministic
// generator, and every resulting table entry is verified in
// tests/bitboard_test.cc against the obvious ray-walking implementation.

#ifndef FOW_BITBOARD_H_
#define FOW_BITBOARD_H_

#include <array>
#include <bit>
#include <cstdint>

namespace fow {

using Bitboard = uint64_t;

inline constexpr int kNumSquares = 64;

// Unscoped enumerations are used for Color and PieceType because both index
// arrays on nearly every line of the search; the enclosing namespace already
// scopes the names.
enum Color : int { kWhite = 0, kBlack = 1, kNumColors = 2 };

enum PieceType : int {
  kPawn = 0,
  kKnight = 1,
  kBishop = 2,
  kRook = 3,
  kQueen = 4,
  kKing = 5,
  kNumPieceTypes = 6,
  kNoPiece = 6,
};

// Directions 0..3 step towards higher-numbered squares and 4..7 towards lower
// ones. The reference ray implementation relies on that split to pick the
// nearest blocker with a single comparison.
enum Direction : int {
  kNorth = 0,
  kEast = 1,
  kNorthEast = 2,
  kNorthWest = 3,
  kSouth = 4,
  kWest = 5,
  kSouthEast = 6,
  kSouthWest = 7,
  kNumDirections = 8,
};

inline constexpr std::array<Direction, 4> kRookDirections = {kNorth, kEast,
                                                            kSouth, kWest};
inline constexpr std::array<Direction, 4> kBishopDirections = {
    kNorthEast, kNorthWest, kSouthEast, kSouthWest};

inline constexpr Bitboard SquareBB(int square) {
  return Bitboard{1} << square;
}
inline constexpr int FileOf(int square) { return square & 7; }
inline constexpr int RankOf(int square) { return square >> 3; }
inline constexpr int MakeSquare(int file, int rank) { return rank * 8 + file; }
inline constexpr bool OnBoard(int file, int rank) {
  return file >= 0 && file < 8 && rank >= 0 && rank < 8;
}

inline int PopCount(Bitboard b) { return std::popcount(b); }
inline int Lsb(Bitboard b) { return std::countr_zero(b); }
inline int Msb(Bitboard b) { return 63 - std::countl_zero(b); }

// Removes and returns the lowest set square. O(1).
inline int PopLsb(Bitboard* b) {
  const int square = Lsb(*b);
  *b &= *b - 1;
  return square;
}

inline constexpr int SquareDistance(int a, int b) {
  const int file = FileOf(a) - FileOf(b);
  const int rank = RankOf(a) - RankOf(b);
  const int file_abs = file < 0 ? -file : file;
  const int rank_abs = rank < 0 ? -rank : rank;
  return file_abs > rank_abs ? file_abs : rank_abs;
}

namespace internal {

inline constexpr std::array<int, kNumDirections> kFileStep = {0, 1, 1, -1,
                                                             0, -1, 1, -1};
inline constexpr std::array<int, kNumDirections> kRankStep = {1, 0, 1, 1,
                                                              -1, 0, -1, -1};

using SquareTable = std::array<Bitboard, kNumSquares>;

constexpr std::array<SquareTable, kNumDirections> MakeRays() {
  std::array<SquareTable, kNumDirections> rays{};
  for (int direction = 0; direction < kNumDirections; ++direction) {
    for (int square = 0; square < kNumSquares; ++square) {
      Bitboard ray = 0;
      int file = FileOf(square);
      int rank = RankOf(square);
      for (;;) {
        file += kFileStep[direction];
        rank += kRankStep[direction];
        if (!OnBoard(file, rank)) break;
        ray |= SquareBB(MakeSquare(file, rank));
      }
      rays[direction][square] = ray;
    }
  }
  return rays;
}

constexpr SquareTable MakeKnightAttacks() {
  constexpr std::array<int, 8> kFile = {1, 2, 2, 1, -1, -2, -2, -1};
  constexpr std::array<int, 8> kRank = {2, 1, -1, -2, -2, -1, 1, 2};
  SquareTable table{};
  for (int square = 0; square < kNumSquares; ++square) {
    Bitboard attacks = 0;
    for (int i = 0; i < 8; ++i) {
      const int file = FileOf(square) + kFile[i];
      const int rank = RankOf(square) + kRank[i];
      if (OnBoard(file, rank)) attacks |= SquareBB(MakeSquare(file, rank));
    }
    table[square] = attacks;
  }
  return table;
}

constexpr SquareTable MakeKingAttacks() {
  SquareTable table{};
  for (int square = 0; square < kNumSquares; ++square) {
    Bitboard attacks = 0;
    for (int file_step = -1; file_step <= 1; ++file_step) {
      for (int rank_step = -1; rank_step <= 1; ++rank_step) {
        if (file_step == 0 && rank_step == 0) continue;
        const int file = FileOf(square) + file_step;
        const int rank = RankOf(square) + rank_step;
        if (OnBoard(file, rank)) attacks |= SquareBB(MakeSquare(file, rank));
      }
    }
    table[square] = attacks;
  }
  return table;
}

constexpr std::array<SquareTable, kNumColors> MakePawnAttacks() {
  std::array<SquareTable, kNumColors> table{};
  for (int square = 0; square < kNumSquares; ++square) {
    for (int file_step = -1; file_step <= 1; file_step += 2) {
      const int file = FileOf(square) + file_step;
      if (file < 0 || file > 7) continue;
      if (RankOf(square) + 1 <= 7) {
        table[kWhite][square] |= SquareBB(MakeSquare(file, RankOf(square) + 1));
      }
      if (RankOf(square) - 1 >= 0) {
        table[kBlack][square] |= SquareBB(MakeSquare(file, RankOf(square) - 1));
      }
    }
  }
  return table;
}

constexpr std::array<std::array<Bitboard, kNumSquares>, kNumSquares>
MakeBetween(const std::array<SquareTable, kNumDirections>& rays) {
  std::array<std::array<Bitboard, kNumSquares>, kNumSquares> table{};
  for (int from = 0; from < kNumSquares; ++from) {
    for (int to = 0; to < kNumSquares; ++to) {
      for (int direction = 0; direction < kNumDirections; ++direction) {
        if (!(rays[direction][from] & SquareBB(to))) continue;
        table[from][to] =
            rays[direction][from] & ~rays[direction][to] & ~SquareBB(to);
        break;
      }
    }
  }
  return table;
}

}  // namespace internal

inline constexpr auto kRay = internal::MakeRays();
inline constexpr auto kKnightAttacks = internal::MakeKnightAttacks();
inline constexpr auto kKingAttacks = internal::MakeKingAttacks();
inline constexpr auto kPawnAttacks = internal::MakePawnAttacks();
inline constexpr auto kBetween = internal::MakeBetween(kRay);

inline constexpr std::array<Bitboard, 8> MakeFileMasks() {
  std::array<Bitboard, 8> masks{};
  for (int square = 0; square < kNumSquares; ++square) {
    masks[FileOf(square)] |= SquareBB(square);
  }
  return masks;
}
inline constexpr std::array<Bitboard, 8> MakeRankMasks() {
  std::array<Bitboard, 8> masks{};
  for (int square = 0; square < kNumSquares; ++square) {
    masks[RankOf(square)] |= SquareBB(square);
  }
  return masks;
}
inline constexpr auto kFileMask = MakeFileMasks();
inline constexpr auto kRankMask = MakeRankMasks();

// Ray-walking attack generation. This is the readable definition of the rules;
// the magic tables below are built from it and tested against it.
constexpr Bitboard ReferenceSliderAttacks(
    const std::array<Direction, 4>& directions, int square, Bitboard occupied) {
  Bitboard attacks = 0;
  for (const Direction direction : directions) {
    Bitboard ray = kRay[direction][square];
    const Bitboard blockers = ray & occupied;
    if (blockers) {
      const int nearest =
          direction < kSouth ? std::countr_zero(blockers)
                             : 63 - std::countl_zero(blockers);
      ray &= ~kRay[direction][nearest];
    }
    attacks |= ray;
  }
  return attacks;
}

constexpr Bitboard ReferenceRookAttacks(int square, Bitboard occupied) {
  return ReferenceSliderAttacks(kRookDirections, square, occupied);
}
constexpr Bitboard ReferenceBishopAttacks(int square, Bitboard occupied) {
  return ReferenceSliderAttacks(kBishopDirections, square, occupied);
}

// One magic entry per square. `attacks` points into a shared pool so the tables
// stay contiguous and cache friendly.
struct MagicEntry {
  Bitboard mask = 0;        // relevant blocker squares, edges excluded
  Bitboard multiplier = 0;  // magic factor
  const Bitboard* attacks = nullptr;
  int shift = 0;

  inline Bitboard Lookup(Bitboard occupied) const {
    return attacks[((occupied & mask) * multiplier) >> shift];
  }
};

// Initializes the magic tables. Must be called once before any attack query;
// InitializeEngine() in engine.h does so. Idempotent.
void InitializeAttackTables();

// Non-const namespace-scope state is used deliberately: these are written once
// by InitializeAttackTables() and only read afterwards, and an explicit
// initialization call avoids any static initialization order question.
extern std::array<MagicEntry, kNumSquares> g_rook_magics;
extern std::array<MagicEntry, kNumSquares> g_bishop_magics;

inline Bitboard RookAttacks(int square, Bitboard occupied) {
  return g_rook_magics[square].Lookup(occupied);
}
inline Bitboard BishopAttacks(int square, Bitboard occupied) {
  return g_bishop_magics[square].Lookup(occupied);
}
inline Bitboard QueenAttacks(int square, Bitboard occupied) {
  return RookAttacks(square, occupied) | BishopAttacks(square, occupied);
}

// Attacks of `piece_type` from `square`. `color` matters only for pawns.
inline Bitboard PieceAttacks(int piece_type, int square, Bitboard occupied,
                             int color = kWhite) {
  switch (piece_type) {
    case kPawn:
      return kPawnAttacks[color][square];
    case kKnight:
      return kKnightAttacks[square];
    case kBishop:
      return BishopAttacks(square, occupied);
    case kRook:
      return RookAttacks(square, occupied);
    case kQueen:
      return QueenAttacks(square, occupied);
    case kKing:
      return kKingAttacks[square];
    default:
      return 0;
  }
}

}  // namespace fow

#endif  // FOW_BITBOARD_H_
