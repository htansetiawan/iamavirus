// Copyright 2026. Fog of War chess engine.
//
// ONNX Runtime inference for the recurrent policy exported by learning/export.py.
//
// Two graphs share one checkpoint: `observe.onnx` advances the recurrent state
// on every real observation event, and `score.onnx` scores a packed list of
// legal candidates at a decision. The adapter keeps the hidden state for the
// whole game, loads both graphs once before "ready", and never downloads or
// trains anything. When the build has no ONNX Runtime, or a graph fails to
// load, `available()` is false and the engine's C++ decision procedure plays.

#ifndef FOW_NEURAL_INFERENCE_H_
#define FOW_NEURAL_INFERENCE_H_

#include <memory>
#include <string>
#include <vector>

#include "neural_observation.h"

namespace fow {

inline constexpr int kNeuralHidden = 256;
inline constexpr int kNeuralChannels = 64;
inline constexpr int kNeuralBeliefClasses = 7;

class NeuralModel {
 public:
  NeuralModel();
  ~NeuralModel();
  NeuralModel(const NeuralModel&) = delete;
  NeuralModel& operator=(const NeuralModel&) = delete;

  // Loads observe.onnx, score.onnx and model_manifest.json from `directory`
  // and runs a warm-up inference. Returns false with a message on failure.
  bool Load(const std::string& directory, int threads, std::string* error);
  bool available() const { return available_; }
  // Marks the model unusable for the rest of the game after a runtime error.
  void Disable() { available_ = false; }

  // Starts a new game: zero recurrent state.
  void Reset();
  // Processes one observation event (planes: 32*64 floats, scalars: 8).
  bool Observe(const float* planes, const float* scalars, std::string* error);
  // Scores candidates from the state left by the last Observe. Outputs are
  // aligned with `candidates`; the caller applies the softmax and the mask.
  bool Score(const std::vector<NeuralCandidate>& candidates,
             std::vector<float>* policy_logits, std::vector<float>* danger_logits,
             std::string* error);

  float value() const { return value_; }
  const std::vector<float>& belief_logits() const { return belief_logits_; }
  const std::string& manifest_summary() const { return manifest_summary_; }

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
  bool available_ = false;
  std::vector<float> hidden_;
  std::vector<float> spatial_;
  std::vector<float> belief_logits_;
  float value_ = 0.0f;
  std::string manifest_summary_;
};

}  // namespace fow

#endif  // FOW_NEURAL_INFERENCE_H_
