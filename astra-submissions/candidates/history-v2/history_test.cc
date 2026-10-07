// Regression tests for bounded recovery with history-dependent opponent priors.
#include "belief.h"

#include <cmath>
#include <tuple>
#include <vector>

#include "bitboard.h"
#include "observation.h"
#include "opponent_model.h"
#include "tests/testing.h"

namespace fow {
struct BeliefStateTestAccess {
  static void Assign(BeliefState* b, const std::vector<Position>& positions,
                     const std::vector<int>& to, const std::vector<bool>& captures) {
    b->particles_ = positions;
    b->last_to_ = to;
    b->last_capture_ = captures;
    b->representative_valid_ = false;
  }
  static void Clear(BeliefState* b) {
    b->particles_.clear(); b->last_to_.clear(); b->last_capture_.clear();
  }
  static void Seed(BeliefState* b, const Position& p, int to = -1, bool capture = false) {
    Assign(b, std::vector<Position>(b->target_count_, p),
           std::vector<int>(b->target_count_, to), std::vector<bool>(b->target_count_, capture));
    b->seen_any_ = true;
    b->previous_mover_ = p.side_to_move() ^ 1;
    b->history_full_certified_ = false;
    b->history_.clear();
    b->RememberHistory(Observation(RenderObservation(p, b->our_side_)));
  }
  static void Remember(BeliefState* b, const Position& p) {
    b->RememberHistory(Observation(RenderObservation(p, b->our_side_)));
  }
  static std::vector<std::tuple<int, bool, double>> Support(const BeliefState& b) {
    std::vector<std::tuple<int, bool, double>> result;
    for (const auto& p : b.history_.back().support) result.emplace_back(p.last_to, p.last_capture, p.weight);
    return result;
  }
  static bool MemoryIs(const BeliefState& b, int to, bool capture) {
    if (b.last_to_.size() != b.particles_.size() || b.last_capture_.size() != b.particles_.size()) return false;
    for (std::size_t i = 0; i < b.particles_.size(); ++i) {
      if (b.last_to_[i] != to || b.last_capture_[i] != capture) return false;
    }
    return true;
  }
  static void Filter(BeliefState* b, const Observation& view, BeliefUpdateReport* report) {
    b->FilterLiveObservation(view, report);
  }
  static void KeepOnlyOldestAnchor(BeliefState* b) {
    for (std::size_t i=1; i<b->history_.size(); ++i) b->history_[i].support.clear();
  }
  static bool FailedRecoveryKeepsRng(BeliefState* b, const Observation& view,
                                    BeliefUpdateReport* report) {
    const auto before=b->rng_;
    b->previous_mover_=b->our_side_;
    const bool recovered=b->RecoverFromHistory(view,report);
    return !recovered && b->rng_==before;
  }
};
namespace {
Position Fen(const char* text) {
  Position p;
  FOW_EXPECT_TRUE(PositionFromFen(text, &p));
  return p;
}
Position Start() { return Fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); }
Move Find(const Position& p, const char* uci) {
  MoveList moves; p.GenerateMoves(&moves);
  for (Move m : moves) if (MoveToUci(m) == uci) return m;
  FOW_EXPECT_TRUE(false);
  return kNullMove;
}
void Live(const BeliefState& belief, const Position& truth) {
  FOW_EXPECT_TRUE(belief.particle_count() > 0);
  for (const auto& p : belief.particles()) {
    FOW_EXPECT_EQ(RenderObservation(p, belief.our_side()), RenderObservation(truth, belief.our_side()));
    FOW_EXPECT_TRUE(!p.PreviousMoverIsLost());
  }
}

void CheckpointsKeepDifferentPriorMemoriesSeparate() {
  const Position p = Start();
  BeliefState b(kWhite, 4, 17, 2); b.set_history_mode(2);
  BeliefStateTestAccess::Assign(&b, {p,p,p,p}, {17,17,22,22}, {false,true,false,false});
  BeliefStateTestAccess::Remember(&b, p);
  const auto support = BeliefStateTestAccess::Support(b);
  FOW_EXPECT_EQ(support.size(), std::size_t{3});
  FOW_EXPECT_TRUE(support[0] == std::make_tuple(17,false,1.0));
  FOW_EXPECT_TRUE(support[1] == std::make_tuple(17,true,1.0));
  FOW_EXPECT_TRUE(support[2] == std::make_tuple(22,false,2.0));
}

void OwnMoveFilteringKeepsMemoryAligned() {
  Position allowed = Fen("4k3/8/8/8/8/8/8/4K2R w K - 0 1");
  Position blocked = allowed; blocked.set_castling_rights(0);
  for (int mode : {0,1,2}) {
    BeliefState b(kWhite, 2, 18, 2); b.set_history_mode(mode);
    BeliefStateTestAccess::Assign(&b, {blocked,allowed}, {17,22}, {true,false});
    b.ApplyOurMove(Find(allowed,"e1g1"));
    FOW_EXPECT_EQ(b.particle_count(),1);
    FOW_EXPECT_TRUE(BeliefStateTestAccess::MemoryIs(b,22,false));
    BeliefStateTestAccess::Assign(&b, {blocked}, {17}, {true});
    b.ApplyOurMove(Find(allowed,"e1g1"));
    FOW_EXPECT_EQ(b.particle_count(),0);
    FOW_EXPECT_TRUE(BeliefStateTestAccess::MemoryIs(b,-1,false));
  }
}

void ExactViewFilteringKeepsMemoryAligned() {
  Position truth = Start();
  Position wrong = truth; wrong.RemovePiece(0);
  BeliefState b(kWhite, 2, 19, 2); b.set_history_mode(1);
  BeliefStateTestAccess::Assign(&b, {wrong,truth}, {17,22}, {true,false});
  BeliefUpdateReport report;
  BeliefStateTestAccess::Filter(&b,Observation(RenderObservation(truth,kWhite)),&report);
  FOW_EXPECT_EQ(report.strict_rejected,1);
  FOW_EXPECT_EQ(b.particle_count(),1);
  FOW_EXPECT_TRUE(BeliefStateTestAccess::MemoryIs(b,22,false));
}

void RecoveryUpdatesAndRetainsCaptureMemory() {
  Position truth = Fen("7k/8/8/8/1R6/2b5/8/7K w - - 0 1");
  BeliefState b(kWhite, 32, 20, 2); b.set_history_mode(2);
  BeliefStateTestAccess::Seed(&b, truth,18,false);
  for (const char* uci : {"h1g1","c3b4"}) {
    const bool ours=truth.side_to_move()==kWhite;
    const Move move=Find(truth,uci);
    if (ours) b.ApplyOurMove(move);
    UndoState undo; truth.MakeMove(move,&undo);
    BeliefStateTestAccess::Clear(&b);
    const auto report=b.Observe(Observation(RenderObservation(truth,kWhite)),ours);
    FOW_EXPECT_TRUE(report.history_recovered);
    FOW_EXPECT_TRUE(!report.history_full_certified);
    FOW_EXPECT_EQ(report.recovery_attempts,0);
    FOW_EXPECT_TRUE(BeliefStateTestAccess::MemoryIs(b,ours?18:25,!ours));
    Live(b,truth);
  }
}

void LearnedPriorActuallyDependsOnMemory() {
  Position p=Start(); p.set_side_to_move(kBlack);
  Move move=Find(p,"b8c6");
  const double fresh=LearnedMovePlausibility(&p,move,-1,false);
  const double repeat=LearnedMovePlausibility(&p,move,57,false);
  const double capture=LearnedMovePlausibility(&p,move,57,true);
  FOW_EXPECT_TRUE(std::abs(fresh-repeat)>1e-6);
  FOW_EXPECT_TRUE(std::abs(repeat-capture)>1e-6);
}

void OpeningRecoveryWorksWithEveryPriorAndColor() {
  for (int prior : {0,1,2}) for (int side : {kWhite,kBlack}) {
    Position truth=Start();
    BeliefState b(side,32,902+side,prior); b.set_history_mode(2); b.set_visibility_deductions(true);
    b.Observe(Observation(RenderObservation(truth,side)),false);
    for (const char* uci : {"e2e4","e7e5","g1f3","b8c6"}) {
      const bool ours=truth.side_to_move()==side;
      const Move move=Find(truth,uci);
      if (ours) b.ApplyOurMove(move);
      UndoState undo; truth.MakeMove(move,&undo);
      BeliefStateTestAccess::Clear(&b);
      const auto report=b.Observe(Observation(RenderObservation(truth,side)),ours);
      FOW_EXPECT_TRUE(report.history_recovered);
      FOW_EXPECT_TRUE(report.history_full_certified);
      FOW_EXPECT_TRUE(report.history_transitions<=1000000);
      FOW_EXPECT_EQ(report.recovery_attempts,0);
      Live(b,truth);
    }
  }
}

void RecoveryRetainsRuleMetadata() {
  struct Case { const char* fen; const char* move; };
  for (const Case c : {
      Case{"4k3/8/8/8/8/8/8/4K2R w K - 0 1","e1g1"},
      Case{"4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1","e5d6"},
      Case{"4k3/P7/8/8/8/8/8/4K3 w - - 0 1","a7a8n"},
      Case{"4k2r/8/8/8/8/8/8/4K3 b k - 0 1","e8g8"},
      Case{"4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1","e4d3"},
      Case{"4k3/8/8/8/8/8/p7/4K3 b - - 0 1","a2a1n"}}) {
    Position truth=Fen(c.fen); const int side=truth.side_to_move();
    BeliefState b(side,8,994,2); b.set_history_mode(2);
    BeliefStateTestAccess::Seed(&b,truth,35,true);
    const Move move=Find(truth,c.move); b.ApplyOurMove(move);
    UndoState undo; truth.MakeMove(move,&undo); BeliefStateTestAccess::Clear(&b);
    const auto report=b.Observe(Observation(RenderObservation(truth,side)),true);
    FOW_EXPECT_TRUE(report.history_recovered);
    FOW_EXPECT_TRUE(!report.history_full_certified);
    FOW_EXPECT_TRUE(BeliefStateTestAccess::MemoryIs(b,35,true));
    for (const auto& p : b.particles()) {
      FOW_EXPECT_EQ(p.BoardFen(),truth.BoardFen());
      FOW_EXPECT_EQ(p.castling_rights(),truth.castling_rights());
      FOW_EXPECT_EQ(p.en_passant_square(),truth.en_passant_square());
      FOW_EXPECT_EQ(p.halfmove_clock(),truth.halfmove_clock());
    }
  }
}

void ImpossibleOwnHistoryIsNotCertified() {
  Position truth=Start();
  BeliefState b(kWhite,8,400,2); b.set_history_mode(2);
  b.Observe(Observation(RenderObservation(truth,kWhite)),false);
  b.ApplyOurMove(Find(truth,"e2e4"));
  const auto report=b.Observe(Observation(RenderObservation(truth,kWhite)),true);
  FOW_EXPECT_TRUE(report.history_attempted);
  FOW_EXPECT_TRUE(!report.history_recovered);
  FOW_EXPECT_TRUE(!report.history_full_certified);
  FOW_EXPECT_TRUE(report.recovery_attempts>0 && report.recovery_attempts<=256);
  FOW_EXPECT_TRUE(report.history_transitions<=1000000);
}

void FailedReplayDoesNotPerturbFallbackRandomness() {
  Position truth=Start();
  BeliefState b(kWhite,1,501,1); b.set_history_mode(2);
  b.Observe(Observation(RenderObservation(truth,kWhite)),false);
  for (const char* uci : {"e2e3","e7e6","g1f3","b8c6"}) {
    const bool ours=truth.side_to_move()==kWhite;
    const Move move=Find(truth,uci);
    if (ours) b.ApplyOurMove(move);
    UndoState undo; truth.MakeMove(move,&undo);
    b.Observe(Observation(RenderObservation(truth,kWhite)),ours);
  }
  // Force a long replay with a beam prune, followed by an impossible own edge.
  // No hypothesis can move d2d4 and still leave our pawn on d2.
  BeliefStateTestAccess::KeepOnlyOldestAnchor(&b);
  b.ApplyOurMove(Find(truth,"d2d4"));
  BeliefUpdateReport report;
  FOW_EXPECT_TRUE(BeliefStateTestAccess::FailedRecoveryKeepsRng(
      &b,Observation(RenderObservation(truth,kWhite)),&report));
  FOW_EXPECT_TRUE(report.history_attempted);
  FOW_EXPECT_TRUE(!report.history_recovered);
  FOW_EXPECT_TRUE(report.history_transitions>64);
}
}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables(); fow::InitializeZobrist();
  FOW_RUN_TEST(fow::CheckpointsKeepDifferentPriorMemoriesSeparate);
  FOW_RUN_TEST(fow::OwnMoveFilteringKeepsMemoryAligned);
  FOW_RUN_TEST(fow::ExactViewFilteringKeepsMemoryAligned);
  FOW_RUN_TEST(fow::RecoveryUpdatesAndRetainsCaptureMemory);
  FOW_RUN_TEST(fow::LearnedPriorActuallyDependsOnMemory);
  FOW_RUN_TEST(fow::OpeningRecoveryWorksWithEveryPriorAndColor);
  FOW_RUN_TEST(fow::RecoveryRetainsRuleMetadata);
  FOW_RUN_TEST(fow::ImpossibleOwnHistoryIsNotCertified);
  FOW_RUN_TEST(fow::FailedReplayDoesNotPerturbFallbackRandomness);
  return fow::testing::Summarize("history_v2");
}
