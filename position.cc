// Copyright 2026. Fog of War chess engine.

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

#include "position.h"

namespace fow {

std::array<std::array<std::array<uint64_t, kNumSquares>, kNumPieceTypes>,
           kNumColors>
    g_zobrist_piece;
uint64_t g_zobrist_side;
std::array<uint64_t, 8> g_zobrist_en_passant_file;
std::array<uint64_t, kNumSquares> g_zobrist_castling;

namespace {

bool g_zobrist_ready = false;

// A fixed xorshift sequence keeps the keys identical on every run, which makes
// search behaviour reproducible.
uint64_t NextKey() {
  static uint64_t state = 0x243F6A8885A308D3ULL;
  state ^= state >> 12;
  state ^= state << 25;
  state ^= state >> 27;
  return state * 0x2545F4914F6CDD1DULL;
}

}  // namespace

void InitializeZobrist() {
  if (g_zobrist_ready) return;
  for (int color = 0; color < kNumColors; ++color) {
    for (int type = 0; type < kNumPieceTypes; ++type) {
      for (int square = 0; square < kNumSquares; ++square) {
        g_zobrist_piece[color][type][square] = NextKey();
      }
    }
  }
  g_zobrist_side = NextKey();
  for (int file = 0; file < 8; ++file) {
    g_zobrist_en_passant_file[file] = NextKey();
  }
  for (int square = 0; square < kNumSquares; ++square) {
    g_zobrist_castling[square] = NextKey();
  }
  g_zobrist_ready = true;
}

void Position::Clear() {
  by_type_.fill(0);
  by_color_.fill(0);
  occupied_ = 0;
  piece_at_.fill(static_cast<int8_t>(kNoPiece));
  color_at_.fill(-1);
  side_to_move_ = kWhite;
  castling_ = 0;
  en_passant_ = -1;
  halfmove_clock_ = 0;
  key_ = 0;
  placement_.fill(0);
}

void Position::set_castling_rights(Bitboard rooks) {
  Bitboard changed = castling_ ^ rooks;
  while (changed) {
    key_ ^= g_zobrist_castling[PopLsb(&changed)];
  }
  castling_ = rooks;
}

void Position::set_en_passant_square(int square) {
  if (en_passant_ >= 0) key_ ^= g_zobrist_en_passant_file[FileOf(en_passant_)];
  en_passant_ = square;
  if (en_passant_ >= 0) key_ ^= g_zobrist_en_passant_file[FileOf(en_passant_)];
}

void Position::MakeMove(Move move, UndoState* undo) {
  const int from = MoveFrom(move);
  const int to = MoveTo(move);
  const int flag = MoveFlagOf(move);

  undo->captured_type = kNoPiece;
  undo->captured_square = -1;
  undo->castling = castling_;
  undo->en_passant = en_passant_;
  undo->halfmove_clock = halfmove_clock_;
  undo->key = key_;

  const int mover = piece_at_[from];
  set_en_passant_square(-1);
  ++halfmove_clock_;

  if (flag == kFlagEnPassant) {
    const int victim = side_to_move_ == kWhite ? to - 8 : to + 8;
    undo->captured_type = kPawn;
    undo->captured_square = victim;
    RemovePiece(victim);
    halfmove_clock_ = 0;
  } else if (piece_at_[to] != kNoPiece) {
    undo->captured_type = piece_at_[to];
    undo->captured_square = to;
    if (castling_ & SquareBB(to)) {
      // Capturing a rook on its original square removes that right.
      set_castling_rights(castling_ & ~SquareBB(to));
    }
    RemovePiece(to);
    halfmove_clock_ = 0;
  }

  RemovePiece(from);
  PutPiece(to, side_to_move_, IsPromotion(move) ? PromotionType(move) : mover);

  if (mover == kPawn) {
    halfmove_clock_ = 0;
    if (flag == kFlagDoublePush) {
      set_en_passant_square(side_to_move_ == kWhite ? from + 8 : from - 8);
    }
  } else if (mover == kKing) {
    set_castling_rights(castling_ & ~by_color_[side_to_move_]);
    const int rank = RankOf(from);
    if (flag == kFlagCastleKingSide) {
      RemovePiece(MakeSquare(7, rank));
      PutPiece(MakeSquare(5, rank), side_to_move_, kRook);
    } else if (flag == kFlagCastleQueenSide) {
      RemovePiece(MakeSquare(0, rank));
      PutPiece(MakeSquare(3, rank), side_to_move_, kRook);
    }
  } else if (mover == kRook && (castling_ & SquareBB(from))) {
    set_castling_rights(castling_ & ~SquareBB(from));
  }

  side_to_move_ ^= 1;
  key_ ^= g_zobrist_side;
}

void Position::UnmakeMove(Move move, const UndoState& undo) {
  const int from = MoveFrom(move);
  const int to = MoveTo(move);
  const int flag = MoveFlagOf(move);
  side_to_move_ ^= 1;

  const int mover =
      IsPromotion(move) ? static_cast<int>(kPawn) : static_cast<int>(piece_at_[to]);
  RemovePiece(to);
  PutPiece(from, side_to_move_, mover);

  if (flag == kFlagCastleKingSide) {
    const int rank = RankOf(from);
    RemovePiece(MakeSquare(5, rank));
    PutPiece(MakeSquare(7, rank), side_to_move_, kRook);
  } else if (flag == kFlagCastleQueenSide) {
    const int rank = RankOf(from);
    RemovePiece(MakeSquare(3, rank));
    PutPiece(MakeSquare(0, rank), side_to_move_, kRook);
  } else if (undo.captured_type != kNoPiece) {
    PutPiece(undo.captured_square, side_to_move_ ^ 1, undo.captured_type);
  }

  castling_ = undo.castling;
  en_passant_ = undo.en_passant;
  halfmove_clock_ = undo.halfmove_clock;
  key_ = undo.key;
}

void Position::GeneratePieceMoves(MoveList* list) const {
  const int us = side_to_move_;
  const Bitboard allowed = ~by_color_[us];
  Bitboard movers = by_color_[us] & ~by_type_[kPawn];
  while (movers) {
    const int from = PopLsb(&movers);
    Bitboard targets =
        PieceAttacks(piece_at_[from], from, occupied_, us) & allowed;
    while (targets) {
      list->Add(EncodeMove(from, PopLsb(&targets)));
    }
  }
}

void Position::GenerateCastlingMoves(MoveList* list) const {
  const int us = side_to_move_;
  if (!(by_type_[kKing] & by_color_[us])) return;
  const int rank = us == kWhite ? 0 : 7;
  const int king_square = MakeSquare(4, rank);
  if (piece_at_[king_square] != kKing || color_at_[king_square] != us) return;

  struct CastlingPlan {
    int rook_file;
    int king_target_file;
    int flag;
    std::array<int, 3> empty_files;
    int empty_count;
  };
  static constexpr std::array<CastlingPlan, 2> kPlans = {
      CastlingPlan{7, 6, kFlagCastleKingSide, {5, 6, 0}, 2},
      CastlingPlan{0, 2, kFlagCastleQueenSide, {1, 2, 3}, 3}};

  for (const CastlingPlan& plan : kPlans) {
    const int rook = MakeSquare(plan.rook_file, rank);
    if (!(castling_ & SquareBB(rook))) continue;
    if (piece_at_[rook] != kRook || color_at_[rook] != us) continue;
    bool blocked = false;
    for (int i = 0; i < plan.empty_count; ++i) {
      if (occupied_ & SquareBB(MakeSquare(plan.empty_files[i], rank))) {
        blocked = true;
        break;
      }
    }
    if (blocked) continue;
    // Deliberately no attack test on the king's path: castling through or into
    // attack is legal here, it merely loses.
    list->Add(EncodeMove(king_square, MakeSquare(plan.king_target_file, rank),
                         plan.flag));
  }
}

void Position::GeneratePawnMoves(MoveList* list) const {
  const int us = side_to_move_;
  const int forward = us == kWhite ? 8 : -8;
  const int promotion_rank = us == kWhite ? 7 : 0;
  const int start_rank = us == kWhite ? 1 : 6;
  const Bitboard theirs = by_color_[us ^ 1];

  const auto add_with_promotions = [list](int from, int to, bool promoting) {
    if (promoting) {
      list->Add(EncodeMove(from, to, kFlagPromoteQueen));
      list->Add(EncodeMove(from, to, kFlagPromoteRook));
      list->Add(EncodeMove(from, to, kFlagPromoteBishop));
      list->Add(EncodeMove(from, to, kFlagPromoteKnight));
    } else {
      list->Add(EncodeMove(from, to));
    }
  };

  Bitboard pawns = by_color_[us] & by_type_[kPawn];
  while (pawns) {
    const int from = PopLsb(&pawns);
    const int ahead = from + forward;
    if (ahead >= 0 && ahead < kNumSquares && !(occupied_ & SquareBB(ahead))) {
      const bool promoting = RankOf(ahead) == promotion_rank;
      add_with_promotions(from, ahead, promoting);
      const int twice = ahead + forward;
      if (!promoting && RankOf(from) == start_rank &&
          !(occupied_ & SquareBB(twice))) {
        list->Add(EncodeMove(from, twice, kFlagDoublePush));
      }
    }
    Bitboard captures = kPawnAttacks[us][from] & theirs;
    while (captures) {
      const int to = PopLsb(&captures);
      add_with_promotions(from, to, RankOf(to) == promotion_rank);
    }
    if (en_passant_ >= 0 && (kPawnAttacks[us][from] & SquareBB(en_passant_))) {
      list->Add(EncodeMove(from, en_passant_, kFlagEnPassant));
    }
  }
}

void Position::GenerateMoves(MoveList* list) const {
  GeneratePieceMoves(list);
  GenerateCastlingMoves(list);
  GeneratePawnMoves(list);
}

void Position::GenerateCaptures(MoveList* list) const {
  MoveList all;
  GenerateMoves(&all);
  for (const Move move : all) {
    if (piece_at_[MoveTo(move)] != kNoPiece ||
        MoveFlagOf(move) == kFlagEnPassant || IsPromotion(move)) {
      list->Add(move);
    }
  }
}

std::string Position::BoardFen() const {
  static constexpr char kSymbols[] = "pnbrqk";
  std::string fen;
  for (int rank = 7; rank >= 0; --rank) {
    int empty = 0;
    for (int file = 0; file < 8; ++file) {
      const int square = MakeSquare(file, rank);
      if (piece_at_[square] == kNoPiece) {
        ++empty;
        continue;
      }
      if (empty > 0) {
        fen += static_cast<char>('0' + empty);
        empty = 0;
      }
      const char symbol = kSymbols[piece_at_[square]];
      fen += color_at_[square] == kWhite
                 ? static_cast<char>(symbol - 'a' + 'A')
                 : symbol;
    }
    if (empty > 0) fen += static_cast<char>('0' + empty);
    if (rank > 0) fen += '/';
  }
  return fen;
}

bool PositionFromFen(const std::string& fen, Position* position) {
  position->Clear();
  std::size_t i = 0;
  int rank = 7;
  int file = 0;
  for (; i < fen.size() && fen[i] != ' '; ++i) {
    const char c = fen[i];
    if (c == '/') {
      --rank;
      file = 0;
      continue;
    }
    if (c >= '1' && c <= '8') {
      file += c - '0';
      continue;
    }
    const int color = (c >= 'A' && c <= 'Z') ? kWhite : kBlack;
    int type = kNoPiece;
    switch (c | 32) {
      case 'p': type = kPawn; break;
      case 'n': type = kKnight; break;
      case 'b': type = kBishop; break;
      case 'r': type = kRook; break;
      case 'q': type = kQueen; break;
      case 'k': type = kKing; break;
      default: return false;
    }
    if (!OnBoard(file, rank)) return false;
    position->PutPiece(MakeSquare(file, rank), color, type);
    ++file;
  }
  while (i < fen.size() && fen[i] == ' ') ++i;
  position->set_side_to_move(i < fen.size() && fen[i] == 'b' ? kBlack : kWhite);
  while (i < fen.size() && fen[i] != ' ') ++i;
  while (i < fen.size() && fen[i] == ' ') ++i;

  Bitboard rooks = 0;
  for (; i < fen.size() && fen[i] != ' '; ++i) {
    switch (fen[i]) {
      case 'K': rooks |= SquareBB(MakeSquare(7, 0)); break;
      case 'Q': rooks |= SquareBB(MakeSquare(0, 0)); break;
      case 'k': rooks |= SquareBB(MakeSquare(7, 7)); break;
      case 'q': rooks |= SquareBB(MakeSquare(0, 7)); break;
      default: break;
    }
  }
  position->set_castling_rights(rooks);

  while (i < fen.size() && fen[i] == ' ') ++i;
  if (i + 1 < fen.size() && fen[i] >= 'a' && fen[i] <= 'h') {
    position->set_en_passant_square(
        MakeSquare(fen[i] - 'a', fen[i + 1] - '1'));
  }
  return true;
}

}  // namespace fow
