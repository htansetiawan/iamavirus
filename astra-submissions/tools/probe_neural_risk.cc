// Offline risk diagnostic. Its input contains actor observations and own
// actions only. Truth labels are joined by Python after inference finishes.
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "bitboard.h"
#include "engine.h"
#include "neural_inference.h"

using namespace fow;

int main(int argc, char** argv) {
  try {
    if (argc != 2 && argc != 3) throw std::runtime_error("usage: probe MODEL_DIR [verify]");
    const bool verify = argc == 3 && std::string(argv[2]) == "verify";
    if (argc == 3 && !verify) throw std::runtime_error("unknown option");
    InitializeAttackTables();
    InitializeZobrist();
    auto options = EngineOptionsFromEnvironment();
    options.node_budget = 10000;  // Used only by the optional integration check.
    options.book_plies = 0;
    NeuralModel model;
    std::string error;
    if (!model.Load(argv[1], 1, &error)) throw std::runtime_error(error);
    std::unique_ptr<Engine> engine;
    std::unique_ptr<NeuralTracker> tracker;
    std::string command, game;
    int side = -1, ply = -1, event = -1;
    bool own_move_pending = false;
    std::cout.precision(17);
    while (std::cin >> command) {
      if (command == "START") {
        if (engine) throw std::runtime_error("nested START");
        std::cin >> game >> side;
        if (game.empty() || game.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789") != std::string::npos ||
            (side != kWhite && side != kBlack)) throw std::runtime_error("invalid actor identity");
        engine = std::make_unique<Engine>(side, 180.0, 2.0, options, 777);
        tracker = std::make_unique<NeuralTracker>(side);
        model.Reset();
        ply = -1;
        event = -1;
        own_move_pending = false;
      } else if (command == "OBS") {
        int next_ply, phase;
        std::string text;
        std::cin >> next_ply >> phase >> text;
        if (!engine || next_ply != ply + 1 || text.size() != 64 ||
            text.find_first_not_of("-?PNBRQKpnbrqk") != std::string::npos ||
            phase != (next_ply == 0 ? kPhaseInitial : own_move_pending ? kPhaseAfterOwnMove : kPhaseAfterOpponentMove)) {
          throw std::runtime_error("invalid observation sequence");
        }
        ply = next_ply;
        ++event;
        const Observation view(text);
        engine->Observe(view, own_move_pending);
        tracker->Observe(view, phase, ply);
        own_move_pending = false;
        float planes[kNeuralPlanes * kNumSquares], scalars[kNeuralScalars];
        tracker->Planes(planes);
        tracker->Scalars(scalars);
        if (!model.Observe(planes, scalars, &error)) throw std::runtime_error(error);
      } else if (command == "SCORE") {
        int requested_event;
        std::cin >> requested_event;
        if (!tracker || event != requested_event || !tracker->our_turn() || own_move_pending) {
          throw std::runtime_error("score outside actor decision");
        }
        MoveList legal;
        tracker->LegalCandidates(&legal);
        const auto packed = tracker->MakeCandidates(legal);
        std::vector<float> logits, dangers;
        if (packed.empty() || !model.Score(packed, &logits, &dangers, &error)) throw std::runtime_error(error);
        const auto risk = engine->DiagnosticKingLossProbabilities(legal, tracker->EnPassant());
        if (risk.size() != packed.size() || logits.size() != risk.size() || dangers.size() != risk.size()) {
          throw std::runtime_error("candidate output size mismatch");
        }
        const float peak = *std::max_element(logits.begin(), logits.end());
        std::vector<double> policy;
        double total = 0;
        for (float x : logits) { policy.push_back(std::exp(static_cast<double>(x - peak))); total += policy.back(); }
        for (double& x : policy) x /= total;
        Move engine_choice = kNullMove;
        int engine_choice_risk = -1;
        if (verify) {
          NeuralAdvice advice;
          advice.available = true;
          advice.policy = policy;
          for (const auto& x : packed) advice.moves.push_back(x.move);
          for (float x : dangers) advice.danger.push_back(1.0 / (1.0 + std::exp(-static_cast<double>(x))));
          DecisionTrace trace;
          const auto chosen = engine->ChooseMove(tracker->current(), 150.0, &trace, &advice);
          engine_choice = chosen;
          engine_choice_risk = trace.king_risk_permille;
          bool found = false;
          for (int i = 0; i < legal.size(); ++i) if (chosen == legal[i]) {
            found = true;
            const bool fused_risk = std::getenv("FOW_CALIBRATED_RISK_FUSION") != nullptr;
            if (legal.size() > 1 && !fused_risk &&
                trace.king_risk_permille != static_cast<int>(risk[i] * 1000.0)) {
              throw std::runtime_error("risk differs from actual engine choice trace");
            }
          }
          if (!found) throw std::runtime_error("engine choice not in tracker candidates");
        }
        std::cout << "{\"game\":\"" << game << "\",\"side\":" << side << ",\"event\":" << event
                  << ",\"ply\":" << ply << ",\"collapsed\":" << (engine->belief().last_report().collapsed ? "true" : "false")
                  << ",\"unseen\":" << PopCount(tracker->current().UnseenMask()) << ",\"candidates\":[";
        for (int i = 0; i < legal.size(); ++i) {
          if (!std::isfinite(risk[i]) || risk[i] < 0 || risk[i] > 1 || !std::isfinite(dangers[i]) ||
              !std::isfinite(policy[i])) throw std::runtime_error("invalid prediction");
          if (i) std::cout << ',';
          const char from = tracker->current().squares()[MoveFrom(legal[i])];
          std::cout << "{\"move\":\"" << MoveToUci(legal[i]) << "\",\"particle\":" << risk[i]
                    << ",\"neural_logit\":" << dangers[i] << ",\"policy\":" << policy[i]
                    << ",\"king_move\":" << ((from == 'K' || from == 'k') ? "true" : "false") << '}';
        }
        std::cout << "]";
        if (verify) {
          if (engine_choice == kNullMove) throw std::runtime_error("missing verified engine choice");
          std::cout << ",\"engine_choice\":\"" << MoveToUci(engine_choice)
                    << "\",\"engine_choice_risk_permille\":" << engine_choice_risk;
        }
        std::cout << "}\n";
      } else if (command == "MOVE") {
        std::string uci;
        std::cin >> uci;
        if (!tracker || !tracker->our_turn() || own_move_pending) throw std::runtime_error("own move outside turn");
        MoveList legal;
        tracker->LegalCandidates(&legal);
        Move move = kNullMove;
        for (const auto candidate : legal) if (MoveToUci(candidate) == uci) move = candidate;
        if (move == kNullMove) throw std::runtime_error("illegal actor move");
        engine->NotifyMovePlayed(move);
        tracker->RecordOwnMove(move);
        own_move_pending = true;
      } else if (command == "END") {
        if (!engine) throw std::runtime_error("END without actor");
        engine.reset(); tracker.reset();
      } else {
        throw std::runtime_error("unknown actor event");
      }
      if (!std::cin) throw std::runtime_error("truncated actor event");
    }
    if (engine) throw std::runtime_error("unterminated actor stream");
  } catch (const std::exception& e) {
    std::cerr << "risk diagnostic failed: " << e.what() << '\n';
    return 1;
  }
  return 0;
}
