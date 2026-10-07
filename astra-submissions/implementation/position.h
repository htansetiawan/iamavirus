// Copyright 2026. Fog of War chess engine.
//
// Board state and Fog of War move generation.
//
// "Legal" here means exactly what referee.py's fow_moves means: ordinary
// pseudo-legal chess with no check, pin or self-exposure restriction at all,
// plus castling that requires only the rights, the rook, and empty squares in
// between. Leaving one's own king attacked is a legal move that loses the game
// immediately, which the search discovers on its own rather than by filtering.
//
// Generation is O(number of moves) with O(1) work per piece, and move
// application is O(1) with incremental Zobrist hashing.

#ifndef FOW_POSITION_H_
#define FOW_POSITION_H_

#include <array>
#include <cstdint>
#include <cstring>
#include <string>

#include "bitboard.h"
#include "move.h"
#include "piece_square.h"

namespace fow {

// Zobrist keys. Written once by InitializeZobrist() and read-only thereafter.
extern std::array<std::array<std::array<uint64_t, kNumSquares>, kNumPieceTypes>,
                  kNumColors>
    g_zobrist_piece;
extern uint64_t g_zobrist_side;
extern std::array<uint64_t, 8> g_zobrist_en_passant_file;
extern std::array<uint64_t, kNumSquares> g_zobrist_castling;

void InitializeZobrist();

// State needed to reverse a move. Captured squares are stored explicitly
// because en passant removes a pawn from a square other than the destination.
struct UndoState {
  int captured_type = kNoPiece;
  int captured_square = -1;
  Bitboard castling = 0;
  int en_passant = -1;
  int halfmove_clock = 0;
  uint64_t key = 0;
};

class Position {
 public:
  Position() { Clear(); }

  void Clear();

  // Places a piece, updating every derived structure and the hash. O(1).
  inline void PutPiece(int square, int color, int piece_type) {
    const Bitboard bb = SquareBB(square);
    by_type_[piece_type] |= bb;
    by_color_[color] |= bb;
    occupied_ |= bb;
    piece_at_[square] = static_cast<int8_t>(piece_type);
    color_at_[square] = static_cast<int8_t>(color);
    key_ ^= g_zobrist_piece[color][piece_type][square];
    placement_[color] += kPieceSquareValue[piece_type][color][square];
  }

  // Removes the piece on `square`. O(1).
  //
  // An empty square is ignored rather than treated as undefined behaviour. Every
  // caller is supposed to have checked, and the tests enforce that, but in the
  // arena a corrupted board or a crash forfeits the game, so the cheap branch is
  // worth keeping.
  inline void RemovePiece(int square) {
    const int piece_type = piece_at_[square];
    if (piece_type == kNoPiece) return;
    const int color = color_at_[square];
    const Bitboard bb = SquareBB(square);
    by_type_[piece_type] &= ~bb;
    by_color_[color] &= ~bb;
    occupied_ &= ~bb;
    piece_at_[square] = static_cast<int8_t>(kNoPiece);
    color_at_[square] = -1;
    key_ ^= g_zobrist_piece[color][piece_type][square];
    placement_[color] -= kPieceSquareValue[piece_type][color][square];
  }

  inline Bitboard pieces(int piece_type) const { return by_type_[piece_type]; }
  inline Bitboard pieces(int piece_type, int color) const {
    return by_type_[piece_type] & by_color_[color];
  }
  inline Bitboard pieces_of(int color) const { return by_color_[color]; }
  inline Bitboard occupied() const { return occupied_; }
  inline int piece_at(int square) const { return piece_at_[square]; }
  inline int color_at(int square) const { return color_at_[square]; }
  inline int side_to_move() const { return side_to_move_; }
  inline void set_side_to_move(int color) {
    if (color != side_to_move_) {
      side_to_move_ = color;
      key_ ^= g_zobrist_side;
    }
  }
  inline Bitboard castling_rights() const { return castling_; }
  void set_castling_rights(Bitboard rooks);
  inline int en_passant_square() const { return en_passant_; }
  void set_en_passant_square(int square);
  inline int halfmove_clock() const { return halfmove_clock_; }
  inline void set_halfmove_clock(int value) { halfmove_clock_ = value; }
  inline uint64_t key() const { return key_; }
  // Running material-plus-placement total for `color`, maintained
  // incrementally so evaluation never loops over the pieces to recompute it.
  inline int placement_score(int color) const { return placement_[color]; }

  // Returns the king square of `color`, or -1 when that king is absent. A king
  // can genuinely be missing from a believed position, so callers must check.
  inline int KingSquare(int color) const {
    const Bitboard kings = pieces(kKing, color);
    return kings ? Lsb(kings) : -1;
  }

  // All pieces of `color` attacking `square`, given the current occupancy.
  // O(1): five table lookups and two magic lookups.
  inline Bitboard AttackersTo(int square, int color) const {
    Bitboard found = kPawnAttacks[color ^ 1][square] & by_type_[kPawn];
    found |= kKnightAttacks[square] & by_type_[kKnight];
    found |= kKingAttacks[square] & by_type_[kKing];
    found |= BishopAttacks(square, occupied_) &
             (by_type_[kBishop] | by_type_[kQueen]);
    found |= RookAttacks(square, occupied_) &
             (by_type_[kRook] | by_type_[kQueen]);
    return found & by_color_[color];
  }

  inline bool IsAttacked(int square, int color) const {
    return AttackersTo(square, color) != 0;
  }

  // True when the side that has just moved left its king capturable, which
  // under the course rules means the game is already decided against it. This
  // mirrors referee.py's outcome() test exactly.
  inline bool PreviousMoverIsLost() const {
    const int target = KingSquare(side_to_move_ ^ 1);
    return target < 0 || IsAttacked(target, side_to_move_);
  }

  void MakeMove(Move move, UndoState* undo);
  void UnmakeMove(Move move, const UndoState& undo);

  // Appends every Fog of War legal move for the side to move.
  void GenerateMoves(MoveList* list) const;
  // Appends only captures, en passant and promotions, for quiescence search.
  void GenerateCaptures(MoveList* list) const;

  std::string BoardFen() const;

 private:
  void GeneratePieceMoves(MoveList* list) const;
  void GenerateCastlingMoves(MoveList* list) const;
  void GeneratePawnMoves(MoveList* list) const;

  std::array<Bitboard, kNumPieceTypes> by_type_;
  std::array<Bitboard, kNumColors> by_color_;
  Bitboard occupied_;
  std::array<int8_t, kNumSquares> piece_at_;
  std::array<int8_t, kNumSquares> color_at_;
  int side_to_move_;
  Bitboard castling_;  // rook squares that still carry a castling right
  int en_passant_;     // target square behind a double push, or -1
  int halfmove_clock_;
  uint64_t key_;
  std::array<int32_t, kNumColors> placement_;
};

// Parses the board, side, castling and en passant fields of a FEN. Returns
// false on malformed input.
bool PositionFromFen(const std::string& fen, Position* position);

}  // namespace fow

#endif  // FOW_POSITION_H_
