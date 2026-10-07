#include "tactical_labels.h"
#include "bait_candidates.h"

#include <cstdio>
#include <stdexcept>
#include <string>

namespace {
using namespace fow;
using namespace fow::astra;
int checks = 0;
void Check(bool value, const char* message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
Position Parse(const char* fen) {
  Position p;
  Check(PositionFromFen(fen, &p), "FEN parsed");
  return p;
}
CaptureOpportunity Find(const Position& p, const std::string& move) {
  for (const auto& row : CaptureOpportunities(p)) {
    if (MoveToUci(row.reply) == move) return row;
  }
  throw std::runtime_error("missing capture " + move);
}
Position Mirror(const Position& p) {
  Position result;
  for (int square = 0; square < 64; ++square) {
    if (p.piece_at(square) != kNoPiece) {
      result.PutPiece(square ^ 56, p.color_at(square) ^ 1, p.piece_at(square));
    }
  }
  result.set_side_to_move(p.side_to_move() ^ 1);
  if (p.en_passant_square() >= 0) result.set_en_passant_square(p.en_passant_square() ^ 56);
  return result;
}
void KingTrap() {
  Position p = Parse("7k/R5N1/8/8/8/8/8/K7 b - - 0 1");
  auto row = Find(p, "h8g7");
  Check(row.fatal_king_bait, "king walks onto concealed rook's defended bait");
  Check(row.hidden_king_guard && !row.visible_king_guard, "hidden pre-response guard");
  Check(!row.hidden_safe_recapture, "no fictitious play after terminal king loss");
  Check(Find(Mirror(p), "h1g2").fatal_king_bait, "black offering mirrored king bait");
  Position seen = Parse("1b5k/R5N1/8/8/8/8/8/K7 b - - 0 1");
  auto visible = Find(seen, "h8g7");
  Check(visible.responder_loses_king && visible.visible_king_guard,
        "bishop sees the rook defending bait");
  Check(!visible.fatal_king_bait, "visible guard is not an apparently free king bait");
}
void MaterialTrapAndVisibilityTiming() {
  Position p = Parse("4q2k/8/8/8/4P3/8/8/KB6 b - - 0 1");
  auto row = Find(p, "e8e4");
  Check(row.hidden_safe_recapture && !row.visible_safe_recapture, "hidden bishop recapture");
  Check(row.best_hidden_recapture_net_cp == kPieceValue[kQueen]-kPieceValue[kPawn],
        "net queen for pawn");
  Check(ProfitableHiddenRecapture(row), "profitable concealed material recapture");
  Check(MoveToUci(row.best_hidden_recapture) == "b1e4", "correct recapturer");
  Position after = p;
  UndoState undo;
  after.MakeMove(row.reply, &undo);
  Check((VisibleSquares(after, kBlack) & SquareBB(1)) != 0,
        "guard becomes visible after commitment; label must use view before it");
  Check(ProfitableHiddenRecapture(Find(Mirror(p), "e1e5")), "mirror material bait");
}
void UnsafeRecapture() {
  Position p = Parse("r7/7k/5B2/8/n7/2P5/8/K7 b - - 0 1");
  auto row = Find(p, "a4c3");
  Check(!row.responder_loses_king, "capture is safe for responder");
  Check(row.unsafe_hidden_recapture, "capture unblocks rook onto offering king");
  Check(!row.hidden_safe_recapture && !ProfitableHiddenRecapture(row),
        "recapture leaving own king attacked cannot justify bait");
}
void EnPassant() {
  Position p = Parse("7k/8/8/8/3pP3/8/8/K1B5 b - e3 0 1");
  auto row = Find(p, "d4e3");
  Check(row.victim_square == 28, "en passant victim is e4, not landing square e3");
  Check(row.hidden_safe_recapture, "bishop can recapture on EP landing square");
  Check(row.best_hidden_recapture_net_cp == 0, "equal pawn exchange");
  Check(!ProfitableHiddenRecapture(row), "equal exchange is not material-winning bait");
}
void PromotionAccounting() {
  Position p = Parse("1R6/6k1/8/8/8/8/p7/1R5K b - - 0 1");
  for (const char promotion : std::string("qnrb")) {
    auto row = Find(p, std::string("a2b1") + promotion);
    Check(row.hidden_safe_recapture, "can capture promoted piece");
    Check(row.best_hidden_recapture_net_cp == kPieceValue[kPawn]-kPieceValue[kRook],
          "capturing a promoted queen does not count free promotion material twice");
    Check(!ProfitableHiddenRecapture(row), "losing a rook for a pawn is not profitable bait");
  }
}
void TerminalInput() {
  Position terminal = Parse("r6k/8/8/8/8/8/8/K7 b - - 0 1");
  bool rejected = false;
  try { (void)CaptureOpportunities(terminal); }
  catch (const std::invalid_argument&) { rejected = true; }
  Check(rejected, "no actor opportunity after previous mover already lost");
}
Move ParseMove(const Position& position, const std::string& text) {
  MoveList moves;
  position.GenerateMoves(&moves);
  for (Move move : moves) if (MoveToUci(move) == text) return move;
  throw std::runtime_error("missing move " + text);
}
void CandidateAdmission() {
  Position p = Parse("4q2k/8/8/8/8/4P3/8/KB6 w - - 0 1");
  auto advance = DescribeBait({p}, kWhite, -1, ParseMove(p, "e3e4"), 16);
  auto quiet = DescribeBait({p}, kWhite, -1, ParseMove(p, "a1a2"), 16);
  Check(advance.mean_conditional_material_cp == kPieceValue[kQueen]-kPieceValue[kPawn],
        "scouting pawn creates a hidden bishop's recapture opportunity");
  Check(advance.particles_checked == 1 && HasBait(advance), "population cap is respected");
  Check(!HasBait(quiet) && BaitBefore(advance, quiet), "quiet move creates no such trap");
  Position no_defender = Parse("4q2k/8/8/8/8/4P3/8/K7 w - - 0 1");
  auto mixed = DescribeBait({p, no_defender}, kWhite, -1, ParseMove(p, "e3e4"), 16);
  Check(mixed.mean_conditional_material_cp == advance.mean_conditional_material_cp / 2,
        "absent hidden defenders reduce belief-averaged opportunity");
  Position unsafe = Parse("r3q2k/8/8/8/N3P3/8/8/KB6 w - - 0 1");
  auto fatal = DescribeBait({unsafe}, kWhite, -1, ParseMove(unsafe, "a4c5"), 16);
  Check(!HasBait(fatal), "opening a rook line onto our king earns no bait admission");
  Position black = Mirror(p);
  auto mirrored = DescribeBait({black}, kBlack, -1, ParseMove(black, "e6e5"), 16);
  Check(mirrored.mean_conditional_material_cp == advance.mean_conditional_material_cp,
        "candidate geometry is color symmetric");
}
}  // namespace

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  KingTrap(); MaterialTrapAndVisibilityTiming(); UnsafeRecapture();
  EnPassant(); PromotionAccounting(); TerminalInput();
  CandidateAdmission();
  std::printf("tactical_labels: %d checks, 0 failures\n", checks);
}
