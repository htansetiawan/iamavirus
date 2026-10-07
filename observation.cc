// Copyright 2026. Fog of War chess engine.

#include "observation.h"

#include <cstddef>
#include <cstring>
#include <string>

namespace fow {
namespace {

constexpr char kWhiteSymbols[] = "PNBRQK";
constexpr char kBlackSymbols[] = "pnbrqk";

const char* SymbolsFor(int color) {
  return color == kWhite ? kWhiteSymbols : kBlackSymbols;
}

bool IsWhiteSymbol(char symbol) { return symbol >= 'A' && symbol <= 'Z'; }

}  // namespace

int SymbolToPieceType(char symbol) {
  switch (symbol | 32) {
    case 'p': return kPawn;
    case 'n': return kKnight;
    case 'b': return kBishop;
    case 'r': return kRook;
    case 'q': return kQueen;
    case 'k': return kKing;
    default: return kNoPiece;
  }
}

char PieceTypeToSymbol(int piece_type, int color) {
  return SymbolsFor(color)[piece_type];
}

bool Observation::IsValid(const std::string& squares) {
  if (squares.size() != static_cast<std::size_t>(kNumSquares)) return false;
  for (const char symbol : squares) {
    if (symbol == kUnseen || symbol == kEmpty) continue;
    if (SymbolToPieceType(symbol) == kNoPiece) return false;
  }
  return true;
}

Bitboard Observation::UnseenMask() const {
  Bitboard mask = 0;
  for (int square = 0; square < kNumSquares; ++square) {
    if (squares_[square] == kUnseen) mask |= SquareBB(square);
  }
  return mask;
}

Bitboard Observation::VisiblePieces(int color) const {
  Bitboard mask = 0;
  for (int square = 0; square < kNumSquares; ++square) {
    const char symbol = squares_[square];
    if (symbol == kUnseen || symbol == kEmpty) continue;
    if (IsWhiteSymbol(symbol) == (color == kWhite)) mask |= SquareBB(square);
  }
  return mask;
}

Bitboard Observation::VisiblePieces(int color, int piece_type) const {
  Bitboard mask = 0;
  const char wanted = PieceTypeToSymbol(piece_type, color);
  for (int square = 0; square < kNumSquares; ++square) {
    if (squares_[square] == wanted) mask |= SquareBB(square);
  }
  return mask;
}

void VisiblePositionFromObservation(const Observation& observation, int side,
                                    Bitboard castling_rights,
                                    int en_passant_square,
                                    Position* position) {
  position->Clear();
  for (int square = 0; square < kNumSquares; ++square) {
    const char symbol = observation.at(square);
    if (symbol == kUnseen || symbol == kEmpty) continue;
    position->PutPiece(square, IsWhiteSymbol(symbol) ? kWhite : kBlack,
                       SymbolToPieceType(symbol));
  }
  position->set_side_to_move(side);
  position->set_castling_rights(castling_rights);
  position->set_en_passant_square(en_passant_square);
}

void LegalMovesFromObservation(const Position& visible,
                               const Observation& observation,
                               MoveList* list) {
  MoveList all;
  visible.GenerateMoves(&all);
  const int side = visible.side_to_move();
  for (const Move move : all) {
    const int from = MoveFrom(move);
    const int to = MoveTo(move);
    if (observation.IsUnseen(to)) continue;
    if (visible.piece_at(from) != kKnight) {
      // A slider may not pass through a square we cannot see. Since every such
      // square would itself be a visible destination, an unseen one proves the
      // move is not available.
      Bitboard path = kBetween[from][to];
      bool blind = false;
      while (path) {
        if (observation.IsUnseen(PopLsb(&path))) {
          blind = true;
          break;
        }
      }
      if (blind) continue;
    }
    if (IsCastle(move)) {
      const int rank = side == kWhite ? 0 : 7;
      const bool king_side = MoveFlagOf(move) == kFlagCastleKingSide;
      bool blind = false;
      if (king_side) {
        for (const int file : {5, 6}) {
          if (!observation.IsVisibleEmpty(MakeSquare(file, rank))) blind = true;
        }
      } else {
        for (const int file : {1, 2, 3}) {
          if (!observation.IsVisibleEmpty(MakeSquare(file, rank))) blind = true;
        }
      }
      if (blind) continue;
    }
    list->Add(move);
  }
}

Bitboard VisibleSquares(const Position& position, int color) {
  Position view = position;
  view.set_side_to_move(color);
  if (color != position.side_to_move()) view.set_en_passant_square(-1);
  MoveList list;
  view.GenerateMoves(&list);
  Bitboard seen = view.pieces_of(color);
  for (const Move move : list) {
    seen |= SquareBB(MoveTo(move));
    if (MoveFlagOf(move) == kFlagEnPassant) {
      seen |= SquareBB(color == kWhite ? MoveTo(move) - 8 : MoveTo(move) + 8);
    }
  }
  return seen;
}

std::string RenderObservation(const Position& position, int color) {
  const Bitboard seen = VisibleSquares(position, color);
  std::string view(kNumSquares, kUnseen);
  for (int square = 0; square < kNumSquares; ++square) {
    if (!(seen & SquareBB(square))) continue;
    if (position.piece_at(square) == kNoPiece) {
      view[square] = kEmpty;
    } else {
      view[square] = PieceTypeToSymbol(position.piece_at(square),
                                       position.color_at(square));
    }
  }
  return view;
}

int InferEnPassant(const Observation* previous, const Observation& current,
                   int side) {
  if (previous == nullptr) return -1;
  const char our_pawn = PieceTypeToSymbol(kPawn, side);
  const char enemy_pawn = PieceTypeToSymbol(kPawn, side ^ 1);
  const char* our_symbols = SymbolsFor(side);

  // Our own pieces are always observed, so if one changed, the opponent's move
  // was a capture rather than a double push.
  for (int square = 0; square < kNumSquares; ++square) {
    const char before = previous->at(square);
    const char after = current.at(square);
    if (before == after) continue;
    if (std::strchr(our_symbols, before) != nullptr ||
        std::strchr(our_symbols, after) != nullptr) {
      return -1;
    }
  }

  const int pawn_rank = side == kWhite ? 4 : 3;
  const int middle_rank = side == kWhite ? 5 : 2;
  const int start_rank = side == kWhite ? 6 : 1;
  int candidate = -1;
  for (int file = 0; file < 8; ++file) {
    const int target = MakeSquare(file, pawn_rank);
    const int middle = MakeSquare(file, middle_rank);
    const int start = MakeSquare(file, start_rank);
    if (current.at(target) != enemy_pawn) continue;
    if (current.at(middle) != kEmpty) continue;

    bool beside_our_pawn = false;
    for (const int other : {file - 1, file + 1}) {
      if (other < 0 || other > 7) continue;
      if (current.at(MakeSquare(other, pawn_rank)) == our_pawn) {
        beside_our_pawn = true;
      }
    }
    if (!beside_our_pawn) continue;

    // Before the move the pawn must not have been seen on its destination or
    // the square it crossed, and it must have been on, or hidden on, its start.
    const char before_target = previous->at(target);
    const char before_middle = previous->at(middle);
    const char before_start = previous->at(start);
    if (before_target != kUnseen && before_target != kEmpty) continue;
    if (before_middle != kUnseen && before_middle != kEmpty) continue;
    if (before_start != kUnseen && before_start != enemy_pawn) continue;
    if (current.at(start) != kUnseen && current.at(start) != kEmpty) continue;

    // Any other explanation would have disturbed some square visible both
    // before and after.
    bool contradicted = false;
    for (int square = 0; square < kNumSquares && !contradicted; ++square) {
      if (square == start || square == target) continue;
      const char before = previous->at(square);
      const char after = current.at(square);
      if (before != kUnseen && after != kUnseen && before != after) {
        contradicted = true;
      }
    }
    if (contradicted) continue;

    if (candidate >= 0) return -1;  // ambiguous, so claim nothing
    candidate = middle;
  }
  return candidate;
}

}  // namespace fow
