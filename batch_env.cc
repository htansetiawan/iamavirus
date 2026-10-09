// Batched training simulator (reports/Deep RL for Fog of War chess.md, experiment 5).
//
// N games live in C++. Each ply the side to move gets its exact legal candidates from
// its own observation history (the bot's NeuralTracker), Python picks a candidate index
// per game, and one call applies it, delivers both sides' observations with the
// referee's phases, and scores the outcome with the referee's ordering. Every
// observation event's input planes are queued per side, so the learner's recurrent
// state sees exactly the events the arena would deliver. No Python per ply per game.
#include <array>
#include <cstdint>
#include <cstring>
#include <random>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "bitboard.h"
#include "move.h"
#include "neural_observation.h"
#include "observation.h"
#include "position.h"

using fow::Move;
using fow::MoveList;
using fow::NeuralCandidate;
using fow::NeuralTracker;
using fow::Observation;
using fow::Position;

namespace {

constexpr int kPlanes = 32 * 64;
constexpr int kScalars = 8;
const char* kStart = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

struct Event {
  std::array<float, kPlanes> planes;
  std::array<float, kScalars> scalars;
};

uint64_t RepetitionKey(const Position& position) {
  uint64_t key = position.key();
  const int ep = position.en_passant_square();
  if (ep >= 0) {
    const int side = position.side_to_move();
    const fow::Bitboard capturers = fow::kPawnAttacks[side ^ 1][ep] & position.pieces(fow::kPawn, side);
    if (capturers == 0) key ^= fow::g_zobrist_en_passant_file[fow::FileOf(ep)];
  }
  return key;
}

struct Game {
  Position truth;
  NeuralTracker trackers[2] = {NeuralTracker(fow::kWhite), NeuralTracker(fow::kBlack)};
  std::vector<Event> pending[2];
  std::unordered_map<uint64_t, int> repetitions;
  std::vector<NeuralCandidate> candidates;  // for the side to move
  int plies = 0;
  int status = 0;  // 0 ongoing, 1 white wins, 2 black wins, 3 draw
  int reason = 0;  // 1 king capturable, 2 repetition, 3 fifty moves, 4 no legal moves, 5 ply limit
  Move last_move = fow::kNullMove;

  void Push(int side) {
    Event e;
    trackers[side].Planes(e.planes.data());
    trackers[side].Scalars(e.scalars.data());
    pending[side].push_back(e);
  }

  void Reset() {
    fow::PositionFromFen(kStart, &truth);
    trackers[0] = NeuralTracker(fow::kWhite);
    trackers[1] = NeuralTracker(fow::kBlack);
    pending[0].clear();
    pending[1].clear();
    repetitions.clear();
    repetitions[RepetitionKey(truth)] = 1;
    candidates.clear();
    plies = 0;
    status = 0;
    reason = 0;
    last_move = fow::kNullMove;
    for (int side = 0; side < 2; ++side) {
      trackers[side].Observe(Observation(fow::RenderObservation(truth, side)), fow::kPhaseInitial, 0);
      Push(side);
    }
    Refresh();
  }

  // Candidates of the side to move, from its own observation history.
  void Refresh() {
    candidates.clear();
    if (status != 0) return;
    const int mover = truth.side_to_move();
    MoveList legal;
    trackers[mover].LegalCandidates(&legal);
    candidates = trackers[mover].MakeCandidates(legal);
  }

  void Outcome(int max_plies) {
    const int mover = truth.side_to_move();
    if (truth.PreviousMoverIsLost()) {  // the side to move can take the king
      status = mover == fow::kWhite ? 1 : 2;
      reason = 1;
      return;
    }
    if (repetitions[RepetitionKey(truth)] >= 3) {
      status = 3;
      reason = 2;
      return;
    }
    if (truth.halfmove_clock() >= 100) {
      status = 3;
      reason = 3;
      return;
    }
    MoveList legal;
    truth.GenerateMoves(&legal);
    if (legal.empty()) {
      status = mover == fow::kWhite ? 2 : 1;
      reason = 4;
      return;
    }
    if (plies >= max_plies) {
      status = 3;
      reason = 5;
    }
  }

  // Applies candidate `index` for the side to move. Returns the status.
  int Step(int index, int max_plies) {
    if (status != 0 || index < 0 || index >= static_cast<int>(candidates.size())) return status;
    const int mover = truth.side_to_move();
    const Move move = candidates[static_cast<std::size_t>(index)].move;
    trackers[mover].RecordOwnMove(move);
    last_move = move;
    fow::UndoState undo;
    truth.MakeMove(move, &undo);
    ++plies;
    repetitions[RepetitionKey(truth)] += 1;
    Outcome(max_plies);
    if (status == 0) {
      // The referee shows no view of a rules-decided terminal frame.
      for (int side = 0; side < 2; ++side) {
        const int phase = side == mover ? fow::kPhaseAfterOwnMove : fow::kPhaseAfterOpponentMove;
        trackers[side].Observe(Observation(fow::RenderObservation(truth, side)), phase, plies);
        Push(side);
      }
    }
    Refresh();
    return status;
  }
};

struct Batch {
  std::vector<Game> games;
  int max_plies = 400;
};

Batch* B(void* h) { return static_cast<Batch*>(h); }

}  // namespace

extern "C" {

void* fow_batch_new(int n, int max_plies) {
  fow::InitializeAttackTables();
  fow::InitializeZobrist();
  Batch* b = new Batch;
  b->games.resize(static_cast<std::size_t>(n));
  b->max_plies = max_plies;
  for (Game& g : b->games) g.Reset();
  return b;
}

void fow_batch_free(void* h) { delete B(h); }

void fow_batch_reset(void* h, int i) { B(h)->games[static_cast<std::size_t>(i)].Reset(); }

int fow_batch_side_to_move(void* h, int i) { return B(h)->games[static_cast<std::size_t>(i)].truth.side_to_move(); }
int fow_batch_status(void* h, int i) { return B(h)->games[static_cast<std::size_t>(i)].status; }
int fow_batch_reason(void* h, int i) { return B(h)->games[static_cast<std::size_t>(i)].reason; }
int fow_batch_plies(void* h, int i) { return B(h)->games[static_cast<std::size_t>(i)].plies; }

// Parity probes: a side's current view and the last move played (UCI), for tests.
void fow_batch_view(void* h, int i, int side, char* out) {
  const std::string v = fow::RenderObservation(B(h)->games[static_cast<std::size_t>(i)].truth, side);
  std::memcpy(out, v.c_str(), 65);
}

void fow_batch_last_move(void* h, int i, char* out) {
  const Game& g = B(h)->games[static_cast<std::size_t>(i)];
  const std::string u = g.last_move == fow::kNullMove ? std::string("-") : fow::MoveToUci(g.last_move);
  std::memcpy(out, u.c_str(), u.size() + 1);
}

void fow_batch_board(void* h, int i, char* out) {
  const Position& p = B(h)->games[static_cast<std::size_t>(i)].truth;
  for (int sq = 0; sq < 64; ++sq) {
    const int type = p.piece_at(sq);
    out[sq] = type == fow::kNoPiece ? '-' : fow::PieceTypeToSymbol(type, p.color_at(sq));
  }
  out[64] = '\0';
}

// Moves the pending observation events of `side` in game i into planes [k][2048] and
// scalars [k][8]; returns k (at most `capacity`), and clears them.
int fow_batch_take_events(void* h, int i, int side, float* planes, float* scalars, int capacity) {
  Game& g = B(h)->games[static_cast<std::size_t>(i)];
  auto& q = g.pending[side];
  const int k = std::min<int>(capacity, static_cast<int>(q.size()));
  for (int e = 0; e < k; ++e) {
    std::memcpy(planes + static_cast<std::size_t>(e) * kPlanes, q[static_cast<std::size_t>(e)].planes.data(), sizeof(float) * kPlanes);
    std::memcpy(scalars + static_cast<std::size_t>(e) * kScalars, q[static_cast<std::size_t>(e)].scalars.data(), sizeof(float) * kScalars);
  }
  q.clear();
  return k;
}

// Candidates of the side to move in game i (canonical from/to, promotion code); returns the count.
int fow_batch_candidates(void* h, int i, int* from, int* to, int* promo, int capacity) {
  const Game& g = B(h)->games[static_cast<std::size_t>(i)];
  const int n = std::min<int>(capacity, static_cast<int>(g.candidates.size()));
  for (int k = 0; k < n; ++k) {
    const NeuralCandidate& c = g.candidates[static_cast<std::size_t>(k)];
    from[k] = c.from;
    to[k] = c.to;
    promo[k] = c.promotion;
  }
  return n;
}

// Applies one candidate index per game (negative = skip) across all games, on
// `threads` threads; writes each game's status. Returns the number of moves applied.
int fow_batch_step_all(void* h, const int* actions, int* status, int threads) {
  Batch* b = B(h);
  const int n = static_cast<int>(b->games.size());
  auto work = [&](int lo, int hi) {
    for (int i = lo; i < hi; ++i) {
      Game& g = b->games[static_cast<std::size_t>(i)];
      if (actions[i] >= 0) g.Step(actions[i], b->max_plies);
      status[i] = g.status;
    }
  };
  threads = std::max(1, threads);
  if (threads == 1) {
    work(0, n);
  } else {
    std::vector<std::thread> pool;
    const int chunk = (n + threads - 1) / threads;
    for (int t = 0; t < threads; ++t) {
      const int lo = t * chunk, hi = std::min(n, lo + chunk);
      if (lo < hi) pool.emplace_back(work, lo, hi);
    }
    for (std::thread& th : pool) th.join();
  }
  int applied = 0;
  for (int i = 0; i < n; ++i) applied += actions[i] >= 0;
  return applied;
}

// Throughput probe: uniform random candidates in every game for `steps` rounds,
// finished games reset in place; returns the number of decisions made.
long long fow_batch_random_rollout(void* h, int steps, unsigned long long seed, int threads) {
  Batch* b = B(h);
  const int n = static_cast<int>(b->games.size());
  std::vector<int> actions(static_cast<std::size_t>(n)), status(static_cast<std::size_t>(n));
  std::mt19937_64 rng(seed);
  long long decisions = 0;
  for (int s = 0; s < steps; ++s) {
    for (int i = 0; i < n; ++i) {
      Game& g = b->games[static_cast<std::size_t>(i)];
      if (g.status != 0) g.Reset();
      g.pending[0].clear();
      g.pending[1].clear();
      const int c = static_cast<int>(g.candidates.size());
      actions[static_cast<std::size_t>(i)] = c > 0 ? static_cast<int>(rng() % static_cast<uint64_t>(c)) : -1;
    }
    decisions += fow_batch_step_all(h, actions.data(), status.data(), threads);
  }
  return decisions;
}

}  // extern "C"
