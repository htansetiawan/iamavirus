"""Audit partial INT8 inference on real, complete observation histories.

Quantizes constant-weight MatMul/Gemm nodes. CNN convolutions and unsupported
operations remain FP32; the report counts what was actually quantized. Each
runtime feeds back its own hidden state. Policy-only changes are diagnostic,
not assertions about the hybrid engine's final search decisions.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.shape_inference import quant_pre_process

from learning import dataset as ds
from learning.features import FEATURE_VERSION
from learning_experiments.run import file_hash, isolate_rules, select_games, write_json


def sessions(directory):
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    return {name: ort.InferenceSession(str(directory / f"{name}.onnx"), options,
                                      providers=["CPUExecutionProvider"])
            for name in ("observe", "score")}


def probabilities(logits):
    shifted = logits - logits.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def audit(graphs, shard, output, games, keep_recurrent_fp32=False):
    manifest = json.loads((graphs / 'model_manifest.json').read_text())
    if manifest.get('feature_version') != FEATURE_VERSION:
        raise ValueError('graph feature contract differs; audit with its frozen feature implementation')
    if (output / "audit.json").exists():
        raise ValueError("audit already exists; use a new output directory")
    output.mkdir(parents=True, exist_ok=True)
    native = isolate_rules(output)
    qdir = output / "int8"
    qdir.mkdir(exist_ok=True)
    graph_stats = {}
    for name in ("observe", "score"):
        source = graphs / f"{name}.onnx"
        prepared = output / f"{name}-prepared.onnx"
        quant_pre_process(source, prepared, skip_optimization=True, skip_symbolic_shape=True)
        target = qdir / f"{name}.onnx"
        exclusions = []
        for node in onnx.load(prepared).graph.node:
            if keep_recurrent_fp32 and '/gru/' in node.name:
                exclusions.append(node.name)
                # ORT rewrites Gemm before applying exclusions. Its MatMul has
                # a new name; excluding only the original Gemm is a no-op.
                if node.op_type == 'Gemm':
                    exclusions.append(node.name + '_MatMul')
        if name == 'observe' and keep_recurrent_fp32 and not exclusions:
            raise RuntimeError('could not identify GRU nodes for selective precision')
        quantize_dynamic(prepared, target, op_types_to_quantize=["MatMul", "Gemm"],
                         weight_type=QuantType.QInt8, per_channel=True,
                         nodes_to_exclude=exclusions,
                         extra_options={"MatMulConstBOnly": True})
        graph = onnx.load(target)
        if keep_recurrent_fp32 and name == 'observe':
            recurrent_weights = [t for t in graph.graph.initializer if '.gru.weight_' in t.name]
            if len(recurrent_weights) != 2 or any(t.data_type != onnx.TensorProto.FLOAT for t in recurrent_weights):
                raise RuntimeError('GRU precision exclusion did not preserve both FP32 weight matrices')
            if any('/gru/' in n.name and n.op_type == 'MatMulInteger' for n in graph.graph.node):
                raise RuntimeError('GRU still contains a quantized matrix multiply')
        ops = Counter(n.op_type for n in graph.graph.node)
        graph_stats[name] = {"source_sha256": file_hash(source), "int8_sha256": file_hash(target),
                             "source_bytes": source.stat().st_size, "int8_bytes": target.stat().st_size,
                             "excluded_nodes": exclusions,
                             "quantized_operators": {k: v for k, v in ops.items() if "Integer" in k or "Quant" in k},
                             "int8_weight_elements": sum(int(np.prod(t.dims)) for t in graph.graph.initializer
                                                         if t.data_type == onnx.TensorProto.INT8)}
        if not graph_stats[name]["int8_weight_elements"]:
            raise RuntimeError(f"no weights were quantized in {name}")
    runtimes = {"fp32": sessions(graphs), "int8": sessions(qdir)}
    episodes = select_games(ds.load_episodes(shard), games)
    counts = Counter()
    sums = Counter()
    worst = Counter()
    timings = {name: [] for name in runtimes}
    changes = []
    for episode in episodes:
        planes, scalars, decisions = ds.episode_tensors(episode)
        by_event = {d["event"]: d for d in decisions}
        hidden = {name: np.zeros((1, 256), np.float32) for name in runtimes}
        for event in range(len(planes)):
            outputs, elapsed = {}, {}
            order = ("fp32", "int8") if event % 2 == 0 else ("int8", "fp32")
            for arm in order:
                start = time.perf_counter_ns()
                outputs[arm] = runtimes[arm]["observe"].run(None, {
                    "planes": planes[event:event + 1], "scalars": scalars[event:event + 1], "hidden": hidden[arm]})
                elapsed[arm] = (time.perf_counter_ns() - start) / 1e6
                hidden[arm] = outputs[arm][0]
            counts["observations"] += 1
            worst["hidden_max_abs"] = max(worst["hidden_max_abs"], float(np.abs(hidden['fp32'] - hidden['int8']).max()))
            d = by_event.get(event)
            if d is None or not d['count']:
                continue
            score = {}
            for arm in order:
                start = time.perf_counter_ns()
                score[arm] = runtimes[arm]['score'].run(None, {
                    'next_hidden': hidden[arm], 'spatial': outputs[arm][1],
                    'candidate_from': d['from'][None], 'candidate_to': d['to'][None], 'promotion': d['promo'][None]})
                elapsed[arm] += (time.perf_counter_ns() - start) / 1e6
                if counts['decisions'] >= 20:
                    timings[arm].append(elapsed[arm])
            counts['decisions'] += 1
            fp, qp = (score[name][0][0] for name in ('fp32', 'int8'))
            a, b = int(fp.argmax()), int(qp.argmax())
            counts['policy_top1_agree'] += int(a == b)
            p, q = probabilities(fp), probabilities(qp)
            sums['policy_kl_fp32_to_int8'] += float((p * (np.log(p.clip(1e-12)) - np.log(q.clip(1e-12)))).sum())
            k = min(8, len(fp))
            sums['policy_top8_overlap'] += len(set(fp.argsort()[-k:]) & set(qp.argsort()[-k:])) / k
            worst['policy_logit_max_abs'] = max(worst['policy_logit_max_abs'], float(np.abs(fp - qp).max()))
            if d['danger_valid']:
                counts['danger_candidates'] += d['count']
                counts['policy_fp32_fatal'] += int(d['danger'][a])
                counts['policy_int8_fatal'] += int(d['danger'][b])
                counts['policy_new_fatal'] += int(d['danger'][b] and not d['danger'][a])
                counts['policy_saved_fatal'] += int(d['danger'][a] and not d['danger'][b])
                risk = {}
                for arm in runtimes:
                    risk[arm] = 1 / (1 + np.exp(-score[arm][1][0].clip(-80, 80)))
                    sums[f'{arm}_danger_brier'] += float(np.square(risk[arm] - d['danger']).sum())
                worst['danger_probability_max_abs'] = max(worst['danger_probability_max_abs'], float(np.abs(risk['fp32'] - risk['int8']).max()))
            if a != b:
                changes.append({'game': episode.metadata.game_id, 'side': episode.actor.side,
                                'ply': episode.actor.plies[event], 'fp32_index': a, 'int8_index': b,
                                'fp32_fatal': bool(d['danger'][a]) if d['danger_valid'] else None,
                                'int8_fatal': bool(d['danger'][b]) if d['danger_valid'] else None})
    n = counts['decisions']
    report = {'source_graph_directory': str(graphs), 'shard_sha256': file_hash(shard),
              'feature_version': FEATURE_VERSION,
              'source_manifest_sha256': file_hash(graphs / 'model_manifest.json'),
              'keep_recurrent_fp32': keep_recurrent_fp32,
              'onnxruntime': ort.__version__, 'native': native, 'graphs': graph_stats,
              'episodes': len(episodes), 'games': len({e.metadata.game_id for e in episodes}),
              'counts': dict(counts), 'worst': dict(worst),
              'policy_top1_agreement': counts['policy_top1_agree'] / max(n, 1),
              'policy_top8_overlap': sums['policy_top8_overlap'] / max(n, 1),
              'policy_kl_fp32_to_int8': sums['policy_kl_fp32_to_int8'] / max(n, 1),
              'danger_brier': {arm: sums[f'{arm}_danger_brier'] / max(counts['danger_candidates'], 1) for arm in runtimes},
              'root_observe_plus_score_ms': {arm: {f'p{p}': float(np.percentile(values, p)) for p in (50, 95, 99)}
                                             for arm, values in timings.items() if values},
              'changes': changes,
              'limitations': ['Partial INT8: unquantized operators remain FP32.',
                              'Policy-only argmax changes are not hybrid search decisions.',
                              'Shared-host timings with alternating order; no arena latency claim.',
                              'Quantization is lossy; numerical equality is not expected or asserted.']}
    write_json(output / 'audit.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('native', 'changes')}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphs', type=Path, required=True)
    parser.add_argument('--shard', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--games', type=int, default=16)
    parser.add_argument('--keep-recurrent-fp32', action='store_true')
    args = parser.parse_args()
    if args.games < 1:
        parser.error('games must be positive')
    audit(args.graphs, args.shard, args.output, args.games, args.keep_recurrent_fp32)


if __name__ == '__main__':
    main()
