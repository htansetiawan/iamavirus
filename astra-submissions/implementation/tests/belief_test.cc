// Copyright 2026. Fog of War chess engine.
//
// Tests for the belief particle filter.
//
// The property that matters is that the truth is never contradicted. A filter
// that discards the real position is worse than useless: it will confidently
// search a board that cannot exist. These tests play out real games, hide the
// opponent exactly as the arena does, and assert the invariants at every ply.

#include "../belief.h"

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <random>
#include <sstream>
#include <string>
#include <vector>

#include "../bitboard.h"
#include "../observation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
// Seed a tiny explicit support in unit tests. This hook has no live input path.
struct BeliefStateTestAccess {
  static void Assign(BeliefState* belief, const std::vector<Position>& support) {
    belief->particles_ = support;
    belief->representative_valid_ = false;
  }
  static void ClearPopulation(BeliefState* belief) { belief->particles_.clear(); }
  static void SeedLocalHistory(BeliefState* belief, const Position& position) {
    belief->particles_.assign(belief->target_count_, position);
    belief->seen_any_ = true;
    belief->previous_mover_ = position.side_to_move() ^ 1;
    belief->history_full_certified_ = false;  // synthetic root, not an opening trajectory
    belief->previous_view_ = Observation(RenderObservation(position, belief->our_side_));
    belief->history_.clear();
    belief->RememberHistory(belief->previous_view_);
  }
};
namespace {

constexpr char kStartFen[] =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

Position StartPosition() {
  Position position;
  FOW_EXPECT_TRUE(PositionFromFen(kStartFen, &position));
  return position;
}

// True when `candidate` places the pieces of `color` exactly as `truth` does.
bool SamePlacement(const Position& candidate, const Position& truth, int color) {
  for (int type = 0; type < kNumPieceTypes; ++type) {
    if (candidate.pieces(type, color) != truth.pieces(type, color)) return false;
  }
  return true;
}

bool BeliefContainsTruth(const BeliefState& belief, const Position& truth) {
  const int enemy = belief.our_side() ^ 1;
  for (const Position& particle : belief.particles()) {
    if (SamePlacement(particle, truth, enemy)) return true;
  }
  return false;
}

// Every hypothesis must agree with the observation on every visible square.
bool AllParticlesAgree(const BeliefState& belief, const Observation& view) {
  for (const Position& particle : belief.particles()) {
    for (int square = 0; square < kNumSquares; ++square) {
      const char symbol = view.at(square);
      if (symbol == kUnseen) continue;
      const int piece = particle.piece_at(square);
      if (symbol == kEmpty) {
        if (piece != kNoPiece) return false;
        continue;
      }
      if (piece == kNoPiece) return false;
      if (PieceTypeToSymbol(piece, particle.color_at(square)) != symbol) {
        return false;
      }
    }
  }
  return true;
}

// Plays a complete game with random legal moves, driving the belief exactly as
// the protocol would, and reports how the invariants held up.
struct GameAudit {
  int plies = 0;
  int truth_present = 0;
  int agreement_failures = 0;
  int deduction_failures = 0;
  int collapses = 0;
  // Total enemy piece count differing from reality. Strictly invariant: material
  // leaves the board only by a capture we can see.
  int total_count_failures = 0;
  // Per-type counts differing from reality. Not invariant, because a pawn
  // promoting behind the fog changes the opponent's composition without
  // changing how many pieces they have, and nothing we observe can tell us it
  // happened.
  int type_count_failures = 0;
  // How many enemy pieces the likeliest hypothesis places on exactly the right
  // square, against how many there are. This, not exact-state tracking, is what
  // a particle filter can be judged on here.
  int64_t correct_squares = 0;
  int64_t total_pieces = 0;
};

GameAudit AuditRandomGame(int our_side, int particle_count, uint64_t seed,
                          int max_plies, bool grouped = false) {
  std::mt19937_64 rng(seed);
  Position truth = StartPosition();
  // Exercise the combined opt-in deduction/capture variant here. The tactical
  // engine default keeps deductions off pending the separate action gate.
  BeliefState belief(our_side, particle_count, seed ^ 0x5DEECE66DULL,
                    true, true, true, grouped);
  GameAudit audit;
  bool we_just_moved = false;

  for (int ply = 0; ply < max_plies; ++ply) {
    // Both players receive an observation before every ply.
    const Observation view(RenderObservation(truth, our_side));
    const BeliefUpdateReport report = belief.Observe(view, we_just_moved);
    we_just_moved = false;
    if (report.collapsed) ++audit.collapses;
    ++audit.plies;
    if (BeliefContainsTruth(belief, truth)) ++audit.truth_present;
    if (!AllParticlesAgree(belief, view)) ++audit.agreement_failures;

    const int enemy = our_side ^ 1;
    const Deductions facts = DeduceFromObservation(view, our_side);
    int true_total = 0;
    for (int type = 0; type < kNumPieceTypes; ++type) {
      true_total += PopCount(truth.pieces(type, enemy));
    }
    for (const Position& particle : belief.particles()) {
      if ((particle.pieces_of(enemy) & facts.must_hold_enemy) != facts.must_hold_enemy ||
          (particle.occupied() & facts.must_be_empty)) ++audit.deduction_failures;
      int total = 0;
      bool type_mismatch = false;
      for (int type = 0; type < kNumPieceTypes; ++type) {
        const int count = PopCount(particle.pieces(type, enemy));
        total += count;
        if (count != PopCount(truth.pieces(type, enemy))) type_mismatch = true;
      }
      if (total != true_total) ++audit.total_count_failures;
      if (type_mismatch) ++audit.type_count_failures;
    }

    {
      const Position& likely = belief.Representative();
      for (int type = 0; type < kNumPieceTypes; ++type) {
        audit.correct_squares +=
            PopCount(likely.pieces(type, enemy) & truth.pieces(type, enemy));
        audit.total_pieces += PopCount(truth.pieces(type, enemy));
      }
    }

    MoveList moves;
    truth.GenerateMoves(&moves);
    if (moves.empty()) break;
    std::uniform_int_distribution<int> pick(0, moves.size() - 1);
    const Move move = moves[pick(rng)];
    if (truth.side_to_move() == our_side) {
      belief.ApplyOurMove(move);
      we_just_moved = true;
    }
    UndoState undo;
    truth.MakeMove(move, &undo);
    // A captured king ends the game.
    if (truth.KingSquare(kWhite) < 0 || truth.KingSquare(kBlack) < 0) break;
  }
  return audit;
}

void BeliefStartsCertain() {
  BeliefState belief(kWhite, 32, 1);
  const Position truth = StartPosition();
  const Observation view(RenderObservation(truth, kWhite));
  belief.Observe(view, false);
  FOW_EXPECT_EQ(belief.particle_count(), 32);
  FOW_EXPECT_TRUE(BeliefContainsTruth(belief, truth));
  // The opening is common knowledge, so every hypothesis is the same one.
  for (const Position& particle : belief.particles()) {
    FOW_EXPECT_TRUE(SamePlacement(particle, truth, kBlack));
  }
}

// The properties a particle filter can actually be held to, checked over whole
// games from both sides.
//
// Exact state tracking is deliberately not one of them. The diagnostic behind
// this test showed that roughly twenty of the opponent's thirty moves are
// typically invisible to us, so the set of positions consistent with everything
// we have seen grows by about that factor every ply. No finite population can
// contain one specific trajectory for long, and demanding it would be demanding
// something information theory forbids. What the filter must do is never
// contradict an observation, never invent or lose material, and keep most enemy
// pieces on their true squares -- which it can, because most pieces never move.
void BeliefMaintainsItsInvariants() {
  int total_plies = 0;
  int total_truth = 0;
  int agreement_failures = 0;
  int deduction_failures = 0;
  int total_count_failures = 0;
  int type_count_failures = 0;
  int collapses = 0;
  int64_t correct_squares = 0;
  int64_t total_pieces = 0;
  for (int game = 0; game < 12; ++game) {
    for (const int side : {kWhite, kBlack}) {
      const GameAudit audit =
          AuditRandomGame(side, 2048, 1000 + game * 7 + side, 70);
      total_plies += audit.plies;
      total_truth += audit.truth_present;
      agreement_failures += audit.agreement_failures;
      deduction_failures += audit.deduction_failures;
      total_count_failures += audit.total_count_failures;
      type_count_failures += audit.type_count_failures;
      collapses += audit.collapses;
      correct_squares += audit.correct_squares;
      total_pieces += audit.total_pieces;
    }
  }
  FOW_EXPECT_TRUE(total_plies > 200);
  // Hard invariants.
  FOW_EXPECT_EQ(agreement_failures, 0);
  FOW_EXPECT_EQ(deduction_failures, 0);
  FOW_EXPECT_EQ(total_count_failures, 0);
  const double placement =
      total_pieces > 0
          ? static_cast<double>(correct_squares) / static_cast<double>(total_pieces)
          : 0.0;
  std::fprintf(stderr,
               "       %d plies, truth in population %d, collapses %d, "
               "pieces correctly placed %.1f%%, composition unknown in %d\n",
               total_plies, total_truth, collapses, placement * 100.0,
               type_count_failures);
  // Most of the opponent's army should be exactly located.
  FOW_EXPECT_TRUE(placement > 0.70);
  // Rebuilding should be a rare fallback, not routine.
  FOW_EXPECT_TRUE(collapses * 20 < total_plies);
}

// When one of our pieces is taken, the hypotheses must conclude that an enemy
// piece now stands there. Nothing in the code says so; it falls out of keeping
// only the hypotheses that could have produced the observation.
void CaptureImpliesAnEnemyPieceOnThatSquare() {
  // Our bishop on c8's square becomes unseen as a white rook takes it.
  // Set up: we are Black; a rook is lurking on b8 behind the fog.
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("1R1bk3/3p4/8/8/8/8/8/4K3 w - - 0 1", &truth));
  BeliefState belief(kBlack, 128, 7);

  // Seed the belief with the truth by observing it once from a position where
  // the rook is visible, then let it be captured.
  const Observation first(RenderObservation(truth, kBlack));
  belief.Observe(first, false);

  // White plays Rb8xd8, taking our bishop.
  const Move capture = EncodeMove(MakeSquare(1, 7), MakeSquare(3, 7));
  UndoState undo;
  truth.MakeMove(capture, &undo);
  const Observation after(RenderObservation(truth, kBlack));
  belief.Observe(after, false);

  FOW_EXPECT_TRUE(belief.particle_count() > 0);
  // Every surviving hypothesis must put a white piece on d8.
  for (const Position& particle : belief.particles()) {
    FOW_EXPECT_EQ(particle.piece_at(MakeSquare(3, 7)), kRook);
    FOW_EXPECT_EQ(particle.color_at(MakeSquare(3, 7)), kWhite);
  }
}

// The case that lost three rated games.
//
// When one of our pieces is captured on a square we cannot afterwards see, the
// observation still proves the capture happened: our own pieces are always
// visible, so a square that has gone unseen cannot be holding one. A
// consistency check that only compares visible squares misses this entirely --
// it lets hypotheses keep a phantom friendly piece on the square, and so never
// concludes that an enemy piece is standing there. In all three losses the piece
// that took our king was the piece that had just captured something of ours on
// exactly that square.
void CaptureOnASquareThatGoesUnseenIsStillInferred() {
  // We are Black: a rook on g8 and a king far away on c8, so once the rook is
  // gone nothing of ours can reach g8 and the square falls into fog.
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("2k3r1/8/8/8/8/8/8/4K1R1 w - - 0 1", &truth));
  BeliefState belief(kBlack, 256, 31);
  belief.Observe(Observation(RenderObservation(truth, kBlack)), false);

  // White's rook takes ours on g8.
  const Move capture = EncodeMove(MakeSquare(6, 0), MakeSquare(6, 7));
  UndoState undo;
  truth.MakeMove(capture, &undo);
  const Observation after(RenderObservation(truth, kBlack));

  // Precondition for the test to be meaningful: g8 really is unseen now.
  FOW_EXPECT_TRUE(after.IsUnseen(MakeSquare(6, 7)));

  belief.Observe(after, false);
  FOW_EXPECT_TRUE(belief.particle_count() > 0);

  // No hypothesis may still believe we own a rook on g8, and every one of them
  // must place a white piece there.
  int phantom_friend = 0;
  int found_enemy = 0;
  for (const Position& particle : belief.particles()) {
    if (particle.piece_at(MakeSquare(6, 7)) == kRook &&
        particle.color_at(MakeSquare(6, 7)) == kBlack) {
      ++phantom_friend;
    }
    if (particle.color_at(MakeSquare(6, 7)) == kWhite) ++found_enemy;
  }
  FOW_EXPECT_EQ(phantom_friend, 0);
  FOW_EXPECT_EQ(found_enemy, belief.particle_count());
}

// Public bluqrpex, through 29...Bxf1. Unlike the smaller capture tests, this
// reaches recovery with a just-captured own piece now behind the fog. The live
// tracker receives observations and our moves only, not Black's recorded moves.
void RecoveryRetainsTheKnownCaptureSquare() {
  const char* line =
      "b1c3 d7d5 d2d4 g8f6 d1d2 c7c5 d4c5 e7e6 c3d5 d8d5 "
      "d2d5 e6d5 e2e3 a7a5 g1h3 f8e7 f1d3 b8c6 e1g1 a5a4 "
      "f1d1 e8g8 d3f1 f8d8 h3f4 c8f5 f4d5 d8d5 d1d5 f6d5 "
      "a2a3 d5f6 c2c4 f5e6 f2f3 a8d8 g1h1 d8d7 c1d2 d7d2 "
      "e3e4 d2d4 b2b4 a4b3 a1b1 b3b2 h2h3 d4d2 g2g4 e7c5 "
      "f1d3 d2d3 b1f1 e6c4 h3h4 d3b3 g4g5 c4f1";
  for (const uint64_t seed : {1ULL, 2ULL, 3ULL, 777ULL}) {
    Position truth = StartPosition();
    BeliefState belief(kWhite, 2048, seed ^ 0x9E3779B97F4A7C15ULL);
    belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
    std::istringstream stream(line);
    std::string uci;
    while (stream >> uci) {
      MoveList legal;
      truth.GenerateMoves(&legal);
      Move move = kNullMove;
      for (Move candidate : legal) if (MoveToUci(candidate) == uci) move = candidate;
      FOW_EXPECT_TRUE(move != kNullMove);
      if (move == kNullMove) return;
      const bool ours = truth.side_to_move() == kWhite;
      if (ours) belief.ApplyOurMove(move);
      UndoState undo;
      truth.MakeMove(move, &undo);
      belief.Observe(Observation(RenderObservation(truth, kWhite)), ours);
    }
    const int f1 = MakeSquare(5, 0);
    FOW_EXPECT_TRUE(Observation(RenderObservation(truth, kWhite)).IsUnseen(f1));
    int occupied_by_enemy = 0;
    for (const Position& particle : belief.particles()) {
      occupied_by_enemy += particle.color_at(f1) == kBlack;
    }
    // The type is unknown. Occupancy follows from the disappeared own rook.
    FOW_EXPECT_EQ(occupied_by_enemy, belief.particle_count());
  }
}

BeliefUpdateReport PlayObservedMove(Position* truth, BeliefState* belief,
                                    const std::string& uci) {
  MoveList legal;
  truth->GenerateMoves(&legal);
  Move move = kNullMove;
  for (Move candidate : legal) if (MoveToUci(candidate) == uci) move = candidate;
  FOW_EXPECT_TRUE(move != kNullMove);
  if (move == kNullMove) return {};
  const bool ours = truth->side_to_move() == belief->our_side();
  if (ours) belief->ApplyOurMove(move);
  UndoState undo;
  truth->MakeMove(move, &undo);
  const Observation view(RenderObservation(*truth, belief->our_side()));
  const auto report = belief->Observe(view, ours);
  FOW_EXPECT_TRUE(AllParticlesAgree(*belief, view));
  return report;
}

void EnPassantDoesNotInventACapturerOnTheVictimSquare() {
  const std::pair<int, const char*> cases[] = {
      {kBlack, "e2e4 a7a6 e4e5 d7d5 e5d6"},
      {kWhite, "a2a3 d7d5 a3a4 d5d4 e2e4 d4e3"},
  };
  for (const auto& [side, moves] : cases) {
    Position truth = StartPosition();
    BeliefState belief(side, 128, 19);
    belief.Observe(Observation(RenderObservation(truth, side)), false);
    std::istringstream stream(moves);
    std::string uci;
    BeliefUpdateReport report;
    while (stream >> uci) report = PlayObservedMove(&truth, &belief, uci);
    FOW_EXPECT_TRUE(report.capture_en_passant_ambiguous);
    FOW_EXPECT_EQ(report.capture_square, -1);
    FOW_EXPECT_TRUE(!report.capture_evidence_conflict);
  }
}

void VisibleOrdinaryCaptureOfADoublePushedPawnIsRecognized() {
  Position truth = StartPosition();
  BeliefState belief(kBlack, 128, 31);
  belief.Observe(Observation(RenderObservation(truth, kBlack)), false);
  PlayObservedMove(&truth, &belief, "e2e4");
  PlayObservedMove(&truth, &belief, "d7d5");
  const auto report = PlayObservedMove(&truth, &belief, "e4d5");
  FOW_EXPECT_EQ(report.capture_square, MakeSquare(3, 4));
  FOW_EXPECT_TRUE(!report.capture_en_passant_ambiguous);
}

void CaptureEvidenceSurvivesOurMoveButExpiresOnTheirNextMove() {
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("2k3r1/8/8/8/8/8/8/4K1R1 w - - 0 1", &truth));
  BeliefState belief(kBlack, 256, 31);
  belief.Observe(Observation(RenderObservation(truth, kBlack)), false);
  auto report = PlayObservedMove(&truth, &belief, "g1g8");
  FOW_EXPECT_EQ(report.capture_square, MakeSquare(6, 7));
  report = PlayObservedMove(&truth, &belief, "c8c7");
  FOW_EXPECT_EQ(report.capture_square, MakeSquare(6, 7));
  report = PlayObservedMove(&truth, &belief, "g8g7");
  FOW_EXPECT_EQ(report.capture_square, -1);
  FOW_EXPECT_TRUE(!report.capture_evidence_conflict);
}

void OurCaptureClearsTheEvidenceConstraint() {
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("1R1bk3/3p4/8/8/8/8/8/4K3 w - - 0 1", &truth));
  BeliefState belief(kBlack, 128, 7);
  belief.Observe(Observation(RenderObservation(truth, kBlack)), false);
  auto report = PlayObservedMove(&truth, &belief, "b8d8");
  FOW_EXPECT_EQ(report.capture_square, MakeSquare(3, 7));
  report = PlayObservedMove(&truth, &belief, "e8d8");
  FOW_EXPECT_EQ(report.capture_square, -1);
  FOW_EXPECT_TRUE(!report.capture_evidence_conflict);
}

void GroupedPredictionEnumeratesTheExactOpeningSupportOnce() {
  Position truth = StartPosition();
  // A uniform opponent prior gives a closed-form posterior for this update.
  BeliefState belief(kWhite, 2048, 813, false, true, true, true);
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
  PlayObservedMove(&truth, &belief, "e2e3");
  const Position before = truth;
  const auto report = PlayObservedMove(&truth, &belief, "g8f6");
  const std::string observed = RenderObservation(truth, kWhite);
  MoveList moves;
  before.GenerateMoves(&moves);
  std::vector<Position> exact;
  for (Move move : moves) {
    Position after = before;
    UndoState undo;
    after.MakeMove(move, &undo);
    if (RenderObservation(after, kWhite) == observed) exact.push_back(after);
  }
  FOW_EXPECT_EQ(report.expanded_predecessors, 1);
  FOW_EXPECT_EQ(report.enumerated_transitions, moves.size());
  FOW_EXPECT_TRUE(!report.successor_prefix_capped);
  FOW_EXPECT_EQ(belief.particle_count(), 2048);
  FOW_EXPECT_TRUE(exact.size() > 5);
  int total = 0;
  for (const Position& expected : exact) {
    int count = 0;
    for (const Position& particle : belief.particles()) {
      count += SamePlacement(particle, expected, kBlack);
    }
    const int floor = 2048 / static_cast<int>(exact.size());
    FOW_EXPECT_TRUE(count == floor || count == floor + 1);
    total += count;
  }
  FOW_EXPECT_EQ(total, 2048);
}

void GroupedPredictionPreservesBeliefInvariantsAcrossGames() {
  int plies = 0, retained = 0, collapses = 0;
  for (int game = 0; game < 12; ++game) {
    for (const int side : {kWhite, kBlack}) {
      const auto audit = AuditRandomGame(side, 2048, 1000 + game * 7 + side, 70, true);
      FOW_EXPECT_EQ(audit.agreement_failures, 0);
      FOW_EXPECT_EQ(audit.deduction_failures, 0);
      FOW_EXPECT_EQ(audit.total_count_failures, 0);
      plies += audit.plies;
      retained += audit.truth_present;
      collapses += audit.collapses;
    }
  }
  std::fprintf(stderr, "       grouped: %d plies, truth in population %d, collapses %d\n",
               plies, retained, collapses);
}

Position SwapSides(const Position& original) {
  Position flipped;
  for (int square = 0; square < kNumSquares; ++square) {
    if (original.piece_at(square) != kNoPiece) {
      flipped.PutPiece(square ^ 56, original.color_at(square) ^ 1, original.piece_at(square));
    }
  }
  flipped.set_side_to_move(original.side_to_move() ^ 1);
  return flipped;
}

void ContinuedPlayProvesOurLastMoveDidNotLose() {
  Position safe, attacked;
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/n7/8/8/7P/1K6 w - - 0 1", &safe));
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/8/8/n7/7P/1K6 w - - 0 1", &attacked));
  for (int side : {kWhite, kBlack}) {
    const Position before = side == kWhite ? safe : SwapSides(safe);
    const Position false_world = side == kWhite ? attacked : SwapSides(attacked);
    const int from = MakeSquare(7, side == kWhite ? 1 : 6);
    const int to = MakeSquare(7, side == kWhite ? 2 : 5);
    const Move quiet = EncodeMove(from, to);
    const Observation initial(RenderObservation(before, side));
    FOW_EXPECT_TRUE(RenderObservation(false_world, side) == initial.squares());
    for (bool enabled : {false, true}) {
      BeliefState belief(side, 32, 99, false, false, false, false, enabled);
      belief.Observe(initial, false);
      BeliefStateTestAccess::Assign(&belief, {before, false_world});
      belief.ApplyOurMove(quiet);
      Position after = before;
      UndoState undo;
      after.MakeMove(quiet, &undo);
      const auto report = belief.Observe(Observation(RenderObservation(after, side)), true);
      int unsafe = 0;
      for (const Position& p : belief.particles()) unsafe += p.IsAttacked(p.KingSquare(side), side ^ 1);
      FOW_EXPECT_EQ(unsafe, enabled ? 0 : 16);
      FOW_EXPECT_EQ(report.continuation_previous_mover, side);
      FOW_EXPECT_EQ(report.continuation_rejected, enabled ? 1 : 0);
      FOW_EXPECT_TRUE(!report.collapsed);
    }
  }
}

void ContinuationAllowsAnInvisibleCheckByEitherMover() {
  Position before;
  FOW_EXPECT_TRUE(PositionFromFen("2k5/8/8/8/8/8/1R6/4K3 w - - 0 1", &before));
  for (int side : {kWhite, kBlack}) {
    Position truth = side == kWhite ? before : SwapSides(before);
    BeliefState belief(side, 32, 16, false, false, false, false, true);
    belief.Observe(Observation(RenderObservation(truth, side)), false);
    BeliefStateTestAccess::Assign(&belief, {truth});
    const int rank = side == kWhite ? 1 : 6;
    const Move checking = EncodeMove(MakeSquare(1, rank), MakeSquare(2, rank));
    belief.ApplyOurMove(checking);
    UndoState undo;
    truth.MakeMove(checking, &undo);
    FOW_EXPECT_TRUE(truth.IsAttacked(truth.KingSquare(side ^ 1), side));
    FOW_EXPECT_TRUE(Observation(RenderObservation(truth, side ^ 1)).IsUnseen(MoveTo(checking)));
    const auto report = belief.Observe(Observation(RenderObservation(truth, side)), true);
    FOW_EXPECT_TRUE(!report.collapsed);
    FOW_EXPECT_EQ(report.continuation_rejected, 0);
  }
  // After the enemy moved, our own king may now be under a hidden check.
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/1r6/8/8/7P/1K6 b - - 0 1", &before));
  for (bool grouped : {false, true}) {
    BeliefState belief(kWhite, 2048, 84, false, false, true, grouped, true);
    belief.Observe(Observation(RenderObservation(before, kWhite)), false);
    BeliefStateTestAccess::Assign(&belief, {before});
    Position after = before;
    UndoState undo;
    after.MakeMove(EncodeMove(MakeSquare(1, 4), MakeSquare(1, 2)), &undo);
    const auto report = belief.Observe(Observation(RenderObservation(after, kWhite)), false);
    FOW_EXPECT_TRUE(!report.collapsed);
    FOW_EXPECT_TRUE(BeliefContainsTruth(belief, after));
    FOW_EXPECT_EQ(report.continuation_previous_mover, kBlack);
  }
}

void RecoveryConditionsOnThePreviousMoversSurvival() {
  Position safe, attacked;
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/n7/8/8/7P/1K6 w - - 0 1", &safe));
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/8/8/n7/7P/1K6 w - - 0 1", &attacked));
  BeliefState belief(kWhite, 128, 27, false, false, true, false, true);
  belief.Observe(Observation(RenderObservation(safe, kWhite)), false);
  BeliefStateTestAccess::Assign(&belief, {attacked});
  const Move quiet = EncodeMove(MakeSquare(7, 1), MakeSquare(7, 2));
  belief.ApplyOurMove(quiet);
  UndoState undo;
  safe.MakeMove(quiet, &undo);
  const auto report = belief.Observe(Observation(RenderObservation(safe, kWhite)), true);
  FOW_EXPECT_TRUE(report.collapsed);
  FOW_EXPECT_TRUE(!report.continuation_evidence_conflict);
  FOW_EXPECT_TRUE(report.recovery_continuation_rejected > 0);
  FOW_EXPECT_TRUE(report.recovery_attempts <= 128 * 32);
  FOW_EXPECT_EQ(belief.particle_count(), 128);
  for (const Position& p : belief.particles()) {
    FOW_EXPECT_EQ(p.side_to_move(), kBlack);
    FOW_EXPECT_TRUE(!p.PreviousMoverIsLost());
  }
}

void ImpossibleContinuationIsBoundedAndReported() {
  Position terminal;
  FOW_EXPECT_TRUE(PositionFromFen("k7/8/8/8/8/8/7P/rK6 w - - 0 1", &terminal));
  BeliefState belief(kWhite, 8, 12, false, false, true, false, true);
  belief.Observe(Observation(RenderObservation(terminal, kWhite)), false);
  BeliefStateTestAccess::Assign(&belief, {terminal});
  const Move quiet = EncodeMove(MakeSquare(7, 1), MakeSquare(7, 2));
  belief.ApplyOurMove(quiet);
  UndoState undo;
  terminal.MakeMove(quiet, &undo);
  // The arena would not send this terminal frame. Deliberately malformed input
  // must expose a conflict rather than loop forever or claim a valid posterior.
  const auto report = belief.Observe(Observation(RenderObservation(terminal, kWhite)), true);
  FOW_EXPECT_TRUE(report.continuation_evidence_conflict);
  FOW_EXPECT_EQ(report.recovery_attempts, 8 * 32);
  FOW_EXPECT_EQ(belief.particle_count(), 8);
}

// A hypothesis contradicted by every observation must not survive; the filter
// must rebuild rather than crash or go empty.
void RecoversWhenEveryHypothesisIsContradicted() {
  BeliefState belief(kWhite, 64, 3);
  const Position truth = StartPosition();
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);

  // An observation that no successor of the opening can explain: a black queen
  // sitting on d4 with the whole board otherwise visible and empty.
  std::string impossible(kNumSquares, kEmpty);
  impossible[MakeSquare(3, 3)] = 'q';
  impossible[MakeSquare(4, 0)] = 'K';
  const BeliefUpdateReport report =
      belief.Observe(Observation(impossible), false);
  FOW_EXPECT_TRUE(report.collapsed);
  FOW_EXPECT_TRUE(belief.particle_count() > 0);
  FOW_EXPECT_TRUE(AllParticlesAgree(belief, Observation(impossible)));
}

// A king that has left its home square and come back has no castling right,
// and a population rebuilt after a collapse must not hand it one. This once
// produced an illegal e1g1 in a simulator game.
void RecoveryKeepsLostCastlingRightsLost() {
  BeliefState belief(kWhite, 64, 5);
  Position truth = StartPosition();
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
  // 1. e3 ... 2. Ke2 ... 3. Ke1: the king returns home with no rights left.
  const char* line[] = {"e2e3", "a7a6", "e1e2", "a6a5", "e2e1", "a5a4"};
  bool ours = true;
  for (const char* uci : line) {
    MoveList legal;
    truth.GenerateMoves(&legal);
    Move move = kNullMove;
    for (const Move candidate : legal) {
      if (MoveToUci(candidate) == uci) move = candidate;
    }
    FOW_EXPECT_TRUE(move != kNullMove);
    if (ours) belief.ApplyOurMove(move);
    UndoState undo;
    truth.MakeMove(move, &undo);
    belief.Observe(Observation(RenderObservation(truth, kWhite)), ours);
    ours = !ours;
  }
  FOW_EXPECT_EQ(belief.Representative().castling_rights() & 0xFFULL, Bitboard{0});
  // Now contradict every hypothesis so the population is rebuilt.
  std::string impossible = RenderObservation(truth, kWhite);
  impossible[MakeSquare(3, 3)] = 'q';
  const BeliefUpdateReport report = belief.Observe(Observation(impossible), false);
  FOW_EXPECT_TRUE(report.collapsed);
  for (const Position& particle : belief.particles()) {
    FOW_EXPECT_EQ(particle.castling_rights() & 0xFFULL, Bitboard{0});
  }
}

void RepresentativeIsOneOfTheParticles() {
  const Position truth = StartPosition();
  BeliefState belief(kWhite, 48, 11);
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
  const Position& chosen = belief.Representative();
  bool found = false;
  for (const Position& particle : belief.particles()) {
    if (&particle == &chosen) found = true;
  }
  FOW_EXPECT_TRUE(found);
}

void SampleReturnsDistinctHypothesesIncludingTheRepresentative() {
  const Position truth = StartPosition();
  BeliefState belief(kWhite, 64, 13);
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
  const std::vector<const Position*> chosen = belief.Sample(5);
  FOW_EXPECT_TRUE(!chosen.empty());
  FOW_EXPECT_TRUE(chosen.size() <= 5);
  FOW_EXPECT_EQ(chosen.front(), &belief.Representative());
  for (std::size_t i = 0; i < chosen.size(); ++i) {
    for (std::size_t j = i + 1; j < chosen.size(); ++j) {
      FOW_EXPECT_TRUE(chosen[i] != chosen[j]);
    }
  }
}

void FogContextReflectsTheRemainingEnemyArmy() {
  const Position truth = StartPosition();
  BeliefState belief(kWhite, 32, 17);
  const Observation view(RenderObservation(truth, kWhite));
  belief.Observe(view, false);
  const FogContext fog = belief.MakeFogContext(view);
  FOW_EXPECT_EQ(fog.side, kWhite);
  FOW_EXPECT_EQ(fog.pawns, 8);
  FOW_EXPECT_EQ(fog.knights, 2);
  FOW_EXPECT_EQ(fog.rook_like, 3);    // two rooks plus the queen
  FOW_EXPECT_EQ(fog.bishop_like, 3);  // two bishops plus the queen
  FOW_EXPECT_EQ(PopCount(fog.unseen), 32);
  // The enemy king is behind the fog at the start.
  FOW_EXPECT_TRUE(!belief.EnemyKingVisible(view));
}

Move HistoryMove(const Position& position, const char* uci) {
  MoveList moves;
  position.GenerateMoves(&moves);
  for (Move move : moves) if (MoveToUci(move) == uci) return move;
  FOW_EXPECT_TRUE(false);
  return kNullMove;
}

void HistoryRecoveryReplaysAnOpeningWithoutInventingPieces() {
  for (const int side : {kWhite, kBlack}) {
    BeliefState belief(side, 32, 902 + side, true, true, true, true, true, true);
    Position truth = StartPosition();
    belief.Observe(Observation(RenderObservation(truth, side)), false);
    for (const char* uci : {"e2e4", "e7e5", "g1f3", "b8c6"}) {
      const bool ours = truth.side_to_move() == side;
      const Move move = HistoryMove(truth, uci);
      if (ours) belief.ApplyOurMove(move);
      UndoState undo;
      truth.MakeMove(move, &undo);
      // Emulate particle extinction, not an impossible observation.
      BeliefStateTestAccess::ClearPopulation(&belief);
      const Observation view(RenderObservation(truth, side));
      const auto report = belief.Observe(view, ours);
      FOW_EXPECT_TRUE(report.collapsed);
      FOW_EXPECT_TRUE(report.history_recovered);
      FOW_EXPECT_TRUE(report.history_full_certified);
      FOW_EXPECT_EQ(report.recovery_attempts, 0);
      FOW_EXPECT_TRUE(report.history_transitions <= 1000000);
      for (const auto& p : belief.particles()) {
        FOW_EXPECT_EQ(RenderObservation(p, side), view.squares());
        FOW_EXPECT_TRUE(!p.PreviousMoverIsLost());
      }
    }
  }
}

void HistoryRecoveryPreservesAHiddenBishopAndAllowsItsMove() {
  Position truth;
  FOW_EXPECT_TRUE(PositionFromFen("8/7k/8/8/8/r1B5/8/7K b - - 0 1", &truth));
  BeliefState belief(kBlack, 32, 404, true, true, true, true, true, true);
  BeliefStateTestAccess::SeedLocalHistory(&belief, truth);
  FOW_EXPECT_EQ(RenderObservation(truth, kBlack)[18], 'B');
  for (const char* uci : {"a3a4", "c3b4"}) {
    const bool ours = truth.side_to_move() == kBlack;
    const Move move = HistoryMove(truth, uci);
    if (ours) belief.ApplyOurMove(move);
    UndoState undo;
    truth.MakeMove(move, &undo);
    BeliefStateTestAccess::ClearPopulation(&belief);
    const Observation view(RenderObservation(truth, kBlack));
    const auto report = belief.Observe(view, ours);
    FOW_EXPECT_TRUE(report.history_recovered);
    FOW_EXPECT_TRUE(!report.history_full_certified);
    const int bishop = ours ? 18 : 25;
    if (ours) FOW_EXPECT_TRUE(view.IsUnseen(18));
    for (const auto& p : belief.particles()) {
      FOW_EXPECT_EQ(p.piece_at(bishop), kBishop);
      FOW_EXPECT_EQ(p.color_at(bishop), kWhite);
      FOW_EXPECT_EQ(RenderObservation(p, kBlack), view.squares());
    }
  }
}

void HistoryRecoveryRetainsSpecialMoveMetadata() {
  struct Case { const char* fen; const char* uci; };
  for (const Case fixture : {
      Case{"4k3/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"},
      Case{"4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6"},
      Case{"4k3/P7/8/8/8/8/8/4K3 w - - 0 1", "a7a8n"},
      Case{"4k2r/8/8/8/8/8/8/4K3 b k - 0 1", "e8g8"},
      Case{"4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1", "e4d3"},
      Case{"4k3/8/8/8/8/8/p7/4K3 b - - 0 1", "a2a1n"}}) {
    Position truth;
    FOW_EXPECT_TRUE(PositionFromFen(fixture.fen, &truth));
    const int side = truth.side_to_move();
    BeliefState belief(side, 8, 994, true, true, true, true, true, true);
    BeliefStateTestAccess::SeedLocalHistory(&belief, truth);
    const Move move = HistoryMove(truth, fixture.uci);
    belief.ApplyOurMove(move);
    UndoState undo;
    truth.MakeMove(move, &undo);
    BeliefStateTestAccess::ClearPopulation(&belief);
    const Observation view(RenderObservation(truth, side));
    const auto report = belief.Observe(view, true);
    FOW_EXPECT_TRUE(report.history_recovered);
    FOW_EXPECT_TRUE(!report.history_full_certified);
    for (const auto& p : belief.particles()) {
      FOW_EXPECT_TRUE(SamePlacement(p, truth, kWhite));
      FOW_EXPECT_TRUE(SamePlacement(p, truth, kBlack));
      FOW_EXPECT_EQ(p.castling_rights(), truth.castling_rights());
      FOW_EXPECT_EQ(p.en_passant_square(), truth.en_passant_square());
      FOW_EXPECT_EQ(p.halfmove_clock(), truth.halfmove_clock());
    }
  }
}

void HistoryRecoveryRejectsAnImpossibleOwnTransition() {
  BeliefState belief(kWhite, 8, 400, true, true, true, true, true, true);
  Position truth = StartPosition();
  belief.Observe(Observation(RenderObservation(truth, kWhite)), false);
  // A successful own move cannot leave the opening board unchanged.
  belief.ApplyOurMove(HistoryMove(truth, "e2e4"));
  const auto report = belief.Observe(Observation(RenderObservation(truth, kWhite)), true);
  FOW_EXPECT_TRUE(report.history_attempted);
  FOW_EXPECT_TRUE(!report.history_recovered);
  FOW_EXPECT_TRUE(!report.history_full_certified);
  FOW_EXPECT_TRUE(report.recovery_attempts > 0);
  FOW_EXPECT_TRUE(report.history_transitions <= 1000000);
}

}  // namespace
}  // namespace fow

int main() {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  FOW_RUN_TEST(fow::BeliefStartsCertain);
  FOW_RUN_TEST(fow::RecoveryKeepsLostCastlingRightsLost);
  FOW_RUN_TEST(fow::RepresentativeIsOneOfTheParticles);
  FOW_RUN_TEST(fow::SampleReturnsDistinctHypothesesIncludingTheRepresentative);
  FOW_RUN_TEST(fow::FogContextReflectsTheRemainingEnemyArmy);
  FOW_RUN_TEST(fow::CaptureImpliesAnEnemyPieceOnThatSquare);
  FOW_RUN_TEST(fow::CaptureOnASquareThatGoesUnseenIsStillInferred);
  FOW_RUN_TEST(fow::RecoveryRetainsTheKnownCaptureSquare);
  FOW_RUN_TEST(fow::EnPassantDoesNotInventACapturerOnTheVictimSquare);
  FOW_RUN_TEST(fow::VisibleOrdinaryCaptureOfADoublePushedPawnIsRecognized);
  FOW_RUN_TEST(fow::CaptureEvidenceSurvivesOurMoveButExpiresOnTheirNextMove);
  FOW_RUN_TEST(fow::OurCaptureClearsTheEvidenceConstraint);
  FOW_RUN_TEST(fow::GroupedPredictionEnumeratesTheExactOpeningSupportOnce);
  FOW_RUN_TEST(fow::GroupedPredictionPreservesBeliefInvariantsAcrossGames);
  FOW_RUN_TEST(fow::ContinuedPlayProvesOurLastMoveDidNotLose);
  FOW_RUN_TEST(fow::ContinuationAllowsAnInvisibleCheckByEitherMover);
  FOW_RUN_TEST(fow::RecoveryConditionsOnThePreviousMoversSurvival);
  FOW_RUN_TEST(fow::ImpossibleContinuationIsBoundedAndReported);
  FOW_RUN_TEST(fow::HistoryRecoveryReplaysAnOpeningWithoutInventingPieces);
  FOW_RUN_TEST(fow::HistoryRecoveryPreservesAHiddenBishopAndAllowsItsMove);
  FOW_RUN_TEST(fow::HistoryRecoveryRetainsSpecialMoveMetadata);
  FOW_RUN_TEST(fow::HistoryRecoveryRejectsAnImpossibleOwnTransition);
  FOW_RUN_TEST(fow::RecoversWhenEveryHypothesisIsContradicted);
  FOW_RUN_TEST(fow::BeliefMaintainsItsInvariants);
  return fow::testing::Summarize("belief_test");
}
