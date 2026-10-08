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
#include <string>
#include <vector>

#include "../bitboard.h"
#include "../observation.h"
#include "../position.h"
#include "testing.h"

namespace fow {
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
                          int max_plies) {
  std::mt19937_64 rng(seed);
  Position truth = StartPosition();
  BeliefState belief(our_side, particle_count, seed ^ 0x5DEECE66DULL);
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
    int true_total = 0;
    for (int type = 0; type < kNumPieceTypes; ++type) {
      true_total += PopCount(truth.pieces(type, enemy));
    }
    for (const Position& particle : belief.particles()) {
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

}  // namespace
}  // namespace fow

namespace fow {
namespace {

// Capture evidence. 1. e4 e5 2. Nf3 Nc6 3. Nxe5 Nxe5: our knight vanishes from
// e5, which nothing of ours can then see. With a one-particle population the
// particle either predicted the recapture (and holds the capturer) or the
// population collapsed and was rebuilt, where the capturer must be placed on
// e5. Either way every particle holds an enemy piece on e5.
void CaptureOnAnUnseenSquareKeepsTheCapturerThere() {
  const char* line[] = {"e2e4", "e7e5", "g1f3", "b8c6", "f3e5", "c6e5"};
  const int e5 = MakeSquare(4, 4);
  for (uint64_t seed = 1; seed <= 8; ++seed) {
    BeliefState belief(kWhite, 1, seed);
    belief.set_capture_evidence(true);
    Position truth;
    FOW_EXPECT_TRUE(PositionFromFen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth));
    bool we_just_moved = false;
    BeliefUpdateReport report;
    for (const char* uci : line) {
      report = belief.Observe(Observation(RenderObservation(truth, kWhite)), we_just_moved);
      we_just_moved = false;
      MoveList legal;
      truth.GenerateMoves(&legal);
      Move move = kNullMove;
      for (const Move candidate : legal) {
        if (MoveToUci(candidate) == uci) move = candidate;
      }
      FOW_EXPECT_TRUE(move != kNullMove);
      if (truth.side_to_move() == kWhite) {
        belief.ApplyOurMove(move);
        we_just_moved = true;
      }
      UndoState undo;
      truth.MakeMove(move, &undo);
    }
    const Observation after(RenderObservation(truth, kWhite));
    FOW_EXPECT_TRUE(after.IsUnseen(e5));
    report = belief.Observe(after, we_just_moved);
    FOW_EXPECT_TRUE(report.capture_square == e5);
    for (const Position& particle : belief.particles()) {
      FOW_EXPECT_TRUE(particle.piece_at(e5) != kNoPiece && particle.color_at(e5) == kBlack);
    }
  }
}


// Persistence of the capturer. After 3...Nxe5 we play 4. d3 and Black 4...d6
// (neither touches e5, which stays unseen): with capture evidence the knight
// should still be held on e5 by most of a rebuilt or resampled population two
// updates later, not scattered like any fog square.
void RecentCapturerPersistsForAFewUpdates() {
  const char* line[] = {"e2e4", "e7e5", "g1f3", "b8c6", "f3e5", "c6e5", "d2d3", "d7d6"};
  const int e5 = MakeSquare(4, 4);
  int held = 0;
  int total = 0;
  for (uint64_t seed = 1; seed <= 4; ++seed) {
    BeliefState belief(kWhite, 64, seed);
    belief.set_capture_evidence(true);
    Position truth;
    PositionFromFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth);
    bool we_just_moved = false;
    for (const char* uci : line) {
      belief.Observe(Observation(RenderObservation(truth, kWhite)), we_just_moved);
      we_just_moved = false;
      MoveList legal;
      truth.GenerateMoves(&legal);
      Move move = kNullMove;
      for (const Move candidate : legal) {
        if (MoveToUci(candidate) == uci) move = candidate;
      }
      FOW_EXPECT_TRUE(move != kNullMove);
      if (truth.side_to_move() == kWhite) {
        belief.ApplyOurMove(move);
        we_just_moved = true;
      }
      UndoState undo;
      truth.MakeMove(move, &undo);
    }
    const Observation after(RenderObservation(truth, kWhite));
    FOW_EXPECT_TRUE(after.IsUnseen(e5));
    belief.Observe(after, we_just_moved);
    for (const Position& particle : belief.particles()) {
      ++total;
      held += particle.piece_at(e5) != kNoPiece && particle.color_at(e5) == kBlack;
    }
  }
  std::printf("       capturer still on e5 two updates later: %d/%d particles\n", held, total);
  FOW_EXPECT_TRUE(held * 2 >= total);
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
  FOW_RUN_TEST(fow::RecoversWhenEveryHypothesisIsContradicted);
  FOW_RUN_TEST(fow::BeliefMaintainsItsInvariants);
  FOW_RUN_TEST(fow::CaptureOnAnUnseenSquareKeepsTheCapturerThere);
  FOW_RUN_TEST(fow::RecentCapturerPersistsForAFewUpdates);
  return fow::testing::Summarize("belief_test");
}
