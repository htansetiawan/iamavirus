"""ONNX export: two graphs from one checkpoint, a manifest, and parity checks.

    python -m learning.export --checkpoint checkpoints/pretrain/best.pt --output releases/v1

    observe.onnx   planes[B,32,8,8], scalars[B,8], hidden[B,256]
                   -> next_hidden[B,256], spatial[B,64,8,8], belief_logits[B,64,7], value[B,1]
    score.onnx     next_hidden[B,256], spatial[B,64,8,8],
                   candidate_from[B,M], candidate_to[B,M], promotion[B,M]
                   -> policy_logits[B,M], danger_logits[B,M]

Candidate masking and the softmax are applied by the adapter. Parity is checked
against PyTorch over complete held-out histories with varying candidate counts
at rtol 1e-4 / atol 1e-5; a failure is reported, never papered over by widening.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

from . import dataset as ds
from . import features
from .action_codec import canonical_square
from .model import FogPolicy, HIDDEN, CHANNELS, ARCHITECTURE, parameter_count
from .pretrain import load_model, checkpoint_hash


class ObserveGraph(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, planes, scalars, hidden):
        return self.model.observe(planes, scalars, hidden)


class ScoreGraph(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, next_hidden, spatial, candidate_from, candidate_to, promotion):
        return self.model.score(next_hidden, spatial, candidate_from, candidate_to, promotion)


def export_graphs(model: FogPolicy, output: Path) -> dict[str, Path]:
    model = model.cpu().eval()
    output.mkdir(parents=True, exist_ok=True)
    observe_path = output / "observe.onnx"
    score_path = output / "score.onnx"
    dynamic = {"planes": {0: "batch"}, "scalars": {0: "batch"}, "hidden": {0: "batch"},
               "next_hidden": {0: "batch"}, "spatial": {0: "batch"},
               "belief_logits": {0: "batch"}, "value": {0: "batch"}}
    torch.onnx.export(
        ObserveGraph(model),
        (torch.zeros(1, features.NUM_PLANES, 8, 8), torch.zeros(1, features.NUM_SCALARS), torch.zeros(1, model.hidden)),
        str(observe_path), input_names=["planes", "scalars", "hidden"],
        output_names=["next_hidden", "spatial", "belief_logits", "value"],
        dynamic_axes=dynamic, opset_version=17, dynamo=False)
    dynamic_score = {"next_hidden": {0: "batch"}, "spatial": {0: "batch"},
                     "candidate_from": {0: "batch", 1: "candidates"},
                     "candidate_to": {0: "batch", 1: "candidates"},
                     "promotion": {0: "batch", 1: "candidates"},
                     "policy_logits": {0: "batch", 1: "candidates"},
                     "danger_logits": {0: "batch", 1: "candidates"}}
    torch.onnx.export(
        ScoreGraph(model),
        (torch.zeros(1, model.hidden), torch.zeros(1, model.channels, 8, 8),
         torch.zeros(1, 3, dtype=torch.int64), torch.ones(1, 3, dtype=torch.int64), torch.zeros(1, 3, dtype=torch.int64)),
        str(score_path), input_names=["next_hidden", "spatial", "candidate_from", "candidate_to", "promotion"],
        output_names=["policy_logits", "danger_logits"], dynamic_axes=dynamic_score,
        opset_version=17, dynamo=False)
    return {"observe": observe_path, "score": score_path}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity_check(model: FogPolicy, graphs: dict[str, Path], episodes, rtol=1e-4, atol=1e-5,
                 max_episodes: int = 8) -> dict:
    """Runs complete histories through both runtimes and compares every output."""
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    observe = ort.InferenceSession(str(graphs["observe"]), options, providers=["CPUExecutionProvider"])
    score = ort.InferenceSession(str(graphs["score"]), options, providers=["CPUExecutionProvider"])
    model = model.cpu().eval()
    worst = {"hidden": 0.0, "policy": 0.0, "danger": 0.0, "belief": 0.0, "value": 0.0}
    decisions = 0
    failures = []
    for episode in episodes[:max_episodes]:
        planes, scalars, decision_list = ds.episode_tensors(episode)
        by_event = {d["event"]: d for d in decision_list}
        hidden_t = torch.zeros(1, model.hidden)
        hidden_o = np.zeros((1, model.hidden), dtype=np.float32)
        for event in range(planes.shape[0]):
            p = planes[event:event + 1]
            s = scalars[event:event + 1]
            with torch.no_grad():
                nh, sp, bl, v = model.observe(torch.from_numpy(p), torch.from_numpy(s), hidden_t)
            onh, osp, obl, ov = observe.run(None, {"planes": p, "scalars": s, "hidden": hidden_o})
            for name, a, b in (("hidden", nh.numpy(), onh), ("belief", bl.numpy(), obl), ("value", v.numpy(), ov)):
                diff = np.max(np.abs(a - b) - atol - rtol * np.abs(b))
                worst[name] = max(worst[name], float(np.max(np.abs(a - b))))
                if diff > 0:
                    failures.append((episode.metadata.game_id, event, name, float(np.max(np.abs(a - b)))))
            if event in by_event and by_event[event]["count"] > 0:
                d = by_event[event]
                cf = d["from"][None]
                ct = d["to"][None]
                cp = d["promo"][None]
                with torch.no_grad():
                    pl, dl = model.score(nh, sp, torch.from_numpy(cf), torch.from_numpy(ct), torch.from_numpy(cp))
                opl, odl = score.run(None, {"next_hidden": onh, "spatial": osp, "candidate_from": cf,
                                            "candidate_to": ct, "promotion": cp})
                for name, a, b in (("policy", pl.numpy(), opl), ("danger", dl.numpy(), odl)):
                    diff = np.max(np.abs(a - b) - atol - rtol * np.abs(b))
                    worst[name] = max(worst[name], float(np.max(np.abs(a - b))))
                    if diff > 0:
                        failures.append((episode.metadata.game_id, event, name, float(np.max(np.abs(a - b)))))
                decisions += 1
            hidden_t, hidden_o = nh, onh
    return {"decisions": decisions, "worst_abs_difference": worst, "failures": failures[:20],
            "failure_count": len(failures), "rtol": rtol, "atol": atol}


def write_manifest(output: Path, checkpoint: Path, payload: dict, graphs: dict[str, Path],
                   parity: dict | None, evaluation_report: str | None, model: FogPolicy | None = None) -> Path:
    manifest = {
        "checkpoint": str(checkpoint), "checkpoint_sha256": checkpoint_hash(checkpoint),
        "graphs": {name: {"path": path.name, "sha256": file_hash(path)} for name, path in graphs.items()},
        # the loaded network's own architecture: the engine sizes its buffers from it
        "architecture": model.architecture if model is not None else payload.get("architecture", ARCHITECTURE),
        "parameters": parameter_count(model) if model is not None else payload.get("parameters"),
        "feature_version": payload.get("feature_version", features.FEATURE_VERSION),
        "action_version": payload.get("action_version", features.ACTION_VERSION),
        "coordinate_transform": "canonical_square = raw ^ 56 for Black; identity for White",
        "rules_fingerprint": payload.get("rules_fingerprint"),
        "dataset_manifest_sha256": payload.get("dataset_manifest_sha256"),
        "normalization": {"age_cap": features.AGE_CAP, "ply_cap": features.PLY_CAP,
                          "coordinates": "file/7, rank/7"},
        "danger_calibrator": {"type": "identity-sigmoid", "note": "fit a calibrator on validation before trusting as a probability"},
        "hidden_size": model.hidden if model is not None else HIDDEN, "planes": features.NUM_PLANES, "scalars": features.NUM_SCALARS,
        "parity": parity, "evaluation_report": evaluation_report,
        "training_step": payload.get("step"), "training_extra": payload.get("extra"),
    }
    path = output / "model_manifest.json"
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parity-shard", type=Path, default=None, help="held-out episodes for the parity check")
    parser.add_argument("--parity-episodes", type=int, default=8)
    parser.add_argument("--evaluation-report", default=None)
    args = parser.parse_args(argv)
    model, payload = load_model(args.checkpoint)
    graphs = export_graphs(model, args.output)
    parity = None
    if args.parity_shard:
        episodes = [e for e in ds.load_episodes(args.parity_shard, args.parity_episodes * 3) if e.num_decisions > 0]
        parity = parity_check(model, graphs, episodes, max_episodes=args.parity_episodes)
        status = "PASS" if parity["failure_count"] == 0 else "FAIL"
        print(f"parity {status}: {parity['decisions']} decisions, worst {parity['worst_abs_difference']}", file=sys.stderr)
    path = write_manifest(args.output, args.checkpoint, payload, graphs, parity, args.evaluation_report, model)
    print(f"wrote {path}")
    return 0 if not parity or parity["failure_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
