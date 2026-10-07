// Copyright 2026. Fog of War chess engine.
//
// Tests for the decision procedure as a whole.
//
// The contract that matters is that the engine only ever returns a move the
// referee will accept, and that it stays inside its clock. Both are checked by
// driving it through complete games exactly as the protocol does, with the
// opponent hidden, and verifying every single move it produces against the move
// list the rules allow.

#include "../engine.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <string>

#include "../bitboard.h"
#include "../observation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
namespace {

constexpr char kStartFen[] =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

// Small and fast, so the tests exercise the whole pipeline rather than the clock.
EngineOptions FastOptions() {
  EngineOptions options;
  options.particle_count = 96;
  options.shortlist_size = 4;
  options.hypothesis_count = 4;
  options.regret_iterations = 300;
  options.transposition_megabytes = 8;
  options.time_reserve = 0.0;
  options.time_cap = 0.06;
  return options;
}

struct GameOutcome {
  int plies = 0;
  int illegal_moves = 0;
  int null_moves = 0;
  double worst_overrun = 0.0;
};

// Plays a full game, our engine against random legal play, driving the protocol
// faithfully: an observation before every ply, a clock only on our turn.
GameOutcome PlayAgainstRandom(int our_side, uint64_t seed, int max_plies,
                             const EngineOptions& options) {
  std::mt19937_64 rng(seed);
  Position truth;
  PositionFromFen(kStartFen, &truth);
  Engine engine(our_side, 10.0, 0.05, options, seed);
  GameOutcome outcome;
  bool we_just_moved = false;

  for (int ply = 0; ply < max_plies; ++ply) {
    const Observation view(RenderObservation(truth, our_side));
    engine.Observe(view, we_just_moved);
    we_just_moved = false;
    ++outcome.plies;

    MoveList legal;
    truth.GenerateMoves(&legal);
    if (legal.empty()) break;

    Move move;
    if (truth.side_to_move() == our_side) {
      DecisionTrace trace;
      const auto started = std::chrono::steady_clock::now();
      move = engine.ChooseMove(view, 10.0, &trace);
      const double spent = std::chrono::duration<double>(
                               std::chrono::steady_clock::now() - started)
                               .count();
      if (spent - trace.budget > outcome.worst_overrun) {
        outcome.worst_overrun = spent - trace.budget;
      }
      if (move == kNullMove) {
        ++outcome.null_moves;
        break;
      }
      // The only thing that truly must hold: the move is legal.
      bool allowed = false;
      for (const Move candidate : legal) {
        if (candidate == move) allowed = true;
      }
      if (!allowed) ++outcome.illegal_moves;
      engine.NotifyMovePlayed(move);
      we_just_moved = true;
    } else {
      std::uniform_int_distribution<int> pick(0, legal.size() - 1);
      move = legal[pick(rng)];
    }
    UndoState undo;
    truth.MakeMove(move, &undo);
    if (truth.KingSquare(kWhite) < 0 || truth.KingSquare(kBlack) < 0) break;
  }
  return outcome;
}

// Every move the engine plays, in whole games from both colours, must be legal.
// This is the property that makes an illegal-move forfeit impossible.
void EveryMoveTheEngineReturnsIsLegal() {
  int plies = 0;
  int illegal = 0;
  double worst_overrun = 0.0;
  for (int game = 0; game < 4; ++game) {
    for (const int side : {kWhite, kBlack}) {
      const GameOutcome outcome =
          PlayAgainstRandom(side, 400 + game * 11 + side, 40, FastOptions());
      plies += outcome.plies;
      illegal += outcome.illegal_moves;
      worst_overrun = std::max(worst_overrun, outcome.worst_overrun);
    }
  }
  FOW_EXPECT_TRUE(plies > 100);
  FOW_EXPECT_EQ(illegal, 0);
  // Overrunning the budget by a whole second would risk the game clock.
  std::fprintf(stderr, "       %d plies, worst budget overrun %.3fs\n", plies,
               worst_overrun);
  FOW_EXPECT_TRUE(worst_overrun < 0.5);
}

// With the matrix game disabled the engine must still behave, since that is the
// comparison used to decide whether solving the game earns its clock.
void WorksWithTheMatrixGameDisabled() {
  EngineOptions options = FastOptions();
  options.use_matrix_game = false;
  const GameOutcome outcome = PlayAgainstRandom(kWhite, 77, 30, options);
  FOW_EXPECT_EQ(outcome.illegal_moves, 0);
  FOW_EXPECT_TRUE(outcome.plies > 5);
}

// The clock policy must never ask for more time than is left, must stay positive,
// and must settle near the increment so a long game cannot run it out.
void TimeBudgetIsAlwaysAffordable() {
  EngineOptions options;
  Engine engine(kWhite, 180.0, 2.0, options, 1);
  for (const double remaining : {180.0, 120.0, 60.0, 30.0, 12.0, 6.0, 3.0, 1.0,
                                 0.4, 0.05}) {
    const double budget = engine.TimeBudget(remaining);
    FOW_EXPECT_TRUE(budget > 0.0);
    FOW_EXPECT_TRUE(budget < remaining);
    FOW_EXPECT_TRUE(budget <= options.time_cap + 1e-9);
  }
  // Deep in a long game the budget should be of the order of the increment, not
  // of the remaining clock.
  FOW_EXPECT_TRUE(engine.TimeBudget(20.0) < 3.0);
  // And it must shrink as the clock does.
  FOW_EXPECT_TRUE(engine.TimeBudget(20.0) < engine.TimeBudget(180.0) + 1e-9);
}

// A position with exactly one legal move must be handled without any search.
void ReturnsTheOnlyMoveWhenForced() {
  EngineOptions options = FastOptions();
  Engine engine(kWhite, 10.0, 0.05, options, 5);
  // White king on a1 boxed in by its own pieces except for one square.
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("7k/8/8/8/8/8/PP6/KP6 w - - 0 1", &truth));
  const Observation view(RenderObservation(truth, kWhite));
  engine.Observe(view, false);
  DecisionTrace trace;
  const Move move = engine.ChooseMove(view, 10.0, &trace);
  FOW_EXPECT_TRUE(move != kNullMove);
  MoveList legal;
  truth.GenerateMoves(&legal);
  bool allowed = false;
  for (const Move candidate : legal) {
    if (candidate == move) allowed = true;
  }
  FOW_EXPECT_TRUE(allowed);
}

// Environment overrides exist so configurations can be measured head to head
// without recompiling. If they silently failed, every such measurement would be
// comparing a configuration against itself.
void EnvironmentOverridesAreApplied() {
  const EngineOptions defaults = EngineOptionsFromEnvironment();
  FOW_EXPECT_TRUE(defaults.piece_risk_weight > 0.0);

  setenv("FOW_PIECE_RISK", "0", 1);
  setenv("FOW_PARTICLES", "77", 1);
  setenv("FOW_HYPOTHESES", "3", 1);
  setenv("FOW_MATRIX_GAME", "0", 1);
  setenv("FOW_SPECULATIVE_WIN", "9000", 1);
  const EngineOptions tuned = EngineOptionsFromEnvironment();
  FOW_EXPECT_EQ(tuned.piece_risk_weight, 0.0);
  FOW_EXPECT_EQ(tuned.particle_count, 77);
  FOW_EXPECT_EQ(tuned.hypothesis_count, 3);
  FOW_EXPECT_TRUE(!tuned.use_matrix_game);
  FOW_EXPECT_EQ(tuned.search.speculative_win_score, 9000);

  // A nonsense value must leave the default alone rather than zero it.
  setenv("FOW_PARTICLES", "not-a-number", 1);
  FOW_EXPECT_EQ(EngineOptionsFromEnvironment().particle_count,
                defaults.particle_count);

  // A value that would break the engine is clamped, not obeyed.
  setenv("FOW_PARTICLES", "0", 1);
  FOW_EXPECT_TRUE(EngineOptionsFromEnvironment().particle_count >= 1);

  for (const char* name : {"FOW_PIECE_RISK", "FOW_PARTICLES", "FOW_HYPOTHESES",
                           "FOW_MATRIX_GAME", "FOW_SPECULATIVE_WIN"}) {
    unsetenv(name);
  }
}

// Regression test taken from a lost rated game.
//
// Game 92of99z7 against TA Baseline S went 1. Nc3 Nc6 2. Nf3 e5 3. e4 d5
// 4. exd5 Qxd5?? and the knight on c3 -- which we had never seen and could not
// see, since no move of ours reaches c3 -- took the queen. Material went from
// level to minus nine at move four and the game was effectively over.
//
// Taking a pawn with the queen is attractive to a search that does not happen to
// have a knight on c3 in the hypothesis it is looking at. What must stop it is
// the risk term, which asks the whole population rather than a handful of
// sampled hypotheses: some of them do place a knight on c3, because that is one
// of the moves White could have made from a square we cannot observe.
void DoesNotRepeatTheQueenBlunderFromGame92of99z7() {
  // Several seeds, because the belief is sampled: a single seed once passed a
  // fix that was a coin flip.
  //
  // History of this test's contract. It first asserted that no seed plays the
  // grab. That passed on a particle filter whose resampling was degenerate
  // (every particle took the same hidden move, so the population was one
  // trajectory), and the pass depended on which trajectory the seed drew.
  // With the resampling repaired the posterior is real: the hidden knight
  // stands on c3 in 5-22% of hypotheses and d5 is guarded in 17-46%. At 512
  // particles with a 0.5 s clock the engine still took the pawn in two of
  // eight seeds; at 1,024 particles with a 400k-node budget (upstream's
  // parameters, used here) it declines in eight of eight. The margin is thin
  // -- a ~20% chance of losing the queen priced against a pawn and a
  // centralised queen -- and that is the open strategic problem recorded in
  // HANDOFF.md. This test pins the measured contract: the posterior is not
  // degenerate, the risk term fires, and every seed declines.
  int declined = 0;
  int risk_seen = 0;
  int informative_posteriors = 0;
  const uint64_t seeds[] = {2026ULL, 1ULL, 2ULL, 3ULL, 4ULL, 5ULL, 6ULL, 7ULL};
  for (const uint64_t seed : seeds) {
    // Node-limited, as upstream made it, so the verdict does not depend on
    // machine load or on which standard library's random sequence is drawn.
    EngineOptions options;
    options.particle_count = 1024;
    options.transposition_megabytes = 16;
    options.time_reserve = 0.0;
    options.node_budget = 400000;

    Position truth;
    FOW_EXPECT_TRUE(PositionFromFen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth));
    Engine engine(kBlack, 180.0, 2.0, options, seed);

    // The game as played, up to the move before the blunder.
    const char* line[] = {"b1c3", "b8c6", "g1f3", "e7e5",
                          "e2e4", "d7d5", "e4d5"};
    bool we_just_moved = false;
    for (const char* uci : line) {
      const Observation view(RenderObservation(truth, kBlack));
      engine.Observe(view, we_just_moved);
      we_just_moved = false;

      MoveList legal;
      truth.GenerateMoves(&legal);
      Move move = kNullMove;
      for (const Move candidate : legal) {
        if (MoveToUci(candidate) == uci) move = candidate;
      }
      FOW_EXPECT_TRUE(move != kNullMove);
      if (move == kNullMove) return;
      if (truth.side_to_move() == kBlack) {
        engine.NotifyMovePlayed(move);
        we_just_moved = true;
      }
      UndoState undo;
      truth.MakeMove(move, &undo);
    }

    // Black to move, with a free pawn on d5 guarded by an unseen knight.
    const Observation view(RenderObservation(truth, kBlack));
    engine.Observe(view, we_just_moved);
    FOW_EXPECT_TRUE(view.IsUnseen(MakeSquare(2, 2)));  // c3 really is in fog
    int guarded = 0;
    for (const Position& particle : engine.belief().particles()) {
      if (particle.IsAttacked(MakeSquare(3, 4), kWhite)) ++guarded;
    }
    const double guarded_share =
        static_cast<double>(guarded) / engine.belief().particle_count();
    if (guarded_share > 0.05) ++informative_posteriors;

    DecisionTrace trace;
    const Move choice = engine.ChooseMove(view, 170.0, &trace);
    FOW_EXPECT_TRUE(choice != kNullMove);
    std::fprintf(stderr, "       seed %llu chose %s (d5 guarded in %.0f%%, risk seen %d cp)\n",
                 static_cast<unsigned long long>(seed),
                 MoveToUci(choice).c_str(), guarded_share * 100.0,
                 trace.worst_risk);
    if (MoveToUci(choice) != "d8d5") ++declined;
    if (trace.worst_risk > 0) ++risk_seen;
  }
  // The posterior must carry the danger in every seed, the risk term must see
  // it, and the grab must be declined in every seed.
  FOW_EXPECT_EQ(informative_posteriors, 8);
  FOW_EXPECT_EQ(risk_seen, 8);
  FOW_EXPECT_EQ(declined, 8);
}

// Regression test from the nine-move loss to Greek Gift, game qp6mfacx.
//
// 1. d4 d5 2. Bf4 Nh6 3. c4 dxc4 4. Nf3 g6 5. Nc3 a6 6. e4 f5 7. Ne5 fxe4
// 8. Bxc4 Nf5 9. Bf7 Kxf7?? and the knight on e5 -- never seen, and unseeable,
// since no move of ours reaches e5 -- took the king. No material had been lost;
// the game was thrown away by one king move onto a defended square.
//
// The information was not missing from the belief: 8.2% of hypotheses said the
// square was covered. It was lost to sampling, because none of the eight columns
// of the matrix game happened to contain an attacker, which reported the risk as
// exactly zero. King safety is therefore decided over the whole population.
void DoesNotTakeTheGreekGiftFromGameQp6mfacx() {
  EngineOptions options;
  options.particle_count = 2048;
  options.transposition_megabytes = 32;
  options.time_reserve = 0.0;
  options.time_cap = 0.4;

  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen(
      "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth));
  Engine engine(kBlack, 180.0, 2.0, options, 4242);

  const char* line[] = {"d2d4", "d7d5", "c1f4", "g8h6", "c2c4", "d5c4",
                        "g1f3", "g7g6", "b1c3", "a7a6", "e2e4", "f7f5",
                        "f3e5", "f5e4", "f1c4", "h6f5", "c4f7"};
  bool we_just_moved = false;
  for (const char* uci : line) {
    const Observation view(RenderObservation(truth, kBlack));
    engine.Observe(view, we_just_moved);
    we_just_moved = false;
    MoveList legal;
    truth.GenerateMoves(&legal);
    Move move = kNullMove;
    for (const Move candidate : legal) {
      if (MoveToUci(candidate) == uci) move = candidate;
    }
    FOW_EXPECT_TRUE(move != kNullMove);
    if (move == kNullMove) return;
    if (truth.side_to_move() == kBlack) {
      engine.NotifyMovePlayed(move);
      we_just_moved = true;
    }
    UndoState undo;
    truth.MakeMove(move, &undo);
  }

  const Observation view(RenderObservation(truth, kBlack));
  engine.Observe(view, we_just_moved);
  // The bishop is sitting on f7 in plain sight; its defender is not.
  FOW_EXPECT_TRUE(!view.IsUnseen(MakeSquare(5, 6)));
  FOW_EXPECT_TRUE(view.IsUnseen(MakeSquare(4, 4)));

  DecisionTrace trace;
  const Move choice = engine.ChooseMove(view, 170.0, &trace);
  FOW_EXPECT_TRUE(choice != kNullMove);
  std::fprintf(stderr,
               "       chose %s (rejected %d unsafe, king risk %d permille)\n",
               MoveToUci(choice).c_str(), trace.rejected_unsafe,
               trace.king_risk_permille);
  // The move that lost the game.
  FOW_EXPECT_TRUE(MoveToUci(choice) != "e8f7");
  // And the filter must have actually thrown something away.
  FOW_EXPECT_TRUE(trace.rejected_unsafe > 0);
}

// Regression test from the second loss to the same opponent, game z6mbi981,
// playing White this time.
//
// 31...Qe1 placed the queen beside the king on d1; 32.Kxe1?? took it and the rook
// on e8 -- unseen in all 63 observations -- took the king down the e-file. The
// trick is the same as game qp6mfacx with the geometry changed: bait adjacent to
// the king, guarded from a distance. Material was near level, so the game was
// thrown away by this one capture.
//
// Note what the queen's own route proves: it travelled e7-e6-e1, so the e-file
// was clear, which is exactly what makes a rook behind it the natural hypothesis.
void DoesNotTakeTheBaitFromGameZ6mbi981() {
  EngineOptions options;
  options.particle_count = 2048;
  options.transposition_megabytes = 32;
  options.time_reserve = 0.0;
  options.time_cap = 0.4;

  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen(
      "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth));
  Engine engine(kWhite, 180.0, 2.0, options, 99);

  const char* line[] = {
      "e2e4", "c7c5", "d2d3", "b8c6", "c1e3", "e7e6", "b1d2", "g8f6", "a2a4",
      "f8e7", "g1e2", "d7d5", "e4d5", "e6d5", "h2h4", "d5d4", "e3f4", "e8g8",
      "h4h5", "f8e8", "d1b1", "e7d6", "f4d6", "d8d6", "a1a3", "h7h6", "a3a1",
      "c8e6", "b1c1", "e6d5", "e1d1", "a7a6", "a1a3", "d6c7", "d2b3", "b7b6",
      "a3a1", "d5b3", "c2b3", "a8d8", "a1a3", "c7d7", "h1h3", "c6b4", "a3a2",
      "b4a2", "c1c4", "a2b4", "c4c1", "g8h8", "h3g3", "b4d5", "c1c4", "d7c7",
      "c4a6", "h8g8", "g3f3", "c7e7", "a6c4", "e7e6", "e2c1", "e6e1"};

  bool we_just_moved = false;
  for (const char* uci : line) {
    const Observation view(RenderObservation(truth, kWhite));
    engine.Observe(view, we_just_moved);
    we_just_moved = false;
    MoveList legal;
    truth.GenerateMoves(&legal);
    Move move = kNullMove;
    for (const Move candidate : legal) {
      if (MoveToUci(candidate) == uci) move = candidate;
    }
    FOW_EXPECT_TRUE(move != kNullMove);
    if (move == kNullMove) return;
    if (truth.side_to_move() == kWhite) {
      engine.NotifyMovePlayed(move);
      we_just_moved = true;
    }
    UndoState undo;
    truth.MakeMove(move, &undo);
  }

  const Observation view(RenderObservation(truth, kWhite));
  engine.Observe(view, we_just_moved);
  FOW_EXPECT_TRUE(!view.IsUnseen(MakeSquare(4, 0)));  // the queen on e1 is seen
  FOW_EXPECT_TRUE(view.IsUnseen(MakeSquare(4, 7)));   // the rook on e8 is not

  DecisionTrace trace;
  const Move choice = engine.ChooseMove(view, 150.0, &trace);
  std::fprintf(stderr, "       chose %s (rejected %d of %d, risk %d permille)\n",
               MoveToUci(choice).c_str(), trace.rejected_unsafe,
               trace.legal_moves, trace.king_risk_permille);
  FOW_EXPECT_TRUE(MoveToUci(choice) != "d1e1");
}

// Regression for en passant lost in the engine integration. The helper passed
// every conformance check while its caller compared an observation with itself,
// so the capture was never generated. Here the opponent double-pushes beside
// our pawn and the engine's legal move count must match the referee's.
void InfersEnPassantAcrossTheOpponentsMove() {
  Position truth;
  PositionFromFen("4k3/3p4/8/4P3/8/8/8/4K3 w - - 0 1", &truth);
  EngineOptions options = FastOptions();
  Engine engine(kWhite, 10.0, 0.05, options, 7);

  engine.Observe(Observation(RenderObservation(truth, kWhite)), false);
  UndoState undo;
  truth.MakeMove(EncodeMove(MakeSquare(4, 0), MakeSquare(4, 1)), &undo);  // Ke2
  engine.NotifyMovePlayed(EncodeMove(MakeSquare(4, 0), MakeSquare(4, 1)));
  engine.Observe(Observation(RenderObservation(truth, kWhite)), true);
  truth.MakeMove(EncodeMove(MakeSquare(3, 6), MakeSquare(3, 4), kFlagDoublePush),
                 &undo);  // ...d5, capturable en passant on d6
  const Observation view(RenderObservation(truth, kWhite));
  engine.Observe(view, false);

  MoveList expected;
  truth.GenerateMoves(&expected);
  bool has_capture = false;
  for (const Move move : expected) {
    if (MoveToUci(move) == "e5d6") has_capture = true;
  }
  FOW_EXPECT_TRUE(has_capture);

  DecisionTrace trace;
  const Move chosen = engine.ChooseMove(view, 10.0, &trace);
  FOW_EXPECT_TRUE(chosen != kNullMove);
  FOW_EXPECT_EQ(trace.legal_moves, expected.size());
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::EnvironmentOverridesAreApplied);
  FOW_RUN_TEST(fow::TimeBudgetIsAlwaysAffordable);
  FOW_RUN_TEST(fow::ReturnsTheOnlyMoveWhenForced);
  FOW_RUN_TEST(fow::WorksWithTheMatrixGameDisabled);
  FOW_RUN_TEST(fow::DoesNotRepeatTheQueenBlunderFromGame92of99z7);
  FOW_RUN_TEST(fow::DoesNotTakeTheGreekGiftFromGameQp6mfacx);
  FOW_RUN_TEST(fow::DoesNotTakeTheBaitFromGameZ6mbi981);
  FOW_RUN_TEST(fow::EveryMoveTheEngineReturnsIsLegal);
  FOW_RUN_TEST(fow::InfersEnPassantAcrossTheOpponentsMove);
  return fow::testing::Summarize("engine_test");
}
