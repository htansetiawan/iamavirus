#!/usr/bin/env python3
"""Build an isolated actor-only choice probe with optional calibrated fusion."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-copy', type=Path,
                        default=ROOT / 'astra-submissions/build/neural-risk-r1')
    parser.add_argument('--calibrator', type=Path,
                        default=ROOT / 'astra-submissions/analysis/neural-risk/evaluation-20261011.json')
    parser.add_argument('--ort', type=Path,
                        default=ROOT.parent / 'onnxruntime-sdk/onnxruntime-linux-x64-1.24.2')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'astra-submissions/build/neural-risk-choice-r1')
    args = parser.parse_args()
    source, output = args.source_copy.resolve(), args.output.resolve()
    receipt_path = source / 'probe-build.json'
    receipt = json.loads(receipt_path.read_text())
    if output.exists():
        raise FileExistsError(output)
    if receipt['source_receipt_sha256'] != sha(Path(receipt['source_receipt'])):
        raise ValueError('frozen integration receipt changed')
    calibrator = json.loads(args.calibrator.read_text())
    fusion = calibrator['calibrators']['fused']['beta']
    means = calibrator['feature_standardization']['weighted_mean']
    scales = calibrator['feature_standardization']['weighted_std']
    if len(fusion) != 3 or len(means) != 2 or len(scales) != 2:
        raise ValueError('unsupported calibrated-risk shape')
    for value in [*fusion, *means, *scales]:
        if not isinstance(value, (int, float)):
            raise ValueError('non-numeric calibrated-risk coefficient')

    output.mkdir(parents=True)
    for name, digest in receipt['files_sha256'].items():
        src = source / name
        if not src.is_file() or sha(src) != digest:
            raise ValueError('frozen source copy changed: ' + name)
        dst = output / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    engine_path = output / 'engine.cc'
    engine = engine_path.read_text()
    needle = '  const std::vector<double> king_risk = KingLossProbabilities(legal, en_passant);'
    if engine.count(needle) != 1:
        raise ValueError('unexpected engine risk calculation')
    replacement = f'''  std::vector<double> king_risk = KingLossProbabilities(legal, en_passant);
  // Offline experiment only. The default engine has no calibrated fusion.
  // FOW_CALIBRATED_RISK_FUSION substitutes the frozen, calibration-only
  // particle+neural probability in the existing safety gate and payoff.
  if (advised && options_.mode == EngineMode::kHybrid &&
      std::getenv("FOW_CALIBRATED_RISK_FUSION") != nullptr) {{
    constexpr double mean_particle = {means[0]:.17g};
    constexpr double mean_neural = {means[1]:.17g};
    constexpr double std_particle = {scales[0]:.17g};
    constexpr double std_neural = {scales[1]:.17g};
    constexpr double beta0 = {fusion[0]:.17g};
    constexpr double beta_particle = {fusion[1]:.17g};
    constexpr double beta_neural = {fusion[2]:.17g};
    for (int i = 0; i < legal.size(); ++i) {{
      const int at = AdviceIndex(*advice, legal[i]);
      if (at < 0 || at >= static_cast<int>(advice->danger.size())) continue;
      const double p_particle = std::clamp(king_risk[static_cast<std::size_t>(i)], 0.0001, 0.9999);
      const double p_neural = std::clamp(advice->danger[static_cast<std::size_t>(at)], 0.0001, 0.9999);
      const double x_particle = (std::log(p_particle / (1.0 - p_particle)) - mean_particle) / std_particle;
      const double x_neural = (std::log(p_neural / (1.0 - p_neural)) - mean_neural) / std_neural;
      const double z = beta0 + beta_particle * x_particle + beta_neural * x_neural;
      king_risk[static_cast<std::size_t>(i)] = z >= 0.0
          ? 1.0 / (1.0 + std::exp(-z))
          : std::exp(z) / (1.0 + std::exp(z));
    }}
  }}'''
    engine_path.write_text(engine.replace(needle, replacement))
    probe_path = output / 'risk_probe.cc'
    probe_path.write_bytes((ROOT / 'astra-submissions/tools/probe_neural_risk.cc').read_bytes())

    units = ['risk_probe', 'engine', 'search', 'evaluation', 'transposition', 'regret',
             'neural_observation', 'neural_inference', 'belief', 'opponent_model',
             'observation', 'position', 'move', 'bitboard']
    ort = args.ort.resolve()
    command = ['g++', '-O2', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread', '-mpopcnt',
               '-DFOW_WITH_ONNX', '-I' + str(output), '-I' + str(ort / 'include'),
               *(str(output / (u + '.cc')) for u in units), '-L' + str(ort / 'lib'),
               '-Wl,-rpath,' + str(ort / 'lib'), '-lonnxruntime', '-o', str(output / 'probe')]
    with (output / 'build.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    manifest = {
        'classification': 'diagnostic binary; default behavior unchanged unless FOW_CALIBRATED_RISK_FUSION is set',
        'source_probe_receipt': str(receipt_path),
        'source_probe_receipt_sha256': sha(receipt_path),
        'calibrator': str(args.calibrator.resolve()),
        'calibrator_sha256': sha(args.calibrator.resolve()),
        'calibration': {'beta': fusion, 'weighted_mean': means, 'weighted_std': scales},
        'files_sha256': {str(p.relative_to(output)): sha(p) for p in output.rglob('*')
                         if p.is_file() and p.suffix in ('.h', '.cc')},
        'probe_sha256': sha(output / 'probe'),
        'builder_sha256': sha(Path(__file__)),
        'command': command,
        'choice_output': 'The verify argument emits the isolated engine choice and its risk estimate for each actor SCORE event.',
        'limitations': ['Counterfactual replay forces the recorded continuation after a different choice.',
                        'This is not an Elo or full-game rollout experiment.',
                        'The fusion coefficients are fitted on development-validation games.',
                        'The sealed test shard remains unread.'],
    }
    (output / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'probe_sha256': manifest['probe_sha256']}))


if __name__ == '__main__':
    main()
