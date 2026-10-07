// Copyright 2026. Fog of War chess engine.

#include <string>

#include "move.h"

namespace fow {

std::string MoveToUci(Move move) {
  static constexpr char kPromotionSymbol[] = "nbrq";
  std::string uci;
  uci += static_cast<char>('a' + FileOf(MoveFrom(move)));
  uci += static_cast<char>('1' + RankOf(MoveFrom(move)));
  uci += static_cast<char>('a' + FileOf(MoveTo(move)));
  uci += static_cast<char>('1' + RankOf(MoveTo(move)));
  if (IsPromotion(move)) {
    uci += kPromotionSymbol[PromotionType(move) - kKnight];
  }
  return uci;
}

}  // namespace fow
