// Bayesian state-retention tests. Test-only access exposes weights; replay truth
// is never passed to the runtime belief as evidence.
#include "belief.h"
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
#include "tests/testing.h"

namespace fow {
using Entry = std::tuple<Position, double, int, bool>;
struct BeliefStateTestAccess {
  static void Seed(BeliefState* b, const std::vector<Entry>& states) {
    b->frontier_.clear();
    for (const auto& [p,w,to,capture] : states) b->frontier_.push_back({p,w,to,capture});
    b->seen_any_=true;
    b->previous_mover_=std::get<0>(states.front()).side_to_move() ^ 1;
    b->previous_view_=Observation(RenderObservation(std::get<0>(states.front()),b->our_side_));
    b->have_previous_view_=true;
    BeliefUpdateReport report; b->SyncFrontierParticles(&report);
  }
  static std::vector<Entry> States(const BeliefState& b) {
    std::vector<Entry> result;
    for (const auto& s : b.frontier_) result.emplace_back(s.position,s.weight,s.last_to,s.last_capture);
    return result;
  }
  static void ResampleWorking(BeliefState* b) { BeliefUpdateReport r; b->SyncFrontierParticles(&r); }
  static bool RngEqual(const BeliefState& a,const BeliefState& b) { return a.frontier_rng_==b.frontier_rng_; }
  static int Census(const BeliefState& b,int type) { return b.enemy_census_[type]; }
};
namespace {
Position Fen(const char* text) { Position p; FOW_EXPECT_TRUE(PositionFromFen(text,&p)); return p; }
Position Start() { return Fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); }
Move Find(const Position& p,const char* text) {
  MoveList moves; p.GenerateMoves(&moves);
  for (Move m:moves) if (MoveToUci(m)==text) return m;
  FOW_EXPECT_TRUE(false); return kNullMove;
}
std::string Key(const Position& p,int to,bool capture) {
  std::string key;
  for (int sq=0;sq<64;++sq) key+=p.piece_at(sq)==kNoPiece?'-':PieceTypeToSymbol(p.piece_at(sq),p.color_at(sq));
  return key+":"+std::to_string(p.side_to_move())+":"+std::to_string(p.castling_rights())+":"+
      std::to_string(p.en_passant_square())+":"+std::to_string(p.halfmove_clock())+":"+
      std::to_string(to)+":"+std::to_string(capture);
}
std::map<std::string,double> Distribution(const BeliefState& b) {
  std::map<std::string,double> out;
  for (const auto& [p,w,to,capture]:BeliefStateTestAccess::States(b)) out[Key(p,to,capture)]+=w;
  return out;
}
void SameDistribution(const BeliefState& a,const BeliefState& b) {
  const auto x=Distribution(a),y=Distribution(b);
  FOW_EXPECT_EQ(x.size(),y.size());
  for (const auto& [key,w]:x) { auto it=y.find(key); FOW_EXPECT_TRUE(it!=y.end());
    if (it!=y.end()) FOW_EXPECT_TRUE(std::abs(w-it->second)<1e-12); }
}

void WeightedUpdateMatchesExhaustiveBayes() {
  const auto rook=Fen("7k/7r/8/8/8/8/8/K7 b - - 0 1");
  const auto knight=Fen("7k/6n1/8/8/8/8/8/K7 b - - 0 1");
  const std::vector<Entry> before={{rook,.17,-1,false},{knight,.83,-1,false}};
  const std::string view=RenderObservation(rook,kWhite);
  // Independent exhaustive oracle: uniform legal prior per parent, then exact
  // observation and survival likelihood. Parents have different move counts.
  std::map<std::string,double> expected; double total=0;
  int transitions=0;
  for (const auto& [parent,w,to,capture]:before) {
    (void)to; (void)capture; MoveList moves; parent.GenerateMoves(&moves);
    for (Move m:moves) {
      ++transitions; Position child=parent;
      const bool takes=parent.piece_at(MoveTo(m))!=kNoPiece || MoveFlagOf(m)==kFlagEnPassant;
      UndoState undo; child.MakeMove(m,&undo);
      if (child.PreviousMoverIsLost() || RenderObservation(child,kWhite)!=view) continue;
      expected[Key(child,MoveTo(m),takes)]+=w/moves.size(); total+=w/moves.size();
    }
  }
  BeliefState b(kWhite,3,91,0); b.set_history_mode(1); b.set_frontier_capacity(256);
  BeliefStateTestAccess::Seed(&b,before);
  const auto report=b.Observe(Observation(view),false);
  const auto actual=Distribution(b);
  FOW_EXPECT_TRUE(!report.collapsed && !report.frontier_reduced);
  FOW_EXPECT_EQ(report.enumerated_transitions,transitions);
  FOW_EXPECT_EQ(actual.size(),expected.size());
  FOW_EXPECT_TRUE(actual.size()>static_cast<std::size_t>(b.particle_count()));
  for (const auto& [key,w]:expected) {
    auto it=actual.find(key); FOW_EXPECT_TRUE(it!=actual.end());
    if (it!=actual.end()) FOW_EXPECT_TRUE(std::abs(it->second-w/total)<1e-12);
  }
}

void RareUnsampledWorldSurvivesUntilItsRevealingObservation() {
  Position rare=Fen("7k/8/8/8/8/2r5/8/KR6 w - - 0 1");
  const Position common=Fen("7k/8/8/8/8/3r4/8/KR6 w - - 0 1");
  FOW_EXPECT_EQ(RenderObservation(rare,kWhite),RenderObservation(common,kWhite));
  BeliefState b(kWhite,1,92,0); b.set_frontier_capacity(64);
  BeliefStateTestAccess::Seed(&b,{{common,1.0-1e-15,-1,false},{rare,1e-15,-1,false}});
  FOW_EXPECT_EQ(b.particles().front().piece_at(18),kNoPiece);
  const Move scout=Find(rare,"b1b3"); b.ApplyOurMove(scout); UndoState undo; rare.MakeMove(scout,&undo);
  const auto r=b.Observe(Observation(RenderObservation(rare,kWhite)),true);
  FOW_EXPECT_TRUE(!r.collapsed);
  FOW_EXPECT_EQ(r.frontier_states,1);
  FOW_EXPECT_EQ(b.particles().front().piece_at(18),kRook);
  FOW_EXPECT_TRUE(std::abs(std::get<1>(BeliefStateTestAccess::States(b).front())-1.0)<1e-12);
}

void OwnMovePreservesMetadataMemoryAndCensus() {
  Position p=Fen("k7/8/8/8/8/8/8/4K2R w K - 0 1"),blocked=p;
  blocked.set_castling_rights(0);
  BeliefState b(kWhite,8,93,2); b.set_frontier_capacity(64);
  BeliefStateTestAccess::Seed(&b,{{blocked,.5,17,true},{p,.2,17,true},{p,.3,22,false}});
  const Move castle=Find(p,"e1g1"); b.ApplyOurMove(castle); UndoState undo; p.MakeMove(castle,&undo);
  const auto r=b.Observe(Observation(RenderObservation(p,kWhite)),true);
  FOW_EXPECT_TRUE(!r.collapsed); FOW_EXPECT_EQ(r.frontier_states,2);
  for (const auto& [state,w,to,capture]:BeliefStateTestAccess::States(b)) {
    FOW_EXPECT_EQ(state.castling_rights(),Bitboard{0});
    FOW_EXPECT_EQ(state.KingSquare(kWhite),6);
    FOW_EXPECT_EQ(state.piece_at(5),kRook);
    FOW_EXPECT_TRUE((to==17 && capture && std::abs(w-.4)<1e-12) ||
                    (to==22 && !capture && std::abs(w-.6)<1e-12));
  }
  Position ep=Fen("7k/8/8/3pP3/8/8/8/K7 w - d6 0 1");
  BeliefState c(kWhite,8,94,1); c.set_frontier_capacity(64);
  BeliefStateTestAccess::Seed(&c,{{ep,1,35,true}});
  const int count=BeliefStateTestAccess::Census(c,kPawn);
  const Move takes=Find(ep,"e5d6"); c.ApplyOurMove(takes); ep.MakeMove(takes,&undo);
  const auto er=c.Observe(Observation(RenderObservation(ep,kWhite)),true);
  FOW_EXPECT_TRUE(!er.collapsed);
  FOW_EXPECT_EQ(BeliefStateTestAccess::Census(c,kPawn),count-1);
  FOW_EXPECT_EQ(b.particle_count(),8);
  const auto states=BeliefStateTestAccess::States(c);
  FOW_EXPECT_EQ(std::get<0>(states.front()).en_passant_square(),-1);
  FOW_EXPECT_EQ(std::get<0>(states.front()).piece_at(35),kNoPiece);
}

void CapacityReductionIsSeparateFromWorkingSamples() {
  Position p=Start(); UndoState undo; p.MakeMove(Find(p,"e2e4"),&undo);
  for (int seed=1;seed<=24;++seed) {
    BeliefState a(kWhite,3,seed,0),b(kWhite,61,seed,0);
    a.set_frontier_capacity(4); b.set_frontier_capacity(4);
    BeliefStateTestAccess::Seed(&a,{{p,1,-1,false}});
    BeliefStateTestAccess::Seed(&b,{{p,1,-1,false}});
    for (int i=0;i<5;++i) BeliefStateTestAccess::ResampleWorking(&a);
    const Observation view(RenderObservation(p,kWhite));
    const auto ra=a.Observe(view,false),rb=b.Observe(view,false);
    FOW_EXPECT_TRUE(ra.frontier_reduced && rb.frontier_reduced);
    FOW_EXPECT_EQ(ra.enumerated_transitions,20);
    FOW_EXPECT_TRUE(ra.frontier_states<=4 && ra.frontier_states>0);
    SameDistribution(a,b);
    FOW_EXPECT_TRUE(BeliefStateTestAccess::RngEqual(a,b));
    FOW_EXPECT_EQ(a.particle_count(),3); FOW_EXPECT_EQ(b.particle_count(),61);
  }
}

void ReductionIncludesLateParents() {
  const Position early=Fen("7k/7r/8/8/8/8/8/K7 b - - 0 1");
  const Position late=Fen("6k1/6n1/8/8/8/8/8/K7 b - - 0 1");
  // The late parent has 99% prior mass. A cap applied during traversal would
  // fill entirely from the first parent's >4 accepted children.
  int knight_trials=0;
  for (int seed=1;seed<=24;++seed) {
    BeliefState b(kWhite,8,seed,0); b.set_frontier_capacity(4);
    BeliefStateTestAccess::Seed(&b,{{early,.01,-1,false},{late,.99,-1,false}});
    const auto r=b.Observe(Observation(RenderObservation(early,kWhite)),false);
    FOW_EXPECT_TRUE(r.frontier_reduced); FOW_EXPECT_EQ(r.expanded_predecessors,2);
    double total=0,late_mass=0;
    for (const auto& [p,w,to,capture]:BeliefStateTestAccess::States(b)) {
      (void)to; (void)capture; total+=w; if (p.pieces(kKnight,kBlack)) late_mass+=w;
    }
    FOW_EXPECT_TRUE(std::abs(total-1.0)<1e-12); knight_trials+=late_mass>.5;
  }
  FOW_EXPECT_EQ(knight_trials,24);
}

void ResetDoesNotMergeRuleStatesOrPriorMemory() {
  const Position p=Start(); Position rights=p,clock=p,ep=p;
  rights.set_castling_rights(0); clock.set_halfmove_clock(1); ep.set_en_passant_square(20);
  BeliefState b(kWhite,16,95,2); b.set_frontier_capacity(16);
  BeliefStateTestAccess::Seed(&b,{{p,.2,17,true},{p,.2,17,false},{rights,.2,17,true},
      {clock,.2,17,true},{ep,.2,17,true}});
  FOW_EXPECT_EQ(Distribution(b).size(),std::size_t{5});
  const Move move=Find(p,"b1c3"); b.ApplyOurMove(move);
  // En-passant and the old halfmove field converge after some moves; the
  // history-dependent move prior and castling fields must stay distinct.
  FOW_EXPECT_TRUE(Distribution(b).size()>=3);
}

void InvalidConfigurationFailsBeforeUse() {
  BeliefState b(kWhite,1,96); bool threw=false;
  try { b.set_frontier_capacity(32769); } catch (const std::invalid_argument&) { threw=true; }
  FOW_EXPECT_TRUE(threw);
  b.set_history_mode(2); threw=false;
  try { b.set_frontier_capacity(8); } catch (const std::invalid_argument&) { threw=true; }
  FOW_EXPECT_TRUE(threw);
}
}  // namespace
}  // namespace fow
int main() {
  fow::InitializeAttackTables(); fow::InitializeZobrist();
  FOW_RUN_TEST(fow::WeightedUpdateMatchesExhaustiveBayes);
  FOW_RUN_TEST(fow::RareUnsampledWorldSurvivesUntilItsRevealingObservation);
  FOW_RUN_TEST(fow::OwnMovePreservesMetadataMemoryAndCensus);
  FOW_RUN_TEST(fow::CapacityReductionIsSeparateFromWorkingSamples);
  FOW_RUN_TEST(fow::ReductionIncludesLateParents);
  FOW_RUN_TEST(fow::ResetDoesNotMergeRuleStatesOrPriorMemory);
  FOW_RUN_TEST(fow::InvalidConfigurationFailsBeforeUse);
  return fow::testing::Summarize("weighted_frontier");
}
