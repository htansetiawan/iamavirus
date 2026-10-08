// Copyright 2026. Fog of War chess engine.
//
// Offline benchmark against real arena games.
//
// Self-play cannot see the weaknesses that lose rated games: a bot playing itself
// shares its own blind spots, so a flaw both sides have cancels out in the score.
// Three changes measured +33, -47 and +51 Elo that way, none of them conclusive.
//
// This replays real games instead. For each game it rebuilds the truth by
// applying the recorded moves, renders the observations the seated player
// actually received -- a renderer that agrees with referee.py on 47,875 checks --
// and drives the engine's belief through them. At selected plies it asks the
// engine what it would play, then checks against the true board whether that move
// leaves our king capturable.
//
// The engine's answer is discarded and the game's real move is played instead, so
// the position stays on the rails of the real game and later plies remain genuine.
//
// This gives thousands of labelled decisions from opponents several hundred Elo
// stronger, which is a far better signal than any number of self-play games.
//
// Corpus line: <id> <side w|b> <result> <reason> <opponent> <uci moves...>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "../belief.h"
#include "../bitboard.h"
#include "../engine.h"
#include "../observation.h"
#include "../position.h"

namespace fow {
namespace {

struct Seat {
  std::string id;
  int side = kWhite;
  std::string result;
  std::string reason;
  std::string opponent;
  std::vector<std::string> moves;
};

struct Tally {
  int seats = 0;
  int decisions = 0;
  int blunders = 0;          // engine's move loses the king on the true board
  int fatal_positions = 0;   // plies where the real player lost the game
  int fatal_saved = 0;       // ...and the engine would not have
  int matched = 0;           // engine chose the same move as the real player
  int unsafe_rejected = 0;
  int exposed = 0;           // engine's move leaves >= 3 points en prise (true board)
  int real_exposed = 0;      // ...and the same for the move actually played
  // The two-ply pattern the one-ply metric cannot see: the move lets the
  // opponent set up >= 3 points with one quiet move to a square the mover's
  // post-move view does not show (true board).
  int threatened = 0;
  int real_threatened = 0;
  // The same counts split by our seat colour, to test for a colour-specific
  // defect (the arena record and the paired gate both look worse as Black).
  int side_decisions[2] = {0, 0};
  int side_blunders[2] = {0, 0};
  int side_exposed[2] = {0, 0};
  int side_real_exposed[2] = {0, 0};
  int side_threatened[2] = {0, 0};
  int side_real_threatened[2] = {0, 0};
  int side_fatal[2] = {0, 0};
  int side_saved[2] = {0, 0};
  // Vision after the move on the true board: squares we see, and our pieces
  // they see; engine vs the real player.
  long vision_engine = 0;
  long vision_real = 0;
  long seen_pieces_engine = 0;
  long seen_pieces_real = 0;
  // After the move, the opponent has a quiet move to a square the mover does
  // not see that puts an unseen attacker on the mover's king (true board).
  // Our queen capturable for a net loss of >= 5 points after the move (true board).
  int queen_en_prise = 0;
  // Opening split (ply < 30): decisions, queen en prise and en prise, engine vs real.
  int early_decisions = 0;
  int early_queen_en_prise = 0;
  int early_real_queen_en_prise = 0;
  int early_exposed = 0;
  int early_real_exposed = 0;
  int book_moves = 0;
  int real_queen_en_prise = 0;
  int king_threatened = 0;
  int real_king_threatened = 0;
  // Belief calibration: over hidden squares holding an enemy piece on the
  // true board, the share of particles that hold that piece there (averaged
  // per decision); and, at the recorded fatal plies, the share of particles
  // holding the true attacker of the king's destination square.
  double hidden_piece_mass = 0.0;
  int hidden_piece_decisions = 0;
  double attacker_mass = 0.0;
  int attacker_plies = 0;
  // Queen-loss seats: belief mass on the true capturer of our queen after the real move,
  // in bands, and how often the engine's own choice also leaves the queen en prise.
  double qc_mass = 0.0;
  int qc_plies = 0;
  int qc_band[3] = {0, 0, 0};
  int qc_band_repeat[3] = {0, 0, 0};
  int qc_avoidable[3] = {0, 0, 0};         // a true-board alternative kept the queen, the king and >=3 points safe
  int qc_avoidable_repeat[3] = {0, 0, 0};
  // Gym: unseen king threats created by the engine's choice vs the real move, at the fatal plies.
  int strike_unseen = 0;
  int real_strike_unseen = 0;
  int fatal_decisions = 0;
};

// Average over the true board's hidden enemy pieces of the particle share
// holding that piece type on that square. 1.0 means the population knows
// every hidden piece exactly; the uniform scatter of a rebuild scores ~0.05.
double HiddenPieceMass(const BeliefState& belief, const Position& truth,
                       const Observation& view, int side) {
  const int enemy = side ^ 1;
  const std::vector<Position>& population = belief.particles();
  if (population.empty()) return 0.0;
  double total = 0.0;
  int squares = 0;
  for (int square = 0; square < kNumSquares; ++square) {
    if (!view.IsUnseen(square)) continue;
    const int type = truth.piece_at(square);
    if (type == kNoPiece || truth.color_at(square) != enemy) continue;
    int holders = 0;
    for (const Position& particle : population) {
      if (particle.piece_at(square) == type && particle.color_at(square) == enemy) ++holders;
    }
    total += static_cast<double>(holders) / population.size();
    ++squares;
  }
  return squares > 0 ? total / squares : -1.0;
}

// At a fatal ply: after the real (losing) move, the share of particles that
// hold the piece which actually attacks our king, on its true square.
double AttackerMass(const BeliefState& belief, const Position& truth, Move fatal, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(fatal, &undo);
  const int king = after.KingSquare(side);
  if (king < 0) return -1.0;
  const Bitboard attackers = after.AttackersTo(king, side ^ 1);
  if (attackers == 0) return -1.0;
  const std::vector<Position>& population = belief.particles();
  if (population.empty()) return 0.0;
  // Credit any attacker square the particle agrees about.
  int holders = 0;
  for (const Position& particle : population) {
    Bitboard scan = attackers;
    bool holds = false;
    while (scan) {
      const int square = PopLsb(&scan);
      if (particle.piece_at(square) == after.piece_at(square) &&
          particle.color_at(square) == side ^ 1) holds = true;
    }
    if (holds) ++holders;
  }
  return static_cast<double>(holders) / population.size();
}

// At a fatal ply of a queen-loss seat: after the real move, the share of
// particles that hold at least one of the pieces which actually attack our
// queen, on its true square. -1 when no queen is attacked.
double QueenCapturerMass(const BeliefState& belief, const Position& truth, Move fatal, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(fatal, &undo);
  if (after.PreviousMoverIsLost()) return -1.0;
  Bitboard queens = after.pieces(kQueen, side);
  Bitboard attackers = 0;
  while (queens) attackers |= after.AttackersTo(PopLsb(&queens), side ^ 1);
  if (attackers == 0) return -1.0;
  const std::vector<Position>& population = belief.particles();
  if (population.empty()) return 0.0;
  int holders = 0;
  for (const Position& particle : population) {
    Bitboard scan = attackers;
    bool holds = false;
    while (scan) {
      const int square = PopLsb(&scan);
      if (particle.piece_at(square) == after.piece_at(square) &&
          particle.color_at(square) == (side ^ 1)) holds = true;
    }
    if (holds) ++holders;
  }
  return static_cast<double>(holders) / population.size();
}

// After `move` on the true board, does the mover attack the enemy king from a
// square the enemy's own view of the new position does not show? The gym's
// "strike from the fog" test: the kind of move that decides most games.
bool KingThreatUnseen(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  if (after.PreviousMoverIsLost()) return false;
  const int king = after.KingSquare(side ^ 1);
  if (king < 0) return false;
  Bitboard attackers = after.AttackersTo(king, side);
  if (attackers == 0) return false;
  const Observation enemy_view(RenderObservation(after, side ^ 1));
  while (attackers) {
    if (enemy_view.IsUnseen(PopLsb(&attackers))) return true;
  }
  return false;
}

// Material the mover leaves to the opponent's best immediate capture after
// `move` on the true board, in pawns; 0 when the move loses the king outright
// (that is counted separately).
int ExposureOf(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  if (after.PreviousMoverIsLost()) return 0;
  return BestNetCapture(&after, side) / 100;
}

// Points (beyond what they can already take) the opponent can set up with one
// quiet move to a square the mover's post-move view does not show, on the true
// board: the oracle version of Engine::ExpectedHiddenThreat.
int HiddenThreatOf(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  if (after.PreviousMoverIsLost()) return 0;
  const int already = BestNetCapture(&after, side);
  const Bitboard seen = VisibleSquares(after, side);
  MoveList replies;
  after.GenerateMoves(&replies);
  int best = already;
  for (const Move reply : replies) {
    const int to = MoveTo(reply);
    if (after.piece_at(to) != kNoPiece) continue;
    if (MoveFlagOf(reply) == kFlagEnPassant) continue;
    if (after.piece_at(MoveFrom(reply)) == kKing) continue;
    if (seen & SquareBB(to)) continue;
    UndoState quiet;
    after.MakeMove(reply, &quiet);
    after.set_side_to_move(side ^ 1);
    const int threat = BestNetCapture(&after, side);
    after.set_side_to_move(side);
    after.UnmakeMove(reply, quiet);
    if (threat > best) best = threat;
  }
  return (best - already) / 100;
}

// Vision after `move` on the true board: (our visible squares, our pieces
// visible to them).
std::pair<int, int> VisionOf(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  const Bitboard ours = VisibleSquares(after, side);
  const Bitboard theirs = VisibleSquares(after, side ^ 1);
  return {PopCount(ours), PopCount(theirs & after.pieces_of(side))};
}

// The king version of HiddenThreatOf: can the opponent, with one quiet move
// to a square the mover's post-move view does not show, put an attacker the
// mover cannot see on the mover's king?
bool HiddenKingThreatOf(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  const int king = after.KingSquare(side);
  if (king < 0 || after.IsAttacked(king, side ^ 1)) return false;
  const Bitboard seen = VisibleSquares(after, side);
  MoveList replies;
  after.GenerateMoves(&replies);
  for (const Move reply : replies) {
    const int to = MoveTo(reply);
    if (after.piece_at(to) != kNoPiece) continue;
    if (MoveFlagOf(reply) == kFlagEnPassant) continue;
    if (after.piece_at(MoveFrom(reply)) == kKing) continue;
    if (seen & SquareBB(to)) continue;
    UndoState quiet;
    after.MakeMove(reply, &quiet);
    const bool hit = (after.AttackersTo(king, side ^ 1) & ~seen) != 0;
    after.UnmakeMove(reply, quiet);
    if (hit) return true;
  }
  return false;
}

// Is the mover's queen capturable for a net loss of at least five points after
// `move`, on the true board?
bool QueenEnPrise(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  if (after.PreviousMoverIsLost()) return false;
  Bitboard queens = after.pieces(kQueen, side);
  while (queens) {
    const int square = PopLsb(&queens);
    const Bitboard attackers = after.AttackersTo(square, side ^ 1);
    if (attackers == 0) continue;
    int cheapest = kPieceValue[kQueen] + 1;
    Bitboard scan = attackers;
    while (scan) {
      const int value = kPieceValue[after.piece_at(PopLsb(&scan))];
      if (value < cheapest) cheapest = value;
    }
    const bool defended = after.AttackersTo(square, side) != 0;
    const int net = kPieceValue[kQueen] - (defended ? cheapest : 0);
    if (net >= 500) return true;
  }
  return false;
}

Move FindMove(const Position& position, const std::string& uci) {
  MoveList legal;
  position.GenerateMoves(&legal);
  for (const Move candidate : legal) {
    if (MoveToUci(candidate) == uci) return candidate;
  }
  return kNullMove;
}

// Does `move` leave the mover's king capturable on the true board?
bool LosesKing(const Position& truth, Move move, int side) {
  Position after = truth;
  UndoState undo;
  after.MakeMove(move, &undo);
  const int king = after.KingSquare(side);
  return king < 0 || after.IsAttacked(king, side ^ 1);
}

void RunSeat(const Seat& seat, const EngineOptions& options, int stride,
             Tally* tally, bool verbose, uint64_t seed) {
  Position truth;
  if (!PositionFromFen(
          "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", &truth)) {
    return;
  }
  Engine engine(seat.side, 180.0, 2.0, options, seed);
  if (const char* book = std::getenv("FOW_BOOK")) {
    if (std::string(book) != "off") engine.LoadBook(book);
  }
  ++tally->seats;

  // The last ply played by our seat is the one that ended the game when we lost.
  int last_own_ply = -1;
  for (size_t ply = 0; ply < seat.moves.size(); ++ply) {
    const int mover = (ply % 2 == 0) ? kWhite : kBlack;
    if (mover == seat.side) last_own_ply = static_cast<int>(ply);
  }
  const bool we_lost = (seat.result == "1-0" && seat.side == kBlack) ||
                       (seat.result == "0-1" && seat.side == kWhite);
  const bool fatal_is_ours = we_lost && seat.reason == "King_capturable";

  bool we_just_moved = false;
  for (size_t ply = 0; ply < seat.moves.size(); ++ply) {
    const Observation view(RenderObservation(truth, seat.side));
    engine.Observe(view, we_just_moved);
    we_just_moved = false;

    const Move actual = FindMove(truth, seat.moves[ply]);
    if (actual == kNullMove) {
      std::fprintf(stderr, "  %s: illegal recorded move %s at ply %zu\n",
                   seat.id.c_str(), seat.moves[ply].c_str(), ply);
      return;
    }

    if (truth.side_to_move() == seat.side) {
      const bool is_fatal_ply =
          fatal_is_ours && static_cast<int>(ply) == last_own_ply;
      // Sample every stride-th *decision of this seat*. The earlier
      // `ply % stride` sampled even plies only, i.e. White's decisions, so
      // Black seats contributed nothing but their terminal losses (Astra's
      // review); counts from before this fix are White-biased diagnostics.
      const bool sampled = ((ply / 2) % static_cast<size_t>(stride)) == 0;
      if (is_fatal_ply || sampled) {
        DecisionTrace trace;
        const Move choice = engine.ChooseMove(view, 150.0, &trace);
        if (choice != kNullMove) {
          ++tally->decisions;
          ++tally->side_decisions[seat.side];
          tally->unsafe_rejected += trace.rejected_unsafe;
          const bool bad = LosesKing(truth, choice, seat.side);
          if (bad) ++tally->blunders;
          if (bad) ++tally->side_blunders[seat.side];
          const double mass = HiddenPieceMass(engine.belief(), truth, view, seat.side);
          if (mass >= 0.0) {
            tally->hidden_piece_mass += mass;
            ++tally->hidden_piece_decisions;
          }
          if (is_fatal_ply) {
            const double held = AttackerMass(engine.belief(), truth, actual, seat.side);
            if (held >= 0.0) {
              tally->attacker_mass += held;
              ++tally->attacker_plies;
            }
            ++tally->fatal_decisions;
            if (KingThreatUnseen(truth, choice, seat.side)) ++tally->strike_unseen;
            if (KingThreatUnseen(truth, actual, seat.side)) ++tally->real_strike_unseen;
            const double qheld = QueenCapturerMass(engine.belief(), truth, actual, seat.side);
            if (qheld >= 0.0) {
              tally->qc_mass += qheld;
              ++tally->qc_plies;
              const int band = qheld < 0.05 ? 0 : (qheld < 0.3 ? 1 : 2);
              ++tally->qc_band[band];
              const bool repeat = QueenEnPrise(truth, choice, seat.side);
              if (repeat) ++tally->qc_band_repeat[band];
              bool safe_alternative = false;
              {
                MoveList legal;
                truth.GenerateMoves(&legal);
                for (int i = 0; i < legal.size() && !safe_alternative; ++i) {
                  const Move m = legal[i];
                  if (!LosesKing(truth, m, seat.side) && !QueenEnPrise(truth, m, seat.side) &&
                      ExposureOf(truth, m, seat.side) < 3) safe_alternative = true;
                }
              }
              if (safe_alternative) {
                ++tally->qc_avoidable[band];
                if (repeat) ++tally->qc_avoidable_repeat[band];
              }
              if (verbose) {
                const int actual_capture = kPieceValue[truth.piece_at(MoveTo(actual))];
                const int choice_capture = kPieceValue[truth.piece_at(MoveTo(choice))];
                std::printf("  QL %s ply %zu mass %.3f real %s(x%d) engine %s(x%d) %s\n", seat.id.c_str(), ply, qheld,
                            MoveToUci(actual).c_str(), actual_capture, MoveToUci(choice).c_str(), choice_capture,
                            repeat ? (safe_alternative ? "REPEAT-avoidable" : "REPEAT-forced") : "avoided");
              }
            }
          }
          if (choice == actual) ++tally->matched;
          if (ExposureOf(truth, choice, seat.side) >= 3) {
            ++tally->exposed;
            ++tally->side_exposed[seat.side];
          }
          if (ExposureOf(truth, actual, seat.side) >= 3) {
            ++tally->real_exposed;
            ++tally->side_real_exposed[seat.side];
          }
          {
            const auto ve = VisionOf(truth, choice, seat.side);
            const auto vr = VisionOf(truth, actual, seat.side);
            tally->vision_engine += ve.first;
            tally->seen_pieces_engine += ve.second;
            tally->vision_real += vr.first;
            tally->seen_pieces_real += vr.second;
          }
          if (QueenEnPrise(truth, choice, seat.side)) ++tally->queen_en_prise;
          if (QueenEnPrise(truth, actual, seat.side)) ++tally->real_queen_en_prise;
          if (ply < 30) {
            ++tally->early_decisions;
            if (QueenEnPrise(truth, choice, seat.side)) ++tally->early_queen_en_prise;
            if (QueenEnPrise(truth, actual, seat.side)) ++tally->early_real_queen_en_prise;
            if (ExposureOf(truth, choice, seat.side) >= 3) ++tally->early_exposed;
            if (ExposureOf(truth, actual, seat.side) >= 3) ++tally->early_real_exposed;
          }
          if (trace.from_book) ++tally->book_moves;
          if (HiddenKingThreatOf(truth, choice, seat.side)) ++tally->king_threatened;
          if (HiddenKingThreatOf(truth, actual, seat.side)) ++tally->real_king_threatened;
          if (HiddenThreatOf(truth, choice, seat.side) >= 3) {
            ++tally->threatened;
            ++tally->side_threatened[seat.side];
          }
          if (HiddenThreatOf(truth, actual, seat.side) >= 3) {
            ++tally->real_threatened;
            ++tally->side_real_threatened[seat.side];
          }
          if (is_fatal_ply) {
            ++tally->fatal_positions;
            ++tally->side_fatal[seat.side];
            if (!bad) {
              ++tally->fatal_saved;
              ++tally->side_saved[seat.side];
            }
            if (verbose) {
              std::printf("  %-10s vs %-20s ply %3zu  real played %-6s (lost)  "
                          "engine plays %-6s  %s\n",
                          seat.id.c_str(), seat.opponent.c_str(), ply,
                          seat.moves[ply].c_str(), MoveToUci(choice).c_str(),
                          bad ? "ALSO LOSES" : "survives");
            }
          }
        }
      }
      engine.NotifyMovePlayed(actual);
      we_just_moved = true;
    }
    UndoState undo;
    truth.MakeMove(actual, &undo);
    if (truth.KingSquare(kWhite) < 0 || truth.KingSquare(kBlack) < 0) break;
  }
}

}  // namespace
}  // namespace fow

int main(int argc, char** argv) {
  using namespace fow;
  if (argc < 2) {
    std::fprintf(stderr,
                 "usage: %s CORPUS [stride] [node_budget] [verbose]\n", argv[0]);
    return 2;
  }
  const int stride = argc > 2 ? std::atoi(argv[2]) : 6;
  const uint64_t nodes = argc > 3 ? std::strtoull(argv[3], nullptr, 10) : 1000000;
  const bool verbose = argc > 4;
  // FOW_SEED varies the engine's RNG so two runs of one arm show how much of
  // a difference between arms is churn on near-tied decisions.
  uint64_t seed = 777;
  if (const char* text = std::getenv("FOW_SEED")) seed = std::strtoull(text, nullptr, 10);

  InitializeAttackTables();
  InitializeZobrist();
  EngineOptions options = EngineOptionsFromEnvironment();
  options.node_budget = nodes;
  options.time_reserve = 0.0;

  std::ifstream input(argv[1]);
  if (!input) {
    std::fprintf(stderr, "cannot open %s\n", argv[1]);
    return 2;
  }
  Tally tally;
  std::string line;
  while (std::getline(input, line)) {
    if (line.empty()) continue;
    std::istringstream stream(line);
    Seat seat;
    std::string side;
    stream >> seat.id >> side >> seat.result >> seat.reason >> seat.opponent;
    seat.side = side == "w" ? kWhite : kBlack;
    std::string uci;
    while (stream >> uci) seat.moves.push_back(uci);
    if (seat.moves.size() < 4) continue;
    RunSeat(seat, options, stride, &tally, verbose, seed);
  }

  std::printf("\ncorpus: %s   stride %d   %llu nodes/decision   seed %llu\n", argv[1],
              stride, static_cast<unsigned long long>(nodes), static_cast<unsigned long long>(seed));
  std::printf("  seats replayed            : %d\n", tally.seats);
  std::printf("  decisions evaluated       : %d\n", tally.decisions);
  std::printf("  immediate king losses     : %d (%.2f%%)\n", tally.blunders,
              tally.decisions ? 100.0 * tally.blunders / tally.decisions : 0.0);
  std::printf("  matched the real move     : %d (%.1f%%)\n", tally.matched,
              tally.decisions ? 100.0 * tally.matched / tally.decisions : 0.0);
  std::printf("  belief: hidden enemy piece mass %.3f (%d decisions); true attacker held at fatal plies %.3f (%d plies)\n",
              tally.hidden_piece_decisions ? tally.hidden_piece_mass / tally.hidden_piece_decisions : 0.0,
              tally.hidden_piece_decisions,
              tally.attacker_plies ? tally.attacker_mass / tally.attacker_plies : 0.0, tally.attacker_plies);
  if (tally.fatal_decisions > 0) {
    std::printf("  unseen king threat created at fatal plies: engine %d (%.1f%%), real move %d (%.1f%%) of %d\n",
                tally.strike_unseen, 100.0 * tally.strike_unseen / tally.fatal_decisions,
                tally.real_strike_unseen, 100.0 * tally.real_strike_unseen / tally.fatal_decisions, tally.fatal_decisions);
  }
  if (tally.qc_plies > 0) {
    std::printf("  queen capturer held at fatal plies: %.3f (%d plies); mass <0.05: %d plies, engine repeats %d; 0.05-0.3: %d, repeats %d; >=0.3: %d, repeats %d\n",
                tally.qc_mass / tally.qc_plies, tally.qc_plies, tally.qc_band[0], tally.qc_band_repeat[0],
                tally.qc_band[1], tally.qc_band_repeat[1], tally.qc_band[2], tally.qc_band_repeat[2]);
    std::printf("  ... with a safe alternative on the true board: <0.05: %d plies, engine repeats %d; 0.05-0.3: %d, repeats %d; >=0.3: %d, repeats %d\n",
                tally.qc_avoidable[0], tally.qc_avoidable_repeat[0], tally.qc_avoidable[1], tally.qc_avoidable_repeat[1],
                tally.qc_avoidable[2], tally.qc_avoidable_repeat[2]);
  }
  std::printf("  left >=3 points en prise  : engine %d (%.2f%%), real player %d (%.2f%%)\n",
              tally.exposed, tally.decisions ? 100.0 * tally.exposed / tally.decisions : 0.0,
              tally.real_exposed, tally.decisions ? 100.0 * tally.real_exposed / tally.decisions : 0.0);
  std::printf("  left a 2-ply hidden threat>=3: engine %d (%.2f%%), real player %d (%.2f%%)\n",
              tally.threatened, tally.decisions ? 100.0 * tally.threatened / tally.decisions : 0.0,
              tally.real_threatened, tally.decisions ? 100.0 * tally.real_threatened / tally.decisions : 0.0);
  std::printf("  real losing positions     : %d\n", tally.fatal_positions);
  std::printf("  ...the engine survives    : %d (%.0f%%)\n", tally.fatal_saved,
              tally.fatal_positions
                  ? 100.0 * tally.fatal_saved / tally.fatal_positions : 0.0);
  std::printf("  opening (ply<30): %d decisions, book moves %d; queen en prise engine %.2f%% real %.2f%%; en prise engine %.2f%% real %.2f%%\n",
              tally.early_decisions, tally.book_moves,
              tally.early_decisions ? 100.0 * tally.early_queen_en_prise / tally.early_decisions : 0.0,
              tally.early_decisions ? 100.0 * tally.early_real_queen_en_prise / tally.early_decisions : 0.0,
              tally.early_decisions ? 100.0 * tally.early_exposed / tally.early_decisions : 0.0,
              tally.early_decisions ? 100.0 * tally.early_real_exposed / tally.early_decisions : 0.0);
  std::printf("  queen left en prise (net>=5): engine %d (%.2f%%), real player %d (%.2f%%)\n",
              tally.queen_en_prise, tally.decisions ? 100.0 * tally.queen_en_prise / tally.decisions : 0.0,
              tally.real_queen_en_prise, tally.decisions ? 100.0 * tally.real_queen_en_prise / tally.decisions : 0.0);
  std::printf("  left a 2-ply hidden king threat: engine %d (%.2f%%), real player %d (%.2f%%)\n",
              tally.king_threatened, tally.decisions ? 100.0 * tally.king_threatened / tally.decisions : 0.0,
              tally.real_king_threatened, tally.decisions ? 100.0 * tally.real_king_threatened / tally.decisions : 0.0);
  std::printf("  vision after the move      : engine sees %.1f squares, %.2f of its pieces seen; real player %.1f squares, %.2f seen\n",
              tally.decisions ? static_cast<double>(tally.vision_engine) / tally.decisions : 0.0,
              tally.decisions ? static_cast<double>(tally.seen_pieces_engine) / tally.decisions : 0.0,
              tally.decisions ? static_cast<double>(tally.vision_real) / tally.decisions : 0.0,
              tally.decisions ? static_cast<double>(tally.seen_pieces_real) / tally.decisions : 0.0);
  for (int side = 0; side < 2; ++side) {
    const int n = tally.side_decisions[side];
    std::printf("  as %s: decisions %d, king losses %d (%.2f%%), en prise engine %.2f%% real %.2f%%, "
                "2-ply threat engine %.2f%% real %.2f%%, survives %d/%d\n",
                side == kWhite ? "White" : "Black", n, tally.side_blunders[side],
                n ? 100.0 * tally.side_blunders[side] / n : 0.0,
                n ? 100.0 * tally.side_exposed[side] / n : 0.0,
                n ? 100.0 * tally.side_real_exposed[side] / n : 0.0,
                n ? 100.0 * tally.side_threatened[side] / n : 0.0,
                n ? 100.0 * tally.side_real_threatened[side] / n : 0.0,
                tally.side_saved[side], tally.side_fatal[side]);
  }
  std::printf("  unsafe moves rejected     : %d (%.1f per decision)\n",
              tally.unsafe_rejected,
              tally.decisions
                  ? static_cast<double>(tally.unsafe_rejected) / tally.decisions
                  : 0.0);
  return 0;
}
