// Copyright 2026. Fog of War chess engine.

#include "neural_inference.h"

#include <array>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#ifdef FOW_WITH_ONNX
#include <onnxruntime_cxx_api.h>
#endif

namespace fow {

#ifdef FOW_WITH_ONNX

struct NeuralModel::Impl {
  Ort::Env env{ORT_LOGGING_LEVEL_WARNING, "fow"};
  Ort::SessionOptions options;
  std::unique_ptr<Ort::Session> observe;
  std::unique_ptr<Ort::Session> score;
  Ort::MemoryInfo memory{Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault)};
};

namespace {

std::string ReadFile(const std::string& path) {
  std::ifstream stream(path);
  std::stringstream buffer;
  buffer << stream.rdbuf();
  return buffer.str();
}

// A compact, dependency-free extraction of the hashes recorded in the manifest,
// for the stderr log. The manifest is informational here; the graphs are what
// the session loads.
std::string ManifestSummary(const std::string& text) {
  std::string summary;
  for (const char* key : {"\"checkpoint_sha256\"", "\"training_step\""}) {
    const std::size_t at = text.find(key);
    if (at == std::string::npos) continue;
    const std::size_t colon = text.find(':', at);
    if (colon == std::string::npos) continue;
    std::size_t end = text.find_first_of(",}\n", colon);
    std::string value = text.substr(colon + 1, end - colon - 1);
    while (!value.empty() && (value.front() == ' ' || value.front() == '"')) value.erase(0, 1);
    while (!value.empty() && (value.back() == ' ' || value.back() == '"')) value.pop_back();
    if (!summary.empty()) summary += ' ';
    summary += std::string(key).substr(1, std::string(key).size() - 2) + '=' +
               value.substr(0, 12);
  }
  return summary;
}

}  // namespace

NeuralModel::NeuralModel() : impl_(new Impl()) {}
NeuralModel::~NeuralModel() = default;

bool NeuralModel::Load(const std::string& directory, int threads,
                       std::string* error) {
  try {
    impl_->options.SetIntraOpNumThreads(threads);
    impl_->options.SetInterOpNumThreads(1);
    impl_->options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    impl_->observe = std::make_unique<Ort::Session>(
        impl_->env, (directory + "/observe.onnx").c_str(), impl_->options);
    impl_->score = std::make_unique<Ort::Session>(
        impl_->env, (directory + "/score.onnx").c_str(), impl_->options);
    const std::string manifest_text = ReadFile(directory + "/model_manifest.json");
    manifest_summary_ = ManifestSummary(manifest_text);
    {
      // The graphs only make sense with the feature encoding they were trained
      // on; a model exported for another version is refused, and the bot falls
      // back to the pure engine with this reason in its log.
      const std::string key = "\"feature_version\": \"";
      const std::size_t at = manifest_text.find(key);
      std::string exported = "(missing)";
      if (at != std::string::npos) {
        const std::size_t start = at + key.size();
        const std::size_t end = manifest_text.find('"', start);
        if (end != std::string::npos) exported = manifest_text.substr(start, end - start);
      }
      if (exported != kFeatureVersion) {
        if (error) *error = "model exported for " + exported + ", this engine builds " + kFeatureVersion;
        available_ = false;
        return false;
      }
    }
    available_ = true;
    Reset();
    // Warm up both graphs so the first real inference is not the slow one.
    std::vector<float> planes(kNeuralPlanes * kNumSquares, 0.0f);
    std::array<float, kNeuralScalars> scalars{};
    std::string warm;
    if (!Observe(planes.data(), scalars.data(), &warm)) {
      if (error) *error = "warm-up observe failed: " + warm;
      available_ = false;
      return false;
    }
    std::vector<NeuralCandidate> candidates(3);
    std::vector<float> policy, danger;
    if (!Score(candidates, &policy, &danger, &warm)) {
      if (error) *error = "warm-up score failed: " + warm;
      available_ = false;
      return false;
    }
    Reset();
    return true;
  } catch (const std::exception& problem) {
    if (error) *error = problem.what();
    available_ = false;
    return false;
  }
}

void NeuralModel::Reset() {
  hidden_.assign(kNeuralHidden, 0.0f);
  spatial_.assign(kNeuralChannels * kNumSquares, 0.0f);
  belief_logits_.assign(kNumSquares * kNeuralBeliefClasses, 0.0f);
  value_ = 0.0f;
}

bool NeuralModel::Observe(const float* planes, const float* scalars,
                          std::string* error) {
  if (!available_) return false;
  try {
    const std::array<int64_t, 4> planes_shape = {1, kNeuralPlanes, 8, 8};
    const std::array<int64_t, 2> scalars_shape = {1, kNeuralScalars};
    const std::array<int64_t, 2> hidden_shape = {1, kNeuralHidden};
    std::array<Ort::Value, 3> inputs = {
        Ort::Value::CreateTensor<float>(impl_->memory, const_cast<float*>(planes),
                                        kNeuralPlanes * kNumSquares,
                                        planes_shape.data(), planes_shape.size()),
        Ort::Value::CreateTensor<float>(impl_->memory, const_cast<float*>(scalars),
                                        kNeuralScalars, scalars_shape.data(),
                                        scalars_shape.size()),
        Ort::Value::CreateTensor<float>(impl_->memory, hidden_.data(), kNeuralHidden,
                                        hidden_shape.data(), hidden_shape.size())};
    const char* input_names[] = {"planes", "scalars", "hidden"};
    const char* output_names[] = {"next_hidden", "spatial", "belief_logits", "value"};
    std::vector<Ort::Value> outputs = impl_->observe->Run(
        Ort::RunOptions{nullptr}, input_names, inputs.data(), inputs.size(),
        output_names, 4);
    const float* next_hidden = outputs[0].GetTensorData<float>();
    hidden_.assign(next_hidden, next_hidden + kNeuralHidden);
    const float* spatial = outputs[1].GetTensorData<float>();
    spatial_.assign(spatial, spatial + kNeuralChannels * kNumSquares);
    const float* belief = outputs[2].GetTensorData<float>();
    belief_logits_.assign(belief, belief + kNumSquares * kNeuralBeliefClasses);
    value_ = outputs[3].GetTensorData<float>()[0];
    return true;
  } catch (const std::exception& problem) {
    if (error) *error = problem.what();
    return false;
  }
}

bool NeuralModel::Score(const std::vector<NeuralCandidate>& candidates,
                        std::vector<float>* policy_logits,
                        std::vector<float>* danger_logits, std::string* error) {
  if (!available_ || candidates.empty()) return false;
  try {
    const int64_t count = static_cast<int64_t>(candidates.size());
    std::vector<int64_t> from(candidates.size()), to(candidates.size()),
        promotion(candidates.size());
    for (std::size_t i = 0; i < candidates.size(); ++i) {
      from[i] = candidates[i].from;
      to[i] = candidates[i].to;
      promotion[i] = candidates[i].promotion;
    }
    const std::array<int64_t, 2> hidden_shape = {1, kNeuralHidden};
    const std::array<int64_t, 4> spatial_shape = {1, kNeuralChannels, 8, 8};
    const std::array<int64_t, 2> cand_shape = {1, count};
    std::array<Ort::Value, 5> inputs = {
        Ort::Value::CreateTensor<float>(impl_->memory, hidden_.data(), kNeuralHidden,
                                        hidden_shape.data(), hidden_shape.size()),
        Ort::Value::CreateTensor<float>(impl_->memory, spatial_.data(),
                                        kNeuralChannels * kNumSquares,
                                        spatial_shape.data(), spatial_shape.size()),
        Ort::Value::CreateTensor<int64_t>(impl_->memory, from.data(), from.size(),
                                          cand_shape.data(), cand_shape.size()),
        Ort::Value::CreateTensor<int64_t>(impl_->memory, to.data(), to.size(),
                                          cand_shape.data(), cand_shape.size()),
        Ort::Value::CreateTensor<int64_t>(impl_->memory, promotion.data(),
                                          promotion.size(), cand_shape.data(),
                                          cand_shape.size())};
    const char* input_names[] = {"next_hidden", "spatial", "candidate_from",
                                 "candidate_to", "promotion"};
    const char* output_names[] = {"policy_logits", "danger_logits"};
    std::vector<Ort::Value> outputs = impl_->score->Run(
        Ort::RunOptions{nullptr}, input_names, inputs.data(), inputs.size(),
        output_names, 2);
    const float* policy = outputs[0].GetTensorData<float>();
    const float* danger = outputs[1].GetTensorData<float>();
    policy_logits->assign(policy, policy + count);
    danger_logits->assign(danger, danger + count);
    return true;
  } catch (const std::exception& problem) {
    if (error) *error = problem.what();
    return false;
  }
}

#else  // FOW_WITH_ONNX

struct NeuralModel::Impl {};

NeuralModel::NeuralModel() : impl_(new Impl()) {}
NeuralModel::~NeuralModel() = default;

bool NeuralModel::Load(const std::string&, int, std::string* error) {
  if (error) *error = "built without ONNX Runtime (FOW_WITH_ONNX not defined)";
  available_ = false;
  return false;
}

void NeuralModel::Reset() {
  hidden_.assign(kNeuralHidden, 0.0f);
  spatial_.assign(kNeuralChannels * kNumSquares, 0.0f);
  belief_logits_.assign(kNumSquares * kNeuralBeliefClasses, 0.0f);
  value_ = 0.0f;
}

bool NeuralModel::Observe(const float*, const float*, std::string* error) {
  if (error) *error = "no model";
  return false;
}

bool NeuralModel::Score(const std::vector<NeuralCandidate>&, std::vector<float>*,
                        std::vector<float>*, std::string* error) {
  if (error) *error = "no model";
  return false;
}

#endif  // FOW_WITH_ONNX

}  // namespace fow
