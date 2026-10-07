"""Untrained graph parity and host CPU diagnostics, not strength or arena timings."""
import argparse
import hashlib
import json
import platform
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from learning.export import export_graphs
from learning.model import parameter_count
from learning_experiments.models import ModelConfig, make_model


def profile(config, output, repeats=100):
    torch.manual_seed(253)
    model = make_model(config).eval()
    graphs = export_graphs(model, output)
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    observe = ort.InferenceSession(str(graphs["observe"]), options, providers=["CPUExecutionProvider"])
    score = ort.InferenceSession(str(graphs["score"]), options, providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(253)
    worst = 0.0
    for batch, candidates in [(1, 1), (2, 37), (3, 96)]:
        inputs = {"planes": rng.normal(size=(batch, 32, 8, 8)).astype(np.float32),
                  "scalars": rng.normal(size=(batch, 8)).astype(np.float32),
                  "hidden": rng.normal(size=(batch, 256)).astype(np.float32)}
        with torch.no_grad():
            expected = model.observe(*(torch.from_numpy(inputs[k]) for k in ("planes", "scalars", "hidden")))
        actual = observe.run(None, inputs)
        for a, b in zip(expected, actual):
            a = a.numpy()
            np.testing.assert_allclose(a, b, atol=1e-5, rtol=1e-4)
            worst = max(worst, float(np.abs(a - b).max()))
        candidate = {"candidate_from": rng.integers(64, size=(batch, candidates), dtype=np.int64),
                     "candidate_to": rng.integers(64, size=(batch, candidates), dtype=np.int64),
                     "promotion": rng.integers(5, size=(batch, candidates), dtype=np.int64)}
        with torch.no_grad():
            expected_score = model.score(expected[0], expected[1],
                *(torch.from_numpy(candidate[k]) for k in ("candidate_from", "candidate_to", "promotion")))
        got = score.run(None, {"next_hidden": actual[0], "spatial": actual[1], **candidate})
        for a, b in zip(expected_score, got):
            np.testing.assert_allclose(a.numpy(), b, atol=1e-5, rtol=1e-4)
            worst = max(worst, float(np.abs(a.numpy() - b).max()))
    obs_input = {"planes": inputs["planes"][:1], "scalars": inputs["scalars"][:1],
                 "hidden": inputs["hidden"][:1]}
    candidate = {k: v[:1] for k, v in candidate.items()}
    durations = []
    for i in range(repeats + 20):
        start = time.perf_counter_ns()
        hidden, spatial, *_ = observe.run(None, obs_input)
        score.run(None, {"next_hidden": hidden, "spatial": spatial, **candidate})
        elapsed = (time.perf_counter_ns() - start) / 1e6
        if i >= 20:
            durations.append(elapsed)
    return {"model": asdict(config), "architecture": config.architecture,
            "parameters": parameter_count(model), "trained": False,
            "parity": {"status": "passed", "cases": [[1, 1], [2, 37], [3, 96]], "worst_absolute_error": worst},
            "onnx": {k: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                     for k, p in graphs.items()},
            "observe_plus_score_96_candidates_ms": {f"p{p}": float(np.percentile(durations, p)) for p in (50, 95, 99)},
            "timing_scope": "untrained random inputs, shared host CPU, one ORT thread; not an arena clock gate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=100)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    torch.set_num_threads(2)
    results = [profile(ModelConfig(name), args.output / name, args.repeats)
               for name in ("cnn", "attention", "compressed_attention")]
    report = {"host": platform.platform(), "torch": torch.__version__, "onnxruntime": ort.__version__,
              "results": results}
    (args.output / "profile.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
