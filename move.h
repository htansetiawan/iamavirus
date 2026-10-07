// Copyright 2026. Fog of War chess engine.
//
// Move encoding. A move is packed into 16 bits so that move lists stay small
// and cache resident: six bits of origin, six of destination, four of flag.
// The flag distinguishes the cases that need special handling when the move is
// applied, and carries the promotion piece.

#ifndef FOW_MOVE_H_
#define FOW_MOVE_H_

#include <cstdint>
#include <string>

#include "bitboard.h"

namespace fow {

using Move = uint16_t;

inline constexpr Move kNullMove = 0;

enum MoveFlag : int {
  kFlagNormal = 0,
  kFlagDoublePush = 1,
  kFlagCastleKingSide = 2,
  kFlagCastleQueenSide = 3,
  kFlagEnPassant = 4,
  // Promotions are ordered so that subtracting kFlagPromoteKnight yields the
  // offset of the promoted piece type from kKnight.
  kFlagPromoteKnight = 5,
  kFlagPromoteBishop = 6,
  kFlagPromoteRook = 7,
  kFlagPromoteQueen = 8,
};

inline constexpr Move EncodeMove(int from, int to, int flag = kFlagNormal) {
  return static_cast<Move>(from | (to << 6) | (flag << 12));
}
inline constexpr int MoveFrom(Move move) { return move & 63; }
inline constexpr int MoveTo(Move move) { return (move >> 6) & 63; }
inline constexpr int MoveFlagOf(Move move) { return (move >> 12) & 15; }

inline constexpr bool IsPromotion(Move move) {
  return MoveFlagOf(move) >= kFlagPromoteKnight;
}
inline constexpr int PromotionType(Move move) {
  return IsPromotion(move) ? kKnight + (MoveFlagOf(move) - kFlagPromoteKnight)
                           : kNoPiece;
}
inline constexpr bool IsCastle(Move move) {
  const int flag = MoveFlagOf(move);
  return flag == kFlagCastleKingSide || flag == kFlagCastleQueenSide;
}

std::string MoveToUci(Move move);

// A fixed-capacity move list. 256 is comfortably above the maximum number of
// pseudo-legal moves in any reachable position, so generation never allocates.
class MoveList {
 public:
  static constexpr int kCapacity = 256;

  inline void Add(Move move) { moves_[size_++] = move; }
  inline int size() const { return size_; }
  inline bool empty() const { return size_ == 0; }
  inline void clear() { size_ = 0; }
  inline Move& operator[](int index) { return moves_[index]; }
  inline Move operator[](int index) const { return moves_[index]; }
  inline Move* begin() { return moves_; }
  inline Move* end() { return moves_ + size_; }
  inline const Move* begin() const { return moves_; }
  inline const Move* end() const { return moves_ + size_; }

 private:
  Move moves_[kCapacity];
  int size_ = 0;
};

}  // namespace fow

#endif  // FOW_MOVE_H_
